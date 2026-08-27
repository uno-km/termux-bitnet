"""Automated Installer and Prebuilt Binary Dispatcher for termux-bitnet."""

import os
import sys
import shutil
import urllib.request
from pathlib import Path

PREBUILT_LIB_URLS = [
    "https://github.com/uno-km/termux-bitnet/releases/download/v1.0.11/libtermux_bitnet-arm64-android.so",
    "https://github.com/uno-km/termux-bitnet/releases/download/v1.0.10/libtermux_bitnet-arm64-android.so",
    "https://github.com/uno-km/termux-bitnet/releases/download/v1.0.9/libtermux_bitnet-arm64-android.so",
    "https://github.com/uno-km/termux-bitnet/releases/download/v1.0.8/libtermux_bitnet-arm64-android.so",
    "https://github.com/uno-km/termux-bitnet/releases/download/v1.0.7/libtermux_bitnet-arm64-android.so",
]


def install_prebuilt_library() -> bool:
    target_dir = Path(__file__).parent
    target_so = target_dir / "libtermux_bitnet.so"

    print("=========================================================")
    print("  termux-bitnet One-Click Engine Provisioning")
    print("=========================================================")
    print(f"  Target: {target_so}")

    for url in PREBUILT_LIB_URLS:
        print(f"[*] Downloading pre-built ARM64 binary from: {url}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "termux-bitnet-installer"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 1024:
                        with open(target_so, "wb") as f:
                            f.write(data)
                        os.chmod(target_so, 0o755)
                        print(f"Successfully provisioned native C++ engine ({len(data)} bytes).")
                        return True
        except Exception as e:
            print(f"[-] Pre-built download skipped: {e}")

    # Fallback to local cmake compilation if tools exist
    print("[*] Attempting local compilation with CMake / Clang...")
    import subprocess
    root_dir = target_dir.parent
    if (root_dir / "CMakeLists.txt").exists():
        build_dir = root_dir / "build"
        build_dir.mkdir(exist_ok=True)
        try:
            subprocess.check_call(["cmake", "-B", str(build_dir), "-DCMAKE_BUILD_TYPE=Release", str(root_dir)])
            subprocess.check_call(["cmake", "--build", str(build_dir), "-j4"])
            built_so = build_dir / "libtermux_bitnet.so"
            if built_so.exists():
                shutil.copy(built_so, target_so)
                os.chmod(target_so, 0o755)
                print("Successfully built native engine locally.")
                return True
        except Exception as e:
            print(f"[-] Local build failed: {e}")

    print("Failed to provision native library. Please ensure clang and cmake are installed.")
    return False


def main():
    success = install_prebuilt_library()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
