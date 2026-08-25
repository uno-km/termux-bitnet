cmake_minimum_required(VERSION 3.14)
project(termux_bitnet LANGUAGES C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Optimization Options
option(BUILD_SHARED_LIBS "Build shared libraries" ON)
option(GGML_NEON "Enable ARM NEON SIMD optimizations" ON)
option(GGML_ARM_DOTPROD "Enable ARM Dot Product extension" AUTO)
option(BUILD_CLI "Build native standalone CLI" ON)

# Compiler Optimization Flags
if(MSVC)
    add_compile_options(/O2 /W3 /utf-8)
else()
    add_compile_options(-O3 -Wall -Wextra -Wno-unused-parameter)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64|arm64")
        if(GGML_NEON)
            add_definitions(-D__ARM_NEON)
            if(GGML_ARM_DOTPROD)
                add_compile_options(-march=armv8.2-a+dotprod+fp16)
                add_definitions(-D__ARM_FEATURE_DOTPROD=1)
            else()
                add_compile_options(-march=armv8-a+simd+fp16)
            endif()
        endif()
    elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64")
        # x86 Fallback / Development environment
        if(NOT MSVC)
            add_compile_options(-mavx2 -mfma)
        endif()
    endif()
endif()

# Include Directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Core Sources
set(BITNET_CORE_SOURCES
    src/ggml_bitnet_mad.cpp
    src/llama_bitnet_core.cpp
    src/c_api.cpp
)

# Shared Library for Python SDK & C/C++ Embedding
add_library(termux_bitnet SHARED ${BITNET_CORE_SOURCES})
target_include_directories(termux_bitnet PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

if(UNIX AND NOT APPLE)
    target_link_libraries(termux_bitnet PRIVATE m pthread dl)
endif()

# Native CLI Application
if(BUILD_CLI)
    add_executable(termux-bitnet-cli src/main.cpp)
    target_link_libraries(termux-bitnet-cli PRIVATE termux_bitnet)
    target_include_directories(termux-bitnet-cli PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
endif()

# Install Directives
install(TARGETS termux_bitnet
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)
install(FILES include/termux_bitnet.h DESTINATION include)
