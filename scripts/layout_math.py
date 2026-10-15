"""Conservative whole-part bounding-box packing; all dimensions are millimetres.

No CAD files are opened or modified. Use actual post-relief outline dimensions.
This heuristic proposes layouts, not a proof of the optimal sheet count.
"""
import math
import sys

EPS = 1e-7


class NoFit(ValueError):
    pass


def validate_layout(layout, sheet_width=2400, sheet_height=1200, gap=6, margin=6):
    ids = [p['id'] for p in layout]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate part ids')
    for p in layout:
        x, y, w, h = (p[k] for k in ('x', 'y', 'width', 'height'))
        if not all(math.isfinite(v) for v in (x, y, w, h)) or min(w, h) <= 0:
            raise ValueError('Invalid part dimensions or position')
        if (x < margin - EPS or y < margin - EPS or
                x + w > sheet_width - margin + EPS or
                y + h > sheet_height - margin + EPS):
            raise ValueError(f'Part outside required frame margin: {p["id"]}')
    for i, a in enumerate(layout):
        for b in layout[i + 1:]:
            separated = (a['x'] + a['width'] + gap <= b['x'] + EPS or
                         b['x'] + b['width'] + gap <= a['x'] + EPS or
                         a['y'] + a['height'] + gap <= b['y'] + EPS or
                         b['y'] + b['height'] + gap <= a['y'] + EPS)
            if not separated:
                raise ValueError(f'Insufficient bounding-box gap: {a["id"]}, {b["id"]}')
    return True


def _split_free(free, occupied):
    ox, oy, ow, oh = occupied
    split = []
    for x, y, w, h in free:
        if ox >= x + w - EPS or ox + ow <= x + EPS or oy >= y + h - EPS or oy + oh <= y + EPS:
            split.append((x, y, w, h))
            continue
        if ox > x + EPS:
            split.append((x, y, ox - x, h))
        if ox + ow < x + w - EPS:
            split.append((ox + ow, y, x + w - ox - ow, h))
        if oy > y + EPS:
            split.append((x, y, w, oy - y))
        if oy + oh < y + h - EPS:
            split.append((x, oy + oh, w, y + h - oy - oh))
    unique = list(dict.fromkeys(split))
    return [a for i, a in enumerate(unique) if not any(
        i != j and a[0] >= b[0] - EPS and a[1] >= b[1] - EPS and
        a[0] + a[2] <= b[0] + b[2] + EPS and a[1] + a[3] <= b[1] + b[3] + EPS
        for j, b in enumerate(unique))]


def pack_parts(parts, sheet_width=2400, sheet_height=1200, gap=6, margin=6,
               allow_rotate=False):
    """Pack records {id, width, height}, returning x/y from sheet lower left.

    rotation is 0 or 90 degrees. Apply that rotation to the entire CAD part,
    recompute its bounding box, then translate its minimum to returned x/y.
    A NoFit result means these heuristics failed, not that no layout exists.
    """
    params = (sheet_width, sheet_height, gap, margin)
    if not all(math.isfinite(v) for v in params) or min(sheet_width, sheet_height) <= 0 or min(gap, margin) < 0:
        raise ValueError('Invalid sheet, gap or margin')
    if sheet_width <= 2 * margin or sheet_height <= 2 * margin:
        raise ValueError('Margins consume the whole sheet')
    parts = [dict(p) for p in parts]
    if len({p['id'] for p in parts}) != len(parts):
        raise ValueError('Duplicate part ids')
    if any(not all(math.isfinite(p[k]) and p[k] > 0 for k in ('width', 'height')) for p in parts):
        raise ValueError('Invalid part dimensions')
    if not parts:
        return []
    orders = (
        lambda p: (-p['height'], -p['width'], str(p['id'])),
        lambda p: (-p['width'], -p['height'], str(p['id'])),
        lambda p: (-p['width'] * p['height'], -max(p['width'], p['height']), str(p['id'])),
        lambda p: (-max(p['width'], p['height']), -min(p['width'], p['height']), str(p['id'])),
    )
    solutions = []
    for order in orders:
        free = [(0, 0, sheet_width - 2 * margin + gap, sheet_height - 2 * margin + gap)]
        placed = []
        for p in sorted(parts, key=order):
            options = [(p['width'], p['height'], 0)]
            if allow_rotate and abs(p['width'] - p['height']) > EPS:
                options.append((p['height'], p['width'], 90))
            candidates = []
            for x, y, w, h in free:
                for pw, ph, rotation in options:
                    iw, ih = pw + gap, ph + gap
                    if iw <= w + EPS and ih <= h + EPS:
                        score = (min(w - iw, h - ih), max(w - iw, h - ih), y, x, rotation)
                        candidates.append((score, x, y, pw, ph, rotation))
            if not candidates:
                break
            _, x, y, pw, ph, rotation = min(candidates)
            placed.append({'id': p['id'], 'x': x + margin, 'y': y + margin,
                           'width': pw, 'height': ph, 'rotation': rotation})
            free = _split_free(free, (x, y, pw + gap, ph + gap))
        if len(placed) == len(parts):
            validate_layout(placed, sheet_width, sheet_height, gap, margin)
            extent_x = max(p['x'] + p['width'] for p in placed) - margin
            extent_y = max(p['y'] + p['height'] for p in placed) - margin
            solutions.append(((extent_x * extent_y, extent_y, extent_x), placed))
    if not solutions:
        raise NoFit('No layout found by four whole-part packing heuristics; do not scale parts or reduce the gap')
    return min(solutions, key=lambda pair: pair[0])[1]


def self_test():
    parts = [dict(id=i, width=w, height=h) for i, (w, h) in enumerate(
        [(100, 100), (100, 100), (50, 70), (70, 50)])]
    layout = pack_parts(parts, 300, 250)
    assert len(layout) == len(parts)
    assert validate_layout(layout, 300, 250)
    narrow = [dict(id='grain-controlled', width=70, height=100)]
    try:
        pack_parts(narrow, 112, 82)
    except NoFit:
        pass
    else:
        raise AssertionError('Rotation must not be silently allowed')
    rotated = pack_parts(narrow, 112, 82, allow_rotate=True)
    assert rotated[0]['rotation'] == 90
    assert validate_layout(rotated, 112, 82)
    invalid = [dict(id=0, x=6, y=6, width=100, height=100),
               dict(id=1, x=111, y=6, width=100, height=100)]
    try:
        validate_layout(invalid, 300, 250)
    except ValueError:
        pass
    else:
        raise AssertionError('A 5 mm gap must fail')
    print('PASS: complete packing, 6 mm gaps/margins, explicit rotation, no-fit and insufficient-gap rejection')


if __name__ == '__main__':
    if sys.argv[1:] != ['--self-test']:
        raise SystemExit('Import pack_parts/validate_layout, or run --self-test')
    self_test()
