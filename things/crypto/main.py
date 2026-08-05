#!/usr/bin/env python3
"""CLI: sha256sum-alike, an HMAC tool, and AES-128-CBC file encrypt/decrypt."""
import argparse
import os
import sys

from crypto import cbc_decrypt, cbc_encrypt, hmac_sha256_hex, sha256_hex


def cmd_sha256(args) -> int:
    data = sys.stdin.buffer.read() if args.file == "-" else open(args.file, "rb").read()
    print(f"{sha256_hex(data)}  {args.file}")
    return 0


def cmd_hmac(args) -> int:
    data = sys.stdin.buffer.read() if args.file == "-" else open(args.file, "rb").read()
    print(hmac_sha256_hex(args.key.encode(), data))
    return 0


def cmd_encrypt(args) -> int:
    key = bytes.fromhex(args.key)
    iv = os.urandom(16)
    plaintext = open(args.input, "rb").read()
    ciphertext = cbc_encrypt(key, iv, plaintext)
    with open(args.output, "wb") as f:
        f.write(iv + ciphertext)  # IV prepended so decrypt doesn't need it passed separately
    print(f"wrote {args.output} ({len(iv) + len(ciphertext)} bytes, IV prepended)")
    return 0


def cmd_decrypt(args) -> int:
    key = bytes.fromhex(args.key)
    blob = open(args.input, "rb").read()
    iv, ciphertext = blob[:16], blob[16:]
    plaintext = cbc_decrypt(key, iv, ciphertext)
    with open(args.output, "wb") as f:
        f.write(plaintext)
    print(f"wrote {args.output} ({len(plaintext)} bytes)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_sha = sub.add_parser("sha256", help="hash a file (or - for stdin)")
    p_sha.add_argument("file")
    p_sha.set_defaults(func=cmd_sha256)

    p_hmac = sub.add_parser("hmac", help="HMAC-SHA256 a file with a text key")
    p_hmac.add_argument("key")
    p_hmac.add_argument("file")
    p_hmac.set_defaults(func=cmd_hmac)

    p_enc = sub.add_parser("encrypt", help="AES-128-CBC encrypt a file")
    p_enc.add_argument("key", help="32 hex characters (16 bytes)")
    p_enc.add_argument("input")
    p_enc.add_argument("output")
    p_enc.set_defaults(func=cmd_encrypt)

    p_dec = sub.add_parser("decrypt", help="AES-128-CBC decrypt a file written by 'encrypt'")
    p_dec.add_argument("key", help="32 hex characters (16 bytes)")
    p_dec.add_argument("input")
    p_dec.add_argument("output")
    p_dec.set_defaults(func=cmd_decrypt)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
