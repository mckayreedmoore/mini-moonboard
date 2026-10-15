"""Carry the frozen mixed-stack necessary test through comparator reactions.

Reuse the continuous support certificate and original-load reaction theorem.
An optional smaller auxiliary-force margin refines only the static dual proof;
it does not compute a new displacement or equilibrium reaction. The uniform
material divisor remains an engineering hypothesis, not an ASD conversion.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path

from scripts import eoere_mixed_continuous_bound as continuous
from scripts import eoere_original_load_audit as audit

method, current, model = audit.method, audit.current, audit.model
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/mixed-reaction-bound-inputs-v1.json'


def dot(a, b):
    return sum((x*y for x, y in zip(a, b, strict=True)), F(0))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def source_functional(shaft, descriptors, identities, arguments, multiplier, loads):
    """Exact binary port actions in the frozen decimal reference geometry.

    This adapter requires an exactly orthonormal common basis and collinear
    bearing points. It therefore needs no approximate basis identities or
    dropped axial terms. Decimal reference caps/intervals/multipliers remain
    as frozen; binary source positions/forces retain their exact values.
    """
    binary, decimal = method.rational, continuous.rational
    basis = [list(map(binary, row)) for row in shaft['basis']]
    origin = list(map(binary, shaft['point']))
    axis = basis[0]
    method.require(len(basis) == 3 and all(len(row) == 3 for row in basis)
        and [[dot(a, b) for b in basis] for a in basis] == [[F(i == j) for j in range(3)] for i in range(3)]
        and cross(basis[0], basis[1]) == basis[2], 'exact right-handed orthonormal common basis required')
    method.require(len(identities) == len(set(identities))
        and len(shaft['surfaces']) == len(arguments['surfaces']) == len(multiplier['surfaces']) == 3,
        'unique source identities and complete three-member multiplier required')
    lookup = {identity: i for i, identity in enumerate(identities)}
    own = [row for row in descriptors if row.get('axis_id') == shaft['axis_id']]
    method.require(len(own) == 6 and len({row['id'] for row in own}) == 6, 'six distinct own bearing ports required')
    coefficients, surface_rows = {}, []
    for i, (surface, reference, weight) in enumerate(zip(shaft['surfaces'], arguments['surfaces'], multiplier['surfaces'], strict=True)):
        method.require(reference['host'] == surface['host'] and reference['kind'] == surface['kind']
            and reference['interval'] == surface['interval_mm'], 'own unchanged reference interval and host required')
        low, high = map(decimal, reference['interval'])
        middle = (low+high)/2
        pair = [row for row in own if row['surface_index'] == i]
        method.require(low < high and len(pair) == 2 and {row['quad_index'] for row in pair} == {0, 1},
                       'complete two-Gauss own surface required')
        forces, firsts = [{}, {}], [{}, {}]
        for row in pair:
            method.require(row['kind'] == 'common_shaft_bearing' and row['first'] == shaft['body']
                and row['second'] == surface['host'] and row['surface'] == surface and row['ka'] == 0
                and [list(map(binary, b)) for b in row['basis']] == basis,
                'same signed common-shaft, host and axial-off source law required')
            delta = [binary(p)-o for p, o in zip(row['point_xyz_mm'], origin, strict=True)]
            station = dot(axis, delta)
            method.require(delta == [station*a for a in axis] and low <= station <= high,
                           'own collinear bearing point inside reference interval required')
            for k in range(2):
                identity = row['id']+f'/lateral-{k+1}'
                method.require(identity in lookup, 'bearing scalar identity missing from certified source order')
                j = lookup[identity]
                # The source constitutive force on the shaft is -basis.T*r.
                forces[k][j], firsts[k][j] = F(-1), -(station-middle)
                coefficient = -decimal(weight['force'][k])-(station-middle)*decimal(weight['first_moment'][k])
                if coefficient:
                    coefficients[j] = coefficient
        surface_rows.append({'force': forces, 'first_moment': firsts})
    method.require(len(loads) == len(shaft['metal_roles'])
        and {row['id'] for row in loads} == {'physical-bolt-metal/'+row['id'] for row in shaft['metal_roles']}
        and all(row['body'] == shaft['body'] for row in loads), 'all and only own metal load roles required')
    points = []
    for load in loads:
        delta = [binary(p)-o for p, o in zip(load['point_xyz_mm'], origin, strict=True)]
        station = dot(axis, delta)
        force = list(map(binary, load['force_xyz_n']))
        arm = [value-station*a for value, a in zip(delta, axis, strict=True)]
        couple = [a+binary(b) for a, b in zip(cross(arm, force), load.get('moment_xyz_nmm', [0, 0, 0]), strict=True)]
        points.append({'s': station, 'force': [dot(b, force) for b in basis[1:]],
                       'couple': [dot(b, couple) for b in basis[1:]]})
    constant = -sum((dot(list(map(decimal, cut['nu'])), continuous.point_moment(points, cut['station'], cut['include']))
                     for cut in multiplier['cuts']), F(0))
    return coefficients, constant, surface_rows, points


def necessary_interval(coefficients, constant, candidate, radius, stiffness, gap, support, divisors):
    """Enclose the scalar necessary ratio, never an upper resistance bound."""
    support, constant = F(support), F(constant)
    method.require(support > 0 and divisors and all(F(value) > 0 for value in divisors), 'positive support and divisors required')
    bound = audit.functional([coefficients], candidate, radius, stiffness, gap)
    center = F(bound['exact_candidate_center'][0])+constant
    error = F(bound['exact_dual_correction_norm_upper'])+F(bound['exact_equilibrium_change_norm_upper'])
    low, high = max(F(0), abs(center)-error), abs(center)+error
    scenarios = []
    for divisor in divisors:
        lower, upper = F(divisor)*low/support, F(divisor)*high/support
        scenarios.append({'uniform_reference_divisor': str(F(divisor)), 'exact_necessary_ratio_lower': str(lower),
            'exact_necessary_ratio_upper': str(upper), 'necessary_ratio_lower': float(lower), 'necessary_ratio_upper': float(upper),
            'every_equilibrium_fails_this_lateral_reference_hypothesis': lower > 1,
            'passing_field_or_complete_resistance_established': False})
    return {'linear_functional_bound': bound, 'exact_fixed_point_work': str(constant), 'exact_signed_center': str(center),
            'exact_signed_lower_upper': [str(center-error), str(center+error)], 'scenarios': scenarios}


def gap_only(family, components, ports, candidate, radius, movement, twice_energy, residual_square):
    """Reuse the frozen scalar/radial proofs without regenerating port bounds."""
    alpha, beta, _ = method.family(F(family['alpha']), F(family['beta']))
    gaps = defaultdict(F)
    for port in ports:
        row, columns = port['descriptor'], port['columns']
        lower, upper = (F(1), F(1)) if row['kind'] in audit.historical.FIXED_KINDS else (alpha, beta)
        if port['type'] == 'vector':
            if columns[0] is not None:
                j = columns[0]
                gaps[row['kind']] += method.upper(method.spring_gap([movement[j]], [candidate[j]], [radius[j]], row['ka'],
                    lower, upper, positive=row['tension_only']))
            js = columns[1:]
            gaps[row['kind']] += method.upper(method.spring_gap([movement[j] for j in js], [candidate[j] for j in js],
                [radius[j] for j in js], row['kl'], lower, upper, clearance=row['clearance']))
        else:
            j = columns[0]
            gaps[row['kind']] += method.upper(method.spring_gap([movement[j]], [candidate[j]], [radius[j]], row['stiffness'],
                lower, upper, positive=port['type'] == 'normal'))
    core_gap = method.elastic_gap(twice_energy, residual_square, alpha, beta)
    return {'exact_core_Fenchel_gap_upper_nmm': str(core_gap),
            'exact_spring_Fenchel_gap_upper_by_kind_nmm': {key: str(value) for key, value in sorted(gaps.items())},
            'exact_total_Fenchel_gap_upper_nmm': str(core_gap+sum(gaps.values(), F(0)))}


def validate(inputs):
    method.require(inputs['schema'] == 'eoere_current_mixed_reaction_bound_inputs/v1'
        and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
        and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
        and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66 and inputs['extra_grid'] is False
        and inputs['axis_id'] == 'eoere_bolt_067' and inputs['refined_case_id'] == 'a12-forward'
        and inputs['minimum_auxiliary_weight_n'] == '1/100000000' and inputs['uniform_reference_divisors'] == ['16/5', '4', '5']
        and inputs['physical_demand_bounds_established'] is False and inputs['structural_acceptance'] is False
        and inputs['actual_observations'] is None, 'unchanged scope and predeclared auxiliary refinement required')


def source_ports(field, manifest, frozen):
    with model.read_array_file(field['operator_bundle']['arrays']) as archive:
        bank = {key: archive[key] for key in archive.files}
    method.require(manifest['arrays'] == field['operator_bundle']['arrays'] and set(bank) == set(manifest['array_metadata'])
        and all(frozen.bundle._array_record(bank[key]) == meta for key, meta in manifest['array_metadata'].items()),
        'exact original full port and numeric bank required')
    partitions = {name: [{**row['descriptor'], 'B': frozen.bundle._get_csr(bank, row['B'])} for row in manifest['partitions'][name]]
                  for name in ('groups', 'contacts', 'tangents')}
    contact = audit.recession.preflight.current_contacts(manifest, field)
    components, ports, bilateral = audit.register(partitions, field, set(contact['enabled_floor_tangent_ids']))
    return bank, components, ports, bilateral


def run():
    own_input = current.ref(INPUT)
    inputs = continuous.read_exact(own_input)
    validate(inputs)
    parent = continuous.read_exact(inputs['original_load_bounds'])
    old = continuous.read_exact(inputs['continuous_certificate'])
    parent_inputs = continuous.read_exact(parent['inputs'])
    audit.validate(parent_inputs)
    core = continuous.read_exact(parent_inputs['core_certificate'])
    core_inputs = continuous.read_exact(core['inputs'])
    prior = continuous.read_exact(core_inputs['recession_certificate'])
    method.require(parent['schema'] == 'eoere_current_original_load_bounds/v1' and parent['all_sources_unchanged'] is True
        and parent['bounds_apply_to_original_exact_loads_for_certified_comparator_family'] is True
        and parent['bounds_apply_to_literal_saved_K_or_physical_parts'] is False
        and core['constructed_comparator_core_PSD_and_exact_registered_kernel_proven'] is True
        and old['schema'] == 'eoere_current_mixed_continuous_bearing_bending_bound/v1' and old['all_sources_unchanged'] is True
        and old['axis_id'] == inputs['axis_id'] and old['case_id'] == inputs['refined_case_id'],
        'completed own original-load comparator and continuous support certificates required')
    method.require(continuous.canonical_sha(old['source_arguments']) == old['source_arguments_sha256'],
                   'frozen decimal argument digest differs')
    frozen = current.load('bridge').frozen()
    helper = model.component.load(audit.recession.preflight.PARTITION, 'current_mixed_reaction_partition')
    refs = [own_input, inputs['original_load_bounds'], inputs['continuous_certificate'], parent['inputs'],
            parent_inputs['core_certificate'], core['inputs'], core_inputs['recession_certificate'], current.ref(OWN),
            current.ref(current.ROOT/'tests/test_eoere_mixed_reaction_bound.py')]
    pins = current.join(parent['source_sha256'], old['source_sha256'], helper.source_pins(), {r['path']: r['sha256'] for r in refs})
    audit.sources(pins, parent_inputs)
    method.require(current.sha(OWN) == LOADED_SHA, 'loaded mapping producer changed')
    identities = parent['scalar_component_identities']
    support = F(old['exact_continuous_certificate']['exact_total_support_lower_upper'][1])
    selected = set(prior['shared_minor_columns'])
    results, refined = [], None
    for case in parent['cases']:
        binding = case['binding']
        field = continuous.read_exact(binding['field'])
        manifest = continuous.read_exact(field['operator_bundle']['manifest'])
        bank, components, ports, bilateral = source_ports(field, manifest, frozen)
        method.require([row['id'] for row in components] == identities == prior['shared_constraint_identities']
            and bilateral == 968 and len(components) == 2872 and len(ports) == 2324
            and field['operator_bundle'] == case['operator_bundle'], 'same complete source scalar order and ports required')
        shaft = next(row for row in field['source_inputs']['shafts'] if row['axis_id'] == inputs['axis_id'])
        descriptors = [port['descriptor'] for port in ports if port['type'] == 'vector']
        loads = [row for row in field['body_applied_loads'] if row['body'] == shaft['body']]
        row, constant, surfaces, points = source_functional(shaft, descriptors, identities, old['source_arguments'], old['candidate_multiplier'], loads)
        # Shaft captures are exactly axial and collinear; no transverse action
        # is omitted from the continuous lateral reference.
        captures = [port['descriptor'] for port in ports if port['descriptor']['kind'] == 'shaft_end_capture'
                    and port['descriptor']['axis_id'] == inputs['axis_id']]
        method.require(len(captures) == 2 and all(cross(list(map(method.rational, c['direction_xyz'])),
            list(map(method.rational, shaft['basis'][0]))) == [0, 0, 0]
            and cross([method.rational(p)-method.rational(o) for p, o in zip(c['point_xyz_mm'], shaft['point'], strict=True)],
                list(map(method.rational, shaft['basis'][0]))) == [0, 0, 0] for c in captures), 'two purely axial collinear captures required')
        saved = [component['reference'] for component in components]
        saved_work = dot([row[j] for j in row], [saved[j] for j in row])+constant
        candidate = list(map(method.rational, case['candidate_auxiliary_weights']))
        correction = F(case['load_certificate']['exact_selected_correction_inf_upper'])
        radius = [correction if j in selected else F(0) for j in range(len(identities))]
        families = []
        for family in case['families']:
            stiffness = [component['stiffness']*(1 if component['kind'] in audit.historical.FIXED_KINDS else F(family['beta']))
                         for component in components]
            families.append({'id': family['id'], **necessary_interval(row, constant, candidate, radius, stiffness,
                F(family['exact_total_Fenchel_gap_upper_nmm']), support, inputs['uniform_reference_divisors'])})
        results.append({'binding': binding, 'exact_saved_source_work': str(saved_work), 'families': families})
        if binding['case_id'] != inputs['refined_case_id']:
            continue
        difference = saved_work-F(old['exact_continuous_certificate']['exact_virtual_work'])
        method.require(abs(difference) < F(1, 10**10), 'binary source reconstruction differs materially from frozen decimal actions')
        imported = audit.recession.import_case(binding, field, frozen, helper)
        method.require(imported['constraint_identities'] == identities and all(imported[key] == case[other] for key, other in [
            ('exact_constraint_matrix_sha256', 'exact_constraint_matrix_sha256'),
            ('exact_rigid_load_sha256', 'exact_original_rigid_load_sha256'),
            ('original_applied_binary64_sha256', 'original_applied_binary64_sha256')]), 'unchanged exact original load and constraint matrix required')
        matrix, maps, owners, bodies, fingerprint = audit.core_audit.original_core(field, imported, frozen)
        method.require(fingerprint == core['shared_core_registration_sha256'], 'same certified comparator registration required')
        blocks = audit.certified_blocks(audit.core_audit.owner_blocks(matrix, maps, owners, bodies), core['body_certificates'])
        chosen = method.nearby_witness(imported['rows'], len(identities), bilateral, imported['load'], saved,
            [component['stiffness'] for component in components], prior['shared_minor_columns'], prior['shared_rank_certificate'],
            F(inputs['minimum_auxiliary_weight_n']))
        fresh = list(map(method.rational, chosen['candidate_auxiliary_weights']))
        fresh_radius = chosen.pop('component_correction_radius')
        q = list(map(method.rational, field['response']['q']))
        applied = list(map(method.rational, bank[manifest['applied_key']]))
        action, energy = audit.elastic_action(q, blocks)
        residual, body_bounds = audit.residual_bound(applied, action, components, fresh, fresh_radius, blocks, maps, imported['load'])
        movement = audit.core.action([component['row'] for component in components], q)
        control = parent_inputs['stiffness_families'][0]
        gap = gap_only(control, components, ports, fresh, fresh_radius, movement, energy, residual)
        bound = necessary_interval(row, constant, fresh, fresh_radius, [component['stiffness'] for component in components],
                                   F(gap['exact_total_Fenchel_gap_upper_nmm']), support, inputs['uniform_reference_divisors'])
        refined = {'binding': binding, **chosen, 'exact_saved_comparator_twice_energy_upper_nmm': str(energy),
            'exact_elastic_residual_complementary_square_upper_nmm': str(residual), 'body_residual_enclosures': body_bounds,
            'family_id': control['id'], **gap, **bound, 'exact_source_work_minus_old_decimal_work': str(difference),
            'source_linear_coefficients': {identities[j]: str(value) for j, value in sorted(row.items())},
            'source_surface_action_rows': [{name: [{identities[j]: str(v) for j, v in sorted(r.items())} for r in action_rows]
                                          for name, action_rows in surface.items()} for surface in surfaces],
            'source_point_actions': [{name: list(map(str, v)) if isinstance(v, list) else str(v) for name, v in point.items()} for point in points]}
    method.require(refined is not None and [case['binding']['case_id'] for case in results] == audit.recession.preflight.SEQUENCE,
                   'all six own cases and one predeclared refined case required')
    audit.sources(pins, parent_inputs)
    method.require(current.sha(OWN) == LOADED_SHA, 'loaded mapping producer changed')
    return {'schema': 'eoere_current_mixed_reaction_bound/v1', 'status': 'MIXED_NECESSARY_TEST_COMPARATOR_ENCLOSURES_COMPLETE',
        'inputs': own_input, 'source_sha256': pins, 'all_sources_unchanged': True,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'], 'current_bolt_count': 100,
        'current_screw_count': 66, 'extra_grid': False, 'axis_id': inputs['axis_id'], 'cases': results, 'refined_control': refined,
        'exact_frozen_continuous_support_upper': str(support), 'auxiliary_selection_is_not_a_response': True,
        'original_load_is_unchanged': True, 'new_frame_response_or_native_FEA_or_CAD_run': False,
        'bounds_apply_to_literal_saved_K_or_physical_parts': False, 'physical_demand_bounds_established': False,
        'physical_failure_established': False, 'complete_joint_or_cleat_or_finished_member_resistance': None,
        'panel_screw_exceedances_deferred': True, 'actual_observations': None, 'structural_acceptance': False,
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
