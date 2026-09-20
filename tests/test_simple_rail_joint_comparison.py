"""Bounded PB-01 geometry comparison; no structural approval."""

import json

import pytest

from scripts.simple_rail_joint_comparison import (
    OUTPUT,
    _bolt_report,
    _contact_area,
    box,
    compare,
)


def test_comparison_keeps_fixed_panel_axes_and_reports_real_offset():
    report = compare()
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
    assert "parallel to the cleat X grain" in cleat["priority_architecture_blocker"]
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
