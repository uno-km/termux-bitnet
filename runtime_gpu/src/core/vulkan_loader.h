#pragma once
#include <string>
#include <cstdint>

namespace ameva {
namespace core {

/**
 * @brief Vulkan Dynamic Loader & Bionic System Vendor Driver Enforcer.
 * Strictly loads the Android hardware vendor driver (/system/lib64/libvulkan.so)
 * without linking to desktop or software emulation loaders.
 */
class VulkanLoader {
public:
    VulkanLoader();
    ~VulkanLoader();

    VulkanLoader(const VulkanLoader&) = delete;
    VulkanLoader& operator=(const VulkanLoader&) = delete;

    bool Load(const std::string& explicit_path = "");
    void Unload();

    bool IsLoaded() const { return library_handle_ != nullptr; }
    const std::string& GetLoadedPath() const { return loaded_path_; }

    void* GetProcAddr(const char* name) const;

private:
    void* library_handle_{nullptr};
    std::string loaded_path_;
};

} // namespace core
} // namespace ameva
