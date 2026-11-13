"""Offline, standard-library rebuild. Run: uv run --no-project python producer.py.
Input defaults to ./source; --input-dir and --out can relocate the package.
--skill-root verifies the recorded candidate skill files when supplied.
"""
from pathlib import Path
import argparse, csv, json, hashlib, html, base64
from datetime import date

HERE = Path(__file__).resolve().parent
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def esc(x): return html.escape(str(x))
def dump(p, obj): p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8',newline='\r\n')

def chart(rows, mobile=False):
    w,h = (340,680) if mobile else (1020,420)
    x0,x1 = (24,306) if mobile else (190,700)
    ys = [155,295,435] if mobile else [157,235,313]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="成熟批次按期续订率，含分子分母和未按期续订人数" viewBox="0 0 {w} {h}">',
       f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
       '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif;fill:#192e39} .muted{fill:#506470}</style>',
       '<text x="24" y="30" font-size="18" font-weight="700">成熟批次：按期续订率</text>',
       '<text x="24" y="58" font-size="14" class="muted">合成数据 · 截止 2026-11-12</text>']
    if not mobile:
        parts += ['<text x="190" y="92" font-size="14" class="muted">按期续订率</text>', '<text x="790" y="92" font-size="14" class="muted">未按期续订</text>', '<text x="900" y="92" font-size="14" class="muted">按期 / 已到期</text>']
    for t in [0,25,50,75,100]:
        x = x0 + (x1-x0)*t/100
        if not mobile: parts += [f'<line x1="{x}" y1="125" x2="{x}" y2="330" stroke="#e4e9eb"/>',f'<text x="{x}" y="118" text-anchor="middle" font-size="13">{t}%</text>']
    for r,y in zip(rows,ys):
        col = '#a83d25' if r.get('priority') else '#546d79'
        pct=r['rate']*100; x=x0+(x1-x0)*r['rate']
        if mobile:
            parts += [f'<text x="24" y="{y-38}" font-size="18" font-weight="700">{esc(r["product"])}</text>',f'<text x="306" y="{y-38}" text-anchor="end" font-size="20" font-weight="700">{pct:g}%</text>',f'<text x="24" y="{y+32}" font-size="15">按期 {r["renewed"]} / 已到期 {r["eligible"]} 人</text>', f'<text x="24" y="{y+56}" font-size="15" class="muted">未按期 {r["not_renewed_by_due"]} 人</text>']
        else:
            parts += [f'<text x="24" y="{y+6}" font-size="19" font-weight="700">{esc(r["product"])}</text>',f'<text x="735" y="{y+5}" font-size="20" font-weight="700">{pct:g}%</text>',f'<text x="790" y="{y+5}" font-size="18">{r["not_renewed_by_due"]} 人</text>',f'<text x="900" y="{y+5}" font-size="15">{r["renewed"]}/{r["eligible"]} 人</text>']
        parts += [f'<line x1="{x0}" x2="{x1}" y1="{y}" y2="{y}" stroke="#d4dde1" stroke-width="5"/>',f'<line x1="{x0}" x2="{x}" y1="{y}" y2="{y}" stroke="{col}" stroke-width="5"/>',f'<circle cx="{x}" cy="{y}" r="7" fill="{col}" stroke="white" stroke-width="2"><title>{esc(r["product"])}：{r["renewed"]}/{r["eligible"]} = {pct:g}%</title></circle>']
    if mobile:
        parts += ['<text x="24" y="539" font-size="13" class="muted">共同尺度：轨道左端0%，右端100%</text>','<text x="24" y="565" font-size="13" class="muted">初次付费批次 2026-08-01</text>','<text x="24" y="588" font-size="13" class="muted">统一到期日 2026-10-30</text>','<text x="24" y="614" font-size="13" class="muted">来源：renewal_cohorts.csv</text>','<text x="24" y="640" font-size="13" class="muted">仅成熟批次；未按期不等于永久流失。</text>','<text x="24" y="663" font-size="13" class="muted">红褐色标记建议的服务试点。</text>']
    else:
        parts += ['<text x="24" y="373" font-size="14" class="muted">初次付费批次：2026-08-01；到期日：2026-10-30。仅比较已完整到期客户。</text>','<text x="24" y="399" font-size="14" class="muted">来源：renewal_cohorts.csv；未按期续订不等于永久流失。红褐色标记建议的服务试点。</text>']
    parts += ['</svg>']
    return ''.join(parts)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input-dir', type=Path, default=HERE/'source'); ap.add_argument('--out', type=Path, default=HERE); ap.add_argument('--skill-root', type=Path)
    args=ap.parse_args(); out=args.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    # This is a reproducible analysis of the frozen source package, not a generic
    # dashboard. Refuse unreviewed source replacement rather than reuse its prose.
    if (HERE/'read-files.json').exists():
        registry=json.loads((HERE/'read-files.json').read_text(encoding='utf-8-sig'))
        for f in registry['files']:
            if f['kind']=='input':
                assert digest(args.input_dir/Path(f['path']).name)==f['sha256'], 'Frozen input changed; replan required: '+f['path']
    if args.skill_root:
        registry=json.loads((HERE/'read-files.json').read_text(encoding='utf-8-sig'))
        for f in registry['files']:
            if f['kind']=='skill':
                assert hashlib.sha256((args.skill_root/f['path']).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==f['sha256'], f['path']+' hash changed'
    raw={n:(args.input_dir/n).read_text(encoding='utf-8-sig') for n in ['stage_events.csv','renewal_cohorts.csv','task.md']}
    events=list(csv.DictReader(raw['stage_events.csv'].splitlines())); cohorts=list(csv.DictReader(raw['renewal_cohorts.csv'].splitlines()))
    for r in events: r['event_n']=int(r['event_n'])
    cutoff=date(2026,11,12)
    for r in cohorts:
        for k in ['cohort_n','eligible_n','renewed_by_due_n','early_renewed_n']: r[k]=int(r[k]) if r[k]!='' else None
        r['mature']=date.fromisoformat(r['renewal_due_date'])<=cutoff
        assert r['cohort_n']>=r['eligible_n']>=0
        if r['mature']:
            assert r['eligible_n']==r['cohort_n'] and r['renewed_by_due_n'] is not None
            assert 0<=r['renewed_by_due_n']<=r['eligible_n']
        else: assert r['eligible_n']==0 and r['renewed_by_due_n'] is None
        r['rate']=r['renewed_by_due_n']/r['eligible_n'] if r['mature'] and r['eligible_n'] else None
    rows=[]
    for p in sorted({r['product'] for r in cohorts}):
        matured=[r for r in cohorts if r['product']==p and r['mature']]; future=[r for r in cohorts if r['product']==p and not r['mature']]
        n=sum(r['eligible_n'] for r in matured); renewed=sum(r['renewed_by_due_n'] for r in matured)
        rows.append(dict(product=p,eligible=n,renewed=renewed,rate=renewed/n if n else None,not_renewed_by_due=n-renewed,immature_cohort_n=sum(r['cohort_n'] for r in future),early_renewed_n=sum(r['early_renewed_n'] for r in future)))
    priority=min((r for r in rows if r['rate'] is not None),key=lambda r:r['rate'])
    for r in rows: r['priority']=r['product']==priority['product']
    computed={'synthetic':True,'cutoff':'2026-11-12','event_period':'2026-10','source_rows':{'stage_events':len(events),'renewal_cohorts':len(cohorts)},'formula':'sum(renewed_by_due_n for mature cohorts) / sum(eligible_n for mature cohorts)','mature_definition':'renewal_due_date <= cutoff; validated eligible_n == cohort_n','conversion_trial_to_paid':None,'conversion_status':'not_identifiable_no_customer_linkage','flow_status':'unsupported_independent_repeatable_stage_event_counts','priority_product':priority['product'],'products':rows,'cohorts':cohorts,'stage_events':events,'geometry':{'rate_scale':[0,1],'desktop_track':[190,700],'mobile_track':[24,306],'desktop_point_x':{r['product']:190+510*r['rate'] for r in rows},'mobile_point_x':{r['product']:24+282*r['rate'] for r in rows}}}
    dump(out/'computed.json',computed)
    desktop=chart(rows); mobile=chart(rows,True)
    (out/'chart.svg').write_text(desktop,encoding='utf-8'); (out/'chart-mobile.svg').write_text(mobile,encoding='utf-8',newline='\r\n')
    cohort_table=''
    for r in cohorts:
        cohort_table+=f'<tr data-product="{r["product"]}"><th scope="row">{r["product"]}</th><td>{r["first_paid_cohort"]}</td><td>{r["renewal_due_date"]}</td><td>{r["cohort_n"]}</td><td>{r["eligible_n"]}</td><td>{r["renewed_by_due_n"] if r["renewed_by_due_n"] is not None else "空白（未知）"}</td><td>{r["early_renewed_n"]}</td><td>{"已成熟" if r["mature"] else "未成熟"}</td><td>{format(r["rate"]*100,"g")+"%" if r["rate"] is not None else "— 不计算"}</td></tr>'
    stage_labels={'trial':'试用','activation':'激活','payment':'付费','renewal':'续订'}
    event_table=''.join(f'<tr data-product="{r["product"]}"><th scope="row">{r["product"]}</th><td>{r["period"]}</td><td>{r["stage"]} · {stage_labels[r["stage"]]}</td><td>{r["event_n"]}</td></tr>' for r in events)
    template='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>订阅服务优先级｜合成数据核查</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f4f3ee;color:#192e39;font-family:Arial,"Microsoft YaHei",sans-serif;line-height:1.65}main{max-width:1120px;margin:auto;padding:42px 32px 64px}.eyebrow{font-size:13px;letter-spacing:.12em;color:#506470}h1{font-size:38px;line-height:1.3;max-width:880px;margin:16px 0}h2{font-size:25px;line-height:1.4;margin:0 0 18px}h3{font-size:18px;margin:0 0 6px}p{margin:8px 0 16px}.lead{font-size:19px;max-width:900px}.verdict{border-left:4px solid #a83d25;padding:10px 20px;background:#fff;margin:28px 0}.section{margin-top:44px;padding-top:26px;border-top:1px solid #cbd4d7}.twocol{display:grid;grid-template-columns:1fr 1fr;gap:30px}.note{color:#506470;font-size:14px}.focus{color:#96351f}.figure{background:#fff;border:1px solid #d9e0e2;margin:20px 0 10px}svg{width:100%;height:auto;display:block}.mobile{display:none}button,select{background:#fff;border:1px solid #8c9ca4;color:#192e39;padding:10px 14px;border-radius:3px;font:inherit;cursor:pointer}button:hover{background:#e8eef0}button:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #a83d25;outline-offset:3px}.actions{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}.tablewrap{overflow-x:auto;background:white;border:1px solid #d9e0e2}table{border-collapse:collapse;width:100%;white-space:nowrap;font-size:14px}th,td{text-align:right;padding:11px 14px;border-bottom:1px solid #e2e7e9}th:first-child,td:first-child{text-align:left}thead th{background:#eaf0f2;color:#334c59}tbody th{font-weight:600}caption{text-align:left;padding:14px;font-size:16px;font-weight:700}.twofacts{display:grid;grid-template-columns:1fr 1fr;gap:32px;padding:14px 0}.twofacts strong{display:block;font-size:20px}details{margin:20px 0}summary{cursor:pointer;font-weight:700;padding:12px 0}ul{padding-left:22px}li{margin:8px 0}footer{margin-top:40px;color:#506470;font-size:13px}code{font-size:.94em} .empty{padding:14px;margin:0;background:#fff2df} @media(max-width:600px){main{padding:26px 18px 44px}h1{font-size:28px}.lead{font-size:17px}h2{font-size:22px}.twocol,.twofacts{grid-template-columns:1fr;gap:15px}.desktop{display:none}.mobile{display:block}.section{margin-top:30px}.verdict{padding:8px 14px}.figure{margin-left:-4px;margin-right:-4px}button,select{min-height:44px}.tablewrap{max-width:100%}}@media print{body{background:white}main{max-width:none;padding:0}.actions,.query{display:none}.desktop{display:block}.mobile{display:none}.section{break-inside:avoid}details{display:block}details>*{display:block!important}tr{display:table-row!important}.tablewrap{overflow:visible}table{font-size:9px;white-space:normal}th,td{padding:6px}.empty{display:none!important}h1{font-size:28px}}</style>
<main><header><div class="eyebrow">订阅业务 · 数据可支持到哪里</div><h1>先停止虚构流转，<br>把服务试点放在 <span class="focus">Comet</span></h1><p class="lead">现有数据不能画客户流转，也不能算10月试用到付费转化率。已成熟付费批次显示，Comet 按期续订为 12/40（30%）；适合先做有边界的客户成功排查。</p><p class="note">完全合成数据 ｜ 截止 2026-11-12 ｜ 事件期间：2026年10月 ｜ 客户批次按各自到期日判断成熟</p></header>
<div class="verdict"><strong>营销经理的请求：部分拒绝，替换决策依据。</strong><p>阶段表统计的是可重复的独立事件，没有用户ID或来源去向；付费和续订还可能属于更早批次。相邻阶段的数不能相除后叫“客户转化”，也不能接成漏斗或桑基流带。</p></div>
<section class="section"><h2>先比较可核对的续订表现</h2><p>每个点只代表已完整到期客户的按期续订率。横向共用 0–100% 尺度，邻近标注保留分子、分母和未按期人数。未到期批次另列。</p><div class="figure"><div class="desktop">__DESKTOP__</div><div class="mobile">__MOBILE__</div></div><p class="note">公式：已成熟批次按期续订人数合计 ÷ 已成熟批次已到期人数合计。未按期 = 已到期 − 按期续订；这不等于永久流失。来源：renewal_cohorts.csv。</p><div class="actions"><button id="export-svg">下载当前尺寸 SVG</button><button id="download-computed">下载计算结果 JSON</button></div>
<div class="twofacts"><div><strong>服务试点：Comet</strong><p>按期续订率最低，40名已到期客户中28名未按期续订。先排查这28名客户的产品使用、到期触达和续费障碍，再决定扩充服务投入。</p></div><div><strong>资源约束：Atlas 同样有28名未按期客户</strong><p>低续订率不是全部资源分配依据。Comet 样本仅40人，且各产品只有一个成熟批次；先做定向试点，同时跟踪 Atlas。不要将描述性差异写成产品质量因果。</p></div></div></section>
<section class="section"><h2>未成熟批次保留，提前续订不混入成熟率</h2><p>Atlas、Beacon、Comet 分别还有250、210、130名未成熟批次客户；提前续订分别为6、5、4人。它们不进入本次成熟批次续订率的分子或分母。</p><div class="query"><label for="product">精确值查询（只筛选下方两张表）</label> <select id="product"><option value="all">全部产品</option><option>Atlas</option><option>Beacon</option><option>Comet</option><option value="none">无匹配示例</option></select> <button id="reset">重置</button><p id="query-status" role="status" class="note">显示全部：9条批次、12条事件；主图始终展示全部产品。</p></div>
<div class="tablewrap"><table id="cohort-table"><caption>全部付费批次（客户单位：人）</caption><thead><tr><th>产品</th><th>初次付费批次</th><th>续订到期日</th><th>批次客户数</th><th>已到期客户数</th><th>按期续订</th><th>提前续订</th><th>成熟状态</th><th>按期续订率</th></tr></thead><tbody>__COHORTS__</tbody></table><p class="empty" hidden>没有匹配批次。请选择产品或重置。</p></div><p class="note">“空白（未知）”保留原始空字段，不当作零。未成熟批次的 eligible_n 为0是题设“已完整到期客户数”，不是批次客户为零；续订率不计算。表格较宽时可左右滑动。</p></section>
<section class="section"><h2>原始阶段记录能说明什么？</h2><p>这里只能核对10月各类事件的次数，不能核对谁从哪一步走到下一步。每行互相独立，事件数不是唯一客户数。</p><div class="tablewrap"><table id="event-table"><caption>2026年10月阶段事件（单位：次）</caption><thead><tr><th>产品</th><th>期间</th><th>阶段</th><th>事件次数</th></tr></thead><tbody>__EVENTS__</tbody></table><p class="empty" hidden>没有匹配事件。请选择产品或重置。</p></div></section>
<section class="section"><h2>下一步：补齐关联，再回答原问题</h2><div class="twocol"><div><h3>补采字段与明确窗口</h3><ul><li>稳定客户/账户ID、产品ID、唯一事件ID、事件时间及事件类型，支持同一阶段去重。</li><li>首次试用时间和试用批次；约定“10月开始试用”的客户范围、转付费观察窗口与截止日。</li><li>激活定义及首次激活时间、首次成功付费时间、支付/订阅ID、续订归属的原订阅ID与应续订日期。</li><li>明确每个客户能否跨产品、重复试用，以及退款、取消、延迟支付的处理。真实去向按ID和时间关联，不按阶段总数推算。</li></ul></div><div><h3>服务试点与复查</h3><ul><li>客户成功负责人先核对 Comet 的28名未按期客户名单，记录未续原因、使用状态、触达及后续续订；现有汇总表不能直接提供名单。</li><li>按原批次跟踪逾期追回人数与追回用时，和“按期续订”分开报告，不回写原到期指标。</li><li>2026-11-30批次完整到期后复查：逐产品重算按期续订人数/已到期人数，保留分母和提前续订口径；12月批次继续标为未成熟。</li><li>记录每客户服务工时及干预分组。评估服务净效果时需可比对照或随机分组，不能只用前后差认定有效。</li></ul></div></div></section>
<section class="section"><h2>源数据与计算口径</h2><p>覆盖全部输入：12条独立阶段事件、9条付费批次、3个产品。未删除记录；未成熟6条不参与成熟率计算，但全部展示。汇总只在同产品、成熟客户范围内进行。</p><div class="actions"><button data-source="stage_events.csv">下载原始阶段 CSV</button><button data-source="renewal_cohorts.csv">下载原始批次 CSV</button><button data-source="task.md">下载原始题设</button></div><details><summary>查看计算结果与全部原始数据文本</summary><h3>计算结果 JSON</h3><pre id="computed-view" style="white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px"></pre><h3>stage_events.csv</h3><pre id="stage-view" style="white-space:pre-wrap;font-size:13px"></pre><h3>renewal_cohorts.csv</h3><pre id="cohort-view" style="white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px"></pre></details></section><footer>本页为合成数据分析。无客户级流向证据；30%、72%、80%为观察批次描述，不是统计显著性结论。HTML 与 SVG 使用同一派生数据生成，无外部资源依赖。</footer></main>
<script id="payload" type="application/json">__PAYLOAD__</script><script>
const payload=JSON.parse(document.getElementById('payload').textContent);
function download(name,text,type){const blob=new Blob([text],{type});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
document.getElementById('computed-view').textContent=JSON.stringify(payload.computed,null,2);document.getElementById('stage-view').textContent=payload.raw['stage_events.csv'];document.getElementById('cohort-view').textContent=payload.raw['renewal_cohorts.csv'];
document.getElementById('download-computed').onclick=()=>download('computed.json',JSON.stringify(payload.computed,null,2),'application/json');
document.querySelectorAll('[data-source]').forEach(b=>b.onclick=()=>download(b.dataset.source,Uint8Array.from(atob(payload.source_bytes[b.dataset.source]),x=>x.charCodeAt(0)),'application/octet-stream'));
document.getElementById('export-svg').onclick=()=>{const m=matchMedia('(max-width:600px)').matches;download(m?'chart-mobile.svg':'chart.svg',document.querySelector(m?'.mobile svg':'.desktop svg').outerHTML,'image/svg+xml')};
function filter(){const v=document.getElementById('product').value;let counts=[];for(const id of ['cohort-table','event-table']){let n=0;const table=document.getElementById(id);table.querySelectorAll('tbody tr').forEach(r=>{r.hidden=v!=='all'&&r.dataset.product!==v;if(!r.hidden)n++});table.nextElementSibling.hidden=n>0;counts.push(n)}document.getElementById('query-status').textContent=`当前显示：${counts[0]}条批次、${counts[1]}条事件；主图始终展示全部产品。`}
document.getElementById('product').onchange=filter;document.getElementById('reset').onclick=()=>{document.getElementById('product').value='all';filter()};
</script></html>'''
    payload=json.dumps({'computed':computed,'raw':raw,'source_bytes':{n:base64.b64encode((args.input_dir/n).read_bytes()).decode('ascii') for n in raw}},ensure_ascii=False).replace('</','<\\/')
    for key,val in {'__DESKTOP__':desktop,'__MOBILE__':mobile,'__COHORTS__':cohort_table,'__EVENTS__':event_table,'__PAYLOAD__':payload}.items(): template=template.replace(key,val)
    (out/'artifact.html').write_text(template,encoding='utf-8',newline='\r\n')
    # Package file fingerprints intentionally exclude this self-referential manifest.
    dump(out/'checksums.json',{str(p.relative_to(out)).replace('\\','/'):digest(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='checksums.json'})
    print('Built artifact.html, computed.json and two SVG files; input validation passed.')

if __name__=='__main__': main()
