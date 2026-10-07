"""Independent analytic coupons for finite saved-field panel diagnostics."""

import copy
import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts import thin_bolted_finite_panel_consumer as consumer
from scripts import thin_bolted_finite_plate as finite
from scripts import thin_bolted_panel_mechanics as method
from scripts.check_thin_bolted_finite_panel_adapter import inputs


def mapped_panel():
    b = method.SheetBasis(1200., 800., 2)
    mapping = {"kind": "panel", "coefficient_order": consumer.MAP_ORDER, "basis_order": b.order,
        "basis_knots_normalized": b.knots.tolist(), "basis_width_mm": b.width, "basis_height_mm": b.height,
        "origin_xyz_mm": [13., -37., 51.], "axes_columns_xyz": np.diag([1., 1., -1.]).tolist(),
        "global_dof_indices": (7 + np.arange(3*b.size)).tolist(), "thickness_mm": method.CAT, "twist_scale": 1.}
    return consumer.MappedFinitePanel("kicker_left", mapping, 3*b.size+20, {"front_height_mm": b.height}, [])


def greville_points(p):
    b = p.basis
    v = np.array([np.mean(b.knots[i+1:i+4]) for i in range(b.order)])
    x, y = np.meshgrid(v*b.width, v*b.height, indexing="ij")
    return np.c_[x.ravel(), y.ravel()]


def rotate_q(p, q, rotation, translation):
    original = p.origin + greville_points(p) @ p.axes[:, :2].T
    current = original + p.local_q(q).reshape(3, p.basis.size).T @ p.axes.T
    return ((current @ rotation.T + translation - original) @ p.axes).T.ravel()


def polynomial_q(p, scale=1.):
    xy = greville_points(p)
    x, y = xy.T
    value = 1e-9*x**3 - 1e-9*x*y**2 + 2e-9*y**3 - 3e-9*x**2*y
    q = np.zeros(p.local_size)
    q[2*p.basis.size:] = scale*np.linalg.solve(p.basis.values(xy), value)
    return q


def action(p, q, source, rotation=None, translation=None, tension=1234.):
    rotation = np.eye(3) if rotation is None else rotation
    translation = np.zeros(3) if translation is None else translation
    xy = method.local_xy(source["origin_xyz_mm"], p.geometry)
    reference = p.origin + p.axes[:, :2] @ xy
    force = rotation @ (p.axes @ [45., -67., tension])
    return {"first": source["panel"], "second": source["receiver"], "director_owner": source["panel"],
        "first_port_kind": "projected_ring", "interaction_enabled": True,
        "point_on_first_xyz_mm": (rotation @ reference + translation).tolist(),
        "point_on_second_xyz_mm": (rotation @ reference + translation).tolist(),
        "current_director_xyz": (rotation @ p.axes[:, 2]).tolist(), "force_on_second_xyz_n": force.tolist(),
        "force_on_first_xyz_n": (-force).tolist(), "axial_scalar_force_n": tension,
        "moment_on_first_at_current_point_xyz_nmm": [0., 0., 0.],
        "state_id": "finite-method-coupon", "case_id": "method-coupon", "accessory_placement": "method-coupon"}


def source_axis(p):
    return {"panel": "kicker_left", "receiver": "coupon-receiver", "axis_id": "coupon-screw",
            "origin_xyz_mm": (p.origin + p.axes @ [270., 310., method.CAT/2]).tolist()}


def test_exact_uniaxial_green_strain_and_reference_resultant():
    p = mapped_panel()
    points = greville_points(p)
    stretch = .025
    q = np.zeros(p.local_size); q[:p.basis.size] = stretch*points[:, 0]
    fields = consumer.finite_fields(p, [[270., 310.], [820., 610.]], q)
    ex = stretch + .5*stretch**2
    np.testing.assert_allclose(fields["green_strain"], [[ex, 0., 0.]]*2, atol=2e-15)
    np.testing.assert_allclose(fields["covariant_curvature_per_mm"], 0., atol=2e-18)
    np.testing.assert_allclose(fields["section_conjugate_resultants"][:, 0], p.section.section_diagonal[0]*ex, rtol=2e-13)
    np.testing.assert_allclose(fields["variational_force_x_local_n_per_mm"][:, 0], p.section.section_diagonal[0]*ex*(1+stretch), rtol=2e-13)


def test_twenty_degree_rigid_motion_has_zero_finite_strain_curvature():
    p = mapped_panel()
    rotation = Rotation.from_rotvec(np.array([2., -1., 3.])/np.sqrt(14)*np.deg2rad(20)).as_matrix()
    q = rotate_q(p, np.zeros(p.local_size), rotation, [19., -21., 34.])
    f = consumer.finite_fields(p, [[270., 310.], [820., 610.]], q)
    np.testing.assert_allclose(f["green_strain"], 0., atol=2e-15)
    np.testing.assert_allclose(f["covariant_curvature_per_mm"], 0., atol=5e-18)
    np.testing.assert_allclose(f["variational_transverse_x_n_per_mm"], 0., atol=2e-10)
    np.testing.assert_allclose(f["variational_transverse_y_n_per_mm"], 0., atol=2e-10)


def test_variational_transverse_force_recovers_known_linear_Q_limit():
    p = mapped_panel(); scale = 1e-4
    q = polynomial_q(p, scale)
    f = consumer.finite_fields(p, [[413., 257.], [820., 610.]], q)
    bx, by, twist = p.section.section_diagonal[3:]
    expected_x = scale*(-bx*6e-9 + 4*twist*1e-9)
    expected_y = scale*(-by*12e-9 + 12*twist*1e-9)
    np.testing.assert_allclose(f["variational_transverse_x_n_per_mm"], expected_x, rtol=2e-8, atol=2e-10)
    np.testing.assert_allclose(f["variational_transverse_y_n_per_mm"], expected_y, rtol=2e-8, atol=2e-10)


def test_variational_force_chain_rule_matches_independent_gradient_differences():
    p = mapped_panel(); q = polynomial_q(p)
    point, h = np.array([413., 257.]), .05
    proxy = finite.FinitePlate(p.basis, p.section)

    def gradient(xy):
        return p.section.local_energy(proxy.surface_derivatives(q, xy)[0])["local_gradient"].reshape(5, 3)

    g = gradient(point)
    dx = (gradient(point+[h, 0]) - gradient(point-[h, 0]))/(2*h)
    dy = (gradient(point+[0, h]) - gradient(point-[0, h]))/(2*h)
    f = consumer.finite_fields(p, point[None], q)
    np.testing.assert_allclose(f["variational_force_x_local_n_per_mm"][0], g[0]-dx[2]-.5*dy[3], atol=3e-7, rtol=2e-7)
    np.testing.assert_allclose(f["variational_force_y_local_n_per_mm"][0], g[1]-dy[4]-.5*dx[3], atol=3e-7, rtol=2e-7)


def test_finite_warp_measures_and_transverse_force_are_objective():
    p = mapped_panel(); q = polynomial_q(p)
    rotation = Rotation.from_rotvec([.18, -.21, .15]).as_matrix()
    transformed = rotate_q(p, q, rotation, [19., -21., 34.])
    first, second = [consumer.finite_fields(p, [[413., 257.]], v) for v in (q, transformed)]
    for key in ("green_strain", "covariant_curvature_per_mm", "section_conjugate_resultants",
                "variational_transverse_x_n_per_mm", "variational_transverse_y_n_per_mm"):
        np.testing.assert_allclose(first[key], second[key], atol=2e-8, rtol=2e-9)
    local_rotation = p.axes.T @ rotation @ p.axes
    for key in ("variational_force_x_local_n_per_mm", "variational_force_y_local_n_per_mm"):
        np.testing.assert_allclose(second[key][0], local_rotation @ first[key][0], atol=2e-8, rtol=2e-9)


def test_current_rotated_force_projection_preserves_same_axis_head_lateral():
    p = mapped_panel(); source = source_axis(p)
    rotation = Rotation.from_rotvec(np.array([2., -1., 3.])/np.sqrt(14)*np.deg2rad(20)).as_matrix()
    translation = np.array([19., -21., 34.])
    q = rotate_q(p, np.zeros(p.local_size), rotation, translation)
    row = consumer.current_screw_diagnostics(p, q, source, action(p, q, source, rotation, translation))
    np.testing.assert_allclose(row["local_force_n"], [1234., 45., -67.], atol=2e-12)
    np.testing.assert_allclose(row["lateral_n"], np.hypot(45, 67), atol=2e-12)
    np.testing.assert_allclose(row["generic_head_ratio_CD1"], 1234/method.scalar_head_reference(method.CAT), rtol=2e-15)
    assert row["Hillman_product_capacity_or_stiffness_established"] is False
    assert row["director_couple_is_a_screw_or_head_capacity"] is False


@pytest.mark.parametrize("mutation", ["point", "director", "force", "host", "alias"])
def test_mixed_current_action_geometry_or_alias_is_rejected(mutation):
    p = mapped_panel(); q = np.zeros(p.local_size); source = source_axis(p)
    row = action(p, q, source)
    if mutation == "point":
        row["point_on_first_xyz_mm"][0] += 1.
    elif mutation == "director":
        row["current_director_xyz"] = [0., 1., 0.]
    elif mutation == "force":
        row["force_on_first_xyz_n"][0] += 1.
    elif mutation == "host":
        row["second"] = "other-host"
    else:
        row["axial_scalar_force_n"] += 1.
    with pytest.raises(ValueError):
        consumer.current_screw_diagnostics(p, q, source, row)


def test_two_generalized_potentials_have_exact_current_wrench_work():
    p = mapped_panel()
    q = polynomial_q(p)
    reference = np.array([0., 750., 1100.])
    rows = []
    for kind, component, amplitude in [("retained_rigid_RHS", 0, .01), ("reference_port_alignment", 2, .000001)]:
        force = np.zeros(p.local_size); force[component*p.basis.size] = amplitude
        current_coefficient_point = p.origin + p.axes @ np.r_[greville_points(p)[0], 0.]
        current_coefficient_point += p.axes @ q.reshape(3, p.basis.size)[:, 0]
        spatial_force = p.axes[:, component]*amplitude
        wrench = np.r_[spatial_force, np.cross(current_coefficient_point-reference, spatial_force)]
        rows.append({"panel": "kicker_left", "kind": kind, "global_coefficient_indices": p.indices.tolist(),
                     "local_generalized_force_n": force.tolist(), "current_equivalent_rigid_wrench_n_nmm": wrench.tolist(),
                     "wrench_reference_xyz_mm": reference.tolist(), "physical_point_forces_or_pressure_representation": False})
    answer = consumer.correction_diagnostics(p, q, rows)
    np.testing.assert_allclose(answer["sum_potential_nmm"], -sum(np.array(r["local_generalized_force_n"])@q for r in rows), atol=1e-18)
    assert answer["physical_forces_assigned"] is False
    bad = copy.deepcopy(rows); bad[0]["current_equivalent_rigid_wrench_n_nmm"][3] += .1
    with pytest.raises(ValueError, match="current wrench differs"):
        consumer.correction_diagnostics(p, q, bad)
    with pytest.raises(ValueError, match="two unique"):
        consumer.correction_diagnostics(p, q, rows[:1])


def test_map_only_consumer_cannot_reassemble_stiffness_or_loads():
    p = mapped_panel()
    with pytest.raises(ValueError, match="cannot assemble"):
        p.response(np.zeros(p.local_size))
    with pytest.raises(ValueError, match="without reconstructing"):
        p.prepare_case_load(None, None, None, None)


def test_section_indices_remain_resolution_and_material_diagnostics():
    p = mapped_panel()
    p.panel["holes"] = [{"xy_mm": [400., 300.], "diameter_mm": 5., "kind": "conditional_screw_clearance"}]
    report = consumer.section_diagnostics(p, polynomial_q(p), 5)
    assert report["finite_plywood_constitutive_or_local_hole_capacity_qualified"] is False
    assert report["sampling_or_response_convergence_established"] is False
    assert report["maximum_thickness_times_abs_principal_curvature"] > 0
    assert len(report["section_witnesses"]) == 6


def test_mass_only_admission_utility_matches_saved_source_operator_and_alignment():
    panels, state, integrated, _ = inputs()
    p = panels["main_upper_left"]
    b, g = p["basis"], p["geometry"]
    mapping = {"kind": "panel", "coefficient_order": consumer.MAP_ORDER, "basis_order": b.order,
        "basis_knots_normalized": b.knots.tolist(), "basis_width_mm": b.width, "basis_height_mm": b.height,
        "origin_xyz_mm": g["origin"].tolist(), "axes_columns_xyz": g["axes"].tolist(),
        "global_dof_indices": list(range(3*b.size)), "thickness_mm": method.CAT, "twist_scale": 1.}
    mapped = consumer.MappedFinitePanel("main_upper_left", mapping, 3*b.size,
                                      {"front_height_mm": g["front_height"]}, p["holes"])
    value = consumer.reconstruct_load_corrections(mapped, "a12-rear", "original_top", integrated, state["body_applied_loads"])
    np.testing.assert_allclose(abs(value["reference_port_alignment"]).max(), 4.02364321416826e-7, atol=2e-13)
    np.testing.assert_allclose(np.linalg.norm(value["retained_rigid_RHS"]), 1.5662083167572513e-5, rtol=2e-8)
    assert abs(value["mass_coefficient_row"].sum()-1) < 2e-14
    assert mapped.measure["mass_weights"].shape[0] > 0
    with pytest.raises(ValueError, match="cannot assemble"):
        mapped.response(np.zeros(mapped.local_size))


def test_failed_new_admission_prevents_field_consumption(tmp_path, monkeypatch):
    field = tmp_path/"finite.json"
    field.write_text(json.dumps({"schema": consumer.FIELD_SCHEMA}))
    expected_sha = "1"*64
    original_sha = method.sha
    monkeypatch.setattr(method, "sha", lambda path: expected_sha if path == consumer.ADMISSION_PATH else original_sha(path))
    fake = SimpleNamespace(__file__=str(consumer.ADMISSION_PATH), audit_finite_state=lambda _: {consumer.ADMISSION_KEY: False})
    monkeypatch.setattr(consumer.importlib, "import_module", lambda _: fake)
    with pytest.raises(ValueError, match="admission failed"):
        consumer.evaluate(field, admission_sha256=expected_sha)


@pytest.mark.parametrize("pin", [None, "", "wrong", "0"*63, "g"*64])
def test_missing_or_malformed_new_gate_pin_is_rejected(tmp_path, pin):
    path = tmp_path/"finite.json"; path.write_text(json.dumps({"schema": consumer.FIELD_SCHEMA}))
    with pytest.raises(ValueError, match="explicit frozen"):
        consumer.evaluate(path, admission_sha256=pin)


def test_gate_receipt_binds_its_source_and_exact_state_field_identity():
    state = {"state_id": "finite-coupon", "case_id": "coupon", "accessory_placement": "original_top"}
    pin, field_sha = "1"*64, "2"*64
    receipt = {consumer.ADMISSION_KEY: True, **state, "field_sha256": field_sha,
               "source_sha256": {str(consumer.ADMISSION_PATH.relative_to(method.ROOT)): pin}}
    consumer.validate_admission_receipt(receipt, state, field_sha, pin)
    wrong_state = copy.deepcopy(receipt); wrong_state["case_id"] = "other"
    with pytest.raises(ValueError, match="another field/state/case"):
        consumer.validate_admission_receipt(wrong_state, state, field_sha, pin)
    with pytest.raises(ValueError, match="audit-source"):
        consumer.validate_admission_receipt(receipt, state, field_sha, "3"*64)


def test_gate_and_consumer_use_one_immutable_field_payload(tmp_path, monkeypatch):
    state = {"schema": consumer.FIELD_SCHEMA, "state_id": "finite-coupon", "case_id": "coupon",
        "accessory_placement": "original_top", "source_sha256": {}, "release": {"fabrication": False},
        "response": {"q": [1.]}, "finite_kinematic_map": {"ndof": 1, "panels": {}}}
    payload = json.dumps(state).encode()
    field = tmp_path/"finite.json"; field.write_bytes(payload)
    pin = "1"*64; original_sha = method.sha
    monkeypatch.setattr(method, "sha", lambda path: pin if path == consumer.ADMISSION_PATH else original_sha(path))
    selected = []

    def gate(immutable):
        assert isinstance(immutable, bytes) and immutable == payload
        changed = copy.deepcopy(state); changed["response"]["q"] = [2.]
        field.write_text(json.dumps(changed))
        return {consumer.ADMISSION_KEY: True, **{k: state[k] for k in ("state_id", "case_id", "accessory_placement")},
            "field_sha256": hashlib.sha256(immutable).hexdigest(),
            "source_sha256": {str(consumer.ADMISSION_PATH.relative_to(method.ROOT)): pin}}

    original_asarray = np.asarray

    def observe(value, *args, **kwargs):
        if value == [1.]:
            selected.append(value)
        return original_asarray(value, *args, **kwargs)

    fake = SimpleNamespace(__file__=str(consumer.ADMISSION_PATH), audit_finite_state=gate)
    monkeypatch.setattr(consumer.importlib, "import_module", lambda _: fake)
    monkeypatch.setattr(consumer.np, "asarray", observe)
    with pytest.raises(ValueError, match="q/six-panel"):
        consumer.evaluate(field, admission_sha256=pin)
    assert selected == [[1.]]


def test_nonfinite_old_fields_are_rejected_before_new_gate_import(tmp_path, monkeypatch):
    path = tmp_path/"old-reference-field.json"
    path.write_text(json.dumps({"schema": "thin_bolted_frame_response/v1"}))

    def fail_import(*args):
        raise AssertionError("reference field reached finite admission importer")

    monkeypatch.setattr(consumer.importlib, "import_module", fail_import)
    with pytest.raises(ValueError, match="reference state rejected"):
        consumer.evaluate(path)
