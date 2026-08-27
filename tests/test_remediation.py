import pytest
import os
import sys
from termux_bitnet.engine import BitNetEngine, BitNetConfig
from termux_bitnet.exceptions import BitNetEngineNotFound
from termux_bitnet.cli import validate_model_path_or_exit, print_catalog_help


def test_bitnet_native_missing_raises_exception():
    """Verify that when native binary is absent, BitNetEngine raises BitNetEngineNotFound instead of returning fake text."""
    cfg = BitNetConfig()
    engine = BitNetEngine(cfg)
    
    if not engine._lib:
        with pytest.raises(BitNetEngineNotFound) as exc_info:
            engine.generate("Explain quantum computing")
            
        err_str = str(exc_info.value)
        assert "not loaded" in err_str.lower() or "runtime" in err_str.lower()


def test_model_missing_raises_file_not_found():
    """Verify that specifying a non-existent model path strictly raises FileNotFoundError."""
    non_existent = "/non_existent_path/fake_model.gguf"
    cfg = BitNetConfig(model_path=non_existent)
    
    with pytest.raises(FileNotFoundError) as exc_info:
        BitNetEngine(cfg)
        
    err = str(exc_info.value)
    assert "Model file not found" in err
    assert "termux-bitnet download" in err
    assert "huggingface.co/1bitLLM" in err


def test_empty_prompt_raises_value_error():
    """Verify that an empty or whitespace prompt strictly raises ValueError without fallback."""
    cfg = BitNetConfig()
    engine = BitNetEngine(cfg)
    
    with pytest.raises(ValueError) as exc_info:
        engine.generate("   ")
    assert "Prompt cannot be empty" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        engine.generate("")
    assert "Prompt cannot be empty" in str(exc_info.value)


def test_cli_model_validation_fails_fast(capsys):
    """Verify validate_model_path_or_exit exits with code 10 and prints catalog when model is missing."""
    with pytest.raises(SystemExit) as exc_info:
        validate_model_path_or_exit("")
    assert exc_info.value.code == 10

    with pytest.raises(SystemExit) as exc_info:
        validate_model_path_or_exit("/invalid/model/path.gguf")
    assert exc_info.value.code == 10

    captured = capsys.readouterr()
    assert "bitnet-2b" in captured.err
    assert "huggingface.co" in captured.err


def test_download_model_typo_suggestion():
    """Verify download_model detects typos and provides 'Did you mean' suggestions."""
    from termux_bitnet.downloader import download_model

    # Typo: bitnet2b -> bitnet-2b
    with pytest.raises(ValueError) as exc_info:
        download_model("bitnet2b")
    err = str(exc_info.value)
    assert "typo detected" in err.lower()
    assert "bitnet-2b" in err
    assert "Did you mean 'bitnet-2b'?" in err

    # Typo: bitnet-lg -> bitnet-large
    with pytest.raises(ValueError) as exc_info:
        download_model("bitnet-lg")
    err = str(exc_info.value)
    assert "typo detected" in err.lower()
    assert "bitnet-large" in err

    # Empty model name
    with pytest.raises(ValueError) as exc_info:
        download_model("")
    assert "cannot be empty" in str(exc_info.value)


def test_download_model_completely_unknown():
    """Verify completely unknown model name lists all available verified models."""
    from termux_bitnet.downloader import download_model

    with pytest.raises(ValueError) as exc_info:
        download_model("completely_nonexistent_xyz_123")
    err = str(exc_info.value)
    assert "Unknown model" in err
    assert "Available verified models" in err
    assert "bitnet-2b" in err
    assert "bitnet-large" in err
    assert "bitnet-3b" in err


def test_server_engine_uninitialized_returns_503(monkeypatch):
    """Verify server handler returns HTTP 503 and JSON error payload when engine is uninitialized."""
    import io
    import json
    from termux_bitnet.server import OpenAIHandler

    class DummyServer:
        pass

    # Ensure engine is None
    OpenAIHandler.engine = None

    class MockRequest:
        def __init__(self, body: bytes):
            self._body = io.BytesIO(body)
        def makefile(self, *args, **kwargs):
            return self._body

    req_body = json.dumps({"messages": [{"role": "user", "content": "Hello"}]}).encode("utf-8")
    
    # Instantiate handler with mock
    handler = OpenAIHandler.__new__(OpenAIHandler)
    handler.rfile = io.BytesIO(req_body)
    handler.wfile = io.BytesIO()
    handler.headers = {"Content-Length": str(len(req_body))}
    handler.path = "/v1/chat/completions"

    responses = []
    def mock_send_response(code):
        responses.append(code)
    def mock_send_header(k, v):
        pass
    def mock_end_headers():
        pass

    handler.send_response = mock_send_response
    handler.send_header = mock_send_header
    handler.end_headers = mock_end_headers

    handler.do_POST()

    output = handler.wfile.getvalue().decode("utf-8")
    assert 503 in responses
    assert "BitNet engine is not initialized" in output
    assert "service_unavailable" in output


def test_server_empty_messages_returns_400():
    """Verify server handler returns HTTP 400 when messages or prompt is empty."""
    import io
    import json
    from termux_bitnet.server import OpenAIHandler

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
    assert 400 in responses
    assert "required and must be a non-empty array" in output

