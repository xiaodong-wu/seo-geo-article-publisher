#!/usr/bin/env python3
"""Check browser-computed article colors, including host CSS overrides."""
import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

EXPECTED = {
    'body': ('color', '--article-text'),
    'surface': ('background-color', '--article-surface'),
    'h2': ('color', '--article-heading'),
    'h3': ('color', '--article-heading'),
    'link': ('color', '--article-link'),
    'caption': ('color', '--article-muted'),
    'table-header': ('background-color', '--article-table-header'),
    'table-header-text': ('color', '--article-table-header-text'),
    'table-body': ('color', '--article-text'),
    'callout-accent': ('border-left-color', '--article-accent'),
}

# These are exact querySelectorAll selectors; index is local to each selector.
# Body descendants are separate groups so a correctly inherited root color does
# not hide a paragraph/list rule supplied by the host stylesheet.
SELECTORS = {
    'body': ('.article-content', '.article-content p', '.article-content li'),
    'surface': ('.article-content',),
    'h2': ('.article-content h2',),
    'h3': ('.article-content h3',),
    'link': ('.article-content a',),
    'caption': ('.article-content figcaption',),
    'table-header': ('.article-content th',),
    'table-header-text': ('.article-content th',),
    'table-body': ('.article-content td',),
    'callout-accent': ('.article-content blockquote',),
}
VOID_ELEMENTS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class ArticleElementCounter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.roots = 0
        self.article_roots = 0
        self.counts = {}

    def handle_starttag(self, tag, attrs):
        inside = any(is_root for _, is_root in self.stack)
        is_root = 'article-content' in (dict(attrs).get('class') or '').split()
        if is_root:
            self.roots += 1
            self.article_roots += tag == 'article'
        if inside:
            self.counts[tag] = self.counts.get(tag, 0) + 1
        if tag not in VOID_ELEMENTS:
            self.stack.append((tag, is_root))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


def expected_sample_counts(content_html):
    """Derive the coverage contract from the final HTML, never sample claims."""
    parser = ArticleElementCounter()
    parser.feed(content_html)
    parser.close()
    if parser.roots != 1 or parser.article_roots != 1:
        raise ValueError('Content must have exactly one article.article-content root')
    return [
        {'role': role, 'selector': selector,
         'count': 1 if selector == '.article-content' else
                  parser.counts.get(selector.rsplit(' ', 1)[1], 0)}
        for role, selectors in SELECTORS.items() for selector in selectors
    ]


def hex_color(value):
    if not isinstance(value, str):
        return None
    if re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        return value.upper()
    match = re.fullmatch(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*(1(?:\.0+)?))?\s*\)', value)
    if match and all(0 <= int(c) <= 255 for c in match.group(1, 2, 3)):
        return '#' + ''.join(f'{int(c):02X}' for c in match.group(1, 2, 3))
    return None


def verify(palette, observation, content_html, article_url=None):
    errors = []
    if not isinstance(observation, dict):
        return {'valid': False, 'errors': ['Rendered evidence must be an object']}
    try:
        coverage = expected_sample_counts(content_html)
    except (TypeError, ValueError) as exc:
        return {'valid': False, 'errors': [str(exc)]}
    expected_keys = {(item['role'], item['selector'], index)
                     for item in coverage for index in range(item['count'])}
    if observation.get('site_host') != palette.get('site_host'):
        errors.append('Rendered evidence belongs to a different site')
    if observation.get('phase') not in ('prepublish', 'postpublish'):
        errors.append('phase must be prepublish or postpublish')
    if observation.get('phase') == 'postpublish':
        url = urlparse(observation.get('url', ''))
        if url.scheme != 'https' or url.netloc != palette.get('site_host'):
            errors.append('Postpublish evidence must be the same-site HTTPS article')
        if not article_url or observation.get('url') != article_url:
            errors.append('Postpublish evidence URL must exactly match the expected article_url')
    viewports = observation.get('viewports', [])
    if not isinstance(viewports, list) or any(not isinstance(v, dict) or
            not isinstance(v.get('width'), int) or isinstance(v.get('width'), bool)
            for v in viewports):
        return {'valid': False, 'errors': errors + ['Viewports must have integer widths']}
    if not any(0 < v.get('width', 0) <= 480 for v in viewports) or not any(v.get('width', 0) >= 1024 for v in viewports):
        errors.append('Capture both mobile and desktop computed styles')
    for viewport in viewports:
        samples = viewport.get('samples', [])
        if not isinstance(samples, list) or any(not isinstance(s, dict) for s in samples):
            errors.append('Rendered samples must be a list of objects')
            continue
        seen = set()
        for sample in samples:
            role = sample.get('role')
            if not isinstance(role, str) or role not in EXPECTED:
                errors.append(f'Unknown rendered role: {role}')
                continue
            prop, token = EXPECTED[role]
            selector, index = sample.get('selector'), sample.get('index')
            if selector not in SELECTORS[role] or not isinstance(index, int) or isinstance(index, bool):
                errors.append(f'{role}: use a canonical article selector and integer index')
                continue
            key = (role, selector, index)
            if key not in expected_keys:
                errors.append(f'{role}: unexpected element {selector}[{index}]')
            if key in seen:
                errors.append(f'{role}: duplicate element {selector}[{index}]')
            seen.add(key)
            if sample.get('property') != prop:
                errors.append(f'{role}: record a selector and computed {prop}')
            actual = hex_color(sample.get('value', ''))
            if actual is None or actual != palette['colors'].get(token):
                errors.append(f"{viewport.get('width')}px {role}: computed {actual} differs from {token}={palette['colors'].get(token)}")
        for item in coverage:
            missing = [index for index in range(item['count'])
                       if (item['role'], item['selector'], index) not in seen]
            if missing:
                errors.append(f"{viewport.get('width')}px {item['role']}: missing "
                              f"{item['selector']} indices {missing}")
    return {'valid': not errors, 'phase': observation.get('phase'),
            'site_host': palette.get('site_host'), 'expected_samples': coverage,
            'errors': errors}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--theme-colors-file', type=Path, required=True)
    p.add_argument('--observations-file', type=Path, required=True)
    p.add_argument('--content-file', type=Path, required=True,
                   help='Final content.html used to derive exact element coverage')
    p.add_argument('--article-url', help='Required expected public URL for postpublish evidence')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = verify(json.loads(args.theme_colors_file.read_text()),
                    json.loads(args.observations_file.read_text()),
                    args.content_file.read_text(), args.article_url)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
