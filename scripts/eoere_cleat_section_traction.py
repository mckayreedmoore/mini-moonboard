"""Exact corrected tractions for the declared six-resultant section-only model.

Reuse the saved support-cell pattern and unchanged strength hypothesis. A
polynomial correction recovers the entire wrench exactly; subadditivity
certifies the pointwise interaction. This does not qualify a compatible 3D
wood field, free side faces, local fracture or complete cleat resistance.
"""
from __future__ import annotations

import argparse
import importlib.metadata
from fractions import Fraction as F
from pathlib import Path

from scripts import eoere_cleat_section_dual as dual

previous, current = dual.previous, dual.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/cleat-section-traction-inputs-v1.json'
rational = previous.rational


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_current_cleat_section_traction_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
                    and inputs['extra_grid'] is False and inputs['actual_observations'] is None
                    and inputs['physical_demand_bounds_established'] is False
                    and inputs['structural_acceptance'] is False, 'unchanged conditional current scope required')
    current.require(inputs['residual_field_interaction_tolerance'] == 1e-5
                    and inputs['bernstein_cell_budget'] == 100000
                    and inputs['runtime_versions'] == {'numpy': '2.5.2', 'scipy': '1.18.1'},
                    'declared unchanged enclosure controls and runtime required')
    for key, module in (('dual_helper', dual), ('section_helper', previous)):
        ref = current.ref(Path(module.__file__))
        current.require(inputs[key] == ref and module.LOADED_SHA == ref['sha256'],
                        'unchanged loaded and on-disk traction helpers required')


def polynomial_integral(field, u_power=0, v_power=0):
    """Integrate a polynomial times a coordinate monomial over [-1,1]^2."""
    result = F(0)
    for (i, j), coefficient in field.items():
        i, j = i+u_power, j+v_power
        if i % 2 == j % 2 == 0:
            result += coefficient*F(2, i+1)*F(2, j+1)
    return result


def polynomial_wrench(fields, width, height):
    """Independent exact six integrals of the existing correction fields."""
    normal, parallel, rolling = fields
    a, b, scale = width/2, height/2, width*height/4
    return [scale*polynomial_integral(normal), scale*polynomial_integral(parallel),
            scale*polynomial_integral(rolling),
            scale*(b*polynomial_integral(rolling, 1)-a*polynomial_integral(parallel, 0, 1)),
            scale*a*polynomial_integral(normal, 0, 1), -scale*b*polynomial_integral(normal, 1)]


def extremal_wrench(certificate, width, height, strengths):
    """The support cell's signed axis traction has unit interaction everywhere."""
    matrix = dual.form_matrix(width, height, strengths, F(1))
    result = [F(0)]*6
    for cell in certificate['normalized_cells']:
        index = cell['traction_axis_intercept_index']
        current.require(isinstance(index, int) and not isinstance(index, bool) and 0 <= index < 6,
                        'own signed traction intercept required')
        measure = list(map(F, cell['area_first_u_first_v_moments']))
        current.require(len(measure) == 3 and measure[0] > 0, 'positive exact support-cell moments required')
        for component in range(6):
            result[component] += width*height/4*sum(matrix[index][power][component]*measure[power] for power in range(3))
    return result


def construct(wrench, bound, tolerance, cell_budget):
    certificate = bound['certificate']
    width, height = map(F, certificate['exact_rectangle_width_height_mm'])
    strengths = {key: F(value) for key, value in certificate['exact_base_strengths_mpa'].items()}
    width, height, strengths = dual.dimensions(width, height, strengths)
    multiplier = list(map(F, certificate['exact_multiplier_N_Vp_Vq_T_Mp_Mq']))
    integral, reconstructed = dual.support(multiplier, width, height, strengths)
    current.require(certificate == reconstructed and integral > 0, 'entire exact own support certificate required')
    current.require(len(wrench) == 6, 'all six own cut-resultant components required')
    wrench = list(map(rational, wrench))
    work = sum(m*w for m, w in zip(multiplier, wrench, strict=True))
    mu = F(bound['exact_necessary_base_interaction_fraction'])
    current.require(mu > 0 and mu == work/integral
                    and work == F(bound['exact_complete_wrench_dual_work_fraction']),
                    'positive exact own dual-work normalization required')
    unit_wrench = extremal_wrench(certificate, width, height, strengths)
    current.require(sum(m*w for m, w in zip(multiplier, unit_wrench, strict=True)) == integral,
                    'exact extremal-field virtual work must equal its support integral')
    residual = [w-mu*g for w, g in zip(wrench, unit_wrench, strict=True)]
    fields = previous.traction_coefficients(residual, width, height)
    correction = polynomial_wrench(fields, width, height)
    current.require(correction == residual, 'correction must carry the entire residual exactly')
    complete = [mu*g+c for g, c in zip(unit_wrench, correction, strict=True)]
    current.require(complete == wrench, 'corrected field must carry all six original cut resultants exactly')
    enclosure = previous.enclosure(previous.interaction_polynomials(fields, strengths), tolerance, cell_budget)
    residual_upper = F(enclosure['exact_upper_fraction'])
    upper = mu+residual_upper
    current.require(residual_upper >= 0 and upper >= mu, 'nonnegative continuous subadditivity bound required')
    return {'exact_extremal_field_six_resultants_at_unit_interaction': list(map(str, unit_wrench)),
            'exact_extremal_field_multiplier_mu': str(mu), 'exact_residual_six_resultants': list(map(str, residual)),
            'exact_correction_six_resultants': list(map(str, correction)),
            'exact_corrected_six_resultants': list(map(str, complete)),
            'exact_equilibrium_remainder_N_Vp_Vq_T_Mp_Mq': ['0']*6,
            'correction_polynomials_in_u_v': [[[i, j, str(value)] for (i, j), value in sorted(field.items())]
                                             for field in fields],
            'continuous_correction_interaction_enclosure': enclosure,
            'necessary_base_interaction_lower_bound': float(mu),
            'corrected_field_base_interaction_upper_bound': float(upper),
            'exact_necessary_base_interaction_fraction': str(mu),
            'exact_corrected_field_base_interaction_upper_fraction': str(upper),
            'section_only_six_resultant_equilibrium_certified': True,
            'three_dimensional_compatibility_volume_equilibrium_or_free_side_faces_certified': False,
            'complete_cleat_resistance': None}


def comparisons(construction, old):
    lower = F(construction['exact_necessary_base_interaction_fraction'])
    upper = F(construction['exact_corrected_field_base_interaction_upper_fraction'])
    current.require(0 <= lower <= upper, 'ordered necessary/sufficient section-only bounds required')
    rows = []
    for scenario in old['scenarios']:
        scale = rational(scenario['strength_divisor'])*rational(scenario['whole_wrench_multiplier'])
        lo, hi = lower*scale, upper*scale
        status = ('section_only_traction_construction_within_hypothesis' if hi <= 1 else
                  'section_only_traction_hypothesis_infeasible' if lo > 1 else
                  'section_only_traction_comparison_unresolved')
        rows.append({key: scenario[key] for key in ('id', 'working_reference', 'strength_divisor', 'whole_wrench_multiplier')} | {
            'necessary_interaction_lower_bound': float(lo), 'corrected_field_interaction_upper_bound': float(hi),
            'exact_necessary_lower_fraction': str(lo), 'exact_corrected_field_upper_fraction': str(hi),
            'section_only_disposition': status,
            'old_polynomial_construction_status_preserved': scenario['construction_status'],
            'old_polynomial_construction_upper_preserved': scenario['interaction_upper'],
            'complete_cleat_resistance': None, 'physical_failure_or_release_established': False})
    return rows


def run():
    input_ref = current.ref(INPUT)
    inputs = current.read(input_ref)
    validate(inputs)
    runtime = {key: importlib.metadata.version(key) for key in inputs['runtime_versions']}
    current.require(runtime == inputs['runtime_versions'], 'declared traction consumer runtime required')
    cases, pins = previous.prior.intake_source.intake()
    source = current.read(inputs['section_dual'])
    old = current.read(inputs['previous_section_construction'])
    materials = current.read(inputs['material_scenarios'])
    previous.validate_assumptions(materials)
    demand = current.read(old['current_cleat_demand'])
    current.require(source['schema'] == 'eoere_current_cleat_section_dual/v1'
                    and source['producer'] == inputs['dual_helper'] and old['producer'] == inputs['section_helper']
                    and old['inputs'] == inputs['material_scenarios']
                    and all(r['geometry_revision'] == inputs['geometry_revision']
                            and r['hardware_revision'] == inputs['hardware_revision'] and r['extra_grid'] is False
                            and r['current_bolt_count'] == 100 and r['current_screw_count'] == 66
                            and r['structural_acceptance'] is False for r in (source, old)),
                    'own retained current source, construction and material bindings required')
    refs = [input_ref, inputs['section_dual'], inputs['previous_section_construction'], inputs['material_scenarios'],
            inputs['dual_helper'], inputs['section_helper'], old['current_cleat_demand'], current.ref(OWN),
            current.ref(current.ROOT/'tests/test_eoere_cleat_section_traction.py'), *inputs['references']]
    pins = current.join(pins, source['source_sha256'], old['source_sha256'], demand['source_sha256'],
                        {r['path']: r['sha256'] for r in refs})
    current.verify(pins)
    bindings = {b['case_id']: b for b, _, _ in cases}
    old_rows = {(r['case_id'], r['member'], r['include_boundary_point_actions']): r for r in old['traces']}
    saved_rows = {(r['case_id'], r['member'], t['boundary_point_actions_in_high_trace']): (r, t)
                  for r in demand['cases'] for t in r['traces']}
    current.require(len(old['traces']) == len(source['traces']) == len(old_rows) == len(saved_rows) == 24
                    and len({(r['case_id'], r['member'], r['include_boundary_point_actions']) for r in source['traces']}) == 24,
                    '24 unique current own one-sided source traces required')
    outputs = []
    for row in source['traces']:
        key = (row['case_id'], row['member'], row['include_boundary_point_actions'])
        preserved, (saved, trace), binding = old_rows[key], saved_rows[key], bindings[row['case_id']]
        current.require(row['source_wrench_n_nmm'] == preserved['source_wrench_n_nmm']
                        == trace['required_cut_on_low_portion_n_nmm']
                        and row['state_id'] == preserved['state_id'] == saved['state_id'] == binding['state_id']
                        and row['field'] == preserved['field'] == saved['field'] == binding['field'],
                        'unchanged own complete cut wrench/case/field required')
        geometry = demand['geometry'][row['member']]
        certificate = row['section_dual']['certificate']
        current.require(geometry['basis_normal_p_q_xyz'] == [[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]]
                        and list(map(F, certificate['exact_rectangle_width_height_mm'])) == [
                            rational(geometry['width_x_mm']), rational(geometry['height_z_mm'])]
                        and {key: F(value) for key, value in certificate['exact_base_strengths_mpa'].items()}
                        == {key: rational(value) for key, value in materials['intact_section_base_reference_mpa'].items()},
                        'unchanged own source rectangle, basis and strengths required')
        construction = construct(row['source_wrench_n_nmm'], row['section_dual'],
                                 inputs['residual_field_interaction_tolerance'], inputs['bernstein_cell_budget'])
        outputs.append({key: row[key] for key in ('case_id', 'state_id', 'field', 'member', 'include_boundary_point_actions',
                                                'source_wrench_n_nmm')} | {
            'corrected_section_traction': construction, 'scenarios': comparisons(construction, preserved)})
    current.verify(pins)
    validate(inputs)
    current.require(current.sha(OWN) == LOADED_SHA, 'loaded traction consumer changed')
    scenarios = [s for row in outputs for s in row['scenarios']]
    return {'schema': 'eoere_current_cleat_section_traction/v1',
            'status': 'COMPLETE_EXACT_SECTION_ONLY_TRACTION_CONSTRUCTIONS_COMPLETE_CLEAT_PENDING',
            'producer': current.ref(OWN), 'inputs': input_ref, 'source_sha256': pins, 'all_sources_unchanged': True,
            'runtime_versions': runtime, 'geometry_revision': inputs['geometry_revision'],
            'hardware_revision': inputs['hardware_revision'], 'extra_grid': False,
            'current_bolt_count': 100, 'current_screw_count': 66, 'traces': outputs, 'trace_count': len(outputs),
            'scenario_comparisons': len(scenarios), 'section_only_constructions_within_hypothesis': sum(
                r['section_only_disposition'] == 'section_only_traction_construction_within_hypothesis' for r in scenarios),
            'complete_cleat_resistance': None, 'complete_joint_or_member_resistance': None,
            'physical_demand_bounds_established': False, 'actual_observations': None, 'structural_acceptance': False,
            'optimizer_frame_native_elastic_solve_CAD_or_geometry_change': False,
            'primary_source_urls': inputs['primary_source_urls'], 'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(current.ref(args.out))


if __name__ == '__main__':
    main()
