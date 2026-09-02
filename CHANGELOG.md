# Changelog

All notable changes to 	ermux-bitnet will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.1] - 2026-09-02

### Added
- **Unicode NFC Subword Tokenizer**: Replaced heuristic byte division with C FFI tokenization and Unicode NFC regex fallback.
- **Fail-Fast Native Build**: Enforced aise RuntimeError on CMake build errors in setup.py.

### Cleaned
- Purged 20+ legacy wheel artifacts from repository tree.

### Verification
- **Unit Tests**: 20 / 20 passed with 100% assertion coverage.