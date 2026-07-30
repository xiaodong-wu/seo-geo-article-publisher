#!/usr/bin/env python3
"""Verify a published article immediately and once more after a delay."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import warnings
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

warnings.filterwarnings("ignore", message=r"urllib3 v2 only supports OpenSSL.*")

import requests


SPACE_RE = re.compile(r"\s+")


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8").strip()


def normalize_space(value: str) -> str:
    return SPACE_RE.sub(" ", value).strip()


def read_theme_colors(path: Path) -> dict[str, str]:
    value = json.loads(read_text(path))
    colors = value.get("colors") if isinstance(value, dict) else None
    if not isinstance(colors, dict) or not colors:
        raise ValueError("Theme colors file must contain a non-empty colors object")
    normalized: dict[str, str] = {}
    for variable, color in colors.items():
        variable_text = normalize_space(str(variable))
        color_text = normalize_space(str(color))
        if not re.fullmatch(r"--article-[a-z0-9-]+", variable_text):
            raise ValueError(f"Invalid article theme variable: {variable_text}")
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color_text):
            raise ValueError(f"Invalid theme color for {variable_text}: {color_text}")
        normalized[variable_text] = color_text.upper()
    return normalized


def check_once(
    session: requests.Session,
    url: str,
    title: str,
    image_paths: list[str],
    theme_colors: dict[str, str],
) -> dict[str, object]:
    try:
        response = session.get(url, timeout=(15, 45))
    except (requests.ConnectionError, requests.Timeout) as exc:
        return {"verified": False, "error": f"request failed: {exc}"}
    parser = TextExtractor()
    parser.feed(response.text)
    page_text = normalize_space("".join(parser.parts))
    missing_images = [path for path in image_paths if path not in response.text]
    non_webp = [path for path in image_paths if not urlparse(path).path.lower().endswith(".webp")]
    errors = []
    if response.status_code != 200:
        errors.append(f"HTTP {response.status_code}")
    if normalize_space(title).casefold() not in page_text.casefold():
        errors.append("title not found")
    if missing_images:
        errors.append("missing image paths: " + ", ".join(missing_images))
    if non_webp:
        errors.append("non-WebP image paths: " + ", ".join(non_webp))
    if not re.search(
        r"<style\b[^>]*\bdata-article-style=[\"']responsive-v1[\"']",
        response.text,
        flags=re.IGNORECASE,
    ):
        errors.append("responsive article style marker not found")
    if not re.search(
        r"<article\b[^>]*\bclass=[\"'][^\"']*\barticle-content\b[^\"']*[\"']",
        response.text,
        flags=re.IGNORECASE,
    ):
        errors.append("article-content wrapper not found")
    missing_theme_colors = [
        variable
        for variable, color in theme_colors.items()
        if not re.search(
            rf"{re.escape(variable)}\s*:\s*{re.escape(color)}\s*;",
            response.text,
            flags=re.IGNORECASE,
        )
    ]
    if missing_theme_colors:
        errors.append(
            "missing site-theme color variables: " + ", ".join(missing_theme_colors)
        )
    if re.search(
        r"<nav\b[^>]*\bclass=[\"'][^\"']*\barticle-toc\b[^\"']*[\"']",
        response.text,
        flags=re.IGNORECASE,
    ):
        errors.append("article table of contents must not be present")
    if "[IMAGE_BASE64]" in response.text:
        errors.append("unreplaced image placeholder found")
    return {
        "verified": not errors,
        "http_status": response.status_code,
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--title-file", type=Path, required=True)
    parser.add_argument("--theme-colors-file", type=Path, required=True)
    parser.add_argument("--image-path", action="append", default=[])
    parser.add_argument("--retry-delay", type=int, default=30)
    parser.add_argument("--allow-http-localhost", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parsed = urlparse(args.url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" and not (
        args.allow_http_localhost
        and parsed.scheme == "http"
        and host in {"127.0.0.1", "localhost"}
    ):
        raise ValueError("Article URL must use HTTPS")
    if args.retry_delay < 0 or args.retry_delay > 60:
        raise ValueError("--retry-delay must be between 0 and 60 seconds")
    if not args.image_path:
        raise ValueError("Provide at least one --image-path")
    title = read_text(args.title_file)
    theme_colors = read_theme_colors(args.theme_colors_file)

    attempts = []
    with requests.Session() as session:
        if host in {"127.0.0.1", "localhost"}:
            session.trust_env = False
        first = check_once(
            session,
            args.url,
            title,
            args.image_path,
            theme_colors,
        )
        attempts.append(first)
        if first["verified"]:
            print(
                json.dumps(
                    {"status": "verified", "attempts": attempts},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        time.sleep(args.retry_delay)
        second = check_once(
            session,
            args.url,
            title,
            args.image_path,
            theme_colors,
        )
        attempts.append(second)

    result = {
        "status": "verified" if second["verified"] else "manual_review",
        "attempts": attempts,
        "retry_delay_seconds": args.retry_delay,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if second["verified"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
