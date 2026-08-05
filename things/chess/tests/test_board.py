from chess.board import Board, STARTING_FEN, opposite_color, square_from_name, square_name


def test_starting_fen_roundtrip():
    b = Board.from_fen(STARTING_FEN)
    assert b.to_fen() == STARTING_FEN


def test_square_name_and_back():
    assert square_name(0) == "a1"
    assert square_name(63) == "h8"
    assert square_name(4) == "e1"
    assert square_from_name("a1") == 0
    assert square_from_name("h8") == 63
    assert square_from_name("e4") == 28


def test_starting_position_piece_placement():
    b = Board.from_fen(STARTING_FEN)
    assert b.piece_at(square_from_name("a1")) == "wR"
    assert b.piece_at(square_from_name("e1")) == "wK"
    assert b.piece_at(square_from_name("d8")) == "bQ"
    assert b.piece_at(square_from_name("e4")) is None


def test_king_square():
    b = Board.from_fen(STARTING_FEN)
    assert b.king_square("w") == square_from_name("e1")
    assert b.king_square("b") == square_from_name("e8")


def test_king_square_missing_returns_none():
    b = Board.from_fen("8/8/8/8/8/8/8/8 w - - 0 1")
    assert b.king_square("w") is None


def test_custom_fen_roundtrip():
    fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    assert Board.from_fen(fen).to_fen() == fen


def test_en_passant_target_parsed():
    b = Board.from_fen("rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3")
    assert b.en_passant_target == square_from_name("d6")


def test_copy_is_independent():
    b = Board.from_fen(STARTING_FEN)
    c = b.copy()
    c.squares[0] = None
    assert b.squares[0] == "wR"


def test_opposite_color():
    assert opposite_color("w") == "b"
    assert opposite_color("b") == "w"


def test_str_representation_has_eight_ranks():
    b = Board.from_fen(STARTING_FEN)
    lines = str(b).splitlines()
    assert len(lines) == 9  # 8 ranks + file labels
    assert lines[0].startswith("8 ")
    assert lines[7].startswith("1 ")
