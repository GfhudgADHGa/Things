"""Renders a Mandelbrot or Julia set to a grid of RGB pixels, given a
viewport in the complex plane (a center point and a width spanning the
image horizontally), by mapping each pixel to a complex number and
coloring it via escape_iterations() + smooth_color().
"""
from __future__ import annotations

from typing import List, Tuple

from .color import smooth_color
from .julia import escape_iterations as julia_escape_iterations
from .mandelbrot import escape_iterations as mandelbrot_escape_iterations


def pixel_to_complex(
    px: int, py: int, width: int, height: int, center: complex, plane_width: float
) -> complex:
    plane_height = plane_width * height / width
    x = center.real + (px / width - 0.5) * plane_width
    y = center.imag - (py / height - 0.5) * plane_height  # image y grows downward; the complex plane's doesn't
    return complex(x, y)


def render_mandelbrot(
    width: int,
    height: int,
    center: complex = -0.5 + 0j,
    plane_width: float = 3.0,
    max_iter: int = 500,
    bailout: float = 2.0,
    cycle: float = 32.0,
) -> List[List[Tuple[int, int, int]]]:
    rows = []
    for py in range(height):
        row = []
        for px in range(width):
            c = pixel_to_complex(px, py, width, height, center, plane_width)
            iterations = mandelbrot_escape_iterations(c, max_iter, bailout)
            row.append(smooth_color(iterations, cycle))
        rows.append(row)
    return rows


def render_julia(
    c: complex,
    width: int,
    height: int,
    center: complex = 0j,
    plane_width: float = 3.0,
    max_iter: int = 500,
    bailout: float = 2.0,
    cycle: float = 32.0,
) -> List[List[Tuple[int, int, int]]]:
    rows = []
    for py in range(height):
        row = []
        for px in range(width):
            z0 = pixel_to_complex(px, py, width, height, center, plane_width)
            iterations = julia_escape_iterations(z0, c, max_iter, bailout)
            row.append(smooth_color(iterations, cycle))
        rows.append(row)
    return rows
