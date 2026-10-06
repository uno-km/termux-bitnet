import os
import sys
from unittest.mock import patch, MagicMock
import pytest

from termux_bitnet.config import BitNetConfig
from termux_bitnet.engine import BitNetEngine
from termux_bitnet.cli import main


def test_bitnet_config_rpc_fields():
    config = BitNetConfig(
        model_path="dummy.gguf",
        rpc="192.168.0.220:50052,192.168.0.253:50052",
        tensor_split="50,50",
    )
    assert config.rpc == "192.168.0.220:50052,192.168.0.253:50052"
    assert config.tensor_split == "50,50"


def test_bitnet_cli_arg_parsing(tmp_path, monkeypatch):
    dummy_model = tmp_path / "dummy.gguf"
    dummy_model.write_text("model_header")

    test_args = [
        "termux-bitnet",
        "run",
        "-m",
        str(dummy_model),
        "-p",
        "Hello RPC",
        "--rpc",
        "192.168.0.220:50052,192.168.0.253:50052",
        "-ts",
        "60,40",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    with patch("termux_bitnet.cli.BitNetEngine") as MockEngine:
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.__exit__.return_value = None
        mock_instance.generate_stream.return_value = ["Output token"]
        mock_instance.get_last_metrics.return_value = MagicMock(tokens_per_second=12.5, total_tokens=10, generation_time_s=0.8)
        MockEngine.return_value = mock_instance

        with patch("termux_bitnet.cli.detect_hardware"):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None

        # Verify BitNetConfig received rpc and tensor_split arguments
        assert MockEngine.call_count == 1
        passed_config = MockEngine.call_args[0][0]
        assert passed_config.rpc == "192.168.0.220:50052,192.168.0.253:50052"
        assert passed_config.tensor_split == "60,40"


def test_bitnet_engine_cli_rpc_cmd_injection(tmp_path):
    dummy_model = tmp_path / "dummy.gguf"
    dummy_model.write_text("dummy")

    config = BitNetConfig(
        model_path=str(dummy_model),
        rpc="192.168.0.220:50052,192.168.0.253:50052",
        tensor_split="40,30,30",
    )
    engine = BitNetEngine(config=config)
    engine.count_tokens = MagicMock(return_value=2)

    with patch("termux_bitnet.engine.verify_rpc_cluster_nodes"), \
         patch("termux_bitnet.engine.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0
        mock_proc.stdout.read.side_effect = ["Prompt: Hello distributed BitNet\n", ""]
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        tokens = list(engine._generate_stream_cli("Prompt:", 10, "/dummy/llama-cli"))
        assert len(tokens) >= 1

        assert mock_popen.call_count >= 1
        cmd_args = mock_popen.call_args[0][0]
        assert "--rpc" in cmd_args
        rpc_idx = cmd_args.index("--rpc")
        assert cmd_args[rpc_idx + 1] == "192.168.0.220:50052,192.168.0.253:50052"

        assert "--tensor-split" in cmd_args
        ts_idx = cmd_args.index("--tensor-split")
        assert cmd_args[ts_idx + 1] == "40,30,30"
