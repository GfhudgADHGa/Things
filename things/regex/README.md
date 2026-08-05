# regex

A regex engine built from scratch on Thompson's NFA construction — the
same technique behind `grep`, RE2, and Rust's `regex` crate. The payoff
isn't just "it works," it's that it's **immune to catastrophic
backtracking**: patterns that make naive regex engines (Python's own `re`
included) hang for seconds or minutes run here in milliseconds, because
matching runs every possible NFA state in parallel instead of trying
alternatives one at a time and backtracking on failure.

```python
import regex

p = regex.compile(r"\d{3}-\d{4}")
p.fullmatch("555-1234")     # Match(start=0, end=8, text='555-1234')
p.findall("call 555-1234 or 555-6789")  # ['555-1234', '555-6789']
```

## Syntax supported

- Literals, `.` (any char but newline)
- `*`, `+`, `?`, and bounded `{m}`, `{m,}`, `{m,n}` repetition
- `|` alternation, `(...)` grouping
- Character classes: `[abc]`, `[^abc]`, `[a-z0-9]` (ranges), with escapes
- Shorthand classes: `\d \D \w \W \s \S` (negated forms not supported
  *inside* `[...]` — see `parser.py`'s docstring for why)
- Anchors `^` and `$`

No capture groups (parenthesized groups only affect precedence/repetition
scope, not extraction) — see Possible Expansions.

## Why this is immune to catastrophic backtracking

A backtracking engine matching `(a+)+b` against a string of just 30 `a`s
(no trailing `b`, so it's *guaranteed* to fail) has to try every way of
partitioning those a's between the inner and outer `+`, because each
failure triggers backtracking into the next partition — exponentially many
of them. Measured directly against Python's own `re` module during
development:

| pattern | text | Python `re` | this engine |
|---|---|---|---|
| `(a+)+b` | 25 a's | 1.5s | — |
| `(a+)+b` | 30 a's | **47.4s** | — |
| `(a+)+b` | 5000 a's | *(would never finish)* | **0.013s** |

Thompson NFA simulation sidesteps this entirely: instead of trying
partitions one at a time, it tracks the *set* of NFA states reachable
after each character — at most one state per NFA node, so the state set
size is bounded by the pattern's size, not the input's. Matching is
`O(pattern_size × text_length)`, full stop, no worst case blowup. See
`tests/test_redos.py`.

## A real tradeoff, not a bug: leftmost-*longest*, not leftmost-first

Running every alternative in parallel has a semantic consequence: given
`a|ab` against `"ab"`, this engine returns the *longest* overall match
(`"ab"`), while Python's `re` (and Perl, PCRE, JavaScript...) returns
whichever alternative was written first and happened to succeed (`"a"`),
because backtracking engines commit to the first alternative that lets the
rest of the match succeed. Neither is "more correct" — POSIX regex
explicitly mandates leftmost-longest; Perl-style engines chose
leftmost-first because it composes better with backreferences and lets
you order alternatives by preference. This engine has no backreferences
(they're fundamentally incompatible with NFA simulation — they make
matching NP-hard), so leftmost-longest was the natural, ReDoS-immune
choice. See `tests/test_posix_semantics.py` for a runnable demonstration.

## Architecture

```
regex/
  ast_nodes.py    AST: Literal, AnyChar, CharClass, Concat, Alternation,
                    Repeat, Group, StartAnchor, EndAnchor
  parser.py         recursive-descent regex syntax -> AST
  nfa.py             Thompson's construction: AST -> NFA (fragment-based,
                       with dangling out-pointers patched as fragments compose)
  matcher.py         NFA simulation: epsilon-closure + parallel state
                       stepping, no backtracking
  pattern.py         public API (compile/match/fullmatch/search/findall),
                       shaped like Python's re for easy comparison
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

252 tests: parser AST shape and syntax-error cases, direct behavioral
tests for every supported construct, an **oracle suite** that
cross-checks dozens of (pattern, text) pairs against Python's own `re`
module and requires identical match/no-match and span results (a much
stronger signal than hand-picked expected values), the ReDoS-immunity
timing tests, and the leftmost-longest semantics demonstration.

## Usage

```bash
python3 main.py '\d+' somefile.txt   # grep-style: print matching lines
echo "no match here" | python3 main.py 'zebra'  # reads stdin if no file given
```

## Possible expansions

- Capture groups (would need a Pike's-VM-style simulation with save slots
  per thread, since plain Thompson simulation only tracks reachability,
  not *how* a state was reached)
- Non-greedy quantifiers (`*?`, `+?`)
- A real memory optimization: right now epsilon-closures are recomputed
  from scratch at every position; a compiled DFA (via subset construction)
  would trade a one-time compilation cost for faster repeated matching
