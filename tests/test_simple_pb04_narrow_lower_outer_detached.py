"""Direct one-station geometry and nominal stack regression."""

import pytest

from scripts import simple_pb04_narrow_lower_outer_detached as trial


def test_narrow_lower_outer_station():
    original = (trial.lower.BLOCK_X_MM, trial.lower.RAIL_X_OFFSETS_MM)
    result = trial.screen()
    assert (trial.lower.BLOCK_X_MM, trial.lower.RAIL_X_OFFSETS_MM) == original
    assert result["block_dimensions_mm"] == pytest.approx([95.25, 57.15, 300])
    assert result["original_upright_wood_grip_mm"] == pytest.approx(228.6)
    assert result["layout"]["rail_x_offsets_from_butt_mm"] == pytest.approx((25, 70))
    assert result["layout"]["rail_center_spacing_mm"] == pytest.approx(45)
    assert result["layout"]["rail_tool_edge_reserves_mm"] == pytest.approx((5, 5.25))
    assert result["stack"]["wood_grip_mm"] == pytest.approx(184.15)
    assert result["stack"]["nominal_margin_mm"] == pytest.approx(7.4676)
    assert result["stack"]["conditional_margin_mm"] == pytest.approx(2.8956)
    assert result["stack"]["conditional_case_is_product_tolerance"] is False
    assert all(result["gates"].values()), result
    assert result["decision"] == "ADVANCE_GEOMETRY_ONLY"
    assert result["old_force_transfer"] is False
    assert result["solve_run"] is False
    assert result["fabrication_released"] is False
