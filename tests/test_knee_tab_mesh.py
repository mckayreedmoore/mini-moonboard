"""Retained tab volume, conforming continuity and physical attachment faces."""
import copy
from itertools import product

import numpy as np
import pytest

from fea.horizontal_panel_frame import Structure
from fea.knee_tab_mesh import attachment, mesh_member, tab_intervals


def record():
    return {'name': 'knee', 'start': [0., 0., 0.], 'end': [0., 0., 1000.],
            'section_u': [1., 0., 0.], 'width_mm': 88.9, 'depth_mm': 139.7,
            'tab_cut_boxes_sxq_mm': [[-1., 200., 0., 45.45, -69.85, 69.85],
                                     [700., 1001., -45.45, 0., -69.85, 69.85]]}


def test_volume_and_shared_native_nodes_without_ties():
    structure = Structure()
    item = record()
    mesh_member(structure, item, size=100.)
    member = structure.members['knee']
    assert member['retained_mesh_volume_mm3'] == pytest.approx(88.9*139.7*750.)
    assert not structure.equations
    assert item['additional_recovery_stations_mm'] == [200., 700.]
    # At each interior full-width interval, eight interface nodes are identical
    # native IDs on the two adjacent 20-node solids.
    cells = [c for c in member['tab_cells'] if c['station_interval_mm'] == [300., 400.]]
    assert len(cells) == 2
    ids = [set(structure.elements[c['element']][1]) for c in cells]
    assert len(ids[0] & ids[1]) == 8
    # The retained end strip shares its complete eight-node shoulder face.
    before = next(c for c in member['tab_cells'] if c['station_interval_mm'] == [100., 200.])
    after = next(c for c in member['tab_cells'] if c['station_interval_mm'] == [200., 300.]
                 and c['section_u_interval_mm'][0] < 0)
    assert len(set(structure.elements[before['element']][1]) &
               set(structure.elements[after['element']][1])) == 8


def test_attachments_stay_in_actual_wood_and_reproduce_rigid_motion():
    structure = Structure()
    mesh_member(structure, record(), [[-22.225, 15., 110.], [22.225, -15., 850.]], size=150.)
    for point in ([-22.225, 15., 110.], [22.225, -15., 850.]):
        tag = attachment(structure, 'knee', point)
        for equation in structure.equations[-3:]:
            # Affine translations and infinitesimal rigid rotations must all
            # satisfy the actual-face interpolation constraint.
            for direction in np.eye(3):
                residual = sum(coef*(np.asarray([1., 2., 3.])+
                    np.cross(direction, structure.nodes[node]))[dof-1]
                    for node, dof, coef in equation)
                assert residual == pytest.approx(0., abs=1.e-9)
        assert structure.nodes[tag] == point
    with pytest.raises(ValueError, match='outside actual retained'):
        attachment(structure, 'knee', [22.225, 15., 110.])


def test_reject_disconnected_or_non_half_width_tab_geometry():
    item = record()
    item['tab_cut_boxes_sxq_mm'][1][0] = 150.
    with pytest.raises(ValueError, match='positive full-width middle'):
        tab_intervals(item)
    item = record()
    item['tab_cut_boxes_sxq_mm'][0][2] = 5.
    with pytest.raises(ValueError, match='exact half-width'):
        tab_intervals(item)


def test_reflection_switches_retained_tab_without_changing_volume():
    left, right = record(), copy.deepcopy(record())
    right['tab_cut_boxes_sxq_mm'] = [[s0, s1, -u1, -u0, v0, v1]
        for s0, s1, u0, u1, v0, v1 in left['tab_cut_boxes_sxq_mm']]
    models = [Structure(), Structure()]
    for model, item in zip(models, (left, right), strict=True):
        mesh_member(model, item)
    assert models[0].members['knee']['retained_mesh_volume_mm3'] == pytest.approx(
        models[1].members['knee']['retained_mesh_volume_mm3'])
    assert models[0].members['knee']['tab_faces'][0.][0]['half'] == 0
    assert models[1].members['knee']['tab_faces'][0.][0]['half'] == 1


def test_c3d20_order_has_positive_constant_jacobian_at_all_quadrature_points():
    """Evaluate standard 20-node brick interpolation independently of mesher."""
    corners = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]])
    edges = np.array([[0, -1, -1], [1, 0, -1], [0, 1, -1], [-1, 0, -1],
                      [0, -1, 1], [1, 0, 1], [0, 1, 1], [-1, 0, 1],
                      [-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]])

    def weights(point):
        values = [np.prod(1+sign*point)*(np.dot(sign, point)-2)/8 for sign in corners]
        for sign in edges:
            along = int(np.flatnonzero(sign == 0)[0])
            values.append((1-point[along]**2)*np.prod(1+sign*point)/4)
        return np.array(values)

    model = Structure()
    item = record()
    # Inclined member catches world-axis assumptions in topology or ordering.
    item['end'] = [0., 600., 800.]
    mesh_member(model, item, size=250.)
    for cell in model.members['knee']['tab_cells']:
        coordinates = np.array([model.nodes[n] for n in model.elements[cell['element']][1]])
        for point in product((-np.sqrt(3/5), 0., np.sqrt(3/5)), repeat=3):
            point = np.array(point)
            derivative = np.column_stack([(weights(point+axis*1.e-6)-weights(point-axis*1.e-6))/2.e-6
                                          for axis in np.eye(3)])
            determinant = np.linalg.det(coordinates.T@derivative)
            assert determinant == pytest.approx(cell['volume_mm3']/8, rel=2.e-8)
