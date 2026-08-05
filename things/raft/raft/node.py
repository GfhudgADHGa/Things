"""A single Raft server's state machine (ITU... well, the Raft paper's
Figure 2 and the extended Raft thesis's log-backtracking optimization).
This module is pure logic: it never touches a clock or a socket. Given
an incoming message it returns the reply (or, for elections, the
messages the caller should broadcast) and mutates only its own state --
all the actual message delivery, timing, and fault injection lives in
network.py/cluster.py so the correctness-critical state machine logic
can be tested and reasoned about in complete isolation from timing.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Sequence

from .messages import AppendEntries, AppendEntriesReply, LogEntry, RequestVote, RequestVoteReply


class Role(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class RaftNode:
    def __init__(self, node_id: int, peer_ids: Sequence[int]):
        self.node_id = node_id
        self.peer_ids = list(peer_ids)
        self.all_ids = sorted(set(self.peer_ids) | {node_id})
        self.majority = len(self.all_ids) // 2 + 1

        # "Persistent" state (Figure 2) -- kept in memory here since this
        # thing doesn't model disk persistence; a real implementation
        # fsyncs these three before replying to any RPC.
        self.current_term = 0
        self.voted_for: Optional[int] = None
        self.log: List[LogEntry] = []  # log[i] is Raft index i+1

        # Volatile state, all servers.
        self.commit_index = 0
        self.last_applied = 0
        self.state_machine: List[object] = []

        self.role = Role.FOLLOWER
        self.leader_id: Optional[int] = None
        self.votes_received: set = set()

        # Volatile state, leaders only (reset on every become_leader()).
        self.next_index: Dict[int, int] = {}
        self.match_index: Dict[int, int] = {}

    # ---- log helpers (Raft's log indices are 1-based; index 0 means
    # "before the log starts", with implicit term 0) ----

    def last_log_index(self) -> int:
        return len(self.log)

    def last_log_term(self) -> int:
        return self.term_at(self.last_log_index())

    def term_at(self, index: int) -> int:
        if index <= 0:
            return 0
        return self.log[index - 1][0]

    def _append_entries_to_log(self, prev_log_index: int, entries: Sequence[LogEntry]) -> None:
        for offset, entry in enumerate(entries):
            idx0 = prev_log_index + offset  # 0-based position in self.log
            if idx0 < len(self.log) and self.log[idx0][0] == entry[0]:
                continue  # already present with a matching term -- leave it (paper 5.3)
            # First mismatch or gap: truncate here and append everything
            # remaining fresh. Never touch entries before this point --
            # "leader never overwrites or deletes entries in its own
            # log" plus "an existing entry conflicts... delete the
            # existing entry and all that follow it" together mean this
            # is the *only* place any node's log is ever truncated.
            del self.log[idx0:]
            self.log.extend(entries[offset:])
            return

    def _apply_committed(self) -> None:
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            _term, command = self.log[self.last_applied - 1]
            self.state_machine.append(command)

    def _step_down(self, new_term: int) -> None:
        self.current_term = new_term
        self.role = Role.FOLLOWER
        self.voted_for = None
        self.leader_id = None

    def _candidate_log_is_up_to_date(self, candidate_last_term: int, candidate_last_index: int) -> bool:
        my_term, my_index = self.last_log_term(), self.last_log_index()
        if candidate_last_term != my_term:
            return candidate_last_term > my_term
        return candidate_last_index >= my_index

    # ---- election ----

    def start_election(self) -> RequestVote:
        self.current_term += 1
        self.role = Role.CANDIDATE
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        self.leader_id = None
        if len(self.votes_received) >= self.majority:
            # A self-vote alone already reaches quorum -- only possible
            # in a single-node cluster, but handled generally rather than
            # special-cased: with zero peers, no RequestVote is ever
            # sent, so nothing would otherwise ever trigger
            # become_leader() and the node would wait forever for vote
            # replies from nobody.
            self.become_leader()
        return RequestVote(self.current_term, self.node_id, self.last_log_index(), self.last_log_term())

    def handle_request_vote(self, msg: RequestVote) -> RequestVoteReply:
        if msg.term > self.current_term:
            self._step_down(msg.term)
        if msg.term < self.current_term:
            return RequestVoteReply(self.current_term, False, self.node_id)

        can_vote = self.voted_for is None or self.voted_for == msg.candidate_id
        log_ok = self._candidate_log_is_up_to_date(msg.last_log_term, msg.last_log_index)
        if can_vote and log_ok:
            self.voted_for = msg.candidate_id
            return RequestVoteReply(self.current_term, True, self.node_id)
        return RequestVoteReply(self.current_term, False, self.node_id)

    def handle_request_vote_reply(self, msg: RequestVoteReply) -> bool:
        """Returns True exactly when this reply just won the election, so
        the caller knows to broadcast heartbeats immediately."""
        if msg.term > self.current_term:
            self._step_down(msg.term)
            return False
        if self.role != Role.CANDIDATE or msg.term != self.current_term:
            return False  # stale reply from an earlier term's election
        if msg.vote_granted:
            self.votes_received.add(msg.voter_id)
            if len(self.votes_received) >= self.majority:
                self.become_leader()
                return True
        return False

    def become_leader(self) -> None:
        self.role = Role.LEADER
        self.leader_id = self.node_id
        self.next_index = {p: self.last_log_index() + 1 for p in self.peer_ids}
        self.match_index = {p: 0 for p in self.peer_ids}
        self.match_index[self.node_id] = self.last_log_index()

    # ---- log replication ----

    def client_append(self, command: object) -> bool:
        """Only valid on the leader. Returns whether it was accepted."""
        if self.role != Role.LEADER:
            return False
        self.log.append((self.current_term, command))
        self._try_advance_commit_index()
        return True

    def _try_advance_commit_index(self) -> None:
        """A log entry commits once a majority of match_index values
        reach its index (restricted to the leader's current term -- see
        the long comment in handle_append_entries_reply). This has to be
        checked after *any* event that can change what a majority holds,
        not just after a follower's reply: in a single-node cluster (or
        more generally, whenever the leader's own match_index already
        satisfies quorum on its own), no AppendEntriesReply ever needs
        to arrive at all, so client_append() must trigger this check
        itself rather than only handle_append_entries_reply doing so."""
        self.match_index[self.node_id] = self.last_log_index()
        sorted_match = sorted(self.match_index[i] for i in self.all_ids)
        candidate_n = sorted_match[-self.majority]
        if candidate_n > self.commit_index and self.term_at(candidate_n) == self.current_term:
            self.commit_index = candidate_n
            self._apply_committed()

    def make_append_entries_for(self, peer_id: int) -> AppendEntries:
        next_idx = self.next_index[peer_id]
        prev_log_index = next_idx - 1
        return AppendEntries(
            self.current_term,
            self.node_id,
            prev_log_index,
            self.term_at(prev_log_index),
            tuple(self.log[next_idx - 1:]),
            self.commit_index,
        )

    def handle_append_entries(self, msg: AppendEntries) -> AppendEntriesReply:
        if msg.term > self.current_term:
            self._step_down(msg.term)
        if msg.term < self.current_term:
            return AppendEntriesReply(self.current_term, False, self.node_id)

        # A valid leader for our current (or higher) term: recognize it,
        # and step down even if we were a candidate in this very term
        # (paper 5.2 -- "if AppendEntries received from new leader:
        # convert to follower").
        self.role = Role.FOLLOWER
        self.leader_id = msg.leader_id

        if msg.prev_log_index > self.last_log_index():
            return AppendEntriesReply(
                self.current_term, False, self.node_id, conflict_index=self.last_log_index() + 1
            )
        if msg.prev_log_index > 0 and self.term_at(msg.prev_log_index) != msg.prev_log_term:
            # Fast backup (extended Raft thesis 4.2.1, not just Figure 2):
            # jump next_index back to the start of the conflicting term
            # instead of retrying one index at a time.
            conflict_term = self.term_at(msg.prev_log_index)
            idx = msg.prev_log_index
            while idx > 1 and self.term_at(idx - 1) == conflict_term:
                idx -= 1
            return AppendEntriesReply(self.current_term, False, self.node_id, conflict_index=idx)

        self._append_entries_to_log(msg.prev_log_index, msg.entries)

        if msg.leader_commit > self.commit_index:
            self.commit_index = min(msg.leader_commit, self.last_log_index())
            self._apply_committed()

        return AppendEntriesReply(
            self.current_term, True, self.node_id,
            match_index=msg.prev_log_index + len(msg.entries),
        )

    def handle_append_entries_reply(self, msg: AppendEntriesReply) -> None:
        if msg.term > self.current_term:
            self._step_down(msg.term)
            return
        if self.role != Role.LEADER or msg.term != self.current_term:
            return  # stale reply, or we're no longer leader

        if not msg.success:
            self.next_index[msg.follower_id] = max(1, msg.conflict_index)
            return

        self.next_index[msg.follower_id] = msg.match_index + 1
        self.match_index[msg.follower_id] = msg.match_index

        # Critically (paper 5.4.2, Figure 8), the leader only ever
        # commits by counting replicas for entries from its *own*
        # current term -- committing an earlier-term entry the instant
        # it's replicated (ignoring this rule) is exactly the scenario
        # the paper's Figure 8 counterexample shows can lose a committed
        # entry after a later leader crash. Enforced inside
        # _try_advance_commit_index.
        self._try_advance_commit_index()
