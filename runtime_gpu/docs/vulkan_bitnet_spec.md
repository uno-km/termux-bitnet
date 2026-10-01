# BitNet 1.58-bit (i2_s) Vulkan Compute Shader Technical Specification

## 1. Mathematical Architecture

BitNet 1.58-bit models quantize linear projection weights into ternary values $\{-1, 0, +1\}$. In the GGML `i2_s` (Type 36) quantization layout:
- Block Size: $QK = 128$ weights per block.
- Block Byte Size: 32 bytes (256 bits).
- Packing: Each byte packs 4 ternary weights using 2 bits per weight with 32-way column interleaving.

### Ternary Dequantization Formula
For byte $b$ at offset $k \in [0, 31]$:
$$w_0 = ((b \gg 6) \ \& \ 0x03) - 1.0$$
$$w_1 = ((b \gg 4) \ \& \ 0x03) - 1.0$$
$$w_2 = ((b \gg 2) \ \& \ 0x03) - 1.0$$
$$w_3 = (b \ \& \ 0x03) - 1.0$$

### Interleaved Column Offsets
The weights correspond to activations at column indices:
- $x_0 = x[b \cdot 128 + 0 \cdot 32 + k]$
- $x_1 = x[b \cdot 128 + 1 \cdot 32 + k]$
- $x_2 = x[b \cdot 128 + 2 \cdot 32 + k]$
- $x_3 = x[b \cdot 128 + 3 \cdot 32 + k]$

The partial dot-product contribution is:
$$\Delta = w_0 x_0 + w_1 x_1 + w_2 x_2 + w_3 x_3$$

---

## 2. Vulkan Compute Workgroup Layout

```
Workgroup Tile: 32 lanes (X) x 4 rows (Y) x 1 (Z) = 128 Invocations
```

- `gl_LocalInvocationID.x`: Lane index $[0..31]$, directly mapped to byte offset $k$ in block.
- `gl_LocalInvocationID.y`: Row index $[0..3]$ within the 4-row tile.
- `gl_WorkGroupID.x`: Workgroup index computing rows $[4 \cdot G .. 4 \cdot G + 3]$.
- Total workgroups dispatched: $G_x = \lceil M / 4 \rceil$.

### Shared Memory Tree Reduction
```glsl
shared float row_shared_sum[4][32];
```
- Each thread accumulates $\Delta$ across all blocks $b \in [0 .. K / 128 - 1]$.
- Parallel binary tree reduction reduces 32 lanes to lane 0:
  - Step 1: `lane < 16` (`+ 16`)
  - Step 2: `lane < 8` (`+ 8`)
  - Step 3: `lane < 4` (`+ 4`)
  - Step 4: `lane < 2` (`+ 2`)
  - Step 5: `lane < 1` (`+ 1`)
- Lane 0 writes final scaled product $y[r] = \text{sum} \times \text{dequant\_scale}$.

---

## 3. Hardware Alignment & Zero-Copy Protocol

- **Host-Coherent Unified Memory**: Buffers are created with `VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT`.
- **Zero-Copy Host Pointers**: Memory is persistently mapped upon buffer allocation. Updating input activation vectors and reading output logits requires only `memcpy` without explicit staging copy passes.
- **ARM Mali Strict 128-Byte Alignment**: Buffer sizes and row offsets are padded to 128 bytes to prevent Valhall L2 cache line tearing and avoid Subgroup Integer Truncation issues.
