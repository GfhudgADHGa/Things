"""Lexical scope: a chain of name -> value dictionaries."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .errors import RuntimeErrorPebble


class Environment:
    def __init__(self, parent: Optional["Environment"] = None):
        self.parent = parent
        self.values: Dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def get(self, name: str, line: int) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name, line)
        raise RuntimeErrorPebble(f"Undefined variable '{name}'.", line)

    def assign(self, name: str, value: Any, line: int) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value, line)
            return
        raise RuntimeErrorPebble(f"Undefined variable '{name}'.", line)
