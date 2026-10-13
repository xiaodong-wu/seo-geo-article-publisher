#!/usr/bin/env python3
"""Build a role-based palette from current, same-site color observations."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse


def rgb(color):
    if not isinstance(color, str) or not re.fullmatch(r'#[0-9A-F]{6}', color):
        raise ValueError('Observed colors must be uppercase six-digit hex')
    return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))


def contrast(a, b):
    def luminance(color):
        c = [v / 255 for v in rgb(color)]
        c = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c]
        return sum(v * w for v, w in zip(c, (.2126, .7152, .0722)))
    x, y = sorted((luminance(a), luminance(b)))
    return (y + .05) / (x + .05)


def mix(accent, surface, weight):
    return '#' + ''.join(f'{int(a * weight + b * (1-weight) + .5):02X}'
                         for a, b in zip(rgb(accent), rgb(surface)))


def build_palette(value):
    if value.get('schema_version') != 2:
        raise ValueError('theme-colors schema_version must be 2; recollect role-based evidence')
    host = value.get('site_host', '')
    if not host or urlparse('https://' + host).netloc != host:
        raise ValueError('site_host must be a bare host')
    sources = value.get('source_urls', [])
    if len(set(sources)) < 2:
        raise ValueError('Inspect at least two distinct same-site pages')
    for url in sources:
        p = urlparse(url)
        if p.scheme != 'https' or p.netloc != host:
            raise ValueError('Every source URL must use exact same-site HTTPS')
    evidence = {}
    for item in value.get('evidence', []):
        key = item.get('id')
        if not key or key in evidence:
            raise ValueError('Evidence IDs must be present and unique')
        if item.get('url') not in sources:
            raise ValueError(f'{key}: evidence URL missing from source_urls')
        if not all(item.get(k) for k in ('selector_or_element', 'css_property', 'component', 'role')):
            raise ValueError(f'{key}: selector, property, component and role are required')
        if item.get('evidence_type') not in ('computed-style', 'stylesheet', 'logo'):
            raise ValueError(f'{key}: unsupported evidence type')
        rgb(item.get('color'))
        evidence[key] = item
    selection = value.get('selection', {})
    if len(selection.get('reason', '').strip()) < 20:
        raise ValueError('Explain the primary-versus-secondary accent and role selection')
    def select(key, roles):
        selected = evidence.get(selection.get(key))
        if selected is None or selected['role'] not in roles:
            raise ValueError(f'selection.{key} requires evidence with role {roles}')
        return selected
    primary_ids = selection.get('primary_accent', [])
    if not isinstance(primary_ids, list) or len(set(primary_ids)) < 2:
        raise ValueError('Primary accent needs two independent corroborating observations')
    primary = [evidence.get(key) for key in primary_ids]
    if any(x is None or x['role'] != 'primary-accent' for x in primary):
        raise ValueError('Primary accent references must use primary-accent evidence')
    if len({x['color'] for x in primary}) != 1:
        raise ValueError('Resolve competing brand colors; do not average them')
    if len({x['component'] for x in primary}) < 2 or len({x['url'] for x in primary}) < 2:
        raise ValueError('Primary accent must recur in two component families on two pages')
    body = select('body', {'body-text'})
    surface = select('surface', {'surface'})
    heading = select('heading', {'heading-text', 'body-text'})
    link = select('link', {'link-text', 'body-text'}) if selection.get('link') else body
    muted = select('muted', {'muted-text', 'body-text'}) if selection.get('muted') else body
    border = select('border', {'border'}) if selection.get('border') else None
    bg, accent = surface['color'], primary[0]['color']
    def readable(item, alternatives):
        for candidate in [item, *alternatives]:
            if contrast(candidate['color'], bg) >= 4.5:
                return candidate
        raise ValueError('No observed readable text color; inspect another same-site text element')
    if contrast(body['color'], bg) < 4.5:
        raise ValueError('Selected body text fails contrast; inspect an appropriate content surface')
    heading = readable(heading, [body])
    link = readable(link, [body, heading])
    muted = readable(muted, [body])
    # Change the foreground, never darken the brand fill just to retain white text.
    header_choice = select('table_header_text', {'heading-text', 'body-text', 'link-text', 'surface'}) if selection.get('table_header_text') else None
    header_candidates = ([header_choice] if header_choice else []) + [surface, heading, body, link]
    header_text = next((x for x in header_candidates
                        if contrast(x['color'], accent) >= 4.5), None)
    if header_text is None:
        raise ValueError('No observed text color contrasts with the original brand fill')
    colors = {'--article-accent': accent, '--article-heading': heading['color'],
              '--article-link': link['color'], '--article-text': body['color'],
              '--article-muted': muted['color'], '--article-surface': bg,
              '--article-table-header': accent, '--article-table-header-text': header_text['color']}
    mapping = {'--article-accent': primary_ids, '--article-table-header': primary_ids,
               '--article-heading': [heading['id']], '--article-link': [link['id']],
               '--article-text': [body['id']], '--article-muted': [muted['id']],
               '--article-surface': [surface['id']], '--article-table-header-text': [header_text['id']]}
    for token, weight in [('--article-border', .20), ('--article-soft', .04),
                          ('--article-table-stripe', .04), ('--article-table-hover', .08)]:
        if token == '--article-border' and border:
            colors[token], mapping[token] = border['color'], [border['id']]
            continue
        # Reduce only a background tint if required for body-text contrast.
        while weight > 0 and token != '--article-border' and contrast(body['color'], mix(accent, bg, weight)) < 4.5:
            weight = max(0, round(weight - .01, 2))
        colors[token] = mix(accent, bg, weight)
        mapping[token] = {'method': 'srgb-mix', 'accent': primary_ids[0],
                          'surface': surface['id'], 'accent_weight': weight}
    result = dict(value)
    result.update(colors=colors, token_sources=mapping,
                  derivation_notes='Brand accents and table fills preserve exact observed values. Text uses observed role colors with readable same-site fallbacks; only pale surfaces/borders use recorded sRGB mixes.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        palette = build_palette(json.loads(args.evidence_file.read_text()))
    except (ValueError, TypeError, KeyError) as exc:
        parser.exit(1, f'Theme evidence rejected: {exc}\n')
    args.output.write_text(json.dumps(palette, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'valid': True, 'site_host': palette['site_host'], 'colors': palette['colors']}))


if __name__ == '__main__':
    main()
