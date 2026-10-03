"""Independent rectangle/diagonal-slot planar moment oracle."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import cadquery as cq


def clip(points, normal, threshold, keep_greater):
    result = []
    for a, b in zip(points, points[1:] + points[:1]):
        da = sum(x * y for x, y in zip(a, normal)) - threshold
        db = sum(x * y for x, y in zip(b, normal)) - threshold
        ina = da >= 0 if keep_greater else da <= 0
        inb = db >= 0 if keep_greater else db <= 0
        if ina:
            result.append(a)
        if ina != inb:
            fraction = da / (da - db)
            result.append(tuple(a[i] + fraction * (b[i] - a[i]) for i in range(2)))
    return result


def moments(points):
    area = sx = sy = xx = xy = yy = 0.0
    for (x, y), (a, b) in zip(points, points[1:] + points[:1]):
        k = x * b - a * y
        area += k / 2
        sx += (x + a) * k / 6
        sy += (y + b) * k / 6
        xx += (x * x + x * a + a * a) * k / 12
        yy += (y * y + y * b + b * b) * k / 12
        xy += (2 * x * y + x * b + a * y + 2 * a * b) * k / 24
    return area, sx, sy, xx, xy, yy


def combined(polygons):
    terms = [moments(p) for p in polygons]
    a, sx, sy, xx, xy, yy = [math.fsum(t[i] for t in terms) for i in range(6)]
    cu, cv = sx / a, sy / a
    return (
        a,
        (cu, cv),
        {"uu": xx - a * cu * cu, "uv": xy - a * cu * cv, "vv": yy - a * cv * cv},
    )


def rotation(v):
    axis = (1 / math.sqrt(14), 2 / math.sqrt(14), 3 / math.sqrt(14))
    c, s = math.cos(math.radians(37)), math.sin(math.radians(37))
    dot = sum(x * y for x, y in zip(axis, v))
    cross = (
        axis[1] * v[2] - axis[2] * v[1],
        axis[2] * v[0] - axis[0] * v[2],
        axis[0] * v[1] - axis[1] * v[0],
    )
    return tuple(c * v[i] + s * cross[i] + (1 - c) * dot * axis[i] for i in range(3))


def test_diagonal_slot_matches_independent_polygon_moments_under_rotation():
    path = Path(__file__).with_name("section_geometry.py")
    spec = importlib.util.spec_from_file_location("parent_section_kernel", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    area, centroid, covariance = combined(
        [[(-20, -30), (20, -30), (20, 30), (-20, 30)]]
    )
    assert math.isclose(area, 2400.0)
    assert centroid == (0.0, 0.0)
    assert covariance == {"uu": 320000.0, "uv": 0.0, "vv": 720000.0}
    root = math.sqrt(0.5)
    rectangle = [(-20, -30), (20, -30), (20, 30), (-20, 30)]
    normal = (root, -root)
    center = (3, -5)
    threshold = sum(x * y for x, y in zip(normal, center))
    polygons = [
        clip(rectangle, normal, threshold + 5, True),
        clip(rectangle, normal, threshold - 5, False),
    ]
    expected_area, expected_centroid, expected_cov = combined(polygons)
    blank = cq.Solid.makeBox(100, 40, 60, (0, -20, -30))
    axis = (0, root, root)
    begin = tuple((50, 3, -5)[i] - 100 * axis[i] for i in range(3))
    bore = cq.Solid.makeCylinder(5, 200, begin, axis)
    shape = blank.cut(bore)
    translation = (120, -80, 200)
    variants = [
        (shape, (50, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
        (
            shape.rotate((0, 0, 0), (1, 2, 3), 37).translate(translation),
            tuple(rotation((50, 0, 0))[i] + translation[i] for i in range(3)),
            rotation((1, 0, 0)),
            rotation((0, 1, 0)),
            rotation((0, 0, 1)),
        ),
    ]
    for solid, origin, g, u, v in variants:
        actual = mod.section_properties(solid, origin, g, u, v)
        assert actual["component_count"] == 2
        assert actual["disconnected_ligaments"] is True
        assert math.isclose(
            actual["area_mm2"], expected_area, rel_tol=1e-9, abs_tol=1e-6
        ), (actual, expected_area)
        for a, b in zip(actual["centroid_relative_uv_mm"], expected_centroid):
            assert math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-7), (a, b)
        for key in ("uu", "uv", "vv"):
            assert math.isclose(
                actual["area_covariance_integrals_mm4"][key],
                expected_cov[key],
                rel_tol=1e-8,
                abs_tol=1e-5,
            ), (key, actual, expected_cov)
