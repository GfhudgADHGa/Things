"""The compressed file format: a small header (magic bytes, original
length, and a symbol -> frequency table) followed by the bit-packed
Huffman-coded payload. The frequency table is what lets the decoder
rebuild the exact same tree `build_tree` produced during compression --
no tree structure needs to be serialized directly.
"""
from __future__ import annotations

import struct
from collections import Counter

from .bitio import BitReader, BitWriter
from .tree import Leaf, build_code_table, build_tree

MAGIC = b"HUF1"


def compress(data: bytes) -> bytes:
    header = MAGIC + struct.pack(">I", len(data))

    if not data:
        return header + struct.pack(">H", 0)

    freqs = Counter(data)
    tree = build_tree(dict(freqs))

    if isinstance(tree, Leaf):
        # A single distinct symbol needs zero payload bits: original_length
        # (already in the header) tells the decoder exactly how many
        # copies of that one symbol to emit.
        payload = b""
    else:
        codes = build_code_table(tree)
        writer = BitWriter()
        for byte in data:
            writer.write_bits(codes[byte])
        payload = writer.getvalue()

    header += struct.pack(">H", len(freqs))
    for symbol in sorted(freqs):
        header += struct.pack(">BI", symbol, freqs[symbol])

    return header + payload


def decompress(data: bytes) -> bytes:
    if data[:4] != MAGIC:
        raise ValueError("not a valid huffman-compressed file (bad magic bytes)")

    pos = 4
    (original_length,) = struct.unpack_from(">I", data, pos)
    pos += 4
    (num_symbols,) = struct.unpack_from(">H", data, pos)
    pos += 2

    if original_length == 0:
        return b""

    freqs = {}
    for _ in range(num_symbols):
        symbol, freq = struct.unpack_from(">BI", data, pos)
        pos += 5
        freqs[symbol] = freq

    tree = build_tree(freqs)

    if isinstance(tree, Leaf):
        return bytes([tree.symbol]) * original_length

    reader = BitReader(data[pos:])
    output = bytearray()
    node = tree
    while len(output) < original_length:
        bit = reader.read_bit()
        node = node.left if bit == 0 else node.right
        if isinstance(node, Leaf):
            output.append(node.symbol)
            node = tree

    return bytes(output)
