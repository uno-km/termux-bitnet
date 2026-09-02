"""
termux_bitnet.control.status — BitNet 상태 파일 Writer + Heartbeat

1.58-bit ARM64 추론 특화 동작:
  - notify_job_start() → Inference 시작
  - notify_job_end()   → Inference 완료
  - notify_error()     → SO 로드 실패, ARM64 DotProd 미지원 등 기록
"""
from __future__ import annotations
from typing import Any
from ameva_component.heartbeat import HeartbeatWriter


class BitNetStatusWriter(HeartbeatWriter):
    """BitNetControl 상태를 10초마다 상태 파일에 원자적으로 기록합니다."""

    def __init__(self, control: Any) -> None:
        super().__init__(control, name="bitnet")
