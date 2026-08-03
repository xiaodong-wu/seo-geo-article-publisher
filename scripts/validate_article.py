#!/usr/bin/env python3
"""Validate one SEO/GEO article, title diversity, and ordered image metadata."""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
import re
import statistics
import sys
from collections import Counter
from datetime import date
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageOps


ANCHOR_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'’/-]*")
SPACE_RE = re.compile(r"\s+")
PLACEHOLDER = "[IMAGE_BASE64]"
STYLE_VERSION = "responsive-v1"
QUESTION_TITLE_PROBABILITY = 70
ARTICLE_MIN_VISIBLE_CHARACTERS = 10000
ARTICLE_PREFERRED_MIN_VISIBLE_CHARACTERS = 12000
ARTICLE_PREFERRED_MAX_VISIBLE_CHARACTERS = 13500
ARTICLE_MAX_VISIBLE_CHARACTERS = 15000
KEYWORD_DENSITY_MIN_PERCENT = 1.0
KEYWORD_DENSITY_MAX_PERCENT = 3.0
NON_FAQ_H3_MIN_CONTENT_CHARACTERS = 180
NON_FAQ_H3_MAX_COUNT = 10
FAQ_HEADING_TEXTS = {
    "faq",
    "faqs",
    "frequently asked questions",
}
ARTICLE_KEYWORD_BLOCK_TAGS = {
    "p",
    "h2",
    "h3",
    "li",
    "th",
    "td",
    "figcaption",
}
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
THEME_COLOR_VARIABLES = (
    "--article-accent",
    "--article-accent-dark",
    "--article-text",
    "--article-muted",
    "--article-border",
    "--article-soft",
    "--article-surface",
    "--article-table-header",
    "--article-table-header-text",
    "--article-table-stripe",
    "--article-table-hover",
)
THEME_EVIDENCE_TYPES = {
    "computed-style",
    "stylesheet",
    "logo",
}
THEME_EVIDENCE_ROLES = {
    "primary-accent",
    "secondary-accent",
    "body-text",
    "muted-text",
    "border",
    "surface",
}
PRODUCT_PRESERVATION_METHODS = {
    "source-product-locked-regeneration",
}
PRODUCT_ADAPTATION_METHODS = {
    "source-product-locked-regeneration": (
        "locked-product-whole-image-regeneration"
    ),
}
NOT_VISIBLE = "not-visible-in-reference"
IMAGE_VIEW_ANGLES = {
    "front",
    "three-quarter",
    "side",
    "top",
    "detail",
    "group",
    "environmental",
    "not-applicable",
}
IMAGE_SCENE_TYPES = {
    "product-hero",
    "product-detail",
    "factory-production",
    "laboratory-quality",
    "application-use",
    "packaging-logistics",
    "warehouse-supply",
    "service-process",
}
IMAGE_ARTICLE_ROLES = {
    "product-hero",
    "product-detail",
    "inspection-comparison",
    "factory-production",
    "laboratory-quality",
    "application-use",
    "packaging-logistics",
    "warehouse-supply",
}
IMAGE_LABEL_LEGIBILITY = {
    "clear",
    "partial",
    "none",
    "not-applicable",
}
IMAGE_ARTICLE_RELEVANCE = {
    "exact-product",
    "same-product-family",
    "supporting-site-scene",
}
IMAGE_SCORE_WEIGHTS = {
    "keyword_product_relevance": 0.30,
    "identity_clarity": 0.25,
    "image_quality": 0.15,
    "section_fit": 0.15,
    "diversity": 0.15,
}
SOURCE_NEAR_DUPLICATE_DISTANCE = 6
FINAL_IMAGE_MINIMUM_DISTANCE = 10
REUSED_SOURCE_FINAL_MINIMUM_DISTANCE = 12
TITLE_ANGLES = {
    "product-education",
    "feature-analysis",
    "application",
    "comparison",
    "selection",
    "specification",
    "process",
    "problem-solution",
    "quality-control",
    "customization",
    "troubleshooting",
}
TITLE_PATTERNS = {
    "direct-statement",
    "question",
    "how-to",
    "comparison",
    "numbered-list",
    "decision-guide",
    "technical-explainer",
    "risk-led",
    "benefit-led",
}
QUESTION_TITLE_PATTERNS = TITLE_PATTERNS - {"direct-statement"}
STATEMENT_TITLE_PATTERNS = TITLE_PATTERNS - {"question"}
SEARCH_INTENTS = {
    "foundational-knowledge",
    "product-selection",
    "product-comparison",
    "oem-odm",
    "supplier-evaluation",
    "application-scenario",
    "problem-solving",
}
BUYER_STAGES = {
    "awareness",
    "consideration",
    "evaluation",
    "inquiry",
}
BUYER_STAGE_ENDING_MODES = {
    "awareness": {"informational-close"},
    "consideration": {"informational-close", "inline-cta"},
    "evaluation": {"informational-close", "inline-cta"},
    "inquiry": {"inline-cta", "standalone-cta"},
}
SEARCH_INTENT_BUYER_STAGES = {
    "foundational-knowledge": {"awareness", "consideration"},
    "product-selection": {"consideration", "evaluation", "inquiry"},
    "product-comparison": {"consideration", "evaluation"},
    "oem-odm": {"consideration", "evaluation", "inquiry"},
    "supplier-evaluation": {"consideration", "evaluation", "inquiry"},
    "application-scenario": {"awareness", "consideration", "evaluation"},
    "problem-solving": {"awareness", "consideration", "evaluation", "inquiry"},
}
STANDALONE_CTA_SEARCH_INTENTS = {
    "product-selection",
    "oem-odm",
    "supplier-evaluation",
}
ENDING_MODES = {
    "informational-close",
    "inline-cta",
    "standalone-cta",
}
INTENT_SOURCE_ROLES = {
    "site-product",
    "site-service",
    "industry-context",
    "standard-regulation",
    "application-context",
}
CTA_BOILERPLATE_PHRASES = (
    "buyers ready to",
    "ready to turn",
    "a strong supplier conversation ends",
    "request a comparable proposal",
    "build a comparable",
    "use the site s contact channel",
)
GENERIC_CTA_HEADING_RE = re.compile(
    r"^(?:(?:build|request|prepare|get|start)\b.*\b"
    r"(?:rfq|proposal|quote|quotation)|contact us|get a quote|request a quote)$",
    flags=re.IGNORECASE,
)
EARLY_CONVERSION_RE = re.compile(
    r"\b(?:request|submit|get|ask\s+for|contact)\b"
    r"(?:\s+[A-Za-z0-9'’/-]+){0,8}\s+"
    r"(?:quote|quotation|rfq|sample|customization|custom\s+request)\b",
    flags=re.IGNORECASE,
)
TITLE_SIMILARITY_STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "of",
    "or",
    "the",
    "to",
    "with",
    "your",
}
COUNTRY_TERM_GROUPS = (
    ("china", "chinese", "prc"),
    (
        "united states",
        "united states of america",
        "usa",
        "u s a",
        "us",
        "u s",
        "america",
        "american",
    ),
    ("united kingdom", "uk", "u k", "britain", "british"),
    ("canada", "canadian"),
    ("australia", "australian"),
    ("germany", "german"),
    ("france", "french"),
    ("italy", "italian"),
    ("spain", "spanish"),
    ("portugal", "portuguese"),
    ("netherlands", "dutch"),
    ("belgium", "belgian"),
    ("poland", "polish"),
    ("sweden", "swedish"),
    ("norway", "norwegian"),
    ("denmark", "danish"),
    ("finland", "finnish"),
    ("switzerland", "swiss"),
    ("austria", "austrian"),
    ("ireland", "irish"),
    ("europe", "european", "european union", "eu", "e u"),
    ("india", "indian"),
    ("japan", "japanese"),
    ("south korea", "korea", "korean"),
    ("singapore", "singaporean"),
    ("malaysia", "malaysian"),
    ("indonesia", "indonesian"),
    ("thailand", "thai"),
    ("vietnam", "vietnamese"),
    ("philippines", "philippine", "filipino"),
    ("united arab emirates", "uae", "u a e", "emirati"),
    ("saudi arabia", "saudi"),
    ("middle east", "middle eastern"),
    ("south africa", "south african"),
    ("brazil", "brazilian"),
    ("mexico", "mexican"),
    ("argentina", "argentine", "argentinian"),
    ("chile", "chilean"),
    ("colombia", "colombian"),
    ("turkey", "turkish", "turkiye"),
    ("russia", "russian"),
)
CUSTOMER_ROLE_GROUPS = (
    ("buyer", "buyers", "purchaser", "purchasers", "purchasing", "procurement", "sourcing"),
    ("customer", "customers", "client", "clients", "b2b"),
    ("distributor", "distributors", "distribution"),
    ("wholesaler", "wholesalers", "wholesale"),
    ("importer", "importers", "importing"),
    ("exporter", "exporters", "exporting"),
    ("retailer", "retailers", "retail"),
    ("seller", "sellers", "ecommerce", "e commerce"),
    ("brand", "brands", "brand owner", "brand owners"),
    ("manufacturer", "manufacturers", "manufacturing"),
    ("supplier", "suppliers", "supply"),
    ("formulator", "formulators", "formulation team", "formulation teams"),
    ("engineer", "engineers", "engineering team", "engineering teams"),
    ("contractor", "contractors"),
    ("pharmacy", "pharmacies", "pharmacist", "pharmacists"),
    ("clinic", "clinics", "hospital", "hospitals"),
)


def normalize_space(value: str) -> str:
    return SPACE_RE.sub(" ", value).strip()


def normalize_title_match(value: str) -> str:
    return normalize_space(re.sub(r"[^a-z0-9]+", " ", value.casefold()))


def contains_normalized_phrase(text: str, phrase: str) -> bool:
    if not text or not phrase:
        return False
    return f" {phrase} " in f" {text} "


def matching_group_terms(
    title: str,
    keyword: str,
    target: str,
    groups: tuple[tuple[str, ...], ...],
) -> list[str]:
    title_value = normalize_title_match(title)
    keyword_value = normalize_title_match(keyword)
    target_value = normalize_title_match(target)
    if not target_value:
        return []

    matches: list[str] = []
    for group in groups:
        normalized_group = tuple(normalize_title_match(term) for term in group)
        applies = any(
            contains_normalized_phrase(target_value, term)
            or contains_normalized_phrase(term, target_value)
            for term in normalized_group
        )
        if not applies:
            continue
        title_terms = [
            term
            for term in normalized_group
            if contains_normalized_phrase(title_value, term)
        ]
        keyword_has_group = any(
            contains_normalized_phrase(keyword_value, term)
            for term in normalized_group
        )
        if title_terms and not keyword_has_group:
            matches.extend(title_terms)
    return matches


def validate_title_audience_context(
    title: str,
    keyword: str,
    target_country: str,
    target_customer: str,
) -> tuple[list[str], list[str]]:
    title_value = normalize_title_match(title)
    keyword_value = normalize_title_match(keyword)
    matched_terms: list[str] = []

    for target in (target_country, target_customer):
        target_value = normalize_title_match(target)
        if (
            target_value
            and contains_normalized_phrase(title_value, target_value)
            and not contains_normalized_phrase(keyword_value, target_value)
        ):
            matched_terms.append(target_value)

    matched_terms.extend(
        matching_group_terms(
            title,
            keyword,
            target_country,
            COUNTRY_TERM_GROUPS,
        )
    )
    matched_terms.extend(
        matching_group_terms(
            title,
            keyword,
            target_customer,
            CUSTOMER_ROLE_GROUPS,
        )
    )
    matched_terms = sorted(set(matched_terms))
    errors: list[str] = []
    if matched_terms:
        errors.append(
            "Title must not expose target-country or target-customer context: "
            + ", ".join(matched_terms)
        )
    return matched_terms, errors


def title_signature(title: str, keyword: str) -> str:
    title_value = normalize_title_match(title)
    keyword_value = normalize_title_match(keyword)
    if keyword_value:
        title_value = (
            f" {title_value} "
            .replace(f" {keyword_value} ", " <keyword> ")
            .strip()
        )
    return title_value


def title_content_tokens(signature: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", signature)
        if token not in TITLE_SIMILARITY_STOPWORDS and token != "keyword"
    }


def stable_percentage_roll(seed: str) -> int:
    normalized_seed = normalize_space(seed)
    if not normalized_seed:
        raise ValueError("Title-mode seed cannot be empty")
    upper_bound = 1 << 64
    acceptance_limit = upper_bound - (upper_bound % 100)
    counter = 0
    while True:
        payload = f"{normalized_seed}\x1f{counter}".encode("utf-8")
        value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
        if value < acceptance_limit:
            return value % 100
        counter += 1


def validate_title_mode(
    title: str,
    keyword: str,
    title_mode_seed: str,
) -> tuple[int, str, bool, list[str]]:
    errors: list[str] = []
    try:
        roll = stable_percentage_roll(title_mode_seed)
    except ValueError as exc:
        return -1, "invalid", False, [str(exc)]

    expected_mode = (
        "question" if roll < QUESTION_TITLE_PROBABILITY else "statement"
    )
    stripped_title = title.rstrip()
    is_question = stripped_title.endswith("?") and stripped_title.count("?") == 1
    if expected_mode == "question" and not is_question:
        errors.append(
            f"Title-mode roll {roll} requires a question title ending with one question mark"
        )
    if expected_mode == "statement" and "?" in stripped_title:
        errors.append(
            f"Title-mode roll {roll} requires a non-question title without a question mark"
        )

    if keyword:
        direct_prefix = re.compile(
            rf"^\s*{re.escape(keyword)}\s*[:|\-\u2013\u2014]",
            flags=re.IGNORECASE,
        )
        if direct_prefix.search(title):
            errors.append(
                "Title must integrate the core keyword into the sentence instead of "
                "using the keyword as a colon or dash prefix"
            )
        keyword_occurrences = count_exact_phrase(title, keyword)
        if keyword_occurrences != 1:
            errors.append(
                "Title must contain the exact core keyword once as a natural phrase; "
                f"received {keyword_occurrences} occurrences"
            )
        supporting_tokens = title_content_tokens(title_signature(title, keyword))
        if len(supporting_tokens) < 3:
            errors.append(
                "Title must add at least three meaningful content words around the "
                "core keyword"
            )

    return roll, expected_mode, is_question, errors


def read_title_history(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    try:
        value = json.loads(read_text(path))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return [], [f"Title history is unavailable or invalid: {exc}"]
    if not isinstance(value, list):
        return [], ["Title history must be a JSON array"]

    records: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"title-history[{index}] must be an object")
            continue
        title = normalize_space(str(item.get("title", "")))
        if not title:
            errors.append(f"title-history[{index}].title is required")
            continue
        angle = normalize_space(str(item.get("angle", "")))
        pattern = normalize_space(str(item.get("pattern", "")))
        if angle and angle not in TITLE_ANGLES:
            errors.append(f"title-history[{index}].angle is invalid: {angle}")
        if pattern and pattern not in TITLE_PATTERNS:
            errors.append(f"title-history[{index}].pattern is invalid: {pattern}")
        records.append(
            {
                "title": title,
                "keyword": normalize_space(str(item.get("keyword", ""))),
                "angle": angle,
                "pattern": pattern,
                "source": normalize_space(str(item.get("source", ""))),
            }
        )
    return records, errors


def validate_title_diversity(
    title: str,
    keyword: str,
    angle: str,
    pattern: str,
    title_mode: str,
    history_path: Path,
) -> tuple[int, float, list[str]]:
    history, errors = read_title_history(history_path)
    if angle not in TITLE_ANGLES:
        errors.append(f"Invalid title angle: {angle}")
    if pattern not in TITLE_PATTERNS:
        errors.append(f"Invalid title pattern: {pattern}")
    compatible_patterns = (
        QUESTION_TITLE_PATTERNS
        if title_mode == "question"
        else STATEMENT_TITLE_PATTERNS
    )
    if pattern in TITLE_PATTERNS and pattern not in compatible_patterns:
        errors.append(
            f"Title pattern {pattern} is incompatible with title mode {title_mode}"
        )

    current_normalized = normalize_title_match(title)
    current_signature = title_signature(title, keyword)
    current_tokens = title_content_tokens(current_signature)
    max_similarity = 0.0
    pair_reused = False
    current_run_history = [
        item for item in history if item["source"] == "current-run"
    ]
    angle_counts = Counter(
        item["angle"] for item in current_run_history if item["angle"]
    )
    pattern_counts = Counter(
        item["pattern"] for item in current_run_history if item["pattern"]
    )

    if angle in TITLE_ANGLES:
        least_angle_count = min(angle_counts.get(item, 0) for item in TITLE_ANGLES)
        if angle_counts.get(angle, 0) > least_angle_count:
            errors.append(
                f"Title angle is not among the least-used choices for this run: {angle}"
            )
    if pattern in compatible_patterns:
        least_pattern_count = min(
            pattern_counts.get(item, 0) for item in compatible_patterns
        )
        if pattern_counts.get(pattern, 0) > least_pattern_count:
            errors.append(
                f"Title pattern is not among the least-used choices for this run: {pattern}"
            )
    if current_run_history:
        previous_current = current_run_history[-1]
        if previous_current["angle"] == angle:
            errors.append(f"Title angle repeats the previous current-run title: {angle}")
        if previous_current["pattern"] == pattern:
            errors.append(
                f"Title pattern repeats the previous current-run title: {pattern}"
            )

    for index, item in enumerate(history):
        previous_title = item["title"]
        previous_normalized = normalize_title_match(previous_title)
        if current_normalized == previous_normalized:
            errors.append(
                f"Title exactly duplicates title-history[{index}]: {previous_title}"
            )
            max_similarity = 1.0
            continue

        previous_signature = title_signature(previous_title, item["keyword"])
        similarity = SequenceMatcher(
            None,
            current_signature,
            previous_signature,
        ).ratio()
        max_similarity = max(max_similarity, similarity)
        previous_tokens = title_content_tokens(previous_signature)
        shared = current_tokens & previous_tokens
        union = current_tokens | previous_tokens
        overlap = len(shared) / len(union) if union else 0.0

        reasons = []
        if similarity >= 0.82:
            reasons.append(f"template similarity {similarity:.2f}")
        if len(shared) >= 3 and overlap >= 0.75:
            reasons.append(f"content-word overlap {overlap:.2f}")
        if reasons:
            errors.append(
                f"Title is too similar to title-history[{index}] "
                f"({'; '.join(reasons)}): {previous_title}"
            )

        if (
            not pair_reused
            and item["source"] == "current-run"
            and item["angle"] == angle
            and item["pattern"] == pattern
        ):
            errors.append(
                f"Title angle-pattern pair is already used: {angle} + {pattern}"
            )
            pair_reused = True

    return len(history), round(max_similarity, 4), errors


def nonempty_string_list(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    normalized = [normalize_space(str(item)) for item in value]
    if any(not item for item in normalized):
        return None
    return normalized


def validate_related_keywords(
    value: object,
    core_keyword: str,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    related_keywords = nonempty_string_list(value)
    if related_keywords is None or not 2 <= len(related_keywords) <= 4:
        received = len(related_keywords) if related_keywords is not None else 0
        return [], [
            "intent-analysis must contain 2–4 non-empty related_keywords; "
            f"received {received}"
        ]

    normalized = [normalize_title_match(item) for item in related_keywords]
    if len(set(normalized)) != len(normalized):
        errors.append("intent-analysis related_keywords must be distinct")

    core_normalized = normalize_title_match(core_keyword)
    for index, (keyword, keyword_normalized) in enumerate(
        zip(related_keywords, normalized)
    ):
        word_count = len(WORD_RE.findall(keyword))
        if not 2 <= word_count <= 8 or len(keyword) > 80:
            errors.append(
                f"intent-analysis related_keywords[{index}] must contain "
                "2–8 English words and at most 80 characters"
            )
        if (
            not keyword_normalized
            or contains_normalized_phrase(core_normalized, keyword_normalized)
            or contains_normalized_phrase(keyword_normalized, core_normalized)
        ):
            errors.append(
                f"intent-analysis related_keywords[{index}] must not equal, "
                "contain, or be contained by the core keyword"
            )

    for first_index, first in enumerate(normalized):
        for second_index, second in enumerate(
            normalized[first_index + 1 :],
            start=first_index + 1,
        ):
            if (
                contains_normalized_phrase(first, second)
                or contains_normalized_phrase(second, first)
            ):
                errors.append(
                    "intent-analysis related keywords must not contain one another: "
                    f"indexes {first_index} and {second_index}"
                )

    return related_keywords, errors


def count_exact_phrase(text: str, phrase: str) -> int:
    normalized_text = normalize_space(text)
    normalized_phrase = normalize_space(phrase)
    if not normalized_text or not normalized_phrase:
        return 0
    pattern = re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(normalized_phrase)}(?![A-Za-z0-9])",
        flags=re.IGNORECASE,
    )
    return len(pattern.findall(normalized_text))


def validate_keyword_usage(
    content_blocks: list[str],
    visible_text: str,
    core_keyword: str,
    related_keywords: list[str],
) -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    core_block_counts = [
        count_exact_phrase(block, core_keyword) for block in content_blocks
    ]
    core_occurrences = sum(core_block_counts)
    core_blocks = sum(count > 0 for count in core_block_counts)

    if core_blocks < 3:
        errors.append(
            "Exact core keyword must be distributed across the lead and at least "
            f"two later content blocks; received {core_blocks} blocks"
        )
    if any(count > 1 for count in core_block_counts):
        errors.append(
            "Exact core keyword must not appear more than once in one paragraph, "
            "heading, list item, table cell, or caption"
        )

    related_counts: dict[str, int] = {}
    related_block_indexes: set[int] = set()
    if related_keywords:
        for related_keyword in related_keywords:
            block_counts = [
                count_exact_phrase(block, related_keyword)
                for block in content_blocks
            ]
            count = sum(block_counts)
            related_counts[related_keyword] = count
            related_block_indexes.update(
                index for index, block_count in enumerate(block_counts) if block_count
            )
            if count < 1:
                errors.append(
                    f'Related keyword "{related_keyword}" must appear at least once '
                    f"in visible content; received {count}"
                )
            if any(block_count > 1 for block_count in block_counts):
                errors.append(
                    f'Related keyword "{related_keyword}" must not appear more '
                    "than once in one content block"
                )

        related_total = sum(related_counts.values())
        if len(related_block_indexes) < 2:
            errors.append(
                "Related keywords must be distributed across at least two content "
                f"blocks; received {len(related_block_indexes)}"
            )
    else:
        related_total = 0

    visible_word_count = len(WORD_RE.findall(visible_text))
    core_keyword_words = len(WORD_RE.findall(core_keyword))
    core_keyword_weighted_words = core_occurrences * core_keyword_words
    related_keyword_weighted_words = sum(
        related_counts[related_keyword] * len(WORD_RE.findall(related_keyword))
        for related_keyword in related_keywords
    )
    keyword_weighted_words = (
        core_keyword_weighted_words + related_keyword_weighted_words
    )
    keyword_density_percent = (
        keyword_weighted_words / visible_word_count * 100
        if visible_word_count
        else 0.0
    )
    if not (
        KEYWORD_DENSITY_MIN_PERCENT
        <= keyword_density_percent
        <= KEYWORD_DENSITY_MAX_PERCENT
    ):
        errors.append(
            "Combined exact target-keyword density must be 1.00%–3.00% of "
            "visible article words; received "
            f"{keyword_density_percent:.2f}% "
            f"({keyword_weighted_words} weighted keyword words / "
            f"{visible_word_count} visible words)"
        )

    metrics: dict[str, object] = {
        "core_keyword_occurrences": core_occurrences,
        "core_keyword_blocks": core_blocks,
        "core_keyword_weighted_words": core_keyword_weighted_words,
        "related_keyword_occurrences": related_counts,
        "related_keyword_occurrences_total": related_total,
        "related_keyword_blocks": len(related_block_indexes),
        "related_keyword_weighted_words": related_keyword_weighted_words,
        "visible_word_count": visible_word_count,
        "keyword_weighted_words": keyword_weighted_words,
        "keyword_density_percent": round(keyword_density_percent, 4),
        "keyword_density_min_percent": KEYWORD_DENSITY_MIN_PERCENT,
        "keyword_density_max_percent": KEYWORD_DENSITY_MAX_PERCENT,
    }
    return metrics, errors


def validate_non_faq_h3_depth(
    h2s: list[dict[str, str]],
    h3_sections: list[dict[str, object]],
    visible_characters: int,
) -> tuple[int, int, int, int, list[str]]:
    errors: list[str] = []
    non_faq_h2_indexes = {
        index
        for index, heading in enumerate(h2s)
        if heading["text"].casefold() not in FAQ_HEADING_TEXTS
    }
    non_faq_h3s = [
        section for section in h3_sections if not bool(section.get("is_faq"))
    ]
    non_faq_h3_count = len(non_faq_h3s)

    length_minimum = (
        6 if visible_characters < 12000 else 7 if visible_characters < 13500 else 8
    )
    length_parent_minimum = 3 if visible_characters < 12000 else 4
    required_parent_sections = min(
        len(non_faq_h2_indexes),
        max(length_parent_minimum, math.ceil(len(non_faq_h2_indexes) / 2)),
    )
    minimum_h3_count = max(length_minimum, required_parent_sections + 1)
    maximum_h3_count = min(
        NON_FAQ_H3_MAX_COUNT,
        max(minimum_h3_count, len(non_faq_h2_indexes) * 2),
    )

    parent_indexes = {
        section.get("parent_h2_index")
        for section in non_faq_h3s
        if section.get("parent_h2_index") in non_faq_h2_indexes
    }
    if not minimum_h3_count <= non_faq_h3_count <= maximum_h3_count:
        errors.append(
            "Non-FAQ body content must contain "
            f"{minimum_h3_count}–{maximum_h3_count} H3 subheadings for this "
            f"article length and H2 structure; received {non_faq_h3_count}"
        )
    if len(parent_indexes) < required_parent_sections:
        errors.append(
            "Non-FAQ H3 subheadings must deepen at least "
            f"{required_parent_sections} different non-FAQ H2 sections; "
            f"received {len(parent_indexes)}"
        )

    normalized_headings = [
        normalize_title_match(str(section.get("text", "")))
        for section in non_faq_h3s
    ]
    if any(not heading for heading in normalized_headings):
        errors.append("Every non-FAQ H3 must have descriptive visible text")
    if len(set(normalized_headings)) != len(normalized_headings):
        errors.append("Non-FAQ H3 subheadings must be unique")

    for section in non_faq_h3s:
        heading = normalize_space(str(section.get("text", ""))) or "(empty H3)"
        text_parts = section.get("text_parts", [])
        if not isinstance(text_parts, list):
            text_parts = []
        section_text = normalize_space(
            " ".join(str(part) for part in text_parts).replace(PLACEHOLDER, "")
        )
        section_characters = len(section_text)
        block_count = section.get("block_count", 0)
        if not isinstance(block_count, int):
            block_count = 0
        if block_count < 1:
            errors.append(
                f'Non-FAQ H3 "{heading}" must be followed by at least one '
                "paragraph, list item, table cell, or caption before the next heading"
            )
        if section_characters < NON_FAQ_H3_MIN_CONTENT_CHARACTERS:
            errors.append(
                f'Non-FAQ H3 "{heading}" must develop at least '
                f"{NON_FAQ_H3_MIN_CONTENT_CHARACTERS} visible characters before "
                f"the next H3 or H2; received {section_characters}"
            )

    return (
        non_faq_h3_count,
        len(parent_indexes),
        required_parent_sections,
        minimum_h3_count,
        errors,
    )


def image_fingerprint(path: Path) -> tuple[str, str, int, int]:
    source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        width, height = image.size
        grayscale = image.convert("L").resize(
            (32, 32),
            Image.Resampling.LANCZOS,
        )
        pixels = list(grayscale.getdata())

    cosine = [
        [
            math.cos((2 * position + 1) * frequency * math.pi / 64)
            for position in range(32)
        ]
        for frequency in range(8)
    ]
    coefficients: list[float] = []
    for vertical_frequency in range(8):
        for horizontal_frequency in range(8):
            value = 0.0
            for y in range(32):
                row_offset = y * 32
                vertical_cosine = cosine[vertical_frequency][y]
                for x in range(32):
                    value += (
                        pixels[row_offset + x]
                        * cosine[horizontal_frequency][x]
                        * vertical_cosine
                    )
            coefficients.append(value)

    median = statistics.median(coefficients[1:])
    bits = 0
    for coefficient in coefficients:
        bits = (bits << 1) | int(coefficient > median)
    return source_sha256, f"{bits:016X}", width, height


def perceptual_hash_distance(first: str, second: str) -> int:
    return bin(int(first, 16) ^ int(second, 16)).count("1")


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.text_parts: list[str] = []
        self.style_parts: list[str] = []
        self.headings: list[dict[str, str]] = []
        self.h3_sections: list[dict[str, object]] = []
        self.links: list[tuple[str, str]] = []
        self.content_blocks: list[str] = []
        self.first_paragraph_segments: list[tuple[str, str | None]] = []
        self.h1_count = 0
        self.img_count = 0
        self.style_count = 0
        self.responsive_style_count = 0
        self.article_wrapper_count = 0
        self.article_toc_count = 0
        self.table_count = 0
        self.wrapped_table_count = 0
        self.figure_count = 0
        self.cta_inline_count = 0
        self.cta_standalone_count = 0
        self.cta_text_parts: list[str] = []
        self.event_index = 0
        self.first_paragraph_index: int | None = None
        self._current_heading: dict[str, str] | None = None
        self._current_link_href: str | None = None
        self._current_link_text: list[str] = []
        self._style_depth = 0
        self._ignored_depth = 0
        self._article_depth = 0
        self._table_wrap_depth = 0
        self._div_table_wrap_stack: list[bool] = []
        self._paragraph_depth = 0
        self._cta_marker_stack: list[str] = []
        self._content_block_stack: list[dict[str, object]] = []
        self._first_paragraph_complete = False
        self._seen_h2 = False
        self._faq_active = False
        self._current_h2_index: int | None = None
        self._current_h2_text = ""
        self._active_h3_section: dict[str, object] | None = None
        self.faq_questions = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.event_index += 1
        tag = tag.lower()
        values = {key.lower(): value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())
        if tag == "style":
            self.style_count += 1
            if values.get("data-article-style") == STYLE_VERSION:
                self.responsive_style_count += 1
            self._style_depth += 1
            return
        if tag == "script":
            self._ignored_depth += 1
            return
        if tag == "article":
            if "article-content" in classes:
                self.article_wrapper_count += 1
                self._article_depth += 1
            return
        if self._article_depth and tag in ARTICLE_KEYWORD_BLOCK_TAGS:
            self._content_block_stack.append({"tag": tag, "parts": []})
        cta_marker = normalize_space(values.get("data-article-cta", "")).lower()
        if cta_marker:
            if not self._article_depth:
                self.errors.append("CTA marker must be inside .article-content")
            if cta_marker == "inline":
                if tag != "p":
                    self.errors.append(
                        'data-article-cta="inline" is allowed only on a paragraph'
                    )
                self.cta_inline_count += 1
            elif cta_marker == "standalone":
                if tag != "section":
                    self.errors.append(
                        'data-article-cta="standalone" is allowed only on a section'
                    )
                self.cta_standalone_count += 1
            else:
                self.errors.append(f"Unknown data-article-cta value: {cta_marker}")
            self._cta_marker_stack.append(tag)
        if tag == "div":
            is_table_wrap = "article-table-wrap" in classes
            self._div_table_wrap_stack.append(is_table_wrap)
            if is_table_wrap:
                self._table_wrap_depth += 1
        if tag == "table":
            self.table_count += 1
            if self._table_wrap_depth:
                self.wrapped_table_count += 1
        elif tag == "figure":
            self.figure_count += 1
        if tag == "h1":
            self.h1_count += 1
        elif tag in {"h2", "h3"}:
            self._active_h3_section = None
            if tag == "h3" and not self._seen_h2:
                self.errors.append("H3 appears before any H2")
            if tag == "h2":
                self._seen_h2 = True
            self._current_heading = {"tag": tag, "id": values.get("id", ""), "text": ""}
        elif tag == "nav":
            if "article-toc" in classes:
                self.article_toc_count += 1
        elif tag == "p" and self._article_depth:
            self._paragraph_depth += 1
            if self.first_paragraph_index is None:
                self.first_paragraph_index = self.event_index
        elif tag == "a" and self._article_depth:
            self._current_link_href = values.get("href", "")
            self._current_link_text = []
        elif tag == "img":
            self.img_count += 1

    def handle_data(self, data: str) -> None:
        if not data:
            return
        if self._style_depth:
            self.style_parts.append(data)
            return
        if self._ignored_depth or not self._article_depth:
            return
        self.text_parts.append(data)
        if self._content_block_stack:
            parts = self._content_block_stack[-1]["parts"]
            if isinstance(parts, list):
                parts.append(data)
        if self._current_heading is not None:
            self._current_heading["text"] += data
        elif self._active_h3_section is not None:
            parts = self._active_h3_section["text_parts"]
            if isinstance(parts, list):
                parts.append(data)
        if self._current_link_href is not None:
            self._current_link_text.append(data)
        if self._cta_marker_stack:
            self.cta_text_parts.append(data)
        if self._paragraph_depth and not self._first_paragraph_complete:
            self.first_paragraph_segments.append((data, self._current_link_href))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "style" and self._style_depth:
            self._style_depth -= 1
            return
        if tag == "script" and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if (
            self._content_block_stack
            and self._content_block_stack[-1]["tag"] == tag
        ):
            block = self._content_block_stack.pop()
            parts = block["parts"]
            if isinstance(parts, list):
                text = normalize_space("".join(str(part) for part in parts))
                if text:
                    self.content_blocks.append(text)
                    if (
                        self._active_h3_section is not None
                        and tag not in {"h2", "h3"}
                    ):
                        block_count = self._active_h3_section["block_count"]
                        if isinstance(block_count, int):
                            self._active_h3_section["block_count"] = block_count + 1
        if tag in {"h2", "h3"} and self._current_heading is not None:
            heading = self._current_heading
            heading["text"] = normalize_space(heading["text"])
            self.headings.append(heading)
            if tag == "h2":
                self._current_h2_index = sum(
                    item["tag"] == "h2" for item in self.headings
                ) - 1
                self._current_h2_text = heading["text"]
                self._faq_active = heading["text"].casefold() in FAQ_HEADING_TEXTS
            else:
                section: dict[str, object] = {
                    "text": heading["text"],
                    "parent_h2_index": self._current_h2_index,
                    "parent_h2_text": self._current_h2_text,
                    "is_faq": self._faq_active,
                    "text_parts": [],
                    "block_count": 0,
                }
                self.h3_sections.append(section)
                self._active_h3_section = section
                if self._faq_active:
                    self.faq_questions += 1
            self._current_heading = None
        elif tag == "a" and self._current_link_href is not None:
            link = (self._current_link_href, normalize_space("".join(self._current_link_text)))
            self.links.append(link)
            self._current_link_href = None
            self._current_link_text = []
        elif tag == "p" and self._paragraph_depth:
            self._paragraph_depth -= 1
            if not self._first_paragraph_complete:
                self._first_paragraph_complete = True
        elif tag == "div" and self._div_table_wrap_stack:
            was_table_wrap = self._div_table_wrap_stack.pop()
            if was_table_wrap:
                self._table_wrap_depth -= 1
        elif tag == "article" and self._article_depth:
            self._active_h3_section = None
            self._article_depth -= 1
        if self._cta_marker_stack and tag == self._cta_marker_stack[-1]:
            self._cta_marker_stack.pop()


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8").strip()


def read_alt_texts(path: Path) -> list[str]:
    raw = read_text(path)
    if raw.startswith("["):
        value = json.loads(raw)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError("Alt text JSON must be an array of strings")
        return [normalize_space(item) for item in value]
    return [normalize_space(line) for line in raw.splitlines() if line.strip()]


def normalized_hex_color(value: object) -> str | None:
    text = normalize_space(str(value))
    if not HEX_COLOR_RE.fullmatch(text):
        return None
    return text.upper()


def relative_luminance(color: str) -> float:
    channels = [
        int(color[index : index + 2], 16) / 255
        for index in (1, 3, 5)
    ]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    first_luminance = relative_luminance(first)
    second_luminance = relative_luminance(second)
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def preserves_theme_hue(candidate: str, observed: str) -> bool:
    def hls(color: str) -> tuple[float, float, float]:
        channels = [
            int(color[index : index + 2], 16) / 255
            for index in (1, 3, 5)
        ]
        return colorsys.rgb_to_hls(*channels)

    candidate_hue, _, candidate_saturation = hls(candidate)
    observed_hue, _, observed_saturation = hls(observed)
    if observed_saturation < 0.12:
        return candidate_saturation < 0.12
    if candidate_saturation < 0.12:
        return False
    hue_distance = abs(candidate_hue - observed_hue)
    hue_distance = min(hue_distance, 1 - hue_distance)
    return hue_distance <= 20 / 360


def validate_site_theme(
    path: Path,
    host: str,
    css: str,
) -> tuple[int, int, float, list[str]]:
    errors: list[str] = []
    try:
        value = json.loads(read_text(path))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return 0, 0, 0.0, [f"Site theme colors are unavailable or invalid: {exc}"]
    if not isinstance(value, dict):
        return 0, 0, 0.0, ["Site theme colors must be a JSON object"]

    bare_host = host[4:] if host.startswith("www.") else host
    allowed_hosts = {bare_host, f"www.{bare_host}"}
    recorded_host = normalize_space(str(value.get("site_host", ""))).lower().rstrip(".")
    if recorded_host not in allowed_hosts:
        errors.append("theme-colors site_host must match --site-host")

    source_urls = nonempty_string_list(value.get("source_urls"))
    if source_urls is None or len(set(source_urls)) < 2:
        received = len(source_urls) if source_urls is not None else 0
        errors.append(
            "theme-colors source_urls must contain at least two distinct same-site URLs; "
            f"received {received}"
        )
        source_urls = []
    source_url_set = set(source_urls)
    for source_url in source_urls:
        parsed = urlparse(source_url)
        source_host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https" or source_host not in allowed_hosts:
            errors.append(
                f"theme-colors source URL must be same-site HTTPS: {source_url}"
            )

    evidence = value.get("evidence")
    if not isinstance(evidence, list) or len(evidence) < 2:
        received = len(evidence) if isinstance(evidence, list) else 0
        errors.append(
            "theme-colors evidence must contain at least two observations; "
            f"received {received}"
        )
        evidence = []

    observed_by_role: dict[str, set[str]] = {
        role: set() for role in THEME_EVIDENCE_ROLES
    }
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(f"theme-colors evidence[{index}] must be an object")
            continue
        url = normalize_space(str(item.get("url", "")))
        parsed = urlparse(url)
        evidence_host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https" or evidence_host not in allowed_hosts:
            errors.append(
                f"theme-colors evidence[{index}].url must be same-site HTTPS"
            )
        if source_url_set and url not in source_url_set:
            errors.append(
                f"theme-colors evidence[{index}].url must appear in source_urls"
            )
        evidence_type = normalize_space(str(item.get("evidence_type", "")))
        if evidence_type not in THEME_EVIDENCE_TYPES:
            errors.append(
                f"theme-colors evidence[{index}].evidence_type is invalid: "
                f"{evidence_type}"
            )
        if not normalize_space(str(item.get("selector_or_element", ""))):
            errors.append(
                f"theme-colors evidence[{index}].selector_or_element is required"
            )
        if not normalize_space(str(item.get("css_property", ""))):
            errors.append(
                f"theme-colors evidence[{index}].css_property is required"
            )
        role = normalize_space(str(item.get("role", "")))
        if role not in THEME_EVIDENCE_ROLES:
            errors.append(
                f"theme-colors evidence[{index}].role is invalid: {role}"
            )
        raw_color = normalize_space(str(item.get("color", "")))
        color = normalized_hex_color(raw_color)
        if color is None:
            errors.append(
                f"theme-colors evidence[{index}].color must be six-digit hex"
            )
        else:
            if raw_color != color:
                errors.append(
                    f"theme-colors evidence[{index}].color must use normalized "
                    "uppercase six-digit hex"
                )
            if role in observed_by_role:
                observed_by_role[role].add(color)

    if not observed_by_role["primary-accent"]:
        errors.append("theme-colors requires observed primary-accent evidence")
    if not observed_by_role["body-text"]:
        errors.append("theme-colors requires observed body-text evidence")

    colors = value.get("colors")
    if not isinstance(colors, dict):
        errors.append("theme-colors colors must be an object")
        colors = {}
    missing_variables = [
        variable for variable in THEME_COLOR_VARIABLES if variable not in colors
    ]
    unexpected_variables = sorted(set(colors) - set(THEME_COLOR_VARIABLES))
    if missing_variables:
        errors.append(
            "theme-colors is missing variables: " + ", ".join(missing_variables)
        )
    if unexpected_variables:
        errors.append(
            "theme-colors contains unsupported variables: "
            + ", ".join(unexpected_variables)
        )

    applied_colors: dict[str, str] = {}
    for variable in THEME_COLOR_VARIABLES:
        raw_color = normalize_space(str(colors.get(variable, "")))
        color = normalized_hex_color(raw_color)
        if color is None:
            errors.append(
                f"theme-colors {variable} must be six-digit hex"
            )
            continue
        if raw_color != color:
            errors.append(
                f"theme-colors {variable} must use normalized uppercase six-digit hex"
            )
        applied_colors[variable] = color

    observed_accents = observed_by_role["primary-accent"]
    for variable in (
        "--article-accent",
        "--article-accent-dark",
        "--article-table-header",
    ):
        color = applied_colors.get(variable)
        if color and observed_accents and not any(
            color == observed or preserves_theme_hue(color, observed)
            for observed in observed_accents
        ):
            errors.append(
                f"{variable} must equal or preserve the hue of an observed "
                "primary-accent color"
            )
    text_color = applied_colors.get("--article-text")
    if text_color and text_color not in observed_by_role["body-text"]:
        errors.append("--article-text must equal an observed body-text color")

    derivation_notes = normalize_space(str(value.get("derivation_notes", "")))
    if len(derivation_notes) < 20:
        errors.append(
            "theme-colors derivation_notes must explain derived shades and tints"
        )

    css_declarations: dict[str, list[str]] = {}
    for variable, color in re.findall(
        r"(?m)^\s*(--article-[a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;",
        css,
    ):
        css_declarations.setdefault(variable, []).append(color.upper())
    for variable in THEME_COLOR_VARIABLES:
        declarations = css_declarations.get(variable, [])
        if len(declarations) != 1:
            errors.append(
                f"Article CSS must declare {variable} exactly once; "
                f"received {len(declarations)}"
            )
            continue
        expected = applied_colors.get(variable)
        if expected and declarations[0] != expected:
            errors.append(
                f"Article CSS {variable} must equal theme-colors value {expected}"
            )
        usage_count = len(
            re.findall(
                rf"var\(\s*{re.escape(variable)}\s*\)",
                css,
                flags=re.IGNORECASE,
            )
        )
        if usage_count < 1:
            errors.append(f"Article CSS must use {variable}")

    required_theme_rules = [
        (
            r"\.article-content\s*\{[^}]*color\s*:\s*"
            r"var\(\s*--article-text\s*\)",
            "Article body text must use --article-text",
        ),
        (
            r"\.article-content\s+h2\s*\{[^}]*color\s*:\s*"
            r"var\(\s*--article-accent-dark\s*\)",
            "Article H2 color must use --article-accent-dark",
        ),
        (
            r"\.article-content\s+h3\s*\{[^}]*color\s*:\s*"
            r"var\(\s*--article-accent-dark\s*\)",
            "Article H3 color must use --article-accent-dark",
        ),
        (
            r"\.article-content\s+a\s*\{[^}]*color\s*:\s*"
            r"var\(\s*--article-accent\s*\)",
            "Article links must use --article-accent",
        ),
        (
            r"\.article-content\s+figcaption\s*\{[^}]*color\s*:\s*"
            r"var\(\s*--article-muted\s*\)",
            "Article captions must use --article-muted",
        ),
        (
            r"\.article-content\s+table\s*\{[^}]*background\s*:\s*"
            r"var\(\s*--article-surface\s*\)",
            "Article table surface must use --article-surface",
        ),
        (
            r"\.article-content\s+th\s*\{[^}]*color\s*:\s*"
            r"var\(\s*--article-table-header-text\s*\)[^}]*"
            r"background\s*:\s*var\(\s*--article-table-header\s*\)",
            "Table headers must use the site-theme header and header-text variables",
        ),
        (
            r"\.article-content\s+tbody\s+tr:nth-child\(even\)\s*\{[^}]*"
            r"background\s*:\s*var\(\s*--article-table-stripe\s*\)",
            "Striped table rows must use --article-table-stripe",
        ),
        (
            r"\.article-content\s+tbody\s+tr:hover\s*\{[^}]*"
            r"background\s*:\s*var\(\s*--article-table-hover\s*\)",
            "Table hover rows must use --article-table-hover",
        ),
    ]
    for pattern, message in required_theme_rules:
        if not re.search(pattern, css, flags=re.IGNORECASE | re.DOTALL):
            errors.append(message)

    contrast_pairs = (
        ("body text", "--article-text", "--article-surface"),
        ("muted text", "--article-muted", "--article-surface"),
        ("links", "--article-accent", "--article-surface"),
        ("headings", "--article-accent-dark", "--article-surface"),
        ("soft callouts", "--article-text", "--article-soft"),
        (
            "table header",
            "--article-table-header-text",
            "--article-table-header",
        ),
        ("striped table rows", "--article-text", "--article-table-stripe"),
        ("hover table rows", "--article-text", "--article-table-hover"),
    )
    contrast_values: list[float] = []
    for label, foreground_variable, background_variable in contrast_pairs:
        foreground = applied_colors.get(foreground_variable)
        background = applied_colors.get(background_variable)
        if not foreground or not background:
            continue
        ratio = contrast_ratio(foreground, background)
        contrast_values.append(ratio)
        if ratio < 4.5:
            errors.append(
                f"Site-theme {label} contrast must be at least 4.5:1; "
                f"received {ratio:.2f}:1"
            )

    minimum_contrast = min(contrast_values) if contrast_values else 0.0
    return (
        len(evidence),
        len(applied_colors),
        round(minimum_contrast, 2),
        errors,
    )


def validate_article_ending(
    parser: ArticleParser,
    content: str,
    target_country: str,
    target_customer: str,
    search_intent: str,
    buyer_stage: str,
    ending_mode: str,
) -> tuple[int, list[str], list[str]]:
    errors: list[str] = []
    if parser._cta_marker_stack:
        errors.append("Article contains an unclosed CTA marker element")
    if search_intent not in SEARCH_INTENTS:
        errors.append(f"Invalid search intent: {search_intent}")
    if buyer_stage not in BUYER_STAGES:
        errors.append(f"Invalid buyer stage: {buyer_stage}")
    if ending_mode not in ENDING_MODES:
        errors.append(f"Invalid ending mode: {ending_mode}")

    allowed_stage_endings = BUYER_STAGE_ENDING_MODES.get(buyer_stage, set())
    if ending_mode in ENDING_MODES and ending_mode not in allowed_stage_endings:
        errors.append(
            f"Buyer stage {buyer_stage} does not allow ending mode {ending_mode}"
        )
    if search_intent == "foundational-knowledge" and ending_mode != "informational-close":
        errors.append(
            "Foundational-knowledge content must use an informational close without "
            "a quotation or sample CTA"
        )
    if (
        ending_mode == "standalone-cta"
        and search_intent not in STANDALONE_CTA_SEARCH_INTENTS
    ):
        errors.append(
            f"Search intent {search_intent} does not justify a standalone CTA"
        )

    lead_text = normalize_space(
        "".join(text for text, _ in parser.first_paragraph_segments)
    )
    if (
        buyer_stage == "awareness" or search_intent == "foundational-knowledge"
    ) and EARLY_CONVERSION_RE.search(lead_text):
        errors.append(
            "Awareness and foundational content must not push a quote, sample, or "
            "custom request in the lead"
        )

    if ending_mode == "informational-close":
        if parser.cta_inline_count or parser.cta_standalone_count:
            errors.append("informational-close must not contain a CTA marker")
    elif ending_mode == "inline-cta":
        if parser.cta_inline_count != 1 or parser.cta_standalone_count:
            errors.append(
                "inline-cta requires exactly one inline marker and no standalone marker"
            )
    elif ending_mode == "standalone-cta":
        if parser.cta_standalone_count != 1 or parser.cta_inline_count:
            errors.append(
                "standalone-cta requires exactly one standalone marker and no inline marker"
            )

    cta_text = normalize_space(" ".join(parser.cta_text_parts))
    cta_word_count = len(WORD_RE.findall(cta_text))
    if ending_mode == "inline-cta" and not 12 <= cta_word_count <= 90:
        errors.append(
            f"inline-cta must contain 12–90 English words; received {cta_word_count}"
        )
    if ending_mode == "standalone-cta" and not 25 <= cta_word_count <= 140:
        errors.append(
            f"standalone-cta must contain 25–140 English words; received {cta_word_count}"
        )

    cta_audience_terms: list[str] = []
    if cta_text:
        cta_audience_terms, _ = validate_title_audience_context(
            cta_text,
            "",
            target_country,
            target_customer,
        )
        if cta_audience_terms:
            errors.append(
                "CTA must not label readers by target country or target customer: "
                + ", ".join(cta_audience_terms)
            )

    visible_text = normalize_space(
        " ".join(parser.text_parts).replace(PLACEHOLDER, "")
    )
    ending_text = normalize_title_match(visible_text[-1600:])
    boilerplate = sorted(
        phrase
        for phrase in CTA_BOILERPLATE_PHRASES
        if phrase in ending_text
    )
    if boilerplate:
        errors.append(
            "Article ending contains generic CTA boilerplate: "
            + ", ".join(boilerplate)
        )

    h2s = [heading for heading in parser.headings if heading["tag"] == "h2"]
    if h2s and GENERIC_CTA_HEADING_RE.search(h2s[-1]["text"]):
        errors.append(
            f"Article must not end with a generic CTA heading: {h2s[-1]['text']}"
        )

    if ending_mode == "inline-cta":
        inline_markers = list(
            re.finditer(
                r"""data-article-cta\s*=\s*["']inline["']""",
                content,
                flags=re.IGNORECASE,
            )
        )
        if inline_markers and re.search(
            r"<h2\b",
            content[inline_markers[-1].end() :],
            flags=re.IGNORECASE,
        ):
            errors.append("inline-cta must appear after the article's final H2")

    return cta_word_count, cta_audience_terms, errors


def validate_intent_analysis(
    path: Path,
    keyword: str,
    search_intent: str,
    buyer_stage: str,
    host: str,
) -> tuple[int, int, int, list[str], str, str, list[str]]:
    errors: list[str] = []
    try:
        value = json.loads(read_text(path))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return 0, 0, 0, [], "", "", [
            f"Intent analysis is unavailable or invalid: {exc}"
        ]
    if not isinstance(value, dict):
        return 0, 0, 0, [], "", "", [
            "Intent analysis must be a JSON object"
        ]

    recorded_keyword = normalize_space(str(value.get("core_keyword", "")))
    if recorded_keyword.casefold() != keyword.casefold():
        errors.append("intent-analysis core_keyword must equal the validator keyword")
    recorded_intent = normalize_space(str(value.get("primary_intent", "")))
    if recorded_intent != search_intent:
        errors.append("intent-analysis primary_intent must equal --search-intent")
    if recorded_intent not in SEARCH_INTENTS:
        errors.append(f"intent-analysis primary_intent is invalid: {recorded_intent}")

    secondary_intent = normalize_space(str(value.get("secondary_intent", "")))
    if secondary_intent:
        if secondary_intent not in SEARCH_INTENTS:
            errors.append(
                f"intent-analysis secondary_intent is invalid: {secondary_intent}"
            )
        if secondary_intent == recorded_intent:
            errors.append(
                "intent-analysis secondary_intent must differ from primary_intent"
            )
        secondary_rationale = normalize_space(
            str(value.get("secondary_intent_rationale", ""))
        )
        if len(secondary_rationale) < 30:
            errors.append(
                "intent-analysis secondary_intent_rationale must contain at least "
                "30 characters when a secondary intent is selected"
            )

    recorded_buyer_stage = normalize_space(str(value.get("buyer_stage", "")))
    if recorded_buyer_stage != buyer_stage:
        errors.append("intent-analysis buyer_stage must equal --buyer-stage")
    if recorded_buyer_stage not in BUYER_STAGES:
        errors.append(
            f"intent-analysis buyer_stage is invalid: {recorded_buyer_stage}"
        )
    allowed_stages = SEARCH_INTENT_BUYER_STAGES.get(recorded_intent, set())
    if recorded_buyer_stage in BUYER_STAGES and recorded_buyer_stage not in allowed_stages:
        errors.append(
            f"Buyer stage {recorded_buyer_stage} is incompatible with primary intent "
            f"{recorded_intent}"
        )
    buyer_stage_rationale = normalize_space(
        str(value.get("buyer_stage_rationale", ""))
    )
    if len(buyer_stage_rationale) < 30:
        errors.append(
            "intent-analysis buyer_stage_rationale must contain at least 30 characters"
        )
    editorial_stance = normalize_space(str(value.get("editorial_stance", "")))
    if editorial_stance != "neutral-buyer-guidance":
        errors.append(
            "intent-analysis editorial_stance must be neutral-buyer-guidance"
        )

    keyword_signals = nonempty_string_list(value.get("keyword_signals"))
    if not keyword_signals:
        errors.append("intent-analysis keyword_signals must contain verified query signals")
        keyword_signals = []
    rationale = normalize_space(str(value.get("intent_rationale", "")))
    if len(rationale) < 30:
        errors.append("intent-analysis intent_rationale must contain at least 30 characters")

    rejected_intents = nonempty_string_list(value.get("rejected_intents"))
    if not rejected_intents:
        errors.append("intent-analysis rejected_intents must contain at least one alternative")
        rejected_intents = []
    for rejected_intent in rejected_intents:
        if rejected_intent not in SEARCH_INTENTS:
            errors.append(
                f"intent-analysis rejected intent is invalid: {rejected_intent}"
            )
        if rejected_intent == search_intent:
            errors.append("intent-analysis cannot reject its selected primary intent")
        if secondary_intent and rejected_intent == secondary_intent:
            errors.append("intent-analysis cannot reject its selected secondary intent")

    related_queries = nonempty_string_list(value.get("related_queries"))
    if related_queries is None or not 2 <= len(related_queries) <= 6:
        received = len(related_queries) if related_queries is not None else 0
        errors.append(
            f"intent-analysis must contain 2–6 non-empty related queries; received {received}"
        )
        related_queries = []
    if len({item.casefold() for item in related_queries}) != len(related_queries):
        errors.append("intent-analysis related queries must be distinct")

    related_keywords, related_keyword_errors = validate_related_keywords(
        value.get("related_keywords"),
        keyword,
    )
    errors.extend(related_keyword_errors)

    research_sources = value.get("research_sources")
    if not isinstance(research_sources, list) or not 2 <= len(research_sources) <= 8:
        received = len(research_sources) if isinstance(research_sources, list) else 0
        errors.append(
            f"intent-analysis must contain 2–8 research sources; received {received}"
        )
        research_sources = []

    bare_host = host[4:] if host.startswith("www.") else host
    allowed_site_hosts = {bare_host, f"www.{bare_host}"}
    same_site_sources = 0
    external_sources = 0
    seen_urls: set[str] = set()
    today = date.today()

    for index, item in enumerate(research_sources):
        if not isinstance(item, dict):
            errors.append(f"intent-analysis research_sources[{index}] must be an object")
            continue
        url = normalize_space(str(item.get("url", "")))
        parsed = urlparse(url)
        source_host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https" or not source_host:
            errors.append(
                f"intent-analysis research_sources[{index}] must use a valid HTTPS URL"
            )
        elif source_host in allowed_site_hosts:
            same_site_sources += 1
        else:
            external_sources += 1
        if url in seen_urls:
            errors.append(
                f"intent-analysis research_sources[{index}] duplicates a source URL"
            )
        seen_urls.add(url)

        if not normalize_space(str(item.get("title", ""))):
            errors.append(
                f"intent-analysis research_sources[{index}].title is required"
            )
        source_role = normalize_space(str(item.get("source_role", "")))
        if source_role not in INTENT_SOURCE_ROLES:
            errors.append(
                f"intent-analysis research_sources[{index}].source_role is invalid: "
                f"{source_role}"
            )
        accessed_at = normalize_space(str(item.get("accessed_at", "")))
        try:
            accessed_date = date.fromisoformat(accessed_at)
        except ValueError:
            errors.append(
                f"intent-analysis research_sources[{index}].accessed_at "
                "must use YYYY-MM-DD"
            )
        else:
            age_days = (today - accessed_date).days
            if age_days < 0:
                errors.append(
                    f"intent-analysis research_sources[{index}].accessed_at "
                    "cannot be in the future"
                )
            elif age_days > 30:
                errors.append(
                    f"intent-analysis research_sources[{index}] was accessed "
                    f"{age_days} days ago; refresh the research"
                )
        if not normalize_space(str(item.get("freshness_note", ""))):
            errors.append(
                f"intent-analysis research_sources[{index}].freshness_note is required"
            )

    if same_site_sources < 1:
        errors.append("intent-analysis requires at least one same-site research source")
    external_source_reason = normalize_space(
        str(value.get("external_source_reason", ""))
    )
    if external_sources < 1 and not external_source_reason:
        errors.append(
            "intent-analysis requires an external source or external_source_reason"
        )

    return (
        len(research_sources),
        same_site_sources,
        external_sources,
        related_keywords,
        secondary_intent,
        recorded_buyer_stage,
        errors,
    )


def validate_image_selection(
    value: dict[str, object],
    manifest_path: Path,
    host: str,
    body_image_count: int,
    thumbnail: dict[str, object],
    body: list[object],
) -> tuple[int, int, int | None, int | None, bool, list[str]]:
    errors: list[str] = []
    bare_host = host[4:] if host.startswith("www.") else host
    allowed_hosts = {bare_host, f"www.{bare_host}"}
    expected_slots = ["thumbnail"] + [
        f"body-{index:02d}" for index in range(1, body_image_count + 1)
    ]

    candidate_pool = value.get("candidate_pool")
    if not isinstance(candidate_pool, list):
        errors.append("image-references candidate_pool must be an array")
        candidate_pool = []
    if len(candidate_pool) > 8:
        errors.append(
            f"candidate_pool must contain at most 8 deduplicated images; "
            f"received {len(candidate_pool)}"
        )
    pool_limit_reason = normalize_space(
        str(value.get("candidate_pool_limit_reason", ""))
    )
    if len(candidate_pool) < max(3, len(expected_slots)) and len(pool_limit_reason) < 30:
        errors.append(
            "candidate_pool_limit_reason must explain why fewer than the preferred "
            "candidate or slot count was available"
        )

    candidates: dict[str, dict[str, object]] = {}
    candidate_technical: dict[str, dict[str, object]] = {}
    for index, candidate in enumerate(candidate_pool):
        label = f"candidate_pool[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{label} must be an object")
            continue
        candidate_id = normalize_space(str(candidate.get("candidate_id", "")))
        if not ANCHOR_RE.fullmatch(candidate_id):
            errors.append(f"{label}.candidate_id must use lowercase words and hyphens")
            continue
        if candidate_id in candidates:
            errors.append(f"candidate_pool candidate_id is duplicated: {candidate_id}")
            continue
        candidates[candidate_id] = candidate

        classification = normalize_space(str(candidate.get("classification", "")))
        if classification not in {"product-present", "non-product"}:
            errors.append(
                f"{label}.classification must be product-present or non-product"
            )

        reference_url = normalize_space(str(candidate.get("reference_url", "")))
        parsed = urlparse(reference_url)
        reference_host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https" or reference_host not in allowed_hosts:
            errors.append(f"{label}.reference_url must be same-site HTTPS")

        reference_value = normalize_space(str(candidate.get("reference_file", "")))
        reference_path = Path(reference_value) if reference_value else Path()
        if reference_value and not reference_path.is_absolute():
            reference_path = manifest_path.parent / reference_path
        reference_path = reference_path.resolve()
        if not reference_value or not reference_path.is_file():
            errors.append(
                f"{label}.reference_file must be an existing image: {reference_value}"
            )
            continue

        try:
            computed_sha256, computed_phash, width, height = image_fingerprint(
                reference_path
            )
        except (OSError, ValueError) as exc:
            errors.append(f"{label}.reference_file cannot be analyzed: {exc}")
            continue

        recorded_sha256 = normalize_space(
            str(candidate.get("source_sha256", ""))
        )
        if not re.fullmatch(r"[0-9a-f]{64}", recorded_sha256):
            errors.append(f"{label}.source_sha256 must be lowercase SHA-256")
        elif recorded_sha256 != computed_sha256:
            errors.append(f"{label}.source_sha256 does not match reference_file")

        recorded_phash = normalize_space(
            str(candidate.get("perceptual_hash", ""))
        )
        if not re.fullmatch(r"[0-9A-F]{16}", recorded_phash):
            errors.append(
                f"{label}.perceptual_hash must be uppercase 64-bit hexadecimal"
            )
        elif recorded_phash != computed_phash:
            errors.append(f"{label}.perceptual_hash does not match reference_file")

        recorded_width = candidate.get("width")
        recorded_height = candidate.get("height")
        if recorded_width != width or recorded_height != height:
            errors.append(
                f"{label} dimensions must match reference_file: {width}x{height}"
            )

        view_angle = normalize_space(str(candidate.get("view_angle", "")))
        if view_angle not in IMAGE_VIEW_ANGLES:
            errors.append(f"{label}.view_angle is invalid: {view_angle}")
        scene_type = normalize_space(str(candidate.get("scene_type", "")))
        if scene_type not in IMAGE_SCENE_TYPES:
            errors.append(f"{label}.scene_type is invalid: {scene_type}")
        label_legibility = normalize_space(
            str(candidate.get("label_legibility", ""))
        )
        if label_legibility not in IMAGE_LABEL_LEGIBILITY:
            errors.append(
                f"{label}.label_legibility is invalid: {label_legibility}"
            )
        article_relevance = normalize_space(
            str(candidate.get("article_relevance", ""))
        )
        if article_relevance not in IMAGE_ARTICLE_RELEVANCE:
            errors.append(
                f"{label}.article_relevance is invalid: {article_relevance}"
            )
        if classification == "product-present" and article_relevance not in {
            "exact-product",
            "same-product-family",
        }:
            errors.append(
                f"{label} product-present candidate must be exact-product or "
                "same-product-family"
            )
        if classification == "non-product" and article_relevance != "supporting-site-scene":
            errors.append(
                f"{label} non-product candidate must be supporting-site-scene"
            )

        eligible = candidate.get("eligible_for_product_lock")
        if not isinstance(eligible, bool):
            errors.append(f"{label}.eligible_for_product_lock must be true or false")
            eligible = False
        if classification == "non-product" and eligible:
            errors.append(
                f"{label} non-product candidate cannot be eligible_for_product_lock"
            )
        if len(normalize_space(str(candidate.get("identity_summary", "")))) < 15:
            errors.append(f"{label}.identity_summary must describe the inspected image")

        candidate_technical[candidate_id] = {
            "path": reference_path,
            "url": reference_url,
            "sha256": computed_sha256,
            "phash": computed_phash,
            "classification": classification,
            "eligible": eligible,
            "scene_type": scene_type,
        }

    candidate_items = list(candidate_technical.items())
    for first_index, (first_id, first) in enumerate(candidate_items):
        for second_id, second in candidate_items[first_index + 1 :]:
            if first["sha256"] == second["sha256"]:
                errors.append(
                    f"candidate_pool contains exact duplicate sources: "
                    f"{first_id}, {second_id}"
                )
                continue
            distance = perceptual_hash_distance(
                str(first["phash"]),
                str(second["phash"]),
            )
            if distance <= SOURCE_NEAR_DUPLICATE_DISTANCE:
                errors.append(
                    f"candidate_pool contains near-duplicate sources "
                    f"(pHash distance {distance}): {first_id}, {second_id}"
                )

    selection_plan = value.get("selection_plan")
    if not isinstance(selection_plan, dict):
        errors.append("image-references selection_plan must be an object")
        selection_plan = {}
    if (
        normalize_space(str(selection_plan.get("global_selection_method", "")))
        != "weighted-global-assignment-with-duplicate-penalty"
    ):
        errors.append(
            "selection_plan.global_selection_method must be "
            "weighted-global-assignment-with-duplicate-penalty"
        )
    slots = selection_plan.get("slots")
    if not isinstance(slots, list):
        errors.append("selection_plan.slots must be an array")
        slots = []
    actual_slot_names = [
        normalize_space(str(slot.get("slot", "")))
        if isinstance(slot, dict)
        else ""
        for slot in slots
    ]
    if actual_slot_names != expected_slots:
        errors.append(
            "selection_plan slots must follow upload order exactly: "
            + ", ".join(expected_slots)
        )

    reference_records: dict[str, dict[str, object]] = {"thumbnail": thumbnail}
    reference_records.update(
        {
            f"body-{index:02d}": record
            for index, record in enumerate(body, start=1)
            if isinstance(record, dict)
        }
    )
    selected_candidate_ids: list[str] = []
    selected_roles: list[str] = []
    slot_to_candidate: dict[str, str] = {}
    for index, slot in enumerate(slots):
        label = f"selection_plan.slots[{index}]"
        if not isinstance(slot, dict):
            errors.append(f"{label} must be an object")
            continue
        slot_name = normalize_space(str(slot.get("slot", "")))
        candidate_id = normalize_space(str(slot.get("candidate_id", "")))
        candidate = candidates.get(candidate_id)
        technical = candidate_technical.get(candidate_id)
        if candidate is None or technical is None:
            errors.append(f"{label}.candidate_id is not in candidate_pool")
            continue
        selected_candidate_ids.append(candidate_id)
        slot_to_candidate[slot_name] = candidate_id

        article_role = normalize_space(str(slot.get("article_role", "")))
        if article_role not in IMAGE_ARTICLE_ROLES:
            errors.append(f"{label}.article_role is invalid: {article_role}")
        selected_roles.append(article_role)
        if len(normalize_space(str(slot.get("section_topic", "")))) < 12:
            errors.append(f"{label}.section_topic must identify the target section")
        if len(normalize_space(str(slot.get("selection_reason", "")))) < 30:
            errors.append(
                f"{label}.selection_reason must explain relevance and diversity"
            )

        scores = slot.get("scores")
        if not isinstance(scores, dict):
            errors.append(f"{label}.scores must be an object")
            scores = {}
        weighted_total = 0.0
        scores_valid = True
        for score_name, weight in IMAGE_SCORE_WEIGHTS.items():
            score = scores.get(score_name)
            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not 0 <= score <= 100
            ):
                errors.append(
                    f"{label}.scores.{score_name} must be between 0 and 100"
                )
                scores_valid = False
                continue
            weighted_total += float(score) * weight
        recorded_total = scores.get("weighted_total")
        if (
            isinstance(recorded_total, bool)
            or not isinstance(recorded_total, (int, float))
        ):
            errors.append(f"{label}.scores.weighted_total must be numeric")
        elif scores_valid and abs(float(recorded_total) - weighted_total) > 0.11:
            errors.append(
                f"{label}.scores.weighted_total must equal {weighted_total:.1f}"
            )

        record = reference_records.get(slot_name)
        if record is None:
            continue
        recorded_candidate_id = normalize_space(
            str(record.get("candidate_id", ""))
        )
        if recorded_candidate_id != candidate_id:
            errors.append(
                f"{slot_name} candidate_id must match selection_plan assignment"
            )
        record_classification = normalize_space(
            str(record.get("classification", ""))
        )
        if record_classification != technical["classification"]:
            errors.append(
                f"{slot_name} classification must match selected candidate"
            )
        record_urls = {
            normalize_space(str(item))
            for item in record.get("reference_urls", [])
        } if isinstance(record.get("reference_urls"), list) else set()
        if technical["url"] not in record_urls:
            errors.append(
                f"{slot_name} reference_urls must include its selected candidate URL"
            )
        record_files: set[Path] = set()
        if isinstance(record.get("reference_files"), list):
            for reference_file in record["reference_files"]:
                file_path = Path(str(reference_file))
                if not file_path.is_absolute():
                    file_path = manifest_path.parent / file_path
                record_files.add(file_path.resolve())
        if technical["path"] not in record_files:
            errors.append(
                f"{slot_name} reference_files must include its selected candidate file"
            )
        if (
            record_classification == "product-present"
            and technical["eligible"] is not True
        ):
            errors.append(
                f"{slot_name} product source must be eligible_for_product_lock"
            )

    if len(selected_roles) != len(set(selected_roles)):
        errors.append(
            "selection_plan must assign a distinct article_role to every image slot"
        )

    selected_counts = Counter(selected_candidate_ids)
    repeated_ids = {
        candidate_id: count
        for candidate_id, count in selected_counts.items()
        if count > 1
    }
    eligible_product_candidates = [
        candidate_id
        for candidate_id, technical in candidate_technical.items()
        if technical["classification"] == "product-present"
        and technical["eligible"] is True
    ]
    duplicate_exception = selection_plan.get("duplicate_exception")
    exception_used = bool(repeated_ids)
    if repeated_ids:
        if not isinstance(duplicate_exception, dict):
            errors.append(
                "Repeated source selection requires duplicate_exception evidence"
            )
            duplicate_exception = {}
        if len(repeated_ids) != 1:
            errors.append("Only one source may be repeated under an exception")
        repeated_id = next(iter(repeated_ids), "")
        if repeated_ids.get(repeated_id, 0) > 2:
            errors.append("A source may be reused at most twice under an exception")
        if len(eligible_product_candidates) != 1:
            errors.append(
                "A source may repeat only when exactly one eligible product image exists"
            )
        elif repeated_id != eligible_product_candidates[0]:
            errors.append(
                "The repeated source must be the sole eligible product candidate"
            )
        if normalize_space(str(duplicate_exception.get("candidate_id", ""))) != repeated_id:
            errors.append("duplicate_exception.candidate_id must match the reused source")
        exception_slots = nonempty_string_list(duplicate_exception.get("slots"))
        actual_exception_slots = sorted(
            slot_name
            for slot_name, candidate_id in slot_to_candidate.items()
            if candidate_id == repeated_id
        )
        if exception_slots is None or sorted(exception_slots) != actual_exception_slots:
            errors.append("duplicate_exception.slots must list the reused assignments")
        if duplicate_exception.get("valid_product_candidates") != 1:
            errors.append("duplicate_exception.valid_product_candidates must equal 1")
        if len(normalize_space(str(duplicate_exception.get("reason", "")))) < 30:
            errors.append("duplicate_exception.reason must explain the source shortage")
        if len(normalize_space(str(duplicate_exception.get("mitigation", "")))) < 40:
            errors.append(
                "duplicate_exception.mitigation must explain composition differences"
            )
    elif duplicate_exception is not None and duplicate_exception != {}:
        errors.append("duplicate_exception must be null when no source is repeated")

    selected_technical = [
        candidate_technical[candidate_id]
        for candidate_id in selected_candidate_ids
        if candidate_id in candidate_technical
    ]
    source_distances: list[int] = []
    for first_index, first in enumerate(selected_technical):
        for second in selected_technical[first_index + 1 :]:
            source_distances.append(
                perceptual_hash_distance(
                    str(first["phash"]),
                    str(second["phash"]),
                )
            )
    minimum_source_distance = min(source_distances) if source_distances else None

    output_hashes: dict[str, str] = {}
    for slot_name, record in reference_records.items():
        output_value = normalize_space(str(record.get("output_file", "")))
        output_path = Path(output_value) if output_value else Path()
        if output_value and not output_path.is_absolute():
            output_path = manifest_path.parent / output_path
        if not output_value or not output_path.is_file():
            continue
        try:
            _, output_phash, _, _ = image_fingerprint(output_path)
        except (OSError, ValueError):
            continue
        output_hashes[slot_name] = output_phash

    final_distances: list[int] = []
    output_items = list(output_hashes.items())
    for first_index, (first_slot, first_hash) in enumerate(output_items):
        for second_slot, second_hash in output_items[first_index + 1 :]:
            distance = perceptual_hash_distance(first_hash, second_hash)
            final_distances.append(distance)
            if distance < FINAL_IMAGE_MINIMUM_DISTANCE:
                errors.append(
                    f"Final images are too visually similar (pHash distance {distance}): "
                    f"{first_slot}, {second_slot}"
                )
    minimum_final_distance = min(final_distances) if final_distances else None

    if repeated_ids and isinstance(duplicate_exception, dict):
        exception_slots = nonempty_string_list(duplicate_exception.get("slots")) or []
        if len(exception_slots) == 2 and all(
            slot_name in output_hashes for slot_name in exception_slots
        ):
            reused_distance = perceptual_hash_distance(
                output_hashes[exception_slots[0]],
                output_hashes[exception_slots[1]],
            )
            if reused_distance < REUSED_SOURCE_FINAL_MINIMUM_DISTANCE:
                errors.append(
                    "Reused product source final scenes must differ by at least "
                    f"{REUSED_SOURCE_FINAL_MINIMUM_DISTANCE} pHash bits; "
                    f"received {reused_distance}"
                )

    return (
        len(candidate_pool),
        len(set(selected_candidate_ids)),
        minimum_source_distance,
        minimum_final_distance,
        exception_used,
        errors,
    )


def validate_image_references(
    path: Path,
    host: str,
    body_image_count: int,
) -> tuple[
    int,
    int,
    int,
    int,
    int,
    int,
    int,
    int | None,
    int | None,
    bool,
    list[str],
]:
    errors: list[str] = []
    try:
        value = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        return 0, 0, 0, 0, 0, 0, 0, None, None, False, [
            f"Image reference manifest is not valid JSON: {exc}"
        ]
    if not isinstance(value, dict):
        return 0, 0, 0, 0, 0, 0, 0, None, None, False, [
            "Image reference manifest must be a JSON object"
        ]

    thumbnail = value.get("thumbnail")
    body = value.get("body")
    if not isinstance(thumbnail, dict):
        errors.append("Image reference manifest must contain one thumbnail object")
        thumbnail = {}
    if not isinstance(body, list):
        errors.append("Image reference manifest body must be an array")
        body = []
    if len(body) != body_image_count:
        errors.append(
            f"Image reference manifest must contain {body_image_count} body records; "
            f"received {len(body)}"
        )

    site_has_product_visuals = value.get("site_has_product_visuals")
    if not isinstance(site_has_product_visuals, bool):
        errors.append("site_has_product_visuals must be true or false")
        site_has_product_visuals = False
    if (
        site_has_product_visuals is False
        and not normalize_space(str(value.get("no_product_visual_reason", "")))
    ):
        errors.append(
            "no_product_visual_reason is required when the site has no product visuals"
        )

    site_has_branded_product_visuals = value.get("site_has_branded_product_visuals")
    if not isinstance(site_has_branded_product_visuals, bool):
        errors.append("site_has_branded_product_visuals must be true or false")
        site_has_branded_product_visuals = False
    site_has_legible_product_labels = value.get("site_has_legible_product_labels")
    if not isinstance(site_has_legible_product_labels, bool):
        errors.append("site_has_legible_product_labels must be true or false")
        site_has_legible_product_labels = False
    if not site_has_product_visuals and (
        site_has_branded_product_visuals or site_has_legible_product_labels
    ):
        errors.append(
            "Branding or legible labels cannot be true when site_has_product_visuals is false"
        )
    if (
        site_has_product_visuals
        and not site_has_branded_product_visuals
        and not normalize_space(
            str(value.get("no_branded_product_visual_reason", ""))
        )
    ):
        errors.append(
            "no_branded_product_visual_reason is required when product visuals exist "
            "but visible branding does not"
        )
    if (
        site_has_product_visuals
        and not site_has_legible_product_labels
        and not normalize_space(
            str(value.get("no_legible_product_label_reason", ""))
        )
    ):
        errors.append(
            "no_legible_product_label_reason is required when product visuals exist "
            "but legible labels do not"
        )

    bare_host = host[4:] if host.startswith("www.") else host
    allowed_hosts = {bare_host, f"www.{bare_host}"}
    records: list[tuple[str, dict[str, object]]] = [("thumbnail", thumbnail)]
    records.extend((f"body[{index}]", record) for index, record in enumerate(body))
    product_present_count = 0
    whole_regenerated_product_count = 0
    brand_preserved_count = 0
    label_preserved_count = 0

    for label, record in records:
        if not isinstance(record, dict):
            errors.append(f"{label} image reference record must be an object")
            continue
        classification = normalize_space(str(record.get("classification", "")))
        if classification not in {"product-present", "non-product"}:
            errors.append(
                f"{label} classification must be product-present or non-product"
            )
        if classification == "product-present":
            product_present_count += 1

        reference_urls = record.get("reference_urls")
        if not isinstance(reference_urls, list) or not reference_urls:
            errors.append(f"{label} must include at least one same-site reference URL")
            reference_urls = []
        for reference_url in reference_urls:
            parsed = urlparse(str(reference_url))
            reference_host = (parsed.hostname or "").lower().rstrip(".")
            if parsed.scheme != "https" or reference_host not in allowed_hosts:
                errors.append(
                    f"{label} reference URL must be same-site HTTPS: {reference_url}"
                )

        reference_files = record.get("reference_files")
        if not isinstance(reference_files, list) or not reference_files:
            errors.append(f"{label} must include at least one local reference file")
            reference_files = []
        resolved_reference_paths: list[Path] = []
        for reference_file in reference_files:
            file_path = Path(str(reference_file))
            if not file_path.is_absolute():
                file_path = path.parent / file_path
            resolved_reference_paths.append(file_path.resolve())
            if not file_path.is_file():
                errors.append(f"{label} reference file does not exist: {file_path}")

        output_value = normalize_space(str(record.get("output_file", "")))
        output_path = Path(output_value) if output_value else Path()
        if output_value and not output_path.is_absolute():
            output_path = path.parent / output_path
        if not output_value or not output_path.is_file():
            errors.append(f"{label} output_file does not exist: {output_value}")
        elif output_path.suffix.lower() != ".webp":
            errors.append(f"{label} output_file must be WebP: {output_path}")

        retained_elements = record.get("retained_site_elements")
        if (
            not isinstance(retained_elements, list)
            or not any(normalize_space(str(item)) for item in retained_elements)
        ):
            errors.append(f"{label} must describe retained same-site visual elements")

        if classification == "product-present":
            adaptation_is_valid = True
            preservation_method = normalize_space(
                str(record.get("preservation_method", ""))
            )
            if preservation_method not in PRODUCT_PRESERVATION_METHODS:
                errors.append(
                    f"{label} preservation_method must be one of: "
                    + ", ".join(sorted(PRODUCT_PRESERVATION_METHODS))
                    + "; deterministic composites, background-only edits, "
                    "unchanged-source, and contain-only product images are not allowed"
                )
                adaptation_is_valid = False

            if (
                output_value
                and output_path.resolve() in resolved_reference_paths
            ):
                errors.append(
                    f"{label} output_file cannot be the unchanged source image"
                )
                adaptation_is_valid = False

            adaptation = record.get("adaptation")
            if not isinstance(adaptation, dict):
                errors.append(f"{label} adaptation must be an object")
                adaptation = {}
                adaptation_is_valid = False
            if adaptation.get("new_image_generated") is not True:
                errors.append(
                    f"{label} adaptation.new_image_generated must be true"
                )
                adaptation_is_valid = False
            expected_adaptation_method = PRODUCT_ADAPTATION_METHODS.get(
                preservation_method
            )
            adaptation_method = normalize_space(
                str(adaptation.get("adaptation_method", ""))
            )
            if (
                expected_adaptation_method is None
                or adaptation_method != expected_adaptation_method
            ):
                expected_text = (
                    expected_adaptation_method
                    or "a method matching preservation_method"
                )
                errors.append(
                    f"{label} adaptation.adaptation_method must be "
                    f"{expected_text}"
                )
                adaptation_is_valid = False
            if adaptation.get("source_product_locked") is not True:
                errors.append(
                    f"{label} adaptation.source_product_locked must be true"
                )
                adaptation_is_valid = False
            if adaptation.get("whole_image_regenerated") is not True:
                errors.append(
                    f"{label} adaptation.whole_image_regenerated must be true"
                )
                adaptation_is_valid = False
            if adaptation.get("deterministic_composite_used") is not False:
                errors.append(
                    f"{label} adaptation.deterministic_composite_used must be false"
                )
                adaptation_is_valid = False
            if adaptation.get("source_canvas_reused_as_final") is not False:
                errors.append(
                    f"{label} adaptation.source_canvas_reused_as_final must be false"
                )
                adaptation_is_valid = False
            if not normalize_space(
                str(adaptation.get("scene_description", ""))
            ):
                errors.append(
                    f"{label} adaptation.scene_description is required"
                )
                adaptation_is_valid = False

            locked_product_value = normalize_space(
                str(adaptation.get("locked_product_file", ""))
            )
            locked_product_path = (
                Path(locked_product_value) if locked_product_value else Path()
            )
            if locked_product_value and not locked_product_path.is_absolute():
                locked_product_path = path.parent / locked_product_path
            if (
                not locked_product_value
                or not locked_product_path.is_file()
                or locked_product_path.suffix.lower() != ".png"
            ):
                errors.append(
                    f"{label} adaptation.locked_product_file must be an "
                    f"existing PNG: {locked_product_value}"
                )
                adaptation_is_valid = False
            elif (
                locked_product_path.resolve() in resolved_reference_paths
                or (
                    output_value
                    and locked_product_path.resolve() == output_path.resolve()
                )
            ):
                errors.append(
                    f"{label} adaptation.locked_product_file must be a "
                    "separate extracted product asset"
                )
                adaptation_is_valid = False

            lock_mask_value = normalize_space(
                str(adaptation.get("lock_mask_file", ""))
            )
            lock_mask_path = (
                Path(lock_mask_value) if lock_mask_value else Path()
            )
            if lock_mask_value and not lock_mask_path.is_absolute():
                lock_mask_path = path.parent / lock_mask_path
            if (
                not lock_mask_value
                or not lock_mask_path.is_file()
                or lock_mask_path.suffix.lower() != ".png"
            ):
                errors.append(
                    f"{label} adaptation.lock_mask_file must be an existing "
                    f"PNG: {lock_mask_value}"
                )
                adaptation_is_valid = False
            elif (
                lock_mask_path.resolve() in resolved_reference_paths
                or (
                    output_value
                    and lock_mask_path.resolve() == output_path.resolve()
                )
                or (
                    locked_product_value
                    and lock_mask_path.resolve() == locked_product_path.resolve()
                )
            ):
                errors.append(
                    f"{label} adaptation.lock_mask_file must be a separate "
                    "inspected mask asset"
                )
                adaptation_is_valid = False

            lock_report_value = normalize_space(
                str(adaptation.get("lock_report_file", ""))
            )
            lock_report_path = (
                Path(lock_report_value) if lock_report_value else Path()
            )
            if lock_report_value and not lock_report_path.is_absolute():
                lock_report_path = path.parent / lock_report_path
            if (
                not lock_report_value
                or not lock_report_path.is_file()
                or lock_report_path.suffix.lower() != ".json"
            ):
                errors.append(
                    f"{label} adaptation.lock_report_file must be an existing "
                    f"JSON file: {lock_report_value}"
                )
                adaptation_is_valid = False
            else:
                try:
                    lock_report = json.loads(read_text(lock_report_path))
                except json.JSONDecodeError as exc:
                    errors.append(
                        f"{label} lock report is not valid JSON: {exc}"
                    )
                    lock_report = {}
                    adaptation_is_valid = False
                if not isinstance(lock_report, dict):
                    errors.append(f"{label} lock report must be a JSON object")
                    lock_report = {}
                    adaptation_is_valid = False
                report_source_value = normalize_space(
                    str(lock_report.get("source", ""))
                )
                report_source_path = (
                    Path(report_source_value)
                    if report_source_value
                    else Path()
                )
                report_mask_value = normalize_space(
                    str(lock_report.get("mask", ""))
                )
                report_mask_path = (
                    Path(report_mask_value) if report_mask_value else Path()
                )
                report_locked_value = normalize_space(
                    str(lock_report.get("locked_product", ""))
                )
                report_locked_path = (
                    Path(report_locked_value)
                    if report_locked_value
                    else Path()
                )
                if (
                    not report_source_value
                    or report_source_path.resolve()
                    not in resolved_reference_paths
                ):
                    errors.append(
                        f"{label} lock report source must match a reference file"
                    )
                    adaptation_is_valid = False
                if (
                    not report_mask_value
                    or report_mask_path.resolve() != lock_mask_path.resolve()
                ):
                    errors.append(
                        f"{label} lock report mask must match lock_mask_file"
                    )
                    adaptation_is_valid = False
                if (
                    not report_locked_value
                    or report_locked_path.resolve()
                    != locked_product_path.resolve()
                ):
                    errors.append(
                        f"{label} lock report locked_product must match "
                        "locked_product_file"
                    )
                    adaptation_is_valid = False
                if lock_report.get("product_rgb_repainted") is not False:
                    errors.append(
                        f"{label} lock report product_rgb_repainted must be false"
                    )
                    adaptation_is_valid = False
                if (
                    normalize_space(str(lock_report.get("operation", "")))
                    != "alpha-mask-extraction-only"
                ):
                    errors.append(
                        f"{label} lock report operation must be "
                        "alpha-mask-extraction-only"
                    )
                    adaptation_is_valid = False

            generated_asset_files = adaptation.get("generated_asset_files")
            if (
                not isinstance(generated_asset_files, list)
                or len(generated_asset_files) < 1
            ):
                errors.append(
                    f"{label} adaptation.generated_asset_files must contain at "
                    "least one raw whole-image generation"
                )
                generated_asset_files = []
                adaptation_is_valid = False
            for generated_asset_file in generated_asset_files:
                generated_path = Path(str(generated_asset_file))
                if not generated_path.is_absolute():
                    generated_path = path.parent / generated_path
                generated_resolved = generated_path.resolve()
                if not generated_path.is_file():
                    errors.append(
                        f"{label} generated asset does not exist: "
                        f"{generated_path}"
                    )
                    adaptation_is_valid = False
                if generated_resolved in resolved_reference_paths:
                    errors.append(
                        f"{label} generated asset cannot be a source reference: "
                        f"{generated_path}"
                    )
                    adaptation_is_valid = False
                if (
                    locked_product_value
                    and generated_resolved == locked_product_path.resolve()
                ) or (
                    lock_mask_value
                    and generated_resolved == lock_mask_path.resolve()
                ) or (
                    lock_report_value
                    and generated_resolved == lock_report_path.resolve()
                ):
                    errors.append(
                        f"{label} generated asset must be the raw whole-image "
                        f"generation, not a lock input: {generated_path}"
                    )
                    adaptation_is_valid = False
                if output_value and generated_resolved == output_path.resolve():
                    errors.append(
                        f"{label} generated asset must be a raw pre-WebP asset, "
                        f"not output_file: {generated_path}"
                    )
                    adaptation_is_valid = False

            prompt_value = normalize_space(
                str(adaptation.get("prompt_file", ""))
            )
            prompt_path = Path(prompt_value) if prompt_value else Path()
            if prompt_value and not prompt_path.is_absolute():
                prompt_path = path.parent / prompt_path
            if (
                not prompt_value
                or not prompt_path.is_file()
                or prompt_path.stat().st_size < 1
            ):
                errors.append(
                    f"{label} adaptation.prompt_file must be a non-empty file: "
                    f"{prompt_value}"
                )
                adaptation_is_valid = False

            source_identity = record.get("source_identity")
            if not isinstance(source_identity, dict):
                errors.append(f"{label} source_identity must be an object")
                source_identity = {}
            brand_text = nonempty_string_list(source_identity.get("brand_text"))
            label_text = nonempty_string_list(source_identity.get("label_text"))
            packaging_details = nonempty_string_list(
                source_identity.get("packaging_details")
            )
            if brand_text is None:
                errors.append(
                    f"{label} source_identity.brand_text must be an array of "
                    "non-empty exact strings"
                )
                brand_text = []
            if label_text is None:
                errors.append(
                    f"{label} source_identity.label_text must be an array of "
                    "non-empty exact strings"
                )
                label_text = []
            if not packaging_details:
                errors.append(
                    f"{label} source_identity.packaging_details must contain "
                    "verified packaging details"
                )

            identity_checks = record.get("identity_checks")
            if not isinstance(identity_checks, dict):
                errors.append(f"{label} identity_checks must be an object")
                identity_checks = {}
            brand_check = normalize_space(
                str(identity_checks.get("brand_text", ""))
            ).lower()
            label_check = normalize_space(
                str(identity_checks.get("label_text", ""))
            ).lower()
            packaging_check = normalize_space(
                str(identity_checks.get("packaging", ""))
            ).lower()
            geometry_check = normalize_space(
                str(identity_checks.get("product_geometry", ""))
            ).lower()

            expected_brand_check = "pass" if brand_text else NOT_VISIBLE
            expected_label_check = "pass" if label_text else NOT_VISIBLE
            if brand_check != expected_brand_check:
                errors.append(
                    f"{label} identity_checks.brand_text must be "
                    f"{expected_brand_check}"
                )
            elif brand_check == "pass":
                brand_preserved_count += 1
            if label_check != expected_label_check:
                errors.append(
                    f"{label} identity_checks.label_text must be "
                    f"{expected_label_check}"
                )
            elif label_check == "pass":
                label_preserved_count += 1
            if packaging_check != "pass":
                errors.append(f"{label} identity_checks.packaging must be pass")
            if geometry_check != "pass":
                errors.append(
                    f"{label} identity_checks.product_geometry must be pass"
                )

            visual_inspection = record.get("visual_inspection")
            if not isinstance(visual_inspection, dict):
                errors.append(f"{label} visual_inspection must be an object")
                visual_inspection = {}
                adaptation_is_valid = False
            if (
                normalize_space(
                    str(visual_inspection.get("comparison_mode", ""))
                ).lower()
                != "side-by-side-100-percent"
            ):
                errors.append(
                    f"{label} visual_inspection.comparison_mode must be "
                    "side-by-side-100-percent"
                )
                adaptation_is_valid = False
            if (
                normalize_space(
                    str(visual_inspection.get("source_vs_locked_product", ""))
                ).lower()
                != "pass"
            ):
                errors.append(
                    f"{label} visual_inspection.source_vs_locked_product "
                    "must be pass"
                )
                adaptation_is_valid = False
            if (
                normalize_space(
                    str(
                        visual_inspection.get(
                            "locked_product_vs_generated", ""
                        )
                    )
                ).lower()
                != "pass"
            ):
                errors.append(
                    f"{label} visual_inspection.locked_product_vs_generated "
                    "must be pass"
                )
                adaptation_is_valid = False
            if (
                normalize_space(
                    str(visual_inspection.get("source_vs_final_webp", ""))
                ).lower()
                != "pass"
            ):
                errors.append(
                    f"{label} visual_inspection.source_vs_final_webp must be pass"
                )
                adaptation_is_valid = False

            if adaptation_is_valid:
                whole_regenerated_product_count += 1

        if normalize_space(str(record.get("inspection_result", ""))).lower() != "pass":
            errors.append(f"{label} inspection_result must be pass")

    if site_has_product_visuals:
        if thumbnail.get("classification") != "product-present":
            errors.append(
                "Thumbnail must be product-present when same-site product visuals exist"
            )
        if not any(
            isinstance(record, dict)
            and record.get("classification") == "product-present"
            for record in body
        ):
            errors.append(
                "At least one body image must be product-present when product visuals exist"
            )

    if site_has_branded_product_visuals:
        thumbnail_brand_text = (
            thumbnail.get("source_identity", {}).get("brand_text", [])
            if isinstance(thumbnail.get("source_identity"), dict)
            else []
        )
        if not nonempty_string_list(thumbnail_brand_text):
            errors.append(
                "Thumbnail must preserve exact source brand text when branded "
                "product visuals exist"
            )
        if not any(
            isinstance(record, dict)
            and record.get("classification") == "product-present"
            and isinstance(record.get("source_identity"), dict)
            and nonempty_string_list(
                record["source_identity"].get("brand_text")
            )
            for record in body
        ):
            errors.append(
                "At least one body image must preserve exact source brand text "
                "when branded product visuals exist"
            )

    if site_has_legible_product_labels:
        thumbnail_label_text = (
            thumbnail.get("source_identity", {}).get("label_text", [])
            if isinstance(thumbnail.get("source_identity"), dict)
            else []
        )
        if not nonempty_string_list(thumbnail_label_text):
            errors.append(
                "Thumbnail must preserve exact source label text when legible "
                "product labels exist"
            )
        if not any(
            isinstance(record, dict)
            and record.get("classification") == "product-present"
            and isinstance(record.get("source_identity"), dict)
            and nonempty_string_list(
                record["source_identity"].get("label_text")
            )
            for record in body
        ):
            errors.append(
                "At least one body image must preserve exact source label text "
                "when legible product labels exist"
            )

    (
        selection_candidate_count,
        selection_unique_sources,
        minimum_source_distance,
        minimum_final_distance,
        duplicate_exception_used,
        selection_errors,
    ) = validate_image_selection(
        value,
        path,
        host,
        body_image_count,
        thumbnail,
        body,
    )
    errors.extend(selection_errors)

    return (
        len(records),
        product_present_count,
        whole_regenerated_product_count,
        brand_preserved_count,
        label_preserved_count,
        selection_candidate_count,
        selection_unique_sources,
        minimum_source_distance,
        minimum_final_distance,
        duplicate_exception_used,
        errors,
    )


def first_keyword_is_linked(
    segments: list[tuple[str, str | None]], keyword: str
) -> tuple[bool, str]:
    combined = ""
    spans: list[tuple[int, int, str | None]] = []
    for text, href in segments:
        start = len(combined)
        combined += text
        spans.append((start, len(combined), href))
    match = re.search(re.escape(keyword), combined, flags=re.IGNORECASE)
    if not match:
        return False, "Lead paragraph does not contain the exact core keyword"
    for start, end, href in spans:
        if start <= match.start() < end:
            if not href:
                return False, "First core-keyword occurrence in the lead is not linked"
            return True, href
    return False, "Unable to locate the first core-keyword occurrence"


def title_case_errors(title: str) -> list[str]:
    errors = []
    for token in WORD_RE.findall(title):
        first_alpha = next((char for char in token if char.isalpha()), "")
        if first_alpha and not first_alpha.isupper():
            errors.append(token)
    return errors


def validate(args: argparse.Namespace) -> dict[str, object]:
    title = read_text(args.title_file)
    seo_title = read_text(args.seo_title_file)
    remark = read_text(args.remark_file)
    seo_desc = read_text(args.seo_desc_file)
    content = read_text(args.content_file)
    alt_texts = read_alt_texts(args.alt_text_file)
    keyword = normalize_space(args.keyword)
    target_country = normalize_space(args.target_country)
    target_customer = normalize_space(args.target_customer)
    title_angle = normalize_space(args.title_angle)
    title_pattern = normalize_space(args.title_pattern)
    search_intent = normalize_space(args.search_intent)
    buyer_stage = normalize_space(args.buyer_stage)
    ending_mode = normalize_space(args.ending_mode)
    host = args.site_host.lower().strip().rstrip(".")
    errors: list[str] = []
    audience_title_terms, audience_title_errors = validate_title_audience_context(
        title,
        keyword,
        target_country,
        target_customer,
    )
    (
        title_question_roll,
        title_mode,
        title_is_question,
        title_mode_errors,
    ) = validate_title_mode(
        title,
        keyword,
        args.title_mode_seed,
    )
    (
        title_history_compared,
        max_title_similarity,
        title_diversity_errors,
    ) = validate_title_diversity(
        title,
        keyword,
        title_angle,
        title_pattern,
        title_mode,
        args.title_history_file,
    )
    errors.extend(audience_title_errors)
    errors.extend(title_mode_errors)
    errors.extend(title_diversity_errors)
    (
        research_source_count,
        same_site_research_sources,
        external_research_sources,
        related_keywords,
        secondary_intent,
        recorded_buyer_stage,
        intent_analysis_errors,
    ) = validate_intent_analysis(
        args.intent_analysis_file,
        keyword,
        search_intent,
        buyer_stage,
        host,
    )
    errors.extend(intent_analysis_errors)
    (
        image_reference_records,
        product_present_images,
        whole_regenerated_product_images,
        brand_preserved_images,
        label_preserved_images,
        image_candidate_pool,
        image_unique_selected_sources,
        image_minimum_source_phash_distance,
        image_minimum_final_phash_distance,
        image_duplicate_exception_used,
        image_reference_errors,
    ) = validate_image_references(
        args.image_reference_file,
        host,
        args.content_images,
    )
    errors.extend(image_reference_errors)

    if not title or len(title) > 100:
        errors.append(f"Title must be 1–100 characters; received {len(title)}")
    if title != seo_title:
        errors.append("seo_title1 must equal title")
    if re.search(r"\b(?:we|our|ours)\b", title, flags=re.IGNORECASE):
        errors.append("Title must use a neutral third-person editorial voice")
    bad_title_tokens = title_case_errors(title)
    if bad_title_tokens:
        errors.append("Title is not Title Case: " + ", ".join(bad_title_tokens[:8]))
    if remark != seo_desc:
        errors.append("remark must equal seo_desc")
    if not seo_desc or len(seo_desc) > 200:
        errors.append(f"seo_desc must be 1–200 characters; received {len(seo_desc)}")
    if keyword.lower() not in seo_desc.lower():
        errors.append("seo_desc must contain the exact core keyword")

    placeholder_count = content.count(PLACEHOLDER)
    if placeholder_count != args.content_images:
        errors.append(
            f"Placeholder count must equal content image count; "
            f"received {placeholder_count} and {args.content_images}"
        )
    if not 4 <= args.content_images <= 5:
        errors.append("Content image count must be between 4 and 5")
    if len(alt_texts) != args.content_images:
        errors.append(
            f"Alt text count must equal content image count; "
            f"received {len(alt_texts)} and {args.content_images}"
        )
    if any(not value for value in alt_texts):
        errors.append("Alt text values cannot be empty")
    if len({value.casefold() for value in alt_texts}) != len(alt_texts):
        errors.append("Every body image must have distinct alt text")

    parser = ArticleParser()
    parser.feed(content)
    parser.close()
    errors.extend(parser.errors)
    (
        cta_word_count,
        cta_audience_terms,
        ending_errors,
    ) = validate_article_ending(
        parser,
        content,
        target_country,
        target_customer,
        search_intent,
        buyer_stage,
        ending_mode,
    )
    errors.extend(ending_errors)
    if parser.h1_count:
        errors.append("content.html must not contain an H1")
    if parser.img_count:
        errors.append("content.html must use placeholders, not pre-existing img tags")
    if parser.article_toc_count:
        errors.append("content.html must not contain an article table of contents")
    if any(href.startswith("#") for href, _ in parser.links):
        errors.append("content.html must not contain generated in-page anchor-directory links")
    if parser.style_count != 1:
        errors.append(
            f"content.html must contain exactly one scoped style block; "
            f"received {parser.style_count}"
        )
    if parser.responsive_style_count != 1:
        errors.append(
            f"Missing <style data-article-style=\"{STYLE_VERSION}\">"
        )
    if parser.article_wrapper_count != 1:
        errors.append(
            f"content.html must contain exactly one <article class=\"article-content\">; "
            f"received {parser.article_wrapper_count}"
        )

    css = "\n".join(parser.style_parts)
    (
        theme_evidence_count,
        theme_color_count,
        theme_minimum_contrast,
        theme_errors,
    ) = validate_site_theme(
        args.theme_colors_file,
        host,
        css,
    )
    errors.extend(theme_errors)
    css_requirements = [
        (r"\.article-content\s*\{", "Missing scoped .article-content root styles"),
        (
            r"\.article-content\s+\.article-table-wrap\s*\{",
            "Missing responsive .article-table-wrap styles",
        ),
        (r"\.article-content\s+table\s*\{", "Missing scoped table styles"),
        (
            r"\.article-content\s+figure\s+img\s*\{",
            "Missing responsive article image styles",
        ),
        (r"box-sizing\s*:\s*border-box", "Missing scoped box-sizing"),
        (r"overflow-x\s*:\s*auto", "Table wrapper must allow horizontal overflow"),
        (r"max-width\s*:\s*100%", "Responsive content must use max-width: 100%"),
        (r"height\s*:\s*auto", "Responsive images must use height: auto"),
    ]
    for pattern, message in css_requirements:
        if not re.search(pattern, css, flags=re.IGNORECASE):
            errors.append(message)
    font_size_values = [
        normalize_space(value)
        for value in re.findall(
            r"font-size\s*:\s*([^;}]+)",
            css,
            flags=re.IGNORECASE,
        )
    ]
    non_px_font_sizes = [
        value
        for value in font_size_values
        if not re.fullmatch(
            r"(?:0|(?:\d+(?:\.\d+)?|\.\d+)px)(?:\s*!important)?",
            value,
            flags=re.IGNORECASE,
        )
    ]
    if not font_size_values:
        errors.append("Article CSS must declare fixed pixel-based font sizes")
    if non_px_font_sizes:
        errors.append(
            "Every font-size declaration must use one fixed px value; found: "
            + ", ".join(non_px_font_sizes[:6])
        )
    if re.search(r"(?<![\w-])(?:\d+(?:\.\d+)?|\.\d+)rem\b", css, flags=re.IGNORECASE):
        errors.append("Article CSS must not contain rem units")
    breakpoints = [
        int(value)
        for value in re.findall(
            r"@media\s*\(\s*max-width\s*:\s*(\d+)px\s*\)",
            css,
            flags=re.IGNORECASE,
        )
    ]
    if len(set(breakpoints)) < 2 or not any(value <= 768 for value in breakpoints):
        errors.append("Responsive CSS must include at least two mobile max-width breakpoints")
    if re.search(
        r"(?:^|[},])\s*(?:html|body)(?:\b|[.#:\[])",
        css,
        flags=re.IGNORECASE,
    ):
        errors.append("Article CSS must not style global html or body selectors")
    if parser.table_count < 1:
        errors.append("Article must contain at least one useful table")
    if parser.wrapped_table_count != parser.table_count:
        errors.append("Every table must be inside one .article-table-wrap container")
    if parser.figure_count != args.content_images:
        errors.append(
            f"Every body image placeholder must use one figure; "
            f"received {parser.figure_count} figures for {args.content_images} images"
        )

    h2s = [heading for heading in parser.headings if heading["tag"] == "h2"]
    if not 5 <= len(h2s) <= 9:
        errors.append(f"Article must contain 5–9 H2 headings; received {len(h2s)}")
    heading_ids = [heading["id"] for heading in parser.headings if heading["id"]]
    if any(not ANCHOR_RE.fullmatch(value) for value in heading_ids):
        errors.append("Heading ids must use lowercase words and hyphens")
    if len(set(heading_ids)) != len(heading_ids):
        errors.append("Heading ids must be unique")
    if not 4 <= parser.faq_questions <= 6:
        errors.append(f"FAQ must contain 4–6 H3 questions; received {parser.faq_questions}")

    visible = normalize_space(" ".join(parser.text_parts).replace(PLACEHOLDER, ""))
    visible_characters = len(visible)
    if not (
        ARTICLE_MIN_VISIBLE_CHARACTERS
        <= visible_characters
        <= ARTICLE_MAX_VISIBLE_CHARACTERS
    ):
        errors.append(
            "Visible article content must be 10,000–15,000 characters; "
            f"received {visible_characters}"
        )
    (
        non_faq_h3_count,
        non_faq_h3_parent_sections,
        non_faq_h3_required_parent_sections,
        non_faq_h3_minimum_required,
        h3_depth_errors,
    ) = validate_non_faq_h3_depth(
        h2s,
        parser.h3_sections,
        visible_characters,
    )
    errors.extend(h3_depth_errors)
    expected_images = 4 if visible_characters < 12500 else 5
    if args.content_images != expected_images:
        errors.append(
            f"Visible length requires {expected_images} body images; "
            f"received {args.content_images}"
        )

    keyword_metrics, keyword_usage_errors = validate_keyword_usage(
        parser.content_blocks,
        visible,
        keyword,
        related_keywords,
    )
    errors.extend(keyword_usage_errors)

    first_paragraph = normalize_space(
        "".join(text for text, _ in parser.first_paragraph_segments)
    )
    if seo_desc not in first_paragraph:
        errors.append("seo_desc must be a complete sentence copied from the lead paragraph")
    keyword_linked, lead_href = first_keyword_is_linked(
        parser.first_paragraph_segments, keyword
    )
    if not keyword_linked:
        errors.append(lead_href)

    internal_links = []
    for href, text in parser.links:
        if href.startswith("#"):
            continue
        parsed = urlparse(href)
        link_host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https" or link_host not in {host, f"www.{host}"}:
            errors.append(f"Article link must be same-site HTTPS: {href}")
        else:
            internal_links.append((href, text))
        if text.lower() in {"click here", "read more"}:
            errors.append(f"Non-descriptive anchor text is not allowed: {text}")
    min_links = math.ceil(visible_characters / 2000)
    max_links = math.ceil(visible_characters / 1000)
    if not min_links <= len(internal_links) <= max_links:
        errors.append(
            f"Internal link count must be {min_links}–{max_links}; "
            f"received {len(internal_links)}"
        )
    if keyword_linked:
        lead_host = (urlparse(lead_href).hostname or "").lower().rstrip(".")
        if lead_host not in {host, f"www.{host}"}:
            errors.append("The lead core-keyword link must point to the same site")

    lowered = visible.lower()
    banned = [
        "welcome to our blog",
        "global number one",
        "100% guaranteed",
        "best in the world",
    ]
    for phrase in banned:
        if phrase in lowered:
            errors.append(f"Unsupported promotional phrase: {phrase}")
    if re.search(r"\b(?:we|our|ours)\b", visible, flags=re.IGNORECASE):
        errors.append(
            "Article content must use a neutral third-person editorial voice, not "
            "first-person brand promotion"
        )

    result: dict[str, object] = {
        "valid": not errors,
        "metrics": {
            "title_characters": len(title),
            "title_angle": title_angle,
            "title_pattern": title_pattern,
            "title_question_probability": QUESTION_TITLE_PROBABILITY,
            "title_question_roll": title_question_roll,
            "title_mode": title_mode,
            "title_is_question": title_is_question,
            "title_history_compared": title_history_compared,
            "max_title_similarity": max_title_similarity,
            "target_audience_title_terms": audience_title_terms,
            "search_intent": search_intent,
            "secondary_intent": secondary_intent,
            "selected_intent_count": 1 + int(bool(secondary_intent)),
            "buyer_stage": recorded_buyer_stage,
            "ending_mode": ending_mode,
            "cta_inline_markers": parser.cta_inline_count,
            "cta_standalone_markers": parser.cta_standalone_count,
            "cta_word_count": cta_word_count,
            "cta_audience_terms": cta_audience_terms,
            "research_sources": research_source_count,
            "same_site_research_sources": same_site_research_sources,
            "external_research_sources": external_research_sources,
            "related_keywords": related_keywords,
            **keyword_metrics,
            "seo_description_characters": len(seo_desc),
            "visible_characters": visible_characters,
            "visible_characters_preferred_range": (
                ARTICLE_PREFERRED_MIN_VISIBLE_CHARACTERS
                <= visible_characters
                <= ARTICLE_PREFERRED_MAX_VISIBLE_CHARACTERS
            ),
            "h2_count": len(h2s),
            "non_faq_h3_count": non_faq_h3_count,
            "non_faq_h3_parent_sections": non_faq_h3_parent_sections,
            "non_faq_h3_required_parent_sections": (
                non_faq_h3_required_parent_sections
            ),
            "non_faq_h3_minimum_required": non_faq_h3_minimum_required,
            "non_faq_h3_minimum_content_characters": (
                NON_FAQ_H3_MIN_CONTENT_CHARACTERS
            ),
            "faq_questions": parser.faq_questions,
            "internal_links": len(internal_links),
            "content_images": args.content_images,
            "placeholders": placeholder_count,
            "responsive_style_blocks": parser.responsive_style_count,
            "article_wrappers": parser.article_wrapper_count,
            "tables": parser.table_count,
            "table_wrappers": parser.wrapped_table_count,
            "theme_evidence_observations": theme_evidence_count,
            "theme_color_variables": theme_color_count,
            "theme_minimum_contrast": theme_minimum_contrast,
            "font_size_declarations": len(font_size_values),
            "font_sizes_px_only": bool(font_size_values) and not non_px_font_sizes,
            "image_reference_records": image_reference_records,
            "product_present_images": product_present_images,
            "whole_regenerated_product_images": (
                whole_regenerated_product_images
            ),
            "brand_preserved_images": brand_preserved_images,
            "label_preserved_images": label_preserved_images,
            "image_candidate_pool": image_candidate_pool,
            "image_unique_selected_sources": image_unique_selected_sources,
            "image_minimum_source_phash_distance": (
                image_minimum_source_phash_distance
            ),
            "image_minimum_final_phash_distance": (
                image_minimum_final_phash_distance
            ),
            "image_duplicate_exception_used": image_duplicate_exception_used,
        },
        "errors": errors,
    }
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title-file", type=Path, required=True)
    parser.add_argument("--seo-title-file", type=Path, required=True)
    parser.add_argument("--remark-file", type=Path, required=True)
    parser.add_argument("--seo-desc-file", type=Path, required=True)
    parser.add_argument("--content-file", type=Path, required=True)
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--target-country", required=True)
    parser.add_argument("--target-customer", required=True)
    parser.add_argument("--title-angle", choices=sorted(TITLE_ANGLES), required=True)
    parser.add_argument("--title-pattern", choices=sorted(TITLE_PATTERNS), required=True)
    parser.add_argument("--title-mode-seed", required=True)
    parser.add_argument("--title-history-file", type=Path, required=True)
    parser.add_argument("--search-intent", choices=sorted(SEARCH_INTENTS), required=True)
    parser.add_argument("--buyer-stage", choices=sorted(BUYER_STAGES), required=True)
    parser.add_argument("--ending-mode", choices=sorted(ENDING_MODES), required=True)
    parser.add_argument("--intent-analysis-file", type=Path, required=True)
    parser.add_argument("--site-host", required=True)
    parser.add_argument("--theme-colors-file", type=Path, required=True)
    parser.add_argument("--content-images", type=int, required=True)
    parser.add_argument("--alt-text-file", type=Path, required=True)
    parser.add_argument("--image-reference-file", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    result = validate(parse_args())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
