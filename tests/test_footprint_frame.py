"""Physical footprint variants, not structural approval."""
import math
from types import SimpleNamespace

import cadquery as cq
import pytest
import test_hybrid_frame as gates

from mini_moonboard import box_frame as b
from mini_moonboard import footprint_frame as frame
from mini_moonboard import hybrid
from mini_moonboard import hybrid_frame as h
from mini_moonboard import shallow_frame as shallow
from mini_moonboard.box_exports import overlap


@pytest.mark.parametrize('extension', [-1, 201, math.nan, math.inf, -math.inf])
def test_invalid_extensions(extension):
    with pytest.raises(ValueError):
        frame.parts(extension)


@pytest.mark.parametrize('drilled', [True, False])
def test_zero_is_unchanged_reference(drilled):
    assert frame.parts(0, drilled) is shallow.parts(drilled)
    assert frame.connections() is shallow.connections()


@pytest.mark.parametrize('extension', frame.EXTENSIONS_MM[1:])
def test_actual_leg_profiles_and_unchanged_assembly(extension):
    baseline = {p.name: p for p in shallow.parts(False)}
    actual = {p.name: p for p in frame.parts(extension, False)}
    assert actual.keys() == baseline.keys()
    assert frame.foot_center(extension).y - frame.foot_center(0).y == pytest.approx(extension)
    assert frame.lower_angle(extension) < frame.lower_angle(0)
    for name, p in actual.items():
        if not name.startswith('leg_'):
            assert p is baseline[name]
            continue
        assert p.shape.isValid() and len(p.shape.Solids()) == 1
        assert p.laminations == 2 and p.blank[2] == pytest.approx(38.1)
        bounds = p.shape.BoundingBox()
        assert p.blank[:2] == pytest.approx((bounds.zlen, bounds.ylen))
        assert bounds.zmin == pytest.approx(0, abs=1e-5)
        assert p.shape.Volume() > baseline[name].shape.Volume()
        floors = [f for f in p.shape.Faces() if abs(f.BoundingBox().zmin) < 1e-5
                  and abs(f.BoundingBox().zmax) < 1e-5]
        assert len(floors) == 1
        assert floors[0].Area() == pytest.approx(38.1 * 180 / math.sin(math.radians(frame.lower_angle(extension))))
        assert floors[0].Center().y == pytest.approx(frame.foot_center(extension).y)
        # The upper attachment region is identical, not merely at similar bounds.
        clip = cq.Workplane('XY').box(10000, 10000, 10000, centered=(True, True, False)).translate(
            (0, 0, b.point(0, 1540, hybrid.leg_normal('2x8')).z - 15)).val()
        a, old = p.shape.intersect(clip), baseline[name].shape.intersect(clip)
        assert a.cut(old).Volume() < .01 and old.cut(a).Volume() < .01
        assert not [(other.name, overlap(p.shape, other.shape)) for other in actual.values()
                    if other.name != name and overlap(p.shape, other.shape) > .01]


@pytest.mark.parametrize('gate', [
    gates.test_solids_and_collisions,
    gates.test_connections_have_receivers_and_connected_graph,
    gates.test_tool_led_and_routing_envelopes,
    gates.test_floor_and_rib_orientation,
    gates.test_rib_crossed_bores_retain_recorded_ligament,
])
@pytest.mark.parametrize('extension', [100, 150])
def test_selected_full_geometry_gates(monkeypatch, gate, extension):
    monkeypatch.setattr(gates, 'h', SimpleNamespace(
        parts=lambda size: frame.parts(extension), connections=lambda size: frame.connections(),
        panel_attachments=h.panel_attachments))
    gate('2x8')


def test_selected_100_mm_shafts_clear_non_receiving_members():
    parts = frame.parts(100)
    collisions = []
    for connection in frame.connections():
        shaft = connection.components()[0]
        for part in parts:
            if part.name not in connection.members and overlap(shaft, part.shape) > .01:
                collisions.append((connection.name, part.name))
    assert not collisions, collisions
