"""Mixed diameter and thickness rails retain actual per-bolt force accounting."""
import copy

import pytest

from fea.compact_rail_checks import assess, hardware_assumptions
from fea.current_response_resistance import VALIDITY


def inputs():
    report={'candidate':'compact-rail-development',**dict.fromkeys(VALIDITY,True),
        'physical_connection_forces':{}}
    geometries,hardware={},{}
    for name,diameter,pair in [('lumber_leg_bolt_left_1',12.7,('rim','leg')),
        ('rail_bolt_rear_left_1',9.525,('rail','leg'))]:
        report['physical_connection_forces'][name]={'first':pair[0],'second':pair[1],
            'axis':[1.,0.,0.],'point':[0.,0.,100.],
            'force_on_first_xyz_n':[50.,-600.,400.],
            'force_on_second_xyz_n':[-50.,600.,-400.]}
        members={}
        for member in pair:
            members[member]={'grain':[0.,1.,0.] if member=='rail' else [0.,0.,1.],
                'bearing_length_mm':38.1 if member=='rail' else 88.9,
                'specific_gravity':.5,'parallel_bearing_psi':5600.,
                'edge_distances_mm':{'grain_positive':150.,'grain_negative':500.,
                    'depth_positive':70.,'depth_negative':70.}}
        geometries[name]={'diameter_mm':diameter,'bending_yield_psi':45000.,'members':members}
        hardware[name]=hardware_assumptions(diameter,washer_od_mm=34.925 if diameter==12.7 else 25.4,
            hole_diameter_mm=14.2875 if diameter==12.7 else 11.1125,washer_thickness_mm=3.175)
    return report,geometries,hardware


def evaluate(report,geometries,hardware):
    return assess(report,geometries,hardware,bolt_prefixes=('lumber_leg_bolt_','rail_bolt_'))


def test_mixed_bolt_sizes_and_unequal_bearing_lengths_survive():
    result=evaluate(*inputs())
    upper=result['bolts']['lumber_leg_bolt_left_1']
    rail=result['bolts']['rail_bolt_rear_left_1']
    assert upper['diameter_mm']==12.7
    assert rail['diameter_mm']==9.525
    assert rail['bearing_lengths_mm']==[38.1,88.9]
    assert rail['fully_threaded_sensitivity']['root_diameter_mm']==pytest.approx(.298*25.4)
    assert upper['fully_threaded_sensitivity']['root_diameter_mm']==pytest.approx(.4056*25.4)
    assert len(result['joint_resultants'])==2
    assert result['qualified_for_design'] is False


def test_reversing_member_order_preserves_single_shear_resistance():
    report,geometry,hardware=inputs()
    name='rail_bolt_rear_left_1'
    before=evaluate(report,geometry,hardware)['bolts'][name]
    row=report['physical_connection_forces'][name]
    row['first'],row['second']=row['second'],row['first']
    row['force_on_first_xyz_n'],row['force_on_second_xyz_n']=row['force_on_second_xyz_n'],row['force_on_first_xyz_n']
    after=evaluate(report,geometry,hardware)['bolts'][name]
    assert after['bearing_lengths_mm']==[88.9,38.1]
    assert after['lateral_reference_n']==pytest.approx(before['lateral_reference_n'])


def test_missing_rail_bolt_or_wrong_hardware_rejected():
    report,geometry,hardware=inputs()
    incomplete=copy.deepcopy(geometry)
    incomplete.pop('rail_bolt_rear_left_1')
    with pytest.raises(ValueError,match='matching geometry'):
        evaluate(report,incomplete,hardware)
    hardware['rail_bolt_rear_left_1']['nominal_diameter_mm']=12.7
    with pytest.raises(ValueError,match='diameter mismatch'):
        evaluate(report,geometry,hardware)


def test_native_numerical_failures_stop_before_any_capacity_claim():
    report,geometry,hardware=inputs()
    for key in VALIDITY:
        invalid=dict(report,**{key:False})
        result=evaluate(invalid,geometry,hardware)
        assert result['status']=='INVALID_RESPONSE_DIAGNOSTIC_ONLY'
        assert 'metrics' not in result


def test_force_directed_end_distinguishes_compression_and_tension():
    from fea.compact_rail_checks import directed_end_distance_check

    report,geometry,_=inputs()
    name='rail_bolt_rear_left_1'
    row=report['physical_connection_forces'][name]
    geometry[name]['members']['leg']['edge_distances_mm']['grain_positive']=44.85
    compression=directed_end_distance_check(row,geometry[name])
    end=compression['members']['leg']['ends']['grain_positive']
    assert end['full_reference_end_distance_mm']==pytest.approx(4*9.525)
    assert compression['end_distance_factor']==1.
    row['force_on_first_xyz_n'][2]=-400.
    row['force_on_second_xyz_n'][2]=400.
    tension=directed_end_distance_check(row,geometry[name])
    assert tension['end_distance_factor']==pytest.approx(44.85/(7*9.525))
    assert tension['applicable'] is True


def test_half_minimum_is_a_gate_not_an_unbounded_capacity_discount():
    from fea.compact_rail_checks import directed_end_distance_check

    report,geometry,_=inputs()
    name='rail_bolt_rear_left_1'
    row=report['physical_connection_forces'][name]
    row['force_on_first_xyz_n'][2]=-400.
    row['force_on_second_xyz_n'][2]=400.
    geometry[name]['members']['leg']['edge_distances_mm']['grain_positive']=3.5*9.525
    at_minimum=directed_end_distance_check(row,geometry[name])
    assert at_minimum['end_distance_factor']==pytest.approx(.5)
    geometry[name]['members']['leg']['edge_distances_mm']['grain_positive']-=.01
    too_short=directed_end_distance_check(row,geometry[name])
    assert too_short['end_distance_factor'] is None
    assert too_short['applicable'] is False


def test_smallest_end_factor_applies_to_the_whole_joint_and_strict_check_survives():
    report,geometry,hardware=inputs()
    first='rail_bolt_rear_left_1'
    second='rail_bolt_rear_left_2'
    report['physical_connection_forces'][second]=copy.deepcopy(report['physical_connection_forces'][first])
    geometry[second]=copy.deepcopy(geometry[first])
    hardware[second]=copy.deepcopy(hardware[first])
    row=report['physical_connection_forces'][second]
    row['force_on_first_xyz_n'][2]=-400.
    row['force_on_second_xyz_n'][2]=400.
    geometry[second]['members']['leg']['edge_distances_mm']['grain_positive']=44.85
    result=evaluate(report,geometry,hardware)
    branch=result['force_directed_end_branch']
    group=branch['joint_groups']['leg / rail']
    factor=44.85/(7*9.525)
    assert group['group_minimum_end_distance_factor']==pytest.approx(factor)
    assert group['nominal_lateral_ratios'][first]==pytest.approx(result['bolts'][first]['lateral_ratio']/factor)
    assert result['bolts'][second]['placement']['leg']['margins_mm']['grain_positive']<0
    assert branch['all_end_distances_above_absolute_minimum'] is True


def test_three_quarter_hardware_uses_its_own_thread_head_and_steel_references():
    import math

    hardware=hardware_assumptions(19.05,washer_od_mm=50.8,
        hole_diameter_mm=20.6375,washer_thickness_mm=3.81)
    assert hardware['tensile_area_mm2']==pytest.approx(.334*25.4**2)
    assert hardware['root_diameter_mm']==pytest.approx(.620*25.4)
    assert hardware['shear_area_mm2']==pytest.approx(math.pi*(.620*25.4)**2/4)
    assert hardware['steel_yield_mpa']==pytest.approx(92000*.006894757293168361)
    assert hardware['washers'][0]['seat_diameter_mm']==pytest.approx(.95*1.100*25.4)
    assert hardware['washers'][0]['thickness_mm']==3.81
    assert hardware['three_quarter_reference_basis']['sources']
    assert 'not a guaranteed' in hardware['three_quarter_reference_basis']['root_scope']


def test_three_quarter_assessment_preserves_actual_diameter_and_root_sensitivity():
    report,geometry,hardware=inputs()
    name='lumber_leg_bolt_left_1'
    geometry[name]['diameter_mm']=19.05
    hardware[name]=hardware_assumptions(19.05,washer_od_mm=50.8,
        hole_diameter_mm=20.6375,washer_thickness_mm=3.81)
    result=evaluate(report,geometry,hardware)
    bolt=result['bolts'][name]
    assert bolt['diameter_mm']==19.05
    assert bolt['fully_threaded_sensitivity']['root_diameter_mm']==pytest.approx(.620*25.4)
    assert bolt['fully_threaded_sensitivity']['lateral_ratio']>bolt['lateral_ratio']
    assert bolt['placement']['leg']['margins_mm']['grain_positive']==pytest.approx(150.-7*19.05)
    assert result['qualified_for_design'] is False
