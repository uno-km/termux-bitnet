"""Simple streaming inference example using termux-bitnet Python SDK."""

import sys
from termux_bitnet import BitNetEngine, BitNetConfig, detect_hardware

def main():
    hw = detect_hardware()
    print(f"[System] Platform: {hw.arch} | SoC: {hw.soc_name} | Cores: {hw.cpu_cores}")

    config = BitNetConfig(
        n_threads=hw.recommended_threads,
        temperature=0.3,
        top_p=0.95,
        repeat_penalty=1.18,
    )

    prompt = "Question: Write a Python function to check if a string is a palindrome. Provide only the code."
    print(f"\n[Prompt]: {prompt}\n[Response]: ", end="", flush=True)

    with BitNetEngine(config) as engine:
        for token in engine.generate_stream(prompt, max_tokens=150):
            sys.stdout.write(token)
            sys.stdout.flush()
        print()

        metrics = engine.get_last_metrics()
        print(f"\n[Telemetry] Speed: {metrics.tokens_per_second:.2f} tokens/sec")

if __name__ == "__main__":
    main()
