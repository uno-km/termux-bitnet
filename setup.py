from setuptools import setup, find_packages

setup(
    name="termux-bitnet",
    version="2.0.1",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "ameva-runtime>=2.0.0",
        "ameva-component-sdk>=0.1.0,<2.0",
    ],
    entry_points={
        "console_scripts": [
            "termux-bitnet = termux_bitnet.cli:main",
        ],
        "ameva.components": [
            "termux-bitnet = termux_bitnet.adapter:create_adapter",
        ],
    },
)
