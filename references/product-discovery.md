# Whole-site product discovery

Read this during site research. The Sheet's related-product URL is a seed, not an exclusive source.
Find relevant products across the site's entire catalogue before choosing product images or
concluding that usable product context is missing.

## Search coverage

1. Discover product catalogue roots and category links from the homepage navigation, supplied URL,
   product menus, and sitemap index. Follow child product/category sitemaps and nested categories.
   Use only the site's public pages; stay on the tab host or its verified same-site www alias.
2. Inspect every discovered product list and category, including every pagination page. For
   load-more or client-rendered lists, use the rendered page and continue until the catalogue ends.
   Deduplicate canonical URLs and stop pagination loops when no new products appear. Do not stop
   after the first promising product, supplied category, or first list page.
3. Search the combined catalogue using the keyword and natural synonyms, alternate product names,
   ingredients/materials, product family, and intended application. Follow the list screening
   procedure below before opening product details.
4. Use the site's own search and focused external `site:` searches to find orphaned pages or resolve
   gaps. Search-engine results supplement catalogue coverage; they do not prove that a product is
   absent. A missing sitemap is not a failure if accessible navigation and lists cover the catalogue.
5. Rank verified matches by keyword relevance, then same-family/use-case relevance, available facts,
   and usable original images. Select the best supported product after surveying the lists.
   Prefer high-resolution images from that product's actual gallery and record the detail-page URL.

Related products are allowed when the article truthfully discusses that family or application.
An exact keyword in the product title is not required. Keep each product's identity and facts
separate: a plant-protein product may support a clearly identified plant-protein comparison, but
does not prove a whey product exists or that the host supplies whey. Do not rename a different
product to match the keyword or add unrelated SKUs merely for visual variety. If the primary
intent can be answered with verified related products and accurately stated limits, continue.
Fail only when the available evidence still cannot support a truthful article and relevant images.

## Screen product lists before opening details

1. Collect each card's product title and product-specific description, ingredients, form, and
   application when shown. Merge useful metadata from duplicate cards by canonical URL. Keep the
   sources that supplied it. Exclude navigation, CTA labels, and repeated site-wide sales copy
   from `list_text`. For broad service keywords such as private label or OEM, derive specific
   product families and applications from the search intent and planned article scope. A shared
   service badge or sales line does not make a product a match.
2. Screen the combined list once with the run's terms. For a large catalogue, use the bundled
   helper on a JSON array of deduplicated records with `url`, `title`, and `list_text` fields.
   Include sitemap-only products even if both metadata fields are empty. Supply `--term` once per
   keyword or synonym. Supply `--boilerplate` once per verified, repeated template phrase still
   present in the cards. Pass the complete phrase, never an isolated term such as `private label`.
   For example, when observed in the current iGuge catalogue, remove `Discuss private label formula
   and packaging options for your market.` from card text while retaining product titles.

   ```sh
   python3 /path/to/seo-geo-article-publisher/scripts/screen_catalogue.py catalogue-products.json \
     --term 'core keyword' --term 'product family' > catalogue-screening.json
   ```

3. Open `open-detail` entries, the supplied seed detail, and any other candidates surfaced by
   site search. Review `review-list` entries in groups by family or use case. Skip a detail only
   when inspected list metadata clearly places the product outside the article's scope. Open
   plausible synonyms, ambiguous entries, and sitemap-only entries with insufficient metadata.
   A missing literal match or a URL slug alone cannot establish irrelevance. If no suitable
   product is confirmed, widen the terms and resolve remaining plausible entries before drawing
   a conclusion. Reuse successful responses within the current run when verifying details and
   galleries so the same canonical URL is fetched once for discovery.

## Evidence

Save `<row-run-dir>/product-discovery.json` and link it from the row manifest. Include:

- `seed_urls` and `search_terms` (keyword, synonyms, family, material, application).
- `run_id` and `site_host` identifying the current row's run and site.
- `catalogue_sources`: each root/category/sitemap URL, access result, visited pagination URLs,
  discovered product count, and whether traversal reached its end.
- `products`: deduplicated discovered detail URLs with titles or other inspected list metadata;
  record which details were opened, the reason for opening or skipping each detail, and which
  list/sitemap discovered them. If the screening helper was used, retain its output alongside
  `product-discovery.json` and record the final decisions in `products`.
- `matches`: product URL, verified name, relevance (`exact-product` or `same-product-family`),
  relevance explanation, and `gallery_image_urls` containing every original gallery image URL
  observed on that detail page, including slides, alternate views, and full-resolution links.
  Record usable images and fact/suitability limitations separately; do not reduce the inventory
  to the chosen product's first picture or copy it from a previous run.
- `coverage_status`: `complete` for all discovered accessible catalogue paths traversed to their
  end, or `incomplete` with the blocked/unvisited URLs and reasons in `coverage_gaps`.
- `selected_product_urls`, `selection_reason`, and `no_suitable_product_reason` when applicable.

Completeness describes the observed catalogue, not a guarantee about undiscoverable pages. If a
list cannot be opened or fully paginated, record the gap and try another public catalogue/search
route. Sufficient verified matches can still support publication despite a disclosed coverage gap.
If no match can be verified because access is incomplete, report an access/coverage limitation;
do not report that the whole site has no relevant product. Include the coverage summary and chosen
product links in the run result.

Next follow [image-selection.md](image-selection.md): review and classify the complete galleries
of all relevant matches before constructing the 3–8 image shortlist. A product shortlist, a renewed
download of an old image, or an unchanged page count is not evidence of a fresh gallery inspection.
