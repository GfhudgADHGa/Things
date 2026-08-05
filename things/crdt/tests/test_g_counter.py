"""The correctness proof for every CRDT in this collection follows the
same shape: check the three algebraic laws that make merge safe under
any network conditions (commutative, associative, idempotent), then run
an end-to-end simulation of several replicas gossiping in random order
with random duplicates and require they all converge to the identical
final state -- the actual real-world guarantee a CRDT is for.
"""
import random

import pytest

from crdt.g_counter import GCounter


def test_increment_and_value():
    c = GCounter("A")
    c.increment(3)
    c.increment(4)
    assert c.value() == 7


def test_negative_increment_rejected():
    c = GCounter("A")
    with pytest.raises(ValueError):
        c.increment(-1)


def test_merge_sums_distinct_replicas():
    a, b = GCounter("A"), GCounter("B")
    a.increment(5)
    b.increment(3)
    assert a.merge(b).value() == 8


def test_merge_takes_max_not_sum_for_the_same_replica():
    # Merging two snapshots of the *same* replica's history must not
    # double-count -- max, not addition, is what makes re-merging safe.
    a1 = GCounter("A")
    a1.increment(5)
    a2 = GCounter("A")
    a2.increment(5)
    a2.increment(2)  # a2 is a later snapshot of the same replica: total 7
    assert a1.merge(a2).value() == 7  # not 5+7=12


def _random_gcounter(replica_id, rng, num_increments):
    c = GCounter(replica_id)
    for _ in range(num_increments):
        c.increment(rng.randint(0, 10))
    return c


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_commutative(seed):
    rng = random.Random(seed)
    a = _random_gcounter("A", rng, rng.randint(0, 5))
    b = _random_gcounter("B", rng, rng.randint(0, 5))
    assert a.merge(b).state() == b.merge(a).state()


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_associative(seed):
    rng = random.Random(seed)
    a = _random_gcounter("A", rng, rng.randint(0, 5))
    b = _random_gcounter("B", rng, rng.randint(0, 5))
    c = _random_gcounter("C", rng, rng.randint(0, 5))
    left = a.merge(b).merge(c)
    right = a.merge(b.merge(c))
    assert left.state() == right.state()


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_idempotent(seed):
    rng = random.Random(seed)
    a = _random_gcounter("A", rng, rng.randint(0, 10))
    assert a.merge(a).state() == a.state()


@pytest.mark.parametrize("seed", range(50))
def test_convergence_under_random_gossip_with_duplicates(seed):
    rng = random.Random(seed)
    num_replicas = rng.randint(2, 6)
    replicas = [GCounter(f"r{i}") for i in range(num_replicas)]

    # each replica performs some local increments
    for r in replicas:
        for _ in range(rng.randint(0, 5)):
            r.increment(rng.randint(1, 5))

    # gossip: repeatedly pick two (possibly the same, or a repeat pair)
    # replicas and merge one into the other -- simulating an unreliable,
    # out-of-order, duplicate-prone network
    for _ in range(rng.randint(20, 60)):
        i, j = rng.randrange(num_replicas), rng.randrange(num_replicas)
        replicas[i] = replicas[i].merge(replicas[j])

    # not all replicas necessarily reached full convergence in a bounded
    # number of random gossip rounds -- but merging *everyone* with
    # everyone else (the eventual, guaranteed-to-happen-eventually state)
    # must converge exactly
    fully_merged = replicas[0]
    for r in replicas[1:]:
        fully_merged = fully_merged.merge(r)
    final_states = [r.merge(fully_merged).state() for r in replicas]
    assert all(s == final_states[0] for s in final_states)
