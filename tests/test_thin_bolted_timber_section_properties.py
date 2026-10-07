"""Analytic known answers for targeted exact finished-section queries."""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np
import pytest

from scripts import thin_bolted_timber_section_properties as section


def rectangle():
    return cq.Solid.makeBox(100., 60., 20.)


def analytic_subtraction(area_removed, center_removed, moment_removed):
    gross_area, gross_center = 6000., np.array([50., 30.])
    area = gross_area - area_removed
    center = (gross_area * gross_center - area_removed * center_removed) / area
    moment = np.diag([6000. * 100.**2 / 12., 6000. * 60.**2 / 12.])
    moment += gross_area * np.outer(gross_center - center, gross_center - center)
    moment -= moment_removed + area_removed * np.outer(center_removed - center, center_removed - center)
    return area, center, moment


def check_properties(shape, area, center, moment):
    value = section.measure_section(shape, origin=[0., 0., 10.], grain=[0., 0., 1.],
                                    expected_prior_area_mm2=area)
    assert value["finished_area_mm2"] == pytest.approx(area, abs=1e-6)
    assert value["centroid_uv_mm"] == pytest.approx(center, abs=1e-7)
    assert np.asarray(value["centroidal_area_moment_matrix_uv_mm4"]) == pytest.approx(moment, abs=1e-4)
    assert value["established_section_measure_area_mm2"] == pytest.approx(area, abs=1e-3)
    assert value["bores_or_other_voids_restored"] is False
    assert value["shear_area_method_qualified"] is False
    return value


def test_rectangle_area_centroid_and_central_inertias():
    check_properties(rectangle(), 6000., [50., 30.], np.diag([5e6, 1.8e6]))


def test_concentric_circular_hole_preserves_void_in_surface_integrals():
    hole = cq.Solid.makeCylinder(10., 30., cq.Vector(50., 30., -5.))
    area = 6000. - math.pi * 100.
    moment = np.diag([5e6 - math.pi * 1e4 / 4., 1.8e6 - math.pi * 1e4 / 4.])
    check_properties(rectangle().cut(hole), area, [50., 30.], moment)


def test_eccentric_circular_hole_recovers_cross_inertia_and_centroid():
    hole = cq.Solid.makeCylinder(10., 30., cq.Vector(70., 40., -5.))
    area, center, moment = analytic_subtraction(math.pi * 100., np.array([70., 40.]),
                                               np.eye(2) * math.pi * 1e4 / 4.)
    value = check_properties(rectangle().cut(hole), area, center, moment)
    assert value["product_integral_uv_mm4"] < 0.


def test_corner_recess_actual_directional_extrema_exclude_absent_bbox_corner():
    recess = cq.Solid.makeBox(40., 20., 30., cq.Vector(60., 40., -5.))
    area, center, moment = analytic_subtraction(800., np.array([80., 50.]),
                                               np.diag([800. * 40.**2 / 12., 800. * 20.**2 / 12.]))
    shape = rectangle().cut(recess)
    check_properties(shape, area, center, moment)
    # beta=(1,1); actual max(U+V)=140, whereas the absent box corner gives160.
    first = moment @ np.ones(2)
    wrench = {"cut_point_xyz_mm": [*map(float, center), 10.], "force_on_lower_portion_xyz_n": [0., 0., 0.],
              "moment_on_lower_portion_about_cut_xyz_nmm": [float(first[1]), -float(first[0]), 0.]}
    result = section.measure_section(shape, origin=[0., 0., 10.], grain=[0., 0., 1.], wrench=wrench)
    stress = result["linear_normal_stress"]
    assert stress["normal_stress_gradient_uv_n_mm3"] == pytest.approx([1., 1.], abs=1e-9)
    assert stress["combined_linear_normal_stress_extrema_n_mm2"] == pytest.approx(
        [-sum(center), 140. - sum(center)], abs=1e-5)
    assert stress["rectangle_corner_envelope_substituted"] is False


def test_complete_wrench_transport_removes_datum_eccentricity_for_centroidal_axial_force():
    wrench = {"cut_point_xyz_mm": [0., 0., 10.], "force_on_lower_portion_xyz_n": [0., 0., 1000.],
              "moment_on_lower_portion_about_cut_xyz_nmm": [30000., -50000., 0.]}
    result = section.measure_section(rectangle(), origin=[0., 0., 10.], grain=[0., 0., 1.], wrench=wrench)
    stress = result["linear_normal_stress"]
    assert stress["moment_about_actual_centroid_xyz_nmm"] == pytest.approx([0., 0., 0.], abs=1e-8)
    assert stress["combined_linear_normal_stress_extrema_n_mm2"] == pytest.approx([1. / 6., 1. / 6.])
    assert stress["complete_adjusted_NDS_resistance_or_acceptance"] is None
    assert stress["shear_stress_or_effective_shear_area"] is None


def test_same_station_area_or_wrench_mismatch_fails_closed():
    with pytest.raises(ValueError, match="frozen same-station"):
        section.measure_section(rectangle(), origin=[0., 0., 10.], grain=[0., 0., 1.], expected_prior_area_mm2=5999.)
    wrench = {"cut_point_xyz_mm": [0., 0., 11.], "force_on_lower_portion_xyz_n": [0., 0., 1000.],
              "moment_on_lower_portion_about_cut_xyz_nmm": [0., 0., 0.]}
    with pytest.raises(ValueError, match="section station"):
        section.measure_section(rectangle(), origin=[0., 0., 10.], grain=[0., 0., 1.], wrench=wrench)
