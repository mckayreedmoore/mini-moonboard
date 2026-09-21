"""PB02 axis-parallel/end-grain calculation remains explicit and bounded."""

import pytest

from scripts.simple_center_pb02_end_grain_screen import screen


def test_root_sensitivities_retain_z_grain_block_for_development():
    result = screen()
    typical = result["cases"]["typical_root"]
    smaller = result["cases"]["smaller_root_sensitivity"]

    assert result["interface"] == "block_header"
    assert typical["bearing_psi"] == 4650
    assert typical["yield_moment_lb_in"] == pytest.approx(50.6345175)
    assert typical["reduction_term"] == pytest.approx(2.9875)
    assert typical["governing_mode"] == "IV"
    assert typical["reference_lateral_lbf"] == pytest.approx(99.8591351)
    assert typical["end_grain_adjusted_reference_n"] == pytest.approx(297.6110275)
    assert typical["single_case_demand_n"] == pytest.approx(33.76660634)
    assert typical["demand_ratio"] == pytest.approx(0.11345885)

    assert smaller["yield_moment_lb_in"] == pytest.approx(43.74)
    assert smaller["reduction_term"] == pytest.approx(2.875)
    assert smaller["governing_mode"] == "IV"
    assert smaller["reference_lateral_lbf"] == pytest.approx(94.1194254)
    assert smaller["end_grain_adjusted_reference_n"] == pytest.approx(280.5049219)
    assert smaller["demand_ratio"] == pytest.approx(0.12037795)
    assert result["rating_or_drilling_release"] is False
