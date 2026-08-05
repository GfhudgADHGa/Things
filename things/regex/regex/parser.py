"""Regex syntax -> AST. Supports literals, '.', *, +, ?, {m,n}, |, (), character
classes with ranges and negation, \\d \\w \\s (and negated forms) shorthands,
and ^ / $ anchors.
"""
from __future__ import annotations

import string
from typing import FrozenSet, Optional

from . import ast_nodes as ast

_SHORTHANDS = {
    "d": (frozenset(string.digits), False),
    "D": (frozenset(string.digits), True),
    "w": (frozenset(string.ascii_letters + string.digits + "_"), False),
    "W": (frozenset(string.ascii_letters + string.digits + "_"), True),
    "s": (frozenset(" \t\n\r\f\v"), False),
    "S": (frozenset(" \t\n\r\f\v"), True),
}

_ESCAPE_LITERALS = {"n": "\n", "t": "\t", "r": "\r", "f": "\f", "v": "\v"}


class RegexSyntaxError(Exception):
    pass


class Parser:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0

    def _peek(self) -> str:
        return self.pattern[self.pos] if self.pos < len(self.pattern) else ""

    def _advance(self) -> str:
        c = self._peek()
        self.pos += 1
        return c

    def _expect(self, ch: str) -> None:
        if self._peek() != ch:
            raise RegexSyntaxError(f"expected '{ch}' at position {self.pos} in {self.pattern!r}")
        self._advance()

    def parse(self) -> ast.Node:
        node = self._parse_alternation()
        if self.pos != len(self.pattern):
            raise RegexSyntaxError(f"unexpected '{self._peek()}' at position {self.pos}")
        return node

    def _parse_alternation(self) -> ast.Node:
        options = [self._parse_concat()]
        while self._peek() == "|":
            self._advance()
            options.append(self._parse_concat())
        return options[0] if len(options) == 1 else ast.Alternation(options)

    def _parse_concat(self) -> ast.Node:
        parts = []
        while self._peek() not in ("", "|", ")"):
            parts.append(self._parse_repeat())
        if len(parts) == 1:
            return parts[0]
        return ast.Concat(parts)

    def _parse_repeat(self) -> ast.Node:
        atom = self._parse_atom()
        q = self._peek()
        if q == "*":
            self._advance()
            return ast.Repeat(atom, 0, None)
        if q == "+":
            self._advance()
            return ast.Repeat(atom, 1, None)
        if q == "?":
            self._advance()
            return ast.Repeat(atom, 0, 1)
        if q == "{":
            return self._parse_bounded_repeat(atom)
        return atom

    def _parse_bounded_repeat(self, atom: ast.Node) -> ast.Node:
        self._advance()  # '{'
        min_str = ""
        while self._peek().isdigit():
            min_str += self._advance()
        if min_str == "":
            raise RegexSyntaxError(f"expected a number after '{{' at position {self.pos}")
        min_n = int(min_str)

        max_n: Optional[int] = min_n
        if self._peek() == ",":
            self._advance()
            max_str = ""
            while self._peek().isdigit():
                max_str += self._advance()
            max_n = int(max_str) if max_str else None

        self._expect("}")
        if max_n is not None and max_n < min_n:
            raise RegexSyntaxError(f"invalid repeat range {{{min_n},{max_n}}}: max < min")
        return ast.Repeat(atom, min_n, max_n)

    def _parse_atom(self) -> ast.Node:
        c = self._peek()
        if c == "(":
            self._advance()
            inner = self._parse_alternation()
            self._expect(")")
            return ast.Group(inner)
        if c == ".":
            self._advance()
            return ast.AnyChar()
        if c == "^":
            self._advance()
            return ast.StartAnchor()
        if c == "$":
            self._advance()
            return ast.EndAnchor()
        if c == "[":
            return self._parse_char_class()
        if c == "\\":
            return self._parse_escape_atom()
        if c in ("", ")", "|", "*", "+", "?"):
            raise RegexSyntaxError(f"unexpected '{c}' at position {self.pos}")
        self._advance()
        return ast.Literal(c)

    def _parse_escape_atom(self) -> ast.Node:
        self._advance()  # backslash
        if self.pos >= len(self.pattern):
            raise RegexSyntaxError("dangling backslash at end of pattern")
        c = self._advance()
        if c in _SHORTHANDS:
            chars, negate = _SHORTHANDS[c]
            return ast.CharClass(chars, negate)
        if c in _ESCAPE_LITERALS:
            return ast.Literal(_ESCAPE_LITERALS[c])
        return ast.Literal(c)

    def _parse_char_class(self) -> ast.Node:
        self._advance()  # '['
        negate = False
        if self._peek() == "^":
            negate = True
            self._advance()

        chars = set()
        while True:
            if self.pos >= len(self.pattern):
                raise RegexSyntaxError("unterminated character class")
            c = self._peek()
            if c == "]":
                self._advance()
                break
            if c == "\\":
                chars |= self._parse_escape_in_class()
                continue
            # a range like a-z, but not if '-' is immediately before ']'
            if self.pattern[self.pos + 1 : self.pos + 2] == "-" and self.pattern[self.pos + 2 : self.pos + 3] not in ("", "]"):
                lo = self._advance()
                self._advance()  # '-'
                hi = self._advance()
                if ord(hi) < ord(lo):
                    raise RegexSyntaxError(f"invalid range '{lo}-{hi}' in character class")
                chars |= {chr(x) for x in range(ord(lo), ord(hi) + 1)}
                continue
            chars.add(c)
            self._advance()

        return ast.CharClass(frozenset(chars), negate)

    def _parse_escape_in_class(self) -> FrozenSet[str]:
        self._advance()  # backslash
        if self.pos >= len(self.pattern):
            raise RegexSyntaxError("dangling backslash in character class")
        c = self._advance()
        if c in _SHORTHANDS:
            chars, negate = _SHORTHANDS[c]
            if negate:
                raise RegexSyntaxError(
                    f"negated shorthand '\\{c}' is not supported inside a character class"
                )
            return chars
        if c in _ESCAPE_LITERALS:
            return frozenset(_ESCAPE_LITERALS[c])
        return frozenset(c)


def parse(pattern: str) -> ast.Node:
    return Parser(pattern).parse()
