"""Top-level baseline JPEG encoder: RGB pixels in, a complete JFIF file's
bytes out. Ties together color conversion, block DCT, quantization,
zigzag ordering, and entropy coding (see each module's docstring for the
step it's responsible for). No chroma subsampling (4:4:4) -- every MCU
is exactly one 8x8 block per component -- which keeps the block/MCU
bookkeeping simple at the cost of a somewhat larger file than a real
encoder's default 4:2:0 subsampling would produce.
"""
from __future__ import annotations

from .bitwriter import BitWriter
from .color import rgb_to_ycbcr
from .dct import forward_dct_block
from .entropy import encode_block
from .huffman_tables import (
    AC_CHROMINANCE, AC_LUMINANCE, DC_CHROMINANCE, DC_LUMINANCE, generate_codes,
)
from .quantize import CHROMINANCE_BASE, LUMINANCE_BASE, quantize_block, scale_table
from .writer import build_jpeg
from .zigzag import zigzag_order


def _ceil_multiple(n: int, m: int) -> int:
    return ((n + m - 1) // m) * m


def _build_planes(pixels: list, width: int, height: int) -> tuple:
    """pixels: list of `height` rows, each a list of `width` (r, g, b)
    tuples. Returns (Y, Cb, Cr) planes padded up to 8x8-block-aligned
    dimensions, padding by replicating the nearest real edge pixel so the
    padding blocks don't introduce sharp fake edges into the DCT."""
    padded_w = _ceil_multiple(width, 8)
    padded_h = _ceil_multiple(height, 8)

    y_plane = [[0.0] * padded_w for _ in range(padded_h)]
    cb_plane = [[0.0] * padded_w for _ in range(padded_h)]
    cr_plane = [[0.0] * padded_w for _ in range(padded_h)]

    for py in range(padded_h):
        src_y = min(py, height - 1)
        row = pixels[src_y]
        for px in range(padded_w):
            src_x = min(px, width - 1)
            r, g, b = row[src_x]
            y, cb, cr = rgb_to_ycbcr(r, g, b)
            y_plane[py][px] = y
            cb_plane[py][px] = cb
            cr_plane[py][px] = cr

    return y_plane, cb_plane, cr_plane


def _extract_block(plane: list, block_row: int, block_col: int) -> list:
    y0, x0 = block_row * 8, block_col * 8
    return [[plane[y0 + dy][x0 + dx] - 128.0 for dx in range(8)] for dy in range(8)]


def encode_rgb_image(pixels: list, width: int, height: int, quality: int = 75) -> bytes:
    """pixels: list of `height` rows of `width` (r, g, b) int tuples."""
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")

    y_plane, cb_plane, cr_plane = _build_planes(pixels, width, height)
    padded_h, padded_w = len(y_plane), len(y_plane[0])
    blocks_h, blocks_w = padded_h // 8, padded_w // 8

    luma_quant = scale_table(LUMINANCE_BASE, quality)
    chroma_quant = scale_table(CHROMINANCE_BASE, quality)

    dc_luma_codes = generate_codes(*DC_LUMINANCE)
    ac_luma_codes = generate_codes(*AC_LUMINANCE)
    dc_chroma_codes = generate_codes(*DC_CHROMINANCE)
    ac_chroma_codes = generate_codes(*AC_CHROMINANCE)

    writer = BitWriter()
    dc_pred = {"y": 0, "cb": 0, "cr": 0}

    for block_row in range(blocks_h):
        for block_col in range(blocks_w):
            for plane, key, quant, dc_codes, ac_codes in (
                (y_plane, "y", luma_quant, dc_luma_codes, ac_luma_codes),
                (cb_plane, "cb", chroma_quant, dc_chroma_codes, ac_chroma_codes),
                (cr_plane, "cr", chroma_quant, dc_chroma_codes, ac_chroma_codes),
            ):
                block = _extract_block(plane, block_row, block_col)
                coeff = forward_dct_block(block)
                quantized = quantize_block(coeff, quant)
                zz = zigzag_order(quantized)
                dc_pred[key] = encode_block(writer, zz, dc_pred[key], dc_codes, ac_codes)

    entropy_data = writer.flush()

    return build_jpeg(
        width,
        height,
        luma_quant,
        chroma_quant,
        {
            "dc_luma": DC_LUMINANCE,
            "ac_luma": AC_LUMINANCE,
            "dc_chroma": DC_CHROMINANCE,
            "ac_chroma": AC_CHROMINANCE,
        },
        entropy_data,
    )
