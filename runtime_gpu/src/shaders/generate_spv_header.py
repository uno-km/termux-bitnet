import struct
import os
import subprocess
import sys

def compile_shader(comp_path: str, spv_path: str):
    cmd = ["glslangValidator", "-V", comp_path, "-o", spv_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Error compiling {comp_path}:\n{res.stderr}\n{res.stdout}")
        sys.exit(1)
    print(f"Compiled {comp_path} -> {spv_path}")

def spv_to_header(spv_path: str, header_path: str, array_name: str):
    with open(spv_path, "rb") as f:
        data = f.read()
    
    assert len(data) % 4 == 0, f"SPV size ({len(data)}) must be a multiple of 4"
    words = struct.unpack(f"<{len(data)//4}I", data)
    assert words[0] == 0x07230203, f"Invalid SPIR-V magic number: 0x{words[0]:08x}"
    
    lines = []
    lines.append(f"// Auto-generated from {os.path.basename(spv_path)} via glslangValidator. DO NOT EDIT.")
    lines.append("#pragma once")
    lines.append("#include <cstdint>")
    lines.append("#include <cstddef>")
    lines.append("")
    lines.append("namespace ameva {")
    lines.append("namespace shaders {")
    lines.append("")
    lines.append(f"alignas(4) static const uint32_t {array_name}[] = {{")
    
    row = []
    for i, w in enumerate(words):
        row.append(f"0x{w:08x}")
        if len(row) == 8:
            lines.append("    " + ", ".join(row) + ",")
            row = []
    if row:
        lines.append("    " + ", ".join(row) + ",")
        
    lines.append("};")
    lines.append(f"static const size_t {array_name}ByteSize = {len(data)};")
    lines.append(f"static const size_t {array_name}WordCount = {len(words)};")
    lines.append("")
    lines.append("} // namespace shaders")
    lines.append("} // namespace ameva")
    lines.append("")
    
    with open(header_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Successfully generated {header_path} ({len(data)} bytes, {len(words)} words)")

if __name__ == "__main__":
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    shaders = [
        ("rope.comp", "rope.spv", "rope_spv.h", "kRopeSpv"),
        ("attention_decode.comp", "attention_decode.spv", "attention_decode_spv.h", "kAttentionDecodeSpv"),
        ("squared_relu.comp", "squared_relu.spv", "squared_relu_spv.h", "kSquaredReluSpv"),
        ("swiglu_silu.comp", "swiglu_silu.spv", "swiglu_silu_spv.h", "kSwigluSiluSpv"),
        ("rmsnorm.comp", "rmsnorm.spv", "rmsnorm_spv.h", "kRmsNormSpv"),
        ("rmsnorm_norm.comp", "rmsnorm_norm.spv", "rmsnorm_norm_spv.h", "kRmsnormNormSpv"),
        ("residual_add.comp", "residual_add.spv", "residual_add_spv.h", "kResidualAddSpv"),
        ("bitnet_gemv_i2_s.comp", "bitnet_gemv_i2_s.spv", "bitnet_gemv_i2_s_spv.h", "kBitnetGemvI2SSpv"),
        ("bitnet_gemv_f16.comp", "bitnet_gemv_f16.spv", "bitnet_gemv_f16_spv.h", "kBitnetGemvF16Spv"),
    ]
    
    compile_all = "--compile" in sys.argv
    for comp, spv, header, arr in shaders:
        comp_path = os.path.join(cur_dir, comp)
        spv_path = os.path.join(cur_dir, spv)
        header_path = os.path.join(cur_dir, header)
        if compile_all and os.path.exists(comp_path):
            compile_shader(comp_path, spv_path)
        if os.path.exists(spv_path):
            spv_to_header(spv_path, header_path, arr)
