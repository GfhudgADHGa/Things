"""Happy-path cluster behavior: a healthy network should elect exactly
one leader and faithfully replicate client commands to every node."""
import random

import pytest

from raft.cluster import Cluster
from raft.network import Network
from raft.node import Role


def make_cluster(node_ids=(1, 2, 3, 4, 5), seed=0, **network_kwargs):
    rng = random.Random(seed)
    net = Network(rng, **network_kwargs)
    return Cluster(list(node_ids), net, rng)


@pytest.mark.parametrize("seed", range(10))
def test_a_healthy_cluster_elects_exactly_one_leader(seed):
    cluster = make_cluster(seed=seed)
    cluster.run_until(1000)
    leader = cluster.leader()
    assert leader is not None
    assert leader.role == Role.LEADER
    followers = [n for n in cluster.nodes.values() if n.node_id != leader.node_id]
    assert all(n.role == Role.FOLLOWER for n in followers)


def test_all_nodes_agree_on_the_leader():
    cluster = make_cluster(seed=1)
    cluster.run_until(1000)
    leader = cluster.leader()
    for node in cluster.nodes.values():
        assert node.leader_id == leader.node_id


def test_client_commands_replicate_to_every_node_in_order():
    cluster = make_cluster(seed=2)
    cluster.run_until(1000)
    commands = [f"cmd{i}" for i in range(10)]
    for cmd in commands:
        assert cluster.client_append(cmd) is True
        cluster.run_until(cluster.now + 100)
    cluster.run_until(cluster.now + 500)

    for node in cluster.nodes.values():
        assert node.state_machine == commands


def test_client_append_fails_with_no_elected_leader_yet():
    cluster = make_cluster(seed=3)
    # nothing has run yet -- no election has happened
    assert cluster.client_append("too early") is False


def test_single_node_cluster_is_immediately_its_own_leader():
    cluster = make_cluster(node_ids=(1,), seed=4)
    cluster.run_until(1000)
    leader = cluster.leader()
    assert leader is not None
    assert leader.node_id == 1
    assert cluster.client_append("solo") is True
    cluster.run_until(cluster.now + 200)
    assert cluster.nodes[1].state_machine == ["solo"]


def test_lossy_network_still_eventually_elects_a_leader_and_replicates():
    cluster = make_cluster(seed=5, drop_probability=0.2)
    cluster.run_until(3000)
    leader = cluster.leader()
    assert leader is not None
    assert cluster.client_append("through the noise") is True
    cluster.run_until(cluster.now + 5000)
    assert all(n.state_machine == ["through the noise"] for n in cluster.nodes.values())
