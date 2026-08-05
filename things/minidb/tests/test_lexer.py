import pytest

from minidb.errors import LexError
from minidb.lexer import TokType, tokenize


def _types(tokens):
    return [t.type for t in tokens]


def _values(tokens):
    return [t.value for t in tokens]


def test_tokenizes_keywords_case_insensitively():
    tokens = tokenize("select * from Users")
    assert _values(tokens) == ["SELECT", "*", "FROM", "Users", ""]
    assert tokens[0].type == TokType.KEYWORD
    assert tokens[3].type == TokType.IDENT


def test_tokenizes_numbers_int_and_float():
    tokens = tokenize("42 3.14 .5")
    assert _values(tokens)[:3] == ["42", "3.14", ".5"]
    assert all(t.type == TokType.NUMBER for t in tokens[:3])


def test_tokenizes_string_literal_with_escaped_quote():
    tokens = tokenize("'it''s here'")
    assert tokens[0].type == TokType.STRING
    assert tokens[0].value == "it's here"


def test_unterminated_string_raises():
    with pytest.raises(LexError):
        tokenize("'unterminated")


def test_two_char_operators():
    tokens = tokenize("a != b <> c <= d >= e")
    ops = [t.value for t in tokens if t.type == TokType.OP]
    assert ops == ["!=", "<>", "<=", ">="]


def test_line_comment_is_skipped():
    tokens = tokenize("SELECT 1 -- this is a comment\nFROM t")
    assert _values(tokens) == ["SELECT", "1", "FROM", "t", ""]


def test_unexpected_character_raises():
    with pytest.raises(LexError):
        tokenize("SELECT @")
