from pebble.errors import LexError
from pebble.lexer import Lexer, TokenType as T
import pytest


def token_types(source):
    return [t.type for t in Lexer(source).scan_tokens()]


def test_single_char_tokens():
    types = token_types("(){}[],;+-*%")
    assert types == [
        T.LPAREN, T.RPAREN, T.LBRACE, T.RBRACE, T.LBRACKET, T.RBRACKET,
        T.COMMA, T.SEMICOLON, T.PLUS, T.MINUS, T.STAR, T.PERCENT, T.EOF,
    ]


def test_two_char_tokens():
    types = token_types("== != <= >= = < >")
    assert types == [
        T.EQUAL_EQUAL, T.BANG_EQUAL, T.LESS_EQUAL, T.GREATER_EQUAL,
        T.EQUAL, T.LESS, T.GREATER, T.EOF,
    ]


def test_line_comment_is_skipped():
    tokens = Lexer("1 // this is a comment\n2").scan_tokens()
    assert [t.type for t in tokens] == [T.NUMBER, T.NUMBER, T.EOF]
    assert tokens[1].line == 2


def test_number_literal():
    tokens = Lexer("42").scan_tokens()
    assert tokens[0].type == T.NUMBER
    assert tokens[0].literal == 42.0


def test_float_literal():
    tokens = Lexer("3.14").scan_tokens()
    assert tokens[0].literal == 3.14


def test_string_literal():
    tokens = Lexer('"hello"').scan_tokens()
    assert tokens[0].type == T.STRING
    assert tokens[0].literal == "hello"


def test_string_with_escapes():
    tokens = Lexer(r'"a\nb\tc\"d"').scan_tokens()
    assert tokens[0].literal == 'a\nb\tc"d'


def test_unterminated_string_raises():
    with pytest.raises(LexError):
        Lexer('"unterminated').scan_tokens()


def test_keywords_are_recognized():
    types = token_types("and or if else while for fn return let true false nil break continue")
    expected = [
        T.AND, T.OR, T.IF, T.ELSE, T.WHILE, T.FOR, T.FN, T.RETURN, T.LET,
        T.TRUE, T.FALSE, T.NIL, T.BREAK, T.CONTINUE, T.EOF,
    ]
    assert types == expected


def test_identifiers_vs_keywords():
    tokens = Lexer("forest").scan_tokens()
    assert tokens[0].type == T.IDENTIFIER
    assert tokens[0].lexeme == "forest"


def test_unexpected_character_raises():
    with pytest.raises(LexError):
        Lexer("@").scan_tokens()


def test_line_numbers_track_newlines():
    tokens = Lexer("1\n2\n3").scan_tokens()
    numbers = [t for t in tokens if t.type == T.NUMBER]
    assert [t.line for t in numbers] == [1, 2, 3]
