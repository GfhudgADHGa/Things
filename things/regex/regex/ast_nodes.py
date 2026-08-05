"""Regex AST node definitions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, List, Optional


class Node:
    pass


@dataclass
class Literal(Node):
    char: str


@dataclass
class AnyChar(Node):
    """Matches any character except newline."""


@dataclass
class CharClass(Node):
    chars: FrozenSet[str]
    negate: bool = False

    def matches(self, c: str) -> bool:
        return (c in self.chars) != self.negate


@dataclass
class Concat(Node):
    parts: List[Node]


@dataclass
class Alternation(Node):
    options: List[Node]


@dataclass
class Repeat(Node):
    child: Node
    min: int
    max: Optional[int]  # None means unbounded


@dataclass
class Group(Node):
    child: Node


@dataclass
class StartAnchor(Node):
    pass


@dataclass
class EndAnchor(Node):
    pass
