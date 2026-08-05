import random

import pytest

from graphs.graph import Graph
from graphs.scc import tarjan_scc, kosaraju_scc
from graphs.brute_force import brute_force_scc


def _random_directed_graph(rng, n, edge_prob):
    g = Graph(directed=True)
    for u in range(n):
        g.add_node(u)
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < edge_prob:
                g.add_edge(u, v)
    return g


def _as_frozenset_of_frozensets(components):
    return frozenset(frozenset(c) for c in components)


@pytest.mark.parametrize("seed", range(300))
def test_tarjan_matches_kosaraju(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 12)
    edge_prob = rng.choice([0.1, 0.2, 0.4, 0.6])
    g = _random_directed_graph(rng, n, edge_prob)
    comps = tarjan_scc(g)
    t = _as_frozenset_of_frozensets(comps)
    k = _as_frozenset_of_frozensets(kosaraju_scc(g))
    assert t == k
    all_nodes = set()
    for comp in comps:
        all_nodes.update(comp)
    assert all_nodes == set(g.nodes())


@pytest.mark.parametrize("seed", range(200))
def test_matches_brute_force(seed):
    rng = random.Random(seed + 10_000)
    n = rng.randint(1, 8)
    edge_prob = rng.choice([0.15, 0.3, 0.5])
    g = _random_directed_graph(rng, n, edge_prob)
    t = _as_frozenset_of_frozensets(tarjan_scc(g))
    bf = _as_frozenset_of_frozensets(brute_force_scc(g))
    assert t == bf


def test_single_cycle_is_one_component():
    g = Graph(directed=True)
    for i in range(5):
        g.add_edge(i, (i + 1) % 5)
    comps = tarjan_scc(g)
    assert len(comps) == 1
    assert set(comps[0]) == {0, 1, 2, 3, 4}


def test_dag_has_all_singleton_components():
    g = Graph(directed=True)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(0, 2)
    comps = tarjan_scc(g)
    assert sorted(len(c) for c in comps) == [1, 1, 1]


def test_disconnected_nodes_are_their_own_components():
    g = Graph(directed=True)
    g.add_node(0)
    g.add_node(1)
    g.add_node(2)
    comps = _as_frozenset_of_frozensets(tarjan_scc(g))
    assert comps == frozenset({frozenset({0}), frozenset({1}), frozenset({2})})


def test_large_chain_does_not_blow_recursion_limit():
    n = 5000
    g = Graph(directed=True)
    for i in range(n - 1):
        g.add_edge(i, i + 1)
    comps = tarjan_scc(g)
    assert len(comps) == n
    comps_k = kosaraju_scc(g)
    assert len(comps_k) == n
