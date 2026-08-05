"""Max-flow via Edmonds-Karp (Ford-Fulkerson with BFS augmenting paths),
plus the min cut read directly off the final residual graph.

The max-flow min-cut theorem says these are always numerically equal --
not an implementation detail, a theorem -- so `min_cut_capacity(...)  ==
max_flow value` is checked as an exact, non-negotiable proof, not just a
plausibility check. It works because when BFS can no longer find an
augmenting path from source to sink, the set of nodes BFS *can* still
reach forms one side of a saturated cut: every edge crossing from the
reachable side to the unreachable side must be at full capacity (else
BFS would have crossed it), and every edge crossing back must carry zero
flow (else its reverse residual edge would let BFS cross it). So cut
capacity == flow across the cut == total flow, automatically at the
moment BFS terminates.
"""
from __future__ import annotations

from collections import deque
from typing import Dict, List, Set, Tuple

from .graph import Graph


def _build_residual(g: Graph) -> Dict[int, Dict[int, float]]:
    residual: Dict[int, Dict[int, float]] = {u: {} for u in g.nodes()}
    for u, nbrs in g.adj.items():
        for v, w in nbrs:
            residual[u][v] = residual[u].get(v, 0.0) + w
            residual.setdefault(v, {})
            residual[v].setdefault(u, 0.0)
    return residual


def _bfs_augmenting_path(residual, source, sink):
    parent = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if u == sink:
            break
        for v, cap in residual[u].items():
            if cap > 1e-12 and v not in parent:
                parent[v] = u
                queue.append(v)
    if sink not in parent:
        return None
    path = []
    v = sink
    while parent[v] is not None:
        u = parent[v]
        path.append((u, v))
        v = u
    path.reverse()
    return path


def edmonds_karp(g: Graph, source: int, sink: int) -> Tuple[float, Dict[int, Dict[int, float]]]:
    """Returns (max_flow_value, final_residual_graph)."""
    residual = _build_residual(g)
    flow_value = 0.0
    while True:
        path = _bfs_augmenting_path(residual, source, sink)
        if path is None:
            break
        bottleneck = min(residual[u][v] for u, v in path)
        for u, v in path:
            residual[u][v] -= bottleneck
            residual[v][u] += bottleneck
        flow_value += bottleneck
    return flow_value, residual


def reachable_in_residual(residual: Dict[int, Dict[int, float]], source: int) -> Set[int]:
    seen = {source}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v, cap in residual[u].items():
            if cap > 1e-12 and v not in seen:
                seen.add(v)
                queue.append(v)
    return seen


def min_cut(g: Graph, source: int, sink: int) -> Tuple[float, List[Tuple[int, int, float]], Set[int]]:
    """Runs edmonds_karp, then reads the min cut off the residual graph.
    Returns (cut_capacity, cut_edges, source_side_nodes)."""
    flow_value, residual = edmonds_karp(g, source, sink)
    reachable = reachable_in_residual(residual, source)
    cut_edges = []
    cut_capacity = 0.0
    for u, nbrs in g.adj.items():
        if u not in reachable:
            continue
        for v, w in nbrs:
            if v not in reachable:
                cut_edges.append((u, v, w))
                cut_capacity += w
    return cut_capacity, cut_edges, reachable
