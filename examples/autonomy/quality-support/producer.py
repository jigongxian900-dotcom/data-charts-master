#!/usr/bin/env python3
"""Offline H04 analysis. Python stdlib only; all paths configurable."""
import argparse, csv, hashlib, html, io, json, math, shutil
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

READ=[]
def read(p, expected=None):
    p=Path(p); b=p.read_bytes(); h=hashlib.sha256(b).hexdigest()
    if expected and h!=expected: raise ValueError('Frozen input mismatch: '+str(p))
    READ.append({'path':p.name,'sha256':h,'verified_before_decode':True})
    return b.decode('utf-8-sig')

def main():
    ap=argparse.ArgumentParser()
    here=Path(__file__).resolve().parent
    workspace=here.parents[2]
    ap.add_argument('--skill-path',type=Path,default=workspace)
    ap.add_argument('--manifest',type=Path,default=None)
    ap.add_argument('--input-dir',type=Path,default=here/'input')
    ap.add_argument('--out-dir',type=Path,default=here)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)
    if a.manifest:
        manifest=json.loads(read(a.manifest))
        for rel in ['SKILL.md','references/business-question-selection.md','references/composition-reasoning.md','references/art-direction.md','references/html-delivery.md']:
            read(a.skill_path/rel,manifest['files'][rel])
    task=read(a.input_dir/'task.md','e4ca8735b172e3599446f12739487f50e61aee001f4b64a4de4a760fba1e8095')
    raw=read(a.input_dir/'quality_daily.csv','bc6d7ac86ff2f921984171562d605f918b2b1af271db28aa0db653732c5af169')
    rows=list(csv.DictReader(io.StringIO(raw)))
    for r in rows:
        for k in ['produced_n','inspected_n','scrap_n','rework_n']: r[k]=int(r[k]) if r[k]!='' else None
        r['rework_hours']=float(r['rework_hours']) if r['rework_hours']!='' else None
    if len({(r['unit'],r['date']) for r in rows})!=len(rows): raise ValueError('Duplicate date')
    start=date(2026,11,2); prior=date(2026,10,5); cutoff=date(2026,11,13)
    def aggregate(rr):
        inspected=sum(r['inspected_n'] for r in rr); scrap=sum(r['scrap_n'] for r in rr); rework=sum(r['rework_n'] for r in rr)
        hours=[r['rework_hours'] for r in rr]
        return {'days':len(rr),'start':rr[0]['date'],'end':rr[-1]['date'],'produced_n':sum(r['produced_n'] for r in rr),'inspected_n':inspected,'scrap_n':scrap,'rework_n':rework,'abnormal_n':scrap+rework,'abnormal_rate':(scrap+rework)/inspected if inspected else None,'known_rework_hours':sum(x for x in hours if x is not None),'rework_hours_missing_days':sum(x is None for x in hours),'rework_hours_total':None if any(x is None for x in hours) else sum(hours)}
    units=[]
    for u in sorted({r['unit'] for r in rows}):
        bydate={r['date']:r for r in rows if r['unit']==u}; curr=[]; d=start
        while d<=cutoff:
            r=bydate.get(d.isoformat())
            if r is None or any(r[k] is None for k in ['produced_n','inspected_n','scrap_n','rework_n']): break
            if r['inspected_n']<=0 or r['scrap_n']+r['rework_n']>r['inspected_n']: raise ValueError('Invalid inspection count')
            curr.append(r); d+=timedelta(days=1)
        pp=[bydate[(prior+timedelta(days=i)).isoformat()] for i in range(len(curr))]
        c=aggregate(curr); p=aggregate(pp)
        excess=max(Decimal(c['abnormal_n'])-Decimal('0.02')*Decimal(c['inspected_n']),Decimal(0))
        daily=excess/len(curr); fraction=Fraction(excess)/len(curr)
        denom=fraction.denominator
        for factor in (2,5):
            while denom%factor==0: denom//=factor
        exact=str(fraction) if denom!=1 else str(daily.normalize())
        units.append({'unit':u,'current':c,'prior_aligned':p,'change_pp':100*(c['abnormal_rate']-p['abnormal_rate']),'benchmark_rate':0.02,'benchmark_abnormal_n':float(Decimal('0.02')*c['inspected_n']),'excess_abnormal_n':float(excess),'priority_daily_excess':float(daily),'priority_exact_decimal':str(daily),'priority_exact':exact,'priority_fraction':str(fraction),'priority_repeating':denom!=1,'coverage_dates':[r['date'] for r in curr],'missing_after_last':[(start+timedelta(days=i)).isoformat() for i in range(12) if (start+timedelta(days=i)).isoformat() not in [r['date'] for r in curr]]})
    units.sort(key=lambda u:(-u['priority_daily_excess'],u['unit']))
    for i,u in enumerate(units): u['rank']=i+1;u['selected']=i<2
    current_all=[r for r in rows if start.isoformat()<=r['date']<=cutoff.isoformat()]
    missing_hours=[{'unit':r['unit'],'date':r['date'],'rework_n':r['rework_n']} for r in current_all if r['rework_hours'] is None]
    computed={'synthetic':True,'cutoff':str(cutoff),'current_start':str(start),'prior_start':str(prior),'source_sha256':READ[-1]['sha256'],'source_rows':len(rows),'units':units,'method':{'rate':'sum(scrap_n+rework_n)/sum(inspected_n)','priority':'max(sum(scrap_n+rework_n)-0.02*sum(inspected_n),0)/complete_contiguous_days','prior_alignment':'2026-10-05 + N consecutive calendar days; N=current complete contiguous observation days','scale_note':'inspected_n is denominator; produced_n is not denominator. Rework hours unknown does not invalidate inspection counts.'},'hours':{'known_subtotal':sum(r['rework_hours'] for r in current_all if r['rework_hours'] is not None),'missing_records':missing_hours,'all_units_total':None if missing_hours else sum(r['rework_hours'] for r in current_all),'claim_complete':not bool(missing_hours)},'raw_records':rows}
    computed['geometry']={'rate_domain':[0,0.10],'circle_area_measure':'current total inspected_n','circle_r_max':22,'max_inspected_n':max(u['current']['inspected_n'] for u in units),'desktop':{'rate_x0':220,'rate_x1':700,'unit_row_centres':[150,280,410,540]},'zero_preservation':{'zero_abnormal_rows':sum(r['scrap_n']==0 and r['rework_n']==0 for r in rows),'zero_scrap_rows':sum(r['scrap_n']==0 for r in rows),'zero_rework_rows':sum(r['rework_n']==0 for r in rows),'zero_hours_rows':sum(r['rework_hours']==0 for r in rows)}}
    for u in units:
        c=u['current'];p=u['prior_aligned'];u['geometry']={'current_x':220+480*c['abnormal_rate']/0.10,'prior_x':220+480*p['abnormal_rate']/0.10,'circle_r':22*math.sqrt(c['inspected_n']/computed['geometry']['max_inspected_n'])}
    (a.out_dir/'computed.json').write_text(json.dumps(computed,ensure_ascii=False,indent=2),encoding='utf-8',newline='\r\n')
    inp=a.out_dir/'input';inp.mkdir(exist_ok=True)
    (inp/'quality_daily.csv').write_bytes((a.input_dir/'quality_daily.csv').read_bytes())
    (inp/'task.md').write_bytes((a.input_dir/'task.md').read_bytes())
    selected='、'.join(u['unit'] for u in units[:2])
    decision=['# 支持分配与复查','',f'先派往 {selected}。按本期完整观测日的平均每日基准差额排名。','']
    for u in units:
        c=u['current'];p=u['prior_aligned'];decision.append(f"- 第{u['rank']}位 {u['unit']}：本期{c['start']}至{c['end']}，{c['days']}日；检验{c['inspected_n']}件，异常{c['abnormal_n']}件，异常率{c['abnormal_rate']:.3%}；前期{p['start']}至{p['end']}同天数异常率{p['abnormal_rate']:.3%}，变化{u['change_pp']:+.3f}个百分点；平均每日基准差额精确值{u['priority_exact']}件/完整观测日。")
    decision+=['','优先级是聚合差额除以观测天数，不是异常率排名，也不是先逐日截零再平均。前期只取对齐前N日，排除前期后续记录。各单元检验覆盖可能非随机，因此不外推生产总体，不预测下周收益。','','行动条件：工艺负责人按上述队列分配两组人员。入场先复核检验台账与异常处置分类、检验样本覆盖，检查高优先级单元的报废与返工工序。保留未选单元监控；本期覆盖不齐，观察期延长或数据补报后重算队列。先前改善不取消当前绝对基准差额优先级。','','复查指标：逐单元在相同完整日窗口记录检验件数、报废件数、返工件数、异常率、相对2%差额/完整日与覆盖天数；与本次同天数、同检验定义对照，并列检验覆盖与工时缺失条数。改善可观察，归因需额外设计。','','工时完整性：不能证明所有单元本期返工总工时已准确掌握。已知工时小计为 '+str(computed['hours']['known_subtotal'])+'小时；未知记录为 '+json.dumps(missing_hours,ensure_ascii=False)+'。该记录有返工件数但工时空白，必须补录或核实，不能填0。本期各单元期间长度不同，即使补齐也应标注各自期间，不冒充统一完整月总量。','','真实零：前期真实零异常保留为0%；本期报废0保留为0；源表中返工0与工时0保留为0。空白工时以未知显示，缺日以未上报显示。']
    (a.out_dir/'decisions.md').write_text('\n'.join(decision),encoding='utf-8',newline='\r\n')
    data=json.dumps(computed,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    page=TEMPLATE.replace('__DATA__',data).replace('__CSV__',json.dumps(raw,ensure_ascii=False).replace('</','<\\/'))
    # This is a reviewed fixed-source rebuild, not a new independent execution.
    (a.out_dir/'artifact.html').write_text(page,encoding='utf-8',newline='\r\n')
    # These entries include the initial human-in-the-loop planning read, which used identical verified files.
    (a.out_dir/'read-files.json').write_text(json.dumps({'boundary':'Portable fixed-source rebuild; original independent-production audit retained separately.','files':READ},ensure_ascii=False,indent=2),encoding='utf-8',newline='\r\n')
    print('Built artifact.html and computed.json; input copies and audit trail saved.')

TEMPLATE=r'''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>工艺支持分配 · 精密陶瓷</title>
<style>
:root{--ink:#18333d;--muted:#51666d;--accent:#11776e;--bad:#b34325;--paper:#f7f6f0;--line:#d2dcda}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1240px;margin:auto;padding:42px 40px 56px}.eyebrow{font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--accent)}h1{font-size:40px;line-height:1.25;letter-spacing:-1px;margin:14px 0 16px;max-width:980px}h2{font-size:24px;line-height:1.35;margin:0 0 12px}h3{font-size:19px;margin:0 0 8px}p{margin:8px 0 16px}.intro{max-width:960px;font-size:18px}.meta{color:var(--muted);font-size:14px}.hero{border-top:4px solid var(--accent);border-bottom:1px solid var(--line);padding:24px 0;margin-top:28px;display:grid;grid-template-columns:1fr 280px;gap:36px}.hero strong{color:var(--accent)}.hero .side{border-left:1px solid var(--line);padding-left:24px;font-size:14px}section{margin-top:36px}.chart-header{display:flex;gap:24px;align-items:start;justify-content:space-between}.chart-header h2{margin:0}.tools{display:flex;gap:8px;flex-wrap:wrap}button,select{font:inherit;font-size:14px;background:white;border:1px solid #80928f;color:var(--ink);padding:7px 12px;border-radius:4px;cursor:pointer}button:hover{background:#e5f1ee}button:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #ba651f;outline-offset:3px}.legend{display:flex;flex-wrap:wrap;gap:12px 24px;font-size:14px;color:var(--muted);margin:15px 0}.legend b{color:var(--ink)}.swatch{display:inline-block;width:11px;height:11px;background:var(--accent);border-radius:50%;margin-right:6px}.diamond{background:white;border:1.5px solid var(--ink);transform:rotate(45deg);border-radius:0}.dash{display:inline-block;width:22px;border-top:2px dashed var(--bad);vertical-align:middle;margin-right:6px}#chart{background:#fff;border:1px solid var(--line);padding:4px 10px 12px}svg{display:block;width:100%;height:auto}svg text{font-family:"Segoe UI","Microsoft YaHei",sans-serif}figure{margin:0}.caption{font-size:14px;color:var(--muted);margin-top:12px;max-width:1040px}.reason{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:34px;border-top:1px solid var(--line);padding-top:28px}.reason>div{min-width:0}.notice{border-left:4px solid var(--bad);padding:12px 18px;background:#fff1e9}.notice h3{color:#96351d}.facts{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.fact{background:#fff;padding:14px 18px;border:1px solid var(--line)}.fact b{display:block;font-size:24px}.fact span{font-size:13px;color:var(--muted)}details{min-width:0;max-width:100%;background:#fff;border:1px solid var(--line);margin-top:16px;padding:16px 20px}summary{font-weight:700;cursor:pointer}ol{padding-left:23px}li{margin:6px 0}.query{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:20px 0 12px}.table-wrap{width:100%;max-width:100%;min-width:0;overflow:auto;max-height:540px;border:1px solid var(--line);background:white}table{border-collapse:collapse;width:100%;font-size:14px;white-space:nowrap}th,td{text-align:right;border-bottom:1px solid #e5eae9;padding:9px 13px}th{background:#eaf0ee;position:sticky;top:0;color:#29434a}th:first-child,td:first-child{text-align:left}th:first-child,td:first-child{position:sticky;left:0;z-index:1;background:#fff}th:first-child{z-index:3;background:#eaf0ee}td.empty{position:static;text-align:left;white-space:normal;padding:18px}td.unknown{color:#96351d;background:#fff1e9}.status{font-size:14px;min-height:24px;color:var(--accent)}footer{margin-top:36px;padding-top:18px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);word-break:break-word}.mobile-unit{padding:18px 2px;border-bottom:1px solid var(--line)}.mobile-unit:last-child{border:0}.mobile-head{display:flex;align-items:baseline;justify-content:space-between;gap:8px}.mobile-head b{font-size:20px}.mobile-rank{font-size:12px;color:var(--accent)}.mobile-stats{display:flex;justify-content:space-between;gap:12px;font-size:13px}.mobile-stats b{font-size:19px;display:block}.mobile-stats .priority{color:var(--accent)}.mobile-note{font-size:13px;color:var(--muted);margin-top:8px}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
@media(max-width:700px){main{padding:24px 16px 40px}h1{font-size:29px;letter-spacing:-.5px}.intro{font-size:16px}.hero{grid-template-columns:1fr;gap:14px;padding:20px 0}.hero .side{border-left:0;border-top:1px solid var(--line);padding:14px 0 0}.chart-header{display:block}.tools{margin:12px 0}.legend{gap:8px 14px;font-size:12px}h2{font-size:21px}#chart{padding:2px 10px}.reason{grid-template-columns:1fr;gap:20px}.facts{gap:8px}.fact{padding:10px 12px}.fact b{font-size:21px}details{padding:14px 12px}.table-wrap{max-height:440px}}
@media print{body{background:white;color:#142b32;font-size:11pt}main{padding:0;max-width:none}h1{font-size:25pt}.tools,.query,.status{display:none!important}details{display:block;border:0;padding:0}details>summary{display:none}.table-wrap{max-height:none;overflow:visible}table{font-size:8pt;white-space:normal}th,td{padding:5px}th,th:first-child,td:first-child{position:static}.hero{break-inside:avoid}.reason{display:block;break-inside:auto}.reason>div{margin-bottom:18px}.notice{break-inside:avoid}.facts{break-inside:avoid}section{margin-top:20px}#chart{break-inside:avoid}footer{font-size:8pt}.print-warning{display:block}#raw-section{break-before:page}tr{break-inside:avoid}}
</style>
<body><main>
<div class="eyebrow">工艺支持分配 / 13 NOV 2026</div>
<h1>两组支持人员，先去哪里？</h1>
<p class="intro" id="lead"></p><p class="meta">合成数据 · 截止 2026-11-13 · 本期从 11-02 起连续完整观测 · 前期从 10-05 起对齐相同天数</p>
<div class="hero"><div><h2 id="answer"></h2><p id="hero-note"></p></div><div class="side"><b>分配依据</b><br>平均每日基准差额 =<br>max(异常合计 − 检验合计 × 2%, 0)<br>÷ 完整观测日数<br><span class="meta">单位：件 / 完整观测日</span></div></div>
<section aria-labelledby="main-title"><div class="chart-header"><div><h2 id="main-title">把规模、异常率、变化与覆盖放在同一行</h2><p class="meta">按平均每日基准差额从高到低；前两名为本次支持对象。</p></div><div class="tools"><button id="svg-download">导出主图 SVG</button><button id="print">打印 / PDF</button></div></div>
<div class="legend"><span><i class="swatch"></i><b>本期</b>，圆面积 = 检验件数</span><span><i class="swatch diamond"></i><b>对齐前期</b>，线连同一单元</span><span><i class="dash"></i><b>2%</b> 比较基准</span><span>实格 = 有上报；空格 = 未上报</span></div>
<figure><div id="chart"></div><figcaption class="caption">异常率以完成检验件数为分母。圆的位置表示异常率，圆面积表示本期检验规模；连线只表示两期对比，不表示期间逐日走势。各行共享率尺度与面积尺度。变化单位为百分点，负值表示异常率下降。覆盖不足不补零。优先级差额不是已确认能消除的异常件数。</figcaption></figure><div class="status" id="export-status" aria-live="polite"></div>
</section>
<section class="reason"><div><h2>为何不只看异常率？</h2><div id="tradeoff"></div><p>本题按“超过基准的异常件数 / 完整观测日”分配支持。异常率、检验规模与覆盖天数必须共同考虑。已观察到改善，仍可能排在支持队列前列。</p><details><summary>查看计算口径与完整比较表</summary><ol><li>异常件数 = scrap_n + rework_n，两种处置互斥。返工工时不进入异常率分子。</li><li>异常率 = 观察期异常合计 / 检验合计。先汇总计数再求比率，不平均每日比率。</li><li>从 11-02 起逐日连续完整上报得到 N；与 10-05 起的前 N 日对应。返工工时缺失不取消已完整的检验计数。</li><li>基准差额 = max(异常合计 − 0.02 × 检验合计, 0)。平均每日差额 = 基准差额 / N。</li><li>检验覆盖未保证随机。结论只适用于已检验记录，不外推全部生产件，不预测未来收益。</li></ol><p class="meta">完整比较表：左右滚动查看全部列；首列固定显示单元。</p><div class="table-wrap" tabindex="0" role="region" aria-label="完整比较表，可左右滚动；第一列为单元"><table id="comparison"></table></div></details></div><div><div class="notice"><h3>返工总工时尚未掌握完整</h3><p id="hours-note"></p></div><div class="facts" id="facts"></div><p class="caption">真实零与未知不同：报废或返工为 0，按 0 保留；工时空白显示“未知”。有异常件数不代表已知处理工时。</p></div></section>
<section><h2>支持后怎么复查</h2><p>工艺负责人先核对检验台账与处置分类，再由两组支持人员检查优先单元的报废和返工工序。连续补报后，按相同规则重算排序。</p><p>复查同天数窗口的检验件数、异常率、平均每日基准差额、覆盖天数及工时缺失条数。检验覆盖改变时单独说明；若要判断支持行动的净效果，仍需可比对照。</p></section>
<section id="raw-section"><h2>精确值与原始记录</h2><p class="meta">源文件全部记录内嵌。查询仅影响下方明细，不改变上方全单元排名。CSV 保留原始空白；JSON 用 null 表示未知。</p><div class="tools"><button id="csv-download">下载原始 CSV</button><button id="json-download">下载 computed.json</button></div><div class="query"><label for="unit-query">单元</label><select id="unit-query"><option value="all">全部单元</option></select><label for="period-query">期间</label><select id="period-query"><option value="all">全部原始日期</option><option value="current">本期观察记录</option><option value="aligned">对齐前期记录</option></select><button id="reset">重置查询</button></div><p id="query-count" class="meta" aria-live="polite"></p><div class="table-wrap" tabindex="0" role="region" aria-label="原始数据表，可左右滚动；第一列为单元"><table id="raw"></table></div></section>
<footer id="source"></footer>
</main><script id="computed" type="application/json">__DATA__</script><script>
'use strict';
const D=JSON.parse(document.getElementById('computed').textContent),CSV=__CSV__,U=D.units,$=id=>document.getElementById(id),fmt=(x,d=2)=>x===null?'未知':Number(x).toLocaleString('zh-CN',{maximumFractionDigits:d}),pct=x=>fmt(x*100,3)+'%',pp=x=>(x>0?'+':'')+fmt(x,3)+' 个百分点';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
$('lead').textContent='按本期每个完整观测日超过 2% 基准的异常件数差额排序，再用同天数前期异常率解释变化。';
$('answer').innerHTML='先支持 <strong>'+U.slice(0,2).map(u=>esc(u.unit)).join(' 与 ')+'</strong>';
$('hero-note').textContent=U.slice(0,2).map(u=>u.unit+'：'+fmt(u.priority_daily_excess)+' 件/日').join('；')+'。这是观察期平均差额，不是下周收益预测。';
$('tradeoff').innerHTML=U.map(u=>'<p><b>'+esc(u.unit)+'</b>：本期 '+pct(u.current.abnormal_rate)+'，较对齐前期 '+pp(u.change_pp)+'；平均每日差额 '+u.priority_exact+' 件，排第 '+u.rank+'。</p>').join('');
$('hours-note').textContent='已知工时小计 '+fmt(D.hours.known_subtotal)+' 小时，但 '+D.hours.missing_records.map(r=>r.unit+' '+r.date+'（返工 '+r.rework_n+' 件）').join('；')+' 的工时未知。不能把这个小计当作准确总工时。';
$('facts').innerHTML='<div class="fact"><b>'+fmt(D.hours.known_subtotal)+'</b><span>已知工时小计 / 小时</span></div><div class="fact"><b>'+D.hours.missing_records.length+'</b><span>本期工时未知记录 / 条</span></div>';
$('source').textContent='来源：H04/input/quality_daily.csv（合成数据），'+D.source_rows+' 条原始记录；截至 '+D.cutoff+'。源文件 SHA-256：'+D.source_sha256+'。所有图、表和导出来自同一内嵌数据。';
const maxN=D.geometry.max_inspected_n,rad=(n,maxr)=>maxr*Math.sqrt(n/maxN),pri=u=>u.priority_repeating?(Math.trunc(u.priority_daily_excess*1000)/1000).toFixed(3)+'…':fmt(u.priority_daily_excess);
function tx(x,y,t,size=14,fill='#18333d',anchor='start',weight='400'){return `<text x="${x}" y="${y}" font-size="${size}" fill="${fill}" text-anchor="${anchor}" font-weight="${weight}">${esc(t)}</text>`}
function circle(x,y,r,fill){return `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" fill-opacity="0.88" stroke="white" stroke-width="1.5"/>`}
function diamond(x,y){return `<path d="M ${x} ${y-5} L ${x+5} ${y} L ${x} ${y+5} L ${x-5} ${y} Z" fill="white" stroke="#18333d" stroke-width="1.5"/>`}
function wrapSVG(w,h,body,label){return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(label)}"><rect width="${w}" height="${h}" fill="white"/>${body}</svg>`}
function desktop(){let s=tx(24,35,'支持顺序 / 单元',14,'#51666d')+tx(220,35,'异常率（%） · 同天数前期 → 本期',14,'#51666d')+tx(778,35,'覆盖日 / 本期检验规模',14,'#51666d')+tx(1114,35,'基准差额 / 日',14,'#11776e','end');
for(let k=0;k<=10;k+=2){let x=220+480*k/10;s+=`<line x1="${x}" x2="${x}" y1="70" y2="594" stroke="${k===2?'#b34325':'#e3e9e7'}" stroke-dasharray="${k===2?'5 4':'none'}"/>`+tx(x,64,k+'%',13,k===2?'#b34325':'#51666d','middle')}
s+=tx(316,88,'2% 基准',12,'#b34325');
U.forEach((u,i)=>{let y=150+i*130,c=u.current,p=u.prior_aligned,x=220+480*c.abnormal_rate/.1,xp=220+480*p.abnormal_rate/.1,col=u.selected?'#11776e':'#607b85';s+=`<line x1="20" x2="1120" y1="${y+70}" y2="${y+70}" stroke="#e3e9e7"/>`+tx(26,y-8,String(u.rank).padStart(2,'0'),17,col,'start','700')+tx(65,y-8,u.unit,20,'#18333d','start','700')+tx(65,y+18,u.selected?'本次支持':'持续观察',13,col)+`<line x1="${xp}" x2="${x}" y1="${y}" y2="${y}" stroke="#526972" stroke-width="2"/>`+circle(x,y,rad(c.inspected_n,22),col)+diamond(xp,y)+tx(x,y-33,pct(c.abnormal_rate),17,col,'middle','700')+tx(xp,y+37,'前期 '+pct(p.abnormal_rate),12,'#51666d',xp>660?'end':xp<260?'start':'middle')+tx(460,y+60,pp(u.change_pp),13,u.change_pp>0?'#96351d':'#11776e','middle');
s+=tx(778,y-20,c.days+' / 12 日',15,'#18333d','start','600')+tx(930,y-20,fmt(c.inspected_n)+' 件',15,'#18333d','end','600');
for(let j=0;j<12;j++){let present=j<c.days;s+=`<rect x="${778+j*13}" y="${y-6}" width="9" height="15" fill="${present?col:'#fff'}" stroke="${present?col:'#b9c8c4'}"/>`}
s+=tx(778,y+30,'11-02 → '+c.end.slice(5),12,'#51666d')+tx(1114,y,pri(u),27,col,'end','700')+tx(1114,y+25,u.priority_repeating?'精确 '+u.priority_exact+' 件/日':'件 / 完整观测日',12,'#51666d','end');});
s+=tx(24,646,'圆面积参照：本期累计检验件数',13,'#51666d');[1000,3000,maxN].forEach((n,i)=>{let x=365+i*140;s+=circle(x,642,rad(n,22),'#607b85')+tx(x+30,647,fmt(n)+' 件',12,'#51666d')});return wrapSVG(1140,685,s,'按基准差额排名，联合异常率、检验规模、前期变化及覆盖天数');}
function mobile(u){let w=286,x0=20,x1=264,y=80,c=u.current,p=u.prior_aligned,x=x0+(x1-x0)*c.abnormal_rate/.1,xp=x0+(x1-x0)*p.abnormal_rate/.1,s='';
for(let k=0;k<=10;k+=2){let xx=x0+(x1-x0)*k/10;s+=`<line x1="${xx}" x2="${xx}" y1="35" y2="111" stroke="${k===2?'#b34325':'#dce5e2'}" stroke-dasharray="${k===2?'4 3':'none'}"/>`+tx(xx,133,k+'%',12,k===2?'#b34325':'#51666d','middle')}
s+=`<line x1="${xp}" x2="${x}" y1="${y}" y2="${y}" stroke="#526972" stroke-width="2"/>`+circle(x,y,rad(c.inspected_n,19),u.selected?'#11776e':'#607b85')+diamond(xp,y);
s+=tx(20,19,'前期 '+pct(p.abnormal_rate),13,'#51666d')+tx(266,19,'本期 '+pct(c.abnormal_rate),14,'#11776e','end','700')+tx(70,51,'2% 基准',11,'#b34325');
return wrapSVG(w,150,s,u.unit+'：前期 '+pct(p.abnormal_rate)+'，本期 '+pct(c.abnormal_rate));}
function render(){if(window.innerWidth>700){$('chart').innerHTML=desktop();return}
$('chart').innerHTML=U.map(u=>`<div class="mobile-unit"><div class="mobile-head"><b>${esc(u.unit)}</b><span class="mobile-rank">第 ${u.rank} 位 · ${u.selected?'本次支持':'持续观察'}</span></div>${mobile(u)}<div class="mobile-stats"><div class="priority"><b>${pri(u)}</b>基准差额 · 件/日</div><div><b>${fmt(u.current.inspected_n)}</b>本期检验 · 件</div><div><b>${u.current.days}/12</b>覆盖 · 日</div></div><div class="mobile-note">${u.priority_repeating?'差额精确值：'+u.priority_exact+' 件/日<br>':''}较前期 ${pp(u.change_pp)}<br>本期 11-02 → ${u.current.end.slice(5)}；前期 10-05 → ${u.prior_aligned.end.slice(5)}</div><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 286 28" role="img" aria-label="${u.current.days}个上报日，之后为空白未上报">${Array.from({length:12},(_,i)=>`<rect x="${3+i*23.3}" y="10" width="17" height="12" fill="${i<u.current.days?'#11776e':'white'}" stroke="#8da9a1"/>`).join('')}</svg></div>`).join('');}
render();window.addEventListener('resize',render);
function table(id,headers,rows){$(id).innerHTML='<thead><tr>'+headers.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+(rows.length?rows.map(r=>'<tr>'+r.map(v=>'<td'+(v===null?' class="unknown"':'')+'>'+esc(v===null?'未知':v)+'</td>').join('')+'</tr>').join(''):'<tr><td class="empty" colspan="'+headers.length+'">当前查询没有记录。请重置查询或更换条件。</td></tr>')+'</tbody>'}
table('comparison',['单元','完整日','本期期间','对齐前期期间','检验件','异常件','异常率','前期率','变化/百分点','总基准差额/件','日均差额精确值/件'],U.map(u=>[u.unit,u.current.days,u.current.start+' ~ '+u.current.end,u.prior_aligned.start+' ~ '+u.prior_aligned.end,u.current.inspected_n,u.current.abnormal_n,pct(u.current.abnormal_rate),pct(u.prior_aligned.abnormal_rate),fmt(u.change_pp,6),fmt(u.excess_abnormal_n,6),u.priority_exact]));
U.forEach(u=>$('unit-query').add(new Option(u.unit,u.unit)));
function query(){let unit=$('unit-query').value,p=$('period-query').value,rr=D.raw_records.filter(r=>(unit==='all'||r.unit===unit)&&(p==='all'||(p==='current'?r.date>=D.current_start:r.date>=D.prior_start&&r.date<=U.find(u=>u.unit===r.unit).prior_aligned.end)));
table('raw',['单元','日期','生产/件','检验/件','报废/件','返工/件','返工工时/小时'],rr.map(r=>[r.unit,r.date,r.produced_n,r.inspected_n,r.scrap_n,r.rework_n,r.rework_hours]));$('query-count').textContent='明细范围：'+(unit==='all'?'全部单元':unit)+' · '+$('period-query').selectedOptions[0].text+' · '+rr.length+' 条；空白工时以“未知”显示。';return rr.length;}
$('unit-query').addEventListener('change',query);$('period-query').addEventListener('change',query);$('reset').onclick=()=>{$('unit-query').value='all';$('period-query').value='all';query()};query();
function download(name,body,mime){const b=new Blob([body],{type:mime}),url=URL.createObjectURL(b),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);$('export-status').textContent='已导出 '+name+'。导出包含全单元数据，明细查询不改变主图。';}
$('csv-download').onclick=()=>download('quality_daily.csv',CSV,'text/csv;charset=utf-8');$('json-download').onclick=()=>download('computed.json',JSON.stringify(D,null,2),'application/json');$('svg-download').onclick=()=>download('quality-support.svg',desktop(),'image/svg+xml');
let priorState=null;window.addEventListener('beforeprint',()=>{if(priorState===null)priorState={u:$('unit-query').value,p:$('period-query').value,details:[...document.querySelectorAll('details')].map(d=>d.open),scrolls:[...document.querySelectorAll('.table-wrap')].map(t=>[t.scrollLeft,t.scrollTop]),page:[scrollX,scrollY],focus:document.activeElement.id};document.querySelectorAll('details').forEach(d=>d.open=true);$('unit-query').value='all';$('period-query').value='all';query();$('chart').innerHTML=desktop()});window.addEventListener('afterprint',()=>{const saved=priorState;priorState=null;if(saved){$('unit-query').value=saved.u;$('period-query').value=saved.p;document.querySelectorAll('details').forEach((d,i)=>d.open=saved.details[i]);query()}render();if(saved)requestAnimationFrame(()=>{document.querySelectorAll('.table-wrap').forEach((t,i)=>{t.scrollLeft=saved.scrolls[i][0];t.scrollTop=saved.scrolls[i][1]});if(saved.focus&&$(saved.focus))$(saved.focus).focus({preventScroll:true});window.scrollTo(...saved.page)})});$('print').onclick=()=>window.print();
window.__H04={data:D,desktop,query};
</script></body></html>'''

if __name__=='__main__':main()
