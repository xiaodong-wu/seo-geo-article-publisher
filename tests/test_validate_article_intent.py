from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_article.py"
SPEC = importlib.util.spec_from_file_location("validate_article_intent", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
validate_article = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_article)


CORE_KEYWORD = "thermal paper roll basics"


def valid_intent_analysis() -> dict[str, object]:
    accessed_at = date.today().isoformat()
    return {
        "core_keyword": CORE_KEYWORD,
        "primary_intent": "foundational-knowledge",
        "secondary_intent": "application-scenario",
        "keyword_signals": ["basics", "roll"],
        "intent_rationale": (
            "The query asks for a definition and operating principles before a "
            "purchase decision."
        ),
        "secondary_intent_rationale": (
            "Application examples clarify the main explanation without changing "
            "the article purpose."
        ),
        "rejected_intents": ["supplier-evaluation", "oem-odm"],
        "buyer_stage": "awareness",
        "buyer_stage_rationale": (
            "The wording shows early learning rather than supplier validation or inquiry."
        ),
        "editorial_stance": "neutral-buyer-guidance",
        "related_queries": [
            "how thermal receipt rolls work",
            "direct thermal coating applications",
        ],
        "related_keywords": [
            "receipt coating basics",
            "thermal print applications",
        ],
        "external_source_reason": "",
        "research_sources": [
            {
                "url": "https://example.com/products/thermal-roll/",
                "title": "Thermal Roll Product",
                "source_role": "site-product",
                "accessed_at": accessed_at,
                "freshness_note": "Current same-site product context",
            },
            {
                "url": "https://standards.example.org/thermal-media/",
                "title": "Thermal Media Background",
                "source_role": "industry-context",
                "accessed_at": accessed_at,
                "freshness_note": "Current technical background checked today",
            },
        ],
    }


class IntentSelectionTests(unittest.TestCase):
    def validate_data(
        self,
        value: dict[str, object],
        buyer_stage: str = "awareness",
    ) -> tuple[int, int, int, list[str], str, str, list[str]]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "intent-analysis.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return validate_article.validate_intent_analysis(
                path,
                CORE_KEYWORD,
                "foundational-knowledge",
                buyer_stage,
                "example.com",
            )

    def test_one_primary_and_one_subordinate_secondary_intent_pass(self) -> None:
        result = self.validate_data(valid_intent_analysis())

        self.assertEqual(result[4], "application-scenario")
        self.assertEqual(result[5], "awareness")
        self.assertEqual(result[6], [])

    def test_duplicate_intent_and_incompatible_stage_fail(self) -> None:
        value = valid_intent_analysis()
        value["secondary_intent"] = "foundational-knowledge"
        value["buyer_stage"] = "inquiry"
        value["editorial_stance"] = "brand-promotion"

        errors = self.validate_data(value, buyer_stage="inquiry")[6]

        self.assertTrue(any("must differ" in error for error in errors))
        self.assertTrue(any("incompatible" in error for error in errors))
        self.assertTrue(any("neutral-buyer-guidance" in error for error in errors))

    def test_awareness_lead_cannot_push_a_quote(self) -> None:
        content = (
            '<article class="article-content"><p>Request a quote for custom '
            "specifications before reviewing the product basics.</p></article>"
        )
        parser = validate_article.ArticleParser()
        parser.feed(content)
        parser.close()

        errors = validate_article.validate_article_ending(
            parser,
            content,
            "",
            "",
            "foundational-knowledge",
            "awareness",
            "informational-close",
        )[2]

        self.assertTrue(any("must not push a quote" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
