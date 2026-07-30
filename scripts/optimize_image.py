#!/usr/bin/env python3
"""Fit and encode an already regenerated article image as WebP; do not generate it."""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageColor, ImageOps, features


MAX_BYTES = 2 * 1024 * 1024
TARGETS = {
    "thumb": {"ratio": 16 / 9, "max_size": (1600, 900)},
    "content": {"ratio": 3 / 2, "max_size": (1600, 1067)},
}


def flatten_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image.copy()
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def crop_to_ratio(image: Image.Image, ratio: float) -> Image.Image:
    width, height = image.size
    current = width / height
    if math.isclose(current, ratio, rel_tol=0.002):
        return image
    if current > ratio:
        crop_width = max(1, round(height * ratio))
        left = (width - crop_width) // 2
        return image.crop((left, 0, left + crop_width, height))
    crop_height = max(1, round(width / ratio))
    top = (height - crop_height) // 2
    return image.crop((0, top, width, top + crop_height))


def contain_to_ratio(
    image: Image.Image,
    ratio: float,
    background: tuple[int, int, int],
) -> Image.Image:
    width, height = image.size
    current = width / height
    if math.isclose(current, ratio, rel_tol=0.002):
        return image
    if current > ratio:
        canvas_width = width
        canvas_height = max(height, math.ceil(width / ratio))
    else:
        canvas_height = height
        canvas_width = max(width, math.ceil(height * ratio))
    canvas = Image.new("RGB", (canvas_width, canvas_height), background)
    left = (canvas_width - width) // 2
    top = (canvas_height - height) // 2
    canvas.paste(image, (left, top))
    return canvas


def downscale(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    if image.width <= max_size[0] and image.height <= max_size[1]:
        return image
    result = image.copy()
    result.thumbnail(max_size, Image.Resampling.LANCZOS)
    return result


def encode_webp(image: Image.Image, quality: int) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=quality, method=6)
    return buffer.getvalue()


def compress(image: Image.Image, max_bytes: int) -> tuple[bytes, Image.Image, int]:
    working = image
    while min(working.size) >= 640:
        for quality in range(88, 57, -3):
            encoded = encode_webp(working, quality)
            if len(encoded) <= max_bytes:
                return encoded, working, quality
        next_size = (
            max(1, round(working.width * 0.9)),
            max(1, round(working.height * 0.9)),
        )
        working = working.resize(next_size, Image.Resampling.LANCZOS)
    raise RuntimeError(
        f"Unable to compress image below {max_bytes} bytes without excessive downscaling"
    )


def validate(path: Path, kind: str, max_bytes: int) -> dict[str, object]:
    size = path.stat().st_size
    if size > max_bytes:
        raise RuntimeError(f"Output is {size} bytes, above the {max_bytes}-byte limit")
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        if image.format != "WEBP":
            raise RuntimeError(f"Output format is {image.format}, expected WEBP")
        width, height = image.size
    ratio = width / height
    expected = TARGETS[kind]["ratio"]
    if abs(ratio - expected) > 0.01:
        raise RuntimeError(f"Output ratio {ratio:.4f} does not match {expected:.4f}")
    return {
        "path": str(path.resolve()),
        "kind": kind,
        "format": "WEBP",
        "width": width,
        "height": height,
        "bytes": size,
        "max_bytes": max_bytes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--kind", choices=sorted(TARGETS), required=True)
    parser.add_argument(
        "--fit",
        choices=("cover", "contain"),
        default="cover",
        help=(
            "cover crops to ratio; contain is a final anti-clipping safeguard "
            "for an already regenerated image and does not satisfy regeneration"
        ),
    )
    parser.add_argument(
        "--background",
        default="#ffffff",
        help="contain-mode canvas color (Pillow color syntax; default: #ffffff)",
    )
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not features.check("webp"):
        raise RuntimeError("Installed Pillow does not support WebP")
    if args.max_bytes <= 0:
        raise ValueError("--max-bytes must be positive")
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    if args.output.suffix.lower() != ".webp":
        raise ValueError("Output filename must end in .webp")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(args.input) as source:
        source = ImageOps.exif_transpose(source)
        image = flatten_to_rgb(source)
    target = TARGETS[args.kind]
    try:
        background = ImageColor.getrgb(args.background)
    except ValueError as exc:
        raise ValueError(f"Invalid --background color: {args.background}") from exc
    if args.fit == "contain":
        image = contain_to_ratio(image, target["ratio"], background)
    else:
        image = crop_to_ratio(image, target["ratio"])
    image = downscale(image, target["max_size"])
    encoded, final_image, quality = compress(image, args.max_bytes)
    args.output.write_bytes(encoded)

    result = validate(args.output, args.kind, args.max_bytes)
    result["quality"] = quality
    result["input"] = str(args.input.resolve())
    result["fit"] = args.fit
    result["operation"] = "final-encoding-only"
    result["whole_image_regenerated_by_this_script"] = False
    if args.fit == "contain":
        result["background"] = args.background
    result["encoded_size"] = list(final_image.size)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
