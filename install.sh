#!/usr/bin/env bash
# ==============================================================================
# termux-bitnet: Universal Dynamic One-Line Bootstrap Installer (v1.4.4)
# Open-Source under Apache License 2.0 (AMEVA Foundation)
# Usage: curl -sL https://raw.githubusercontent.com/uno-km/termux-bitnet/main/install.sh | bash
# ==============================================================================
set -euo pipefail

if [ -z "${TERMUX_BITNET_VERSION:-}" ]; then
    VERSION="$(curl -sL https://api.github.com/repos/uno-km/termux-bitnet/releases/latest 2>/dev/null | grep '"tag_name":' | head -n 1 | cut -d '"' -f 4 | sed 's/^v//')"
    VERSION="${VERSION:-latest}"
else
    VERSION="${TERMUX_BITNET_VERSION}"
fi
REPO="uno-km/termux-bitnet"
ARCH="$(uname -m)"

echo "================================================================="
echo " [AMEVA Foundation] termux-bitnet Universal Installer (${VERSION})"
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

# 3. System Runtime & Compilers
MISSING_PKGS=""
for cmd_pkg in "python:python" "clang:clang" "cmake:cmake" "git:git" "curl:curl"; do
    CMD="${cmd_pkg%%:*}"
    PKG="${cmd_pkg##*:}"
    if ! command -v "${CMD}" >/dev/null 2>&1; then
        MISSING_PKGS="${MISSING_PKGS} ${PKG}"
    fi
done

if [ -n "${MISSING_PKGS}" ]; then
    echo "-> [1/4] Ensuring missing runtimes (${MISSING_PKGS})..."
    if [ "${IS_TERMUX}" = "true" ] && command -v pkg >/dev/null 2>&1; then
        pkg install -y ${MISSING_PKGS} 2>/dev/null || true
    elif command -v apt-get >/dev/null 2>&1; then
        apt-get update -y && apt-get install -y ${MISSING_PKGS} 2>/dev/null || true
    fi
fi

# 4. Standard Python SDK Installation
echo "-> [2/4] Installing termux-bitnet Python SDK..."
if [ -f "pyproject.toml" ]; then
    python -m pip install --no-build-isolation -e .
else
    python -m pip install --upgrade termux-bitnet
fi

# 5. Native Pure-CPU Compute Engine & 1-Click Stream Extraction
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/termux-bitnet-inst.XXXXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT INT TERM HUP

echo "-> [3/4] Provisioning 100% Zero-Compilation Pure-CPU ARM64 Native Engine..."
CANDIDATE_URLS=(
    "https://github.com/${REPO}/releases/latest/download/libtermux_bitnet.so"
    "https://github.com/${REPO}/releases/latest/download/termux-bitnet-android-aarch64.tar.gz"
)
if [ "${VERSION}" != "latest" ]; then
    CANDIDATE_URLS+=(
        "https://github.com/${REPO}/releases/download/v${VERSION}/libtermux_bitnet.so"
        "https://github.com/${REPO}/releases/download/v${VERSION}/termux-bitnet-v${VERSION}-android-aarch64.tar.gz"
    )
fi

PREBUILT_TAR="${TMP_DIR}/termux-bitnet.tar.gz"
STAGING_DIR="${TMP_DIR}/.staging"

mkdir -p "${STAGING_DIR}" "${LIB_DIR}" "${BIN_DIR}"
FETCH_SUCCESS=false
for URL in "${CANDIDATE_URLS[@]}"; do
    if [[ "${URL}" == *.so ]]; then
        if curl -sSL -f --connect-timeout 10 --retry 2 -o "${LIB_DIR}/libtermux_bitnet.so" "${URL}"; then
            chmod 0755 "${LIB_DIR}/libtermux_bitnet.so"
            FETCH_SUCCESS=true
            echo "   -> [OK] Successfully fetched prebuilt native library from: ${URL}"
            break
        fi
    else
        if curl -sSL -f --connect-timeout 10 --retry 2 -o "${PREBUILT_TAR}" "${URL}"; then
            tar -xzf "${PREBUILT_TAR}" -C "${STAGING_DIR}" 2>/dev/null || true
            if [ -f "${STAGING_DIR}/libtermux_bitnet.so" ]; then
                cp "${STAGING_DIR}/libtermux_bitnet.so" "${LIB_DIR}/"
                chmod 0755 "${LIB_DIR}/libtermux_bitnet.so"
                echo "   -> [OK] Deployed pure-CPU C-ABI engine to ${LIB_DIR}/libtermux_bitnet.so"
            fi
            if [ -f "${STAGING_DIR}/termux-bitnet-cli" ]; then
                cp "${STAGING_DIR}/termux-bitnet-cli" "${BIN_DIR}/"
                chmod 0755 "${BIN_DIR}/termux-bitnet-cli"
                ln -sf "${BIN_DIR}/termux-bitnet-cli" "${BIN_DIR}/termux-bitnet-cpu" 2>/dev/null || true
                ln -sf "${BIN_DIR}/termux-bitnet-cli" "${BIN_DIR}/termux-bitnet-cli-cpu" 2>/dev/null || true
                echo "   -> [OK] Deployed native standalone CLI to ${BIN_DIR}/termux-bitnet-cli"
            fi
            rm -rf "${STAGING_DIR}"
            FETCH_SUCCESS=true
            echo "   -> [OK] Successfully extracted prebuilt native bundle from: ${URL}"
            break
        fi
    fi
done

if [ "${FETCH_SUCCESS}" != "true" ]; then
    echo "[ERROR] Failed to fetch verified prebuilt binary bundle from candidate release mirrors."
    exit 1
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
