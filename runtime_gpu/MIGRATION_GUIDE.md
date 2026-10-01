# AMEVA-Runtime Migration Guide: BitNet 1.58-bit Vulkan Engine

This guide details the procedure for migrating the verified `runtime_gpu/` module from `termux-bitnet` into `dev/ameva-runtime`.

---

## 📂 Source-to-Destination File Mapping

The files in `runtime_gpu/` have been architected to map directly into `dev/ameva-runtime`:

| Source Path (`runtime_gpu/`) | Target Path (`dev/ameva-runtime/`) | Purpose |
| :--- | :--- | :--- |
| `src/core/vulkan_bitnet_engine.h` | `src/core/vulkan_bitnet_engine.h` | C++ Native Vulkan BitNet GEMV Engine |
| `src/core/vulkan_bitnet_engine.cpp` | `src/core/vulkan_bitnet_engine.cpp` | Engine implementation with Zero Silent Fallback |
| `src/shaders/bitnet_gemv_i2_s.comp` | `src/shaders/bitnet_gemv_i2_s.comp` | GLSL 450 Compute Shader |
| `src/shaders/bitnet_gemv_i2_s_spv.h` | `src/shaders/bitnet_gemv_i2_s_spv.h` | Embedded SPIR-V bytecode header array |
| `src/cli/probe_vulkan_gemv.cpp` | `src/cli/probe_vulkan_gemv.cpp` | Standalone CLI hardware probe |
| `python/ameva_runtime/adapters/bitnet_vulkan.py` | `python/ameva_runtime/adapters/bitnet_vulkan.py` | Python Adapter for BitNet GPU routing |
| `tests/test_vulkan_probe.py` | `python/tests/test_bitnet_vulkan_probe.py` | Pytest hardware detection tests |
| `tests/test_gemv_parity.py` | `python/tests/test_bitnet_gemv_parity.py` | Pytest mathematical equivalence tests |
| `tests/test_zero_silent_fallback.py` | `python/tests/test_bitnet_zero_fallback.py` | Pytest fail-fast integrity tests |

---

## 🚀 One-Step Migration Script

When ready to merge into `dev/ameva-runtime`, execute:

```bash
#!/usr/bin/env bash
set -e

SRC_DIR="dev/termux-bitnet/runtime_gpu"
DST_DIR="dev/ameva-runtime"

echo "==> Migrating BitNet Vulkan Engine to ameva-runtime..."

# 1. Copy Core Sources
cp "${SRC_DIR}/src/core/vulkan_bitnet_engine.h" "${DST_DIR}/src/core/"
cp "${SRC_DIR}/src/core/vulkan_bitnet_engine.cpp" "${DST_DIR}/src/core/"

# 2. Copy Shaders
cp "${SRC_DIR}/src/shaders/bitnet_gemv_i2_s.comp" "${DST_DIR}/src/shaders/"
cp "${SRC_DIR}/src/shaders/bitnet_gemv_i2_s_spv.h" "${DST_DIR}/src/shaders/"

# 3. Copy CLI Probe
cp "${SRC_DIR}/src/cli/probe_vulkan_gemv.cpp" "${DST_DIR}/src/cli/"

# 4. Copy Python Adapter
cp "${SRC_DIR}/python/ameva_runtime/adapters/bitnet_vulkan.py" "${DST_DIR}/python/ameva_runtime/adapters/"

# 5. Copy Tests
cp "${SRC_DIR}/tests/test_vulkan_probe.py" "${DST_DIR}/python/tests/test_bitnet_vulkan_probe.py"
cp "${SRC_DIR}/tests/test_gemv_parity.py" "${DST_DIR}/python/tests/test_bitnet_gemv_parity.py"
cp "${SRC_DIR}/tests/test_zero_silent_fallback.py" "${DST_DIR}/python/tests/test_bitnet_zero_fallback.py"

echo "==> Migration complete. Update CMakeLists.txt and router.py in ameva-runtime."
```

---

## ⚙️ CMakeLists.txt Integration in `dev/ameva-runtime`

In `dev/ameva-runtime/CMakeLists.txt`, append `src/core/vulkan_bitnet_engine.cpp` to `CORE_SOURCES`:

```cmake
set(CORE_SOURCES
    src/core/vulkan_loader.cpp
    src/core/vulkan_bitnet_engine.cpp
    src/quirks/mali_quirks.cpp
    src/quirks/adreno_quirks.cpp
)
```

And add the probe executable:

```cmake
add_executable(probe_vulkan_gemv
    src/cli/probe_vulkan_gemv.cpp
    ${CORE_SOURCES}
)
target_link_libraries(probe_vulkan_gemv PRIVATE ${EXTRA_LIBS})
```

---

## 🛡️ Anti-Deception & Fail-Fast Guarantee

The migrated code contains **zero silent fallbacks**. If a user requests Vulkan offload on a device where Vulkan is unavailable or misconfigured, it will throw `AmevaVulkanExecutionError` immediately with full diagnostics.
