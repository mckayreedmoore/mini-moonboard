"""Limit every fixed-gap rigid-kernel projection using two saved load witnesses.

The pressure embedding uses the existing disjoint material supports. Its dual
norm bounds the full continuous metric, not a centroid substitute for it.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PRIOR = {'path': 'scripts/eoere_mixed_shaft_projection_limit.py',
         'sha256': '9a8ced955420f2c092ffc0724847440a9d0413e493ebefa679fa8a2f3610a64e'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def prior_method(pins):
    data = (ROOT/PRIOR['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == PRIOR['sha256']
            and pins.get(PRIOR['path'], PRIOR['sha256']) == PRIOR['sha256'], 'frozen projection arithmetic changed')
    pins[PRIOR['path']] = PRIOR['sha256']
    module = ModuleType('_eoere_verified_global_projection_prior')
    module.__file__ = str(ROOT/PRIOR['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - verified frozen buffer
    return module


def annihilator_floor(difference, coefficients, stiffness, selected, correction_sum):
    """Bound a same-load witness difference; balance is certified separately.

    Continuous columns represent constant pressure on disjoint supports,
    with k_aux=kappa*area. This is their dual density norm. Every projected
    functional uses its full continuous-area metric in the Cauchy theorem.
    """
    difference, coefficients, stiffness = [list(map(F, values)) for values in (difference, coefficients, stiffness)]
    n, selected, correction_sum = len(difference), set(selected), F(correction_sum)
    require(n > 0 and len(coefficients) == len(stiffness) == n and min(stiffness) > 0 and correction_sum >= 0,
            'complete positive metric and nonnegative correction sum required')
    require(all(type(j) is int and 0 <= j < n for j in selected), 'bounded selected scalar indices required')
    work = sum((a*b for a, b in zip(coefficients, difference, strict=True)), F(0))
    work_error = correction_sum*sum((abs(coefficients[j]) for j in selected), F(0))
    norm_upper = sum(((abs(value)+(correction_sum if j in selected else 0))**2/stiffness[j]
                      for j, value in enumerate(difference)), F(0))
    require(norm_upper > 0, 'nonzero witness-difference norm bound required')
    work_lower = max(F(0), abs(work)-work_error)
    return {'exact_nominal_difference_action': str(work), 'exact_action_box_radius': str(work_error),
            'exact_nonnegative_action_lower': str(work_lower), 'exact_dual_density_norm_square_upper': str(norm_upper),
            'exact_full_metric_lower_for_every_registered_kernel_projection': str(work_lower**2/norm_upper)}


def run(reference):
    pins = {}; prior = prior_method(pins); boot = prior.bootstrap(pins); base = boot.producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_mixed_global_projection_limit_inputs/v1'
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
            and inputs['extra_grid'] is False and inputs['axis_id'] == 'eoere_bolt_067'
            and inputs['case_id'] == 'a12-forward' and inputs['uniform_reference_divisor'] == '5'
            and inputs['actual_observations'] is None and inputs['structural_acceptance'] is False,
            'retained design and fixed working comparison required')
    for row in inputs['execution_sources']:
        base.captured(row, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing global-limit helper required')
    parent = json.loads(base.captured(inputs['prior_projection_result'], pins))
    require(parent['schema'] == 'eoere_mixed_shaft_projection_limit/v1'
            and parent['continuous_law_core_loads_gap_candidate_box_functional_or_support_changed'] is False,
            'preserved unchanged-certificate shaft limit required')
    for path, digest in parent['source_sha256'].items():
        base.captured({'path': path, 'sha256': digest}, pins)
    parent_inputs = json.loads(base.captured(parent['inputs'], pins))
    source = json.loads(base.captured(parent_inputs['reaction_result'], pins))
    require(source['all_six_exact_original_load_dual_bounds_proven'] is True
            and source['support_regions_are_auxiliary_pressure_fields_not_model_energy_cells'] is True,
            'completed disjoint material-support pressure certificate required')
    source_inputs = json.loads(base.captured(source['inputs'], pins)); runtime = boot.check_runtime(source_inputs['runtime'])
    require(runtime == parent['runtime'], 'same exact algebra runtime required')
    h = base.prepare(source_inputs, pins)
    original = json.loads(base.captured(source_inputs['original_bounds'], pins))
    mixed = json.loads(base.captured(source_inputs['mixed_result'], pins))
    old = json.loads(base.captured(h.prior_inputs['recession_result'], pins))
    bound, = [c for c in source['cases'] if c['binding']['case_id'] == inputs['case_id']]
    previous, = [c for c in original['cases'] if c['binding'] == bound['binding']]
    require(parent['binding'] == mixed['refined_control']['binding'] == bound['binding'], 'same frozen original load required')
    field = json.loads(base.captured(bound['binding']['field'], pins)); pointer = field['operator_bundle']
    require(pointer == previous['operator_bundle'] == bound['operator_bundle'] == parent['operator_bundle'], 'same source operators required')
    manifest = json.loads(base.captured(pointer['manifest'], pins)); data = base.captured(pointer['arrays'], pins)
    with np.load(io.BytesIO(data), allow_pickle=False) as arrays:
        maps, owners, bodies, dimension = h.reader.rigid_basis(manifest['coordinate_map'], arrays[manifest['rigid_modes_key']])
        parts = h.transfer.partitions(manifest, arrays)
        enabled = {row['id'] for row in parts['tangents']} & set(old['shared_constraint_identities'])
        components, ports, bilateral = h.audit.register(parts, field, enabled)
        require(dimension == 800 and len(bodies) == 150 and len(maps) == len(owners) == 9350
                and bilateral == 968 and len(ports) == 2324
                and [c['id'] for c in components] == original['scalar_component_identities'], 'complete source registration required')
        rows = h.core.product([c['row'] for c in components], maps)
        load = h.core.action(h.core.transpose(maps, dimension), list(map(F, arrays[manifest['applied_key']])))
    load_digest = hashlib.sha256(json.dumps(list(map(str, load)), separators=(',', ':')).encode()).hexdigest()
    require(load_digest == bound['exact_original_rigid_load_sha256'] == previous['exact_original_rigid_load_sha256'],
            'same exact original rigid load required')
    stiffness = [c['stiffness'] for c in components]; replaced = set()
    for record in source['shared_material_support_records']:
        j = record['column']
        require(type(j) is int and 0 <= j < len(components) and j not in replaced
                and record['id'] == components[j]['id'] and components[j]['kind'] == 'flange_contact', 'own unique pressure-support column required')
        rows[j] = {int(key): F(value) for key, value in record['exact_rigid_compression_row'].items()}
        stiffness[j] = F(record['exact_area_mm2'])*F(record['exact_density_n_mm3']); replaced.add(j)
    require(len(replaced) == 352 and replaced == {j for j, c in enumerate(components) if c['kind'] == 'flange_contact'},
            'all and only existing disjoint material supports required')
    matrix = h.core.transpose(rows, dimension)
    require(h.exact.matrix_digest(matrix) == source['shared_exact_new_rigid_matrix_sha256'], 'same complete continuous rigid matrix required')
    selected, rank = old['shared_minor_columns'], source['shared_perturbed_rank_certificate']
    candidates = [previous['candidate_auxiliary_weights'], mixed['refined_control']['candidate_auxiliary_weights']]
    certificates = [h.exact.certify(matrix, len(components), bilateral, load, candidate, selected, rank) for candidate in candidates]
    require(certificates[0] == bound['load_certificate'], 'unchanged first corrected dual and its box required')
    correction = sum((F(c['exact_selected_correction_inf_upper']) for c in certificates), F(0))
    ids = [c['id'] for c in components]
    coefficients = [F(mixed['refined_control']['source_linear_coefficients'].get(identity, '0')) for identity in ids]
    require(all(not coefficients[j] for j in replaced), 'original functional must remain the frozen bearing-only test')
    difference = [F(a)-F(b) for a, b in zip(*candidates, strict=True)]
    obstruction = annihilator_floor(difference, coefficients, stiffness, selected, correction)
    frozen = bound['bolt_067_original_lateral_necessary_interval']
    require(frozen == parent['original_necessary_interval'], 'same first-candidate center, box, gap, functional and support required')
    ceiling = prior.certificate_ceiling(frozen['exact_signed_center'], frozen['linear_functional_bound']['exact_dual_correction_norm_upper'],
        bound['exact_total_Fenchel_gap_upper_nmm'], obstruction['exact_full_metric_lower_for_every_registered_kernel_projection'],
        parent['exact_frozen_support_upper'], inputs['uniform_reference_divisor'])
    del ceiling['no_shaft_only_projection_can_certify_exceedance_with_this_fixed_certificate']
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_mixed_global_projection_limit/v1', 'inputs': reference, 'runtime': runtime, 'source_sha256': pins,
            'binding': bound['binding'], 'operator_bundle': pointer, 'exact_original_rigid_load_sha256': load_digest,
            'registered_rigid_rows_covered': dimension, 'continuous_uniform_pressure_supports': len(replaced),
            'exact_continuous_rigid_matrix_sha256': source['shared_exact_new_rigid_matrix_sha256'],
            'same_load_certificates': certificates, 'exact_correction_radius_sum': str(correction),
            'candidate_difference_nonzero_components': sum(v != 0 for v in difference),
            **obstruction, **ceiling, 'original_necessary_interval': frozen,
            'exact_fixed_gap_certificate_nmm': bound['exact_total_Fenchel_gap_upper_nmm'],
            'exact_frozen_support_upper': parent['exact_frozen_support_upper'],
            'global_annihilator_is_difference_of_two_certified_same_load_duals': True,
            'projection_metric_is_full_continuous_area_not_the_auxiliary_mean_metric': True,
            'no_registered_kernel_projection_can_certify_exceedance_with_this_fixed_certificate': F(ceiling['exact_necessary_lower_endpoint_ceiling']) < 1,
            'candidate2_used_only_as_annihilator_witness_not_a_replacement_for_candidate1': True,
            'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'continuous_law_core_loads_gap_candidate1_box_functional_or_support_changed': False,
            'new_solve_optimization_inverse_factorization_or_response': False,
            'actual_pass_failure_or_complete_resistance_established': False, 'physical_stiffness_demand_restraint_qualified': False,
            'panel_screw_exceedances_deferred': True, 'actual_observations': None, 'structural_acceptance': False, 'limits': inputs['limits']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); require(not args.out.exists(), 'preserve issued global-limit evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(),
                      'necessary_lower_endpoint_ceiling': result['necessary_lower_endpoint_ceiling']}))


if __name__ == '__main__':
    main()
