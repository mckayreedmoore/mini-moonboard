"""Controls for finer-field equilibrium, claim boundaries and exact mesh pairs."""
import copy

import numpy as np
import pytest
from scipy import sparse

from scripts import eoere_cleat_field_refinement_audit as audit


def response_fixture():
    nodes = np.array([[0., 0., 0.], [1., 0., 0.]])
    force = np.zeros((6, 48))
    force[0], force[3] = 1., -1.
    return sparse.eye(6).tocsr(), nodes, force, force.copy(), np.ones(48)


def test_saved_equilibrium_and_work_are_recovered_without_factorization():
    energy, result = audit.field_response(*response_fixture())
    assert energy == pytest.approx(np.ones(48))
    assert result == {'maximum_residual_n': 0., 'complete_force_residual_n': 0.,
                      'complete_moment_residual_nmm': 0., 'maximum_strain_work_difference_nmm': 0.}


@pytest.mark.parametrize('mutation,message', [('displacement', 'equilibrium'), ('energy', 'energies differ'),
                                             ('force', 'load wrench'), ('moment', 'load wrench'),
                                             ('nonfinite', 'finite complete'), ('truncated', '48-column')])
def test_consistent_metadata_cannot_hide_a_bad_saved_field(mutation, message):
    k, nodes, force, u, energy = response_fixture()
    if mutation == 'displacement':
        u[0, 0] += .01
    elif mutation == 'energy':
        energy[0] += .01
    elif mutation == 'force':
        force[0, 0] += .01
        u = force.copy()
    elif mutation == 'moment':
        force[1, 0], force[4, 0] = .1, -.1
        u = force.copy()
    elif mutation == 'nonfinite':
        u[0, 0] = np.nan
    else:
        force, u = force[:, :-1], u[:, :-1]
    with pytest.raises(ValueError, match=message):
        audit.field_response(k, nodes, force, u, energy)


def paired_fixture():
    row = {'member': 'left', 'case_id': 'a12-left', 'state_id': 'own',
           'field': {'path': 'own.json', 'sha256': 'ownhash'}, 'bore_id': 'bore1', 'tip': 'high',
           'radius_increment_mm': 15., 'coincident_point_side': -1,
           'initial_final_area_mm2': [2., 3.], 'signed_free_face_energy_release_n_per_mm': .01,
           'signed_contact_upper_reference_n_per_mm': .02, 'intact_sampled_tension_reference_index': 2.}
    second = {**row, 'bore_id': 'bore2', 'tip': 'low'}
    job = {'plane_mm': -25.4, 'swap_RT': False, 'mesh_size_mm': 10.}
    coarse = [{'job': job, 'comparisons': [row, second]}]
    fine = copy.deepcopy(coarse)
    fine[0]['job']['mesh_size_mm'] = 7.5
    for r in fine[0]['comparisons']:
        r.update(signed_free_face_energy_release_n_per_mm=.009,
                 signed_contact_upper_reference_n_per_mm=.01, intact_sampled_tension_reference_index=1.)
    return coarse, fine


def test_pairing_preserves_failed_guards_and_counts_intact_fields_once():
    energy, stress = audit.pair_checks(*paired_fixture(), .2)
    assert len(energy) == 4 and len(stress) == 1
    assert [r['within_declared_20_percent_guard'] for r in energy] == [True, False, True, False]
    assert [r['relative_change'] for r in energy] == pytest.approx([.1, .5, .1, .5])
    assert stress[0]['relative_change'] == .5 and stress[0]['within_declared_20_percent_guard'] is False


@pytest.mark.parametrize('key,value', [('member', 'right'), ('case_id', 'other'), ('state_id', 'other'),
                                    ('field', {'path': 'other.json', 'sha256': 'ownhash'}),
                                    ('bore_id', 'wrongbore'), ('tip', 'low'), ('radius_increment_mm', 30.),
                                    ('coincident_point_side', 1)])
def test_mesh_pairing_refuses_a_changed_physical_identity(key, value):
    coarse, fine = paired_fixture()
    fine[0]['comparisons'][0][key] = value
    with pytest.raises(ValueError, match='identity set'):
        audit.pair_checks(coarse, fine, .2)


@pytest.mark.parametrize('change', ['duplicate', 'missing', 'area', 'inconsistent_stress', 'nonfinite'])
def test_duplicate_truncated_or_inconsistent_pair_results_are_refused(change):
    coarse, fine = paired_fixture()
    if change == 'duplicate':
        fine[0]['comparisons'].append(copy.deepcopy(fine[0]['comparisons'][0]))
    elif change == 'missing':
        fine[0]['comparisons'].pop()
    elif change == 'area':
        fine[0]['comparisons'][0]['initial_final_area_mm2'][0] += 1.
    elif change == 'inconsistent_stress':
        fine[0]['comparisons'][1]['intact_sampled_tension_reference_index'] = .9
    else:
        fine[0]['comparisons'][0]['signed_free_face_energy_release_n_per_mm'] = np.nan
    with pytest.raises(ValueError):
        audit.pair_checks(coarse, fine, .2)


def job_fixture():
    # Scope control uses a source-shaped synthetic inventory, not ignored raw fields.
    inputs = {'seed_results': ['seed'], 'original_seed_job_indices': [4], 'parent_inputs': 'parent',
              'parent_saved_field_audit': 'audit', 'new_mesh_size_mm': 7.5,
              'geometry_revision': 'eoere-raised-kicker-screws-v1',
              'hardware_revision': 'eoere-selected-purchase-hardware-v1'}
    seed = {'job': {'mesh_size_mm': 10., 'plane_mm': -25.4, 'swap_RT': False},
            'geometry': {'own': 'shape'}, 'records': [{'case_id': 'own'}],
            'configurations': [{'index': i, 'interval': None if i == 0 else [i, i+1]} for i in range(7)]}
    result = {'schema': 'eoere_current_refined_fixed_action_finite_crack_comparisons/v1',
              'status': 'CURRENT_DECLARED_FINER_GRID_BORE_FLAW_COMPARISONS_COMPLETE_LOCAL_MODEL_ONLY',
              'inputs': 'input', 'job_index': 0, 'source_seed': 'seed', 'original_seed_job_index': 4,
              'parent_inputs': 'parent', 'parent_saved_field_audit': 'audit',
              'job': {**seed['job'], 'mesh_size_mm': 7.5}, 'geometry': seed['geometry'], 'records': seed['records'],
              'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
              'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False, 'actual_observations': None,
              'local_python_elastic_comparison_performed': True, 'whole_frame_or_native_executable_solve_performed': False,
              'physical_demand_bounds_established': False, 'complete_cleat_joint_or_member_resistance': None,
              'structural_acceptance': False, 'configurations': copy.deepcopy(seed['configurations']), 'comparisons': [None]*192}
    return result, inputs, seed


def test_only_completed_own_job_with_false_qualification_boundary_is_admitted():
    result, inputs, seed = job_fixture()
    audit.check_job(result, 'input', inputs, seed, 0)


@pytest.mark.parametrize('change', ['geometry', 'actions', 'seed', 'pending', 'grid', 'crack', 'acceptance',
                                  'physical', 'resistance', 'observations', 'bolts', 'missing'])
def test_wrong_seed_pending_work_and_qualification_promotions_are_refused(change):
    result, inputs, seed = job_fixture()
    result = copy.deepcopy(result)
    if change == 'geometry':
        result['geometry']['own'] = 'other'
    elif change == 'actions':
        result['records'][0]['case_id'] = 'other'
    elif change == 'seed':
        result['source_seed'] = 'other'
    elif change == 'pending':
        result['status'] = 'CURRENT_FINER_GRID_GEOMETRY_LOADS_AND_SOURCES_PREPARED_RESPONSE_PENDING'
    elif change == 'grid':
        result['job']['mesh_size_mm'] = 5.
    elif change == 'crack':
        result['configurations'][1]['interval'] = [9., 10.]
    elif change == 'acceptance':
        result['structural_acceptance'] = True
    elif change == 'physical':
        result['physical_demand_bounds_established'] = True
    elif change == 'resistance':
        result['complete_cleat_joint_or_member_resistance'] = 1.
    elif change == 'observations':
        result['actual_observations'] = 'assumed'
    elif change == 'bolts':
        result['current_bolt_count'] = 102
    else:
        result['comparisons'].pop()
    with pytest.raises(ValueError):
        audit.check_job(result, 'input', inputs, seed, 0)
