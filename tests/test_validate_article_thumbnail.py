from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_article.py"
SPEC = importlib.util.spec_from_file_location("validate_article_thumbnail", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
MINOR = "pass-with-minor-differences"


class ThumbnailToleranceTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in ("source.webp", "locked.png", "mask.png", "raw.png", "final.webp"):
            Image.new("RGB", (32, 32), "gray").save(self.root / name)
        (self.root / "prompt.txt").write_text("Preserve the referenced product.")
        (self.root / "lock.json").write_text(json.dumps({
            "source": str(self.root / "source.webp"),
            "mask": str(self.root / "mask.png"),
            "locked_product": str(self.root / "locked.png"),
            "product_rgb_repainted": False,
            "operation": "alpha-mask-extraction-only",
        }))
        record = {
            "classification": "product-present",
            "reference_urls": ["https://example.com/product.webp"],
            "reference_files": [str(self.root / "source.webp")],
            "output_file": str(self.root / "final.webp"),
            "retained_site_elements": ["Source logo and cabinet form"],
            "preservation_method": "source-product-locked-regeneration",
            "adaptation": {
                "new_image_generated": True,
                "adaptation_method": "locked-product-whole-image-regeneration",
                "source_product_locked": True,
                "whole_image_regenerated": True,
                "deterministic_composite_used": False,
                "source_canvas_reused_as_final": False,
                "scene_description": "Cabinet in a clean product showroom",
                "locked_product_file": str(self.root / "locked.png"),
                "lock_mask_file": str(self.root / "mask.png"),
                "lock_report_file": str(self.root / "lock.json"),
                "generated_asset_files": [str(self.root / "raw.png")],
                "prompt_file": str(self.root / "prompt.txt"),
            },
            "source_identity": {
                "brand_text": ["EXAMPLE"],
                "label_text": ["Model A"],
                "packaging_details": ["Gray cabinet with lower vent grille"],
            },
            "identity_checks": {
                "brand_text": "pass", "label_text": "pass",
                "packaging": "pass", "product_geometry": "pass",
            },
            "visual_inspection": {
                "comparison_mode": "side-by-side-100-percent",
                "source_vs_locked_product": "pass",
                "locked_product_vs_generated": "pass",
                "source_vs_final_webp": "pass",
            },
            "inspection_result": "pass",
        }
        self.value = {
            "site_has_product_visuals": True,
            "site_has_branded_product_visuals": True,
            "site_has_legible_product_labels": True,
            "thumbnail": copy.deepcopy(record),
            "body": [copy.deepcopy(record)],
        }

    def add_minor_review(self, record: dict | None = None) -> dict:
        if record is None:
            record = self.value["thumbnail"]
        record["inspection_result"] = MINOR
        record["identity_checks"]["packaging"] = MINOR
        record["identity_checks"]["product_geometry"] = MINOR
        record["visual_inspection"]["locked_product_vs_generated"] = MINOR
        record["visual_inspection"]["source_vs_final_webp"] = MINOR
        record["minor_difference_review"] = {
            "severity": "minor",
            "critical_identity_preserved": True,
            "differences": [{
                "aspect": "non-functional-detail",
                "description": "Handle reflection is a little brighter; its form is unchanged.",
            }],
            "acceptance_reason": "Brand, labels and all functional parts remain accurate.",
            "disclosure": "缩略图把手反光略亮，产品身份和功能结构未改变。",
        }
        return record

    def errors(self) -> list[str]:
        path = self.root / "image-references.json"
        path.write_text(json.dumps(self.value))
        # Candidate diversity is independent of the per-image acceptance gate under test.
        with patch.object(validator, "validate_image_selection", return_value=(0, 0, None, None, False, [])):
            return validator.validate_image_references(path, "example.com", 1)[-1]

    def test_exact_preservation_remains_accepted(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_documented_minor_thumbnail_differences_are_accepted(self) -> None:
        record = self.add_minor_review()
        for aspect in validator.THUMBNAIL_MINOR_DIFFERENCE_ASPECTS:
            with self.subTest(aspect=aspect):
                record["minor_difference_review"]["differences"][0]["aspect"] = aspect
                self.assertEqual(self.errors(), [])

    def test_review_requires_concrete_changes_reason_and_disclosure(self) -> None:
        record = self.add_minor_review()
        good = copy.deepcopy(record["minor_difference_review"])
        invalid_values = {
            "severity": "major", "critical_identity_preserved": False,
            "differences": [], "acceptance_reason": "", "disclosure": None,
        }
        for field, value in invalid_values.items():
            with self.subTest(field=field):
                record["minor_difference_review"] = {**good, field: value}
                self.assertTrue(any(field in error for error in self.errors()))
        record["minor_difference_review"] = {**good, "differences": [{"aspect": "model-number", "description": "Changed model."}]}
        self.assertTrue(any("aspect" in error for error in self.errors()))
        record["minor_difference_review"] = {**good, "differences": [{"aspect": "surface-lighting", "description": ""}]}
        self.assertTrue(any("description" in error for error in self.errors()))

    def test_undocumented_or_hidden_minor_differences_are_rejected(self) -> None:
        record = self.add_minor_review()
        review = record.pop("minor_difference_review")
        self.assertTrue(any("minor_difference_review" in error for error in self.errors()))
        record["minor_difference_review"] = review
        record["inspection_result"] = "pass"
        self.assertTrue(any("inspection_result" in error for error in self.errors()))

    def test_body_images_keep_strict_preservation(self) -> None:
        self.add_minor_review(self.value["body"][0])
        self.assertTrue(any("only for a product-present thumbnail" in error for error in self.errors()))

    def test_non_product_thumbnail_cannot_use_product_exception(self) -> None:
        self.add_minor_review()["classification"] = "non-product"
        self.assertTrue(any("only for a product-present thumbnail" in error for error in self.errors()))

    def test_brand_and_label_changes_cannot_use_exception(self) -> None:
        record = self.add_minor_review()
        for field in ("brand_text", "label_text"):
            for result in ("fail", MINOR):
                with self.subTest(field=field, result=result):
                    record["identity_checks"][field] = result
                    self.assertTrue(any(f"identity_checks.{field}" in error for error in self.errors()))
                    record["identity_checks"][field] = "pass"

    def test_failed_visual_checks_cannot_be_overridden_by_review(self) -> None:
        record = self.add_minor_review()
        for section, field in (("identity_checks", "product_geometry"), ("identity_checks", "packaging"), ("visual_inspection", "source_vs_final_webp"), ("visual_inspection", "locked_product_vs_generated")):
            with self.subTest(section=section, field=field):
                record[section][field] = "fail"
                self.assertTrue(any(f"{section}.{field}" in error for error in self.errors()))
                record[section][field] = MINOR

    def test_source_extraction_stays_strict(self) -> None:
        record = self.add_minor_review()
        record["visual_inspection"]["source_vs_locked_product"] = MINOR
        self.assertTrue(any("source_vs_locked_product" in error for error in self.errors()))

    def test_minor_review_does_not_bypass_generation_evidence(self) -> None:
        self.add_minor_review()["adaptation"]["deterministic_composite_used"] = True
        self.assertTrue(any("deterministic_composite_used" in error for error in self.errors()))


if __name__ == "__main__":
    unittest.main()
