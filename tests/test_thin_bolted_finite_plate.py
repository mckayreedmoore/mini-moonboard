"""Objective rigid motion, analytical stretches/bends and central derivatives."""

import math

import numpy as np
import pytest

from scripts.thin_bolted_finite_plate import APAProxy, FinitePlate, normal_derivatives
from scripts.thin_bolted_panel_mechanics import CAT, SheetBasis, plate_matrix


def collocation(basis):
    points = np.array([(x, y) for x in np.linspace(0, basis.width, basis.order)
                       for y in np.linspace(0, basis.height, basis.order)])
    return points, basis.values(points)


def coefficients(basis, values):
    points, matrix = collocation(basis)
    data = values(points)
    return np.concatenate([np.linalg.solve(matrix, data[:, i]) for i in range(3)])


@pytest.mark.parametrize("angle", [20., 73.])
def test_exact_rigid_rotation_has_no_strain_energy_and_rotates_offset_port(angle):
    basis = SheetBasis(120., 80., 1)
    plate = FinitePlate(basis)
    theta = math.radians(angle)
    rotation = np.array([[1., 0., 0.], [0., math.cos(theta), -math.sin(theta)],
                         [0., math.sin(theta), math.cos(theta)]])
    translation = np.array([7., -11., 13.])
    q = coefficients(basis, lambda p: np.c_[p, np.zeros(len(p))] @ (rotation - np.eye(3)).T + translation)
    for point in ([15., 23.], [120., 80.]):
        local = plate.point_energy(q, point)
        assert np.max(abs(local["strain"])) < 1e-14
        assert np.max(abs(local["curvature"])) < 1e-14
        assert local["energy_per_reference_area_n_per_mm"] < 1e-21
        port = plate.point_port(q, point, CAT / 2 + 100)
        assert port["position_xyz_mm"] == pytest.approx(rotation @ np.r_[point, CAT / 2 + 100] + translation, abs=1e-11)
        assert port["normal_xyz"] == pytest.approx(rotation[:, 2], abs=1e-13)


def test_superposed_arbitrary_rotation_preserves_nonzero_strain_energy():
    a = np.array([1.02, .01, .08]); b = np.array([-.02, .99, -.03])
    values = np.array([a, b, [.001, -.002, .004], [.002, .003, -.001], [-.001, .002, .005]])
    axis = np.array([1., -2., 3.]); axis /= np.linalg.norm(axis)
    cross = np.array([[0., -axis[2], axis[1]], [axis[2], 0., -axis[0]], [-axis[1], axis[0], 0.]])
    theta = math.radians(20.)
    rotation = np.eye(3) + math.sin(theta) * cross + (1 - math.cos(theta)) * cross @ cross
    initial, rotated = APAProxy().local_energy(values), APAProxy().local_energy(values @ rotation.T)
    assert rotated["strain"] == pytest.approx(initial["strain"], abs=1e-14)
    assert rotated["curvature"] == pytest.approx(initial["curvature"], abs=1e-14)
    assert rotated["energy_per_reference_area_n_per_mm"] == pytest.approx(initial["energy_per_reference_area_n_per_mm"], rel=1e-13)


def test_uniaxial_stretch_energy_gradient_and_tangent_match_exact_green_strain():
    basis = SheetBasis(12., 8., 1)
    plate = FinitePlate(basis)
    lam = 1.03
    direction = coefficients(basis, lambda p: np.c_[p[:, 0], np.zeros((len(p), 2))])
    q = (lam - 1) * direction
    points, area = basis.quadrature(3)
    result = plate.energy(q, points, area)
    ea = 5100000 * 4.4482216152605 / 304.8
    strain = .5 * (lam**2 - 1)
    assert result["energy_nmm"] == pytest.approx(.5 * ea * strain**2 * 96, rel=1e-12)
    assert direction @ result["gradient_n"] == pytest.approx(ea * strain * lam * 96, rel=1e-12)
    assert direction @ result["hessian_n_per_mm"] @ direction == pytest.approx(ea * (lam**2 + strain) * 96, rel=1e-12)


def test_exact_cylinder_has_zero_midplane_strain_and_known_covariant_curvature():
    radius, x = 1000., 437.
    theta = x / radius
    derivatives = np.array([[math.cos(theta), 0., math.sin(theta)], [0., 1., 0.],
                            [-math.sin(theta) / radius, 0., math.cos(theta) / radius],
                            [0., 0., 0.], [0., 0., 0.]])
    result = APAProxy().local_energy(derivatives)
    ei = 320000 * 4.4482216152605 * 25.4**2 / 304.8
    assert result["strain"] == pytest.approx([0., 0., 0.], abs=1e-14)
    assert result["curvature"] == pytest.approx([-1 / radius, 0., 0.], abs=1e-15)
    assert result["energy_per_reference_area_n_per_mm"] == pytest.approx(.5 * ei / radius**2, rel=1e-13)


def test_reference_tangent_matches_frozen_linear_plate_and_small_strain_energy():
    basis = SheetBasis(12., 8., 1)
    plate = FinitePlate(basis)
    points, area = basis.quadrature()
    q = np.zeros(3 * basis.size)
    finite = plate.energy(q, points, area)
    linear = plate_matrix(basis, points, area)
    assert finite["hessian_n_per_mm"] == pytest.approx(linear, rel=1e-12, abs=2e-8)
    direction = coefficients(basis, lambda p: np.c_[.002 * p[:, 0], -.003 * p[:, 1],
                                                    .001 * p[:, 0]**2 + .002 * p[:, 0] * p[:, 1]])
    scale = 1e-5
    energy = plate.energy(scale * direction, points, area)["energy_nmm"]
    assert energy == pytest.approx(.5 * scale**2 * direction @ linear @ direction, rel=1e-6)


def test_analytic_local_gradient_and_full_hessian_match_central_differences():
    section = APAProxy()
    values = np.array([[1.02, .01, .08], [-.02, .99, -.03], [.001, -.002, .004],
                       [.002, .003, -.001], [-.001, .002, .005]])
    result = section.local_energy(values)
    step = 1e-6
    gradient, hessian = [], []
    for column in range(15):
        direction = np.zeros(15); direction[column] = step
        plus, minus = section.local_energy(values + direction.reshape(5, 3)), section.local_energy(values - direction.reshape(5, 3))
        gradient.append((plus["energy_per_reference_area_n_per_mm"] - minus["energy_per_reference_area_n_per_mm"]) / (2 * step))
        hessian.append((plus["local_gradient"] - minus["local_gradient"]) / (2 * step))
    assert result["local_gradient"] == pytest.approx(gradient, rel=2e-7, abs=2e-7)
    assert result["local_hessian"] == pytest.approx(np.asarray(hessian).T, rel=2e-7, abs=2e-5)
    assert np.max(abs(result["local_hessian"] - result["local_hessian"].T)) < 1e-14 * np.max(abs(result["local_hessian"]))


def test_port_jacobian_hessian_and_left_handed_world_embedding():
    basis = SheetBasis(12., 8., 1)
    plate = FinitePlate(basis)
    q = coefficients(basis, lambda p: np.c_[.001 * p[:, 0] * p[:, 1], -.002 * p[:, 0],
                                           .002 * p[:, 0]**2 + .003 * p[:, 1]**2])
    origin = np.array([10., 20., 30.]); axes = np.diag([1., 1., -1.])
    point, z = np.array([4.3, 3.7]), 100 + CAT / 2
    port = plate.point_port(q, point, z, origin_xyz_mm=origin, axes_columns_xyz=axes)
    direction = np.random.default_rng(109).normal(size=len(q))
    step = 1e-5
    plus = plate.point_port(q + step * direction, point, z, origin_xyz_mm=origin, axes_columns_xyz=axes)
    minus = plate.point_port(q - step * direction, point, z, origin_xyz_mm=origin, axes_columns_xyz=axes)
    assert port["jacobian_xyz_per_coefficient"] @ direction == pytest.approx(
        (plus["position_xyz_mm"] - minus["position_xyz_mm"]) / (2 * step), rel=1e-8, abs=1e-8)
    assert np.einsum("ijk,k->ij", port["hessian_xyz_per_coefficient_squared"], direction) == pytest.approx(
        (plus["jacobian_xyz_per_coefficient"] - minus["jacobian_xyz_per_coefficient"]) / (2 * step), rel=2e-7, abs=1e-8)
    assert port["reference_position_xyz_mm"] == pytest.approx(origin + axes @ np.r_[point, z])


def test_collapsed_metric_is_rejected():
    with pytest.raises(ValueError, match="collapsed"):
        normal_derivatives(np.array([1., 0., 0.]), np.array([2., 0., 0.]))
