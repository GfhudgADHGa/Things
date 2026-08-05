# huffman

A general-purpose file compressor built on Huffman coding, from scratch:
tree construction, a bit-packed custom file format, and a CLI. No
`zlib`, no `gzip` — just `struct` and a min-heap.

```bash
python3 main.py compress somefile.txt        # -> somefile.txt.huf
python3 main.py decompress somefile.txt.huf  # -> somefile.txt
```

Real numbers, not just claimed ones: compressing this repo's
`things/chess/README.md` (7,048 bytes of English prose and Markdown)
produces a 4,627-byte file — **65.6%** of the original, and it
round-trips back to the original byte-for-byte.

## How it works

**The idea**: characters that appear more often get shorter bit-codes,
characters that appear rarely get longer ones, and — the part that makes
this decodable at all — no code is ever a prefix of another, so a decoder
can walk bit-by-bit and know unambiguously when one code ends and the
next begins, without any separators.

**Building the tree** (`tree.py`): count how often each byte value
appears, then repeatedly pull the two least-frequent nodes off a min-heap
and merge them into a new internal node (frequency = the sum), until one
node remains. Walking that final tree from the root, each left branch
appends a `0` and each right branch a `1` — the path to a leaf *is* that
symbol's code. Frequent symbols end up near the root (short codes);
rare ones end up deep (long codes). This is the standard greedy
construction, and it's provably optimal among prefix codes for a known
frequency distribution.

**The file format** (`format.py`): a compressed file doesn't store the
tree structure directly — it stores the frequency table (`symbol -> count`
for each distinct byte present), and the decoder rebuilds the *identical*
tree from that table using the same deterministic construction. Then:
magic bytes, original length (so the decoder knows exactly how many
symbols to expect and can ignore the padding bits at the end of the last
byte), the frequency table, and the bit-packed payload.

**A real edge case, not an afterthought**: a file containing only one
distinct byte value (`bytes([7]) * 10_000_000`, say) has no real Huffman
code at all — with only one symbol, you need zero bits to identify it,
since there's nothing to distinguish it *from*. The tree degenerates to
a single leaf with no root-to-leaf path. The format handles this
directly: the original-length field already tells the decoder how many
copies of that one symbol to emit, so the payload is empty regardless of
how large the file is. `test_single_symbol_needs_no_payload_bits` checks
exactly this — compressing 100 repeats and 10 million repeats of the same
byte produces identically-sized output.

## Usage

```bash
python3 main.py compress input.bin -o output.huf
python3 main.py decompress output.huf -o restored.bin
```

Compression ratio depends entirely on how skewed the input's byte
frequencies are. Highly repetitive data compresses well; the frequency
table itself is a fixed ~5 bytes per distinct byte value (up to 256 × 5 =
1,280 bytes worst case), so **very small or high-entropy files can come
out *larger*** than the input — true of every Huffman-based compressor,
and worth knowing rather than hiding: compressing a 68-byte test file
produces a 161-byte `.huf` file in this repo's own test run, because the
header overhead swamps such a small payload.

## Architecture

```
huffman/
  tree.py       build_tree() / build_code_table(): frequencies -> Huffman
                  tree -> symbol -> bitstring code map
  bitio.py        BitWriter / BitReader: pack/unpack individual bits
                    into bytes, MSB-first
  format.py        the compressed file format: header + frequency table
                    + bit-packed payload
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

39 tests: tree construction (determinism given the same frequencies,
every code is prefix-free, more frequent symbols get shorter-or-equal
codes, all 256 byte values get distinct codes), bit-level I/O
round-tripping, and format round-tripping across edge cases (empty
input, a single byte, all 256 byte values, random binary data, skewed
text, and a parametrized sweep of sizes from 0 to 1000 bytes including
values just above/below byte boundaries) plus the single-symbol
zero-payload case described above.

## Possible expansions

- Adaptive/dynamic Huffman coding (build the tree incrementally as data
  streams in, instead of requiring two passes and a stored frequency
  table)
- Combine with a dictionary-based pass (LZ77-style) for an actual
  general-purpose compressor competitive with `gzip` — Huffman alone only
  exploits skewed byte *frequency*, not repeated *sequences*
