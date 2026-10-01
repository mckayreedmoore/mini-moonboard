"""Regression checks for the generic clamped-annulus plate response."""

from __future__ import annotations

import pytest

from mini_moonboard.washer_plate_response import uniform_pressure_clamped_annulus


def test_mit_ocw_clamped_annulus_known_answer_at_mid_radius():
    response = uniform_pressure_clamped_annulus(
        inner_radius=1.0,
        outer_radius=10.0,
        flexural_rigidity=1.0,
        pressure=1.0,
        radius=5.0,
    )

    assert response.deflection == pytest.approx(17.551854163565369, rel=2e-14)


@pytest.mark.parametrize("edge", [1.0, 10.0])
def test_clamped_annulus_has_zero_deflection_and_radial_slope_at_both_edges(edge):
    response = uniform_pressure_clamped_annulus(
        inner_radius=1.0,
        outer_radius=10.0,
        flexural_rigidity=1.0,
        pressure=1.0,
        radius=edge,
    )

    assert response.deflection == pytest.approx(0.0, abs=1e-12)
    assert response.radial_slope == pytest.approx(0.0, abs=1e-12)


def test_response_scales_linearly_with_pressure_and_inversely_with_rigidity():
    def response(*, pressure, flexural_rigidity):
        return uniform_pressure_clamped_annulus(
            inner_radius=1.0,
            outer_radius=10.0,
            flexural_rigidity=flexural_rigidity,
            pressure=pressure,
            radius=5.0,
        )

    base = response(pressure=1.0, flexural_rigidity=1.0)
    doubled_pressure = response(pressure=2.0, flexural_rigidity=1.0)
    doubled_rigidity = response(pressure=1.0, flexural_rigidity=2.0)

    assert doubled_pressure.deflection == pytest.approx(2.0 * base.deflection)
    assert doubled_pressure.radial_slope == pytest.approx(2.0 * base.radial_slope)
    assert doubled_rigidity.deflection == pytest.approx(base.deflection / 2.0)
    assert doubled_rigidity.radial_slope == pytest.approx(base.radial_slope / 2.0)


def test_geometric_scaling_preserves_normalized_shape():
    base = uniform_pressure_clamped_annulus(
        inner_radius=1.0,
        outer_radius=10.0,
        flexural_rigidity=1.0,
        pressure=1.0,
        radius=5.0,
    )
    scale = 3.0
    enlarged = uniform_pressure_clamped_annulus(
        inner_radius=scale,
        outer_radius=10.0 * scale,
        flexural_rigidity=1.0,
        pressure=1.0,
        radius=5.0 * scale,
    )

    assert enlarged.deflection == pytest.approx(scale**4 * base.deflection)
    assert enlarged.radial_slope == pytest.approx(scale**3 * base.radial_slope)


@pytest.mark.parametrize(
    "overrides",
    [
        {"inner_radius": 0.0},
        {"outer_radius": 1.0},
        {"flexural_rigidity": 0.0},
        {"radius": 11.0},
        {"pressure": float("nan")},
        {"outer_radius": float("inf")},
    ],
)
def test_invalid_inputs_fail_closed(overrides):
    inputs = {
        "inner_radius": 1.0,
        "outer_radius": 10.0,
        "flexural_rigidity": 1.0,
        "pressure": 1.0,
        "radius": 5.0,
    }
    inputs.update(overrides)

    with pytest.raises(ValueError):
        uniform_pressure_clamped_annulus(**inputs)


def test_non_numeric_inputs_raise_type_error():
    with pytest.raises(TypeError, match="inner_radius"):
        uniform_pressure_clamped_annulus(
            inner_radius="1.0",
            outer_radius=10.0,
            flexural_rigidity=1.0,
            pressure=1.0,
            radius=5.0,
        )


def test_numerically_thin_annulus_fails_closed():
    outer_radius = 1.0001

    with pytest.raises(ValueError, match="outer_radius / inner_radius must be at least 1.02"):
        uniform_pressure_clamped_annulus(
            inner_radius=1.0,
            outer_radius=outer_radius,
            flexural_rigidity=1.0,
            pressure=1.0,
            radius=(1.0 + outer_radius) / 2.0,
        )


def test_minimum_supported_radius_ratio_matches_high_precision_check():
    outer_radius = 1.02
    response = uniform_pressure_clamped_annulus(
        inner_radius=1.0,
        outer_radius=outer_radius,
        flexural_rigidity=1.0,
        pressure=1.0,
        radius=(1.0 + outer_radius) / 2.0,
    )

    # 80-digit Decimal evaluation of the same source boundary equations.
    assert response.deflection == pytest.approx(4.166680281671852e-10, rel=2e-8)


def test_numerically_thin_annulus_is_rejected_even_at_zero_pressure():
    with pytest.raises(ValueError, match="outer_radius / inner_radius must be at least 1.02"):
        uniform_pressure_clamped_annulus(
            inner_radius=1.0,
            outer_radius=1.0001,
            flexural_rigidity=1.0,
            pressure=0.0,
            radius=1.00005,
        )
