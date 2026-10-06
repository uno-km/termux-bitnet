import unittest
import io
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

from termux_bitnet.engine import BitNetEngine, BitNetConfig
from termux_bitnet.exceptions import BitNetEngineNotFound
from termux_bitnet.cli import validate_model_path_or_exit
from termux_bitnet.downloader import download_model
from termux_bitnet.server import OpenAIHandler


class TestTermuxBitNetRemediation(unittest.TestCase):

    def test_bitnet_native_missing_raises_exception(self):
        """Verify that when native binary/lib is absent and no model is specified, engine raises exception."""
        cfg = BitNetConfig()
        engine = BitNetEngine(cfg)
        
        if not engine._lib and not engine._find_bitnet_cli_binary():
            with self.assertRaises(BitNetEngineNotFound) as ctx:
                engine.generate("Explain quantum computing")
            err_str = str(ctx.exception)
            self.assertTrue("not loaded" in err_str.lower() or "runtime" in err_str.lower())

    def test_model_missing_raises_file_not_found(self):
        """Verify that specifying a non-existent model path strictly raises FileNotFoundError."""
        non_existent = "/non_existent_path/fake_model.gguf"
        cfg = BitNetConfig(model_path=non_existent)
        
        with self.assertRaises(FileNotFoundError) as ctx:
            BitNetEngine(cfg)
            
        err = str(ctx.exception)
        self.assertIn("Model file not found", err)
        self.assertIn("termux-bitnet download", err)
        self.assertIn("huggingface.co/1bitLLM", err)

    def test_empty_prompt_raises_value_error(self):
        """Verify that an empty or whitespace prompt strictly raises ValueError without fallback."""
        cfg = BitNetConfig()
        engine = BitNetEngine(cfg)
        
        with self.assertRaises(ValueError) as ctx:
            engine.generate("   ")
        self.assertIn("Prompt cannot be empty", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            engine.generate("")
        self.assertIn("Prompt cannot be empty", str(ctx.exception))

    def test_cli_model_validation_fails_fast(self):
        """Verify validate_model_path_or_exit exits with code 10 and prints catalog when model is missing."""
        stderr_capture = io.StringIO()
        with patch("pathlib.Path.home", return_value=Path("/non_existent_cache_dir_for_test")):
            with patch("sys.stderr", stderr_capture):
                with self.assertRaises(SystemExit) as ctx:
                    validate_model_path_or_exit("")
                self.assertEqual(ctx.exception.code, 10)

        with patch("sys.stderr", stderr_capture):
            with self.assertRaises(SystemExit) as ctx:
                validate_model_path_or_exit("/invalid/model/path.gguf")
            self.assertEqual(ctx.exception.code, 10)

        err_out = stderr_capture.getvalue()
        self.assertIn("bitnet-2b", err_out)
        self.assertIn("huggingface.co", err_out)

    def test_download_model_typo_suggestion(self):
        """Verify download_model detects typos and provides 'Did you mean' suggestions."""
        # Typo: bitnet2b -> bitnet-2b
        with self.assertRaises(ValueError) as ctx:
            download_model("bitnet2b")
        err = str(ctx.exception)
        self.assertIn("typo detected", err.lower())
        self.assertIn("bitnet-2b", err)
        self.assertIn("Did you mean 'bitnet-2b'?", err)

        # Typo: bitnet-lg -> bitnet-large
        with self.assertRaises(ValueError) as ctx:
            download_model("bitnet-lg")
        err = str(ctx.exception)
        self.assertIn("typo detected", err.lower())
        self.assertIn("bitnet-large", err)

        # Empty model name
        with self.assertRaises(ValueError) as ctx:
            download_model("")
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_download_model_completely_unknown(self):
        """Verify completely unknown model name lists all available verified models."""
        with self.assertRaises(ValueError) as ctx:
            download_model("completely_nonexistent_xyz_123")
        err = str(ctx.exception)
        self.assertIn("Unknown model", err)
        self.assertIn("Available verified models", err)
        self.assertIn("bitnet-2b", err)
        self.assertIn("bitnet-large", err)
        self.assertIn("bitnet-3b", err)

    def test_server_engine_uninitialized_returns_503(self):
        """Verify server handler returns HTTP 503 and JSON error payload when engine is uninitialized."""
        OpenAIHandler.engine = None

        req_body = json.dumps({"messages": [{"role": "user", "content": "Hello"}]}).encode("utf-8")
        
        handler = OpenAIHandler.__new__(OpenAIHandler)
        handler.rfile = io.BytesIO(req_body)
        handler.wfile = io.BytesIO()
        handler.headers = {"Content-Length": str(len(req_body))}
        handler.path = "/v1/chat/completions"

        responses = []
        handler.send_response = lambda code: responses.append(code)
        handler.send_header = lambda k, v: None
        handler.end_headers = lambda: None

        handler.do_POST()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn(503, responses)
        self.assertIn("BitNet engine is not initialized", output)
        self.assertIn("service_unavailable", output)

    def test_server_empty_messages_returns_400(self):
        """Verify server handler returns HTTP 400 when messages or prompt is empty."""
        class MockEngine:
            def generate(self, prompt, max_tokens=256):
                return "mock response"

        OpenAIHandler.engine = MockEngine()

        req_body = json.dumps({"messages": []}).encode("utf-8")
        handler = OpenAIHandler.__new__(OpenAIHandler)
        handler.rfile = io.BytesIO(req_body)
        handler.wfile = io.BytesIO()
        handler.headers = {"Content-Length": str(len(req_body))}
        handler.path = "/v1/chat/completions"

        responses = []
        handler.send_response = lambda code: responses.append(code)
        handler.send_header = lambda k, v: None
        handler.end_headers = lambda: None

        handler.do_POST()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn(400, responses)
        self.assertIn("required and must be a non-empty array", output)

    def test_server_large_payload_rejected(self):
        """Verify server handler rejects payloads exceeding size limit with HTTP 413."""
        OpenAIHandler.engine = None
        handler = OpenAIHandler.__new__(OpenAIHandler)
        handler.rfile = io.BytesIO(b"")
        handler.wfile = io.BytesIO()
        handler.headers = {"Content-Length": str(20 * 1024 * 1024)} # 20MB
        handler.path = "/v1/chat/completions"

        responses = []
        handler.send_response = lambda code: responses.append(code)
        handler.send_header = lambda k, v: None
        handler.end_headers = lambda: None

        handler.do_POST()

        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn(413, responses)
        self.assertIn("Payload Too Large", output)

    def test_no_fake_arithmetic_in_native_core(self):
        """Verify native C++ core contains zero fake arithmetic patterns (e.g. (i*17)%64 or (r+k)%3-1)."""
        import os
        from pathlib import Path
        cpp_file = Path(__file__).parent.parent / "src" / "llama_bitnet_core.cpp"
        if cpp_file.exists():
            content = cpp_file.read_text(encoding="utf-8")
            self.assertNotIn("(i * 17) % 64", content)
            self.assertNotIn("(r + k) % 3", content)
            self.assertIn("CreateFileMappingA", content) # Windows mmap
            self.assertIn("mmap(", content)               # POSIX mmap

    def test_korean_multibyte_token_counting_accuracy(self):
        """Verify Korean/multibyte text token counting produces valid positive count without byte division heuristic."""
        from termux_bitnet import BitNetEngine, BitNetConfig
        
        engine = BitNetEngine(BitNetConfig())
        korean_text = "안녕하세요! termux-bitnet 1.58비트 고성능 온디바이스 엔진입니다."
        
        if not engine._lib:
            with self.assertRaises(BitNetEngineNotFound):
                engine.count_tokens(korean_text)
            return

        count = engine.count_tokens(korean_text)
        self.assertGreater(count, 0)
        self.assertLessEqual(count, len(korean_text) * 2)
        
        tokens = engine.tokenize(korean_text)
        self.assertIsInstance(tokens, list)
        self.assertEqual(len(tokens), count)

    def test_setup_py_fails_fast_on_cmake_compilation_failure(self):
        """Direct line verification that setup.py CMakeBuild strictly raises RuntimeError on CMake errors."""
        import sys
        import subprocess
        from pathlib import Path
        from unittest.mock import patch

        setup_py_path = Path(__file__).parent.parent / "setup.py"
        self.assertTrue(setup_py_path.exists())

        # Dynamically import CMakeBuild from setup.py
        import importlib.util
        spec = importlib.util.spec_from_file_location("setup_module", str(setup_py_path))
        setup_mod = importlib.util.module_from_spec(spec)
        
        # Prevent setup() execution during import
        with patch("setuptools.setup"):
            spec.loader.exec_module(setup_mod)

        cmake_ext = setup_mod.CMakeExtension("termux_bitnet._libtermux_bitnet", sourcedir="non_existent_dir")
        builder = setup_mod.CMakeBuild.__new__(setup_mod.CMakeBuild)
        builder.build_temp = str(Path(__file__).parent / "_test_build_temp")
        builder.get_ext_fullpath = lambda name: str(Path(__file__).parent / "_test_build_temp" / "libtermux_bitnet.so")

        # Verify that CMakeBuild.build_extension raises RuntimeError unconditionally
        with self.assertRaises(RuntimeError) as cm:
            builder.build_extension(cmake_ext)
        self.assertIn("[termux-bitnet] Native build failed", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

