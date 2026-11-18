"""Show all supported mark treatments side by side for the same chart data."""
from argparse import ArgumentParser
from pathlib import Path
import json

from chart_html import esc, svg_chart, theme_css, validate
from chart_shapes import STYLES
from compose_html import data_url, safe_json, static_svg


ROOT = Path(__file__).resolve().parents[1]


def sample_spec():
    shared = {'source': '示例数据', 'scope': '四个营运区', 'period': '2026 年 10 月', 'unit': '百万元'}
    ranking = [{'label': n, 'value': v, 'highlight': i == 0} for i, (n, v) in
               enumerate([('东区', 60), ('南区', 20), ('北区', 18), ('西区', -6)])]
    bars = dict(shared, id='rank', kind='bar', title='各区目标差额', question='哪个区离目标最远？', rows=ranking)
    columns = dict(bars, id='column', orientation='vertical')
    trend = dict(shared, id='trend', kind='line', title='六个月营业额', question='营业额何时回升？',
                 frequency='month', rows=[{'x': f'2026-{i:02d}-01', 'value': v}
                                            for i, v in enumerate([56, 68, None, 63, 77, 86], 5)])
    points = dict(shared, id='points', kind='scatter', title='租金与店均营业额', question='投入与产出怎样分布？',
                  unit='千元', x_unit='租金（千元）', y_unit='店均营业额（千元）', label_extremes=False,
                  rows=[{'label': f'门店 {i}', 'x': x, 'y': y}
                        for i, (x, y) in enumerate([(13, 54), (15, 66), (18, 61), (22, 68), (23, 74), (24, 73), (26, 84), (32, 79)], 1)])
    bridge = dict(shared, id='bridge', kind='waterfall', title='营业额增减构成', question='哪些区贡献了增量？',
                  rows=[{'label': n, 'value': v, 'role': r} for n, v, r in [
                      ('上期', 100, 'start'), ('东区', 35, 'change'), ('西区', -11, 'change'), ('本期', 124, 'total')]])
    stack = dict(shared, id='stack', kind='stacked', title='分区销售结构', question='不同渠道如何构成地区营业额？',
                 rows=[{'label':name,'parts':{'门店':own,'外送':delivery}} for name,own,delivery in [
                       ('东区',74,31),('北区',35,28),('南区',41,32)]])
    distribution = dict(shared, id='box', kind='box', title='订单等待时间分布', question='哪个时段等待更长？',
                        unit='分钟',scope='三个时段的订单样本',
                        rows=[{'label':name,'value':value} for name,values in [
                              ('早餐',[2,3,5,6,8,9]),('午餐',[3,7,8,10,11,14]),('晚餐',[3,4,6,7,9,11])]
                              for value in values])
    return {'title': '图形样式库', 'synthetic': True, 'charts': [columns, bars, trend, points, bridge, stack, distribution]}


def build(spec):
    validate(spec)
    theme = theme_css(spec.get('theme','graphite'),brand_accent=spec.get('brand_accent'))
    sections = []
    links = []
    for i, chart in enumerate(spec['charts'], 1):
        styles = STYLES.get(chart['kind'])
        if not styles:
            raise ValueError(f'{chart["kind"]} has no built-in shape set')
        family = {'bar': '竖柱' if chart.get('orientation') == 'vertical' else '横条',
                  'line': '时间序列', 'scatter': '散点', 'waterfall': '瀑布', 'stacked': '构成', 'box': '分布区间'}[chart['kind']]
        links.append(f'<a href="#chart-{i}">{esc(family)}</a>')
        choices = []
        for key, label, purpose in styles:
            styled = dict(chart, shape=key)
            svg, _ = svg_chart(styled, mobile=True)
            standalone, _ = svg_chart(styled)
            export = data_url(static_svg(standalone, theme, styled), 'image/svg+xml;charset=utf-8')
            choices.append(f'<article data-shape="{esc(key)}"><header><h3>{esc(label)}</h3>'
                           f'<p>{esc(purpose)}</p></header>{svg}<a href="{export}" download="{esc(f"chart-{i}-{key}.svg")}">下载 SVG</a></article>')
        sections.append(f'<section id="chart-{i}" class="group"><header class="group-head"><div><p>{esc(family)}</p>'
                        f'<h2>{esc(chart["title"])}</h2></div><span>{esc(chart["unit"])}</span></header>'
                        f'<div class="choices">{"".join(choices)}</div></section>')
    source = data_url(safe_json(spec),'application/json;charset=utf-8')
    template=(ROOT/'assets'/'chart-shape-gallery.html').read_text(encoding='utf-8')
    bindings={'THEME':theme,'TITLE':esc(spec['title']),'NAV':''.join(links),'SECTIONS':''.join(sections),
              'SOURCE':source,'NOTE':'示例数据' if spec.get('synthetic') else ''}
    for key,value in bindings.items():
        template=template.replace(f'@@{key}@@',value)
    return template


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'examples'/'chart-shapes'/'index.html')
    args=parser.parse_args()
    spec=json.loads(args.input.read_text(encoding='utf-8-sig')) if args.input else sample_spec()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(build(spec),encoding='utf-8',newline='\n')


if __name__=='__main__':
    main()
