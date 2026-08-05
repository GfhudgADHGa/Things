"""Thompson's construction: AST -> NFA.

Each State is one of:
  - "char":  consumes one character satisfying `test`, then goes to out[0]
  - "split": epsilon transitions to every state in `out` (used for
             alternation and repetition)
  - "anchor_start" / "anchor_end": epsilon transition to out[0], but only
    passable at position 0 / at the end of the text respectively
  - "match": the unique accepting state, no outgoing edges

Construction builds each AST node as a "fragment": a start state plus a
list of states with a dangling outgoing edge still to be wired up (patched)
to whatever comes next. This is the standard technique described in Russ
Cox's "Regular Expression Matching Can Be Simple And Fast" -- implemented
here from scratch in Python.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from . import ast_nodes as ast


class State:
    __slots__ = ("kind", "test", "out")

    def __init__(self, kind: str, test: Optional[Callable[[str], bool]] = None):
        self.kind = kind
        self.test = test
        self.out: List["State"] = []


@dataclass
class Frag:
    start: State
    dangling: List[State] = field(default_factory=list)


def _patch(dangling: List[State], target: State) -> None:
    for s in dangling:
        s.out.append(target)


def _epsilon_frag() -> Frag:
    s = State("split")
    return Frag(s, [s])


def _concat_frags(frags: List[Frag]) -> Frag:
    first = frags[0]
    dangling = first.dangling
    for f in frags[1:]:
        _patch(dangling, f.start)
        dangling = f.dangling
    return Frag(first.start, dangling)


def _build_star(child: ast.Node) -> Frag:
    split = State("split")
    cfrag = _build(child)
    split.out = [cfrag.start]
    _patch(cfrag.dangling, split)
    return Frag(split, [split])


def _build_optional(child: ast.Node) -> Frag:
    split = State("split")
    cfrag = _build(child)
    split.out = [cfrag.start]
    return Frag(split, cfrag.dangling + [split])


def _build_repeat(node: ast.Repeat) -> Frag:
    parts = [_build(node.child) for _ in range(node.min)]
    if node.max is None:
        parts.append(_build_star(node.child))
    else:
        for _ in range(node.max - node.min):
            parts.append(_build_optional(node.child))
    if not parts:
        return _epsilon_frag()
    return _concat_frags(parts)


def _build(node: ast.Node) -> Frag:
    if isinstance(node, ast.Literal):
        char = node.char
        s = State("char", test=lambda c, char=char: c == char)
        return Frag(s, [s])

    if isinstance(node, ast.AnyChar):
        s = State("char", test=lambda c: c != "\n")
        return Frag(s, [s])

    if isinstance(node, ast.CharClass):
        s = State("char", test=node.matches)
        return Frag(s, [s])

    if isinstance(node, ast.Group):
        return _build(node.child)

    if isinstance(node, ast.Concat):
        if not node.parts:
            return _epsilon_frag()
        return _concat_frags([_build(p) for p in node.parts])

    if isinstance(node, ast.Alternation):
        split = State("split")
        frags = [_build(opt) for opt in node.options]
        split.out = [f.start for f in frags]
        dangling = [d for f in frags for d in f.dangling]
        return Frag(split, dangling)

    if isinstance(node, ast.Repeat):
        return _build_repeat(node)

    if isinstance(node, ast.StartAnchor):
        s = State("anchor_start")
        return Frag(s, [s])

    if isinstance(node, ast.EndAnchor):
        s = State("anchor_end")
        return Frag(s, [s])

    raise TypeError(f"unknown AST node type: {type(node).__name__}")


def build_nfa(root: ast.Node) -> Tuple[State, State]:
    """Returns (start_state, match_state)."""
    match_state = State("match")
    frag = _build(root)
    _patch(frag.dangling, match_state)
    return frag.start, match_state
