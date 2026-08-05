"""DC differential + AC run-length entropy coding: turns 64 zigzag-ordered
quantized coefficients per block into Huffman-coded bits.

DC: each block's DC coefficient is coded as the *difference* from the
previous block's DC value (same component) rather than the absolute
value, since adjacent blocks' average brightness is highly correlated --
the differences cluster near zero and compress much better than the raw
values would.

AC: the 63 AC coefficients are coded as (run-of-zeros, value) pairs, with
ZRL (0xF0) as an escape for runs longer than 15 zeros and EOB (0x00) to
mean "everything remaining in this block is zero" -- the whole reason
zigzag order (zigzag.py) puts low frequencies first is so that the
(usually many) trailing high-frequency zeros end up contiguous, which is
exactly what this run-length scheme wants.
"""
from __future__ import annotations

from .bitwriter import BitWriter

ZRL = 0xF0  # (run=15, size=0): "16 zero coefficients, keep going"
EOB = 0x00  # (run=0, size=0): "rest of block is zero"


def magnitude_category(value: int) -> int:
    """Number of bits needed to represent |value|; 0 only for value==0."""
    return abs(value).bit_length()


def additional_bits(value: int, size: int) -> int:
    """The `size`-bit value written after a magnitude-category symbol.
    Non-negative values are written directly; negative values use JPEG's
    one's-complement-style encoding (value + (2**size - 1)), so the
    top bit of the additional bits distinguishes sign on decode."""
    if size == 0:
        return 0
    return value if value >= 0 else value + (1 << size) - 1


def encode_block(
    writer: BitWriter,
    zigzag_coeffs: list,
    dc_predictor: int,
    dc_codes: dict,
    ac_codes: dict,
) -> int:
    """Encodes one block's 64 zigzag-ordered quantized coefficients.
    Returns the new DC predictor value (this block's absolute DC)."""
    dc_value = zigzag_coeffs[0]
    diff = dc_value - dc_predictor
    size = magnitude_category(diff)
    code, length = dc_codes[size]
    writer.write_bits(code, length)
    writer.write_bits(additional_bits(diff, size), size)

    zero_run = 0
    for k in range(1, 64):
        coeff = zigzag_coeffs[k]
        if coeff == 0:
            zero_run += 1
            continue
        while zero_run > 15:
            code, length = ac_codes[ZRL]
            writer.write_bits(code, length)
            zero_run -= 16
        size = magnitude_category(coeff)
        symbol = (zero_run << 4) | size
        code, length = ac_codes[symbol]
        writer.write_bits(code, length)
        writer.write_bits(additional_bits(coeff, size), size)
        zero_run = 0

    if zero_run > 0:
        code, length = ac_codes[EOB]
        writer.write_bits(code, length)

    return dc_value
