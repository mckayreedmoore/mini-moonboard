"""Prepare one pinned A12 fixed-active-set KKT refinement; never run it here.

The CLI only freezes/verifies the provisional active-set proposal. A parent
wrapper may import ``one_shot_refine`` after its own freeze and serialization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import scipy
from scipy import linalg


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
PREP = BASE / "current-a12-fixed-episode-dual-qp-preparation-attempt01"
ATTEMPT02 = BASE / "current-a12-fixed-episode-dual-qp-known-answer-attempt02"
TINY = BASE / "current-fixed-active-kkt-refinement-fixture-attempt01"
COMP = BASE / "current-frame-connector-compliance-attempt04"
ANSWER = PREP / "known-answer.npz"
CANDIDATE = ATTEMPT02 / "diagnostic-candidate.npz"
OUTPUT = HERE / "readiness.json"

PROVISIONAL_BOUND_FORCE_TOL_N = 1.0e-4
KKT_RANK_RELATIVE_CUTOFF = 1.0e-12
KKT_RESIDUAL_TOL = 2.0e-10
ACTIVE_PRIMAL_DUAL_TOL = 2.0e-9

PINNED = {
    "preparation_known_answer": "507588fa63144656d2db90b8222fd7fc091b0b1102539fbfdbb55c075e3269ba",
    "preparation_assessment": "b2d7ff17393d1afc66728d7de9d890ac26ba57aed08035a0ce0b27736469e4df",
    "preparation_producer": "9e8ad7d39e1155cfe740a47247c3d8115c341c6b691a0b2ba72fe7bc2ee0ca48",
    "raw_operators": "88a2f2f384edb7be7daa0e20cc87c7b8672ed13e975f8e86afd56d8aeb385b79",
    "attempt02_assessment": "ca52e94df2937fee7a2cf7a310c77f5251a3a6087a2ea930e855aee5c01205a0",
    "attempt02_candidate": "6b19fd37ce22d0e5fea46d0610804e4e51b7eaecacbfa9dfd15242b9cdc6c29b",
    "attempt02_frozen_inputs": "4efffd20b358a0476804e456d94206798498577308c8f65749660009ddda2d05",
    "attempt02_parent_runner": "c5c0d3af831c38551c7f187deba86d057d96d779e1a09f9ebd316956157d295e",
    "tiny_kkt_producer": "ef94dbbc1048a86aeeadff2219b1129e58925510ebce72dc0464e761e56374c4",
    "tiny_kkt_result": "26103aa3ba2d438d6a5bbaa3e2ef556568b6e583e970d69877183fe956c0c82c",
}
PIN_PATHS = {
    "preparation_known_answer": ANSWER,
    "preparation_assessment": PREP / "assessment.json",
    "preparation_producer": PREP / "prepare.py",
    "raw_operators": COMP / "operators.npz",
    "attempt02_assessment": ATTEMPT02 / "assessment.json",
    "attempt02_candidate": CANDIDATE,
    "attempt02_frozen_inputs": ATTEMPT02 / "frozen-inputs.json",
    "attempt02_parent_runner": ATTEMPT02 / "parent_run.py",
    "tiny_kkt_producer": TINY / "refine.py",
    "tiny_kkt_result": TINY / "refinement-fixture.json",
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def max_abs(values: np.ndarray) -> float:
    return float(np.max(np.abs(values), initial=0.0))


def _read_frozen_inputs() -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict]:
    observed = {name: sha(path) for name, path in PIN_PATHS.items()}
    assert observed == PINNED, "a source input changed after this proposal was prepared"
    with np.load(ANSWER, allow_pickle=False) as archive:
        answer = {key: archive[key] for key in archive.files}
    with np.load(CANDIDATE, allow_pickle=False) as archive:
        candidate = {key: archive[key] for key in archive.files}
    assessment = json.loads((ATTEMPT02 / "assessment.json").read_text(encoding="utf-8"))
    assert assessment["status"] == "STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE"
    assert assessment["solver_status"] == "solved" and assessment["candidate_forces_adopted"] is False
    assert "y" not in candidate and len(candidate["f_N"]) == 1840
    return answer, candidate, assessment


def build_proposal() -> tuple[dict, dict[str, np.ndarray]]:
    answer, prior, assessment = _read_frozen_inputs()
    active = answer["active_row_positions"].astype(np.int64)
    families = answer["active_row_family"]
    assert active.shape == (1615,) and families.shape == (1615,)
    assert answer["S"].shape == (1615, 1615)
    assert answer["D_active"].shape == (1615, 300)
    assert answer["W_total"].shape == (300,)
    assert len(answer["nonnegative_active_positions"]) == 1217
    assert len(answer["closed_floor_normal_rows"]) == 25
    assert len(answer["open_floor_normal_rows"]) == 75
    assert len(answer["held_floor_tangent_rows"]) == 50
    assert len(answer["released_floor_tangent_rows"]) == 150

    unilateral_local = np.flatnonzero(families == "unilateral_springa")
    unilateral_global = active[unilateral_local]
    closed_floor = answer["closed_floor_normal_rows"].astype(np.int64)
    nonfloor = np.setdiff1d(unilateral_global, closed_floor, assume_unique=True)
    assert len(unilateral_global) == 1217 and len(nonfloor) == 1192
    old_f = prior["f_N"]
    old_q = prior["q_raw_mm"]
    assert old_f.shape == old_q.shape == (1840,)

    # One fixed estimate only. Do not probe nearby thresholds or reselect after
    # the proposed KKT solve.
    bound_rows = nonfloor[np.abs(old_f[nonfloor]) <= PROVISIONAL_BOUND_FORCE_TOL_N]
    free_nonfloor = np.setdiff1d(nonfloor, bound_rows, assume_unique=True)
    assert len(bound_rows) == 734 and len(free_nonfloor) == 458
    max_bound_candidate = max_abs(old_f[bound_rows])
    min_free_candidate = float(np.min(old_f[free_nonfloor]))
    assert max_bound_candidate < PROVISIONAL_BOUND_FORCE_TOL_N
    assert min_free_candidate > PROVISIONAL_BOUND_FORCE_TOL_N
    assert np.all(old_f[free_nonfloor] > 0.0)
    assert np.all(old_q[bound_rows] < 0.0)

    # The independent native token intervals distinguish this one proposed
    # set: estimated bound rows have f-centre zero and strict-negative q
    # intervals; estimated free rows have strictly-positive force intervals.
    native_f = answer["f_native_full_N"]
    native_f_radius = answer["f_native_rounding_radius_full_N"]
    native_q = answer["q_native_full_mm"]
    native_q_radius = answer["q_native_DAT_rounding_radius_full_mm"]
    bound_q_interval_upper = native_q[bound_rows] + native_q_radius[bound_rows]
    free_f_interval_lower = native_f[free_nonfloor] - native_f_radius[free_nonfloor]
    assert np.all(native_f[bound_rows] == 0.0)
    assert np.all(bound_q_interval_upper < 0.0)
    assert np.all(free_f_interval_lower > 0.0)
    min_closed_floor_force = float(np.min(old_f[closed_floor]))
    assert min_closed_floor_force > 1.0
    assert np.intersect1d(bound_rows, closed_floor).size == 0

    global_to_local = {int(row): local for local, row in enumerate(active)}
    assert len(global_to_local) == len(active)
    bound_local = [global_to_local[int(row)] for row in bound_rows]
    assert len(bound_local) == len(set(bound_local))
    row_ids_by_global = {
        int(row): str(answer["active_row_ids"][local])
        for local, row in enumerate(active)
    }

    observed_pins = {name: sha(path) for name, path in PIN_PATHS.items()}
    proposal = {
        "schema": "a12_fixed_episode_active_kkt_refinement_readiness/v1",
        "status": "PREPARED_ONE_PROVISIONAL_ACTIVE_SET_NO_SOLVE",
        "source_sha256": observed_pins,
        "runtime": {"numpy": np.__version__, "scipy": scipy.__version__,
                    "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"},
        "episode": {
            "source": "attempt02 saved full-load A12 conditional numerical response",
            "load_factor": 1.0,
            "selected_floor_cells": 25,
            "open_floor_cells": 75,
            "held_tangent_rows": 50,
            "released_tangent_rows": 150,
            "interpretation": "known-answer reproduction of the old prescribed episode only; no new state selection or mechanical acceptance",
        },
        "prior_attempt02": {
            "status": assessment["status"],
            "candidate_forces_adopted": False,
            "inequality_duals_saved": False,
            "force_DAT_failed_count": assessment["original_DAT_comparisons"]["forces"]["failed_count"],
            "projected_q_DAT_failed_count": assessment["original_DAT_comparisons"]["projected_q"]["failed_count"],
            "rigid_coordinate_DAT_failed_count": assessment["original_DAT_comparisons"]["rigid_coordinates"]["failed_count"],
            "candidate_min_unilateral_force_N": float(np.min(old_f[unilateral_global])),
            "candidate_forces_adopted": False,
            "inequality_duals_saved": False,
        },
        "provisional_active_set": {
            "rule": "Among 1,192 nonfloor unilateral SPRINGA variables only, classify old candidate rows with abs(f_N)<=1e-4 N as fixed lower bounds for this single proposed solve.",
            "force_threshold_N": PROVISIONAL_BOUND_FORCE_TOL_N,
            "nonfloor_unilateral_count": len(nonfloor),
            "estimated_active_bound_count": len(bound_rows),
            "estimated_free_count": len(free_nonfloor),
            "active_bound_global_row_positions": bound_rows.astype(int).tolist(),
            "active_bound_row_ids": [row_ids_by_global[int(row)] for row in bound_rows],
            "max_abs_old_candidate_force_on_bound_N": max_bound_candidate,
            "min_old_candidate_force_on_free_N": min_free_candidate,
            "min_free_to_threshold_ratio": min_free_candidate / PROVISIONAL_BOUND_FORCE_TOL_N,
            "max_bound_to_threshold_ratio": max_bound_candidate / PROVISIONAL_BOUND_FORCE_TOL_N,
            "native_interval_separation": {
                "bound_native_force_centres_all_zero": True,
                "bound_max_native_force_radius_N": float(np.max(native_f_radius[bound_rows])),
                "bound_max_native_q_interval_upper_mm": float(np.max(bound_q_interval_upper)),
                "free_min_native_force_interval_lower_N": float(np.min(free_f_interval_lower)),
                "closed_floor_normal_min_old_candidate_force_N": min_closed_floor_force,
                "floor_normal_rows_are_excluded_from_bound_estimate": True,
            },
            "uncertainty_stop": "Do not search another threshold or change this set. Stop before KKT solve if the input pins, exact 734/458 partition, strict native interval separation, floor exclusion, or source row identities differ. After solve, stop if any proposed bound multiplier is not strictly below -2e-9 mm, any free nonfloor unilateral force is <=1e-4 N, or any original source/physical gate fails.",
        },
        "direct_kkt": {
            "objective": "0.5*f.T*S*f + c.T*f; D_active.T*f = W_total; lower bounds f_i>=0 only for the 1,217 unilateral rows",
            "fixed_guess": "734 nonfloor unilateral lower-bound rows are set to zero; all other 881 QP coordinates remain free in the direct active-set KKT system",
            "matrix": "K=[[S,E.T,G.T],[E,0,0],[G,0,0]], E=D_active.T, G selects the 734 estimated active rows; K*[f,lambda,mu]=[-c,W_total,0]",
            "matrix_order": 2649,
            "variable_counts": {"QP_variables": 1615, "equilibrium_equalities": 300, "fixed_lower_bound_rows": 734},
            "recover_physical_coordinates": "a=-lambda; do not change or project D/W",
            "bound_multiplier_sign": "mu<=0 for f_i>=0 with G*f=0; require strictly mu<-2e-9 mm to avoid boundary ambiguity",
            "method": "scipy.linalg.svdvals rank gate then unregularized scipy.linalg.solve(..., assume_a='sym'); no clipping, regularization, pseudoinverse, least-squares, active-set reselection, or threshold search",
            "rank_relative_cutoff": KKT_RANK_RELATIVE_CUTOFF,
            "relative_KKT_residual_max": KKT_RESIDUAL_TOL,
            "parent_resource_gate": {"wall_seconds": 180, "cpu_seconds": 180, "memory_bytes": 6 * 1024**3, "BLAS_threads": 1},
        },
        "postsolve_gates": {
            "description": "Recompute the prior attempt02 audit against original Hraw, source arrays, native token intervals and exact floor episode, without changing thresholds.",
            "original_parent_runner_sha256": PINNED["attempt02_parent_runner"],
            "raw_body_force_max_N": 0.1,
            "raw_body_moment_max_Nmm": 2.0,
            "raw_H_qsym_vs_qraw_max_mm": 2e-8,
            "source_spring_law_max_N": 0.1,
            "unilateral_force_min_N": -1e-8,
            "unilateral_table_domain_abs_q_max_mm": 10.0,
            "closed_floor_normal_q_and_force_min": {"q_mm_strictly_above": 2e-8, "force_N_strictly_above": 1e-8},
            "open_floor_normal_q_max_mm": -2e-8,
            "held_floor_tangent_abs_q_max_mm": 2e-8,
            "released_floor_tangent_force": "exactly zero",
            "DAT_intervals": "unchanged force, projected-q and all 300 rigid-coordinate intervals with the parent runner's 128-epsilon arithmetic guard; no interval enlargement",
            "outputs": "Report KKT/rank, active-set validity, physical gates and each original DAT comparison separately. Any stop leaves candidate unadopted.",
        },
        "scope": {
            "KKT_assembled_by_prepare_or_verify": False,
            "KKT_solved": False,
            "native_run": False,
            "gravity_direction_or_new_state_selected": False,
            "candidate_forces_adopted": False,
            "mechanical_acceptance": False,
        },
        "stop_conditions": [
            "Any source pin or provisional active-set uncertainty gate fails.",
            "KKT rank cutoff, SciPy warning/error, nonfinite output, or residual gate fails.",
            "Active multiplier sign/boundary or free unilateral force contradicts the one guessed active set; do not reselect.",
            "Any raw-H, body equilibrium, spring law, strict floor, released-row, or original DAT interval gate fails.",
            "Any 180 s / 6 GiB / single-thread resource cap is reached.",
        ],
    }
    arrays = dict(answer=answer, old_candidate=prior, bound_global=bound_rows,
                  free_nonfloor_global=free_nonfloor,
                  bound_local=np.asarray(bound_local, dtype=np.int64))
    return proposal, arrays


def interval_check(value: np.ndarray, center: np.ndarray, radius: np.ndarray) -> dict:
    """Same unchanged arithmetic and reporting used by attempt02 parent_run."""
    difference = np.abs(value - center)
    guard = 128 * np.finfo(float).eps * (np.abs(value) + np.abs(center) + 1)
    bound = radius + guard
    ratios = difference / bound
    return dict(pass_gate=bool(np.all(difference <= bound)),
                max_abs_difference=float(np.max(difference)),
                max_ratio=float(np.max(ratios)),
                failed_count=int(np.count_nonzero(difference > bound)),
                worst_full_position=int(np.argmax(ratios)))


def direct_active_set_solve(answer: dict[str, np.ndarray], bound_local: np.ndarray) -> dict:
    """Single fixed-set dense symmetric KKT solve; never chooses another set."""
    S = np.asarray(answer["S"], dtype=np.float64)
    D_active = np.asarray(answer["D_active"], dtype=np.float64)
    c = np.asarray(answer["linear_objective"], dtype=np.float64)
    W = np.asarray(answer["W_total"], dtype=np.float64)
    n, neq = len(c), len(W)
    bound_local = np.asarray(bound_local, dtype=np.int64)
    if S.shape != (1615, 1615) or D_active.shape != (1615, 300) or neq != 300:
        return {"status": "STOP_INVALID_KKT_SHAPES"}
    if (not np.isfinite(S).all() or not np.isfinite(D_active).all()
            or not np.isfinite(c).all() or not np.isfinite(W).all()):
        return {"status": "STOP_NONFINITE_KKT_INPUT"}
    if max_abs(S - S.T) > 1e-14:
        return {"status": "STOP_NONSYMMETRIC_HESSIAN"}
    if (len(set(bound_local.tolist())) != len(bound_local)
            or np.any(bound_local < 0) or np.any(bound_local >= n)):
        return {"status": "STOP_INVALID_ACTIVE_SET"}

    G = np.zeros((len(bound_local), n), dtype=np.float64)
    G[np.arange(len(bound_local)), bound_local] = 1.0
    E = D_active.T
    order = n + neq + len(bound_local)
    KKT = np.zeros((order, order), dtype=np.float64)
    KKT[:n, :n] = S
    KKT[:n, n:n + neq] = E.T
    KKT[n:n + neq, :n] = E
    KKT[:n, n + neq:] = G.T
    KKT[n + neq:, :n] = G
    rhs = np.r_[-c, W, np.zeros(len(bound_local), dtype=np.float64)]

    try:
        singular = linalg.svdvals(KKT, check_finite=True)
    except (ValueError, linalg.LinAlgError) as error:
        return {"status": "STOP_KKT_RANK_CHECK_FAILURE", "detail": str(error)}
    largest = float(np.max(singular))
    smallest = float(np.min(singular))
    rank = int(np.count_nonzero(singular > KKT_RANK_RELATIVE_CUTOFF * largest))
    if rank != order:
        return {"status": "STOP_RANK_DEFICIENT_KKT", "matrix_order": order,
                "numerical_rank": rank, "singular_value_ratio": smallest / largest}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", linalg.LinAlgWarning)
            solution = linalg.solve(KKT, rhs, assume_a="sym", check_finite=True)
    except (linalg.LinAlgWarning, linalg.LinAlgError, ValueError) as error:
        return {"status": "STOP_KKT_DIRECT_SOLVE_FAILURE", "detail": str(error),
                "matrix_order": order, "singular_value_ratio": smallest / largest}

    residual = KKT @ solution - rhs
    relative_residual = max_abs(residual) / max(
        1.0,
        float(linalg.norm(KKT, ord=np.inf)) * float(linalg.norm(solution, ord=np.inf))
        + float(linalg.norm(rhs, ord=np.inf)),
    )
    if relative_residual > KKT_RESIDUAL_TOL:
        return {"status": "STOP_KKT_RESIDUAL", "matrix_order": order,
                "relative_residual_inf": relative_residual,
                "singular_value_ratio": smallest / largest}

    f_active = solution[:n]
    lam = solution[n:n + neq]
    mu = solution[n + neq:]
    nonnegative_local = np.asarray(answer["nonnegative_active_positions"], dtype=np.int64)
    free_lower = np.setdiff1d(nonnegative_local, bound_local, assume_unique=True)
    active_error = max_abs(f_active[bound_local])
    free_min = float(np.min(f_active[free_lower]))
    max_mu = float(np.max(mu))
    if active_error > ACTIVE_PRIMAL_DUAL_TOL or free_min < -ACTIVE_PRIMAL_DUAL_TOL or max_mu > ACTIVE_PRIMAL_DUAL_TOL:
        return {"status": "STOP_INVALID_ACTIVE_SET", "matrix_order": order,
                "active_bound_max_abs_N": active_error,
                "free_unilateral_min_N": free_min,
                "active_bound_max_multiplier_mm": max_mu,
                "singular_value_ratio": smallest / largest}
    if max_mu >= -ACTIVE_PRIMAL_DUAL_TOL:
        return {"status": "STOP_UNCERTAIN_BOUNDARY_ACTIVE_SET", "matrix_order": order,
                "active_bound_max_multiplier_mm": max_mu,
                "singular_value_ratio": smallest / largest}

    return {"status": "PASS_FIXED_ACTIVE_SET_KKT", "f_active_N": f_active,
            "a_minus_lambda_mm": -lam, "mu_active_mm": mu,
            "matrix_order": order, "numerical_rank": rank,
            "singular_value_ratio": smallest / largest,
            "relative_residual_inf": relative_residual,
            "active_bound_max_abs_N": active_error,
            "free_unilateral_min_N": free_min,
            "active_bound_max_multiplier_mm": max_mu}


def audit_candidate(answer: dict[str, np.ndarray], H_raw: np.ndarray, D: np.ndarray,
                    f_active: np.ndarray, a: np.ndarray) -> dict:
    """Replay attempt02's original physical and DAT gates without retuning."""
    active = answer["active_row_positions"]
    families = answer["active_row_family"]
    f = np.zeros(1840, dtype=np.float64)
    f[active] = f_active
    e_full = answer["e_total_full"]
    W = answer["W_total"]
    assert H_raw.shape == (1840, 1840) and D.shape == (1840, 300)
    assert np.array_equal(D[active], answer["D_active"])
    H_sym = (H_raw + H_raw.T) * 0.5
    q_raw = D @ a + e_full - H_raw @ f
    q_sym = D @ a + e_full - H_sym @ f
    skew_shift = max_abs(q_sym - q_raw)
    equilibrium = (D.T @ f - W).reshape(50, 6)
    force_residual = float(np.max(np.abs(equilibrium[:, :3])))
    moment_residual = float(1000 * np.max(np.abs(equilibrium[:, 3:])))
    finite = families != "conditional_floor_tangent_constraint"
    unilateral = families == "unilateral_springa"
    q_active = q_raw[active]
    expected = answer["k_active"][finite] * np.where(
        unilateral[finite], np.maximum(q_active[finite], 0), q_active[finite])
    law_residual = max_abs(f_active[finite] - expected)
    closed = answer["closed_floor_normal_rows"]
    opened = answer["open_floor_normal_rows"]
    held = answer["held_floor_tangent_rows"]
    released = answer["released_floor_tangent_rows"]
    floor = dict(min_closed_normal_q_mm=float(np.min(q_raw[closed])),
                 min_closed_normal_force_N=float(np.min(f[closed])),
                 max_open_normal_q_mm=float(np.max(q_raw[opened])),
                 max_abs_open_normal_force_N=float(np.max(np.abs(f[opened]))),
                 max_abs_held_tangent_q_mm=float(np.max(np.abs(q_raw[held]))),
                 max_abs_released_tangent_force_N=float(np.max(np.abs(f[released]))))
    physical_gates = dict(
        raw_body_force=force_residual <= 0.1,
        raw_body_moment=moment_residual <= 2.0,
        raw_H_compatibility=skew_shift <= 2e-8,
        source_spring_laws=law_residual <= 0.1,
        unilateral_nonnegative=bool(np.min(f_active[unilateral]) >= -1e-8),
        source_unilateral_table_domain=bool(np.max(np.abs(q_active[unilateral])) <= 10.0
                                            and np.max(np.abs(q_raw[opened])) <= 10.0),
        closed_normals_strict=bool(np.min(q_raw[closed]) > 2e-8
                                  and np.min(f[closed]) > 1e-8),
        open_normals_strict=bool(np.max(q_raw[opened]) < -2e-8
                                and np.all(f[opened] == 0)),
        held_tangent_reference=bool(np.max(np.abs(q_raw[held])) <= 2e-8),
        released_tangent_law=bool(np.all(f[released] == 0)))
    source_checks = dict(
        forces=interval_check(f, answer["f_native_full_N"], answer["f_native_rounding_radius_full_N"]),
        projected_q=interval_check(q_raw, answer["q_native_full_mm"],
                                   answer["q_native_DAT_rounding_radius_full_mm"]),
        rigid_coordinates=interval_check(a, answer["a_native_mm_and_scaled_rotation"],
                                        answer["a_native_DAT_rounding_radius"]))
    return {
        "physical_gates": physical_gates,
        "original_DAT_comparisons": source_checks,
        "max_body_force_residual_N": force_residual,
        "max_body_moment_residual_Nmm": moment_residual,
        "max_source_law_residual_N": law_residual,
        "max_raw_vs_symmetric_H_shift_mm": skew_shift,
        "floor": floor,
        "candidate_forces_adopted": False,
        "joint_accepted": False,
        "mechanical_acceptance": False,
    }


def one_shot_refine() -> dict:
    """Parent-callable only; deliberately not exposed as a CLI mode here."""
    proposal, state = build_proposal()
    answer = state["answer"]
    solved = direct_active_set_solve(answer, state["bound_local"])
    report = {"native_run": False, "candidate_forces_adopted": False,
              "mechanical_acceptance": False,
              "proposal_source_sha256": proposal["source_sha256"],
              "kkt": {key: value for key, value in solved.items()
                      if key not in {"f_active_N", "a_minus_lambda_mm", "mu_active_mm"}}}
    if solved["status"] != "PASS_FIXED_ACTIVE_SET_KKT":
        report["status"] = solved["status"]
        return report
    with np.load(COMP / "operators.npz", allow_pickle=False) as operators:
        H_raw, D = operators["H"], operators["D"]
    audited = audit_candidate(answer, H_raw, D, solved["f_active_N"], solved["a_minus_lambda_mm"])
    free_nonfloor_global = state["free_nonfloor_global"]
    free_nonfloor_local = np.asarray([np.flatnonzero(answer["active_row_positions"] == row)[0]
                                      for row in free_nonfloor_global], dtype=np.int64)
    free_nonfloor_min = float(np.min(solved["f_active_N"][free_nonfloor_local]))
    max_active_mu = float(np.max(solved["mu_active_mm"]))
    boundary_gates = dict(
        free_nonfloor_above_declared_estimate=free_nonfloor_min > PROVISIONAL_BOUND_FORCE_TOL_N,
        estimated_active_bounds_strict=max_active_mu < -ACTIVE_PRIMAL_DUAL_TOL,
        no_active_set_reselection=True)
    all_physical = all(audited["physical_gates"].values())
    all_source = all(item["pass_gate"] for item in audited["original_DAT_comparisons"].values())
    all_boundary = all(boundary_gates.values())
    report.update(audited)
    report["fixed_active_set_boundary_gates"] = boundary_gates
    report["free_nonfloor_unilateral_min_N"] = free_nonfloor_min
    report["active_bound_max_multiplier_mm"] = max_active_mu
    report["status"] = ("PASS_FIXED_EPISODE_KNOWN_ANSWER_ONLY"
                        if all_physical and all_source and all_boundary
                        else "STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-proposal", action="store_true")
    group.add_argument("--verify-inputs", action="store_true")
    args = parser.parse_args()
    proposal, _ = build_proposal()
    rendered = json.dumps(proposal, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write_proposal:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print("Wrote one fixed A12 active-set proposal; no KKT was assembled or solved")
    else:
        assert OUTPUT.read_text(encoding="utf-8") == rendered, "frozen proposal differs"
        print("PASS_A12_FIXED_ACTIVE_KKT_INPUTS: one 734-row estimate; no KKT assembled/solved")


if __name__ == "__main__":
    main()
