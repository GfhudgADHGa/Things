import pytest

from jpeg.bitwriter import BitWriter
from jpeg.entropy import additional_bits, encode_block, magnitude_category
from jpeg.huffman_tables import AC_LUMINANCE, DC_LUMINANCE, generate_codes


def test_magnitude_category():
    assert magnitude_category(0) == 0
    assert magnitude_category(1) == 1
    assert magnitude_category(-1) == 1
    assert magnitude_category(3) == 2
    assert magnitude_category(-3) == 2
    assert magnitude_category(4) == 3
    assert magnitude_category(2047) == 11
    assert magnitude_category(-2047) == 11


def test_additional_bits_positive_is_direct_binary():
    assert additional_bits(5, 3) == 0b101


def test_additional_bits_negative_uses_ones_complement_style_offset():
    # -5 has size 3 (|−5| = 5, needs 3 bits); JPEG encodes it as
    # value + (2^size - 1) = -5 + 7 = 2 = 0b010. A decoder sees the
    # leading 0 bit and knows to subtract (2^size - 1) back off.
    assert additional_bits(-5, 3) == 0b010
    assert additional_bits(-1, 1) == 0b0
    assert additional_bits(1, 1) == 0b1


def test_additional_bits_round_trips_through_decode_formula():
    for value in list(range(-100, 101)):
        size = magnitude_category(value)
        bits = additional_bits(value, size)
        if size == 0:
            decoded = 0
        else:
            threshold = 1 << (size - 1)
            decoded = bits if bits >= threshold else bits - ((1 << size) - 1)
        assert decoded == value


def _decode_bits(data: bytes, pad_bits: int = 0):
    """De-stuff and turn scan bytes back into a flat bit string, for
    testing encode_block's output by hand-decoding it independently of
    the encoder's own logic."""
    bits = []
    i = 0
    while i < len(data):
        byte = data[i]
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
        if byte == 0xFF:
            i += 2  # skip stuffed 0x00
        else:
            i += 1
    if pad_bits:
        bits = bits[:-pad_bits]
    return bits


def test_encode_block_all_zero_ac_emits_just_dc_and_eob():
    dc_codes = generate_codes(*DC_LUMINANCE)
    ac_codes = generate_codes(*AC_LUMINANCE)
    writer = BitWriter()
    zz = [5] + [0] * 63  # DC=5, no AC energy at all
    new_pred = encode_block(writer, zz, 0, dc_codes, ac_codes)
    assert new_pred == 5
    data = writer.flush()

    bits = _decode_bits(data)
    pos = 0
    # DC: size=3 for value 5 (diff=5-0=5)
    dc_code, dc_len = dc_codes[3]
    dc_bits = [int(c) for c in format(dc_code, f"0{dc_len}b")]
    assert bits[pos:pos + dc_len] == dc_bits
    pos += dc_len
    add_bits = [int(c) for c in format(additional_bits(5, 3), "03b")]
    assert bits[pos:pos + 3] == add_bits
    pos += 3
    # then EOB (symbol 0x00) from the AC table
    eob_code, eob_len = ac_codes[0x00]
    eob_bits = [int(c) for c in format(eob_code, f"0{eob_len}b")]
    assert bits[pos:pos + eob_len] == eob_bits


def test_encode_block_dc_predictor_carries_across_calls():
    dc_codes = generate_codes(*DC_LUMINANCE)
    ac_codes = generate_codes(*AC_LUMINANCE)
    writer = BitWriter()
    pred = encode_block(writer, [10] + [0] * 63, 0, dc_codes, ac_codes)
    assert pred == 10
    pred = encode_block(writer, [7] + [0] * 63, pred, dc_codes, ac_codes)
    assert pred == 7  # returns the absolute DC, not the diff


def test_encode_block_long_zero_run_uses_zrl():
    dc_codes = generate_codes(*DC_LUMINANCE)
    ac_codes = generate_codes(*AC_LUMINANCE)
    writer = BitWriter()
    zz = [0] * 64
    zz[0] = 1  # DC
    zz[20] = 3  # a nonzero AC coefficient after 19 leading zeros -> needs one ZRL (16) + run of 3
    encode_block(writer, zz, 0, dc_codes, ac_codes)
    data = writer.flush()
    bits = _decode_bits(data)

    dc_code, dc_len = dc_codes[1]  # size=1 for DC diff of 1
    pos = dc_len + 1  # DC code + 1 additional bit
    zrl_code, zrl_len = ac_codes[0xF0]
    zrl_bits = [int(c) for c in format(zrl_code, f"0{zrl_len}b")]
    assert bits[pos:pos + zrl_len] == zrl_bits
