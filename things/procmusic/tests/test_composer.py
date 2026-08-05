import pytest

from procmusic.composer import compose

SAMPLE_RATE = 44100


def test_compose_produces_nonempty_audio():
    samples = compose(seed=1)
    assert len(samples) > 0
    assert any(s != 0.0 for s in samples)


def test_compose_duration_matches_progression_length():
    tempo = 100
    beats_per_chord = 4
    progression = ("I", "V", "vi", "IV")
    beat = 60.0 / tempo
    expected_duration = len(progression) * beats_per_chord * beat

    samples = compose(progression=progression, tempo_bpm=tempo, beats_per_chord=beats_per_chord)
    actual_duration = len(samples) / SAMPLE_RATE
    assert abs(actual_duration - expected_duration) < 0.05


def test_compose_is_deterministic_given_seed():
    a = compose(seed=7)
    b = compose(seed=7)
    assert a == b


def test_different_seeds_produce_different_melodies():
    a = compose(seed=1)
    b = compose(seed=2)
    assert a != b


def test_compose_stays_within_safe_amplitude_range():
    samples = compose(seed=3)
    assert max(abs(s) for s in samples) <= 1.0


def test_unknown_scale_raises():
    with pytest.raises(ValueError):
        compose(scale_name="not_a_real_scale")


def test_unknown_roman_numeral_raises():
    with pytest.raises(ValueError):
        compose(progression=("I", "not_a_numeral"))


def test_minor_key_composition_works():
    samples = compose(key="A3", scale_name="natural_minor", progression=("I", "vi", "iii", "vii"))
    assert len(samples) > 0


def test_longer_progression_yields_longer_audio():
    short = compose(progression=("I", "V"))
    long = compose(progression=("I", "V", "vi", "IV", "I", "V"))
    assert len(long) > len(short)


def test_tempo_affects_duration():
    slow = compose(progression=("I",), tempo_bpm=60)
    fast = compose(progression=("I",), tempo_bpm=120)
    assert len(slow) > len(fast)
