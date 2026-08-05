import os
import random

import pytest

from huffman.format import MAGIC, compress, decompress


def roundtrip(data: bytes) -> bytes:
    return decompress(compress(data))


def test_empty_data():
    assert roundtrip(b"") == b""


def test_single_byte():
    assert roundtrip(b"x") == b"x"


def test_single_repeated_byte():
    data = bytes([42]) * 1000
    assert roundtrip(data) == data


def test_two_distinct_bytes():
    data = b"ab" * 500
    assert roundtrip(data) == data


def test_plain_text():
    data = b"the quick brown fox jumps over the lazy dog" * 50
    assert roundtrip(data) == data


def test_all_256_byte_values_present():
    data = bytes(range(256))
    assert roundtrip(data) == data


def test_all_256_byte_values_repeated_with_skew():
    rng = random.Random(1)
    weights = [max(1, 256 - i) for i in range(256)]
    data = bytes(rng.choices(range(256), weights=weights, k=5000))
    assert roundtrip(data) == data


def test_random_binary_data():
    rng = random.Random(2)
    data = bytes(rng.randrange(256) for _ in range(2000))
    assert roundtrip(data) == data


def test_compressed_output_starts_with_magic():
    compressed = compress(b"hello")
    assert compressed[:4] == MAGIC


def test_decompress_rejects_bad_magic():
    with pytest.raises(ValueError):
        decompress(b"NOPE" + b"\x00" * 20)


def test_skewed_text_actually_compresses():
    # highly repetitive text should end up meaningfully smaller than the original
    data = (b"aaaaaaaaab" * 200)
    compressed = compress(data)
    assert len(compressed) < len(data)


def test_single_symbol_needs_no_payload_bits():
    # original_length in the header already tells the decoder how many
    # copies of the one distinct symbol to emit, so there's nothing left
    # for the payload to encode -- compressed size should be header-only,
    # independent of how many times the byte repeats.
    small = compress(bytes([7]) * 100)
    large = compress(bytes([7]) * 10_000_000)
    assert len(small) == len(large)
    assert len(large) < 20


def test_compress_decompress_file_roundtrip(tmp_path):
    original = b"some file contents\nwith multiple lines\n" * 30
    src = tmp_path / "input.txt"
    src.write_bytes(original)

    compressed = compress(src.read_bytes())
    comp_path = tmp_path / "input.huf"
    comp_path.write_bytes(compressed)

    restored = decompress(comp_path.read_bytes())
    assert restored == original


@pytest.mark.parametrize("size", [0, 1, 2, 7, 8, 9, 255, 256, 257, 1000])
def test_various_sizes_of_random_data_roundtrip(size):
    rng = random.Random(size)
    data = bytes(rng.randrange(256) for _ in range(size))
    assert roundtrip(data) == data
