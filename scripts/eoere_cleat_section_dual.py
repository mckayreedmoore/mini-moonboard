"""Necessary complete-wrench section bounds under the existing strength hypothesis.

Any dual multiplier gives a necessary interaction lower bound. A six-variable
search selects a candidate; exact-rational affine-cell integration certifies
its ratio without claiming optimizer optimality, a stress-field pass or full
cleat resistance. The previous construction and its exceedances are retained.
"""
from __future__ import annotations

import argparse
import importlib.metadata
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from scripts import eoere_cleat_section_reference as previous

current = previous.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/cleat-section-dual-inputs-v1.json'
rational = previous.rational


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_current_cleat_section_dual_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
                    and inputs['extra_grid'] is False and inputs['actual_observations'] is None
                    and inputs['physical_demand_bounds_established'] is False
                    and inputs['structural_acceptance'] is False, 'unchanged conditional current scope required')
    current.require(inputs['optimizer_options'] == {'method': 'SLSQP', 'ftol': 1e-9, 'maxiter': 200}
                    and inputs['runtime_versions'] == {'numpy': '2.5.2', 'scipy': '1.18.1'},
                    'declared support search and runtime required')
    current.require(inputs['section_helper'] == current.ref(Path(previous.__file__))
                    and previous.LOADED_SHA == inputs['section_helper']['sha256'],
                    'unchanged loaded section helper required')


def clip(polygon, plane):
    """Retain a convex polygon in c0+c1*u+c2*v >= 0, with caller arithmetic."""
    if not polygon:
        return []
    output = []
    for first, second in zip(polygon, polygon[1:]+polygon[:1], strict=True):
        fa = plane[0]+plane[1]*first[0]+plane[2]*first[1]
        fb = plane[0]+plane[1]*second[0]+plane[2]*second[1]
        if fa >= 0:
            output.append(first)
        if (fa < 0 <= fb) or (fb < 0 <= fa):
            t = fa/(fa-fb)
            output.append(tuple(first[j]+t*(second[j]-first[j]) for j in range(2)))
    return output


def moments(polygon, zero):
    """Signed area and first u/v moments of a counterclockwise convex polygon."""
    if len(polygon) < 3:
        return zero, zero, zero
    twice_area, u6, v6 = zero, zero, zero
    for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True):
        cross = a[0]*b[1]-b[0]*a[1]
        twice_area += cross
        u6 += (a[0]+b[0])*cross
        v6 += (a[1]+b[1])*cross
    return twice_area/2, u6/6, v6/6


def cells(forms, one):
    """Partition the square by the maximum of distinct affine forms.

Identical forms share an entire region; keep one to avoid double counting.
Other ties lie on boundaries with zero area. No quadrature or grid is used.
"""
    retained = []
    for index, form in enumerate(forms):
        if any(form == forms[j] for j in retained):
            continue
        retained.append(index)
    result = []
    for index in retained:
        polygon = [(-one, -one), (one, -one), (one, one), (-one, one)]
        for other in retained:
            if other != index:
                polygon = clip(polygon, tuple(forms[index][j]-forms[other][j] for j in range(3)))
        area_moments = moments(polygon, one*0)
        if area_moments[0] > 0:
            result.append((index, polygon, area_moments))
    return result


def form_matrix(width, height, strengths, one):
    """Affine coefficients in (1,u=Z/b,v=X/a) per each physical dual component.

Order is N,Vp,Vq,T,Mp,Mq; p=Z and q=X, so the normal moments have
weights +q*lambda_Mp and -p*lambda_Mq, and torque has -q,+p shear arms.
"""
    a, b = width/2, height/2
    ft, fc, fv, fr = (strengths[k] for k in ('tension', 'compression', 'parallel_shear', 'rolling_shear'))
    zero = one*0
    matrix = [[[zero for _ in range(6)] for _ in range(3)] for _ in range(6)]
    for index, strength in ((0, ft), (1, -fc)):
        matrix[index][0][0] = strength
        matrix[index][1][5] = -strength*b
        matrix[index][2][4] = strength*a
    for index, strength in ((2, fv), (3, -fv)):
        matrix[index][0][1] = strength
        matrix[index][2][3] = -strength*a
    for index, strength in ((4, fr), (5, -fr)):
        matrix[index][0][2] = strength
        matrix[index][1][3] = strength*b
    return matrix


def dimensions(width, height, strengths):
    width, height = rational(width), rational(height)
    current.require(width > 0 and height > 0 and set(strengths) == {
        'tension', 'compression', 'parallel_shear', 'rolling_shear'}, 'positive rectangle and four references required')
    strengths = {key: rational(value) for key, value in strengths.items()}
    current.require(min(strengths.values()) > 0, 'positive own strength hypothesis required')
    return width, height, strengths


def support(multiplier, width, height, strengths):
    """Exact support integral and its complete affine-cell certificate."""
    width, height, strengths = dimensions(width, height, strengths)
    current.require(len(multiplier) == 6, 'six finite physical dual multiplier components required')
    multiplier = list(map(rational, multiplier))
    matrix = form_matrix(width, height, strengths, F(1))
    forms = [tuple(sum(row[j]*multiplier[j] for j in range(6)) for row in piece) for piece in matrix]
    partition = cells(forms, F(1))
    current.require(sum(m[0] for _, _, m in partition) == 4, 'exact support cells must cover the square once')
    integral = width*height/4*sum(sum(c*m for c, m in zip(forms[index], measure, strict=True))
                                for index, _, measure in partition)
    current.require(integral >= 0, 'support integral cannot be negative')
    return integral, {
        'exact_rectangle_width_height_mm': [str(width), str(height)],
        'exact_base_strengths_mpa': {key: str(value) for key, value in strengths.items()},
        'exact_multiplier_N_Vp_Vq_T_Mp_Mq': list(map(str, multiplier)),
        'exact_support_integral_fraction': str(integral),
        'normalized_cells': [{'traction_axis_intercept_index': i, 'affine_coefficients': list(map(str, forms[i])),
                              'vertices_u_v': [list(map(str, p)) for p in polygon],
                              'area_first_u_first_v_moments': list(map(str, measure))}
                             for i, polygon, measure in partition],
        'exact_normalized_partition_area': '4'}


def support_value_gradient(multiplier, width, height, strengths):
    """Floating support/subgradient for candidate search only, never certification."""
    matrix = np.asarray(form_matrix(width, height, strengths, 1.), dtype=float)
    forms = [tuple(row) for row in matrix@multiplier]
    value, gradient = 0., np.zeros(6)
    for index, _, measure in cells(forms, 1.):
        value += float(np.asarray(forms[index])@measure)
        gradient += matrix[index].T@measure
    scale = width*height/4
    return scale*value, scale*gradient


def search(wrench, width, height, strengths, options):
    """Choose one finite candidate; its success flag does not establish optimality."""
    exact_width, exact_height, exact_strengths = dimensions(width, height, strengths)
    current.require(len(wrench) == 6, 'six own wrench components required')
    exact_wrench = list(map(rational, wrench))
    width, height = float(exact_width), float(exact_height)
    strengths = {key: float(value) for key, value in exact_strengths.items()}
    wrench = np.asarray(wrench, dtype=float)
    current.require(wrench.shape == (6,) and np.isfinite(wrench).all() and np.linalg.norm(wrench) > 0.,
                    'finite nonzero six-component own wrench required')
    a, b, area = width/2, height/2, width*height
    normal = max(strengths['tension'], strengths['compression'])
    fv, fr = strengths['parallel_shear'], strengths['rolling_shear']
    scale = np.array([area*normal, area*fv, area*fr, area*(fv*a+fr*b), area*normal*a, area*normal*b])
    normalized_wrench = wrench/scale
    initial = normalized_wrench/(normalized_wrench@normalized_wrench)

    def objective(z):
        value, gradient = support_value_gradient(z/scale, width, height, strengths)
        return value, gradient/scale

    result = minimize(objective, initial, jac=True, method=options['method'],
                      constraints={'type': 'eq', 'fun': lambda z: float(z@normalized_wrench)-1.,
                                   'jac': lambda z: normalized_wrench},
                      options={key: options[key] for key in ('ftol', 'maxiter')})
    current.require(result.x.shape == (6,) and np.isfinite(result.x).all(), 'finite dual search candidate required')
    multiplier = result.x/scale
    integral, certificate = support(multiplier.tolist(), exact_width, exact_height, exact_strengths)
    work = sum(rational(v)*w for v, w in zip(multiplier.tolist(), exact_wrench, strict=True))
    current.require(integral > 0 and work > 0, 'nonzero support and positive complete-wrench dual work required')
    ratio = work/integral
    return {'necessary_base_interaction_lower_bound': float(ratio), 'exact_necessary_base_interaction_fraction': str(ratio),
            'exact_complete_wrench_dual_work_fraction': str(work), 'certificate': certificate,
            'optimizer_diagnostic': {'success': bool(result.success), 'status': int(result.status),
                                     'message': str(result.message), 'iterations': int(result.nit),
                                     'normalization_residual': float(result.x@normalized_wrench)-1.,
                                     'global_optimality_certified': False}}


def comparisons(dual, old):
    lower = F(dual['exact_necessary_base_interaction_fraction'])
    upper = F(old['continuous_base_reference_interaction']['exact_upper_fraction'])
    current.require(0 <= lower <= upper, 'necessary bound exceeds the preserved constructive bound')
    rows = []
    for scenario in old['scenarios']:
        scale = rational(scenario['strength_divisor'])*rational(scenario['whole_wrench_multiplier'])
        lo, hi = lower*scale, upper*scale
        status = ('section_traction_hypothesis_infeasible' if lo > 1 else
                  'preserved_construction_within_section_hypothesis' if hi <= 1 else
                  'section_traction_hypothesis_unresolved_between_bounds')
        rows.append({'id': scenario['id'], 'working_reference': scenario['working_reference'],
                     'strength_divisor': scenario['strength_divisor'],
                     'whole_wrench_multiplier': scenario['whole_wrench_multiplier'],
                     'necessary_interaction_lower_bound': float(lo), 'preserved_construction_upper_bound': float(hi),
                     'exact_necessary_lower_fraction': str(lo), 'exact_preserved_upper_fraction': str(hi),
                     'section_disposition': status, 'complete_cleat_resistance': None,
                     'physical_failure_established': False})
    return rows


def run():
    input_ref = current.ref(INPUT)
    inputs = current.read(input_ref)
    validate(inputs)
    runtime = {key: importlib.metadata.version(key) for key in inputs['runtime_versions']}
    current.require(runtime == inputs['runtime_versions'], 'declared section-dual runtime required')
    cases, pins = previous.prior.intake_source.intake()
    old = current.read(inputs['previous_section_construction'])
    materials = current.read(inputs['material_scenarios'])
    previous.validate_assumptions(materials)
    current.require(old['producer'] == inputs['section_helper'] and old['inputs'] == inputs['material_scenarios']
                    and old['geometry_revision'] == inputs['geometry_revision']
                    and old['hardware_revision'] == inputs['hardware_revision'] and old['extra_grid'] is False
                    and old['current_bolt_count'] == 100 and old['current_screw_count'] == 66
                    and old['structural_acceptance'] is False and len(old['traces']) == 24,
                    'exact retained current construction and material hypothesis required')
    demand = current.read(old['current_cleat_demand'])
    refs = [input_ref, inputs['previous_section_construction'], inputs['material_scenarios'], inputs['section_helper'],
            old['current_cleat_demand'], current.ref(OWN), current.ref(current.ROOT/'tests/test_eoere_cleat_section_dual.py'),
            *inputs['references']]
    pins = current.join(pins, old['source_sha256'], demand['source_sha256'], {r['path']: r['sha256'] for r in refs})
    current.verify(pins)
    bindings = {b['case_id']: b for b, _, _ in cases}
    sources = {(r['case_id'], r['member'], t['boundary_point_actions_in_high_trace']): (r, t)
               for r in demand['cases'] for t in r['traces']}
    current.require(len(sources) == 24 and len({(r['case_id'], r['member'], r['include_boundary_point_actions'])
                    for r in old['traces']}) == 24, '24 unique own current one-sided traces required')
    rows = []
    for row in old['traces']:
        saved, trace = sources[(row['case_id'], row['member'], row['include_boundary_point_actions'])]
        binding = bindings[row['case_id']]
        current.require(row['source_wrench_n_nmm'] == trace['required_cut_on_low_portion_n_nmm']
                        and row['state_id'] == saved['state_id'] == binding['state_id']
                        and row['field'] == saved['field'] == binding['field'], 'own unchanged complete cut wrench required')
        geometry = demand['geometry'][row['member']]
        current.require(geometry['basis_normal_p_q_xyz'] == [[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]],
                        'own saved right-handed Y,Z,X cut basis required')
        dual = search(row['source_wrench_n_nmm'], geometry['width_x_mm'], geometry['height_z_mm'],
                      materials['intact_section_base_reference_mpa'], inputs['optimizer_options'])
        rows.append({key: row[key] for key in ('case_id', 'state_id', 'field', 'member', 'include_boundary_point_actions',
                                             'source_wrench_n_nmm')} | {
            'section_dual': dual, 'scenarios': comparisons(dual, row), 'complete_cleat_resistance': None})
    current.verify(pins)
    validate(inputs)
    current.require(current.sha(OWN) == LOADED_SHA, 'loaded section-dual consumer changed')
    return {'schema': 'eoere_current_cleat_section_dual/v1',
            'status': 'COMPLETE_NECESSARY_SECTION_WRENCH_BOUNDS_COMPLETE_CLEAT_PENDING',
            'producer': current.ref(OWN), 'inputs': input_ref, 'source_sha256': pins, 'all_sources_unchanged': True,
            'runtime_versions': runtime, 'geometry_revision': inputs['geometry_revision'],
            'hardware_revision': inputs['hardware_revision'], 'extra_grid': False,
            'current_bolt_count': 100, 'current_screw_count': 66, 'traces': rows,
            'trace_count': len(rows), 'scenario_comparisons': sum(len(r['scenarios']) for r in rows),
            'complete_cleat_resistance': None, 'complete_joint_or_member_resistance': None,
            'physical_demand_bounds_established': False, 'actual_observations': None, 'structural_acceptance': False,
            'frame_native_elastic_solve_CAD_or_geometry_change': False,
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
