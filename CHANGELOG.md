# Changelog

All notable changes to 	ermux-bitnet will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.0] - 2026-09-07

### Added
- **Native Vulkan Compute GPU Engine (`runtime_gpu/`)**:
  - Pure native Vulkan compute runtime supporting ARM Mali (Bifrost/Valhall) and Qualcomm Adreno (6xx/7xx/8xx) on Android Termux.
  - GLSL 450 SPIR-V kernels for 1.58-bit ternary GEMV (`bitnet_gemv_i2_s.comp`), in-place RoPE (`rope.comp`), decode multi-head attention (`attention_decode.comp`), SwiGLU SiLU (`swiglu_silu.comp`), RMSNorm (`rmsnorm_norm.comp`), and residual accumulation (`residual_add.comp`).
- **Permanent Model VRAM Residency Architecture**:
  - Pre-allocates unified GPU storage buffers for all 30 transformer layers (498 MB) and LM Head (626 MB) at initialization.
  - Reduces host-to-device weight bus traffic to 0 Byte during token evaluation.
- **Full-Pipeline On-Chain Execution (`DispatchFullTokenChain`)**:
  - Chains all 30 transformer layers into a single `VkCommandBuffer` submission and a single fence wait per token.
  - Cuts GPU driver submission overhead by 99.4% (168 submissions down to 1 submission per token).
- **FP16 LM Head GPU Compute Shader Offload (`bitnet_gemv_f16.comp`)**:
  - Offloads $128,256 \times 2,560$ (626.2 MB) FP16 output projection to GPU with native `unpackHalf2x16` and 4-wide SIMD dot products.
  - 32-lane workgroup shared memory tree reduction with Cosine Similarity 1.000000 against CPU reference.
- **Vectorized ARM NEON F16 Multi-Threaded GEMV (`llama_bitnet_core.cpp`)**:
  - 8-way ARM NEON SIMD (`vld1q_f16`, `vcvt_f32_f16`, `vmlaq_f32`) with parallel chunking for CPU fallback paths.

### Performance
- **Samsung Galaxy S25 (Snapdragon 8 Elite / Adreno 830)**:
  - Token speed: **17.56 tokens/sec** (up from 1.39 t/s native CPU baseline, **12.6x speedup**).
  - Prompt eval: **205.9 ms** (down from 2,041 ms).
- **Samsung Galaxy A35 (Exynos 1380 / Mali-G68)**:
  - Token speed: **3.47 tokens/sec** (up from 0.58 t/s native CPU baseline, **6.0x speedup**).
  - Prompt eval: **1,552.8 ms** (down from 8,775 ms).
  - LM Head latency: 128.8 ms -> 48.9 ms (2.63x faster, saving 80 ms per token).

---

## [1.2.0] - 2026-09-07

### Added
- Direct integration with `BitNetAdapter` from `ameva_runtime.adapters` SSOT.
- Strict hardware acceleration verification and Fail-Fast on missing NEON/dotprod instruction set.
- English localization for diagnostics and CLI messages.

---

## [1.1.5] - 2026-09-05

### Changed
- Synchronized ameva-runtime unified acceleration bridge and updated installation toolchain.
- Refined platform detection comments and hardware profile SSOT integration.

---

## [1.1.4] - 2026-09-05

### Changed
- Migrated hardware acceleration dependency to unified `ameva-runtime>=2.0.0` and `@ameva/runtime>=2.0.0`.
- Enforced strict Fail-Fast compilation in CMake build extension (RuntimeError on missing toolchain or build failure).
- Eradicated silent fallback and return paths in native C++ bindings.

---

## [1.1.1] - 2026-09-02

### Added
- **Unicode NFC Subword Tokenizer**: Replaced heuristic byte division with C FFI tokenization and Unicode NFC regex fallback.
- **Fail-Fast Native Build**: Enforced 
aise RuntimeError on CMake build errors in setup.py.

### Cleaned
- Purged 20+ legacy wheel artifacts from repository tree.

### Verification
- **Unit Tests**: 20 / 20 passed with 100% assertion coverage.