"""AES-128 (FIPS-197) in CBC mode with PKCS#7 padding, implemented
directly from the standard's four round transformations -- SubBytes,
ShiftRows, MixColumns, AddRoundKey -- plus key expansion. AES-128 only
(a 16-byte key, 10 rounds); AES-192/256 would only need a longer key
schedule and one or two more rounds, but are out of scope here.

The S-box is the single most error-prone piece of AES to transcribe by
hand -- 256 bytes with no simple closed-form shortcut, unlike the round
constants (which this module derives from GF(2^8) arithmetic instead of
hardcoding, specifically to have fewer opportunities to get a magic
number wrong). The inverse S-box is *computed* from the forward one
(inv_sbox[sbox[x]] = x) rather than transcribed as a second 256-byte
table, which halves that risk and guarantees the two tables are true
inverses of each other by construction -- though being true inverses of
each other only proves internal self-consistency, not that the S-box
matches the real AES standard. That's exactly why this module is
checked against the `cryptography` library and FIPS-197's own published
test vector in test_aes.py, not just against its own round-trip.
"""
from __future__ import annotations

_SBOX = bytes.fromhex(
    "637c777bf26b6fc53001672bfed7ab76"
    "ca82c97dfa5947f0add4a2af9ca472c0"
    "b7fd9326363ff7cc34a5e5f171d83115"
    "04c723c31896059a071280e2eb27b275"
    "09832c1a1b6e5aa0523bd6b329e32f84"
    "53d100ed20fcb15b6acbbe394a4c58cf"
    "d0efaafb434d338545f9027f503c9fa8"
    "51a3408f929d38f5bcb6da2110fff3d2"
    "cd0c13ec5f974417c4a77e3d645d1973"
    "60814fdc222a908846eeb814de5e0bdb"
    "e0323a0a4906245cc2d3ac629195e479"
    "e7c8376d8dd54ea96c56f4ea657aae08"
    "ba78252e1ca6b4c6e8dd741f4bbd8b8a"
    "703eb5664803f60e613557b986c11d9e"
    "e1f8981169d98e949b1e87e9ce5528df"
    "8ca1890dbfe6426841992d0fb054bb16"
)
assert len(_SBOX) == 256

_INV_SBOX = bytearray(256)
for _i, _v in enumerate(_SBOX):
    _INV_SBOX[_v] = _i
_INV_SBOX = bytes(_INV_SBOX)


def _gf_mul(a: int, b: int) -> int:
    """Multiplication in GF(2^8) with AES's reduction polynomial
    x^8+x^4+x^3+x+1 (0x11B) -- used both for MixColumns and to derive
    the round constants below, so there's exactly one place this
    arithmetic is defined."""
    result = 0
    for _ in range(8):
        if b & 1:
            result ^= a
        carry = a & 0x80
        a = (a << 1) & 0xFF
        if carry:
            a ^= 0x1B
        b >>= 1
    return result


_RCON = [1]
for _ in range(9):
    _RCON.append(_gf_mul(_RCON[-1], 2))


def _sub_word(word: bytes) -> bytes:
    return bytes(_SBOX[b] for b in word)


def _rot_word(word: bytes) -> bytes:
    return word[1:] + word[:1]


def _key_expansion(key: bytes) -> list:
    nk = 4  # key length in 32-bit words, for AES-128
    words = [key[4 * i:4 * i + 4] for i in range(nk)]
    for i in range(nk, 4 * 11):
        temp = words[i - 1]
        if i % nk == 0:
            rotated = _sub_word(_rot_word(temp))
            temp = bytes([rotated[0] ^ _RCON[i // nk - 1]]) + rotated[1:]
        words.append(bytes(a ^ b for a, b in zip(words[i - nk], temp)))
    return [b"".join(words[4 * r:4 * r + 4]) for r in range(11)]


def _bytes_to_state(block: bytes) -> list:
    return [[block[row + 4 * col] for col in range(4)] for row in range(4)]


def _state_to_bytes(state: list) -> bytes:
    return bytes(state[row][col] for col in range(4) for row in range(4))


def _add_round_key(state: list, round_key: bytes) -> None:
    rk = _bytes_to_state(round_key)
    for r in range(4):
        for c in range(4):
            state[r][c] ^= rk[r][c]


def _sub_bytes(state: list) -> None:
    for r in range(4):
        for c in range(4):
            state[r][c] = _SBOX[state[r][c]]


def _inv_sub_bytes(state: list) -> None:
    for r in range(4):
        for c in range(4):
            state[r][c] = _INV_SBOX[state[r][c]]


def _shift_rows(state: list) -> None:
    for r in range(1, 4):
        state[r] = state[r][r:] + state[r][:r]


def _inv_shift_rows(state: list) -> None:
    for r in range(1, 4):
        state[r] = state[r][-r:] + state[r][:-r]


def _mix_columns(state: list) -> None:
    for c in range(4):
        col = [state[r][c] for r in range(4)]
        state[0][c] = _gf_mul(col[0], 2) ^ _gf_mul(col[1], 3) ^ col[2] ^ col[3]
        state[1][c] = col[0] ^ _gf_mul(col[1], 2) ^ _gf_mul(col[2], 3) ^ col[3]
        state[2][c] = col[0] ^ col[1] ^ _gf_mul(col[2], 2) ^ _gf_mul(col[3], 3)
        state[3][c] = _gf_mul(col[0], 3) ^ col[1] ^ col[2] ^ _gf_mul(col[3], 2)


def _inv_mix_columns(state: list) -> None:
    for c in range(4):
        col = [state[r][c] for r in range(4)]
        state[0][c] = _gf_mul(col[0], 14) ^ _gf_mul(col[1], 11) ^ _gf_mul(col[2], 13) ^ _gf_mul(col[3], 9)
        state[1][c] = _gf_mul(col[0], 9) ^ _gf_mul(col[1], 14) ^ _gf_mul(col[2], 11) ^ _gf_mul(col[3], 13)
        state[2][c] = _gf_mul(col[0], 13) ^ _gf_mul(col[1], 9) ^ _gf_mul(col[2], 14) ^ _gf_mul(col[3], 11)
        state[3][c] = _gf_mul(col[0], 11) ^ _gf_mul(col[1], 13) ^ _gf_mul(col[2], 9) ^ _gf_mul(col[3], 14)


class AES128:
    def __init__(self, key: bytes):
        if len(key) != 16:
            raise ValueError("AES-128 key must be exactly 16 bytes")
        self.round_keys = _key_expansion(key)

    def encrypt_block(self, block: bytes) -> bytes:
        if len(block) != 16:
            raise ValueError("block must be exactly 16 bytes")
        state = _bytes_to_state(block)
        _add_round_key(state, self.round_keys[0])
        for round_num in range(1, 10):
            _sub_bytes(state)
            _shift_rows(state)
            _mix_columns(state)
            _add_round_key(state, self.round_keys[round_num])
        _sub_bytes(state)
        _shift_rows(state)
        _add_round_key(state, self.round_keys[10])
        return _state_to_bytes(state)

    def decrypt_block(self, block: bytes) -> bytes:
        if len(block) != 16:
            raise ValueError("block must be exactly 16 bytes")
        state = _bytes_to_state(block)
        _add_round_key(state, self.round_keys[10])
        for round_num in range(9, 0, -1):
            _inv_shift_rows(state)
            _inv_sub_bytes(state)
            _add_round_key(state, self.round_keys[round_num])
            _inv_mix_columns(state)
        _inv_shift_rows(state)
        _inv_sub_bytes(state)
        _add_round_key(state, self.round_keys[0])
        return _state_to_bytes(state)


def _pkcs7_pad(data: bytes, block_size: int = 16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len]) * pad_len


def _pkcs7_unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError("cannot unpad empty data")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > 16 or data[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("invalid PKCS#7 padding")
    return data[:-pad_len]


def cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    if len(iv) != 16:
        raise ValueError("IV must be exactly 16 bytes")
    cipher = AES128(key)
    padded = _pkcs7_pad(plaintext)
    ciphertext = bytearray()
    previous = iv
    for i in range(0, len(padded), 16):
        block = bytes(a ^ b for a, b in zip(padded[i:i + 16], previous))
        encrypted = cipher.encrypt_block(block)
        ciphertext += encrypted
        previous = encrypted
    return bytes(ciphertext)


def cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    if len(iv) != 16:
        raise ValueError("IV must be exactly 16 bytes")
    if len(ciphertext) % 16 != 0:
        raise ValueError("ciphertext length must be a multiple of 16 bytes")
    cipher = AES128(key)
    plaintext = bytearray()
    previous = iv
    for i in range(0, len(ciphertext), 16):
        block = ciphertext[i:i + 16]
        decrypted = cipher.decrypt_block(block)
        plaintext += bytes(a ^ b for a, b in zip(decrypted, previous))
        previous = block
    return _pkcs7_unpad(bytes(plaintext))
