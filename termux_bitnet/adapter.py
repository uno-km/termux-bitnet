"""
termux_bitnet.adapter
======================
AMEVA Component Protocol v1 — Orchestrator Adapter (v0.8.1 호환)
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from ameva_component.adapter_base import BaseOrchestratorAdapter
from ameva_component.exceptions import OperationNotSupported
from termux_bitnet.control.component import BitNetControl


class BitNetOrchestratorAdapter(BaseOrchestratorAdapter):
    """BitNet Orchestrator Adapter.

    BitNet CLI 및 C ABI inference는 내장 HTTP 서버를 통해 수행됩니다.
    infer()는 OPERATION_NOT_SUPPORTED — BitNet 서버 URL을 직접 사용하십시오.
    """

    COMPONENT_ID = "termux-bitnet"

    def __init__(self, control: BitNetControl | None = None) -> None:
        self._control = control or BitNetControl()

    async def infer(self, request: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """BitNet inference는 내장 HTTP 서버(port 8080)를 통해 수행됩니다.
        Orchestrator 직접 streaming은 미지원 — OperationNotSupported를 발생시킵니다.

        P0-2: yield로 오류 객체를 반환하면 상위 소비자가 정상 Frame으로 처리할 수 있어
        raise 방식으로 변경합니다.
        """
        raise OperationNotSupported(operation="infer", component_id=self.COMPONENT_ID)
        # AsyncIterator 타입 시그니처 충족을 위해 도달 불가 yield 유지
        yield  # type: ignore[misc]


def create_adapter() -> BitNetOrchestratorAdapter:
    """Entry Point Factory. 오케스트레이터가 ameva.components 그룹에서 호출합니다."""
    return BitNetOrchestratorAdapter()
