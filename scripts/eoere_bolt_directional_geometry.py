"""Signed force-component end/edge screens on the retained current geometry.

Reuse the frozen 120-occurrence inventory and six original wood actions. A
projected-force screen does not qualify an oblique complete connection, free
couples, bearing reversals, fracture, shear area or the full geometry factor.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import math
from pathlib import Path

import numpy as np

from scripts import eoere_current_washer_lands as intake_source
from scripts import eoere_two_member_group_bound as ordinary

current, component = intake_source.current, intake_source.component
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/bolt-directional-geometry-inputs-v2.json'


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_current_bolt_directional_geometry_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
                    and inputs['extra_grid'] is False and inputs['actual_observations'] is None
                    and inputs['physical_demand_bounds_established'] is False
                    and inputs['structural_acceptance'] is False, 'unchanged conditional current scope required')
    current.require(inputs['force_direction_gate_n'] == 1e-5 and inputs['distance_gate_mm'] == 1e-6
                    and inputs['loaded_perpendicular_edge_multiplier'] == 4.
                    and inputs['unloaded_edge_multiplier'] == 1.5
                    and inputs['runtime_versions'] == {'numpy': '2.5.2'}, 'declared force-component markers and gates required')


def helper_sources(inputs):
    """Bind the reused ordinary-group helper and both transitive vector readers."""
    declared = {r['path']: r['sha256'] for r in inputs['references']}
    current.require(len(declared) == len(inputs['references']), 'unique declared execution sources required')
    for module in (ordinary, ordinary.front, ordinary.front.prior):
        ref = current.ref(Path(module.__file__))
        current.require(declared.get(ref['path']) == ref['sha256'] == module.LOADED_SHA,
                        'complete unchanged loaded ordinary-group execution sources required')


def directional(row, profile, shaft, action, end_method, inputs):
    current.require(action['axis_id'] == row['axis_id'] == shaft['axis_id']
                    and action['host'] == row['host'] == profile['member']
                    and action['surface_interval_mm'] == row['bearing_interval_mm'],
                    'own current action/geometry/shaft/interval join required')
    basis = np.asarray(profile['basis_grain_u_v_xyz'])
    force = np.asarray(action['force_on_host_xyz_n'], dtype=float)
    couple = np.asarray(action['moment_on_host_at_point_xyz_nmm'], dtype=float)
    point = np.asarray(action['point_xyz_mm'], dtype=float)
    lo, hi = row['bearing_interval_mm']
    center = np.asarray(shaft['point'])+.5*(lo+hi)*np.asarray(shaft['basis'][0])
    current.require(force.shape == couple.shape == point.shape == (3,) and np.isfinite(force).all()
                    and np.isfinite(couple).all() and np.isfinite(point).all()
                    and basis.shape == (3, 3) and np.isfinite(basis).all()
                    and np.linalg.norm(basis@basis.T-np.eye(3)) < 1e-8
                    and np.linalg.norm(point-center) < 1e-6
                    and np.linalg.norm(np.asarray(action['grain_axis_xyz'])-basis[0]) < 1e-8
                    and shaft['diameter_mm'] == row['nominal_diameter_mm'],
                    'finite own source vectors, midpoint, declared grain and diameter required')
    grain, edge = float(force@basis[0]), float(force@basis[row['edge_transverse_dimension']])
    bore = float(force@basis[row['bore_transverse_dimension']])
    gate, d = inputs['force_direction_gate_n'], row['nominal_diameter_mm']
    current.require(math.isfinite(d) and d > 0., 'positive own nominal diameter required')
    edges = {sign: min(r['minimum_axis_to_outer_edge_mm'] for r in row['outer_edge_distances'] if r['edge_sign'] == sign)
             for sign in (-1, 1)}
    current.require(all(math.isfinite(value) and value > 0. for value in edges.values()),
                    'two finite positive own outer edges required')
    resolved = abs(edge) > gate
    sign = int(np.sign(edge)) if resolved else None
    loaded, unloaded = edges[sign] if resolved else None, edges[-sign] if resolved else None
    # A null screen when the projected component is unresolved neither passes
    # it nor chooses a favorable direction. The full source vector is retained.
    edge_screen = None if not resolved else {
        'loaded_edge_sign': sign, 'loaded_edge_distance_mm': loaded,
        'unloaded_edge_distance_mm': unloaded,
        'loaded_requirement_mm': inputs['loaded_perpendicular_edge_multiplier']*d,
        'unloaded_requirement_mm': inputs['unloaded_edge_multiplier']*d,
        'loaded_requirement_over_distance': inputs['loaded_perpendicular_edge_multiplier']*d/loaded,
        'unloaded_requirement_over_distance': inputs['unloaded_edge_multiplier']*d/unloaded,
        'loaded_marker_pass': loaded >= inputs['loaded_perpendicular_edge_multiplier']*d-inputs['distance_gate_mm'],
        'unloaded_marker_pass': unloaded >= inputs['unloaded_edge_multiplier']*d-inputs['distance_gate_mm']}
    trials = []
    for end in row['grain_end_distances']:
        categories = []
        if abs(grain) > gate:
            categories.append('softwood_parallel_tension' if end['end_sign']*grain > 0. else 'parallel_compression')
        else:
            categories.append('softwood_parallel_tension')  # Unresolved sign: keep the reversible upper requirement.
        if resolved:
            categories.append('perpendicular')
        square = abs(abs(end['outward_normal_luv'][0])-1.) < 1e-7
        for category in categories:
            trial = end_method(end['minimum_axis_to_end_along_grain_mm'], d, category)
            trials.append({'end_sign': end['end_sign'], 'outward_normal_luv': end['outward_normal_luv'],
                           'category': category, 'parallel_sign_resolved': abs(grain) > gate,
                           'source_end_plane_square': square, 'reference_trial': trial,
                           'factor_is_complete_Cdelta': False,
                           'square_end_component_factor_if_plane_applies': trial['end_factor_only'] if square else None})
    minimum = None if any(r['reference_trial']['end_factor_only'] is None for r in trials) else min(
        r['reference_trial']['end_factor_only'] for r in trials)
    return {'axis_id': row['axis_id'], 'host': row['host'], 'surface_index': action['surface_index'],
            'own_action_point_xyz_mm': point.tolist(), 'own_force_on_host_xyz_n': force.tolist(),
            'own_free_couple_on_host_about_action_point_xyz_nmm': couple.tolist(),
            'declared_grain_force_component_n': grain, 'declared_cross_edge_force_component_n': edge,
            'declared_bore_direction_force_component_n': bore,
            'perpendicular_component_direction_resolved': resolved, 'edge_component_screen': edge_screen,
            'end_component_trials': trials, 'minimum_signed_force_end_trial': minimum,
            'any_partial_sloping_end_trial': any(not r['source_end_plane_square'] and
                                                r['reference_trial']['end_factor_only'] != 1. for r in trials),
            'complete_Cdelta': None, 'complete_joint_resistance': None,
            'physical_or_complete_code_failure_established': False}


def ordinary_minima(groups, rows):
    """The connection minimum includes both physical fasteners and all wood members.

No factor is assigned: sloping-plane and other Cdelta duties remain open.
"""
    result = []
    by_key = {(r['axis_id'], r['host']): r for r in rows}
    current.require(len(by_key) == len(rows), 'unique own wood occurrence keys required')
    for group in groups:
        hosts = [r['host'] for r in group['bearing_members'] if r['kind'] == 'wood']
        members = [by_key[(axis, host)] for axis in group['physical_axis_ids'] for host in hosts]
        values = [r['minimum_signed_force_end_trial'] for r in members]
        value = None if None in values else min(values)
        result.append({'physical_axis_ids': group['physical_axis_ids'], 'wood_hosts': hosts,
                       'own_wood_occurrences_considered': len(members),
                       'smallest_force_component_end_trial_for_entire_connection': value,
                       'partial_sloping_end_trial_present': any(r['any_partial_sloping_end_trial'] for r in members),
                       'complete_Cdelta': None, 'complete_joint_resistance': None})
    return result


def run():
    input_ref = current.ref(INPUT)
    inputs = current.read(input_ref)
    validate(inputs)
    helper_sources(inputs)
    runtime = {name: importlib.metadata.version(name) for name in inputs['runtime_versions']}
    current.require(runtime == inputs['runtime_versions'], 'declared directional-geometry runtime required')
    cases, pins = intake_source.intake()
    geometry = current.read(inputs['geometry_inventory'])
    current.require(geometry['schema'] == 'eoere_current_bolt_outer_geometry/v1'
                    and geometry['geometry_revision'] == inputs['geometry_revision']
                    and geometry['hardware_revision'] == inputs['hardware_revision']
                    and geometry['extra_grid'] is False and geometry['current_bolt_count'] == 100
                    and geometry['current_screw_count'] == 66 and geometry['structural_acceptance'] is False
                    and len(geometry['wood_bore_occurrences']) == 120 and len(geometry['member_profiles']) == 22,
                    'exact retained current outer-profile inventory required')
    refs = [input_ref, inputs['geometry_inventory'], current.ref(OWN),
            current.ref(current.ROOT/'tests/test_eoere_bolt_directional_geometry.py'),
            *inputs['references'], inputs['end_method'], inputs['supersedes_preexecution_input']]
    pins = current.join(pins, geometry['source_sha256'], {r['path']: r['sha256'] for r in refs})
    current.verify(pins)
    end_method = component.load(inputs['end_method'], 'current_directional_end_component').end_geometry_factor
    bindings = {r['case_id']: r for r in geometry['case_bindings']}
    first = cases[0][1]
    groups = ordinary.ordinary_groups(first['source_inputs']['shafts'])
    current.require(len(groups) == 46, 'all 46 ordinary physical connections required')
    outputs = []
    for binding, field, _ in cases:
        current.require(bindings[binding['case_id']] == {key: binding[key] for key in ('case_id', 'state_id', 'field')}
                        and field['source_inputs']['shafts'] == first['source_inputs']['shafts']
                        and field['source_inputs']['timber_rows'] == first['source_inputs']['timber_rows']
                        and len(field['panel_screw_actions']) == 66, 'own unchanged geometry/case/field binding required')
        shafts = {r['axis_id']: r for r in field['source_inputs']['shafts']}
        actions = {(r['axis_id'], r['host']): r for r in field['common_shaft_wood_bearing_actions']}
        current.require(len(actions) == 120 and all(r['case_id'] == binding['case_id'] and r['state_id'] == binding['state_id']
                        for r in actions.values()), 'all 120 own same-case wood actions required')
        rows = [directional(r, geometry['member_profiles'][r['host']], shafts[r['axis_id']],
                            actions[(r['axis_id'], r['host'])], end_method, inputs)
                for r in geometry['wood_bore_occurrences']]
        outputs.append({'binding': bindings[binding['case_id']], 'wood_force_component_screens': rows,
                        'ordinary_connection_end_trial_minima': ordinary_minima(groups, rows)})
    all_rows = [{'case_id': c['binding']['case_id'], **r} for c in outputs for r in c['wood_force_component_screens']]
    resolved = [r for r in all_rows if r['edge_component_screen'] is not None]
    current.verify(pins)
    helper_sources(inputs)
    current.require(current.sha(OWN) == LOADED_SHA, 'loaded directional consumer changed')
    return {'schema': 'eoere_current_bolt_directional_geometry/v1',
            'status': 'COMPLETE_CURRENT_SIGNED_FORCE_GEOMETRY_COMPONENTS_FULL_JOINT_PENDING',
            'producer': current.ref(OWN), 'inputs': input_ref, 'source_sha256': pins, 'all_sources_unchanged': True,
            'runtime_versions': runtime, 'geometry_inventory': inputs['geometry_inventory'],
            'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False, 'cases': outputs,
            'wood_occurrence_case_comparisons': len(all_rows), 'ordinary_connection_case_minima': 46*len(outputs),
            'resolved_perpendicular_component_screens': len(resolved),
            'loaded_edge_component_marker_misses': [r for r in resolved if not r['edge_component_screen']['loaded_marker_pass']],
            'unloaded_edge_component_marker_misses': [r for r in resolved if not r['edge_component_screen']['unloaded_marker_pass']],
            'worst_loaded_edge_required_over_actual': max(r['edge_component_screen']['loaded_requirement_over_distance'] for r in resolved),
            'complete_Cdelta': None, 'complete_joint_resistance': None, 'finished_member_capacity': None,
            'physical_demand_bounds_established': False, 'actual_observations': None, 'structural_acceptance': False,
            'native_or_frame_solve_CAD_query_geometry_change_or_actual_fit': False,
            'primary_source_urls': inputs['primary_source_urls'], 'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(current.ref(args.out))


if __name__ == '__main__':
    main()
