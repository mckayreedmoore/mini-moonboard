"""PB-02 stock sidecar accounting and boundary checks."""

import pytest

from scripts.simple_center_stock_yield import cut_yield, report, side_rip


def test_trial_cut_yield_accounts_for_each_kerf_and_remainder():
    result = report()
    four = result["four_by_four_8ft"]
    two = result["two_by_four_8ft"]
    assert four["cut_lengths_mm"] == [238.9, 183.0]
    assert four["crosscuts"] == 2
    assert four["total_crosscut_kerf_mm"] == 6.4
    assert four["remainder_mm"] == pytest.approx(2010.1)
    assert four["length_feasible"] is True
    assert two["total_crosscut_kerf_mm"] == 3.2
    assert two["remainder_mm"] == pytest.approx(1975.2)
    assert result["two_by_four_lowes_kd_min_7_72ft"]["remainder_mm"] == pytest.approx(
        1889.856
    )


def test_rip_accounts_for_kerf_and_rejects_too_narrow_blank():
    assert side_rip() == {
        "blank_depth_mm": 88.9,
        "finished_depth_mm": 56.8,
        "rip_kerf_mm": 3.2,
        "offcut_width_mm": 28.9,
        "section_feasible": True,
    }
    assert side_rip(blank_depth_mm=59, kerf_mm=3.2)["section_feasible"] is False


def test_cut_yield_flags_short_stock_and_rejects_invalid_inputs():
    assert cut_yield(100, [99], kerf_mm=3.2)["length_feasible"] is False
    with pytest.raises(ValueError):
        cut_yield(100, [0])
    with pytest.raises(ValueError):
        cut_yield(100, [10], kerf_mm=-1)
