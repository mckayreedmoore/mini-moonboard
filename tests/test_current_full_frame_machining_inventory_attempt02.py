from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "scripts/build_current_full_frame_machining_inventory_attempt02.py"
SPEC = importlib.util.spec_from_file_location(
    "current_full_frame_machining_inventory_attempt02", PRODUCER
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _manifest() -> dict:
    return json.loads((ROOT / MODULE.CURRENT_MANIFEST).read_text(encoding="utf-8"))


def test_attempt02_binds_all_66_current_wj_axis_records_verbatim() -> None:
    record = MODULE.build()
    manifest = _manifest()
    rows = record["axis_maps"]["panel_kicker_screw_axes"]
    actual = {row["axis_id"]: row for row in rows}
    source = {row["axis_id"]: row for row in manifest["panel_kicker_screw_axes"]}

    assert len(actual) == len(source) == 66
    assert set(actual) == set(source)
    for axis_id, row in actual.items():
        assert row["current_wj_coordinate_and_receiver_source"][
            "axis_record_verbatim"
        ] == source[axis_id]
        assert row["current_wj_coordinate_and_receiver_source"]["file_sha256"] == (
            MODULE.EXPECTED_INPUT_SHA256[MODULE.CURRENT_MANIFEST]
        )
        assert row["not_a_cutter_inference"] is True
    assert record["panel_screw_policy_binding"]["current_wj_coordinate_source"][
        "axis_rows_canonical_sha256"
    ] == MODULE.canonical_sha256(manifest["panel_kicker_screw_axes"])
    assert MODULE.canonical_sha256(manifest["panel_kicker_screw_axes"]) == (
        MODULE.EXPECTED_CURRENT_AXIS_ROWS_SHA256
    )


def test_policy_dimensions_are_carried_to_every_axis_with_unknowns_open() -> None:
    record = MODULE.build()
    axes = record["axis_maps"]["panel_kicker_screw_axes"]
    assert len(axes) == 66
    for row in axes:
        policy = row["owner_selected_hillman_prep_policy"]
        assert policy["policy_id"] == "hillman-42605-kobalt-80277-pilot-countersink-policy"
        assert policy["pilot_diameter_in"] == 0.125
        assert policy["pilot_diameter_mm"] == 3.175
        assert policy["face_countersink_diameter_in"] == 0.375
        assert policy["face_countersink_diameter_mm"] == 9.525
        assert policy["offcut_trial_required_before_production"] is True
        assert row["unresolved_current_operation_fields"] == {
            "pilot_depth_mm": None,
            "countersink_depth_mm": None,
            "countersink_included_angle_deg": None,
            "location_tolerance_mm": None,
            "datum_and_setup_sequence": None,
            "physical_receiver_material_section_and_condition": None,
            "offcut_trial_observation": None,
            "axis_to_hold_led_cut_interaction_evidence": None,
            "net_section_or_local_section_evidence": None,
        }
        assert row["not_a_machining_or_fabrication_release"] is True


def test_axis_counts_and_eight_owner_directed_moves_are_preserved() -> None:
    record = MODULE.build()
    binding = record["panel_screw_policy_binding"]
    assert binding["axis_counts"] == {
        "all_current_axes": 66,
        "source_station_retained": 58,
        "owner_directed_moved": 8,
        "by_panel_member": {
            "kicker_left": 9,
            "kicker_right": 9,
            "main_lower_left": 12,
            "main_lower_right": 12,
            "main_upper_left": 12,
            "main_upper_right": 12,
        },
    }
    moves = binding["owner_directed_moves"]
    assert len(moves) == 8
    assert {row["axis_id"] for row in moves} == MODULE.EXPECTED_MOVED_AXIS_IDS
    assert all(row["new_start_global_xyz_mm"] for row in moves)


def test_six_panel_and_104_bolt_hole_operations_remain_unresolved() -> None:
    record = MODULE.build()
    gaps = {row["gap_id"]: row for row in record["gap_register"]}
    assert gaps["MACH-GAP-01"]["status"] == "open"
    assert gaps["MACH-GAP-04"]["status"] == "open"
    assert gaps["MACH-GAP-03"]["scope"] == (
        "92 candidate bolt axes and 12 retained frame-bolt axes"
    )
    assert record["counts"]["current_plywood_panels"] == 6
    assert record["counts"]["candidate_bolt_axes"] == 92
    assert record["counts"]["retained_frame_bolt_axes"] == 12
    assert record["criterion_effect"]["all_machining_represented"] is False
    assert record["criterion_effect"]["disposition"] == "pending"
    assert record["cutting_or_drilling_released"] is False
    assert record["fabrication_released"] is False


def test_six_exact_panel_step_identities_are_pinned_but_not_cut_decompositions() -> None:
    record = MODULE.build()
    rows = {
        row["member_id"]: row
        for row in record["members"]
        if row["member_kind"] == "plywood_panel"
    }
    assert set(rows) == set(MODULE.PANEL_STEP_IDENTITIES)
    for member_id, (path, digest) in MODULE.PANEL_STEP_IDENTITIES.items():
        row = rows[member_id]
        assert row["finished_step_path"] == path
        assert row["finished_step_sha256"] == digest
        assert row["cut_profile_decomposition_status"].startswith(
            "No row in the prior 44-member timber/block cut inventory"
        )
        assert row["prior_cut_inventory_coverage"] == "not_covered_by_prior_cut_inventory"
        assert record["source_pins"][path]["sha256"] == digest
        assert "artifact identity only" in record["source_pins"][path]["source_role"]


def test_panel_identity_validation_rejects_wrong_recorded_step_digest() -> None:
    prior = MODULE.read_json(MODULE.INPUTS["attempt01_inventory"])
    panel = next(row for row in prior["members"] if row["member_id"] == "kicker_left")
    panel["finished_step_sha256"] = "0" * 64
    try:
        MODULE._validate_panel_step_identities(prior)
    except ValueError as error:
        assert "recorded STEP digest drift" in str(error)
    else:
        raise AssertionError("Expected mismatched panel STEP identity to fail closed")


def test_owner_policy_source_and_current_wj_coordinate_source_are_separate() -> None:
    record = MODULE.build()
    binding = record["panel_screw_policy_binding"]
    policy_source = binding["policy_source"]
    coordinate_source = binding["current_wj_coordinate_source"]
    assert policy_source["path"] == MODULE.SHOP_CHECKLIST
    assert policy_source["applicability"].startswith("Selected-baseline checklist policy source")
    assert coordinate_source["path"] == MODULE.CURRENT_MANIFEST
    assert coordinate_source["manifest_id"] == "current-full-frame-input-manifest-attempt04"
    assert "does not define current-WJ coordinate datums" in policy_source["applicability"]


def test_current_manifest_pin_drift_fails_closed(monkeypatch) -> None:
    monkeypatch.setitem(
        MODULE.EXPECTED_INPUT_SHA256,
        MODULE.CURRENT_MANIFEST,
        "0" * 64,
    )
    try:
        MODULE.build()
    except ValueError as error:
        assert "Pinned source drift" in str(error)
    else:
        raise AssertionError("Expected current manifest source drift to fail closed")


def test_duplicate_axis_identifiers_fail_closed() -> None:
    row = {"axis_id": "axis-1"}
    try:
        MODULE.index_unique([row, row], "axis_id", "fixture axis")
    except ValueError as error:
        assert "Duplicate fixture axis identifier" in str(error)
    else:
        raise AssertionError("Expected duplicate axis IDs to fail closed")


def test_attempt02_record_digest_is_reproducible() -> None:
    record = MODULE.build()
    digest = record.pop("record_sha256")
    assert MODULE.canonical_sha256(record) == digest
