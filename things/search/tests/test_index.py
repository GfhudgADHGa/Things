import pytest

from search.index import InvertedIndex


def test_add_document_and_term_frequency():
    idx = InvertedIndex()
    idx.add_document(1, "the fox jumps over the fox")
    assert idx.term_frequency("fox", 1) == 2
    assert idx.term_frequency("the", 1) == 2
    assert idx.term_frequency("dog", 1) == 0


def test_document_frequency_counts_distinct_documents():
    idx = InvertedIndex()
    idx.add_document(1, "fox fox fox")
    idx.add_document(2, "fox dog")
    idx.add_document(3, "cat dog")
    assert idx.document_frequency("fox") == 2
    assert idx.document_frequency("dog") == 2
    assert idx.document_frequency("cat") == 1
    assert idx.document_frequency("nonexistent") == 0


def test_positions_are_recorded_correctly():
    idx = InvertedIndex()
    idx.add_document(1, "a b a c a")
    assert idx.positions("a", 1) == [0, 2, 4]
    assert idx.positions("b", 1) == [1]
    assert idx.positions("missing", 1) == []


def test_document_length_and_average():
    idx = InvertedIndex()
    idx.add_document(1, "one two three")
    idx.add_document(2, "four five")
    assert idx.documents[1].length == 3
    assert idx.documents[2].length == 2
    assert idx.average_document_length() == pytest.approx(2.5)


def test_average_length_of_empty_index_is_zero():
    idx = InvertedIndex()
    assert idx.average_document_length() == 0.0


def test_duplicate_doc_id_raises():
    idx = InvertedIndex()
    idx.add_document(1, "a")
    with pytest.raises(ValueError):
        idx.add_document(1, "b")


def test_documents_containing():
    idx = InvertedIndex()
    idx.add_document(1, "fox dog")
    idx.add_document(2, "cat dog")
    assert idx.documents_containing("dog") == {1, 2}
    assert idx.documents_containing("fox") == {1}
    assert idx.documents_containing("nope") == set()


def test_empty_document_is_valid():
    idx = InvertedIndex()
    idx.add_document(1, "")
    assert idx.documents[1].length == 0
    assert idx.doc_count == 1
