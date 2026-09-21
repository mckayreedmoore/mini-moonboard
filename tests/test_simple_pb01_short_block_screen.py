"""Bounded 152.4-mm PB01 geometry trial."""

import pytest

from scripts.simple_pb01_short_block_screen import screen


def test_short_block_keeps_fixed_interfaces_and_reports_open_gates():
    result = screen()
    geometry = result["geometry"]
    assert geometry["before_x_t_n_mm"] == [139.7, 57.15, 300]
    assert geometry["trial_x_t_n_mm"] == [139.7, 57.15, 152.4]
    assert geometry["front_n_mm"] == pytest.approx(209.841, abs=0.001)
    assert geometry["upright_bolt_n_mm"] == [265, 310]
    assert geometry["rail_bolt_n_mm"] == [290, 290]
    assert geometry["rail_bolt_x_mm"] == [70, 110]
    assert geometry["trial_rear_end_from_last_upright_bolt_mm"] == pytest.approx(
        52.241, abs=0.001
    )
    assert geometry["conditional_7d_rear_reserve_mm"] == pytest.approx(7.791, abs=0.001)
    assert geometry["fixed_panel_axes"] == 66
    assert geometry["bore_diameter_mm_trial_not_drill_instruction"] == 7.5
    assert geometry["contact_area_trial_mm2"] == geometry["contact_area_before_mm2"]
    assert geometry["status"] == "diagnostic_pose_only"
    assert geometry["parent_clashes_mm3"] == {}
    assert geometry["panel_clashes_mm3"] == {}
    assert geometry["host_clashes_mm3"] == {}
    assert result["member"]["conditional_only"] is True
    assert result["member"]["joint_capacity_lbf"] is None
    assert (
        result["member"]["before_components_lbf"]
        == result["member"]["trial_components_lbf"]
    )
    assert result["member"]["rear_end_and_bored_section_check_complete"] is False
    assert result["stack"]["grips_unchanged_mm"] == {
        "u1": 182.8,
        "u2": 182.8,
        "r1": 100.25,
        "r2": 100.25,
    }
    assert result["stack"]["wood_grips_mm"] == {"upright": 177.8, "rail": 95.25}
    assert result["cost"]["volume_reduction_percent"] == 49.2
    assert result["cost"]["installed_cost_usd"] is None
    assert result["native_forces_transferred"] is False
    assert result["joint_accepted"] is False
