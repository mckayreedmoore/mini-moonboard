"""Physical wrench, reference-law and derivative controls for finite ports."""

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts.thin_bolted_finite_connectors import connector_response
from scripts.thin_bolted_frame_mechanics import connector_basis, spring_constitutive


def field(value, j, h=None):
    n = j.shape[1]
    return {"value_xyz": np.asarray(value), "J_csr": csr_matrix(j),
            "H_xyz_csr": [csr_matrix(a) for a in (np.zeros((3, n, n)) if h is None else h)]}


def rotating_field(value, angle, ndof, column):
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array([[c, -s, 0.], [s, c, 0.], [0., 0., 1.]])
    generator = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 0.]])
    current = rotation @ value
    j, h = np.zeros((3, ndof)), np.zeros((3, ndof, ndof))
    j[:, column] = generator @ current
    h[:, column, column] = generator @ generator @ current
    return field(current, j, h)


def test_fixed_director_matches_the_frozen_axial_circular_gap_law():
    first = field([.4, .7, -.2], np.c_[np.eye(3), np.zeros((3, 3))])
    second = field([0., 0., 0.], np.c_[np.zeros((3, 3)), np.eye(3)])
    axis = np.array([1., 2., 3.]) / np.sqrt(14)
    normal = field(axis, np.zeros((3, 6)))
    result = connector_response(first, second, normal, axial_stiffness_n_mm=20.,
                                lateral_stiffness_n_mm=50., radial_gap_mm=.1)
    basis = connector_basis(axis)
    force, jacobian, energy = spring_constitutive(basis @ first["value_xyz"], 20., 50., .1, True)
    block = basis @ np.c_[np.eye(3), -np.eye(3)]
    assert result["energy_nmm"] == pytest.approx(energy, abs=1e-12)
    np.testing.assert_allclose(result["gradient_n"], block.T @ force, atol=1e-12)
    np.testing.assert_allclose(result["hessian_csr"].toarray(), block.T @ jacobian @ block, atol=1e-11)


@pytest.mark.parametrize("angle", [0., np.deg2rad(20.), np.deg2rad(73.)])
def test_common_rigid_rotation_preserves_energy_and_zero_virtual_work(angle):
    first = rotating_field(np.array([3., 2., 1.]), angle, 1, 0)
    second = rotating_field(np.array([1., 0., -.2]), angle, 1, 0)
    normal = rotating_field(np.array([1., 0., 0.]), angle, 1, 0)
    result = connector_response(first, second, normal, axial_stiffness_n_mm=13.,
                                lateral_stiffness_n_mm=27., radial_gap_mm=.3)
    expected = .5 * 13 * 2**2 + .5 * 27 * (np.sqrt(2**2 + 1.2**2) - .3)**2
    assert result["energy_nmm"] == pytest.approx(expected, abs=1e-12)
    np.testing.assert_allclose(result["gradient_n"], 0., atol=1e-12)
    np.testing.assert_allclose(result["hessian_csr"].toarray(), 0., atol=1e-10)
    np.testing.assert_allclose(result["pair_spatial_moment_residual_nmm"], 0., atol=1e-12)


def test_distinct_capture_datums_do_not_create_rigid_rotation_compression():
    angle = np.deg2rad(20.)
    first = rotating_field(np.array([5., 0., 0.]), angle, 1, 0)
    second = field([0., 0., 0.], np.zeros((3, 1)))
    normal = rotating_field(np.array([1., 0., 0.]), angle, 1, 0)
    result = connector_response(first, second, normal, axial_stiffness_n_mm=1000.,
                                axial_sign=-1., reference_axial_projection_mm=-5.)
    assert abs(result["signed_axial_extension_mm"]) < 1e-12
    assert result["energy_nmm"] < 1e-20


def nonlinear_response(q):
    first = field(np.array([.5, 1., -.7]) + q[:3], np.c_[np.eye(3), np.zeros((3, 4))])
    second = field(np.array([-.2, .1, .2]) + q[3:6], np.c_[np.zeros((3, 3)), np.eye(3), np.zeros(3)])
    normal = rotating_field(np.array([.6, .8, 0.]), q[6], 7, 6)
    return connector_response(first, second, normal, axial_stiffness_n_mm=17.,
                              lateral_stiffness_n_mm=29., radial_gap_mm=.2)


def test_finite_director_gradient_and_full_geometric_tangent():
    q = np.array([.1, -.05, .03, .02, -.04, -.1, .12])
    response = nonlinear_response(q)
    step = 1e-5
    basis = np.eye(len(q)) * step
    numeric_gradient = np.array([(nonlinear_response(q + d)["energy_nmm"] - nonlinear_response(q - d)["energy_nmm"])
                                 / (2 * step) for d in basis])
    numeric_hessian = np.column_stack([(nonlinear_response(q + d)["gradient_n"] - nonlinear_response(q - d)["gradient_n"])
                                      / (2 * step) for d in basis])
    np.testing.assert_allclose(response["gradient_n"], numeric_gradient, rtol=1e-9, atol=1e-8)
    np.testing.assert_allclose(response["hessian_csr"].toarray(), numeric_hessian, rtol=1e-9, atol=1e-8)
    # Position forces alone have a nonzero couple. Director action closes it.
    assert np.linalg.norm(response["moment_on_director_owner_xyz_nmm"]) > 1.
    np.testing.assert_allclose(response["pair_spatial_moment_residual_nmm"], 0., atol=1e-12)


def test_zero_gap_at_zero_slip_keeps_the_reference_lateral_tangent():
    first = field([0., 0., 0.], np.eye(3))
    second = field([0., 0., 0.], np.zeros((3, 3)))
    normal = field([1., 0., 0.], np.zeros((3, 3)))
    result = connector_response(first, second, normal, lateral_stiffness_n_mm=50.)
    np.testing.assert_array_equal(result["hessian_csr"].toarray(), np.diag([0., 50., 50.]))


def test_nonunit_director_is_rejected():
    port = field([0., 0., 0.], np.eye(3))
    with pytest.raises(ValueError, match="unit material"):
        connector_response(port, port, field([2., 0., 0.], np.zeros((3, 3))))
