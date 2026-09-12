"""Physical invariants and catalog dimensional extremes for the six-bolt joint."""
import math

import pytest

from mini_moonboard.wider_leg_hardware import (
    axial_couple_screen,
    bolt_combined_screen,
    dimensional_window,
    plate_screen,
    washer_screen,
)


def points():
    return [(0., s*66, t*42+s*20) for s in (-1, 0, 1) for t in (-1, 1)]


def test_dimensional_corners_and_out_of_window():
    for rim in (37.5, 38.5):
        for leg in (37.5, 38.5):
            assert dimensional_window(rim, leg)['dimensional_pass']
    with pytest.raises(ValueError):
        dimensional_window(39, 38.1)


def test_skew_group_balances_both_moments_and_ignores_translation():
    p = points()
    r = axial_couple_screen(p, (0, -1500, 4000))
    t = r['unamplified_signed_axial_n']
    assert sum(t) == pytest.approx(0, abs=1e-10)
    my = sum(q[2]*v for q, v in zip(p, t, strict=True))
    mz = -sum(q[1]*v for q, v in zip(p, t, strict=True))
    assert (my, mz) == pytest.approx(r['target_couple_xyz_nmm'][1:])
    shifted = [(x+200, y-700, z+111) for x, y, z in p]
    assert axial_couple_screen(shifted, (0, -1500, 4000))['peak_tension_n'] == pytest.approx(r['peak_tension_n'])
    assert axial_couple_screen(p, (0, 1500, -4000))['peak_tension_n'] == pytest.approx(r['peak_tension_n'])


def test_prying_and_resistance_scaling_are_explicit():
    p = points()
    r = axial_couple_screen(p, (0, -1500, 4000), amplification=1)
    doubled = axial_couple_screen(p, (0, -1500, 4000), amplification=2)
    assert doubled['peak_tension_n'] == pytest.approx(2*r['peak_tension_n'])
    for key in ('wood_bearing_ratio', 'plate_plastic_bending_ratio'):
        assert plate_screen(2000)[key] == pytest.approx(2*plate_screen(1000)[key])
    assert plate_screen(100000)['plate_plastic_bending_ratio'] > 1
    assert plate_screen(0)['plate_plastic_bending_ratio'] == 0
    assert washer_screen(1500)['single_washer_elastic_bending_ratio'] < 1
    assert not washer_screen(1500)['washers_act_compositely']


def test_invalid_group_and_steel_overload_fail():
    with pytest.raises(ValueError):
        axial_couple_screen([(0, 0, 0), (0, 1, 1), (0, 2, 2)], (0, 1, 2))
    with pytest.raises(ValueError):
        axial_couple_screen(points(), (0, math.nan, 0))
    assert bolt_combined_screen(1000, 1500)['steel_direct_interaction_ratio'] < 1
    assert bolt_combined_screen(100000, 1500)['steel_direct_interaction_ratio'] > 1
    assert not bolt_combined_screen(0, 100000)['nds_45000psi_bending_assumption_retained']


def test_combined_lateral_axial_reference_is_required_explicitly():
    omitted = bolt_combined_screen(1000, 1500)
    assert omitted['linear_lateral_axial_interaction_ratio'] is None
    checked = bolt_combined_screen(1000, 1500, lateral_ratio=.82)
    assert .82 < checked['linear_lateral_axial_interaction_ratio'] < 1
    assert bolt_combined_screen(1000, 1500, lateral_ratio=.99)['linear_lateral_axial_interaction_ratio'] > 1
    with pytest.raises(ValueError):
        bolt_combined_screen(1000, 1500, lateral_ratio=math.nan)
