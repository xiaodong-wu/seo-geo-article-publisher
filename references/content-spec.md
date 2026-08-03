# SEO/GEO article content specification

## Intent and evidence

- Write for Google Search, Google AI Overviews, AI Mode, Bing, Copilot, and overseas B2B buyers.
- Use the core keyword, target country, target customer, related product URL, and researched site
  facts. Choose exactly one primary `search_intent` from the seven-type taxonomy below. Select zero
  or one subordinate `secondary_intent` only when it is necessary to answer the primary purpose.
- Classify exactly one `buyer_stage`: `awareness`, `consideration`, `evaluation`, or `inquiry`.
- Use target country and target customer as silent audience context for research and body content,
  never as automatic title text.
- Separate confirmed site facts, general industry knowledge, and information that must be confirmed.
- Never invent specifications, certifications, test results, prices, MOQ, lead times, rankings,
  sales, reviews, cases, research, or expert claims.
- Use a neutral third-person editorial stance. Do not frame the host site as “we” or “our,” and do
  not privilege its products or capabilities over alternatives without comparable evidence.

## Search-intent analysis and research

Treat the exact core keyword as the primary evidence of search purpose. Use target country, target
customer, and the related product page only to resolve ambiguity and select relevant examples; do
not let those fields turn one keyword into multiple article purposes.

Use these seven article types:

| Search intent | Typical keyword signals | Required emphasis |
| --- | --- | --- |
| `foundational-knowledge` | what, meaning, basics, how it works, technology, process | accurate definition, operating principle, key parameters, common uses, suitable and unsuitable conditions |
| `product-selection` | how to choose, selection, specification, grade, size, tolerance, buying criteria | procurement criteria, parameter meaning, quality verification, common mistakes, information to confirm before inquiry |
| `product-comparison` | vs, compare, difference, alternative, material or solution choice | identical comparison dimensions, advantages and limitations, suitable applications, no deliberate disparagement |
| `oem-odm` | OEM, ODM, private label, custom formula, custom specification, contract manufacturing | customization scope, specification or formula confirmation, samples, packaging, MOQ and lead-time factors, quality documents |
| `supplier-evaluation` | manufacturer, supplier, factory, partner, wholesale source, top manufacturers | production and quality capability, document verification, communication, samples, delivery, after-sales support, cooperation risk |
| `application-scenario` | application, use case, industry, environment, suitable for, target outcome | operating conditions, buyer pain points, fit logic, limitations, implementation and purchasing cautions |
| `problem-solving` | problem, failure, defect, troubleshooting, fix, prevent, use correctly | problem definition, common causes, diagnostic steps, remedies, escalation to a supplier or specialist |

Choose exactly one primary intent. Select a secondary intent only when it is a supporting lens, such
as using one application example inside a foundational explanation or adding supplier-verification
checks to a product-selection article. Do not give the secondary intent its own unrelated outline,
and never select more than two intents in total.

Treat quotation, RFQ, sample, and custom-request words primarily as buyer-stage signals. Determine
the underlying article type from the object of the request: an OEM quotation remains `oem-odm`, a
manufacturer shortlist remains `supplier-evaluation`, and a specification-led purchase remains
`product-selection`.

| Buyer stage | Query evidence | Content and ending behavior |
| --- | --- | --- |
| `awareness` | what, basics, meaning, how it works, early problem discovery | explain first; use an informational close and do not push a quote or sample request |
| `consideration` | options, uses, suitability, comparison, how to choose | clarify tradeoffs and suggest the next relevant check; a soft inline action is optional |
| `evaluation` | specifications, validation, supplier capability, documents, risks | provide verification criteria and evidence requests; a contextual inline action is appropriate |
| `inquiry` | quote, RFQ, sample, custom request, MOQ, lead time | help the buyer submit specifications and requirements; inline or substantive standalone CTA is allowed |

When signals overlap, choose the primary intent that best matches the dominant wording of the core
keyword, then confirm it against the related product page. Record why plausible alternatives were
rejected, why any secondary intent is necessary, and why the buyer stage fits. Keep every H2, table,
FAQ, image, and ending relevant to the primary intent.

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
  "primary_intent": "product-selection",
  "secondary_intent": "",
  "keyword_signals": ["specifications", "roll"],
  "intent_rationale": "The query asks for measurable roll requirements rather than a supplier list or quotation.",
  "secondary_intent_rationale": "",
  "rejected_intents": ["supplier-evaluation", "oem-odm"],
  "buyer_stage": "evaluation",
  "buyer_stage_rationale": "The query focuses on checking parameters before a purchase or supplier decision.",
  "editorial_stance": "neutral-buyer-guidance",
  "related_queries": [
    "thermal paper roll width core diameter tolerance",
    "thermal paper roll storage standard"
  ],
  "related_keywords": [
    "receipt roll dimensions",
    "thermal media storage"
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

Use only these intent-stage combinations:

- `foundational-knowledge`: `awareness` or `consideration`;
- `product-selection`: `consideration`, `evaluation`, or `inquiry`;
- `product-comparison`: `consideration` or `evaluation`;
- `oem-odm`: `consideration`, `evaluation`, or `inquiry`;
- `supplier-evaluation`: `consideration`, `evaluation`, or `inquiry`;
- `application-scenario`: `awareness`, `consideration`, or `evaluation`;
- `problem-solving`: any of the four buyer stages when supported by the query wording.

Allowed source roles are `site-product`, `site-service`, `industry-context`,
`standard-regulation`, and `application-context`. If no credible external source exists, keep the
same-site evidence and explain the search limitation in `external_source_reason`. Replace every
`YYYY-MM-DD` placeholder with the actual access date.

Select 2–4 `related_keywords` from the related-query and source evidence before drafting. Each must
be a natural English phrase of 2–8 words, remain within the selected primary intent, and add a
distinct supporting concept. A related keyword must not equal, contain, or be contained by the
exact core keyword or another selected related keyword; this prevents one occurrence from
artificially satisfying multiple counters.

For originality:

- synthesize source facts into a new decision framework, explanation, comparison, or checklist;
- vary the lead, H2 architecture, section order, table dimensions, examples, FAQ, and ending;
- do not reuse generic sections merely to reach the character target;
- do not combine unrelated intents or repeat the same idea under different headings;
- treat recent sources as freshness evidence, not as text to paraphrase line by line.

## Required fields

- `title` is the page H1 and must equal `seo_title1`.
- Use natural professional English, include the exact core keyword exactly once as a grammatical
  part of the title sentence, use Title Case, and stay within 100 English characters. Prefer 80 or
  fewer for WUZHICMS compatibility.
- Do not write `<keyword>: <subtitle>`, `<keyword> - <subtitle>`, or a bare keyword followed by a
  separator. Add at least three meaningful content words around the keyword and connect it to a
  verb, question, comparison, decision, process, risk, or outcome.
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
Before drafting, run:

```bash
python scripts/select_title_mode.py \
  --seed "<run-id>|<tab>|<sheet-row-number>|<exact-core-keyword>" \
  --output <row-run-dir>/title-mode.json
```

Create the seed from values fixed before title drafting and never redraw or alter it after seeing
the result. A roll from 0 through 69 requires one question mark at the end of a genuine question; a
roll from 70 through 99 requires a statement title with no question mark. This produces an
auditable 70% question-title probability across jobs. Record the seed, roll, and `title_mode` in the
row manifest.

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

For question mode, use any pattern except `direct-statement`. For statement mode, use any pattern
except `question`; `how-to` may be a declarative “How to…” title without a question mark. Treat mode
and pattern as separate fields so the 70% question requirement still permits varied how, which,
why, process, comparison, risk, benefit, numbered, and decision structures.

Use the least-used compatible angles and patterns in the current run. Rotate through every
compatible value before starting another cycle; never repeat an angle or pattern on consecutive
current-run titles, and never reuse the same angle-pattern pair within one run. Rotate openings,
syntax, and value propositions; do not repeatedly start with “How to Choose,” “Ultimate Guide,”
“Best,” “Top,” or “Complete Guide.” Country/customer substitution does not count as diversity.

Write every title in a neutral third-person editorial voice. Do not use “we,” “our,” unsupported
superlatives, or a formula that presents the host company as the inevitable answer. For a keyword
that explicitly requests “top N,” “best,” “leading,” or a manufacturer list, disclose objective
inclusion criteria and the evidence date in the article. Prefer alphabetical, categorical, or
otherwise non-ranked ordering unless comparable evidence supports each rank. Evaluate the host
company under the same criteria as every other named company.

Before validation, create `title-history.json` containing accepted titles from earlier tabs in the
run and up to 20 recent titles from the current site when available. Exclude the current draft.
Use this shape:

```json
[
  {
    "title": "How Does Material Grade Change Product Performance?",
    "keyword": "material grade",
    "angle": "feature-analysis",
    "pattern": "technical-explainer",
    "mode": "question",
    "question_roll": 24,
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

## Neutral editorial treatment

- Write from the buyer's decision perspective in third person. Replace “we,” “our product,” and
  “our factory” with the verified company, product, or facility name.
- Present advantages together with operating conditions and limitations. For comparisons, apply the
  same dimensions and evidence standard to every material, solution, or supplier.
- For “top N manufacturers” or similar list content, state the inclusion criteria, evidence date,
  geographic or product scope, and limitations. Do not imply that inclusion is an audited rank.
- Use alphabetical, categorical, or evidence-based ordering. Assign numbered ranks only when
  current comparable data supports each position; otherwise describe the list as a shortlist.
- Do not automatically place the host company first. Evaluate it under the same criteria, distinguish
  same-site claims from independently verifiable facts, and omit any company lacking sufficient
  evidence rather than filling a target count with invented claims.

## HTML structure

Use this order:

1. Copy the complete scoped `<style data-article-style="responsive-v1">` block from
   `assets/article-content-style.html`.
2. Open one `<article class="article-content">` wrapper.
3. Add one lead `<p>` that directly answers the primary question.
4. Add five to nine H2 sections and deepen multiple non-FAQ H2 sections with H3 subheadings.
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

### Non-FAQ H3 depth

Use H3s to develop the existing H2 argument, not to add a second search intent or inflate the
outline. FAQ question H3s never count toward the body-depth requirement.

| Visible article length | Minimum non-FAQ H3s | Minimum non-FAQ H2 sections containing H3s |
| --- | --- | --- |
| 10,000–11,999 characters | 6 | the greater of 3 or half of non-FAQ H2s, rounded up |
| 12,000–13,499 characters | 7 | the greater of 4 or half of non-FAQ H2s, rounded up |
| 13,500–15,000 characters | 8 | the greater of 4 or half of non-FAQ H2s, rounded up |

Cap the required parent-section count at the number of available non-FAQ H2s. Require at least one
more body H3 than the minimum parent-section count so at least one important H2 receives a genuine
two-part analysis. Use at most 10 non-FAQ H3s and no more than twice the number of non-FAQ H2s; the
validator applies the lower of those two limits.

- Make every H3 unique, descriptive, and specific to its parent H2. Avoid labels such as
  “Overview,” “Key Factors,” “More Details,” or “Things to Consider” when the heading does not name
  the actual factor, test, material, decision, or limitation.
- Follow every non-FAQ H3 with at least one paragraph, list item, table cell, or caption and at least
  180 visible characters before the next H3 or H2. A heading followed only by an image, placeholder,
  or one-line restatement is not developed content.
- Start the subsection with a direct answer or finding, then add the evidence, operating condition,
  comparison basis, limitation, or buyer implication that makes the subsection independently useful.
- Keep H3s within the same primary search intent. Do not fragment one paragraph into artificial
  headings, duplicate the parent H2 wording, or give every H2 the same repeated subheading pattern.

## Intent-driven ending

Choose and record exactly one `ending_mode`:

| Buyer stage | Allowed ending modes | Default |
| --- | --- | --- |
| `awareness` | `informational-close` | `informational-close` |
| `consideration` | `informational-close`, `inline-cta` | `informational-close` |
| `evaluation` | `informational-close`, `inline-cta` | `inline-cta` when a next verification step is useful |
| `inquiry` | `inline-cta`, `standalone-cta` | `inline-cta` |

- `informational-close`: End with a useful synthesis, limitation, decision criterion, or next
  technical step. Do not add a CTA marker or force a contact link.
- `inline-cta`: Add one short, article-specific final paragraph marked exactly
  `<p data-article-cta="inline">...</p>`. Integrate it after the final useful content; do not create
  a CTA-only H2.
- `standalone-cta`: Use only at the `inquiry` stage for `product-selection`, `oem-odm`, or
  `supplier-evaluation` when the ending adds substantive RFQ,
  specification, sample, testing, packaging, or quotation guidance. Wrap it exactly in
  `<section data-article-cta="standalone">...</section>`. Do not use it merely to repeat a contact
  link.

Prefer the default mode. `foundational-knowledge` always uses `informational-close`, even at the
consideration stage. An awareness article must not ask for a quote, sample, or customization request
in the lead or ending. A contact link is optional outside inquiry and appropriate only when it
directly advances the buyer's current task. Base every CTA on services confirmed on the site.

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

## Lead, keyword distribution, and internal links

- Place the core keyword naturally near the beginning of the lead.
- Link the first occurrence of the core keyword to a real, relevant page on the same site.
- Use the exact core keyword 3–5 times in visible `content.html` copy. The linked lead occurrence
  counts as the first use. Distribute the phrase across the lead and at least two later content
  blocks; never use it more than once in the same paragraph, heading, list item, table cell, or
  caption. A heading occurrence is optional and must not be a mechanical prefix.
- Use every selected related keyword 1–2 times. Keep all selected related keywords at 3–5 visible
  occurrences in total and distribute them across at least two content blocks. Prefer a useful
  technical, comparison, application, or purchasing sentence over a standalone keyword sentence.
- Count only reader-visible text inside `.article-content`: headings, paragraphs, list items,
  table cells, and captions. Do not count or manipulate `title`, `seo_title1`, `remark`, `seo_desc`,
  CSS, HTML attributes, anchor URLs, image alt text, hidden text, or page chrome. Do not use a
  plural/singular rewrite as an exact occurrence unless it exactly matches the recorded phrase.
- Use only verified same-site HTTPS links. Never invent a URL or substitute a competitor.
- Add one or two relevant internal links per 2,000 visible English characters: normally 5–10 links
  for a 10,000-character article and 8–15 for a 15,000-character article.
- Use descriptive, non-repeated anchor text; do not use “Click Here” or “Read More”.

## Length and GEO quality

- Target 12,000–13,500 visible English characters. Require the final article to remain between
  10,000 and 15,000 characters, including spaces and punctuation in headings, paragraphs, lists,
  tables, FAQ, and any CTA that is present.
- Exclude HTML tags, anchors, image paths, SEO fields, and page chrome from the count.
- Prefer independently understandable answers, complete product/material names, explicit
  comparison conditions, and consistent facts. Meet keyword counts through relevant statements;
  do not pad, cluster, or mechanically repeat phrases.

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
- Use 4 body images for 10,000–12,499 visible characters and 5 for 12,500–15,000.
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

Require exact field equality, valid heading hierarchy, length-adjusted non-FAQ H3 depth across
multiple body sections, no generated TOC, one scoped responsive style block, one
`.article-content` wrapper, fixed pixel-based font sizes, responsive table wrappers,
same-site theme evidence, exact palette-to-CSS equality, accessible site-themed font and table
colors, natural spacing, the configured visible-character range, verified internal links, the
correct placeholder/image count, distinct alt text, four to six FAQs, inspected same-site visual
references, a deduplicated global image pool, unique source assignment and article roles,
perceptually distinct final images, no target-country/customer title modifiers, a unique
title angle-pattern pair, a valid seeded 70/30 title mode, one naturally integrated title keyword,
neutral title and article wording, sufficient title diversity, one primary intent from the
seven-type taxonomy, no more than one subordinate secondary intent, a compatible buyer stage,
current documented research, a varied evidence-led outline, 10,000–15,000 visible characters with
a 12,000–13,500 target, 3–5 distributed exact core-keyword occurrences, 2–4 distinct related
keywords with 3–5 combined distributed occurrences, a buyer-stage-appropriate non-boilerplate
ending, and no unsupported claims.
