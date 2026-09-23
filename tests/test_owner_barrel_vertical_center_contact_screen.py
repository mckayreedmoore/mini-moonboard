"""Regression tests for signed vertical-barrel contact equilibrium."""

import math
from unittest.mock import patch

import pytest

from scripts import owner_barrel_vertical_center_contact_screen as contact


@pytest.fixture(scope="module")
def report():
    return contact.build_report()


def test_exact_combined_cut_contact_geometry_is_pinned(report):
    assert report["case_count"] == 14
    for side, geometry in report["contact_geometry"].items():
        assert geometry["gross_area_mm2"] == pytest.approx(5113.121681)
        assert geometry["net_area_mm2"] == pytest.approx(5024.764388)
        assert geometry["cell_area_sum_mm2"] == pytest.approx(geometry["net_area_mm2"])
        assert geometry["cell_count"] == 16
        expected_x = -70.0 if side == "left" else 70.0
        assert geometry["net_centroid_xyz_mm"] == pytest.approx(
            [expected_x, -108.644361, 277.0], abs=1e-6
        )
        if side == "left":
            assert geometry["x_centroid_range_mm"] == pytest.approx(
                [-80.114095, -59.885905], abs=1e-6
            )
        else:
            assert geometry["x_centroid_range_mm"] == pytest.approx(
                [59.885905, 80.114095], abs=1e-6
            )
        assert geometry["y_centroid_range_mm"] == pytest.approx(
            [-167.312333, -49.884998], abs=1e-6
        )


def test_signed_two_bolt_and_face_contact_path_resolves_my(report):
    summary = report["summary"]
    assert summary["all_vertical_equilibria_feasible"]
    assert summary["all_equilibrium_residuals_pass"]
    assert summary["maximum_adapted_reference_utilization"] == pytest.approx(0.63726)
    assert summary["maximum_case"] == {
        "source_group": "a1_rear_sensitivity",
        "series": "proxy-scale0p1",
        "case": "a1-rear",
        "side": "left",
    }
    assert summary["my_path"] == "EXISTS_IN_SIGNED_PROXY_EQUILIBRIUM"
    assert report["decision"]["my_topology_screen"] == ("PATH_EXISTS_REFERENCE_ONLY")


def test_governing_static_witness_is_pinned(report):
    governing = next(
        row
        for row in report["cases"]
        if all(
            row[key] == value
            for key, value in report["summary"]["maximum_case"].items()
        )
    )["vertical_contact_tension"]
    assert governing["target_fz_mx_my"] == pytest.approx(
        [613.752541, 34798.062199, 10589.378494], abs=1e-6
    )
    assert governing["bolt_tension_n"] == pytest.approx(
        [220.475915, 220.475915], abs=1e-6
    )
    assert governing["contact_total_n"] == pytest.approx(1054.704371, abs=1e-6)
    assert governing["contact_resultant_xyz_mm"] == pytest.approx(
        [-80.040139, -73.00681, 277.0], abs=1e-6
    )
    assert governing["maximum_piecewise_uniform_cell_pressure_mpa"] == pytest.approx(
        2.746095
    )
    assert governing["equilibrium_residual_fz_mx_my"] == pytest.approx(
        [0.0, 0.0, 0.0], abs=1e-9
    )


def test_lateral_row_resolution_is_equilibrated_but_not_qualified(report):
    assert report["summary"]["maximum_lateral_row_resultant_n"] == pytest.approx(
        88.465028
    )
    pitch = 80.0
    for case in report["cases"]:
        force = case["shifted_force_xyz_n"]
        moment = case["shifted_moment_xyz_nmm"]
        lateral = case["lateral_two_row_resolution"]
        rear = lateral["rear_force_xy_n"]
        forward = lateral["forward_force_xy_n"]
        assert rear[0] + forward[0] == pytest.approx(force[0], abs=2e-6)
        assert rear[1] + forward[1] == pytest.approx(force[1], abs=2e-6)
        assert (rear[0] - forward[0]) * pitch / 2 == pytest.approx(moment[2], abs=5e-5)
        assert lateral["maximum_resultant_n"] == pytest.approx(
            max(math.hypot(*rear), math.hypot(*forward)), abs=1e-6
        )
        assert lateral["capacity_qualified"] is False


def test_screen_remains_fail_closed(report):
    assert report["model"]["compatibility_or_stiffness_solved"] is False
    assert report["summary"]["fresh_barrel_case_count"] == 0
    assert report["summary"]["missing_case"] == "a12-forward"
    decision = report["decision"]
    assert decision["finite_decision"] == "EVIDENCE_BLOCKED"
    assert not decision["diy_ready"]
    assert not decision["drilling_released"]
    assert not decision["fabrication_released"]
    assert not decision["structural_released"]
    assert any("stiffness" in limit for limit in report["limits"])
    assert any("splitting" in limit for limit in report["limits"])


def test_nominal_geometry_has_full_wrench_rank_and_required_levers(report):
    for topology in report["topology"].values():
        assert topology["nominal_six_dof_wrench_matrix_rank"] == 6
        assert topology["rank_with_contact_x_collapsed_to_bolt_axis"] == 5
        assert topology["rank_with_bolt_rows_collapsed_to_group_y"] == 5
    ranges = report["summary"]["available_proxy_action_ranges"]
    assert ranges["my_nmm"][0] < 0 < ranges["my_nmm"][1]
    assert ranges["fz_n"][0] > 0
    assert ranges["mx_nmm"][0] > 0


def test_infeasible_contact_case_fails_closed_without_report_crash():
    with patch.object(
        contact,
        "_solve_vertical",
        return_value={
            "feasible": False,
            "solver_status": 2,
            "solver_message": "synthetic infeasible topology",
        },
    ):
        blocked = contact.build_report()
    assert not blocked["summary"]["all_vertical_equilibria_feasible"]
    assert not blocked["summary"]["all_equilibrium_residuals_pass"]
    assert blocked["summary"]["maximum_adapted_reference_utilization"] is None
    assert blocked["summary"]["maximum_case"] is None
    assert blocked["summary"]["my_path"] == "NO_PATH_IN_SCREEN"
    assert blocked["decision"]["my_topology_screen"] == "NO_PATH_IN_SCREEN"
    assert blocked["decision"]["finite_decision"] == "EVIDENCE_BLOCKED"
