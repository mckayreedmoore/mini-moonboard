"""Exact signed source registration and elastic-compliance bound controls."""
import copy
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import eoere_original_load_audit as audit


def rows(values):
    return [{j: F(value) for j, value in enumerate(row) if value} for row in values]


def source_fixture():
    groups = [
        {'id': 'bearing', 'kind': 'common_shaft_bearing', 'ka': 0., 'kl': 2., 'clearance': 1., 'tension_only': False,
         'B': csr_matrix([[1., 0., 0., 0.], [0., 1., 0., 0.], [0., 0., 1., 0.]])},
        {'id': 'panel', 'kind': 'panel_screw', 'ka': 3., 'kl': 4., 'clearance': 0., 'tension_only': True,
         'B': csr_matrix([[0., 1., 0., 0.], [0., 0., 1., 0.], [0., 0., 0., 1.]])}]
    contacts = [{'id': 'normal', 'kind': 'floor_normal', 'stiffness': 7., 'B': csr_matrix([[1., 0., 0., -1.]])}]
    tangents = [{'id': identity, 'kind': 'floor_tangent', 'stiffness': 11., 'B': csr_matrix([[1., 0., -1., 0.]])}
                for identity in ['enabled', 'disabled']]
    field = {'response': {'q': [1., 2., 3., 4.], 'connector_local_force_n': [[0., 1., -2.], [.2, 3., -4.]],
                          'normal_contact_force_n': [5.]}}
    return {'groups': groups, 'contacts': contacts, 'tangents': tangents}, field


def test_scalar_registry_keeps_bilateral_then_unilateral_order_and_signed_weights():
    partitions, field = source_fixture()
    components, ports, bilateral = audit.register(partitions, field, {'enabled'})
    assert bilateral == 5
    assert [row['id'] for row in components] == ['bearing/lateral-1', 'bearing/lateral-2', 'panel/lateral-1',
        'panel/lateral-2', 'enabled', 'panel/axial', 'normal']
    assert [row['reference'] for row in components] == [F(1), F(-2), F(3), F(-4), F(-22), F.from_float(.2), F(5)]
    assert ports[0]['columns'] == [None, 0, 1] and ports[1]['columns'] == [5, 2, 3]
    assert len(ports) == 4 and all(row['id'] != 'disabled' for row in components)


@pytest.mark.parametrize('change', ['axial-off', 'negative-normal', 'negative-panel-axial', 'nonfinite', 'duplicate-id'])
def test_invalid_source_force_domains_and_identities_refuse(change):
    partitions, field = source_fixture()
    if change == 'axial-off':
        field['response']['connector_local_force_n'][0][0] = 1e-100
    elif change == 'negative-normal':
        field['response']['normal_contact_force_n'][0] = -1e-100
    elif change == 'negative-panel-axial':
        field['response']['connector_local_force_n'][1][0] = -1e-100
    elif change == 'nonfinite':
        field['response']['connector_local_force_n'][0][1] = np.inf
    else:
        partitions['tangents'].append(copy.deepcopy(partitions['tangents'][0]))
    with pytest.raises(ValueError):
        audit.register(partitions, field, {'enabled'})


def test_duplicate_csr_port_coefficients_retain_the_exact_small_remainder():
    matrix = csr_matrix((np.array([1., -1., 2**-100]), np.array([0, 0, 0]), np.array([0, 3])), shape=(1, 1))
    assert audit.scalar_row(matrix, 0) == {0: F(1, 2**100)}


def core_fixture():
    raw = {'body': 'known', 'family': 'synthetic', 'global_coordinates': [0, 1, 2],
           'rows': rows([[1, -1, 0], [-1, 2, -1], [0, -1, 1]]), 'rigid': rows([[1], [1], [1]])}
    record, _, _ = audit.core.certify_core(raw['rows'], raw['rigid'], datum=[0])
    certificate = {key: raw[key] for key in ['body', 'family', 'global_coordinates']} | record
    blocks = audit.certified_blocks([raw], [certificate])
    return raw, certificate, blocks


def test_certified_local_core_reproduces_the_known_connected_body_action_and_energy():
    _, _, blocks = core_fixture()
    force, twice_energy = audit.elastic_action([F(1), F(2), F(4)], blocks)
    assert force == [F(-1), F(-1), F(2)] and twice_energy == 5
    assert sum(force) == 0
    shifted, changed = audit.elastic_action([F(8), F(9), F(11)], blocks)
    assert shifted == force and changed == twice_energy


@pytest.mark.parametrize('change', ['matrix', 'rigid', 'datum', 'mu', 'G'])
def test_a_changed_source_block_or_certificate_cannot_enter_residual_compliance(change):
    raw, certificate, _ = core_fixture()
    if change == 'matrix':
        raw['rows'][1][1] += F(1, 2**100)
    elif change == 'rigid':
        raw['rigid'][1][0] += F(1, 2**100)
    elif change == 'datum':
        certificate['exact_datum_inverse_sha256'] = 'changed'
    elif change == 'mu':
        certificate['quotient_positive_certificate']['exact_smallest_eigenvalue_lower'] = '100'
    else:
        certificate['quotient_positive_certificate']['exact_matrix_sha256'] = 'changed'
    with pytest.raises(ValueError):
        audit.certified_blocks([raw], [certificate])


def test_free_residual_bound_carries_the_original_load_and_the_whole_correction_box():
    _, _, blocks = core_fixture()
    force, _ = audit.elastic_action([F(1), F(2), F(4)], blocks)
    components = [{'row': {0: F(1), 1: F(-1)}}]
    bound, records = audit.residual_bound([F(1), F(0), F(-1)], force, components, [F(2)], [F(1, 100)],
                                         blocks, rows([[1], [1], [1]]), [F(0)])
    # h=(0,3,-3) before correction; free norm box is (3.01,3).
    expected_square = F(301, 100)**2+9
    assert F(records[0]['exact_free_residual_square_upper']) == expected_square
    mu = blocks[0]['mu']
    assert expected_square/mu <= bound < expected_square/mu+F(1, 10**24)
    for epsilon in [F(-1, 100), F(0), F(1, 100)]:
        # G^-1=[[1,1],[1,2]], exact complementary norm of corrected h.
        h = [3+epsilon, F(-3)]
        actual = h[0]**2+2*h[0]*h[1]+2*h[1]**2
        assert actual <= bound


def test_a_non_rigid_orthogonal_elastic_action_cannot_hide_in_a_small_residual():
    _, _, blocks = core_fixture()
    force, _ = audit.elastic_action([F(1), F(2), F(4)], blocks)
    force[0] += F(1, 2**100)
    with pytest.raises(ValueError, match='certified rigid projection'):
        audit.residual_bound([F(1), F(0), F(-1)], force, [{'row': {0: F(1), 1: F(-1)}}], [F(2)], [F(0)],
                             blocks, rows([[1], [1], [1]]), [F(0)])


def test_sparse_functional_compression_preserves_every_global_column():
    candidate = list(map(F, range(8)))
    radius, stiffness = [F(1, 100)]*8, [F(3)]*8
    actual = audit.functional([{2: F(1), 7: F(-2)}, {7: F(3)}], candidate, radius, stiffness, F(1, 5))
    expected = audit.method.functional([{0: F(1), 1: F(-2)}, {1: F(3)}], [F(2), F(7)], [F(1, 100)]*2, [F(3)]*2, F(1, 5))
    assert actual == expected


def test_exactly_zero_functionals_do_not_gain_a_spurious_reaction_radius():
    result = audit.functional([{}, {}, {}], [F(1)], [F(1, 100)], [F(2)], F(1))
    assert result['norm_upper'] == 0 and F(result['exact_weighted_Gram_spectral_upper']) == 0


def rotated_gauss_pair():
    basis = [[0, 0, 1], [F(3, 5), F(4, 5), 0], [F(-4, 5), F(3, 5), 0]]
    return [{'descriptor': {'basis': basis, 'point_xyz_mm': [7, -3, 9]}, 'columns': [None, 2, 7]},
            {'descriptor': {'basis': basis, 'point_xyz_mm': [7, -3, 13]}, 'columns': [None, 4, 9]}]


def test_rotated_asymmetric_two_gauss_force_and_couple_have_independent_signed_answers():
    pair = rotated_gauss_pair()
    force, couple = audit.bearing_rows(pair, [7, -3, 11])
    candidate = [F(0)]*10
    candidate[2], candidate[7], candidate[4], candidate[9] = F(5), F(-10), F(-15), F(20)
    # World station forces are (-11,2,0) and (25,0,0); arms are z=-2,+2.
    assert audit.core.action(force, candidate) == [F(14), F(2), F(0)]
    assert audit.core.action(couple, candidate) == [F(4), F(72), F(0)]
    result = audit.functional(couple, candidate, [F(0)]*10, [F(1)]*10, F(0))
    assert list(map(F, result['exact_candidate_center'])) == [F(4), F(72), F(0)]


def test_opposing_gauss_forces_cancel_the_resultant_while_preserving_the_couple():
    force, couple = audit.bearing_rows(rotated_gauss_pair(), [7, -3, 11])
    candidate = [F(0)]*10
    candidate[2], candidate[7], candidate[4], candidate[9] = F(5), F(-10), F(-5), F(10)
    assert audit.core.action(force, candidate) == [F(0)]*3
    assert audit.core.action(couple, candidate) == [F(8), F(44), F(0)]


def floor_pair_fixture():
    return [{'descriptor': {'kind': 'floor_normal', 'first': body, 'id': f'{body}/{i}', 'direction_xyz': [0., 0., 1.]},
             'columns': [i+offset]} for offset, body in [(0, 'own'), (4, 'other')] for i in range(4)]


@pytest.mark.parametrize('value,gap,expected', [(F(25), F(0), True), (F(0), F(0), False),
    (F(25), F(1000), False), (F(1, 2**100), F(0), True)])
def test_leg_normal_classification_uses_its_exact_own_summed_lower_bound(value, gap, expected):
    ports = floor_pair_fixture()
    candidate = [value]*4+[F(10**8)]*4
    result = audit.rear_leg(ports, 'own', candidate, [F(0)]*8, [F(2)]*8, gap)
    assert result['strict_positive_normal_resultant_certified'] is expected
    lower = F(result['normal_resultant']['exact_scalar_lower'])
    assert (lower > 0) is expected
    if gap == 0:
        assert lower == 4*value


@pytest.mark.parametrize('change', ['direction', 'duplicate', 'missing'])
def test_leg_bearing_cannot_credit_foreign_or_incomplete_floor_ports(change):
    ports = floor_pair_fixture()
    if change == 'direction':
        ports[0]['descriptor']['direction_xyz'] = [1., 0., 0.]
    elif change == 'duplicate':
        ports[1]['descriptor']['id'] = ports[0]['descriptor']['id']
    else:
        ports.pop(0)
    with pytest.raises(ValueError, match='distinct own upward'):
        audit.rear_leg(ports, 'own', [F(1)]*8, [F(0)]*8, [F(2)]*8, F(0))
