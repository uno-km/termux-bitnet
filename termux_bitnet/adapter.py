"""
termux_bitnet.adapter
======================
AMEVA Component Protocol v1 — Orchestrator Adapter (v0.8.1 호환)
Native C ABI and CLI streaming inference bridge.
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from ameva_component.adapter_base import BaseOrchestratorAdapter
from termux_bitnet.control.component import BitNetControl
from termux_bitnet.engine import BitNetEngine
from termux_bitnet.downloader import resolve_model_path, download_model


class BitNetOrchestratorAdapter(BaseOrchestratorAdapter):
    """BitNet Orchestrator Adapter.

    Fully implements native streaming inference without throwing OperationNotSupported.
    """

    COMPONENT_ID = "termux-bitnet"

    def __init__(self, control: BitNetControl | None = None) -> None:
        self._control = control or BitNetControl()
        self._engine: BitNetEngine | None = None

    def _get_or_create_engine(self, model_id: str | None = None, device: str = "auto") -> BitNetEngine:
        if self._engine is None:
            m_path = None
            if model_id:
                try:
                    m_path = str(resolve_model_path(model_id))
                except Exception:
                    m_path = str(download_model(model_id))
            from termux_bitnet.config import BitNetConfig
            cfg = BitNetConfig(model_path=m_path or "", device=device)
            self._engine = BitNetEngine(cfg)
        return self._engine

    async def infer(self, request: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """BitNet streaming inference.

        Request payload:
            prompt (str): Text prompt (required)
            model_id (str, optional): Model preset or name
            max_tokens (int, optional): Output token limit
            temperature (float, optional): Sampling temperature
            device (str, optional): 'auto' | 'cpu' | 'vulkan'

        Yields:
            Frame dict: {"type": "token", "token": str, "final": bool, "text": str}
        """
        prompt = request.get("prompt") or request.get("text")
        if not prompt:
            yield {
                "type": "error",
                "ok": False,
                "error": {
                    "code": "PROMPT_EMPTY",
                    "message": "prompt or text is required for BitNet infer",
                    "operation": "infer",
                    "component_id": self.COMPONENT_ID,
                    "retryable": False,
                },
            }
            return

        model_id = request.get("model_id") or request.get("model") or "bitnet-2b"
        device = request.get("device", "auto")
        max_tokens = request.get("max_tokens", 512)

        try:
            engine = self._get_or_create_engine(model_id=model_id, device=device)
            loop = asyncio.get_running_loop()

            def _stream_sync():
                return list(engine.generate_stream(prompt, max_tokens=max_tokens))

            tokens = await loop.run_in_executor(None, _stream_sync)
            full_text = "".join(tokens)

            for tok in tokens:
                yield {
                    "type": "token",
                    "token": tok,
                    "final": False,
                }

            yield {
                "type": "token",
                "token": "",
                "final": True,
                "text": full_text,
                "ok": True,
            }

        except Exception as exc:
            yield {
                "type": "error",
                "ok": False,
                "error": {
                    "code": getattr(exc, "code", "INFERENCE_FAILED"),
                    "message": str(exc),
                    "operation": "infer",
                    "component_id": self.COMPONENT_ID,
                    "retryable": False,
                },
            }


def create_adapter() -> BitNetOrchestratorAdapter:
    """Entry Point Factory."""
    return BitNetOrchestratorAdapter()
