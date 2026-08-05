import math
import random

import pytest

from graphs.graph import Graph
from graphs.shortest_path import dijkstra, bellman_ford, floyd_warshall
from graphs.brute_force import brute_force_shortest_paths


def _random_graph(rng, n, edge_prob, directed, weight_range, allow_negative=False):
    g = Graph(directed=directed)
    for u in range(n):
        g.add_node(u)
    for u in range(n):
        for v in range(n):
            if u == v:
                continue
            if not directed and v < u:
                continue
            if rng.random() < edge_prob:
                lo, hi = weight_range
                w = rng.uniform(lo, hi) if allow_negative else rng.uniform(0, hi)
                g.add_edge(u, v, round(w, 3))
    return g


@pytest.mark.parametrize("seed", range(150))
def test_dijkstra_matches_bellman_ford_nonnegative(seed):
    rng = random.Random(seed)
    n = rng.randint(2, 8)
    directed = rng.random() < 0.5
    g = _random_graph(rng, n, 0.4, directed, (0.5, 10.0))
    d1 = dijkstra(g, 0)
    d2 = bellman_ford(g, 0)
    assert d2 is not None
    for node in g.nodes():
        assert d1[node] == pytest.approx(d2[node]), node


@pytest.mark.parametrize("seed", range(150))
def test_dijkstra_matches_floyd_warshall_nonnegative(seed):
    rng = random.Random(seed + 10_000)
    n = rng.randint(2, 7)
    directed = rng.random() < 0.5
    g = _random_graph(rng, n, 0.45, directed, (0.5, 10.0))
    d1 = dijkstra(g, 0)
    fw = floyd_warshall(g)
    assert fw is not None
    for node in g.nodes():
        assert d1[node] == pytest.approx(fw[(0, node)]), node


@pytest.mark.parametrize("seed", range(200))
def test_bellman_ford_matches_floyd_warshall_with_negative_weights_no_cycle(seed):
    rng = random.Random(seed + 20_000)
    n = rng.randint(2, 6)
    g = Graph(directed=True)
    for u in range(n):
        g.add_node(u)
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < 0.35:
                g.add_edge(u, v, round(rng.uniform(-3, 8), 3))
    bf = bellman_ford(g, 0)
    fw = floyd_warshall(g)
    if bf is None or fw is None:
        pytest.skip("negative cycle present, covered by a separate test")
    for node in g.nodes():
        assert bf[node] == pytest.approx(fw[(0, node)]), node


@pytest.mark.parametrize("seed", range(200))
def test_bellman_ford_and_floyd_warshall_agree_on_negative_cycle_presence(seed):
    rng = random.Random(seed + 30_000)
    n = rng.randint(2, 6)
    g = Graph(directed=True)
    for u in range(n):
        g.add_node(u)
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < 0.4:
                g.add_edge(u, v, round(rng.uniform(-4, 4), 3))
    bf = bellman_ford(g, 0)
    fw = floyd_warshall(g)
    if fw is None:
        pytest.skip("global negative cycle not necessarily reachable from source")
    # no negative cycle anywhere implies none reachable from source either
    assert bf is not None


def test_dijkstra_rejects_negative_weights():
    g = Graph(directed=True)
    g.add_edge(0, 1, -1.0)
    with pytest.raises(ValueError):
        dijkstra(g, 0)


@pytest.mark.parametrize("seed", range(200))
def test_matches_brute_force_on_small_graphs(seed):
    rng = random.Random(seed + 40_000)
    n = rng.randint(2, 6)
    directed = rng.random() < 0.5
    g = _random_graph(rng, n, 0.5, directed, (0.5, 9.0))
    d1 = dijkstra(g, 0)
    bf = brute_force_shortest_paths(g, 0)
    assert bf is not None
    for node in g.nodes():
        assert d1[node] == pytest.approx(bf[node]), node


def test_unreachable_node_has_infinite_distance():
    g = Graph(directed=True)
    g.add_edge(0, 1, 1.0)
    g.add_node(2)
    d = dijkstra(g, 0)
    assert d[2] == math.inf
    bf = bellman_ford(g, 0)
    assert bf[2] == math.inf
    fw = floyd_warshall(g)
    assert fw[(0, 2)] == math.inf


def test_bellman_ford_detects_simple_negative_cycle():
    g = Graph(directed=True)
    g.add_edge(0, 1, 1.0)
    g.add_edge(1, 2, -3.0)
    g.add_edge(2, 1, 1.0)
    assert bellman_ford(g, 0) is None


def test_floyd_warshall_detects_negative_cycle_anywhere():
    g = Graph(directed=True)
    g.add_edge(0, 1, 1.0)
    g.add_edge(2, 3, 1.0)
    g.add_edge(3, 4, -3.0)
    g.add_edge(4, 3, 1.0)
    assert floyd_warshall(g) is None
