import random
import string

import pytest

from spellcheck.edit_distance import levenshtein, levenshtein_recursive_bruteforce


def _random_string(rng, alphabet, max_len):
    length = rng.randint(0, max_len)
    return "".join(rng.choice(alphabet) for _ in range(length))


@pytest.mark.parametrize("seed", range(300))
def test_matches_recursive_brute_force(seed):
    rng = random.Random(seed)
    alphabet = "ab" if seed % 3 == 0 else string.ascii_lowercase[:6]
    a = _random_string(rng, alphabet, 6)
    b = _random_string(rng, alphabet, 6)
    assert levenshtein(a, b) == levenshtein_recursive_bruteforce(a, b)


def test_identical_strings_have_distance_zero():
    assert levenshtein("hello", "hello") == 0
    assert levenshtein("", "") == 0


def test_empty_string_distance_is_length_of_other():
    assert levenshtein("", "abc") == 3
    assert levenshtein("abcde", "") == 5


def test_single_substitution():
    assert levenshtein("cat", "cot") == 1


def test_single_insertion_and_deletion():
    assert levenshtein("cat", "cats") == 1
    assert levenshtein("cats", "cat") == 1


def test_known_classic_example():
    # kitten -> sitten (sub) -> sittin (sub) -> sitting (insert) = 3
    assert levenshtein("kitten", "sitting") == 3


@pytest.mark.parametrize("seed", range(200))
def test_symmetric(seed):
    rng = random.Random(seed + 10_000)
    a = _random_string(rng, string.ascii_lowercase[:8], 8)
    b = _random_string(rng, string.ascii_lowercase[:8], 8)
    assert levenshtein(a, b) == levenshtein(b, a)


@pytest.mark.parametrize("seed", range(200))
def test_identity_of_indiscernibles(seed):
    rng = random.Random(seed + 20_000)
    a = _random_string(rng, string.ascii_lowercase, 10)
    assert levenshtein(a, a) == 0


@pytest.mark.parametrize("seed", range(300))
def test_triangle_inequality(seed):
    """d(a, c) <= d(a, b) + d(b, c) -- a real property of the edit-distance
    *metric*, not an implementation detail, checked numerically across
    hundreds of random string triples. This is also the exact property
    that makes BK-tree pruning valid (see bk_tree.py)."""
    rng = random.Random(seed + 30_000)
    alphabet = string.ascii_lowercase[:5]
    a = _random_string(rng, alphabet, 7)
    b = _random_string(rng, alphabet, 7)
    c = _random_string(rng, alphabet, 7)
    assert levenshtein(a, c) <= levenshtein(a, b) + levenshtein(b, c)
