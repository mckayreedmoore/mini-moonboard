"""Independent support-mask coupon with off-center world-point force arms."""

import numpy as np
from scipy.sparse import csr_matrix

from scripts import thin_bolted_support_state_search as search


def point_port(point, center, direction, body):
    """Virtual work for world translations and1000-scaled world rotations."""
    row = np.zeros((1, 12))
    row[0, 6 * body:6 * body + 3] = direction
    row[0, 6 * body + 3:6 * body + 6] = np.cross(point - center, direction) / 1000.
    return csr_matrix(row)


def test_off_center_floor_ports_recover_the_hand_branch_and_own_force_moments():
    """Two tiny synthetic bodies; no candidate or native solver is evaluated."""
    centers = [np.array([0., 0., 50.]), np.array([100., 0., 50.])]
    # This positive diagonal is a synthetic material block, not a floor law.
    K = csr_matrix(np.diag([10., 10., 10., 100., 100., 100.] * 2))
    applied = np.array([3., 2., -100., .002, -.001, 0.,
                        3., 2., 100., .002, -.001, 0.])
    contacts, tangents = [], []
    corners = ((-10., -10.), (-10., 10.), (10., -10.), (10., 10.))
    for body, (host, center) in enumerate(zip(("foot-A", "foot-B"), centers, strict=True)):
        for corner, (x, y) in enumerate(corners):
            point = np.array([center[0] + x, y, 0.])
            contacts.append({
                "id": host + f"/floor-{corner}", "kind": "floor_normal", "first": host,
                "second": "floor", "point": point,
                "B": point_port(point, center, np.array([0., 0., -1.]), body),
                "stiffness": 25000.,
            })
        for component in (0, 1):
            point = np.array([center[0], 0., 0.])
            tangents.append({
                "id": host + f"/no-slip-{component}", "kind": "floor_tangent", "first": host,
                "point": point, "B": point_port(point, center, np.eye(3)[component], body),
                "stiffness": 100000.,
            })

    response = search.compatible_contact_solve(K, applied, [], contacts, tangents, mask_budget=4)
    assert response["converged"]
    assert response["nonbearing_no_slip_removed"] == ["foot-B"]
    assert [row["mask_id"] for row in response["support_state_search_v1"]["tested_masks"]] == [
        "centroid-mask-11", "centroid-mask-10",
    ]

    # The exact accepted branch has A's four normals and two XY rows, with
    # all B floor rows inactive. Its hand matrix is independent of the search.
    matrix = K.toarray()
    for row in contacts[:4] + tangents[:2]:
        B = row["B"].toarray()
        matrix += row["stiffness"] * B.T @ B
    expected = np.linalg.solve(matrix, applied)
    assert all(float((row["B"] @ expected)[0]) > 0. for row in contacts[:4])
    assert all(float((row["B"] @ expected)[0]) < 0. for row in contacts[4:])
    actual = np.asarray(response["q"])
    tolerance = response["generalized_residual_tolerance_n"]
    # A residual bound gives a state error bound using this known SPD branch.
    q_bound = tolerance / float(np.linalg.eigvalsh(matrix).min())
    np.testing.assert_allclose(actual, expected, rtol=0., atol=q_bound)

    generalized = np.zeros(12)
    for row, scalar in zip(contacts, response["normal_contact_force_n"], strict=True):
        body = 0 if row["first"] == "foot-A" else 1
        force = np.array([0., 0., scalar])
        moment = np.cross(row["point"] - centers[body], force)
        own_wrench = np.r_[force, moment / 1000.]
        generalized[body * 6:body * 6 + 6] += own_wrench
        recovered = np.asarray(-row["B"].T @ np.array([scalar])).ravel()
        np.testing.assert_allclose(recovered[body * 6:body * 6 + 6], own_wrench, atol=1e-12)
    np.testing.assert_array_equal(response["normal_contact_force_n"][4:], np.zeros(4))
    for row in tangents[:2]:
        component = int(row["id"][-1])
        scalar = -row["stiffness"] * float((row["B"] @ actual)[0])
        force = scalar * np.eye(3)[component]
        moment = np.cross(row["point"] - centers[0], force)
        generalized[:6] += np.r_[force, moment / 1000.]

    # Original springs at their world points give the same generalized force
    # as independent force and reference-arm moment recovery.
    residual = K @ actual - applied - generalized
    assert float(np.max(abs(residual))) < tolerance == 1e-5
