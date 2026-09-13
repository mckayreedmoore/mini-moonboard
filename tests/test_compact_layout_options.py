"""Independent arithmetic checks for the bounded layout sensitivity screen."""

import math

import numpy as np
import pytest

from fea.dowel_yield import single_shear
from scripts.compact_layout_options import LEG, RIM, capacity


@pytest.mark.parametrize('diameter', [.375, .5, .625, .75, .875, 1.])
def test_directional_capacity_matches_scalar_yield_equations(diameter):
    forces = np.array([[0., 1., 0.], [0., 0., 1.], [0., .3, -.9]])
    actual, _ = capacity(forces, diameter)
    for force, reference in zip(forces, actual, strict=True):
        angles = [math.degrees(math.acos(min(1., abs(float(force @ grain)) /
                                             np.linalg.norm(force)))) for grain in (RIM, LEG)]
        ktheta = 1+max(angles)/360
        perpendicular = 6100*.5**1.45/math.sqrt(diameter)
        bearing = [5600*perpendicular /
                   (5600*math.sin(math.radians(angle))**2 +
                    perpendicular*math.cos(math.radians(angle))**2)*diameter
                   for angle in angles]
        moment = 45000*diameter**3/6
        scalar = single_shear(
            main_length_in=3.5, side_length_in=3.5,
            main_bearing_lb_in=bearing[0], side_bearing_lb_in=bearing[1],
            main_yield_moment_lb_in=moment, side_yield_moment_lb_in=moment,
            gap_in=0., reduction_terms={
                'Im': 4*ktheta, 'Is': 4*ktheta, 'II': 3.6*ktheta,
                'IIIm': 3.2*ktheta, 'IIIs': 3.2*ktheta, 'IV': 3.2*ktheta})
        assert reference == pytest.approx(scalar['reference_lateral_lbf']*4.4482216152605)


def test_higher_bending_yield_cannot_reduce_single_fastener_reference():
    angles = np.linspace(0., math.pi, 91)
    forces = np.column_stack([np.zeros(len(angles)), np.cos(angles), np.sin(angles)])
    ordinary, modes = capacity(forces, .625)
    higher, _ = capacity(forces, .625, 90000.)
    assert np.all(higher >= ordinary-1e-9)
    mode_ii = modes == 2
    assert mode_ii.any()
    assert np.allclose(higher[mode_ii], ordinary[mode_ii], rtol=1e-12)


def test_capacity_uses_supplied_grains_under_common_rotation():
    angle = .17
    rotation = np.array([[1., 0., 0.], [0., math.cos(angle), -math.sin(angle)],
                         [0., math.sin(angle), math.cos(angle)]])
    forces = np.array([[0., 100., -200.], [0., -50., 10.]])
    expected, modes = capacity(forces, .625)
    actual, rotated_modes = capacity(forces @ rotation.T, .625,
                                     leg=rotation @ LEG, rim=rotation @ RIM)
    assert np.allclose(actual, expected, rtol=1e-12)
    assert np.array_equal(rotated_modes, modes)
