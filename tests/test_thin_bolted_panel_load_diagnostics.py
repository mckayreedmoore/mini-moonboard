"""Known force/moment projections, area subtraction and geometric strain scales."""

import math

import numpy as np
import pytest

from scripts.thin_bolted_panel_load_diagnostics import (
    REFERENCE,
    affine_traction_interpretation,
    mass_only_quadrature,
    rhs_correction,
    rigid_modes,
    warp_slope_markers,
)
from scripts.thin_bolted_panel_mechanics import CAT, SheetBasis


def rectangle_panel():
    basis = SheetBasis(120., 80., 3)
    return {"basis": basis, "geometry": {"origin": np.zeros(3), "axes": np.eye(3),
                                        "front_height": 80.},
            "holes": [], "q": np.zeros(3 * basis.size), "thickness": CAT, "twist_scale": 1.}


def test_mass_only_bore_subtraction_has_known_area_and_first_moments():
    panel = rectangle_panel()
    panel["holes"] = [{"xy_mm": [33., 26.], "diameter_mm": 10.}]
    points, area = mass_only_quadrature(panel)
    assert area.sum() == pytest.approx(9600 - 25 * math.pi)
    assert area @ points == pytest.approx([9600 * 60 - 25 * math.pi * 33,
                                          9600 * 40 - 25 * math.pi * 26])
    assert panel["mass_row"].sum() == pytest.approx(1.)


def test_projection_restores_exact_wrench_and_is_minimum_coefficient_norm():
    panel = rectangle_panel()
    rigid = rigid_modes(panel, np.zeros(3))
    original = np.zeros(3 * panel["basis"].size)
    desired = np.array([5., -6., 7., 13., -17., 19.])
    correction, delta = rhs_correction(rigid, original, desired)
    assert delta == pytest.approx(desired)
    assert rigid.T @ correction == pytest.approx(desired, abs=1e-10)
    # Every self-equilibrated addition is orthogonal to this range(R)
    # projection, so it increases coefficient-load squared norm.
    extra = np.random.default_rng(706).normal(size=len(original))
    extra -= rigid @ np.linalg.solve(rigid.T @ rigid, rigid.T @ extra)
    assert np.linalg.norm(rigid.T @ extra) < 1e-10
    assert correction @ extra == pytest.approx(0., abs=1e-12)
    assert np.linalg.norm(correction + extra) > np.linalg.norm(correction)


def test_uniform_affine_traction_matches_known_force_and_centroid_moment():
    panel = rectangle_panel()
    points, area = mass_only_quadrature(panel)
    force = np.array([5., -6., 7.])
    delta = np.r_[force, np.cross(np.array([60., 40., 0.]) - REFERENCE, force)]
    correction, _ = rhs_correction(rigid_modes(panel), np.zeros(3 * panel["basis"].size), delta)
    interpretation = affine_traction_interpretation(panel, points, area, delta, correction)
    assert interpretation["traction_global_rigid_field_coefficients"] == pytest.approx(
        [*(force / 9600).tolist(), 0., 0., 0.], abs=1e-13)
    assert interpretation["maximum_sampled_affine_traction_norm_n_per_mm2"] == pytest.approx(np.linalg.norm(force) / 9600)
    assert interpretation["force_wrench_residual_norm_n"] < 1e-10
    assert interpretation["moment_wrench_residual_norm_nmm"] < 1e-8
    assert interpretation["generalized_load_difference_from_producer_projection_norm_n"] > .1


def test_quadratic_warp_slopes_and_von_karman_markers_are_known():
    panel = rectangle_panel()
    basis = panel["basis"]
    points = np.array([(x, y) for x in np.linspace(0, 120, basis.order)
                       for y in np.linspace(0, 80, basis.order)])
    # Centered parabola gives zero fitted affine slopes independently of
    # constant assembly translation or a superimposed known tilt.
    x, y = points.T
    value = 11. + .3 * x - .4 * y + .001 * (x - 60)**2 / 2 + .002 * (y - 40)**2 / 2
    q = panel["q"]
    q[2 * basis.size:] = np.linalg.solve(basis.values(points), value)
    result = warp_slope_markers(panel, q, 41)
    assert result["best_affine_outward_coefficients_mm_mm_per_mm"][1:] == pytest.approx([.3, -.4])
    assert result["maximum_sampled_affine_removed_slope_norm"] == pytest.approx(.1)
    assert result["maximum_half_affine_removed_slope_norm_squared"] == pytest.approx(.005)
    assert result["maximum_abs_von_karman_component_markers"] == pytest.approx([.0018, .0032, .0048])
    assert result["maximum_abs_first_order_membrane_strain_components"] == pytest.approx([0., 0., 0.])
    assert result["geometrically_nonlinear_solution_or_applicability_pass"] is False
