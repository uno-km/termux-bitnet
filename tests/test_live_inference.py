"""Live on-device integration test suite for real BitNet GGUF models (Strict Fail-Fast)."""

import os
import unittest
from pathlib import Path

from termux_bitnet.config import BitNetConfig
from termux_bitnet.engine import BitNetEngine


class TestLiveBitNetInference(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cache_dir = Path.home() / ".cache" / "termux-bitnet" / "models"
        candidates = [
            cache_dir / "bitnet-2b-ggml-model-i2_s.gguf",
            cache_dir / "bitnet_b1_58-large.Q4_0.gguf",
            cache_dir / "bitnet-large.gguf",
        ]
        cls.model_path = None
        for c in candidates:
            if c.exists():
                cls.model_path = str(c)
                break
        if not cls.model_path:
            ggufs = list(cache_dir.glob("*.gguf")) if cache_dir.exists() else []
            if ggufs:
                cls.model_path = str(ggufs[0])

    def setUp(self):
        if not self.model_path:
            self.skipTest("No cached GGUF model available for live test")

    def test_01_live_engine_initialization(self):
        cfg = BitNetConfig(model_path=self.model_path, n_threads=4)
        with BitNetEngine(cfg) as engine:
            hw_info = engine.get_hardware_info()
            self.assertIn("ARM64", hw_info)
            self.assertIn("DOTPROD = 1", hw_info)
            self.assertIsNotNone(engine._ctx)

    def test_02_live_tokenization_and_detokenization(self):
        cfg = BitNetConfig(model_path=self.model_path, n_threads=4)
        with BitNetEngine(cfg) as engine:
            prompt = "The quick brown fox jumps over the lazy dog."
            tokens = engine.tokenize(prompt)
            self.assertIsInstance(tokens, list)
            self.assertGreater(len(tokens), 5)
            self.assertEqual(tokens[0], 128000)  # BOS token

    def test_03_live_stream_generation(self):
        cfg = BitNetConfig(model_path=self.model_path, n_threads=4, temperature=0.7)
        with BitNetEngine(cfg) as engine:
            prompt = "1 + 1 equals"
            chunks = []
            for chunk in engine.generate_stream(prompt, max_tokens=10):
                chunks.append(chunk)
            full_response = "".join(chunks)
            self.assertGreater(len(full_response), 0)
            
            metrics = engine.get_last_metrics()
            self.assertGreater(metrics.prompt_eval_time_ms, 0.0)
            self.assertGreater(metrics.tokens_per_second, 0.1)

    def test_04_stress_loop_stability(self):
        cfg = BitNetConfig(model_path=self.model_path, n_threads=4, temperature=0.5)
        with BitNetEngine(cfg) as engine:
            for i in range(3):
                prompt = f"Count {i}:"
                resp = engine.generate(prompt, max_tokens=8)
                self.assertIsInstance(resp, str)
                self.assertGreater(len(resp), 0)


if __name__ == "__main__":
    unittest.main()
