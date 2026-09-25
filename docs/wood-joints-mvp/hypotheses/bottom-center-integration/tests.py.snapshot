"""Pure inventory-contract tests for the bottom-center source-bound producer."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_bottom_center_integration as bottom_center

ROOT = Path(__file__).resolve().parents[1]


def _inventory():
    return json.loads(
        (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text()
    )


def test_exact_bottom_center_duty_and_axis_contract():
    duties = bottom_center._duty_rows(_inventory())

    assert set(duties) == {
        "clip_horizontal_bottom_left_2",
        "clip_horizontal_bottom_right_1",
    }
    assert duties["clip_horizontal_bottom_left_2"]["legacy_host_members"] == [
        "base_rail_bottom_left",
        "base_principal_center_left",
    ]
    assert duties["clip_horizontal_bottom_right_1"]["legacy_host_members"] == [
        "base_rail_bottom_right",
        "base_principal_center_right",
    ]
    assert len(bottom_center._source_axis_ids(duties)) == 12
    assert bottom_center.BOTTOM_CANDIDATE_AXIS_IDS == {
        f"bottom_center/{duty}/{role}_{index}"
        for duty in duties
        for role in ("rail", "principal")
        for index in (1, 2)
    }


def test_source_faces_derive_outboard_cleats_and_head_seats_from_each_rail():
    placements = bottom_center.derive_bottom_center_placements(_inventory())
    left = placements["clip_horizontal_bottom_left_2"]
    right = placements["clip_horizontal_bottom_right_1"]

    assert left["cleat_local_intervals_mm"] == {
        "X": [952.35, 1041.25],
        "T": [38.1, 127.0],
        "N": [10.0, 129.7],
    }
    assert right["cleat_local_intervals_mm"] == {
        "X": [0.0, 88.9],
        "T": [38.1, 127.0],
        "N": [10.0, 129.7],
    }
    assert left["source_rail_origin_global_xyz_mm"] == [-1130.3, -6.077296, 319.211955]
    assert right["source_rail_origin_global_xyz_mm"] == [89.05, -6.077296, 319.211955]
    assert left["cleat_bounds_global_xyz_mm"] == [
        -177.95,
        -89.05,
        -80.943052,
        67.896286,
        354.826124,
        499.869152,
    ]
    assert right["cleat_bounds_global_xyz_mm"] == [
        89.05,
        177.95,
        -80.943052,
        67.896286,
        354.826124,
        499.869152,
    ]
    assert left["principal_bolt_head_seat_X_mm"] == 952.35
    assert left["principal_bolt_interface_X_mm"] == 1041.25
    assert right["principal_bolt_head_seat_X_mm"] == 88.9
    assert right["principal_bolt_interface_X_mm"] == 0.0
    assert left["inward_cleat_pair_gap_mm"] == 178.1
    assert right["inward_cleat_pair_gap_mm"] == 178.1


def test_head_to_nut_principal_rows_have_correct_direction_layers_and_grip():
    placements = bottom_center.derive_bottom_center_placements(_inventory())
    left = placements["clip_horizontal_bottom_left_2"]
    right = placements["clip_horizontal_bottom_right_1"]

    assert left["principal_bolt_T_positions_mm"] == [68.15, 96.95]
    assert right["principal_bolt_T_positions_mm"] == [68.15, 96.95]
    assert left["principal_bolt_N_mm"] == right["principal_bolt_N_mm"] == 69.85
    assert left["principal_bolt_direction_global_xyz"] == [1.0, 0.0, 0.0]
    assert right["principal_bolt_direction_global_xyz"] == [-1.0, 0.0, 0.0]
    assert left["rail_bolt_N_positions_mm"] == [55.45, 84.25]
    assert left["rail_bolt_X_mm"] == 996.8
    assert right["rail_bolt_X_mm"] == 44.45
    assert left["rail_grip_mm"] == left["principal_grip_mm"] == 127.0
    assert right["rail_grip_mm"] == right["principal_grip_mm"] == 127.0
    assert left["interface_stack_datum_is_not_head_seat_datum"] is True


def test_changed_receiver_identity_or_source_face_is_fail_closed():
    inventory = copy.deepcopy(_inventory())
    row = next(
        item
        for item in inventory["legacy_duties"]
        if item["legacy_station_id"] == "clip_horizontal_bottom_right_1"
    )
    row["legacy_host_members"][1] = "base_side_right"
    with pytest.raises(ValueError, match="receiver mapping changed"):
        bottom_center._duty_rows(inventory)

    inventory = copy.deepcopy(_inventory())
    principal = next(
        item
        for item in inventory["parts"]
        if item["part_id"] == "base_principal_center_left"
    )
    for face in principal["actual_planar_faces"]:
        if face["normal_global_xyz"] == [-1.0, -0.0, 0.0]:
            face["normal_global_xyz"] = [1.0, 0.0, 0.0]
    with pytest.raises(ValueError, match="expected one actual face"):
        bottom_center.derive_bottom_center_placements(inventory)


def test_conditional_edge_screen_and_dimensional_fit_do_not_claim_acceptance():
    placements = bottom_center.derive_bottom_center_placements(_inventory())
    edge = bottom_center._conditional_edge_screen(placements)
    fit = bottom_center._dimensional_fit_screen()

    for row in edge["per_duty"].values():
        assert row["minimum_grain_end_distance_mm"] == 45.45
        assert row["conditional_7D_reference_mm"] == 44.45
        assert row["conditional_7D_geometric_screen_clear"] is True
        assert row["signed_demand_directions_available"] is False
    assert fit["grip_nominal_mm"] == 127.0
    assert fit["grip_range_with_each_wood_layer_plus_or_minus_0p5mm_mm"] == [
        126.0,
        128.0,
    ]
    assert fit["required_length_with_tip_reserve_mm"] == 140.3444
    assert fit["minimum_length_envelope_margin_mm"] == 9.5156
    assert fit["first_full_form_thread_and_nut_engagement_established"] is False
    assert fit["received_stack_fit_established"] is False


def test_release_flags_are_unconditionally_false():
    assert bottom_center._false_release() == {
        name: False for name in bottom_center.RELEASE_FLAG_NAMES
    }


def test_candidate_scene_filters_generated_clips_and_fasteners_from_source_parts():
    inventory = _inventory()
    timber_ids = {
        row["part_id"] for row in inventory["parts"] if row["kind"] == "timber"
    }
    panel_ids = {
        row["part_id"]
        for row in inventory["parts"]
        if row["kind"] == "plywood_panel"
    }
    shape = cq.Solid.makeBox(1, 1, 1)
    raw_source_parts = {
        part_id: shape for part_id in timber_ids | panel_ids
    }
    assert len(raw_source_parts) == 26
    assert set(raw_source_parts) == timber_ids | panel_ids
    canonical_finished = {
        **raw_source_parts,
        **{panel_id: shape for panel_id in panel_ids},
        "clip_horizontal_bottom_left_2": shape,
        "legacy_sds_axis_001": shape,
        "generated_washer_001": shape,
    }
    geometry = SimpleNamespace(
        finished_hosts={},
        additional_finished_source_parts={},
        panel_replacements={},
    )

    scene = bottom_center._candidate_scene(
        geometry,
        raw_source_parts,
        canonical_finished,
        inventory,
        {},
        {},
    )

    assert set(scene) == timber_ids | panel_ids
    assert "clip_horizontal_bottom_left_2" not in scene
    assert "legacy_sds_axis_001" not in scene
    assert "generated_washer_001" not in scene


def test_candidate_scene_rejects_raw_wood_id_drift():
    inventory = _inventory()
    shape = cq.Solid.makeBox(1, 1, 1)
    wood_ids = {row["part_id"] for row in inventory["parts"]}
    canonical_finished = {
        row["part_id"]: shape for row in inventory["parts"]
    }
    geometry = SimpleNamespace(
        finished_hosts={},
        additional_finished_source_parts={},
        panel_replacements={},
    )

    with pytest.raises(ValueError, match="exact inventory timber-and-panel set"):
        bottom_center._candidate_scene(
            geometry,
            {part_id: shape for part_id in wood_ids if part_id != "kicker_right"},
            canonical_finished,
            inventory,
            {},
            {},
        )


def _through_cut(x_mm: float) -> cq.Shape:
    return cq.Solid.makeCylinder(
        0.75,
        20.0,
        cq.Vector(x_mm, 5.0, 0.0),
        cq.Vector(0, 0, 1),
    )


def test_retained_host_replay_does_not_restore_wj18_removed_source_holes():
    host_id = "base_principal_center_left"
    raw = cq.Solid.makeBox(24.0, 10.0, 20.0)
    old_removed_id = "old_wj18_replaced_axis"
    target_replaced_id = "bottom_center_target_axis"
    retained_id = "source_axis_still_present"
    old_removed, target_old, retained = (
        _through_cut(3.0),
        _through_cut(9.0),
        _through_cut(18.0),
    )
    previous_bore = _through_cut(6.0)
    new_bore = _through_cut(12.0)
    retained_host = raw.cut(target_old, retained, previous_bore).clean()
    geometry = SimpleNamespace(
        replaced_source_cutter_ids={old_removed_id},
        applied_source_cutters_by_host={
            host_id: {
                old_removed_id: old_removed,
                target_replaced_id: target_old,
                retained_id: retained,
            }
        },
        finished_hosts={host_id: retained_host},
        additional_finished_source_parts={},
        candidate_bores={
            "retained_candidate_axis": SimpleNamespace(
                shape=previous_bore,
                receiver_ids=(host_id,),
            )
        },
    )

    before, after, evidence = bottom_center._rebuild_one_host_preview(
        geometry,
        host_id,
        raw,
        {
            host_id: {
                old_removed_id: old_removed,
                target_replaced_id: target_old,
                retained_id: retained,
            }
        },
        {host_id: {}},
        frozenset({target_replaced_id}),
        {"bottom_center_new_axis": new_bore},
    )

    expected_retained = raw.cut(target_old, retained, previous_bore).clean()
    expected_before = raw.cut(retained, previous_bore).clean()
    expected_after = expected_before.cut(new_bore).clean()
    assert bottom_center._symmetric_difference_volume(
        expected_retained, retained_host
    ) < 1e-6
    assert bottom_center._symmetric_difference_volume(before, expected_before) < 1e-6
    assert bottom_center._symmetric_difference_volume(after, expected_after) < 1e-6
    assert evidence["wj18_removed_source_cutter_ids_excluded"] == [old_removed_id]
    assert evidence["reconstructed_retained_wj18_symmetric_difference_mm3"] == 0.0


def test_bottom_rail_replay_uses_source_overlay_when_no_finished_host_override_exists():
    host_id = "base_rail_bottom_left"
    raw = cq.Solid.makeBox(24.0, 10.0, 20.0)
    target_id = "bottom_center_legacy_axis"
    native_id = "retained_native_axis"
    purchase_id = "panel_purchase/retained_panel_axis"
    target_old, native_cut, purchase_cut = (
        _through_cut(3.0),
        _through_cut(9.0),
        _through_cut(18.0),
    )
    previous_bore = _through_cut(6.0)
    new_bore = _through_cut(12.0)
    source_overlay = raw.cut(target_old, native_cut, purchase_cut).clean()
    geometry = SimpleNamespace(
        replaced_source_cutter_ids=set(),
        applied_source_cutters_by_host={},
        finished_hosts={},
        additional_finished_source_parts={host_id: source_overlay},
        candidate_bores={
            "retained_bottom_rail_axis": SimpleNamespace(
                shape=previous_bore,
                receiver_ids=(host_id,),
            )
        },
    )

    before, after, evidence = bottom_center._rebuild_one_host_preview(
        geometry,
        host_id,
        raw,
        {host_id: {target_id: target_old, native_id: native_cut}},
        {host_id: {purchase_id: purchase_cut}},
        frozenset({target_id}),
        {"bottom_center_new_axis": new_bore},
    )

    expected_retained = source_overlay.cut(previous_bore).clean()
    expected_before = raw.cut(native_cut, purchase_cut, previous_bore).clean()
    expected_after = expected_before.cut(new_bore).clean()
    assert bottom_center._symmetric_difference_volume(
        before, expected_before
    ) < 1e-6
    assert bottom_center._symmetric_difference_volume(after, expected_after) < 1e-6
    assert evidence["retained_state_kind"] == (
        "source_purchase_overlay_plus_retained_candidate_bores"
    )
    assert bottom_center._symmetric_difference_volume(
        expected_retained, source_overlay.cut(previous_bore).clean()
    ) < 1e-6
