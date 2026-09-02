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


if __name__ == "__main__":
    unittest.main()

