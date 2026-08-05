from chess.board import Board, STARTING_FEN, square_from_name
from chess.moves import generate_legal_moves
from chess.search import MATE_SCORE, find_best_move


def test_finds_mate_in_one():
    board = Board.from_fen("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    move, score, stats = find_best_move(board, depth=2)
    assert move is not None
    assert move.to_uci() == "a1a8"
    assert score > MATE_SCORE - 100


def test_avoids_hanging_the_queen_for_free():
    # a black pawn on f6 guards e5; moving the white queen there loses it
    # for nothing, which a 2-ply search should see and avoid.
    board = Board.from_fen("4k3/8/5p2/8/8/8/8/4QK2 w - - 0 1")
    move, score, stats = find_best_move(board, depth=2)
    assert move.to_sq != square_from_name("e5")


def test_returns_none_when_no_legal_moves():
    stalemated = Board.from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    move, score, stats = find_best_move(stalemated, depth=2)
    assert move is None


def test_move_returned_is_always_legal():
    board = Board.from_fen(STARTING_FEN)
    move, score, stats = find_best_move(board, depth=2)
    assert move in generate_legal_moves(board)


def test_search_visits_at_least_one_node_per_move_considered():
    board = Board.from_fen(STARTING_FEN)
    move, score, stats = find_best_move(board, depth=1)
    assert stats.nodes >= len(generate_legal_moves(board))
