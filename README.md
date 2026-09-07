# Termux-BitNet

> **Production 1.58-bit (i2_s) BitNet On-Device Inference SDK with Native Vulkan Compute GPU Acceleration for Android Termux & ARM64.**

<p align="center">
  <a href="https://pypi.org/project/termux-bitnet/"><img src="https://img.shields.io/pypi/v/termux-bitnet?color=3775A9&logo=pypi&logoColor=white&label=PyPI" alt="PyPI Version"></a>
  <a href="https://www.npmjs.com/package/termux-bitnet"><img src="https://img.shields.io/npm/v/termux-bitnet?color=CB3837&logo=npm&logoColor=white&label=npm" alt="npm Version"></a>
  <a href="https://github.com/uno-km/termux-bitnet/releases/tag/v1.4.0"><img src="https://img.shields.io/github/v/release/uno-km/termux-bitnet?color=0969da&logo=github&logoColor=white&label=Release" alt="GitHub Release"></a>
  <a href="https://uno-km.vercel.app/lib/bitnet/"><img src="https://img.shields.io/badge/Docs-Portal%20(13%20Langs)-004499.svg?logo=googlechrome&logoColor=white" alt="Documentation Portal"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?logo=apache&logoColor=white" alt="License"></a>
  <img src="https://img.shields.io/badge/GPU%20Compute-Vulkan%20SPIR--V%20%7C%20Adreno%20%26%20Mali-purple.svg?logo=vulkan&logoColor=white" alt="Vulkan GPU Compute">
  <img src="https://img.shields.io/badge/Core-Native%20C%2B%2B17%20%7C%20NEON%20%7C%20DotProd-brightgreen.svg?logo=cplusplus&logoColor=white" alt="Core C++">
  <img src="https://img.shields.io/badge/Platform-Android%20Termux%20%7C%20ARM64%20%7C%20Linux-orange.svg?logo=android&logoColor=white" alt="Platform">
</p>

---

> [!NOTE]
> ### ⚡ Major Breakthrough: Native Vulkan Compute GPU Acceleration via AMEVA-Runtime
>
> Starting in **v1.4.0**, `termux-bitnet` natively offloads the entire BitNet 1.58-bit transformer pipeline to mobile GPUs (Qualcomm Adreno & ARM Mali) through **AMEVA-Runtime**.
>
> * **Permanent VRAM Residency**: All 30 transformer layers (498 MB) and FP16 LM Head (626 MB) pre-allocated in unified GPU buffers with **zero bus traffic** per token.
> * **Full-Pipeline On-Chain Execution (`DispatchFullTokenChain`)**: Fuses all 30 layers into a single `VkCommandBuffer` submission and a single fence wait per token, cutting driver submission overhead by 99.4%.
> * **FP16 LM Head Offload (`bitnet_gemv_f16.comp`)**: Accelerates the 128,256-dim vocabulary projection on GPU with `unpackHalf2x16` SIMD dot products.
> * **Empirical Speedups**:
>   - **Samsung Galaxy S25 (Adreno 830 GPU)**: **17.558 tok/s** (**12.58x speedup** over CPU baseline).
>   - **Samsung Galaxy A35 5G (Mali-G68 GPU)**: **3.471 tok/s** (**5.94x speedup** over CPU baseline).

---

### Empirical Real-Device Benchmarks (Microsoft BitNet b1.58 2B-4T)

| Target Device | SoC / Microarchitecture | Compute Backend | Token Generation | Prompt Eval Time | Speedup | Verification Status |
|---|---|---|---|---|---|---|
| **Samsung Galaxy S25** | Snapdragon 8 Elite (Adreno 830) | **AMEVA Vulkan GPU Full Pipeline** | **17.558 tok/s** | **205.9 ms** | **12.58x** | **Verified (Ground Truth)** |
| Samsung Galaxy S25 | Snapdragon 8 Elite (Oryon CPU) | Native CPU (4 Threads) | 1.396 tok/s | 2,041.0 ms | 1.00x | Baseline |
| **Samsung Galaxy A35 5G** | Exynos 1380 (Mali-G68) | **AMEVA Vulkan GPU Full Pipeline** | **3.471 tok/s** | **1,552.8 ms** | **5.94x** | **Verified (Ground Truth)** |
| Samsung Galaxy A35 5G | Exynos 1380 (Cortex-A78 CPU) | Native CPU (4 Threads) | 0.584 tok/s | 8,775.0 ms | 1.00x | Baseline |
| Samsung Galaxy S20 | Snapdragon 865 (Kryo 585 CPU) | Native CPU (4 Threads) | 2.990 tok/s | 334.4 ms | Reference | Historical Baseline |

---

> [!WARNING]
> ### Public Engineering Disclosure & Upstream Contributions: Permanent Elimination of Interim Heuristics
>
> In earlier development iterations prior to `v1.3.0`, when confronted with upstream ARM dequantization mismatches and missing NEON kernel paths in the upstream repository, an interim heuristic fallback was temporarily utilized to produce candidate outputs under mobile device constraints.
>
> This technical limitation has been **completely resolved, validated on real hardware, and permanently eliminated**. Through architectural reverse engineering and direct upstream contributions to Microsoft's official `microsoft/BitNet` ecosystem:
>
> 1. **Upstream PR #551 ([microsoft/BitNet#551](https://github.com/microsoft/BitNet/pull/551))**: Identified and isolated the original ARM `i2_s` tensor corruption ("word salad") and layout divergence on mobile architectures.
> 2. **Upstream PR #624 ([microsoft/BitNet#624](https://github.com/microsoft/BitNet/pull/624))**: Fully implemented the missing `__ARM_NEON` 4-row parallel kernel (`1x4_32W`) utilizing ARMv8.2-A `sdot` hardware dot-product acceleration, automated Android Termux environment detection, and validated genuine on-device inference on Samsung Galaxy devices (Snapdragon 8 Elite and Exynos 1380).
> 3. **Mathematical Resolution of Dequantization Centering**: Solved the 32-way interleaved dequantization center mismatch (correcting unsigned raw $\{0, 1, 2\}$ mapping vs. centered $\{-1, 0, 1\}$ dot product with activation summation), eradicating repetitive token degeneration defects.
> 4. **Strict Zero-Mock & Fail-Fast Engineering Standard**: Operating strictly with genuine on-device C++ and Vulkan GPU inference. If a native binary or kernel cannot execute, the engine strictly fails fast with explicit error codes and remediation steps rather than emitting deceptive mock responses.

---

## 1. Overview & Architecture

`termux-bitnet` is an optimized on-device inference engine and dual SDK (Python & Node.js) engineered for running **1.58-bit quantized Large Language Models (BitNet b1.58)** natively on Android Termux, ARM64 mobile processors, and edge devices.

```text
[Python Application / CLI]        [Node.js / TypeScript App]
       │                                     │
       ▼ (BitNetEngine / ctypes)             ▼ (BitNetEngine / FFI)
[termux-bitnet Python SDK]        [termux-bitnet npm Thin Gateway]
       │                                     │
       └──────────────────┬──────────────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
[Native C++17 BitNet Core]    [AMEVA-Runtime Vulkan Engine]
       │ (ARM NEON DotProd)              │ (SPIR-V Compute Shaders)
       ▼                                 ▼
[ARM64 CPU: 4 Big Cores]      [Mobile GPU: Adreno 830 / Mali-G68]
```

---

## 2. Installation & Verification

### 2.1 Python Package with Vulkan GPU Acceleration (PyPI)

```bash
# Inside Android Termux (prerequisites: clang cmake python openblas)
pkg update && pkg install -y clang cmake python openblas

# Install Termux-BitNet and AMEVA-Runtime for Vulkan GPU acceleration
pip install termux-bitnet ameva-runtime
```

### 2.2 Node.js / TypeScript Thin Gateway (npm)

```bash
# Global CLI installation (Provides 'termux-bitnet-js' command)
npm install -g termux-bitnet @ameva/runtime
```

### 2.3 Automated Installer (Precompiled Binary or Fast Native Build)

```bash
curl -sL https://raw.githubusercontent.com/uno-km/termux-bitnet/main/install.sh | bash
```

---

## 3. CLI Usage

### 3.1 Python CLI (`termux-bitnet`)

```bash
# 1. Hardware Diagnostic (ARM NEON, DotProd SIMD & Vulkan GPU Verification)
termux-bitnet info

# 2. Download Model with HTTP Range Resume Support
termux-bitnet download bitnet-2b

# 3. Run On-Device Inference with Native Vulkan GPU Acceleration
termux-bitnet run -m ~/.cache/termux-bitnet/models/bitnet-2b-ggml-model-i2_s.gguf \
  -p "Explain quantum computing in one sentence." \
  --device gpu -t 4 -c 2048 -n 64 --temp 0.7 --top-p 0.95
```

### 3.2 Node.js CLI (`termux-bitnet-js`)

```bash
# 1. Hardware Diagnostic
termux-bitnet-js info

# 2. Run Inference via Node.js Gateway with GPU backend
termux-bitnet-js run -m ~/.cache/termux-bitnet/models/bitnet-2b-ggml-model-i2_s.gguf \
  -p "Explain quantum computing in one sentence." -d gpu -t 4 -n 64
```

---

## 4. Programmatic API

### 4.1 Python SDK (with Vulkan GPU Mode)

```python
from termux_bitnet import BitNetEngine, BitNetConfig

# 1. Configure Engine Parameters with Vulkan GPU Acceleration
config = BitNetConfig(
    model_path="~/.cache/termux-bitnet/models/bitnet-2b-ggml-model-i2_s.gguf",
    device="gpu",          # "gpu" (Vulkan via AMEVA-Runtime), "cpu", or "auto"
    n_threads=4,
    temperature=0.7,
    top_p=0.95,
    top_k=40,
    min_p=0.05,
    repeat_penalty=1.15,
)

# 2. Stream Generation with Dynamic Parameters
with BitNetEngine(config) as engine:
    print("[Prompt]: Write a Python palindrome check function")
    print("[Response]: ", end="", flush=True)
    for token in engine.generate_stream("Write a Python palindrome check function:"):
        print(token, end="", flush=True)
    print()
    metrics = engine.get_last_metrics()
    print(f"Speed: {metrics.tokens_per_second:.2f} tok/s, Prompt tokens: {metrics.prompt_tokens}")
```

### 4.2 Node.js & TypeScript SDK

```javascript
const { createEngine } = require('termux-bitnet');

async function main() {
  const engine = createEngine({
    modelPath: '~/.cache/termux-bitnet/models/bitnet-2b-ggml-model-i2_s.gguf',
    device: 'gpu',         // 'gpu' (Vulkan), 'cpu', or 'auto'
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

### 4.3 Direct AMEVA-Runtime Adapter API

```python
from ameva_runtime.adapters.bitnet import BitnetAdapter

adapter = BitnetAdapter()
adapter.load_model("~/.cache/termux-bitnet/models/bitnet-2b-ggml-model-i2_s.gguf")

for token in adapter.generate("Explain quantum computing in one sentence:"):
    print(token, end="", flush=True)
print()
```

---

## 5. Configuration Parameter Matrix (`BitNetConfig`)

| CLI Flag | Python (`BitNetConfig`) | Node.js (`BitNetOptions`) | Default | Description |
|---|---|---|---|---|
| `-m, --model` | `model_path` | `modelPath` | `""` | Path to GGUF model binary |
| `-p, --prompt` | `prompt` | `prompt` | `""` | Input prompt text |
| `-d, --device` | `device` | `device` | `"auto"` | Compute backend (`auto`, `gpu`, `cpu`) |
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

## 6. Official Documentation & Specifications

* **Official Documentation Site**: [https://uno-km.vercel.app/lib/bitnet/](https://uno-km.vercel.app/lib/bitnet/)
* **AI Agent Context Feed**: [llms.txt](https://uno-km.vercel.app/lib/bitnet/llms.txt)
* **Full Technical Specification**: [llms-full.txt](https://uno-km.vercel.app/lib/bitnet/llms-full.txt)

---

## 7. License & Foundation

Released under the **Apache License 2.0**.  
Engineered under the **AMEVA Open-Source Foundation (AOSF)** & **uno-km** ecosystem.
