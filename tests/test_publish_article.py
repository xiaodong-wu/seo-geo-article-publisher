from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from PIL import Image


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "publish_article.py"
SPEC = importlib.util.spec_from_file_location("publish_article", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)

HOST = "www.hoyinno.com"
ROUTE = "/index.php?m=autocreate&f=index&v=autocreate"
ENDPOINT = f"https://{HOST}{ROUTE}"


class EndpointValidationTests(unittest.TestCase):
    def test_builds_route_from_selected_site_host(self) -> None:
        for host in (HOST, "www.nutricdmo.com", "example.com"):
            with self.subTest(host=host):
                self.assertEqual(publisher.build_endpoint(host), f"https://{host}{ROUTE}")

    def test_equivalent_order_case_and_standard_port_are_canonicalized(self) -> None:
        for url in (
            ENDPOINT,
            f"https://{HOST}/index.php?v=autocreate&m=autocreate&f=index",
            f"https://WWW.HOYINNO.COM:443{ROUTE}",
        ):
            with self.subTest(url=url):
                self.assertEqual(publisher.validate_endpoint(url, False, HOST), ENDPOINT)

    def test_rejects_wrong_or_ambiguous_routes(self) -> None:
        invalid_routes = (
            "/index.php?m=seo_article",
            "/index.php?m=seo_article&f=index&v=autocreate",
            "/index.php?m=autocreate&f=other&v=autocreate",
            "/index.php?m=autocreate&f=index&v=other",
            "/index.php?m=autocreate&f=index",
            "/index.php?m=autocreate&f=index&v=",
            ROUTE + "&m=autocreate",
            ROUTE + "&m=seo_article",
            ROUTE + "&key=unexpected",
            ROUTE + "&",
            ROUTE + ";m=seo_article",
            ROUTE.replace("m=", "m[]=", 1),
            ROUTE.replace("m=", "%6d=", 1),
            ROUTE.replace("autocreate", "%61utocreate", 1),
            ROUTE.replace("autocreate", "auto+create", 1),
            ROUTE.replace("&f", "&amp;f"),
            ROUTE.replace("/index.php", "/other.php"),
            ROUTE.replace("/index.php", "/admin/index.php"),
            ROUTE.replace("/index.php", "/%69ndex.php"),
            ROUTE.replace("/index.php", "/index.php/"),
            ROUTE.replace("/index.php", "/index.php;extra"),
            ROUTE.replace("/index.php", "/index.php;"),
            ROUTE.replace("/index.php", "/INDEX.php"),
            ROUTE + "#ignored",
            ROUTE + "#",
        )
        for route in invalid_routes:
            with self.subTest(route=route), self.assertRaises(ValueError):
                publisher.validate_endpoint(f"https://{HOST}{route}", False, HOST)

    def test_rejects_wrong_host_transport_or_authority(self) -> None:
        urls = (
            f"https://www.nutricdmo.com{ROUTE}",
            f"https://hoyinno.com{ROUTE}",
            f"https://{HOST}.example.com{ROUTE}",
            f"https://{HOST}.{ROUTE}",
            f"http://{HOST}{ROUTE}",
            f"ftp://{HOST}{ROUTE}",
            f"https://{HOST}:8443{ROUTE}",
            f"https://{HOST}:invalid{ROUTE}",
            f"https://{HOST}:99999{ROUTE}",
            f"https://{HOST}:{ROUTE}",
            f"https://user:secret@{HOST}{ROUTE}",
            f"https://@{HOST}{ROUTE}",
            f" https://{HOST}{ROUTE}",
            f"https://{HOST}{ROUTE}\n",
            f"https://www.hoyi\tnno.com{ROUTE}",
            f"https://{HOST}\\{ROUTE}",
        )
        for url in urls:
            with self.subTest(url=url), self.assertRaises(ValueError):
                publisher.validate_endpoint(url, False, HOST)

    def test_rejects_url_components_in_site_host(self) -> None:
        for host in ("", "https://example.com", "example.com/path", "example.com:443",
                     "user@example.com", "example.com?m=other", "example.com#fragment",
                     "example.com ", "example.com\n", "example.com.", "example..com",
                     "-example.com", "example-.com", "exam_ple.com"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                publisher.build_endpoint(host)

    def test_local_test_exception_preserves_route_and_host_checks(self) -> None:
        for host in ("localhost", "127.0.0.1"):
            url = f"http://{host}:8765{ROUTE}"
            with self.subTest(host=host):
                self.assertEqual(publisher.validate_endpoint(url, True, host), url)
                with self.assertRaises(ValueError):
                    publisher.validate_endpoint(url, False, host)
                with self.assertRaises(ValueError):
                    publisher.validate_endpoint(url, True, HOST)
                with self.assertRaises(ValueError):
                    publisher.validate_endpoint(f"http://{host}:8765/index.php?m=seo_article", True, host)
        with self.assertRaises(ValueError):
            publisher.validate_endpoint(f"http://{HOST}{ROUTE}", True, HOST)
        with self.assertRaises(ValueError):
            publisher.validate_endpoint(f"http://localhost:0{ROUTE}", True, "localhost")

    def test_check_endpoint_does_not_read_files_prompt_or_send_network(self) -> None:
        with mock.patch.object(sys, "argv", [str(SCRIPT_PATH), "--site-host", HOST, "--check-endpoint"]), \
             mock.patch.object(publisher, "read_text") as read_text, \
             mock.patch.object(publisher.getpass, "getpass") as prompt, \
             mock.patch.object(publisher.requests, "Session") as session, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(publisher.main(), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["endpoint"], ENDPOINT)
        self.assertTrue(result["valid"])
        self.assertFalse(result["network_request_sent"])
        read_text.assert_not_called()
        prompt.assert_not_called()
        session.assert_not_called()

    def test_bad_route_stops_before_files_credentials_and_network_in_both_modes(self) -> None:
        argv = [str(SCRIPT_PATH), "--site-host", HOST, "--endpoint",
                f"https://{HOST}/index.php?m=seo_article"]
        for flag in ("--title-file", "--seo-title-file", "--remark-file", "--seo-desc-file", "--content-file", "--thumb"):
            argv.extend([flag, "/nonexistent/publisher-test-input"])
        for mode in ([], ["--dry-run"]):
            with self.subTest(mode=mode), \
                 mock.patch.object(sys, "argv", argv + mode), \
                 mock.patch.object(publisher, "read_text") as read_text, \
                 mock.patch.object(publisher.getpass, "getpass") as prompt, \
                 mock.patch.object(publisher.requests, "Session") as session:
                with self.assertRaisesRegex(ValueError, "Publishing route"):
                    publisher.main()
                read_text.assert_not_called()
                prompt.assert_not_called()
                session.assert_not_called()

    def test_cli_bad_route_exits_nonzero_without_echoing_sensitive_query(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--site-host", HOST, "--check-endpoint",
             "--endpoint", f"https://{HOST}/index.php?m=seo_article&key=do-not-echo"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Publishing route", result.stderr)
        self.assertNotIn("do-not-echo", result.stdout + result.stderr)


class PublishingHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.server.requests_seen.append(("POST", self.path, body))
        status = self.server.publish_status
        self.send_response(status)
        if 300 <= status < 400:
            self.send_header("Location", "/index.php?m=seo_article")
        payload = json.dumps({"code": 0, "data": {
            "id": 1, "article_url": "http://localhost/article.html",
            "thumb_path": "/thumb.webp", "content_images": [],
        }}).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        self.server.requests_seen.append(("GET", self.path, b""))
        self.send_response(405)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


class PublishingBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="publisher-route-test-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.argv = [str(SCRIPT_PATH), "--site-host", "127.0.0.1", "--allow-http-localhost",
                     "--api-key-env", "PUBLISHER_TEST_KEY"]
        fixtures = {"title-file": "Route validation test", "seo-title-file": "Route validation test",
                    "remark-file": "Local test only.", "seo-desc-file": "Local test only.",
                    "content-file": "<article>[IMAGE_BASE64][IMAGE_BASE64]</article>"}
        for flag, value in fixtures.items():
            path = root / f"{flag}.txt"
            path.write_text(value, encoding="utf-8")
            self.argv.extend(["--" + flag, str(path)])
        for index, flag in enumerate(("--thumb", "--content-image", "--content-image")):
            path = root / f"fixture-{index}.webp"
            Image.new("RGB", (8, 8), "white").save(path, "WEBP")
            self.argv.extend([flag, str(path)])
            if flag == "--content-image":
                self.argv.extend(["--content-image-alt", f"Test image {index}"])
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), PublishingHandler)
        self.server.requests_seen = []
        self.server.publish_status = 200
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = f"http://127.0.0.1:{self.server.server_port}{ROUTE}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def run_main(self, *extra: str) -> dict:
        with mock.patch.object(sys, "argv", self.argv + list(extra)), \
             mock.patch.dict(os.environ, {"PUBLISHER_TEST_KEY": "local-test-only"}), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(publisher.main(), 0)
        return json.loads(output.getvalue())

    def test_valid_route_sends_one_multipart_post_to_exact_path(self) -> None:
        result = self.run_main("--endpoint", self.endpoint)
        self.assertEqual(result["article_id"], 1)
        self.assertEqual(result["endpoint"], self.endpoint)
        self.assertEqual(len(self.server.requests_seen), 1)
        method, path, body = self.server.requests_seen[0]
        self.assertEqual((method, path), ("POST", ROUTE))
        self.assertIn(b'name="thumb"', body)
        self.assertEqual(body.count(b'name="content_img[]"'), 2)
        self.assertEqual(body.count(b'name="content_img_alt[]"'), 2)

    def test_invalid_route_sends_no_request_to_local_server(self) -> None:
        bad = self.endpoint.replace("m=autocreate", "m=seo_article")
        with self.assertRaisesRegex(ValueError, "Publishing route"):
            self.run_main("--endpoint", bad)
        self.assertEqual(self.server.requests_seen, [])

    def test_dry_run_defaults_to_generated_route_without_network(self) -> None:
        result = self.run_main("--dry-run")
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["endpoint"], f"https://127.0.0.1{ROUTE}")
        self.assertEqual(result["route_validation"], "passed")
        self.assertEqual(self.server.requests_seen, [])

    def test_redirects_never_replay_post_or_follow_with_get(self) -> None:
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                self.server.publish_status = status
                self.server.requests_seen.clear()
                with self.assertRaisesRegex(RuntimeError, "redirect not followed"):
                    self.run_main("--endpoint", self.endpoint)
                self.assertEqual(len(self.server.requests_seen), 1)
                self.assertEqual(self.server.requests_seen[0][:2], ("POST", ROUTE))


if __name__ == "__main__":
    unittest.main()
