"""Known answers for finite CURRENT timber cut and section-frame recovery."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from scripts import thin_bolted_timber_finite_checks as finite


def mapped_coupon(rotation=None, translation=None):
    rotation = np.eye(3) if rotation is None else np.asarray(rotation)
    translation = np.zeros(3) if translation is None else np.asarray(translation)
    from scripts.thin_bolted_finite_mechanics import so3_log

    centers = np.array([[0., 0., 0.], [100., 0., 0.]])
    q = np.zeros((2, 6))
    q[:, :3] = centers @ rotation.T + translation - centers
    q[:, 3:] = so3_log(rotation) * 1000.
    mapping = {"ndof": 12, "panels": {}, "mechanical_bodies": {"wood": {
        "kind": "timber", "node_reference_centers_xyz_mm": centers.tolist(),
        "node_dof_indices": np.arange(12).reshape(2, 6).tolist(), "storage_basis_columns_xyz": np.eye(3).tolist(),
        "reference_start_xyz_mm": [0., 0., 0.], "reference_axis_xyz": [1., 0., 0.], "reference_stations_mm": [0., 100.]}}}
    return mapping, q.ravel().tolist()


def action(point, force, *, moment=None, current=None, name="load"):
    return {"id": name, "reference_point_xyz_mm": point, "current_point_xyz_mm": point if current is None else current,
        "force_xyz_n": force, "free_spatial_moment_xyz_nmm": [0., 0., 0.] if moment is None else moment}


def test_current_cut_frame_rigidly_transports_exact_centroid_and_material_basis():
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    translation = [5., -3., 2.]
    mapping, q = mapped_coupon(rotation, translation)
    frame = finite.current_cut_frame(mapping, "wood", [50., 0., 0.], [1., 0., 0.], q,
                                     reference_centroid=[50., 10., 4.])
    assert frame["current_cut_point_xyz_mm"] == pytest.approx([5., 47., 2.])
    assert frame["current_finished_section_centroid_xyz_mm"] == pytest.approx([-5., 47., 6.])
    assert np.asarray(frame["current_basis_u_v_grain_xyz"]) == pytest.approx(
        np.array([[-1., 0., 0.], [0., 0., 1.], [0., 1., 0.]]), abs=1e-12)


def test_deformed_cut_centroid_uses_current_center_and_geodesic_material_director():
    mapping, q = mapped_coupon()
    q = np.asarray(q).reshape(2, 6)
    q[1, :3] = [-10., 20., 0.]
    q[:, 5] = np.deg2rad([30., 50.]) * 1000.
    frame = finite.current_cut_frame(mapping, "wood", [50., 0., 0.], [1., 0., 0.], q.ravel().tolist(),
                                     reference_centroid=[50., 10., 4.])
    angle = np.deg2rad(40.)
    assert frame["current_cut_point_xyz_mm"] == pytest.approx([45., 10., 0.])
    assert frame["current_finished_section_centroid_xyz_mm"] == pytest.approx(
        [45. - 10. * np.sin(angle), 10. + 10. * np.cos(angle), 4.])
    assert frame["current_basis_u_v_grain_xyz"][2] == pytest.approx([np.cos(angle), np.sin(angle), 0.])


def test_same_material_cut_spatial_wrench_is_objective_under_superposed_rotation():
    mapping, q = mapped_coupon()
    frame = finite.current_cut_frame(mapping, "wood", [50., 0., 0.], [1., 0., 0.], q)
    loads = [action([25., 10., 0.], [-10., 20., 30.], moment=[2., 3., 4.]),
             action([60., 0., 0.], [999., 888., 777.], name="upper")]
    reference = finite.current_cut_wrench(loads, [1., 0., 0.], 50., frame)
    assert reference["force_on_lower_material_portion_xyz_n"] == pytest.approx([10., -20., -30.])
    assert reference["moment_on_lower_material_portion_about_current_cut_xyz_nmm"] == pytest.approx([-302., -753., 396.])
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    translation = [5., -3., 2.]
    mapping, q = mapped_coupon(rotation, translation)
    moved_frame = finite.current_cut_frame(mapping, "wood", [50., 0., 0.], [1., 0., 0.], q)
    moved = [action(row["reference_point_xyz_mm"], (rotation @ row["force_xyz_n"]).tolist(),
        current=(rotation @ row["current_point_xyz_mm"] + translation).tolist(),
        moment=(rotation @ row["free_spatial_moment_xyz_nmm"]).tolist(), name=row["id"]) for row in loads]
    result = finite.current_cut_wrench(moved, [1., 0., 0.], 50., moved_frame)
    assert result["own_lower_material_action_ids"] == ["load"]
    assert result["force_on_lower_material_portion_xyz_n"] == pytest.approx(rotation @ reference["force_on_lower_material_portion_xyz_n"])
    assert result["moment_on_lower_material_portion_about_current_cut_xyz_nmm"] == pytest.approx(rotation @ reference["moment_on_lower_material_portion_about_current_cut_xyz_nmm"])
    assert result["local_Vu_Vv_N_TensionPositive_n"] == pytest.approx(reference["local_Vu_Vv_N_TensionPositive_n"])
    assert result["local_Mu_Mv_T_nmm"] == pytest.approx(reference["local_Mu_Mv_T_nmm"])
    # Both moved points have globalX=5 or-5; selecting by currentX would
    # include the upper material load. The consumer uses source materialX.
    assert result["current_point_projection_used_to_select_material_side"] is False


def test_each_side_retains_own_current_point_and_director_induced_spatial_couple():
    identity = {"state_id": "method", "case_id": "C", "accessory_placement": "rear"}
    row = {**identity, "id": "port", "kind": "shaft_end_capture", "first": "shaft", "second": "wood",
        "reference_first_point_xyz_mm": [1., 0., 0.], "reference_second_point_xyz_mm": [2., 0., 0.],
        "point_on_first_xyz_mm": [10., 3., 0.], "point_on_second_xyz_mm": [11., 5., 0.],
        "force_on_first_xyz_n": [-5., 0., 0.], "force_on_second_xyz_n": [5., 0., 0.],
        "moment_on_first_at_current_point_xyz_nmm": [0., 0., 0.],
        "moment_on_second_at_current_point_xyz_nmm": [0., 0., -10.]}
    demand = {**identity, "finite_interaction_actions": [row], "finite_body_applied_loads": []}
    own = finite.own_current_actions(demand)
    assert own["wood"][0]["current_point_xyz_mm"] == [11., 5., 0.]
    assert own["shaft"][0]["current_point_xyz_mm"] == [10., 3., 0.]
    assert own["wood"][0]["free_spatial_moment_xyz_nmm"] == [0., 0., -10.]
    changed = copy.deepcopy(demand)
    changed["finite_interaction_actions"][0]["case_id"] = "mixed"
    with pytest.raises(ValueError, match="admitted state/case"):
        finite.own_current_actions(changed)
    changed = copy.deepcopy(demand)
    changed["finite_interaction_actions"][0]["force_on_second_xyz_n"][0] = 6.
    with pytest.raises(ValueError, match="dual"):
        finite.own_current_actions(changed)


def test_saved_gauss_gravity_is_discrete_and_cut_station_tie_belongs_to_upper_side():
    mapping, q = mapped_coupon()
    frame = finite.current_cut_frame(mapping, "wood", [50., 0., 0.], [1., 0., 0.], q)
    loads = [action([20., 0., 0.], [0., 0., -7.], name="gauss0"),
        action([80., 0., 0.], [0., 0., -13.], name="gauss1"),
        action([50., 0., 0.], [999., 0., 0.], name="at-cut")]
    wrench = finite.current_cut_wrench(loads, [1., 0., 0.], 50., frame)
    assert wrench["own_lower_material_action_ids"] == ["gauss0"]
    assert wrench["force_on_lower_material_portion_xyz_n"] == pytest.approx([0., 0., 7.])
    assert wrench["moment_on_lower_material_portion_about_current_cut_xyz_nmm"] == pytest.approx([0., 210., 0.])
    assert wrench["old_affine_continuous_force_integral_substituted"] is False


def test_current_net_centroid_transport_recovers_uniform_axial_stress():
    mapping, q = mapped_coupon()
    frame = finite.current_cut_frame(mapping, "wood", [50., 0., 0.], [1., 0., 0.], q,
                                     reference_centroid=[50., 10., 4.])
    wrench = {**frame, "force_on_lower_material_portion_xyz_n": [1000., 0., 0.],
        "moment_on_lower_material_portion_about_current_cut_xyz_nmm": [0., 4000., -10000.],
        "local_Vu_Vv_N_TensionPositive_n": [0., 0., 1000.]}
    properties = {"centroidal_area_moment_matrix_uv_mm4": [[10000., 1000.], [1000., 20000.]], "finished_area_mm2": 100.,
        "basis_u_v_grain_xyz": [[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]]}
    result = finite.centroid_components(wrench, properties)
    assert result["moment_about_current_finished_centroid_xyz_nmm"] == pytest.approx([0., 0., 0.])
    assert result["mean_axial_normal_stress_n_mm2"] == 10.
    assert result["linear_normal_stress_gradient_uv_n_mm3"] == pytest.approx([0., 0.])
    assert result["actual_trimmed_boundary_normal_stress_extrema"] is None


def test_net_cross_inertia_and_material_basis_are_not_aliased():
    mapping, q = mapped_coupon()
    frame = finite.current_cut_frame(mapping, "wood", [50., 0., 0.], [1., 0., 0.], q,
                                     reference_centroid=[50., 0., 0.])
    matrix = np.array([[10000., 1000.], [1000., 20000.]])
    # beta=(2,-3), so [-Mv,Mu]=H*beta=(17000,-58000).
    wrench = {**frame, "force_on_lower_material_portion_xyz_n": [0., 0., 0.],
        "moment_on_lower_material_portion_about_current_cut_xyz_nmm": [0., -58000., -17000.],
        "local_Vu_Vv_N_TensionPositive_n": [0., 0., 0.]}
    props = {"centroidal_area_moment_matrix_uv_mm4": matrix.tolist(), "finished_area_mm2": 100.,
             "basis_u_v_grain_xyz": frame["reference_basis_u_v_grain_xyz"]}
    assert finite.centroid_components(wrench, props)["linear_normal_stress_gradient_uv_n_mm3"] == pytest.approx([2., -3.])
    changed = dict(props, basis_u_v_grain_xyz=[[0., 0., 1.], [0., 1., 0.], [-1., 0., 0.]])
    with pytest.raises(ValueError, match="inertia basis"):
        finite.centroid_components(wrench, changed)


def test_own_finite_capture_retains_current_pressure_and_support_and_couple():
    identity = {"state_id": "method", "case_id": "C", "accessory_placement": "rear"}
    row = {"id": "axis/head-capture", "kind": "shaft_end_capture", "second": "wood",
        "source_descriptor": {"axis_id": "axis", "end": {"end": "head"}},
        "point_on_first_xyz_mm": [5., 6., 7.], "point_on_second_xyz_mm": [8., 9., 10.],
        "force_on_second_xyz_n": [3., 4., 0.], "moment_on_second_at_current_point_xyz_nmm": [0., 0., 12.],
        "axial_scalar_force_n": 5.}
    packet = {"washer_wood_interface_references": [{"axis_id": "axis", "role": "head_washer", "support_material": "wood",
        "ideal_full_contact_wood_annulus_reference_n": 10.}]}
    result = finite.current_capture_annuli({**identity, "finite_interaction_actions": [row]}, packet)[0]
    assert result["own_model_capture_over_ideal_annulus_component_ratio"] == .5
    assert result["current_host_support_point_xyz_mm"] == [8., 9., 10.]
    assert result["current_shaft_pressure_point_xyz_mm"] == [5., 6., 7.]
    assert result["own_current_director_spatial_couple_on_host_xyz_nmm"] == [0., 0., 12.]
    assert result["duration_increase_applied_to_Fc_perp"] is False


@pytest.mark.parametrize("wrong_sha", [None, "UNISSUED", "A" * 64, "0" * 64])
def test_finite_admission_sha_is_mandatory_and_cannot_use_an_old_gate_or_field(tmp_path, wrong_sha):
    with pytest.raises(ValueError, match="admission|dependency"):
        finite.consume(tmp_path / "old-field.json", "old-sha", admission_sha256=wrong_sha)
    with pytest.raises(TypeError, match="admission_sha256"):
        finite.consume(tmp_path / "old-field.json", "old-sha")


@pytest.mark.parametrize("mutation", ["schema", "payload", "gate_source", "state", "case", "accessory", "failure"])
def test_new_finite_receipt_binds_exact_bytes_sources_and_whole_state(mutation):
    identity = {"state_id": "finite-S", "case_id": "C", "accessory_placement": "rear"}
    field_sha, gate_sha = "a" * 64, "b" * 64
    receipt = {**identity, "schema": "thin_bolted_independent_finite_admission/v1", "field_sha256": field_sha,
        "source_sha256": {finite.GATE: gate_sha}, "independent_finite_current_support_load_and_equilibrium_checks_pass": True}
    finite.require_admission_receipt(receipt, identity, field_sha, gate_sha)
    if mutation == "schema":
        receipt["schema"] = "old-linear-admission"
    elif mutation == "payload":
        receipt["field_sha256"] = None  # A parsed-dict receipt has no raw-byte identity.
    elif mutation == "gate_source":
        receipt["source_sha256"][finite.GATE] = "c" * 64
    elif mutation == "state":
        receipt["state_id"] = "other-state"
    elif mutation == "case":
        receipt["case_id"] = "other-case"
    elif mutation == "accessory":
        receipt["accessory_placement"] = "front"
    else:
        receipt["independent_finite_current_support_load_and_equilibrium_checks_pass"] = False
    with pytest.raises(ValueError, match="finite"):
        finite.require_admission_receipt(receipt, identity, field_sha, gate_sha)
