"""Hardware inspection and acceleration feature detection for ARM64 / Termux."""

import os
import platform
import subprocess
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple



@dataclass
class HardwareProfile:
    arch: str
    is_termux: bool
    is_proot: bool
    has_neon: bool
    has_dotprod: bool
    has_fp16: bool
    cpu_cores: int
    soc_name: str
    recommended_threads: int


# [B방안] Platform SSOT: ameva-runtime.platform 에서 공유 구현을 가져옵니다.
try:
    from ameva_runtime.vulkan.platform import (
        is_termux as _ameva_is_termux,
        is_proot as _ameva_is_proot,
    )
    _AMEVA_PLATFORM_AVAILABLE = True
except ImportError:
    _AMEVA_PLATFORM_AVAILABLE = False


def is_termux() -> bool:
    """Check whether running in Termux."""
    if _AMEVA_PLATFORM_AVAILABLE:
        return _ameva_is_termux()
    return "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")


def is_proot() -> bool:
    """Check whether running in PRoot."""
    if _AMEVA_PLATFORM_AVAILABLE:
        return _ameva_is_proot()
    return "PROOT_TMP_DIR" in os.environ or os.path.exists("/proc/sys/fs/binfmt_misc/proot")


def detect_hardware() -> HardwareProfile:
    """Inspect local hardware environment and return optimal inference configuration.

    [B방안] ameva-runtime.platform 에서 플랫폼 감지를 통합 위임합니다.
    """
    arch = platform.machine().lower()
    _is_termux_env = is_termux()
    _is_proot_env = is_proot()

    has_neon = False
    has_dotprod = False
    has_fp16 = False
    soc_name = "Unknown SoC"
    cpu_cores = os.cpu_count() or 4

    # Probe /proc/cpuinfo if available (Linux/Android/PRoot)
    if os.path.exists("/proc/cpuinfo"):
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()

                # SIMD flags
                if "asimd" in content or "neon" in content:
                    has_neon = True
                if "asimddp" in content or "dotprod" in content:
                    has_dotprod = True
                if "fphp" in content or "fp16" in content:
                    has_fp16 = True

                # Hardware SoC identification
                if "exynos" in content or "s5e" in content:
                    soc_name = "Samsung Exynos (ARMv8.2-A+)"
                elif "qualcomm" in content or "qcom" in content or "sm" in content:
                    soc_name = "Qualcomm Snapdragon (Kyro/Adreno)"
                elif "mediatek" in content or "mt" in content:
                    soc_name = "MediaTek Dimensity"
                elif "tensor" in content:
                    soc_name = "Google Tensor"
                elif "cortex" in content:
                    soc_name = "ARM Cortex Core"
        except Exception as e:
            import logging
            logging.getLogger("termux_bitnet.hardware").warning(
                "[termux-bitnet] /proc/cpuinfo 파싱 실패 — SoC/SIMD 감지 건너뜀: %s", e
            )

    # Recommendation heuristic: On 8-core mobile Big.LITTLE (4 Big + 4 Little), 4 big cores prevent thermal throttling
    if _is_termux_env and cpu_cores >= 8:
        recommended_threads = 4
    else:
        recommended_threads = min(cpu_cores, 4) if cpu_cores >= 4 else cpu_cores

    return HardwareProfile(
        arch=arch,
        is_termux=_is_termux_env,
        is_proot=is_proot,
        has_neon=has_neon,
        has_dotprod=has_dotprod,
        has_fp16=has_fp16,
        cpu_cores=cpu_cores,
        soc_name=soc_name,
        recommended_threads=recommended_threads,
    )


def print_hardware_summary() -> None:
    """Print formatted hardware summary to console."""
    profile = detect_hardware()
    print("=========================================================")
    print("           termux-bitnet Hardware Diagnostic             ")
    print("=========================================================")
    print(f"  Architecture:         {profile.arch}")
    print(f"  SoC Family:           {profile.soc_name}")
    print(f"  CPU Cores:            {profile.cpu_cores} cores")
    print(f"  Termux Native:        {'YES' if profile.is_termux else 'NO'}")
    print(f"  PRoot Virtualized:    {'YES' if profile.is_proot else 'NO'}")
    print(f"  ARM NEON SIMD:        {'SUPPORTED' if profile.has_neon else 'UNAVAILABLE'}")
    print(f"  ARM DotProd Accel:    {'ACTIVE (vdotq_s32)' if profile.has_dotprod else 'FALLBACK (FMA)'}")
    print(f"  Recommended Threads:  {profile.recommended_threads} threads")
    print("=========================================================")


def _resolve_ameva_runtime() -> Optional[Any]:
    """Check for ameva_runtime availability without top-level static dependency.

    Returns the ameva_runtime module if installed, otherwise None.
    """
    try:
        import importlib.util
        spec = importlib.util.find_spec("ameva_runtime")
        if spec is not None:
            import ameva_runtime
            return ameva_runtime
    except (ImportError, AttributeError):
        pass
    return None


def resolve_device_backend(requested_device: str, requested_ngl: Optional[int] = None) -> Tuple[str, int]:
    """Resolve the user's device= argument to an actual backend and ngl count.

    Adheres strictly to the AMEVA Decoupled Gateway Protocol:
    1. 'cpu': Always routes to pure CPU NEON without external dependency.
    2. 'auto': If ameva-runtime is absent, safely defaults to CPU NEON with explicit INFO log.
               If ameva-runtime is present, queries SmartRouter / BitnetAdapter for optimal device routing.
    3. 'vulkan' / 'gpu': Requires ameva-runtime. Emits Fail-Fast error [AMEVA-BITNET-E001] if absent.
    """
    import sys
    from termux_bitnet.exceptions import PlatformNotSupportedError

    req = str(requested_device or "auto").lower().strip()
    ameva_mod = _resolve_ameva_runtime()
    ngl_target = 33 if requested_ngl is None else requested_ngl

    if req == "cpu":
        return "cpu", 0

    if req == "auto":
        if ameva_mod is None:
            sys.stdout.write("[INFO] ameva-runtime is not installed. Defaulting to ARM64 NEON CPU backend.\n")
            sys.stdout.flush()
            return "cpu", 0

        # ameva_runtime is available: evaluate via SmartRouter / Doctor
        try:
            from ameva_runtime.router import SmartRouter
            plan = SmartRouter().route_for_llm(requested_backend=None)
            backend_norm = "vulkan" if plan.backend in ("vulkan", "gpu") else "cpu"
            ngl_val = (plan.ngl if requested_ngl is None else requested_ngl) if backend_norm == "vulkan" else 0
            return backend_norm, ngl_val
        except Exception:
            # If router evaluation cannot find GPU, default to CPU
            return "cpu", 0

    if req in ("vulkan", "gpu"):
        if ameva_mod is None:
            raise PlatformNotSupportedError(
                "[ERROR: AMEVA-BITNET-E001] GPU acceleration requires 'ameva-runtime'.\n"
                "Cause: Hardware abstraction provider 'ameva-runtime' is not installed.\n"
                "Action Required: Install the hardware acceleration package via:\n"
                "  - Python: pip install ameva-runtime\n"
                "  - Node.js: npm install @unokm/ameva-runtime\n"
                "Documentation: https://uno-km.vercel.app/lib/bitnet/"
            )

        # Check native Vulkan availability via ameva-runtime Doctor probe
        try:
            from ameva_runtime import vulkan as avr
            report = avr.Doctor().run_self_test(verbose=False)
            if not (report.overall_success or report.recommended_backend in ("vulkan", "vulkan_driver_only") or getattr(report, "passed_stages", 0) >= 7):
                raise PlatformNotSupportedError(
                    f"[ERROR: AMEVA-BITNET-E002] Vulkan GPU probe failed on device '{report.device_name}'.\n"
                    f"Cause: {getattr(report, 'failure_reason', 'Vulkan hardware validation did not pass')}.\n"
                    "Action Required: Use CPU inference: termux-bitnet run --device cpu ..."
                )
            return "vulkan", ngl_target
        except Exception as e:
            if isinstance(e, PlatformNotSupportedError):
                raise
            raise PlatformNotSupportedError(
                f"[ERROR: AMEVA-BITNET-E002] Vulkan GPU acceleration failed: {e}\n"
                "Action Required: Use CPU inference: termux-bitnet run --device cpu ..."
            ) from e

    raise ValueError(f"Unknown device: '{requested_device}'. Supported options: 'auto', 'cpu', 'gpu', 'vulkan'.")


def bind_bitnet_hardware(engine: Any, requested_device: str) -> Optional[Any]:
    """Safely invoke AMEVA-Runtime BitnetAdapter if present to configure engine instance."""
    ameva_mod = _resolve_ameva_runtime()
    if ameva_mod is None:
        return None

    try:
        from ameva_runtime.adapters.bitnet import BitnetAdapter
        binding = BitnetAdapter.bind(engine=engine, requested_backend=requested_device)
        return binding
    except Exception as e:
        import logging
        logging.getLogger("termux_bitnet.hardware").debug("Hardware adapter binding skipped: %s", e)
        return None


def doctor() -> Dict[str, Any]:
    """Diagnostic inspection adhering to AMEVA Doctor specification."""
    ameva_mod = _resolve_ameva_runtime()
    if ameva_mod is not None:
        try:
            from ameva_runtime.adapters.bitnet import BitnetAdapter
            adapter = BitnetAdapter()
            rep = adapter.resolve_diagnostic_report()
            return {
                "doctor_report": rep,
                "overall_success": getattr(rep, "overall_success", False),
                "passed_stages": getattr(rep, "passed_stages", 0),
                "recommended_backend": getattr(rep, "recommended_backend", "cpu_neon"),
                "status": "DIAGNOSED_VIA_AMEVA",
            }
        except Exception as e:
            import logging
            logging.getLogger("termux_bitnet.hardware").debug("AMEVA Doctor invocation exception: %s", e)

    profile = detect_hardware()
    return {
        "doctor_report": None,
        "overall_success": True,
        "passed_stages": 7,
        "recommended_backend": "cpu",
        "status": "NATIVE_CPU_ONLY",
        "arch": profile.arch,
        "has_neon": profile.has_neon,
        "has_dotprod": profile.has_dotprod,
    }

