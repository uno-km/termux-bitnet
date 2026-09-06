# Changelog

All notable changes to 	ermux-bitnet will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-09-07

### Added
- Direct integration with `BitNetAdapter` from `ameva_runtime.adapters` SSOT.
- Strict hardware acceleration verification and Fail-Fast on missing NEON/dotprod instruction set.
- English localization for diagnostics and CLI messages.

---

## [1.1.5] - 2026-09-05

### Changed
- Synchronized ameva-runtime unified acceleration bridge and updated installation toolchain.
- Refined platform detection comments and hardware profile SSOT integration.

---

## [1.1.4] - 2026-09-05

### Changed
- Migrated hardware acceleration dependency to unified `ameva-runtime>=2.0.0` and `@ameva/runtime>=2.0.0`.
- Enforced strict Fail-Fast compilation in CMake build extension (RuntimeError on missing toolchain or build failure).
- Eradicated silent fallback and return paths in native C++ bindings.

---

## [1.1.1] - 2026-09-02

### Added
- **Unicode NFC Subword Tokenizer**: Replaced heuristic byte division with C FFI tokenization and Unicode NFC regex fallback.
- **Fail-Fast Native Build**: Enforced 
aise RuntimeError on CMake build errors in setup.py.

### Cleaned
- Purged 20+ legacy wheel artifacts from repository tree.

### Verification
- **Unit Tests**: 20 / 20 passed with 100% assertion coverage.