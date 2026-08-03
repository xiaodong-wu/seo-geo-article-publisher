#!/usr/bin/env python3
"""Select an auditable 70/30 question-versus-statement title mode."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


QUESTION_TITLE_PROBABILITY = 70


def normalize_seed(value: str) -> str:
    return " ".join(value.split())


def stable_percentage_roll(seed: str) -> int:
    normalized_seed = normalize_seed(seed)
    if not normalized_seed:
        raise ValueError("Title-mode seed cannot be empty")
    upper_bound = 1 << 64
    acceptance_limit = upper_bound - (upper_bound % 100)
    counter = 0
    while True:
        payload = f"{normalized_seed}\x1f{counter}".encode("utf-8")
        value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
        if value < acceptance_limit:
            return value % 100
        counter += 1


def select_title_mode(seed: str) -> dict[str, object]:
    normalized_seed = normalize_seed(seed)
    roll = stable_percentage_roll(normalized_seed)
    return {
        "seed": normalized_seed,
        "question_probability": QUESTION_TITLE_PROBABILITY,
        "roll": roll,
        "title_mode": (
            "question" if roll < QUESTION_TITLE_PROBABILITY else "statement"
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed",
        required=True,
        help="Fixed <run-id>|<tab>|<row-number>|<core-keyword> seed",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = select_title_mode(args.seed)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
