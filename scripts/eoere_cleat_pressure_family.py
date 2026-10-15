"""Necessary cleat rejection across a continuous prescribed-pressure family.

One unchanged bore band suffices for this conditional negative certificate.
No interior, contact-equilibrium or frame response is calculated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from fractions import Fraction as F
from functools import cache
from pathlib import Path
from types import ModuleType

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BASE_PATH = 'scripts/eoere_cleat_traction_witness.py'
BASE_SHA = '941cdd505e60e0e4275aa3b71fb5434d80d26a2f1c8d8f0ec96a6d87f5ae8dce'
WINDOWS = ((30, 45), (45, 60), (60, 90))


@cache
def base():
    path = ROOT/BASE_PATH
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != BASE_SHA:
        raise ValueError('preserved boundary method changed')
    module = ModuleType('_eoere_pressure_family_boundary_method')
    module.__file__ = str(path)
    exec(compile(data, str(path), 'exec'), module.__dict__)  # noqa: S102 - authenticated source buffer
    return module


def normalization_bounds(degrees, method):
    """J(beta)=integral[-beta,beta](cos(pi*phi/(2*beta))*cos(phi) dphi)."""
    source = base()
    if degrees == 30:
        return tuple(3*v/8 for v in source.sqrt_bounds(F(3)))
    if degrees == 45:
        return tuple(2*v/3 for v in source.sqrt_bounds(F(2)))
    if degrees == 60:
        return F(6, 5), F(6, 5)
    if degrees == 90:
        return tuple(v/2 for v in method.pi_bounds())
    raise ValueError('declared exact normalization endpoint required')


def shape_lower(degrees, cosine):
    cosine = F(cosine)
    source = base()
    source.require(0 < cosine <= 1 and degrees in (30, 45, 60), 'declared loaded-angle shape required')
    threshold = {30: F(3, 4), 45: F(1, 2), 60: F(1, 4)}[degrees]
    source.require(cosine*cosine > threshold, 'witness lies outside the smallest pressure arc')
    if degrees == 30:
        return 4*cosine**3-3*cosine
    if degrees == 45:
        return 2*cosine**2-1
    return source.sqrt_bounds((1+4*cosine**3-3*cosine)/2)[0]


def certify(band, window, quarter, interval, method, divisor=F(2), load_factor=F(1)):
    """One finite patch bound valid for every real beta in the entire window."""
    source = base()
    source.require(not isinstance(divisor, bool) and not isinstance(load_factor, bool), 'positive exact scenario required')
    divisor, load_factor = F(divisor), F(load_factor)
    low, high = map(F, interval)
    source.require(window in WINDOWS and 0 <= low < high <= 1 and divisor > 0 and load_factor > 0,
                   'declared pressure window and positive exact scenario required')
    first, last = method.normal(quarter, low), method.normal(quarter, high)
    ranges = [tuple(sorted((a, b))) for a, b in zip(first, last, strict=True)]
    force = list(map(F, band['local_force_n']))
    radius = F(band['radius_mm']); u0, u1 = map(F, band['axial_interval_mm']); length = u1-u0
    source.require(len(force) == 3 and force[1] == 0 and radius > 0 and length > 0,
                   'own lateral band geometry required')
    norm = source.sqrt_bounds(force[0]**2+force[2]**2)
    source.require(norm[0] > 0, 'nonzero resolved band force required')
    dot = sum((min(f*a, f*b) for f, (a, b) in zip((force[0], force[2]), ranges, strict=True)), F(0))
    cosine = min(F(1), dot/norm[1])
    shape = shape_lower(window[0], cosine)
    integral = normalization_bounds(window[1], method)
    pressure_lower = load_factor*norm[0]*shape/(radius*length*integral[1])
    strengths = {k: v/divisor for k, v in method.BASE_STRENGTHS.items()}
    c, s = (max(map(abs, bounds)) for bounds in ranges)
    support = method.support((-c*c, F(0), -s*s, F(0), 2*c*s, F(0)), strengths)
    source.require(support > 0, 'positive complete stress-domain support required')
    area = radius*(length/2)*2*(high-low)/(1+high*high)
    index = pressure_lower/support
    return {'half_angle_window_degrees': list(window), 'quarter': quarter,
            'half_tangent_interval': list(map(str, (low, high))),
            'radial_normal_component_intervals': [list(map(str, r)) for r in ranges],
            'axial_patch_interval_mm': list(map(str, (u0+length/4, u1-length/4))),
            'exact_area_lower_mm2': str(area), 'exact_cosine_lower': str(cosine),
            'exact_shape_lower': str(shape), 'normalization_upper_interval': list(map(str, integral)),
            'exact_pressure_lower_mpa': str(pressure_lower),
            'exact_full_tensor_support_upper_mpa': str(support),
            'exact_necessary_index_lower': str(index), 'strict_positive_area_reference_failure': index > 1}


def run(reference):
    source, pins = base(), {}
    inputs = json.loads(source.capture(reference, pins))
    source.require(inputs['schema'] == 'eoere_cleat_continuous_pressure_family_inputs/v1'
                   and inputs['runtime'] == {'python': platform.python_version(), 'numpy': np.__version__}
                   and inputs['half_angle_windows_degrees'] == [list(v) for v in WINDOWS],
                   'exact retained pressure-family input and runtime required')
    for ref in inputs['execution_sources']:
        source.capture(ref, pins)
    source.require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA and pins.get(BASE_PATH) == BASE_SHA,
                   'exact executing and preserved source identities required')
    parent = json.loads(source.capture(inputs['boundary_result'], pins))
    for path, digest in parent['source_sha256'].items():
        source.capture({'path': path, 'sha256': digest}, pins)
    prior_inputs = json.loads(source.capture(parent['inputs'], pins))
    loads = json.loads(source.capture(prior_inputs['continuous_load_result'], pins))
    current = json.loads(source.capture(prior_inputs['current_response'], pins))
    index = json.loads(source.capture(prior_inputs['revision_index'], pins))
    material = json.loads(source.capture(prior_inputs['retained_strength_input'], pins))
    method = source.methods(prior_inputs['methods'], pins)
    source.require(index['current_response']['cases'] == prior_inputs['current_response']
                   and parent['geometry_revision'] == current['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                   and parent['hardware_revision'] == current['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                   and parent['current_bolt_count'] == 100 and parent['current_screw_count'] == 66
                   and parent['extra_grid'] is False and len(parent['rows']) == 1728
                   and len(loads['records']) == 12 and len(current['cases']) == 6
                   and material['working_strength_divisor'] == '2'
                   and method.BASE_STRENGTHS == {k: F(v) for k, v in material['base_strengths_mpa'].items()},
                   'unchanged complete current load and strength authority required')
    selected = inputs['selected_band']
    record, = [r for r in loads['records'] if all(r[k] == selected[k] for k in ('member', 'case_id'))]
    binding, = [r for r in current['cases'] if r['case_id'] == selected['case_id']]
    source.require(record['field'] == binding['field'] and record['state_id'] == binding['state_id'], 'own current field required')
    band, = [r for r in record['actions'] if r['kind'] == 'compressive_radial_bore_band'
             and r['source_action_id'] == selected['source_action_id']]
    candidates = [r for r in parent['rows'] if all(r[k] == selected[k] for k in selected)
                  and r['strength_divisor'] == '2' and r['load_factor'] == '1']
    source.require(len(candidates) == 3 and {r['half_angle_degrees'] for r in candidates} == {30, 60, 90}
                   and all(r['certificate'] is not None for r in candidates), 'three own preserved arc candidates required')
    rows = []
    for window in WINDOWS:
        certificates = []
        for row in candidates:
            old = row['certificate']
            try:
                certificate = certify(band, window, old['quarter'], old['half_tangent_interval'], method)
            except ValueError as exc:
                if 'outside the smallest pressure arc' not in str(exc):
                    raise
                continue
            certificates.append((certificate, row['half_angle_degrees']))
        source.require(certificates, 'no admissible finite-area witness; no family conclusion follows')
        certificate, origin = max(certificates, key=lambda v: F(v[0]['exact_necessary_index_lower']))
        rows.append({'selected_from_prior_half_angle_degrees': origin, **certificate})
    summary = []
    for divisor in material['uniform_strength_divisors']:
        for factor in material['load_factors']:
            lower = min(F(r['exact_necessary_index_lower']) for r in rows)*F(divisor)*F(factor)/2
            summary.append({'strength_divisor': divisor, 'load_factor': factor,
                            'exact_uniform_necessary_lower': str(lower),
                            'all_real_half_angles_in_30_to_90_rejected': lower > 1,
                            'failure_can_be_certified_with_independent_per_band_angles': lower > 1})
    for path, digest in tuple(pins.items()):
        source.capture({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_cleat_continuous_pressure_family/v1', 'inputs': reference, 'source_sha256': pins,
            'geometry_revision': current['geometry_revision'], 'hardware_revision': current['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'selected_band': selected, 'field': binding['field'], 'state_id': binding['state_id'],
            'complete_band_source': band, 'angle_window_certificates': rows, 'scenario_summary': summary,
            'family_definition': inputs['family_definition'], 'limits': inputs['limits'],
            'new_elastic_native_frame_contact_equilibrium_or_CAD_solve': False,
            'physical_failure_or_complete_physical_resistance_established': False,
            'actual_observations': None, 'structural_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    source = base(); source.require(not args.out.exists(), 'preserve issued pressure-family evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)),
                 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
