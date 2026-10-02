"""Simple static contact frame scenario using the existing elastic reduction.

No CAD, native solver, source changes, or review loop. Each case is independent.
The floor uses one compression spring per existing footprint and a
zero-reference no-slip hypothesis at bearing footprints. This is not a
local floor-pressure or staged contact-history model.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import osqp
from scipy import sparse

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
COMP = BASE / "current-frame-connector-compliance-attempt04"
PINS = {
    "operators.npz": "88a2f2f384edb7be7daa0e20cc87c7b8672ed13e975f8e86afd56d8aeb385b79",
    "row-identities.json": "768d2afe58b48fa482f118f73bb01b8c911d1f937a5891d5c420a0d821b45037",
    "assessment.json": "ae30902f9340875a771d60dab83621ab5e0d6dcadb58c06a35bdb1bc8ac9da6c",
}
SETTINGS = {
    "verbose": False,
    "eps_abs": 1e-9,
    "eps_rel": 1e-9,
    "eps_prim_inf": 1e-9,
    "eps_dual_inf": 1e-9,
    "max_iter": 100000,
    "time_limit": 10.0,
    "polishing": True,
    "adaptive_rho": True,
    "adaptive_rho_interval": 50,
}
FORCE_TOL_N = 0.1
MOMENT_TOL_NMM = 2.0
MOTION_TOL_MM = 1e-5
BEARING_THRESHOLD_N = 0.01
MODELED_MASS_KG = 224.4207766683882
PLANNING_ACCESSORY_MASS_KG = 25.0
DEAD_LOAD_FACTOR = (MODELED_MASS_KG + PLANNING_ACCESSORY_MASS_KG) / MODELED_MASS_KG


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def peak(values):
    return float(np.max(np.abs(values), initial=0))


def solve_branch(H, D, e, W, stiffness, unilateral, tangents, bearing):
    """Dual elastic energy: min .5 f'Sf-e'f, D'f=W, unilateral f>=0."""
    active = np.r_[np.flatnonzero(stiffness > 0), tangents[bearing].ravel()]
    inv_k = np.zeros(len(active))
    finite = stiffness[active] > 0
    inv_k[finite] = 1 / stiffness[active[finite]]
    S = H[np.ix_(active, active)] + np.diag(inv_k)
    bounded = np.flatnonzero(unilateral[active])
    signs = sparse.csc_matrix(
        (np.ones(len(bounded)), (np.arange(len(bounded)), bounded)),
        shape=(len(bounded), len(active)),
    )
    A = sparse.vstack([sparse.csc_matrix(D[active].T), signs], format="csc")
    problem = osqp.OSQP()
    problem.setup(
        P=sparse.triu(sparse.csc_matrix(S), format="csc"),
        q=-e[active],
        A=A,
        l=np.r_[W, np.zeros(len(bounded))],
        u=np.r_[W, np.full(len(bounded), np.inf)],
        **SETTINGS,
    )
    result = problem.solve(raise_error=False)
    if result.info.status_val != 1:
        raise RuntimeError(f"QP {result.info.status}; no accepted response")
    f = np.zeros(len(H))
    f[active] = result.x
    a = -result.y[: D.shape[1]]
    q = D @ a + e - H @ f
    return f, a, q, int(result.info.iter)


def solve_case(H, D, e, W, stiffness, unilateral, normals, tangents):
    # ponytail: iterate bearing cells; stop on a cycle instead of adding a
    # combinatorial floor-history selector to this static scenario.
    bearing = np.ones(len(normals), dtype=bool)
    seen = set()
    history = []
    for step in range(20):
        key = tuple(np.flatnonzero(bearing))
        if key in seen:
            raise RuntimeError(f"bearing-set cycle after {step} iterations: {history}")
        seen.add(key)
        f, a, q, iterations = solve_branch(
            H, D, e, W, stiffness, unilateral, tangents, bearing
        )
        next_bearing = f[normals] > BEARING_THRESHOLD_N
        history.append(
            {
                "bearing_cells": int(bearing.sum()),
                "qp_iterations": iterations,
                "changed_cells": int(np.count_nonzero(bearing != next_bearing)),
            }
        )
        if np.array_equal(next_bearing, bearing):
            expected = stiffness * np.where(unilateral, np.maximum(q, 0), q)
            finite = stiffness > 0
            balance = (D.T @ f - W).reshape(-1, 6)
            metrics = {
                "body_force_residual_n": peak(balance[:, :3]),
                "body_moment_residual_nmm": 1000 * peak(balance[:, 3:]),
                "spring_law_residual_n": peak(f[finite] - expected[finite]),
                "minimum_unilateral_force_n": float(f[unilateral].min()),
                "held_tangent_motion_mm": peak(q[tangents[bearing]]),
                "released_tangent_force_n": peak(f[tangents[~bearing]]),
                "minimum_bearing_normal_force_n": float(f[normals[bearing]].min()),
                "maximum_unilateral_motion_mm": peak(q[unilateral]),
            }
            checks = {
                "body_force": metrics["body_force_residual_n"] <= FORCE_TOL_N,
                "body_moment": metrics["body_moment_residual_nmm"] <= MOMENT_TOL_NMM,
                "spring_law": metrics["spring_law_residual_n"] <= FORCE_TOL_N,
                "nonnegative": metrics["minimum_unilateral_force_n"] >= -FORCE_TOL_N,
                "held_floor": metrics["held_tangent_motion_mm"] <= MOTION_TOL_MM,
                "released_floor": metrics["released_tangent_force_n"] == 0,
                "source_law_domain": metrics["maximum_unilateral_motion_mm"] <= 10,
            }
            return (
                f,
                a,
                q,
                bearing,
                {
                    "status": "PASS_STATIC_SCENARIO_BALANCE_AND_LAWS"
                    if all(checks.values())
                    else "STOP_STATIC_SCENARIO_CHECK",
                    "checks": checks,
                    "metrics": metrics,
                    "bearing_iteration_history": history,
                },
            )
        bearing = next_bearing
    raise RuntimeError("bearing-set iteration limit")


def lump_floor(raw_H, D, e, W, rows):
    """Replace each footprint's distributed support rows with three means.

    Weights are the normal spring stiffness fractions. A positive resultant
    maps back to positive distributed normal forces. The mean displacement
    law replaces individual cell laws; local lift/pressure is not resolved.
    """
    floor = [r for r in rows if r["ownership"]["second_body"] == "floor"]
    retained = [r for r in rows if r["ownership"]["second_body"] != "floor"]
    members = sorted({r["ownership"]["first_body"] for r in floor})
    by_id = {r["row_id"]: r["row"] for r in rows}
    T = np.zeros((len(retained) + 3 * len(members), len(rows)))
    k = [r["law"]["stiffness_N_per_mm"] for r in retained]
    uni = [r["family"] == "unilateral_springa" for r in retained]
    T[np.arange(len(retained)), [r["row"] for r in retained]] = 1
    normals, tangents, footprint_records = [], [], []
    for member in members:
        cells = [
            r
            for r in floor
            if r["ownership"]["first_body"] == member
            and r["ownership"]["role"] == "floor_normal"
        ]
        ids = np.array([r["row"] for r in cells])
        cell_k = np.array([r["law"]["stiffness_N_per_mm"] for r in cells])
        weights = cell_k / cell_k.sum()
        normal = len(k)
        normals.append(normal)
        tangents.append([normal + 1, normal + 2])
        T[normal, ids] = weights
        for component, axis in enumerate([2, 3], start=1):
            indices = [
                by_id[r["row_id"] + "_friction/local-dof-" + str(axis)] for r in cells
            ]
            T[normal + component, indices] = weights
        k.extend([float(cell_k.sum()), 0.0, 0.0])
        uni.extend([True, False, False])
        footprint_records.append(
            {
                "member_id": member,
                "source_cell_count": len(cells),
                "resultant_point_xyz_mm": (
                    weights @ np.array([r["ownership"]["point_mm"] for r in cells])
                ).tolist(),
                "normal_stiffness_n_per_mm": float(cell_k.sum()),
            }
        )
    return (
        T @ raw_H @ T.T,
        T @ D,
        T @ e,
        W,
        np.array(k),
        np.array(uni),
        np.array(normals),
        np.array(tangents),
        T,
        footprint_records,
    )


def known_answer():
    """Small mechanics oracle: one six-coordinate body on one floor cell."""
    D = np.zeros((6, 6))
    D[0, 2] = 1
    D[1, 0] = 1
    D[2, 1] = 1
    D[3:, 3:] = np.eye(3)
    H = np.eye(6) * 0.001
    k = np.array([1000.0, 0, 0, 1000.0, 1000.0, 1000.0])
    uni = np.array([True, False, False, False, False, False])
    W = np.array([12.0, -8.0, 100.0, 0, 0, 0])
    f, _, q, mask, report = solve_case(
        H, D, np.zeros(6), W, k, uni, np.array([0]), np.array([[1, 2]])
    )
    assert report["status"] == "PASS_STATIC_SCENARIO_BALANCE_AND_LAWS"
    np.testing.assert_allclose(f[:3], [100, 12, -8], atol=1e-5)
    np.testing.assert_allclose(q[:3], [0.1, 0, 0], atol=1e-5)
    assert mask.tolist() == [True]
    # No downward load: a floor normal cannot supply a tensile reaction.
    W[2] = -100
    try:
        solve_branch(H, D, np.zeros(6), W, k, uni, np.array([[1, 2]]), mask)
    except RuntimeError:
        return "PASS_COMPRESSION_NO_SLIP_AND_TENSION_REFUSAL_ORACLE"
    raise AssertionError("tensile floor reaction was accepted")


def run():
    for name, digest in PINS.items():
        if sha(COMP / name) != digest:
            raise ValueError(f"changed source: {name}")
    assessment = json.loads((COMP / "assessment.json").read_text())
    rows = json.loads((COMP / "row-identities.json").read_text())
    with np.load(COMP / "operators.npz", allow_pickle=False) as data:
        raw_H, D, e, W = (data[name] for name in ["H", "D", "e", "W"])
    raw_H, D, e, W, stiffness, unilateral, normals, tangents, T, footprints = (
        lump_floor(raw_H, D, e, W, rows)
    )
    H = (raw_H + raw_H.T) / 2
    report = {
        "schema": "simple_static_frame_scenario/v1",
        "candidate": assessment["candidate"],
        "revision_id": assessment["geometry_revision_id"],
        "source_sha256": PINS,
        "producer_sha256": sha(Path(__file__)),
        "known_answer": known_answer(),
        "settings": SETTINGS,
        "floor_footprints": footprints,
        "modeled_mass_kg": MODELED_MASS_KG,
        "planning_accessory_mass_kg": PLANNING_ACCESSORY_MASS_KG,
        "dead_load_factor": DEAD_LOAD_FACTOR,
        "assumptions": [
            "existing conditional elastic members and connector stiffness",
            "25 kg accessory allowance distributed in proportion to modeled body masses; analytical placement only",
            "compression-only face/floor springs and tension-only axial ties",
            "one uniform resultant spring per existing floor footprint",
            "no-slip floor at bearing footprints with zero tangential reference",
            "independent full static loads; no staged contact history",
            "symmetric elastic compliance; no preload or timber-face friction",
        ],
        "mechanical_acceptance": False,
        "engineering_mvp_complete": False,
        "physical_release": False,
        "cases": [],
    }
    outputs = {}
    start = time.monotonic()
    for column in range(0, 12, 2):
        case = assessment["load_columns"][column]["case_id"]
        try:
            f, a, q, mask, result = solve_case(
                H,
                D,
                DEAD_LOAD_FACTOR * e[:, column] + e[:, column + 1],
                DEAD_LOAD_FACTOR * W[:, column] + W[:, column + 1],
                stiffness,
                unilateral,
                normals,
                tangents,
            )
            result["raw_vs_symmetric_motion_mm"] = peak((raw_H - H) @ f)
            result["peak_body_translation_mm"] = float(
                np.linalg.norm(a.reshape(-1, 6)[:, :3], axis=1).max()
            )
            result["peak_body_rotation_degrees"] = float(
                np.rad2deg(np.linalg.norm(a.reshape(-1, 6)[:, 3:], axis=1).max() / 1000)
            )
            result["peak_scalar_connector_force_n"] = peak(f)
            outputs.update(
                {
                    case + "_force_n": T.T @ f,
                    case + "_lumped_force_n": f,
                    case + "_rigid_coordinates": a,
                    case + "_motion_mm": q,
                    case + "_bearing_mask": mask,
                }
            )
        except RuntimeError as error:
            result = {"status": "STOP_STATIC_SCENARIO", "reason": str(error)}
        report["cases"].append(dict(case_id=case, **result))
        print(case, result["status"], flush=True)
    report["elapsed_seconds"] = time.monotonic() - start
    report["source_unchanged"] = all(
        sha(COMP / name) == digest for name, digest in PINS.items()
    )
    if not report["source_unchanged"]:
        raise RuntimeError("source changed during static calculation")
    np.savez_compressed(HERE / "simple-frame-response.npz", **outputs)
    report["response_sha256"] = sha(HERE / "simple-frame-response.npz")
    (HERE / "simple-frame-results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--known-answer", action="store_true")
    args = parser.parse_args()
    if args.known_answer:
        print(known_answer())
    else:
        lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
        with lock.open("a") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if (
                json.loads(lock.with_suffix(".json").read_text())["slot"]["state"]
                != "idle"
            ):
                raise RuntimeError("shared analysis slot is occupied")
            run()
