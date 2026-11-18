"""Compose original offline reading reports and HTML slide decks from chart contracts.

Only the Python standard library is required. Narrative is supplied, never inferred.
"""
import argparse
import base64
import json
from pathlib import Path
import re
import sys

from chart_html import CSS, KIND_NAMES, canonical, digest, esc, fmt, require, svg_chart, theme_credit, theme_css, validate
from custom_chart import registry_for, render_variant, validate_spec


def data_url(content, media):
    return f'data:{media};base64,' + base64.b64encode(content.encode('utf-8')).decode('ascii')


def safe_json(obj):
    return canonical(obj).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def static_svg(svg, theme, chart=None, *, palette_credit=''):
    """Export a static, standalone SVG with resolved colors and system typography."""
    colors = dict(re.findall(r'--([\w-]+):(#[0-9a-fA-F]+)', theme.split('@media print')[0]))
    svg = re.sub(r'var\(--([\w-]+)\)', lambda m: colors[m[1]], svg)
    style = f'<style>text{{font-family:Arial,"Microsoft YaHei",sans-serif;font-size:14px;fill:{colors["ink"]}}}.tick{{fill:{colors["muted"]}}}.value,.legend{{font-weight:600}}</style>'
    metadata = ''
    if chart is not None:
        metadata = f'<desc>来源：{esc(chart["source"])}；期间：{esc(chart["period"])}；范围：{esc(chart["scope"])}；单位：{esc(chart["unit"])}。缺失值未替换为零。</desc><metadata id="chart-source">{esc(canonical(chart))}</metadata>'
    if palette_credit:
        metadata += f'<metadata id="palette-credit">{esc(palette_credit)}</metadata>'
    if not re.search(r'<svg\b[^>]*\bxmlns=', svg):
        svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    return svg.replace('>', '>' + style + metadata, 1)


def validate_composition(spec, renderers=None):
    result = validate_spec(spec, renderers)
    composition = spec.get('composition', {})
    require(isinstance(composition, dict), 'composition must be an object')
    for key in ['subtitle', 'summary', 'closing']:
        require(key not in composition or isinstance(composition[key], str), f'composition.{key} must be text')
    sections = composition.get('sections')
    if sections is not None:
        require(isinstance(sections, list) and sections, 'composition.sections must be a nonempty list')
        ids = {c['id'] for c in spec['charts']}
        used = []
        for section in sections:
            require(isinstance(section, dict), 'section must be an object')
            require(isinstance(section.get('title'), str) and section['title'].strip(), 'section title required')
            require(isinstance(section.get('intro', ''), str), 'section intro must be text')
            require(section.get('layout', 'feature') in {'feature', 'comparison', 'sequence'}, 'section layout must be feature/comparison/sequence')
            require(isinstance(section.get('charts'), list) and section['charts'], 'section charts required')
            require(all(isinstance(cid, str) and cid in ids for cid in section['charts']), 'unknown chart in composition')
            require(section.get('layout') != 'comparison' or len(section['charts']) == 2, 'comparison requires exactly two charts')
            used.extend(section['charts'])
        require(len(used) == len(ids) and set(used) == ids, 'composition must include every chart exactly once')
    return result


def sections_for(spec):
    if 'sections' in spec.get('composition', {}):
        return spec['composition']['sections']
    # Structural grouping only. No computed business headline or relationship claim.
    result = []
    for chart in spec['charts']:
        result.append({'title': chart['question'], 'charts': [chart['id']],
                       'layout': 'feature' if chart['kind'] in {'line', 'bar'} else 'sequence'})
    return result


def chart_panel(c, index, theme, renderer=None, *, palette_credit=''):
    if renderer is not None:
        return custom_chart_panel(c, index, theme, renderer, palette_credit=palette_credit)
    desktop, ledger = svg_chart(c)
    mobile, mobile_ledger = svg_chart(c, True)
    compact, compact_ledger = svg_chart(c, compact=True)
    fields = list(dict.fromkeys(k for row in c['rows'] for k in row))
    names = {'label': '对象', 'value': '数值', 'group': '分组', 'parts': '构成（原始值）', 'role': '增减类型', 'highlight': '重点标记', 'x': '日期' if c['kind'] == 'line' else c.get('x_unit', '横轴'), 'y': c.get('y_unit', '纵轴')}
    heads = ''.join(f'<th scope="col">{esc(names.get(k, k))}</th>' for k in fields)
    rows = ''.join('<tr>' + ''.join(f'<td>{esc(fmt(row.get(k)))}</td>' for k in fields) + '</tr>' for row in c['rows'])
    missing = sum(1 for r in c['rows'] if (r.get('value') is None if c['kind'] not in {'stacked', 'scatter'} else c['kind'] == 'scatter' and (r['x'] is None or r['y'] is None)))
    notes = c.get('note', '')
    if missing:
        notes += f' 含{missing}条缺失记录；未替换为零。'
    if c['kind'] == 'box':
        notes += ' 分位数采用线性插值；须为1.5×IQR内最远原始值；n为非缺失观测数。'
    if c['kind'] == 'waterfall':
        notes += {'neutral': ' 颜色区分增减，不判断好坏。', 'higher': ' 数值越高越有利。', 'lower': ' 数值越低越有利。'}[c.get('performance_direction', 'neutral')]
    unit = '占比（%）；原始值：' + c['unit'] if c['kind'] == 'stacked' and c.get('percent') else c['unit']
    claims = ''.join(f'<p class="verified">{esc({"sum":"合计","mean":"平均","median":"中位数","count":"有效记录数"}[cl["method"]])} <strong>{esc(fmt(cl["expected"]))}</strong>{"" if cl["method"] == "count" else " " + esc(c["unit"])}</p>' for cl in c.get('claims', []))
    table = f'<details class="source-table"><summary>同源数据 · {len(c["rows"])}条</summary><div class="table-scroll"><table><caption>{esc(c["scope"])} · {esc(c["unit"])}</caption><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table></div></details>'
    export = data_url(static_svg(desktop, theme, c, palette_credit=palette_credit), 'image/svg+xml;charset=utf-8')
    panel = f'<article class="chart-panel kind-{c["kind"]}" data-chart-id="{esc(c["id"])}"><div class="chart-heading"><span class="eyebrow">{index:02d} / {KIND_NAMES[c["kind"]]}</span><h3>{esc(c["title"])}</h3><p class="question">{esc(c["question"])}</p><p class="scope">{esc(c["period"])} · {esc(unit)}</p>{claims}</div><figure>{desktop}{mobile}<figcaption>{esc(notes)}</figcaption></figure><p class="provenance">来源：{esc(c["source"])}<br>期间：{esc(c["period"])} · 范围：{esc(c["scope"])} · 单位：{esc(unit)}</p><div class="chart-tools"><a href="{export}" download="chart-{index:02d}.svg">下载静态SVG</a>{table}</div></article>'
    panel=panel.replace(f'{desktop}{mobile}',f'{desktop}{mobile}<div class="compact-chart">{compact}</div>')
    return panel, {'desktop': ledger, 'mobile': mobile_ledger, 'compact': compact_ledger, 'data_sha256': digest(c['rows'])}


def custom_chart_panel(c, index, theme, renderer, *, palette_credit=''):
    variants = {variant: render_variant(c, renderer, variant, theme)
                for variant in ['desktop', 'mobile', 'compact']}
    desktop = variants['desktop']
    for result in variants.values():
        require(canonical(sorted(result.coverage, key=lambda row: row['row_index'])) == canonical(sorted(desktop.coverage, key=lambda row: row['row_index'])), 'custom variants must preserve the same coverage')
        require(result.table_fields == desktop.table_fields, 'custom variants must preserve the same table fields')
    fields = desktop.table_fields
    heads = ''.join(f'<th scope="col">{esc(k)}</th>' for k in fields)
    rows = ''.join('<tr>' + ''.join(f'<td>{esc(fmt(row.get(k))) if k in row else "未提供字段"}</td>' for k in fields) + '</tr>' for row in c['rows'])
    notes = c.get('note', '')
    require(isinstance(notes, str), 'custom note must be text')
    for status, name in [('missing', '缺失'), ('excluded', '排除')]:
        records = [item for item in desktop.coverage if item['status'] == status]
        if records:
            notes += f' {name}{len(records)}条：' + '；'.join(f'第{item["row_index"]+1}条 {item["reason"]}' for item in records) + '。'
    table = f'<details class="source-table"><summary>同源数据 · {len(c["rows"])}条</summary><div class="table-scroll"><table><caption>{esc(c["scope"])} · {esc(c["unit"])}</caption><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table></div></details>'
    export = data_url(static_svg(desktop.export_svg, theme, c, palette_credit=palette_credit), 'image/svg+xml;charset=utf-8')
    panel = f'<article class="chart-panel kind-{esc(c["kind"])}" data-chart-id="{esc(c["id"])}"><div class="chart-heading"><span class="eyebrow">{index:02d} / {esc(renderer.label)}</span><h3>{esc(c["title"])}</h3><p class="question">{esc(c["question"])}</p><p class="scope">{esc(c["period"])} · {esc(c["unit"])}</p></div><figure>{desktop.svg}{variants["mobile"].svg}<div class="compact-chart">{variants["compact"].svg}</div><figcaption>{esc(notes)}</figcaption></figure><p class="provenance">来源：{esc(c["source"])}<br>期间：{esc(c["period"])} · 范围：{esc(c["scope"])} · 单位：{esc(c["unit"])}</p><div class="chart-tools"><a href="{export}" download="chart-{index:02d}.svg">下载静态SVG</a>{table}</div></article>'
    ledger = {variant: result.ledger for variant, result in variants.items()}
    ledger.update(coverage=desktop.coverage, table_fields=fields, data_sha256=digest(c['rows']),
                  export={'variant': 'desktop', 'coverage': desktop.coverage, 'data_sha256': digest(c['rows'])})
    return panel, ledger


COMPOSE_CSS = r'''
body{font-size:16px;line-height:1.65}h1,h2,h3,p{overflow-wrap:anywhere}a{ text-underline-offset:4px}header,main,footer{max-width:1300px;padding:40px 56px}header{padding-top:64px}.edition{display:flex;gap:24px;align-items:center;border-top:4px solid var(--accent);padding-top:15px}.edition span:last-child{margin-left:auto}header h1{font-size:clamp(34px,4.8vw,66px);max-width:1000px;margin:30px 0 22px;letter-spacing:-.04em}.subtitle{font-size:20px;max-width:830px;color:var(--muted)}.summary{max-width:900px;font-size:21px;border-left:3px solid var(--accent);padding:4px 0 4px 22px}.disclosure{font-size:13px;color:var(--muted)}.toolbar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:24px 0}.toolbar a,.chart-tools>a,.slide-index button{font-size:14px}.toc{display:flex;flex-wrap:wrap;gap:10px 25px;border-top:1px solid var(--rule);padding-top:20px;margin-top:32px}.toc a{font-size:14px}.chapter{margin:0 0 70px;padding-top:24px;border-top:1px solid var(--ink)}.chapter-heading{display:grid;grid-template-columns:70px 1fr;gap:10px 20px;margin-bottom:30px}.chapter-no{font-size:35px;line-height:1.2;color:var(--accent)}.chapter h2{margin:0;font-size:30px;line-height:1.3;max-width:950px}.chapter-intro{grid-column:2;max-width:850px;margin:4px 0;color:var(--muted);font-size:17px}.chart-panel{min-width:0}.chart-panel h3{font-size:26px;line-height:1.35;margin:8px 0 12px}.question{color:var(--muted);font-size:15px;margin:0 0 7px}.scope{font-size:13px;margin:0 0 14px}.chart-panel figure{margin:0;min-width:0}.chart-panel figcaption{font-size:14px;line-height:1.7;margin:16px 0;color:var(--muted)}.provenance{font-size:12px;color:var(--muted);border-top:1px solid var(--rule);padding-top:12px;overflow-wrap:anywhere}.chart-tools{margin-top:14px}.source-table{margin-top:12px}.verified{font-size:15px;margin:10px 0}.verified strong{font-size:28px;color:var(--accent);margin-left:10px}.layout-feature .chart-panel{display:grid;grid-template-columns:minmax(190px,1fr) minmax(0,3.2fr);column-gap:35px}.layout-feature .chart-heading{grid-row:1/4}.layout-feature .chart-panel figure{grid-column:2}.layout-feature .provenance,.layout-feature .chart-tools{grid-column:2}.layout-comparison .chart-group{display:grid;grid-template-columns:1fr 1fr;gap:38px}.layout-comparison .chart-panel h3{font-size:23px}.layout-comparison .desktop-svg{display:none}.layout-comparison .mobile-svg{display:block}.layout-comparison .chart-heading{min-height:165px}.layout-sequence .chart-heading{max-width:800px}.layout-sequence .chart-panel+.chart-panel{margin-top:50px}.closing{font-size:22px;max-width:900px;border-top:3px solid var(--accent);padding-top:24px}.digest{font-size:12px;overflow-wrap:anywhere;color:var(--muted)}.slide-frame{background:var(--paper);border-top:4px solid var(--accent);padding:44px 48px;margin:0 0 40px;aspect-ratio:16/9;min-height:0;position:relative;display:flex;flex-direction:column;overflow:visible}.slide-frame h2{font-size:32px;line-height:1.3;margin:0 0 15px}.slide-topline{display:flex;justify-content:space-between;gap:15px;margin-bottom:18px;color:var(--muted);font-size:12px}.slide-frame .chart-panel{display:grid;grid-template-columns:minmax(190px,1fr) minmax(0,2.5fr);gap:0 26px}.slide-frame .chart-heading{grid-row:1/3}.slide-frame .chart-panel h3{font-size:26px}.slide-frame figure,.slide-frame .provenance,.slide-frame .chart-tools{grid-column:2}.slide-frame .provenance{margin:8px 0 0}.slide-frame figcaption{margin:8px 0;font-size:13px}.slide-frame .chart-tools{margin-top:8px}.slide-frame .chart-tools>a{font-size:12px}.slide-frame .source-table{font-size:13px}.slide-frame .scope{font-size:12px}.slide-frame .chart-panel{flex:1}.cover h1{font-size:clamp(32px,4vw,55px);line-height:1.2;max-width:960px;margin:8px 0 20px;letter-spacing:-.04em}.cover .summary{font-size:18px}.slide-index{display:grid;grid-template-columns:1fr 1fr;gap:0 28px;margin-top:auto;padding-top:20px}.slide-index button{text-align:left;border:0;border-top:1px solid var(--rule);border-radius:0;background:transparent;padding:12px 0;display:flex;gap:14px}.slide-index b{color:var(--accent)}body.mode-slides main{padding-top:14px}.deck-controls{position:sticky;top:0;z-index:5;background:var(--bg);padding:12px 0;border-bottom:1px solid var(--rule);margin-bottom:20px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}.deck-controls button{padding:7px 12px;font-size:14px}.deck-controls .counter{margin-left:auto;font-variant-numeric:tabular-nums;color:var(--muted);font-size:14px}.js-deck:not(.overview) .slide-frame:not(.current){display:none}.js-deck.overview .slide-frame{display:flex}.mode-slides>header{padding-top:26px;padding-bottom:0}.mode-slides>header .edition{font-size:12px}.mode-slides>header .toolbar{margin-bottom:0}.mode-slides>footer{padding-top:0}.mode-report .deck-controls{display:none}noscript{display:block;font-size:13px;color:var(--muted)}button:disabled{opacity:.45;cursor:default}
.slide-frame{aspect-ratio:auto;min-height:calc(min(100vw - 112px,1188px) * .5625)}.slide-frame .chart-panel{flex:none}.slide-frame figure{align-self:start}
@media(min-width:901px){.mode-slides .slide-frame .chart-panel{grid-template-columns:minmax(200px,1fr) minmax(0,2.5fr)}.mode-slides .slide-frame svg text,.mode-slides .slide-frame svg .tick,.mode-slides .slide-frame svg .value,.mode-slides .slide-frame svg .legend{font-size:16px}}
@media(max-width:900px){header,main,footer{padding:30px}.layout-feature .chart-panel{grid-template-columns:1fr 2.4fr;gap:20px}.slide-frame{padding:28px;aspect-ratio:auto;min-height:56vw}.slide-frame .chart-panel{display:block!important}.slide-frame .chart-panel h3{font-size:26px}.slide-frame figure{margin-top:20px}.slide-frame .chart-heading{max-width:100%}}
@media(max-width:700px){header,main,footer{padding:24px 18px}header{padding-top:32px}.edition{gap:12px}.edition span:last-child{font-size:10px}header h1{font-size:36px}.subtitle{font-size:17px}.summary{font-size:18px;padding-left:15px}.toc{display:grid;gap:13px}.chapter{margin-bottom:44px}.chapter-heading{grid-template-columns:40px 1fr;gap:10px}.chapter-no{font-size:28px}.chapter h2{font-size:25px}.chapter-intro{font-size:16px}.layout-feature .chart-panel,.layout-comparison .chart-group{display:block}.layout-comparison .chart-panel+.chart-panel{margin-top:40px}.layout-comparison .chart-heading{min-height:0}.chart-panel h3,.layout-comparison .chart-panel h3{font-size:24px}.chart-panel figcaption{font-size:14px}.slide-frame{padding:22px 14px;border-top-width:3px;min-height:0;margin-bottom:25px}.cover h1{font-size:30px}.cover .summary{font-size:17px}.slide-index{grid-template-columns:1fr}.slide-topline{font-size:11px}.deck-controls{gap:7px}.deck-controls button{font-size:13px;padding:7px 9px}.deck-controls .counter{font-size:12px}.slide-frame .chart-panel h3{font-size:24px}.slide-frame figcaption{font-size:14px}.closing{font-size:19px}}
@media print{@page{size:A4 landscape;margin:12mm}body{background:white;font-size:12px}header,main,footer{max-width:none;padding:0}.toolbar,.deck-controls,.toc,.chart-tools>a,.source-table{display:none!important}.chapter{break-before:page;margin:0 0 20px}.chapter:first-child{break-before:auto}.layout-feature .chart-panel{display:block}.layout-comparison .chart-group{display:grid;grid-template-columns:1fr 1fr;gap:25px}.chart-panel{break-inside:avoid}.chapter-heading{margin-bottom:15px}.chart-panel h3{font-size:22px}.chart-panel figure{max-width:800px}.desktop-svg{display:block}.mobile-svg{display:none}.slide-frame,.js-deck:not(.overview) .slide-frame:not(.current){display:flex!important;aspect-ratio:auto;min-height:170mm;break-before:page;break-after:page;padding:15px 22px;margin:0;border:0;border-top:3px solid var(--accent)}.slide-frame:first-child{break-before:auto}.mode-slides>header,.mode-slides>footer{display:none}.slide-frame .chart-panel{display:grid!important;grid-template-columns:1fr 2fr!important;gap:25px}.mode-slides .slide-frame .mobile-svg{display:none}.mode-slides .slide-frame .desktop-svg{display:block}.slide-frame .chart-panel h3{font-size:23px}.slide-frame figcaption{font-size:12px}.slide-index button{font-size:14px;color:var(--ink)}.slide-frame .chart-tools{display:none}.cover .summary{font-size:18px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
@media print{.mode-report>header{break-after:page}.mode-report .chapter{break-inside:avoid}.mode-report .chapter-heading{margin-bottom:16px}.mode-report .chapter h2{font-size:24px}.mode-report .chapter-intro{font-size:13px}.mode-report .layout-feature .chart-panel{display:grid;grid-template-columns:1fr 3fr;gap:20px}.mode-report .chart-panel h3{font-size:20px}.mode-report .question{font-size:12px}.mode-report .chart-panel figcaption{font-size:11px;margin:8px 0}.mode-report .provenance{font-size:10px;margin:7px 0}.mode-report .layout-comparison .chart-heading{min-height:0}.mode-report .layout-comparison .desktop-svg{display:block}.mode-report .layout-comparison .mobile-svg{display:none}.mode-report .layout-sequence figure{max-width:740px}.mode-report .chart-tools{display:none}.mode-report .layout-sequence .chart-heading{max-width:none}.mode-report .layout-sequence .chart-panel{display:grid;grid-template-columns:1fr 3fr;gap:0 20px}.mode-report .layout-sequence .chart-heading{grid-row:1/3}.mode-report .layout-sequence figure,.mode-report .layout-sequence .provenance{grid-column:2}}
@media print{.mode-report>footer{break-inside:avoid}.mode-report>footer p{font-size:11px;margin:6px 0}.mode-report>footer .closing{font-size:14px;padding-top:10px;margin-top:10px}.mode-report>footer .digest{font-size:9px}}
.resources{margin:10px 0 22px;padding:12px 16px;border:1px solid var(--rule);font-size:14px}.resources>summary{font-size:14px}.resource-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px 30px;margin-top:22px}.resource-grid section{min-width:0;border-top:1px solid var(--rule);padding-top:12px}.resource-grid h2{font-size:18px;line-height:1.4}.resource-grid .source-table{font-size:14px}.slide-frame .provenance{font-size:13px;line-height:1.6}.slide-frame .scope{font-size:13px}.slide-frame .chart-tools{display:none}.slide-full .chart-panel{display:block!important}.slide-full .chart-heading{display:grid;grid-template-columns:1fr auto;gap:0 25px}.slide-full .chart-heading .eyebrow,.slide-full .chart-heading h3{grid-column:1/-1}.slide-full .chart-heading h3{font-size:30px;margin:6px 0 9px}.slide-full .scope{text-align:right}.slide-full figure{max-width:920px;margin:18px auto 0}.slide-full .provenance{margin-top:14px}.slide-evidence .chart-panel{display:grid!important;grid-template-columns:1.7fr 1fr;gap:0 24px!important}.slide-evidence .chart-heading{grid-column:1/-1;grid-row:auto;display:grid;grid-template-columns:1fr auto;gap:0 25px}.slide-evidence .chart-heading .eyebrow,.slide-evidence .chart-heading h3{grid-column:1/-1}.slide-evidence .chart-heading h3{font-size:30px;margin:6px 0 9px}.slide-evidence .scope{text-align:right}.slide-evidence figure{display:contents}.slide-evidence figure svg{grid-column:1/-1;max-width:900px;justify-self:center;margin:10px 0 18px}.slide-evidence figcaption{grid-column:1;border-top:2px solid var(--accent);padding:14px 16px;background:var(--bg);margin:0;font-size:14px}.slide-evidence .provenance{grid-column:2;border-top:2px solid var(--accent);padding:14px 16px;background:var(--bg);margin:0;font-size:13px}.slide-full .chart-panel h3,.slide-evidence .chart-panel h3{font-size:30px}
@media(max-width:900px){.slide-full .chart-heading,.slide-evidence .chart-heading{display:block}.slide-full .scope,.slide-evidence .scope{text-align:left}.slide-evidence .chart-panel{display:block!important}.slide-evidence figure{display:block}.slide-evidence figure svg{margin:10px 0 18px}.slide-evidence .provenance{margin-top:12px}.slide-frame .provenance,.slide-frame .scope{font-size:13px}.slide-full .chart-panel h3,.slide-evidence .chart-panel h3{font-size:26px}}
@media(max-width:700px){.resource-grid{display:block}.resource-grid section{margin-top:20px}.slide-full .chart-panel h3,.slide-evidence .chart-panel h3{font-size:24px}.resources{padding:12px}.slide-frame .provenance{font-size:12px}.slide-frame .scope{font-size:13px}}
.slide-frame{scroll-margin-top:100px}.mode-slides .slide-frame.slide-evidence .chart-panel{grid-template-columns:1.7fr 1fr}
.projection-warning{font-size:13px;color:var(--negative);margin-left:10px}.projection-warning:empty{display:none}
@media(min-width:901px){body.projection{overflow:hidden}body.projection>header,body.projection>footer,.projection .resources{display:none}.projection main{max-width:none;padding:0}.projection .deck-controls{height:56px;margin:0;padding:8px 16px;position:static}.projection #stage{padding:12px 16px}.projection .slide-frame{height:calc(100dvh - 80px);min-height:0;margin:0;padding:22px 30px;scroll-margin:0}.projection .slide-topline{display:none}.projection .chart-heading>.eyebrow{display:none}.projection .chart-panel h3{font-size:28px;margin:0 0 10px}.projection .chart-heading .question,.projection .chart-heading .scope{margin-bottom:8px}.projection .chart-heading{grid-row:1/3}.projection .slide-frame .chart-panel{flex:1;min-height:0;grid-template-rows:minmax(0,1fr) auto;gap:0 24px}.projection .slide-frame figure{display:flex;flex-direction:column;min-height:0;align-self:stretch;margin:0;max-width:none}.projection .slide-frame figure svg{flex:1;min-height:0;height:0;width:100%;max-width:none;max-height:none;margin:0}.projection .slide-frame figure .mobile-svg{display:none}.projection .slide-frame figcaption{flex:none;margin:8px 0;font-size:13px;line-height:1.5}.projection .slide-frame .provenance{font-size:12px;line-height:1.5;padding-top:8px;margin:8px 0 0}.projection .slide-full .chart-panel{display:flex!important;flex-direction:column}.projection .slide-full .chart-heading{flex:none;display:grid;grid-template-columns:1fr auto}.projection .slide-full figure{flex:1;margin:0}.projection .slide-full .provenance{flex:none}.projection .slide-evidence .chart-panel{display:grid!important;grid-template-columns:1.7fr 1fr;grid-template-rows:auto minmax(0,1fr) auto}.projection .slide-evidence .chart-heading{grid-column:1/-1;grid-row:1;display:grid;grid-template-columns:1fr auto}.projection .slide-evidence figure{display:contents}.projection .slide-evidence figure svg{grid-column:1/-1;grid-row:2;height:100%;width:100%;min-height:0;max-height:100%;margin:0}.projection .slide-evidence figure .mobile-svg{display:none}.projection .slide-evidence figcaption{grid-row:3;grid-column:1;margin:8px 0 0;padding:10px 12px}.projection .slide-evidence .provenance{grid-row:3;grid-column:2;padding:10px 12px}.projection .cover{justify-content:space-between}.projection .cover h1{font-size:40px}.projection .cover .summary{font-size:18px}.projection .slide-index{padding-top:10px}.projection .slide-index button{padding:9px 0}}
@media(max-width:900px){#projection{display:none}}
@media(min-width:901px){body.mode-slides.projection main{padding:0;max-width:none}}
@media print{.resources{display:none!important}.slide-full .chart-heading,.slide-evidence .chart-heading{display:block}.slide-full .scope,.slide-evidence .scope{text-align:left}.slide-full .chart-panel,.slide-evidence .chart-panel{display:block!important}.slide-full figure,.slide-evidence figure{display:block;max-width:760px;margin:10px auto}.slide-full .chart-panel h3,.slide-evidence .chart-panel h3{font-size:23px}.slide-full .provenance,.slide-evidence .provenance,.slide-evidence figcaption{font-size:11px;padding:8px;margin:6px 0;border-top:1px solid var(--rule);background:white}.slide-full figure svg,.slide-evidence figure svg{max-width:760px;max-height:340px;margin:0 auto}.slide-full .chart-heading .question,.slide-evidence .chart-heading .question{display:inline;margin-right:25px}.slide-full .scope,.slide-evidence .scope{display:inline;font-size:12px}}
@media print{body.projection{overflow:visible}.projection .slide-frame{height:auto;min-height:170mm}.projection .slide-frame .chart-panel{flex:none}.projection .slide-frame figure svg{height:auto;min-height:0;max-height:340px}.projection .slide-frame .chart-heading .eyebrow{display:block}.projection .slide-frame .chart-heading{display:block}.projection .slide-frame .chart-panel{display:block!important}.projection .slide-evidence figure{display:block}.projection .slide-evidence figure svg{height:auto}.projection .cover{display:flex}}
@media screen and (min-width:901px){
  .projection #stage{display:grid;justify-items:center;align-items:center;height:calc(100dvh - 56px);padding:12px 16px}
  .projection .slide-frame{width:min(calc(100vw - 32px),calc((100dvh - 80px) * 16 / 9));height:auto;aspect-ratio:16 / 9}
}
'''


DECK_JS = r'''
const frames=[...document.querySelectorAll('.slide-frame')];
if(frames.length){
 document.body.classList.add('js-deck');let index=0,overview=false;
 const counter=document.getElementById('counter'),prev=document.getElementById('previous'),next=document.getElementById('next'),all=document.getElementById('overview'),project=document.getElementById('projection');
 function checkProjection(){requestAnimationFrame(()=>{const f=frames[index],active=document.body.classList.contains('projection');const tiny=[...f.querySelectorAll('svg')].filter(s=>getComputedStyle(s).display!=='none').some(s=>s.getBoundingClientRect().height<140||[...s.querySelectorAll('text')].some(t=>parseFloat(getComputedStyle(t).fontSize)*Math.abs(t.getScreenCTM().a)<12));document.getElementById('projection-warning').textContent=active&&(f.scrollHeight>f.clientHeight+1||tiny)?'内容较长，请切回阅读模式查看。':'';});}
 function show(n,scroll=false){index=Math.max(0,Math.min(frames.length-1,n));if(overview&&document.body.classList.contains('projection')){document.body.classList.remove('projection');project.textContent='聚焦投影';project.setAttribute('aria-pressed','false')}frames.forEach((f,i)=>{f.classList.toggle('current',i===index);f.setAttribute('aria-hidden',String(!overview&&i!==index));f.inert=!overview&&i!==index});counter.textContent=`${index+1} / ${frames.length}`;prev.disabled=index===0;next.disabled=index===frames.length-1;document.body.classList.toggle('overview',overview);all.setAttribute('aria-pressed',String(overview));all.textContent=overview?'返回单页':'总览全部';if(scroll&&!document.body.classList.contains('projection'))frames[index].scrollIntoView({block:'start',behavior:'instant'});checkProjection();}
 project.onclick=()=>{const active=!document.body.classList.contains('projection');document.body.classList.toggle('projection',active);project.textContent=active?'返回阅读':'聚焦投影';project.setAttribute('aria-pressed',String(active));overview=false;show(index);window.scrollTo(0,0)};
 prev.onclick=()=>show(index-1);next.onclick=()=>show(index+1);all.onclick=()=>{overview=!overview;if(overview){document.body.classList.remove('projection');project.textContent='聚焦投影';project.setAttribute('aria-pressed','false')}show(index)};
 document.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>{overview=false;show(Number(b.dataset.go),true)});
 addEventListener('keydown',e=>{if(e.altKey||e.ctrlKey||e.metaKey||/INPUT|SELECT|TEXTAREA|BUTTON|SUMMARY|A/.test(document.activeElement.tagName))return;if(['ArrowRight','PageDown','ArrowLeft','PageUp','Home','End','Escape'].includes(e.key)){e.preventDefault();if(e.key==='Escape'){overview=!overview;show(index)}else{overview=false;show(e.key==='Home'?0:e.key==='End'?frames.length-1:index+(['ArrowRight','PageDown'].includes(e.key)?1:-1))}}});
 let start=null;const stage=document.getElementById('stage');stage.addEventListener('touchstart',e=>{if(e.target.closest('a,button,summary,.table-scroll'))return;start={x:e.changedTouches[0].clientX,y:e.changedTouches[0].clientY}},{passive:true});stage.addEventListener('touchend',e=>{if(!start)return;const dx=e.changedTouches[0].clientX-start.x,dy=e.changedTouches[0].clientY-start.y;start=null;if(!overview&&Math.abs(dx)>70&&Math.abs(dx)>Math.abs(dy)*1.5)show(index+(dx<0?1:-1))},{passive:true});
 addEventListener('resize',()=>{if(innerWidth<=900){document.body.classList.remove('projection');project.textContent='聚焦投影';project.setAttribute('aria-pressed','false')}checkProjection()});
 let printState=null;addEventListener('beforeprint',()=>{printState={index,overview,projection:document.body.classList.contains('projection')};document.body.classList.remove('projection');overview=true;show(index)});addEventListener('afterprint',()=>{if(printState){overview=printState.overview;document.body.classList.toggle('projection',printState.projection);show(printState.index);printState=null}});show(0);
}
document.querySelectorAll('[data-print]').forEach(b=>b.onclick=()=>window.print());
document.documentElement.dataset.composeReady='true';
'''

REPORT_READING_CSS = {
    'brief': '''
.reading-brief>header,.reading-brief>main,.reading-brief>footer{padding-block:22px}
.reading-brief>header{margin:22px auto 0;padding-top:0}
.reading-brief>header::before{content:"";display:block;border-top:6px solid var(--accent)}
.reading-brief header h1{margin:13px 0 8px;font-size:clamp(32px,3.9vw,56px)}
.reading-brief .subtitle{font-size:16px}
.reading-brief .summary{margin:12px 0;padding:0 0 0 16px;font-size:19px}
.reading-brief .toolbar{margin:10px 0}
.reading-brief .toc{padding-top:12px;margin-top:12px}
.reading-brief .chapter{padding-top:15px;margin-bottom:36px}
.reading-brief .chapter-heading{display:block;margin-bottom:16px}
.reading-brief .chapter-no,.reading-brief .chart-heading>.eyebrow{display:none}
.reading-brief .chapter h2{font-size:24px}
.reading-brief .chapter-intro{font-size:15px}
.reading-brief .chart-panel h3{font-size:21px;margin-top:0}
.reading-brief .layout-comparison .chart-heading{min-height:122px}
@media print{
 @page{size:A4 portrait;margin:12mm}
 .mode-report.reading-brief>header{break-after:auto;margin:0}
 .mode-report.reading-brief .chapter{break-before:auto}
 .reading-brief .chart-panel .scope{font-size:10px}
 .reading-brief .digest{display:none}
}
''',
    'editorial': '''
.reading-editorial>header,.reading-editorial>main,.reading-editorial>footer{max-width:1180px}
.reading-editorial>header{padding-block:45px 20px}
.reading-editorial>main{padding-top:18px}
.reading-editorial>header::before{content:"";display:block;border-top:1px solid var(--ink)}
.reading-editorial header h1,.reading-editorial .chapter h2{
  font-family:"Songti SC","Noto Serif CJK SC",SimSun,Georgia,serif;letter-spacing:-.025em
}
.reading-editorial header h1{max-width:16em;line-height:1.14}
.reading-editorial .summary{border:0;padding:0;max-width:40em;font-size:20px}
.reading-editorial .chapter-heading{grid-template-columns:2.6rem 1fr;gap:7px 18px}
.reading-editorial .chapter-no{font:20px/1.5 Georgia,serif;color:var(--muted)}
.reading-editorial .chapter-intro{max-width:45em}
.reading-editorial .layout-feature .chart-panel{grid-template-columns:minmax(180px,1fr) minmax(0,3.8fr)}
.reading-editorial figcaption{padding-left:12px;border-left:1px solid var(--rule)}
@media(max-width:940px){
  .reading-editorial .layout-feature .chart-panel{grid-template-columns:1fr}
  .reading-editorial .layout-feature .chart-panel>*{grid-column:1;grid-row:auto}
}
''',
    'story': '''
.reading-story>header,.reading-story>footer{max-width:1080px}
.reading-story>header{padding-top:38px;padding-bottom:12px}
.reading-story>main{padding-top:20px}
.reading-story header h1{margin-top:0;max-width:18em;font-size:clamp(32px,4.3vw,61px);font-family:"Songti SC",SimSun,Georgia,serif}
.reading-story .summary{max-width:42em;border-left:0;padding-left:0;color:var(--ink)}
.reading-story .toc{margin-top:20px;padding-top:12px}
.reading-story .chapter{padding-top:32px;margin-bottom:70px}
.reading-story .chapter-heading{max-width:720px;margin:0 auto 28px;display:block}
.reading-story .chapter-no{display:none}
.reading-story .chapter h2{font-size:clamp(25px,3.3vw,42px)}
.reading-story .chapter-intro{margin:12px 0 0}
.reading-story .layout-feature .chart-panel{display:block}
.reading-story .layout-feature figure{margin:16px 0}
.reading-story .layout-feature .chart-heading{max-width:720px;margin-inline:auto}
.reading-story .layout-feature .provenance,.reading-story .layout-feature .chart-tools{max-width:720px;margin-inline:auto}
.reading-story .chart-panel .eyebrow{display:none}
''',
    'evidence': '''
.reading-evidence>header,.reading-evidence>main,.reading-evidence>footer{max-width:1320px}
.reading-evidence>header{padding-top:30px;padding-bottom:14px}
.reading-evidence header h1{font-size:clamp(29px,4.2vw,53px);margin:15px 0 10px}
.reading-evidence .chapter{border-top:1px solid var(--ink);margin-bottom:38px;padding-top:16px}
.reading-evidence .chapter-heading{grid-template-columns:42px 1fr;gap:6px 14px;margin-bottom:15px}
.reading-evidence .chapter-no{font-size:17px;line-height:1.7;color:var(--muted)}
.reading-evidence .chapter h2{font-size:24px}
.reading-evidence .chapter-intro{font-size:14px}
.reading-evidence .chart-panel h3{font-size:20px;margin:4px 0 7px}
.reading-evidence .chart-panel figure{padding-top:10px;border-top:1px solid var(--rule)}
.reading-evidence .chart-panel .eyebrow{display:none}
.reading-evidence .provenance{border-top:0;padding-top:3px}
.reading-evidence .layout-comparison .chart-heading{min-height:125px}
''',
}


def build(spec, mode='report', theme=None, *, renderers=None, reading=None, brand_accent=None, delivery=None):
    result = validate_composition(spec, renderers)
    registry = registry_for(renderers)
    require(mode in {'report', 'slides'}, 'mode must be report or slides')
    require(reading is None or (mode == 'report' and isinstance(reading, str) and reading in REPORT_READING_CSS),
            'reading requires report mode and a supported reading layout')
    reading_class = f' reading-{reading}' if reading else ''
    reading_css = REPORT_READING_CSS.get(reading, '')
    use_graphite = reading is not None or brand_accent is not None
    theme_id = theme or spec.get('theme', 'graphite' if use_graphite else 'tidal')
    selected = theme_css(theme_id, brand_accent=brand_accent)
    credit = theme_credit(theme_id)
    require(delivery in {None, 'final'}, 'delivery must be final when specified')
    if delivery == 'final':
        from report_delivery import build_final
        layout = 'deck' if mode == 'slides' else 'brief' if reading == 'brief' else 'report'
        return build_final(spec, layout, selected, credit, registry, result['sha256'])
    composition = spec.get('composition', {})
    panels, ledgers, resources = {}, {}, []
    for i, c in enumerate(spec['charts'], 1):
        panels[c['id']], ledgers[c['id']] = chart_panel(c, i, selected, registry.get(c['kind']), palette_credit=credit)
        if mode == 'slides':
            panel, tools = panels[c['id']].rsplit('<div class="chart-tools">', 1)
            panels[c['id']] = panel + '</article>'
            resources.append(f'<section><h2>{i:02d} · {esc(c["title"])}</h2>' + tools.removesuffix('</div></article>') + '</section>')
    source = canonical(spec)
    source_link = data_url(source, 'application/json;charset=utf-8')
    disclosure = '合成测试数据，仅用于演示；不是实际经营事实。' if spec.get('synthetic') else spec.get('data_note', '')
    toolbar = f'<div class="toolbar"><a href="{source_link}" download="source.json">下载完整源数据</a><button type="button" data-print>打印全部 / 另存PDF</button></div>'
    edition = f'<div class="edition"><span class="eyebrow">DATA / {"READING REPORT" if mode == "report" else "HTML PRESENTATION"}</span><span>{result["charts"]} 个图表 · {result["rows"]} 条输入记录</span></div>'
    if mode == 'report':
        sections = sections_for(spec)
        toc = '<nav class="toc" aria-label="章节">' + ''.join(f'<a href="#chapter-{i}">{i:02d} {esc(s["title"])}</a>' for i, s in enumerate(sections, 1)) + '</nav>'
        header = (edition if not reading else '') + f'<h1>{esc(spec["title"])}</h1><p class="subtitle">{esc(composition.get("subtitle", spec.get("intro", "")))}</p>'
        if composition.get('summary'):
            header += f'<p class="summary">{esc(composition["summary"])}</p>'
        header += f'<p class="disclosure">{esc(disclosure)}</p>'
        header += {'brief': '', 'story': toc}.get(reading, toolbar + toc)
        content = ''.join(f'<section class="chapter layout-{s.get("layout", "feature")}" id="chapter-{i}"><div class="chapter-heading"><span class="chapter-no">{i:02d}</span><h2>{esc(s["title"])}</h2><p class="chapter-intro">{esc(s.get("intro", ""))}</p></div><div class="chart-group">' + ''.join(panels[cid] for cid in s['charts']) + '</div></section>' for i, s in enumerate(sections, 1))
    else:
        header = edition + '<noscript>当前显示全部页面。按钮、键盘与滑动导航需要JavaScript；数据与图表可离线阅读。</noscript>'
        index = ''.join(f'<button type="button" data-go="{i}"><b>{i:02d}</b><span>{esc(c["question"])}</span></button>' for i, c in enumerate(spec['charts'], 1))
        if composition.get('closing'):
            index += f'<button type="button" data-go="{len(spec["charts"])+1}"><b>↳</b><span>阅读结论与边界</span></button>'
        content = '<nav class="deck-controls" aria-label="演示导航"><button id="previous" type="button">← 上一页</button><button id="next" type="button">下一页 →</button><button id="overview" type="button" aria-pressed="false">总览全部</button><button id="projection" type="button" aria-pressed="false">聚焦投影</button><span id="projection-warning" class="projection-warning" role="status"></span><span id="counter" class="counter" role="status" aria-live="polite"></span></nav>'
        content += '<details class="resources"><summary>资料与导出 · 源数据 / SVG / 同源表</summary>' + toolbar + '<div class="resource-grid">' + ''.join(resources) + '</div></details><div id="stage">'
        content += f'<section class="slide-frame cover current" aria-label="封面与目录"><div class="slide-topline"><span>阅读目录</span><span>00 / {len(spec["charts"])}</span></div><h1>{esc(spec["title"])}</h1><p class="subtitle">{esc(composition.get("subtitle", spec.get("intro", "")))}</p><p class="summary">{esc(composition.get("summary", ""))}</p><p class="disclosure">{esc(disclosure)}</p><div class="slide-index">{index}</div></section>'
        for i, c in enumerate(spec['charts'], 1):
            arrangement = 'full' if c['kind'] in {'line', 'waterfall'} else 'evidence' if c['kind'] in {'box', 'scatter'} else 'comparison'
            contexts=[s.get('intro','') for s in sections_for(spec) if c['id'] in s['charts'] and s.get('intro')]
            context='<p class="slide-context">'+esc(' '.join(contexts))+'</p>' if contexts else ''
            content += f'<section class="slide-frame slide-{arrangement}" aria-label="{i:02d} {esc(c["title"])}"><div class="slide-topline"><span>{esc(spec["title"])}</span><span>{i:02d} / {len(spec["charts"])}</span></div>{context}{panels[c["id"]]}</section>'
        if composition.get('closing'):
            content += f'<section class="slide-frame closing-slide" aria-label="阅读结论与边界"><div class="slide-topline"><span>{esc(spec["title"])}</span><span>阅读结论与边界</span></div><h2>回到证据，再作判断。</h2><p class="summary">{esc(composition["closing"])}</p><p class="disclosure">{esc(disclosure)}</p></section>'
        content += '</div>'
    closing = f'<p class="closing">{esc(composition["closing"])}</p>' if composition.get('closing') else ''
    footer = f'{closing}<p>图表、表格、SVG与源数据来自同一份输入。输入中的标题和解释由作者提供；本工具不生成业务结论。</p><p class="digest">数据SHA-256：{result["sha256"]}</p>'
    if credit:
        footer += f'<p class="palette-credit">{esc(credit)}</p>'
    if reading == 'brief':
        footer = toc + toolbar + footer
    if reading == 'story':
        footer = toolbar + footer
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="chart-data-sha256" content="{result["sha256"]}"><title>{esc(spec["title"])}</title><style>{CSS}{COMPOSE_CSS}{selected}{reading_css}.slide-context{{font-size:14px;line-height:1.55;color:var(--muted);margin:0 0 14px;max-width:100%;flex-shrink:0}}.closing-slide .summary{{font-size:24px;line-height:1.7}}@media(max-width:700px){{.slide-context{{font-size:14px}}.closing-slide .summary{{font-size:19px}}}}</style></head><body class="mode-{mode}{reading_class}"><header>{header}</header><main>{content}</main><footer>{footer}</footer><script type="application/json" id="chart-spec">{safe_json(spec)}</script><script type="application/json" id="chart-ledger">{safe_json(ledgers)}</script><script>{DECK_JS}</script></body></html>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec', type=Path)
    parser.add_argument('--mode', choices=['report', 'slides'], default='report')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--theme')
    parser.add_argument('--brand-accent', help='Exact #RRGGBB focus color; defaults the base palette to graphite')
    parser.add_argument('--reading', choices=REPORT_READING_CSS, help='Optional layout for the intended reading task')
    parser.add_argument('--delivery', choices=['final'], help='Audience-facing HTML layout')
    parser.add_argument('--source-out', type=Path, help='Optional exact original source-file copy; inline/download always included')
    args = parser.parse_args()
    try:
        raw = args.spec.read_bytes()
        spec = json.loads(raw.decode('utf-8-sig'))
        content = build(spec, args.mode, args.theme, reading=args.reading, brand_accent=args.brand_accent, delivery=args.delivery)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(content, encoding='utf-8', newline='\n')
        if args.source_out:
            require(args.source_out.resolve() != args.out.resolve(), 'source-out must differ from HTML output')
            args.source_out.parent.mkdir(parents=True, exist_ok=True)
            args.source_out.write_bytes(raw)
        print(json.dumps({'ok': True, **validate_composition(spec), 'mode': args.mode, 'output': str(args.out.resolve())}, ensure_ascii=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as e:
        print(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
