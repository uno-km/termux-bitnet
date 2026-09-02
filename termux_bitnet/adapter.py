"""termux_bitnet.adapter — Orchestrator Adapter."""
from __future__ import annotations
from termux_bitnet.control.component import BitNetControl

class BitNetOrchestratorAdapter:
    def __init__(self, control: BitNetControl | None = None) -> None:
        self._control = control or BitNetControl()
    def info(self) -> dict: return self._control.component_info()
    def health(self) -> dict: return self._control.doctor_lite()
    def models(self) -> dict: return self._control.list_models()
    def instances(self) -> dict: return self._control.list_instances()
    async def activate(self, req: dict) -> dict: return await self._control.activate_model(req)
    async def deactivate(self, req: dict) -> dict: return await self._control.deactivate_model(req)
