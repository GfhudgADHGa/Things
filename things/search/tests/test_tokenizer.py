from search.tokenizer import tokenize


def test_lowercases():
    assert tokenize("Hello WORLD") == ["hello", "world"]


def test_splits_on_punctuation():
    assert tokenize("fox, dog. cat!") == ["fox", "dog", "cat"]


def test_keeps_digits():
    assert tokenize("Python 3.12 released") == ["python", "3", "12", "released"]


def test_empty_string_is_empty():
    assert tokenize("") == []


def test_only_punctuation_is_empty():
    assert tokenize("... !!! ---") == []


def test_collapses_whitespace_runs():
    assert tokenize("a   b\t\tc\nd") == ["a", "b", "c", "d"]
