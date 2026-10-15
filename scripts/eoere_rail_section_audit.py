"""Continuous six-wrench rail-section bounds through the existing bore region.

Read cached solids, certify common material corridors, and reuse original
point actions and affine selfweight. Cubic Bernstein load controls and exact
section-traction certificates cover every station between source load events.
This is a section-law comparison, not volume equilibrium or brittle resistance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import math
from fractions import Fraction as F
from itertools import pairwise
from pathlib import Path

from scripts import eoere_cleat_finite_body as model
from scripts import eoere_local_timber_closure as local
from scripts import eoere_section_patches as method
from scripts.eoere_mixed_continuous_bound import read_exact

current, component = local.current, local.component
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = local.PACKET/'rail-continuous-section-inputs-v1.json'
SEQUENCE = local.SEQUENCE


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_current_rail_continuous_section_inputs/v1'
        and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
        and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
        and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
        and inputs['extra_grid'] is False and inputs['member'] == 'base_rail_top'
        and inputs['frame_half_tangent'] == '-0.363970234266'
        and inputs['projected_vertex_envelope_mm'] == '1/500000'
        and inputs['patch_inset_mm'] == '1/10000' and inputs['coordinate_decimal_digits'] == 8
        and inputs['traction_enclosure_tolerance'] == '1/10000000'
        and inputs['source_recovery_absolute_tolerance_n_nmm'] == '1/100000'
        and inputs['actual_observations'] is None and inputs['structural_acceptance'] is False
        and inputs['physical_demand_bounds_established'] is False, 'predeclared retained geometry and conditional section scope required')
    current.require(inputs['base_strengths_mpa'] == {'tension': '17/2', 'compression': '17',
        'parallel_shear': '268/125', 'rolling_shear': '268/125'}
        and inputs['runtime_versions'] == {'numpy': '2.5.2', 'scipy': '1.18.1', 'cadquery': '2.8.0', 'cadquery-ocp': '7.9.3.1.1'}
        and inputs['highs_version'] == '1.12.0', 'declared C16 scalar hypothesis and current query/LP runtimes required')
    current.require(inputs['method_helper'] == current.ref(method.OWN) and method.LOADED_SHA == inputs['method_helper']['sha256'],
                    'unchanged loaded and on-disk patch method required')


def local_wrench(force, moment, basis):
    return [method.dot(row, force) for row in basis]+[method.dot(row, moment) for row in basis]


def encode_points(points):
    return [list(map(str, point)) for point in points]


def polygon(face, origin, basis, digits):
    current.require(len(face.Wires()) == 1 and len(face.Edges()) == len(face.Vertices()) == 4
        and all(edge.geomType() == 'LINE' for edge in face.Edges()), 'one convex straight quadrilateral without holes required')
    raw = []
    for vertex in face.Vertices():
        delta = [method.rational(value)-center for value, center in zip(vertex.toTuple(), origin, strict=True)]
        current.require(abs(delta[0]) < F(1, 10**6), 'query vertex escaped its source plane')
        raw.append([method.dot(axis, delta) for axis in basis[1:]])
    center = [sum(point[i] for point in raw)/4 for i in range(2)]
    raw.sort(key=lambda point: math.atan2(float(point[1]-center[1]), float(point[0]-center[0])))
    rounded = [[round(value, digits) for value in point] for point in raw]
    rounding = max(abs(a-b) for first, second in zip(raw, rounded, strict=True) for a, b in zip(first, second, strict=True))
    current.require(rounding <= F(1, 2*10**digits), 'coordinate rounding exceeds its exact enclosure')
    return raw, rounded, rounding


def read_pinned_brep(reference, importer):
    """Import the verified byte buffer, independent of later path changes."""
    data = (current.ROOT/reference['path']).read_bytes()
    current.require(hashlib.sha256(data).hexdigest() == reference['sha256'],
                    'consumed BREP bytes changed: '+reference['path'])
    return importer(io.BytesIO(data))


def corridors(source, raw_source, central_origin, basis, interval, plane, inputs):
    import cadquery as cq

    shape, raw_shape = [read_pinned_brep(ref, cq.Shape.importBrep) for ref in (source, raw_source)]
    current.require(all(s.isValid() and len(s.Solids()) == 1 for s in (shape, raw_shape))
        and abs(shape.Volume()-source['volume_mm3']) < .01, 'own valid cached finished and raw solids required')
    current.require(all(face.geomType() == 'PLANE' for face in raw_shape.Faces())
        and all(edge.geomType() == 'LINE' for edge in raw_shape.Edges()), 'raw-stock outer enclosure requires planar straight-edged boundaries')
    outside = shape.cut(raw_shape)
    current.require(len(outside.Solids()) == 0 and outside.Volume() == 0, 'finished material escapes the original raw stock')
    face = shape.intersect(plane._plane_face(cq.Vector(*map(float, central_origin)), cq.Vector(1, 0, 0)))
    current.require(len(face.Faces()) == 3, 'three disconnected central-cut faces required')
    inner, observations = [], []
    for surface in face.Faces():
        raw, rounded, error = polygon(surface, central_origin, basis, inputs['coordinate_decimal_digits'])
        inside, outer = method.robust_boxes(rounded, F(inputs['projected_vertex_envelope_mm']), F(inputs['patch_inset_mm']))
        inner.append(inside)
        observations.append({'source_face_area_mm2': surface.Area(), 'exact_projected_vertices': encode_points(raw),
            'rounded_projected_vertices': encode_points(rounded), 'exact_max_coordinate_rounding_mm': str(error),
            'exact_inner_rectangle': list(map(str, inside)), 'exact_outer_face_rectangle': list(map(str, outer))})
    order = sorted(range(len(inner)), key=lambda i: inner[i][0])
    inner, observations = [inner[i] for i in order], [observations[i] for i in order]
    method.disjoint(inner)
    y, z = central_origin[1:]
    probe_plane = cq.Plane(origin=(float(interval[0]), float(y), float(z)), xDir=cq.Vector(*map(float, basis[1])), normal=(1, 0, 0))
    proofs = []
    for box in inner:
        p0, p1, q0, q1 = box
        probe = cq.Workplane(probe_plane).center(float((p0+p1)/2), float((q0+q1)/2)).rect(float(p1-p0), float(q1-q0)).extrude(float(interval[1]-interval[0])).val()
        missing = probe.cut(shape)
        current.require(len(missing.Solids()) == 0 and missing.Volume() == 0, 'a proposed continuous corridor leaves the cached finished wood')
        proofs.append({'query_prism_volume_mm3': probe.Volume(), 'outside_finished_volume_mm3': missing.Volume(),
                       'outside_finished_solid_count': len(missing.Solids())})
    raw_points = []
    for vertex in raw_shape.Vertices():
        delta = [method.rational(v)-o for v, o in zip(vertex.toTuple(), central_origin, strict=True)]
        raw_points.append([method.dot(axis, delta) for axis in basis[1:]])
    envelope = F(inputs['projected_vertex_envelope_mm'])
    outer = [min(point[0] for point in raw_points)-envelope, max(point[0] for point in raw_points)+envelope,
             min(point[1] for point in raw_points)-envelope, max(point[1] for point in raw_points)+envelope]
    current.require(all(a <= c <= d <= b for a, b, c, d in [(outer[0], outer[1], box[0], box[1]) for box in inner])
        and all(outer[2] <= box[2] < box[3] <= outer[3] for box in inner), 'common patches escape the raw-stock outer enclosure')
    return inner, outer, {'central_origin_xyz_mm': list(map(str, central_origin)),
        'central_cut_area_mm2': face.Area(), 'face_count': 3, 'faces': observations, 'corridor_queries': proofs,
        'finished_outside_raw_volume_mm3': outside.Volume(), 'exact_outer_rectangle': list(map(str, outer)),
        'vertex_envelope_is_an_adopted_CAD_query_assumption': True, 'physical_cut_tolerance_or_inspection_qualified': False}


def source_case(field, member, helper, interval):
    current.require(member['axis'] == [1., 0., 0.], 'current X-grain rail required')
    actions, gravity = helper.own.member_point_inputs(field)
    points = [[list(map(method.rational, values)) for values in row] for row in actions[member['name']]]
    center, weight = [list(map(method.rational, values)) for values in gravity[member['name']]]
    events = sorted({point[0] for point, force, couple in points if interval[0] < point[0] < interval[1] and any(force+couple)})
    return points, center, weight, events


def span_controls(first, last, points, center, gravity, low, high, transverse, basis):
    first, last = F(first), F(last)
    current.require(first < last and not any(first < point[0][0] < last and any(point[1]+point[2]) for point in points),
                    'uncounted nonzero source event inside cubic span')
    selected = [point for point in points if point[0][0] <= first]
    def value(t):
        return local_wrench(*method.cut_wrench(first+t*(last-first), transverse, low, high, center, gravity, selected), basis)
    samples = [value(t) for t in (F(0), F(1, 3), F(2, 3), F(1))]
    controls = method.cubic_controls(samples)
    current.require(all(method.evaluate_controls(controls, t) == value(t) for t in (F(1, 7), F(2, 5), F(5, 8))),
                    'source cubic wrench identity failed')
    return controls, samples, len(selected)


def comparison(lower, upper, scenario):
    scale = method.rational(scenario['strength_divisor'])*method.rational(scenario['whole_wrench_multiplier'])
    current.require(0 <= lower <= upper and scale > 0, 'ordered nonnegative bounds and positive scenario required')
    lo, hi = lower*scale, upper*scale
    status = 'section_hypothesis_fails_at_a_recorded_actual_station' if lo > 1 else (
        'continuous_section_traction_construction_within_hypothesis' if hi <= 1 else 'section_hypothesis_inconclusive')
    return {**scenario, 'exact_necessary_actual_station_lower': str(lo), 'exact_continuous_construction_upper': str(hi),
        'necessary_actual_station_lower': float(lo), 'continuous_construction_upper': float(hi), 'disposition': status,
        'complete_member_or_joint_resistance': None, 'physical_failure_established': False}


def source_guard(pins, inputs):
    from scipy.optimize._highspy import _core

    current.require(current.sha(OWN) == LOADED_SHA and current.sha(method.OWN) == method.LOADED_SHA,
                    'loaded rail or patch producer changed')
    current.require({key: importlib.metadata.version(key) for key in inputs['runtime_versions']} == inputs['runtime_versions'],
                    'declared query and numerical runtimes required')
    current.require('.'.join(str(getattr(_core, 'HIGHS_VERSION_'+part)) for part in ('MAJOR', 'MINOR', 'PATCH')) == inputs['highs_version'],
                    'declared LP runtime required')
    model.verify_execution_sources(pins)


def run():
    own_input = current.ref(INPUT)
    inputs = read_exact(own_input)
    validate(inputs)
    parent = read_exact(inputs['local_queries'])
    material = read_exact(inputs['material_hypothesis'])
    method.section.validate_assumptions(material)
    current.require(parent['schema'] == 'eoere_current_local_timber_closure_queries/v1'
        and parent['all_input_sources_unchanged'] is True and parent['geometry_revision'] == inputs['geometry_revision']
        and parent['hardware_revision'] == inputs['hardware_revision'] and parent['extra_grid'] is False
        and [case['case_id'] for case in parent['cases']] == SEQUENCE, 'completed own six-case local queries required')
    fields = [read_exact(case['field']) for case in parent['cases']]
    members = [next(row for row in field['source_inputs']['timber_rows'] if row['name'] == inputs['member']) for field in fields]
    current.require(all(member == members[0] for member in members), 'same own rail geometry in all six states required')
    member = members[0]
    raw_source = member['raw_profile_source']['raw_native_body']
    source = parent['top_rail_finished_source']
    refs = [own_input, inputs['local_queries'], inputs['material_hypothesis'], inputs['reference_pdf'], inputs['method_helper'],
            current.ref(OWN), current.ref(current.ROOT/'tests/test_eoere_section_patches.py'),
            current.ref(current.ROOT/'tests/test_eoere_rail_section_audit.py'), *inputs['execution_sources'], source, raw_source]
    pins = current.join(parent['source_sha256'], {ref['path']: ref['sha256'] for ref in refs})
    current.verify(pins)
    helper = component.load(local.targeted.METHODS['cuts'], 'current_rail_section_cut_source')
    plane = component.load(local.targeted.METHODS['plane'], 'current_rail_section_query_source')
    pins = current.join(pins, helper.source_pins())
    basis = method.frame(inputs['frame_half_tangent'])
    low, high = map(method.rational, member['source_centerline_grain_interval_mm'])
    interval = tuple(map(method.rational, [min(row['station_global_grain_projection_mm'] for row in parent['top_rail_finished_sections']),
                                         max(row['station_global_grain_projection_mm'] for row in parent['top_rail_finished_sections'])]))
    origins = [row['properties']['section_origin_xyz_mm'] for row in parent['top_rail_finished_sections']]
    transverse = list(map(method.rational, origins[0][1:]))
    current.require(all(list(map(method.rational, point[1:])) == transverse for point in origins), 'one unchanged rail centerline cut datum required')
    central = [method.rational(inputs['central_station_mm']), *transverse]
    # All bound records and source hashes authenticate before cached geometry.
    inner, outer, geometry = corridors(source, raw_source, central, basis, interval, plane, inputs)
    source_guard(pins, inputs)
    strengths = {key: F(value) for key, value in inputs['base_strengths_mpa'].items()}
    cases, all_events = [], set()
    for binding, field in zip(parent['cases'], fields, strict=True):
        current.require(field['case_id'] == binding['case_id'] and field['state_id'] == binding['state_id'], 'own original field/state binding required')
        points, center, gravity, events = source_case(field, member, helper, interval)
        all_events.update(events)
        recovery = []
        for row in parent['top_rail_finished_sections']:
            old = next(record for record in row['case_comparisons'] if record['case_id'] == binding['case_id'])['linear_normal_stress']['signed_same_cut_wrench']
            origin = list(map(method.rational, old['cut_point_xyz_mm']))
            selected = [point for point in points if point[0][0] < origin[0]]
            force, moment = method.cut_wrench(origin[0], origin[1:], low, high, center, gravity, selected)
            errors = [abs(a-method.rational(b)) for values, key in [(force, 'force_on_lower_portion_xyz_n'), (moment, 'moment_on_lower_portion_about_cut_xyz_nmm')]
                      for a, b in zip(values, old[key], strict=True)]
            current.require(max(errors) < F(inputs['source_recovery_absolute_tolerance_n_nmm']), 'exact source recovery differs from the frozen query')
            recovery.append({'source_station_mm': str(origin[0]), 'exact_maximum_old_float_recovery_difference': str(max(errors))})
        endpoints = [interval[0], *events, interval[1]]
        spans = []
        for first, last in pairwise(endpoints):
            controls, samples, selected_count = span_controls(first, last, points, center, gravity, low, high, transverse, basis)
            certificates, selected_multipliers = [], []
            for control in controls:
                chosen = method.candidate(control, inner, strengths)
                certified = method.certify(control, inner, strengths, chosen['corner_tractions_n_mm2'], F(inputs['traction_enclosure_tolerance']))
                certificates.append({'candidate': chosen, 'certificate': certified})
                selected_multipliers.append(chosen['dual_multiplier'])
            necessary, support_cache = [], {}
            for t, sample in zip((F(0), F(1, 3), F(2, 3), F(1)), samples, strict=True):
                candidates = []
                for multiplier in selected_multipliers:
                    key = tuple(map(method.rational, multiplier))
                    work = method.dot(key, sample)
                    if work < 0:
                        key, work = tuple(-value for value in key), -work
                    if key not in support_cache:
                        support_cache[key] = method.necessary(key, sample, [outer], strengths)
                    template = support_cache[key]
                    lower = work/F(template['exact_outer_support'])
                    candidates.append({**template, 'exact_work': str(work), 'exact_necessary_lower': str(lower), 'necessary_lower': float(lower)})
                winner = max(candidates, key=lambda row: F(row['exact_necessary_lower']))
                necessary.append({'exact_span_fraction': str(t), 'exact_station_mm': str(first+t*(last-first)), **winner})
            upper = max(F(row['certificate']['exact_construction_upper']) for row in certificates)
            lower = max(F(row['exact_necessary_lower']) for row in necessary)
            current.require(lower <= upper, 'continuous necessary lower exceeds the constructed span upper')
            scenarios = [comparison(lower, upper, scenario) for scenario in material['strength_scaling_scenarios']]
            spans.append({'exact_station_interval_mm': list(map(str, (first, last))),
                'left_trace': 'after all source events at left endpoint', 'right_trace': 'before all source events at right endpoint',
                'included_source_point_count': selected_count, 'exact_cubic_wrench_controls': encode_points(controls),
                'control_traction_certificates': certificates, 'necessary_actual_station_tests': necessary, 'scenarios': scenarios})
        cases.append({'binding': binding, 'exact_nonzero_source_event_stations_mm': list(map(str, events)),
            'source_point_action_count': len(points), 'old_query_recovery_comparisons': recovery, 'spans': spans})
        print({'case_id': binding['case_id'], 'source_spans': len(spans), 'working_upper': max(s['scenarios'][0]['continuous_construction_upper'] for s in spans)}, flush=True)
    current.require(sorted(all_events) == list(map(F, inputs['expected_nonzero_source_event_stations_mm'])), 'complete frozen source event census differs')
    source_guard(pins, inputs)
    return {'schema': 'eoere_current_rail_continuous_section_bounds/v1', 'status': 'CONTINUOUS_BORE_REGION_SECTION_COMPARISONS_COMPLETE',
        'inputs': own_input, 'source_sha256': pins, 'all_sources_unchanged': True,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
        'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False, 'member': inputs['member'],
        'finished_source': source, 'raw_stock_source': raw_source, 'exact_basis_grain_p_q': encode_points(basis),
        'exact_station_interval_mm': list(map(str, interval)), 'geometry': geometry, 'cases': cases,
        'static_section_LPs_performed': True, 'new_frame_response_native_FEA_or_CAD_rebuild_performed': False,
        'continuous_section_law_only': True, 'volume_equilibrium_or_free_side_tractions_or_compatibility_proved': False,
        'complete_joint_or_cleat_or_finished_member_resistance': None, 'physical_demand_bounds_established': False,
        'actual_observations': None, 'structural_acceptance': False, 'panel_screw_exceedances_deferred': True,
        'runtime_versions': inputs['runtime_versions'], 'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(current.ref(args.out))


if __name__ == '__main__':
    main()
