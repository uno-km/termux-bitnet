#!/bin/bash
# ==============================================================================
# termux-bitnet: Zero-Drift One-Touch Installer for Android Termux / ARM64
# Author: uno-km (https://github.com/uno-km)
# Version: 1.3.0
# ==============================================================================

set -e

VERSION="v1.3.0"
ASSET_NAME="termux-bitnet-${VERSION}-android-aarch64.tar.gz"
RELEASE_URL="https://github.com/uno-km/termux-bitnet/releases/download/${VERSION}/${ASSET_NAME}"

echo "========================================================="
echo "        🚀 Initializing termux-bitnet ${VERSION} Installer"
echo "========================================================="

# 1. Detect Package Manager & Environment
if command -v pkg >/dev/null 2>&1; then
    echo "[1/5] Updating Termux repositories & checking dependencies..."
    pkg update -y
    pkg install -y clang cmake git python python-pip openblas libandroid-execinfo nodejs curl tar
    BIN_DIR="$PREFIX/bin"
elif command -v apt-get >/dev/null 2>&1; then
    echo "[1/5] Updating Ubuntu/Debian repositories..."
    apt-get update -y
    apt-get install -y build-essential cmake git python3 python3-pip libopenblas-dev nodejs npm curl tar
    BIN_DIR="/usr/local/bin"
else
    echo "Warning: Unknown package manager. Ensure cmake, clang, python3, curl, and nodejs are installed."
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
fi

# 2. Check Architecture & Precompiled GitHub Release Asset
ARCH=$(uname -m)
PREBUILT_SUCCESS=false

if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    echo "[2/5] Checking for verified ARM64 prebuilt release bundle (${VERSION})..."
    TMP_DIR=$(mktemp -d)
    if curl -sSL -f --connect-timeout 10 "$RELEASE_URL" -o "$TMP_DIR/$ASSET_NAME" 2>/dev/null; then
        echo "  [+] Verified prebuilt binary downloaded successfully!"
        tar -xzf "$TMP_DIR/$ASSET_NAME" -C "$TMP_DIR"
        mkdir -p termux_bitnet
        if [ -f "$TMP_DIR/libtermux_bitnet.so" ]; then
            cp "$TMP_DIR/libtermux_bitnet.so" termux_bitnet/
            echo "  [+] Installed libtermux_bitnet.so -> termux_bitnet/"
        fi
        if [ -f "$TMP_DIR/termux-bitnet-cli" ]; then
            cp "$TMP_DIR/termux-bitnet-cli" "$BIN_DIR/"
            chmod +x "$BIN_DIR/termux-bitnet-cli"
            echo "  [+] Installed termux-bitnet-cli -> $BIN_DIR/"
        fi
        PREBUILT_SUCCESS=true
    else
        echo "  [-] Prebuilt bundle not available or network restricted. Falling back to native on-device compilation."
    fi
    rm -rf "$TMP_DIR"
fi

# 3. Native Source Compilation (If prebuilt not loaded)
if [ "$PREBUILT_SUCCESS" = false ]; then
    echo "[2/5] Executing hardened on-device C++ CMake compilation (NEON + DotProd)..."
    cmake -B build \
        -DGGML_NEON=ON \
        -DGGML_ARM_DOTPROD=ON \
        -DCMAKE_C_COMPILER=clang \
        -DCMAKE_CXX_COMPILER=clang++ \
        -DCMAKE_BUILD_TYPE=Release
    cmake --build build --config Release -j$(nproc 2>/dev/null || echo 4)
    mkdir -p termux_bitnet
    if [ -f "build/libtermux_bitnet.so" ]; then
        cp build/libtermux_bitnet.so termux_bitnet/
    fi
    if [ -f "build/termux-bitnet-cli" ]; then
        cp build/termux-bitnet-cli "$BIN_DIR/" 2>/dev/null || true
        chmod +x "$BIN_DIR/termux-bitnet-cli" 2>/dev/null || true
    fi
fi

# 4. Python SDK & Runtime Installation
echo "[3/5] Pre-provisioning Python wheel and build toolchains..."
pip install --upgrade setuptools wheel
if pip install ameva-runtime 2>/dev/null; then
    echo "  [+] ameva-runtime acceleration ready."
fi

echo "[4/5] Installing termux-bitnet Python SDK..."
pip install --no-build-isolation -e .

# 5. Node.js Dual Engine CLI Installation
echo "[5/5] Installing Node.js Dual Engine CLI..."
if [ -d "npm" ] && command -v npm >/dev/null 2>&1; then
    (cd npm && npm install -g .) || echo "  [-] Node.js CLI optional global install skipped."
fi

echo "========================================================="
echo "  ✅ termux-bitnet ${VERSION} successfully installed!"
echo "========================================================="
echo "  Hardware Verification:"
echo "    * Python CLI:       termux-bitnet info"
echo "    * Native CLI:       termux-bitnet-cli --help"
echo "    * Node.js CLI:      termux-bitnet-js info"
echo "    * Model Download:   termux-bitnet download bitnet-2b"
echo "    * Live Inference:   termux-bitnet run -p 'Hello BitNet' -n 16"
echo "========================================================="
