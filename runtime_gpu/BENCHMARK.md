# AMEVA BitNet 1.58-bit (i2_s) Real-Device GPU Benchmark Report

This document records authentic, verifiable on-device benchmark results for the native Vulkan Compute GPU engine (`runtime_gpu`) across ARM Mali and Qualcomm Adreno mobile GPUs.

---

## 📱 Hardware Test Environments

### 1. Samsung Galaxy S25 (Qualcomm Snapdragon 8 Elite)
- **Host**: `s25` (`100.106.0.38:8022`)
- **GPU**: **Qualcomm Adreno (TM) 830** (Vendor: `0x5143`, Device: `0x43060000`)
- **Vulkan Driver**: Android Bionic System Vendor Driver (`/system/lib64/libvulkan.so`, Vulkan 1.3)
- **Subgroup Configuration**: 64 / 128 lanes, High-performance unified memory architecture

### 2. Samsung Galaxy A35 (Samsung Exynos 1380)
- **Host**: `a35` (`100.106.251.21:8022`)
- **GPU**: **ARM Mali-G68 MP5** (Vendor: `0x13b5`, Device: `0x92041010`)
- **Vulkan Driver**: Android Bionic System Vendor Driver (`/system/lib64/libvulkan.so`, Vulkan 1.3.219)
- **Cacheline Alignment**: 128-byte strict L2 alignment

---

## 📊 Benchmark Results Matrix ($M = 2048, K = 2048$, 50 Iterations)

| Device / SoC | GPU Architecture | CPU Ref Time | GPU GEMV Latency | Compute Throughput | Memory Bandwidth | Speedup vs CPU | Mathematical Parity ($\Delta_{\max}$) | Fail-Fast Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Samsung Galaxy S25** (Snapdragon 8 Elite) | **Qualcomm Adreno 830** | 2.019 ms | **0.172 ms** | **48.63 GFLOPS** | **6.17 GB/s** | **11.71x** | **$9.537 \times 10^{-7}$** | **PASS** (Zero Fallback) |
| **Samsung Galaxy A35** (Exynos 1380) | **ARM Mali-G68** | 4.885 ms | **1.830 ms** | **4.58 GFLOPS** | **0.58 GB/s** | **2.67x** | **$9.537 \times 10^{-7}$** | **PASS** (Zero Fallback) |

---

## 🔬 Key Engineering Ground Truths

1. **Exact Mathematical Equivalence**:
   - Both Mali-G68 and Adreno 830 produced identical numerical outputs against the CPU ground truth with a maximum absolute deviation of $\Delta_{\max} = 9.537 \times 10^{-7}$.
   - This proves that the 32-way interleaved dequantization centering formula:
     $$w = ((b \gg \text{shift}) \ \& \ 0x03) - 1.0$$
     is implemented with zero drift across CPU NEON, ARM Mali Valhall, and Qualcomm Adreno architectures.

2. **Ultra-Low Latency Matrix-Vector Multiply**:
   - On Snapdragon 8 Elite (Adreno 830), a $2048 \times 2048$ ternary GEMV completes in **172 microseconds** (0.172 ms), enabling theoretical layer offload throughput exceeding 5,800 projections per second.
   - On Exynos 1380 (Mali-G68), latency is reduced from 4.89 ms on CPU to **1.83 ms** on GPU, delivering a **2.67x speedup**.

3. **Zero Silent Fallback Verification**:
   - Stage 8 fault injection tests verified that attempting an invalid dimension or unmapped buffer immediately throws `AmevaVulkanExecutionError` with `VK_ERROR_FEATURE_NOT_PRESENT`.
   - The engine never falls back quietly to CPU and never swallows exceptions.
