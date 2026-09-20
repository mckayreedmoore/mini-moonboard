"""Bounded PB-01 geometry comparison; no structural approval."""

import json

import cadquery as cq
import pytest

from scripts.simple_rail_joint_comparison import (
    DIAMETER,
    NDS_HOLE_MAX,
    NDS_HOLE_MIN,
    OUTPUT,
    _bolt_report,
    _contact_area,
    _screw_envelope_hits,
    box,
    compare,
)


def test_purchased_screw_intersection_screen_uses_finite_solids():
    screws = {
        "nominal": {"fixed": cq.Solid.makeCylinder(4.5085, 63.5)},
        "margin": {"fixed": cq.Solid.makeCylinder(5.5085, 63.5)},
    }
    near = cq.Solid.makeCylinder(0.3, 2, cq.Vector(5.2, 0, 60))
    beyond_tip = cq.Solid.makeCylinder(1, 2, cq.Vector(0, 0, 64))
    result = _screw_envelope_hits({"near": near, "beyond_tip": beyond_tip}, screws)
    assert result["axis_count"] == 1
    assert result["clashes_mm3"]["nominal"] == {}
    assert result["clashes_mm3"]["margin"]["near"]["fixed"] > 0
    assert "beyond_tip" not in result["clashes_mm3"]["margin"]


def test_comparison_keeps_fixed_panel_axes_and_reports_real_offset():
    report = compare()
    screen = report["purchased_hillman_conditional_screen"]
    assert (
        screen["product"]
        == "Hillman/Fas-n-Tite 42605 #10 x 2-1/2 in exterior wood screw"
    )
    assert screen["axis_count"] == 66
    assert screen["length_mm"] == pytest.approx(63.5)
    assert screen["nominal_head_diameter_mm"] == pytest.approx(9.017)
    assert screen["shaft_max_diameter_verified"] is False
    assert screen["head_tolerance_verified"] is False
    assert screen["installed_seat_datum_verified"] is False
    assert screen["physical_clearance_accepted"] is False
    assert screen["sensitivity_radial_margin_mm"] == pytest.approx(1.0)
    for pose in (
        "overlap",
        "cleat",
        "cleat_grain_n",
        "cleat_grain_n_4x6",
        "cleat_grain_n_4x6_quarter",
        "cleat_grain_n_4x6_group",
    ):
        assert report[pose]["purchased_hillman_screen"]["axis_count"] == 66
        assert set(report[pose]["purchased_hillman_screen"]["clashes_mm3"]) == {
            "nominal_head_diameter_full_length",
            "nominal_plus_1mm_radial_sensitivity",
        }
    nominal_overlap = report["overlap"]["purchased_hillman_screen"]["clashes_mm3"][
        "nominal_head_diameter_full_length"
    ]
    assert nominal_overlap["trial_bore"]["round_panel_lower_right_center_4"] > 0
    assert nominal_overlap["trial_washer_head"]["round_panel_lower_right_center_4"] > 0
    assert (
        report["cleat_grain_n_4x6_group"]["purchased_hillman_screen"]["clashes_mm3"][
            "nominal_plus_1mm_radial_sensitivity"
        ]
        == {}
    )
    assert NDS_HOLE_MIN == pytest.approx(10.31875)
    assert NDS_HOLE_MAX == pytest.approx(11.1125)
    assert NDS_HOLE_MIN <= DIAMETER <= NDS_HOLE_MAX
    assert DIAMETER == pytest.approx(10.5)
    assert report["diagnostic_wood_bore_diameter_mm_not_drill_instruction"] == DIAMETER
    for pose in (
        "overlap",
        "cleat",
        "cleat_grain_n",
        "cleat_grain_n_4x6",
        "cleat_grain_n_4x6_group",
    ):
        for bolts in report[pose]["bolt_groups"].values():
            for bolt in bolts:
                assert (
                    bolt["clearance_diameter_mm_trial_not_shop_instruction"] == DIAMETER
                )
    assert report["station"] == "clip_horizontal_lower_right_1"
    assert report["fixed_panel_axes"] == 66
    assert report["butt_plane_x_mm"] == 89.05
    assert report["overlap"]["offset_mm"] == 139.7
    assert report["overlap"]["extended_end_x_mm"] < 89.05
    assert all(
        item["offset_receiver_intersection_mm3"] == 0
        for item in report["overlap"]["protected_receiver_changes"].values()
    )
    assert report["overlap"]["status"] == "reject_this_pose"
    assert report["overlap"]["nominal_rail_upright_intersection_mm3"] == 0
    assert (
        report["overlap"]["bolt_groups"]["trial_one_bolt_only_not_a_joint_schedule"][0][
            "washer_clashes_mm3"
        ]["head"]["main_lower_right"]
        > 0
    )
    assert report["drilling_released"] is False
    assert report["load_rating_adopted"] is False


def test_cleat_has_separate_crossing_checked_bolt_groups():
    report = compare()
    cleat = report["cleat"]
    assert cleat["size_mm"] == [200, 57.15, 88.9]
    assert cleat["upright_bolt_axis_dot_cleat_grain"] == 1
    assert "parallel to cleat X grain" in cleat["priority_architecture_blocker"]
    assert "12.3.3.4" in cleat["priority_architecture_blocker"]
    assert "not a capacity rejection" in cleat["priority_architecture_blocker"]
    assert cleat["local_tangent_near_far_mm"][0] == cleat["rail_tangent_near_far_mm"][1]
    assert cleat["local_tangent_near_far_mm"][1] - cleat["local_tangent_near_far_mm"][
        0
    ] == pytest.approx(57.15)
    assert cleat["upright_bolt_tangent_from_cleat_near_mm"] == pytest.approx(28.575)
    assert cleat["nominal_center_to_tangent_edge_mm"] == pytest.approx(28.575)
    assert cleat["edge_distance_structurally_qualified"] is False
    assert cleat["bolt_groups"]["upright"][0]["start_xyz_mm"]
    assert cleat["bolt_groups"]["upright"]
    assert cleat["bolt_groups"]["rail"]
    assert all(cleat["bolt_groups"]["upright"][0]["full_bore_containment"].values())
    assert all(cleat["bolt_groups"]["rail"][0]["full_bore_containment"].values())
    assert cleat["orthogonal_axis_dot"] == 0
    assert cleat["bolt_intersections_mm3"] == 0
    assert cleat["protected_screw_axis_clashes_mm3"] == {}
    assert cleat["protected_axis_hardware_clashes_mm3"]["upright_bore"] == {}
    assert cleat["protected_axis_hardware_clashes_mm3"]["rail_bore"] == {}
    for item in (
        "upright_washers",
        "rail_washers",
        "upright_tools",
        "rail_tools",
    ):
        assert all(
            hits == {}
            for hits in cleat["protected_axis_hardware_clashes_mm3"][item].values()
        )
    assert cleat["cleat_host_clashes_mm3"] == {}
    assert cleat["cleat_parent_clashes_mm3"] == {}
    assert cleat["cleat_panel_clashes_mm3"] == {}
    assert cleat["bolt_groups"]["upright"][0]["parent_bore_clashes_mm3"] == {}
    assert cleat["bolt_groups"]["rail"][0]["parent_bore_clashes_mm3"] == {}
    assert all(
        not clash
        for bolt in (
            cleat["bolt_groups"]["upright"][0],
            cleat["bolt_groups"]["rail"][0],
        )
        for clash in bolt["washer_clashes_mm3"].values()
    )
    assert cleat["cleat_to_upper_rail_tangent_gap_mm"] == pytest.approx(48.8)
    assert cleat["rail_nut_tool_tangent_clearance_mm"] == pytest.approx(6.3)
    assert all(
        not hits
        for group in cleat["tool_clashes_mm3"].values()
        for hits in group.values()
    )
    assert cleat["status"] == "diagnostic_pose_only"
    assert cleat["installed_access_verified"] is False
    assert cleat["actual_head_nut_socket_stack_verified"] is False
    assert cleat["remaining_open_checks"]
    assert json.loads(OUTPUT.read_text()) == report


def test_grain_n_cleat_is_separately_screened_without_promoting_prior_poses():
    report = compare()
    trial = report["cleat_grain_n"]
    assert report["overlap"]["status"] == "reject_this_pose"
    assert report["cleat"]["priority_architecture_blocker"]
    assert trial["size_local_x_t_n_mm"] == [88.9, 57.15, 200]
    assert trial["grain_direction_xyz"] == pytest.approx([0, -0.766044, 0.642788])
    assert trial["bolt_axis_dot_cleat_grain"] == {"upright": 0, "rail": 0}
    assert trial["fixed_panel_axes_checked"] == 66
    assert all(trial["bolt_groups"]["upright"][0]["full_bore_containment"].values())
    assert all(trial["bolt_groups"]["rail"][0]["full_bore_containment"].values())
    assert trial["edge_distance_structurally_qualified"] is False
    assert trial["rail_first_bolt_end_distance_mm"] == pytest.approx(44.45)
    assert trial["nominal_7d_mm"] == pytest.approx(66.675)
    assert trial["rail_end_distance_shortfall_if_7d_applies_mm"] == pytest.approx(
        22.225
    )
    assert trial["trial_bolt_n_center_separation_mm"] == pytest.approx(55)
    assert trial["actual_local_bounds_mm"]["x"] == pytest.approx([89.05, 177.95])
    assert trial["actual_local_bounds_mm"]["t"] == pytest.approx([1353.874, 1411.024])
    assert trial["actual_local_bounds_mm"]["n"] == pytest.approx([209.841, 409.841])
    assert trial["cleat_host_clashes_mm3"] == {}
    assert trial["cleat_parent_clashes_mm3"] == {}
    assert trial["cleat_panel_clashes_mm3"] == {}
    assert trial["bolt_intersections_mm3"] == 0
    assert all(
        hits == {} for hits in trial["protected_axis_envelope_clashes_mm3"].values()
    )
    for family in ("upright", "rail"):
        bolt = trial["bolt_groups"][family][0]
        assert bolt["full_bore_tolerance_mm3"] == 1
        assert all(volume <= 1 for volume in bolt["missing_wood_bore_mm3"].values())
        assert bolt["parent_bore_clashes_mm3"] == {}
        assert all(not hits for hits in bolt["washer_clashes_mm3"].values())
        assert all(not hits for hits in bolt["tool_clashes_mm3"].values())
    assert trial["rail_nut_tool_tangent_clearance_mm"] == pytest.approx(6.3)
    assert trial["face_contact_perturbation_mm"] == pytest.approx(0.1)
    assert trial["face_contact_geometry_verified"] == {
        "rail_to_cleat": True,
        "upright_to_cleat": True,
    }
    assert trial["washer_faces_geometry_verified"] is True
    assert all(gap <= 0.01 for gap in trial["washer_wood_face_gap_mm"].values())
    for face, nominal in trial["nominal_face_contact_area_mm2"].items():
        assert trial["measured_face_contact_area_mm2"][face] == pytest.approx(
            nominal, abs=1
        )
    assert trial["status"] == "diagnostic_pose_only"
    assert trial["installed_access_verified"] is False
    assert trial["actual_head_nut_socket_stack_verified"] is False
    assert (
        "diagnostic clearance envelopes only" in trial["tool_clearance_interpretation"]
    )
    assert trial["trial_stack_count_not_selected"] == 2
    assert trial["installed_cost_usd"] is None
    assert trial["real_stock_and_cost_caveats"]
    assert trial["remaining_open_checks"]
    assert trial["load_rating_adopted"] is False
    assert trial["drilling_released"] is False


def test_full_bore_rejects_more_than_one_cubic_mm_missing_wood():
    trial, _, washers, _ = _bolt_report(
        "incomplete_test_bore",
        (0, 0, 0),
        (1, 0, 0),
        10,
        {"host": box(0, -20, -20, 9, 40, 40)},
        {"host": 10},
        {},
    )
    assert trial["missing_wood_bore_mm3"]["host"] > 1
    assert trial["full_bore_containment"]["host"] is False
    assert trial["washer_wood_face_xyz_mm"] == {
        "head": [2.5, 0.0, 0.0],
        "nut": [7.5, 0.0, 0.0],
    }
    assert washers["head"].BoundingBox().xmin == pytest.approx(0)
    assert washers["head"].BoundingBox().xmax == pytest.approx(2.5)
    assert washers["nut"].BoundingBox().xmin == pytest.approx(7.5)
    assert washers["nut"].BoundingBox().xmax == pytest.approx(10)
    assert trial["actual_head_nut_socket_stack_verified"] is False


def test_contact_measurement_rejects_separated_faces():
    host = box(0, 0, 0, 1, 2, 3)
    touching = box(1, 0, 0, 1, 2, 3)
    separated = box(1.2, 0, 0, 1, 2, 3)
    assert _contact_area(touching, host, (-1, 0, 0)) == pytest.approx(6)
    assert _contact_area(separated, host, (-1, 0, 0)) == 0


def test_grain_n_4x6_trial_uses_same_screen_and_corrected_rail_station():
    report = compare()
    old = report["cleat_grain_n"]
    trial = report["cleat_grain_n_4x6"]
    assert old["size_local_x_t_n_mm"] == [88.9, 57.15, 200]
    assert old["rail_first_bolt_end_distance_mm"] == pytest.approx(44.45)
    assert trial["size_local_x_t_n_mm"] == [139.7, 57.15, 200]
    assert trial["rail_first_bolt_end_distance_mm"] == pytest.approx(70)
    assert trial["rail_first_bolt_end_distance_mm"] >= trial["nominal_7d_mm"]
    assert trial["rail_end_distance_shortfall_if_7d_applies_mm"] == 0
    assert trial["bolt_groups"]["upright"][0]["grip_mm"] == pytest.approx(182.8)
    assert trial["retail_dimensional_comparator"]["model"] == "637637"
    assert trial["retail_dimensional_comparator"]["listed_actual_cross_section_mm"] == [
        90.4748,
        142.875,
    ]
    assert (
        trial["retail_dimensional_comparator"][
            "local_availability_price_delivered_size_verified"
        ]
        is False
    )
    assert trial["fixed_panel_axes_checked"] == 66
    assert all(trial["face_contact_geometry_verified"].values())
    assert trial["washer_faces_geometry_verified"] is True
    assert all(
        hits == {} for hits in trial["protected_axis_envelope_clashes_mm3"].values()
    )
    for family in ("upright", "rail"):
        bolt = trial["bolt_groups"][family][0]
        assert all(bolt["full_bore_containment"].values())
        assert bolt["parent_bore_clashes_mm3"] == {}
        assert all(not hits for hits in bolt["washer_clashes_mm3"].values())
        assert all(not hits for hits in bolt["tool_clashes_mm3"].values())
    assert trial["cleat_parent_clashes_mm3"] == {}
    assert trial["cleat_panel_clashes_mm3"] == {}
    assert trial["bolt_intersections_mm3"] == 0
    assert trial["status"] == "diagnostic_pose_only"
    assert trial["installed_access_verified"] is False
    assert trial["actual_head_nut_socket_stack_verified"] is False
    assert trial["load_rating_adopted"] is False
    assert trial["drilling_released"] is False


def test_grain_n_4x6_quarter_pose_is_conditional_and_keeps_all_axes_clear():
    report = compare()
    legacy = report["cleat_grain_n_4x6"]
    trial = report["cleat_grain_n_4x6_quarter"]
    assert legacy["nominal_trial_bolt_diameter_mm_not_selected"] == pytest.approx(9.525)
    assert legacy[
        "diagnostic_wood_bore_diameter_mm_not_drill_instruction"
    ] == pytest.approx(10.5)
    assert legacy["conditional_4d_mm"] == pytest.approx(38.1)
    assert legacy["conditional_7d_mm"] == pytest.approx(66.675)
    assert trial["size_local_x_t_n_mm"] == legacy["size_local_x_t_n_mm"]
    assert trial["nominal_trial_bolt_diameter_mm_not_selected"] == pytest.approx(6.35)
    assert trial[
        "diagnostic_wood_bore_diameter_mm_not_drill_instruction"
    ] == pytest.approx(7.5)
    assert trial["nds_2024_nominal_hole_interval_mm"] == pytest.approx(
        [7.14375, 7.9375]
    )
    assert trial["conditional_4d_mm"] == pytest.approx(25.4)
    assert trial["conditional_7d_mm"] == pytest.approx(44.45)
    edges = trial["center_to_edges_mm"]
    assert edges["upright_bolt_in_cleat_t"] == pytest.approx([28.575, 28.575])
    assert edges["upright_bolt_in_cleat_n"] == pytest.approx([50.159, 149.841])
    assert edges["rail_bolt_in_cleat_n"] == pytest.approx([105.159, 94.841])
    assert edges["rail_bolt_in_host_n"] == pytest.approx([105.159, 34.541])
    assert trial["fixed_panel_axes_checked"] == 66
    assert trial["purchased_hillman_screen"]["axis_count"] == 66
    assert trial["purchased_hillman_screen"]["clashes_mm3"] == {
        "nominal_head_diameter_full_length": {},
        "nominal_plus_1mm_radial_sensitivity": {},
    }
    assert all(
        not hits for hits in trial["protected_axis_envelope_clashes_mm3"].values()
    )
    assert trial["cleat_host_clashes_mm3"] == {}
    assert trial["cleat_parent_clashes_mm3"] == {}
    assert trial["cleat_panel_clashes_mm3"] == {}
    assert trial["bolt_intersections_mm3"] == 0
    assert trial["rail_nut_tool_tangent_clearance_mm"] == pytest.approx(6.3)
    assert trial["washer_faces_geometry_verified"] is True
    assert all(trial["face_contact_geometry_verified"].values())
    for family in ("upright", "rail"):
        bolt = trial["bolt_groups"][family][0]
        assert bolt[
            "clearance_diameter_mm_trial_not_shop_instruction"
        ] == pytest.approx(7.5)
        assert all(bolt["full_bore_containment"].values())
        assert bolt["parent_bore_clashes_mm3"] == {}
        assert all(not hits for hits in bolt["washer_clashes_mm3"].values())
        assert all(not hits for hits in bolt["tool_clashes_mm3"].values())
    assert trial["status"] == "diagnostic_pose_only"
    assert trial["installed_access_verified"] is False
    assert trial["load_rating_adopted"] is False
    assert trial["drilling_released"] is False


def test_grain_n_4x6_two_bolt_groups_record_initial_clash_and_one_adjustment():
    report = compare()
    group = report["cleat_grain_n_4x6_group"]
    assert report["cleat_grain_n_4x6"]["status"] == "diagnostic_pose_only"
    assert group["initial_front_probe"]["n_front_mm"] == 160
    assert group["initial_front_probe"]["panel_clashes_mm3"]["main_lower_right"] > 0
    assert group["adjusted_front_n_mm"] == pytest.approx(209.841)
    assert group["adjustment_count"] == 1
    assert group["size_local_x_t_n_mm"] == [139.7, 57.15, 300]
    assert group["upright_bolt_n_centers_mm"] == [265, 310]
    assert group["rail_bolt_x_from_butt_mm"] == [70, 110]
    assert group["rail_bolt_n_centers_mm"] == [290, 290]
    assert len(group["bolt_groups"]["upright"]) == 2
    assert len(group["bolt_groups"]["rail"]) == 2
    assert group["fixed_panel_axes_checked"] == 66
    assert group["edge_end_spacing_structurally_qualified"] is False
    assert group["installed_access_verified"] is False
    assert group["load_rating_adopted"] is False
    assert group["drilling_released"] is False
    assert group["pairwise_envelope_intersections_mm3"] is not None
    assert group["pairwise_bolt_pair_count"] == 6
    assert group["pairwise_envelope_comparisons_per_pair"] == 25
    assert all(
        hits == {} for hits in group["pairwise_envelope_intersections_mm3"].values()
    )
    assert group["cleat_host_clashes_mm3"] == {}
    assert group["cleat_parent_clashes_mm3"] == {}
    assert group["cleat_panel_clashes_mm3"] == {}
    assert all(group["face_contact_geometry_verified"].values())
    assert all(
        hits == {}
        for envelope in group["protected_axis_envelope_clashes_mm3"].values()
        for hits in (envelope.values() if "bore" in envelope else [envelope])
    )
    assert all(
        gap <= 0.01
        for faces in group["washer_wood_face_gap_mm"].values()
        for gap in faces.values()
    )
    for family in ("upright", "rail"):
        for bolt in group["bolt_groups"][family]:
            assert all(bolt["full_bore_containment"].values())
            assert bolt["parent_bore_clashes_mm3"] == {}
            assert all(not hits for hits in bolt["washer_clashes_mm3"].values())
            assert all(not hits for hits in bolt["tool_clashes_mm3"].values())
    tradeoff = group["conditional_upright_n_feasibility"]
    assert tradeoff["available_pitch_if_all_apply_mm"] == pytest.approx(34.925)
    assert tradeoff["hypothetical_required_in_row_pitch_4d_mm"] == pytest.approx(38.1)
    assert tradeoff["pitch_shortfall_if_all_apply_mm"] == pytest.approx(3.175)
    assert tradeoff["actual_cleat_front_end_of_first_upright_bolt_mm"] == pytest.approx(
        55.159
    )
    assert group["center_to_edges_and_spacing_mm"]["rail_in_cleat_x"][1][
        1
    ] == pytest.approx(29.7)
    assert group["trial_envelope_grips_mm_not_purchased_lengths"] == {
        "u1": pytest.approx(182.8),
        "u2": pytest.approx(182.8),
        "r1": pytest.approx(100.25),
        "r2": pytest.approx(100.25),
    }
    assert group["trial_stack_count_not_selected"] == 4
    assert group["installed_cost_usd"] is None
    assert group["status"] == "diagnostic_pose_only"
    assert group["remaining_open_checks"]
