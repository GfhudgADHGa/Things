# search

A small text search engine from scratch: an inverted index (postings
with term frequencies and positions), BM25 ranking, and a boolean query
language — `word1 word2` (AND), `-word` (NOT), `"exact phrase"`, and
`clause1 OR clause2`.

```bash
python3 main.py examples/corpus "ray OR chess"
# indexed 4 documents from examples/corpus
#   1.1532  examples/corpus/raytracer.txt
#   0.8932  examples/corpus/chess.txt
```

## The correctness proof: a brute-force oracle

The inverted index exists purely as a performance optimization — the
*definition* of "which documents match" and "what's their score" doesn't
need one at all. So `tests/test_engine_oracle.py` implements that exact
same definition a second time, completely from scratch: no
`InvertedIndex`, no cached postings, no cached document lengths — just
re-tokenizing every document and re-counting term frequencies and
document frequencies directly from raw text, on every single query. Then
it checks `SearchEngine.search()` against that brute-force recomputation
across 15 hand-picked queries and 150 randomized (corpus, query) pairs —
random vocabulary-drawn terms, random negations, and phrases drawn from
real substrings of actual documents (so they have a real chance of
matching something, not just always missing). If the index ever
disagreed with the brute-force version, the index itself would be wrong,
not just some edge case of it — same "don't just hand-pick cases you
already know work" idea as `difftool`'s, `minidb`'s, and `raft`'s
fuzz/property tests, aimed at exactly the layer where an indexing
optimization is most likely to silently diverge from its own spec.

## A real (not a bug) BM25 property: negative IDF

This uses the *classic* Okapi BM25 IDF formula,
`log((N - df + 0.5) / (df + 0.5))` — not the "+1 inside the log" variant
some engines (Lucene included) use specifically to keep it non-negative.
For a term appearing in **more than half** the corpus, this is
mathematically negative: matching that term actually *lowers* a
document's score relative to an otherwise-identical document without
it. `tests/test_scoring.py` verifies this directly (`idf(10, 8) < 0`)
and end-to-end (a document with more occurrences of a supermajority term
scores strictly lower than one with fewer). This isn't a defect being
worked around — it's a real, well-documented property of the original
formula, kept deliberately rather than silently "fixed" to the
always-positive variant, and called out here so it reads as understood
rather than stumbled into.

## Architecture

```
search/
  tokenizer.py    lowercase + split on non-alphanumeric runs; no
                    stemming or stopword removal (see the module
                    docstring for why that's deliberate)
  index.py          InvertedIndex: postings (term -> {doc_id: Posting}),
                      document lengths, the numbers BM25 needs
  scoring.py          bm25_score() + the idf() formula discussed above
  query.py             the boolean/phrase query language: parsing,
                         per-clause matching, phrase position-matching
  engine.py             SearchEngine: index documents, then search()
```

## What's supported

Exact multi-term AND, `-term` exclusion, `"exact phrase"` (via stored
token positions), and `clause1 OR clause2` at the top level. Ranking is
BM25 over the union of every positive term/phrase-word mentioned
anywhere in the query. **Not supported**: stemming, fuzzy/typo-tolerant
matching, nested boolean grouping (parentheses), relevance feedback,
persistence to disk (the index is rebuilt from the corpus directory on
every run of `main.py`).

## Usage

```bash
python3 main.py path/to/text/files "query"       # one query, then exit
python3 main.py path/to/text/files                # interactive REPL
```

Or as a library:

```python
from search import SearchEngine

engine = SearchEngine()
engine.add_document(1, "the quick brown fox jumps over the lazy dog")
engine.add_document(2, "a lazy dog sleeps all day in the sun")
engine.search('"lazy dog"')   # [(1, ...), (2, ...)] -- both contain the phrase
engine.search("fox -hound")   # only documents with "fox" and without "hound"
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

205 tests: the tokenizer, the inverted index's postings/frequencies/
positions, BM25 scoring against hand-computed values (including the
negative-IDF property above), the query language's parsing and matching
rules, and the 165-case brute-force oracle suite described above.

## Possible expansions

- Parenthesized boolean grouping, e.g. `(fox OR dog) AND -cat`
- Stemming (Porter or similar) so "jump"/"jumps"/"jumping" all match
- Persistence: write the index to disk instead of rebuilding on startup
  (the same durability problem `kvstore` solves for a key-value index,
  applied here)
