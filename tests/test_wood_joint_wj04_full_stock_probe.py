"""Lightweight guards for the separate full-stock WJ-04 hypothesis."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_full_stock_probe as probe


def test_four_provisional_stacks_use_candidate_datums_and_127mm_grips():
    canonical_sha256 = WJ04_TRIAL.canonical_sha256
    stacks = probe.build_stacks()

    assert tuple(stacks) == ("rail_1", "rail_2", "upright_1", "upright_2")
    assert all(stack.grip_mm == pytest.approx(127.0) for stack in stacks.values())
    assert all(
        stack.hardware.candidate_sku == "25C600HCS5Z" for stack in stacks.values()
    )
    assert stacks["rail_1"].head_seat.center.toTuple() == pytest.approx(
        WJ04_TRIAL.frame.to_global((134.5, 1442.774134, 273.190968))
    )
    assert stacks["rail_1"].direction.toTuple() == pytest.approx(
        WJ04_TRIAL.frame.vector_to_global((0.0, -1.0, 0.0))
    )
    assert stacks["upright_2"].head_seat.center.toTuple() == pytest.approx(
        WJ04_TRIAL.frame.to_global((177.95, 1414.874134, 289.690968))
    )
    assert WJ04_TRIAL.canonical_sha256 == canonical_sha256
    assert WJ04_TRIAL.cleat.size_x_t_n_mm == (95.25, 38.1, 119.7)


def test_conditional_placement_screen_records_only_margins_not_acceptance():
    result = probe.trial_plan()
    placement = result["conditional_placement_screen"]

    assert placement["conditional_4d_mm"] == pytest.approx(25.4)
    assert placement["conditional_5d_mm"] == pytest.approx(31.75)
    assert placement["conditional_7d_mm"] == pytest.approx(44.45)
    assert placement["rail_group"][
        "first_center_minus_conditional_7d_mm"
    ] == pytest.approx(1.0)
    assert placement["rail_group"][
        "cleat_grain_n_end_distance_each_mm"
    ] == pytest.approx(43.35)
    assert placement["rail_group"][
        "conditional_c_delta_if_7d_tension_end_rule_applies"
    ] == pytest.approx(0.975253)
    assert placement["principal_group"]["cleat_t_edge_distances_mm"] == pytest.approx(
        [28.0, 27.9]
    )
    assert placement["principal_group"][
        "minimum_t_edge_minus_conditional_4d_mm"
    ] == pytest.approx(2.5)
    assert placement["rail_group"]["signed_loading_classified"] is False
    assert placement["principal_group"]["signed_loading_classified"] is False


def test_stack_screen_preserves_thread_and_hardware_uncertainty():
    result = probe.trial_plan()
    screen = result["fastener_stack_dimensional_screen"]

    assert screen["candidate_minimum_length_mm"] == pytest.approx(149.86)
    assert screen["minimum_delivered_tip_projection_mm"] == pytest.approx(12.0556)
    assert screen["projection_remaining_after_receiving_reserve_mm"] == pytest.approx(
        9.5156
    )
    assert screen["earliest_nut_bearing_face_from_underhead_mm"] == pytest.approx(
        128.5908
    )
    assert screen["catalog_Lb_min_last_thread_scratch_mm"] == pytest.approx(127.0)
    assert screen["catalog_Lg_max_ring_gage_inspection_plane_mm"] == pytest.approx(
        133.35
    )
    assert screen["Lg_max_minus_earliest_nut_face_mm"] == pytest.approx(4.7592)
    assert screen["actual_full_thread_transition_window_mm"].startswith("unresolved")
    assert (
        screen["delivered_body_end_thread_start_and_functional_nut_engagement_verified"]
        is False
    )


def test_builder_fails_closed_on_missing_duplicate_or_altered_stack():
    specs = probe.STACK_SPECS

    with pytest.raises(ValueError, match="four unique stacks"):
        probe.build_stacks((specs[0], specs[1], specs[2], specs[2]))
    missing_principal = replace(
        specs[2],
        interface_id="rail_to_cleat",
        layers=(
            ("wj04_cleat", 88.9),
            ("base_rail_service_lower_right", 38.1),
        ),
    )
    with pytest.raises(ValueError, match="two rail stacks"):
        probe.build_stacks((specs[0], specs[1], missing_principal, specs[3]))
    altered = replace(
        specs[0],
        layers=(("wj04_cleat", 88.9), ("base_rail_service_lower_right", 39.1)),
    )
    with pytest.raises(ValueError, match="layer order or dimensions changed"):
        probe.build_stacks((altered, *specs[1:]))


def test_hypothesis_keeps_all_release_and_acceptance_claims_false():
    result = probe.trial_plan()
    claims = result["claim_boundary"]

    assert result["status"] == "unaccepted_geometry_hypothesis"
    assert claims["accepted_replacement_count"] == 0
    assert claims["physical_replacement_accepted"] is False
    assert claims["structural_accepted"] is False
    assert claims["purchase_approved"] is False
    assert claims["drilling_released"] is False
    assert claims["fabrication_released"] is False
    assert claims["capacity_established"] is False
