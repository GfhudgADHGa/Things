import pytest

from chess.board import Board, STARTING_FEN, square_from_name
from chess.moves import (
    apply_move,
    generate_legal_moves,
    is_checkmate,
    is_in_check,
    is_square_attacked,
    is_stalemate,
)
from chess.perft import perft

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


# ---- perft: the authoritative check that move generation is correct ----
# Reference values are the standard, widely-published perft results for
# these two positions (see the chess programming wiki's "Perft Results").

@pytest.mark.parametrize(
    "depth,expected",
    [(1, 20), (2, 400), (3, 8902), (4, 197281)],
)
def test_perft_starting_position(depth, expected):
    board = Board.from_fen(STARTING_FEN)
    assert perft(board, depth) == expected


@pytest.mark.parametrize(
    "depth,expected",
    [(1, 48), (2, 2039), (3, 97862)],
)
def test_perft_kiwipete(depth, expected):
    board = Board.from_fen(KIWIPETE)
    assert perft(board, depth) == expected


# ---- targeted rule tests ----

def test_starting_position_has_20_legal_moves():
    board = Board.from_fen(STARTING_FEN)
    assert len(generate_legal_moves(board)) == 20


def test_pawn_double_push_available_from_start():
    board = Board.from_fen(STARTING_FEN)
    moves = generate_legal_moves(board)
    e2e4 = [m for m in moves if m.from_sq == square_from_name("e2") and m.to_sq == square_from_name("e4")]
    assert len(e2e4) == 1


def test_en_passant_capture_available():
    # white just pushed e2-e4 past a black pawn on d4, giving en passant
    board = Board.from_fen("rnbqkbnr/ppp1pppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 3")
    moves = generate_legal_moves(board)
    ep_moves = [m for m in moves if m.is_en_passant]
    assert len(ep_moves) == 1
    assert ep_moves[0].to_sq == square_from_name("e3")

    result = apply_move(board, ep_moves[0])
    assert result.piece_at(square_from_name("e4")) is None  # captured pawn removed
    assert result.piece_at(square_from_name("e3")) == "bP"


def test_promotion_generates_four_moves():
    board = Board.from_fen("8/P7/8/8/8/8/8/k6K w - - 0 1")
    moves = generate_legal_moves(board)
    promos = [m for m in moves if m.from_sq == square_from_name("a7") and m.to_sq == square_from_name("a8")]
    assert {m.promotion for m in promos} == {"Q", "R", "B", "N"}


def test_promotion_to_queen_places_queen():
    board = Board.from_fen("8/P7/8/8/8/8/8/k6K w - - 0 1")
    move = next(
        m
        for m in generate_legal_moves(board)
        if m.to_sq == square_from_name("a8") and m.promotion == "Q"
    )
    result = apply_move(board, move)
    assert result.piece_at(square_from_name("a8")) == "wQ"


def test_castling_kingside_moves_rook_too():
    board = Board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    move = next(m for m in generate_legal_moves(board) if m.is_castle_kingside)
    result = apply_move(board, move)
    assert result.piece_at(square_from_name("g1")) == "wK"
    assert result.piece_at(square_from_name("f1")) == "wR"
    assert result.piece_at(square_from_name("h1")) is None


def test_castling_unavailable_through_check():
    # black rook on e-file pins nothing but f1 is attacked by a rook on f8
    board = Board.from_fen("4k3/5r2/8/8/8/8/8/R3K2R w KQ - 0 1")
    moves = generate_legal_moves(board)
    assert not any(m.is_castle_kingside for m in moves)


def test_castling_unavailable_when_squares_occupied():
    board = Board.from_fen("r3k2r/8/8/8/8/8/8/R2NK2R w KQkq - 0 1")
    moves = generate_legal_moves(board)
    assert not any(m.is_castle_queenside for m in moves)


def test_castling_rights_revoked_after_king_moves():
    board = Board.from_fen(STARTING_FEN)
    move = next(m for m in generate_legal_moves(board) if m.from_sq == square_from_name("e2") and m.to_sq == square_from_name("e4"))
    board = apply_move(board, move)
    move2 = next(m for m in generate_legal_moves(board) if m.from_sq == square_from_name("e7") and m.to_sq == square_from_name("e5"))
    board = apply_move(board, move2)
    move3 = next(m for m in generate_legal_moves(board) if m.from_sq == square_from_name("e1") and m.to_sq == square_from_name("e2"))
    board = apply_move(board, move3)
    assert "K" not in board.castling_rights and "Q" not in board.castling_rights


def test_pinned_piece_cannot_move_exposing_check():
    # white king e1, white bishop e2 pinned by black rook e8
    board = Board.from_fen("4r3/8/8/8/8/8/4B3/4K3 w - - 0 1")
    moves = generate_legal_moves(board)
    bishop_moves = [m for m in moves if m.from_sq == square_from_name("e2")]
    assert bishop_moves == []


def test_must_respond_to_check():
    # white king in check from black rook on e-file; only legal moves address it
    board = Board.from_fen("4r3/8/8/8/8/8/8/4K3 w - - 0 1")
    assert is_in_check(board, "w")
    moves = generate_legal_moves(board)
    for move in moves:
        result = apply_move(board, move)
        assert not is_in_check(result, "w")


def test_checkmate_detection_back_rank():
    board = Board.from_fen("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    move = next(m for m in generate_legal_moves(board) if m.to_sq == square_from_name("a8"))
    mated = apply_move(board, move)
    assert is_checkmate(mated)
    assert generate_legal_moves(mated) == []


def test_stalemate_detection():
    board = Board.from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert is_stalemate(board)
    assert not is_in_check(board, "b")
    assert generate_legal_moves(board) == []


def test_is_square_attacked_by_pawn():
    board = Board.from_fen("8/8/8/8/3p4/8/8/k6K b - - 0 1")
    # black pawn on d4 attacks c3 and e3
    assert is_square_attacked(board, square_from_name("c3"), "b")
    assert is_square_attacked(board, square_from_name("e3"), "b")
    assert not is_square_attacked(board, square_from_name("d3"), "b")


def test_capture_updates_halfmove_clock():
    board = Board.from_fen("8/8/8/3p4/4P3/8/8/k6K w - - 5 10")
    move = next(
        m for m in generate_legal_moves(board)
        if m.from_sq == square_from_name("e4") and m.to_sq == square_from_name("d5")
    )
    result = apply_move(board, move)
    assert result.halfmove_clock == 0


def test_fullmove_number_increments_after_black_moves():
    board = Board.from_fen(STARTING_FEN)
    move = next(m for m in generate_legal_moves(board) if m.from_sq == square_from_name("e2"))
    board = apply_move(board, move)
    assert board.fullmove_number == 1
    move2 = generate_legal_moves(board)[0]
    board = apply_move(board, move2)
    assert board.fullmove_number == 2
