from sudoku.board import (
    box_of,
    cell_index,
    col_of,
    is_complete,
    is_valid_board,
    is_valid_placement,
    parse,
    peers,
    pretty,
    row_of,
    to_string,
)

SOLVED = [
    6, 3, 9, 2, 5, 1, 7, 4, 8,
    4, 5, 8, 3, 6, 7, 9, 1, 2,
    1, 7, 2, 8, 4, 9, 3, 6, 5,
    5, 8, 3, 4, 1, 6, 2, 9, 7,
    2, 9, 4, 7, 3, 8, 1, 5, 6,
    7, 6, 1, 5, 9, 2, 4, 8, 3,
    3, 4, 6, 1, 2, 5, 8, 7, 9,
    8, 2, 5, 9, 7, 4, 6, 3, 1,
    9, 1, 7, 6, 8, 3, 5, 2, 4,
]


def test_row_col_box_of():
    assert row_of(0) == 0
    assert col_of(0) == 0
    assert row_of(80) == 8
    assert col_of(80) == 8
    assert box_of(0) == 0
    assert box_of(4) == 1
    assert box_of(80) == 8


def test_cell_index_roundtrip():
    for r in range(9):
        for c in range(9):
            i = cell_index(r, c)
            assert row_of(i) == r
            assert col_of(i) == c


def test_peers_count_is_twenty():
    for i in range(81):
        assert len(peers(i)) == 20


def test_peers_excludes_self():
    for i in [0, 40, 80]:
        assert i not in peers(i)


def test_peers_share_row_col_or_box():
    i = cell_index(4, 4)
    for p in peers(i):
        assert row_of(p) == 4 or col_of(p) == 4 or box_of(p) == box_of(i)


def test_parse_and_to_string_roundtrip():
    text = "." * 81
    board = parse(text)
    assert board == [0] * 81
    assert to_string(board) == text


def test_parse_rejects_wrong_length():
    import pytest

    with pytest.raises(ValueError):
        parse("123")


def test_parse_accepts_zeros_and_dots_interchangeably():
    a = parse("0" * 81)
    b = parse("." * 81)
    assert a == b


def test_is_complete():
    assert is_complete(SOLVED)
    assert not is_complete([0] + SOLVED[1:])


def test_is_valid_board_true_for_solved_grid():
    assert is_valid_board(SOLVED)


def test_is_valid_board_false_for_duplicate_in_row():
    bad = SOLVED[:]
    bad[1] = bad[0]  # duplicate within row 0
    assert not is_valid_board(bad)


def test_is_valid_board_false_for_duplicate_in_column():
    bad = SOLVED[:]
    bad[9] = bad[0]  # duplicate within column 0
    assert not is_valid_board(bad)


def test_is_valid_board_true_for_empty_board():
    assert is_valid_board([0] * 81)


def test_is_valid_placement():
    board = [0] * 81
    board[0] = 5
    assert not is_valid_placement(board, 1, 5)  # same row
    assert not is_valid_placement(board, 9, 5)  # same column
    assert is_valid_placement(board, 1, 6)


def test_pretty_has_nine_rows_and_dividers():
    output = pretty(SOLVED)
    lines = output.splitlines()
    assert len(lines) == 11  # 9 rows + 2 divider lines
    assert "------+-------+------" in lines
