# procmusic

Algorithmic music generation, entirely from scratch: raw waveform
synthesis, a hand-rolled `.wav` file writer, and a small composer that
turns a key/scale/chord-progression into an actual playable song. No
audio libraries — just `struct`, `math`, and `random`.

```bash
python3 main.py --preset calm --output song.wav
```

Listen to the examples in [`examples/`](examples/) — `calm.wav`,
`upbeat.wav`, `melancholy.wav`, `bluesy.wav` — each generated with a
different key, scale, and chord progression.

## How a song gets made

**Theory** (`theory.py`): note names map to frequencies via 12-tone equal
temperament (`440 * 2^((midi-69)/12)`, same math every piano tuner uses).
Scales and chords are just semitone-offset patterns from a root — e.g.
major is `[0,2,4,5,7,9,11]`, a major triad is `[0,4,7]`.

**Synthesis** (`synth.py`): four oscillators (sine, square, sawtooth,
triangle) generate raw sample buffers by phase-accumulation, and an ADSR
envelope (attack/decay/sustain/release) shapes each note's amplitude over
time so notes don't click on/off abruptly.

**Composition** (`composer.py`): given a chord progression written in
roman numerals (`I`, `V`, `vi`, `IV`, ...), diatonic harmony rules pick
each chord's quality (I/IV/V are major, ii/iii/vi are minor, vii is
diminished — the standard major-key convention), then four layers get
rendered and mixed:
- a **bass** note (the chord root, an octave down, triangle wave)
- a **chord pad** (soft sustained sine tones under everything)
- a **melody**: a random walk through the current scale, biased toward
  small steps (favoring stepwise motion, since that's how real melodies
  mostly move) rather than large random jumps
- a **drum track** (`drums.py`, on by default) — see below

**Drums** (`drums.py`): three synthesized percussion sounds, each built
the same first-principles way as the pitched oscillators, no samples
involved. A **kick** is a sine wave whose frequency sweeps from ~150Hz
down to ~45Hz under a fast exponential decay — the standard cheap way to
fake a kick drum. A **snare** blends a short 180Hz tone with white noise
under a similar decay. A **hi-hat** is white noise pushed through the
simplest possible highpass filter (`y[n] = x[n] - x[n-1]`) under a very
fast decay, which strips out the low-frequency content and leaves a
thin, bright tick. All three trigger from a 16th-note step pattern
(`"x...x...x...x..."`-style strings for kick/snare/hi-hat), and the
default pattern is a plain kick-on-1-and-3, snare-on-2-and-4, hi-hat-on-
every-8th-note beat, generated to fit whatever `beats_per_chord` you
give `compose()` rather than being hardcoded to 4/4.

It sounds coherent not because there's anything clever about the melody
generator, but because every note comes from one diatonic scale and every
chord is built from that same scale's degrees — real music theory doing
the heavy lifting, with just a random walk on top for melodic variety.

**WAV output** (`wav.py`): writes the RIFF/WAVE header and 16-bit PCM
samples by hand per the format spec — same approach as the raytracer's
PNG fallback writer elsewhere in this repo.

## Usage

```bash
python3 main.py --preset upbeat --seed 7 --repeats 4 --output song.wav
```

| Flag | Meaning |
|---|---|
| `--preset` | `calm`, `upbeat`, `melancholy`, or `bluesy` (key/scale/progression/tempo) |
| `--seed` | melody RNG seed, for reproducible output |
| `--repeats` | how many times to loop the chord progression |
| `--no-drums` | disable the drum track |
| `--output` | output `.wav` path |

Or use it as a library directly:

```python
from procmusic import compose, write_wav

samples = compose(
    key="E3", scale_name="blues",
    progression=("I", "IV", "I", "V"),
    tempo_bpm=95, seed=42,
    drums=True,  # the default; pass drum_pattern=(kick, snare, hihat) for a custom beat
)
write_wav(samples, "blues.wav")
```

## Architecture

```
procmusic/
  wav.py         RIFF/WAVE PCM reader + writer (stdlib struct only)
  synth.py         oscillators, ADSR envelope, mixing
  drums.py           kick/snare/hi-hat synthesis + step-pattern rendering
  theory.py             note names <-> frequencies, scales, chords
  composer.py             compose(): bass + chords + melody + drums ->
                            one audio buffer
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

74 tests: WAV round-tripping (including clamping and empty-file edge
cases), music theory (known reference frequencies, enharmonic
equivalence, scale/chord construction), oscillator correctness — verified
by counting zero-crossings to estimate each waveform's actual frequency,
rather than trusting the phase-accumulation math by inspection — ADSR
envelope shape, drums (the kick's frequency sweep verified the same
zero-crossing way, the highpass filter checked against its own
closed-form property — a constant signal must highpass to exactly zero
after the first sample — pattern-to-buffer alignment, and determinism
given a seed), and composition (determinism given a seed, duration
matches the requested tempo/progression, amplitude stays within safe
bounds with drums layered in).

## Possible expansions

- Real instrument timbres (additive/FM synthesis with harmonics, not just
  a single oscillator per note)
- A proper voice-leading algorithm for the chord pad instead of root
  position triads
- Non-diatonic scales' chord qualities (currently only the major scale's
  chord-quality table is used; other scales default to major triads
  everywhere, which is a simplification worth fixing)
- More drum sounds (open/closed hi-hat distinction, toms, claps) and
  pattern variation across repeats instead of the same loop every bar
