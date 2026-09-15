"""Beveled runner mesh must reproduce its solid and arbitrary affine motion."""
import numpy as np
import pytest

from fea.floor_flush_mesh import FlushStructure, mesh_runner
from fea.floor_taper_mesh import locate


def test_actual_bevel_volume_centroid_and_affine_interpolation():
    centre = [0., (100**2+100*80+80**2)/(3*180), 20*(100+2*80)/(3*180)]
    record = {'name': 'runner', 'start': [0., 0., 10.], 'end': [0., 100., 10.],
        'axis': [0., 1., 0.], 'section_u': [1., 0., 0.], 'section_v': [0., 0., -1.],
        'width_mm': 4., 'depth_mm': 20.,
        'flush_runner_geometry': {'front_y_mm': 0., 'rear_bottom_y_mm': 100.,
            'rear_top_y_mm': 80., 'x_bounds_mm': [-2., 2.], 'height_mm': 20.,
            'expected_volume_mm3': 7200., 'expected_centroid_xyz_mm': centre}}
    structure = FlushStructure({})
    mesh_runner(structure, record, [(0., 40., 10.)], size=30.)
    member = structure.members['runner']
    assert member['retained_mesh_volume_mm3'] == pytest.approx(7200.)
    assert member['retained_mesh_centroid_xyz_mm'] == pytest.approx(centre)
    matrix = np.array([[1., 2., 3.], [0., -.5, .2], [1., -.2, 0.]])
    offset = np.array([4., 5., 6.])
    for point in ((1., 40., 4.), (0., 90., 10.), (-2., 80., 20.), (2., 100., 0.)):
        ids, weights = locate(structure, 'runner', point)
        field = np.array([matrix@structure.nodes[n]+offset for n in ids])
        assert weights@field == pytest.approx(matrix@point+offset, abs=1.e-8)
    with pytest.raises(ValueError, match='outside'):
        locate(structure, 'runner', [0., 100., 20.])
