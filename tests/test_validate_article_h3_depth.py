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


def h2(text: str) -> dict[str, str]:
    return {"tag": "h2", "id": "", "text": text}


def h3_section(
    text: str,
    parent_h2_index: int,
    characters: int = 200,
    block_count: int = 1,
    is_faq: bool = False,
) -> dict[str, object]:
    return {
        "text": text,
        "parent_h2_index": parent_h2_index,
        "parent_h2_text": "Parent",
        "is_faq": is_faq,
        "text_parts": ["x" * characters],
        "block_count": block_count,
    }


class NonFaqH3DepthTests(unittest.TestCase):
    def test_parser_separates_body_h3s_from_faq_questions(self) -> None:
        parser = validate_article.ArticleParser()
        parser.feed(
            f'''<article class="article-content">
              <h2>Material Decisions</h2>
              <h3>Match The Surface To The Process</h3><p>{"a" * 200}</p>
              <h3>Document Environmental Limits</h3><ul><li>{"b" * 200}</li></ul>
              <h2>Inspection Evidence</h2>
              <h3>Compare Samples Under One Method</h3><p>{"c" * 200}</p>
              <h3>Record Every Test Condition</h3><p>{"d" * 200}</p>
              <h2>Application Limits</h2>
              <h3>Check The Operating Environment</h3><p>{"e" * 200}</p>
              <h3>Match Constraints To The Specification</h3><p>{"f" * 200}</p>
              <h2>Frequently Asked Questions</h2>
              <h3>What Should A Sample Record Include?</h3><p>A clear answer.</p>
            </article>'''
        )
        parser.close()

        self.assertEqual(len(parser.h3_sections), 7)
        self.assertEqual(parser.faq_questions, 1)
        self.assertEqual(parser.h3_sections[0]["parent_h2_index"], 0)
        self.assertEqual(parser.h3_sections[4]["parent_h2_index"], 2)
        self.assertFalse(parser.h3_sections[4]["is_faq"])
        self.assertTrue(parser.h3_sections[6]["is_faq"])
        self.assertGreaterEqual(parser.h3_sections[0]["block_count"], 1)

        body_h2s = [
            heading for heading in parser.headings if heading["tag"] == "h2"
        ]
        result = validate_article.validate_non_faq_h3_depth(
            body_h2s,
            parser.h3_sections,
            11000,
        )

        self.assertEqual(result[:4], (6, 3, 3, 6))
        self.assertEqual(result[4], [])

    def test_longer_article_requires_more_h3s_and_parent_sections(self) -> None:
        h2s = [h2(f"Body Section {index}") for index in range(5)] + [h2("FAQ")]
        sections = [
            h3_section("First Detailed Finding", 0),
            h3_section("Second Detailed Finding", 1),
            h3_section("Third Detailed Finding", 2),
            h3_section("Fourth Detailed Finding", 3),
            h3_section("Fifth Detailed Finding", 0),
            h3_section("Sixth Detailed Finding", 1),
        ]

        result = validate_article.validate_non_faq_h3_depth(h2s, sections, 12500)

        self.assertEqual(result[:4], (6, 4, 4, 7))
        self.assertTrue(any("7–10 H3" in error for error in result[4]))

    def test_faq_h3s_do_not_satisfy_body_depth(self) -> None:
        h2s = [
            h2("Materials"),
            h2("Testing"),
            h2("Selection"),
            h2("Applications"),
            h2("FAQ"),
        ]
        sections = [
            h3_section(f"FAQ Question {index}", 4, is_faq=True)
            for index in range(4)
        ]

        result = validate_article.validate_non_faq_h3_depth(h2s, sections, 11000)

        self.assertEqual(result[0], 0)
        self.assertTrue(any("Non-FAQ body content" in error for error in result[4]))
        self.assertTrue(any("different non-FAQ H2" in error for error in result[4]))

    def test_shallow_duplicate_or_unstructured_h3_content_fails(self) -> None:
        h2s = [
            h2("Materials"),
            h2("Testing"),
            h2("Selection"),
            h2("Applications"),
            h2("FAQ"),
        ]
        sections = [
            h3_section("Specific Evidence", 0, characters=120),
            h3_section("Specific Evidence", 0),
            h3_section("Decision Limits", 1, block_count=0),
            h3_section("Packaging Evidence", 1),
            h3_section("Application Limits", 2),
            h3_section("Verification Records", 2),
        ]

        errors = validate_article.validate_non_faq_h3_depth(
            h2s,
            sections,
            11000,
        )[4]

        self.assertTrue(any("must be unique" in error for error in errors))
        self.assertTrue(any("at least 180 visible characters" in error for error in errors))
        self.assertTrue(any("at least one paragraph" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
