"""Independent known answers for the fresh thin-frame matrix method."""

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import thin_bolted_frame_mechanics as mechanics


def member_fixture():
    return {"name": "test_member", "start": [0., 0., 0.], "end": [1000., 0., 0.],
            "axis": [1., 0., 0.], "section_u": [0., 1., 0.], "section_v": [0., 0., 1.],
            "width_mm": 38.1, "depth_mm": 139.7}


def test_analytic_coupons_close_and_unilateral_support_rejects_tipping():
    result = mechanics.method_coupons()
    assert result["simple_beam_reactions_n"] == [80., 20.]
    assert result["outside_support_load_rejected"]
    assert result["virtual_work_error_nmm"] < 1e-13
    elastic = mechanics.elastic_method_coupons()
    assert max(r["absolute_error"] for r in elastic["cantilever_axial_two_bending_torsion"]) < 1e-15


def test_force_dual_operator_preserves_equal_opposite_world_wrenches():
    edge = {"first": "one", "second": "two", "point_xyz_mm": [3., 4., 5.], "direction_xyz": [2., -1., 4.]}
    matrix = mechanics.equilibrium_operator(["one", "two"], [edge], np.zeros(3), 1.)
    actions = matrix.toarray()[:, 0].reshape(2, 6)
    expected = np.r_[[2., -1., 4.], np.cross([3., 4., 5.], [2., -1., 4.])]
    np.testing.assert_allclose(actions[0], expected)
    np.testing.assert_allclose(actions.sum(axis=0), 0.)


@pytest.mark.parametrize("scale", [10., 100., 1000.])
def test_point_matrix_rotation_scale_does_not_change_physical_displacement(scale):
    point = np.array([101., -73., 28.])
    translation = np.array([3., -2., 1.])
    rotation = np.array([.03, -.02, .01])
    np.testing.assert_allclose(mechanics.point_matrix(point, np.zeros(3), scale) @ np.r_[translation, rotation * scale],
                               translation + np.cross(rotation, point))


def test_beam_stiffness_has_exact_six_rigid_motions():
    length = 500.
    k = mechanics.beam_stiffness(length, 4000., 8e6, 4e6, 2e6, 11000., 700.)
    for component in range(6):
        q = np.zeros(12)
        if component < 3:
            q[component] = q[component + 6] = 1.
        else:
            rotation = np.eye(3)[component - 3]
            q[3:6] = q[9:12] = rotation
            q[6:9] = np.cross(rotation, [length, 0., 0.])
        assert np.max(np.abs(k @ q)) < 1e-7


def test_eccentric_tip_force_matches_bending_shear_and_torsion_known_answer():
    member = member_fixture()
    assembly = mechanics.ElasticAssembly({"raw_fittings": []}, {"members": [member]}, {}, beam_size=100.)
    point, force = np.array([1000., 100., 0.]), np.array([0., 0., -1.])
    applied = np.asarray(assembly.port("test_member", point).T @ force)
    q = np.zeros(assembly.ndof)
    free = np.arange(6, assembly.ndof)
    q[free] = np.linalg.solve(assembly.K.toarray()[np.ix_(free, free)], applied[free])
    width, depth, L, E, G = 38.1, 139.7, 1000., 11031.612, .064 * 11031.612
    A, Iy, J = width * depth, width * depth**3 / 12., mechanics.rectangular_torsion(width, depth)
    expected = -(L**3 / (3 * E * Iy) + L / ((5 / 6) * G * A) + 100.**2 * L / (G * J))
    observed = (assembly.port("test_member", point) @ q)[2]
    assert observed == pytest.approx(expected, rel=1e-9)
    assert np.max(np.abs(assembly.port("test_member", point) @ assembly.rigid_modes() -
                         np.hstack((np.eye(3), -mechanics.cross_matrix(point - mechanics.REFERENCE))))) < 1e-10


def test_off_node_eccentric_point_load_converges_to_cantilever_known_answer():
    point = np.array([371., 100., 0.])
    errors = []
    width, depth, E, G = 38.1, 139.7, 11031.612, .064 * 11031.612
    a, eccentricity = point[:2]
    expected = -(a**3 / (3 * E * width * depth**3 / 12) + a / ((5 / 6) * G * width * depth)
                 + eccentricity**2 * a / (G * mechanics.rectangular_torsion(width, depth)))
    for size in (50., 25.):
        assembly = mechanics.ElasticAssembly({"raw_fittings": []}, {"members": [member_fixture()]}, {}, beam_size=size)
        port = assembly.port("test_member", point)
        applied = np.asarray(port.T @ [0., 0., -1.])
        q = np.zeros(assembly.ndof)
        free = np.arange(6, assembly.ndof)
        q[free] = np.linalg.solve(assembly.K.toarray()[np.ix_(free, free)], applied[free])
        errors.append(abs(float((port @ q)[2]) - expected) / abs(expected))
    assert errors[1] < errors[0]
    assert errors[1] < .01


def test_member_section_recovery_accounts_for_uniform_gravity_between_supports():
    geo = {"members": [member_fixture()], "bodies": [{"id": "test_member", "mass_kg": 100. / mechanics.GRAVITY,
                                                    "center_xyz_mm": [500., 0., 0.]}]}
    actions = [{"first": "test_member", "second": "floor", "point_xyz_mm": [x, 0., 0.],
                "force_on_first_xyz_n": [0., 0., 50.]} for x in (0., 1000.)]
    case = {"loads": [{"id": "self-weight/test_member", "body": "test_member", "point_xyz_mm": [500., 0., 0.],
                       "force_xyz_n": [0., 0., -100.]}],
            "equilibrium_feasibility_witness": {"feasible": True, "point_actions": actions, "compression_actions": []}}
    result = mechanics.member_sections(case, geo)[0]["sampled_extrema"]
    # Uniform load100N over1m: simply supported maximum moment W*L/8.
    assert abs(result["bending_u_nmm"]["signed_action"]) == pytest.approx(12500.)
    assert result["bending_u_nmm"]["cut_grain_station_mm"] == pytest.approx(500.)
    assert abs(result["shear_v_n"]["signed_action"]) == pytest.approx(50., abs=1e-5)


@pytest.mark.parametrize("force", [-10., 10.])
def test_tension_and_compression_springs_apply_only_on_their_own_side(force):
    group = {"B": csr_matrix([[1.], [0.], [0.]]), "ka": 100., "kl": 100., "clearance": 0., "tension_only": True}
    contact = {"B": csr_matrix([[-1.]]), "stiffness": 100., "kind": "other", "first": "body"}
    result = mechanics.compatible_contact_solve(csr_matrix((1, 1)), np.array([force]), [group], [contact], [])
    assert result["converged"]
    assert result["q"][0] == pytest.approx(force / 100.)
    assert result["connector_local_force_n"][0][0] == pytest.approx(max(force, 0.))
    assert result["normal_contact_force_n"][0] == pytest.approx(max(-force, 0.))


def test_round_radial_clearance_responds_independently_of_lateral_basis_direction():
    group = {"B": csr_matrix([[0., 0.], [1., 0.], [0., 1.]]), "ka": 100., "kl": 100.,
             "clearance": .1, "tension_only": True}
    contact = {"B": csr_matrix([[0., 0.]]), "stiffness": 1., "kind": "other", "first": "body"}
    f = np.array([3., 4.])
    result = mechanics.compatible_contact_solve(csr_matrix((2, 2)), f, [group], [contact], [])
    assert result["converged"]
    np.testing.assert_allclose(result["q"], (.1 + 5. / 100.) * f / 5., atol=1e-10)
    np.testing.assert_allclose(result["connector_local_force_n"][0][1:], f, atol=1e-10)


@pytest.mark.parametrize("displacement", [[.3, .4, -.2], [-.3, .4, -.2], [.3, .03, -.02]])
def test_radial_gap_energy_gradient_and_hessian_match_finite_differences(displacement):
    d, step = np.array(displacement), 1e-6
    force, tangent, _ = mechanics.spring_constitutive(d, 70., 110., .1, True)
    finite_force, finite_tangent = [], []
    for direction in np.eye(3):
        plus = mechanics.spring_constitutive(d + step * direction, 70., 110., .1, True)
        minus = mechanics.spring_constitutive(d - step * direction, 70., 110., .1, True)
        finite_force.append((plus[2] - minus[2]) / (2. * step))
        finite_tangent.append((plus[0] - minus[0]) / (2. * step))
    np.testing.assert_allclose(force, finite_force, rtol=1e-8, atol=1e-8)
    np.testing.assert_allclose(tangent, np.array(finite_tangent).T, rtol=1e-8, atol=1e-8)
