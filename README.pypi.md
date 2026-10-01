# Termux-BitNet (Python)

[![PyPI](https://img.shields.io/pypi/v/termux-bitnet.svg?style=flat-square&color=0369a1)](https://pypi.org/project/termux-bitnet/)
[![Python](https://img.shields.io/pypi/pyversions/termux-bitnet.svg?style=flat-square)](https://pypi.org/project/termux-bitnet/)
[![License](https://img.shields.io/badge/License-Apache_2.0-004499.svg?style=flat-square)](https://github.com/uno-km/termux-bitnet)

> Sovereign 1.58-Bit On-Device LLM Inference Engine with ARM64 NEON DotProd SIMD & Native Vulkan GPU Acceleration

## Installation

```bash
pip install termux-bitnet
```

## Quickstart

```python
from termux_bitnet import BitNetEngine, BitNetConfig

# 1. Initialize engine with multi-model support (BitNet 2B, Falcon-E 1B, Falcon3 7B)
config = BitNetConfig(
    model_path="~/.cache/termux-bitnet/models/falcon-e-1b-instruct-i2_s.gguf",
    device="auto",        # "auto", "cpu", or "gpu" (Vulkan via ameva-runtime)
    n_threads=4,
    temperature=0.7,
    top_p=0.95
)

# 2. Stream tokens in real time (9.69 tok/s on Galaxy A53)
with BitNetEngine(config) as engine:
    print("[Prompt]: Explain quantum entanglement in one sentence.")
    print("[Response]: ", end="", flush=True)
    for token in engine.generate_stream("Explain quantum entanglement in one sentence:"):
        print(token, end="", flush=True)
    print()
    metrics = engine.get_last_metrics()
    print(f"Speed: {metrics.tokens_per_second:.2f} tok/s | Prompt tokens: {metrics.prompt_tokens}")

```

## Description
Executes 1.58-bit ternary quantized weights {-1, 0, +1} directly via hand-vectorized ARM64 NEON assembly kernels and native Vulkan compute shaders powered by AMEVA-Runtime. Features a dynamic zero-overhead activation dispatcher supporting Squared ReLU (Microsoft 2B) and SwiGLU (Falcon-E-1B / Falcon3-7B) alongside Zero-Copy mmap streaming for 7.45B model execution on 6GB RAM smartphones.

## Documentation
- [Official Documentation & API Reference](https://uno-km.vercel.app/lib/bitnet/)
- [GitHub Repository](https://github.com/uno-km/termux-bitnet)

## License
Apache-2.0 License. Copyright (c) 2026 Eunho Kim (@uno-km).
