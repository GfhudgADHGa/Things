from sudoku.board import is_complete, is_valid_board
from sudoku.generator import generate_puzzle, generate_solved_grid, rate_difficulty
from sudoku.solver import has_unique_solution, solve


def test_generate_solved_grid_is_complete_and_valid():
    grid = generate_solved_grid()
    assert is_complete(grid)
    assert is_valid_board(grid)


def test_generate_solved_grid_is_deterministic_given_seed():
    import random

    a = generate_solved_grid(random.Random(5))
    b = generate_solved_grid(random.Random(5))
    assert a == b


def test_different_seeds_give_different_grids():
    import random

    a = generate_solved_grid(random.Random(1))
    b = generate_solved_grid(random.Random(2))
    assert a != b


def test_generated_puzzle_has_unique_solution():
    puzzle = generate_puzzle(seed=1, min_clues=30)
    assert has_unique_solution(puzzle)


def test_generated_puzzle_is_solvable_to_a_valid_complete_grid():
    puzzle = generate_puzzle(seed=2, min_clues=30)
    result = solve(puzzle)
    assert result is not None
    assert is_complete(result)
    assert is_valid_board(result)


def test_generated_puzzle_respects_min_clues_floor():
    puzzle = generate_puzzle(seed=3, min_clues=30)
    clue_count = sum(1 for v in puzzle if v != 0)
    assert clue_count >= 30


def test_generate_puzzle_is_deterministic_given_seed():
    a = generate_puzzle(seed=42, min_clues=28)
    b = generate_puzzle(seed=42, min_clues=28)
    assert a == b


def test_many_generated_puzzles_all_have_unique_solutions():
    for seed in range(15):
        puzzle = generate_puzzle(seed=seed, min_clues=30)
        assert has_unique_solution(puzzle), f"seed {seed} produced a non-unique puzzle"


def test_rate_difficulty_returns_known_bucket():
    puzzle = generate_puzzle(seed=7, min_clues=30)
    assert rate_difficulty(puzzle) in ("easy", "medium", "hard")


def test_fewer_clues_tend_to_be_rated_harder_or_equal():
    # not a strict law (technique-based rating is a heuristic), but a puzzle
    # with very few givens should essentially never be rated "easy"
    hard_ish = generate_puzzle(seed=11, min_clues=24)
    assert rate_difficulty(hard_ish) in ("medium", "hard")
