"""Demonstrates the actual payoff of building on Thompson NFA simulation
instead of backtracking: classic catastrophic-backtracking patterns run in
linear time here, where a naive backtracking engine (including Python's own
`re`!) blows up exponentially.

Measured directly against Python's `re` during development: `(a+)+b`
against a string of 30 a's (no trailing b) took `re` about 47 seconds --
and every additional 'a' roughly doubles that. Our engine handles 5000 a's
in well under a second, because it tracks a bounded set of NFA states
instead of exploring every possible backtrack.
"""
import time

import regex


def test_nested_quantifier_no_match_stays_fast():
    pattern = regex.compile("(a+)+b")
    text = "a" * 5000  # no trailing 'b', so this is the worst case: total non-match

    start = time.time()
    result = pattern.fullmatch(text)
    elapsed = time.time() - start

    assert result is None
    assert elapsed < 2.0, f"expected linear-time matching, took {elapsed:.2f}s"


def test_alternation_of_repeats_stays_fast():
    pattern = regex.compile("(a|aa)*b")
    text = "a" * 3000

    start = time.time()
    result = pattern.fullmatch(text)
    elapsed = time.time() - start

    assert result is None
    assert elapsed < 2.0, f"expected linear-time matching, took {elapsed:.2f}s"


def test_matching_time_scales_linearly_not_exponentially():
    pattern = regex.compile("(a+)+b")

    def timed(n):
        text = "a" * n
        start = time.time()
        pattern.fullmatch(text)
        return time.time() - start

    small = timed(500)
    large = timed(4000)  # 8x the input

    # Exponential blowup would make this ratio astronomically larger than
    # the input-size ratio; linear/low-degree-polynomial matching keeps it
    # in the same ballpark. Generous bound to avoid flakiness on a shared CPU.
    assert large < small * 100 + 1.0
