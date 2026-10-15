"""Own-field identity, hypothesis preservation and new energy reconstruction."""
import copy

import pytest

from scripts import eoere_cleat_field_refinement as method


def fixture():
    labels = [{'member': member, 'case_id': f'case{i}', 'state_id': f'state{i}',
               'field': {'path': f'field{i}.json', 'sha256': f'hash{i}'},
               'radius_increment_mm': 15., 'coincident_point_side': -1}
              for i, member in enumerate(method.MEMBERS)]
    seed = {'geometry': {member: {'bores': [{'id': f'own-bore{i}', 'origin': [20., 0., 0.], 'radius_mm': 2.}]}
                         for i, member in enumerate(method.MEMBERS)},
            'job': {'mesh_size_mm': 10., 'plane_mm': 0., 'swap_RT': False},
            'comparisons': [{**label, 'bore_id': f'own-bore{i}', 'tip': tip,
                             'energies_nmm': [-999., -999., -999.],
                             'signed_free_face_energy_release_n_per_mm': -777.}
                            for i, label in enumerate(labels) for tip in ('low', 'high')]}
    states = [(None, [1., 2.], 0.), ((13., 27.), [3., 4.], 4.),
              ((8., 27.), [7., 8.], 6.), ((13., 32.), [9., 10.], 6.)]
    configs = [{'interval': interval, 'labels': labels, 'response': {'strain_energy_nmm': energies},
                'census': {'crack_area_mm2': area}, 'sampled_transverse_tension_mpa': [.03, .04]}
               for interval, energies, area in states]
    return seed, configs, {'Gc_all_modes_n_per_mm': [.1, .05], 'Ft90_reference_mpa': .2}


def test_new_field_energies_replace_coarse_numbers_without_changing_own_case_bore_or_hypotheses():
    seed, configs, base = fixture()
    original = copy.deepcopy(seed)
    rows = method.comparisons(seed, configs, base)
    assert seed == original
    assert len(rows) == 4
    assert rows[0]['energies_nmm'] == [1., 3., 7.]
    assert rows[0]['signed_free_face_energy_release_n_per_mm'] == 2.
    assert rows[0]['signed_contact_upper_reference_n_per_mm'] == 3.
    assert rows[0]['common_energy_hypothesis_indices'] == [
        {'Gc_n_per_mm': .1, 'signed_free_face_index': 20., 'signed_contact_upper_index': 30.},
        {'Gc_n_per_mm': .05, 'signed_free_face_index': 40., 'signed_contact_upper_index': 60.}]
    assert rows[0]['intact_sampled_tension_reference_index'] == pytest.approx(.15)
    assert rows[2]['energies_nmm'] == [2., 4., 8.]
    assert rows[2]['member'] == 'eoere_cleat_right'
    assert rows[2]['bore_id'] == 'own-bore1'
    assert rows[2]['case_id'] == 'case1' and rows[2]['field'] == {'path': 'field1.json', 'sha256': 'hash1'}
    assert all(row['fracture_or_complete_joint_qualification'] is False for row in rows)


def test_duplicate_physical_comparison_is_rejected():
    seed, configs, base = fixture()
    seed['comparisons'].append(seed['comparisons'][0])
    with pytest.raises(ValueError, match='duplicate physical'):
        method.comparisons(seed, configs, base)


def test_duplicate_column_identity_is_rejected():
    seed, configs, base = fixture()
    for c in configs:
        c['labels'] = [c['labels'][0], c['labels'][0]]
    with pytest.raises(ValueError, match='exactly one own field column'):
        method.comparisons(seed, configs, base)


def test_changed_configuration_column_order_is_rejected():
    seed, configs, base = fixture()
    configs[1]['labels'] = configs[1]['labels'][::-1]
    with pytest.raises(ValueError, match='column labels changed'):
        method.comparisons(seed, configs, base)


def test_duplicate_or_misordered_intact_configuration_is_rejected():
    seed, configs, base = fixture()
    with pytest.raises(ValueError, match='first configuration'):
        method.comparisons(seed, configs[::-1], base)
    with pytest.raises(ValueError, match='duplicate crack'):
        method.comparisons(seed, configs+[configs[1]], base)


def test_reduced_energy_or_nonpositive_added_sound_area_is_rejected():
    seed, configs, base = fixture()
    configs[2]['response']['strain_energy_nmm'][0] = .5
    with pytest.raises(ValueError, match='nested crack'):
        method.comparisons(seed, configs, base)
    seed, configs, base = fixture()
    configs[2]['census']['crack_area_mm2'] = 3.
    with pytest.raises(ValueError, match='positive added sound area'):
        method.comparisons(seed, configs, base)


@pytest.mark.parametrize('field,value', [('new_mesh_size_mm', 10.), ('two_grid_relative_change_guard', .5),
                                        ('original_seed_job_indices', [0, 1, 2, 3]), ('current_bolt_count', 102),
                                        ('current_screw_count', 65), ('extra_grid', True),
                                        ('actual_observations', {}), ('structural_acceptance', True)])
def test_refinement_cannot_weaken_guards_or_change_the_current_scope(field, value):
    inputs = method.current.read(method.current.ref(method.INPUT))
    inputs[field] = value
    with pytest.raises(ValueError):
        method.validate(inputs)


def test_seed_identity_is_bound_to_its_own_material_plane_and_completed_scope():
    parent = {'path': 'frozen-parent.json', 'sha256': 'frozen-hash'}
    seed = {'schema': 'eoere_current_fixed_action_finite_crack_comparisons/v1',
            'status': 'CURRENT_DECLARED_BORE_FLAW_COMPARISONS_COMPLETE_LOCAL_MODEL_ONLY',
            'inputs': parent, 'job_index': 4, 'job': {'mesh_size_mm': 10., 'plane_mm': -25.4, 'swap_RT': False},
            'configurations': [None]*7, 'comparisons': [None]*192,
            'geometry': {member: {} for member in method.MEMBERS},
            'records': [{'member': member, 'case_id': f'case{i}'} for i in range(6) for member in method.MEMBERS],
            'current_bolt_count': 100, 'current_screw_count': 66, 'structural_acceptance': False,
            'complete_cleat_joint_or_member_resistance': None, 'physical_demand_bounds_established': False,
            'whole_frame_or_native_executable_solve_performed': False}
    method.check_seed(seed, parent, 4)
    wrong = copy.deepcopy(seed)
    wrong['job']['swap_RT'] = True
    with pytest.raises(ValueError, match='own seed material/plane'):
        method.check_seed(wrong, parent, 4)
    wrong = copy.deepcopy(seed)
    wrong['job']['mesh_size_mm'] = 15.
    with pytest.raises(ValueError, match='complete own10-mm seed'):
        method.check_seed(wrong, parent, 4)
    wrong = copy.deepcopy(seed)
    wrong['structural_acceptance'] = True
    with pytest.raises(ValueError):
        method.check_seed(wrong, parent, 4)
