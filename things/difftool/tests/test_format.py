from difftool.diff import myers_diff
from difftool.format import format_diff, parse_diff


def test_format_uses_expected_prefixes():
    ops = [("equal", "a"), ("delete", "b"), ("insert", "x")]
    text = format_diff(ops)
    assert text == " a\n-b\n+x"


def test_format_empty_ops_is_empty_string():
    assert format_diff([]) == ""


def test_parse_is_inverse_of_format():
    ops = [("equal", "a"), ("delete", "b"), ("insert", "x"), ("equal", "c")]
    assert parse_diff(format_diff(ops)) == ops


def test_parse_empty_string_is_empty_ops():
    assert parse_diff("") == []


def test_format_then_parse_roundtrips_for_real_diffs():
    a = ["one", "two", "three", "four"]
    b = ["one", "TWO", "three", "five"]
    ops = myers_diff(a, b)
    assert parse_diff(format_diff(ops)) == ops


def test_format_preserves_lines_containing_no_special_chars():
    ops = [("equal", "hello world"), ("insert", "  indented")]
    text = format_diff(ops)
    assert parse_diff(text) == ops
