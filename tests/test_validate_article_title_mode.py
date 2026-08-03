from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_article = load_module(
    "validate_article_title_mode",
    ROOT / "scripts" / "validate_article.py",
)
select_title_mode = load_module(
    "select_title_mode",
    ROOT / "scripts" / "select_title_mode.py",
)


KEYWORD = "thermal paper manufacturers"


def seed_for_mode(mode: str) -> str:
    for index in range(1000):
        seed = f"run-1|example.com|{index}|{KEYWORD}"
        roll = validate_article.stable_percentage_roll(seed)
        if (roll < 70) == (mode == "question"):
            return seed
    raise AssertionError(f"Unable to find a deterministic {mode} seed")


class TitleModeTests(unittest.TestCase):
    def test_selector_and_validator_use_the_same_roll(self) -> None:
        for mode in ("question", "statement"):
            seed = seed_for_mode(mode)
            selected = select_title_mode.select_title_mode(seed)

            self.assertEqual(
                selected["roll"],
                validate_article.stable_percentage_roll(seed),
            )
            self.assertEqual(selected["title_mode"], mode)

    def test_question_roll_requires_a_natural_question_title(self) -> None:
        seed = seed_for_mode("question")
        title = "How Do Thermal Paper Manufacturers Verify Roll Consistency?"

        result = validate_article.validate_title_mode(title, KEYWORD, seed)

        self.assertEqual(result[1], "question")
        self.assertTrue(result[2])
        self.assertEqual(result[3], [])

    def test_statement_roll_rejects_a_question_title(self) -> None:
        seed = seed_for_mode("statement")
        title = "How Do Thermal Paper Manufacturers Verify Roll Consistency?"

        errors = validate_article.validate_title_mode(title, KEYWORD, seed)[3]

        self.assertTrue(any("requires a non-question title" in error for error in errors))

    def test_keyword_colon_prefix_is_rejected(self) -> None:
        seed = seed_for_mode("question")
        title = "Thermal Paper Manufacturers: How Is Roll Consistency Verified?"

        errors = validate_article.validate_title_mode(title, KEYWORD, seed)[3]

        self.assertTrue(any("colon or dash prefix" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
