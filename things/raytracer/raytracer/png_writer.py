"""Writes a grid of (r, g, b) rows to a PNG file, using Pillow if available,
falling back to a small hand-rolled PNG encoder (stdlib zlib only) otherwise.
"""
from __future__ import annotations

import struct
import zlib
from typing import List, Tuple

Color = Tuple[int, int, int]


def write_png(rows: List[List[Color]], path: str) -> None:
    try:
        from PIL import Image

        height = len(rows)
        width = len(rows[0])
        img = Image.new("RGB", (width, height))
        img.putdata([px for row in rows for px in row])
        img.save(path)
        return
    except ImportError:
        _write_png_stdlib(rows, path)


def _write_png_stdlib(rows: List[List[Color]], path: str) -> None:
    height = len(rows)
    width = len(rows[0])

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data))
        )

    raw = bytearray()
    for row in rows:
        raw.append(0)  # no filter
        for r, g, b in row:
            raw += bytes((r, g, b))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))
