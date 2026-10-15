"""Known-answer controls for source work, necessary intervals and dual gaps."""
import copy
from fractions import Fraction as F

import pytest

from scripts import eoere_mixed_reaction_bound as mixed


def fixture():
    surfaces = [{'host': name, 'kind': kind, 'interval_mm': interval}
                for name, kind, interval in [('wood-a', 'wood', [0, 2]), ('wood-b', 'wood', [2, 4]), ('steel', 'steel', [-2, 0])]]
    shaft = {'axis_id': 'own', 'body': 'shaft/own', 'basis': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
             'point': [10, 20, 30], 'surfaces': surfaces, 'metal_roles': [{'id': 'own/head'}]}
    arguments = {'surfaces': [{'host': s['host'], 'kind': s['kind'], 'interval': s['interval_mm']} for s in surfaces]}
    multiplier = {'surfaces': [{'force': [2, 3], 'first_moment': [5, 7]},
                              {'force': [0, 0], 'first_moment': [0, 0]}, {'force': [0, 0], 'first_moment': [0, 0]}],
                  'cuts': [{'station': 1, 'nu': [11, 13], 'include': True}]}
    ports, identities = [], []
    for i, surface in enumerate(surfaces):
        low, high = surface['interval_mm']
        for quad, station in enumerate([F(3*low+high, 4), F(low+3*high, 4)]):
            identity = f'own/bearing-{i}-{quad}'
            ports.append({'id': identity, 'axis_id': 'own', 'kind': 'common_shaft_bearing', 'surface_index': i,
                          'quad_index': quad, 'first': 'shaft/own', 'second': surface['host'], 'surface': surface,
                          'ka': 0, 'basis': shaft['basis'], 'point_xyz_mm': [10+station, 20, 30]})
            identities.extend([identity+'/lateral-1', identity+'/lateral-2'])
    loads = [{'body': 'shaft/own', 'id': 'physical-bolt-metal/own/head', 'point_xyz_mm': [9, 20, 30],
              'force_xyz_n': [3, 5, 7], 'moment_xyz_nmm': [0, 17, 19]}]
    return shaft, ports, identities, arguments, multiplier, loads


def test_signed_gauss_work_and_point_couples_have_independent_known_answers():
    row, constant, surfaces, points = mixed.source_functional(*fixture())
    assert row == {0: F(1, 2), 1: F(1, 2), 2: F(-9, 2), 3: F(-13, 2)}
    assert constant == 458
    assert surfaces[0] == {'force': [{0: -1, 2: -1}, {1: -1, 3: -1}],
                           'first_moment': [{0: F(1, 2), 2: F(-1, 2)}, {1: F(1, 2), 3: F(-1, 2)}]}
    assert points == [{'s': -1, 'force': [5, 7], 'couple': [17, 19]}]
    candidate = list(map(F, [2, 4, 6, 8]))
    # F=(-8,-12), J=(-2,-2): lambda.F + lambda.J = -76.
    assert sum(row[j]*candidate[j] for j in row)+constant == 382


def test_exact_rotated_basis_preserves_the_same_local_work():
    args = list(fixture())
    basis = [[F(3, 5), F(4, 5), 0], [F(-4, 5), F(3, 5), 0], [0, 0, 1]]
    original = mixed.source_functional(*args)
    shaft, ports, _, _, _, loads = args
    shaft['basis'] = basis
    for port in ports:
        station = port['point_xyz_mm'][0]-10
        port['basis'] = basis
        port['point_xyz_mm'] = [o+station*a for o, a in zip(shaft['point'], basis[0], strict=True)]
    loads[0]['point_xyz_mm'] = [o-a for o, a in zip(shaft['point'], basis[0], strict=True)]
    loads[0]['force_xyz_n'] = [sum(basis[j][i]*v for j, v in enumerate([3, 5, 7])) for i in range(3)]
    loads[0]['moment_xyz_nmm'] = [sum(basis[j][i]*v for j, v in enumerate([0, 17, 19])) for i in range(3)]
    assert mixed.source_functional(*args) == original


def test_exact_binary_station_is_not_replaced_with_its_decimal_rendering():
    args = list(fixture())
    args[0]['point'][0] = 0
    for port in args[1]:
        port['point_xyz_mm'][0] -= 10
    args[1][0]['point_xyz_mm'][0] = .1
    row, _, _, _ = mixed.source_functional(*args)
    assert row[0] == -2-(F.from_float(.1)-1)*5
    assert row[0] != -2-(F(1, 10)-1)*5


def test_nonzero_tiny_multiplier_terms_are_retained():
    args = list(fixture())
    args[4]['surfaces'][1]['force'][0] = '1e-100'
    row, _, _, _ = mixed.source_functional(*args)
    assert row[4] == row[6] == -F(1, 10**100)


@pytest.mark.parametrize('change', ['basis', 'handedness', 'missing-port', 'duplicate-port', 'quad', 'host',
    'interval', 'axial', 'port-basis', 'noncollinear', 'outside', 'missing-scalar', 'duplicate-scalar', 'gravity'])
def test_incompatible_or_incomplete_source_mapping_refuses(change):
    args = copy.deepcopy(list(fixture()))
    shaft, ports, identities, arguments, _, loads = args
    if change == 'basis':
        shaft['basis'][1][1] += F(1, 2**100)
    elif change == 'handedness':
        shaft['basis'][2][2] = -1
    elif change == 'missing-port':
        ports.pop()
    elif change == 'duplicate-port':
        ports[-1]['id'] = ports[0]['id']
    elif change == 'quad':
        ports[1]['quad_index'] = 0
    elif change == 'host':
        ports[0]['second'] = 'foreign'
    elif change == 'interval':
        arguments['surfaces'][0]['interval'] = [0, 3]
    elif change == 'axial':
        ports[0]['ka'] = F(1, 2**100)
    elif change == 'port-basis':
        ports[0]['basis'] = [[1, 0, 0], [0, -1, 0], [0, 0, -1]]
    elif change == 'noncollinear':
        ports[0]['point_xyz_mm'][2] += F(1, 2**100)
    elif change == 'outside':
        ports[0]['point_xyz_mm'][0] = 100
    elif change == 'missing-scalar':
        identities.pop(0)
    elif change == 'duplicate-scalar':
        identities[-1] = identities[0]
    else:
        loads[0]['id'] = 'physical-bolt-metal/foreign'
    with pytest.raises(ValueError):
        mixed.source_functional(*args)


@pytest.mark.parametrize('center,error,expected', [(F(3), F(1), [2, 4]), (F(-3), F(1), [2, 4]),
                                                 (F(1), F(2), [0, 3]), (F(0), F(0), [0, 0])])
def test_signed_necessary_interval_handles_both_signs_and_a_zero_crossing(center, error, expected):
    got = mixed.necessary_interval({0: F(1)}, F(7), [center-7], [error], [F(1)], F(0), F(1), ['1'])
    assert list(map(F, got['exact_signed_lower_upper'])) == [center-error, center+error]
    scenario = got['scenarios'][0]
    assert [F(scenario[key]) for key in ['exact_necessary_ratio_lower', 'exact_necessary_ratio_upper']] == expected
    assert scenario['every_equilibrium_fails_this_lateral_reference_hypothesis'] is (expected[0] > 1)
    assert scenario['passing_field_or_complete_resistance_established'] is False


def test_an_equilibrium_gap_and_correction_box_both_enlarge_the_necessary_interval():
    got = mixed.necessary_interval({0: F(2)}, F(1), [F(3)], [F(1, 10)], [F(2)], F(1, 4), F(5), ['5'])
    # C*x+constant=7; box radius=.2; sqrt(2*gap*C*k*C)=2.
    assert list(map(F, got['exact_signed_lower_upper'])) == [F(24, 5), F(46, 5)]
    assert F(got['scenarios'][0]['exact_necessary_ratio_lower']) == F(24, 5)


@pytest.mark.parametrize('support,divisors', [(0, ['1']), (-1, ['1']), (1, []), (1, ['0']), (1, ['-1'])])
def test_nonpositive_support_or_divisor_cannot_generate_a_resistance_claim(support, divisors):
    with pytest.raises(ValueError):
        mixed.necessary_interval({0: F(1)}, F(0), [F(1)], [F(0)], [F(1)], F(0), F(support), divisors)


def test_smaller_inactive_contact_margin_refines_only_the_dual_gap():
    component = [{'kind': 'floor_normal', 'stiffness': F(2)}]
    ports = [{'descriptor': {'kind': 'floor_normal', 'stiffness': F(2)}, 'columns': [0], 'type': 'normal'}]
    family = {'alpha': '1', 'beta': '1'}
    for value in [F(1, 10**5), F(1, 10**8)]:
        gap = mixed.gap_only(family, component, ports, [value], [F(0)], [F(-3)], F(0), F(0))
        assert F(gap['exact_total_Fenchel_gap_upper_nmm']) == mixed.method.upper(value**2/4+3*value)


def test_vector_clearance_and_positive_axial_gaps_keep_their_separate_domains():
    port = {'descriptor': {'kind': 'panel_screw', 'ka': F(2), 'kl': F(3), 'clearance': F(1), 'tension_only': True},
            'columns': [0, 1, 2], 'type': 'vector'}
    gap = mixed.gap_only({'alpha': '1/2', 'beta': '2'}, [], [port], [F(1), F(3), F(4)], [F(0)]*3,
                        [F(1), F(3), F(4)], F(0), F(0))
    # Panel laws stay fixed even when the variable comparator range is wider.
    expected = mixed.method.upper(mixed.method.spring_gap([F(1)], [F(1)], [F(0)], 2, 1, 1, positive=True))
    expected += mixed.method.upper(mixed.method.spring_gap([F(3), F(4)], [F(3), F(4)], [F(0)]*2, 3, 1, 1, clearance=1))
    assert F(gap['exact_total_Fenchel_gap_upper_nmm']) == expected
