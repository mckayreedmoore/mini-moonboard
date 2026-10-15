"""Reaction enclosures for the declared continuous flange-normal model.

Spread previously saved auxiliary weights over disjoint material boxes. Reuse
the certified minor and elastic residual bounds; compute no new response,
static optimization, matrix inverse or factorization.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import math
import platform
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def captured(reference, pins):
    path = (ROOT/reference['path']).resolve()
    require(path.is_relative_to(ROOT), 'repository source required')
    data = path.read_bytes(); digest = hashlib.sha256(data).hexdigest()
    require(digest == reference['sha256'] and pins.get(reference['path'], digest) == digest,
            'captured source changed: '+reference['path'])
    pins[reference['path']] = digest
    return data


def private(reference, pins):
    module = ModuleType('_eoere_verified_normal_reactions_'+Path(reference['path']).stem)
    module.__file__ = str(ROOT/reference['path'])
    exec(compile(captured(reference, pins), module.__file__, 'exec'), module.__dict__)  # noqa: S102 - pinned buffer
    return module


def disjoint(boxes):
    """Interiors must be disjoint; touching boundaries have zero area."""
    return all(a[1] <= b[0] or b[1] <= a[0] or a[3] <= b[2] or b[3] <= a[2]
               for i, a in enumerate(boxes) for b in boxes[i+1:])


def material_boxes(domain, maximum, trace, method):
    half = F(maximum)
    require(half > 0, 'positive finite box-size control required')
    for _ in range(32):
        polygons = []
        for center in domain['samples']:
            x, y = map(F, center)
            box = x-half, x+half, y-half, y+half
            polygon = [(box[0], box[2]), (box[1], box[2]), (box[1], box[3]), (box[0], box[3])]
            if not (all(trace.previous().inside([tuple(map(F, p)) for p in domain['polygon']], p) for p in polygon)
                    and all(trace.previous().box_hole_clearance(box, tuple(map(F, h))) > 0 for h in domain['holes'])):
                break
            polygons.append(polygon)
        bounds = [(p[0][0], p[1][0], p[0][1], p[2][1]) for p in polygons]
        if len(polygons) == len(domain['samples']) and disjoint(bounds):
            require(all(method.geometry.moments(p, F(0))[0] == 4*half*half for p in polygons), 'exact box measure required')
            return half, polygons
        half /= 2
    raise ValueError('no certified finite disjoint material boxes selected')


def relevant_coordinates(timber, fitting, regions):
    indices = set(fitting)
    for region in regions:
        if region['mode'] == 'interior':
            nodes = timber['index'][region['segment']:region['segment']+2]
        else:
            require(region['mode'] in ('before', 'after'), 'registered station mode required')
            nodes = [timber['index'][0 if region['mode'] == 'before' else -1]]
        indices.update(i for node in nodes for i in node)
    return sorted(indices)


def residual_transfer(old_rows, new_rows, candidate, old_radius, new_radius, certificates, previous, core, bounds):
    """Carry the old core residual plus an exact free-coordinate load box.

    Both corrected complete loads annihilate the same registered kernel.
    Their difference is in range K0. For that range the free coordinates give
    the complementary norm through the already certified positive G blocks.
    """
    require(len(old_rows) == len(new_rows) == len(candidate) == len(old_radius) == len(new_radius),
            'same complete auxiliary scalar order required')
    n = sum(c['coordinates'] for c in certificates)
    old_bt, new_bt = core.transpose(old_rows, n), core.transpose(new_rows, n)
    center = [a-b for a, b in zip(core.action(old_bt, candidate), core.action(new_bt, candidate), strict=True)]
    uncertainty = [sum((abs(v)*old_radius[j] for j, v in a.items()), F(0))
                   +sum((abs(v)*new_radius[j] for j, v in b.items()), F(0))
                   for a, b in zip(old_bt, new_bt, strict=True)]
    require([r['body'] for r in previous] == [c['body'] for c in certificates], 'own old body residual order required')
    result, total = [], F(0)
    for certificate, old in zip(certificates, previous, strict=True):
        own, datum = certificate['global_coordinates'], set(certificate['datum_local_coordinates'])
        mu = F(certificate['quotient_positive_certificate']['exact_smallest_eigenvalue_lower'])
        require(mu > 0 and certificate['constructed_core_PSD_and_exact_registered_kernel_proven'] is True,
                'positive certified own free/free block required')
        square = sum(((abs(center[g])+uncertainty[g])**2 for i, g in enumerate(own) if i not in datum), F(0))
        delta = bounds.upper(square/mu)
        inherited = F(old['exact_complementary_residual_square_upper'])
        combined = bounds.upper((bounds.root_bounds(inherited)[1]+bounds.root_bounds(delta)[1])**2)
        result.append({'body': certificate['body'], 'exact_inherited_residual_square_upper_nmm': str(inherited),
                       'exact_changed_dual_load_square_upper_nmm': str(delta),
                       'exact_complementary_residual_square_upper_nmm': str(combined)})
        total += combined
    return total, result


def distributed_gap(primal, columns, components, candidate, radius, movement):
    """A feasible constant nonnegative pressure on each disjoint material box."""
    result = F(primal)
    for j in columns:
        row = components[j]
        x, r, k, d = candidate[j], radius[j], row['stiffness'], movement[j]
        require(x-r >= 0 and r >= 0 and k > 0, 'nonnegative dual box pressure required')
        result += (x+r)**2/(2*k)-x*d+r*abs(d)
    require(result >= 0, 'distributed Fenchel-gap upper cannot be negative')
    return result


def unchanged_gaps(ports, candidate, radius, movement, bounds):
    result = defaultdict(F)
    for port in ports:
        row, columns = port['descriptor'], port['columns']
        if row['kind'] == 'flange_contact':
            continue
        if port['type'] == 'vector':
            if columns[0] is not None:
                j = columns[0]
                result[row['kind']] += bounds.upper(bounds.spring_gap([movement[j]], [candidate[j]], [radius[j]],
                    row['ka'], F(1), F(1), positive=row['tension_only']))
            js = columns[1:]
            result[row['kind']] += bounds.upper(bounds.spring_gap([movement[j] for j in js], [candidate[j] for j in js],
                [radius[j] for j in js], row['kl'], F(1), F(1), clearance=row['clearance']))
        else:
            j = columns[0]
            result[row['kind']] += bounds.upper(bounds.spring_gap([movement[j]], [candidate[j]], [radius[j]],
                row['stiffness'], F(1), F(1), positive=port['type'] == 'normal'))
    return result


def patch_resultants(records, domains, candidate, radius, gap, method, bounds):
    result = []
    for identity, nominal in domains.items():
        own = [r for r in records if r['patch_id'] == identity]
        require(len(own) == 4, 'four disjoint dual supports per complete patch required')
        columns = [r['column'] for r in own]
        center = sum((candidate[j] for j in columns), F(0))
        uncertainty = sum((radius[j] for j in columns), F(0))
        outer = [tuple(map(F, p)) for p in nominal['analytic_domain']['polygon']]
        area_upper = method.geometry.moments(outer, F(0))[0]
        gram_upper = F(nominal['declared_existing_stiffness_n_mm3'])*area_upper
        # Cauchy-Schwarz on the complete continuous pressure field uses its
        # full material area. Box support areas apply only to the dual cost.
        enclosure = bounds.functional([{0: F(1)}], [center], [uncertainty], [gram_upper], gap)
        result.append({'patch_id': identity, 'exact_material_area_upper_mm2': str(area_upper),
                       'normal_resultant': enclosure})
    return result


def prepare(inputs, pins):
    transfer = private(inputs['transfer_helper'], pins)
    prior_inputs = json.loads(captured(inputs['transfer_inputs'], pins))
    exact = private(prior_inputs['exact_recession_helper'], pins)
    trace = private(prior_inputs['trace_helper'], pins)
    loader = private(prior_inputs['definition_loader'], pins)
    core = loader.definitions(inputs['core_helper'], ('transpose', 'product', 'action'), (),
                              {'F': F, 'rational': exact.rational}, pins)
    env = {'F': F, 'math': math, 'rational': exact.rational, 'require': require, 'core': core, 'exact': exact}
    bounds = loader.definitions(inputs['bound_helper'], ('root_bounds', 'upper', 'family', 'spring_gap', 'functional'), (), env, pins)
    bounds.require, bounds.rational = require, exact.rational
    reader = loader.definitions(prior_inputs['rigid_reader'], ('rigid_basis',), ('FAMILIES',),
                                {'F': F, 'np': np, 'method': exact}, pins)
    audit = loader.definitions(inputs['port_reader'], ('scalar_row', 'register', 'functional', 'rear_leg'), (),
                               {'F': F, 'np': np, 'method': bounds, 'core': core}, pins)
    mixed = loader.definitions(inputs['mixed_helper'], ('necessary_interval',), (),
                              {'F': F, 'method': bounds, 'audit': audit}, pins)
    trace_result = json.loads(captured(prior_inputs['trace_result'], pins))
    for path, digest in trace_result['source_sha256'].items():
        captured({'path': path, 'sha256': digest}, pins)
    trace_inputs = json.loads(captured(trace_result['inputs'], pins))
    method = trace.methods(trace_inputs, pins)
    nominal = json.loads(captured(trace_inputs['normal_patch_result'], pins))
    return SimpleNamespace(transfer=transfer, exact=exact, trace=trace, core=core, bounds=bounds, reader=reader, mixed=mixed,
                           audit=audit, trace_result=trace_result, trace_inputs=trace_inputs, method=method, nominal=nominal,
                           prior_inputs=prior_inputs)


def replace_rows(field, chart, components, ports, maps, domains, maximum, helpers):
    """Full coordinate area rows, retaining every station and binary coefficient."""
    h, records = helpers, []
    by_identity = {c['id']: j for j, c in enumerate(components)}
    contacts = {p['descriptor']['id']: p['descriptor'] for p in ports if p['descriptor']['kind'] == 'flange_contact'}
    for patch in field['source_inputs']['flange_shared_face_patches']:
        nominal = domains[patch['id']]; domain = nominal['analytic_domain']
        require(patch['trimmed_region_signature_sha256'] == nominal['trimmed_region_signature_sha256'], 'own nominal patch required')
        timber, fitting = chart['timber'][patch['second']], chart['four_port_fittings'][patch['first']]
        port, = [p for p in fitting['ports'] if p['id'] == patch['source_owned_port_id']]
        indices = fitting['dof_indices'][6*port['port_index']:6*(port['port_index']+1)]
        half, polygons = material_boxes(domain, maximum, h.trace, h.method)
        for cell, polygon in zip(patch['cells'], polygons, strict=True):
            identity = patch['id'].rsplit('/timber-face/', 1)[0]+'/'+cell['id']; j = by_identity[identity]
            normal = contacts[identity]['direction_xyz']
            regions = h.trace.pieces(dict(domain, polygon=polygon), timber, h.method.geometry, h.method.poly)
            coordinates = relevant_coordinates(timber, indices, regions)
            unit = {i: defaultdict(F, {i: F(1)}) for i in coordinates}
            row, regions, area = h.transfer.average_compression_row(domain, polygon, timber, port, indices, unit, normal, h.trace, h.method)
            rigid = h.core.product([row], maps)[0]
            density = F(nominal['declared_existing_stiffness_n_mm3'])
            components[j] = dict(components[j], row=row, stiffness=density*area)
            records.append({'patch_id': patch['id'], 'id': identity, 'column': j, 'exact_half_width_mm': str(half),
                            'normal_director_xyz': normal,
                            'polygon_xy_mm': [[str(v) for v in p] for p in polygon], 'exact_area_mm2': str(area),
                            'exact_density_n_mm3': str(density), 'station_piece_count': len(regions),
                            'exact_full_compression_row': {str(i): str(v) for i, v in row.items()},
                            'exact_rigid_compression_row': {str(i): str(v) for i, v in rigid.items()}})
    require(len(records) == len({r['column'] for r in records}) == 352, 'all 352 distinct flange rows required')
    return records


def run(reference):
    pins = {}; inputs = json.loads(captured(reference, pins))
    require(inputs['schema'] == 'eoere_continuous_normal_reaction_inputs/v1'
            and inputs['runtime'] == {'python': platform.python_version(), 'numpy': np.__version__,
                                      'scipy': importlib.metadata.version('scipy')}
            and inputs['material_box_maximum_half_width_mm'] == '8'
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
            and inputs['extra_grid'] is False and inputs['actual_observations'] is None
            and inputs['structural_acceptance'] is False, 'exact reaction-bound scope, input and runtime required')
    for ref in inputs['execution_sources']:
        captured(ref, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing reaction producer required')
    h = prepare(inputs, pins)
    source = json.loads(captured(inputs['original_bounds'], pins)); source_inputs = json.loads(captured(source['inputs'], pins))
    core = json.loads(captured(h.prior_inputs['core_result'], pins))
    old = json.loads(captured(h.prior_inputs['recession_result'], pins))
    existence = json.loads(captured(inputs['existence_result'], pins))
    response = json.loads(captured(h.trace_inputs['current_response'], pins))
    mixed = json.loads(captured(inputs['mixed_result'], pins))
    require(source_inputs['core_certificate'] == h.prior_inputs['core_result']
            and source['schema'] == 'eoere_current_original_load_bounds/v1'
            and source['bounds_apply_to_original_exact_loads_for_certified_comparator_family'] is True
            and source['scalar_component_identities'] == old['shared_constraint_identities']
            and existence['all_six_original_loads_have_conditional_continuous_normal_model_existence'] is True
            and existence['inputs'] == inputs['transfer_inputs'] and core['body_count'] == 150
            and response['geometry_revision'] == inputs['geometry_revision']
            and response['hardware_revision'] == inputs['hardware_revision'] and response['extra_grid'] is False
            and mixed['schema'] == 'eoere_current_mixed_reaction_bound/v1'
            and mixed['axis_id'] == 'eoere_bolt_067'
            and len(response['cases']) == len(source['cases']) == len(old['cases']) == 6,
            'same completed original-load, core, existence and response authority required')
    domains = {r['id']: r for r in h.nominal['records']}
    require(len(domains) == 88 and len(h.trace_result['records']) == 528, 'all retained normal domains and saved traces required')
    selected = old['shared_minor_columns']; selected_set = set(selected)
    results, records, common_chart, common_maps, common_old, common_new, rank, common_patches = [], None, None, None, None, None, None, None
    trace_rows = {(r['case_id'], r['patch_id']): r for r in h.trace_result['records']}
    require(len(trace_rows) == 528, 'distinct own saved contact traces required')
    for binding, previous, original in zip(response['cases'], source['cases'], old['cases'], strict=True):
        require(previous['binding'] == original['binding'] == {k: binding[k] for k in ('case_id', 'state_id', 'field')},
                'own unchanged saved case and original-load bounds required')
        field = json.loads(captured(binding['field'], pins)); pointer = field['operator_bundle']
        manifest = json.loads(captured(pointer['manifest'], pins)); data = captured(pointer['arrays'], pins)
        require(pointer == previous['operator_bundle'] == original['operator_bundle'], 'own original operator bundle required')
        with np.load(io.BytesIO(data), allow_pickle=False) as arrays:
            chart = manifest['coordinate_map']
            maps, owners, bodies, dimension = h.reader.rigid_basis(chart, arrays[manifest['rigid_modes_key']])
            parts = h.transfer.partitions(manifest, arrays)
            enabled = {r['id'] for r in parts['tangents']} & set(old['shared_constraint_identities'])
            components, ports, bilateral = h.audit.register(parts, field, enabled)
            require(dimension == 800 and bilateral == 968 and len(maps) == len(owners) == 9350 and len(ports) == 2324
                    and len(field['source_inputs']['shafts']) == 100 and len(field['panel_screw_actions']) == 66
                    and [r['id'] for r in components] == source['scalar_component_identities']
                    and bodies == old['shared_body_rigid_basis'], 'complete retained port and rigid registration required')
            old_rows = [r['row'] for r in components]
            old_matrix = h.core.transpose(h.core.product(old_rows, maps), dimension)
            require(h.exact.matrix_digest(old_matrix) == previous['exact_constraint_matrix_sha256'] == original['exact_constraint_matrix_sha256'],
                    'own exact old rigid constraint matrix required')
            if records is None:
                for body, certificate in zip(bodies, core['body_certificates'], strict=True):
                    own = [i for i, name in enumerate(owners) if name == body['body']]
                    local = [{j-body['first_rigid_column']: v for j, v in maps[i].items()} for i in own]
                    require(certificate['global_coordinates'] == own and certificate['body'] == body['body']
                            and certificate['exact_registered_rigid_basis_sha256'] == h.exact.matrix_digest(local),
                            'same exact own core rigid registration required')
                records = replace_rows(field, chart, components, ports, maps, domains, F(inputs['material_box_maximum_half_width_mm']), h)
                common_new = [r['row'] for r in components]
                new_matrix = h.core.transpose(h.core.product(common_new, maps), dimension)
                rank = h.transfer.perturb_rank(old_matrix, new_matrix, selected, old['shared_rank_certificate'], h.exact)
                require(rank['full_rank_proven'], 'new material-box minor perturbation inconclusive')
                common_chart, common_maps, common_old = chart, maps, old_rows
                common_patches = field['source_inputs']['flange_shared_face_patches']
            else:
                require(chart == common_chart and maps == common_maps and old_rows == common_old
                        and field['source_inputs']['flange_shared_face_patches'] == common_patches,
                        'same complete source maps across all cases required')
                for record in records:
                    j = record['column']
                    components[j] = dict(components[j], row=common_new[j],
                                         stiffness=F(record['exact_area_mm2'])*F(record['exact_density_n_mm3']))
            load = h.core.action(h.core.transpose(maps, dimension), list(map(F, arrays[manifest['applied_key']])))
            load_digest = hashlib.sha256(json.dumps(list(map(str, load)), separators=(',', ':')).encode()).hexdigest()
            require(load_digest == previous['exact_original_rigid_load_sha256'] == original['exact_rigid_load_sha256']
                    and hashlib.sha256(arrays[manifest['applied_key']].tobytes()).hexdigest() == previous['original_applied_binary64_sha256'],
                    'same exact original full load required')
            candidate = list(map(F, previous['candidate_auxiliary_weights']))
            require(h.exact.certify(old_matrix, len(components), bilateral, load, previous['candidate_auxiliary_weights'],
                                    selected, old['shared_rank_certificate']) == previous['load_certificate'],
                    'same exact inherited corrected auxiliary witness required')
            new_matrix = h.core.transpose(h.core.product(common_new, maps), dimension)
            proof = h.exact.certify(new_matrix, len(components), bilateral, load,
                                    previous['candidate_auxiliary_weights'], selected, rank)
            old_error, new_error = F(previous['load_certificate']['exact_selected_correction_inf_upper']), F(proof['exact_selected_correction_inf_upper'])
            old_radius = [old_error if j in selected_set else F(0) for j in range(len(components))]
            radius = [new_error if j in selected_set else F(0) for j in range(len(components))]
            residual, body_residuals = residual_transfer(old_rows, common_new, candidate, old_radius, radius,
                core['body_certificates'], previous['body_residual_enclosures'], h.core, h.bounds)
            require(sum((F(r['exact_complementary_residual_square_upper']) for r in previous['body_residual_enclosures']), F(0))
                    == F(previous['exact_elastic_residual_complementary_square_upper_nmm']), 'complete inherited residual sum required')
            q = list(map(F, field['response']['q'])); movement = h.core.action(common_new, q)
            gaps = unchanged_gaps(ports, candidate, radius, movement, h.bounds)
            columns = [r['column'] for r in records]
            primal = F(0)
            for patch in field['source_inputs']['flange_shared_face_patches']:
                prior_trace = trace_rows[binding['case_id'], patch['id']]
                normal, = {tuple(r['normal_director_xyz']) for r in records if r['patch_id'] == patch['id']}
                require(prior_trace['field'] == binding['field'] and prior_trace['state_id'] == binding['state_id']
                        and tuple(prior_trace['contact_director_xyz']) == normal, 'own saved-pose contact upper required')
                primal += F(prior_trace['exact_energy_upper_nmm'])
            normal_gap = h.bounds.upper(distributed_gap(primal, columns, components, candidate, radius, movement))
            total = residual/2+sum(gaps.values(), F(0))+normal_gap
            stiffness = [r['stiffness'] for r in components]
            legs = [h.audit.rear_leg(ports, name, candidate, radius, stiffness, total) for name in ('lumber_leg_left', 'lumber_leg_right')]
            normal_resultants = patch_resultants(records, domains, candidate, radius, total, h.method, h.bounds)
            mixed_bound = None
            if previous['binding'] == mixed['refined_control']['binding']:
                lookup = {r['id']: j for j, r in enumerate(components)}
                coefficients = {lookup[key]: F(value) for key, value in mixed['refined_control']['source_linear_coefficients'].items()}
                require(all(components[j]['kind'] != 'flange_contact' for j in coefficients), 'unchanged mixed lateral action definition required')
                mixed_bound = h.mixed.necessary_interval(coefficients, F(mixed['refined_control']['exact_fixed_point_work']),
                    candidate, radius, stiffness, total, F(mixed['exact_frozen_continuous_support_upper']), ['16/5', '4', '5'])
            lands = []
            captures = {p['descriptor']['id']: p for p in ports if p['descriptor']['kind'] == 'shaft_end_capture'}
            for land in previous['families'][0]['wood_land_mean_reference_enclosures']:
                port = captures[land['capture_id']]; row = port['descriptor']; j = port['columns'][0]
                require(row['axis_id'] == land['axis_id'] and row['second'] == land['host'], 'same own washer land required')
                enclosure = h.audit.functional([{j: F(v)} for v in row['direction_xyz']], candidate, radius, stiffness, total)
                index = F(enclosure['exact_norm_upper'])/(F(land['least_catalog_profile_area_mm2'])*F(source_inputs['wood_land_reference_mpa']))
                lands.append({k: land[k] for k in ('axis_id', 'capture_id', 'host', 'least_catalog_profile_area_mm2')} |
                             {'force': enclosure, 'exact_mean_pressure_reference_upper_index': str(index), 'mean_pressure_reference_upper_index': float(index)})
            require(len(lands) == 112, 'all catalog wood lands required')
            results.append({'binding': previous['binding'], 'operator_bundle': pointer, 'load_certificate': proof,
                            'exact_original_rigid_load_sha256': load_digest,
                            'exact_old_correction_inf_n': str(old_error), 'exact_new_correction_inf_n': str(new_error),
                            'exact_elastic_residual_complementary_square_upper_nmm': str(residual), 'body_residual_enclosures': body_residuals,
                            'exact_saved_pose_continuous_primal_energy_upper_nmm': str(primal),
                            'exact_distributed_normal_Fenchel_gap_upper_nmm': str(normal_gap),
                            'exact_unchanged_spring_gap_upper_by_kind_nmm': {k: str(v) for k, v in gaps.items()},
                            'exact_total_Fenchel_gap_upper_nmm': str(total), 'total_Fenchel_gap_upper_nmm': float(total),
                            'credited_rear_leg_normal_enclosures': legs, 'wood_land_mean_reference_enclosures': lands,
                            'continuous_patch_normal_resultant_enclosures': normal_resultants,
                            'bolt_067_original_lateral_necessary_interval': mixed_bound,
                            'worst_wood_land_upper_index': max(lands, key=lambda r: F(r['exact_mean_pressure_reference_upper_index']))})
        print(json.dumps({'case': binding['case_id'], 'gap_upper_nmm': results[-1]['total_Fenchel_gap_upper_nmm']}), flush=True)
    for path, digest in tuple(pins.items()):
        captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_continuous_normal_reactions/v1', 'inputs': reference, 'source_sha256': pins,
            'geometry_revision': response['geometry_revision'], 'hardware_revision': response['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'shared_material_box_records': records, 'shared_perturbed_rank_certificate': rank,
            'shared_exact_old_rigid_matrix_sha256': h.exact.matrix_digest(old_matrix),
            'shared_exact_new_rigid_matrix_sha256': h.exact.matrix_digest(new_matrix), 'cases': results,
            'all_six_exact_original_load_dual_bounds_proven': True,
            'saved_poses_admitted_as_changed_law_equilibria': False,
            'new_LP_inverse_factorization_native_CAD_or_response_solve': False,
            'physical_stiffness_demand_restraint_or_complete_resistance_qualified': False,
            'panel_screw_exceedances_deferred': True, 'actual_observations': None, 'structural_acceptance': False,
            'limits': inputs['limits']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'preserve issued continuous-normal reaction evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size, 'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
