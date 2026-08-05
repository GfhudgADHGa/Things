"""Brute-force oracles for small graphs -- exponential, deliberately
naive, and coded independently of every algorithm in this package. Used
as the ground truth in tests, not as anything meant to scale.
"""
from __future__ import annotations

from itertools import permutations
from typing import Dict, List, Optional, Set, Tuple

from .graph import Graph

INF = float("inf")


def brute_force_shortest_paths(g: Graph, source: int) -> Optional[Dict[int, float]]:
    """Enumerates every simple path from source to every node and takes
    the minimum length. Returns None if a negative cycle makes "shortest
    simple path" ill-defined in the presence of arbitrarily-repeatable
    negative cycles reachable from source (detected the same way
    bellman_ford does, independently re-implemented here)."""
    nodes = g.nodes()
    edges = [(u, v, w) for u, v, w in g.edges()] if not g.directed else [
        (u, v, w) for u, nbrs in g.adj.items() for v, w in nbrs
    ]

    dist = {u: INF for u in nodes}
    dist[source] = 0.0
    for _ in range(len(nodes)):
        for u, v, w in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    for u, v, w in edges:
        if dist[u] != INF and dist[u] + w < dist[v]:
            return None

    best: Dict[int, float] = {u: INF for u in nodes}
    best[source] = 0.0

    def dfs(u, visited, cost):
        if cost < best[u]:
            best[u] = cost
        for v, w in g.neighbors(u):
            if v not in visited:
                dfs(v, visited | {v}, cost + w)

    dfs(source, {source}, 0.0)
    return best


def brute_force_mst_weight(g: Graph) -> float:
    """Tries every subset of edges of size (n-1), keeps the cheapest one
    that's actually a spanning tree (connected, acyclic). Only usable on
    tiny graphs."""
    from itertools import combinations

    nodes = g.nodes()
    n = len(nodes)
    edges = g.edges()
    best = INF
    for combo in combinations(edges, n - 1):
        adj: Dict[int, List[int]] = {u: [] for u in nodes}
        for u, v, _ in combo:
            adj[u].append(v)
            adj[v].append(u)
        seen = {nodes[0]}
        stack = [nodes[0]]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        if len(seen) != n:
            continue
        weight = sum(w for _, _, w in combo)
        if weight < best:
            best = weight
    return best


def brute_force_max_flow(g: Graph, source: int, sink: int) -> float:
    """Tries every integer flow assignment up to total outgoing capacity
    of source via repeated simple-path saturation in all orders -- more
    precisely, since exact brute force over continuous flow is infinite,
    this enumerates all simple paths from source to sink and solves the
    resulting small LP by trying all edge orderings for greedy
    saturation, taking the max achieved value across all orderings. For
    the small, integer-capacity test graphs used here, this reliably
    finds the true maximum (which by max-flow-min-cut equals the min cut
    over all source/sink partitions, cross-checked separately)."""
    edges = [(u, v, w) for u, nbrs in g.adj.items() for v, w in nbrs]
    nodes = g.nodes()

    def all_simple_paths(u, target, visited):
        if u == target:
            yield []
            return
        for v, w in g.neighbors(u):
            if v not in visited and w > 0:
                for rest in all_simple_paths(v, target, visited | {v}):
                    yield [(u, v)] + rest

    paths = list(all_simple_paths(source, sink, {source}))
    if not paths:
        return 0.0

    best = 0.0
    for order in permutations(range(len(paths))):
        cap = {(u, v): w for u, nbrs in g.adj.items() for v, w in nbrs}
        total = 0.0
        for idx in order:
            path = paths[idx]
            bottleneck = min(cap[(u, v)] for u, v in path)
            if bottleneck <= 0:
                continue
            for u, v in path:
                cap[(u, v)] -= bottleneck
            total += bottleneck
        best = max(best, total)
    return best


def brute_force_min_cut_capacity(g: Graph, source: int, sink: int) -> float:
    """Tries every subset of nodes containing source but not sink, sums
    the capacity of edges crossing from the subset to its complement,
    keeps the minimum. Exponential in node count -- small graphs only."""
    nodes = [n for n in g.nodes() if n != source and n != sink]
    best = INF
    for mask in range(1 << len(nodes)):
        side = {source}
        for i, n in enumerate(nodes):
            if mask & (1 << i):
                side.add(n)
        if sink in side:
            continue
        cap = 0.0
        for u, nbrs in g.adj.items():
            if u not in side:
                continue
            for v, w in nbrs:
                if v not in side:
                    cap += w
        best = min(best, cap)
    return best


def brute_force_scc(g: Graph) -> List[Set[int]]:
    """Two nodes are in the same SCC iff each can reach the other. Builds
    full reachability by brute-force BFS from every node, then groups
    nodes into components by mutual reachability."""
    nodes = g.nodes()
    reach: Dict[int, Set[int]] = {}
    for u in nodes:
        seen = {u}
        stack = [u]
        while stack:
            x = stack.pop()
            for v, _ in g.neighbors(x):
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        reach[u] = seen

    components = []
    assigned: Set[int] = set()
    for u in nodes:
        if u in assigned:
            continue
        comp = {v for v in nodes if v in reach[u] and u in reach[v]}
        components.append(comp)
        assigned |= comp
    return components
