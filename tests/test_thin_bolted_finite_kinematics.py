"""Local geometric known answers; no frame assembly or equilibrium solve."""

import json

import numpy as np
import pytest

from scripts import thin_bolted_finite_kinematics as diagnostics

POSITIONS = np.array([[0., 0., 0.], [100., 0., 0.]])


@pytest.mark.parametrize("kind", ["timber", "shaft", "fitting"])
def test_large_common_rigid_rotation_has_zero_local_deformation(kind):
    rotation = diagnostics.corot.so3_exp([.5, -.7, .6])
    translation = np.array([7., -11., 13.])
    state = np.zeros((2, 6))
    state[:, :3] = POSITIONS @ (rotation-np.eye(3)).T + translation
    state[:, 3:] = 1000*diagnostics.corot.so3_log(rotation)
    if kind == "timber":
        result = diagnostics.timber_element(POSITIONS, np.eye(3), state.ravel())
        assert result["maximum_local_rotation_rad"] < 1e-14
        assert result["shear_angle_marker_norm_rad"] < 1e-14
    elif kind == "shaft":
        result = diagnostics.shaft_element(POSITIONS, np.eye(3), state.ravel())
        assert abs(result["midpoint_axial_strain_measure"]) < 1e-14
        assert result["midpoint_shear_measure_norm"] < 1e-14
        assert np.linalg.norm(result["material_twist_bend1_bend2_curvature_rad_mm"]) < 1e-14
    else:
        result = diagnostics.fitting_element(POSITIONS, state.ravel())
        assert result["relative_port_translation_over_reference_chord_length"] < 1e-14
        assert result["maximum_local_rotation_rad"] < 1e-14
    assert abs(result["chord_extension_mm"]) < 1e-12
    assert result["neighbor_relative_rotation_rad"] < 1e-14


def test_pure_axial_chord_and_midpoint_shear_known_answer():
    state = np.zeros(12); state[6:9] = [2., 3., -4.]
    shaft = diagnostics.shaft_element(POSITIONS, np.eye(3), state)
    assert shaft["midpoint_axial_strain_measure"] == pytest.approx(.02)
    np.testing.assert_allclose(shaft["midpoint_shear_measures"], [.03, -.04], atol=1e-14)
    assert shaft["midpoint_shear_measure_norm"] == pytest.approx(.05)
    assert shaft["current_length_mm"] == pytest.approx(np.sqrt(102**2+3**2+4**2))
    state[7:9] = 0.
    timber = diagnostics.timber_element(POSITIONS, np.eye(3), state)
    assert timber["corotational_chord_extension_mm"] == pytest.approx(2.)
    assert timber["chord_extension_over_reference_length"] == pytest.approx(.02)


def test_constant_bending_arc_replays_recorded_chord_shortening_comparison():
    angle = .2
    state = np.zeros((2, 6))
    state[:, 5] = [-500*angle, 500*angle]
    state[1, 0] = 100*(np.sin(angle/2)/(angle/2)-1)
    shaft = diagnostics.shaft_element(POSITIONS, np.eye(3), state.ravel())
    timber = diagnostics.timber_element(POSITIONS, np.eye(3), state.ravel())
    expected = np.sin(angle/2)/(angle/2)-1
    assert shaft["midpoint_axial_strain_measure"] == pytest.approx(expected, abs=1e-14)
    assert timber["chord_extension_over_reference_length"] == pytest.approx(expected, abs=1e-14)
    assert shaft["constant_bending_arc_chord_shortening_comparison"] == pytest.approx(-expected, abs=1e-14)
    assert shaft["material_bending_curvature_norm_rad_mm"] == pytest.approx(angle/100)
    assert shaft["midpoint_shear_measure_norm"] < 1e-14
    assert not shaft["arc_comparison_is_recovered_physical_axial_strain"]


def test_fitting_local_pose_is_distinct_from_flat_leg_shear_or_curvature():
    state = np.zeros(12); state[6:9] = [2., 3., -4.]; state[11] = 100.
    result = diagnostics.fitting_element(POSITIONS, state)
    np.testing.assert_allclose(result["relative_port_translation_in_first_pose_reference_world_xyz_mm"], [2., 3., -4.])
    np.testing.assert_allclose(result["relative_flange_rotation_in_first_pose_rad"], [0., 0., .1])
    assert result["transverse_port_translation_over_reference_chord_length"] == pytest.approx(.05)
    assert not result["individual_flat_leg_heel_curvature_recovered"]
    assert not result["port_translation_marker_is_flat_leg_shear_strain"]


def test_storage_basis_mapping_reproduces_world_shaft_measures():
    basis = diagnostics.corot.so3_exp([.12, -.23, .17])
    positions = POSITIONS @ basis.T
    local = np.zeros((2, 6)); local[1, :3] = [2., 3., -4.]
    mapping = {"ndof": 12, "mechanical_bodies": {"shaft/coupon": {"kind": "shaft",
        "node_reference_centers_xyz_mm": positions.tolist(), "node_dof_indices": np.arange(12).reshape(2, 6).tolist(),
        "storage_basis_columns_xyz": basis.tolist()}}}
    result = diagnostics.evaluate_map(mapping, local.ravel(), {})["shaft_elements"][0]
    assert result["midpoint_axial_strain_measure"] == pytest.approx(.02)
    np.testing.assert_allclose(result["midpoint_shear_measures"], [.03, -.04], atol=1e-14)
    assert result["adopted_deformation_acceptance_limit"] is None


def test_recorded_local_chart_failure_is_preserved_without_new_threshold():
    state = np.zeros(12); state[11] = 1000*np.pi/2
    with pytest.raises(ValueError, match="90-degree"):
        diagnostics.shaft_element(POSITIONS, np.eye(3), state)
    with pytest.raises(ValueError, match="90-degree"):
        diagnostics.fitting_element(POSITIONS, state)


def test_failed_or_canonical_only_admission_is_not_a_current_field_receipt(tmp_path):
    field = tmp_path/"field.json"; field.write_text("{}")
    admission = tmp_path/"admission.json"
    admission.write_text(json.dumps({"schema": "thin_bolted_independent_finite_admission/v1",
        "independent_finite_current_support_load_and_equilibrium_checks_pass": False}))
    with pytest.raises(ValueError, match="finite-current admission"):
        diagnostics.evaluate_admitted(field, admission, diagnostics.frame.sha(admission), "0"*64)
    with pytest.raises(ValueError, match="immutable finite admission"):
        diagnostics.evaluate_admitted(field, admission, "0"*64, "0"*64)
    gate = "scripts/thin_bolted_finite_state_audit.py"
    gate_sha = diagnostics.frame.sha(diagnostics.frame.ROOT/gate)
    admission.write_text(json.dumps({"schema": "thin_bolted_independent_finite_admission/v1",
        "independent_finite_current_support_load_and_equilibrium_checks_pass": True,
        "source_sha256": {gate: gate_sha}, "field_sha256": None,
        "field_canonical_sha256": diagnostics.frame.sha(field)}))
    with pytest.raises(ValueError, match="field bytes differ"):
        diagnostics.evaluate_admitted(field, admission, diagnostics.frame.sha(admission), gate_sha)
