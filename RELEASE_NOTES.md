# Release Notes - Termux-BitNet v2.0.0 (Sovereign Ternary)

**Release Tag**: `v2.0.0`  
**Distribution Channels**: PyPI (`termux-bitnet`), NPM (`termux-bitnet`), GitHub Releases  
**Target Platform**: Android Termux (ARM64 / aarch64 Bionic libc & Vulkan GPU)  
**License**: Apache-2.0  
**Research Paper**: [AOSF-TR-2026-BITNET-TERNARY-02: Root Cause Analysis of Ternary Numerical Collapse in ARM64 On-Device 1.58-bit LLMs and Implementation of Dynamic Activation Engine](https://uno-km.vercel.app/labs/?menu=research-papers)  
**Governance**: AMEVA Open-Source Foundation (AOSF) & @uno-km  

---

## 🏛️ Executive Summary: Generational Leap to Sovereign Ternary

`termux-bitnet v2.0.0` marks a generational architectural leap from a single-model experimental CLI into a **universal, multi-model 1.58-bit on-device inference runtime**. 

This major release mathematically eradicates the notorious **ternary numerical collapse ("word salad")** that has afflicted the global 1.58-bit LLM community, introduces a **zero-overhead dynamic activation dispatcher**, and breaks mobile memory boundaries by executing **7.45B parameter models on mainstream 6GB RAM smartphones without OOM crashes**.

---

## ⚡ Ground Truth Hardware Fleet Benchmarks

All metrics represent physically measured ground truth under unrooted Android Termux Bionic libc environments across 4 canonical 1.58-bit model families under steady thermal equilibrium:

| Target Model | Parameter Count & Size | Microarchitecture / Activation | Test Hardware & SoC | Prompt Eval Latency | Generation Speed | Empirical Verification Verdict |
|---|:---:|:---:|---|:---:|:---:|---|
| **Falcon-E-1B** | 1.0B (635 MB) | SwiGLU (SiLU) | **Samsung Galaxy A53** (Exynos 1280) | 1,986 ms | **9.69 tok/s** | **REAL-TIME (Exceeds Human Silent Reading Speed)** |
| **BitNet-2B** | 2.0B (1.13 GB) | Squared ReLU + Sub-Norm | **Samsung Galaxy S25** (Snapdragon 8 Elite) | 1,269 ms | **3.95 tok/s** | **PASS (100% Coherent Text Output)** |
| **BitNet-2B** | 2.0B (1.13 GB) | Squared ReLU + Sub-Norm | **Samsung Galaxy A53** (Exynos 1280) | 1,382 ms | **5.91 tok/s** | **PASS (100% Coherent Text Output)** |
| **BitNet-2B** | 2.0B (1.13 GB) | Squared ReLU + Sub-Norm | **Samsung Galaxy A35** (Exynos 1380) | 5,386 ms | **1.57 tok/s** | **PASS (100% Coherent Text Output)** |
| **BitNet-Embed** | 268M (367 MB) | 1.58-bit Vector Search | **Samsung Galaxy A53** (Exynos 1280) | 126 ms | **30.68 tok/s** | **PASS (Zero-Copy Mmap Embedding Pass)** |
| **Falcon3-7B** | 7.45B (3.05 GB) | SwiGLU (SiLU) | **Samsung Galaxy A53** (6GB RAM / E1280) | 7,170 ms | **2.00 tok/s** | **PASS (Zero-Copy Mmap 6GB RAM OOM Defense)** |
| **Falcon3-7B** | 7.45B (3.05 GB) | SwiGLU (SiLU) | **Samsung Galaxy A35** (6GB RAM / E1380) | 16,386 ms | **0.57 tok/s** | **PASS (Zero-Copy Mmap 6GB RAM OOM Defense)** |

---

## 🔬 Core Architectural Breakthroughs

### 1. Mathematical Elimination of Ternary Numerical Collapse (Word Salad)
- **Root Cause Forensic**: Legacy forks and scalar fallbacks historically decoded 2-bit unsigned containers using `(b & 1) - (b >> 1)`. In Microsoft's official specification, weights are offset by $+1$ ($w_{\text{stored}} = w_{\text{ternary}} + 1$). The legacy mapping turned the **49.6% inactive zero neurons into $+1$**, causing exponential activation norm explosion across 30 transformer layers.
- **Canonical Formula**: `v2.0.0` enforces the canonical dequantization relation:
  $$w_{\text{ternary}} = (b \& 3) - 1 \implies 00 \to -1,\; 01 \to 0,\; 10 \to +1$$
- **Weight Scale Trailer Integration**: GGUF tensor trailers store a 4-byte `float32` weight scale ($S_W = \text{mean}(|W|)$, typically $0.96 \sim 2.16$). `v2.0.0` parses this 32-byte trailer and compounds it into the dequantization factor ($\text{total\_scale} = \text{dequant} \times S_W$), preserving logit distribution calibration.

### 2. Zero-Overhead Dynamic Activation Dispatcher
- **Multi-Family Support**: Standard runtimes hardcode either SiLU or Squared ReLU. `termux-bitnet v2.0.0` inspects `lay.ffn_sub_norm` tensor presence at load time to seamlessly auto-dispatch:
  - **Microsoft BitNet 2B**: Squared ReLU ($\text{relu}(x)^2$) coupled with Sub-LayerNorm.
  - **Falcon-E-1B & Falcon3-7B**: Standard SwiGLU ($\text{SiLU}(x) \cdot \text{up}$) without Sub-LayerNorm.
- Enables a single binary to seamlessly serve Microsoft, Technology Innovation Institute (TII), and LLaMA 1.58-bit model families.

### 3. Mainstream 6GB RAM Smartphone 7.45B Model Execution
- Bypasses physical RAM ceilings through Zero-Copy memory-mapped I/O (`mmap`) and bounded KV cache eviction.
- Enables 3.05GB 7.45B parameter weights (`Falcon3-7B`) to stream directly from flash storage without duplicating Resident Set Size (RSS), completing coherent inference on 6GB RAM phones without triggering Android Low Memory Killer (`lmkd`) eviction.

---

## 🌐 Academic Citations & Upstream Contributions

Our engineering team maintains an active upstream track record solving systemic defects across global AI repositories:

* **Foundation Research Monograph**: [AOSF-TR-2026-BITNET-TERNARY-02: Root Cause Analysis of Ternary Numerical Collapse and Dynamic Activation Engine](https://uno-km.vercel.app/labs/?menu=research-papers)
* **[microsoft/BitNet #551](https://github.com/microsoft/BitNet/pull/551)**: Resolved ARM QK=128 stride memory layout desynchronization, curing word salad and GGGG infinite repetition bugs across ARM Ampere and x86 CPUs.
* **[microsoft/BitNet #624](https://github.com/microsoft/BitNet/pull/624)**: Completed the 1x4_32W parallel NEON `sdot` hardware acceleration kernel and automated Android Termux build detection.
* **[ggml-org/whisper.cpp #4089](https://github.com/ggml-org/whisper.cpp/pull/4089)**: Engineered mobile heterogeneous GPU-Encoder / CPU-Decoder split-mode architecture, cooling mobile CPU thermal load by 84%.

---

## 📦 Verified Release Assets & Checksums

| Asset File | Size | SHA256 Checksum | Target Platform |
|---|:---:|---|---|
| `termux-bitnet-v2.0.0-android-aarch64.tar.gz` | 78.7 KB | `1fb5e9859ed2fc51a01e064c3d78b47aefa2f9b8cd37545db34e22c921bb2f56` | Android Termux ARM64 (CLI + .so) |
| `libtermux_bitnet.so` | 130.7 KB | `e6850acbc42559cc15517a8f482cd9c2713dba974f4110851de2f6bb1afcd198` | ARM64 Android Bionic libc C++ ABI |
| `termux_bitnet-2.0.0-py3-none-any.whl` | 44.4 KB | `13264fe06d20387600bb9810bb9930f7ae828fe78df4960d1ba74fc0294fc99b` | Python 3.8+ Universal Wheel (PyPI) |
| `termux_bitnet-2.0.0.tar.gz` | 120.4 KB | `7d7d242a420faad0a0b1bc89456bbd0cb004724a737f551b9b1836691c28c89b` | Python Source Distribution |

---

## 🚀 Quickstart Installation

```bash
# Python SDK (PyPI)
pip install --upgrade termux-bitnet ameva-runtime

# Node.js CLI (npm)
npm install -g termux-bitnet @ameva/runtime

# One-Touch Termux Native Installer
curl -sSL https://raw.githubusercontent.com/uno-km/termux-bitnet/main/install.sh | bash
```

**Official Documentation Portal**: [https://uno-km.vercel.app/lib/bitnet/](https://uno-km.vercel.app/lib/bitnet/)
