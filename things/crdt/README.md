# crdt

Four Conflict-free Replicated Data Types, built from scratch:
`GCounter` (grow-only counter), `PNCounter` (increment/decrement
counter), `ORSet` (an add-wins observed-remove set), and `LWWRegister`
(last-writer-wins). Each has a `merge(other)` that combines two
replicas' state into one.

```bash
python3 main.py
# -- ORSet: two shopping-list replicas edited offline --
#    home added milk+eggs; work added milk then removed it (without seeing home's add)
#    merged list: ['eggs', 'milk']  (add-wins: milk survives)
```

## The opposite philosophy from `raft`

`raft` elsewhere in this collection gets replicas to agree by electing a
leader and requiring a majority quorum before anything commits — strong
consistency, but no progress at all during a network partition that
splits the cluster below quorum. CRDTs take the opposite bet: give up on
a single global order of operations, and instead design `merge()` so
that *no coordination is ever required* — any two replicas can merge in
any order, any number of times, after being apart for any length of
time, and are mathematically guaranteed to converge to the same state
once they've all seen the same updates. No leader, no quorum, no
partition-tolerance tradeoff to reason about — the tradeoff moves
somewhere else instead (see "What's given up," below).

## The correctness proof: three algebraic laws, then real convergence

A merge function is safe under arbitrary network conditions — out-of-
order delivery, duplicate delivery, partial connectivity, anything —
if and only if it's a **commutative, associative, idempotent**
(join-)semilattice operation. Those three laws are exactly what's
checked, per type, across 100 randomized trials each:

- **Commutative**: `a.merge(b) == b.merge(a)`
- **Associative**: `a.merge(b).merge(c) == a.merge(b.merge(c))`
- **Idempotent**: `a.merge(a) == a`

All three are checked at the level of full internal `state()`, not just
the externally-visible `value()` — a stronger, more meaningful
guarantee, since state-equality implies value-equality but not the
reverse.

Then, because those three laws being individually true doesn't *by
itself* prove a real multi-replica system converges (it proves merge is
well-behaved pairwise; convergence is the emergent claim), each type
also gets an end-to-end simulation: several replicas apply random local
operations, then gossip by merging random pairs in random order — with
repeats, i.e. duplicate merges — for dozens of rounds, simulating an
unreliable, out-of-order network directly. That's the actual real-world
guarantee a CRDT is for.

## Two design subtleties, caught before they shipped

**`ORSet`'s "add-wins" semantics are a specific, deliberate choice, not
an accident.** Each `add()` tags that individual add with a fresh,
globally-unique tag; `remove()` only ever tombstones the tags it has
actually observed for that element. That means a concurrent add and
remove of the same element resolves to *present*: the remover's
tombstone can't cover a tag it never saw. (A "remove-wins" set is also
a valid, different CRDT — this one just isn't it.)

**`LWWRegister` needs to track *who wrote the current value*
separately from *which local replica this object is*.** An early design
built `merge()`'s result as `LWWRegister(self.replica_id, winner.value,
winner.timestamp)` — reasonable-looking, and wrong: whenever `other`'s
value won the merge, that line silently discarded whose write actually
won, corrupting the tiebreaker for every merge after that one. Caught
while reasoning through the design, before it was ever a failing test —
`test_lww_register.py`'s
`test_three_way_merge_preserves_the_correct_writer_through_an_intermediate_hop`
exists specifically to pin down the exact scenario (a three-way merge
where the winning value passes through an intermediate hop) that would
have caught it if it *had* shipped.

## What's given up

Strong consistency and a single global order of operations. `GCounter`
can only count up — decrements need `PNCounter`'s two-sided trick.
`ORSet` never actually deletes a removed element's tombstones (a real
system needs periodic garbage collection once it's safe to assume every
replica has seen a given remove — not implemented here). And CRDTs
answer "what's the state once everyone's seen everything," not "what
happened first" — there's no analog of `raft`'s linearizable log here,
by design.

## Architecture

```
crdt/
  g_counter.py      GCounter: per-replica counts, merge = element-wise max
  pn_counter.py        PNCounter: two GCounters (positive, negative)
  or_set.py               ORSet: tagged adds + observed tombstones,
                            add-wins on concurrent add/remove
  lww_register.py            LWWRegister: (value, timestamp, writer_id),
                               merge = keep the (timestamp, writer_id) max
```

## Usage

```python
from crdt import GCounter, PNCounter, ORSet, LWWRegister

a, b = GCounter("replica-a"), GCounter("replica-b")
a.increment(3)
b.increment(5)
a.merge(b).value()  # 8, regardless of which replica initiates the merge
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

1417 tests: basic operation semantics per type (including the add-wins
and writer-id-tracking scenarios described above), the three algebraic
laws checked across 100 randomized trials per type, and a 50-trial
random-gossip convergence simulation per type.

## Possible expansions

- Delta-state CRDTs (ship only what changed since the last sync, not
  the full state every time) — a real bandwidth concern this
  state-based approach ignores entirely
- Garbage collection for `ORSet`'s tombstones, once causal stability
  (every replica has seen a given remove) can be established
- A CRDT map/JSON-document type composing the primitives here per-key
- An actual gossip *transport* (network.py-style, borrowing the idea
  from `raft`'s fault-injection simulator) instead of directly calling
  `.merge()` in tests
