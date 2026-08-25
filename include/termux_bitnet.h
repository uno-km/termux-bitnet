/**
 * @file termux_bitnet.h
 * @brief C ABI Interface for BitNet 1.58-bit (i2_s) On-Device Inference Engine.
 * @author uno-km (https://github.com/uno-km)
 * @license Apache-2.0
 */

#ifndef TERMUX_BITNET_H
#define TERMUX_BITNET_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#if defined(_WIN32)
    #if defined(TERMUX_BITNET_EXPORTS)
        #define BITNET_API __declspec(dllexport)
    #else
        #define BITNET_API __declspec(dllimport)
    #endif
#else
    #define BITNET_API __attribute__((visibility("default")))
#endif

/** Opaque handle to the BitNet execution context. */
typedef struct bitnet_context* bitnet_context_t;

/** Inference configuration and sampling hyperparameters. */
typedef struct {
    const char* model_path;      /**< Absolute or relative path to .gguf model */
    const char* system_prompt;   /**< System prompt prefix */
    const char* stop_tokens;     /**< Comma-separated stop sequences (e.g. "<|end|>,</s>") */
    int32_t n_threads;           /**< CPU worker threads (default: hardware core count) */
    int32_t n_ctx;               /**< KV Cache context window length (default: 2048) */
    int32_t n_batch;             /**< Prompt evaluation logical batch size (default: 512) */
    int32_t n_ubatch;            /**< Physical micro-batch size (default: 512) */
    int32_t n_predict;           /**< Maximum tokens to generate (default: 128) */
    int32_t top_k;               /**< Top-K sampling cutoff (0 = disabled, default: 40) */
    int32_t repeat_last_n;       /**< Number of previous tokens to consider for penalty (default: 64) */
    int32_t n_gpu_layers;        /**< Number of layers to offload to GPU/NPU (default: 0) */
    uint32_t seed;               /**< RNG seed for deterministic sampling (0 = random) */
    float temperature;           /**< Softmax temperature (0.0 = deterministic greedy) */
    float top_p;                 /**< Nucleus sampling threshold (default: 0.95) */
    float min_p;                 /**< Min-P sampling cutoff relative to max prob (default: 0.05) */
    float typical_p;             /**< Locally typical sampling threshold (default: 1.0) */
    float repeat_penalty;        /**< Repetition penalty coefficient (default: 1.15) */
    float frequency_penalty;     /**< Frequency penalty coefficient (default: 0.0) */
    float presence_penalty;      /**< Presence penalty coefficient (default: 0.0) */
    bool flash_attn;             /**< Enable flash attention acceleration (default: false) */
    bool verbose;                /**< Enable verbose diagnostic logs */
} bitnet_params_t;

/** Token generation callback for streaming responses. Return false to abort early. */
typedef bool (*bitnet_stream_cb)(const char* token_str, int32_t token_id, void* user_data);

/**
 * @brief Initialize default hyperparameters.
 */
BITNET_API bitnet_params_t bitnet_default_params(void);

/**
 * @brief Load a 1.58-bit GGUF model and initialize the execution engine.
 * @param params Pointer to engine parameters.
 * @return Context handle on success, NULL on failure.
 */
BITNET_API bitnet_context_t bitnet_init(const bitnet_params_t* params);

/**
 * @brief Release all memory, KV cache, and model weights associated with the context.
 * @param ctx Context handle.
 */
BITNET_API void bitnet_free(bitnet_context_t ctx);

/**
 * @brief Tokenize an input string into token IDs.
 * @param ctx Context handle.
 * @param text UTF-8 input string.
 * @param tokens Output buffer for token IDs.
 * @param max_tokens Maximum size of the output buffer.
 * @return Number of tokens generated, or negative error code.
 */
BITNET_API int32_t bitnet_tokenize(bitnet_context_t ctx, const char* text, int32_t* tokens, int32_t max_tokens);

/**
 * @brief Convert a token ID to its UTF-8 string representation.
 * @param ctx Context handle.
 * @param token Token ID.
 * @param buf Output string buffer.
 * @param buf_len Buffer capacity.
 * @return Number of characters written.
 */
BITNET_API int32_t bitnet_token_to_str(bitnet_context_t ctx, int32_t token, char* buf, int32_t buf_len);

/**
 * @brief Perform forward evaluation of a token sequence into the KV cache.
 * @param ctx Context handle.
 * @param tokens Array of token IDs.
 * @param n_tokens Number of tokens to evaluate.
 * @return 0 on success, non-zero on error.
 */
BITNET_API int32_t bitnet_eval(bitnet_context_t ctx, const int32_t* tokens, int32_t n_tokens);

/**
 * @brief Sample the next token from current logits using configured temperature & top_p.
 * @param ctx Context handle.
 * @return Sampled token ID.
 */
BITNET_API int32_t bitnet_sample(bitnet_context_t ctx);

/**
 * @brief High-level streaming text generation interface.
 * @param ctx Context handle.
 * @param prompt Input prompt text.
 * @param max_new_tokens Maximum number of tokens to generate.
 * @param callback Callback invoked on each generated token piece.
 * @param user_data User-defined pointer passed to callback.
 * @return Total number of tokens generated.
 */
BITNET_API int32_t bitnet_generate_stream(bitnet_context_t ctx, const char* prompt, int32_t max_new_tokens, bitnet_stream_cb callback, void* user_data);

/**
 * @brief Inspect runtime hardware features and acceleration modes.
 * @param buf Output buffer.
 * @param buf_len Buffer capacity.
 */
BITNET_API void bitnet_get_hardware_info(char* buf, int32_t buf_len);

/**
 * @brief Retrieve performance metrics of the last generation.
 * @param ctx Context handle.
 * @param prompt_eval_ms Output pointer for TTFT / prompt eval time in ms.
 * @param eval_ms Output pointer for token generation eval time in ms.
 * @param tokens_per_sec Output pointer for generation tokens/sec.
 */
BITNET_API void bitnet_get_perf_stats(bitnet_context_t ctx, double* prompt_eval_ms, double* eval_ms, double* tokens_per_sec);

#ifdef __cplusplus
}
#endif

#endif /* TERMUX_BITNET_H */
