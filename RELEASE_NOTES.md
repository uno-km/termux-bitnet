# Release Notes - termux-bitnet v1.4.5

**Release Tag**: `v1.4.5`  
**Distribution Channels**: PyPI (`termux-bitnet`), NPM (`termux-bitnet`), GitHub Releases  
**Target Platform**: Android Termux (ARM64 / aarch64 Bionic)  
**License**: Apache-2.0  

---

## Highlights & Key Architectural Changes

### 1. 100% Zero-Hardcoding Dynamic Provisioning Architecture
- **Eradicated Static Version Fallbacks**: Permanently eliminated static fallback strings (`1.4.0`) from `install.sh` and `termux_bitnet/installer.py`.
- **Unified 3-Tier Resolution Protocol**:
  1. **Tier 1 (Explicit Environment Overrides)**: Prioritizes `TERMUX_BITNET_RELEASE_BASE` and `TERMUX_BITNET_RELEASE_TAG`.
  2. **Tier 2 (GitHub Releases Latest Canonical SSOT)**: Directly fetches canonical binary assets (`libtermux_bitnet.so`, `termux-bitnet-android-aarch64.tar.gz`) from `https://github.com/uno-km/termux-bitnet/releases/latest/download/`.
  3. **Tier 3 (Runtime Dynamic Version Resolution)**: Binds to currently installed package version tags dynamically via `_resolve_package_version()`.
- **Dynamic HTTP User-Agent**: Replaced static headers with dynamic package version introspection (`termux-bitnet-installer/{ver}`).

### 2. Fast-Track Direct SO Deployment & Invariant Extraction
- **Bionic ELF Direct Loading**: `install.sh` provisions `libtermux_bitnet.so` directly to `$PREFIX/lib` with zero compilation latency.
- **Full Packaging Parity**: Aligned `pyproject.toml`, `package.json`, and `termux_bitnet/__init__.py` to `1.4.5`.

---

## Detailed Changelog

### Changed
- `install.sh`: Dynamic version resolution via GitHub Releases API and `--upgrade` pip provisioning.
- `termux_bitnet/installer.py`: Replaced static release URLs with prioritized 3-Tier candidate URL generator.
- `CHANGELOG.md`: Added release documentation for `v1.4.5`.
- Package manifests bumped to `1.4.5`.
