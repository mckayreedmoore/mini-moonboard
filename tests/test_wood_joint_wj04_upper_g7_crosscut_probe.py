"""Pure source-bound tests for the revised upper G7 crosscut hypothesis."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_upper_g7_crosscut_probe as probe


def test_plan_keeps_new_hypothesis_separate_and_unaccepted():
    canonical_sha = WJ04_TRIAL.canonical_sha256
    plan = probe.trial_plan()

    assert plan["trial_id"] == probe.TRIAL_ID
    assert plan["predecessor_hypothesis"]["report_sha256"] == (
        probe.PRIOR_FAILED_REPORT_SHA256
    )
    assert plan["pair_spacing"]["nominal_clear_gap_mm"] == pytest.approx(55.15)
    assert plan["claim_boundary"]["former_duty_count"] == 2
    assert plan["claim_boundary"]["former_sds_axis_count"] == 12
    assert plan["claim_boundary"]["accepted_replacement_count"] == 0
    assert plan["fixed_obligations"]["panel_kicker_screw_axes"] == 66
    assert plan["fixed_obligations"]["starting_frame_bolts"] == 12
    assert plan["fixed_obligations"]["cad_environment_materialized"] is False
    assert plan["claim_boundary"]["physical_replacement_accepted"] is False
    assert plan["claim_boundary"]["structural_accepted"] is False
    assert plan["claim_boundary"]["drilling_released"] is False
    assert plan["claim_boundary"]["fabrication_released"] is False
    assert WJ04_TRIAL.canonical_sha256 == canonical_sha


def test_g7_projection_reserve_and_full_section_crosscut_are_explicit():
    plan = probe.trial_plan()
    upper = plan["stations"][probe.UPPER_STATION]

    assert upper["g7_projection"]["datum_id"] == "hold_tnut_main_G7"
    assert upper["g7_projection"]["bounds_x_t_n_mm"]["X"] == pytest.approx(
        [175.24375, 186.35625]
    )
    assert upper["g7_projection"]["bounds_x_t_n_mm"]["T"] == pytest.approx(
        [1514.267884, 1525.380384]
    )
    assert upper["g7_projection"]["bounds_x_t_n_mm"]["N"] == pytest.approx(
        [209.840968, 260.640968]
    )
    assert upper["cleat_origin_x_t_n_mm"] == pytest.approx(
        [89.05, 1497.924134, 262.640968]
    )
    assert upper["cleat_size_x_t_n_mm"] == pytest.approx([88.9, 88.9, 86.9])
    assert upper["g7_clearance_reserve_mm"] == pytest.approx(2.0)
    assert "tolerances are not included" in upper["g7_clearance_basis"]
    assert upper["cleat_origin_x_t_n_mm"][2] + upper["cleat_size_x_t_n_mm"][
        2
    ] == pytest.approx(WJ04_TRIAL.source_bounds.rail_n_max_mm)


def test_upper_rail_stack_reversal_uses_revised_axes_layers_and_seats():
    plan = probe.trial_plan()
    upper_rails = [
        stack for stack in plan["stacks"] if stack["stack_id"].startswith("upper_rail")
    ]

    assert [row["axis_point_basis_mm"] for row in upper_rails] == [
        [134.5, 1459.824134, 289.590968],
        [134.5, 1459.824134, 322.590968],
    ]
    assert all(row["axis_direction_basis"] == [0.0, 1.0, 0.0] for row in upper_rails)
    assert all(
        [layer["member_id"] for layer in row["layers_head_to_nut"]]
        == [probe.UPPER_RAIL, probe.UPPER_CLEAT]
        for row in upper_rails
    )
    reversal = plan["upper_rail_reversal"]
    assert reversal["wood_face_gap_to_lower_cleat_mm"] == pytest.approx(17.05)
    assert reversal["max_head_plus_washer_depth_per_side_mm"] == pytest.approx(6.1722)
    assert reversal["opposing_head_envelope_gap_mm"] == pytest.approx(4.7056)
    assert reversal["installed_axial_overlap_removed_by_reversal"] is True
    assert reversal["tool_access_status"].startswith("unresolved")


def test_conditional_end_distance_washer_and_contact_screens_stay_unaccepted():
    plan = probe.trial_plan()
    upper = plan["stations"][probe.UPPER_STATION]
    assert upper["rail_row_end_distances_mm"] == pytest.approx([26.95, 26.95])
    assert upper["rail_row_pitch_mm"] == pytest.approx(33.0)
    assert upper["rail_minimum_3p5d_mm"] == pytest.approx(22.225)
    assert upper["rail_full_factor_7d_mm"] == pytest.approx(44.45)
    assert upper["rail_end_distance_ratio_to_7d"] == pytest.approx(0.606299213)
    assert upper["critical_rail_washer_support_margin_mm"] == pytest.approx(17.4377)
    assert upper["contact_area_screen"]["crosscut_length_mm2"] == pytest.approx(7725.41)
    assert upper["contact_area_screen"]["geometry_status"].startswith("analytic")
    assert upper["signed_demand_and_capacity_status"].startswith("unresolved")
    assert all(
        stack["thread_transition_status"].startswith("unresolved")
        for stack in plan["stacks"]
    )


def test_stack_builder_rejects_duplicate_missing_and_altered_assignment():
    specs = probe.STACK_SPECS
    with pytest.raises(ValueError, match="eight unique stack assignments"):
        probe.build_stacks((*specs[:-1], specs[0]))
    with pytest.raises(ValueError, match="eight unique stack assignments"):
        probe.build_stacks(specs[:-1])

    altered = replace(
        specs[-1],
        axis_point_basis_mm=(
            specs[-1].axis_point_basis_mm[0],
            specs[-1].axis_point_basis_mm[1],
            specs[-1].axis_point_basis_mm[2] + 1.0,
        ),
    )
    with pytest.raises(ValueError, match="differs from named hypothesis axes"):
        probe.build_stacks((*specs[:-1], altered))
