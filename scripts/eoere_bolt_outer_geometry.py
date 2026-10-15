"""All current wood-bore outer-profile end/edge components, without CAD rebuild.

Compound end cuts, changed raw union extents and either stock transverse bore
direction require more than the frozen front-only helper. Use source vertices
and the separate finished cleat polygon; never correct a frozen source in place.
Outer end/edge distances do not cover intervening bores, channels or fracture.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import math
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

from scripts import eoere_current_washer_lands as intake_source

current, component = intake_source.current, intake_source.component
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/bolt-outer-geometry-inputs-v1.json'


def profile_vertices(profile):
    basis = np.asarray(profile['basis_grain_u_v_xyz'], dtype=float)
    datum = np.asarray(profile['datum_xyz_mm'], dtype=float)
    points = np.asarray(profile['raw_profile_vertices_luv_mm'], dtype=float)
    current.require(basis.shape == (3, 3) and datum.shape == (3,) and points.ndim == 2
                    and points.shape[1] == 3 and np.isfinite(points).all() and np.isfinite(basis).all()
                    and np.isfinite(datum).all() and np.linalg.norm(basis@basis.T-np.eye(3)) < 1e-8
                    and np.linalg.det(basis) > 0., 'finite right-handed orthonormal stock vertices required')
    interpretation = 'source raw-profile vertices; frozen end offsets unchanged'
    if 'finished_YZ_polygon_mm' in profile:
        polygon = np.asarray(profile['finished_YZ_polygon_mm'], dtype=float)
        current.require(profile['member'] in ('eoere_cleat_left', 'eoere_cleat_right')
                        and polygon.shape == (4, 2) and np.isfinite(polygon).all()
                        and np.allclose(basis, [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]], rtol=0., atol=1e-10)
                        and abs(points[:, 1].min()) < 1e-8 and abs(points[:, 1].max()-38.1) < 1e-8,
                        'own current vertical-grain cleat scenario and finished polygon required')
        points = np.array([basis@(np.array([datum[0]+x, y, z])-datum)
                           for x in (0., 38.1) for y, z in polygon])
        interpretation = 'source finished sloping cleat polygon; gross rectangular analysis blank is not its end boundary'
    current.require(len(np.unique(points, axis=0)) >= 4, 'nondegenerate source profile required')
    return basis, datum, points, interpretation


def outer_profile(profile):
    basis, datum, points, interpretation = profile_vertices(profile)
    hull = ConvexHull(points)
    current.require(math.isfinite(hull.volume) and hull.volume > 0., 'positive three-dimensional profile hull required')
    planes = []
    for equation in hull.equations:
        normal, offset = equation[:3], -float(equation[3])
        current.require(abs(np.linalg.norm(normal)-1.) < 1e-8
                        and np.max(points@normal-offset) < 1e-5, 'outward unit hull equation required')
        if any(np.linalg.norm(normal-np.asarray(p['normal_luv'])) < 1e-7
               and abs(offset-p['offset_luv_mm']) < 1e-5 for p in planes):
            continue
        world = basis.T@normal
        planes.append({'normal_luv': normal.tolist(), 'offset_luv_mm': offset,
                       'normal_xyz': world.tolist(), 'offset_world_mm': offset+float(world@datum)})
    ends = [p for p in planes if abs(p['normal_luv'][0]) > 1e-7]
    current.require({int(np.sign(p['normal_luv'][0])) for p in ends} == {-1, 1},
                    'bounded grain directions required')
    return {'member': profile['member'], 'basis_grain_u_v_xyz': basis.tolist(), 'datum_xyz_mm': datum.tolist(),
            'vertices_luv_mm': points.tolist(), 'interpretation': interpretation, 'outer_planes': planes,
            'profile_hull_volume_mm3': float(hull.volume),
            'all_grain_end_planes_square': all(abs(abs(p['normal_luv'][0])-1.) < 1e-7 for p in ends)}


def placement(profile, shaft, surface, end_method):
    current.require(surface['kind'] == 'wood' and surface['host'] == profile['member']
                    and surface in shaft['surfaces'], 'own wood/profile/shaft join required')
    basis, datum = np.asarray(profile['basis_grain_u_v_xyz']), np.asarray(profile['datum_xyz_mm'])
    direction, point = np.asarray(shaft['basis'][0]), np.asarray(shaft['point'])
    local_axis = basis@direction
    current.require(abs(local_axis[0]) < 1e-8 and abs(np.linalg.norm(direction)-1.) < 1e-8,
                    'current perpendicular-grain unit bore scenario required')
    bore_dim = int(np.argmax(abs(local_axis)))
    current.require(bore_dim in (1, 2) and abs(abs(local_axis[bore_dim])-1.) < 1e-8,
                    'bore must traverse one own stock transverse axis')
    edge_dim = 3-bore_dim
    interval = np.asarray(surface['interval_mm'], dtype=float)
    current.require(interval.shape == (2,) and np.isfinite(interval).all() and interval[1] > interval[0],
                    'positive own bearing interval required')
    points = np.array([basis@(point+s*direction-datum) for s in interval])
    ends, edges = [], []
    for plane in profile['outer_planes']:
        normal = np.asarray(plane['normal_luv'])
        clear = plane['offset_luv_mm']-points@normal
        current.require(np.min(clear) >= -1e-5, 'own bearing interval must lie inside the source outer profile')
        if abs(normal[0]) > 1e-7:
            ends.append({'end_sign': int(np.sign(normal[0])), 'outward_normal_luv': normal.tolist(),
                         'minimum_axis_to_end_along_grain_mm': max(0., float(np.min(clear)/abs(normal[0])))})
        elif abs(normal[edge_dim]) > 1e-7:
            edges.append({'edge_sign': int(np.sign(normal[edge_dim])),
                          'minimum_axis_to_outer_edge_mm': max(0., float(np.min(clear)/abs(normal[edge_dim])))})
    current.require({r['edge_sign'] for r in edges} == {-1, 1}, 'two own cross-grain outer edges required')
    end = min(r['minimum_axis_to_end_along_grain_mm'] for r in ends)
    edge = min(r['minimum_axis_to_outer_edge_mm'] for r in edges)
    diameter = shaft['diameter_mm']
    current.require(math.isfinite(diameter) and diameter > 0., 'positive own nominal bolt diameter required')
    trial = end_method(end, diameter, 'softwood_parallel_tension')
    # The existing helper supplies a square-end component only. Keep its
    # partial value on sloping profiles as an explicitly unadopted trial.
    applicable = profile['all_grain_end_planes_square']
    return {'axis_id': shaft['axis_id'], 'host': surface['host'], 'nominal_diameter_mm': diameter,
            'bearing_interval_mm': surface['interval_mm'], 'bore_transverse_dimension': bore_dim,
            'edge_transverse_dimension': edge_dim, 'grain_end_distances': ends, 'outer_edge_distances': edges,
            'minimum_grain_end_distance_mm': end, 'minimum_outer_edge_distance_mm': edge,
            'full_7D_end_marker_pass': end >= 7.*diameter-1e-6,
            'full_4D_outer_edge_marker_pass': edge >= 4.*diameter-1e-6,
            'square_end_component_trial': trial, 'square_end_component_applicable': applicable,
            'square_end_component_factor_if_profile_applies': trial['end_factor_only'] if applicable else None,
            'complete_Cdelta': None, 'complete_joint_resistance': None,
            'marker_miss_is_adopted_failure': False}


def confirm_faces(shape, profile):
    """Confirm hull planes against cached faces; retain other cut faces explicitly.

All vertex containment is a diagnostic, not a curved-boundary containment
proof or a claim that intervening cuts leave a complete timber ligament.
"""
    planes = profile['outer_planes']
    found, extra, curved = set(), [], Counter()
    for face in shape.Faces():
        kind = face.geomType()
        if kind != 'PLANE':
            curved[kind] += 1
            continue
        normal, point = np.asarray(face.normalAt().toTuple()), np.asarray(face.Center().toTuple())
        matches = [i for i, p in enumerate(planes) if np.linalg.norm(normal-p['normal_xyz']) < 1e-7
                   and abs(float(normal@point)-p['offset_world_mm']) < 1e-4]
        current.require(len(matches) <= 1, 'ambiguous cached face/profile-plane identity')
        if matches:
            found.add(matches[0])
        else:
            extra.append({'outward_normal_xyz': normal.tolist(), 'point_xyz_mm': point.tolist(),
                          'area_mm2': float(face.Area())})
    vertices = np.array([v.toTuple() for v in shape.Vertices()])
    violation = max(float(np.max(vertices@np.asarray(p['normal_xyz'])-p['offset_world_mm'])) for p in planes)
    return {'profile_plane_count': len(planes), 'matched_profile_planes': sorted(found),
            'all_profile_planes_present_on_cached_finished_faces': found == set(range(len(planes))),
            'maximum_cached_vertex_outer_hull_violation_mm': violation,
            'cached_vertices_within_outer_hull': violation <= 1e-4,
            'additional_finished_planar_faces': extra, 'other_finished_face_types': dict(curved),
            'complete_finished_ligament_or_curved_containment_proven': False}


def run():
    input_ref = current.ref(INPUT)
    inputs = current.read(input_ref)
    current.require(inputs['schema'] == 'eoere_current_bolt_outer_geometry_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
                    and inputs['extra_grid'] is False and inputs['actual_observations'] is None
                    and inputs['structural_acceptance'] is False, 'unchanged unobserved current geometry required')
    runtime = {name: importlib.metadata.version(name) for name in inputs['runtime_versions']}
    current.require(runtime == inputs['runtime_versions'], 'pinned geometry-query runtime required')
    cases, pins = intake_source.intake()
    refs = [input_ref, current.ref(OWN), current.ref(current.ROOT/'tests/test_eoere_bolt_outer_geometry.py'),
            *inputs['references'], *inputs['methods'].values()]
    pins = current.join(pins, {r['path']: r['sha256'] for r in refs})
    current.verify(pins)
    end_method = component.load(inputs['methods']['end_component'], 'current_outer_end_component').end_geometry_factor
    container = component.load(inputs['methods']['container'], 'current_outer_container')
    reference = component.load(inputs['methods']['distance'], 'current_outer_distance')
    reference.tools()
    known = container.known_answer(reference)
    first = cases[0][1]
    members = {r['name']: r for r in first['source_inputs']['timber_rows']}
    observations = {r['id']: r for r in first['source_inputs']['finished_body_observations']}
    profiles, geometry = {}, []
    for shaft in first['source_inputs']['shafts']:
        for surface in shaft['surfaces']:
            if surface['kind'] != 'wood':
                continue
            host = surface['host']
            if host not in profiles:
                profile = outer_profile(members[host]['raw_profile_source'])
                observation = observations[host]
                shape = reference.cq.Shape.importBrep(str(current.ROOT/observation['source']['path']))
                solid, wrapper = container.strict_solid(shape, reference)
                current.require(wrapper == observation['strict_container']
                                and abs(solid.Volume()-observation['volume_mm3']) < .01,
                                'own unchanged finished solid/container required')
                profiles[host] = {**profile, 'solid_source': observation['source'],
                                  'finished_face_diagnostics': confirm_faces(solid, profile)}
            geometry.append(placement(profiles[host], shaft, surface, end_method))
    current.require(len(profiles) == 22 and len(geometry) == 120
                    and len({(r['axis_id'], r['host']) for r in geometry}) == 120,
                    'all 120 own wood-bore occurrences on the current 22 timbers required')
    bindings = []
    for binding, field, _ in cases:
        current.require(all(field['source_inputs'][key] == first['source_inputs'][key]
                            for key in ('shafts', 'timber_rows', 'finished_body_observations'))
                        and len(field['panel_screw_actions']) == 66, 'same current geometry and 66-screw policy across cases required')
        bindings.append({key: binding[key] for key in ('case_id', 'state_id', 'field')})
    current.verify(pins)
    current.require(current.sha(OWN) == LOADED_SHA, 'loaded geometry consumer changed')
    return {'schema': 'eoere_current_bolt_outer_geometry/v1',
            'status': 'COMPLETE_CURRENT_OUTER_PROFILE_COMPONENT_SCREENS_LOCAL_RESISTANCE_PENDING',
            'producer': current.ref(OWN), 'inputs': input_ref, 'source_sha256': pins, 'all_sources_unchanged': True,
            'runtime_versions': runtime, 'known_answer_container': known, 'case_bindings': bindings,
            'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'member_profiles': profiles, 'wood_bore_occurrences': geometry,
            'full_7D_outer_end_marker_misses': sum(not r['full_7D_end_marker_pass'] for r in geometry),
            'full_4D_outer_edge_marker_misses': sum(not r['full_4D_outer_edge_marker_pass'] for r in geometry),
            'square_end_component_applicability_count': sum(r['square_end_component_applicable'] for r in geometry),
            'complete_Cdelta': None, 'complete_joint_resistance': None, 'finished_member_capacity': None,
            'physical_demand_bounds_established': False, 'actual_observations': None, 'structural_acceptance': False,
            'native_or_frame_solve_CAD_rebuild_geometry_change_or_actual_fit': False,
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
