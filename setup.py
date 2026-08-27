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
            print(f"[termux-bitnet] Warning: Native CMake build skipped or failed ({e}). Package will run with fallback / runtime compilation mode.")

setup(
    name="termux-bitnet",
    version="1.0.14",
    packages=find_packages(),
    ext_modules=[CMakeExtension("termux_bitnet._libtermux_bitnet")],
    cmdclass={"build_ext": CMakeBuild},
)
