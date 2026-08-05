"""Turns Pebble source text into a flat list of tokens."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, List

from .errors import LexError


class TokenType(Enum):
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()

    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()

    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    AND = auto()
    OR = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    FN = auto()
    RETURN = auto()
    LET = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()
    BREAK = auto()
    CONTINUE = auto()

    EOF = auto()


KEYWORDS = {
    "and": TokenType.AND,
    "or": TokenType.OR,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "let": TokenType.LET,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "nil": TokenType.NIL,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
}


@dataclass
class Token:
    type: TokenType
    lexeme: str
    literal: Any
    line: int


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> List[Token]:
        while not self._at_end():
            self.start = self.current
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def _at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        return c

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _peek(self) -> str:
        return "" if self._at_end() else self.source[self.current]

    def _peek_next(self) -> str:
        return "" if self.current + 1 >= len(self.source) else self.source[self.current + 1]

    def _add_token(self, type_: TokenType, literal: Any = None) -> None:
        text = self.source[self.start : self.current]
        self.tokens.append(Token(type_, text, literal, self.line))

    def _scan_token(self) -> None:
        c = self._advance()

        simple = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ",": TokenType.COMMA,
            ";": TokenType.SEMICOLON,
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "%": TokenType.PERCENT,
        }

        if c in simple:
            self._add_token(simple[c])
        elif c == "!":
            self._add_token(TokenType.BANG_EQUAL if self._match("=") else TokenType.BANG)
        elif c == "=":
            self._add_token(TokenType.EQUAL_EQUAL if self._match("=") else TokenType.EQUAL)
        elif c == "<":
            self._add_token(TokenType.LESS_EQUAL if self._match("=") else TokenType.LESS)
        elif c == ">":
            self._add_token(TokenType.GREATER_EQUAL if self._match("=") else TokenType.GREATER)
        elif c == "/":
            if self._match("/"):
                while self._peek() != "\n" and not self._at_end():
                    self._advance()
            else:
                self._add_token(TokenType.SLASH)
        elif c in " \r\t":
            pass
        elif c == "\n":
            self.line += 1
        elif c == '"':
            self._string()
        elif c.isdigit():
            self._number()
        elif c.isalpha() or c == "_":
            self._identifier()
        else:
            raise LexError(f"Unexpected character '{c}'", self.line)

    def _string(self) -> None:
        start_line = self.line
        chars = []
        while self._peek() != '"' and not self._at_end():
            if self._peek() == "\n":
                self.line += 1
            if self._peek() == "\\":
                self._advance()
                escaped = self._advance() if not self._at_end() else ""
                chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(escaped, escaped))
            else:
                chars.append(self._advance())

        if self._at_end():
            raise LexError("Unterminated string", start_line)

        self._advance()  # closing quote
        self._add_token(TokenType.STRING, "".join(chars))

    def _number(self) -> None:
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        self._add_token(TokenType.NUMBER, float(self.source[self.start : self.current]))

    def _identifier(self) -> None:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[self.start : self.current]
        self._add_token(KEYWORDS.get(text, TokenType.IDENTIFIER))
