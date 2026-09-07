/**
 * @file llama_bitnet_core.h
 * @brief BitNet Core Engine Context Internal Definitions with GGUF Tensor and True Forward Pipeline.
 */

#ifndef LLAMA_BITNET_CORE_H
#define LLAMA_BITNET_CORE_H

#include "termux_bitnet.h"
#include <string>
#include <vector>
#include <unordered_map>
#include <chrono>
#include <random>
#include <memory>
#include <mutex>

// GGUF Tensor Definition
struct GGUFTensor {
    std::string name;
    uint32_t n_dims = 0;
    std::vector<uint64_t> ne; // dimensions
    uint32_t type = 0;        // GGML type (e.g. i2_s = 30, Q4_0 = 2, F32 = 0)
    uint64_t offset = 0;
    size_t size_bytes = 0;
    const uint8_t* data = nullptr;
    std::vector<uint8_t> owned_data; // In case of direct read
};

struct BitNetVocab {
    std::vector<std::string> id_to_token;
    std::unordered_map<std::string, int32_t> token_to_id;
    int32_t byte_to_id[256];
    int32_t bos_id = 1;
    int32_t eos_id = 2;
    int32_t pad_id = 0;
    int32_t unk_id = 0;

    BitNetVocab() {
        for (int i = 0; i < 256; ++i) byte_to_id[i] = -1;
    }
};

struct BitNetPerfMetrics {
    double load_time_ms = 0.0;
    double prompt_eval_ms = 0.0;
    double eval_time_ms = 0.0;
    int32_t prompt_tokens = 0;
    int32_t eval_tokens = 0;
    double tokens_per_sec = 0.0;
};

// Architecture Hyperparameters extracted from GGUF
struct BitNetConfig {
    uint32_t n_vocab = 32000;
    uint32_t n_ctx = 2048;
    uint32_t n_embd = 2048;
    uint32_t n_layers = 24;
    uint32_t n_heads = 32;
    uint32_t n_kv_heads = 32;
    uint32_t head_dim = 64;   // n_embd / n_heads
    uint32_t n_ffn = 5632;    // SwiGLU FFN hidden dimension
    float norm_eps = 1e-5f;
    float rope_theta = 10000.0f;
};

// Layer-wise weight references directly mapped to GGUF memory
struct BitNetLayerWeights {
    const float* attn_norm = nullptr;     // blk.N.attn_norm.weight (RMSNorm FP32/FP16)
    uint32_t attn_norm_type = 0;
    const void*  wq = nullptr;            // blk.N.attn_q.weight (i2_s / Q4_0 / etc)
    uint32_t wq_type = 30;
    const void*  wk = nullptr;            // blk.N.attn_k.weight
    uint32_t wk_type = 30;
    const void*  wv = nullptr;            // blk.N.attn_v.weight
    uint32_t wv_type = 30;
    const float* attn_sub_norm = nullptr; // blk.N.attn_sub_norm.weight (BitNet Sub-LayerNorm)
    uint32_t attn_sub_norm_type = 0;
    const void*  wo = nullptr;            // blk.N.attn_output.weight
    uint32_t wo_type = 30;

    const float* ffn_norm = nullptr;     // blk.N.ffn_norm.weight (RMSNorm FP32/FP16)
    uint32_t ffn_norm_type = 0;
    const void*  w_gate = nullptr;        // blk.N.ffn_gate.weight
    uint32_t w_gate_type = 30;
    const void*  w_up = nullptr;          // blk.N.ffn_up.weight
    uint32_t w_up_type = 30;
    const float* ffn_sub_norm = nullptr;  // blk.N.ffn_sub_norm.weight (BitNet Sub-LayerNorm)
    uint32_t ffn_sub_norm_type = 0;
    const void*  w_down = nullptr;        // blk.N.ffn_down.weight
    uint32_t w_down_type = 30;

    // GPU residency byte offsets in unified Vulkan buffer
    uint32_t gpu_offset_attn_norm = 0;
    uint32_t gpu_offset_wq = 0;
    uint32_t gpu_offset_wk = 0;
    uint32_t gpu_offset_wv = 0;
    uint32_t gpu_offset_wo = 0;
    uint32_t gpu_offset_attn_sub_norm = 0xFFFFFFFF;
    uint32_t gpu_offset_ffn_norm = 0;
    uint32_t gpu_offset_w_gate = 0;
    uint32_t gpu_offset_w_up = 0;
    uint32_t gpu_offset_w_down = 0;
    uint32_t gpu_offset_ffn_sub_norm = 0xFFFFFFFF;
};

// In-Memory Dynamic KV Cache
struct BitNetKVCache {
    std::vector<float> k_cache; // [n_layers * n_ctx * n_kv_heads * head_dim]
    std::vector<float> v_cache; // [n_layers * n_ctx * n_kv_heads * head_dim]
    size_t current_pos = 0;

    void init(uint32_t n_layers, uint32_t n_ctx, uint32_t n_kv_heads, uint32_t head_dim) {
        size_t total_elements = (size_t)n_layers * n_ctx * n_kv_heads * head_dim;
        k_cache.assign(total_elements, 0.0f);
        v_cache.assign(total_elements, 0.0f);
        current_pos = 0;
    }

    void reset() {
        current_pos = 0;
    }
};

struct bitnet_context {
    bitnet_params_t params;
    std::string model_path;
    std::string system_prompt;
    std::vector<std::string> stop_words;
    BitNetVocab vocab;
    BitNetPerfMetrics metrics;
    BitNetConfig config;
    BitNetKVCache kv_cache;

    std::vector<int32_t> context_tokens;
    std::unordered_map<int32_t, int32_t> token_frequencies;
    std::vector<float> logits;

    std::vector<GGUFTensor> tensors;
    std::unordered_map<std::string, size_t> tensor_map;
    std::vector<BitNetLayerWeights> layers;

    // Primary global tensors
    const void* embd_weight = nullptr;
    uint32_t embd_type = 1; // F16 default
    const float* output_norm = nullptr;
    uint32_t output_norm_type = 0;
    const void* output_weight = nullptr;
    uint32_t output_weight_type = 36; // GGML_TYPE_I2_S default
    
    // Cross-Platform Memory Mapping (mmap / CreateFileMapping)
    void* mmap_addr = nullptr;
    size_t mmap_size = 0;
    void* file_handle = nullptr;
    void* map_handle = nullptr;
    
    std::vector<float> scratch_buf;
    std::mt19937 rng;
    std::mutex ctx_mutex;
    bool is_initialized = false;

    // GPU Acceleration Engine
    int32_t n_gpu_layers = 0;
    void* vk_engine = nullptr; // Opaque pointer to ameva::core::VulkanBitNetEngine
};

// Forward declaration of kernel functions
void ggml_vec_dot_i2_i8_s(int n, float * s, size_t bs, const void * vx, size_t bx, const void * vy, size_t by, int nrc, int type);

#endif // LLAMA_BITNET_CORE_H

