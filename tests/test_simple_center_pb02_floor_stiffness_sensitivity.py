"""PB02 floor-stiffness sensitivity stays evidence-bound and non-releasing."""

import copy

import pytest

from scripts import simple_center_pb02_floor_stiffness_sensitivity as sensitivity


def test_retained_evidence_reports_only_10k_and_fails_closed_on_missing_trials():
    result = sensitivity.evaluate()

    assert result["status"] == "insufficient_authenticated_stiffness_evidence"
    assert result["trial_floor_contact_n_per_mm"] == [5000.0, 10000.0, 20000.0]
    assert result["available_authenticated_trials"] == [10000.0]
    assert result["missing_authenticated_trials"] == [5000.0, 20000.0]
    assert result["comparison"]["complete"] is False
    assert result["comparison"]["material_change_conclusion"] == "not_evaluated"

    baseline = result["trials"]["10000"]
    assert baseline["evidence_status"] == "authenticated_retained_suite"
    assert baseline["accepted_case_count"] == 6
    assert baseline["governing_identities"]["bolt_combined_demand"] == {
        "name": "principal_block_principal/bolt_1",
        "case": "a12-rear",
    }
    assert baseline["governing_ratios"]["individual_wood_yield"] == pytest.approx(
        0.1998376485
    )
    assert result["floor_stiffness_is_physical_property"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def test_complete_comparison_detects_identity_ratio_and_signed_action_changes():
    baseline = sensitivity._retained_baseline_record()
    low = copy.deepcopy(baseline)
    high = copy.deepcopy(baseline)
    high["governing_identities"]["bolt_combined_demand"]["case"] = "a12-left"
    high["governing_ratios"]["direct_shaft"] *= 1.06
    action_name = next(iter(high["signed_actions_n_or_nmm"]))
    high["signed_actions_n_or_nmm"][action_name] += 10.0

    comparison = sensitivity._compare_records(
        {5000.0: low, 10000.0: baseline, 20000.0: high}
    )

    assert comparison["complete"] is True
    assert comparison["governing_identity_changed"] is True
    assert comparison["governing_ratio_materially_changed"] is True
    assert comparison["signed_action_materially_changed"] is True
    assert comparison["material_change_conclusion"] == "material_change_detected"


def test_small_complete_changes_are_reported_as_not_material_by_numerical_rule():
    baseline = sensitivity._retained_baseline_record()
    low = copy.deepcopy(baseline)
    high = copy.deepcopy(baseline)
    high["governing_ratios"]["direct_shaft"] *= 1.01
    action_name = max(
        baseline["signed_actions_n_or_nmm"],
        key=lambda name: abs(baseline["signed_actions_n_or_nmm"][name]),
    )
    high["signed_actions_n_or_nmm"][action_name] *= 1.01

    comparison = sensitivity._compare_records(
        {5000.0: low, 10000.0: baseline, 20000.0: high}
    )

    assert comparison["complete"] is True
    assert comparison["governing_identity_changed"] is False
    assert comparison["governing_ratio_materially_changed"] is False
    assert comparison["signed_action_materially_changed"] is False
    assert comparison["material_change_conclusion"] == "no_material_change_by_rule"


def test_external_suite_contract_rejects_missing_summary(tmp_path):
    with pytest.raises(ValueError, match="suite summary is missing"):
        sensitivity._authenticate_external_suite(tmp_path, 5000.0)


def test_only_prescribed_trial_values_are_accepted(tmp_path):
    with pytest.raises(ValueError, match="prescribed trial"):
        sensitivity.evaluate({7500.0: tmp_path})
