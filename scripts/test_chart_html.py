import copy
import importlib.util
import json
import math
from pathlib import Path
import re
import unittest

HERE=Path(__file__).resolve().parent
module=importlib.util.spec_from_file_location('chart_html',HERE/'chart_html.py')
chart=importlib.util.module_from_spec(module)
module.loader.exec_module(chart)


class Contracts(unittest.TestCase):
    def test_small_units_do_not_become_zero(self):
        self.assertEqual(chart.fmt(0.004), '0.004')
        self.assertEqual(chart.fmt(-0.004), '-0.004')
        self.assertEqual(chart.fmt(0), '0')
        self.assertNotEqual(chart.fmt(1e-14), '0')
        self.assertEqual(chart.fmt(1234.56789), '1,234.56789')
        self.assertEqual(chart.fmt(0.1 + 0.2, axis=True), '0.3')
        c=copy.deepcopy(self.spec['charts'][1])
        c['rows']=[{'label':'检出量','value':0.004},{'label':'真零','value':0},{'label':'负修正','value':-0.004}]
        svg,ledger=chart.svg_chart(c,True)
        self.assertIn('检出量：0.004',svg)
        self.assertIn('负修正：-0.004',svg)
        nonzero=[m for m in ledger if m['shape']=='rect' and m['value']!=0]
        self.assertTrue(all(m['width']>0 for m in nonzero))

    def test_small_units_cannot_pass_a_false_zero_claim(self):
        c=copy.deepcopy(self.spec['charts'][1])
        c['rows']=[{'label':'微量','value':1e-12}]
        c['claims']=[{'method':'sum','expected':0}]
        with self.assertRaisesRegex(ValueError,'claim'):
            chart.validate({'title':'微量核对','charts':[c]})
        c['kind']='waterfall';c.pop('claims')
        c['rows']=[{'label':'期初','value':1e-12,'role':'start'},{'label':'变动','value':0,'role':'change'},{'label':'期末','value':0,'role':'total'}]
        with self.assertRaisesRegex(ValueError,'reconcile'):
            chart.validate({'title':'微量核对','charts':[c]})

    def test_long_line_series_wraps_and_keeps_plot_space(self):
        c=copy.deepcopy(self.spec['charts'][0])
        name='地下综合设备间东侧空气处理与变配电计量单元超长系列名称'
        for row in c['rows']:row['group']=name+str(row.get('group',''))
        svg,ledger=chart.svg_chart(c,True)
        self.assertIn('地下综合设备间',svg)
        self.assertNotIn(name,svg.split('<text')[1].split('</text>')[0])
        height=float(re.search(r'viewBox="0 0 [\d.]+ ([\d.]+)"',svg).group(1))
        self.assertGreater(height,340)
        self.assertTrue(all(m['y']>80 for m in ledger if m['shape']=='point'))

    def setUp(self):
        self.spec=json.loads((HERE.parent/'examples/representative.json').read_text(encoding='utf-8'))

    def test_baseline_and_geometry(self):
        chart.validate(self.spec)
        for c in self.spec['charts']:
            for mobile in [False,True]:
                svg,ledger=chart.svg_chart(c,mobile)
                for mark in ledger:
                    if mark['shape']=='rect':
                        length=mark['width'] if mark['axis']=='x' else mark['height']
                        self.assertAlmostEqual(length,abs(mark['end']-mark['start'])*mark['scale'])
                self.assertNotIn('nan',svg.lower())

    def test_missing_and_zero_differ(self):
        svg,ledger=chart.svg_chart(self.spec['charts'][1])
        self.assertEqual(len([m for m in ledger if m['shape']=='rect']),5)
        self.assertTrue(any(m['value']==0 and m['width']==0 for m in ledger))
        self.assertIn('缺失',svg)

    def test_missing_line_is_separate_segments(self):
        svg,_=chart.svg_chart(self.spec['charts'][0])
        self.assertEqual(svg.count('<polyline'),4)
        bad=copy.deepcopy(self.spec)
        bad['charts'][0]['rows']=[r for r in bad['charts'][0]['rows'] if not (r['group']=='丙组' and r['value'] is None)]
        with self.assertRaises(ValueError):chart.validate(bad)

    def test_reconcile_before_build(self):
        self.spec['charts'][3]['rows'][-1]['value']=125
        with self.assertRaisesRegex(ValueError,'reconcile'):chart.build(self.spec)

    def test_claim_is_computed(self):
        self.spec['charts'][1]['claims'][0]['expected']=266
        with self.assertRaisesRegex(ValueError,'claim'):chart.validate(self.spec)

    def test_invalid_numeric_and_duplicates(self):
        for invalid in [True,'12',float('inf'),float('nan')]:
            bad=copy.deepcopy(self.spec)
            bad['charts'][1]['rows'][0]['value']=invalid
            with self.assertRaises(ValueError):chart.validate(bad)
        bad=copy.deepcopy(self.spec)
        bad['charts'][1]['rows'][1]['label']=bad['charts'][1]['rows'][0]['label']
        with self.assertRaises(ValueError):chart.validate(bad)

    def test_percent_no_zero_denominator(self):
        self.spec['charts'][2]['rows'][0]['parts']={'甲':0,'乙':0}
        with self.assertRaisesRegex(ValueError,'denominator'):chart.validate(self.spec)

    def test_box_preserves_outlier(self):
        svg,ledger=chart.svg_chart(self.spec['charts'][4])
        group=next(m for m in ledger if m['shape']=='box' and m['label']=='乙组')
        self.assertEqual(group['n'],8)
        self.assertEqual(group['median'],38)
        self.assertEqual(group['high'],55)
        self.assertTrue(any(m.get('value')==160 for m in ledger))

    def test_empty_zero_and_negative_data(self):
        for kind in chart.KINDS:
            c=copy.deepcopy(self.spec['charts'][0]);c['kind']=kind;c['rows']=[]
            self.assertIn('没有可绘制',chart.svg_chart(c)[0])
        c=copy.deepcopy(self.spec['charts'][1]);c.pop('claims');c['rows']=[{'label':'负数','value':-10},{'label':'零','value':0}]
        spec={'title':'陌生任务','charts':[c]};chart.validate(spec)
        _,ledger=chart.svg_chart(c)
        self.assertGreater(ledger[0]['width'],0)
        self.assertEqual(ledger[1]['width'],0)

    def test_escape_and_source_roundtrip(self):
        self.spec['title']='</script><img src=x onerror=alert(1)>'
        document=chart.build(self.spec)
        payload=re.search(r'<script id="chart-spec" type="application/json">(.*?)</script>',document,re.S).group(1)
        self.assertEqual(json.loads(payload),self.spec)
        self.assertNotIn('<img src=x',document)
        self.assertNotRegex(document,r'<script[^>]+src=|<link[^>]+href=')

    def test_foreign_domain_and_unequal_time_spacing(self):
        c=copy.deepcopy(self.spec['charts'][0]);c.update(unit='千瓦时',period='2024年2–4月',frequency='month')
        c['rows']=[{'x':'2024-02-01','value':4},{'x':'2024-03-01','value':6},{'x':'2024-04-01','value':8}]
        chart.validate({'title':'能源试验','charts':[c]})
        _,ledger=chart.svg_chart(c)
        self.assertAlmostEqual((ledger[1]['x']-ledger[0]['x'])/(ledger[2]['x']-ledger[1]['x']),29/31)


if __name__=='__main__':unittest.main()
