"""NFA simulation: runs all live states in parallel (Thompson's algorithm),
so matching is O(len(pattern) * len(text)) with no backtracking, and
therefore immune to the catastrophic-backtracking blowup that plagues
naive backtracking regex engines on patterns like (a+)+b.
"""
from __future__ import annotations

from typing import List, Optional, Set

from .nfa import State


def _add_state(state: State, position: int, text: str, out: List[State], visited: Set[int]) -> None:
    if id(state) in visited:
        return
    visited.add(id(state))

    if state.kind in ("char", "match"):
        out.append(state)
        return
    if state.kind == "split":
        for nxt in state.out:
            _add_state(nxt, position, text, out, visited)
        return
    if state.kind == "anchor_start":
        if position == 0:
            for nxt in state.out:
                _add_state(nxt, position, text, out, visited)
        return
    if state.kind == "anchor_end":
        if position == len(text):
            for nxt in state.out:
                _add_state(nxt, position, text, out, visited)
        return
    raise ValueError(f"unknown state kind: {state.kind}")


def _closure(states: List[State], position: int, text: str) -> List[State]:
    result: List[State] = []
    visited: Set[int] = set()
    for s in states:
        _add_state(s, position, text, result, visited)
    return result


def run_from(start: State, text: str, start_pos: int = 0) -> Optional[int]:
    """Greedy longest match anchored at start_pos. Returns the furthest end
    position reachable, or None if no match starts exactly at start_pos.
    """
    current = _closure([start], start_pos, text)
    best_end = start_pos if any(s.kind == "match" for s in current) else None

    pos = start_pos
    while pos < len(text) and current:
        c = text[pos]
        next_states = [s.out[0] for s in current if s.kind == "char" and s.test(c)]
        pos += 1
        current = _closure(next_states, pos, text)
        if any(s.kind == "match" for s in current):
            best_end = pos

    return best_end


def matches_full(start: State, text: str) -> bool:
    """Whether the NFA accepts the *entire* text (like re.fullmatch)."""
    current = _closure([start], 0, text)
    pos = 0
    while pos < len(text):
        c = text[pos]
        next_states = [s.out[0] for s in current if s.kind == "char" and s.test(c)]
        pos += 1
        current = _closure(next_states, pos, text)
        if not current:
            return False
    return any(s.kind == "match" for s in current)
