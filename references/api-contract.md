# WUZHICMS publishing API contract

## Request

Send `multipart/form-data` to:

`https://<site>/index.php?m=autocreate&f=index&v=autocreate`

Required header:

`Authorization: Bearer <webkey>`

Required text fields:

- `title`
- `seo_title1`
- `remark`
- `seo_desc`
- `content`

Required files:

- `thumb`: one WebP thumbnail
- `content_img[]`: 2–4 WebP body images

Optional but expected repeated fields:

- `content_img_alt[]`: one accurate English alt text per body image

Place `[IMAGE_BASE64]` in `content` once per body image. The server replaces each occurrence with
the next uploaded image tag. Placeholder count and body-image count must match.

The endpoint remains compatible with one legacy scalar `content_img` upload.

## Success response

```json
{
  "code": 0,
  "msg": "Success",
  "data": {
    "id": 123,
    "article_url": "https://example.com/blog/article.html",
    "thumb_path": "/uploadfile/2026/07/30/thumb.webp",
    "thumb_url": "https://example.com/uploadfile/2026/07/30/thumb.webp",
    "content_images": [
      {
        "path": "/uploadfile/2026/07/30/body-1.webp",
        "url": "https://example.com/uploadfile/2026/07/30/body-1.webp"
      }
    ],
    "created_at": "2026-07-30 14:00:00"
  }
}
```

## Errors

- `401`: missing or malformed bearer token
- `403`: invalid publishing key
- `405`: method other than POST
- `422`: missing field, invalid WebP upload, or placeholder/image-count mismatch
- `500`: server-side storage or content insertion failure

Do not retry a POST automatically when the outcome is unknown. Check the site and Sheet first.
