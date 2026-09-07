/**
 * @file c_api.cpp
 * @brief C ABI Bridge for Direct Native Tensor Operations and Diagnostics.
 */

#include "termux_bitnet.h"
#include "llama_bitnet_core.h"
#include <cstring>
#include <cstdlib>

extern "C" {

/**
 * @brief Directly test raw 1.58-bit matrix-vector dot product without initializing full LLM.
 * @param n Vector dimension (must be multiple of 128).
 * @param s Output buffer (size nrc).
 * @param vx Packed 2-bit weight buffer (size n * nrc / 4).
 * @param vy 8-bit quantized activation buffer (size n).
 * @param nrc Number of rows to compute.
 * @param kernel_type 0: Nx1, 1: 1xN, 2: 1x1.
 */
BITNET_API void bitnet_raw_vec_dot_i2_s(int32_t n, float* s, const void* vx, const void* vy, int32_t nrc, int32_t kernel_type) {
    if (!s || !vx || !vy || n <= 0 || nrc <= 0) return;
    ggml_vec_dot_i2_i8_s(n, s, 1, vx, n, vy, n, nrc, kernel_type);
}

BITNET_API bool bitnet_has_vulkan(void) {
#if defined(GGML_USE_VULKAN)
    return true;
#else
    return false;
#endif
}

}

