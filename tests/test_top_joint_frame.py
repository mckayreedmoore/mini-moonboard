"""Top-joint relocation geometry and declared spacing screen, not resistance approval."""
import math
from types import SimpleNamespace

import cadquery as cq
import pytest
import test_clip_frame as clip_tests
import test_product_frame as product_tests
import test_product_service_clearance as service

from mini_moonboard import box_frame as b
from mini_moonboard import product_frame as baseline
from mini_moonboard import top_joint_frame as frame
from mini_moonboard.box_exports import overlap

CHANGED_BODIES = {f"{prefix}_{side}" for prefix in ("box_side", "transition_top_angle")
                  for side in ("left", "right")}
CHANGED_BOLTS = {f"transition_top_{side}_bolt_{index}" for side in ("left", "right") for index in (1, 2)}
TANGENT = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
service_envelopes = service.service_envelopes


@pytest.fixture(scope="module")
def parts():
    return {p.name: p for p in frame.parts()}


def test_goal_critical_current_candidate_floor_orientation_and_graph(monkeypatch):
    monkeypatch.setattr(clip_tests, "frame", frame)
    clip_tests.test_candidate_floor_seating_orientation_and_connection_graph()


def test_goal_critical_climbing_underside_and_rear_rib_sidedness():
    # Independent world-axis expectation: climbing face points +Y and down;
    # using abs(normal dot axis) would also accept the opposite face.
    angle = math.radians(40.)
    climbing = cq.Vector(0, math.cos(angle), -math.sin(angle))
    rear = -climbing
    origin = b.point(0, 0, 0)
    raw = frame.parts(False)
    panels = [p for p in raw if p.name.startswith("main_")]
    ribs = [p for p in raw if p.name.startswith("rib_")]
    assert len(panels) == 4 and len(ribs) == 12
    for part in panels+ribs:
        depths = [(v.Center()-origin).dot(rear) for v in part.shape.Vertices()]
        expected = (-18.25625, 0.) if part.name.startswith("main_") else (38.1, 128.05)
        assert (min(depths), max(depths)) == pytest.approx(expected, abs=1e-6), part.name
        if part.name.startswith("main_"):
            faces = [f for f in part.shape.Faces() if f.geomType() == "PLANE"
                     and abs((f.Center()-origin).dot(rear)+18.25625) < 1e-6]
            assert len(faces) == 1, part.name
            assert faces[0].normalAt().dot(climbing) > 1-1e-7, part.name


def test_exact_four_bolt_relocation_preserves_other_connection_datums():
    old = {c.name: c for c in baseline.connections()}
    new = {c.name: c for c in frame.connections()}
    assert len(new) == len(frame.connections()) == 278 and new.keys() == old.keys()
    for name, c in new.items():
        previous = old[name]
        assert (c.members, c.kind, c.length, c.diameter, c.grip) == (
            previous.members, previous.kind, previous.length, previous.diameter, previous.grip)
        assert c.direction.toTuple() == pytest.approx(previous.direction.toTuple())
        if name not in CHANGED_BOLTS:
            assert (c.start-previous.start).Length < 1e-8, name
            continue
        station = 2328. if name.endswith("_1") else 2368.
        assert (c.start-b.point(0, 0, 0)).dot(TANGENT) == pytest.approx(station)
        assert (c.start-b.point(0, 0, 0)).dot(b.normal()) == pytest.approx(63.)
        assert c.start.x == pytest.approx(previous.start.x)
        assert "inspection envelope only" in c.product_status


def test_exact_four_changed_bodies_and_preserved_rail_facing_leaf(parts):
    old = {p.name: p for p in baseline.parts()}
    assert len(parts) == 87 and parts.keys() == old.keys()
    for name, part in parts.items():
        assert part.shape.isValid(), name
        same_volume = overlap(part.shape, old[name].shape)
        difference = part.shape.Volume()+old[name].shape.Volume()-2*same_volume
        if name in CHANGED_BODIES:
            assert difference > 1, name
        else:
            assert difference == pytest.approx(0, abs=1e-4), name
    for side, sign in (("left", -1), ("right", 1)):
        angle = f"transition_top_angle_{side}"
        # Interior slab of horizontal leaf, including both unchanged screw bores.
        x0, x1 = sorted((sign*b.HALF, sign*(b.HALF-140)))
        slab = b.block(x0, x1, 2359.5, 2428.4, 38.1, 44.)
        before, after = old[angle].shape.intersect(slab), parts[angle].shape.intersect(slab)
        assert before.Volume() > 0
        assert after.Volume() == pytest.approx(before.Volume(), abs=1e-5)
        assert overlap(after, before) == pytest.approx(before.Volume(), abs=1e-5)
        stations = [(v.Center()-b.point(0, 0, 0)).dot(TANGENT) for v in parts[angle].shape.Vertices()]
        assert min(stations) == pytest.approx(2313., abs=1e-6)
        assert max(stations) == pytest.approx(2428.4, abs=1e-6)


def test_old_top_bores_refilled_and_new_full_diameter_paths_open(parts):
    old = {c.name: c for c in baseline.connections()}
    new = {c.name: c for c in frame.connections()}
    raw = {p.name: p for p in baseline.parts(False)}
    for name in CHANGED_BOLTS:
        previous, current = old[name], new[name]
        old_core = cq.Solid.makeCylinder(.4, previous.length, previous.start, previous.direction)
        new_core = cq.Solid.makeCylinder(11.1125/2-.1, current.length, current.start, current.direction)
        for member in current.members:
            expected_filled = overlap(old_core, raw[member].shape)
            assert expected_filled > 1, (name, member)
            assert overlap(old_core, parts[member].shape) == pytest.approx(expected_filled, abs=1e-5), (name, member)
            assert overlap(new_core, parts[member].shape) < 1e-5, (name, member)
            witness = cq.Solid.makeCylinder(6.5, current.length, current.start, current.direction)
            assert overlap(witness, parts[member].shape) > 1, (name, member)


def test_declared_wood_end_edge_and_spacing_arithmetic_only():
    diameter = 9.525
    assert 7*diameter == pytest.approx(66.675)
    assert 4*diameter == pytest.approx(38.1)
    raw = {p.name: p for p in frame.parts(False)}
    for side in ("left", "right"):
        bolts = [c for c in frame.connections() if c.name in CHANGED_BOLTS and f"_{side}_" in c.name]
        stations = sorted((c.start-b.point(0, 0, 0)).dot(TANGENT) for c in bolts)
        assert [b.LENGTH-s for s in stations] == pytest.approx([110.4, 70.4])
        assert all(b.LENGTH-s >= 7*diameter for s in stations)
        assert stations[1]-stations[0] == pytest.approx(40.)
        assert stations[1]-stations[0] >= 4*diameter
        normals = [(v.Center()-b.point(0, 0, 0)).dot(b.normal())
                   for v in raw[f"box_side_{side}"].shape.Vertices()]
        edges = (63.-min(normals), max(normals)-63.)
        assert edges == pytest.approx((81., 103.15))
        assert min(edges) >= 4*diameter
    # Applied to the nominal wooden rim only; not a steel-edge rule, mixed-load
    # capacity check, material approval or allowance for fabrication tolerances.


def test_full_selected_washer_bearing_after_relocation(monkeypatch):
    monkeypatch.setattr(service, "frame", SimpleNamespace(parts=frame.parts, connections=frame.connections,
        BOLT_HOLE_DIAMETER_MM=baseline.BOLT_HOLE_DIAMETER_MM))
    service.test_all_bolt_washers_have_full_minimum_bearing_annuli_in_receiving_bodies()


def test_every_incident_connection_preserves_its_open_core_and_receiver(monkeypatch, parts):
    monkeypatch.setattr(product_tests, "frame", SimpleNamespace(connections=frame.connections))
    product_tests.test_every_connection_has_receiving_material_and_open_core(parts)


@pytest.mark.parametrize("category", ["parts", "hardware"])
def test_relocated_joint_preserves_reserved_service_clearance(monkeypatch, service_envelopes, category):
    monkeypatch.setattr(service, "frame", SimpleNamespace(parts=frame.parts, connections=frame.connections))
    service.test_all_selected_parts_and_hardware_clear_reserved_service_space(category, service_envelopes)
