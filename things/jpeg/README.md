# jpeg

A baseline JPEG encoder from scratch: RGB → YCbCr, 8×8 block DCT,
standard quantization tables, zigzag reordering, run-length + Huffman
entropy coding, and a real JFIF file wrapper (SOI/APP0/DQT/SOF0/DHT/SOS/EOI)
— readable by any standard JPEG decoder. No chroma subsampling (4:4:4),
which keeps the MCU bookkeeping simple at the cost of a somewhat larger
file than a real encoder's default 4:2:0 would produce.

```bash
python3 main.py photo.png -o photo.jpg -q 80
#  256x192, quality=80
#    raw:  147,456 bytes
#    jpeg: 5,711 bytes (3.9% of raw)
#    PSNR: 46.76 dB
```

| quality 80 | quality 20 |
|---|---|
| 5,711 bytes, 46.8 dB | 2,787 bytes, 35.6 dB |

## The correctness proof, in two parts

**Part 1 — a hand-derived closed form for the DCT itself.** For a
spatially *constant* 8×8 block (every pixel the same value `c`), the
definition of the DCT-II gives an exact answer without needing to trust
any implementation at all: `sum_{n=0}^{7} cos((2n+1)k*pi/16) == 0` for
every frequency `k` in 1..7 (the same orthogonality property that makes
the DCT basis a basis), so every AC coefficient must be exactly zero and
the DC coefficient must be exactly `8c`. `tests/test_dct.py` checks this
along with two other closed-form properties — linearity, and that this
particular 0.5·C(k) normalization makes the transform exactly
energy-preserving (Parseval, with a preservation ratio of precisely 1.0,
not some DCT-flavor-specific fudge factor). None of this depends on
JPEG, Pillow, or any other DCT implementation — it's math checked against
math.

**Part 2 — Pillow as an independent whole-pipeline oracle**, the same
pattern as `physics2d`'s GIF encoder checked against Pillow's GIF
decoder. The DCT being individually correct doesn't guarantee the
*file* is well-formed: quantization tables have to be written in zigzag
order in the `DQT` segment, Huffman tables have to satisfy the JPEG
canonicalization procedure with no all-ones codes, byte-stuffing has to
escape every literal `0xFF` in the entropy stream, and dozens of other
small format details all have to line up. `tests/test_encoder_oracle.py`
feeds every produced file through `PIL.Image.open()` and requires it to
decode without error, at sizes both aligned and *not* aligned to the 8×8
block grid (`13×7`, `1×1`, `33×65`, ...), across 20 randomized
width/height/quality trials. Beyond "does it open," PSNR against the
known original is measured directly and required to rise monotonically
with quality — and a spatially-constant block is checked to round-trip
back to within a few intensity levels of the original color, exactly as
the Part 1 closed form predicts (DC-only coefficients means quantization
error is the *only* possible source of error for that block).

Unusually for this collection: nothing was actually broken on the first
real Pillow test. The two-part approach here — validating the DCT
against hand-derived math *before* ever touching the file format, plus
`assert`-ing the zigzag table and every Huffman table's structural
invariants (all 64 positions covered exactly once; `BITS` total matches
`HUFFVAL` count; no all-ones codes) right at import time — front-loaded
the kind of transcription mistakes that would otherwise have only shown
up as "Pillow refuses to open the file," the way physics2d's GIF bug
did. The honest lesson from that thing carried forward into building
this one differently, not just into writing more tests after the fact.

## Architecture

```
jpeg/
  color.py            RGB -> YCbCr (ITU-R BT.601 / JFIF coefficients)
  dct.py                separable 8x8 forward DCT-II
  quantize.py            standard luminance/chrominance tables + IJG
                           quality-scaling formula
  zigzag.py               the 64-entry zigzag scan order (self-checked
                            at import: covers all 64 positions exactly once)
  huffman_tables.py        the 4 standard JPEG Huffman tables (DC/AC x
                             luma/chroma) + canonical code generation
                             (ITU-T.81 Annex C's exact procedure)
  bitwriter.py               MSB-first bit packing + 0xFF/0x00 byte stuffing
  entropy.py                  DC differential + AC run-length coding
  writer.py                    JFIF marker segments (SOI/APP0/DQT/SOF0/
                                 DHT/SOS/EOI)
  encoder.py                    ties it all together: encode_rgb_image()
```

## What's supported

Baseline (non-progressive) DCT encoding, 8-bit RGB input, quality
1-100, arbitrary image dimensions (edge-replicated padding up to the
next 8×8-block boundary). **Not supported**: chroma subsampling (always
4:4:4), progressive/arithmetic coding, a decoder (this is encode-only —
Pillow, or any other standard JPEG decoder, is the reader), optimized
per-image Huffman tables (always the spec's standard tables, same as
most simple encoders default to).

## Usage

```bash
python3 main.py                       # synthetic demo image -> output.jpg
python3 main.py photo.png -q 90       # from a real image, higher quality
```

Or as a library:

```python
from jpeg import encode_rgb_image

pixels = [[(255, 0, 0)] * 64 for _ in range(64)]  # 64x64 solid red
data = encode_rgb_image(pixels, 64, 64, quality=85)
open("red.jpg", "wb").write(data)
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

74 tests: the DCT's closed-form properties (constant-block, linearity,
Parseval), quantization table scaling and rounding, Huffman canonical
code generation (prefix-free, no all-ones codes, matches the `BITS`
table exactly), bit-packing and byte-stuffing, DC/AC entropy coding
against hand-decoded expected bitstreams, and `test_encoder_oracle.py`'s
Pillow round-trip checks described above.

## Possible expansions

- 4:2:0 chroma subsampling (smaller files, matching what real-world
  encoders default to; would need proper MCU interleaving instead of
  today's 1 block per component per MCU)
- Optimized (per-image) Huffman tables instead of the fixed standard
  ones — a real compression-ratio win, since the standard tables are
  built from average statistics across many photos, not this one
- A matching decoder (IDCT + dequantize + Huffman decode), which would
  let this thing verify itself without depending on Pillow at all
