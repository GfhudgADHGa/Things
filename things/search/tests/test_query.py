from search.index import InvertedIndex
from search.query import (
    all_positive_terms, clause_matches, matching_documents, parse_query, phrase_matches,
)


def test_parse_plain_terms_are_all_required():
    clauses = parse_query("fox dog")
    assert len(clauses) == 1
    assert clauses[0].required_terms == ["fox", "dog"]


def test_parse_negated_term():
    clauses = parse_query("fox -dog")
    assert clauses[0].required_terms == ["fox"]
    assert clauses[0].excluded_terms == ["dog"]


def test_parse_phrase():
    clauses = parse_query('"lazy dog" fox')
    assert clauses[0].required_phrases == [["lazy", "dog"]]
    assert clauses[0].required_terms == ["fox"]


def test_parse_or_splits_into_multiple_clauses():
    clauses = parse_query("fox OR dog")
    assert len(clauses) == 2
    assert clauses[0].required_terms == ["fox"]
    assert clauses[1].required_terms == ["dog"]


def test_parse_or_is_case_sensitive_lowercase_or_is_just_a_term():
    clauses = parse_query("fox or dog")
    assert len(clauses) == 1
    assert clauses[0].required_terms == ["fox", "or", "dog"]


def test_parse_query_is_case_insensitive_for_terms():
    clauses = parse_query("FOX Dog")
    assert clauses[0].required_terms == ["fox", "dog"]


def test_all_positive_terms_deduplicates_and_preserves_order():
    clauses = parse_query('fox "fox jumps" OR dog fox')
    assert all_positive_terms(clauses) == ["fox", "jumps", "dog"]


def make_index():
    idx = InvertedIndex()
    idx.add_document(1, "the quick brown fox jumps over the lazy dog")
    idx.add_document(2, "a lazy dog sleeps all day")
    idx.add_document(3, "the fox and the hound")
    return idx


def test_clause_matches_requires_all_terms():
    idx = make_index()
    clauses = parse_query("fox dog")
    assert clause_matches(clauses[0], 1, idx) is True
    assert clause_matches(clauses[0], 2, idx) is False  # no fox
    assert clause_matches(clauses[0], 3, idx) is False  # no dog


def test_clause_matches_excludes_negated_term():
    idx = make_index()
    clauses = parse_query("fox -hound")
    assert clause_matches(clauses[0], 1, idx) is True
    assert clause_matches(clauses[0], 3, idx) is False  # has "hound"


def test_phrase_matches_requires_consecutive_positions():
    idx = make_index()
    assert phrase_matches(["lazy", "dog"], 1, idx) is True
    assert phrase_matches(["dog", "lazy"], 1, idx) is False  # wrong order
    assert phrase_matches(["lazy", "day"], 2, idx) is False  # not adjacent


def test_phrase_matches_single_word_phrase():
    idx = make_index()
    assert phrase_matches(["fox"], 1, idx) is True
    assert phrase_matches(["nonexistent"], 1, idx) is False


def test_phrase_matches_empty_phrase_is_false():
    idx = make_index()
    assert phrase_matches([], 1, idx) is False


def test_matching_documents_unions_across_or_clauses():
    idx = make_index()
    clauses = parse_query("sleeps OR hound")
    assert matching_documents(clauses, idx) == {2, 3}


def test_matching_documents_with_no_matches_is_empty():
    idx = make_index()
    clauses = parse_query("nonexistentword")
    assert matching_documents(clauses, idx) == set()


def test_repeated_phrase_occurrence_still_matches_once():
    idx = InvertedIndex()
    idx.add_document(1, "fox jumps fox jumps again")
    clauses = parse_query('"fox jumps"')
    assert matching_documents(clauses, idx) == {1}
