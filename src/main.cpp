/**
 * @file main.cpp
 * @brief Native Standalone CLI Application for Termux/ARM64.
 */

#include "termux_bitnet.h"
#include <iostream>
#include <string>
#include <vector>
#include <cstring>

static bool stream_print_cb(const char* token_str, int32_t token_id, void* user_data) {
    (void)token_id;
    (void)user_data;
    std::cout << token_str << std::flush;
    return true;
}

int main(int argc, char** argv) {
    bitnet_params_t params = bitnet_default_params();
    std::string prompt = "The capital of France is";
    int32_t n_predict = 128;

    char hw_info[256];
    bitnet_get_hardware_info(hw_info, sizeof(hw_info));
    std::cout << "=========================================================" << std::endl;
    std::cout << "  termux-bitnet: Native 1.58-bit Inference Engine" << std::endl;
    std::cout << "  " << hw_info << std::endl;
    std::cout << "=========================================================" << std::endl;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if ((arg == "-m" || arg == "--model") && i + 1 < argc) {
            params.model_path = argv[++i];
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
        } else if (arg == "-h" || arg == "--help") {
            std::cout << "Usage: termux-bitnet-cli [options]\n"
                      << "  -m, --model <path>         Path to GGUF model\n"
                      << "  -p, --prompt <text>        Input prompt text\n"
                      << "  -t, --threads <int>        CPU worker threads\n"
                      << "  -c, --ctx-size <int>       Context size (default: 2048)\n"
                      << "  -b, --batch-size <int>     Batch size (default: 512)\n"
                      << "  -n, --n-predict <int>      Tokens to predict (default: 128)\n"
                      << "  --temp <float>             Temperature (default: 0.7)\n"
                      << "  --top-p <float>            Top-P sampling (default: 0.95)\n"
                      << "  --top-k <int>              Top-K sampling (default: 40)\n"
                      << "  --min-p <float>            Min-P sampling (default: 0.05)\n"
                      << "  --repeat-penalty <float>   Repetition penalty (default: 1.15)\n"
                      << "  --repeat-last-n <int>      Repetition penalty window (default: 64)\n"
                      << "  --freq-penalty <float>     Frequency penalty (default: 0.0)\n"
                      << "  --presence-penalty <float> Presence penalty (default: 0.0)\n"
                      << "  -s, --seed <uint>          RNG seed (default: 0 for random)\n"
                      << "  -ngl <int>                 GPU/NPU offload layers (default: 0)\n"
                      << "  -fa, --flash-attn          Enable Flash Attention\n"
                      << "  --system-prompt <text>     System prompt prefix\n"
                      << "  -r, --stop <tokens>        Comma-separated stop sequences\n"
                      << "  -v, --verbose              Enable diagnostic logging\n";
            return 0;
        }
    }

    std::cout << "[Prompt]: " << prompt << std::endl;
    std::cout << "[Response]: " << std::flush;

    bitnet_context_t ctx = bitnet_init(&params);
    if (!ctx) {
        std::cerr << "Failed to initialize BitNet context." << std::endl;
        return 1;
    }

    int32_t total_tokens = bitnet_generate_stream(ctx, prompt.c_str(), n_predict, stream_print_cb, nullptr);
    std::cout << std::endl << std::endl;

    double prompt_eval_ms = 0.0, eval_ms = 0.0, tokens_per_sec = 0.0;
    bitnet_get_perf_stats(ctx, &prompt_eval_ms, &eval_ms, &tokens_per_sec);

    std::cout << "---------------------------------------------------------" << std::endl;
    std::cout << "  Prompt Eval Time: " << prompt_eval_ms << " ms" << std::endl;
    std::cout << "  Generation Time:  " << eval_ms << " ms (" << total_tokens << " tokens)" << std::endl;
    std::cout << "  Inference Speed:  " << tokens_per_sec << " tokens/sec" << std::endl;
    std::cout << "---------------------------------------------------------" << std::endl;

    bitnet_free(ctx);
    return 0;
}
