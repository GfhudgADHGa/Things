import random

import pytest

from crdt.lww_register import LWWRegister


def test_set_and_value():
    r = LWWRegister("A")
    r.set("hello", 1.0)
    assert r.value == "hello"


def test_later_timestamp_wins_on_merge():
    a, b = LWWRegister("A"), LWWRegister("B")
    a.set("old", 1.0)
    b.set("new", 2.0)
    assert a.merge(b).value == "new"
    assert b.merge(a).value == "new"


def test_earlier_local_set_does_not_overwrite_a_later_one():
    r = LWWRegister("A")
    r.set("second", 5.0)
    r.set("first", 1.0)  # an out-of-order / stale write
    assert r.value == "second"


def test_tiebreak_by_replica_id_on_equal_timestamps():
    a, b = LWWRegister("A"), LWWRegister("B")
    a.set("from_a", 1.0)
    b.set("from_b", 1.0)  # exact same timestamp
    # merge must be deterministic regardless of direction: whichever
    # replica_id wins the tiebreak, both merge orders must agree
    assert a.merge(b).value == b.merge(a).value


def test_three_way_merge_preserves_the_correct_writer_through_an_intermediate_hop():
    # The scenario the module docstring calls out: B has the winning
    # write. Merging A with B first (producing an intermediate register
    # that must remember B actually wrote it), then merging that with C,
    # must still produce B's value -- this fails if merge() forgets
    # *who* wrote the winning value and reports the merging replica's
    # own id instead.
    a, b, c = LWWRegister("A"), LWWRegister("B"), LWWRegister("C")
    b.set("from_B", 5.0)
    intermediate = a.merge(b)
    assert intermediate.value == "from_B"
    assert intermediate.writer_id == "B"
    final = intermediate.merge(c)
    assert final.value == "from_B"
    assert final.writer_id == "B"


def _random_lww(replica_id, rng, n):
    r = LWWRegister(replica_id)
    t = 0.0
    for _ in range(n):
        t += rng.uniform(0.1, 2.0)
        r.set(f"{replica_id}-{_}", t)
    return r


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_commutative(seed):
    rng = random.Random(seed)
    a = _random_lww("A", rng, rng.randint(0, 5))
    b = _random_lww("B", rng, rng.randint(0, 5))
    assert a.merge(b).state() == b.merge(a).state()


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_associative(seed):
    rng = random.Random(seed)
    a = _random_lww("A", rng, rng.randint(0, 5))
    b = _random_lww("B", rng, rng.randint(0, 5))
    c = _random_lww("C", rng, rng.randint(0, 5))
    assert a.merge(b).merge(c).state() == a.merge(b.merge(c)).state()


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_idempotent(seed):
    rng = random.Random(seed)
    a = _random_lww("A", rng, rng.randint(0, 10))
    assert a.merge(a).state() == a.state()


@pytest.mark.parametrize("seed", range(50))
def test_convergence_under_random_gossip_with_duplicates(seed):
    rng = random.Random(seed)
    num_replicas = rng.randint(2, 6)
    replicas = [LWWRegister(f"r{i}") for i in range(num_replicas)]

    t = 0.0
    for r in replicas:
        for _ in range(rng.randint(0, 4)):
            t += rng.uniform(0.1, 1.0)
            r.set(f"val-{t}", t)

    for _ in range(rng.randint(20, 60)):
        i, j = rng.randrange(num_replicas), rng.randrange(num_replicas)
        replicas[i] = replicas[i].merge(replicas[j])

    fully_merged = replicas[0]
    for r in replicas[1:]:
        fully_merged = fully_merged.merge(r)
    final_states = [r.merge(fully_merged).state() for r in replicas]
    assert all(s == final_states[0] for s in final_states)
