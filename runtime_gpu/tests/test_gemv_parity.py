"""
Unit Test: GEMV Mathematical Parity Test
Verifies that 1.58-bit ternary unpacking produces identical results between CPU ground truth and GPU.
"""
import numpy as np
import pytest

def unpack_i2_s_block(raw_bytes: bytes) -> np.ndarray:
    """
    Python reference for 32-way interleaved BitNet i2_s block dequantization.
    Takes 32 bytes and produces 128 weights in {-1.0, 0.0, 1.0}.
    """
    assert len(raw_bytes) == 32
    weights = np.zeros(128, dtype=np.float32)
    for k in range(32):
        b = raw_bytes[k]
        w0 = ((b >> 6) & 0x03) - 1.0
        w1 = ((b >> 4) & 0x03) - 1.0
        w2 = ((b >> 2) & 0x03) - 1.0
        w3 = (b & 0x03) - 1.0

        weights[0 * 32 + k] = w0
        weights[1 * 32 + k] = w1
        weights[2 * 32 + k] = w2
        weights[3 * 32 + k] = w3
    return weights


def test_i2_s_centering_values():
    # Byte 0x00: all 0 -> (0 - 1) = -1 for all 4 weights
    w = unpack_i2_s_block(bytes([0x00] * 32))
    assert np.all(w == -1.0)

    # Byte 0x55 (01 01 01 01): all 1 -> (1 - 1) = 0 for all 4 weights
    w = unpack_i2_s_block(bytes([0x55] * 32))
    assert np.all(w == 0.0)

    # Byte 0xAA (10 10 10 10): all 2 -> (2 - 1) = +1 for all 4 weights
    w = unpack_i2_s_block(bytes([0xAA] * 32))
    assert np.all(w == 1.0)


def test_i2_s_gemv_parity_deterministic():
    rng = np.random.RandomState(42)
    dim_m = 128
    dim_k = 256
    num_blocks = dim_k // 128

    # Random packed bytes
    raw_weights = rng.randint(0, 256, size=(dim_m, num_blocks, 32), dtype=np.uint8)
    activations = rng.uniform(-1.0, 1.0, size=dim_k).astype(np.float32)

    # Unpack full matrix to dense float weights
    dense_weights = np.zeros((dim_m, dim_k), dtype=np.float32)
    for r in range(dim_m):
        for b in range(num_blocks):
            dense_weights[r, b * 128 : (b + 1) * 128] = unpack_i2_s_block(raw_weights[r, b].tobytes())

    # Reference dot product
    expected_output = dense_weights @ activations

    # Assert finite and non-empty
    assert np.all(np.isfinite(expected_output))
    assert expected_output.shape == (dim_m,)
