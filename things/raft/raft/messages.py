"""RPC message types, straight out of the Raft paper (Figure 2). Reply
messages carry the responder's own id (`voter_id`/`follower_id`) since
the network simulator delivers messages asynchronously -- a node can't
just remember "who am I currently talking to" the way a synchronous RPC
call would let it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

# A log entry is (term, command). command is an opaque value from Raft's
# point of view -- this implementation doesn't interpret it, just
# replicates and orders it.
LogEntry = Tuple[int, object]


@dataclass(frozen=True)
class RequestVote:
    term: int
    candidate_id: int
    last_log_index: int
    last_log_term: int


@dataclass(frozen=True)
class RequestVoteReply:
    term: int
    vote_granted: bool
    voter_id: int


@dataclass(frozen=True)
class AppendEntries:
    term: int
    leader_id: int
    prev_log_index: int
    prev_log_term: int
    entries: Tuple[LogEntry, ...]
    leader_commit: int


@dataclass(frozen=True)
class AppendEntriesReply:
    term: int
    success: bool
    follower_id: int
    # The paper's "optimistic" implementations often let this drive
    # next_index/match_index directly instead of decrementing by one per
    # rejected AppendEntries -- match_index on success, or a conflict
    # hint on failure -- which is what keeps convergence fast after a
    # partition heals instead of retrying one entry at a time.
    match_index: int = 0
    conflict_index: int = 0
