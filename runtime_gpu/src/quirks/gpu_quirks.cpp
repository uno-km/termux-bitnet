#include "gpu_quirks.h"
#include <algorithm>
#include <cstring>

namespace ameva {
namespace quirks {

GpuDeviceInfo GpuQuirksEngine::AnalyzeDevice(uint32_t vendor_id, uint32_t device_id, const char* name, uint32_t api_ver, uint32_t driver_ver) {
    GpuDeviceInfo info;
    info.vendor_id = vendor_id;
    info.device_id = device_id;
    info.api_version = api_ver;
    info.driver_version = driver_ver;
    info.device_name = name ? name : "Unknown";

    std::string lower_name = info.device_name;
    std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);

    if (vendor_id == ARM_VENDOR_ID || lower_name.find("mali") != std::string::npos) {
        info.is_mali = true;
        info.required_alignment = 128; // Strict L2 cacheline alignment
        info.optimal_workgroup_size = 128; // 32x4 layout prevents subgroup integer truncation
    } else if (vendor_id == QUALCOMM_VENDOR_ID || lower_name.find("adreno") != std::string::npos) {
        info.is_adreno = true;
        info.required_alignment = 64;  // Adreno cacheline alignment
        info.optimal_workgroup_size = 128;
    } else {
        info.required_alignment = 64;
        info.optimal_workgroup_size = 128;
    }

    return info;
}

uint32_t GpuQuirksEngine::AlignSize(uint32_t size, uint32_t align_bytes) {
    if (align_bytes == 0) return size;
    return (size + align_bytes - 1) & ~(align_bytes - 1);
}

bool GpuQuirksEngine::ValidateTensorAlignment(uint32_t dim_k, uint32_t dim_m) {
    // BitNet i2_s blocks require K to be a multiple of 128
    if (dim_k % 128 != 0) return false;
    // Our 4-row workgroup tiling processes 4 rows per workgroup
    if (dim_m == 0) return false;
    return true;
}

} // namespace quirks
} // namespace ameva
