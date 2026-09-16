import copy

import pytest

from scripts.floor_flush_checks import (
    FROZEN_ADOPTED_CRITERIA,
    checks,
    face_contact_check,
)


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


def test_projected_seat_scalar_is_preserved_but_not_adopted(monkeypatch):
    result = {
        'criteria': {**dict.fromkeys(FROZEN_ADOPTED_CRITERIA, True),
                     'base_end_cut_geometry': False},
        'metrics': {},
        'base': {'base_side_left': {
            'quarter_depth_margin_after_3mm_allowance_mm': -4.97}},
        'limits': [],
    }
    monkeypatch.setattr('scripts.floor_flush_checks.existing_checks',
                        lambda report, geometry: copy.deepcopy(result))
    monkeypatch.setattr('scripts.floor_flush_checks.face_contact_check', lambda report: {
        'normal_contact_passed': True, 'peak_wood_bearing_ratio': .12})
    monkeypatch.setattr('scripts.floor_flush_checks.rim_cut_side_stress_diagnostic',
                        lambda report: {})
    report = {'candidate': 'compact-floor-flush-development',
              'clearance_monitors': [
                  {'name': f'flush_taper_top_{side}_{depth}_{station}',
                   'deformed_gap_mm': 1.}
                  for side in ('left', 'right') for depth in range(3) for station in range(3)]}
    assessed = checks(report, {'candidate': 'compact-floor-flush-development'})
    assert 'base_end_cut_geometry' not in assessed['criteria']
    assert set(assessed['criteria']) == FROZEN_ADOPTED_CRITERIA
    assert assessed['non_adopted_sensitivities']['base_end_cut_geometry'] == {
        'recorded_result': False,
        'minimum_quarter_depth_margin_after_3mm_allowance_mm': -4.97,
        'adopted_as_acceptance_criterion': False,
        'reason': ('Historical projected-seat scalar has no established mapping to '
                   'this supported terminal bevel. Retained-section, bearing, '
                   'contact and gross/net checks remain adopted.'),
    }
    assert assessed['status'] == 'IMPLEMENTED_FLUSH_CRITERIA_MET_COMPLETION_GATES_OPEN'
