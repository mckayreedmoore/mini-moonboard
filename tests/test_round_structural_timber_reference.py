"""Tolerance rejection and independent section identities for the passage screen."""
import math

import pytest

from fea.round_structural_timber_reference import centered_section, dimensional_screen


def test_zero_margin_requires_actual_dimensional_acceptance():
    nominal = dimensional_screen(139.7, 38.1)
    assert nominal['dimensional_comparison_passed']
    assert nominal['two_inch_edge_margin_mm'] == pytest.approx(0)
    for allowance in ('depth_shortfall_mm', 'diameter_oversize_mm', 'center_error_mm'):
        assert not dimensional_screen(139.7, 38.1, **{allowance: .01})['dimensional_comparison_passed']
    assert dimensional_screen(141.2, 38.1, diameter_oversize_mm=.5,
                              center_error_mm=.5)['dimensional_comparison_passed']


def test_section_matches_two_separated_rectangles():
    section = centered_section()
    width, ligament, offset = 38.1, 50.8, 44.45
    assert section['net_area_mm2'] == pytest.approx(2*width*ligament)
    assert section['strong_I_mm4'] == pytest.approx(
        2*(width*ligament**3/12+width*ligament*offset**2))
    assert section['weak_S_mm3'] == pytest.approx(2*ligament*width**2/6)
    assert not section['qualified_for_design']


@pytest.mark.parametrize('invalid', [math.nan, math.inf, -1])
def test_invalid_inputs_rejected(invalid):
    with pytest.raises(ValueError):
        dimensional_screen(139.7, 38.1, center_error_mm=invalid)
    with pytest.raises(ValueError):
        centered_section(depth_mm=invalid)
