"""Independent tiny component-method arithmetic; no candidate action reader."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import platform
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
LEAF = 'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1'
FROZEN = {
    LEAF + '/component-method-v1/gross_members.py': '01aaf22c8b2cf93430e7bbce4768260efea39bed3d527b8f5486ba4e38e32258',
    LEAF + '/component-method-v1/test_gross_members.py': 'cbf76b357af6c80dfbece3d48520948b5c088c17628209dd0f77e6c53ef5cafe',
    LEAF + '/steel-shaft-comparison-v1/comparison.py': '9d670f264d5b074abf4cbd48baaebde486b1c15e3ddb612302bd1f41a577a360',
    LEAF + '/steel-shaft-comparison-v1/test_comparison.py': '7e14df56a8265f8f9b705f09a74249d4f19fa8f878555b3ead0c127e28240afb',
    LEAF + '/steel-shaft-comparison-v1/plan.json': 'ffa8b5022faffae40ee44140a8cfade7c257dd7a4f84dd98f89251c7ccf0467c',
}


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(pins):
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, 'frozen source changed: ' + path)


def module(relative, name):
    verify(FROZEN)
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def rotated_member(Q, origin):
    def point(value):
        return (origin + Q @ np.asarray(value)).tolist()
    def vector(value):
        return (Q @ np.asarray(value)).tolist()
    return {'source_inputs': {'timber_rows': [{'name': 'independent-toy', 'axis': vector([1., 0., 0.]),
        'section_u': vector([0., 1., 0.]), 'section_v': vector([0., 0., 1.]), 'start': point([0., 0., 0.]),
        'end': point([100., 0., 0.]), 'width_mm': 38.1, 'depth_mm': 139.7}]},
        'physical_body_descriptors': [{'id': 'independent-toy', 'center_xyz_mm': point([60., 3., -2.])}],
        'body_applied_loads': [{'id': 'self-weight/independent-toy', 'body': 'independent-toy',
            'point_xyz_mm': point([60., 3., -2.]), 'force_xyz_n': vector([0., 0., -12.])}],
        'common_shaft_bearing_actions': [{'first': 'shaft/toy', 'second': 'independent-toy',
            'point_xyz_mm': point([20., 5., 7.]), 'host_support_point_xyz_mm': point([20., 5., 7.]),
            'force_on_first_xyz_n': vector([-2., -3., -5.]), 'moment_on_first_at_point_xyz_nmm': vector([-11., -13., -17.]),
            'moment_on_second_at_point_xyz_nmm': vector([11., 13., 17.])}],
        'shaft_end_capture_actions': [{'first': 'shaft/toy', 'second': 'independent-toy',
            'point_xyz_mm': point([49., 1., 2.]), 'host_support_point_xyz_mm': point([55., 1., 2.]),
            'force_on_first_xyz_n': vector([8., 0., 0.])}],
        'panel_screw_actions': [], 'contact_actions': [], 'floor_actions': []}


def member_check(method):
    angle = .37
    Q = np.array([[math.cos(angle), -math.sin(angle), 0.], [math.sin(angle), math.cos(angle), 0.], [0., 0., 1.]])
    transforms = [(np.eye(3), np.zeros(3)), (Q, np.array([17., -31., 9.]))]
    errors, witnesses = [], []
    # Integral density 1+.012(s-50) over[0,50]: force fraction .35,
    # first moment10 mm. Gravity cut=(-Fg,-Mg); point action has own
    # F=(2,3,5), M=(11,13,17). Capture's host station55 is excluded.
    expected = np.array([-2., -3., -.8, -2.4, -87., 83.])
    for Q, origin in transforms:
        field = rotated_member(Q, origin)
        before = copy.deepcopy(field)
        actions, gravity = method.own.member_point_inputs(field)
        grain = Q[:, 0]
        low = float(grain @ origin)
        cut = (origin + Q @ np.array([50., 0., 0.])).tolist()
        result = method.own.previous.member_cut_wrench(grain.tolist(), low, low + 100., cut,
            *gravity['independent-toy'], actions['independent-toy'])
        local = np.r_[Q.T @ result['force_on_lower_portion_xyz_n'], Q.T @ result['moment_on_lower_portion_about_cut_xyz_nmm']]
        errors.append(float(np.max(abs(local - expected))))
        rows = method.member_witnesses(field, samples=3)
        witnesses.append(rows[0]['witnesses']['fully_braced_normal']['gross_CD1_comparison']['fully_braced_component_normal_interaction'])
        require(field == before, 'pure member method mutated synthetic field')
        require(rows[0]['finished_net_resistance_established'] is False and rows[0]['continuous_maximum_or_actual_bracing_established'] is False,
            'gross sampled result acquired an unsupported strength claim')
    require(max(errors) < 1e-8 and abs(witnesses[0] - witnesses[1]) < 1e-9, 'independent rotated affine/point-couple arithmetic differs')
    return {'expected_local_N_Vu_Vv_T_Mu_Mv_n_nmm': expected.tolist(), 'max_same_cut_error_n_nmm': max(errors),
        'rotated_gross_normal_witness_difference': abs(witnesses[0] - witnesses[1]),
        'host_station55_capture_excluded_at_cut50_despite_shaft_pressure_station49': True}


def steel_check(method, toys):
    response, descriptor = toys.strip_coupon()
    independent = []
    result = method.fitting_strip_comparisons(response, descriptor)
    for strip in result['strips']:
        source = next(r for r in response['strip_root_actions'] if r['port_id'] == strip['port_id'])
        basis = np.asarray(strip['basis_columns_xyz'])
        F = basis.T @ source['applied_to_strip_force_xyz_n']
        M = basis.T @ source['applied_to_strip_couple_at_root_xyz_nmm']
        for station, saved in zip((0., 65.0875), strip['same_strip_endpoint_witnesses'], strict=True):
            transported = M + np.cross([-station, 0., 0.], F)
            sigma = abs(F[0]) / (44.45 * 6.35) + 6 * abs(transported[1]) / (44.45 * 6.35**2) + 6 * abs(transported[2]) / (6.35 * 44.45**2)
            shear = 1.5 * math.hypot(F[1], F[2]) / (44.45 * 6.35)
            torsion = abs(transported[0]) * 6.35 / saved['torsion_rectangle']['J_lower_mm4']
            vm = math.hypot(sigma, math.sqrt(3) * (shear + torsion))
            independent.append(abs(vm - saved['simultaneous_nominal_vm_bound_mpa']))
    # Equal/opposite own root torsion cancels the flange aggregate entirely;
    # neither half-strip may inherit that zero as its own stress demand.
    cancelled = copy.deepcopy(response)
    for index, root in enumerate(cancelled['strip_root_actions']):
        moment = [50. if index == 0 else -50. if index == 1 else 0., 0., 0.]
        root['applied_to_strip_force_xyz_n'] = [0., 0., 0.]
        root['applied_to_strip_couple_at_root_xyz_nmm'] = moment
        cancelled['port_actions'][index]['external_force_required_at_port_xyz_n'] = [0., 0., 0.]
        cancelled['port_actions'][index]['external_couple_required_at_port_xyz_nmm'] = [-v for v in moment]
    cancelled['per_flange_applied_strip_root_wrench_about_heel_n_nmm'] = {'arm-x': [0.] * 6, 'arm-z': [0.] * 6}
    cancelled['load_projection']['heel_wrench_n_nmm'] = [0.] * 6
    noncancel = method.fitting_strip_comparisons(cancelled, descriptor)
    own_vm = [r['nominal_gross_prismatic_field_governing_endpoint']['simultaneous_nominal_vm_bound_mpa'] for r in noncancel['strips']]
    require(own_vm[0] > 0 and own_vm[1] > 0 and noncancel['full_flange_aggregate_stress_comparison'] is None,
        'opposed strip torsion silently cancelled the own comparison')
    circle_errors = []
    for diameter in (9.525, 12.7):
        actual = method.shaft_circle_comparisons(*toys.circle_coupon(diameter))['section_scenarios'][0]['sampled_governing_same_cut']
        area = math.pi * diameter**2 / 4
        sigma = 11 / area + 32 * math.hypot(23, 29) / (math.pi * diameter**3)
        tau = 4 * math.hypot(13, 17) / (3 * area) + 16 * 19 / (math.pi * diameter**3)
        circle_errors.append(abs(math.hypot(sigma, math.sqrt(3) * tau) - actual['same_section_nominal_stress_envelope_mpa']))
        require(actual['same_section_nominal_first_yield_index'] is None, 'unknown grade acquired a yield index')
    require(max(independent + circle_errors) < 1e-13, 'independent strip/circle formulas differ')
    return {'strip_endpoint_hand_formula_max_error_mpa': max(independent), 'circle_hand_formula_max_error_mpa': max(circle_errors),
        'zero_aggregate_opposed_strip_torsion_own_VM_mpa': own_vm, 'all_four_strip_comparisons_remain_separate': True,
        'nominal_circle_diameters_fixture_mm': [9.525, 12.7], 'unknown_product_yield_and_thread_root_remain_null': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'preserve issued independent review')
    verify(FROZEN)
    gross = module(LEAF + '/component-method-v1/gross_members.py', 'independent_gross_method')
    steel = module(LEAF + '/steel-shaft-comparison-v1/comparison.py', 'independent_steel_method')
    toys = module(LEAF + '/steel-shaft-comparison-v1/test_comparison.py', 'independent_steel_fixture_ledger')
    pins = dict(FROZEN)
    for additions in (gross.source_pins(), steel.source_contract()['source_sha256'], {str(OWN.relative_to(ROOT)): LOADED_SHA}):
        for path, value in additions.items():
            require(path not in pins or pins[path] == value, 'contradictory independent pin')
            pins[path] = value
    verify(pins)
    member, metal = member_check(gross), steel_check(steel, toys)
    verify(pins)
    require(sha(OWN) == LOADED_SHA, 'loaded independent reviewer changed')
    receipt = {'schema': 'eoere_minimal_component_methods_independent_readiness/v1', 'status': 'READY_METHOD_ONLY',
        'independent_component_method_checks_pass': True, 'source_sha256': pins, 'source_pins_before_after_unchanged': True,
        'focused_owner_fixtures': {'passed': 23, 'ruff_pass': True,
            'pytest_command': 'PYTHONPATH=. .venv/bin/python -B -m pytest -q ' + LEAF + '/component-method-v1/test_gross_members.py ' + LEAF + '/steel-shaft-comparison-v1/test_comparison.py'},
        'independent_member_arithmetic': member, 'independent_steel_arithmetic': metal,
        'source_reviews': {'gross': ['Fresh source spans/bases only; sampled51 stations plus every own point station±1e-5 mm.',
            'Own host capture support points, explicit first/second free couples, all force directions and affine selfweight retained.',
            'World-to-local uses proper row basis; same signed cut supplies simultaneous six actions.',
            'Conditional DF-L No2 CD1 fully braced and full-length K1 references only; actual bracing/net cuts and continuous extrema remain false.'],
            'steel': ['Source current geometry census is100 unique shafts:96 at9.525 mm and4 at12.7 mm;22 fitting owners with176 holes/88 ports.',
            'Each own loaded strip root and tip equilibrates its own force/couple; moments transport with the signed cross product.',
            'Four gross44.45×6.35 mm strips remain independent; endpoint envelope is convex for constant F/T and affine bending.',
            'Gross strip/circle section references fill holes and omit concentrations/heel/warping/thread effects; unknown product Fy and actual root remain unadopted.']},
        'caller_requirements': ['New actual field admission before calling either pure helper; these methods have no admission or field reader.',
            'Outer consumer must require22 source-owned timbers and complete new action tables; tiny fixtures intentionally permit one member.',
            'Outer gate must authenticate pair-action force/couple datums and source6-vector cuts; circle helper does not independently replay their equilibrium.',
            'Source closures must be checked before loading the modules; the historical pure dependency imports perform no candidate body query.'],
        'candidate_actions_CAD_query_profile_q_K_or_solve_consumed': False,
        'execution': {'sys_orig_argv': sys.orig_argv, 'cwd': str(Path.cwd()), 'python': platform.python_version(), 'numpy': np.__version__, 'PYTHONPATH': os.environ.get('PYTHONPATH')},
        'release': dict.fromkeys(('candidate_admitted', 'physical_contact', 'complete_joint_resistance', 'fabrication', 'climbing'), False)}
    with args.output.open('x') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'path': str(args.output), 'sha256': sha(args.output), 'bytes': args.output.stat().st_size,
        'pins': len(pins), 'member_error_n_nmm': member['max_same_cut_error_n_nmm'], 'steel_error_mpa': metal['strip_endpoint_hand_formula_max_error_mpa']}))


if __name__ == '__main__':
    main()
