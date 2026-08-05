"""Renders an edit script as unified-diff-style text (' '/'-'/'+' prefixed
lines), and parses that format back into an edit script.
"""
from __future__ import annotations

from typing import List

from .diff import Op

_PREFIX = {"equal": " ", "delete": "-", "insert": "+"}
_FROM_PREFIX = {v: k for k, v in _PREFIX.items()}


def format_diff(ops: List[Op]) -> str:
    return "\n".join(f"{_PREFIX[op]}{line}" for op, line in ops)


def parse_diff(text: str) -> List[Op]:
    if text == "":
        return []
    ops = []
    for line in text.split("\n"):
        prefix, content = line[0], line[1:]
        ops.append((_FROM_PREFIX[prefix], content))
    return ops
