"""Complete candidate geometry screens; no product or structural approval."""
import math
from collections import defaultdict
from itertools import pairwise
from types import SimpleNamespace

import cadquery as cq
import pytest
import test_hybrid_frame as gates

from mini_moonboard import box_frame as b
from mini_moonboard import hybrid_frame as h
from mini_moonboard import independent_leg_frame as baseline
from mini_moonboard import spacing_frame as frame
from mini_moonboard.box_exports import overlap
from mini_moonboard.panel_grid import main_led_datums, main_tnut_datums

ORIGIN = b.point(0, 0, 0)
TANGENT = (b.point(0, 1, 0) - ORIGIN).normalized()


def local(point):
    return point.x, (point - ORIGIN).dot(TANGENT), (point - ORIGIN).dot(b.normal())


@pytest.mark.parametrize("gate", [gates.test_solids_and_collisions, gates.test_tool_led_and_routing_envelopes])
def test_complete_body_hardware_socket_and_wiring_gates(monkeypatch, gate):
    monkeypatch.setattr(gates, "h", SimpleNamespace(parts=lambda _: frame.parts(),
        connections=lambda _: frame.connections(), panel_attachments=h.panel_attachments))
    gate(frame.KEY)


def test_receivers_connected_graph_and_all_four_floor_faces():
    parts = {p.name: p for p in frame.parts()}
    graph = {name: set() for name in parts}
    for c in frame.connections():
        for member in c.members:
            graph[member].update(set(c.members) - {member})
        # Upper attachment bolts intentionally connect a wall and two plies.
        for a, other in pairwise(c.members):
            assert parts[a].shape.distance(parts[other].shape) < 1e-5
        probe = cq.Solid.makeCylinder(5.5 if c.kind == "bolt" else 3, c.length, c.start, c.direction)
        assert all(overlap(probe, parts[name].shape) > 1 for name in c.members), c.name
        if c.kind == "screw":
            radial = c.direction.cross(cq.Vector(1, 0, 0))
            if radial.Length < .5:
                radial = c.direction.cross(cq.Vector(0, 1, 0))
            tip = c.start + c.direction * (c.length - .5) + radial.normalized() * 2.5
            assert parts[c.members[-1]].shape.isInside(tip, 1e-5), c.name
        else:
            assert 3 <= c.length - c.grip - 13 <= 7
    reached, todo = set(), ["box_side_left"]
    while todo:
        name = todo.pop()
        if name not in reached:
            reached.add(name)
            todo.extend(graph[name] - reached)
    assert reached == parts.keys()
    legs = [p for p in parts.values() if p.name.startswith("leg_")]
    assert {p.name for p in legs} == {f"leg_{side}_{layer}" for side in ("left", "right")
                                    for layer in ("inner", "outer")}
    for ply in legs:
        assert ply.laminations == 1 and ply.blank[2] == 19.05
        assert ply.shape.BoundingBox().zmin == pytest.approx(0, abs=1e-5)
        floors = [face for face in ply.shape.Faces() if abs(face.BoundingBox().zmin) < 1e-5
                  and abs(face.BoundingBox().zmax) < 1e-5]
        assert len(floors) == 1 and floors[0].geomType() == "PLANE"
        assert floors[0].Area() > 19.05 * 180


def test_exact_inventory_preserves_plies_stitches_panels_and_unmoved_parts():
    old = {c.name: c for c in baseline.connections()}
    current = {c.name: c for c in frame.connections()}
    assert len(current) == len(frame.connections()) == 226
    assert current.keys() == old.keys()
    changed = {f"rib_{row}_seam_{side}_front" for row in (1, 2, 3) for side in ("left", "right")}
    changed |= {f"angle_rib_{row}_seam_{side}_rib_{i}" for row in (1, 2, 3)
                for side in ("left", "right") for i in (1, 2)}
    changed |= {f"angle_rib_2_seam_{side}_beam_{i}" for side in ("left", "right") for i in (1, 2)}
    assert len(changed) == 22
    assert {name for name in current if current[name] is not old[name]} == changed
    for name, c in current.items():
        assert (c.members, c.kind, c.length, c.diameter, c.grip, c.direction) == (
            old[name].members, old[name].kind, old[name].length, old[name].diameter, old[name].grip, old[name].direction)
    assert {name for name in current if name.startswith("leg_stitch_")} == {
        f"leg_stitch_{side}_{i}" for side in ("left", "right") for i in (1, 2, 3)}
    seam_ribs = {f"rib_{row}_seam_{side}" for row in (1, 2, 3) for side in ("left", "right")}
    for drilled in (False, True):
        original = {p.name: p for p in (baseline.parts() if drilled else baseline.parts(False))}
        candidate = {p.name: p for p in frame.parts(drilled)}
        assert candidate.keys() == original.keys() and len(candidate) == len(frame.parts(drilled))
        expected = seam_ribs | ({"angle_" + name for name in seam_ribs} | {
            "panel_seam_vertical_lower", "panel_seam_vertical_upper", "panel_seam_horizontal", "rear_cross_2"}
            if drilled else {"angle_rib_2_seam_left", "angle_rib_2_seam_right"})
        assert {name for name in candidate if candidate[name] is not original[name]} == expected
    # The published predecessor still retains its own station geometry.
    assert local(old["rib_1_seam_left_front"].start) == pytest.approx((-54, 430, 0))
    assert local(old["rib_2_seam_right_front"].start) == pytest.approx((54, 1219.2, 0))


def test_all_twelve_positions_end_distances_reliefs_and_receiving_threads():
    undrilled = {p.name: p for p in frame.parts(False)}
    connections = {c.name: c for c in frame.connections()}
    expected = [
        (1, "seam_left", -54, 330, 350, 35), (1, "seam_right", 54, 505, 420, 70),
        (2, "seam_left", -76, 1219.2, 300, 70), (2, "seam_right", 76, 1219.2, 300, 35),
        (3, "seam_left", -54, 1930, 350, 35), (3, "seam_right", 54, 2105, 420, 70),
        *[(row, side, x, s, 300, 35) for row, s in ((1, 400), (2, 1219.2), (3, 2000))
          for side, x in (("mid_left", -519.2), ("mid_right", 680.8))],
    ]
    assert {f"rib_{row}_{side}_front" for row, side, *_ in expected} == {
        name for name in connections if name.startswith("rib_")}
    for row, side, x, s, length, bolt_offset in expected:
        name = f"rib_{row}_{side}"
        c, rib = connections[name + "_front"], undrilled[name]
        assert local(c.start) == pytest.approx((x, s, 0))
        assert rib.blank == pytest.approx((length, 89.95, 63.5))
        vertices = [local(v.Center()) for v in rib.shape.Vertices()]
        ends = min(p[1] for p in vertices), max(p[1] for p in vertices)
        assert ends == pytest.approx((b.CROSS_STATIONS[row - 1] - length / 2,
                                      b.CROSS_STATIONS[row - 1] + length / 2))
        assert min(s - ends[0], ends[1] - s) >= 101.6
        assert min(x - min(p[0] for p in vertices), max(p[0] for p in vertices) - x) >= 25.4
        # Include the actual chase's exposed X face, not just the blank edges.
        assert min(abs(x - face.Center().x) for face in rib.shape.Faces()
                   if abs(face.normalAt().x) > .999999) >= 25.4
        batten = [local(v.Center()) for v in undrilled[c.members[0]].shape.Vertices()]
        end_axis, edge_axis = (0, 1) if row == 2 else (1, 0)
        for axis, minimum in ((end_axis, 101.6), (edge_axis, 25.4)):
            value = (x, s)[axis]
            assert min(value - min(p[axis] for p in batten), max(p[axis] for p in batten) - value) >= minimum
        for i, offset in enumerate((-bolt_offset, bolt_offset), 1):
            bolt = connections[f"angle_{name}_rib_{i}"]
            bolt_s = local(bolt.start)[1]
            sign = -1 if x < 0 else 1
            assert local(bolt.start) == pytest.approx((x + sign * 39.75,
                b.CROSS_STATIONS[row - 1] + offset, 83.075))
            assert abs(s - bolt_s) - 5 - 5.4864 / 2 >= 25
            if row != 2 and side.startswith("seam"):
                assert min(bolt_s - ends[0], ends[1] - bolt_s) == pytest.approx(140)
        for i, offset in enumerate((38, 66), 1):
            assert local(connections[f"angle_{name}_beam_{i}"].start) == pytest.approx((
                x + sign * (31.75 + offset), b.CROSS_STATIONS[row - 1], 168.15))
        relief = min(math.hypot(x - (u - b.HALF), s - v) - 20
                     for u, v in (*main_led_datums().values(), *main_tnut_datums().values()))
        assert relief >= 25.4
        # Larger published SDWS16 thread envelope; still no head-profile or
        # product substitution claim. All 50.8 mm must lie in actual net wood.
        thread = cq.Solid.makeCylinder(5.4864 / 2, 50.8, c.start + c.direction * 38.1, c.direction)
        assert thread.intersect(rib.shape).Volume() == pytest.approx(thread.Volume(), abs=1e-5)


def test_directional_spacing_without_close_stagger_credit():
    connections = frame.connections()
    for c in connections:
        if not c.name.startswith("rib_") or c.name.startswith("rib_2_"):
            continue
        x, s, _ = local(c.start)
        for other in connections:
            if other.name == c.name or c.members[0] not in other.members or abs(other.direction.dot(b.normal())) < .99:
                continue
            ox, os, _ = local(other.start)
            # Conservative project screen for the near-aligned vertical strips,
            # not a radial allowance or mixed-product design approval.
            assert abs(x - ox) >= 50.8 or abs(s - os) >= 50.8
    points = [(round(local(c.start)[0], 6), round(local(c.start)[1], 6)) for c in connections
              if "panel_seam_horizontal" in c.members and abs(c.direction.dot(b.normal())) > .99]
    assert len(points) == 20  # Sixteen preserved panel screws plus four rib screws.
    for along_x, expected_spacing in ((True, 50), (False, 26)):
        rows = defaultdict(list)
        for x, s in points:
            rows[s if along_x else x].append(x if along_x else s)
        keys = sorted(rows)
        spacing = min(right - left for left, right in pairwise(keys))
        pitch = min(right - left for values in rows.values()
                    for left, right in pairwise(sorted(values)))
        assert spacing == pytest.approx(expected_spacing) and spacing >= 25.4
        assert pitch == pytest.approx(100) and pitch >= 50.8


def test_screw_clearance_and_pilot_cores_are_drilled():
    parts = {p.name: p.shape for p in frame.parts()}
    for c in frame.connections():
        if c.kind != "screw":
            continue
        for index, name in enumerate(c.members):
            # Only the drilled core must be empty; the larger nominal screw
            # envelope intentionally engages wood in the receiving member.
            radius = (2.6 if index == 0 else 1.6) - .01
            core = cq.Solid.makeCylinder(radius, c.length, c.start, c.direction)
            assert overlap(core, parts[name]) < .01, (c.name, name)


def test_bolt_bores_shafts_and_superseded_holes():
    parts = {p.name: p.shape for p in frame.parts()}
    old = {c.name: c for c in baseline.connections()}
    checked_old_holes = 0
    for c in frame.connections():
        probe = cq.Solid.makeCylinder(5 if c.kind == "bolt" else c.diameter / 2, c.length, c.start, c.direction)
        assert not [name for name, shape in parts.items() if (c.kind == "bolt" or name not in c.members)
                    and overlap(probe, shape) > .01], c.name
        previous = old[c.name]
        # Translation along an existing bore axis does not create a separate
        # abandoned bore. Every changed, noncoincident axis must be refilled.
        if (c.start - previous.start).cross(c.direction).Length < 1e-5:
            continue
        depth = 5 if c.name.startswith("angle_") and c.name.rsplit("_", 2)[1] == "rib" else 20
        filled = cq.Solid.makeCylinder(.5, 1, previous.start + previous.direction * depth, previous.direction)
        assert overlap(filled, parts[previous.members[0]]) == pytest.approx(filled.Volume(), abs=1e-5), c.name
        checked_old_holes += 1
    assert checked_old_holes == 18
