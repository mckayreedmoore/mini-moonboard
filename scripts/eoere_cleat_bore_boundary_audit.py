"""Replay original cleat bore wrenches on analytic cylindrical walls.

This constructs only boundary pressure/stress traces. The independent necessary
test allows all full-tensor tractions and can refute, but never approve, the
declared material law. Interior equilibrium and contact compatibility stay open.
"""
from __future__ import annotations

import argparse
import importlib.metadata
from fractions import Fraction as F
from pathlib import Path

from scripts import eoere_bore_boundary_tractions as method
from scripts import eoere_cleat_finite_body as model
from scripts import eoere_cleat_section_reference as section
from scripts import eoere_section_patches as patches
from scripts.eoere_mixed_continuous_bound import read_exact

current = model.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/cleat-bore-boundary-inputs-v2.json'
MEMBERS = ('eoere_cleat_left', 'eoere_cleat_right')
CASES = ('a12-forward', 'a12-rear', 'a12-left', 'k12-right', 'k12-rear', 'a1-rear')


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_current_cleat_bore_boundary_inputs/v1'
        and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
        and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
        and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
        and inputs['extra_grid'] is False and inputs['angular_divisions_per_quarter'] == inputs['axial_divisions'] == 16
        and inputs['actual_observations'] is None and inputs['structural_acceptance'] is False
        and inputs['complete_cleat_resistance'] is None and inputs['physical_demand_bounds_established'] is False,
        'retained geometry and declared boundary-only scope required')
    current.require(inputs['base_strengths_mpa'] == {key: str(value) for key, value in method.volume.BASE_STRENGTHS.items()}
        and inputs['runtime_versions'] == {'numpy': '2.5.2', 'scipy': '1.18.1'} and inputs['highs_version'] == '1.12.0',
        'unchanged full-tensor C16 hypothesis and pinned static LP runtimes required')
    for key, module in (('method_helper', method), ('tensor_helper', method.volume),
                        ('correction_helper', method.correction), ('rational_helper', patches)):
        current.require(inputs[key] == current.ref(module.OWN) and module.LOADED_SHA == inputs[key]['sha256'],
                        'loaded and on-disk boundary helper changed: '+key)


def full_bore_surfaces(geometry):
    current.require(geometry['frame'] == [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]]
        and len(geometry['bores']) == len({b['id'] for b in geometry['bores']}) == 4 and geometry['current_finished_solid']['valid_single_solid'] is True
        and abs(geometry['analytic_finished_volume_mm3']-geometry['actual_volume_mm3']) < 1e-6,
        'own analytic current cleat with its cached single-solid volume check required')
    proofs = []
    bores = geometry['bores']
    for bore in bores:
        current.require(bore['axis'] == [0., 1., 0.], 'current full-width bore direction required')
        origin = tuple(map(method.rational, bore['origin']))
        low, high = map(method.rational, bore['interval_mm'])
        radius = method.rational(bore['radius_mm'])
        current.require(origin[1] == 0 and radius > 0 and low < high, 'positive centered full-width bore required')
        gaps = []
        for plane in geometry['planes']:
            normal = tuple(map(method.rational, plane['normal']))
            room = method.rational(plane['offset'])-method.dot(normal, origin)-max(normal[1]*low, normal[1]*high)
            square = radius*radius*(normal[0]**2+normal[2]**2)
            current.require(room >= 0 and room*room >= square, 'cylindrical wall leaves its frozen profile')
            gaps.append(str(room*room-square))
        current.require(any(plane['normal'] == [0., 1., 0.] and method.rational(plane['offset']) == high for plane in geometry['planes'])
            and any(plane['normal'] == [0., -1., 0.] and method.rational(plane['offset']) == -low for plane in geometry['planes']),
            'bore interval must end at both source width faces')
        clearances = []
        for other in bores:
            if other['id'] == bore['id']:
                continue
            offset = [origin[i]-method.rational(other['origin'][i]) for i in (0, 2)]
            gap = method.dot(offset, offset)-(radius+method.rational(other['radius_mm']))**2
            current.require(gap > 0, 'intersecting bore walls require another boundary adapter')
            clearances.append(str(gap))
        proofs.append({'bore': bore['id'], 'exact_profile_squared_clearance_margins': gaps,
                       'exact_other_bore_squared_clearance_margins': clearances})
    return proofs


def source_wrench(record, geometry, bore):
    names = [bore['id']+'/point/'+str(i) for i in (0, 1, 2)]
    actions = [action for action in record['actions'] if action['id'].startswith(bore['id']+'/point/')]
    current.require(len(actions) == 3 and {a['id'] for a in actions} == set(names), 'two own bearing actions and separate axial washer capture required')
    total, points = [F(0)]*4, []
    frame = [[method.rational(value) for value in row] for row in geometry['frame']]
    origin, start = list(map(method.rational, bore['origin'])), list(map(method.rational, geometry['start']))
    low, high = map(method.rational, bore['interval_mm'])
    for action in actions:
        world = list(map(method.rational, action['point_mm']))
        point = [method.dot(row, [p-s for p, s in zip(world, start, strict=True)])-center for row, center in zip(frame, origin, strict=True)]
        force = [method.dot(row, list(map(method.rational, action['force_n']))) for row in frame]
        if action['id'] == names[2]:
            current.require(point[0] == point[2] == force[0] == force[2] == 0
                and not any(map(method.rational, action['free_moment_nmm'])), 'washer capture has an unhandled lateral force or couple')
            continue
        current.require(point[0] == point[2] == force[1] == 0 and low <= point[1] <= high
            and not any(map(method.rational, action['free_moment_nmm'])), 'off-axis, axial or free-couple bore action requires another adapter')
        value = [force[0], force[2], point[1]*force[2], -point[1]*force[0]]
        total = [a+b for a, b in zip(total, value, strict=True)]
        points.append({'id': action['id'], 'exact_relative_point_LUV_mm': list(map(str, point)), 'exact_force_LUV_n': list(map(str, force))})
    current.require(any(total), 'nonzero source bore wrench required')
    return total, points


def disposition(lower, upper, scenario):
    current.require(0 <= lower <= upper, 'ordered necessary and constructive boundary bounds required')
    factor = method.rational(scenario['strength_divisor'])*method.rational(scenario['whole_wrench_multiplier'])
    current.require(factor > 0, 'positive declared scenario required')
    lower, upper = factor*lower, factor*upper
    status = 'full_tensor_boundary_hypothesis_necessarily_fails' if lower > 1 else (
        'compressive_radial_pressure_and_stress_trace_within_hypothesis' if upper <= 1 else 'boundary_hypothesis_inconclusive')
    return {**scenario, 'exact_necessary_lower': str(lower), 'exact_construction_upper': str(upper),
        'necessary_lower': float(lower), 'construction_upper': float(upper), 'disposition': status,
        'complete_cleat_resistance': None, 'physical_failure_established': False}


def source_guard(pins, inputs):
    from scipy.optimize._highspy import _core

    current.require(current.sha(OWN) == LOADED_SHA and current.sha(method.OWN) == method.LOADED_SHA,
                    'loaded boundary adapter or helper changed')
    current.require({key: importlib.metadata.version(key) for key in inputs['runtime_versions']} == inputs['runtime_versions']
        and '.'.join(str(getattr(_core, 'HIGHS_VERSION_'+key)) for key in ('MAJOR', 'MINOR', 'PATCH')) == inputs['highs_version'],
        'boundary certificate numerical runtimes changed')
    model.verify_execution_sources(pins)


def run():
    input_ref = current.ref(INPUT)
    inputs = read_exact(input_ref)
    validate(inputs)
    job, materials = read_exact(inputs['source_job']), read_exact(inputs['material_hypothesis'])
    section.validate_assumptions(materials)
    current.require(job['schema'] == 'eoere_current_refined_fixed_action_finite_crack_comparisons/v1'
        and job['status'] == 'CURRENT_DECLARED_FINER_GRID_BORE_FLAW_COMPARISONS_COMPLETE_LOCAL_MODEL_ONLY'
        and job['geometry_revision'] == inputs['geometry_revision'] and job['hardware_revision'] == inputs['hardware_revision']
        and job['current_bolt_count'] == 100 and job['current_screw_count'] == 66 and job['extra_grid'] is False
        and set(job['geometry']) == set(MEMBERS)
        and {(r['case_id'], r['member']) for r in job['records']} == {(case, member) for case in CASES for member in MEMBERS}
        and len(job['records']) == 12, 'own completed six-case/two-cleat source records required')
    refs = [input_ref, inputs['source_job'], inputs['material_hypothesis'], inputs['reference_pdf'], inputs['method_helper'],
            current.ref(OWN), current.ref(current.ROOT/'tests/test_eoere_bore_boundary_tractions.py'),
            current.ref(current.ROOT/'tests/test_eoere_cleat_bore_boundary_audit.py'), *inputs['execution_sources'],
            inputs['prior_readiness_input'], *inputs['prior_readiness_source_snapshots']]
    pins = current.join(job['source_sha256'], {ref['path']: ref['sha256'] for ref in refs})
    source_guard(pins, inputs)
    geometry_proofs = {member: full_bore_surfaces(job['geometry'][member]) for member in MEMBERS}
    first = job['geometry'][MEMBERS[0]]['bores'][0]
    current.require(all(bore['radius_mm'] == first['radius_mm'] and bore['interval_mm'] == first['interval_mm']
        for geometry in job['geometry'].values() for bore in geometry['bores']), 'one shared source radius/width required')
    data = method.grid(first['radius_mm'], first['interval_mm'], inputs['angular_divisions_per_quarter'], inputs['axial_divisions'])
    records = []
    for record in job['records']:
        field = read_exact(record['field'])
        current.require(field['case_id'] == record['case_id'] and field['state_id'] == record['state_id'], 'own original field/state binding required')
        geometry = job['geometry'][record['member']]
        for bore in geometry['bores']:
            wrench, points = source_wrench(record, geometry, bore)
            chosen = method.select(wrench, data)
            certificate = method.certify(wrench, data, chosen['pressures_mpa'])
            lower = method.necessary(chosen['dual_multiplier'], wrench, data)
            comparisons = [disposition(F(lower['exact_necessary_lower']), F(certificate['exact_construction_upper']), scenario)
                           for scenario in materials['strength_scaling_scenarios']]
            records.append({'case_id': record['case_id'], 'state_id': record['state_id'], 'field': record['field'],
                'member': record['member'], 'bore': bore, 'signed_source_actions': points,
                'exact_complete_wrench_LUV': list(map(str, [wrench[0], F(0), wrench[1], wrench[2], F(0), wrench[3]])),
                'candidate': chosen, 'pressure_certificate': certificate, 'necessary_bound': lower, 'comparisons': comparisons})
        print({'case_id': record['case_id'], 'member': record['member'], 'bore_certificates': 4}, flush=True)
    source_guard(pins, inputs)
    return {'schema': 'eoere_current_cleat_bore_boundary_comparisons/v1', 'status': 'BORE_BOUNDARY_COMPARISONS_COMPLETE',
        'inputs': input_ref, 'source_sha256': pins, 'all_sources_unchanged': True,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
        'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
        'source_job': inputs['source_job'], 'geometry_proofs': geometry_proofs,
        'shared_grid': {'exact_radius_mm': str(data['radius']), 'exact_width_interval_mm': list(map(str, data['interval'])),
            'angular_sectors': len(data['angles']), 'axial_segments': len(data['axial']), 'pressure_patches': len(data['columns']),
            'normal_parameterization': 'four rational quarter-circle half-tangent charts', 'pressure_order': 'angle-major then axial'},
        'records': records, 'new_frame_response_native_FEA_or_CAD_rebuild_performed': False,
        'axial_washer_captures_remain_separate_from_bore_wall_duties': True,
        'static_boundary_LPs_performed': True, 'volume_equilibrium_or_contact_compatibility_or_fracture_proved': False,
        'complete_cleat_joint_or_finished_member_resistance': None, 'physical_demand_bounds_established': False,
        'actual_observations': None, 'structural_acceptance': False, 'panel_screw_exceedances_deferred': True,
        'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(current.ref(args.out))


if __name__ == '__main__':
    main()
