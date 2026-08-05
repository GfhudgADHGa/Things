"""BM25 ranking (Robertson/Sparck Jones's classic Okapi BM25 formula, not
the "+1 inside the log" variant some engines use -- see the README for
why that choice was deliberate). k1 controls how quickly additional term
occurrences saturate (diminishing returns on repeated terms); b controls
how much document length is normalized against the corpus average (0 =
no length normalization, 1 = full normalization).
"""
from __future__ import annotations

import math

from .index import InvertedIndex

K1_DEFAULT = 1.5
B_DEFAULT = 0.75


def idf(doc_count: int, doc_freq: int) -> float:
    """The classic Okapi BM25 IDF term. Deliberately NOT clamped to be
    non-negative: for a term that appears in more than half the corpus
    (doc_freq > doc_count/2), this is mathematically negative -- meaning
    a document containing that term scores *lower* than an otherwise
    identical document without it. That's a real, well-documented
    property of this exact formula, not a bug (see test_scoring.py and
    the README)."""
    return math.log((doc_count - doc_freq + 0.5) / (doc_freq + 0.5))


def bm25_score(
    query_terms,
    doc_id: int,
    index: InvertedIndex,
    k1: float = K1_DEFAULT,
    b: float = B_DEFAULT,
) -> float:
    doc = index.documents.get(doc_id)
    if doc is None:
        raise KeyError(f"no such document: {doc_id}")
    avg_length = index.average_document_length()
    doc_length = doc.length

    score = 0.0
    for term in query_terms:
        tf = index.term_frequency(term, doc_id)
        if tf == 0:
            continue
        df = index.document_frequency(term)
        length_norm = (1 - b) + b * (doc_length / avg_length if avg_length else 0.0)
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * length_norm
        score += idf(index.doc_count, df) * (numerator / denominator)
    return score
