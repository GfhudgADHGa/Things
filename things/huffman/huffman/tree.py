"""Huffman tree construction and code-table generation."""
from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass
from typing import Dict, Optional, Union


@dataclass
class Leaf:
    symbol: int


@dataclass
class Internal:
    left: "Node"
    right: "Node"


Node = Union[Leaf, Internal]


def build_tree(frequencies: Dict[int, int]) -> Optional[Node]:
    """Builds a Huffman tree from a symbol -> frequency count map.

    Processes symbols in a fixed order (sorted by value) so that, given
    the same frequency map, this always builds the identical tree -- the
    decoder rebuilds the tree from the same frequency table stored in the
    compressed file's header, and needs bit-for-bit agreement on codes.
    """
    if not frequencies:
        return None

    counter = itertools.count()
    heap = [(freq, next(counter), Leaf(symbol)) for symbol, freq in sorted(frequencies.items())]
    heapq.heapify(heap)

    if len(heap) == 1:
        _, _, only_node = heap[0]
        return only_node

    while len(heap) > 1:
        freq1, _, node1 = heapq.heappop(heap)
        freq2, _, node2 = heapq.heappop(heap)
        merged = Internal(node1, node2)
        heapq.heappush(heap, (freq1 + freq2, next(counter), merged))

    _, _, root = heap[0]
    return root


def build_code_table(root: Optional[Node]) -> Dict[int, str]:
    """Maps each symbol to its code as a string of '0'/'1' characters."""
    if root is None:
        return {}

    if isinstance(root, Leaf):
        # A single distinct symbol has no real Huffman code (0 bits would
        # suffice information-theoretically), but a decoder needs to
        # consume *something* per occurrence -- 1 bit per symbol.
        return {root.symbol: "0"}

    codes: Dict[int, str] = {}

    def walk(node: Node, prefix: str) -> None:
        if isinstance(node, Leaf):
            codes[node.symbol] = prefix
            return
        walk(node.left, prefix + "0")
        walk(node.right, prefix + "1")

    walk(root, "")
    return codes
