"""Reference wood-bearing inputs, not connection capacities."""

import math

import pytest

from mini_moonboard.bolted_timber_checks import dfl_dowel_bearing_psi


def test_dfl_three_eighths_bolt_parallel_and_perpendicular_reference_values():
    assert dfl_dowel_bearing_psi(0.375, 0) == 5600
    assert dfl_dowel_bearing_psi(0.375, 90) == pytest.approx(3650)


def test_dfl_angle_to_grain_uses_hankinson_bearing_interpolation():
    expected = 5600 * 3650 / (5600 * 0.5 + 3650 * 0.5)
    assert dfl_dowel_bearing_psi(0.375, 45) == pytest.approx(expected)
    assert 3650 < expected < 5600


@pytest.mark.parametrize("diameter", [0, -0.375, 0.2499, math.nan, math.inf])
def test_dfl_bearing_rejects_inapplicable_diameter(diameter):
    with pytest.raises(ValueError):
        dfl_dowel_bearing_psi(diameter, 0)


@pytest.mark.parametrize("angle", [-1, 91, math.nan, math.inf])
def test_dfl_bearing_rejects_inapplicable_angle(angle):
    with pytest.raises(ValueError):
        dfl_dowel_bearing_psi(0.375, angle)
