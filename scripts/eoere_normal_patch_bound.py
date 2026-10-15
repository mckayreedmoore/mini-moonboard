"""Test whether scaling centroid contacts can enclose a continuous normal law.

This constructs local affine-gap controls on the retained nominal patches.
They are not candidate response states or whole-frame energy counterexamples.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import itertools
import json
import math
import platform
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(value):
    require(not isinstance(value, bool), 'finite real scalar required')
    try:
        return F(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError('finite real scalar required') from exc


def captured(reference, pins):
    path = (ROOT/reference['path']).resolve()
    require(path.is_relative_to(ROOT), 'repository source required')
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == reference['sha256'] and pins.get(reference['path'], digest) == digest,
            'source changed: '+reference['path'])
    pins[reference['path']] = digest
    return data


def methods(inputs, pins):
    ref = inputs['definition_loader']
    module = ModuleType('_eoere_normal_patch_definitions')
    module.__file__ = str(ROOT/ref['path'])
    exec(compile(captured(ref, pins), module.__file__, 'exec'), module.__dict__)  # noqa: S102 - authenticated buffer
    namespace = {'F': F, 'np': np, 'math': math, 'itertools': itertools,
                 'require': require, 'cache': functools.cache}
    for role, functions in [('rational', ('rational', 'rectangle', 'robust_boxes')),
                            ('polygon', ('clip', 'moments')), ('pi', ('atan_series', 'pi_bounds'))]:
        module.definitions(inputs['pure_helpers'][role], functions, (), namespace, pins)
    return SimpleNamespace(**{k: namespace[k] for k in ('clip', 'moments', 'robust_boxes', 'pi_bounds')})


def turn(a, b, c):
    return (b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])


def hull(points):
    points = sorted({tuple(map(exact, p)) for p in points})
    require(len(points) >= 3 and all(len(p) == 2 for p in points), 'positive planar polygon required')
    halves = []
    for order in (points, points[::-1]):
        half = []
        for point in order:
            while len(half) >= 2 and turn(half[-2], half[-1], point) <= 0:
                half.pop()
            half.append(point)
        halves.append(half[:-1])
    result = halves[0]+halves[1]
    require(len(result) >= 3, 'noncollinear polygon required')
    return result


def value(form, point):
    return form[0]+form[1]*point[0]+form[2]*point[1]


def inside(polygon, point, margin=F(0)):
    return all((b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])
               > margin*(abs(b[0]-a[0])+abs(b[1]-a[1]))
               for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True))


def box_hole_clearance(box, hole):
    x0, x1, y0, y1 = box
    x, y, radius = hole
    distances = [max(lo-center, center-hi, F(0)) for center, lo, hi in ((x, x0, x1), (y, y0, y1))]
    return sum((d*d for d in distances), F(0))-radius*radius


def witness(polygon, holes, samples, stiffness, method, opening=F(1, 100)):
    """Exact finite-area control: every old sample opens, a material box closes."""
    polygon = [tuple(map(exact, p)) for p in polygon]
    holes = [tuple(map(exact, h)) for h in holes]
    samples = [tuple(map(exact, p)) for p in samples]
    stiffness, opening = exact(stiffness), exact(opening)
    require(stiffness > 0 and opening > 0 and samples and len(polygon) >= 3
            and all(len(p) == 2 for p in [*polygon, *samples])
            and all(len(h) == 3 and h[2] > 0 for h in holes), 'positive complete patch control required')
    require(all(turn(a, b, c) > 0 for a, b, c in
                zip(polygon, polygon[1:]+polygon[:1], polygon[2:]+polygon[:2], strict=True)),
            'strict counterclockwise convex outer polygon required')
    require(all(inside(polygon, p) and all((p[0]-h[0])**2+(p[1]-h[1])**2 > h[2]**2 for h in holes)
                for p in samples), 'all samples must be in the material interior')
    options = []
    for coordinate in range(2):
        for sign in (-1, 1):
            outer = max(sign*p[coordinate] for p in polygon)
            sampled = max(sign*p[coordinate] for p in samples)
            options.append((outer-sampled, coordinate, sign, outer, sampled))
    distance, coordinate, sign, outer, sampled = max(options)
    require(distance > 0, 'no separated support direction found')
    level = (outer+sampled)/2
    form = [opening*level/(distance/2), F(0), F(0)]
    form[coordinate+1] = -opening*sign/(distance/2)
    threshold = (3*outer+sampled)/4
    plane = [-threshold, F(0), F(0)]
    plane[coordinate+1] = F(sign)
    active = method.clip(polygon, plane)
    # Remove duplicate/collinear clipping vertices before the existing box helper.
    active = hull(active)
    box, _ = method.robust_boxes(active, F(1, 10**8), F(1, 10**5))
    corners = [(x, y) for x in box[:2] for y in box[2:]]
    require(all(inside(polygon, p) for p in corners)
            and all(box_hole_clearance(box, h) > 0 for h in holes),
            'positive-area witness box must lie entirely in material')
    sample_gaps = [value(form, p) for p in samples]
    penetration = -max(value(form, p) for p in corners)
    area = (box[1]-box[0])*(box[3]-box[2])
    require(min(sample_gaps) >= opening and penetration > opening/2 and area > 0,
            'strict opening and finite-area compression controls required')
    energy = stiffness*area*penetration**2/2
    force = stiffness*area*penetration
    return {'gap_coefficients_1_x_y': list(map(str, form)), 'sample_gaps_mm': list(map(str, sample_gaps)),
            'selected_support_axis': coordinate, 'selected_support_sign': sign,
            'exact_unsampled_support_distance_mm': str(distance),
            'inner_material_box_xy_mm': list(map(str, box)), 'exact_box_area_mm2': str(area),
            'exact_penetration_lower_mm': str(penetration),
            'exact_distributed_energy_lower_nmm': str(energy),
            'exact_distributed_normal_force_lower_n': str(force),
            'sampled_contact_energy_nmm': 0, 'sampled_contact_force_n': 0,
            'finite_local_multiplicative_upper_exists': False,
            'is_current_case_response_or_whole_frame_counterexample': False}


def geometry(patch, method):
    """Declare an analytic polygon-minus-two-disks from the frozen signature.

    Projection/rounding and identity gates establish a nominal model mapping,
    not a certified tolerance envelope for the CAD or a physical observation.
    """
    source = patch['trimmed_region_geometry']
    digest = hashlib.sha256(json.dumps(source, sort_keys=True, separators=(',', ':'),
                                      ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    require(digest == patch['trimmed_region_signature_sha256'], 'trimmed patch signature changed')
    lines = [e for e in source['edge_signatures'] if e['curve_type'] == 'LINE']
    circles = [e for e in source['edge_signatures'] if e['curve_type'] == 'CIRCLE']
    require(len(lines) in (4, 5) and len(circles) == 2
            and len(lines)+2 == len(source['edge_signatures']), 'complete convex polygon/two-full-hole domain required')
    origin = np.asarray(patch['centroid_xyz_mm'])
    normal = np.asarray(patch['normal_from_second_to_first_xyz'])
    normal = normal/np.linalg.norm(normal)
    edge = max(lines, key=lambda e: e['length_mm'])
    direction = np.subtract(*edge['vertex_xyz_mm'])
    direction -= normal*float(direction@normal)
    direction /= np.linalg.norm(direction)
    across = np.cross(normal, direction)
    basis = np.asarray([direction, across])

    def project(point):
        point = np.asarray(point)
        require(abs(float((point-origin)@normal)) < 2e-6, 'source point leaves the nominal plane')
        return tuple(F(str(round(float(x), 12))) for x in basis@(point-origin))

    endpoints = [[project(p) for p in e['vertex_xyz_mm']] for e in lines]
    polygon = hull(p for pair in endpoints for p in pair)
    require(len(polygon) == len(lines) and
            {frozenset(pair) for pair in endpoints} ==
            {frozenset((a, b)) for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True)},
            'all outer edges must match the convex hull; no concavity may be filled')
    holes = []
    pi = method.pi_bounds()
    for edge in circles:
        radius = min((F(5), F(1651, 320)), key=lambda r: abs(2*math.pi*float(r)-edge['length_mm']))
        require(abs(2*math.pi*float(radius)-edge['length_mm']) < 2e-7,
                'current full circular 5/5.159375-mm holes required')
        center = project(edge['center_xyz_mm'])
        for a, b in zip(polygon, polygon[1:]+polygon[:1], strict=True):
            cross = (b[0]-a[0])*(center[1]-a[1])-(b[1]-a[1])*(center[0]-a[0])
            require(cross > 0 and cross**2 > radius**2*((b[0]-a[0])**2+(b[1]-a[1])**2),
                    'each complete disk must lie strictly inside the outer polygon')
        holes.append((*center, radius))
    require(sum((a-b)**2 for a, b in zip(holes[0][:2], holes[1][:2], strict=True)) > (holes[0][2]+holes[1][2])**2,
            'hole disks must be disjoint')
    area, mx, my = method.moments(polygon, F(0))
    pi_mid = sum(pi)/2
    for x, y, radius in holes:
        void = pi_mid*radius**2
        area -= void; mx -= void*x; my -= void*y
    area_error = abs(float(area)-patch['area_mm2'])
    centroid_error = max(abs(float(mx/area)), abs(float(my/area)))
    require(area > 0 and area_error < 2e-5 and centroid_error < 2e-6,
            'declared analytic patch must match recorded area and centroid')
    return {'polygon': polygon, 'holes': holes, 'samples': [project(c['point_xyz_mm']) for c in patch['cells']],
            'origin_xyz_mm': origin.tolist(), 'basis_rows_xyz': basis.tolist(),
            'area_identity_error_mm2': area_error, 'centroid_identity_error_mm': centroid_error}


def run(reference):
    pins = {}
    inputs = json.loads(captured(reference, pins))
    require(inputs['schema'] == 'eoere_current_normal_patch_bound_inputs/v1'
            and inputs['runtime'] == {'python': platform.python_version(), 'numpy': np.__version__}
            and inputs['implementation'] == {'path': str(OWN.relative_to(ROOT)), 'sha256': LOADED_SHA},
            'exact current normal-patch input and executing implementation required')
    for ref in (inputs['implementation'], inputs['tests'], inputs['prior_traction_result'], inputs['prior_steel_result']):
        captured(ref, pins)
    method = methods(inputs, pins)
    response = json.loads(captured(inputs['current_response'], pins))
    index = json.loads(captured(inputs['revision_index'], pins))
    require(index['current_response']['cases'] == inputs['current_response']
            and response['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and response['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and response['extra_grid'] is False and len(response['cases']) == 6,
            'retained six-case authority required')
    for role in ('geometry', 'hardware_model'):
        captured(index['current_response'][role], pins)
    fields = [json.loads(captured(row['field'], pins)) for row in response['cases']]
    first = fields[0]['source_inputs']
    patches, domains = first['flange_shared_face_patches'], first['flange_domains']
    require(len(patches) == len(domains) == 88 and len({p['id'] for p in patches}) == 88,
            'complete 88 half-flange patches required')
    for field, binding in zip(fields, response['cases'], strict=True):
        require(field['case_id'] == binding['case_id'] and field['state_id'] == binding['state_id']
                and len(field['source_inputs']['shafts']) == 100 and len(field['panel_screw_actions']) == 66
                and len(field['fitting_operator_descriptors']) == 22
                and field['source_inputs']['flange_shared_face_patches'] == patches
                and field['source_inputs']['flange_domains'] == domains and not any(field['release'].values()),
                'all own current cases must retain geometry, contact priors and hardware')
        descriptors = {r['id']: r for r in field['reference_interaction_descriptors'] if r['kind'] == 'flange_contact'}
        require(len(descriptors) == 352, 'complete 352 flange centroid contacts required')
        for patch in patches:
            domain = next(d for d in domains if d['id'] == patch['id'].rsplit('/timber-face/', 1)[0])
            stiffness = domain['declared_flange_area_density_n_mm3']
            require(stiffness > 0, 'positive existing flange foundation prior required')
            for cell in patch['cells']:
                identity = domain['id']+'/'+cell['id']
                row = descriptors[identity]
                require(row['point_xyz_mm'] == cell['point_xyz_mm'] and
                        row['source_trimmed_region_signature_sha256'] == patch['trimmed_region_signature_sha256']
                        and abs(row['stiffness']-stiffness*cell['area_mm2']) < 1e-8,
                        'source stiffness must remain the own area-weighted centroid prior')
    records = []
    for patch in patches:
        domain = next(d for d in domains if d['id'] == patch['id'].rsplit('/timber-face/', 1)[0])
        data = geometry(patch, method)
        proof = witness(data['polygon'], data['holes'], data['samples'],
                        domain['declared_flange_area_density_n_mm3'], method, inputs['sample_opening_mm'])
        records.append({'id': patch['id'], 'first': patch['first'], 'second': patch['second'],
                        'trimmed_region_signature_sha256': patch['trimmed_region_signature_sha256'],
                        'declared_existing_stiffness_n_mm3': domain['declared_flange_area_density_n_mm3'],
                        'analytic_domain': {k: ([[str(v) for v in row] for row in value]
                                                if k in ('polygon', 'holes', 'samples') else value)
                                            for k, value in data.items()}, 'certificate': proof})
    for p, digest in tuple(pins.items()):
        captured({'path': p, 'sha256': digest}, pins)
    require(hashlib.sha256(OWN.read_bytes()).hexdigest() == LOADED_SHA, 'executing producer changed')
    return {'schema': 'eoere_current_normal_patch_bound/v1', 'inputs': reference, 'source_sha256': pins,
            'geometry_revision': response['geometry_revision'], 'hardware_revision': response['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'records': records, 'patch_controls': len(records), 'verified_case_patch_occurrences': 528,
            'source_centroid_points_per_case': 352, 'existing_cases_or_forces_changed': False,
            'new_native_frame_CAD_or_equilibrium_solve': False, 'physical_demand_bounds_established': False,
            'complete_joint_or_member_resistance_qualified': False, 'physical_failure_established': False,
            'actual_observations': None, 'structural_acceptance': False, 'limits': inputs['limits']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'preserve issued patch-bound evidence')
    ref = {'path': str(args.inputs.resolve().relative_to(ROOT)),
           'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(ref)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), 'patch_controls': result['patch_controls']}))


if __name__ == '__main__':
    main()
