"""Running Pebble source: from a file, a string, or an interactive REPL."""
from __future__ import annotations

import sys

from .errors import PebbleError
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import parse


def run_source(source: str, interpreter: Interpreter) -> None:
    tokens = Lexer(source).scan_tokens()
    statements = parse(tokens)
    interpreter.interpret(statements)


def run_file(path: str) -> int:
    with open(path) as f:
        source = f.read()

    interpreter = Interpreter()
    try:
        run_source(source, interpreter)
    except PebbleError as e:
        print(f"pebble: {e.message}" + (f" [line {e.line}]" if e.line else ""), file=sys.stderr)
        return 1
    return 0


def repl() -> None:
    interpreter = Interpreter()
    print("Pebble REPL. Ctrl-D to exit.")
    buffer = ""
    while True:
        try:
            prompt = "... " if buffer else ">>> "
            line = input(prompt)
        except EOFError:
            print()
            break

        buffer += line + "\n"
        if buffer.count("{") > buffer.count("}") or buffer.count("(") > buffer.count(")"):
            continue  # keep collecting an incomplete block/call

        try:
            tokens = Lexer(buffer).scan_tokens()
            statements = parse(tokens)
            interpreter.interpret(statements)
        except PebbleError as e:
            print(f"error: {e.message}" + (f" [line {e.line}]" if e.line else ""))
        finally:
            buffer = ""
