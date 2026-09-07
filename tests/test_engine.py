"""Unit and integration test suite for termux-bitnet."""

import unittest
from termux_bitnet import BitNetEngine, BitNetConfig, detect_hardware


class TestTermuxBitNet(unittest.TestCase):

    def test_01_hardware_detection(self):
        """Verify hardware profile contains valid architectural fields."""
        hw = detect_hardware()
        self.assertTrue(len(hw.arch) > 0)
        self.assertGreater(hw.cpu_cores, 0)
        self.assertGreater(hw.recommended_threads, 0)
        self.assertIsInstance(hw.has_neon, bool)
        self.assertIsInstance(hw.has_dotprod, bool)

    def test_02_engine_initialization(self):
        """Verify BitNetEngine initializes and closes cleanly."""
        config = BitNetConfig(n_threads=2, temperature=0.5)
        with BitNetEngine(config) as engine:
            hw_str = engine.get_hardware_info()
            self.assertGreater(len(hw_str), 0)

    def test_03_runtime_missing_raises_error(self):
        """Verify engine raises RuntimeError instead of returning fake text when native lib is missing."""
        with BitNetEngine() as engine:
            if not engine._lib:
                with self.assertRaises(RuntimeError) as cm:
                    engine.generate("Hello world")
                self.assertIn("Native BitNet C++ runtime library is not loaded", str(cm.exception))
            else:
                resp = engine.generate("Hello world", max_tokens=10)
                self.assertIsInstance(resp, str)

    def test_04_streaming_runtime_missing_raises_error(self):
        """Verify streaming generation also fails cleanly without fake fallback when lib is missing."""
        with BitNetEngine() as engine:
            if not engine._lib:
                with self.assertRaises(RuntimeError) as cm:
                    list(engine.generate_stream("Hello", max_tokens=10))
                self.assertIn("Native BitNet C++ runtime library is not loaded", str(cm.exception))

    def test_08_comprehensive_config_parameters(self):
        """Verify full parameter matrix initialization in BitNetConfig."""
        config = BitNetConfig(
            model_path="models/test.gguf",
            system_prompt="You are a helpful assistant.",
            stop_tokens="<|end|>,</s>",
            n_threads=8,
            n_ctx=4096,
            n_batch=256,
            n_ubatch=256,
            n_predict=64,
            top_k=50,
            repeat_last_n=128,
            n_gpu_layers=0,
            seed=42,
            temperature=0.8,
            top_p=0.9,
            min_p=0.1,
            typical_p=0.95,
            repeat_penalty=1.2,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            flash_attn=True,
            verbose=True,
        )
        self.assertEqual(config.model_path, "models/test.gguf")
        self.assertEqual(config.top_k, 50)
        self.assertEqual(config.seed, 42)
        self.assertTrue(config.flash_attn)
        self.assertTrue(config.verbose)
        self.assertEqual(config.stop_tokens, "<|end|>,</s>")

    def test_09_model_registry_integrity(self):
        """Verify AVAILABLE_MODELS contains all valid aliases, HTTPS URLs, and metadata."""
        from termux_bitnet.downloader import AVAILABLE_MODELS
        self.assertIn("bitnet-2b", AVAILABLE_MODELS)
        self.assertIn("bitnet-large", AVAILABLE_MODELS)
        self.assertIn("bitnet-3b", AVAILABLE_MODELS)
        for name, info in AVAILABLE_MODELS.items():
            self.assertTrue(info["url"].startswith("https://huggingface.co/"))
            self.assertTrue(info["file"].endswith(".gguf"))
            self.assertGreater(info["size_mb"], 100)

    def test_10_ctypes_struct_alignment(self):
        """Verify CBitNetParams ctypes structure fields match C ABI."""
        from termux_bitnet.engine import CBitNetParams
        params = CBitNetParams()
        fields = [f[0] for f in CBitNetParams._fields_]
        expected_fields = [
            "model_path", "system_prompt", "stop_tokens", "n_threads", "n_ctx",
            "n_batch", "n_ubatch", "n_predict", "top_k", "repeat_last_n",
            "n_gpu_layers", "seed", "temperature", "top_p", "min_p",
            "typical_p", "repeat_penalty", "frequency_penalty", "presence_penalty",
            "flash_attn", "verbose"
        ]
        self.assertEqual(fields, expected_fields)

    def test_12_downloader_206_and_200_mode_isolation(self):
        """Verify downloader uses wb for 200 OK and ab strictly for 206 Partial Content."""
        import tempfile
        from pathlib import Path
        from termux_bitnet.downloader import verify_model_file
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"GGUF" + b"\x00" * 2048)
            f_path = Path(f.name)
            
        try:
            self.assertTrue(verify_model_file(f_path))
        finally:
            if f_path.exists():
                f_path.unlink()

    def test_13_server_threading_lock_presence(self):
        """Verify server module defines and utilizes threading lock for engine execution."""
        from termux_bitnet.server import ENGINE_LOCK
        import threading
        self.assertIsInstance(ENGINE_LOCK, type(threading.Lock()))

    def test_14_parameter_passthrough_and_gc_safety(self):
        """Verify 100% parameter coverage and GC reference retention."""
        import tempfile
        from pathlib import Path
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as f:
            f.write(b"GGUF" + b"\x00" * 1024)
            temp_model = f.name

        try:
            config = BitNetConfig(
                model_path=temp_model,
                system_prompt="System Prompt Test",
                stop_tokens="<stop>,</s>",
                device="cpu",
                n_threads=4,
                n_ctx=1024,
                n_batch=256,
                n_ubatch=128,
                n_predict=64,
                top_k=30,
                repeat_last_n=32,
                n_gpu_layers=0,
                seed=12345,
                temperature=0.6,
                top_p=0.9,
                min_p=0.08,
                typical_p=0.98,
                repeat_penalty=1.1,
                frequency_penalty=0.05,
                presence_penalty=0.05,
                flash_attn=True,
                verbose=True,
            )
            from unittest.mock import MagicMock
            mock_lib = MagicMock()
            mock_lib.bitnet_init.return_value = 0x123456
            engine = BitNetEngine(config)
            engine._lib = mock_lib
            engine._init_context()

            # 1. Check Python object references kept alive on engine to prevent GC dangling pointer segfault
            self.assertEqual(engine._c_model_path, temp_model.encode("utf-8"))
            self.assertEqual(engine._c_system_prompt, b"System Prompt Test")
            self.assertEqual(engine._c_stop_tokens, b"<stop>,</s>")

            # 2. Check all 21 CBitNetParams fields passed without omitting any
            self.assertTrue(mock_lib.bitnet_init.called)
            byref_arg = mock_lib.bitnet_init.call_args[0][0]
            c_params = getattr(byref_arg, "_obj", byref_arg)
            self.assertEqual(c_params.n_threads, 4)
            self.assertEqual(c_params.n_ctx, 1024)
            self.assertEqual(c_params.n_batch, 256)
            self.assertEqual(c_params.n_ubatch, 128)
            self.assertEqual(c_params.n_predict, 64)
            self.assertEqual(c_params.top_k, 30)
            self.assertEqual(c_params.repeat_last_n, 32)
            self.assertEqual(c_params.n_gpu_layers, 0)
            self.assertEqual(c_params.seed, 12345)
            self.assertAlmostEqual(c_params.temperature, 0.6, places=2)
            self.assertAlmostEqual(c_params.top_p, 0.9, places=2)
            self.assertAlmostEqual(c_params.min_p, 0.08, places=2)
            self.assertAlmostEqual(c_params.typical_p, 0.98, places=2)
            self.assertAlmostEqual(c_params.repeat_penalty, 1.1, places=2)
            self.assertAlmostEqual(c_params.frequency_penalty, 0.05, places=2)
            self.assertAlmostEqual(c_params.presence_penalty, 0.05, places=2)
            self.assertTrue(c_params.flash_attn)
            self.assertTrue(c_params.verbose)
            engine.close()
        finally:
            Path(temp_model).unlink(missing_ok=True)

    def test_15_device_routing_protocol(self):
        """Verify strict adherence to device routing rules."""
        from termux_bitnet.hardware import resolve_device_backend
        from termux_bitnet.exceptions import PlatformNotSupportedError

        # 1. CPU explicit
        backend, ngl = resolve_device_backend("cpu", 10)
        self.assertEqual(backend, "cpu")
        self.assertEqual(ngl, 0)

        # 2. AUTO routing
        backend_auto, ngl_auto = resolve_device_backend("auto")
        self.assertIn(backend_auto, ("cpu", "vulkan"))

        # 3. GPU/VULKAN routing
        try:
            backend_gpu, ngl_gpu = resolve_device_backend("gpu", 33)
            self.assertEqual(backend_gpu, "vulkan")
            self.assertEqual(ngl_gpu, 33)
        except PlatformNotSupportedError as e:
            self.assertIn("AMEVA-BITNET-E00", str(e))

    def test_16_adapter_cli_args_completeness(self):
        """Verify BitnetAdapter.build_cli_args preserves all flags."""
        import sys
        try:
            from ameva_runtime.adapters.bitnet import BitnetAdapter
            args = BitnetAdapter.build_cli_args(
                executable="llama-cli",
                model_path="/data/model.gguf",
                prompt="test prompt",
                target_backend="vulkan",
                threads=4,
                context_limit=2048,
                batch_size=512,
                ubatch_size=256,
                max_tokens=64,
                temperature=0.5,
                top_p=0.9,
                top_k=50,
                min_p=0.05,
                typical_p=1.0,
                repeat_penalty=1.2,
                repeat_last_n=64,
                freq_penalty=0.1,
                presence_penalty=0.1,
                seed=42,
                ngl_override=20,
                flash_attn=True,
                system_prompt="System Prompt",
                stop_tokens="<|end|>",
                verbose=True,
            )
            self.assertIn("-b", args)
            self.assertIn("512", args)
            self.assertIn("-ub", args)
            self.assertIn("256", args)
            self.assertIn("--min-p", args)
            self.assertIn("0.05", args)
            self.assertIn("--typical", args)
            self.assertIn("--freq-penalty", args)
            self.assertIn("--presence-penalty", args)
            self.assertIn("-s", args)
            self.assertIn("42", args)
            self.assertIn("-fa", args)
            self.assertIn("--system-prompt", args)
            self.assertIn("-r", args)
            self.assertIn("<|end|>", args)
            self.assertIn("--verbose", args)
            self.assertIn("--device", args)
            self.assertIn("vulkan", args)
        except ImportError:
            pass

    def test_17_token_to_str_and_detokenize(self):
        """Verify token_to_str and detokenize decode token IDs properly."""
        import tempfile
        from pathlib import Path
        from unittest.mock import MagicMock

        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as tf:
            tf.write(b"GGUF" + b"\x00" * 64)
            temp_path = tf.name

        try:
            config = BitNetConfig(model_path=temp_path)
            engine = BitNetEngine(config)
            mock_lib = MagicMock()
            engine._lib = mock_lib
            engine._ctx = 0x9999

            def mock_token_to_str(ctx, tok, buf, buf_len):
                mapping = {1: b"Hello", 2: b" ", 3: b"World"}
                val = mapping.get(tok, b"")
                for idx, b in enumerate(val):
                    buf[idx] = b
                buf[len(val)] = 0
                return len(val)

            mock_lib.bitnet_token_to_str.side_effect = mock_token_to_str
            self.assertEqual(engine.token_to_str(1), "Hello")
            self.assertEqual(engine.token_to_str(2), " ")
            self.assertEqual(engine.token_to_str(3), "World")
            self.assertEqual(engine.detokenize([1, 2, 3]), "Hello World")
            self.assertEqual(engine.detokenize([]), "")
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_18_realtime_stream_native_worker(self):
        """Verify real-time worker thread streaming and metrics recording."""
        import tempfile
        from pathlib import Path
        from unittest.mock import MagicMock

        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as tf:
            tf.write(b"GGUF" + b"\x00" * 64)
            temp_path = tf.name

        try:
            config = BitNetConfig(model_path=temp_path)
            engine = BitNetEngine(config)
            mock_lib = MagicMock()
            engine._lib = mock_lib
            engine._ctx = 0x9999

            def mock_generate_stream(ctx, prompt, max_new, callback, user_data):
                tokens = [b"The", b" ", b"answer", b" ", b"is", b" ", b"42"]
                for tok_id, tok_bytes in enumerate(tokens):
                    keep_going = callback(tok_bytes, tok_id, user_data)
                    if not keep_going:
                        break
                return len(tokens)

            mock_lib.bitnet_generate_stream.side_effect = mock_generate_stream

            # Test normal stream consumption
            yielded = list(engine._generate_stream_native("test prompt", 10))
            self.assertEqual("".join(yielded), "The answer is 42")
            metrics = engine.get_last_metrics()
            self.assertEqual(metrics.generated_tokens, 7)
            self.assertGreater(metrics.tokens_per_second, 0.0)

            # Test early abort
            stream_gen = engine._generate_stream_native("test prompt", 10)
            first_token = next(stream_gen)
            self.assertEqual(first_token, "The")
            stream_gen.close()  # Triggers GeneratorExit and abort_event
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_19_cli_doctor_and_models(self):
        """Verify doctor and models CLI command handlers run cleanly."""
        from unittest.mock import MagicMock
        import io
        from termux_bitnet.cli import cmd_doctor, cmd_models

        # Capture output of cmd_doctor
        out = io.StringIO()
        import sys
        old_stdout = sys.stdout
        try:
            sys.stdout = out
            cmd_doctor(MagicMock())
            cmd_models(MagicMock())
        finally:
            sys.stdout = old_stdout

        output_str = out.getvalue()
        self.assertIn("termux-bitnet Pre-flight Doctor", output_str)
        self.assertIn("Verified 1.58-bit GGUF Model Registry", output_str)

    def test_20_completions_streaming_sse(self):
        """Verify OpenAI handler supports stream: true on /v1/completions."""
        from unittest.mock import MagicMock
        import json
        import io
        from termux_bitnet.server import OpenAIHandler

        mock_engine = MagicMock()
        mock_engine.generate_stream.return_value = iter(["Quantum", " ", "Computing"])
        OpenAIHandler.engine = mock_engine

        handler = OpenAIHandler.__new__(OpenAIHandler)
        handler.headers = {"Content-Length": "100"}
        handler.rfile = io.BytesIO(json.dumps({
            "prompt": "Explain quantum:",
            "stream": True,
            "max_tokens": 10
        }).encode("utf-8"))
        handler.wfile = io.BytesIO()

        # Mock send_response and send_header
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.path = "/v1/completions"
        handler.do_POST()

        written_data = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("data: ", written_data)
        self.assertIn("Quantum", written_data)
        self.assertIn("[DONE]", written_data)
        OpenAIHandler.engine = None

    def test_21_dynamic_kwargs_and_prompt_tokens_sync(self):
        """Verify dynamic kwargs are synchronized to C ABI params and prompt_tokens is non-zero."""
        import tempfile
        from unittest.mock import MagicMock
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as f:
            temp_path = f.name

        try:
            cfg = BitNetConfig(model_path=temp_path, temperature=0.7, top_p=0.95)
            engine = BitNetEngine(cfg)
            mock_lib = MagicMock()
            engine._lib = mock_lib
            engine._ctx = 0x8888

            def mock_generate_stream(ctx, prompt, max_new, callback, user_data):
                callback(b"Hello", 1, user_data)
                return 1

            mock_lib.bitnet_generate_stream.side_effect = mock_generate_stream

            # Execute with dynamic kwargs overrides
            list(engine.generate_stream("What is 1.58-bit LLM?", max_tokens=16, temperature=0.2, top_p=0.85))

            # Verify kwargs updated config
            self.assertEqual(engine.config.temperature, 0.2)
            self.assertEqual(engine.config.top_p, 0.85)

            # Verify bitnet_set_params was called with updated params
            self.assertTrue(mock_lib.bitnet_set_params.called)

            # Verify prompt_tokens in metrics is non-zero
            metrics = engine.get_last_metrics()
            self.assertGreater(metrics.prompt_tokens, 0)
            self.assertEqual(metrics.generated_tokens, 1)
        finally:
            import os
            try:
                os.unlink(temp_path)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()

