"""Applying an edit script back to a source to reconstruct the target --
validated against the given source, the way a real patch tool refuses to
apply a diff that doesn't actually match what you're applying it to.
"""
from __future__ import annotations

from typing import List

from .diff import Op


class PatchError(Exception):
    pass


def apply_patch(a: List[str], ops: List[Op]) -> List[str]:
    result: List[str] = []
    pos = 0

    for op, line in ops:
        if op in ("equal", "delete"):
            if pos >= len(a):
                raise PatchError(f"patch does not apply: ran out of source lines at op {op!r} {line!r}")
            if a[pos] != line:
                raise PatchError(
                    f"patch does not apply: expected {a[pos]!r} at position {pos}, patch has {line!r}"
                )
            pos += 1
            if op == "equal":
                result.append(line)
        elif op == "insert":
            result.append(line)
        else:
            raise PatchError(f"unknown op {op!r}")

    if pos != len(a):
        raise PatchError(f"patch does not apply: {len(a) - pos} source line(s) left unconsumed")

    return result
