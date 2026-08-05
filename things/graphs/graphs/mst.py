"""Minimum spanning tree via two independent classic algorithms.

kruskal: sort all edges globally, add if it doesn't close a cycle
    (union-find), greedy on edges.
prim: grow a single tree from a start node, always adding the cheapest
    edge leaving the current tree (a heap of frontier edges), greedy on
    nodes.

Both are correct by the cut property, but they explore in totally
different orders, so agreement on total weight is a real check -- and
with distinct edge weights the edge *sets* must match too (the MST is
then unique)."""
from __future__ import annotations

import heapq
from typing import List, Tuple

from .graph import Graph


class _UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}
        self.rank = {x: 0 for x in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def kruskal(g: Graph) -> List[Tuple[int, int, float]]:
    edges = sorted(g.edges(), key=lambda e: e[2])
    uf = _UnionFind(g.nodes())
    mst = []
    for u, v, w in edges:
        if uf.union(u, v):
            mst.append((u, v, w))
    return mst


def prim(g: Graph, start: int) -> List[Tuple[int, int, float]]:
    visited = {start}
    heap = []
    for v, w in g.neighbors(start):
        heapq.heappush(heap, (w, start, v))
    mst = []
    nodes = set(g.nodes())
    while heap and len(visited) < len(nodes):
        w, u, v = heapq.heappop(heap)
        if v in visited:
            continue
        visited.add(v)
        mst.append((u, v, w))
        for v2, w2 in g.neighbors(v):
            if v2 not in visited:
                heapq.heappush(heap, (w2, v, v2))
    return mst


def total_weight(edges: List[Tuple[int, int, float]]) -> float:
    return sum(w for _, _, w in edges)
