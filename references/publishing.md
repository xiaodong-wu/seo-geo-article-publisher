# Spreadsheet and publishing workflow

## Spreadsheet contract

Spreadsheet ID: `1n-J4tu5IfiaVQI9496hRzlFNKLwXNQLDQY_HZAf1UmM`

Require these columns in row 1:

1. `核心关键字`
2. `目标国家`
3. `目标客户`
4. `相关产品链接`
5. `发布密钥`
6. `发布状态`
7. `发布时间`
8. `新发布文章链接`

Read metadata before values. Use exact visible tab names and tab order. Treat every tab name as the
site host. Read only bounded ranges and select the first data row whose `发布状态` is empty. Select
at most one row from each tab per invocation.

## Claiming

For a live run:

1. Generate a non-secret run ID.
2. Re-read the candidate row.
3. Write `处理中:<run-id>` to `发布状态`.
4. Re-read the status cell and continue only if the exact value remains.

For a dry-run, do not claim or update any row.

Never write the publishing key to a local file, log, command argument, or response.

## Endpoint and payload

Pass the exact bare Sheet tab domain as required `--site-host`; the publisher constructs:

`https://<tab-host>/index.php?m=autocreate&f=index&v=autocreate`

Run `python3 scripts/publish_article.py --site-host TAB_HOST --check-endpoint` during preflight.
Record its canonical `endpoint` in the row manifest and use the same `--site-host` for dry-run
and live submission. `--check-endpoint` does not read article files, request credentials, or send
HTTP. For live reachability preflight, make a credential-free GET to the returned URL with
redirects disabled and require HTTP 405 (the API is POST-only). A redirect, HTML error, or another
status does not satisfy this check; do not substitute another module or perform a test POST.

`--endpoint` is optional and serves only as an assertion, not a free-form routing override.
When supplied, quote the entire URL in shell commands. The script requires:

- HTTPS on the standard port and an exact match to `--site-host` (no implicit `www` alias).
- Exactly `/index.php` and exactly one each of `m=autocreate`, `f=index`, and `v=autocreate`.
  Parameter order may vary and is normalized; duplicate, extra, missing, empty, or encoded
  parameters are rejected, including `m=seo_article`.
- No URL credentials, fragment, whitespace, control characters, backslash, or path parameters.

An invalid route fails before reading files or credentials and before creating an HTTP session.
`--dry-run` checks the route and local payload but does not prove server reachability or permission
to publish. `--allow-http-localhost` permits HTTP and a test port only for `localhost` or
`127.0.0.1`; it never relaxes the host, path, or route checks. POST redirects are disabled to avoid
forwarding credentials or replaying a multipart request at another route. A redirect is a failure
requiring inspection under the existing retry rules, not an automatic second request.

Use an HTTPS multipart POST with:

- `Authorization: Bearer <发布密钥>`
- text fields `title`, `seo_title1`, `remark`, `seo_desc`, and `content`
- file field `thumb`
- repeated file field `content_img[]` in placeholder order
- repeated text field `content_img_alt[]` in the same order

Treat only HTTP 200 with JSON `code: 0` as API success. Require `data.article_url` or `data.url`.

## Live-page verification

Before publishing, identify the canonical same-site article listing page from the site's primary
navigation or article archive. Require HTTPS, the same host as the article, HTTP 200, and evidence
that it lists recent articles. Record this URL as `article_listing_url`; do not use a generic
homepage unless it is the site's actual article listing.

After API success, verify the article detail page:

- HTTP 200
- the exact page title appears in rendered page text
- every returned content-image path appears in the detail-page HTML
- every returned content image uses a `.webp` path
- the `responsive-v1` article style marker and `.article-content` wrapper appear in page HTML
- every color variable recorded in the row's `theme-colors.json` appears with the same value in the
  published article CSS
- no `<nav class="article-toc">` or unreplaced `[IMAGE_BASE64]` remains

Verify the returned thumbnail separately:

- resolve the returned thumbnail path against the article host
- require the thumbnail asset to return HTTP 200 with non-empty content
- require the thumbnail path to use `.webp`
- require `article_listing_url` to return HTTP 200 and contain the returned thumbnail path

Do not require the thumbnail path to appear on the article detail page. Treat the detail-page,
thumbnail-asset, and listing-page checks as one complete verification attempt. Check immediately.
If any part fails, wait 30 seconds and repeat the complete verification once. Do not submit the
article again while waiting or after the second failure.

## Sheet result states

- **Verified:** write `已发布`, current Asia/Shanghai time, and the public article URL.
- **API succeeded but both complete verification attempts failed:** write `待人工检查`, current
  time, and the returned article URL.
- **Failure before API success:** write `失败:<concise reason>`. Leave publication time and new
  article URL blank unless the API returned an article URL.

Never clear or automatically retry `失败` or `待人工检查`.

## Run report

Record non-secret source coordinates, generated artifact paths, researched URLs, validation
metrics, API status, returned article ID/URL, image paths, verification attempts, and final Sheet
state in `manifest.json`. Redact authorization headers and publishing keys.
