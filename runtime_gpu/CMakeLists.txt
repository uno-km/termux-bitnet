cmake_minimum_required(VERSION 3.10)
project(ameva_vulkan_bitnet LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

set(CORE_SOURCES
    src/core/vulkan_loader.cpp
    src/core/vulkan_bitnet_engine.cpp
    src/quirks/gpu_quirks.cpp
)

# Detect Vulkan library
if(ANDROID OR CMAKE_SYSTEM_NAME STREQUAL "Android" OR EXISTS "/system/lib64/libvulkan.so")
    find_library(VULKAN_LIB vulkan PATHS /data/data/com.termux/files/usr/lib /system/lib64 /vendor/lib64)
    if(NOT VULKAN_LIB)
        set(VULKAN_LIB "vulkan")
    endif()
    set(EXTRA_LIBS ${VULKAN_LIB} dl)
elseif(UNIX)
    find_library(VULKAN_LIB vulkan)
    set(EXTRA_LIBS ${VULKAN_LIB} dl pthread)
else()
    set(EXTRA_LIBS)
endif()

# 1. Build Standalone CLI Hardware Probe
add_executable(probe_vulkan_gemv
    src/cli/probe_vulkan_gemv.cpp
    ${CORE_SOURCES}
)
target_link_libraries(probe_vulkan_gemv PRIVATE ${EXTRA_LIBS})

# 2. Build Shared C++ Library for Ameva-Runtime & Python CFFI/ctypes Binding
add_library(ameva_vulkan_bitnet SHARED
    ${CORE_SOURCES}
)
target_link_libraries(ameva_vulkan_bitnet PRIVATE ${EXTRA_LIBS})

install(TARGETS probe_vulkan_gemv ameva_vulkan_bitnet
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)