"""Known-answer mapped-surface coupons; no candidate response or K."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from scripts import thin_bolted_finite_mechanics as frozen
from scripts.thin_bolted_corotational_methods import so3_exp, so3_log

PATH = Path(__file__).with_name("contact_geometry.py")
SPEC = importlib.util.spec_from_file_location("current_contact_geometry_coupons", PATH)
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def chart():
    return {"kind": "timber", "reference_stations_mm": [0., 100.],
            "node_reference_centers_xyz_mm": [[0., 0., 0.], [100., 0., 0.]],
            "node_dof_indices": np.arange(12).reshape(2, 6).tolist(),
            "storage_basis_columns_xyz": np.eye(3).tolist(),
            "reference_axis_xyz": [1., 0., 0.], "reference_start_xyz_mm": [0., 0., 0.]}


def transformed_state(row, q, rotation, translation):
    state = np.asarray(q).reshape(2, 6).copy()
    centers = np.asarray(row["node_reference_centers_xyz_mm"])
    for i in range(2):
        state[i, :3] = rotation @ (centers[i] + state[i, :3]) + translation - centers[i]
        state[i, 3:] = 1000. * so3_log(rotation @ so3_exp(state[i, 3:] / 1000.))
    return state.ravel()


def test_reference_surface_exact_identity():
    result = method.surface_state(chart(), np.zeros(12), [30., 2., 5.], [0., 1., 0.])
    assert np.array_equal(result["position"], [30., 2., 5.])
    assert np.array_equal(result["reference_coordinate_jacobian"], np.eye(3))
    assert np.array_equal(result["geometric_normal"], [0., 1., 0.])
    assert result["jacobian_determinant"] == 1.


def test_genuine_frozen_point_known_rigid_motion_and_normal():
    row, rotation, translation = chart(), so3_exp([.3, -.5, .8]), np.array([8., -3., 11.])
    q = transformed_state(row, np.zeros(12), rotation, translation)
    point, normal = np.array([37., -4., 9.]), np.array([0., 1., 0.])
    result = method.surface_state(row, q, point, normal)
    expected = rotation @ point + translation
    assert np.max(abs(result["position"] - expected)) < 3e-14
    genuine = frozen.interpolated_point(point, np.asarray(row["node_reference_centers_xyz_mm"]), q, .37)[0]
    assert np.array_equal(result["position"], genuine)
    assert np.max(abs(result["reference_coordinate_jacobian"] - rotation)) < 3e-15
    assert np.max(abs(result["geometric_normal"] - rotation @ normal)) < 3e-15


def test_shear_changes_surface_normal_and_has_hand_closest_point():
    row, q = chart(), np.zeros(12)
    q[7] = 20.
    result = method.surface_state(row, q, [40., 0., 7.], [0., 1., 0.])
    expected = np.eye(3)
    expected[1, 0] = .2
    assert np.array_equal(result["reference_coordinate_jacobian"], expected)
    assert np.max(abs(result["geometric_normal"] - np.array([-.2, 1., 0.]) / np.sqrt(1.04))) < 1e-15
    assert np.array_equal(result["material_normal"], [0., 1., 0.])
    assert abs(result["geometric_vs_material_normal_angle_rad"] - np.arctan(.2)) < 1e-15
    foot = method.closest_point(row, q, [40., 0., 7.], [0., 1., 0.], [40., 10., 7.])
    expected_x = (40. + .2 * 10.) / 1.04
    assert np.max(abs(np.asarray(foot["reference_footpoint_xyz_mm"]) - [expected_x, 0., 7.])) < 1e-13
    assert abs(foot["gap_opening_positive_mm"] - 2. / np.sqrt(1.04)) < 1e-13
    assert foot["local_stationary_closest_point_certified"] is True
    assert foot["global_closest_point_unique"] is False


def test_curved_geodesic_surface_jacobian_matches_reference_fd():
    row, q = chart(), np.array([2., -3., 1., 120., -70., 90., -1., 8., 3., 140., 40., 10.])
    point, normal = np.array([37., -4., 9.]), [0., 1., 0.]
    state = method.surface_state(row, q, point, normal)
    step = 1e-3
    numerical = np.column_stack([
        (method.surface_state(row, q, point + h, normal)["position"]
         - method.surface_state(row, q, point - h, normal)["position"]) / (2. * step)
        for h in np.eye(3) * step])
    assert np.max(abs(state["reference_coordinate_jacobian"] - numerical)) < 8e-11
    tangent = state["reference_coordinate_jacobian"] @ method.plane_basis(normal)
    assert np.max(abs(tangent.T @ state["geometric_normal"])) < 3e-16
    cross = np.cross(tangent[:, 0], tangent[:, 1])
    assert np.max(abs(cross / np.linalg.norm(cross) - state["geometric_normal"])) < 3e-16


def test_closest_point_and_geometric_normal_are_objective():
    row, q = chart(), np.array([2., -3., 1., 120., -70., 90., -1., 8., 3., 140., 40., 10.])
    point, normal = np.array([37., -4., 9.]), [0., 1., 0.]
    origin = method.surface_state(row, q, point, normal)
    target = origin["position"] + 3. * origin["geometric_normal"]
    foot = method.closest_point(row, q, point, normal, target)
    assert foot["local_stationary_closest_point_certified"]
    assert np.max(abs(np.asarray(foot["reference_footpoint_xyz_mm"]) - point)) < 2e-12
    rotation, translation = so3_exp([.7, -.2, .6]), np.array([8., -3., 11.])
    moved_q = transformed_state(row, q, rotation, translation)
    moved = method.surface_state(row, moved_q, point, normal)
    moved_foot = method.closest_point(row, moved_q, point, normal, rotation @ target + translation)
    assert moved_foot["local_stationary_closest_point_certified"]
    assert np.max(abs(moved["reference_coordinate_jacobian"] - rotation @ origin["reference_coordinate_jacobian"])) < 4e-15
    assert np.max(abs(moved["geometric_normal"] - rotation @ origin["geometric_normal"])) < 4e-15
    assert np.max(abs(np.asarray(moved_foot["reference_footpoint_xyz_mm"]) - point)) < 2e-9
    assert abs(moved_foot["gap_opening_positive_mm"] - foot["gap_opening_positive_mm"]) < 4e-14


def test_endpoint_extension_matches_frozen_provider_and_is_flagged():
    row, q = chart(), np.array([2., -3., 1., 120., -70., 90., -1., 8., 3., 140., 40., 10.])
    point = np.array([-10., 3., 5.])
    result = method.surface_state(row, q, point, [0., 1., 0.])
    original = frozen.interpolated_point(point, np.asarray(row["node_reference_centers_xyz_mm"]), q, 0.)[0]
    assert np.array_equal(result["position"], original)
    assert result["rigid_endpoint_extension_used"] is True
    assert result["raw_segment_fraction"] == -.1
    assert np.max(abs(result["reference_coordinate_jacobian"] - so3_exp(q[3:6] / 1000.))) < 1e-15


def test_internal_station_preserves_frozen_left_derivative_flag():
    row = chart()
    row["reference_stations_mm"] = [0., 50., 100.]
    row["node_reference_centers_xyz_mm"] = [[0., 0., 0.], [50., 0., 0.], [100., 0., 0.]]
    row["node_dof_indices"] = np.arange(18).reshape(3, 6).tolist()
    result = method.surface_state(row, np.zeros(18), [50., 2., 4.], [0., 1., 0.])
    assert result["at_internal_station_derivative_is_one_sided"] is True
    assert result["segment_index"] == 0


@pytest.mark.parametrize("station", [0., 100.])
def test_outer_station_has_no_smooth_closest_point_certificate(station):
    row, q, point = chart(), np.zeros(12), np.array([station, 0., 7.])
    q[7] = 20.
    target = method.surface_state(row, q, point, [0., 1., 0.])["position"]
    foot = method.closest_point(row, q, point, [0., 1., 0.], target)
    assert foot["at_any_station_derivative_is_one_sided"] is True
    assert foot["distance_hessian_stencil_remains_in_one_smooth_branch"] is False
    assert foot["local_stationary_closest_point_certified"] is False


def test_closest_point_hessian_stencil_cannot_cross_endpoint_clamp():
    row, q, point = chart(), np.zeros(12), np.array([.0004, 0., 7.])
    q[7] = 20.
    target = method.surface_state(row, q, point, [0., 1., 0.])["position"]
    foot = method.closest_point(row, q, point, [0., 1., 0.], target)
    assert foot["at_any_station_derivative_is_one_sided"] is False
    assert foot["distance_hessian_stencil_remains_in_one_smooth_branch"] is False
    assert foot["local_stationary_closest_point_certified"] is False


def test_collapsed_or_inverted_chart_rejected():
    for translation in (-100., -110.):
        q = np.zeros(12)
        q[6] = translation
        with pytest.raises(ValueError, match="singular or inverted"):
            method.surface_state(chart(), q, [40., 0., 0.], [0., 1., 0.])


def test_exact_current_raw_is_required_before_gate_or_q(tmp_path, monkeypatch):
    path = tmp_path / "foreign.json"
    path.write_text(json.dumps({"response": {"q": [0.]}}))
    monkeypatch.setattr(method, "load", lambda *args: pytest.fail("gate cannot run before raw hash check"))
    with pytest.raises(ValueError, match="exact current contact diagnostic input differs"):
        method.consume(path, path, path)


def test_exclusive_output_preserves_racing_file(tmp_path, monkeypatch):
    out = tmp_path / "result.json"
    def consume(*args):
        out.write_text("other owned bytes")
        return {"counts": {}}
    monkeypatch.setattr(method, "consume", consume)
    monkeypatch.setattr(sys, "argv", [str(PATH), "--out", str(out)])
    with pytest.raises(FileExistsError):
        method.main()
    assert out.read_text() == "other owned bytes"
