"""OpenAI Python SDK integration example with termux-bitnet local server."""

import urllib.request
import json

def test_local_server():
    url = "http://localhost:8080/v1/chat/completions"
    payload = {
        "model": "bitnet-b1.58-2b-4t",
        "messages": [
            {"role": "user", "content": "Explain the harmonic mean in simple terms."}
        ],
        "temperature": 0.3,
        "max_tokens": 150
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    print(f"[Client] Sending request to {url}...")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            print(f"[Assistant Response]:\n{content}")
    except Exception as e:
        print(f"[Client] Could not connect to local server: {e}")
        print("  Make sure the server is running with: termux-bitnet serve --port 8080")

if __name__ == "__main__":
    test_local_server()
