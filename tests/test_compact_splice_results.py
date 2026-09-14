"""Splice grouping and compression-contact gates do not infer missing evidence."""
import copy

import pytest

from fea.compact_assumption_checks import compare_bolt
from fea.compact_rail_checks import hardware_assumptions
from fea.compact_thick_checks import fully_threaded_sensitivity
from fea.thick_leg_checks import bolt_check
from scripts.compact_splice_results import (
    actual_root_comparison,
    connection_groups,
    local_groups,
    overlap_contact_check,
)


def test_actual_root_modes_match_fixed_root_before_angle_adjustment():
    member = {'grain':[0., 0., 1.], 'specific_gravity':.5, 'parallel_bearing_psi':5600.,
        'bearing_length_mm':88.9, 'edge_distances_mm':dict.fromkeys(
            ('grain_positive', 'grain_negative', 'depth_positive', 'depth_negative'), 100.)}
    geometry = {'diameter_mm':12.7, 'bending_yield_psi':45000., 'members':{'a':member, 'b':member}}
    row = {'first':'a', 'second':'b', 'axis':[1., 0., 0.],
        'force_on_first_xyz_n':[20., 500., 500.], 'force_on_second_xyz_n':[-20., -500., -500.]}
    hardware = hardware_assumptions(12.7, washer_od_mm=34.925,
        hole_diameter_mm=14.2875, washer_thickness_mm=3.175)
    nominal = bolt_check(row, geometry, hardware)
    root = hardware['root_diameter_mm']
    nominal['fully_threaded_sensitivity'] = fully_threaded_sensitivity(nominal, geometry, root)
    result = actual_root_comparison(nominal, geometry, compare_bolt(row, geometry), root)
    assert result['Ktheta'] == pytest.approx(1.125)
    assert result['actual_Ktheta_root_ratio_CD_1'] == pytest.approx(result['fixed_Ktheta_root_ratio']*.9)
    assert result['dowel_reference']['yield_values_lbf'] == nominal['fully_threaded_sensitivity']['dowel_reference']['yield_values_lbf']
    assert geometry['diameter_mm'] == 12.7
    nominal['fully_threaded_sensitivity']['lateral_ratio'] *= 1.01
    with pytest.raises(ValueError):
        actual_root_comparison(nominal, geometry, compare_bolt(row, geometry), root)


def test_two_endpoint_and_four_overlap_bolts_remain_distinct_groups():
    rows = {f'end{i}':{'first':'knee_rim', 'second':'rim'} for i in range(2)}
    rows.update({f'splice{i}':{'first':'knee_rim', 'second':'knee_leg'} for i in range(4)})
    groups = connection_groups(rows)
    assert sorted(len(names) for names in groups.values()) == [2, 4]
    assert sum('knee_rim' in pair for pair in groups) == 2
    rows['extra'] = {'first':'knee_rim', 'second':'knee_leg'}
    with pytest.raises(ValueError):
        connection_groups(rows)


def test_local_force_groups_include_other_holes_without_combining_demands():
    rows, hardware, bolts, actual = {}, {}, {}, {}
    for prefix, count, other, start, demand in (('end', 2, 'rim', -300., 100.),
                                               ('splice', 4, 'knee_leg', 0., -50.)):
        for i in range(count):
            name = prefix+str(i)
            rows[name] = {'first':'knee_rim', 'second':other, 'point':[0., 0., start+50*i],
                'force_on_first_xyz_n':[0., 0., demand], 'force_on_second_xyz_n':[0., 0., -demand]}
            hardware[name] = {'hole_diameter_mm':11.1125}
            bolts[name] = {'diameter_mm':9.525}
            actual[name] = {'comparisons':{'actual_angle':{'ratio_CD_1':.2}}}
    member = {'grain':[0., 0., 1.], 'centre_mm':[0., 0., 0.], 'width_mm':38.1,
        'depth_mm':139.7, 'end_stations_mm':[-500., 500.], 'additional_section_boxes':[]}
    geometry = {'members':{name:copy.deepcopy(member) for name in ('knee_rim', 'knee_leg', 'rim')},
        'hardware_by_name':hardware, 'geometries_by_bolt_name':bolts}
    groups = local_groups(rows, geometry, actual)
    checks = [g['member_checks']['knee_rim'] for g in groups.values()]
    assert sorted(c['other_group_holes_in_net_envelope'] for c in checks) == [2, 4]
    assert [c['wood']['rows'][0]['demand_n'] for c in checks] == [200., 200.]


def contacts():
    report = {'splice_assumptions':dict.fromkeys(('independent_members', 'compression_only_overlap',
              'no_tensile_tie', 'no_composite_action'), True), 'bearings':[], 'member_contacts':[]}
    for side in ('left', 'right'):
        name = 'knee_splice_contact_'+side+'_0'
        report['member_contacts'].append({'name':name, 'first':f'base_knee_{side}_rim',
            'second':f'base_knee_{side}_leg', 'tributary_area_mm2':100.})
        report['bearings'].append({'name':name, 'compression_force_n':100.,
            'compression_only_assumption_satisfied':True})
    return report


def test_contact_pressure_and_independent_member_assumptions_are_required():
    report = contacts()
    assert overlap_contact_check(report)['passes']
    missing = copy.deepcopy(report)
    missing['splice_assumptions'].pop('no_tensile_tie')
    assert not overlap_contact_check(missing)['passes']
    report['bearings'][0]['compression_force_n'] = 1000.
    assert not overlap_contact_check(report)['passes']
    report['bearings'][0]['compression_force_n'] = -1.
    assert not overlap_contact_check(report)['passes']
    assert not overlap_contact_check({})['passes']


def test_each_side_requires_real_contact_and_positive_area():
    report = contacts()
    report['member_contacts'].pop()
    assert not overlap_contact_check(report)['passes']
    report['member_contacts'][0]['tributary_area_mm2'] = 0.
    with pytest.raises(ValueError):
        overlap_contact_check(report)
