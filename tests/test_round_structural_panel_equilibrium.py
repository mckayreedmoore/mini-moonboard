"""Verify force-only bounds against the existing mixed-load equation."""
import math

import pytest

from fea.round_structural_panel_equilibrium import (
    maximum_lateral,
    necessary_force_check,
    report,
)
from fea.round_structural_screw_reference import wood_interaction


@pytest.mark.parametrize('w,z,h', [(733.6,235.68,304.125), (800.,200.,1000.),
                                   (800.,200.,100.), (200.,200.,300.), (100.,200.,20.)])
def test_analytic_lateral_maximum_against_dense_angular_envelope(w,z,h):
    result = maximum_lateral(w,z,h)
    v, t = result['maximum_lateral_n'], result['tension_at_maximum_n']
    assert wood_interaction(t,v,withdrawal_n=w,lateral_reference_n=z,
                            head_reference_n=h)['wood_interaction_ratio'] == pytest.approx(1.)
    sampled = []
    for i in range(10001):
        angle = math.pi/2*i/10000
        c,s = math.cos(angle),math.sin(angle)
        radius = 1/(c*c/z+s*s/w)
        if radius*s <= h:
            sampled.append(radius*c)
    assert max(sampled) <= v+1e-9
    assert v-max(sampled) < .1
    assert t <= h and v >= z


def test_kicker_failure_is_not_equal_sharing_assumption():
    caps = {'withdrawal_n': 733.6, 'lateral_n': 235.68, 'head_n': 304.125}
    r = necessary_force_check(4,1200.,angle_from_vertical_deg=0.,**caps)
    assert r['conditional_force_equilibrium_impossible']
    assert r['optimistic_lateral_sum_n'] > 4*caps['lateral_n']
    heavier = necessary_force_check(4,1200.,angle_from_vertical_deg=0.,panel_dead_n=50.,**caps)
    assert heavier['required_tangential_n'] == 1250.


def test_current_report_has_every_panel_and_hold_without_qualification():
    r = report()
    assert sorted(map(len,r['holds_by_panel'].values())) == [5,5,30,30,36,36]
    assert sum(map(len,r['holds_by_panel'].values())) == 142
    assert len(r['cases']) == 30
    assert not r['qualified_for_design'] and not r['moments_evaluated']
    assert all(row['conditional_force_equilibrium_impossible'] for row in r['cases']
               if row['panel'].startswith('kicker_'))
    assert not any(row['conditional_force_equilibrium_impossible'] for row in r['cases']
                   if row['panel'].startswith('main_'))


@pytest.mark.parametrize('bad', [0., -1., math.inf, math.nan])
def test_invalid_reference_rejected(bad):
    with pytest.raises(ValueError):
        maximum_lateral(bad,200.,300.)
