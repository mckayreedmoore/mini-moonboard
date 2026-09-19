"""LB-12 native producer/input contract checks."""

from scripts.bolted_candidate_native_contract import CANONICAL_CASES, validate_contract


def test_native_contract_preserves_all_six_case_ids_and_panel_scope() -> None:
    result = validate_contract()
    assert tuple(result["canonical_cases"]) == CANONICAL_CASES
    assert result["case_count"] == 6
    assert result["panel_connection_count"] == 66
    assert result["structural_screw_macros_remaining"] == []


def test_native_contract_is_explicitly_not_ready_for_a_solve() -> None:
    result = validate_contract()
    assert result["native_ready"] is False
    assert result["no_native_cases_run"] is True
    assert "adapter" in result["native_blocker"]
    assert len(result["required_artifacts_per_case"]) >= 5
