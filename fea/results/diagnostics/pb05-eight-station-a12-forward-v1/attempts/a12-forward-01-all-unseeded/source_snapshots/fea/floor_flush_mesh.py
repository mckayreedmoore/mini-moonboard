"""Actual trapezoidal runner meshes alongside the retained tapered-leg mesher."""
import math
from itertools import pairwise, product

import numpy as np

from fea import current_response_model as base
from fea.floor_recess_mesh import CORNERS, EDGES
from fea.floor_taper_mesh import TaperStructure, attachment, locate, mapped


def mesh_runner(structure, record, attachment_points=(), size=100.):
    data = record['flush_runner_geometry']
    front = data['front_y_mm']; rear_bottom = data['rear_bottom_y_mm']; rear_top = data['rear_top_y_mm']
    xmin, xmax = data['x_bounds_mm']; height = data['height_mm']
    grain, normal = np.array([0., 1., 0.]), np.array([0., 0., -1.])
    # Partition at every requested longitudinal station using a common normalized
    # coordinate; attachments are then interpolated in actual C3D20 cells.
    cuts = {0., 1., *np.linspace(0., 1., math.ceil((rear_bottom-front)/size)+1)}
    for point in attachment_points:
        _, y, z = point
        rear = rear_bottom+(rear_top-rear_bottom)*z/height
        fraction = (y-front)/(rear-front)
        if not -1.e-7 <= fraction <= 1+1.e-7:
            raise ValueError('Runner attachment outside trimmed profile')
        cuts.add(float(min(1., max(0., fraction))))
    # Merge near-coincident attachment fractions to avoid sliver elements.
    fractions = []
    for value in sorted(cuts):
        if not fractions or value-fractions[-1] > 1.e-6:
            fractions.append(value)
    fractions[-1] = 1.
    cells, nodes = [], {}
    def node(point):
        key = tuple(round(float(v), 8) for v in point)
        if key not in nodes:
            nodes[key] = structure.node(point)
        return nodes[key]
    volume = 0.; moment = np.zeros(3)
    for t0, t1 in pairwise(fractions):
        cell = {'q_mm': [-height, 0.], 'lower_s_mm': [front, front],
            'upper_s_mm': [rear_top, rear_bottom], 't_interval': [t0, t1],
            'taper_stations_mm': [0., 1.], 'recess_depth_mm': 0.,
            'raw_x_mm': [xmin, xmax], 'outer_left': True}
        ids = [node(mapped(cell, p, grain, normal)) for p in np.vstack((CORNERS, EDGES))]
        cell['element'] = structure.element('C3D20', ids, record['name'])
        cell_volume = 0.
        for point in product((-1/math.sqrt(3), 1/math.sqrt(3)), repeat=3):
            xyz = mapped(cell, point, grain, normal)
            fraction = (point[1]+1)/2
            length = (rear_top-front)*(1-fraction)+(rear_bottom-front)*fraction
            det = (xmax-xmin)*height*length*(t1-t0)/8
            if det <= 0:
                raise ValueError('Nonpositive runner Jacobian')
            cell_volume += det; moment += xyz*det
        cell['volume_mm3'] = cell_volume; volume += cell_volume; cells.append(cell)
    if not math.isclose(volume, data['expected_volume_mm3'], rel_tol=1.e-9, abs_tol=.03):
        raise ValueError('Runner native volume differs from CAD')
    centre = moment/volume
    if not np.allclose(centre, data['expected_centroid_xyz_mm'], rtol=0, atol=1.e-6):
        raise ValueError('Runner native centroid differs from CAD')
    start, end, u = (np.asarray(record[k], dtype=float) for k in ('start', 'end', 'section_u'))
    record.update(native_section_geometry='ACTUAL_FLUSH_RUNNER_C3D20',
        retained_mesh_volume_mm3=volume, retained_mesh_centroid_xyz_mm=centre.tolist())
    structure.members[record['name']] = {'record': record, 'start': start, 'axis': grain, 'u': u,
        'v': np.cross(grain, u), 'length': float(np.linalg.norm(end-start)), 'sections': {},
        'floor_taper_cells': cells, 'floor_taper_normal': normal,
        'retained_mesh_volume_mm3': volume, 'retained_mesh_centroid_xyz_mm': centre.tolist()}
    for point in attachment_points:
        locate(structure, record['name'], point)


class FlushStructure(TaperStructure):
    def member(self, record, attachment_points=(), size=100.):
        if 'flush_runner_geometry' in record:
            return mesh_runner(self, record, attachment_points, size)
        return super().member(record, attachment_points, size)


def prepare_flush(module, **kwargs):
    legs = module.floor_recess_geometry()
    runners = module.runner_end_geometry()
    raw = {p.name: p for p in module.uncut_wood_parts()}
    original = base.CurrentStructure, base.gross_member_record, base.floor_attachment
    def revised_record(part, *args, **options):
        record = original[1](part, *args, **options)
        if part.name in legs:
            record['floor_recess_geometry'] = legs[part.name]
        if part.name in runners:
            shape = raw[part.name].shape; bounds = shape.BoundingBox()
            record['flush_runner_geometry'] = {**runners[part.name],
                'x_bounds_mm': [bounds.xmin, bounds.xmax], 'height_mm': bounds.zlen,
                'expected_volume_mm3': shape.Volume(), 'expected_centroid_xyz_mm': shape.Center().toTuple()}
        return record
    def actual_floor(structure, name, point):
        if 'floor_taper_cells' in structure.members[name]:
            return attachment(structure, name, point)
        return original[2](structure, name, point)
    try:
        base.CurrentStructure = FlushStructure; base.gross_member_record = revised_record; base.floor_attachment = actual_floor
        return base.prepare(module, **kwargs)
    finally:
        base.CurrentStructure, base.gross_member_record, base.floor_attachment = original
