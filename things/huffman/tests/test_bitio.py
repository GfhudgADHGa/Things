from huffman.bitio import BitReader, BitWriter


def test_write_and_read_single_bits():
    writer = BitWriter()
    bits = [1, 0, 1, 1, 0, 0, 0, 1, 1, 0]
    for b in bits:
        writer.write_bit(b)
    data = writer.getvalue()

    reader = BitReader(data)
    read_back = [reader.read_bit() for _ in range(len(bits))]
    assert read_back == bits


def test_write_bits_string():
    writer = BitWriter()
    writer.write_bits("101101")
    data = writer.getvalue()
    reader = BitReader(data)
    assert [reader.read_bit() for _ in range(6)] == [1, 0, 1, 1, 0, 1]


def test_exact_byte_multiple_no_padding():
    writer = BitWriter()
    writer.write_bits("11110000")
    data = writer.getvalue()
    assert len(data) == 1
    assert data[0] == 0b11110000


def test_partial_byte_padded_with_zeros():
    writer = BitWriter()
    writer.write_bits("101")
    data = writer.getvalue()
    assert len(data) == 1
    assert data[0] == 0b10100000


def test_empty_writer_produces_empty_bytes():
    writer = BitWriter()
    assert writer.getvalue() == b""


def test_multi_byte_roundtrip():
    writer = BitWriter()
    bitstring = "1101001011010010110100101101"
    writer.write_bits(bitstring)
    data = writer.getvalue()
    reader = BitReader(data)
    read_back = "".join(str(reader.read_bit()) for _ in range(len(bitstring)))
    assert read_back == bitstring
