#!/usr/bin/env python3
"""Fingerprint and compare same-site image candidates before global slot selection."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

from PIL import Image, ImageOps


NEAR_DUPLICATE_DISTANCE = 6


def image_fingerprint(path: Path) -> tuple[str, str, int, int]:
    source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        width, height = image.size
        grayscale = image.convert("L").resize(
            (32, 32),
            Image.Resampling.LANCZOS,
        )
        pixels = list(grayscale.getdata())

    cosine = [
        [
            math.cos((2 * position + 1) * frequency * math.pi / 64)
            for position in range(32)
        ]
        for frequency in range(8)
    ]
    coefficients: list[float] = []
    for vertical_frequency in range(8):
        for horizontal_frequency in range(8):
            value = 0.0
            for y in range(32):
                row_offset = y * 32
                vertical_cosine = cosine[vertical_frequency][y]
                for x in range(32):
                    value += (
                        pixels[row_offset + x]
                        * cosine[horizontal_frequency][x]
                        * vertical_cosine
                    )
            coefficients.append(value)

    median = statistics.median(coefficients[1:])
    bits = 0
    for coefficient in coefficients:
        bits = (bits << 1) | int(coefficient > median)
    return source_sha256, f"{bits:016X}", width, height


def perceptual_hash_distance(first: str, second: str) -> int:
    return bin(int(first, 16) ^ int(second, 16)).count("1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", action="append", type=Path, required=True)
    parser.add_argument("--reference-url", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if len(args.image) != len(args.reference_url):
        raise ValueError("Provide one --reference-url for every --image")
    if not 1 <= len(args.image) <= 12:
        raise ValueError("Analyze between 1 and 12 image candidates")

    candidates: list[dict[str, object]] = []
    for index, (image_path, reference_url) in enumerate(
        zip(args.image, args.reference_url),
        start=1,
    ):
        resolved = image_path.expanduser().resolve()
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        source_sha256, perceptual_hash, width, height = image_fingerprint(resolved)
        candidates.append(
            {
                "candidate_id": f"candidate-{index:02d}",
                "classification": "",
                "reference_url": reference_url,
                "reference_file": str(resolved),
                "source_sha256": source_sha256,
                "perceptual_hash": perceptual_hash,
                "width": width,
                "height": height,
                "view_angle": "",
                "scene_type": "",
                "label_legibility": "",
                "article_relevance": "",
                "eligible_for_product_lock": False,
                "identity_summary": "",
            }
        )

    pairs: list[dict[str, object]] = []
    for first_index, first in enumerate(candidates):
        for second in candidates[first_index + 1 :]:
            exact_duplicate = first["source_sha256"] == second["source_sha256"]
            distance = perceptual_hash_distance(
                str(first["perceptual_hash"]),
                str(second["perceptual_hash"]),
            )
            if exact_duplicate or distance <= NEAR_DUPLICATE_DISTANCE:
                pairs.append(
                    {
                        "first": first["candidate_id"],
                        "second": second["candidate_id"],
                        "exact_duplicate": exact_duplicate,
                        "perceptual_hash_distance": distance,
                    }
                )

    result = {
        "candidate_pool": candidates,
        "duplicate_analysis": {
            "near_duplicate_distance": NEAR_DUPLICATE_DISTANCE,
            "pairs_to_consolidate": pairs,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "candidates": len(candidates),
                "pairs_to_consolidate": len(pairs),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
