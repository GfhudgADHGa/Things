"""Minimal graph representation: adjacency lists, directed or undirected,
weighted or unweighted (unit weight if omitted)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Graph:
    directed: bool = False
    adj: Dict[int, List[Tuple[int, float]]] = field(default_factory=dict)

    def add_node(self, u: int) -> None:
        self.adj.setdefault(u, [])

    def add_edge(self, u: int, v: int, weight: float = 1.0) -> None:
        self.add_node(u)
        self.add_node(v)
        self.adj[u].append((v, weight))
        if not self.directed:
            self.adj[v].append((u, weight))

    def nodes(self) -> List[int]:
        return list(self.adj.keys())

    def edges(self) -> List[Tuple[int, int, float]]:
        """Every edge once, even for undirected graphs (u < v canonical order
        isn't assumed -- caller-inserted direction is preserved for directed
        graphs). Undirected graphs are de-duplicated by unordered pair,
        keeping the *minimum*-weight copy when parallel edges exist between
        the same two nodes -- not an arbitrary "first one seen", which
        would silently make algorithms that consult edges() (Kruskal) see
        a different, possibly more expensive graph than algorithms that
        walk raw adjacency instead (Prim, which always finds the cheapest
        parallel edge naturally via its heap)."""
        if self.directed:
            return [(u, v, w) for u, nbrs in self.adj.items() for v, w in nbrs]
        best: Dict[frozenset, Tuple[int, int, float]] = {}
        for u, nbrs in self.adj.items():
            for v, w in nbrs:
                key = frozenset((u, v))
                if key not in best or w < best[key][2]:
                    best[key] = (u, v, w)
        return list(best.values())

    def neighbors(self, u: int) -> List[Tuple[int, float]]:
        return self.adj.get(u, [])

    def copy(self) -> "Graph":
        g = Graph(directed=self.directed)
        for u, nbrs in self.adj.items():
            g.adj[u] = list(nbrs)
        return g
