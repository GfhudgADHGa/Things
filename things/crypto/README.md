# crypto

From-scratch implementations of three standard cryptographic primitives,
each built directly from its published specification: **SHA-256**
(FIPS 180-4), **HMAC-SHA256** (RFC 2104), and **AES-128 in CBC mode**
with PKCS#7 padding (FIPS-197). Educational, not production — see the
warning below.

```bash
python3 main.py sha256 somefile.txt
python3 main.py encrypt 000102030405060708090a0b0c0d0e0f plain.txt cipher.bin
python3 main.py decrypt 000102030405060708090a0b0c0d0e0f cipher.bin plain_again.txt
```

## ⚠️ Educational only — do not use this to protect real secrets

This code is **not constant-time**: several operations (S-box lookups,
GF(2^8) multiplication, PKCS#7 padding validation) branch or index on
secret data in ways a real cryptographic library carefully avoids,
specifically to prevent timing side-channel attacks that can leak key
material. It also hasn't been reviewed, audited, or hardened against any
of the other implementation attacks real crypto libraries defend
against. It exists to implement the published algorithms correctly and
prove that against real oracles — not to be a safe choice for actually
protecting anything. Use `hashlib`, `hmac`, and `cryptography` (all
already used *as the oracles* below) for real work.

## The correctness proof

**SHA-256 and HMAC-SHA256** are checked bit-for-bit against Python's own
`hashlib`/`hmac` — a live, independent, standard-library oracle — across
the standard NIST test vectors (including the famously slow
one-million-`'a'` vector), every message length that straddles a
padding-block boundary (54 through 65 bytes, 119 through 129 bytes — the
lengths where a hand-transcribed padding routine is most likely to have
an off-by-one), and 300 rounds of randomized fuzzing each. HMAC's key
handling is separately stressed right at the 64-byte block-size boundary
where RFC 2104's "hash the key first if it's longer than one block" rule
kicks in.

**AES-128** has two independent legs of proof. First, FIPS-197
Appendix B's own published single-block test vector — matched exactly,
no external library needed — plus round-trip self-consistency
(`decrypt(encrypt(x)) == x`) across 200 randomized trials. Second, the
`cryptography` package as a live oracle: 200 single-block trials and 100
CBC-mode trials checked **ciphertext-for-ciphertext**, not just "does it
decrypt back to the right thing" (which a self-consistent-but-wrong
implementation — say, a transposed `ShiftRows` — could also achieve by
accident, as long as encrypt and decrypt use the same mistaken
convention). The `cryptography`-oracle tests are skipped, not failed, if
that package isn't importable/working in the current environment; the
FIPS-197 vector and round-trip tests already provide a real,
dependency-free baseline regardless.

Everything matched on the first real run except one thing: a typo while
hand-transcribing the 256-byte AES S-box as three chained
`.replace(" ", "")` calls produced invalid Python syntax outright (a
`SyntaxError`, caught immediately, before any test even ran) rather than
a subtly wrong table. Rewritten as sixteen clean 32-character hex
literals — the values themselves, re-derived by hand row by row and
checked against the original, were correct throughout.

## A design choice worth calling out: derived, not just transcribed

AES's round constants (`Rcon`) are computed from `GF(2^8)` doubling
(`_gf_mul(x, 2)` applied repeatedly, starting from 1) rather than
hardcoded as a second small lookup table. The inverse S-box is
*computed* from the forward S-box (`inv_sbox[sbox[x]] = x`) rather than
transcribed as a second 256-byte table. Both choices mean fewer literal
magic numbers with a chance to be silently wrong — though, as the S-box
notes point out, being self-consistent (inverse-of-itself, or correctly
derived from a starting value) only proves internal consistency, not
that the *starting* values match the real standard. That's exactly why
the `cryptography`-library and FIPS-197 comparisons above check the
actual standard, not just this implementation's own round-trip.

## Architecture

```
crypto/
  sha256.py         FIPS 180-4: message padding, message schedule
                       expansion, the 64-round compression function
  hmac_sha256.py      RFC 2104, built on this package's own sha256()
  aes.py                FIPS-197: S-box, key expansion, the four round
                          transformations, CBC mode + PKCS#7 padding
```

## Usage

```bash
python3 main.py sha256 file.txt
python3 main.py hmac mykey file.txt
python3 main.py encrypt <32-hex-char-key> plain.txt cipher.bin   # random IV, prepended to output
python3 main.py decrypt <32-hex-char-key> cipher.bin plain.txt
```

Or as a library:

```python
from crypto import sha256_hex, hmac_sha256_hex, AES128, cbc_encrypt, cbc_decrypt

sha256_hex(b"hello world")
hmac_sha256_hex(b"key", b"message")

key, iv = bytes(16), bytes(16)
ciphertext = cbc_encrypt(key, iv, b"a secret message")
cbc_decrypt(key, iv, ciphertext)   # b"a secret message"
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

1153 tests: SHA-256 and HMAC against `hashlib`/`hmac` (NIST/RFC vectors,
padding-boundary lengths, key-length-boundary lengths, and hundreds of
fuzz trials each), and AES-128 against FIPS-197's own vector plus the
`cryptography` package (single-block and CBC-mode, ciphertext-exact) —
along with structural tests (wrong key/block/IV lengths raise, tampered
ciphertext doesn't silently "recover" the original, invalid PKCS#7
padding is rejected on decrypt).

## Possible expansions

- AES-192/256 (longer keys, more rounds — the key expansion and round
  structure generalize directly)
- A constant-time S-box lookup (bit-sliced or otherwise) — the actual
  engineering work real AES libraries do that this one deliberately
  skips, exactly because it's out of scope for "implement the algorithm
  correctly," not "implement it safely"
- Authenticated encryption (AES-GCM, or HMAC-then-encrypt) instead of
  plain CBC, which provides confidentiality but no integrity guarantee
  on its own
