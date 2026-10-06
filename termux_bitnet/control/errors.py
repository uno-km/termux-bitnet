"""
termux_bitnet.control.errors
termux-bitnet 전용 오류 계층

BitNet 고유 오류는 AmevaError를 상속합니다.
측정 실패를 정상으로 위장하지 않습니다.
"""
from __future__ import annotations

from ameva_component.exceptions import AmevaError


class BitNetEngineError(AmevaError):
    """BitNet 네이티브 엔진(SO/CLI 바이너리) 관련 오류."""
    code = "BITNET_ENGINE_ERROR"
    exit_code = 3

    def __init__(self, reason: str) -> None:
        super().__init__(f"BitNet engine error: {reason}", details={"reason": reason})
        self.reason = reason


class BitNetBinaryNotFound(AmevaError):
    """libtermux_bitnet.so 또는 llama-cli 바이너리를 찾을 수 없을 때."""
    code = "BITNET_BINARY_NOT_FOUND"
    exit_code = 69  # 외부 서비스 이용 불가

    def __init__(self) -> None:
        super().__init__(
            "BitNet engine binary (libtermux_bitnet.so / llama-cli) not found. "
            "Run 'termux-bitnet install' to build the native engine.",
        )


class BitNetModelNotGGUF(AmevaError):
    """다운로드된 파일이 유효한 GGUF 헤더를 가지지 않을 때."""
    code = "BITNET_MODEL_NOT_GGUF"
    exit_code = 65

    def __init__(self, path: str) -> None:
        super().__init__(
            f"File '{path}' does not have a valid GGUF magic header.",
            details={"path": path},
        )
        self.path = path


class BitNetSIMDUnavailable(AmevaError):
    """ARM DotProd/NEON SIMD 가속이 사용 불가할 때 (degraded 운영 경고)."""
    code = "BITNET_SIMD_UNAVAILABLE"
    exit_code = 2  # DEGRADED

    def __init__(self, arch: str) -> None:
        super().__init__(
            f"ARM64 SIMD acceleration (DotProd/NEON) is unavailable on arch '{arch}'. "
            "Performance will be significantly degraded.",
            details={"arch": arch},
        )
        self.arch = arch
