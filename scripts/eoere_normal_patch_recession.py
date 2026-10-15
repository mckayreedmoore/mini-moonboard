"""Transfer an existing strict recession certificate to continuous flange beds.

Material-box averages are necessary tests of zero distributed contact energy.
Exact matrix perturbation and old auxiliary weights require no new solve.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import platform
from collections import defaultdict
from fractions import Fraction as F
from itertools import pairwise
from pathlib import Path
from types import ModuleType

import numpy as np
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def captured(reference, pins):
    path = (ROOT/reference['path']).resolve()
    require(path.is_relative_to(ROOT), 'repository source required')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == reference['sha256'] and pins.get(reference['path'], digest) == digest,
            'captured source changed: '+reference['path'])
    pins[reference['path']] = digest
    return data


def private(reference, pins):
    module = ModuleType('_eoere_verified_patch_recession_'+Path(reference['path']).stem)
    module.__file__ = str(ROOT/reference['path'])
    exec(compile(captured(reference, pins), module.__file__, 'exec'), module.__dict__)  # noqa: S102 - pinned source buffer
    return module


def triangle_integral(polynomial, polygon, evaluate):
    """Exact degree-two edge-midpoint triangle rule on a convex polygon fan."""
    polynomial = {powers: F(value) for powers, value in polynomial.items()}
    polygon = [tuple(map(F, p)) for p in polygon]
    require(all(i+j <= 2 for i, j in polynomial) and len(polygon) >= 3, 'quadratic convex-polygon trace required')
    total = F(0)
    a = polygon[0]
    for b, c in pairwise(polygon[1:]):
        area = ((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
        require(area >= 0, 'counterclockwise convex polygon fan required')
        midpoints = [tuple((x+y)/2 for x, y in zip(p, q, strict=True)) for p, q in ((a, b), (b, c), (c, a))]
        total += area*sum((evaluate(polynomial, p) for p in midpoints), F(0))/3
    return total


def material_box(domain, center, half, trace, method):
    half = F(half); x, y = map(F, center)
    require(half > 0, 'positive material-box half-width required')
    box = x-half, x+half, y-half, y+half
    polygon = [(box[0], box[2]), (box[1], box[2]), (box[1], box[3]), (box[0], box[3])]
    outer = [tuple(map(F, p)) for p in domain['polygon']]
    holes = [tuple(map(F, h)) for h in domain['holes']]
    require(all(trace.previous().inside(outer, p) for p in polygon)
            and all(trace.previous().box_hole_clearance(box, h) > 0 for h in holes),
            'complete positive-area box must be strictly inside retained material')
    require(method.geometry.moments(polygon, F(0))[0] == 4*half*half, 'exact box area identity required')
    return polygon


def average_compression_row(domain, polygon, timber, port, fitting_indices, basis_poses, normal, trace, method):
    """Integrate the actual piecewise point map on each registered rigid column."""
    box_domain = dict(domain, polygon=polygon)
    regions = trace.pieces(box_domain, timber, method.geometry, method.poly)
    area = sum((r['outer_area'] for r in regions), F(0))
    require(area > 0, 'positive complete material-box measure required')
    point = trace.world_polynomials(domain)
    coefficients = {}
    for column, pose in basis_poses.items():
        integral = F(0)
        for region in regions:
            polynomial = trace.gap_polynomial(point, timber, port, fitting_indices, pose, normal,
                                              region['mode'], region['segment'], method.poly)
            integral += triangle_integral(polynomial, region['polygon'], method.poly.evaluate)
        if integral:
            coefficients[column] = -integral/area
    return coefficients, regions, area


def perturb_rank(old, new, selected, prior, exact):
    require(prior['full_rank_proven'] is True and prior['minor_dimension'] == len(old) == len(new)
            and prior['exact_minor_sha256'] == exact.matrix_digest(exact.minor(old, selected)),
            'unchanged original certified minor required')
    subset = set(selected)
    delta = max(sum((abs(b.get(j, F(0))-a.get(j, F(0))) for j in (a.keys() | b.keys()) & subset), F(0))
                for a, b in zip(old, new, strict=True))
    inverse = F(prior['exact_inverse_norm_upper'])
    require(inverse > 0, 'positive inherited inverse bound required')
    eta = inverse*delta
    return {'full_rank_proven': eta < 1, 'minor_dimension': len(new),
            'exact_minor_sha256': exact.matrix_digest(exact.minor(new, selected)),
            'exact_minor_perturbation_inf': str(delta), 'exact_Neumann_product_upper': str(eta),
            'exact_inverse_norm_upper': str(inverse/(1-eta)) if eta < 1 else None,
            'inherited_rank_certificate': prior,
            'new_inverse_factorization_or_matrix_solve': False}


def partitions(manifest, arrays):
    return {name: [{**r['descriptor'], 'B': csr_matrix((arrays[r['B']['data']], arrays[r['B']['indices']],
                                                     arrays[r['B']['indptr']]), shape=tuple(r['B']['shape']))}
                   for r in manifest['partitions'][name]] for name in ('groups', 'contacts', 'tangents')}


def case_check(rows, imported, old, rank, selected, exact):
    require(imported['binding'] == old['binding'] and imported['operator_bundle'] == old['operator_bundle']
            and imported['exact_constraint_matrix_sha256'] == old['exact_constraint_matrix_sha256']
            and imported['exact_registered_rigid_basis_sha256'] == old['exact_registered_rigid_basis_sha256']
            and imported['exact_rigid_load_sha256'] == old['exact_rigid_load_sha256']
            and imported['original_applied_binary64_sha256'] == old['original_applied_binary64_sha256'],
            'unchanged own original operator, registered map and load required')
    result = {k: imported[k] for k in ('binding', 'operator_bundle', 'exact_rigid_load_sha256', 'original_applied_binary64_sha256')}
    if not rank['full_rank_proven']:
        return dict(result, strict_exact_certificate_proven=False, reason='minor perturbation bound inconclusive')
    try:
        proof = exact.certify(rows, imported['columns'], imported['bilateral'], imported['load'],
                              old['candidate_auxiliary_weights'], selected, rank)
    except ValueError as exc:
        if 'strict one-sided exact witness not certified' not in str(exc):
            raise
        return dict(result, strict_exact_certificate_proven=False, reason=str(exc))
    return dict(result, strict_exact_certificate_proven=True, load_certificate=proof)


def run(reference):
    pins = {}
    inputs = json.loads(captured(reference, pins))
    require(inputs['schema'] == 'eoere_continuous_normal_recession_inputs/v1'
            and inputs['runtime'] == {'python': platform.python_version(), 'numpy': np.__version__,
                                      'scipy': importlib.metadata.version('scipy')}
            and inputs['material_box_half_width_mm'] == '1/10000', 'exact transfer input and runtime required')
    for ref in inputs['execution_sources']:
        captured(ref, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing transfer implementation required')
    exact = private(inputs['exact_recession_helper'], pins)
    trace = private(inputs['trace_helper'], pins)
    loader = private(inputs['definition_loader'], pins)
    reader = loader.definitions(inputs['rigid_reader'], ('rigid_basis', 'compose_row', 'constraints', 'original_load'),
                                ('FAMILIES',), {'np': np, 'F': F, 'method': exact}, pins)
    old = json.loads(captured(inputs['recession_result'], pins))
    core = json.loads(captured(inputs['core_result'], pins))
    core_inputs = json.loads(captured(core['inputs'], pins))
    require(core_inputs['recession_certificate'] == inputs['recession_result'], 'core proof must use this exact recession registration')
    saved_trace = json.loads(captured(inputs['trace_result'], pins))
    for path, digest in saved_trace['source_sha256'].items():
        captured({'path': path, 'sha256': digest}, pins)
    trace_inputs = json.loads(captured(saved_trace['inputs'], pins))
    nominal = json.loads(captured(trace_inputs['normal_patch_result'], pins))
    response = json.loads(captured(trace_inputs['current_response'], pins))
    require(core['constructed_comparator_core_PSD_and_exact_registered_kernel_proven'] is True
            and core['registered_rigid_dimension'] == 800 and core['body_count'] == 150
            and old['conditional_fixed_reference_convex_family_coercivity_and_existence_at_original_loads'] is True
            and old['current_bolt_count'] == 100 and old['current_screw_count'] == 66
            and response['geometry_revision'] == saved_trace['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and response['hardware_revision'] == saved_trace['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and len(response['cases']) == len(old['cases']) == 6 and len(nominal['records']) == 88,
            'complete retained core, original-load and continuous-trace authority required')
    method = trace.methods(trace_inputs, pins)
    domains = {r['id']: r for r in nominal['records']}
    patch_records, cases, old_rows, new_rows, common_chart, common_modes, common_ids, rank = [], [], None, None, None, None, None, None
    for binding, previous, core_case in zip(response['cases'], old['cases'], core['cases'], strict=True):
        field = json.loads(captured(binding['field'], pins))
        pointer = field['operator_bundle']; manifest = json.loads(captured(pointer['manifest'], pins))
        data = captured(pointer['arrays'], pins); chart = manifest['coordinate_map']
        require(pointer == previous['operator_bundle'] and chart['final_ndof'] == 9350
                and core_case['operator_bundle'] == pointer and core_case['field'] == binding['field']
                and core_case['case_id'] == binding['case_id'] and core_case['state_id'] == binding['state_id']
                and len(field['source_inputs']['shafts']) == 100 and len(field['panel_screw_actions']) == 66,
                'own unchanged operator bundle and hardware required')
        with np.load(io.BytesIO(data), allow_pickle=False) as arrays:
            modes = arrays[manifest['rigid_modes_key']]
            maps, owners, bodies, size = reader.rigid_basis(chart, modes)
            parts = partitions(manifest, arrays)
            enabled = {r['id'] for r in parts['tangents']} & set(old['shared_constraint_identities'])
            rows, bilateral, identities = reader.constraints(parts, maps, owners, enabled)
            require(size == 800 and bilateral == 968 and len(identities) == 2872
                    and bodies == old['shared_body_rigid_basis'] and identities == old['shared_constraint_identities'],
                    'complete unchanged rigid owners and source constraints required')
            load = reader.original_load(arrays[manifest['applied_key']], maps)
            imported = {'binding': {k: binding[k] for k in ('case_id', 'state_id', 'field')},
                        'operator_bundle': pointer, 'rows': rows, 'load': load, 'columns': len(identities), 'bilateral': bilateral,
                        'exact_constraint_matrix_sha256': exact.matrix_digest(rows),
                        'exact_registered_rigid_basis_sha256': exact.matrix_digest(maps),
                        'exact_rigid_load_sha256': hashlib.sha256(json.dumps(list(map(str, load)), separators=(',', ':')).encode()).hexdigest(),
                        'original_applied_binary64_sha256': hashlib.sha256(arrays[manifest['applied_key']].tobytes()).hexdigest()}
            if old_rows is None:
                old_rows, new_rows, common_chart, common_modes, common_ids = rows, [dict(r) for r in rows], chart, modes.copy(), identities
                for body, certificate in zip(bodies, core['body_certificates'], strict=True):
                    own = [i for i, name in enumerate(owners) if name == body['body']]
                    local = [{j-body['first_rigid_column']: v for j, v in maps[i].items()} for i in own]
                    require(certificate['body'] == body['body'] and certificate['family'] == body['family']
                            and certificate['global_coordinates'] == own
                            and certificate['constructed_core_PSD_and_exact_registered_kernel_proven'] is True
                            and certificate['exact_registered_rigid_basis_sha256'] == exact.matrix_digest(local),
                            'every retained core proof must have its exact own rigid map')
                columns = {identity: j for j, identity in enumerate(identities)}
                poses = defaultdict(lambda: defaultdict(F))
                for i, row in enumerate(maps):
                    for j, value in row.items():
                        poses[j][i] = value
                owner_columns = {r['body']: range(r['first_rigid_column'], r['first_rigid_column']+len(r['source_mode_columns'])) for r in bodies}
                contact = {r['id']: r for r in parts['contacts'] if r['kind'] == 'flange_contact'}
                for patch in field['source_inputs']['flange_shared_face_patches']:
                    domain = domains[patch['id']]['analytic_domain']
                    require(patch['trimmed_region_signature_sha256'] == domains[patch['id']]['trimmed_region_signature_sha256'], 'own retained patch domain required')
                    timber = chart['timber'][patch['second']]; fitting = chart['four_port_fittings'][patch['first']]
                    port, = [p for p in fitting['ports'] if p['id'] == patch['source_owned_port_id']]
                    indices = fitting['dof_indices'][6*port['port_index']:6*(port['port_index']+1)]
                    local_poses = {j: poses[j] for name in (patch['first'], patch['second']) for j in owner_columns[name]}
                    for cell, center in zip(patch['cells'], domain['samples'], strict=True):
                        identity = patch['id'].rsplit('/timber-face/', 1)[0]+'/'+cell['id']; column = columns[identity]
                        require(column >= bilateral, 'normal patch can replace only its own one-sided row')
                        normal = contact[identity]['direction_xyz']
                        polygon = material_box(domain, center, F(inputs['material_box_half_width_mm']), trace, method)
                        average, regions, area = average_compression_row(domain, polygon, timber, port, indices, local_poses, normal, trace, method)
                        for i, row in enumerate(new_rows):
                            value = average.get(i, F(0))
                            if value:
                                row[column] = value
                            else:
                                row.pop(column, None)
                        patch_records.append({'patch_id': patch['id'], 'source_centroid_id': identity,
                                              'normal_director_xyz': normal, 'source_constraint_column': column,
                                              'material_box_polygon_xy_mm': [[str(v) for v in p] for p in polygon],
                                              'exact_box_area_mm2': str(area), 'station_piece_count': len(regions),
                                              'exact_original_compression_row': {str(j): str(r[column]) for j, r in enumerate(old_rows) if column in r},
                                              'exact_average_compression_row': {str(j): str(v) for j, v in average.items()}})
                require(len(patch_records) == 352 and len({r['source_constraint_column'] for r in patch_records}) == 352,
                        'all original flange rows require distinct material boxes')
                rank = perturb_rank(old_rows, new_rows, old['shared_minor_columns'], old['shared_rank_certificate'], exact)
            require(chart == common_chart and np.array_equal(modes, common_modes) and identities == common_ids
                    and rows == old_rows, 'all original cases require the same exact maps and source matrix')
            cases.append(case_check(new_rows, imported, previous, rank, old['shared_minor_columns'], exact))
        print(json.dumps({'case': binding['case_id'], 'strict_certificate': cases[-1]['strict_exact_certificate_proven']}), flush=True)
    for path, digest in tuple(pins.items()):
        captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_continuous_normal_recession/v1', 'inputs': reference, 'source_sha256': pins,
            'geometry_revision': response['geometry_revision'], 'hardware_revision': response['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'replaced_flange_point_rows': 352, 'continuous_flange_domains': 88, 'rigid_dimension': 800,
            'bilateral_rows': 968, 'one_sided_rows': 1904, 'patch_records': patch_records,
            'shared_original_matrix_sha256': exact.matrix_digest(old_rows), 'shared_surrogate_matrix_sha256': exact.matrix_digest(new_rows),
            'shared_minor_columns': old['shared_minor_columns'], 'shared_perturbed_rank_certificate': rank, 'cases': cases,
            'all_six_original_loads_have_conditional_continuous_normal_model_existence': all(c['strict_exact_certificate_proven'] for c in cases),
            'material_boxes_are_auxiliary_cone_tests_not_new_contact_cells': True,
            'actual_observations': None, 'physical_stiffness_demand_restraint_or_resistance_qualified': False,
            'new_LP_factorization_inverse_response_native_or_CAD_solve': False,
            'structural_acceptance': False, 'law_hypothesis': inputs['law_hypothesis'], 'limits': inputs['limits']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'preserve issued continuous-normal existence evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
