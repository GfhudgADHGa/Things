from chess.board import Board, STARTING_FEN
from chess.evaluate import evaluate


def test_starting_position_is_symmetric():
    board = Board.from_fen(STARTING_FEN)
    assert evaluate(board) == 0


def test_extra_material_favors_that_side():
    white_up_a_queen = Board.from_fen("4k3/8/8/8/8/8/8/Q3K3 w - - 0 1")
    even = Board.from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    assert evaluate(white_up_a_queen) > evaluate(even)


def test_black_material_advantage_is_negative():
    black_up_a_rook = Board.from_fen("4k3/8/8/8/8/8/8/r3K3 w - - 0 1")
    assert evaluate(black_up_a_rook) < 0


def test_symmetric_position_with_pieces_is_zero():
    board = Board.from_fen("4k3/8/8/3n4/3N4/8/8/4K3 w - - 0 1")
    assert evaluate(board) == 0
