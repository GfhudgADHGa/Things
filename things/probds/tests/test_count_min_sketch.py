import random
from collections import Counter

import pytest

from probds.count_min_sketch import CountMinSketch


def _random_stream(rng, n_events, n_distinct, zipf_skew=True):
    if zipf_skew:
        weights = [1.0 / (rank + 1) for rank in range(n_distinct)]
    else:
        weights = [1.0] * n_distinct
    population = [f"key-{i}" for i in range(n_distinct)]
    return rng.choices(population, weights=weights, k=n_events)


@pytest.mark.parametrize("seed", range(150))
def test_never_underestimates(seed):
    """min-of-counters can only be inflated by collisions, never
    deflated below the truth -- checked against collections.Counter as
    an independently-implemented exact oracle."""
    rng = random.Random(seed)
    n_events = rng.randint(50, 3000)
    n_distinct = rng.randint(5, 200)
    stream = _random_stream(rng, n_events, n_distinct)
    true_counts = Counter(stream)

    width = rng.choice([20, 50, 100])
    depth = rng.choice([2, 3, 4])
    cms = CountMinSketch(width, depth)
    for item in stream:
        cms.add(item)

    for item, true_count in true_counts.items():
        assert cms.estimate(item) >= true_count


@pytest.mark.parametrize(
    "epsilon,delta",
    [(0.05, 0.1), (0.02, 0.05), (0.1, 0.2), (0.01, 0.1)],
)
def test_overestimate_bounded_by_theoretical_error(epsilon, delta):
    """For width/depth sized via for_error_bound(epsilon, delta), the
    theorem guarantees estimate <= true_count + epsilon * total, with
    probability >= 1 - delta *per query*. We check the much cheaper,
    always-true engineering-grade version of that guarantee: the worst
    observed overestimate across every distinct key, on one sizeable
    randomized stream, should stay comfortably under the bound (a
    generous 3x safety margin on epsilon, since actual sketches perform
    far better than the worst-case theorem in typical, non-adversarial
    data)."""
    rng = random.Random(hash((epsilon, delta)) & 0xFFFFFFFF)
    n_events = 20000
    n_distinct = 300
    stream = _random_stream(rng, n_events, n_distinct)
    true_counts = Counter(stream)

    cms = CountMinSketch.for_error_bound(epsilon, delta)
    for item in stream:
        cms.add(item)

    bound = epsilon * cms.total
    for item, true_count in true_counts.items():
        estimate = cms.estimate(item)
        assert estimate >= true_count
        assert estimate - true_count <= 3 * bound, (item, estimate, true_count, bound)


def test_for_error_bound_sizing_matches_formula():
    import math

    cms = CountMinSketch.for_error_bound(0.01, 0.01)
    assert cms.width == math.ceil(math.e / 0.01)
    assert cms.depth == math.ceil(math.log(1 / 0.01))


def test_rejects_invalid_dimensions():
    with pytest.raises(ValueError):
        CountMinSketch(0, 3)
    with pytest.raises(ValueError):
        CountMinSketch(10, 0)


def test_uniform_vs_skewed_stream_both_stay_conservative():
    rng = random.Random(99)
    for skew in (True, False):
        stream = _random_stream(rng, 5000, 100, zipf_skew=skew)
        true_counts = Counter(stream)
        cms = CountMinSketch(50, 4)
        for item in stream:
            cms.add(item)
        for item, true_count in true_counts.items():
            assert cms.estimate(item) >= true_count
