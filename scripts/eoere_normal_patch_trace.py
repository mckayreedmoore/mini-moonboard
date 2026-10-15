"""Continuous normal-contact traces at the six unchanged saved first-order poses.

Exact piecewise quadratic kinematics and inner-box witnesses give local bounds.
This neither solves a new response nor admits these poses for a changed law.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import io
import json
import math
import platform
from fractions import Fraction as F
from itertools import pairwise
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PREVIOUS = {'path': 'scripts/eoere_normal_patch_bound.py',
            'sha256': '47967f6ad033b6f0cd86fb2e928e704ef4ad7f179ef7d4b81bd1e59f3e2a46e2'}
ZERO = (0, 0)


@functools.cache
def previous():
    path = ROOT/PREVIOUS['path']
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != PREVIOUS['sha256']:
        raise ValueError('preserved normal-patch implementation changed')
    module = ModuleType('_eoere_verified_normal_patch')
    module.__file__ = str(path)
    exec(compile(data, str(path), 'exec'), module.__dict__)  # noqa: S102 - pinned repository buffer
    return module


def require(condition, message):
    if not condition:
        raise ValueError(message)


def methods(inputs, pins):
    base = previous()
    loader_ref = inputs['definition_loader']
    loader = ModuleType('_eoere_trace_definition_loader')
    loader.__file__ = str(ROOT/loader_ref['path'])
    exec(compile(base.captured(loader_ref, pins), loader.__file__, 'exec'), loader.__dict__)  # noqa: S102
    env = {'F': F, 'math': math, 'np': np, 'require': require}
    poly = loader.definitions(inputs['polynomial_helper'], ('number', 'add', 'scaled', 'multiply', 'evaluate'), (), env, pins)
    bernstein = loader.definitions(inputs['bernstein_helper'], ('evaluate', 'bernstein'), (),
                                   {'F': F, 'current': SimpleNamespace(require=require)}, pins)
    geometry = base.methods(inputs, pins)
    return SimpleNamespace(poly=poly, bernstein=bernstein.bernstein, geometry=geometry)


def constant(value):
    return {ZERO: F(value)} if value else {}


def world_polynomials(domain):
    return [{ZERO: F(origin), (1, 0): F(domain['basis_rows_xyz'][0][i]),
             (0, 1): F(domain['basis_rows_xyz'][1][i])}
            for i, origin in enumerate(domain['origin_xyz_mm'])]


def station_polynomial(point, timber, poly):
    return poly.add(*(poly.scaled(poly.add(p, constant(-F(start))), F(axis))
                      for p, start, axis in zip(point, timber['start'], timber['axis'], strict=True)))


def gap_polynomial(point, timber, port, fitting_indices, q, normal, mode, segment, poly):
    """Literal algebra of the source's linear nodal interpolation and rigid arm."""
    indices, stations = timber['index'], list(map(F, timber['stations']))
    if mode == 'interior':
        a, b = stations[segment:segment+2]
        t = poly.scaled(poly.add(station_polynomial(point, timber, poly), constant(-a)), 1/(b-a))
        center_station = poly.add(constant(a), poly.scaled(t, b-a))
        first, second = indices[segment], indices[segment+1]
    else:
        require(mode in ('before', 'after'), 'declared source segment mode required')
        index = 0 if mode == 'before' else -1
        first = second = indices[index]
        t = {}
        center_station = constant(stations[index])
    nodal = [poly.add(constant(F(q[i])), poly.scaled(t, F(q[j])-F(q[i]))) for i, j in zip(first, second, strict=True)]
    center = [poly.add(constant(F(start)), poly.scaled(center_station, F(axis)))
              for start, axis in zip(timber['start'], timber['axis'], strict=True)]
    arm = [poly.add(p, poly.scaled(c, -1)) for p, c in zip(point, center, strict=True)]
    rotation = [poly.scaled(p, F(1, 1000)) for p in nodal[3:]]
    wood = [poly.add(nodal[i], poly.multiply(rotation[j], arm[k]), poly.scaled(poly.multiply(rotation[k], arm[j]), -1))
            for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1))]
    own = [F(q[i]) for i in fitting_indices]
    fit_arm = [poly.add(p, constant(-F(ref))) for p, ref in zip(point, port['point_reference_xyz_mm'], strict=True)]
    fitting = [poly.add(constant(own[i]), poly.scaled(fit_arm[k], own[3+j]/1000),
                       poly.scaled(fit_arm[j], -own[3+k]/1000))
               for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1))]
    return poly.add(*(poly.scaled(poly.add(a, poly.scaled(b, -1)), F(n))
                      for a, b, n in zip(fitting, wood, normal, strict=True)))


def segment_mode(station, stations):
    if station < stations[0]:
        return 'before', 0
    if station > stations[-1]:
        return 'after', len(stations)-2
    return 'interior', next(i for i in range(len(stations)-1) if stations[i] <= station <= stations[i+1])


def pieces(domain, timber, geometry, poly):
    polygon = [tuple(map(F, p)) for p in domain['polygon']]
    station = station_polynomial(world_polynomials(domain), timber, poly)
    require(all(i+j <= 1 for i, j in station), 'affine station trace required')
    form = [station.get(ZERO, F(0)), station.get((1, 0), F(0)), station.get((0, 1), F(0))]
    stations = list(map(F, timber['stations']))
    require(len(stations) >= 2 and all(a < b for a, b in pairwise(stations)),
            'ordered source beam stations required')
    if form[1] == form[2] == 0:
        mode, segment = segment_mode(form[0], stations)
        return [{'mode': mode, 'segment': segment, 'polygon': polygon,
                 'outer_area': geometry.moments(polygon, F(0))[0]}]
    definitions = [('before', 0, None, stations[0])]
    definitions += [('interior', i, a, b) for i, (a, b) in enumerate(pairwise(stations))]
    definitions += [('after', len(stations)-2, stations[-1], None)]
    result = []
    for mode, segment, low, high in definitions:
        region = polygon
        if low is not None:
            region = geometry.clip(region, (form[0]-low, form[1], form[2]))
        if high is not None:
            region = geometry.clip(region, (high-form[0], -form[1], -form[2]))
        area = geometry.moments(region, F(0))[0]
        if area > 0:
            result.append({'mode': mode, 'segment': segment, 'polygon': previous().hull(region), 'outer_area': area})
    require(sum(r['outer_area'] for r in result) == geometry.moments(polygon, F(0))[0],
            'station pieces must cover the complete outer polygon exactly')
    return result


def polynomial_bounds(polynomial, box, method):
    x0, x1, y0, y1 = map(F, box)
    require(x0 < x1 and y0 < y1, 'positive polynomial bounding box required')
    mx, hx, my, hy = (x0+x1)/2, (x1-x0)/2, (y0+y1)/2, (y1-y0)/2
    normalized = {}
    for (i, j), value in polynomial.items():
        require(0 <= i <= 2 and 0 <= j <= 2, 'quadratic-coordinate trace required')
        for a in range(i+1):
            for b in range(j+1):
                contribution = value*math.comb(i, a)*mx**(i-a)*hx**a*math.comb(j, b)*my**(j-b)*hy**b
                normalized[a, b] = normalized.get((a, b), F(0))+contribution
    values = method.bernstein(normalized)
    return min(v for row in values for v in row), max(v for row in values for v in row)


def bounding_box(polygon):
    return min(p[0] for p in polygon), max(p[0] for p in polygon), min(p[1] for p in polygon), max(p[1] for p in polygon)


def material_witness(piece, holes, method, subdivisions=8, closure_gate=F(1, 10**8)):
    """Floating grid selects only; exact containment and Bernstein signs decide."""
    base, poly = previous(), method.poly
    polygon, polynomial = piece['polygon'], piece['polynomial']
    box = bounding_box(polygon)
    coefficients = [(i, j, float(c)) for (i, j), c in polynomial.items()]
    candidates = []
    for i in range(subdivisions+1):
        for j in range(subdivisions+1):
            point = (box[0]+(box[1]-box[0])*F(2*i+1, 2*subdivisions+2),
                     box[2]+(box[3]-box[2])*F(2*j+1, 2*subdivisions+2))
            if base.inside(polygon, point) and all((point[0]-x)**2+(point[1]-y)**2 > r*r for x, y, r in holes):
                score = sum(c*float(point[0])**i*float(point[1])**j for i, j, c in coefficients)
                candidates.append((score, point))
    if not candidates:
        return None
    _, point = min(candidates)
    if poly.evaluate(polynomial, point) >= -closure_gate:
        return None
    half = min(box[1]-box[0], box[3]-box[2])/32
    for _ in range(24):
        inner = point[0]-half, point[0]+half, point[1]-half, point[1]+half
        corners = [(x, y) for x in inner[:2] for y in inner[2:]]
        if all(base.inside(polygon, p) for p in corners) and all(base.box_hole_clearance(inner, h) > 0 for h in holes):
            lower, upper = polynomial_bounds(polynomial, inner, method)
            if upper < -closure_gate:
                area = 4*half*half
                return {'box_xy_mm': list(map(str, inner)), 'gap_interval_mm': list(map(str, (lower, upper))),
                        'exact_material_area_mm2': str(area), 'exact_penetration_lower_mm': str(-upper),
                        'exact_normal_force_lower_n': str(piece['density']*area*(-upper)),
                        'exact_energy_lower_nmm': str(piece['density']*area*upper**2/2),
                        'selection_grid_is_not_the_certificate': True}
        half /= 2
    return None


def trace(domain, timber, port, fitting_indices, q, normal, density, method, subdivisions=8):
    density = F(density)
    require(density > 0 and len(normal) == 3 and len(fitting_indices) == 6, 'own positive normal law and fitting node required')
    point = world_polynomials(domain)
    regions = pieces(domain, timber, method.geometry, method.poly)
    holes = [tuple(map(F, h)) for h in domain['holes']]
    energy_upper, force_upper, witness = F(0), F(0), None
    moment_lower, moment_upper = [F(0)]*3, [F(0)]*3
    records = []
    for region in regions:
        polynomial = gap_polynomial(point, timber, port, fitting_indices, q, normal,
                                    region['mode'], region['segment'], method.poly)
        region.update(polynomial=polynomial, density=density)
        lower, upper = polynomial_bounds(polynomial, bounding_box(region['polygon']), method)
        force = density*region['outer_area']*max(-lower, 0)
        energy = density*region['outer_area']*max(-lower, 0)**2/2
        force_upper += force; energy_upper += energy
        for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
            arm = method.poly.add(method.poly.scaled(method.poly.add(point[j], constant(-F(domain['origin_xyz_mm'][j]))), F(normal[k])),
                                  method.poly.scaled(method.poly.add(point[k], constant(-F(domain['origin_xyz_mm'][k]))), -F(normal[j])))
            values = [method.poly.evaluate(arm, p) for p in region['polygon']]
            moment_lower[i] += min(F(0), min(values)*force)
            moment_upper[i] += max(F(0), max(values)*force)
        local = material_witness(region, holes, method, subdivisions)
        if local and (witness is None or F(local['exact_energy_lower_nmm']) > F(witness['exact_energy_lower_nmm'])):
            witness = dict(local, piece_index=len(records))
        records.append({'mode': region['mode'], 'segment': region['segment'],
                        'outer_polygon_xy_mm': [[str(v) for v in p] for p in region['polygon']],
                        'gap_polynomial_ij_mm': [[i, j, str(v)] for (i, j), v in sorted(polynomial.items())],
                        'outer_area_mm2': str(region['outer_area']), 'gap_interval_mm': list(map(str, (lower, upper))),
                        'exact_normal_force_upper_n': str(force), 'exact_energy_upper_nmm': str(energy)})
    require(witness is None or (F(witness['exact_normal_force_lower_n']) <= force_upper
                                and F(witness['exact_energy_lower_nmm']) <= energy_upper),
            'inner/outer contact bounds must be ordered')
    return {'pieces': records, 'material_witness': witness, 'exact_normal_force_upper_n': str(force_upper),
            'exact_energy_upper_nmm': str(energy_upper),
            'force_on_first_xyz_interval_n': [[str(min(F(0), F(n)*force_upper)), str(max(F(0), F(n)*force_upper))] for n in normal],
            'moment_on_first_about_patch_origin_xyz_interval_nmm': [[str(a), str(b)] for a, b in zip(moment_lower, moment_upper, strict=True)],
            'changed_law_equilibrium_or_physical_demand_qualified': False}


def source_gap(point, timber, port, fitting_indices, q, normal, poly):
    point = list(map(F, point))
    station = sum((F(a)*(p-F(s)) for a, p, s in zip(timber['axis'], point, timber['start'], strict=True)), F(0))
    stations = list(map(F, timber['stations']))
    mode, segment = segment_mode(station, stations)
    polynomial = gap_polynomial([constant(v) for v in point], timber, port, fitting_indices, q, normal, mode, segment, poly)
    require(set(polynomial) <= {ZERO}, 'constant source point must have a scalar gap')
    return polynomial.get(ZERO, F(0))


def run(reference):
    base, pins = previous(), {}
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_current_normal_patch_trace_inputs/v1'
            and inputs['implementation'] == {'path': str(OWN.relative_to(ROOT)), 'sha256': LOADED_SHA}
            and inputs['runtime'] == {'python': platform.python_version(), 'numpy': np.__version__}
            and type(inputs['witness_grid_subdivisions']) is int and inputs['witness_grid_subdivisions'] == 8
            and inputs['opening_gate_mm'] == '1/100000000',
            'exact trace input, driver and runtime required')
    for ref in (inputs['implementation'], inputs['tests'], PREVIOUS, *inputs['source_kinematics'].values()):
        base.captured(ref, pins)
    prior = json.loads(base.captured(inputs['normal_patch_result'], pins))
    require(prior['current_bolt_count'] == 100 and prior['current_screw_count'] == 66 and len(prior['records']) == 88,
            'complete unchanged current patch packet required')
    for path, digest in prior['source_sha256'].items():
        base.captured({'path': path, 'sha256': digest}, pins)
    response = json.loads(base.captured(inputs['current_response'], pins))
    prior_inputs = json.loads(base.captured(prior['inputs'], pins))
    require(inputs['current_response'] == prior_inputs['current_response'] and len(response['cases']) == 6
            and response['geometry_revision'] == prior['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and response['hardware_revision'] == prior['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and response['extra_grid'] is prior['extra_grid'] is False, 'same retained six-case authority required')
    method = methods(inputs, pins)
    domains = {r['id']: r for r in prior['records']}
    records, common_chart, errors = [], None, []
    for binding in response['cases']:
        field = json.loads(base.captured(binding['field'], pins))
        manifest = json.loads(base.captured(field['operator_bundle']['manifest'], pins))
        array_bytes = base.captured(field['operator_bundle']['arrays'], pins)
        chart = manifest['coordinate_map']
        require(chart['rotation_scale'] == 1000. and chart['final_ndof'] == len(field['response']['q']) == 9350
                and len(chart['timber']) == len(chart['four_port_fittings']) == 22
                and field['case_id'] == binding['case_id'] and field['state_id'] == binding['state_id']
                and len(field['source_inputs']['shafts']) == 100 and len(field['panel_screw_actions']) == 66
                and not any(field['release'].values()),
                'own current coordinate chart, response and hardware required')
        if common_chart is None:
            common_chart = chart
        require(chart == common_chart, 'shared geometry requires identical current charts')
        q = list(map(F, field['response']['q']))
        rows = {r['descriptor']['id']: r for r in manifest['partitions']['contacts'] if r['descriptor']['kind'] == 'flange_contact'}
        actions = {r['id']: r for r in field['contact_actions'] if r['kind'] == 'flange_contact'}
        require(len(rows) == len(actions) == 352, 'complete source flange centroid inventory required')
        with np.load(io.BytesIO(array_bytes), allow_pickle=False) as arrays:
            for patch in field['source_inputs']['flange_shared_face_patches']:
                saved = domains[patch['id']]
                require(patch['trimmed_region_signature_sha256'] == saved['trimmed_region_signature_sha256'],
                        'own retained analytic patch mapping required')
                fitting = chart['four_port_fittings'][patch['first']]
                port = next(p for p in fitting['ports'] if p['id'] == patch['source_owned_port_id'])
                indices = fitting['dof_indices'][6*port['port_index']:6*(port['port_index']+1)]
                timber = chart['timber'][patch['second']]
                checked_rows, normal = [], None
                for cell in patch['cells']:
                    identity = patch['id'].rsplit('/timber-face/', 1)[0]+'/'+cell['id']
                    row = rows[identity]; desc, matrix = row['descriptor'], row['B']
                    if normal is None:
                        normal = desc['direction_xyz']
                    require(desc['direction_xyz'] == normal and matrix['shape'] == [1, 9350], 'own common normal and scalar source map required')
                    coefficients, columns = arrays[matrix['data']], arrays[matrix['indices']]
                    stored = sum((F(float(v))*q[int(i)] for v, i in zip(coefficients, columns, strict=True)), F(0))
                    gap = source_gap(cell['point_xyz_mm'], timber, port, indices, q, normal, method.poly)
                    force_error = abs(F(desc['stiffness'])*max(-gap, 0)-F(actions[identity]['compression_n']))
                    map_error = abs(stored-gap)
                    require(map_error < F(1, 10**9) and force_error < F(1, 10**7), 'literal source gap/force recovery failed')
                    checked_rows.append({'id': identity, 'exact_gap_mm': str(gap), 'exact_stored_Bq_mm': str(stored),
                                         'exact_map_error_mm': str(map_error), 'exact_force_error_n': str(force_error)})
                    errors.append((map_error, force_error))
                result = trace(saved['analytic_domain'], timber, port, indices, q, normal,
                               saved['declared_existing_stiffness_n_mm3'], method, inputs['witness_grid_subdivisions'])
                records.append({'case_id': binding['case_id'], 'state_id': binding['state_id'], 'patch_id': patch['id'],
                                'field': binding['field'], 'contact_director_xyz': normal, 'source_centroids': checked_rows,
                                'source_all_centroids_open_above_gate': min(F(r['exact_gap_mm']) for r in checked_rows) > F(inputs['opening_gate_mm']),
                                'pose_is_changed_law_equilibrium': False, **result})
        print(json.dumps({'case': binding['case_id'], 'patches': 88}), flush=True)
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    require(hashlib.sha256(OWN.read_bytes()).hexdigest() == LOADED_SHA and len(records) == 528, 'complete unchanged trace calculation required')
    return {'schema': 'eoere_current_normal_patch_trace/v1', 'inputs': reference, 'source_sha256': pins,
            'geometry_revision': 'eoere-raised-kicker-screws-v1', 'hardware_revision': 'eoere-selected-purchase-hardware-v1',
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False, 'records': records,
            'maximum_exact_source_map_error_mm': str(max(r[0] for r in errors)),
            'maximum_exact_source_force_error_n': str(max(r[1] for r in errors)),
            'missed_positive_area_patch_states': sum(r['source_all_centroids_open_above_gate'] and r['material_witness'] is not None for r in records),
            'new_native_frame_CAD_or_equilibrium_solve': False, 'physical_demand_bounds_established': False,
            'complete_joint_or_member_resistance_qualified': False, 'actual_observations': None,
            'structural_acceptance': False, 'limits': inputs['limits']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'preserve issued trace evidence')
    result = run({'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), 'patch_states': len(result['records'])}))


if __name__ == '__main__':
    main()
