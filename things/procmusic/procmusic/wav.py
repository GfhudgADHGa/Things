"""A minimal PCM WAV file reader/writer, built directly on the RIFF/WAVE
format spec using stdlib `struct` -- no audio libraries.
"""
from __future__ import annotations

import struct
from typing import List, Tuple

SAMPLE_RATE = 44100


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def write_wav(samples: List[float], path: str, sample_rate: int = SAMPLE_RATE) -> None:
    """Writes mono 16-bit PCM audio. `samples` are floats expected to lie in
    [-1, 1]; values outside that range are clamped rather than wrapping
    around (wrapping would turn clipping into ugly aliasing noise).
    """
    num_channels = 1
    bits_per_sample = 16
    block_align = num_channels * bits_per_sample // 8
    byte_rate = sample_rate * block_align

    pcm = bytearray()
    for s in samples:
        clamped = _clamp(s, -1.0, 1.0)
        value = int(clamped * 32767)
        pcm += struct.pack("<h", value)

    data_size = len(pcm)
    riff_size = 36 + data_size

    header = b"RIFF"
    header += struct.pack("<I", riff_size)
    header += b"WAVE"
    header += b"fmt "
    header += struct.pack("<I", 16)  # PCM fmt chunk size
    header += struct.pack("<H", 1)  # AudioFormat = PCM
    header += struct.pack("<H", num_channels)
    header += struct.pack("<I", sample_rate)
    header += struct.pack("<I", byte_rate)
    header += struct.pack("<H", block_align)
    header += struct.pack("<H", bits_per_sample)
    header += b"data"
    header += struct.pack("<I", data_size)

    with open(path, "wb") as f:
        f.write(header)
        f.write(pcm)


def read_wav(path: str) -> Tuple[List[float], int]:
    """Returns (samples, sample_rate) for a mono 16-bit PCM WAV file."""
    with open(path, "rb") as f:
        data = f.read()

    assert data[0:4] == b"RIFF" and data[8:12] == b"WAVE", "not a RIFF/WAVE file"

    pos = 12
    sample_rate = None
    num_channels = None
    bits_per_sample = None
    samples: List[float] = []

    while pos + 8 <= len(data):
        chunk_id = data[pos : pos + 4]
        (chunk_size,) = struct.unpack_from("<I", data, pos + 4)
        chunk_start = pos + 8

        if chunk_id == b"fmt ":
            (_, num_channels, sample_rate, _, _, bits_per_sample) = struct.unpack_from(
                "<HHIIHH", data, chunk_start
            )
        elif chunk_id == b"data":
            assert bits_per_sample == 16, "only 16-bit PCM is supported"
            count = chunk_size // 2
            values = struct.unpack_from(f"<{count}h", data, chunk_start)
            samples = [v / 32768.0 for v in values]

        pos = chunk_start + chunk_size + (chunk_size % 2)  # chunks are word-aligned

    assert sample_rate is not None, "no fmt chunk found"
    return samples, sample_rate
