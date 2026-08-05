"""The actual correctness proof for this thing: Raft's own safety
properties (from the paper's Figure 3), checked not on the happy path
but under randomized network faults -- message loss, reordering (delays
are randomized per-message, so later-sent messages can arrive first),
partitions, and leader crashes -- across many seeds. A protocol bug that
only shows up 1 time in 50 under adversarial conditions is exactly the
kind of thing a single hand-written scenario test would never catch;
this is the same "don't just hand-pick cases you already know work"
philosophy as difftool's and minidb's fuzz tests, aimed at a much
higher-stakes kind of bug.

Two real bugs were caught getting this far (see raft/node.py and
cluster.py's comments): a single-node cluster never became leader
(nothing ever triggers become_leader() with zero peers to reply), and
even after that fix, it never committed anything either (nothing ever
triggers the commit-index check with zero peers to reply). Both were
found by a plain scenario test, before fault injection was even
involved -- which is the point of building up from simple tests to
adversarial ones rather than jumping straight to the hardest case.
"""
import random

import pytest

from raft.cluster import Cluster
from raft.network import Network


def assert_election_safety(cluster: Cluster) -> None:
    """At most one node may ever have won the election for a given term."""
    for term, winners in cluster.leader_history.items():
        assert len(winners) <= 1, f"term {term} had multiple leaders: {winners}"


def assert_log_matching(cluster: Cluster) -> None:
    """If two logs contain an entry with the same index and term, the
    logs are identical in every entry up to and including that index."""
    nodes = list(cluster.nodes.values())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            log_a, log_b = nodes[i].log, nodes[j].log
            diverged = False
            for k in range(min(len(log_a), len(log_b))):
                term_a, _ = log_a[k]
                term_b, _ = log_b[k]
                if term_a == term_b:
                    assert not diverged, (
                        f"log matching violated between {nodes[i].node_id} and "
                        f"{nodes[j].node_id} at index {k + 1}"
                    )
                    assert log_a[k] == log_b[k]
                else:
                    diverged = True


def assert_state_machine_safety(cluster: Cluster) -> None:
    """If two servers have both applied an entry at a given index, it
    must be the same entry -- equivalently, one node's applied sequence
    is always a prefix of the other's (or vice versa)."""
    nodes = list(cluster.nodes.values())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i].state_machine, nodes[j].state_machine
            n = min(len(a), len(b))
            assert a[:n] == b[:n], (
                f"state machine safety violated between {nodes[i].node_id} and {nodes[j].node_id}"
            )


def assert_all_safety_properties(cluster: Cluster) -> None:
    assert_election_safety(cluster)
    assert_log_matching(cluster)
    assert_state_machine_safety(cluster)


def make_cluster(node_ids, seed, **network_kwargs):
    rng = random.Random(seed)
    net = Network(rng, **network_kwargs)
    return Cluster(list(node_ids), net, rng), net, rng


@pytest.mark.parametrize("seed", range(40))
def test_lossy_network_preserves_all_safety_properties(seed):
    cluster, net, rng = make_cluster([1, 2, 3, 4, 5], seed, drop_probability=0.3, max_delay=15)
    for round_num in range(8):
        cluster.run_until(cluster.now + 400)
        cluster.client_append(f"round{round_num}")
        assert_all_safety_properties(cluster)
    cluster.run_until(cluster.now + 2000)
    assert_all_safety_properties(cluster)


@pytest.mark.parametrize("seed", range(30))
def test_repeated_partitions_preserve_all_safety_properties(seed):
    rng = random.Random(seed)
    net = Network(rng, max_delay=10, drop_probability=0.05)
    cluster = Cluster([1, 2, 3, 4, 5], net, rng)
    cluster.run_until(600)

    for _ in range(6):
        # a random 2-3 / 3-2 split (minority side can never elect a
        # leader on its own -- 2 or 3 nodes can't reach a 5-node majority
        # of 3 -- so at most one side keeps making progress)
        ids = [1, 2, 3, 4, 5]
        rng.shuffle(ids)
        split = rng.choice([2, 3])
        net.partition([ids[:split], ids[split:]])
        cluster.run_until(cluster.now + 800)
        cluster.client_append(f"during-partition-{cluster.now}")
        assert_all_safety_properties(cluster)

        net.heal()
        cluster.run_until(cluster.now + 800)
        assert_all_safety_properties(cluster)

    cluster.run_until(cluster.now + 2000)
    assert_all_safety_properties(cluster)


@pytest.mark.parametrize("seed", range(30))
def test_random_leader_crashes_preserve_all_safety_properties_and_committed_entries_survive(seed):
    rng = random.Random(seed)
    net = Network(rng, max_delay=10, drop_probability=0.1)
    cluster = Cluster([1, 2, 3, 4, 5], net, rng)
    cluster.run_until(600)

    committed_commands = []
    for round_num in range(6):
        cluster.run_until(cluster.now + 500)
        command = f"cmd{round_num}"
        accepted = cluster.client_append(command)
        if accepted:
            # client_append() returning True only means the *leader*
            # appended it to its own log -- not that it committed. An
            # entry that's appended but hasn't yet replicated to a
            # majority is allowed to be lost if its leader crashes
            # before replicating it; only entries that actually reach
            # a majority (visible via the leader's own state machine
            # once applied) carry Raft's durability guarantee. Give it
            # a chance to actually replicate before deciding whether to
            # hold it to that guarantee.
            cluster.run_until(cluster.now + 400)
            leader = cluster.leader()
            if leader is not None and command in leader.state_machine:
                committed_commands.append(command)
        assert_all_safety_properties(cluster)

        leader = cluster.leader()
        if leader is not None and rng.random() < 0.6:
            crashed_id = leader.node_id
            cluster.crash(crashed_id)
            cluster.run_until(cluster.now + 600)
            assert_all_safety_properties(cluster)
            cluster.recover(crashed_id)
            cluster.run_until(cluster.now + 300)

    cluster.run_until(cluster.now + 3000)
    assert_all_safety_properties(cluster)

    # Every command that was ever accepted by a leader (client_append
    # returned True) must have survived every subsequent leader crash --
    # this is the practically-meaningful payoff of the safety properties
    # above: once acknowledged, a command is never silently lost.
    alive_nodes = [n for nid, n in cluster.nodes.items() if nid not in cluster.crashed]
    for node in alive_nodes:
        for command in committed_commands:
            assert command in node.state_machine, (
                f"committed command {command!r} missing from node {node.node_id}'s state machine"
            )


@pytest.mark.parametrize("seed", range(20))
def test_severe_faults_combined_still_preserve_safety_properties(seed):
    # The worst-case combination: heavy message loss AND a partition AND
    # a leader crash all in the same run.
    rng = random.Random(seed)
    net = Network(rng, max_delay=20, drop_probability=0.35)
    cluster = Cluster([1, 2, 3, 4, 5], net, rng)
    cluster.run_until(800)

    cluster.client_append("before-chaos")
    ids = [1, 2, 3, 4, 5]
    rng.shuffle(ids)
    net.partition([ids[:2], ids[2:]])
    cluster.run_until(cluster.now + 1000)
    assert_all_safety_properties(cluster)

    leader = cluster.leader()
    if leader is not None:
        cluster.crash(leader.node_id)
    net.heal()
    cluster.run_until(cluster.now + 2000)
    assert_all_safety_properties(cluster)

    cluster.client_append("after-chaos")
    cluster.run_until(cluster.now + 2000)
    assert_all_safety_properties(cluster)
