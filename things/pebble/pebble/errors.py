"""Error types shared across the lexer, parser, and interpreter."""
from __future__ import annotations


class PebbleError(Exception):
    """Base class for all errors that should be reported to the user
    (as opposed to internal bugs, which raise plain Python exceptions).
    """

    def __init__(self, message: str, line: int | None = None):
        self.message = message
        self.line = line
        location = f" [line {line}]" if line is not None else ""
        super().__init__(f"{message}{location}")


class LexError(PebbleError):
    pass


class ParseError(PebbleError):
    pass


class RuntimeErrorPebble(PebbleError):
    """Named to avoid clashing with the builtin RuntimeError."""
