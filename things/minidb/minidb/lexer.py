"""Hand-written tokenizer for a SQL subset."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from .errors import LexError


class TokType(Enum):
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    KEYWORD = auto()
    OP = auto()
    EOF = auto()


KEYWORDS = {
    "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "CREATE", "TABLE",
    "PRIMARY", "KEY", "UPDATE", "SET", "DELETE", "AND", "OR", "NOT", "NULL",
    "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "ASC", "DESC", "JOIN", "ON",
    "INNER", "LEFT", "AS", "DISTINCT", "LIKE", "IN", "IS", "INDEX",
    "INTEGER", "REAL", "TEXT",
}

_TWO_CHAR_OPS = {"!=", "<>", "<=", ">="}
_SINGLE_CHAR_OPS = set("()*,.;+-/%=<>")


@dataclass
class Token:
    type: TokType
    value: str
    pos: int


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
            continue
        if c == "-" and i + 1 < n and text[i + 1] == "-":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c.isdigit() or (c == "." and i + 1 < n and text[i + 1].isdigit()):
            start = i
            while i < n and text[i].isdigit():
                i += 1
            if i < n and text[i] == ".":
                i += 1
                while i < n and text[i].isdigit():
                    i += 1
            tokens.append(Token(TokType.NUMBER, text[start:i], start))
            continue
        if c == "'":
            start = i
            i += 1
            chars: list[str] = []
            closed = False
            while i < n:
                if text[i] == "'":
                    if i + 1 < n and text[i + 1] == "'":
                        chars.append("'")
                        i += 2
                        continue
                    i += 1
                    closed = True
                    break
                chars.append(text[i])
                i += 1
            if not closed:
                raise LexError(f"unterminated string literal starting at {start}")
            tokens.append(Token(TokType.STRING, "".join(chars), start))
            continue
        if c.isalpha() or c == "_":
            start = i
            while i < n and (text[i].isalnum() or text[i] == "_"):
                i += 1
            word = text[start:i]
            upper = word.upper()
            if upper in KEYWORDS:
                tokens.append(Token(TokType.KEYWORD, upper, start))
            else:
                tokens.append(Token(TokType.IDENT, word, start))
            continue
        two = text[i:i + 2]
        if two in _TWO_CHAR_OPS:
            tokens.append(Token(TokType.OP, two, i))
            i += 2
            continue
        if c in _SINGLE_CHAR_OPS:
            tokens.append(Token(TokType.OP, c, i))
            i += 1
            continue
        raise LexError(f"unexpected character {c!r} at position {i}")
    tokens.append(Token(TokType.EOF, "", n))
    return tokens
