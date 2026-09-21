"""PB02 axis-parallel/end-grain calculation remains explicit and bounded."""

import hashlib
import json

import pytest

from scripts import simple_center_pb02_end_grain_screen as end_grain


def test_root_sensitivities_retain_z_grain_block_for_development():
    result = end_grain.screen()
    typical = result["cases"]["typical_root"]
    smaller = result["cases"]["smaller_root_sensitivity"]

    assert result["interface"] == "block_header"
    assert result["evidence_report"] == (
        "fea/results/diagnostics/pb02-contact-refinement-a12-forward-v1/"
        "density-2x/report.json"
    )
    assert result["authentication"] == {
        "candidate": "pb02-kerf-right-native-development-only",
        "case": "a12-forward",
        "contact_grid": [8, 8],
        "mean_contact_total_n_per_mm": 2000.0,
        "report_sha256": end_grain.EXPECTED_REPORT_SHA256,
        "model_identity": end_grain.EXPECTED_MODEL_IDENTITY,
        "diagnostic_scope_fingerprint": end_grain.EXPECTED_SCOPE_FINGERPRINT,
        "active_geometry_fingerprint": end_grain.EXPECTED_GEOMETRY_FINGERPRINT,
        "numerically_accepted": True,
        "no_release": True,
    }
    assert result["demand_by_bolt_n"] == pytest.approx(
        {"bolt_1": 18.11806500953031, "bolt_2": 35.81052578517264}
    )
    assert result["pair_geometry"]["spacing_mm"] == pytest.approx(30.55360044)
    assert result["pair_geometry"]["spacing_nominal_diameters"] > 4.8
    assert result["pair_geometry"]["force_angle_from_pair_line_degrees"] == (
        pytest.approx({"bolt_1": 76.78127701, "bolt_2": 19.92493954})
    )
    assert result["adjustments"] == {
        "end_grain_factor": 0.67,
        "geometry_factor": 1.0,
        "group_factor": None,
        "group_factor_applicable": False,
        "group_factor_reason": result["adjustments"]["group_factor_reason"],
    }
    assert typical["bearing_psi"] == 4650
    assert typical["yield_moment_lb_in"] == pytest.approx(50.6345175)
    assert typical["reduction_term"] == pytest.approx(2.9875)
    assert typical["governing_mode"] == "IV"
    assert typical["reference_lateral_lbf"] == pytest.approx(99.8591351)
    assert typical["end_grain_adjusted_reference_n"] == pytest.approx(297.6110275)
    assert typical["single_case_demand_n"] == pytest.approx(35.81052579)
    assert typical["demand_ratio"] == pytest.approx(0.12032661)
    assert typical["individual_bolt_demand_ratios"] == pytest.approx(
        {"bolt_1": 0.06087834, "bolt_2": 0.12032661}
    )

    assert smaller["yield_moment_lb_in"] == pytest.approx(43.74)
    assert smaller["reduction_term"] == pytest.approx(2.875)
    assert smaller["governing_mode"] == "IV"
    assert smaller["reference_lateral_lbf"] == pytest.approx(94.1194254)
    assert smaller["end_grain_adjusted_reference_n"] == pytest.approx(280.5049219)
    assert smaller["demand_ratio"] == pytest.approx(0.12766452)
    assert smaller["individual_bolt_demand_ratios"] == pytest.approx(
        {"bolt_1": 0.06459090, "bolt_2": 0.12766452}
    )
    assert result["rating_or_drilling_release"] is False


def _mutated_report(tmp_path, monkeypatch, mutate):
    report = json.loads(end_grain.EVIDENCE_REPORT.read_text())
    mutate(report)
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    monkeypatch.setattr(end_grain, "EVIDENCE_REPORT", path)
    monkeypatch.setattr(
        end_grain,
        "EXPECTED_REPORT_SHA256",
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda report: report["diagnostic_scope"].update(case="a12-rear"),
        lambda report: report.update(candidate="other-candidate"),
        lambda report: report.update(pb02_model_identity="changed"),
        lambda report: report.update(numerically_accepted=False),
        lambda report: report.update(actual_joint_demands_qualified=True),
        lambda report: report.update(qualified_for_design=True),
        lambda report: report.update(drilling_released=True),
        lambda report: report.update(fabrication_released=True),
        lambda report: report.update(structural_released=True),
        lambda report: report["source_sha256"].update(
            {end_grain.GEOMETRY_SOURCE: "changed"}
        ),
    ],
)
def test_end_grain_evidence_authentication_fails_closed(tmp_path, monkeypatch, mutate):
    _mutated_report(tmp_path, monkeypatch, mutate)

    with pytest.raises(ValueError, match="authentication changed"):
        end_grain.screen()
