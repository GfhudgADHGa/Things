import pytest

from jpeg.huffman_tables import (
    AC_CHROMINANCE, AC_LUMINANCE, DC_CHROMINANCE, DC_LUMINANCE, generate_codes,
)

ALL_TABLES = {
    "dc_luma": DC_LUMINANCE,
    "dc_chroma": DC_CHROMINANCE,
    "ac_luma": AC_LUMINANCE,
    "ac_chroma": AC_CHROMINANCE,
}


def test_generate_codes_simple_hand_worked_example():
    # A minimal, exactly-full Huffman tree: 1 code of length 1 uses up
    # half the code space (Kraft sum 1/2), leaving exactly two codes of
    # length 2 (2 * 1/4 = 1/2) to fill the rest -- Kraft sum == 1, valid.
    bits = [1, 2] + [0] * 14
    vals = ["a", "b", "c"]
    codes = generate_codes(bits, vals)
    assert codes["a"] == (0b0, 1)
    assert codes["b"] == (0b10, 2)
    assert codes["c"] == (0b11, 2)


def test_generate_codes_produces_prefix_free_codes():
    for name, (bits, vals) in ALL_TABLES.items():
        codes = generate_codes(bits, vals)
        code_strings = [format(code, f"0{length}b") for code, length in codes.values()]
        for i, a in enumerate(code_strings):
            for j, b in enumerate(code_strings):
                if i == j:
                    continue
                assert not b.startswith(a), f"{name}: code {a!r} is a prefix of {b!r}"


def test_generate_codes_never_produces_all_ones_code():
    # JPEG explicitly reserves the all-1-bits code of any length (it would
    # collide with the padding/marker byte 0xFF at the bitstream level).
    for name, (bits, vals) in ALL_TABLES.items():
        codes = generate_codes(bits, vals)
        for symbol, (code, length) in codes.items():
            assert code != (1 << length) - 1, f"{name}: symbol {symbol} got the all-ones code"


def test_generate_codes_lengths_match_bits_table():
    for name, (bits, vals) in ALL_TABLES.items():
        codes = generate_codes(bits, vals)
        counts = [0] * 16
        for _, length in codes.values():
            counts[length - 1] += 1
        assert counts == bits, name


def test_generate_codes_assigns_codes_in_nondecreasing_length_order():
    for name, (bits, vals) in ALL_TABLES.items():
        codes = generate_codes(bits, vals)
        lengths_in_order = [codes[sym][1] for sym in vals]
        assert lengths_in_order == sorted(lengths_in_order), name


def test_mismatched_bits_and_values_raises():
    with pytest.raises(AssertionError):
        generate_codes([1] + [0] * 15, ["a", "b"])  # bits says 1 symbol, 2 given
