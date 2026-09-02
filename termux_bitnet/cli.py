"""Command Line Interface for termux-bitnet (Strict Fail-Fast Protocol)."""

import os
import sys
import argparse
import time
from pathlib import Path

from termux_bitnet import __version__
from termux_bitnet.config import BitNetConfig
from termux_bitnet.engine import BitNetEngine
from termux_bitnet.hardware import print_hardware_summary, detect_hardware
from termux_bitnet.downloader import download_model, AVAILABLE_MODELS
from termux_bitnet.server import run_server


def print_catalog_help():
    print("\n[Available Official BitNet Models]", file=sys.stderr)
    print("  1. bitnet-2b    : Microsoft BitNet 2B-4T (1.13 GB, i2_s)", file=sys.stderr)
    print("     Command      : termux-bitnet download bitnet-2b", file=sys.stderr)
    print("  2. bitnet-large : BitNet b1.58 Large 0.7B (700 MB, i2_s)", file=sys.stderr)
    print("     Command      : termux-bitnet download bitnet-large", file=sys.stderr)
    print("  3. bitnet-3b    : BitNet b1.58 3B (2.4 GB, i2_s)", file=sys.stderr)
    print("     Command      : termux-bitnet download bitnet-3b", file=sys.stderr)
    print("  4. bitnet-3b-q4 : BitNet b1.58 3B Q4_K_M (1.8 GB)", file=sys.stderr)
    print("     Command      : termux-bitnet download bitnet-3b-q4", file=sys.stderr)
    print("\nOfficial Hugging Face Repositories:", file=sys.stderr)
    print("  - https://huggingface.co/1bitLLM/bitnet_b1_58-large-GGUF", file=sys.stderr)
    print("  - https://huggingface.co/1bitLLM/bitnet_b1_58-3B-GGUF", file=sys.stderr)


def validate_model_path_or_exit(model_path: str = None) -> str:
    if model_path and model_path.strip():
        expanded = os.path.abspath(os.path.expanduser(model_path))
        if os.path.isfile(expanded):
            return expanded
        print(f"[termux-bitnet ERROR] Model file not found at path: '{expanded}'", file=sys.stderr)
        print_catalog_help()
        sys.exit(10)

    # Auto-discover in cache directory
    cache_dir = Path.home() / ".cache" / "termux-bitnet" / "models"
    if cache_dir.exists():
        for preferred in ["bitnet_b1_58-large.Q4_0.gguf", "bitnet-large.gguf", "bitnet-2b-ggml-model-i2_s.gguf"]:
            p = cache_dir / preferred
            if p.exists() and p.is_file():
                return str(p)
        ggufs = list(cache_dir.glob("*.gguf"))
        if ggufs:
            return str(ggufs[0])

    print("[termux-bitnet ERROR] No model file specified and no cached models found. Use -m or run: termux-bitnet download", file=sys.stderr)
    print_catalog_help()
    sys.exit(10)


def cmd_info(args):
    print_hardware_summary()


def cmd_download(args):
    download_model(args.model_name, output_dir=args.output_dir)


def cmd_run(args):
    # 1. Validate Prompt
    prompt_text = args.prompt
    if args.file:
        file_path = os.path.abspath(os.path.expanduser(args.file))
        if not os.path.isfile(file_path):
            print(f"[termux-bitnet ERROR] Prompt file not found: '{file_path}'", file=sys.stderr)
            sys.exit(2)
        with open(file_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()

    if not prompt_text or not prompt_text.strip():
        print("[termux-bitnet ERROR] No input prompt specified. Use -p / --prompt \"<text>\" or -f / --file <path>.", file=sys.stderr)
        print("Example:\n  termux-bitnet run -m ~/.cache/termux-bitnet/models/bitnet-2b.gguf -p \"Explain 1-bit LLM:\"", file=sys.stderr)
        sys.exit(2)

    # 2. Validate Model
    resolved_model = validate_model_path_or_exit(args.model)

    config = BitNetConfig(
        model_path=resolved_model,
        system_prompt=args.system_prompt or "",
        stop_tokens=args.stop or "",
        device=getattr(args, "device", "auto"),
        n_threads=args.threads,
        n_ctx=args.ctx_size,
        n_batch=args.batch_size,
        n_ubatch=args.ubatch_size,
        n_predict=args.n_predict,
        top_k=args.top_k,
        repeat_last_n=args.repeat_last_n,
        n_gpu_layers=args.n_gpu_layers,
        seed=args.seed,
        temperature=args.temp,
        top_p=args.top_p,
        min_p=args.min_p,
        typical_p=args.typical,
        repeat_penalty=args.repeat_penalty,
        frequency_penalty=args.freq_penalty,
        presence_penalty=args.presence_penalty,
        flash_attn=args.flash_attn,
        verbose=args.verbose,
    )

    print("=========================================================")
    print(f"  termux-bitnet CLI (v{__version__})")
    print(f"  Model:  {resolved_model}")
    print(f"  Prompt: {prompt_text[:80]}...")
    print("=========================================================")
    print("[Response]: ", end="", flush=True)

    try:
        with BitNetEngine(config) as engine:
            t0 = time.time()
            for token in engine.generate_stream(prompt_text, max_tokens=args.n_predict):
                sys.stdout.write(token)
                sys.stdout.flush()
            t1 = time.time()

            metrics = engine.get_last_metrics()
            print("\n\n---------------------------------------------------------")
            print(f"  Inference Speed: {metrics.tokens_per_second:.2f} tokens/sec")
            print(f"  Total Duration:  {(t1 - t0)*1000:.1f} ms")
            print("---------------------------------------------------------")
    except Exception as e:
        print(f"\n[termux-bitnet ERROR] Execution failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_chat(args):
    resolved_model = validate_model_path_or_exit(args.model)

    config = BitNetConfig(
        model_path=resolved_model,
        system_prompt=args.system_prompt or "",
        stop_tokens=args.stop or "",
        n_threads=args.threads,
        n_ctx=args.ctx_size,
        temperature=args.temp,
        top_p=args.top_p,
        top_k=args.top_k,
        repeat_penalty=args.repeat_penalty,
    )

    print("=========================================================")
    print(f"  termux-bitnet Interactive Chat (v{__version__})")
    print(f"  Model: {resolved_model}")
    print("  Type 'exit' or 'quit' to end session.")
    print("=========================================================")

    try:
        with BitNetEngine(config) as engine:
            while True:
                try:
                    user_input = input("\nUser > ").strip()
                    if not user_input:
                        continue
                    if user_input.lower() in ("exit", "quit", "q"):
                        print("Exiting chat session.")
                        break

                    print("Assistant > ", end="", flush=True)
                    for chunk in engine.generate_stream(user_input, max_tokens=args.n_predict):
                        sys.stdout.write(chunk)
                        sys.stdout.flush()
                    print()
                except KeyboardInterrupt:
                    print("\nSession interrupted.")
                    break
    except Exception as e:
        print(f"[termux-bitnet ERROR] Chat initialization failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_serve(args):
    resolved_model = validate_model_path_or_exit(args.model)
    run_server(host=args.host, port=args.port, model_path=resolved_model)


def cmd_benchmark(args):
    resolved_model = validate_model_path_or_exit(args.model)

    print("=========================================================")
    print("        termux-bitnet Comprehensive Benchmark            ")
    print(f"  Model: {resolved_model}")
    print("=========================================================")
    print_hardware_summary()

    prompts = [
        ("Coding (Palindrome)", "Write a Python function to check if a string is palindrome ignoring spaces."),
        ("Logic (Harmonic Mean)", "A train goes City A to B at 60 mph, returns at 40 mph. What is average speed?"),
        ("Psychology (CBT Analysis)", "Analyze: 'I made a mistake, so I am a total failure and will lose my job.'"),
    ]

    config = BitNetConfig(model_path=resolved_model, n_threads=args.threads)
    try:
        with BitNetEngine(config) as engine:
            for title, p in prompts:
                print(f"\n[Running Benchmark: {title}]")
                t0 = time.time()
                resp = engine.generate(p, max_tokens=100)
                t1 = time.time()
                dur = t1 - t0
                tps = len(resp.split()) / max(dur, 0.001)
                print(f"  Result Length: {len(resp)} chars")
                print(f"  Elapsed Time:  {dur:.2f} sec")
                print(f"  Estimated TPS: {tps:.2f} tokens/sec")
        print("\nBenchmark successfully completed.")
    except Exception as e:
        print(f"[termux-bitnet ERROR] Benchmark failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="termux-bitnet",
        description="High-performance 1.58-bit BitNet Inference SDK & CLI for Android Termux / ARM64."
    )
    parser.add_argument("-v", "--version", action="version", version=f"termux-bitnet {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # install
    p_inst = subparsers.add_parser("install", help="1-Click installer and prebuilt engine dispatcher")
    p_inst.set_defaults(func=lambda args: __import__("termux_bitnet.installer", fromlist=["main"]).main())

    # info
    p_info = subparsers.add_parser("info", help="Inspect local CPU SIMD/DotProd capabilities")
    p_info.set_defaults(func=cmd_info)

    # download
    p_dl = subparsers.add_parser("download", help="Download 1.58-bit GGUF model")
    p_dl.add_argument("model_name", choices=list(AVAILABLE_MODELS.keys()), default="bitnet-2b", nargs="?", help="Model alias to download")
    p_dl.add_argument("-o", "--output-dir", default=None, help="Target download directory")
    p_dl.add_argument("--force", action="store_true", help="Force re-download even if cached")
    p_dl.set_defaults(func=cmd_download)

    # run
    p_run = subparsers.add_parser("run", help="Run single prompt inference (Strict Validation)")
    p_run.add_argument("-m", "--model", default=None, help="Path to GGUF model binary (default: auto-discover cached model)")
    p_run.add_argument("-p", "--prompt", default=None, help="Input prompt text")
    p_run.add_argument("-f", "--file", help="Path to prompt text file")
    p_run.add_argument("-d", "--device", default="auto", choices=["auto", "gpu", "vulkan", "cpu"], help="Hardware acceleration backend (default: auto)")
    p_run.add_argument("-t", "--threads", type=int, default=8, help="Worker threads (default: 8)")
    p_run.add_argument("-c", "--ctx-size", type=int, default=2048, help="Context size (default: 2048)")
    p_run.add_argument("-b", "--batch-size", type=int, default=512, help="Batch size (default: 512)")
    p_run.add_argument("-ub", "--ubatch-size", type=int, default=512, help="Micro-batch size (default: 512)")
    p_run.add_argument("-n", "--n-predict", type=int, default=128, help="Max tokens to generate")
    p_run.add_argument("--temp", type=float, default=0.7, help="Softmax temperature (default: 0.7)")
    p_run.add_argument("--top-p", type=float, default=0.95, help="Top-P threshold (default: 0.95)")
    p_run.add_argument("--top-k", type=int, default=40, help="Top-K cutoff (default: 40)")
    p_run.add_argument("--min-p", type=float, default=0.05, help="Min-P cutoff (default: 0.05)")
    p_run.add_argument("--typical", type=float, default=1.0, help="Locally typical sampling (default: 1.0)")
    p_run.add_argument("--repeat-penalty", type=float, default=1.15, help="Repetition penalty (default: 1.15)")
    p_run.add_argument("--repeat-last-n", type=int, default=64, help="Repetition penalty window (default: 64)")
    p_run.add_argument("--freq-penalty", type=float, default=0.0, help="Frequency penalty (default: 0.0)")
    p_run.add_argument("--presence-penalty", type=float, default=0.0, help="Presence penalty (default: 0.0)")
    p_run.add_argument("-s", "--seed", type=int, default=0, help="RNG seed (0 for random)")
    p_run.add_argument("-ngl", "--n-gpu-layers", type=int, default=0, help="GPU/NPU offload layers (default: 0)")
    p_run.add_argument("-fa", "--flash-attn", action="store_true", help="Enable Flash Attention")
    p_run.add_argument("--system-prompt", help="System prompt prefix")
    p_run.add_argument("-r", "--stop", help="Comma-separated stop tokens")
    p_run.add_argument("--verbose", action="store_true", help="Enable verbose logs")
    p_run.set_defaults(func=cmd_run)

    # chat
    p_chat = subparsers.add_parser("chat", help="Start interactive chat REPL")
    p_chat.add_argument("-m", "--model", default=None, help="Path to GGUF model binary (default: auto-discover cached model)")
    p_chat.add_argument("-d", "--device", default="auto", choices=["auto", "gpu", "vulkan", "cpu"], help="Hardware acceleration backend")
    p_chat.add_argument("-t", "--threads", type=int, default=8, help="Worker threads (default: 8)")
    p_chat.add_argument("-c", "--ctx-size", type=int, default=2048, help="Context size")
    p_chat.add_argument("-n", "--n-predict", type=int, default=256, help="Max tokens per turn")
    p_chat.add_argument("--temp", type=float, default=0.7, help="Temperature")
    p_chat.add_argument("--top-p", type=float, default=0.95, help="Top-P threshold")
    p_chat.add_argument("--top-k", type=int, default=40, help="Top-K cutoff")
    p_chat.add_argument("--repeat-penalty", type=float, default=1.15, help="Repetition penalty")
    p_chat.add_argument("--system-prompt", help="System prompt prefix")
    p_chat.add_argument("-r", "--stop", help="Comma-separated stop tokens")
    p_chat.set_defaults(func=cmd_chat)

    # serve
    p_serve = subparsers.add_parser("serve", help="Run OpenAI-compatible local API server")
    p_serve.add_argument("-m", "--model", default=None, help="Path to GGUF model binary (default: auto-discover cached model)")
    p_serve.add_argument("--host", default="0.0.0.0", help="Binding host")
    p_serve.add_argument("--port", type=int, default=8080, help="Port number")
    p_serve.set_defaults(func=cmd_serve)

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run inference performance benchmark")
    p_bench.add_argument("-m", "--model", default=None, help="Path to GGUF model binary (default: auto-discover cached model)")
    p_bench.add_argument("-t", "--threads", type=int, default=4, help="Worker threads")
    p_bench.set_defaults(func=cmd_benchmark)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
