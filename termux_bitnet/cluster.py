"""
AMEVA Unified Distributed RPC Cluster Orchestration Utility.
Strict Protocol: Zero-Silent-Fallback & Zero-Deception ABI.
Component: [BITNET-CLUSTER]
"""

import socket
import logging
from typing import List, Optional, Union, Dict, Any, Tuple

from termux_bitnet.exceptions import (
    ClusterConnectionError,
    ClusterConfigurationError,
    ClusterLicenseRequiredError,
)

logger = logging.getLogger(__name__)


def check_cluster_license(license_key: Optional[str] = None) -> None:
    """Enforces exclusive AMEVA-Cluster runtime license requirement.
    Fail-Fast: Raises ClusterLicenseRequiredError if ameva_cluster is not installed
    or license verification fails.
    """
    try:
        from ameva_cluster.guard import verify_cluster_license
    except ImportError:
        raise ClusterLicenseRequiredError()

    if not verify_cluster_license(license_key):
        raise ClusterLicenseRequiredError(
            "\n================================================================================\n"
            "[AMEVA-CLUSTER] CLUSTER LICENSE INVALID (E403)\n"
            "================================================================================\n"
            "The provided AMEVA Cluster license token is invalid or expired.\n"
            "Please check your AMEVA_CLUSTER_LICENSE environment variable.\n"
            "================================================================================"
        )


def setup_cluster_guard_tunnels(
    servers: List[str],
    secret_key: Optional[str] = None
) -> Tuple[List[str], List[Any]]:
    """Establishes authenticated loopback MasterTunnels for remote RPC nodes.

    Transforms remote endpoints into local authenticated tunnel endpoints (127.0.0.1:PORT)
    which transparently inject the AMEVA Guard cryptographic handshake.

    Returns:
        Tuple of (tunnel_server_endpoints, active_tunnel_instances)
    """
    if not servers:
        return [], []

    try:
        from ameva_cluster.guard import MasterTunnel
    except ImportError:
        raise ClusterLicenseRequiredError()

    tunnel_endpoints: List[str] = []
    active_tunnels: List[Any] = []

    for endpoint in servers:
        host, port_str = endpoint.split(":")
        port = int(port_str)

        # Local loopback addresses do not require an extra proxy hop
        if host in ("127.0.0.1", "localhost", "::1"):
            tunnel_endpoints.append(endpoint)
            continue

        tunnel = MasterTunnel(remote_host=host, remote_port=port, secret_key=secret_key)
        tunnel.start()
        active_tunnels.append(tunnel)
        local_ep = f"127.0.0.1:{tunnel.local_port}"
        tunnel_endpoints.append(local_ep)
        logger.info(
            "[AMEVA-BITNET-CLUSTER] Authenticated MasterTunnel active: %s -> %s",
            local_ep,
            endpoint,
        )

    return tunnel_endpoints, active_tunnels



def parse_cluster_rpc_spec(rpc_input: Optional[Union[str, List[str]]]) -> List[str]:
    """Parse and normalize distributed RPC server endpoints.

    Supports comma-separated strings or list of host:port strings.
    Validates port ranges and host syntax strictly without silent normalization.
    """
    if not rpc_input:
        return []

    if isinstance(rpc_input, str):
        raw_servers = [s.strip() for s in rpc_input.split(",") if s.strip()]
    elif isinstance(rpc_input, (list, tuple)):
        raw_servers = [str(s).strip() for s in rpc_input if str(s).strip()]
    else:
        raise ClusterConfigurationError(
            f"Invalid cluster_rpc_servers specification type: {type(rpc_input).__name__}. "
            f"Expected comma-separated string or list of endpoints."
        )

    parsed_servers: List[str] = []
    for entry in raw_servers:
        if ":" not in entry:
            raise ClusterConfigurationError(
                f"Invalid RPC endpoint format '{entry}'. Expected 'host:port' format (e.g. '192.0.2.11:50052')."
            )
        parts = entry.split(":")
        if len(parts) != 2:
            raise ClusterConfigurationError(
                f"Malformed RPC endpoint '{entry}'. Exactly one colon separator required."
            )
        host, port_str = parts[0].strip(), parts[1].strip()
        if not host:
            raise ClusterConfigurationError(f"Empty hostname/IP in RPC endpoint '{entry}'.")
        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            raise ClusterConfigurationError(
                f"Invalid port number '{port_str}' in RPC endpoint '{entry}'. Must be integer 1..65535."
            )
        parsed_servers.append(f"{host}:{port}")

    return parsed_servers


def ensure_wakelock() -> bool:
    """Acquires Termux system-level wakelock to prevent Android kernel Doze deep-sleep."""
    wakelock_bin = "/data/data/com.termux/files/usr/bin/termux-wake-lock"
    import os
    import subprocess
    if os.path.exists(wakelock_bin):
        try:
            res = subprocess.run([wakelock_bin], capture_output=True, timeout=2.0)
            if res.returncode == 0:
                logger.info("[AMEVA-BITNET-CLUSTER] Termux WakeLock acquired successfully.")
                return True
        except Exception as exc:
            logger.warning("[AMEVA-BITNET-CLUSTER] Failed to acquire termux-wake-lock: %s", exc)
    return False


def resolve_auto_tensor_split(
    rpc_spec: Optional[Union[str, List[str]]],
    tensor_split: Optional[str] = None,
    min_guardband_mb: int = 400
) -> Tuple[List[str], Optional[str]]:
    """Automatically compute optimal tensor split when tensor_split == 'auto'.
    Preserves explicit tensor_split specifications without alteration.
    """
    servers = parse_cluster_rpc_spec(rpc_spec)
    if not servers:
        return [], tensor_split

    if tensor_split and str(tensor_split).strip().lower() == "auto":
        try:
            from termux_ai_orchestrator.auto_split import resolve_auto_tensor_split as orch_resolve
            return orch_resolve(servers, min_guardband_mb=min_guardband_mb)
        except Exception as exc:
            logger.warning("[AMEVA-BITNET-CLUSTER] Auto-TS fallback to equal distribution: %s", exc)
            n_nodes = len(servers) + 1
            equal_pct = int(100 // n_nodes)
            remainder = 100 - (equal_pct * n_nodes)
            splits = [equal_pct + remainder] + [equal_pct] * len(servers)
            return servers, ",".join(str(s) for s in splits)

    return servers, tensor_split


def verify_rpc_cluster_nodes(servers: List[str], timeout: float = 3.0) -> None:
    """Strictly verify TCP reachability of each RPC server prior to initiating inference graph.

    Zero-Silent-Fallback: If ANY specified RPC worker is unreachable, this function raises
    ClusterConnectionError immediately to prevent silent local CPU/GPU fallback degradation.
    """
    if not servers:
        return

    failed_nodes = []
    for endpoint in servers:
        host, port_str = endpoint.split(":")
        port = int(port_str)
        try:
            with socket.create_connection((host, port), timeout=timeout):
                logger.info("[AMEVA-BITNET-CLUSTER] RPC Worker verified reachable: %s", endpoint)
        except (socket.timeout, ConnectionRefusedError, OSError) as exc:
            failed_nodes.append((endpoint, str(exc)))

    if failed_nodes:
        err_details = "\n".join([f"  - {ep}: {err}" for ep, err in failed_nodes])
        raise ClusterConnectionError(
            f"Distributed RPC Cluster Pre-Flight Check FAILED for {len(failed_nodes)}/{len(servers)} worker(s):\n"
            f"{err_details}\n"
            f"Zero-Silent-Fallback Violation Prevented: Inference terminated to avoid silent execution degradation."
        )


def verify_rpc_cluster_health(servers: List[str], timeout: float = 3.0) -> Dict[str, Any]:
    """Inspect and report cluster connectivity status without throwing, returning granular diagnostics."""
    status: Dict[str, Any] = {"all_healthy": True, "nodes": {}}
    for endpoint in servers:
        host, port_str = endpoint.split(":")
        port = int(port_str)
        try:
            with socket.create_connection((host, port), timeout=timeout):
                status["nodes"][endpoint] = {"reachable": True, "error": None}
        except Exception as exc:
            status["all_healthy"] = False
            status["nodes"][endpoint] = {"reachable": False, "error": str(exc)}
    return status
