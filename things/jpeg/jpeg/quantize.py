"""Standard JPEG quantization tables (ITU-T.81 Annex K.1, the same
"quality 50" base tables essentially every baseline encoder ships) and
the standard IJG quality-scaling formula.

Quantization is where JPEG actually throws information away: each DCT
coefficient is divided by the matching table entry and rounded to the
nearest integer. The luminance and chrominance tables are shaped very
differently on purpose -- entries grow sharply toward the bottom-right
(high spatial frequency), and the eye is far less sensitive to fine
chrominance detail than fine luminance detail, so the chrominance table
is coarser almost everywhere.
"""
from __future__ import annotations

# Row v (vertical frequency) x column u (horizontal frequency), matching
# dct.py's coeff[v][u] convention.
LUMINANCE_BASE = [
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99],
]

CHROMINANCE_BASE = [
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
]


def _quality_scale(quality: int) -> int:
    quality = max(1, min(100, quality))
    return 5000 // quality if quality < 50 else 200 - quality * 2


def scale_table(base: list, quality: int) -> list:
    """The standard IJG scaling formula: table entries shrink toward 1
    (finer, less loss) as quality rises toward 100, and grow toward 255
    (coarser, more loss) as quality drops toward 1."""
    scale = _quality_scale(quality)
    return [
        [max(1, min(255, (value * scale + 50) // 100)) for value in row]
        for row in base
    ]


def quantize_block(coeff: list, table: list) -> list:
    """coeff: 8x8 DCT coefficients. Rounds coeff[v][u] / table[v][u] to
    the nearest integer (round-half-away-from-zero, matching standard
    JPEG rounding, not Python's round-half-to-even)."""
    result = [[0] * 8 for _ in range(8)]
    for v in range(8):
        for u in range(8):
            ratio = coeff[v][u] / table[v][u]
            result[v][u] = int(ratio + 0.5) if ratio >= 0 else -int(-ratio + 0.5)
    return result
