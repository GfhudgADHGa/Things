"""The 8x8 forward DCT-II, the core transform behind JPEG's lossy
compression: it packs a block's energy into a few low-frequency
coefficients, which is what lets quantization (see quantize.py) throw
away the rest with comparatively little visible loss.

Implemented as a separable transform (1D DCT along each row, then along
each column) rather than the direct O(N^4) double sum -- mathematically
identical, ~4x fewer multiply-adds per block.

Follows ITU-T.81 Annex A's indexing exactly: input block[y][x] is a
spatial sample at row y, column x; output coeff[v][u] is the coefficient
at vertical frequency v, horizontal frequency u. That row/column
convention is what makes the standard zigzag ordering and quantization
tables (quantize.py, zigzag.py) line up correctly -- getting u and v
transposed would silently produce a technically-decodable but wrong
(mirrored across the diagonal) image.
"""
from __future__ import annotations

import math

_N = 8

# basis[k][n] = 0.5 * C(k) * cos((2n+1) * k * pi / 16)
_C = [1.0 / math.sqrt(2.0)] + [1.0] * (_N - 1)
_BASIS = [
    [0.5 * _C[k] * math.cos((2 * n + 1) * k * math.pi / 16.0) for n in range(_N)]
    for k in range(_N)
]


def _transform_1d(vec: list) -> list:
    return [sum(_BASIS[k][n] * vec[n] for n in range(_N)) for k in range(_N)]


def forward_dct_block(block: list) -> list:
    """block: 8x8 list of lists, block[y][x]. Returns an 8x8 list of
    lists, coeff[v][u] (v = vertical frequency, u = horizontal frequency;
    coeff[0][0] is the DC term)."""
    # Pass 1: transform each row (horizontal direction, x -> u)
    intermediate = [_transform_1d(block[y]) for y in range(_N)]
    # Pass 2: transform each column of the result (vertical direction, y -> v)
    coeff = [[0.0] * _N for _ in range(_N)]
    for u in range(_N):
        column = [intermediate[y][u] for y in range(_N)]
        transformed = _transform_1d(column)
        for v in range(_N):
            coeff[v][u] = transformed[v]
    return coeff
