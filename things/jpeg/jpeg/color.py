"""RGB <-> YCbCr color conversion, ITU-R BT.601 / JFIF coefficients (the
same constants libjpeg and every standard JPEG encoder use, so a decoder
expecting a standard JFIF file interprets the channels correctly)."""
from __future__ import annotations


def rgb_to_ycbcr(r: int, g: int, b: int) -> tuple:
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cb = -0.168736 * r - 0.331264 * g + 0.5 * b + 128.0
    cr = 0.5 * r - 0.418688 * g - 0.081312 * b + 128.0
    return y, cb, cr
