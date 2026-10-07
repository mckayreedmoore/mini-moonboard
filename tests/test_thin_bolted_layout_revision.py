import copy

import cadquery as cq
import pytest

from scripts import hl35_candidate as shared
from scripts import thin_bolted_layout_revision as revised
from scripts import thin_bolted_occupied as occupied


def test_front_channel_contains_full_wire_lifting_corridor():
    route = [[0., 100., 8.], [100., 100., 8.]]
    cutter = revised.front_open_cutter(route, [0., 0., 0.], 6.35)
    first = revised.round_structural_wiring.b.point(*route[0])
    probe = cq.Solid.makeCylinder(6.35, 100., first, cq.Vector(1, 0, 0))
    for lift in (0., 2., 4., 6., 8.):
        body = probe.translate(revised.screen.N.multiply(-lift))
        assert shared.overlaps(body, cutter) / body.Volume() == pytest.approx(1., abs=1e-6)


def test_front_channel_rejects_depth_change_it_cannot_qualify():
    with pytest.raises(ValueError, match="planar route"):
        revised.front_open_cutter([[0., 0., 8.], [100., 0., 10.]], [0., 0., 0.], 6.35)


def test_flattened_collinear_wire_controls_preserve_endpoints_and_length():
    route = [[0., 100., 8.], [30., 100., 8.], [70., 100., 8.], [100., 100., 8.]]
    reduced = revised.simplify_route(route)
    assert reduced == [route[0], route[-1]]
    _, length = revised.service_tools.sweep(reduced, 1.5, [0., 0., 0.])
    assert length == pytest.approx(100.)


def fixture_axis():
    return {"id": "fixture", "point": cq.Vector(0, 0, 0), "direction": cq.Vector(0, 0, 1),
            "grip_mm": 38.1, "diameter_mm": 12.7, "before_plate_mm": 5.55625,
            "after_plate_mm": 0., "receivers": ["wood"],
            "hardware_scenario": copy.deepcopy(occupied.DEFAULT_SETTINGS["new_half_inch_hardware"]),
            "attachments": [{"angle_id": "B103ZN_fixture", "flange": "post", "duty_id": "fixture"}]}


def test_smaller_steel_face_washer_keeps_large_wood_face_washer_and_head_contact():
    record = fixture_axis()
    parts, changes = revised.metal_with_washers([record])
    parts = {role: shape for _, role, shape in parts}
    assert len(changes) == 1 and changes[0]["role"] == "head_washer"
    assert parts["head_washer"].BoundingBox().xlen == pytest.approx(27.7368)
    assert parts["nut_washer"].BoundingBox().xlen == pytest.approx(35.052)
    assert parts["head"].BoundingBox().zmax == pytest.approx(parts["head_washer"].BoundingBox().zmin)
    assert record["nominal_under_head_length_mm"] == pytest.approx(76.2)
    assert record["tip_projection_beyond_nut_mm"] > 2 * 25.4 / 13


def test_end_ray_on_known_rectangular_beam_distinguishes_bore_from_end_marker():
    beam = cq.Solid.makeBox(300, 139.7, 38.1)
    record = fixture_axis()
    record["point"] = cq.Vector(30, 69.85, 0)
    record["receivers"] = ["base_rail_fixture"]
    result = revised.grain_ray_ends({"base_rail_fixture": beam}, [record])[0]
    assert result["grain_ray_end_distances_mm"] == pytest.approx([30., 270.])
    assert result["at_least_3p5d_on_this_ray"] is False
    assert result["formal_end_distance_classified_or_force_applicable"] is False


def test_normal_hole_bridging_does_not_hide_missing_outer_washer_backing():
    record = fixture_axis()
    record["before_plate_mm"] = 0.
    record["bore_diameter_mm"] = 14.2875
    wood = cq.Solid.makeBox(100, 100, 38.1, cq.Vector(-50, -50, 0))
    wood = occupied.bore_wood({"wood": wood}, [record])["wood"]
    changes = [{"axis_id": "fixture", "role": "nut_washer", **revised.SAE_WASHER}]
    full = revised.actual_washer_seats([record], changes, {"wood": wood}, [])[1]
    assert full["actual_annulus_backed_fraction"] < 1.
    assert full["annulus_outside_intentional_opening_backed_fraction"] == pytest.approx(1.)
    slot = cq.Solid.makeBox(20, 100, 38.1, cq.Vector(10, -50, 0))
    partial = revised.actual_washer_seats([record], changes, {"wood": wood.cut(slot)}, [])[1]
    assert partial["annulus_outside_intentional_opening_backed_fraction"] < .99
    assert full["bridge_bending_and_bearing_resistance_checked"] is False
