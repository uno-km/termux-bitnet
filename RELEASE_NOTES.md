# Release Notes - termux-bitnet v1.4.7

**Release Tag**: `v1.4.7`  
**Distribution Channels**: PyPI (`termux-bitnet`), NPM (`termux-bitnet`), GitHub Releases  
**Target Platform**: Android Termux (ARM64 / aarch64 Bionic libc)  
**License**: Apache-2.0  
**Research Paper**: [AOSF-TR-2026-BITNET-TERNARY-02](https://uno-km.vercel.app/labs/?menu=research-papers)

---

## 🚀 Highlights & Key Architectural Breakthroughs

### 1. Root-Cause Resolution of Ternary Numerical Collapse (Word Salad)
- **Ternary Bitfield Mathematical Realignment**: Corrected low-level unpacking mapping from legacy `(b & 1) - (b >> 1)` to the canonical Microsoft BitNet b1.58 specification:
  $$w_{\text{ternary}} = (b \& 3) - 1 \implies 00 \to -1, 01 \to 0, 10 \to +1$$
  Eliminates catastrophic misallocation of 49.6% inactive neurons to +1, preventing exponential activation norm explosion across 30 transformer layers.
- **32-Byte Tensor Trailer Weight Scale Integration**: Restores exact dequantization scaling $S_W = \text{mean}(|W|)$ from GGUF tensor trailers ($0.96 \sim 2.16$), ensuring calibrated logit distributions.

### 2. Zero-Overhead Dynamic Activation Dispatcher
- **Multi-Model Architectural Agility**: Dynamically inspects layer weight tensors (`lay.ffn_sub_norm`) to auto-dispatch:
  - **Microsoft BitNet b1.58 (2B)**: Squared ReLU ($\text{relu}(x)^2$) + Sub-LayerNorm
  - **LLaMA-based 1.58-bit (Falcon-E-1B, Falcon3-7B)**: Standard SwiGLU ($\text{SiLU}(x) \cdot \text{up}$) without Sub-LayerNorm
- Eliminates hardcoded activation constraints, allowing a single binary to seamlessly serve multiple model families.

### 3. Fleet Hardware Verification & 6GB RAM 7B Model Inference
- **Samsung Galaxy S25** (Snapdragon 8 Elite): **3.95 tok/s** (BitNet-2B, clean coherent generation)
- **Samsung Galaxy A53** (Exynos 1280): **9.69 tok/s** (Falcon-E-1B, real-time conversational speed), **5.91 tok/s** (BitNet-2B), **2.00 tok/s** (Falcon3-7B)
- **Samsung Galaxy A35** (Exynos 1380): **2.29 tok/s** (Falcon-E-1B), **1.57 tok/s** (BitNet-2B), **0.57 tok/s** (Falcon3-7B)
- **Zero-Copy Mmap Streaming**: Validated execution of 3.05GB 7.45B model on 6GB RAM devices without triggering Android Low Memory Killer (LMK).

### 4. Release Assets & Binaries
- `termux-bitnet-v1.4.7-android-aarch64.tar.gz` (Precompiled native ARM64 Android Bionic binary & shared library)
- `termux_bitnet-1.4.7-py3-none-any.whl` (Python Wheel package)
- `termux_bitnet-1.4.7.tar.gz` (Source distribution)
