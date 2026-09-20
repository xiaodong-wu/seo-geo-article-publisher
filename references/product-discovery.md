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
   ingredients/materials, product family, and intended application. Inspect list titles and
   descriptions; open matching and ambiguous detail pages to check relevance and original images.
   Inspect sitemap-only product entries too; open unclear entries rather than treating a URL slug
   as proof of the product's contents. Unrelated products with clear list metadata need no deep read.
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

## Evidence

Save `<row-run-dir>/product-discovery.json` and link it from the row manifest. Include:

- `seed_urls` and `search_terms` (keyword, synonyms, family, material, application).
- `catalogue_sources`: each root/category/sitemap URL, access result, visited pagination URLs,
  discovered product count, and whether traversal reached its end.
- `products`: deduplicated discovered detail URLs with titles or other inspected list metadata;
  record which details were opened and which list/sitemap discovered them.
- `matches`: product URL, verified name, relevance (`exact-product` or `same-product-family`),
  relevance explanation, usable original image URLs, and any fact or suitability limitations.
- `coverage_status`: `complete` for all discovered accessible catalogue paths traversed to their
  end, or `incomplete` with the blocked/unvisited URLs and reasons in `coverage_gaps`.
- `selected_product_urls`, `selection_reason`, and `no_suitable_product_reason` when applicable.

Completeness describes the observed catalogue, not a guarantee about undiscoverable pages. If a
list cannot be opened or fully paginated, record the gap and try another public catalogue/search
route. Sufficient verified matches can still support publication despite a disclosed coverage gap.
If no match can be verified because access is incomplete, report an access/coverage limitation;
do not report that the whole site has no relevant product. Include the coverage summary and chosen
product links in the run result.
