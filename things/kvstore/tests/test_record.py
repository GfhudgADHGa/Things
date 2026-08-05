import io

from kvstore.record import OP_DELETE, OP_PUT, encode_record, read_valid_records


def test_encode_decode_put_roundtrip():
    data = encode_record(OP_PUT, b"key", b"value")
    records, valid_end = read_valid_records(io.BytesIO(data))
    assert len(records) == 1
    assert records[0].op == OP_PUT
    assert records[0].key == b"key"
    assert records[0].value == b"value"
    assert valid_end == len(data)


def test_encode_decode_delete_roundtrip():
    data = encode_record(OP_DELETE, b"key")
    records, _ = read_valid_records(io.BytesIO(data))
    assert records[0].op == OP_DELETE
    assert records[0].key == b"key"
    assert records[0].value is None


def test_multiple_records_in_sequence():
    data = (
        encode_record(OP_PUT, b"a", b"1")
        + encode_record(OP_PUT, b"b", b"2")
        + encode_record(OP_DELETE, b"a")
    )
    records, valid_end = read_valid_records(io.BytesIO(data))
    assert [(r.op, r.key, r.value) for r in records] == [
        (OP_PUT, b"a", b"1"),
        (OP_PUT, b"b", b"2"),
        (OP_DELETE, b"a", None),
    ]
    assert valid_end == len(data)


def test_empty_stream_yields_no_records():
    records, valid_end = read_valid_records(io.BytesIO(b""))
    assert records == []
    assert valid_end == 0


def test_truncated_header_is_discarded_not_raised():
    data = encode_record(OP_PUT, b"a", b"1") + b"\x00\x00\x00"  # 3 stray bytes
    records, valid_end = read_valid_records(io.BytesIO(data))
    assert len(records) == 1
    assert valid_end == len(encode_record(OP_PUT, b"a", b"1"))


def test_truncated_body_is_discarded_not_raised():
    good = encode_record(OP_PUT, b"a", b"1")
    torn = encode_record(OP_PUT, b"b", b"this record gets cut off")[:20]
    data = good + torn
    records, valid_end = read_valid_records(io.BytesIO(data))
    assert len(records) == 1
    assert records[0].key == b"a"
    assert valid_end == len(good)


def test_corrupted_checksum_is_discarded_not_raised():
    good = encode_record(OP_PUT, b"a", b"1")
    corrupt = bytearray(encode_record(OP_PUT, b"b", b"2"))
    corrupt[-1] ^= 0xFF  # flip a bit in the value payload
    data = good + bytes(corrupt)
    records, valid_end = read_valid_records(io.BytesIO(data))
    assert len(records) == 1
    assert records[0].key == b"a"
    assert valid_end == len(good)


def test_corruption_in_middle_discards_everything_after_it():
    good1 = encode_record(OP_PUT, b"a", b"1")
    corrupt = bytearray(encode_record(OP_PUT, b"b", b"2"))
    corrupt[-1] ^= 0xFF
    good2 = encode_record(OP_PUT, b"c", b"3")  # well-formed, but comes after corruption
    data = good1 + bytes(corrupt) + good2
    records, valid_end = read_valid_records(io.BytesIO(data))
    assert [r.key for r in records] == [b"a"]
    assert valid_end == len(good1)


def test_empty_value_roundtrips():
    data = encode_record(OP_PUT, b"k", b"")
    records, _ = read_valid_records(io.BytesIO(data))
    assert records[0].value == b""


def test_binary_safe_key_and_value():
    key = bytes(range(256))
    value = bytes(reversed(range(256)))
    data = encode_record(OP_PUT, key, value)
    records, _ = read_valid_records(io.BytesIO(data))
    assert records[0].key == key
    assert records[0].value == value
