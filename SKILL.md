---
name: seo-geo-article-publisher
description: Generate, validate, publish, and verify English B2B SEO/GEO articles from the configured Google keyword spreadsheet, one pending row per site tab. Use only when the user explicitly invokes $seo-geo-article-publisher to run or dry-run this exact multi-site workflow, including keyword-led search-intent research, diverse drafting, site-theme-matched content and table colors, intent-driven article endings, globally deduplicated same-site image selection, whole-image regeneration around an extracted and locked original product, WebP preparation, WUZHICMS API publishing, live-page verification, and spreadsheet status updates.
---

# SEO/GEO Article Publisher

Run the configured spreadsheet-to-website workflow as one auditable job. Treat explicit invocation
without `dry-run` as authorization to claim pending rows, publish articles, and update the source
spreadsheet. Never expose, persist, or repeat a publishing key.

## Required reading

- Read [references/content-spec.md](references/content-spec.md) before researching or drafting.
- Read [references/publishing.md](references/publishing.md) before reading or updating the Sheet,
  publishing, verifying a page, or handling a partial failure.
- Read [references/api-contract.md](references/api-contract.md) before calling a site API.
- Load and follow the installed `google-drive:google-drive` and
  `google-drive:google-sheets` skills before Sheet operations.
- Load and follow the installed `imagegen` skill before generating any article image.

## Workflow

1. **Preflight**
   - Use spreadsheet ID `1n-J4tu5IfiaVQI9496hRzlFNKLwXNQLDQY_HZAf1UmM`.
   - Read spreadsheet metadata and preserve visible tab order. Require the eight headers documented
     in `references/publishing.md`.
   - Confirm Google Sheets read/write access, image generation, network access, and a writable run
     directory outside this skill.
   - For a live run, confirm each selected domain serves HTTPS and its publishing endpoint exists.

2. **Select and claim work**
   - Process every visible site tab in order.
   - Select only the first row whose `发布状态` is blank; select at most one row per tab.
   - In a live run, write `处理中:<run-id>` to that row, re-read it, and continue only if the same
     value remains. In a dry-run, do not write the Sheet or publish.
   - Save non-secret job metadata and artifact paths in `<cwd>/article-runs/<run-id>/manifest.json`.
     Never store `发布密钥`.
   - Initialize `<cwd>/article-runs/<run-id>/title-history.json` as a JSON array. Before drafting
     each row, include accepted titles from earlier tabs in the current run and up to 20 recent
     article titles from the current site when available. Exclude the current draft title.

3. **Research the site**
   - Start from the related product URL and the tab domain. Inspect relevant product/category,
     service, factory/about, application, contact, and sitemap pages as available.
   - Identify the canonical same-site article listing page from the site's primary navigation or
     article archive. Require HTTPS, the same host as the site tab, HTTP 200, and evidence that the
     page lists recent articles. Save it as `article_listing_url` in the row manifest for
     post-publish thumbnail verification; do not substitute a generic homepage unless it is the
     site's actual article listing.
   - Inspect the rendered homepage and related product page for the current site's visual theme.
     Capture same-site evidence for the primary accent and normal body-text color from computed CSS,
     a loaded same-site stylesheet, or—in the absence of a usable UI accent—the site's logo. Do not
     infer the website theme from product packaging or another domain.
   - Normalize observed colors to six-digit hex and save the evidence plus the complete applied
     palette in `<row-run-dir>/theme-colors.json` using `references/content-spec.md`. Build a fresh
     palette for every site tab; never reuse another site's palette unless the recorded evidence
     independently shows the same colors. Record the palette file, source URLs, and selected colors
     in the row manifest.
   - Infer the user's search purpose primarily from `核心关键字`. Use query modifiers and phrasing
     first; use `目标国家`, `目标客户`, and `相关产品链接` only to disambiguate and deepen the chosen
     intent. Select exactly one primary intent from the seven types in
     `references/content-spec.md`. Select zero or one secondary intent only when it directly
     supports the primary intent; never give both equal weight or join unrelated topics.
   - Classify the buyer stage as exactly one of `awareness`, `consideration`, `evaluation`, or
     `inquiry` from the keyword evidence. Record why the query belongs to that stage and use the
     stage—not a fixed commercial template—to control the ending and next action.
   - Search two to six closely related queries before drafting. Prefer current primary sources,
     standards bodies, regulators, industry associations, and technically credible references.
     Use external research for general context only; never replace verified site/product facts with
     competitor claims or copy another page's wording, outline, or examples.
   - Select 2–4 natural English `related_keywords` from the related-query and source evidence.
     Keep every phrase within the same primary intent, use 2–8 words, and reject phrases that
     equal, contain, or are contained by the core keyword or another selected related keyword.
   - Save the keyword signals, primary and optional secondary intent, intent rationales, rejected
     intents, buyer stage and rationale, `neutral-buyer-guidance` editorial stance, related queries,
     selected related keywords, same-site sources, external research sources, access dates, and
     freshness notes in
     `<row-run-dir>/intent-analysis.json`. Require at least one same-site source and one external
     source; when no credible external source exists, record a concrete
     `external_source_reason`.
   - Use only confirmed site facts and general industry knowledge. Record source URLs for claims,
     internal links, and image references in the manifest.
   - Build one global same-site candidate pool before selecting any image. Prefer 3–8 distinct
     candidates across the related product gallery/category and relevant factory, application,
     laboratory, production, packaging, warehouse, or service pages. Keep the highest-resolution
     product views that make the real product verifiable. Do not add a different SKU, variant, or
     brand merely to create visual variety.
   - Run `scripts/analyze_image_pool.py` on the downloaded candidates. Consolidate exact SHA-256
     duplicates and perceptual near-duplicates at Hamming distance 6 or less before selection.
     Classify the retained candidates and record view angle, scene type, label legibility, article
     relevance, product-lock eligibility, and an exact identity summary. If fewer than the
     preferred candidates remain, record a concrete `candidate_pool_limit_reason`.
   - For every product candidate, inventory the exact visible brand/logo text, product or variant
     name, other legible label text, package colors/materials, container shape, closures,
     proportions, and product form. Preserve capitalization and spelling; never translate or
     "correct" label text.
   - Record whether the site has product visuals, visibly branded product visuals, and legible
     product labels. A generic category illustration does not count as a product reference.
   - Record the selected primary slug as `search_intent`, the optional subordinate slug as
     `secondary_intent`, and the stage as `buyer_stage`; require all three to match
     `intent-analysis.json`. Stop and mark the row failed if the site lacks enough trustworthy
     product context to produce the minimum article length.

4. **Draft and generate images**
   - Follow `references/content-spec.md`. Save `title.txt`, `seo_title1.txt`, `remark.txt`,
     `seo_desc.txt`, and `content.html`.
   - Use `目标国家` and `目标客户` only to shape the article's research, examples, terminology,
     objections, and any justified CTA. Do not copy, append, translate, paraphrase, or otherwise
     expose either value in `title`/`seo_title1`; do not use geographic names, demonyms, country
     codes, customer segments, buyer roles, or formulas such as `for <customer> in <country>`. The
     only exception is an audience term already present inside the exact `核心关键字`; do not add
     another audience term.
   - Before drafting the title, create the immutable seed
     `<run-id>|<tab>|<sheet-row-number>|<exact-core-keyword>` and run
     `scripts/select_title_mode.py`. Save the result as `<row-run-dir>/title-mode.json`; never
     redraw or change the seed after seeing the result. Rolls 0–69 require a question title and
     rolls 70–99 require a statement title, producing an auditable 70% question probability.
   - Select one evidence-based title angle and one title pattern from
     `references/content-spec.md`. Use the least-used available angles and patterns so each set is
     rotated once before reuse; never repeat either one on consecutive current-run titles and never
     reuse the same angle-pattern pair within a run. Compare the draft against `title-history.json`
     and rewrite exact, template-level, or high-overlap matches. Record `title_angle` and
     `title_pattern` in the row manifest. Treat question/statement mode separately from the pattern
     so question titles still rotate among how, which, why, comparison, risk, process, and decision
     structures.
   - Include the exact core keyword once as a grammatical part of the title sentence. Do not use
     `<keyword>: <subtitle>`, `<keyword> - <subtitle>`, or a bare keyword followed by punctuation.
     Give the keyword a natural subject, verb, decision, comparison, or consequence. Use a neutral
     third-person editorial voice in both title and article; do not write as “we” or “our.”
   - For “top N,” “best,” “leading,” or manufacturer-list queries, use transparent inclusion
     criteria, current evidence, and neutral ordering. Apply the same criteria to the host company
     and other named companies; do not invent ranks, imply endorsement, or turn the article into a
     disguised advertisement.
   - Use the site page title as the page H1; do not add an `<h1>` inside `content.html`.
   - Select one `ending_mode` from `informational-close`, `inline-cta`, or `standalone-cta` according
     to the buyer-stage rules in `references/content-spec.md`, and record it in the row manifest.
     Do not generate a fixed CTA for every article. Awareness content must close informationally;
     consideration and evaluation content may suggest a relevant next check; inquiry content may
     naturally request specifications, samples, customization details, or a quotation.
     Use a standalone CTA section only when it adds specific decision or RFQ value that cannot fit
     naturally into the preceding section.
   - Mark an inline CTA only as `<p data-article-cta="inline">...</p>` and a standalone CTA only as
     `<section data-article-cta="standalone">...</section>`. Do not label readers by target country
     or target customer, and do not reuse headings or phrases such as “Buyers ready to,” “Build a
     comparable RFQ,” or “Request a comparable proposal.”
   - Build every H2 around the single primary intent and the current research evidence. Use an
     optional secondary intent only where it helps answer the primary question. Vary the
     outline, lead, examples, comparison dimensions, table structure, FAQ questions, and ending
     across articles. Add source-derived decision value rather than padding to a fixed word count.
     Do not reuse a standard article skeleton or splice in sections that answer a different intent.
   - Deepen the existing non-FAQ H2 sections with topic-specific H3 subheadings according to the
     length and section-coverage rules in `references/content-spec.md`. FAQ questions do not count
     toward this requirement. Give every non-FAQ H3 at least 180 visible characters of substantive
     explanation before the next heading, and distribute H3s across multiple H2 sections instead of
     mechanically splitting one section or repeating generic labels.
   - Keep the combined exact target-keyword density between 1.00% and 3.00% of all reader-visible
     English words in `content.html`. Calculate density as the weighted word count of the exact core
     keyword plus every selected `related_keyword`, divided by the total visible word count. For
     example, a four-word phrase used three times contributes 12 keyword words. Do not count
     `title`, SEO fields, CSS, HTML attributes, image alt text, hidden text, or page chrome.
   - Count the linked lead occurrence of the core keyword, then distribute the phrase across the
     lead and at least two later paragraphs, headings, list items, table cells, or captions. Use
     every selected related keyword at least once and distribute related-keyword uses across at
     least two content blocks. Never repeat the same exact phrase twice in one content block or
     force every occurrence into headings. Rewrite a sentence when a phrase sounds forced; never
     add an unrelated section merely to reach the density range.
   - Do not generate a table of contents or `<nav class="article-toc">`. Start `content.html` with
     the scoped style block from `assets/article-content-style.html`, then wrap the article in
     `<article class="article-content">`.
   - Before inserting the style block, replace every article color custom property with the current
     site's validated palette from `theme-colors.json`. Apply the site theme consistently to body
     text, muted text, headings, links, borders, surfaces, table headers, table-header text, striped
     rows, hover rows, and soft callout backgrounds. Do not leave the asset's example green palette
     in articles for unrelated sites.
   - Preserve the site's primary hue while deriving darker or lighter variants where contrast
     requires it. Require WCAG AA contrast for normal text, links, headings, table-header text, and
     table body text; never sacrifice readability merely to copy a low-contrast site color.
   - Include readable element spacing and at least one responsive table inside
     `.article-table-wrap`; preserve the style asset's mobile breakpoints.
   - Keep every CSS `font-size` declaration as a fixed `px` value. Do not use `rem`, `em`, `%`,
     viewport units, or fluid `clamp()` expressions for text sizing because the host sites define
     root typography differently.
   - Place `[IMAGE_BASE64]` repeatedly at the intended body-image locations.
   - Plan the thumbnail and all body images together before generating any of them. Use
     `weighted-global-assignment-with-duplicate-penalty`, score every candidate for the intended
     slot with 30% keyword/product relevance, 25% identity clarity, 15% image quality, 15% section
     fit, and 15% diversity, and record the scores plus a specific selection reason.
   - Assign a distinct article role to every slot. Prefer `product-hero` for the thumbnail, then
     choose section-relevant roles such as `product-detail`, `inspection-comparison`,
     `factory-production`, `laboratory-quality`, `application-use`, `packaging-logistics`, or
     `warehouse-supply`. Do not choose the first or clearest product photo greedily for every slot.
   - Select each retained source candidate at most once per article. The only exception is when
     exactly one valid product candidate exists: that source may appear in at most two slots, the
     exception must be documented, and the two outputs must have different roles, composition,
     scale, section purpose, and regenerated scenes. Fill remaining slots with relevant same-site
     non-product candidates. Product identity accuracy always outranks variety.
   - Classify every planned image as `product-present` or `non-product`. For `product-present`
     images, use an inspected original same-site product image as the identity source, not merely as
     loose inspiration. Every final `product-present` image must be newly regenerated for
     its article placement; copying the source image unchanged, placing it on a plain `contain`
     canvas, or using a blurred/solid extension does not count.
   - Use only `source-product-locked-regeneration`. Create and inspect a product mask, then run
     `scripts/prepare_locked_product.py` to extract the complete original product as a transparent
     locked PNG without repainting its interior, and save its JSON extraction report. Supply that
     locked product as the required image input and regenerate the complete final canvas in one
     cohesive image-generation pass. Generate the new scene, layout, surface, props, ambient light,
     and natural contact shadow around the locked product; do not generate an empty background first
     and do not paste the product onto it afterward with deterministic compositing.
   - Call image generation as a referenced-image edit, passing both the local locked-product PNG and
     inspected mask as `referenced_image_paths`; omit `num_last_images_to_include`. A text-only
     generation or a call that omits the locked product is invalid.
   - Treat the extracted product as a non-editable identity object during whole-image regeneration.
     The model may reposition or proportionally scale the complete object only when needed for the
     composition. It must not redraw, retype, restyle, blur, hide, crop, rotate, relight, recolor,
     or substitute the product, logo, brand name, label text, package colors, container geometry,
     closure, proportions, reflections, accessories, or visible product form.
   - Reject a regenerated image if image generation changes any brand letter, label word, typography,
     package detail, package color, or product geometry. Retry whole-image regeneration using the
     extracted product and lock mask as the identity constraint. If no regenerated result preserves
     exact product identity, fail the image and row; do not fall back to deterministic compositing,
     the unchanged source, or a `contain`-only output. Use same-site factory, application,
     laboratory, production, or service references for `non-product` images whenever available.
   - Target 12,000–13,500 visible characters and require 10,000–15,000. Create one thumbnail plus
     4 body images below 12,500 visible characters or 5 body images from 12,500–15,000. Do not
     invent packaging, certificates, factories, test results, label text, or specifications.
   - When same-site branded/labelled product visuals exist, require the thumbnail and at least one
     body image to show the original brand and legible label accurately. Do not satisfy this rule
     by shrinking, blurring, turning away, or obscuring the package.
   - Load the original reference, extracted locked product, raw whole-image generation, and final
     WebP with `view_image` (or equivalent original-detail visual inspection) and compare them side
     by side at 100% zoom. Do not mark a check from the prompt alone. Record image classification,
     candidate ID, reference URLs/files, preservation method, lock-mask and extraction evidence,
     whole-image regeneration evidence, exact source identity, retained product elements,
     brand/label/package/geometry checks, visual inspection evidence, output file, and inspection
     result in `image-references.json` and the run manifest. Also record the complete deduplicated
     `candidate_pool` and global `selection_plan`.
   - Run `scripts/optimize_image.py` only after the whole-image regeneration exists, to encode the
     final WebP and save body-image alt text in upload order. `--fit contain` is only a final
     anti-clipping safeguard for an already regenerated image; it never satisfies the regeneration
     requirement by itself. Reinspect the final WebP against the source before setting
     `inspection_result` to `pass`. Reject final output pairs whose perceptual hashes are less than
     10 bits apart; when the one-source exception is used, require its two regenerated outputs to
     be at least 12 bits apart.

5. **Validate**
   - Run `scripts/validate_article.py` with the final copy, keyword, target country, target
     customer, title-mode seed, primary search intent, buyer stage, ending mode, title angle, title
     pattern, title history, site host, intent-analysis file, image count, and ordered alt texts.
   - Require the validator to confirm no generated TOC, one scoped responsive CSS block, one
     `.article-content` wrapper, responsive table wrappers, mobile breakpoints, and fixed
     pixel-based font sizes. Pass `theme-colors.json` and require exact agreement between its
     site-specific palette and every CSS color variable, same-site theme evidence, complete
     theme-variable use for fonts and tables, and passing contrast checks. Also require structured
     same-site product-identity evidence, an extracted locked product and mask, auditable raw
     whole-image regeneration, and passing brand, label, packaging, geometry, and side-by-side
     visual checks for every `product-present` image. Reject deterministic composites,
     background-only edits, unchanged-source, and contain-only product outputs.
   - Require a 3–8-candidate global image plan unless a concrete shortage is documented. Require
     recorded source hashes, consolidation of exact/near duplicates, weighted whole-article slot
     assignment, distinct article roles, unique selected sources, and perceptually distinct final
     outputs. Allow a repeated product source only under the documented single-valid-source
     exception.
   - Require the validator to reject titles derived from target-country or target-customer fields,
     duplicate angle-pattern pairs, exact title duplicates, repeated title templates, and
     high-overlap titles. Require the seeded 70/30 title mode, exactly one naturally integrated core
     keyword, no keyword-plus-colon/dash prefix, and neutral third-person wording. After clean
     validation, append the title, core keyword, title mode, question roll, title angle, title
     pattern, tab, and `current-run` source to `title-history.json`.
   - Require the validator to reject a mandatory or generic bottom CTA, an ending mode incompatible
     with the search intent, missing/duplicate CTA markers, target-country/customer labels inside a
     CTA, and repeated CTA boilerplate.
   - Require the validator to confirm one primary intent from the seven-type taxonomy, no more than
     one subordinate secondary intent, a compatible buyer stage, neutral editorial stance,
     documented query signals, related searches, 2–4 non-overlapping related keywords, a combined
     exact target-keyword density of 1.00%–3.00% of reader-visible words, natural block-level
     distribution, current source access dates, same-site evidence, and external research (or a
     concrete no-source reason).
   - Require length-adjusted non-FAQ H3 counts, coverage across multiple body H2 sections, unique
     H3 text, and at least 180 visible characters of supporting content beneath every body H3.
   - Verify every internal link returns a successful response and belongs to the site.
   - Require a clean validation result before any API call.

6. **Publish and verify**
   - Run `scripts/publish_article.py`; enter the row's publishing key through its hidden prompt or a
     pre-existing environment variable. Never put the key in a command argument.
   - Upload `thumb` plus ordered `content_img[]` WebP files and matching `content_img_alt[]` values.
   - After API success, run `scripts/verify_article.py` with the returned article URL, recorded
     `article_listing_url`, returned thumbnail path, returned content-image paths, and
     `theme-colors.json`.
   - Check the exact title, every returned content-image path, responsive style marker, complete
     site-theme palette, `.article-content` wrapper, absence of the old TOC, and placeholder
     replacement on the article detail page. Do not require the thumbnail path on the detail page.
   - Check the returned thumbnail separately: require its same-site `.webp` path to return HTTP 200
     with non-empty content, and require the path to appear on the recorded article listing page.
     Treat the complete detail-page, thumbnail-asset, and listing-page result as one verification
     attempt. Check immediately, wait 30 seconds once when needed, and then check the complete
     result again.
   - Update the Sheet exactly as specified in `references/publishing.md`.

7. **Continue and report**
   - Continue to the next site tab after a site-specific failure. Stop the whole run for lost Sheet
     access, invalid headers, or another systemic preflight failure.
   - Report each tab, source row, primary and optional secondary intent, buyer stage, title mode,
     ending mode, title angle, title pattern, final state, article URL, verification result, and
     manifest path. Never report publishing keys.

## Failure rules

- Before API success, write `失败:<concise reason>` for a claimed live row.
- After API success, never publish the same job again speculatively.
- If both complete public verification attempts fail, write `待人工检查`, retain the publish time
  and returned article URL, and continue to the next tab.
- Write `已发布` only after the public page passes verification.
- Do not automatically clear `失败` or `待人工检查`; require an explicit user decision before retrying.

## Script commands

```bash
python scripts/analyze_image_pool.py --image CANDIDATE_1 --reference-url SAME_SITE_URL_1 \
  [--image CANDIDATE_2 --reference-url SAME_SITE_URL_2 ...] --output IMAGE_POOL_JSON
python scripts/prepare_locked_product.py --source SOURCE_PRODUCT \
  --mask INSPECTED_MASK_PNG --output LOCKED_PRODUCT_PNG --report LOCK_REPORT_JSON
python scripts/select_title_mode.py --seed "RUN_ID|TAB|ROW_NUMBER|CORE_KEYWORD" \
  --output TITLE_MODE_JSON
python scripts/optimize_image.py INPUT OUTPUT --kind thumb|content [--fit cover|contain]
python scripts/validate_article.py --title-file FILE --seo-title-file FILE \
  --remark-file FILE --seo-desc-file FILE --content-file FILE --keyword TEXT \
  --target-country TEXT --target-customer TEXT --title-angle ANGLE \
  --title-pattern PATTERN --title-mode-seed TEXT --title-history-file FILE \
  --search-intent INTENT --buyer-stage STAGE --ending-mode MODE \
  --intent-analysis-file FILE --site-host HOST \
  --theme-colors-file FILE --content-images N --alt-text-file FILE \
  --image-reference-file FILE
python scripts/publish_article.py --endpoint URL --title-file FILE --seo-title-file FILE \
  --remark-file FILE --seo-desc-file FILE --content-file FILE --thumb FILE \
  --content-image FILE --content-image-alt TEXT [--content-image FILE ...] [--dry-run]
python scripts/verify_article.py --url ARTICLE_URL --listing-url LISTING_URL \
  --title-file FILE --theme-colors-file FILE --thumbnail-path THUMB_PATH \
  --content-image-path BODY_PATH [--content-image-path BODY_PATH ...] --retry-delay 30
```

Use paths relative to this skill directory for scripts. Keep generated runs outside the skill.
