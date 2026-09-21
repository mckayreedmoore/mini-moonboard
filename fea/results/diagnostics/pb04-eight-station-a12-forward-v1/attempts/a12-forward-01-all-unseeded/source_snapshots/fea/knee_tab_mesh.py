"""Conforming C3D20 mesh for two opposite half-width end tabs.

The caller supplies exact CAD cut boxes in member coordinates: station from
the gross member start, section-u and section-v from its gross centreline.
Adjacent retained cells share native nodes. No tie, hinge, stiffness multiplier
or constraint connects the continuous timber at its shoulders.
"""
from itertools import pairwise

import numpy as np

from fea.horizontal_panel_frame import panel_kernel, shape8


def tab_intervals(record):
    """Validate the bounded two-tab geometry and return retained strip spans."""
    length = float(np.linalg.norm(np.asarray(record['end'])-record['start']))
    width, depth = float(record['width_mm']), float(record['depth_mm'])
    if not np.isfinite([length, width, depth]).all() or min(length, width, depth) <= 0:
        raise ValueError('Require positive finite tab member dimensions')
    boxes = np.asarray(record['tab_cut_boxes_sxq_mm'], dtype=float)
    if boxes.shape != (2, 6) or not np.isfinite(boxes).all():
        raise ValueError('Require exactly two finite CAD tab cut boxes')
    removals = []
    for s0, s1, u0, u1, v0, v1 in boxes:
        if not (s0 < s1 and u0 < u1 and v0 < v1):
            raise ValueError('Require ordered CAD cut box bounds')
        s0, s1 = max(0., s0), min(length, s1)
        u0, u1 = max(-width/2, u0), min(width/2, u1)
        v0, v1 = max(-depth/2, v0), min(depth/2, v1)
        if not np.allclose([v0, v1], [-depth/2, depth/2], atol=1.e-6, rtol=0):
            raise ValueError('Tab cut must remove full section depth')
        half = next((i for i, interval in enumerate(((-width/2, 0.), (0., width/2)))
                     if np.allclose([u0, u1], interval, atol=1.e-6, rtol=0)), None)
        if half is None or not s0 < s1:
            raise ValueError('Require exact half-width end removal')
        if abs(s0) < 1.e-6 and s1 < length-1.e-6:
            removals.append((half, 'start', s1))
        elif abs(s1-length) < 1.e-6 and s0 > 1.e-6:
            removals.append((half, 'end', s0))
        else:
            raise ValueError('Each tab removal must intersect exactly one member end')
    if {r[0] for r in removals} != {0, 1} or {r[1] for r in removals} != {'start', 'end'}:
        raise ValueError('Require opposite half-width cuts at opposite ends')
    shoulders = {end: station for _, end, station in removals}
    if shoulders['start'] >= shoulders['end']-1.e-6:
        raise ValueError('Require a positive full-width middle joining both tabs')
    retained = {0: [0., length], 1: [0., length]}
    for half, end, station in removals:
        retained[half][0 if end == 'start' else 1] = station
    return retained, sorted(shoulders.values())


def mesh_member(structure, record, attachment_points=(), size=100.):
    """Mesh actual retained wood using conforming half-width solid strips."""
    name = record['name']
    if name in structure.members:
        raise ValueError('Member already meshed: '+name)
    retained, shoulders = tab_intervals(record)
    start, end, u = (np.asarray(record[k], dtype=float) for k in ('start', 'end', 'section_u'))
    length = float(np.linalg.norm(end-start))
    axis = (end-start)/length
    v = np.cross(axis, u)
    if abs(np.dot(axis, u)) > 1.e-8 or abs(np.linalg.norm(u)-1) > 1.e-8:
        raise ValueError('Member axes must be orthonormal')
    stations = [float(np.dot(np.asarray(p)-start, axis)) for p in attachment_points]
    if any(s < -1.e-6 or s > length+1.e-6 for s in stations):
        raise ValueError('Tab attachment lies beyond physical member ends')
    stations = [min(length, max(0., s)) for s in stations]
    xs = panel_kernel.mesh_axes(0., length, size, [*stations, *shoulders])
    width, depth = record['width_mm'], record['depth_mm']
    section = [(-1, -1), (1, -1), (1, 1), (-1, 1),
               (0, -1), (1, 0), (0, 1), (-1, 0)]
    nodes, faces, cells = {}, {}, []

    def node(s, x, y):
        key = tuple(round(float(value), 8) for value in (s, x, y))
        if key not in nodes:
            nodes[key] = structure.node(start+axis*s+u*x+v*y)
        return nodes[key]

    def face(s, half):
        key = (round(s, 8), half)
        if key not in faces:
            centre = (-1 if half == 0 else 1)*width/4
            faces[key] = [node(s, centre+x*width/4, y*depth/2) for x, y in section]
        return faces[key]

    for a, b in pairwise(xs):
        for half, (low, high) in retained.items():
            if not low-1.e-7 <= (a+b)/2 <= high+1.e-7:
                continue
            first, last = face(a, half), face(b, half)
            centre = (-1 if half == 0 else 1)*width/4
            middle = [node((a+b)/2, centre+x*width/4, y*depth/2) for x, y in section[:4]]
            eid = structure.element('C3D20', first[:4]+last[:4]+first[4:]+last[4:]+middle, name)
            cells.append({'element': eid, 'station_interval_mm': [a, b],
                          'section_u_interval_mm': [-width/2, 0.] if half == 0 else [0., width/2],
                          'volume_mm3': (b-a)*width/2*depth})
    sections = {}
    tab_faces = {}
    for (station, half), ids in faces.items():
        sections.setdefault(station, set()).update(ids)
        tab_faces.setdefault(station, []).append({'half': half, 'nodes': ids,
            'centre_u_mm': (-1 if half == 0 else 1)*width/4, 'width_mm': width/2})
    record['additional_recovery_stations_mm'] = shoulders
    record['native_section_geometry'] = 'Conforming solid half-width strips with actual opposite end-tab removals'
    structure.members[name] = {'record': record, 'start': start, 'axis': axis, 'u': u, 'v': v,
        'length': length, 'sections': {s: sorted(ids) for s, ids in sections.items()},
        'tab_faces': tab_faces, 'tab_cells': cells,
        'retained_mesh_volume_mm3': sum(c['volume_mm3'] for c in cells)}


def attachment(structure, member_name, point):
    """Interpolate only within an actual retained half-section face."""
    member = structure.members[member_name]
    point = np.asarray(point, dtype=float)
    station = float(np.dot(point-member['start'], member['axis']))
    key = round(station, 8)
    if key not in member['tab_faces']:
        raise ValueError('Tab attachment station was not imprinted in member mesh')
    delta = point-(member['start']+station*member['axis'])
    x, y = float(np.dot(delta, member['u'])), float(np.dot(delta, member['v']))
    depth = member['record']['depth_mm']
    faces = [face for face in member['tab_faces'][key]
             if abs(x-face['centre_u_mm']) <= face['width_mm']/2+1.e-6 and abs(y) <= depth/2+1.e-6]
    if not faces:
        raise ValueError('Attachment lies outside actual retained tab section')
    face = faces[0]
    weights = shape8(2*(x-face['centre_u_mm'])/face['width_mm'], 2*y/depth)
    ids = face['nodes']
    reconstructed = sum(w*np.asarray(structure.nodes[n]) for n, w in zip(ids, weights, strict=True))
    if np.linalg.norm(reconstructed-point) > 1.e-6 or abs(sum(weights)-1) > 1.e-10:
        raise ValueError('Tab attachment interpolation lost affine geometry')
    tag = structure.node(point)
    for dof in (1, 2, 3):
        structure.equations.append([(tag, dof, 1.)]+[(n, dof, -float(w))
            for n, w in zip(ids, weights, strict=True) if abs(w) > 1.e-13])
    return tag
