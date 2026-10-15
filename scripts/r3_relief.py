"""FreeCAD helper: one radius-r semicircle through each material concave corner.

Use inside FreeCAD or with its bundled Python. This accepts linear XY polygons,
not existing arcs. It returns a wire and corner records, without changing a file.
"""
import math
import sys

import FreeCAD as App
import Part

EPS = 1e-7


def make_relief_wire(points, radius=3.0, material_inside=True):
    """Return {wire, reliefs, skipped} for an outer polygon or hole polygon.

    points: FreeCAD vectors, with optional duplicated closing point.
    material_inside: True for a board outline, False for a hole/slot outline.
    Each relief record contains corner, center, radius and the single arc edge.
    Non-right-angle concave corners are reported as skipped.
    """
    if radius <= 0:
        raise ValueError('Radius must be positive')
    vertices = [App.Vector(p) for p in points]
    if len(vertices) > 1 and vertices[0].distanceToPoint(vertices[-1]) < EPS:
        vertices.pop()
    if len(vertices) < 3:
        raise ValueError('A closed polygon needs at least three vertices')
    if max(p.z for p in vertices) - min(p.z for p in vertices) > EPS:
        raise ValueError('Expected a planar XY polygon')
    area = sum(a.x * b.y - b.x * a.y
               for a, b in zip(vertices, vertices[1:] + vertices[:1])) / 2
    if abs(area) < EPS:
        raise ValueError('Degenerate polygon')
    if (area > 0) != material_inside:
        vertices.reverse()
    n = len(vertices)
    selected, skipped = {}, []
    trim = radius * math.sqrt(2)
    for i, c in enumerate(vertices):
        incoming = c - vertices[i - 1]
        outgoing = vertices[(i + 1) % n] - c
        if min(incoming.Length, outgoing.Length) < EPS:
            raise ValueError('Zero-length original segment')
        incoming.normalize()
        outgoing.normalize()
        cross = incoming.cross(outgoing).z
        if cross >= -EPS:
            continue
        if abs(incoming.dot(outgoing)) > EPS:
            skipped.append({'corner': c, 'reason': 'Concave angle is not 90 degrees'})
            continue
        u, v = -incoming, outgoing
        a, b = c + u * trim, c + v * trim
        center = c + (u + v) * (radius / math.sqrt(2))
        arc = Part.Arc(a, c, b).toShape()
        assert abs(arc.Curve.Radius - radius) < EPS
        assert abs(arc.Length - math.pi * radius) < EPS
        assert arc.Curve.Center.distanceToPoint(center) < EPS
        assert arc.distToShape(Part.Vertex(c))[0] < EPS
        selected[i] = {'corner': c, 'center': center, 'radius': radius,
                       'arc': arc, 'start': a, 'end': b}
    edges = []
    for i, start in enumerate(vertices):
        j = (i + 1) % n
        length = start.distanceToPoint(vertices[j])
        required = trim * ((i in selected) + (j in selected))
        if length <= required + EPS:
            raise ValueError(f'Segment {i} is too short: {length:g} mm, trim {required:g} mm')
        a = selected[i]['end'] if i in selected else start
        b = selected[j]['start'] if j in selected else vertices[j]
        edges.append(Part.makeLine(a, b))
        if j in selected:
            edges.append(selected[j]['arc'])
    wire = Part.Wire(edges)
    if not wire.isClosed() or not wire.isValid() or not Part.Face(wire).isValid():
        raise ValueError('Relief produced an invalid or intersecting profile')
    return {'wire': wire, 'reliefs': list(selected.values()), 'skipped': skipped}


def self_test():
    def vectors(points):
        return [App.Vector(x, y, 0) for x, y in points]

    board = vectors([(0, 0), (60, 0), (60, 20), (20, 20), (20, 60), (0, 60)])
    for polygon in (board, list(reversed(board))):
        result = make_relief_wire(polygon)
        assert len(result['reliefs']) == 1 and not result['skipped']
        record = result['reliefs'][0]
        assert record['corner'].distanceToPoint(App.Vector(20, 20, 0)) < EPS
        assert record['center'].distanceToPoint(App.Vector(20 + 3 / math.sqrt(2),
                                                        20 + 3 / math.sqrt(2), 0)) < EPS
        assert len(result['wire'].Edges) == 7
    slot = vectors([(0, 0), (80, 0), (80, 18), (0, 18)])
    result = make_relief_wire(slot, material_inside=False)
    assert len(result['reliefs']) == 4 and len(result['wire'].Edges) == 8
    assert sum(isinstance(e.Curve, Part.Circle) for e in result['wire'].Edges) == 4
    assert len(make_relief_wire(slot, material_inside=True)['reliefs']) == 0
    try:
        make_relief_wire(vectors([(0, 0), (8, 0), (8, 8), (0, 8)]), material_inside=False)
    except ValueError as error:
        assert 'too short' in str(error)
    else:
        raise AssertionError('A narrow slot must not produce overlapping reliefs')
    print('PASS: single R3 arcs, material-side classification, reversed input, closed wires, short-edge rejection')


if __name__ == '__main__':
    if sys.argv[1:] != ['--self-test']:
        raise SystemExit('Import make_relief_wire in FreeCAD, or run --self-test')
    self_test()
