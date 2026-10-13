import copy
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load('build_theme_palette')
validator = load('validate_article')
renderer = load('verify_theme_rendering')
ARTICLE_URL = 'https://example.com/article.html'
ARTICLE_HTML = '''<style>.article-content p { color: inherit }</style>
<p>Outside article</p><article class="article-content">
<h2>First heading</h2><p>First <a href="/one">link</a></p>
<h2>Second heading</h2><h3>Subheading</h3>
<p>Second <a href="/two">link</a></p><ul><li>One</li><li>Two</li></ul>
<figure><img src="image.webp"><figcaption>Caption</figcaption></figure>
<table><thead><tr><th>A</th><th>B</th></tr></thead>
<tbody><tr><td>C</td><td>D</td></tr></tbody></table>
<blockquote><p>Callout</p></blockquote></article><h2>Outside heading</h2>'''


def evidence(brand='#FF6614', heading='#222222', body='#333333'):
    home, product = 'https://example.com/', 'https://example.com/product/'
    records = [('brand-a', brand, 'primary-accent', home, 'navigation'),
               ('brand-b', brand, 'primary-accent', product, 'category-control'),
               ('heading', heading, 'heading-text', product, 'content-heading'),
               ('body', body, 'body-text', product, 'description'),
               ('surface', '#FFFFFF', 'surface', product, 'article-surface')]
    return {'schema_version': 2, 'site_host': 'example.com', 'source_urls': [home, product],
            'evidence': [dict(id=i, color=c, role=r, url=u, component=g,
                              selector_or_element=f'.{i}', css_property='color',
                              evidence_type='computed-style') for i, c, r, u, g in records],
            'selection': dict(primary_accent=['brand-a', 'brand-b'], heading='heading',
                              body='body', surface='surface', reason='Brand controls repeat across pages; headings and body retain their native neutral colors.')}


def css_for(palette):
    style = (ROOT / 'assets/article-content-style.html').read_text()
    for token, color in palette['colors'].items():
        style = re.sub(re.escape(token) + r':\s*#[0-9A-Fa-f]{6};', token + ': ' + color + ';', style)
    return style


class SiteThemeTests(unittest.TestCase):
    def check_palette(self, palette):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'theme.json'
            p.write_text(json.dumps(palette))
            return validator.validate_site_theme(p, 'example.com', css_for(palette))[-1]

    def test_four_bright_and_dark_site_colors_remain_exact(self):
        for brand in ('#2D7A4F', '#FF6614', '#58A44E', '#FF6C28'):
            with self.subTest(brand=brand):
                p = builder.build_palette(evidence(brand))
                self.assertEqual(p['colors']['--article-accent'], brand)
                self.assertEqual(p['colors']['--article-table-header'], brand)
                self.assertGreaterEqual(builder.contrast(brand, p['colors']['--article-table-header-text']), 4.5)
                self.assertEqual(self.check_palette(p), [])

    def test_orange_fill_uses_dark_text_instead_of_becoming_brown(self):
        p = builder.build_palette(evidence())
        self.assertEqual(p['colors']['--article-table-header'], '#FF6614')
        self.assertEqual(p['colors']['--article-table-header-text'], '#222222')
        self.assertEqual(p['colors']['--article-heading'], '#222222')

    def test_old_hue_preserving_darkening_is_rejected(self):
        for token in ('--article-accent', '--article-table-header'):
            p = builder.build_palette(evidence())
            p['colors'][token] = '#AD3B00'
            self.assertTrue(any(token in error and 'role-derived' in error for error in self.check_palette(p)))

    def test_cross_site_muted_and_border_defaults_are_rejected(self):
        p = builder.build_palette(evidence())
        p['colors']['--article-muted'] = '#526058'
        p['colors']['--article-border'] = '#DCE6DE'
        errors = self.check_palette(p)
        self.assertTrue(any('--article-muted' in x for x in errors))
        self.assertTrue(any('--article-border' in x for x in errors))

    def test_a_single_button_repeated_on_two_pages_is_not_corroboration(self):
        e = evidence()
        e['evidence'][1]['component'] = 'navigation'
        with self.assertRaisesRegex(ValueError, 'two component families'):
            builder.build_palette(e)

    def test_neutral_headings_are_not_forced_to_brand_hue(self):
        p = builder.build_palette(evidence('#FF6614', '#222222'))
        self.assertEqual(self.check_palette(p), [])

    def test_unreadable_brand_link_falls_back_without_changing_brand(self):
        e = evidence()
        e['evidence'].append(dict(e['evidence'][0], id='link', role='link-text'))
        e['selection']['link'] = 'link'
        p = builder.build_palette(e)
        self.assertEqual(p['colors']['--article-link'], '#333333')
        self.assertEqual(p['token_sources']['--article-link'], ['body'])

    def test_competing_colors_and_cross_domain_evidence_fail(self):
        e = evidence()
        e['evidence'][1]['color'] = '#2D7A4F'
        with self.assertRaisesRegex(ValueError, 'competing'):
            builder.build_palette(e)
        e = evidence()
        e['source_urls'][1] = 'https://other.example/product/'
        with self.assertRaisesRegex(ValueError, 'same-site'):
            builder.build_palette(e)

    def test_extra_observed_dark_text_can_make_bright_green_header_readable(self):
        e = evidence('#58A44E', '#333333', '#333333')
        with self.assertRaisesRegex(ValueError, 'No observed text color'):
            builder.build_palette(e)
        e['evidence'].append(dict(e['evidence'][2], id='header-text', color='#222222'))
        e['selection']['table_header_text'] = 'header-text'
        p = builder.build_palette(e)
        self.assertEqual(p['colors']['--article-heading'], '#333333')
        self.assertEqual(p['colors']['--article-table-header-text'], '#222222')
        self.assertEqual(self.check_palette(p), [])

    def test_schema_v1_cannot_silently_pass_new_palette_rules(self):
        e = evidence()
        del e['schema_version']
        with self.assertRaisesRegex(ValueError, 'schema_version'):
            builder.build_palette(e)

    def rendered(self):
        p = builder.build_palette(evidence())
        counts = [('body', '', 1), ('body', 'p', 3), ('body', 'li', 2),
                  ('surface', '', 1), ('h2', 'h2', 2), ('h3', 'h3', 1),
                  ('link', 'a', 2), ('caption', 'figcaption', 1),
                  ('table-header', 'th', 2), ('table-header-text', 'th', 2),
                  ('table-body', 'td', 2), ('callout-accent', 'blockquote', 1)]
        samples = [dict(role=role, selector='.article-content' + (' ' + tag if tag else ''),
                        index=index, property=renderer.EXPECTED[role][0],
                        value=p['colors'][renderer.EXPECTED[role][1]])
                   for role, tag, count in counts for index in range(count)]
        obs = dict(site_host='example.com', phase='postpublish', url=ARTICLE_URL,
                   viewports=[dict(width=1440, samples=copy.deepcopy(samples)), dict(width=390, samples=copy.deepcopy(samples))])
        return p, obs

    def verify_rendered(self, palette, observation, content_html=ARTICLE_HTML, article_url=ARTICLE_URL):
        return renderer.verify(palette, observation, content_html, article_url)

    def test_rendered_host_override_fails_even_when_palette_is_correct(self):
        p, obs = self.rendered()
        self.assertTrue(self.verify_rendered(p, obs)['valid'])
        next(s for s in obs['viewports'][1]['samples'] if s['role'] == 'h2')['value'] = 'rgb(128, 44, 7)'
        result = self.verify_rendered(p, obs)
        self.assertFalse(result['valid'])
        self.assertIn('390px h2', result['errors'][0])

    def test_missing_mobile_and_missing_table_samples_fail(self):
        p, obs = self.rendered()
        obs['viewports'].pop()
        self.assertFalse(self.verify_rendered(p, obs)['valid'])
        p, obs = self.rendered()
        obs['viewports'][0]['samples'] = [x for x in obs['viewports'][0]['samples'] if x['role'] != 'table-body']
        self.assertFalse(self.verify_rendered(p, obs)['valid'])

    def test_rendered_other_site_and_transparent_text_fail(self):
        p, obs = self.rendered()
        obs['url'] = 'https://other.example/article.html'
        self.assertFalse(self.verify_rendered(p, obs)['valid'])
        p, obs = self.rendered()
        obs['viewports'][0]['samples'][0]['value'] = 'rgba(51, 51, 51, 0.5)'
        self.assertFalse(self.verify_rendered(p, obs)['valid'])

    def test_all_paragraphs_and_headings_must_be_sampled(self):
        for role, selector, index in [('body', '.article-content p', 2),
                                      ('body', '.article-content li', 1),
                                      ('h2', '.article-content h2', 1)]:
            with self.subTest(selector=selector):
                p, obs = self.rendered()
                obs['viewports'][0]['samples'] = [s for s in obs['viewports'][0]['samples']
                    if (s['role'], s['selector'], s['index']) != (role, selector, index)]
                result = self.verify_rendered(p, obs)
                self.assertFalse(result['valid'])
                self.assertTrue(any(f'missing {selector} indices [{index}]' in e for e in result['errors']))

    def test_outside_selectors_duplicate_indices_and_extra_elements_fail(self):
        for change in ('outside', 'duplicate', 'extra', 'missing-index'):
            with self.subTest(change=change):
                p, obs = self.rendered()
                samples = obs['viewports'][0]['samples']
                if change == 'outside':
                    samples[0]['selector'] = '#native-body'
                elif change == 'duplicate':
                    samples.append(copy.deepcopy(samples[0]))
                elif change == 'extra':
                    samples.append(dict(samples[0], index=1))
                else:
                    del samples[0]['index']
                self.assertFalse(self.verify_rendered(p, obs)['valid'])

    def test_callout_is_mandatory_only_when_present_in_content(self):
        p, obs = self.rendered()
        for v in obs['viewports']:
            v['samples'] = [s for s in v['samples'] if s['role'] != 'callout-accent']
        self.assertFalse(self.verify_rendered(p, obs)['valid'])
        without_callout = ARTICLE_HTML.replace('<blockquote><p>Callout</p></blockquote>', '')
        for v in obs['viewports']:
            v['samples'] = [s for s in v['samples']
                            if (s['role'], s['selector'], s['index']) != ('body', '.article-content p', 2)]
        self.assertTrue(self.verify_rendered(p, obs, without_callout)['valid'])

    def test_same_site_homepage_and_missing_expected_article_url_fail(self):
        p, obs = self.rendered()
        obs['url'] = 'https://example.com/'
        self.assertFalse(self.verify_rendered(p, obs)['valid'])
        p, obs = self.rendered()
        self.assertFalse(self.verify_rendered(p, obs, article_url=None)['valid'])

    def test_prepublication_uses_same_coverage_without_public_url(self):
        p, obs = self.rendered()
        obs.update(phase='prepublish', url='http://127.0.0.1:8000/preview.html')
        self.assertTrue(self.verify_rendered(p, obs, article_url=None)['valid'])

    def test_content_counts_ignore_surroundings_and_reject_duplicate_roots(self):
        p, obs = self.rendered()
        result = self.verify_rendered(p, obs)
        counts = {(c['role'], c['selector']): c['count'] for c in result['expected_samples']}
        self.assertEqual(counts[('body', '.article-content p')], 3)
        self.assertEqual(counts[('h2', '.article-content h2')], 2)
        self.assertFalse(self.verify_rendered(p, obs, ARTICLE_HTML + ARTICLE_HTML)['valid'])


if __name__ == '__main__':
    unittest.main()
