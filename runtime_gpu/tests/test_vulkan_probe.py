"""
Test Vulkan Probe & Hardware Detection
Validates detection of ARM Mali / Qualcomm Adreno and adapter binding logic.
"""
import pytest
from ameva_runtime.adapters.bitnet_vulkan import BitnetVulkanAdapter, AmevaVulkanExecutionError


def test_adapter_bind_vulkan_defaults():
    class DummyReport:
        device_name = "Mali-G68"
        vendor_id = 0x13b5

    class DummyEngine:
        class Config:
            n_gpu_layers = 0
            flash_attn = False
        config = Config()

    res = BitnetVulkanAdapter.bind(engine=DummyEngine(), report=DummyReport())
    assert res["status"] == "BOUND"
    assert res["is_vulkan"] is True
    assert res["is_mali"] is True
    assert res["is_adreno"] is False
    assert res["mali_128byte_align"] is True
    assert res["n_gpu_layers"] == 32
    assert DummyEngine.config.n_gpu_layers == 32
    assert DummyEngine.config.flash_attn is True


def test_adapter_bind_adreno():
    class DummyReport:
        device_name = "Adreno (TM) 750"
        vendor_id = 0x5143

    res = BitnetVulkanAdapter.bind(report=DummyReport())
    assert res["status"] == "BOUND"
    assert res["is_vulkan"] is True
    assert res["is_adreno"] is True
    assert res["is_mali"] is False


def test_adapter_explicit_cpu_binding():
    res = BitnetVulkanAdapter.bind(requested_backend="cpu")
    assert res["status"] == "BOUND_CPU"
    assert res["is_vulkan"] is False
    assert res["backend"] == "cpu"
