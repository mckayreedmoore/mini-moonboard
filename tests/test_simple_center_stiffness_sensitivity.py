"""PB02 stiffness sensitivity remains compatible, source-bound, and provisional."""

import numpy as np
import pytest

from scripts.simple_center_connected_kinematics import (
    CONTACT_PARTITION,
    CONTACT_PARTITION_FINGERPRINT,
    constraint_rows,
)
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
        expected_count = 30 + CONTACT_PARTITION["contact_row_count"]
        assert len(solved["rows"]) == expected_count
        assert len({row["name"] for row in solved["rows"]}) == expected_count
        assert solved["contact_partition_fingerprint"] == (
            CONTACT_PARTITION_FINGERPRINT
        )
        density = solved["trial_stiffness_n_per_mm"]["face_contact_per_area_n_per_mm3"]
        for row in solved["rows"]:
            if row["kind"] == "contact_compression":
                assert row["stiffness_n_per_mm"] == pytest.approx(
                    density * row["tributary_area_mm2"]
                )
        assert all(
            {
                "force_resultant_n",
                "moment_resultant_about_net_centroid_nmm",
                "active_tributary_area_mm2",
                "peak_average_cell_pressure_n_per_mm2",
            }
            <= set(edge["contact_aggregation"])
            for edge in solved["edges"].values()
        )
        for edge_name, edge in solved["edges"].items():
            expected_force_on_first = -sum(
                (
                    row["signed_reaction_n"] * np.asarray(row["direction"])
                    for row in solved["rows"]
                    if row["edge"] == edge_name
                    and row["kind"] == "contact_compression"
                    and row["active"]
                ),
                np.zeros(3),
            )
            np.testing.assert_allclose(
                edge["contact_aggregation"]["force_resultant_n"],
                expected_force_on_first,
                atol=1e-9,
            )

    sensitivity = result["fixed_case_stiffness_sensitivity"]
    finite_ratios = []
    for case in sensitivity.values():
        for edge in case.values():
            for response in edge.values():
                ratio = response["maximum_to_minimum"]
                if ratio is not None:
                    assert ratio >= 1.0
                    finite_ratios.append(ratio)
    assert finite_ratios
    assert max(finite_ratios) > 1.0

    assert all(
        solved["seed_optimizer"]["singular_refinement_advances"] >= 0
        for solved in result["results"]
    )
    assert all(
        solved["seed_optimizer"]["singular_refinement_advances"] == 0
        for solved in result["results"]
    )
    governing = result["fixed_case_stiffness_sensitivity"]["a12-left"][
        "block_header"
    ]["total_contact_compression_n"]
    assert governing["maximum_to_minimum"] == pytest.approx(121.3433649445826)
    assert governing["minimum_n"] == pytest.approx(22.351300921008065)
    assert governing["maximum_n"] == pytest.approx(2712.182064644067)

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
