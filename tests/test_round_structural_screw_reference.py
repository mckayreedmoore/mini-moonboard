"""Check conditional-reference mechanics without manufacturing a frame pass."""
import math

import pytest

from fea.round_structural_screw_reference import references, wood_interaction


def test_current_reference_uses_root_section_and_lower_plywood_bearing():
    r = references()
    assert r['lateral']['governing_mode'] == 'IIIs'
    assert r['lateral']['reference_lateral_lbf'] == pytest.approx(52.9829570333)
    assert r['lateral_inputs']['main_length_in'] == pytest.approx(1.11825)
    assert r['lateral_inputs']['side_length_in'] == pytest.approx(.55875)
    assert r['lateral_inputs']['side_bearing_lb_in'] == pytest.approx(335.)
    # Independent NDS mode-IV expression checks TR12 bending-moment convention.
    expected_iv = .1**2/2.2*math.sqrt(2*4650*187000/(3*(1+4650/3350)))
    assert r['lateral']['reference_values_lbf']['IV'] == pytest.approx(expected_iv)
    assert not r['qualified_for_design'] and not r['current_demands_evaluated']
    assert not r['installation_adjustments_applied'] and not r['steel_interaction_evaluated']


def test_interaction_pure_limits_and_45_degree_capacity():
    caps = {'withdrawal_n': 800., 'lateral_reference_n': 200., 'head_reference_n': 1000.}
    assert wood_interaction(0., 0., **caps)['wood_interaction_ratio'] == 0.
    assert wood_interaction(800., 0., **caps)['wood_interaction_ratio'] == 1.
    assert wood_interaction(0., 200., **caps)['wood_interaction_ratio'] == 1.
    # At45deg the resultant limit is the harmonic mean of the two references.
    component = (2/(1/800+1/200))/math.sqrt(2)
    r = wood_interaction(component, component, **caps)
    assert r['wood_interaction_ratio'] == pytest.approx(1.)
    assert r['head_pull_through_ratio'] == pytest.approx(component/1000)
    assert not r['qualified_for_design']


@pytest.mark.parametrize('bad', [-1., math.nan, math.inf])
def test_no_compression_or_nonfinite_demand_disguised_as_tension(bad):
    with pytest.raises(ValueError):
        wood_interaction(bad, 0., withdrawal_n=800., lateral_reference_n=200., head_reference_n=1000.)


def test_head_capacity_is_mandatory_and_checked_separately():
    with pytest.raises(ValueError):
        wood_interaction(0., 0., withdrawal_n=800., lateral_reference_n=200., head_reference_n=0.)
    r = wood_interaction(300., 0., withdrawal_n=800., lateral_reference_n=200., head_reference_n=100.)
    assert r['wood_interaction_ratio'] < 1 < r['head_pull_through_ratio']
