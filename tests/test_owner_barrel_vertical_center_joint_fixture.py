"""Tests for the reduced two-vertical-bolt compatibility fixture."""

import numpy as np
import pytest

from scripts import owner_barrel_vertical_center_joint_fixture as fixture


def _small_geometry():
    cells = []
    for index, (x, y) in enumerate(
        ((-20, -146), (20, -146), (-20, -66), (20, -66))
    ):
        cells.append(
            {
                "name": f"cell_{index}",
                "point_xyz_mm": [x, y, fixture.INTERFACE_Z_MM],
                "tributary_area_mm2": 100.0,
            }
        )
    bolts = [
        {"thread_axis_xyz_mm": [0.0, y, fixture.THREAD_Z_MM]}
        for y in (-146.0, -66.0)
    ]
    return {"cells": cells, "bolts": bolts}


def test_point_matrix_uses_scaled_rigid_rotation():
    origin = np.asarray((0.0, 0.0, 0.0))
    point = np.asarray((0.0, 100.0, 0.0))
    q = np.asarray((0.0, 0.0, 0.0, 0.1, 0.0, 0.0))
    displacement = fixture._point_matrix(point, origin) @ q
    # q_rx=0.1 mm-equivalent means theta_x=0.001 rad.
    assert displacement == pytest.approx([0.0, 0.0, 0.1])


def test_tension_and_compression_are_one_sided():
    geometry = _small_geometry()
    scenario = fixture.STIFFNESS_SCENARIOS[1]
    upward = fixture.solve_wrench(
        geometry, (0, 0, 100), (0, 0, 0), scenario, 0.0
    )
    downward = fixture.solve_wrench(
        geometry, (0, 0, -100), (0, 0, 0), scenario, 0.0
    )
    assert upward["converged"]
    assert downward["converged"]
    assert sum(row["tension_n"] for row in upward["bolts"]) == pytest.approx(100)
    assert upward["contact_total_n"] == pytest.approx(0)
    assert sum(row["tension_n"] for row in downward["bolts"]) == pytest.approx(0)
    assert downward["contact_total_n"] == pytest.approx(100)


def test_circular_clearance_is_taken_up_before_shear():
    geometry = _small_geometry()
    scenario = fixture.STIFFNESS_SCENARIOS[1]
    solved = fixture.solve_wrench(
        geometry,
        (100, 0, 0),
        (0, 0, 0),
        scenario,
        fixture.NOMINAL_CENTERED_CLEARANCE_MM,
    )
    assert solved["converged"]
    assert solved["translation_xyz_mm"][0] > fixture.NOMINAL_CENTERED_CLEARANCE_MM
    assert sum(row["shear_resultant_n"] for row in solved["bolts"]) == pytest.approx(
        100, abs=1e-5
    )


@pytest.fixture(scope="module")
def report():
    return fixture.build_report()


def test_actual_cut_geometry_and_signed_case_inventory(report):
    assert report["geometry"]["left"]["contact_cell_count"] >= 60
    assert report["geometry"]["left"]["net_contact_area_mm2"] == pytest.approx(
        5024.764388
    )
    assert report["load_set"]["old_combined_proxy_count"] == 28
    assert report["load_set"]["artificial_signed_component_count"] == 12
    assert report["summary"]["case_scenario_count"] == 360


def test_fixture_fails_closed(report):
    assert report["summary"]["all_positive_stiffness_cases_converged"]
    assert report["summary"]["unsupported_lower_model"] == {
        "zero_lateral_stiffness_rank_maximum": 3,
        "pure_fx_fy_mz_behavior": "UNBOUNDED_MECHANISM",
        "meaning": "No supported positive complete-joint lateral stiffness lower bound exists; the captive-barrel sensitivity cannot be promoted to a bound.",
    }
    assert report["load_set"]["fresh_48_pair_case_count"] == 0
    assert report["fresh_demand_blocker"]["status"] == "BLOCKED"
    assert report["decision"]["finite_decision"] == "BLOCKED"
    assert not report["decision"]["cad_go"]
    assert not report["decision"]["diy_ready"]
