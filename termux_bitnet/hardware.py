"""Hardware inspection and acceleration feature detection for ARM64 / Termux."""

import os
import platform
import subprocess
from dataclasses import dataclass
from typing import Dict, Any


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


def detect_hardware() -> HardwareProfile:
    """Inspect local hardware environment and return optimal inference configuration.

    [버그 수정] 기존 코드에서 `is_termux` 라는 지역 bool 변수가 같은 모듈 내
    `is_termux()` 함수(미래에 추가될 수 있는)와 이름 충돌(shadowing)을 일으킬 수 있었습니다.
    지역 변수명을 `_is_termux_env` 로 변경하였습니다. HardwareProfile API 는 불변입니다.
    """
    arch = platform.machine().lower()
    _is_termux_env = "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")
    is_proot = "PROOT_TMP_DIR" in os.environ or os.path.exists("/proc/sys/fs/binfmt_misc/proot")

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
