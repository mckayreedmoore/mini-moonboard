"""One preparation-only check for the provisional kerf-right response proxy."""

from scripts.bolted_kerf_diagnostic_probe import prepare_case


def test_prepare_one_case_without_solver():
    structure, report = prepare_case("a12-rear")
    assert report["case"] == "a12-rear"
    assert report["diagnostic_only"] is True
    assert report["provisional_structural_connectors"] == "baseline ML24Z angles and SDS screws"
    assert report["bolted_joint_demands"] is False
    assert len(report["panel_connections"]) == 66
    assert structure.panels
    for bounds in report["panel_bounds"].values():
        assert bounds["mesh_x_mm"] == bounds["actual_x_mm"] or all(
            abs(mesh-actual) < 1e-6
            for mesh, actual in zip(bounds["mesh_x_mm"], bounds["actual_x_mm"], strict=True)
        )
