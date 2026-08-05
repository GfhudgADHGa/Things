import random

import pytest

from crdt.pn_counter import PNCounter


def test_increment_and_decrement():
    c = PNCounter("A")
    c.increment(10)
    c.decrement(3)
    assert c.value() == 7


def test_merge_combines_independent_replicas():
    a, b = PNCounter("A"), PNCounter("B")
    a.increment(5)
    b.decrement(2)
    assert a.merge(b).value() == 3


def _random_pncounter(replica_id, rng, n):
    c = PNCounter(replica_id)
    for _ in range(n):
        if rng.random() < 0.5:
            c.increment(rng.randint(0, 10))
        else:
            c.decrement(rng.randint(0, 10))
    return c


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_commutative(seed):
    rng = random.Random(seed)
    a = _random_pncounter("A", rng, rng.randint(0, 5))
    b = _random_pncounter("B", rng, rng.randint(0, 5))
    assert a.merge(b).state() == b.merge(a).state()


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_associative(seed):
    rng = random.Random(seed)
    a = _random_pncounter("A", rng, rng.randint(0, 5))
    b = _random_pncounter("B", rng, rng.randint(0, 5))
    c = _random_pncounter("C", rng, rng.randint(0, 5))
    assert a.merge(b).merge(c).state() == a.merge(b.merge(c)).state()


@pytest.mark.parametrize("seed", range(100))
def test_merge_is_idempotent(seed):
    rng = random.Random(seed)
    a = _random_pncounter("A", rng, rng.randint(0, 10))
    assert a.merge(a).state() == a.state()


@pytest.mark.parametrize("seed", range(50))
def test_convergence_under_random_gossip_with_duplicates(seed):
    rng = random.Random(seed)
    num_replicas = rng.randint(2, 6)
    replicas = [PNCounter(f"r{i}") for i in range(num_replicas)]

    for r in replicas:
        for _ in range(rng.randint(0, 5)):
            if rng.random() < 0.5:
                r.increment(rng.randint(1, 5))
            else:
                r.decrement(rng.randint(1, 5))

    for _ in range(rng.randint(20, 60)):
        i, j = rng.randrange(num_replicas), rng.randrange(num_replicas)
        replicas[i] = replicas[i].merge(replicas[j])

    fully_merged = replicas[0]
    for r in replicas[1:]:
        fully_merged = fully_merged.merge(r)
    final_states = [r.merge(fully_merged).state() for r in replicas]
    assert all(s == final_states[0] for s in final_states)
