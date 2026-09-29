# Release Notes - termux-bitnet v1.4.6

**Release Tag**: `v1.4.6`  
**Distribution Channels**: PyPI (`termux-bitnet`), NPM (`termux-bitnet`), GitHub Releases  
**Target Platform**: Android Termux (ARM64 / aarch64 Bionic)  
**License**: Apache-2.0  

---

## Highlights & Key Architectural Changes

### 1. Unified 5-Backend Standardization
- **Ecosystem Whitelist Governance**: Aligned all CLI subcommands (`run`, `chat`, `serve`, `benchmark`) to the standard 5-backend options: `["auto", "gpu", "vulkan", "opencl", "cpu"]`.
- **Fail-Fast Rejection**: Passing unauthorized parameters triggers immediate rejection with strict diagnostics.

### 2. ARM64 NEON & DotProd SIMD Validation
- **Zero-Regression Verification**: Validated 29 passed unit tests with pure NEON and DotProd acceleration under Termux Android environments.
