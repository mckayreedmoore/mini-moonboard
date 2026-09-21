"""PB02 axis-parallel/end-grain calculation remains explicit and bounded."""

import pytest

from scripts.simple_center_pb02_end_grain_screen import screen


def test_root_sensitivities_retain_z_grain_block_for_development():
    result = screen()
    typical = result["cases"]["typical_root"]
    smaller = result["cases"]["smaller_root_sensitivity"]

    assert result["interface"] == "block_header"
    assert result["demand_by_bolt_n"] == pytest.approx(
        {"bolt_1": 16.35670906081702, "bolt_2": 33.76660633999291}
    )
    assert result["pair_geometry"]["spacing_mm"] == pytest.approx(30.55360044)
    assert result["pair_geometry"]["spacing_nominal_diameters"] > 4.8
    assert result["pair_geometry"]["force_angle_from_pair_line_degrees"] == (
        pytest.approx({"bolt_1": 78.18151, "bolt_2": 20.40886})
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
    assert typical["single_case_demand_n"] == pytest.approx(33.76660634)
    assert typical["demand_ratio"] == pytest.approx(0.11345885)
    assert typical["individual_bolt_demand_ratios"] == pytest.approx(
        {"bolt_1": 0.05496004, "bolt_2": 0.11345885}
    )

    assert smaller["yield_moment_lb_in"] == pytest.approx(43.74)
    assert smaller["reduction_term"] == pytest.approx(2.875)
    assert smaller["governing_mode"] == "IV"
    assert smaller["reference_lateral_lbf"] == pytest.approx(94.1194254)
    assert smaller["end_grain_adjusted_reference_n"] == pytest.approx(280.5049219)
    assert smaller["demand_ratio"] == pytest.approx(0.12037795)
    assert smaller["individual_bolt_demand_ratios"] == pytest.approx(
        {"bolt_1": 0.05831167, "bolt_2": 0.12037795}
    )
    assert result["rating_or_drilling_release"] is False
