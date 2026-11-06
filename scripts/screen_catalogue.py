#!/usr/bin/env python3
"""Triage current-run product list metadata before opening product details."""

import argparse
import json
from collections import Counter
from pathlib import Path


def normalize(value):
    return " ".join(value.casefold().split())


def screen_products(products, terms, boilerplate):
    terms = list(dict.fromkeys(normalize(term) for term in terms if term.strip()))
    boilerplate = sorted({normalize(phrase) for phrase in boilerplate if phrase.strip()},
                         key=lambda phrase: (-len(phrase), phrase))
    if not terms:
        raise ValueError("Provide at least one nonempty search term")

    decisions = []
    for product in products:
        title = normalize(product.get("title", ""))
        list_text = normalize(product.get("list_text", ""))
        for phrase in boilerplate:
            list_text = list_text.replace(phrase, " ")
        matched_terms = [term for term in terms if term in title or term in list_text]
        if matched_terms:
            decision, reason = "open-detail", "matched-list-metadata"
        elif not title or not list_text.strip():
            decision, reason = "open-detail", "insufficient-list-metadata"
        else:
            decision, reason = "review-list", "needs-family-or-use-case-review"
        decisions.append({
            "url": product["url"],
            "title": product.get("title", ""),
            "screened_list_text": " ".join(list_text.split()),
            "decision": decision,
            "reason": reason,
            "matched_terms": matched_terms,
        })

    return {
        "terms": terms,
        "removed_phrases": boilerplate,
        "counts": dict(Counter(item["decision"] for item in decisions)),
        "products": decisions,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("products", type=Path, help="JSON array of deduplicated product records")
    parser.add_argument("--term", action="append", required=True, help="Search term, repeatable")
    parser.add_argument("--boilerplate", action="append", default=[], help="Template phrase, repeatable")
    args = parser.parse_args()
    try:
        products = json.loads(args.products.read_text(encoding="utf-8"))
        if not isinstance(products, list):
            raise ValueError("Expected a JSON array of product records")
        result = screen_products(products, args.term, args.boilerplate)
    except (OSError, ValueError, AttributeError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
