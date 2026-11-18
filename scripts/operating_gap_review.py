"""Three audience-specific treatments of a fully reported operating gap."""

from pathlib import Path

from build_operating_story import derive, display, make_spec, percentage
from chart_html import esc, svg_chart, theme_css
from compose_html import data_url, safe_json, static_svg


ASSETS = Path(__file__).resolve().parents[1] / "assets"


def reviewed(raw):
    data = derive(raw)
    gaps = data["gaps"]
    if (not raw["synthetic"] or not 4 <= len(gaps) <= 8 or data["gap_n"] != data["n"]
            or data["growth_n"] != data["n"] or data["scatter_n"] != data["n"]
            or not data["gap"] or data["gap"] <= 0 or not data["growth"] or data["growth"] <= 0
            or any(row["gap"] < 0 or not row["target"] for row in gaps)):
        return None
    lead = gaps[0]
    if lead["growth"] <= 0 or lead["sameStoreGrowth"] >= 0:
        return None
    date = raw["period"].split("对比", 1)[0]
    share = percentage(lead["gap"], data["gap"])
    top_three = sum(row["gap"] for row in gaps[:3])
    return dict(data, lead=lead, share=share, date=date, unit=raw["unit"], top_three=top_three,
                trio_rate=percentage(top_three, data["gap"]), other_gap=data["gap"]-top_three,
                metric=raw.get("same_store_metric", "同店指标"))


def signed(value):
    return display(round(value,1), "%", signed=True)


def amount(value, d):
    return f'{display(value)} {d["unit"]}'


def source(d):
    return f'示例数据 · {esc(d["date"])} · {d["n"]} 个市场'


def mast(d, edition):
    return f'<header class="mast"><span>{edition}</span><time>{esc(d["date"])}</time></header>'


def focus_track(d):
    lead = d["lead"]
    share = d["share"]
    return f'''<div class="focus-track">
      <div class="track-labels"><span>{esc(lead["name"])}</span><span>其余市场</span></div>
      <div class="track" role="img" aria-label="{esc(lead["name"])}占总缺口 {share:.1f}%"><i style="width:{share:.8f}%"></i></div>
      <div class="track-labels track-values"><span>{esc(amount(lead["gap"],d))}</span>
        <span>{esc(amount(d["gap"]-lead["gap"],d))}</span></div>
    </div>'''


def remainder_ranking(d):
    rows = [(r["name"],r["gap"]) for r in d["gaps"][1:3]]
    rows.append((f'其余 {d["n"]-3} 个市场', d["other_gap"]))
    max_value = max(value for _,value in rows) or 1
    parts = []
    for name, value in rows:
        parts.append(f'<li><span>{esc(name)}</span><div class="rank-track" style="--value:{value/max_value:.8%}">'
                     f'<i aria-hidden="true"></i><b>{display(value)}</b></div></li>')
    return '<ol class="rank" aria-label="目标差额">' + ''.join(parts) + '</ol>'


def materials(d):
    rows = ''.join(f'<tr><th scope="row">{esc(row["name"])}</th><td>{display(row["prior"])}</td><td>{display(row["revenue"])}</td>'
                   f'<td>{display(row["target"])}</td><td>{display(row["gap"])}</td><td>{signed(row["growth"])}</td>'
                   f'<td>{signed(row["sameStoreGrowth"])}</td></tr>' for row in d["gaps"])
    download = data_url(safe_json(d["source"]), "application/json;charset=utf-8")
    return f'''<details id="materials" class="materials">
    <summary>原始数据与口径</summary><p>金额单位为{esc(d["unit"])}。同比对比上年同月。同店为两期均营业的相同门店。</p>
    <div class="table-scroll"><table><thead><tr><th>市场</th><th>上年同期</th><th>本期</th><th>目标</th>
    <th>目标缺口</th><th>全量营业额同比</th><th>{esc(d["metric"])}同比</th></tr></thead><tbody>{rows}</tbody></table></div>
    <div class="downloads"><a href="{download}" download="source.json">下载原始数据</a>{d["downloads"]}</div></details>'''


def priority_actions(d):
    other_markets="、".join(esc(row["name"]) for row in d["gaps"][1:3])
    return (
        '核对门店目标与实际，列出主要差额。另列下月改善估算，写明措施、金额和依据。',
        f'复核{other_markets}的目标缺口。按同店、新开、退出门店拆本期增量，单列口径变化。',
    )


def brief(d):
    name = esc(d["lead"]["name"])
    item, _ = priority_actions(d)
    other_markets="、".join(esc(row["name"]) for row in d["gaps"][1:3])
    return f'''<main class="brief">
    {mast(d,'经营简报')}
    <div class="brief-heading"><h1>目标缺口，先查{name}</h1>
      <p>全区目标 {display(d["target"])}，实际 {esc(amount(d["actual"],d))}，达成 {percentage(d["actual"],d["target"]):.1f}%。</p></div>
    <div class="brief-proof">
      <section class="feature-number" aria-label="目标缺口集中程度">
        <div class="big">{d["share"]:.0f}<small>%</small></div><p>{name}占全区 {esc(amount(d["gap"],d))}缺口</p>{focus_track(d)}
      </section>
      <section class="ranking"><div class="section-title"><h2>其余缺口分布</h2><span>{esc(d["unit"])}</span></div>
        {remainder_ranking(d)}<p class="figure-note">{name}、{other_markets}合计占全区缺口 {d["trio_rate"]:.0f}%。</p>
      </section>
    </div>
    <div class="brief-contrast"><strong>{name}为何先查</strong><div>
      <span>全量营业额同比 <b>{signed(d["lead"]["growth"])}</b></span><span>{esc(d["metric"])}同比 <b class="negative">{signed(d["lead"]["sameStoreGrowth"])}</b></span>
    </div></div>
    <section class="brief-action"><h2>下次复盘带回</h2><div>
      <p><strong>{name}营运</strong>　{item}</p><p><strong>区域分析</strong>　核对{other_markets}的目标缺口，拆出各类门店贡献的增量。</p></div></section>
    <footer class="source">{source(d)}</footer>{materials(d)}
    </main>'''


def market_table(d):
    lead_id = d["lead"]["id"]
    rows = []
    for row in d["gaps"]:
        selected = row["id"] == lead_id
        bar = row['gap'] / d['lead']['gap']
        rows.append(f'<tr{" class=selected" if selected else ""}><th scope="row"><button type="button" '
                    f'data-market="{esc(row["id"])}" aria-pressed="{str(selected).lower()}">{esc(row["name"])}</button></th>'
                    f'<td>{display(row["revenue"])} <span class="scale-separator">/</span> {display(row["target"])}</td>'
                    f'<td class="deficit"><div><i style="width:{bar:.8%}" aria-hidden="true"></i><b>{display(row["gap"])}</b></div></td><td>{signed(row["growth"])}</td>'
                    f'<td class="{"negative" if row["sameStoreGrowth"]<0 else ""}">{signed(row["sameStoreGrowth"])}</td></tr>')
    return ('<div class="table-scroll" role="region" aria-label="各市场表现" tabindex="0">'
            '<table class="market-table"><caption><span class="screen-caption">选择市场可查看该市场的达成率</span>'
            '<span class="print-caption">按目标缺口排序</span></caption>'
            f'<thead><tr><th>市场</th><th>本期 / 目标</th><th>缺口</th><th>全量同比</th><th>{esc(d["metric"])}同比</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def detail_panel(d):
    lead=d["lead"]
    ratio=percentage(lead["revenue"],lead["target"])
    return f'''<div class="profile" id="profile" aria-live="polite">
    <p class="profile-label" id="market-name">{esc(lead["name"])}</p>
    <div class="profile-rate" id="market-attainment">{ratio:.1f}%</div>
    <p class="profile-caption">目标达成率</p>
    <div class="attain-track" role="img" id="attain-track" aria-label="目标达成率 {ratio:.1f}%"><i style="width:{ratio:.8f}%"></i></div>
    <dl class="profile-stats"><div><dt>较去年同期增减</dt><dd id="market-increment">{esc(amount_delta(lead["contribution"],d))}</dd></div>
      <div><dt>{esc(d["metric"])}同比</dt><dd id="market-same">{signed(lead["sameStoreGrowth"])}</dd></div>
      <div><dt>距目标</dt><dd id="market-gap">{esc(amount(lead["gap"], d))}</dd></div></dl></div>'''


def contribution(d):
    top=d["top"]
    rest=d["change"]-sum(row["contribution"] for row in top)
    entries=[(row["name"],row["contribution"]) for row in top]+[("其余市场净额",rest)]
    cells=''.join(f'<li><span>{esc(name)}</span><strong>{display(value,signed=True)}</strong></li>' for name,value in entries)
    strip=''
    if all(value >= 0 for _,value in entries):
        strip='<div class="contribution-strip" aria-hidden="true">'+''.join(
            f'<i style="width:{value/d["change"]:.8%}"></i>' for _,value in entries)+'</div>'
    heading=(f'{esc("、".join(row["name"] for row in top))}贡献净增量的 {d["top_share"]:.1f}%'
             if d["top_share"] <= 100 else '区域营业额增量及抵消项')
    return f'''<section class="report-section contribution" id="growth">
      <div class="section-title"><h2>{heading}</h2><span>同比增量 · {esc(d["unit"])}</span></div>
      <p class="section-intro">全区较上年同月净增 {esc(amount(d["change"],d))}。</p>
      {strip}<ul aria-label="地区营业额增量">{cells}</ul></section>'''


def amount_delta(value,d):
    return f'{display(value,signed=True)} {d["unit"]}'


def diagnosis(d):
    lead=d["lead"]
    label=esc(lead["name"])
    others=[r for r in d["risk"] if r["id"] != lead["id"]]
    if others:
        other=others[0]
        compare=f'{esc(other["name"])}也出现同样的分化，但目标差额只有 {esc(amount(other["gap"],d))}。'
    else:
        compare=f'区域第二大差额来自{esc(d["gaps"][1]["name"])}，为 {esc(amount(d["gaps"][1]["gap"],d))}。'
    falling=sorted((r for r in d["rows"] if r["sameStoreGrowth"] < 0 and r["id"] != lead["id"]),
                   key=lambda row:row["sameStoreGrowth"])
    watch=''
    if falling:
        watch='<div class="watch-markets"><h3>其他同店下行市场</h3><dl>'+''.join(
            f'<div><dt>{esc(row["name"])}</dt><dd><span>全量营业额 <strong>{signed(row["growth"])}</strong></span>'
            f'<span>{esc(d["metric"])} <strong>{signed(row["sameStoreGrowth"])}</strong></span></dd></div>'
            for row in falling)+'</dl></div>'
    return f'''<section id="same-store" class="report-section composition-turn">
      <div><p class="section-label">增量与同店</p><h2>{label}总额增长，同店下降</h2>
        <p>{label}营业额由 {display(lead["prior"])} 增至 {esc(amount(lead["revenue"],d))}。{compare}</p></div>
      <div class="paired-reading" aria-label="{label}的两组同比">
        <div><strong>{signed(lead["growth"])}</strong><span>全量营业额同比</span></div>
        <div><strong>{signed(lead["sameStoreGrowth"])}</strong><span>{esc(d["metric"])}同比</span></div>
      </div>{watch}</section>'''


def report(d):
    title=esc(d["lead"]["name"])
    item,followup=priority_actions(d)
    watch="、".join(esc(row["name"]) for row in sorted(d["rows"],key=lambda r:r["sameStoreGrowth"])
                   if row["sameStoreGrowth"] < 0 and row["id"] != d["lead"]["id"])
    watch_task=f'<p>复核{watch}的同店名单和降幅，同店样本与全量分别报告。</p>' if watch else ''
    return f'''<main class="report">
    {mast(d,'区域经营复盘')}
    <header class="report-heading"><h1>营业额同比增 {display(round(d["growth"],1),"%")}，<br>
      {title}占缺口 {d["share"]:.0f}%</h1>
      <div class="report-intro"><p>全区净增 {display(d["change"])}，距目标差 {esc(amount(d["gap"],d))}。</p>
      <p>先查{title}差额，再核对同店下降涉及的金额、样本与门店。</p></div></header>
    <nav class="contents" aria-label="章节"><a href="#markets">各市场表现</a><a href="#growth">增长来源</a><a href="#same-store">同店表现</a>
      <a href="#review">下次复盘</a><a href="#materials">数据与口径</a></nav>
    <section id="markets" class="report-section markets">
      <div class="section-title"><h2>缺口集中在{title}、{esc(d["gaps"][1]["name"])}和{esc(d["gaps"][2]["name"])}</h2>
      <span>金额 · {esc(d["unit"])}</span></div>
      <p class="section-intro">三个市场合计差 {esc(amount(d["top_three"],d))}，占全区缺口 {d["trio_rate"]:.0f}%。</p>
      <p class="scroll-hint">横滑表格查看同店同比</p>
      <div class="market-layout">{market_table(d)}{detail_panel(d)}</div>
    </section>
    {contribution(d)}{diagnosis(d)}
    <section id="review" class="report-section review"><h2>下次复盘带回两份结果</h2>
      <dl><div><dt>{title}营运</dt><dd><strong>门店差额清单</strong><p>{item}</p></dd></div>
        <div><dt>区域分析</dt><dd><strong>市场缺口与增量拆分表</strong><p>{followup}</p>{watch_task}</dd></div></dl>
    </section>
    <footer class="source">{source(d)}</footer>{materials(d)}
    </main>'''


def meeting_lanes(d):
    target=d["gaps"][1:3]
    stated={r["id"] for r in d["gaps"][:3]}
    watch=sorted((r for r in d["rows"] if r["sameStoreGrowth"]<0 and r["id"] not in stated),
                 key=lambda r:r["sameStoreGrowth"])
    gap_rows=''.join(f'<div><dt>{esc(r["name"])}</dt><dd>{esc(amount(r["gap"],d))}</dd></div>'
                     for r in target)
    same_rows=''.join(f'<div><dt>{esc(r["name"])}</dt><dd>{signed(r["sameStoreGrowth"])}</dd></div>'
                     for r in watch)
    if not same_rows:
        same_rows='<p class="no-watch">其余市场暂无同店下降。</p>'
    return f'''<div class="review-lanes">
      <section><h3>目标差额 · 第二、三位</h3><dl>{gap_rows}</dl><p>按目标与实际核对缺口。</p></section>
      <section><h3>{esc(d["metric"])}同比 · 其余市场</h3><dl>{same_rows}</dl><p>按同店名单核对覆盖与降幅。</p></section>
    </div>'''


def slides(d):
    lead=d["lead"]
    name=esc(lead["name"])
    other_markets="、".join(esc(row["name"]) for row in d["gaps"][1:3])
    stated={r["id"] for r in d["gaps"][:3]}
    watch="、".join(esc(row["name"]) for row in sorted(d["rows"],key=lambda r:r["sameStoreGrowth"])
                   if row["sameStoreGrowth"]<0 and row["id"] not in stated)
    due=f'{other_markets}的目标缺口' + (f'，{watch}的同店降幅' if watch else '')
    bound=max(abs(lead["growth"]),abs(lead["sameStoreGrowth"]))
    paired=[]
    for label,value in [("全量营业额同比",lead["growth"]),(f'{d["metric"]}同比',lead["sameStoreGrowth"])]:
        side="up" if value>=0 else "down"
        paired.append(f'<div class="signed-row"><span>{esc(label)}</span><b class="{side}">{signed(value)}</b>'
                      f'<div class="signed-plot {side}"><i style="width:{abs(value)/bound*.48:.8%}"></i></div></div>')
    body = [
        f'''<div class="opening-main"><div><h1>目标缺口，<br>先查{name}</h1>
        <p>全区本期还差 {esc(amount(d["gap"],d))}。</p></div>
        <div class="opening-proof"><strong>{d["share"]:.0f}<small>%</small></strong><p>{name}占全区缺口</p>{focus_track(d)}</div></div>''',
        f'''<h2>{name}总额增长，同店却在下降</h2>
        <div class="slide-comparison"><div class="market-trajectory"><p>{name}营业额 · {esc(d["unit"])}</p>
          <strong>{display(lead["prior"])} <small>→</small> {display(lead["revenue"])}</strong>
          <span>上年同月 → 本期</span><p>本期目标 {display(lead["target"])}，达成 {percentage(lead["revenue"],lead["target"]):.1f}%。</p></div>
          <div class="signed-chart">{''.join(paired)}<p>0</p></div></div>
        <p class="slide-takeaway">拆出同店、新开和退出门店各贡献多少增量。</p>''',
        f'''<h2>目标缺口与同店下行分开核查</h2>{meeting_lanes(d)}
        <p class="slide-takeaway">{name}优先，区域同时跟进差额靠前和同店下行的市场。</p>''',
        f'''<h2>会上确认两项分工</h2><div class="slide-decisions">
        <article><h3>{name}营运</h3><strong>门店差额清单</strong>
          <dl><div><dt>核对</dt><dd>门店本期实际与目标</dd></div><div><dt>另列</dt><dd>下月改善措施、估算金额与依据</dd></div></dl></article>
        <article><h3>区域分析</h3><strong>市场缺口与增量拆分表</strong>
          <dl><div><dt>核对</dt><dd>{due}</dd></div><div><dt>区分</dt><dd>同店、新开、退出门店与口径变化的影响</dd></div></dl></article></div>
        <p class="slide-takeaway"><span>下次复盘</span>　按门店差额和改善估算，确定优先门店及核查指标。</p>'''
    ]
    return '<main class="deck-wrap"><div class="deck">' + ''.join(
        f'<section class="slide slide-{i}" data-slide>{mast(d,"区域经营会议")}{html}'
        f'<footer class="slide-foot"><span>{source(d)}</span><span>{i:02d} / 04</span></footer></section>'
        for i,html in enumerate(body,1)) + '''</div>
        <nav class="deck-controls" aria-label="翻页"><button id="previous" aria-label="上一页">←</button>
        <output id="page" aria-live="polite"></output><button id="next" aria-label="下一页">→</button>
        <a href="#materials">数据</a></nav>''' + materials(d) + '</main>'


def build(raw):
    d=reviewed(raw)
    if d is None:
        return None
    market_data={row["id"]:dict(name=row["name"],increment=amount_delta(row["contribution"],d),same=signed(row["sameStoreGrowth"]),
                    gap=amount(row["gap"],d),attainment=percentage(row["revenue"],row["target"])) for row in d["gaps"]}
    spec,_=make_spec(raw)
    theme=theme_css('graphite',brand_accent='#923C38')
    labels=['营业额增量','各市场差额',f'全量与{d["metric"]}同比']
    exports=[]
    for chart, label in zip(spec["charts"],labels):
        if chart["kind"] == "waterfall":
            chart["rows"][0]["label"]="上年同期"
            chart["rows"][-1]["label"]="本期"
        if chart["kind"] == "scatter":
            chart["y_unit"]=f'{d["metric"]}同比（%）'
        svg,_=svg_chart(chart)
        link=data_url(static_svg(svg,theme,chart),'image/svg+xml;charset=utf-8')
        exports.append(f'<a href="{link}" download="{chart["id"]}.svg">{esc(label)} SVG</a>')
    css=(ASSETS/"operating-gap-review.css").read_text(encoding="utf-8")
    js=(ASSETS/"operating-gap-review.js").read_text(encoding="utf-8")
    return {
        f'{mode}.html': (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
                       f'<meta name="viewport" content="width=device-width,initial-scale=1">'
                       f'<title>{title} · {esc(d["date"])}</title><style>{css}</style></head>'
                       f'<body class="mode-{mode}">{render(dict(d,downloads=exports[1] if mode=="brief" else "".join(exports)))}'
                       f'<script type="application/json" id="source-data">{safe_json(raw)}</script>'
                       f'<script type="application/json" id="market-data">{safe_json(market_data)}</script>'
                       f'<script>{js}</script></body></html>')
        for mode,title,render in [('brief','经营简报',brief),('report','经营复盘',report),('slides','区域经营会议',slides)]
    }
