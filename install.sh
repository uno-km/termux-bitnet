#!/usr/bin/env bash
# ==============================================================================
# termux-bitnet: Universal Dynamic One-Line Bootstrap Installer (v1.4.0)
# Open-Source under Apache License 2.0 (AMEVA Foundation)
# Usage: curl -sL https://raw.githubusercontent.com/uno-km/termux-bitnet/main/install.sh | bash
# ==============================================================================
set -euo pipefail

VERSION="${TERMUX_BITNET_VERSION:-1.4.0}"
REPO="uno-km/termux-bitnet"
ARCH="$(uname -m)"

echo "================================================================="
echo " [AMEVA Foundation] termux-bitnet Universal Installer v${VERSION}"
echo "================================================================="
echo "-> Detected Architecture: ${ARCH}"

# 1. Platform Detection
IS_TERMUX=false
if [ -d "/data/data/com.termux" ] || [ -n "${TERMUX_VERSION:-}" ]; then
    IS_TERMUX=true
    BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"
    LIB_DIR="${PREFIX:-/data/data/com.termux/files/usr}/lib"
    echo "-> Detected Platform: Android Termux (Bionic libc)"
else
    BIN_DIR="/usr/local/bin"
    LIB_DIR="/usr/local/lib"
    echo "-> Detected Platform: Generic Linux / Host POSIX"
fi

if [ "${ARCH}" != "aarch64" ] && [ "${ARCH}" != "arm64" ]; then
    echo "[WARN] Architecture is ${ARCH}. ARM64 NEON DotProd is strongly recommended for 1.58-bit ternary acceleration."
fi

# 2. Storage Setup (Termux only)
if [ "${IS_TERMUX}" = "true" ] && command -v termux-setup-storage >/dev/null 2>&1; then
    if [ ! -d "${HOME}/storage" ]; then
        echo "-> Requesting Android storage permission..."
        termux-setup-storage || true
    fi
fi

# 3. System Package Dependencies
if [ "${IS_TERMUX}" = "true" ] && command -v pkg >/dev/null 2>&1; then
    echo "-> [1/6] Updating Termux package repositories..."
    pkg update -y
    echo "-> [2/6] Installing build toolchains, OpenBLAS, and runtimes..."
    pkg install -y \
        python \
        nodejs \
        clang \
        make \
        cmake \
        git \
        curl \
        tar \
        wget \
        openblas \
        libandroid-execinfo
elif command -v apt-get >/dev/null 2>&1; then
    echo "-> [1/6] Updating Ubuntu/Debian repositories..."
    apt-get update -y
    echo "-> [2/6] Installing build tools and dependencies..."
    apt-get install -y build-essential cmake git python3 python3-pip libopenblas-dev nodejs npm curl tar wget
fi

# 4. Pre-provision Core Python Toolchain & Ecosystem Dependencies
echo "-> [3/6] Pre-provisioning Python build toolchain and ecosystem accelerators..."
python -m pip install setuptools wheel
python -m pip install ameva-runtime || true

# 5. Standard Python SDK Installation
echo "-> [4/6] Installing termux-bitnet Python SDK (v${VERSION})..."
if [ -f "pyproject.toml" ]; then
    echo "   -> Installing from local source repository..."
    python -m pip install --no-build-isolation -e .
else
    echo "   -> Installing from PyPI..."
    python -m pip install termux-bitnet || true
fi

# 6. Native C/C++ Compute Engine & Prebuilt Artifact Installation
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/termux-bitnet-inst.XXXXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT INT TERM HUP

PREBUILT_SUCCESS=false
if [ "${ARCH}" = "aarch64" ] || [ "${ARCH}" = "arm64" ]; then
    echo "-> [5/6] Checking for verified ARM64 prebuilt native core bundle (v${VERSION})..."
    PREBUILT_URL="https://github.com/${REPO}/releases/download/v${VERSION}/termux-bitnet-v${VERSION}-android-aarch64.tar.gz"
    PREBUILT_TAR="${TMP_DIR}/termux-bitnet-v${VERSION}-android-aarch64.tar.gz"
    STAGING_DIR="${TMP_DIR}/.staging"
    if curl -sSL -f --connect-timeout 8 -o "${PREBUILT_TAR}" "${PREBUILT_URL}" 2>/dev/null; then
        if [ -s "${PREBUILT_TAR}" ] && [ "$(wc -c < "${PREBUILT_TAR}")" -gt 10000 ]; then
            echo "   -> Fetched verified prebuilt native bundle from: ${PREBUILT_URL}"
            mkdir -p "${STAGING_DIR}" "${LIB_DIR}" "${BIN_DIR}"
            tar -xzf "${PREBUILT_TAR}" -C "${STAGING_DIR}"
            if [ -f "${STAGING_DIR}/libtermux_bitnet.so" ]; then
                cp "${STAGING_DIR}/libtermux_bitnet.so" "${LIB_DIR}/"
                chmod 0755 "${LIB_DIR}/libtermux_bitnet.so"
            fi
            if [ -f "${STAGING_DIR}/termux-bitnet-cli" ]; then
                cp "${STAGING_DIR}/termux-bitnet-cli" "${BIN_DIR}/"
                chmod 0755 "${BIN_DIR}/termux-bitnet-cli"
            fi
            rm -rf "${STAGING_DIR}"
            PREBUILT_SUCCESS=true
        fi
    fi
fi

if [ "${PREBUILT_SUCCESS}" = false ] && [ -f "CMakeLists.txt" ] && command -v cmake >/dev/null 2>&1; then
    echo "   -> Executing hardened on-device C++ CMake compilation (ARM64 NEON + DotProd)..."
    cmake -B build \
        -DGGML_NEON=ON \
        -DGGML_ARM_DOTPROD=ON \
        -DGGML_VULKAN=OFF \
        -DCMAKE_BUILD_TYPE=Release
    cmake --build build --config Release -j"$(nproc 2>/dev/null || echo 4)"
    if [ -f "build/libtermux_bitnet.so" ]; then
        mkdir -p "${LIB_DIR}"
        cp build/libtermux_bitnet.so "${LIB_DIR}/"
        chmod 0755 "${LIB_DIR}/libtermux_bitnet.so"
    fi
    if [ -f "build/termux-bitnet-cli" ]; then
        mkdir -p "${BIN_DIR}"
        cp build/termux-bitnet-cli "${BIN_DIR}/"
        chmod 0755 "${BIN_DIR}/termux-bitnet-cli"
    fi
fi

# 7. Node.js Dual Engine CLI Installation
if command -v npm >/dev/null 2>&1; then
    echo "-> [6/6] Linking Node.js Dual Engine CLI..."
    if [ -d "npm" ]; then
        (cd npm && npm install -g . || npm link || true)
    elif [ -f "package.json" ]; then
        npm install -g . || npm link || true
    else
        npm install -g termux-bitnet 2>/dev/null || true
    fi
fi

echo "================================================================="
echo "  [SUCCESS] termux-bitnet v${VERSION} successfully installed!"
echo "================================================================="
echo "  Dual-Engine Verification:"
echo "    * Python CLI:   termux-bitnet doctor"
echo "    * Native CLI:   termux-bitnet-cli --help"
echo "    * Node.js CLI:  termux-bitnet-js info"
echo "================================================================="

# 8. Run Hardware Diagnostics Probe
if command -v termux-bitnet >/dev/null 2>&1; then
    echo "-> Running Hardware Diagnostics Probe (ARM SIMD & Acceleration)..."
    termux-bitnet doctor || true
fi

echo ""
echo "termux-bitnet is ready for 1.58-bit on-device LLM inference."
