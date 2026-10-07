"""Observable coupons for sparse integration, finite ports and constant loads."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts import thin_bolted_finite_panel_adapter as adapter
from scripts import thin_bolted_finite_plate as finite
from scripts import thin_bolted_panel_mechanics as method
from scripts.check_thin_bolted_finite_panel_adapter import inputs


def panel(bevel=True):
    basis = method.SheetBasis(450., 390., 2)
    return {"basis": basis, "geometry": {"name": "kicker_left", "origin": np.array([13., -37., 51.]),
            "axes": np.diag([1., 1., -1.]), "front_height": 330. if bevel else 390.},
            "thickness": method.CAT, "twist_scale": 1., "holes": [
                {"kind": "conditional_screw_clearance", "xy_mm": [120., 140.], "diameter_mm": 5.},
                {"kind": "hold_tnut", "xy_mm": [230., 180.], "diameter_mm": 11.1125}]}


def screw(p):
    geometry = p["geometry"]
    return {"panel": "kicker_left", "axis_id": "coupon-screw", "receiver": "coupon-wood",
            "origin_xyz_mm": geometry["origin"] + geometry["axes"] @ [120., 140., method.CAT / 2]}


def world_point(a, xy, z):
    return a.origin + a.axes @ np.r_[xy, z]


def rigid_q(a, rotation, translation):
    basis = a.basis
    greville = np.array([np.mean(basis.knots[i + 1:i + 4]) for i in range(basis.order)])
    x, y = np.meshgrid(greville * basis.width, greville * basis.height, indexing="ij")
    original = a.origin + np.c_[x.ravel(), y.ravel()] @ a.axes[:, :2].T
    displacement = original @ rotation.T + translation - original
    return (displacement @ a.axes).T.ravel()


def linear_reference(p):
    b = p["basis"]
    xy, w = b.quadrature()
    k = method.plate_matrix(b, xy, w) - method.aperture_matrix(b, p["holes"], p["thickness"])[0]
    xy, w, remaining = method.bevel_quadrature(b, p["geometry"]["front_height"])
    if len(w):
        membrane = method.plate_matrix(b, xy, w * (1 - remaining))
        bending = method.plate_matrix(b, xy, w * (1 - remaining**3))
        n = 2 * b.size
        k[:n, :n] -= membrane[:n, :n]; k[n:, n:] -= bending[n:, n:]
    return k


@pytest.mark.parametrize("bevel", [False, True])
def test_reference_tangent_matches_frozen_aperture_and_bevel_energy(bevel):
    p = panel(bevel)
    a = adapter.FinitePanelAdapter(p)
    answer = a.response(np.zeros(a.local_size))
    assert answer["energy_nmm"] == 0
    assert np.linalg.norm(answer["gradient_n"]) == 0
    np.testing.assert_allclose(answer["hessian_csr"].toarray(), linear_reference(p), rtol=2e-12, atol=2e-10)


def test_sparse_global_embedding_preserves_unrelated_coefficients():
    p = panel()
    indices = 7 + 2 * np.arange(3 * p["basis"].size)
    a = adapter.FinitePanelAdapter(p, indices, ndof=int(indices[-1]) + 9)
    local = np.linspace(-.08, .11, a.local_size)
    whole = np.full(a.ndof, 123.); whole[indices] = local
    first, second = a.response(local), a.response(whole)
    assert first["energy_nmm"] == second["energy_nmm"]
    np.testing.assert_array_equal(first["gradient_n"], second["gradient_n"])
    outside = np.setdiff1d(np.arange(a.ndof), indices)
    assert np.count_nonzero(first["gradient_n"][outside]) == 0
    assert first["hessian_csr"][outside].nnz == 0


def test_integrated_gradient_and_full_tangent_by_central_directions():
    a = adapter.FinitePanelAdapter(panel())
    rng = np.random.default_rng(352)
    q = rng.normal(0, .1, a.local_size)
    direction = rng.normal(size=a.local_size); direction /= np.linalg.norm(direction)
    answer = a.response(q)
    h = 1e-4
    plus, minus = a.response(q + h * direction, False), a.response(q - h * direction, False)
    np.testing.assert_allclose((plus["energy_nmm"] - minus["energy_nmm"]) / (2 * h),
                               answer["gradient_n"] @ direction, rtol=2e-7, atol=1e-6)
    np.testing.assert_allclose((plus["gradient_n"] - minus["gradient_n"]) / (2 * h),
                               answer["hessian_csr"] @ direction, rtol=2e-7, atol=1e-6)


def test_exact_world_point_and_normal_jets_match_frozen_local_primitive():
    a = adapter.FinitePanelAdapter(panel())
    q = np.linspace(-.1, .15, a.local_size)
    xy, z = np.array([210., 185.]), method.CAT / 2 + 100.
    answer = a.point_port(q, world_point(a, xy, z))
    expected = finite.FinitePlate(a.basis).point_port(q, xy, z,
        origin_xyz_mm=a.origin, axes_columns_xyz=a.axes)
    np.testing.assert_allclose(answer["position_xyz_mm"], expected["position_xyz_mm"], atol=1e-12)
    np.testing.assert_allclose(answer["J_csr"].toarray(), expected["jacobian_xyz_per_coefficient"], atol=1e-13)
    for i in range(3):
        np.testing.assert_allclose(answer["H_xyz_csr"][i].toarray(), expected["hessian_xyz_per_coefficient_squared"][i], atol=1e-13)
    assert abs(answer["outward_offset_mm"] - 109.128125) < 1e-12


def test_reference_screw_jacobian_retains_point_lateral_and_annular_axial():
    p = panel(); a = adapter.FinitePanelAdapter(p)
    answer = a.screw_port(np.zeros(a.local_size), screw(p))
    xy = np.array([120., 140.])
    u, v, w = method.port_rows(a.basis, xy[None])
    ring, area = method.disk_quadrature(xy, 4.5, inner=2.5)
    w[0, 2*a.basis.size:] = area @ a.basis.values(ring) / area.sum()
    expected = a.axes @ np.vstack([u[0], v[0], w[0]])
    np.testing.assert_allclose(answer["J_csr"].toarray(), expected, rtol=2e-13, atol=2e-14)
    assert abs(answer["ring_projected_area_mm2"] - np.pi * (4.5**2 - 2.5**2)) < 1e-12


def test_twenty_degree_common_motion_is_unstrained_and_all_ports_transform():
    p = panel(); a = adapter.FinitePanelAdapter(p)
    rotation = Rotation.from_rotvec(np.array([2., -1., 3.]) / np.sqrt(14.) * np.deg2rad(20.)).as_matrix()
    translation = np.array([19., -21., 34.])
    q = rigid_q(a, rotation, translation)
    answer = a.response(q, False)
    assert answer["energy_nmm"] < 1e-18
    assert np.linalg.norm(answer["gradient_n"]) < 1e-8
    ports = [a.point_port(q, world_point(a, [210., 185.], -method.CAT/2)),
             a.point_port(q, world_point(a, [210., 185.], method.CAT/2+100)),
             a.point_port(q, world_point(a, [-1.5875, 260.], -method.CAT/2), allow_edge_extension=True),
             a.screw_port(q, screw(p))]
    for port in ports:
        np.testing.assert_allclose(port["position_xyz_mm"], rotation @ port["reference_position_xyz_mm"] + translation, atol=2e-12)
        np.testing.assert_allclose(port["normal_xyz"], rotation @ a.axes[:, 2], atol=2e-14)


def test_projected_ring_jacobian_hessian_and_spatial_force_dual():
    p = panel(); a = adapter.FinitePanelAdapter(p)
    rng = np.random.default_rng(353)
    q = rng.normal(0, .2, a.local_size)
    direction = rng.normal(size=a.local_size); direction /= np.linalg.norm(direction)
    port = a.screw_port(q, screw(p))
    h = 1e-4
    plus, minus = a.screw_port(q+h*direction, screw(p)), a.screw_port(q-h*direction, screw(p))
    np.testing.assert_allclose((plus["position_xyz_mm"]-minus["position_xyz_mm"])/(2*h),
                               port["J_csr"] @ direction, atol=5e-10, rtol=2e-7)
    numerical = (plus["J_csr"] - minus["J_csr"])/(2*h)
    expected = np.vstack([matrix @ direction for matrix in port["H_xyz_csr"]])
    np.testing.assert_allclose(numerical.toarray(), expected, atol=2e-11, rtol=2e-7)
    force, reference = np.array([17., -26., 33.]), np.array([11., 21., 37.])
    dual = np.asarray(port["J_csr"].T @ force)
    wrench = a.current_rigid_modes(q, reference).T @ dual
    np.testing.assert_allclose(wrench, np.r_[force, np.cross(port["position_xyz_mm"]-reference, force)], atol=1e-9)
    rotation_derivative = port["normal_J_csr"] @ a.current_rigid_modes(q, reference)
    expected_normal = np.c_[np.zeros((3, 3)), np.column_stack([np.cross(e, port["normal_xyz"]) for e in np.eye(3)])]
    np.testing.assert_allclose(rotation_derivative, expected_normal, atol=1e-12)


def test_nonzero_warp_energy_and_projected_ring_are_objective():
    p = panel(); a = adapter.FinitePanelAdapter(p)
    rng = np.random.default_rng(354)
    q = rng.normal(0, .2, a.local_size)
    rotation = Rotation.from_rotvec(np.array([.18, -.21, .15])).as_matrix()
    translation = np.array([19., -21., 34.])
    rigid = rigid_q(a, rotation, translation).reshape(3, a.basis.size)
    changed = (rigid + (a.axes.T @ rotation @ a.axes) @ q.reshape(3, a.basis.size)).ravel()
    first, second = a.response(q, False), a.response(changed, False)
    np.testing.assert_allclose(second["energy_nmm"], first["energy_nmm"], rtol=2e-12)
    first_port, second_port = a.screw_port(q, screw(p)), a.screw_port(changed, screw(p))
    np.testing.assert_allclose(second_port["position_xyz_mm"], rotation @ first_port["position_xyz_mm"] + translation, atol=2e-12)
    np.testing.assert_allclose(second_port["normal_xyz"], rotation @ first_port["normal_xyz"], atol=2e-14)


def test_constant_world_force_port_potential_gradient_tangent():
    a = adapter.FinitePanelAdapter(panel())
    q = np.linspace(-.2, .11, a.local_size)
    point, force = world_point(a, [210., 185.], -22.), np.array([0., 0., -123.])
    direction = np.sin(np.arange(a.local_size)); direction /= np.linalg.norm(direction)
    port = a.point_port(q, point)
    gradient = -np.asarray(port["J_csr"].T @ force)
    tangent = -sum((f * matrix for f, matrix in zip(force, port["H_xyz_csr"], strict=True)))
    h = 1e-4
    plus, minus = a.point_port(q+h*direction, point), a.point_port(q-h*direction, point)
    numerical_energy_gradient = -force @ (plus["position_xyz_mm"]-minus["position_xyz_mm"])/(2*h)
    np.testing.assert_allclose(numerical_energy_gradient, gradient @ direction, rtol=1e-7, atol=1e-7)
    numerical_tangent = -np.asarray((plus["J_csr"]-minus["J_csr"]).T @ force)/(2*h)
    np.testing.assert_allclose(numerical_tangent, tangent @ direction, rtol=2e-7, atol=1e-8)


def test_saved_reference_alignment_preserves_rhs_and_separate_wrench_work():
    panels, state, integrated, pins = inputs()
    a = adapter.FinitePanelAdapter(panels["main_upper_left"], source_sha256=pins)
    case = next(r for r in method.load_cases(integrated) if r["id"] == state["case_id"])
    loads = a.prepare_case_load(case, integrated, "original_top", state["body_applied_loads"])
    zero = loads.external(np.zeros(a.local_size))
    np.testing.assert_allclose(-zero["local_gradient_n"], loads.corrected_reference_force_n, atol=2e-13)
    assert 1e-8 < abs(loads.reference_port_alignment_correction_n).max() < 1e-5
    original_rigid = adapter.diagnostics.rhs_correction(adapter.diagnostics.rigid_modes(a.panel),
        loads.uncorrected_reference_force_n, adapter.diagnostics.load_wrench(loads.loads))[0]
    np.testing.assert_array_equal(loads.retained_rigid_correction_n, original_rigid)
    q = np.linspace(-.12, .09, a.local_size)
    answer = loads.external(q)
    np.testing.assert_allclose(answer["reference_port_alignment_potential_nmm"],
                               -loads.reference_port_alignment_correction_n @ q, atol=1e-18)
    np.testing.assert_allclose(answer["generalized_correction_wrench_n_nmm"],
                               answer["retained_rigid_correction_wrench_n_nmm"] + answer["reference_port_alignment_wrench_n_nmm"], atol=1e-12)
    assert np.linalg.norm(answer["wrench_residual_n_nmm"][:3]) < 2e-6
    assert np.linalg.norm(answer["wrench_residual_n_nmm"][3:]) < 2e-3


def test_outside_ports_invalid_indices_and_changed_sources_are_rejected():
    p = panel(); a = adapter.FinitePanelAdapter(p)
    with pytest.raises(ValueError, match="outside panel"):
        a.point_port(np.zeros(a.local_size), world_point(a, [-3., 10.], 0.), allow_edge_extension=True)
    with pytest.raises(ValueError, match="distinct nonnegative"):
        adapter.FinitePanelAdapter(p, np.zeros(a.local_size, dtype=int))
    with pytest.raises(ValueError, match="contradictory"):
        adapter.FinitePanelAdapter(p, source_sha256={"scripts/thin_bolted_finite_plate.py": "changed"})
