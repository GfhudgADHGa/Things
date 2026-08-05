from chess.board import Board, STARTING_FEN
from chess.moves import apply_move, generate_legal_moves
from chess.zobrist import zobrist_hash


def test_same_fen_hashes_identically():
    a = Board.from_fen(STARTING_FEN)
    b = Board.from_fen(STARTING_FEN)
    assert zobrist_hash(a) == zobrist_hash(b)


def test_different_positions_hash_differently():
    a = Board.from_fen(STARTING_FEN)
    b = Board.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    assert zobrist_hash(a) != zobrist_hash(b)


def test_transposition_same_position_via_different_move_orders():
    # 1. Nf3 Nf6 2. Ng1 Ng8 reaches the exact starting position again
    board = Board.from_fen(STARTING_FEN)
    start_hash = zobrist_hash(board)

    def play(b, from_name, to_name):
        moves = generate_legal_moves(b)
        for m in moves:
            from chess.board import square_from_name
            if m.from_sq == square_from_name(from_name) and m.to_sq == square_from_name(to_name):
                return apply_move(b, m)
        raise AssertionError(f"no legal move {from_name}{to_name}")

    board = play(board, "g1", "f3")
    board = play(board, "g8", "f6")
    board = play(board, "f3", "g1")
    board = play(board, "f6", "g8")

    # piece placement, side to move, castling rights, and en passant are
    # all back to the starting position -- only the halfmove clock and
    # fullmove number differ, and Zobrist hashing deliberately ignores
    # those (they don't affect what moves are legal)
    assert board.squares == Board.from_fen(STARTING_FEN).squares
    assert zobrist_hash(board) == start_hash


def test_side_to_move_affects_hash():
    white_to_move = Board.from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    black_to_move = Board.from_fen("4k3/8/8/8/8/8/8/4K3 b - - 0 1")
    assert zobrist_hash(white_to_move) != zobrist_hash(black_to_move)


def test_castling_rights_affect_hash():
    with_rights = Board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    without_rights = Board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1")
    assert zobrist_hash(with_rights) != zobrist_hash(without_rights)


def test_en_passant_target_affects_hash():
    with_ep = Board.from_fen("rnbqkbnr/ppp1pppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 3")
    without_ep = Board.from_fen("rnbqkbnr/ppp1pppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 3")
    assert zobrist_hash(with_ep) != zobrist_hash(without_ep)


def test_hash_is_deterministic_across_calls():
    board = Board.from_fen(STARTING_FEN)
    assert zobrist_hash(board) == zobrist_hash(board)
