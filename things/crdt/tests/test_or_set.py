import random

import pytest

from crdt.or_set import ORSet


def test_add_and_contains():
    s = ORSet("A")
    s.add("x")
    assert s.contains("x")
    assert s.elements() == {"x"}


def test_remove():
    s = ORSet("A")
    s.add("x")
    s.remove("x")
    assert not s.contains("x")
    assert s.elements() == set()


def test_remove_of_absent_element_is_a_no_op():
    s = ORSet("A")
    s.remove("nonexistent")  # must not raise
    assert s.elements() == set()


def test_add_wins_on_concurrent_add_and_remove():
    # Replica B removes "x" without ever having observed replica A's
    # concurrent add of "x" -- B's remove can only tombstone tags it has
    # actually seen, so A's add-tag is untouched and survives the merge.
    a, b = ORSet("A"), ORSet("B")
    b.add("x")
    b.remove("x")  # B adds and removes locally first
    a.add("x")     # A adds concurrently, unaware of B's remove
    merged = a.merge(b)
    assert merged.contains("x")  # add-wins: A's add-tag was never observed by B's remove


def test_remove_then_add_by_the_same_replica_makes_element_present_again():
    s = ORSet("A")
    s.add("x")
    s.remove("x")
    s.add("x")  # a fresh tag, not covered by the earlier tombstone
    assert s.contains("x")


def test_merge_of_a_removed_element_with_a_replica_that_never_saw_it_stays_removed():
    a, b = ORSet("A"), ORSet("B")
    a.add("x")
    a.remove("x")
    # b never added or removed x at all
    merged = a.merge(b)
    assert not merged.contains("x")


def _random_orset(replica_id, rng, n, universe):
    s = ORSet(replica_id)
    for _ in range(n):
        element = rng.choice(universe)
        if rng.random() < 0.6:
            s.add(element)
        else:
            s.remove(element)
    return s


UNIVERSE = ["a", "b", "c", "d"]


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_commutative(seed):
    rng = random.Random(seed)
    a = _random_orset("A", rng, rng.randint(0, 8), UNIVERSE)
    b = _random_orset("B", rng, rng.randint(0, 8), UNIVERSE)
    assert a.merge(b).state() == b.merge(a).state()


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_associative(seed):
    rng = random.Random(seed)
    a = _random_orset("A", rng, rng.randint(0, 6), UNIVERSE)
    b = _random_orset("B", rng, rng.randint(0, 6), UNIVERSE)
    c = _random_orset("C", rng, rng.randint(0, 6), UNIVERSE)
    assert a.merge(b).merge(c).state() == a.merge(b.merge(c)).state()


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_idempotent(seed):
    rng = random.Random(seed)
    a = _random_orset("A", rng, rng.randint(0, 10), UNIVERSE)
    assert a.merge(a).state() == a.state()


@pytest.mark.parametrize("seed", range(50))
def test_convergence_under_random_gossip_with_duplicates(seed):
    rng = random.Random(seed)
    num_replicas = rng.randint(2, 5)
    replicas = [ORSet(f"r{i}") for i in range(num_replicas)]

    for r in replicas:
        for _ in range(rng.randint(0, 6)):
            element = rng.choice(UNIVERSE)
            if rng.random() < 0.6:
                r.add(element)
            else:
                r.remove(element)

    for _ in range(rng.randint(20, 60)):
        i, j = rng.randrange(num_replicas), rng.randrange(num_replicas)
        replicas[i] = replicas[i].merge(replicas[j])

    fully_merged = replicas[0]
    for r in replicas[1:]:
        fully_merged = fully_merged.merge(r)
    final_states = [r.merge(fully_merged).state() for r in replicas]
    assert all(s == final_states[0] for s in final_states)
