import copy

import pytest

from scripts.floor_flush_checks import checks, face_contact_check


def contact_report():
    report = {'member_contacts': [], 'bearings': [], 'physical_connection_forces': {}}
    for side in ('left', 'right'):
        for index, (first, second) in enumerate((
                (f'base_side_{side}', f'lumber_leg_{side}'),
                (f'base_post_outer_{side}', f'base_floor_{side}'),
                (f'lumber_leg_{side}', f'base_floor_{side}'))):
            name = f'{side}_{index}'
            report['member_contacts'].append({'name': name, 'first': first, 'second': second,
                'point_xyz_mm': [0., 0., 0.], 'normal_xyz': [1., 0., 0.], 'tributary_area_mm2': 100.})
            report['bearings'].append({'name': name, 'compression_force_n': 200.,
                'opening_mm': -.02, 'active': True, 'compression_only_assumption_satisfied': True})
            report['physical_connection_forces'][name] = {'first': first, 'second': second,
                'point': [0., 0., 0.], 'scalar_normal': [1., 0., 0.]}
    return report


def test_contact_comparison_requires_six_interfaces_and_saved_geometry_match():
    report = contact_report()
    result = face_contact_check(report)
    assert result['interface_count'] == 6
    assert result['peak_wood_bearing_ratio'] == pytest.approx(200/(100*625*.006894757293168361))
    missing = copy.deepcopy(report)
    missing['member_contacts'].pop()
    with pytest.raises(ValueError, match='six actual flush interfaces'):
        face_contact_check(missing)
    changed = copy.deepcopy(report)
    changed['physical_connection_forces']['left_0']['point'][1] = 1.
    with pytest.raises(ValueError, match='inventory mismatch'):
        face_contact_check(changed)
    report['bearings'][0]['compression_only_assumption_satisfied'] = False
    assert not face_contact_check(report)['normal_contact_passed']


def test_historical_or_mismatched_candidate_cannot_enter_flush_assessment():
    for report, geometry in (({'candidate': 'compact-floor-taper-development'},
                             {'candidate': 'compact-floor-taper-development'}),
                            ({'candidate': 'compact-floor-flush-development'},
                             {'candidate': 'compact-floor-taper-development'})):
        with pytest.raises(ValueError, match='actual flush identities'):
            checks(report, geometry)
