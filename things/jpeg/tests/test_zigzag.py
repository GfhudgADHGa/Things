from jpeg.zigzag import ZIGZAG, zigzag_order


def test_zigzag_starts_at_dc_and_covers_every_position_once():
    assert ZIGZAG[0] == (0, 0)
    assert len(ZIGZAG) == 64
    assert len(set(ZIGZAG)) == 64
    assert set(ZIGZAG) == {(v, u) for v in range(8) for u in range(8)}


def test_zigzag_order_extracts_correct_values():
    coeff = [[v * 8 + u for u in range(8)] for v in range(8)]
    ordered = zigzag_order(coeff)
    assert ordered[0] == 0  # (0,0)
    assert ordered[1] == 1  # (0,1)
    assert ordered[2] == 8  # (1,0)
    assert len(ordered) == 64
    assert set(ordered) == set(range(64))


def test_zigzag_visits_low_frequencies_before_high():
    # The point of zigzag order: (v+u) should be non-decreasing "mostly"
    # (it alternates direction within each anti-diagonal, but never jumps
    # backward to an earlier diagonal).
    diagonals = [v + u for v, u in ZIGZAG]
    for i in range(1, len(diagonals)):
        assert diagonals[i] >= diagonals[i - 1] - 0  # never regresses to an earlier diagonal group
    # more precisely: the diagonal index is monotonically non-decreasing
    assert diagonals == sorted(diagonals)
