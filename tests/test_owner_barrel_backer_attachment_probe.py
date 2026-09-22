"""Detached geometry-only backer attachment trial on the current viewer pose."""

import pytest

from scripts.owner_barrel_backer_attachment_probe import probe


@pytest.fixture(scope="module")
def result():
    return probe()


def test_source_pose_and_fixed_inventory_are_bound(result):
    assert result["schema"] == "owner_barrel_backer_attachment_probe/v1"
    assert result["viewer_pose"]["outer_header_forward_y_mm"] == -85.0
    assert result["fixed_inventory_counts"] == {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
    }
    assert set(result["backers"]) == {
        "inner_kicker_backer_left",
        "inner_kicker_backer_right",
    }
    assert len(result["candidates"]) == 4


def test_two_diagonal_nominal_pairs_per_backer_clear_finite_screen(result):
    assert {name: row["point_xy_mm"] for name, row in result["candidates"].items()} == {
        "inner_kicker_backer_left/rear": [-35.0, -100.0],
        "inner_kicker_backer_left/front": [-20.0, -65.0],
        "inner_kicker_backer_right/rear": [20.0, -100.0],
        "inner_kicker_backer_right/front": [35.0, -65.0],
    }
    assert result["candidate_hardware"]["per_backer_bolt_barrel_pairs"] == 2
    assert result["candidate_hardware"]["trial_nominal_bolt_length_mm"] == 88.9
    assert result["mutual_candidate_hits_mm3"] == {}
    assert result["nonempty_existing_obstacles"] == {}
    assert result["finite_clearance_screen_passed"] is True
    for row in result["candidates"].values():
        assert row["seat_to_assumed_axis_mm"] == pytest.approx(77.0)
        assert row["nominal_shaft_reach_past_axis_mm"] == pytest.approx(9.9)
        assert row["nominal_tip_to_backer_bottom_mm"] == pytest.approx(190.1)
        assert row["nominal_tip_z_mm"] == pytest.approx(190.1)
        assert row["modeled_barrel_far_wall_z_mm"] == pytest.approx(194.9962)
        assert row["nominal_tip_past_modeled_barrel_far_wall_mm"] == pytest.approx(
            4.8962
        )
        assert row["modeled_bore_end_z_mm"] == pytest.approx(186.1)
        assert row["modeled_bore_depth_past_nominal_tip_mm"] == pytest.approx(4.0)
        assert row["machine_bore_depth_from_header_top_mm"] == pytest.approx(90.9)
        assert row["nominal_margin_to_backer_x_edges_mm"] > 18
        assert row["nominal_margin_to_backer_y_edges_mm"] > 20
        assert row["barrel_body_inside_backer_mm3"] == pytest.approx(
            row["barrel_body_mm3"], abs=0.01
        )
        assert row["cross_bore_meets_machine_bore_mm3"] > 0
        assert row["intended_header_bore_mm3"] > 0
        assert row["intended_backer_bore_mm3"] > 0
        assert all(not any(families.values()) for families in row["screen"].values())


def test_all_non_geometry_gates_remain_closed(result):
    assert result["status"] == "detached_geometry_screen_only"
    for key in (
        "retail_fit_verified",
        "thread_engagement_verified",
        "head_tool_fit_verified",
        "structural_capacity_verified",
        "complete_assembly_sequence_verified",
        "drilling_released",
        "fabrication_released",
    ):
        assert result[key] is False


def test_three_inch_bolt_with_raised_barrel_is_nominally_contained():
    trial = probe(nominal_bolt_length_mm=76.2, barrel_axis_z_mm=205.0)
    assert trial["candidate_hardware"]["trial_nominal_bolt_length_mm"] == 76.2
    assert trial["candidate_hardware"]["trial_barrel_axis_z_mm"] == 205.0
    assert trial["finite_clearance_screen_passed"] is True
    assert trial["mutual_candidate_hits_mm3"] == {}
    assert trial["nonempty_existing_obstacles"] == {}
    for row in trial["candidates"].values():
        assert row["nominal_shaft_reach_past_axis_mm"] == pytest.approx(2.2)
        assert row["nominal_tip_past_modeled_barrel_far_wall_mm"] == pytest.approx(
            -2.8038
        )
        assert row["modeled_bore_depth_past_nominal_tip_mm"] == pytest.approx(4.0)
    assert trial["thread_engagement_verified"] is False
    assert trial["drilling_released"] is False
