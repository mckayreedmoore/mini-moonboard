"""Seed the unchanged frame equations with convex circular-gap contact forces.

The conic calculation selects an initial force guess only. The preserved
circular-gap solver and every existing force/law/floor/domain gate still
determine whether a state is returned. No stiffness or load is changed.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import sys
from pathlib import Path

import clarabel
import numpy as np
from scipy import optimize, sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import both_corner_frame as frame_run
import right_corner_clearance as original
import top_corner_actions as accounting

ORIGINAL_SOLVE = original.solve
ORIGINAL_OFFSETS = frame_run.circular_clearance.clearance_offsets
ROOT = accounting.ROOT
require, sha, read = accounting.require, accounting.sha, accounting.read


def convex_branch(H, D, e, W, k, uni, held, pairs, gaps):
    """Minimize .5 f'(H+1/k)f-e'f + sum(gap*||f_pair||).

    D'f=W retains every body wrench, and unilateral forces are nonnegative.
    Each circular norm has an exact second-order-cone epigraph. Floor tangent
    forces are present only at the supplied bearing footprints.
    """
    positions = np.sort(np.r_[np.flatnonzero(k > 0), held])
    local_pairs = np.searchsorted(positions, pairs)
    require(np.array_equal(positions[local_pairs], pairs), "missing circular rows")
    inverse = np.divide(1.0, k[positions], out=np.zeros(len(positions)),
                        where=k[positions] > 0)
    S = H[np.ix_(positions, positions)] + np.diag(inverse)
    # Native H's roundoff asymmetry is below the preserved reciprocal gate.
    S = (S + S.T) / 2
    n, m, d = len(positions), len(pairs), D.shape[1]
    P = sparse.block_diag((sparse.csc_matrix(S), sparse.csc_matrix((m, m))), format="csc")
    bounded = np.flatnonzero(uni[positions])
    sign = sparse.csc_matrix((-np.ones(len(bounded)),
                             (np.arange(len(bounded)), bounded)), shape=(len(bounded), n + m))
    eq = sparse.hstack((sparse.csc_matrix(D[positions].T), sparse.csc_matrix((d, m))), format="csc")
    soc = sparse.lil_matrix((3 * m, n + m))
    for i, pair in enumerate(local_pairs):
        soc[3 * i, n + i] = -1
        soc[3 * i + 1, pair[0]] = -1
        soc[3 * i + 2, pair[1]] = -1
    A = sparse.vstack((eq, sign, soc.tocsc()), format="csc")
    rhs = np.r_[W, np.zeros(len(bounded) + 3 * m)]
    cones = [clarabel.ZeroConeT(d), clarabel.NonnegativeConeT(len(bounded)),
             *[clarabel.SecondOrderConeT(3) for _ in pairs]]
    settings = clarabel.DefaultSettings()
    settings.verbose = False
    settings.max_iter = 150
    settings.time_limit = 30.0
    settings.tol_gap_abs = 1e-8
    settings.tol_gap_rel = 1e-11
    settings.tol_feas = 1e-11
    result = clarabel.DefaultSolver(sparse.triu(P, format="csc"),
                                    np.r_[-e[positions], gaps], A, rhs, cones, settings).solve()
    status = str(result.status)
    require(status in {"Solved", "AlmostSolved", "InsufficientProgress", "MaxIterations"},
            "conic seed " + status)
    require(len(result.x) == n + m and np.isfinite(result.x).all()
            and np.isfinite(result.z).all(), "nonfinite conic force guess")
    f = np.zeros(len(k))
    f[positions] = np.array(result.x[:n])
    a = -np.array(result.z[:d])
    q = D @ a + e - H @ f
    return f, q, a, {"status": status, "accepted_conic_solution": status == "Solved",
                      "numerical_guess_only": True, "iterations": result.iterations,
                      "solve_time_seconds": result.solve_time,
                      "objective": result.obj_val, "dual_objective": result.obj_val_dual}


def convex_seed(H, D, e, W, k, uni, normals, tangents, targets, gaps, seed):
    bearing = seed[normals] > 0.01
    f, _q, _a, info = convex_branch(H, D, e, W, k, uni, tangents[bearing].ravel(),
                                 targets.reshape(-1, 2), gaps)
    return f, {"bearing_guess_from_original_iterate": bearing.tolist(),
               "floor_forces_n": f[normals].tolist(), "conic": info,
               "seed_is_physical_acceptance": False}


def conic_offsets(f0, response, clearance):
    """Initialize the same disk-projection residual with a small cone QP."""
    size, pairs = len(f0), len(f0) // 2
    scale = np.linalg.norm(response, ord=2)
    require(scale > 0 and clearance > 0, "invalid projection scale")
    soc = sparse.lil_matrix((3 * pairs, size))
    for i in range(pairs):
        soc[3 * i + 1, 2 * i] = -1
        soc[3 * i + 2, 2 * i + 1] = -1
    bounds = np.tile([clearance, 0.0, 0.0], pairs)
    settings = clarabel.DefaultSettings()
    settings.verbose = False
    settings.max_iter = 200
    settings.time_limit = 20.0
    settings.tol_gap_abs = 1e-10
    settings.tol_gap_rel = 1e-11
    settings.tol_feas = 1e-11
    symmetric = (response + response.T) / 2
    result = clarabel.DefaultSolver(
        sparse.triu(sparse.csc_matrix(symmetric / scale), format="csc"), -f0 / scale,
        soc.tocsc(), bounds, [clarabel.SecondOrderConeT(3) for _ in range(pairs)], settings).solve()
    require(np.isfinite(result.x).all(), "nonfinite disk initializer")
    project = frame_run.circular_clearance.project_disks
    step, eye = 1 / scale, np.eye(size)

    def residual(h):
        return h - project(h + step * (f0 - response @ h), clearance)

    def jacobian(h):
        z = (h + step * (f0 - response @ h)).reshape(-1, 2)
        derivative = np.zeros((size, size))
        for i, pair in enumerate(z):
            radius = np.linalg.norm(pair)
            unit = pair / max(radius, 1e-300)
            derivative[2 * i:2 * i + 2, 2 * i:2 * i + 2] = (
                np.eye(2) if radius <= clearance else
                clearance / radius * (np.eye(2) - np.outer(unit, unit)))
        return eye - derivative @ (eye - step * response)

    answer = optimize.least_squares(residual, project(np.array(result.x), clearance),
                                    jac=jacobian, ftol=None, gtol=None,
                                    xtol=1e-14, max_nfev=400)
    error = float(np.max(abs(residual(answer.x))))
    require(error <= 1e-8, "conic-initialized disk residual exceeded unchanged tolerance")
    return answer.x, {"projection_residual_mm": error, "evaluations": int(answer.nfev),
                      "conic_initializer_status": str(result.status),
                      "conic_initializer_iterations": result.iterations,
                      "conic_solution_is_physical_acceptance": False}


def oracle():
    """Analytic mechanics coupon for force, cone direction and dual pose sign."""
    H, D, e = np.zeros((2, 2)), np.eye(2), np.zeros(2)
    W, k = np.array([3.0, 4.0]), np.array([1000.0, 1000.0])
    f, q, _, info = convex_branch(H, D, e, W, k, np.zeros(2, dtype=bool),
                                  np.array([], dtype=int), np.array([[0, 1]]), np.array([1.15]))
    expected = W * (1 / 1000 + 1.15 / 5)
    require(np.max(abs(f - W)) < 1e-8 and np.max(abs(q - expected)) < 1e-7,
            "circular-gap coupon differs from analytic answer")
    f0, q0, _, _ = convex_branch(H, D, np.array([-1.0, 0.0]), np.zeros(2), k,
                                np.ones(2, dtype=bool), np.array([], dtype=int),
                                np.empty((0, 2), dtype=int), np.array([]))
    require(np.max(abs(f0)) < 1e-8 and q0[0] <= 0,
            "open unilateral coupon differs")
    disk, disk_info = conic_offsets(W, 2 * np.eye(2), 1.0)
    require(np.max(abs(disk - W / 5)) < 1e-8, "disk projection coupon differs")
    return {"circular_force_n": f.tolist(), "circular_motion_mm": q.tolist(),
            "analytic_motion_mm": expected.tolist(), "conic": info,
            "open_unilateral_force_n": f0.tolist(), "open_motion_mm": q0.tolist(),
            "disk_offset": disk.tolist(), "disk_projection": disk_info}


def run(output, operators):
    require(not output.exists(), "preserve completed or stopped calculations")
    coupon = oracle()
    seed_reports = []
    disk_reports = []

    def seeded_offsets(f0, response, clearance):
        try:
            return ORIGINAL_OFFSETS(f0, response, clearance)
        except ValueError as error:
            if not str(error).startswith("clearance projection did not converge"):
                raise
            value, report = conic_offsets(f0, response, clearance)
            disk_reports.append({"original_exception": str(error), **report})
            return value, report

    def seeded_solve(H, D, e, W, k, uni, normals, tangents, targets, gaps, seed, worker):
        try:
            result = ORIGINAL_SOLVE(H, D, e, W, k, uni, normals, tangents,
                                    targets, gaps, seed, worker)
            seed_reports.append({"method": "unchanged_original_equations"})
            return result
        except ValueError as initial:
            if str(initial) == "normal active-set cycle":
                trace = initial.__traceback__
                finite = None
                while trace is not None:
                    if trace.tb_frame.f_code is ORIGINAL_SOLVE.__code__:
                        finite = trace.tb_frame.f_locals.get("f")
                    trace = trace.tb_next
                require(finite is not None and np.isfinite(finite).all(),
                        "cycle stopped without a finite force guess")
                guessed, report = convex_seed(H, D, e, W, k, uni, normals, tangents,
                                             targets, gaps, finite)
                seed_reports.append(report)
                try:
                    return ORIGINAL_SOLVE(H, D, e, W, k, uni, normals, tangents,
                                          targets, gaps, guessed, worker)
                except ValueError as final:
                    error = final
            else:
                seed_reports.append({"method": "unchanged_original_equations", "exception": str(initial)})
                error = initial
            # The unchanged parent retains strict-rank failures only after its
            # existing bounded-seating certificate. Expose the original final
            # locals to that path, including its unmodified gate audit.
            trace = error.__traceback__
            saved = {}
            while trace is not None:
                if trace.tb_frame.f_code is ORIGINAL_SOLVE.__code__:
                    saved = trace.tb_frame.f_locals
                trace = trace.tb_next
            f = saved.get("f")  # noqa: F841
            q = saved.get("q")  # noqa: F841
            a = saved.get("a")  # noqa: F841
            audit = saved.get("audit")  # noqa: F841
            raise error

    original.solve = seeded_solve
    frame_run.circular_clearance.clearance_offsets = seeded_offsets
    try:
        frame_run.run(output, service_joints=True, bottom_corners=True,
                      all_two_receiver_clearances=True, bounded_freeplay=True,
                      frame_directory=operators, connection_inputs=operators / "model-inputs.json",
                      qp_seed=True)
    finally:
        original.solve = ORIGINAL_SOLVE
        frame_run.circular_clearance.clearance_offsets = ORIGINAL_OFFSETS
        if output.exists():
            record = {"schema": "convex_numerical_seed/v1", "producer_sha256": sha(Path(__file__)),
                      "clarabel_version": clarabel.__version__, "oracle": coupon,
                      "states_attempted": seed_reports, "disk_initializers": disk_reports,
                      "physical_acceptance_transferred": False,
                      "preserved_gate_producer_sha256": sha(Path(frame_run.__file__)),
                      "preserved_solver_sha256": sha(Path(original.__file__))}
            (output / "conic-seeding.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
            (output / "conic-producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
            target = output / ("comparison.json" if (output / "comparison.json").exists() else "stop.json")
            report = read(target)
            report["source_sha256"][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
            report["numerical_seed_record_sha256"] = sha(output / "conic-seeding.json")
            report["numerical_seed_scope"] = "Convex normal/circular-gap force guess followed by unchanged original equations and gates"
            target.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operators", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle", "analysis slot occupied")
        run(args.output.resolve(), args.operators.resolve())
