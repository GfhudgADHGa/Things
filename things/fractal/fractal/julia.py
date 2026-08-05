"""Julia sets: same escape-time iteration z_{n+1} = z_n^2 + c as the
Mandelbrot set, but with c held *fixed* for the whole image and the
starting point z_0 varying per pixel instead -- the Mandelbrot set is,
in a sense, a map of which c values produce a connected (in one piece)
Julia set, but the two are rendered by walking the same formula in
different directions.
"""
from __future__ import annotations

from typing import Optional

from .mandelbrot import _smooth_correction


def escape_iterations(z0: complex, c: complex, max_iter: int = 500, bailout: float = 2.0) -> Optional[float]:
    z = z0
    for n in range(max_iter):
        z = z * z + c
        z_abs = abs(z)
        if z_abs > bailout:
            return (n + 1) - _smooth_correction(z_abs, bailout)
    return None
