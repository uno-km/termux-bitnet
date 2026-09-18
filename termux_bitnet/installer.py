"""Automated Installer and Prebuilt Binary Dispatcher for termux-bitnet."""

import os
import sys
import shutil
import urllib.request
from pathlib import Path

try:
    from . import __version__
except Exception:
    __version__ = "1.4.0"

GITHUB_REPO = "uno-km/termux-bitnet"


def get_candidate_library_urls() -> list[str]:
    """Generate dynamic SSOT candidate URLs with multi-tier fallback."""
    urls = []
    custom_base = os.environ.get("TERMUX_BITNET_RELEASE_BASE", "").strip()
    custom_tag = os.environ.get("TERMUX_BITNET_RELEASE_TAG", "").strip()

    if custom_base:
        base = custom_base.rstrip("/")
        urls.append(f"{base}/libtermux_bitnet.so")
    if custom_tag:
        tag = custom_tag if custom_tag.startswith("v") else f"v{custom_tag}"
        urls.append(f"https://github.com/{GITHUB_REPO}/releases/download/{tag}/libtermux_bitnet.so")

    # Current version SSOT
    current_tag = f"v{__version__}"
    urls.append(f"https://github.com/{GITHUB_REPO}/releases/download/{current_tag}/libtermux_bitnet.so")
    urls.append(f"https://github.com/{GITHUB_REPO}/releases/latest/download/libtermux_bitnet.so")

    return urls


def install_prebuilt_library() -> bool:
    prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
    lib_dir = Path(prefix) / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    target_so = lib_dir / "libtermux_bitnet.so"

    xdg_cache = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    staging_dir = xdg_cache / "termux-bitnet" / ".staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    staging_so = staging_dir / "libtermux_bitnet.so"

    print("=========================================================")
    print(f"  termux-bitnet Pure-CPU Engine Provisioning (v{__version__})")
    print("=========================================================")
    print(f"  Target: {target_so}")

    candidate_urls = get_candidate_library_urls()
    for url in candidate_urls:
        print(f"[*] Downloading pre-built ARM64 binary from: {url}...")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": f"termux-bitnet-installer/{__version__} (Android; ARM64)"}
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
    success = install_prebuilt_library()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
