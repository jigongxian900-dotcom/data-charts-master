"""One original, source-driven operating story; stdlib only, no source mutation.

This composition is a specimen, not a general business-inference engine.
"""
import argparse
import copy
from decimal import Decimal
import json
import math
from pathlib import Path
import re

from chart_html import canonical, digest, esc, fmt, require, validate
from compose_html import build, data_url


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def checked(raw):
    require(isinstance(raw, dict), 'input must be an object')
    for key in ('title', 'question', 'source', 'period', 'unit', 'scope'):
        require(isinstance(raw.get(key), str) and raw[key].strip(), key + ' must be nonempty text')
    require(isinstance(raw.get('synthetic'), bool), 'synthetic must be an explicit boolean')
    require(isinstance(raw.get('rows'), list) and raw['rows'], 'rows must be nonempty')
    ids, names = set(), set()
    for row in raw['rows']:
        require(isinstance(row, dict), 'source row must be an object')
        for key, seen in (('id', ids), ('name', names)):
            require(isinstance(row.get(key), str) and row[key].strip(), key + ' must be nonempty text')
            require(row[key] not in seen, 'duplicate ' + key)
            seen.add(row[key])
        for key in ('prior', 'revenue', 'target', 'sameStoreGrowth'):
            require(key in row, key + ' must be explicit, including null')
            value = row[key]
            require(value is None or number(value), key + ' must be a finite number or null')
            require(value is None or key == 'sameStoreGrowth' or value >= 0, key + ' must be nonnegative')
    canonical(raw)
    return copy.deepcopy(raw)


def total(values):
    return None if any(v is None for v in values) else float(sum((Decimal(str(v)) for v in values), Decimal(0)))


def diff(a, b):
    return None if a is None or b is None else float(Decimal(str(a)) - Decimal(str(b)))


def percentage(a, b):
    return None if a is None or b is None or b == 0 else a / b * 100


def display(value, suffix='', signed=False):
    if value is None:
        return '未知'
    if value == 0:
        return '0' + suffix
    # Amounts retain useful decimal precision without binary arithmetic noise.
    # Ordinary rates use two decimals; a genuinely nonzero rate that would
    # round to zero uses significant digits instead. Never print +0 or -0 for
    # a nonzero quantity, including values written in scientific notation.
    if suffix == '%':
        rounded = round(value, 2)
        shown = rounded if rounded != 0 else float(format(value, '.4g'))
    else:
        shown = float(format(value, '.12g'))
    text = fmt(shown)
    return ('+' if signed and shown > 0 else '') + text + suffix


def derive(raw):
    source = checked(raw)
    rows, n = source['rows'], len(source['rows'])
    prior = total([r['prior'] for r in rows])
    actual = total([r['revenue'] for r in rows])
    target = total([r['target'] for r in rows])
    change = diff(actual, prior)
    growth = percentage(change, prior)
    gap = diff(target, actual)
    enriched = [dict(r, contribution=diff(r['revenue'], r['prior']),
                     gap=diff(r['target'], r['revenue']),
                     growth=percentage(diff(r['revenue'], r['prior']), r['prior'])) for r in rows]
    contribution = sorted(enriched, key=lambda r: (r['contribution'] is None, -(r['contribution'] or 0), r['name']))
    gaps = sorted(enriched, key=lambda r: (r['gap'] is None, -(r['gap'] or 0), r['name']))
    valid_growth = [r for r in enriched if r['contribution'] is not None]
    valid_gap = [r for r in enriched if r['gap'] is not None]
    valid_scatter = [r for r in enriched if r['growth'] is not None and r['sameStoreGrowth'] is not None]
    risk = sorted([r for r in valid_scatter if r['growth'] > 0 and r['sameStoreGrowth'] < 0], key=lambda r: r['sameStoreGrowth'])
    same_store_negative = sorted([r for r in valid_scatter if r['sameStoreGrowth'] < 0], key=lambda r: r['sameStoreGrowth'])
    top = [r for r in contribution if r['contribution'] is not None and r['contribution'] > 0][:3]
    top_value = total([r['contribution'] for r in top]) if top else 0
    top_share = percentage(top_value, change) if change is not None and change > 0 else None
    return dict(source=source, n=n, prior=prior, actual=actual, target=target, change=change, growth=growth,
                gap=gap, rows=enriched, contribution=contribution, gaps=gaps, top=top,
                top_value=top_value, top_share=top_share, growth_n=len(valid_growth), gap_n=len(valid_gap),
                scatter_n=len(valid_scatter), risk=risk, same_store_negative=same_store_negative,
                actual_n=sum(r['revenue'] is not None for r in rows), prior_n=sum(r['prior'] is not None for r in rows),
                target_n=sum(r['target'] is not None for r in rows))


def names(rows):
    return '、'.join(r['name'] for r in rows)


def make_spec(raw):
    d = derive(raw)
    source, n = d['source'], d['n']
    complete = d['growth_n'] == n
    shared = {key: source[key] for key in ('unit', 'period', 'scope', 'source')}
    growth_title = ('营业额从 ' + display(d['prior']) + ' 到 ' + display(d['actual']) + '，净变化 ' + display(d['change'], signed=True)) if complete else f'可比记录覆盖 {d["growth_n"]}/{n}，仅展示已知贡献'
    if complete:
        bridge_rows = [{'label': '上期合计', 'value': d['prior'], 'role': 'start'}]
        bridge_rows += [{'label': r['name'], 'value': r['contribution'], 'role': 'change'} for r in d['contribution']]
        bridge_rows += [{'label': '本期合计', 'value': d['actual'], 'role': 'total'}]
    else:
        bridge_rows = [{'label': r['name'], 'value': r['contribution']} for r in d['contribution']]
    bridge = dict(shared, id='growth-contribution', kind='waterfall' if complete else 'bar', title=growth_title,
                  question='哪些市场解释了两期全量营业额的金额变化？', rows=bridge_rows, performance_direction='higher',
                  note='贡献=本期营业额−上期营业额；按贡献金额降序。起点、终点与贡献是原始市场记录的派生值，不是额外独立观测。' if complete else '仅对两期营业额均已知的市场计算贡献；缺失值保持未知。此图不能拼成完整总盘增长桥。')
    gap_title = '距目标仍差 ' + display(d['gap']) + ' ' + source['unit'] if d['gap'] is not None and d['gap'] > 0 else ('相对目标的金额差为 ' + display(d['gap']) + ' ' + source['unit'] if d['gap'] is not None else f'目标差额覆盖 {d["gap_n"]}/{n}，总盘差额未知')
    gap_chart = dict(shared, id='target-gap', kind='bar', title=gap_title,
                     question='按尚需追赶的金额排序，先核查哪些目标差额？',
                     rows=[{'label': r['name'], 'value': r['gap'], 'highlight': r['gap'] is not None and r['gap'] > 0 and r == d['gaps'][0]} for r in d['gaps']],
                     performance_direction='lower', note='差额=目标−本期营业额；正数为待追赶，负数为超额。按金额降序，未知置后。金额排序不代表投入优先级；未给定剩余时间、资源和可追回性。')
    risk_title = ('已知成对记录中，' if d['scatter_n'] < n else '') + f'{len(d["risk"])} 个市场出现总额增长、同店下降'
    scatter = dict(shared, id='growth-same-store', kind='scatter', title=risk_title,
                   question='总盘增长是否与同店表现同时改善？', unit='%', x_unit='全量营业额同比（%）', y_unit='同店指标同比（%）',
                   rows=[{'label': r['name'], 'x': r['growth'], 'y': r['sameStoreGrowth'], 'highlight': r in d['risk']} for r in d['rows']],
                   label_extremes=False,
                   note=f'有效成对记录 {d["scatter_n"]}/{n}。横轴=(本期÷上期−1)×100；上期为0或未知时不计算。纵轴沿用源字段 sameStoreGrowth，单位为%。完整数值保留在派生图表数据和原始源表中。')
    top_line = (('已知可比记录中，' if not complete else '') + f'{names(d["top"])}合计贡献 {display(d["top_value"])} {source["unit"]}') if d['top'] else '没有已知的正向金额贡献'
    if d['top_share'] is not None:
        top_line += f'，占净增量 {display(d["top_share"], "%")}'
    summary = f'本期合计 {display(d["actual"])} {source["unit"]}；同比 {display(d["growth"], "%", True)}。' + top_line + '。'
    spec = dict(title=source['title'], synthetic=source['synthetic'], theme='tidal',
                source_data=copy.deepcopy(source), source_observation_count=n,
                derivation=dict(contribution='revenue - prior', target_gap='target - revenue', total_growth='(revenue / prior - 1) * 100; prior must be positive',
                                source_sha256=digest(source), observation_note='Chart rows are derived views; only source_data.rows are original observations.'),
                charts=[bridge, gap_chart, scatter], composition=dict(subtitle=source['question'], summary=summary,
                sections=[dict(title='增长由谁贡献？', intro=top_line + '。先核对增量结构。', charts=[bridge['id']], layout='sequence'),
                          dict(title='离目标还差多少？', intro=f'实际与目标成对覆盖 {d["gap_n"]}/{n}。差额用于排查追赶金额，不替代资源决策。', charts=[gap_chart['id']], layout='feature'),
                          dict(title='增长背后，哪里需复核同店？', intro=f'总额与同店成对覆盖 {d["scatter_n"]}/{n}。◇ 标出总额增长、同店下降；其余已知市场保留为圆点。', charts=[scatter['id']], layout='sequence')],
                closing='把三件事分开处理：核对增长来源，排查目标差额，再复核同店风险。源表没有门店、订单、月度序列、成本或资源数据，不能继续推导原因和投入回报。'))
    validate(spec)
    return spec, d


STORY_CSS = r'''
body{background:#f5f3ec;color:#132e36}body>header,body>main,body>footer{max-width:1320px;padding-left:64px;padding-right:64px}.story-mast{border-top:2px solid #132e36;padding-top:18px;display:flex;justify-content:space-between;gap:16px;font-size:12px;letter-spacing:.08em}.story-mast b{color:#176b87}.story-head{display:grid;grid-template-columns:1.15fr 1fr;gap:54px;margin-top:40px}.story-head h1{font-size:clamp(36px,4.2vw,58px);line-height:1.16;margin:0 0 22px;letter-spacing:-.04em}.story-head .subtitle{font-size:18px}.hero{border-left:1px solid #b9c8c9;padding-left:34px}.hero-label{font-size:13px;color:#596974;margin:0}.hero-growth{font-size:clamp(48px,6vw,76px);font-weight:650;line-height:1.12;letter-spacing:-.055em;margin:9px 0;color:#176b87}.hero-growth small{font-size:18px;letter-spacing:0;margin-left:6px}.hero-track{display:grid;grid-template-columns:44px minmax(0,1fr) 74px;align-items:center;gap:9px;margin-top:12px;font-size:13px}.hero-track i{display:block;height:12px;background:#176b87}.hero-track.old i{background:#718a92}.hero-track strong{text-align:right;font-size:17px}.hero-caption{font-size:12px;color:#596974;margin:15px 0}.reading-line{font-size:18px;line-height:1.65;margin:27px 0 14px;max-width:1000px}.coverage{display:flex;gap:12px 26px;flex-wrap:wrap;font-size:12px;color:#596974;border-top:1px solid #ccd4d2;padding-top:16px}.disclosure{margin-top:18px;font-size:13px}.toolbar a,.toolbar button{font-size:13px}.toc{margin-top:22px}.chapter{padding-top:28px;margin-bottom:76px}.chapter-no{font-size:20px;font-weight:650}.chapter-heading{grid-template-columns:46px 1fr;gap:9px 14px;margin-bottom:24px}.chapter h2{font-size:32px;letter-spacing:-.035em}.chapter-intro{font-size:16px;max-width:970px}.chart-panel h3{font-size:23px;margin:8px 0;letter-spacing:-.02em}.chart-panel .eyebrow{font-size:11px;letter-spacing:.12em}.chart-panel .scope{font-size:12px}.chart-panel .question{font-size:14px}.chart-panel figcaption{font-size:13px;line-height:1.7}.chart-panel .provenance{font-size:12px}.chart-tools{font-size:13px}.chart-tools>a{font-size:12px}.chapter:first-child .chart-panel figure{background:#fff;padding:22px 16px 4px;border-bottom:2px solid #132e36}.chapter:first-child .chart-panel .chart-heading{max-width:none;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:0 18px}.chapter:first-child .chart-panel .chart-heading h3{grid-column:1/-1}.chapter:first-child .chart-panel .chart-heading .question{grid-column:1}.chapter:first-child .chart-panel .chart-heading .scope{grid-column:2}.chapter:nth-child(2){background:#eaf0ee;padding:26px 26px 20px;margin-left:-26px;margin-right:-26px;border-top:2px solid #176b87}.chapter:nth-child(2) .chart-panel{grid-template-columns:minmax(210px,1fr) minmax(0,2.3fr);column-gap:40px}.chapter:nth-child(2) .chart-heading{padding-top:22px}.evidence-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;margin:24px 0 0;border-top:1px solid #cbd5d3;padding-top:18px}.evidence-strip p{margin:0;font-size:13px;line-height:1.6}.evidence-strip b{display:block;font-size:19px;font-weight:600;color:#176b87;margin-bottom:7px}.evidence-note{border-left:3px solid #b83d45;padding-left:16px;margin-top:22px;font-size:15px;max-width:900px}.chapter:nth-child(3) .chart-group{display:grid;grid-template-columns:minmax(0,2.15fr) minmax(230px,1fr);column-gap:38px}.chapter:nth-child(3) .chart-panel{grid-column:1}.chapter:nth-child(3) .evidence-note{grid-column:2;align-self:start;margin-top:74px}.chapter:nth-child(3) .chart-panel figure{margin-top:25px}.source-original{margin-top:34px;border-top:1px solid #132e36;padding-top:22px}.source-original h2{font-size:21px}.source-original p{font-size:13px}.source-original table{font-size:13px}.source-original td,.source-original th{white-space:normal;min-width:95px}.source-original td:first-child,.source-original th:first-child{min-width:110px}.closing{font-size:19px}.digest{font-size:11px}.mode-report .chart-panel .source-table summary{font-size:13px}.story-scope{font-size:12px;color:#596974;max-width:1020px}.story-head p,.story-head h1{overflow-wrap:anywhere}svg{max-width:100%}
@media(max-width:1000px){body>header,body>main,body>footer{padding-left:34px;padding-right:34px}.story-head{gap:30px}.chapter:nth-child(3) .chart-group{display:block}.chapter:nth-child(3) .evidence-note{margin-top:24px}.hero{padding-left:24px}}
@media(max-width:700px){body>header,body>main,body>footer{padding-left:20px;padding-right:20px}.story-mast{font-size:10px}.story-head{display:block;margin-top:28px}.story-head h1{font-size:37px;max-width:530px}.story-head .subtitle{font-size:16px}.hero{border-left:0;border-top:1px solid #b9c8c9;margin-top:28px;padding:24px 0 0}.hero-growth{font-size:62px}.hero-track{grid-template-columns:42px minmax(0,1fr) 70px}.reading-line{font-size:16px;margin-top:24px}.coverage{gap:8px 14px}.chapter h2{font-size:26px}.chapter-heading{grid-template-columns:34px 1fr;gap:8px}.chapter-intro{font-size:15px}.chapter{margin-bottom:48px}.chapter:first-child .chart-panel .chart-heading{display:block}.chapter:first-child .chart-panel figure{padding:16px 5px 3px}.chart-panel h3{font-size:22px}.chapter:nth-child(2){margin-left:-8px;margin-right:-8px;padding:22px 8px 16px}.chapter:nth-child(2) .chart-heading{padding-top:0}.chapter:nth-child(2) .chart-panel{display:block}.evidence-strip{display:block;margin-top:18px;padding-top:4px}.evidence-strip p{padding-top:15px}.evidence-strip b{font-size:18px;margin-bottom:3px}.evidence-note{font-size:14px}.source-original h2{font-size:20px}.toolbar{gap:12px}.toolbar button{max-width:100%}.toc a{font-size:13px}.source-original .table-scroll{max-height:390px}.source-original td,.source-original th{min-width:90px}.hero-caption{font-size:12px}.closing{font-size:17px}}
@media(max-width:350px){body>header,body>main,body>footer{padding-left:16px;padding-right:16px}.story-head h1{font-size:32px}.hero-growth{font-size:54px}.hero-growth small{font-size:16px}.story-mast{letter-spacing:0}.chapter h2{font-size:24px}}
.hero-track{grid-template-columns:44px minmax(0,1fr) auto}.hero-track strong{width:var(--story-amount-width);min-width:0;max-width:45vw;overflow-wrap:anywhere}.story-svg-pan{overflow-x:auto;max-width:100%;overscroll-behavior-x:contain}
.chapter:nth-child(3) .chart-panel{grid-row:1}.chapter:nth-child(3) .evidence-note{grid-row:1;margin-top:0}.evidence-note p{margin:0 0 12px}.evidence-note p:last-child{margin-bottom:0}.risk-boundary{font-size:13px;color:var(--muted)}svg .story-risk-label{font-size:14px;font-weight:700;fill:var(--ink);paint-order:stroke;stroke:var(--bg);stroke-width:4px;stroke-linejoin:round}.story-risk-marker,.story-risk-leader{fill:none;stroke:var(--ink);stroke-width:1.5;vector-effect:non-scaling-stroke}
.story-number{white-space:nowrap}
@media(max-width:1000px){.chapter:nth-child(3) .evidence-note{margin:0 0 24px}}
@media print{.story-head{display:grid}.hero-growth{font-size:52px}.source-original .table-scroll{max-height:none}.source-original{break-before:page}.evidence-strip{display:grid}.chapter:nth-child(3) .chart-group{display:block}}
'''


STORY_FIT_JS = r'''
// This specimen directly names only the calculated risk-condition points.
// Original circles, their coordinates, all other markets and both scales stay.
function decorateStoryRisk(){
 const spec=JSON.parse(document.getElementById('chart-spec').textContent);
 const chart=spec.charts.find(c=>c.id==='growth-same-store');
 const rows=chart.rows.filter(r=>r.x!==null&&r.y!==null),ns='http://www.w3.org/2000/svg';
 for(const svg of document.querySelectorAll('[data-chart-id="growth-same-store"] svg')){
  if(!svg.getClientRects().length||getComputedStyle(svg).display==='none'||svg.dataset.storyRiskAnnotated)continue;
  const points=[...svg.querySelectorAll('circle[role="img"]')];
  if(points.length!==rows.length)continue;
  const risks=rows.map((row,i)=>({row,point:points[i]})).filter(p=>p.row.highlight);
  // Replace the helper's repeated risk-name lists/direct labels with one
  // direct label per risk point. Full numeric rows remain in the data table.
  for(const text of [...svg.querySelectorAll('text')]){
   if(risks.some(p=>text.textContent===('重点：'+p.row.label))){
    const next=text.nextElementSibling;if(next&&next.tagName==='text'&&next.classList.contains('value'))next.remove();text.remove();
   }else if(risks.some(p=>text.textContent.startsWith(p.row.label+' · ')))text.remove();
  }
  if(svg.classList.contains('compact-svg')){
   const box=svg.getBBox(),v=svg.viewBox.baseVal;
   svg.setAttribute('viewBox',`${v.x} ${v.y} ${v.width} ${Math.max(80,box.y+box.height+12-v.y)}`);
  }
  const v=svg.viewBox.baseVal,occupied=[...svg.querySelectorAll('text')].map(t=>t.getBBox());
  const coordinates=points.map(p=>({x:Number(p.getAttribute('cx')),y:Number(p.getAttribute('cy'))}));
  const group=document.createElementNS(ns,'g');group.setAttribute('class','story-risk-decorations');svg.append(group);
  const overlaps=(a,b)=>a.x<b.x+b.width+3&&a.x+a.width+3>b.x&&a.y<b.y+b.height+3&&a.y+a.height+3>b.y;
  for(const {row,point} of risks){
   const x=Number(point.getAttribute('cx')),y=Number(point.getAttribute('cy'));
   const marker=document.createElementNS(ns,'path');marker.setAttribute('class','story-risk-marker');marker.setAttribute('d',`M ${x} ${y-8} L ${x+8} ${y} L ${x} ${y+8} L ${x-8} ${y} Z`);marker.setAttribute('aria-hidden','true');group.append(marker);
   const text=document.createElementNS(ns,'text');text.setAttribute('class','story-risk-label');text.dataset.riskLabel=row.label;text.textContent=row.label;group.append(text);
   const candidates=[[x+13,y-11,'start'],[x+13,y+23,'start'],[x-13,y-11,'end'],[x-13,y+23,'end'],[x,y-19,'middle'],[x,y+30,'middle']];
   let chosen=null;
   for(const [tx,ty,anchor] of candidates){
    text.setAttribute('x',tx);text.setAttribute('y',ty);text.setAttribute('text-anchor',anchor);const b=text.getBBox();
    const inside=b.x>=v.x+6&&b.x+b.width<=v.x+v.width-6&&b.y>=v.y+6&&b.y+b.height<=v.y+v.height-6;
    const hitsText=occupied.some(a=>overlaps(b,a)),hitsPoint=coordinates.some(p=>p.x>b.x-8&&p.x<b.x+b.width+8&&p.y>b.y-8&&p.y<b.y+b.height+8);
    if(inside&&!hitsText&&!hitsPoint){chosen={tx,ty,anchor,b};break;}
   }
   if(!chosen){
    // Crowded/long names use a real extra label gutter. The local canvas
    // padding/pan below retains the font floor instead of covering a point.
    const tx=v.x+v.width+18;let ty=y-11;text.setAttribute('x',tx);text.setAttribute('text-anchor','start');text.setAttribute('y',ty);let b=text.getBBox(),hit;
    while((hit=occupied.find(a=>overlaps(b,a)))){ty=hit.y+hit.height+b.height+6;text.setAttribute('y',ty);b=text.getBBox();}
    chosen={tx,ty,anchor:'start',b};
   }
   occupied.push(chosen.b);
   const leader=document.createElementNS(ns,'path'),endX=chosen.anchor==='end'?chosen.b.x+chosen.b.width:chosen.anchor==='middle'?chosen.tx:chosen.b.x;
   leader.setAttribute('class','story-risk-leader');leader.setAttribute('d',`M ${x} ${y} L ${endX} ${chosen.b.y+chosen.b.height/2}`);leader.setAttribute('aria-hidden','true');group.insertBefore(leader,text);
  }
  svg.dataset.storyRiskAnnotated='true';
 }
}
// Specimen-local label padding, not an engine-wide geometry correction.
// Preserve a 12px rendered-text floor via a local pan if a wider canvas needs it.
function fitStoryLabels(){
 for(const svg of document.querySelectorAll('.chart-panel svg')){
  if(!svg.getClientRects().length||getComputedStyle(svg).display==='none')continue;
  const original=(svg.dataset.storyOriginalViewbox||svg.getAttribute('viewBox'));
  svg.dataset.storyOriginalViewbox=original;
  const [x,y,w,h]=original.split(/\s+/).map(Number),texts=[...svg.querySelectorAll('text')];
  let left=x,top=y,right=x+w,bottom=y+h,minFont=Infinity;
  for(const text of texts){const b=text.getBBox();left=Math.min(left,b.x-4);top=Math.min(top,b.y-4);right=Math.max(right,b.x+b.width+4);bottom=Math.max(bottom,b.y+b.height+4);minFont=Math.min(minFont,parseFloat(getComputedStyle(text).fontSize));}
  if(left<x||top<y||right>x+w||bottom>y+h){
   const width=right-left;svg.setAttribute('viewBox',`${left} ${top} ${width} ${bottom-top}`);
   if(Number.isFinite(minFont)&&minFont>0){svg.style.minWidth=Math.ceil(width*12/minFont)+'px';svg.parentElement.classList.add('story-svg-pan');}
   svg.dataset.storyLabelPadding='local-adaptation';
  }
 }
}
const storyPrintMedia=matchMedia('print'),storyScreenGeometry=new Map();
const storyGeometryAttributes=['viewBox','style','data-story-original-viewbox','data-story-label-padding'];
function syncStoryRendering(){
 decorateStoryRisk();fitStoryLabels();
 if(!storyPrintMedia.matches)for(const svg of document.querySelectorAll('.chart-panel svg')){
  if(!svg.getClientRects().length||getComputedStyle(svg).display==='none')continue;
  storyScreenGeometry.set(svg,{attributes:storyGeometryAttributes.map(name=>[name,svg.getAttribute(name)]),pan:svg.parentElement.classList.contains('story-svg-pan')});
 }
}
syncStoryRendering();addEventListener('resize',syncStoryRendering);
// Printing can switch from a compact screen SVG to a previously hidden
// desktop SVG without a resize. Synchronize immediately after that media
// switch; never measure hidden geometry or defer work beyond PDF capture.
function syncPrintedStory(){if(storyPrintMedia.matches){decorateStoryRisk();fitStoryLabels()}}
function restoreScreenStory(){
 if(storyPrintMedia.matches)return;
 for(const [svg,state] of storyScreenGeometry){
  for(const [name,value] of state.attributes){if(value===null)svg.removeAttribute(name);else svg.setAttribute(name,value);}
  svg.parentElement.classList.toggle('story-svg-pan',state.pan);
 }
}
addEventListener('beforeprint',syncPrintedStory);
storyPrintMedia.addEventListener('change',event=>{if(event.matches)syncPrintedStory();else restoreScreenStory()});
addEventListener('afterprint',restoreScreenStory);
'''


def render(raw):
    spec, d = make_spec(raw)
    page = build(spec, mode='report')
    source, n = d['source'], d['n']
    hero_rate = display(d['growth'], '%', True)
    maximum = max([v for v in (d['actual'], d['prior']) if v is not None] + [1])
    tracks = ''
    for key, label in (('prior', '上期'), ('actual', '本期')):
        value = d[key]
        bar = '<i style="width:' + str(value / maximum * 100) + '%"></i>' if value is not None else '<span>合计未知</span>'
        tracks += f'<div class="hero-track {"old" if key == "prior" else ""}"><span>{label}</span><div>{bar}</div><strong>{esc(display(value))}</strong></div>'
    disclosure = '合成演示数据；不是实际经营事实。' if source['synthetic'] else '按所提供源表计算；来源与范围见下。'
    raw_download = data_url(canonical(source), 'application/json;charset=utf-8')
    spec_download = data_url(canonical(spec), 'application/json;charset=utf-8')
    header = f'''<header><div class="story-mast"><b>OPERATING NOTES / 01</b><span>{n} 个市场 · 一组原始记录</span></div><div class="story-head"><div><h1>{esc(source['title'])}</h1><p class="subtitle">{esc(source['question'])}</p></div><div class="hero"><p class="hero-label">全量营业额同比 · 金额单位 {esc(source['unit'])}</p><p class="hero-growth">{esc(hero_rate)}</p>{tracks}<p class="hero-caption">两条长度共用零基线。净变化 {esc(display(d['change'], signed=True))} {esc(source['unit'])}；上期为零或数据不全时，同比保持未知。</p></div></div><p class="reading-line">{esc(spec['composition']['summary'])}</p><div class="coverage"><span>两期可比 {d['growth_n']}/{n}</span><span>实际与目标成对 {d['gap_n']}/{n}</span><span>增长与同店成对 {d['scatter_n']}/{n}</span><span>本期已知 {d['actual_n']}/{n} · 上期已知 {d['prior_n']}/{n} · 目标已知 {d['target_n']}/{n}</span></div><p class="disclosure">{disclosure}</p><p class="story-scope">期间：{esc(source['period'])}<br>范围：{esc(source['scope'])}<br>来源：{esc(source['source'])}</p><div class="toolbar"><a href="{raw_download}" download="operating-source.json">下载完整原始源表</a><a href="{spec_download}" download="operating-derived-spec.json">下载派生图表契约</a><button type="button" data-print>打印全部 / 另存PDF</button></div><nav class="toc" aria-label="章节"><a href="#chapter-1">01 增长贡献</a><a href="#chapter-2">02 目标差额</a><a href="#chapter-3">03 同店复核</a><a href="#source-original">原始源表与边界</a></nav></header>'''
    # Both rows need the same number-column width, so digit counts cannot
    # change the available bar length and distort their shared amount scale.
    amount_chars = max(4, *(len(display(d[key])) + 1 for key in ('prior', 'actual')))
    header = header.replace('<div class="hero">', f'<div class="hero" style="--story-amount-width:{amount_chars}ch">', 1)
    page = re.sub(r'<header>.*?</header>', lambda _: header, page, count=1, flags=re.S)
    notes = []
    top = d['top']
    if top:
        ranking_label = ('前三项正向贡献' if len(top) == 3 else f'前 {len(top)} 项正向贡献')
        if d['growth_n'] < n:
            ranking_label = '已知记录中，' + ranking_label
        notes.append((ranking_label, names(top) + '：' + display(d['top_value']) + ' ' + source['unit'] + ('；占净增量 ' + display(d['top_share'], '%') if d['top_share'] is not None else '；净增量未知或非正，不计算占比') + '。'))
    else:
        notes.append(('正向贡献未知或不存在', '仅根据已知两期金额识别，不以缺失值代替零。'))
    negatives = [r for r in d['contribution'] if r['contribution'] is not None and r['contribution'] < 0]
    notes.append(('负向贡献 ' + str(len(negatives)) + ' 项', names(negatives) + '合计 ' + display(total([r['contribution'] for r in negatives]), signed=True) + ' ' + source['unit'] + '。' if negatives else '已知两期金额中没有负向贡献；未知记录不在此判断内。'))
    notes.append(('覆盖 ' + str(d['growth_n']) + '/' + str(n), '完整两期金额才计算总盘变化；贡献桥是金额恒等式，不能证明变化原因。'))
    strip = '<div class="evidence-strip">' + ''.join(f'<p><b>{esc(t)}</b>{esc(b)}</p>' for t, b in notes) + '</div>'
    chapter_end = '</div></section>'
    pos = page.index(chapter_end, page.index('id="chapter-1"'))
    page = page[:pos] + '</div>' + strip + '</section>' + page[pos + len(chapter_end):]
    risk_readings = '；'.join(esc(r['name']) + ' <span class="story-number">' + esc(display(r['sameStoreGrowth'], '%', True)) + '</span>' for r in d['risk'])
    risk_note = ('待复核的同店指标：' + risk_readings + '。') if d['risk'] else '已知成对记录中，未发现总额增长且同店下降。'
    boundary = '同店指标的分母和门店样本未附明细，不能确认是营业额还是日店均。位置不等于原因；先核对口径与样本。'
    note = f'<aside class="evidence-note"><p>{risk_note}</p><p class="risk-boundary">{esc(boundary)}</p></aside>'
    pos = page.index('<div class="chart-group">', page.index('id="chapter-3"')) + len('<div class="chart-group">')
    page = page[:pos] + note + page[pos:]
    headers = ['市场ID', '市场', '上期营业额', '本期营业额', '目标', '同店指标同比（%）']
    fields = ['id', 'name', 'prior', 'revenue', 'target', 'sameStoreGrowth']
    table = '<section class="source-original" id="source-original"><h2>只保留这一组原始记录</h2><p>下面是输入源表；图中起点、终点、贡献、差额和增长率均由它计算。派生图行数不代表原始样本数。null 为未知，0 为已知零值。原始同店字段未附指标定义和门店明细，不推导其分母。</p><div class="table-scroll" tabindex="0" role="region" aria-label="原始市场源表，可横向滚动"><table><caption>' + esc(source['period'] + ' · 金额单位：' + source['unit'] + '；sameStoreGrowth 单位：%') + '</caption><thead><tr>' + ''.join('<th scope="col">' + esc(h) + '</th>' for h in headers) + '</tr></thead><tbody>'
    table += ''.join('<tr>' + ''.join('<td>' + esc('未知（null）' if r[k] is None else fmt(r[k])) + '</td>' for k in fields) + '</tr>' for r in source['rows'])
    table += '</tbody></table></div><p>来源：' + esc(source['source']) + '<br>范围：' + esc(source['scope']) + '</p><p class="digest">原始源表 SHA-256：' + digest(source) + '</p></section>'
    page = page.replace('</main>', table + '</main>', 1)
    # The SVG file is the helper's base export. Page-only risk annotations
    # must not be represented as part of that downloadable static artifact.
    page = re.sub(r'(<article\b[^>]*data-chart-id="growth-same-store".*?</article>)',
                  lambda m: m[0].replace('下载静态SVG', '下载基础SVG（不含页面强调标注）', 1), page, count=1, flags=re.S)
    page = re.sub(r'同源数据 · (\d+)条', r'派生图表数据 · \1行', page)
    page = page.replace('</style>', STORY_CSS + '</style>', 1)
    page = page.replace('</body>', '<script>' + STORY_FIT_JS + '</script></body>', 1)
    page = page.replace('图表、表格、SVG与源数据来自同一份输入。输入中的标题和解释由作者提供；本工具不生成业务结论。', '此示例的标题、覆盖率与金额结论由源表计算；解释边界由示例作者明确。图表、表格与下载来自同一输入。')
    return page, spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).resolve().parents[1] / 'examples/operating-story/input.json')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'examples/operating-story/report.html')
    args = parser.parse_args()
    require(args.input.resolve() != args.output.resolve(), 'output must not overwrite the immutable input source')
    raw = json.loads(args.input.read_text(encoding='utf-8-sig'))
    page, spec = render(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page, encoding='utf-8', newline='\n')
    print(canonical(dict(output=str(args.output), source_observations=len(raw['rows']), charts=len(spec['charts']), source_sha256=digest(raw), spec_sha256=digest(spec))))


if __name__ == '__main__':
    main()
