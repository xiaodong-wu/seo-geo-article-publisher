# Fresh image selection and reuse control

Read before selecting images, including on retries. Discovery supplies the sources; article intent
determines eligibility; recent usage breaks ties among similarly relevant candidates. A new scene
around the same original product still counts as reuse of that source.

## Current-run evidence

1. Finish whole-site discovery as described in `product-discovery.md`. For every verified relevant
   match, inspect the entire original gallery, including alternate views and gallery slides.
   Also inspect the supporting pages needed by the article. Save page HTML, extracted gallery
   inventories, or screenshots under the current row directory. Previous results may locate pages
   but cannot supply this run's candidate inventory without a fresh page/gallery inspection.
2. Give every observed image a disposition: `candidate`, `excluded`, `duplicate`, or
   `shortlisted-out`, with a specific reason. Record `eligible_for_product_lock` and
   `topic_relation` even for images not shortlisted. `excluded` means unusable/irrelevant, not
   simply lower ranked. A usable image omitted for pool size remains `shortlisted-out`.
   Compare duplicate fingerprints and identify the retained candidate with `duplicate_of`.
3. Download and inspect candidate originals inside this row directory. Analyze fingerprints with
   `analyze_image_pool.py` (batches of at most 12 if necessary), consolidate exact and near duplicates
   across batches, then retain 3–8 relevant candidates. Preserve each retained candidate's gallery
   page and product URL. A broad catalogue scan followed by reuse of the old five-image pool does
   not satisfy this step.
4. Record topic relationship from the keyword, article intent, and actual product identity:
   `primary-topic`, `supporting-context`, or `comparison-only`. Plant-protein packaging in a whey
   article is comparison-only and may appear only in a clearly identified comparison section.
   It cannot become the main whey-product thumbnail. When no verified primary-topic product
   image exists, use a truthful relevant same-site process or laboratory scene. Do not claim a
   product is unavailable site-wide when catalogue access was incomplete.

The single-source exception requires `coverage_status: complete`, no `coverage_gaps`, and exactly
one eligible primary-topic product source across **all inspected relevant galleries**, after
duplicate consolidation. An alternate usable view left out of the shortlist invalidates the
exception. Keep the existing two-slot limit, different roles/scenes, documented mitigation, and
12-bit final-image separation. Comparison-only products do not prove availability of a primary-topic
product source and cannot be repeated under this exception.

## Recent usage and scoring

Build `<row-run-dir>/image-history.json` using:

```bash
python scripts/image_selection.py history --runs-dir /absolute/workspace/article-runs \
  --site-host www.example.com --run-id RUN_ID --output ROW_RUN_DIR/image-history.json
```

The script reads the 20 most recent locally recorded same-site published/API-success articles,
including those pending public verification, and counts each article URL once. It copies only
publication/image evidence, never raw Sheet rows or publishing keys. Inspect the live article
archive too and save evidence. Report articles without local source records and history gaps in
`live_archive_review.coverage_note` and the run manifest; do not call a source unused site-wide
merely because local history lacks its record. Historical records are reuse evidence only.

For every candidate × slot pair, state eligibility and score these inspected properties 0–100:
keyword/product relevance (30%), identity clarity (25%), image quality (15%), and section fit (15%).
Give a concrete explanation for each score. For non-product scenes, identity clarity means clarity
of the verified site element or process. Do not prefer a filename or copy a fixed score vector.

The script calculates the remaining 15% diversity score:

`max(0, 100 − 20 × source_articles − 5 × product_articles − 20 × used_in_latest_article)`.

A source match is the original URL, SHA-256, or perceptual-hash distance ≤6; a product match uses
the product detail URL. Multiple placements in one article count once. A new crop/background does
not reset history. Different views of one product incur the product penalty, not an automatic
source match. Missing source evidence is disclosed, not treated as proof of no reuse.

`image_selection.py plan` considers candidates within five relevance points of the best eligible
candidate for each slot, maximizes total weighted score across all slots, and subtracts 18 points
for the one-source exception. Normal assignments require distinct sources. Primary-topic product
visuals, when available, must fill the thumbnail and at least one body slot. Never substitute an
unrelated product to increase variety. If no assignment is possible, expand the reviewed sources
or revise section roles; do not falsify scores or exemptions.

## Metadata contract

Add these fields to `image-references.json` alongside the identity records in `content-spec.md`:

```json
{
  "topic_product_visuals": true,
  "no_topic_product_visual_reason": "",
  "selection_context": {
    "policy": "fresh-gallery-history-v2",
    "run_id": "RUN_ID",
    "product_discovery_file": "product-discovery.json",
    "product_discovery_sha256": "ACTUAL_SHA256",
    "image_history_file": "image-history.json",
    "live_archive_review": {
      "run_id": "RUN_ID",
      "url": "https://www.example.com/news/",
      "evidence_file": "evidence/archive.html",
      "coverage_note": "Describe the observed recent articles and any missing source history."
    },
    "gallery_reviews": [{
      "page_url": "https://www.example.com/product.html",
      "run_id": "RUN_ID",
      "evidence_file": "evidence/product.html",
      "inspection_complete": true,
      "gallery_image_urls": ["https://www.example.com/product-front.webp"],
      "images": [{
        "reference_url": "https://www.example.com/product-front.webp",
        "decision": "candidate",
        "candidate_id": "product-front",
        "eligible_for_product_lock": true,
        "topic_relation": "primary-topic",
        "reason": "Explain this image's inspected topic fit, identity and usability."
      }]
    }]
  }
}
```

Each candidate additionally needs `source_page_url`, `topic_relation`, `relevance_reason`, and,
for product images, `product_url` equal to the current discovered product page. Gallery inventories
must equal the corresponding match's `gallery_image_urls`; every URL needs one disposition.
A `duplicate` disposition needs `duplicate_of` plus its measured `source_sha256` and/or
`perceptual_hash`, with the same eligibility and topic relation as its retained representative.
Keep eligible primary-topic views represented in the shortlist.

Initialize `selection_plan.slots` in thumbnail/body upload order with a unique `article_role` and
`section_topic`. Add `selection_plan.candidate_slot_scores`: one entry for every candidate/slot,
including ineligible pairs, with this shape:

```json
{
  "slot": "thumbnail",
  "candidate_id": "product-front",
  "eligible": true,
  "eligibility_reason": "Explain why this verified product represents the article's main topic.",
  "scores": {
    "keyword_product_relevance": 95,
    "identity_clarity": 98,
    "image_quality": 90,
    "section_fit": 95
  },
  "score_evidence": {
    "keyword_product_relevance": "Describe the actual product and keyword relationship.",
    "identity_clarity": "Describe readable identity details observed in the source.",
    "image_quality": "Describe resolution, focus and completeness of the source.",
    "section_fit": "Describe what this image explains in this particular placement."
  }
}
```

Run before generation:

```bash
python scripts/image_selection.py plan --site-host www.example.com \
  --image-reference-file ROW_RUN_DIR/image-references.json
```

The command updates selection metadata in place, adding computed diversity/history usage, scores,
assignments, `policy`, `objective_score`, and `duplicate_penalty`. Generate images and populate
thumbnail/body identity records from these assignments afterward. If it uses the single-source
exception, supply the required `duplicate_exception` explanation and mitigation before validation.
After any source, score, slot, or history change, recompute the plan and reconcile the image records.

`validate_article.py` independently recomputes this plan and verifies gallery coverage, evidence
paths/digests, history freshness, the full score matrix, and chosen assignments. Old metadata without
these fields fails validation. This checks the recorded evidence and arithmetic; the agent must
still inspect images and judge relevance honestly. Preserve the existing product identity checks
and documented minor-difference acceptance rules.
