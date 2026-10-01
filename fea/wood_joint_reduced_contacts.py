"""Area-cell resultants of the frozen contact faces for reduced static analysis.

Each spring samples the mean movement at an exact clipped cell's area centroid.
This preserves uniform-traction resultants, not local pressure peaks. Contact
stiffness and active/open status belong to the caller, not this geometry export.
"""
import hashlib
import math
from pathlib import Path

import cadquery as cq
import numpy as np


def load_shapes(root, model):
    shapes = {}
    for member in model['members']:
        binding = member['current_finished_step_binding']
        path = Path(root)/binding['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != binding['file_sha256']:
            raise ValueError('Current STEP changed: '+str(path))
        shape = cq.importers.importStep(str(path)).val()
        if len(shape.Solids()) != 1 or not shape.isValid():
            raise ValueError('Require one valid current solid')
        shapes[member['member_id']] = shape
    return shapes


def area_cells(face, normal, *, size_mm=80., minimum_divisions=2):
    """Clip a regular plane grid to a real trimmed face, retaining area moments."""
    if size_mm <= 0 or minimum_divisions < 1:
        raise ValueError('Positive cell size and minimum divisions required')
    normal = np.asarray(normal, dtype=float)
    normal /= np.linalg.norm(normal)
    edges = [edge for edge in face.Edges() if edge.geomType() == 'LINE']
    if not edges:
        raise ValueError('Current contact cell orientation requires a straight boundary edge')
    longest = max(edges, key=lambda edge: edge.Length())
    u = np.asarray((longest.endPoint()-longest.startPoint()).toTuple())
    u /= np.linalg.norm(u)
    center = np.asarray(face.Center().toTuple())
    plane = cq.Plane(origin=center.tolist(), xDir=u.tolist(), normal=normal.tolist())
    local = plane.toLocalCoords(face)
    bounds = local.BoundingBox()
    nx = max(minimum_divisions, math.ceil(bounds.xlen/size_mm))
    ny = max(minimum_divisions, math.ceil(bounds.ylen/size_mm))
    xs, ys = np.linspace(bounds.xmin, bounds.xmax, nx+1), np.linspace(bounds.ymin, bounds.ymax, ny+1)
    cells = []
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            wire = cq.Wire.makePolygon([(x0,y0,0.), (x1,y0,0.), (x1,y1,0.), (x0,y1,0.)], close=True)
            cell = cq.Face.makeFromWires(wire)
            pieces = local.intersect(cell).Faces()
            area = sum(part.Area() for part in pieces)
            if area <= 1e-8:
                continue
            # Several disconnected pieces may share a cell. This is an area
            # resultant, not a claim of wood occupancy at the resultant point.
            centroid = sum((part.Center()*part.Area() for part in pieces), cq.Vector())/area
            point = plane.toWorldCoords(centroid)
            cells.append({'point_xyz_mm': list(point.toTuple()), 'area_mm2': area})
    area = sum(row['area_mm2'] for row in cells)
    first_moment = sum((np.asarray(row['point_xyz_mm'])*row['area_mm2'] for row in cells), np.zeros(3))
    if (not math.isclose(area, face.Area(), abs_tol=1e-5, rel_tol=1e-8)
            or not np.allclose(first_moment/area, center, atol=1e-6, rtol=0.)):
        raise ValueError('Clipped contact cells lost face area or first moment')
    return cells


def contact_samples(root, model, geometry, *, size_mm=80., minimum_divisions=2, shapes=None):
    """Return current opposed-face cells and the eight existing floor-face cells."""
    shapes = load_shapes(root, model) if shapes is None else shapes
    samples = []
    for index, record in enumerate(geometry['contact_patches']):
        first, second = record['member_ids']
        ia, ib = record['source_face_indices']
        common = shapes[first].Faces()[ia-1].intersect(shapes[second].Faces()[ib-1])
        candidates = [face for face in common.Faces()
                      if abs(face.Area()-record['area_mm2']) < 1e-5
                      and np.linalg.norm(np.asarray(face.Center().toTuple())-record['centroid_xyz_mm']) < 1e-6]
        if len(candidates) != 1:
            raise ValueError('Stored contact patch does not reconstruct uniquely')
        cells = area_cells(candidates[0], record['normal_on_first_xyz'],
                           size_mm=size_mm, minimum_divisions=minimum_divisions)
        for cell_index, cell in enumerate(cells):
            samples.append({'name': f'contact_{index}_{cell_index}', 'first': first, 'second': second,
                            'normal_xyz': [-value for value in record['normal_on_first_xyz']],
                            'source_patch_index': index, 'kind': 'timber_or_panel_contact', **cell})
    floors = []
    for index, record in enumerate(geometry['floor_patches']):
        name = record['member_id']
        face = shapes[name].Faces()[record['source_face_index']-1]
        cells = area_cells(face, record['outward_normal_xyz'],
                           size_mm=size_mm, minimum_divisions=minimum_divisions)
        for cell_index, cell in enumerate(cells):
            floors.append({'name': f'floor_{name}_{cell_index}', 'first': name, 'second': 'floor',
                           'normal_xyz': [0.,0.,1.], 'source_floor_patch_index': index,
                           'kind': 'floor_normal', **cell})
    if {row['first'] for row in floors} != {row['member_id'] for row in geometry['floor_patches']}:
        raise ValueError('Floor sampling lost an existing member')
    return samples, floors


def self_check():
    # Eccentric circular hole exercises trimmed-area conservation independently
    # of the current assembly. No native mechanics solver is involved.
    rectangle = cq.Face.makeFromWires(cq.Wire.makePolygon([(0,0,0),(120,0,0),(120,80,0),(0,80,0)], close=True))
    hole = cq.Face.makeFromWires(cq.Wire.makeCircle(5., cq.Vector(37.,29.,0.), cq.Vector(0.,0.,1.)))
    face = rectangle.cut(hole).Faces()[0]
    rows = area_cells(face, [0,0,1], size_mm=40.)
    expected_area = 120*80-math.pi*25
    expected_center = (np.array([60.,40.,0.])*9600-np.array([37.,29.,0.])*math.pi*25)/expected_area
    assert math.isclose(sum(row['area_mm2'] for row in rows), expected_area, rel_tol=1e-10)
    measured = sum((np.asarray(row['point_xyz_mm'])*row['area_mm2'] for row in rows), np.zeros(3))/expected_area
    assert np.allclose(measured, expected_center, atol=1e-8)


if __name__ == '__main__':
    self_check()
    print('Trimmed contact area and eccentric first-moment check passed')
