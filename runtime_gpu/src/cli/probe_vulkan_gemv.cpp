#include "../core/vulkan_bitnet_engine.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <chrono>
#include <iomanip>
#include <random>
#include <cassert>

int main(int argc, char** argv) {
    uint32_t dim_m = 2048;
    uint32_t dim_k = 2048;
    uint32_t benchmark_iters = 50;
    float dequant_scale = 0.0125f;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--dim-m" && i + 1 < argc) dim_m = std::stoul(argv[++i]);
        else if (arg == "--dim-k" && i + 1 < argc) dim_k = std::stoul(argv[++i]);
        else if (arg == "--iters" && i + 1 < argc) benchmark_iters = std::stoul(argv[++i]);
    }

    std::cout << "========================================================\n"
              << "  AMEVA BitNet Vulkan GPU Engine — Real-Device Probe\n"
              << "  Target: ARM Mali & Qualcomm Adreno (Zero Silent Fallback)\n"
              << "========================================================\n"
              << "Configuration:\n"
              << "  Matrix Dimensions: M = " << dim_m << " (rows), K = " << dim_k << " (cols)\n"
              << "  Ternary Blocks:    " << (dim_k / 128) << " blocks per row (" << (dim_k / 4) << " bytes/row)\n"
              << "  Total Weight Size: " << (dim_m * (dim_k / 4)) / 1024 << " KB\n"
              << "  Benchmark Rounds:  " << benchmark_iters << "\n"
              << "--------------------------------------------------------" << std::endl;

    // Stage 1: Initialize Engine
    std::cout << "[STAGE 1] Initializing Vulkan GPU Engine..." << std::endl;
    ameva::core::VulkanBitNetEngine engine;
    try {
        engine.Initialize();
    } catch (const ameva::core::AmevaVulkanExecutionError& e) {
        std::cerr << "[CRITICAL FAILURE] Engine Init Failed: " << e.what()
                  << " (VkResult: " << e.GetVkResult() << ")" << std::endl;
        return 101;
    }

    // Stage 2: Allocate GPU Buffers
    std::cout << "[STAGE 2] Allocating GPU Unified Host-Coherent Buffers..." << std::endl;
    try {
        engine.AllocateBuffers(dim_m, dim_k);
    } catch (const ameva::core::AmevaVulkanExecutionError& e) {
        std::cerr << "[CRITICAL FAILURE] Buffer Allocation Failed: " << e.what() << std::endl;
        return 102;
    }

    // Stage 3: Synthesize Deterministic Test Data
    std::cout << "[STAGE 3] Generating Test Vectors (CPU Reference vs GPU)..." << std::endl;
    size_t num_blocks = dim_k / 128;
    size_t weight_bytes_total = dim_m * num_blocks * 32;
    std::vector<uint8_t> h_weights(weight_bytes_total);
    std::vector<float> h_activations(dim_k);
    std::vector<float> h_output_cpu(dim_m, 0.0f);
    std::vector<float> h_output_gpu(dim_m, 0.0f);

    std::mt19937 rng(42); // Deterministic seed
    std::uniform_int_distribution<int> weight_dist(0, 255);
    std::uniform_real_distribution<float> act_dist(-1.0f, 1.0f);

    for (size_t i = 0; i < weight_bytes_total; ++i) {
        h_weights[i] = static_cast<uint8_t>(weight_dist(rng));
    }
    for (size_t i = 0; i < dim_k; ++i) {
        h_activations[i] = act_dist(rng);
    }

    engine.UploadWeights(h_weights.data(), weight_bytes_total);

    // Stage 4: CPU Reference Computation
    std::cout << "[STAGE 4] Executing CPU Ground-Truth Reference GEMV..." << std::endl;
    auto t_cpu_start = std::chrono::high_resolution_clock::now();
    for (uint32_t r = 0; r < dim_m; ++r) {
        float sum = 0.0f;
        const uint8_t* row_weights = h_weights.data() + r * (num_blocks * 32);
        for (uint32_t b = 0; b < num_blocks; ++b) {
            const uint8_t* block_weights = row_weights + b * 32;
            const float* block_acts = h_activations.data() + b * 128;

            for (uint32_t k = 0; k < 32; ++k) {
                uint8_t byte_val = block_weights[k];

                int8_t w0 = static_cast<int8_t>((byte_val >> 6) & 0x03) - 1;
                int8_t w1 = static_cast<int8_t>((byte_val >> 4) & 0x03) - 1;
                int8_t w2 = static_cast<int8_t>((byte_val >> 2) & 0x03) - 1;
                int8_t w3 = static_cast<int8_t>(byte_val & 0x03) - 1;

                float x0 = block_acts[k + 0 * 32];
                float x1 = block_acts[k + 1 * 32];
                float x2 = block_acts[k + 2 * 32];
                float x3 = block_acts[k + 3 * 32];

                sum += static_cast<float>(w0) * x0 +
                       static_cast<float>(w1) * x1 +
                       static_cast<float>(w2) * x2 +
                       static_cast<float>(w3) * x3;
            }
        }
        h_output_cpu[r] = sum * dequant_scale;
    }
    auto t_cpu_end = std::chrono::high_resolution_clock::now();
    double cpu_time_ms = std::chrono::duration<double, std::milli>(t_cpu_end - t_cpu_start).count();
    std::cout << "  CPU Reference Time: " << std::fixed << std::setprecision(3) << cpu_time_ms << " ms" << std::endl;

    // Stage 5: GPU Execution & Warmup
    std::cout << "[STAGE 5] Executing GPU Dispatch & Warmup..." << std::endl;
    for (int w = 0; w < 5; ++w) {
        engine.DispatchGemv(h_activations.data(), h_output_gpu.data(), dim_m, dim_k, dequant_scale);
    }

    // Stage 6: Parity Validation
    std::cout << "[STAGE 6] Validating Mathematical Parity (Zero Deception)..." << std::endl;
    float max_diff = 0.0f;
    float sum_diff = 0.0f;
    uint32_t worst_row = 0;

    for (uint32_t r = 0; r < dim_m; ++r) {
        float diff = std::abs(h_output_cpu[r] - h_output_gpu[r]);
        if (diff > max_diff) {
            max_diff = diff;
            worst_row = r;
        }
        sum_diff += diff;
    }
    float avg_diff = sum_diff / dim_m;

    std::cout << "  Max Absolute Difference: " << std::scientific << max_diff << "\n"
              << "  Mean Absolute Difference: " << avg_diff << std::defaultfloat << "\n"
              << "  Worst Row Index: " << worst_row
              << " (CPU: " << h_output_cpu[worst_row] << ", GPU: " << h_output_gpu[worst_row] << ")" << std::endl;

    // Strict threshold: floating-point reduction summation order variation allows <= 1e-4
    if (max_diff > 1e-4f) {
        std::cerr << "\n[CRITICAL ERROR] Mathematical Parity Check FAILED! Max diff exceeds 1e-4 threshold.\n"
                  << "Zero Deception Violation: GPU kernel computed corrupted values!" << std::endl;
        return 103;
    }
    std::cout << "  [PASS] Output Parity Verified (Δ < 1e-4)." << std::endl;

    // Stage 7: Benchmark Execution
    std::cout << "[STAGE 7] Benchmarking GPU Kernel (" << benchmark_iters << " iterations)..." << std::endl;
    auto t_gpu_start = std::chrono::high_resolution_clock::now();
    for (uint32_t it = 0; it < benchmark_iters; ++it) {
        engine.DispatchGemv(h_activations.data(), h_output_gpu.data(), dim_m, dim_k, dequant_scale);
    }
    auto t_gpu_end = std::chrono::high_resolution_clock::now();
    double total_gpu_time_ms = std::chrono::duration<double, std::milli>(t_gpu_end - t_gpu_start).count();
    double avg_gpu_time_ms = total_gpu_time_ms / benchmark_iters;

    double gflops = (2.0 * dim_m * dim_k) / (avg_gpu_time_ms * 1e6);
    double bandwidth_gb_s = (weight_bytes_total + (dim_k + dim_m) * sizeof(float)) / (avg_gpu_time_ms * 1e6);

    std::cout << "--------------------------------------------------------\n"
              << "  Benchmark Results:\n"
              << "    Average GPU GEMV Latency: " << std::fixed << std::setprecision(3) << avg_gpu_time_ms << " ms\n"
              << "    Compute Throughput:       " << std::fixed << std::setprecision(2) << gflops << " GFLOPS\n"
              << "    Memory Bandwidth:         " << std::fixed << std::setprecision(2) << bandwidth_gb_s << " GB/s\n"
              << "    Speedup vs CPU Ref:       " << std::fixed << std::setprecision(2) << (cpu_time_ms / avg_gpu_time_ms) << "x\n"
              << "--------------------------------------------------------" << std::endl;

    // Stage 8: Fail-Fast Fault Injection Test
    std::cout << "[STAGE 8] Testing Zero-Silent-Fallback Fail-Fast Mandate..." << std::endl;
    bool caught_expected_error = false;
    try {
        // Attempt dispatch with mismatched dimensions
        engine.DispatchGemv(h_activations.data(), h_output_gpu.data(), dim_m + 1, dim_k, dequant_scale);
    } catch (const ameva::core::AmevaVulkanExecutionError& e) {
        caught_expected_error = true;
        std::cout << "  [PASS] Correctly intercepted fault injection with Fail-Fast: " << e.what() << std::endl;
    }

    if (!caught_expected_error) {
        std::cerr << "[CRITICAL ERROR] Zero-Silent-Fallback Violation: Invalid operation did not raise exception!" << std::endl;
        return 104;
    }

    engine.Shutdown();
    std::cout << "\n========================================================\n"
              << "  ALL PROBE STAGES PASSED: 100% Verified Authentic GPU Acceleration\n"
              << "========================================================\n" << std::endl;
    return 0;
}
