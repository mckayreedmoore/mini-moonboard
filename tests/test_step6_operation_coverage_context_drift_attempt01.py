from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "scripts/reconcile_step6_operation_coverage_context_drift_attempt01.py"
SPEC = importlib.util.spec_from_file_location("step6_context_drift", PRODUCER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_replay_is_limited_to_the_plan_context_and_derived_digest() -> None:
    record = MODULE.build()
    assert record["status"] == "replay_matches_except_for_current_plan_context_pin"
    assert len(record["replay"]["json_diff_paths"]) == 1
    assert record["replay"]["json_diff_paths"][0].endswith("/sha256")
    assert record["replay"]["readme_diff_lines"][0]["frozen"].startswith(
        "Machine JSON SHA-256:"
    )
    assert record["replay"]["axis_records_unchanged"] is True
    assert record["replay"]["service_records_unchanged"] is True
    assert record["replay"]["operation_counts_unchanged"]["operation_records"] == 575
    assert len(record["replay"]["current_source_bindings"]) == 22


def test_reconciliation_keeps_fit_and_release_gates_open() -> None:
    record = MODULE.build()
    assert record["criterion_effect"]["fit_and_transport_criteria_closed"] is False
    assert record["criterion_effect"]["engineering_mvp_complete"] is False
    assert record["criterion_effect"]["release"] is False


def test_source_pin_drift_fails_closed(monkeypatch) -> None:
    monkeypatch.setitem(MODULE.EXPECTED_SOURCE_SHA256, MODULE.CURRENT_PLAN, "0" * 64)
    try:
        MODULE.build()
    except ValueError as error:
        assert "Pinned source drift" in str(error)
    else:
        raise AssertionError("Expected changed plan source to fail closed")
