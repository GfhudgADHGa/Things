"""Cross-checked against Python's hmac+hashlib -- and specifically
fuzzed across the 64-byte block-size boundary for the key, since HMAC's
"hash the key first if it's longer than one block" rule (RFC 2104) is
exactly the kind of conditional branch a hand-transcribed implementation
could plausibly get backwards or off-by-one on."""
import hashlib
import hmac
import random

import pytest

from crypto.hmac_sha256 import hmac_sha256_hex


def test_rfc4231_case_1():
    key = bytes.fromhex("0b" * 20)
    msg = b"Hi There"
    assert hmac_sha256_hex(key, msg) == hmac.new(key, msg, hashlib.sha256).hexdigest()


def test_rfc4231_case_2_short_key_and_ascii_message():
    key = b"Jefe"
    msg = b"what do ya want for nothing?"
    assert hmac_sha256_hex(key, msg) == hmac.new(key, msg, hashlib.sha256).hexdigest()


def test_rfc4231_case_6_key_longer_than_block_size():
    key = bytes.fromhex("aa" * 131)  # 131 bytes > 64-byte SHA-256 block size
    msg = b"Test Using Larger Than Block-Size Key - Hash Key First"
    assert hmac_sha256_hex(key, msg) == hmac.new(key, msg, hashlib.sha256).hexdigest()


@pytest.mark.parametrize("key_len", [0, 1, 63, 64, 65, 100, 131, 200])
def test_key_length_boundary_around_block_size(key_len):
    key = bytes((i * 7) % 256 for i in range(key_len))
    msg = b"boundary test message"
    assert hmac_sha256_hex(key, msg) == hmac.new(key, msg, hashlib.sha256).hexdigest()


@pytest.mark.parametrize("seed", range(300))
def test_fuzz_random_keys_and_messages(seed):
    rng = random.Random(seed)
    key = bytes(rng.randrange(256) for _ in range(rng.randint(0, 150)))
    msg = bytes(rng.randrange(256) for _ in range(rng.randint(0, 300)))
    assert hmac_sha256_hex(key, msg) == hmac.new(key, msg, hashlib.sha256).hexdigest()


def test_different_keys_give_different_macs_for_the_same_message():
    msg = b"same message"
    assert hmac_sha256_hex(b"key1", msg) != hmac_sha256_hex(b"key2", msg)
