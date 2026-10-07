"""Known-answer necessary force allocation and eccentric-load moment checks."""

import numpy as np
import pytest

from scripts.thin_bolted_panel_equilibrium_bound import (
    minimum_peak_tension,
    normal_tilt_target,
)


def test_two_symmetric_heads_carry_centred_tension_equally():
    answer = minimum_peak_tension([[-1, 0], [1, 0]], [], 100., 0., 0.)
    assert answer["equilibrium_feasible"]
    assert answer["minimum_peak_tension_n"] == pytest.approx(50.)
    assert answer["head_tensions_n"] == pytest.approx([50., 50.])
    assert answer["dual_objective_n"] == pytest.approx(50.)


def test_compression_opposite_head_requires_additional_tension_for_couple():
    answer = minimum_peak_tension([[0, 0]], [[1, 0]], 100., 0., 100.)
    assert answer["minimum_peak_tension_n"] == pytest.approx(200.)
    assert answer["liberal_corner_compressions_n"] == pytest.approx([100.])


def test_free_head_row_cannot_resist_missing_tilt_direction():
    answer = minimum_peak_tension([[-1, 0], [1, 0]], [], 100., 100., 0.)
    assert not answer["equilibrium_feasible"]


def test_normal_tilt_uses_real_lever_and_same_world_reference():
    loads = [{"point_xyz_mm": [2., 3., -10.], "force_n": [0., -20., -100.]}]
    target = normal_tilt_target(loads, np.zeros(3), np.eye(3))
    assert target == pytest.approx((100., 500., -200.))
    moved = [{"point_xyz_mm": [9., 12., 2.], "force_n": [0., -20., -100.]}]
    assert normal_tilt_target(moved, np.array([7., 9., 12.]), np.eye(3)) == pytest.approx(target)
