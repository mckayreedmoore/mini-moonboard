"""Define the remaining timber gravity work and retain saved panel load rows.

Cached-solid queries and exact saved-array arithmetic only. The panel rows
are linear numerical work, not an objective finite panel/bulk coupling.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BOOT = {'path': 'scripts/eoere_distributed_gravity.py',
        'sha256': '137fa551309d833a285b0242bc4482c411c5481e831beab03f371dba8ec1b988'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bootstrap(pins):
    data = (ROOT/BOOT['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == BOOT['sha256']
            and pins.get(BOOT['path'], BOOT['sha256']) == BOOT['sha256'], 'frozen gravity-work bootstrap changed')
    pins[BOOT['path']] = BOOT['sha256']
    module = ModuleType('_eoere_verified_remaining_load_bootstrap'); module.__file__ = str(ROOT/BOOT['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - authenticated source buffer
    return module


def cube_law(row, half_width, boundary_distance, geometry_tolerance, inside, contact):
    """A uniform world-axis cube: exact force and all 12 affine coefficients.

    The finite spread is an explicit numerical load hypothesis. It is not a
    screw, a drilled void, a physical metal density or an attachment stiffness.
    """
    require(type(inside) is bool and inside, 'source centroid must be strictly inside its own finished timber')
    require(all(type(value) is not bool for value in (half_width, boundary_distance, geometry_tolerance)),
            'nonboolean cube and distance inputs required')
    radius, distance, tolerance = map(F, (half_width, boundary_distance, geometry_tolerance))
    require(radius > 0 and tolerance > 0 and distance > tolerance
            and 3*radius**2 < (distance-tolerance)**2, 'whole cube must fit strictly inside the own numerical boundary margin')
    force, point = contact.vector(row['force_xyz_n']), contact.vector(row['point_xyz_mm'])
    require(force[:2] == [0, 0] and force[2] < 0 and not any(contact.vector(row.get('moment_xyz_nmm', [0, 0, 0]))),
            'retained downward metal-share gravity without a free couple required')
    volume = 8*radius**3
    coefficients = contact.affine_load_coefficients([row])
    return {'half_width_mm': str(radius), 'volume_mm3': str(volume),
        'cube_center_xyz_mm': row['point_xyz_mm'], 'uniform_force_density_n_per_mm3': [str(value/volume) for value in force],
        'cube_bounds_xyz_mm': [[str(value-radius), str(value+radius)] for value in point],
        'exact_affine_work_coefficients': list(map(str, coefficients)),
        'L2_load_functional_norm_square_n2_per_mm3': str(sum(value**2 for value in force)/volume),
        'numerical_inscribed_ball_margin_square_mm2': str((distance-tolerance)**2-3*radius**2),
        'exact_resultant_and_affine_first_moments_preserved': True,
        'arbitrary_old_beam_work_or_comparator_bounds_transferred': False}


def linear_panel_work(force, coefficients):
    require(len(force) == len(coefficients) > 0 and all(type(value) is not bool for value in (*force, *coefficients)),
            'complete nonboolean panel force and coefficient rows required')
    return sum((F(a)*F(b) for a, b in zip(force, coefficients, strict=True)), F(0))


def attachment_axes(loads, hillman):
    axes = {row['id']: row['second'] for row in hillman}
    require(len(axes) == len(hillman) == len(loads), 'one timber metal share per retained Hillman axis required')
    used = {}
    for row in loads:
        prefix = 'bolt-weight/fastener_'
        require(row['id'].startswith(prefix) and '/source-metal-share-' in row['id'], 'bound source metal-share identity required')
        axis = row['id'].removeprefix(prefix).split('/source-metal-share-', 1)[0]
        require(axis in axes and row['body'] == axes[axis] and axis not in used, 'unique own receiver and Hillman axis required')
        used[axis] = row['id']
    require(set(used) == set(axes), 'all retained Hillman axes must retain their own metal share')
    return {identity: axis for axis, identity in used.items()}


def complete_partition(mapped, gravity_ids, attachment_ids, panel_ids):
    originals = [list(ids) for ids in (gravity_ids, attachment_ids, panel_ids)]
    groups = [set(ids) for ids in originals]
    require(len({row['id'] for row in mapped}) == len(mapped)
            and all(len(old) == len(group) for old, group in zip(originals, groups, strict=True))
            and sum(map(len, groups)) == len(set.union(*groups)) == len(mapped)
            and set.union(*groups) == {row['id'] for row in mapped}, 'each original source load must occur in exactly one work space')


def panel_work_record(name, descriptor, loads, applied, rigid, reference, contact, force_tolerance, moment_tolerance):
    require(isinstance(applied, np.ndarray) and isinstance(rigid, np.ndarray)
            and applied.dtype.str == rigid.dtype.str == '<f8' and np.isfinite(applied).all() and np.isfinite(rigid).all(),
            'saved finite float64 panel force and generator arrays required')
    indices = descriptor['indices']
    require(indices and all(type(i) is int and 0 <= i < len(applied) for i in indices)
            and len(indices) == len(set(indices)), 'distinct in-range own panel coefficient indices required')
    require(len(rigid) == len(applied) and all(len(row) == 6 for row in rigid), 'six saved rigid-work columns required')
    require(loads and all(row['body'] == name for row in loads) and len({row['id'] for row in loads}) == len(loads),
            'unique own source panel loads required')
    local = [F(float(applied[i])) for i in indices]
    generators = [[F(float(rigid[i][j])) for i in indices] for j in range(6)]
    actual = [linear_panel_work(local, generator) for generator in generators]
    forces = [contact.vector(row['force_xyz_n']) for row in loads]
    moments = [contact.cross(contact.sub(row['point_xyz_mm'], reference), force)
               for row, force in zip(loads, forces, strict=True)]
    require(not any(any(contact.vector(row.get('moment_xyz_nmm', [0, 0, 0]))) for row in loads),
            'current source panel loads have no external point couples')
    expected = [sum(row[j] for row in forces) for j in range(3)]+[sum(row[j] for row in moments) for j in range(3)]
    error = [a-b for a, b in zip(actual, expected, strict=True)]
    require(max(map(abs, error[:3])) <= force_tolerance and max(map(abs, error[3:])) <= moment_tolerance,
            'saved panel generator work and exact source wrench disagree')
    values = list(map(str, local)); digest = hashlib.sha256(json.dumps(values, separators=(',', ':')).encode()).hexdigest()
    return {'panel': name, 'coefficient_indices': indices, 'source_load_ids': [row['id'] for row in loads],
        'exact_linear_generalized_force_n': values, 'force_vector_sha256': digest,
        'rigid_generator_reference_xyz_mm': reference,
        'exact_saved_rigid_work_n_nmm': list(map(str, actual)), 'exact_source_wrench_n_nmm': list(map(str, expected)),
        'exact_rigid_work_minus_source_wrench_n_nmm': list(map(str, error)),
        'potential': '-sum_i f_saved_i*q_panel_i', 'all_saved_linear_panel_work_preserved_by_definition': True,
        'physical_finite_panel_bulk_coupling_or_objectivity_qualified': False}


def saved_arrays(manifest, captured):
    with np.load(io.BytesIO(captured), allow_pickle=False) as arrays:
        result = []
        for key, shape in [(manifest['applied_key'], (manifest['final_ndof'],)),
                           (manifest['rigid_modes_key'], (manifest['final_ndof'], 6))]:
            value = arrays[key]
            require(value.dtype.str == '<f8' and value.shape == shape and np.isfinite(value).all(),
                    'finite float64 saved force and rigid-work arrays required')
            metadata = manifest['array_metadata'][key]
            require(metadata['shape'] == list(shape) and metadata['dtype'] == value.dtype.str
                    and metadata['nbytes'] == value.nbytes
                    and metadata['content_sha256'] == hashlib.sha256(value.tobytes()).hexdigest(),
                    'saved array content binding differs')
            result.append(value)
    return result


def geometry_helpers(inputs, base, pins):
    """Reuse fixed reference-distance and strict-container definitions only."""
    import cadquery as cq
    import OCP
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape

    loader = base.private(inputs['definition_loader'], pins)
    namespace = {'io': io, 'hashlib': hashlib, 'importlib': importlib, 'np': np, 'cq': cq, 'OCP': OCP,
                 'BRepExtrema_DistShapeShape': BRepExtrema_DistShapeShape, 'require': require}
    reference = loader.definitions(inputs['reference_geometry_helper'], ('brep_sha', 'distance_tool', 'tools'),
        ('PINNED_TOOLS',), namespace, pins)
    reference.cq = cq
    strict = loader.definitions(inputs['strict_container_helper'], ('strict_solid',), (), {'require': require}, pins)
    return reference, strict, reference.tools()


def cube_geometry(loads, observations, reference, strict, base, pins, tolerance):
    solids, proofs, results = {}, {}, []
    for row in loads:
        name = row['body']; observed = observations[name]
        if name not in solids:
            data = base.captured(observed['source'], pins)
            imported = reference.cq.Shape.importBrep(io.BytesIO(data))
            solid, proof = strict.strict_solid(imported, reference)
            require(proof == observed['strict_container'], 'same complete finished-solid wrapper and topology required')
            solids[name] = solid; proofs[name] = proof
        solid = solids[name]; center = row['point_xyz_mm']
        vertex = reference.cq.Vertex.makeVertex(*center)
        shells = solid.Shells(); require(shells, 'complete closed-solid boundary shells required')
        distances = [reference.distance_tool(vertex, shell, float(tolerance)).Value() for shell in shells]
        inside = bool(solid.isInside(center, float(tolerance)))
        require(inside and min(distances) > float(tolerance), 'strictly interior original load point required')
        results.append({'id': row['id'], 'body': name, 'boundary_shell_count': len(shells),
            'all_shell_distances_mm': distances, 'minimum_boundary_distance_mm': min(distances), 'inside': inside})
    return results, proofs


def run(reference):
    pins = {}; gravity = bootstrap(pins); contact = gravity.bootstrap(pins); material = contact.bootstrap(pins)
    prior = material.bootstrap(pins); boot = prior.bootstrap(pins); base = boot.producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_remaining_load_work_inputs/v1'
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
            and inputs['extra_grid'] is False and inputs['actual_observations'] is None
            and inputs['structural_acceptance'] is False, 'current load-work-only scope required')
    for row in inputs['execution_sources']:
        base.captured(row, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing load-work checker required')
    parent = json.loads(base.captured(inputs['gravity_result'], pins))
    require(parent['inventory']['material_gravity_laws'] == 552
            and parent['complete_coupled_load_contact_fracture_law_or_evaluation_ready'] is False, 'same incomplete retained gravity stage required')
    for path, digest in parent['source_sha256'].items():
        base.captured({'path': path, 'sha256': digest}, pins)
    runtime = boot.check_runtime(parent['runtime'])
    tolerance = F(inputs['geometry_query_tolerance_mm']); widths = list(map(F, inputs['cube_half_widths_mm']))
    require(tolerance == F(1, 10**7) and widths == [F(1, 2), F(1), F(2)], 'predeclared numerical cube spread and geometry gate required')
    force_tol, moment_tol = F(inputs['panel_force_work_tolerance_n']), F(inputs['panel_moment_work_tolerance_nmm'])
    require(force_tol == F(1, 10**7) and moment_tol == F(1, 10**5), 'predeclared separate panel work gates required')
    geo, strict, versions = geometry_helpers(inputs, base, pins)
    common, supports, proofs, cubes = None, None, None, None
    case_results, vectors, panel_indices = [], {}, None
    for case in parent['cases']:
        binding = case['binding']; field = json.loads(base.captured(binding['field'], pins)); own = field['source_inputs']
        require(field['case_id'] == binding['case_id'] and field['state_id'] == binding['state_id'], 'own retained case required')
        mapped = contact.split_loads(field); timbers = {row['name'] for row in own['timber_rows']}
        timber_loads = [row for row in mapped if row['body'] in timbers and row['id'].startswith('bolt-weight/')]
        require(len(timber_loads) == 66, 'all 66 timber metal-share forces required')
        share_axes = attachment_axes(timber_loads, own['hillman_rows'])
        if common is None:
            common = timber_loads
            observations = {row['id']: row for row in own['finished_body_observations']}
            supports, proofs = cube_geometry(timber_loads, observations, geo, strict, base, pins, tolerance)
            cubes = [{'source_load': row, 'axis_id': share_axes[row['id']], 'geometry_support': support,
                      'spread_scenarios': [cube_law(row, width, support['minimum_boundary_distance_mm'], tolerance, support['inside'], contact)
                                           for width in widths]} for row, support in zip(timber_loads, supports, strict=True)]
        else:
            require(common == timber_loads, 'same 66 attachment gravity loads in all six cases required')
        bundle = field['operator_bundle']; manifest = json.loads(base.captured(bundle['manifest'], pins))
        require(manifest['arrays'] == bundle['arrays'] and manifest['final_ndof'] == 9350
                and manifest['coordinate_map']['final_ndof'] == 9350, 'same complete saved operator bundle required')
        applied, rigid = saved_arrays(manifest, base.captured(bundle['arrays'], pins))
        panels = manifest['coordinate_map']['panels']; indices = {name: row['indices'] for name, row in panels.items()}
        require(set(panels) == set(own['panel_ids']) and len(panels) == 6
                and all(len(value) == 363 for value in indices.values())
                and len({i for value in indices.values() for i in value}) == 2178, 'six disjoint retained panel spaces required')
        require(panel_indices is None or panel_indices == indices, 'same panel coefficient ordering across cases required')
        panel_indices = indices; records = []
        for name, descriptor in panels.items():
            loads = [row for row in mapped if row['body'] == name]
            record = panel_work_record(name, descriptor, loads, applied, rigid, manifest['rigid_modes_reference_xyz_mm'],
                                       contact, force_tol, moment_tol)
            values = record.pop('exact_linear_generalized_force_n'); digest = record['force_vector_sha256']
            require(digest not in vectors or vectors[digest] == values, 'same vector digest must bind identical force coefficients')
            vectors[digest] = values; records.append(record)
        require(sum(len(row['source_load_ids']) for row in records) == 217, 'all 217 source panel actions required per case')
        complete_partition(mapped, [row['id'] for row in parent['common_gravity_laws']],
                           [row['id'] for row in timber_loads], [identity for row in records for identity in row['source_load_ids']])
        case_results.append({'binding': binding, 'operator_bundle': bundle, 'panel_work': records,
            'source_load_inventory_accounted_for': 552+66+217, 'new_response_evaluated': False})
    require(len(case_results) == 6 and len(cubes) == 66, 'six complete retained load inventories required')
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_remaining_load_work/v1', 'inputs': reference, 'source_sha256': pins,
        'runtime': runtime, 'geometry_query_versions': versions,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
        'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
        'inventory': {'source_loads_per_case': 835, 'prior_material_gravity_laws': 552, 'timber_metal_share_loads': 66,
                      'cube_spread_scenarios_per_load': 3, 'panel_loads_per_case': 217, 'panels': 6, 'panel_coefficients_per_case': 2178},
        'common_timber_gravity_cubes': cubes, 'finished_timber_container_proofs': proofs,
        'saved_panel_force_vectors_by_sha256': vectors, 'cases': case_results,
        'load_hypotheses_and_limits': inputs['load_hypotheses_and_limits'], 'primary_method': inputs['primary_method'],
        'source_actions_all_accounted_for_in_declared_work_spaces': True,
        'old_panel_objective_finite_or_physical_bulk_coupling_adopted': False,
        'new_response_native_frame_contact_equilibrium_optimization_inverse_or_factorization': False,
        'cached_solid_boundary_and_inside_queries_performed': True, 'candidate_CAD_rebuild_or_geometry_change': False,
        'complete_coupled_contact_fracture_law_or_evaluation_ready': False,
        'physical_stiffness_restraint_demand_or_complete_resistance_qualified': False,
        'panel_screw_exceedances_deferred': True, 'actual_observations': None, 'structural_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); require(not args.out.exists(), 'preserve issued remaining-load evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({'output': str(args.out), 'timber_loads': len(result['common_timber_gravity_cubes']),
                      'panel_vectors': len(result['saved_panel_force_vectors_by_sha256'])}))


if __name__ == '__main__':
    main()
