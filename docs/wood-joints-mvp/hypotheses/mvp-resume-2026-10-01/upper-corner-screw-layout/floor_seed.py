"""Bounded fixed-floor-mask QP guesses for the unchanged final frame method.

API: ``f, report = run(H, D, e, W, k, uni, normals, tangents)``.
This is a zero-clearance numerical seed, not a completed frame response.
The caller must pass f to right_corner_clearance.solve with the original
operators, laws and requested clearances, and retain that method's checks.

Inactive floor normals are omitted by zeroing a private stiffness copy for
simple_frame.solve_branch. All other finite unilateral contacts remain in
its convex QP; only the selected floor tangents are held. Every returned
candidate is audited using the ORIGINAL stiffness and operators and the
stricter final-method tolerances. No force is clipped or repaired.

Try the suggested open normal rows 1588 and 1603, then masks at Hamming
distance one and two (at most 37 QPs for eight footprints). Stop at the
first fully checked seed. Otherwise return the best finite guess marked
UNACCEPTED_NUMERICAL_SEED_ONLY. If no QP provides a finite response, raise
RuntimeError with the retained report path; do not manufacture a guess.

Each call retains input arrays, source snapshots, selected vectors and a
strict JSON report under this directory's ignored rawlocal/floor-seed.
Importing this module performs no calculation or filesystem writes.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import itertools
import json
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "rawlocal/floor-seed"
PREFERRED_OPEN_ROWS = (1588, 1603)
MAX_MASKS = 37
FORCE_TOL_N = 1e-4
GAP_TOL_MM = 1e-8
BODY_FORCE_TOL_N = 0.1
BODY_MOMENT_TOL_NMM = 2.0
SEED_ACTIVE_THRESHOLD_N = 1e-6
SOURCE_PINS = {
    "simple_frame.py": "3d8c14cccf9306766a4993bad9ea39501bbc9c812af9e79b393875d5d3c09d34",
    "right_corner_clearance.py": "93c7727c1c24fb5b7ed725fc4656651fe6e760a36a378d635a97e202b872fb88",
}


def _peak(values):
    return float(np.max(np.abs(values), initial=0.0))


def _masks(normals):
    preferred = ~np.isin(normals, PREFERRED_OPEN_ROWS)
    for distance in range(3):
        for flips in itertools.combinations(range(len(normals)), distance):
            mask = preferred.copy()
            mask[list(flips)] = ~mask[list(flips)]
            yield mask


def _inputs(H, D, e, W, k, uni, normals, tangents):
    # Keep private arrays so the caller's laws and operators cannot be changed.
    H, D, e, W, k = (np.array(x, dtype=float, copy=True) for x in (H, D, e, W, k))
    raw_uni, raw_normals, raw_tangents = map(np.asarray, (uni, normals, tangents))
    if not np.isin(raw_uni, [False, True]).all():
        raise ValueError("uni must contain only boolean flags")
    if not all(np.issubdtype(x.dtype, np.integer) for x in (raw_normals, raw_tangents)):
        raise ValueError("floor row indices must be integers")
    uni = np.array(raw_uni, dtype=bool, copy=True)
    normals = np.array(raw_normals, dtype=int, copy=True)
    tangents = np.array(raw_tangents, dtype=int, copy=True)
    n = len(k)
    if (k.shape != (n,) or H.shape != (n, n) or D.ndim != 2
            or D.shape[0] != n or e.shape != (n,) or uni.shape != (n,)
            or W.shape != (D.shape[1],) or not D.shape[1] or D.shape[1] % 6):
        raise ValueError("incompatible frame equation shapes")
    if not all(np.isfinite(x).all() for x in (H, D, e, W, k)) or np.any(k < 0):
        raise ValueError("nonfinite operators or negative stiffness")
    if normals.shape != (8,) or tangents.shape != (8, 2):
        raise ValueError("expected eight floor normals and eight tangent pairs")
    floor_rows = np.r_[normals, tangents.ravel()]
    if (len(np.unique(floor_rows)) != 24 or np.any(floor_rows < 0)
            or np.any(floor_rows >= n)):
        raise ValueError("invalid or overlapping floor rows")
    if not (uni[normals].all() and np.all(k[normals] > 0)
            and not uni[tangents].any() and np.all(k[tangents] == 0)):
        raise ValueError("floor law does not match finite normals and ideal tangents")
    return H, D, e, W, k, uni, normals, tangents


def _audit(H, D, e, W, k, uni, normals, tangents, bearing, f, a, q):
    expected = k * np.where(uni, np.maximum(q, 0.0), q)
    held, released = tangents[bearing].ravel(), tangents[~bearing].ravel()
    balance = (D.T @ f - W).reshape(-1, 6)
    finite = k > 0
    inactive = normals[~bearing]
    seed_bearing = f[normals] > SEED_ACTIVE_THRESHOLD_N
    metrics = {
        "force_balance_n": _peak(balance[:, :3]),
        "moment_balance_nmm": 1000 * _peak(balance[:, 3:]),
        "finite_law_error_n": _peak(f[finite] - expected[finite]),
        "minimum_unilateral_force_n": float(f[uni].min()),
        "minimum_floor_normal_force_n": float(f[normals].min()),
        "held_floor_motion_mm": _peak(q[held]),
        "released_floor_force_n": _peak(f[released]),
        "inactive_floor_force_n": _peak(f[inactive]),
        "inactive_floor_positive_motion_mm": float(np.max(q[inactive], initial=0.0)),
        "positive_normal_domain_mm": float(q[uni].max()),
        "open_normal_beyond_negative_table_endpoint": int(np.count_nonzero(q[uni] < -10)),
        "floor_seed_mask_mismatches": int(np.count_nonzero(seed_bearing != bearing)),
        "kinematic_residual_mm": _peak(q - (D @ a + e - H @ f)),
    }
    checks = {
        "body_force": metrics["force_balance_n"] < BODY_FORCE_TOL_N,
        "body_moment": metrics["moment_balance_nmm"] < BODY_MOMENT_TOL_NMM,
        "original_finite_laws": metrics["finite_law_error_n"] < FORCE_TOL_N,
        "nonnegative_unilateral": metrics["minimum_unilateral_force_n"] >= -FORCE_TOL_N,
        "nonnegative_floor_normals": metrics["minimum_floor_normal_force_n"] >= -FORCE_TOL_N,
        "held_floor": metrics["held_floor_motion_mm"] < GAP_TOL_MM,
        "released_floor": metrics["released_floor_force_n"] == 0.0,
        "inactive_floor_zero_force": metrics["inactive_floor_force_n"] == 0.0,
        "inactive_floor_closed_domain": metrics["inactive_floor_positive_motion_mm"] <= GAP_TOL_MM,
        "original_positive_domain": metrics["positive_normal_domain_mm"] <= 10.0,
        "final_method_floor_seed_mask": metrics["floor_seed_mask_mismatches"] == 0,
    }
    # Check the zero-clearance seed's force-bearing rows. The final method
    # must additionally apply its target-pair exclusions and repeat its rank
    # check; this API intentionally takes no clearance targets. Defer the SVD
    # until all balance and law checks pass; it cannot rescue a failure.
    metrics["zero_gap_seed_rigid_rank"] = None
    if all(checks.values()):
        rank_rows = np.union1d(
            np.flatnonzero(~uni & finite),
            np.r_[np.flatnonzero(uni & (f > FORCE_TOL_N)), held],
        )
        metrics["zero_gap_seed_rigid_rank"] = int(np.linalg.matrix_rank(D[rank_rows]))
    checks["zero_gap_seed_rigid_rank"] = metrics["zero_gap_seed_rigid_rank"] == D.shape[1]
    score = max(
        metrics["force_balance_n"] / BODY_FORCE_TOL_N,
        metrics["moment_balance_nmm"] / BODY_MOMENT_TOL_NMM,
        metrics["finite_law_error_n"] / FORCE_TOL_N,
        max(0.0, -metrics["minimum_unilateral_force_n"]) / FORCE_TOL_N,
        metrics["held_floor_motion_mm"] / GAP_TOL_MM,
        metrics["inactive_floor_positive_motion_mm"] / GAP_TOL_MM,
        max(0.0, metrics["positive_normal_domain_mm"]) / 10.0,
    )
    return {
        "checks": checks,
        "metrics": metrics,
        "all_checks_pass": all(checks.values()),
        "ranking": [sum(not value for value in checks.values()), score],
        "bearing_mask": bearing.tolist(),
        "seed_bearing_mask": seed_bearing.tolist(),
        "active_floor_normals": normals[bearing].tolist(),
        "inactive_floor_normals": inactive.tolist(),
        "floor_normal_force_n": f[normals].tolist(),
        "floor_normal_motion_mm": q[normals].tolist(),
        "floor_tangent_force_n": f[tangents].tolist(),
        "floor_tangent_motion_mm": q[tangents].tolist(),
    }


def run(H, D, e, W, k, uni, normals, tangents):
    """Return (finite force seed, JSON-safe report); never accept final physics.

    The report records every attempted fixed mask, original-law residuals,
    exact input/source hashes and ignored artifact paths. An unaccepted seed
    may initialize the caller's unchanged method but confers no acceptance.
    RuntimeError means no finite candidate; its report remains recoverable.
    """
    H, D, e, W, k, uni, normals, tangents = _inputs(H, D, e, W, k, uni, normals, tangents)
    source_bytes = {"floor_seed.py": Path(__file__).read_bytes()}
    for name, pin in SOURCE_PINS.items():
        value = (HERE.parent / name).read_bytes()
        if hashlib.sha256(value).hexdigest() != pin:
            raise RuntimeError(f"changed source {name}; seed method requires its recorded equations")
        source_bytes[name] = value
    # Reuse the pinned parent helper without changing its settings.
    import simple_frame as frame

    if Path(frame.__file__).resolve() != (HERE.parent / "simple_frame.py").resolve():
        raise RuntimeError("seed helper resolved outside the pinned parent packet")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="attempt-", dir=OUTPUT))
    sources = {}
    for name, value in source_bytes.items():
        path = output / (name + ".snapshot")
        path.write_bytes(value)
        sources[name] = {"sha256": hashlib.sha256(value).hexdigest(), "snapshot": str(path)}
    inputs_path = output / "inputs.npz"
    np.savez_compressed(inputs_path, H=H, D=D, e=e, W=W, k=k, uni=uni,
                        normals=normals, tangents=tangents)
    report = {
        "schema": "bounded_fixed_floor_mask_numerical_seed/v1",
        "status": "NO_FINITE_NUMERICAL_SEED",
        "physical_acceptance_transferred": False,
        "final_method_required": "right_corner_clearance.solve with original inputs and requested gaps",
        "source_snapshot": sources,
        "inputs": {"path": str(inputs_path), "sha256": hashlib.sha256(inputs_path.read_bytes()).hexdigest()},
        "preferred_open_rows": list(PREFERRED_OPEN_ROWS),
        "preferred_open_rows_present": normals[np.isin(normals, PREFERRED_OPEN_ROWS)].tolist(),
        "maximum_masks": MAX_MASKS,
        "maximum_hamming_distance": 2,
        "qp_settings": dict(frame.SETTINGS),
        "tool_versions": {name: importlib.metadata.version(name)
                          for name in ("numpy", "scipy", "osqp")},
        "tolerances": {
            "body_force_n_strict": BODY_FORCE_TOL_N,
            "body_moment_nmm_strict": BODY_MOMENT_TOL_NMM,
            "finite_force_n_strict": FORCE_TOL_N,
            "floor_motion_mm_strict": GAP_TOL_MM,
            "inactive_floor_motion_mm_inclusive": GAP_TOL_MM,
            "positive_unilateral_domain_mm_inclusive": 10.0,
            "final_method_seed_active_threshold_n_strict": SEED_ACTIVE_THRESHOLD_N,
        },
        "attempts": [],
        "selected_attempt": None,
        "report_path": str(output / "report.json"),
    }
    best = None
    for index, bearing in enumerate(_masks(normals)):
        seed_k = k.copy()
        seed_k[normals[~bearing]] = 0.0
        try:
            f, a, q, iterations = frame.solve_branch(H, D, e, W, seed_k, uni, tangents, bearing)
            if (f.shape != k.shape or a.shape != W.shape or q.shape != k.shape
                    or not all(np.isfinite(x).all() for x in (f, a, q))):
                raise RuntimeError("QP returned a nonfinite or incorrectly shaped response")
            attempt = _audit(H, D, e, W, k, uni, normals, tangents, bearing, f, a, q)
            attempt["qp_iterations"] = iterations
            # Reject overflow in derived metrics too; persisted reports never
            # contain NaN or infinity, including failed finite-force guesses.
            json.dumps(attempt, allow_nan=False)
        except (RuntimeError, ValueError, np.linalg.LinAlgError) as error:
            attempt = {"bearing_mask": bearing.tolist(), "all_checks_pass": False,
                       "terminal_exception": str(error)}
        else:
            if best is None or tuple(attempt["ranking"]) < best[0]:
                best = (tuple(attempt["ranking"]), index, f.copy(), a.copy(), q.copy(), bearing.copy())
        report["attempts"].append(attempt)
        if attempt["all_checks_pass"]:
            break
    report["attempted_masks"] = len(report["attempts"])
    if best is not None:
        _, index, f, a, q, bearing = best
        report["selected_attempt"] = index
        selected = report["attempts"][index]
        report["status"] = ("CHECKED_ZERO_GAP_NUMERICAL_SEED_ONLY" if selected["all_checks_pass"]
                            else "UNACCEPTED_NUMERICAL_SEED_ONLY")
        vectors_path = output / "seed.npz"
        np.savez_compressed(vectors_path, f=f, a=a, q=q, bearing=bearing)
        report["vectors"] = {"path": str(vectors_path),
                             "sha256": hashlib.sha256(vectors_path.read_bytes()).hexdigest()}
    report["source_files_unchanged"] = all(
        (Path(__file__) if name == "floor_seed.py" else HERE.parent / name).read_bytes() == value
        for name, value in source_bytes.items()
    )
    if not report["source_files_unchanged"]:
        report["status"] = "STOP_SOURCE_CHANGED"
    Path(report["report_path"]).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    if not report["source_files_unchanged"] or best is None:
        raise RuntimeError(f"{report['status']}; retained report: {report['report_path']}")
    return f, report
