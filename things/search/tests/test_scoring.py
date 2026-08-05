import math

import pytest

from search.index import InvertedIndex
from search.scoring import B_DEFAULT, K1_DEFAULT, bm25_score, idf


def test_idf_matches_hand_computed_formula():
    # idf = log((N - df + 0.5) / (df + 0.5)); N=10, df=2
    assert idf(10, 2) == pytest.approx(math.log(8.5 / 2.5))


def test_idf_is_zero_when_term_appears_in_exactly_half_the_corpus():
    # (N - df + 0.5) / (df + 0.5) == 1 exactly when df == N/2
    assert idf(4, 2) == pytest.approx(0.0, abs=1e-12)


def test_idf_is_negative_for_a_term_in_more_than_half_the_corpus():
    # This is a real, well-documented property of the classic Okapi BM25
    # IDF formula (not the "+1 inside the log" variant some engines use
    # specifically to avoid this) -- a term so common it appears in most
    # of the corpus carries *negative* information value, and BM25 as
    # originally formulated lets that pull a document's score down.
    assert idf(10, 8) < 0


def test_document_with_a_supermajority_term_scores_lower_than_without_it():
    # The concrete, end-to-end consequence of the property above: build a
    # corpus where "the" appears in 9 of 10 documents, then check that
    # for a query on "the", the document *without* "the" would trivially
    # not match (BM25 is 0 with tf=0) -- but among documents that DO
    # contain it, adding more occurrences of a supermajority term still
    # provides strictly negative marginal score per the negative IDF.
    idx = InvertedIndex()
    for i in range(9):
        idx.add_document(i, "the " * (i + 1) + "filler")
    idx.add_document(9, "completely different content with no overlap")

    assert idf(idx.doc_count, idx.document_frequency("the")) < 0
    score_one_the = bm25_score(["the"], 0, idx)
    score_five_the = bm25_score(["the"], 4, idx)
    # more occurrences of a negative-idf term => more negative score
    assert score_five_the < score_one_the < 0


def test_score_increases_with_term_frequency_for_a_positive_idf_term():
    idx = InvertedIndex()
    idx.add_document(1, "rare")
    idx.add_document(2, "rare rare rare rare")
    idx.add_document(3, "filler filler filler")
    idx.add_document(4, "filler filler filler")
    idx.add_document(5, "filler filler filler")

    score_1 = bm25_score(["rare"], 1, idx)
    score_2 = bm25_score(["rare"], 2, idx)
    assert score_2 > score_1 > 0


def test_score_is_zero_when_document_lacks_all_query_terms():
    idx = InvertedIndex()
    idx.add_document(1, "fox dog")
    idx.add_document(2, "cat mouse")
    assert bm25_score(["fox"], 2, idx) == 0.0


def test_bm25_matches_hand_computed_value_for_a_simple_case():
    idx = InvertedIndex()
    idx.add_document(1, "fox fox")  # length 2
    idx.add_document(2, "fox dog cat")  # length 3

    avg_len = 2.5
    tf, df, n = 2, 2, 2
    expected_idf = math.log((n - df + 0.5) / (df + 0.5))
    length_norm = (1 - B_DEFAULT) + B_DEFAULT * (2 / avg_len)
    expected = expected_idf * (tf * (K1_DEFAULT + 1)) / (tf + K1_DEFAULT * length_norm)

    assert bm25_score(["fox"], 1, idx) == pytest.approx(expected)


def test_missing_document_raises():
    idx = InvertedIndex()
    idx.add_document(1, "a")
    with pytest.raises(KeyError):
        bm25_score(["a"], 999, idx)


def test_score_of_empty_index_or_empty_query_terms_is_zero():
    idx = InvertedIndex()
    idx.add_document(1, "a b c")
    assert bm25_score([], 1, idx) == 0.0
