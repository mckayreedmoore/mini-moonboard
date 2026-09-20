"""Common-core HL33 screen must reject blocked access without false wood overlaps."""

import json

import pytest

from scripts.hardware_first_hl33_common_core import OUTPUT, screen_common_core


@pytest.fixture(scope="module")
def result():
    return screen_common_core()


def test_two_bounded_integrated_trials(result):
    assert [t["parameter_core_rear_extension_mm"] for t in result["trials"]] == [45, 65]
    assert result["fixed_panel_solid_count"] == 6
    assert result["fixed_panel_screw_axis_count"] == 66
    assert result["fixed_frame_axis_count"] == 12
    assert len(result["fundamental_integration_gaps"]) == 3
    for trial in result["trials"]:
        assert trial["bore_count"] == trial["bolt_path_count"] == 9
        assert trial["stack_envelope_count"] == 54
        assert trial["protected_receiver_loss_mm3"] == {}
        assert trial["existing_frame_axis_receivers_changed"] == []
        assert len(trial["kicker_center_backing_mm3"]) == 4
        assert all(v > 0 for v in trial["kicker_center_backing_mm3"].values())


def test_core_and_backings_are_disjoint_solids_with_real_bracket_paths(result):
    for trial in result["trials"]:
        assert trial["core_backing_intersection_mm3"] == {"left": 0, "right": 0}
        assert trial["checks_mm3"]["wood_pairs"] == {}
        rear = trial["core_rear_block_bounds_mm"]
        tongue = trial["core_front_tongue_bounds_mm"]
        assert rear[3] == tongue[2]
        assert tongue[0] == -25.4 and tongue[1] == 25.4
        for name in ("backing_left_core", "backing_right_core", "backing_shared"):
            assert trial["intended_plate_path_mm3"][name] > 0
            assert trial["bore_missing_wood_mm3"][name] == 0
        assert trial["intended_plate_path_mm3"]["backing_shared_right_leg"] > 0


def test_access_rejection_and_report_are_explicit(result):
    assert result["rating_or_drilling_released"] is False
    for trial in result["trials"]:
        assert trial["status"] == "rejected_nominal_pose"
        assert (
            "catalog_inapplicable_backing_connection"
            in trial["fundamental_for_this_pose"]
        )
        assert trial["backing_connection_catalog_applicable"] is False
        assert trial["catalog_minimum_wood_shortfall_mm"] == {
            "backing_shared_core_tongue": 38.1
        }
        assert (
            trial["bolted_wood_section_thickness_mm"]["backing_shared_core_tongue"]
            == 50.8
        )
        assert all(
            thickness >= result["factory_nominal_mm"]["minimum_bolted_wood"]
            for name, thickness in trial["bolted_wood_section_thickness_mm"].items()
            if name != "backing_shared_core_tongue"
        )
        assert "stack_changed_wood" in trial["repairable_geometry_or_detail"]
        assert "lower_core_nut_tool" in trial["checks_mm3"]["stack_changed_wood"]
        assert "different_axis_tool_pairs" in trial["repairable_geometry_or_detail"]
        assert trial["checks_mm3"]["plate_panel"] == {}
        assert trial["checks_mm3"]["fixed_screw_hardware"] == {}
    assert json.loads(OUTPUT.read_text()) == result


def test_shape_bound_does_not_claim_catalog_applicability(result):
    bound = result["shape_only_minimum_revision_mm"]
    assert bound["minimum_total_core_width"] == 266.7
    assert bound["increase_over_current_core_width"] == 26.7
    assert bound["minimum_rail_end_abs_x_for_side_plate"] == 137.9
    assert "untested" in result["minimum_connection_revision"]
    assert (
        result["direct_independent_bolt_split"]["inner_wing_to_tongue_face_gap_mm"] == 0
    )
    assert result["direct_independent_bolt_split"]["cad_trial_run"] is False
