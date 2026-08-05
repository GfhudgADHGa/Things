"""A small algorithmic composer: given a key, scale, and chord progression,
generates a bass line, sustained chord pads, and a stepwise-random-walk
melody, then mixes them into one audio buffer.

This is deliberately simple -- a random walk biased toward small steps
(favoring stepwise motion, the way real melodies mostly move) rather than
anything resembling real music AI. It sounds coherent because diatonic
harmony (picking notes from one scale, chords built from that scale's
degrees) does most of the work.
"""
from __future__ import annotations

import random
from typing import List, Optional, Sequence

from .drums import render_drum_track
from .synth import mix, render_note, silence
from .theory import SCALES, chord_midi_notes, midi_to_freq, note_name_to_midi, scale_midi_notes

ROMAN_TO_DEGREE = {"I": 0, "ii": 1, "iii": 2, "IV": 3, "V": 4, "vi": 5, "vii": 6}

# diatonic chord qualities for a major scale (I/IV/V major, ii/iii/vi minor,
# vii diminished) -- the standard major-key harmony rule of thumb
MAJOR_SCALE_CHORD_QUALITIES = {
    0: "major", 1: "minor", 2: "minor", 3: "major",
    4: "major", 5: "minor", 6: "diminished",
}

MELODY_STEP_CHOICES = [-2, -1, -1, 0, 1, 1, 2]


def _default_drum_patterns(beats_per_chord: int) -> tuple:
    """A plain pop/rock beat, generated to fit any beats_per_chord: kick
    on beat 1 (and beat 3, if there are at least 3 beats), snare on the
    other even-numbered beats, hi-hat on every 8th note."""
    steps = beats_per_chord * 4  # 16th notes per chord
    kick_steps = {0}
    if beats_per_chord >= 3:
        kick_steps.add(2 * 4)
    snare_steps = {b * 4 for b in range(1, beats_per_chord, 2)}
    hihat_steps = set(range(0, steps, 2))
    pattern = lambda hit_steps: "".join("x" if i in hit_steps else "." for i in range(steps))  # noqa: E731
    return pattern(kick_steps), pattern(snare_steps), pattern(hihat_steps)


def compose(
    key: str = "C4",
    scale_name: str = "major",
    progression: Sequence[str] = ("I", "V", "vi", "IV"),
    tempo_bpm: float = 100,
    beats_per_chord: int = 4,
    seed: int = 42,
    sample_rate: int = 44100,
    drums: bool = True,
    drum_pattern: Optional[tuple] = None,
) -> List[float]:
    if scale_name not in SCALES:
        raise ValueError(f"unknown scale: {scale_name!r}")

    rng = random.Random(seed)
    root_midi = note_name_to_midi(key)
    intervals = SCALES[scale_name]
    melody_range = scale_midi_notes(root_midi, scale_name, octaves=2)

    beat = 60.0 / tempo_bpm
    chord_duration = beats_per_chord * beat
    eighth = beat / 2
    sixteenth = beat / 4
    notes_per_chord = max(1, round(chord_duration / eighth))

    if drums:
        kick_pattern, snare_pattern, hihat_pattern = drum_pattern or _default_drum_patterns(beats_per_chord)
        expected_steps = beats_per_chord * 4
        if any(len(p) != expected_steps for p in (kick_pattern, snare_pattern, hihat_pattern)):
            raise ValueError(
                f"drum_pattern strings must each have {expected_steps} steps "
                f"(beats_per_chord * 4) to stay aligned with the chord progression"
            )

    bass_track: List[float] = []
    chord_track: List[float] = []
    melody_track: List[float] = []
    drum_track: List[float] = []

    melody_idx = rng.randrange(len(melody_range))

    for chord_index, roman in enumerate(progression):
        if roman not in ROMAN_TO_DEGREE:
            raise ValueError(f"unknown roman numeral: {roman!r}")
        degree = ROMAN_TO_DEGREE[roman] % len(intervals)
        chord_root = root_midi + intervals[degree]
        quality = MAJOR_SCALE_CHORD_QUALITIES.get(degree, "major") if scale_name == "major" else "major"
        chord_notes = chord_midi_notes(chord_root, quality)

        bass_track += render_note(
            midi_to_freq(chord_root - 12), chord_duration, sample_rate,
            waveform="triangle", amplitude=0.22, adsr=(0.02, 0.08, 0.8, 0.15),
        )
        chord_track += mix(*[
            render_note(
                midi_to_freq(n), chord_duration, sample_rate,
                waveform="sine", amplitude=0.07, adsr=(0.4, 0.2, 0.6, 0.3),
            )
            for n in chord_notes
        ])

        for _ in range(notes_per_chord):
            step = rng.choice(MELODY_STEP_CHOICES)
            melody_idx = max(0, min(len(melody_range) - 1, melody_idx + step))
            note_freq = midi_to_freq(melody_range[melody_idx]) * 2  # an octave up, for a brighter lead
            melody_track += render_note(
                note_freq, eighth * 0.9, sample_rate,
                waveform="square", amplitude=0.12, adsr=(0.005, 0.03, 0.6, 0.05),
            )
            melody_track += silence(eighth * 0.1, sample_rate)

        if drums:
            drum_track += render_drum_track(
                kick_pattern, snare_pattern, hihat_pattern,
                step_duration=sixteenth, sample_rate=sample_rate,
                seed=seed + chord_index,
            )

    tracks = [bass_track, chord_track, melody_track]
    if drums:
        tracks.append(drum_track)
    return mix(*tracks)
