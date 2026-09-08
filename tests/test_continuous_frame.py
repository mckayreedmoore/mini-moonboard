"""Continuous cross-board material and inherited clearance checks, not approval."""
import cadquery as cq
import pytest
import test_mvp_fasteners as hardware
import test_redesign_mvp as layouts

from mini_moonboard import box_frame as b
from mini_moonboard import continuous_frame as frame


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


def test_two_unspliced_full_width_crossmembers(candidate):
    _, parts = candidate
    raw = {p.name: p for p in frame.parts(False)}
    assert not set(frame.REPLACEMENTS) & parts.keys()
    for level, s, n in (("top", 2419.35, 120.), ("lower", 119.05, 160.)):
        name = f"lean_beam_{level}_full"
        assert len(parts[name].shape.Solids()) == 1
        assert raw[name].blank == pytest.approx((2438.4, 139.7, 38.1))
        assert raw[name].shape.Volume() == pytest.approx(2438.4*139.7*38.1)
        # A material witness spans the old gap and upright widths, away from
        # legitimate connection drillings in the member's shallower region.
        witness = cq.Solid.makeCylinder(1., 200., b.point(-100., s, n), cq.Vector(1, 0, 0))
        assert witness.intersect(parts[name].shape).Volume() == pytest.approx(witness.Volume(), abs=1e-5)
        clips = [c for c in frame.connections() if name in c.members and c.name.startswith("clip_")]
        assert len(clips) == 12  # Three rail screws at each of four retained clips.
    for side in ("left", "right"):
        assert raw["lean_principal_"+side].blank[0] == pytest.approx(2260.6)
    for c in frame.connections():
        assert not set(c.members) & frame.REPLACEMENTS.keys()
