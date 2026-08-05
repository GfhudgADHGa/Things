"""Our engine deliberately does leftmost-*longest* matching (POSIX style),
not leftmost-first-alternative backtracking (Perl/Python `re` style). This
is a direct consequence of running all NFA states in parallel: we track
every alternative simultaneously and report the longest one that reaches
an accept state, rather than trying alternatives in written order and
stopping at the first success.

This is a deliberate, documented tradeoff -- not a bug -- and it's exactly
what buys the ReDoS immunity in test_redos.py: a backtracking engine's
"try alternatives in order, backtrack on failure" strategy is what causes
exponential blowup on nested/ambiguous quantifiers in the first place.

Verified directly against Python's `re` during development:
    re.search('a|ab', 'ab')      -> matches 'a'  (first alternative wins)
    regex.search('a|ab', 'ab')   -> matches 'ab' (longest overall wins)
"""
import re as stdlib_re

import regex


def test_alternation_prefers_first_alternative_in_stdlib_re():
    m = stdlib_re.compile("a|ab").search("ab")
    assert m.group() == "a"


def test_our_engine_prefers_longest_overall_match():
    m = regex.compile("a|ab").search("ab")
    assert m.text == "ab"


def test_difference_also_shows_up_in_fullmatch_when_it_matters():
    # fullmatch requires consuming the whole string, so here both engines
    # actually agree -- backtracking retries 'a' failing to consume "ab"
    # fully, then falls back to trying 'ab', and succeeds. The divergence
    # in the tests above is specifically about search()/match() stopping
    # early on the first viable alternative.
    assert stdlib_re.compile("a|ab").fullmatch("ab").group() == "ab"
    assert regex.compile("a|ab").fullmatch("ab").text == "ab"
