#!/usr/bin/env python3
"""Validate and publish one article through the WUZHICMS multipart API."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
import warnings
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import urlsplit

warnings.filterwarnings("ignore", message=r"urllib3 v2 only supports OpenSSL.*")

import requests
from PIL import Image


PLACEHOLDER = "[IMAGE_BASE64]"
PUBLISH_PATH = "/index.php"
PUBLISH_QUERY = "m=autocreate&f=index&v=autocreate"
LOCAL_TEST_HOSTS = {"127.0.0.1", "localhost"}


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


def validate_site_host(site_host: str) -> str:
    """Accept only a bare Sheet tab host, without URL components or a port."""
    host = site_host.lower()
    labels = host.split(".")
    if not site_host.isascii() or len(host) > 253 or not all(
        re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in labels
    ):
        raise ValueError("Site host must be the bare domain from the selected Sheet tab")
    return host


def build_endpoint(site_host: str) -> str:
    return f"https://{validate_site_host(site_host)}{PUBLISH_PATH}?{PUBLISH_QUERY}"


def validate_endpoint(
    endpoint: str, allow_http_localhost: bool, site_host: str
) -> str:
    """Fail closed on a wrong route or host; return the canonical validated URL."""
    expected_host = validate_site_host(site_host)
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in endpoint):
        raise ValueError("Endpoint must not contain whitespace or control characters")
    if "\\" in endpoint:
        raise ValueError("Endpoint must not contain backslashes")
    parsed = urlsplit(endpoint)
    host = (parsed.hostname or "").lower()
    if parsed.username is not None or parsed.password is not None or "#" in endpoint:
        raise ValueError("Endpoint must not contain credentials or a fragment")
    if host != expected_host:
        raise ValueError("Endpoint host must exactly match --site-host from the selected Sheet tab")
    local_http = (
        allow_http_localhost and parsed.scheme == "http" and host in LOCAL_TEST_HOSTS
    )
    if parsed.scheme != "https" and not local_http:
        raise ValueError("Endpoint must use HTTPS; HTTP is allowed only for explicit localhost tests")
    if not re.fullmatch(r"[A-Za-z0-9.-]+(?::[0-9]+)?", parsed.netloc):
        raise ValueError("Endpoint authority must contain only the host and an optional numeric port")
    port = parsed.port
    if local_http:
        if port is not None and port < 1:
            raise ValueError("Local test endpoint port must be between 1 and 65535")
    elif port not in {None, 443}:
        raise ValueError("Production endpoint must use the standard HTTPS port 443")
    if parsed.path != PUBLISH_PATH:
        raise ValueError(f"Publishing endpoint path must be exactly {PUBLISH_PATH}")
    # Compare raw tokens, not a dict: duplicates, encoded aliases and extra keys
    # must not be collapsed or decoded into an apparently valid route.
    if sorted(parsed.query.split("&")) != sorted(PUBLISH_QUERY.split("&")):
        raise ValueError(
            f"Publishing route must contain exactly {PUBLISH_QUERY}, each parameter once"
        )
    authority = expected_host
    if local_http and port is not None:
        authority += f":{port}"
    return f"{parsed.scheme}://{authority}{PUBLISH_PATH}?{PUBLISH_QUERY}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-host", required=True,
        help="Exact bare domain from the selected Sheet tab",
    )
    parser.add_argument(
        "--endpoint",
        help="Optional URL assertion; defaults to the fixed route for --site-host",
    )
    parser.add_argument("--title-file", type=Path)
    parser.add_argument("--seo-title-file", type=Path)
    parser.add_argument("--remark-file", type=Path)
    parser.add_argument("--seo-desc-file", type=Path)
    parser.add_argument("--content-file", type=Path)
    parser.add_argument("--thumb", type=Path)
    parser.add_argument("--content-image", type=Path, action="append", default=[])
    parser.add_argument("--content-image-alt", action="append", default=[])
    parser.add_argument(
        "--api-key-env",
        default="SEO_GEO_ARTICLE_WEBKEY",
        help="Read the publishing key from this environment variable; otherwise prompt securely",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true",
        help="Validate local route and payload only; no HTTP request",
    )
    mode.add_argument(
        "--check-endpoint", action="store_true",
        help="Validate and print the route only; no files, key, or HTTP request",
    )
    parser.add_argument("--allow-http-localhost", action="store_true")
    args = parser.parse_args()
    if not args.check_endpoint:
        required_files = (
            "title_file", "seo_title_file", "remark_file", "seo_desc_file", "content_file", "thumb",
        )
        missing = [
            "--" + name.replace("_", "-")
            for name in required_files if getattr(args, name) is None
        ]
        if missing:
            parser.error("the following arguments are required: " + ", ".join(missing))
    return args


def main() -> int:
    args = parse_args()
    endpoint = validate_endpoint(
        args.endpoint if args.endpoint is not None else build_endpoint(args.site_host),
        args.allow_http_localhost,
        args.site_host,
    )
    if args.check_endpoint:
        print(json.dumps({
            "valid": True,
            "site_host": validate_site_host(args.site_host),
            "endpoint": endpoint,
            "validation_scope": "local-route-only",
            "network_request_sent": False,
        }, ensure_ascii=False, indent=2))
        return 0
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
        "endpoint": endpoint,
        "route_validation": "passed",
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
        if (urlsplit(endpoint).hostname or "").lower() in LOCAL_TEST_HOSTS:
            session.trust_env = False
        try:
            response = session.post(
                endpoint,
                headers=headers,
                data=data,
                files=files,
                timeout=(15, 120),
                allow_redirects=False,
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise RuntimeError(
                "Publish request outcome is unknown; inspect the site before any retry"
            ) from exc

    if 300 <= response.status_code < 400:
        raise RuntimeError(
            f"Publishing endpoint returned HTTP {response.status_code}; redirect not followed. "
            "Inspect the site and Sheet before any retry"
        )
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
