#!/usr/bin/env python3
"""Builds a small Merkle tree, demonstrates tamper detection and proof
verification on the command line, and renders a diagram of the tree
with one leaf's inclusion proof highlighted. Pillow is used only for
drawing; merkle/ itself has zero dependencies.
"""
from __future__ import annotations

import argparse

from PIL import Image, ImageDraw

from merkle.tree import MerkleTree, verify_proof

BG = (15, 15, 20)
BOX_FILL = (40, 45, 60)
BOX_OUTLINE = (90, 95, 110)
PATH_FILL = (60, 90, 70)
PATH_OUTLINE = (120, 220, 160)
LEAF_FILL = (55, 60, 110)
LEAF_HIGHLIGHT = (200, 170, 90)
LINE_COLOR = (70, 75, 90)
TEXT_COLOR = (220, 225, 235)


def demo_tamper_detection():
    documents = [f"invoice #{1000 + i}: ${(i + 1) * 137}".encode() for i in range(8)]
    tree = MerkleTree(documents)
    print(f"[merkle] {len(documents)} documents committed, root = {tree.root.hex()[:16]}...")

    tampered = list(documents)
    original_bytes = bytearray(tampered[3])
    original_bytes[-1] ^= 0xFF  # flip the last byte -- guaranteed to change the content, unlike a text search-replace that might silently miss
    tampered[3] = bytes(original_bytes)
    tampered_root = MerkleTree(tampered).root
    print(f"[tamper] document 3 silently edited (\"{documents[3].decode()}\" -> altered) -> root = {tampered_root.hex()[:16]}... (changed: {tampered_root != tree.root})")

    index = 5
    proof = tree.proof(index)
    print(f"[proof]  leaf {index} verifies against the original root: {verify_proof(documents[index], proof, tree.root)}")
    forged = documents[index] + b" (modified)"
    print(f"[proof]  forged leaf {index} verifies: {verify_proof(forged, proof, tree.root)}")
    return tree, documents, index, proof


def render_tree_diagram(tree, documents, highlight_index, proof, width, height, output):
    # recompute per-level hashes for drawing (small helper, mirrors tree.py's construction)
    from merkle.hashing import leaf_hash, node_hash
    levels = [[leaf_hash(d) for d in documents]]
    while len(levels[-1]) > 1:
        current = levels[-1]
        nxt = []
        i = 0
        while i < len(current):
            if i + 1 < len(current):
                nxt.append(node_hash(current[i], current[i + 1]))
            else:
                nxt.append(current[i])
            i += 2
        levels.append(nxt)

    path_positions = set()
    idx = highlight_index
    for level_num in range(len(levels) - 1):
        path_positions.add((level_num, idx))
        idx //= 2
    path_positions.add((len(levels) - 1, 0))

    sibling_positions = set()
    idx = highlight_index
    for step_level, step in enumerate(proof):
        if step.sibling is None:
            continue
        sib_idx = idx - 1 if step.sibling_is_left else idx + 1
        sibling_positions.add((step_level, sib_idx))
        idx //= 2

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    num_levels = len(levels)
    row_h = (height - 60) / num_levels
    positions = {}

    for level_num, level in enumerate(levels):
        y = height - 40 - level_num * row_h
        count = len(level)
        box_w = min(90, (width - 40) / count - 8)
        total_w = count * (box_w + 8) - 8
        x_start = (width - total_w) / 2
        for i, h in enumerate(level):
            x = x_start + i * (box_w + 8)
            positions[(level_num, i)] = (x + box_w / 2, y)

    # draw connecting lines first (so boxes sit on top)
    for level_num in range(len(levels) - 1):
        current = levels[level_num]
        i = 0
        while i < len(current):
            cx, cy = positions[(level_num, i)]
            parent_idx = i // 2
            px, py = positions[(level_num + 1, parent_idx)]
            draw.line([(cx, cy), (px, py)], fill=LINE_COLOR, width=1)
            if i + 1 < len(current):
                cx2, cy2 = positions[(level_num, i + 1)]
                draw.line([(cx2, cy2), (px, py)], fill=LINE_COLOR, width=1)
            i += 2

    box_h = 22
    for level_num, level in enumerate(levels):
        for i, h in enumerate(level):
            cx, cy = positions[(level_num, i)]
            is_leaf = level_num == 0
            on_path = (level_num, i) in path_positions
            is_sibling = (level_num, i) in sibling_positions
            if on_path:
                fill, outline = PATH_FILL, PATH_OUTLINE
            elif is_sibling:
                fill, outline = (90, 70, 50), (210, 160, 90)
            elif is_leaf:
                fill, outline = LEAF_FILL, BOX_OUTLINE
            else:
                fill, outline = BOX_FILL, BOX_OUTLINE
            box_w = 74
            draw.rectangle([cx - box_w / 2, cy - box_h / 2, cx + box_w / 2, cy + box_h / 2], fill=fill, outline=outline, width=2)
            draw.text((cx - box_w / 2 + 6, cy - 6), h.hex()[:8], fill=TEXT_COLOR)

    draw.text((10, 10), f"leaf {highlight_index}'s inclusion proof (green = path, orange = sibling hashes needed)", fill=TEXT_COLOR)
    img.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="tree_diagram.png")
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=500)
    args = parser.parse_args()

    tree, documents, index, proof = demo_tamper_detection()
    render_tree_diagram(tree, documents, index, proof, args.width, args.height, args.output)
    print(f"\nwrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
