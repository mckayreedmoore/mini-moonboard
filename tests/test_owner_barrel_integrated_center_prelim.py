"""Conditional, source-bound components for the revised principal/header pair."""

import pytest

from scripts import owner_barrel_integrated_center_prelim as preliminary


@pytest.fixture(scope="module")
def result():
    return preliminary.report()


def test_actual_joint_geometry_and_2024_material_basis(result):
    assert result["edition"] == "2024 NDS / 2024 NDS Supplement"
    assert result["source_station"] == "clip_split_base_center_right"
    geometry = result["geometry"]
    assert geometry["principal_section_x_n_mm"] == pytest.approx([38.1, 139.7])
    assert geometry["row_axis_pitch_mm"] == pytest.approx(20.706, abs=0.01)
    assert geometry["opposing_barrel_bore_cap_x_gap_mm"] == pytest.approx(3.998)
    assert [row["nominal_bolt_length_mm"] for row in geometry["rows"]] == pytest.approx(
        [127.0, 114.3]
    )
    assert all(row["bore_past_nominal_tip_mm"] == 4.0 for row in geometry["rows"])


def test_separate_component_scales_and_unknown_complete_resistance(result):
    wood = result["wood"]
    assert wood["ideal_washer_fc_perp_n_per_bolt"] == pytest.approx(1037, rel=0.01)
    assert wood["nominal_dowel_bearing_psi"] == {
        "parallel": 5600.0,
        "perpendicular": 4450.0,
    }
    section = wood["sampled_principal_net_section"]
    assert section["gross_area_mm2"] == pytest.approx(5322.57, abs=0.01)
    assert 5000 < section["minimum_sampled_net_area_mm2"] < 5100
    assert section["minimum_sampled_net_area_mm2"] < section["gross_area_mm2"]
    assert section["minimum_sampled_net_area_mm2"] == pytest.approx(5034.615, abs=0.1)
    assert section["unadjusted_Ft_times_sampled_area_n"] == pytest.approx(
        19959.659, abs=0.5
    )
    assert wood["two_full_slot_parallel_tension_sensitivity_n"] == pytest.approx(
        18078.017, abs=0.1
    )
    assert len(result["lateral_yield_surrogate"]["rows"]) == 2
    for row in result["lateral_yield_surrogate"]["rows"]:
        assert set(row["directions"]) == {"across_x", "transverse_yz"}
        assert all(
            case["one_bolt_reference_n"] > 0 for case in row["directions"].values()
        )
    assert [
        row["directions"]["across_x"]["one_bolt_reference_n"]
        for row in result["lateral_yield_surrogate"]["rows"]
    ] == pytest.approx([444.196, 352.017], abs=0.02)
    assert (
        result["lateral_yield_surrogate"]["actual_bearing_lengths_qualified"] is False
    )
    assert result["lateral_yield_surrogate"]["actual_barrel_joint_rating_n"] is None
    assert result["bolt_shaft"]["actual_axial_resistance_n"] is None
    assert result["barrel_thread"]["verified_resistance_n"] is None
    assert result["axial_withdrawal"]["complete_path_resistance_n"] is None
    assert result["stiffness"]["complete_joint_n_per_mm"] is None
    assert result["stiffness"]["steel_only_nominal_shank_n_per_mm"] == pytest.approx(
        63867.444, abs=0.1
    )
    assert result["group_action"]["two_bolt_resistance_n"] is None
    assert result["actual_new_topology_joint_demands"] is None
    assert not any(result["release_flags"].values())
