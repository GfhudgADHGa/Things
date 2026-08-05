"""SHA-256 (FIPS 180-4) implemented directly from the published spec:
message padding, the 64 round constants (the first 32 bits of the
fractional parts of the cube roots of the first 64 primes), and the
64-round compression function built from the standard's six functions
(the two "Sigma" functions used once per round on a/e, the two "sigma"
functions used in message schedule expansion, plus Ch and Maj).

Every value here is a 32-bit unsigned word, and Python integers don't
wrap at 32 bits on their own the way a real CPU register would -- every
addition and left-shift below is explicitly masked with `& _MASK32`.
Forgetting even one of those would silently work for small/lucky inputs
and then diverge from the real algorithm on others, which is exactly
the kind of bug the hashlib oracle comparison in test_sha256.py is
there to catch.
"""
from __future__ import annotations

_MASK32 = 0xFFFFFFFF

_H0 = [
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
    0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19,
]

_K = [
    0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
    0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3, 0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
    0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
    0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
    0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13, 0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
    0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
    0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
    0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208, 0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
]


def _rotr(x: int, n: int) -> int:
    return ((x >> n) | (x << (32 - n))) & _MASK32


def _pad(message: bytes) -> bytes:
    length_bits = (len(message) * 8) & 0xFFFFFFFFFFFFFFFF
    padded = message + b"\x80"
    while len(padded) % 64 != 56:
        padded += b"\x00"
    return padded + length_bits.to_bytes(8, "big")


def sha256(message: bytes) -> bytes:
    h = list(_H0)
    padded = _pad(message)

    for chunk_start in range(0, len(padded), 64):
        chunk = padded[chunk_start:chunk_start + 64]
        w = [int.from_bytes(chunk[i:i + 4], "big") for i in range(0, 64, 4)]
        for i in range(16, 64):
            s0 = _rotr(w[i - 15], 7) ^ _rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
            s1 = _rotr(w[i - 2], 17) ^ _rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
            w.append((w[i - 16] + s0 + w[i - 7] + s1) & _MASK32)

        a, b, c, d, e, f, g, hh = h
        for i in range(64):
            big_s1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
            ch = (e & f) ^ ((~e) & g & _MASK32)
            temp1 = (hh + big_s1 + ch + _K[i] + w[i]) & _MASK32
            big_s0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (big_s0 + maj) & _MASK32
            hh, g, f, e, d, c, b, a = g, f, e, (d + temp1) & _MASK32, c, b, a, (temp1 + temp2) & _MASK32

        h = [
            (h[0] + a) & _MASK32, (h[1] + b) & _MASK32, (h[2] + c) & _MASK32, (h[3] + d) & _MASK32,
            (h[4] + e) & _MASK32, (h[5] + f) & _MASK32, (h[6] + g) & _MASK32, (h[7] + hh) & _MASK32,
        ]

    return b"".join(word.to_bytes(4, "big") for word in h)


def sha256_hex(message: bytes) -> str:
    return sha256(message).hex()
