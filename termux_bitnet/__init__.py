"""termux-bitnet: High-performance 1.58-bit BitNet Inference SDK for Android Termux & ARM64."""

from termux_bitnet.config import BitNetConfig, GenerationMetrics
from termux_bitnet.engine import BitNetEngine
from termux_bitnet.hardware import (
    detect_hardware,
    print_hardware_summary,
    resolve_device_backend,
    resolve_device,
    HardwareProfile,
    bind_bitnet_hardware,
    doctor,
)
from termux_bitnet.downloader import download_model, list_models, resolve_model_path, AVAILABLE_MODELS
from termux_bitnet.exceptions import AmevaTermuxError, PlatformNotSupportedError, BitNetEngineNotFound

__version__ = "1.4.1"
__author__ = "uno-km"

__all__ = [
    "BitNetConfig",
    "GenerationMetrics",
    "BitNetEngine",
    "detect_hardware",
    "print_hardware_summary",
    "resolve_device_backend",
    "resolve_device",
    "HardwareProfile",
    "bind_bitnet_hardware",
    "doctor",
    "download_model",
    "list_models",
    "resolve_model_path",
    "AVAILABLE_MODELS",
    "AmevaTermuxError",
    "PlatformNotSupportedError",
    "BitNetEngineNotFound",
]



# Standard Unified Engine Factory
def load(model: str = "bitnet-2b", device: str = "auto", threads: int | None = None, **kwargs) -> BitNetEngine:
    """Standard Unified Engine Factory for termux-bitnet."""
    from termux_bitnet.config import BitNetConfig
    from termux_bitnet.downloader import resolve_model_path
    m_path = ""
    try:
        m_path = str(resolve_model_path(model))
    except Exception:
        pass
    cfg = BitNetConfig(model_path=m_path, device=device, n_threads=threads or 4, **kwargs)
    return BitNetEngine(cfg)
