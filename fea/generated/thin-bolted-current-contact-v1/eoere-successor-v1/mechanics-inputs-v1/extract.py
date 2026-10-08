"""Deferred source-bound successor geometry metadata, without assembly or solve.

Only the parent extraction mode imports candidate BREPs. Plan and pure helpers
read saved metadata. Unchanged generic methods are compiled directly from their
pinned source functions; no old candidate query selector or response is called.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.metadata
import io
import json
import math
import os
import platform
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PACKET = 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison'
LEAF = 'fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1'
REPORT = LEAF + '/occupied-geometry-v2-complete/geometry.json'
REPORT_SHA = '05baab7ffdd329c3240a1770cf3539e321ab47d5cd2bc6354f8fceb6db8a0efd'
MIRROR = PACKET + '/eoere-successor-v1/occupied-geometry-v2.json'
SCENE = LEAF + '/occupied-geometry-v2-complete/scene.json'
SCENE_SHA = '8599fca392ccf2ec366ab4c39e4c1d74be89da50167edc7c760e5cb73c524c4a'
DATA = {
    'joined': ('fea/generated/thin-bolted-build-planning-v4/joined-shop-data-final.json', '7982d8612014d6d55279f7847798ea3bf87e6c2eca2fa585ef4457daf3787074'),
    'native': (PACKET + '/native-geometry-v4.json', 'cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9'),
    'layout': (PACKET + '/mixed-offset-rows-shallow-wires-v4.json', '8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c'),
    'integrated': (PACKET + '/integrated-model-v4.json', '28bbd2d2fb6f1a93acb441af124c453f04f81e03be551906c633d5acad1d407e'),
    'access': (PACKET + '/access-takeoff-v4.json', '0c5a09879c9b191c39b96ce670d71ad110661bff7dfeab68133f711b32de476c'),
}
METHODS = {
    'fea/generated/thin-bolted-build-planning-v4/prepare.py': '51e7b0bc082ce3fbfaba1826660b4497918ced45a983498bfc998dbc8396a62a',
    'scripts/thin_bolted_timber_resistance.py': '74d992cfbe4947587a8c6f0e65f7a8b47e0cd1c79f07721620c7137208919c2d',
    'scripts/thin_bolted_timber_face_geometry.py': '4397c90479ba0ce2d54b82e2427f63bace50e0d217910d2dea43d1872c6cb183',
    'scripts/wood_joint_current_face_pair_atlas_attempt01.py': '016dbce14bff6408de418fc6cce35fa0590a72ceef43565164aa10f4b4bea3bb',
    'fea/wood_joint_reduced_contacts.py': '4e088d485cee8953bfdca411f646f18abfb49271c9d8f3b46044588a6a7c1ce7',
    'scripts/thin_bolted_frame_mechanics.py': '05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448',
    'fea/current_response_model.py': 'faae5b14c47c3c485f41d56eb77ec9e9a6c1801e5a143276a91afc3a294a9894',
    LEAF + '/reuse-plan-v1/inventory.py': '851c2a68b81bab39bd11f24622b77639e66f13820c1fb36dc6beaa72cf36c8a5',
    'fea/generated/thin-bolted-current-contact-v1/candidate-reference-solids-v2/bridge.py': 'a215a91e1ef3f1f48c36e41065bea5078be5f3d3e1bfcb9fc5e6bd263bf91098',
    'fea/generated/thin-bolted-current-contact-v1/reference-solid-distance-v1/distance.py': 'b0b94063be8fc595bb01ffcb08f876061e3aa9efca6cb4466e5c74fb183fdc8d',
}
VERSIONS = {'python': '3.12.3', 'cadquery': '2.8.0', 'cadquery-ocp': '7.9.3.1.1', 'numpy': '2.5.2', 'scipy': '1.18.1'}
PARAMETERS = {'wood_density_kg_m3': 500., 'metal_density_kg_m3': 7850., 'gravity_m_s2': 9.80665,
              'wood_bedding_n_mm3': 1., 'panel_foundation_n_mm3': 2., 'screw_stiffness_n_mm': 1000.,
              'contact_cell_size_mm': 50., 'flange_nominal_total_stiffness_n_mm': 40000.}
SCENARIO = {'timber_stiffness_basis': 'declared-gross-stock-Timoshenko',
            'fitting_gravity_route': 'source-point-wrench-through-internal-rigid-heel-v1',
            'beam_size_mm': 150., 'timber_e_mpa': 11031.612, 'timber_shear_ratio': .064,
            'metal_density_kg_mm3': 7850e-9, 'floor_kn_n_mm': 25000., 'floor_kt_n_mm': 100000.,
            'floor_activation_threshold_n': 1e-7,
            'common_shaft_parameters': {'steel_E_mpa': 200000., 'steel_nu': .3, 'max_segment_mm': 25.,
                'wood_foundation_n_mm2': 26.2467191601, 'plate_foundation_n_mm2': 1799.77502812, 'end_capture_n_mm': 1000.}}


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def merge(pins, additions):
    for path, value in additions.items():
        require(path not in pins or pins[path] == value, 'contradictory source pin: ' + path)
        pins[path] = value


def verify(pins):
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, 'source changed: ' + path)


def exact_functions(relative, names, namespace):
    require(sha(ROOT / relative) == METHODS[relative], 'method source differs before compilation')
    tree = ast.parse((ROOT / relative).read_text(), filename=str(ROOT / relative))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require({n.name for n in nodes} == set(names), 'pinned generic function missing')
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future, *nodes], type_ignores=[])), str(ROOT / relative), 'exec'), namespace)  # noqa: S102
    return SimpleNamespace(**{n.name: namespace[n.name] for n in nodes})


def pure_methods():
    relative = 'fea/generated/thin-bolted-build-planning-v4/prepare.py'
    return exact_functions(relative, ('dot', 'sub', 'add', 'scale', 'cross', 'unit', 'vector', 'proper'), {'math': math, 'require': require})


def read_sources(expected):
    require(expected == REPORT_SHA and sha(ROOT / REPORT) == expected and sha(ROOT / MIRROR) == expected, 'exact final geometry and mirror required')
    report = json.loads((ROOT / REPORT).read_bytes())
    pins = dict(report['source_sha256'])
    merge(pins, METHODS)
    merge(pins, {p: s for p, s in DATA.values()})
    merge(pins, {REPORT: expected, MIRROR: expected, SCENE: SCENE_SHA,
                 str(OWN.relative_to(ROOT)): LOADED_SHA, str(OWN.with_name('test_extract.py').relative_to(ROOT)): sha(OWN.with_name('test_extract.py'))})
    verify(pins)
    data = {name: json.loads((ROOT / path).read_bytes()) for name, (path, _) in DATA.items()}
    for obj in data.values():
        merge(pins, obj.get('source_sha256', {}))
    panels = [r for r in data['native']['parts'] if r['kind'] == 'panel']
    for row in [*report['finished_solids'], *panels]:
        merge(pins, {row['path']: row['sha256']})
    verify(pins)
    require(report['counts']['physical_bolt_axes'] == 100 and report['counts']['timber'] == report['counts']['bracket'] == 22, 'final owner census differs')
    require(all(not rows for rows in report['collisions'].values()) and all(r['pre_bore_full_body_fraction'] == 1. for r in report['bore_support']), 'final geometry blocker remains')
    require(report['changes']['Hillman_axes_moved'] == [] and len(data['layout']['screw_axes']) == 66 and len(panels) == 6, 'protected panel/screw scope differs')
    require(all(a['point_xyz_mm'][2] == 200. for a in report['axes'] if a['source'] == 'cleat_post_through_bolt'), 'lower revision not Z200')
    return report, data, pins, panels


def gross_row(profile, m):
    """Gross raw-stock beam datum from the saved eight-vertex source profile.

    Mirrors gross_member_record's transverse box and level bevel centerline
    start convention. The partial bevel remains a declared beam extension;
    neither changed cuts nor holes reduce this response section.
    """
    g, u, _ = profile['basis_grain_u_v_xyz']
    g, u = m.unit(g), m.unit(u)
    v = m.unit(m.cross(g, u))
    points = [m.add(profile['datum_xyz_mm'], [sum(b[j] * x for b, x in zip((g, u, v), p, strict=True)) for j in range(3)])
              for p in profile['raw_profile_vertices_luv_mm']]
    bounds = [[min(m.dot(p, a) for p in points), max(m.dot(p, a) for p in points)] for a in (g, u, v)]
    center = m.add(m.scale(u, sum(bounds[1]) / 2), m.scale(v, sum(bounds[2]) / 2))
    low, high = bounds[0]
    if 1e-8 < abs(g[2]) < 1. - 1e-8:
        low = (min(p[2] for p in points) - center[2]) / g[2]
    return {'name': profile['member'], 'start': m.add(center, m.scale(g, low)), 'end': m.add(center, m.scale(g, high)),
            'axis': g, 'section_u': u, 'section_v': v, 'width_mm': bounds[1][1] - bounds[1][0], 'depth_mm': bounds[2][1] - bounds[2][0],
            'stiffness_scenario': 'gross_raw_stock_Timoshenko', 'finished_cut_stiffness_or_resistance_qualified': False,
            'raw_profile_source': profile, 'source_centerline_grain_interval_mm': [low, high]}


def cleat_profile(side):
    x = -1257.3 if side == 'left' else 1216.025
    return {'member': 'eoere_cleat_' + side, 'datum_xyz_mm': [x, -175.7, 139.7],
            'basis_grain_u_v_xyz': [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
            'raw_profile_vertices_luv_mm': [[z, a, b] for z in (0., 289.7) for a in (0., 38.1) for b in (0., 139.7)],
            'raw_stock_scenario_dimensions_mm': [38.1, 139.7, 289.7], 'grain_inspected': False}


def recover_poses(scene, m):
    rows = []
    for obj in scene['solids']:
        if obj['fabrication']['kind'] != 'bracket':
            continue
        t = obj['transform']
        source = [[t[i], t[i + 1], t[i + 2]] for i in (0, 4, 8)]
        u = m.unit(source[0])
        v = m.unit(m.sub(source[1], m.scale(u, m.dot(source[1], u))))
        w = m.cross(u, v)
        require(math.dist(w, source[2]) < 1e-8, 'saved source fitting proper basis differs')
        rows.append({'id': obj['id'], 'duty_id': obj['fabrication']['duty_id'], 'origin_xyz_mm': t[12:15],
                     'u_xyz': u, 'v_xyz': v, 'w_xyz': w, 'saved_scene_basis_columns_xyz': source,
                     'pose_recovery': 'same normalize-u/orthogonalize-v/cross-w rule as pinned eoere_bolted_candidate.pose'})
    require(len(rows) == len({r['id'] for r in rows}) == 22, '22 fitting poses required')
    return rows


def port_id(flange, transverse):
    require(flange in ('beam', 'post') and transverse in (-1, 1), 'exact owned flange/sign required')
    return ('arm-x' if flange == 'beam' else 'arm-z') + ('/far-plus' if transverse == -1 else '/far-minus')


def role_rows(axis, m, volumes):
    p, g, h = axis['point_xyz_mm'], m.unit(axis['direction_xyz']), axis['hardware_scenario']
    start = -axis['before_plate_mm'] - h['washer_thickness_mm']
    nut = axis['grip_mm'] + axis['after_plate_mm'] + h['washer_thickness_mm']
    mid = {'shaft': start + axis['nominal_under_head_length_mm'] / 2,
           'head': start - h['head_height_mm'] / 2, 'head_washer': start + h['washer_thickness_mm'] / 2,
           'nut_washer': axis['grip_mm'] + axis['after_plate_mm'] + h['washer_thickness_mm'] / 2,
           'nut': nut + h['nut_height_mm'] / 2}
    return [{'id': axis['id'] + '/' + role, 'kind': role, 'volume_mm3': volume,
             'center_of_mass_xyz_mm': m.add(p, m.scale(g, mid[role])), 'mass_kg': volume * 7850e-9,
             'basis': 'exact scalar volume and axial centroid of pinned nominal local_hardware recipe'} for role, volume in volumes.items()]


def end_seats(axis, surfaces, m):
    g, h, grip = m.unit(axis['direction_xyz']), axis['hardware_scenario'], axis['grip_mm']
    ends = []
    for end, support, sign in (('head', -axis['before_plate_mm'], -1.), ('nut', grip + axis['after_plate_mm'], 1.)):
        index = 0 if end == 'head' else 1
        match = [s for s in surfaces if s['kind'] == 'steel' and abs(s['interval_mm'][index] - support) < 1e-5]
        if not match:
            target = 0. if end == 'head' else grip
            match = [s for s in surfaces if s['kind'] == 'wood' and abs(s['interval_mm'][index] - target) < 1e-5]
        require(len(match) == 1, 'capture needs one actual external host: ' + axis['id'] + '/' + end)
        ends.append({'end': end, 'host': match[0]['host'], 'flange': match[0].get('flange'),
            'support_s_mm': support, 'pressure_face_s_mm': support + sign * h['washer_thickness_mm'],
            'own_washer_thickness_mm': h['washer_thickness_mm'], 'direction_on_shaft_xyz': m.scale(g, sign),
            'washer_id': axis['id'] + '/' + end + '_washer', 'delivered_bearing_seat_or_pressure_qualified': False})
    return ends


def load_query_methods(pins):
    """No source body is imported while loading the pinned generic functions."""
    verify(pins)
    from typing import Any

    import cadquery as cq
    import numpy as np
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    actual = {'python': platform.python_version(), **{k: importlib.metadata.version(k) for k in VERSIONS if k != 'python'}}
    require(actual == VERSIONS, 'pinned extraction versions differ')
    atlas_names = ('sha256_bytes', '_canonical_json', '_canonical_sha256', '_finite', '_round9', '_vector3', '_bounds',
                   '_edge_geometry_signature', '_face_signature_data', '_region_geometry_data', 'source_face_records', '_face_boxes_overlap')
    atlas = exact_functions('scripts/wood_joint_current_face_pair_atlas_attempt01.py', atlas_names, {'Any': Any, 'math': math, 'json': json, 'hashlib': hashlib})
    partition = exact_functions('fea/wood_joint_reduced_contacts.py', ('area_cells',), {'cq': cq, 'np': np, 'math': math})
    geo = exact_functions('scripts/thin_bolted_timber_face_geometry.py', ('centroidal_second_moments', 'occupied_cells', 'find_patches'),
        {'cq': cq, 'np': np, 'require': require, 'atlas': atlas, 'partition': partition, 'BRepGProp': BRepGProp, 'GProp_GProps': GProp_GProps,
         'PLANE_TOL_MM': 1e-5, 'OCCUPANCY_TOL_MM': 1e-7})
    bore = exact_functions('scripts/thin_bolted_timber_resistance.py', ('finished_bore_wall_intervals',), {'require': require, 'math': math})
    frame = exact_functions('scripts/thin_bolted_frame_mechanics.py', ('connector_basis', 'wrench', 'load_cases'),
        {'np': np, 'copy': copy, 'GRAVITY': 9.80665, 'CASE_INPUTS': (('a12-rear', 'A12', (0., 300.)),)})
    inventory = exact_functions(LEAF + '/reuse-plan-v1/inventory.py', ('hardware_volumes',), {'math': math, 'require': require})
    floor = exact_functions('fea/current_response_model.py', ('level_face_points',), {'np': np})
    bridge = exact_functions('fea/generated/thin-bolted-current-contact-v1/candidate-reference-solids-v2/bridge.py', ('strict_solid',), {'require': require})
    distance = exact_functions('fea/generated/thin-bolted-current-contact-v1/reference-solid-distance-v1/distance.py', ('brep_sha',),
        {'require': require, 'io': io, 'hashlib': hashlib})
    return SimpleNamespace(cq=cq, np=np, atlas=atlas, geometry=geo, bore=bore, frame=frame, inventory=inventory, floor=floor, bridge=bridge, distance=distance, versions=actual)


def import_cached(report, panels, pins, q):
    verify(pins)
    bodies, observed = {}, []
    for row in [*report['finished_solids'], *panels]:
        require(sha(ROOT / row['path']) == row['sha256'], 'cached body changed before import')
    reference = SimpleNamespace(cq=q.cq, brep_sha=q.distance.brep_sha)
    for row in [*report['finished_solids'], *panels]:
        original = q.cq.Shape.importBrep(str(ROOT / row['path']))
        body, container = q.bridge.strict_solid(original, reference)
        bb = body.BoundingBox()
        bounds = [[getattr(bb, a + 'min'), getattr(bb, a + 'max')] for a in 'xyz']
        require(abs(body.Volume() - row['volume_mm3']) < max(.01, row['volume_mm3'] * 1e-9), 'cached volume join differs')
        require(max(abs(a - b) for aa, bb in zip(bounds, row['bounds_xyz_mm'], strict=True) for a, b in zip(aa, bb, strict=True)) < 1e-5, 'cached bounds join differs')
        bodies[row['id']] = body
        observed.append({'id': row['id'], 'source': row, 'volume_mm3': body.Volume(), 'center_xyz_mm': list(body.Center().toTuple()),
                         'bounds_xyz_mm': bounds, 'strict_container': container})
    require(len(bodies) == 28, '22 finished timber plus six unchanged panels required')
    return bodies, observed


def shafts(report, profiles, bodies, q, m):
    result, wall_rows = [], []
    for axis in report['axes']:
        p, g = q.cq.Vector(*axis['point_xyz_mm']), q.cq.Vector(*m.unit(axis['direction_xyz']))
        surfaces = []
        for receiver in axis['receivers']:
            wall = q.bore.finished_bore_wall_intervals(bodies[receiver], p, g, axis['bore_diameter_mm'] / 2)
            intervals = [[max(0., lo), min(axis['grip_mm'], hi)] for lo, hi in wall['full_wall_intervals_mm']]
            require(intervals and all(hi - lo > 1e-6 for lo, hi in intervals), 'full finished bearing wall missing')
            grain = profiles[receiver]['axis']
            wall_rows.append({'axis_id': axis['id'], 'receiver': receiver, 'grain_axis_xyz': grain, **wall,
                              'finished_full_wall_intervals_from_axis_point_mm': intervals})
            surfaces.extend({'host': receiver, 'kind': 'wood', 'interval_mm': interval, 'grain_axis_xyz': grain,
                'bore_diameter_mm': axis['bore_diameter_mm'], 'source_axis_id': axis['id']} for interval in intervals)
        for attachment in axis['attachments']:
            point = attachment['point']
            station = m.dot(m.sub(point, axis['point_xyz_mm']), m.unit(axis['direction_xyz']))
            require(abs(station) < 1e-5 or abs(station - axis['grip_mm']) < 1e-5, 'factory port is not on external stack face')
            interval = [-axis['before_plate_mm'], 0.] if abs(station) < 1e-5 else [axis['grip_mm'], axis['grip_mm'] + axis['after_plate_mm']]
            require(interval[1] - interval[0] > 0, 'occupied fitting plate missing')
            surfaces.append({'host': attachment['angle_id'], 'kind': 'steel', 'interval_mm': interval,
                'flange': port_id(attachment['flange'], attachment['transverse']), 'source_flange': attachment['flange'],
                'source_transverse': attachment['transverse'], 'entry_xyz_mm': point, 'receiver': attachment['receiver'],
                'bore_diameter_mm': report['scenario']['factory_hole_mm'], 'source_axis_id': axis['id']})
        ends = end_seats(axis, surfaces, m)
        metal = role_rows(axis, m, q.inventory.hardware_volumes(axis))
        start = ends[0]['pressure_face_s_mm']
        result.append({'axis_id': axis['id'], 'body': 'shaft/' + axis['id'], 'point': axis['point_xyz_mm'],
            'basis': q.frame.connector_basis(axis['direction_xyz']).tolist(), 'diameter_mm': axis['diameter_mm'], 'bore_diameter_mm': axis['bore_diameter_mm'],
            'shaft_interval_mm': [start, start + axis['nominal_under_head_length_mm']], 'surfaces': surfaces, 'ends': ends, 'metal_roles': metal,
            'source_axis': axis, 'nominal_geometry_not_delivered_thread_root_or_shank': True})
    require(len(result) == 100 and len(wall_rows) == 120 and sum(s['kind'] == 'steel' for a in result for s in a['surfaces']) == 88, '100/120/88 shaft ownership differs')
    return result, wall_rows


def aabb_overlap(first, second, tol=1e-5):
    a, b = first.BoundingBox(), second.BoundingBox()
    return all(getattr(a, d + 'min') <= getattr(b, d + 'max') + tol and getattr(b, d + 'min') <= getattr(a, d + 'max') + tol for d in 'xyz')


def contact_bank(bodies, timber_ids, panel_ids, q, parameters):
    faces = {name: q.atlas.source_face_records(name, shape) for name, shape in bodies.items()}
    patches, checked = [], []
    pairs = [(a, b, 'timber_face_contact') for i, a in enumerate(timber_ids) for b in timber_ids[i + 1:]]
    pairs += [(a, b, 'panel_contact') for a in panel_ids for b in timber_ids]
    for first, second, kind in pairs:
        if not aabb_overlap(bodies[first], bodies[second]):
            continue
        own = q.geometry.find_patches(first, second, faces, bodies, cell_size_mm=parameters['contact_cell_size_mm'])
        checked.append({'first': first, 'second': second, 'kind': kind, 'patch_count': len(own)})
        for patch in own:
            patch['kind'] = kind
            patches.append(patch)
    contacts = []
    for patch in patches:
        density = parameters['panel_foundation_n_mm3'] if patch['kind'] == 'panel_contact' else parameters['wood_bedding_n_mm3']
        for cell in patch['cells']:
            contacts.append({'id': cell['id'], 'kind': patch['kind'], 'first': patch['first'], 'second': patch['second'],
                'point_xyz_mm': cell['point_xyz_mm'], 'direction_xyz': patch['normal_from_second_to_first_xyz'],
                'stiffness': density * cell['area_mm2'], 'reference_area_mm2': cell['area_mm2'], 'bedding_n_mm3': density,
                'source_patch_id': patch['id'], 'source_trimmed_region_signature_sha256': patch['trimmed_region_signature_sha256'],
                'source_first_face_signature_sha256': patch['source_first_face']['signature_sha256'],
                'source_second_face_signature_sha256': patch['source_second_face']['signature_sha256'],
                'pressure_convergence_or_physical_contact_qualified': False})
    return patches, contacts, checked, faces


def fitting_face(pose, flange, sign, scenario, q, m):
    """One nominal holed flat flange half, with a truthful small prism mask."""
    along, normal = (pose['u_xyz'], pose['v_xyz']) if flange == 'beam' else (pose['v_xyz'], pose['u_xyz'])
    w, origin = pose['w_xyz'], pose['origin_xyz_mm']
    lo, hi = (-scenario['width_mm'] / 2, 0.) if sign == -1 else (0., scenario['width_mm'] / 2)
    def point(a, b):
        return q.cq.Vector(*m.add(origin, m.add(m.scale(along, a), m.scale(w, b))))
    outer = q.cq.Wire.makePolygon([point(a, b) for a, b in ((scenario['thickness_mm'], lo), (scenario['leg_mm'], lo),
                                                           (scenario['leg_mm'], hi), (scenario['thickness_mm'], hi))], close=True)
    holes = [q.cq.Wire.makeCircle(scenario['factory_hole_mm'] / 2, point(station, sign * scenario['transverse_pitch_mm'] / 2), q.cq.Vector(*normal))
             for station in (scenario['far_offset_mm'] - scenario['axial_pitch_mm'], scenario['far_offset_mm'])]
    face = q.cq.Face.makeFromWires(outer, holes)
    prism = q.cq.Solid.extrudeLinear(face.outerWire(), face.innerWires(), q.cq.Vector(*m.scale(normal, scenario['thickness_mm'])))
    return prism, face.Area(), normal


def flange_bank(poses, report, bodies, faces, q, m, parameters):
    bindings = {(a['angle_id'], a['flange'], a['transverse']): a for axis in report['axes'] for a in axis['attachments']}
    contacts, patches, domains = [], [], []
    for pose in poses:
        for flange in ('beam', 'post'):
            for sign in (-1, 1):
                binding = bindings[(pose['id'], flange, sign)]
                mask, half_area, normal = fitting_face(pose, flange, sign, report['scenario'], q, m)
                # The query owner is the physical fitting. The source surface is
                # one exact strip; the tiny prism is a reference mask only.
                own_faces = q.atlas.source_face_records(pose['id'], mask)
                outward = [r for r in own_faces if m.dot(r['signature']['oriented_normal_xyz'], normal) < -1. + 1e-8]
                require(len(outward) == 1, 'one nominal flat strip contact face required')
                receiver = binding['receiver']
                local_faces = {pose['id']: outward, receiver: faces[receiver]}
                local_bodies = {pose['id']: mask, receiver: bodies[receiver]}
                own = q.geometry.find_patches(pose['id'], receiver, local_faces, local_bodies, cell_size_mm=parameters['contact_cell_size_mm'])
                identity = f'{pose["id"]}/{flange}/{sign}'
                total = parameters['flange_nominal_total_stiffness_n_mm']
                density = None if total is None else total / (2 * half_area)
                domains.append({'id': identity, 'fitting': pose['id'], 'receiver': receiver,
                    'model_port_id': port_id(flange, sign), 'source_flange': flange, 'source_transverse': sign,
                    'nominal_full_holed_flange_area_mm2': 2 * half_area, 'nominal_half_area_mm2': half_area,
                    'clipped_area_mm2': sum(p['area_mm2'] for p in own), 'declared_nominal_flange_total_stiffness_n_mm': total,
                    'declared_flange_area_density_n_mm3': density, 'point_stiffness_ready': total is not None,
                    'stiffness_formula': '40000 N/mm * clipped cell area / complete nominal holed flat flange area',
                    'stiffness_basis': 'owner-adopted new first-order area-weighted prior; rigid-translation total only, no old rocking stiffness, forces or physical calibration',
                    'unmeasured_sharp_flat_flange_scenario': True})
                for patch in own:
                    patch['id'] = identity + '/' + patch['id']
                    patch['source_owned_port_id'] = port_id(flange, sign)
                    patches.append(patch)
                    for index, cell in enumerate(patch['cells']):
                        contacts.append({'id': patch['id'] + f'/cell-{index}', 'kind': 'flange_contact', 'first': pose['id'], 'second': receiver,
                            'first_port_id': port_id(flange, sign), 'point_xyz_mm': cell['point_xyz_mm'], 'direction_xyz': normal,
                            'stiffness': None if density is None else density * cell['area_mm2'], 'reference_area_mm2': cell['area_mm2'],
                            'nominal_full_holed_flange_area_mm2': 2 * half_area, 'source_domain_id': identity,
                            'source_trimmed_region_signature_sha256': patch['trimmed_region_signature_sha256'],
                            'rigid_translation_total_prior_only_no_old_rocking_or_forces': True})
    return domains, patches, contacts


def fitting_centroid(scenario, pose, m):
    leg, width, t, radius = (scenario[k] for k in ('leg_mm', 'width_mm', 'thickness_mm', 'factory_hole_mm'))
    radius /= 2
    arm, overlap, hole = leg * t * width, t * t * width, math.pi * radius * radius * t
    near, far = scenario['far_offset_mm'] - scenario['axial_pitch_mm'], scenario['far_offset_mm']
    volume = 2 * arm - overlap - 8 * hole
    first_x = arm * (leg + t) / 2 - overlap * t / 2 - hole * (2 * near + 2 * far + 4 * t / 2)
    center = first_x / volume
    return m.add(pose['origin_xyz_mm'], m.scale(m.add(pose['u_xyz'], pose['v_xyz']), center))


def extract(report, data, pins, panels, parameters):
    require(os.environ.get('EOERE_PARENT_SERIALIZED_EXTRACTION') == '1', 'parent serialized extraction marker required')
    q, m = load_query_methods(pins), pure_methods()
    scene = json.loads((ROOT / SCENE).read_bytes())
    poses = recover_poses(scene, m)
    timber = [gross_row(p, m) for p in data['joined']['members']]
    timber += [gross_row(cleat_profile(side), m) for side in ('left', 'right')]
    profiles = {p['name']: p for p in timber}
    require(len(profiles) == 22 and set(profiles) == {r['id'] for r in report['finished_solids']}, 'own raw profile join differs')
    bodies, observations = import_cached(report, panels, pins, q)
    shaft_rows, walls = shafts(report, profiles, bodies, q, m)
    timber_ids, panel_ids = sorted(profiles), sorted(r['id'] for r in panels)
    patches, direct, pair_queries, faces = contact_bank(bodies, timber_ids, panel_ids, q, parameters)
    domains, flange_patches, flange_contacts = flange_bank(poses, report, bodies, faces, q, m, parameters)
    direct += flange_contacts
    base = [{'id': r['id'], 'kind': 'timber' if r['id'] in profiles else 'panel', 'mass_kg': r['volume_mm3'] * parameters['wood_density_kg_m3'] * 1e-9,
             'center_xyz_mm': r['center_xyz_mm'], 'gravity_basis': 'source-pinned finished volume and queried COM; conditional uniform500 kg/m3'} for r in observations]
    base += [{'id': p['id'], 'kind': 'fitting', 'mass_kg': 1.46 * .45359237,
              'center_xyz_mm': fitting_centroid(report['scenario'], p, m),
              'gravity_basis': 'source drawing1.46lb; exact nominal sharp holed-angle centroid, declared internal collector routing'} for p in poses]
    metal = [{'id': r['id'], 'owner': s['body'], 'mass_kg': r['mass_kg'], 'center_xyz_mm': r['center_of_mass_xyz_mm'],
              'basis': r['basis']} for s in shaft_rows for r in s['metal_roles']]
    other = [r for r in data['access']['takeoff']['conditional_metal_gravity_rows'] if r['role'] in ('screw', 'tnut')]
    extra = [{'id': r['id'] + f'/unchanged-gravity-share-{i}', 'owner': r['owner'], 'mass_kg': r['mass_kg'], 'center_xyz_mm': r['centroid_xyz_mm'],
              'basis': 'unchanged source metal in unchanged raw envelopes: ' + r['ownership_method']} for i, r in enumerate(other)]
    cases, gravity = q.frame.load_cases(data['integrated'], {'bodies': base, 'bolt_gravity_components': metal + extra})
    case = next(r for r in cases if r['case_id'] == 'a12-rear' and r['primary_load_basis'])
    for load in case['loads']:
        if load['id'].startswith('bolt-weight/') and load['body'].startswith('shaft/'):
            load['id'] = 'physical-bolt-metal/' + load['id'].removeprefix('bolt-weight/')
    require(sum(r['id'].startswith('physical-bolt-metal/') for r in case['loads']) == 500, '500 own metal loads required')
    owner_rows = list(base)
    for s in shaft_rows:
        mass = sum(r['mass_kg'] for r in s['metal_roles'])
        center = [sum(r['mass_kg'] * r['center_of_mass_xyz_mm'][i] for r in s['metal_roles']) / mass for i in range(3)]
        owner_rows.append({'id': s['body'], 'kind': 'shaft', 'mass_kg': mass, 'center_xyz_mm': center,
                           'gravity_route': 'five separate physical-bolt-metal loads; no duplicate owner selfweight'})
    require(len(owner_rows) == len({r['id'] for r in owner_rows}) == 150, '150 distinct physical owners required')
    require(all(r['body'] in {b['id'] for b in owner_rows} for r in case['loads']), 'load owner missing')
    footprints = {name: [p.tolist() for p in q.floor.level_face_points(bodies[name], True)] for name in timber_ids
                  if name.startswith(('base_post_', 'base_floor_', 'lumber_leg_'))}
    require(len(footprints) == 8, 'eight actual floor hosts required')
    hillman = [{'id': s['axis_id'], 'first': s['panel'], 'second': s['receiver'],
                'point_xyz_mm': m.add(s['origin_xyz_mm'], m.scale(m.unit(s['direction_xyz']), 18.25625 / 2)),
                'basis': q.frame.connector_basis(m.scale(m.unit(s['direction_xyz']), -1)).tolist(),
                'ka': parameters['screw_stiffness_n_mm'], 'kl': parameters['screw_stiffness_n_mm'], 'clearance': 0., 'tension_only': True,
                'source_screw_descriptor': s, 'physical_Hillman_stiffness_or_capacity_qualified': False} for s in data['layout']['screw_axes']]
    bindings = [{**a, 'model_port_id': port_id(a['flange'], a['transverse']), 'physical_axis_id': axis['id']}
                for axis in report['axes'] for a in axis['attachments']]
    flat_holes = [{**hole, 'angle_id': angle['angle_id'], 'used': hole['installed_bolt_axis_id'] is not None}
                  for angle in scene['factory_angle_holes'] for hole in angle['holes']]
    factory_bindings = [{'angle_id': b['angle_id'], 'model_port_id': b['model_port_id'], 'axis_id': b['physical_axis_id'],
                         'entry_xyz_mm': b['point'], 'source_flange': b['flange'], 'source_transverse': b['transverse']}
                        for b in bindings]
    verify(pins)
    require(sha(OWN) == LOADED_SHA, 'loaded extraction source changed')
    return {'schema': 'eoere_first_order_mechanics_inputs/v1', 'status': 'GEOMETRY_METADATA_AND_DECLARED_SCENARIO_ONLY',
        'source_sha256': pins, 'source_pins_before_after_unchanged': True,
        'geometry': {'report': {'path': REPORT, 'sha256': REPORT_SHA}, 'mirror': {'path': MIRROR, 'sha256': REPORT_SHA},
                     'scene': {'path': SCENE, 'sha256': SCENE_SHA}}, 'parameters': parameters, 'scenario': SCENARIO,
        'timber_rows': timber, 'base_bodies': base, 'physical_owner_gravity_rows': owner_rows,
        'fitting_poses': poses, 'all_factory_holes': scene['factory_angle_holes'], 'hole_to_axis_port_bindings': bindings,
        'factory_holes': flat_holes, 'fitting_port_bindings': factory_bindings,
        'shafts': shaft_rows, 'finished_receiver_wall_queries': walls, 'finished_body_observations': observations,
        'direct_contacts': direct, 'timber_and_panel_shared_face_patches': patches, 'shared_pair_query_census': pair_queries,
        'flange_domains': domains, 'flange_shared_face_patches': flange_patches,
        'hillman_rows': hillman, 'panel_ids': panel_ids, 'floor_footprints': footprints, 'case': case, 'gravity': gravity,
        'factory_contact_stiffness_complete': all(r['stiffness'] is not None for r in direct),
        'readiness': {'source_joins_independently_reviewed': False, 'complete_reference_contact_inventory': False,
                      'independent_actual_extraction_review': None},
        'counts': {'finished_timbers': 22, 'unchanged_panels': 6, 'physical_owners': 150, 'base_bodies_excluding_shafts': 50,
                   'fittings': 22, 'shafts': 100, 'metal_role_loads': 500, 'Hillman': 66, 'shaft_receiver_rows': len(walls),
                   'factory_ports': len(bindings), 'flange_domains': len(domains), 'contact_points': len(direct)},
        'method': {'versions': q.versions, 'candidate_cached_BREP_imports': 28, 'candidate_assembly_profile_q_K_solve': False,
                   'gross_stock_stiffness_is_separate_from_finished_volume_walls_and_contact_masks': True,
                   'old_changed_hole_stiffness_profiles_or_old_contact_domains_copied': False,
                   'flange_masks_are_small_nominal_flat_reference_prisms_not_new_frame_bodies': True},
        'limits': ['No actual wood grade, density, screws, root/shank/thread, steel modulus/yield, contact stiffness or floor was measured.',
                   'Gross raw-stock beams and gross four-strip fitting stiffness leave bore/cut effects and response accuracy unqualified.',
                   'Clipped finite-face area centroids conserve area and first moments, not pressure peaks or rocking stiffness.',
                   'Exact reference domains with holes do not establish overlap after deformation, physical pressure or complete resistance.',
                   'Factory must reject any null contact stiffness; source masks cannot silently acquire a law.',
                   'This is new successor metadata; no predecessor force, q, case pass, admission, capacity or release transfers.'],
        'release': dict.fromkeys(('candidate_admitted', 'complete_joint_resistance', 'physical_contact', 'fabrication', 'structural', 'climbing'), False)}


def plan(report, pins):
    return {'schema': 'eoere_successor_mechanics_inputs_extraction_plan/v1', 'source_sha256': pins,
        'source_pins_before_after_unchanged': True, 'geometry_report_sha256': REPORT_SHA, 'scene_sha256': SCENE_SHA,
        'planned_cached_imports': {'finished_timbers': 22, 'unchanged_panels': 6}, 'expected_physical_owners': 150,
        'planned_shaft_ids': [a['id'] for a in report['axes']], 'planned_receiver_queries': report['bore_support'],
        'parameters': PARAMETERS, 'generic_methods_only_old_query_selectors_not_called': True,
        'source_face_masks': 'All opposed coplanar finished timber/timber and unchanged panel/timber intersections; nominal holed flange halves clipped to their actual receiver.',
        'flange_law_decision_required': PARAMETERS['flange_nominal_total_stiffness_n_mm'] is None,
        'candidate_CAD_import_query_profile_q_K_force_or_solve_executed': False,
        'release': dict.fromkeys(('candidate_admitted', 'physical_contact', 'complete_joint_resistance', 'fabrication', 'climbing'), False)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry-sha256', required=True)
    parser.add_argument('--mode', choices=('plan', 'extract'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'preserve existing output')
    report, data, pins, panels = read_sources(args.geometry_sha256)
    result = plan(report, pins) if args.mode == 'plan' else extract(report, data, pins, panels, dict(PARAMETERS))
    result['execution'] = {'sys_orig_argv': sys.orig_argv, 'cwd': str(Path.cwd()), 'python': sys.version,
        'PYTHONPATH': os.environ.get('PYTHONPATH'), 'parent_serialized_extraction_marker': os.environ.get('EOERE_PARENT_SERIALIZED_EXTRACTION')}
    verify(pins)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'path': str(args.output), 'sha256': sha(args.output), 'bytes': args.output.stat().st_size,
                      'source_pins': len(pins), 'actual_candidate_extraction': args.mode == 'extract'}))


if __name__ == '__main__':
    main()
