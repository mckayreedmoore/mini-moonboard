"""Checks fail closed and preserve actual diameter, axial force and net sections."""
import copy

import numpy as np
import pytest

from fea.current_leg_mvp_checks import assess, bolt_check, net_member_check
from fea.current_leg_revision_screen import LEG, RIM, capacity
from fea.current_response_resistance import VALIDITY


def members():
    return {'rim':{'grain':RIM.tolist(),'width_mm':38.1},
            'leg':{'grain':LEG.tolist(),'width_mm':38.1}}


def bolt(force):
    return {'first':'rim','second':'leg','axis':[1.,0.,0.],
            'force_on_first_xyz_n':force,'force_on_second_xyz_n':[-v for v in force]}


@pytest.mark.parametrize('force', [[0.,100.,200.],[0.,-500.,100.],[0.,200.,-350.],[0.,0.,0.]])
def test_scalar_capacity_matches_vector_screen(force):
    result = bolt_check(bolt(force),members())
    assert result['reference_lateral_n'] == pytest.approx(float(capacity(np.array(force),.5)))


def test_axial_force_is_recovered_without_invented_prying_multiplier():
    result = bolt_check(bolt([-321.,100.,200.]),members())
    assert result['axial_absolute_envelope_n'] == 321.
    assert result['axial_increment_signed_n'] == -321.
    assert result['plate']['wood_bearing_ratio'] > 0
    assert result['steel']['linear_lateral_axial_interaction_ratio'] > result['lateral_ratio']


def test_wrong_diameter_and_nonfinite_or_unbalanced_forces_rejected():
    with pytest.raises(ValueError,match='1/2-inch'):
        bolt_check(bolt([0.,100.,200.]),members(),diameter_mm=9.525)
    with pytest.raises(ValueError,match='finite'):
        bolt_check(bolt([0.,float('nan'),0.]),members())
    row = bolt([0.,100.,200.])
    row['force_on_second_xyz_n'] = [0.,0.,0.]
    with pytest.raises(ValueError,match='action/reaction'):
        bolt_check(row,members())


def test_invalid_native_case_never_emits_resistance_pass():
    report = {'candidate':'leg-mvp-development',**dict.fromkeys(VALIDITY,True)}
    for flag in VALIDITY:
        invalid = dict(report, **{flag:False})
        result = assess(invalid,{'candidate':'leg-mvp-development'})
        assert result['status'] == 'INVALID_RESPONSE_DIAGNOSTIC_ONLY'
        assert 'metrics' not in result
        assert result['qualified_for_design'] is False


def section_data():
    return {'member':{'width_mm':38.1,'depth_mm':234.95},'length_mm':1800.,
            'sections':[{'axial_n_tension_positive':-1000.,'moment_u_nmm':200000.,
                         'moment_v_nmm':20000.,'shear_u_n':100.,'shear_v_n':150.,
                         'torsion_nmm':10.,'station_along_grain_mm':500.}]}


def test_actual_offcentre_holes_increase_member_stresses():
    member = {'width_mm':38.1,'depth_mm':234.95}
    solid = net_member_check(section_data(),member,[])
    holes = net_member_check(section_data(),member,[(500.,40.,14.2875),(500.,-30.,14.2875)])
    assert holes['minimum_area_mm2'] < solid['minimum_area_mm2']
    assert holes['maximum_centroid_eccentricity_mm'] > 0
    assert holes['conservative_peak']['conservative_net_section_envelope_ratio'] > solid['conservative_peak']['conservative_net_section_envelope_ratio']
    assert holes['conservative_peak']['local_opening_resistance_evaluated'] is False
    assert holes['conservative_peak']['torsion_resistance_evaluated'] is False


def test_missing_inventory_rejected_after_numerical_gates():
    report = {'candidate':'leg-mvp-development',**dict.fromkeys(VALIDITY,True),
              'physical_connection_forces':{}}
    geometry = {'candidate':'leg-mvp-development',
                'members':{name:{} for name in ('lumber_leg_left','lumber_leg_right','base_side_left','base_side_right')},
                'bolt_names':['lumber_leg_bolt_left_1'],'hole_diameter_mm':14.2875,'bolt_diameter_mm':12.7}
    with pytest.raises(ValueError,match='inventory'):
        assess(copy.deepcopy(report),geometry)


@pytest.mark.parametrize('candidate', ['leg-mvp-development', 'leg-mvp-sole-development'])
def test_complete_synthetic_case_reports_both_sides_and_keeps_open_limits(candidate):
    report = {'candidate':'leg-mvp-development',**dict.fromkeys(VALIDITY,True),
              'physical_connection_forces':{},'member_section_demands':{}}
    geometry = {'candidate':'leg-mvp-development','members':{},'bolt_names':[],
                'bolt_diameter_mm':12.7,'hole_diameter_mm':14.2875}
    for side in ('left','right'):
        for name, grain in [('lumber_leg_'+side,LEG),('base_side_'+side,RIM)]:
            geometry['members'][name] = {'grain':grain.tolist(),'centre_mm':[0.,0.,0.],
                'end_stations_mm':[-900.,900.],'width_mm':38.1,'depth_mm':234.95,
                'additional_section_boxes':[],'openings_complete':False}
            data = section_data()
            data.update(section_valid_from_mm=0.,force_residual_n=0.,moment_residual_nmm=0.)
            data['sections'][0]['include_station_loads'] = True
            report['member_section_demands'][name] = data
        for index, station in enumerate((-50.,50.)):
            name = f'lumber_leg_bolt_{side}_{index+1}'
            row = bolt([10.,20.,30.])
            row.update(first='base_side_'+side,second='lumber_leg_'+side,
                       point=(LEG*station).tolist())
            report['physical_connection_forces'][name] = row
            geometry['bolt_names'].append(name)
    report['candidate'] = geometry['candidate'] = candidate
    result = assess(report,geometry)
    assert len(result['local_wood']) == len(result['net_members']) == 4
    assert len(result['bolts']) == 4
    assert all(not row['all_openings_represented'] for row in result['local_wood'].values())
    assert result['qualified_for_design'] is False
    assert result['limits']


@pytest.mark.parametrize('report_key,geometry_key', [
    ('leg-mvp-sole-development','leg-mvp-development'),
    ('leg-mvp-development','leg-mvp-sole-development'),
    ('unknown','unknown'),
])
def test_candidate_identity_mismatch_rejected(report_key, geometry_key):
    with pytest.raises(ValueError,match='matching leg MVP'):
        assess({'candidate':report_key},{'candidate':geometry_key})
