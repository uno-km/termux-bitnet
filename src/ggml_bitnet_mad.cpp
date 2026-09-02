/**
 * @file ggml_bitnet_mad.cpp
 * @brief High-performance 1.58-bit (i2_s) Quantized Dot-Product Kernels.
 *        Standardized with QK=128 memory interleaving layout and ARM NEON / DotProd acceleration.
 * @author uno-km (https://github.com/uno-km)
 */

#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#if defined(__ARM_NEON)
#include <arm_neon.h>
#elif defined(__AVX2__)
#include <immintrin.h>
#endif

#define QK_I2_S 128
#define PARALLEL_SIZE 4

#if defined(__AVX2__)
static inline int hsum_i32_8(__m256i a) {
    __m128i l = _mm256_extractf128_si256(a, 0);
    __m128i h = _mm256_extractf128_si256(a, 1);
    __m128i sum128 = _mm_add_epi32(l, h);
    __m128i sum64 = _mm_add_epi32(sum128, _mm_shuffle_epi32(sum128, _MM_SHUFFLE(1, 0, 3, 2)));
    __m128i sum32 = _mm_add_epi32(sum64, _mm_shuffle_epi32(sum64, _MM_SHUFFLE(2, 3, 0, 1)));
    return _mm_cvtsi128_si32(sum32);
}
#endif

// ============================================================================
// 1x1 Matrix-Vector Dot Product Kernel
// ============================================================================
void ggml_vec_dot_i2_i8_s_1x1(int n, float * s, size_t bs, const void * vx, size_t bx, const void * vy, size_t by, int nrc) {
    (void)bs;
    (void)by;
#if defined(__AVX2__)
    const uint8_t * x = (const uint8_t *)vx;
    const int8_t  * y = (const int8_t  *)vy;

    const int nb = n / QK_I2_S;
    const int group32_num = nb / 32;
    __m256i mask = _mm256_set1_epi8(0x03);
    __m256i one16 = _mm256_set1_epi16(1);

    for (int row = 0; row < nrc; row++) {
        __m256i accu = _mm256_setzero_si256();
        const uint8_t * x_row = x + row * bx / 4;
        
        for (int i = 0; i < group32_num; i++) {
            const uint8_t * px = x_row + i * 1024;
            const int8_t  * py = y + i * 4096;
            __m256i accu32 = _mm256_setzero_si256();
            
            for (int j = 0; j < 32; j++) {
                __m256i xq8_3 = _mm256_loadu_si256((const __m256i*)(px));
                __m256i xq8_2 = _mm256_srli_epi16(xq8_3, 2);
                __m256i xq8_1 = _mm256_srli_epi16(xq8_3, 4);
                __m256i xq8_0 = _mm256_srli_epi16(xq8_3, 6);

                xq8_3 = _mm256_and_si256(xq8_3, mask);
                xq8_2 = _mm256_and_si256(xq8_2, mask);
                xq8_1 = _mm256_and_si256(xq8_1, mask);
                xq8_0 = _mm256_and_si256(xq8_0, mask);

                __m256i yq8_0 = _mm256_loadu_si256((const __m256i*)(py));
                __m256i yq8_1 = _mm256_loadu_si256((const __m256i*)(py + 32));
                __m256i yq8_2 = _mm256_loadu_si256((const __m256i*)(py + 64));
                __m256i yq8_3 = _mm256_loadu_si256((const __m256i*)(py + 96));

                xq8_0 = _mm256_maddubs_epi16(xq8_0, yq8_0);
                xq8_1 = _mm256_maddubs_epi16(xq8_1, yq8_1);
                xq8_2 = _mm256_maddubs_epi16(xq8_2, yq8_2);
                xq8_3 = _mm256_maddubs_epi16(xq8_3, yq8_3);

                accu32 = _mm256_add_epi16(accu32, _mm256_add_epi16(xq8_0, xq8_1));
                accu32 = _mm256_add_epi16(accu32, _mm256_add_epi16(xq8_2, xq8_3));

                px += 32;
                py += 128;
            }
            accu = _mm256_add_epi32(_mm256_madd_epi16(accu32, one16), accu);
        }

        const int rem = nb % 32;
        if (rem > 0) {
            const uint8_t * px = x_row + group32_num * 1024;
            const int8_t  * py = y + group32_num * 4096;
            __m256i accula = _mm256_setzero_si256();
            for (int j = 0; j < rem; j++) {
                __m256i xq8_3 = _mm256_loadu_si256((const __m256i*)(px));
                __m256i xq8_2 = _mm256_srli_epi16(xq8_3, 2);
                __m256i xq8_1 = _mm256_srli_epi16(xq8_3, 4);
                __m256i xq8_0 = _mm256_srli_epi16(xq8_3, 6);

                xq8_3 = _mm256_and_si256(xq8_3, mask);
                xq8_2 = _mm256_and_si256(xq8_2, mask);
                xq8_1 = _mm256_and_si256(xq8_1, mask);
                xq8_0 = _mm256_and_si256(xq8_0, mask);

                __m256i yq8_0 = _mm256_loadu_si256((const __m256i*)(py));
                __m256i yq8_1 = _mm256_loadu_si256((const __m256i*)(py + 32));
                __m256i yq8_2 = _mm256_loadu_si256((const __m256i*)(py + 64));
                __m256i yq8_3 = _mm256_loadu_si256((const __m256i*)(py + 96));

                xq8_0 = _mm256_maddubs_epi16(xq8_0, yq8_0);
                xq8_1 = _mm256_maddubs_epi16(xq8_1, yq8_1);
                xq8_2 = _mm256_maddubs_epi16(xq8_2, yq8_2);
                xq8_3 = _mm256_maddubs_epi16(xq8_3, yq8_3);

                accula = _mm256_add_epi16(accula, _mm256_add_epi16(xq8_0, xq8_1));
                accula = _mm256_add_epi16(accula, _mm256_add_epi16(xq8_2, xq8_3));

                px += 32;
                py += 128;
            }
            accu = _mm256_add_epi32(accu, _mm256_madd_epi16(accula, one16));
        }
        
        int sumi = hsum_i32_8(accu);
        s[row] = (float)sumi;
    }
#elif defined(__ARM_NEON)
    const uint8_t * x = (const uint8_t *)vx;
    const int8_t  * y = (const int8_t  *)vy;

    const int QK = 128; 
    const int nb = n / QK;
    const uint8x16_t mask = vdupq_n_u8(0x03);

    for (int row = 0; row < nrc; row++) {
        int32x4_t accu = vdupq_n_s32(0);
        const uint8_t * x_row = x + (row * bx) / 4;

        for (int b = 0; b < nb; b++) {
            const uint8_t * px = x_row + b * 32;
            const int8_t  * py = y + b * QK;

            for (int j = 0; j < 2; j++) {
                int k = j * 16;
                uint8x16_t xb = vld1q_u8(px + k);

                // MSB -> LSB 2-bit Unpacking (Identical to AVX2 logic)
                int8x16_t ones = vdupq_n_s8(1);
                int8x16_t v0 = vsubq_s8(vreinterpretq_s8_u8(vandq_u8(vshrq_n_u8(xb, 6), mask)), ones);
                int8x16_t v1 = vsubq_s8(vreinterpretq_s8_u8(vandq_u8(vshrq_n_u8(xb, 4), mask)), ones);
                int8x16_t v2 = vsubq_s8(vreinterpretq_s8_u8(vandq_u8(vshrq_n_u8(xb, 2), mask)), ones);
                int8x16_t v3 = vsubq_s8(vreinterpretq_s8_u8(vandq_u8(xb, mask)), ones);

                // 32-stride Interleaved Load
                int8x16_t y0 = vld1q_s8(py + k +  0*32);
                int8x16_t y1 = vld1q_s8(py + k +  1*32);
                int8x16_t y2 = vld1q_s8(py + k +  2*32);
                int8x16_t y3 = vld1q_s8(py + k +  3*32);

#if defined(__ARM_FEATURE_DOTPROD)
                accu = vdotq_s32(accu, v0, y0);
                accu = vdotq_s32(accu, v1, y1);
                accu = vdotq_s32(accu, v2, y2);
                accu = vdotq_s32(accu, v3, y3);
#else
                int16x8_t accula = vdupq_n_s16(0);
                accula = vmlal_s8(accula, vget_low_s8(v0), vget_low_s8(y0));
                accula = vmlal_s8(accula, vget_high_s8(v0), vget_high_s8(y0));
                accula = vmlal_s8(accula, vget_low_s8(v1), vget_low_s8(y1));
                accula = vmlal_s8(accula, vget_high_s8(v1), vget_high_s8(y1));
                accula = vmlal_s8(accula, vget_low_s8(v2), vget_low_s8(y2));
                accula = vmlal_s8(accula, vget_high_s8(v2), vget_high_s8(y2));
                accula = vmlal_s8(accula, vget_low_s8(v3), vget_low_s8(y3));
                accula = vmlal_s8(accula, vget_high_s8(v3), vget_high_s8(y3));

                accu = vaddq_s32(accu, vmovl_s16(vget_low_s16(accula)));
                accu = vaddq_s32(accu, vmovl_high_s16(accula));
#endif
            }
        }
        int64_t sumi = vaddvq_s32(accu);
        s[row] = (float)sumi; 
    }
#else
    // Pure Scalar Fallback
    const uint8_t * x_ptr = (const uint8_t *)vx;
    const int8_t  * y_ptr = (const int8_t  *)vy;
    const int QK = 128;
    const int nb = n / QK;

    for (int row = 0; row < nrc; row++) {
        int64_t total_sum = 0;
        const uint8_t * x_row = x_ptr + (row * bx) / 4;

        for (int b = 0; b < nb; b++) {
            const uint8_t * px = x_row + b * 32;
            const int8_t  * py = y_ptr + b * QK;

            for (int k = 0; k < 32; k++) {
                uint8_t byte_val = px[k];

                int8_t v0 = (int8_t)((byte_val >> 6) & 0x03);
                int8_t v1 = (int8_t)((byte_val >> 4) & 0x03);
                int8_t v2 = (int8_t)((byte_val >> 2) & 0x03);
                int8_t v3 = (int8_t)(byte_val & 0x03);

                int8_t y0 = py[k + 0 * 32];
                int8_t y1 = py[k + 1 * 32];
                int8_t y2 = py[k + 2 * 32];
                int8_t y3 = py[k + 3 * 32];

                total_sum += (int32_t)v0 * (int32_t)y0;
                total_sum += (int32_t)v1 * (int32_t)y1;
                total_sum += (int32_t)v2 * (int32_t)y2;
                total_sum += (int32_t)v3 * (int32_t)y3;
            }
        }
        s[row] = (float)total_sum;
    }
#endif
}

// ============================================================================
// 1xN Matrix-Vector Dot Product Kernel
// ============================================================================
void ggml_vec_dot_i2_i8_s_1xN(int n, float * s, size_t bs, const void * vx, size_t bx, const void * vy, size_t by, int nrc) {
    (void)bx;
#if defined(__ARM_NEON)
    const uint8_t * x = (const uint8_t *)vx;
    const int8_t  * y = (const int8_t  *)vy;

    const int QK = 128;
    const int nb = n / QK;
    const uint8x16_t mask = vdupq_n_u8(0x03);

    for (int col = 0; col < nrc; col += PARALLEL_SIZE) {
        int cur_p = (col + PARALLEL_SIZE <= nrc) ? PARALLEL_SIZE : (nrc - col);
        int32x4_t accu[PARALLEL_SIZE];
        for (int iy = 0; iy < PARALLEL_SIZE; iy++) {
            accu[iy] = vdupq_n_s32(0);
        }

        for (int b = 0; b < nb; b++) {
            const uint8_t * px = x + b * 32;

            for (int j = 0; j < 2; j++) {
                int k = j * 16;
                uint8x16_t xb = vld1q_u8(px + k);

                int8x16_t v0 = vreinterpretq_s8_u8(vandq_u8(vshrq_n_u8(xb, 6), mask));
                int8x16_t v1 = vreinterpretq_s8_u8(vandq_u8(vshrq_n_u8(xb, 4), mask));
                int8x16_t v2 = vreinterpretq_s8_u8(vandq_u8(vshrq_n_u8(xb, 2), mask));
                int8x16_t v3 = vreinterpretq_s8_u8(vandq_u8(xb, mask));

                for (int iy = 0; iy < cur_p; iy++) {
                    const int8_t * py = y + (col + iy) * by + b * QK;

                    int8x16_t y0 = vld1q_s8(py + k + 0*32);
                    int8x16_t y1 = vld1q_s8(py + k + 1*32);
                    int8x16_t y2 = vld1q_s8(py + k + 2*32);
                    int8x16_t y3 = vld1q_s8(py + k + 3*32);

#if defined(__ARM_FEATURE_DOTPROD)
                    accu[iy] = vdotq_s32(accu[iy], v0, y0);
                    accu[iy] = vdotq_s32(accu[iy], v1, y1);
                    accu[iy] = vdotq_s32(accu[iy], v2, y2);
                    accu[iy] = vdotq_s32(accu[iy], v3, y3);
#else
                    int16x8_t accula = vdupq_n_s16(0);
                    accula = vmlal_s8(accula, vget_low_s8(v0), vget_low_s8(y0));
                    accula = vmlal_s8(accula, vget_high_s8(v0), vget_high_s8(y0));
                    accula = vmlal_s8(accula, vget_low_s8(v1), vget_low_s8(y1));
                    accula = vmlal_s8(accula, vget_high_s8(v1), vget_high_s8(y1));
                    accula = vmlal_s8(accula, vget_low_s8(v2), vget_low_s8(y2));
                    accula = vmlal_s8(accula, vget_high_s8(v2), vget_high_s8(y2));
                    accula = vmlal_s8(accula, vget_low_s8(v3), vget_low_s8(y3));
                    accula = vmlal_s8(accula, vget_high_s8(v3), vget_high_s8(y3));

                    accu[iy] = vaddq_s32(accu[iy], vmovl_s16(vget_low_s16(accula)));
                    accu[iy] = vaddq_s32(accu[iy], vmovl_high_s16(accula));
#endif
                }
            }
        }

        for (int iy = 0; iy < cur_p; iy++) {
            int32_t sumi = vaddvq_s32(accu[iy]);
            s[(col + iy) * bs] = (float)sumi;
        }
    }
#else
    for (int i = 0; i < nrc; i++) {
        ggml_vec_dot_i2_i8_s_1x1(n, &s[i * bs], 1, vx, 0, (const int8_t *)vy + i * by, 0, 1);
    }
#endif
}

// ============================================================================
// Nx1 Matrix-Vector Dot Product Kernel (Multi-row X, Single Y)
// ============================================================================
void ggml_vec_dot_i2_i8_s_Nx1(int n, float * s, size_t bs, const void * vx, size_t bx, const void * vy, size_t by, int nrc) {
    (void)by;
    for (int i = 0; i < nrc; i++) {
        ggml_vec_dot_i2_i8_s_1x1(n, &s[i * bs], 1, (const uint8_t *)vx + (i * bx) / 4, 0, vy, 0, 1);
    }
}

// ============================================================================
// Router Dispatch Function
// ============================================================================
void ggml_vec_dot_i2_i8_s(int n, float * s, size_t bs, const void * vx, size_t bx, const void * vy, size_t by, int nrc, int type) {
    if (type == 0) {
        ggml_vec_dot_i2_i8_s_Nx1(n, s, bs, vx, bx, vy, by, nrc);
    } else if (type == 1) {
        ggml_vec_dot_i2_i8_s_1xN(n, s, bs, vx, bx, vy, by, nrc);
    } else {
        ggml_vec_dot_i2_i8_s_1x1(n, s, bs, vx, bx, vy, by, nrc);
    }
}
