import random

from raft.network import Network


def test_fully_connected_by_default():
    net = Network(random.Random(0))
    assert net.connected(1, 2) is True
    assert net.connected(1, 1) is True


def test_partition_splits_groups_both_directions():
    net = Network(random.Random(0))
    net.partition([[1, 2], [3, 4, 5]])
    assert net.connected(1, 2) is True
    assert net.connected(4, 5) is True
    assert net.connected(1, 3) is False
    assert net.connected(3, 1) is False


def test_heal_restores_full_connectivity():
    net = Network(random.Random(0))
    net.partition([[1], [2, 3]])
    net.heal()
    assert net.connected(1, 2) is True


def test_partitioned_nodes_never_get_a_delay():
    net = Network(random.Random(0), min_delay=1, max_delay=5, drop_probability=0.0)
    net.partition([[1], [2]])
    for _ in range(50):
        assert net.transmit_delay_or_none(1, 2) is None


def test_delay_is_within_configured_bounds():
    net = Network(random.Random(0), min_delay=3, max_delay=7, drop_probability=0.0)
    for _ in range(200):
        delay = net.transmit_delay_or_none(1, 2)
        assert delay is not None
        assert 3 <= delay <= 7


def test_drop_probability_of_one_drops_everything():
    net = Network(random.Random(0), drop_probability=1.0)
    for _ in range(50):
        assert net.transmit_delay_or_none(1, 2) is None


def test_drop_probability_of_zero_never_drops_when_connected():
    net = Network(random.Random(0), drop_probability=0.0)
    for _ in range(200):
        assert net.transmit_delay_or_none(1, 2) is not None
