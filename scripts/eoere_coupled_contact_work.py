"""Define contact work and retained source ownership before coupled evaluation.

Exact geometric controls and source mappings only. No contact multiplier,
candidate response, assembled interface law or resistance is solved here.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BOOT = {'path': 'scripts/eoere_continuum_material_law.py',
        'sha256': '33a5fc73e4ab33290412dcec07d03a2bc3c5f55c65942db3dcb11a17057b9b82'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bootstrap(pins):
    data = (ROOT/BOOT['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == BOOT['sha256']
            and pins.get(BOOT['path'], BOOT['sha256']) == BOOT['sha256'], 'frozen bulk-work bootstrap changed')
    pins[BOOT['path']] = BOOT['sha256']
    module = ModuleType('_eoere_verified_contact_work_bootstrap'); module.__file__ = str(ROOT/BOOT['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - pinned source buffer
    return module


def vector(values):
    require(len(values) == 3 and all(type(value) is not bool for value in values), 'three nonboolean coordinates required')
    return list(map(F, values))


def dot(a, b):
    return sum((x*y for x, y in zip(vector(a), vector(b), strict=True)), F(0))


def sub(a, b):
    return [x-y for x, y in zip(vector(a), vector(b), strict=True)]


def cross(a, b):
    a, b = vector(a), vector(b)
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def triangle_pair(point, vertices):
    """Oriented gap H=m.(p-a), m=(b-a)x(c-a); scalar projection only.

    H has units mm^3. The physical signed distance is H/|m|. This one-pair
    identity is not a complete 3D contact-search or continuum discretization.
    """
    require(len(vertices) == 3, 'one three-vertex master face required')
    a, b, c = map(vector, vertices); point = vector(point)
    first, second, offset = sub(b, a), sub(c, a), sub(point, a)
    normal = cross(first, second); area_square = dot(normal, normal)
    require(area_square > 0, 'nondegenerate oriented master triangle required')
    h = dot(normal, offset)
    s = (dot(offset, first)*dot(second, second)-dot(offset, second)*dot(first, second))/area_square
    t = (dot(offset, second)*dot(first, first)-dot(offset, first)*dot(first, second))/area_square
    weights = [1-s-t, s, t]
    grad_b, grad_c = cross(second, offset), cross(offset, first)
    grad_a = [-x-y-z for x, y, z in zip(normal, grad_b, grad_c, strict=True)]
    return {'oriented_gap': h, 'normal_area_vector': normal,
            'normal_area_square': area_square, 'master_weights': weights,
            'projected_point': [x-h*n/area_square for x, n in zip(point, normal, strict=True)],
            'projection_inside_closed_triangle': min(weights) >= 0,
            'gap_gradients_slave_a_b_c': [normal, grad_a, grad_b, grad_c]}


def contact_forces(point, vertices, multiplier):
    """Synthetic admitted pair forces +lambda*DH; no multiplier is solved.

    lambda is a scaled multiplier (N/mm^2), not a physical pressure density.
    At contact, slave resultant magnitude is lambda*|m|; pressure needs its
    own surface quadrature/tributary-area mapping.
    """
    require(type(multiplier) is not bool, 'nonboolean contact multiplier required')
    multiplier = F(multiplier); pair = triangle_pair(point, vertices)
    require(pair['projection_inside_closed_triangle'] and pair['oriented_gap'] >= 0
            and multiplier >= 0 and multiplier*pair['oriented_gap'] == 0,
            'interior-or-edge nonpenetrating repulsive complementary pair required')
    return [[multiplier*value for value in gradient] for gradient in pair['gap_gradients_slave_a_b_c']]


def affine_load_coefficients(rows):
    """L(a+B*x): three constant and nine affine coefficients, no response."""
    result = [F(0)]*12
    for row in rows:
        force, point = vector(row['force_xyz_n']), vector(row['point_xyz_mm'])
        require(not any(vector(row.get('moment_xyz_nmm', [0, 0, 0]))), 'current source has no external point couples')
        for i in range(3):
            result[i] += force[i]
            for j in range(3):
                result[3+3*i+j] += force[i]*point[j]
    return result


def split_loads(field, expected_counts=(50, 508, 835)):
    own = field['source_inputs']; sources = own['physical_owner_gravity_rows']
    ordinary = {row['id']: row for row in sources if row['kind'] != 'shaft'}
    roles = {role['id']: (shaft['body'], role) for shaft in own['shafts'] for role in shaft['metal_roles']}
    expected_ordinary, expected_roles, expected_loads = expected_counts
    require(len(ordinary) == expected_ordinary and len(roles) == expected_roles
            and len({row['id'] for row in sources}) == len(sources)
            and sum(len(shaft['metal_roles']) for shaft in own['shafts']) == len(roles),
            'complete retained ordinary owners and metal roles required')
    mapped, seen = [], set()
    for row in field['body_applied_loads']:
        target = row['body']
        if row['id'].startswith('physical-bolt-metal/'):
            target = row['id'].removeprefix('physical-bolt-metal/')
            require(target in roles and target not in seen and roles[target][0] == row['body']
                    and row['point_xyz_mm'] == roles[target][1]['center_of_mass_xyz_mm'],
                    'exactly one unchanged own-centroid load for each retained metal role required')
            seen.add(target)
        else:
            require(target in ordinary, 'nonmetal source load must retain its original owner')
        mapped.append({**row, 'parent_body': row['body'], 'body': target})
    require(seen == set(roles) and len(mapped) == expected_loads and len({row['id'] for row in mapped}) == expected_loads,
            'all unchanged own-case load identities required')
    old_by_parent, new_by_parent = defaultdict(list), defaultdict(list)
    for old, new in zip(field['body_applied_loads'], mapped, strict=True):
        old_by_parent[old['body']].append(old); new_by_parent[new['parent_body']].append(new)
    require(set(old_by_parent) == set(new_by_parent)
            and all(affine_load_coefficients(rows) == affine_load_coefficients(new_by_parent[name])
                    for name, rows in old_by_parent.items()), 'all shared-parent affine load work must be preserved')
    return mapped


def nominal_stack(shaft, tolerance):
    """Reference axial chain and potential surfaces, without creating solids."""
    axis = shaft['source_axis']; h = axis['hardware_scenario']
    before, after, grip, washer, spacer = map(F, (axis['before_plate_mm'], axis['after_plate_mm'], axis['grip_mm'],
        h['washer_thickness_mm'], axis.get('nut_side_spacer_mm', 0)))
    start = -before-washer; nut_start = grip+after+washer+spacer
    intervals = {'shaft': [start, start+F(axis['nominal_under_head_length_mm'])],
        'head': [start-F(h['head_height_mm']), start], 'head_washer': [start, -before],
        'nut_washer': [grip+after, grip+after+washer], 'nut': [nut_start, nut_start+F(h['nut_height_mm'])]}
    if spacer:
        intervals['spacer'] = [grip+after+washer, nut_start]
    require(min(grip, washer, F(h['head_height_mm']), F(h['nut_height_mm']), F(axis['nominal_under_head_length_mm'])) > 0
            and min(before, after, spacer) >= 0, 'positive retained nominal stack dimensions required')
    require(max(abs(a-F(b)) for a, b in zip(intervals['shaft'], shaft['shaft_interval_mm'], strict=True)) <= tolerance,
            'same nominal shaft interval required')
    roles = {role['kind']: role for role in shaft['metal_roles']}
    require(len(roles) == len(shaft['metal_roles']) and set(roles) == set(intervals), 'one own role per nominal stack domain required')
    direction = vector(shaft['basis'][0]); point = vector(shaft['point'])
    require(abs(dot(direction, direction)-1) <= F(1, 10**10), 'recorded unit shaft axis required')
    center_errors = []
    for kind, interval in intervals.items():
        center = sub(roles[kind]['center_of_mass_xyz_mm'], point); station = sum(interval)/2
        center_errors.extend(abs(value-station*n) for value, n in zip(center, direction, strict=True))
    require(max(center_errors) <= tolerance, 'same recorded nominal metal-role centroids required')
    ends = {row['end']: row for row in shaft['ends']}
    require(set(ends) == {'head', 'nut'} and len(shaft['ends']) == 2, 'own head and nut hosts required')
    errors = [abs(F(ends['head']['support_s_mm'])+before), abs(F(ends['head']['pressure_face_s_mm'])-start),
              abs(F(ends['nut']['support_s_mm'])-grip-after), abs(F(ends['nut']['pressure_face_s_mm'])-nut_start)]
    surfaces = sorted(shaft['surfaces'], key=lambda row: row['interval_mm'][0]); cursor = -before
    bores = []
    for row in surfaces:
        low, high = map(F, row['interval_mm']); clearance = (F(row['bore_diameter_mm'])-F(shaft['diameter_mm']))/2
        require(low < high and clearance >= 0, 'positive nominal bore domain and nonnegative radial gap required')
        errors.append(abs(low-cursor)); cursor = high
        bores.append({'host': row['host'], 'kind': row['kind'], 'interval_mm': list(map(str, (low, high))),
                      'exact_nominal_radial_clearance_mm': str(clearance)})
    errors.append(abs(cursor-grip-after))
    require(max(errors) <= tolerance, 'retained contiguous host chain and axial seats required')
    pairs = [['head', 'head_washer'], ['head_washer', 'host/'+ends['head']['host']],
             ['host/'+ends['nut']['host'], 'nut_washer'], ['nut_washer', 'spacer' if spacer else 'nut']]
    if spacer:
        pairs.append(['spacer', 'nut'])
    loose = []
    for kind in ['head_washer', 'nut_washer']+(['spacer'] if spacer else []):
        bore = F('10.31875') if kind == 'spacer' else F(h['washer_id_mm'])
        gap = (bore-F(shaft['diameter_mm']))/2
        require(gap >= 0, 'nonnegative nominal loose-metal bore gap required')
        loose.append({'role': kind, 'interval_mm': list(map(str, intervals[kind])),
                      'exact_nominal_radial_clearance_mm': str(gap)})
    return {'axis_id': shaft['axis_id'], 'parent_body': shaft['body'],
        'nominal_role_intervals_mm': {key: list(map(str, value)) for key, value in intervals.items()},
        'potential_host_bore_pairs': bores, 'potential_loose_metal_bore_pairs': loose,
        'potential_axial_pairs': pairs, 'head_and_nut_shaft_connections_required': 2,
        'maximum_stored_centroid_error_mm': str(max(center_errors)),
        'maximum_stored_axial_chain_error_mm': str(max(errors)),
        'engaged_thread_geometry_partial_shank_and_interface_compliance_resolved': False,
        'full_thread_root_sensitivity_adopted': False}


def literal_flange_dimensions(data):
    cls, = [node for node in ast.parse(data).body if isinstance(node, ast.ClassDef) and node.name == 'Scenario']
    values = {node.target.id: F(str(ast.literal_eval(node.value))) for node in cls.body
              if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None}
    return {key: values[key] for key in ('leg_mm', 'width_mm', 'thickness_mm')}


def run(reference):
    pins = {}; material = bootstrap(pins); prior = material.bootstrap(pins); boot = prior.bootstrap(pins); base = boot.producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_coupled_contact_work_inputs/v1'
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
            and inputs['extra_grid'] is False and inputs['structural_acceptance'] is False
            and inputs['actual_observations'] is None, 'retained definition-only scope required')
    for row in inputs['execution_sources']:
        base.captured(row, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing contact-work checker required')
    parent = json.loads(base.captured(inputs['bulk_material_result'], pins))
    require(parent['complete_assembled_joint_contact_law_evaluated'] is False
            and parent['current_bolt_count'] == 100 and parent['current_screw_count'] == 66,
            'same unqualified retained bulk-input stage required')
    runtime = boot.check_runtime(parent['runtime'])
    for path, digest in parent['source_sha256'].items():
        base.captured({'path': path, 'sha256': digest}, pins)
    dimensions = literal_flange_dimensions(base.captured(inputs['fitting_geometry_recipe'], pins))
    base.captured(inputs['hardware_geometry_recipe'], pins)
    base.captured(inputs['selected_spacer_recipe'], pins)
    tolerance = F(inputs['stored_geometry_consistency_tolerance_mm'])
    require(tolerance == F(1, 10**7), 'recorded source-roundoff gate required')
    common, cases, stacks, centroids, load_counts = None, [], None, [], None
    for binding in parent['case_bindings']:
        field = json.loads(base.captured(binding['field'], pins)); own = field['source_inputs']
        require(field['case_id'] == binding['case_id'] and field['state_id'] == binding['state_id'], 'own current case required')
        require(all(field['source_sha256'].get(inputs[key]['path']) == inputs[key]['sha256']
                    for key in ('fitting_geometry_recipe', 'hardware_geometry_recipe', 'selected_spacer_recipe')),
                'same geometry recipes as the retained case source pins required')
        mapped = split_loads(field); static = [row for row in mapped if not row['id'].startswith('climber/')]
        climber = [row for row in mapped if row['id'].startswith('climber/')]
        require(len(climber) == 1, 'one retained own-case climber action required')
        if common is None:
            common = static; stacks = [nominal_stack(row, tolerance) for row in own['shafts']]
            masses = {row['id']: row for row in own['physical_owner_gravity_rows']}
            load_counts = Counter(masses[row['body']]['kind'] for row in field['body_applied_loads'])
            require(load_counts == {'timber': 88, 'fitting': 22, 'shaft': 508, 'panel': 217},
                    'complete retained load family census required')
            ordinary_gravity = sum(row['id'].startswith('self-weight/') and masses[row['body']]['kind'] in ('timber', 'fitting')
                                   for row in field['body_applied_loads'])
            timber_gravity = sum(row['id'].startswith('self-weight/') and masses[row['body']]['kind'] == 'timber'
                                for row in field['body_applied_loads'])
            require(ordinary_gravity == 44 and timber_gravity == 22, 'own timber/fitting selfweight inventory required')
            for pose in own['fitting_poses']:
                load_point = masses[pose['id']]['center_xyz_mm']; offset = sub(load_point, pose['origin_xyz_mm'])
                local = [dot(offset, pose[key]) for key in ('u_xyz', 'v_xyz', 'w_xyz')]
                outside = (dimensions['thickness_mm']+tolerance < local[0] < dimensions['leg_mm']-tolerance
                    and dimensions['thickness_mm']+tolerance < local[1] < dimensions['leg_mm']-tolerance
                    and abs(local[2]) < dimensions['width_mm']/2-tolerance)
                centroids.append({'fitting': pose['id'], 'source_mass_kg': masses[pose['id']]['mass_kg'],
                    'nominal_local_centroid_mm': list(map(str, local)), 'point_outside_gross_sharp_L': outside})
        else:
            require(common == static, 'same 834 retained static loads in all six cases required')
        cases.append({'binding': binding, 'climber_load': climber[0],
            'all_835_source_loads_mapped_once': True, 'all_shared_parent_affine_work_coefficients_preserved': True,
            'exact_original_affine_load_coefficients': list(map(str, affine_load_coefficients(field['body_applied_loads'])))})
    require(len(common) == 834 and len(cases) == 6 and len(stacks) == 100
            and len(centroids) == 22 and all(row['point_outside_gross_sharp_L'] for row in centroids),
            'complete current common load/stack and sharp-reference centroid census required')
    inventory = {'retained_parent_owners': 150, 'material_role_and_ordinary_owner_targets': 558,
        'source_loads_per_case': 835, 'common_static_loads': 834, 'explicit_metal_role_loads': 508,
        'source_body_gravity_loads_for_future_3d_domains': ordinary_gravity+load_counts['shaft'],
        'other_point_loads_on_future_3d_timbers': load_counts['timber']-timber_gravity,
        'retained_reduced_panel_point_loads': load_counts['panel'],
        'host_bore_pairs': sum(len(row['potential_host_bore_pairs']) for row in stacks),
        'loose_metal_bore_pairs': sum(len(row['potential_loose_metal_bore_pairs']) for row in stacks),
        'axial_seat_pairs': sum(len(row['potential_axial_pairs']) for row in stacks),
        'head_or_nut_shaft_connections_to_define': 200, 'sharp_fitting_mass_centroids_outside_material': 22}
    require((inventory['host_bore_pairs'], inventory['loose_metal_bore_pairs'], inventory['axial_seat_pairs']) == (208, 208, 408),
            'current reference interface census required')
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_coupled_contact_work/v1', 'inputs': reference, 'source_sha256': pins, 'runtime': runtime,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
        'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False, 'inventory': inventory,
        'common_static_load_map': common, 'cases': cases, 'nominal_stacks': stacks,
        'sharp_reference_fitting_centroids': centroids, 'fitting_reference_dimensions_mm': {k: str(v) for k, v in dimensions.items()},
        'primary_methods': inputs['primary_methods'],
        'contact_work_definition': inputs['contact_work_definition'], 'load_mapping_limits': inputs['load_mapping_limits'],
        'remaining_assembly_and_evaluation': inputs['remaining_assembly_and_evaluation'],
        'new_response_contact_multiplier_pressure_or_stress_computed': False,
        'complete_coupled_contact_search_load_law_or_fracture_treatment_ready': False,
        'physical_stiffness_restraint_demand_or_complete_resistance_qualified': False,
        'geometry_hardware_or_original_case_load_records_changed': False,
        'panel_screw_exceedances_deferred': True, 'actual_observations': None, 'structural_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); require(not args.out.exists(), 'preserve issued contact-work evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), 'inventory': result['inventory']}))


if __name__ == '__main__':
    main()
