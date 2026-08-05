#!/usr/bin/env python3
"""CLI for the from-scratch JPEG encoder. Loads an image with Pillow
(a demo/IO concern -- the encoder itself, jpeg/, has no dependencies),
encodes it, writes the result, and reports the compression ratio and
PSNR against the original (using Pillow again, this time as the decode
oracle, to measure exactly what was lost)."""
import argparse
import math

from PIL import Image

from jpeg import encode_rgb_image


def _psnr(original: Image.Image, decoded: Image.Image) -> float:
    w, h = original.size
    se = 0
    orig_px = original.load()
    dec_px = decoded.load()
    for y in range(h):
        for x in range(w):
            for c in range(3):
                se += (orig_px[x, y][c] - dec_px[x, y][c]) ** 2
    mse = se / (w * h * 3)
    return float("inf") if mse == 0 else 10 * math.log10(255 * 255 / mse)


def _synthetic_demo_image(width=256, height=192):
    im = Image.new("RGB", (width, height))
    pixels = []
    for y in range(height):
        for x in range(width):
            r = (x * 255) // width
            g = (y * 255) // height
            b = 128 + int(60 * math.sin(x / 12.0) * math.cos(y / 12.0))
            pixels.append((r, g, max(0, min(255, b))))
    im.putdata(pixels)
    return im


def main() -> int:
    parser = argparse.ArgumentParser(description="Encode an image with a from-scratch baseline JPEG encoder")
    parser.add_argument("input", nargs="?", help="input image path (any format Pillow can read); omit for a synthetic demo image")
    parser.add_argument("-o", "--output", default="output.jpg", help="output .jpg path")
    parser.add_argument("-q", "--quality", type=int, default=80, help="JPEG quality, 1-100 (default 80)")
    args = parser.parse_args()

    if args.input:
        source = Image.open(args.input).convert("RGB")
    else:
        source = _synthetic_demo_image()

    width, height = source.size
    source_px = source.load()
    pixels = [[source_px[x, y] for x in range(width)] for y in range(height)]

    data = encode_rgb_image(pixels, width, height, quality=args.quality)
    with open(args.output, "wb") as f:
        f.write(data)

    decoded = Image.open(args.output).convert("RGB")
    psnr = _psnr(source, decoded)
    raw_size = width * height * 3
    print(f"{width}x{height}, quality={args.quality}")
    print(f"  raw:  {raw_size:,} bytes")
    print(f"  jpeg: {len(data):,} bytes ({100 * len(data) / raw_size:.1f}% of raw)")
    print(f"  PSNR: {psnr:.2f} dB")
    print(f"  wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
