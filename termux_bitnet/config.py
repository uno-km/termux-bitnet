"""Configuration and generation hyperparameters for termux-bitnet."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BitNetConfig:
    """Inference hyperparameters and runtime settings."""
    model_path: str = ""
    system_prompt: str = ""
    stop_tokens: str = ""
    device: str = "auto"
    n_threads: int = 4
    n_ctx: int = 2048
    n_batch: int = 512
    n_ubatch: int = 512
    n_predict: int = 128
    top_k: int = 40
    repeat_last_n: int = 64
    n_gpu_layers: int = 0
    seed: int = 0
    temperature: float = 0.7
    top_p: float = 0.95
    min_p: float = 0.05
    typical_p: float = 1.0
    repeat_penalty: float = 1.15
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    flash_attn: bool = False
    verbose: bool = False

    def __post_init__(self):
        """Auto-discover cached model if model_path is not explicitly provided."""
        if not self.model_path or not self.model_path.strip():
            from pathlib import Path
            import os
            cache_dir = Path.home() / ".cache" / "termux-bitnet" / "models"
            if cache_dir.exists():
                for preferred in [
                    "bitnet-2b-ggml-model-i2_s.gguf",
                    "bitnet-b1.58-2b-i1_s.gguf",
                    "bitnet-b1.58-2b-i1_m.gguf",
                    "bitnet-large.gguf",
                    "bitnet_b1_58-large.i2_s.gguf",
                    "bitnet_b1_58-large.Q4_0.gguf",
                ]:
                    p = cache_dir / preferred
                    if p.exists() and p.is_file():
                        self.model_path = str(p)
                        return
                ggufs = list(cache_dir.glob("*.gguf"))
                if ggufs:
                    ggufs.sort(key=lambda x: (0 if ("i2_s" in x.name or "i1_s" in x.name or "i1_m" in x.name) else 1, x.name))
                    self.model_path = str(ggufs[0])


@dataclass
class GenerationMetrics:
    """Performance telemetry of a single generation."""
    prompt_tokens: int = 0
    generated_tokens: int = 0
    prompt_eval_time_ms: float = 0.0
    eval_time_ms: float = 0.0
    tokens_per_second: float = 0.0
    total_time_ms: float = 0.0
