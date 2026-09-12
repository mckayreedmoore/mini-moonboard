"""Verify APA force-per-width conversion and conservative orientation treatment."""
import math

import pytest

from fea.round_structural_kicker_bearing import reference


def test_one_foot_width_carries_tabulated_force():
    row = reference(2900*4.4482216152605, panel_dead_n=0)
    assert row['minimum_uniform_axial_width_mm'] == pytest.approx(304.8)
    assert not row['qualified_contact_length']
    assert not row['qualified_for_design']


def test_dead_weight_and_weaker_species_increase_required_width():
    base = reference(2669, panel_dead_n=30)
    weak = reference(2669, panel_dead_n=30, species_group=4)
    assert weak['minimum_uniform_axial_width_mm'] == pytest.approx(
        base['minimum_uniform_axial_width_mm']/.61)
    assert base['minimum_uniform_axial_width_mm'] > reference(
        2669, panel_dead_n=0)['minimum_uniform_axial_width_mm']
    assert base['minimum_uniform_axial_width_mm'] > reference(
        2669, panel_dead_n=30, axis='parallel')['minimum_uniform_axial_width_mm']


@pytest.mark.parametrize('value', [-1, math.nan, math.inf])
def test_invalid_load_rejected(value):
    with pytest.raises(ValueError):
        reference(value, panel_dead_n=0)
