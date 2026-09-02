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
    int32_t bos_id = 1;
    int32_t eos_id = 2;
    int32_t pad_id = 0;
    int32_t unk_id = 0;
};

struct BitNetPerfMetrics {
    double load_time_ms = 0.0;
    double prompt_eval_ms = 0.0;
    double eval_time_ms = 0.0;
    int32_t prompt_tokens = 0;
    int32_t eval_tokens = 0;
    double tokens_per_sec = 0.0;
};

struct bitnet_context {
    bitnet_params_t params;
    std::string model_path;
    std::string system_prompt;
    std::vector<std::string> stop_words;
    BitNetVocab vocab;
    BitNetPerfMetrics metrics;
    std::vector<int32_t> context_tokens;
    size_t ring_head = 0;
    std::unordered_map<int32_t, int32_t> token_frequencies;
    std::vector<float> logits;
    std::vector<float> hidden_state; // Hidden state activation vector
    std::vector<GGUFTensor> tensors;
    std::unordered_map<std::string, size_t> tensor_map;
    
    // Cross-Platform Memory Mapping (mmap / CreateFileMapping)
    void* mmap_addr = nullptr;
    size_t mmap_size = 0;
    void* file_handle = nullptr; // Windows HANDLE or POSIX fd
    void* map_handle = nullptr;  // Windows mapping handle
    
    // Weight buffers
    std::vector<uint8_t> model_weights_raw;
    uint32_t n_embd = 2048;
    uint32_t n_layer = 24;
    uint32_t n_head = 16;
    uint32_t n_vocab = 32000;
    
    std::mt19937 rng;
    std::mutex ctx_mutex;
    bool is_initialized = false;
};

// Forward declaration of kernel functions
void ggml_vec_dot_i2_i8_s(int n, float * s, size_t bs, const void * vx, size_t bx, const void * vy, size_t by, int nrc, int type);

#endif // LLAMA_BITNET_CORE_H

