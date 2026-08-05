"""HSV -> RGB conversion (hand-rolled, not `colorsys` -- the standard
library module is used only as a test oracle in test_color.py, the same
"implement the low-level piece ourselves, verify against a real
implementation" split this collection uses throughout) and a palette
that maps a smooth escape-iteration count to a color: black for points
in the set, a cycling hue for everything else so the color bands don't
depend on max_iter.
"""
from __future__ import annotations

from typing import Optional, Tuple


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[float, float, float]:
    """h wraps to [0, 1); s and v are clamped to [0, 1]. Returns (r, g, b)
    each in [0, 1] -- the standard six-sector HSV->RGB algorithm."""
    h = h % 1.0
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))

    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i %= 6

    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    return v, p, q


def smooth_color(iterations: Optional[float], cycle: float = 32.0, saturation: float = 0.8) -> Tuple[int, int, int]:
    """iterations: a smooth escape count from mandelbrot/julia's
    escape_iterations(), or None for a point that never escaped (that
    is, presumed to be in the set) -- rendered as pure black."""
    if iterations is None:
        return (0, 0, 0)
    hue = (iterations / cycle) % 1.0
    r, g, b = hsv_to_rgb(hue, saturation, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))
