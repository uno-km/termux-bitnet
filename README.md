# termux-bitnet

> **Production 1.58-bit (i2_s) BitNet On-Device Inference SDK & Dual Engine for Android Termux & ARM64.**

<p align="center">
  <a href="https://pypi.org/project/termux-bitnet/"><img src="https://img.shields.io/pypi/v/termux-bitnet?color=3775A9&logo=pypi&logoColor=white&label=PyPI" alt="PyPI Version"></a>
  <a href="https://www.npmjs.com/package/termux-bitnet"><img src="https://img.shields.io/npm/v/termux-bitnet?color=CB3837&logo=npm&logoColor=white&label=npm" alt="npm Version"></a>
  <a href="https://github.com/uno-km/termux-bitnet/releases/tag/v1.1.0"><img src="https://img.shields.io/github/v/release/uno-km/termux-bitnet?color=0969da&logo=github&logoColor=white&label=Release" alt="GitHub Release"></a>
  <a href="https://uno-km.vercel.app/lib/bitnet/"><img src="https://img.shields.io/badge/Docs-Portal%20(13%20Langs)-004499.svg?logo=googlechrome&logoColor=white" alt="Documentation Portal"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?logo=apache&logoColor=white" alt="License"></a>
  <img src="https://img.shields.io/badge/Core-Native%20C%2B%2B17%20%7C%20NEON%20%7C%20DotProd-brightgreen.svg?logo=cplusplus&logoColor=white" alt="Core C++">
  <img src="https://img.shields.io/badge/Platform-Android%20Termux%20%7C%20ARM64%20%7C%20Linux-orange.svg?logo=android&logoColor=white" alt="Platform">
</p>

---

## 1. Overview & Architecture

`termux-bitnet` is an optimized on-device inference engine and dual SDK (Python & Node.js) engineered for running **1.58-bit quantized Large Language Models (BitNet b1.58)** natively on Android Termux, ARM64 mobile processors, and edge devices.

The underlying computation engine executes 1.58-bit ternary quantized weights `{-1, 0, +1}` directly via hand-vectorized ARM64 NEON SIMD and DotProd vector instructions (`vdotq_s32`), replacing floating-point matrix multiplications with integer additions and subtractions under a sub-350MB RAM footprint.

```text
[Python Application / CLI]        [Node.js / TypeScript App]
       │                                     │
       ▼ (BitNetEngine / ctypes)             ▼ (BitNetEngine / FFI)
[termux-bitnet Python SDK]        [termux-bitnet npm Thin Gateway]
       │                                     │
       └──────────────────┬──────────────────┘
                          │
                          ▼ (Strict C ABI: libtermux_bitnet.so)
         [Native C++17 BitNet Core Engine]
                          │
                          ▼
    [ARM64 NEON + DotProd (vdotq_s32) Vector Kernels]
```

---

## 2. Verified BitNet GGUF Model Registry

`termux-bitnet` provides deterministic model downloading and caching from verified Hugging Face repositories with HTTP Range resume capability:

| Model Alias | Hugging Face Repository & File | Parameters | Quantization | File Size | Target Device |
|---|---|---|---|---|---|
| `bitnet-2b` | `microsoft/bitnet-b1.58-2B-4T-gguf` | 2.4B | `i2_s` | **1.13 GB** | Flagship Phones (Galaxy S20+, S24, S25, Pixel) |
| `bitnet-large` | `RichardErkhov/1bitLLM_-_bitnet_b1_58-large-gguf` | 0.7B | `Q4_0` | **404 MB** | Entry-level / Low-RAM ARM64 Devices |
| `bitnet-3b` | `Green-Sky/bitnet_b1_58-3B-GGUF` | 3.3B | `q1_3` | **730 MB** | High-Capacity Mobile Workstations |
| `bitnet-3b-q4` | `RichardErkhov/1bitLLM_-_bitnet_b1_58-3B-gguf` | 3.3B | `Q4_0` | **1.83 GB** | High-Precision Quantized Model |

---

## 3. Installation

### 3.1 Python SDK & CLI (PyPI)

```bash
# In Android Termux or ARM64 Linux
pip install termux-bitnet
```

### 3.2 Node.js SDK & CLI (npm)

```bash
# Global installation (Independent CLI namespace: termux-bitnet-js)
npm install -g termux-bitnet
```

### 3.3 Zero-Drift Source Installation

```bash
git clone https://github.com/uno-km/termux-bitnet.git
cd termux-bitnet
chmod +x install.sh
./install.sh
```

---

## 4. CLI Usage

### 4.1 Python CLI (`termux-bitnet`)

```bash
# 1. Hardware Diagnostic (ARM NEON & DotProd SIMD Verification)
termux-bitnet info

# 2. List Available Verified Models
termux-bitnet models

# 3. Download Model with Range Resume Support
termux-bitnet download bitnet-2b

# 4. Run On-Device Inference
termux-bitnet run -m ~/.cache/termux-bitnet/models/bitnet-2b-ggml-model-i2_s.gguf \
  -p "Explain quantum computing in one sentence." \
  -t 4 -c 2048 -n 64 --temp 0.7 --top-p 0.95
```

### 4.2 Node.js CLI (`termux-bitnet-js`)

```bash
# 1. Hardware Diagnostic
termux-bitnet-js info

# 2. Model Registry List
termux-bitnet-js models

# 3. Run Inference via Node.js Gateway
termux-bitnet-js run -m ~/.cache/termux-bitnet/models/bitnet-2b-ggml-model-i2_s.gguf \
  -p "Explain quantum computing in one sentence." -t 4 -n 64
```

---

## 5. Programmatic API

### 5.1 Python SDK

```python
from termux_bitnet import BitNetEngine, BitNetConfig

# 1. Configure Engine Parameters
config = BitNetConfig(
    model_path="models/bitnet-2b.gguf",
    n_threads=4,
    temperature=0.7,
    top_p=0.95,
    top_k=40,
    min_p=0.05,
    repeat_penalty=1.15,
)

# 2. Stream Generation with Context Manager
with BitNetEngine(config) as engine:
    print("[Prompt]: Write a Python palindrome check function")
    print("[Response]: ", end="", flush=True)
    for token in engine.generate_stream("Write a Python palindrome check function:"):
        print(token, end="", flush=True)
    print()
```

### 5.2 Node.js & TypeScript SDK

```javascript
const { createEngine } = require('termux-bitnet');

async function main() {
  const engine = createEngine({
    modelPath: 'models/bitnet-2b.gguf',
    threads: 4,
    temperature: 0.7,
    topP: 0.95,
  });

  console.log('[Prompt]: Explain quantum computing in one sentence');
  console.log('[Response]: ');

  await engine.generateStream(
    'Explain quantum computing in one sentence',
    64,
    (token) => {
      process.stdout.write(token);
    }
  );
  console.log('\n');
}

main();
```

---

## 6. Configuration Parameter Matrix (`BitNetConfig`)

| CLI Flag | Python (`BitNetConfig`) | Node.js (`BitNetOptions`) | Default | Description |
|---|---|---|---|---|
| `-m, --model` | `model_path` | `modelPath` | `""` | Path to GGUF model binary |
| `-p, --prompt` | `prompt` | `prompt` | `""` | Input prompt text |
| `-t, --threads` | `n_threads` | `threads` | `cores` | Number of CPU worker threads |
| `-c, --ctx-size` | `n_ctx` | `contextSize` | `2048` | KV Cache context window size |
| `-b, --batch-size` | `n_batch` | `batchSize` | `512` | Prompt evaluation batch size |
| `-n, --n-predict` | `n_predict` | `maxTokens` | `128` | Maximum tokens to generate |
| `--temp` | `temperature` | `temperature` | `0.7` | Softmax temperature (0.0 = Greedy) |
| `--top-p` | `top_p` | `topP` | `0.95` | Nucleus Top-P sampling cutoff |
| `--top-k` | `top_k` | `topK` | `40` | Top-K sampling cutoff |
| `--min-p` | `min_p` | `minP` | `0.05` | Min-P relative probability cutoff |
| `--repeat-penalty` | `repeat_penalty` | `repeatPenalty` | `1.15` | Repetition penalty coefficient |
| `-s, --seed` | `seed` | `seed` | `0` | Random seed (0 = non-deterministic) |
| `--system-prompt` | `system_prompt` | `systemPrompt` | `""` | System prompt prefix |
| `-r, --stop` | `stop_tokens` | `stopTokens` | `""` | Stop sequence tokens |

---

## 7. Official Documentation & Specifications

* **Official Documentation Site**: [https://uno-km.github.io/termux-bitnet/](https://uno-km.github.io/termux-bitnet/)
* **AI Agent Context Feed**: [llms.txt](https://uno-km.github.io/termux-bitnet/llms.txt)
* **Full Technical Specification**: [llms-full.txt](https://uno-km.github.io/termux-bitnet/llms-full.txt)

---

## 8. License & Foundation

Released under the **Apache License 2.0**.  
Engineered under the **AMEVA Open-Source Foundation (AOSF)** & **uno-km** ecosystem.