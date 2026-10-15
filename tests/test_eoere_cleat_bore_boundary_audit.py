"""Original-action, cylinder-domain and exact comparison controls."""
import copy
from fractions import Fraction as F

import pytest

from scripts import eoere_cleat_bore_boundary_audit as audit


def geometry():
    return {'frame': [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]], 'start': [0, 0, 0],
        'analytic_finished_volume_mm3': 100, 'actual_volume_mm3': 100,
        'current_finished_solid': {'valid_single_solid': True},
        'planes': [{'normal': normal, 'offset': offset} for normal, offset in
            [([-1, 0, 0], 0), ([1, 0, 0], 10), ([0, 1, 0], 2), ([0, -1, 0], 2), ([0, 0, 1], 5), ([0, 0, -1], 5)]],
        'bores': [{'id': f'bore{i}', 'origin': [l, 0, v], 'axis': [0., 1., 0.], 'radius_mm': 1, 'interval_mm': [-2, 2]}
                  for i, (l, v) in enumerate([(2, -2), (2, 2), (8, -2), (8, 2)])]}


def record():
    # Local coordinates (L,U,V) transform to world (U,V,L).
    return {'actions': [{'id': 'bore0/point/'+str(i), 'point_mm': p, 'force_n': f, 'free_moment_nmm': [0, 0, 0]}
        for i, (p, f) in enumerate([([-1, -2, 2], [0, 3, 2]), ([1, -2, 2], [0, 4, -1]), ([-2, -2, 2], [5, 0, 0])])]}


def test_full_cylinder_walls_fit_the_profile_and_do_not_intersect_other_bores():
    proofs = audit.full_bore_surfaces(geometry())
    assert len(proofs) == 4
    assert all(min(map(F, row['exact_profile_squared_clearance_margins'])) >= 0 for row in proofs)
    assert all(min(map(F, row['exact_other_bore_squared_clearance_margins'])) > 0 for row in proofs)


@pytest.mark.parametrize('change', ['axis', 'radius', 'outside-profile', 'intersection', 'short-interval', 'duplicate-id', 'volume', 'frame'])
def test_unsupported_cylindrical_boundaries_refuse(change):
    data = geometry()
    if change == 'axis':
        data['bores'][0]['axis'] = [1, 0, 0]
    elif change == 'radius':
        data['bores'][0]['radius_mm'] = -1
    elif change == 'outside-profile':
        data['bores'][0]['origin'][0] = F(1, 2)
    elif change == 'intersection':
        data['bores'][1]['origin'] = data['bores'][0]['origin']
    elif change == 'short-interval':
        data['bores'][0]['interval_mm'][1] = 1
    elif change == 'duplicate-id':
        data['bores'][1]['id'] = data['bores'][0]['id']
    elif change == 'volume':
        data['actual_volume_mm3'] = 90
    else:
        data['frame'][0][2] = -1
    with pytest.raises(ValueError):
        audit.full_bore_surfaces(data)


def test_original_two_point_wrench_keeps_signs_moments_and_separate_axial_capture():
    data = geometry()
    wrench, points = audit.source_wrench(record(), data, data['bores'][0])
    assert wrench == [1, 7, 1, 3]
    assert len(points) == 2
    assert points[0]['exact_relative_point_LUV_mm'] == ['0', '-1', '0']


def test_tiny_original_force_is_retained_without_screening():
    data, actions = geometry(), record()
    tiny = F(1, 2**150)
    actions['actions'][0]['force_n'][2] = tiny
    wrench, _ = audit.source_wrench(actions, data, data['bores'][0])
    assert wrench[0] == tiny-1 and wrench[3] == tiny+1


@pytest.mark.parametrize('change', ['off-axis', 'axial-bearing', 'free-couple', 'lateral-capture', 'missing', 'extra'])
def test_changed_bore_action_roles_refuse(change):
    data, actions = geometry(), record()
    tiny = F(1, 2**150)
    if change == 'off-axis':
        actions['actions'][0]['point_mm'][1] += tiny
    elif change == 'axial-bearing':
        actions['actions'][0]['force_n'][0] = tiny
    elif change == 'free-couple':
        actions['actions'][0]['free_moment_nmm'][0] = tiny
    elif change == 'lateral-capture':
        actions['actions'][2]['force_n'][1] = tiny
    elif change == 'missing':
        actions['actions'].pop()
    else:
        extra = copy.deepcopy(actions['actions'][0]); extra['id'] = 'bore0/point/3'; actions['actions'].append(extra)
    with pytest.raises(ValueError):
        audit.source_wrench(actions, data, data['bores'][0])


@pytest.mark.parametrize('lower,upper,status', [
    (F(1), F(1), 'compressive_radial_pressure_and_stress_trace_within_hypothesis'),
    (F(1)+F(1, 2**150), F(2), 'full_tensor_boundary_hypothesis_necessarily_fails'),
    (F(1, 2), F(1)+F(1, 2**150), 'boundary_hypothesis_inconclusive'),
])
def test_scenario_thresholds_do_not_call_a_failed_construction_a_failure(lower, upper, status):
    scenario = {'id': 'toy', 'strength_divisor': 2., 'whole_wrench_multiplier': 1.5}
    result = audit.disposition(lower/3, upper/3, scenario)
    assert result['disposition'] == status
    assert F(result['exact_necessary_lower']) == lower and F(result['exact_construction_upper']) == upper
    assert result['complete_cleat_resistance'] is None and result['physical_failure_established'] is False
