import time

from sudoku.board import is_complete, is_valid_board, parse
from sudoku.generator import generate_puzzle
from sudoku.solver import candidates, count_solutions, has_unique_solution, solve

EASY_PUZZLE = parse(
    "53..7...."
    "6..195..."
    ".98....6."
    "8...6...3"
    "4..8.3..1"
    "7...2...6"
    ".6....28."
    "...419..5"
    "....8..79"
)

EASY_SOLUTION = parse(
    "534678912"
    "672195348"
    "198342567"
    "859761423"
    "426853791"
    "713924856"
    "961537284"
    "287419635"
    "345286179"
)


def test_solves_known_easy_puzzle():
    result = solve(EASY_PUZZLE)
    assert result == EASY_SOLUTION


def test_solve_returns_none_for_unsolvable_board():
    # two 5s given in the same row: no valid completion can ever exist.
    # (This directly exercises solve()'s upfront is_valid_board() check --
    # see test_solve_rejects_conflicting_givens_instantly below for why
    # that check exists at all, not just what it returns.)
    board = [0] * 81
    board[0] = 5
    board[1] = 5
    assert solve(board) is None


def test_solve_rejects_conflicting_givens_instantly():
    # Without an upfront validity check, a board with two peers already
    # sharing a value doesn't look locally broken to the backtracking
    # search: each individual empty cell's candidate list just excludes
    # the duplicated value once, same as it would for a normal single
    # given -- so the search can spend a very long time constructing an
    # otherwise-plausible completion before it exhausts every possibility
    # and concludes there's no solution. solve() should short-circuit
    # instead of ever starting that search.
    board = [0] * 81
    board[0] = 5
    board[1] = 5
    start = time.time()
    result = solve(board)
    elapsed = time.time() - start
    assert result is None
    assert elapsed < 0.1


def test_solve_returns_none_for_unsolvable_board_with_a_dead_end_cell():
    # A different flavor of unsolvable: take a valid solved grid, clear one
    # cell, then force one of its peers to also take on that cleared cell's
    # own correct value -- now every one of the 9 digits is "used" among
    # its peers, so it has zero valid candidates. This one isn't caught by
    # the upfront is_valid_board() check (the *given* cells are all still
    # mutually consistent) -- it has to be found during the search itself,
    # which it is, immediately, since it's the very first cell considered.
    from sudoku.board import peers

    full = solve([0] * 81)
    board = full[:]
    target = 0
    correct_value = board[target]
    board[target] = 0
    conflicting_peer = next(iter(peers(target)))
    board[conflicting_peer] = correct_value

    assert solve(board) is None


def test_solve_result_is_complete_and_valid():
    result = solve(EASY_PUZZLE)
    assert is_complete(result)
    assert is_valid_board(result)


def test_solve_preserves_given_clues():
    result = solve(EASY_PUZZLE)
    for i, v in enumerate(EASY_PUZZLE):
        if v != 0:
            assert result[i] == v


def test_solve_does_not_mutate_input():
    original = EASY_PUZZLE[:]
    solve(EASY_PUZZLE)
    assert EASY_PUZZLE == original


def test_candidates_for_empty_cell():
    board = [0] * 81
    board[0] = 5
    cands = candidates(board, 1)
    assert 5 not in cands
    assert len(cands) == 8


def test_candidates_for_filled_cell_is_empty():
    board = [0] * 81
    board[0] = 5
    assert candidates(board, 0) == []


def test_count_solutions_on_unique_puzzle():
    assert count_solutions(EASY_PUZZLE, limit=2) == 1


def test_count_solutions_on_empty_board_hits_limit():
    # a blank board has millions of solutions; should stop counting at the limit
    assert count_solutions([0] * 81, limit=2) == 2


def test_has_unique_solution_true_for_easy_puzzle():
    assert has_unique_solution(EASY_PUZZLE)


def test_has_unique_solution_false_for_near_empty_board():
    assert not has_unique_solution([0] * 81)


def test_solver_handles_a_hard_generated_puzzle_quickly():
    # low clue count puzzles need real backtracking, not just elimination
    puzzle = generate_puzzle(seed=99, min_clues=24)
    start = time.time()
    result = solve(puzzle)
    elapsed = time.time() - start
    assert result is not None
    assert is_valid_board(result)
    assert is_complete(result)
    assert elapsed < 5.0


def test_solver_is_consistent_across_many_generated_puzzles():
    for seed in range(10):
        puzzle = generate_puzzle(seed=seed, min_clues=28)
        result = solve(puzzle)
        assert result is not None
        assert is_valid_board(result)
        assert is_complete(result)
