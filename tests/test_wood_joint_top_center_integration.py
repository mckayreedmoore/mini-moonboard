import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import wood_joint_top_center_integration as top_center
from scripts import wood_joint_wj18_compositor as wj18

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = json.loads((ROOT / top_center.INVENTORY_PATH).read_text())


def test_top_center_inventory_contract_binds_exact_duties_hosts_and_old_axes():
    duties = top_center._duty_rows(INVENTORY)

    assert set(duties) == {
        "clip_split_top_center_left",
        "clip_split_top_center_right",
    }
    assert duties["clip_split_top_center_left"]["legacy_host_members"] == [
        "base_rail_top",
        "base_principal_center_left",
    ]
    assert duties["clip_split_top_center_right"]["legacy_host_members"] == [
        "base_rail_top",
        "base_principal_center_right",
    ]
    assert len(top_center._expected_source_axis_ids(duties)) == 12
    assert {axis["axis_id"] for row in duties.values() for axis in row["legacy_sds_axes"]} == {
        f"clip_split_top_center_{side}_{kind}_{index}"
        for side in ("left", "right")
        for kind in ("beam", "upright")
        for index in (1, 2, 3)
    }


def test_outboard_cleat_placement_avoids_inward_overlap_and_keeps_source_offsets():
    placement = top_center._proposed_placement(1041.25, 1219.35)

    assert placement["left"]["x_interval_mm"] == pytest.approx([952.35, 1041.25])
    assert placement["right"]["x_interval_mm"] == pytest.approx([1219.35, 1308.25])
    assert placement["left"]["principal_bolt_direction_sign_x"] == 1.0
    assert placement["right"]["principal_bolt_direction_sign_x"] == -1.0
    assert placement["left"]["rail_row_x_mm"] == pytest.approx(997.8)
    assert placement["right"]["rail_row_x_mm"] == pytest.approx(1262.8)
    assert placement["left"]["rail_bolt_n_mm"] == pytest.approx([65.45, 94.25])
    assert placement["inward_face_pair_overlap_if_used_mm"] == pytest.approx(75.9)


def test_top_center_conditional_end_screen_is_explicit_and_not_release():
    placement = top_center._proposed_placement(1041.25, 1219.35)
    screen = top_center._conditional_edge_screen(placement)

    assert screen["rail_bolt_row_spacing_mm"] == pytest.approx(28.8)
    assert screen["minimum_rail_bolt_grain_end_distance_mm"] == pytest.approx(45.45)
    assert screen["conditional_7D_reference_mm"] == pytest.approx(44.45)
    assert screen["conditional_7D_geometric_screen_clear"] is True
    assert screen["signed_demand_directions_available"] is False
    assert screen["conditional_end_distance_is_not_an_accepted_limit_state"] is True


def test_six_inch_envelope_uses_layer_tolerance_and_does_not_claim_engagement():
    screen = top_center._dimensional_fit_screen()["per_127mm_grip_stack"]

    assert screen["nominal_grip_mm"] == pytest.approx(127.0)
    assert screen["grip_range_with_two_layer_tolerances_mm"] == pytest.approx([126.0, 128.0])
    assert screen["earliest_nut_bearing_plane_mm"] == pytest.approx(128.5908)
    assert screen["farthest_nut_face_mm"] == pytest.approx(137.8044)
    assert screen["required_length_with_tip_reserve_mm"] == pytest.approx(140.3444)
    assert screen["minimum_length_envelope_margin_mm"] == pytest.approx(9.5156)
    assert screen[
        "earliest_nut_bearing_minus_minimum_smooth_body_bound_mm"
    ] == pytest.approx(1.5908)
    assert screen[
        "maximum_ring_gage_plane_minus_earliest_nut_bearing_mm"
    ] == pytest.approx(4.7592)
    assert screen["farthest_nut_face_minus_maximum_ring_gage_plane_mm"] == pytest.approx(
        4.4544
    )
    assert screen["gage_plane_is_not_first_full_form_thread"] is True
    assert screen["conservative_bounds_are_not_an_actual_received_stack_measurement"] is True
    assert screen["full_form_nut_engagement_established"] is False
    assert screen["received_stack_fit_established"] is False


def _valid_wj18_context():
    counts = {
        "target_duties": 18,
        "source_hosts": 14,
        "replaced_source_sds_axes": 108,
        "candidate_bores": 80,
        "candidate_installed_hardware_components": 400,
        "candidate_parts": 22,
        "fixed_panel_axes": 66,
        "retained_frame_bolts": 12,
        "retained_frame_bolt_shapes": 72,
        "retained_legacy_clips": 6,
        "retained_legacy_sds_axes": 36,
    }
    return SimpleNamespace(
        layout_id=wj18.LAYOUT_ID,
        trial_id=wj18.TRIAL_ID,
        counts=counts,
        composition_checks={
            "exact_wj16_base_contract": True,
            "exact_top_outer_two_duty_contract": True,
            "source_inventory_and_family_hashes_current": True,
            "all_108_source_sds_axes_replaced": True,
            "top_rail_purchase_overlay_absorbed_into_host_map": True,
            "two_bottom_rail_overlays_and_four_cuts_preserved": True,
            "native_and_purchase_maps_remain_distinct": True,
            "four_existing_backer_receiver_redirects_preserved": True,
            "all_80_candidate_axes_and_400_cad_roles_preserved": True,
            "candidate_axis_station_bindings_match_exact_contract": True,
            "all_14_shared_hosts_rebuilt_from_union_cut_maps_and_bores": True,
            "source_reconstruction_evidence_covers_all_14_hosts": True,
            "all_66_fixed_axes_and_12_frame_bolts_preserved": True,
        },
        target_station_ids=wj18.EXPECTED_TARGET_DUTY_IDS,
        finished_hosts={name: object() for name in wj18.EXPECTED_SOURCE_HOST_IDS},
        candidate_bores={name: object() for name in wj18.EXPECTED_CANDIDATE_AXIS_IDS},
        candidate_installed_hardware={
            name: {f"role_{index}": object() for index in range(5)}
            for name in wj18.EXPECTED_CANDIDATE_AXIS_IDS
        },
        finished_candidate_parts={
            name: object() for name in wj18.EXPECTED_CANDIDATE_PART_IDS
        },
        fixed_axes={f"fixed_{index}": object() for index in range(66)},
        frame_bolt_records=tuple({"axis_id": f"frame_{index}"} for index in range(12)),
        frame_bolt_shapes={f"shape_{index}": object() for index in range(72)},
    )


def test_context_contract_accepts_exact_wj18_identity_and_rejects_wrong_axis_census():
    context = _valid_wj18_context()

    assert top_center._context_identity(context)["candidate_bores"] == 80
    context.candidate_bores.pop(next(iter(context.candidate_bores)))
    with pytest.raises(ValueError, match="exact 80-axis contract"):
        top_center._context_identity(context)


def test_all_top_center_release_flags_are_false():
    assert set(top_center.RELEASE_FLAGS) == {
        "candidate_accepted",
        "source_cutting_released",
        "drilling_released",
        "fabrication_released",
        "structural_accepted",
        "assembly_proven",
    }
    assert top_center._false_release_flags() == {
        "candidate_accepted": False,
        "source_cutting_released": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_accepted": False,
        "assembly_proven": False,
    }
