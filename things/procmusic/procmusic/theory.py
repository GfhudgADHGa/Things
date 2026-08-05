"""Music theory: note names <-> frequencies (12-tone equal temperament,
A4 = 440 Hz), scales, and chords -- all as semitone offsets from a root.
"""
from __future__ import annotations

import re
from typing import List

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

_FLAT_TO_SHARP = {
    "Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#",
}

_NOTE_RE = re.compile(r"^([A-Ga-g])([#b]?)(-?\d+)$")

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],
    "major_pentatonic": [0, 2, 4, 7, 9],
    "minor_pentatonic": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
}

CHORDS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented": [0, 4, 8],
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "dominant7": [0, 4, 7, 10],
}


def note_name_to_midi(name: str) -> int:
    """'A4' -> 69, 'C4' -> 60 (middle C), 'Db4' == 'C#4' -> 61."""
    m = _NOTE_RE.match(name)
    if not m:
        raise ValueError(f"unrecognized note name: {name!r}")
    letter, accidental, octave_str = m.groups()
    letter = letter.upper()
    octave = int(octave_str)

    normalized = letter + accidental
    if normalized in _FLAT_TO_SHARP:
        normalized = _FLAT_TO_SHARP[normalized]

    pitch_class = NOTE_NAMES.index(normalized)
    # MIDI note numbers: C-1 = 0, so C4 = 60
    return (octave + 1) * 12 + pitch_class


def midi_to_freq(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def midi_to_note_name(midi: int) -> str:
    octave = midi // 12 - 1
    pitch_class = midi % 12
    return f"{NOTE_NAMES[pitch_class]}{octave}"


def note_to_freq(name: str) -> float:
    return midi_to_freq(note_name_to_midi(name))


def scale_midi_notes(root_midi: int, scale_name: str, octaves: int = 1) -> List[int]:
    intervals = SCALES[scale_name]
    notes = []
    for octave in range(octaves):
        for interval in intervals:
            notes.append(root_midi + octave * 12 + interval)
    return notes


def chord_midi_notes(root_midi: int, chord_name: str) -> List[int]:
    return [root_midi + interval for interval in CHORDS[chord_name]]
