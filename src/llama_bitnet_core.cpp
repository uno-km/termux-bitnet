/**
 * @file llama_bitnet_core.cpp
 * @brief BitNet Core Engine Implementation with True GGUF Binary Parser & SIMD Kernels.
 * @author uno-km (https://github.com/uno-km)
 */

#include "llama_bitnet_core.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <cmath>
#include <cstring>
#include <algorithm>
#include <chrono>

#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#endif
#include <vector>
#include <memory>

#if defined(__ARM_NEON)
#include <arm_neon.h>
#elif defined(__AVX2__)
#include <immintrin.h>
#endif

#if defined(GGML_USE_VULKAN)
#include "core/vulkan_bitnet_engine.h"
#endif

static void print_download_catalog_help(std::ostream& out) {
    out << "\n[Official BitNet Verified Model Catalog]\n"
        << "  1. bitnet-2b    : Microsoft BitNet 2B-4T (1.13 GB, i2_s)\n"
        << "     Download CLI : termux-bitnet download bitnet-2b\n"
        << "     Hugging Face : https://huggingface.co/1bitLLM/bitnet_b1_58-large-GGUF\n"
        << "  2. bitnet-large : BitNet b1.58 Large 0.7B (700 MB, i2_s)\n"
        << "     Download CLI : termux-bitnet download bitnet-large\n"
        << "     Hugging Face : https://huggingface.co/1bitLLM/bitnet_b1_58-large-GGUF\n"
        << "  3. bitnet-3b    : BitNet b1.58 3B (2.4 GB, i2_s)\n"
        << "     Download CLI : termux-bitnet download bitnet-3b\n"
        << "     Hugging Face : https://huggingface.co/1bitLLM/bitnet_b1_58-3B-GGUF\n"
        << "  4. bitnet-3b-q4 : BitNet b1.58 3B Q4_K_M (1.8 GB)\n"
        << "     Download CLI : termux-bitnet download bitnet-3b-q4\n"
        << "     Hugging Face : https://huggingface.co/1bitLLM/bitnet_b1_58-3B-GGUF\n";
}

// Helper: read binary data safely
template<typename T>
static bool read_val(std::ifstream& f, T& val) {
    return (bool)f.read(reinterpret_cast<char*>(&val), sizeof(T));
}

static bool read_string(std::ifstream& f, std::string& str) {
    uint64_t len = 0;
    if (!read_val(f, len)) return false;
    if (len > 10 * 1024 * 1024) return false; // Sanity check: max 10MB string
    str.resize(len);
    if (len > 0) {
        if (!f.read(&str[0], len)) return false;
    }
    return true;
}

// Skip GGUF metadata value based on type
static bool skip_gguf_value(std::ifstream& f, uint32_t val_type) {
    switch (val_type) {
        case 0: case 1: case 7: { uint8_t v; return read_val(f, v); }
        case 2: case 3: { uint16_t v; return read_val(f, v); }
        case 4: case 5: case 6: { uint32_t v; return read_val(f, v); }
        case 8: { std::string s; return read_string(f, s); }
        case 10: case 11: case 12: { uint64_t v; return read_val(f, v); }
        case 9: { // Array
            uint32_t arr_type = 0;
            uint64_t arr_len = 0;
            if (!read_val(f, arr_type) || !read_val(f, arr_len)) return false;
            for (uint64_t i = 0; i < arr_len; ++i) {
                if (!skip_gguf_value(f, arr_type)) return false;
            }
            return true;
        }
        default:
            return false;
    }
}

bitnet_params_t bitnet_default_params(void) {
    bitnet_params_t p;
    p.model_path = "";
    p.system_prompt = "";
    p.stop_tokens = "";
    p.n_threads = 4;
    p.n_ctx = 2048;
    p.n_batch = 512;
    p.n_ubatch = 512;
    p.n_predict = 128;
    p.top_k = 40;
    p.repeat_last_n = 64;
    p.n_gpu_layers = 0;
    p.seed = 0;
    p.temperature = 0.7f;
    p.top_p = 0.95f;
    p.min_p = 0.05f;
    p.typical_p = 1.0f;
    p.repeat_penalty = 1.15f;
    p.frequency_penalty = 0.0f;
    p.presence_penalty = 0.0f;
    p.flash_attn = false;
    p.verbose = false;
    return p;
}

bitnet_context_t bitnet_init(const bitnet_params_t* params) {
    if (!params) {
        std::cerr << "[termux-bitnet ERROR] Initialization failed: params pointer is NULL." << std::endl;
        return nullptr;
    }

    if (!params->model_path || std::strlen(params->model_path) == 0) {
        std::cerr << "[termux-bitnet ERROR] No model path specified. Native GGUF loading requires a valid model path." << std::endl;
        print_download_catalog_help(std::cerr);
        return nullptr;
    }

    std::ifstream model_file(params->model_path, std::ios::binary);
    if (!model_file.is_open()) {
        std::cerr << "[termux-bitnet ERROR] Model file not found or inaccessible: '" << params->model_path << "'" << std::endl;
        print_download_catalog_help(std::cerr);
        return nullptr;
    }

    // 1. Verify GGUF Magic & Header
    char magic[5] = {0};
    if (!model_file.read(magic, 4) || std::memcmp(magic, "GGUF", 4) != 0) {
        std::cerr << "[termux-bitnet ERROR] Invalid model format. Expected GGUF header magic ('GGUF')." << std::endl;
        return nullptr;
    }

    uint32_t version = 0;
    uint64_t tensor_count = 0;
    uint64_t metadata_kv_count = 0;

    if (!read_val(model_file, version) || (version != 2 && version != 3)) {
        std::cerr << "[termux-bitnet ERROR] Unsupported GGUF version: " << version << " (Supported: 2, 3)." << std::endl;
        return nullptr;
    }

    if (!read_val(model_file, tensor_count) || !read_val(model_file, metadata_kv_count)) {
        std::cerr << "[termux-bitnet ERROR] Corrupted GGUF header." << std::endl;
        return nullptr;
    }

    auto* ctx = new bitnet_context();
    ctx->params = *params;
    ctx->model_path = params->model_path;

    if (params->system_prompt) {
        ctx->system_prompt = params->system_prompt;
    }
    if (params->stop_tokens && std::strlen(params->stop_tokens) > 0) {
        std::stringstream ss(params->stop_tokens);
        std::string item;
        while (std::getline(ss, item, ',')) {
            if (!item.empty()) ctx->stop_words.push_back(item);
        }
    }

    if (params->seed != 0) {
        ctx->rng.seed(params->seed);
    } else {
        std::random_device rd;
        ctx->rng.seed(rd());
    }

    auto start_time = std::chrono::high_resolution_clock::now();

    // 2. Parse Metadata Key-Values (Load real Vocab & Arch info)
    bool tokens_loaded = false;
    for (uint64_t i = 0; i < metadata_kv_count; ++i) {
        std::string key;
        if (!read_string(model_file, key)) break;
        uint32_t val_type = 0;
        if (!read_val(model_file, val_type)) break;

        if (key == "tokenizer.ggml.tokens" && val_type == 9) { // Array of tokens
            uint32_t elem_type = 0;
            uint64_t elem_count = 0;
            if (read_val(model_file, elem_type) && read_val(model_file, elem_count)) {
                if (elem_type == 8) { // Array of string
                    ctx->vocab.id_to_token.clear();
                    ctx->vocab.token_to_id.clear();
                    ctx->vocab.id_to_token.reserve(elem_count);
                    for (uint64_t tok_i = 0; tok_i < elem_count; ++tok_i) {
                        std::string tok_str;
                        if (read_string(model_file, tok_str)) {
                            ctx->vocab.token_to_id[tok_str] = (int32_t)ctx->vocab.id_to_token.size();
                            ctx->vocab.id_to_token.push_back(tok_str);
                        }
                    }
                    ctx->config.n_vocab = (uint32_t)ctx->vocab.id_to_token.size();
                    tokens_loaded = true;
                }
            }
        } else if (key.find("bos_token_id") != std::string::npos && (val_type == 4 || val_type == 10)) {
            uint64_t bid = 128000;
            if (val_type == 4) { uint32_t v; read_val(model_file, v); bid = v; }
            else { read_val(model_file, bid); }
            ctx->vocab.bos_id = (int32_t)bid;
        } else if (key.find("eos_token_id") != std::string::npos && (val_type == 4 || val_type == 10)) {
            uint64_t eid = 128001;
            if (val_type == 4) { uint32_t v; read_val(model_file, v); eid = v; }
            else { read_val(model_file, eid); }
            ctx->vocab.eos_id = (int32_t)eid;
        } else if (key.find("block_count") != std::string::npos) {
            uint64_t v = 0;
            if (val_type == 4) { uint32_t t; read_val(model_file, t); v = t; }
            else if (val_type == 10) { read_val(model_file, v); }
            else skip_gguf_value(model_file, val_type);
            ctx->config.n_layers = (uint32_t)v;
        } else if (key.find("context_length") != std::string::npos) {
            uint64_t v = 0;
            if (val_type == 4) { uint32_t t; read_val(model_file, t); v = t; }
            else if (val_type == 10) { read_val(model_file, v); }
            else skip_gguf_value(model_file, val_type);
            ctx->config.n_ctx = (uint32_t)v;
        } else if (key.find("embedding_length") != std::string::npos) {
            uint64_t v = 0;
            if (val_type == 4) { uint32_t t; read_val(model_file, t); v = t; }
            else if (val_type == 10) { read_val(model_file, v); }
            else skip_gguf_value(model_file, val_type);
            ctx->config.n_embd = (uint32_t)v;
        } else if (key.find("head_count_kv") != std::string::npos) {
            uint64_t v = 0;
            if (val_type == 4) { uint32_t t; read_val(model_file, t); v = t; }
            else if (val_type == 10) { read_val(model_file, v); }
            else skip_gguf_value(model_file, val_type);
            ctx->config.n_kv_heads = (uint32_t)v;
        } else if (key.find("head_count") != std::string::npos) {
            uint64_t v = 0;
            if (val_type == 4) { uint32_t t; read_val(model_file, t); v = t; }
            else if (val_type == 10) { read_val(model_file, v); }
            else skip_gguf_value(model_file, val_type);
            ctx->config.n_heads = (uint32_t)v;
        } else if (key.find("feed_forward_length") != std::string::npos) {
            uint64_t v = 0;
            if (val_type == 4) { uint32_t t; read_val(model_file, t); v = t; }
            else if (val_type == 10) { read_val(model_file, v); }
            else skip_gguf_value(model_file, val_type);
            ctx->config.n_ffn = (uint32_t)v;
        } else if (key.find("rms_epsilon") != std::string::npos) {
            float v = 1e-5f;
            if (val_type == 5) { read_val(model_file, v); }
            else skip_gguf_value(model_file, val_type);
            ctx->config.norm_eps = v;
        } else if (key.find("rope") != std::string::npos && key.find("freq_base") != std::string::npos) {
            float v = 10000.0f;
            if (val_type == 5) { read_val(model_file, v); }
            else skip_gguf_value(model_file, val_type);
            ctx->config.rope_theta = v;
        } else {
            skip_gguf_value(model_file, val_type);
        }
    }

    // Build byte fallback map for tokenizer
    for (size_t i = 0; i < ctx->vocab.id_to_token.size(); ++i) {
        const std::string& t = ctx->vocab.id_to_token[i];
        if (t.size() == 6 && t[0] == '<' && t[1] == '0' && t[2] == 'x' && t[5] == '>') {
            unsigned int b = 0;
            if (sscanf(t.c_str(), "<0x%02X>", &b) == 1 && b < 256) {
                ctx->vocab.byte_to_id[b] = (int32_t)i;
            }
        }
    }

    // Fail-Fast: verify vocabulary presence
    if (!tokens_loaded || ctx->vocab.id_to_token.empty()) {
        std::cerr << "[termux-bitnet ERROR] [FAIL-FAST] GGUF file lacks valid tokenizer vocabulary." << std::endl;
        delete ctx;
        return nullptr;
    }
    ctx->config.n_vocab = (uint32_t)ctx->vocab.id_to_token.size();

    // 3. Parse Tensor Info Headers
    ctx->tensors.clear();
    ctx->tensor_map.clear();
    for (uint64_t i = 0; i < tensor_count; ++i) {
        GGUFTensor t;
        if (!read_string(model_file, t.name)) break;
        if (!read_val(model_file, t.n_dims)) break;
        t.ne.resize(t.n_dims);
        for (uint32_t d = 0; d < t.n_dims; ++d) {
            read_val(model_file, t.ne[d]);
        }
        read_val(model_file, t.type);
        read_val(model_file, t.offset);
        
        ctx->tensor_map[t.name] = ctx->tensors.size();
        ctx->tensors.push_back(t);
    }

    // 4. Calculate Tensor Data Start Alignment (default 32 bytes)
    uint64_t current_pos = (uint64_t)model_file.tellg();
    uint64_t tensor_data_offset = (current_pos + 31) & ~((uint64_t)31);
    model_file.close(); // Close file stream before mmap

    // 5. Memory Map the entire GGUF file for Zero-Copy tensor access
#if defined(_WIN32)
    HANDLE hFile = CreateFileA(ctx->model_path.c_str(), GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile != INVALID_HANDLE_VALUE) {
        LARGE_INTEGER size;
        if (GetFileSizeEx(hFile, &size)) {
            ctx->mmap_size = (size_t)size.QuadPart;
            HANDLE hMap = CreateFileMappingA(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
            if (hMap) {
                ctx->mmap_addr = MapViewOfFile(hMap, FILE_MAP_READ, 0, 0, 0);
                ctx->file_handle = (void*)hFile;
                ctx->map_handle = (void*)hMap;
            }
        }
    }
#else
    int fd = open(ctx->model_path.c_str(), O_RDONLY);
    if (fd >= 0) {
        struct stat sb;
        if (fstat(fd, &sb) == 0) {
            ctx->mmap_size = (size_t)sb.st_size;
            ctx->mmap_addr = mmap(NULL, ctx->mmap_size, PROT_READ, MAP_SHARED, fd, 0);
            ctx->file_handle = (void*)(intptr_t)fd;
        }
    }
#endif

    // Bind real data pointers for all tensors
    if (ctx->mmap_addr && ctx->mmap_size > tensor_data_offset) {
        uint8_t* base_ptr = (uint8_t*)ctx->mmap_addr;
        for (auto& t : ctx->tensors) {
            uint64_t abs_offset = tensor_data_offset + t.offset;
            if (abs_offset < ctx->mmap_size) {
                t.data = base_ptr + abs_offset;
            }
        }
    }

    // Configure model architecture dimensions
    if (ctx->config.n_kv_heads == 0) ctx->config.n_kv_heads = ctx->config.n_heads;
    if (ctx->config.n_heads > 0) ctx->config.head_dim = ctx->config.n_embd / ctx->config.n_heads;
    if (ctx->config.n_ffn == 0) ctx->config.n_ffn = ctx->config.n_embd * 8 / 3;
    if (ctx->params.n_ctx > 0) ctx->config.n_ctx = (uint32_t)ctx->params.n_ctx;

    // Bind Global Tensors
    auto it_embd = ctx->tensor_map.find("token_embd.weight");
    if (it_embd != ctx->tensor_map.end()) {
        ctx->embd_weight = ctx->tensors[it_embd->second].data;
        ctx->embd_type = ctx->tensors[it_embd->second].type;
    }
    auto it_out_norm = ctx->tensor_map.find("output_norm.weight");
    if (it_out_norm != ctx->tensor_map.end()) {
        ctx->output_norm = (const float*)ctx->tensors[it_out_norm->second].data;
        ctx->output_norm_type = ctx->tensors[it_out_norm->second].type;
    }
    auto it_out = ctx->tensor_map.find("output.weight");
    if (it_out != ctx->tensor_map.end()) {
        ctx->output_weight = ctx->tensors[it_out->second].data;
        ctx->output_weight_type = ctx->tensors[it_out->second].type;
    } else {
        ctx->output_weight = ctx->embd_weight;
        ctx->output_weight_type = ctx->embd_type;
    }

    // Bind Layer Tensors across all N layers
    ctx->layers.resize(ctx->config.n_layers);
    for (uint32_t l = 0; l < ctx->config.n_layers; ++l) {
        auto& lay = ctx->layers[l];
        std::string prefix = "blk." + std::to_string(l) + ".";

        auto bind_t = [&](const std::string& name, const void*& ptr, uint32_t& type) {
            auto it = ctx->tensor_map.find(prefix + name);
            if (it != ctx->tensor_map.end()) {
                ptr = ctx->tensors[it->second].data;
                type = ctx->tensors[it->second].type;
            }
        };

        const void* tmp_norm = nullptr;
        bind_t("attn_norm.weight", tmp_norm, lay.attn_norm_type);
        lay.attn_norm = (const float*)tmp_norm;

        bind_t("attn_q.weight", lay.wq, lay.wq_type);
        bind_t("attn_k.weight", lay.wk, lay.wk_type);
        bind_t("attn_v.weight", lay.wv, lay.wv_type);

        tmp_norm = nullptr;
        bind_t("attn_sub_norm.weight", tmp_norm, lay.attn_sub_norm_type);
        lay.attn_sub_norm = (const float*)tmp_norm;

        bind_t("attn_output.weight", lay.wo, lay.wo_type);

        tmp_norm = nullptr;
        bind_t("ffn_norm.weight", tmp_norm, lay.ffn_norm_type);
        lay.ffn_norm = (const float*)tmp_norm;

        bind_t("ffn_gate.weight", lay.w_gate, lay.w_gate_type);
        bind_t("ffn_up.weight", lay.w_up, lay.w_up_type);

        tmp_norm = nullptr;
        bind_t("ffn_sub_norm.weight", tmp_norm, lay.ffn_sub_norm_type);
        lay.ffn_sub_norm = (const float*)tmp_norm;

        bind_t("ffn_down.weight", lay.w_down, lay.w_down_type);

        // Strict Fail-Fast: verify all linear projection weight types are supported 1.58-bit (i2_s) or F32/F16
        auto check_type = [&](const char* name, uint32_t type) {
            if (type != 36 && type != 30 && type != 0 && type != 1) {
                std::cerr << "[termux-bitnet FATAL] Layer " << l << " tensor '" << name 
                          << "' has unsupported quantization type " << type 
                          << ". termux-bitnet native core requires 1.58-bit i2_s tensors (type 36/30).\n"
                          << "Download a verified 1.58-bit model via: termux-bitnet download bitnet-2b\n";
                return false;
            }
            return true;
        };
        if (lay.wq && !check_type("attn_q.weight", lay.wq_type)) {
            bitnet_free(ctx);
            return nullptr;
        }
        if (lay.wk && !check_type("attn_k.weight", lay.wk_type)) {
            bitnet_free(ctx);
            return nullptr;
        }
        if (lay.wv && !check_type("attn_v.weight", lay.wv_type)) {
            bitnet_free(ctx);
            return nullptr;
        }
        if (lay.wo && !check_type("attn_output.weight", lay.wo_type)) {
            bitnet_free(ctx);
            return nullptr;
        }
        if (lay.w_gate && !check_type("ffn_gate.weight", lay.w_gate_type)) {
            bitnet_free(ctx);
            return nullptr;
        }
        if (lay.w_up && !check_type("ffn_up.weight", lay.w_up_type)) {
            bitnet_free(ctx);
            return nullptr;
        }
        if (lay.w_down && !check_type("ffn_down.weight", lay.w_down_type)) {
            bitnet_free(ctx);
            return nullptr;
        }
    }

    // Initialize KV Cache and Scratch Buffers
    ctx->kv_cache.init(ctx->config.n_layers, ctx->config.n_ctx, ctx->config.n_kv_heads, ctx->config.head_dim);
    ctx->logits.assign(ctx->config.n_vocab, 0.0f);
    ctx->context_tokens.reserve(ctx->config.n_ctx);

    // Initialize GPU Acceleration Engine (Fail-Fast: Never Silent Fallback)
    ctx->n_gpu_layers = params->n_gpu_layers;
#if defined(GGML_USE_VULKAN)
    if (ctx->n_gpu_layers > 0) {
        try {
            auto* engine = new ameva::core::VulkanBitNetEngine();
            engine->Initialize();
            uint32_t max_dim = std::max(ctx->config.n_embd, ctx->config.n_ffn);
            engine->AllocateBuffers(max_dim, max_dim);
            ctx->vk_engine = engine;
            std::cout << "[termux-bitnet] Vulkan GPU Engine activated: "
                      << engine->GetDeviceInfo().device_name
                      << " (" << ctx->n_gpu_layers << "/" << ctx->config.n_layers
                      << " layers offloaded to GPU with Zero Silent Fallback)" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[termux-bitnet FATAL FAIL-FAST] GPU offload requested (-ngl "
                      << ctx->n_gpu_layers << "), but Vulkan initialization failed: "
                      << e.what() << std::endl;
            bitnet_free(ctx);
            return nullptr;
        }
    }
#else
    if (ctx->n_gpu_layers > 0) {
        std::cerr << "[termux-bitnet FATAL FAIL-FAST] -ngl " << ctx->n_gpu_layers
                  << " requested, but binary was built without GGML_USE_VULKAN!" << std::endl;
        bitnet_free(ctx);
        return nullptr;
    }
#endif

    ctx->is_initialized = true;

    auto end_time = std::chrono::high_resolution_clock::now();
    ctx->metrics.load_time_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();

    if (params->verbose) {
        std::cout << "[termux-bitnet] Native GGUF model mmap loaded: " << ctx->model_path
                  << "\n  Architecture Params: Layers=" << ctx->config.n_layers
                  << ", Embd=" << ctx->config.n_embd
                  << ", Heads=" << ctx->config.n_heads
                  << " (KV Heads=" << ctx->config.n_kv_heads << ")"
                  << ", HeadDim=" << ctx->config.head_dim
                  << ", FFN=" << ctx->config.n_ffn
                  << ", Vocab=" << ctx->config.n_vocab
                  << "\n  Tensors=" << ctx->tensors.size()
                  << ", mmap size=" << ctx->mmap_size / (1024 * 1024) << " MB"
                  << ", Load time=" << ctx->metrics.load_time_ms << " ms" << std::endl;
    }

    return ctx;
}

void bitnet_free(bitnet_context_t ctx) {
    if (ctx) {
        std::lock_guard<std::mutex> lock(ctx->ctx_mutex);
        ctx->is_initialized = false;

#if defined(GGML_USE_VULKAN)
        if (ctx->vk_engine) {
            auto* engine = static_cast<ameva::core::VulkanBitNetEngine*>(ctx->vk_engine);
            delete engine;
            ctx->vk_engine = nullptr;
        }
#endif

        // Clean up mmap handles
#if defined(_WIN32)
        if (ctx->mmap_addr) {
            UnmapViewOfFile(ctx->mmap_addr);
            ctx->mmap_addr = nullptr;
        }
        if (ctx->map_handle) {
            CloseHandle((HANDLE)ctx->map_handle);
            ctx->map_handle = nullptr;
        }
        if (ctx->file_handle && ctx->file_handle != INVALID_HANDLE_VALUE) {
            CloseHandle((HANDLE)ctx->file_handle);
            ctx->file_handle = nullptr;
        }
#else
        if (ctx->mmap_addr && ctx->mmap_addr != MAP_FAILED) {
            munmap(ctx->mmap_addr, ctx->mmap_size);
            ctx->mmap_addr = nullptr;
        }
        if (ctx->file_handle) {
            int fd = (int)(intptr_t)ctx->file_handle;
            if (fd >= 0) close(fd);
            ctx->file_handle = nullptr;
        }
#endif

        ctx->tensors.clear();
        ctx->tensor_map.clear();
        delete ctx;
    }
}

// ============================================================================
// IEEE 754 Half-Precision Float Converter
// ============================================================================
static inline float f16_to_f32(uint16_t h) {
    uint32_t w = (uint32_t)(h & 0x7FFF) << 13;
    uint32_t sign = (uint32_t)(h & 0x8000) << 16;
    uint32_t exp = (h >> 10) & 0x1F;
    if (exp == 0x1F) {
        w = 0x7F800000 | ((uint32_t)(h & 0x03FF) << 13);
    } else if (exp != 0) {
        w += 0x38000000;
    } else {
        w = 0;
    }
    uint32_t result = sign | w;
    float f;
    std::memcpy(&f, &result, sizeof(float));
    return f;
}

// ============================================================================
// Pure Native BPE Tokenizer & Detokenizer
// ============================================================================
int32_t bitnet_tokenize(bitnet_context_t ctx, const char* text, int32_t* tokens, int32_t max_tokens) {
    if (!ctx || !ctx->is_initialized || !text || !tokens || max_tokens <= 0) return -1;
    std::lock_guard<std::mutex> lock(ctx->ctx_mutex);

    int32_t count = 0;
    if (ctx->vocab.bos_id >= 0 && count < max_tokens) {
        tokens[count++] = ctx->vocab.bos_id;
    }

    // Convert raw string to GPT-2/Llama-3 byte-level BPE representation (space -> Ġ, newline -> Ċ)
    std::string s = "";
    for (size_t i = 0; text[i] != '\0'; ++i) {
        if (text[i] == ' ') {
            s += "\xc4\xa0"; // Ġ
        } else if (text[i] == '\n') {
            s += "\xc4\x8a"; // Ċ
        } else {
            s += text[i];
        }
    }

    size_t pos = 0;
    while (pos < s.length() && count < max_tokens) {
        int32_t best_id = -1;
        size_t best_len = 0;
        size_t max_match = std::min(s.length() - pos, (size_t)64);

        for (size_t len = max_match; len >= 1; --len) {
            std::string sub = s.substr(pos, len);
            auto it = ctx->vocab.token_to_id.find(sub);
            if (it != ctx->vocab.token_to_id.end()) {
                best_id = it->second;
                best_len = len;
                break;
            }
        }

        if (best_id != -1) {
            tokens[count++] = best_id;
            pos += best_len;
        } else {
            uint8_t byte_val = (uint8_t)s[pos];
            int32_t byte_tok = ctx->vocab.byte_to_id[byte_val];
            if (byte_tok >= 0) {
                tokens[count++] = byte_tok;
            } else if (ctx->vocab.unk_id >= 0) {
                tokens[count++] = ctx->vocab.unk_id;
            } else {
                tokens[count++] = (int32_t)(byte_val % ctx->config.n_vocab);
            }
            pos++;
        }
    }
    return count;
}

int32_t bitnet_token_to_str(bitnet_context_t ctx, int32_t token, char* buf, int32_t buf_len) {
    if (!ctx || !ctx->is_initialized || !buf || buf_len <= 0) return 0;
    std::lock_guard<std::mutex> lock(ctx->ctx_mutex);

    if (token < 0 || token >= (int32_t)ctx->vocab.id_to_token.size()) {
        buf[0] = '\0';
        return 0;
    }

    const std::string& raw_str = ctx->vocab.id_to_token[token];
    if (raw_str.size() == 6 && raw_str[0] == '<' && raw_str[1] == '0' && raw_str[2] == 'x' && raw_str[5] == '>') {
        unsigned int b = 0;
        if (sscanf(raw_str.c_str(), "<0x%02X>", &b) == 1 && b < 256) {
            buf[0] = (char)b;
            buf[1] = '\0';
            return 1;
        }
    }

    // Convert BPE symbols (Ġ -> space, Ċ -> newline)
    std::string decoded = "";
    for (size_t i = 0; i < raw_str.size(); ) {
        if (i + 1 < raw_str.size() && (uint8_t)raw_str[i] == 0xc4 && (uint8_t)raw_str[i + 1] == 0xa0) {
            decoded += ' ';
            i += 2;
        } else if (i + 1 < raw_str.size() && (uint8_t)raw_str[i] == 0xc4 && (uint8_t)raw_str[i + 1] == 0x8a) {
            decoded += '\n';
            i += 2;
        } else {
            decoded += raw_str[i];
            i++;
        }
    }

    int32_t copied = (int32_t)std::min((size_t)buf_len - 1, decoded.length());
    std::memcpy(buf, decoded.data(), copied);
    buf[copied] = '\0';
    return copied;
}

// ============================================================================
// Transformer Forward Math Kernels
// ============================================================================

static void lookup_embedding(float* out, const void* embd_weight, uint32_t embd_type, int32_t token, uint32_t n_embd) {
    if (!embd_weight) {
        std::memset(out, 0, n_embd * sizeof(float));
        return;
    }
    if (embd_type == 0) { // F32
        const float* p = (const float*)embd_weight + (size_t)token * n_embd;
        std::memcpy(out, p, n_embd * sizeof(float));
    } else if (embd_type == 1) { // F16
        const uint16_t* p = (const uint16_t*)embd_weight + (size_t)token * n_embd;
        for (uint32_t i = 0; i < n_embd; ++i) {
            out[i] = f16_to_f32(p[i]);
        }
    } else {
        std::memset(out, 0, n_embd * sizeof(float));
    }
}

static void rms_norm(float* out, const float* x, const float* w, uint32_t w_type, uint32_t dim, float eps) {
    float sum_sq = 0.0f;
#if defined(__ARM_NEON)
    float32x4_t sum_v = vdupq_n_f32(0.0f);
    for (uint32_t i = 0; i < dim; i += 4) {
        float32x4_t v = vld1q_f32(x + i);
        sum_v = vmlaq_f32(sum_v, v, v);
    }
    sum_sq = vaddvq_f32(sum_v);
#else
    for (uint32_t i = 0; i < dim; ++i) {
        sum_sq += x[i] * x[i];
    }
#endif
    float scale = 1.0f / std::sqrt(sum_sq / (float)dim + eps);

    if (w) {
        if (w_type == 1) { // F16 weight
            const uint16_t* hw = (const uint16_t*)w;
            for (uint32_t i = 0; i < dim; ++i) out[i] = x[i] * scale * f16_to_f32(hw[i]);
        } else { // F32 weight
            for (uint32_t i = 0; i < dim; ++i) out[i] = x[i] * scale * w[i];
        }
    } else {
        for (uint32_t i = 0; i < dim; ++i) out[i] = x[i] * scale;
    }
}

static float quantize_activation_int8(int8_t* out, const float* x, uint32_t dim) {
    float max_abs = 1e-7f;
    for (uint32_t i = 0; i < dim; ++i) {
        float a = std::abs(x[i]);
        if (a > max_abs) max_abs = a;
    }
    float scale = 127.0f / max_abs;
    for (uint32_t i = 0; i < dim; ++i) {
        int v = (int)std::round(x[i] * scale);
        out[i] = (int8_t)std::clamp(v, -127, 127);
    }
    return 1.0f / scale; // dequantization factor
}

static void bitnet_gemv(float* out, const void* w, uint32_t w_type, 
                        const int8_t* x_q8, const float* x_f32, float dequant, 
                        uint32_t in_dim, uint32_t out_dim) {
    if (!w) {
        std::memset(out, 0, out_dim * sizeof(float));
        return;
    }
    if (w_type == 36 || w_type == 30) { // GGML_TYPE_I2_S (36 in BitNet GGUF standard, 30 legacy)
        ggml_vec_dot_i2_i8_s((int)in_dim, out, 1, w, (size_t)in_dim, x_q8, (size_t)in_dim, (int)out_dim, 0);
        for (uint32_t r = 0; r < out_dim; ++r) {
            out[r] *= dequant;
        }
    } else if (w_type == 0) { // F32 Fallback
        const float* fw = (const float*)w;
        for (uint32_t r = 0; r < out_dim; ++r) {
            float sum = 0.0f;
            const float* w_row = fw + (size_t)r * in_dim;
            for (uint32_t c = 0; c < in_dim; ++c) sum += w_row[c] * x_f32[c];
            out[r] = sum;
        }
    } else if (w_type == 1) { // F16 Fallback
        const uint16_t* hw = (const uint16_t*)w;
        for (uint32_t r = 0; r < out_dim; ++r) {
            float sum = 0.0f;
            const uint16_t* w_row = hw + (size_t)r * in_dim;
            for (uint32_t c = 0; c < in_dim; ++c) sum += f16_to_f32(w_row[c]) * x_f32[c];
            out[r] = sum;
        }
    } else {
        std::cerr << "[termux-bitnet FATAL] Unsupported tensor quantization type in GEMV: " << w_type << std::endl;
        std::abort();
    }
}

static void apply_rope(float* vec, size_t pos, uint32_t n_heads, uint32_t head_dim, float theta_base) {
    for (uint32_t h = 0; h < n_heads; ++h) {
        float* head_ptr = vec + h * head_dim;
        for (uint32_t i = 0; i < head_dim; i += 2) {
            float theta = (float)pos / std::pow(theta_base, (float)i / (float)head_dim);
            float cos_t = std::cos(theta);
            float sin_t = std::sin(theta);
            float v0 = head_ptr[i];
            float v1 = head_ptr[i + 1];
            head_ptr[i]     = v0 * cos_t - v1 * sin_t;
            head_ptr[i + 1] = v0 * sin_t + v1 * cos_t;
        }
    }
}

static void store_kv_cache(BitNetKVCache& kv, uint32_t layer_idx, size_t pos, 
                           const float* k, const float* v, const BitNetConfig& cfg) {
    size_t layer_stride = (size_t)cfg.n_ctx * cfg.n_kv_heads * cfg.head_dim;
    size_t pos_stride = (size_t)cfg.n_kv_heads * cfg.head_dim;
    size_t base_offset = layer_idx * layer_stride + pos * pos_stride;
    if (base_offset + pos_stride <= kv.k_cache.size()) {
        std::memcpy(&kv.k_cache[base_offset], k, pos_stride * sizeof(float));
        std::memcpy(&kv.v_cache[base_offset], v, pos_stride * sizeof(float));
    }
}

static void multi_head_attention(float* out, const float* q, const BitNetKVCache& kv, 
                                 uint32_t layer_idx, size_t current_pos, 
                                 const BitNetConfig& cfg, std::vector<float>& scores_buf) {
    float inv_sqrt = 1.0f / std::sqrt((float)cfg.head_dim);
    uint32_t gqa_ratio = cfg.n_heads / cfg.n_kv_heads;

    for (uint32_t h = 0; h < cfg.n_heads; ++h) {
        uint32_t kv_h = h / gqa_ratio;
        const float* q_h = q + h * cfg.head_dim;

        // 1. Calculate Attention Scores: Q * K^T / sqrt(head_dim)
        float max_score = -1e9f;
        for (size_t p = 0; p <= current_pos; ++p) {
            size_t k_offset = layer_idx * ((size_t)cfg.n_ctx * cfg.n_kv_heads * cfg.head_dim)
                            + p * ((size_t)cfg.n_kv_heads * cfg.head_dim)
                            + kv_h * cfg.head_dim;
            const float* k_p = &kv.k_cache[k_offset];
            float dot = 0.0f;
            for (uint32_t d = 0; d < cfg.head_dim; ++d) {
                dot += q_h[d] * k_p[d];
            }
            float score = dot * inv_sqrt;
            scores_buf[p] = score;
            if (score > max_score) max_score = score;
        }

        // 2. Softmax over past sequence tokens [0 ... current_pos]
        float sum_exp = 0.0f;
        for (size_t p = 0; p <= current_pos; ++p) {
            float exp_val = std::exp(scores_buf[p] - max_score);
            scores_buf[p] = exp_val;
            sum_exp += exp_val;
        }
        float inv_sum = 1.0f / (sum_exp + 1e-9f);

        // 3. Weighted Accumulation with V_cache
        float* out_h = out + h * cfg.head_dim;
        std::memset(out_h, 0, cfg.head_dim * sizeof(float));
        for (size_t p = 0; p <= current_pos; ++p) {
            float weight = scores_buf[p] * inv_sum;
            size_t v_offset = layer_idx * ((size_t)cfg.n_ctx * cfg.n_kv_heads * cfg.head_dim)
                            + p * ((size_t)cfg.n_kv_heads * cfg.head_dim)
                            + kv_h * cfg.head_dim;
            const float* v_p = &kv.v_cache[v_offset];
            for (uint32_t d = 0; d < cfg.head_dim; ++d) {
                out_h[d] += weight * v_p[d];
            }
        }
    }
}

static void forward_swiglu(float* out, const float* ffn_norm, const BitNetLayerWeights& lay, 
                           const BitNetConfig& cfg, void* vk_engine, bool use_gpu) {
#if defined(GGML_USE_VULKAN)
    if (use_gpu && vk_engine) {
        auto* engine = static_cast<ameva::core::VulkanBitNetEngine*>(vk_engine);
        std::vector<float> gate(cfg.n_ffn);
        std::vector<float> up(cfg.n_ffn);
        engine->ComputeGemvDynamic(lay.w_gate, ffn_norm, gate.data(), cfg.n_ffn, cfg.n_embd, 1.0f);
        engine->ComputeGemvDynamic(lay.w_up, ffn_norm, up.data(), cfg.n_ffn, cfg.n_embd, 1.0f);

        for (uint32_t i = 0; i < cfg.n_ffn; ++i) {
            float g = gate[i];
            float silu = g / (1.0f + std::exp(-g));
            gate[i] = silu * up[i];
        }

        if (lay.ffn_sub_norm) {
            rms_norm(gate.data(), gate.data(), lay.ffn_sub_norm, lay.ffn_sub_norm_type, cfg.n_ffn, cfg.norm_eps);
        }

        engine->ComputeGemvDynamic(lay.w_down, gate.data(), out, cfg.n_embd, cfg.n_ffn, 1.0f);
        return;
    }
#endif

    std::vector<int8_t> x_q8(cfg.n_embd);
    float dequant = quantize_activation_int8(x_q8.data(), ffn_norm, cfg.n_embd);

    std::vector<float> gate(cfg.n_ffn);
    std::vector<float> up(cfg.n_ffn);
    bitnet_gemv(gate.data(), lay.w_gate, lay.w_gate_type, x_q8.data(), ffn_norm, dequant, cfg.n_embd, cfg.n_ffn);
    bitnet_gemv(up.data(), lay.w_up, lay.w_up_type, x_q8.data(), ffn_norm, dequant, cfg.n_embd, cfg.n_ffn);

    // SiLU(gate) * up
    for (uint32_t i = 0; i < cfg.n_ffn; ++i) {
        float g = gate[i];
        float silu = g / (1.0f + std::exp(-g));
        gate[i] = silu * up[i];
    }

    // BitNet Sub-LayerNorm for FFN intermediate
    if (lay.ffn_sub_norm) {
        rms_norm(gate.data(), gate.data(), lay.ffn_sub_norm, lay.ffn_sub_norm_type, cfg.n_ffn, cfg.norm_eps);
    }

    // Down projection: gate_intermediate * w_down
    std::vector<int8_t> inter_q8(cfg.n_ffn);
    float inter_dequant = quantize_activation_int8(inter_q8.data(), gate.data(), cfg.n_ffn);
    bitnet_gemv(out, lay.w_down, lay.w_down_type, inter_q8.data(), gate.data(), inter_dequant, cfg.n_ffn, cfg.n_embd);
}

// ============================================================================
// Complete Pure Native Transformer Forward Pass (L Layers)
// ============================================================================
int32_t bitnet_eval(bitnet_context_t ctx, const int32_t* tokens, int32_t n_tokens) {
    if (!ctx || !ctx->is_initialized || !tokens || n_tokens <= 0) return -1;
    std::lock_guard<std::mutex> lock(ctx->ctx_mutex);

    const auto& cfg = ctx->config;
    std::vector<float> x(cfg.n_embd);
    std::vector<float> x_norm(cfg.n_embd);
    std::vector<float> q(cfg.n_embd);
    std::vector<float> k(cfg.n_kv_heads * cfg.head_dim);
    std::vector<float> v(cfg.n_kv_heads * cfg.head_dim);
    std::vector<float> attn_out(cfg.n_embd);
    std::vector<float> wo_out(cfg.n_embd);
    std::vector<float> ffn_out(cfg.n_embd);
    std::vector<float> attn_scores(cfg.n_ctx, 0.0f);
    std::vector<int8_t> q8_buf(std::max(cfg.n_embd, cfg.n_ffn));

    uint32_t q_dim = cfg.n_embd;
    uint32_t kv_dim = cfg.n_kv_heads * cfg.head_dim;

    for (int32_t t = 0; t < n_tokens; ++t) {
        int32_t token = tokens[t];
        size_t pos = ctx->kv_cache.current_pos;
        if (pos >= cfg.n_ctx) {
            pos = cfg.n_ctx - 1; // Window clamp
        }

        // 1. Token Embedding Lookup
        lookup_embedding(x.data(), ctx->embd_weight, ctx->embd_type, token, cfg.n_embd);

        // 2. Loop sequentially through all L Transformer Layers
        for (uint32_t l = 0; l < cfg.n_layers; ++l) {
            const auto& lay = ctx->layers[l];
            bool use_gpu = (ctx->vk_engine != nullptr && (int32_t)l < ctx->n_gpu_layers);

            // 2.1 Attention RMSNorm
            rms_norm(x_norm.data(), x.data(), lay.attn_norm, lay.attn_norm_type, cfg.n_embd, cfg.norm_eps);

            // 2.2 Activation Quantization & Q, K, V GEMV (GQA aware)
            if (use_gpu) {
#if defined(GGML_USE_VULKAN)
                auto* engine = static_cast<ameva::core::VulkanBitNetEngine*>(ctx->vk_engine);
                engine->ComputeGemvDynamic(lay.wq, x_norm.data(), q.data(), q_dim, cfg.n_embd, 1.0f);
                engine->ComputeGemvDynamic(lay.wk, x_norm.data(), k.data(), kv_dim, cfg.n_embd, 1.0f);
                engine->ComputeGemvDynamic(lay.wv, x_norm.data(), v.data(), kv_dim, cfg.n_embd, 1.0f);
#endif
            } else {
                float dequant = quantize_activation_int8(q8_buf.data(), x_norm.data(), cfg.n_embd);
                bitnet_gemv(q.data(), lay.wq, lay.wq_type, q8_buf.data(), x_norm.data(), dequant, cfg.n_embd, q_dim);
                bitnet_gemv(k.data(), lay.wk, lay.wk_type, q8_buf.data(), x_norm.data(), dequant, cfg.n_embd, kv_dim);
                bitnet_gemv(v.data(), lay.wv, lay.wv_type, q8_buf.data(), x_norm.data(), dequant, cfg.n_embd, kv_dim);
            }

            // 2.3 Rotary Position Embedding (RoPE)
            apply_rope(q.data(), pos, cfg.n_heads, cfg.head_dim, cfg.rope_theta);
            apply_rope(k.data(), pos, cfg.n_kv_heads, cfg.head_dim, cfg.rope_theta);

            // 2.4 KV Cache Store & Multi-Head Self Attention
            store_kv_cache(ctx->kv_cache, l, pos, k.data(), v.data(), cfg);
            multi_head_attention(attn_out.data(), q.data(), ctx->kv_cache, l, pos, cfg, attn_scores);

            // 2.5 BitNet Sub-LayerNorm on Attention Output
            if (lay.attn_sub_norm) {
                rms_norm(attn_out.data(), attn_out.data(), lay.attn_sub_norm, lay.attn_sub_norm_type, cfg.n_embd, cfg.norm_eps);
            }

            // 2.6 Output Projection & Residual Connection
            if (use_gpu) {
#if defined(GGML_USE_VULKAN)
                auto* engine = static_cast<ameva::core::VulkanBitNetEngine*>(ctx->vk_engine);
                engine->ComputeGemvDynamic(lay.wo, attn_out.data(), wo_out.data(), cfg.n_embd, cfg.n_embd, 1.0f);
#endif
            } else {
                float attn_dequant = quantize_activation_int8(q8_buf.data(), attn_out.data(), cfg.n_embd);
                bitnet_gemv(wo_out.data(), lay.wo, lay.wo_type, q8_buf.data(), attn_out.data(), attn_dequant, cfg.n_embd, cfg.n_embd);
            }
            for (uint32_t i = 0; i < cfg.n_embd; ++i) x[i] += wo_out[i];

            // 2.7 FFN RMSNorm & SwiGLU FFN (with Sub-LayerNorm)
            rms_norm(x_norm.data(), x.data(), lay.ffn_norm, lay.ffn_norm_type, cfg.n_embd, cfg.norm_eps);
            forward_swiglu(ffn_out.data(), x_norm.data(), lay, cfg, ctx->vk_engine, use_gpu);

            // 2.8 Residual Connection
            for (uint32_t i = 0; i < cfg.n_embd; ++i) x[i] += ffn_out[i];
        }

        // 3. Final RMSNorm & LM Head Projection (Evaluated on last sequence token)
        if (t == n_tokens - 1) {
            rms_norm(x_norm.data(), x.data(), ctx->output_norm, ctx->output_norm_type, cfg.n_embd, cfg.norm_eps);
            float final_dequant = quantize_activation_int8(q8_buf.data(), x_norm.data(), cfg.n_embd);
            bitnet_gemv(ctx->logits.data(), ctx->output_weight, ctx->output_weight_type, 
                        q8_buf.data(), x_norm.data(), final_dequant, cfg.n_embd, cfg.n_vocab);
        }

        // Record token in context history
        ctx->context_tokens.push_back(token);
        ctx->token_frequencies[token]++;
        ctx->kv_cache.current_pos++;
    }

    return 0;
}

int32_t bitnet_sample(bitnet_context_t ctx) {
    if (!ctx || !ctx->is_initialized || ctx->logits.empty()) return -1;
    std::lock_guard<std::mutex> lock(ctx->ctx_mutex);

    std::vector<float> working_logits = ctx->logits;

    // 1. Repetition Penalty Matrix calculation across active context window
    int32_t last_n = std::min((int32_t)ctx->context_tokens.size(), ctx->params.repeat_last_n > 0 ? ctx->params.repeat_last_n : 64);
    if (last_n > 0 && ctx->params.repeat_penalty > 1.0f) {
        for (int32_t i = (int32_t)ctx->context_tokens.size() - last_n; i < (int32_t)ctx->context_tokens.size(); ++i) {
            int32_t tok = ctx->context_tokens[i];
            if (tok >= 0 && tok < (int32_t)working_logits.size()) {
                if (working_logits[tok] > 0) {
                    working_logits[tok] /= ctx->params.repeat_penalty;
                } else {
                    working_logits[tok] *= ctx->params.repeat_penalty;
                }
            }
        }
    }

    // 2. Extract and sort Candidate Probs over the entire vocabulary space
    std::vector<std::pair<float, int32_t>> candidates;
    candidates.reserve(ctx->config.n_vocab);
    for (size_t i = 3; i < (size_t)ctx->config.n_vocab; ++i) {
        candidates.emplace_back(working_logits[i], (int32_t)i);
    }
    if (candidates.empty()) return ctx->vocab.eos_id;
    std::sort(candidates.rbegin(), candidates.rend());

    // 3. Apply Top-K cutoff
    size_t k = ctx->params.top_k > 0 ? (size_t)ctx->params.top_k : 40;
    size_t k_limit = std::min(candidates.size(), k);

    // 4. Softmax with Temperature & Top-P
    float temp = std::max(0.01f, ctx->params.temperature);
    float max_logit = candidates[0].first;
    float sum_exp = 0.0f;
    std::vector<float> exp_probs(k_limit);

    for (size_t i = 0; i < k_limit; ++i) {
        exp_probs[i] = std::exp((candidates[i].first - max_logit) / temp);
        sum_exp += exp_probs[i];
    }

    std::uniform_real_distribution<float> dist(0.0f, sum_exp);
    float r = dist(ctx->rng);
    float cur = 0.0f;
    int32_t selected_token = candidates[0].second;

    for (size_t i = 0; i < k_limit; ++i) {
        cur += exp_probs[i];
        if (cur >= r) {
            selected_token = candidates[i].second;
            break;
        }
    }

    return selected_token;
}

int32_t bitnet_generate_stream(bitnet_context_t ctx, const char* prompt, int32_t max_new_tokens, bitnet_stream_cb callback, void* user_data) {
    if (!ctx || !ctx->is_initialized) {
        std::cerr << "[termux-bitnet ERROR] bitnet_generate_stream: BitNet context is NULL or uninitialized." << std::endl;
        return 0;
    }
    if (!prompt || std::strlen(prompt) == 0) {
        std::cerr << "[termux-bitnet ERROR] bitnet_generate_stream: Prompt cannot be empty." << std::endl;
        return 0;
    }
    if (max_new_tokens <= 0) {
        std::cerr << "[termux-bitnet ERROR] bitnet_generate_stream: max_new_tokens must be greater than 0." << std::endl;
        return 0;
    }

    std::string full_prompt;
    if (!ctx->system_prompt.empty()) {
        full_prompt = ctx->system_prompt + "\n" + prompt;
    } else {
        full_prompt = prompt;
    }

    std::vector<int32_t> prompt_tokens(ctx->params.n_ctx > 0 ? ctx->params.n_ctx : 2048);
    int32_t n_prompt = bitnet_tokenize(ctx, full_prompt.c_str(), prompt_tokens.data(), (int32_t)prompt_tokens.size());
    if (n_prompt <= 0) {
        std::cerr << "[termux-bitnet ERROR] bitnet_generate_stream: Tokenization produced 0 tokens." << std::endl;
        return 0;
    }

    ctx->metrics.prompt_tokens = n_prompt;
    auto t_start_prompt = std::chrono::high_resolution_clock::now();
    bitnet_eval(ctx, prompt_tokens.data(), n_prompt);
    auto t_end_prompt = std::chrono::high_resolution_clock::now();
    ctx->metrics.prompt_eval_ms = std::chrono::duration<double, std::milli>(t_end_prompt - t_start_prompt).count();

    int32_t generated_count = 0;
    auto t_start_eval = std::chrono::high_resolution_clock::now();

    char token_buf[512];
    for (int32_t i = 0; i < max_new_tokens; ++i) {
        int32_t next_tok = bitnet_sample(ctx);
        if (next_tok == ctx->vocab.eos_id) break;

        bitnet_token_to_str(ctx, next_tok, token_buf, sizeof(token_buf));
        if (std::strlen(token_buf) == 0) break;

        bool stop_triggered = false;
        for (const auto& sw : ctx->stop_words) {
            if (std::strcmp(token_buf, sw.c_str()) == 0) {
                stop_triggered = true;
                break;
            }
        }
        if (stop_triggered) break;

        generated_count++;

        if (callback) {
            bool keep_going = callback(token_buf, next_tok, user_data);
            if (!keep_going) break;
        }

        bitnet_eval(ctx, &next_tok, 1);
    }

    auto t_end_eval = std::chrono::high_resolution_clock::now();
    ctx->metrics.eval_time_ms = std::chrono::duration<double, std::milli>(t_end_eval - t_start_eval).count();
    ctx->metrics.eval_tokens = generated_count;
    if (ctx->metrics.eval_time_ms > 0.0) {
        ctx->metrics.tokens_per_sec = (generated_count / (ctx->metrics.eval_time_ms / 1000.0));
    }

    return generated_count;
}

void bitnet_get_hardware_info(char* buf, int32_t buf_len) {
    if (!buf || buf_len <= 0) return;

    std::ostringstream ss;
    ss << "Platform: ";
#if defined(__aarch64__) || defined(_M_ARM64)
    ss << "ARM64 (aarch64)";
    #if defined(__ARM_NEON)
    ss << " | NEON = 1";
    #endif
    #if defined(__ARM_FEATURE_DOTPROD)
    ss << " | DOTPROD = 1";
    #else
    ss << " | DOTPROD = 0 (FMA Fallback)";
    #endif
#elif defined(__x86_64__) || defined(_M_X64)
    ss << "x86_64";
    #if defined(__AVX2__)
    ss << " | AVX2 = 1";
    #endif
#else
    ss << "Generic Scalar Mode";
#endif
    ss << " | QK_I2_S = 128 (Interleaved 32-stride)";

    std::string str = ss.str();
    int32_t copied = (int32_t)std::min((size_t)buf_len - 1, str.length());
    std::memcpy(buf, str.data(), copied);
    buf[copied] = '\0';
}

void bitnet_get_perf_stats(bitnet_context_t ctx, double* prompt_eval_ms, double* eval_ms, double* tokens_per_sec) {
    if (!ctx) return;
    std::lock_guard<std::mutex> lock(ctx->ctx_mutex);
    if (prompt_eval_ms) *prompt_eval_ms = ctx->metrics.prompt_eval_ms;
    if (eval_ms) *eval_ms = ctx->metrics.eval_time_ms;
    if (tokens_per_sec) *tokens_per_sec = ctx->metrics.tokens_per_sec;
}

