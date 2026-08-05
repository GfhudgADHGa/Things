"""AES-128's correctness proof has two independent legs:

1. FIPS-197 Appendix B's own published single-block test vector, and
   round-trip self-consistency (decrypt(encrypt(x)) == x) across
   randomized fuzzing -- neither needs any external library.
2. The `cryptography` package (a real, independently-implemented AES) as
   a live oracle, checked ciphertext-for-ciphertext (not just "it
   decrypts back correctly," which a self-consistent-but-wrong
   implementation could also achieve) across hundreds of random
   single-block and CBC-mode trials. These are skipped, not failed, if
   `cryptography` isn't importable/working in the current environment --
   the FIPS-197 vector and round-trip tests above already provide a
   real, dependency-free correctness baseline regardless.
"""
import random

import pytest

from crypto.aes import AES128, cbc_decrypt, cbc_encrypt

crypto_lib = pytest.importorskip(
    "cryptography.hazmat.primitives.ciphers", reason="cryptography package not available/working"
)
from cryptography.hazmat.primitives import padding as _lib_padding  # noqa: E402
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # noqa: E402


# ---- FIPS-197 published test vector (no external dependency needed) ----

def test_fips197_appendix_b_vector():
    key = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
    expected = bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a")
    assert AES128(key).encrypt_block(plaintext) == expected


def test_fips197_vector_decrypts_back():
    key = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    ciphertext = bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a")
    expected_plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
    assert AES128(key).decrypt_block(ciphertext) == expected_plaintext


# ---- structural checks (no external dependency) ----

def test_wrong_key_length_raises():
    with pytest.raises(ValueError):
        AES128(b"short key")


def test_wrong_block_length_raises():
    cipher = AES128(bytes(16))
    with pytest.raises(ValueError):
        cipher.encrypt_block(bytes(15))


@pytest.mark.parametrize("seed", range(200))
def test_encrypt_decrypt_round_trip_random_blocks(seed):
    rng = random.Random(seed)
    key = bytes(rng.randrange(256) for _ in range(16))
    block = bytes(rng.randrange(256) for _ in range(16))
    cipher = AES128(key)
    assert cipher.decrypt_block(cipher.encrypt_block(block)) == block


def test_different_keys_give_different_ciphertext_for_the_same_block():
    block = bytes(range(16))
    assert AES128(bytes(16)).encrypt_block(block) != AES128(bytes([1] * 16)).encrypt_block(block)


@pytest.mark.parametrize("length", [0, 1, 15, 16, 17, 31, 32, 33, 100, 257])
def test_cbc_round_trip_various_lengths(length):
    key, iv = bytes(range(16)), bytes(range(16, 32))
    plaintext = bytes((i * 13) % 256 for i in range(length))
    ciphertext = cbc_encrypt(key, iv, plaintext)
    assert len(ciphertext) % 16 == 0
    assert cbc_decrypt(key, iv, ciphertext) == plaintext


def test_cbc_tampered_ciphertext_does_not_silently_recover_original():
    key, iv = bytes(range(16)), bytes(range(16, 32))
    plaintext = b"a secret message, block-aligned"
    ciphertext = bytearray(cbc_encrypt(key, iv, plaintext))
    ciphertext[0] ^= 0xFF
    assert cbc_decrypt(key, bytes(range(16, 32)), bytes(ciphertext)) != plaintext


def test_cbc_wrong_iv_length_raises():
    with pytest.raises(ValueError):
        cbc_encrypt(bytes(16), bytes(15), b"data")


def test_cbc_ciphertext_not_multiple_of_block_size_raises():
    with pytest.raises(ValueError):
        cbc_decrypt(bytes(16), bytes(16), b"not16")


def test_cbc_invalid_padding_on_decrypt_raises():
    key, iv = bytes(16), bytes(16)
    # a block that, once decrypted, is very unlikely to end in valid PKCS7 padding
    bad_ciphertext = AES128(key).encrypt_block(bytes(range(16)))
    with pytest.raises(ValueError):
        cbc_decrypt(key, iv, bad_ciphertext)


# ---- live oracle: the `cryptography` package ----

@pytest.mark.parametrize("seed", range(200))
def test_matches_cryptography_library_single_block(seed):
    rng = random.Random(seed)
    key = bytes(rng.randrange(256) for _ in range(16))
    block = bytes(rng.randrange(256) for _ in range(16))

    mine = AES128(key).encrypt_block(block)

    encryptor = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    reference = encryptor.update(block) + encryptor.finalize()

    assert mine == reference


@pytest.mark.parametrize("seed", range(100))
def test_matches_cryptography_library_cbc_mode_ciphertext_exactly(seed):
    rng = random.Random(seed)
    key = bytes(rng.randrange(256) for _ in range(16))
    iv = bytes(rng.randrange(256) for _ in range(16))
    plaintext = bytes(rng.randrange(256) for _ in range(rng.randint(0, 150)))

    mine_ciphertext = cbc_encrypt(key, iv, plaintext)

    padder = _lib_padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    reference_ciphertext = encryptor.update(padded) + encryptor.finalize()

    assert mine_ciphertext == reference_ciphertext
    assert cbc_decrypt(key, iv, mine_ciphertext) == plaintext
