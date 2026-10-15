"""Current fixed-action finite-body crack comparisons with the existing kernel.

This is a local Python elastic calculation, not an external native executable
or a frame solve. It retains all signed actions, couples and three-dimensional
elastic modes. Its finite crack family and force clouds are explicit hypotheses.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib.metadata
import io
import json
import sys
import sysconfig
from itertools import pairwise
from pathlib import Path

import numpy as np
from scipy import sparse

from scripts import eoere_cleat_reference_audit as prior

current = prior.current
component = prior.intake_source.component
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC / 'selected-hardware-v1/current-response-v1/joint-closure-v1/cleat-finite-body-inputs-v4.json'


def geometry(profile, saved_geometry, bore_actions, shafts):
    """Bind the current trapezoid and four full-width bores, without a CAD rebuild."""
    source = profile['raw_profile_source']
    current.require(profile['axis'] == [0., 0., 1.] and source['basis_grain_u_v_xyz'] ==
                    [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]], 'current grain-Z geometry required')
    polygon = np.asarray(source['finished_YZ_polygon_mm'], dtype=float)
    current.require(polygon.shape == (4, 2) and np.isfinite(polygon).all(), 'finite current YZ polygon required')
    (yl, bottom), (yr, br), (yt, tr), (yb, tl) = polygon
    current.require(yl == yb and yr == yt and bottom == br and yl < yr and bottom < tl < tr,
                    'current flat-bottom sloped-top trapezoid required')
    width, depth, length = profile['width_mm'], yr-yl, tr-bottom
    current.require(width > 0. and abs(profile['depth_mm']-depth) < 1e-8,
                    'current positive width/depth required')
    cy = (yl+yr)/2
    start = [profile['start'][0], cy, bottom]
    frame = np.asarray(source['basis_grain_u_v_xyz'])
    slope, top_offset = (tr-tl)/(yr-yl), (tr+tl)/2-bottom
    bores = []
    for action in bore_actions:
        suffix = '/complete-wood-wrench'
        if not action['id'].endswith(suffix):
            continue
        axis_id = action['id'][:-len(suffix)]
        shaft = shafts[axis_id]
        current.require(abs(abs(shaft['basis'][0][0])-1) < 1e-10, 'X-directed current bore required')
        center = frame @ (np.asarray(action['point_xyz_mm'])-start)
        current.require(abs(center[1]) < 1e-7, 'current bore midpoint must equal the member mid-width')
        bores.append({'id': axis_id, 'origin': center.tolist(), 'axis': [0., 1., 0.],
                      'radius_mm': shaft['bore_diameter_mm']/2, 'interval_mm': [-width/2, width/2]})
    current.require(len(bores) == len({b['id'] for b in bores}) == 4, 'four distinct own bores required')
    raw_volume = width*depth*(tl+tr-2*bottom)/2
    exact_volume = raw_volume-sum(np.pi*b['radius_mm']**2*width for b in bores)
    current.require(abs(exact_volume-saved_geometry['whole_volume_mm3']) < 1e-4,
                    'profile/four-cylinder volume differs from the authenticated finished solid')
    for b in bores:
        z, _, y = b['origin']
        r = b['radius_mm']
        current.require(-depth/2 < y-r < y+r < depth/2 and z-r > 0.
                        and z+r < top_offset+slope*(y-r), 'full bore must lie within the finished profile')
    return {'body': profile['name'], 'frame': frame.tolist(), 'start': start,
            'length_mm': length, 'width_mm': width, 'depth_mm': depth,
            'actual_volume_mm3': saved_geometry['whole_volume_mm3'], 'recess_source': None,
            'bores': bores, 'planes': [
                {'normal': [-1., 0., 0.], 'offset': 0.},
                {'normal': [1., 0., -slope], 'offset': top_offset},
                *[{'normal': n, 'offset': off} for n, off in
                  (([0., 1., 0.], width/2), ([0., -1., 0.], width/2),
                   ([0., 0., 1.], depth/2), ([0., 0., -1.], depth/2))]],
            'analytic_finished_volume_mm3': exact_volume,
            'current_finished_solid': saved_geometry['observation']['source']}


def point_actions(field, components, member):
    """Copy individual current bearing/seat/contact/body actions; add no correction."""
    actions = []
    for row in components['findings']['timber']['wood_surfaces']:
        if row['receiver'] == member:
            for i, a in enumerate(row['own_point_actions']):
                actions.append({'id': f"{row['axis_id']}/point/{i}", 'point_mm': a['point_xyz_mm'],
                                'force_n': a['signed_components']['force_on_receiver_xyz_n'],
                                'free_moment_nmm': a['own_free_moment_nmm']})
    for a in field['contact_actions']:
        if member in (a['first'], a['second']):
            sign = 1. if a['first'] == member else -1.
            actions.append({'id': a['id'], 'point_mm': a['point_xyz_mm'],
                            'force_n': (sign*np.asarray(a['force_on_first_xyz_n'])).tolist(),
                            'free_moment_nmm': (sign*np.asarray(a['moment_at_point_model_xyz_nmm'])).tolist()})
    current.require(all(member not in (r['first'], r['second']) for r in field['panel_screw_actions']),
                    'additional cleat screw actions require a new adapter')
    gravity = [a for a in field['body_applied_loads'] if a['body'] == member]
    current.require(len(gravity) == 1 and gravity[0]['id'] == 'self-weight/'+member,
                    'exactly one original own self-weight load required')
    a = gravity[0]
    actions.append({'id': a['id'], 'point_mm': a['point_xyz_mm'], 'force_n': a['force_xyz_n'],
                    'free_moment_nmm': a.get('free_moment_xyz_nmm', [0., 0., 0.])})
    current.require(len(actions) == len({a['id'] for a in actions}), 'duplicate original point action')
    force = sum((np.asarray(a['force_n']) for a in actions), np.zeros(3))
    moment = sum((np.cross(a['point_mm'], a['force_n'])+a['free_moment_nmm'] for a in actions), np.zeros(3))
    current.require(np.max(abs(force)) < 1e-7 and np.max(abs(moment)) < 1e-5,
                    'original whole-body actions are not balanced; no artificial support or correction allowed')
    return actions


def nodal_loads(kernel, nodes, geom, records, plane, radius, boundary_side):
    """Reuse the existing mapper at an exactly scaled length, keeping the wrench.

    Scaling all coordinates and couples by 15/radius makes the unchanged
    15-mm kernel operate on the requested physical radius. For points on the
    plane, a 1e-6-mm selection offset and its exact counter-couple choose the
    declared side without changing the original force/moment about any origin.
    """
    current.require(radius in (15., 30.) and boundary_side in (-1, 1), 'declared footprint/side required')
    adjusted = copy.deepcopy(records)
    frame, start = np.asarray(geom['frame']), np.asarray(geom['start'])
    offset_count = 0
    for record in adjusted:
        for action in record['actions']:
            point = np.asarray(action['point_mm'])
            if abs((frame @ (point-start))[2]-plane) <= 1e-7:
                delta = frame[2]*boundary_side*1e-6
                action['point_mm'] = (point+delta).tolist()
                action['free_moment_nmm'] = (np.asarray(action['free_moment_nmm'])-np.cross(delta, action['force_n'])).tolist()
                offset_count += 1
    scale = 15./radius
    scaled_geom = {**geom, 'start': (start*scale).tolist()}
    for record in adjusted:
        for action in record['actions']:
            for key in ('point_mm', 'free_moment_nmm'):
                action[key] = (np.asarray(action[key])*scale).tolist()
    f, census = kernel.load_vector(nodes*scale, scaled_geom, adjusted, 2, plane*scale)
    physical = f.reshape(len(nodes), 3, len(records))
    force = physical.sum(axis=0)
    moment = np.cross(nodes[:, :, None], physical, axisa=1, axisb=1, axisc=1).sum(axis=0)
    current.require(np.max(abs(force)) < 1e-7 and np.max(abs(moment)) < 1e-5,
                    'physical nodal loads do not retain the original complete balanced wrench')
    active = np.flatnonzero(np.any(abs(physical) > 1e-15, axis=(1, 2)))
    order = sorted(active.tolist(), key=lambda j: tuple(nodes[j]))
    payload = np.round(np.column_stack((nodes[order], f.reshape(len(nodes), -1)[order])), 11).tobytes()
    return f, {**census, 'physical_nodal_load_sha256': hashlib.sha256(payload).hexdigest(),
               'radius_increment_mm': radius, 'coincident_point_side': boundary_side,
               'coincident_selection_offsets': offset_count,
               'maximum_physical_force_residual_n': float(np.max(abs(force))),
               'maximum_physical_moment_residual_nmm': float(np.max(abs(moment))),
               'maximum_patch_node_distance_from_source_mm': census['maximum_patch_node_distance_from_source_mm']/scale,
               'maximum_individual_wrench_residual_n_nmm': [
                   *census['maximum_individual_wrench_residual_n_nmm'][:3],
                   *(v/scale for v in census['maximum_individual_wrench_residual_n_nmm'][3:])]}


def assembly_map(full_nodes, full_elements, nodes, elements):
    """Boolean congruence: close the full seam outside the selected crack."""
    current.require(full_elements.shape == elements.shape
                    and np.array_equal(full_nodes[full_elements], nodes[elements]),
                    'the physical elements must be identical in every crack configuration')
    low = np.full(len(full_nodes), len(nodes), dtype=int)
    high = np.full(len(full_nodes), -1, dtype=int)
    np.minimum.at(low, full_elements.ravel(), elements.ravel())
    np.maximum.at(high, full_elements.ravel(), elements.ravel())
    current.require(np.array_equal(low, high) and (low >= 0).all() and (low < len(nodes)).all(),
                    'every fully split degree must map to exactly one current node')
    rows = np.arange(3*len(full_nodes))
    columns = (3*low[:, None]+np.arange(3)).ravel()
    return sparse.coo_matrix((np.ones(len(rows)), (rows, columns)), shape=(len(rows), 3*len(nodes))).tocsr()


def exact_crack_area(geom, plane, interval):
    """Independent actual full-width sound area in a grain/Y-plane interval."""
    if interval is None:
        return 0.
    top = next(p for p in geom['planes'] if p['normal'][0] == 1.)
    current.require(top['normal'][1] == 0. and top['normal'][2] < 0., 'current sloping top required')
    low, high = max(0., interval[0]), min(interval[1], top['offset']-top['normal'][2]*plane)
    current.require(low < high and -geom['depth_mm']/2 < plane < geom['depth_mm']/2,
                    'interior plane and positive finished grain interval required')
    intervals = []
    for b in geom['bores']:
        offset = plane-b['origin'][2]
        if abs(offset) < b['radius_mm']:
            half = np.sqrt(b['radius_mm']**2-offset**2)
            a, z = max(low, b['origin'][0]-half), min(high, b['origin'][0]+half)
            if a < z:
                intervals.append((a, z))
    intervals.sort()
    current.require(all(a[1] <= b[0] for a, b in pairwise(intervals)),
                    'overlapping bore sections require a separate union-area adapter')
    return geom['width_mm']*(high-low-sum(b-a for a, b in intervals))


def energy_comparison(energies, areas, tolerance=1e-7):
    e0, e1, e2 = np.asarray(energies, dtype=float)
    a1, a2 = areas
    current.require(np.isfinite([e0, e1, e2, a1, a2]).all() and 0. < a1 < a2,
                    'finite intact/initial/final energies and positive added sound area required')
    current.require(e0 >= 0. and e1 >= e0-tolerance and e2 >= e1-tolerance,
                    'fixed-load nested crack spaces must not lower strain energy')
    free, upper = (e2-e1)/(a2-a1), (e2-e0)/(a2-a1)
    return {'signed_free_face_energy_release_n_per_mm': float(free),
            'signed_contact_upper_reference_n_per_mm': float(upper),
            'added_sound_area_mm2': float(a2-a1)}


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_cleat_finite_body_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['extra_grid'] is False and inputs['actual_observations'] is None,
                    'current declared unobserved local-model scope required')
    current.require(inputs['mesh_sizes_mm'] == [15., 10.] and inputs['radius_increments_mm'] == [15., 30.]
                    and inputs['coincident_point_sides'] == [-1, 1]
                    and inputs['Gc_all_modes_n_per_mm'] == [.1, .05]
                    and inputs['Ft90_reference_mpa'] == .2,
                    'declared mesh, boundary and resistance hypotheses required')
    current.require(len(inputs['jobs']) == 8 and len({(j['mesh_size_mm'], j['swap_RT'], j['plane_mm']) for j in inputs['jobs']}) == 8
                    and all(j['mesh_size_mm'] in (15., 10.) and isinstance(j['swap_RT'], bool)
                            and j['plane_mm'] in (-25.4, 25.4) for j in inputs['jobs']),
                    'complete eight-job material/mesh/plane inventory required')


def repository_source(file):
    """Separate repository code from the interpreter's locked dependencies."""
    path = Path(file).resolve()
    dependency_roots = {Path(sysconfig.get_path(k)).resolve() for k in ('purelib', 'platlib')}
    if path.suffix != '.py' or not path.is_relative_to(current.ROOT) or any(path.is_relative_to(p) for p in dependency_roots):
        return None
    return str(path.relative_to(current.ROOT))


def verify_execution_sources(pins):
    for module in tuple(sys.modules.values()):
        file = getattr(module, '__file__', None)
        relative = repository_source(file) if file else None
        if relative is not None:
            current.require(relative in pins and current.sha(current.ROOT/relative) == pins[relative],
                            'unbound repository execution source: '+relative)
    current.require(current.sha(OWN) == LOADED_SHA, 'producer changed after import')
    current.verify(pins)


def read_array_file(reference, sparse_matrix=False):
    """Hash the exact bytes parsed, including adopted previously unsealed fields."""
    raw = (current.ROOT/reference['path']).read_bytes()
    current.require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'saved array source changed')
    return sparse.load_npz(io.BytesIO(raw)) if sparse_matrix else np.load(io.BytesIO(raw), allow_pickle=False)


def saved_response(kernel, k, nodes, f, u):
    """Validate a saved full field without another interior factorization."""
    from scipy.linalg import qr
    current.require(u.shape == f.shape and np.isfinite(u).all(), 'finite saved field of the original size required')
    q = kernel.rigid_columns(nodes)
    fixed = qr(q.T, mode='economic', pivoting=True)[2][:6]
    free = np.setdiff1d(np.arange(len(f)), fixed)
    condition = float(np.linalg.cond(q[fixed]))
    residual = k@u-f
    current.require(np.linalg.matrix_rank(q[fixed]) == 6 and condition < 1e6
                    and np.max(abs(k@q)) < 1e-5 and np.max(abs(q.T@f)) < 2e-5
                    and np.max(abs(u[fixed])) < 1e-12 and np.max(abs(residual[free])) < 1e-5
                    and np.max(abs(residual[fixed])) < 1e-5, 'saved gauge/rigid/equilibrium field gate fails')
    return {'maximum_equilibrium_residual_n': float(np.max(abs(residual))),
            'maximum_gauge_reaction_n': float(np.max(abs(residual[fixed]))),
            'strain_energy_nmm': (.5*np.sum(f*u, axis=0)).tolist(),
            'maximum_source_rigid_load_projection_n': float(np.max(abs(q.T@f))),
            'gauge': 'QR-selected six scalar nodal DOFs; no physical support stiffness',
            'fixed_scalar_dofs': fixed.tolist(), 'fixed_rigid_rank': 6, 'fixed_rigid_condition': condition,
            'original_K_nonzeros': int(k.nnz), 'stored_factor_nonzeros': None,
            'saved_field_recovered_without_interior_factorization': True}


def run(output, job_index, prepare_only=False, recover=None):
    raw = INPUT.read_bytes()
    input_ref = {'path': str(INPUT.relative_to(current.ROOT)), 'sha256': hashlib.sha256(raw).hexdigest()}
    inputs = json.loads(raw)
    validate(inputs)
    current.require(inputs['runtime_versions'] == {p: importlib.metadata.version(p) for p in ('numpy', 'scipy')},
                    'declared shared numerical tool versions required')
    current.require(inputs['kernel'] in inputs['references'], 'kernel must be an explicit frozen source')
    current.require(isinstance(job_index, int) and 0 <= job_index < 8 and not output.exists(),
                    'a declared job and fresh output directory required')
    cases, pins = prior.intake_source.intake()
    source = current.read(prior.DEMAND)
    current.require(current.sha(Path(prior.__file__)) == prior.LOADED_SHA, 'imported prior adapter changed after load')
    refs = [input_ref, prior.DEMAND, current.ref(OWN), current.ref(Path(prior.__file__)),
            current.ref(current.ROOT/'tests/test_eoere_cleat_finite_body.py'),
            *inputs['references']]
    pins = current.join(pins, source['source_sha256'], {r['path']: r['sha256'] for r in refs})
    current.require('uv.lock' in pins, 'runtime dependencies require the frozen shared lockfile')
    current.verify(pins)
    recovery = None
    if recover is not None:
        current.require(recover.resolve().is_relative_to(current.ROOT/'fea/generated'), 'owned saved-field directory required')
        stop_ref = current.ref(recover/'stop.json')
        recovery = current.read(stop_ref)
        old_plan = current.read(recovery['plan'])
        current.require(recovery['status'] == 'STOP_LATE_UNBOUND_REPOSITORY_STRESS_HELPER_WITH_SAVED_FIELDS'
                        and old_plan['job_index'] == job_index and old_plan['job'] == inputs['jobs'][job_index]
                        and len(recovery['saved_fields']) == old_plan['configuration_count'] == 7,
                        'exact previously stopped current job required')
        snapshots = {r['original_path']: r for r in recovery['source_snapshots']}
        rebound = {}
        for path, digest in old_plan['source_sha256'].items():
            if path in snapshots:
                current.require(snapshots[path]['sha256'] == digest, 'saved original source snapshot differs')
                path = snapshots[path]['snapshot_path']
            rebound[path] = digest
        adopted = [stop_ref, recovery['plan'], recovery['input'], *recovery['saved_fields'], *recovery['full_operator'].values()]
        pins = current.join(pins, rebound, {r['path']: r['sha256'] for r in adopted})
        current.verify(pins)
    kernel = component.load(inputs['kernel'], 'eoere_existing_finite_body_kernel')
    _, _, _, _, _, scenario, _ = kernel.libraries()
    constants = scenario()['calculix_engineering_constants']
    job = inputs['jobs'][job_index]
    plane, size, swap = (job[k] for k in ('plane_mm', 'mesh_size_mm', 'swap_RT'))
    geometries, records = {}, []
    demand = {(r['case_id'], r['member']): r for r in source['cases']}
    for binding, field, components in cases:
        shafts = {r['axis_id']: r for r in field['source_inputs']['shafts']}
        for member in ('eoere_cleat_left', 'eoere_cleat_right'):
            saved = demand[binding['case_id'], member]
            current.require(saved['state_id'] == binding['state_id'] and saved['field'] == binding['field'],
                            'own current authenticated state/field required')
            profile = next(r for r in field['source_inputs']['timber_rows'] if r['name'] == member)
            geom = geometry(profile, source['geometry'][member], saved['complete_saved_exterior_point_actions'], shafts)
            current.require(member not in geometries or geom == geometries[member], 'geometry differs between own cases')
            geometries[member] = geom
            records.append({'case_id': binding['case_id'], 'state_id': binding['state_id'], 'field': binding['field'],
                            'member': member, 'actions': point_actions(field, components, member)})
    canonical = geometries['eoere_cleat_left']
    full_nodes, full_elements, full_census = kernel.mesh(canonical, size, 2, plane, crack_interval=[0., canonical['length_mm']])
    current.require(3*len(full_nodes) <= inputs['maximum_dofs']
                    and len(full_elements)*3600*24 < inputs['maximum_raw_COO_bytes'], 'bounded local assembly preflight exceeded')
    for geom in geometries.values():
        own_nodes, own_elements, _ = kernel.mesh(geom, size, 2, plane, crack_interval=[0., geom['length_mm']])
        current.require(np.array_equal(full_nodes, own_nodes) and np.array_equal(full_elements, own_elements),
                        'operator reuse requires bit-identical own local nodes and physical elements')
    paths = [p for p in kernel.crack_paths(canonical, (2,)) if p['kind'] == 'cross_grain_bore_seeded_full_front'
             and abs(p['plane_mm']-plane) < 1e-7]
    current.require(len(paths) == 4, 'two bore seeds and both grain-tip extensions on this plane required')
    intervals = [None, *sorted({tuple(p[k]) for p in paths for k in ('initial_interval_mm', 'final_interval_mm')})]
    configurations, fingerprints = [], None
    for interval in intervals:
        nodes, elements, census = kernel.mesh(canonical, size, 2, plane, crack_interval=interval)
        actual_area = exact_crack_area(canonical, plane, interval)
        current.require(abs(census['crack_area_mm2']-actual_area) < 1e-6,
                        'staircase crack area differs from independent current sound-area integration')
        census['independent_actual_sound_crack_area_mm2'] = actual_area
        mapping = assembly_map(full_nodes, full_elements, nodes, elements)
        loads, labels, maps = [], [], []
        for radius in inputs['radius_increments_mm']:
            for side in inputs['coincident_point_sides']:
                f, info = nodal_loads(kernel, nodes, canonical, [
                    {**r, 'actions': [{**a, 'point_mm': (np.asarray(a['point_mm'])-
                     np.asarray(geometries[r['member']]['start'])+np.asarray(canonical['start'])).tolist()}
                     for a in r['actions']]} for r in records], plane, radius, side)
                loads.append(f)
                labels.extend([{k: r[k] for k in ('case_id', 'state_id', 'field', 'member')} |
                              {'radius_increment_mm': radius, 'coincident_point_side': side} for r in records])
                maps.append(info)
        digests = [m['physical_nodal_load_sha256'] for m in maps]
        current.require(fingerprints is None or digests == fingerprints,
                        'physical prescribed loads changed between intact and crack configurations')
        fingerprints = digests
        configurations.append({'interval': interval, 'nodes': nodes, 'elements': elements, 'census': census,
                               'mapping': mapping, 'F': np.column_stack(loads), 'labels': labels, 'load_maps': maps})
    verify_execution_sources(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output/'producer.py.snapshot').write_bytes(OWN.read_bytes())
    writer = lambda path, data: path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False)+'\n')
    plan = {'schema': 'eoere_cleat_fixed_action_local_plan/v1', 'inputs': input_ref, 'producer': current.ref(OWN),
            'source_sha256': pins, 'job_index': job_index, 'job': job, 'geometry': geometries,
            'records': records, 'full_seam_mesh': full_census, 'configuration_count': len(configurations),
            'configuration_intervals': intervals, 'physical_load_fingerprints': fingerprints,
            'right_operator_reuse_requires_bit_identical_local_mesh': True,
            'saved_field_recovery': None if recovery is None else current.ref(recover/'stop.json'),
            'runtime_dependency_binding': 'Recorded numpy/scipy versions and source-pinned uv.lock; interpreter purelib/platlib are third-party dependencies, not repository execution sources.',
            'external_native_executable_or_frame_solve': False, 'physical_release': False}
    writer(output/'plan.json', plan)
    if prepare_only:
        return {'status': 'CURRENT_LOCAL_GEOMETRY_AND_ALL_FIXED_LOADS_PREPARED_RESPONSE_PENDING',
                'plan': current.ref(output/'plan.json')}
    lock = current.ROOT/'fea/generated/selected-hardware-followup-v1/engineering-closure-v1/.cleat-local-elastic.lock'
    with lock.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        full_k = kernel.stiffness(full_nodes, full_elements, constants, swap)
        if recovery is None:
            sparse.save_npz(output/'full-seam-stiffness.npz', full_k)
            np.savez_compressed(output/'full-seam-mesh.npz', nodes=full_nodes, elements=full_elements)
            operator_refs = {'stiffness': current.ref(output/'full-seam-stiffness.npz'),
                             'mesh': current.ref(output/'full-seam-mesh.npz')}
        else:
            operator_refs = recovery['full_operator']
            saved_k = read_array_file(operator_refs['stiffness'], sparse_matrix=True)
            saved_mesh = read_array_file(operator_refs['mesh'])
            current.require(np.array_equal(saved_mesh['nodes'], full_nodes)
                            and np.array_equal(saved_mesh['elements'], full_elements)
                            and saved_k.shape == full_k.shape
                            and np.max(abs((saved_k-full_k).data), initial=0.) < 1e-8,
                            'saved full operator differs from independent current element reassembly')
        saved_configs = []
        for index, configuration in enumerate(configurations):
            nodes, elements, mapping, f = (configuration[k] for k in ('nodes', 'elements', 'mapping', 'F'))
            k = (mapping.T @ full_k @ mapping).tocsr()
            if recovery is None:
                u, response = kernel.elastic_response(k, nodes, f)
            else:
                field_ref = recovery['saved_fields'][index]
                old = read_array_file(field_ref)
                current.require(np.array_equal(old['nodes'], nodes) and np.array_equal(old['elements'], elements)
                                and np.array_equal(old['F'], f), 'saved current mesh or prescribed loads differ')
                u = old['U']
                response = saved_response(kernel, k, nodes, f, u)
            work = .5*np.sum(f*u, axis=0)
            strain = .5*np.sum(u*(k@u), axis=0)
            current.require(np.allclose(work, strain, rtol=1e-8, atol=1e-8), 'strain energy and source work disagree')
            peak, witness = kernel.transverse_stress(nodes, elements, u, constants, swap) if index == 0 else (None, None)
            if recovery is None:
                file = output/f'configuration-{index:02d}.npz'
                np.savez_compressed(file, nodes=nodes, elements=elements, F=f, U=u)
                field_ref = current.ref(file)
            saved_configs.append({'index': index, 'interval': configuration['interval'], 'census': configuration['census'],
                                  'response': response, 'labels': configuration['labels'], 'load_maps': configuration['load_maps'],
                                  'sampled_transverse_tension_mpa': None if peak is None else peak.tolist(), 'sampled_stress_witnesses': witness,
                                  'field': field_ref, 'strain_work_maximum_difference_nmm': float(np.max(abs(work-strain)))})
            writer(output/f'configuration-{index:02d}.json', saved_configs[-1])
            print(json.dumps({'job': job_index, 'configuration': index, 'count': len(configurations),
                              'maximum_residual_n': response['maximum_equilibrium_residual_n']}), flush=True)
        fcntl.flock(handle, fcntl.LOCK_UN)
    verify_execution_sources(pins)
    comparisons = []
    intact = saved_configs[0]
    for path in paths:
        initial, final = [next(c for c in saved_configs if c['interval'] is not None and
                              list(c['interval']) == path[key]) for key in ('initial_interval_mm', 'final_interval_mm')]
        for col, label in enumerate(intact['labels']):
            energy = [c['response']['strain_energy_nmm'][col] for c in (intact, initial, final)]
            areas = [c['census']['crack_area_mm2'] for c in (initial, final)]
            comparison = energy_comparison(energy, areas)
            own_bores = geometries[label['member']]['bores']
            original_bore = next(b for b in canonical['bores'] if b['id'] == path['bore_id'])
            own_bore = next(b for b in own_bores if b['origin'] == original_bore['origin'])
            comparisons.append({**label, 'bore_id': own_bore['id'], 'tip': path['tip'], 'energies_nmm': energy,
                                'initial_final_area_mm2': areas, **comparison,
                                'common_energy_hypothesis_indices': [{
                                    'Gc_n_per_mm': gc,
                                    'signed_free_face_index': comparison['signed_free_face_energy_release_n_per_mm']/gc,
                                    'signed_contact_upper_index': comparison['signed_contact_upper_reference_n_per_mm']/gc}
                                    for gc in inputs['Gc_all_modes_n_per_mm']],
                                'intact_sampled_tension_reference_index': intact['sampled_transverse_tension_mpa'][col]/inputs['Ft90_reference_mpa'],
                                'fracture_or_complete_joint_qualification': False})
    result = {**plan, 'schema': 'eoere_current_fixed_action_finite_crack_comparisons/v1',
              'status': 'CURRENT_DECLARED_BORE_FLAW_COMPARISONS_COMPLETE_LOCAL_MODEL_ONLY',
              'runtime': {p: importlib.metadata.version(p) for p in ('numpy', 'scipy')},
              'configurations': saved_configs, 'comparisons': comparisons,
              'full_operator': operator_refs,
              'local_python_elastic_comparison_performed': True, 'current_bolt_count': 100, 'current_screw_count': 66,
              'whole_frame_or_native_executable_solve_performed': False, 'physical_demand_bounds_established': False,
              'complete_cleat_joint_or_member_resistance': None, 'structural_acceptance': False,
              'limits': inputs['assumptions']}
    current.require(len(comparisons) == 192 and current.sha(OWN) == LOADED_SHA, 'complete unchanged current job required')
    writer(output/'result.json', result)
    return {'status': result['status'], 'result': current.ref(output/'result.json')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--job', type=int, required=True)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--recover', type=Path)
    args = parser.parse_args()
    current.require(args.out.resolve().is_relative_to(current.ROOT/'fea/generated'), 'ignored generated output required')
    print(json.dumps(run(args.out.resolve(), args.job, args.prepare_only, args.recover)))


if __name__ == '__main__':
    main()
