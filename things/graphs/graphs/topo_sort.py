"""Topological sort via Kahn's algorithm (repeatedly remove a node with
in-degree zero). Returns None if the graph has a cycle -- a DAG has a
topological order iff it's acyclic, so Kahn's algorithm doubles as a
cycle detector: if it terminates having emitted fewer nodes than the
graph has, whatever's left is entangled in a cycle."""
from __future__ import annotations

from collections import deque
from typing import List, Optional

from .graph import Graph


def kahn_topo_sort(g: Graph) -> Optional[List[int]]:
    if not g.directed:
        raise ValueError("topological sort requires a directed graph")
    in_degree = {u: 0 for u in g.nodes()}
    for u, v, _ in g.edges():
        in_degree[v] += 1

    queue = deque(sorted(u for u, d in in_degree.items() if d == 0))
    order = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v, _ in g.neighbors(u):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    if len(order) != len(g.nodes()):
        return None
    return order


def is_valid_topo_order(g: Graph, order: List[int]) -> bool:
    position = {u: i for i, u in enumerate(order)}
    for u, v, _ in g.edges():
        if position[u] >= position[v]:
            return False
    return True
