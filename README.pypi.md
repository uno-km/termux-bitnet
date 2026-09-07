# termux-bitnet

> **Production 1.58-bit (i2_s) BitNet On-Device Inference SDK for Android Termux & ARM64.**  
> *Native C++17 Core · ARM64 NEON & DotProd (`vdotq_s32`) Acceleration · Zero-Mock / Fail-Fast Guarantee*

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

## ⚡ 5-Minute Quickstart

### 1. Installation

```bash
# In Android Termux:
pkg update && pkg install -y clang cmake python openblas libandroid-execinfo
pip install termux-bitnet
```

### 2. Download Model

```bash
termux-bitnet download bitnet-2b
```

### 3. Run Inference via CLI

```bash
termux-bitnet run -m ~/.cache/termux-bitnet/models/bitnet-2b-ggml-model-i2_s.gguf \
  -p "The capital of South Korea is" -n 16 -t 4
```

### 4. Python SDK Usage

```python
from termux_bitnet import BitNetEngine, BitNetConfig

# Initialize engine with verified 1.58-bit model
config = BitNetConfig(
    model_path="models/bitnet-2b-ggml-model-i2_s.gguf",
    n_threads=4,
    temperature=0.7,
    top_p=0.95,
)
engine = BitNetEngine(config)

# Stream generation
for chunk in engine.generate_stream("Explain quantum computing in one sentence:", max_tokens=64):
    print(chunk, end="", flush=True)
print()
```

---

## 📚 Official Resources

- **GitHub Repository**: [https://github.com/uno-km/termux-bitnet](https://github.com/uno-km/termux-bitnet)
- **Web Documentation**: [https://uno-km.vercel.app/lib/bitnet/](https://uno-km.vercel.app/lib/bitnet/)
- **License**: Apache-2.0