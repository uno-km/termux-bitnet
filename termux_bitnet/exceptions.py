"""Exceptions for termux-bitnet framework."""

class BitNetError(RuntimeError):
    """Base exception for all termux-bitnet errors, inheriting from RuntimeError for backward compatibility."""
    pass

class BitNetEngineNotFound(BitNetError):
    """Raised when the native BitNet shared library or executable is not found."""
    pass

class RuntimeNotFoundError(BitNetEngineNotFound):
    """Raised when runtime resolver fails to locate verified native binaries."""
    pass

class PlatformNotSupportedError(BitNetError):
    """Raised when running on an unsupported platform or missing hardware abstraction provider."""
    pass

