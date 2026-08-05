import regex


def test_literal_fullmatch():
    p = regex.compile("abc")
    assert p.fullmatch("abc") is not None
    assert p.fullmatch("abcd") is None
    assert p.fullmatch("ab") is None


def test_any_char():
    p = regex.compile("a.c")
    assert p.fullmatch("abc") is not None
    assert p.fullmatch("axc") is not None
    assert p.fullmatch("a\nc") is None  # '.' does not match newline


def test_star():
    p = regex.compile("ab*c")
    assert p.fullmatch("ac") is not None
    assert p.fullmatch("abc") is not None
    assert p.fullmatch("abbbbbc") is not None
    assert p.fullmatch("abd") is None


def test_plus_requires_at_least_one():
    p = regex.compile("ab+c")
    assert p.fullmatch("ac") is None
    assert p.fullmatch("abc") is not None
    assert p.fullmatch("abbc") is not None


def test_optional():
    p = regex.compile("ab?c")
    assert p.fullmatch("ac") is not None
    assert p.fullmatch("abc") is not None
    assert p.fullmatch("abbc") is None


def test_bounded_repeat():
    p = regex.compile("a{2,3}")
    assert p.fullmatch("a") is None
    assert p.fullmatch("aa") is not None
    assert p.fullmatch("aaa") is not None
    assert p.fullmatch("aaaa") is None


def test_alternation():
    p = regex.compile("cat|dog")
    assert p.fullmatch("cat") is not None
    assert p.fullmatch("dog") is not None
    assert p.fullmatch("cow") is None


def test_grouped_repeat():
    p = regex.compile("(ab)+")
    assert p.fullmatch("ab") is not None
    assert p.fullmatch("ababab") is not None
    assert p.fullmatch("aba") is None


def test_character_class():
    p = regex.compile("[aeiou]+")
    assert p.fullmatch("aeiou") is not None
    assert p.fullmatch("aeioux") is None


def test_negated_character_class():
    p = regex.compile("[^0-9]+")
    assert p.fullmatch("abc") is not None
    assert p.fullmatch("abc1") is None


def test_digit_shorthand():
    p = regex.compile(r"\d{3}-\d{4}")
    assert p.fullmatch("555-1234") is not None
    assert p.fullmatch("55-1234") is None


def test_anchors_restrict_match_position():
    p = regex.compile("^abc$")
    assert p.fullmatch("abc") is not None
    m = p.match("abc")
    assert m is not None and m.span() == (0, 3)


def test_match_is_anchored_at_start_but_neednt_consume_all():
    p = regex.compile("ab")
    m = p.match("abcdef")
    assert m is not None
    assert m.span() == (0, 2)
    assert p.match("xabcdef") is None


def test_search_finds_first_occurrence_anywhere():
    p = regex.compile("cat")
    m = p.search("the cat sat")
    assert m is not None
    assert m.span() == (4, 7)
    assert m.text == "cat"


def test_search_returns_none_when_absent():
    p = regex.compile("zebra")
    assert p.search("the cat sat") is None


def test_findall_multiple_matches():
    p = regex.compile(r"\d+")
    assert p.findall("a1 b22 c333") == ["1", "22", "333"]


def test_findall_handles_empty_matches_without_looping_forever():
    p = regex.compile("a*")
    results = p.findall("baab")
    assert results == ["", "aa", "", ""]


def test_empty_pattern_matches_empty_string_everywhere():
    p = regex.compile("")
    assert p.fullmatch("") is not None
    assert p.fullmatch("x") is None
    m = p.search("xyz")
    assert m is not None
    assert m.span() == (0, 0)
