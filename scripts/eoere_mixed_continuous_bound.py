"""Necessary continuous bearing/bending bounds for the unchanged mixed model.

An arbitrary virtual-work multiplier gives a necessary bound on every
measurable bearing density, not only the saved constant-cell witnesses.
Candidate multipliers may come from the existing finite LP. Exact rational
chord/Jensen integration certifies the resulting continuous support bound.
This is not complete joint resistance, physical failure or a design remedy.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from fractions import Fraction as F
from itertools import pairwise
from pathlib import Path

from scripts import eoere_joint_reference_reductions as reductions
from scripts import eoere_joint_vector_tests as vector
from scripts.summarize_eoere_current_response import canonical_sha

current = vector.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/mixed-continuous-bound-inputs-v1.json'


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_current_mixed_continuous_bound_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
                    and inputs['extra_grid'] is False and inputs['actual_observations'] is None
                    and inputs['complete_joint_resistance'] is None
                    and inputs['physical_failure_established'] is False
                    and inputs['physical_demand_bounds_established'] is False
                    and inputs['physical_or_structural_release'] is False
                    and inputs['structural_acceptance'] is False, 'unchanged conditional current model required')
    current.require(inputs['case_id'] == 'a12-forward' and inputs['axis_id'] == 'eoere_bolt_067'
                    and inputs['candidate_cells_per_member'] == inputs['candidate_facets'] == 32
                    and inputs['uniform_reference_divisors'] == [3.2, 4., 5.]
                    and inputs['working_uniform_reference_divisor'] == 5.,
                    'unchanged recorded governing stack, grid and reference hypotheses required')
    current.require(inputs['continuous_support_gap_tolerance'] == '1/1000000'
                    and inputs['integration_cell_budget_per_piece'] == 100000
                    and inputs['highs_version'] == '1.12.0'
                    and inputs['runtime_versions'] == {'numpy': '2.5.2', 'scipy': '1.18.1'},
                    'declared certificate controls and numerical versions required')
    for key, module in (('vector_helper', vector), ('spatial_helper', vector.spatial),
                        ('reduction_helper', reductions)):
        ref = current.ref(Path(module.__file__))
        current.require(inputs[key] == ref and module.LOADED_SHA == ref['sha256'],
                        'unchanged loaded and on-disk continuous-bound helper required')


def read_exact(reference):
    """Bind the actual JSON bytes consumed, independent of later disk audits."""
    data = (current.ROOT/reference['path']).read_bytes()
    current.require(hashlib.sha256(data).hexdigest() == reference['sha256'],
                    'consumed JSON bytes changed: '+reference['path'])
    return json.loads(data)


def rational(value):
    return value if isinstance(value, F) else F(str(value))


def norm_bounds(value, digits=24):
    """Exact outward square-root enclosure, including an exact zero."""
    value = tuple(map(rational, value))
    vector.require(len(value) == 2 and type(digits) is int and 1 <= digits <= 40,
                   'two rational components and bounded root precision required')
    square = sum(v*v for v in value)
    scale = 10**digits
    low = math.isqrt(square.numerator*scale**2//square.denominator)
    if low*low*square.denominator == square.numerator*scale**2:
        return F(low, scale), F(low, scale)
    return F(low, scale), F(low+1, scale)


def affine_norm_integral(first, last, length, tolerance=F(1, 10**8), budget=100000):
    """Jensen lower and trapezoidal upper bounds for an affine vector norm.

    Both inequalities follow from convexity. Rational bisection and outward
    square roots retain every nonzero vector; no tiny coefficient is dropped.
    """
    first, last = tuple(map(rational, first)), tuple(map(rational, last))
    length, tolerance = rational(length), rational(tolerance)
    vector.require(len(first) == len(last) == 2 and length > 0 and tolerance > 0
                   and type(budget) is int and budget > 0, 'positive affine integral controls required')

    def cell(a, b, span):
        middle = tuple((x+y)/2 for x, y in zip(a, b, strict=True))
        low = span*norm_bounds(middle)[0]
        high = span*(norm_bounds(a)[1]+norm_bounds(b)[1])/2
        vector.require(low <= high, 'exact convex integral enclosure failed')
        return a, b, span, low, high

    cells = [cell(first, last, length)]
    lower, upper = cells[0][-2:]
    while upper-lower > tolerance:
        vector.require(len(cells) < budget, 'continuous support integration budget exhausted')
        index = max(range(len(cells)), key=lambda k: cells[k][-1]-cells[k][-2])
        a, b, span, low, high = cells.pop(index)
        middle = tuple((x+y)/2 for x, y in zip(a, b, strict=True))
        children = [cell(a, middle, span/2), cell(middle, b, span/2)]
        lower += sum(c[-2] for c in children)-low
        upper += sum(c[-1] for c in children)-high
        cells.extend(children)
    return lower, upper, len(cells)


def point_moment(points, station, include):
    """Direct exact two-component moment of all own point actions."""
    station = rational(station)
    result = [F(0), F(0)]
    vector.require(type(include) is bool, 'one-sided point trace required')
    for point in points:
        at = rational(point['s'])
        force = tuple(map(rational, point['force']))
        couple = tuple(map(rational, point['couple']))
        vector.require(len(force) == len(couple) == 2, 'complete point force and couple required')
        if at < station or (include and at == station):
            result[0] += -force[1]*(station-at)-couple[0]
            result[1] += force[0]*(station-at)-couple[1]
    return result


def cap_at(caps, station):
    station = rational(station)
    choices = [rational(c['cap']) for c in caps
               if rational(c['interval'][0]) <= station <= rational(c['interval'][1])]
    vector.require(choices and min(choices) > 0, 'own positive moment reference at the trace required')
    return min(choices)


def continuous_bound(arguments, multiplier, tolerance=F(1, 10**8), budget=100000):
    """Certify |B| <= u*(bearing support integral + selected moment support).

    M(t) = P(t) + integral R*q(s)*(t-s)_+ ds, R*(y,z)=(-z,y).
    For a_i(s)=lambda_F+(s-mid_i)*lambda_J+sum R^T*nu_j*(t_j-s)_+,
    B=sum(lambda_F.F+lambda_J.J)-sum(nu_j.P(t_j))
     =sum integral a_i.q - sum nu_j.M(t_j).
    Cauchy gives the bound using the continuous circle, without LP facets.
    """
    surfaces, cuts = arguments['surfaces'], multiplier['cuts']
    rows = multiplier['surfaces']
    vector.require(surfaces and len(rows) == len(surfaces), 'complete own member multiplier census required')
    low, high = map(rational, arguments['domain'])
    vector.require(low < high, 'positive shaft domain required')
    tolerance = rational(tolerance)
    vector.require(tolerance > 0, 'positive continuous support tolerance required')
    exact_cuts, penalty_low, penalty_high = [], F(0), F(0)
    numerator = F(0)
    for cut in cuts:
        station = rational(cut['station'])
        nu = tuple(map(rational, cut['nu']))
        vector.require(low <= station <= high and len(nu) == 2, 'own in-domain moment multiplier required')
        known = point_moment(arguments['points'], station, cut['include'])
        numerator -= sum(n*p for n, p in zip(nu, known, strict=True))
        cap = cap_at(arguments['moment_caps'], station)
        bounds = norm_bounds(nu)
        penalty_low += cap*bounds[0]
        penalty_high += cap*bounds[1]
        exact_cuts.append((station, nu))

    intervals, pieces = [], []
    for surface, row in zip(surfaces, rows, strict=True):
        start, end = map(rational, surface['interval'])
        cap = rational(surface['cap'])
        lf, lj = (tuple(map(rational, row[k])) for k in ('force', 'first_moment'))
        force, first = (tuple(map(rational, surface[k])) for k in ('force', 'first_moment'))
        vector.require(low <= start < end <= high and cap > 0 and
                       len(lf) == len(lj) == len(force) == len(first) == 2
                       and all(end <= a or b <= start for a, b in intervals),
                       'own disjoint bearing intervals, forces and first moments required')
        intervals.append((start, end))
        numerator += sum(x*y for x, y in zip(lf, force, strict=True))
        numerator += sum(x*y for x, y in zip(lj, first, strict=True))
        middle = (start+end)/2

        def coefficient(at, lf=lf, lj=lj, middle=middle):
            result = [x+(at-middle)*y for x, y in zip(lf, lj, strict=True)]
            for station, nu in exact_cuts:
                arm = max(station-at, F(0))
                result[0] += nu[1]*arm
                result[1] -= nu[0]*arm
            return tuple(result)

        stations = sorted({start, end, *(t for t, _ in exact_cuts if start < t < end)})
        for a, b in pairwise(stations):
            pieces.append((a, b, cap, coefficient(a), coefficient(b)))

    # Every piece's weighted enclosure gap is at most tolerance/count.
    bearing_low, bearing_high, cells = F(0), F(0), 0
    for start, end, cap, first, last in pieces:
        lower, upper, count = affine_norm_integral(first, last, end-start,
                                                  tolerance/(len(pieces)*cap), budget)
        bearing_low += cap*lower
        bearing_high += cap*upper
        cells += count
    lower, upper = bearing_low+penalty_low, bearing_high+penalty_high
    vector.require(upper > 0, 'nonzero virtual-work support required')
    return {'exact_virtual_work': numerator,
            'exact_bearing_support_lower_upper': (bearing_low, bearing_high),
            'exact_moment_support_lower_upper': (penalty_low, penalty_high),
            'exact_total_support_lower_upper': (lower, upper),
            'exact_necessary_raw_index_lower': abs(numerator)/upper,
            'integration_cells': cells, 'coefficient_piece_count': len(pieces),
            'exact_affine_support_pieces': pieces}


def candidate(arguments, cells=32, facets=32):
    """Reuse the old LP only to choose multipliers, restoring both callbacks."""
    original_lp, original_point = vector.linprog, vector.point_moment
    pending, calls = [], []

    def point(points, station, include):
        pending.append((station, include))
        return original_point(points, station, include)

    def lp(*args, **kwargs):
        traces = pending.copy()
        pending.clear()
        result = original_lp(*args, **kwargs)
        calls.append((traces, result))
        return result

    try:
        vector.point_moment, vector.linprog = point, lp
        witness = vector.solve(**arguments, cells=cells, facets=facets)
    finally:
        vector.point_moment, vector.linprog = original_point, original_lp
    vector.require(calls, 'candidate LP must expose a complete final multiplier set')
    traces, result = calls[-1]
    rows, normals, _ = vector.prepare(arguments['surfaces'], arguments['points'], arguments['domain'],
                                      arguments['moment_caps'], cells, facets)
    scale = sum((r['high']-r['low'])*r['cap'] for r in rows)
    total = arguments['domain'][1]-arguments['domain'][0]
    equality = result.eqlin.marginals
    vector.require(len(equality) == 4*len(arguments['surfaces'])
                   and len(result.ineqlin.marginals) == (len(rows)+len(traces))*facets,
                   'complete current member forces/first moments and trace rows required')
    member = [{'force': [float(equality[4*i]/scale), float(equality[4*i+2]/scale)],
               'first_moment': [float(equality[4*i+1]/(scale*total)),
                                float(equality[4*i+3]/(scale*total))]}
              for i in range(len(arguments['surfaces']))]
    cuts = []
    for i, (station, include) in enumerate(traces):
        marginal = result.ineqlin.marginals[(len(rows)+i)*facets:(len(rows)+i+1)*facets]
        nu = marginal@normals/vector.cap_at(arguments['moment_caps'], station)
        # Zero multipliers contribute exactly nothing; nonzero values are retained.
        if any(nu != 0):
            cuts.append({'station': float(station), 'include': include, 'nu': nu.tolist()})
    return {'surfaces': member, 'cuts': cuts}, witness


def exact_values(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: exact_values(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [exact_values(v) for v in value]
    return value


def run():
    from scipy.optimize._highspy import _core

    current.require(current.sha(OWN) == LOADED_SHA, 'continuous-bound source changed after import')
    input_ref = current.ref(INPUT)
    inputs = read_exact(input_ref)
    validate(inputs)
    versions = {p: importlib.metadata.version(p) for p in ('numpy', 'scipy')}
    current.require(versions == inputs['runtime_versions'], 'declared numerical runtime required')
    highs = '.'.join(str(getattr(_core, 'HIGHS_VERSION_'+part)) for part in ('MAJOR', 'MINOR', 'PATCH'))
    current.require(highs == inputs['highs_version'], 'declared HiGHS version required')
    source = read_exact(inputs['source_vector_fields'])
    verified = read_exact(inputs['source_saved_verification'])
    reduced = read_exact(inputs['source_uniform_reduction'])
    current.require(source['schema'] == 'eoere_current_representative_vector_joint_tests/v1'
                    and source['current_stack_case_count'] == 48 and source['current_statics_trial_count'] == 144
                    and source['all_sources_unchanged'] is True
                    and source['geometry_revision'] == inputs['geometry_revision']
                    and source['hardware_revision'] == inputs['hardware_revision'] and source['extra_grid'] is False
                    and source['complete_joint_resistance'] is None and source['structural_acceptance'] is False
                    and verified['schema'] == 'eoere_current_vector_joint_saved_witness_verification/v1'
                    and verified['record'] == inputs['source_vector_fields']
                    and verified['trial_count'] == 144 and verified['source_pin_count'] == len(source['source_sha256'])
                    and verified['all_original_current_inputs_joined'] is True
                    and verified['all_saved_vector_fields_independently_integrated'] is True
                    and reduced['schema'] == 'eoere_current_mixed_uniform_material_reference_comparisons/v1'
                    and reduced['comparison_count'] == 432 and reduced['all_sources_unchanged'] is True
                    and reduced['geometry_revision'] == inputs['geometry_revision']
                    and reduced['hardware_revision'] == inputs['hardware_revision']
                    and reduced['current_bolt_count'] == 100 and reduced['current_screw_count'] == 66
                    and reduced['extra_grid'] is False and reduced['complete_joint_resistance'] is None
                    and reduced['structural_acceptance'] is False
                    and reduced['source_vector_fields'] == inputs['source_vector_fields']
                    and reduced['source_saved_verification'] == inputs['source_saved_verification'],
                    'complete unchanged source fields, independent verification and reduction comparison required')
    case = next(c for c in source['cases'] if c['case_id'] == inputs['case_id'])
    stack = next(s for s in case['mixed_stacks'] if s['axis_id'] == inputs['axis_id'])
    arguments = {k: stack['own_inputs'][k] for k in ('surfaces', 'points', 'domain', 'moment_caps')}
    current.require(canonical_sha(arguments) == inputs['source_arguments_sha256']
                    and case['current_equilibrium_and_recovery_pass'] is True
                    and all(s['first_moment'] is not None for s in arguments['surfaces'])
                    and stack['complete_joint_resistance'] is None and stack['physical_compatibility'] is False,
                    'exact complete signed own arguments and unqualified compatibility required')
    old = next(g for g in stack['grids'] if g['cells_per_member'] == 32)
    comparisons = [r for r in reduced['comparisons'] if r['case_id'] == inputs['case_id']
                   and r['axis_id'] == inputs['axis_id'] and r['source_grid_cells_per_member'] == 32]
    current.require(len(comparisons) == 3 and {r['uniform_reference_divisor'] for r in comparisons} == {3.2, 4., 5.}
                    and all(r['state_id'] == case['state_id'] and r['field'] == case['field'] for r in comparisons),
                    'own unchanged source comparison/state/field joins required')
    refs = [input_ref, inputs['source_vector_fields'], inputs['source_saved_verification'],
            inputs['source_uniform_reduction'], current.ref(OWN),
            current.ref(current.ROOT/'tests/test_eoere_mixed_continuous_bound.py')]
    pins = current.join(source['source_sha256'], reduced['source_sha256'], {r['path']: r['sha256'] for r in refs})
    reductions.verify_execution_sources(pins)
    multiplier, witness = candidate(arguments, inputs['candidate_cells_per_member'], inputs['candidate_facets'])
    current.require(abs(witness['certified_raw_reference_index']-old['certified_raw_reference_index']) < 1e-9,
                    'candidate must reproduce the unchanged saved finite-grid witness reference')
    certificate = continuous_bound(arguments, multiplier, F(inputs['continuous_support_gap_tolerance']),
                                   inputs['integration_cell_budget_per_piece'])
    lower = certificate['exact_necessary_raw_index_lower']
    current.require(lower <= rational(witness['certified_raw_reference_index']),
                    'necessary continuous bound cannot exceed an authenticated feasible witness')
    scenarios = []
    for divisor in inputs['uniform_reference_divisors']:
        bound = lower*rational(divisor)
        prior = next(r for r in comparisons if r['uniform_reference_divisor'] == divisor)
        scenarios.append({'uniform_reference_divisor': divisor, 'working_reference': divisor == 5.,
                          'exact_necessary_index_lower': str(bound), 'necessary_index_lower': float(bound),
                          'all_continuous_fields_exceed_hypothesis': bound > 1,
                          'preserved_saved_witness_index': prior['uniform_reduced_certified_witness_index']})
    current.require(current.sha(OWN) == LOADED_SHA, 'continuous-bound source changed after import')
    reductions.verify_execution_sources(pins)
    return {'schema': 'eoere_current_mixed_continuous_bearing_bending_bound/v1', 'inputs': input_ref,
            'producer': current.ref(OWN), 'source_sha256': pins, 'all_sources_unchanged': True,
            'runtime_versions': versions, 'highs_version': highs,
            'case_id': case['case_id'], 'state_id': case['state_id'],
            'field': case['field'], 'axis_id': stack['axis_id'],
            'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'source_arguments': arguments, 'source_arguments_sha256': inputs['source_arguments_sha256'],
            'source_vector_fields': inputs['source_vector_fields'],
            'source_saved_verification': inputs['source_saved_verification'],
            'source_uniform_reduction': inputs['source_uniform_reduction'],
            'candidate_multiplier': multiplier, 'candidate_finite_grid_witness': witness,
            'exact_continuous_certificate': exact_values(certificate), 'scenarios': scenarios,
            'status': 'COMPLETE_NECESSARY_CONTINUOUS_BEARING_BENDING_MODEL_BOUND',
            'candidate_static_LP_performed': True, 'new_frame_forces': False,
            'external_native_frame_elastic_or_CAD_solve': False, 'actual_observations': None,
            'physical_failure_established': False, 'physical_demand_bounds_established': False,
            'physical_or_structural_release': False, 'complete_joint_resistance': None,
            'structural_acceptance': False, 'panel_screw_exceedances_deferred': True,
            'limits': inputs['limits']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(current.ref(args.out))


if __name__ == '__main__':
    main()
