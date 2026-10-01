# Termux-BitNet (v2.0.0 Sovereign Ternary)

> **Production-Grade Universal 1.58-Bit (i2_s) On-Device LLM Inference Engine with ARM64 NEON DotProd SIMD & Native Vulkan GPU Acceleration.**

<p align="center">
  <a href="https://pypi.org/project/termux-bitnet/"><img src="https://img.shields.io/pypi/v/termux-bitnet?color=3775A9&logo=pypi&logoColor=white&label=PyPI" alt="PyPI Version"></a>
  <a href="https://www.npmjs.com/package/termux-bitnet"><img src="https://img.shields.io/npm/v/termux-bitnet?color=CB3837&logo=npm&logoColor=white&label=npm" alt="npm Version"></a>
  <a href="https://github.com/uno-km/termux-bitnet/releases/tag/v2.0.0"><img src="https://img.shields.io/github/v/release/uno-km/termux-bitnet?color=0969da&logo=github&logoColor=white&label=Release" alt="GitHub Release"></a>
  <a href="https://uno-km.vercel.app/lib/bitnet/"><img src="https://img.shields.io/badge/Docs-Official%20Portal-004499.svg?logo=googlechrome&logoColor=white" alt="Documentation Portal"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?logo=apache&logoColor=white" alt="License"></a>
  <img src="https://img.shields.io/badge/Core-ARM64%20NEON%20%7C%20DotProd%20%7C%20Vulkan-brightgreen.svg?logo=cplusplus&logoColor=white" alt="Core Acceleration">
  <img src="https://img.shields.io/badge/Models-BitNet%20%7C%20Falcon--E%20%7C%20Falcon3--7B-purple.svg" alt="Supported Models">
  <img src="https://img.shields.io/badge/Fleet-Galaxy%20S25%20%7C%20A53%20%7C%20A35-orange.svg" alt="Tested Hardware">
</p>

---

### 🏛️ Executive Engineering Disclosure: The v2.0.0 Sovereign Ternary Breakthrough

`termux-bitnet v2.0.0` represents a generational architectural leap from a single-model experimental wrapper into a **universal, multi-model 1.58-bit on-device inference runtime**. 

This release mathematically resolves the notorious **ternary numerical collapse ("word salad")** that has plagued the global BitNet community, introduces a **zero-overhead dynamic activation dispatcher**, and breaks mobile memory boundaries by executing **7.45B parameter models on 6GB RAM smartphones without OOM crashes**.

#### 📚 Official Academic & Upstream Credibility
* **Foundation Technical Whitepaper**: [AOSF-TR-2026-BITNET-TERNARY-02: Root Cause Analysis of Ternary Numerical Collapse and Dynamic Activation Engine](https://uno-km.vercel.app/labs/?menu=research-papers)
* **Upstream Contributions to Microsoft**:
  * [microsoft/BitNet #551](https://github.com/microsoft/BitNet/pull/551): Resolved ARM QK=128 stride memory layout desynchronization and word salad.
  * [microsoft/BitNet #624](https://github.com/microsoft/BitNet/pull/624): Completed 1x4_32W parallel NEON `sdot` hardware acceleration kernel and automated Android Termux tooling.
* **Upstream Contributions to GGML**:
  * [ggml-org/whisper.cpp #4089](https://github.com/ggml-org/whisper.cpp/pull/4089): Mobile heterogeneous GPU-Encoder / CPU-Decoder split-mode architecture.

---

### ⚡ Empirical Real-Device Hardware Fleet Scorecard (Ground Truth)

All benchmarks were empirically measured on genuine Samsung Galaxy hardware under unrooted Android Termux Bionic libc environments across 4 canonical 1.58-bit model families:

| Target Model | Parameter / Size | Architecture / Activation | Device & SoC | Prompt Eval | Token Generation | Empirical Verification Status |
|---|:---:|:---:|---|:---:|:---:|---|
| **Falcon-E-1B** | 1.0B (635 MB) | SwiGLU (SiLU) | **Galaxy A53** (Exynos 1280) | 1,986 ms | **9.69 tok/s** | **REAL-TIME (Human Reading Speed)** |
| **BitNet-2B** | 2.0B (1.13 GB) | Squared ReLU + Sub-Norm | **Galaxy S25** (Snapdragon 8 Elite) | 1,269 ms | **3.95 tok/s** | **PASS (100% Coherent Output)** |
| **BitNet-2B** | 2.0B (1.13 GB) | Squared ReLU + Sub-Norm | **Galaxy A53** (Exynos 1280) | 1,382 ms | **5.91 tok/s** | **PASS (100% Coherent Output)** |
| **BitNet-2B** | 2.0B (1.13 GB) | Squared ReLU + Sub-Norm | **Galaxy A35** (Exynos 1380) | 5,386 ms | **1.57 tok/s** | **PASS (100% Coherent Output)** |
| **BitNet-Embed** | 268M (367 MB) | 1.58-bit Vector Search | **Galaxy A53** (Exynos 1280) | 126 ms | **30.68 tok/s** | **PASS (Zero-Copy Mmap)** |
| **Falcon3-7B** | 7.45B (3.05 GB) | SwiGLU (SiLU) | **Galaxy A53** (6GB RAM / E1280) | 7,170 ms | **2.00 tok/s** | **PASS (6GB RAM OOM Defense)** |
| **Falcon3-7B** | 7.45B (3.05 GB) | SwiGLU (SiLU) | **Galaxy A35** (6GB RAM / E1380) | 16,386 ms | **0.57 tok/s** | **PASS (6GB RAM OOM Defense)** |

---

### 🔬 Key Technical Breakthroughs in v2.0.0

#### 1. Mathematical Elimination of Ternary Numerical Collapse
Upstream forks historically mapped raw bitfields using `(b & 1) - (b >> 1)`. In Microsoft's official specification, weights are offset by +1 ($w_{\text{stored}} = w_{\text{ternary}} + 1$). The legacy mapping turned the 49.6% inactive zero neurons into +1, causing exponential activation norm explosion across 30 layers.
`termux-bitnet v2.0.0` enforces canonical dequantization:
$$w_{\text{ternary}} = (b \& 3) - 1 \implies 00 \to -1,\; 01 \to 0,\; 10 \to +1$$
Coupled with the extraction and accumulation of 32-byte GGUF tensor trailer weight scales ($S_W = \text{mean}(|W|)$), output logits remain perfectly calibrated.

#### 2. Zero-Overhead Dynamic Activation Dispatcher
Standard runtimes hardcode either SiLU or Squared ReLU. `termux-bitnet v2.0.0` inspects the presence of `lay.ffn_sub_norm` to seamlessly auto-dispatch:
* **Microsoft BitNet 2B**: Squared ReLU ($\text{relu}(x)^2$) + Sub-LayerNorm.
* **Falcon-E-1B & Falcon3-7B**: Standard SwiGLU ($\text{SiLU}(x) \cdot \text{up}$) without Sub-LayerNorm.

#### 3. 6GB RAM Smartphone 7.45B Model Execution
Through Zero-Copy mmap weight streaming and bounded KV cache management, 3.05GB model weights are mapped directly from flash storage without duplicating resident set size (RSS), allowing 7.45B parameter LLMs to complete inference on mainstream 6GB RAM devices without triggering Android Low Memory Killer (LMK).

---

## 📦 Installation

### 1. Python SDK (PyPI)
```bash
# Inside Android Termux (prerequisites: clang cmake python openblas)
pkg update && pkg install -y clang cmake python openblas

# Install Termux-BitNet and AMEVA-Runtime
pip install --upgrade termux-bitnet ameva-runtime
```

### 2. Node.js CLI (npm)
```bash
npm install -g termux-bitnet @ameva/runtime
```

### 3. One-Touch Native Installer
```bash
curl -sSL https://raw.githubusercontent.com/uno-km/termux-bitnet/main/install.sh | bash
```

---

## 🚀 Quickstart Recipes

### 1. Python Programmatic Inference
```python
from termux_bitnet import BitNetEngine, BitNetConfig

# Configure for real-time Falcon-E-1B or BitNet-2B
config = BitNetConfig(
    model_path="~/.cache/termux-bitnet/models/falcon-e-1b-instruct-i2_s.gguf",
    device="auto",        # "auto", "cpu", or "gpu"
    n_threads=4,
    temperature=0.7,
    top_p=0.95
)

with BitNetEngine(config) as engine:
    print("[Prompt]: Explain the theory of relativity in one sentence.")
    print("[Response]: ", end="", flush=True)
    for token in engine.generate_stream("Explain the theory of relativity in one sentence:"):
        print(token, end="", flush=True)
    print()
    metrics = engine.get_last_metrics()
    print(f"Speed: {metrics.tokens_per_second:.2f} tok/s")
```

### 2. Standalone CLI Usage
```bash
# Run 1B real-time conversational model
termux-bitnet run -m models/falcon-e-1b-instruct-i2_s.gguf \
  -p "What is the capital of South Korea?" -t 4

# Run 7.45B model on 6GB RAM device
termux-bitnet run -m models/falcon3-7b-instruct-1.58bit-i2_s.gguf \
  -p "Solve this riddle: I speak without a mouth..." -t 4
```

---

## 📑 Supported Pretrained Models

| Model Identifier | Parameter Count | Disk Footprint | Target Use Case | Recommended Hardware |
|---|:---:|:---:|---|---|
| `falcon-e-1b` | 1.0B | 635 MB | Real-Time Mobile Dialogue (9.69 tok/s) | Galaxy A53 / A35 / All Devices |
| `bitnet-2b` | 2.0B | 1.13 GB | General Reasoning & Q&A | Galaxy S25 / A53 / A35 |
| `bitnet-embed-270m` | 268M | 367 MB | On-Device Vector Search & Local RAG | All Devices (30+ tok/s) |
| `falcon3-7b` | 7.45B | 3.05 GB | Advanced Coding & Complex Reasoning | 6GB+ RAM Devices (A53, A35, S25) |

---

## 🌐 Ecosystem Links & Documentation

* **Official Documentation Portal**: [https://uno-km.vercel.app/lib/bitnet/](https://uno-km.vercel.app/lib/bitnet/)
* **Foundation Research Lab**: [https://uno-km.vercel.app/labs/](https://uno-km.vercel.app/labs/)
* **License**: Apache-2.0
* **Governance**: AMEVA Open-Source Foundation (AOSF) & @uno-km
