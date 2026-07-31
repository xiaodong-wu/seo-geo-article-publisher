#!/usr/bin/env python3
"""Verify a published article immediately and once more after a delay."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import warnings
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

warnings.filterwarnings("ignore", message=r"urllib3 v2 only supports OpenSSL.*")

import requests


SPACE_RE = re.compile(r"\s+")
REQUEST_TIMEOUT = (15, 45)


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


def path_appears_in_html(path: str, html: str) -> bool:
    decoded_html = unescape(html)
    parsed_path = urlparse(path).path
    candidates = {path}
    if parsed_path:
        candidates.add(parsed_path)
    return any(candidate in decoded_html for candidate in candidates)


def get_response(
    session: requests.Session,
    url: str,
    label: str,
) -> tuple[requests.Response | None, str | None]:
    try:
        return session.get(url, timeout=REQUEST_TIMEOUT), None
    except (requests.ConnectionError, requests.Timeout) as exc:
        return None, f"{label} request failed: {exc}"


def check_once(
    session: requests.Session,
    url: str,
    listing_url: str,
    title: str,
    thumbnail_path: str,
    content_image_paths: list[str],
    theme_colors: dict[str, str],
) -> dict[str, object]:
    errors: list[str] = []
    article_response, article_request_error = get_response(session, url, "article page")
    listing_response, listing_request_error = get_response(
        session, listing_url, "article listing page"
    )
    thumbnail_url = urljoin(url, thumbnail_path)
    thumbnail_response, thumbnail_request_error = get_response(
        session, thumbnail_url, "thumbnail asset"
    )

    article_status = article_response.status_code if article_response is not None else None
    listing_status = listing_response.status_code if listing_response is not None else None
    thumbnail_status = (
        thumbnail_response.status_code if thumbnail_response is not None else None
    )
    content_images_present = False
    thumbnail_present_on_listing = False
    thumbnail_content_type = ""

    if article_request_error:
        errors.append(article_request_error)
    elif article_response is not None:
        parser = TextExtractor()
        parser.feed(article_response.text)
        page_text = normalize_space("".join(parser.parts))
        missing_content_images = [
            path
            for path in content_image_paths
            if not path_appears_in_html(path, article_response.text)
        ]
        content_images_present = not missing_content_images
        non_webp_content_images = [
            path
            for path in content_image_paths
            if not urlparse(path).path.lower().endswith(".webp")
        ]
        if article_response.status_code != 200:
            errors.append(f"article page HTTP {article_response.status_code}")
        if normalize_space(title).casefold() not in page_text.casefold():
            errors.append("title not found on article page")
        if missing_content_images:
            errors.append(
                "missing content image paths on article page: "
                + ", ".join(missing_content_images)
            )
        if non_webp_content_images:
            errors.append(
                "non-WebP content image paths: " + ", ".join(non_webp_content_images)
            )
        if not re.search(
            r"<style\b[^>]*\bdata-article-style=[\"']responsive-v1[\"']",
            article_response.text,
            flags=re.IGNORECASE,
        ):
            errors.append("responsive article style marker not found")
        if not re.search(
            r"<article\b[^>]*\bclass=[\"'][^\"']*\barticle-content\b[^\"']*[\"']",
            article_response.text,
            flags=re.IGNORECASE,
        ):
            errors.append("article-content wrapper not found")
        missing_theme_colors = [
            variable
            for variable, color in theme_colors.items()
            if not re.search(
                rf"{re.escape(variable)}\s*:\s*{re.escape(color)}\s*;",
                article_response.text,
                flags=re.IGNORECASE,
            )
        ]
        if missing_theme_colors:
            errors.append(
                "missing site-theme color variables: " + ", ".join(missing_theme_colors)
            )
        if re.search(
            r"<nav\b[^>]*\bclass=[\"'][^\"']*\barticle-toc\b[^\"']*[\"']",
            article_response.text,
            flags=re.IGNORECASE,
        ):
            errors.append("article table of contents must not be present")
        if "[IMAGE_BASE64]" in article_response.text:
            errors.append("unreplaced image placeholder found")

    if thumbnail_request_error:
        errors.append(thumbnail_request_error)
    elif thumbnail_response is not None:
        thumbnail_content_type = thumbnail_response.headers.get("Content-Type", "")
        if thumbnail_response.status_code != 200:
            errors.append(f"thumbnail asset HTTP {thumbnail_response.status_code}")
        if not thumbnail_response.content:
            errors.append("thumbnail asset is empty")
    if not urlparse(thumbnail_path).path.lower().endswith(".webp"):
        errors.append(f"non-WebP thumbnail path: {thumbnail_path}")

    if listing_request_error:
        errors.append(listing_request_error)
    elif listing_response is not None:
        if listing_response.status_code != 200:
            errors.append(f"article listing page HTTP {listing_response.status_code}")
        thumbnail_present_on_listing = path_appears_in_html(
            thumbnail_path, listing_response.text
        )
        if not thumbnail_present_on_listing:
            errors.append(
                "thumbnail path not found on article listing page: " + thumbnail_path
            )

    return {
        "verified": not errors,
        "http_status": article_status,
        "article_page": {
            "url": url,
            "http_status": article_status,
            "content_images_present": content_images_present,
        },
        "thumbnail_asset": {
            "url": thumbnail_url,
            "http_status": thumbnail_status,
            "content_type": thumbnail_content_type,
        },
        "article_listing_page": {
            "url": listing_url,
            "http_status": listing_status,
            "thumbnail_present": thumbnail_present_on_listing,
        },
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--listing-url", required=True)
    parser.add_argument("--title-file", type=Path, required=True)
    parser.add_argument("--theme-colors-file", type=Path, required=True)
    parser.add_argument("--thumbnail-path", required=True)
    parser.add_argument("--content-image-path", action="append", default=[])
    parser.add_argument("--retry-delay", type=int, default=30)
    parser.add_argument("--allow-http-localhost", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parsed = urlparse(args.url)
    parsed_listing = urlparse(args.listing_url)
    host = (parsed.hostname or "").lower()
    listing_host = (parsed_listing.hostname or "").lower()
    localhost_allowed = (
        args.allow_http_localhost
        and parsed.scheme == "http"
        and host in {"127.0.0.1", "localhost"}
    )
    if parsed.scheme != "https" and not localhost_allowed:
        raise ValueError("Article URL must use HTTPS")
    if parsed_listing.scheme != parsed.scheme or listing_host != host:
        raise ValueError("Article listing URL must use the same scheme and host as the article URL")
    if parsed_listing.scheme != "https" and not localhost_allowed:
        raise ValueError("Article listing URL must use HTTPS")
    if args.retry_delay < 0 or args.retry_delay > 60:
        raise ValueError("--retry-delay must be between 0 and 60 seconds")
    if not args.content_image_path:
        raise ValueError("Provide at least one --content-image-path")
    thumbnail_url = urlparse(urljoin(args.url, args.thumbnail_path))
    if (
        thumbnail_url.scheme != parsed.scheme
        or (thumbnail_url.hostname or "").lower() != host
    ):
        raise ValueError("Thumbnail path must resolve to the article host")
    title = read_text(args.title_file)
    theme_colors = read_theme_colors(args.theme_colors_file)

    attempts = []
    with requests.Session() as session:
        if host in {"127.0.0.1", "localhost"}:
            session.trust_env = False
        first = check_once(
            session,
            args.url,
            args.listing_url,
            title,
            args.thumbnail_path,
            args.content_image_path,
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
            args.listing_url,
            title,
            args.thumbnail_path,
            args.content_image_path,
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
