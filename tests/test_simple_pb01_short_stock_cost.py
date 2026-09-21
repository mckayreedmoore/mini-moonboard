"""Bounded PB01 stock and cost arithmetic; no purchasing or fabrication output."""

import pytest

from scripts.simple_pb01_short_stock_cost import report, yield_from_stick


def test_length_yield_charges_each_crosscut_and_rejects_extra_blank():
    short = yield_from_stick(2438.4, 152.4, 3.2)
    old = yield_from_stick(2438.4, 300, 3.2)
    assert (short["blanks"], short["used_mm"], short["remainder_mm"]) == pytest.approx(
        (15, 2334, 104.4)
    )
    assert (old["blanks"], old["used_mm"], old["remainder_mm"]) == pytest.approx(
        (8, 2425.6, 12.8)
    )
    assert 16 * (152.4 + 3.2) > 2438.4
    assert 9 * (300 + 3.2) > 2438.4


def test_trim_sensitivity_and_invalid_lengths():
    assert yield_from_stick(2438.4, 300, 3.2, 25.4)["blanks"] == 7
    assert yield_from_stick(2438.4, 152.4, 3.2, 25.4)["blanks"] == 15
    assert yield_from_stick(2438.4, 152.4, 3.2, 105)["blanks"] == 14
    with pytest.raises(ValueError):
        yield_from_stick(100, 0, 3.2)
    with pytest.raises(ValueError):
        yield_from_stick(100, 10, -1)


def test_rip_and_cost_boundary():
    result = report()
    assert result["lowes"]["stock_section_mm"] == pytest.approx([90.4748, 142.875])
    assert result["lowes"]["depth_offcut_after_rip_kerf_mm"] == pytest.approx(30.1248)
    assert result["lowes"]["width_to_remove_mm"] == pytest.approx(3.175)
    assert result["home_depot_assumed"][
        "depth_offcut_after_rip_kerf_mm"
    ] == pytest.approx(28.55)
    assert result["volume_reduction_percent"] == pytest.approx(49.2)
    assert result["hardware_change_usd"] == 0
    assert result["board_checkout_usd"] is None
