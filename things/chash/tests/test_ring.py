import random
import statistics

import pytest

from chash.ring import ConsistentHashRing
from chash.naive import naive_route
from chash.brute_force import brute_force_get_node


def _random_ring(rng, n_nodes, vnodes):
    ring = ConsistentHashRing(virtual_nodes_per_physical=vnodes)
    nodes = [f"node-{i}" for i in range(n_nodes)]
    for node in nodes:
        ring.add_node(node)
    return ring, nodes


@pytest.mark.parametrize("seed", range(150))
def test_matches_brute_force(seed):
    rng = random.Random(seed)
    n_nodes = rng.randint(1, 12)
    vnodes = rng.randint(1, 50)
    ring, nodes = _random_ring(rng, n_nodes, vnodes)
    for i in range(20):
        key = f"key-{seed}-{i}-{rng.random()}"
        assert ring.get_node(key) == brute_force_get_node(key, nodes, vnodes)


@pytest.mark.parametrize("seed", range(50))
def test_deterministic(seed):
    rng = random.Random(seed)
    ring, _ = _random_ring(rng, rng.randint(2, 8), 40)
    key = f"stable-key-{seed}"
    first = ring.get_node(key)
    for _ in range(10):
        assert ring.get_node(key) == first


@pytest.mark.parametrize("seed", range(50))
def test_returns_only_valid_nodes(seed):
    rng = random.Random(seed)
    ring, nodes = _random_ring(rng, rng.randint(1, 10), 30)
    for i in range(100):
        assert ring.get_node(f"k{i}") in set(nodes)


@pytest.mark.parametrize("seed", range(60))
def test_adding_a_node_only_ever_reassigns_keys_to_the_new_node(seed):
    rng = random.Random(seed)
    n_nodes = rng.randint(2, 10)
    vnodes = 50
    ring, nodes = _random_ring(rng, n_nodes, vnodes)
    keys = [f"key-{i}" for i in range(500)]
    before = {k: ring.get_node(k) for k in keys}

    new_node = "new-node"
    ring.add_node(new_node)
    after = {k: ring.get_node(k) for k in keys}

    for k in keys:
        if before[k] != after[k]:
            assert after[k] == new_node, (k, before[k], after[k])


@pytest.mark.parametrize("seed", range(60))
def test_removing_a_node_only_changes_that_nodes_own_keys(seed):
    rng = random.Random(seed)
    n_nodes = rng.randint(3, 10)
    vnodes = 50
    ring, nodes = _random_ring(rng, n_nodes, vnodes)
    keys = [f"key-{i}" for i in range(500)]
    before = {k: ring.get_node(k) for k in keys}

    victim = nodes[0]
    ring.remove_node(victim)
    after = {k: ring.get_node(k) for k in keys}

    for k in keys:
        if before[k] == victim:
            assert after[k] != victim
        else:
            assert after[k] == before[k], (k, before[k], after[k])


def test_minimal_disruption_close_to_theoretical_1_over_n_plus_1():
    rng = random.Random(42)
    n_nodes = 10
    ring, nodes = _random_ring(rng, n_nodes, 200)
    keys = [f"key-{i}" for i in range(20000)]
    before = {k: ring.get_node(k) for k in keys}

    ring.add_node("new-node")
    after = {k: ring.get_node(k) for k in keys}

    changed = sum(1 for k in keys if before[k] != after[k])
    fraction = changed / len(keys)
    expected = 1 / (n_nodes + 1)
    # generous band: real ring behavior fluctuates around the expected
    # fraction depending on how virtual node positions happen to land,
    # but should stay within a small constant factor of it
    assert expected * 0.4 < fraction < expected * 2.5, (fraction, expected)


def test_naive_hashing_remaps_far_more_than_consistent_hashing():
    rng = random.Random(7)
    n_nodes = 10
    nodes = [f"node-{i}" for i in range(n_nodes)]
    keys = [f"key-{i}" for i in range(20000)]

    before = {k: naive_route(k, nodes) for k in keys}
    after = {k: naive_route(k, nodes + ["new-node"]) for k in keys}
    naive_fraction = sum(1 for k in keys if before[k] != after[k]) / len(keys)

    ring, _ = _random_ring(rng, n_nodes, 200)
    ch_before = {k: ring.get_node(k) for k in keys}
    ring.add_node("new-node")
    ch_after = {k: ring.get_node(k) for k in keys}
    ch_fraction = sum(1 for k in keys if ch_before[k] != ch_after[k]) / len(keys)

    assert naive_fraction > 0.5
    assert ch_fraction < naive_fraction / 3


def test_more_virtual_nodes_gives_more_uniform_load():
    rng = random.Random(11)
    n_nodes = 8
    keys = [f"key-{i}" for i in range(20000)]

    def load_coefficient_of_variation(vnodes):
        ring, nodes = _random_ring(rng, n_nodes, vnodes)
        counts = {n: 0 for n in nodes}
        for k in keys:
            counts[ring.get_node(k)] += 1
        values = list(counts.values())
        return statistics.stdev(values) / statistics.mean(values)

    cv_few = load_coefficient_of_variation(1)
    cv_many = load_coefficient_of_variation(200)
    assert cv_many < cv_few


def test_every_node_gets_a_share_with_enough_virtual_nodes():
    rng = random.Random(13)
    ring, nodes = _random_ring(rng, 6, 100)
    counts = {n: 0 for n in nodes}
    for i in range(5000):
        counts[ring.get_node(f"key-{i}")] += 1
    assert all(c > 0 for c in counts.values())


def test_duplicate_add_raises():
    ring = ConsistentHashRing()
    ring.add_node("a")
    with pytest.raises(ValueError):
        ring.add_node("a")


def test_remove_missing_raises():
    ring = ConsistentHashRing()
    with pytest.raises(ValueError):
        ring.remove_node("ghost")


def test_get_node_on_empty_ring_raises():
    ring = ConsistentHashRing()
    with pytest.raises(RuntimeError):
        ring.get_node("anything")


def test_rejects_nonpositive_vnodes():
    with pytest.raises(ValueError):
        ConsistentHashRing(virtual_nodes_per_physical=0)


def test_naive_route_rejects_empty_node_list():
    with pytest.raises(RuntimeError):
        naive_route("key", [])
