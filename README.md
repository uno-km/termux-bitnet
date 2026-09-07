# termux-bitnet

> **Production 1.58-bit (i2_s) BitNet On-Device Inference SDK & Dual Engine for Android Termux & ARM64.**

<p align="center">
  <a href="https://pypi.org/project/termux-bitnet/"><img src="https://img.shields.io/pypi/v/termux-bitnet?color=3775A9&logo=pypi&logoColor=white&label=PyPI" alt="PyPI Version"></a>
  <a href="https://www.npmjs.com/package/termux-bitnet"><img src="https://img.shields.io/npm/v/termux-bitnet?color=CB3837&logo=npm&logoColor=white&label=npm" alt="npm Version"></a>
  <a href="https://github.com/uno-km/termux-bitnet/releases/tag/v1.3.0"><img src="https://img.shields.io/github/v/release/uno-km/termux-bitnet?color=0969da&logo=github&logoColor=white&label=Release" alt="GitHub Release"></a>
  <a href="https://uno-km.vercel.app/lib/bitnet/"><img src="https://img.shields.io/badge/Docs-Portal%20(13%20Langs)-004499.svg?logo=googlechrome&logoColor=white" alt="Documentation Portal"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?logo=apache&logoColor=white" alt="License"></a>
  <img src="https://img.shields.io/badge/Core-Native%20C%2B%2B17%20%7C%20NEON%20%7C%20DotProd-brightgreen.svg?logo=cplusplus&logoColor=white" alt="Core C++">
  <img src="https://img.shields.io/badge/Platform-Android%20Termux%20%7C%20ARM64%20%7C%20Linux-orange.svg?logo=android&logoColor=white" alt="Platform">
</p>

---

> [!WARNING]
> ### ⚠️ Public Engineering Disclosure & Sincere Apology: Permanent Retirement of Interim Heuristic Fallbacks in Favor of Genuine Hardware-Accelerated BitNet Kernels
>
> In earlier development iterations prior to `v1.3.0`, when confronted with upstream ARM dequantization mismatches and missing NEON kernel paths in the upstream repository, an interim heuristic fallback was temporarily utilized to produce candidate outputs under mobile device constraints. **We sincerely apologize to the developer and open-source community for this compromise.**
>
> We are proud to report that this technical limitation has been **completely resolved, validated on real hardware, and permanently eliminated**. Through architectural reverse engineering and direct upstream contributions to Microsoft's official `microsoft/BitNet` ecosystem:
>
> 1. **Upstream PR #551 ([microsoft/BitNet#551](https://github.com/microsoft/BitNet/pull/551))**: Identified and isolated the original ARM `i2_s` tensor corruption ("word salad") and layout divergence on mobile architectures.
> 2. **Upstream PR #624 ([microsoft/BitNet#624](https://github.com/microsoft/BitNet/pull/624))**: Fully implemented the missing `__ARM_NEON` 4-row parallel kernel (`1x4_32W`) utilizing ARMv8.2-A `sdot` hardware dot-product acceleration, automated Android Termux environment detection, and validated genuine on-device inference on Samsung Galaxy devices (Snapdragon 8 Elite and Exynos 1380).
> 3. **Mathematical Resolution of Dequantization Centering**: Solved the 32-way interleaved dequantization center mismatch (correcting unsigned raw $\{0, 1, 2\}$ mapping vs. centered $\{-1, 0, 1\}$ dot product with activation summation), eradicating the infamous repetitive `@` token degeneration defect.
> 4. **Strict Zero-Mock & Fail-Fast Engineering Standard**: As of `v1.3.0`, `termux-bitnet` operates strictly with 100% genuine on-device C++ inference. If a native binary or kernel cannot execute, the engine strictly fails fast with an explicit error code and remediation steps rather than emitting deceptive mock responses.
>
> **Verified Real-Device On-Device Benchmarks (BitNet b1.58 2B-4T i2_s natively inside Android Termux):**
> - **Samsung Galaxy S25** (Snapdragon 8 Elite / Oryon): **1.15 tokens/sec** (~2,814 ms TTFT)
> - **Samsung Galaxy A35 5G** (Samsung Exynos 1380): **0.58 tokens/sec** (~8,501 ms TTFT)

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

## 3. Installation & Verification

### 3.1 Automated Installer (Precompiled Binary or Fast Native Build)

The recommended installation method uses `install.sh`, which automatically downloads verified ARM64 prebuilt binaries from GitHub Releases or compiles the native C++ core on the device:

```bash
git clone https://github.com/uno-km/termux-bitnet.git
cd termux-bitnet
chmod +x install.sh
./install.sh
```

### 3.2 Python Package (PyPI)

```bash
# Inside Android Termux (prerequisites: clang cmake python openblas)
pkg update && pkg install -y clang cmake python openblas
pip install termux-bitnet
```

### 3.3 Node.js / TypeScript Thin Gateway (npm)

```bash
# Global CLI installation (Provides 'termux-bitnet-js' command)
npm install -g termux-bitnet
```

### 3.4 Hardened Manual Compilation Workflow

To compile the native C++ engine manually with verified hardware acceleration on Samsung Exynos (Cortex-A78/A55) or Qualcomm Snapdragon (Oryon/Kryo):

```bash
# 1. Install prerequisites in Termux
pkg install -y clang cmake openblas libandroid-execinfo

# 2. Configure CMake with explicit NEON + DotProd and Clang toolchain
cmake -B build \
  -DGGML_NEON=ON \
  -DGGML_ARM_DOTPROD=ON \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_BUILD_TYPE=Release

# 3. Build native standalone CLI and shared library
cmake --build build --target termux-bitnet-cli -j$(nproc 2>/dev/null || echo 4)
```

> [!TIP]
> **Why our toolchain configuration avoids upstream mobile build pitfalls:**
> - **Eliminates OpenMP Crashes (`__kmpc_dispatch_deinit`)**: Avoids broken NDK OpenMP dependencies by utilizing native C++17 thread pools.
> - **Resolves Math Library Mismatch (`MATH_LIBRARY-NOTFOUND`)**: Directly links Bionic libm (`-lm`) avoiding standard glibc assumption errors.
> - **Prevents Linker Symbol Pollution**: Binds local `build/` artifacts to `LD_LIBRARY_PATH` preventing collisions with Termux system `libllama.so`.

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