import random

import pytest

from difftool.diff import myers_diff
from difftool.patch import PatchError, apply_patch


def test_apply_patch_reconstructs_b():
    a = ["a", "b", "c"]
    b = ["a", "x", "c"]
    ops = myers_diff(a, b)
    assert apply_patch(a, ops) == b


def test_apply_patch_identity():
    a = ["one", "two", "three"]
    ops = myers_diff(a, a)
    assert apply_patch(a, ops) == a


def test_apply_patch_empty_to_something():
    ops = myers_diff([], ["a", "b"])
    assert apply_patch([], ops) == ["a", "b"]


def test_apply_patch_something_to_empty():
    ops = myers_diff(["a", "b"], [])
    assert apply_patch(["a", "b"], ops) == []


def test_apply_patch_rejects_mismatched_source():
    a = ["a", "b", "c"]
    b = ["a", "x", "c"]
    ops = myers_diff(a, b)
    wrong_source = ["a", "DIFFERENT", "c"]
    with pytest.raises(PatchError):
        apply_patch(wrong_source, ops)


def test_apply_patch_rejects_shorter_source():
    ops = myers_diff(["a", "b", "c"], ["a", "x"])
    with pytest.raises(PatchError):
        apply_patch(["a"], ops)


def test_apply_patch_rejects_longer_source():
    ops = myers_diff(["a", "b"], ["a", "x"])
    with pytest.raises(PatchError):
        apply_patch(["a", "b", "extra"], ops)


def test_random_roundtrip_diff_then_patch():
    random.seed(3)
    alphabet = list("abcde")
    for _ in range(300):
        a = [random.choice(alphabet) for _ in range(random.randint(0, 10))]
        b = [random.choice(alphabet) for _ in range(random.randint(0, 10))]
        ops = myers_diff(a, b)
        assert apply_patch(a, ops) == b
