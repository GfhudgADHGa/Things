from chess.board import Board, STARTING_FEN, square_from_name
from chess.cli import game_status_message, parse_move_input, render


def test_render_shows_eight_ranks_and_files():
    board = Board.from_fen(STARTING_FEN)
    output = render(board)
    lines = output.splitlines()
    assert len(lines) == 9
    assert "R N B Q K B N R" in lines[7]  # rank 1


def test_parse_move_input_valid():
    board = Board.from_fen(STARTING_FEN)
    move = parse_move_input(board, "e2e4")
    assert move is not None
    assert move.from_sq == square_from_name("e2")
    assert move.to_sq == square_from_name("e4")


def test_parse_move_input_illegal_returns_none():
    board = Board.from_fen(STARTING_FEN)
    assert parse_move_input(board, "e2e5") is None  # pawns can't jump 3 ranks


def test_parse_move_input_garbage_returns_none():
    board = Board.from_fen(STARTING_FEN)
    assert parse_move_input(board, "not a move") is None
    assert parse_move_input(board, "") is None


def test_parse_move_input_promotion():
    board = Board.from_fen("8/P7/8/8/8/8/8/k6K w - - 0 1")
    move = parse_move_input(board, "a7a8q")
    assert move is not None
    assert move.promotion == "Q"


def test_game_status_message_none_mid_game():
    board = Board.from_fen(STARTING_FEN)
    assert game_status_message(board) is None


def test_game_status_message_checkmate():
    from chess.moves import apply_move, generate_legal_moves

    mate_board = Board.from_fen("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    move = next(m for m in generate_legal_moves(mate_board) if m.to_sq == square_from_name("a8"))
    mated = apply_move(mate_board, move)
    message = game_status_message(mated)
    assert message is not None
    assert "Checkmate" in message


def test_game_status_message_stalemate():
    board = Board.from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    message = game_status_message(board)
    assert message == "Stalemate. Draw."
