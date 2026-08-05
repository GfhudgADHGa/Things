# kvstore

A durable key-value store: a write-ahead log where every write is
fsync'd to disk before the call returns, so a crash can never lose a
write that already succeeded — and, just as importantly, a crash *during*
a write can't corrupt the store either. This one is less about a clever
algorithm and more about a systems property: proving the store actually
survives the failure modes it's designed for, not just trusting the
design on paper.

```python
from kvstore import KVStore

with KVStore("mydata.db") as db:
    db.put("name", "Claude")
    db.put("mood", "curious")
    db.get("name")     # "Claude"
    db.delete("mood")
    db.compact()        # shrink the log back down
```

## The durability story

Every write is one **record**: a 4-byte length, a 4-byte CRC32 checksum,
then the payload (op + key + value). `put`/`delete` write the record,
`flush()`, then `os.fsync()` the file descriptor before returning — so by
the time a call returns, the write is physically on disk, not sitting in
an OS buffer that a power loss could erase.

On open, the store replays every record in the log to rebuild its
in-memory index. The interesting part is what happens when the log itself
isn't perfectly well-formed, which is exactly what a crash produces:

- **A torn write** (the process died mid-`write()` of a record): the
  length prefix says the body should be N bytes, but fewer than N bytes
  are actually there.
- **Bit-flip corruption** (a torn write that happened to land on a
  boundary, or genuine disk-level corruption): the bytes are all present,
  but the CRC32 doesn't match.

Either way, `read_valid_records` (`kvstore/record.py`) stops cleanly at
that point — no exception, no guessing — and reports the byte offset of
the last *good* record. `KVStore._recover` then truncates the file back
to that offset, so the garbage is gone and future writes append cleanly
after real data, not after a torn record that might confuse the next
recovery.

This is checked by literally simulating the failure: write real records
with a real `KVStore`, close it, then hand-append a truncated record or
flip a bit in the file with plain file I/O (exactly what a crash or disk
error would leave behind), and assert that reopening the store recovers
every valid record with no exception and no lingering garbage. See
`tests/test_crash_recovery.py`.

## Compaction

Every `put` appends a new record even if the key already exists, so the
log grows forever under repeated writes to the same keys. `compact()`
rewrites it down to just the current value of each live key (dropping
overwritten values and deleted keys entirely). The rewrite itself is
crash-safe: the new log is fully written and `fsync`'d to a **temp
file** first, and only then swapped in with a single `os.replace()` —
which is atomic on POSIX filesystems. A crash at any point before that
one atomic rename leaves the original log completely untouched; there is
no window where the on-disk file is a half-written mix of old and new.
This is verified in `test_crash_mid_compaction_never_loses_the_original_log`
by monkeypatching `os.replace` to raise mid-compaction and asserting the
original file's bytes are unchanged afterward.

## Usage

```bash
python3 main.py --path mydata.db
> put name Claude
ok
> get name
Claude
> keys
name
> compact
compacted: 41 bytes -> 20 bytes
> quit
```

## Architecture

```
kvstore/
  record.py   binary record format + read_valid_records() (the
                crash-tolerant reader that never raises on bad input)
  store.py     KVStore: in-memory index + WAL file, put/get/delete/
                compact, recovery on open
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

33 tests: record encode/decode round-tripping including binary-unsafe
edge cases, every discard path in the reader (truncated header, truncated
body, bad checksum, corruption mid-stream), the store's basic operations
and persistence-across-reopen, compaction (including that it's usable
immediately afterward and survives a second reopen), and the crash
simulations described above.

## Possible expansions

- Concurrent access (currently single-process, no file locking)
- A real index structure (B-tree/LSM) instead of an in-memory dict, so
  the working set isn't bounded by RAM
- Range queries
- Configurable fsync policy (batch writes for throughput, at the cost of
  a small durability window) with a benchmark showing the tradeoff
