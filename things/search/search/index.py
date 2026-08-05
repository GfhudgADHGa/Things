"""The inverted index: for each term, which documents contain it, how
many times, and at which token positions (positions are what make exact
phrase queries possible without re-scanning document text)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .tokenizer import tokenize


@dataclass
class Posting:
    doc_id: int
    term_freq: int
    positions: List[int] = field(default_factory=list)


@dataclass
class DocumentInfo:
    text: str
    length: int  # token count


class InvertedIndex:
    def __init__(self):
        self.documents: Dict[int, DocumentInfo] = {}
        self.postings: Dict[str, Dict[int, Posting]] = {}
        self.total_length = 0

    @property
    def doc_count(self) -> int:
        return len(self.documents)

    def average_document_length(self) -> float:
        return self.total_length / self.doc_count if self.doc_count else 0.0

    def add_document(self, doc_id: int, text: str) -> None:
        if doc_id in self.documents:
            raise ValueError(f"document {doc_id} already indexed")
        tokens = tokenize(text)
        self.documents[doc_id] = DocumentInfo(text=text, length=len(tokens))
        self.total_length += len(tokens)

        positions_by_term: Dict[str, List[int]] = {}
        for position, term in enumerate(tokens):
            positions_by_term.setdefault(term, []).append(position)

        for term, positions in positions_by_term.items():
            self.postings.setdefault(term, {})[doc_id] = Posting(doc_id, len(positions), positions)

    def document_frequency(self, term: str) -> int:
        return len(self.postings.get(term, {}))

    def term_frequency(self, term: str, doc_id: int) -> int:
        posting = self.postings.get(term, {}).get(doc_id)
        return posting.term_freq if posting else 0

    def positions(self, term: str, doc_id: int) -> List[int]:
        posting = self.postings.get(term, {}).get(doc_id)
        return posting.positions if posting else []

    def documents_containing(self, term: str) -> set:
        return set(self.postings.get(term, {}).keys())
