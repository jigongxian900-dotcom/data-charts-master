"""Extension failures that the six built-in chart contracts cannot cover."""
import base64
import copy
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from chart_html import canonical, digest, esc, num
from compose_html import build, validate_composition
from custom_chart import CustomRenderer, RenderedChart, checked_svg


def validate_interval(chart):
    for row in chart['rows']:
        if not isinstance(row.get('label'), str) or not all(k in row and (row[k] is None or num(row[k])) for k in ['low', 'high']):
            raise ValueError('interval needs label and explicit finite low/high or null')
        if row['low'] is not None and row['high'] is not None and row['low'] > row['high']:
            raise ValueError('interval bounds reversed')


def render_interval(chart, variant, theme):
    scale = {'desktop': 10, 'mobile': 4, 'compact': 6}[variant]
    marks, ledger, coverage = [], [], []
    for index, row in enumerate(chart['rows']):
        if row['low'] is None or row['high'] is None:
            coverage.append({'row_index': index, 'status': 'missing', 'reason': '区间端点缺失'})
            continue
        x, width = row['low']*scale, (row['high']-row['low'])*scale
        marks.append(f'<rect x="{x}" y="{index*20}" width="{width}" height="10" fill="url(#tone)"/><text x="{x}" y="{index*20+15}">{esc(row["label"])}</text>')
        ledger.append({'row_index': index, 'source': copy.deepcopy(row), 'geometry': {'x': x, 'width': width}})
        coverage.append({'row_index': index, 'status': 'rendered'})
    svg = '<svg viewBox="0 0 400 150"><defs><linearGradient id="tone"><stop offset="0" stop-color="var(--accent)"/><stop offset="1" stop-color="var(--series)"/></linearGradient></defs>' + ''.join(marks) + '</svg>'
    return RenderedChart(svg, ledger, coverage, list(dict.fromkeys(k for row in chart['rows'] for k in row)), svg)


class CustomTests(unittest.TestCase):
    def setUp(self):
        self.chart = {'id': 'range', 'kind': 'interval-demo', 'title': '区间', 'question': '谁的区间更宽？',
                      'source': '独立来源 <&"', 'unit': '万元', 'period': '2026-10', 'scope': '三对象',
                      'metadata': {'preserve': ['full', None]},
                      'rows': [{'label': '</text><script>unsafe()</script>', 'low': 2, 'high': 7},
                               {'label': 'B', 'low': 1, 'high': 1, 'extra': '完整字段'},
                               {'label': 'C', 'low': None, 'high': 4}]}
        self.spec = {'title': '自定义组合', 'charts': [self.chart], 'synthetic': True, 'untouched': {'a': [1, 2]}}
        self.registry = {'interval-demo': CustomRenderer('比较区间', validate_interval, render_interval)}

    def output_ledger(self, text):
        return json.loads(re.search(r'id="chart-ledger">(.*?)</script>', text).group(1))['range']

    def exported(self, text):
        data = re.search(r'href="data:image/svg\+xml;charset=utf-8;base64,([^"]+)"', text).group(1)
        return base64.b64decode(data).decode()

    def test_no_value_field_preserves_full_source_and_coverage_not_false_missing(self):
        before = canonical(self.spec)
        for mode in ['report', 'slides']:
            output = build(self.spec, mode, renderers=self.registry)
            source = json.loads(re.search(r'id="chart-spec">(.*?)</script>', output).group(1))
            self.assertEqual(source, self.spec)
            ledger = self.output_ledger(output)
            self.assertEqual([r['status'] for r in ledger['coverage']], ['rendered', 'rendered', 'missing'])
            self.assertEqual(ledger['data_sha256'], digest(self.chart['rows']))
            self.assertEqual(set(ledger['table_fields']), {'label', 'low', 'high', 'extra'})
            self.assertIn('缺失1条', output)
            self.assertNotIn('缺失3条', output)
            self.assertIn('未提供字段', output)
            self.assertNotIn('<script>unsafe()', output)
        self.assertEqual(canonical(self.spec), before)

    def test_three_variants_recompute_geometry_and_static_export_keeps_full_metadata(self):
        output = build(self.spec, renderers=self.registry)
        ledger = self.output_ledger(output)
        self.assertEqual([ledger[v][0]['geometry']['width'] for v in ['desktop', 'mobile', 'compact']], [50, 20, 30])
        for variant in ['desktop', 'mobile', 'compact']:
            self.assertEqual(ledger[variant][0]['source'], self.chart['rows'][0])
        raw = self.exported(output)
        root = ET.fromstring(raw)
        metadata = next(node for node in root if node.tag.endswith('metadata'))
        self.assertEqual(json.loads(metadata.text), self.chart)
        self.assertEqual([float(n.get('width')) for n in root.iter() if n.tag.endswith('rect')], [50, 0])
        self.assertNotIn('var(--', raw)
        self.assertNotIn('<script', raw)
        self.assertEqual(ledger['export']['data_sha256'], digest(self.chart['rows']))
        changed = copy.deepcopy(self.spec)
        changed['charts'][0]['rows'][0]['high'] = 11
        changed_root = ET.fromstring(self.exported(build(changed, renderers=self.registry)))
        self.assertEqual(float(next(n for n in changed_root.iter() if n.tag.endswith('rect')).get('width')), 90)

    def test_ids_and_local_defs_are_isolated_across_variants(self):
        output = build(self.spec, renderers=self.registry)
        inline = output.split('<script type="application/json"')[0]
        ids = re.findall(r'<linearGradient id="([^"]+)"', inline)
        self.assertEqual(len(set(ids)), 3)
        for key in ids:
            self.assertIn('url(#' + key + ')', inline)

    def test_unknown_kind_and_invalid_registration_fail_closed(self):
        with self.assertRaises(ValueError):
            build(self.spec)
        with self.assertRaisesRegex(ValueError, 'unregistered'):
            build(self.spec, renderers={'other': self.registry['interval-demo']})
        for registry in [{'bar': self.registry['interval-demo']}, {'broken key': self.registry['interval-demo']}, {'interval-demo': render_interval}]:
            with self.subTest(registry=registry), self.assertRaises(ValueError):
                build(self.spec, renderers=registry)

    def test_author_validator_runs_and_builtin_contract_is_still_strict(self):
        self.chart['rows'][0]['high'] = -5
        with self.assertRaisesRegex(ValueError, 'reversed'):
            validate_composition(self.spec, self.registry)
        self.chart['rows'][0]['high'] = 7
        builtin = copy.deepcopy(self.chart)
        builtin.update(id='builtin', kind='bar', rows=[{'label': 'bad', 'value': float('inf')}])
        self.spec['charts'].append(builtin)
        with self.assertRaises(ValueError):
            validate_composition(self.spec, self.registry)

    def modified_renderer(self, change):
        def render(chart, variant, theme):
            result = render_interval(chart, variant, theme)
            change(result, variant)
            return result
        return {'interval-demo': CustomRenderer('测试', validate_interval, render)}

    def test_ledger_cannot_substitute_or_drop_original_source(self):
        def substitute(result, variant):
            result.ledger[0]['source']['high'] = 999
        def omit(result, variant):
            result.ledger.pop()
        for mutation in [substitute, omit]:
            with self.subTest(mutation=mutation.__name__), self.assertRaises(ValueError):
                build(self.spec, renderers=self.modified_renderer(mutation))

    def test_coverage_cannot_drop_duplicate_or_silently_exclude_a_row(self):
        def drop(result, variant):
            result.coverage.pop()
        def duplicate(result, variant):
            result.coverage[2] = copy.deepcopy(result.coverage[0])
        def unexplained(result, variant):
            result.coverage[2] = {'row_index': 2, 'status': 'excluded'}
        for mutation in [drop, duplicate, unexplained]:
            with self.subTest(mutation=mutation.__name__), self.assertRaises(ValueError):
                build(self.spec, renderers=self.modified_renderer(mutation))

    def test_table_and_cross_variant_coverage_cannot_hide_fields_or_change_status(self):
        def omit_field(result, variant):
            result.table_fields.pop()
        def alter_missing(result, variant):
            if variant == 'mobile':
                result.coverage[2]['status'] = 'excluded'
        for mutation in [omit_field, alter_missing]:
            with self.subTest(mutation=mutation.__name__), self.assertRaises(ValueError):
                build(self.spec, renderers=self.modified_renderer(mutation))

    def test_callback_input_mutations_are_rejected_and_never_touch_original(self):
        original = canonical(self.spec)
        def mutating_validator(chart):
            chart['rows'][0]['high'] = 888
        registry = {'interval-demo': CustomRenderer('测试', mutating_validator, render_interval)}
        with self.assertRaisesRegex(ValueError, 'mutated'):
            build(self.spec, renderers=registry)
        def mutating_render(chart, variant, theme):
            chart['metadata']['preserve'].append('bad')
            return render_interval(chart, variant, theme)
        registry = {'interval-demo': CustomRenderer('测试', validate_interval, mutating_render)}
        with self.assertRaisesRegex(ValueError, 'mutated'):
            build(self.spec, renderers=registry)
        self.assertEqual(canonical(self.spec), original)

    def test_unsafe_export_is_validated_even_if_inline_svg_is_safe(self):
        def active_export(result, variant):
            result.export_svg = '<svg viewBox="0 0 10 10"><script>alert(1)</script></svg>'
        with self.assertRaises(ValueError):
            build(self.spec, renderers=self.modified_renderer(active_export))

    def test_svg_safety_rejects_active_external_nonfinite_and_unknown_reference(self):
        unsafe = ['<script/>', '<foreignObject/>', '<image href="https://example.org/x"/>',
                  '<rect onclick="alert(1)"/>', '<use href="other.svg#a"/>',
                  '<rect fill="url(https://example.org/a)"/>', '<rect x="NaN"/>',
                  '<path d="M 0 0 L 1e999 0"/>', '<use href="#unknown"/>',
                  '<g id="same"/><g id="same"/>', '<animate attributeName="x"/>']
        for element in unsafe:
            with self.subTest(element=element), self.assertRaises(ValueError):
                checked_svg('<svg viewBox="0 0 10 10">' + element + '</svg>', 'test-', 'desktop')

    def test_explicit_exclusion_is_disclosed_but_original_table_and_source_remain(self):
        def exclude(result, variant):
            result.ledger = result.ledger[1:]
            result.coverage[0] = {'row_index': 0, 'status': 'excluded', 'reason': '仅作示例，排除原因 <unsafe>'}
            result.svg = re.sub(r'<rect\b[^>]*/><text\b[^>]*>.*?</text>', '', result.svg, count=1)
            result.export_svg = result.svg
        output = build(self.spec, renderers=self.modified_renderer(exclude))
        self.assertIn('排除1条', output)
        self.assertIn('&lt;unsafe&gt;', output)
        self.assertEqual(self.output_ledger(output)['coverage'][0]['status'], 'excluded')
        self.assertEqual(json.loads(re.search(r'id="chart-spec">(.*?)</script>', output).group(1)), self.spec)

    def test_all_required_provenance_fields_remain_required(self):
        for key in ['source', 'unit', 'period', 'scope', 'question']:
            spec = copy.deepcopy(self.spec)
            spec['charts'][0].pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError):
                build(spec, renderers=self.registry)

    def test_custom_claims_fail_instead_of_using_builtin_value_semantics(self):
        self.chart['claims'] = [{'method': 'sum', 'expected': 10}]
        with self.assertRaisesRegex(ValueError, 'custom claims'):
            build(self.spec, renderers=self.registry)


if __name__ == '__main__':
    unittest.main()
