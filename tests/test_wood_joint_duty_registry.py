"""Lightweight accounting checks for former-angle duty registry."""

import json
from collections import Counter

import pytest

from scripts.wood_joint_duty_registry import (
    OUTPUT_JSON,
    RegistryError,
    build_registry,
    validate_duty_assignments,
)


def test_registry_maps_all_legacy_duties_and_preserves_retained_obligations():
    registry = build_registry()

    assert registry["counts"] == {
        "legacy_former_angle_duties": 24,
        "legacy_removed_sds_axes": 144,
        "legacy_axes_mapped_to_duty_rows": 144,
        "unique_duty_assignments": 24,
        "source_inventory_replacement_owner_fields_unassigned": 24,
        "duties_with_WJ03_interface_owner_evidence": 4,
        "duties_without_materialized_interface_records": 20,
        "missing_proposed_owner_id_count": 0,
        "unresolved_or_unaccepted_duty_count": 24,
        "accepted_replacement_duty_count": 0,
        "fixed_panel_kicker_hillman_axes_retained": 66,
        "starting_frame_bolt_obligations_retained": 12,
    }
    assert len({row["legacy_duty_id"] for row in registry["duties"]}) == 24
    assert all(len(row["legacy_sds_axis_ids"]) == 6 for row in registry["duties"])
    assert Counter(row["owner_assignment_status"] for row in registry["duties"]) == {
        "proposed_layout_path_strength_incomplete": 4,
        "diagnostic_revise_unaccepted": 1,
        "proposed_unimplemented_blocked_by_WJ05": 4,
        "proposed_unimplemented_no_generated_report": 15,
    }
    assert all(row["replacement_accepted"] is False for row in registry["duties"])
    assert registry["retained_obligations"]["fixed_panel_kicker_screws"]["count"] == 66
    assert registry["retained_obligations"]["fixed_panel_kicker_screws"][
        "axes_moved_per_receiver_audit"
    ] == 0
    assert registry["retained_obligations"]["starting_frame_bolts"]["count"] == 12
    assert registry["provisional_axes_and_hardware"]["wj06_residual_probe"][
        "complete_installed_stack_count"
    ] == 0
    assert registry["provisional_axes_and_hardware"]["wj05_center_backer_attachment"][
        "complete_installed_stack_count"
    ] == 0
    assert not any(registry["release_flags"].values())


def test_assignment_validator_rejects_duplicate_duty_rows():
    rows = [
        {"legacy_duty_id": "duty_a"},
        {"legacy_duty_id": "duty_a"},
    ]

    with pytest.raises(RegistryError, match="duplicate assignments"):
        validate_duty_assignments(["duty_a", "duty_b"], rows)


def test_assignment_validator_rejects_missing_duty_rows():
    rows = [{"legacy_duty_id": "duty_a"}]

    with pytest.raises(RegistryError, match="missing assignments"):
        validate_duty_assignments(["duty_a", "duty_b"], rows)


def test_written_registry_matches_generator():
    assert json.loads(OUTPUT_JSON.read_text()) == build_registry()


def test_script_only_wj06_corridors_are_not_counted_as_materialized_or_accepted():
    registry = build_registry()
    wj06 = registry["provisional_axes_and_hardware"]["wj06_residual_probe"]

    assert wj06["report_status"] == "not_materialized"
    assert wj06["potential_corridor_count_if_all_declared_trials_run"] == 540
    assert wj06["materialized_corridor_count"] == 0
    assert wj06["complete_installed_stack_count"] == 0
