"""One authenticated case, two exact pocket depths, and explicit open modes."""

import math

import pytest

from scripts import simple_pb04_pocket_local_screen as local


@pytest.fixture(scope="module")
def result():
    return local.screen()


def test_pocket_sections_and_no_force_cancellation(result):
    assert result["case"] == "a12-forward"
    assert len(result["stations"]) == 6
    assert any(
        sum(math.dist(bolt["force_on_block_xyz_n"], (0, 0, 0)) for bolt in row["bolts"])
        > math.dist(row["pair"]["signed_force_on_block_xyz_n"], (0, 0, 0)) + 1
        for row in result["stations"]
    )
    for row in result["stations"]:
        assert len(row["bolts"]) == 2
        assert row["pair"]["absolute_grain_force_n"] >= abs(
            row["pair"]["signed_grain_force_n"]
        )
        assert row["pair"]["moment_magnitude_nmm"] > 0
        original, deeper = row["sections"]["36.9824"], row["sections"]["37.9824"]
        assert deeper["exact_net_area_mm2"] < original["exact_net_area_mm2"]
        assert deeper["net_tension_reference_n"] < original["net_tension_reference_n"]
        assert deeper["pocket_depth_mm"] == pytest.approx(37.9824)
        assert original["exact_net_area_mm2"] == pytest.approx(6274.12004)
        assert deeper["exact_net_area_mm2"] == pytest.approx(6256.22004)
        assert row["intervening_rail_bore_section"][
            "exact_net_area_mm2"
        ] == pytest.approx(7126.605)
        assert deeper["pocket_depth_mm"] - original["pocket_depth_mm"] == pytest.approx(
            1
        )
        assert (
            row["detached_37_9824_cut_block_volume_mm3"] < row["cut_block_volume_mm3"]
        )
        assert row["cut_block_volume_mm3"] < row["gross_block_volume_mm3"]
        assert row["net_section_fully_rated"] is False
        assert row["net_reference_gate"]["exceeds_reference"] is False
        assert row["net_reference_gate"]["ratios_by_depth"]["37.9824"] < 1
        assert row["block_shear_rated"] is False
        assert row["near_hole_splitting_rated"] is False


def test_development_decision_preserves_joint_gates(result):
    assert result["development_decision"] == "REVISE_LOCAL_CHECKS"
    assert result["physical_revision_selected"] is False
    assert "exact centroid and second moments" in result["next_calculation"]
    assert result["qualified_for_design"] is False
    assert result["structural_released"] is False
    assert "torsion" in result["unqualified_modes"]
    assert "other five cases" in result["unqualified_modes"]


def test_reference_exceedance_is_a_reported_isolated_gate():
    gate = local._net_reference_gate(11, {"installed": {"net_tension_reference_n": 10}})
    assert gate["exceeds_reference"] is True
    assert gate["ratios_by_depth"]["installed"] == pytest.approx(1.1)
    assert "joint interaction open" in gate["scope"]
    assert local._development_decision([{"net_reference_gate": gate}]) == (
        "REJECT_POCKETED_NET_REFERENCE"
    )
