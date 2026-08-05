"""Myers' O(ND) shortest-edit-script diff algorithm (Myers, 1986: "An O(ND)
Difference Algorithm and Its Variations"). Finds the minimum number of
line insertions/deletions that turns sequence `a` into sequence `b`.

The core idea: think of an edit script as a path through an (x, y) grid
from (0, 0) to (len(a), len(b)), where a right-move is "delete a[x]", a
down-move is "insert b[y]", and a diagonal move is "keep a line that
matches" (free). The shortest edit script is the shortest such path.
Myers' algorithm finds it by, for each possible path length D = 0, 1, 2,
..., tracking the furthest-reaching x reachable on each diagonal k = x-y
using exactly D non-diagonal moves -- extending every diagonal move as
far as it'll go for free first. The first D for which some diagonal
reaches the far corner is the edit distance, and backtracking through
the recorded diagonals reconstructs the actual script.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

Op = Tuple[str, str]  # ("equal" | "insert" | "delete", line)


def _shortest_edit_trace(a: List[str], b: List[str]) -> List[Dict[int, int]]:
    n, m = len(a), len(b)
    v: Dict[int, int] = {1: 0}
    trace: List[Dict[int, int]] = []

    for d in range(n + m + 1):
        trace.append(dict(v))
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                x = v.get(k + 1, 0)
            else:
                x = v.get(k - 1, 0) + 1
            y = x - k

            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[k] = x

            if x >= n and y >= m:
                return trace

    return trace  # only reached if a == b (d=0 already covers that case above)


def _backtrack(a: List[str], b: List[str], trace: List[Dict[int, int]]) -> List[Op]:
    x, y = len(a), len(b)
    ops: List[Op] = []

    for d in range(len(trace) - 1, -1, -1):
        v = trace[d]
        k = x - y
        if k == -d or (k != d and v.get(k - 1, float("-inf")) < v.get(k + 1, float("-inf"))):
            prev_k = k + 1
        else:
            prev_k = k - 1

        prev_x = v.get(prev_k, 0)
        prev_y = prev_x - prev_k

        while x > prev_x and y > prev_y:
            ops.append(("equal", a[x - 1]))
            x, y = x - 1, y - 1

        if d > 0:
            if x == prev_x:
                ops.append(("insert", b[y - 1]))
                y -= 1
            else:
                ops.append(("delete", a[x - 1]))
                x -= 1

    ops.reverse()
    return ops


def myers_diff(a: List[str], b: List[str]) -> List[Op]:
    """Returns the shortest edit script turning `a` into `b`, as a list of
    ("equal" | "insert" | "delete", line) operations in order.
    """
    if a == b:
        return [("equal", line) for line in a]
    trace = _shortest_edit_trace(a, b)
    return _backtrack(a, b, trace)


def edit_distance(a: List[str], b: List[str]) -> int:
    """Number of insert/delete operations in the shortest edit script."""
    return sum(1 for op, _ in myers_diff(a, b) if op != "equal")
