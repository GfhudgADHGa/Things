"""Cross-checks our engine against Python's stdlib `re` module, which we
trust to be correct. This is a much stronger correctness signal than
hand-picking expected values for every case.

Patterns are chosen to avoid a known, deliberate semantic difference: our
engine does leftmost-*longest* matching (like POSIX), while Python's `re`
does leftmost-first-alternative backtracking (like Perl). These agree for
every pattern below; the difference itself is demonstrated and explained
in test_posix_semantics.py.
"""
import re as stdlib_re

import pytest

import regex

CASES = [
    ("abc", ["abc", "ab", "abcd", "xabc", ""]),
    ("a.c", ["abc", "axc", "ac", "a\nc", "aXXc"]),
    ("ab*c", ["ac", "abc", "abbbbc", "abd", ""]),
    ("ab+c", ["ac", "abc", "abbc", ""]),
    ("ab?c", ["ac", "abc", "abbc"]),
    ("a{2,3}", ["a", "aa", "aaa", "aaaa", ""]),
    ("a{2}", ["a", "aa", "aaa"]),
    ("a{2,}", ["a", "aa", "aaaaa"]),
    ("cat|dog|bird", ["cat", "dog", "bird", "fish", ""]),
    ("(ab)+", ["ab", "abab", "aba", "ababab"]),
    ("(cat|dog)s", ["cats", "dogs", "cat", "birds"]),
    ("[aeiou]+", ["aeiou", "aeioux", "xyz", ""]),
    ("[^aeiou]+", ["xyz", "aeiou", "xyzA"]),
    ("[a-f]+", ["abcdef", "abcdefg", "xyz"]),
    (r"\d+", ["123", "abc", "12a34", ""]),
    (r"\d{3}-\d{4}", ["555-1234", "55-1234", "5555-1234"]),
    (r"\w+", ["hello_world123", "hello world", ""]),
    (r"\s+", ["   ", "\t\n", "abc"]),
    ("^abc$", ["abc", "xabc", "abcx", ""]),
    ("^a.*z$", ["az", "abcz", "azz", "za"]),
    ("colou?r", ["color", "colour", "colouur"]),
    ("(a|b)(c|d)", ["ac", "ad", "bc", "bd", "ab"]),
    ("(foo)+bar", ["foobar", "foofoobar", "bar", "foobarx"]),
    ("[0-9a-fA-F]+", ["1a2B3c", "xyz", "DEAD"]),
    ("a*b*c*", ["", "abc", "aaabbbccc", "cba"]),
    (".*", ["", "anything at all", "\n"]),
]


@pytest.mark.parametrize("pattern,text", [(p, t) for p, texts in CASES for t in texts])
def test_fullmatch_agrees_with_stdlib_re(pattern, text):
    ours = regex.compile(pattern).fullmatch(text)
    theirs = stdlib_re.compile(pattern).fullmatch(text)
    assert (ours is not None) == (theirs is not None), (pattern, text)


@pytest.mark.parametrize("pattern,text", [(p, t) for p, texts in CASES for t in texts])
def test_search_agrees_with_stdlib_re_on_presence(pattern, text):
    ours = regex.compile(pattern).search(text)
    theirs = stdlib_re.compile(pattern).search(text)
    assert (ours is not None) == (theirs is not None), (pattern, text)
    if ours is not None and theirs is not None:
        assert ours.span() == theirs.span(), (pattern, text)


FINDALL_CASES = [
    (r"\d+", "there are 42 cats and 7 dogs, id 12345"),
    (r"[a-z]+", "Hello World foo Bar baz"),
    ("a+", "aaa bb a aa"),
    (r"\w+", "  spaced   out   words  "),
    ("ab", "abababab"),
]


@pytest.mark.parametrize("pattern,text", FINDALL_CASES)
def test_findall_agrees_with_stdlib_re(pattern, text):
    ours = regex.compile(pattern).findall(text)
    theirs = stdlib_re.compile(pattern).findall(text)
    assert ours == theirs, (pattern, text)
