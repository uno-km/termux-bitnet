# termux-bitnet (npm)

> **Ultra-lightweight Node.js & TypeScript Thin Gateway for 1.58-bit (i2_s) BitNet On-Device Inference on Android Termux & ARM64.**

<p align="center">
  <a href="https://www.npmjs.com/package/termux-bitnet"><img src="https://img.shields.io/npm/v/termux-bitnet?color=CB3837&logo=npm&logoColor=white&label=npm" alt="npm Version"></a>
  <a href="https://www.npmjs.com/package/termux-bitnet"><img src="https://img.shields.io/npm/dm/termux-bitnet?color=CB3837&logo=npm&logoColor=white&label=npm%20Downloads" alt="npm Downloads"></a>
  <a href="https://pypi.org/project/termux-bitnet/"><img src="https://img.shields.io/pypi/v/termux-bitnet?color=3775A9&logo=pypi&logoColor=white&label=PyPI" alt="PyPI Version"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?logo=apache&logoColor=white" alt="License"></a>
  <img src="https://img.shields.io/badge/Node-%3E%3D16.0.0-brightgreen.svg?logo=nodedotjs&logoColor=white" alt="Node Version">
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

`termux-bitnet` provides an idiomatic, zero-overhead Node.js / TypeScript gateway to execute **1.58-bit quantized large language models (BitNet b1.58)** directly on Android Termux and ARM64 Linux devices.

The underlying tensor operations and SIMD vectorizations are computed by the native C++ NEON engine (`libtermux_bitnet`), while this npm package provides non-blocking stream APIs, hardware diagnostics, and zero-conflict CLI tooling.

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

## 2. Installation

```bash
# Global installation (Provides termux-bitnet-js CLI)
npm install -g termux-bitnet

# Or local project dependency
npm install termux-bitnet
```

---

## 3. CLI Usage

```bash
# 1. Hardware Diagnostic (Check NEON & DotProd SIMD Acceleration)
termux-bitnet-js info

# 2. List Available Verified Models
termux-bitnet-js models

# 3. Download Model
termux-bitnet-js download bitnet-2b

# 4. Run On-Device Inference
termux-bitnet-js run -p "Explain quantum computing in one sentence." -t 4 --temp 0.7 --top-p 0.95
```

---

## 4. Programmatic JavaScript & TypeScript API

### 4.1 Token Streaming (Recommended)

```javascript
const { createEngine } = require('termux-bitnet');

async function main() {
  const engine = createEngine({
    threads: 4,
    temperature: 0.7,
    topP: 0.95,
    topK: 40,
    repeatPenalty: 1.15,
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

## 5. Verified BitNet GGUF Models

| Model Alias | Parameters | Quantization | File Size | Recommended Device |
|---|---|---|---|---|
| `bitnet-2b` | 2.4B | `i2_s` | **1.13 GB** | Flagship Phones (Galaxy S20+, S24, S25, Pixel) |
| `bitnet-large` | 0.7B | `Q4_0` | **404 MB** | Entry-level / Low-RAM ARM64 Devices |
| `bitnet-3b` | 3.3B | `q1_3` | **730 MB** | High-Capacity Mobile Workstations |
| `bitnet-3b-q4` | 3.3B | `Q4_0` | **1.83 GB** | High-Precision Q4 Quantized Model |

---

## 6. Official Resources

* **Documentation Site**: [https://uno-km.github.io/termux-bitnet/](https://uno-km.github.io/termux-bitnet/)
* **PyPI Package**: [https://pypi.org/project/termux-bitnet/](https://pypi.org/project/termux-bitnet/)
* **GitHub Repository**: [https://github.com/uno-km/termux-bitnet](https://github.com/uno-km/termux-bitnet)

---

## 7. License

Apache License 2.0. Copyright (c) 2026 uno-km (AMEVA Foundation).