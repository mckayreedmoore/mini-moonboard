"""Reference wood-bearing inputs, not connection capacities."""

import math

import pytest

from mini_moonboard.bolted_timber_checks import (
    dfl_dowel_bearing_psi,
    dfl_net_parallel_tension_reference_lbf,
    dfl_parallel_row_tear_out_reference_lbf,
)


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


def test_dfl_net_tension_uses_all_bores_on_the_same_critical_section():
    assert dfl_net_parallel_tension_reference_lbf(1.5, 5.5, (7 / 16,)) == pytest.approx(
        4366.40625
    )
    assert dfl_net_parallel_tension_reference_lbf(1.5, 5.5, (7 / 16, 7 / 16)) == pytest.approx(
        3989.0625
    )


def test_dfl_row_tear_out_uses_lesser_end_or_pitch_distance():
    assert dfl_parallel_row_tear_out_reference_lbf(1.5, 1, 2.625) == pytest.approx(708.75)
    assert dfl_parallel_row_tear_out_reference_lbf(1.5, 2, 2.625, 1.125) == pytest.approx(607.5)
    assert dfl_parallel_row_tear_out_reference_lbf(1.5, 2, 0.75, 1.125) == pytest.approx(405)


@pytest.mark.parametrize(
    ("thickness", "width", "bores"),
    [
        (0, 5.5, (7 / 16,)),
        (1.5, 0, (7 / 16,)),
        (1.5, 5.5, ()),
        (1.5, 5.5, (0,)),
        (1.5, 5.5, (5.5,)),
        (math.nan, 5.5, (7 / 16,)),
    ],
)
def test_dfl_net_tension_rejects_missing_or_impossible_section(thickness, width, bores):
    with pytest.raises(ValueError):
        dfl_net_parallel_tension_reference_lbf(thickness, width, bores)


@pytest.mark.parametrize(
    ("thickness", "count", "end", "pitch"),
    [(0, 2, 2.625, 1.125), (1.5, 0, 2.625, None), (1.5, 2, 2.625, None),
     (1.5, 2, math.inf, 1.125), (1.5, 2, 2.625, 0)],
)
def test_dfl_row_tear_out_rejects_missing_or_invalid_geometry(thickness, count, end, pitch):
    with pytest.raises(ValueError):
        dfl_parallel_row_tear_out_reference_lbf(thickness, count, end, pitch)
