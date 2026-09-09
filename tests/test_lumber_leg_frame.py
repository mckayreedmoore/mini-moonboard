"""Straight stock and new attachment geometry, not connection qualification."""
import math

import cadquery as cq
import pytest

from mini_moonboard import lumber_leg_frame as model
from mini_moonboard import wide_frame as parent
from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.connection_geometry import material_intervals


@pytest.mark.parametrize("size", model.WIDTHS)
@pytest.mark.parametrize("extension", model.EXTENSIONS)
def test_straight_grain_stock_and_full_level_floor(size, extension):
    _, foot, along, across = model.geometry(size, extension)
    right = model.leg(size, extension, "right")
    left = model.leg(size, extension, "left")
    assert right.shape.isValid() and len(right.shape.Solids()) == 1
    assert right.shape.Volume() == pytest.approx(left.shape.Volume())
    assert right.blank[0] < 2438.4  # Nominal 8 ft stock, before kerf/trim allowance.
    assert right.blank[1:] == (model.WIDTHS[size], 38.1)
    assert exact_bounds(right.shape).zmin == pytest.approx(0., abs=1e-6)
    floors = [f for f in right.shape.Faces() if abs(exact_bounds(f).zmin) < 1e-6
              and abs(exact_bounds(f).zmax) < 1e-6]
    assert len(floors) == 1
    assert floors[0].Area() == pytest.approx(38.1*model.WIDTHS[size]/along.z)
    assert floors[0].Center().y == pytest.approx(foot.y)
    assert along.dot(across) == pytest.approx(0., abs=1e-10)
    for point in model.bolt_points(size, extension):
        bore = cq.Solid.makeCylinder(11.1125/2, 38.1,
            cq.Vector(model.b.HALF, point.y, point.z), cq.Vector(1., 0., 0.))
        assert right.shape.intersect(bore).Volume() == pytest.approx(bore.Volume(), abs=.01)


def overlap(a, b):
    aa, bb = exact_bounds(a), exact_bounds(b)
    if any(getattr(aa, axis+"max") < getattr(bb, axis+"min") or
           getattr(bb, axis+"max") < getattr(aa, axis+"min") for axis in "xyz"):
        return 0.
    return a.intersect(b).Volume()


@pytest.mark.parametrize("size", model.WIDTHS)
@pytest.mark.parametrize("extension", model.EXTENSIONS)
def test_assembly_new_bores_hardware_and_unchanged_parts(size, extension):
    parts = {p.name: p for p in model.parts(size, extension)}
    raw = {p.name: p for p in model.parts(size, extension, False)}
    connections = model.connections(size, extension)
    assert len(parts) == 101 and len(connections) == 182
    assert not any(n.startswith("leg_") for n in parts)
    assert not any(c.name.startswith(("analysis_leg_wall_bolt_", "leg_stitch_")) for c in connections)
    for p in parent.parts(True):
        if not p.name.startswith(("base_side_", "leg_")):
            assert parts[p.name] is p
    bolts = [c for c in connections if c.name.startswith("lumber_leg_bolt_")]
    other_hardware = {c.name: c.components() for c in connections}
    assert len(bolts) == 8
    for c in bolts:
        for name in c.members:
            runs = material_intervals(raw[name].shape, c.start, c.direction, 0., c.length)
            assert len(runs) == 1 and runs[0][1]-runs[0][0] == pytest.approx(38.1)
            shaft = cq.Solid.makeCylinder(c.diameter/2, c.length, c.start, c.direction)
            assert overlap(shaft, parts[name].shape) < .01
        for component in c.components():
            for p in parts.values():
                assert overlap(component, p.shape) < .01, (c.name, p.name)
            for other in connections:
                if c.name == other.name:
                    continue
                for other_component in other_hardware[other.name]:
                    assert overlap(component, other_component) < .01, (c.name, other.name)
    for side in ("left", "right"):
        leg = parts[f"lumber_leg_{side}"].shape
        assert leg.distance(parts[f"base_side_{side}"].shape) == pytest.approx(0., abs=1e-6)
        for name, part in parts.items():
            if name != f"lumber_leg_{side}":
                assert overlap(leg, part.shape) < .01, name


@pytest.mark.parametrize("extension", model.EXTENSIONS)
def test_two_grain_parallel_rows_and_nominal_geometric_margins(extension):
    centre, _, along, across = model.geometry("2x6", extension)
    tangent = (model.b.point(0., 1., 0.)-model.b.point(0., 0., 0.)).normalized()
    points = model.bolt_points("2x6", extension)
    diameter = 9.525
    # NDS Table12.5.1D intermediate l/D=4 row-spacing comparison.
    row_min = (5*38.1+10*diameter)/8
    for grain, cross in ((along, across), (tangent, model.b.normal())):
        rows = sorted({round((p-centre).dot(cross), 8) for p in points})
        assert len(rows) == 2
        assert rows[1]-rows[0] >= row_min
        for row in rows:
            members = [p for p in points if abs((p-centre).dot(cross)-row) < 1e-6]
            assert len(members) == 2
            assert abs((members[1]-members[0]).dot(grain)) == pytest.approx(50.)
    assert min(139.7/2-abs((p-centre).dot(across)) for p in points) >= 4*diameter
    assert min(184.15/2-abs((p-centre).dot(model.b.normal())) for p in points) >= 4*diameter
    assert min(120.-(p-centre).dot(along) for p in points) >= 7*diameter


@pytest.mark.parametrize("size,extension", [("2x4", 0), ("2x8", -1), ("2x8", math.nan)])
def test_invalid_variants(size, extension):
    with pytest.raises(ValueError):
        model.geometry(size, extension)
