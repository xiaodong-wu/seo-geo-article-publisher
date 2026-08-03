# SEO/GEO Article Publisher

A Codex skill for producing and publishing English B2B SEO/GEO articles from a structured Google Sheet.

It combines keyword-led search-intent research, title and outline diversity, site-theme-matched article styling, same-site image selection, product-identity-preserving image regeneration, validation, WUZHICMS publishing, live-page verification, and spreadsheet status updates.

## Highlights

- Processes at most one pending row per configured site tab in a run.
- Selects one primary intent from a seven-type taxonomy, allows at most one subordinate intent,
  and aligns the ending with the buyer's stage.
- Uses an auditable seeded 70/30 question-versus-statement title mode while requiring the exact
  keyword to be integrated naturally instead of used as a colon prefix.
- Targets 12,000–13,500 visible characters and validates a 10,000–15,000-character range.
- Uses neutral third-person buyer guidance, including evidence-led treatment of manufacturer lists.
- Adds length-adjusted, substantive H3 analysis across multiple non-FAQ H2 sections instead of
  limiting H3s to FAQ questions.
- Requires the exact core keyword 3–5 times and 2–4 intent-aligned related keywords with 3–5
  combined occurrences, distributed naturally across the visible article content.
- Prevents target-country and target-customer fields from becoming repetitive title templates.
- Matches article typography and table colors to each site's observed theme.
- Builds and deduplicates a same-site image candidate pool before assigning image slots.
- Requires different source images and article roles unless only one valid product source exists.
- Locks original branding, labels, packaging colors, and product geometry during whole-image regeneration.
- Validates content structure, length, FAQ count, links, theme contrast, image diversity, and product-identity evidence.
- Publishes through a multipart WUZHICMS endpoint, checks body images on the article detail page,
  and verifies the thumbnail asset plus its appearance on the article listing page.
- Keeps publishing keys out of files, command arguments, logs, and reports.

## Repository Layout

```text
.
├── SKILL.md
├── agents/openai.yaml
├── assets/article-content-style.html
├── references/
│   ├── api-contract.md
│   ├── content-spec.md
│   └── publishing.md
├── scripts/
    ├── analyze_image_pool.py
    ├── optimize_image.py
    ├── prepare_locked_product.py
    ├── publish_article.py
    ├── select_title_mode.py
    ├── validate_article.py
    └── verify_article.py
└── tests/
    ├── test_validate_article_h3_depth.py
    ├── test_validate_article_intent.py
    ├── test_validate_article_keywords.py
    ├── test_validate_article_title_mode.py
    └── test_verify_article.py
```

## Installation

Clone the repository into your Codex skills directory:

```bash
git clone https://github.com/xiaodong-wu/seo-geo-article-publisher.git \
  ~/.codex/skills/seo-geo-article-publisher
```

The scripts require Python 3 with `Pillow` and `requests`. The live workflow also requires access to the configured Google Sheet, image generation, and the target site's publishing endpoint.

Before using the skill in another environment, replace the configured spreadsheet ID and confirm that the sheet headers and publishing API follow the contracts in `references/`.

## Usage

Invoke the skill explicitly:

```text
$seo-geo-article-publisher run once
```

Use a dry run when you want research, generation, and validation without claiming rows, publishing, or updating the sheet:

```text
$seo-geo-article-publisher dry-run
```

## Security

Never commit publishing keys or generated run directories. The publishing helper reads a key from a hidden prompt or a pre-existing environment variable and sends it only in the HTTPS authorization header.

## Validation

The repository's Python helpers can be syntax-checked with:

```bash
python3 -m py_compile scripts/*.py
python3 -m unittest discover -s tests
```

`validate_article.py` is the final local gate and should pass before any publishing API call.
