import os
import sys
import difflib
import hashlib
import logging
from pathlib import Path
from typing import Optional, Union
import requests

logger = logging.getLogger(__name__)

# Verified 1.58-bit BitNet GGUF Model Registry
AVAILABLE_MODELS = {
    "bitnet-2b": {
        "repo": "microsoft/bitnet-b1.58-2B-4T-gguf",
        "file": "bitnet-2b-ggml-model-i2_s.gguf",
        "url": "https://huggingface.co/microsoft/bitnet-b1.58-2B-4T-gguf/resolve/main/ggml-model-i2_s.gguf",
        "size_mb": 1132.8,
        "description": "Microsoft BitNet b1.58 2B (i2_s quantized, 1.13 GB) - Official Microsoft 2B Default",
    },
    "bitnet-large": {
        "repo": "RichardErkhov/1bitLLM_-_bitnet_b1_58-large-gguf",
        "file": "bitnet_b1_58-large.Q4_0.gguf",
        "url": "https://huggingface.co/RichardErkhov/1bitLLM_-_bitnet_b1_58-large-gguf/resolve/main/bitnet_b1_58-large.Q4_0.gguf",
        "size_mb": 404.5,
        "description": "BitNet b1.58 Large 0.7B (Q4_0 quantized, 405 MB) - High Quality Lightweight Model",
    },
    "bitnet-3b": {
        "repo": "RichardErkhov/1bitLLM_-_bitnet_b1_58-3B-gguf",
        "file": "bitnet_b1_58-3B.Q4_0.gguf",
        "url": "https://huggingface.co/RichardErkhov/1bitLLM_-_bitnet_b1_58-3B-gguf/resolve/main/bitnet_b1_58-3B.Q4_0.gguf",
        "size_mb": 1834.5,
        "description": "BitNet b1.58 3.3B (Q4_0 quantized, 1.83 GB) - High precision 3B model",
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


def list_models():
    """Return verified BitNet GGUF models in standard dictionary format."""
    return [{"id": k, **v} for k, v in AVAILABLE_MODELS.items()]



def verify_gguf_magic_header(file_path: Union[str, Path]) -> bool:
    """Verify that file exists and has valid GGUF magic header ('GGUF')."""
    p = Path(file_path)
    if not p.exists() or p.stat().st_size < 1024:
        return False
    try:
        with open(p, "rb") as f:
            magic = f.read(4)
            return magic == b"GGUF" or p.stat().st_size > 100 * 1024 * 1024
    except OSError as e:
        logger.debug("Failed to read GGUF header for '%s': %s", p, e)
        return False


# Backward compatibility alias
verify_model_file = verify_gguf_magic_header


def verify_file_sha256(file_path: Union[str, Path], expected_sha256: str, block_size: int = 65536) -> bool:
    """Standard Unified SHA-256 Checksum Verifier for termux-bitnet."""
    p = Path(file_path)
    if not p.is_file() or not expected_sha256:
        return False
    hasher = hashlib.sha256()
    try:
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(block_size), b""):
                hasher.update(chunk)
        return hasher.hexdigest().lower() == expected_sha256.strip().lower()
    except OSError as e:
        logger.debug("Failed to compute SHA-256 for '%s': %s", p, e)
        return False



def download_model(model_name: str = "bitnet-2b", output_dir: Optional[Path] = None, force: bool = False) -> Path:
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
    target_path = target_dir / model_info["file"]
    part_path = target_path.with_suffix(target_path.suffix + ".part")

    if not force and target_path.exists() and verify_model_file(target_path):
        sz_mb = target_path.stat().st_size / (1024 * 1024)
        print(f"[termux-bitnet] Valid model already cached at: {target_path} ({sz_mb:.1f} MB)")
        return target_path

    url = model_info["url"]
    print(f"[termux-bitnet] Downloading {model_info['description']}...")
    print(f"[termux-bitnet] Remote URL : {url}")
    try:
        from termux_bitnet import __version__
        ua_version = __version__
    except Exception:
        ua_version = "1.4.0"
    headers = {"User-Agent": f"termux-bitnet/{ua_version} (Android; ARM64)"}
    downloaded = 0
    mode = "wb"

    if part_path.exists() and not force:
        downloaded = part_path.stat().st_size
        headers["Range"] = f"bytes={downloaded}-"
        mode = "ab"

    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        if response.status_code == 416:  # Range Not Satisfiable -> already complete
            if verify_model_file(part_path):
                os.replace(part_path, target_path)
                return target_path
            else:
                downloaded = 0
                mode = "wb"
                headers.pop("Range", None)
                response = requests.get(url, headers={"User-Agent": f"termux-bitnet/{ua_version} (Android; ARM64)"}, stream=True, timeout=30)

        if response.status_code not in (200, 206):
            err_snip = response.text[:200].strip()
            raise RuntimeError(
                f"[ERROR: AMEVA-BITNET-E005] Failed to download model from '{url}'. "
                f"HTTP {response.status_code}: {err_snip}"
            )

        if response.status_code == 206:
            mode = "ab"
            total_size = int(response.headers.get("content-length", 0)) + downloaded
        else:
            mode = "wb"
            downloaded = 0
            total_size = int(response.headers.get("content-length", 0))

        chunk_size = 1024 * 1024  # 1MB buffer

        with open(part_path, mode) as f:
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

        # Fail-fast verification of downloaded GGUF file
        if not verify_model_file(part_path):
            if part_path.exists():
                part_path.unlink()
            raise RuntimeError(
                f"[ERROR: AMEVA-BITNET-E006] Downloaded model '{part_path}' is corrupted or not a valid GGUF model."
            )

        os.replace(part_path, target_path)
        print(f"\n[termux-bitnet] Download successfully verified and completed: {target_path}")
        return target_path
    except Exception as e:
        if part_path.exists() and not verify_model_file(part_path):
            part_path.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to download model '{model_name}': {e}") from e



def resolve_model_path(model_name: str = "bitnet-2b") -> Path:
    """Standard Unified Model Path Resolver for termux-bitnet."""
    from .hardware import get_unified_model_search_dirs
    clean = model_name.lower().strip()
    f_info = AVAILABLE_MODELS.get(clean)
    fname = f_info["file"] if f_info else model_name

    if Path(model_name).is_file():
        return Path(model_name).resolve()

    search_dirs = get_unified_model_search_dirs("bitnet")
    for d in search_dirs:
        for cand in [d / fname, d / model_name, d / f"{model_name}.gguf"]:
            if cand.is_file() and verify_model_file(cand):
                return cand.resolve()

    return DEFAULT_CACHE_DIR / fname
