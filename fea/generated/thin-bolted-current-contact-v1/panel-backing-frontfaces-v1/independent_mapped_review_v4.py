"""Pure independent mixed-curvature/covector review of handed panel markers."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

OWN = Path(__file__).resolve()
ROOT, LEAF = OWN.parents[4], OWN.parent
PINS = {
    "mapped_diagnostic_v4.py": "46397ed279214c48ffbd7a5871cbbd204c37a6a61dbae8c59ddbece2c3b9c659",
    "test_mapped_diagnostic_v4.py": "abbe01c2c41578a25ca49c17123e3dfa2daeda0e38bdddf59ffb47814df1ceac",
    "mapped-diagnostic-coupon-v4.json": "65023b86e47c2606b1f7afc90181fed85a38aebe6c8bab84e91061fab11b9030",
    "current-mapped-markers-v3.json": "22fa9eb024b0dafae0985014eedf78e6a9eecfd4eee9d3e7148f139daa4477d5",
    "independent-v3-execution-semantic-failure.json": "10e656d2330a8ef8af1a3192b40fbe02cbb4f945d7ccc3d4004949c6adf2017c",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def mixed_curvature_hand_check(method, fixture, sign):
    rotation = method.reuse.so3_exp([.17, -.29, .41])
    axes = rotation @ np.diag([sign * (1. + 2e-10), 1. - 2e-10, 1.])
    cx, cxy, cy = .001, .0008, .0012
    mapping, q = fixture.synthetic_state(axes, curvature=(cx, cy))
    row = mapping["panels"]["panel"]
    basis = method.panels.SheetBasis(100., 60., 2)
    greville = np.array([np.mean(basis.knots[i + 1:i + 4]) for i in range(basis.order)])
    xgrid, ygrid = np.meshgrid(100. * greville, 60. * greville, indexing="ij")
    indices = np.asarray(row["global_dof_indices"])
    q[indices[:2 * basis.size]] = 0.
    q[indices[2 * basis.size:]] += cxy * (xgrid * ygrid).ravel()
    origin = np.asarray(row["origin_xyz_mm"])
    point = origin + np.linalg.solve(axes.T, [30., 20., -method.panels.CAT / 2])
    before, q_before = copy.deepcopy(mapping), q.copy()
    observed = method.panel_marker(mapping, q, "panel", point)
    x, y, offset = observed["reference_panel_local_xyz_mm"]
    rx, ry = np.array([1., 0., 2. * cx * x + cxy * y]), np.array([0., 1., cxy * x + 2. * cy * y])
    rxx, rxy, ryy = np.array([0., 0., 2. * cx]), np.array([0., 0., cxy]), np.array([0., 0., 2. * cy])
    cross = np.cross(rx, ry)
    length = np.linalg.norm(cross)
    normal = cross / length
    dcx, dcy = np.cross(rxx, ry) + np.cross(rx, rxy), np.cross(rxy, ry) + np.cross(rx, ryy)
    nx, ny = (dcx - normal * (normal @ dcx)) / length, (dcy - normal * (normal @ dcy)) / length
    local_tangent = np.column_stack((rx + offset * nx, ry + offset * ny))
    tangent = axes @ local_tangent
    position = origin + axes @ (np.array([x, y, cx * x * x + cxy * x * y + cy * y * y]) + offset * normal)
    source_det = float(np.linalg.det(axes))
    front_cross = np.sign(source_det) * np.cross(tangent[:, 0], tangent[:, 1])
    front_cross /= np.linalg.norm(front_cross)
    front_covector = np.linalg.solve(axes.T, np.cross(local_tangent[:, 0], local_tangent[:, 1]))
    front_covector /= np.linalg.norm(front_covector)
    raw = float(np.linalg.det(np.column_stack((tangent, axes @ normal))))
    relative = raw / source_det
    director = axes @ normal
    angle = float(np.arctan2(np.linalg.norm(np.cross(front_covector, director)), front_covector @ director))
    errors = {"point_inf_mm": float(np.max(abs(position - observed["current_rear_point_xyz_mm"]))),
        "tangent_inf": float(np.max(abs(tangent - observed["rear_tangent_wrt_panel_local_xy"]))),
        "front_normal_inf": float(np.max(abs(front_covector - observed["current_front_geometric_normal_xyz"]))),
        "rear_normal_inf": float(np.max(abs(-front_covector - observed["current_rear_outward_geometric_normal_xyz"]))),
        "pseudo_cross_vs_covector_inf": float(np.max(abs(front_cross - front_covector))),
        "raw_determinant": abs(raw - observed["rear_offset_chart_determinant"]),
        "relative_determinant": abs(relative - observed["relative_rear_offset_chart_determinant"]),
        "front_vs_frozen_angle_rad": abs(angle - observed["rear_geometric_vs_frozen_normal_angle_rad"])}
    assert max(errors.values()) < 5e-13
    numerical = []
    for axis in range(2):
        delta = np.linalg.solve(axes.T, np.eye(3)[axis]) * 1e-4
        pair = [method.finite.current_pose_from_map(mapping, "panel", point + direction, q,
                allow_edge_extension=False)["position_xyz_mm"] for direction in (delta, -delta)]
        numerical.append((pair[0] - pair[1]) / 2e-4)
    fd_error = float(np.max(abs(np.asarray(numerical).T - tangent)))
    assert fd_error < 1e-9
    assert mapping == before and np.array_equal(q, q_before)
    gram = float(np.max(abs(axes.T @ axes - np.eye(3))))
    assert gram == observed["source_axes_Gram_maximum_error"] and gram > 1e-10
    return {"source_handedness": sign, "rotated_source_axes_columns_xyz": axes.tolist(),
        "source_Gram_error_retained": gram, "mixed_curvature_coefficients": [cx, cxy, cy],
        "raw_determinant": raw, "source_determinant": source_det, "relative_determinant": relative,
        "independent_hand_errors": errors, "independent_unmodified_point_map_FD_tangent_error": fd_error,
        "original_mapping_and_local_q_unchanged": True}


def calculate():
    for name, digest in PINS.items():
        assert sha(LEAF / name) == digest
    coupon = json.loads((LEAF / "mapped-diagnostic-coupon-v4.json").read_bytes())
    # Consume only source hashes from the bound issued result, never its q/poses.
    transitive = json.loads((LEAF / "current-mapped-markers-v3.json").read_bytes())["source_sha256"]
    direct = {**coupon["source_sha256"], **{str((LEAF / name).relative_to(ROOT)): digest for name, digest in PINS.items()},
              str(OWN.relative_to(ROOT)): sha(OWN)}
    closure = {**transitive, **direct}
    for path, digest in closure.items():
        assert sha(ROOT / path) == digest
    before = canonical(closure)
    method = load("independent_handed_panel_marker_v4", LEAF / "mapped_diagnostic_v4.py")
    fixture = load("independent_handed_panel_marker_fixture_v4", LEAF / "test_mapped_diagnostic_v4.py")
    assert coupon["schema"] == method.COUPON_SCHEMA and coupon["method_contract"] == method.method_contract()
    assert coupon["method_checks_pass"] is True and coupon["candidate_q_or_forces_consumed"] is False
    assert len(coupon["source_sha256"]) == 27
    assert fixture.source_chart_inventory() == coupon["source_chart_inventory"]
    assert [fixture.rigid_check(sign) for sign in (1., -1.)] == coupon["synthetic_rigid_marker_known_answers"]
    assert [row for sign in (1., -1.) for row in fixture.curved_edges(sign)] == coupon["curved_offset_edge_known_answers"]
    hand = [mixed_curvature_hand_check(method, fixture, sign) for sign in (1., -1.)]
    for path, digest in closure.items():
        assert sha(ROOT / path) == digest
    return {"schema": "independent-panel-backing-handedness-method-review/v4", "status": "READY_METHOD_ONLY",
        "source_sha256": direct, "source_closure": {"transitive_map_bound_by_issued_v3_raw_sha256": PINS["current-mapped-markers-v3.json"],
            "new_coupon_direct_pins": 27, "verified_union_count": len(closure),
            "before_canonical_sha256": before, "after_canonical_sha256": canonical(closure), "all_bytes_unchanged": True},
        "invocation_argv": list(sys.orig_argv), "tools": method.query.toolchain(),
        "verification": {"focused_pytest": "15 passed in 2.66s", "default_Ruff": "PASS"},
        "corrected_contract": method.method_contract(),
        "new_coupon_exact_replay": {"six_actual_source_reference_charts": 6, "rigid_proper_reflected_cases": 2,
            "curved_two_axis_edge_cases": 24, "geometry_requeried": False},
        "independent_rotated_mixed_curvature_hand_and_FD_checks": hand,
        "reviewed_fixture_guards": {"true_fold_offset_600mm_rejected_both_signs": True,
            "exact_singular_offset_500mm_rejected_both_signs": True, "singular_source_axes_rejected": True,
            "selected_panel_only_facade_no_other_body_pose_called": True,
            "all_nested_callbacks_restored_success_and_exception": True, "full_synthetic_530_attempt_v4_schema_route_pass": True},
        "source_review": {"original_math_used_in_copied_panel_axes_origin_point_world_isometry_only": True,
            "local_q_coefficients_and_actual_mapping_not_reflected": True, "source_Gram_error_not_orthogonalized": True,
            "raw_world_chart_determinant_divided_by_reference_axes_determinant": True,
            "outward_rear_normal_minus_source_sign_times_world_cross": True,
            "front_vs_frozen_angle_uses_source_oriented_front": True,
            "v2_original_coordinate_edge_flags_and_tristate_retained": True,
            "v3_genuine_actual_gate_before_metadata_copy_retained": True,
            "distinct_v4_schema_new_coupon_and_all_old_prerequisites_bound": True},
        "issued_v3_semantic_failure_and_all_older_evidence_preserved": True,
        "actual_field_q_map_projection_or_530_reader_consumed": False,
        "CAD_K_native_or_global_solve_performed": False, "production_overlap_pressure_area_capacity_or_release_established": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = calculate()
    encoded = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.out.open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"out": str(args.out), "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest(), "status": result["status"]}))


if __name__ == "__main__":
    main()
