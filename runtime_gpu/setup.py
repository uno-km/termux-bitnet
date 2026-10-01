import os
from setuptools import setup, find_packages

setup(
    name="ameva-runtime-bitnet",
    version="1.0.0",
    description="Native Vulkan Compute GPU Acceleration for BitNet 1.58-bit Ternary Models (Mali & Adreno)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Eunho Kim",
    author_email="contact@uno-km.com",
    url="https://github.com/uno-km/termux-bitnet",
    package_dir={"": "python"},
    packages=find_packages(where="python", exclude=["tests*", "*tests*"]),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Android",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
