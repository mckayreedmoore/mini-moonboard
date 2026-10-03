"""Prepare/readiness-check one raw-H fixed-active A12 comparison.

`--verify-ready` reads the exact frozen inputs and checks formulation/source
identities only. It does not assemble or solve the bordered system. The
parent-only runner imports `solve_and_audit` after freezing these sources.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import warnings

import numpy as np
import scipy
from scipy import linalg


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
PREFLIGHT = BASE / "current-a12-fixed-active-kkt-refinement-preflight-attempt01"
PRIOR = BASE / "current-a12-fixed-active-kkt-parent-attempt01"
COMP = BASE / "current-frame-connector-compliance-attempt04"
TINY_RAW_H = BASE / "current-fixed-active-raw-H-linear-fixture-attempt01"
ANSWER = BASE / "current-a12-fixed-episode-dual-qp-preparation-attempt01/known-answer.npz"
OPERATORS = COMP / "operators.npz"
ROW_IDENTITIES = COMP / "row-identities.json"
READINESS = HERE / "readiness.json"

KKT_RANK_RELATIVE_CUTOFF = 1.0e-12
KKT_RESIDUAL_TOL = 2.0e-10
ACTIVE_PRIMAL_DUAL_TOL = 2.0e-9
PROVISIONAL_BOUND_FORCE_TOL_N = 1.0e-4


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def max_abs(value: np.ndarray) -> float:
    return float(np.max(np.abs(value), initial=0.0))


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def import_preflight():
    path = PREFLIGHT / "prepare.py"
    spec = importlib.util.spec_from_file_location("pinned_a12_fixed_kkt_preflight", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import pinned preflight: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_path_inventory(preflight) -> dict[str, Path]:
    paths = {relative(path): path for path in preflight.PIN_PATHS.values()}
    prior_frozen = json.loads((PRIOR / "frozen-inputs.json").read_text(encoding="utf-8"))
    paths.update({name: ROOT / name for name in prior_frozen["source_sha256"]})
    extra = [
        PREFLIGHT / "README.md", PREFLIGHT / "readiness.json",
        PRIOR / "parent_run.py", PRIOR / "README.md", PRIOR / "results.md",
        PRIOR / "assessment.json", PRIOR / "frozen-inputs.json", PRIOR / "output-pin.json",
        COMP / "row-identities.json", COMP / "output-pin.json",
        TINY_RAW_H / "solve_raw.py", TINY_RAW_H / "assessment.json",
        TINY_RAW_H / "source-pins.json", TINY_RAW_H / "README.md",
        HERE / "prepare_raw.py", HERE / "parent_run.py", HERE / "README.md",
    ]
    paths.update({relative(path): path for path in extra})
    return dict(sorted(paths.items()))


def load_problem():
    if np.__version__ != "2.5.2" or scipy.__version__ != "1.18.1":
        raise AssertionError(f"pinned numerical environment changed: NumPy {np.__version__}, SciPy {scipy.__version__}")
    preflight = import_preflight()
    proposal, state = preflight.build_proposal()
    expected = json.dumps(proposal, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if not (PREFLIGHT / "readiness.json").is_file() or (PREFLIGHT / "readiness.json").read_text() != expected:
        raise AssertionError("pinned fixed-active readiness differs from its exact source inputs")

    with np.load(OPERATORS, allow_pickle=False) as data:
        H_raw, D = data["H"], data["D"]
    with np.load(ANSWER, allow_pickle=False) as data:
        answer = {key: data[key] for key in data.files}
    rows = json.loads(ROW_IDENTITIES.read_text(encoding="utf-8"))

    if H_raw.shape != (1840, 1840) or D.shape != (1840, 300) or len(rows) != 1840:
        raise AssertionError("raw operator/source-row dimensions changed")
    if not np.array_equal(D[answer["active_row_positions"]], answer["D_active"]):
        raise AssertionError("active D rows no longer match the pinned operator")
    if not all(int(row["row"]) == i for i, row in enumerate(rows)):
        raise AssertionError("row identity source position/order changed")

    # Confirm the prior energy matrix only differs from the raw fixed-branch
    # operator by taking the old H symmetric part. Preserve its original
    # inverse-stiffness row scaling and all affine source offsets.
    active = answer["active_row_positions"].astype(np.int64)
    H_active = H_raw[np.ix_(active, active)]
    k = np.asarray(answer["k_active"], dtype=np.float64)
    if np.any(k < 0.0) or not np.isfinite(k).all():
        raise AssertionError("invalid source stiffness rows")
    inverse_k = np.zeros_like(k)
    positive = k > 0.0
    inverse_k[positive] = 1.0 / k[positive]
    old_S = np.asarray(answer["S"], dtype=np.float64)
    expected_old_S = 0.5 * (H_active + H_active.T) + np.diag(inverse_k)
    old_S_difference = max_abs(old_S - expected_old_S)
    if old_S_difference > 1.0e-14:
        raise AssertionError(f"old source Hessian decomposition changed: {old_S_difference}")
    e_active = answer["e_total_full"][active]
    objective_difference = max_abs(answer["linear_objective"] + e_active)
    if objective_difference != 0.0:
        raise AssertionError(f"source affine RHS changed: {objective_difference}")

    families = answer["active_row_family"]
    conditional = families == "conditional_floor_tangent_constraint"
    if int(np.count_nonzero(conditional)) != 50 or int(np.count_nonzero(k == 0.0)) != 50:
        raise AssertionError("held-floor tangent row/stiffness inventory changed")
    if not np.all(conditional == (k == 0.0)):
        raise AssertionError("zero inverse-stiffness rows no longer exactly equal held tangents")
    held_reference = np.asarray(answer["held_reference_active_mm"], dtype=np.float64)
    held_reference_max = max_abs(held_reference[conditional])
    if held_reference_max != 0.0:
        raise AssertionError("held tangent references changed from their frozen zero values")

    # Full source identity is positional. Text labels can repeat, so retain
    # the row position, source group and source element in every failure row.
    for local, global_row in enumerate(active):
        row = rows[int(global_row)]
        if (str(row["row_id"]) != str(answer["active_row_ids"][local])
                or str(row["family"]) != str(families[local])):
            raise AssertionError(f"active source row identity changed at position {global_row}")

    prior = json.loads((PRIOR / "assessment.json").read_text(encoding="utf-8"))
    prior_frozen = json.loads((PRIOR / "frozen-inputs.json").read_text(encoding="utf-8"))
    prior_pin = json.loads((PRIOR / "output-pin.json").read_text(encoding="utf-8"))
    if sha(PRIOR / "assessment.json") != prior_pin.get("assessment_sha256"):
        raise AssertionError("prior parent assessment output pin mismatch")
    if not prior.get("source_freeze_unchanged") or prior.get("candidate_forces_adopted"):
        raise AssertionError("prior fixed-active source result is not an immutable non-adopted record")
    if prior.get("status") != "STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE":
        raise AssertionError("prior comparison status changed")
    previous_comparisons = prior["original_DAT_comparisons"]
    if (previous_comparisons["forces"]["failed_count"] != 25
            or previous_comparisons["projected_q"]["failed_count"] != 0
            or previous_comparisons["rigid_coordinates"]["failed_count"] != 0
            or not all(prior["physical_gates"].values())):
        raise AssertionError("prior attempt's source/physical gate record changed")
    if prior_frozen.get("active_bound_estimate_count") != 734 or prior_frozen.get("floor_mask_changed") is not False:
        raise AssertionError("prior parent fixed-set/floor provenance changed")
    tiny_pins = json.loads((TINY_RAW_H / "source-pins.json").read_text(encoding="utf-8"))
    tiny_assessment = json.loads((TINY_RAW_H / "assessment.json").read_text(encoding="utf-8"))
    if (sha(TINY_RAW_H / "solve_raw.py") != tiny_pins.get("producer_sha256")
            or sha(TINY_RAW_H / "assessment.json") != tiny_pins.get("assessment_sha256")
            or tiny_assessment.get("status") != "PASS_TINY_24_MASKS_AND_RAW_H_FIXED_BRANCH_METHOD"):
        raise AssertionError("tiny raw-H known-answer method fixture is not pinned PASS")

    old_bound_global = np.asarray(state["bound_global"], dtype=np.int64)
    bound_local = np.asarray(state["bound_local"], dtype=np.int64)
    if (old_bound_global.shape != (734,) or bound_local.shape != (734,)
            or len(np.unique(bound_local)) != 734):
        raise AssertionError("fixed provisional active set is no longer exactly 734 rows")
    if not np.array_equal(active[bound_local], old_bound_global):
        raise AssertionError("fixed bound local/global row order changed")
    if np.intersect1d(old_bound_global, answer["closed_floor_normal_rows"]).size:
        raise AssertionError("fixed bound estimate now includes closed floor normals")

    return preflight, proposal, state, H_raw, D, rows, prior, prior_frozen, {
        "H_active": H_active,
        "inverse_k": inverse_k,
        "old_S_difference": old_S_difference,
        "objective_difference": objective_difference,
        "held_reference_max": held_reference_max,
    }


def assemble_bordered(row_block: np.ndarray, D_active: np.ndarray,
                      bound_local: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Build the raw compatibility border and its RHS in documented order."""
    row_block = np.asarray(row_block, dtype=np.float64)
    D_active = np.asarray(D_active, dtype=np.float64)
    bound_local = np.asarray(bound_local, dtype=np.int64)
    n, neq = D_active.shape
    nb = len(bound_local)
    if row_block.shape != (n, n) or len(np.unique(bound_local)) != nb:
        raise ValueError("invalid bordered-system shapes or duplicate lower-bound positions")
    if np.any(bound_local < 0) or np.any(bound_local >= n):
        raise ValueError("lower-bound position is outside the force vector")
    M = np.zeros((n + neq + nb, n + neq + nb), dtype=np.float64)
    M[:n, :n] = row_block
    M[:n, n:n + neq] = D_active
    M[n:n + neq, :n] = D_active.T
    bound_number = np.arange(nb, dtype=np.int64)
    M[bound_local, n + neq + bound_number] = 1.0
    M[n + neq + bound_number, bound_local] = 1.0
    return M, bound_number


def verify_bordered_assembly_oracle() -> dict:
    """Cheap synthetic check for noncontiguous bound-row placement/signs."""
    row_block = np.arange(49, dtype=np.float64).reshape(7, 7) / 17.0
    D_small = np.arange(14, dtype=np.float64).reshape(7, 2) / 11.0
    bound = np.array([1, 5, 6], dtype=np.int64)
    M, bound_number = assemble_bordered(row_block, D_small, bound)
    G = np.zeros((len(bound), len(row_block)), dtype=np.float64)
    G[bound_number, bound] = 1.0
    top_Gt = M[:len(row_block), len(row_block) + D_small.shape[1]:]
    bottom_G = M[len(row_block) + D_small.shape[1]:, :len(row_block)]
    assert np.array_equal(top_Gt, G.T)
    assert np.array_equal(bottom_G, G)
    assert np.count_nonzero(top_Gt) == len(bound)
    assert np.count_nonzero(bottom_G) == len(bound)
    return {
        "status": "PASS_NONCONTIGUOUS_G_BORDER_IDENTITY",
        "synthetic_force_count": len(row_block), "synthetic_equilibrium_count": D_small.shape[1],
        "synthetic_bound_local_rows": bound.tolist(),
        "top_border_equals_G_transpose_exactly": True,
        "bottom_border_equals_G_exactly": True,
        "actual_frame_matrix_assembled": False,
    }


def build_readiness() -> tuple[dict, tuple]:
    preflight, proposal, state, H_raw, D, rows, prior, prior_frozen, checks = load_problem()
    path_inventory = source_path_inventory(preflight)
    source_sha = {name: sha(path) for name, path in path_inventory.items()}
    prior_pins = prior_frozen["source_sha256"]
    changed_prior = [name for name, expected in prior_pins.items() if source_sha.get(name) != expected]
    if changed_prior:
        raise AssertionError(f"the preserved prior 49-source freeze changed: {changed_prior}")
    answer = state["answer"]
    active = answer["active_row_positions"].astype(np.int64)
    families = answer["active_row_family"]
    bound_global = np.asarray(state["bound_global"], dtype=np.int64)
    source_ids = [str(row["row_id"]) for row in rows]
    border_oracle = verify_bordered_assembly_oracle()
    readiness = {
        "schema": "a12_fixed_active_raw_H_comparison_readiness/v1",
        "status": "READY_FOR_PARENT_ONE_SHOT_RAW_H_FIXED_BRANCH_COMPARISON",
        "source_sha256": source_sha,
        "input_source_sha256": proposal["source_sha256"],
        "runtime": {"numpy": np.__version__, "scipy": scipy.__version__,
                    "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"},
        "operator_and_source_identity": {
            "H_raw_shape": list(H_raw.shape), "D_shape": list(D.shape),
            "full_source_rows": len(rows), "unique_text_row_ids": len(set(source_ids)),
            "duplicate_text_labels_preserve_source_position": len(set(source_ids)) < len(source_ids),
            "active_source_rows": int(len(active)), "equilibrium_coordinates": int(D.shape[1]),
            "active_D_equals_raw_D_rows_exactly": True,
            "active_row_identity_and_family_order_exact": True,
            "row_position_is_identity_key": True,
        },
        "fixed_episode_and_set": {
            "source": "same attempt02 saved full-load A12 episode and exact one 734-row nonfloor unilateral bound estimate",
            "active_lower_bound_count": int(len(bound_global)),
            "closed_floor_normal_rows_excluded": True,
            "no_threshold_change_or_active_set_reselection": True,
            "historical_parent_attempt01_status": prior["status"],
            "historical_force_DAT_failed_count": prior["original_DAT_comparisons"]["forces"]["failed_count"],
            "historical_projected_q_failed_count": prior["original_DAT_comparisons"]["projected_q"]["failed_count"],
            "historical_rigid_coordinate_failed_count": prior["original_DAT_comparisons"]["rigid_coordinates"]["failed_count"],
            "historical_physical_gates_all_passed": all(prior["physical_gates"].values()),
            "historical_candidate_adopted": False,
            "historical_parent_frozen_source_map_count": len(prior_frozen["source_sha256"]),
            "all_historical_source_pins_preserved_exactly": True,
            "tiny_raw_H_fixture_status": "PASS_TINY_24_MASKS_AND_RAW_H_FIXED_BRANCH_METHOD",
        },
        "raw_linear_system": {
            "equations": "q=D*a+e-H_raw*f; D.T*f=W; (H_raw_active+diag(inverse_k))*f_active + D_active*lambda + G.T*mu=e_active; G*f_active=0; a=-lambda",
            "matrix_order": int(len(answer["linear_objective"]) + len(answer["W_total"]) + len(bound_global)),
            "row_scaling": "Preserve original inverse-stiffness diagonal exactly; inverse_k=1/k for k>0 and 0 for the 50 held-tangent rows, with original e/reference offsets unchanged.",
            "conditional_floor_tangent_rows": int(np.count_nonzero(families == "conditional_floor_tangent_constraint")),
            "held_reference_max_abs_mm": checks["held_reference_max"],
            "held_references_are_exactly_zero": checks["held_reference_max"] == 0.0,
            "linear_objective_equals_negative_active_e_exactly": checks["objective_difference"] == 0.0,
            "old_energy_S_matches_sym_H_plus_inverse_k_max_difference": checks["old_S_difference"],
            "active_bound_multiplier_identity": "With zero held-reference offsets and f=0 on each selected lower-bound row, the raw bordered row equation gives mu_bound=q_raw_bound. Save and report both vectors/identity discrepancy.",
            "solver": "one unregularized scipy.linalg.solve(..., assume_a='gen') after the unchanged 1e-12 singular-value rank gate; no retries or fallback",
            "border_assembly_oracle": border_oracle,
            "rank_relative_cutoff": KKT_RANK_RELATIVE_CUTOFF,
            "relative_linear_residual_max": KKT_RESIDUAL_TOL,
            "active_force_and_multiplier_gates": {
                "bound_force_max_abs_N": ACTIVE_PRIMAL_DUAL_TOL,
                "free_nonfloor_force_min_N_strictly_above": PROVISIONAL_BOUND_FORCE_TOL_N,
                "bound_multiplier_max_mm_strictly_below": -ACTIVE_PRIMAL_DUAL_TOL,
            },
        },
        "postsolve_audit": {
            "implementation": "reuse the preflight audit_candidate and interval_check without changing formulas/thresholds; append every failed force/q/coordinate source interval by source position",
            "physical_gates": "all ten parent attempt01 raw-H, body force/moment, spring law, unilateral/domain, floor, held and released gates unchanged",
            "DAT_gates": "original force, projected-q and 300 rigid-coordinate center/radius intervals with the same 128-epsilon guard",
            "source_row_failures_include": ["source position", "row_id", "source group", "element", "family", "center", "radius", "roundoff guard", "difference", "ratio"],
            "coordinate_failures_include": ["coordinate position", "body", "within-body component position", "center", "radius", "difference", "ratio"],
            "arrays_saved_after_parent_execution": ["f_active_N", "a_mm", "lambda_eq_mm", "mu_active_bound_mm", "f_full_N", "q_raw_mm", "q_sym_mm", "body_equilibrium_residuals", "raw_source_law_residuals"],
        },
        "scope": {
            "KKT_or_bordered_matrix_assembled_during_readiness": False,
            "factorization_or_solve_during_readiness": False,
            "native_solver_run": False,
            "physical_response_or_state_selection": False,
            "candidate_adopted": False,
            "parent_one_shot_entry_prepared_not_executed": True,
        },
    }
    context = (preflight, proposal, state, H_raw, D, rows, prior, checks)
    return readiness, context


def direct_raw_h_solve(preflight, state, H_raw: np.ndarray, D: np.ndarray) -> dict:
    """One fixed-bound bordered compatibility solve, with original row scaling."""
    answer = state["answer"]
    n = len(answer["linear_objective"])
    neq = len(answer["W_total"])
    bound_local = np.asarray(state["bound_local"], dtype=np.int64)
    active = np.asarray(answer["active_row_positions"], dtype=np.int64)
    D_active = np.asarray(answer["D_active"], dtype=np.float64)
    k = np.asarray(answer["k_active"], dtype=np.float64)
    inv_k = np.zeros_like(k)
    positive = k > 0.0
    inv_k[positive] = 1.0 / k[positive]
    H_active = H_raw[np.ix_(active, active)]
    raw_row_block = H_active + np.diag(inv_k)
    e_active = np.asarray(answer["e_total_full"][active], dtype=np.float64)
    W = np.asarray(answer["W_total"], dtype=np.float64)
    if (H_active.shape != (n, n) or D_active.shape != (n, neq)
            or e_active.shape != (n,) or bound_local.shape != (734,)):
        return {"status": "STOP_INVALID_RAW_BORDERED_SHAPES"}

    nb = len(bound_local)
    order = n + neq + nb
    M, _ = assemble_bordered(raw_row_block, D_active, bound_local)
    rhs = np.r_[e_active, W, np.zeros(nb, dtype=np.float64)]

    try:
        singular = linalg.svdvals(M, check_finite=True)
    except (ValueError, linalg.LinAlgError) as error:
        return {"status": "STOP_RAW_BORDERED_RANK_CHECK_FAILURE", "detail": str(error)}
    sigma_max = float(np.max(singular, initial=0.0))
    sigma_min = float(np.min(singular))
    rank = int(np.count_nonzero(singular > KKT_RANK_RELATIVE_CUTOFF * sigma_max))
    if rank != order:
        return {"status": "STOP_RANK_DEFICIENT_RAW_BORDERED_SYSTEM",
                "matrix_order": order, "numerical_rank": rank,
                "singular_value_ratio": sigma_min / sigma_max if sigma_max else 0.0}

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", linalg.LinAlgWarning)
            solution = linalg.solve(M, rhs, assume_a="gen", check_finite=True)
    except linalg.LinAlgWarning as error:
        return {"status": "STOP_ILL_CONDITIONED_RAW_GENERAL_LU", "detail": str(error),
                "matrix_order": order, "singular_value_ratio": sigma_min / sigma_max}
    except (linalg.LinAlgError, ValueError) as error:
        return {"status": "STOP_RAW_GENERAL_LU_FAILURE", "detail": str(error),
                "matrix_order": order, "singular_value_ratio": sigma_min / sigma_max}

    residual = M @ solution - rhs
    relative_residual = max_abs(residual) / max(
        1.0, float(linalg.norm(M, ord=np.inf)) * float(linalg.norm(solution, ord=np.inf))
        + float(linalg.norm(rhs, ord=np.inf)),
    )
    f_active = solution[:n]
    lambda_eq = solution[n:n + neq]
    mu_active = solution[n + neq:]
    a = -lambda_eq
    nonnegative = np.asarray(answer["nonnegative_active_positions"], dtype=np.int64)
    free = np.setdiff1d(nonnegative, bound_local, assume_unique=True)
    active_force_error = max_abs(f_active[bound_local])
    free_min = float(np.min(f_active[free]))
    mu_max = float(np.max(mu_active))
    active_set_gates = {
        "active_bound_force_within_unchanged_tolerance": active_force_error <= ACTIVE_PRIMAL_DUAL_TOL,
        "free_nonfloor_unilateral_above_original_estimate": free_min > PROVISIONAL_BOUND_FORCE_TOL_N,
        "active_bound_multipliers_strictly_negative": mu_max < -ACTIVE_PRIMAL_DUAL_TOL,
    }
    solver_gates = {
        "full_rank_at_unchanged_cutoff": rank == order,
        "relative_residual_within_unchanged_gate": relative_residual <= KKT_RESIDUAL_TOL,
    }
    status = "PASS_RAW_BORDERED_FIXED_SET" if all(solver_gates.values()) and all(active_set_gates.values()) else "STOP_RAW_BORDERED_OR_FIXED_SET_GATE"
    bound_global = active[bound_local]
    return {
        "status": status,
        "f_active_N": f_active,
        "a_mm": a,
        "lambda_eq_mm": lambda_eq,
        "mu_active_bound_mm": mu_active,
        "matrix_order": order,
        "numerical_rank": rank,
        "singular_value_ratio": sigma_min / sigma_max,
        "relative_residual_inf": relative_residual,
        "absolute_residual_inf": max_abs(residual),
        "active_bound_max_abs_N": active_force_error,
        "free_nonfloor_unilateral_min_N": free_min,
        "active_bound_max_multiplier_mm": mu_max,
        "solver_gates": solver_gates,
        "fixed_set_gates": active_set_gates,
        "bound_local_rows": bound_local,
        "bound_global_rows": bound_global,
        "raw_row_block": raw_row_block,
        "bordered_residual": residual,
    }


def _interval_failures(value: np.ndarray, center: np.ndarray, radius: np.ndarray,
                       records: list[dict], quantity: str) -> tuple[dict, list[dict]]:
    value = np.asarray(value)
    center = np.asarray(center)
    radius = np.asarray(radius)
    if value.shape != center.shape or value.shape != radius.shape:
        raise AssertionError(f"DAT vector shape differs: {quantity}")
    diff = np.abs(value - center)
    guard = 128 * np.finfo(float).eps * (np.abs(value) + np.abs(center) + 1.0)
    allowed = radius + guard
    ratios = diff / allowed
    failed = []
    for i in np.flatnonzero(diff > allowed):
        item = {
            "quantity": quantity, "index": int(i),
            "prediction": float(value[i]), "native_center": float(center[i]),
            "native_radius": float(radius[i]), "roundoff_guard": float(guard[i]),
            "allowed_absolute_difference": float(allowed[i]),
            "absolute_difference": float(diff[i]), "ratio": float(ratios[i]),
        }
        item.update(records[int(i)])
        failed.append(item)
    summary = {
        "pass_gate": not failed,
        "failed_count": len(failed),
        "max_abs_difference": float(np.max(diff, initial=0.0)),
        "max_ratio": float(np.max(ratios, initial=0.0)),
        "worst_full_position": int(np.argmax(ratios)),
    }
    return summary, failed


def _source_row_record(row: dict, index: int) -> dict:
    return {
        "global_source_row_position": int(index),
        "row_identity": {
            "row_id": str(row["row_id"]), "source_group": str(row["source_group"]),
            "source_element": int(row["source_element"]), "family": str(row["family"]),
            "ownership": row["ownership"],
        },
    }


def audit_verbose(preflight, answer: dict, H_raw: np.ndarray, D: np.ndarray,
                  rows: list[dict], solve: dict) -> tuple[dict, dict[str, np.ndarray]]:
    f_active = solve["f_active_N"]
    a = solve["a_mm"]
    active = np.asarray(answer["active_row_positions"], dtype=np.int64)
    f = np.zeros(1840, dtype=np.float64)
    f[active] = f_active
    e = np.asarray(answer["e_total_full"], dtype=np.float64)
    q_raw = D @ a + e - H_raw @ f
    H_sym = 0.5 * (H_raw + H_raw.T)
    q_sym = D @ a + e - H_sym @ f
    physical = preflight.audit_candidate(answer, H_raw, D, f_active, a)
    if len(rows) != len(f) or any(int(row["row"]) != i for i, row in enumerate(rows)):
        raise AssertionError("source row identity order changed during interval audit")
    source_records = [_source_row_record(row, i) for i, row in enumerate(rows)]
    coordinate_records = []
    body_names = [str(item) for item in answer["body_names_rigid_column_order"]]
    if len(body_names) != 50 or len(a) != 300:
        raise AssertionError("rigid coordinate/body identity order changed")
    for i in range(300):
        coordinate_records.append({
            "body": body_names[i // 6], "within_body_component_index": int(i % 6),
            "component_indexing": "source order 0..5 per body; stored coordinate units are preserved exactly",
        })
    source_checks = physical["original_DAT_comparisons"]
    force_summary, force_failures = _interval_failures(
        f, answer["f_native_full_N"], answer["f_native_rounding_radius_full_N"],
        source_records, "force_N",
    )
    q_summary, q_failures = _interval_failures(
        q_raw, answer["q_native_full_mm"], answer["q_native_DAT_rounding_radius_full_mm"],
        source_records, "projected_q_mm",
    )
    a_summary, a_failures = _interval_failures(
        a, answer["a_native_mm_and_scaled_rotation"], answer["a_native_DAT_rounding_radius"],
        coordinate_records, "rigid_coordinate_source_units",
    )
    for key, actual in (("forces", force_summary), ("projected_q", q_summary), ("rigid_coordinates", a_summary)):
        expected = source_checks[key]
        for field in ("pass_gate", "failed_count", "max_abs_difference", "max_ratio", "worst_full_position"):
            if actual[field] != expected[field]:
                raise AssertionError(f"rowwise {key} interval replay differs at {field}: {actual[field]} != {expected[field]}")

    body_eq = (D.T @ f - answer["W_total"]).reshape((50, 6))
    body_force_max = np.max(np.abs(body_eq[:, :3]), axis=1)
    body_moment_max = 1000.0 * np.max(np.abs(body_eq[:, 3:]), axis=1)
    body_failures = [
        {"body": body_names[i], "body_index": i,
         "force_residual_xyz_N": body_eq[i, :3].tolist(),
         "moment_residual_scaled_xyz_Nmm": (1000.0 * body_eq[i, 3:]).tolist()}
        for i in range(50) if body_force_max[i] > 0.1 or body_moment_max[i] > 2.0
    ]

    families = answer["active_row_family"]
    unilateral = families == "unilateral_springa"
    finite = families != "conditional_floor_tangent_constraint"
    q_active = q_raw[active]
    k = answer["k_active"]
    expected_force = k[finite] * np.where(unilateral[finite], np.maximum(q_active[finite], 0.0), q_active[finite])
    law_residual = np.zeros(len(active), dtype=np.float64)
    law_residual[finite] = f_active[finite] - expected_force
    source_law_failures = [
        {"active_local_row": int(i), **_source_row_record(rows[int(active[i])], int(active[i])),
         "force_N": float(f_active[i]), "expected_force_N": float(f_active[i] - law_residual[i]),
         "law_residual_N": float(law_residual[i])}
        for i in np.flatnonzero(np.abs(law_residual) > 0.1)
    ]
    unilateral_global = active[np.flatnonzero(unilateral)]
    unilateral_failures = [
        {**_source_row_record(rows[int(row)], int(row)), "force_N": float(f[int(row)])}
        for row in unilateral_global if f[int(row)] < -1.0e-8
    ]
    raw_sym_shift = np.abs(q_sym - q_raw)
    compatibility_failures = [
        {**_source_row_record(rows[i], i), "q_raw_mm": float(q_raw[i]),
         "q_sym_mm": float(q_sym[i]), "absolute_shift_mm": float(raw_sym_shift[i])}
        for i in np.flatnonzero(raw_sym_shift > 2.0e-8)
    ]

    closed = np.asarray(answer["closed_floor_normal_rows"], dtype=np.int64)
    opened = np.asarray(answer["open_floor_normal_rows"], dtype=np.int64)
    held = np.asarray(answer["held_floor_tangent_rows"], dtype=np.int64)
    released = np.asarray(answer["released_floor_tangent_rows"], dtype=np.int64)
    floor_failures = {
        "closed_normal_q_not_strict": [{**_source_row_record(rows[i], i), "q_raw_mm": float(q_raw[i])}
                                       for i in closed if q_raw[i] <= 2e-8],
        "closed_normal_force_not_strict": [{**_source_row_record(rows[i], i), "force_N": float(f[i])}
                                            for i in closed if f[i] <= 1e-8],
        "open_normal_q_not_strict": [{**_source_row_record(rows[i], i), "q_raw_mm": float(q_raw[i])}
                                      for i in opened if q_raw[i] >= -2e-8],
        "open_normal_force_nonzero": [{**_source_row_record(rows[i], i), "force_N": float(f[i])}
                                      for i in opened if f[i] != 0.0],
        "held_tangent_reference": [{**_source_row_record(rows[i], i), "q_raw_mm": float(q_raw[i])}
                                   for i in held if abs(q_raw[i]) > 2e-8],
        "released_tangent_nonzero": [{**_source_row_record(rows[i], i), "force_N": float(f[i])}
                                      for i in released if f[i] != 0.0],
    }
    max_bound_q_mu_difference = max_abs(
        solve["mu_active_bound_mm"] - q_raw[solve["bound_global_rows"]]
    )
    verbose = {
        "physical_gates": physical["physical_gates"],
        "original_DAT_comparisons": {
            "forces": force_summary, "projected_q": q_summary, "rigid_coordinates": a_summary,
        },
        "failed_source_intervals": {
            "forces": force_failures, "projected_q": q_failures,
            "rigid_coordinates": a_failures,
        },
        "source_law_failure_rows_over_unchanged_0_1N_gate": source_law_failures,
        "unilateral_sign_failure_rows_over_unchanged_gate": unilateral_failures,
        "raw_H_compatibility_failure_rows_over_unchanged_gate": compatibility_failures,
        "body_equilibrium_failures_over_unchanged_gates": body_failures,
        "floor_failure_rows_over_unchanged_gates": floor_failures,
        "max_body_force_residual_N": physical["max_body_force_residual_N"],
        "max_body_moment_residual_Nmm": physical["max_body_moment_residual_Nmm"],
        "max_source_law_residual_N": physical["max_source_law_residual_N"],
        "max_raw_vs_symmetric_H_shift_mm": physical["max_raw_vs_symmetric_H_shift_mm"],
        "floor_summary": physical["floor"],
        "max_active_bound_q_minus_mu_mm": max_bound_q_mu_difference,
        "active_bound_q_equals_mu_by_raw_bordered_row_equation": True,
        "candidate_forces_adopted": False,
        "mechanical_acceptance": False,
    }
    saved = {
        "f_active_N": f_active,
        "a_mm": a,
        "lambda_eq_mm": solve["lambda_eq_mm"],
        "mu_active_bound_mm": solve["mu_active_bound_mm"],
        "f_full_N": f,
        "q_raw_mm": q_raw,
        "q_sym_mm": q_sym,
        "body_equilibrium_residuals_N_and_unscaled_moment": body_eq,
        "raw_source_law_residuals_N_active_order": law_residual,
        "raw_bordered_equation_residual": solve["bordered_residual"],
        "fixed_bound_local_positions": solve["bound_local_rows"],
        "fixed_bound_global_source_positions": solve["bound_global_rows"],
    }
    return verbose, saved


def solve_and_audit(context: tuple) -> tuple[dict, dict[str, np.ndarray] | None]:
    preflight, proposal, state, H_raw, D, rows, prior, checks = context
    answer = state["answer"]
    solved = direct_raw_h_solve(preflight, state, H_raw, D)
    kkt_report = {key: value for key, value in solved.items()
                  if key not in {"f_active_N", "a_mm", "lambda_eq_mm", "mu_active_bound_mm",
                                 "raw_row_block", "bordered_residual", "bound_local_rows", "bound_global_rows"}}
    report = {
        "status": solved["status"], "native_run": False,
        "candidate_forces_adopted": False, "mechanical_acceptance": False,
        "proposal_source_sha256": proposal["source_sha256"], "raw_H_fixed_set_solver": kkt_report,
        "comparison_to_prior_symmetric_attempt": {
            "prior_status": prior["status"],
            "prior_force_DAT_failed_count": prior["original_DAT_comparisons"]["forces"]["failed_count"],
            "prior_projected_q_DAT_failed_count": prior["original_DAT_comparisons"]["projected_q"]["failed_count"],
            "prior_rigid_coordinate_DAT_failed_count": prior["original_DAT_comparisons"]["rigid_coordinates"]["failed_count"],
            "prior_max_raw_H_source_law_residual_N": prior["max_source_law_residual_N"],
            "prior_max_raw_vs_symmetric_H_shift_mm": prior["max_raw_vs_symmetric_H_shift_mm"],
        },
    }
    if "f_active_N" not in solved:
        return report, None
    audit, saved = audit_verbose(preflight, answer, H_raw, D, rows, solved)
    report.update(audit)
    physical_pass = all(audit["physical_gates"].values())
    source_pass = all(item["pass_gate"] for item in audit["original_DAT_comparisons"].values())
    fixed_set_pass = all(solved["fixed_set_gates"].values())
    linear_pass = all(solved["solver_gates"].values())
    report["source_and_physical_gates_all_pass"] = bool(physical_pass and source_pass and fixed_set_pass and linear_pass)
    raw_force_failures = audit["original_DAT_comparisons"]["forces"]["failed_count"]
    if not linear_pass or not fixed_set_pass:
        explanation = "INCONCLUSIVE_RAW_BRANCH_STOPPED_BEFORE_SOURCE_COMPARISON_ACCEPTANCE"
    elif raw_force_failures == 0 and physical_pass and source_pass:
        explanation = "RAW_H_FIXED_BRANCH_PASSES_ALL_ORIGINAL_SOURCE_INTERVALS_WHERE_PRIOR_SYMMETRIC_ATTEMPT_FAILED_FORCE_INTERVALS"
    elif raw_force_failures < prior["original_DAT_comparisons"]["forces"]["failed_count"]:
        explanation = "RAW_H_REDUCES_BUT_DOES_NOT_REMOVE_PRIOR_FORCE_INTERVAL_FAILURES"
    else:
        explanation = "RAW_H_FIXED_BRANCH_DOES_NOT_REMOVE_PRIOR_FORCE_INTERVAL_FAILURES"
    report["symmetrization_explanation_disposition"] = explanation
    report["status"] = (
        "PASS_RAW_H_FIXED_EPISODE_SOURCE_REPRODUCTION_ONLY"
        if physical_pass and source_pass and fixed_set_pass and linear_pass
        else "STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE"
    )
    return report, saved


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-readiness", action="store_true")
    group.add_argument("--verify-ready", action="store_true")
    args = parser.parse_args()
    readiness, _ = build_readiness()
    rendered = json.dumps(readiness, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write_readiness:
        READINESS.write_text(rendered, encoding="utf-8")
        print("Wrote raw-H readiness only; no bordered matrix assembled or solved")
        return
    if not READINESS.exists() or READINESS.read_text(encoding="utf-8") != rendered:
        raise SystemExit("STOP_READINESS_OR_SOURCE_PIN_MISMATCH")
    print("PASS_RAW_H_FIXED_BRANCH_READINESS: exact 734-row set, no matrix solve")


if __name__ == "__main__":
    main()
