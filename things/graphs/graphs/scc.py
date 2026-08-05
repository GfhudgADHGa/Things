"""Strongly connected components via two independent algorithms.

tarjan_scc: single DFS pass, tracking discovery indices and the lowest
    reachable discovery index (the "low-link"), popping a component off
    an explicit stack whenever a node's low-link equals its own index.
kosaraju_scc: DFS finishing-order on the graph, then DFS again on the
    transposed (edge-reversed) graph in reverse finishing order -- each
    DFS tree in the second pass is exactly one SCC.

Both run only on directed graphs. They're structurally very different
(Tarjan needs no transpose or second pass; Kosaraju needs both), so
agreement is a real cross-check.
"""
from __future__ import annotations

from typing import Dict, List

from .graph import Graph


def tarjan_scc(g: Graph) -> List[List[int]]:
    index_counter = [0]
    index: Dict[int, int] = {}
    lowlink: Dict[int, int] = {}
    on_stack: Dict[int, bool] = {}
    stack: List[int] = []
    result: List[List[int]] = []

    def strongconnect(v):
        work = [(v, iter(g.neighbors(v)), False)]
        while work:
            node, it, entered = work[-1]
            if not entered:
                index[node] = index_counter[0]
                lowlink[node] = index_counter[0]
                index_counter[0] += 1
                stack.append(node)
                on_stack[node] = True
                work[-1] = (node, it, True)
            recursed = False
            for w, _ in it:
                if w not in index:
                    work.append((w, iter(g.neighbors(w)), False))
                    recursed = True
                    break
                elif on_stack.get(w):
                    lowlink[node] = min(lowlink[node], index[w])
            if recursed:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])
            if lowlink[node] == index[node]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    component.append(w)
                    if w == node:
                        break
                result.append(component)

    for v in g.nodes():
        if v not in index:
            strongconnect(v)
    return result


def _transpose(g: Graph) -> Graph:
    t = Graph(directed=True)
    for u in g.nodes():
        t.add_node(u)
    for u, v, w in g.edges():
        t.add_edge(v, u, w)
    return t


def kosaraju_scc(g: Graph) -> List[List[int]]:
    visited = set()
    finish_order: List[int] = []

    for start in g.nodes():
        if start in visited:
            continue
        stack = [(start, iter(g.neighbors(start)))]
        visited.add(start)
        while stack:
            node, it = stack[-1]
            advanced = False
            for w, _ in it:
                if w not in visited:
                    visited.add(w)
                    stack.append((w, iter(g.neighbors(w))))
                    advanced = True
                    break
            if not advanced:
                finish_order.append(node)
                stack.pop()

    gt = _transpose(g)
    visited = set()
    result: List[List[int]] = []
    for node in reversed(finish_order):
        if node in visited:
            continue
        component = []
        stack = [node]
        visited.add(node)
        while stack:
            u = stack.pop()
            component.append(u)
            for v, _ in gt.neighbors(u):
                if v not in visited:
                    visited.add(v)
                    stack.append(v)
        result.append(component)
    return result
