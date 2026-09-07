"""High-level Python SDK Engine for BitNet 1.58-bit (i2_s) inference (Strict Fail-Fast Architecture)."""

import os
import sys
import ctypes
import logging
from typing import Generator, Optional, List, Tuple
from pathlib import Path

from termux_bitnet.config import BitNetConfig, GenerationMetrics
from termux_bitnet.hardware import detect_hardware
from termux_bitnet.exceptions import BitNetEngineNotFound, RuntimeNotFoundError

logger = logging.getLogger(__name__)


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

        # Hardware acceleration context delegation via ameva-runtime
        self.avr_ctx = None
        try:
            from ameva_runtime import vulkan as avr
            self.avr_ctx = avr.get_or_create_context(self.config.device)
            if self.avr_ctx.is_gpu and self.config.n_gpu_layers == 0:
                self.config.n_gpu_layers = 33
        except Exception as e:
            if str(self.config.device).lower() in ("gpu", "vulkan"):
                raise RuntimeError(
                    f"[termux-bitnet] [FAIL-FAST] Explicit GPU backend requested ('{self.config.device}'), "
                    f"but Vulkan hardware initialization failed: {e}"
                )

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
        self._last_metrics = GenerationMetrics()
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

        safe_max_tokens = max(1, min(int(max_tokens), 8192))
        cli_bin = self._find_bitnet_cli_binary()
        has_valid_model = bool(self.config.model_path and os.path.isfile(self.config.model_path))

        # Backend selection logic: In-process Native C ABI (Priority 1) or CLI binary (Secondary/Explicit)
        if self._lib:
            yield from self._generate_stream_native(prompt, safe_max_tokens)
        elif cli_bin and has_valid_model:
            yield from self._generate_stream_cli(prompt, safe_max_tokens, cli_bin)
        else:
            raise BitNetEngineNotFound(
                "[termux-bitnet] [FAIL-FAST] Native BitNet C++ runtime library is not loaded.\n"
                "No usable BitNet inference runtime detected (neither 'libtermux_bitnet.so' shared library nor 'llama-cli' binary found).\n"
                "Please compile/install the native engine by running: termux-bitnet install\n"
                "Or verify your ARM64 device environment."
            )

    def _generate_stream_cli(self, prompt: str, max_tokens: int, cli_bin: str) -> Generator[str, None, None]:
        """Execute inference stream via standalone native CLI binary."""
        import subprocess
        import time

        cmd = [
            cli_bin,
            "-m", self.config.model_path,
            "-p", prompt,
            "-n", str(max_tokens),
            "-t", str(self.config.n_threads),
            "-c", str(self.config.n_ctx if self.config.n_ctx > 0 else 512),
            "--temp", str(self.config.temperature),
            "--top-p", str(self.config.top_p),
            "--top-k", str(self.config.top_k),
            "--repeat-penalty", str(self.config.repeat_penalty),
            "--repeat-last-n", str(self.config.repeat_last_n),
            "--simple-io",
            "--no-warmup",
        ]
        if self.config.n_gpu_layers > 0:
            cmd.extend(["-ngl", str(self.config.n_gpu_layers)])

        env = os.environ.copy()
        env["LANG"] = "C.UTF-8"
        env["LC_ALL"] = "C.UTF-8"
        lib_dir = os.path.dirname(cli_bin)
        try:
            from ameva_runtime.vulkan.adapters import get_vulkan_env
            env = get_vulkan_env(env)
            if lib_dir and lib_dir not in env["LD_LIBRARY_PATH"]:
                env["LD_LIBRARY_PATH"] = f"{lib_dir}:{env['LD_LIBRARY_PATH']}"
        except ImportError:
            env["LD_LIBRARY_PATH"] = f"{lib_dir}:{env.get('LD_LIBRARY_PATH', '')}"

        proc = None
        has_yielded = False
        clean_tokens = []
        t0 = time.time()

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
                env=env,
            )

            prompt_buffer = ""
            prompt_stripped = False

            while True:
                chunk = proc.stdout.read(32)
                if not chunk:
                    if proc.poll() is not None:
                        break
                    continue

                if not prompt_stripped:
                    prompt_buffer += chunk
                    clean_pb = prompt_buffer.strip()
                    clean_pr = prompt.strip()
                    if clean_pb.startswith(clean_pr) or clean_pr in clean_pb:
                        prompt_stripped = True
                        idx = prompt_buffer.find(prompt)
                        remainder = prompt_buffer[idx + len(prompt):] if idx != -1 else ""
                        if remainder:
                            clean_tokens.append(remainder)
                            has_yielded = True
                            yield remainder
                    elif len(prompt_buffer) > len(prompt) + 64:
                        prompt_stripped = True
                        clean_tokens.append(prompt_buffer)
                        has_yielded = True
                        yield prompt_buffer
                else:
                    clean_tokens.append(chunk)
                    has_yielded = True
                    yield chunk

            proc.wait(timeout=5)
            t1 = time.time()
            elapsed_sec = max(t1 - t0, 0.001)
            full_text = "".join(clean_tokens)
            token_count = self.count_tokens(full_text)
            tps = token_count / elapsed_sec
            self._last_metrics = GenerationMetrics(
                generated_tokens=token_count,
                eval_time_ms=elapsed_sec * 1000.0,
                tokens_per_second=tps,
                total_time_ms=elapsed_sec * 1000.0,
            )
        except Exception as e:
            if proc and proc.poll() is None:
                try:
                    proc.kill()
                    proc.wait(timeout=2)
                except OSError as _kill_err:
                    import logging
                    logging.getLogger("termux_bitnet").warning(
                        "[termux-bitnet] Failed to kill inference process pid=%s: %s",
                        getattr(proc, 'pid', 'unknown'), _kill_err,
                    )

            # 토큰이 이미 yield된 경우 부분 결과 오염 방지를 위해 즉시 실패
            if has_yielded:
                raise RuntimeError(
                    f"[termux-bitnet] CLI inference stream failed mid-generation: {e}"
                ) from e

            raise RuntimeError(f"[termux-bitnet] [FAIL-FAST] CLI inference failed: {e}") from e



    def _generate_stream_native(self, prompt: str, max_tokens: int) -> Generator[str, None, None]:
        """Execute inference stream via in-process C ABI shared library."""
        import time
        import unicodedata

        if not self._lib:
            raise BitNetEngineNotFound("Native BitNet C++ runtime library is not loaded.")

        if not self._ctx:
            self._init_context()

        chunks: List[str] = []

        def _callback(token_str: bytes, token_id: int, user_data: int) -> bool:
            if token_str:
                text = token_str.decode("utf-8", errors="ignore")
                chunks.append(text)
            return True

        safe_prompt = unicodedata.normalize("NFC", prompt).encode("utf-8", errors="replace")
        cb = STREAM_CB_TYPE(_callback)

        t0 = time.time()
        self._lib.bitnet_generate_stream(self._ctx, safe_prompt, max_tokens, cb, None)
        t1 = time.time()

        elapsed_sec = max(t1 - t0, 0.001)
        gen_token_count = max(len(chunks), 1)
        tps = gen_token_count / elapsed_sec
        self._last_metrics = GenerationMetrics(
            generated_tokens=gen_token_count,
            eval_time_ms=elapsed_sec * 1000.0,
            tokens_per_second=tps,
            total_time_ms=elapsed_sec * 1000.0,
        )

        for chunk in chunks:
            yield chunk

    def tokenize(self, text: str) -> List[int]:
        """Tokenize input text into token IDs using native C++ vocabulary."""
        if not text:
            return []

        # 1. Execute true native C++ bitnet_tokenize with auto-initialized context
        if not self._lib:
            raise BitNetEngineNotFound(
                "[termux-bitnet] [FAIL-FAST] Native C ABI library is not loaded. Cannot tokenize without native engine."
            )

        if not self._ctx and self.config.model_path and os.path.isfile(self.config.model_path):
            self._init_context()

        if not self._ctx:
            raise RuntimeError(
                "[termux-bitnet] [FAIL-FAST] Engine context is uninitialized. A valid model_path is required for tokenization."
            )

        import unicodedata
        safe_text = unicodedata.normalize("NFC", text).encode("utf-8", errors="replace")
        max_tokens = len(safe_text) * 2 + 128
        buf = (ctypes.c_int32 * max_tokens)()
        count = self._lib.bitnet_tokenize(self._ctx, safe_text, buf, max_tokens)
        if count < 0:
            raise RuntimeError(
                f"[termux-bitnet] [FAIL-FAST] Native BPE tokenization failed with error code {count} for text: '{text[:40]}...'"
            )
        return [buf[i] for i in range(count)]

    def count_tokens(self, text: str) -> int:
        """Count true token length without byte division heuristics."""
        if not text or not text.strip():
            return 0
        tokens = self.tokenize(text)
        return max(len(tokens), 1)

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
        return self._last_metrics

    def close(self) -> None:
        """Release context memory."""
        if self._ctx and self._lib:
            self._lib.bitnet_free(self._ctx)
            self._ctx = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
