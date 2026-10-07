"""Independent rectangular torsion benchmarks and same-cut stress-bound fixtures."""

import math

import numpy as np
import pytest

from scripts import thin_bolted_flange_torsion as torsion


@pytest.mark.parametrize("aspect,coefficient", [(1., .1406), (2., .2287), (4., .2808), (8., .307)])
def test_primary_published_rectangular_J_table(aspect, coefficient):
    section = torsion.rectangle_torsion(aspect, 1.)
    observed = (section["J_lower_mm4"]+section["J_upper_mm4"])/(2*aspect)
    assert observed == pytest.approx(coefficient, abs=5.1e-4 if aspect == 8. else 5.1e-5)
    assert section["polar_second_moment_substituted_for_J"] is False


def test_independent_primary_two_by_half_mm_benchmark():
    section = torsion.rectangle_torsion(2., .5)
    assert section["J_lower_mm4"] == pytest.approx(.0702, abs=5.1e-5)


def test_thin_rectangle_closed_form_limit_and_homogeneous_scaling():
    thin = torsion.rectangle_torsion(10000., 1.)
    assert thin["J_lower_mm4"]/(10000./3.) == pytest.approx(1., abs=6.4e-5)
    assert thin["global_torsion_shear_bound_mpa_per_nmm"] == pytest.approx(3./10000., rel=6.4e-5)
    first, scaled = torsion.rectangle_torsion(4., 1.), torsion.rectangle_torsion(12., 3.)
    assert scaled["J_lower_mm4"] == pytest.approx(first["J_lower_mm4"]*3**4)
    assert scaled["global_torsion_shear_bound_mpa_per_nmm"] == pytest.approx(first["global_torsion_shear_bound_mpa_per_nmm"]/3**3)


@pytest.mark.parametrize("aspect", [1., 2., 7.428571428571429])
def test_exact_positive_series_tail_brackets_finer_sum(aspect):
    coarse, fine = torsion.rectangle_torsion(aspect, 1., 8), torsion.rectangle_torsion(aspect, 1., 2048)
    assert coarse["J_lower_mm4"] < fine["J_lower_mm4"] <= fine["J_upper_mm4"] < coarse["J_upper_mm4"]


def test_prandtl_torque_integral_independently_matches_J_series():
    # T=2 integral(phi), using independent 2D Gauss quadrature at G*theta=1.
    abscissa, weights = np.polynomial.legendre.leggauss(96)
    width, thickness = 2., 1.
    observed = 0.
    for i, y in enumerate(abscissa*width/2):
        for j, z in enumerate(abscissa*thickness/2):
            observed += weights[i]*weights[j]*torsion.prandtl_unit_field(width, thickness, y, z)["phi_mm2_per_unit_G_twist"]
    observed *= 2*width*thickness/4
    section = torsion.rectangle_torsion(width, thickness)
    assert observed == pytest.approx((section["J_lower_mm4"]+section["J_upper_mm4"])/2, rel=2e-7)


def test_point_stresses_obey_analytic_norm_bound_and_free_surface_conditions():
    width, thickness = 41.275, 5.55625
    for y in np.linspace(-width/2, width/2, 9):
        for z in np.linspace(-thickness/2, thickness/2, 9):
            field = torsion.prandtl_unit_field(width, thickness, float(y), float(z))
            assert math.hypot(field["tau_xy_mpa_per_unit_G_twist"], field["tau_xz_mpa_per_unit_G_twist"]) <= thickness*(1+1e-12)
            if abs(y) == width/2:
                assert abs(field["phi_mm2_per_unit_G_twist"]) < 1e-12
                assert abs(field["tau_xy_mpa_per_unit_G_twist"]) < 1e-12
            if abs(z) == thickness/2:
                assert abs(field["phi_mm2_per_unit_G_twist"]) < 1e-12
                assert abs(field["tau_xz_mpa_per_unit_G_twist"]) < 1e-12


def test_simultaneous_N_V_M_T_bound_preserves_signed_full_same_section_actions():
    row = torsion.simultaneous_section_bound(width_mm=4., thickness_mm=2., removed_center_width_mm=0.,
        force_local_n=[-100., 3., -4.], moment_local_nmm=[-40., 20., -30.], fy_mpa=200., scenario="gross_rectangle")
    sigma = 100/8 + 20/(4*2**2/6) + 30/(2*4**2/6)
    tau_v = 1.5*5/8
    tau_t = 40*2/row["torsion_rectangle"]["J_lower_mm4"]
    expected = math.sqrt(sigma**2 + 3*(tau_v+tau_t)**2)
    assert row["simultaneous_nominal_vm_bound_mpa"] == pytest.approx(expected)
    assert row["simultaneous_nominal_first_yield_bound_index"] == pytest.approx(expected/200.)
    assert row["same_section_moment_T_M1_M2_nmm"] == [-40., 20., -30.]
    assert row["nominal_field_pointwise_analytic_bound"] is True
    assert row["physical_fitting_strength_or_complete_joint_acceptance"] is False


def test_hole_proxy_cannot_inherit_gross_rectangle_applicability():
    common = {"width_mm": 41.275, "thickness_mm": 5.55625, "removed_center_width_mm": 14.2875,
        "force_local_n": [0., 0., 0.], "moment_local_nmm": [1000., 0., 0.], "fy_mpa": 227.527}
    gross = torsion.simultaneous_section_bound(**common, scenario="gross_rectangle")
    proxy = torsion.simultaneous_section_bound(**common, scenario="two_ligament_equal_twist_proxy")
    assert gross["gross_rectangle_fills_removed_hole"] is True
    assert proxy["two_separate_ligaments_equal_twist_and_rectangular_shear_allocation_assumed"] is True
    assert proxy["actual_holed_plate_torsion_sharing_or_stress_concentrations_verified"] is False
    assert proxy["nominal_torsion_shear_norm_bound_mpa"] > gross["nominal_torsion_shear_norm_bound_mpa"]


@pytest.mark.parametrize("width,thickness,terms", [(0., 1., 64), (1., float("nan"), 64), (1., 1., True), (1., 1., 0)])
def test_nonfinite_zero_or_invalid_series_inputs_reject(width, thickness, terms):
    with pytest.raises((ValueError, TypeError)):
        torsion.rectangle_torsion(width, thickness, terms)


def test_historical_or_failed_component_field_is_not_admitted():
    with pytest.raises(ValueError, match="accepted physical common-shaft"):
        torsion.extend_flange_comparisons({"schema": "thin_bolted_common_shaft_steel/v1"})
