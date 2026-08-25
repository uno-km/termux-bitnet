# termux-bitnet

> **Ultra-lightweight Node.js & TypeScript Thin Gateway for 1.58-bit (i2_s) BitNet On-Device Inference on Android Termux & ARM64.**

<p align="center">
  <a href="https://www.npmjs.com/package/termux-bitnet"><img src="https://img.shields.io/npm/v/termux-bitnet?color=CB3837&logo=npm&logoColor=white&label=npm" alt="npm Version"></a>
  <a href="https://www.npmjs.com/package/termux-bitnet"><img src="https://img.shields.io/npm/dm/termux-bitnet?color=CB3837&logo=npm&logoColor=white&label=npm%20Downloads" alt="npm Downloads"></a>
  <a href="https://www.npmjs.com/package/termux-bitnet"><img src="https://img.shields.io/npm/dt/termux-bitnet?color=CB3837&logo=npm&logoColor=white&label=Total%20Downloads" alt="npm Total Downloads"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?logo=apache&logoColor=white" alt="License"></a>
  <img src="https://img.shields.io/badge/Node-%3E%3D16.0.0-brightgreen.svg?logo=nodedotjs&logoColor=white" alt="Node Version">
  <img src="https://img.shields.io/badge/Platform-Android%20Termux%20%7C%20ARM64%20%7C%20Linux-orange.svg?logo=android&logoColor=white" alt="Platform">
</p>

---

## 1. Overview & Architecture

`termux-bitnet` provides an idiomatic, zero-overhead Node.js / TypeScript interface to run **1.58-bit quantized large language models (BitNet b1.58)** locally on Android Termux and ARM64 Linux devices.

The heavy tensor math and memory management are handled by the native C++ NEON engine (`libtermux_bitnet`), while this npm package provides non-blocking stream APIs, hardware diagnostics, and automated model provisioning.

```text
[Node.js / TypeScript Application]
       │
       ▼ (createEngine / BitNetEngine)
[termux-bitnet npm Thin Gateway]
       │
       ▼ (Process IPC / C ABI Boundary)
[Native C++ BitNet Core] ──► ARM64 NEON + DotProd SIMD Vector Kernels
```

---

## 2. Verified BitNet GGUF Model Registry

`termux-bitnet` provides single-command downloads from verified Hugging Face repositories with automatic HTTP Range resume support:

| Model Alias | Hugging Face Repository & File | Parameters | File Size | Recommended Device |
|---|---|---|---|---|
| `bitnet-2b` | `microsoft/bitnet-b1.58-2B-4T-gguf` | 2.4B | **1.13 GB** | Flagship Phones (Galaxy S20+, S24, S25, Pixel) |
| `bitnet-large` | `RichardErkhov/1bitLLM_-_bitnet_b1_58-large-gguf` | 0.7B | **404 MB** | Entry-level / Low-RAM ARM64 Devices |
| `bitnet-3b` | `Green-Sky/bitnet_b1_58-3B-GGUF` | 3.3B | **730 MB** | High-Capacity Mobile Workstations |
| `bitnet-3b-q4` | `RichardErkhov/1bitLLM_-_bitnet_b1_58-3B-gguf` | 3.3B | **1.83 GB** | High-Precision Q4 Quantized Model |

---

## 3. Quick Start

### 3.1 Installation

```bash
npm install termux-bitnet
```

### 3.2 CLI Usage (No Code Required)

```bash
# 1. Hardware Diagnostic (Check NEON & DotProd SIMD Acceleration)
npx termux-bitnet info

# 2. List Available Verified Models
npx termux-bitnet models

# 3. Download Official Microsoft 1.58-bit Model (With Resume Support)
npx termux-bitnet download bitnet-2b

# 4. Run On-Device Inference
npx termux-bitnet run -p "Explain harmonic mean in one sentence" -t 8 --temp 0.7 --top-p 0.95
```

---

## 4. Programmatic JavaScript & TypeScript API

### 4.1 Token Streaming (Recommended)

```javascript
const { createEngine } = require('termux-bitnet');

async function main() {
  const engine = createEngine({
    threads: 8,
    temperature: 0.7,
    topP: 0.95,
    topK: 40,
    repeatPenalty: 1.15,
  });

  console.log('[Prompt]: Explain harmonic mean in one sentence');
  console.log('[Response]: ');

  await engine.generateStream(
    'Explain harmonic mean in one sentence',
    128,
    (token) => {
      process.stdout.write(token);
    }
  );
  console.log('\n');
}

main();
```

### 4.2 Promise-based Completion

```typescript
import { createEngine, BitNetOptions } from 'termux-bitnet';

const options: BitNetOptions = {
  threads: 4,
  contextSize: 2048,
  temperature: 0.5,
};

const engine = createEngine(options);
const response = await engine.generate('Write a Python palindrome function:', 64);
console.log(response);
```

### 4.3 Programmatic Model Downloader

```javascript
const { downloadModel, listModels } = require('termux-bitnet');

async function setup() {
  listModels();
  const modelPath = await downloadModel('bitnet-2b');
  console.log(`Model ready at: ${modelPath}`);
}

setup();
```

---

## 5. Parameter Options Reference (`BitNetOptions`)

| Option | Type | Default | Description |
|---|---|---|---|
| `modelPath` | `string` | `""` | Path to GGUF model binary |
| `threads` | `number` | `os.cpus().length` | Number of CPU worker threads |
| `contextSize` | `number` | `2048` | KV Cache context window size |
| `batchSize` | `number` | `512` | Prompt evaluation batch size |
| `temperature` | `number` | `0.7` | Softmax temperature (0.0 = Greedy) |
| `topP` | `number` | `0.95` | Nucleus Top-P sampling cutoff |
| `topK` | `number` | `40` | Top-K sampling cutoff |
| `minP` | `number` | `0.05` | Min-P relative probability cutoff |
| `repeatPenalty` | `number` | `1.15` | Repetition penalty coefficient |
| `systemPrompt` | `string` | `""` | Optional system prompt prefix |
| `stopTokens` | `string` | `""` | Stop sequence tokens |

---

## 6. License

Apache License 2.0. Copyright (c) 2026 uno-km (AMEVA Foundation).\n