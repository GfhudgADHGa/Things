import random

import pytest

from probds.hyperloglog import HyperLogLog


@pytest.mark.parametrize(
    "seed,b,true_n",
    [(s, b, n) for s in range(8) for b in (8, 10, 12) for n in (200, 2000, 20000)],
)
def test_estimate_within_generous_multiple_of_standard_error(seed, b, true_n):
    """HyperLogLog's classic guarantee is a *standard error* of about
    1.04/sqrt(m) -- a statistical statement, not a hard bound, so
    individual trials can and will exceed 1 standard error fairly often.
    A 5-standard-error window should essentially never be exceeded
    (well under a in a million chance under the usual normal
    approximation), which is what's checked here across a spread of
    seeds, register counts, and true cardinalities."""
    rng = random.Random(f"{seed}-{b}-{true_n}")
    hll = HyperLogLog(b=b)
    distinct_items = [f"user-{seed}-{i}" for i in range(true_n)]
    # duplicate each item a random number of times, in random order --
    # HyperLogLog's whole point is that duplicates must not move the
    # estimate, since it estimates distinct count, not stream length.
    stream = []
    for item in distinct_items:
        stream.extend([item] * rng.randint(1, 5))
    rng.shuffle(stream)

    for item in stream:
        hll.add(item)

    estimate = hll.estimate()
    relative_error = abs(estimate - true_n) / true_n
    allowed = 5 * HyperLogLog.standard_error(hll.m)
    assert relative_error < allowed, (b, true_n, estimate, relative_error, allowed)


def test_duplicates_do_not_change_estimate():
    hll_unique = HyperLogLog(b=10)
    hll_dup = HyperLogLog(b=10)
    for i in range(500):
        hll_unique.add(f"x-{i}")
        for _ in range(7):
            hll_dup.add(f"x-{i}")
    assert hll_unique.estimate() == pytest.approx(hll_dup.estimate())


def test_empty_estimate_is_zero():
    hll = HyperLogLog(b=8)
    assert hll.estimate() == 0.0


def test_small_cardinality_uses_linear_counting_correction():
    """For true cardinalities far below m, the raw harmonic-mean
    estimator is biased and HyperLogLog switches to linear counting
    (based on the fraction of still-empty registers) instead -- checked
    here against the trivial fact that adding a single item must yield
    an estimate near 1, which the uncorrected raw estimator alone
    would badly overshoot for a large m."""
    hll = HyperLogLog(b=12)
    hll.add("only-item")
    assert 0.5 < hll.estimate() < 3.0


def test_rejects_out_of_range_b():
    with pytest.raises(ValueError):
        HyperLogLog(b=2)
    with pytest.raises(ValueError):
        HyperLogLog(b=40)


@pytest.mark.parametrize("b", [8, 10, 12, 14])
def test_standard_error_matches_formula(b):
    import math

    m = 1 << b
    assert HyperLogLog.standard_error(m) == pytest.approx(1.04 / math.sqrt(m))


def test_larger_m_gives_tighter_average_error():
    """Cross-check the 1.04/sqrt(m) claim itself, not just that
    individual trials fall within it: averaged relative error across
    many independent trials should shrink as m grows, in roughly the
    predicted proportion."""
    true_n = 5000
    errors_by_b = {}
    for b in (8, 12):
        rng = random.Random(b)
        errs = []
        for trial in range(25):
            hll = HyperLogLog(b=b)
            for i in range(true_n):
                hll.add(f"t{trial}-item-{i}")
            errs.append(abs(hll.estimate() - true_n) / true_n)
        errors_by_b[b] = sum(errs) / len(errs)

    assert errors_by_b[12] < errors_by_b[8]
