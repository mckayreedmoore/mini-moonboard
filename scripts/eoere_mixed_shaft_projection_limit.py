"""Bound the reach of a fixed-gap, shaft-only mixed-reaction certificate.

This is a limitation of one proof family, not a resistance pass or failure.
The null witness and all calculations are exact algebra on retained operators.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from fractions import Fraction as F
from math import isqrt
from pathlib import Path
from types import ModuleType

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BOOT = {'path': 'scripts/eoere_normal_patch_functionals.py',
        'sha256': '221bd5ff7313815cac7cc61825403187e32e95ab8c6fc9ba14f8a6b17c189d07'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bootstrap(pins):
    """Reuse the frozen loader and runtime gate from captured source bytes."""
    data = (ROOT/BOOT['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == BOOT['sha256']
            and pins.get(BOOT['path'], BOOT['sha256']) == BOOT['sha256'], 'frozen bootstrap changed')
    pins[BOOT['path']] = BOOT['sha256']
    module = ModuleType('_eoere_verified_projection_bootstrap')
    module.__file__ = str(ROOT/BOOT['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - verified frozen buffer
    return module


def metric_obstruction(rows, coefficients, stiffness, pivots):
    """One explicit 3-point null vector, checked against every shaft column."""
    rows = [list(map(F, row)) for row in rows]
    coefficients, stiffness = [list(map(F, values)) for values in (coefficients, stiffness)]
    require(len(rows) == len(coefficients) == len(stiffness) == 3
            and all(len(row) == 5 for row in rows) and min(stiffness) > 0,
            'three own reactions, all five shaft columns and positive metrics required')
    require(len(pivots) == 2 and len(set(pivots)) == 2
            and all(type(j) is int and 0 <= j < 5 for j in pivots), 'two distinct bounded pivot columns required')
    a, b = [[row[j] for row in rows] for j in pivots]
    z = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    require(any(z), 'nonzero null witness required')
    require(all(sum((row[j]*v for row, v in zip(rows, z, strict=True)), F(0)) == 0 for j in range(5)),
            'witness must annihilate every retained shaft column')
    work = sum((c*v for c, v in zip(coefficients, z, strict=True)), F(0))
    denominator = sum((v*v/k for v, k in zip(z, stiffness, strict=True)), F(0))
    require(work != 0, 'nonzero functional action required for a positive obstruction')
    return {'exact_null_witness': list(map(str, z)), 'exact_functional_action': str(work),
            'exact_inverse_metric_square': str(denominator),
            'exact_weighted_Gram_lower_for_every_shaft_projection': str(work*work/denominator)}


def certificate_ceiling(center, correction, gap, gram_lower, support, divisor):
    """Upper bound the lower endpoint produced by this fixed certificate family.

    At the same exact corrected dual r0 in the certified box, every shifted
    representation agrees. Thus |center_v|-box_v <= |center_0|+box_0.
    The unchanged formula radius is at least sqrt(2*fixed_gap*gram_lower).
    The fixed gap is the previously used UPPER certificate, not a lower bound
    on the physical or exact Fenchel gap. Changing that certificate is outside
    the quantified family.
    """
    center, correction, gap, gram_lower, support, divisor = map(F, (center, correction, gap, gram_lower, support, divisor))
    require(correction >= 0 and gap >= 0 and gram_lower > 0 and support > 0 and divisor > 0,
            'nonnegative box/gap and positive metric/support/divisor required')
    square, scale = 2*gap*gram_lower, 10**24
    radius_lower = F(isqrt(square.numerator*scale*scale//square.denominator), scale)
    ceiling = divisor*max(F(0), abs(center)+correction-radius_lower)/support
    return {'exact_formula_radius_lower': str(radius_lower),
            'exact_same_corrected_dual_work_absolute_upper': str(abs(center)+correction),
            'exact_necessary_lower_endpoint_ceiling': str(ceiling),
            'necessary_lower_endpoint_ceiling': float(ceiling),
            'no_shaft_only_projection_can_certify_exceedance_with_this_fixed_certificate': ceiling < 1}


def run(reference):
    pins = {}; boot = bootstrap(pins); base = boot.producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_mixed_shaft_projection_limit_inputs/v1'
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
            and inputs['extra_grid'] is False and inputs['axis_id'] == 'eoere_bolt_067'
            and inputs['case_id'] == 'a12-forward' and inputs['uniform_reference_divisor'] == '5'
            and inputs['actual_observations'] is None and inputs['structural_acceptance'] is False,
            'retained model and fixed working comparison required')
    for row in inputs['execution_sources']:
        base.captured(row, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing limit helper required')
    source = json.loads(base.captured(inputs['reaction_result'], pins))
    require(source['schema'] == 'eoere_continuous_normal_support_refinement/v1'
            and source['all_six_exact_original_load_dual_bounds_proven'] is True
            and source['continuous_normal_law_or_original_load_changed'] is False,
            'completed unchanged-law continuous certificate required')
    for path, digest in source['source_sha256'].items():
        base.captured({'path': path, 'sha256': digest}, pins)
    source_inputs = json.loads(base.captured(source['inputs'], pins))
    runtime = boot.check_runtime(source_inputs['runtime'])
    h = base.prepare(source_inputs, pins)
    mixed = json.loads(base.captured(source_inputs['mixed_result'], pins))
    previous = json.loads(base.captured(source_inputs['original_bounds'], pins))
    old = json.loads(base.captured(h.prior_inputs['recession_result'], pins))
    core = json.loads(base.captured(h.prior_inputs['core_result'], pins))
    require(core['constructed_comparator_core_PSD_and_exact_registered_kernel_proven'] is True,
            'certified exact registered kernel required')
    bound, = [c for c in source['cases'] if c['binding']['case_id'] == inputs['case_id']]
    prior, = [c for c in previous['cases'] if c['binding'] == bound['binding']]
    require(mixed['refined_control']['binding'] == bound['binding'], 'same mixed functional and original case required')
    field = json.loads(base.captured(bound['binding']['field'], pins)); pointer = field['operator_bundle']
    require(pointer == prior['operator_bundle'] == bound['operator_bundle'], 'same original operators required')
    manifest = json.loads(base.captured(pointer['manifest'], pins)); data = base.captured(pointer['arrays'], pins)
    with np.load(io.BytesIO(data), allow_pickle=False) as arrays:
        maps, owners, bodies, dimension = h.reader.rigid_basis(manifest['coordinate_map'], arrays[manifest['rigid_modes_key']])
        parts = h.transfer.partitions(manifest, arrays)
        enabled = {r['id'] for r in parts['tangents']} & set(old['shared_constraint_identities'])
        components, ports, bilateral = h.audit.register(parts, field, enabled)
        require(dimension == 800 and len(maps) == len(owners) == 9350 and bilateral == 968 and len(ports) == 2324
                and [c['id'] for c in components] == previous['scalar_component_identities'], 'complete original registration required')
        rows = h.core.product([c['row'] for c in components], maps)
        load = h.core.action(h.core.transpose(maps, dimension), list(map(F, arrays[manifest['applied_key']])))
    load_digest = hashlib.sha256(json.dumps(list(map(str, load)), separators=(',', ':')).encode()).hexdigest()
    require(load_digest == bound['exact_original_rigid_load_sha256'] == prior['exact_original_rigid_load_sha256'],
            'same exact original registered load required')
    body, = [b for b in bodies if b['body'] == 'shaft/'+inputs['axis_id']]
    require(body['source_mode_columns'] == [0, 1, 2, 4, 5], 'all five own retained shaft modes required')
    columns = list(range(body['first_rigid_column'], body['first_rigid_column']+5))
    require(all(body['body'] not in (p['first'], p['second']) for p in field['source_inputs']['flange_shared_face_patches'])
            and all(not any(F(r['exact_rigid_compression_row'].get(str(j), '0')) for j in columns)
                    for r in source['shared_material_support_records']), 'whole continuous bed must exclude this shaft')
    require(all(c['kind'] in ('common_shaft_bearing', 'shaft_end_capture')
                for c, row in zip(components, rows, strict=True) if any(row.get(j, F(0)) for j in columns)),
            'shaft projections must use unchanged spring metrics only')
    ids = [c['id'] for c in components]; chosen = inputs['null_reaction_ids']
    require(len(chosen) == len(set(chosen)) == 3 and all(identity in ids for identity in chosen), 'three distinct source reactions required')
    js = [ids.index(identity) for identity in chosen]
    require(all(components[j]['kind'] == 'common_shaft_bearing' and ids[j].startswith(inputs['axis_id']+'/') for j in js),
            'own bearing reactions required')
    coefficients = {ids.index(key): F(value) for key, value in mixed['refined_control']['source_linear_coefficients'].items()}
    stiffness = [c['stiffness'] for c in components]
    candidate = list(map(F, prior['candidate_auxiliary_weights']))
    selected = set(old['shared_minor_columns']); error = F(bound['exact_new_correction_inf_n'])
    require(error == F(bound['load_certificate']['exact_selected_correction_inf_upper']), 'same certified correction box required')
    radius = [error if j in selected else F(0) for j in range(len(components))]
    gap, support = F(bound['exact_total_Fenchel_gap_upper_nmm']), F(mixed['exact_frozen_continuous_support_upper'])
    original = h.mixed.necessary_interval(coefficients, F(mixed['refined_control']['exact_fixed_point_work']),
        candidate, radius, stiffness, gap, support, ['16/5', '4', '5'])
    require(original == bound['bolt_067_original_lateral_necessary_interval'], 'same complete center, box, gap, support and functional required')
    obstruction = metric_obstruction([[row.get(j, F(0)) for j in columns] for row in (rows[i] for i in js)],
        [coefficients.get(j, F(0)) for j in js], [stiffness[j] for j in js], inputs['pivot_column_offsets'])
    ceiling = certificate_ceiling(original['exact_signed_center'], original['linear_functional_bound']['exact_dual_correction_norm_upper'],
        gap, obstruction['exact_weighted_Gram_lower_for_every_shaft_projection'], support, inputs['uniform_reference_divisor'])
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_mixed_shaft_projection_limit/v1', 'inputs': reference, 'runtime': runtime, 'source_sha256': pins,
            'binding': bound['binding'], 'operator_bundle': pointer, 'exact_original_rigid_load_sha256': load_digest,
            'shaft_body': body, 'registered_shaft_columns': columns, 'null_reaction_ids': chosen,
            'exact_selected_shaft_rows': [[str(rows[i].get(j, F(0))) for j in columns] for i in js],
            'exact_selected_coefficients': [str(coefficients.get(j, F(0))) for j in js],
            'exact_selected_stiffness': [str(stiffness[j]) for j in js], **obstruction, **ceiling,
            'exact_fixed_gap_certificate_nmm': str(gap), 'exact_frozen_support_upper': str(support),
            'original_necessary_interval': original, 'same_correction_box_load_certificate': bound['load_certificate'],
            'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'continuous_law_core_loads_gap_candidate_box_functional_or_support_changed': False,
            'new_solve_optimization_inverse_factorization_or_response': False,
            'actual_pass_failure_or_complete_resistance_established': False,
            'physical_stiffness_demand_restraint_qualified': False,
            'panel_screw_exceedances_deferred': True, 'actual_observations': None, 'structural_acceptance': False,
            'limits': inputs['limits']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'preserve issued projection-limit evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), **{k:v for k,v in result.items()
                       if k in ('necessary_lower_endpoint_ceiling', 'no_shaft_only_projection_can_certify_exceedance_with_this_fixed_certificate')}}))


if __name__ == '__main__':
    main()
