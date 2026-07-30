# SEO/GEO article content specification

## Intent and evidence

- Write for Google Search, Google AI Overviews, AI Mode, Bing, Copilot, and overseas B2B buyers.
- Use the core keyword, target country, target customer, related product URL, and researched site
  facts. Choose exactly one `search_intent`: `product-education`, `feature-application`,
  `comparison`, `supplier-manufacturer-discovery`, `oem-odm`, `specifications`,
  `problem-solving`, `purchasing-advice`, or `quotation-customization`.
- Use target country and target customer as silent audience context for research and body content,
  never as automatic title text.
- Separate confirmed site facts, general industry knowledge, and information that must be confirmed.
- Never invent specifications, certifications, test results, prices, MOQ, lead times, rankings,
  sales, reviews, cases, research, or expert claims.

## Search-intent analysis and research

Treat the exact core keyword as the primary evidence of search purpose. Use target country, target
customer, and the related product page only to resolve ambiguity and select relevant examples; do
not let those fields turn one keyword into multiple article purposes.

Use these signals:

| Keyword signal | Primary intent |
| --- | --- |
| what, meaning, guide, how it works, industry basics | `product-education` |
| feature, benefit, use, application, suitable for | `feature-application` |
| vs, compare, difference, alternative, material choice | `comparison` |
| supplier, manufacturer, factory, company, wholesale source | `supplier-manufacturer-discovery` |
| OEM, ODM, private label, custom formula, contract manufacturing | `oem-odm` |
| specification, size, grade, material, parameter, tolerance | `specifications` |
| problem, failure, troubleshooting, how to choose or use correctly | `problem-solving` |
| buy, source, cost factors, procurement, selection checklist | `purchasing-advice` |
| quote, quotation, RFQ, custom request, sample request | `quotation-customization` |

When signals overlap, choose the intent that best matches the dominant wording of the core keyword,
then confirm it against the related product page. Record why plausible alternatives were rejected.
Keep every H2, table, FAQ, image, and ending relevant to the selected intent.

Search two to six related queries before drafting. Use at least two current sources, including one
same-site product/service source and one credible external source when available. Prefer official
standards, regulators, industry associations, research institutions, and primary technical
documentation. Record access dates and whether each source is current, stable background, or tied
to a current standard/version. Use external sources as background evidence recorded in the
manifest; do not add external links to `content.html`, whose links must remain same-site. Do not copy
competitor wording, examples, tables, or outline.

Save `intent-analysis.json`:

```json
{
  "core_keyword": "thermal paper roll specifications",
  "primary_intent": "specifications",
  "keyword_signals": ["specifications", "roll"],
  "intent_rationale": "The query asks for measurable roll requirements rather than a supplier list or quotation.",
  "rejected_intents": ["supplier-manufacturer-discovery", "quotation-customization"],
  "related_queries": [
    "thermal paper roll width core diameter tolerance",
    "thermal paper roll storage standard"
  ],
  "external_source_reason": "",
  "research_sources": [
    {
      "url": "https://www.example.com/product/thermal-roll/",
      "title": "Thermal Roll Product Page",
      "source_role": "site-product",
      "accessed_at": "YYYY-MM-DD",
      "freshness_note": "Current same-site product specifications"
    },
    {
      "url": "https://www.iso.org/example-standard.html",
      "title": "Relevant Technical Standard",
      "source_role": "standard-regulation",
      "accessed_at": "YYYY-MM-DD",
      "freshness_note": "Current edition checked for stable technical context"
    }
  ]
}
```

Allowed source roles are `site-product`, `site-service`, `industry-context`,
`standard-regulation`, and `application-context`. If no credible external source exists, keep the
same-site evidence and explain the search limitation in `external_source_reason`. Replace every
`YYYY-MM-DD` placeholder with the actual access date.

For originality:

- synthesize source facts into a new decision framework, explanation, comparison, or checklist;
- vary the lead, H2 architecture, section order, table dimensions, examples, FAQ, and ending;
- do not reuse generic sections merely to reach the character target;
- do not combine unrelated intents or repeat the same idea under different headings;
- treat recent sources as freshness evidence, not as text to paraphrase line by line.

## Required fields

- `title` is the page H1 and must equal `seo_title1`.
- Use natural professional English, include the exact core keyword naturally, use Title Case, and
  stay within 100 English characters. Prefer 80 or fewer for WUZHICMS compatibility.
- Do not put the `目标国家` or `目标客户` value—or a translation, country adjective/demonym, country
  code, region label, customer segment, buyer role, or close paraphrase—into `title` or
  `seo_title1`. Reject templates such as `<keyword> for <customer>`,
  `<keyword> in <country>`, and `<keyword> for <customer> in <country>`.
- Treat an audience term already embedded in the exact core keyword as the only exception. Keep the
  exact keyword, but do not append another geographic or customer modifier.
- `remark` must equal `seo_desc`.
- Select `remark`/`seo_desc` as one complete sentence from the lead paragraph. Include the exact
  core keyword naturally and stay within 200 English characters.
- Write all user-facing article content in English. Use Chinese only for process and validation
  reports.

## Title diversity

Base the title on researched product evidence and search intent, not on spreadsheet audience fields.
Select exactly one angle:

- `product-education`
- `feature-analysis`
- `application`
- `comparison`
- `selection`
- `specification`
- `process`
- `problem-solution`
- `quality-control`
- `customization`
- `troubleshooting`

Select exactly one pattern:

- `direct-statement`
- `question`
- `how-to`
- `comparison`
- `numbered-list`
- `decision-guide`
- `technical-explainer`
- `risk-led`
- `benefit-led`

Use the least-used available angles and patterns in the current run. Rotate through every value in
each set once before starting another cycle; never repeat an angle or pattern on consecutive
current-run titles, and never reuse the same angle-pattern pair within one run. Rotate openings,
syntax, and value propositions; do not repeatedly start with “How to Choose,” “Ultimate Guide,”
“Best,” “Top,” or “Complete Guide.” Country/customer substitution does not count as diversity.

Before validation, create `title-history.json` containing accepted titles from earlier tabs in the
run and up to 20 recent titles from the current site when available. Exclude the current draft.
Use this shape:

```json
[
  {
    "title": "How Material Grade Changes Product Performance",
    "keyword": "material grade",
    "angle": "feature-analysis",
    "pattern": "technical-explainer",
    "source": "current-run",
    "tab": "www.example.com"
  },
  {
    "title": "Existing Article Title",
    "keyword": "",
    "angle": "",
    "pattern": "",
    "source": "site-recent",
    "tab": "www.example.com"
  }
]
```

Reject an exact duplicate, an unbalanced or consecutive angle/pattern reuse, a repeated
angle-pattern pair, a normalized title-template similarity of 0.82 or higher, or non-keyword
content-word overlap of 0.75 or higher with at least three shared words. Rewrite the title around a
different researched angle instead of swapping only the country, customer, adjective, or year.

## HTML structure

Use this order:

1. Copy the complete scoped `<style data-article-style="responsive-v1">` block from
   `assets/article-content-style.html`.
2. Open one `<article class="article-content">` wrapper.
3. Add one lead `<p>` that directly answers the primary question.
4. Add four to eight H2 sections, with H3 only beneath an H2.
5. Add one FAQ H2 with four to six non-duplicative questions and self-contained answers.
6. Apply the intent-driven ending rules below, then close `</article>`.

Do not include an H1 in `content.html`; the WUZHICMS page template renders `title` as H1.
Do not generate a table of contents, anchor directory, or `<nav class="article-toc">`.

- Begin each section with a direct answer, then explain conditions, use cases, and limitations.
- Keep heading, paragraph, list, figure, and table spacing natural; do not stack elements without
  readable vertical separation.
- Include at least one useful comparison, specification, or procurement table. Wrap every table in
  `<div class="article-table-wrap" role="region" aria-label="Descriptive table name" tabindex="0">`.
  Keep the wrapper around the table only; do not put unrelated paragraphs inside it.
- Use ordered lists for processes and unordered lists for checks or requirements.
- Heading `id` attributes are optional. If used, make them unique lowercase English words joined
  by hyphens.
- Do not add breadcrumbs, author/date/read-count/rating blocks, hidden text, hidden links, or
  manipulative AI instructions.

## Intent-driven ending

Choose and record exactly one `ending_mode`:

| Search intent | Allowed ending modes | Default |
| --- | --- | --- |
| `product-education`, `feature-application`, `comparison`, `specifications`, `problem-solving` | `informational-close`, `inline-cta` | `informational-close` |
| `supplier-manufacturer-discovery`, `oem-odm`, `purchasing-advice`, `quotation-customization` | `inline-cta`, `standalone-cta` | `inline-cta` |

- `informational-close`: End with a useful synthesis, limitation, decision criterion, or next
  technical step. Do not add a CTA marker or force a contact link.
- `inline-cta`: Add one short, article-specific final paragraph marked exactly
  `<p data-article-cta="inline">...</p>`. Integrate it after the final useful content; do not create
  a CTA-only H2.
- `standalone-cta`: Use only for a commercial intent when the ending adds substantive RFQ,
  specification, sample, testing, packaging, or quotation guidance. Wrap it exactly in
  `<section data-article-cta="standalone">...</section>`. Do not use it merely to repeat a contact
  link.

Prefer the default mode. A contact link is optional for informational intent and expected only when
it directly advances the commercial task. Base every CTA on services confirmed on the site.

Do not:

- add the same bottom section to every article;
- use generic headings such as “Build A Comparable RFQ,” “Request A Comparable Proposal,” “Contact
  Us,” or “Get A Quote” without topic-specific decision value;
- use formulas such as “Buyers ready to…,” “Ready to turn…,” “A strong supplier conversation ends
  with…,” or “use the site’s contact channel”;
- repeat the target country or target customer to label the reader;
- pad the CTA with a generic list that is not specific to the article.

Keep an inline CTA to 12–90 English words and a standalone CTA to 25–140. When no CTA is justified,
use `informational-close`; omission is correct, not a missing section.

## Embedded responsive presentation

- Copy the entire style asset into `content.html`; the API stores this CSS with the `content` field.
- Keep every selector scoped beneath `.article-content`, except the `.article-content` root itself
  and its media queries. Never style `body`, `html`, the site header, or generic page elements.
- Preserve the responsive table container, `max-width: 100%` images, automatic image height,
  readable line height, mobile font sizing, and both `@media` breakpoints.
- Use a fixed `px` value for every `font-size` declaration, including headings, captions, body
  copy, and mobile overrides. Do not use `rem`, `em`, `%`, `vw`, `vh`, or `clamp()` for text
  sizing; each host site may define root typography differently.
- Replace every CSS custom-property color near the top with the current site's validated palette.
  Do not retain the asset's example palette for an unrelated site and do not copy a palette from a
  previously processed tab.
- Use `<figure>[IMAGE_BASE64]<figcaption>...</figcaption></figure>` for every body image. The server
  replaces the placeholder with a responsive `<img>` tag.
- Do not add fixed content widths, fixed image heights, viewport-wide offsets, absolute positioning,
  or other rules that can overflow on phones.

## Site theme color system

Build a separate theme palette for every site before drafting `content.html`.

1. Inspect the rendered homepage and related product page. Prefer computed styles from stable
   visible elements such as the header/navigation, primary button, links, headings, normal body
   copy, borders, and page surface. A loaded same-site stylesheet is acceptable. Use a logo color
   only when the rendered UI exposes no usable primary accent, and record that fallback.
2. Record at least one `primary-accent` observation and one `body-text` observation. Normalize
   `rgb()`, `rgba()`, three-digit hex, or other CSS color forms to uppercase six-digit hex.
3. Use the confirmed primary accent for links and as the source hue for headings and table
   accents. Use the confirmed body-text color for article and table body copy. Derive darker
   variants, borders, and subtle tints only when needed for contrast or table readability.
4. Require a contrast ratio of at least 4.5:1 for body text against the article surface, muted text
   against the article surface, links and headings against the article surface, table-header text
   against the table header, and table body text against striped and hover rows.
5. Apply all of these variables; font and table color styling must not contain unrelated hard-coded
   colors:

   - `--article-accent`
   - `--article-accent-dark`
   - `--article-text`
   - `--article-muted`
   - `--article-border`
   - `--article-soft`
   - `--article-surface`
   - `--article-table-header`
   - `--article-table-header-text`
   - `--article-table-stripe`
   - `--article-table-hover`

Save `<row-run-dir>/theme-colors.json`:

```json
{
  "site_host": "www.example.com",
  "source_urls": [
    "https://www.example.com/",
    "https://www.example.com/product/"
  ],
  "evidence": [
    {
      "url": "https://www.example.com/",
      "evidence_type": "computed-style",
      "selector_or_element": "primary header button",
      "css_property": "background-color",
      "color": "#176B5B",
      "role": "primary-accent"
    },
    {
      "url": "https://www.example.com/product/",
      "evidence_type": "computed-style",
      "selector_or_element": "product description paragraph",
      "css_property": "color",
      "color": "#263238",
      "role": "body-text"
    }
  ],
  "colors": {
    "--article-accent": "#176B5B",
    "--article-accent-dark": "#0F4F44",
    "--article-text": "#263238",
    "--article-muted": "#52646C",
    "--article-border": "#DCE6E3",
    "--article-soft": "#F4F8F7",
    "--article-surface": "#FFFFFF",
    "--article-table-header": "#176B5B",
    "--article-table-header-text": "#FFFFFF",
    "--article-table-stripe": "#F4F8F7",
    "--article-table-hover": "#E8F2EF"
  },
  "derivation_notes": "Dark and tint variants preserve the observed site hue while meeting contrast requirements."
}
```

Allowed `evidence_type` values are `computed-style`, `stylesheet`, and `logo`. Allowed roles are
`primary-accent`, `secondary-accent`, `body-text`, `muted-text`, `border`, and `surface`. Every
evidence URL must be same-site HTTPS. `--article-accent`, `--article-accent-dark`, and
`--article-table-header` must equal an observed `primary-accent` or be an accessible lighter/darker
shade that preserves its hue; `--article-text` must equal an observed `body-text`. If any applied
color is not directly observed, explain its relationship to the observed palette in
`derivation_notes`. Do not select colors from a product label, third-party widget, advertisement,
photograph, or competitor site.

## Lead and internal links

- Place the core keyword naturally near the beginning of the lead.
- Link the first occurrence of the core keyword to a real, relevant page on the same site.
- Use only verified same-site HTTPS links. Never invent a URL or substitute a competitor.
- Add one or two relevant internal links per 2,000 visible English characters: normally 3–5 links
  for a 5,000-character article and 5–10 for a 10,000-character article.
- Use descriptive, non-repeated anchor text; do not use “Click Here” or “Read More”.

## Length and GEO quality

- Keep final visible English content between 5,000 and 10,000 characters, including spaces and
  punctuation in headings, paragraphs, lists, tables, FAQ, and any CTA that is present.
- Exclude HTML tags, anchors, image paths, SEO fields, and page chrome from the count.
- Prefer independently understandable answers, complete product/material names, explicit
  comparison conditions, and consistent facts. Do not pad or mechanically repeat keywords.

## Images

- Create every final image from visual references taken from the same site and record the exact
  reference page and image URLs in the manifest.
- Build and deduplicate a global candidate pool before assigning the thumbnail or any body slot.
  Prefer 3–8 retained candidates for the article: exact-product views from the product gallery or
  category plus section-relevant same-site factory, laboratory, application, production,
  packaging, warehouse, or service scenes. Candidate shortage is allowed only with a concrete
  `candidate_pool_limit_reason`. Do not introduce a different SKU, variant, product family, or
  brand merely to satisfy the preferred pool size.
- Run `scripts/analyze_image_pool.py` on the downloaded candidates. Treat identical SHA-256 hashes
  as exact duplicates and perceptual-hash Hamming distance 6 or less as near-duplicates. Consolidate
  each duplicate cluster to its clearest, highest-resolution, most article-relevant representative
  before selection.
- Record for every retained candidate: ID, classification, same-site URL, local file, SHA-256,
  64-bit perceptual hash, dimensions, view angle, scene type, label legibility, article relevance,
  product-lock eligibility, and an identity summary. Product-lock eligibility is `true` only for a
  real, sufficiently clear product source that can support the required mask and identity checks.
- Plan all slots at once with `weighted-global-assignment-with-duplicate-penalty`; do not select
  images greedily one slot at a time. Score each candidate from 0–100 for the intended slot and
  calculate `weighted_total` as 30% keyword/product relevance, 25% identity clarity, 15% image
  quality, 15% section fit, and 15% diversity. A high score is not permission to change product
  identity or use an unrelated image.
- Give every slot a distinct article role. Use `product-hero` for the thumbnail when a valid
  product source exists; body roles may be `product-detail`, `inspection-comparison`,
  `factory-production`, `laboratory-quality`, `application-use`, `packaging-logistics`, or
  `warehouse-supply`, selected only when they fit the surrounding section. The image placement and
  alt text must express that role.
- Use a retained source candidate no more than once per article. The only exception is when the
  deduplicated pool contains exactly one eligible product candidate: it may be used in at most two
  slots, `selection_plan.duplicate_exception` must document the affected slots and mitigation, and
  the resulting images must differ in article role, section purpose, composition, scale, and
  regenerated scene. Fill other slots with relevant same-site non-product candidates. Product
  truth takes priority over source diversity.
- Classify each planned image as `product-present` or `non-product` before generation.
- For every `product-present` image, download and inspect one to three original product images from
  the related product/category pages. Prefer the highest-resolution front or three-quarter view
  that makes the actual brand, label, packaging, and product form verifiable.
- Before generation, transcribe an identity inventory from those references: every visible brand
  or logo word, the product/variant name and other legible label text, package colors/materials,
  container geometry, closure, proportions, and visible product form. Copy visible text exactly,
  including case and spelling. Do not translate, correct, abbreviate, or infer obscured text.
- Use the original product image as the identity source for whole-image regeneration, not as
  style-only inspiration or a layer for later compositing. Every final `product-present` image must
  be regenerated for the current article placement. The only allowed preservation method is
  `source-product-locked-regeneration`; `source-product-composite`,
  `source-product-locked-edit`, `unaltered-source-image`, plain `contain` padding, a solid/blurred
  border, or a renamed/re-encoded copy is not a compliant regenerated product image.
- Create and manually inspect a product mask that covers the complete product, packaging, visible
  product material, accessories that define the source presentation, edge reflections, and
  readable label area. Run `scripts/prepare_locked_product.py` with the source and inspected mask
  to create a transparent locked-product PNG and JSON extraction report. The script may change
  alpha only; it must not synthesize, repaint, crop, recolor, sharpen, or relabel product pixels.
- Supply the extracted locked product as a required image input and regenerate the complete 16:9 or
  3:2 final canvas in one cohesive generation pass. Generate the scene, composition, supporting
  surface, props, ambient lighting, depth, and natural contact shadow together around the product.
  Do not first generate a product-free background, do not use deterministic layer compositing as
  the final construction method, and do not treat the original product as optional inspiration.
- Call image generation through the referenced-image edit path with both
  `locked_product_file` and `lock_mask_file` in `referenced_image_paths`, and omit
  `num_last_images_to_include`. Do not perform a text-only generation and do not substitute a
  recently generated image for either required local lock input.
- Treat the locked product as a non-editable identity object. Whole-object proportional scaling and
  translation are allowed when needed for composition, but the model must not alter the product
  interior, outline, front-facing label, packaging, accessories, or visible product form. Save the
  raw whole-image generation before WebP encoding. If the model changes the locked object, discard
  the result; a prompt instruction is not proof of preservation.
- Preserve the exact logo, brand name, label text, typography, label layout, package colors,
  material, reflections, container/roll shape, closure, proportions, and visible product form.
  Do not remove, rewrite, approximate, hallucinate, blur, hide, turn away, crop, or replace them.
  A visually similar blank or generic package is a failed output.
- If a regenerated image changes even one visible brand letter, label word, packaging color, or
  product-shape detail, retry whole-image regeneration with the extracted product and inspected
  lock mask. If exact identity still cannot be retained, fail the image and row. Do not fall back
  to deterministic compositing, a background-only edit, the unchanged source, or a `contain`-only
  canvas. Never trade product identity for a more cinematic scene.
- For `non-product` images, use same-site factory, laboratory, application, production, warehouse,
  or service images as references whenever the site provides them. Use generic visual knowledge only
  when no relevant same-site visual exists.
- Generate one 16:9 thumbnail and body images in 3:2 format.
- Use 2 body images for 5,000–6,499 visible characters, 3 for 6,500–8,499, and 4 for
  8,500–10,000.
- Place repeated `[IMAGE_BASE64]` tokens at relevant locations in `content.html`, one per body
  image and in the same order as the upload list.
- Provide a distinct, accurate English alt text for each body image. Describe visible content and
  purpose; use the core or related keyword only when natural.
- Inspect every generated image at full size. Reject and regenerate a `product-present` image when
  any product detail is missing or changed, any brand/label character differs, or the source product
  is replaced by generic packaging. Reject invented certifications, performance claims, contact
  details, third-party branding, or a misleading factory/product context.
- Load the source reference, extracted locked product, raw whole-image generation, and final WebP
  with `view_image` (or an equivalent original-detail viewer), and compare all four side by side at
  100% zoom. Do not infer fidelity from the prompt or the model response. Mark `brand_text`,
  `label_text`, `packaging`, and `product_geometry` independently. Use
  `not-visible-in-reference` only when that element truly is absent or unreadable in the selected
  source; never create absence by choosing a blurrier reference, cropping the label, or hiding the
  package in the output.
- When the site has visibly branded or legibly labelled product images, the thumbnail and at least
  one body image must retain those elements clearly enough to compare. Optimizing or fitting an
  already regenerated image must not crop them. `scripts/optimize_image.py --fit contain` may be
  used only as a final anti-clipping safeguard and never as the regeneration method.
- Record for each output: classification, local reference files, source URLs, preservation method,
  lock-mask and extracted-product files, raw whole-image generation, exact source identity,
  retained site-product elements, identity checks, four-way visual inspection evidence, output
  WebP file, and inspection result. Convert all final assets to compressed WebP before upload.
- Compute perceptual hashes for all final WebP outputs. Every pair must be at least 10 bits apart.
  If the single-product-source exception is used, the two outputs derived from that source must be
  at least 12 bits apart. A palette shift, crop, flipped canvas, or background-only variation does
  not count as meaningful diversity.

Use this product-preserving prompt structure for every `product-present` edit:

```text
Use case: locked-product-whole-image-regeneration
Asset type: B2B article thumbnail or body image
Input image 1: extracted and locked original site product; mandatory identity object
Input image 2: inspected product lock mask
Primary request: regenerate the complete final image in one cohesive pass around the locked product
Text (verbatim): "<exact brand and label text from the identity inventory>"
Product invariants: preserve the complete source product as a locked region, including logo, every
visible letter, label layout, package color/material, container geometry, closure, proportions,
reflections, and visible product form; do not synthesize or repaint any product-region pixels
Whole-image freedom: regenerate the background, surface, props, ambient lighting, depth, natural
contact shadow, and overall composition as one integrated scene
Constraints: keep the branded front label clear and readable; allow only whole-object proportional
scaling or translation; preserve product edges and all locked identity details
Avoid: separate empty-background generation, deterministic product compositing, background-only
editing, redrawing, retyping, relabelling, generic packaging, invented claims, blur, obstruction,
rotation, crop, third-party branding, watermark
```

Use the extracted product as a mandatory protected input while regenerating the whole image. Do not
ask the model to recreate the branded product from text, and do not build the final image by
separately generating a background and pasting the product onto it. Save the source, mask, extracted
locked product, prompt, raw whole-image generation, and final WebP for validation.
- Save those records as `image-references.json` with this shape and pass it to the article validator:

```json
{
  "site_has_product_visuals": true,
  "site_has_branded_product_visuals": true,
  "site_has_legible_product_labels": true,
  "no_product_visual_reason": "",
  "no_branded_product_visual_reason": "",
  "no_legible_product_label_reason": "",
  "candidate_pool": [
    {
      "candidate_id": "product-01",
      "classification": "product-present",
      "reference_url": "https://www.example.com/path/product.webp",
      "reference_file": "/absolute/run/path/source/product.webp",
      "source_sha256": "64-lowercase-hex-characters",
      "perceptual_hash": "16HEXCHARACTERS",
      "width": 1600,
      "height": 1600,
      "view_angle": "front",
      "scene_type": "product-hero",
      "label_legibility": "clear",
      "article_relevance": "exact-product",
      "eligible_for_product_lock": true,
      "identity_summary": "EXAMPLE Product Name, matte white pouch with blue top band"
    },
    {
      "candidate_id": "product-02",
      "classification": "product-present",
      "reference_url": "https://www.example.com/path/product-detail.webp",
      "reference_file": "/absolute/run/path/source/product-detail.webp",
      "source_sha256": "64-lowercase-hex-characters",
      "perceptual_hash": "16HEXCHARACTERS",
      "width": 1600,
      "height": 1600,
      "view_angle": "three-quarter",
      "scene_type": "product-detail",
      "label_legibility": "clear",
      "article_relevance": "exact-product",
      "eligible_for_product_lock": true,
      "identity_summary": "Same EXAMPLE Product Name pouch in a distinct three-quarter view"
    },
    {
      "candidate_id": "factory-01",
      "classification": "non-product",
      "reference_url": "https://www.example.com/path/factory.webp",
      "reference_file": "/absolute/run/path/source/factory.webp",
      "source_sha256": "64-lowercase-hex-characters",
      "perceptual_hash": "16HEXCHARACTERS",
      "width": 1800,
      "height": 1200,
      "view_angle": "environmental",
      "scene_type": "factory-production",
      "label_legibility": "not-applicable",
      "article_relevance": "supporting-site-scene",
      "eligible_for_product_lock": false,
      "identity_summary": "Same-site production line shown on the factory page"
    }
  ],
  "candidate_pool_limit_reason": "",
  "selection_plan": {
    "global_selection_method": "weighted-global-assignment-with-duplicate-penalty",
    "duplicate_exception": null,
    "slots": [
      {
        "slot": "thumbnail",
        "candidate_id": "product-01",
        "article_role": "product-hero",
        "section_topic": "Article thumbnail",
        "selection_reason": "Exact product with the clearest verifiable front label",
        "scores": {
          "keyword_product_relevance": 95,
          "identity_clarity": 98,
          "image_quality": 90,
          "section_fit": 95,
          "diversity": 100,
          "weighted_total": 95.8
        }
      }
    ]
  },
  "thumbnail": {
    "candidate_id": "product-01",
    "classification": "product-present",
    "reference_urls": ["https://www.example.com/path/product.webp"],
    "reference_files": ["/absolute/run/path/source/product.webp"],
    "preservation_method": "source-product-locked-regeneration",
    "adaptation": {
      "new_image_generated": true,
      "adaptation_method": "locked-product-whole-image-regeneration",
      "locked_product_file": "/absolute/run/path/locked/thumb-product.png",
      "lock_mask_file": "/absolute/run/path/locked/thumb-mask.png",
      "lock_report_file": "/absolute/run/path/locked/thumb-product.json",
      "generated_asset_files": [
        "/absolute/run/path/generated/thumb-whole-image.png"
      ],
      "prompt_file": "/absolute/run/path/prompts/thumb.txt",
      "source_product_locked": true,
      "whole_image_regenerated": true,
      "deterministic_composite_used": false,
      "source_canvas_reused_as_final": false,
      "scene_description": "Clean ingredient-evaluation workspace with neutral daylight"
    },
    "source_identity": {
      "brand_text": ["EXAMPLE"],
      "label_text": ["Product Name", "Net Wt. 500 g"],
      "packaging_details": ["matte white stand-up pouch", "blue top band", "zip closure"]
    },
    "output_file": "/absolute/run/path/images/thumb.webp",
    "retained_site_elements": ["original EXAMPLE logo", "original front label", "original pouch"],
    "identity_checks": {
      "brand_text": "pass",
      "label_text": "pass",
      "packaging": "pass",
      "product_geometry": "pass"
    },
    "visual_inspection": {
      "comparison_mode": "side-by-side-100-percent",
      "source_vs_locked_product": "pass",
      "locked_product_vs_generated": "pass",
      "source_vs_final_webp": "pass"
    },
    "inspection_result": "pass"
  },
  "body": [
    {
      "candidate_id": "product-02",
      "classification": "product-present",
      "reference_urls": ["https://www.example.com/path/product-detail.webp"],
      "reference_files": ["/absolute/run/path/source/product-detail.webp"],
      "preservation_method": "source-product-locked-regeneration",
      "adaptation": {
        "new_image_generated": true,
        "adaptation_method": "locked-product-whole-image-regeneration",
        "locked_product_file": "/absolute/run/path/locked/body-01-product.png",
        "lock_mask_file": "/absolute/run/path/locked/body-01-mask.png",
        "lock_report_file": "/absolute/run/path/locked/body-01-product.json",
        "generated_asset_files": [
          "/absolute/run/path/generated/body-01-whole-image.png"
        ],
        "prompt_file": "/absolute/run/path/prompts/body-01.txt",
        "source_product_locked": true,
        "whole_image_regenerated": true,
        "deterministic_composite_used": false,
        "source_canvas_reused_as_final": false,
        "scene_description": "Ingredient verification bench with the source product unobstructed"
      },
      "source_identity": {
        "brand_text": ["EXAMPLE"],
        "label_text": ["Product Name", "Net Wt. 500 g"],
        "packaging_details": ["matte white stand-up pouch", "blue top band", "zip closure"]
      },
      "output_file": "/absolute/run/path/images/body-01.webp",
      "retained_site_elements": ["original EXAMPLE logo", "original front label", "original pouch"],
      "identity_checks": {
        "brand_text": "pass",
        "label_text": "pass",
        "packaging": "pass",
        "product_geometry": "pass"
      },
      "visual_inspection": {
        "comparison_mode": "side-by-side-100-percent",
        "source_vs_locked_product": "pass",
        "locked_product_vs_generated": "pass",
        "source_vs_final_webp": "pass"
      },
      "inspection_result": "pass"
    }
  ]
}
```

The `body` array must match placeholder/upload order. When product visuals exist, the thumbnail and
at least one body image must be `product-present`. Set `site_has_branded_product_visuals` and
`site_has_legible_product_labels` from the inspected site references. When either is true, both the
thumbnail and at least one body record must contain the exact corresponding source-identity text and
a passing check. When a capability is false, give a concrete corresponding reason. When no product
visual exists, set all three booleans to `false` and give `no_product_visual_reason`.

The example abbreviates `selection_plan.slots`; the real file must contain exactly one slot in
upload order for `thumbnail`, `body-01`, `body-02`, and so on, and each slot must match the
corresponding record's `candidate_id`, classification, reference URL, and reference file. Article
roles must be unique. If the only eligible product candidate is intentionally reused, set
`duplicate_exception` to an object containing its `candidate_id`, the two `slots`,
`valid_product_candidates: 1`, a concrete `reason`, and a concrete `mitigation`; otherwise keep it
`null`.

## Final checks

Require exact field equality, valid heading hierarchy, no generated TOC, one scoped responsive style
block, one `.article-content` wrapper, fixed pixel-based font sizes, responsive table wrappers,
same-site theme evidence, exact palette-to-CSS equality, accessible site-themed font and table
colors, natural spacing, the configured visible-character range, verified internal links, the
correct placeholder/image count, distinct alt text, four to six FAQs, inspected same-site visual
references, a deduplicated global image pool, unique source assignment and article roles,
perceptually distinct final images, no target-country/customer title modifiers, a unique
title angle-pattern pair,
sufficient title diversity, one keyword-led search intent, current documented research, a varied
evidence-led outline, an intent-appropriate non-boilerplate ending, and no unsupported claims.
