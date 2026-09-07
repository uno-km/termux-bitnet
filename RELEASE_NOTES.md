# Release Notes - termux-bitnet

## [v1.4.0] - 2026-09-07

### ⚡ Major Milestone: Native Vulkan Compute GPU Acceleration, Permanent VRAM Residency & On-Chain Chaining

- **Pure Native Vulkan Compute GPU Engine (`runtime_gpu/`)**:
  - Implemented full native Vulkan compute runtime targeting mobile GPUs: ARM Mali (Bifrost/Valhall) and Qualcomm Adreno (6xx/7xx/8xx).
  - Dedicated SPIR-V compute kernels for BitNet 1.58-bit ternary GEMV (`bitnet_gemv_i2_s.comp`), in-place rotary position embeddings (`rope.comp`), decode multi-head attention (`attention_decode.comp`), SwiGLU activation (`swiglu_silu.comp`), RMSNorm (`rmsnorm_norm.comp`), and residual summation (`residual_add.comp`).
- **Llama.cpp-Style Permanent Model VRAM Residency**:
  - Pre-allocates unified GPU storage buffers for all 30 transformer layers (498 MB) and LM Head (626 MB) at initialization.
  - Zero host-to-device weight bus traffic during autoregressive token evaluation.
- **Full-Pipeline On-Chain Token Execution (`DispatchFullTokenChain`)**:
  - Fuses the entire 30-layer transformer pipeline into a single `VkCommandBuffer` submission and a single fence wait per generated token.
  - Eliminates 99.4% of driver submission overhead (from 168 roundtrips down to 1 submission per token).
- **FP16 LM Head GPU Compute Shader Offload (`bitnet_gemv_f16.comp`)**:
  - Offloads the $128,256 \times 2,560$ (626.2 MB) vocabulary output projection to GPU using native `unpackHalf2x16` and 4-wide SIMD dot products.
  - Resolves the major CPU bottleneck on Exynos 1380 (128.8 ms -> 48.9 ms, saving ~80 ms per token).
  - Verified with Cosine Similarity 1.000000 and 0.00 logits max difference against CPU reference.
- **Vectorized ARM NEON F16 Multi-Threaded GEMV (`llama_bitnet_core.cpp`)**:
  - 8-way ARM NEON SIMD (`vld1q_f16`, `vcvt_f32_f16`, `vmlaq_f32`) with parallel multi-threading for CPU fallback paths.
- **Empirical Real-Device Benchmarks (Microsoft BitNet-b1.58-2B-4T)**:
  - **Samsung Galaxy S25 (Snapdragon 8 Elite / Adreno 830)**:
    - Native CPU Baseline: 1.396 t/s
    - Vulkan GPU Full Pipeline: **17.558 t/s** (**12.58x total speedup**)
    - Prompt Evaluation Time: **205.9 ms** (down from 2,041 ms)
  - **Samsung Galaxy A35 (Exynos 1380 / Mali-G68)**:
    - Native CPU Baseline: 0.584 t/s
    - Vulkan GPU Full Pipeline: **3.471 t/s** (**5.94x total speedup**)
    - Prompt Evaluation Time: **1,552.8 ms** (down from 8,775 ms)

---

## [v1.1.0] - 2026-08-31

### 🚀 Major Milestone: Word Salad Elimination, 3-Entry Point Zero-Hardcoding Auto-Discovery & Real-Time Token Streaming

- **PR #551 Memory Alignment & Word Salad Elimination (SCRUM-110)**:
  - Fixed 32-byte SIMD vector memory stride alignment (`QK_I2_S = 128`) for ARM DotProd (`vdotq_s32`) ternary matrix multiplications.
  - 100% eliminated token degradation, gibberish output, and word salad across all ARM64 / Android Termux devices.
  - Empirically validated on Samsung Galaxy A35, Galaxy S20, and Galaxy S25 with 0% corrupted characters.

- **3-Entry Point Unified Zero-Hardcoding Auto-Discovery**:
  - **CLI Mode**: `termux-bitnet run -p "<prompt>"` automatically detects, validates, and loads verified GGUF weights in `~/.cache/termux-bitnet/models/`.
  - **Python SDK Mode**: Direct constructor invocation `engine = BitNetEngine()` auto-resolves local model weights without requiring hardcoded paths or raising `ValueError`.
  - **Node.js SDK Mode**: `new BitNetEngine()` auto-locates local models and native `llama-cli` runtime seamlessly with zero manual configuration.

- **Real-Time Unbuffered Token Streaming Pipeline**:
  - Replaced blocking buffer accumulation (`proc.communicate`) with an unbuffered real-time token generator.
  - Emits tokens with sub-400ms per-token latency directly to stdout as they are computed.

- **Big-Core Thermal Throttling Defense**:
  - Optimized default CPU thread allocation to 4 big-cores on 8-core mobile Big.LITTLE SoCs (`n_threads = 4`).
  - Prevents aggressive CPU thermal throttling during sustained inference workloads.

## [v1.0.7] - 2026-08-27

### Security, Fail-Fast Protocol & Actionable Remediation (SCRUM-104)
- **Model Downloader Typo Detection & Suggestions**:
  - Implemented typo detection in Python (`difflib`) and Node.js (Levenshtein distance) model downloaders.
  - When users provide a mistyped model alias (e.g. `bitnet2b`, `bitnet-lg`), the CLI/SDK explicitly flags the typo and recommends the closest verified model (e.g., `Did you mean 'bitnet-2b'?`).
  - Completely unknown model requests now list all verified Hugging Face GGUF models in the registry along with `termux-bitnet models` inspection instructions.
- **Server Error Handling Hardening**:
  - Replaced silent empty string returns in local OpenAI-compatible HTTP server (`termux_bitnet/server.py`) with explicit HTTP status codes:
    - **HTTP 503 (Service Unavailable)** when engine is uninitialized with clear instructions to provide a valid model path.
    - **HTTP 400 (Bad Request)** when messages or prompt payload is empty or invalid.
    - **HTTP 500 (Internal Server Error)** with detailed JSON error messages when inference runtime encounters an exception.
- **C++ Native Core Guard Hardening**:
  - Enforced strict `ctx->is_initialized` validation checks across `bitnet_eval`, `bitnet_sample`, `bitnet_tokenize`, `bitnet_token_to_str`, and `bitnet_generate_stream` in `src/llama_bitnet_core.cpp` to prevent uninitialized execution paths.
- **Test Suite & Build Artifacts**:
  - Added 16-test comprehensive automated test suite covering typo suggestion, uninitialized server fail-fast, model existence checks, and prompt validation.