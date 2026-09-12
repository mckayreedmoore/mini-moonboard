"""Check the continuous-envelope construction, not just a saved LP result."""
import itertools
import math

import numpy as np

from fea.reinforced_floor_envelope import (
    boundary_locations,
    enclosing_horizontal_vertices,
    wrench,
)


def test_horizontal_polygon_encloses_full_disk():
    vertices = np.asarray(enclosing_horizontal_vertices())
    for a, b in zip(vertices, np.roll(vertices, -1, axis=0), strict=True):
        distance = abs((b[0]-a[0])*(-a[1])-(b[1]-a[1])*(-a[0]))/np.linalg.norm(b-a)
        assert abs(distance-300.) < 1e-10
    assert np.linalg.norm(vertices[0]) > 300.


def test_product_vertex_interpolation_preserves_cross_terms():
    # Nonzero/unequal axes deliberately retain p x H and e*n x H terms.
    p = [np.array([-30., 20., 50.]), np.array([150., 100., 190.])]
    h = [np.array([-120., 80.]), np.array([210., -200.])]
    intervals = [p, [0., 100.], [1100., 2700.], h, [140., 180.]]
    t = [.31, .67, .29, .43, .81]
    n = np.array([0., .8, -.6])
    centre = np.array([2., 560., 930.])
    average = np.zeros(6)
    for bits in itertools.product((0, 1), repeat=5):
        values = [intervals[i][bit] for i, bit in enumerate(bits)]
        weight = math.prod(t[i] if bit else 1-t[i] for i, bit in enumerate(bits))
        average += weight*np.array(wrench(values[0], n, values[1], values[2],
                                         values[3], values[4], centre))
    mid = [(1-t[i])*np.asarray(v[0])+t[i]*np.asarray(v[1])
           for i, v in enumerate(intervals)]
    assert np.allclose(average, wrench(mid[0], n, mid[1], mid[2], mid[3], mid[4], centre),
                       rtol=1e-12, atol=1e-8)


def test_all_current_holds_inside_coplanar_boundary():
    from fea.round_structural_global_envelope import locations
    from mini_moonboard import round_reinforcement_frame as model

    points = locations(model)
    boundary = boundary_locations(points)
    assert len(points) == 142
    assert len(boundary) == 6
    for kicker in (False, True):
        group = [p for p in points if p[0].startswith('kicker_') == kicker]
        corners = [p for p in boundary if p[0].startswith('kicker_') == kicker]
        normal = np.asarray(corners[0][2])
        origin = np.asarray(corners[0][1])
        lo = np.min([p[1] for p in corners], axis=0)
        hi = np.max([p[1] for p in corners], axis=0)
        for _, point, outward in group:
            assert np.allclose(normal, outward)
            assert abs(np.dot(np.asarray(point)-origin, normal)) < 1e-8
            assert np.all(np.asarray(point) >= lo-1e-8)
            assert np.all(np.asarray(point) <= hi+1e-8)
