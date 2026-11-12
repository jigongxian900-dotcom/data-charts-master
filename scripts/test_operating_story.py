"""Business arithmetic, unknown coverage, immutability and safe embedding tests."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_operating_story import derive, display, main, make_spec, render

SOURCE = Path(__file__).resolve().parents[1] / 'examples/operating-story/input.json'


def text_content(page):
    class Reader(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []

        def handle_data(self, data):
            self.parts.append(data)
    reader = Reader()
    reader.feed(page)
    return ''.join(reader.parts)


class OperatingStoryTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(SOURCE.read_text(encoding='utf-8-sig'))

    def test_default_arithmetic_and_original_observation_boundary(self):
        spec, d = make_spec(self.raw)
        self.assertEqual((d['prior'], d['actual'], d['change'], d['target'], d['gap']), (1080, 1271, 191, 1385, 114))
        self.assertAlmostEqual(d['growth'], 17.685185185185187)
        self.assertEqual([r['name'] for r in d['top']], ['越南', '印尼', '泰国'])
        self.assertEqual(d['top_value'], 152)
        self.assertAlmostEqual(d['top_share'], 152/191*100)
        self.assertEqual({r['name'] for r in d['risk']}, {'印尼', '新加坡'})
        self.assertEqual([r['gap'] for r in d['gaps'][:3]], [60, 20, 18])
        self.assertEqual(spec['source_data'], self.raw)
        self.assertEqual(spec['source_observation_count'], 8)
        self.assertEqual(len(spec['charts'][0]['rows']), 10)
        self.assertEqual(spec['charts'][0]['kind'], 'waterfall')

    def test_changed_names_values_and_metadata_drive_every_view(self):
        raw = copy.deepcopy(self.raw)
        raw.update(title='修改后的标题', question='本次审阅问题', period='2030年第一期对第二期', unit='万元', scope='两个演示市场', source='修改后的来源')
        raw['rows'] = [dict(id='NEW_A', name='甲市场', prior=100, revenue=120, target=130, sameStoreGrowth=-5), dict(id='NEW_B', name='乙市场', prior=50, revenue=80, target=75, sameStoreGrowth=3)]
        page, spec = render(raw)
        d = derive(raw)
        self.assertEqual((d['change'], d['gap']), (50, 5))
        self.assertEqual(d['top'][0]['name'], '乙市场')
        self.assertEqual(d['risk'][0]['name'], '甲市场')
        self.assertIn('+33.33%', page)
        self.assertIn('甲市场', page)
        for stale in ('越南', '印尼', '百万元', '2026年10月', '1,271', '17.69%'):
            self.assertNotIn(stale, page)
        for chart in spec['charts']:
            for key in ('scope', 'source', 'period'):
                self.assertEqual(chart[key], raw[key])

    def test_target_null_is_unknown_and_zero_is_real(self):
        raw = copy.deepcopy(self.raw)
        raw['rows'][0]['target'] = None
        raw['rows'][1]['target'] = 0
        spec, d = make_spec(raw)
        self.assertIsNone(d['target'])
        self.assertIsNone(d['gap'])
        self.assertEqual(d['gap_n'], 7)
        gaps = {r['label']: r['value'] for r in spec['charts'][1]['rows']}
        self.assertIsNone(gaps['越南'])
        self.assertEqual(gaps['印尼'], -340)
        self.assertIn('覆盖 7/8', spec['charts'][1]['title'])

    def test_all_targets_missing_do_not_become_zero(self):
        for row in self.raw['rows']:
            row['target'] = None
        page, spec = render(self.raw)
        self.assertTrue(all(r['value'] is None for r in spec['charts'][1]['rows']))
        self.assertIn('目标差额覆盖 0/8', page)
        self.assertIsNone(derive(self.raw)['target'])

    def test_all_zero_targets_remain_a_complete_known_total(self):
        for row in self.raw['rows']:
            row['target'] = 0
        spec, d = make_spec(self.raw)
        self.assertEqual((d['target'], d['gap'], d['gap_n']), (0, -1271, 8))
        self.assertTrue(all(r['value'] < 0 for r in spec['charts'][1]['rows']))
        self.assertNotIn('未知', spec['charts'][1]['title'])

    def test_unknown_growth_switches_to_partial_contribution_bar(self):
        self.raw['rows'][0]['prior'] = None
        self.raw['rows'][1]['revenue'] = None
        page, spec = render(self.raw)
        d = derive(self.raw)
        self.assertIsNone(d['actual'])
        self.assertIsNone(d['prior'])
        self.assertIsNone(d['change'])
        self.assertIsNone(d['growth'])
        self.assertEqual(d['growth_n'], 6)
        self.assertEqual(spec['charts'][0]['kind'], 'bar')
        self.assertEqual(len(spec['charts'][0]['rows']), 8)
        self.assertEqual(sum(r['value'] is None for r in spec['charts'][0]['rows']), 2)
        self.assertIn('6/8', page)
        self.assertNotIn('+17.69%', page)

    def test_zero_prior_does_not_create_a_rate(self):
        self.raw['rows'][0]['prior'] = 0
        spec, d = make_spec(self.raw)
        self.assertEqual(spec['charts'][0]['kind'], 'waterfall')
        self.assertEqual(d['growth_n'], 8)
        self.assertEqual(d['scatter_n'], 7)
        self.assertIsNone(spec['charts'][2]['rows'][0]['x'])
        for row in self.raw['rows']:
            row['prior'] = 0
        spec, d = make_spec(self.raw)
        self.assertIsNone(d['growth'])
        self.assertEqual(d['change'], d['actual'])
        self.assertTrue(all(r['x'] is None for r in spec['charts'][2]['rows']))

    def test_zero_actual_is_known_and_missing_same_store_stays_unknown(self):
        self.raw['rows'][0]['revenue'] = 0
        self.raw['rows'][1]['sameStoreGrowth'] = None
        spec, d = make_spec(self.raw)
        self.assertEqual(d['actual_n'], 8)
        self.assertEqual(spec['charts'][2]['rows'][0]['x'], -100)
        self.assertIsNone(spec['charts'][2]['rows'][1]['y'])
        self.assertEqual(d['scatter_n'], 7)

    def test_source_objects_and_file_are_immutable(self):
        before = SOURCE.read_bytes()
        original = copy.deepcopy(self.raw)
        render(self.raw)
        self.assertEqual(self.raw, original)
        self.assertEqual(SOURCE.read_bytes(), before)

    def test_cli_rejects_overwriting_the_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.json'
            source.write_text(json.dumps(self.raw), encoding='utf-8')
            before = source.read_bytes()
            with patch('sys.argv', ['build_operating_story.py', '--input', str(source), '--output', str(source)]):
                with self.assertRaisesRegex(ValueError, 'immutable input'):
                    main()
            self.assertEqual(source.read_bytes(), before)

    def test_rejects_invalid_types_instead_of_coercion(self):
        for key in ('prior', 'revenue', 'target', 'sameStoreGrowth'):
            for value in ('100', True, float('nan'), float('inf'), [], {}):
                with self.subTest(key=key, value=value):
                    raw = copy.deepcopy(self.raw)
                    raw['rows'][0][key] = value
                    with self.assertRaises(ValueError):
                        render(raw)
        for key in ('title', 'source', 'unit', 'period', 'scope'):
            raw = copy.deepcopy(self.raw)
            raw[key] = False
            with self.assertRaises(ValueError):
                render(raw)

    def test_script_payload_cannot_escape_into_markup(self):
        payload = '</script><img src=x onerror=alert(1)><script>'
        for key in ('title', 'question', 'source', 'scope', 'period', 'unit'):
            self.raw[key] = payload
        self.raw['rows'][0]['name'] = payload
        self.raw['rows'][0]['id'] = payload
        page, _ = render(self.raw)
        self.assertNotIn(payload, page)
        self.assertNotIn('<img src=x', page)
        self.assertIn('\\u003c/script\\u003e', page)
        self.assertIn('&lt;/script&gt;', page)

    def test_tiny_nonzero_amounts_rates_and_risk_do_not_become_zero(self):
        raw = copy.deepcopy(self.raw)
        raw.update(title='微量变化', unit='千美元', scope='两个合成市场全量；保留输入精度')
        raw['rows'] = [dict(id='MICRO-A', name='大基数微增城', prior=1000000, revenue=1000000.0001, target=1000000.0002, sameStoreGrowth=-1e-7),
                       dict(id='MICRO-B', name='小量级微增城', prior=0.001, revenue=0.0011, target=0.0012, sameStoreGrowth=1.23e-5)]
        page, spec = render(raw)
        d = derive(raw)
        self.assertEqual((d['change'], d['gap'], len(d['risk'])), (0.0002, 0.0002, 1))
        self.assertIn('净变化 +0.0002', spec['charts'][0]['title'])
        self.assertIn('距目标仍差 0.0002 千美元', spec['charts'][1]['title'])
        self.assertIn('同比 +2e-08%', spec['composition']['summary'])
        self.assertIn('大基数微增城 -1e-07%', text_content(page))
        self.assertNotIn('净变化 +0 ', page)
        self.assertNotIn('同比 +0%', page)
        self.assertNotIn('大基数微增城 0%', page)
        self.assertEqual(spec['source_data'], raw)

    def test_display_keeps_sign_and_nonzero_at_extreme_scales_without_noise(self):
        for value in (0.0002, -0.0002, 1e-7, -1e-7, 1e-200, -1e-200):
            for suffix in ('', '%'):
                with self.subTest(value=value, suffix=suffix):
                    text = display(value, suffix, signed=True)
                    parsed = float(text.removesuffix(suffix).replace(',', '')) if suffix else float(text.replace(',', ''))
                    self.assertNotEqual(parsed, 0)
                    self.assertEqual(parsed > 0, value > 0)
        self.assertEqual(display(-0.0, '%', True), '0%')
        self.assertEqual(display(0.30000000000000004), '0.3')
        self.assertEqual(display(17.685185185185187, '%', True), '+17.69%')
        self.assertEqual(display(1000000.0012), '1,000,000.0012')

    def test_risk_emphasis_uses_the_condition_not_country_ids_or_all_negatives(self):
        raw = copy.deepcopy(self.raw)
        raw['rows'] = [dict(id='CHANGED-1', name='增长同店降', prior=100, revenue=110, target=120, sameStoreGrowth=-2),
                       dict(id='CHANGED-2', name='总额同店均降', prior=100, revenue=90, target=120, sameStoreGrowth=-3),
                       dict(id='CHANGED-3', name='总额持平同店降', prior=100, revenue=100, target=120, sameStoreGrowth=-4),
                       dict(id='CHANGED-4', name='上期为零', prior=0, revenue=10, target=20, sameStoreGrowth=-5),
                       dict(id='CHANGED-5', name='同店未知', prior=100, revenue=110, target=120, sameStoreGrowth=None)]
        page, spec = render(raw)
        scatter = spec['charts'][2]
        self.assertEqual([r['label'] for r in scatter['rows'] if r['highlight']], ['增长同店降'])
        self.assertEqual(len(scatter['rows']), 5)
        self.assertFalse(scatter['label_extremes'])
        self.assertIn('增长同店降 -2%', text_content(page))
        self.assertEqual(spec['source_data'], raw)

    def test_same_store_boundary_precedes_the_plot_and_explanation_is_not_repeated(self):
        page, _ = render(self.raw)
        section = page[page.index('id="chapter-3"'):page.index('id="source-original"')]
        self.assertLess(section.index('<p class="risk-boundary">'), section.index('<figure>'))
        self.assertEqual(section.count('位置不等于原因'), 1)
        self.assertIn('◇ 标出总额增长、同店下降', section)
        self.assertIn('下载基础SVG（不含页面强调标注）', section)


if __name__ == '__main__':
    unittest.main()
