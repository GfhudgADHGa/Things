from jpeg.bitwriter import BitWriter


def test_simple_bits_pack_msb_first():
    w = BitWriter()
    w.write_bits(0b1010, 4)
    w.write_bits(0b0101, 4)
    assert w.flush() == bytes([0b10100101])


def test_bits_spanning_multiple_bytes():
    w = BitWriter()
    w.write_bits(0b111, 3)
    w.write_bits(0b00001111, 8)
    w.write_bits(0b0, 5)
    # 111 00001111 00000 -> 11100001 11100000
    assert w.flush() == bytes([0b11100001, 0b11100000])


def test_flush_pads_with_ones():
    w = BitWriter()
    w.write_bits(0b101, 3)
    result = w.flush()
    assert result == bytes([0b10111111])


def test_flush_with_no_pending_bits_writes_nothing():
    w = BitWriter()
    w.write_bits(0xFF, 8)
    assert w.flush() == bytes([0xFF, 0x00])  # stuffed


def test_0xff_byte_is_stuffed_with_a_following_zero():
    w = BitWriter()
    w.write_bits(0b11111111, 8)
    w.write_bits(0b00000000, 8)
    assert w.flush() == bytes([0xFF, 0x00, 0x00])


def test_writing_zero_length_is_a_noop():
    w = BitWriter()
    w.write_bits(0, 0)
    w.write_bits(0b1, 1)
    result = w.flush()
    assert result == bytes([0xFF, 0x00])  # 1 + 7 padding 1s = 0xFF, then stuffed


def test_many_small_writes_match_one_big_write():
    a = BitWriter()
    for bit in [1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0]:
        a.write_bits(bit, 1)
    b = BitWriter()
    b.write_bits(0b101100011010, 12)
    assert a.flush() == b.flush()
