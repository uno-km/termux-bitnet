"""
Unit Test: Zero-Silent-Fallback & Fail-Fast Mandate
Verifies that any Vulkan initialization or execution fault raises an explicit exception.
"""
import pytest
from ameva_runtime.adapters.bitnet_vulkan import BitnetVulkanAdapter, AmevaVulkanExecutionError, BitnetVulkanCtypesEngine


def test_zero_silent_fallback_on_broken_engine():
    """
    If the engine object raises an attribute or configuration exception during Vulkan binding,
    BitnetVulkanAdapter must NOT catch and swallow it, but immediately throw AmevaVulkanExecutionError.
    """
    class ExplodingConfig:
        @property
        def n_gpu_layers(self):
            return 32

        @n_gpu_layers.setter
        def n_gpu_layers(self, val):
            raise RuntimeError("Simulated Hardware Driver Fault")

    class FaultyEngine:
        config = ExplodingConfig()

    class ValidReport:
        device_name = "Mali-G68"
        vendor_id = 0x13b5

    with pytest.raises(AmevaVulkanExecutionError) as exc_info:
        BitnetVulkanAdapter.bind(engine=FaultyEngine(), report=ValidReport())

    assert exc_info.value.step == "AdapterBindEngineConfig"
    assert exc_info.value.code == -8
    assert "Simulated Hardware Driver Fault" in str(exc_info.value)


def test_ctypes_engine_fails_fast_on_missing_library():
    """
    If libameva_vulkan_bitnet.so is not found, BitnetVulkanCtypesEngine must fail immediately.
    """
    with pytest.raises(AmevaVulkanExecutionError) as exc_info:
        BitnetVulkanCtypesEngine(lib_path="/nonexistent/path/to/libvulkan_fake.so")

    assert exc_info.value.step == "NativeLibraryLoad"
    assert exc_info.value.code == -3
