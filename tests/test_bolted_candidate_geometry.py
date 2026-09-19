"""LB-08 integrated inventory and nominal-envelope checks."""

from scripts.bolted_candidate_geometry_checks import report


def test_integrated_candidate_covers_all_structural_and_panel_axes() -> None:
    result = report()
    assert result["inventory"] == {
        "structural_axes": 144,
        "panel_axes": 66,
        "retained_frame_bolts": 12,
        "structural_stations": 24,
        "prototype_joints": 24,
        "prototype_fasteners": 48,
        "prototype_interfaces": 24,
    }
    assert sum(result["family_counts"].values()) == 24


def test_geometry_report_cannot_be_misread_as_exact_fit_or_acceptance() -> None:
    result = report()
    assert result["nominal_envelope_screen"]["within_preserved_nominal_face"] is True
    assert result["nominal_envelope_screen"]["exact_solid_fit_checked"] is False
    assert result["scope_checks"]["resistance_checked"] is False
    assert result["scope_checks"]["native_cases_complete"] is False
