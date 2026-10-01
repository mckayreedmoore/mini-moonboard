from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "scripts/build_current_full_frame_machining_inventory_attempt01.py"
SPEC = importlib.util.spec_from_file_location("full_frame_machining_inventory", PRODUCER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_all_current_members_reconcile_to_manifest_and_step_bundle() -> None:
    record = MODULE.build()
    assert record["counts"] == {
        "current_members": 50,
        "current_timbers": 20,
        "current_candidate_blocks": 24,
        "current_plywood_panels": 6,
        "members_reconciled_to_prior_cut_inventory": 44,
        "members_without_prior_cut_inventory_row": 6,
        "candidate_bolt_axes": 92,
        "retained_frame_bolt_axes": 12,
        "panel_kicker_screw_axes": 66,
    }
    assert len({row["member_id"] for row in record["members"]}) == 50
    assert all(row["finished_step_sha256"] for row in record["members"])


def test_only_six_panels_lack_prior_cut_inventory_rows() -> None:
    record = MODULE.build()
    missing = [
        row
        for row in record["members"]
        if row["prior_cut_inventory_coverage"]
        == "not_covered_by_prior_cut_inventory"
    ]
    assert {row["member_id"] for row in missing} == {
        "kicker_left",
        "kicker_right",
        "main_lower_left",
        "main_lower_right",
        "main_upper_left",
        "main_upper_right",
    }
    assert all(row["member_kind"] == "plywood_panel" for row in missing)


def test_axis_occupancy_never_becomes_a_cutter_dimension() -> None:
    record = MODULE.build()
    candidate = record["axis_maps"]["candidate_bolt_axes"]
    retained = record["axis_maps"]["retained_frame_bolt_axes"]
    screws = record["axis_maps"]["panel_kicker_screw_axes"]
    assert len(candidate) == 92
    assert len(retained) == 12
    assert len(screws) == 66
    assert all(row["clearance_bore_diameter_mm"] is None for row in candidate)
    assert all(row["clearance_bore_diameter_mm"] is None for row in retained)
    assert all("operation dimensions" in row["preparatory_hole_geometry_status"] for row in screws)


def test_packet_does_not_claim_complete_machining_or_release() -> None:
    record = MODULE.build()
    assert record["criterion_effect"]["all_machining_represented"] is False
    assert record["criterion_effect"]["disposition"] == "pending"
    assert record["cutting_or_drilling_released"] is False
    assert record["fabrication_released"] is False


def test_source_drift_fails_closed(monkeypatch) -> None:
    monkeypatch.setitem(MODULE.EXPECTED_INPUT_SHA256, MODULE.INPUTS["current_manifest"], "0" * 64)
    try:
        MODULE.build()
    except ValueError as error:
        assert "Pinned source drift" in str(error)
    else:
        raise AssertionError("Expected source drift to fail closed")


def test_duplicate_source_identities_fail_closed() -> None:
    try:
        MODULE.index_unique([{"id": "member-1"}, {"id": "member-1"}], "id", "fixture")
    except ValueError as error:
        assert "Duplicate fixture identifier" in str(error)
    else:
        raise AssertionError("Expected duplicate member IDs to fail closed")
    try:
        MODULE.require_unique(["axis-1", "axis-1"], "fixture axis")
    except ValueError as error:
        assert "Duplicate fixture axis identifier" in str(error)
    else:
        raise AssertionError("Expected duplicate axis IDs to fail closed")
