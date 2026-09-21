"""PB02 stiffness sensitivity remains compatible, source-bound, and provisional."""

import numpy as np
import pytest

from scripts.simple_center_connected_kinematics import constraint_rows
from scripts.simple_center_pb02_geometry import ACTIVE_FINGERPRINT
from scripts.simple_center_stiffness_sensitivity import (
    SCENARIOS,
    _validate_self_equilibrium,
    screen,
)


def test_compatibility_sensitivity_converges_and_preserves_equilibrium():
    result = screen()

    assert result["source_fingerprint"] == ACTIVE_FINGERPRINT
    assert result["case_count"] == 5
    assert result["attempted_scenario_count"] == 50
    assert result["converged_scenario_count"] == 50
    assert [row["name"] for row in result["scenarios"]] == [row[0] for row in SCENARIOS]
    for solved in result["results"]:
        assert solved["equilibrium"]["maximum_force_residual_n"] < 1e-5
        assert solved["equilibrium"]["maximum_moment_residual_nmm"] < 1e-3
        assert solved["equilibrium"]["constitutive_law_passed"] is True
        assert solved["seed_optimizer"]["active_tangent_rank"] == 36
        assert len(solved["rows"]) == 58
        assert len({row["name"] for row in solved["rows"]}) == 58

    sensitivity = result["fixed_case_stiffness_sensitivity"]
    controlling = sensitivity["a12-rear"]["principal_block_principal"]
    assert controlling["total_bolt_tension_n"]["maximum_to_minimum"] == pytest.approx(
        1.478677614
    )

    for case in sensitivity.values():
        assert case["post_block"]["total_bolt_tension_n"][
            "maximum_to_minimum"
        ] == pytest.approx(1.0, abs=1e-9)

    singular_traversals = {
        (solved["case"], solved["scenario"]): solved["seed_optimizer"][
            "singular_refinement_advances"
        ]
        for solved in result["results"]
        if solved["seed_optimizer"]["singular_refinement_advances"]
    }
    assert singular_traversals == {
        ("a1-rear", "bolt_dominant_contrast"): 1,
        ("a12-left", "bolt_dominant_contrast"): 1,
        ("k12-rear", "bolt_dominant_contrast"): 1,
    }

    assert "cross_case_and_scenario_reaction_envelopes" in result
    assert result["strength_or_fabrication_release"] is False


def test_rows_have_complete_physical_metadata():
    rows = constraint_rows(closed=())
    assert len(rows) == 30
    for row in rows:
        assert {"first", "second", "direction", "point_mm"} <= set(row)
        assert len(row["direction"]) == len(row["point_mm"]) == 3


def test_non_self_equilibrated_fixture_is_rejected():
    load = np.zeros(42)
    load[6] = 1
    with pytest.raises(ValueError, match="not self-equilibrated"):
        _validate_self_equilibrium(load)
