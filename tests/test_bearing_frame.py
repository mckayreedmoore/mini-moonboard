"""Lower-bearing development: nominal geometry, not connection qualification."""
import cadquery as cq
import pytest
import test_mvp_fasteners as hardware
import test_redesign_mvp as layouts

from mini_moonboard import bearing_frame as frame
from mini_moonboard import box_frame as b
from mini_moonboard import bracket_mvp as bracket
from mini_moonboard import continuous_frame as baseline


@pytest.fixture(scope="module")
def candidate():
    return frame, {p.name: p for p in frame.parts()}


test_faces = layouts.test_purchased_face_thickness_and_fixed_backing_datums
test_holes = layouts.test_all_official_hold_and_led_axes_remain_open
test_floor_graph = layouts.test_four_independent_legs_have_flat_floor_faces_and_connected_inventory
test_body_collisions = layouts.test_body_housings_contact_without_unintended_penetration
test_fastener_collisions = hardware.test_heads_washers_nuts_and_unrelated_shafts_clear_all_bodies
test_receivers = hardware.test_axes_have_real_receivers_and_open_pilot_paths
test_fastener_pairs = hardware.test_distinct_fastener_components_do_not_intersect
test_service = hardware.test_rear_hold_flanges_and_led_reservations_clear_nonface_parts


def test_full_rails_and_finite_lower_bearing(candidate):
    _, parts = candidate
    raw = {p.name: p for p in frame.parts(False)}
    rail = parts["lean_beam_lower_full"].shape
    for level in ("lower", "top"):
        name = f"lean_beam_{level}_full"
        assert len(parts[name].shape.Solids()) == 1
        assert raw[name].blank == pytest.approx((2438.4, 139.7, 38.1))
        for side in ("left", "right"):
            assert parts[name].shape.distance(parts["box_side_"+side].shape) < 1e-6
    for side in ("left", "right"):
        upright = parts["lean_principal_"+side].shape
        # Infinitesimal translation measures a positive-area bearing interface,
        # rather than accepting a single corner contact or metadata graph edge.
        contact = upright.translate(-frame.TANGENT*.001).intersect(rail).Volume()/.001
        assert contact == pytest.approx(38.1*101.6, rel=1e-5)
        assert upright.intersect(rail).Volume() < 1e-6
    witness = cq.Solid.makeCylinder(1., 200., b.point(-100., 120.65, 160.), cq.Vector(1, 0, 0))
    assert witness.intersect(rail).Volume() == pytest.approx(witness.Volume(), abs=1e-5)


def test_replaces_failed_ledge_screws_with_rotated_connector_groups(candidate):
    _, parts = candidate
    connections = frame.connections()
    assert not any(c.name.startswith("lean_lower_ledge_") for c in connections)
    assert len(connections) == len(baseline.connections())-4+24
    for index in range(1, 5):
        name = f"clip_mvp_ledge_{index}"
        group = [c for c in connections if c.name.startswith(name+"_")]
        assert len(group) == 6
        assert {c.members[1] for c in group} == {"wood_rail_lower", "lean_beam_lower_full"}
        for c in group:
            expected = frame.TANGENT if "_beam_" in c.name else -b.normal()
            assert c.direction.toTuple() == pytest.approx(expected.toTuple())
            assert c.length == 38.1
        for receiver in ("wood_rail_lower", "lean_beam_lower_full"):
            assert parts[name].shape.distance(parts[receiver].shape) < 1e-6


def test_new_angles_are_rigid_copies_not_custom_steel():
    raw = {p.name: p for p in frame.parts(False)}
    factory, _ = bracket._connector(cq.Vector(), cq.Vector(1, 0, 0), frame.TANGENT)
    for index, x in enumerate(frame.LEDGE_CLIP_X_MM, 1):
        restored = raw[f"clip_mvp_ledge_{index}"].shape.translate(-b.point(x, 101.6, 38.1)).rotate(
            (0, 0, 0), (cq.Vector(1, 0, 0)+b.normal()).toTuple(), -180)
        assert restored.Volume() == pytest.approx(factory.Volume(), abs=1e-5)
        assert restored.cut(factory).Volume()+factory.cut(restored).Volume() < 1e-5
