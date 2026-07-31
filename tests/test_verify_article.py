from __future__ import annotations

import importlib.util
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "verify_article.py"
SPEC = importlib.util.spec_from_file_location("verify_article", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
verify_article = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_article)

TITLE = "A Verified Article"
THUMBNAIL_PATH = "/upload/thumb.webp"
CONTENT_IMAGE_PATH = "/upload/body.webp"
THEME_COLORS = {
    "--article-accent": "#112233",
    "--article-text": "#445566",
}
ARTICLE_HTML = f"""
<html>
  <body>
    <style data-article-style="responsive-v1">
      .article-content {{
        --article-accent: #112233;
        --article-text: #445566;
      }}
    </style>
    <article class="article-content">
      <h1>{TITLE}</h1>
      <img src="{CONTENT_IMAGE_PATH}" alt="">
    </article>
  </body>
</html>
""".encode()
LISTING_HTML = (
    f'<html><body><img src="{THUMBNAIL_PATH}" alt=""></body></html>'.encode()
)
WEBP_BYTES = b"RIFF\x00\x00\x00\x00WEBPVP8 "


class RouteHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        status, content_type, body = self.server.routes.get(  # type: ignore[attr-defined]
            self.path,
            (404, "text/plain", b"not found"),
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class VerifyArticleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), RouteHandler)
        self.server.routes = {  # type: ignore[attr-defined]
            "/article.html": (200, "text/html; charset=utf-8", ARTICLE_HTML),
            "/blog/": (200, "text/html; charset=utf-8", LISTING_HTML),
            THUMBNAIL_PATH: (200, "image/webp", WEBP_BYTES),
        }
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def check(self) -> dict[str, object]:
        with verify_article.requests.Session() as session:
            session.trust_env = False
            return verify_article.check_once(
                session,
                f"{self.origin}/article.html",
                f"{self.origin}/blog/",
                TITLE,
                THUMBNAIL_PATH,
                [CONTENT_IMAGE_PATH],
                THEME_COLORS,
            )

    def test_thumbnail_need_not_appear_on_article_detail_page(self) -> None:
        result = self.check()

        self.assertTrue(result["verified"])
        self.assertNotIn(THUMBNAIL_PATH, ARTICLE_HTML.decode())
        self.assertTrue(result["article_page"]["content_images_present"])
        self.assertEqual(result["thumbnail_asset"]["http_status"], 200)
        self.assertTrue(result["article_listing_page"]["thumbnail_present"])

    def test_missing_thumbnail_on_listing_page_fails(self) -> None:
        self.server.routes["/blog/"] = (  # type: ignore[attr-defined]
            200,
            "text/html; charset=utf-8",
            b"<html><body>No thumbnail yet</body></html>",
        )

        result = self.check()

        self.assertFalse(result["verified"])
        self.assertTrue(
            any(
                "thumbnail path not found on article listing page" in error
                for error in result["errors"]
            )
        )

    def test_unavailable_thumbnail_asset_fails(self) -> None:
        self.server.routes[THUMBNAIL_PATH] = (  # type: ignore[attr-defined]
            404,
            "text/plain",
            b"not found",
        )

        result = self.check()

        self.assertFalse(result["verified"])
        self.assertIn("thumbnail asset HTTP 404", result["errors"])

    def test_missing_content_image_on_article_page_fails(self) -> None:
        self.server.routes["/article.html"] = (  # type: ignore[attr-defined]
            200,
            "text/html; charset=utf-8",
            ARTICLE_HTML.replace(CONTENT_IMAGE_PATH.encode(), b"/upload/other.webp"),
        )

        result = self.check()

        self.assertFalse(result["verified"])
        self.assertTrue(
            any(
                "missing content image paths on article page" in error
                for error in result["errors"]
            )
        )


if __name__ == "__main__":
    unittest.main()
