from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_article.py"
SPEC = importlib.util.spec_from_file_location("validate_article", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
validate_article = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_article)


CORE_KEYWORD = "direct thermal paper manufacturers"
RELATED_KEYWORDS = [
    "receipt roll quality control",
    "thermal media storage",
]


def visible_text_with_word_count(blocks: list[str], total_words: int) -> str:
    text = " ".join(blocks)
    current_words = len(validate_article.WORD_RE.findall(text))
    if current_words > total_words:
        raise ValueError("Requested word count is shorter than the supplied blocks")
    return f"{text} {'context ' * (total_words - current_words)}".strip()


class KeywordUsageTests(unittest.TestCase):
    def test_exact_phrase_count_uses_word_boundaries(self) -> None:
        text = (
            "Direct thermal paper manufacturers qualify rolls. "
            "Notdirect thermal paper manufacturersx is not an exact phrase. "
            "DIRECT THERMAL PAPER MANUFACTURERS document changes."
        )

        self.assertEqual(
            validate_article.count_exact_phrase(text, CORE_KEYWORD),
            2,
        )

    def test_valid_keyword_distribution_passes(self) -> None:
        blocks = [
            f"{CORE_KEYWORD} connect printer limits with receipt roll quality control.",
            f"A second review by {CORE_KEYWORD} should define thermal media storage.",
            "Document receipt roll quality control before repeat production.",
            f"Qualified {CORE_KEYWORD} identify every proposed deviation.",
        ]

        metrics, errors = validate_article.validate_keyword_usage(
            blocks,
            visible_text_with_word_count(blocks, 1000),
            CORE_KEYWORD,
            RELATED_KEYWORDS,
        )

        self.assertEqual(metrics["core_keyword_occurrences"], 3)
        self.assertEqual(metrics["core_keyword_blocks"], 3)
        self.assertEqual(metrics["core_keyword_weighted_words"], 12)
        self.assertEqual(
            metrics["related_keyword_occurrences"]["receipt roll quality control"],
            2,
        )
        self.assertEqual(
            metrics["related_keyword_occurrences"]["thermal media storage"],
            1,
        )
        self.assertEqual(metrics["related_keyword_occurrences_total"], 3)
        self.assertEqual(metrics["related_keyword_weighted_words"], 11)
        self.assertEqual(metrics["visible_word_count"], 1000)
        self.assertEqual(metrics["keyword_weighted_words"], 23)
        self.assertEqual(metrics["keyword_density_percent"], 2.3)
        self.assertEqual(errors, [])

    def test_core_keyword_repetition_in_one_block_fails(self) -> None:
        blocks = [
            f"{CORE_KEYWORD} compare {CORE_KEYWORD} in one paragraph.",
            f"Qualified {CORE_KEYWORD} document controls.",
            "Receipt roll quality control supports thermal media storage.",
            "Receipt roll quality control should be recorded.",
        ]

        _, errors = validate_article.validate_keyword_usage(
            blocks,
            visible_text_with_word_count(blocks, 1000),
            CORE_KEYWORD,
            RELATED_KEYWORDS,
        )

        self.assertTrue(
            any("must not appear more than once" in error for error in errors)
        )
        self.assertTrue(
            any("at least two later content blocks" in error for error in errors)
        )

    def test_missing_related_keyword_fails(self) -> None:
        blocks = [
            f"{CORE_KEYWORD} define receipt roll quality control.",
            f"Qualified {CORE_KEYWORD} audit receipt roll quality control.",
            f"Compare {CORE_KEYWORD} through documented acceptance criteria.",
        ]

        _, errors = validate_article.validate_keyword_usage(
            blocks,
            visible_text_with_word_count(blocks, 1000),
            CORE_KEYWORD,
            RELATED_KEYWORDS,
        )

        self.assertTrue(
            any(
                '"thermal media storage" must appear at least once' in error
                for error in errors
            )
        )

    def test_keyword_density_below_one_percent_fails(self) -> None:
        blocks = [
            f"{CORE_KEYWORD} connect printer limits with receipt roll quality control.",
            f"A second review by {CORE_KEYWORD} should define thermal media storage.",
            "Document receipt roll quality control before repeat production.",
            f"Qualified {CORE_KEYWORD} identify every proposed deviation.",
        ]

        metrics, errors = validate_article.validate_keyword_usage(
            blocks,
            visible_text_with_word_count(blocks, 3000),
            CORE_KEYWORD,
            RELATED_KEYWORDS,
        )

        self.assertLess(metrics["keyword_density_percent"], 1.0)
        self.assertTrue(any("must be 1.00%–3.00%" in error for error in errors))

    def test_keyword_density_above_three_percent_fails(self) -> None:
        blocks = [
            f"{CORE_KEYWORD} connect printer limits with receipt roll quality control.",
            f"A second review by {CORE_KEYWORD} should define thermal media storage.",
            "Document receipt roll quality control before repeat production.",
            f"Qualified {CORE_KEYWORD} identify every proposed deviation.",
        ]

        metrics, errors = validate_article.validate_keyword_usage(
            blocks,
            visible_text_with_word_count(blocks, 500),
            CORE_KEYWORD,
            RELATED_KEYWORDS,
        )

        self.assertGreater(metrics["keyword_density_percent"], 3.0)
        self.assertTrue(any("must be 1.00%–3.00%" in error for error in errors))

    def test_related_keywords_cannot_overlap_core_or_each_other(self) -> None:
        related, errors = validate_article.validate_related_keywords(
            ["thermal paper manufacturers", "thermal paper manufacturers quality"],
            CORE_KEYWORD,
        )

        self.assertEqual(len(related), 2)
        self.assertTrue(any("core keyword" in error for error in errors))
        self.assertTrue(any("contain one another" in error for error in errors))

    def test_parser_counts_visible_blocks_not_css_or_attributes(self) -> None:
        parser = validate_article.ArticleParser()
        parser.feed(
            f'''<style data-article-style="responsive-v1">.{CORE_KEYWORD} {{}}</style>
            <article class="article-content" data-note="{CORE_KEYWORD}">
              <p><a href="https://example.com/{CORE_KEYWORD}">{CORE_KEYWORD}</a>
              defines receipt roll quality control.</p>
              <h2>Thermal Media Storage</h2>
            </article>'''
        )
        parser.close()

        self.assertEqual(len(parser.content_blocks), 2)
        self.assertEqual(
            sum(
                validate_article.count_exact_phrase(block, CORE_KEYWORD)
                for block in parser.content_blocks
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
