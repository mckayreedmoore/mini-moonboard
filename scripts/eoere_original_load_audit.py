"""Original-load reaction bounds for the explicitly certified core comparator.

Reuse the six original fields, port maps, static rank certificate and local
core proofs. Select auxiliary dual weights and bound elastic corrections;
do not solve, update or admit a new frame response or physical stiffness.
"""
from __future__ import annotations

import argparse
import importlib.metadata
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

import numpy as np

from scripts import eoere_elastic_core_audit as core_audit
from scripts import eoere_original_load_bounds as method
from scripts import eoere_reaction_energy_bounds as historical
from scripts.eoere_mixed_continuous_bound import read_exact

core, exact = method.core, method.exact
recession = core_audit.recession
current, model = core_audit.current, core_audit.model
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/original-load-bound-inputs-v1.json'


def validate(inputs):
    method.require(inputs['schema'] == 'eoere_current_original_load_bound_inputs/v1'
        and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
        and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
        and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
        and inputs['extra_grid'] is False and inputs['actual_observations'] is None
        and inputs['structural_acceptance'] is False and inputs['physical_demand_bounds_established'] is False,
        'unchanged conditional retained scope required')
    method.require(inputs['minimum_auxiliary_weight_n'] == '1/100000'
        and inputs['runtime_versions'] == {'numpy': '2.5.2', 'scipy': '1.18.1'} and inputs['highs_version'] == '1.12.0'
        and inputs['stiffness_families'] == [
            {'id': 'certified-core-control', 'alpha': '1', 'beta': '1'},
            {'id': 'half-to-double-comparator-trial', 'alpha': '1/2', 'beta': '2'},
            {'id': 'tenth-to-tenfold-comparator-trial', 'alpha': '1/10', 'beta': '10'}]
        and inputs['fixed_spring_kinds'] == sorted(historical.FIXED_KINDS)
        and inputs['wood_land_reference_mpa'] == 625*0.006894757293168361 and inputs['decimal_upper_rounding_digits'] == 24
        and inputs['method_helper'] == current.ref(method.OWN) and method.LOADED_SHA == inputs['method_helper']['sha256'],
        'predeclared comparator families, reference and exact helper required')


def scalar_row(matrix, i):
    result = {}
    for at in range(matrix.indptr[i], matrix.indptr[i+1]):
        j, value = int(matrix.indices[at]), method.rational(matrix.data[at])
        result[j] = result.get(j, F(0))+value
    return {j: value for j, value in result.items() if value}


def register(partitions, field, enabled):
    """Keep the exact signed source B rows in the parent mixed-cone order."""
    bilateral, unilateral, ports = [], [], []
    q = list(map(method.rational, field['response']['q']))
    def component(row, index, stiffness, reference, positive, identity):
        value = {'id': identity, 'row': scalar_row(row['B'], index), 'stiffness': method.rational(stiffness),
                 'reference': method.rational(reference), 'kind': row['kind'], 'positive': positive}
        method.require(value['stiffness'] > 0 and (not positive or value['reference'] >= 0),
                       'positive source law and conjugate reference domain required')
        (unilateral if positive else bilateral).append(value)
        return identity
    for row, force in zip(partitions['groups'], field['response']['connector_local_force_n'], strict=True):
        method.require(len(force) == 3 and np.isfinite(force).all() and row['ka'] >= 0 and row['kl'] > 0
                       and row['clearance'] >= 0, 'complete finite original vector law required')
        ids = [None, None, None]
        if row['ka']:
            ids[0] = component(row, 0, row['ka'], force[0], row['tension_only'], row['id']+'/axial')
        else:
            method.require(force[0] == 0., 'axial-off source cannot carry a dual force')
        for i in (1, 2):
            ids[i] = component(row, i, row['kl'], force[i], False, row['id']+f'/lateral-{i}')
        ports.append({'descriptor': row, 'ids': ids, 'type': 'vector'})
    for row, force in zip(partitions['contacts'], field['response']['normal_contact_force_n'], strict=True):
        ports.append({'descriptor': row, 'ids': [component(row, 0, row['stiffness'], force, True, row['id'])], 'type': 'normal'})
    for row in partitions['tangents']:
        if row['id'] in enabled:
            reference = method.rational(row['stiffness'])*core.action([scalar_row(row['B'], 0)], q)[0]
            ports.append({'descriptor': row, 'ids': [component(row, 0, row['stiffness'], reference, False, row['id'])], 'type': 'tangent'})
    components = bilateral+unilateral
    lookup = {row['id']: i for i, row in enumerate(components)}
    method.require(len(lookup) == len(components), 'unique source scalar identities required')
    for port in ports:
        port['columns'] = [lookup[identity] if identity is not None else None for identity in port['ids']]
    return components, ports, len(bilateral)


def certified_blocks(blocks, certificates):
    result = []
    for block, certificate in zip(blocks, certificates, strict=True):
        method.require(all(block[key] == certificate[key] for key in ('body', 'family', 'global_coordinates'))
            and exact.matrix_digest(block['rows']) == certificate['exact_saved_matrix_sha256']
            and exact.matrix_digest(block['rigid']) == certificate['exact_registered_rigid_basis_sha256'],
            'own saved elastic block or rigid basis differs from certified comparator')
        symmetric, _ = core.symmetrize(block['rows'])
        datum = certificate['datum_local_coordinates']
        inverse = core.exact_inverse([block['rigid'][i] for i in datum])
        method.require(exact.matrix_digest(inverse) == certificate['exact_datum_inverse_sha256'], 'certified datum inverse drift')
        interpolation = core.product(block['rigid'], inverse)
        free = [i for i in range(len(block['rows'])) if i not in datum]
        lookup = {j: i for i, j in enumerate(free)}
        g = [{lookup[j]: value for j, value in symmetric[i].items() if j in lookup} for i in free]
        proof = certificate['quotient_positive_certificate']
        mu = F(proof['exact_smallest_eigenvalue_lower'])
        method.require(proof['positive_definite_proven'] is True and mu > 0
            and mu == F(proof['exact_verification_shift'])-F(proof['exact_factor_residual_inf'])
            and exact.matrix_digest(g) == proof['exact_matrix_sha256'], 'own certified positive G required')
        result.append({'body': block['body'], 'global': block['global_coordinates'], 'datum': datum, 'free': free,
                       'G': g, 'S_free': [interpolation[i] for i in free], 'mu': mu})
    return result


def elastic_action(q, blocks):
    result, energy = [F(0)]*len(q), F(0)
    for block in blocks:
        local = [q[i] for i in block['global']]
        rigid_datum = [local[i] for i in block['datum']]
        removed = core.action(block['S_free'], rigid_datum)
        z = [local[i]-value for i, value in zip(block['free'], removed, strict=True)]
        gz = core.action(block['G'], z)
        energy += method.upper(sum((a*b for a, b in zip(z, gz, strict=True)), F(0)))
        for i, value in zip(block['free'], gz, strict=True):
            result[block['global'][i]] = value
        reaction = core.action(core.transpose(block['S_free'], len(block['datum'])), gz)
        for i, value in zip(block['datum'], reaction, strict=True):
            result[block['global'][i]] = -value
    method.require(energy >= 0, 'certified comparator has nonnegative saved-pose energy')
    return result, energy


def residual_bound(applied, core_action, components, candidate, radius, blocks, maps, projected_load):
    bt = core.transpose([row['row'] for row in components], len(applied))
    forces = core.action(bt, candidate)
    center = [f-k-b for f, k, b in zip(applied, core_action, forces, strict=True)]
    uncertainty = [sum((abs(value)*radius[j] for j, value in row.items()), F(0)) for row in bt]
    projected = core.action(core.transpose(maps, len(projected_load)), center)
    d = core.transpose(core.product([row['row'] for row in components], maps), len(projected_load))
    expected = [p-value for p, value in zip(projected_load, core.action(d, candidate), strict=True)]
    method.require(projected == expected, 'comparator elastic residual does not have the certified rigid projection')
    records, total = [], F(0)
    for block in blocks:
        square = sum((abs(center[block['global'][i]])+uncertainty[block['global'][i]])**2 for i in block['free'])
        bound = method.upper(square/block['mu'])
        total += bound
        records.append({'body': block['body'], 'exact_free_residual_square_upper': str(square),
                        'exact_complementary_residual_square_upper': str(bound)})
    return total, records


def functional(rows, candidate, radius, stiffness, gap):
    columns = sorted({j for row in rows for j in row})
    if not columns:
        return method.functional([{} for _ in rows], [0], [0], [1], gap)
    lookup = {j: i for i, j in enumerate(columns)}
    local = [{lookup[j]: value for j, value in row.items()} for row in rows]
    return method.functional(local, [candidate[j] for j in columns], [radius[j] for j in columns],
                             [stiffness[j] for j in columns], gap)


def bearing_rows(pair, center):
    """Signed world force and free couple, retaining both Gauss stations."""
    center = list(map(method.rational, center))
    force, couple = [{} for _ in range(3)], [{} for _ in range(3)]
    for port in pair:
        descriptor = port['descriptor']
        arm = [method.rational(value)-origin for value, origin in zip(descriptor['point_xyz_mm'], center, strict=True)]
        for local_component, j in enumerate(port['columns']):
            if j is None:
                continue
            direction = [-method.rational(value) for value in descriptor['basis'][local_component]]
            cross = [arm[1]*direction[2]-arm[2]*direction[1], arm[2]*direction[0]-arm[0]*direction[2],
                     arm[0]*direction[1]-arm[1]*direction[0]]
            for i in range(3):
                force[i][j] = force[i].get(j, F(0))+direction[i]
                couple[i][j] = couple[i].get(j, F(0))+cross[i]
    return force, couple


def rear_leg(ports, body, candidate, radius, stiffness, gap):
    own = [port for port in ports if port['descriptor']['kind'] == 'floor_normal' and port['descriptor']['first'] == body]
    method.require(len(own) == len({port['descriptor']['id'] for port in own}) == 4
        and all(port['descriptor']['direction_xyz'] == [0., 0., 1.] for port in own),
        'four distinct own upward normal ports per credited leg required')
    enclosure = functional([{port['columns'][0]: F(1) for port in own}], candidate, radius, stiffness, gap)
    return {'body': body, 'normal_resultant': enclosure,
            'strict_positive_normal_resultant_certified': F(enclosure['exact_scalar_lower']) > 0}


def family_case(family, components, ports, candidate, radius, movement, twice_energy, residual_square, field, old_lands, inputs):
    alpha, beta, _ = method.family(F(family['alpha']), F(family['beta']))
    gaps = defaultdict(F)
    for port in ports:
        row, columns = port['descriptor'], port['columns']
        lower, upper = (F(1), F(1)) if row['kind'] in historical.FIXED_KINDS else (alpha, beta)
        if port['type'] == 'vector':
            if columns[0] is not None:
                j = columns[0]
                gaps[row['kind']] += method.upper(method.spring_gap([movement[j]], [candidate[j]], [radius[j]], row['ka'], lower, upper,
                                                       positive=row['tension_only']))
            js = columns[1:]
            gaps[row['kind']] += method.upper(method.spring_gap([movement[j] for j in js], [candidate[j] for j in js],
                [radius[j] for j in js], row['kl'], lower, upper, clearance=row['clearance']))
        else:
            j = columns[0]
            gaps[row['kind']] += method.upper(method.spring_gap([movement[j]], [candidate[j]], [radius[j]], row['stiffness'], lower, upper,
                                                   positive=port['type'] == 'normal'))
    core_gap = method.elastic_gap(twice_energy, residual_square, alpha, beta)
    gap = core_gap+sum(gaps.values(), F(0))
    stiffness = [row['stiffness']*(1 if row['kind'] in historical.FIXED_KINDS else beta) for row in components]
    worsts, captures, bearings = {}, {}, defaultdict(list)
    for port in ports:
        row = port['descriptor']
        columns = [j for j in port['columns'] if j is not None]
        enclosure = functional([{j: F(1)} for j in columns], candidate, radius, stiffness, gap)
        if row['kind'] not in worsts or enclosure['norm_upper'] > worsts[row['kind']]['local_constitutive_force_norm_upper_n']:
            worsts[row['kind']] = {'id': row['id'], 'local_constitutive_force_norm_upper_n': enclosure['norm_upper']}
        if row['kind'] == 'shaft_end_capture':
            captures[row['id']] = port
        if row['kind'] == 'common_shaft_bearing' and row['surface']['kind'] == 'wood':
            bearings[(row['axis_id'], row['surface_index'])].append(port)
    source_actions = {row['id']: row for row in field['common_shaft_bearing_actions']}
    shafts = {row['axis_id']: row for row in field['source_inputs']['shafts']}
    wood = []
    for (axis, surface), pair in sorted(bearings.items()):
        old_ports = [{'row': port['descriptor'], 'force': np.asarray([float(components[j]['reference']) if j is not None else 0.
                      for j in port['columns']]), 'source_action': source_actions[port['descriptor']['id']]} for port in pair]
        checked = historical.wood_surface(pair[0]['descriptor'], shafts[axis], old_ports, 0., 1.)
        center = list(map(method.rational, checked['moment_reference_xyz_mm']))
        force, couple = bearing_rows(pair, center)
        wood.append({'axis_id': axis, 'surface_index': surface, 'host': pair[0]['descriptor']['surface']['host'],
                     'reference_point_xyz_mm': list(map(str, center)),
                     'force': functional(force, candidate, radius, stiffness, gap),
                     'couple': functional(couple, candidate, radius, stiffness, gap)})
    lands = []
    for old in old_lands:
        port = captures[old['capture_id']]
        row, j = port['descriptor'], port['columns'][0]
        method.require(row['axis_id'] == old['axis_id'] and row['second'] == old['host']
                       and old['least_catalog_profile_area_mm2'] > 0, 'own catalog wood-land/capture identity required')
        enclosure = functional([{j: method.rational(value)} for value in row['direction_xyz']], candidate, radius, stiffness, gap)
        index = F(enclosure['exact_norm_upper'])/(method.rational(old['least_catalog_profile_area_mm2'])*method.rational(inputs['wood_land_reference_mpa']))
        lands.append({key: old[key] for key in ('axis_id', 'capture_id', 'host', 'least_catalog_profile_area_mm2')} |
                     {'exact_force_upper_n': enclosure['exact_norm_upper'], 'force_upper_n': enclosure['norm_upper'],
                      'exact_mean_pressure_reference_upper_index': str(index), 'mean_pressure_reference_upper_index': float(index)})
    legs = [rear_leg(ports, body, candidate, radius, stiffness, gap) for body in ['lumber_leg_left', 'lumber_leg_right']]
    method.require(len(wood) == 120 and len(lands) == 112 and len(ports) == 2324, 'complete own reaction/reference coverage required')
    return family | {'exact_core_Fenchel_gap_upper_nmm': str(core_gap),
        'exact_spring_Fenchel_gap_upper_by_kind_nmm': {kind: str(value) for kind, value in gaps.items()},
        'exact_total_Fenchel_gap_upper_nmm': str(gap), 'total_Fenchel_gap_upper_nmm': float(gap),
        'spring_port_enclosures_count': len(ports), 'worst_local_force_enclosure_by_kind': worsts,
        'wood_bearing_enclosures': wood, 'wood_land_mean_reference_enclosures': lands,
        'wood_land_upper_index_above_one_count': sum(F(row['exact_mean_pressure_reference_upper_index']) > 1 for row in lands),
        'worst_wood_land_upper_index': max(lands, key=lambda row: F(row['exact_mean_pressure_reference_upper_index'])),
        'credited_rear_leg_normal_enclosures': legs,
        'physical_stiffness_or_contact_or_complete_resistance_qualified': False}


def sources(pins, inputs):
    from scipy.optimize._highspy import _core
    method.require(current.sha(OWN) == LOADED_SHA and current.sha(method.OWN) == method.LOADED_SHA,
                   'loaded original-load bound source changed')
    method.require({key: importlib.metadata.version(key) for key in inputs['runtime_versions']} == inputs['runtime_versions'],
                   'declared static-selection runtime required')
    version = '.'.join(str(getattr(_core, 'HIGHS_VERSION_'+part)) for part in ('MAJOR', 'MINOR', 'PATCH'))
    method.require(version == inputs['highs_version'], 'declared static LP runtime required')
    model.verify_execution_sources(pins)


def run():
    own_input = current.ref(INPUT)
    inputs = read_exact(own_input)
    validate(inputs)
    parent = read_exact(inputs['core_certificate'])
    parent_inputs = read_exact(parent['inputs'])
    core_audit.validate(parent_inputs)
    prior = read_exact(parent_inputs['recession_certificate'])
    old = read_exact(inputs['historical_area_reference'])
    method.require(parent['constructed_comparator_core_PSD_and_exact_registered_kernel_proven'] is True
        and parent['literal_saved_symmetric_core_hypothesis_proven'] is False and parent['all_sources_unchanged'] is True
        and old['bounds_apply_to_original_exact_loads'] is False and old['all_sources_unchanged'] is True,
        'certified distinct comparator and immutable area-only historical intake required')
    with patch.object(current, 'read', read_exact):
        cases, pins = recession.intake_source.intake()
    frozen = current.load('bridge').frozen()
    partition = model.component.load(recession.preflight.PARTITION, 'current_original_load_partition')
    refs = [own_input, inputs['method_helper'], inputs['core_certificate'], inputs['historical_area_reference'],
            parent['inputs'], parent_inputs['recession_certificate'], *inputs['execution_sources'], current.ref(OWN),
            current.ref(current.ROOT/'tests/test_eoere_original_load_bounds.py'), current.ref(current.ROOT/'tests/test_eoere_original_load_audit.py')]
    pins = current.join(pins, parent['source_sha256'], old['source_sha256'], partition.source_pins(),
                        {ref['path']: ref['sha256'] for ref in refs})
    sources(pins, inputs)
    results, common_ids, blocks = [], None, None
    for (binding, field, _), old_core, old_static, old_area in zip(cases, parent['cases'], prior['cases'], old['cases'], strict=True):
        imported = recession.import_case(binding, field, frozen, partition)
        method.require(imported['binding'] == old_static['binding'] == old_area['binding']
            and all(old_core[key] == binding[key] for key in ('case_id', 'state_id', 'field')),
            'six own original case bindings required')
        matrix, maps, owners, bodies, fingerprint = core_audit.original_core(field, imported, frozen)
        method.require(fingerprint == parent['shared_core_registration_sha256'] == old_core['own_core_registration_sha256'],
                       'own certified comparator K/R/ownership required')
        manifest = read_exact(field['operator_bundle']['manifest'])
        with model.read_array_file(field['operator_bundle']['arrays']) as archive:
            bank = {key: archive[key] for key in archive.files}
        method.require(set(bank) == set(manifest['array_metadata'])
            and all(frozen.bundle._array_record(bank[key]) == meta for key, meta in manifest['array_metadata'].items()),
            'own exact full original port/load bank required')
        partitions = {name: [{**row['descriptor'], 'B': frozen.bundle._get_csr(bank, row['B'])} for row in manifest['partitions'][name]]
                      for name in ('groups', 'contacts', 'tangents')}
        contact = recession.preflight.current_contacts(manifest, field)
        components, ports, bilateral = register(partitions, field, set(contact['enabled_floor_tangent_ids']))
        ids = [row['id'] for row in components]
        method.require(bilateral == 968 and len(ids) == 2872 and len(ports) == 2324
            and ids == prior['shared_constraint_identities'] == imported['constraint_identities'], 'complete mixed-cone source registration required')
        d = core.transpose(core.product([row['row'] for row in components], maps), 800)
        method.require(exact.matrix_digest(d) == imported['exact_constraint_matrix_sha256']
            and all(imported[key] == old_static[key] for key in ('exact_constraint_matrix_sha256', 'exact_rigid_load_sha256',
                'exact_registered_rigid_basis_sha256', 'original_applied_binary64_sha256')), 'unchanged original-load rigid projection required')
        if blocks is None:
            blocks = certified_blocks(core_audit.owner_blocks(matrix, maps, owners, bodies), parent['body_certificates'])
            common_ids = ids
        method.require(ids == common_ids, 'shared scalar registration drift')
        q = list(map(method.rational, field['response']['q']))
        applied = list(map(method.rational, bank[manifest['applied_key']]))
        core_force, twice_energy = elastic_action(q, blocks)
        chosen = method.nearby_witness(d, len(ids), bilateral, imported['load'], [row['reference'] for row in components],
            [row['stiffness'] for row in components], prior['shared_minor_columns'], prior['shared_rank_certificate'],
            F(inputs['minimum_auxiliary_weight_n']))
        candidate = list(map(method.rational, chosen['candidate_auxiliary_weights']))
        radius = chosen.pop('component_correction_radius')
        residual_square, body_bounds = residual_bound(applied, core_force, components, candidate, radius, blocks, maps, imported['load'])
        movement = core.action([row['row'] for row in components], q)
        families = [family_case(family, components, ports, candidate, radius, movement, twice_energy, residual_square,
                               field, old_area['families'][0]['wood_land_mean_reference_enclosures'], inputs)
                    for family in inputs['stiffness_families']]
        results.append({'binding': imported['binding'], 'operator_bundle': imported['operator_bundle'],
            'exact_original_rigid_load_sha256': imported['exact_rigid_load_sha256'],
            'original_applied_binary64_sha256': imported['original_applied_binary64_sha256'],
            'exact_constraint_matrix_sha256': imported['exact_constraint_matrix_sha256'],
            **chosen, 'exact_saved_comparator_twice_energy_upper_nmm': str(twice_energy),
            'exact_elastic_residual_complementary_square_upper_nmm': str(residual_square),
            'body_residual_enclosures': body_bounds, 'families': families})
        print({'case_id': binding['case_id'], 'control_gap_upper_nmm': families[0]['total_Fenchel_gap_upper_nmm']}, flush=True)
    sources(pins, inputs)
    return {'schema': 'eoere_current_original_load_bounds/v1', 'status': 'EXACT_ORIGINAL_LOAD_COMPARATOR_REACTION_BOUNDS_COMPLETE',
        'inputs': own_input, 'source_sha256': pins, 'all_sources_unchanged': True,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
        'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False, 'case_count': len(results), 'cases': results,
        'scalar_component_identities': common_ids, 'original_load_is_unchanged': True,
        'bounds_apply_to_original_exact_loads_for_certified_comparator_family': True,
        'bounds_apply_to_literal_saved_K_or_physical_parts': False, 'contact_switches_permitted': True,
        'new_frame_response_or_native_FEA_or_CAD_run': False, 'new_equilibrium_reactions_predicted': False,
        'physical_demand_bounds_established': False, 'complete_joint_or_cleat_or_finished_member_resistance': None,
        'actual_observations': None, 'structural_acceptance': False, 'runtime_versions': inputs['runtime_versions'],
        'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(current.ref(args.out))


if __name__ == '__main__':
    main()
