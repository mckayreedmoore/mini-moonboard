"""Actual geometric inspection, not catalog compatibility or strength gates."""
import math
from itertools import combinations
from types import SimpleNamespace

import cadquery as cq
import pytest
import test_hybrid_frame as gates

from mini_moonboard import box_frame as b
from mini_moonboard import clip_frame as frame
from mini_moonboard import hybrid_frame as h
from mini_moonboard import spacing_frame as baseline
from mini_moonboard.box_exports import overlap
from mini_moonboard.panel_grid import main_led_datums, main_tnut_datums


def test_exact_inventory_translation_and_fixed_panel_axes():
    old = {c.name: c for c in baseline.connections()}
    new = {c.name: c for c in frame.connections()}
    assert len(old) == 226 and len(new) == len(frame.connections()) == 250
    assert set(old)-set(new) == {f"mid_end_{band}_{side}_{end}" for band in ("lower", "upper")
                                for side in ("left", "right") for end in ("bottom", "top")}
    assert len(set(new)-set(old)) == 32
    translated = {name for name in old if name.startswith(("rib_", "angle_rib_")) and "_mid_" in name}
    assert len(translated) == 30
    for name in set(old) & set(new):
        if name in translated:
            assert (new[name].start-old[name].start).toTuple() == pytest.approx((5, 0, 0))
            assert new[name].members == old[name].members
        else:
            assert new[name] is old[name]
    original = {p.name: p for p in baseline.parts(False)}
    candidate = {p.name: p for p in frame.parts(False)}
    assert len(candidate) == len(original)+8
    moved = {n for n in original if n.startswith("mid_") or (n.startswith(("rib_", "angle_rib_")) and "_mid_" in n)}
    assert len(moved) == 16
    for name, part in original.items():
        if name in moved:
            assert candidate[name].shape.Volume() == pytest.approx(part.shape.Volume(), abs=1e-5)
            assert (candidate[name].shape.Center()-part.shape.Center()).toTuple() == pytest.approx((5, 0, 0))
        else:
            assert candidate[name] is part


def test_all_eight_official_model_outlines_holes_and_relief_allowance():
    raw = {p.name: p for p in frame.parts(False)}
    stations = list(frame.stations())
    assert len(stations) == 8
    assert sorted({s for _, _, s, _, _, _ in stations}) == [88.9, 1149.35, 1289.05, 2349.5]
    assert sorted({x for _, x, *_ in stations}) == pytest.approx([-558.65, 641.35])
    expected_volume = ((34.925*(51.9684+39.2684)-2*6.35**2)*1.1684
                       -34.925*1.1684**2-4*math.pi*2.1717**2*1.1684)
    reliefs = [(u-b.HALF, s, cq.Solid.makeCylinder(20, 40.1, b.point(u-b.HALF, s, -1), b.normal()))
               for u, s in (*main_tnut_datums().values(), *main_led_datums().values()) if s >= 0]
    for name, x, s, direction, _, _ in stations:
        shape = raw[name].shape
        assert shape.isValid() and len(shape.Solids()) == 1
        assert shape.Volume() == pytest.approx(expected_volume, abs=1e-5)
        assert shape.BoundingBox().xmin == pytest.approx(x-39.2684, abs=1e-5)
        cylinders = [face for face in shape.Faces() if face.geomType() == "CYLINDER"]
        assert len(cylinders) == 4
        for u, v, w, axis in ((-7.9375, -42.4434, -1, cq.Vector(-1, 0, 0)),
                               (7.9375, -29.7434, -1, cq.Vector(-1, 0, 0)),
                               (-7.9375, 1, 17.0434, frame.TANGENT*direction),
                               (7.9375, 1, 29.7434, frame.TANGENT*direction)):
            core = cq.Solid.makeCylinder(2.1716, 3.1684, frame.placed(x, s, direction, u, v, w), axis)
            assert overlap(core, shape) < 1e-7
        # CQ/OCCT distance can return a spurious zero for remote pairs (this
        # upper-left clip versus C12 LED is separated by >838 mm along S).
        # An enclosing X/S rectangle gives a rigorous lower bound for every
        # through-N cylinder. Only near pairs need the exact-solid distance.
        s0, s1 = sorted((s, s+direction*51.9684))
        near = []
        for rx, rs, relief in reliefs:
            lower = math.hypot(max(x-39.2684-rx, 0, rx-x), max(s0-rs, 0, rs-s1))-20
            if lower >= 50:
                continue
            distance = shape.distance(relief)
            assert distance >= lower-1e-5, (name, rx, rs, distance, lower)
            assert distance >= 2 and overlap(shape, relief) < 1e-7, (name, rx, rs, distance)
            near.append(distance)
        assert near and min(near) >= 2
        # Model-only N edge distance; no manufacturer fastener-spacing rule implied.
        for c in frame.connections():
            if c.members[0] == name:
                n = (c.start-b.point(0, 0, 0)).dot(b.normal())
                assert min(n, 38.1-n) == pytest.approx(11.1125, abs=1e-7)


@pytest.mark.parametrize("gate", [gates.test_solids_and_collisions, gates.test_tool_led_and_routing_envelopes])
def test_complete_candidate_body_hardware_led_and_existing_tool_gates(monkeypatch, gate):
    monkeypatch.setattr(gates, "h", SimpleNamespace(parts=lambda _: frame.parts(),
        connections=lambda _: frame.connections(), panel_attachments=h.panel_attachments))
    gate(frame.KEY)


def test_all_clip_receivers_pilot_cores_and_provisional_driver_access():
    parts = {p.name: p for p in frame.parts()}
    hardware = {c.name: cq.Compound.makeCompound(c.components()) for c in frame.connections()}
    screws = [c for c in frame.connections() if c.name.startswith("clip_")]
    assert len(screws) == 32
    for c in screws:
        assert isinstance(c, frame.ClipScrew) and (c.length, c.diameter) == (30, 3.75)
        assert "UNSELECTED SCREW" in c.product_status and "specifies nails, not these screws" in c.product_status
        assert parts[c.members[0]].shape.distance(parts[c.members[1]].shape) < 1e-5
        pilot = cq.Solid.makeCylinder(1.59, c.length, c.start, c.direction)
        assert all(overlap(pilot, parts[n].shape) < .01 for n in c.members)
        # Receiving thread ring must remain entirely within the drilled net wood.
        outer = cq.Solid.makeCylinder(1.875, c.length-frame.THICKNESS, c.start+c.direction*frame.THICKNESS, c.direction)
        inner = cq.Solid.makeCylinder(1.61, c.length-frame.THICKNESS, c.start+c.direction*frame.THICKNESS, c.direction)
        ring = outer.cut(inner)
        assert overlap(ring, parts[c.members[1]].shape) == pytest.approx(ring.Volume(), abs=1e-5), c.name
        # Declared Ø10 straight driver, 25 mm approach; not a measured product/tool.
        tool = cq.Solid.makeCylinder(5, 25, c.start-c.direction*3, -c.direction)
        assert not [(n, overlap(tool, p.shape)) for n, p in parts.items() if overlap(tool, p.shape) > .01], c.name
        assert not [n for n, shape in hardware.items() if n != c.name and overlap(tool, shape) > .01], c.name
    for a, c in combinations(screws, 2):
        assert overlap(hardware[a.name], hardware[c.name]) < .01


def test_removed_mid_end_bores_are_refilled_in_rebuilt_rails():
    parts = {p.name: p for p in frame.parts()}
    removed = [c for c in baseline.connections() if c.name.startswith("mid_end_")]
    assert len(removed) == 8
    for c in removed:
        probe = cq.Solid.makeCylinder(.5, 1, c.start+c.direction*10, c.direction)
        assert overlap(probe, parts[c.members[0]].shape) == pytest.approx(probe.Volume(), abs=1e-5), c.name


def test_complete_shaft_clearance_receivers_and_moved_holes():
    parts = {p.name: p.shape for p in frame.parts()}
    old = {c.name: c for c in baseline.connections()}
    checked = 0
    for c in frame.connections():
        shaft = cq.Solid.makeCylinder(c.diameter/2, c.length, c.start, c.direction)
        assert not [name for name, shape in parts.items() if (c.kind == "bolt" or name not in c.members)
                    and overlap(shaft, shape) > .01], c.name
        receiver = cq.Solid.makeCylinder(5.5 if c.kind == "bolt" else 3, c.length, c.start, c.direction)
        assert all(overlap(receiver, parts[name]) > 1 for name in c.members), c.name
        previous = old.get(c.name)
        if previous is None or (c.start-previous.start).cross(c.direction).Length < 1e-5:
            continue
        # Old and new Ø10 bolt bores overlap at a 5 mm shift. Probe the old
        # bore's negative-X crescent, outside the intentional new bore.
        filled = cq.Solid.makeCylinder(.5, 1, previous.start+previous.direction*20-cq.Vector(2, 0, 0), previous.direction)
        assert overlap(filled, parts[previous.members[0]]) == pytest.approx(filled.Volume(), abs=1e-5), c.name
        checked += 1
    assert checked == 18
