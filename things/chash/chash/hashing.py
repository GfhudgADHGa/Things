import hashlib


def ring_hash(key: str) -> int:
    """Maps any string to a position on a 64-bit ring."""
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
