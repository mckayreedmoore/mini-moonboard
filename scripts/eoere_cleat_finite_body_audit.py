"""Audit all saved current cleat fields and the declared two-grid comparisons.

No elastic factorization, frame solve, native executable or CAD work occurs.
Matrix entries are independently coalesced to each saved seam configuration.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
from scipy import sparse

from scripts import eoere_cleat_finite_body as model

current = model.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)


def verify_runtime(inputs):
    actual = {p: importlib.metadata.version(p) for p in ('numpy', 'scipy')}
    current.require(actual == inputs['runtime_versions'], 'declared auditor numerical runtime versions required')
    return actual


def coalesce_operator(full_k, full_nodes, full_elements, nodes, elements):
    """Independent direct matrix-entry assembly; no Boolean matrix product."""
    current.require(full_elements.shape == elements.shape
                    and np.array_equal(full_nodes[full_elements], nodes[elements]), 'physical elements changed')
    mapping = np.full(len(full_nodes), -1, dtype=int)
    for full_element, element in zip(full_elements, elements, strict=True):
        assigned = mapping[full_element]
        current.require(np.all((assigned == -1) | (assigned == element)), 'inconsistent full-to-current node identification')
        mapping[full_element] = element
    current.require((mapping >= 0).all(), 'unmapped full-seam node')
    indices = (mapping[:, None]*3+np.arange(3)).ravel()
    coo = full_k.tocoo()
    return sparse.coo_matrix((coo.data, (indices[coo.row], indices[coo.col])), shape=(3*len(nodes),)*2).tocsr()


def physical_fingerprint(nodes, force):
    values = force.reshape(len(nodes), 3, -1)
    active = np.flatnonzero(np.any(abs(values) > 1e-15, axis=(1, 2)))
    order = sorted(active.tolist(), key=lambda j: tuple(nodes[j]))
    payload = np.round(np.column_stack((nodes[order], force.reshape(len(nodes), -1)[order])), 11).tobytes()
    return hashlib.sha256(payload).hexdigest()


def verify_fixed_loads(nodes, force, load_maps, declared, intact=None):
    """Require the same physical force clouds throughout a crack family."""
    actual = [physical_fingerprint(nodes, force[:, i*12:(i+1)*12]) for i in range(4)]
    current.require(actual == [m['physical_nodal_load_sha256'] for m in load_maps]
                    and actual == declared and (intact is None or actual == intact),
                    'fixed prescribed physical loads differ between crack configurations')
    return actual


def verify_crack_topology(nodes, elements, axis, plane, interval, length):
    """Independently check the equivalence classes of every element node.

    Only upper-side nodes strictly inside the declared seam may be distinct
    from coincident lower-side nodes. Node numbering itself is immaterial.
    """
    points = nodes[elements]
    center = points[:, :8].mean(axis=1)
    inside = np.zeros(points.shape[:2], dtype=bool)
    if interval is not None:
        low, high = interval
        current.require(0. <= low < high <= length, 'crack interval outside the member')
        inside = (points[:, :, 0] > low+1e-7) & (points[:, :, 0] < high-1e-7)
        if low == 0.:
            inside |= points[:, :, 0] < high-1e-7
        if high == length:
            inside |= points[:, :, 0] > low+1e-7
    side = inside & (abs(points[:, :, axis]-plane) < 1e-7) & (center[:, None, axis] > plane)
    identifiers = np.column_stack((np.round(points.reshape(-1, 3), 8), side.ravel()))
    _, expected = np.unique(identifiers, axis=0, return_inverse=True)
    actual = elements.ravel()
    # Equality of both partitions proves no spurious split or closure, while
    # allowing an arbitrary bijection of saved node indices.
    for source, target, count in ((expected, actual, int(expected.max())+1),
                                  (actual, expected, len(nodes))):
        low = np.full(count, len(actual), dtype=int)
        high = np.full(count, -1, dtype=int)
        np.minimum.at(low, source, target)
        np.maximum.at(high, source, target)
        current.require(np.array_equal(low, high), 'saved seam topology differs from the declared crack interval')


def relative_change(coarse, fine):
    current.require(np.isfinite([coarse, fine]).all(), 'finite mesh values required')
    return abs(fine-coarse)/max(abs(coarse), abs(fine), 1e-8)


def trace_key(row, job):
    return (row['member'], row['case_id'], row['state_id'], row['field']['path'], row['field']['sha256'],
            row['bore_id'], row['tip'], row['radius_increment_mm'], row['coincident_point_side'],
            job['swap_RT'], job['plane_mm'])


def independent_energies(intact, initial, final, added_area):
    current.require(np.isfinite([intact, initial, final, added_area]).all() and added_area > 0.,
                    'finite energies and positive actual sound area required')
    current.require(0. <= intact <= initial+1e-7 and initial <= final+1e-7, 'non-nested fixed-load energies')
    return (final-initial)/added_area, (final-intact)/added_area


def witness_stress(nodes, displacement, constitutive, natural):
    """Recover a single C3D20 witness directly from its displacement gradient."""
    from fea.wood_joint_reduced_members import shape20_derivatives
    derivative = shape20_derivatives(np.asarray(natural))
    gradient = displacement.T @ (derivative @ np.linalg.inv(nodes.T@derivative))
    strain = np.array([gradient[0, 0], gradient[1, 1], gradient[2, 2],
                       gradient[0, 1]+gradient[1, 0], gradient[0, 2]+gradient[2, 0],
                       gradient[1, 2]+gradient[2, 1]])
    return constitutive@strain


def audit(folder):
    inputs_ref = current.ref(model.INPUT)
    inputs = current.read(inputs_ref)
    model.validate(inputs)
    runtime = verify_runtime(inputs)
    kernel = model.component.load(inputs['kernel'], 'eoere_saved_field_witness_kernel')
    _, _, _, _, _, scenario, brick = kernel.libraries()
    constants = scenario()['calculix_engineering_constants']
    pins = {inputs_ref['path']: inputs_ref['sha256'], **{r['path']: r['sha256'] for r in
            (current.ref(OWN), current.ref(current.ROOT/'tests/test_eoere_cleat_finite_body_audit.py'))}}
    jobs, by_grid, field_audits, references = [], {}, [], []
    for index, job in enumerate(inputs['jobs']):
        reference = current.ref(folder/f'job{index:02d}/result.json')
        result = current.read(reference)
        current.require(result['schema'] == 'eoere_current_fixed_action_finite_crack_comparisons/v1'
                        and result['status'] == 'CURRENT_DECLARED_BORE_FLAW_COMPARISONS_COMPLETE_LOCAL_MODEL_ONLY'
                        and result['inputs'] == inputs_ref and result['job_index'] == index and result['job'] == job
                        and len(result['configurations']) == 7 and len(result['comparisons']) == 192
                        and result['current_bolt_count'] == 100 and result['current_screw_count'] == 66
                        and result['whole_frame_or_native_executable_solve_performed'] is False
                        and result['physical_demand_bounds_established'] is False
                        and result['complete_cleat_joint_or_member_resistance'] is None
                        and result['structural_acceptance'] is False, 'complete own local job and unchanged claim boundary required')
        refs = [reference, *result['full_operator'].values(), *(c['field'] for c in result['configurations'])]
        pins = current.join(pins, result['source_sha256'], {r['path']: r['sha256'] for r in refs})
        current.verify(pins)
        k_full = model.read_array_file(result['full_operator']['stiffness'], sparse_matrix=True)
        with model.read_array_file(result['full_operator']['mesh']) as full:
            full_nodes, full_elements = full['nodes'], full['elements']
        labels = result['configurations'][0]['labels']
        current.require(len(labels) == 48 and len(result['records']) == 12, 'complete two-member/six-case/four-hypothesis fields required')
        expected = [{k: r[k] for k in ('case_id', 'state_id', 'field', 'member')} |
                    {'radius_increment_mm': radius, 'coincident_point_side': side}
                    for radius in inputs['radius_increments_mm'] for side in inputs['coincident_point_sides']
                    for r in result['records']]
        current.require(labels == expected and len({(r['member'], r['case_id']) for r in result['records']}) == 12,
                        'own labels must match the current complete record inventory')
        axes = {'L': [1., 0., 0.], 'R': [0., 0., 1.] if job['swap_RT'] else [0., 1., 0.],
                'T': [0., -1., 0.] if job['swap_RT'] else [0., 0., 1.]}
        constitutive = brick.engineering_stiffness(constants, axes)
        energies, intact_fingerprints = {}, None
        for config in result['configurations']:
            current.require(config['labels'] == labels and len(config['load_maps']) == 4, 'configuration labels or load maps changed')
            with model.read_array_file(config['field']) as field:
                nodes, elements, force, u = (field[k] for k in ('nodes', 'elements', 'F', 'U'))
            current.require(force.shape == u.shape == (3*len(nodes), 48) and np.isfinite(force).all()
                            and np.isfinite(u).all(), 'finite complete saved full fields required')
            verify_crack_topology(nodes, elements, 2, job['plane_mm'], config['interval'],
                                  result['geometry']['eoere_cleat_left']['length_mm'])
            k = coalesce_operator(k_full, full_nodes, full_elements, nodes, elements)
            residual = k@u-force
            maximum = float(np.max(abs(residual)))
            current.require(maximum < 1e-5, 'independent saved-field equilibrium gate failed')
            physical = force.reshape(len(nodes), 3, -1)
            force_error = float(np.max(abs(physical.sum(axis=0))))
            moment_error = float(np.max(abs(np.cross(nodes[:, :, None], physical, axisa=1, axisb=1, axisc=1).sum(axis=0))))
            current.require(force_error < 1e-7 and moment_error < 1e-5, 'independent complete physical load wrench failed')
            work = .5*np.sum(force*u, axis=0)
            strain = .5*np.sum(u*(k@u), axis=0)
            current.require(np.allclose(work, strain, rtol=1e-8, atol=1e-8)
                            and np.allclose(work, config['response']['strain_energy_nmm'], rtol=1e-12, atol=1e-10),
                            'independent strain/work or exported energy comparison failed')
            fingerprints = verify_fixed_loads(nodes, force, config['load_maps'],
                                              result['physical_load_fingerprints'], intact_fingerprints)
            if intact_fingerprints is None:
                intact_fingerprints = fingerprints
            if config['index'] == 0:
                current.require(len(config['sampled_transverse_tension_mpa']) == len(config['sampled_stress_witnesses']) == 48,
                                'all original sampled-peak witnesses required')
                for col, witness in enumerate(config['sampled_stress_witnesses']):
                    if witness is None:
                        current.require(config['sampled_transverse_tension_mpa'][col] == 0., 'positive sampled peak requires a witness')
                        continue
                    element = elements[witness['element']]
                    dofs = (3*element[:, None]+np.arange(3)).ravel()
                    stress = witness_stress(nodes[element], u[dofs, col].reshape(20, 3), constitutive, witness['gauss_natural'])
                    tension = max(0., np.linalg.eigvalsh([[stress[1], stress[5]], [stress[5], stress[2]]])[-1])
                    current.require(np.allclose(stress, witness['stress_g_u_v_gu_gv_uv_mpa'], rtol=1e-10, atol=1e-8)
                                    and np.isclose(tension, config['sampled_transverse_tension_mpa'][col], rtol=1e-10, atol=1e-8),
                                    'independent saved sampled-stress witness differs')
            interval = None if config['interval'] is None else tuple(config['interval'])
            area = model.exact_crack_area(result['geometry']['eoere_cleat_left'], job['plane_mm'], config['interval'])
            current.require(abs(area-config['census']['crack_area_mm2']) < 1e-6 and interval not in energies,
                            'actual sound area or unique configuration differs')
            energies[interval] = (work, area)
            field_audits.append({'job_index': index, 'configuration': config['index'], 'field': config['field'],
                                 'full_field_columns': 48, 'maximum_residual_n': maximum,
                                 'complete_force_residual_n': force_error, 'complete_moment_residual_nmm': moment_error,
                                 'maximum_strain_work_difference_nmm': float(np.max(abs(work-strain)))})
        seen = set()
        for row in result['comparisons']:
            label = {k: row[k] for k in labels[0]}
            col = labels.index(label)
            bore = next(b for b in result['geometry'][row['member']]['bores'] if b['id'] == row['bore_id'])
            s, r = bore['origin'][0], bore['radius_mm']
            initial = (s-r-5., s+r+5.)
            final = (s-r-10., initial[1]) if row['tip'] == 'low' else (initial[0], s+r+10.)
            current.require(row['tip'] in ('low', 'high') and abs(bore['origin'][2]-job['plane_mm']) < 1e-7,
                            'own bore and selected grain-tip identity required')
            e0, e1, e2 = (energies[key][0][col] for key in (None, initial, final))
            area = energies[final][1]-energies[initial][1]
            free, upper = independent_energies(e0, e1, e2, area)
            current.require(np.allclose([free, upper, area], [row['signed_free_face_energy_release_n_per_mm'],
                            row['signed_contact_upper_reference_n_per_mm'], row['added_sound_area_mm2']], rtol=1e-10, atol=1e-10)
                            and np.allclose([e0, e1, e2], row['energies_nmm'], rtol=1e-12, atol=1e-10),
                            'independent finite-crack energy arithmetic differs')
            current.require(row['fracture_or_complete_joint_qualification'] is False
                            and [v['Gc_n_per_mm'] for v in row['common_energy_hypothesis_indices']] == inputs['Gc_all_modes_n_per_mm'],
                            'energy hypotheses or null qualification changed')
            current.require(np.isclose(row['intact_sampled_tension_reference_index'],
                            result['configurations'][0]['sampled_transverse_tension_mpa'][col]/inputs['Ft90_reference_mpa'],
                            rtol=1e-12, atol=1e-12), 'sampled-stress reference index differs from the own intact field')
            for value in row['common_energy_hypothesis_indices']:
                current.require(np.allclose([value['signed_free_face_index'], value['signed_contact_upper_index']],
                                            [free/value['Gc_n_per_mm'], upper/value['Gc_n_per_mm']], rtol=1e-10, atol=1e-10),
                                'energy reference scaling differs')
            key = trace_key(row, job)
            current.require(key not in seen, 'duplicate current fracture comparison')
            seen.add(key)
            grids = by_grid.setdefault(key, {})
            current.require(job['mesh_size_mm'] not in grids, 'duplicate grid for one physical comparison')
            grids[job['mesh_size_mm']] = {**row, 'source_result': reference}
        jobs.append({'job_index': index, 'job': job, 'result': reference, 'comparison_count': len(seen)})
        references.append(reference)
        print(json.dumps({'audited_job': index, 'saved_field_states': len(field_audits)*48}), flush=True)
    current.require(len(by_grid) == 768 and len(field_audits) == 56, 'all declared jobs and paired field inventory required')
    mesh_checks, stress_checks, all_rows = [], {}, []
    for key, grids in by_grid.items():
        current.require(set(grids) == {15., 10.}, 'both declared meshes required')
        coarse, fine = grids[15.], grids[10.]
        all_rows.extend((coarse, fine))
        for metric in ('signed_free_face_energy_release_n_per_mm', 'signed_contact_upper_reference_n_per_mm'):
            change = relative_change(coarse[metric], fine[metric])
            mesh_checks.append({'identity': list(key), 'metric': metric, 'coarse': coarse[metric], 'fine': fine[metric],
                                'relative_change': change, 'within_declared_20_percent_guard': change <= .2})
        stress_key = key[:5]+key[7:]
        change = relative_change(coarse['intact_sampled_tension_reference_index'], fine['intact_sampled_tension_reference_index'])
        stress_checks.setdefault(stress_key, {'identity': list(stress_key), 'coarse_index': coarse['intact_sampled_tension_reference_index'],
                                            'fine_index': fine['intact_sampled_tension_reference_index'], 'relative_change': change,
                                            'within_declared_20_percent_guard': change <= .2})
    current.require(len(stress_checks) == 192 and len(all_rows) == 1536, 'complete unique stress and finite-crack comparison scope required')
    model.verify_execution_sources(pins)
    current.require(current.sha(OWN) == LOADED_SHA, 'audit source changed after import')
    return {'schema': 'eoere_current_finite_body_saved_field_audit/v1', 'source_sha256': pins,
            'all_sources_unchanged': True, 'inputs': inputs_ref, 'producer': current.ref(OWN),
            'runtime_versions': runtime,
            'status': 'COMPLETE_DECLARED_FIXED_ACTION_BORE_FLAW_FIELD_AND_TWO_MESH_AUDIT',
            'jobs': jobs, 'field_audits': field_audits, 'finite_comparison_count': 1536,
            'independently_checked_full_field_states': 2688,
            'energy_mesh_checks': mesh_checks, 'unique_intact_stress_mesh_checks': list(stress_checks.values()),
            'reference_maxima': {k: max(r[k] for r in all_rows) for k in
                ('signed_free_face_energy_release_n_per_mm', 'signed_contact_upper_reference_n_per_mm', 'intact_sampled_tension_reference_index')},
            'energy_reference_exceedance_counts': [{
                'Gc_n_per_mm': gc, 'free_face': sum(r['signed_free_face_energy_release_n_per_mm'] > gc for r in all_rows),
                'contact_upper': sum(r['signed_contact_upper_reference_n_per_mm'] > gc for r in all_rows)} for gc in inputs['Gc_all_modes_n_per_mm']],
            'external_native_frame_elastic_factorization_or_CAD_work': False,
            'complete_cleat_joint_or_member_resistance': None, 'physical_demand_bounds_established': False,
            'structural_acceptance': False, 'limits': inputs['assumptions']}


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
