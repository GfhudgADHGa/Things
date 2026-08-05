import random

import pytest

from graphs.graph import Graph
from graphs.maxflow import edmonds_karp, min_cut
from graphs.brute_force import brute_force_max_flow, brute_force_min_cut_capacity


def _random_dag_like_flow_graph(rng, n, edge_prob, weight_range):
    """Directed graph with edges only from lower-numbered to
    higher-numbered nodes (guarantees no cycles, keeps brute-force path
    enumeration finite and fast)."""
    g = Graph(directed=True)
    for u in range(n):
        g.add_node(u)
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < edge_prob:
                g.add_edge(u, v, round(rng.uniform(*weight_range), 2))
    return g


@pytest.mark.parametrize("seed", range(300))
def test_max_flow_equals_min_cut_capacity_exactly(seed):
    """The max-flow min-cut theorem, checked as an exact equality on
    every trial -- not an approximation, a proof that the algorithm's
    two outputs (flow value, cut capacity) must coincide."""
    rng = random.Random(seed)
    n = rng.randint(2, 10)
    g = _random_dag_like_flow_graph(rng, n, 0.4, (1.0, 20.0))
    flow_value, _ = edmonds_karp(g, 0, n - 1)
    cut_capacity, cut_edges, reachable = min_cut(g, 0, n - 1)
    assert flow_value == pytest.approx(cut_capacity)
    assert 0 in reachable
    assert (n - 1) not in reachable


@pytest.mark.parametrize("seed", range(80))
def test_matches_brute_force_max_flow_on_tiny_graphs(seed):
    rng = random.Random(seed + 10_000)
    n = rng.randint(2, 5)
    g = _random_dag_like_flow_graph(rng, n, 0.5, (1.0, 6.0))
    flow_value, _ = edmonds_karp(g, 0, n - 1)
    bf = brute_force_max_flow(g, 0, n - 1)
    assert flow_value == pytest.approx(bf)


@pytest.mark.parametrize("seed", range(80))
def test_matches_brute_force_min_cut_on_tiny_graphs(seed):
    rng = random.Random(seed + 20_000)
    n = rng.randint(2, 6)
    g = _random_dag_like_flow_graph(rng, n, 0.45, (1.0, 8.0))
    cut_capacity, _, _ = min_cut(g, 0, n - 1)
    bf = brute_force_min_cut_capacity(g, 0, n - 1)
    assert cut_capacity == pytest.approx(bf)


def test_classic_textbook_example():
    """Cormen/Leiserson/Rivest/Stein's canonical max-flow figure: max
    flow is exactly 23."""
    g = Graph(directed=True)
    edges = [
        ("s", "a", 16), ("s", "c", 13),
        ("a", "c", 10), ("c", "a", 4),
        ("a", "b", 12), ("c", "d", 14),
        ("d", "b", 7), ("b", "c", 9),
        ("d", "t", 4), ("b", "t", 20),
    ]
    for u, v, w in edges:
        g.add_edge(u, v, w)
    flow_value, _ = edmonds_karp(g, "s", "t")
    assert flow_value == pytest.approx(23.0)
    cut_capacity, _, _ = min_cut(g, "s", "t")
    assert cut_capacity == pytest.approx(23.0)


def test_no_path_gives_zero_flow():
    g = Graph(directed=True)
    g.add_edge(0, 1, 5.0)
    g.add_node(2)
    flow_value, _ = edmonds_karp(g, 0, 2)
    assert flow_value == 0.0
    cut_capacity, _, _ = min_cut(g, 0, 2)
    assert cut_capacity == 0.0
