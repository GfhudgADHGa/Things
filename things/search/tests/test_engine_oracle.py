"""The correctness proof for this thing: a from-scratch brute-force
recomputation of matching and scoring -- no InvertedIndex, no caching,
just re-tokenizing every document and re-counting from raw text on every
single query -- cross-checked against SearchEngine.search() across many
randomized synthetic corpora and queries (the same "don't just hand-pick
cases you already know work" idea as difftool's, minidb's, and raft's
fuzz/property tests). The indexed engine is a *performance* optimization
over this exact same definition of matching and BM25 scoring; if it ever
disagreed with the brute-force recomputation, the index itself -- not
just some edge case -- would be wrong.
"""
import math
import random
import re

import pytest

from search.engine import SearchEngine
from search.scoring import B_DEFAULT, K1_DEFAULT
from search.tokenizer import tokenize

_QUERY_TOKEN_RE = re.compile(r'"[^"]*"|-?[A-Za-z0-9]+')
_OR_SPLIT_RE = re.compile(r"\bOR\b")


def _brute_phrase_match(tokens, phrase):
    n, m = len(tokens), len(phrase)
    if m == 0:
        return False
    return any(tokens[start:start + m] == phrase for start in range(n - m + 1))


def brute_force_search(docs: dict, query_string: str, top_k: int, k1=K1_DEFAULT, b=B_DEFAULT):
    """Re-derives matching documents and BM25 scores entirely from raw
    text, independent of search/index.py, search/query.py, and
    search/scoring.py's implementations."""
    clauses = []
    for part in _OR_SPLIT_RE.split(query_string):
        required_terms, required_phrases, excluded_terms = [], [], []
        for raw in _QUERY_TOKEN_RE.findall(part):
            if raw.startswith('"'):
                phrase = tokenize(raw.strip('"'))
                if phrase:
                    required_phrases.append(phrase)
            elif raw.startswith("-"):
                term = raw[1:].lower()
                if term:
                    excluded_terms.append(term)
            else:
                required_terms.append(raw.lower())
        clauses.append((required_terms, required_phrases, excluded_terms))

    doc_tokens = {doc_id: tokenize(text) for doc_id, text in docs.items()}

    def matches_clause(doc_id, clause):
        required_terms, required_phrases, excluded_terms = clause
        token_set = set(doc_tokens[doc_id])
        if any(t not in token_set for t in required_terms):
            return False
        if any(t in token_set for t in excluded_terms):
            return False
        if any(not _brute_phrase_match(doc_tokens[doc_id], p) for p in required_phrases):
            return False
        return True

    matched = {doc_id for doc_id in docs if any(matches_clause(doc_id, c) for c in clauses)}

    positive_terms, seen = [], set()
    for required_terms, required_phrases, _ in clauses:
        for term in required_terms:
            if term not in seen:
                seen.add(term)
                positive_terms.append(term)
        for phrase in required_phrases:
            for term in phrase:
                if term not in seen:
                    seen.add(term)
                    positive_terms.append(term)

    n = len(docs)
    avg_len = sum(len(toks) for toks in doc_tokens.values()) / n if n else 0.0

    def score(doc_id):
        tokens = doc_tokens[doc_id]
        length = len(tokens)
        total = 0.0
        for term in positive_terms:
            tf = tokens.count(term)
            if tf == 0:
                continue
            df = sum(1 for toks in doc_tokens.values() if term in toks)
            idf_val = math.log((n - df + 0.5) / (df + 0.5))
            length_norm = (1 - b) + b * (length / avg_len if avg_len else 0.0)
            total += idf_val * (tf * (k1 + 1)) / (tf + k1 * length_norm)
        return total

    scored = [(doc_id, score(doc_id)) for doc_id in matched]
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return scored[:top_k]


def build_engine(docs: dict) -> SearchEngine:
    engine = SearchEngine()
    for doc_id, text in docs.items():
        engine.add_document(doc_id, text)
    return engine


def assert_matches_oracle(docs, query, top_k=50):
    engine = build_engine(docs)
    actual = engine.search(query, top_k=top_k)
    expected = brute_force_search(docs, query, top_k=top_k)
    assert len(actual) == len(expected), f"query={query!r}: {actual} vs {expected}"
    for (doc_a, score_a), (doc_b, score_b) in zip(actual, expected):
        assert doc_a == doc_b, f"query={query!r}: doc order mismatch {actual} vs {expected}"
        assert score_a == pytest.approx(score_b, abs=1e-9), f"query={query!r}: score mismatch on doc {doc_a}"


SAMPLE_DOCS = {
    1: "the quick brown fox jumps over the lazy dog",
    2: "a lazy dog sleeps all day in the warm sun",
    3: "the fox and the hound became unlikely friends",
    4: "quick quick quick repetition test of the word quick",
    5: "completely unrelated content about astronomy and distant stars",
    6: "another unrelated document about cooking recipes and spices",
    7: "the dog barked at the fox near the lazy river",
    8: "friends gathered to watch the sun set over the river",
}


@pytest.mark.parametrize("query", [
    "fox",
    "dog",
    "the",
    "fox dog",
    "quick fox",
    "fox -hound",
    "dog -lazy",
    '"lazy dog"',
    '"the fox"',
    "sleeps OR hound",
    "fox OR astronomy OR cooking",
    "river friends",
    "nonexistentword",
    'fox "lazy dog"',
    "fox dog -hound",
])
def test_matches_brute_force_oracle_on_hand_picked_queries(query):
    assert_matches_oracle(SAMPLE_DOCS, query)


def _random_corpus(rng: random.Random, vocab, num_docs, max_len):
    return {
        doc_id: " ".join(rng.choice(vocab) for _ in range(rng.randint(0, max_len)))
        for doc_id in range(num_docs)
    }


def _random_query(rng: random.Random, vocab, docs):
    parts = []
    num_or_clauses = rng.randint(1, 2)
    for _ in range(num_or_clauses):
        tokens = []
        for _ in range(rng.randint(1, 3)):
            kind = rng.random()
            if kind < 0.2:
                tokens.append("-" + rng.choice(vocab))
            elif kind < 0.4:
                # a real phrase drawn from an actual document, so it has
                # a decent chance of really matching something
                doc_text = rng.choice(list(docs.values()))
                words = doc_text.split()
                if len(words) >= 2:
                    start = rng.randrange(len(words) - 1)
                    tokens.append(f'"{words[start]} {words[start + 1]}"')
                else:
                    tokens.append(rng.choice(vocab))
            else:
                tokens.append(rng.choice(vocab))
        parts.append(" ".join(tokens))
    return " OR ".join(parts)


@pytest.mark.parametrize("seed", range(150))
def test_fuzz_random_corpora_and_queries_match_brute_force_oracle(seed):
    rng = random.Random(seed)
    vocab = ["fox", "dog", "cat", "the", "a", "quick", "lazy", "jumps", "river", "sun", "friends"]
    docs = _random_corpus(rng, vocab, num_docs=rng.randint(1, 12), max_len=rng.randint(0, 10))
    query = _random_query(rng, vocab, docs)
    assert_matches_oracle(docs, query)


def test_top_k_truncates_but_keeps_correct_order():
    engine = build_engine(SAMPLE_DOCS)
    full = engine.search("the", top_k=100)
    truncated = engine.search("the", top_k=3)
    assert truncated == full[:3]


def test_empty_corpus_returns_no_results():
    engine = SearchEngine()
    assert engine.search("anything") == []
