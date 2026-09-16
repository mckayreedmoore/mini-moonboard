"""Actual constant-X timber prisms for the full-stock floor-runner candidate.

The convex YZ outline is retained at both ends. Floor and joint attachments
interpolate the actual C3D20 cells rather than a rigid gross-section end arm.
"""
import math
from itertools import pairwise, product

import numpy as np
from scipy.spatial import ConvexHull

from fea import current_response_model as base
from fea.floor_flush_mesh import mesh_runner
from fea.floor_recess_mesh import CORNERS, EDGES
from fea.floor_taper_mesh import attachment, locate, mapped


def geometry(record):
    data = record['uncut_prism_geometry']
    grain = np.asarray(record['axis'], dtype=float)
    if (not np.all(np.isfinite(grain)) or abs(grain[0]) > 1.e-8
            or abs(grain[2]) <= 1.e-8
            or not math.isclose(np.linalg.norm(grain), 1., abs_tol=1.e-8)):
        raise ValueError('Require a unit nonhorizontal grain axis in the YZ plane')
    normal = np.array([0., grain[2], -grain[1]])
    points = np.asarray(data['side_profile_yz_mm'], dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.all(np.isfinite(points)):
        raise ValueError('Require finite YZ profile points')
    points = points[ConvexHull(points).vertices]
    qs, ss = points@normal[1:], points@grain[1:]
    qvalues = []
    for q in sorted(qs):
        if not qvalues or q-qvalues[-1] > 1.e-6:
            qvalues.append(float(q))
    ends = []
    for q in qvalues:
        values = []
        for i, j in zip(range(len(points)), np.roll(np.arange(len(points)), -1), strict=True):
            if abs(qs[j]-qs[i]) < 1.e-7:
                if abs(q-qs[i]) < 1.e-6:
                    values.extend((ss[i], ss[j]))
            elif min(qs[i], qs[j])-1.e-7 <= q <= max(qs[i], qs[j])+1.e-7:
                fraction = min(1., max(0., (q-qs[i])/(qs[j]-qs[i])))
                values.append(ss[i]+fraction*(ss[j]-ss[i]))
        if not values or max(values)-min(values) <= 1.e-6:
            raise ValueError('Require noncollapsed longitudinal prism boundaries')
        ends.append((float(min(values)), float(max(values))))
    xmin, xmax = map(float, data['x_bounds_mm'])
    if not math.isfinite(xmin+xmax) or xmax-xmin <= 1.e-6:
        raise ValueError('Require positive finite prism width')
    return data, grain, normal, qvalues, ends, xmin, xmax


def mesh_member(structure, record, attachment_points=(), size=100.):
    if not math.isfinite(size) or size <= 0 or record['name'] in structure.members:
        raise ValueError('Require positive size and unmeshed member')
    data, grain, normal, qs, ends, xmin, xmax = geometry(record)
    # Common normalized grain subdivisions keep adjacent q strips conforming.
    count = max(1, math.ceil(max(high-low for low, high in ends)/size))
    nodes, cells = {}, []
    def node(point):
        key = tuple(round(float(value), 8) for value in point)
        if key not in nodes:
            nodes[key] = structure.node(point)
        return nodes[key]
    volume = 0.; moment = np.zeros(3)
    for index, (q0, q1) in enumerate(pairwise(qs)):
        lower = [ends[index][0], ends[index+1][0]]
        upper = [ends[index][1], ends[index+1][1]]
        for t0, t1 in pairwise(np.linspace(0., 1., count+1)):
            cell = {'q_mm': [q0, q1], 'lower_s_mm': lower, 'upper_s_mm': upper,
                    't_interval': [float(t0), float(t1)], 'taper_stations_mm': [0., 1.],
                    'recess_depth_mm': 0., 'raw_x_mm': [xmin, xmax], 'outer_left': True}
            ids = [node(mapped(cell, p, grain, normal)) for p in np.vstack((CORNERS, EDGES))]
            cell['element'] = structure.element('C3D20', ids, record['name'])
            cell_volume = 0.
            for point in product((-1/math.sqrt(3), 1/math.sqrt(3)), repeat=3):
                fraction = (point[1]+1)/2
                length = (upper[0]-lower[0])*(1-fraction)+(upper[1]-lower[1])*fraction
                det = (xmax-xmin)*(q1-q0)*length*(t1-t0)/8
                if det <= 0:
                    raise ValueError('Nonpositive uncut prism Jacobian')
                cell_volume += det
                moment += mapped(cell, point, grain, normal)*det
            cell['volume_mm3'] = cell_volume
            volume += cell_volume
            cells.append(cell)
    if not math.isclose(volume, data['expected_volume_mm3'], rel_tol=1.e-9, abs_tol=.03):
        raise ValueError('Native prism volume differs from actual CAD')
    centre = moment/volume
    if not np.allclose(centre, data['expected_centroid_xyz_mm'], atol=1.e-6, rtol=0):
        raise ValueError('Native prism centroid differs from actual CAD')
    start, end, u = (np.asarray(record[key], dtype=float) for key in ('start', 'end', 'section_u'))
    length = float(np.linalg.norm(end-start))
    start_s = float(start@grain)
    low = max(0., record.get('verification_grain_interval_mm', [start_s])[0]-start_s)
    attachment_stations = (float(np.asarray(point, dtype=float)@grain)-start_s
                           for point in attachment_points)
    recovery = sorted({station for station in
        [*(s-start_s for pair in ends for s in pair), *attachment_stations]
        if low <= station <= length})
    record.update(native_section_geometry='ACTUAL_UNCUT_PRISM_C3D20',
                  retained_mesh_volume_mm3=volume, retained_mesh_centroid_xyz_mm=centre.tolist(),
                  additional_recovery_stations_mm=recovery)
    structure.members[record['name']] = {'record': record, 'start': start, 'axis': grain,
        'u': u, 'v': np.cross(grain, u), 'length': length, 'sections': {},
        'floor_taper_cells': cells, 'floor_taper_normal': normal,
        'retained_mesh_volume_mm3': volume, 'retained_mesh_centroid_xyz_mm': centre.tolist()}
    for point in attachment_points:
        try:
            spec = panel_offset_spec(record, point)
            if spec is not None:
                panel_offset_weights(structure, record['name'], spec)
            else:
                locate(structure, record['name'], point)
        except ValueError as exc:
            raise ValueError(f"Exact-profile attachment outside {record['name']}: {point}") from exc


def panel_offset_spec(record, point):
    """Recognize only explicitly registered named panel midsurface axes."""
    rows = record.get('panel_midsurface_offsets', ())
    if not isinstance(rows, (list, tuple)):
        raise TypeError('Malformed panel midsurface registration')
    registered = []
    for row in rows:
        try:
            vectors = [np.asarray(row[key], dtype=float) for key in
                       ('point_xyz_mm', 'anchor_xyz_mm', 'direction_xyz')]
            valid = (isinstance(row['name'], str) and bool(row['name'].strip())
                     and all(vector.shape == (3,) and np.all(np.isfinite(vector))
                             for vector in vectors))
        except (KeyError, TypeError, ValueError):
            valid = False
        if not valid:
            raise ValueError('Malformed panel midsurface registration')
        registered.append((row, vectors[0]))
    matches = [row for row, registered_point in registered
               if np.allclose(point, registered_point, atol=1.e-8, rtol=0)]
    if len(matches) > 1:
        raise ValueError('Ambiguous registered panel midsurface point')
    return matches[0] if matches else None


def shape20_derivatives(point):
    """Exact natural-coordinate derivatives of the existing C3D20 basis."""
    point = np.asarray(point, dtype=float)
    rows = []
    for sign in CORNERS:
        factors = 1+sign*point
        rows.append([sign[k]*np.prod(np.delete(factors, k))
                     *(sign@point-2+factors[k])/8 for k in range(3)])
    for sign in EDGES:
        along = int(np.flatnonzero(sign == 0)[0])
        rows.append([(-point[k]*np.prod(1+sign*point)/2 if k == along else
                      (1-point[along]**2)*sign[k]*np.prod(np.delete(1+sign*point, k))/4)
                     for k in range(3)])
    return np.asarray(rows)


def panel_offset_weights(structure, name, spec):
    """Surface translation plus local infinitesimal rotation of a short rigid arm.

    This is a named panel-screw load-transfer idealization, not timber outside
    its CAD face. The matrix transpose retains the force and moment at the
    actual panel midsurface. Symmetric strain is not extended into the offset.
    """
    member = structure.members[name]
    point = np.asarray(spec['point_xyz_mm'], dtype=float)
    anchor = np.asarray(spec['anchor_xyz_mm'], dtype=float)
    direction = np.asarray(spec['direction_xyz'], dtype=float)
    half = base.panel_kernel.THICKNESS/2
    normal, grain = member['floor_taper_normal'], member['axis']
    outer_q = max(c['q_mm'][1] for c in member['floor_taper_cells'])
    if (not spec.get('name') or not all(np.isfinite(v).all() for v in (point, anchor, direction))
            or not np.allclose(direction, -normal, atol=1.e-8, rtol=0)
            or not np.allclose(anchor-point, direction*half, atol=1.e-7, rtol=0)
            or not math.isclose(float(anchor@normal), outer_q, abs_tol=1.e-6)):
        raise ValueError('Panel midsurface offset must meet its actual timber face')
    ids, weights = locate(structure, name, anchor)
    cell = next(c for c in member['floor_taper_cells'] if structure.elements[c['element']][1] == ids)
    q0, q1 = cell['q_mm']; t0, t1 = cell['t_interval']; x0, x1 = cell['raw_x_mm']
    fraction = (float(anchor@normal)-q0)/(q1-q0)
    lower = cell['lower_s_mm'][0]+fraction*np.diff(cell['lower_s_mm'])[0]
    upper = cell['upper_s_mm'][0]+fraction*np.diff(cell['upper_s_mm'])[0]
    t = (float(anchor@grain)-lower)/(upper-lower)
    natural = [2*(anchor[0]-x0)/(x1-x0)-1, 2*fraction-1, 2*(t-t0)/(t1-t0)-1]
    xyz = np.asarray([structure.nodes[n] for n in ids])
    derivatives = shape20_derivatives(natural)
    jacobian = xyz.T@derivatives
    if np.linalg.det(jacobian) <= 0:
        raise ValueError('Panel arm anchor has a nonpositive Jacobian')
    gradients = derivatives@np.linalg.inv(jacobian)
    arm = point-anchor
    matrices = np.array([w*np.eye(3)+.5*((gradient@arm)*np.eye(3)-np.outer(gradient, arm))
                         for w, gradient in zip(weights, gradients, strict=True)])
    return ids, matrices


def panel_offset_attachment(structure, name, spec):
    ids, matrices = panel_offset_weights(structure, name, spec)
    tag = structure.node(spec['point_xyz_mm'])
    for dof in range(3):
        structure.equations.append([(tag, dof+1, 1.)]+
            [(node, component+1, -float(matrix[dof, component]))
             for node, matrix in zip(ids, matrices, strict=True) for component in range(3)
             if abs(matrix[dof, component]) > 1.e-13])
    return tag


class UncutStructure(base.CurrentStructure):
    """Module-level class keeps native saved states pickleable."""
    def member(self, record, attachment_points=(), size=100.):
        if 'uncut_prism_geometry' in record:
            return mesh_member(self, record, attachment_points, size)
        if 'flush_runner_geometry' in record:
            return mesh_runner(self, record, attachment_points, size)
        return super().member(record, attachment_points, size)

    def attachment(self, name, point):
        if 'floor_taper_cells' in self.members[name]:
            spec = panel_offset_spec(self.members[name]['record'], point)
            if spec is not None:
                return panel_offset_attachment(self, name, spec)
            return attachment(self, name, point)
        return super().attachment(name, point)


def prepare_uncut(module, **kwargs):
    """Serial geometry adapters, restored even if preparation raises."""
    raw = {part.name: part for part in module.uncut_wood_parts()}
    runners = module.runner_end_geometry()
    panel_offsets = {}
    for connection in module.panel_connections():
        if not isinstance(connection, base.CurrentModule(module).timber.PanelScrew):
            raise TypeError('Panel midsurface registry requires named PanelScrew connections')
        if not connection.members[0].startswith(('main_', 'kicker_')):
            raise ValueError('Panel midsurface registry requires an actual panel receiver pair')
        half = base.panel_kernel.THICKNESS/2
        panel_offsets.setdefault(connection.members[1], []).append({
            'name': connection.name,
            'point_xyz_mm': (connection.start+connection.direction*half).toTuple(),
            'anchor_xyz_mm': (connection.start+connection.direction*(2*half)).toTuple(),
            'direction_xyz': connection.direction.toTuple()})
    original = base.CurrentStructure, base.gross_member_record, base.floor_attachment
    def revised_record(part, *args, **options):
        record = original[1](part, *args, **options)
        shape = raw[part.name].shape
        bounds = shape.BoundingBox()
        if part.name.startswith(('base_side_', 'base_principal_', 'lumber_leg_', 'base_knee_')):
            vertices = [v.Center().toTuple() for v in shape.Vertices()]
            if any(min(abs(x-bounds.xmin), abs(x-bounds.xmax)) > 1.e-6 for x, _, _ in vertices):
                raise ValueError('Native uncut member requires constant-X prism')
            grain = np.asarray(record['axis'], dtype=float)
            stations = [float(np.dot(vertex, grain)) for vertex in vertices]
            for key, station in (('start', min(stations)), ('end', max(stations))):
                point = np.asarray(record[key], dtype=float)
                record[key] = (point+grain*(station-float(point@grain))).tolist()
            record['verification_grain_interval_mm'] = [min(stations), max(stations)]
            record['uncut_prism_geometry'] = {
                'side_profile_yz_mm': sorted({(y, z) for _, y, z in vertices}),
                'x_bounds_mm': [bounds.xmin, bounds.xmax],
                'expected_volume_mm3': shape.Volume(),
                'expected_centroid_xyz_mm': shape.Center().toTuple()}
            record['panel_midsurface_offsets'] = panel_offsets.get(part.name, [])
        if part.name in runners:
            record['flush_runner_geometry'] = {**runners[part.name],
                'x_bounds_mm': [bounds.xmin, bounds.xmax], 'height_mm': bounds.zlen,
                'expected_volume_mm3': shape.Volume(),
                'expected_centroid_xyz_mm': shape.Center().toTuple()}
        return record
    def actual_floor(structure, name, point):
        if 'floor_taper_cells' in structure.members[name]:
            return attachment(structure, name, point)
        return original[2](structure, name, point)
    try:
        base.CurrentStructure = UncutStructure
        base.gross_member_record = revised_record
        base.floor_attachment = actual_floor
        return base.prepare(module, **kwargs)
    finally:
        base.CurrentStructure, base.gross_member_record, base.floor_attachment = original
