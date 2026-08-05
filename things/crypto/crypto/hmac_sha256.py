"""HMAC (RFC 2104 / FIPS 198-1), built on this package's own sha256() --
not on Python's hashlib -- so the hash and the MAC construction here are
one self-consistent implementation, checked together against Python's
hmac+hashlib as the independent oracle in test_hmac.py.
"""
from __future__ import annotations

from .sha256 import sha256

_BLOCK_SIZE = 64  # SHA-256's internal block size, in bytes
_IPAD = 0x36
_OPAD = 0x5C


def hmac_sha256(key: bytes, message: bytes) -> bytes:
    if len(key) > _BLOCK_SIZE:
        key = sha256(key)
    key = key + b"\x00" * (_BLOCK_SIZE - len(key))

    inner_key = bytes(k ^ _IPAD for k in key)
    outer_key = bytes(k ^ _OPAD for k in key)

    return sha256(outer_key + sha256(inner_key + message))


def hmac_sha256_hex(key: bytes, message: bytes) -> str:
    return hmac_sha256(key, message).hex()
