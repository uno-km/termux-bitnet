# termux-bitnet

> **1-Bit (1.58-bit) LLM Inference Engine with ARM64 DotProd SIMD Acceleration for Android Termux**  
> *Native C++ Core · Unicode NFC Subword Tokenizer · Fail-Fast Compilation · Zero Heavy Framework Lock-in*

---

## ⚡ 5-Minute Quickstart

### Python Installation

`ash
# In Android Termux:
pkg update && pkg install -y clang cmake python openblas
pip install termux-bitnet
`

### Python SDK Usage

`python
from termux_bitnet import BitNetEngine

engine = BitNetEngine()
tokens = engine.tokenize("안녕하세요 AMEVA BitNet입니다.")
print("Token Count:", len(tokens))
`

---

## 📚 Official Documentation

- **Official Web Documentation**: [https://uno-km.vercel.app/lib/bitnet/](https://uno-km.vercel.app/lib/bitnet/)
- **GitHub Repository**: [https://github.com/uno-km/termux-bitnet](https://github.com/uno-km/termux-bitnet)
- **License**: Apache-2.0