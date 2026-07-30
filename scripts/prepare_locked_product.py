#!/usr/bin/env python3
"""Apply an inspected mask to a source image without repainting product pixels."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--mask",
        type=Path,
        required=True,
        help="Grayscale or alpha PNG: white keeps the locked product; black removes background",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for label, path in (("source", args.source), ("mask", args.mask)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} does not exist: {path}")
    if args.mask.suffix.lower() != ".png":
        raise ValueError("Mask filename must end in .png")
    if args.output.suffix.lower() != ".png":
        raise ValueError("Output filename must end in .png")
    if args.report.suffix.lower() != ".json":
        raise ValueError("Report filename must end in .json")
    resolved_inputs = {args.source.resolve(), args.mask.resolve()}
    if args.output.resolve() in resolved_inputs:
        raise ValueError("Output must not overwrite the source or mask")
    if args.report.resolve() in resolved_inputs | {args.output.resolve()}:
        raise ValueError("Report must not overwrite an image asset")

    with Image.open(args.source) as source_image:
        source_image = ImageOps.exif_transpose(source_image).convert("RGBA")
    with Image.open(args.mask) as mask_image:
        mask_image = ImageOps.exif_transpose(mask_image)
        if "A" in mask_image.getbands():
            mask = mask_image.getchannel("A")
        else:
            mask = mask_image.convert("L")

    if mask.size != source_image.size:
        raise ValueError(
            "Mask dimensions must exactly match the source; resizing a lock mask "
            "could change product edges"
        )
    minimum, maximum = mask.getextrema()
    if minimum == maximum:
        raise ValueError("Mask must contain both removed and retained pixels")
    visible_bounds = mask.getbbox()
    if visible_bounds is None:
        raise ValueError("Mask does not retain any product pixels")

    output_image = source_image.copy()
    output_image.putalpha(mask)
    output_image = output_image.crop(visible_bounds)
    if output_image.width < 2 or output_image.height < 2:
        raise ValueError("Masked product bounds are too small")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_image.save(args.output, format="PNG", optimize=True)

    source_crop = source_image.crop(visible_bounds).convert("RGB")
    output_crop = output_image.convert("RGB")
    if ImageChops.difference(source_crop, output_crop).getbbox() is not None:
        raise RuntimeError("Product RGB pixels changed during extraction")

    retained_pixels = sum(1 for value in mask.getdata() if value > 0)
    total_pixels = mask.width * mask.height
    report = {
        "source": str(args.source.resolve()),
        "mask": str(args.mask.resolve()),
        "locked_product": str(args.output.resolve()),
        "source_size": list(source_image.size),
        "locked_product_size": list(output_image.size),
        "visible_bounds": list(visible_bounds),
        "retained_pixel_fraction": round(retained_pixels / total_pixels, 6),
        "product_rgb_repainted": False,
        "operation": "alpha-mask-extraction-only",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
