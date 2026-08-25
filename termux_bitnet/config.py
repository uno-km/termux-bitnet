"""Configuration and generation hyperparameters for termux-bitnet."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BitNetConfig:
    """Inference hyperparameters and runtime settings."""
    model_path: str = ""
    system_prompt: str = ""
    stop_tokens: str = ""
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


@dataclass
class GenerationMetrics:
    """Performance telemetry of a single generation."""
    prompt_tokens: int = 0
    generated_tokens: int = 0
    prompt_eval_time_ms: float = 0.0
    eval_time_ms: float = 0.0
    tokens_per_second: float = 0.0
    total_time_ms: float = 0.0
