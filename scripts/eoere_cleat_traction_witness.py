"""Certified necessary boundary-stress tests for declared continuous cleat loads.

An angular search only chooses witnesses. Exact arithmetic bounds pressure
below and the full-tensor strength support above on positive-area bore patches.
This does not solve an interior field, fracture, contact or frame response.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import platform
from fractions import Fraction as F
from functools import cache
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def capture(reference, pins):
    path = (ROOT/reference['path']).resolve()
    require(path.is_relative_to(ROOT), 'repository source required')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == reference['sha256'] and pins.get(reference['path'], digest) == digest,
            'captured source changed: '+reference['path'])
    pins[reference['path']] = digest
    return data


def definitions(reference, functions, assignments, namespace, pins):
    """Reuse selected pure definitions from the exact authenticated buffer."""
    tree = ast.parse(capture(reference, pins), filename=reference['path'])
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in functions]
    values = [node for node in tree.body if isinstance(node, ast.Assign) and len(node.targets) == 1
              and isinstance(node.targets[0], ast.Name) and node.targets[0].id in assignments]
    require(len(selected) == len(functions) and {n.name for n in selected} == set(functions)
            and len(values) == len(assignments) and {n.targets[0].id for n in values} == set(assignments),
            'complete unique frozen pure definitions required')
    code = compile(ast.Module(body=values+selected, type_ignores=[]), reference['path'], 'exec')
    exec(code, namespace)  # noqa: S102 - authenticated owner-authorized repository definitions
    return SimpleNamespace(**{name: namespace[name] for name in (*functions, *assignments)})


def methods(refs, pins):
    namespace = {'F': F, 'math': math, 'np': np, 'cache': cache, 'require': require}
    definitions(refs['rational'], ('rational',), (), namespace, pins)
    definitions(refs['normal'], ('normal',), (), namespace, pins)
    definitions(refs['stress'], ('number', 'support'), ('BASE_STRENGTHS',), namespace, pins)
    definitions(refs['pi'], ('atan_series', 'pi_bounds'), (), namespace, pins)
    return SimpleNamespace(**{k: namespace[k] for k in ('normal', 'support', 'BASE_STRENGTHS', 'pi_bounds')})


def sqrt_bounds(value, bits=96):
    value = F(value)
    require(value >= 0 and type(bits) is int and 16 <= bits <= 256, 'bounded nonnegative square root required')
    scale = 1 << bits
    lower = F(math.isqrt(value.numerator*scale*scale//value.denominator), scale)
    upper = lower if lower*lower == value else lower+F(1, scale)
    require(lower*lower <= value <= upper*upper, 'exact square-root enclosure failed')
    return lower, upper


def pressure_bounds(force, radius, length, stored_peak, degrees, dot_interval, pi_interval):
    """Enclose both exact wrench normalization and its stored float amplitude."""
    f = tuple(map(F, force))
    radius, length, stored_peak = map(F, (radius, length, stored_peak))
    require(len(f) == 3 and f[1] == 0 and radius > 0 and length > 0 and stored_peak > 0
            and degrees in (30, 60, 90), 'nonzero own lateral pressure hypothesis required')
    q = f[0]**2+f[2]**2
    require(q > 0, 'nonzero lateral force required')
    d0, d1 = map(F, dot_interval)
    require(0 < d0 <= d1, 'strictly loaded angular patch required')
    threshold = {30: F(3, 4), 60: F(1, 4), 90: F(0)}[degrees]
    require(d0*d0 > threshold*q, 'whole witness patch must lie strictly inside the pressure arc')
    lo, hi = sqrt_bounds(q)
    require(lo > 0, 'force below the declared square-root resolution')
    c0, c1 = max(F(0), d0/hi), min(F(1), d1/lo)
    require(c0 <= c1, 'unit-normal dot enclosure failed')
    if degrees == 30:
        root3 = sqrt_bounds(F(3))
        integral = 3*root3[0]/8, 3*root3[1]/8
        shape = (max(F(0), 4*c0**3-3*c0), max(F(0), 4*c1**3-3*c1))
    elif degrees == 60:
        c0 = max(c0, F(1, 2))
        integral = F(6, 5), F(6, 5)
        shape = (sqrt_bounds(max(F(0), (1+4*c0**3-3*c0)/2))[0],
                 sqrt_bounds(max(F(0), (1+4*c1**3-3*c1)/2))[1])
    else:
        integral = pi_interval[0]/2, pi_interval[1]/2
        shape = c0, c1
    peak = min(lo/(radius*length*integral[1]), stored_peak), max(hi/(radius*length*integral[0]), stored_peak)
    require(0 <= shape[0] <= shape[1] <= 1, 'nonnegative pressure-shape enclosure failed')
    return (peak[0]*shape[0], peak[1]*shape[1]), peak


def certify(band, degrees, quarter, interval, method, divisor=F(2), load_factor=F(1)):
    low, high = map(F, interval)
    require(0 <= low < high <= 1 and divisor > 0 and load_factor > 0, 'positive quarter-arc/scenario required')
    first, last = method.normal(quarter, low), method.normal(quarter, high)
    normal_ranges = [tuple(sorted((a, b))) for a, b in zip(first, last, strict=True)]
    force = tuple(map(F, band['local_force_n']))
    dot_range = tuple(sum((min(f*a, f*b) if i == 0 else max(f*a, f*b)
                           for f, (a, b) in zip((force[0], force[2]), normal_ranges, strict=True)), F(0))
                      for i in (0, 1))
    u0, u1 = map(F, band['axial_interval_mm'])
    length, radius = u1-u0, F(band['radius_mm'])
    pressure, peak = pressure_bounds(force, radius, length,
        band['peak_pressure_mpa_by_half_angle'][str(degrees)], degrees, dot_range, method.pi_bounds())
    strengths = {k: v/divisor for k, v in method.BASE_STRENGTHS.items()}
    c, s = (max(map(abs, bounds)) for bounds in normal_ranges)
    support = method.support((-c*c, F(0), -s*s, F(0), 2*c*s, F(0)), strengths)
    require(support > 0, 'positive complete stress-domain support required')
    lower = load_factor*pressure[0]/support
    # The middle half of the axial band avoids every end discontinuity.
    inner = u0+length/4, u1-length/4
    area_lower = radius*(inner[1]-inner[0])*2*(high-low)/(1+high*high)
    require(area_lower > 0, 'positive physical witness-patch area required')
    return {'quarter': quarter, 'half_tangent_interval': list(map(str, (low, high))),
            'radial_normal_component_intervals': [list(map(str, row)) for row in normal_ranges],
            'axial_patch_interval_mm': list(map(str, inner)), 'exact_area_lower_mm2': str(area_lower),
            'exact_pressure_interval_mpa': list(map(str, pressure)),
            'exact_peak_normalization_hull_mpa': list(map(str, peak)),
            'exact_full_tensor_support_upper_mpa': str(support),
            'exact_necessary_index_lower': str(lower), 'necessary_index_lower_display': float(lower),
            'strict_positive_area_reference_failure': lower > 1,
            'disposition': 'DECLARED_LOAD_STRENGTH_HYPOTHESIS_FAILS' if lower > 1 else 'INCONCLUSIVE_NECESSARY_WITNESS'}


def select(band, degrees, method, divisions):
    """Floating search chooses one rational chart point; no acceptance uses it."""
    entries = [(q, F(i, divisions)) for q in range(4) for i in range(divisions+1)]
    normals = np.array([[float(v) for v in method.normal(q, t)] for q, t in entries])
    force = np.array(band['local_force_n'])[[0, 2]]
    norm = float(np.linalg.norm(force))
    require(norm > 0, 'nonzero band required for selection')
    cosine = np.clip(normals@force/norm, -1., 1.)
    phi = np.arccos(cosine)
    beta = math.radians(degrees)
    pressure = band['peak_pressure_mpa_by_half_angle'][str(degrees)]*np.maximum(0., np.cos(math.pi*phi/(2*beta)))
    pressure[phi >= beta] = 0.
    c, s = normals.T
    raw = method.BASE_STRENGTHS
    support = np.maximum.reduce([float(raw['compression_parallel'])*c*c,
                                 float(raw['compression_perpendicular'])*s*s,
                                 2*float(raw['parallel_shear'])*abs(c*s)])
    return entries[int(np.argmax(pressure/support))]


def run(reference):
    pins = {}
    inputs = json.loads(capture(reference, pins))
    require(inputs['schema'] == 'eoere_cleat_continuous_traction_witness_inputs/v1'
            and inputs['selection_divisions_per_quarter'] == 512
            and inputs['initial_half_tangent_radius'] == '1/4096'
            and inputs['maximum_arc_halvings'] == 20, 'declared bounded witness rule required')
    for ref in inputs['execution_sources']:
        capture(ref, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing witness producer required')
    require(inputs['runtime'] == {'python': platform.python_version(), 'numpy': np.__version__}, 'declared shared runtime required')
    material = json.loads(capture(inputs['retained_strength_input'], pins))
    capture(material['material_source'], pins)
    method = methods(inputs['methods'], pins)
    require(method.BASE_STRENGTHS == {k: F(v) for k, v in material['base_strengths_mpa'].items()}
            and material['uniform_strength_divisors'] == ['1.5', '2', '3']
            and material['load_factors'] == ['1', '1.5'] and material['working_strength_divisor'] == '2',
            'unchanged complete C16 tensor hypothesis/scenarios required')
    source = json.loads(capture(inputs['continuous_load_result'], pins))
    for path, digest in source['source_sha256'].items():
        capture({'path': path, 'sha256': digest}, pins)
    parent = json.loads(capture(source['inputs'], pins))
    index = json.loads(capture(inputs['revision_index'], pins))
    current = json.loads(capture(inputs['current_response'], pins))
    require(index['current_response']['cases'] == inputs['current_response']
            and current['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and current['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and current['extra_grid'] is False and len(current['cases']) == 6,
            'current checked response authority required')
    require(parent['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and parent['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and parent['current_bolt_count'] == 100 and parent['current_screw_count'] == 66
            and parent['extra_grid'] is False and parent['actual_observations'] is None
            and source['preserved_v1_load_rows_equal'] is True
            and source['counts'] == {'bore_bands': 96, 'washer_seats': 48, 'contact_cells': 360, 'body_loads': 12}
            and source['status'] == 'COMPLETE_DECLARED_CONTINUOUS_LOAD_FUNCTIONAL_NOT_JOINT_OR_RESISTANCE_QUALIFICATION',
            'complete retained current continuous-load source required')
    cases = {r['case_id']: r for r in current['cases']}
    require(len(source['records']) == 12 and
            {(r['member'], r['case_id']) for r in source['records']} ==
            {(member, case) for member in ('eoere_cleat_left', 'eoere_cleat_right') for case in cases}
            and all(r['field'] == cases[r['case_id']]['field'] and r['state_id'] == cases[r['case_id']]['state_id']
                    for r in source['records']), 'complete distinct current member/case/action joins required')
    rows = []
    for record in source['records']:
        bands = [r for r in record['actions'] if r['kind'] == 'compressive_radial_bore_band']
        require(len(bands) == 8, 'all own bore bands required')
        for band in bands:
            for degrees in (30, 60, 90):
                witness = None
                if any(band['local_force_n']):
                    quarter, center = select(band, degrees, method, inputs['selection_divisions_per_quarter'])
                    for halving in range(inputs['maximum_arc_halvings']+1):
                        radius = F(inputs['initial_half_tangent_radius'])/2**halving
                        interval = max(F(0), center-radius), min(F(1), center+radius)
                        try:
                            witness = certify(band, degrees, quarter, interval, method)
                            break
                        except ValueError as exc:
                            if 'pressure arc' not in str(exc) and 'strictly loaded' not in str(exc):
                                raise
                    require(witness is not None, 'no admissible exact witness; no failure or pass follows')
                for divisor in material['uniform_strength_divisors']:
                    for factor in material['load_factors']:
                        certificate = certify(band, degrees, quarter, interval, method, F(divisor), F(factor)) if witness else None
                        rows.append({k: record[k] for k in ('member', 'case_id', 'state_id', 'field')} |
                                    {'source_action_id': band['source_action_id'], 'half_angle_degrees': degrees,
                                     'strength_divisor': divisor, 'load_factor': factor, 'certificate': certificate,
                                     'zero_source_action': witness is None})
    require(len(rows) == 1728 and sum(r['zero_source_action'] for r in rows) == 270,
            'all 96 bands/three footprints/six scenarios required')
    summaries = []
    for degrees in (30, 60, 90):
        for divisor in material['uniform_strength_divisors']:
            for factor in material['load_factors']:
                selected = [r for r in rows if (r['half_angle_degrees'], r['strength_divisor'], r['load_factor']) == (degrees, divisor, factor)]
                active = [r for r in selected if r['certificate'] is not None]
                worst = max(active, key=lambda r: F(r['certificate']['exact_necessary_index_lower']))
                summaries.append({'half_angle_degrees': degrees, 'strength_divisor': divisor, 'load_factor': factor,
                                  'bands': len(selected), 'zero_actions': len(selected)-len(active),
                                  'certified_failed_bands': sum(r['certificate']['strict_positive_area_reference_failure'] for r in active),
                                  'inconclusive_nonzero_bands': sum(not r['certificate']['strict_positive_area_reference_failure'] for r in active),
                                  'maximum_selected_necessary_lower': worst['certificate']['necessary_index_lower_display'],
                                  'maximum_selected_necessary_lower_exact': worst['certificate']['exact_necessary_index_lower'],
                                  'largest_lower_identity': {k: worst[k] for k in ('member', 'case_id', 'source_action_id')},
                                  'minimum_witness_patch_area_lower_mm2': min(float(F(r['certificate']['exact_area_lower_mm2'])) for r in active)})
    for path, digest in pins.items():
        require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, 'source changed during witness evaluation: '+path)
    return {'schema': 'eoere_cleat_continuous_traction_necessary_witnesses/v1', 'inputs': reference,
            'status': 'DECLARED_CONTINUOUS_LOAD_STRENGTH_NECESSARY_WITNESSES_EVALUATED',
            'geometry_revision': current['geometry_revision'], 'hardware_revision': current['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'source_sha256': pins, 'summary': summaries, 'rows': rows,
            'interior_or_fracture_resistance_qualified': False, 'physical_failure_established': False,
            'physical_demand_bounds_established': False, 'new_elastic_native_or_frame_solve': False,
            'structural_acceptance': False, 'actual_observations': None, 'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'fresh owned output path required')
    data = args.inputs.read_bytes()
    result = run({'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest()})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), 'comparisons': len(result['rows'])}))


if __name__ == '__main__':
    main()
