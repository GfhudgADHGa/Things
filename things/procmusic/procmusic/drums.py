"""Percussion synthesis: no sample playback, just short synthesized
transients built from the same first-principles approach as synth.py's
oscillators -- a pitch-swept sine for the kick, tone plus noise for the
snare, and highpass-filtered noise for the hi-hat -- triggered from a
16th-note step pattern ("x...x...x...x..." style) and mixed into the
rest of the composition.
"""
from __future__ import annotations

import math
import random
from typing import List, Optional

from .wav import SAMPLE_RATE


def _white_noise(num_samples: int, rng: random.Random) -> List[float]:
    return [rng.uniform(-1.0, 1.0) for _ in range(num_samples)]


def _exp_envelope(num_samples: int, sample_rate: int, decay_rate: float) -> List[float]:
    """A percussive amplitude envelope: starts at 1.0 and decays
    exponentially -- decay_rate bigger means a faster, tighter hit."""
    return [math.exp(-decay_rate * i / sample_rate) for i in range(num_samples)]


def _highpass(samples: List[float]) -> List[float]:
    """The simplest possible highpass filter: each output sample is the
    difference from the previous input sample (a single-zero FIR
    filter). That attenuates slowly-varying (low-frequency) content and
    passes fast-varying (high-frequency) content through, which is
    exactly what turns flat white noise into the thin, tinny texture a
    hi-hat needs -- without needing a real filter design."""
    if not samples:
        return []
    return [samples[0]] + [samples[i] - samples[i - 1] for i in range(1, len(samples))]


def kick(
    duration: float = 0.25,
    sample_rate: int = SAMPLE_RATE,
    start_freq: float = 150.0,
    end_freq: float = 45.0,
    amplitude: float = 0.42,
) -> List[float]:
    """A pitch-swept sine, high frequency sweeping down to low, under a
    fast decay -- the standard cheap way to synthesize a kick drum
    without a sampled sound."""
    num_samples = int(sample_rate * duration)
    envelope = _exp_envelope(num_samples, sample_rate, decay_rate=18.0)
    samples = []
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples if num_samples else 0.0
        freq = start_freq + (end_freq - start_freq) * t
        phase += 2 * math.pi * freq / sample_rate
        samples.append(amplitude * math.sin(phase) * envelope[i])
    return samples


def snare(
    duration: float = 0.18,
    sample_rate: int = SAMPLE_RATE,
    rng: Optional[random.Random] = None,
    amplitude: float = 0.3,
) -> List[float]:
    """A blend of a short low tone (the drum shell) and white noise (the
    snare wires), under a fast decay."""
    rng = rng if rng is not None else random.Random()
    num_samples = int(sample_rate * duration)
    envelope = _exp_envelope(num_samples, sample_rate, decay_rate=22.0)
    tone_freq = 180.0
    phase = 0.0
    tone = []
    for _ in range(num_samples):
        phase += 2 * math.pi * tone_freq / sample_rate
        tone.append(math.sin(phase))
    noise = _white_noise(num_samples, rng)
    return [amplitude * (0.4 * tone[i] + 0.6 * noise[i]) * envelope[i] for i in range(num_samples)]


def hihat(
    duration: float = 0.08,
    sample_rate: int = SAMPLE_RATE,
    rng: Optional[random.Random] = None,
    amplitude: float = 0.15,
) -> List[float]:
    """Highpass-filtered noise under a very fast decay -- a short,
    bright tick rather than a low thud."""
    rng = rng if rng is not None else random.Random()
    num_samples = int(sample_rate * duration)
    envelope = _exp_envelope(num_samples, sample_rate, decay_rate=45.0)
    filtered = _highpass(_white_noise(num_samples, rng))
    return [amplitude * filtered[i] * envelope[i] for i in range(num_samples)]


def render_pattern(pattern: str, step_duration: float, sample_rate: int, sound_fn) -> List[float]:
    """pattern: one character per 16th-note step -- 'x' triggers
    sound_fn(), anything else (conventionally '.') is silence. Returns a
    buffer exactly len(pattern) * step_duration seconds long, regardless
    of how long each individual hit's own sound decays to (hits are
    additively overlaid, so a still-decaying hit and the next step's hit
    naturally overlap rather than being cut off)."""
    total_samples = int(sample_rate * step_duration * len(pattern))
    buffer = [0.0] * total_samples
    for step, char in enumerate(pattern):
        if char != "x":
            continue
        hit = sound_fn()
        start = int(round(step * step_duration * sample_rate))
        for i, s in enumerate(hit):
            idx = start + i
            if idx >= total_samples:
                break
            buffer[idx] += s
    return buffer


def render_drum_track(
    kick_pattern: str,
    snare_pattern: str,
    hihat_pattern: str,
    step_duration: float,
    sample_rate: int = SAMPLE_RATE,
    seed: int = 0,
) -> List[float]:
    """The three patterns must all be the same length (one 16th-note
    grid); mismatched lengths raise rather than silently truncating."""
    if not (len(kick_pattern) == len(snare_pattern) == len(hihat_pattern)):
        raise ValueError("kick/snare/hihat patterns must all be the same length")
    rng = random.Random(seed)
    kick_track = render_pattern(kick_pattern, step_duration, sample_rate, lambda: kick(sample_rate=sample_rate))
    snare_track = render_pattern(
        snare_pattern, step_duration, sample_rate, lambda: snare(sample_rate=sample_rate, rng=rng)
    )
    hihat_track = render_pattern(
        hihat_pattern, step_duration, sample_rate, lambda: hihat(sample_rate=sample_rate, rng=rng)
    )
    length = max(len(kick_track), len(snare_track), len(hihat_track))
    out = [0.0] * length
    for track in (kick_track, snare_track, hihat_track):
        for i, s in enumerate(track):
            out[i] += s
    return out
