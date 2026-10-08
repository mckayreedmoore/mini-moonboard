"""Pure handedness/offset/edge known answers; no actual q, CAD or projection."""

import argparse
import copy
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).with_name("mapped_diagnostic_v4.py")
SPEC = importlib.util.spec_from_file_location("handed_panel_marker_method_fixture", PATH)
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def synthetic_state(axes, *, rotation=None, translation=None, curvature=(0., 0.)):
    mapping, q = method.reuse.mapping_state(relative_panel_shift=np.zeros(3))
    row = mapping["panels"]["panel"]
    row["axes_columns_xyz"] = np.asarray(axes).tolist()
    basis = method.panels.SheetBasis(100., 60., 2)
    greville = np.array([np.mean(basis.knots[i + 1:i + 4]) for i in range(basis.order)])
    x, y = np.meshgrid(100. * greville, 60. * greville, indexing="ij")
    local = np.c_[x.ravel(), y.ravel(), np.zeros(basis.size)]
    rotation = np.eye(3) if rotation is None else rotation
    translation = np.zeros(3) if translation is None else translation
    origin, axes = np.asarray(row["origin_xyz_mm"]), np.asarray(axes)
    transform = np.linalg.solve(axes, rotation @ axes)
    affine = np.linalg.solve(axes, rotation @ origin + translation - origin)
    coefficients = local @ (transform - np.eye(3)).T + affine
    quadratic = np.array([sum(a * b for a, b in ((t[0], t[1]), (t[0], t[2]), (t[1], t[2]))) / 3.
        for i in range(basis.order) for t in [basis.knots[i + 1:i + 4]]])
    coefficients[:, 2] += (curvature[0] * 100.**2 * quadratic[:, None]
        + curvature[1] * 60.**2 * quadratic[None, :]).ravel()
    q[np.asarray(row["global_dof_indices"])] = coefficients.T.ravel()
    return mapping, q


def reference_point(mapping, local):
    row = mapping["panels"]["panel"]
    return np.asarray(row["origin_xyz_mm"]) + np.asarray(row["axes_columns_xyz"]) @ local


def checked_marker(mapping, q, point):
    before_map, before_q = copy.deepcopy(mapping), q.copy()
    result = method.panel_marker(mapping, q, "panel", point)
    assert mapping == before_map and np.array_equal(q, before_q)
    actual = method.finite.current_pose_from_map(mapping, "panel", point, q, allow_edge_extension=False)
    np.testing.assert_array_equal(result["current_rear_point_xyz_mm"], actual["position_xyz_mm"])
    np.testing.assert_array_equal(result["frozen_midsurface_front_normal_vector_xyz"], actual["current_vector_xyz"])
    row = mapping["panels"]["panel"]
    axes = np.asarray(row["axes_columns_xyz"])
    local = (point - row["origin_xyz_mm"]) @ axes
    np.testing.assert_array_equal(result["reference_panel_local_xyz_mm"], local)
    np.testing.assert_array_equal(result["reference_panel_xy_clipping_mm"], local[:2] - np.clip(local[:2], [0., 0.], [100., 60.]))
    assert result["source_axes_Gram_maximum_error"] == float(np.max(abs(axes.T @ axes - np.eye(3))))
    assert result["source_axes_determinant"] == float(np.linalg.det(axes))
    assert result["relative_rear_offset_chart_determinant"] > 0.
    return result


@pytest.mark.parametrize("sign", [1., -1.])
def test_reflected_rigid_pose_point_tangent_normal_and_relative_chart(sign):
    rigid_check(sign)


def rigid_check(sign):
    axes = np.diag([sign, 1., 1.])
    rotation, translation = method.reuse.so3_exp([.3, -.5, .8]), np.array([8., -3., 11.])
    mapping, q = synthetic_state(axes, rotation=rotation, translation=translation)
    local = np.array([30., 20., -method.panels.CAT / 2])
    point = reference_point(mapping, local)
    result = checked_marker(mapping, q, point)
    np.testing.assert_allclose(result["current_rear_point_xyz_mm"], rotation @ point + translation, atol=3e-14, rtol=0.)
    np.testing.assert_allclose(result["rear_tangent_wrt_panel_local_xy"], rotation @ axes[:, :2], atol=1e-14, rtol=0.)
    np.testing.assert_allclose(result["current_rear_outward_geometric_normal_xyz"], -rotation @ axes[:, 2], atol=1e-14, rtol=0.)
    assert result["rear_geometric_vs_frozen_normal_angle_rad"] < 2e-15
    assert result["rear_offset_chart_determinant"] == pytest.approx(sign, abs=2e-15)
    assert result["reference_normal_offset_chart_determinant"] == sign
    assert result["relative_rear_offset_chart_determinant"] == pytest.approx(1., abs=2e-15)
    return result


def source_chart_inventory():
    method.query.verify(method.CHART_SOURCES)
    source = json.loads((method.ROOT / "fea/generated/thin-bolted-panel/operators-intervals8.json").read_bytes())
    rows = []
    for name, row in source.items():
        axes = np.asarray(row["local_axes_columns_xyz"])
        determinant = float(np.linalg.det(axes))
        assert determinant == -1.
        mapping, q = synthetic_state(axes)
        result = checked_marker(mapping, q, reference_point(mapping, [30., 20., -method.panels.CAT / 2]))
        assert result["relative_rear_offset_chart_determinant"] == pytest.approx(1., abs=1e-15)
        rows.append({"panel": name, "source_axes_columns_xyz": axes.tolist(), "source_axes_determinant": determinant,
            "source_axes_Gram_maximum_error": result["source_axes_Gram_maximum_error"],
            "synthetic_reference_raw_determinant": result["rear_offset_chart_determinant"],
            "synthetic_reference_relative_determinant": result["relative_rear_offset_chart_determinant"]})
    assert len(rows) == 6
    return rows


def test_all_six_authenticated_source_charts_reference_orientation_and_Gram_preserved():
    source_chart_inventory()


def curved_edges(sign):
    axes = np.diag([sign, 1., 1.])
    mapping, q = synthetic_state(axes, curvature=(.001, .001))
    records = []
    for axis, limit in ((0, 100.), (1, 60.)):
        for boundary in (0., limit):
            for epsilon in (-5e-8, 0., 5e-8):
                local = np.array([30., 20., -method.panels.CAT / 2])
                local[axis] = boundary + epsilon
                point = reference_point(mapping, local)
                result = checked_marker(mapping, q, point)
                actual_local = np.asarray(result["reference_panel_local_xyz_mm"])
                xy = np.clip(actual_local[:2], [0., 0.], [100., 60.])
                inside = (actual_local[:2] >= 0.) & (actual_local[:2] <= [100., 60.])
                slopes = .002 * xy
                normal = np.r_[-slopes, 1.]; normal /= np.linalg.norm(normal)
                length = np.linalg.norm(np.r_[-slopes, 1.])
                nx = ([-.002, 0., 0.] - normal * (normal @ [-.002, 0., 0.])) / length
                ny = ([0., -.002, 0.] - normal * (normal @ [0., -.002, 0.])) / length
                tangent = axes @ np.column_stack((np.r_[1., 0., slopes[0]] + inside[0] * actual_local[2] * nx,
                    np.r_[0., 1., slopes[1]] + inside[1] * actual_local[2] * ny))
                error = float(np.max(abs(tangent - result["rear_tangent_wrt_panel_local_xy"])))
                assert error < 1e-14
                expected_branch = ("tolerance_extrapolation" if actual_local[axis] < 0. or actual_local[axis] > limit else
                    "material_interior_side_at_boundary" if actual_local[axis] in (0., limit) else "material_interior")
                assert result["panel_xy_derivative_branch_by_axis"][axis] == expected_branch
                cross = np.cross(tangent[:, 0], tangent[:, 1]); rear = -sign * cross / np.linalg.norm(cross)
                np.testing.assert_allclose(result["current_rear_outward_geometric_normal_xyz"], rear, atol=3e-16, rtol=0.)
                records.append({"source_sign": sign, "axis": axis, "boundary": boundary, "epsilon_mm": epsilon,
                    "reference_local_xyz_mm": actual_local.tolist(), "branches": result["panel_xy_derivative_branch_by_axis"],
                    "hand_tangent_maximum_error": error, "raw_determinant": result["rear_offset_chart_determinant"],
                    "relative_determinant": result["relative_rear_offset_chart_determinant"]})
    return records


@pytest.mark.parametrize("sign", [1., -1.])
def test_curved_normal_offset_near_edges_original_clipping_and_branch(sign):
    curved_edges(sign)


@pytest.mark.parametrize("sign", [1., -1.])
def test_curved_offset_derivative_matches_unmodified_pose_finite_difference(sign):
    mapping, q = synthetic_state(np.diag([sign, 1., 1.]), curvature=(.001, .001))
    local = np.array([30., 20., -method.panels.CAT / 2])
    result = checked_marker(mapping, q, reference_point(mapping, local))
    finite_difference = []
    for axis in (0, 1):
        step = np.eye(3)[axis] * 1e-4
        points = [method.finite.current_pose_from_map(mapping, "panel", reference_point(mapping, local + delta), q,
            allow_edge_extension=False)["position_xyz_mm"] for delta in (step, -step)]
        finite_difference.append((points[0] - points[1]) / 2e-4)
    np.testing.assert_allclose(result["rear_tangent_wrt_panel_local_xy"], np.asarray(finite_difference).T, atol=7e-11, rtol=0.)


@pytest.mark.parametrize("sign", [1., -1.])
@pytest.mark.parametrize("offset,match", [(600., "inverted panel"), (500., "singular panel rear")])
def test_real_offset_fold_and_singular_chart_rejected_independent_of_source_sign(sign, offset, match):
    mapping, q = synthetic_state(np.diag([sign, 1., 1.]), curvature=(.001, 0.))
    # Zero datum keeps the exact singular h=500 representable after world
    # point subtraction; a nonzero datum rounds that local offset below 500.
    mapping["panels"]["panel"]["origin_xyz_mm"] = [0., 0., 0.]
    with pytest.raises(ValueError, match=match):
        method.panel_marker(mapping, q, "panel", reference_point(mapping, [0., 20., offset]))


def test_source_singular_chart_rejected_before_pose():
    mapping, q = synthetic_state(np.eye(3))
    mapping["panels"]["panel"]["axes_columns_xyz"][0][0] = 0.
    with pytest.raises(ValueError, match="singular/nonfinite source"):
        method.panel_marker(mapping, q, "panel", [0., 0., 0.])


@pytest.mark.parametrize("raises", [False, True])
def test_nested_v3_v2_callback_route_selected_panel_only_and_restoration(monkeypatch, raises):
    mapping, q = synthetic_state(np.diag([-1., 1., 1.]))
    before = (method.v3.v2.ORIGINAL_PANEL, method.core.panel_marker, method.core.union_summary,
        method.core.load, method.core.observe_port)
    pose, calls = method.finite.current_pose_from_map, []

    def observed_pose(facade, body, point, passed_q, **kwargs):
        assert body == "panel" and passed_q is q
        assert facade["mechanical_bodies"] is mapping["mechanical_bodies"]
        assert np.linalg.det(facade["panels"][body]["axes_columns_xyz"]) > 0.
        calls.append(body)
        return pose(facade, body, point, passed_q, **kwargs)

    monkeypatch.setattr(method.finite, "current_pose_from_map", observed_pose)
    try:
        with method.handed_callbacks() as context, method.v3.bridge_callbacks(), method.v3.v2.corrected_callbacks():
            result = method.core.panel_marker(mapping, q, "panel", reference_point(mapping, [-5e-8, 20., -method.panels.CAT / 2]))
            assert result["panel_xy_derivative_branch_by_axis"][0] == "tolerance_extrapolation"
            assert context["panel_marker_attempt_count"] == 1 and calls == ["panel"]
            if raises:
                raise RuntimeError("declared synthetic observer failure")
    except RuntimeError as exc:
        assert raises and str(exc) == "declared synthetic observer failure"
    assert (method.v3.v2.ORIGINAL_PANEL, method.core.panel_marker, method.core.union_summary,
        method.core.load, method.core.observe_port) == before


def test_full_v4_schema_consumer_nests_old_callbacks_and_restores(monkeypatch):
    mapping, q = synthetic_state(np.diag([-1., 1., 1.]))
    before = (method.v3.v2.ORIGINAL_PANEL, method.core.panel_marker, method.core.union_summary,
        method.core.load, method.core.observe_port)

    def synthetic_v3_consume(path, digest, *, progress=None):
        assert path.name == "mapped-diagnostic-coupon-v3.json" and digest == method.REUSED[path.name]
        with method.v3.bridge_callbacks(), method.v3.v2.corrected_callbacks():
            for _ in range(530):
                marker = method.core.panel_marker(mapping, q, "panel", reference_point(mapping, [30., 20., -method.panels.CAT / 2]))
        return {"schema": method.v3.SCHEMA, "method_contract": method.v3.method_contract(),
            "source_sha256": {}, "synthetic_marker": marker, "sentinel": "unchanged"}

    monkeypatch.setattr(method.v3, "consume", synthetic_v3_consume)
    with tempfile.TemporaryDirectory(dir=PATH.parent, prefix="pure-v4-route-") as temporary:
        path = Path(temporary) / "coupon.json"
        method.query.write_exclusive(path, {"schema": method.COUPON_SCHEMA, "method_checks_pass": True,
            "method_contract": method.method_contract(), "source_sha256": method.own_pins(), "candidate_q_or_forces_consumed": False})
        result = method.consume(path, method.sha(path))
    assert result["schema"] == method.SCHEMA and result["reused_v3_consumer_schema"] == method.v3.SCHEMA
    assert result["handedness_marker_attempt_count"] == 530 and result["sentinel"] == "unchanged"
    assert result["reused_v3_method_contract"] == method.v3.method_contract()
    assert (method.v3.v2.ORIGINAL_PANEL, method.core.panel_marker, method.core.union_summary,
        method.core.load, method.core.observe_port) == before


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    inventory = source_chart_inventory()
    rigid = [rigid_check(sign) for sign in (1., -1.)]
    edges = [record for sign in (1., -1.) for record in curved_edges(sign)]
    for sign in (1., -1.):
        test_curved_offset_derivative_matches_unmodified_pose_finite_difference(sign)
        for offset, match in ((600., "inverted panel"), (500., "singular panel rear")):
            test_real_offset_fold_and_singular_chart_rejected_independent_of_source_sign(sign, offset, match)
    pins = method.own_pins()
    method.query.write_exclusive(args.out, {"schema": method.COUPON_SCHEMA, "method_checks_pass": True,
        "method_contract": method.method_contract(), "source_sha256": pins, "source_chart_inventory": inventory,
        "synthetic_rigid_marker_known_answers": rigid, "curved_offset_edge_known_answers": edges,
        "offset_fold_600mm_and_singularity_500mm_rejected_both_handednesses": True,
        "original_v3_coupon_and_review_reused_without_new_readiness_transfer": True,
        "candidate_q_or_forces_consumed": False, "actual_current_gate_executed": False,
        "CAD_or_K_or_native_or_global_solve_evaluated": False,
        "invocation_argv": list(sys.orig_argv), "working_directory": str(Path.cwd()),
        "environment": {key: os.environ.get(key) for key in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "OPENBLAS_NUM_THREADS")},
        "toolchain": method.query.toolchain(), "actual_consumer_readiness_or_physical_contact_proven": False})
    print(json.dumps({"output": str(args.out), "sha256": method.sha(args.out)}))


if __name__ == "__main__":
    main()
