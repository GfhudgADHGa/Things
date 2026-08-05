"""Binary format for one write-ahead-log record, plus a crash-tolerant reader.

Layout (all integers big-endian):

    [4 bytes body_len][4 bytes crc32(body)][body]

    body := op(1 byte) key_len(4) key value_len(4) value    # PUT
          | op(1 byte) key_len(4) key                        # DELETE

The length prefix and checksum exist for exactly one reason: so that a
truncated write (the process was killed mid-`write()`) or a bit-flipped
byte (partial disk corruption) can be detected and discarded during
recovery, instead of either crashing the reader or silently returning
corrupted data.
"""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from typing import BinaryIO, List, Optional, Tuple

OP_PUT = 1
OP_DELETE = 2

_HEADER = struct.Struct(">II")  # body_len, crc32
_U32 = struct.Struct(">I")
_U8 = struct.Struct(">B")


@dataclass
class Record:
    op: int
    key: bytes
    value: Optional[bytes]


def encode_record(op: int, key: bytes, value: Optional[bytes] = None) -> bytes:
    body = _U8.pack(op) + _U32.pack(len(key)) + key
    if op == OP_PUT:
        assert value is not None
        body += _U32.pack(len(value)) + value
    checksum = zlib.crc32(body) & 0xFFFFFFFF
    return _HEADER.pack(len(body), checksum) + body


def _decode_body(body: bytes) -> Optional[Record]:
    if len(body) < 5:
        return None
    op = body[0]
    if op not in (OP_PUT, OP_DELETE):
        return None
    (key_len,) = _U32.unpack_from(body, 1)
    key_start = 5
    key_end = key_start + key_len
    if key_end > len(body):
        return None
    key = body[key_start:key_end]

    if op == OP_DELETE:
        if key_end != len(body):
            return None
        return Record(op, key, None)

    # OP_PUT
    if key_end + 4 > len(body):
        return None
    (value_len,) = _U32.unpack_from(body, key_end)
    value_start = key_end + 4
    value_end = value_start + value_len
    if value_end != len(body):
        return None
    return Record(op, key, body[value_start:value_end])


def read_valid_records(f: BinaryIO) -> Tuple[List[Record], int]:
    """Reads records from the current file position until EOF, a truncated
    record, or a checksum mismatch. Returns (records, valid_end_offset) --
    valid_end_offset is the byte offset just past the last good record, so
    the caller can truncate away anything corrupt/incomplete that follows.
    """
    records: List[Record] = []
    valid_end = f.tell()

    while True:
        header_bytes = f.read(_HEADER.size)
        if len(header_bytes) < _HEADER.size:
            break  # clean EOF, or a torn write of the header itself

        body_len, expected_crc = _HEADER.unpack(header_bytes)
        body = f.read(body_len)
        if len(body) < body_len:
            break  # torn write: process died mid-write of this record

        if (zlib.crc32(body) & 0xFFFFFFFF) != expected_crc:
            break  # corruption: bit flip, or a torn write that happened to
            # land on a body_len/crc boundary

        record = _decode_body(body)
        if record is None:
            break  # checksum matched but the body doesn't parse -- treat
            # as corrupt rather than raising

        records.append(record)
        valid_end = f.tell()

    return records, valid_end
