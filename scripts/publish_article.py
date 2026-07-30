#!/usr/bin/env python3
"""Validate and publish one article through the WUZHICMS multipart API."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import warnings
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import urlparse

warnings.filterwarnings("ignore", message=r"urllib3 v2 only supports OpenSSL.*")

import requests
from PIL import Image


PLACEHOLDER = "[IMAGE_BASE64]"


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8").strip()


def validate_webp(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() != ".webp":
        raise ValueError(f"{path.name} must use the .webp extension")
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        if image.format != "WEBP":
            raise ValueError(f"{path.name} must contain WebP data")
        width, height = image.size
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "width": width,
        "height": height,
    }


def validate_endpoint(endpoint: str, allow_http_localhost: bool) -> None:
    parsed = urlparse(endpoint)
    host = (parsed.hostname or "").lower()
    if parsed.scheme == "https" and host:
        return
    if allow_http_localhost and parsed.scheme == "http" and host in {"127.0.0.1", "localhost"}:
        return
    raise ValueError("Endpoint must use HTTPS")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--title-file", type=Path, required=True)
    parser.add_argument("--seo-title-file", type=Path, required=True)
    parser.add_argument("--remark-file", type=Path, required=True)
    parser.add_argument("--seo-desc-file", type=Path, required=True)
    parser.add_argument("--content-file", type=Path, required=True)
    parser.add_argument("--thumb", type=Path, required=True)
    parser.add_argument("--content-image", type=Path, action="append", default=[])
    parser.add_argument("--content-image-alt", action="append", default=[])
    parser.add_argument(
        "--api-key-env",
        default="SEO_GEO_ARTICLE_WEBKEY",
        help="Read the publishing key from this environment variable; otherwise prompt securely",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-http-localhost", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_endpoint(args.endpoint, args.allow_http_localhost)
    title = read_text(args.title_file)
    seo_title = read_text(args.seo_title_file)
    remark = read_text(args.remark_file)
    seo_desc = read_text(args.seo_desc_file)
    content = read_text(args.content_file)
    if title != seo_title:
        raise ValueError("seo_title1 must equal title")
    if remark != seo_desc:
        raise ValueError("remark must equal seo_desc")
    if not 2 <= len(args.content_image) <= 4:
        raise ValueError("Provide 2–4 --content-image files")
    if len(args.content_image_alt) != len(args.content_image):
        raise ValueError("Provide one --content-image-alt value per body image")
    if content.count(PLACEHOLDER) != len(args.content_image):
        raise ValueError("Placeholder count must match the body-image count")

    image_metrics = {
        "thumb": validate_webp(args.thumb),
        "content": [validate_webp(path) for path in args.content_image],
    }
    result: dict[str, object] = {
        "dry_run": args.dry_run,
        "endpoint": args.endpoint,
        "fields": {
            "title_characters": len(title),
            "seo_title_characters": len(seo_title),
            "remark_characters": len(remark),
            "seo_desc_characters": len(seo_desc),
            "placeholders": content.count(PLACEHOLDER),
        },
        "images": image_metrics,
    }
    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    api_key = os.environ.get(args.api_key_env, "").strip()
    if not api_key:
        api_key = getpass.getpass("Publishing key: ").strip()
    if not api_key:
        raise RuntimeError("Publishing key is empty")

    headers = {"Authorization": f"Bearer {api_key}"}
    data: list[tuple[str, str]] = [
        ("title", title),
        ("seo_title1", seo_title),
        ("remark", remark),
        ("seo_desc", seo_desc),
        ("content", content),
    ]
    data.extend(("content_img_alt[]", alt) for alt in args.content_image_alt)

    with ExitStack() as stack:
        thumb_handle = stack.enter_context(args.thumb.open("rb"))
        files: list[tuple[str, tuple[str, object, str]]] = [
            ("thumb", (args.thumb.name, thumb_handle, "image/webp"))
        ]
        for path in args.content_image:
            handle = stack.enter_context(path.open("rb"))
            files.append(("content_img[]", (path.name, handle, "image/webp")))
        session = stack.enter_context(requests.Session())
        if (urlparse(args.endpoint).hostname or "").lower() in {"127.0.0.1", "localhost"}:
            session.trust_env = False
        try:
            response = session.post(
                args.endpoint,
                headers=headers,
                data=data,
                files=files,
                timeout=(15, 120),
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise RuntimeError(
                "Publish request outcome is unknown; inspect the site before any retry"
            ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        excerpt = response.text[:300].replace("\n", " ")
        raise RuntimeError(
            f"Publishing API returned non-JSON HTTP {response.status_code}: {excerpt}"
        ) from exc
    if response.status_code != 200 or payload.get("code") != 0:
        message = str(payload.get("msg", "Unknown error"))[:500]
        detail = str(payload.get("detail", "")).strip()[:500]
        if detail:
            message = f"{message} ({detail})"
        raise RuntimeError(
            f"Publishing API failed (HTTP {response.status_code}): {message}"
        )
    response_data = payload.get("data") or {}
    article_url = response_data.get("article_url") or response_data.get("url")
    if not article_url:
        raise RuntimeError("Publishing API succeeded but returned no article URL")

    result.update(
        {
            "dry_run": False,
            "article_id": response_data.get("id"),
            "article_url": article_url,
            "thumb_path": response_data.get("thumb_path", ""),
            "content_images": response_data.get("content_images", []),
            "created_at": response_data.get("created_at", ""),
        }
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
