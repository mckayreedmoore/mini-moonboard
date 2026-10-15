"""Define normalized gravity work on the retained nominal material domains.

Uniform volume loads, source-moment differences and exact enclosures only.
No response, contact equilibrium, stiffness, stress or resistance is solved.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from fractions import Fraction as F
from functools import cache
from pathlib import Path
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BOOT = {'path': 'scripts/eoere_coupled_contact_work.py',
        'sha256': 'abea0f9b501f09a4b314f97dce241318b09f9ea022a94c6471c39f4703784ccf'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bootstrap(pins):
    data = (ROOT/BOOT['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == BOOT['sha256']
            and pins.get(BOOT['path'], BOOT['sha256']) == BOOT['sha256'], 'frozen contact-work bootstrap changed')
    pins[BOOT['path']] = BOOT['sha256']
    module = ModuleType('_eoere_verified_gravity_bootstrap'); module.__file__ = str(ROOT/BOOT['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - authenticated buffer
    return module


def methods(inputs, base, pins):
    loader = base.private(inputs['definition_loader'], pins)
    namespace = {'F': F, 'math': math, 'cache': cache, 'require': require}
    for key, functions in [('pi', ('atan_series', 'pi_bounds')), ('root', ('sqrt_bounds',)),
                           ('intervals', ('product_interval', 'scale_interval', 'sum_intervals'))]:
        loader.definitions(inputs['pure_helpers'][key], functions, (), namespace, pins)
    return SimpleNamespace(**{name: namespace[name] for name in
        ('pi_bounds', 'sqrt_bounds', 'product_interval', 'scale_interval', 'sum_intervals')})


def point_interval(value):
    require(type(value) is not bool, 'nonboolean finite scalar required')
    return F(value), F(value)


def exact_interval(values):
    result = tuple(point_interval(value)[0] for value in values)
    require(len(result) == 2 and result[0] <= result[1], 'two ordered exact interval endpoints required')
    return result


def quotient(numerator, denominator):
    numerator, denominator = exact_interval(numerator), exact_interval(denominator)
    require(denominator[0] > 0, 'positive volume required')
    values = [a/b for a in numerator for b in denominator]
    return min(values), max(values)


def short_enclosure(interval, bits=96):
    """Outward dyadic rounding keeps issued rational bounds compact."""
    low, high = exact_interval(interval)
    require(type(bits) is int and 16 <= bits <= 256, 'bounded enclosure resolution required')
    scale = 1 << bits
    return F(low.numerator*scale//low.denominator, scale), F(-(-high.numerator*scale//high.denominator), scale)


def fitting_scenario(data):
    """Reuse only the pinned Scenario definition; never import its CAD module."""
    node, = [row for row in ast.parse(data).body if isinstance(row, ast.ClassDef) and row.name == 'Scenario']
    namespace = {'dataclass': dataclass, 'asdict': asdict, 'math': math}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<retained-fitting-scenario>', 'exec'), namespace)  # noqa: S102
    scenario = namespace['Scenario'](); scenario.validate()
    return scenario


def fitting_moments(scenario, method):
    """Union of two boxes minus all eight disjoint, complete circular holes."""
    length, width, thick, radius = (F(str(value)) for value in
        (scenario.leg_mm, scenario.width_mm, scenario.thickness_mm, scenario.factory_hole_mm/2))
    holes = scenario.holes()
    require(len(holes) == 8 and {row['flange'] for row in holes} == {'beam', 'post'}, 'all eight sharp-reference holes required')
    centers = []
    for row in holes:
        along, across = F(str(row['along_mm'])), F(str(row['transverse_mm']))
        require(thick+radius < along < length-radius and abs(across)+radius < width/2,
                'complete hole outside overlap and inside its own flange required')
        centers.append([along, thick/2, across] if row['flange'] == 'beam' else [thick/2, along, across])
    for i, first in enumerate(holes):
        for second in holes[i+1:]:
            if first['flange'] == second['flange']:
                require(sum((F(str(first[key]))-F(str(second[key])))**2 for key in ('along_mm', 'transverse_mm')) > 4*radius**2,
                        'disjoint flange holes required')
    pi = short_enclosure(method.pi_bounds())
    volume = method.sum_intervals(point_interval(width*thick*(2*length-thick)),
                                   method.scale_interval(pi, -len(holes)*radius**2*thick))
    first = width*(thick*length**2+length*thick**2-thick**3)/2
    moments = [method.sum_intervals(point_interval(first if i < 2 else 0),
        method.scale_interval(pi, -radius**2*thick*sum(row[i] for row in centers))) for i in range(3)]
    center = [quotient(value, volume) for value in moments]
    require(volume[0] > 0 and center[0] == center[1] and center[2] == (0, 0), 'positive symmetric sharp-L moments required')
    return {'volume': volume, 'center': center, 'hole_count': len(holes),
            'dimensions_mm': {'leg': str(length), 'width': str(width), 'thickness': str(thick), 'hole_radius': str(radius)}}


def chart(origin, axes, local_center, local_volume, contact, method):
    """Use the stored orthogonal chart with its actual, slightly nonunit Jacobian."""
    require(len(axes) == 3 and len(local_center) == 3 and len(origin) == 3, 'complete three-dimensional chart required')
    axes = [contact.vector(row) for row in axes]; origin = contact.vector(origin)
    local_center = list(map(exact_interval, local_center)); local_volume = exact_interval(local_volume)
    gram = [[contact.dot(a, b) for b in axes] for a in axes]
    require(all(gram[i][j] == 0 for i in range(3) for j in range(3) if i != j)
            and max(abs(gram[i][i]-1) for i in range(3)) <= F(1, 10**10), 'retained orthogonal near-unit chart required')
    jacobian = contact.dot(axes[0], contact.cross(axes[1], axes[2]))
    require(jacobian > 0 and local_volume[0] > 0, 'positive chart Jacobian and material volume required')
    center = [method.sum_intervals(point_interval(origin[i]),
        *(method.scale_interval(local_center[j], axes[j][i]) for j in range(3))) for i in range(3)]
    return method.scale_interval(local_volume, jacobian), center, jacobian


def role_volume(kind, shaft, interval, method):
    low, high = map(F, interval); height = high-low
    h = shaft['source_axis']['hardware_scenario']; diameter = F(shaft['diameter_mm'])
    require(height > 0 and diameter > 0, 'positive role height and shaft diameter required')
    pi, root3 = short_enclosure(method.pi_bounds()), short_enclosure(method.sqrt_bounds(F(3)))
    if kind == 'shaft':
        return method.scale_interval(pi, diameter**2*height/4)
    if kind in ('head', 'nut'):
        across = F(h['hex_across_flats_mm'])
        require(across > diameter, 'positive hexagon outside nominal shaft bore required')
        gross = method.scale_interval(root3, across**2*height/2)
        return gross if kind == 'head' else method.sum_intervals(gross, method.scale_interval(pi, -diameter**2*height/4))
    require(kind in ('head_washer', 'nut_washer', 'spacer'), 'retained metal role required')
    inner, outer = (F('10.31875'), F('19.05')) if kind == 'spacer' else (F(h['washer_id_mm']), F(h['washer_od_mm']))
    require(outer > inner >= diameter, 'positive annulus with noninterfering bore required')
    return method.scale_interval(pi, (outer**2-inner**2)*height/4)


def uniform_load(row, volume, center, method):
    """b=F/V: exact resultant by normalization; enclose affine-work changes.

    The analytic law uses the true integral V. Numeric enclosures describe
    its coefficients, not an independently adopted rounded constant load.
    """
    force = [point_interval(value)[0] for value in row['force_xyz_n']]
    point = [point_interval(value)[0] for value in row['point_xyz_mm']]
    volume = exact_interval(volume); center = list(map(exact_interval, center))
    require(len(force) == len(point) == len(center) == 3 and force[:2] == [0, 0] and force[2] < 0,
            'one retained downward gravity force required')
    require(not any(map(F, row.get('moment_xyz_nmm', [0, 0, 0]))), 'gravity has no external point couple')
    require(volume[0] > 0 and all(len(value) == 2 and value[0] <= value[1] for value in center),
            'positive material volume and ordered centroid enclosure required')
    delta = [method.sum_intervals(value, point_interval(-old)) for value, old in zip(center, point, strict=True)]
    coefficients = [(F(0), F(0))]*3 + [method.scale_interval(delta[j], force[i]) for i in range(3) for j in range(3)]
    density = [quotient(point_interval(value), volume) for value in force]
    norm_square = quotient(point_interval(sum(value**2 for value in force)), volume)
    return {'id': row['id'], 'body': row['body'], 'parent_body': row['parent_body'],
        'source_force_xyz_n': row['force_xyz_n'], 'source_point_xyz_mm': row['point_xyz_mm'],
        'volume_mm3_interval': [str(value) for value in short_enclosure(volume)],
        'uniform_force_density_n_per_mm3_intervals': [[str(value) for value in short_enclosure(a)] for a in density],
        'centroid_xyz_mm_intervals': [[str(value) for value in short_enclosure(a)] for a in center],
        'centroid_minus_source_mm_intervals': [[str(value) for value in short_enclosure(a)] for a in delta],
        'affine_work_coefficient_difference_intervals': [[str(value) for value in short_enclosure(a)] for a in coefficients],
        'L2_load_functional_norm_square_n2_per_mm3_interval': [str(value) for value in short_enclosure(norm_square)],
        'maximum_centroid_difference_mm_upper': str(max(abs(value) for a in delta for value in a)),
        'exact_resultant_preserved_by_definition': True,
        'exact_source_first_moment_equality_claimed': False,
        'arbitrary_old_kinematic_work_or_comparator_bounds_transferred': False}


def timber_moments(source, mass, row, volume_tolerance):
    require(mass['kind'] == 'timber' and mass['center_xyz_mm'] == source['center_xyz_mm'] == row['point_xyz_mm']
            and F(source['volume_mm3']) > 0 and F(source['source']['volume_mm3']) > 0,
            'same recorded finished timber moments required')
    difference = F(source['volume_mm3'])-F(source['source']['volume_mm3'])
    require(abs(difference) <= volume_tolerance, 'timber observed and metadata volumes are inconsistent')
    return point_interval(source['volume_mm3']), list(map(point_interval, source['center_xyz_mm'])), difference


def gravity_laws(field, stacks, fitting, method, contact, tolerance, volume_tolerance):
    own = field['source_inputs']; mapped = contact.split_loads(field)
    loads = {row['id']: row for row in mapped}; laws = []; used = set()
    observations = {row['id']: row for row in own['finished_body_observations']}
    masses = {row['id']: row for row in own['physical_owner_gravity_rows']}

    def append(row, volume, center, domain):
        require(row['id'] not in used, 'gravity load must be distributed once')
        result = uniform_load(row, volume, center, method)
        require(F(result['maximum_centroid_difference_mm_upper']) <= tolerance, 'source centroid consistency gate exceeded')
        result['domain'] = domain; laws.append(result); used.add(row['id'])

    for timber in own['timber_rows']:
        name = timber['name']; source = observations[name]; mass = masses[name]
        row = loads['self-weight/'+name]
        volume, center, difference = timber_moments(source, mass, row, volume_tolerance)
        append(row, volume, center,
            {'kind': 'recorded_finished_timber_numerical_moments', 'brep': source['source'],
             'observed_minus_metadata_volume_mm3': str(difference),
             'exact_geometric_volume_and_centroid_certified': False,
             'future_quadrature_must_recheck_force_and_centroid': True})
    for pose in own['fitting_poses']:
        name = pose['id']; row = loads['self-weight/'+name]
        require(masses[name]['kind'] == 'fitting' and masses[name]['center_xyz_mm'] == row['point_xyz_mm'],
                'same catalog fitting load center required')
        axes = [pose[key] for key in ('u_xyz', 'v_xyz', 'w_xyz')]
        volume, center, jacobian = chart(pose['origin_xyz_mm'], axes, fitting['center'], fitting['volume'], contact, method)
        append(row, volume, center, {'kind': 'sharp_eight_hole_L_catalog_mass_normalization',
            'origin_xyz_mm': pose['origin_xyz_mm'], 'basis_columns_xyz': axes, 'exact_chart_jacobian': str(jacobian),
            'dimensions_mm': fitting['dimensions_mm'], 'hole_count': fitting['hole_count'],
            'source_mass_kg': masses[name]['mass_kg'], 'formed_heel_or_whole_fitting_mechanics_qualified': False})
    require(len(stacks) == len(own['shafts']) == 100, 'all current bolt stacks required')
    for shaft, stack in zip(own['shafts'], stacks, strict=True):
        require(shaft['axis_id'] == stack['axis_id'], 'same source stack order required')
        for role in shaft['metal_roles']:
            kind = role['kind']; interval = stack['nominal_role_intervals_mm'][kind]
            local_volume = role_volume(kind, shaft, interval, method)
            require(max(abs(value-F(role['volume_mm3'])) for value in local_volume) <= volume_tolerance,
                    'same nominal role recipe volume required')
            center_local = [point_interval(sum(map(F, interval))/2), point_interval(0), point_interval(0)]
            volume, center, jacobian = chart(shaft['point'], shaft['basis'], center_local, local_volume, contact, method)
            row = loads['physical-bolt-metal/'+role['id']]
            append(row, volume, center, {'kind': 'nominal_'+kind, 'axis_id': shaft['axis_id'],
                'axial_interval_mm': interval, 'exact_chart_jacobian': str(jacobian),
                'cross_section_dimensions_source': 'own retained shaft source_axis.hardware_scenario',
                'source_mass_kg': role['mass_kg'], 'partial_thread_geometry_or_engagement_qualified': False})
    expected = {row['id'] for row in mapped if row['id'].startswith('physical-bolt-metal/') or
        row['id'].startswith('self-weight/') and masses[row['body']]['kind'] in ('timber', 'fitting')}
    require(used == expected and len(laws) == 552, 'all and only 552 retained material-gravity loads required')
    return laws


def run(reference):
    pins = {}; contact = bootstrap(pins); material = contact.bootstrap(pins)
    prior = material.bootstrap(pins); boot = prior.bootstrap(pins); base = boot.producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_distributed_gravity_inputs/v1'
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
            and inputs['extra_grid'] is False and inputs['structural_acceptance'] is False
            and inputs['actual_observations'] is None, 'current gravity-definition-only scope required')
    for row in inputs['execution_sources']:
        base.captured(row, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing gravity checker required')
    parent = json.loads(base.captured(inputs['contact_work_result'], pins))
    require(parent['complete_coupled_contact_search_load_law_or_fracture_treatment_ready'] is False
            and parent['inventory']['source_body_gravity_loads_for_future_3d_domains'] == 552,
            'retained unqualified current source-map stage required')
    for path, digest in parent['source_sha256'].items():
        base.captured({'path': path, 'sha256': digest}, pins)
    runtime = boot.check_runtime(parent['runtime']); method = methods(inputs, base, pins)
    scenario = fitting_scenario(base.captured(inputs['fitting_geometry_recipe'], pins))
    fitting = fitting_moments(scenario, method); tolerance = F(inputs['source_centroid_consistency_tolerance_mm'])
    require(tolerance == F(1, 10**7), 'unchanged source-roundoff gate required')
    volume_tolerance = F(inputs['source_volume_consistency_tolerance_mm3'])
    require(volume_tolerance == F(1, 10**5), 'existing uniform finished-volume numerical gate required')
    laws, cases = None, []
    for case in parent['cases']:
        binding = case['binding']; field = json.loads(base.captured(binding['field'], pins))
        require(field['case_id'] == binding['case_id'] and field['state_id'] == binding['state_id'], 'own retained case required')
        mapped = contact.split_loads(field)
        require([row for row in mapped if not row['id'].startswith('climber/')] == parent['common_static_load_map'],
                'unchanged common gravity and other static actions required')
        if laws is None:
            laws = gravity_laws(field, parent['nominal_stacks'], fitting, method, contact, tolerance, volume_tolerance)
        cases.append({'binding': binding, 'common_gravity_law_count': len(laws), 'climber_load': case['climber_load']})
    require(len(cases) == 6, 'six unchanged current load cases required')
    total = [(F(0), F(0)) for _ in range(12)]
    for row in laws:
        total = [method.sum_intervals(old, tuple(map(F, new))) for old, new in
                 zip(total, row['affine_work_coefficient_difference_intervals'], strict=True)]
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_distributed_gravity/v1', 'inputs': reference, 'source_sha256': pins, 'runtime': runtime,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
        'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
        'inventory': {'material_gravity_laws': 552, 'analytic_metal_domains': 530,
            'recorded_numerical_timber_moment_domains': 22, 'other_timber_actions_still_to_distribute': 66,
            'reduced_panel_actions_per_case': 217},
        'common_gravity_laws': laws, 'cases': cases,
        'total_affine_work_coefficient_difference_intervals': [[str(v) for v in short_enclosure(row)] for row in total],
        'maximum_source_centroid_difference_mm_upper': str(max(F(row['maximum_centroid_difference_mm_upper']) for row in laws)),
        'load_law': inputs['load_law'], 'applicability_limits': inputs['applicability_limits'],
        'primary_method': inputs['primary_method'],
        'all_gravity_resultants_preserved_by_normalization': True, 'extra_density_derived_gravity_added': False,
        'exact_original_first_moments_or_arbitrary_old_kinematic_work_preserved': False,
        'new_response_contact_equilibrium_native_frame_or_CAD_solve': False,
        'complete_coupled_load_contact_fracture_law_or_evaluation_ready': False,
        'physical_stiffness_restraint_demand_or_complete_resistance_qualified': False,
        'panel_screw_exceedances_deferred': True, 'actual_observations': None, 'structural_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); require(not args.out.exists(), 'preserve issued gravity evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({'output': str(args.out), 'gravity_laws': len(result['common_gravity_laws']),
                      'maximum_centroid_difference_mm_upper': float(F(result['maximum_source_centroid_difference_mm_upper']))}))


if __name__ == '__main__':
    main()
