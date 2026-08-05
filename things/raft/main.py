#!/usr/bin/env python3
"""A narrated demo run: a 5-node Raft cluster elects a leader, replicates
some client commands, survives a network partition and a leader crash,
and ends with every surviving node's state machine printed side by side
so you can see them agree."""
import argparse
import random

from raft import Cluster, Network, Role


def _describe(cluster: Cluster) -> str:
    leader = cluster.leader()
    return f"t={cluster.now:>5}  leader={leader.node_id if leader else None}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--drop-probability", type=float, default=0.1)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    net = Network(rng, min_delay=1, max_delay=8, drop_probability=args.drop_probability)
    cluster = Cluster([1, 2, 3, 4, 5], net, rng)

    print("-- electing an initial leader --")
    cluster.run_until(1000)
    print(_describe(cluster))

    print("\n-- replicating client commands --")
    for i in range(5):
        cluster.client_append(f"SET x={i}")
        cluster.run_until(cluster.now + 150)
    print(_describe(cluster), " log lengths:", {nid: len(n.log) for nid, n in cluster.nodes.items()})

    print("\n-- partitioning the cluster (2 nodes | 3 nodes) --")
    net.partition([[1, 2], [3, 4, 5]])
    cluster.run_until(cluster.now + 1500)
    print(_describe(cluster), " (only the 3-node majority side can elect/commit)")

    print("\n-- healing the partition --")
    net.heal()
    cluster.run_until(cluster.now + 1000)
    print(_describe(cluster))

    leader = cluster.leader()
    if leader is not None:
        print(f"\n-- crashing the leader (node {leader.node_id}) --")
        cluster.crash(leader.node_id)
        cluster.run_until(cluster.now + 1500)
        print(_describe(cluster))
        cluster.client_append("SET x=post-crash")
        cluster.run_until(cluster.now + 1000)

    print("\n-- final state (crashed nodes excluded) --")
    for nid, node in sorted(cluster.nodes.items()):
        tag = "CRASHED" if nid in cluster.crashed else node.role.value
        print(f"  node {nid} [{tag:10s}] term={node.current_term} "
              f"commit={node.commit_index} applied={node.state_machine}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
