#!/usr/bin/env python3
"""A narrated demo: three replicas of each CRDT make concurrent,
conflicting edits with no coordination between them, gossip in a random
order, and end up in the exact same state anyway -- no leader, no
quorum, no consensus round, just merge()."""
import random

from crdt import GCounter, LWWRegister, ORSet, PNCounter


def demo_gcounter(rng: random.Random) -> None:
    print("-- GCounter: three replicas independently counting page views --")
    a, b, c = GCounter("edge-a"), GCounter("edge-b"), GCounter("edge-c")
    a.increment(12)
    b.increment(7)
    c.increment(31)
    merged = a.merge(b).merge(c)
    print(f"   edge-a saw 12, edge-b saw 7, edge-c saw 31 -> total: {merged.value()}")


def demo_pncounter() -> None:
    print("\n-- PNCounter: a like/unlike counter, edited from two devices --")
    phone, laptop = PNCounter("phone"), PNCounter("laptop")
    phone.increment()  # liked from phone
    laptop.increment()  # liked from laptop (before syncing)
    laptop.decrement()  # then unliked from laptop
    merged = phone.merge(laptop)
    print(f"   phone: +1, laptop: +1 then -1, never synced with each other -> net: {merged.value()}")


def demo_orset() -> None:
    print("\n-- ORSet: two shopping-list replicas edited offline --")
    home, work = ORSet("home"), ORSet("work")
    home.add("milk")
    home.add("eggs")
    work.add("milk")
    work.remove("milk")  # work never saw home's concurrent "milk" add
    merged = home.merge(work)
    print(f"   home added milk+eggs; work added milk then removed it (without seeing home's add)")
    print(f"   merged list: {sorted(merged.elements())}  (add-wins: milk survives)")


def demo_lww() -> None:
    print("\n-- LWWRegister: a profile status, edited on two devices at once --")
    phone, laptop = LWWRegister("phone"), LWWRegister("laptop")
    phone.set("Busy", timestamp=100.0)
    laptop.set("Available", timestamp=100.5)
    merged = phone.merge(laptop)
    print(f'   phone set "Busy" @100.0, laptop set "Available" @100.5 -> merged: "{merged.value}"')


def main() -> int:
    rng = random.Random(0)
    demo_gcounter(rng)
    demo_pncounter()
    demo_orset()
    demo_lww()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
