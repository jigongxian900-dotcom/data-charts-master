"""Offline SVG chart artifacts. Python stdlib only; no remote calls or data repair."""
import argparse
import collections
import datetime as dt
from decimal import Decimal
import hashlib
import html
import json
import math
from pathlib import Path
import statistics
import sys

KINDS = {'bar', 'line', 'stacked', 'waterfall', 'box', 'scatter'}
KIND_NAMES = {'bar':'比较高低','line':'观察趋势','stacked':'比较构成','waterfall':'核对增减','box':'观察分布','scatter':'观察关联'}
COLORS = [f'var(--category{i})' for i in range(8)]
LINE_DASHES = ['', '7 4', '2 3', '10 3 2 3', '12 5', '4 2 1 2', '1 4', '8 2 2 2 2 2']
COLOR_SYSTEM = Path(__file__).resolve().parents[1] / 'assets' / 'color-system.json'


def theme_css(theme_id):
    themes = json.loads(COLOR_SYSTEM.read_text(encoding='utf-8'))['themes']
    selected = next((t for t in themes if t['id'] == theme_id), None)
    require(selected is not None, f'unknown color theme: {theme_id}')
    roles = {'paper':'surface', 'bg':'paper', 'ink':'ink', 'muted':'muted',
             'rule':'grid', 'accent':'accent', 'series':'accent2', 'positive':'positive', 'negative':'negative'}
    tokens = {k:selected[v] for k,v in roles.items()}
    tokens.update({f'category{i}':c for i,c in enumerate(selected['categorical'])})
    print_theme = next(t for t in themes if t['id']=='tidal') if theme_id=='nocturne' else selected
    print_tokens = {k:print_theme[v] for k,v in roles.items()}
    print_tokens.update({f'category{i}':c for i,c in enumerate(print_theme['categorical'])})
    print_tokens.update({'bg':'#FFFFFF','paper':'#FFFFFF'})
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


def svg_chart(c, mobile=False):
    width, height = (360, 340) if mobile else (760, 360)
    left, right, top, bottom = (58, width - 35, 36, height - 55)
    kind, rows = c['kind'], c['rows']
    out, ledger = [], []
    def text(x, y, value, anchor='start', cls='', extra=''):
        out.append(f'<text x="{x:.3f}" y="{y:.3f}" text-anchor="{anchor}" class="{cls}" {extra}>{esc(value)}</text>')
    def line(x1, y1, x2, y2, color='var(--rule)', dash=''):
        out.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-dasharray="{dash}"/>')
    def dot(x, y, value, label, color, radius=4):
        out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{radius}" fill="{color}" stroke="var(--paper)" tabindex="0" role="img" aria-label="{esc(label)}"><title>{esc(label)}</title></circle>')
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
        parts = [str(label)[i:i+limit] for i in range(0, len(str(label)), limit)]
        for i, part in enumerate(parts):
            text(x, y + i * 16, part, anchor, 'category')
    def empty():
        text(width / 2, height / 2, '当前没有可绘制的数据', 'middle', 'empty')
    vals = [r.get('value') for r in rows if num(r.get('value'))]
    if not rows:
        empty()
    elif kind == 'bar':
        left = 138 if mobile else 205
        value_space = max(68, max((len(fmt(v))*7.5+12 for v in vals), default=68))
        right = width - value_space
        require(right > left + 30, 'values too wide for this layout; choose a table or a wider canvas')
        # Reserve actual Chinese glyph width, not an ASCII-sized estimate.
        # Twelve full-width glyphs fit the 193px desktop label column with
        # a font-fallback margin; wrapped rows grow with the same limit.
        label_limit = 8 if mobile else 12
        row_sizes = [max(56 if mobile else 49, math.ceil(len(r['label'])/label_limit)*16+20) for r in rows]
        height = max(210, sum(row_sizes) + 80)
        bottom = height - 38
        if not vals:
            empty()
        else:
            lo, hi = extent(vals, True)
            x = lambda v: left + (v - lo) / (hi - lo) * (right - left)
            scale = (right - left) / (hi - lo)
            line(x(0), top - 7, x(0), bottom)
            text(x(0),top-12,'0','middle','tick')
            for i, r in enumerate(rows):
                yy = top + 15 + sum(row_sizes[:i])
                category_text(left-12, yy, r['label'], 'end', label_limit)
                v = r['value']
                if v is None:
                    text(left + 7, yy, '缺失', cls='muted')
                    continue
                color = 'var(--accent)' if r.get('highlight') else 'var(--series)'
                rect(min(x(0), x(v)), yy-13, abs(x(v)-x(0)), 21, v, f'{r["label"]}：{fmt(v)} {c["unit"]}', color, 'x', 0, v, scale)
                # A stable value column prevents labels crossing negative bars.
                text(width-4, yy+3, fmt(v), 'end', 'value')
    elif kind == 'line':
        if not vals:
            empty()
        else:
            groups = collections.defaultdict(list)
            for r in rows:
                groups[r.get('group', '系列')].append(r)
            # Each character gets a full-em fallback allowance, including
            # Latin names, so long series names wrap inside the SVG instead
            # of relying on visible overflow. Grow the canvas, not tiny type.
            columns = 2 if mobile else 4
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
                    label = str(group)
                    parts = [label[i:i+limit] for i in range(0,len(label),limit)]
                    legends.append((left+column*cell,legend_y,parts,gi))
                    row_height = max(row_height,len(parts)*17)
                legend_y += row_height+4
            extra = max(0,legend_y+12-top)
            top += extra; bottom += extra; height += extra
            yy, lo, hi = axis_y(vals)
            times = [dt.date.fromisoformat(r['x']).toordinal() for r in rows]
            minx, maxx = min(times), max(times)
            xx = lambda v: left + (v-minx) / (maxx-minx or 1) * (right-left)
            for gi, (group, rr) in enumerate(groups.items()):
                color = COLORS[gi % len(COLORS)]
                segments, segment = [], []
                for r in sorted(rr, key=lambda r:r['x']):
                    if r['value'] is None:
                        if segment: segments.append(segment)
                        segment = []
                        continue
                    px, py = xx(dt.date.fromisoformat(r['x']).toordinal()), yy(r['value'])
                    segment.append((px, py))
                    dot(px, py, r['value'], f'{group} {r["x"]}：{fmt(r["value"])} {c["unit"]}', color)
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
        height = max(230, 95 + len(rows)*53)
        bottom = height - 35
        names = list(dict.fromkeys(k for r in rows for k in r['parts']))
        require(len(names) <= 6, 'more than six stack series: choose another layout')
        maxima = 100 if c.get('percent') else max(sum(r['parts'].values()) for r in rows)
        scale = (right-left)/(maxima or 1)
        for j, name in enumerate(names):
            lx, ly = 10 + (j % (2 if mobile else 4)) * (170 if mobile else 185), 16 + (j // (2 if mobile else 4))*17
            out.append(f'<rect x="{lx}" y="{ly-9}" width="9" height="9" fill="{COLORS[j]}" stroke="var(--ink)" stroke-width=".5"/>')
            text(lx+15, ly, name, cls='legend')
        for i, r in enumerate(rows):
            yy, start = 65 + i*53, 0
            category_text(left-10, yy+13, r['label'], 'end', 6 if mobile else 11)
            denom = sum(r['parts'].values())
            for j, name in enumerate(names):
                if name not in r['parts']:
                    continue  # Absent categories are not invented as zero rows.
                raw = r['parts'][name]
                value = raw/denom*100 if c.get('percent') else raw
                rect(left+start*scale, yy, value*scale, 25, value, f'{r["label"]} {name}：{fmt(raw)} {c["unit"]}' + (f'，占{value:.1f}%' if c.get('percent') else ''), COLORS[j], 'x', start, start+value, scale)
                start += value
            text(width-4, yy+39, f'合计 {fmt(denom)}', 'end', 'tick')
    elif kind == 'waterfall':
        cumulative, segments = 0, []
        for r in rows:
            if r['role'] in {'start', 'total'}:
                a, b = 0, r['value']
            else:
                a, b = cumulative, cumulative+r['value']
            segments.append((a,b))
            cumulative = b
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
                out.append(f'<rect x="{x-18:.3f}" y="{yy(q3):.3f}" width="36" height="{max(0,yy(q1)-yy(q3)):.3f}" fill="var(--paper)" fill-opacity=".75" stroke="var(--accent)"/>')
                line(x-18,yy(med),x+18,yy(med),'var(--accent)')
                text(x,bottom+25,label,'middle','category')
                text(x,top-13,f'n={len(vv)}','middle','tick')
                ledger.append({'shape':'box','label':label,'q1':q1,'median':med,'q3':q3,'low':min(inner),'high':max(inner),'n':len(vv)})
    elif kind == 'scatter':
        points=[r for r in rows if r['x'] is not None and r['y'] is not None]
        if not points:
            empty()
        else:
            yy,lo,hi=axis_y([r['y'] for r in points])
            xlo,xhi=extent([r['x'] for r in points])
            xx=lambda v:left+(v-xlo)/(xhi-xlo)*(right-left)
            for i in range(4):
                v=xlo+(xhi-xlo)*i/3
                text(xx(v),bottom+25,fmt(v, axis=True),'middle','tick')
            for r in points:
                dot(xx(r['x']),yy(r['y']),r['y'],f'{r["label"]}：{fmt(r["x"])} {c["x_unit"]}，{fmt(r["y"])} {c["y_unit"]}','var(--accent)',5)
                if r.get('highlight'):
                    text(xx(r['x'])+8,yy(r['y'])-9,r['label'],cls='value')
            text((left+right)/2,height-6,c['x_unit'],'middle','tick')
            text(6,16,c['y_unit'],cls='tick')
    label=f'{c["title"]}。{c["question"]}。{c["unit"]}。完整数值见同源数据表。'
    svg=f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}" class="{"mobile-svg" if mobile else "desktop-svg"}"><title>{esc(label)}</title>'+''.join(out)+'</svg>'
    return svg,ledger


CSS = '''
:root{--paper:#fff;--bg:#f3f3ef;--ink:#18292f;--muted:#53626a;--rule:#d7dddf;--accent:#225b69;--series:#527984;--negative:#9a4b29}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI","Microsoft YaHei",sans-serif;font-size:15px;line-height:1.6}a{color:var(--accent)}button,select,summary{font:inherit}button,select{padding:8px 13px;border:1px solid #aab5ba;background:white;color:var(--ink);border-radius:3px}button{cursor:pointer}:focus-visible{outline:3px solid #9a4b29;outline-offset:4px}header,main,footer{max-width:1180px;margin:auto;padding:28px 42px}header{padding-top:46px}header h1{font-size:clamp(28px,4vw,49px);line-height:1.2;max-width:960px;letter-spacing:-.04em;margin:20px 0}.eyebrow{font-size:12px;letter-spacing:.15em;font-weight:700;text-transform:uppercase}.intro{max-width:800px;color:var(--muted)}.notice{font-weight:600;color:#814026}nav{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:22px}.status{font-size:13px;color:var(--muted)}.charts{display:grid;gap:32px}.panel{background:var(--paper);padding:28px 30px;border-top:2px solid var(--ink);min-width:0}.panel h2{font-size:23px;line-height:1.35;margin:4px 0 10px;letter-spacing:-.025em}.q{color:var(--muted);font-size:14px;margin:0 0 8px}.scope,.source{font-size:12px;color:var(--muted);overflow-wrap:anywhere}.scope{margin-bottom:12px}.source{padding-top:12px;border-top:1px solid var(--rule)}svg{width:100%;height:auto;display:block;overflow:visible}svg text{font-family:inherit;font-size:13px;fill:var(--ink);font-variant-numeric:tabular-nums}svg .tick{font-size:12px;fill:var(--muted)}svg .value{font-weight:650;font-size:13px}svg .legend{font-weight:600;font-size:12px}svg .muted{fill:var(--muted)}svg .empty{font-size:17px}.mobile-svg{display:none}.table-scroll{overflow:auto;max-width:100%}details{margin-top:16px}summary{cursor:pointer;color:var(--accent);font-weight:600}table{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}th,td{border-bottom:1px solid var(--rule);padding:9px;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}caption{text-align:left;font-size:12px;margin:6px 0;color:var(--muted)}.note{color:var(--muted);font-size:13px;margin:12px 0}.claims{font-size:14px;font-weight:600}.ledger{font-family:monospace;font-size:11px;overflow-wrap:anywhere;color:var(--muted)}footer{padding-bottom:60px}.layout-analytical .charts{grid-template-columns:1fr 1fr;gap:22px}.layout-analytical header h1{font-size:35px}.layout-analytical .panel{padding:24px}.layout-focus main{max-width:1040px}.layout-focus .panel[hidden]{display:none}.layout-focus nav{padding:16px;background:#e8eeee;border-left:3px solid var(--accent)}.layout-editorial .panel{display:grid;grid-template-columns:220px minmax(0,1fr);gap:26px}.layout-editorial .panel .data{align-self:start}.layout-editorial .panel h2{font-size:26px}.layout-editorial .panel .source{grid-column:1/-1}.sample-label{font-size:12px;color:var(--muted)}[hidden]{display:none!important}
@media(max-width:700px){header,main,footer{padding:22px 18px}header{padding-top:24px}.panel,.layout-analytical .panel{padding:20px 12px}.layout-editorial .panel{display:block}.layout-analytical .charts{grid-template-columns:1fr}.desktop-svg{display:none}.mobile-svg{display:block}.panel h2,.layout-editorial .panel h2{font-size:22px}.charts{gap:22px}nav label{width:100%}select{max-width:100%}.source{margin-top:14px}table{font-size:13px}}
@media print{body{background:white}header,main,footer{max-width:none;padding:12px}nav,.screen-only{display:none}.charts,.layout-analytical .charts{display:block}.panel,.layout-editorial .panel{display:block;border-top:1px solid #333;break-inside:avoid;margin-bottom:20px;padding:16px}.panel[hidden]{display:block!important}.desktop-svg{display:block}.mobile-svg{display:none}details{display:block}.table-scroll{overflow:visible}details:not([open])>div{display:block}a{color:inherit}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
svg text,svg .tick,svg .value,svg .legend{font-size:14px}
.layout-analytical .desktop-svg{display:none}.layout-analytical .mobile-svg{display:block}.layout-analytical svg text,.layout-analytical svg .tick,.layout-analytical svg .value,.layout-analytical svg .legend{font-size:11px}
@media(max-width:700px){.layout-analytical svg text,.layout-analytical svg .tick,.layout-analytical svg .value,.layout-analytical svg .legend{font-size:14px}}
@media print{.layout-analytical .desktop-svg{display:block}.layout-analytical .mobile-svg{display:none}}
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


def build(spec, layout='editorial', theme=None):
    result=validate(spec)
    require(layout in {'editorial','analytical','focus'}, 'unknown layout')
    css = CSS + theme_css(theme or spec.get('theme', 'tidal'))
    panels,ledgers=[],{}
    for i,c in enumerate(spec['charts']):
        display_unit = '占比（%），原始值：'+c['unit'] if c['kind']=='stacked' and c.get('percent') else c['unit']
        svg,ledger=svg_chart(c)
        mobile,ml=svg_chart(c,True)
        ledgers[c['id']]={'desktop':ledger,'mobile':ml,'data_sha256':digest(c['rows'])}
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
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="chart-data-sha256" content="{result["sha256"]}"><title>{esc(spec["title"])}</title><style>{css}</style></head><body class="layout-{layout}"><header><div class="eyebrow">Data charts / {layout}</div><h1>{esc(spec["title"])}</h1><p class="intro">{esc(intro)}</p><p class="notice">{esc(disclosure)}</p><nav aria-label="图表视图"><label for="chart-select">定位问题</label><select id="chart-select">{options}</select><button id="reset" type="button">显示全部</button><button id="download" type="button">下载源数据</button><span id="view-status" class="status" role="status" aria-live="polite"></span></nav><noscript>当前为静态完整视图；数值和数据表可读，视图定位与下载按钮需要JavaScript。</noscript></header><main><div class="charts">'+''.join(panels)+f'</div></main><footer><p>图表、表格与标注来自同一份输入。数据文件随HTML交付；浏览器下载也可取得完整输入。</p><p class="ledger">数据SHA-256：{result["sha256"]}</p><p class="sample-label">本页检查数值合同与渲染；标题的业务判断、因果和审美仍需审阅。</p></footer><script id="chart-spec" type="application/json">{data}</script><script id="chart-ledger" type="application/json">{ledger}</script><script>{JS}</script></body></html>'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['validate','build'])
    parser.add_argument('spec',type=Path)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--layout',choices=['editorial','analytical','focus'],default='editorial')
    parser.add_argument('--theme', help='tidal / cobalt / grove / iris / nocturne / graphite / mixue-ruby; defaults to spec.theme or tidal')
    args=parser.parse_args()
    try:
        spec=json.loads(args.spec.read_text(encoding='utf-8-sig'))
        result=validate(spec)
        if args.command=='build':
            require(args.out is not None,'--out is required for build')
            content=build(spec,args.layout,args.theme)
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(content,encoding='utf-8')
            # Save the exact source contract next to the delivered artifact.
            args.out.with_suffix('.data.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
            result['output']=str(args.out.resolve())
        print(json.dumps({'ok':True,**result},ensure_ascii=False))
    except (ValueError,TypeError,KeyError,OSError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    sys.exit(main())
