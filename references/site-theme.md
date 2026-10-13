# Match the site's color roles

Read this before building article CSS. Use the current site's own interface, not previous generated
articles, as the source of truth. Do not infer a complete palette from one CTA button.

## Collect and distinguish roles

Inspect the rendered homepage and a relevant product/service page. Record computed colors from
normal content headings, body copy, inline links, the content surface, navigation/active controls,
and recurring brand accents. Inspect a native article template when it helps resolve a role, but
exclude `.article-content` styles inserted by this publisher. Exclude chat widgets, WhatsApp,
photographs, packaging and campaign banners. Record the actual background behind text; transparent
and alpha colors must be composited against that background, not treated as opaque hex colors.

Distinguish the site's main visual identity from secondary action colors. A site can have green
content and orange quotation buttons. Compare repeated component families across both pages;
choose the stable content/brand accent and explain why competing colors are secondary. Corroborate
the exact primary color on two pages in two component families; the same header button on two pages
is one family. Do not average colors. If evidence conflicts, inspect the stylesheet or another
native component before choosing. Logo evidence is a fallback when usable UI evidence is absent;
it alone cannot replace the two corroborating observations.

Select heading, body, link and surface colors independently by role. White hero text over a dark
photo is not a heading color for a white article. A product-card title is not body copy. Prefer a
normal paragraph on the product/service page; record a concrete fallback when that page has no
prose. A dark native heading or underlined body-colored link is valid even on an orange-brand site.

## Evidence and deterministic palette

Save `theme-evidence.json` with this schema (example values only; never copy across sites):

```json
{
  "schema_version": 2,
  "site_host": "www.example.com",
  "observed_at": "2026-10-13T10:00:00+08:00",
  "source_urls": ["https://www.example.com/", "https://www.example.com/product/"],
  "evidence": [
    {"id":"brand-home","url":"https://www.example.com/","evidence_type":"computed-style","selector_or_element":"nav .active","css_property":"color","color":"#FF6614","role":"primary-accent","component":"navigation"},
    {"id":"brand-product","url":"https://www.example.com/product/","evidence_type":"computed-style","selector_or_element":".category-control.active","css_property":"background-color","color":"#FF6614","role":"primary-accent","component":"category-filter"},
    {"id":"heading","url":"https://www.example.com/product/","evidence_type":"computed-style","selector_or_element":"main h2","css_property":"color","color":"#222222","role":"heading-text","component":"content-heading"},
    {"id":"body","url":"https://www.example.com/product/","evidence_type":"computed-style","selector_or_element":"main .description p","css_property":"color","color":"#4C4B4B","role":"body-text","component":"description"},
    {"id":"surface","url":"https://www.example.com/product/","evidence_type":"computed-style","selector_or_element":"main","css_property":"background-color","color":"#FFFFFF","role":"surface","component":"content-surface"}
  ],
  "selection": {
    "primary_accent": ["brand-home", "brand-product"],
    "heading": "heading", "body": "body", "surface": "surface",
    "reason": "Repeated navigation and category accents establish orange; normal headings are neutral dark, and absent inline link evidence falls back to underlined body text."
  }
}
```

Use exact selectors plus relevant element text when a selector matches several styles. Evidence
roles: `primary-accent`, `secondary-accent`, `heading-text`, `body-text`, `link-text`, `muted-text`,
`border`, `surface`. Evidence types: `computed-style`, `stylesheet`, `logo`. Optional selections
`link`, `muted`, `border` refer to matching evidence IDs. `table_header_text` can select another
observed heading/body/link/surface color if the other selected colors do not contrast with the
brand fill. Explain omitted roles/fallbacks in
`selection.reason`. All colors are uppercase six-digit hex, all source URLs exact same-host HTTPS.

Run `scripts/build_theme_palette.py --evidence-file theme-evidence.json --output theme-colors.json`.
Use its complete `colors` object to replace the style asset's example variables. Do not hand-edit
the output colors to make the validator pass. Keep `token_sources` for every exact or mixed value.

- `--article-accent` and `--article-table-header` retain the **exact observed brand color**.
  Accent is used for decorative borders and link underlines, not forced onto all text.
- `--article-heading`, `--article-link`, `--article-text` and `--article-muted` use their observed
  roles. If a chosen heading/link/caption color lacks 4.5:1 contrast on the article surface, use a
  readable observed body/heading color. Preserve the brand in the decoration.
- Choose table-header text from observed light/dark colors to reach 4.5:1 against the unchanged
  brand fill. Do not darken orange into brown simply to keep white header text.
- `--article-border`, `--article-soft`, `--article-table-stripe`, `--article-table-hover` use
  observed borders or recorded sRGB mixtures of this site's accent and surface. Do not inherit
  another site's green-gray caption/border defaults. Shadows are neutral.
- `--article-surface` uses the actual light/dark content surface. Test normal text, callout text
  and table text against their applied backgrounds. The builder rejects impossible combinations
  rather than inventing a new brand shade. Collect suitable native evidence if it rejects one.

The previous `--article-accent-dark` and schema v1 are retired for new drafts. Historical run
evidence stays immutable. Recollect and rebuild a pending old draft before submitting it.

## Verify actual rendering

Before publication, render the final scoped CSS and article in a local preview with the current
host's typography/CSS context where possible. Compare headings, links, captions and a table against
the native site. Check desktop (at least 1024px) and mobile (at most 480px). Save screenshots and
`theme-rendered-prepublish.json`; set its `content_sha256` to the final `content.html` bytes' SHA256.
If the draft changes, capture it again. Run `validate_article.py --rendered-theme-file ...` with
the other normal arguments. Color-variable equality alone does not prove that host CSS renders it.

After publication, capture the same computed-style roles on the **actual public article** at both
widths. Run `verify_theme_rendering.py` on `theme-rendered-postpublish.json`. Record the result and
screenshots in the manifest together with the HTTP article/thumbnail/listing checks. Mark the row
published only when both checks pass. For a visual override, do not repost: use the existing
one-recheck/manual-review rule. Recollect browser evidence on recheck; do not rerun stale samples.
Pass the final `content.html` as `--content-file` for both phases; the verifier derives required
element counts from that HTML rather than trusting sample totals. For `postpublish`, also pass
`--article-url` with the exact published article URL from the API/reconciled manifest. The sampled
page's `url` must match it exactly; another page on the same site is insufficient.

Rendered evidence format:

```json
{
  "site_host": "www.example.com", "phase": "prepublish",
  "url": "http://127.0.0.1:8000/preview.html",
  "content_sha256": "SHA256_OF_FINAL_CONTENT_HTML",
  "viewports": [{"width": 1440, "samples": [
    {"role":"body","selector":".article-content","index":0,"property":"color","value":"rgb(76, 75, 75)"}
  ]}, {"width": 390, "samples": []}]
}
```

The shortened example is not passing evidence. Use these **exact** selector strings and properties
for each role; query every selector with `document.querySelectorAll(selector)` in each viewport:

| Role | Canonical selector | Computed property |
| --- | --- | --- |
| `body` | `.article-content` | `color` |
| `body` | `.article-content p` | `color` |
| `body` | `.article-content li` | `color` |
| `surface` | `.article-content` | `background-color` |
| `h2` | `.article-content h2` | `color` |
| `h3` | `.article-content h3` | `color` |
| `link` | `.article-content a` | `color` |
| `caption` | `.article-content figcaption` | `color` |
| `table-header` | `.article-content th` | `background-color` |
| `table-header-text` | `.article-content th` | `color` |
| `table-body` | `.article-content td` | `color` |
| `callout-accent` | `.article-content blockquote` | `border-left-color` |

For every returned element, record its zero-based `index` **within that selector's NodeList** and
the actual `getComputedStyle(element).getPropertyValue(property)`. Record all elements, not only
the first or a representative sample. A selector with zero matches contributes no samples.
Each `(role, selector, index)` must appear exactly once per viewport; missing, duplicate, out-of-range
or noncanonical samples fail. Paragraph/list samples catch host rules that override inherited root
text. Blockquote evidence is mandatory whenever the final HTML contains a blockquote. The verifier
requires exactly one `article.article-content` root and reports its HTML-derived coverage counts.
For `postpublish`, record the exact public article URL. Restore temporary browser viewport settings.

```bash
python scripts/verify_theme_rendering.py --theme-colors-file theme-colors.json \
  --observations-file theme-rendered-postpublish.json --content-file content.html \
  --article-url "https://www.example.com/the-published-article.html" \
  --output theme-rendering-result.json
```
