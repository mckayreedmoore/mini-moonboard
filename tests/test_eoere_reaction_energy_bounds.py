"""Known equilibria, contact switches, conjugacy and source/claim controls."""
import copy
import math
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix, eye, vstack

from scripts import eoere_reaction_energy_bounds as bounds
from scripts import thin_bolted_numerical_step as original


def inputs():
    return bounds.current.read(bounds.current.ref(bounds.INPUT))


@pytest.mark.parametrize('alpha,beta', [(1., 1.), (.5, 2.), (.1, 10.)])
def test_exact_parallel_spring_equilibria_obey_force_and_total_complementary_gap_bounds(alpha, beta):
    k0 = np.array([2., 3.])
    load = 10.
    q0 = load/sum(k0)
    r0 = k0*q0
    quadratic = .5*sum(k0)*q0**2
    gap = bounds.gap_factor(alpha, beta)*quadratic
    for m1 in (alpha, 1., beta):
        for m2 in (alpha, 1., beta):
            knew = k0*np.array([m1, m2])
            qnew = load/sum(knew)  # Exact independent closed-form equilibrium.
            rnew = knew*qnew
            assert sum((rnew-r0)**2/(2*knew)) <= gap+1e-12
            for j in (0, 1):
                assert abs(rnew[j]-r0[j]) <= bounds.perturbation_bound(gap, beta*k0[j])+1e-12


def test_radial_clearance_contact_can_deactivate_inside_the_declared_interval():
    # Scalar radial analogue: F=q+max(q-1,0), so F=1.5 gives q0=1.25.
    q0, old = 1.25, np.array([1.25, .25])
    quadratic = .5*float(old@old)
    gap = bounds.gap_factor(.5, 2.)*quadratic
    qnew, new = .75, np.array([1.5, 0.])  # First stiffness doubles; clearance branch opens.
    assert qnew < 1. < q0 and sum(old) == sum(new) == 1.5
    assert sum((new-old)**2/(2*np.array([2., .5]))) <= gap
    assert abs(new[1]-old[1]) <= bounds.perturbation_bound(gap, 2.)
    # Complementary energy includes c*F on the active clearance port.
    primal = .5*q0**2+.5*(q0-1)**2-1.5*q0
    assert quadratic+old[1] == pytest.approx(-primal)


def test_compression_contact_can_activate_when_a_coupled_spring_is_softened():
    # Coordinates q=(x,y), fixed x/y load. Contact Cq=x-y initially open.
    # Core diagonal (2,1), load (1,1): q0=(.5,1), old contact force zero.
    # New core (.5,1) plus unit compression contact has positive Cq.
    old_q = np.array([.5, 1.])
    old_core = np.diag([2., 1.])
    load = np.ones(2)
    new_core = np.diag([.5, 1.])
    contact = np.array([1., -1.])
    new_q = np.linalg.solve(new_core+np.outer(contact, contact), load)
    new_force = float(contact@new_q)
    assert contact@old_q < 0. < new_force
    quadratic = .5*float(old_q@old_core@old_q)
    gap = bounds.gap_factor(.25, 4.)*quadratic
    assert new_force <= bounds.perturbation_bound(gap, 1.)


def test_rotated_core_loewner_interval_bounds_its_fenchel_gap_without_commuting_with_old_core():
    core = np.array([[4., 1.], [1., 2.]])
    values, vectors = np.linalg.eigh(core)
    root = (vectors*np.sqrt(values))@vectors.T
    rotation = np.array([[.6, -.8], [.8, .6]])
    alpha, beta = .5, 2.
    trial = root@(rotation@np.diag([alpha, beta])@rotation.T)@root
    q = np.array([2., -3.])
    z0 = core@q
    actual_gap = .5*float(q@trial@q+z0@np.linalg.solve(trial, z0))-float(q@z0)
    quadratic = .5*float(q@core@q)
    assert 0. <= actual_gap <= bounds.gap_factor(alpha, beta)*quadratic+1e-12


@pytest.mark.parametrize('alpha,beta', [(0., 2.), (-1., 2.), (1.1, 2.), (.5, .9), (np.nan, 2.), (.5, np.inf)])
def test_invalid_family_cannot_produce_a_bound(alpha, beta):
    with pytest.raises(ValueError):
        bounds.gap_factor(alpha, beta)


@pytest.mark.parametrize('gap,stiffness', [(-1., 1.), (1., -1.), (np.nan, 1.), (1., np.inf)])
def test_invalid_gap_or_stiffness_is_rejected(gap, stiffness):
    with pytest.raises(ValueError):
        bounds.perturbation_bound(gap, stiffness)


def test_conjugacy_keeps_clearance_work_and_handles_zero_axial_stiffness():
    row = {'ka': 0., 'kl': 2., 'clearance': .5, 'tension_only': False}
    quadratic, travel = bounds.group_energy(row, [0., 3., 4.])
    assert quadratic == 6.25 and travel == 2.5
    assert bounds.contact_energy({'stiffness': 2.}, 3.) == 2.25
    assert bounds.group_energy(row, [0., 0., 0.]) == (0., 0.)


@pytest.mark.parametrize('change', ['zero_axial', 'zero_lateral', 'negative_tension', 'negative_k', 'negative_gap', 'nonfinite'])
def test_force_outside_a_spring_conjugate_domain_is_refused(change):
    row = {'ka': 1., 'kl': 2., 'clearance': .5, 'tension_only': False}
    force = [1., 3., 4.]
    if change == 'zero_axial':
        row['ka'] = 0.
    elif change == 'zero_lateral':
        row['kl'] = 0.
    elif change == 'negative_tension':
        row['tension_only'], force[0] = True, -1.
    elif change == 'negative_k':
        row['kl'] = -1.
    elif change == 'negative_gap':
        row['clearance'] = -1.
    else:
        force[0] = np.nan
    with pytest.raises(ValueError):
        bounds.group_energy(row, force)


def test_negative_normal_force_is_not_dual_feasible():
    with pytest.raises(ValueError):
        bounds.contact_energy({'stiffness': 2.}, -1.)


def wood_fixture():
    length = 38.1
    surface = {'kind': 'wood', 'host': 'ownwood', 'interval_mm': [0., length]}
    shaft = {'axis_id': 'ownbolt', 'body': 'shaft/ownbolt', 'basis': np.eye(3).tolist(),
             'point': [0., 0., 0.], 'surfaces': [surface]}
    ports = []
    for i, sign in enumerate((-1., 1.)):
        row = {'id': f'ownbolt/bearing-{i}', 'axis_id': 'ownbolt', 'surface': surface,
               'first': 'shaft/ownbolt', 'second': 'ownwood', 'surface_index': 0, 'quad_index': i,
               'kind': 'common_shaft_bearing', 'basis': np.eye(3).tolist(), 'ka': 0., 'kl': 500.,
               'weight_length_mm': length/2, 'point_xyz_mm': [length/2+sign*length/(2*math.sqrt(3)), 0., 0.]}
        force = np.array([0., sign*10., 0.])
        action = {key: row[key] for key in ('id', 'axis_id', 'first', 'second', 'surface_index', 'quad_index', 'point_xyz_mm')}
        action.update(surface_interval_mm=surface['interval_mm'], force_on_first_xyz_n=(-force).tolist(),
                      force_on_second_xyz_n=force.tolist(), moment_on_first_at_point_xyz_nmm=[0., 0., 0.],
                      moment_on_second_at_point_xyz_nmm=[0., 0., 0.])
        ports.append({'row': row, 'force': force, 'source_action': action})
    return shaft, ports


def test_own_gauss_force_cancellation_retains_a_free_bearing_couple_and_cauchy_arms():
    shaft, ports = wood_fixture()
    row = bounds.wood_surface(ports[0]['row'], shaft, ports, 2., 2.)
    assert row['old_force_on_shaft_xyz_n'] == [0., 0., 0.]
    assert row['old_couple_on_shaft_xyz_nmm'] == pytest.approx([0., 0., -10*38.1/math.sqrt(3)])
    assert row['force_change_norm_upper_n'] == pytest.approx(math.sqrt(8000.))
    assert row['couple_change_norm_upper_nmm'] == pytest.approx(math.sqrt(8000.)*38.1/math.sqrt(12))
    assert row['complete_joint_or_brittle_resistance'] is None


@pytest.mark.parametrize('change', ['foreign_surface', 'missing_port', 'duplicate_quad', 'station', 'basis',
                                  'stiffness', 'coverage', 'foreign_first', 'saved_sign', 'saved_couple'])
def test_foreign_or_changed_wood_surface_cannot_enter_an_enclosure(change):
    shaft, ports = copy.deepcopy(wood_fixture())
    if change == 'foreign_surface':
        ports[1]['row']['surface'] = {**ports[1]['row']['surface'], 'host': 'other'}
    elif change == 'missing_port':
        ports.pop()
    elif change == 'duplicate_quad':
        ports[1]['row']['quad_index'] = 0
    elif change == 'station':
        ports[1]['row']['point_xyz_mm'][0] += 1.
    elif change == 'basis':
        ports[1]['row']['basis'][0][0] = 2.
    elif change == 'stiffness':
        ports[1]['row']['kl'] = 1000.
    elif change == 'coverage':
        ports[1]['row']['weight_length_mm'] = 10.
    elif change == 'foreign_first':
        ports[1]['row']['first'] = 'other-shaft'
    elif change == 'saved_sign':
        ports[1]['source_action']['force_on_first_xyz_n'][1] *= -1.
    else:
        ports[1]['source_action']['moment_on_first_at_point_xyz_nmm'][0] = 1.
    with pytest.raises(ValueError):
        bounds.wood_surface(ports[0]['row'], shaft, ports, 2., 2.)


def census_fixture():
    groups = []
    for kind, count in bounds.GROUP_COUNTS.items():
        groups += [{'id': f'{kind}-{i}', 'kind': kind, 'ka': 0. if kind == 'common_shaft_bearing' else 2.,
                    'kl': 2., 'clearance': .5, 'tension_only': kind == 'panel_screw', 'B': eye(3, format='csr')}
                   for i in range(count)]
    contacts = []
    for kind, count in bounds.CONTACT_COUNTS.items():
        contacts += [{'id': f'{kind}-{i}', 'kind': kind, 'stiffness': 3., 'B': csr_matrix([[1., 0., 0.]])}
                     for i in range(count)]
    tangents = [{'id': f'foot-{i}', 'kind': 'floor_tangent', 'first': 'lumber_leg_left' if i < 2 else
                 'lumber_leg_right' if i < 4 else f'other-{i//2}', 'stiffness': 4., 'B': csr_matrix([[0., 1., 0.]])}
                for i in range(16)]
    q, core = np.array([1., 2., 3.]), eye(3, format='csr')

    def replay(k, applied, groups, contacts, tangents, state):
        linear = k.copy()
        for row in tangents[:4]:
            linear += row['stiffness']*(row['B'].T@row['B'])
        return original.physical_fields(linear, applied, groups, vstack([r['B'] for r in contacts]),
                                        np.array([r['stiffness'] for r in contacts]), state)

    expected_gradient = np.array([2e-6, -3e-6, 4e-6])
    internal = replay(core, np.zeros(3), groups, contacts, tangents, q)[0]
    applied = internal-expected_gradient
    response = replay(core, applied, groups, contacts, tangents, q)
    snapshot = SimpleNamespace(assembly=SimpleNamespace(K=core), applied=applied, groups=groups,
                               contacts=contacts, tangents=tangents)
    field = {'response': {'q': q.tolist(), 'connector_local_force_n': np.asarray(response[3]).tolist(),
                         'normal_contact_force_n': response[4].tolist(), 'potential_energy_nmm': response[1]}}
    binding = {'case_id': 'control', 'state_id': 'own', 'field': {'path': 'fixture', 'sha256': 'control'}}
    return binding, field, snapshot, SimpleNamespace(law=SimpleNamespace(replay=replay))


def test_current_census_seed_recovers_conjugate_energy_and_preserves_nonzero_load_residual():
    binding, field, snapshot, frozen = census_fixture()
    data, ports = bounds.seed(binding, field, snapshot, frozen, inputs())
    assert len(ports) == 2324
    assert data['dual_load_correction_inf_n'] == pytest.approx(4e-6, abs=1e-9)
    assert data['original_load_is_exactly_dual_feasible'] is False
    assert data['original_load_canonical_sha256'] != data['dual_feasible_load_canonical_sha256']
    assert data['complementary_energy_nmm'] > data['quadratic_complementary_energy_nmm']
    assert abs(data['conjugacy_identity_error_nmm']) < 1e-5
    assert data['variable_quadratic_energy_nmm'] < data['quadratic_complementary_energy_nmm']


@pytest.mark.parametrize('change', ['missing_group', 'foreign_force', 'potential', 'unbalanced_load', 'asymmetry'])
def test_source_census_force_potential_residual_and_core_symmetry_guards(change):
    binding, field, snapshot, frozen = census_fixture()
    if change == 'missing_group':
        snapshot.groups.pop()
    elif change == 'foreign_force':
        field['response']['connector_local_force_n'][0][0] += 1.
    elif change == 'potential':
        field['response']['potential_energy_nmm'] += 1.
    elif change == 'unbalanced_load':
        snapshot.applied[0] += 1.
    else:
        snapshot.assembly.K = csr_matrix([[1., 1., 0.], [0., 1., 0.], [0., 0., 1.]])
    with pytest.raises(ValueError):
        bounds.seed(binding, field, snapshot, frozen, inputs())


@pytest.mark.parametrize('key,value', [('structural_acceptance', True), ('physical_demand_bounds_established', True),
                                    ('actual_observations', 'assumed'), ('current_bolt_count', 102),
                                    ('fixed_spring_kinds', []), ('energy_padding_nmm', 1.),
                                    ('wood_land_reference_mpa', .5), ('runtime_versions', {})])
def test_scope_and_unobserved_family_inputs_cannot_be_promoted(key, value):
    data = inputs()
    bounds.validate(data)
    data[key] = value
    with pytest.raises(ValueError):
        bounds.validate(data)
