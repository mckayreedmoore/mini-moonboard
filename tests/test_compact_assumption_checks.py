"""Actual load angle changes reductions, without silently adopting duration credit."""
import copy
import math

import pytest

from fea.compact_assumption_checks import assess, compare_bolt
from fea.current_response_resistance import VALIDITY


def fixture():
    row={'first':'leg','second':'rim','axis':[1.,0.,0.],
        'force_on_first_xyz_n':[0.,0.,1000.],'force_on_second_xyz_n':[0.,0.,-1000.]}
    geometry={'diameter_mm':19.05,'bending_yield_psi':45000.,'members':{}}
    for name,grain in (('leg',[0.,0.,1.]),('rim',[0.,math.sqrt(.5),math.sqrt(.5)])):
        geometry['members'][name]={'grain':grain,'parallel_bearing_psi':5600.,
            'specific_gravity':.5,'bearing_length_mm':88.9}
    return row,geometry


def test_actual_angle_recomputes_every_mode_and_preserves_original_branch():
    result=compare_bolt(*fixture())
    assert result['maximum_angle_deg']==pytest.approx(45.)
    actual=result['comparisons']['actual_angle']
    old=result['comparisons']['original_fixed_1_25']
    assert actual['Ktheta']==pytest.approx(1.125)
    assert actual['reduction_terms']['II']==pytest.approx(3.6*1.125)
    for mode in ('Im','Is','II','IIIm','IIIs','IV'):
        assert actual['all_modes']['yield_values_lbf'][mode]==pytest.approx(old['all_modes']['yield_values_lbf'][mode])
        assert actual['all_modes']['reference_values_lbf'][mode]==pytest.approx(old['all_modes']['reference_values_lbf'][mode]*1.25/1.125)
    assert actual['hypothetical_ratio_CD_1_6']==pytest.approx(actual['ratio_CD_1']/1.6)
    assert result['duration_factor_adopted']==1.
    assert result['hypothetical_duration_applicability_established'] is False


def test_stale_original_ratio_rejected_and_zero_force_is_finite():
    row,geometry=fixture()
    with pytest.raises(ValueError,match='historical ratio'):
        compare_bolt(row,geometry,123.)
    row['force_on_first_xyz_n']=row['force_on_second_xyz_n']=[0.,0.,0.]
    result=compare_bolt(row,geometry)
    assert result['comparisons']['actual_angle']['ratio_CD_1']==0.
    assert result['comparisons']['actual_angle']['Ktheta']==1.25


def test_mode_two_does_not_gain_capacity_from_stronger_bending_steel():
    row,geometry=fixture()
    before=compare_bolt(row,geometry)['comparisons']['actual_angle']['all_modes']
    geometry['bending_yield_psi']=130000.
    after=compare_bolt(row,geometry)['comparisons']['actual_angle']['all_modes']
    assert after['reference_values_lbf']['II']==before['reference_values_lbf']['II']
    assert after['reference_values_lbf']['IV']>before['reference_values_lbf']['IV']


def test_numerical_candidate_and_direct_source_identity_gates():
    row,one_geometry=fixture()
    report={'candidate':'compact-two-development',**dict.fromkeys(VALIDITY,True),
        'physical_connection_forces':{'lumber_leg_bolt_left_1':row},
        'source_sha256':{'mini_moonboard/compact_two_frame.py':'same'}}
    geometry={'candidate':'compact-two-development',
        'geometries_by_bolt_name':{'lumber_leg_bolt_left_1':one_geometry},
        'source_sha256':dict(report['source_sha256'])}
    result=assess(report,geometry)
    assert result['matched_direct_model_source_sha256']==report['source_sha256']
    for flag in VALIDITY:
        invalid=dict(report,**{flag:False})
        assert assess(invalid,geometry)['status']=='INVALID_RESPONSE_DIAGNOSTIC_ONLY'
    stale=copy.deepcopy(geometry)
    stale['source_sha256']['mini_moonboard/compact_two_frame.py']='different'
    with pytest.raises(ValueError,match='source mismatch'):
        assess(report,stale)
    report['candidate']=geometry['candidate']='compact-leg-new-trial'
    with pytest.raises(ValueError,match='supported candidate'):
        assess(report,geometry)
    assert assess(report,geometry,expected_candidate='compact-leg-new-trial')['candidate']=='compact-leg-new-trial'
    geometry['candidate']='another'
    with pytest.raises(ValueError,match='supported candidate'):
        assess(report,geometry,expected_candidate='compact-leg-new-trial')
