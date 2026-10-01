# AMEVA Runtime - Vulkan Compute 1.58-bit Engine Architecture

## 1. Mathematical Ground Truth

In Microsoft BitNet 1.58-bit (`i2_s` / type 36) quantization:
- Each block contains $QK = 128$ weights packed into $32$ consecutive bytes ($2$ bits per weight).
- The 4 weights packed inside byte $b$ correspond to 4 interleaved columns spaced 32 elements apart:
  $$w[0 \cdot 32 + k] = ((b \gg 6) \ \& \ 0x03) - 1$$
  $$w[1 \cdot 32 + k] = ((b \gg 4) \ \& \ 0x03) - 1$$
  $$w[2 \cdot 32 + k] = ((b \gg 2) \ \& \ 0x03) - 1$$
  $$w[3 \cdot 32 + k] = (b \ \& \ 0x03) - 1$$
  where $k \in [0, 31]$ is the intra-block byte offset.

For matrix-vector multiplication (GEMV):
$$\text{Output}[r] = \sum_{c=0}^{N-1} W[r, c] \cdot X[c]$$

On GPU compute cores, this is computed by:
1. Loading packed weight bytes as 32-bit `uvec4` words.
2. Unpacking 4 ternary values $\{-1, 0, +1\}$ per byte using bit shifts and masking.
3. Performing FMA (Fused Multiply-Add) against activation vectors in FP16/FP32.
4. Performing subgroup tree reduction using Vulkan subgroup operations (`subgroupAdd`) or workgroup shared memory.

---

## 2. Zero-Silent-Fallback & Fail-Fast Contract

In accordance with strict OpenSSF / CNCF / AMEVA engineering guidelines:

| Scenario | Strict Behavior | Forbidden Behavior |
| :--- | :--- | :--- |
| **Vulkan ICD Missing** | Raise `VulkanNotAvailableError` with exit code `21` | Silently fall back to CPU |
| **Out of GPU VRAM** | Raise `VulkanOutOfMemoryError` with explicit byte requirement | Silently truncate model layers |
| **Shader Compilation Error**| Abort with full SPIR-V validation dump | Pretend compute succeeded |
| **Numeric Divergence ($\Delta > 10^{-4}$)** | Trigger assert failure and abort | Emit hallucinated token responses |

---

## 3. Mobile GPU Optimizations

### ARM Mali-G68 / Valhall (Samsung Exynos 1380)
- **Subgroup Size**: 16 execution threads (Warp/Wavefront).
- **Memory Architecture**: Unified System RAM (Zero-copy host visible memory `VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT` eliminates PCIe transfer overhead).
- **Shader Strategy**: Tile rows into workgroups of $(32, 4, 1)$ invocations to saturate all 5 Execution Engines (EE).

### Qualcomm Adreno 7xx/8xx (Snapdragon 8 Gen 3 / 8 Elite)
- **Subgroup Size**: 64 / 128 threads.
- **Compute Queue**: Asynchronous compute queue preferred (`VK_QUEUE_COMPUTE_BIT`).
- **Texture / Buffer Cache**: L2 cache prefetching via aligned 64-byte strides.
