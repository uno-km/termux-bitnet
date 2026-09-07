/**
 * @file main.cpp
 * @brief Native Standalone CLI Application for Termux/ARM64 (Strict Fail-Fast).
 */

#include "termux_bitnet.h"
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <cstring>

static void print_usage(std::ostream& out) {
    out << "Usage: termux-bitnet-cli -m <model_path> -p \"<prompt>\" [options]\n\n"
        << "Required Options:\n"
        << "  -m, --model <path>         Path to GGUF model binary (*.gguf)\n"
        << "  -p, --prompt <text>        Input prompt text for text generation\n\n"
        << "Hyperparameter Options:\n"
        << "  -d, --device <backend>     Hardware device ('auto', 'cpu', 'vulkan', 'gpu')\n"
        << "  -t, --threads <int>        CPU worker threads (default: 4)\n"
        << "  -c, --ctx-size <int>       Context window size (default: 2048)\n"
        << "  -b, --batch-size <int>     Batch size (default: 512)\n"
        << "  -ub, --ubatch-size <int>   Micro-batch size (default: 512)\n"
        << "  -n, --n-predict <int>      Max tokens to predict (default: 128)\n"
        << "  --temp <float>             Sampling temperature (default: 0.7)\n"
        << "  --top-p <float>            Top-P cumulative probability (default: 0.95)\n"
        << "  --top-k <int>              Top-K selection threshold (default: 40)\n"
        << "  --min-p <float>            Min-P probability threshold (default: 0.05)\n"
        << "  --typical <float>          Locally typical threshold (default: 1.0)\n"
        << "  --repeat-penalty <float>   Repetition penalty multiplier (default: 1.15)\n"
        << "  --repeat-last-n <int>      Repetition penalty window (default: 64)\n"
        << "  --freq-penalty <float>     Frequency penalty (default: 0.0)\n"
        << "  --presence-penalty <float> Presence penalty (default: 0.0)\n"
        << "  -s, --seed <uint>          RNG seed (0 for random)\n"
        << "  -ngl <int>                 GPU/NPU offload layers (default: 0)\n"
        << "  -fa, --flash-attn          Enable Flash Attention\n"
        << "  --system-prompt <text>     System prompt prefix\n"
        << "  -r, --stop <tokens>        Comma-separated stop sequences\n"
        << "  -v, --verbose              Enable diagnostic logging\n"
        << "  -h, --help                 Show this help manual\n\n"
        << "Download Verified Models:\n"
        << "  termux-bitnet download bitnet-2b       (Microsoft BitNet 2B-4T, 1.13 GB)\n"
        << "  termux-bitnet download bitnet-large    (BitNet Large 0.7B, 700 MB)\n"
        << "  termux-bitnet download bitnet-3b       (BitNet 3B, 2.4 GB)\n"
        << "  termux-bitnet download bitnet-3b-q4    (BitNet 3B Q4_K_M, 1.8 GB)\n\n"
        << "Official Hugging Face Repositories:\n"
        << "  - https://huggingface.co/1bitLLM/bitnet_b1_58-large-GGUF\n"
        << "  - https://huggingface.co/1bitLLM/bitnet_b1_58-3B-GGUF\n";
}

static bool stream_print_cb(const char* token_str, int32_t token_id, void* user_data) {
    (void)token_id;
    (void)user_data;
    std::cout << token_str << std::flush;
    return true;
}

int main(int argc, char** argv) {
    bitnet_params_t params = bitnet_default_params();
    std::string prompt = "";
    int32_t n_predict = 128;

    char hw_info[256];
    bitnet_get_hardware_info(hw_info, sizeof(hw_info));

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-h" || arg == "--help") {
            print_usage(std::cout);
            return 0;
        } else if ((arg == "-m" || arg == "--model") && i + 1 < argc) {
            params.model_path = argv[++i];
        } else if ((arg == "-d" || arg == "--device") && i + 1 < argc) {
            std::string dev_arg = argv[++i];
            if (dev_arg == "cpu") {
                params.n_gpu_layers = 0;
            } else if (dev_arg == "gpu" || dev_arg == "vulkan") {
                if (params.n_gpu_layers == 0) params.n_gpu_layers = 33;
            } else if (dev_arg == "auto") {
#if defined(GGML_USE_VULKAN)
                if (params.n_gpu_layers == 0) params.n_gpu_layers = 33;
#else
                params.n_gpu_layers = 0;
#endif
            } else {
                std::cerr << "[ERROR] Unsupported device: '" << dev_arg << "'. Expected 'auto', 'cpu', 'vulkan', or 'gpu'." << std::endl;
                return 2; // EXIT_ARG_ERROR
            }
        } else if ((arg == "-p" || arg == "--prompt") && i + 1 < argc) {
            prompt = argv[++i];
        } else if ((arg == "-t" || arg == "--threads") && i + 1 < argc) {
            params.n_threads = std::atoi(argv[++i]);
        } else if ((arg == "-c" || arg == "--ctx-size") && i + 1 < argc) {
            params.n_ctx = std::atoi(argv[++i]);
        } else if ((arg == "-b" || arg == "--batch-size") && i + 1 < argc) {
            params.n_batch = std::atoi(argv[++i]);
        } else if ((arg == "-ub" || arg == "--ubatch-size") && i + 1 < argc) {
            params.n_ubatch = std::atoi(argv[++i]);
        } else if ((arg == "-n" || arg == "--n-predict") && i + 1 < argc) {
            n_predict = std::atoi(argv[++i]);
            params.n_predict = n_predict;
        } else if ((arg == "-temp" || arg == "--temp" || arg == "--temperature") && i + 1 < argc) {
            params.temperature = (float)std::atof(argv[++i]);
        } else if (arg == "--top-p" && i + 1 < argc) {
            params.top_p = (float)std::atof(argv[++i]);
        } else if (arg == "--top-k" && i + 1 < argc) {
            params.top_k = std::atoi(argv[++i]);
        } else if (arg == "--min-p" && i + 1 < argc) {
            params.min_p = (float)std::atof(argv[++i]);
        } else if (arg == "--typical" && i + 1 < argc) {
            params.typical_p = (float)std::atof(argv[++i]);
        } else if (arg == "--repeat-penalty" && i + 1 < argc) {
            params.repeat_penalty = (float)std::atof(argv[++i]);
        } else if (arg == "--repeat-last-n" && i + 1 < argc) {
            params.repeat_last_n = std::atoi(argv[++i]);
        } else if (arg == "--freq-penalty" && i + 1 < argc) {
            params.frequency_penalty = (float)std::atof(argv[++i]);
        } else if (arg == "--presence-penalty" && i + 1 < argc) {
            params.presence_penalty = (float)std::atof(argv[++i]);
        } else if ((arg == "-s" || arg == "--seed") && i + 1 < argc) {
            params.seed = (uint32_t)std::strtoul(argv[++i], nullptr, 10);
        } else if ((arg == "-ngl" || arg == "--n-gpu-layers") && i + 1 < argc) {
            params.n_gpu_layers = std::atoi(argv[++i]);
        } else if (arg == "-fa" || arg == "--flash-attn") {
            params.flash_attn = true;
        } else if (arg == "--system-prompt" && i + 1 < argc) {
            params.system_prompt = argv[++i];
        } else if ((arg == "-r" || arg == "--stop") && i + 1 < argc) {
            params.stop_tokens = argv[++i];
        } else if (arg == "-v" || arg == "--verbose") {
            params.verbose = true;
        } else {
            std::cerr << "[ERROR] Unrecognized or incomplete argument: '" << arg << "'" << std::endl;
            std::cerr << "Run 'termux-bitnet-cli --help' for supported CLI options." << std::endl;
            return 2; // EXIT_ARG_ERROR
        }
    }

    // Strict Validation 1: Model file must be provided and must exist
    if (!params.model_path || std::strlen(params.model_path) == 0) {
        std::cerr << "[ERROR] No model file specified. Missing required argument: -m or --model <path>\n" << std::endl;
        print_usage(std::cerr);
        return 10; // EXIT_MODEL_NOT_FOUND
    }

    std::ifstream model_check(params.model_path, std::ios::binary);
    if (!model_check.is_open()) {
        std::cerr << "[ERROR] Specified model file does not exist or is inaccessible: '" << params.model_path << "'\n" << std::endl;
        print_usage(std::cerr);
        return 10; // EXIT_MODEL_NOT_FOUND
    }
    model_check.close();

    // Strict Validation 2: Prompt must be provided and non-empty
    if (prompt.empty() || prompt.find_first_not_of(" \t\n\r") == std::string::npos) {
        std::cerr << "[ERROR] No input prompt specified. Missing required argument: -p or --prompt \"<text>\"\n" << std::endl;
        std::cerr << "Example:\n"
                  << "  termux-bitnet-cli -m " << params.model_path << " -p \"Explain 1.58-bit quantization in one sentence:\"\n" << std::endl;
        return 2; // EXIT_ARG_ERROR
    }

    std::cout << "=========================================================" << std::endl;
    std::cout << "  termux-bitnet: Native 1.58-bit Inference Engine" << std::endl;
    std::cout << "  " << hw_info << std::endl;
    std::cout << "  Model: " << params.model_path << std::endl;
    std::cout << "  Prompt: " << prompt << std::endl;
    std::cout << "=========================================================" << std::endl;

    bitnet_context_t ctx = bitnet_init(&params);
    if (!ctx) {
        std::cerr << "[FATAL] BitNet context initialization failed for model: " << params.model_path << std::endl;
        return 10;
    }

    std::cout << "[Response]: " << std::flush;
    bitnet_generate_stream(ctx, prompt.c_str(), n_predict, stream_print_cb, nullptr);
    std::cout << std::endl;

    double p_eval_ms = 0.0, eval_ms = 0.0, tps = 0.0;
    bitnet_get_perf_stats(ctx, &p_eval_ms, &eval_ms, &tps);

    std::cout << "---------------------------------------------------------" << std::endl;
    std::cout << "  Prompt Eval Time: " << p_eval_ms << " ms" << std::endl;
    std::cout << "  Eval Time:        " << eval_ms << " ms" << std::endl;
    std::cout << "  Inference Speed:  " << tps << " tokens/sec" << std::endl;
    std::cout << "---------------------------------------------------------" << std::endl;

    bitnet_free(ctx);
    return 0;
}
