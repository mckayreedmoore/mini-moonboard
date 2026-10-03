"""Tiny-only unregularized fixed-active-set KKT refinement checks.

This module consumes the existing 24 tiny prescribed-mask QP branches. It
does not load or assemble the A12 frame operator and does not run OSQP or a
native solver.
"""

from __future__ import annotations

import ast
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import warnings

import numpy as np
import scipy
from scipy import linalg


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
KNOWN = BASE / "current-coupled-indicator-selector-fixture-attempt01/known-answer.json"
OLD_RESULT = BASE / "current-floor-mask-dual-qp-fixture-attempt01/fixed-mask-dual-qp.json"
OLD_PRODUCER = BASE / "current-floor-mask-dual-qp-fixture-attempt01/solve_fixture.py"
RUN02 = BASE / "current-a12-fixed-episode-dual-qp-known-answer-attempt02"
RUN01 = BASE / "current-a12-fixed-episode-dual-qp-known-answer-attempt01"
RUN03 = BASE / "current-a12-fixed-episode-dual-qp-known-answer-attempt03"
PREP = BASE / "current-a12-fixed-episode-dual-qp-preparation-attempt01"
OUTPUT = HERE / "refinement-fixture.json"

PINNED = {
    "known-answer.json": "8b42e4282952d8174f93b5f6138de14d0c88cbb1602d3968665aba5558045e88",
    "fixed-mask-dual-qp.json": "a3bd6f411f25185d909bd6751f1f3ad17142e61c7a5e98806365e6911c9ab59c",
    "solve_fixture.py": "87641f8d3622f3e38350f41c511556e76284a8df5b7ee812c925f2966499cbba",
}
PINNED_RUNS = {
    "attempt01_assessment": "bcbd3800e6667f77da4631842e6a61123ef43053d7e9f620106581311d697c91",
    "attempt02_assessment": "ca52e94df2937fee7a2cf7a310c77f5251a3a6087a2ea930e855aee5c01205a0",
    "attempt02_diagnostic_candidate": "6b19fd37ce22d0e5fea46d0610804e4e51b7eaecacbfa9dfd15242b9cdc6c29b",
    "attempt02_frozen_inputs": "4efffd20b358a0476804e456d94206798498577308c8f65749660009ddda2d05",
    "attempt03_method_readme": "3851b00846483a818b33f5166cd0f6999b09045e56910977ca83320776d0d079",
    "attempt03_parent_run": "44250fe61e730dc0b10b43244cf326289bcbd497a6726ee33dc44eac8d6e4c3f",
    "attempt03_tiny_settings_script": "91ea8f4da910f01461787b8bd42ded7b389739518d51b6fd9aab0c55728028cc",
}
KKT_RANK_RELATIVE_CUTOFF = 1.0e-12
KKT_RESIDUAL_TOL = 2.0e-10
ACTIVE_PRIMAL_DUAL_TOL = 2.0e-9
SOURCE_ORACLE_TOL = 2.0e-9
MASK_TOL = 2.0e-8


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def max_abs(x: np.ndarray) -> float:
    return float(np.max(np.abs(x), initial=0.0))


def load_pinned_inputs() -> tuple[dict, dict, dict[str, str]]:
    observed = {
        "known-answer.json": sha(KNOWN),
        "fixed-mask-dual-qp.json": sha(OLD_RESULT),
        "solve_fixture.py": sha(OLD_PRODUCER),
    }
    assert observed == PINNED, "an existing tiny oracle changed"
    known = json.loads(KNOWN.read_text(encoding="utf-8"))
    old = json.loads(OLD_RESULT.read_text(encoding="utf-8"))
    assert known["status"] == "ALL_TINY_FIXTURES_REPLAYED"
    assert old["status"] == "PASS_TINY_SOURCE_BRANCHES_AND_KKT_FIXTURES"
    assert len(known["results"]) == len(old["source_branch_cases"]) == 8
    assert sum(case["possible_binary_masks"] for case in known["results"]) == 24
    return known, old, observed


def read_a12_attempts() -> dict:
    paths = {
        "attempt01_assessment": RUN01 / "assessment.json",
        "attempt02_assessment": RUN02 / "assessment.json",
        "attempt02_diagnostic_candidate": RUN02 / "diagnostic-candidate.npz",
        "attempt02_frozen_inputs": RUN02 / "frozen-inputs.json",
        "attempt03_method_readme": RUN03 / "README.md",
        "attempt03_parent_run": RUN03 / "parent_run.py",
        "attempt03_tiny_settings_script": RUN03 / "verify_settings.py",
    }
    observed = {name: sha(path) for name, path in paths.items()}
    assert observed == PINNED_RUNS, "a recorded A12 attempt changed"
    run01 = json.loads(paths["attempt01_assessment"].read_text(encoding="utf-8"))
    run02 = json.loads(paths["attempt02_assessment"].read_text(encoding="utf-8"))
    run02_freeze = json.loads(paths["attempt02_frozen_inputs"].read_text(encoding="utf-8"))
    run03_tree = ast.parse(paths["attempt03_parent_run"].read_text(encoding="utf-8"))
    run03_settings = None
    for node in run03_tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SETTINGS" for target in node.targets
        ):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) \
                    and node.value.func.id == "dict":
                run03_settings = {keyword.arg: ast.literal_eval(keyword.value)
                                  for keyword in node.value.keywords}
            else:
                run03_settings = ast.literal_eval(node.value)
            break
    assert isinstance(run03_settings, dict)
    assert run03_settings["eps_abs"] == 1e-11 and run03_settings["eps_rel"] == 0.0
    assert run01["status"] == "STOP_SOLVER_STATUS_OR_BUDGET"
    assert run01["solver_status_value"] == 8 and run01["solver_status"] == "run time limit reached"
    assert run02["status"] == "STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE"
    assert run02["solver_status"] == "solved" and run02["solver_status_value"] == 1
    assert run02["frozen_inputs_sha256"] == sha(paths["attempt02_frozen_inputs"])
    assert run02["diagnostic_candidate_sha256"] == observed["attempt02_diagnostic_candidate"]
    assert run02["candidate_forces_adopted"] is False and run02["source_freeze_unchanged"] is True

    # Count the small negative iterate entries from the saved result without
    # assembling any frame operator or attempting a new solve.
    with np.load(PREP / "known-answer.npz", allow_pickle=False) as source:
        active = source["active_row_positions"]
        family = source["active_row_family"]
        unilateral_positions = active[family == "unilateral_springa"]
    with np.load(paths["attempt02_diagnostic_candidate"], allow_pickle=False) as candidate:
        candidate_force = candidate["f_N"]
        candidate_fields = sorted(candidate.files)
        assert candidate_force.shape == (1840,)
        min_unilateral = float(np.min(candidate_force[unilateral_positions]))
        negative_unilateral_count = int(np.count_nonzero(candidate_force[unilateral_positions] < 0.0))

    return {
        "source_sha256": observed,
        "attempt01": {
            "status": run01["status"],
            "solver_status": run01["solver_status"],
            "solver_status_value": run01["solver_status_value"],
            "elapsed_seconds": run01["elapsed_seconds"],
            "solver_seconds": run01["solver_seconds"],
            "iterations": run01["iterations"],
            "primal_residual": run01["primal_residual"],
            "dual_residual": run01["dual_residual"],
            "candidate_forces_adopted": run01["candidate_forces_adopted"],
        },
        "attempt02": {
            "status": run02["status"],
            "solver_status": run02["solver_status"],
            "solver_status_value": run02["solver_status_value"],
            "elapsed_seconds": run02["elapsed_seconds"],
            "solver_seconds": run02["solver_seconds"],
            "iterations": run02["iterations"],
            "primal_residual": run02["primal_residual"],
            "dual_residual": run02["dual_residual"],
            "polish_status": run02["polish_status"],
            "physical_gates": run02["physical_gates"],
            "force_comparison": run02["original_DAT_comparisons"]["forces"],
            "projected_q_comparison": run02["original_DAT_comparisons"]["projected_q"],
            "rigid_coordinate_comparison": run02["original_DAT_comparisons"]["rigid_coordinates"],
            "min_unilateral_force_N": min_unilateral,
            "negative_unilateral_force_count": negative_unilateral_count,
            "source_freeze_unchanged": run02["source_freeze_unchanged"],
            "candidate_forces_adopted": run02["candidate_forces_adopted"],
            "settings": run02_freeze["settings"],
            "saved_candidate_fields": candidate_fields,
            "inequality_duals_saved": "y" in candidate_fields,
        },
        "attempt03": {
            "settings": run03_settings,
            "frame_run_artifact_present": (RUN03 / "assessment.json").exists(),
            "frame_run": False,
            "parent_reported_tiny_preflight_status": "maximum iterations reached",
            "provenance_note": "The tiny-preflight status came from the parent task handoff; attempt03 contains no assessment.json result artifact.",
        },
    }


def solve_fixed_active_set(
    P: np.ndarray,
    c: np.ndarray,
    E: np.ndarray,
    b: np.ndarray,
    nonnegative: list[int],
    active_lower: list[int],
) -> dict:
    """Solve the equality-constrained KKT system for one hypothesized set.

    Lower-bound rows use `x_i=0` with multiplier `mu_i <= 0`, consistent with
    the `x_i >= 0` convention used by the pinned tiny QP fixture. No clipping,
    pseudoinverse, diagonal regularization, or least-squares fallback exists.
    """
    P = np.asarray(P, dtype=np.float64)
    c = np.asarray(c, dtype=np.float64)
    E = np.asarray(E, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    n = len(c)
    if P.shape != (n, n) or E.ndim != 2 or E.shape[1] != n or b.shape != (E.shape[0],):
        return {"status": "STOP_INVALID_KKT_SHAPES"}
    if not (np.isfinite(P).all() and np.isfinite(c).all()
            and np.isfinite(E).all() and np.isfinite(b).all()):
        return {"status": "STOP_NONFINITE_KKT_INPUT"}
    if max_abs(P - P.T) > 1.0e-13:
        return {"status": "STOP_NONSYMMETRIC_HESSIAN"}
    nonnegative = list(map(int, nonnegative))
    active_lower = list(map(int, active_lower))
    if (len(set(nonnegative)) != len(nonnegative)
            or any(i < 0 or i >= n for i in nonnegative)):
        return {"status": "STOP_INVALID_LOWER_BOUND_INDEX_SET"}
    if (len(set(active_lower)) != len(active_lower)
            or any(i not in nonnegative for i in active_lower)):
        return {"status": "STOP_INVALID_ACTIVE_SET"}

    # The QP Hessian may be semidefinite when held tangent forces have no
    # compliance. Convexity is required; nonsingularity is checked on the
    # complete KKT matrix below, where equality constraints remove gauges.
    p_eigmin = float(np.min(linalg.eigvalsh(P)))
    if p_eigmin < -1.0e-10:
        return {"status": "STOP_NONCONVEX_HESSIAN", "hessian_min_eigenvalue": p_eigmin}

    G = np.zeros((len(active_lower), n), dtype=np.float64)
    for row, index in enumerate(active_lower):
        G[row, index] = 1.0
    C = np.vstack((E, G))
    rhs_constraints = np.r_[b, np.zeros(len(active_lower))]
    M = np.block([
        [P, C.T],
        [C, np.zeros((C.shape[0], C.shape[0]), dtype=np.float64)],
    ])
    rhs = np.r_[-c, rhs_constraints]
    singular_values = linalg.svdvals(M, check_finite=True)
    sigma_max = float(np.max(singular_values, initial=0.0))
    sigma_min = float(np.min(singular_values))
    cutoff = KKT_RANK_RELATIVE_CUTOFF * sigma_max
    numerical_rank = int(np.count_nonzero(singular_values > cutoff))
    if numerical_rank != M.shape[0]:
        return {
            "status": "STOP_RANK_DEFICIENT_KKT",
            "matrix_order": int(M.shape[0]),
            "numerical_rank": numerical_rank,
            "smallest_singular_value": sigma_min,
            "largest_singular_value": sigma_max,
            "rank_relative_cutoff": KKT_RANK_RELATIVE_CUTOFF,
        }

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", linalg.LinAlgWarning)
            solution = linalg.solve(M, rhs, assume_a="sym", check_finite=True)
    except linalg.LinAlgWarning as error:
        return {"status": "STOP_ILL_CONDITIONED_KKT", "detail": str(error)}
    except linalg.LinAlgError as error:
        return {"status": "STOP_SINGULAR_KKT", "detail": str(error)}

    x = solution[:n]
    multipliers = solution[n:]
    lambda_eq = multipliers[:E.shape[0]]
    mu_lower = multipliers[E.shape[0]:]
    residual = M @ solution - rhs
    relative_residual = max_abs(residual) / max(
        1.0,
        float(linalg.norm(M, ord=np.inf)) * float(linalg.norm(solution, ord=np.inf))
        + float(linalg.norm(rhs, ord=np.inf)),
    )
    if relative_residual > KKT_RESIDUAL_TOL:
        return {
            "status": "STOP_KKT_RESIDUAL",
            "relative_residual_inf": relative_residual,
            "absolute_residual_inf": max_abs(residual),
        }

    active_values = x[active_lower]
    free_lower = [i for i in nonnegative if i not in set(active_lower)]
    free_values = x[free_lower]
    if (max_abs(active_values) > ACTIVE_PRIMAL_DUAL_TOL
            or np.min(free_values, initial=0.0) < -ACTIVE_PRIMAL_DUAL_TOL
            or (mu_lower.size and np.max(mu_lower) > ACTIVE_PRIMAL_DUAL_TOL)):
        return {
            "status": "STOP_INVALID_ACTIVE_SET",
            "active_bound_max_abs_x": max_abs(active_values),
            "free_lower_min_x": float(np.min(free_values, initial=0.0)),
            "active_lower_max_mu": float(np.max(mu_lower)) if mu_lower.size else None,
        }

    return {
        "status": "PASS_KKT_ACTIVE_SET",
        "x": x,
        "lambda_eq": lambda_eq,
        "mu_lower": mu_lower,
        "active_lower": active_lower,
        "matrix_order": int(M.shape[0]),
        "numerical_rank": numerical_rank,
        "singular_value_ratio": sigma_min / sigma_max,
        "relative_residual_inf": relative_residual,
        "absolute_residual_inf": max_abs(residual),
        "stationarity_inf": max_abs(P @ x + c + E.T @ lambda_eq + G.T @ mu_lower),
        "equality_inf": max_abs(E @ x - b),
        "active_bound_inf": max_abs(active_values),
        "free_lower_min": float(np.min(free_values, initial=0.0)),
        "active_lower_max_mu": float(np.max(mu_lower)) if mu_lower.size else None,
        "max_active_complementarity": max_abs(active_values * mu_lower),
    }


def assemble_tiny_branch(case: dict, mask: tuple[bool, ...]) -> dict:
    src = case["selector_input"]
    K = np.asarray(src["operator_n_per_mm"], dtype=np.float64)
    W = np.asarray(src["external_wrench_n"], dtype=np.float64)
    contact_sign = np.asarray(src["contact_basis_diagonal"], dtype=np.float64)
    ncontact, ndof = len(mask), len(W)
    if ndof != 2 * ncontact or K.shape != (ndof, ndof):
        raise AssertionError(f"tiny fixture dimensions changed for {case['id']}")
    B = np.linalg.cholesky(K).T
    D_internal = B
    D_contact = -np.diag(contact_sign)
    D_all = np.vstack((D_internal, D_contact))
    H_all = np.zeros((len(D_all), len(D_all)), dtype=np.float64)
    e_all = np.zeros(len(D_all), dtype=np.float64)
    qp_reference = np.asarray([
        -contact_sign[2 * i] * float(src["tangent_reference_mm"][i])
        for i in range(ncontact)
    ])

    active_global_rows = list(range(ndof))
    k_active = [1.0] * ndof
    linear = [0.0] * ndof
    normal_local_by_cell = {}
    for i, closed in enumerate(mask):
        if not closed:
            continue
        tangent_row = ndof + 2 * i
        normal_row = ndof + 2 * i + 1
        active_global_rows.append(tangent_row)
        k_active.append(float("inf"))
        linear.append(float(qp_reference[i]))
        normal_local_by_cell[i] = len(active_global_rows)
        active_global_rows.append(normal_row)
        k_active.append(float(src["normal_penalty_n_per_mm"]))
        linear.append(0.0)

    D_active = D_all[active_global_rows]
    H_active = H_all[np.ix_(active_global_rows, active_global_rows)]
    k_active = np.asarray(k_active, dtype=np.float64)
    inverse_k = np.zeros(len(k_active), dtype=np.float64)
    finite_k = np.isfinite(k_active)
    inverse_k[finite_k] = 1.0 / k_active[finite_k]
    P = H_active + np.diag(inverse_k)
    c = -e_all[active_global_rows] + np.asarray(linear, dtype=np.float64)
    E = D_active.T
    nonnegative = [normal_local_by_cell[i] for i, closed in enumerate(mask) if closed]
    return {
        "P": P,
        "c": c,
        "E": E,
        "b": W,
        "nonnegative": nonnegative,
        "D_all": D_all,
        "H_all": H_all,
        "e_all": e_all,
        "active_global_rows": active_global_rows,
        "D_active": D_active,
        "W": W,
        "K": K,
        "contact_sign": contact_sign,
        "qp_reference": qp_reference,
        "nonnegative_local": nonnegative,
    }


def classify_branches(branches: list[dict]) -> str:
    admissible = [branch for branch in branches if branch["admissible"]]
    if not admissible:
        return "NO_ADMISSIBLE_STATE"
    if len(admissible) == 1:
        return "ONE_ADMISSIBLE_MASK"
    for left, right in itertools.combinations(admissible, 2):
        differing = [i for i, (a, b) in enumerate(zip(left["closed_mask"], right["closed_mask"], strict=True))
                     if a != b]
        same = (
            np.allclose(left["u_mm"], right["u_mm"], atol=MASK_TOL, rtol=0.0)
            and np.allclose(left["tangent_forces_N"], right["tangent_forces_N"], atol=MASK_TOL, rtol=0.0)
            and np.allclose(left["normal_forces_N"], right["normal_forces_N"], atol=MASK_TOL, rtol=0.0)
        )
        boundary = all(
            abs(left["tangent_forces_N"][i]) <= MASK_TOL
            and abs(left["normal_forces_N"][i]) <= MASK_TOL
            and abs(left["contact_q_mm"][2 * i + 1]) <= MASK_TOL
            for i in differing
        )
        if not (same and boundary):
            return "MULTIPLE_ADMISSIBLE_MASKS"
    return "AMBIGUOUS_ZERO_BOUNDARY_MASKS"


def refine_branch(case: dict, mask: tuple[bool, ...], old_branch: dict) -> dict:
    model = assemble_tiny_branch(case, mask)
    nonnegative = model["nonnegative"]
    feasible_kkt = []
    rejected = []
    for bits in itertools.product((False, True), repeat=len(nonnegative)):
        active = [nonnegative[i] for i, enabled in enumerate(bits) if enabled]
        solved = solve_fixed_active_set(
            model["P"], model["c"], model["E"], model["b"], nonnegative, active
        )
        if solved["status"] == "PASS_KKT_ACTIVE_SET":
            feasible_kkt.append(solved)
        else:
            rejected.append({"active_lower_local": active, "status": solved["status"],
                             **{key: value for key, value in solved.items() if key != "status"}})
    if not feasible_kkt:
        raise AssertionError(f"no KKT-consistent active set for {case['id']} mask={mask}: {rejected}")
    reference_x = feasible_kkt[0]["x"]
    if any(not np.allclose(item["x"], reference_x, atol=1e-10, rtol=0.0)
           for item in feasible_kkt[1:]):
        raise AssertionError(f"multiple distinct primal KKT states for {case['id']} mask={mask}")

    active_rows = model["active_global_rows"]
    f_all = np.zeros(len(model["D_all"]), dtype=np.float64)
    f_all[active_rows] = reference_x
    a = -feasible_kkt[0]["lambda_eq"]
    q_all = model["D_all"] @ a + model["e_all"] - model["H_all"] @ f_all
    ncontact = len(mask)
    contact_f = f_all[len(model["K"]):]
    contact_q = q_all[len(model["K"]):]
    tangent_force = contact_f[0::2]
    normal_force = contact_f[1::2]
    tangent_q = contact_q[0::2]
    normal_q = contact_q[1::2]
    source_balance = model["K"] @ a - model["contact_sign"] * contact_f - model["W"]
    internal_law = model["D_all"][:len(model["K"])] @ a - f_all[:len(model["K"])]

    reasons = []
    for i, closed in enumerate(mask):
        if closed:
            if abs(tangent_q[i] - model["qp_reference"][i]) > MASK_TOL:
                reasons.append(f"cell_{i}_held_tangent_reference_mismatch")
            if normal_force[i] < -MASK_TOL:
                reasons.append(f"cell_{i}_negative_closed_normal_force")
            if normal_q[i] < -MASK_TOL:
                reasons.append(f"cell_{i}_closed_normal_extension_negative")
            if abs(normal_q[i] - normal_force[i] / float(case["selector_input"]["normal_penalty_n_per_mm"])) > MASK_TOL:
                reasons.append(f"cell_{i}_closed_normal_spring_law_mismatch")
        else:
            if abs(tangent_force[i]) > MASK_TOL or abs(normal_force[i]) > MASK_TOL:
                reasons.append(f"cell_{i}_open_contact_force_nonzero")
            if normal_q[i] > MASK_TOL:
                reasons.append(f"cell_{i}_open_normal_extension_positive")
    if max_abs(internal_law) > 2e-8:
        reasons.append("bilateral_spring_bank_law_mismatch")
    if max_abs(source_balance) > 2e-7:
        reasons.append("source_equilibrium_residual")

    # Compare with both the existing branch record and, where present, the
    # independent admissible selector candidate. The old branch record covers
    # every one of the 24 masks, including rejected physical branches.
    assert list(mask) == old_branch["closed_mask"]
    assert max_abs(a - np.asarray(old_branch["source_displacement_u_mm"])) <= SOURCE_ORACLE_TOL
    assert max_abs(tangent_force - np.asarray(old_branch["source_tangent_forces_N"])) <= SOURCE_ORACLE_TOL
    assert max_abs(normal_force - np.asarray(old_branch["source_normal_forces_N"])) <= SOURCE_ORACLE_TOL
    assert max_abs(contact_q - np.asarray(old_branch["source_qp_contact_coordinates_mm"])) <= SOURCE_ORACLE_TOL
    admissible = not reasons
    if bool(old_branch["admissible"]) != admissible:
        raise AssertionError(f"branch admissibility differs: {case['id']} mask={mask} reasons={reasons}")

    return {
        "closed_mask": list(mask),
        "admissible": admissible,
        "rejection": reasons,
        "u_mm": a.tolist(),
        "contact_q_mm": contact_q.tolist(),
        "tangent_forces_N": tangent_force.tolist(),
        "normal_forces_N": normal_force.tolist(),
        "source_equilibrium_inf_N": max_abs(source_balance),
        "internal_law_inf_N": max_abs(internal_law),
        "valid_kkt_active_sets": [item["active_lower"] for item in feasible_kkt],
        "rank_checks": [
            {"matrix_order": item["matrix_order"], "rank": item["numerical_rank"],
             "singular_value_ratio": item["singular_value_ratio"],
             "relative_residual_inf": item["relative_residual_inf"]}
            for item in feasible_kkt
        ],
        "rejected_active_sets": rejected,
    }


def sign_fixture(old: dict) -> dict:
    source = old["nonzero_H_e_sign_fixture"]
    D = np.asarray(source["D"], dtype=np.float64)
    H = np.asarray(source["H"], dtype=np.float64)
    k = np.asarray(source["spring_k"], dtype=np.float64)
    e = np.asarray(source["e"], dtype=np.float64)
    W = np.asarray(source["W"], dtype=np.float64)
    inverse_k = 1.0 / k
    P = H + np.diag(inverse_k)
    c = -e
    solved = solve_fixed_active_set(P, c, D.T, W, [1], [])
    assert solved["status"] == "PASS_KKT_ACTIVE_SET"
    f = solved["x"]
    a = -solved["lambda_eq"]
    q = D @ a + e - H @ f
    for name, result, expected in (
        ("f", f, np.asarray(source["known_answer_f"], dtype=np.float64)),
        ("a", a, np.asarray(source["known_answer_a"], dtype=np.float64)),
        ("q", q, np.asarray(source["known_answer_q"], dtype=np.float64)),
    ):
        assert max_abs(result - expected) <= SOURCE_ORACLE_TOL, name
    assert q[1] > 0.0 and f[1] > 0.0
    return {
        "id": "one_dof_nonzero_H_and_e_sign_oracle",
        "status": "PASS_DIRECT_KKT_SIGN_FIXTURE",
        "D": D.tolist(), "H": H.tolist(), "e": e.tolist(), "W": W.tolist(),
        "k": k.tolist(), "f": f.tolist(), "a_minus_lambda": a.tolist(), "q": q.tolist(),
        "kkt": {"rank": solved["numerical_rank"], "matrix_order": solved["matrix_order"],
                "stationarity_inf": solved["stationarity_inf"],
                "equality_inf": solved["equality_inf"],
                "relative_residual_inf": solved["relative_residual_inf"]},
    }


def stop_oracles() -> dict:
    # Duplicate equilibrium rows give a singular saddle-point KKT system.
    dependent = solve_fixed_active_set(
        np.eye(2), np.zeros(2), np.array([[1.0, 1.0], [2.0, 2.0]]),
        np.zeros(2), [], [],
    )
    assert dependent["status"] == "STOP_RANK_DEFICIENT_KKT"
    # An unconstrained zero-curvature mode is another singular KKT system.
    flat = solve_fixed_active_set(
        np.diag([0.0, 1.0]), np.zeros(2), np.zeros((0, 2)), np.zeros(0), [], [],
    )
    assert flat["status"] == "STOP_RANK_DEFICIENT_KKT"
    # An index not present in the declared lower-bound set is rejected before
    # assembly, and a mathematically wrong guessed set fails the dual sign.
    invalid_index = solve_fixed_active_set(
        np.eye(1), np.zeros(1), np.zeros((0, 1)), np.zeros(0), [0], [1],
    )
    assert invalid_index["status"] == "STOP_INVALID_ACTIVE_SET"
    wrong_sign = solve_fixed_active_set(
        np.eye(1), np.array([-1.0]), np.zeros((0, 1)), np.zeros(0), [0], [0],
    )
    assert wrong_sign["status"] == "STOP_INVALID_ACTIVE_SET"
    correct_active = solve_fixed_active_set(
        np.eye(1), np.array([1.0]), np.zeros((0, 1)), np.zeros(0), [0], [0],
    )
    assert correct_active["status"] == "PASS_KKT_ACTIVE_SET"
    assert abs(float(correct_active["x"][0])) <= ACTIVE_PRIMAL_DUAL_TOL
    assert float(correct_active["mu_lower"][0]) < 0.0
    return {
        "dependent_equalities": {key: value for key, value in dependent.items() if key != "x"},
        "unconstrained_flat_mode": {key: value for key, value in flat.items() if key != "x"},
        "invalid_active_index": invalid_index,
        "wrong_active_set_dual_sign": {key: value for key, value in wrong_sign.items() if key != "x"},
        "correct_active_lower_bound": {
            "status": correct_active["status"],
            "x": correct_active["x"].tolist(),
            "mu_lower": correct_active["mu_lower"].tolist(),
        },
        "regularization_or_clipping_used": False,
    }


def produce() -> dict:
    known, old, pins = load_pinned_inputs()
    a12_attempts = read_a12_attempts()
    old_by_case = {case["id"]: case for case in old["source_branch_cases"]}
    results = []
    mask_count = 0
    for case in known["results"]:
        previous = old_by_case[case["id"]]
        old_by_mask = {tuple(branch["closed_mask"]): branch for branch in previous["branches"]}
        contact_count = len(case["selector_input"]["tangent_reference_mm"])
        branches = []
        for mask in itertools.product((False, True), repeat=contact_count):
            direct = refine_branch(case, mask, old_by_mask[mask])
            branches.append(direct)
            mask_count += 1
        classification = classify_branches(branches)
        assert len(branches) == case["possible_binary_masks"]
        assert classification == case["classification"]
        assert [branch["closed_mask"] for branch in branches if branch["admissible"]] == [
            candidate["closed_mask"] for candidate in case["candidate_masks"]
        ]
        results.append({
            "id": case["id"],
            "source_oracle": case["source_oracle"],
            "expected_classification": case["classification"],
            "direct_kkt_classification": classification,
            "mask_count": len(branches),
            "valid_mask_count": sum(branch["admissible"] for branch in branches),
            "branches": branches,
        })
    assert mask_count == 24
    return {
        "schema": "tiny_fixed_active_kkt_refinement_fixture/v1",
        "status": "PASS_TINY_DIRECT_KKT_REFINEMENT_AND_STOP_ORACLES",
        "method": {
            "objective": "0.5*x.T*P*x + c.T*x subject to E*x=b and x[nonnegative]>=0",
            "active_set_kkt": "[[P,C.T],[C,0]]*[x,lambda,mu]=[-c,[b,0]], C=[E; I_active]",
            "lower_bound_multiplier_convention": "active x_i=0 rows use mu_i<=0 for x_i>=0",
            "physical_coordinate_sign": "a=-lambda_eq",
            "linear_solver": "scipy.linalg.solve(..., assume_a='sym'); unregularized direct solve",
            "rank_gate": {
                "singular_value_relative_cutoff": KKT_RANK_RELATIVE_CUTOFF,
                "relative_residual_inf_max": KKT_RESIDUAL_TOL,
                "no_pseudoinverse": True,
                "no_least_squares_fallback": True,
                "no_diagonal_regularization": True,
                "no_force_clipping": True,
            },
            "active_set_scope": "exhaustive lower-bound active sets for tiny prescribed masks only; no guessed frame mask",
        },
        "source_pin_sha256": pins,
        "a12_run_diagnostics": a12_attempts,
        "tiny_mask_cases": results,
        "tiny_mask_count": mask_count,
        "nonzero_H_e_sign_fixture": sign_fixture(old),
        "stop_oracles": stop_oracles(),
        "versions": {"numpy": np.__version__, "scipy": scipy.__version__},
        "scope": {
            "native_run": False,
            "frame_solve": False,
            "A12_H_or_D_operator_loaded": False,
            "A12_KKT_assembled_or_solved": False,
            "geometry_changed": False,
            "forces_adopted": False,
            "physical_state_claimed": False,
        },
        "limitations": [
            "The result proves only that the direct unregularized KKT method reproduces pinned tiny prescribed-mask branches and rejects singular or invalid active sets.",
            "The actual attempt02 active lower-bound set is not stored as solver duals; it can only be estimated from the saved candidate and then must pass complete raw-H, source-law, strict-floor and DAT-interval gates.",
            "The A12 KKT matrix conditioning, active-set correctness, fill/memory, runtime and DAT-token reproduction are untested. No frame result or global selector readiness follows.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(produce(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print("Wrote tiny direct KKT refinement result; no frame operator or solver was used")
    else:
        assert OUTPUT.read_text(encoding="utf-8") == rendered, "saved tiny refinement result differs"
        print("PASS_TINY_DIRECT_KKT_REFINEMENT_AND_STOP_ORACLES: 24 masks + sign/rank/active-set checks")


if __name__ == "__main__":
    main()
