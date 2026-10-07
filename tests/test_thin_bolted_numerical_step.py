"""Known equilibria with inactive radial/capture modes; no whole-frame runs."""

from itertools import pairwise

import numpy as np
import pytest
from scipy.sparse import csr_matrix, vstack

from scripts import thin_bolted_common_shaft as shaft
from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_numerical_step as numerical


def inactive_fixture(shaft_force=2., radial_force=(3., 4.)):
    K = csr_matrix(np.diag([100., 100., 0., 0., 0.]))
    B = np.zeros((3, 5))
    B[1, 3], B[2, 4] = 1., 1.
    groups = [{"B": csr_matrix(B), "ka": 0., "kl": 100., "clearance": 1., "tension_only": False}]
    contacts = [{"id": "head", "kind": "shaft_end_capture", "first": "shaft", "second": "left",
                 "B": csr_matrix([[-1., 0., 1., 0., 0.]]), "stiffness": 100.},
                {"id": "nut", "kind": "shaft_end_capture", "first": "shaft", "second": "right",
                 "B": csr_matrix([[0., 1., -1., 0., 0.]]), "stiffness": 100.}]
    applied = np.array([100., -100., shaft_force, *radial_force])
    return K, applied, groups, contacts


def test_inactive_radial_and_loaded_axial_modes_traverse_to_hand_equilibrium():
    K, applied, groups, contacts = inactive_fixture()
    C = vstack([row["B"] for row in contacts])
    ck = np.array([row["stiffness"] for row in contacts])
    gradient, _, H, _, _, _ = numerical.physical_fields(K, applied, groups, C, ck, np.zeros(5), tangent=True)
    assert np.linalg.matrix_rank(H.toarray()) == 2
    assert np.linalg.norm(gradient[2:]) > 0.
    response = numerical.compatible_contact_solve(K, applied, groups, contacts, [])
    assert response["converged"]
    np.testing.assert_allclose(response["q"], [1.02, -1., 1.04, .63, .84], atol=2e-7)
    np.testing.assert_allclose(response["normal_contact_force_n"], [2., 0.], atol=1e-6)
    np.testing.assert_allclose(response["connector_local_force_n"][0], [0., 3., 4.], atol=1e-6)
    gradient, energy, _, _, _, _ = numerical.physical_fields(K, applied, groups, C, ck, response["q"])
    assert max(abs(gradient)) < frame.GENERALIZED_RESIDUAL_TOLERANCE_N
    assert energy == pytest.approx(response["potential_energy_nmm"], abs=1e-10)


def test_unloaded_floating_translations_need_no_physical_support_or_gauge():
    K, applied, groups, contacts = inactive_fixture(0., (0., 0.))
    original = K.copy()
    response = numerical.compatible_contact_solve(K, applied, groups, contacts, [])
    assert response["converged"]
    np.testing.assert_allclose(response["q"][:2], [1., -1.], atol=1e-7)
    np.testing.assert_allclose(response["normal_contact_force_n"], 0., atol=1e-10)
    np.testing.assert_allclose(K.toarray(), original.toarray())
    C = vstack([row["B"] for row in contacts])
    _, _, H, _, _, _ = numerical.physical_fields(K, applied, groups, C, np.array([100., 100.]), response["q"], tangent=True)
    assert np.linalg.matrix_rank(H.toarray()) == 2
    assert response["physical_residual_uses_unmodified_laws"]


def unequal_supported_shaft():
    K, index, _ = shaft.reduced_shaft_matrix([0., 25., 100.], 12.7, 200000., 200000. / 2.6)
    groups = []
    for node, stiffness in ((0, 500.), (2, 1000.)):
        B = np.zeros((3, K.shape[0]))
        B[1, index[node, 1]], B[2, index[node, 2]] = 1., 1.
        groups.append({"B": csr_matrix(B), "ka": 0., "kl": stiffness, "clearance": .2, "tension_only": False})
    contacts = []
    for node, sign in ((0, 1.), (2, -1.)):
        B = np.zeros((1, K.shape[0]))
        B[0, index[node, 0]] = sign
        contacts.append({"B": csr_matrix(B), "stiffness": 1000., "kind": "shaft_end_capture", "first": "shaft"})
    applied = np.zeros(K.shape[0])
    applied[index[1, 1]] = 10.
    return K, applied, groups, contacts, index


def test_unequal_two_support_shaft_conserves_force_moment_and_energy():
    K, applied, groups, contacts, index = unequal_supported_shaft()
    response = numerical.compatible_contact_solve(K, applied, groups, contacts, [])
    assert response["converged"]
    reactions = np.array([r[1] for r in response["connector_local_force_n"]])
    np.testing.assert_allclose(reactions, [7.5, 2.5], atol=1e-6)
    assert reactions.sum() == pytest.approx(10., abs=1e-6)
    assert reactions[1] * 100. == pytest.approx(10. * 25., abs=1e-4)
    np.testing.assert_allclose(response["q"][index[[0, 2], 1]], [.215, .2025], atol=1e-7)
    A, I, _ = shaft.circular_properties(12.7)
    expected = .75 * .215 + .25 * .2025 + 10. * 25.**2 * 75.**2 / (3. * 200000. * I * 100.)
    expected += 10. * 25. * 75. / (.9 * (200000. / 2.6) * A * 100.)
    assert response["q"][index[1, 1]] == pytest.approx(expected, abs=1e-7)
    C = vstack([row["B"] for row in contacts])
    gradient, energy, _, _, _, _ = numerical.physical_fields(K, applied, groups, C, np.array([1000., 1000.]), response["q"])
    assert max(abs(gradient)) < frame.GENERALIZED_RESIDUAL_TOLERANCE_N
    assert energy == pytest.approx(response["potential_energy_nmm"], abs=1e-12)


def test_physical_energy_gradient_and_hessian_are_force_duals():
    K, applied, groups, contacts = inactive_fixture()
    C, ck = vstack([row["B"] for row in contacts]), np.array([100., 100.])
    q = np.array([.9, -.8, 1.2, .8, 1.1])
    gradient, _, H, _, _, _ = numerical.physical_fields(K, applied, groups, C, ck, q, tangent=True)
    differences, columns = [], []
    for i in range(len(q)):
        step = np.eye(len(q))[i] * 1e-6
        plus = numerical.physical_fields(K, applied, groups, C, ck, q + step)
        minus = numerical.physical_fields(K, applied, groups, C, ck, q - step)
        differences.append((plus[1] - minus[1]) / 2e-6)
        columns.append((plus[0] - minus[0]) / 2e-6)
    np.testing.assert_allclose(differences, gradient, atol=2e-8)
    np.testing.assert_allclose(np.array(columns).T, H.toarray(), atol=3e-8)


def test_iteration_stop_keeps_actual_failed_iterate_separate_from_actions():
    K, applied, groups, contacts = inactive_fixture()
    response = numerical.compatible_contact_solve(K, applied, groups, contacts, [], max_iterations=1)
    assert not response["converged"]
    assert "q" not in response
    assert "connector_local_force_n" not in response
    q = response["diagnostic_last_q"]
    C = vstack([row["B"] for row in contacts])
    gradient = numerical.physical_fields(K, applied, groups, C, np.array([100., 100.]), q)[0]
    assert response["gradient_inf_n"] == pytest.approx(max(abs(gradient)))
    assert not response["diagnostic_last_q_is_a_converged_or_accepted_force_field"]


def test_accepted_steps_use_original_energy_and_no_regularized_force_credit():
    K, applied, groups, contacts = inactive_fixture()
    response = numerical.compatible_contact_solve(K, applied, groups, contacts, [])
    energies = [row["physical_potential_energy_nmm"] for row in response["iteration_history"]]
    assert all(b <= a + 1e-8 for a, b in pairwise(energies))
    assert response["maximum_transient_scaled_step_regularization"] > 0.
    assert response["generalized_residual_tolerance_n"] == 1e-5
    assert response["gradient_inf_n"] < 1e-5
