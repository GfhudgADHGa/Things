import random

import pytest

from probds.bloom_filter import BloomFilter


@pytest.mark.parametrize("seed", range(120))
def test_no_false_negatives(seed):
    rng = random.Random(seed)
    n = rng.randint(10, 500)
    bf = BloomFilter(expected_items=n, false_positive_rate=0.02)
    items = [f"item-{seed}-{i}-{rng.random()}" for i in range(n)]
    for item in items:
        bf.add(item)
    for item in items:
        assert item in bf


@pytest.mark.parametrize(
    "n,target_fpr",
    [(500, 0.05), (1000, 0.02), (2000, 0.01), (5000, 0.05), (3000, 0.1)],
)
def test_empirical_false_positive_rate_matches_bit_fill_prediction(n, target_fpr):
    """The false-positive rate predicted from the *actual* bit-array fill
    ratio -- (fraction of bits set)^k -- should closely match the
    empirical rate measured over thousands of fresh non-member queries.
    This isn't checking against the a-priori target_fpr (which is just a
    sizing input); it's checking the filter's own math against reality."""
    rng = random.Random(hash((n, target_fpr)) & 0xFFFFFFFF)
    bf = BloomFilter(expected_items=n, false_positive_rate=target_fpr)
    inserted = set()
    for i in range(n):
        item = f"member-{n}-{target_fpr}-{i}"
        bf.add(item)
        inserted.add(item)

    predicted = bf.predicted_false_positive_rate()

    trials = 20000
    false_positives = 0
    for i in range(trials):
        item = f"absent-{n}-{target_fpr}-{i}"
        assert item not in inserted
        if item in bf:
            false_positives += 1
    empirical = false_positives / trials

    tolerance = max(0.01, predicted * 0.5)
    assert abs(empirical - predicted) < tolerance, (predicted, empirical)


def test_more_bits_set_as_items_added():
    bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
    prev = bf.bits_set_fraction()
    for i in range(200):
        bf.add(f"item-{i}")
        current = bf.bits_set_fraction()
        assert current >= prev
        prev = current


def test_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        BloomFilter(expected_items=0, false_positive_rate=0.01)
    with pytest.raises(ValueError):
        BloomFilter(expected_items=100, false_positive_rate=0.0)
    with pytest.raises(ValueError):
        BloomFilter(expected_items=100, false_positive_rate=1.0)


def test_empty_filter_contains_nothing_falsely_with_high_probability():
    bf = BloomFilter(expected_items=100, false_positive_rate=0.01)
    assert bf.bits_set_fraction() == 0.0
    assert "anything" not in bf
