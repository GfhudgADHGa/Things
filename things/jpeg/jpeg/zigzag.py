"""The standard JPEG zigzag scan order: reorders an 8x8 coefficient
matrix (v, u) into a 64-element sequence that visits low frequencies
first. After quantization, most high-frequency coefficients are zero;
zigzag order clusters those zeros together at the tail so the run-length
step (entropy.py) has long runs to compress instead of scattered ones.
"""
from __future__ import annotations

# ZIGZAG[k] = (v, u) coordinate visited at scan position k.
ZIGZAG = [
    (0, 0), (0, 1), (1, 0), (2, 0), (1, 1), (0, 2), (0, 3), (1, 2),
    (2, 1), (3, 0), (4, 0), (3, 1), (2, 2), (1, 3), (0, 4), (0, 5),
    (1, 4), (2, 3), (3, 2), (4, 1), (5, 0), (6, 0), (5, 1), (4, 2),
    (3, 3), (2, 4), (1, 5), (0, 6), (0, 7), (1, 6), (2, 5), (3, 4),
    (4, 3), (5, 2), (6, 1), (7, 0), (7, 1), (6, 2), (5, 3), (4, 4),
    (3, 5), (2, 6), (1, 7), (2, 7), (3, 6), (4, 5), (5, 4), (6, 3),
    (7, 2), (7, 3), (6, 4), (5, 5), (4, 6), (3, 7), (4, 7), (5, 6),
    (6, 5), (7, 4), (7, 5), (6, 6), (5, 7), (6, 7), (7, 6), (7, 7),
]

assert len(ZIGZAG) == 64
assert set(ZIGZAG) == {(v, u) for v in range(8) for u in range(8)}


def zigzag_order(coeff: list) -> list:
    """coeff: 8x8 list of lists, coeff[v][u]. Returns the 64 values in
    zigzag scan order."""
    return [coeff[v][u] for v, u in ZIGZAG]
