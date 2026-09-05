"""termux-bitnet: High-performance 1.58-bit BitNet Inference SDK for Android Termux & ARM64."""

from termux_bitnet.config import BitNetConfig, GenerationMetrics
from termux_bitnet.engine import BitNetEngine
from termux_bitnet.hardware import detect_hardware, print_hardware_summary
from termux_bitnet.downloader import download_model, AVAILABLE_MODELS

__version__ = "1.1.4"
__author__ = "uno-km"

__all__ = [
    "BitNetConfig",
    "GenerationMetrics",
    "BitNetEngine",
    "detect_hardware",
    "print_hardware_summary",
    "download_model",
    "AVAILABLE_MODELS",
]
