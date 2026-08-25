/**
 * @file llama_bitnet_core.h
 * @brief BitNet Core Engine Context Internal Definitions.
 */

#ifndef LLAMA_BITNET_CORE_H
#define LLAMA_BITNET_CORE_H

#include "termux_bitnet.h"
#include <string>
#include <vector>
#include <unordered_map>
#include <chrono>

struct BitNetVocab {
    std::vector<std::string> id_to_token;
    std::unordered_map<std::string, int32_t> token_to_id;
    int32_t bos_id = 1;
    int32_t eos_id = 2;
    int32_t pad_id = 0;
};

struct BitNetPerfMetrics {
    double load_time_ms = 0.0;
    double prompt_eval_ms = 0.0;
    double eval_time_ms = 0.0;
    int32_t prompt_tokens = 0;
    int32_t eval_tokens = 0;
    double tokens_per_sec = 0.0;
};

#include <random>

struct bitnet_context {
    bitnet_params_t params;
    std::string model_path;
    std::string system_prompt;
    std::vector<std::string> stop_words;
    BitNetVocab vocab;
    BitNetPerfMetrics metrics;
    std::vector<int32_t> context_tokens;
    std::unordered_map<int32_t, int32_t> token_frequencies;
    std::vector<float> logits;
    std::mt19937 rng;
    bool is_initialized = false;
    int32_t n_vocab = 32000;
};

// Forward declaration of kernel functions
void ggml_vec_dot_i2_i8_s(int n, float * s, size_t bs, const void * vx, size_t bx, const void * vy, size_t by, int nrc, int type);

#endif // LLAMA_BITNET_CORE_H
