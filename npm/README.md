# Termux-BitNet (Node.js & TypeScript)

[![npm](https://img.shields.io/npm/v/termux-bitnet.svg?style=flat-square&color=b91c1c)](https://www.npmjs.com/package/termux-bitnet)
[![npm downloads](https://img.shields.io/npm/dm/termux-bitnet.svg?style=flat-square&color=b91c1c)](https://www.npmjs.com/package/termux-bitnet)
[![License](https://img.shields.io/badge/License-Apache_2.0-004499.svg?style=flat-square)](https://github.com/uno-km/termux-bitnet)

> Sovereign 1.58-Bit On-Device LLM Inference Engine with ARM64 NEON DotProd SIMD & Native Vulkan GPU Acceleration

## Installation

```bash
npm install termux-bitnet
```

## Quickstart

```typescript
const { createEngine } = require('termux-bitnet');

async function main() {
  // 1. Initialize engine with dynamic activation support
  const engine = createEngine({
    modelPath: '~/.cache/termux-bitnet/models/falcon-e-1b-instruct-i2_s.gguf',
    device: 'auto',      // 'auto', 'cpu', or 'gpu'
    threads: 4,
    temperature: 0.7,
    topP: 0.95
  });

  console.log('[Prompt]: Explain quantum computing in one sentence');
  console.log('[Response]: ');

  await engine.generateStream('Explain quantum computing in one sentence', 64, (token) => {
    process.stdout.write(token);
  });
  console.log('\n');
}

main();

```

## Description
Executes 1.58-bit ternary quantized weights {-1, 0, +1} directly via hand-vectorized ARM64 NEON assembly kernels and native Vulkan compute shaders powered by AMEVA-Runtime. Features a dynamic zero-overhead activation dispatcher supporting Squared ReLU (Microsoft 2B) and SwiGLU (Falcon-E-1B / Falcon3-7B) alongside Zero-Copy mmap streaming for 7.45B model execution on 6GB RAM smartphones.

## Documentation
- [Official Documentation & API Reference](https://uno-km.vercel.app/lib/bitnet/)
- [GitHub Repository](https://github.com/uno-km/termux-bitnet)

## License
Apache-2.0 License. Copyright (c) 2026 Eunho Kim (@uno-km).
