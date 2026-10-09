"""Pure finite-envelope screen for the four lower cleat/post bolt Z coordinates.

No CAD imports or geometry queries. A circular cylinder/cone or regular hex
is contained in the capsule of its finite axis and maximum radial extent.
Thus distance between finite axes minus the two radii is a conservative
lower bound on solid separation. This deliberately overbounds finite ends.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BASE = ROOT / 'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1'
GEOMETRY = BASE / 'occupied-geometry-v1/geometry.json'
GEOMETRY_SHA = '552870d3ff7c7f2c678ef917b7cee037614c11cef180126d9cf06ab8d2cab3ec'
LAYOUT = ROOT / 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/mixed-offset-rows-shallow-wires-v4.json'
PRIOR = BASE / 'cleat-corners-v1/plan.json'
PRIOR_SHA = '810f8cc24f477ff8c1ea8010cda96e5664113fadb50fd32d137b766964873f6c'


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unit(direction):
    length = math.sqrt(sum(v * v for v in direction))
    require(abs(length - 1.) < 1e-8, 'source direction not unit within recorded precision')
    return [v / length for v in direction]


def primitive(name, role, point, direction, near, far, radius):
    direction = unit(direction)
    return {'id': name, 'role': role,
            'start_xyz_mm': [p + near * d for p, d in zip(point, direction, strict=True)],
            'end_xyz_mm': [p + far * d for p, d in zip(point, direction, strict=True)],
            'containing_capsule_radius_mm': radius}


def axis_distance(first, second):
    """Exact finite-axis distance: first X; second X or constant-X/YZ.

    X and YZ minimizations separate. In the YZ case the second parameter is
    its clamped orthogonal projection; X is its constant X to first interval.
    In the parallel case each coordinate is a point or independent interval.
    """
    a, b = first['start_xyz_mm'], first['end_xyz_mm']
    c, d = second['start_xyz_mm'], second['end_xyz_mm']
    require(a[1:] == b[1:], 'first finite axis must be parallel to X')
    lo, hi = sorted((a[0], b[0]))
    if c[1:] == d[1:]:
        otherlo, otherhi = sorted((c[0], d[0]))
        dx = max(lo - otherhi, otherlo - hi, 0.)
        dyz2 = sum((a[i] - c[i]) ** 2 for i in (1, 2))
    else:
        require(c[0] == d[0], 'second axis must be X or constant-X/YZ')
        dx = max(lo - c[0], c[0] - hi, 0.)
        denominator = sum((d[i] - c[i]) ** 2 for i in (1, 2))
        t = max(0., min(1., sum((a[i] - c[i]) * (d[i] - c[i]) for i in (1, 2)) / denominator))
        dyz2 = sum((a[i] - c[i] - t * (d[i] - c[i])) ** 2 for i in (1, 2))
    return math.sqrt(dx * dx + dyz2)


def pair(first, second):
    distance = axis_distance(first, second)
    return {'first': first['id'], 'first_role': first['role'],
            'second': second['id'], 'second_role': second['role'],
            'finite_axis_distance_mm': distance,
            'capsule_separation_lower_bound_mm': distance - first['containing_capsule_radius_mm'] - second['containing_capsule_radius_mm']}


def hardware(axis, z=None, bore=False):
    point = list(axis['point_xyz_mm'])
    if z is not None:
        point[2] = z
    h, grip = axis['hardware_scenario'], axis['grip_mm']
    start = -axis['before_plate_mm'] - h['washer_thickness_mm']
    nut = grip + axis['after_plate_mm'] + h['washer_thickness_mm']
    length = axis['nominal_under_head_length_mm']
    records = [('shaft', start, start + length, axis['diameter_mm'] / 2),
               ('head', start - h['head_height_mm'], start, h['hex_across_flats_mm'] / math.sqrt(3)),
               ('head_washer', start, start + h['washer_thickness_mm'], h['washer_od_mm'] / 2),
               ('nut_washer', grip + axis['after_plate_mm'], nut, h['washer_od_mm'] / 2),
               ('nut', nut, nut + h['nut_height_mm'], h['hex_across_flats_mm'] / math.sqrt(3))]
    if bore:
        records.append(('wood_bore_cutter', -1., grip + 1., axis['bore_diameter_mm'] / 2))
    return [primitive(axis['id'], role, point, axis['direction_xyz'], near, far, radius)
            for role, near, far, radius in records]


def known_answers():
    x = primitive('a', 'axis', [0., 0., 0.], [1., 0., 0.], 0., 10., 0.)
    require(axis_distance(x, primitive('b', 'axis', [5., 3., 4.], [1., 0., 0.], 0., 2., 0.)) == 5., 'parallel coupon')
    require(axis_distance(x, primitive('b', 'axis', [12., 0., 0.], [0., 1., 0.], 3., 7., 0.)) == math.sqrt(13.), 'finite outside-X coupon')
    require(axis_distance(x, primitive('b', 'axis', [5., 3., 4.], [0., -.6, -.8], 0., 10., 0.)) < 1e-14, 'inclined YZ interior coupon')
    require(axis_distance(x, primitive('b', 'axis', [5., 3., 4.], [0., .6, .8], 0., 10., 0.)) == 5., 'finite endpoint coupon')
    return 4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(sha(GEOMETRY) == GEOMETRY_SHA and sha(PRIOR) == PRIOR_SHA, 'frozen geometry/prior changed')
    geometry = json.loads(GEOMETRY.read_bytes())
    pins = dict(geometry['source_sha256'])
    for path, expected in ((GEOMETRY, GEOMETRY_SHA), (PRIOR, PRIOR_SHA), (OWN, LOADED_SHA)):
        key = str(path.relative_to(ROOT))
        require(key not in pins or pins[key] == expected, 'source pin contradiction')
        pins[key] = expected
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, 'source differs before coordinate access: ' + path)
    require(pins['scripts/thin_bolted_occupied.py'] == 'ffe285122150654f97dba1682d1f96da9aab470547bba6e3173207a03a449b77', 'screw/hardware recipe source differs')
    screws = json.loads(LAYOUT.read_bytes())['screw_axes']
    axes = geometry['axes']
    lower = [a for a in axes if a['id'].startswith('cleat_post_bolt_')]
    require(len(screws) == 66 and len(axes) == 100 and len(lower) == 4, 'source census')
    expected_ids = {f'cleat_post_bolt_{side}_{number}' for side in ('left', 'right') for number in (1, 2)}
    require({a['id'] for a in lower} == expected_ids, 'lower selector differs')
    require(all(a['point_xyz_mm'][2] == 189.3 and a['point_xyz_mm'][1] in (-131.25, -80.45) and a['diameter_mm'] == 9.525 and a['bore_diameter_mm'] == 10.31875 for a in lower), 'original lower geometry differs')
    fixed = [a for a in axes if a['id'] not in expected_ids]
    screw_primitives = [primitive(s['axis_id'], role, s['origin_xyz_mm'], s['direction_xyz'], near, far, radius)
                        for s in screws for role, near, far, radius in (('screw_head_containing_cylinder', 0., 3., 4.5), ('screw_body', 3., 63.5, 2.5))]
    fixtures = known_answers()
    scans = []
    for z in (189.3, 199., 199.7, 200., 200.8, 201., 210., 220.):
        candidates = [p for a in lower for p in hardware(a, z, bore=True)]
        comparisons = [pair(a, b) for a in candidates for b in screw_primitives]
        scans.append({'common_Z_mm': z, 'comparison_count': len(comparisons),
                      'minimum': min(comparisons, key=lambda r: r['capsule_separation_lower_bound_mm']),
                      'all_screw_envelope_separation_bounds_positive': all(r['capsule_separation_lower_bound_mm'] > 0 for r in comparisons),
                      'post_top_end_mm': 238.9 - z, 'cleat_bottom_end_mm': z - 139.7})
    z = 200.
    candidates = [p for a in lower for p in hardware(a, z, bore=True)]
    screw_checks = [pair(a, b) for a in candidates for b in screw_primitives]
    fixed_checks = [pair(a, b) for a in candidates for fixed_axis in fixed for b in hardware(fixed_axis, bore=True)]
    require(all(r['capsule_separation_lower_bound_mm'] > 0 for r in screw_checks + fixed_checks), 'chosen nominal envelope has unresolved intersection')
    role_minima = {role: min((r for r in screw_checks if r['first_role'] == role), key=lambda r: r['capsule_separation_lower_bound_mm']) for role in {p['role'] for p in candidates}}
    solids = {r['id']: r for r in geometry['finished_solids']}
    receiver_rows = []
    for a in lower:
        p = [*a['point_xyz_mm'][:2], z]
        for member in a['receivers']:
            bb = solids[member]['bounds_xyz_mm']
            ymargin = min(p[1] - bb[1][0], bb[1][1] - p[1])
            zmargin = min(z - bb[2][0], bb[2][1] - z)
            receiver_rows.append({'axis_id': a['id'], 'member': member, 'unchanged_recorded_bounds_xyz_mm': bb,
                'Y_edge_center_distance_mm': ymargin, 'Z_min_end_center_distance_mm': zmargin,
                'wood_bore_Y_margin_mm': ymargin - a['bore_diameter_mm'] / 2,
                'wood_bore_Z_margin_mm': zmargin - a['bore_diameter_mm'] / 2,
                'washer_outer_radius_Y_margin_mm': ymargin - a['hardware_scenario']['washer_od_mm'] / 2,
                'washer_outer_radius_Z_margin_mm': zmargin - a['hardware_scenario']['washer_od_mm'] / 2,
                'complete_group_or_strength_disposition': None})
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, 'source differs after coordinate screen: ' + path)
    require(sha(OWN) == LOADED_SHA and 'cadquery' not in sys.modules, 'loaded source changed or CAD imported')
    result = {'schema': 'eoere_lower_bolt_common_Z_pure_proposal/v2', 'status': 'PROPOSED_NOT_ADOPTED',
        'source_sha256': pins, 'source_pins_before_after_unchanged': True,
        'execution': {'actual_orig_argv': sys.orig_argv, 'cwd': str(Path.cwd()), 'python': sys.version, 'PYTHONPATH': os.environ.get('PYTHONPATH'),
                      'CAD_import_query_native_q_K_force_or_response': False, 'known_answer_checks': fixtures},
        'fixed_scope': {'Hillman_axes_unchanged': 66, 'other_bolt_axes_unchanged': 96, 'existing_stock_sections_changed': False,
                       'cleat_bounds_changed': False, 'lower_pair_Y_mm': [-131.25, -80.45], 'main_depth_shift_mm': 0.},
        'proposed_axes': [{**a, 'point_xyz_mm': [*a['point_xyz_mm'][:2], z], 'original_point_xyz_mm': a['point_xyz_mm']} for a in lower],
        'common_Z_mm': z, 'shift_mm': z - 189.3, 'search': scans,
        'envelope_proof': 'Every finite cylinder, conical screw head and hex prism is contained in its axis capsule at the recorded maximum radius. Capsule separation is at least the finite axis distance minus both radii. Positive values therefore prove separation of these nominal primitives; negative values are inconclusive. Axis distance is exact for X versus X or a constant-X YZ segment.',
        'screw_recipe': {'source_function': 'scripts/thin_bolted_occupied.py:screw_shapes', 'body_radius_mm': 2.5, 'body_axis_interval_mm': [3., 63.5],
                         'head_radius_containing_mm': 4.5, 'head_axis_interval_mm': [0., 3.], 'delivered_screw_dimensions_verified': False},
        'all66_screw_comparisons': {'count': len(screw_checks), 'positive_lower_bounds': True, 'minimum_by_lower_primitive_role': role_minima},
        'all96_fixed_bolt_comparisons': {'count': len(fixed_checks), 'positive_lower_bounds': True,
                                       'minimum': min(fixed_checks, key=lambda r: r['capsule_separation_lower_bound_mm'])},
        'receiver_coordinate_margins': receiver_rows,
        'conditional_end_reference': {'diameter_mm': 9.525, 'cleat_bottom_end_mm': 60.3, 'post_top_end_mm': 38.9,
            'softwood_tension_full7D_mm': 66.675, 'softwood_tension_minimum3p5D_mm': 33.3375,
            'compression_full4D_mm': 38.1, 'compression_geometric_margin_at_post_top_mm': .8,
            'common_overlap_Z_mm': [139.7, 238.9], 'tension_full_both_directions_possible': False,
            'minimum_end_over_full7D_diagnostic_only': 38.9 / 66.675,
            'complete_Cdelta_load_direction_group_splitting_or_strength': None},
        'choice': '200 mm is the first whole-millimeter station above the conservative bore/screw threshold 199.659375 mm and retains the 4D post-top compression reference. 210 and 220 mm lose even the 3.5D post-top tension minimum. The 0.340625 mm nominal bore/screw bound is narrow and requires actual dimensions/tolerance consideration.',
        'preserved_failed_geometry': {'path': str(GEOMETRY.relative_to(ROOT)), 'sha256': GEOMETRY_SHA, 'metal_screw_collisions': geometry['collisions']['metal_screws']},
        'next_parent_query': 'Query only the new explicit four-axis Z revision through the unchanged source-bound occupied geometry adapter. Recheck complete backing, all metal/wood/panel/service intersections and full screw fractions; preserve this original failed scenario.',
        'limits': ['This is a pure nominal finite-envelope proposal, not a CAD rerun or delivered clearance.',
                   'Conical head and hex/washer bore holes are conservatively filled by containing capsules.',
                   'Current service-wire/panel/angle solid intersections are not recomputed here; the parent actual revised query must check them.',
                   'No pressure, signed load, compatible sharing, grade, end factor adoption, resistance, structural or fabrication release.'],
        'release': dict.fromkeys(('geometry_adopted', 'mechanics_ready', 'complete_joint_resistance', 'fabrication', 'structural', 'climbing'), False)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
    print(json.dumps({'path': str(args.output), 'bytes': args.output.stat().st_size, 'sha256': sha(args.output), 'producer_sha256': LOADED_SHA,
                      'source_pins': len(pins), 'common_Z_mm': z, 'minimum_screw_bound_mm': min(r['capsule_separation_lower_bound_mm'] for r in screw_checks),
                      'minimum_fixed_bolt_bound_mm': min(r['capsule_separation_lower_bound_mm'] for r in fixed_checks)}))


if __name__ == '__main__':
    main()
