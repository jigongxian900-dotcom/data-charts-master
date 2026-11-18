"""Audience-facing report layouts on the existing chart and source contracts."""

from pathlib import Path
import re

from chart_html import digest, esc, fmt, require, svg_chart
from compose_html import data_url, safe_json, sections_for, static_svg
from custom_chart import render_variant


ASSETS = Path(__file__).resolve().parents[1] / 'assets'


def story_copy(composition, ids):
    copy = composition.get('audience', {})
    require(isinstance(copy, dict), 'composition.audience must be an object')
    for key in ('edition', 'date', 'source', 'action_label'):
        require(isinstance(copy.get(key, ''), str), f'audience.{key} must be text')
    metrics = copy.get('metrics', [])
    require(isinstance(metrics, list) and len(metrics) <= 3, 'audience.metrics allows up to three metrics')
    for metric in metrics:
        require(isinstance(metric, dict) and all(isinstance(metric.get(k), str) and metric[k].strip()
                for k in ('label', 'value')) and isinstance(metric.get('unit', ''), str),
                'Each audience metric needs a label, a display value and optional unit')
    figures = copy.get('figures', {})
    require(isinstance(figures, dict) and set(figures) <= ids, 'audience.figures keys must identify charts')
    for figure in figures.values():
        require(isinstance(figure, dict) and all(isinstance(v, str) for v in figure.values()), 'audience figure copy must be text')
    return copy


def source_table(fields, rows):
    names = {'label': '对象', 'x': '横轴', 'y': '纵轴', 'value': '数值',
             'group': '分组', 'parts': '构成', 'role': '类型', 'target': '目标', 'highlight': '重点'}
    headers = ''.join(f'<th scope="col">{esc(names.get(key, key))}</th>' for key in fields)
    cells = ''.join('<tr>' + ''.join(f'<td>{esc(fmt(row.get(key)))}</td>' for key in fields) + '</tr>' for row in rows)
    return f'<div class="table-scroll"><table><thead><tr>{headers}</tr></thead><tbody>{cells}</tbody></table></div>'


def render_charts(spec, options, theme, credit, registry):
    figures, sources, ledgers = {}, [], {}
    for index, chart in enumerate(spec['charts'], 1):
        cid = chart['id']
        copy = options.get('figures', {}).get(cid, {})
        renderer = registry.get(chart['kind'])
        if renderer is None:
            svg, ledger = svg_chart(chart, tight=True)
            small, small_ledger = svg_chart(chart, True, tight=True)
            fields = list(dict.fromkeys(k for row in chart['rows'] for k in row))
            standalone = svg
            ledgers[cid] = {'desktop': ledger, 'mobile': small_ledger, 'data_sha256': digest(chart['rows'])}
        else:
            desktop, mobile = (render_variant(chart, renderer, name, theme) for name in ('desktop', 'mobile'))
            require(desktop.coverage == mobile.coverage and desktop.table_fields == mobile.table_fields,
                    'Audience chart variants must retain the same coverage and source fields')
            svg, small, standalone, fields = desktop.svg, mobile.svg, desktop.export_svg, desktop.table_fields
            ledgers[cid] = {'desktop': desktop.ledger, 'mobile': mobile.ledger,
                            'coverage': desktop.coverage, 'data_sha256': digest(chart['rows'])}
        title = copy.get('title', chart['title'])
        note = copy.get('caption', chart.get('note', ''))
        unit = '' if chart['kind'] == 'scatter' else f'<span>{esc(chart["unit"])}</span>'
        heading = f'<div class="figure-head"><h3>{esc(title)}</h3>{unit}</div>'
        caption = f'<figcaption>{esc(note)}</figcaption>' if note else ''
        figures[cid] = (heading, f'<figure data-chart-id="{esc(cid)}"><div class="rendered-figure">'
                        f'<div class="viz-wide">{svg}</div><div class="viz-narrow">{small}</div>'
                        f'</div>{caption}</figure>', copy)
        export = data_url(static_svg(standalone, theme, chart, palette_credit=credit), 'image/svg+xml;charset=utf-8')
        details = source_table(fields, chart['rows'])
        sources.append(f'<details class="chart-data"><summary>{esc(title)}</summary>'
                       f'<p>{esc(chart["period"])} · {esc(chart["scope"])} · {esc(chart["unit"])}</p>'
                       f'{details}<a href="{export}" download="chart-{index:02d}.svg">下载 SVG</a></details>')
    return figures, sources, ledgers


def paragraph(text, cls=''):
    return f'<p class="{cls}">{esc(text)}</p>' if text else ''


def display_title(text):
    parts = re.split('([，；])', text)
    return ''.join(f'<span class="title-clause">{esc("".join(parts[i:i+2]))}</span>'
                   for i in range(0, len(parts), 2) if parts[i])


def metric_ledger(items):
    if not items:
        return ''
    rows = [f'<div><dt>{esc(item["label"])}</dt><dd>{esc(item["value"])}'
            f'<small>{esc(item.get("unit", ""))}</small></dd></div>' for item in items]
    return '<dl class="metric-ledger">' + ''.join(rows) + '</dl>'


def figure_markup(figures, ids, include_heading=True):
    return ''.join(f'<div class="figure-block">{heading if include_heading else ""}{figure}</div>'
                   for heading, figure, _ in (figures[cid] for cid in ids))


def section_html(section, i, figures):
    layout = section.get('layout', 'feature')
    primary = figures[section['charts'][0]][2]
    eyebrow = primary.get('nav', '')
    heading = f'<h2>{esc(section["title"])}</h2>'
    chart = figure_markup(figures, section['charts'])
    insight = paragraph(section.get('intro', ''), 'section-intro')
    callout = primary.get('callout', '')
    annotation = paragraph(callout, 'callout') if callout.rstrip('。') != section['title'].rstrip('。') else ''
    return (f'<section class="story-section layout-{layout}" id="chapter-{i}">'
            f'{paragraph(eyebrow, "section-label")}{heading}'
            f'<div class="section-body"><div class="section-reading">{insight}{annotation}</div>'
            f'<div class="figures">{chart}</div></div></section>')


def action_line(composition, options):
    if not composition.get('closing'):
        return ''
    label = options.get('action_label', '下一步')
    return f'<aside class="action"><h2>{esc(label)}</h2>{paragraph(composition["closing"])}</aside>'


def deck_markup(spec, options, composition, sections, figures, sources):
    caption = options.get('edition', '')
    date = options.get('date', '')
    ledger = metric_ledger(options.get('metrics', []))
    action = action_line(composition, options)
    frames = [f'<section class="frame cover" data-slide><header class="frame-top">{esc(caption)}'
              f'<span>{esc(date)}</span></header><div class="cover-body"><div><h1>{display_title(spec["title"])}</h1>'
              f'{paragraph(composition.get("summary", ""),"standfirst")}</div>{ledger}</div>{action}</section>']
    charts = {chart['id']: chart for chart in spec['charts']}
    for section in sections:
        for cid in section['charts']:
            _, figure, copy = figures[cid]
            title = copy.get('headline', section['title'])
            name = copy.get('nav', '')
            thought = copy.get('callout', section.get('intro', ''))
            aside = paragraph(thought)
            if copy.get('key_reading'):
                aside = f'{paragraph(copy.get("key_label", ""),"aside-label")}{paragraph(copy["key_reading"],"aside-number")}'
            chart = charts[cid]
            unit = paragraph(chart['unit'], 'frame-unit') if chart['kind'] != 'scatter' else '<span></span>'
            frames.append(f'<section class="frame evidence-frame" data-slide>'
                          f'<header class="frame-top">{esc(name)}<span>{esc(date)}</span></header>'
                          f'<h2>{esc(title)}</h2><div class="frame-evidence"><div class="figure-block">{unit}{figure}</div>'
                          f'<aside class="frame-aside">{aside}</aside></div></section>')
    total = len(frames)
    for i, frame in enumerate(frames,1):
        source = f'<span>{esc(sources)}</span>' if sources else '<span></span>'
        frames[i-1] = frame.removesuffix('</section>') + f'<footer>{source}<span>{i:02d} / {total:02d}</span></footer></section>'
    return '<div class="deck-stage">' + ''.join(frames) + '</div>'


def build_final(spec, layout, theme, credit, registry, checksum):
    composition = spec.get('composition', {})
    sections = sections_for(spec)
    options = story_copy(composition, {chart['id'] for chart in spec['charts']})
    figures, data, ledgers = render_charts(spec, options, theme, credit, registry)
    disclosure = '示例数据' if spec.get('synthetic') else ''
    source = options.get('source', '')
    if not source:
        source = ' · '.join(dict.fromkeys(chart['source'] for chart in spec['charts']))
    provenance = ' · '.join(filter(None, (disclosure, source if source != disclosure else '', credit)))
    raw = data_url(safe_json(spec), 'application/json;charset=utf-8')
    materials = ('<details id="materials" class="materials"><summary>数据与口径</summary>'
                 f'<p>{esc(provenance)}</p><a href="{raw}" download="source.json">下载原始数据</a>'
                 + ''.join(data) + '</details>')
    css = (ASSETS / 'report-delivery.css').read_text(encoding='utf-8')
    script = (ASSETS / 'report-delivery.js').read_text(encoding='utf-8')
    edition = options.get('edition', '')
    date = options.get('date', composition.get('subtitle', ''))
    action = action_line(composition, options)
    intro = paragraph(composition.get('summary', ''), 'standfirst')
    metrics = metric_ledger(options.get('metrics', []))
    if layout == 'deck':
        stage = deck_markup(spec, options, composition, sections, figures, provenance)
        controls = ('<nav class="deck-nav" aria-label="演示翻页"><button type="button" id="back" aria-label="上一页">←</button>'
                    '<output id="page" aria-live="polite"></output><button type="button" id="next" aria-label="下一页">→</button>'
                    '<a href="#materials">数据</a></nav>')
        content = stage + controls + materials
    elif layout == 'brief':
        plots = ''.join(figure_markup(figures, section['charts']) for section in sections)
        content = (f'<main class="brief-sheet"><header class="mast">{esc(edition)}<span>{esc(date)}</span></header>'
                   f'<h1>{display_title(spec["title"])}</h1>{intro}<div class="brief-evidence">'
                   f'<div class="brief-sidebar"><div class="brief-lead">{metrics}</div>{action}</div>'
                   f'<div class="brief-figures">{plots}</div></div><footer class="page-source">{esc(provenance)}</footer>{materials}</main>')
    else:
        links = []
        for i, section in enumerate(sections, 1):
            primary = figures[section['charts'][0]][2]
            links.append(f'<a href="#chapter-{i}">{esc(primary.get("nav", section["title"]))}</a>')
        nav = ''.join(links)
        chapters = ''.join(section_html(section,i,figures) for i,section in enumerate(sections,1))
        content = (f'<div class="report-shell"><aside class="report-rail"><strong>{esc(edition)}</strong>'
                   f'{paragraph(date,"rail-date")}<nav aria-label="章节">{nav}<a href="#materials">数据与口径</a></nav></aside>'
                   f'<main class="report-body"><header class="report-lead"><h1>{display_title(spec["title"])}</h1>'
                   f'{intro}{metrics}</header>{chapters}{action}<footer class="page-source">{esc(provenance)}</footer>{materials}</main></div>')
    return (f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="chart-data-sha256" content="{checksum}"><title>{esc(spec["title"])}</title>'
            f'<style>{theme}{css}</style><body class="final-{layout}">{content}'
            f'<script type="application/json" id="chart-spec">{safe_json(spec)}</script>'
            f'<script type="application/json" id="chart-ledger">{safe_json(ledgers)}</script><script>{script}</script></body></html>')
