"""Known answers for finite beam objectivity and exact rigid-arm work."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts.thin_bolted_corotational_methods import (
    ROTATION_SCALE,
    CorotationalBeam,
    physical_rotation_moment,
    rigid_port,
    rigid_port_force_dual,
    rigid_port_wrench_dual,
    so3_exp,
    so3_left_jacobian,
    so3_left_jacobian_inverse,
    so3_log,
)

LENGTH, AREA, IY, IZ, J, E, G = 800., 3000., 2e6, 3e6, 1e6, 11000., 700.


def beam(basis=None):
    basis = np.eye(3) if basis is None else basis
    origin = np.array([32., -81., 47.])
    return CorotationalBeam.from_properties(
        [origin, origin + LENGTH * basis[:, 0]], basis, AREA, IY, IZ, J, E, G)


def linear_world_stiffness(element):
    transform = np.zeros((12, 12))
    for node in range(2):
        start = 6 * node
        transform[start:start+3, start:start+3] = element.reference_basis.T
        transform[start+3:start+6, start+3:start+6] = element.reference_basis.T / ROTATION_SCALE
    return transform.T @ element.local_stiffness @ transform


def rotate_state(element, q, rotation, translation):
    state = q.reshape(2, 6)
    answer = np.zeros_like(state)
    for node in range(2):
        position = element.reference_positions[node]
        answer[node, :3] = rotation @ (position + state[node, :3]) + translation - position
        answer[node, 3:] = ROTATION_SCALE * so3_log(rotation @ so3_exp(state[node, 3:] / ROTATION_SCALE))
    return answer.ravel()


@pytest.mark.parametrize("theta", [np.zeros(3), np.array([1e-8, -2e-8, 3e-8]),
                                   np.array([.13, -.22, .24]), np.array([1., -.7, .3])])
def test_so3_matches_independent_rotation_and_inverse(theta):
    np.testing.assert_allclose(so3_exp(theta), Rotation.from_rotvec(theta).as_matrix(), atol=2e-15)
    np.testing.assert_allclose(so3_log(so3_exp(theta)), theta, atol=2e-15)
    np.testing.assert_allclose(so3_left_jacobian_inverse(theta) @ so3_left_jacobian(theta),
                               np.eye(3), atol=2e-15)


def test_port_jacobian_and_physical_force_moment_at_twenty_degrees():
    center = np.array([20., 40., -30.])
    point = center + [35., -22., 80.]
    theta = np.array([2., -1., 3.])
    theta *= np.deg2rad(20.) / np.linalg.norm(theta)
    q = np.r_[np.array([2., 3., -4.]), ROTATION_SCALE * theta]
    position, derivative = rigid_port(point, center, q)
    h = 1e-3
    numerical = np.column_stack([(rigid_port(point, center, q + h * e)[0]
                                  - rigid_port(point, center, q - h * e)[0]) / (2 * h)
                                 for e in np.eye(6)])
    np.testing.assert_allclose(derivative, numerical, atol=1e-11, rtol=2e-9)
    force = np.array([17., -26., 33.])
    dual = rigid_port_force_dual(point, center, q, force)
    actual_arm = position - center - q[:3]
    np.testing.assert_allclose(physical_rotation_moment(theta, dual[3:]),
                               np.cross(actual_arm, force), atol=1e-11)
    increment = np.array([.3, -.5, .4, 2., -3., 1.])
    assert abs(dual @ increment - force @ (derivative @ increment)) < 1e-12
    moment = np.array([41., -73., 29.])
    wrench_dual = rigid_port_wrench_dual(point, center, q, force, moment)
    np.testing.assert_allclose(physical_rotation_moment(theta, wrench_dual[3:]),
                               np.cross(actual_arm, force) + moment, atol=1e-11)


def test_port_local_basis_has_same_world_state_and_dual():
    basis = so3_exp([.3, -.2, .1])
    local = np.array([2., -1., 3., 140., -35., 65.])
    world = np.r_[basis @ local[:3], basis @ local[3:]]
    point, center = np.array([52., -18., 63.]), np.array([10., 3., -4.])
    xp, jp = rigid_port(point, center, local, basis)
    xw, jw = rigid_port(point, center, world)
    transform = np.zeros((6, 6))
    transform[:3, :3] = transform[3:, 3:] = basis
    np.testing.assert_allclose(xp, xw, atol=1e-13)
    np.testing.assert_allclose(jp, jw @ transform, atol=1e-15)


@pytest.mark.parametrize("angle", [0., .12, np.deg2rad(20.), np.deg2rad(80.)])
def test_exact_common_rigid_rotation_is_unstrained(angle):
    element = beam(so3_exp([.11, .25, -.17]))
    axis = np.array([2., -3., 5.]); axis /= np.linalg.norm(axis)
    rotation = so3_exp(axis * angle)
    q = rotate_state(element, np.zeros(12), rotation, np.array([123., -41., 35.]))
    response = element.response(q, tangent=False)
    assert response["energy_nmm"] < 1e-19
    assert np.linalg.norm(response["residual_work_conjugate_q"]) < 1e-8
    assert np.linalg.norm(response["local_rotations_rad"]) < 1e-14


def test_deformed_energy_and_physical_forces_are_objective():
    element = beam(so3_exp([.13, -.25, .19]))
    q = np.array([1., -.6, .3, 7., -6., 4., 2., .9, -.7, 11., 5., -9.])
    rotation = so3_exp(np.array([2., -1., 3.]) / np.sqrt(14.) * np.deg2rad(20.))
    changed = rotate_state(element, q, rotation, np.array([29., -43., 13.]))
    np.testing.assert_allclose(element.energy(changed), element.energy(q), rtol=1e-11)
    f, changed_f = element.residual(q).reshape(2, 6), element.residual(changed).reshape(2, 6)
    for node in range(2):
        np.testing.assert_allclose(changed_f[node, :3], rotation @ f[node, :3], atol=1e-8, rtol=1e-10)
        moment = physical_rotation_moment(q.reshape(2, 6)[node, 3:] / ROTATION_SCALE, f[node, 3:])
        changed_moment = physical_rotation_moment(changed.reshape(2, 6)[node, 3:] / ROTATION_SCALE,
                                                  changed_f[node, 3:])
        np.testing.assert_allclose(changed_moment, rotation @ moment, atol=1e-7, rtol=1e-10)


def test_undeformed_tangent_recovers_existing_linear_beam():
    element = beam(so3_exp([.13, -.2, .17]))
    expected = linear_world_stiffness(element)
    actual = element.tangent(np.zeros(12))
    np.testing.assert_allclose(actual, expected, rtol=2e-7, atol=2e-5)
    assert np.linalg.norm(actual - actual.T) / np.linalg.norm(actual) < 1e-8


def test_axial_energy_and_force_are_known_answer():
    element = beam()
    q = np.zeros(12); q[6] = .35
    np.testing.assert_allclose(element.energy(q), E * AREA / LENGTH * .35**2 / 2, rtol=1e-12)
    force = element.residual(q)
    np.testing.assert_allclose(force[[0, 6]], E * AREA / LENGTH * .35 * np.array([-1., 1.]), rtol=1e-12)
    np.testing.assert_allclose(force[[1, 2, 3, 4, 5, 7, 8, 9, 10, 11]], 0., atol=1e-12)


def test_torsion_and_free_common_twist_gauge_are_known_answer():
    element = beam()
    q = np.zeros(12); q[9] = 12.
    angle = q[9] / ROTATION_SCALE
    np.testing.assert_allclose(element.energy(q), G * J / LENGTH * angle**2 / 2, rtol=1e-12)
    force = element.residual(q)
    np.testing.assert_allclose(force[[3, 9]] * ROTATION_SCALE,
                               G * J / LENGTH * angle * np.array([-1., 1.]), rtol=1e-12)
    common_twist = so3_exp([np.deg2rad(20.), 0., 0.])
    changed = rotate_state(element, q, common_twist, np.zeros(3))
    np.testing.assert_allclose(element.energy(changed), element.energy(q), rtol=1e-12)
    changed_force = element.residual(changed)
    assert abs(changed_force[3] + changed_force[9]) < 1e-12


@pytest.mark.parametrize("direction,inertia,rotation_index,sign", [(1, IZ, 5, 1), (2, IY, 4, -1)])
def test_small_tip_cantilever_recovers_timoshenko_known_answer(direction, inertia, rotation_index, sign):
    element = beam()
    stiffness = linear_world_stiffness(element)[6:, 6:]
    force = np.zeros(6); force[direction] = .001
    free = np.linalg.solve(stiffness, force)
    expected_tip = force[direction] * (LENGTH**3 / (3 * E * inertia) + LENGTH / ((5./6.) * G * AREA))
    expected_rotation = sign * force[direction] * LENGTH**2 / (2 * E * inertia)
    np.testing.assert_allclose(free[direction], expected_tip, rtol=1e-13)
    np.testing.assert_allclose(free[rotation_index] / ROTATION_SCALE, expected_rotation, rtol=1e-13)
    q = np.r_[np.zeros(6), free]
    # Tiny transverse motion introduces second-order axial strain; subtracting
    # two 800mm chord lengths also gives an approximately5e-9N roundoff floor.
    np.testing.assert_allclose(element.residual(q)[6:], force, atol=1e-8, rtol=1e-6)


def test_analytic_residual_and_numerical_tangent_match_energy_derivatives():
    element = beam()
    q = np.array([.2, -.4, .1, 11., -8., 6., .7, .9, -.3, -4., 7., 15.])
    direction = np.array([.1, -.2, .3, -.7, .2, .4, .4, .7, -.3, .4, -.2, .3])
    step = .001
    work = (element.energy(q + step * direction) - element.energy(q - step * direction)) / (2 * step)
    np.testing.assert_allclose(element.residual(q) @ direction, work, rtol=1e-8)
    tangent = element.tangent(q)
    directional = (element.residual(q + step * direction) - element.residual(q - step * direction)) / (2 * step)
    np.testing.assert_allclose(tangent @ direction, directional, atol=2e-6, rtol=3e-8)
    assert np.linalg.norm(tangent - tangent.T) / np.linalg.norm(tangent) < 1e-8
    np.testing.assert_allclose(element.tangent(q, step_mm=.0005), tangent, atol=2e-5, rtol=2e-6)


def test_unsupported_rotation_branches_and_director_flips_raise():
    with pytest.raises(ValueError, match="pi"):
        so3_exp([np.pi, 0., 0.])
    with pytest.raises(ValueError, match="pi"):
        so3_log(Rotation.from_rotvec([np.pi, 0., 0.]).as_matrix())
    q = np.zeros(12); q[[5, 11]] = ROTATION_SCALE * np.pi / 2.
    with pytest.raises(ValueError, match="director"):
        beam().energy(q)
    q = np.zeros(12); q[6] = -LENGTH
    with pytest.raises(ValueError, match="collapsed"):
        beam().energy(q)
