"""Cross-check the WJ-04 trial contract against its lightweight consumers.

These checks compare already-built input/report records. They do not invoke
the full CAD probe or assign hardware capacity.
"""

import json
from dataclasses import replace
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_wj04_config import (
    WJ04_TRIAL,
    validate_wj04_trial,
)
from scripts import wood_joint_wj04_probe
from scripts.wj04_fastener_stack_method import report as fastener_report

ROOT = Path(__file__).resolve().parents[1]
PROBE_ARTIFACT = ROOT / "docs/wood-joints-mvp/wj04-probe.json"


def _stack_layers(stack):
    return tuple((layer.member_id, layer.thickness_mm) for layer in stack.layers)


def _trial_with_layer_thickness(stack_id, layer_index, thickness_mm):
    stacks = []
    for stack in WJ04_TRIAL.stacks:
        if stack.stack_id != stack_id:
            stacks.append(stack)
            continue
        layers = list(stack.layers)
        layers[layer_index] = replace(layers[layer_index], thickness_mm=thickness_mm)
        stacks.append(replace(stack, layers=tuple(layers)))
    return replace(WJ04_TRIAL, stacks=tuple(stacks))


def _trial_with_axis_shift(stack_id, delta_mm):
    stacks = tuple(
        replace(
            stack,
            axis_point_basis_mm=(
                stack.axis_point_basis_mm[0] + delta_mm,
                *stack.axis_point_basis_mm[1:],
            ),
        )
        if stack.stack_id == stack_id
        else stack
        for stack in WJ04_TRIAL.stacks
    )
    return replace(WJ04_TRIAL, stacks=stacks)


def test_trial_config_keeps_active_geometry_and_ordered_joint_stacks_coherent():
    validate_wj04_trial()

    assert WJ04_TRIAL.trial_id == "narrow_x95p25_ordinary_bolt_candidate"
    assert WJ04_TRIAL.cleat.size_x_t_n_mm == (95.25, 38.1, 119.7)
    assert WJ04_TRIAL.fixed_panel_kicker_screw_axis_count == 66

    rail_layers = (
        ("base_rail_service_lower_right", 38.1),
        ("wj04_cleat", 38.1),
    )
    principal_layers = (
        ("wj04_cleat", 95.25),
        ("base_principal_center_right", 38.1),
    )
    rail_stacks = (
        WJ04_TRIAL.stack_by_id("rail_1"),
        WJ04_TRIAL.stack_by_id("rail_2"),
    )
    principal_stacks = (
        WJ04_TRIAL.stack_by_id("upright_1"),
        WJ04_TRIAL.stack_by_id("upright_2"),
    )

    assert {_stack_layers(stack) for stack in rail_stacks} == {rail_layers}
    assert {_stack_layers(stack) for stack in principal_stacks} == {principal_layers}
    assert {stack.grip_mm for stack in rail_stacks} == {76.2}
    assert {stack.grip_mm for stack in principal_stacks} == {133.35}
    assert len({stack.hardware_candidate.sku for stack in rail_stacks}) == 1
    assert len({stack.hardware_candidate.sku for stack in principal_stacks}) == 1

    rail_bolt = rail_stacks[0].hardware_candidate
    principal_bolt = principal_stacks[0].hardware_candidate
    assert (rail_bolt.sku, rail_bolt.nominal_length_mm) == (
        "25C375HCS5Z",
        95.25,
    )
    assert (principal_bolt.sku, principal_bolt.nominal_length_mm) == (
        "25C600HCS5Z",
        152.4,
    )
    assert not rail_bolt.full_form_thread_end_guaranteed
    assert not principal_bolt.full_form_thread_end_guaranteed


@pytest.mark.parametrize(
    ("stack_id", "layer_index", "independent_geometry_mm"),
    (
        # These were separate dimensions in the earlier fastener screen.
        ("rail_2", 1, 53.34),
        ("upright_2", 0, 100.0),
    ),
)
def test_validator_rejects_a_stack_that_drifts_from_its_interface_layers(
    stack_id, layer_index, independent_geometry_mm,
):
    drifted = _trial_with_layer_thickness(
        stack_id, layer_index, independent_geometry_mm,
    )

    with pytest.raises(ValueError, match="layer|interface"):
        validate_wj04_trial(config=drifted)


def test_validator_rejects_a_bolt_axis_that_moves_off_its_source_station():
    drifted = _trial_with_axis_shift("rail_1", 0.001)

    with pytest.raises(ValueError, match="bolt axis moved"):
        validate_wj04_trial(config=drifted)


def test_fastener_report_uses_each_config_layer_and_catalog_bound():
    screens = fastener_report(WJ04_TRIAL)
    assert tuple(row.stack_id for row in screens) == tuple(
        stack.stack_id for stack in WJ04_TRIAL.stacks
    )

    for screen in screens:
        config_stack = WJ04_TRIAL.stack_by_id(screen.stack_id)
        candidate = config_stack.hardware_candidate
        assert screen.interface_id == config_stack.interface_id
        assert screen.bolt_candidate_id == candidate.candidate_id
        assert screen.bolt_sku == candidate.sku
        assert screen.layer_member_ids == tuple(
            layer.member_id for layer in config_stack.layers
        )
        assert screen.layer_grip_mm == tuple(
            layer.thickness_mm for layer in config_stack.layers
        )
        assert screen.delivered_length_min_mm == pytest.approx(
            candidate.nominal_length_mm - candidate.length_minus_tolerance_mm
        )
        assert screen.delivered_length_max_mm == pytest.approx(
            candidate.nominal_length_mm
        )
        assert screen.standard_body_min_mm == pytest.approx(
            candidate.minimum_smooth_body_mm
        )
        assert screen.standard_full_thread_start_max_mm == pytest.approx(
            candidate.maximum_full_thread_start_mm
        )
        assert screen.standards_guarantee_full_form_thread_end is (
            candidate.full_form_thread_end_guaranteed
        )

    by_id = {row.stack_id: row for row in screens}
    assert by_id["rail_1"].nut_bearing_face_min_mm == pytest.approx(77.7908)
    assert by_id["rail_1"].nut_far_face_max_mm == pytest.approx(87.0044)
    assert by_id["upright_1"].nut_bearing_face_min_mm == pytest.approx(134.9408)
    assert by_id["upright_1"].nut_far_face_max_mm == pytest.approx(144.1544)


def test_cad_stack_adapter_builds_the_same_four_configured_fastener_models():
    modeled = wood_joint_wj04_probe.build_stacks(WJ04_TRIAL)
    assert set(modeled) == {stack.stack_id for stack in WJ04_TRIAL.stacks}

    for config_stack in WJ04_TRIAL.stacks:
        stack = modeled[config_stack.stack_id]
        candidate = config_stack.hardware_candidate
        envelope = config_stack.cad_envelope
        axis_global = WJ04_TRIAL.axis_point_global(config_stack.stack_id)
        direction_global = WJ04_TRIAL.axis_direction_global(config_stack.stack_id)

        assert tuple(
            (layer.body_id, layer.thickness_mm) for layer in stack.layers
        ) == _stack_layers(config_stack)
        assert stack.grip_mm == pytest.approx(config_stack.grip_mm)
        assert stack.hardware.candidate_sku == candidate.sku
        assert stack.hardware.under_head_length_mm == pytest.approx(
            candidate.nominal_length_mm
        )
        assert stack.hardware.steel_diameter_mm == pytest.approx(
            envelope.shaft_diameter_mm
        )
        assert stack.hardware.drill_diameter_mm == pytest.approx(
            envelope.bore_occupancy_diameter_mm
        )
        assert stack.hardware.washer_od_mm == pytest.approx(
            WJ04_TRIAL.fasteners.washer.outer_diameter_range_mm[1]
        )
        assert stack.hardware.washer_thickness_mm == pytest.approx(
            WJ04_TRIAL.fasteners.washer.thickness_range_mm[1]
        )
        assert stack.hardware.nut_height_mm == pytest.approx(
            WJ04_TRIAL.fasteners.nut.thickness_range_mm[1]
        )
        assert stack.head_seat.center.toTuple() == pytest.approx(axis_global)
        assert stack.direction.toTuple() == pytest.approx(direction_global)
        expected_under_head = cq.Vector(*axis_global) - cq.Vector(
            *direction_global
        ) * envelope.washer_thickness_mm
        assert stack.under_head_origin.toTuple() == pytest.approx(
            expected_under_head.toTuple()
        )


def test_checked_probe_record_matches_trial_axes_layers_and_candidate_lengths():
    artifact = json.loads(PROBE_ARTIFACT.read_text())

    assert artifact["trial_id"] == WJ04_TRIAL.trial_id
    assert artifact["trial_config_sha256"] == WJ04_TRIAL.canonical_sha256
    assert artifact["source_inventory_sha256"] == WJ04_TRIAL.source_inventory_sha256
    assert artifact["stock"]["section_x_t_n_mm"] == list(
        WJ04_TRIAL.cleat.size_x_t_n_mm
    )
    assert artifact["stock"]["grain_axis"] == WJ04_TRIAL.cleat.grain_axis
    assert set(artifact["stacks"]) == {
        stack.stack_id for stack in WJ04_TRIAL.stacks
    }
    canonical_stacks = {
        stack["stack_id"]: stack for stack in WJ04_TRIAL.as_dict()["stacks"]
    }
    members = {member.member_id: member for member in WJ04_TRIAL.members}
    assert artifact["source_faces"]["rail_rear"] in members[
        "base_rail_service_lower_right"
    ].source_face_ids
    assert artifact["source_faces"]["principal_rear"] in members[
        "base_principal_center_right"
    ].source_face_ids

    for config_stack in WJ04_TRIAL.stacks:
        row = artifact["stacks"][config_stack.stack_id]
        candidate = config_stack.hardware_candidate
        assert row["bolt_candidate_id"] == candidate.candidate_id
        assert row["bolt_sku"] == candidate.sku
        assert row["cad_envelope"] == canonical_stacks[
            config_stack.stack_id
        ]["cad_envelope"]
        assert row["grip_mm"] == pytest.approx(config_stack.grip_mm)
        assert row["nominal_under_head_length_mm"] == pytest.approx(
            candidate.nominal_length_mm
        )
        assert row["axis_global_xyz_mm"] == pytest.approx(
            WJ04_TRIAL.axis_point_global(config_stack.stack_id)
        )
        expected_direction = WJ04_TRIAL.axis_direction_global(
            config_stack.stack_id
        )
        assert row["direction_global_xyz"] == pytest.approx(expected_direction)
