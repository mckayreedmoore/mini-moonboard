"""Bound the fixed-force seating freedom of one saved finite-clearance state.

This calculation never solves for frame forces or changes a branch. Circular
holes are enclosed by component boxes only to certify boundedness. Box vertices
are not proposed circular-law states. The callable certificate also returns the
small nullspace, LP inequalities and dual bounds for reuse by the parent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import scipy
from scipy import linalg, optimize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRAME = HERE / "corner-frame-attempt01"
SOURCE = HERE / "two-receiver-frame-attempt02"
BASELINE = HERE / "all-outer-corner-frame-attempt01"
BASELINE_PINS = {
    "comparison.json": "ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3",
    "response.npz": "aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901",
}
FORCE_TOL_N = 1e-4
MOTION_TOL_MM = 1e-8
RANK_RTOL = 1e-11
LP_OPTIONS = {"primal_feasibility_tolerance": 1e-9, "dual_feasibility_tolerance": 1e-9}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def peak(values):
    return float(np.max(np.abs(values), initial=0.0))


def nullspace(matrix, columns, *, normalize=False):
    """Use a direct SVD, retaining the singular values and explicit cutoff."""
    matrix = np.asarray(matrix, dtype=float).reshape(-1, columns)
    if normalize:
        norms = np.linalg.norm(matrix, axis=1)
        matrix = matrix[norms > 0] / norms[norms > 0, None]
    if not len(matrix):
        return np.eye(columns), {"rank": 0, "cutoff": 0.0, "singular_values": []}
    _, singular, vt = linalg.svd(
        matrix, full_matrices=len(matrix) < columns, check_finite=False
    )
    cutoff = RANK_RTOL * singular[0]
    rank = int(np.count_nonzero(singular > cutoff))
    return vt[rank:].T, {
        "rank": rank,
        "cutoff": float(cutoff),
        "singular_values": singular.tolist(),
    }


def finite_clearance_certificate(
    D, q, f, k, unilateral, floor_normals, floor_tangents,
    clearance_targets, clearance_gaps, W, *, movement_maps=None,
):
    """Return ``(report, arrays)`` for one fixed-force state, at recorded tolerances.

    ``delta_a = N @ z`` preserves active finite-law motions and held floor
    tangents. Inactive unilateral rows obey ``q + D @ delta_a <= 0``; free
    circular pairs obey disks. LPs use a conservative outer component box for
    each disk, inflated by the stated numerical motion tolerance. Every null
    coordinate must have finite extrema and checked dual bounds. An unbounded
    LP instead produces a concrete recession direction preserving disk motion.

    ``movement_maps`` maps labels to matrices with ``D.shape[1]`` columns. Each
    matrix maps rigid coordinate increments to an observable, e.g. translation
    in mm or rotation in rad. Bounds are increments about the supplied state.
    No returned flag accepts a complete joint, frame branch or native result.
    """
    D, q, f, k, W = [np.asarray(x, dtype=float) for x in (D, q, f, k, W)]
    uni = np.asarray(unilateral, dtype=bool)
    normals = np.asarray(floor_normals, dtype=int)
    tangents = np.asarray(floor_tangents, dtype=int)
    targets = np.asarray(clearance_targets, dtype=int)
    gaps = np.asarray(clearance_gaps, dtype=float)
    pairs = targets.reshape(-1, 2)
    columns = D.shape[1]
    require(0 < columns <= 300, "certificate is limited to 300 rigid columns")
    require(D.shape[0] == len(q) == len(f) == len(k) == len(uni), "row mismatch")
    require(W.shape == (columns,), "external wrench shape mismatch")
    require(len(pairs) == len(gaps) and len(np.unique(targets)) == len(targets), "pair mismatch")
    require(np.all(np.isfinite(D)) and all(np.all(np.isfinite(x)) for x in (q, f, k, W, gaps)), "nonfinite input")
    require(np.all(k >= 0) and np.all(k[targets] > 0) and np.all(gaps >= 0), "invalid stiffness or gap")
    require(np.all(~uni[targets]) and np.all(uni[normals]), "incorrect circular or floor family")
    require(tangents.shape == (len(normals), 2) and np.all(k[tangents] == 0), "floor tangent mismatch")

    pair_forces = np.linalg.norm(f[pairs], axis=1)
    radii = np.linalg.norm(q[pairs], axis=1)
    free = pair_forces <= FORCE_TOL_N
    free_rows = pairs[free].ravel()
    bilateral = np.flatnonzero(~uni & (k > 0))
    active = np.flatnonzero(uni & (f > FORCE_TOL_N))
    inactive = np.setdiff1d(np.flatnonzero(uni), active)
    held = tangents[np.isin(normals, active)].ravel()
    released = np.setdiff1d(tangents.ravel(), held)
    fixed_rows = np.setdiff1d(np.union1d(bilateral, np.r_[active, held]), free_rows)
    N, row_svd = nullspace(D[fixed_rows], columns, normalize=True)
    m = N.shape[1]
    require(peak(D[fixed_rows] @ N) < MOTION_TOL_MM, "nullspace does not preserve fixed motions")
    require(np.all(radii[free] <= gaps[free] + MOTION_TOL_MM), "free pair outside its disk")
    require(np.all(q[inactive] <= MOTION_TOL_MM), "inactive unilateral row is not open")

    expected = k * np.where(uni, np.maximum(q, 0.0), q)
    tangent_parts = []
    ordinary = np.setdiff1d(np.union1d(bilateral, active), targets)
    tangent_parts.append(np.sqrt(k[ordinary, None]) * D[ordinary])
    circular_stiffness = []
    for i, pair in enumerate(pairs):
        require(np.isclose(k[pair[0]], k[pair[1]], rtol=1e-12, atol=0), "unequal circular component stiffness")
        radius, gap, spring = radii[i], gaps[i], k[pair[0]]
        unit = q[pair] / max(radius, 1e-300)
        expected[pair] = spring * max(radius - gap, 0.0) * unit
        if not free[i]:
            require(radius > gap, "force-bearing pair has no positive tangent")
            transverse = spring * (1 - gap / radius)
            perpendicular = np.array([-unit[1], unit[0]])
            tangent_parts.append(
                np.vstack((np.sqrt(spring) * unit, np.sqrt(transverse) * perpendicular)) @ D[pair]
            )
            circular_stiffness.append({
                "pair_index": i, "radial_n_per_mm": float(spring),
                "transverse_n_per_mm": float(transverse),
            })
    # Hard held-floor constraints receive a finite scale solely for the SVD;
    # their exact equality rows are already present in the fixed-motion set.
    tangent_parts.append(np.sqrt(k.max()) * D[held])
    tangent_N, tangent_svd = nullspace(np.vstack(tangent_parts), columns)
    balance = D.T @ f - W
    require(peak(balance.reshape(-1, 6)[:, :3]) < 0.1 and 1000 * peak(balance.reshape(-1, 6)[:, 3:]) < 2, "body imbalance")
    require(peak(f[k > 0] - expected[k > 0]) < FORCE_TOL_N and np.min(f[uni], initial=0) >= -FORCE_TOL_N, "finite law failure")
    require(peak(q[held]) < MOTION_TOL_MM and peak(f[released]) == 0, "floor law failure")
    require(np.max(q[uni], initial=0) <= 10, "positive spring domain exceeded")

    # The exact disk set is contained in this outer polyhedron. Inflation only
    # enlarges that polyhedron; it cannot create a false finite bound.
    DN = D @ N
    A = np.vstack((DN[inactive], DN[free_rows], -DN[free_rows]))
    box_radius = np.repeat(gaps[free], 2)
    b = np.r_[-q[inactive], box_radius - q[free_rows], box_radius + q[free_rows]] + MOTION_TOL_MM
    arrays = {
        "nullspace": N, "fixed_rows": fixed_rows, "inactive_rows": inactive,
        "free_pairs": pairs[free], "free_pair_indices": np.flatnonzero(free),
        "A_ub": A, "b_ub": b, "tangent_nullspace": tangent_N,
    }
    calls = 0
    dual_records = []
    rays = []

    def extremum(c, label, retain=False):
        nonlocal calls
        c = np.asarray(c, dtype=float)
        scale = peak(c)
        if m == 0 or scale == 0:
            return {"status": "finite", "maximum": 0.0}, np.zeros(m)
        calls += 1
        result = optimize.linprog(-c / scale, A_ub=A, b_ub=b, bounds=[(None, None)] * m, method="highs", options=LP_OPTIONS)
        if result.status == 3:
            # Obtain a recession ray with positive projection in this objective.
            calls += 1
            ray_lp = optimize.linprog(np.zeros(m), A_ub=np.vstack((A, -c[None] / scale)), b_ub=np.r_[np.zeros(len(b)), -1.0], bounds=[(None, None)] * m, method="highs", options=LP_OPTIONS)
            require(ray_lp.success, "unbounded LP has no recovered recession witness")
            ray = ray_lp.x / peak(ray_lp.x)
            delta = N @ ray
            require(np.max(A @ ray, initial=0) < 1e-8 and peak(D[free_rows] @ delta) < 1e-8, "invalid disk-preserving recession ray")
            require(peak(D[fixed_rows] @ delta) < 1e-8 and c @ ray > 0, "invalid fixed-law recession ray")
            arrays[f"recession_ray_{len(rays)}"] = delta
            rays.append({"objective": label, "null_direction": ray.tolist(), "external_work_nmm_per_unit": float(W @ delta), "maximum_inactive_direction_mm": float(np.max(D[inactive] @ delta, initial=0)), "maximum_disk_direction_mm": peak(D[free_rows] @ delta)})
            return {"status": "unbounded", "maximum": None}, None
        require(result.success, f"LP {label} unresolved: {result.message}")
        # y >= 0, A.T y = c implies c.z <= b.y for every feasible z.
        y = -scale * result.ineqlin.marginals
        primal = float(c @ result.x)
        upper = float(b @ y)
        dual_error = peak(A.T @ y - c)
        require(np.min(y, initial=0) >= -1e-9 * max(scale, 1) and dual_error < 1e-8 * max(scale, 1), f"LP {label} dual bound unresolved")
        require(np.max(A @ result.x - b, initial=0) < 1e-8 and abs(upper - primal) < 1e-7 * max(abs(primal), 1), f"LP {label} bound mismatch")
        if retain:
            dual_records.append(y)
        return {"status": "finite", "maximum": upper, "primal_value": primal, "dual_residual": dual_error, "minimum_dual": float(np.min(y, initial=0)), "primal_violation_mm": float(np.max(A @ result.x - b, initial=0))}, result.x

    coordinate_bounds, extrema = [], []
    for j in range(m):
        c = np.eye(m)[j]
        lo, xlo = extremum(-c, f"null_{j}_minimum", retain=True)
        hi, xhi = extremum(c, f"null_{j}_maximum", retain=True)
        coordinate_bounds.append({"coordinate": j, "minimum": -lo["maximum"] if lo["status"] == "finite" else None, "maximum": hi["maximum"], "lower_certificate": lo, "upper_certificate": hi})
        extrema.extend(x for x in (xlo, xhi) if x is not None)
    if dual_records:
        arrays["null_coordinate_dual_multipliers"] = np.array(dual_records)
    arrays["null_coordinate_extrema"] = np.array(extrema).reshape(-1, m) if m else np.empty((0, 0))
    bounded = all(x["minimum"] is not None and x["maximum"] is not None for x in coordinate_bounds)

    movements = {}
    if bounded:
        for label, mapping in (movement_maps or {}).items():
            mapping = np.asarray(mapping, dtype=float)
            require(mapping.ndim == 2 and mapping.shape[1] == columns and np.all(np.isfinite(mapping)), "movement map mismatch")
            projected = mapping @ N
            intervals = []
            for j, row in enumerate(projected):
                lo, _ = extremum(-row, f"{label}_{j}_minimum")
                hi, _ = extremum(row, f"{label}_{j}_maximum")
                intervals.append([-lo["maximum"], hi["maximum"]])
            max_components = np.max(np.abs(intervals), axis=1)
            movements[label] = {"component_increment_intervals": intervals, "euclidean_increment_upper_bound": float(np.linalg.norm(max_components))}

    work_projection = W @ N
    work_min, _ = extremum(-work_projection, "external_work_minimum")
    work_max, _ = extremum(work_projection, "external_work_maximum")

    # Demonstrate nonuniqueness with a shortened segment that stays in actual
    # disks. No outer-box endpoint is admitted as a circular-law state.
    disk_witness = None
    if bounded and extrema:
        for endpoint in sorted(extrema, key=lambda x: np.linalg.norm(N @ x), reverse=True):
            dq = DN @ endpoint
            limit = 1.0
            for i in inactive:
                if dq[i] > 1e-11:
                    limit = min(limit, max(0.0, -q[i]) / dq[i])
            for pair, gap in zip(pairs[free], gaps[free], strict=True):
                u, v = q[pair], dq[pair]
                aa, bb, cc = v @ v, 2 * u @ v, u @ u - gap**2
                if aa > 1e-22:
                    # Negative cc means the origin lies in the actual disk.
                    require(cc <= 1e-8, "witness origin outside disk")
                    limit = min(limit, max(0.0, (-bb + np.sqrt(max(0, bb**2 - 4 * aa * min(cc, 0)))) / (2 * aa)))
            z = 0.5 * limit * endpoint
            delta = N @ z
            if np.linalg.norm(delta) <= 1e-5:
                continue
            moved = q + D @ delta
            circular_excess = np.linalg.norm(moved[pairs[free]], axis=1) - gaps[free]
            require(np.max(circular_excess, initial=0) <= MOTION_TOL_MM and np.max(moved[inactive], initial=0) <= MOTION_TOL_MM, "shortened witness outside exact disk/unilateral constraints")
            arrays["disk_witness_delta_a"] = delta
            arrays["disk_witness_q"] = moved
            disk_witness = {"null_coordinates": z.tolist(), "rigid_coordinate_increment_norm_mm": float(np.linalg.norm(delta)), "maximum_free_disk_excess_mm": float(np.max(circular_excess)), "fixed_motion_change_mm": peak(D[fixed_rows] @ delta), "maximum_inactive_q_mm": float(np.max(moved[inactive], initial=0)), "external_work_nmm": float(W @ delta), "is_accepted_frame_state": False}
            break

    report = {
        "schema": "finite_clearance_fixed_force_certificate/v1",
        "classification": "BOUNDED_FIXED_FORCE_SEATING_FREEDOM" if bounded and m else "FIXED_FORCE_UNIQUE" if bounded else "UNBOUNDED_FIXED_FORCE_MECHANISM",
        "bounded": bounded, "linear_fixed_motion_unique": m == 0,
        "fixed_force_unique": True if m == 0 else False if disk_witness is not None else None,
        "nonunique_disk_witness_found": disk_witness is not None,
        "force_bearing_row_svd": row_svd, "actual_active_tangent_svd": tangent_svd,
        "force_bearing_rank_gate_satisfied": row_svd["rank"] == columns,
        "strict_active_tangent_stability_established": tangent_svd["rank"] == columns,
        "tangent_rank_matches_fixed_row_rank": tangent_svd["rank"] == row_svd["rank"],
        "nullity": m, "free_circular_pair_count": int(free.sum()),
        "bearing_circular_pair_count": int((~free).sum()),
        "active_unilateral_row_count": len(active), "inactive_unilateral_row_count": len(inactive),
        "held_floor_tangent_count": len(held), "fixed_row_count": len(fixed_rows),
        "circular_tangent_stiffness": circular_stiffness,
        "numerical_tolerances": {"force_n": FORCE_TOL_N, "outer_constraint_inflation_mm": MOTION_TOL_MM, "relative_svd_cutoff": RANK_RTOL, "lp_options": LP_OPTIONS},
        "state_gates": {"force_balance_n": peak(balance.reshape(-1, 6)[:, :3]), "moment_balance_nmm": 1000 * peak(balance.reshape(-1, 6)[:, 3:]), "finite_law_error_n": peak(f[k > 0] - expected[k > 0]), "fixed_null_motion_error_mm": peak(D[fixed_rows] @ N), "maximum_free_pair_force_n": float(np.max(pair_forces[free], initial=0))},
        "null_coordinate_bounds": coordinate_bounds, "movement_bounds": movements,
        "external_work_projection_n": work_projection.tolist(),
        "external_work_increment_interval_nmm": [-work_min["maximum"] if work_min["status"] == "finite" else None, work_max["maximum"]],
        "recession_directions": rays, "disk_seating_witness": disk_witness,
        "lp_call_count": calls, "complete_joint_acceptance": False,
        "formal_acceptance": False, "native_acceptance": False,
        "frame_state_accepted": False, "baseline_replaced": False, "physical_release": False,
    }
    return report, arrays


def movement_maps(model, retained):
    """Rigid body and common-datum receiver differences, using physical geometry."""
    names = model["body_names"]
    columns = 6 * len(names)
    centers = {b: np.mean([model["physical_node_coordinates_mm"][str(n)] for n in model["body_nodes"][b]], axis=0) for b in names}
    maps, descriptions = {}, {}

    def at_point(body, point):
        matrix = np.zeros((3, columns))
        i = names.index(body)
        matrix[:, 6 * i:6 * i + 3] = np.eye(3)
        arm = np.asarray(point) - centers[body]
        matrix[:, 6 * i + 3:6 * i + 6] = np.stack([np.cross(e, arm) / 1000 for e in np.eye(3)], axis=1)
        return matrix

    def rotation(body):
        matrix = np.zeros((3, columns))
        i = names.index(body)
        matrix[:, 6 * i + 3:6 * i + 6] = np.eye(3) / 1000
        return matrix

    for body in names:
        maps[f"body/{body}/centroid_translation_mm"] = at_point(body, centers[body])
        maps[f"body/{body}/rotation_rad"] = rotation(body)
    groups = {}
    for row in retained:
        o = row["ownership"]
        a, b = o["first_body"], o["second_body"]
        if "point_mm" in o:
            groups.setdefault(tuple(sorted((a, b))), []).append(o["point_mm"])
    for (a, b), points in groups.items():
        datum = np.mean(points, axis=0)
        label = f"interface/{a}--{b}"
        maps[label + "/translation_mm"] = at_point(b, datum) - at_point(a, datum)
        maps[label + "/rotation_rad"] = rotation(b) - rotation(a)
        descriptions[label] = {"first_body": a, "second_body": b, "common_datum_mm": datum.tolist()}
    return maps, descriptions


def run(output):
    """Consume only the completed parent packet and calculate its terminal state."""
    import simple_frame as frame

    require(output.resolve() == (HERE / "bounded-clearance-attempt01").resolve(), "output must stay in the owned attempt directory")
    require(not output.exists(), "preserve existing bounded-clearance evidence")
    for name in ("stop.json", "unaccepted-iterate.npz", "producer.py.snapshot"):
        require((SOURCE / name).is_file(), "parent diagnostic packet incomplete")
    stop = read(SOURCE / "stop.json")
    require(sha(SOURCE / "producer.py.snapshot") == stop["producer_sha256"], "parent snapshot does not match stop producer hash")
    require(stop["case_id"] == "a12-rear" and stop["gap_scale"] == 1.0 and stop["terminal_exception"] == "unrestrained rigid coordinate", "different terminal state")
    require(stop["last_iterate_is_accepted"] is False, "diagnostic packet is not an unaccepted state")
    pins = {SOURCE / n: sha(SOURCE / n) for n in ("stop.json", "unaccepted-iterate.npz", "producer.py.snapshot")}
    for path in (FRAME / "operators.npz", FRAME / "row-identities.json", FRAME / "model.json", FRAME / "frame-results.json", Path(frame.__file__)):
        digest = stop["source_sha256"][str(path.relative_to(ROOT))]
        require(sha(path) == digest, "consumed source changed: " + str(path))
        pins[path] = digest
    for name, digest in BASELINE_PINS.items():
        require(sha(BASELINE / name) == digest, "retained six-joint baseline changed")
        pins[BASELINE / name] = digest
    connections_path = HERE.parent / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
    pins[connections_path] = stop["source_sha256"][str(connections_path.relative_to(ROOT))]
    require(sha(connections_path) == pins[connections_path], "bolt inventory changed")
    with np.load(SOURCE / "unaccepted-iterate.npz", allow_pickle=False) as saved:
        state = {name: saved[name].copy() for name in saved.files}
    rows = read(FRAME / "row-identities.json")
    with np.load(FRAME / "operators.npz", allow_pickle=False) as operators:
        H, D, e, W, k, uni, normals, tangents, _, floors = frame.lump_floor(*[operators[n] for n in ("H", "D", "e", "W")], rows)
    H = (H + H.T) / 2
    for name, reconstructed in (("k", k), ("unilateral", uni), ("floor_normals", normals), ("floor_tangents", tangents)):
        require(np.array_equal(state[name], reconstructed), "saved/reconstructed " + name + " mismatch")
    baseline = read(FRAME / "frame-results.json")
    index = next(i for i, case in enumerate(baseline["cases"]) if case["case_id"] == stop["case_id"])
    load_e = baseline["dead_load_factor"] * e[:, 2 * index] + e[:, 2 * index + 1]
    load_W = baseline["dead_load_factor"] * W[:, 2 * index] + W[:, 2 * index + 1]
    q_error = peak(D @ state["a"] + load_e - H @ state["f"] - state["q"])
    require(q_error < MOTION_TOL_MM, "saved motion does not reconstruct")
    retained = [r for r in rows if r["ownership"]["second_body"] != "floor"]
    connections = {c["axis_id"]: c for c in read(connections_path)["connections"] if c["kind"] == "candidate_bolt"}
    pairs = state["clearance_targets"].reshape(-1, 2)
    axes = [retained[int(pair[0])]["row_id"].rsplit("/", 1)[0] for pair in pairs]
    expected_axes = {axis for axis, c in connections.items() if len(c["receiver_member_ids"]) == 2}
    require(len(axes) == len(set(axes)) == 88 and set(axes) == expected_axes, "88 independent bolt pairs not preserved")
    continuous = [axis for axis, c in connections.items() if len(c["receiver_member_ids"]) != 2]
    require(len(continuous) == 4, "continuous bolt inventory changed")
    for pair in pairs:
        require(retained[int(pair[0])]["row_id"] == retained[int(pair[1])]["row_id"], "mispaired circular components")
    screw = np.array([i for i, r in enumerate(retained) if r["ownership"]["role"] in ("panel_screw_lateral_plane", "non_qualifying_parametric_screw_withdrawal")])
    require(len(screw) == 198 and peak(k[screw] - 2689.679) < 0.0005, "Hillman laws changed")
    retained_axes = sorted({r["row_id"].rsplit("/", 1)[0] for r in retained if r["ownership"]["role"] == "retained_bolt_lateral_plane"})
    require(len(retained_axes) == 12, "retained frame bolt inventory changed")
    model = read(FRAME / "model.json")
    maps, descriptions = movement_maps(model, retained)
    report, arrays = finite_clearance_certificate(D, state["q"], state["f"], k, uni, normals, tangents, state["clearance_targets"], state["clearance_gaps"], load_W, movement_maps=maps)
    require(report["force_bearing_row_svd"]["rank"] == stop["audit_if_available"]["force_bearing_rigid_rank"], "rank differs from consumed terminal audit")
    report.update({
        "case_id": stop["case_id"], "gap_scale": stop["gap_scale"],
        "consumed_parent_audit": stop["audit_if_available"],
        "consumed_parent_producer_sha256": stop["producer_sha256"],
        "consumed_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "saved_motion_reconstruction_error_mm": q_error,
        "body_names_in_column_order": model["body_names"],
        "interface_datums": descriptions, "floor_footprints": floors,
        "clearance_axis_gaps_mm": dict(zip(axes, state["clearance_gaps"].tolist(), strict=True)),
        "continuous_zero_gap_candidate_bolts": continuous,
        "retained_zero_gap_frame_bolt_lateral_axes": retained_axes,
        "panel_screw_stiffness_n_per_mm": float(k[screw[0]]),
        "versions": {"numpy": np.__version__, "scipy": scipy.__version__},
        "producer_sha256": sha(Path(__file__)),
        "command": "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 uv run --offline --no-project --python 3.12 --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/bounded_clearance.py",
    })
    arrays.update({"saved_a": state["a"], "saved_q": state["q"], "saved_f": state["f"], "external_W": load_W})
    for path, digest in pins.items():
        require(sha(path) == digest, "consumed input changed during calculation")
    output.mkdir()
    np.savez_compressed(output / "certificate.npz", **arrays)
    report["certificate_sha256"] = sha(output / "certificate.npz")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (output / "result.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: report[k] for k in ("classification", "nullity", "nonunique_disk_witness_found", "external_work_increment_interval_nmm", "lp_call_count")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "bounded-clearance-attempt01")
    run(parser.parse_args().output)
