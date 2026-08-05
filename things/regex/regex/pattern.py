"""Public API: compile(pattern) -> CompiledPattern, mirroring the shape of
Python's re module (match/fullmatch/search/findall) so behavior is easy to
compare directly against the standard library.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .matcher import matches_full, run_from
from .nfa import build_nfa
from .parser import parse


@dataclass
class Match:
    start: int
    end: int
    text: str

    def span(self):
        return (self.start, self.end)


class CompiledPattern:
    def __init__(self, pattern: str):
        self.pattern = pattern
        root = parse(pattern)
        self._start, self._match_state = build_nfa(root)

    def match(self, text: str, pos: int = 0) -> Optional[Match]:
        end = run_from(self._start, text, pos)
        if end is None:
            return None
        return Match(pos, end, text[pos:end])

    def fullmatch(self, text: str) -> Optional[Match]:
        if matches_full(self._start, text):
            return Match(0, len(text), text)
        return None

    def search(self, text: str, pos: int = 0) -> Optional[Match]:
        for i in range(pos, len(text) + 1):
            end = run_from(self._start, text, i)
            if end is not None:
                return Match(i, end, text[i:end])
        return None

    def findall(self, text: str) -> List[str]:
        results = []
        pos = 0
        while pos <= len(text):
            m = self.search(text, pos)
            if m is None:
                break
            results.append(m.text)
            pos = m.end + 1 if m.end == m.start else m.end
        return results

    def __repr__(self) -> str:
        return f"CompiledPattern({self.pattern!r})"


def compile(pattern: str) -> CompiledPattern:
    return CompiledPattern(pattern)


def match(pattern: str, text: str) -> Optional[Match]:
    return compile(pattern).match(text)


def fullmatch(pattern: str, text: str) -> Optional[Match]:
    return compile(pattern).fullmatch(text)


def search(pattern: str, text: str) -> Optional[Match]:
    return compile(pattern).search(text)


def findall(pattern: str, text: str) -> List[str]:
    return compile(pattern).findall(text)
