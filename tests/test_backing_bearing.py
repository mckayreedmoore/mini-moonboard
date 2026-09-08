"""Dimensional, units and input checks for a conditional bearing calculation."""
import math

import pytest

from fea.backing_bearing import envelope


def test_selected_annulus_and_stress_units():
    row = envelope(20.447, 11.1125, 1.)
    expected = math.pi*((20.447/2)**2-(11.1125/2)**2)
    assert row["supported_annular_area_mm2"] == pytest.approx(expected)
    assert row["pressure_at_1kn_mpa"]*expected == pytest.approx(1000.)
    assert row["conditional_wood_bearing_force_n"] == pytest.approx(expected)
    assert envelope(20.447, 11.1125, 2.)["conditional_wood_bearing_force_n"] == pytest.approx(2*expected)
    # A larger unsupported bore must decrease, not increase, conditional bearing.
    assert envelope(20.447, 12., 1.)["conditional_wood_bearing_force_n"] < expected


@pytest.mark.parametrize("args", [(0., 1., 1.), (10., 10., 1.), (10., 11., 1.),
    (10., -1., 1.), (10., 1., 0.), (10., 1., -1.), (math.inf, 1., 1.),
    (10., math.nan, 1.), (10., 1., math.inf)])
def test_invalid_geometry_or_stress_rejected(args):
    with pytest.raises(ValueError):
        envelope(*args)
