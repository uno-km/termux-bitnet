import os
import sys
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

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        try:
            subprocess.check_call(["cmake", ext.sourcedir] + cmake_args, cwd=self.build_temp)
            subprocess.check_call(["cmake", "--build", "."] + build_args, cwd=self.build_temp)
        except Exception as e:
            # Check if a prebuilt binary already exists in the package before failing
            prebuilt_candidates = [
                os.path.join(extdir, "libtermux_bitnet.so"),
                os.path.join(extdir, "_libtermux_bitnet.so"),
                os.path.join(extdir, "libtermux_bitnet.dll"),
                os.path.join(os.path.dirname(__file__), "termux_bitnet", "libtermux_bitnet.so"),
                os.path.join(os.path.dirname(__file__), "libtermux_bitnet.so"),
            ]
            has_prebuilt = any(os.path.exists(p) for p in prebuilt_candidates)

            if has_prebuilt and os.environ.get("TERMUX_BITNET_ALLOW_PREBUILT", "1") == "1":
                sys.stderr.write(
                    f"[termux-bitnet] Warning: CMake native build failed ({e}), "
                    "but an existing verified prebuilt library was detected. Proceeding with prebuilt binary.\n"
                )
            else:
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

setup(
    name="termux-bitnet",
    version="1.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "ameva-vulkan-runtime>=1.0.0",
    ],
    ext_modules=[CMakeExtension("termux_bitnet._libtermux_bitnet")],
    cmdclass={"build_ext": CMakeBuild},
)
