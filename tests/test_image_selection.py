from __future__ import annotations

import copy
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


selection = load("image_selection")
HOST = "www.example.com"
BASE = f"https://{HOST}"
REASON = "Inspected product identity and article section support this placement."


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class ImageSelectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.runs = Path(temporary.name) / "article-runs"
        self.row = self.runs / "current-run" / "example-row-1"
        self.row.mkdir(parents=True)
        self.path = self.row / "image-references.json"
        self.discovery_path = self.row / "product-discovery.json"
        self.history_path = self.row / "image-history.json"
        self.product_page = BASE + "/product.html"
        self.scene_page = BASE + "/factory.html"
        hashes = ["0000000000000000", "FFFFFFFF00000000", "00000000FFFFFFFF",
                  "FFFF0000FFFF0000", "FF00FF00FF00FF00", "F0F0F0F0F0F0F0F0"]
        pool = []
        for index, cid in enumerate(["product-a", "product-b", "product-c", "lab", "line", "pack"]):
            source = self.row / "source" / f"{cid}.webp"
            source.parent.mkdir(exist_ok=True)
            source.write_bytes(f"unique image fixture {index}".encode())
            product = index < 3
            pool.append(dict(candidate_id=cid, reference_url=f"{BASE}/{cid}.webp",
                reference_file=str(source), source_sha256=selection.digest(source),
                perceptual_hash=hashes[index], width=64, height=64,
                classification="product-present" if product else "non-product",
                source_page_url=self.product_page if product else self.scene_page,
                product_url=self.product_page if product else "",
                topic_relation="primary-topic" if product else "supporting-context",
                relevance_reason=REASON, eligible_for_product_lock=product,
                article_relevance="exact-product" if product else "supporting-site-scene",
                view_angle="front" if product else "environmental", scene_type="product-hero" if product else "factory-production",
                label_legibility="clear" if product else "not-applicable", identity_summary=REASON))
        self.discovery = dict(run_id="current-run", site_host=HOST, coverage_status="complete", coverage_gaps=[],
            matches=[dict(url=self.product_page, relevance="exact-product", gallery_image_urls=[c["reference_url"] for c in pool[:3]])])
        reviews = []
        for page, sources in [(self.product_page, pool[:3]), (self.scene_page, pool[3:])]:
            evidence = self.row / ("product.html" if page == self.product_page else "factory.html")
            evidence.write_text("Current-run gallery evidence fixture")
            reviews.append(dict(page_url=page, run_id="current-run", evidence_file=str(evidence), inspection_complete=True,
                gallery_image_urls=[c["reference_url"] for c in sources], images=[dict(reference_url=c["reference_url"],
                decision="candidate", candidate_id=c["candidate_id"], eligible_for_product_lock=c["eligible_for_product_lock"],
                topic_relation=c["topic_relation"], reason=REASON) for c in sources]))
        (self.row / "archive.html").write_text("Current-run archive evidence fixture")
        roles = ["product-hero", "product-detail", "laboratory-quality", "factory-production", "packaging-logistics"]
        slots = [dict(slot="thumbnail" if i == 0 else f"body-{i:02d}", article_role=role, section_topic="Inspected article section purpose") for i, role in enumerate(roles)]
        matrix = []
        for index, slot in enumerate(slots):
            for c in pool:
                eligible = (index < 2 and c["classification"] == "product-present") or (index >= 2 and c["candidate_id"] == ["lab", "line", "pack"][index-2])
                fields = [f for f in selection.WEIGHTS if f != "diversity"]
                matrix.append(dict(slot=slot["slot"], candidate_id=c["candidate_id"], eligible=eligible,
                    eligibility_reason=REASON, scores={f:90 for f in fields}, score_evidence={f:REASON for f in fields}))
        self.value = dict(site_has_product_visuals=True, topic_product_visuals=True, candidate_pool=pool,
            selection_context=dict(policy=selection.POLICY, run_id="current-run", product_discovery_file=str(self.discovery_path),
                image_history_file=str(self.history_path), gallery_reviews=reviews,
                live_archive_review=dict(run_id="current-run", url=BASE+"/news/", evidence_file="archive.html", coverage_note=REASON)),
            selection_plan=dict(slots=slots, candidate_slot_scores=matrix, duplicate_exception=None))
        self.save_discovery()
        self.refresh_history()

    def save_discovery(self):
        write(self.discovery_path, self.discovery)
        self.value["selection_context"]["product_discovery_sha256"] = selection.digest(self.discovery_path)

    def refresh_history(self):
        write(self.history_path, selection.make_history(self.runs, HOST, "current-run"))

    def publish_record(self, run_id="old-run", cid="product-a", url=None, state="published", created="2026-09-23 09:00:00"):
        row = self.runs / run_id / "row"
        candidate = copy.deepcopy(next(c for c in self.value["candidate_pool"] if c["candidate_id"] == cid))
        image = dict(candidate_id=cid, classification=candidate["classification"], reference_urls=[candidate["reference_url"]])
        write(row / "image-references.json", dict(candidate_pool=[candidate], thumbnail=image, body=[image]))
        site = dict(tab=HOST, state=state, row_directory=str(row), article_url=url or BASE+f"/{run_id}.html",
            selected_product_urls=[self.product_page], publishing_key="fixture-secret-never-copy")
        if state != "failed":
            site["api_result"] = dict(article_id=7, created_at=created)
        write(row.parent / "manifest.json", dict(run_id=run_id, started_at=created, sites=[site]))
        return row

    def plan(self):
        self.value["selection_plan"] = selection.compute_plan(self.value, self.row, HOST)
        return self.value["selection_plan"]

    def assert_rejected(self, text):
        errors = selection.validate_selection_evidence(self.value, self.path, HOST)
        self.assertTrue(any(text in error for error in errors), errors)

    def remove_candidate(self, cid, disposition="shortlisted-out"):
        self.value["candidate_pool"] = [c for c in self.value["candidate_pool"] if c["candidate_id"] != cid]
        self.value["selection_plan"]["candidate_slot_scores"] = [s for s in self.value["selection_plan"]["candidate_slot_scores"] if s["candidate_id"] != cid]
        for review in self.value["selection_context"]["gallery_reviews"]:
            for item in review["images"]:
                if item.get("candidate_id") == cid:
                    item["decision"] = disposition
                    if disposition == "excluded":
                        item["eligible_for_product_lock"] = False

    def test_fresh_plan_has_unique_sources_and_validates(self):
        plan = self.plan()
        self.assertEqual(len({s["candidate_id"] for s in plan["slots"]}), 5)
        self.assertEqual(selection.validate_selection_evidence(self.value, self.path, HOST), [])

    def test_recent_source_rotates_to_equally_relevant_alternatives(self):
        self.publish_record()
        self.refresh_history()
        plan = self.plan()
        selected = [s["candidate_id"] for s in plan["slots"]]
        self.assertNotIn("product-a", selected)
        self.assertEqual(selected[:2], ["product-b", "product-c"])
        self.assertEqual(selection.validate_selection_evidence(self.value, self.path, HOST), [])

    def test_rotation_does_not_override_primary_relevance(self):
        self.publish_record()
        self.refresh_history()
        for item in self.value["selection_plan"]["candidate_slot_scores"]:
            if item["slot"] == "thumbnail" and item["candidate_id"] in {"product-b", "product-c"}:
                item["scores"]["keyword_product_relevance"] = 70
        self.assertEqual(self.plan()["slots"][0]["candidate_id"], "product-a")

    def test_history_deduplicates_articles_and_excludes_failed_rows_and_secrets(self):
        self.publish_record()
        self.publish_record("retry-run", url=BASE+"/old-run.html")
        self.publish_record("failed-run", state="failed")
        history = selection.make_history(self.runs, HOST, "current-run")
        self.assertEqual(len(history["articles"]), 1)
        usage = selection.usage(self.value["candidate_pool"][0], history["articles"])
        self.assertEqual(usage["source_article_uses"], 1)
        self.assertEqual(usage["diversity"], 55)
        self.assertNotIn("fixture-secret", json.dumps(history))

    def test_history_counts_pending_api_success_and_sorts_mixed_timestamps(self):
        self.publish_record("pending-run", state="pending-manual-check", created="2026-09-24T01:00:00+00:00")
        self.publish_record("later-run", cid="product-b", created="2026-09-24 10:00:00")
        history = selection.make_history(self.runs, HOST, "current-run")
        self.assertEqual([a["run_id"] for a in history["articles"]], ["later-run", "pending-run"])

    def test_history_is_limited_to_twenty_same_site_articles(self):
        for i in range(22):
            self.publish_record(f"old-{i:02d}", created=f"2026-09-{i+1:02d} 09:00:00")
        articles = selection.make_history(self.runs, HOST, "current-run")["articles"]
        self.assertEqual(len(articles), 20)
        self.assertEqual(articles[0]["run_id"], "old-21")
        self.assertEqual(articles[-1]["run_id"], "old-02")

    def test_missing_historical_sources_are_disclosed(self):
        row = self.publish_record()
        (row / "image-references.json").unlink()
        history = selection.make_history(self.runs, HOST, "current-run")
        self.assertIn("history_gap", history["articles"][0])
        self.assertEqual(history["articles"][0]["images"], [])

    def test_source_matching_survives_renamed_urls_and_near_duplicates(self):
        original = self.value["candidate_pool"][0]
        renamed = {**original, "reference_url": BASE+"/renamed.webp"}
        self.assertTrue(selection.same_source(renamed, original))
        near = {**renamed, "source_sha256": "changed", "perceptual_hash": "000000000000000F"}
        self.assertTrue(selection.same_source(near, original))
        self.assertFalse(selection.same_source(self.value["candidate_pool"][1], original))

    def test_different_view_of_used_product_gets_only_product_penalty(self):
        self.publish_record()
        articles = selection.make_history(self.runs, HOST, "current-run")["articles"]
        use = selection.usage(self.value["candidate_pool"][1], articles)
        self.assertEqual(use["source_article_uses"], 0)
        self.assertEqual(use["product_article_uses"], 1)
        self.assertEqual(use["diversity"], 95)

    def test_old_metadata_and_wrong_run_are_rejected(self):
        context = self.value.pop("selection_context")
        self.assert_rejected("legacy pools must be rebuilt")
        self.value["selection_context"] = context
        context["run_id"] = "previous-run"
        self.assert_rejected("current run directory")

    def test_borrowed_candidate_file_is_rejected(self):
        old_file = self.runs / "old-source.webp"
        old_file.write_bytes(Path(self.value["candidate_pool"][0]["reference_file"]).read_bytes())
        self.value["candidate_pool"][0]["reference_file"] = str(old_file)
        self.assert_rejected("not borrowed from an old pool")

    def test_changed_source_or_discovery_digest_is_rejected(self):
        Path(self.value["candidate_pool"][0]["reference_file"]).write_bytes(b"changed")
        self.assert_rejected("Candidate source digest")
        self.discovery_path.write_text("{}")
        self.assert_rejected("Product discovery digest")

    def test_omitted_gallery_and_gallery_images_are_rejected(self):
        reviews = self.value["selection_context"]["gallery_reviews"]
        removed = reviews.pop(0)
        self.assert_rejected("Every relevant discovered product gallery")
        reviews.insert(0, removed)
        removed["gallery_image_urls"].pop()
        self.assert_rejected("omits discovered product images")

    def test_every_gallery_image_requires_disposition(self):
        self.value["selection_context"]["gallery_reviews"][0]["images"].pop()
        self.assert_rejected("Every gallery image needs")

    def test_shortlisting_away_other_usable_views_cannot_allow_reuse(self):
        self.remove_candidate("product-b")
        self.remove_candidate("product-c")
        self.assert_rejected("No distinct relevant assignment")

    def test_true_single_source_allows_two_slots_only_with_complete_coverage(self):
        self.remove_candidate("product-b", "excluded")
        self.remove_candidate("product-c", "excluded")
        self.assertEqual([s["candidate_id"] for s in self.plan()["slots"][:2]], ["product-a", "product-a"])
        # Identity/composition exception evidence remains enforced by validate_article.py.
        self.assertEqual(selection.validate_selection_evidence(self.value, self.path, HOST), [])
        self.discovery["coverage_status"] = "incomplete"
        self.save_discovery()
        self.assert_rejected("catalogue access gaps")

    def test_eligible_image_cannot_be_hidden_as_excluded(self):
        self.value["selection_context"]["gallery_reviews"][0]["images"][1]["decision"] = "excluded"
        self.assert_rejected("cannot be silently excluded")

    def test_no_primary_product_cannot_be_claimed_by_omitting_all_views(self):
        for cid in ["product-a", "product-b", "product-c"]:
            self.remove_candidate(cid)
        self.value["topic_product_visuals"] = False
        self.assert_rejected("cannot all be omitted")

    def test_comparison_product_cannot_be_main_thumbnail(self):
        self.value["candidate_pool"][0]["topic_relation"] = "comparison-only"
        self.value["selection_context"]["gallery_reviews"][0]["images"][0]["topic_relation"] = "comparison-only"
        self.assert_rejected("Comparison-only product")

    def test_no_primary_product_can_use_context_thumbnail_and_comparison_body(self):
        for c in self.value["candidate_pool"][:3]:
            c["topic_relation"] = "comparison-only"
        for item in self.value["selection_context"]["gallery_reviews"][0]["images"]:
            item["topic_relation"] = "comparison-only"
        self.value.update(topic_product_visuals=False, no_topic_product_visual_reason=REASON)
        self.value["selection_plan"]["slots"] = self.value["selection_plan"]["slots"][:2]
        self.value["selection_plan"]["candidate_slot_scores"] = [item for item in self.value["selection_plan"]["candidate_slot_scores"] if item["slot"] in {"thumbnail", "body-01"}]
        for item in self.value["selection_plan"]["candidate_slot_scores"]:
            if item["slot"] == "thumbnail":
                item["eligible"] = item["candidate_id"] == "lab"
        plan = self.plan()
        self.assertEqual(plan["slots"][0]["candidate_id"], "lab")
        self.assertEqual(plan["slots"][1]["candidate_id"], "product-a")

    def test_fixed_diversity_or_forged_assignment_is_rejected(self):
        self.plan()
        self.value["selection_plan"]["candidate_slot_scores"][0]["scores"]["diversity"] = 90
        self.assert_rejected("candidate_slot_scores differs")
        self.plan()
        self.value["selection_plan"]["slots"][0]["candidate_id"] = "product-c"
        self.assert_rejected("slots differs")

    def test_missing_matrix_pair_or_score_evidence_is_rejected(self):
        matrix = self.value["selection_plan"]["candidate_slot_scores"]
        item = matrix.pop()
        self.assert_rejected("Score every candidate")
        matrix.append(item)
        item["score_evidence"]["section_fit"] = ""
        self.assert_rejected("Missing inspected score evidence")

    def test_new_publication_or_manually_emptied_history_is_rejected(self):
        self.plan()
        self.publish_record()
        self.assert_rejected("history is stale or incomplete")
        self.refresh_history()
        self.plan()
        history = selection.read(self.history_path)
        history["articles"] = []
        write(self.history_path, history)
        self.assert_rejected("history is stale or incomplete")

    def test_cli_computes_plan_and_keeps_identity_records(self):
        self.value["thumbnail"] = {"identity_fixture": "must be preserved"}
        write(self.path, self.value)
        result = subprocess.run([sys.executable, str(SCRIPTS / "image_selection.py"), "plan",
            "--site-host", HOST, "--image-reference-file", str(self.path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = selection.read(self.path)
        self.assertEqual(output["thumbnail"], self.value["thumbnail"])
        self.assertEqual(output["selection_plan"]["policy"], selection.POLICY)

    def test_article_validator_accepts_computed_plan_and_blocks_legacy_pool(self):
        from PIL import Image
        validator = load("validate_article")
        for index, c in enumerate(self.value["candidate_pool"]):
            rng = random.Random(index)
            image = Image.frombytes("RGB", (64, 64), rng.randbytes(64*64*3))
            image.save(c["reference_file"], format="PNG")
            sha, phash, width, height = validator.image_fingerprint(Path(c["reference_file"]))
            c.update(source_sha256=sha, perceptual_hash=phash, width=width, height=height)
        plan = self.plan()
        pool = {c["candidate_id"]:c for c in self.value["candidate_pool"]}
        records = []
        for slot in plan["slots"]:
            c = pool[slot["candidate_id"]]
            records.append(dict(candidate_id=c["candidate_id"], classification=c["classification"],
                reference_urls=[c["reference_url"]], reference_files=[c["reference_file"]], output_file=c["reference_file"]))
        errors = validator.validate_image_selection(self.value, self.path, HOST, 4, records[0], records[1:])[-1]
        self.assertEqual(errors, [])
        del self.value["selection_context"]
        errors = validator.validate_image_selection(self.value, self.path, HOST, 4, records[0], records[1:])[-1]
        self.assertTrue(any("legacy pools must be rebuilt" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
