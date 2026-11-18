"""Focused contract and geometry tests. Browser checks are documented separately."""
import base64
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose_html as compose


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.sources = []
        self.links = []
        self.active = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('id') == 'chart-spec':
            self.active = True
        if tag == 'a' and 'download' in attrs:
            self.links.append(attrs)

    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.sources.append(data)


class ComposeTests(unittest.TestCase):
    def test_compact_ledger_and_exports_keep_the_same_original_source(self):
        for mode in ['report','slides']:
            output=compose.build(self.spec,mode)
            self.assertEqual(output.count('<div class="compact-chart">'),6)
            ledger=json.loads(re.search(r'<script type="application/json" id="chart-ledger">(.*?)</script>',output).group(1))
            for c in self.spec['charts']:
                self.assertEqual(ledger[c['id']]['data_sha256'],compose.digest(c['rows']))
                self.assertTrue(ledger[c['id']]['compact'])
            self.assertEqual(json.loads(''.join(Document(output).sources)),self.spec)
            downloads=[a for a in Document(output).links if a['download'].endswith('.svg')]
            for c,link in zip(self.spec['charts'],downloads):
                downloaded=base64.b64decode(link['href'].split(',')[1]).decode()
                desktop,_=compose.svg_chart(c)
                self.assertEqual(downloaded,compose.static_svg(desktop,compose.theme_css('tidal'),c))
                self.assertNotIn('compact-svg',downloaded)

    def test_critical_section_context_and_closing_survive_slide_mode(self):
        spec=copy.deepcopy(self.spec)
        caveat='先变产量再变工时。顺序会改变贡献分配。这不是因果。'
        spec['composition']['sections'][0]['intro']=caveat
        spec['composition']['closing']='仅作算术核对，不作为活动净效果。'
        for mode in ['report','slides']:
            output=compose.build(spec,mode,'ruby')
            self.assertIn(caveat,output)
            self.assertIn('条输入记录',output)
            if mode=='slides':
                visible=re.sub(r'<script.*?</script>','',output,flags=re.S)
                self.assertIn(caveat,visible)
                self.assertIn('仅作算术核对，不作为活动净效果。',visible)

    def setUp(self):
        self.spec = json.loads((Path(__file__).resolve().parents[1] / 'examples/composed/source.json').read_text(encoding='utf-8'))

    def test_both_modes_roundtrip_identical_full_source_and_download(self):
        for mode in ['report', 'slides']:
            document = Document(compose.build(self.spec, mode, 'ruby'))
            self.assertEqual(json.loads(''.join(document.sources)), self.spec)
            source = next(a for a in document.links if a['download'] == 'source.json')
            self.assertEqual(json.loads(base64.b64decode(source['href'].split(',')[1])), self.spec)
            self.assertEqual(len([a for a in document.links if a['download'].endswith('.svg')]), len(self.spec['charts']))

    def test_optional_reading_layout_preserves_source_and_uses_checked_focus(self):
        brief = compose.build(self.spec, reading='brief')
        editorial = compose.build(self.spec, reading='editorial', brand_accent='#873548')
        self.assertIn('class="mode-report reading-brief"', brief)
        self.assertIn('class="mode-report reading-editorial"', editorial)
        for output in (brief, editorial):
            self.assertEqual(json.loads(''.join(Document(output).sources)), self.spec)
        self.assertIn('--accent:#873548', editorial)
        with self.assertRaisesRegex(ValueError, '4.5:1'):
            compose.build(self.spec, reading='brief', brand_accent='#E7CDB8')
        with self.assertRaisesRegex(ValueError, 'must be #RRGGBB'):
            compose.build(self.spec, brand_accent='#873548;--ink:red')
        with self.assertRaisesRegex(ValueError, 'reading requires report'):
            compose.build(self.spec, mode='slides', reading='editorial')

    def test_final_layout_keeps_source_without_builder_prose(self):
        for mode, reading in (('report', 'brief'), ('report', 'editorial'), ('slides', None)):
            output = compose.build(self.spec, mode, 'graphite', reading=reading, delivery='final')
            document = Document(output)
            self.assertEqual(json.loads(''.join(document.sources)), self.spec)
            self.assertIn('数据与口径', output)
            self.assertNotIn('本工具不生成业务结论', output)
            self.assertNotIn('数据SHA-256', output)
            self.assertEqual(len([a for a in document.links if a['download'].endswith('.svg')]), len(self.spec['charts']))

    def test_unfamiliar_changed_values_recompute_geometry_and_tables(self):
        changed = copy.deepcopy(self.spec)
        c = next(c for c in changed['charts'] if c['kind'] == 'bar')
        c['rows'][0]['value'] = 913.375
        c['claims'][0]['expected'] = sum(r['value'] for r in c['rows'] if r['value'] is not None)
        old = Document(compose.build(self.spec))
        new = Document(compose.build(changed))
        def rects(doc):
            link = next(a for a in doc.links if a['download'] == 'chart-02.svg')
            svg = ET.fromstring(base64.b64decode(link['href'].split(',')[1]))
            return [r for r in svg.iter() if r.tag.endswith('rect') and 'data-value' in r.attrib]
        before, after = rects(old), rects(new)
        self.assertEqual(float(after[0].attrib['data-value']), 913.375)
        self.assertNotEqual(before[1].attrib['width'], after[1].attrib['width'])
        html = compose.build(changed)
        self.assertIn('<td>913.375</td>', html)
        self.assertEqual(json.loads(''.join(new.sources))['charts'][1]['rows'][0]['value'], 913.375)

    def test_script_closing_and_long_text_are_inert_and_roundtrip(self):
        self.spec['title'] = '</script><script>window.UNSAFE=1</script>' + '长标题' * 60
        self.spec['charts'][0]['source'] = '"<&来源' * 80
        for mode in ['report', 'slides']:
            text = compose.build(self.spec, mode)
            doc = Document(text)
            self.assertEqual(json.loads(''.join(doc.sources)), self.spec)
            self.assertNotIn('<script>window.UNSAFE', text)
            self.assertIn('&lt;/script&gt;', text)

    def test_svg_download_is_parseable_static_and_color_resolved(self):
        doc = Document(compose.build(self.spec, theme='ruby'))
        index = 0
        for link in doc.links:
            if not link['download'].endswith('.svg'):
                continue
            raw = base64.b64decode(link['href'].split(',')[1]).decode('utf-8')
            root = ET.fromstring(raw)
            self.assertTrue(root.tag.endswith('svg'))
            metadata = next(e for e in root if e.tag.endswith('metadata'))
            self.assertEqual(json.loads(metadata.text), self.spec['charts'][index])
            index += 1
            self.assertNotIn('var(--', raw)
            self.assertNotIn('<script', raw)
            self.assertNotIn('http://', raw.replace('http://www.w3.org/2000/svg', ''))

    def test_missing_values_are_not_converted_and_invalid_claim_rejected(self):
        doc = Document(compose.build(self.spec))
        self.assertEqual(json.loads(''.join(doc.sources)), self.spec)
        self.assertIn('未替换为零', compose.build(self.spec))
        self.spec['charts'][1]['claims'][0]['expected'] = 0
        with self.assertRaisesRegex(ValueError, 'claim'):
            compose.build(self.spec)

    def test_invalid_composition_cannot_silently_drop_or_duplicate_charts(self):
        self.spec['composition']['sections'][0]['charts'].append('trend')
        with self.assertRaisesRegex(ValueError, 'exactly once'):
            compose.build(self.spec)

    def test_generic_six_kind_contract_without_narrative_is_supported(self):
        self.spec.pop('composition')
        for mode in ['report', 'slides']:
            doc = Document(compose.build(self.spec, mode))
            self.assertEqual(len([a for a in doc.links if a['download'].endswith('.svg')]), 6)


if __name__ == '__main__':
    unittest.main()
