"""Waveform oscillators, ADSR envelopes, and mixing -- the raw synthesis
building blocks, all operating on plain lists of floats in [-1, 1].
"""
from __future__ import annotations

import math
from typing import List, Tuple

from .wav import SAMPLE_RATE


def _phase_samples(freq: float, duration: float, sample_rate: int) -> List[float]:
    n = int(duration * sample_rate)
    return [((freq * i) / sample_rate) % 1.0 for i in range(n)]


def sine_wave(freq: float, duration: float, sample_rate: int = SAMPLE_RATE, amplitude: float = 1.0) -> List[float]:
    return [amplitude * math.sin(2 * math.pi * p) for p in _phase_samples(freq, duration, sample_rate)]


def square_wave(freq: float, duration: float, sample_rate: int = SAMPLE_RATE, amplitude: float = 1.0, duty: float = 0.5) -> List[float]:
    return [amplitude if p < duty else -amplitude for p in _phase_samples(freq, duration, sample_rate)]


def sawtooth_wave(freq: float, duration: float, sample_rate: int = SAMPLE_RATE, amplitude: float = 1.0) -> List[float]:
    return [amplitude * (2 * p - 1) for p in _phase_samples(freq, duration, sample_rate)]


def triangle_wave(freq: float, duration: float, sample_rate: int = SAMPLE_RATE, amplitude: float = 1.0) -> List[float]:
    return [amplitude * (4 * abs(p - 0.5) - 1) for p in _phase_samples(freq, duration, sample_rate)]


OSCILLATORS = {
    "sine": sine_wave,
    "square": square_wave,
    "sawtooth": sawtooth_wave,
    "triangle": triangle_wave,
}


def apply_adsr(
    samples: List[float],
    sample_rate: int,
    attack: float,
    decay: float,
    sustain_level: float,
    release: float,
) -> List[float]:
    n = len(samples)
    attack_n = min(n, int(attack * sample_rate))
    decay_n = min(n - attack_n, int(decay * sample_rate))
    release_n = min(n - attack_n - decay_n, int(release * sample_rate))
    sustain_n = n - attack_n - decay_n - release_n

    envelope: List[float] = []
    envelope += [i / attack_n for i in range(attack_n)] if attack_n else []
    envelope += [1.0 + (sustain_level - 1.0) * (i / decay_n) for i in range(decay_n)] if decay_n else []
    envelope += [sustain_level] * sustain_n
    envelope += [sustain_level * (1.0 - i / release_n) for i in range(release_n)] if release_n else []

    return [s * e for s, e in zip(samples, envelope)]


DEFAULT_ADSR: Tuple[float, float, float, float] = (0.01, 0.05, 0.7, 0.08)


def render_note(
    freq: float,
    duration: float,
    sample_rate: int = SAMPLE_RATE,
    waveform: str = "sine",
    amplitude: float = 0.3,
    adsr: Tuple[float, float, float, float] = DEFAULT_ADSR,
) -> List[float]:
    oscillator = OSCILLATORS[waveform]
    samples = oscillator(freq, duration, sample_rate, amplitude)
    attack, decay, sustain_level, release = adsr
    return apply_adsr(samples, sample_rate, attack, decay, sustain_level, release)


def mix(*tracks: List[float]) -> List[float]:
    length = max((len(t) for t in tracks), default=0)
    out = [0.0] * length
    for track in tracks:
        for i, s in enumerate(track):
            out[i] += s
    return out


def silence(duration: float, sample_rate: int = SAMPLE_RATE) -> List[float]:
    return [0.0] * int(duration * sample_rate)
