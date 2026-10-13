"""Synthetic source-map checks; no candidate q, body, actions or solve."""
import importlib.util
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

LEAF = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("injectivity_method_owned_fixture", LEAF / "injectivity.py")
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def bound(row, q, extent=None, **kwargs):
    return method.sufficient_box_bound(row, np.asarray(q).ravel(), owner_id="synthetic-timber",
                                       extent=method.toy_extent() if extent is None else extent, **kwargs)


def observed(row, q, point):
    return method.geometry.surface_state(row, np.asarray(q).ravel(), point, [0., 0., 1.])


def rz(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0.], [s, c, 0.], [0., 0., 1.]])


@pytest.mark.parametrize("translation", ([0., 0., 0.], [100., -50., 7.]))
def test_identity_and_translation_have_zero_derivative_bound(translation):
    row, q = method.toy_row(), np.zeros((2, 6))
    q[:, :3] = translation
    result = bound(row, q)
    assert result["computed_sufficient_L"] == 0.
    assert result["sufficient_global_one_to_one_criterion_met"] is True
    assert result["lower_bilipschitz_factor"] == 1. - result["comparison_padding"]
    assert result["containing_finished_candidate_body_source_binding_verified"] is False
    for point in ([37., 1., 2.], [-3., -1., 2.], [103., -1., -2.]):
        state = observed(row, q, point)
        np.testing.assert_allclose(state["position"], np.asarray(point) + translation)
        np.testing.assert_allclose(state["reference_coordinate_jacobian"], np.eye(3))


def test_shear_bound_exact_interior_and_clamped_extensions():
    row, q = method.toy_row(), np.zeros((2, 6))
    q[1, 1] = 20.
    result = bound(row, q)
    assert result["computed_sufficient_L"] == pytest.approx(.2)
    expected = np.eye(3); expected[1, 0] = .2
    np.testing.assert_allclose(observed(row, q, [37., 1., 2.])["reference_coordinate_jacobian"], expected)
    for point in ([-3., 1., 2.], [103., 1., 2.]):
        state = observed(row, q, point)
        assert state["rigid_endpoint_extension_used"] is True
        np.testing.assert_allclose(state["reference_coordinate_jacobian"], np.eye(3))
    assert result["segments"][0]["rotation_term_bound"] == 0.
    assert result["segments"][0]["geodesic_arm_slope_term_bound"] == 0.


def test_rigid_rotation_with_nodal_centerline_motion_is_exact_rigid_map():
    row, q = method.toy_row(), np.zeros((2, 6))
    rotation, translation = rz(.2), np.array([4., -2., 1.])
    centers = np.asarray(row["node_reference_centers_xyz_mm"])
    q[:, :3] = centers @ (rotation - np.eye(3)).T + translation
    q[:, 5] = 200.
    result = bound(row, q)
    assert result["computed_sufficient_L"] == pytest.approx(4. * np.sin(.1))
    for point in ([-3., 1., 2.], [37., -1., 2.], [103., -1., -2.]):
        state = observed(row, q, point)
        np.testing.assert_allclose(state["position"], rotation @ point + translation, atol=3e-14)
        np.testing.assert_allclose(state["reference_coordinate_jacobian"], rotation, atol=1e-15)
    # The strong identity comparison is conservative even for an exact rigid
    # rotation, with no rotation-reference optimization implied.
    assert result["computed_sufficient_L"] > np.linalg.norm(rotation - np.eye(3), 2)


def test_large_proper_rigid_rotation_is_inconclusive_not_inversion():
    row, q = method.toy_row(), np.zeros((2, 6))
    q[:, 3] = 1400.
    result = bound(row, q)
    assert result["computed_sufficient_L"] == pytest.approx(2. * np.sin(.7))
    assert result["computed_sufficient_L"] > 1.
    assert result["disposition"] == "INCONCLUSIVE_SUFFICIENT_BOUND"
    for key in ("lower_bilipschitz_factor", "upper_bilipschitz_factor", "inverse_lipschitz_factor_on_image_only"):
        assert result[key] is None
    points = np.array([[-3., 1., 2.], [103., -1., -2.]])
    states = [observed(row, q, point) for point in points]
    assert all(state["jacobian_determinant"] == pytest.approx(1.) for state in states)
    assert np.linalg.norm(states[1]["position"] - states[0]["position"]) == pytest.approx(np.linalg.norm(points[1] - points[0]))


def test_exact_geodesic_derivative_includes_centerline_cancellation():
    row, q = method.toy_row(), np.zeros((2, 6))
    q[:, 1] = [2., 5.]
    q[:, 5] = [30., 130.]
    result = bound(row, q)
    segment = result["segments"][0]
    assert segment["maximum_affine_reference_arm_norm_box_corner_bound_mm"] == pytest.approx(np.sqrt(13.))
    assert segment["absolute_geodesic_angle_upper_rad"] == pytest.approx(.13)
    axis = np.array([1., 0., 0.])
    projector = np.diag([0., 1., 1.])
    omega_skew = np.array([[0., -.1, 0.], [.1, 0., 0.], [0., 0., 0.]])
    for point in ([7., -2., 3.], [37., 1., 2.], [89., -1., -2.]):
        rotation = rz(.03 + .1 * point[0] / 100.)
        arm = np.array([0., point[1], point[2]])
        correction = ((rotation - np.eye(3)) @ projector
                      + np.outer(np.array([0., .03, 0.]) + rotation @ omega_skew @ arm / 100., axis))
        observed_derivative = observed(row, q, point)["reference_coordinate_jacobian"]
        np.testing.assert_allclose(observed_derivative - np.eye(3), correction, atol=3e-16)
        assert np.linalg.norm(correction, 2) <= segment["sufficient_segment_L"]


def test_actual_tolerated_chord_deviation_is_kept_in_projector_and_arms():
    row, q = method.toy_row(), np.zeros((2, 6))
    row["node_reference_centers_xyz_mm"][1][1] = 5e-8
    q[1, 5] = 100.
    result = bound(row, q)
    segment = result["segments"][0]
    assert segment["reference_chord_per_station_xyz"][1] == pytest.approx(5e-10)
    assert segment["centerline_cancellation_matrix_I_minus_v_aT"][1][0] == pytest.approx(-5e-10)
    point, h, t = np.array([37., 1., 2.]), 100., .37
    chord = np.asarray(row["node_reference_centers_xyz_mm"][1])
    arm = point - t * chord
    rotation = rz(.1 * t)
    expected = ((rotation - np.eye(3)) @ (np.eye(3) - np.outer(chord / h, [1., 0., 0.]))
                + np.outer(rotation @ np.cross([0., 0., .1], arm) / h, [1., 0., 0.]))
    np.testing.assert_allclose(observed(row, q, point)["reference_coordinate_jacobian"] - np.eye(3), expected, atol=3e-16)


def test_multisegment_C0_values_and_one_sided_derivative_jumps():
    row, q = method.toy_row((0., 40., 100.)), np.zeros((3, 6))
    q[:, 1], q[:, 5] = [0., 2., -1.], [0., 30., 10.]
    result = bound(row, q)
    assert result["sufficient_global_one_to_one_criterion_met"] is True
    for i, station in enumerate(row["reference_stations_mm"]):
        point = np.array([station, 1., 2.])
        expected = np.array([station, q[i, 1], 0.]) + rz(q[i, 5] / 1000.) @ [0., 1., 2.]
        state = observed(row, q, point)
        np.testing.assert_allclose(state["position"], expected, atol=2e-14)
        assert state["at_any_station_derivative_is_one_sided"] is True
        for delta in (-1e-7, 1e-7):
            np.testing.assert_allclose(observed(row, q, point + [delta, 0., 0.])["position"], expected, atol=2e-7)
    left = observed(row, q, [40. - 1e-7, 1., 2.])["reference_coordinate_jacobian"]
    right = observed(row, q, [40. + 1e-7, 1., 2.])["reference_coordinate_jacobian"]
    assert np.linalg.norm(left - right) > .09
    assert result["C0_segment_join_and_clamped_endpoint_values_match_by_same_nodal_pose"] is True
    assert result["derivatives_at_join_planes_are_piecewise_one_sided"] is True


def test_distance_bounds_cover_points_across_joins_and_extensions():
    row, q = method.toy_row((0., 40., 100.)), np.zeros((3, 6))
    q[:, 1], q[:, 5] = [0., 2., -1.], [0., 30., 10.]
    result = bound(row, q)
    points = np.array([[-5., -2., -3.], [12., 1., -2.], [40., -1., 3.], [77., 2., 0.], [105., 0., 2.]])
    mapped = [observed(row, q, p)["position"] for p in points]
    for i in range(len(points)):
        for j in range(i):
            distance = np.linalg.norm(points[i] - points[j])
            actual = np.linalg.norm(mapped[i] - mapped[j])
            assert result["lower_bilipschitz_factor"] * distance <= actual
            assert actual <= result["upper_bilipschitz_factor"] * distance


@pytest.mark.parametrize("changed", ("owner", "empty-source", "nonfinite", "degenerate"))
def test_extent_source_contract_rejects_missing_or_foreign_inputs(changed):
    extent = method.toy_extent()
    if changed == "owner":
        extent["owner_id"] = "another-timber"
    elif changed == "empty-source":
        extent["source_identity"] = {}
    elif changed == "nonfinite":
        extent["bounds_xyz_mm"][0][0] = float("nan")
    else:
        extent["bounds_xyz_mm"][0] = [0., 0.]
    with pytest.raises(ValueError):
        bound(method.toy_row(), np.zeros(12), extent)


@pytest.mark.parametrize("changed", ("duplicate-index", "fractional-index", "off-centerline", "wrong-basis", "wrong-axis"))
def test_chart_contract_rejects_unsupported_geometry(changed):
    row = method.toy_row()
    if changed == "duplicate-index":
        row["node_dof_indices"][1][0] = 0
    elif changed == "fractional-index":
        row["node_dof_indices"][1][0] = 6.5
    elif changed == "off-centerline":
        row["node_reference_centers_xyz_mm"][1][1] = .01
    elif changed == "wrong-basis":
        row["storage_basis_columns_xyz"][0][0] = 2.
    else:
        row["reference_axis_xyz"] = [2., 0., 0.]
    with pytest.raises(ValueError):
        bound(row, np.zeros(12))


@pytest.mark.parametrize("angle", (np.pi / 2., 3.2))
def test_frozen_rotation_chart_guards_are_not_weakened(angle):
    q = np.zeros((2, 6)); q[1, 5] = angle * 1000.
    with pytest.raises(ValueError):
        bound(method.toy_row(), q)


def test_near_one_padding_remains_inconclusive_and_inputs_immutable():
    row, q, extent = method.toy_row(), np.zeros((2, 6)), method.toy_extent()
    q[1, 1] = 100. - 5e-9
    before = method.canonical({"row": row, "q": q.tolist(), "extent": extent})
    result = bound(row, q, extent)
    assert result["computed_sufficient_L"] < 1.
    assert result["padded_sufficient_L"] >= 1.
    assert result["sufficient_global_one_to_one_criterion_met"] is False
    assert method.canonical({"row": row, "q": q.tolist(), "extent": extent}) == before
    assert not any(result["release"].values())
    assert result["target_in_image_inverse_existence_or_nearest_feature_proved"] is False
    assert result["interval_arithmetic_or_formal_float_roundoff_certificate"] is False


def test_loaded_source_guard_rejects_without_touching_source(monkeypatch):
    monkeypatch.setattr(method, "LOADED_SOURCE_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="loaded injectivity source changed"):
        bound(method.toy_row(), np.zeros(12))


def test_positive_determinant_illustration_is_not_global_injectivity():
    # An independent analytic counterexample, not the frozen timber map.
    def illustration(point):
        x, y, z = point
        return np.array([np.exp(x) * np.cos(y), np.exp(x) * np.sin(y), z])
    first, second = np.array([.3, 0., .4]), np.array([.3, 2. * np.pi, .4])
    np.testing.assert_allclose(illustration(first), illustration(second), atol=1e-15)
    assert np.exp(2. * first[0]) > 0.
    assert np.linalg.norm(first - second) > 6.


def test_synthetic_method_receipt_sources_releases_and_no_candidate_claim():
    before = method.source_pins()
    result = method.known_answers()
    assert result["method_checks_pass"] is True
    assert result["source_sha256"] == before == method.source_pins()
    assert len(result["known_answers"]) == 6
    assert result["candidate_q_BREP_K_or_action_consumed"] is False
    assert not any(result["release"].values())
    assert deepcopy(result)["source_pins_before_after_unchanged"] is True
