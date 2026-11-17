#!/usr/bin/env python3
"""Build an offline business-motion scaffold from explicit, comparable observations."""
import argparse
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def validate(data):
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    def finite_number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        try:
            return math.isfinite(value) and abs(value) <= 9007199254740991
        except OverflowError:
            return False
    def text(value, label):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{label}: nonempty text required')
        return value
    text(data.get('title'), 'title')
    text(data.get('source'), 'source')
    charts = data.get('charts')
    if not isinstance(charts, list) or not 1 <= len(charts) <= 2:
        raise ValueError('charts: one or two charts required')
    for chart in charts:
        if not isinstance(chart, dict):
            raise ValueError("chart must be object")
        if chart.get('type') not in ('ranking', 'attainment'):
            raise ValueError('type must be ranking or attainment')
        text(chart.get('title'), 'chart title')
        text(chart.get('unit'), 'unit')
        text(chart.get('definition'), 'definition')
        if chart.get('comparable') is not True:
            raise ValueError('explicit comparable=true is required; verify same metric, units and object identity')
        scale = chart.get('scale_max')
        if not finite_number(scale) or scale <= 0:
            raise ValueError('scale_max must be positive and finite')
        if chart['type'] == 'attainment' and (scale != 100 or chart['unit'] != '%'):
            raise ValueError('attainment requires percent values, unit % and scale_max 100')
        states = chart.get('states')
        if not isinstance(states, dict) or not 2 <= len(states) <= 4:
            raise ValueError('states: 2–4 named states required')
        labels = {}
        for state, records in states.items():
            text(state, 'state')
            if not isinstance(records, list) or not 1 <= len(records) <= (8 if chart['type'] == 'ranking' else 4):
                raise ValueError('each state needs 1–8 ranking or 1–4 attainment records')
            seen = set()
            for record in records:
                if not isinstance(record, dict):
                    raise ValueError('record must be object')
                key = text(record.get('id'), 'id')
                label = text(record.get('label'), 'label')
                if key in seen or (key in labels and labels[key] != label):
                    raise ValueError('IDs must be unique per state with stable label')
                seen.add(key); labels[key] = label
                value = record.get('value', 'absent')
                if value is not None and (not finite_number(value) or value < 0 or value > scale):
                    raise ValueError('value must be null or finite between 0 and scale_max')
    return data

PAGE = r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>__TITLE__</title>
<style>:root{font:16px/1.5 system-ui,'Microsoft YaHei',sans-serif;color:#173047;background:#f4f7f6}*{box-sizing:border-box}body{margin:0}main{max-width:1100px;margin:48px auto;padding:0 24px}h1{font-size:30px;line-height:1.25}h2{font-size:20px;margin:0 0 8px}.lead,.source{color:#4f6268}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,400px),1fr));gap:20px}.panel{background:white;border:1px solid #dbe6e1;border-radius:16px;padding:24px;min-width:0}.controls{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}button{font:inherit;color:#24443e;background:white;border:1px solid #a7bfb8;border-radius:24px;padding:7px 13px;cursor:pointer}button[aria-pressed=true]{background:#126557;color:white}button:focus-visible,g:focus-visible{outline:3px solid #a75e0e;outline-offset:3px}svg{width:100%;display:block}svg text{font:13px system-ui,sans-serif;fill:#193842}.axis{stroke:#d9e5e0}.status{min-height:3em;color:#4f6268;font-size:13px}.target{font-weight:650}.key,.source{font-size:13px}footer{margin-top:28px}.offscreen{position:absolute;left:-9999px}details{margin-top:16px}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:right;padding:6px;border-bottom:1px solid #dbe6e1}th:first-child,td:first-child{text-align:left}.table-scroll{overflow:auto}caption{text-align:left;padding:8px 0;color:#4f6268}@media print{button{display:none}details>div{display:block}section{break-inside:avoid}}</style></head><body><main><header><h1 id="title"></h1><p class="lead">比较范围内的对象以稳定标识对应；图形过渡值并非新增观测。</p></header><div class="grid" id="charts"></div><footer><button id="export">打印或保存</button><p class="source" id="source"></p></footer></main>
<script>__CHART_MOTION__</script><script>__RETAINED_MOTION__</script><script>
'use strict';const config=JSON.parse(__DATA__),ns='http://www.w3.org/2000/svg',instances=[];
document.querySelector('#title').textContent=config.title;document.querySelector('#source').textContent='来源：'+config.source;
function el(tag,cls,txt){const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n}
function svg(tag,attrs={}){const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));return n}
function fmt(v){return v.toLocaleString('zh-CN',{maximumSignificantDigits:8})}
function chart(cfg,idx){const panel=el('section','panel');panel.dataset.chart=String(idx);panel.append(el('h2','',cfg.title),el('p','source',cfg.definition+' · 单位：'+cfg.unit+' · 比较尺度：0–'+fmt(cfg.scale_max)));
 const controls=el('div','controls'),target=el('p','target'),status=el('p','status');status.setAttribute('role','status');panel.append(controls,target,status);
 const plot=svg('svg',{viewBox:cfg.type==='ranking'?'0 0 500 370':'0 0 500 280',role:'group','aria-label':cfg.title});panel.append(plot);let axis=svg('g'),marks=svg('g');plot.append(axis,marks);
 if(cfg.type==='ranking'){for(let i=0;i<=4;i++){let x=130+i*75;axis.append(svg('line',{x1:x,x2:x,y1:15,y2:345,class:'axis'}));let t=svg('text',{x,y:365,'text-anchor':'middle'});t.textContent=fmt(cfg.scale_max*i/4);axis.append(t)}}
 panel.append(el('p','key','颜色：保留对象为绿色，进入为橙色，退出为灰色。目标摘要始终对应目标范围。'));document.querySelector('#charts').append(panel);
 const labels=Object.create(null),scopes=Object.create(null);for(const [name,rows] of Object.entries(cfg.states)){for(const row of rows)labels[row.id]=row.label;const known=rows.filter(r=>r.value!==null);if(cfg.type==='ranking')known.sort((a,b)=>b.value-a.value||a.id.localeCompare(b.id));const ranks=new Map(known.map((r,i)=>[r.id,i]));scopes[name]=rows.map(r=>({id:r.id,x:r.value,y:r.value===null?null:ranks.get(r.id)}));}
 const names=Object.keys(scopes);
 const details=el('details'),summary=el('summary','','全部期间对照与源数据'),wrap=el('div','table-scroll'),table=el('table');details.open=true;details.append(summary,wrap);wrap.append(table);table.append(el('caption','','原始观测（不随动画插值）；未报与不在范围分开显示'));
 const head=el('thead'),hr=el('tr');hr.append(el('th','','对象'));for(const name of names)hr.append(el('th','',name+' / '+cfg.unit));head.append(hr);table.append(head);const body=el('tbody');
 for(const [id,label] of Object.entries(labels)){const tr=el('tr');tr.append(el('th','',label));for(const name of names){const row=cfg.states[name].find(r=>r.id===id);tr.append(el('td','',!row?'不在范围':row.value===null?'未报':String(row.value)))}body.append(tr)}table.append(body);panel.append(details);
 let selected=names[0],targetButton;
 for(const name of names){let b=el('button','',name);b.type='button';b.setAttribute('aria-pressed',String(name===selected));b.addEventListener('click',()=>{targetButton=b;selected=name;for(const e of controls.children)e.setAttribute('aria-pressed',String(e===b));motion.set(name)});controls.append(b)}targetButton=controls.firstChild;
 const motion=RetainedMotion.create({scopes,initial:selected,duration:650,validate:d=>{if(d.x!==null&&(d.x<0||d.x>cfg.scale_max))throw Error('scale violation')},render:f=>{
 status.textContent=f.currentValuesAreTransition?'正在切换至 '+f.target+'：图形和数字是过渡值，不是新增观测。':f.target+' · 数据已稳定';let missing=f.targetRecords.filter(d=>d.x===null).map(d=>labels[d.id]);target.textContent='目标 '+f.target+'：'+(f.targetRecords.length-missing.length)+' 项有数据'+(missing.length?'；未报 '+missing.join('、'):'');const keep=new Set();
 for(const m of f.marks){keep.add(m.id);let g=[...marks.children].find(e=>e.dataset.id===m.id);if(!g){g=svg('g',{tabindex:0});g.dataset.id=m.id;if(cfg.type==='ranking'){g.append(svg('text',{x:0,y:5}),svg('rect',{x:130,y:-10,height:20,rx:5}),svg('text',{x:438,y:5}))}else{g.append(svg('circle',{r:35,fill:'none',stroke:'#e2eeea','stroke-width':10}),svg('circle',{r:35,fill:'none','stroke-width':10,'stroke-linecap':'round',transform:'rotate(-90)'}),svg('text',{'text-anchor':'middle',y:5}),svg('text',{'text-anchor':'middle',y:61}))}marks.append(g)}
 const role={retained:'保留',entered:'进入',exited:'退出','earlier-exit':'退出'}[m.role],color=m.role==='entered'?'#bd7522':m.role==='retained'?'#167b69':'#8b9d98',value=m.x;g.style.opacity=m.opacity;g.dataset.role=m.role;g.dataset.value=value;g.setAttribute('aria-label',labels[m.id]+'，'+role+'，'+fmt(value)+cfg.unit+(f.currentValuesAreTransition?'，过渡值':''));
 if(cfg.type==='ranking'){let shift=f.currentValuesAreTransition&&m.role!=='retained'?(m.role==='entered'?1:-1)*12*Math.sin(Math.PI*f.progress):0;g.setAttribute('transform',`translate(0,${37+m.y*39+shift})`);g.children[0].textContent=labels[m.id];g.children[1].setAttribute('width',String(300*value/cfg.scale_max));g.children[1].setAttribute('fill',color);g.children[2].textContent=fmt(value)+' '+cfg.unit}else{g.setAttribute('transform',`translate(${65+(m.y%4)*120},110)`);g.children[1].setAttribute('stroke',color);g.children[1].setAttribute('stroke-dasharray',`${value/100*219.911} 219.911`);g.children[2].textContent=fmt(value)+'%';g.children[3].textContent=labels[m.id]}}
 for(const g of [...marks.children])if(!keep.has(g.dataset.id)){if(document.activeElement===g)targetButton.focus({preventScroll:true});g.remove()}
 }});instances.push(motion)}
config.charts.forEach(chart);let printDetails=[];addEventListener('beforeprint',()=>{printDetails=[...document.querySelectorAll('details')].map(d=>[d,d.open]);for(const [d] of printDetails)d.open=true});addEventListener('afterprint',()=>{for(const [d,open] of printDetails)d.open=open;printDetails=[]});document.querySelector('#export').addEventListener('click',()=>{function stable(i){return i===instances.length?window.print():instances[i].withStableFrame(()=>stable(i+1))}stable(0)});window.motionBuilder=instances;
</script></body></html>'''

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('data', type=Path); p.add_argument('output', type=Path)
    args = p.parse_args()
    try:
        data = validate(json.loads(args.data.read_text(encoding='utf-8-sig')))
        payload = json.dumps(json.dumps(data, ensure_ascii=False, separators=(',', ':')), ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        replacements = {'__TITLE__': html.escape(data['title'], quote=True), '__DATA__': payload}
        for marker, name in [('__CHART_MOTION__', 'chart-motion.js'), ('__RETAINED_MOTION__', 'retained-motion.js')]:
            source = (ROOT / 'assets' / name).read_text(encoding='utf-8')
            if '</script' in source.lower():
                raise ValueError(f'{name} contains an unsafe script terminator')
            replacements[marker] = source
        doc = re.sub(r"__TITLE__|__DATA__|__CHART_MOTION__|__RETAINED_MOTION__", lambda match: replacements[match.group()], PAGE)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(doc, encoding='utf-8')
        print(f'Created {args.output} ({len(data["charts"])} charts); verify business comparability and actual behavior.')
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        p.error(str(exc))

if __name__ == '__main__':
    main()
