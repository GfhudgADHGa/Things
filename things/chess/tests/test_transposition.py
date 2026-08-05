from chess.board import Board, STARTING_FEN, square_from_name
from chess.moves import generate_legal_moves
from chess.search import MATE_SCORE, find_best_move, find_best_move_iterative


KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def test_tt_backed_search_still_finds_mate_in_one():
    board = Board.from_fen("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    move, score, stats = find_best_move(board, depth=2)
    assert move is not None
    assert move.to_uci() == "a1a8"
    assert score > MATE_SCORE - 100


def test_tt_reduces_node_count_on_a_richer_position():
    # Kiwipete has a lot of transpositions reachable within a few plies,
    # but only once the search is deep enough for different move orders to
    # actually reconverge on the same position (depth 3 sees essentially
    # none; depth 4 reliably does) -- the TT should show hits at depth 4.
    board = Board.from_fen(KIWIPETE)
    _, _, stats = find_best_move(board, depth=4)
    assert stats.tt_hits > 0


def test_tt_search_move_is_always_legal():
    board = Board.from_fen(STARTING_FEN)
    move, _, _ = find_best_move(board, depth=3)
    assert move in generate_legal_moves(board)


def test_iterative_deepening_returns_legal_move():
    board = Board.from_fen(STARTING_FEN)
    move, score, stats, depth_reached = find_best_move_iterative(board, max_depth=3)
    assert move in generate_legal_moves(board)
    assert depth_reached == 3


def test_iterative_deepening_finds_mate_in_one():
    board = Board.from_fen("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    move, score, stats, depth_reached = find_best_move_iterative(board, max_depth=5)
    assert move is not None
    assert move.to_uci() == "a1a8"
    assert score > MATE_SCORE - 100


def test_iterative_deepening_stops_searching_deeper_once_mate_found():
    board = Board.from_fen("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    move, score, stats, depth_reached = find_best_move_iterative(board, max_depth=20)
    assert depth_reached < 20  # should bail out early once mate-in-1 is confirmed


def test_iterative_deepening_respects_time_limit():
    import time

    board = Board.from_fen(STARTING_FEN)
    start = time.time()
    move, score, stats, depth_reached = find_best_move_iterative(
        board, max_depth=20, time_limit_seconds=0.3
    )
    elapsed = time.time() - start
    assert move is not None
    assert elapsed < 3.0  # generous bound: one in-progress iteration may overrun slightly


def test_iterative_deepening_returns_none_with_no_legal_moves():
    stalemated = Board.from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    move, score, stats, depth_reached = find_best_move_iterative(stalemated, max_depth=3)
    assert move is None
    assert depth_reached == 0


def test_iterative_deepening_depth_1_matches_fixed_depth_1():
    board = Board.from_fen(STARTING_FEN)
    move_a, score_a, _, _ = find_best_move_iterative(board, max_depth=1)
    move_b, score_b, _ = find_best_move(board, depth=1)
    assert score_a == score_b


def test_deeper_iterative_search_reaches_requested_depth_when_no_mate():
    board = Board.from_fen(STARTING_FEN)
    _, _, _, depth_reached = find_best_move_iterative(board, max_depth=2)
    assert depth_reached == 2
