#pragma once
#include <cstdint>
#include <string>

namespace ameva {
namespace quirks {

struct GpuDeviceInfo {
    uint32_t vendor_id{0};
    uint32_t device_id{0};
    uint32_t api_version{0};
    uint32_t driver_version{0};
    std::string device_name;
    bool is_mali{false};
    bool is_adreno{false};
    uint32_t required_alignment{128};
    uint32_t optimal_workgroup_size{128};
};

class GpuQuirksEngine {
public:
    static constexpr uint32_t ARM_VENDOR_ID = 0x13b5;
    static constexpr uint32_t QUALCOMM_VENDOR_ID = 0x5143;

    static GpuDeviceInfo AnalyzeDevice(uint32_t vendor_id, uint32_t device_id, const char* name, uint32_t api_ver, uint32_t driver_ver);

    static uint32_t AlignSize(uint32_t size, uint32_t align_bytes);

    static bool ValidateTensorAlignment(uint32_t dim_k, uint32_t dim_m);
};

} // namespace quirks
} // namespace ameva
