import random
import string

import pytest

from spellcheck.trie import Trie
from spellcheck.words import COMMON_WORDS


def _brute_force_autocomplete(words, prefix):
    return sorted(w for w in words if w.startswith(prefix))


@pytest.mark.parametrize("seed", range(150))
def test_autocomplete_matches_brute_force_on_word_list(seed):
    rng = random.Random(seed)
    sample = rng.sample(COMMON_WORDS, 200)
    trie = Trie()
    for w in sample:
        trie.insert(w)

    prefix_source = rng.choice(sample)
    prefix = prefix_source[: rng.randint(0, len(prefix_source))]

    got = sorted(trie.autocomplete(prefix))
    expected = _brute_force_autocomplete(sample, prefix)
    assert got == expected


@pytest.mark.parametrize("seed", range(100))
def test_contains_matches_python_set(seed):
    rng = random.Random(seed + 10_000)
    sample = rng.sample(COMMON_WORDS, 150)
    reference = set(sample)
    trie = Trie()
    for w in sample:
        trie.insert(w)

    for w in sample:
        assert w in trie
    absent_candidates = [w for w in COMMON_WORDS if w not in reference]
    for w in rng.sample(absent_candidates, min(50, len(absent_candidates))):
        assert w not in trie


def test_empty_prefix_returns_everything():
    trie = Trie()
    words = ["cat", "car", "cart", "dog"]
    for w in words:
        trie.insert(w)
    assert sorted(trie.autocomplete("")) == sorted(words)


def test_nonexistent_prefix_returns_empty():
    trie = Trie()
    trie.insert("hello")
    assert trie.autocomplete("xyz") == []


def test_limit_caps_results():
    trie = Trie()
    for w in ["aa", "ab", "ac", "ad", "ae"]:
        trie.insert(w)
    results = trie.autocomplete("a", limit=3)
    assert len(results) == 3
    assert all(r.startswith("a") for r in results)


def test_duplicate_insert_does_not_grow_size():
    trie = Trie()
    trie.insert("word")
    trie.insert("word")
    assert len(trie) == 1


def test_len_tracks_distinct_words():
    trie = Trie()
    for w in ["a", "ab", "abc", "a"]:
        trie.insert(w)
    assert len(trie) == 3


def test_prefix_that_is_not_itself_a_word():
    trie = Trie()
    trie.insert("cats")
    assert "cat" not in trie
    assert trie.autocomplete("cat") == ["cats"]
