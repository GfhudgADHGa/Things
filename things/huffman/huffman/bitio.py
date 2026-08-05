"""Packing/unpacking individual bits into bytes, MSB-first."""
from __future__ import annotations


class BitWriter:
    def __init__(self):
        self._bytes = bytearray()
        self._current = 0
        self._nbits = 0

    def write_bit(self, bit: int) -> None:
        self._current = (self._current << 1) | bit
        self._nbits += 1
        if self._nbits == 8:
            self._bytes.append(self._current)
            self._current = 0
            self._nbits = 0

    def write_bits(self, bits: str) -> None:
        for ch in bits:
            self.write_bit(1 if ch == "1" else 0)

    def getvalue(self) -> bytes:
        if self._nbits == 0:
            return bytes(self._bytes)
        padded = self._current << (8 - self._nbits)
        return bytes(self._bytes) + bytes([padded])


class BitReader:
    def __init__(self, data: bytes):
        self._data = data
        self._byte_pos = 0
        self._bit_pos = 0  # 0..7, counting from the MSB of the current byte

    def read_bit(self) -> int:
        byte = self._data[self._byte_pos]
        bit = (byte >> (7 - self._bit_pos)) & 1
        self._bit_pos += 1
        if self._bit_pos == 8:
            self._bit_pos = 0
            self._byte_pos += 1
        return bit
