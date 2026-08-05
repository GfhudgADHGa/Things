import random

import pytest

from graphs.graph import Graph
from graphs.topo_sort import kahn_topo_sort, is_valid_topo_order


def _random_dag(rng, n, edge_prob):
    """Edges only go from lower to higher index, guaranteeing a DAG,
    then node labels are shuffled so the "obvious" order isn't the
    answer."""
    labels = list(range(n))
    rng.shuffle(labels)
    g = Graph(directed=True)
    for lbl in labels:
        g.add_node(lbl)
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < edge_prob:
                g.add_edge(labels[i], labels[j])
    return g


@pytest.mark.parametrize("seed", range(300))
def test_valid_topo_order_on_random_dags(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 15)
    g = _random_dag(rng, n, 0.3)
    order = kahn_topo_sort(g)
    assert order is not None
    assert sorted(order) == sorted(g.nodes())
    assert is_valid_topo_order(g, order)


def test_detects_cycle():
    g = Graph(directed=True)
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 0)
    assert kahn_topo_sort(g) is None


@pytest.mark.parametrize("seed", range(100))
def test_detects_cycle_embedded_in_larger_dag(seed):
    rng = random.Random(seed + 10_000)
    n = rng.randint(4, 12)
    g = _random_dag(rng, n, 0.25)
    nodes = g.nodes()
    if len(nodes) < 2:
        pytest.skip("too few nodes to add a cycle")
    a, b = rng.sample(nodes, 2)
    g.add_edge(max(a, b), min(a, b))
    g.add_edge(min(a, b), max(a, b))
    assert kahn_topo_sort(g) is None


def test_requires_directed_graph():
    g = Graph(directed=False)
    with pytest.raises(ValueError):
        kahn_topo_sort(g)


def test_empty_graph():
    g = Graph(directed=True)
    assert kahn_topo_sort(g) == []


def test_single_node_no_edges():
    g = Graph(directed=True)
    g.add_node(0)
    assert kahn_topo_sort(g) == [0]
