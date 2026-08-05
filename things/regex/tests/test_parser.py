import pytest

from regex import ast_nodes as ast
from regex.parser import RegexSyntaxError, parse


def test_literal():
    assert parse("a") == ast.Literal("a")


def test_concat():
    node = parse("ab")
    assert isinstance(node, ast.Concat)
    assert node.parts == [ast.Literal("a"), ast.Literal("b")]


def test_any_char():
    assert parse(".") == ast.AnyChar()


def test_star_plus_optional():
    assert parse("a*") == ast.Repeat(ast.Literal("a"), 0, None)
    assert parse("a+") == ast.Repeat(ast.Literal("a"), 1, None)
    assert parse("a?") == ast.Repeat(ast.Literal("a"), 0, 1)


def test_bounded_repeat_exact():
    assert parse("a{3}") == ast.Repeat(ast.Literal("a"), 3, 3)


def test_bounded_repeat_range():
    assert parse("a{2,5}") == ast.Repeat(ast.Literal("a"), 2, 5)


def test_bounded_repeat_open_ended():
    assert parse("a{2,}") == ast.Repeat(ast.Literal("a"), 2, None)


def test_bounded_repeat_invalid_range_raises():
    with pytest.raises(RegexSyntaxError):
        parse("a{5,2}")


def test_alternation():
    node = parse("a|b|c")
    assert isinstance(node, ast.Alternation)
    assert node.options == [ast.Literal("a"), ast.Literal("b"), ast.Literal("c")]


def test_grouping_affects_precedence():
    # without grouping, 'ab|c' parses as 'ab' or 'c'
    node = parse("ab|c")
    assert isinstance(node, ast.Alternation)
    assert isinstance(node.options[0], ast.Concat)

    # with grouping, 'a(b|c)' is 'a' followed by a group alternating b/c
    node2 = parse("a(b|c)")
    assert isinstance(node2, ast.Concat)
    assert isinstance(node2.parts[1], ast.Group)
    assert isinstance(node2.parts[1].child, ast.Alternation)


def test_char_class_simple():
    node = parse("[abc]")
    assert node == ast.CharClass(frozenset("abc"), False)


def test_char_class_negated():
    node = parse("[^abc]")
    assert node == ast.CharClass(frozenset("abc"), True)


def test_char_class_range():
    node = parse("[a-e]")
    assert node == ast.CharClass(frozenset("abcde"), False)


def test_char_class_mixed_ranges_and_literals():
    node = parse("[a-cX0-2]")
    assert node == ast.CharClass(frozenset("abcX012"), False)


def test_char_class_escaped_bracket():
    node = parse(r"[\]]")
    assert node == ast.CharClass(frozenset("]"), False)


def test_char_class_literal_dash_at_end():
    node = parse("[a-]")
    assert node == ast.CharClass(frozenset("a-"), False)


def test_shorthand_digit_class():
    node = parse(r"\d")
    assert node == ast.CharClass(frozenset("0123456789"), False)


def test_shorthand_negated_word_class():
    node = parse(r"\W")
    import string

    assert node == ast.CharClass(frozenset(string.ascii_letters + string.digits + "_"), True)


def test_negated_shorthand_inside_class_raises():
    with pytest.raises(RegexSyntaxError):
        parse(r"[\D]")


def test_anchors():
    node = parse("^abc$")
    assert isinstance(node, ast.Concat)
    assert isinstance(node.parts[0], ast.StartAnchor)
    assert isinstance(node.parts[-1], ast.EndAnchor)


def test_unterminated_group_raises():
    with pytest.raises(RegexSyntaxError):
        parse("(abc")


def test_unterminated_char_class_raises():
    with pytest.raises(RegexSyntaxError):
        parse("[abc")


def test_dangling_backslash_raises():
    with pytest.raises(RegexSyntaxError):
        parse("abc\\")


def test_escaped_metacharacters_are_literal():
    assert parse(r"\.") == ast.Literal(".")
    assert parse(r"\*") == ast.Literal("*")
    assert parse(r"\(") == ast.Literal("(")


def test_empty_pattern_parses_to_empty_concat():
    node = parse("")
    assert node == ast.Concat([])
