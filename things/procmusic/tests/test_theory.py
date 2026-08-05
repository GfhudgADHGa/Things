import math

import pytest

from procmusic.theory import (
    CHORDS,
    SCALES,
    chord_midi_notes,
    midi_to_freq,
    midi_to_note_name,
    note_name_to_midi,
    note_to_freq,
    scale_midi_notes,
)


def test_a4_is_concert_pitch():
    assert note_name_to_midi("A4") == 69
    assert midi_to_freq(69) == 440.0


def test_middle_c_is_midi_60():
    assert note_name_to_midi("C4") == 60


def test_octave_doubles_frequency():
    assert math.isclose(note_to_freq("A5"), note_to_freq("A4") * 2, rel_tol=1e-9)
    assert math.isclose(note_to_freq("A3"), note_to_freq("A4") / 2, rel_tol=1e-9)


def test_known_equal_temperament_frequencies():
    # standard reference values, equal temperament, A4=440
    assert math.isclose(note_to_freq("C4"), 261.63, abs_tol=0.01)
    assert math.isclose(note_to_freq("E4"), 329.63, abs_tol=0.01)
    assert math.isclose(note_to_freq("G4"), 392.00, abs_tol=0.01)


def test_sharp_and_flat_enharmonic_equivalence():
    assert note_name_to_midi("C#4") == note_name_to_midi("Db4")
    assert note_to_freq("D#3") == note_to_freq("Eb3")


def test_lowercase_letter_accepted():
    assert note_name_to_midi("c4") == note_name_to_midi("C4")


def test_invalid_note_name_raises():
    with pytest.raises(ValueError):
        note_name_to_midi("H4")


def test_midi_to_note_name_roundtrip():
    for name in ["C4", "A4", "C#5", "G3"]:
        midi = note_name_to_midi(name)
        assert note_name_to_midi(midi_to_note_name(midi)) == midi


def test_major_scale_intervals_from_c():
    notes = scale_midi_notes(60, "major", octaves=1)
    names = [midi_to_note_name(n) for n in notes]
    assert names == ["C4", "D4", "E4", "F4", "G4", "A4", "B4"]


def test_natural_minor_scale_intervals_from_a():
    notes = scale_midi_notes(69, "natural_minor", octaves=1)
    names = [midi_to_note_name(n) for n in notes]
    assert names == ["A4", "B4", "C5", "D5", "E5", "F5", "G5"]


def test_scale_spans_multiple_octaves():
    notes = scale_midi_notes(60, "major", octaves=2)
    assert len(notes) == 14
    assert notes[7] == notes[0] + 12  # same scale degree, one octave up


def test_all_scales_are_within_one_octave_of_intervals():
    for name, intervals in SCALES.items():
        assert all(0 <= i < 12 for i in intervals), name
        assert intervals[0] == 0, name


def test_major_chord_from_c():
    notes = chord_midi_notes(60, "major")
    names = [midi_to_note_name(n) for n in notes]
    assert names == ["C4", "E4", "G4"]


def test_minor_chord_from_a():
    notes = chord_midi_notes(69, "minor")
    names = [midi_to_note_name(n) for n in notes]
    assert names == ["A4", "C5", "E5"]


def test_dominant_seventh_chord():
    notes = chord_midi_notes(60, "dominant7")
    names = [midi_to_note_name(n) for n in notes]
    assert names == ["C4", "E4", "G4", "A#4"]


def test_all_chords_start_at_root():
    for name, intervals in CHORDS.items():
        assert intervals[0] == 0, name
