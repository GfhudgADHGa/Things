"""Assembles a complete baseline JFIF/JPEG file: SOI, an APP0 JFIF
header, DQT (quantization tables), SOF0 (frame header, baseline DCT),
DHT (Huffman tables), SOS (scan header) plus the already-entropy-coded
scan data, and EOI. Every marker except the entropy-coded scan data
itself is a short, fixed-format binary segment straight out of ITU-T.81.
"""
from __future__ import annotations

from .zigzag import ZIGZAG

SOI = b"\xff\xd8"
EOI = b"\xff\xd9"


def _u16(value: int) -> bytes:
    return value.to_bytes(2, "big")


def _app0_jfif() -> bytes:
    payload = (
        b"JFIF\x00"
        b"\x01\x01"  # version 1.1
        b"\x00"  # density units: 0 = no units, aspect ratio only
        + _u16(1) + _u16(1)  # Xdensity, Ydensity
        + b"\x00\x00"  # no embedded thumbnail
    )
    return b"\xff\xe0" + _u16(len(payload) + 2) + payload


def _dqt(table_id: int, table: list) -> bytes:
    zigzag_values = bytes(table[v][u] for v, u in ZIGZAG)
    payload = bytes([table_id]) + zigzag_values
    return b"\xff\xdb" + _u16(len(payload) + 2) + payload


def _sof0(width: int, height: int, components: list) -> bytes:
    # components: list of (component_id, h_sampling, v_sampling, quant_table_id)
    payload = bytes([8]) + _u16(height) + _u16(width) + bytes([len(components)])
    for comp_id, h, v, qt in components:
        payload += bytes([comp_id, (h << 4) | v, qt])
    return b"\xff\xc0" + _u16(len(payload) + 2) + payload


def _dht(table_class: int, table_id: int, bits: list, huffval: list) -> bytes:
    payload = bytes([(table_class << 4) | table_id]) + bytes(bits) + bytes(huffval)
    return b"\xff\xc4" + _u16(len(payload) + 2) + payload


def _sos(components: list) -> bytes:
    # components: list of (component_id, dc_table_id, ac_table_id)
    payload = bytes([len(components)])
    for comp_id, dc_id, ac_id in components:
        payload += bytes([comp_id, (dc_id << 4) | ac_id])
    payload += bytes([0, 63, 0])  # spectral selection 0..63, no successive approx
    return b"\xff\xda" + _u16(len(payload) + 2) + payload


def build_jpeg(
    width: int,
    height: int,
    luma_quant: list,
    chroma_quant: list,
    huffman_tables: dict,
    entropy_data: bytes,
) -> bytes:
    """huffman_tables: {"dc_luma": (bits, vals), "ac_luma": (...),
    "dc_chroma": (...), "ac_chroma": (...)}. Components are always Y=1,
    Cb=2, Cr=3 at 1x1 sampling (no chroma subsampling): Y uses quant
    table 0 / huffman table set 0, Cb and Cr use quant table 1 / set 1.
    """
    frame_components = [(1, 1, 1, 0), (2, 1, 1, 1), (3, 1, 1, 1)]
    scan_components = [(1, 0, 0), (2, 1, 1), (3, 1, 1)]

    parts = [
        SOI,
        _app0_jfif(),
        _dqt(0, luma_quant),
        _dqt(1, chroma_quant),
        _sof0(width, height, frame_components),
        _dht(0, 0, *huffman_tables["dc_luma"]),
        _dht(1, 0, *huffman_tables["ac_luma"]),
        _dht(0, 1, *huffman_tables["dc_chroma"]),
        _dht(1, 1, *huffman_tables["ac_chroma"]),
        _sos(scan_components),
        entropy_data,
        EOI,
    ]
    return b"".join(parts)
