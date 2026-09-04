import os
import sys
import shutil
import subprocess
from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext

class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        super().__init__(name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)

class CMakeBuild(build_ext):
    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        
        # Required for auto-detection & build output
        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            "-DCMAKE_BUILD_TYPE=Release"
        ]

        # Detect ARM architecture & NEON/DotProd support
        if os.path.exists("/proc/cpuinfo"):
            try:
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                    if "asimd" in cpuinfo or "neon" in cpuinfo:
                        cmake_args.append("-DGGML_NEON=ON")
                    if "asimddp" in cpuinfo or "dotprod" in cpuinfo:
                        cmake_args.append("-DGGML_ARM_DOTPROD=ON")
            except Exception:
                pass

        build_args = ["--config", "Release", "--", "-j4"]

        # BLOCKER 3: cmake 미설치 환경(테스트 호스트 등)에서는 Pure-Python 패키지 빌드 허용
        import shutil
        if not shutil.which("cmake") or os.environ.get("TERMUX_BITNET_PURE_PYTHON") == "1":
            sys.stderr.write(
                "\n[termux-bitnet] cmake unavailable or TERMUX_BITNET_PURE_PYTHON=1; "
                "skipping C++ extension build. Pure Python adapter will be installed.\n"
            )
            return

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        # CMake configure and build
        try:
            subprocess.check_call(["cmake", ext.sourcedir] + cmake_args, cwd=self.build_temp)
            subprocess.check_call(["cmake", "--build", "."] + build_args, cwd=self.build_temp)
        except Exception as e:
            if os.environ.get("TERMUX_BITNET_REQUIRE_NATIVE") != "1":
                sys.stderr.write(
                    f"\n[termux-bitnet WARNING] Native C++ compilation failed: {e}. "
                    "Proceeding with Pure Python installation (Native Engine unavailable).\n"
                )
                return
            sys.stderr.write(
                "\n"
                "================================================================================\n"
                "  [termux-bitnet ERROR] Native C++ Core CMake Compilation Failed!\n"
                f"  Error Detail: {e}\n"
                "--------------------------------------------------------------------------------\n"
                "  Required Build Dependencies:\n"
                "    - Android Termux: pkg install -y clang cmake python openblas\n"
                "    - Ubuntu/Debian:  sudo apt install -y build-essential cmake libopenblas-dev\n"
                "    - macOS:          brew install cmake\n"
                "================================================================================\n"
            )
            raise RuntimeError(
                f"[termux-bitnet] Native build failed: {e}. "
                "Ensure cmake and a C++17 compiler (clang/gcc) are installed."
            ) from e

use_native = bool(shutil.which("cmake")) and os.environ.get("TERMUX_BITNET_PURE_PYTHON") != "1"
if not use_native:
    sys.stderr.write(
        "\n[termux-bitnet] cmake unavailable or TERMUX_BITNET_PURE_PYTHON=1; "
        "configuring Pure Python package without native C++ extension.\n"
    )

setup(
    name="termux-bitnet",
    version="1.1.3",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "ameva-vulkan-runtime>=1.0.0",
        "ameva-component-sdk>=0.1.0,<2.0",
    ],
    ext_modules=[CMakeExtension("termux_bitnet._libtermux_bitnet")] if use_native else [],
    cmdclass={"build_ext": CMakeBuild} if use_native else {},
    entry_points={
        "ameva.components": [
            "termux-bitnet = termux_bitnet.adapter:create_adapter",
        ],
    },
)
