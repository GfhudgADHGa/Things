"""The correctness proof for sha256.py: Python's own hashlib as a live
oracle, across the standard NIST test vectors, the padding-boundary
lengths where a hand-transcribed implementation is most likely to have
an off-by-one, and randomized fuzzing."""
import hashlib
import random

import pytest

from crypto.sha256 import sha256, sha256_hex


def test_empty_string():
    assert sha256_hex(b"") == hashlib.sha256(b"").hexdigest()


def test_nist_vector_abc():
    assert sha256_hex(b"abc") == hashlib.sha256(b"abc").hexdigest()


def test_nist_vector_two_block_message():
    msg = b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"
    assert sha256_hex(msg) == hashlib.sha256(msg).hexdigest()


def test_nist_vector_one_million_a():
    msg = b"a" * 1_000_000
    assert sha256_hex(msg) == hashlib.sha256(msg).hexdigest()


@pytest.mark.parametrize("length", [
    0, 1, 54, 55, 56, 57, 63, 64, 65, 119, 120, 121, 127, 128, 129, 200,
])
def test_padding_boundary_lengths(length):
    # 55/56/57 straddle the "does the 0x80 + length still fit in this
    # 64-byte block" boundary; 119/120/121 do the same one block later.
    # A padding off-by-one would most likely only show up right here.
    msg = bytes((i * 37) % 256 for i in range(length))
    assert sha256_hex(msg) == hashlib.sha256(msg).hexdigest()


@pytest.mark.parametrize("seed", range(300))
def test_fuzz_random_messages(seed):
    rng = random.Random(seed)
    msg = bytes(rng.randrange(256) for _ in range(rng.randint(0, 300)))
    assert sha256_hex(msg) == hashlib.sha256(msg).hexdigest()


def test_returns_32_raw_bytes():
    assert len(sha256(b"anything")) == 32


def test_different_inputs_give_different_hashes():
    assert sha256_hex(b"a") != sha256_hex(b"b")
