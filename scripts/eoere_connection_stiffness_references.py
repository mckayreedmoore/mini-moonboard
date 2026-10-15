"""Current bolt/reference stiffness arithmetic and its exact applicability limits.

Reuse authenticated current geometry and spring descriptors. These scalar
references do not change a spring, solve a frame or establish physical bounds.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from fea import wood_joint_patch_materials as materials
from scripts import eoere_current_washer_lands as intake_source

current = intake_source.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/connection-stiffness-reference-inputs-v2.json'


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_current_connection_stiffness_reference_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
                    and inputs['extra_grid'] is False and inputs['actual_observations'] is None
                    and inputs['physical_demand_bounds_established'] is False and inputs['structural_acceptance'] is False,
                    'unchanged unobserved current scope required')
    current.require(inputs['mean_density_sensitivities_kg_m3'] == [460., 480., 500., 520.]
                    and inputs['steel_modulus_mpa'] == 205000.
                    and inputs['purchase_root_floors_by_nominal_diameter_mm'] == {'9.525': 7.31774, '12.7': 9.9949}
                    and inputs['runtime_versions'] == {'numpy': '2.5.2'}, 'declared scalar-reference hypotheses required')


def positive(*values):
    current.require(all(math.isfinite(v) and v > 0. for v in values), 'finite positive scalar quantities required')


def ec5_slip(diameter, density):
    positive(diameter, density)
    return density**1.5*diameter/23.


def nds_group_slip(diameter):
    positive(diameter)
    current.require(6.35 <= diameter <= 25.4, 'NDS dowel-diameter scope required')
    return 180000.*(diameter/25.4)**1.5*4.4482216152605/25.4


def steel_axial(diameter, modulus, length):
    positive(diameter, modulus, length)
    return modulus*math.pi*diameter**2/(4.*length)


def series(*stiffnesses):
    current.require(bool(stiffnesses), 'nonempty series path required')
    positive(*stiffnesses)
    return 1./math.fsum(1./k for k in stiffnesses)


def normal_modulus_enclosure(compliance):
    """Rotation-invariant Rayleigh enclosure for uniaxial stress compliance.

    Engineering stress has unscaled shear components. Kelvin stress scales
    them by sqrt(2), so its Euclidean norm is the tensor Frobenius norm.
    For unit n, ||n tensor n||=1; eigenvalue bounds enclose 1/E(n).
    """
    s = np.asarray(compliance, dtype=float)
    current.require(s.shape == (6, 6) and np.isfinite(s).all() and np.allclose(s, s.T, rtol=0., atol=1e-15),
                    'finite symmetric engineering compliance required')
    scale = np.diag([1., 1., 1., 1/math.sqrt(2), 1/math.sqrt(2), 1/math.sqrt(2)])
    values = np.linalg.eigvalsh(scale@s@scale)
    current.require(values[0] > 0., 'positive definite Kelvin compliance required')
    return [float(1./values[-1]), float(1./values[0])]


def bearing_census(rows):
    families = dict(sorted(Counter('/'.join(r['bearing_member_kinds']) for r in rows).items()))
    wood = sum(len(r['own_wood_foundations']) for r in rows)
    nds = sum(r['NDS_wood_to_wood_group_action_gamma_n_mm'] is not None for r in rows)
    current.require(len(rows) == 100 and wood == 120 and nds == 16
                    and families == {'steel/steel/wood': 4, 'steel/wood': 76, 'steel/wood/wood': 4, 'wood/wood': 16},
                    'complete current 100-axis, 120-wood-bearing and 16-ordinary-wood-pair census required')
    return {'physical_bolts': 100, 'bearing_member_families': families, 'wood_bearing_occurrences': wood,
            'wood_quadrature_samples': 2*wood, 'ordinary_wood_to_wood_gamma_references': nds}


def shaft_reference(shaft, descriptors, inputs):
    diameter, bore = shaft['diameter_mm'], shaft['bore_diameter_mm']
    positive(diameter, bore)
    current.require(bore > diameter and len(shaft['ends']) == 2
                    and {e['end'] for e in shaft['ends']} == {'head', 'nut'}, 'current clear bore and two own ends required')
    captures = [r for r in descriptors if r['kind'] == 'shaft_end_capture' and r['axis_id'] == shaft['axis_id']]
    current.require(len(captures) == 2 and {r['end']['end'] for r in captures} == {'head', 'nut'}
                    and all(r['stiffness'] == 1000. and r['end'] in shaft['ends'] for r in captures),
                    'two exact current generic capture descriptors required')
    ends = {e['end']: e for e in shaft['ends']}
    length = ends['nut']['pressure_face_s_mm']-ends['head']['pressure_face_s_mm']
    positive(length)
    roots = inputs['purchase_root_floors_by_nominal_diameter_mm']
    current.require(str(diameter) in roots, 'own nominal diameter must have a recorded purchase-root reference')
    root = roots[str(diameter)]
    current.require(0. < root <= diameter, 'own root sensitivity cannot exceed the body')
    stiffnesses = {name: steel_axial(d, inputs['steel_modulus_mpa'], length) for name, d in
                   (('full_nominal_body', diameter), ('full_root_sensitivity', root))}
    chained = {name: series(k, *(r['stiffness'] for r in captures)) for name, k in stiffnesses.items()}
    wood = []
    for index, surface in enumerate(shaft['surfaces']):
        if surface['kind'] != 'wood':
            continue
        rows = [r for r in descriptors if r['kind'] == 'common_shaft_bearing' and r['axis_id'] == shaft['axis_id']
                and r['surface_index'] == index]
        own_length = surface['interval_mm'][1]-surface['interval_mm'][0]
        positive(own_length)
        current.require(len(rows) == 2 and all(r['surface'] == surface and r['kl'] > 0. for r in rows)
                        and abs(sum(r['weight_length_mm'] for r in rows)-own_length) < 1e-7,
                        'two source-bound quadrature samples covering the own wood interval required')
        k = math.fsum(r['kl'] for r in rows)
        current.require(abs(k/own_length-26.246719160104988) < 1e-7,
                        'unchanged current wood-foundation coefficient required')
        wood.append({'host': surface['host'], 'bearing_interval_mm': surface['interval_mm'],
                     'own_length_mm': own_length, 'integrated_uniform_translation_foundation_n_mm': k,
                     'foundation_is_complete_joint_slip_modulus': False})
    kinds = sorted(s['kind'] for s in shaft['surfaces'])
    return {'axis_id': shaft['axis_id'], 'nominal_diameter_mm': diameter, 'bore_diameter_mm': bore,
            'own_purchase_reference_root_floor_mm': root,
            'centered_one_sided_clearance_mm': (bore-diameter)/2., 'bearing_member_kinds': kinds,
            'own_pressure_face_distance_mm': length, 'length_is_delivered_free_bolt_length': False,
            'steel_only_axial_n_mm': stiffnesses, 'two_1000_N_mm_captures_plus_steel_series_n_mm': chained,
            'series_sensitivity_scope': 'One-dimensional illustrative series; current steel beam/capture operators are unchanged. No head/thread/washer/wood joint stiffness is qualified.',
            'full_root_change_fraction_in_declared_series': 1.-chained['full_root_sensitivity']/chained['full_nominal_body'],
            'EC5_wood_dowel_service_reference_n_mm': [{'mean_density_kg_m3': rho, 'Kser_n_mm': ec5_slip(diameter, rho)}
                                                     for rho in inputs['mean_density_sensitivities_kg_m3']],
            'EC5_reference_is_current_complete_joint_stiffness': False,
            'NDS_wood_to_wood_group_action_gamma_n_mm': nds_group_slip(diameter) if kinds == ['wood', 'wood'] else None,
            'NDS_gamma_is_general_physical_spring_law': False, 'own_wood_foundations': wood,
            'physical_axial_or_lateral_stiffness_qualified': False}


def run():
    input_ref = current.ref(INPUT)
    inputs = current.read(input_ref)
    validate(inputs)
    runtime = {name: importlib.metadata.version(name) for name in inputs['runtime_versions']}
    current.require(runtime == inputs['runtime_versions'], 'declared scalar-reference runtime required')
    cases, pins = intake_source.intake()
    refs = [input_ref, current.ref(OWN), current.ref(current.ROOT/'tests/test_eoere_connection_stiffness_references.py'),
            *inputs['references']]
    pins = current.join(pins, {r['path']: r['sha256'] for r in refs})
    current.verify(pins)
    first = cases[0][1]
    shafts, descriptors = first['source_inputs']['shafts'], first['reference_interaction_descriptors']
    current.require(len(shafts) == len({s['axis_id'] for s in shafts}) == 100 and len(cases) == 6,
                    'all current axes and six authenticated cases required')
    bindings = []
    for binding, field, components in cases:
        current.require(field['source_inputs']['shafts'] == shafts
                        and field['reference_interaction_descriptors'] == descriptors
                        and field['source_inputs']['parameters'] == first['source_inputs']['parameters']
                        and len(field['panel_screw_actions']) == 66,
                        'one unchanged geometry/law inventory across all six cases required')
        roots = components['findings']['shaft']['all100']
        own_shafts = {s['axis_id']: s for s in shafts}
        current.require(len(roots) == 100 and {r['axis_id'] for r in roots} == set(own_shafts)
                        and all(r['reference_root_floor_mm'] == inputs['purchase_root_floors_by_nominal_diameter_mm'].get(
                            str(own_shafts[r['axis_id']]['diameter_mm'])) for r in roots),
                        'root sensitivity must reuse all own current purchase-root references')
        bindings.append({k: binding[k] for k in ('case_id', 'state_id', 'field')})
    current.require(first['source_inputs']['parameters']['wood_density_kg_m3'] == 500.
                    and first['source_inputs']['parameters']['wood_bedding_n_mm3'] == 1., 'unchanged current density/bedding prior required')
    rows = [shaft_reference(s, descriptors, inputs) for s in shafts]
    census = bearing_census(rows)
    scenario = materials.material_scenario()
    enclosure = normal_modulus_enclosure(scenario['compliance_matrix_mpa_inv'])
    current.verify(pins)
    current.require(current.sha(OWN) == LOADED_SHA, 'loaded scalar-reference source changed')
    return {'schema': 'eoere_current_connection_stiffness_reference_applicability/v1',
            'status': 'COMPLETE_CURRENT_SCALAR_STIFFNESS_REFERENCES_NO_PHYSICAL_RESPONSE_BOUND',
            'producer': current.ref(OWN), 'inputs': input_ref, 'source_sha256': pins, 'all_sources_unchanged': True,
            'runtime_versions': runtime, 'geometry_revision': inputs['geometry_revision'],
            'hardware_revision': inputs['hardware_revision'], 'current_bolt_count': 100, 'current_screw_count': 66,
            'extra_grid': False, 'actual_observations': None, 'current_case_bindings': bindings, 'shaft_references': rows,
            'current_bearing_census': census,
            'EC5_scalar_reference_count': 400, 'steel_axial_reference_count': 200, 'current_wood_foundation_occurrences': 120,
            'orthotropic_scenario': scenario['scenario_id'], 'scenario_normal_modulus_enclosure_mpa': enclosure,
            'implied_compression_depth_mm_for_current_bedding_1_N_mm3': enclosure,
            'largest_full_root_change_fraction_in_declared_series': max(r['full_root_change_fraction_in_declared_series'] for r in rows),
            'physical_stiffness_contact_or_restraint_qualified': False, 'physical_demand_bounds_established': False,
            'complete_joint_resistance': None, 'finished_member_capacity': None, 'structural_acceptance': False,
            'frame_native_elastic_solve_CAD_or_geometry_change': False, 'primary_source_urls': inputs['primary_source_urls'],
            'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == '__main__':
    main()
