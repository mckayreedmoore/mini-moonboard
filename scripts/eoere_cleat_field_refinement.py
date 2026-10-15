"""Refine current cleat fields while retaining every non-grid hypothesis.

Only local Python C3D20 calculations occur. Frozen parent producer, fields and
auditor remain unchanged; their pure geometry/load/energy helpers are reused.
"""
from __future__ import annotations

import argparse
import fcntl
import json
from pathlib import Path

import numpy as np
from scipy import sparse

from scripts import eoere_cleat_finite_body as model
from scripts import eoere_cleat_finite_body_audit as checks

current = model.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/cleat-field-grid-refinement-inputs-v1.json'
MEMBERS = ('eoere_cleat_left', 'eoere_cleat_right')


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_current_cleat_field_grid_refinement_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
                    and inputs['extra_grid'] is False and inputs['actual_observations'] is None
                    and inputs['structural_acceptance'] is False, 'unchanged unobserved current scope required')
    current.require(inputs['new_mesh_size_mm'] == 7.5 and inputs['two_grid_relative_change_guard'] == .2
                    and inputs['original_seed_job_indices'] == [4, 5, 6, 7] and len(inputs['seed_results']) == 4,
                    'complete finer-grid scope and unchanged comparison guard required')


def check_seed(seed, parent, index):
    current.require(seed['schema'] == 'eoere_current_fixed_action_finite_crack_comparisons/v1'
                    and seed['status'] == 'CURRENT_DECLARED_BORE_FLAW_COMPARISONS_COMPLETE_LOCAL_MODEL_ONLY'
                    and seed['inputs'] == parent and seed['job_index'] == index
                    and seed['job']['mesh_size_mm'] == 10. and len(seed['configurations']) == 7
                    and len(seed['comparisons']) == 192 and seed['current_bolt_count'] == 100
                    and seed['current_screw_count'] == 66 and seed['structural_acceptance'] is False
                    and seed['complete_cleat_joint_or_member_resistance'] is None
                    and seed['physical_demand_bounds_established'] is False
                    and seed['whole_frame_or_native_executable_solve_performed'] is False,
                    'complete own10-mm seed with unchanged qualification boundary required')
    expected = {'mesh_size_mm': 10., 'plane_mm': -25.4 if index % 2 == 0 else 25.4, 'swap_RT': index >= 6}
    current.require(seed['job'] == expected and set(seed['geometry']) == set(MEMBERS)
                    and len(seed['records']) == 12
                    and len({(r['member'], r['case_id']) for r in seed['records']}) == 12,
                    'own seed material/plane and complete two-member/six-case records required')


def comparisons(seed, configurations, base):
    """Rebuild energies/indices from new fields, retaining every own identity."""
    intact = configurations[0]
    current.require(intact['interval'] is None, 'first configuration must be intact')
    by_interval = {None if c['interval'] is None else tuple(c['interval']): c for c in configurations}
    current.require(len(by_interval) == len(configurations), 'duplicate crack configuration')
    labels = intact['labels']
    current.require(all(c['labels'] == labels for c in configurations), 'configuration column labels changed')
    output, seen = [], set()
    for row in seed['comparisons']:
        label = {key: row[key] for key in labels[0]}
        current.require(labels.count(label) == 1, 'exactly one own field column required')
        col = labels.index(label)
        bore = next(b for b in seed['geometry'][row['member']]['bores'] if b['id'] == row['bore_id'])
        s, r = bore['origin'][0], bore['radius_mm']
        initial_interval = (s-r-5., s+r+5.)
        current.require(row['tip'] in ('low', 'high'), 'own grain-tip identity required')
        final_interval = (s-r-10., initial_interval[1]) if row['tip'] == 'low' else (initial_interval[0], s+r+10.)
        initial, final = (by_interval[v] for v in (initial_interval, final_interval))
        energies = [c['response']['strain_energy_nmm'][col] for c in (intact, initial, final)]
        areas = [c['census']['crack_area_mm2'] for c in (initial, final)]
        energy = model.energy_comparison(energies, areas)
        key = checks.trace_key(row, seed['job'])
        current.require(key not in seen, 'duplicate physical bore-flaw comparison')
        seen.add(key)
        output.append({**label, 'bore_id': row['bore_id'], 'tip': row['tip'], 'energies_nmm': energies,
                       'initial_final_area_mm2': areas, **energy,
                       'common_energy_hypothesis_indices': [
                           {'Gc_n_per_mm': gc, 'signed_free_face_index': energy['signed_free_face_energy_release_n_per_mm']/gc,
                            'signed_contact_upper_index': energy['signed_contact_upper_reference_n_per_mm']/gc}
                           for gc in base['Gc_all_modes_n_per_mm']],
                       'intact_sampled_tension_reference_index': intact['sampled_transverse_tension_mpa'][col]/base['Ft90_reference_mpa'],
                       'fracture_or_complete_joint_qualification': False})
    return output


def prepare(kernel, seed, base, size):
    geometries, records = seed['geometry'], seed['records']
    canonical = geometries[MEMBERS[0]]
    plane = seed['job']['plane_mm']
    full_nodes, full_elements, full_census = kernel.mesh(canonical, size, 2, plane,
                                                       crack_interval=[0., canonical['length_mm']])
    current.require(3*len(full_nodes) <= base['maximum_dofs']
                    and len(full_elements)*3600*24 < base['maximum_raw_COO_bytes'], 'unchanged bounded resource preflight exceeded')
    for own in geometries.values():
        own_nodes, own_elements, _ = kernel.mesh(own, size, 2, plane, crack_interval=[0., own['length_mm']])
        current.require(np.array_equal(full_nodes, own_nodes) and np.array_equal(full_elements, own_elements),
                        'operator sharing requires bit-identical independently generated own meshes')
    configurations, fingerprints = [], None
    for old in seed['configurations']:
        nodes, elements, census = kernel.mesh(canonical, size, 2, plane, crack_interval=old['interval'])
        checks.verify_crack_topology(nodes, elements, 2, plane, old['interval'], canonical['length_mm'])
        area = model.exact_crack_area(canonical, plane, old['interval'])
        current.require(abs(census['crack_area_mm2']-area) < 1e-6
                        and abs(area-old['census']['crack_area_mm2']) < 1e-6, 'current true sound area must be grid invariant')
        loads, labels, maps = [], [], []
        for radius in base['radius_increments_mm']:
            for side in base['coincident_point_sides']:
                own_records = [{**record, 'actions': [{**a, 'point_mm': (np.asarray(a['point_mm'])-
                               np.asarray(geometries[record['member']]['start'])+np.asarray(canonical['start'])).tolist()}
                               for a in record['actions']]} for record in records]
                f, info = model.nodal_loads(kernel, nodes, canonical, own_records, plane, radius, side)
                loads.append(f)
                maps.append(info)
                labels.extend([{key: record[key] for key in ('case_id', 'state_id', 'field', 'member')} |
                               {'radius_increment_mm': radius, 'coincident_point_side': side} for record in records])
        force = np.column_stack(loads)
        current.require(labels == old['labels'] and len(labels) == 48, 'all own physical field identities must remain unchanged')
        declared = [m['physical_nodal_load_sha256'] for m in maps]
        own_fingerprints = checks.verify_fixed_loads(nodes, force, maps, declared, fingerprints)
        if fingerprints is None:
            fingerprints = own_fingerprints
        configurations.append({'index': old['index'], 'interval': old['interval'], 'nodes': nodes, 'elements': elements,
                               'mapping': model.assembly_map(full_nodes, full_elements, nodes, elements), 'F': force,
                               'labels': labels, 'load_maps': maps, 'census': census})
    return full_nodes, full_elements, full_census, configurations, fingerprints


def run(output, index, prepare_only=False):
    input_ref = current.ref(INPUT)
    inputs = current.read(input_ref)
    validate(inputs)
    current.require(isinstance(index, int) and 0 <= index < 4, 'one of four declared jobs required')
    base = current.read(inputs['parent_inputs'])
    model.validate(base)
    runtime = checks.verify_runtime(base)
    parent_audit = current.read(inputs['parent_saved_field_audit'])
    current.require(parent_audit['inputs'] == inputs['parent_inputs'] and parent_audit['all_sources_unchanged'] is True
                    and parent_audit['status'] == 'COMPLETE_DECLARED_FIXED_ACTION_BORE_FLAW_FIELD_AND_TWO_MESH_AUDIT'
                    and parent_audit['independently_checked_full_field_states'] == 2688,
                    'completed exact-parent saved-field audit required')
    seed_ref = inputs['seed_results'][index]
    original_index = inputs['original_seed_job_indices'][index]
    current.require(parent_audit['jobs'][original_index]['result'] == seed_ref, 'seed must be in authenticated parent inventory')
    seed = current.read(seed_ref)
    check_seed(seed, inputs['parent_inputs'], original_index)
    refs = [input_ref, inputs['parent_inputs'], inputs['parent_saved_field_audit'], inputs['history_review_source'],
            *inputs['seed_results'], *inputs['method_references'], current.ref(OWN),
            current.ref(current.ROOT/'tests/test_eoere_cleat_field_refinement.py')]
    pins = current.join(parent_audit['source_sha256'], {r['path']: r['sha256'] for r in refs})
    model.verify_execution_sources(pins)
    kernel = model.component.load(base['kernel'], 'current_cleat_finer_grid_kernel')
    _, _, _, _, _, scenario, _ = kernel.libraries()
    constants = scenario()['calculix_engineering_constants']
    nodes, elements, census, configurations, fingerprints = prepare(kernel, seed, base, inputs['new_mesh_size_mm'])
    model.verify_execution_sources(pins)
    plan = {'schema': 'eoere_current_cleat_finer_grid_plan/v1', 'inputs': input_ref,
            'parent_inputs': inputs['parent_inputs'], 'parent_saved_field_audit': inputs['parent_saved_field_audit'],
            'source_seed': seed_ref, 'producer': current.ref(OWN), 'source_sha256': pins, 'job_index': index,
            'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
            'extra_grid': False, 'actual_observations': None, 'physical_demand_bounds_established': False,
            'original_seed_job_index': original_index, 'job': {**seed['job'], 'mesh_size_mm': inputs['new_mesh_size_mm']},
            'runtime_versions': runtime, 'geometry': seed['geometry'], 'records': seed['records'],
            'full_seam_mesh': census, 'configuration_count': 7,
            'configuration_intervals': [c['interval'] for c in configurations],
            'physical_load_fingerprints': fingerprints, 'current_bolt_count': 100, 'current_screw_count': 66,
            'right_operator_reuse_requires_bit_identical_local_mesh': True,
            'whole_frame_or_native_executable_solve_performed': False, 'structural_acceptance': False}
    writer = lambda path, data: path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+'\n')
    writer(output/'plan.json', plan)
    if prepare_only:
        return {**plan, 'status': 'CURRENT_FINER_GRID_GEOMETRY_LOADS_AND_SOURCES_PREPARED_RESPONSE_PENDING',
                'local_python_elastic_comparison_performed': False, 'complete_cleat_joint_or_member_resistance': None}
    lock = current.ROOT/'fea/generated/selected-hardware-followup-v1/engineering-closure-v1/.cleat-local-elastic.lock'
    with lock.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        full_k = kernel.stiffness(nodes, elements, constants, seed['job']['swap_RT'])
        sparse.save_npz(output/'full-seam-stiffness.npz', full_k)
        np.savez_compressed(output/'full-seam-mesh.npz', nodes=nodes, elements=elements)
        operator = {'stiffness': current.ref(output/'full-seam-stiffness.npz'), 'mesh': current.ref(output/'full-seam-mesh.npz')}
        saved = []
        for config in configurations:
            own_nodes, own_elements, mapping, force = (config[k] for k in ('nodes', 'elements', 'mapping', 'F'))
            k = (mapping.T@full_k@mapping).tocsr()
            u, response = kernel.elastic_response(k, own_nodes, force)
            work, strain = .5*np.sum(force*u, axis=0), .5*np.sum(u*(k@u), axis=0)
            current.require(np.allclose(work, strain, rtol=1e-8, atol=1e-8), 'source work and strain energy disagree')
            peak, witness = kernel.transverse_stress(own_nodes, own_elements, u, constants, seed['job']['swap_RT']) \
                if config['index'] == 0 else (None, None)
            field = output/f"configuration-{config['index']:02d}.npz"
            np.savez_compressed(field, nodes=own_nodes, elements=own_elements, F=force, U=u)
            row = {key: config[key] for key in ('index', 'interval', 'census', 'labels', 'load_maps')}
            saved.append({**row, 'response': response, 'field': current.ref(field),
                          'sampled_transverse_tension_mpa': None if peak is None else peak.tolist(),
                          'sampled_stress_witnesses': witness,
                          'strain_work_maximum_difference_nmm': float(np.max(abs(work-strain)))})
            writer(output/f"configuration-{config['index']:02d}.json", saved[-1])
            print(json.dumps({'job': index, 'configuration': config['index'], 'configuration_count': 7,
                              'maximum_residual_n': response['maximum_equilibrium_residual_n']}), flush=True)
        fcntl.flock(handle, fcntl.LOCK_UN)
    rows = comparisons(seed, saved, base)
    model.verify_execution_sources(pins)
    current.require(len(rows) == 192 and current.sha(OWN) == LOADED_SHA, 'complete unchanged refined job required')
    return {**plan, 'schema': 'eoere_current_refined_fixed_action_finite_crack_comparisons/v1',
            'status': 'CURRENT_DECLARED_FINER_GRID_BORE_FLAW_COMPARISONS_COMPLETE_LOCAL_MODEL_ONLY',
            'configurations': saved, 'comparisons': rows, 'full_operator': operator,
            'local_python_elastic_comparison_performed': True, 'physical_demand_bounds_established': False,
            'complete_cleat_joint_or_member_resistance': None, 'limits': [*base['assumptions'], *inputs['assumptions']]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', type=int, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    current.require(not args.out.exists(), 'fresh owned output directory required')
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out/'producer.py.snapshot').write_bytes(OWN.read_bytes())
    test = current.ROOT/'tests/test_eoere_cleat_field_refinement.py'
    (args.out/'tests.py.snapshot').write_bytes(test.read_bytes())
    with current.load('bridge').reserve(args.out/'result.json') as output:
        output.write(run(args.out, args.job, args.prepare_only))
    print(json.dumps(current.ref(args.out/'result.json')))


if __name__ == '__main__':
    main()
