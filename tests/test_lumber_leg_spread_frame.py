"""Actual spread-group CAD checks; no connection or member qualification."""
import pytest

from mini_moonboard import lumber_leg_spread_frame as model
from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.connection_geometry import material_intervals


def overlap(a, b):
    aa, bb = exact_bounds(a), exact_bounds(b)
    if any(getattr(aa, axis+"max") < getattr(bb, axis+"min") or
           getattr(bb, axis+"max") < getattr(aa, axis+"min") for axis in "xyz"):
        return 0.
    return a.intersect(b).Volume()


@pytest.mark.parametrize("size", model.WIDTHS)
@pytest.mark.parametrize("extension", model.EXTENSIONS)
def test_extended_stock_and_nominal_geometry(size, extension):
    centre, _, along, across = model.geometry(size, extension)
    tangent = (model.original.b.point(0., 1., 0.)-model.original.b.point(0., 0., 0.)).normalized()
    normal = model.original.b.normal()
    points = model.bolt_points(size, extension)
    d = 9.525
    for grain, cross, pitch in ((along, across, 100.), (tangent, normal, 50.)):
        rows = sorted({round((p-centre).dot(cross), 8) for p in points})
        assert len(rows) == 2 and rows[1]-rows[0] >= (5*38.1+10*d)/8
        assert rows[1]-rows[0] < 127.
        for row in rows:
            members = [p for p in points if abs((p-centre).dot(cross)-row) < 1e-6]
            assert len(members) == 2
            assert abs((members[1]-members[0]).dot(grain)) == pytest.approx(pitch)
    assert min(150.-(p-centre).dot(along) for p in points) >= 7*d
    assert min(184.15/2-abs((p-centre).dot(normal)) for p in points) >= 4*d
    assert min(model.WIDTHS[size]/2-abs((p-centre).dot(across)) for p in points) >= 4*d
    for side in ("left", "right"):
        part = model.leg(size, extension, side)
        old = model.original.leg(size, extension, side)
        assert part.shape.isValid() and len(part.shape.Solids()) == 1
        assert part.blank[0] == pytest.approx(old.blank[0]+30.)
        assert part.blank[0] < 2438.4
        assert part.shape.Volume()-old.shape.Volume() == pytest.approx(30*38.1*model.WIDTHS[size])
        floors = [f for f in part.shape.Faces() if abs(exact_bounds(f).zmin) < 1e-6
                  and abs(exact_bounds(f).zmax) < 1e-6]
        assert len(floors) == 1
        assert floors[0].Area() == pytest.approx(38.1*model.WIDTHS[size]/along.z)


@pytest.mark.parametrize("size,extension", [("2x8", 300.), ("2x6", 0.)])
def test_actual_new_machining_and_complete_collisions(size, extension):
    parts = {p.name: p for p in model.parts(size, extension)}
    raw = {p.name: p for p in model.parts(size, extension, False)}
    connections = model.connections(size, extension)
    assert len(parts) == 101 and len(connections) == 182
    for part in model.original.parent.parts(True):
        if not part.name.startswith(("base_side_", "leg_")):
            assert parts[part.name] is part
    bolts = [c for c in connections if c.name.startswith("lumber_leg_bolt_")]
    assert len(bolts) == 8
    hardware = {c.name: c.components() for c in connections}
    for bolt in bolts:
        assert bolt.grip == 76.2 and bolt.length == 95.25
        for name in bolt.members:
            runs = material_intervals(raw[name].shape, bolt.start, bolt.direction, 0., bolt.length)
            assert len(runs) == 1 and runs[0][1]-runs[0][0] == pytest.approx(38.1)
        for component in hardware[bolt.name]:
            for part in parts.values():
                assert overlap(component, part.shape) < .01, (bolt.name, part.name)
            for name, others in hardware.items():
                if name != bolt.name:
                    for other in others:
                        assert overlap(component, other) < .01, (bolt.name, name)
    # Obsolete compact-pattern axes have intact timber, not retained bores.
    for bolt in model.original.connections(size, extension):
        if bolt.name.startswith("lumber_leg_bolt_"):
            for name in bolt.members:
                runs = material_intervals(parts[name].shape, bolt.start, bolt.direction, 0., bolt.length)
                assert len(runs) == 1 and runs[0][1]-runs[0][0] == pytest.approx(38.1)
    for side in ("left", "right"):
        name = f"lumber_leg_{side}"
        assert parts[name].shape.distance(parts[f"base_side_{side}"].shape) == pytest.approx(0., abs=1e-6)
        # The extra top length must clear retained hardware too, not only the
        # eight relocated bolts checked above.
        for hardware_name, components in hardware.items():
            for component in components:
                assert overlap(parts[name].shape, component) < .01, (name, hardware_name)
        for other, part in parts.items():
            if other != name:
                assert overlap(parts[name].shape, part.shape) < .01, (name, other)


def test_invalid_variant():
    with pytest.raises(ValueError):
        model.parts("2x4")
