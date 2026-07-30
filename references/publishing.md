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

Build the endpoint from the tab host:

`https://<tab-host>/index.php?m=autocreate&f=index&v=autocreate`

Use an HTTPS multipart POST with:

- `Authorization: Bearer <发布密钥>`
- text fields `title`, `seo_title1`, `remark`, `seo_desc`, and `content`
- file field `thumb`
- repeated file field `content_img[]` in placeholder order
- repeated text field `content_img_alt[]` in the same order

Treat only HTTP 200 with JSON `code: 0` as API success. Require `data.article_url` or `data.url`.

## Live-page verification

After API success, verify:

- HTTP 200
- the exact page title appears in rendered page text
- every returned content-image path appears in the page HTML
- every returned content image uses a `.webp` path
- the `responsive-v1` article style marker and `.article-content` wrapper appear in page HTML
- every color variable recorded in the row's `theme-colors.json` appears with the same value in the
  published article CSS
- no `<nav class="article-toc">` or unreplaced `[IMAGE_BASE64]` remains

Check immediately. If verification fails, wait 30 seconds and check once more. Do not submit the
article again while waiting or after the second failure.

## Sheet result states

- **Verified:** write `已发布`, current Asia/Shanghai time, and the public article URL.
- **API succeeded but both checks failed:** write `待人工检查`, current time, and the returned
  article URL.
- **Failure before API success:** write `失败:<concise reason>`. Leave publication time and new
  article URL blank unless the API returned an article URL.

Never clear or automatically retry `失败` or `待人工检查`.

## Run report

Record non-secret source coordinates, generated artifact paths, researched URLs, validation
metrics, API status, returned article ID/URL, image paths, verification attempts, and final Sheet
state in `manifest.json`. Redact authorization headers and publishing keys.
