"""
AMEVA Unified Exception Hierarchy for Termux AI Engines.
Component: [BITNET]
"""
from typing import Optional, Any


class AmevaTermuxError(RuntimeError):
    """Root exception for all Termux On-Device AI Engines."""
    COMPONENT_TAG = "[BITNET]"
    DEFAULT_CODE = "E000_UNKNOWN"

    def __init__(self, message: str = "", code: Optional[Any] = None, details: Optional[Any] = None):
        self.code = code or self.DEFAULT_CODE
        self.details = details
        self.raw_message = message
        super().__init__(message if message.startswith("[BITNET]") or message.startswith("[termux-bitnet]") else f"{self.COMPONENT_TAG} [{self.code}] {message}")


TermuxBitNetError = AmevaTermuxError
BitNetError = AmevaTermuxError


class PlatformNotSupportedError(AmevaTermuxError):
    DEFAULT_CODE = "E002_PLATFORM_NOT_SUPPORTED"


class HardwareCompatibilityError(AmevaTermuxError):
    DEFAULT_CODE = "E003_HARDWARE_INCOMPATIBLE"


class RuntimeNotFoundError(AmevaTermuxError):
    DEFAULT_CODE = "E004_RUNTIME_NOT_FOUND"


class BitNetEngineNotFound(RuntimeNotFoundError):
    pass


class ProvisioningError(AmevaTermuxError):
    DEFAULT_CODE = "E005_PROVISIONING_FAILED"


class InferenceTimeoutError(AmevaTermuxError):
    DEFAULT_CODE = "E006_INFERENCE_TIMEOUT"


class InferenceExecutionError(AmevaTermuxError):
    DEFAULT_CODE = "E007_INFERENCE_FAILED"


class ModelCorruptedError(AmevaTermuxError):
    DEFAULT_CODE = "E008_MODEL_CORRUPTED"


class ModelNotFoundError(AmevaTermuxError):
    DEFAULT_CODE = "E001_MODEL_NOT_FOUND"


class ModelDownloadError(ProvisioningError):
    DEFAULT_CODE = "E009_MODEL_DOWNLOAD_FAILED"


class ClusterConnectionError(AmevaTermuxError):
    """Raised when one or more distributed RPC worker nodes cannot be reached or fail handshake."""
    DEFAULT_CODE = "E010_CLUSTER_CONNECTION"


class ClusterConfigurationError(AmevaTermuxError):
    """Raised when cluster parameters (tensor split, backend, vram budget) are invalid."""
    DEFAULT_CODE = "E011_CLUSTER_CONFIG"


class ClusterLicenseRequiredError(AmevaTermuxError):
    """Raised when distributed clustering is invoked without required AMEVA Cluster license."""
    DEFAULT_CODE = "E403_CLUSTER_LICENSE_REQUIRED"

    def __init__(self, message: str = ""):
        if not message:
            message = (
                "\n================================================================================\n"
                "[AMEVA-CLUSTER] CLUSTER LICENSE REQUIRED (E403)\n"
                "================================================================================\n"
                "Multi-device distributed clustering is an exclusive capability of 'ameva-cluster'.\n"
                "Standalone distributed execution without the official AMEVA-Cluster package is prohibited.\n\n"
                "Resolution:\n"
                "  1. Install official AMEVA-Cluster runtime:\n"
                "     pip install ameva-cluster  (or npm install @ameva/cluster)\n"
                "  2. Launch worker/master through 'ameva-cluster' control plane:\n"
                "     ameva-cluster worker\n"
                "     ameva-cluster master -m model.gguf\n"
                "================================================================================"
            )
        super().__init__(message)
