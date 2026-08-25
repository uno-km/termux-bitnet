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
    pkg install -y clang cmake git python python-pip openblas libandroid-execinfo
elif command -v apt-get >/dev/null 2>&1; then
    echo "[1/5] Updating Ubuntu/Debian repositories..."
    apt-get update -y
    echo "[2/5] Installing build tools..."
    apt-get install -y build-essential cmake git python3 python3-pip libopenblas-dev
else
    echo "Warning: Unknown package manager. Ensure cmake, clang, and python3 are installed."
fi

# 2. Hardware Inspection for Optimal SIMD Flags
echo "[3/5] Inspecting CPU acceleration capabilities..."
CMAKE_EXTRA_FLAGS="-DGGML_NEON=ON"

if grep -q -E "asimddp|dotprod" /proc/cpuinfo 2>/dev/null; then
    echo "  -> Found ARMv8.2-A Dot Product Accelerator (__ARM_FEATURE_DOTPROD)!"
    CMAKE_EXTRA_FLAGS="-DGGML_NEON=ON -DGGML_ARM_DOTPROD=ON"
else
    echo "  -> DotProd not detected. Enabling NEON + FMA Fallback."
fi

# 3. Native Engine Build
echo "[4/5] Compiling native C++ 1.58-bit BitNet Core..."
rm -rf build
mkdir -p build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release $CMAKE_EXTRA_FLAGS
make -j$(nproc 2>/dev/null || echo 4)
cd ..

# 4. Python SDK Package Installation
echo "[5/5] Installing termux-bitnet Python SDK & CLI..."
pip install -e .

echo "========================================================="
echo "  ✅ termux-bitnet successfully installed!"
echo "========================================================="
echo "  Quick Start:"
echo "    1. Check Hardware:  termux-bitnet info"
echo "    2. Download Model:  termux-bitnet download bitnet-2b"
echo "    3. Start Chat:      termux-bitnet chat"
echo "    4. Run API Server:  termux-bitnet serve --port 8080"
echo "========================================================="
