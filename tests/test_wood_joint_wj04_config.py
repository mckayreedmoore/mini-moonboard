import json
from dataclasses import replace

import pytest

from mini_moonboard.wood_joint_wj04_config import (
    WJ04_TRIAL,
    LayerConfig,
    validate_wj04_trial,
)


def test_trial_config_binds_narrow_cleat_stock_and_frozen_screw_policy():
    assert WJ04_TRIAL.development_candidate_id == "compact-floor-flush-wood-joints-development"
    assert WJ04_TRIAL.preserved_selected_candidate_id == "compact-floor-flush-development"
    assert WJ04_TRIAL.fixed_panel_kicker_screw_axis_count == 66
    assert WJ04_TRIAL.cleat.size_x_t_n_mm == (95.25, 38.1, 119.7)
    assert WJ04_TRIAL.cleat.origin_x_t_n_mm == (89.05, 1353.874134, 229.840968)
    assert WJ04_TRIAL.cleat.grain_axis == "N"
    assert "2x6" in WJ04_TRIAL.cleat.stock_note
    assert not WJ04_TRIAL.stock_grade_verified
    assert not WJ04_TRIAL.purchase_approved
    assert not WJ04_TRIAL.drilling_released
    assert not WJ04_TRIAL.fabrication_released
    assert not WJ04_TRIAL.structural_released


def test_stack_contract_uses_ordered_actual_layers_and_separates_cad_lengths():
    rail = WJ04_TRIAL.stack_by_id("rail_1")
    principal = WJ04_TRIAL.stack_by_id("upright_1")

    assert [(layer.member_id, layer.thickness_mm) for layer in rail.layers] == [
        ("base_rail_service_lower_right", 38.1),
        ("wj04_cleat", 38.1),
    ]
    assert rail.grip_mm == 76.2
    assert rail.hardware_candidate.sku == "25C375HCS5Z"
    assert rail.hardware_candidate.nominal_length_mm == 95.25
    assert rail.cad_envelope.product_bound_head_dimensions
    assert rail.cad_envelope.head_diameter_mm == 12.827
    assert rail.cad_envelope.head_height_mm == 4.1402
    assert rail.cad_envelope.product_bound_shaft_diameter
    assert rail.hardware_candidate.body_diameter_range_mm == (6.223, 6.35)
    assert rail.cad_envelope.washer_outer_diameter_mm == 19.0246
    assert rail.cad_envelope.washer_inner_diameter_mm == 7.7978
    assert rail.cad_envelope.washer_thickness_mm == 2.032
    assert rail.cad_envelope.nut_height_mm == 5.7404
    assert rail.cad_envelope.washer_maximum_bounds_applied
    assert rail.cad_envelope.nut_maximum_thickness_applied

    assert [(layer.member_id, layer.thickness_mm) for layer in principal.layers] == [
        ("wj04_cleat", 95.25),
        ("base_principal_center_right", 38.1),
    ]
    assert principal.grip_mm == 133.35
    assert principal.hardware_candidate.sku == "25C600HCS5Z"


def test_trial_axes_preserve_saved_source_positions_and_candidate_access_record():
    rail = WJ04_TRIAL.stack_by_id("rail_1")
    principal = WJ04_TRIAL.stack_by_id("upright_1")

    assert rail.axis_point_basis_mm == (127.15, 1315.774134, 265.0)
    assert rail.axis_direction_basis == (0.0, 1.0, 0.0)
    assert WJ04_TRIAL.axis_point_global("rail_1") == pytest.approx((127.15, 642.761533, 1178.28018))
    assert principal.axis_point_basis_mm == (184.3, 1372.924134, 293.0)
    assert principal.axis_direction_basis == (-1.0, 0.0, 0.0)
    assert WJ04_TRIAL.axis_point_global("upright_1") == pytest.approx((184.3, 658.0476, 1240.057673))

    assert WJ04_TRIAL.fasteners.washers_per_stack == 2
    assert WJ04_TRIAL.fasteners.washer.thickness_range_mm == (1.2954, 2.032)
    assert WJ04_TRIAL.fasteners.nut.thickness_range_mm == (5.3848, 5.7404)
    assert WJ04_TRIAL.fasteners.head.height_range_mm == (3.81, 4.1402)
    assert WJ04_TRIAL.fasteners.head.across_flats_range_mm == (10.8712, 11.1252)
    assert WJ04_TRIAL.fasteners.head.across_corners_range_mm == (12.3952, 12.827)
    tool = WJ04_TRIAL.fasteners.tools[0]
    assert (tool.head_width_mm, tool.head_thickness_mm, tool.overall_length_mm) == (22.0, 3.0, 100.0)
    assert not tool.published_dimension_tolerances
    assert not tool.handle_sweep_verified


def test_serialized_trial_contains_derived_grips_and_is_json_encodable():
    payload = WJ04_TRIAL.as_dict()
    assert json.loads(json.dumps(payload))["stacks"][0]["grip_mm"] == 76.2
    assert payload["stacks"][0]["axis_point_global_mm"] == pytest.approx(
        (127.15, 642.761533, 1178.28018)
    )
    assert len(WJ04_TRIAL.canonical_sha256) == 64


def test_config_hash_and_global_coordinates_follow_replaced_config_frame():
    shifted = replace(
        WJ04_TRIAL,
        frame=replace(WJ04_TRIAL.frame, origin_global_mm=(10.0, 0.0, 0.0)),
    )

    assert shifted.axis_point_global("rail_1") == pytest.approx((137.15, 642.761533, 1178.28018))
    assert shifted.as_dict()["stacks"][0]["axis_point_global_mm"] == pytest.approx(
        (137.15, 642.761533, 1178.28018)
    )
    assert shifted.canonical_sha256 != WJ04_TRIAL.canonical_sha256

    with pytest.raises(ValueError, match="absolute projections"):
        validate_wj04_trial(shifted)


def test_validator_rejects_changed_actual_member_layer_thickness():
    original = WJ04_TRIAL.stack_by_id("rail_1")
    changed = replace(
        original,
        layers=(LayerConfig("base_rail_service_lower_right", 38.1), LayerConfig("wj04_cleat", 53.34)),
    )
    changed_trial = replace(
        WJ04_TRIAL,
        stacks=tuple(changed if stack.stack_id == changed.stack_id else stack for stack in WJ04_TRIAL.stacks),
    )

    with pytest.raises(ValueError, match="ordered actual layer data"):
        validate_wj04_trial(changed_trial)


def test_validator_rejects_moved_axis_and_wrong_interface_bolt_candidate():
    rail = WJ04_TRIAL.stack_by_id("rail_1")
    moved_axis = replace(rail, axis_point_basis_mm=(127.15, 1315.774134, 266.0))
    moved_trial = replace(
        WJ04_TRIAL,
        stacks=tuple(moved_axis if stack.stack_id == "rail_1" else stack for stack in WJ04_TRIAL.stacks),
    )
    with pytest.raises(ValueError, match="bolt axis moved"):
        validate_wj04_trial(moved_trial)

    wrong_candidate = replace(rail, hardware_candidate=WJ04_TRIAL.stack_by_id("upright_1").hardware_candidate)
    changed_trial = replace(
        WJ04_TRIAL,
        stacks=tuple(wrong_candidate if stack.stack_id == "rail_1" else stack for stack in WJ04_TRIAL.stacks),
    )
    with pytest.raises(ValueError, match="wrong bolt candidate"):
        validate_wj04_trial(changed_trial)


def test_validator_rejects_changed_source_frame_member_binding_and_cad_envelope():
    rotated_frame = replace(WJ04_TRIAL.frame, t_global=(0.0, 1.0, 0.0))
    with pytest.raises(ValueError, match="source-inventory X/T/N basis"):
        validate_wj04_trial(replace(WJ04_TRIAL, frame=rotated_frame))

    rail_member = next(member for member in WJ04_TRIAL.members if member.member_id == "base_rail_service_lower_right")
    drifted_rail = replace(rail_member, grain_axis="T")
    members = tuple(drifted_rail if member == rail_member else member for member in WJ04_TRIAL.members)
    with pytest.raises(ValueError, match="member records"):
        validate_wj04_trial(replace(WJ04_TRIAL, members=members))

    rail = WJ04_TRIAL.stack_by_id("rail_1")
    drifted_envelope = replace(rail.cad_envelope, head_height_mm=4.7752)
    drifted_stack = replace(rail, cad_envelope=drifted_envelope)
    stacks = tuple(drifted_stack if stack.stack_id == rail.stack_id else stack for stack in WJ04_TRIAL.stacks)
    with pytest.raises(ValueError, match="CAD envelope"):
        validate_wj04_trial(replace(WJ04_TRIAL, stacks=stacks))
