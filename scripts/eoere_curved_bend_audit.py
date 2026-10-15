"""Use admitted current fitting actions in a declared ideal curved-bend field.

No response, native or CAD solve runs. End resultants, generated end tractions,
plastic-collapse references and complete fitting acceptance stay distinct.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np

from scripts import eoere_curved_bend_field as method
from scripts.eoere_current_components import load

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT/'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/current-response-v1/joint-closure-v1'
INPUT = PACKET/'steel-curved-bend-inputs-v1.json'
RAW = ROOT/'fea/generated/selected-hardware-followup-v1/engineering-closure-v1'
ROTATION = np.array([[-1., 0., 0.], [0., 0., -1.], [0., -1., 0.]])
LOADED_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def read(ref, pins):
    path = (ROOT/ref['path']).resolve()
    require(path.is_relative_to(ROOT) and sha(path) == ref['sha256'], 'changed or foreign source: '+str(path))
    pins[ref['path']] = ref['sha256']
    return json.loads(path.read_bytes())


def gravity_partition(data, source, thickness):
    """Preserve the source total force and COM while loading the assumed bend.

    The bend has uniform force density G/Vgross. Remaining gravity resultants
    lie inside the two straight flanges. This is a declared load-distribution
    hypothesis, not measured product geometry or mass distribution.
    """
    require(len(source) == 1, 'one own source gravity resultant required')
    a, t, w, arm = thickness, thickness, data['width_mm'], data['arm_length_mm']
    b = a+t
    center = np.array([b, 0., b])
    force, point = source[0]['force'], source[0]['point']
    gross_volume = w*t*(2*arm-t)
    bend_volume = w*math.pi*(b*b-a*a)/4
    fraction = bend_volume/gross_volume
    radial_com = 4*(b**3-a**3)/(3*math.pi*(b*b-a*a))
    bend_com = np.array([b-radial_com, 0., b-radial_com])
    remaining_com = (point-fraction*bend_com)/(1-fraction)
    px = np.array([2*remaining_com[0]-t/2, remaining_com[1], t/2])
    pz = np.array([t/2, remaining_com[1], 2*remaining_com[2]-t/2])
    require(0 < fraction < 1 and b < px[0] < arm and b < pz[2] < arm
            and abs(remaining_com[1]) < w/2, 'positive gravity partition must fit the assumed straight flanges')
    straight_force = (1-fraction)*force/2
    rows = [{'point': p, 'force': straight_force, 'moment': np.zeros(3)} for p in (px, pz)]
    bend_force = fraction*force
    force_error = 2*straight_force+bend_force-force
    moment_error = sum((np.cross(r['point']-center, r['force']) for r in rows), np.zeros(3))
    moment_error += np.cross(bend_com-center, bend_force)-np.cross(point-center, force)
    require(np.linalg.norm(force_error) < 1e-10 and np.linalg.norm(moment_error) < 1e-8,
            'gravity partition changed source force or moment')
    return center, ROTATION.T@force/gross_volume, rows, {
        'source_gravity_force_local_xyz_n': force.tolist(), 'source_gravity_com_local_xyz_mm': point.tolist(),
        'bend_uniform_force_density_curved_xyz_n_mm3': (ROTATION.T@force/gross_volume).tolist(),
        'gross_reference_volume_mm3': gross_volume, 'bend_volume_mm3': bend_volume,
        'bend_mass_fraction': fraction, 'bend_com_local_xyz_mm': bend_com.tolist(),
        'straight_flange_resultant_points_local_xyz_mm': [px.tolist(), pz.tolist()],
        'each_straight_gravity_force_local_xyz_n': straight_force.tolist(),
        'total_force_error_n': force_error.tolist(), 'total_moment_about_bend_center_error_nmm': moment_error.tolist(),
        'actual_gravity_distribution_verified': False}


def reduce(field, descriptor, thickness, calculator, cell_budget):
    data, _, _, loads, source_gravity, _, integrity = calculator.own_loads(field, descriptor)
    require((data['width_mm'], data['arm_length_mm'], data['thickness_mm'],
             data['near_station_mm'], data['factory_hole_diameter_mm']) == (88.9, 88.9, 6.35, 23.8125, 10.),
            'different fitting dimensions require a separate hypothesis')
    center, density, gravity_rows, gravity_record = gravity_partition(data, source_gravity, thickness)
    minimum_station = min(r['point'][0 if r['flange'].startswith('arm-x/') else 2] for r in loads)
    hole_clearance = data['near_station_mm']-data['factory_hole_diameter_mm']/2-center[0]
    require(minimum_station > center[0] and hole_clearance > 0, 'source point actions or holes enter assumed bend')
    first = [r for r in loads if r['flange'].startswith('arm-z/')]+[gravity_rows[1]]
    last = [r for r in loads if r['flange'].startswith('arm-x/')]+[gravity_rows[0]]
    first_force, first_moment = calculator.core.wrench(first, center)
    last_force, last_moment = calculator.core.wrench(last, center)
    force = -ROTATION.T@first_force
    first_moment = -ROTATION.T@first_moment
    a = t = thickness
    w = data['width_mm']
    r1, r2 = ((a+t)**2-a*a)/2, ((a+t)**3-a**3)/3
    particular_first_moment = w*r2*np.array([density[2], 0., -density[0]])
    moment = first_moment-particular_first_moment
    params = {'a': a, 't': t, 'w': w, 'force': force.tolist(), 'moment': moment.tolist(), 'density': density.tolist()}
    # Positive-theta cut at pi/2 follows from the exact uniform-body-force
    # integrals. Reconcile its full wrench with the opposite source flange.
    predicted_force = force-w*r1*(math.pi/2)*density
    predicted_moment = moment+w*r2*np.array([0., density[2], -density[1]])
    force_error = predicted_force-ROTATION.T@last_force
    moment_error = predicted_moment-ROTATION.T@last_moment
    require(np.linalg.norm(force_error) < 1e-4 and np.linalg.norm(moment_error) < .1,
            'opposite bend end does not reconcile within the unchanged source recovery gates')
    certificate = method.enclose(params, cell_budget=cell_budget)
    return {'case_id': field['case_id'], 'state_id': field['state_id'], 'body': descriptor['body'],
            'comparison_thickness_mm': thickness, 'inside_radius_mm': thickness,
            'current_source_action_census': integrity, 'curved_cartesian_basis_columns_local_xyz': ROTATION.tolist(),
            'curve_center_local_xyz_mm': center.tolist(), 'field_parameters': params,
            'gravity_partition': gravity_record,
            'minimum_source_point_action_station_mm': float(minimum_station),
            'minimum_nominal_factory_hole_to_bend_tangent_clearance_mm': float(hole_clearance),
            'first_positive_theta_cut_force_n': force.tolist(),
            'first_positive_theta_cut_moment_about_curve_center_nmm': first_moment.tolist(),
            'opposite_end_force_reconciliation_error_n': force_error.tolist(),
            'opposite_end_moment_reconciliation_error_nmm': moment_error.tolist(),
            'opposite_end_force_reconciliation_norm_n': float(np.linalg.norm(force_error)),
            'opposite_end_moment_reconciliation_norm_nmm': float(np.linalg.norm(moment_error)),
            'certificate': certificate, 'actual_flange_interface_traction_matched': False,
            'complete_fitting_or_joint_accepted': False}


def run(input_path):
    inputs = json.loads(input_path.read_bytes())
    require(inputs['schema'] == 'current_ideal_curved_bend_inputs/v1'
            and inputs['comparisons_mm'] == [6.35, 6.0] and inputs['interval_cell_budget'] == 10000,
            'exact declared curved-bend inputs required')
    pins = {str(input_path.relative_to(ROOT)): sha(input_path)}
    for ref in inputs['implementation'].values():
        require(sha(ROOT/ref['path']) == ref['sha256'], 'changed implementation or controls')
        pins[ref['path']] = ref['sha256']
    require(inputs['implementation']['adapter']['sha256'] == LOADED_SHA
            and inputs['implementation']['field']['sha256'] == method.LOADED_SHA, 'loaded implementation differs')
    index = read(inputs['revision_index'], pins)
    require(index['current_response']['cases'] == inputs['current_response']
            and index['current_response']['components'] == inputs['current_components'], 'current authority differs')
    for role in ('geometry', 'hardware_model'):
        read(index['current_response'][role], pins)
    current = read(inputs['current_response'], pins)
    read(inputs['current_components'], pins)
    material = read(inputs['retained_material_source'], pins)
    guide = material['primary_guide']
    require(guide['minimum_yield_mpa'] == 235 and guide['minimum_tensile_mpa'] == 370
            and sha(ROOT/guide['local_path']) == guide['sha256'], 'changed conditional material reference')
    pins[guide['local_path']] = guide['sha256']
    require(current['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and current['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and current['extra_grid'] is False and len(current['cases']) == 6, 'exact current response required')
    code = inputs['frozen_steel_calculator']
    require(sha(ROOT/code['core']['path']) == code['core']['sha256'], 'changed saved-action steel helper')
    sys.path.insert(0, str((ROOT/code['calculator']['path']).parent))
    calculator = load(code['calculator'], 'current_curved_bend_saved_loads')
    require(Path(calculator.core.__file__).resolve() == (ROOT/code['core']['path']).resolve(), 'foreign steel module imported')
    pins.update({ref['path']: ref['sha256'] for ref in code.values()})
    rows = []
    for case in current['cases']:
        field = read(case['field'], pins)
        require(field['case_id'] == case['case_id'] and field['state_id'] == case['state_id']
                and len(field['source_inputs']['shafts']) == 100 and len(field['source_inputs']['hillman_rows']) == 66
                and len(field['fitting_operator_descriptors']) == 22 and not any(field['release'].values()),
                'matching unreleased 100-bolt/66-screw/22-angle field required')
        for descriptor in field['fitting_operator_descriptors']:
            rows.extend(reduce(field, descriptor, thickness, calculator, inputs['interval_cell_budget'])
                        for thickness in inputs['comparisons_mm'])
    require(len(rows) == 264 and len({(r['case_id'], r['body'], r['comparison_thickness_mm']) for r in rows}) == 264,
            'complete own fitting/case/scenario census required')
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, 'source changed during interval audit')
    summaries = []
    for thickness in inputs['comparisons_mm']:
        selected = [r for r in rows if r['comparison_thickness_mm'] == thickness]
        complete = [r for r in selected if r['certificate']['all_material_boxes_covered']]
        worst = max(complete, key=lambda r: r['certificate']['covering_upper_index_squared']) if complete else None
        summaries.append({'thickness_mm': thickness, 'inside_radius_mm': thickness, 'comparisons': len(selected),
            'everywhere_constructions_within_reference': len(complete), 'inconclusive': len(selected)-len(complete),
            'maximum_certified_upper_index_display': worst['certificate']['covering_upper_index_display'] if worst else None,
            'maximum_certified_upper_index_squared': worst['certificate']['covering_upper_index_squared'] if worst else None,
            'worst_upper_case': worst['case_id'] if worst else None, 'worst_upper_body': worst['body'] if worst else None,
            'total_visited_interval_boxes': sum(r['certificate']['visited_boxes'] for r in selected)})
    return {'schema': 'current_ideal_curved_bend_construction_audit/v1', 'status': 'IDEAL_BEND_REFERENCE_CONSTRUCTIONS_EVALUATED',
        'geometry_revision': current['geometry_revision'], 'hardware_revision': current['hardware_revision'],
        'source_sha256': pins, 'source_count': len(pins), 'summary': summaries, 'rows': rows,
        'uniform_bend_gravity_and_source_total_wrench_retained': True,
        'source_recovery_gates_n_nmm': [1e-4, .1], 'source_recovery_residuals_are_not_exact_balance': True,
        'actual_flange_interface_traction_matched': False, 'elastic_first_yield_or_stiffness_qualified': False,
        'actual_formed_fitting_or_complete_joint_resistance_qualified': False, 'structural_acceptance': False,
        'panel_screw_exceedances_deferred': True, 'native_FEA_frame_response_CAD_or_design_change': False,
        'assumptions': inputs['assumptions'], 'limits': inputs['limits'],
        'execution': {'python': platform.python_version(), 'numpy': np.__version__,
                      'command': 'uv run python -B -m scripts.eoere_curved_bend_audit --input INPUT --output OUTPUT'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(RAW) and not output.exists(), 'new owned ignored output required')
    result = run(args.input.resolve())
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'output': str(output.relative_to(ROOT)), 'bytes': output.stat().st_size,
                      'sha256': sha(output), 'summary': result['summary']}))


if __name__ == '__main__':
    main()
