import random

import pytest

from difftool.diff import edit_distance, myers_diff


def reconstruct_a(ops):
    return [line for op, line in ops if op in ("equal", "delete")]


def reconstruct_b(ops):
    return [line for op, line in ops if op in ("equal", "insert")]


def test_identical_sequences_are_all_equal_ops():
    a = ["x", "y", "z"]
    ops = myers_diff(a, a)
    assert all(op == "equal" for op, _ in ops)
    assert [line for _, line in ops] == a


def test_empty_to_empty():
    assert myers_diff([], []) == []


def test_empty_a_is_all_inserts():
    ops = myers_diff([], ["a", "b"])
    assert ops == [("insert", "a"), ("insert", "b")]


def test_empty_b_is_all_deletes():
    ops = myers_diff(["a", "b"], [])
    assert ops == [("delete", "a"), ("delete", "b")]


def test_single_middle_line_changed():
    ops = myers_diff(["a", "b", "c"], ["a", "x", "c"])
    assert reconstruct_a(ops) == ["a", "b", "c"]
    assert reconstruct_b(ops) == ["a", "x", "c"]
    # 'a' and 'c' are unchanged context; 'b' is deleted, 'x' is inserted
    assert ("equal", "a") in ops
    assert ("equal", "c") in ops
    assert ("delete", "b") in ops
    assert ("insert", "x") in ops


def test_reconstruction_roundtrip_always_holds():
    random.seed(0)
    alphabet = list("abcde")
    for _ in range(300):
        a = [random.choice(alphabet) for _ in range(random.randint(0, 10))]
        b = [random.choice(alphabet) for _ in range(random.randint(0, 10))]
        ops = myers_diff(a, b)
        assert reconstruct_a(ops) == a
        assert reconstruct_b(ops) == b


def test_edit_distance_of_identical_sequences_is_zero():
    assert edit_distance(["a", "b"], ["a", "b"]) == 0


def test_edit_distance_of_completely_disjoint_sequences():
    assert edit_distance(["a", "b"], ["c", "d"]) == 4  # delete both, insert both


def test_edit_distance_matches_hand_computed_lcs_case():
    # LCS(['c','e'], ['a','d','e','a','b']) = ['e'] (length 1); minimal
    # edit distance under insert/delete only = len(a) + len(b) - 2*LCS
    # = 2 + 5 - 2 = 5
    assert edit_distance(["c", "e"], ["a", "d", "e", "a", "b"]) == 5


def test_myers_is_never_worse_than_difflib_across_many_random_cases():
    """Myers finds a *provably minimal* edit script. difflib's
    SequenceMatcher does not guarantee minimality (it's a different,
    heuristic algorithm) -- so the correct cross-check isn't "equal edit
    counts," it's "ours is never larger." An earlier version of this test
    compared edit counts directly and saw frequent, large "mismatches" in
    both directions; those turned out to be a bug in the comparison itself
    (treating a difflib 'replace' opcode's cost as max(deleted, inserted)
    instead of the correct deleted + inserted under an insert/delete-only
    model, which is what myers_diff produces) rather than a real problem
    with either algorithm. With the comparison fixed, minimality holds
    across every random case tried.
    """
    import difflib

    def difflib_edit_count(a, b):
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        total = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            total += (i2 - i1) + (j2 - j1)
        return total

    random.seed(1)
    alphabet = list("abcde")
    for _ in range(500):
        a = [random.choice(alphabet) for _ in range(random.randint(0, 8))]
        b = [random.choice(alphabet) for _ in range(random.randint(0, 8))]
        assert edit_distance(a, b) <= difflib_edit_count(a, b), (a, b)


@pytest.mark.parametrize("size", [1, 5, 20, 50])
def test_larger_random_inputs_still_roundtrip(size):
    random.seed(size)
    alphabet = [f"line{i}" for i in range(10)]
    a = [random.choice(alphabet) for _ in range(size)]
    b = [random.choice(alphabet) for _ in range(size)]
    ops = myers_diff(a, b)
    assert reconstruct_a(ops) == a
    assert reconstruct_b(ops) == b
