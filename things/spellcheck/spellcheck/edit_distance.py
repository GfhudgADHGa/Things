"""Levenshtein edit distance: the minimum number of single-character
insertions, deletions, and substitutions needed to turn one string into
another. Computed here via the standard O(len(a) * len(b)) dynamic
program, with a from-scratch exponential recursive version kept around
purely as an independent proof oracle for small strings.
"""
from __future__ import annotations


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(
                prev[j] + 1,        # deletion
                curr[j - 1] + 1,    # insertion
                prev[j - 1] + cost,  # substitution (or match)
            )
        prev = curr
    return prev[m]


def levenshtein_recursive_bruteforce(a: str, b: str) -> int:
    """Independently-coded, no shared code with levenshtein() beyond the
    same textbook recurrence -- genuinely exponential, no memoization,
    so only safe on short strings. Used purely as a cross-check oracle
    in tests, never for real use."""

    def rec(i: int, j: int) -> int:
        if i == 0:
            return j
        if j == 0:
            return i
        if a[i - 1] == b[j - 1]:
            return rec(i - 1, j - 1)
        return 1 + min(rec(i - 1, j), rec(i, j - 1), rec(i - 1, j - 1))

    return rec(len(a), len(b))
