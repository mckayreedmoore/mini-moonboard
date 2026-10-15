"""Tighten one continuous-model gap with a fixed scalar energy polynomial.

Bound the inverse quadratic form on the already certified header block.
Compute no inverse matrix, factorization, displacement or reaction response.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType

import numpy as np
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BOOT = {'path': 'scripts/eoere_mixed_shaft_projection_limit.py',
        'sha256': '9a8ced955420f2c092ffc0724847440a9d0413e493ebefa679fa8a2f3610a64e'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bootstrap(pins):
    data = (ROOT/BOOT['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == BOOT['sha256']
            and pins.get(BOOT['path'], BOOT['sha256']) == BOOT['sha256'], 'frozen scalar bootstrap changed')
    pins[BOOT['path']] = BOOT['sha256']
    module = ModuleType('_eoere_verified_polynomial_bootstrap')
    module.__file__ = str(ROOT/BOOT['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - verified frozen buffer
    return module


def polynomial_energy(matrix, vector, mu, power_count, core):
    """Exact fixed polynomial majorant, conditional on G >= mu*I > 0.

    With U=||G||inf and A=I-G/U, the scalar polynomial is
    q_p(lambda)=1/lambda+(1/mu-1/lambda)*(1-lambda/U)**(2*p).
    Thus G^-1 <= q_p(G) <= I/mu. No inverse matrix is evaluated.
    The caller must authenticate the inherited positive-block certificate.
    """
    vector, mu = list(map(F, vector)), F(mu)
    n = len(vector)
    require(n > 0 and len(matrix) == n and type(power_count) is int and 0 <= power_count <= 64,
            'same nonempty dimensions and bounded fixed integer power count required')
    require(all(type(j) is int and 0 <= j < n for row in matrix for j in row),
            'bounded integer matrix indices required')
    matrix = [{j: F(v) for j, v in row.items() if F(v)} for row in matrix]
    require(matrix == core.transpose(matrix, n), 'exact symmetric matrix required')
    upper = max(sum(map(abs, row.values()), F(0)) for row in matrix)
    require(0 < mu <= upper, 'positive inherited eigenvalue lower bound required')
    value, current = F(0), vector
    for _ in range(power_count):
        action = core.action(matrix, current)
        square = sum((v*v for v in current), F(0))
        mixed = sum((v*w for v, w in zip(current, action, strict=True)), F(0))
        increment = 2*square/upper-mixed/upper**2
        require(increment >= 0, 'positive polynomial summands required')
        value += increment
        current = [v-w/upper for v, w in zip(current, action, strict=True)]
    value += sum((v*v for v in current), F(0))/mu
    require(0 <= value <= sum((v*v for v in vector), F(0))/mu, 'polynomial spectral bounds required')
    return value, upper


def box_energy(center_energy, uncertainty, mu, bounds):
    """Minkowski bound using q_p(G) <= I/mu and outward scalar roots."""
    center_energy, mu = F(center_energy), F(mu)
    uncertainty = list(map(F, uncertainty))
    require(center_energy >= 0 and mu > 0 and uncertainty and min(uncertainty) >= 0,
            'nonnegative center/box and positive inherited eigenvalue bound required')
    error = bounds.upper(sum((v*v for v in uncertainty), F(0))/mu)
    return bounds.upper((bounds.root_bounds(bounds.upper(center_energy))[1]+bounds.root_bounds(error)[1])**2)


def certified_free_block(matrix, certificate, core, exact):
    """Read the saved block and match its existing exact positive certificate."""
    own, datum = certificate['global_coordinates'], certificate['datum_local_coordinates']
    require(certificate['constructed_core_PSD_and_exact_registered_kernel_proven'] is True
            and len(own) == certificate['coordinates'] and len(set(own)) == len(own)
            and all(type(g) is int and 0 <= g < matrix.shape[0] for g in own)
            and len(set(datum)) == len(datum)
            and all(type(i) is int and 0 <= i < len(own) for i in datum), 'own certified body/datum coordinates required')
    free = [g for i, g in enumerate(own) if i not in set(datum)]
    lookup = {g: i for i, g in enumerate(free)}
    require(matrix.has_canonical_format and matrix.shape[0] == matrix.shape[1] and free,
            'canonical saved square CSR matrix and nonempty free block required')
    rows = []
    for g in free:
        row = {}
        for at in range(matrix.indptr[g], matrix.indptr[g+1]):
            j = int(matrix.indices[at])
            if j in lookup and matrix.data[at]:
                row[lookup[j]] = F(matrix.data[at])
        rows.append(row)
    proof = certificate['quotient_positive_certificate']
    require(rows == core.transpose(rows, len(rows)) and exact.matrix_digest(rows) == proof['exact_matrix_sha256'],
            'exact symmetric free block must match the inherited positive certificate')
    mu = F(proof['exact_smallest_eigenvalue_lower'])
    require(mu > 0, 'positive inherited free-block eigenvalue bound required')
    return free, rows, mu


def run(reference):
    pins = {}; prior_method = bootstrap(pins); boot = prior_method.bootstrap(pins); base = boot.producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_normal_patch_polynomial_gap_inputs/v1'
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
            and inputs['extra_grid'] is False and inputs['case_id'] == 'a12-forward'
            and inputs['body'] == 'base_header' and type(inputs['fixed_power_count']) is int and inputs['fixed_power_count'] == 64
            and inputs['actual_observations'] is None and inputs['structural_acceptance'] is False,
            'same current case/body and predeclared 64-term scalar bound required')
    for row in inputs['execution_sources']:
        base.captured(row, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing scalar bound required')
    source = json.loads(base.captured(inputs['reaction_result'], pins))
    global_limit = json.loads(base.captured(inputs['projection_limit_result'], pins))
    require(source['schema'] == 'eoere_continuous_normal_support_refinement/v1'
            and source['all_six_exact_original_load_dual_bounds_proven'] is True
            and source['continuous_normal_law_or_original_load_changed'] is False
            and global_limit['registered_rigid_rows_covered'] == 800, 'completed unchanged-model certificates required')
    for record in (source, global_limit):
        for path, digest in record['source_sha256'].items():
            base.captured({'path': path, 'sha256': digest}, pins)
    source_inputs = json.loads(base.captured(source['inputs'], pins)); runtime = boot.check_runtime(source_inputs['runtime'])
    h = base.prepare(source_inputs, pins)
    old = json.loads(base.captured(h.prior_inputs['recession_result'], pins))
    core = json.loads(base.captured(h.prior_inputs['core_result'], pins))
    original = json.loads(base.captured(source_inputs['original_bounds'], pins))
    mixed = json.loads(base.captured(source_inputs['mixed_result'], pins))
    bound, = [c for c in source['cases'] if c['binding']['case_id'] == inputs['case_id']]
    previous, = [c for c in original['cases'] if c['binding'] == bound['binding']]
    require(global_limit['binding'] == bound['binding'] == mixed['refined_control']['binding']
            and core['constructed_comparator_core_PSD_and_exact_registered_kernel_proven'] is True,
            'same original case and certified invariant core required')
    field = json.loads(base.captured(bound['binding']['field'], pins)); pointer = field['operator_bundle']
    require(pointer == previous['operator_bundle'] == bound['operator_bundle'] == global_limit['operator_bundle'],
            'same immutable saved operators required')
    manifest = json.loads(base.captured(pointer['manifest'], pins)); data = base.captured(pointer['arrays'], pins)
    with np.load(io.BytesIO(data), allow_pickle=False) as arrays:
        parts = h.transfer.partitions(manifest, arrays)
        enabled = {r['id'] for r in parts['tangents']} & set(old['shared_constraint_identities'])
        components, ports, bilateral = h.audit.register(parts, field, enabled)
        spec = manifest['K']
        matrix = csr_matrix((arrays[spec['data']], arrays[spec['indices']], arrays[spec['indptr']]), shape=spec['shape'])
    require(len(components) == 2872 and bilateral == 968 and len(ports) == 2324
            and [c['id'] for c in components] == original['scalar_component_identities'], 'complete unchanged scalar order required')
    old_rows = [c['row'] for c in components]; new_rows = list(old_rows)
    stiffness = [c['stiffness'] for c in components]; replaced = set()
    for record in source['shared_material_support_records']:
        j = record['column']
        require(type(j) is int and 0 <= j < len(components) and j not in replaced
                and record['id'] == components[j]['id'] and components[j]['kind'] == 'flange_contact',
                'own unique normal-support column required')
        new_rows[j] = {int(g): F(v) for g, v in record['exact_full_compression_row'].items()}
        stiffness[j] = F(record['exact_area_mm2'])*F(record['exact_density_n_mm3']); replaced.add(j)
    require(len(replaced) == 352 and replaced == {j for j, c in enumerate(components) if c['kind'] == 'flange_contact'},
            'all and only existing finite-area supports required')
    candidate = list(map(F, previous['candidate_auxiliary_weights'])); selected = set(old['shared_minor_columns'])
    rho_old, rho_new = [F(bound[k]) for k in ('exact_old_correction_inf_n', 'exact_new_correction_inf_n')]
    require(rho_old == F(previous['load_certificate']['exact_selected_correction_inf_upper'])
            and rho_new == F(bound['load_certificate']['exact_selected_correction_inf_upper']), 'same correction boxes required')
    transposes = [h.core.transpose(rows, matrix.shape[0]) for rows in (old_rows, new_rows)]
    center = [a-b for a, b in zip(*(h.core.action(rows, candidate) for rows in transposes), strict=True)]
    uncertainty = [sum((abs(v)*rho_old for j, v in a.items() if j in selected), F(0))
                   +sum((abs(v)*rho_new for j, v in b.items() if j in selected), F(0))
                   for a, b in zip(*transposes, strict=True)]
    certificate, = [c for c in core['body_certificates'] if c['body'] == inputs['body']]
    free, block, mu = certified_free_block(matrix, certificate, h.core, h.exact)
    residual, box = [center[g] for g in free], [uncertainty[g] for g in free]
    body, = [c for c in bound['body_residual_enclosures'] if c['body'] == inputs['body']]
    old_delta = h.bounds.upper(sum(((abs(v)+e)**2 for v, e in zip(residual, box, strict=True)), F(0))/mu)
    require(old_delta == F(body['exact_changed_dual_load_square_upper_nmm']), 'same prior componentwise residual bound required')
    energy, upper = polynomial_energy(block, residual, mu, inputs['fixed_power_count'], h.core)
    polynomial_delta = box_energy(energy, box, mu, h.bounds); delta = min(old_delta, polynomial_delta)
    inherited = F(body['exact_inherited_residual_square_upper_nmm'])
    combined = h.bounds.upper((h.bounds.root_bounds(inherited)[1]+h.bounds.root_bounds(delta)[1])**2)
    prior_combined = F(body['exact_complementary_residual_square_upper_nmm'])
    require(prior_combined == h.bounds.upper((h.bounds.root_bounds(inherited)[1]+h.bounds.root_bounds(old_delta)[1])**2)
            and combined <= prior_combined, 'same inherited residual and separately certified tighter upper required')
    old_gap = F(bound['exact_total_Fenchel_gap_upper_nmm'])
    gap = h.bounds.upper(old_gap-(prior_combined-combined)/2)
    coefficients = {j: F(mixed['refined_control']['source_linear_coefficients'].get(c['id'], '0')) for j, c in enumerate(components)}
    coefficients = {j: v for j, v in coefficients.items() if v}
    radius = [rho_new if j in selected else F(0) for j in range(len(components))]
    support, offset = F(mixed['exact_frozen_continuous_support_upper']), F(mixed['refined_control']['exact_fixed_point_work'])
    def interval(value):
        return h.mixed.necessary_interval(coefficients, offset, candidate, radius, stiffness, value, support, ['16/5', '4', '5'])
    frozen = interval(old_gap)
    require(frozen == bound['bolt_067_original_lateral_necessary_interval'] == global_limit['original_necessary_interval']
            and old_gap == F(global_limit['exact_fixed_gap_certificate_nmm']), 'unchanged prior functional, support and gap required')
    new_interval = interval(gap)
    consumer = base.private(global_limit['execution_consumer'], pins)
    initial_policy = sys.get_int_max_str_digits()
    with consumer.integer_text_policy(20000):
        metric = F(global_limit['exact_full_metric_lower_for_every_registered_kernel_projection'])
        ceiling = prior_method.certificate_ceiling(frozen['exact_signed_center'],
            frozen['linear_functional_bound']['exact_dual_correction_norm_upper'], gap, metric, support, 5)
        height = F(global_limit['exact_same_corrected_dual_work_absolute_upper'])
        critical = max(F(0), height-support/5)**2/(2*metric)
        scale = 10**24
        critical_bounds = [F(critical.numerator*scale//critical.denominator, scale), h.bounds.upper(critical)]
        below = gap < critical
    require(sys.get_int_max_str_digits() == initial_policy, 'restore incoming integer text policy')
    del ceiling['no_shaft_only_projection_can_certify_exceedance_with_this_fixed_certificate']
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    digest = lambda values: hashlib.sha256(json.dumps(list(map(str, values)), separators=(',', ':')).encode()).hexdigest()
    return {'schema': 'eoere_normal_patch_polynomial_gap/v1', 'inputs': reference, 'runtime': runtime,
        'source_sha256': pins, 'binding': bound['binding'], 'operator_bundle': pointer,
        'reaction_result': inputs['reaction_result'], 'projection_limit_result': inputs['projection_limit_result'],
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
        'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False, 'body': inputs['body'],
        'free_coordinates': free, 'free_block_sha256': certificate['quotient_positive_certificate']['exact_matrix_sha256'],
        'exact_inherited_eigenvalue_lower': str(mu), 'exact_norm_inf_upper': str(upper),
        'fixed_power_count': inputs['fixed_power_count'], 'polynomial_degree_upper': 2*inputs['fixed_power_count'],
        'fixed_matrix_applications': inputs['fixed_power_count'],
        'exact_free_residual_sha256': digest(residual), 'exact_free_uncertainty_sha256': digest(box),
        'exact_center_polynomial_energy_upper_nmm': str(h.bounds.upper(energy)),
        'exact_prior_changed_dual_square_upper_nmm': str(old_delta),
        'exact_polynomial_changed_dual_square_upper_nmm': str(polynomial_delta),
        'exact_used_changed_dual_square_upper_nmm': str(delta), 'exact_inherited_residual_square_upper_nmm': str(inherited),
        'exact_prior_combined_residual_square_upper_nmm': str(prior_combined),
        'exact_new_combined_residual_square_upper_nmm': str(combined),
        'exact_prior_total_gap_upper_nmm': str(old_gap), 'exact_new_total_gap_upper_nmm': str(gap),
        'prior_total_gap_upper_nmm': float(old_gap), 'new_total_gap_upper_nmm': float(gap),
        'exact_necessary_gap_threshold_lower_upper_nmm': list(map(str, critical_bounds)),
        'gap_below_prior_necessary_threshold': below,
        'new_fixed_family_ceiling': ceiling,
        'old_global_impossibility_bound_still_below_one': F(ceiling['exact_necessary_lower_endpoint_ceiling']) < 1,
        'prior_unprojected_necessary_interval': frozen, 'new_unprojected_necessary_interval': new_interval,
        'integer_text_policy_restored': True, 'continuous_law_core_loads_candidate_box_functional_support_changed': False,
        'only_one_body_complementary_energy_upper_replaced': True, 'inverse_quadratic_form_bounded': True,
        'new_optimization_inverse_matrix_factorization_or_response': False,
        'mixed_exceedance_pass_or_complete_resistance_established': False,
        'physical_stiffness_demand_restraint_qualified': False, 'panel_screw_exceedances_deferred': True,
        'actual_observations': None, 'structural_acceptance': False, 'limits': inputs['limits']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); require(not args.out.exists(), 'preserve issued scalar-gap evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
        'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), 'gap_upper_nmm': result['new_total_gap_upper_nmm']}))


if __name__ == '__main__':
    main()
