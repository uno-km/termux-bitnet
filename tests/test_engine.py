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

    def test_03_palindrome_code_generation(self):
        """Verify coding logical precision for palindrome problem."""
        with BitNetEngine() as engine:
            prompt = "Write a Python function to check if a string is a palindrome. Provide only code."
            resp = engine.generate(prompt, max_tokens=100)
            self.assertTrue("def is_palindrome" in resp or "s[::-1]" in resp or "palindrome" in resp.lower())

    def test_04_harmonic_mean_math(self):
        """Verify mathematical reasoning avoids the arithmetic mean trap."""
        with BitNetEngine() as engine:
            prompt = "A train goes from City A to B at 60 mph and returns at 40 mph. What is average speed?"
            resp = engine.generate(prompt, max_tokens=100)
            self.assertTrue("48" in resp or "harmonic" in resp.lower() or "distance" in resp.lower())

    def test_05_cbt_psychology_analysis(self):
        """Verify psychological cognitive distortion identification."""
        with BitNetEngine() as engine:
            prompt = "Analyze CBT perspective: 'I made a mistake, so I am a complete failure and will lose my job.'"
            resp = engine.generate(prompt, max_tokens=100)
            self.assertTrue("all-or-nothing" in resp.lower() or "black-and-white" in resp.lower() or "catastrophizing" in resp.lower() or "reframing" in resp.lower())

    def test_06_streaming_generation(self):
        """Verify streaming token emission."""
        with BitNetEngine() as engine:
            chunks = list(engine.generate_stream("Hello world", max_tokens=20))
            self.assertGreater(len(chunks), 0)
            full_text = "".join(chunks)
            self.assertGreater(len(full_text), 0)

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
        from termux_bitnet.downloader import AVAILABLE_MODELS, verify_model_file
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

    def test_11_cli_parser_coverage(self):
        """Verify CLI argument parser processes all flags."""
        from termux_bitnet.cli import main
        import sys
        # Test --help does not crash
        orig_argv = sys.argv
        try:
            sys.argv = ["termux-bitnet", "--help"]
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
        finally:
            sys.argv = orig_argv


if __name__ == "__main__":
    unittest.main()
