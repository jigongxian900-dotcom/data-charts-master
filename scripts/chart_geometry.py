"""Small, composable geometry functions; authors remain free to use other tools.

Angles are radians, increasing clockwise in SVG coordinates. Missing quantities
are never converted to zero. Hierarchy leaves require explicit nonnegative values;
an internal null value means derive its complete total from its children.
"""
import math

from chart_html import num, numerically_equal, require


def _finite(*values):
    require(all(num(value) for value in values), 'geometry parameters must be finite numbers')


def linear_scale(value, domain, output=(0, 1), *, clamp=False):
    """Map a number between two endpoints. Explicit null stays null."""
    require(len(domain) == len(output) == 2, 'scales need two endpoints')
    a, b = domain
    lo, hi = output
    _finite(a, b, lo, hi)
    require(a != b, 'linear scale domain must have distinct endpoints')
    if value is None:
        return None
    _finite(value)
    t = (value-a)/(b-a)
    if clamp:
        t = min(1, max(0, t))
    result = lo + t*(hi-lo)
    _finite(result)
    return result


def band_scale(categories, output=(0, 1), *, padding=0):
    """Ordered categorical bands as {key: {start, end, center, width}}.

    padding is the fraction of each step reserved for spacing, split equally at
    either end. Reversed outputs are allowed; width is an unsigned length.
    """
    require(len(output) == 2, 'band scale needs two output endpoints')
    lo, hi = output
    _finite(lo, hi, padding)
    require(0 <= padding < 1, 'band padding must be in [0, 1)')
    require(isinstance(categories, (list, tuple)), 'categories must be ordered')
    require(all(isinstance(v, (str, int, float)) and not isinstance(v, bool) and (not isinstance(v, float) or math.isfinite(v)) for v in categories), 'band keys must be finite scalar categories')
    require(len(set(categories)) == len(categories), 'duplicate band category')
    if not categories:
        return {}
    step = (hi-lo)/len(categories)
    result = {}
    for index, key in enumerate(categories):
        start = lo + step*(index+padding/2)
        end = lo + step*(index+1-padding/2)
        _finite(start, end)
        result[key] = {'start': start, 'end': end, 'center': (start+end)/2, 'width': abs(end-start)}
    return result


def polar_point(cx, cy, radius, angle):
    _finite(cx, cy, radius, angle)
    require(radius >= 0, 'polar radius must be nonnegative')
    point = (cx + radius*math.cos(angle), cy + radius*math.sin(angle))
    _finite(*point)
    return point


def area_radius(value, max_value, outer_radius, *, inner_radius=0):
    """Area-proportional radius: (r²-inner²)/(outer²-inner²)=value/max.

    Null returns None; zero returns inner_radius; negative, overflow and an
    exceeded maximum are rejected. max_value must be positive even for zero.
    The author must use equal angular spans when comparing these areas.
    """
    _finite(max_value, outer_radius, inner_radius)
    require(max_value > 0 and 0 <= inner_radius <= outer_radius, 'invalid area scale bounds')
    if value is None:
        return None
    _finite(value)
    require(0 <= value <= max_value, 'area value must be nonnegative and within max_value')
    # Ratio formulation avoids squaring a large radius before the final result.
    if outer_radius == 0:
        return 0.0
    fraction = value/max_value
    ratio = inner_radius/outer_radius
    radius = outer_radius*math.sqrt(ratio*ratio + fraction*(1-ratio*ratio))
    _finite(radius)
    return radius


def annular_sector(cx, cy, inner_radius, outer_radius, start_angle, angle_span):
    """Return an SVG path and mathematical area for any signed span up to 2π.

    Full circles use two arcs. Zero span or equal radii have zero area. Half
    circles, rotated fans and annuli are parameters, not separate chart kinds.
    """
    _finite(cx, cy, inner_radius, outer_radius, start_angle, angle_span)
    require(0 <= inner_radius <= outer_radius, 'sector radii must satisfy 0 <= inner <= outer')
    require(abs(angle_span) <= math.tau, 'sector span cannot exceed one turn')
    sweep = 1 if angle_span >= 0 else 0
    def coordinate(point):
        return f'{point[0]:.15g},{point[1]:.15g}'
    outer_start = polar_point(cx, cy, outer_radius, start_angle)
    end_angle = start_angle+angle_span
    outer_end = polar_point(cx, cy, outer_radius, end_angle)
    path = 'M' + coordinate(outer_start)
    segments = 2 if abs(angle_span) > math.pi else 1
    for i in range(1, segments+1):
        endpoint = polar_point(cx, cy, outer_radius, start_angle+angle_span*i/segments)
        if outer_radius > 0 and angle_span != 0:
            path += f' A{outer_radius:.15g},{outer_radius:.15g} 0 0,{sweep} ' + coordinate(endpoint)
    if inner_radius:
        path += ' L' + coordinate(polar_point(cx, cy, inner_radius, end_angle))
        for i in range(1, segments+1):
            endpoint = polar_point(cx, cy, inner_radius, end_angle-angle_span*i/segments)
            if angle_span != 0:
                path += f' A{inner_radius:.15g},{inner_radius:.15g} 0 0,{1-sweep} ' + coordinate(endpoint)
    else:
        path += f' L{cx:.15g},{cy:.15g}'
    path += ' Z'
    area = abs(angle_span)/2*(outer_radius-inner_radius)*(outer_radius+inner_radius)
    _finite(area)
    return {'path': path, 'area': area, 'outer_start': outer_start, 'outer_end': outer_end,
            'start_angle': start_angle, 'angle_span': angle_span,
            'inner_radius': inner_radius, 'outer_radius': outer_radius}


def hierarchy_partition(rows, *, layout='rect', bounds=(0, 0, 1, 1),
                        start_angle=0, angle_span=math.tau, inner_radius=0, outer_radius=1):
    """Validate one complete tree, then return source-indexed rectangular/angular cells.

    Input is ordinary rows containing id, parent (root: None) and value. Internal
    value may be None to derive its sum. Explicit internal totals must reconcile;
    null leaves, negative values, missing parents, forests and cycles are errors.
    Zero subtrees retain cells with zero breadth. Every row is returned exactly
    once. Each depth gets one strip or equal-area radial ring; this is a partition
    primitive, not a treemap/sunburst styling policy or a universal layout engine.
    """
    require(layout in {'rect', 'angular'}, 'partition layout must be rect or angular')
    require(isinstance(rows, list) and rows, 'hierarchy rows must be nonempty')
    nodes, children, indices = {}, {}, {}
    for index, row in enumerate(rows):
        require(isinstance(row, dict) and isinstance(row.get('id'), str) and row['id'], 'hierarchy id required')
        key = row['id']
        require(key not in nodes, 'duplicate hierarchy id')
        require('parent' in row and (row['parent'] is None or isinstance(row['parent'], str)), 'hierarchy parent must be text or explicit null')
        require('value' in row and (row['value'] is None or (num(row['value']) and row['value'] >= 0)), 'hierarchy value must be nonnegative or explicit null')
        nodes[key], children[key], indices[key] = row, [], index
    roots = []
    for key, row in nodes.items():
        parent = row['parent']
        if parent is None:
            roots.append(key)
        else:
            require(parent in nodes, 'unknown hierarchy parent')
            children[parent].append(key)
    visiting, visited = set(), set()
    totals, depths = {}, {}
    def total(key):
        require(key not in visiting, 'hierarchy cycle detected')
        if key in visited:
            return totals[key]
        visiting.add(key)
        row, descendants = nodes[key], children[key]
        if descendants:
            value = math.fsum(total(child) for child in descendants)
            _finite(value)
            require(row['value'] is None or numerically_equal(row['value'], value), 'hierarchy parent total does not reconcile')
        else:
            require(row['value'] is not None, 'hierarchy leaf cannot be missing; declare missing separately')
            value = row['value']
        totals[key] = value
        visiting.remove(key)
        visited.add(key)
        return value
    for key in nodes:
        total(key)
    require(len(roots) == 1, 'hierarchy must have exactly one root')
    def depth(key, level):
        depths[key] = level
        for child in children[key]:
            depth(child, level+1)
    depth(roots[0], 0)
    require(len(depths) == len(nodes), 'hierarchy must cover every node')
    levels = max(depths.values())+1
    if layout == 'rect':
        require(len(bounds) == 4, 'rectangular bounds need x,y,width,height')
        x, y, width, height = bounds
        _finite(x, y, width, height)
        require(width >= 0 and height >= 0, 'rectangular dimensions must be nonnegative')
        initial_start, initial_span = x, width
    else:
        _finite(start_angle, angle_span, inner_radius, outer_radius)
        require(abs(angle_span) <= math.tau and 0 <= inner_radius <= outer_radius, 'invalid angular partition bounds')
        initial_start, initial_span = start_angle, angle_span
    cells = {}
    def partition(key, start, span):
        level = depths[key]
        cell = {'id': key, 'parent': nodes[key]['parent'], 'source_index': indices[key], 'value': totals[key], 'depth': level}
        if layout == 'rect':
            cell.update(x=start, y=y+height*level/levels, width=span, height=height/levels)
        else:
            low = area_radius(level, levels, outer_radius, inner_radius=inner_radius)
            high = area_radius(level+1, levels, outer_radius, inner_radius=inner_radius)
            cell.update(start_angle=start, angle_span=span, inner_radius=low, outer_radius=high)
        cells[key] = cell
        cursor = start
        for child in children[key]:
            child_span = span*(totals[child]/totals[key]) if totals[key] else 0
            partition(child, cursor, child_span)
            cursor += child_span
    root = roots[0]
    partition(root, initial_start, initial_span if totals[root] else 0)
    for cell in cells.values():
        _finite(*(value for key, value in cell.items() if key not in {'id', 'parent'}))
    return [cells[row['id']] for row in rows]
