# AMEVA Runtime - BitNet Vulkan Compute GPU Acceleration Staging Module

> **Zero-Silent-Fallback Native Vulkan Compute GPU Engine for BitNet 1.58-bit (i2_s) on ARM Mali & Qualcomm Adreno.**  
> *Architected for seamless one-touch migration into `dev/ameva-runtime`.*

---

## 1. Overview & Purpose

This staging module implements the **world's first native Vulkan Compute GPU engine specifically tailored for 1.58-bit ternary quantized weights (`i2_s`)** on mobile Android GPUs (ARM Mali & Qualcomm Adreno).

While standard LLM runtimes rely on CPU NEON or lack Vulkan shaders for type 36 (`i2_s`), this module provides:
1. **GLSL / SPIR-V 1.58-bit GEMV Compute Shader**: Unpacks 4-way interleaved ternary weights in hardware registers with zero CPU overhead.
2. **Dynamic Bionic Vulkan ICD Dispatcher**: Binds directly to Android's `/system/lib64/libvulkan.so` without root or user-space X11/Mesa dependencies.
3. **Mali & Adreno Architectural Quirks**: Tuned for ARM Mali-G68 MP5 (subgroup size 16, unified memory) and Qualcomm Adreno 7xx/8xx (subgroup size 64/128, asynchronous compute queues).
4. **Zero-Silent-Fallback / Fail-Fast Guarantee**: If GPU initialization or memory allocation fails, the engine immediately aborts with explicit error codes rather than deceiving the user with quiet CPU fallback.

---

## 2. Directory Layout (Mirrors `dev/ameva-runtime`)

```text
runtime_gpu/
├── CMakeLists.txt                  # Independent C++ CMake build configuration
├── README.md                       # High-level architecture & migration roadmap
├── ARCHITECTURE.md                 # Deep mathematical & Vulkan shader specification
├── pyproject.toml                  # Standalone wheel packaging for test distribution
├── setup.py                        # Python extension build script
├── src/
│   ├── core/
│   │   ├── vulkan_loader.h         # Dynamic ICD loader (/system/lib64/libvulkan.so)
│   │   ├── vulkan_loader.cpp
│   │   ├── vulkan_bitnet_engine.h  # Vulkan pipeline & buffer orchestrator
│   │   └── vulkan_bitnet_engine.cpp
│   ├── quirks/
│   │   ├── mali_quirks.h           # Mali Valhall/Bifrost memory alignment & quirks
│   │   ├── mali_quirks.cpp
│   │   ├── adreno_quirks.h         # Adreno compute pipeline & queue quirks
│   │   └── adreno_quirks.cpp
│   └── shaders/
│       ├── bitnet_gemv_i2_s.comp   # Native 1.58-bit ternary GEMV compute shader
│       └── bitnet_gemv_i2_s_spv.h  # Embedded SPIR-V bytecode header
├── python/
│   └── ameva_runtime/
│       └── adapters/
│           └── bitnet_vulkan.py    # Fail-Fast adapter matching ameva-runtime conventions
└── tests/
    ├── test_vulkan_probe.cpp       # Standalone C++ GPU hardware probe test
    └── test_vulkan_i2_s_parity.py  # Zero-deception mathematical parity test
```

---

## 3. Migration Roadmap to `dev/ameva-runtime`

Once real-device benchmarks and mathematical parity tests pass on the Samsung Galaxy A35 (Mali-G68) and Galaxy S25 (Snapdragon 8 Elite / Adreno 830):
1. Copy `src/shaders/bitnet_gemv_i2_s.comp` and `bitnet_gemv_i2_s_spv.h` -> `dev/ameva-runtime/src/shaders/`
2. Copy `src/core/vulkan_bitnet_engine.*` -> `dev/ameva-runtime/src/core/`
3. Merge `python/ameva_runtime/adapters/bitnet_vulkan.py` -> `dev/ameva-runtime/python/ameva_runtime/adapters/bitnet.py`
4. Register the Vulkan GPU GEMV entry point in `dev/ameva-runtime/src/c_api/`
