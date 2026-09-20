"""Bounded PB-01 geometry comparison; no structural approval."""

import json

import pytest

from scripts.simple_rail_joint_comparison import OUTPUT, compare


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
    assert cleat["status"] == "geometry_only_candidate"
    assert cleat["remaining_open_checks"]
    assert json.loads(OUTPUT.read_text()) == report
