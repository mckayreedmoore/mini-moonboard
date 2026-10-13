"""Sufficient geodesic timber-map injectivity on a declared convex box only.

This is an analytic method bound, not a candidate inverse or contact query.
The frozen map's rotations, point interpolation, clamping and source bytes
remain unchanged. A failed sufficient bound says nothing about inversion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import platform
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OWN = Path(__file__).resolve()
LOADED_SOURCE_SHA256 = hashlib.sha256(OWN.read_bytes()).hexdigest()
PINS = {
    "scripts/thin_bolted_corotational_methods.py": "7638a09c145135a19dcccb7cd84a01b8a01d2a4465b02ebfc33372e672e5ebc8",
    "scripts/thin_bolted_finite_mechanics.py": "8c2bf2f27538fc1d599db9ddee2efbbb6344687393781bd689de09a4998772a2",
    "scripts/thin_bolted_finite_frame.py": "68f711549da9e6b52c60db4e4df78235ba8105084ded0d81c9a3430cf5973588",
    "fea/generated/thin-bolted-direct-contact-a12-v1/observer-isolation-v2/current-contact-v1/contact_geometry.py": "c260834cd7caf6bbafbe317fe757ac29370aea6912fd9f9f77ed1574e43dd711",
    "fea/generated/thin-bolted-current-contact-v1/implicit-reference-solid-v1/coupon.py": "c801e88a8d35a20602ceeb863b84b045230c72982d0ea87bb842ecee371ca73a",
    "fea/generated/thin-bolted-current-contact-v1/implicit-reference-solid-v1/method-result.json": "06cf0f31c2e3f96cf5601144c0fe962a57679d18e8e4564a19447c1b04345a12",
}
for _path, _digest in PINS.items():
    if hashlib.sha256((ROOT / _path).read_bytes()).hexdigest() != _digest:
        raise ValueError("preserve the frozen map/inverse method: " + _path)
GEOMETRY_PATH = ROOT / next(p for p in PINS if p.endswith("/contact_geometry.py"))
_spec = importlib.util.spec_from_file_location("frozen_geodesic_geometry_for_injectivity", GEOMETRY_PATH)
geometry = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(geometry)
require = geometry.require
RELEASE = {"candidate_method_ready": False, "candidate_admission": False,
           "capacity": False, "fabrication": False, "climbing": False}


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def source_pins():
    pins = dict(PINS)
    for path in (OWN, OWN.with_name("test_injectivity.py"), OWN.with_name("input.json")):
        pins[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    require(pins[str(OWN.relative_to(ROOT))] == LOADED_SOURCE_SHA256, "loaded injectivity source changed")
    for path, digest in pins.items():
        require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, "injectivity source changed: " + path)
    return pins


def sufficient_box_bound(row, q, *, owner_id, extent, comparison_padding=1e-10):
    """Bound every segment and both rigid endpoint extensions without sampling.

    Extent is a source-described BOX. This method does not authenticate that
    the box contains a finished candidate body; that is a separate source join.
    All segments are included conservatively even if outside the box station
    range. Floating computations do not constitute interval arithmetic.
    """
    before = source_pins()
    require(isinstance(owner_id, str) and owner_id and row.get("kind") == "timber", "explicit own timber chart required")
    require(extent.get("schema") == "thin_bolted_finite_reference_domain_box/v1"
            and extent.get("owner_id") == owner_id and isinstance(extent.get("source_identity"), dict)
            and extent["source_identity"], "own finite extent/source description required")
    bounds = np.asarray(extent["bounds_xyz_mm"], dtype=float)
    require(bounds.shape == (3, 2) and np.isfinite(bounds).all() and np.all(bounds[:, 1] > bounds[:, 0]),
            "finite nondegenerate convex ambient box required")
    corners = np.asarray(list(itertools.product(*bounds.tolist())))
    state = np.asarray(q, dtype=float)
    stations = np.asarray(row["reference_stations_mm"], dtype=float)
    centers = np.asarray(row["node_reference_centers_xyz_mm"], dtype=float)
    declared_indices = np.asarray(row["node_dof_indices"])
    indices = np.asarray(row["node_dof_indices"], dtype=int)
    basis = np.asarray(row["storage_basis_columns_xyz"], dtype=float)
    axis = np.asarray(row["reference_axis_xyz"], dtype=float)
    start = np.asarray(row["reference_start_xyz_mm"], dtype=float)
    require(state.ndim == 1 and np.isfinite(state).all() and stations.ndim == 1 and len(stations) >= 2
            and np.isfinite(stations).all() and np.all(np.diff(stations) > 0.)
            and centers.shape == (len(stations), 3) and np.isfinite(centers).all()
            and indices.shape == (len(stations), 6) and np.array_equal(declared_indices, indices)
            and np.all(indices >= 0) and np.all(indices < len(state))
            and len(set(indices.ravel())) == indices.size
            and axis.shape == start.shape == (3,) and np.isfinite(np.r_[axis, start]).all()
            and abs(np.linalg.norm(axis) - 1.) < 1e-8
            and basis.shape == (3, 3) and np.isfinite(basis).all()
            and np.linalg.norm(basis.T @ basis - np.eye(3)) < 1e-8 and abs(np.linalg.det(basis) - 1.) < 1e-8
            and np.max(abs(centers - start - stations[:, None] * axis)) < 1e-7,
            "ordered finite proper straight timber chart and unique source indices required")
    require(np.isfinite(comparison_padding) and comparison_padding >= 0., "nonnegative finite comparison padding required")
    nodal = state[indices]
    translations = nodal[:, :3] @ basis.T
    theta = nodal[:, 3:] @ basis.T / 1000.
    rotations = [geometry.so3_exp(value) for value in theta]
    angles = np.linalg.norm(theta, axis=1)
    axis_norm = float(np.linalg.norm(axis))
    all_segments = []
    for i, h in enumerate(np.diff(stations)):
        omega = geometry.so3_log(rotations[i].T @ rotations[i + 1])
        turn = float(np.linalg.norm(omega))
        # Invoke the exact frozen branch guard, including its <90deg turn.
        geometry.mechanics.interpolated_rotation(nodal[i:i + 2].ravel(), 0., basis)
        # SO(3) triangle inequalities: theta(t)<=min(theta0+t*w,
        # theta1+(1-t)*w). Its maximum is <=(theta0+theta1+w)/2.
        angle_upper = min(float(np.pi), float(.5 * (angles[i] + angles[i + 1] + turn)))
        rotation_bound = float(2. * np.sin(.5 * angle_upper))
        chord_per_station = (centers[i + 1] - centers[i]) / h
        projector = np.eye(3) - np.outer(chord_per_station, axis)
        fractions = ((corners - start) @ axis - stations[i]) / h
        arms = corners - centers[i] - fractions[:, None] * (centers[i + 1] - centers[i])
        arm_radius = float(np.linalg.norm(arms, axis=1).max())
        delta_u = translations[i + 1] - translations[i]
        rotation_term = rotation_bound * float(np.linalg.norm(projector, 2))
        translation_term = axis_norm * float(np.linalg.norm(delta_u)) / h
        geodesic_arm_term = axis_norm * turn * arm_radius / h
        all_segments.append({"segment_index": i, "station_interval_mm": stations[i:i + 2].tolist(),
            "reference_chord_per_station_xyz": chord_per_station.tolist(),
            "centerline_cancellation_matrix_I_minus_v_aT": projector.tolist(),
            "world_translation_change_mm": delta_u.tolist(), "relative_rotation_log_rad": omega.tolist(),
            "absolute_geodesic_angle_upper_rad": angle_upper,
            "maximum_affine_reference_arm_norm_box_corner_bound_mm": arm_radius,
            "rotation_term_bound": rotation_term, "translation_slope_term_bound": translation_term,
            "geodesic_arm_slope_term_bound": geodesic_arm_term,
            "sufficient_segment_L": rotation_term + translation_term + geodesic_arm_term})
    extensions = [{"endpoint": label, "station_mm": float(stations[i]),
                   "rigid_endpoint_extension_L": float(2. * np.sin(.5 * angles[i]))}
                  for label, i in (("first", 0), ("last", -1))]
    raw = max([r["sufficient_segment_L"] for r in all_segments]
              + [r["rigid_endpoint_extension_L"] for r in extensions])
    padded = raw + comparison_padding
    sufficient = bool(padded < 1.)
    require(source_pins() == before, "injectivity sources changed during bound")
    return {"schema": "thin_bolted_geodesic_reference_box_injectivity_bound/v1", "owner_id": owner_id,
        "row_canonical_sha256": canonical(row), "q_canonical_sha256": canonical(state.tolist()),
        "extent_canonical_sha256": canonical(extent), "source_described_domain": extent,
        "segments": all_segments, "rigid_endpoint_extensions": extensions,
        "computed_sufficient_L": raw, "comparison_padding": comparison_padding,
        "padded_sufficient_L": padded,
        "disposition": "SUFFICIENT_ON_DECLARED_BOX_UNDER_EXACT_MAP_HYPOTHESES" if sufficient else "INCONCLUSIVE_SUFFICIENT_BOUND",
        "sufficient_global_one_to_one_criterion_met": sufficient,
        "lower_bilipschitz_factor": 1. - padded if sufficient else None,
        "upper_bilipschitz_factor": 1. + padded if sufficient else None,
        "inverse_lipschitz_factor_on_image_only": 1. / (1. - padded) if sufficient else None,
        "C0_segment_join_and_clamped_endpoint_values_match_by_same_nodal_pose": True,
        "derivatives_at_join_planes_are_piecewise_one_sided": True,
        "containing_finished_candidate_body_source_binding_verified": False,
        "interval_arithmetic_or_formal_float_roundoff_certificate": False,
        "target_in_image_inverse_existence_or_nearest_feature_proved": False,
        "candidate_q_geometry_contact_or_capacity_admitted": False, "release": dict(RELEASE)}


def toy_row(stations=(0., 100.)):
    return {"kind": "timber", "reference_stations_mm": list(stations),
            "node_reference_centers_xyz_mm": [[x, 0., 0.] for x in stations],
            "node_dof_indices": np.arange(6 * len(stations)).reshape(-1, 6).tolist(),
            "storage_basis_columns_xyz": np.eye(3).tolist(), "reference_axis_xyz": [1., 0., 0.],
            "reference_start_xyz_mm": [0., 0., 0.]}


def toy_extent():
    return {"schema": "thin_bolted_finite_reference_domain_box/v1", "owner_id": "synthetic-timber",
            "bounds_xyz_mm": [[-5., 105.], [-2., 2.], [-3., 3.]],
            "source_identity": {"kind": "analytic-synthetic-convex-box", "finished_body_containment": "toy declaration only"}}


def known_answers():
    before = source_pins()
    inputs = json.loads(OWN.with_name("input.json").read_bytes())
    require(inputs["synthetic_extent"] == toy_extent(), "matching frozen synthetic extent required")
    row, extent = toy_row(), toy_extent()
    cases = []
    for name, state in (("straight-identity", np.zeros((2, 6))), ("rigid-translation", np.zeros((2, 6))),
                        ("affine-centerline-shear", np.zeros((2, 6))), ("geodesic-director-change", np.zeros((2, 6)))):
        if name == "rigid-translation":
            state[:, :3] = [100., -50., 7.]
        elif name == "affine-centerline-shear":
            state[1, 1] = 20.
        elif name == "geodesic-director-change":
            state[1, 5] = 100.
        result = sufficient_box_bound(row, state.ravel(), owner_id="synthetic-timber", extent=extent)
        require(result["sufficient_global_one_to_one_criterion_met"], "small synthetic criterion did not close")
        cases.append({"case_id": name, "synthetic_row": row, "synthetic_q": state.ravel().tolist(), "bound": result})
    multi = toy_row((0., 40., 100.))
    state = np.zeros((3, 6)); state[:, 1] = [0., 2., -1.]; state[:, 5] = [0., 30., 10.]
    cases.append({"case_id": "C0-two-segments-and-rigid-extensions", "synthetic_row": multi,
                  "synthetic_q": state.ravel().tolist(),
                  "bound": sufficient_box_bound(multi, state.ravel(), owner_id="synthetic-timber", extent=extent)})
    # A proper rigid axial rotation is known injective even when this strong
    # absolute-identity bound is >=1. It must remain merely inconclusive.
    state = np.zeros((2, 6)); state[:, 3] = 1400.
    large = sufficient_box_bound(row, state.ravel(), owner_id="synthetic-timber", extent=extent)
    require(not large["sufficient_global_one_to_one_criterion_met"] and large["lower_bilipschitz_factor"] is None,
            "an inconclusive sufficient criterion was converted to inversion")
    cases.append({"case_id": "large-proper-rigid-rotation-inconclusive", "known_true_rigid_map_injective": True,
                  "synthetic_row": row, "synthetic_q": state.ravel().tolist(), "bound": large})
    require(source_pins() == before, "injectivity method sources changed")
    return {"schema": "thin_bolted_geodesic_map_injectivity_method_coupon/v1", "method_checks_pass": True,
            "source_sha256": before, "source_pins_before_after_unchanged": True, "known_answers": cases,
            "analytic_proof": inputs["analytic_proof"], "finite_extent_source_contract": inputs["finite_extent_source_contract"],
            "limits": inputs["limits"], "toolchain": {"python": platform.python_version(), "numpy": np.__version__},
            "candidate_q_BREP_K_or_action_consumed": False, "release": dict(RELEASE)}


def main():
    invocation = {"actual_sys_argv_from_start": sys.argv.copy(), "actual_sys_orig_argv_from_start": sys.orig_argv.copy(),
                  "loaded_source_path": str(OWN.relative_to(ROOT)), "loaded_driver_sha256": LOADED_SOURCE_SHA256,
                  "cwd_from_start": str(Path.cwd())}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "preserve existing injectivity method evidence")
    result = {**known_answers(), "execution": invocation}
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
