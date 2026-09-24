"""WJ-05 fixed screw receiver and backing-path audit."""

import json

import pytest

from scripts.wood_joint_wj05_receiver_audit import (
    OUTPUT_JSON,
    OUTPUT_MD,
    build_report,
    render_markdown,
)


@pytest.fixture(scope="module")
def report():
    return build_report()


def test_all_sixty_six_fixed_axes_are_preserved_and_enumerated(report):
    identity = report["fixed_axis_identity"]
    assert identity == {
        "count": 66,
        "unique_count": 66,
        "main_panel_axes": 48,
        "kicker_axes": 18,
        "axes_moved": 0,
    }
    source = json.loads(
        (
            OUTPUT_JSON.parent / "source-inventory.json"
        ).read_text()
    )["fixed_panel_kicker_screws"]
    expected = {
        row["axis_id"]: (
            row["origin_global_xyz_mm"],
            row["axis_global_xyz"],
            row["candidate_finished_receiver_member"],
        )
        for row in source
    }
    actual = {
        row["axis_id"]: (
            row["axis_origin_global_xyz_mm"],
            row["axis_direction_global_xyz"],
            row["candidate_finished_receiver_member"],
        )
        for row in report["axes"]
    }
    assert actual == expected


def test_every_axis_has_finished_receiver_continuity_and_exact_embedment(report):
    assert report["receiver_summary"]["finished_receiver_geometry_pass_count"] == 66
    for row in report["axes"]:
        assert row["uncut_receiver_material_interval_from_axis_origin_mm"] == pytest.approx(
            [18.25625, 63.5]
        )
        assert row["nominal_receiver_embedment_mm"] == pytest.approx(45.24375)
        probe = row["finished_receiver_annular_probe"]
        assert probe["radial_width_outside_occupied_axis_mm"] == 1.0
        assert probe["continuous_nominal_wood"] is True
        assert probe["support_fraction"] == pytest.approx(1.0)
        assert row["physical_receiver_observed"] is None


def test_receiver_groups_distinguish_direct_frame_members_from_center_backers(report):
    summary = report["receiver_summary"]
    assert summary["direct_structural_frame_member_axes"] == 62
    assert summary["separate_center_backer_axes"] == 4
    assert summary["accepted_separate_backer_attachment_axes"] == 0
    assert summary["receiver_axis_counts"]["base_header"] == 10
    assert summary["receiver_axis_counts"]["base_side_left"] == 8
    assert summary["receiver_axis_counts"]["base_side_right"] == 8
    assert summary["receiver_axis_counts"]["inner_kicker_backer_left"] == 2
    assert summary["receiver_axis_counts"]["inner_kicker_backer_right"] == 2
    assert not any(row["whole_frame_replacement_path_complete"] for row in report["axes"])


def test_center_axes_inner_edges_and_provisional_attachment_are_explicit(report):
    center = report["center_receiver_trial"]
    assert set(center["center_axis_ids"]) == {
        "round_kicker_left_center_1",
        "round_kicker_left_center_2",
        "round_kicker_right_center_1",
        "round_kicker_right_center_2",
    }
    assert center["backer_bounds_xyz_mm"] == {
        "left": [-90.4875, -1.5875, -124.9, -36.0, 0.0, 238.9],
        "right": [-1.5875, 87.3125, -124.9, -36.0, 0.0, 238.9],
    }
    assert all(
        row["all_inside_receiver"]
        for row in center["inner_kicker_edge_support"].values()
    )
    bolts = center["provisional_backer_header_attachment_bolts"]
    assert {row["bolt_id"] for row in bolts} == {
        "backer_header_left_1",
        "backer_header_left_2",
        "backer_header_right_1",
        "backer_header_right_2",
    }
    assert all(
        row["bore_fraction_in_backer"] + row["bore_fraction_in_header"]
        == pytest.approx(1.0)
        for row in bolts
    )
    assert center["accepted"] is False


def test_exact_blockers_and_release_boundary_are_preserved(report):
    assert report["status"] == "blocked_center_receiver_path"
    blockers = {row["id"]: row for row in report["blocking_conditions"]}
    assert "right_backer_upper_tool_hits_F1_G1_wire" not in blockers
    assert set(blockers["center_structural_duties_not_implemented"]["legacy_duty_ids"]) == {
        "clip_split_header_center_left",
        "clip_split_header_center_right",
        "clip_split_base_center_left",
        "clip_split_base_center_right",
    }
    assert set(report["physical_observations"].values()) == {None, False}
    assert not any(report["release_flags"].values())


def test_right_backer_tool_clash_is_repaired_without_moving_fixed_axes(report):
    repair = report["resolved_findings"][0]
    assert repair["id"] == "right_backer_upper_tool_hits_F1_G1_wire"
    assert repair["disposition"] == "repaired_nominal_geometry"
    assert repair["fixed_panel_kicker_axes_moved"] == 0
    assert repair["original_station_global_xy_mm"] == [35.0, -63.0]
    assert repair["repaired_station_global_xy_mm"] == [25.0, -76.0]
    assert repair["paired_right_station_global_xy_mm"] == [41.0, -98.0]
    assert repair["original_tool_wire_intersection_volume_mm3"] == pytest.approx(
        140.52882
    )
    assert repair["repaired_tool_wire_intersection_volume_mm3"] == 0.0
    assert repair["repaired_tool_to_wire_clearance_mm"] == pytest.approx(
        1.661248, abs=1e-6
    )
    assert repair["right_pair_spacing"]["center_distance_mm"] == pytest.approx(
        27.202941
    )
    assert repair["right_pair_spacing"]["margin_beyond_4d_mm"] == pytest.approx(
        1.802941
    )
    assert repair["minimum_right_edge_margin_beyond_4d_mm"] == pytest.approx(
        1.1875
    )
    screens = report["center_receiver_trial"]["nominal_collision_screens"]
    assert screens["all_clear"] is True
    assert all(
        not hits
        for group in screens.values()
        if isinstance(group, dict)
        for hits in group.values()
    )


def test_checked_receiver_audit_artifacts_match_generator(report):
    assert json.loads(OUTPUT_JSON.read_text()) == report
    assert OUTPUT_MD.read_text() == render_markdown(report)
