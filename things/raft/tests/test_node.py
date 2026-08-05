"""Unit tests for RaftNode in complete isolation -- hand-constructed
messages, no network or clock involved. These pin down the state
machine's per-RPC-handler logic (Figure 2 of the Raft paper) precisely,
independent of whether the simulation harness wires it up correctly."""
from raft.messages import AppendEntries, AppendEntriesReply, RequestVote, RequestVoteReply
from raft.node import RaftNode, Role


def make_node(node_id=1, peers=(2, 3)):
    return RaftNode(node_id, peers)


# ---- elections ----

def test_start_election_increments_term_and_votes_for_self():
    node = make_node()
    msg = node.start_election()
    assert node.current_term == 1
    assert node.role == Role.CANDIDATE
    assert node.voted_for == node.node_id
    assert msg.term == 1
    assert msg.candidate_id == node.node_id


def test_grants_vote_to_up_to_date_candidate():
    node = make_node()
    reply = node.handle_request_vote(RequestVote(term=1, candidate_id=2, last_log_index=0, last_log_term=0))
    assert reply.vote_granted is True
    assert node.voted_for == 2
    assert node.current_term == 1


def test_refuses_second_vote_in_same_term():
    node = make_node()
    node.handle_request_vote(RequestVote(1, 2, 0, 0))
    reply = node.handle_request_vote(RequestVote(1, 3, 0, 0))
    assert reply.vote_granted is False


def test_grants_repeated_vote_to_same_candidate_in_same_term():
    # A duplicate/retried RequestVote from the same candidate in the same
    # term should still be granted (idempotent), not refused as "already voted".
    node = make_node()
    node.handle_request_vote(RequestVote(1, 2, 0, 0))
    reply = node.handle_request_vote(RequestVote(1, 2, 0, 0))
    assert reply.vote_granted is True


def test_refuses_vote_for_stale_term():
    node = make_node()
    node.current_term = 5
    reply = node.handle_request_vote(RequestVote(term=3, candidate_id=2, last_log_index=0, last_log_term=0))
    assert reply.vote_granted is False
    assert reply.term == 5


def test_steps_down_on_higher_term_vote_request():
    node = make_node()
    node.role = Role.LEADER
    node.current_term = 2
    node.handle_request_vote(RequestVote(term=5, candidate_id=2, last_log_index=0, last_log_term=0))
    assert node.role == Role.FOLLOWER
    assert node.current_term == 5


def test_refuses_vote_when_candidate_log_is_less_up_to_date():
    node = make_node()
    node.log = [(1, "a"), (1, "b")]  # last_log_term=1, last_log_index=2
    reply = node.handle_request_vote(RequestVote(term=1, candidate_id=2, last_log_index=1, last_log_term=1))
    assert reply.vote_granted is False


def test_grants_vote_when_candidate_log_has_higher_term_even_if_shorter():
    node = make_node()
    node.log = [(1, "a"), (1, "b"), (1, "c")]
    reply = node.handle_request_vote(RequestVote(term=2, candidate_id=2, last_log_index=1, last_log_term=2))
    assert reply.vote_granted is True


def test_becomes_leader_after_majority_of_votes():
    node = make_node(1, peers=(2, 3, 4, 5))  # 5-node cluster, majority=3
    node.start_election()
    assert node.handle_request_vote_reply(RequestVoteReply(1, True, 2)) is False
    assert node.handle_request_vote_reply(RequestVoteReply(1, True, 3)) is True
    assert node.role == Role.LEADER


def test_vote_reply_from_stale_term_is_ignored():
    node = make_node(1, peers=(2, 3, 4, 5))
    node.start_election()  # term 1
    node.start_election()  # term 2, abandoning the term-1 election
    became_leader = node.handle_request_vote_reply(RequestVoteReply(1, True, 2))
    assert became_leader is False
    assert node.role == Role.CANDIDATE  # still campaigning for term 2


def test_higher_term_in_vote_reply_steps_candidate_down():
    node = make_node()
    node.start_election()
    node.handle_request_vote_reply(RequestVoteReply(term=9, vote_granted=False, voter_id=2))
    assert node.role == Role.FOLLOWER
    assert node.current_term == 9


# ---- log replication ----

def test_follower_accepts_first_entries_into_empty_log():
    node = make_node()
    node.current_term = 1
    reply = node.handle_append_entries(
        AppendEntries(term=1, leader_id=2, prev_log_index=0, prev_log_term=0, entries=((1, "x"), (1, "y")), leader_commit=0)
    )
    assert reply.success is True
    assert node.log == [(1, "x"), (1, "y")]


def test_follower_rejects_when_prev_log_index_beyond_its_log():
    node = make_node()
    reply = node.handle_append_entries(
        AppendEntries(term=1, leader_id=2, prev_log_index=5, prev_log_term=1, entries=(), leader_commit=0)
    )
    assert reply.success is False
    assert reply.conflict_index == 1  # last_log_index()+1 == 0+1


def test_follower_rejects_and_truncates_on_term_mismatch_at_prev_index():
    node = make_node()
    node.current_term = 3
    node.log = [(1, "a"), (2, "b"), (2, "c")]
    reply = node.handle_append_entries(
        AppendEntries(term=3, leader_id=2, prev_log_index=3, prev_log_term=3, entries=(), leader_commit=0)
    )
    assert reply.success is False
    # fast-backup: should point to the start of the conflicting term (2), not just index-1
    assert reply.conflict_index == 2


def test_conflicting_entry_truncates_the_log():
    node = make_node()
    node.current_term = 2
    node.log = [(1, "a"), (1, "b"), (1, "c")]
    reply = node.handle_append_entries(
        AppendEntries(term=2, leader_id=2, prev_log_index=1, prev_log_term=1, entries=((2, "B"),), leader_commit=0)
    )
    assert reply.success is True
    assert node.log == [(1, "a"), (2, "B")]  # "b" and "c" were discarded


def test_matching_entries_are_left_untouched_not_rewritten():
    node = make_node()
    node.current_term = 1
    node.log = [(1, "a"), (1, "b")]
    original_b_object = node.log[1]
    node.handle_append_entries(
        AppendEntries(term=1, leader_id=2, prev_log_index=0, prev_log_term=0, entries=((1, "a"), (1, "b")), leader_commit=0)
    )
    assert node.log[1] is original_b_object  # untouched, not deleted-and-reappended


def test_leader_commit_advances_follower_commit_index_and_applies():
    node = make_node()
    node.current_term = 1
    node.log = [(1, "a"), (1, "b"), (1, "c")]
    node.handle_append_entries(
        AppendEntries(term=1, leader_id=2, prev_log_index=3, prev_log_term=1, entries=(), leader_commit=2)
    )
    assert node.commit_index == 2
    assert node.state_machine == ["a", "b"]


def test_candidate_steps_down_to_follower_on_append_entries_same_term():
    node = make_node()
    node.role = Role.CANDIDATE
    node.current_term = 1
    node.voted_for = node.node_id
    node.handle_append_entries(
        AppendEntries(term=1, leader_id=2, prev_log_index=0, prev_log_term=0, entries=(), leader_commit=0)
    )
    assert node.role == Role.FOLLOWER
    assert node.leader_id == 2


def test_append_entries_from_stale_term_is_rejected():
    node = make_node()
    node.current_term = 5
    reply = node.handle_append_entries(
        AppendEntries(term=2, leader_id=2, prev_log_index=0, prev_log_term=0, entries=(), leader_commit=0)
    )
    assert reply.success is False
    assert reply.term == 5


# ---- leader-side commit logic ----

def make_leader(peers=(2, 3, 4, 5)):
    node = make_node(1, peers)
    node.current_term = 1
    node.role = Role.LEADER
    node.log = [(1, "x")]
    node.next_index = {p: 2 for p in peers}
    node.match_index = {p: 0 for p in peers}
    node.match_index[1] = 1
    return node


def test_leader_commits_after_majority_match_index_reaches_entry():
    leader = make_leader()
    leader.handle_append_entries_reply(AppendEntriesReply(1, True, 2, match_index=1))
    assert leader.commit_index == 0  # only 2 of 5 (self+2) -- not yet a majority
    leader.handle_append_entries_reply(AppendEntriesReply(1, True, 3, match_index=1))
    assert leader.commit_index == 1  # self+2+3 = 3 of 5, majority reached
    assert leader.state_machine == ["x"]


def test_leader_does_not_commit_earlier_term_entry_by_count_alone():
    # Figure 8 of the Raft paper: an entry from an *older* term must not
    # be considered committed just because a majority now has it -- only
    # once an entry from the leader's *current* term is also replicated
    # to a majority does everything up to and including it commit.
    leader = make_leader()
    leader.current_term = 2
    leader.log = [(1, "old")]  # replicated widely, but from term 1 -- leader is now in term 2
    leader.match_index = {2: 1, 3: 1, 4: 0, 5: 0, 1: 1}
    leader.handle_append_entries_reply(AppendEntriesReply(2, True, 4, match_index=1))
    # 4 of 5 now show match_index >= 1, a clear majority -- but the entry
    # at index 1 is from term 1, not the leader's current term 2, so it
    # must NOT be committed by this rule alone.
    assert leader.commit_index == 0


def test_leader_backs_off_next_index_on_conflict_reply():
    leader = make_leader()
    leader.handle_append_entries_reply(AppendEntriesReply(1, False, 2, conflict_index=1))
    assert leader.next_index[2] == 1


def test_leader_steps_down_on_higher_term_reply():
    leader = make_leader()
    leader.handle_append_entries_reply(AppendEntriesReply(term=9, success=False, follower_id=2))
    assert leader.role == Role.FOLLOWER
    assert leader.current_term == 9


def test_client_append_rejected_when_not_leader():
    node = make_node()
    assert node.client_append("x") is False
    assert node.log == []


def test_client_append_accepted_when_leader():
    leader = make_leader()
    assert leader.client_append("y") is True
    assert leader.log[-1] == (1, "y")
