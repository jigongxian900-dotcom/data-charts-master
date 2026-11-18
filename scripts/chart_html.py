"""Offline SVG chart artifacts. Python stdlib only; no remote calls or data repair."""
import argparse
import collections
import datetime as dt
from decimal import Decimal
import hashlib
import html
import json
import math
import re
from pathlib import Path
import statistics
import sys

KINDS = {'bar', 'line', 'stacked', 'waterfall', 'box', 'scatter'}
KIND_NAMES = {'bar':'比较高低','line':'观察趋势','stacked':'比较构成','waterfall':'核对增减','box':'观察分布','scatter':'观察关联'}
COLORS = [f'var(--category{i})' for i in range(8)]
LINE_DASHES = ['', '7 4', '2 3', '10 3 2 3', '12 5', '4 2 1 2', '1 4', '8 2 2 2 2 2']
COLOR_SYSTEM = Path(__file__).resolve().parents[1] / 'assets' / 'color-system.json'


def load_theme(theme_id):
    themes = json.loads(COLOR_SYSTEM.read_text(encoding='utf-8'))['themes']
    selected = next((t for t in themes if t['id'] == theme_id), None)
    require(selected is not None, f'unknown color theme: {theme_id}')
    return selected, themes


def theme_credit(theme_id):
    selected, _ = load_theme(theme_id)
    return selected.get('attribution', '')


def relative_luminance(hex_color):
    components = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in components]
    return sum(c * weight for c, weight in zip(linear, (.2126, .7152, .0722)))


def theme_css(theme_id, *, brand_accent=None):
    selected, themes = load_theme(theme_id)
    roles = {'paper':'surface', 'bg':'paper', 'ink':'ink', 'muted':'muted',
             'rule':'grid', 'accent':'accent', 'series':'accent2', 'positive':'positive', 'negative':'negative'}
    tokens = {k:selected[v] for k,v in roles.items()}
    tokens.update({f'category{i}':c for i,c in enumerate(selected['categorical'])})
    print_id = selected.get('print_theme', 'tidal' if theme_id == 'nocturne' else theme_id)
    print_theme = next(t for t in themes if t['id'] == print_id)
    print_tokens = {k:print_theme[v] for k,v in roles.items()}
    print_tokens.update({f'category{i}':c for i,c in enumerate(print_theme['categorical'])})
    print_tokens.update({'bg':'#FFFFFF','paper':'#FFFFFF'})
    if brand_accent is not None:
        require(isinstance(brand_accent, str) and re.fullmatch(r'#[0-9A-Fa-f]{6}', brand_accent), 'brand accent must be #RRGGBB')
        for background in (tokens['bg'], tokens['paper'], print_tokens['paper']):
            darker, lighter = sorted(map(relative_luminance, (brand_accent, background)))
            require((lighter + .05) / (darker + .05) >= 4.5,
                    f'brand accent must contrast 4.5:1 with {background}; use an approved shade')
        tokens['accent'] = print_tokens['accent'] = brand_accent.upper()
    print_css = '@media print{:root{' + ';'.join(f'--{k}:{v}' for k,v in print_tokens.items()) + '}}'
    return ':root{' + ';'.join(f'--{k}:{v}' for k,v in tokens.items()) + '}' + '''
button,select{background:var(--paper);border-color:var(--muted)}
.notice{color:var(--ink)}:focus-visible{outline-color:var(--accent)}
.layout-focus nav{background:var(--paper)}
''' + print_css


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(obj):
    return hashlib.sha256(canonical(obj).encode('utf-8')).hexdigest()


def numerically_equal(actual, expected):
    """Relative tolerance without a unit-dependent absolute zero bucket."""
    a, b = Decimal(str(actual)), Decimal(str(expected))
    return abs(a-b) <= max(abs(a),abs(b))*Decimal('1e-9')


def quantile(values, p):
    values = sorted(values)
    k = (len(values) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def validate(spec):
    require(isinstance(spec, dict), 'spec must be an object')
    require(isinstance(spec.get('title'), str) and spec['title'].strip(), 'title is required')
    require(isinstance(spec.get('charts'), list) and spec['charts'], 'charts must be a nonempty list')
    seen = set()
    for c in spec['charts']:
        require(isinstance(c, dict), 'each chart must be an object')
        for key in ['id', 'title', 'question', 'unit', 'period', 'scope', 'source']:
            require(isinstance(c.get(key), str) and c[key].strip(), f'{key} is required')
        require(c['id'] not in seen, f'duplicate chart id: {c["id"]}')
        seen.add(c['id'])
        require(c.get('kind') in KINDS, 'unsupported chart kind')
        require(isinstance(c.get('rows'), list), 'rows must be a list')
        kind, rows = c['kind'], c['rows']
        if 'orientation' in c:
            require(kind == 'bar' and c['orientation'] in {'horizontal', 'vertical'},
                    'orientation applies to bars and must be horizontal or vertical')
            if c['orientation'] == 'vertical':
                require(len(rows) <= 12, 'Use horizontal bars for more than twelve categories')
        if 'shape' in c:
            from chart_shapes import STYLES
            require(any(style == c['shape'] for style, _, _ in STYLES.get(kind, [])),
                    f'unsupported shape for {kind}')
        require(c.get('performance_direction', 'neutral') in {'neutral', 'higher', 'lower'}, 'performance_direction must be neutral, higher or lower')
        keys = set()
        for r in rows:
            require(isinstance(r, dict), 'row must be an object')
            if kind == 'line':
                require(isinstance(r.get('x'), str), 'line x must be ISO date')
                require('group' not in r or isinstance(r['group'], str), 'line group must be text')
                dt.date.fromisoformat(r['x'])
                require(c.get('frequency') in {'day', 'month', 'year'}, 'line needs day/month/year frequency')
                key = (r.get('group', ''), r['x'])
                require(key not in keys, 'duplicate date in line group')
                keys.add(key)
            else:
                require(isinstance(r.get('label'), str) and r['label'], 'row label is required')
                if kind in {'bar', 'stacked', 'waterfall'}:
                    require(r['label'] not in keys, 'duplicate category; aggregate explicitly first')
                    keys.add(r['label'])
            if kind == 'stacked':
                parts = r.get('parts')
                require(isinstance(parts, dict) and parts, 'stacked parts required')
                require(all(isinstance(k, str) and k and num(v) and v >= 0 for k, v in parts.items()), 'stacked parts must be nonnegative finite values; no implicit missing-to-zero')
                require(not c.get('percent') or sum(parts.values()) > 0, 'zero denominator in percent stack')
            elif kind == 'scatter':
                require(all(k in r and (r[k] is None or num(r[k])) for k in ['x', 'y']), 'scatter x/y must be numbers or explicit null')
                require(c.get('x_unit') and c.get('y_unit'), 'scatter needs axis units')
            else:
                require('value' in r and (r['value'] is None or num(r['value'])), 'value must be finite number or explicit null')
                if kind == 'bar' and 'target' in r:
                    require(r['target'] is None or (num(r['target']) and r['target'] >= 0), 'target must be nonnegative finite number or explicit null')
                if kind == 'waterfall':
                    require(num(r['value']), 'waterfall cannot reconcile missing values')
                    require(r.get('role') in {'start', 'change', 'total'}, 'waterfall role required')
        if kind == 'line' and rows:
            groups = collections.defaultdict(list)
            for r in rows:
                groups[r.get('group', '')].append(dt.date.fromisoformat(r['x']))
            for dates in groups.values():
                dates.sort()
                for a, b in zip(dates, dates[1:]):
                    if c['frequency'] == 'day':
                        contiguous = (b - a).days == 1
                    elif c['frequency'] == 'month':
                        contiguous = (b.year * 12 + b.month) - (a.year * 12 + a.month) == 1
                    else:
                        contiguous = b.year - a.year == 1
                    require(contiguous, 'line has undeclared missing periods; add explicit null rows')
        if kind == 'waterfall' and rows:
            require(len(rows) >= 2 and rows[0]['role'] == 'start' and rows[-1]['role'] == 'total', 'waterfall needs start and final total')
            require(all(r['role'] == 'change' for r in rows[1:-1]), 'intermediate totals are not supported')
            total = sum((Decimal(str(r['value'])) for r in rows[:-1]), Decimal(0))
            require(numerically_equal(total, rows[-1]['value']), 'waterfall does not reconcile')
        if kind == 'stacked' and rows:
            names = set(rows[0]['parts'])
            require(all(set(r['parts']) == names for r in rows), 'stacked categories differ; declare missing values instead of omitting a part')
        for claim in c.get('claims', []):
            values = [r['value'] for r in rows if r.get('value') is not None]
            require(kind in {'bar', 'line', 'box'} and values, 'claim requires nonempty numeric values')
            method = claim.get('method')
            require(method in {'sum', 'mean', 'median', 'count'}, 'unsupported claim method')
            precise = [Decimal(str(v)) for v in values]
            actual = {'sum': sum, 'mean': statistics.mean, 'median': statistics.median, 'count': len}[method](precise)
            require(num(claim.get('expected')) and numerically_equal(actual, claim['expected']), 'declared numeric claim does not match rows')
    canonical(spec)
    return {'charts': len(spec['charts']), 'rows': sum(len(c['rows']) for c in spec['charts']), 'sha256': digest(spec)}


def esc(s):
    return html.escape(str(s), quote=True)


def fmt(v, *, axis=False):
    if v is None:
        return '缺失'
    if isinstance(v, dict):
        return ' · '.join(f'{k}: {fmt(x)}' for k, x in v.items())
    if num(v):
        if v == 0:
            return '0'
        if isinstance(v, int):
            return f'{v:,}'
        # Raw labels/tables retain the supplied decimal precision. Axis
        # arithmetic may have binary noise; significant digits never turn a
        # nonzero value into a fabricated zero, including very small units.
        raw = format(v, '.12g') if axis else str(v)
        if 'e' in raw.lower():
            return raw
        value = format(Decimal(raw), ',f')
        return value.rstrip('0').rstrip('.') if '.' in value else value
    return str(v)


def extent(values, zero=False):
    lo, hi = min(values), max(values)
    if zero:
        lo, hi = min(0, lo), max(0, hi)
    if lo == hi:
        if zero and lo == 0:
            return 0, 1
        pad = max(abs(lo) * .1, 1)
        return lo - pad, hi + pad
    pad = (hi - lo) * .10
    return (lo if zero and lo == 0 else lo - pad), (hi if zero and hi == 0 else hi + pad)


def display_number(value, max_chars=16):
    """Shorten only a display glyph; source/ledger values remain unchanged."""
    reading = fmt(value)
    if num(value) and len(reading) > max_chars:
        return format(value, '.6g')
    return reading


def compact_ticks(values, intervals=4):
    """Readable ticks with one outward-rounded domain for every observation.

    Decimal tick arithmetic avoids float tails and never buckets a tiny
    nonzero step into zero. This is used only by compact layouts.
    """
    low, high = map(lambda v: Decimal(str(v)), extent(values))
    raw_step = (high-low)/intervals
    # Converted coordinates must also retain distinct floats at large bases.
    raw_step=max(raw_step,Decimal(str(max(math.ulp(float(low)),math.ulp(float(high))))))
    magnitude = Decimal(10) ** raw_step.adjusted()
    step = next(v*magnitude for v in map(Decimal, ['1','2','2.5','5','10']) if v*magnitude >= raw_step)
    first, last = math.floor(low/step), math.ceil(high/step)
    ticks = [float(step*i) for i in range(first,last+1)]
    return ticks[0], ticks[-1], ticks


def compact_tick_readings(ticks):
    readings=[format(v,'.4g') for v in ticks]
    if len(set(readings))==len(ticks):
        return readings,None
    # A small span around a large base needs an explicit offset, rather than
    # printing several identical rounded labels at different coordinates.
    base=Decimal(str(ticks[0]))
    offsets=[Decimal(str(v))-base for v in ticks]
    readings=['0' if v==0 else format(v,'.6g') for v in offsets]
    return readings,'轴值 = '+fmt(ticks[0])+' + 刻度'


def compact_chart(c):
    """A narrow *layout*, not a scaled desktop canvas.

    At the smallest supported 256 CSS-pixel chart slot, 14 SVG units on
    this 280-unit canvas are 12.8 CSS pixels. Rows grow vertically. Numeric
    tokens stay atomic; the exact values always remain in the source table.
    """
    width, pad, font, leading = 280, 8, 14, 20
    out, ledger = [], []
    cursor = 20
    natural_width = width
    def measured(s):
        return sum(4 if ch.isspace() else 8 if ord(ch) < 256 else 14 for ch in str(s))
    def wrapped(value, available=264):
        nonlocal natural_width
        # A signed decimal/exponent/percentage is a single token. Never wrap
        # 100 into 10 / 0 or split a minus sign from its number.
        tokens = re.findall(r'[+−-]?\d[\d,]*(?:\.\d+)?(?:[eE][+−-]?\d+)?%?|[A-Za-z_]+|\s+|.', str(value))
        lines, part = [], ''
        for token in tokens:
            if re.search(r'\d', token):
                natural_width=max(natural_width, measured(token)+32)
            if measured(token) > available and not re.search(r'\d', token):
                pieces = list(token)
            else:
                pieces = [token]
            for piece in pieces:
                if part and measured(part + piece) > available:
                    lines.append(part.rstrip()); part = ''
                part += piece
        if part.strip(): lines.append(part.rstrip())
        return lines or ['']
    def text(x, y, value, anchor='start', cls=''):
        out.append(f'<text x="{x:.3f}" y="{y:.3f}" text-anchor="{anchor}" class="{cls}">{esc(value)}</text>')
    def paragraph(value, cls='', x=pad, available=264):
        nonlocal cursor
        for reading in wrapped(value, available):
            text(x, cursor, reading, cls=cls); cursor += leading
    def line(x1,y1,x2,y2,color='var(--rule)',dash=''):
        out.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-dasharray="{dash}"/>')
    def rect(x,y,w,h,value,label,color,axis,start,end,scale):
        out.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.12g}" height="{h:.12g}" fill="{color}" data-value="{value}" data-start="{start}" data-end="{end}" data-scale="{scale}" data-axis="{axis}" role="img" aria-label="{esc(label)}"><title>{esc(label)}</title></rect>')
        ledger.append(dict(shape='rect',value=value,x=x,y=y,width=w,height=h,axis=axis,start=start,end=end,scale=scale))
    def dot(x,y,value,label,color='var(--accent)',reference=False):
        out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="4" fill="{"var(--paper)" if reference else color}" stroke="{color}" stroke-width="2" role="img" aria-label="{esc(label)}"><title>{esc(label)}</title></circle>')
        ledger.append(dict(shape='point',value=value,x=x,y=y))
    def short(v): return display_number(v, 12)
    rows, kind = c['rows'], c['kind']
    vals = [r['value'] for r in rows if num(r.get('value'))]
    if not rows:
        paragraph('当前没有可绘制的数据', 'empty')
    elif kind in {'bar','waterfall'}:
        waterfall = kind == 'waterfall'
        if waterfall:
            net = float(Decimal(str(rows[-1]['value'])) - Decimal(str(rows[0]['value'])))
            paragraph('窄屏阅读：零基线贡献行', 'comparison-note')
            paragraph('期初 '+rows[0]['label']+'：'+short(rows[0]['value']), 'value')
            paragraph('期末 '+rows[-1]['label']+'：'+short(rows[-1]['value']), 'value')
            paragraph('净变化 '+('+' if net>0 else '')+short(net)+' '+c['unit'], 'comparison-note')
            paragraph('下方仅绘制增减，共用贡献尺度。', 'tick')
            ledger.extend(dict(shape='reference-total',role=r['role'],label=r['label'],value=r['value']) for r in [rows[0],rows[-1]])
        plotted_rows=rows[1:-1] if waterfall else rows
        scale_values = [r['value'] for r in plotted_rows if num(r.get('value'))] + [r['target'] for r in plotted_rows if r.get('target') is not None]
        if not scale_values:
            paragraph('没有中间增减项' if waterfall else '当前没有可绘制的数据', 'tick' if waterfall else 'empty')
        else:
            lo,hi = extent(scale_values, True)
            scale = 264/(hi-lo)
            xx = lambda v: pad+(v-lo)*scale
            for r in plotted_rows:
                paragraph(r['label'], 'category')
                v = r['value']
                prefix = '+' if waterfall and r['role']=='change' and v>0 else ''
                paragraph(('实际 ' if not waterfall else '')+prefix+short(v)+' '+c['unit'], 'value')
                yy=cursor-5
                line(xx(0),yy-4,xx(0),yy+25,'var(--ink)')
                if v is not None:
                    color='var(--accent)' if r.get('highlight') else 'var(--series)'
                    if waterfall:
                        direction=c.get('performance_direction','neutral')
                        if r['role']!='change':color='var(--ink)'
                        elif direction=='neutral':color='var(--accent)' if v>=0 else 'var(--series)'
                        else:color='var(--positive)' if ((v>=0)==(direction=='higher')) else 'var(--negative)'
                    rect(min(xx(0),xx(v)),yy,abs(v)*scale,20,v,r['label']+'：'+fmt(v)+' '+c['unit'],color,'x',0,v,scale)
                if 'target' in r:
                    target=r['target']
                    if target is not None:line(xx(target),yy-4,xx(target),yy+25,'var(--ink)','3 2')
                    attainment=None if target in (None,0) or v is None else v/target*100
                    ledger.append(dict(shape='target',value=target,attainment=attainment,actual=v,x=None if target is None else xx(target)))
                cursor=yy+44
                if 'target' in r:
                    target=r['target']; direction=c.get('performance_direction','neutral')
                    paragraph('目标未知' if target is None else '目标 '+short(target), 'tick')
                    if target is not None and v is not None:
                        delta=float(Decimal(str(v))-Decimal(str(target)))
                        paragraph('差额 '+('+' if delta>0 else '')+short(delta), 'tick')
                    if attainment is None:
                        paragraph('目标未提供' if target is None else '实际未提供' if v is None else '零目标，不计算比率', 'tick')
                    else:
                        reading=round(attainment,2) if abs(attainment)>=.01 else float(format(attainment,'.3g'))
                        paragraph(('达成 ' if direction=='higher' else '实际/目标 ')+short(reading)+'%', 'target-reading')
                        if direction!='neutral':paragraph('达标' if (v>=target if direction=='higher' else v<=target) else '未达标', 'tick')
                cursor+=12
            paragraph('0 为各行共同基线', 'tick')
    elif kind == 'stacked':
        names=list(rows[0]['parts'])
        paragraph('构成：色块对应下方同色明细', 'comparison-note')
        maxima=100 if c.get('percent') else max(sum(r['parts'].values()) for r in rows)
        scale=264/(maxima or 1)
        for r in rows:
            paragraph(r['label'], 'category')
            denom=sum(r['parts'].values())
            paragraph('合计 '+short(denom)+' '+c['unit'], 'value')
            start=0; yy=cursor-5
            for j,name in enumerate(names):
                raw=r['parts'][name]; value=raw/denom*100 if c.get('percent') else raw
                rect(pad+start*scale,yy,value*scale,24,value,r['label']+' '+name+'：'+fmt(raw),COLORS[j%len(COLORS)],'x',start,start+value,scale)
                start+=value
            cursor=yy+44
            for j,name in enumerate(names):
                out.append(f'<rect x="8" y="{cursor-11}" width="9" height="9" fill="{COLORS[j%len(COLORS)]}"/>')
                paragraph(name, 'legend', 25, 247)
                raw=r['parts'][name]
                reading=short(raw)+' '+c['unit']
                if c.get('percent'):reading+=' · 占 '+short(float(format(raw/denom*100,'.6g')))+'%'
                paragraph(reading, 'tick',25,247)
            cursor+=12
    elif kind == 'line':
        groups=collections.defaultdict(list)
        for r in rows:groups[r.get('group','观测值')].append(r)
        for rr in groups.values():rr.sort(key=lambda r:r['x'])
        if vals:
            lo,hi,ticks=compact_ticks(vals)
            tick_readings,offset_note=compact_tick_readings(ticks)
        else:offset_note=None
        endpoint_reading=lambda v:fmt(v) if offset_note else short(v)
        windows={(rr[0]['x'],rr[-1]['x']) for rr in groups.values()}
        common_window=len(windows)==1
        if common_window:
            start,end=next(iter(windows))
            paragraph('共同期间：'+start+' → '+end, 'comparison-note')
        for gi,(name,rr) in enumerate(groups.items()):
            paragraph(name, 'legend')
            a,z=rr[0],rr[-1]
            if common_window:
                reading='起 '+endpoint_reading(a['value'])+' → 末 '+endpoint_reading(z['value'])
                if measured(reading)<=264:
                    paragraph(reading, 'tick')
                else:
                    paragraph('起 '+endpoint_reading(a['value']), 'tick')
                    paragraph('末 '+endpoint_reading(z['value']), 'tick')
            else:
                paragraph('起 '+a['x']+'：'+endpoint_reading(a['value']), 'tick')
                paragraph('末 '+z['x']+'：'+endpoint_reading(z['value']), 'tick')
            if len(rr)>1 and a['value'] is not None and z['value'] is not None:
                delta=float(Decimal(str(z['value']))-Decimal(str(a['value'])))
                paragraph('首尾差 '+('+' if delta>0 else '')+short(delta)+' '+('百分点' if c['unit']=='%' else c['unit']), 'comparison-note')
            elif a['value'] is None or z['value'] is None:
                paragraph('起末期均缺测' if a['value'] is None and z['value'] is None else '起期缺测' if a['value'] is None else '末期缺测', 'tick')
            # A visible line key ties wrapped series names to the plot.
            line(pad,cursor-6,272,cursor-6,COLORS[gi%len(COLORS)],LINE_DASHES[gi%len(LINE_DASHES)])
            cursor+=14
        if vals:
            if offset_note:paragraph(offset_note,'comparison-note')
            left,right,top,bottom=78,264,cursor+10,cursor+230
            yy=lambda v:bottom-(v-lo)/(hi-lo)*(bottom-top)
            for v,reading in zip(ticks,tick_readings):
                line(left,yy(v),right,yy(v)); text(left-8,yy(v)+4,reading,'end','tick')
            dates=sorted({r['x'] for r in rows}); ordinals=[dt.date.fromisoformat(d).toordinal() for d in dates]
            xx=lambda d:left+(dt.date.fromisoformat(d).toordinal()-ordinals[0])/(ordinals[-1]-ordinals[0] or 1)*(right-left)
            for gi,(name,rr) in enumerate(groups.items()):
                segment=[]
                def finish():
                    if segment:out.append('<polyline points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in segment)+f'" fill="none" stroke="{COLORS[gi%len(COLORS)]}" stroke-width="2.4" stroke-dasharray="{LINE_DASHES[gi%len(LINE_DASHES)]}"/>')
                for r in rr:
                    if r['value'] is None:finish(); segment=[]; continue
                    px,py=xx(r['x']),yy(r['value']);segment.append((px,py))
                    dot(px,py,r['value'],name+' '+r['x']+'：'+fmt(r['value']),COLORS[gi%len(COLORS)],reference=r is rr[0])
                finish()
            for date in dict.fromkeys([dates[0],dates[len(dates)//2],dates[-1]]):
                label=date[:4] if c['frequency']=='year' else date[5:]
                anchor='start' if date==dates[0] else 'end' if date==dates[-1] else 'middle'
                text(xx(date),bottom+25,label,anchor,'tick')
            cursor=bottom+50
        else:paragraph('当前没有可绘制的数据','empty')
    elif kind == 'box':
        if not vals:paragraph('当前没有可绘制的数据','empty')
        else:
            lo,hi,ticks=compact_ticks(vals,2); scale=248/(hi-lo); xx=lambda v:16+(v-lo)*scale
            tick_readings,offset_note=compact_tick_readings(ticks)
            groups=collections.defaultdict(list)
            for r in rows:
                if r['value'] is not None:groups[r['label']].append(r['value'])
            paragraph('各组共用横轴；圆点为原始观测值。','comparison-note')
            if offset_note:paragraph(offset_note,'comparison-note')
            for name,vv in groups.items():
                paragraph(name,'category')
                med=quantile(vv,.5);q1=quantile(vv,.25);q3=quantile(vv,.75);iqr=q3-q1
                inner=[v for v in vv if q1-1.5*iqr<=v<=q3+1.5*iqr]
                paragraph('n='+str(len(vv))+' · 中位数 '+(fmt(med) if offset_note else short(med)),'annotated-value')
                yy=cursor+24
                line(xx(min(inner)),yy,xx(max(inner)),yy,'var(--accent)')
                for v in [min(inner),max(inner)]:line(xx(v),yy-12,xx(v),yy+12,'var(--accent)')
                mark_axis = ' data-box-direction="x"' if c.get('shape') else ''
                out.append(f'<rect x="{xx(q1):.3f}" y="{yy-15:.3f}" width="{max(0,xx(q3)-xx(q1)):.3f}" height="30" fill="var(--paper)" stroke="var(--accent)"{mark_axis}/>')
                line(xx(med),yy-15,xx(med),yy+15,'var(--accent)')
                for i,v in enumerate(sorted(vv)):dot(xx(v),yy+((i*7)%17-8)*1.5,v,name+' 原始值 '+fmt(v),'var(--muted)')
                ledger.append(dict(shape='box',label=name,q1=q1,median=med,q3=q3,low=min(inner),high=max(inner),n=len(vv)))
                cursor=yy+58
            for i,(v,reading) in enumerate(zip(ticks,tick_readings)):
                text(xx(v),cursor,reading,'start' if i==0 else 'end' if i==len(ticks)-1 else 'middle','tick')
            cursor+=28;paragraph(c['unit'],'tick')
    elif kind == 'scatter':
        points=[r for r in rows if r['x'] is not None and r['y'] is not None]
        if not points:paragraph('当前没有可绘制的数据','empty')
        else:
            paragraph('纵轴：'+c['y_unit'],'tick')
            left,right,top,bottom=78,264,cursor+10,cursor+230
            lo,hi=extent([r['y'] for r in points]);xlo,xhi=extent([r['x'] for r in points])
            yy=lambda v:bottom-(v-lo)/(hi-lo)*(bottom-top)
            xx=lambda v:left+(v-xlo)/(xhi-xlo)*(right-left)
            for i in range(5):
                v=lo+(hi-lo)*i/4;line(left,yy(v),right,yy(v));text(left-8,yy(v)+4,format(v,'.4g'),'end','tick')
            for i in range(3):
                v=xlo+(xhi-xlo)*i/2;text(xx(v),bottom+25,format(v,'.4g'),'start' if i==0 else 'end' if i==2 else 'middle','tick')
            for r in points:dot(xx(r['x']),yy(r['y']),r['y'],r['label']+'：'+fmt(r['x'])+' '+c['x_unit']+'，'+fmt(r['y'])+' '+c['y_unit'])
            cursor=bottom+50;paragraph('横轴：'+c['x_unit'],'tick')
            extreme=[]
            if c.get('label_extremes',True):
                for key,axis in [('x','横轴'),('y','纵轴')]:
                    for method,label in [(min,'最小'),(max,'最大')]:
                        r=method(points,key=lambda r:r[key]);extreme.append((r,axis+label))
            extreme.extend((r,'重点') for r in points if r.get('highlight'))
            for r,reason in extreme:
                paragraph(reason+'：'+r['label'],'category')
                paragraph('x '+short(r['x'])+' · y '+short(r['y']),'value')
    height=max(80,cursor+8)
    label=c['title']+'。'+c['question']+'。窄屏重排，完整数值见同源数据表。'
    wide=' compact-wide' if natural_width>width else ''
    minimum=f' style="min-width:{natural_width}px"' if wide else ''
    svg=f'<svg viewBox="0 0 {natural_width} {height}" role="img" aria-label="{esc(label)}" class="compact-svg{wide}"{minimum} data-source-sha256="{digest(rows)}"><title>{esc(label)}</title>'+''.join(out)+'</svg>'
    return svg,ledger


def svg_chart(c, mobile=False, *, compact=False, tight=False, bar_row_height=39):
    if compact:
        svg, ledger = compact_chart(c)
        return svg_shape(svg, c), ledger
    width, height = (360, 340) if mobile else (760, 326 if tight else 360)
    left, right, top, bottom = (58, width - 35, 36, height - 55)
    kind, rows = c['kind'], c['rows']
    out, ledger = [], []
    def text(x, y, value, anchor='start', cls='', extra=''):
        out.append(f'<text x="{x:.3f}" y="{y:.3f}" text-anchor="{anchor}" class="{cls}" {extra}>{esc(value)}</text>')
    def line(x1, y1, x2, y2, color='var(--rule)', dash=''):
        out.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-dasharray="{dash}"/>')
    def dot(x, y, value, label, color, radius=4, reference=False):
        fill,stroke=('var(--paper)',color) if reference else (color,'var(--paper)')
        out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{2 if reference else 1}" tabindex="0" role="img" aria-label="{esc(label)}"><title>{esc(label)}</title></circle>')
        ledger.append({'shape': 'point', 'value': value, 'x': x, 'y': y})
    def rect(x, y, w, h, value, label, color, axis, start, end, scale):
        out.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="{color}" tabindex="0" role="img" aria-label="{esc(label)}" data-value="{value}" data-start="{start}" data-end="{end}" data-scale="{scale}" data-axis="{axis}"><title>{esc(label)}</title></rect>')
        ledger.append({'shape': 'rect', 'value': value, 'x': x, 'y': y, 'width': w, 'height': h, 'axis': axis, 'start': start, 'end': end, 'scale': scale})
    def axis_y(values, zero=False):
        lo, hi = extent(values, zero)
        raw_step = (hi-lo)/4
        magnitude = 10**math.floor(math.log10(raw_step))
        step = next(v for v in [1,2,2.5,5,10] if v*magnitude >= raw_step)*magnitude
        lo, hi = math.floor(lo/step)*step, math.ceil(hi/step)*step
        y = lambda v: bottom - (v - lo) / (hi - lo) * (bottom - top)
        for i in range(round((hi-lo)/step)+1):
            v = lo + step*i
            line(left, y(v), right, y(v))
            text(left - 8, y(v) + 4, fmt(v, axis=True), 'end', 'tick')
        return y, lo, hi
    def category_text(x, y, label, anchor='start', limit=10):
        parts,part,used=[], '',0
        for ch in str(label):
            advance=.3 if ch.isspace() else .5 if ord(ch)<256 else 1
            if part and used+advance>limit:
                parts.append(part)
                part,used='',0
            part+=ch
            used+=advance
        if part:parts.append(part)
        for i, part in enumerate(parts):
            text(x, y + i * 16, part, anchor, 'category')
    def empty():
        text(width / 2, height / 2, '当前没有可绘制的数据', 'middle', 'empty')
    vals = [r.get('value') for r in rows if num(r.get('value'))]
    if not rows:
        empty()
    elif kind == 'bar' and c.get('orientation') == 'vertical':
        if not vals:
            empty()
        else:
            measured = vals + [r['target'] for r in rows if num(r.get('target'))]
            yy, lo, hi = axis_y(measured, True)
            scale = (bottom-top)/(hi-lo)
            step = (right-left)/len(rows)
            bar_width = min(44,step*.55)
            line(left,yy(0),right,yy(0),'var(--muted)')
            for i,r in enumerate(rows):
                x=left+(i+.5)*step
                value=r['value']
                target=r.get('target')
                if value is None:
                    text(x, yy(0)-9, '未报', 'middle', 'tick')
                else:
                    color='var(--accent)' if r.get('highlight') else 'var(--series)'
                    rect(x-bar_width/2,min(yy(0),yy(value)),bar_width,abs(value)*scale,value,
                         f'{r["label"]}：{fmt(value)} {c["unit"]}',color,'y',0,value,scale)
                    text(x,yy(value)+(17 if value<0 else -8),display_number(value),'middle','value')
                if target is not None:
                    line(x-bar_width*.7,yy(target),x+bar_width*.7,yy(target),'var(--ink)','3 2')
                category_text(x, bottom+24, r['label'], 'middle', max(1,min(8,int(step/15))))
            max_lines=max(math.ceil(len(r['label'])/max(1,min(8,int(step/15)))) for r in rows)
            height += max(0,max_lines-2)*16 + (12 if any(v<0 for v in vals) else 0)
    elif kind == 'bar':
        left = 138 if mobile else 205
        plain_rank = tight and all('target' not in row for row in rows)
        negative_room = 36 if any(v < 0 for v in vals) else 0
        if plain_rank:
            character_count = max((len(r['label']) for r in rows), default=0)
            left = max(60, min(left, 16*character_count+23)) + negative_room
        value_space = max(68, max((len(display_number(v))*7.5+12 for v in vals), default=68))
        if plain_rank:
            value_space = max(32, value_space - 22)
        right = width - value_space
        require(right > left + 30, 'values too wide for this layout; choose a table or a wider canvas')
        # Reserve actual Chinese glyph width, not an ASCII-sized estimate.
        # Twelve full-width glyphs fit the 193px desktop label column with
        # a font-fallback margin; wrapped rows grow with the same limit.
        label_limit = max(2, (left-15-negative_room)//16) if plain_rank else 8 if mobile else 12
        def target_details(r):
            target,v=r.get('target'),r['value']
            result='目标未知' if target is None else '目标 '+fmt(target)
            if target is not None and v is not None:
                delta=float(Decimal(str(v))-Decimal(str(target)))
                result+=' · 差额 '+('+' if delta>0 else '')+fmt(delta)
            lines,part,used=[], '',0
            # Keep a signed decimal/scientific number in one reading token.
            tokens=re.findall(r'[+-]?\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?|.',result,re.I)
            for ch in tokens:
                advance=sum(.55 if ord(glyph)<256 else 1 for glyph in ch)
                if part and used+advance>(width-left-6)/14:
                    lines.append(part)
                    part,used='',0
                part+=ch
                used+=advance
            if part:lines.append(part)
            return lines
        row_sizes=[]
        for r in rows:
            size=max(bar_row_height if plain_rank else 56 if mobile else 49,math.ceil(len(r['label'])/label_limit)*16+20)
            if 'target' in r:
                offset=max(41,math.ceil(len(r['label'])/label_limit)*16+18)
                size=max(size,offset+17*len(target_details(r))+63)
            row_sizes.append(size)
        if plain_rank:
            top = 10
        height = max(176 if plain_rank else 210, sum(row_sizes) + (43 if plain_rank else 80))
        bottom = height - 38
        scale_values = vals + [r['target'] for r in rows if r.get('target') is not None]
        if not scale_values:
            empty()
        else:
            lo, hi = extent(scale_values, True)
            x = lambda v: left + (v - lo) / (hi - lo) * (right - left)
            scale = (right - left) / (hi - lo)
            line(x(0), top - 7, x(0), bottom)
            text(x(0),bottom+26,'0','middle','tick')
            for i, r in enumerate(rows):
                yy = top + 15 + sum(row_sizes[:i])
                category_text(left-12-(negative_room if plain_rank else 0), yy, r['label'], 'end', label_limit)
                v = r['value']
                if v is None:
                    text(left + 7, yy, '缺失', cls='muted')
                else:
                    color = 'var(--accent)' if r.get('highlight') else 'var(--series)'
                    rect(min(x(0), x(v)), yy-13, abs(v)*scale, 21, v, f'{r["label"]}：{fmt(v)} {c["unit"]}', color, 'x', 0, v, scale)
                    if plain_rank:
                        text(x(v)+(8 if v>=0 else -8), yy+1, display_number(v), 'start' if v>=0 else 'end', 'value')
                    else:
                        text(width-4, yy+3, display_number(v), 'end', 'value')
                if 'target' in r:
                    target = r['target']
                    if target is not None:
                        line(x(target),yy-20,x(target),yy+14,'var(--ink)','3 2')
                    attainment = None if target in (None,0) or v is None else v/target*100
                    target_text = '目标未知' if target is None else '目标 '+fmt(target)
                    direction=c.get('performance_direction','neutral')
                    ratio_label='达成' if direction=='higher' else '实际/目标'
                    if attainment is None:
                        ratio_text='目标未提供' if target is None else '实际未提供' if v is None else '零目标，不计算比率'
                    else:
                        displayed=round(attainment,2) if abs(attainment)>=.01 else float(format(attainment,'.3g'))
                        ratio_text=ratio_label+' '+fmt(displayed)+'%'
                    status_text=''
                    if v is not None and target is not None and direction!='neutral':
                        met=v>=target if direction=='higher' else v<=target
                        status_text='达标' if met else '未达标'
                    units=sum(.55 if ord(ch)<256 else 1 for ch in ratio_text)
                    reading_size=min(22,max(14,(width-left-6)/max(units,1))) if attainment is not None else 14
                    text(left,yy-25,ratio_text,cls='target-reading'+(' target-unknown' if attainment is None else ''),extra=f'style="font-size:{reading_size}px"')
                    offset=max(41,math.ceil(len(r['label'])/label_limit)*16+18)
                    details=target_details(r)
                    for detail_index,detail in enumerate(details):text(left,yy+offset+detail_index*17,detail,cls='tick')
                    if status_text:text(left,yy+offset+len(details)*17,status_text,cls='tick')
                    if v is not None and target is not None and v!=target:
                        a,z=sorted([x(v),x(target)])
                        line(a,yy+21,z,yy+21,'var(--ink)')
                        line(a,yy+17,a,yy+25,'var(--ink)')
                        line(z,yy+17,z,yy+25,'var(--ink)')
                    ledger.append({'shape':'target','value':target,'attainment':attainment,'actual':v,'x':None if target is None else x(target)})
    elif kind == 'line':
        if not vals:
            empty()
        else:
            groups = collections.defaultdict(list)
            for r in rows:
                groups[r.get('group', '系列')].append(r)
            ordered_groups={group:sorted(values,key=lambda r:r['x']) for group,values in groups.items()}
            common_window=len({(values[0]['x'],values[-1]['x']) for values in ordered_groups.values()})==1
            compare_groups=len(groups)<=4 and common_window
            # Each character gets a full-em fallback allowance, including
            # Latin names, so long series names wrap inside the SVG instead
            # of relying on visible overflow. Grow the canvas, not tiny type.
            columns = min(2 if mobile else 4,len(groups))
            cell = (right-left)/columns
            if any(len(str(group))*15+28 > cell for group in groups):
                columns = 1
                cell = right-left
            limit = max(1, math.floor((cell-20)/15))
            legends, legend_y = [], 16
            group_items = list(groups)
            for row_start in range(0,len(group_items),columns):
                row_height = 0
                for column, group in enumerate(group_items[row_start:row_start+columns]):
                    gi = row_start+column
                    label = '观测值' if group=='系列' else str(group)
                    ordered=ordered_groups[group]
                    reading=None
                    if compare_groups:
                        a,z=ordered[0],ordered[-1]
                        if a['value'] is None and z['value'] is None:reading='起末期均缺测'
                        elif a['value'] is None:reading='起期缺测'
                        elif z['value'] is None:reading='末期缺测'
                        elif len(groups)>1:reading=fmt(float(format(a['value'],'.4g')))+' → '+fmt(float(format(z['value'],'.4g')))
                        else:reading='空心起期 / 实心末期'
                    parts = [label[i:i+limit] for i in range(0,len(label),limit)]
                    if reading:
                        reading_width=sum(7.5 if ord(ch)<256 else 14 for ch in reading)
                        if reading_width>cell-20 and a['value'] is not None and z['value'] is not None:
                            parts.extend(['起 '+fmt(float(format(a['value'],'.4g'))),'末 '+fmt(float(format(z['value'],'.4g')))])
                        else:parts.append(reading)
                    legends.append((left+column*cell,legend_y,parts,gi))
                    row_height = max(row_height,len(parts)*17)
                legend_y += row_height+4
            endpoint_pair=None
            if len(groups)==1:
                ordered=sorted(next(iter(groups.values())),key=lambda r:r['x'])
                if len(ordered)>1 and ordered[0]['value'] is not None and ordered[-1]['value'] is not None:
                    endpoint_pair=(ordered[0],ordered[-1])
                    a,z=endpoint_pair
                    change=float(Decimal(str(z['value']))-Decimal(str(a['value'])))
                    delta_unit='百分点' if c['unit']=='%' else c['unit']
                    text(left,legend_y+14,a['x']+' → '+z['x'],cls='comparison-note')
                    text(left,legend_y+35,'首尾差 '+('+' if change>0 else '')+fmt(change)+' '+delta_unit,cls='comparison-note')
                    legend_y+=43
            extra = max(0,legend_y+12-top)
            top += extra; bottom += extra; height += extra
            yy, lo, hi = axis_y(vals)
            times = [dt.date.fromisoformat(r['x']).toordinal() for r in rows]
            minx, maxx = min(times), max(times)
            xx = lambda v: left + (v-minx) / (maxx-minx or 1) * (right-left)
            for gi, (group, rr) in enumerate(groups.items()):
                color = COLORS[gi % len(COLORS)]
                ordered=ordered_groups[group]
                paired=compare_groups and ordered[0]['value'] is not None and ordered[-1]['value'] is not None
                segments, segment = [], []
                for r in sorted(rr, key=lambda r:r['x']):
                    if r['value'] is None:
                        if segment: segments.append(segment)
                        segment = []
                        continue
                    px, py = xx(dt.date.fromisoformat(r['x']).toordinal()), yy(r['value'])
                    segment.append((px, py))
                    is_endpoint=paired and (r is ordered[0] or r is ordered[-1])
                    dot(px, py, r['value'], f'{group} {r["x"]}：{fmt(r["value"])} {c["unit"]}', color,5 if is_endpoint else 4,reference=paired and r is ordered[0])
                if segment: segments.append(segment)
                for segment in segments:
                    points = ' '.join(f'{x:.3f},{y:.3f}' for x,y in segment)
                    out.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.4" stroke-dasharray="{LINE_DASHES[gi % len(LINE_DASHES)]}"/>')
            dates = sorted(set(r['x'] for r in rows))
            step = max(1, math.ceil(len(dates)/(4 if mobile else 7)))
            for date in dates[::step]:
                text(xx(dt.date.fromisoformat(date).toordinal()), bottom+26, date[5:] if c['frequency'] != 'year' else date[:4], 'middle', 'tick')
            for lx,ly,parts,gi in legends:
                out.append(f'<line x1="{lx-22}" x2="{lx-5}" y1="{ly-4}" y2="{ly-4}" stroke="{COLORS[gi % len(COLORS)]}" stroke-width="3" stroke-dasharray="{LINE_DASHES[gi % len(LINE_DASHES)]}"/>')
                for index,part in enumerate(parts):
                    text(lx,ly+index*17,part,cls='legend')
    elif kind == 'stacked':
        left = 100 if mobile else 165
        def wrap_reading(value,limit):
            lines,part,used=[], '',0
            for ch in value:
                advance=.55 if ord(ch)<256 else 1
                if part and used+advance>limit:
                    lines.append(part)
                    part,used='',0
                part+=ch
                used+=advance
            if part:lines.append(part)
            return lines
        summaries=[]
        for r in rows:
            summary=' · '.join(k+' '+fmt(v)+('%' if c['unit']=='%' else '') for k,v in r['parts'].items())
            summaries.append(wrap_reading(summary,(width-16)/13))
        summary_offsets=[max(43,math.ceil(len(r['label'])/(6 if mobile else 11))*16+18) for r in rows]
        row_sizes=[max(64,offset+17*(len(lines)-1)+24) for offset,lines in zip(summary_offsets,summaries)]
        names = list(dict.fromkeys(k for r in rows for k in r['parts']))
        require(len(names) <= 6, 'more than six stack series: choose another layout')
        columns=2 if mobile else 4
        cell_width=(width-20)/columns
        legend_lines=[wrap_reading(name,(cell_width-25)/13) for name in names]
        header_heights=[max(len(v) for v in legend_lines[i:i+columns])*17+8 for i in range(0,len(names),columns)]
        chart_top=max(65,26+sum(header_heights))
        height = max(160, chart_top+sum(row_sizes)+35)
        bottom = height - 35
        maxima = 100 if c.get('percent') else max(sum(r['parts'].values()) for r in rows)
        scale = (right-left)/(maxima or 1)
        for j, name in enumerate(names):
            lx, ly = 10 + (j % columns)*cell_width,16+sum(header_heights[:j//columns])
            out.append(f'<rect x="{lx}" y="{ly-9}" width="9" height="9" fill="{COLORS[j]}" stroke="var(--ink)" stroke-width=".5"/>')
            for line_index,part in enumerate(legend_lines[j]):text(lx+15,ly+line_index*17,part,cls='legend')
        for i, r in enumerate(rows):
            yy, start = chart_top + sum(row_sizes[:i]), 0
            category_text(left-10, yy+13, r['label'], 'end', 6 if mobile else 11)
            denom = sum(r['parts'].values())
            for j, name in enumerate(names):
                if name not in r['parts']:
                    continue  # Absent categories are not invented as zero rows.
                raw = r['parts'][name]
                value = raw/denom*100 if c.get('percent') else raw
                rect(left+start*scale, yy, value*scale, 25, value, f'{r["label"]} {name}：{fmt(raw)} {c["unit"]}' + (f'，占{value:.1f}%' if c.get('percent') else ''), COLORS[j], 'x', start, start+value, scale)
                label=fmt(float(format(value,'.12g')))+'%' if c.get('percent') else fmt(raw)+('%' if c['unit']=='%' else '')
                if value*scale >= len(label)*8+12:
                    text(left+(start+value/2)*scale,yy+18,label,'middle','stack-value','style="fill:var(--ink);stroke:var(--paper);stroke-width:1.6;paint-order:stroke"')
                start += value
            for j,label in enumerate(summaries[i]):text(8,yy+summary_offsets[i]+j*17,label,cls='tick')
            text(width-4, yy-8, f'合计 {fmt(denom)}', 'end', 'tick')
    elif kind == 'waterfall':
        cumulative, segments = 0, []
        for r in rows:
            if r['role'] in {'start', 'total'}:
                a, b = 0, r['value']
            else:
                a, b = cumulative, cumulative+r['value']
            segments.append((a,b))
            cumulative = b
        net=float(Decimal(str(rows[-1]['value']))-Decimal(str(rows[0]['value'])))
        text(left,17,'净变化 '+('+' if net>0 else '')+fmt(net)+' '+c['unit'],cls='comparison-note')
        yy, lo, hi = axis_y([v for segment in segments for v in segment], True)
        step = (right-left)/len(rows)
        scale = (bottom-top)/(hi-lo)
        for i,(r,(a,b)) in enumerate(zip(rows,segments)):
            x, bw = left+i*step+step*.18, step*.64
            direction = c.get('performance_direction', 'neutral')
            if r['role'] != 'change':
                color = 'var(--ink)'
            elif direction == 'neutral':
                color = 'var(--accent)' if r['value'] >= 0 else 'var(--series)'
            else:
                favorable = (r['value'] >= 0) == (direction == 'higher')
                color = 'var(--positive)' if favorable else 'var(--negative)'
            rect(x, min(yy(a),yy(b)), bw, abs(yy(b)-yy(a)), r['value'], f'{r["label"]}：{fmt(r["value"])} {c["unit"]}', color, 'y', a, b, scale)
            if r['role']=='start':
                out.append(f'<rect x="{x:.3f}" y="{min(yy(a),yy(b)):.3f}" width="{bw:.3f}" height="{abs(yy(b)-yy(a)):.3f}" fill="var(--paper)" stroke="var(--ink)" stroke-width="1.6" stroke-dasharray="4 3" pointer-events="none"/>')
            text(x+bw/2, min(yy(a),yy(b))-9, ('+' if r['role']=='change' and r['value']>0 else '')+fmt(r['value']), 'middle', 'value')
            category_text(x+bw/2, bottom+23, r['label'], 'middle', 4 if mobile else 9)
            if i<len(rows)-1:
                line(x+bw,yy(b),left+(i+1)*step+step*.18,yy(b),dash='3 3')
    elif kind == 'box':
        if not vals:
            empty()
        else:
            yy,lo,hi = axis_y(vals)
            groups = collections.defaultdict(list)
            for r in rows:
                if r['value'] is not None: groups[r['label']].append(r['value'])
            step=(right-left)/max(1,len(groups))
            for i,(label, vv) in enumerate(groups.items()):
                x=left+(i+.5)*step
                q1,med,q3 = quantile(vv,.25),quantile(vv,.5),quantile(vv,.75)
                iqr=q3-q1
                inner=[v for v in vv if q1-1.5*iqr<=v<=q3+1.5*iqr]
                line(x,yy(min(inner)),x,yy(max(inner)),'var(--accent)')
                for k,v in enumerate(sorted(vv)):
                    offset=((k*7)%17-8)*min(1.8,step/50)
                    dot(x+offset,yy(v),v,f'{label} 原始值 {fmt(v)} {c["unit"]}','var(--muted)',3)
                mark_axis = ' data-box-direction="y"' if c.get('shape') else ''
                out.append(f'<rect x="{x-18:.3f}" y="{yy(q3):.3f}" width="36" height="{max(0,yy(q1)-yy(q3)):.3f}" fill="var(--paper)" fill-opacity=".75" stroke="var(--accent)"{mark_axis}/>')
                line(x-18,yy(med),x+18,yy(med),'var(--accent)')
                text(x,bottom+25,label,'middle','category')
                text(x,top-13,f'n={len(vv)}','middle','tick')
                text(x,bottom+43,fmt(float(format(med,'.4g'))),'middle','annotated-value')
                ledger.append({'shape':'box','label':label,'q1':q1,'median':med,'q3':q3,'low':min(inner),'high':max(inner),'n':len(vv)})
            text(4,bottom+43,'中位数',cls='tick')
    elif kind == 'scatter':
        points=[r for r in rows if r['x'] is not None and r['y'] is not None]
        if not points:
            empty()
        else:
            yy,lo,hi=axis_y([r['y'] for r in points])
            xlo,xhi=extent([r['x'] for r in points])
            xx=lambda v:left+(v-xlo)/(xhi-xlo)*(right-left)
            ticks = [xlo+(xhi-xlo)*i/3 for i in range(4)]
            if tight and xlo < 0 < xhi:
                line(xx(0),top,xx(0),bottom,'var(--muted)','4 4')
                ticks = sorted([v for v in ticks if abs(xx(v)-xx(0)) >= 35] + [0])
            if tight and lo < 0 < hi:
                line(left,yy(0),right,yy(0),'var(--muted)','4 4')
            for v in ticks:
                text(xx(v),bottom+25,fmt(v, axis=True),'middle','tick')
            labels=[]
            extreme_indices=set()
            if c.get('label_extremes',True):
                for key in ['x','y']:
                    extreme_indices.update([min(range(len(points)),key=lambda i:points[i][key]),max(range(len(points)),key=lambda i:points[i][key])])
            coordinates=[(xx(r['x']),yy(r['y'])) for r in points]
            for index,r in enumerate(points):
                color = 'var(--series)' if tight and any(row.get('highlight') for row in points) and not r.get('highlight') else 'var(--accent)'
                dot(xx(r['x']),yy(r['y']),r['y'],f'{r["label"]}：{fmt(r["x"])} {c["x_unit"]}，{fmt(r["y"])} {c["y_unit"]}',color,5)
                if r.get('highlight') or index in extreme_indices:
                    px,py=coordinates[index]
                    reading=r['label']+' · '+fmt(float(format(r['y'],'.4g')))
                    size=sum(7.5 if ord(ch)<256 else 14 for ch in reading)
                    for lx,ly,anchor in [(px+9,py-11,'start'),(px+9,py+22,'start'),(px-9,py-11,'end'),(px-9,py+22,'end')]:
                        l=lx if anchor=='start' else lx-size
                        box=(l,ly-14,l+size,ly+3)
                        inside=box[0]>=left and box[2]<=right and box[1]>=top-8 and box[3]<=bottom+4
                        collision=any(not(box[2]+4<a or box[0]-4>z or box[3]+3<b or box[1]-3>t) for a,b,z,t in labels)
                        covered=any(box[0]-5<x<box[2]+5 and box[1]-5<y<box[3]+5 for x,y in coordinates)
                        if inside and not collision and not covered:
                            text(lx,ly,reading,anchor,'value')
                            labels.append(box)
                            break
            text((left+right)/2,height-6,c['x_unit'],'middle','tick')
            text(6,16,c['y_unit'],cls='tick')
    label=f'{c["title"]}。{c["question"]}。{c["unit"]}。完整数值见同源数据表。'
    svg=f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}" class="{"mobile-svg" if mobile else "desktop-svg"}"><title>{esc(label)}</title>'+''.join(out)+'</svg>'
    return svg_shape(svg, c), ledger


def svg_shape(svg, chart):
    if chart.get('shape') in {None, 'solid'}:
        return svg
    from chart_shapes import apply_shape
    return apply_shape(svg, chart['kind'], chart['shape'])


CSS = '''
:root{--paper:#fff;--bg:#f3f3ef;--ink:#18292f;--muted:#53626a;--rule:#d7dddf;--accent:#225b69;--series:#527984;--negative:#9a4b29}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI","Microsoft YaHei",sans-serif;font-size:15px;line-height:1.6}a{color:var(--accent)}button,select,summary{font:inherit}button,select{padding:8px 13px;border:1px solid #aab5ba;background:white;color:var(--ink);border-radius:3px}button{cursor:pointer}:focus-visible{outline:3px solid #9a4b29;outline-offset:4px}header,main,footer{max-width:1180px;margin:auto;padding:28px 42px}header{padding-top:46px}header h1{font-size:clamp(28px,4vw,49px);line-height:1.2;max-width:960px;letter-spacing:-.04em;margin:20px 0}.eyebrow{font-size:12px;letter-spacing:.15em;font-weight:700;text-transform:uppercase}.intro{max-width:800px;color:var(--muted)}.notice{font-weight:600;color:#814026}nav{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:22px}.status{font-size:13px;color:var(--muted)}.charts{display:grid;gap:32px}.panel{background:var(--paper);padding:28px 30px;border-top:2px solid var(--ink);min-width:0}.panel h2{font-size:23px;line-height:1.35;margin:4px 0 10px;letter-spacing:-.025em}.q{color:var(--muted);font-size:14px;margin:0 0 8px}.scope,.source{font-size:12px;color:var(--muted);overflow-wrap:anywhere}.scope{margin-bottom:12px}.source{padding-top:12px;border-top:1px solid var(--rule)}svg{width:100%;height:auto;display:block;overflow:visible}svg text{font-family:inherit;font-size:13px;fill:var(--ink);font-variant-numeric:tabular-nums}svg .tick{font-size:12px;fill:var(--muted)}svg .value{font-weight:650;font-size:13px}svg .legend{font-weight:600;font-size:12px}svg .muted{fill:var(--muted)}svg .empty{font-size:17px}.mobile-svg{display:none}.table-scroll{overflow:auto;max-width:100%}details{margin-top:16px}summary{cursor:pointer;color:var(--accent);font-weight:600}table{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}th,td{border-bottom:1px solid var(--rule);padding:9px;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}caption{text-align:left;font-size:12px;margin:6px 0;color:var(--muted)}.note{color:var(--muted);font-size:13px;margin:12px 0}.claims{font-size:14px;font-weight:600}.ledger{font-family:monospace;font-size:11px;overflow-wrap:anywhere;color:var(--muted)}footer{padding-bottom:60px}.layout-analytical .charts{grid-template-columns:1fr 1fr;gap:22px}.layout-analytical header h1{font-size:35px}.layout-analytical .panel{padding:24px}.layout-focus main{max-width:1040px}.layout-focus .panel[hidden]{display:none}.layout-focus nav{padding:16px;background:#e8eeee;border-left:3px solid var(--accent)}.layout-editorial .panel{display:grid;grid-template-columns:220px minmax(0,1fr);gap:26px}.layout-editorial .panel .data{align-self:start}.layout-editorial .panel h2{font-size:26px}.layout-editorial .panel .source{grid-column:1/-1}.sample-label{font-size:12px;color:var(--muted)}[hidden]{display:none!important}
@media(max-width:700px){header,main,footer{padding:22px 18px}header{padding-top:24px}.panel,.layout-analytical .panel{padding:20px 12px}.layout-editorial .panel{display:block}.layout-analytical .charts{grid-template-columns:1fr}.desktop-svg{display:none}.mobile-svg{display:block}.panel h2,.layout-editorial .panel h2{font-size:22px}.charts{gap:22px}nav label{width:100%}select{max-width:100%}.source{margin-top:14px}table{font-size:13px}}
@media print{body{background:white}header,main,footer{max-width:none;padding:12px}nav,.screen-only{display:none}.charts,.layout-analytical .charts{display:block}.panel,.layout-editorial .panel{display:block;border-top:1px solid #333;break-inside:avoid;margin-bottom:20px;padding:16px}.panel[hidden]{display:block!important}.desktop-svg{display:block}.mobile-svg{display:none}details{display:block}.table-scroll{overflow:visible}details:not([open])>div{display:block}a{color:inherit}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
svg text,svg .tick,svg .value,svg .legend{font-size:14px}
svg .target-reading{font-size:22px;font-weight:700;fill:var(--accent)}
svg .target-unknown{font-weight:400;fill:var(--muted)}
svg .comparison-note{font-size:14px;fill:var(--muted)}svg .annotated-value{font-size:14px;fill:var(--accent);font-weight:700}
.layout-analytical .desktop-svg{display:none}.layout-analytical .mobile-svg{display:block}.layout-analytical svg text,.layout-analytical svg .tick,.layout-analytical svg .value,.layout-analytical svg .legend{font-size:11px}
@media(max-width:700px){.layout-analytical svg text,.layout-analytical svg .tick,.layout-analytical svg .value,.layout-analytical svg .legend{font-size:14px}}
@media print{.layout-analytical .desktop-svg{display:block}.layout-analytical .mobile-svg{display:none}}
.compact-chart{display:none;max-width:100%;overflow-x:auto;overscroll-behavior-x:contain}.compact-svg{display:none}.compact-chart:has(.compact-wide)::before{content:"图表较宽，可左右滑动查看。";display:block;font-size:13px;color:var(--muted);margin-bottom:8px}
@media screen and (max-width:400px){.desktop-svg,.mobile-svg,.layout-comparison .mobile-svg,.layout-analytical .mobile-svg{display:none!important}.compact-chart{display:block}.compact-chart .compact-svg{display:block;width:100%;height:auto;max-width:360px;margin:0 auto}.compact-chart .compact-wide{max-width:none}.compact-chart svg text,.compact-chart svg .tick,.compact-chart svg .legend,.compact-chart svg .value,.compact-chart svg .target-reading,.compact-chart svg .comparison-note,.compact-chart svg .annotated-value{font-size:14px}.compact-chart svg .target-reading{font-weight:700}}
@media print{.compact-chart,.compact-svg{display:none!important}}
'''

JS = '''
const spec=JSON.parse(document.getElementById('chart-spec').textContent);
const panels=[...document.querySelectorAll('.panel[data-chart-id]')], select=document.getElementById('chart-select');
function selectChart(){const id=select.value;panels.forEach(p=>p.hidden=id!=='all'&&p.dataset.chartId!==id);const n=panels.filter(p=>!p.hidden).length;document.getElementById('view-status').textContent=`显示 ${n} / ${panels.length} 张图；数据范围未改变`;}
select.addEventListener('change',selectChart);document.getElementById('reset').addEventListener('click',()=>{select.value='all';selectChart();});
document.getElementById('download').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(spec,null,2)],{type:'application/json;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='chart-spec.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);});
if(document.body.classList.contains('layout-focus'))select.value=spec.charts[0].id;
let printState=[];
addEventListener('beforeprint',()=>{printState=[...document.querySelectorAll('details')].map(d=>[d,d.open]);printState.forEach(([d])=>d.open=true);});
addEventListener('afterprint',()=>{printState.forEach(([d,open])=>d.open=open);});
selectChart();document.documentElement.dataset.chartReady='true';
'''


def build(spec, layout='editorial', theme=None, *, brand_accent=None):
    result=validate(spec)
    require(layout in {'editorial','analytical','focus'}, 'unknown layout')
    theme_id = theme or spec.get('theme', 'graphite' if brand_accent is not None else 'tidal')
    css = CSS + theme_css(theme_id, brand_accent=brand_accent)
    credit = theme_credit(theme_id)
    credit_html = f'<p class="palette-credit">{esc(credit)}</p>' if credit else ''
    panels,ledgers=[],{}
    for i,c in enumerate(spec['charts']):
        display_unit = '占比（%），原始值：'+c['unit'] if c['kind']=='stacked' and c.get('percent') else c['unit']
        svg,ledger=svg_chart(c)
        mobile,ml=svg_chart(c,True)
        compact,cl=svg_chart(c,compact=True)
        ledgers[c['id']]={'desktop':ledger,'mobile':ml,'compact':cl,'data_sha256':digest(c['rows'])}
        fields=list(dict.fromkeys(k for r in c['rows'] for k in r))
        field_names={'label':'对象','value':'数值','group':'分组','parts':'构成','role':'增减类型','highlight':'重点标记','x':'日期' if c['kind']=='line' else c.get('x_unit','横轴数值'),'y':c.get('y_unit','纵轴数值')}
        headings=''.join(f'<th scope="col">{esc(field_names.get(k,k))}</th>' for k in fields)
        tr=''.join('<tr>'+''.join(f'<td>{esc(fmt(r.get(k)))}</td>' for k in fields)+'</tr>' for r in c['rows'])
        source=f'来源：{c["source"]} · 期间：{c["period"]} · 范围：{c["scope"]} · 单位：{display_unit}'
        notes=c.get('note','')
        if c['kind']=='waterfall':
            direction = c.get('performance_direction', 'neutral')
            notes += ' 颜色仅区分增减，不判断好坏。' if direction == 'neutral' else (' 数值越高越有利。' if direction == 'higher' else ' 数值越低越有利。')
        if c['kind']=='box': notes+=' 分位数采用线性插值；须为1.5×IQR范围内最远原始值；原始点全部保留，n为非缺失观测数。'
        missing=sum(1 for r in c['rows'] if (r.get('value') is None if c['kind'] not in {'stacked','scatter'} else c['kind']=='scatter' and (r['x'] is None or r['y'] is None)))
        if missing: notes+=f' 含{missing}条缺失记录；未替换为零。'
        claims=''.join(f'<p class="claims">核对值 · {esc(cl["method"])} = {esc(fmt(cl["expected"]))}</p>' for cl in c.get('claims',[]))
        panels.append(f'<section class="panel" data-chart-id="{esc(c["id"])}" aria-labelledby="title-{i}"><div class="heading"><span class="eyebrow">{i+1:02d} / {esc(c["kind"])}</span><h2 id="title-{i}">{esc(c["title"])}</h2><p class="q">{esc(c["question"])}</p><p class="scope">{esc(c["period"])} · {esc(c["unit"])}</p>{claims}<p class="note">{esc(notes)}</p></div><div class="data">{svg}{mobile}<details><summary>查看同源数据（{len(c["rows"])}条）</summary><div class="table-scroll"><table><caption>{esc(c["scope"])}</caption><thead><tr>{headings}</tr></thead><tbody>{tr}</tbody></table></div></details></div><div class="source">{esc(source)}</div></section>')
        panels[-1]=panels[-1].replace(f'{svg}{mobile}',f'{svg}{mobile}<div class="compact-chart">{compact}</div>')
        if display_unit != c['unit']:
            panels[-1] = panels[-1].replace(f'<p class="scope">{esc(c["period"])} · {esc(c["unit"])}</p>', f'<p class="scope">{esc(c["period"])} · {esc(display_unit)}</p>')
        panels[-1] = panels[-1].replace(f'{i+1:02d} / {esc(c["kind"])}', f'{i+1:02d} / {KIND_NAMES[c["kind"]]}')
        for method,label in {'sum':'合计','mean':'平均','median':'中位数','count':'有效记录数'}.items():
            panels[-1] = panels[-1].replace(f'核对值 · {method} = ', label+' ')
    options='<option value="all">全部图表</option>'+''.join(f'<option value="{esc(c["id"])}">{esc(c["title"])}</option>' for c in spec['charts'])
    data=canonical(spec).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    ledger=canonical(ledgers).replace('<','\\u003c')
    intro=spec.get('intro','')
    disclosure='合成测试数据，仅用于验证图表；不是实际经营事实。' if spec.get('synthetic') else spec.get('data_note','')
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="chart-data-sha256" content="{result["sha256"]}"><title>{esc(spec["title"])}</title><style>{css}</style></head><body class="layout-{layout}"><header><div class="eyebrow">Data charts / {layout}</div><h1>{esc(spec["title"])}</h1><p class="intro">{esc(intro)}</p><p class="notice">{esc(disclosure)}</p><nav aria-label="图表视图"><label for="chart-select">定位问题</label><select id="chart-select">{options}</select><button id="reset" type="button">显示全部</button><button id="download" type="button">下载源数据</button><span id="view-status" class="status" role="status" aria-live="polite"></span></nav><noscript>当前为静态完整视图；数值和数据表可读，视图定位与下载按钮需要JavaScript。</noscript></header><main><div class="charts">'+''.join(panels)+f'</div></main><footer><p>图表、表格与标注来自同一份输入。数据文件随HTML交付；浏览器下载也可取得完整输入。</p>{credit_html}<p class="ledger">数据SHA-256：{result["sha256"]}</p><p class="sample-label">本页检查数值合同与渲染；标题的业务判断、因果和审美仍需审阅。</p></footer><script id="chart-spec" type="application/json">{data}</script><script id="chart-ledger" type="application/json">{ledger}</script><script>{JS}</script></body></html>'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['validate','build'])
    parser.add_argument('spec',type=Path)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--layout',choices=['editorial','analytical','focus'],default='editorial')
    parser.add_argument('--theme', help='Palette ID from assets/color-system.json. Defaults to spec.theme or tidal.')
    parser.add_argument('--brand-accent', help='Exact #RRGGBB focus color; defaults the base palette to graphite')
    args=parser.parse_args()
    try:
        spec=json.loads(args.spec.read_text(encoding='utf-8-sig'))
        result=validate(spec)
        if args.command=='build':
            require(args.out is not None,'--out is required for build')
            content=build(spec,args.layout,args.theme,brand_accent=args.brand_accent)
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(content,encoding='utf-8',newline='\n')
            # Save the exact source contract next to the delivered artifact.
            args.out.with_suffix('.data.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8',newline='\n')
            result['output']=str(args.out.resolve())
        print(json.dumps({'ok':True,**result},ensure_ascii=False))
    except (ValueError,TypeError,KeyError,OSError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    sys.exit(main())
