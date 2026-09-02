"""
termux_bitnet.control.component
AMEVA Component Protocol v1 — BitNetControl

1.58-bit GGUF 모델 전용 (ARM64 네이티브 SO).
기존 info 서브커맨드 → doctor_lite Adapter.
AVAILABLE_MODELS + ModelRegistry 통합.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from ameva_component import (
    ActivationLock, ComponentInfo, ComponentStateFile,
    ControlMode, InstanceRegistry, InstanceState, InstanceStatus,
    ModelRegistry, ModelState, ModelNotFound, ModelLoadFailed,
    OperationNotSupported, now_timestamps, log_stderr, PROTOCOL_COMPONENT,
)
from ameva_component.control import ComponentControl

# BitNet 공식 모델 목록 (기존 downloader.py AVAILABLE_MODELS 미러)
BITNET_AVAILABLE_MODELS = ["bitnet-2b", "bitnet-large", "bitnet-3b", "bitnet-3b-q4"]


class BitNetControl(ComponentControl):
    """
    termux-bitnet ComponentControl.
    기존 hardware.detect_hardware() + engine.BitNetEngine Adapter.
    """

    COMPONENT_ID   = "termux-bitnet"
    COMPONENT_TYPE = "llm"
    CAPABILITIES   = ("llm.chat", "llm.completion")

    DEFAULT_MODELS_DIR = Path.home() / ".termux-bitnet" / "models"

    def __init__(self, models_dir: Path | None = None) -> None:
        self._models_dir = models_dir or self.DEFAULT_MODELS_DIR
        self._state_file = ComponentStateFile(self.COMPONENT_ID)
        self._model_reg  = ModelRegistry(self.COMPONENT_ID)
        self._inst_reg   = InstanceRegistry(self.COMPONENT_ID)
        self._act_lock   = ActivationLock()

    def _get_version(self) -> str:
        try:
            from termux_bitnet import __version__; return __version__
        except Exception: return "1.1.2"

    def component_info(self) -> dict:
        info = ComponentInfo(
            protocol=PROTOCOL_COMPONENT, component_id=self.COMPONENT_ID,
            component_type=self.COMPONENT_TYPE, version=self._get_version(),
            capabilities=self.CAPABILITIES,
        )
        info.validate()
        return info.to_dict()

    def doctor_lite(self) -> dict:
        """
        기존 info 서브커맨드 + hardware.detect_hardware() Adapter.
        새로운 추론 실행 금지.
        """
        ts = now_timestamps()
        state_data = self._state_file.read()
        stale = self._state_file.is_stale(threshold_ms=30_000)
        pid, pid_alive = self._check_pid()
        instances = self._inst_reg.list_all()
        hot = [i for i in instances if i.state == InstanceState.HOT]

        hw_info = self._check_hardware()
        engine_ok = self._check_engine_binary()
        ready = engine_ok
        degraded = stale or not pid_alive

        return {
            "protocol": "ameva-component-status/1",
            "component_id": self.COMPONENT_ID, "component_type": self.COMPONENT_TYPE,
            "version": self._get_version(), "ready": ready, "degraded": degraded,
            **ts,
            "process": {"running": pid_alive, "pid": pid},
            "capabilities": list(self.CAPABILITIES),
            "active_models": [i.model_id for i in hot],
            "hardware": hw_info,
            "engine": {"present": engine_ok},
            "instances": [{"instance_id": i.instance_id, "model_id": i.model_id,
                           "state": i.state.value, "active_jobs": i.active_jobs} for i in instances],
            "errors": [state_data.get("last_error")] if state_data and state_data.get("last_error") else [],
            "state_file": {"path": str(self._state_file.path), "stale": stale,
                           "updated_at": state_data.get("updated_at") if state_data else None},
        }

    def _check_pid(self) -> tuple[int | None, bool]:
        pid_file = Path.home() / ".local" / "run" / "termux-bitnet.pid"
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, 0)
                return pid, True
            except Exception: pass
        state_data = self._state_file.read()
        if state_data:
            pid = state_data.get("process", {}).get("pid")
            if pid:
                try:
                    os.kill(pid, 0)
                    return pid, True
                except Exception:
                    return pid, False
        return None, False

    def _check_hardware(self) -> dict:
        """ARM64 SIMD/DotProd 지원 여부 — 추론 실행 금지."""
        try:
            from termux_bitnet.hardware import detect_hardware
            hw = detect_hardware()
            return hw.__dict__ if hasattr(hw, "__dict__") else {"info": str(hw)}
        except Exception as e:
            return {"error": str(e)}

    def _check_engine_binary(self) -> bool:
        try:
            from termux_bitnet.engine import BitNetEngine
            return True
        except ImportError:
            return False

    def doctor_full(self) -> dict:
        lite = self.doctor_lite()
        try:
            from termux_bitnet.hardware import print_hardware_summary
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                print_hardware_summary()
            lite["hardware_full"] = buf.getvalue()
        except Exception as e:
            lite["hardware_error"] = str(e)
        lite["doctor_level"] = "full"
        return lite

    def list_models(self) -> dict:
        """AVAILABLE_MODELS + ModelRegistry 통합."""
        reg_map = {m["model_id"]: m for m in self._model_reg.list_all()}
        for mid in BITNET_AVAILABLE_MODELS:
            if mid not in reg_map:
                model_path = self._models_dir / f"{mid}.gguf"
                state = "installed" if model_path.exists() else "missing"
                if state == "installed":
                    state = "unverified"  # 파일 존재 ≠ Hash 검증됨
                reg_map[mid] = {
                    "model_id": mid, "state": state,
                    "format": "gguf", "note": "1.58-bit BitNet GGUF model",
                    "verified_at": None,
                }
        return {"models": list(reg_map.values()), "total": len(reg_map),
                "models_dir": str(self._models_dir)}

    def model_status(self, model_id: str | None = None) -> dict:
        if model_id:
            rec = self._model_reg.get(model_id)
            if rec is None:
                # AVAILABLE_MODELS에는 있지만 Registry에 없는 경우
                if model_id in BITNET_AVAILABLE_MODELS:
                    return {"model": {"model_id": model_id, "state": "missing",
                                      "note": "Available but not downloaded"}}
                raise ModelNotFound(model_id)
            return {"model": rec}
        return self.list_models()

    def install_model(self, request: dict) -> dict:
        from ameva_component import ModelInstaller
        url = request.get("url", ""); filename = request.get("filename", "")
        sha256 = request.get("sha256", ""); expected_bytes = int(request.get("expected_bytes", 0))
        model_id = request.get("model_id") or Path(filename).stem
        self._models_dir.mkdir(parents=True, exist_ok=True)
        installer = ModelInstaller(self.COMPONENT_ID, self._models_dir, self._model_reg)
        return installer.install(url=url, filename=filename, sha256=sha256,
                                 expected_bytes=expected_bytes, model_id=model_id,
                                 after_download=self._verify_gguf)

    def _verify_gguf(self, path: Path) -> None:
        with path.open("rb") as f:
            magic = f.read(4)
        if magic != b"GGUF":
            raise ValueError(f"BitNet GGUF magic mismatch: got {magic!r}")

    async def activate_model(self, request: dict) -> dict:
        model_id = request.get("model_id", "")
        rec = self._model_reg.get(model_id)
        if rec is None:
            if model_id in BITNET_AVAILABLE_MODELS:
                raise ModelLoadFailed(model_id, "Model not downloaded yet")
            raise ModelNotFound(model_id)
        if ModelState.from_str(rec.get("state", "missing")) not in (ModelState.INSTALLED, ModelState.INACTIVE):
            raise ModelLoadFailed(model_id, f"State is '{rec.get('state')}'")
        with self._act_lock.acquire(timeout=60.0):
            self._model_reg.set_state(model_id, ModelState.ACTIVE)
            self._write_state()
        return {"activated": True, "model_id": model_id,
                "rollback": {"attempted": False, "succeeded": False}}

    async def deactivate_model(self, request: dict) -> dict:
        model_id = request.get("model_id", "")
        self._model_reg.set_state(model_id, ModelState.INACTIVE)
        self._write_state()
        return {"deactivated": True, "model_id": model_id}

    def list_instances(self) -> dict:
        instances = self._inst_reg.list_all()
        return {"instances": [i.to_dict() for i in instances], "total": len(instances)}

    async def start_instance(self, request: dict) -> dict:
        model_id = request.get("model_id", "")
        instance_id = request.get("instance_id") or f"bitnet-worker-{int(time.time())}"
        inst = InstanceStatus(
            instance_id=instance_id, component_id=self.COMPONENT_ID,
            model_id=model_id, state=InstanceState.HOT,
            active_jobs=0, queue_depth=0, max_concurrency=1,
            backend="arm64-bitnet", started_at=time.time(), last_heartbeat=time.time(),
            last_error=None, control_mode=ControlMode.IN_PROCESS,
        )
        self._inst_reg.register(inst)
        self._write_state()
        return {"instance_id": instance_id, "state": InstanceState.HOT.value}

    async def drain_instance(self, instance_id: str) -> dict:
        from ameva_component import InstanceNotFound
        if not self._inst_reg.get(instance_id): raise InstanceNotFound(instance_id)
        self._inst_reg.update_state(instance_id, InstanceState.DRAINING)
        return {"instance_id": instance_id, "state": InstanceState.DRAINING.value}

    async def stop_instance(self, instance_id: str) -> dict:
        from ameva_component import InstanceNotFound
        if not self._inst_reg.get(instance_id): raise InstanceNotFound(instance_id)
        self._inst_reg.update_state(instance_id, InstanceState.STOPPED)
        self._inst_reg.remove(instance_id)
        self._write_state()
        return {"instance_id": instance_id, "state": InstanceState.STOPPED.value}

    def _write_state(self, *, ready: bool | None = None, last_error: str | None = None) -> None:
        ts = now_timestamps()
        hot = [i for i in self._inst_reg.list_all() if i.state == InstanceState.HOT]
        _, pid_alive = self._check_pid()
        _ready = self._check_engine_binary() if ready is None else ready
        self._state_file.write({
            "protocol": "ameva-component-status/1", "component_id": self.COMPONENT_ID,
            "component_type": self.COMPONENT_TYPE, "version": self._get_version(),
            "ready": _ready, "degraded": not _ready, **ts,
            "active_models": [i.model_id for i in hot], "last_error": last_error,
        })
