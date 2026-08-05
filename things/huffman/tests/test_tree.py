from huffman.tree import Internal, Leaf, build_code_table, build_tree


def test_empty_frequencies_gives_no_tree():
    assert build_tree({}) is None
    assert build_code_table(None) == {}


def test_single_symbol_gives_leaf_root():
    tree = build_tree({65: 10})
    assert isinstance(tree, Leaf)
    assert tree.symbol == 65


def test_single_symbol_code_table_uses_one_bit():
    tree = build_tree({65: 10})
    codes = build_code_table(tree)
    assert codes == {65: "0"}


def test_two_symbols_get_complementary_one_bit_codes():
    tree = build_tree({65: 5, 66: 3})
    codes = build_code_table(tree)
    assert set(codes.values()) == {"0", "1"}
    assert len(set(codes.values())) == 2


def test_more_frequent_symbol_gets_shorter_or_equal_code():
    freqs = {ord("a"): 100, ord("b"): 50, ord("c"): 10, ord("d"): 1}
    codes = build_code_table(build_tree(freqs))
    assert len(codes[ord("a")]) <= len(codes[ord("d")])


def test_codes_are_prefix_free():
    freqs = {ord(c): f for c, f in zip("abcdef", [45, 13, 12, 16, 9, 5])}
    codes = build_code_table(build_tree(freqs))
    values = list(codes.values())
    for i, a in enumerate(values):
        for j, b in enumerate(values):
            if i != j:
                assert not b.startswith(a), f"{a!r} is a prefix of {b!r}"


def test_every_symbol_has_a_code():
    freqs = {i: i + 1 for i in range(20)}
    codes = build_code_table(build_tree(freqs))
    assert set(codes.keys()) == set(freqs.keys())


def test_tree_is_deterministic_given_same_frequencies():
    freqs = {ord(c): f for c, f in zip("abcde", [5, 3, 3, 2, 1])}
    codes_a = build_code_table(build_tree(freqs))
    codes_b = build_code_table(build_tree(freqs))
    assert codes_a == codes_b


def test_all_256_byte_values_get_distinct_prefix_free_codes():
    freqs = {i: (i % 7) + 1 for i in range(256)}
    codes = build_code_table(build_tree(freqs))
    assert len(codes) == 256
    values = sorted(codes.values(), key=len)
    for i, a in enumerate(values):
        for b in values[i + 1 :]:
            assert not b.startswith(a)


def test_internal_and_leaf_are_distinguishable():
    tree = build_tree({1: 5, 2: 3})
    assert isinstance(tree, Internal)
    assert isinstance(tree.left, Leaf) or isinstance(tree.left, Internal)
