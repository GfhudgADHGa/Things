"""MSB-first bit packing for the entropy-coded JPEG scan data, including
the mandatory 0xFF -> 0xFF 0x00 byte-stuffing rule: a raw 0xFF byte in
the entropy stream would otherwise be indistinguishable from the start
of a marker (all JPEG markers begin with 0xFF), so the spec requires a
stuffed 0x00 after every literal 0xFF byte in scan data."""
from __future__ import annotations


class BitWriter:
    def __init__(self):
        self._bytes = bytearray()
        self._bit_buffer = 0
        self._bit_count = 0

    def write_bits(self, value: int, length: int) -> None:
        if length == 0:
            return
        self._bit_buffer = (self._bit_buffer << length) | (value & ((1 << length) - 1))
        self._bit_count += length
        while self._bit_count >= 8:
            self._bit_count -= 8
            byte = (self._bit_buffer >> self._bit_count) & 0xFF
            self._emit_byte(byte)
        if self._bit_count:
            self._bit_buffer &= (1 << self._bit_count) - 1
        else:
            self._bit_buffer = 0

    def _emit_byte(self, byte: int) -> None:
        self._bytes.append(byte)
        if byte == 0xFF:
            self._bytes.append(0x00)

    def flush(self) -> bytes:
        """Pad the final partial byte with 1-bits (standard JPEG
        practice) and return the complete stuffed byte stream."""
        if self._bit_count > 0:
            pad_length = 8 - self._bit_count
            self.write_bits((1 << pad_length) - 1, pad_length)
        return bytes(self._bytes)
