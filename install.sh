#!/bin/bash
# ==============================================================================
# termux-bitnet: Zero-Drift One-Touch Installer for Android Termux / PRoot
# Author: uno-km (https://github.com/uno-km)
# ==============================================================================

set -e

echo "========================================================="
echo "        🚀 Initializing termux-bitnet Installer         "
echo "========================================================="

# 1. Detect Package Manager & Environment
if command -v pkg >/dev/null 2>&1; then
    echo "[1/5] Updating Termux repositories..."
    pkg update -y
    echo "[2/5] Installing core build dependencies..."
    pkg install -y clang cmake git python python-pip openblas libandroid-execinfo nodejs
elif command -v apt-get >/dev/null 2>&1; then
    echo "[1/5] Updating Ubuntu/Debian repositories..."
    apt-get update -y
    echo "[2/5] Installing build tools..."
    apt-get install -y build-essential cmake git python3 python3-pip libopenblas-dev nodejs npm
else
    echo "Warning: Unknown package manager. Ensure cmake, clang, python3, and nodejs are installed."
fi

# 2. Python Toolchain Pre-provisioning (Avoid PyPI build isolation & cmake source build bottleneck)
echo "[3/5] Pre-provisioning Python wheel and build toolchains..."
pip install --upgrade setuptools wheel

# 3. Python SDK & Native Core Fast Build (Bypass isolated build environment)
echo "[4/5] Building & Installing termux-bitnet Python SDK & Native C++ Core..."
pip install --no-build-isolation -e .

# 4. Node.js Dual Engine CLI Installation (Zero Conflict with Python CLI)
echo "[5/5] Installing Node.js Dual Engine CLI..."
if [ -d "npm" ] && command -v npm >/dev/null 2>&1; then
    (cd npm && npm install -g . || true)
fi

echo "========================================================="
echo "  ✅ termux-bitnet successfully installed!"
echo "========================================================="
echo "  Dual Engine Verification:"
echo "    * Python CLI:   termux-bitnet info"
echo "    * Node.js CLI:  termux-bitnet-js info"
echo "    * Download:     termux-bitnet download bitnet-2b"
echo "    * Quick Chat:   termux-bitnet chat"
echo "========================================================="
