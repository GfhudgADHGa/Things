"""A GIF89a encoder built directly from the file format spec: a global
color table, LZW-compressed indexed image data (implemented here, not
using zlib -- GIF's LZW variant is its own thing), and a NETSCAPE2.0
looping extension for animation.
"""
from __future__ import annotations

import struct
from typing import Dict, List, Tuple

Color = Tuple[int, int, int]
Frame = List[List[Color]]


class _BitWriter:
    """Packs variable-width codes into bytes, LSB-first (as GIF requires)."""

    def __init__(self):
        self.out = bytearray()
        self.buffer = 0
        self.bits_in_buffer = 0

    def write(self, code: int, num_bits: int) -> None:
        self.buffer |= code << self.bits_in_buffer
        self.bits_in_buffer += num_bits
        while self.bits_in_buffer >= 8:
            self.out.append(self.buffer & 0xFF)
            self.buffer >>= 8
            self.bits_in_buffer -= 8

    def flush(self) -> bytes:
        if self.bits_in_buffer > 0:
            self.out.append(self.buffer & 0xFF)
            self.buffer = 0
            self.bits_in_buffer = 0
        return bytes(self.out)


def _lzw_encode(indices: List[int], min_code_size: int) -> bytes:
    clear_code = 1 << min_code_size
    end_code = clear_code + 1

    def fresh_table() -> Dict[Tuple[int, ...], int]:
        return {(i,): i for i in range(clear_code)}

    writer = _BitWriter()
    code_size = min_code_size + 1
    table = fresh_table()
    next_code = end_code + 1

    writer.write(clear_code, code_size)

    if not indices:
        writer.write(end_code, code_size)
        return writer.flush()

    w: Tuple[int, ...] = (indices[0],)
    for pixel in indices[1:]:
        wc = w + (pixel,)
        if wc in table:
            w = wc
            continue

        writer.write(table[w], code_size)

        # The code we're about to hand out is `next_code`. If it no longer
        # fits in the current code_size, grow *before* handing it out (not
        # after) -- a decoder reconstructs this same code one read later
        # (via the "code == next available code" case), by which point it
        # must already be using the wider size to parse the bits correctly.
        # Growing here, before assigning, is what keeps the two in sync.
        if next_code == (1 << code_size):
            if code_size < 12:
                code_size += 1
            else:
                writer.write(clear_code, code_size)
                table = fresh_table()
                next_code = end_code + 1
                code_size = min_code_size + 1
                w = (pixel,)
                continue

        table[wc] = next_code
        next_code += 1
        w = (pixel,)

    writer.write(table[w], code_size)
    writer.write(end_code, code_size)
    return writer.flush()


def _sub_blocks(data: bytes) -> bytes:
    out = bytearray()
    for i in range(0, len(data), 255):
        chunk = data[i : i + 255]
        out.append(len(chunk))
        out += chunk
    out.append(0)  # block terminator
    return bytes(out)


def _next_power_of_two(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


def encode_gif(frames: List[Frame], path: str, delay_ms: int = 100, loop: bool = True) -> None:
    if not frames:
        raise ValueError("need at least one frame")

    height = len(frames[0])
    width = len(frames[0][0]) if height else 0

    colors_seen = []
    color_index: Dict[Color, int] = {}
    for frame in frames:
        for row in frame:
            for pixel in row:
                if pixel not in color_index:
                    color_index[pixel] = len(colors_seen)
                    colors_seen.append(pixel)

    if len(colors_seen) > 256:
        raise ValueError(f"too many distinct colors for a GIF palette: {len(colors_seen)} > 256")

    palette_size = max(4, _next_power_of_two(len(colors_seen)))
    color_bits = palette_size.bit_length() - 1
    palette = colors_seen + [(0, 0, 0)] * (palette_size - len(colors_seen))

    out = bytearray()
    out += b"GIF89a"
    out += struct.pack("<HH", width, height)
    packed = 0b1_111_0_000 | (color_bits - 1)  # global color table, 8-bit color res, size field
    out.append(packed)
    out.append(0)  # background color index
    out.append(0)  # pixel aspect ratio

    for r, g, b in palette:
        out += bytes((r, g, b))

    if loop:
        out += bytes([0x21, 0xFF, 0x0B]) + b"NETSCAPE2.0" + bytes([0x03, 0x01]) + struct.pack("<H", 0) + bytes([0x00])

    delay_hundredths = max(1, round(delay_ms / 10))
    for frame in frames:
        out += bytes([0x21, 0xF9, 0x04, 0x00])
        out += struct.pack("<H", delay_hundredths)
        out += bytes([0x00, 0x00])  # transparent color index (unused), block terminator

        out += bytes([0x2C])
        out += struct.pack("<HHHH", 0, 0, width, height)
        out.append(0x00)  # no local color table

        indices = [color_index[pixel] for row in frame for pixel in row]
        out.append(color_bits)
        out += _sub_blocks(_lzw_encode(indices, color_bits))

    out.append(0x3B)  # trailer

    with open(path, "wb") as f:
        f.write(bytes(out))
