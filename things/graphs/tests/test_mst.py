import random

import pytest

from graphs.graph import Graph
from graphs.mst import kruskal, prim, total_weight
from graphs.brute_force import brute_force_mst_weight


def _random_connected_graph(rng, n, extra_edge_prob, weight_range):
    g = Graph(directed=False)
    nodes = list(range(n))
    rng.shuffle(nodes)
    for i in range(1, n):
        u = nodes[i]
        v = nodes[rng.randint(0, i - 1)]
        g.add_edge(u, v, round(rng.uniform(*weight_range), 3))
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < extra_edge_prob:
                g.add_edge(u, v, round(rng.uniform(*weight_range), 3))
    return g


@pytest.mark.parametrize("seed", range(300))
def test_kruskal_matches_prim_total_weight(seed):
    rng = random.Random(seed)
    n = rng.randint(2, 12)
    g = _random_connected_graph(rng, n, 0.3, (1.0, 20.0))
    k = kruskal(g)
    p = prim(g, 0)
    assert len(k) == n - 1
    assert len(p) == n - 1
    assert total_weight(k) == pytest.approx(total_weight(p))


@pytest.mark.parametrize("seed", range(150))
def test_matches_brute_force_on_tiny_graphs(seed):
    rng = random.Random(seed + 10_000)
    n = rng.randint(2, 6)
    g = _random_connected_graph(rng, n, 0.4, (1.0, 15.0))
    k = kruskal(g)
    bf = brute_force_mst_weight(g)
    assert total_weight(k) == pytest.approx(bf)


@pytest.mark.parametrize("seed", range(150))
def test_unique_mst_with_distinct_weights_has_matching_edge_sets(seed):
    rng = random.Random(seed + 20_000)
    n = rng.randint(3, 9)
    g = _random_connected_graph(rng, n, 0.3, (1.0, 1000.0))
    weights = [w for _, _, w in g.edges()]
    if len(set(weights)) != len(weights):
        pytest.skip("only distinct-weight graphs have a unique MST")
    k = {frozenset((u, v)) for u, v, _ in kruskal(g)}
    p = {frozenset((u, v)) for u, v, _ in prim(g, 0)}
    assert k == p


def test_single_edge_graph():
    g = Graph(directed=False)
    g.add_edge(0, 1, 5.0)
    assert total_weight(kruskal(g)) == 5.0
    assert total_weight(prim(g, 0)) == 5.0


@pytest.mark.parametrize("seed", range(100))
def test_cut_property_every_mst_edge_is_cheapest_crossing_its_cut(seed):
    """For each edge (u, v) in the MST, removing it splits the tree into
    two components; no edge in the original graph crossing that same
    split may be strictly cheaper (the cut property, the theorem both
    algorithms are correct because of)."""
    rng = random.Random(seed + 30_000)
    n = rng.randint(3, 8)
    g = _random_connected_graph(rng, n, 0.35, (1.0, 30.0))
    mst_edges = kruskal(g)

    for removed_idx in range(len(mst_edges)):
        remaining = mst_edges[:removed_idx] + mst_edges[removed_idx + 1:]
        adj = {u: [] for u in g.nodes()}
        for u, v, _ in remaining:
            adj[u].append(v)
            adj[v].append(u)
        start = mst_edges[removed_idx][0]
        side = {start}
        stack = [start]
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if y not in side:
                    side.add(y)
                    stack.append(y)
        removed_weight = mst_edges[removed_idx][2]
        for u, v, w in g.edges():
            crosses = (u in side) != (v in side)
            if crosses:
                assert w >= removed_weight - 1e-9
