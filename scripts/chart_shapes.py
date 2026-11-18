"""Alternate mark shapes on the same positions, order, units and scales."""

from math import sqrt
from xml.etree import ElementTree as ET

from chart_html import require


STYLES = {
    'bar': [('solid', '实心柱', '用柱长直接比较大小，适合密集汇报。'),
            ('pin', '端点杆', '细杆保留零线，圆点落在真实读数处。'),
            ('notched', '刻痕柱', '等距浅刻痕压低视觉重量，柱长仍按原值。')],
    'line': [('solid', '折线', '突出相邻观测的变化方向。'),
             ('observations', '观测点', '直接读观测位置，缺报期间自然留空。'),
             ('ticks', '刻点折线', '用短刻线区分每次采集，保留已知观测之间的连接。')],
    'scatter': [('solid', '圆点', '用紧凑标记看总体分布。'),
                ('rings', '透底圆环', '浅层叠高时保留遮挡线索。'),
                ('diamonds', '菱形点', '用不同轮廓区分呈现风格，位置不变。')],
    'waterfall': [('solid', '实块瀑布', '增减用浮动块表示。'),
                  ('frame', '线框瀑布', '用轮廓保留两端范围，适合灰度打印。'),
                  ('notched', '刻痕桥', '保持连桥的起止增减，浅刻痕区分主体。')],
    'stacked': [('solid', '色块拼合', '整条显示总量，各色段显示构成。'),
                ('frame', '线框分段', '强调相邻分段的真实边界。'),
                ('notched', '刻痕分段', '保留组内构成和分段起止，适合编辑式图注。')],
    'box': [('solid', '箱体', '以矩形呈现中间一半的原始观测。'),
            ('rail', '四分位粗轨', '用粗轨显示四分位间距，中央横线仍为中位数。'),
            ('brackets', '四分位括号', '两端短线标记四分位，保留须线和原始观测。')],
}


def attrs(element, keys):
    return [float(element.get(key)) for key in keys.split()]


def mark(element, tag, **geometry):
    return ET.SubElement(element, tag, {name.replace('_', '-'): str(value) for name, value in geometry.items()})


def bar_group(rect, style):
    x, y, w, h, start, end = attrs(rect, 'x y width height data-start data-end')
    horizontal = rect.get('data-axis') == 'x'
    ink = rect.get('fill')
    if style == 'frame':
        rect.set('stroke', ink)
        rect.set('stroke-width', '1.5')
        rect.set('fill-opacity', '.13')
        return
    if not w or not h:
        return
    rect.tag = 'g'
    for key in ('x', 'y', 'width', 'height', 'fill'):
        del rect.attrib[key]
    rect.set('data-shape', style)
    if style == 'pin':
        if horizontal:
            a, b = (x, x+w) if end >= start else (x+w, x)
            xx, yy = b, y+h/2
            mark(rect, 'line', x1=a, x2=b, y1=yy, y2=yy, stroke=ink, stroke_width=2.8)
        else:
            a, b = (y+h, y) if end >= start else (y, y+h)
            xx, yy = x+w/2, b
            mark(rect, 'line', x1=xx, x2=xx, y1=a, y2=b, stroke=ink, stroke_width=2.8)
        mark(rect, 'circle', cx=xx, cy=yy, r=4.2, fill=ink)
    else:
        mark(rect, 'rect', x=x, y=y, width=w, height=h, fill=ink)
        length, thickness = (w,h) if horizontal else (h,w)
        fixed = min(5, thickness * .23)
        # These are equal visual graduations. The presence of a notch encodes no extra observation.
        for offset in range(13, int(length)-3, 13):
            if horizontal:
                mark(rect, 'path', d=f'M{x+offset-1},{y} L{x+offset},{y+fixed} L{x+offset+1},{y} Z', fill='var(--paper)')
            else:
                mark(rect, 'path', d=f'M{x+w},{y+offset-1} L{x+w-fixed},{y+offset} L{x+w},{y+offset+1} Z', fill='var(--paper)')


def point_groups(root, style):
    for point in root.iter('circle'):
        if point.get('role') != 'img' or point.find('title') is None:
            continue
        x,y,r = attrs(point,'cx cy r')
        ink = point.get('fill')
        if style == 'rings':
            point.set('fill', 'none')
            point.set('stroke', ink)
            point.set('stroke-width', '1.8')
        if style == 'diamonds':
            point.tag = 'path'
            for key in ('cx','cy','r'):
                del point.attrib[key]
            edge = r * sqrt(3.14159265359/2)
            point.set('d', f'M{x},{y-edge} L{x+edge},{y} L{x},{y+edge} L{x-edge},{y} Z')
        if style == 'ticks' and r != 5 and ink != 'var(--paper)':
            point.tag = 'line'
            for key in ('cx','cy','r'):
                del point.attrib[key]
            point.attrib.update(x1=str(x), x2=str(x), y1=str(y-r-2), y2=str(y+r+2))
            point.set('stroke', point.get('stroke') if ink == 'var(--paper)' else ink)
            point.set('stroke-width','2')


def quartile_mark(rect, style):
    x,y,w,h = attrs(rect,'x y width height')
    axis = rect.get('data-box-direction')
    ink = rect.get('stroke')
    rect.tag = 'g'
    rect.attrib.clear()
    if axis == 'x':
        a,b,cross = x,x+w,y+h/2
        mark(rect,'line',x1=a,x2=b,y1=cross,y2=cross,stroke=ink,stroke_width=6 if style=='rail' else 2)
        if style=='brackets':
            for p in (a,b):
                mark(rect,'line',x1=p,x2=p,y1=y+4,y2=y+h-4,stroke=ink,stroke_width=2)
    else:
        a,b,cross = y,y+h,x+w/2
        mark(rect,'line',x1=cross,x2=cross,y1=a,y2=b,stroke=ink,stroke_width=6 if style=='rail' else 2)
        if style=='brackets':
            for p in (a,b):
                mark(rect,'line',x1=x+4,x2=x+w-4,y1=p,y2=p,stroke=ink,stroke_width=2)


def apply_shape(svg, kind, style):
    if style == 'solid':
        return svg
    require(any(s == style for s, _, _ in STYLES.get(kind, [])), f'{style} is not a supported {kind} shape')
    root = ET.fromstring(svg)
    if kind in {'bar', 'stacked', 'waterfall'}:
        for element in list(root.iter('rect')):
            if element.get('data-axis'):
                bar_group(element, style)
    elif kind == 'box':
        for element in list(root.iter('rect')):
            if element.get('data-box-direction'):
                quartile_mark(element, style)
    elif kind == 'scatter' or style == 'ticks':
        point_groups(root, style)
    elif style == 'observations':
        for segment in list(root.findall('polyline')):
            root.remove(segment)
    return ET.tostring(root, encoding='unicode')
