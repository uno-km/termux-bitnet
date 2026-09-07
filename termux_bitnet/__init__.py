"""termux-bitnet: High-performance 1.58-bit BitNet Inference SDK for Android Termux & ARM64."""

from termux_bitnet.config import BitNetConfig, GenerationMetrics
from termux_bitnet.engine import BitNetEngine
from termux_bitnet.hardware import (
    detect_hardware,
    print_hardware_summary,
    resolve_device_backend,
    bind_bitnet_hardware,
    doctor,
)
from termux_bitnet.downloader import download_model, AVAILABLE_MODELS
from termux_bitnet.exceptions import PlatformNotSupportedError, BitNetEngineNotFound

__version__ = "1.4.0"
__author__ = "uno-km"

__all__ = [
    "BitNetConfig",
    "GenerationMetrics",
    "BitNetEngine",
    "detect_hardware",
    "print_hardware_summary",
    "resolve_device_backend",
    "bind_bitnet_hardware",
    "doctor",
    "download_model",
    "AVAILABLE_MODELS",
    "PlatformNotSupportedError",
    "BitNetEngineNotFound",
]
