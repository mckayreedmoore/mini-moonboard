"""Check continuous handle bounds independently at much finer angles."""
import csv
import json
import math
from pathlib import Path

import pytest

from scripts.eoere_drill_fixture_requirements import (
    alignment_budget,
    raw_contains,
    receiver_support,
)
from scripts.eoere_nominal_access import (
    envelope_intrusions,
    removal_envelopes,
    removal_interval,
    selected_setup_requirements,
    swept_handle_polygon,
    wrench_envelopes,
)


@pytest.mark.parametrize("degrees", [15, 30, 60, 90])
def test_convex_bound_encloses_every_corner_through_fine_continuous_sweep(degrees):
    polygon = swept_handle_polygon(degrees)
    for i in range(degrees * 10 + 1):
        a = math.radians(-degrees / 2 + i / 10)
        for x in (9.525, 161.925):
            for y in (-9.525, 9.525):
                p = (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))
                for u, v in zip(polygon, polygon[1:] + polygon[:1], strict=True):
                    cross = (v[0] - u[0]) * (p[1] - u[1]) - (v[1] - u[1]) * (p[0] - u[0])
                    assert cross >= -1e-9
    assert max(math.hypot(*p) for p in polygon) < 162.3


def test_drill_budget_uses_shop_bit_not_larger_occupied_cad_bore():
    result = alignment_budget(177.8, 19.05, 13.49375, 12.7, .02, .1984375)
    assert result["nominal_radial_fit_budget_mm"] == pytest.approx(.396875)
    assert result["worst_nominal_guide_play_drift_mm"] == pytest.approx(.1866666666667)
    assert result["remaining_nominal_radial_budget_mm"] == pytest.approx(.0117708333333)
    assert alignment_budget(177.8, 19.05, 13.49375, 12.7, .1, 0)["remaining_nominal_radial_budget_mm"] < 0


def test_clamp_pad_bound_honors_sloping_raw_end():
    profile = {"vertices_luv_mm": [[0, 0, 0], [100, 10, 20]],
        "end_planes": [
            {"outward_normal_l_unitless": -1, "outward_normal_u_unitless": 0,
             "outward_normal_v_unitless": 0, "plane_offset_from_datum_mm": 0},
            {"outward_normal_l_unitless": 1, "outward_normal_u_unitless": 0,
             "outward_normal_v_unitless": 1, "plane_offset_from_datum_mm": 100}]}
    assert raw_contains([80, 5, 20], profile)
    assert not raw_contains([90, 5, 20], profile)
    assert not raw_contains([50, 11, 0], profile)


@pytest.mark.parametrize("part_length", [8.5598, 12.7])
def test_removal_corridor_contains_rigid_part_through_complete_tip_clearance(part_length):
    seat, tip = 47.0916, 79.9084
    start, end = removal_interval(seat, part_length, tip)
    # Independently move both physical faces until the near face reaches the
    # selected tip. A nut-height bound fails the last part of spacer travel.
    for i in range(201):
        displacement = (tip - seat) * i / 200
        for face in (seat, seat + part_length):
            assert start - 1e-9 <= face + displacement <= end + 1e-9
    assert end == pytest.approx(92.6084 if part_length == 12.7 else 88.4682)


def test_spacer_corridor_detects_obstacle_beyond_the_shorter_nut_height():
    import cadquery as cq

    axis = {"before_plate_mm": 6.35, "after_plate_mm": 6.35, "grip_mm": 38.1, "diameter_mm": 9.525,
            "hardware_scenario": {"washer_thickness_mm": 2.6416, "head_height_mm": 6,
                                  "nut_height_mm": 8.5598, "hex_across_flats_mm": 14.2875}}
    selection = {"selected_underhead_length_mm": 88.9, "nut_side_spacer_mm": 12.7}
    envelopes = {row[0]: row[1:] for row in removal_envelopes(axis, selection, "nut")}
    start, length, radius = envelopes["spacer_removal"]
    body = cq.Solid.makeCylinder(radius, length, cq.Vector(0, 0, start))
    assert body.BoundingBox().zmax == pytest.approx(92.6084)
    nut_start, nut_length, _ = envelopes["nut_removal"]
    assert nut_start + nut_length == pytest.approx(88.4682)
    # Entire obstacle lies beyond tip + 8.5598, inside the last spacer travel.
    obstacle = cq.Workplane("XY").box(1, 1, 1).translate((0, 0, 90)).val()
    bank = {"foreign_bracket": {"kind": "bracket", "bounds": [-.5, .5, -.5, .5, 89.5, 90.5]}}
    result = envelope_intrusions(body, bank, lambda _: obstacle, "own", stage=True)
    assert result["nominal_intrusions"] == ["foreign_bracket"]
    assert result["fine_queries"][0]["intersection_mm3"] == pytest.approx(1)


def test_production_envelopes_contain_every_selected_part_through_full_removal():
    doc = Path(__file__).resolve().parents[1] / ("docs/wood-joints-mvp/hypotheses/hl35-candidate/"
        "thin-frame-comparison/eoere-successor-v1")
    axes = {row["id"]: row for row in json.loads((doc / "occupied-kicker-clearance-v1.json").read_bytes())["axes"]}
    selections = json.loads((doc / "occupied-selected-hardware-v1.json").read_bytes())["selected_stacks"]
    for selection in selections:
        axis = axes[selection["axis_id"]]
        h = axis["hardware_scenario"]
        length, spacer = selection["selected_underhead_length_mm"], selection["nut_side_spacer_mm"]
        head_seat = -axis["before_plate_mm"] - h["washer_thickness_mm"]
        tip = head_seat + length
        spacer_seat = axis["grip_mm"] + axis["after_plate_mm"] + h["washer_thickness_mm"]
        nut_seat = spacer_seat + spacer
        physical_parts = {
            "head": [("full_shaft_withdrawal", head_seat, length, -length, axis["diameter_mm"] / 2),
                     ("head_withdrawal", head_seat - h["head_height_mm"], h["head_height_mm"], -length,
                      h["hex_across_flats_mm"] / math.sqrt(3))],
            "nut": [("nut_removal", nut_seat, h["nut_height_mm"], tip - nut_seat,
                     h["hex_across_flats_mm"] / math.sqrt(3))]}
        if spacer:
            physical_parts["nut"].append(("spacer_removal", spacer_seat, spacer, tip - spacer_seat, 19.05 / 2))
        for side, parts in physical_parts.items():
            envelopes = {row[0]: row[1:] for row in removal_envelopes(axis, selection, side)}
            assert set(envelopes) == {row[0] for row in parts}
            for operation, seat, thickness, travel, radius in parts:
                start, extent, envelope_radius = envelopes[operation]
                assert envelope_radius >= radius - 1e-9
                for i in range(101):
                    for face in (seat, seat + thickness):
                        coordinate = face + travel * i / 100
                        assert start - 1e-9 <= coordinate <= start + extent + 1e-9


def test_production_query_keeps_foreign_bolts_and_applies_stage_and_stack_exclusions():
    import cadquery as cq

    body = cq.Workplane("XY").box(2, 2, 2).val()
    parts = {"own_shaft": body, "own_spacer": body, "other_shaft": body.translate((1, 0, 0)),
             "panel": body, "remote": body.translate((10, 0, 0))}
    bank = {}
    for name, part in parts.items():
        box = part.BoundingBox()
        bank[name] = {"kind": "panel" if name == "panel" else "bolt",
                      "bounds": [getattr(box, axis + end) for axis in "xyz" for end in ("min", "max")]}
    assembled = envelope_intrusions(body, bank, parts.__getitem__, "own")
    frame = envelope_intrusions(body, bank, parts.__getitem__, "own", stage=True)
    assert assembled["nominal_intrusions"] == ["other_shaft", "panel"]
    assert frame["nominal_intrusions"] == ["other_shaft"]
    assert frame["fine_queries"] == [{"part": "other_shaft", "intersection_mm3": pytest.approx(4)}]
    assert envelope_intrusions(body, bank, parts.__getitem__, "own", stage=True,
                               excluded=["other_shaft"])["reference_envelope_clear"]


def test_selected_setup_retains_below_floor_extents_and_observation_boundary():
    result = selected_setup_requirements([{"bounds_xyz_mm": [0, 1, 0, 1, 10, 20]},
                                          {"bounds_xyz_mm": [0, 1, 0, 1, -93.22173, 0]}])
    assert result["off_floor_setup_required"] is True
    assert result["minimum_additional_reference_floor_clearance_mm"] == pytest.approx(93.22173)
    assert result["actual_temporary_support_verified"] is False
    assert selected_setup_requirements([{"bounds_xyz_mm": [0, 1, 0, 1, 0, 1]}])["off_floor_setup_required"] is False


def test_published_access_rows_expose_selected_pose_floor_requirements():
    packet = Path(__file__).resolve().parents[1] / ("docs/wood-joints-mvp/hypotheses/hl35-candidate/"
        "thin-frame-comparison/eoere-successor-v1/selected-hardware-v1")
    rows = list(csv.DictReader((packet / "access-methods.csv").open()))
    summary = json.loads((packet / "nominal-access.json").read_bytes())
    assert len(rows) == 200
    assert sum(row["off_floor_setup_required"] == "True" for row in rows) == summary["off_floor_setup_required_sides"]
    for row in rows:
        z = float(row["minimum_selected_operation_z_mm"])
        assert (row["off_floor_setup_required"] == "True") == (z < 0)
        assert float(row["minimum_additional_reference_floor_clearance_mm"]) == pytest.approx(max(0, -z))
        assert row["actual_temporary_support_verified"] == "False"
    left_nut = next(row for row in rows if row["axis_id"] == "rail_rear_bolt_left_1" and row["side"] == "nut")
    assert float(left_nut["minimum_selected_operation_z_mm"]) == pytest.approx(-93.22173)
    assert summary["temporary_support_or_reorientation_qualified"] is False


@pytest.mark.parametrize("normal", [(0, 0, 1), (0, 0, -1), (1, 0, 0), (1, 2, 3)])
def test_production_wrenches_contain_transformed_handle_and_full_entry(normal):
    import cadquery as cq

    point, direction = cq.Vector(17, -23, 41), cq.Vector(*normal).normalized()
    thickness, entry = 6, 31
    bodies = wrench_envelopes(point.toTuple(), direction.toTuple(), thickness, entry, 10)
    plane = cq.Plane(origin=point, normal=direction)

    def world(x, y, z):
        return point + plane.xDir * x + plane.yDir * y + direction * z

    for x in (9.526, 161.924):
        for y in (-9.524, 9.524):
            for z in (.001, thickness - .001):
                assert bodies["static_counterhold"].isInside(world(x, y, z), 1e-7)
            for z in (.001, entry + thickness - .001):
                assert bodies["complete_wrench_axial_insertion"].isInside(world(x, y, z), 1e-7)
            for degrees in range(-30, 31):
                a = math.radians(degrees)
                u, v = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
                for z in (.001, thickness - .001):
                    assert bodies["working_handle_60deg"].isInside(world(u, v, z), 1e-7)


def _production_intrusions(body, obstacle):
    box = obstacle.BoundingBox()
    bank = {"foreign_timber": {"kind": "timber",
            "bounds": [getattr(box, axis + end) for axis in "xyz" for end in ("min", "max")]}}
    return envelope_intrusions(body, bank, lambda _: obstacle, "own", stage=True)


def test_production_wrench_sweep_hits_intermediate_rotation_obstacle():
    import cadquery as cq

    bodies = wrench_envelopes((0, 0, 0), (0, 0, 1), 6, 31, 10)
    obstacle = cq.Workplane("XY").box(1, 1, 1).translate((150, 0, 3)).val()
    # Both endpoint handles miss a block reached halfway through the turn.
    for angle in (-30, 30):
        endpoint = bodies["static_counterhold"].rotate((0, 0, 0), (0, 0, 1), angle)
        assert _production_intrusions(endpoint, obstacle)["reference_envelope_clear"]
    result = _production_intrusions(bodies["working_handle_60deg"], obstacle)
    assert result["nominal_intrusions"] == ["foreign_timber"]
    assert result["fine_queries"][0]["intersection_mm3"] == pytest.approx(1)


def test_production_wrench_insertion_hits_obstacle_beyond_seated_handle():
    import cadquery as cq

    bodies = wrench_envelopes((0, 0, 0), (0, 0, 1), 6, 31, 10)
    obstacle = cq.Workplane("XY").box(1, 1, 1).translate((150, 0, 36)).val()
    assert _production_intrusions(bodies["working_handle_60deg"], obstacle)["reference_envelope_clear"]
    result = _production_intrusions(bodies["complete_wrench_axial_insertion"], obstacle)
    assert result["nominal_intrusions"] == ["foreign_timber"]
    assert result["fine_queries"][0]["intersection_mm3"] == pytest.approx(1)


def _receiver_fixture(top=False):
    profile = {"vertices_luv_mm": [[-100, -50, 0], [100, 50, 38.1]],
        "datum_xyz_mm": [10, 20, 30], "basis_grain_u_v_xyz": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "end_planes": [{"outward_normal_l_unitless": sign, "outward_normal_u_unitless": 0,
                        "outward_normal_v_unitless": 0, "plane_offset_from_datum_mm": 100} for sign in (-1, 1)]}
    entry_z = 38.1 if top else 0
    axis = {"id": "fixture", "point_xyz_mm": [10, 20, 30 + entry_z],
            "direction_xyz": [0, 0, -1 if top else 1], "bore_diameter_mm": 11}
    row = {"receiver": "fixture_stock", "entry_in_receiver_l_mm": 0, "entry_in_receiver_u_mm": 0,
           "entry_in_receiver_v_mm": entry_z, "entry_from_axis_point_mm": 0}
    return profile, axis, row


@pytest.mark.parametrize("top", [False, True])
def test_production_finished_face_probe_enters_supported_stock_from_either_side(top):
    import cadquery as cq

    body = cq.Solid.makeBox(200, 100, 38.1, cq.Vector(-90, -30, 30))
    result = receiver_support(*_receiver_fixture(top), body)
    assert result["guide_ring_missing_nominal_wood_mm3_at_0p2_depth"] == pytest.approx(0, abs=1e-8)
    assert result["guide_ring_fully_supported_nominally"]
    pair = result["two_nominal_finished_pad_candidates"]
    assert pair is not None
    assert max(abs(a - b) for a, b in zip(*pair, strict=True)) >= 25.4 - 1e-8
    for x, y in pair:
        assert math.hypot(max(abs(x) - 12.7, 0), max(abs(y) - 12.7, 0)) >= 25.4 - 1e-8
    assert result["actual_land_and_clamp_retention_verified"] is False
    assert result["Actual"] == result["Disposition"] == ""


def test_production_finished_face_probe_rejects_recess_under_guide_ring():
    import cadquery as cq

    body = cq.Solid.makeBox(200, 100, 38.1, cq.Vector(-90, -30, 30))
    recess = cq.Solid.makeBox(10, 10, 1, cq.Vector(18, 15, 30))
    result = receiver_support(*_receiver_fixture(), body.cut(recess))
    assert result["38p1_mm_square_guide_inside_raw_face"]
    assert not result["guide_ring_fully_supported_nominally"]
    assert result["guide_ring_missing_nominal_wood_mm3_at_0p2_depth"] == pytest.approx(20)


@pytest.mark.parametrize("lands, has_pair", [([-50.8], False), ([-50.8, -38.1], False), ([-50.8, 50.8], True)])
def test_production_pad_selection_requires_two_supported_nonoverlapping_lands(lands, has_pair):
    import cadquery as cq

    # The stock is connected below the probe. Its entry face contains a guide
    # island and only these pad lands; raw-stock containment alone cannot pass.
    body = cq.Solid.makeBox(200, 100, 37.1, cq.Vector(-90, -30, 31))
    body = body.fuse(cq.Solid.makeBox(38.1, 38.1, 1, cq.Vector(-9.05, .95, 30)))
    for x in lands:
        body = body.fuse(cq.Solid.makeBox(25.4, 25.4, 1, cq.Vector(10 + x - 12.7, 7.3, 30)))
    result = receiver_support(*_receiver_fixture(), body.clean())
    assert result["guide_ring_fully_supported_nominally"]
    assert all(result["25p4_mm_square_pads_at_plus_minus50p8_grain_inside_raw_face"])
    assert (result["two_nominal_finished_pad_candidates"] is not None) == has_pair
    if has_pair:
        assert result["two_nominal_finished_pad_candidates"] == [(-50.8, 0), (50.8, 0)]
