"""High-level Python SDK Engine for BitNet 1.58-bit (i2_s) inference (Strict Fail-Fast Architecture)."""

import os
import sys
import ctypes
from typing import Generator, Optional, List, Tuple
from pathlib import Path

from termux_bitnet.config import BitNetConfig, GenerationMetrics
from termux_bitnet.hardware import detect_hardware
from termux_bitnet.exceptions import BitNetEngineNotFound, RuntimeNotFoundError


# C ABI Structures
class CBitNetParams(ctypes.Structure):
    _fields_ = [
        ("model_path", ctypes.c_char_p),
        ("system_prompt", ctypes.c_char_p),
        ("stop_tokens", ctypes.c_char_p),
        ("n_threads", ctypes.c_int32),
        ("n_ctx", ctypes.c_int32),
        ("n_batch", ctypes.c_int32),
        ("n_ubatch", ctypes.c_int32),
        ("n_predict", ctypes.c_int32),
        ("top_k", ctypes.c_int32),
        ("repeat_last_n", ctypes.c_int32),
        ("n_gpu_layers", ctypes.c_int32),
        ("seed", ctypes.c_uint32),
        ("temperature", ctypes.c_float),
        ("top_p", ctypes.c_float),
        ("min_p", ctypes.c_float),
        ("typical_p", ctypes.c_float),
        ("repeat_penalty", ctypes.c_float),
        ("frequency_penalty", ctypes.c_float),
        ("presence_penalty", ctypes.c_float),
        ("flash_attn", ctypes.c_bool),
        ("verbose", ctypes.c_bool),
    ]


STREAM_CB_TYPE = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_int32, ctypes.c_void_p)


class BitNetEngine:
    """High-performance Python wrapper around the native BitNet C++ core engine."""

    def __init__(self, config: Optional[BitNetConfig] = None):
        self.config = config or BitNetConfig()
        if self.config.n_threads <= 0:
            hw = detect_hardware()
            self.config.n_threads = hw.recommended_threads

        # Strict validation of model_path if provided
        if self.config.model_path:
            expanded = os.path.abspath(os.path.expanduser(self.config.model_path))
            if not os.path.isfile(expanded):
                raise FileNotFoundError(
                    f"[termux-bitnet] Model file not found at: '{expanded}'.\n"
                    f"Download a verified BitNet model using:\n"
                    f"  termux-bitnet download bitnet-2b       (Microsoft BitNet 2B-4T, 1.13 GB)\n"
                    f"  termux-bitnet download bitnet-large    (BitNet Large 0.7B, 700 MB)\n"
                    f"  termux-bitnet download bitnet-3b       (BitNet 3B, 2.4 GB)\n"
                    f"Or visit Hugging Face: https://huggingface.co/1bitLLM/bitnet_b1_58-large-GGUF"
                )
            self.config.model_path = expanded

        self._lib = self._load_native_library()
        self._ctx = None
        self._setup_bindings()

        if self._lib and self.config.model_path:
            self._init_context()

    def _find_library_path(self) -> Optional[Path]:
        """Locate compiled native shared library in package or system paths."""
        candidates = [
            # Local package build directory
            Path(__file__).parent / "libtermux_bitnet.so",
            Path(__file__).parent / "termux_bitnet.dll",
            Path(__file__).parent / "libtermux_bitnet.dylib",
            # CMake build outputs
            Path(__file__).parents[1] / "build" / "libtermux_bitnet.so",
            Path(__file__).parents[1] / "build" / "Release" / "termux_bitnet.dll",
            Path(__file__).parents[1] / "build" / "lib" / "libtermux_bitnet.so",
            Path(__file__).parents[1] / "libtermux_bitnet.so",
        ]
        for path in candidates:
            if path.exists():
                return path
        return None

    def _load_native_library(self) -> Optional[ctypes.CDLL]:
        """Dynamically load the C ABI shared library."""
        lib_path = self._find_library_path()
        if lib_path and lib_path.exists():
            try:
                return ctypes.CDLL(str(lib_path))
            except Exception as e:
                print(f"[termux-bitnet] Warning: Failed to load native library '{lib_path}': {e}")
        return None

    def _setup_bindings(self) -> None:
        """Define C function signatures."""
        if not self._lib:
            return

        self._lib.bitnet_default_params.restype = CBitNetParams
        self._lib.bitnet_default_params.argtypes = []

        self._lib.bitnet_init.restype = ctypes.c_void_p
        self._lib.bitnet_init.argtypes = [ctypes.POINTER(CBitNetParams)]

        self._lib.bitnet_free.restype = None
        self._lib.bitnet_free.argtypes = [ctypes.c_void_p]

        self._lib.bitnet_tokenize.restype = ctypes.c_int32
        self._lib.bitnet_tokenize.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int32), ctypes.c_int32]

        self._lib.bitnet_token_to_str.restype = ctypes.c_int32
        self._lib.bitnet_token_to_str.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_char_p, ctypes.c_int32]

        self._lib.bitnet_eval.restype = ctypes.c_int32
        self._lib.bitnet_eval.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int32), ctypes.c_int32]

        self._lib.bitnet_sample.restype = ctypes.c_int32
        self._lib.bitnet_sample.argtypes = [ctypes.c_void_p]

        self._lib.bitnet_generate_stream.restype = ctypes.c_int32
        self._lib.bitnet_generate_stream.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int32, STREAM_CB_TYPE, ctypes.c_void_p]

        self._lib.bitnet_get_hardware_info.restype = None
        self._lib.bitnet_get_hardware_info.argtypes = [ctypes.c_char_p, ctypes.c_int32]

        self._lib.bitnet_get_perf_stats.restype = None
        self._lib.bitnet_get_perf_stats.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]

    def _init_context(self) -> None:
        """Instantiate C context from config."""
        if not self.config.model_path:
            raise ValueError(
                "[termux-bitnet] Cannot initialize BitNet engine context without a valid model_path. "
                "Specify config.model_path or run 'termux-bitnet download bitnet-2b'."
            )

        import unicodedata
        def _safe_encode(s: str) -> bytes:
            if not s:
                return b""
            clean_s = unicodedata.normalize("NFC", s)
            return clean_s.encode("utf-8", errors="replace")

        c_params = CBitNetParams()
        c_params.model_path = _safe_encode(self.config.model_path)
        c_params.system_prompt = _safe_encode(self.config.system_prompt)
        c_params.stop_tokens = _safe_encode(self.config.stop_tokens)
        c_params.n_threads = self.config.n_threads
        c_params.n_ctx = self.config.n_ctx
        c_params.n_batch = self.config.n_batch
        c_params.n_ubatch = self.config.n_ubatch
        c_params.n_predict = self.config.n_predict
        c_params.top_k = self.config.top_k
        c_params.repeat_last_n = self.config.repeat_last_n
        c_params.n_gpu_layers = self.config.n_gpu_layers
        c_params.seed = self.config.seed
        c_params.temperature = self.config.temperature
        c_params.top_p = self.config.top_p
        c_params.min_p = self.config.min_p
        c_params.typical_p = self.config.typical_p
        c_params.repeat_penalty = self.config.repeat_penalty
        c_params.frequency_penalty = self.config.frequency_penalty
        c_params.presence_penalty = self.config.presence_penalty
        c_params.flash_attn = self.config.flash_attn
        c_params.verbose = self.config.verbose

        self._ctx = self._lib.bitnet_init(ctypes.byref(c_params))
        if not self._ctx:
            raise RuntimeError(
                f"[termux-bitnet] Failed to initialize native model context from '{self.config.model_path}'. "
                f"Verify that the model file is a valid 1.58-bit GGUF binary."
            )

    def get_hardware_info(self) -> str:
        """Return native runtime hardware diagnostic string."""
        if self._lib:
            buf = ctypes.create_string_buffer(256)
            self._lib.bitnet_get_hardware_info(buf, 256)
            return buf.value.decode("utf-8")
        hw = detect_hardware()
        return f"Python-Engine | Arch: {hw.arch} | NEON: {hw.has_neon} | DotProd: {hw.has_dotprod} | Cores: {hw.cpu_cores}"

    def _find_bitnet_cli_binary(self) -> Optional[str]:
        import shutil
        candidates = [
            os.path.expanduser("~/BitNet_ms/3rdparty/llama.cpp/build/bin/llama-cli"),
            os.path.expanduser("~/.local/bin/llama-cli"),
            "/data/data/com.termux/files/usr/bin/llama-cli",
            shutil.which("llama-cli"),
        ]
        for c in candidates:
            if c and os.path.isfile(c) and os.access(c, os.X_OK):
                return c
        return None

    def generate_stream(self, prompt: str, max_tokens: int = 128) -> Generator[str, None, None]:
        """Stream generation tokens produced directly by the BitNet neural network."""
        if not prompt or not prompt.strip():
            raise ValueError("[termux-bitnet] Prompt cannot be empty. Please provide a valid prompt string.")

        # 1. First priority: Execute genuine 1.58-bit neural network inference via native BitNet C++ binary
        cli_bin = self._find_bitnet_cli_binary()
        if cli_bin and self.config.model_path and os.path.isfile(self.config.model_path):
            import subprocess
            cmd = [
                cli_bin,
                "-m", self.config.model_path,
                "-p", prompt,
                "-n", str(max_tokens),
                "-t", str(self.config.n_threads),
                "-c", "512",
                "--temp", str(self.config.temperature),
                "--top-p", str(self.config.top_p),
                "--top-k", str(self.config.top_k),
                "--repeat-penalty", str(self.config.repeat_penalty),
                "--repeat-last-n", str(self.config.repeat_last_n),
                "--no-warmup",
            ]
            env = os.environ.copy()
            env["LANG"] = "C.UTF-8"
            env["LC_ALL"] = "C.UTF-8"
            lib_dir = os.path.dirname(cli_bin)
            env["LD_LIBRARY_PATH"] = f"{lib_dir}:{env.get('LD_LIBRARY_PATH', '')}"
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                )
                stdout_data, _ = proc.communicate(timeout=90)
                clean_output = stdout_data
                if f"> {prompt}" in clean_output:
                    clean_output = clean_output.split(f"> {prompt}", 1)[-1]
                elif "> " in clean_output:
                    clean_output = clean_output.rsplit("> ", 1)[-1]
                for line in clean_output.splitlines():
                    if line.startswith("build :") or line.startswith("model :") or "modalities :" in line or "ftype :" in line or "Loading model" in line or "available commands:" in line or "[ Prompt:" in line:
                        continue
                    if line.strip():
                        yield line.strip() + " "
                return
            except Exception:
                pass

        # 2. Fallback to native C ABI library
        if not self._lib:
            raise BitNetEngineNotFound(
                "Native BitNet C++ runtime library is not loaded.\n"
                "Please compile/install the native engine by running: termux-bitnet install\n"
                "Or verify your ARM64 device environment."
            )

        if not self._ctx:
            self._init_context()

        chunks: List[str] = []

        def _callback(token_str: bytes, token_id: int, user_data: int) -> bool:
            if token_str:
                text = token_str.decode("utf-8", errors="ignore")
                chunks.append(text)
            return True

        import unicodedata
        safe_prompt = unicodedata.normalize("NFC", prompt).encode("utf-8", errors="replace")

        cb = STREAM_CB_TYPE(_callback)
        self._lib.bitnet_generate_stream(self._ctx, safe_prompt, max_tokens, cb, None)

        for chunk in chunks:
            yield chunk

    def generate(self, prompt: str, max_tokens: int = 128) -> str:
        """Generate full text completion."""
        return "".join(list(self.generate_stream(prompt, max_tokens)))

    def get_last_metrics(self) -> GenerationMetrics:
        """Retrieve telemetry metrics of the most recent evaluation."""
        if self._ctx and self._lib:
            p_eval = ctypes.c_double()
            eval_ms = ctypes.c_double()
            tps = ctypes.c_double()
            self._lib.bitnet_get_perf_stats(self._ctx, ctypes.byref(p_eval), ctypes.byref(eval_ms), ctypes.byref(tps))
            return GenerationMetrics(
                prompt_eval_time_ms=p_eval.value,
                eval_time_ms=eval_ms.value,
                tokens_per_second=tps.value,
                total_time_ms=p_eval.value + eval_ms.value,
            )
        return GenerationMetrics(tokens_per_second=0.0)

    def close(self) -> None:
        """Release context memory."""
        if self._ctx and self._lib:
            self._lib.bitnet_free(self._ctx)
            self._ctx = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
