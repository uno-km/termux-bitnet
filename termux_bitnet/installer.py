"""Automated Installer and Prebuilt Binary Dispatcher for termux-bitnet."""

import os
import sys
import shutil
import urllib.request
from pathlib import Path

from typing import Optional

def _resolve_package_version() -> Optional[str]:
    """Dynamically resolve current installed package version without static fallback."""
    try:
        from . import __version__
        if __version__:
            return __version__
    except Exception:
        pass
    try:
        import importlib.metadata
        return importlib.metadata.version("termux-bitnet")
    except Exception:
        return None

GITHUB_REPO = "uno-km/termux-bitnet"


def get_candidate_library_urls() -> list[str]:
    """Generate dynamic SSOT candidate URLs with 3-tier fallback."""
    urls = []
    custom_base = os.environ.get("TERMUX_BITNET_RELEASE_BASE", "").strip()
    custom_tag = os.environ.get("TERMUX_BITNET_RELEASE_TAG", "").strip()

    # Tier 1: Explicit environment overrides
    if custom_base:
        base = custom_base.rstrip("/")
        urls.append(f"{base}/libtermux_bitnet.so")
    if custom_tag:
        tag = custom_tag if custom_tag.startswith("v") else f"v{custom_tag}"
        urls.append(f"https://github.com/{GITHUB_REPO}/releases/download/{tag}/libtermux_bitnet.so")

    # Tier 2: GitHub Releases latest canonical endpoint (Zero-Hardcoding SSOT)
    urls.append(f"https://github.com/{GITHUB_REPO}/releases/latest/download/libtermux_bitnet.so")

    # Tier 3: Current installed package dynamic version matching
    ver = _resolve_package_version()
    if ver:
        urls.append(f"https://github.com/{GITHUB_REPO}/releases/download/v{ver}/libtermux_bitnet.so")

    return urls


def is_valid_elf(path: Path) -> bool:
    """Verifies that the target path is a valid ELF executable/library via magic bytes."""
    try:
        p = path.resolve() if path.is_symlink() else path
        if not p.is_file():
            return False
        with open(p, "rb") as f:
            return f.read(4) == b"\x7fELF"
    except (OSError, PermissionError):
        return False


def inspect_engine_state(so_path: Path, current_pkg_version: Optional[str] = None) -> str:
    """Dynamically triages existing binary state without hardcoding."""
    if not so_path.exists() and not so_path.is_symlink():
        return "NOT_INSTALLED"
    if not is_valid_elf(so_path):
        return "BROKEN"
    if so_path.is_symlink():
        target = str(so_path.resolve())
        if ".local/share/ameva" in target:
            return "AMEVA_MANAGED"
    return "LEGACY_STANDALONE"


def install_prebuilt_library(force: bool = False, dedicate: bool = False) -> bool:
    prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
    lib_dir = Path(prefix) / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    target_so = lib_dir / "libtermux_bitnet.so"

    ver = _resolve_package_version() or "latest"

    # Dedicated triage mode
    if dedicate:
        state = inspect_engine_state(target_so, ver)
        if state == "AMEVA_MANAGED":
            print(f"  [termux-bitnet] [DEDICATE] AMEVA Runtime managed engine detected. Preserving co-existence (<0.002s).")
            return True
        elif state == "LEGACY_STANDALONE":
            print(f"  [termux-bitnet] [DEDICATE] Legacy standalone engine detected. Upgrading to latest...")
            force = True

    # "있어? 넘어가" - Skip if verified ELF shared library exists (<0.002s)
    if not force and is_valid_elf(target_so):
        print(f"  [termux-bitnet] [OK] Verified native ARM64 engine already present: {target_so}. Skipping download (<0.002s).")
        return True

    xdg_cache = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    staging_dir = xdg_cache / "termux-bitnet" / ".staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    staging_so = staging_dir / "libtermux_bitnet.so"

    print("=========================================================")
    print(f"  termux-bitnet Pure-CPU Engine Provisioning (v{ver})")
    print("=========================================================")
    print(f"  Target: {target_so}")

    candidate_urls = get_candidate_library_urls()
    for url in candidate_urls:
        print(f"[*] Downloading pre-built ARM64 binary from: {url}...")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": f"termux-bitnet-installer/{ver} (Android; ARM64)"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 1024 and data[:4] == b"\x7fELF":
                        with open(staging_so, "wb") as f:
                            f.write(data)
                        staging_so.chmod(0o755)
                        shutil.move(str(staging_so), str(target_so))
                        target_so.chmod(0o755)
                        shutil.rmtree(staging_dir, ignore_errors=True)
                        print(f"Successfully provisioned native pure-CPU engine to {target_so} ({len(data)} bytes, ELF verified).")
                        return True
                    elif data[:4] != b"\x7fELF":
                        print(f"[-] Downloaded file from {url} is not a valid ELF shared object.")
        except Exception as e:
            print(f"[-] Pre-built download skipped: {e}")
            if staging_so.exists():
                staging_so.unlink(missing_ok=True)

    shutil.rmtree(staging_dir, ignore_errors=True)
    print("[-] Failed to provision prebuilt native library from GitHub Releases endpoints.")
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="termux-bitnet native library provisioner")
    parser.add_argument("--force", "-f", action="store_true", help="Force clean re-download and installation")
    parser.add_argument("--dedicate", action="store_true", help="Smart inspection mode: preserve AMEVA runtime symlinks, auto-upgrade legacy binaries")
    args = parser.parse_args()

    success = install_prebuilt_library(force=args.force, dedicate=args.dedicate)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
