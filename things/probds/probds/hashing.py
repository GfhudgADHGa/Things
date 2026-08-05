"""Shared hashing utilities. Bloom filters and count-min sketches both
need several statistically-independent-enough hash functions; rather
than compute k separate cryptographic hashes (slow), both use the
Kirsch-Mitzenmacher double-hashing trick: derive two real hashes h1, h2
once, then synthesize g_i(x) = (h1 + i*h2) mod modulus for i = 0..k-1.
This is a well-known, provably-good-enough substitute for k independent
hash functions in these data structures."""
from __future__ import annotations

import hashlib
from typing import Tuple


def to_bytes(item) -> bytes:
    if isinstance(item, bytes):
        return item
    return repr(item).encode("utf-8")


def hash_pair(item) -> Tuple[int, int]:
    b = to_bytes(item)
    h1 = int.from_bytes(hashlib.sha256(b).digest()[:8], "big")
    h2 = int.from_bytes(hashlib.blake2b(b, digest_size=8).digest(), "big")
    if h2 % 2 == 0:
        h2 += 1  # keep h2 odd so repeated addition cycles through all residues mod a power of two
    return h1, h2


def kth_hash(item, i: int, modulus: int) -> int:
    h1, h2 = hash_pair(item)
    return (h1 + i * h2) % modulus


def hash64(item) -> int:
    b = to_bytes(item)
    return int.from_bytes(hashlib.sha256(b).digest()[:8], "big")


def row_hash(item, row: int, modulus: int) -> int:
    """A genuinely fresh hash per row, for structures (count-min sketch)
    where two different rows' hash functions must be independent of each
    other -- unlike kth_hash's cheap linear-combination trick, which is
    fine for Bloom filters but not safe here (see count_min_sketch.py's
    docstring for why)."""
    b = to_bytes(item) + b"|row|" + str(row).encode("ascii")
    h = int.from_bytes(hashlib.sha256(b).digest()[:8], "big")
    return h % modulus
