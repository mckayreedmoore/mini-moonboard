"""Bolted square-cut candidates: geometry screens, never a capacity approval."""
import math
from importlib import import_module

import cadquery as cq
import pytest
import test_mvp_fasteners as hardware
import test_redesign_mvp as layouts

from mini_moonboard import box_frame as b
from mini_moonboard import product_frame as product


@pytest.fixture(scope="module", params=["bolted_frame", "bolted_blocks"])
def candidate(request):
    frame = import_module("mini_moonboard." + request.param)
    values = frame.parts()
    parts = {p.name: p for p in values}
    assert len(parts) == len(values), "Duplicate body identifiers"
    return frame, parts


# Reuse the established full-body and hardware checks with our local fixture.
test_purchased_face_datums = layouts.test_purchased_face_thickness_and_fixed_backing_datums
test_official_hold_led_grid = layouts.test_all_official_hold_and_led_axes_remain_open
test_floor_and_connection_graph = layouts.test_four_independent_legs_have_flat_floor_faces_and_connected_inventory
test_body_contacts_and_collisions = layouts.test_body_housings_contact_without_unintended_penetration
test_hardware_body_clearance = hardware.test_heads_washers_nuts_and_unrelated_shafts_clear_all_bodies
test_receivers_and_pilot_paths = hardware.test_axes_have_real_receivers_and_open_pilot_paths
test_hardware_pair_clearance = hardware.test_distinct_fastener_components_do_not_intersect
test_hold_and_led_service = hardware.test_rear_hold_flanges_and_led_reservations_clear_nonface_parts


def local_bounds(shape):
    """Net-stock bounds in board X/S/N, independent of declared blank sizes."""
    origin = b.point(0, 0, 0)
    tangent = (b.point(0, 1, 0) - origin).normalized()
    points = [(v.Center().x, (v.Center()-origin).dot(tangent),
               (v.Center()-origin).dot(b.normal())) for v in shape.Vertices()]
    return tuple((min(p[i] for p in points), max(p[i] for p in points)) for i in range(3))


def test_inventory_valid_and_no_custom_steel(candidate):
    frame, parts = candidate
    assert layouts.FACES <= parts.keys()
    for name, part in parts.items():
        assert part.shape.isValid() and len(part.shape.Solids()) == 1, name
        assert math.isfinite(part.shape.Volume()) and part.shape.Volume() > 0, name
        assert all(math.isfinite(v) and v > 0 for v in part.blank), name
        assert not name.startswith(("angle_", "transition_")), name
        if name.startswith("clip_"):
            assert frame.__name__.endswith(".bolted_frame"), name
            assert "ML24Z" in part.description, name


def test_repeated_deep_stock_is_rectangular_without_housings(candidate):
    frame, _ = candidate
    raw = frame.parts(False)
    uprights, beams = [], []
    for part in raw:
        if not part.name.startswith(("wood_principal_", "wood_beam_", "wood_edge_principal_")):
            continue
        bounds = local_bounds(part.shape)
        sizes = tuple(hi-lo for lo, hi in bounds)
        expected = b.block(*(value for pair in bounds for value in pair))
        assert len(part.shape.Faces()) == 6, part.name
        assert all(face.geomType() == "PLANE" for face in part.shape.Faces()), part.name
        assert part.shape.Volume() == pytest.approx(expected.Volume(), abs=1e-5), part.name
        assert sorted(part.blank) == pytest.approx(sorted(sizes)), part.name
        if part.name.startswith("wood_beam_"):
            assert sizes == pytest.approx((984.1, 88.9, 139.7)), part.name
            beams.append(part.name)
        else:
            length = 2324.1 if part.name.startswith("wood_edge_principal_") else 2438.4
            assert sizes == pytest.approx((88.9, length, 139.7)), part.name
            assert bounds[1][0] == pytest.approx(114.3 if length == 2324.1 else 0.), part.name
            uprights.append(part.name)
    assert len(uprights) == 4, uprights
    assert sum(name.startswith("wood_edge_principal_") for name in uprights) == 2
    assert len(beams) == 6, beams


def test_flat_ledges_have_only_service_reliefs_before_connection_drilling(candidate):
    frame, _ = candidate
    baseline = import_module("mini_moonboard.bolted_frame")
    raw = {p.name: p for p in frame.parts(False)}
    rows = list(baseline.ledger_layout())
    assert len(rows) == 11
    for name, x0, x1, s0, s1 in rows:
        part = raw[name]
        blank = b.block(x0, x1, s0, s1, 0., 38.1)
        witness = b.Part("panel_"+name, blank, part.blank, "service-only witness")
        expected = product._backing_reliefs(witness)
        assert part.shape.Volume() == pytest.approx(expected.Volume(), abs=1e-5), name
        assert part.shape.intersect(expected).Volume() == pytest.approx(expected.Volume(), abs=1e-5), name


def test_front_through_bolts_and_recesses_replace_withdrawal_connections(candidate):
    frame, parts = candidate
    connections = frame.connections()
    assert not any(c.name.startswith(("easy_", "wood_edge_", "wood_principal_ledge_"))
                   for c in connections)
    front = [c for c in connections if c.name.startswith(("bolted_ledge_", "bolted_lower_", "bolted_rail_"))]
    rim = [c for c in connections if c.name.startswith("bolted_rim_")]
    assert len(front) == 28 and len(rim) == 8
    origin, normal = b.point(0, 0, 0), b.normal()
    for c in front:
        assert c.kind == "bolt" and c.diameter == pytest.approx(9.525), c.name
        assert c.length == pytest.approx(190.5), c.name
        assert c.grip == pytest.approx(168.4608), c.name
        assert c.direction.toTuple() == pytest.approx(normal.toTuple()), c.name
        assert (c.start-origin).dot(normal) == pytest.approx(7.3072), c.name
        depths = [(v.Center()-origin).dot(normal) for v in c.components()[3].Vertices()]
        assert min(depths) == pytest.approx(.5, abs=1e-6), c.name
        # Cylinder must fit the full 1-1/8 in counterbore, not merely shaft hole.
        face_start = c.start-normal*7.3072
        pocket = cq.Solid.makeCylinder(28.575/2-.01, 9.3392, face_start, normal)
        ledge = parts[c.members[0]].shape
        assert pocket.intersect(ledge).Volume() < 1e-5, c.name
        # Immediately behind the pocket wall, material resumes. The remaining
        # ledge thickness is 28.7608 mm; no strength is inferred from this.
        witness = cq.Solid.makeCylinder(.1, 28.7608-.02,
            face_start+normal*(9.3392+.01)+cq.Vector(13., 0, 0), normal)
        assert witness.intersect(ledge).Volume() == pytest.approx(witness.Volume(), abs=1e-5), c.name
    for c in rim:
        assert c.kind == "bolt" and c.diameter == pytest.approx(9.525), c.name
        assert c.length == pytest.approx(152.4) and c.grip == pytest.approx(127.), c.name
        assert abs(c.direction.x) == pytest.approx(1.), c.name
    leg_bolts = [c for c in connections if c.name.startswith("analysis_leg_wall_bolt_")]
    assert len(leg_bolts) == 8
    for c in leg_bolts:
        assert c.kind == "bolt" and c.diameter == pytest.approx(9.525), c.name
        assert c.length == pytest.approx(190.5) and c.grip == pytest.approx(165.1), c.name
        assert len(c.members) == 4, c.name
        assert sum(name.startswith("leg_") for name in c.members) == 2, c.name
        assert sum(name.startswith("wood_edge_principal_") for name in c.members) == 1, c.name
        assert (c.start-origin).dot(normal) == pytest.approx(78.075), c.name


def test_assumed_front_socket_approach_before_skins_and_legs(candidate):
    frame, parts = candidate
    normal = b.normal()
    front = [c for c in frame.connections() if c.name.startswith(("bolted_ledge_", "bolted_lower_", "bolted_rail_"))]
    framing = {name: p for name, p in parts.items()
               if name not in layouts.FACES and not name.startswith("leg_")}
    bounds, findings = {}, []
    approaches = {c.name: cq.Solid.makeCylinder(12.7, 100.,
        c.start-normal*(6.8072+100.), normal) for c in front}
    for c in front:
        # Assumed socket stops at the top of recessed head (N0.5), not at
        # washer plane. It is not an actual tool sweep or product fit proof.
        approach = approaches[c.name]
        for name, part in framing.items():
            volume = hardware.positive_overlap(approach, part.shape, bounds)
            if volume > hardware.THRESHOLD_MM3:
                findings.append((c.name, name, volume))
    assert not findings, findings


def test_common_bolt_actual_receiver_end_and_edge_screen(candidate):
    frame, _ = candidate
    raw = {p.name: p for p in frame.parts(False)}
    origin = b.point(0, 0, 0)
    axes = (cq.Vector(1, 0, 0), (b.point(0, 1, 0)-origin).normalized(), b.normal())
    connections = [c for c in frame.connections() if c.name.startswith(("bolted_", "analysis_leg_wall_bolt_"))]
    assert len(connections) == 44
    for c in connections:
        shaft_axis = max(range(3), key=lambda i: abs(c.direction.dot(axes[i])))
        position = tuple((c.start-origin).dot(axis) for axis in axes)
        for name in c.members:
            if name.startswith("leg_"):
                continue  # Independent plywood plies are not solid-timber grain screens.
            grain = 0 if name.startswith(("wood_rail_", "wood_beam_")) else 1
            assert shaft_axis != grain, (c.name, name, "end-grain fastening")
            transverse = next(i for i in range(3) if i not in (grain, shaft_axis))
            bounds = local_bounds(raw[name].shape)
            end_distance = min(position[grain]-bounds[grain][0], bounds[grain][1]-position[grain])
            edge_distance = min(position[transverse]-bounds[transverse][0], bounds[transverse][1]-position[transverse])
            assert end_distance >= 7*c.diameter-1e-6, (c.name, name, "7D end", end_distance)
            assert edge_distance >= 4*c.diameter-1e-6, (c.name, name, "4D loaded edge", edge_distance)


def test_block_bolts_have_actual_two_member_edge_margins(candidate):
    frame, parts = candidate
    if not frame.__name__.endswith(".bolted_blocks"):
        return
    raw = {p.name: p for p in frame.parts(False)}
    blocks = [p for p in raw.values() if p.name.startswith("wood_joint_block_")]
    assert len(blocks) == 12
    for part in blocks:
        bounds = local_bounds(part.shape)
        assert tuple(hi-lo for lo, hi in bounds) == pytest.approx((88.9, 88.9, 139.7)), part.name
        assert len(part.shape.Faces()) == 6, part.name
        assert part.shape.Volume() == pytest.approx(88.9*88.9*139.7), part.name
    bolts = [c for c in frame.connections() if c.name.startswith("wood_joint_block_")]
    assert len(bolts) == 36
    assert sum(any(name.startswith("box_side_") for name in c.members) for c in bolts) == 12
    origin = b.point(0, 0, 0)
    axes = (cq.Vector(1, 0, 0), (b.point(0, 1, 0)-origin).normalized(), b.normal())
    for c in bolts:
        assert c.kind == "bolt" and c.diameter == pytest.approx(6.35), c.name
        outer = any(name.startswith("box_side_") for name in c.members)
        assert c.length == pytest.approx(228.6 if outer else 190.5), c.name
        assert c.grip == pytest.approx(215.9 if outer else 177.8), c.name
        assert len(c.members) == (3 if outer else 2), c.name
        shaft_axis = max(range(3), key=lambda i: abs(c.direction.dot(axes[i])))
        position = tuple((c.start-origin).dot(axis) for axis in axes)
        for name in c.members:
            # The block grain is N; beams grain X; continuous uprights grain S.
            grain = 2 if name.startswith("wood_joint_block_") else (0 if name.startswith("wood_beam_") else 1)
            assert shaft_axis != grain, (c.name, name, "end-grain fastening")
            bounds = local_bounds(raw[name].shape)
            transverse = next(i for i in range(3) if i not in (grain, shaft_axis))
            end_distance = min(position[grain]-bounds[grain][0], bounds[grain][1]-position[grain])
            edge_distance = min(position[transverse]-bounds[transverse][0], bounds[transverse][1]-position[transverse])
            assert end_distance >= 7*c.diameter-1e-6, (c.name, name, "7D end", end_distance)
            assert edge_distance >= 4*c.diameter-1e-6, (c.name, name, "4D loaded edge", edge_distance)
            # Verify the drilled body, not only the clearance constant: the
            # quarter-inch clearance is open, and material remains just beyond
            # it (a mistakenly reused 3/8-inch clearance would remove this).
            core = cq.Solid.makeCylinder(7.14375/2-.01, c.length, c.start, c.direction)
            assert core.intersect(parts[name].shape).Volume() < 1e-5, (c.name, name)
            midpoint = sum(bounds[shaft_axis])/2
            center = c.start+axes[shaft_axis]*(midpoint-position[shaft_axis])
            witness = cq.Solid.makeCylinder(.1, 1., center+axes[grain]*3.9-c.direction*.5, c.direction)
            assert witness.intersect(parts[name].shape).Volume() == pytest.approx(witness.Volume(), abs=1e-5), (c.name, name)
        # Exact nominal clearance remains a smaller quarter-inch-family bore,
        # independently of the reused 3/8-inch common frame connections.
        assert frame.BOLT_CLEARANCE_MM == pytest.approx(7.14375)
