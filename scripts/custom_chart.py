"""Author-side extension protocol, not a chart-type catalogue or JSON DSL.

Business geometry is the author's responsibility. The wrapper checks provenance,
row coverage and inert SVG; it does not prove that a mark encodes a value correctly.
"""
from copy import deepcopy
from dataclasses import dataclass
import math
import re
import xml.etree.ElementTree as ET

from chart_html import KINDS, canonical, digest, require, validate


@dataclass(frozen=True)
class CustomRenderer:
    label: str
    validate: object  # validate(chart) -> None; raise ValueError for invalid business data
    render: object  # render(chart, variant, theme_css) -> RenderedChart


@dataclass
class RenderedChart:
    svg: str
    ledger: list  # one {row_index, source: original_row, ...} per rendered source row
    coverage: list  # every row: {row_index, status: rendered|missing|excluded, reason?}
    table_fields: list  # all original row keys, in the author's preferred order
    export_svg: str  # explicit, complete static counterpart of this variant


def registry_for(renderers):
    require(renderers is None or isinstance(renderers, dict), 'renderers must be a dictionary')
    for key, renderer in (renderers or {}).items():
        require(isinstance(key, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', key), 'renderer key must be a safe identifier')
        require(key not in KINDS, 'custom renderer cannot override a built-in kind')
        require(isinstance(renderer, CustomRenderer), 'renderer must be CustomRenderer')
        require(isinstance(renderer.label, str) and renderer.label.strip(), 'renderer label required')
        require(callable(renderer.validate) and callable(renderer.render), 'renderer needs validate and render callbacks')
    return renderers or {}


def call_readonly(callback, chart, *args):
    supplied = deepcopy(chart)
    before = canonical(supplied)
    result = callback(supplied, *args)
    require(canonical(supplied) == before, 'custom callback mutated its chart input')
    return result


def validate_spec(spec, renderers=None):
    registry = registry_for(renderers)
    if not registry:
        return validate(spec)
    require(isinstance(spec, dict), 'spec must be an object')
    require(isinstance(spec.get('title'), str) and spec['title'].strip(), 'title is required')
    require(isinstance(spec.get('charts'), list) and spec['charts'], 'charts must be a nonempty list')
    seen = set()
    for chart in spec['charts']:
        require(isinstance(chart, dict), 'each chart must be an object')
        for field in ['id', 'title', 'question', 'unit', 'period', 'scope', 'source']:
            require(isinstance(chart.get(field), str) and chart[field].strip(), f'{field} is required')
        require(chart['id'] not in seen, f'duplicate chart id: {chart["id"]}')
        seen.add(chart['id'])
        kind = chart.get('kind')
        require(isinstance(kind, str), 'chart kind must be text')
        if kind in KINDS:
            validate({'title': spec['title'], 'charts': [chart]})
            continue
        require(kind in registry, f'unregistered custom chart kind: {kind}')
        require(isinstance(chart.get('rows'), list) and all(isinstance(r, dict) for r in chart['rows']), 'custom rows must be a list of objects')
        require(not chart.get('claims'), 'custom claims must be checked and presented by the author renderer; built-in claims are unsupported')
        canonical(chart)
        call_readonly(registry[kind].validate, chart)
    return {'charts': len(spec['charts']), 'rows': sum(len(c['rows']) for c in spec['charts']), 'sha256': digest(spec)}


_ELEMENTS = {'svg', 'g', 'defs', 'clipPath', 'mask', 'linearGradient', 'radialGradient', 'stop', 'pattern', 'marker', 'symbol', 'use', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'text', 'tspan', 'textPath', 'title', 'desc'}
_ATTRS = set(('id class viewBox width height x y x1 y1 x2 y2 cx cy r rx ry d points transform fill fill-opacity fill-rule stroke stroke-width stroke-opacity stroke-linecap stroke-linejoin stroke-dasharray stroke-dashoffset opacity clip-path clip-rule mask marker-start marker-mid marker-end offset stop-color stop-opacity gradientUnits gradientTransform patternUnits patternContentUnits patternTransform markerWidth markerHeight refX refY orient preserveAspectRatio text-anchor dominant-baseline font-size font-family font-weight font-style letter-spacing dx dy rotate textLength lengthAdjust role aria-label aria-hidden href').split())
_NUMBER = r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'
_GEOMETRY = set('viewBox width height x y x1 y1 x2 y2 cx cy r rx ry d points transform stroke-width stroke-dasharray stroke-dashoffset dx dy rotate textLength font-size letter-spacing gradientTransform patternTransform markerWidth markerHeight refX refY'.split())


def checked_svg(raw, prefix, variant):
    """Parse inert SVG, reject external/active content, isolate local defs references."""
    require(isinstance(raw, str) and '<!DOCTYPE' not in raw.upper() and '<!ENTITY' not in raw.upper() and '<?' not in raw, 'SVG must be plain XML without declarations or entities')
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f'invalid custom SVG: {exc}') from exc
    namespace = 'http://www.w3.org/2000/svg'
    def local(tag):
        require(isinstance(tag, str) and (not tag.startswith('{') or tag.startswith('{' + namespace + '}')), 'unsupported SVG namespace')
        return tag.rsplit('}', 1)[-1]
    require(local(root.tag) == 'svg', 'custom SVG root required')
    viewbox = root.get('viewBox', '').split()
    require(len(viewbox) == 4, 'SVG requires a four-number viewBox')
    try:
        box = [float(v) for v in viewbox]
    except ValueError as exc:
        raise ValueError('invalid SVG viewBox') from exc
    require(all(math.isfinite(v) for v in box) and box[2] > 0 and box[3] > 0, 'SVG viewBox must be finite and positive')
    ids, refs = {}, []
    for element in root.iter():
        require(local(element.tag) in _ELEMENTS, f'unsafe or unsupported SVG element: {local(element.tag)}')
        for attr, value in element.attrib.items():
            key = attr
            if attr == '{http://www.w3.org/1999/xlink}href':
                key = 'href'
            require(key in _ATTRS, f'unsafe or unsupported SVG attribute: {attr}')
            require(not re.search(r'(?:https?:|data:|javascript:|file:|//|[<>])', value, re.I), 'external or active SVG attribute')
            if key == 'id':
                require(re.fullmatch(r'[A-Za-z_][\w.-]*', value) and value not in ids, 'invalid or duplicate SVG id')
                ids[value] = prefix + value
            if key == 'href':
                require(value.startswith('#') and len(value) > 1, 'SVG href must be a local fragment')
                refs.append(value[1:])
            if 'url(' in value.lower():
                matches = re.findall(r'url\(#([A-Za-z_][\w.-]*)\)', value)
                require(matches and re.sub(r'url\(#[A-Za-z_][\w.-]*\)', '', value).strip() == '', 'SVG paint reference must be local')
                refs.extend(matches)
            if key in _GEOMETRY:
                require(not re.search(r'(?i)(?:nan|inf(?:inity)?)', value), 'SVG geometry must be finite')
                require(all(math.isfinite(float(n)) for n in re.findall(_NUMBER, value)), 'SVG geometry must be finite')
    require(all(ref in ids for ref in refs), 'SVG references unknown local id')
    for element in root.iter():
        for attr, value in list(element.attrib.items()):
            if attr == 'id':
                element.set(attr, ids[value])
            elif attr.endswith('href') and value.startswith('#'):
                element.set(attr, '#' + ids[value[1:]])
            elif 'url(' in value:
                element.set(attr, re.sub(r'url\(#([A-Za-z_][\w.-]*)\)', lambda m: 'url(#' + ids[m[1]] + ')', value))
        element.tag = '{' + namespace + '}' + local(element.tag)
    root.set('class', variant + '-svg')
    ET.register_namespace('', namespace)
    return ET.tostring(root, encoding='unicode')


def render_variant(chart, renderer, variant, theme):
    result = call_readonly(renderer.render, chart, variant, theme)
    require(isinstance(result, RenderedChart), 'custom render must return RenderedChart')
    rows = chart['rows']
    fields = set(k for row in rows for k in row)
    require(isinstance(result.table_fields, list) and all(isinstance(k, str) for k in result.table_fields), 'table_fields must be a list of field names')
    require(len(result.table_fields) == len(set(result.table_fields)) and set(result.table_fields) == fields, 'table_fields must preserve every original field exactly once')
    require(isinstance(result.coverage, list) and len(result.coverage) == len(rows), 'coverage must account for every source row')
    coverage = {}
    for item in result.coverage:
        require(isinstance(item, dict), 'coverage entry must be an object')
        index = item.get('row_index')
        require(type(index) is int and 0 <= index < len(rows) and index not in coverage, 'invalid or duplicate coverage row_index')
        require(item.get('status') in {'rendered', 'missing', 'excluded'}, 'invalid coverage status')
        if item['status'] != 'rendered':
            require(isinstance(item.get('reason'), str) and item['reason'].strip(), 'missing/excluded coverage needs a reason')
        coverage[index] = item
    require(isinstance(result.ledger, list), 'ledger must be a list')
    bound = set()
    for entry in result.ledger:
        require(isinstance(entry, dict), 'ledger entry must be an object')
        index = entry.get('row_index')
        require(type(index) is int and index in coverage and index not in bound, 'invalid or duplicate ledger row_index')
        require(coverage[index]['status'] == 'rendered', 'ledger may bind only rendered rows')
        require('source' in entry and canonical(entry['source']) == canonical(rows[index]), 'ledger source must equal the full original row')
        bound.add(index)
    require(bound == {i for i, item in coverage.items() if item['status'] == 'rendered'}, 'rendered coverage and source ledger disagree')
    canonical(result.ledger)
    canonical(result.coverage)
    prefix = 'c' + digest(chart['id'])[:16] + '-' + variant + '-'
    result.svg = checked_svg(result.svg, prefix, variant)
    result.export_svg = checked_svg(result.export_svg, prefix + 'export-', variant)
    return result
