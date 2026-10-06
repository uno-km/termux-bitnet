"""
AMEVA Unified Distributed RPC Cluster Orchestration Cold Tests for termux-bitnet.
Strict Protocol: Zero-Silent-Fallback & Fail-Fast Verification.
Component: [BITNET-CLUSTER]
"""

import socket
import sys
import pytest
from unittest.mock import patch, MagicMock

import termux_bitnet as tb
from termux_bitnet.exceptions import (
    ClusterConnectionError,
    ClusterConfigurationError,
)
from termux_bitnet.cluster import (
    parse_cluster_rpc_spec,
    verify_rpc_cluster_nodes,
    verify_rpc_cluster_health,
)
from termux_bitnet.config import BitNetConfig
from termux_bitnet.engine import BitNetEngine
from termux_bitnet.cli import main


def test_parse_cluster_rpc_spec_valid():
    """Verify parsing and normalization of valid RPC specs."""
    servers_str = "192.0.2.11:50052, 192.0.2.12:50052"
    parsed = parse_cluster_rpc_spec(servers_str)
    assert parsed == ["192.0.2.11:50052", "192.0.2.12:50052"]

    servers_list = ["192.0.2.11:50052", "192.0.2.12:50052"]
    parsed2 = parse_cluster_rpc_spec(servers_list)
    assert parsed2 == ["192.0.2.11:50052", "192.0.2.12:50052"]

    assert parse_cluster_rpc_spec(None) == []
    assert parse_cluster_rpc_spec("") == []


def test_parse_cluster_rpc_spec_invalid():
    """Verify invalid RPC formats strictly raise ClusterConfigurationError."""
    with pytest.raises(ClusterConfigurationError):
        parse_cluster_rpc_spec("invalid_host_no_port")

    with pytest.raises(ClusterConfigurationError):
        parse_cluster_rpc_spec("host:not_a_number")

    with pytest.raises(ClusterConfigurationError):
        parse_cluster_rpc_spec("host:999999")  # Port out of range

    with pytest.raises(ClusterConfigurationError):
        parse_cluster_rpc_spec(12345)  # Invalid type


def test_verify_rpc_cluster_nodes_success():
    """Verify pre-flight check succeeds when all RPC nodes accept TCP connection."""
    servers = ["192.0.2.11:50052", "192.0.2.12:50052"]
    with patch("socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__.return_value = MagicMock()
        verify_rpc_cluster_nodes(servers, timeout=1.0)
        assert mock_conn.call_count == 2


def test_verify_rpc_cluster_nodes_fail_fast():
    """Verify Zero-Silent-Fallback: Unreachable node raises ClusterConnectionError immediately."""
    servers = ["192.0.2.11:50052", "192.0.2.12:50052"]

    def fake_connect(addr, timeout=None):
        host, port = addr
        if host == "192.0.2.12":
            raise ConnectionRefusedError("Connection refused by test worker")
        return MagicMock()

    with patch("socket.create_connection", side_effect=fake_connect):
        with pytest.raises(ClusterConnectionError) as exc_info:
            verify_rpc_cluster_nodes(servers, timeout=1.0)
        assert "Zero-Silent-Fallback Violation Prevented" in str(exc_info.value)
        assert "192.0.2.12:50052" in str(exc_info.value)


def test_verify_rpc_cluster_health_reporting():
    """Verify granular diagnostics from verify_rpc_cluster_health."""
    servers = ["192.0.2.11:50052", "192.0.2.12:50052"]

    def fake_connect(addr, timeout=None):
        host, port = addr
        if host == "192.0.2.12":
            raise socket.timeout("Timed out")
        return MagicMock()

    with patch("socket.create_connection", side_effect=fake_connect):
        health = verify_rpc_cluster_health(servers, timeout=1.0)
        assert health["all_healthy"] is False
        assert health["nodes"]["192.0.2.11:50052"]["reachable"] is True
        assert health["nodes"]["192.0.2.12:50052"]["reachable"] is False


def test_bitnet_config_cluster_fields():
    """Verify BitNetConfig correctly synchronizes cluster fields."""
    config = BitNetConfig(
        model_path="dummy.gguf",
        cluster_rpc_servers="192.0.2.11:50052, 192.0.2.12:50052",
        cluster_tensor_split="40,60",
        cluster_split_mode="tensor",
    )
    assert config.cluster_rpc_servers == "192.0.2.11:50052, 192.0.2.12:50052"
    assert config.rpc == "192.0.2.11:50052, 192.0.2.12:50052"
    assert config.cluster_tensor_split == "40,60"
    assert config.tensor_split == "40,60"


def test_bitnet_engine_cluster_args_and_preflight(tmp_path):
    """Verify BitNetEngine runs preflight and injects cluster args."""
    dummy_model = tmp_path / "dummy.gguf"
    dummy_model.write_text("dummy")

    config = BitNetConfig(
        model_path=str(dummy_model),
        cluster_rpc_servers="192.0.2.11:50052,192.0.2.12:50052",
        cluster_tensor_split="50,50",
    )
    engine = BitNetEngine(config=config)
    engine.count_tokens = MagicMock(return_value=2)

    with patch("termux_bitnet.engine.verify_rpc_cluster_nodes") as mock_verify, \
         patch("termux_bitnet.engine.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0
        mock_proc.stdout.read.side_effect = ["Prompt: Output\n", ""]
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        tokens = list(engine._generate_stream_cli("Prompt:", 10, "/dummy/llama-cli"))
        assert mock_verify.called
        assert len(tokens) >= 1

        cmd_args = mock_popen.call_args[0][0]
        assert "--rpc" in cmd_args
        rpc_idx = cmd_args.index("--rpc")
        assert cmd_args[rpc_idx + 1] == "192.0.2.11:50052,192.0.2.12:50052"
        assert "--tensor-split" in cmd_args
        ts_idx = cmd_args.index("--tensor-split")
        assert cmd_args[ts_idx + 1] == "50,50"


def test_cli_cluster_rpc_flag_parsing(tmp_path, monkeypatch):
    """Verify CLI parses --cluster-rpc-servers and --cluster-tensor-split."""
    dummy_model = tmp_path / "dummy.gguf"
    dummy_model.write_text("model_header")

    test_args = [
        "termux-bitnet",
        "run",
        "-m",
        str(dummy_model),
        "-p",
        "Hello Cluster",
        "--cluster-rpc-servers",
        "192.0.2.11:50052,192.0.2.12:50052",
        "--cluster-tensor-split",
        "50,50",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    with patch("termux_bitnet.cli.BitNetEngine") as MockEngine:
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.__exit__.return_value = None
        mock_instance.generate_stream.return_value = ["Output"]
        mock_instance.get_last_metrics.return_value = MagicMock(tokens_per_second=10.0, total_tokens=5, generation_time_s=0.5)
        MockEngine.return_value = mock_instance

        with patch("termux_bitnet.cli.detect_hardware"):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None

        assert MockEngine.call_count == 1
        passed_config = MockEngine.call_args[0][0]
        assert passed_config.cluster_rpc_servers == "192.0.2.11:50052,192.0.2.12:50052"
        assert passed_config.cluster_tensor_split == "50,50"
