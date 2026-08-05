# raft

A from-scratch implementation of Raft — leader election and log
replication (no snapshotting, no cluster membership changes) — plus a
deterministic discrete-event network simulator that can drop messages,
delay/reorder them, partition the cluster, and crash/recover nodes.

```bash
python3 main.py --seed 3
# -- electing an initial leader --
# t= 1001  leader=3
# -- partitioning the cluster (2 nodes | 3 nodes) --
# t= 3253  leader=3  (only the 3-node majority side can elect/commit)
# -- crashing the leader (node 1) --
# -- final state (crashed nodes excluded) --
#   node 3 [leader    ] commit=6 applied=['SET x=0', ..., 'SET x=post-crash']
#   (every surviving node's applied list matches exactly)
```

## The correctness proof: adversarial fault injection

`kvstore` proves durability by literally corrupting a log file and
checking recovery. This thing's failure modes are different — not "does
a single node survive a crash" but "does the *cluster* keep agreeing
with itself while nodes crash, the network drops messages, and it
splits into partitions that can't talk to each other" — so the proof has
to be different too: `tests/test_safety_properties.py` runs the cluster
through randomized combinations of message loss, reordering, network
partitions, and leader crashes (120 parametrized trials), and after
*every* injected fault, checks three of the safety properties from the
Raft paper's Figure 3 directly against live cluster state:

- **Election Safety** — at most one leader can ever be elected for a
  given term. Checked via a running history of every `become_leader()`
  call, not a snapshot of `.role` fields (a node that lost leadership
  still shows `FOLLOWER` by the time a test looks at it, so a snapshot
  alone could never catch a transient double-leadership bug even if one
  existed).
- **Log Matching** — if two nodes' logs contain an entry with the same
  index *and* term, every entry before that index is identical between
  them. Checked for every pair of nodes.
- **State Machine Safety** — if two nodes have each applied an entry at
  a given index, it's the same entry. Equivalently: one node's applied
  command sequence is always a prefix of the other's.

Plus the property that actually matters to a client: once a command is
confirmed committed (present in a leader's applied state machine), it
must survive every subsequent leader crash and still show up in every
surviving node's state machine, checked directly in
`test_random_leader_crashes_preserve_all_safety_properties_and_committed_entries_survive`.

## Two real protocol bugs, both single-node-cluster edge cases

Both were caught by the very first, non-adversarial scenario test
(`test_cluster_basic.py`) — before fault injection ever entered the
picture, which is exactly why this repo builds proof suites bottom-up
instead of jumping straight to the hardest case:

1. **A single-node cluster never elected a leader.** `become_leader()`
   was only ever triggered from the `RequestVoteReply` handler — but
   with zero peers, no `RequestVote` is ever sent, so no reply ever
   arrives, so a one-node "majority" of 1 (its own vote) was never
   actually checked. Fixed in `RaftNode.start_election()`: check for an
   immediate self-vote majority before returning.

2. **After fixing #1, a single-node cluster still never committed
   anything.** The exact same shape of bug one level up: commit-index
   advancement lived only in the `AppendEntriesReply` handler, so with
   no peers to reply, `client_append()` could add to the leader's own
   log forever without `commit_index` ever moving. Fixed by factoring
   the majority-check into `_try_advance_commit_index()` and calling it
   from `client_append()` directly, not only from the reply handler.

## A test bug, not a protocol bug

The first version of the "committed entries survive crashes" test
tracked *every* command that `client_append()` accepted (returned
`True` for) and asserted it must survive any later crash. That's not
what Raft actually guarantees — `client_append()` returning `True` only
means the leader appended the command to its *own* log, not that a
majority has it yet. An entry that's appended but hasn't yet replicated
anywhere else is legitimately allowed to be lost if that leader crashes
before replicating it. 17 of 30 trials in that test "failed" against
this too-strong assertion before the test itself was corrected to only
require durability for commands actually confirmed present in a
leader's applied state machine (i.e., actually committed) before the
crash — the same "the test was wrong, not the code" shape as
`difftool`'s minimality check against `difflib`.

## Architecture

```
raft/
  messages.py    RequestVote/Reply, AppendEntries/Reply -- straight
                    out of the paper's Figure 2, plus the extended
                    thesis's conflict_index fast-backup optimization
  node.py          RaftNode: pure state-machine logic, no clock or
                     network -- given a message, returns a reply (or,
                     for elections, the message to broadcast) and
                     mutates only its own state
  network.py         Network: a fault-injection *policy* (drop / delay
                       / partition), no event queue of its own
  cluster.py           Cluster: the discrete-event simulation loop that
                         actually owns time, wires nodes to the network,
                         and drives elections/heartbeats/replication
```

## What's supported

Leader election (randomized timeouts, split-vote handling), log
replication with the paper's conflict-index fast-backup optimization,
the Figure 8 same-term commit rule, and a network simulator with
message loss/delay/reordering, partitions, and node crash/recovery.
**Not supported**: log compaction/snapshotting, cluster membership
changes (adding/removing nodes), persistence to disk (a "crash" here
means the process stops running, not that its in-memory log is
corrupted or lost — `kvstore`'s WAL is the thing in this collection
that's actually about surviving *disk*-level failure).

## Usage

```bash
python3 main.py --seed 3 --drop-probability 0.15
```

Or as a library:

```python
import random
from raft import Cluster, Network

rng = random.Random(0)
net = Network(rng, drop_probability=0.1)
cluster = Cluster([1, 2, 3, 4, 5], net, rng)
cluster.run_until(1000)          # let an initial election happen
cluster.client_append("SET x=1")
cluster.run_until(cluster.now + 500)
cluster.nodes[1].state_machine   # ['SET x=1'], once replicated
```

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

167 tests: `RaftNode`'s RPC handlers in isolation with hand-constructed
messages (elections, vote-granting rules, log conflict resolution, the
Figure 8 same-term commit rule), the `Network` fault-injection policy,
basic cluster scenarios (clean election, in-order replication, a
single-node cluster), and the 120-trial randomized fault-injection
safety-property suite described above.

## Possible expansions

- Log compaction / snapshotting (the log grows forever right now)
- Cluster membership changes (the paper's joint-consensus approach)
- A Jepsen-style linearizability checker over the client-visible
  command sequence, instead of checking Raft's own internal invariants
  directly
