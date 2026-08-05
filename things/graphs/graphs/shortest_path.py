"""Three independent single-source/all-pairs shortest path algorithms.

dijkstra: requires non-negative weights, O((V+E) log V) via a binary heap.
bellman_ford: handles negative weights, detects negative cycles, O(VE).
floyd_warshall: all-pairs, O(V^3), also handles negative weights (not
    negative cycles reachable from within the cycle itself, which it
    detects via a negative diagonal after relaxation).

These share no code with each other by design, so agreement between them
is a real cross-check, not a shared-bug coincidence.
"""
from __future__ import annotations

import heapq
from typing import Dict, Optional, Tuple

from .graph import Graph

INF = float("inf")


def dijkstra(g: Graph, source: int) -> Dict[int, float]:
    for _, nbrs in g.adj.items():
        for _, w in nbrs:
            if w < 0:
                raise ValueError("dijkstra requires non-negative edge weights")
    dist = {u: INF for u in g.nodes()}
    dist[source] = 0.0
    heap = [(0.0, source)]
    visited = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for v, w in g.neighbors(u):
            nd = d + w
            if nd < dist.get(v, INF):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def bellman_ford(g: Graph, source: int) -> Optional[Dict[int, float]]:
    """Returns None if a negative-weight cycle is reachable from source."""
    dist = {u: INF for u in g.nodes()}
    dist[source] = 0.0
    edges = []
    for u, nbrs in g.adj.items():
        for v, w in nbrs:
            edges.append((u, v, w))

    n = len(g.nodes())
    for _ in range(max(n - 1, 0)):
        changed = False
        for u, v, w in edges:
            if dist[u] == INF:
                continue
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                changed = True
        if not changed:
            break

    for u, v, w in edges:
        if dist[u] != INF and dist[u] + w < dist[v]:
            return None
    return dist


def floyd_warshall(g: Graph) -> Optional[Dict[Tuple[int, int], float]]:
    """Returns None if any negative-weight cycle exists anywhere in the
    graph (not just reachable from a particular source)."""
    nodes = g.nodes()
    dist: Dict[Tuple[int, int], float] = {}
    for u in nodes:
        for v in nodes:
            dist[(u, v)] = 0.0 if u == v else INF
    for u, nbrs in g.adj.items():
        for v, w in nbrs:
            if w < dist[(u, v)]:
                dist[(u, v)] = w

    for k in nodes:
        for i in nodes:
            dik = dist[(i, k)]
            if dik == INF:
                continue
            for j in nodes:
                nd = dik + dist[(k, j)]
                if nd < dist[(i, j)]:
                    dist[(i, j)] = nd

    for u in nodes:
        if dist[(u, u)] < 0:
            return None
    return dist
