# Release Notes - termux-bitnet

## [v1.0.7] - 2026-08-27

### Security, Fail-Fast Protocol & Actionable Remediation (SCRUM-104)
- **Model Downloader Typo Detection & Suggestions**:
  - Implemented typo detection in Python (`difflib`) and Node.js (Levenshtein distance) model downloaders.
  - When users provide a mistyped model alias (e.g. `bitnet2b`, `bitnet-lg`), the CLI/SDK explicitly flags the typo and recommends the closest verified model (e.g., `Did you mean 'bitnet-2b'?`).
  - Completely unknown model requests now list all verified Hugging Face GGUF models in the registry along with `termux-bitnet models` inspection instructions.
- **Server Error Handling Hardening**:
  - Replaced silent empty string returns in local OpenAI-compatible HTTP server (`termux_bitnet/server.py`) with explicit HTTP status codes:
    - **HTTP 503 (Service Unavailable)** when engine is uninitialized with clear instructions to provide a valid model path.
    - **HTTP 400 (Bad Request)** when messages or prompt payload is empty or invalid.
    - **HTTP 500 (Internal Server Error)** with detailed JSON error messages when inference runtime encounters an exception.
- **C++ Native Core Guard Hardening**:
  - Enforced strict `ctx->is_initialized` validation checks across `bitnet_eval`, `bitnet_sample`, `bitnet_tokenize`, `bitnet_token_to_str`, and `bitnet_generate_stream` in `src/llama_bitnet_core.cpp` to prevent uninitialized execution paths.
- **Test Suite & Build Artifacts**:
  - Added 16-test comprehensive automated test suite covering typo suggestion, uninitialized server fail-fast, model existence checks, and prompt validation.