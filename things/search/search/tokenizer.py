"""Deliberately the simplest possible tokenizer: lowercase, split on runs
of non-alphanumeric characters, drop empties. No stemming, no stopword
removal -- both are real quality improvements a production search engine
would want, but both are also judgment calls with no single "correct"
answer, which would make the brute-force oracle comparison (the whole
point of this thing) a comparison against another arbitrary judgment
call instead of against something unambiguous.
"""
from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list:
    return _TOKEN_RE.findall(text.lower())
