from graphs.graph import Graph


def test_undirected_edge_is_symmetric():
    g = Graph(directed=False)
    g.add_edge(0, 1, 3.0)
    assert (1, 3.0) in g.neighbors(0)
    assert (0, 3.0) in g.neighbors(1)


def test_directed_edge_is_one_way():
    g = Graph(directed=True)
    g.add_edge(0, 1, 3.0)
    assert (1, 3.0) in g.neighbors(0)
    assert g.neighbors(1) == []


def test_edges_deduplicated_for_undirected():
    g = Graph(directed=False)
    g.add_edge(0, 1, 1.0)
    g.add_edge(2, 3, 1.0)
    edges = g.edges()
    assert len(edges) == 2


def test_edges_not_deduplicated_for_directed():
    g = Graph(directed=True)
    g.add_edge(0, 1, 1.0)
    g.add_edge(1, 0, 1.0)
    assert len(g.edges()) == 2


def test_copy_is_independent():
    g = Graph(directed=False)
    g.add_edge(0, 1, 1.0)
    g2 = g.copy()
    g2.add_edge(1, 2, 1.0)
    assert 2 not in g.adj
    assert 2 in g2.adj


def test_isolated_node_has_no_neighbors():
    g = Graph(directed=True)
    g.add_node(5)
    assert g.neighbors(5) == []
    assert 5 in g.nodes()
