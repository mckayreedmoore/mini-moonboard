"""Independently audit saved finer cleat fields and pair them with frozen 10-mm fields.

The frozen field-auditor helpers supply direct entry assembly, seam topology,
load fingerprints and stress recovery. No factorization or model solve occurs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts import eoere_cleat_field_refinement as refinement

model, checks, current = refinement.model, refinement.checks, refinement.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
ENERGY_METRICS = ('signed_free_face_energy_release_n_per_mm', 'signed_contact_upper_reference_n_per_mm')


def check_job(result, inputs_ref, inputs, seed, index):
    current.require(result['schema'] == 'eoere_current_refined_fixed_action_finite_crack_comparisons/v1'
                    and result['status'] == 'CURRENT_DECLARED_FINER_GRID_BORE_FLAW_COMPARISONS_COMPLETE_LOCAL_MODEL_ONLY'
                    and result['inputs'] == inputs_ref and result['job_index'] == index
                    and result['source_seed'] == inputs['seed_results'][index]
                    and result['original_seed_job_index'] == inputs['original_seed_job_indices'][index]
                    and result['parent_inputs'] == inputs['parent_inputs']
                    and result['parent_saved_field_audit'] == inputs['parent_saved_field_audit']
                    and result['job'] == {**seed['job'], 'mesh_size_mm': inputs['new_mesh_size_mm']}
                    and result['geometry'] == seed['geometry'] and result['records'] == seed['records'],
                    'completed finer job must retain its exact own coarse seed geometry and actions')
    current.require(result['geometry_revision'] == inputs['geometry_revision']
                    and result['hardware_revision'] == inputs['hardware_revision']
                    and result['current_bolt_count'] == 100 and result['current_screw_count'] == 66
                    and result['extra_grid'] is False and result['actual_observations'] is None
                    and result['local_python_elastic_comparison_performed'] is True
                    and result['whole_frame_or_native_executable_solve_performed'] is False
                    and result['physical_demand_bounds_established'] is False
                    and result['complete_cleat_joint_or_member_resistance'] is None
                    and result['structural_acceptance'] is False,
                    'unchanged current scope and unqualified physical boundary required')
    current.require(len(result['configurations']) == 7 and len(result['comparisons']) == 192
                    and [(c['index'], c['interval']) for c in result['configurations']] ==
                        [(c['index'], c['interval']) for c in seed['configurations']],
                    'exact complete own crack-configuration inventory required')


def field_response(k, nodes, force, displacement, exported_energy):
    current.require(force.shape == displacement.shape == (3*len(nodes), 48)
                    and np.isfinite(force).all() and np.isfinite(displacement).all(),
                    'finite complete 48-column saved fields required')
    residual = k@displacement-force
    maximum = float(np.max(abs(residual)))
    current.require(maximum < 1e-5, 'independent saved-field equilibrium gate failed')
    physical = force.reshape(len(nodes), 3, -1)
    force_error = float(np.max(abs(physical.sum(axis=0))))
    moment_error = float(np.max(abs(np.cross(nodes[:, :, None], physical,
                                             axisa=1, axisb=1, axisc=1).sum(axis=0))))
    current.require(force_error < 1e-7 and moment_error < 1e-5, 'complete physical load wrench failed')
    work = .5*np.sum(force*displacement, axis=0)
    strain = .5*np.sum(displacement*(k@displacement), axis=0)
    current.require(np.allclose(work, strain, rtol=1e-8, atol=1e-8)
                    and np.allclose(work, exported_energy, rtol=1e-12, atol=1e-10),
                    'independent saved strain/work or exported energies differ')
    return work, {'maximum_residual_n': maximum, 'complete_force_residual_n': force_error,
                  'complete_moment_residual_nmm': moment_error,
                  'maximum_strain_work_difference_nmm': float(np.max(abs(work-strain)))}


def pair_checks(coarse_jobs, fine_jobs, guard):
    def index(jobs):
        rows = {}
        for result in jobs:
            for row in result['comparisons']:
                key = checks.trace_key(row, result['job'])
                current.require(key not in rows, 'duplicate physical comparison in one grid')
                rows[key] = row
        return rows
    coarse, fine = index(coarse_jobs), index(fine_jobs)
    current.require(coarse.keys() == fine.keys(), 'exact own coarse/fine comparison identity set required')
    energy_checks, stress_checks = [], {}
    for key, c in coarse.items():
        f = fine[key]
        current.require(np.allclose(c['initial_final_area_mm2'], f['initial_final_area_mm2'], rtol=0., atol=1e-6),
                        'true flaw areas must remain grid invariant')
        for metric in ENERGY_METRICS:
            change = checks.relative_change(c[metric], f[metric])
            energy_checks.append({'identity': list(key), 'metric': metric, 'coarse': c[metric], 'fine': f[metric],
                                  'relative_change': change, 'within_declared_20_percent_guard': change <= guard})
        stress_key = key[:5]+key[7:]
        cvalue, fvalue = (r['intact_sampled_tension_reference_index'] for r in (c, f))
        if stress_key in stress_checks:
            old = stress_checks[stress_key]
            current.require(old['coarse_index'] == cvalue and old['fine_index'] == fvalue,
                            'one intact stress field must be invariant across its bore-tip comparisons')
        else:
            change = checks.relative_change(cvalue, fvalue)
            stress_checks[stress_key] = {'identity': list(stress_key), 'coarse_index': cvalue, 'fine_index': fvalue,
                                        'relative_change': change, 'within_declared_20_percent_guard': change <= guard}
    return energy_checks, list(stress_checks.values())


def audit_job(result, base, constitutive):
    k_full = model.read_array_file(result['full_operator']['stiffness'], sparse_matrix=True)
    with model.read_array_file(result['full_operator']['mesh']) as full:
        full_nodes, full_elements = full['nodes'], full['elements']
    labels = result['configurations'][0]['labels']
    expected = [{k: r[k] for k in ('case_id', 'state_id', 'field', 'member')} |
                {'radius_increment_mm': radius, 'coincident_point_side': side}
                for radius in base['radius_increments_mm'] for side in base['coincident_point_sides']
                for r in result['records']]
    current.require(labels == expected and len(labels) == 48, 'complete own member/case/cloud field inventory required')
    energies, audits, fingerprints = {}, [], None
    for config in result['configurations']:
        current.require(config['labels'] == labels and len(config['load_maps']) == 4,
                        'saved configuration identities changed')
        with model.read_array_file(config['field']) as field:
            nodes, elements, force, u = (field[k] for k in ('nodes', 'elements', 'F', 'U'))
        checks.verify_crack_topology(nodes, elements, 2, result['job']['plane_mm'], config['interval'],
                                    result['geometry'][refinement.MEMBERS[0]]['length_mm'])
        k = checks.coalesce_operator(k_full, full_nodes, full_elements, nodes, elements)
        work, response = field_response(k, nodes, force, u, config['response']['strain_energy_nmm'])
        actual = checks.verify_fixed_loads(nodes, force, config['load_maps'], result['physical_load_fingerprints'], fingerprints)
        if fingerprints is None:
            fingerprints = actual
        if config['index'] == 0:
            current.require(len(config['sampled_transverse_tension_mpa']) == len(config['sampled_stress_witnesses']) == 48,
                            'all intact sampled-stress witnesses required')
            for col, witness in enumerate(config['sampled_stress_witnesses']):
                if witness is None:
                    current.require(config['sampled_transverse_tension_mpa'][col] == 0., 'positive sample requires a witness')
                    continue
                element = elements[witness['element']]
                dofs = (3*element[:, None]+np.arange(3)).ravel()
                stress = checks.witness_stress(nodes[element], u[dofs, col].reshape(20, 3), constitutive,
                                               witness['gauss_natural'])
                tension = max(0., np.linalg.eigvalsh([[stress[1], stress[5]], [stress[5], stress[2]]])[-1])
                current.require(np.allclose(stress, witness['stress_g_u_v_gu_gv_uv_mpa'], rtol=1e-10, atol=1e-8)
                                and np.isclose(tension, config['sampled_transverse_tension_mpa'][col], rtol=1e-10, atol=1e-8),
                                'independent intact stress witness differs')
        interval = None if config['interval'] is None else tuple(config['interval'])
        area = model.exact_crack_area(result['geometry'][refinement.MEMBERS[0]], result['job']['plane_mm'], config['interval'])
        current.require(interval not in energies and abs(area-config['census']['crack_area_mm2']) < 1e-6,
                        'unique own configuration and true sound area required')
        energies[interval] = (work, area)
        audits.append({'configuration': config['index'], 'field': config['field'], 'full_field_columns': 48, **response})
    for row in result['comparisons']:
        label = {k: row[k] for k in labels[0]}
        current.require(labels.count(label) == 1, 'one exact own current field column required')
        col = labels.index(label)
        bore = next(b for b in result['geometry'][row['member']]['bores'] if b['id'] == row['bore_id'])
        s, r = bore['origin'][0], bore['radius_mm']
        current.require(row['tip'] in ('low', 'high') and abs(bore['origin'][2]-result['job']['plane_mm']) < 1e-7,
                        'own bore and grain-tip identity required')
        initial = (s-r-5., s+r+5.)
        final = (s-r-10., initial[1]) if row['tip'] == 'low' else (initial[0], s+r+10.)
        values = [energies[key][0][col] for key in (None, initial, final)]
        areas = [energies[key][1] for key in (initial, final)]
        area = areas[1]-areas[0]
        free, upper = checks.independent_energies(*values, area)
        current.require(np.allclose(values, row['energies_nmm'], rtol=1e-12, atol=1e-10)
                        and np.allclose(areas, row['initial_final_area_mm2'], rtol=0., atol=1e-6)
                        and np.allclose([free, upper, area], [row[ENERGY_METRICS[0]], row[ENERGY_METRICS[1]],
                                        row['added_sound_area_mm2']], rtol=1e-10, atol=1e-10),
                        'independent finite-crack energies or areas differ')
        current.require(row['fracture_or_complete_joint_qualification'] is False
                        and [v['Gc_n_per_mm'] for v in row['common_energy_hypothesis_indices']] == base['Gc_all_modes_n_per_mm'],
                        'unchanged energy hypotheses and unqualified boundary required')
        for value in row['common_energy_hypothesis_indices']:
            current.require(np.allclose([value['signed_free_face_index'], value['signed_contact_upper_index']],
                                        [free/value['Gc_n_per_mm'], upper/value['Gc_n_per_mm']], rtol=1e-10, atol=1e-10),
                            'energy-reference scaling differs')
        current.require(np.isclose(row['intact_sampled_tension_reference_index'],
                                  result['configurations'][0]['sampled_transverse_tension_mpa'][col]/base['Ft90_reference_mpa'],
                                  rtol=1e-12, atol=1e-12), 'own intact tension-reference index differs')
    return audits


def audit(folder):
    input_ref = current.ref(refinement.INPUT)
    inputs = current.read(input_ref)
    refinement.validate(inputs)
    base = current.read(inputs['parent_inputs'])
    model.validate(base)
    runtime = checks.verify_runtime(base)
    parent = current.read(inputs['parent_saved_field_audit'])
    current.require(parent['inputs'] == inputs['parent_inputs'] and parent['all_sources_unchanged'] is True
                    and parent['status'] == 'COMPLETE_DECLARED_FIXED_ACTION_BORE_FLAW_FIELD_AND_TWO_MESH_AUDIT'
                    and parent['independently_checked_full_field_states'] == 2688,
                    'completed exact-parent saved-field audit required')
    refs = [input_ref, inputs['parent_inputs'], inputs['parent_saved_field_audit'], *inputs['seed_results'],
            *inputs['method_references'], inputs['history_review_source'], current.ref(OWN),
            current.ref(current.ROOT/'tests/test_eoere_cleat_field_refinement_audit.py')]
    pins = current.join(parent['source_sha256'], {r['path']: r['sha256'] for r in refs})
    kernel = model.component.load(base['kernel'], 'current_refined_field_audit_kernel')
    _, _, _, _, _, scenario, brick = kernel.libraries()
    constants = scenario()['calculix_engineering_constants']
    coarse, fine, jobs, field_audits = [], [], [], []
    for index, seed_ref in enumerate(inputs['seed_results']):
        seed = current.read(seed_ref)
        original_index = inputs['original_seed_job_indices'][index]
        refinement.check_seed(seed, inputs['parent_inputs'], original_index)
        current.require(parent['jobs'][original_index]['result'] == seed_ref, 'own seed must belong to the parent audit')
        reference = current.ref(folder/f'job{index:02d}/result.json')
        result = current.read(reference)
        check_job(result, input_ref, inputs, seed, index)
        current.require(result['runtime_versions'] == runtime and result['producer'] == current.ref(refinement.OWN),
                        'declared producer and runtime required')
        refs = [reference, *result['full_operator'].values(), *(c['field'] for c in result['configurations'])]
        pins = current.join(pins, result['source_sha256'], {r['path']: r['sha256'] for r in refs})
        current.verify(pins)
        axes = {'L': [1., 0., 0.], 'R': [0., 0., 1.] if result['job']['swap_RT'] else [0., 1., 0.],
                'T': [0., -1., 0.] if result['job']['swap_RT'] else [0., 0., 1.]}
        field_audits.extend({'job_index': index, **r} for r in audit_job(result, base, brick.engineering_stiffness(constants, axes)))
        coarse.append(seed)
        fine.append(result)
        jobs.append({'job_index': index, 'job': result['job'], 'coarse_result': seed_ref, 'fine_result': reference})
        print(json.dumps({'audited_refined_job': index, 'new_saved_field_states': len(field_audits)*48}), flush=True)
    energy_checks, stress_checks = pair_checks(coarse, fine, inputs['two_grid_relative_change_guard'])
    current.require(len(field_audits) == 28 and len(energy_checks) == 1536 and len(stress_checks) == 192,
                    'complete four-job finer-field and paired-comparison inventory required')
    model.verify_execution_sources(pins)
    current.require(current.sha(OWN) == LOADED_SHA, 'audit source changed after import')
    rows = [r for result in fine for r in result['comparisons']]
    metrics = (*ENERGY_METRICS, 'intact_sampled_tension_reference_index')
    return {'schema': 'eoere_current_finer_cleat_saved_field_audit/v1', 'inputs': input_ref, 'producer': current.ref(OWN),
            'source_sha256': pins, 'all_sources_unchanged': True, 'runtime_versions': runtime,
            'status': 'COMPLETE_DECLARED_FINER_FIXED_ACTION_FIELDS_AND_10_TO_7P5_MM_COMPARISONS',
            'jobs': jobs, 'field_audits': field_audits, 'independently_checked_new_full_field_states': 1344,
            'new_finite_crack_comparison_count': 768, 'reused_authenticated_coarse_comparison_count': 768,
            'energy_mesh_checks': energy_checks, 'unique_intact_stress_mesh_checks': stress_checks,
            'finer_reference_maxima': {metric: max(r[metric] for r in rows) for metric in metrics},
            'energy_reference_exceedance_counts': [{'Gc_n_per_mm': gc,
                'free_face': sum(r[ENERGY_METRICS[0]] > gc for r in rows),
                'contact_upper': sum(r[ENERGY_METRICS[1]] > gc for r in rows)} for gc in base['Gc_all_modes_n_per_mm']],
            'energy_mesh_guard_misses': {metric: sum(not c['within_declared_20_percent_guard'] for c in energy_checks
                                                    if c['metric'] == metric) for metric in ENERGY_METRICS},
            'intact_stress_mesh_guard_misses': sum(not c['within_declared_20_percent_guard'] for c in stress_checks),
            'external_native_frame_elastic_factorization_or_CAD_work': False,
            'complete_cleat_joint_or_member_resistance': None, 'physical_demand_bounds_established': False,
            'structural_acceptance': False, 'limits': [*base['assumptions'], *inputs['assumptions']]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(audit(args.jobs))
    print(json.dumps(current.ref(args.out)))


if __name__ == '__main__':
    main()
