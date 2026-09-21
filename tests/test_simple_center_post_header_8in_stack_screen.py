"""PB-02 axial feasibility, without treating nominal length as delivery."""

import pytest

from scripts.simple_center_post_header_8in_stack_screen import screen


def test_two_grips_have_distinct_8_in_outcomes():
    cases = screen()
    for lead in ("everbilt_800696", "prime_line_9058821"):
        long = cases["grip_202_mm"][lead]
        short = cases["grip_182_mm"][lead]
        assert long["thin_washer_seating"]["minimum_grip_seating_margin_in"] > 0
        assert long["thick_washer_tip"]["maximum_grip_tip_projection_margin_in"] < 0
        assert long["passes_assumed_interval"] is False
        assert short["passes_assumed_interval"] is True
        assert short["thick_washer_tip"][
            "maximum_grip_tip_projection_margin_in"
        ] == pytest.approx(0.134646, abs=1e-6)
    assert cases["grip_182_mm"]["prime_line_9058821"]["thin_washer_seating"][
        "minimum_grip_seating_margin_in"
    ] == pytest.approx(0.215354, abs=1e-6)
    long = cases["grip_202_mm"]["illustrative_one_inch_tip_thread"]
    assert long["9_in"]["minimum_grip_seating_margin_in"] == pytest.approx(
        0.002756, abs=1e-6
    )
    assert long["9_in"]["passes_assumed_interval"] is True
    assert long["10_in"]["minimum_grip_seating_margin_in"] < 0
    assert long["10_in"]["passes_assumed_interval"] is False
    assert cases["selected_purchase"] is False
    assert cases["drilling_released"] is False
