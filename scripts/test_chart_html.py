import copy
import importlib.util
import json
import math
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
module=importlib.util.spec_from_file_location('chart_html',HERE/'chart_html.py')
chart=importlib.util.module_from_spec(module)
module.loader.exec_module(chart)


class Contracts(unittest.TestCase):
    def test_compact_common_window_is_declared_once_with_complete_group_readings(self):
        c=copy.deepcopy(self.spec['charts'][0]);c.pop('claims',None)
        c['rows']=[{'x':f'2027-0{i+1}-01','value':v,'group':name} for name,vv in [('甲',[72,90,112]),('乙',[99,95,87]),('丙',[None,78,None])] for i,v in enumerate(vv)]
        before=chart.canonical(c)
        svg,ledger=chart.svg_chart(c,compact=True)
        texts=[e.text for e in ET.fromstring(svg).iter('text')]
        self.assertEqual(sum('2027-01-01' in s for s in texts),1)
        self.assertEqual(sum('2027-03-01' in s for s in texts),1)
        for reading in ['起 72 → 末 112','起 99 → 末 87','起 缺失 → 末 缺失','起末期均缺测']:
            self.assertIn(reading,texts)
        self.assertEqual(len([m for m in ledger if m['shape']=='point']),7)
        self.assertEqual(chart.canonical(c),before)
        c['rows']=[r for r in c['rows'] if not(r['group']=='乙' and r['x']=='2027-01-01')]
        svg,_=chart.svg_chart(c,compact=True)
        self.assertNotIn('共同期间',svg)
        self.assertIn('起 2027-02-01：95',svg)

    def test_compact_readable_ticks_recompute_one_honest_scale_and_keep_extrema(self):
        for kind,expected in [('line',[60,80,100,120]),('box',[0,100,200])]:
            c=next(c for c in self.spec['charts'] if c['kind']==kind)
            values=[r['value'] for r in c['rows'] if r['value'] is not None]
            lo,hi,ticks=chart.compact_ticks(values,2 if kind=='box' else 4)
            self.assertEqual(ticks,expected)
            self.assertLessEqual(lo,min(values));self.assertGreaterEqual(hi,max(values))
            svg,ledger=chart.svg_chart(c,compact=True)
            root=ET.fromstring(svg)
            points=[m for m in ledger if m['shape']=='point']
            self.assertCountEqual([m['value'] for m in points],values)
            if kind=='line':
                grid=[float(e.attrib['y1']) for e in root.iter('line') if e.attrib.get('stroke')=='var(--rule)']
                top,bottom=min(grid),max(grid)
                for m in points:self.assertAlmostEqual(m['y'],bottom-(m['value']-lo)/(hi-lo)*(bottom-top))
            else:
                for m in points:self.assertAlmostEqual(m['x'],16+(m['value']-lo)/(hi-lo)*248)

    def test_compact_ticks_keep_tiny_nonzero_and_disambiguate_large_base_small_span(self):
        lo,hi,ticks=chart.compact_ticks([1e-14,2e-14])
        readings,note=chart.compact_tick_readings(ticks)
        self.assertTrue(all(v>0 for v in ticks))
        self.assertTrue(all(float(v)>0 for v in readings));self.assertIsNone(note)
        self.assertEqual(len(set(readings)),len(ticks))
        values=[1000000000000.001,1000000000000.0012]
        lo,hi,ticks=chart.compact_ticks(values)
        readings,note=chart.compact_tick_readings(ticks)
        self.assertEqual(len(set(ticks)),len(ticks))
        self.assertEqual(len(set(readings)),len(ticks))
        self.assertIn('1,000,000,000,000.001',note)
        self.assertEqual(readings,['0','0.0002'])
        self.assertLessEqual(lo,min(values));self.assertGreaterEqual(hi,max(values))
        c=copy.deepcopy(self.spec['charts'][0]);c.pop('claims',None)
        c['rows']=[{'x':f'2027-0{i+1}-01','value':v} for i,v in enumerate(values)]
        svg,_=chart.svg_chart(c,compact=True)
        for value in values:self.assertIn(chart.fmt(value),svg)

    def test_unbreakable_numeric_label_gets_an_explicit_readable_pan_fallback(self):
        c=copy.deepcopy(self.spec['charts'][1]);c.pop('claims',None)
        label='设备编号'+'1234567890'*6
        c['rows']=[{'label':label,'value':123456789012345678901234567890}]
        chart.validate({'title':'合法大数','charts':[c]})
        for mobile in [False,True]:
            chart.svg_chart(c,mobile)  # valid data must not be rejected by narrow layout
        svg,_=chart.svg_chart(c,compact=True)
        root=ET.fromstring(svg)
        self.assertIn('compact-wide',root.attrib['class'])
        self.assertGreater(float(root.attrib['viewBox'].split()[2]),280)
        self.assertIn('min-width:',root.attrib['style'])
        self.assertIn(label[4:],svg)
        self.assertIn('可左右滑动',chart.CSS)

    def test_compact_all_six_kinds_relayout_and_bind_raw_source(self):
        for c in self.spec['charts']:
            desktop,_=chart.svg_chart(c)
            svg,ledger=chart.svg_chart(c,compact=True)
            root=ET.fromstring(svg)
            self.assertEqual(float(root.attrib['viewBox'].split()[2]),280)
            self.assertEqual(root.attrib['data-source-sha256'],chart.digest(c['rows']))
            self.assertNotEqual(svg,desktop)
            self.assertTrue(ledger)
            width,height=map(float,root.attrib['viewBox'].split()[2:])
            for mark in ledger:
                if mark['shape']=='rect':
                    self.assertGreaterEqual(mark['x'],0)
                    self.assertLessEqual(mark['x']+mark['width'],width+.001)
                    self.assertLessEqual(mark['y']+mark['height'],height+.001)
                    length=mark['width'] if mark['axis']=='x' else mark['height']
                    self.assertAlmostEqual(length,abs(mark['end']-mark['start'])*mark['scale'])
                if mark['shape']=='point':
                    self.assertTrue(0<=mark['x']<=width and 0<=mark['y']<=height)

    def test_compact_numeric_readings_are_atomic_nonzero_and_targets_explicit(self):
        c=copy.deepcopy(self.spec['charts'][1]);c.pop('claims',None)
        c['performance_direction']='higher'
        c['rows']=[{'label':'超长中文对象标签设备计量单元东区需要完整显示','value':123456789012345,'target':123456789012345},
                   {'label':'微量','value':1e-14,'target':2e-14},
                   {'label':'未知目标','value':5,'target':None},
                   {'label':'零目标','value':8,'target':0},
                   {'label':'实际缺失','value':None,'target':20}]
        svg,ledger=chart.svg_chart(c,compact=True)
        texts=[e.text for e in ET.fromstring(svg).iter('text')]
        self.assertTrue(any('1.23457e+14' in s for s in texts))
        self.assertTrue(any('1e-14' in s for s in texts))
        self.assertIn('目标未知',texts);self.assertIn('零目标，不计算比率',texts)
        self.assertIn('实际未提供',texts)
        actual=[m for m in ledger if m['shape']=='rect']
        self.assertEqual([m['value'] for m in actual],[r['value'] for r in c['rows'] if r['value'] is not None])
        self.assertTrue(all(m['width']>0 for m in actual))
        self.assertTrue(all(float(r.attrib['width'])>0 for r in ET.fromstring(svg).iter('rect') if 'data-value' in r.attrib))
        targets=[m for m in ledger if m['shape']=='target']
        self.assertEqual([m['attainment'] for m in targets],[100,50,None,None,None])

    def test_compact_waterfall_contribution_scale_excludes_totals_and_reconciles(self):
        c=copy.deepcopy(next(c for c in self.spec['charts'] if c['kind']=='waterfall'))
        c['rows']=[{'label':'期初原标签','value':10000,'role':'start'}]+[{'label':'第'+str(i)+'项贡献','value':v,'role':'change'} for i,v in enumerate([80,-50,30,-10,25,-15,5,-5])]+[{'label':'期末原标签','value':10060,'role':'total'}]
        chart.validate({'title':'核对','charts':[c]})
        svg,ledger=chart.svg_chart(c,compact=True)
        self.assertIn('净变化 +60',svg)
        self.assertIn('共用贡献尺度',svg)
        totals=[m for m in ledger if m['shape']=='reference-total']
        self.assertEqual([m['value'] for m in totals],[10000,10060])
        changes=[m for m in ledger if m['shape']=='rect']
        self.assertEqual(len(changes),8)
        self.assertGreater(next(m['width'] for m in changes if m['value']==80),100)
        self.assertEqual(sum(m['value'] for m in changes),totals[-1]['value']-totals[0]['value'])

    def test_compact_line_values_are_whole_tokens_and_missing_ends_stay_missing(self):
        c=copy.deepcopy(self.spec['charts'][0]);c.pop('claims',None)
        c['rows']=[{'x':f'2027-0{i+1}-01','value':v,'group':'超长系列名称与实际数字不可以拆散显示'} for i,v in enumerate([72,86,98,112])]
        svg,_=chart.svg_chart(c,compact=True)
        texts=[e.text for e in ET.fromstring(svg).iter('text')]
        self.assertIn('起 72 → 末 112',texts)
        self.assertEqual(sum('2027-01-01' in s for s in texts),1)
        self.assertEqual(sum('2027-04-01' in s for s in texts),1)
        c['rows'][0]['value']=None;c['rows'][-1]['value']=None
        svg,ledger=chart.svg_chart(c,compact=True)
        self.assertIn('起末期均缺测',svg);self.assertNotIn('首尾差',svg)
        self.assertEqual(len([m for m in ledger if m['shape']=='point']),2)

    def test_line_endpoint_values_are_atomic_and_missing_ends_are_explicit(self):
        source=json.loads((HERE.parent/'examples/representative.json').read_text(encoding='utf-8'))
        c=copy.deepcopy(next(c for c in source['charts'] if c['kind']=='line'))
        c.pop('claims',None)
        c['frequency']='month'
        c['rows']=[{'x':f'2027-0{i+1}-01','value':v,'group':name} for name,values in [('甲组',[72,86,98,112]),('乙组',[99,95,90,87]),('丙组',[65,78,91,101])] for i,v in enumerate(values)]
        for mobile in [False,True]:
            svg,ledger=chart.svg_chart(c,mobile)
            readings=re.findall(r'<text[^>]*>(.*?)</text>',svg)
            for pair in ['72 → 112','99 → 87','65 → 101']:self.assertIn(pair,readings)
            self.assertEqual(len([r for r in ledger if r['shape']=='point']),12)
        c['rows']=[{'x':f'2027-0{i+1}-01','value':v} for i,v in enumerate([None,8,12,None])]
        svg,ledger=chart.svg_chart(c,True)
        self.assertIn('起末期均缺测',svg)
        self.assertNotIn('首尾差',svg)
        self.assertEqual(len([r for r in ledger if r['shape']=='point']),2)

    def test_target_reference_uses_same_scale_and_handles_undefined_ratio(self):
        spec=json.loads((HERE.parent/'examples/representative.json').read_text(encoding='utf-8'))
        c=copy.deepcopy(next(c for c in spec['charts'] if c['kind']=='bar'))
        c.pop('claims',None)
        c['performance_direction']='higher'
        c['rows']=[{'label':'达成','value':73,'target':100}, {'label':'未知目标','value':5,'target':None}, {'label':'零目标','value':8,'target':0}, {'label':'实际缺失','value':None,'target':20}]
        spec['charts']=[c]
        chart.validate(spec)
        svg,ledger=chart.svg_chart(c)
        targets=[r for r in ledger if r['shape']=='target']
        self.assertEqual(targets[0]['attainment'],73)
        self.assertTrue(all(r['attainment'] is None for r in targets[1:]))
        self.assertIn('目标 100',svg)
        self.assertIn('达成 73%',svg)
        self.assertIn('目标未知',svg)
        actual=next(r for r in ledger if r['shape']=='rect' and r['value']==73)
        self.assertAlmostEqual((targets[0]['x']-actual['x'])/actual['scale'],100)
        lower=copy.deepcopy(c)
        lower['performance_direction']='lower'
        lower['rows']=[{'label':'处理时长','value':26,'target':30}]
        reading,_=chart.svg_chart(lower)
        self.assertIn('实际/目标',reading)
        self.assertIn('达标',reading)
        self.assertNotIn('未达标',reading)
        for invalid in [True,'100',-1,float('inf')]:
            c['rows'][0]['target']=invalid
            with self.assertRaises(ValueError):chart.validate(spec)

    def test_stacks_show_component_values_without_hover(self):
        spec=json.loads((HERE.parent/'examples/representative.json').read_text(encoding='utf-8'))
        c=copy.deepcopy(next(c for c in spec['charts'] if c['kind']=='stacked'))
        c['rows']=[{'label':'来源','parts':{'搜索':41,'直接':28,'推荐':19,'邮件':12}}]
        for mobile in [False,True]:
            svg,ledger=chart.svg_chart(c,mobile)
            texts=re.findall(r'<text[^>]*>(.*?)</text>',svg)
            reading=' '.join(texts)
            for name,value in c['rows'][0]['parts'].items():self.assertIn(name+' '+str(value),reading)
            self.assertEqual(sum(r['value'] for r in ledger if r['shape']=='rect'),100)

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


    def test_large_decimal_target_gap_keeps_decimal_subtraction(self):
        c=copy.deepcopy(self.spec['charts'][1]);c.pop('claims',None)
        c['rows']=[{'label':'大额服务','value':1280000000.12,'target':1350000000}]
        for mobile,compact in [(False,False),(True,False),(True,True)]:
            svg,ledger=chart.svg_chart(c,mobile,compact=compact)
            text=''.join(ET.fromstring(svg).itertext())
            self.assertIn('69,999,999.88' if not compact else '7e+07',text)
            self.assertNotIn('88000011',text)
            if not compact:
                self.assertTrue(any('-69,999,999.88' in (node.text or '') for node in ET.fromstring(svg).iter()))
            self.assertEqual(next(m for m in ledger if m['shape']=='target')['actual'],1280000000.12)

if __name__=='__main__':unittest.main()
