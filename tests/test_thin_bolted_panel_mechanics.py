"""Independent polynomial energies, beam solution and unilateral port laws."""

import math

import numpy as np
import pytest
from scipy.linalg import solve

from scripts.thin_bolted_panel_mechanics import (
    SheetBasis,
    disk_quadrature,
    equilibrium_cut_references,
    footprint_quadrature,
    load_cases,
    plate_matrix,
    point_load,
    point_matrix,
    positive_spring_solve,
)


def test_polynomial_bending_energy_and_six_rigid_modes():
    basis = SheetBasis(120., 80., 3)
    points, weights = basis.quadrature()
    grid = np.array([(x, y) for x in np.linspace(0, 120, basis.order)
                     for y in np.linspace(0, 80, basis.order)])
    b = basis.values(grid)
    q = np.zeros(3 * basis.size)
    kx, ky, kxy = .002, -.003, .001
    q[2 * basis.size:] = np.linalg.solve(b, kx * grid[:, 0]**2 / 2 + ky * grid[:, 1]**2 / 2 + kxy * grid[:, 0] * grid[:, 1])
    k = plate_matrix(basis, points, weights)
    lbf = 4.4482216152605
    dx, dy = 320000 * lbf * 25.4**2 / 304.8, 90500 * lbf * 25.4**2 / 304.8
    twist = (50500 * lbf / 25.4) * (23 / 32 * 25.4)**2 / 12
    expected = 120 * 80 * (dx * kx**2 + dy * ky**2 + 4 * twist * kxy**2) / 2
    assert q @ k @ q / 2 == pytest.approx(expected, rel=1e-11)
    for block, values in ((0, np.ones(len(grid))), (1, np.ones(len(grid))),
                          (2, np.ones(len(grid))), (2, grid[:, 0]), (2, grid[:, 1])):
        rigid = np.zeros_like(q)
        rigid[block * basis.size:(block + 1) * basis.size] = np.linalg.solve(b, values)
        assert np.linalg.norm(k @ rigid) < 1e-6
    rotation = np.zeros_like(q)
    rotation[:basis.size] = np.linalg.solve(b, -grid[:, 1])
    rotation[basis.size:2 * basis.size] = np.linalg.solve(b, grid[:, 0])
    assert np.linalg.norm(k @ rotation) < 1e-5


def test_free_sides_cantilever_matches_euler_bernoulli_exact_answer():
    basis = SheetBasis(300., 50., 4)
    points, weights = basis.quadrature()
    bending = plate_matrix(basis, points, weights)[2 * basis.size:, 2 * basis.size:]
    # Every y coefficient is equal: a 1D cylindrical plate, with free sides
    # and the zero-Poisson proxy. The first two open-knot x coefficients fix
    # displacement and derivative at x=0, exactly.
    transformation = np.kron(np.eye(basis.order), np.ones((basis.order, 1)))
    beam = transformation.T @ bending @ transformation
    f = np.zeros(basis.order)
    f[-1] = 100.
    q = np.r_[0., 0., solve(beam[2:, 2:], f[2:], assume_a="pos")]
    dx = 320000 * 4.4482216152605 * 25.4**2 / 304.8
    assert q[-1] == pytest.approx(100 * 300**3 / (3 * dx * 50), rel=1e-10)
    assert np.sum(beam @ q - f) == pytest.approx(-100, abs=1e-7)


def test_tension_and_compression_use_separate_active_ports():
    for force, expected, active in ((6., 3., [6., 0.]), (-6., -2., [0., 6.])):
        result = positive_spring_solve(np.zeros((1, 1)), np.array([force]),
                                       np.array([[1.], [-1.]]), np.array([2., 3.]))
        assert result["q"][0] == pytest.approx(expected)
        assert result["port_force_n"] == pytest.approx(active)
        assert result["gradient_inf_n"] < 1e-12


def test_polar_void_and_clipped_contact_preserve_independent_geometry():
    xy, weights = disk_quadrature(np.array([17., 23.]), 5.)
    assert weights.sum() == pytest.approx(math.pi * 25)
    assert weights @ xy == pytest.approx(math.pi * 25 * np.array([17., 23.]))
    assert weights @ (xy[:, 0] - 17)**2 == pytest.approx(math.pi * 5**4 / 4)
    triangle = np.array([[-20., 0., 0.], [20., 0., 0.], [0., 20., 0.]])
    xy, weights = footprint_quadrature([triangle], np.zeros(3), np.eye(3), 10., 10., 4.)
    assert weights.sum() == pytest.approx(100.)
    assert np.all(xy >= 0) and np.all(xy <= 10)


def test_original_six_signed_load_cases_are_retained():
    report = {"panel_machining": {"features": [{"identity": "hold_tnut_main_" + hold}
                                             for hold in ("A12", "K12", "A1")]}}
    cases = {r["id"]: r for r in load_cases(report)}
    expected = {"a12-rear": [0, 300], "a12-forward": [0, -300],
                "a12-left": [-300, 0], "k12-right": [300, 0],
                "k12-rear": [0, 300], "a1-rear": [0, 300]}
    for case_id, horizontal in expected.items():
        assert cases[case_id]["force_n"][:2] == horizontal
        assert cases[case_id]["force_n"][2] == pytest.approx(-2224.11080763025)


def test_world_port_map_preserves_rigid_rotations_and_thickness_arm():
    basis = SheetBasis(100., 80., 2)
    axes = np.array([[1, 0, 0], [0, math.sin(.7), math.cos(.7)],
                     [0, math.cos(.7), -math.sin(.7)]])
    origin = np.array([10., 20., 30.])
    panel = {"basis": basis, "geometry": {"axes": axes, "origin": origin}}
    grid = np.array([(x, y) for x in np.linspace(0, 100, basis.order)
                     for y in np.linspace(0, 80, basis.order)])
    b = basis.values(grid)
    omega = np.array([.02, -.01, .03])
    translation = np.array([3., -2., 5.])
    world_delta = grid @ axes[:, :2].T
    displacement = (translation + np.cross(omega, world_delta)) @ axes
    q = np.concatenate([np.linalg.solve(b, displacement[:, i]) for i in range(3)])
    point = origin + axes @ np.array([45., 35., -9.])
    assert point_matrix(panel, point) @ q == pytest.approx(translation + np.cross(omega, point - origin))
    force = np.array([123., -234., -345.])
    face = origin + axes @ np.array([45., 35., 9.])
    load, _ = point_load(panel, face, force, 109.)
    climber = face + axes[:, 2] * 100
    assert load @ q == pytest.approx(force @ (translation + np.cross(omega, climber - origin)))


def test_net_cut_uses_balanced_fresh_actions_and_full_bore_chords():
    panel = {"basis": SheetBasis(100., 80., 2),
             "geometry": {"name": "coupon", "origin": np.zeros(3), "axes": np.eye(3)},
             "holes": [{"xy_mm": [50., 40.], "diameter_mm": 10.}]}
    external = [{"point_xyz_mm": [100., 40., 0.], "force_n": [0., 0., -10.]}]
    screws = [{"point_xyz_mm": [0., 40., 0.], "force_on_receiver_n": [0., 0., -10.]}]
    result = equilibrium_cut_references(panel, screws, [], external, count=3)
    rolling = result["necessary_mean_resultant_maxima"]["mean_net_rolling_shear_ratio_CD1"]
    assert rolling["net_full_bore_width_mm"] == pytest.approx(70.)
    assert rolling["outward_shear_resultant_n"] == pytest.approx(10.)
    assert rolling["mean_net_rolling_shear_ratio_CD1"] == pytest.approx(10 / (350 * 4.4482216152605 / 304.8 * 70))
