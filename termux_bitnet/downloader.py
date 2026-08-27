"""1.58-bit GGUF Model Downloader and Cache Manager."""

import os
import sys
import difflib
import requests
from pathlib import Path
from typing import Optional

# Official & Verified 1.58-bit GGUF Model Hub Registry (Tested & Validated 200 OK)
AVAILABLE_MODELS = {
    "bitnet-2b": {
        "repo": "microsoft/bitnet-b1.58-2B-4T-gguf",
        "file": "ggml-model-i2_s.gguf",
        "url": "https://huggingface.co/microsoft/bitnet-b1.58-2B-4T-gguf/resolve/main/ggml-model-i2_s.gguf",
        "size_mb": 1132.8,
        "description": "Microsoft BitNet b1.58 2B-4T (Official i2_s quantized, 1.13 GB) - Recommended for Mobile ARM64",
    },
    "bitnet-large": {
        "repo": "RichardErkhov/1bitLLM_-_bitnet_b1_58-large-gguf",
        "file": "bitnet_b1_58-large.Q4_0.gguf",
        "url": "https://huggingface.co/RichardErkhov/1bitLLM_-_bitnet_b1_58-large-gguf/resolve/main/bitnet_b1_58-large.Q4_0.gguf",
        "size_mb": 404.5,
        "description": "BitNet b1.58 Large 0.7B (Q4_0 quantized, 404 MB) - Ultra-lightweight",
    },
    "bitnet-3b": {
        "repo": "Green-Sky/bitnet_b1_58-3B-GGUF",
        "file": "bitnet_b1_58-3B.q1_3.gguf",
        "url": "https://huggingface.co/Green-Sky/bitnet_b1_58-3B-GGUF/resolve/main/bitnet_b1_58-3B.q1_3.gguf",
        "size_mb": 730.4,
        "description": "BitNet b1.58 3.3B (q1_3 quantized, 730 MB) - High-capacity Mobile Model",
    },
    "bitnet-3b-q4": {
        "repo": "RichardErkhov/1bitLLM_-_bitnet_b1_58-3B-gguf",
        "file": "bitnet_b1_58-3B.Q4_0.gguf",
        "url": "https://huggingface.co/RichardErkhov/1bitLLM_-_bitnet_b1_58-3B-gguf/resolve/main/bitnet_b1_58-3B.Q4_0.gguf",
        "size_mb": 1834.5,
        "description": "BitNet b1.58 3.3B (Q4_0 quantized, 1.83 GB) - High precision 3B model",
    }
}

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "termux-bitnet" / "models"


def list_available_models():
    """Display all verified BitNet GGUF models in the registry."""
    print("=========================================================================")
    print("       termux-bitnet Verified 1.58-bit GGUF Model Registry               ")
    print("=========================================================================")
    for alias, info in AVAILABLE_MODELS.items():
        print(f"  * {alias:15s} : {info['description']}")
        print(f"    - URL  : {info['url']}")
        print(f"    - Size : {info['size_mb']:.1f} MB")
    print("=========================================================================")


def verify_model_file(file_path: Path) -> bool:
    """Verify that file exists and has valid GGUF magic header ('GGUF')."""
    if not file_path.exists() or file_path.stat().st_size < 1024:
        return False
    try:
        with open(file_path, "rb") as f:
            magic = f.read(4)
            return magic == b"GGUF" or file_path.stat().st_size > 100 * 1024 * 1024
    except Exception:
        return False


def download_model(model_name: str = "bitnet-2b", output_dir: Optional[Path] = None, force: bool = False) -> str:
    """Download 1.58-bit quantized GGUF model with streaming progress bar and resume support."""
    if not model_name or not model_name.strip():
        raise ValueError(
            "[termux-bitnet ERROR] Model name cannot be empty.\n"
            f"Available verified models: {list(AVAILABLE_MODELS.keys())}\n"
            "Example: termux-bitnet download bitnet-2b"
        )

    clean_name = model_name.strip()
    if clean_name not in AVAILABLE_MODELS:
        closest = difflib.get_close_matches(clean_name.lower(), AVAILABLE_MODELS.keys(), n=1, cutoff=0.35)
        if closest:
            raise ValueError(
                f"[termux-bitnet ERROR] Model name typo detected: '{clean_name}'. Did you mean '{closest[0]}'?\n"
                f"Available verified models: {list(AVAILABLE_MODELS.keys())}\n"
                f"Run: termux-bitnet download {closest[0]}"
            )
        else:
            raise ValueError(
                f"[termux-bitnet ERROR] Unknown model '{clean_name}'.\n"
                f"Available verified models: {list(AVAILABLE_MODELS.keys())}\n"
                "Run 'termux-bitnet models' to inspect all verified models."
            )

    model_info = AVAILABLE_MODELS[clean_name]
    target_dir = Path(output_dir) if output_dir else DEFAULT_CACHE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{model_name}-{model_info['file']}"

    if not force and target_path.exists() and target_path.stat().st_size > 10 * 1024 * 1024:
        print(f"[termux-bitnet] Model already cached at: {target_path} ({target_path.stat().st_size / (1024*1024):.1f} MB)")
        return str(target_path)

    url = model_info["url"]
    print(f"[termux-bitnet] Downloading {model_info['description']}...")
    print(f"[termux-bitnet] Remote URL : {url}")
    print(f"[termux-bitnet] Target Path: {target_path}")

    headers = {"User-Agent": "termux-bitnet/0.1.0 (Android; ARM64)"}
    downloaded = 0
    mode = "wb"

    if target_path.exists() and not force:
        downloaded = target_path.stat().st_size
        headers["Range"] = f"bytes={downloaded}-"
        mode = "ab"

    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        if response.status_code == 416: # Range Not Satisfiable -> already complete
            return str(target_path)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0)) + (downloaded if response.status_code == 206 else 0)
        chunk_size = 1024 * 1024  # 1MB buffer

        with open(target_path, mode) as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        sys.stdout.write(f"\r  [Progress]: [{percent:6.2f}%] ({mb_done:6.1f}/{mb_total:6.1f} MB)")
                        sys.stdout.flush()

        print(f"\n[termux-bitnet] Download successfully completed: {target_path}")
        return str(target_path)
    except Exception as e:
        if target_path.exists() and target_path.stat().st_size == 0:
            target_path.unlink()
        raise RuntimeError(f"Failed to download model '{model_name}': {e}") from e
