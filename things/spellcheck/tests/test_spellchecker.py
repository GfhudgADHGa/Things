import random

import pytest

from spellcheck.spellchecker import SpellChecker
from spellcheck.words import COMMON_WORDS


@pytest.fixture(scope="module")
def checker():
    return SpellChecker(COMMON_WORDS)


def test_dictionary_words_are_correct(checker):
    for w in random.Random(0).sample(COMMON_WORDS, 100):
        assert checker.is_correct(w)


def test_nonwords_are_incorrect(checker):
    for w in ["xzqvth", "blorpster", "asdfghjk"]:
        assert not checker.is_correct(w)


def test_suggest_ranks_closest_first():
    # a controlled dictionary where "receive" is *uniquely* closest to
    # "recieve" -- the full COMMON_WORDS list also contains "believe",
    # which turns out to tie "receive" at distance 2 (b/r and l/c are
    # both single substitutions), so that word list can't be used to
    # test uniqueness of the top suggestion, only tie-aware ordering.
    checker = SpellChecker(["receive", "receipt", "deceive", "perceive", "achieve"])
    suggestions = checker.suggest("recieve", max_dist=2)
    assert suggestions[0][0] == "receive"
    distances = [d for _, d in suggestions]
    assert distances == sorted(distances)


def test_suggest_breaks_distance_ties_alphabetically(checker):
    # "recieve" is equidistant (2) from both "believe" and "receive" in
    # the full dictionary; the ranking must still be deterministic.
    suggestions = checker.suggest("recieve", max_dist=2)
    tied = [w for w, d in suggestions if d == suggestions[0][1]]
    assert tied == sorted(tied)


def test_suggest_returns_only_words_within_max_dist(checker):
    for word, dist in checker.suggest("teh", max_dist=2):
        assert dist <= 2
        assert checker.is_correct(word)


def test_autocomplete_only_returns_dictionary_words(checker):
    for word in checker.autocomplete("th", limit=20):
        assert checker.is_correct(word)
        assert word.startswith("th")


def test_correct_word_suggests_itself_first():
    checker = SpellChecker(["the", "there", "then", "them"])
    suggestions = checker.suggest("the", max_dist=2)
    assert suggestions[0] == ("the", 0)


@pytest.mark.parametrize("seed", range(80))
def test_suggest_matches_brute_force_scan(seed):
    from spellcheck.edit_distance import levenshtein

    rng = random.Random(seed)
    sample = rng.sample(COMMON_WORDS, 200)
    checker = SpellChecker(sample)
    target = rng.choice(COMMON_WORDS)
    max_dist = rng.choice([1, 2])

    got = {w for w, _ in checker.suggest(target, max_dist=max_dist)}
    expected = {w for w in sample if levenshtein(target, w) <= max_dist}
    assert got == expected
