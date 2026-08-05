"""A small boolean query language: `word1 word2` requires both (AND),
`-word` excludes documents containing it, `"exact phrase"` requires
those words consecutively in that order, and `clause1 OR clause2` (a
literal, standalone, uppercase `OR`) matches documents satisfying either
side. A document matches the whole query if it matches at least one
OR-separated clause; within a clause, every required term/phrase must be
present and no excluded term may be.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Set

from .index import InvertedIndex
from .tokenizer import tokenize

_QUERY_TOKEN_RE = re.compile(r'"[^"]*"|-?[A-Za-z0-9]+')
_OR_SPLIT_RE = re.compile(r"\bOR\b")


@dataclass
class Clause:
    required_terms: List[str] = field(default_factory=list)
    required_phrases: List[List[str]] = field(default_factory=list)
    excluded_terms: List[str] = field(default_factory=list)


def parse_query(query_string: str) -> List[Clause]:
    """Returns the OR-separated clauses; a document matches the query if
    it matches ANY of them."""
    clauses = []
    for part in _OR_SPLIT_RE.split(query_string):
        clause = Clause()
        for raw in _QUERY_TOKEN_RE.findall(part):
            if raw.startswith('"'):
                phrase = tokenize(raw.strip('"'))
                if phrase:
                    clause.required_phrases.append(phrase)
            elif raw.startswith("-"):
                term = raw[1:].lower()
                if term:
                    clause.excluded_terms.append(term)
            else:
                clause.required_terms.append(raw.lower())
        clauses.append(clause)
    return clauses


def phrase_matches(phrase_tokens: List[str], doc_id: int, index: InvertedIndex) -> bool:
    if not phrase_tokens:
        return False
    for start in index.positions(phrase_tokens[0], doc_id):
        if all(start + offset in index.positions(term, doc_id) for offset, term in enumerate(phrase_tokens)):
            return True
    return False


def clause_matches(clause: Clause, doc_id: int, index: InvertedIndex) -> bool:
    for term in clause.required_terms:
        if doc_id not in index.documents_containing(term):
            return False
    for term in clause.excluded_terms:
        if doc_id in index.documents_containing(term):
            return False
    for phrase in clause.required_phrases:
        if not phrase_matches(phrase, doc_id, index):
            return False
    return True


def matching_documents(clauses: List[Clause], index: InvertedIndex) -> Set[int]:
    matched: Set[int] = set()
    for clause in clauses:
        matched |= {doc_id for doc_id in index.documents if clause_matches(clause, doc_id, index)}
    return matched


def all_positive_terms(clauses: List[Clause]) -> List[str]:
    """Every required term/phrase-word mentioned anywhere in the query,
    in first-seen order, deduplicated -- used to compute a single BM25
    score across all OR-branches uniformly."""
    seen: Set[str] = set()
    terms: List[str] = []
    for clause in clauses:
        for term in clause.required_terms:
            if term not in seen:
                seen.add(term)
                terms.append(term)
        for phrase in clause.required_phrases:
            for term in phrase:
                if term not in seen:
                    seen.add(term)
                    terms.append(term)
    return terms
