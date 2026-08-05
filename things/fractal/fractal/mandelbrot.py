"""The Mandelbrot set: the set of complex numbers c for which the orbit
z_0=0, z_{n+1}=z_n^2+c stays bounded forever. Escape-time rendering
approximates this by iterating up to some cap and checking whether the
orbit ever leaves a disk of radius `bailout` -- once |z_n| > 2, the
orbit is *proven* to diverge to infinity (a standard result: if
|z_n| > max(|c|, 2), then |z_n| grows without bound), so bailout=2 is
the smallest value that's still mathematically correct, not just a
practical guess.

Smooth (continuous) coloring uses the escape iteration count plus a
fractional correction (`_smooth_correction`) so that color bands don't
show up as visible rings -- see color.py for how that value becomes a
pixel color.
"""
from __future__ import annotations

import math
from typing import Optional


def _smooth_correction(z_abs: float, bailout: float) -> float:
    # log(log(|z|)/log(bailout)) / log(2): the standard renormalization
    # that turns a discrete "escaped after n steps" into a continuous
    # value, by measuring *how far past* the bailout radius the orbit
    # landed relative to how fast it's diverging.
    return math.log(math.log(z_abs) / math.log(bailout)) / math.log(2)


def escape_iterations(c: complex, max_iter: int = 500, bailout: float = 2.0) -> Optional[float]:
    """Returns the smooth escape iteration count (a float >= 1), or None
    if the orbit hasn't escaped the bailout radius within max_iter
    steps -- treated as "in the set" for rendering purposes (true only
    in the limit as max_iter -> infinity; a finite render always risks
    misclassifying points arbitrarily close to the boundary, which is
    inherent to the problem, not a bug in this implementation)."""
    z = 0j
    for n in range(max_iter):
        z = z * z + c
        z_abs = abs(z)
        if z_abs > bailout:
            return (n + 1) - _smooth_correction(z_abs, bailout)
    return None


def in_main_cardioid(c: complex) -> bool:
    """Closed-form membership test for the main cardioid (the big
    heart-shaped body of the set), independent of iterating anything.
    A point here never escapes, for any max_iter -- used in
    test_mandelbrot.py to cross-check escape_iterations() against a
    completely different derivation of the same fact."""
    x, y = c.real, c.imag
    q = (x - 0.25) ** 2 + y ** 2
    return q * (q + (x - 0.25)) <= 0.25 * y ** 2


def in_period2_bulb(c: complex) -> bool:
    """Closed-form membership test for the period-2 bulb (the circular
    disk to the left of the main cardioid, centered at c=-1)."""
    x, y = c.real, c.imag
    return (x + 1) ** 2 + y ** 2 <= 1.0 / 16.0


def in_known_bounded_region(c: complex) -> bool:
    return in_main_cardioid(c) or in_period2_bulb(c)
