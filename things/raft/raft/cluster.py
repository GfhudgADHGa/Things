"""Drives a group of RaftNodes through a deterministic discrete-event
simulation: a min-heap of (time, sequence, kind, payload) events, popped
in strictly increasing time order. Given the same rng seed, network
fault schedule, and sequence of client_append calls, a run is perfectly
reproducible -- which is what makes randomized fault-injection testing
(tests/test_safety_properties.py) actually debuggable when it finds
something.

Timers use lazy invalidation instead of a "cancel event" API: resetting
a node's election deadline just records the new deadline and pushes a
fresh heap entry; when a *stale* timer event is eventually popped, its
payload no longer matches the node's current deadline, so it's a no-op.
Same idea for heartbeats, keyed by (node_id, term) instead of a raw
deadline, since a leader's heartbeat schedule is only valid for as long
as it's still the leader of that exact term.
"""
from __future__ import annotations

import heapq
import itertools
import random
from typing import Dict, List, Optional

from .messages import AppendEntries, AppendEntriesReply, RequestVote, RequestVoteReply
from .network import Network
from .node import RaftNode, Role

ELECTION_TIMEOUT_MIN = 150
ELECTION_TIMEOUT_MAX = 300
HEARTBEAT_INTERVAL = 50


class Cluster:
    def __init__(self, node_ids: List[int], network: Network, rng: random.Random):
        self.nodes: Dict[int, RaftNode] = {
            nid: RaftNode(nid, [p for p in node_ids if p != nid]) for nid in node_ids
        }
        self.network = network
        self.rng = rng
        self.now = 0
        self._heap: list = []
        self._counter = itertools.count()
        self._election_deadline: Dict[int, int] = {}
        self.crashed: set = set()
        # term -> list of node_ids that ever won that term's election, in
        # the order they won it. A single election-safety violation would
        # show up as some term mapping to more than one node_id -- this
        # is tracked continuously (not read off a final role snapshot)
        # because a node's .role field is a live, mutable field: a node
        # that lost leadership by stepping down still shows FOLLOWER by
        # the time a test looks at it, so a snapshot alone could never
        # catch a transient double-leadership bug even if one existed.
        self.leader_history: Dict[int, List[int]] = {}

        for nid in node_ids:
            self._reset_election_timer(nid)

    # ---- fault injection ----

    def crash(self, node_id: int) -> None:
        """Simulates a crash-stop failure: the node stops processing
        timers and messages entirely. Its in-memory state (term, vote,
        log) is left untouched, modeling a crash-recovery fault model
        with stable storage -- not a disk failure -- since that's the
        fault Raft itself is designed to tolerate; disk corruption is
        kvstore's territory, not this one's."""
        self.crashed.add(node_id)

    def recover(self, node_id: int) -> None:
        self.crashed.discard(node_id)
        self._reset_election_timer(node_id)  # no timer was live while crashed; arm a fresh one

    # ---- scheduling ----

    def _reset_election_timer(self, node_id: int) -> None:
        deadline = self.now + self.rng.randint(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)
        self._election_deadline[node_id] = deadline
        heapq.heappush(self._heap, (deadline, next(self._counter), "election_timeout", (node_id, deadline)))

    def _schedule_heartbeat(self, node_id: int, term: int) -> None:
        deadline = self.now + HEARTBEAT_INTERVAL
        heapq.heappush(self._heap, (deadline, next(self._counter), "heartbeat", (node_id, term)))

    def _send(self, sender_id: int, receiver_id: int, message: object) -> None:
        if sender_id in self.crashed or receiver_id in self.crashed:
            return
        delay = self.network.transmit_delay_or_none(sender_id, receiver_id)
        if delay is None:
            return
        heapq.heappush(
            self._heap, (self.now + delay, next(self._counter), "deliver", (sender_id, receiver_id, message))
        )

    def _broadcast_append_entries(self, node_id: int) -> None:
        node = self.nodes[node_id]
        for peer in node.peer_ids:
            self._send(node_id, peer, node.make_append_entries_for(peer))

    # ---- simulation loop ----

    def step(self) -> bool:
        """Processes exactly one event. Returns False if the event queue
        is empty (shouldn't happen in practice: elections and heartbeats
        keep rescheduling themselves)."""
        if not self._heap:
            return False
        time, _, kind, payload = heapq.heappop(self._heap)
        self.now = time

        if kind == "election_timeout":
            self._on_election_timeout(*payload)
        elif kind == "heartbeat":
            self._on_heartbeat_tick(*payload)
        elif kind == "deliver":
            self._deliver(*payload)
        return True

    def run_until(self, end_time: int) -> None:
        while self._heap and self.now < end_time:
            self.step()

    def run_steps(self, count: int) -> None:
        for _ in range(count):
            if not self.step():
                break

    def _on_election_timeout(self, node_id: int, deadline: int) -> None:
        if self._election_deadline.get(node_id) != deadline:
            return  # a newer timer already superseded this one
        if node_id in self.crashed:
            return  # no reschedule either: recover() re-arms explicitly
        node = self.nodes[node_id]
        if node.role == Role.LEADER:
            return  # leaders never time out into an election
        msg = node.start_election()
        if node.role == Role.LEADER:
            # Self-vote alone reached quorum (single-node cluster) --
            # start_election() already promoted it; there's no one to
            # send RequestVote to, so go straight to heartbeating.
            self.leader_history.setdefault(node.current_term, []).append(node.node_id)
            self._broadcast_append_entries(node_id)
            self._schedule_heartbeat(node_id, node.current_term)
            return
        self._reset_election_timer(node_id)  # so a split election retries on its own
        for peer in node.peer_ids:
            self._send(node_id, peer, msg)

    def _on_heartbeat_tick(self, node_id: int, term: int) -> None:
        if node_id in self.crashed:
            return  # no reschedule: a recovered ex-leader isn't leader anymore anyway
        node = self.nodes[node_id]
        if node.role != Role.LEADER or node.current_term != term:
            return  # stale generation: no longer leader of that term
        self._broadcast_append_entries(node_id)
        self._schedule_heartbeat(node_id, term)

    def _deliver(self, sender_id: int, receiver_id: int, message: object) -> None:
        if receiver_id in self.crashed:
            return  # the process isn't running to receive it
        node = self.nodes[receiver_id]

        if isinstance(message, RequestVote):
            reply = node.handle_request_vote(message)
            if reply.vote_granted:
                self._reset_election_timer(receiver_id)
            self._send(receiver_id, sender_id, reply)

        elif isinstance(message, RequestVoteReply):
            became_leader = node.handle_request_vote_reply(message)
            if became_leader:
                self.leader_history.setdefault(node.current_term, []).append(node.node_id)
                self._broadcast_append_entries(receiver_id)
                self._schedule_heartbeat(receiver_id, node.current_term)

        elif isinstance(message, AppendEntries):
            heard_from_current_or_newer_leader = message.term >= node.current_term
            reply = node.handle_append_entries(message)
            if heard_from_current_or_newer_leader:
                self._reset_election_timer(receiver_id)
            self._send(receiver_id, sender_id, reply)

        elif isinstance(message, AppendEntriesReply):
            node.handle_append_entries_reply(message)

    # ---- test/client convenience ----

    def leader(self) -> Optional[RaftNode]:
        # Excluding crashed nodes matters: a crashed node's .role field is
        # frozen at whatever it was the instant it crashed (crash() is a
        # simulation-level flag, not a state transition the node itself
        # makes), so a node that crashed while leader would otherwise
        # keep looking like "the leader" externally forever.
        leaders = [n for n in self.nodes.values() if n.role == Role.LEADER and n.node_id not in self.crashed]
        return leaders[0] if len(leaders) == 1 else None

    def leaders_by_term(self) -> Dict[int, List[int]]:
        result: Dict[int, List[int]] = {}
        for n in self.nodes.values():
            if n.role == Role.LEADER and n.node_id not in self.crashed:
                result.setdefault(n.current_term, []).append(n.node_id)
        return result

    def client_append(self, command: object) -> bool:
        """Appends to whichever node is currently the (unique) leader,
        and immediately broadcasts it rather than waiting for the next
        heartbeat tick -- purely a test-speed convenience, not part of
        the protocol itself."""
        leader = self.leader()
        if leader is None:
            return False
        if not leader.client_append(command):
            return False
        self._broadcast_append_entries(leader.node_id)
        return True
