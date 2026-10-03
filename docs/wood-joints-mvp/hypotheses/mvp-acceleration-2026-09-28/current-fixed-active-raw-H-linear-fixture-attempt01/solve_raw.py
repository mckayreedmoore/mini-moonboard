"""Tiny-only raw-H fixed-active linear compatibility/equilibrium preflight.

No A12 arrays/operators, frame solve, or native solver are read or run here.
The earlier fixture module is imported only for its tiny source branch
assembly, its 24-mask source comparisons, and its existing sign/rank/invalid
set oracles. Its frame-diagnostic reader is deliberately not called.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
OLD_REFINER = BASE / "current-fixed-active-kkt-refinement-fixture-attempt01/refine.py"
PINS_PATH = HERE / "source-pins.json"
OUTPUT = HERE / "assessment.json"

INPUT_PINS = {
    "known-answer.json": "8b42e4282952d8174f93b5f6138de14d0c88cbb1602d3968665aba5558045e88",
    "fixed-mask-dual-qp.json": "a3bd6f411f25185d909bd6751f1f3ad17142e61c7a5e98806365e6911c9ab59c",
    "solve_fixture.py": "87641f8d3622f3e38350f41c511556e76284a8df5b7ee812c925f2966499cbba",
    "refine.py": "ef94dbbc1048a86aeeadff2219b1129e58925510ebce72dc0464e761e56374c4",
}
LINEAR_RANK_CUTOFF = 1.0e-12
LINEAR_RESIDUAL_TOL = 2.0e-10
SOURCE_TOL = 2.0e-9
MASK_TOL = 2.0e-8


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def max_abs(value: np.ndarray) -> float:
    return float(np.max(np.abs(value), initial=0.0))


def load_tiny_sources() -> tuple[dict, dict, object]:
    observed = {
        "known-answer.json": sha(KNOWN),
        "fixed-mask-dual-qp.json": sha(OLD_RESULT),
        "solve_fixture.py": sha(OLD_PRODUCER),
        "refine.py": sha(OLD_REFINER),
    }
    if observed != INPUT_PINS:
        raise AssertionError(f"pinned tiny source changed: {observed}")
    known = json.loads(KNOWN.read_text(encoding="utf-8"))
    old = json.loads(OLD_RESULT.read_text(encoding="utf-8"))
    assert known["status"] == "ALL_TINY_FIXTURES_REPLAYED"
    assert old["status"] == "PASS_TINY_SOURCE_BRANCHES_AND_KKT_FIXTURES"
    assert len(known["results"]) == len(old["source_branch_cases"]) == 8
    assert sum(case["possible_binary_masks"] for case in known["results"]) == 24

    # Load only functions over those pinned tiny JSON records. Do not call
    # refine.produce(), load_pinned_inputs(), or read_a12_attempts(): the latter
    # paths also inspect a frame-run diagnostic candidate.
    spec = importlib.util.spec_from_file_location("pinned_tiny_kkt_refiner", OLD_REFINER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load pinned tiny refiner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return known, old, module


def solve_fixed_branch(
    D: np.ndarray,
    H: np.ndarray,
    e: np.ndarray,
    W: np.ndarray,
    force_rows: list[int],
    laws: dict[int, tuple[str, float, float]],
) -> dict:
    """Solve q=D a+e-H f, D.T f=W, with one fixed linear law per force row.

    A law is either ('spring', k, offset), meaning f_i=k_i*q_i+offset, or
    ('held_q', target, 0), meaning q_i=target. Unlisted force rows are zero.
    The square system is solved with SciPy's general (pivoted LU) path because
    raw H need not be symmetric. No energy/Hessian symmetrization is applied.
    """
    D = np.asarray(D, dtype=np.float64)
    H = np.asarray(H, dtype=np.float64)
    e = np.asarray(e, dtype=np.float64)
    W = np.asarray(W, dtype=np.float64)
    force_rows = list(map(int, force_rows))
    if (D.ndim != 2 or H.shape != (D.shape[0], D.shape[0])
            or e.shape != (D.shape[0],) or W.shape != (D.shape[1],)
            or len(set(force_rows)) != len(force_rows)
            or any(row < 0 or row >= D.shape[0] for row in force_rows)
            or set(force_rows) != set(laws)):
        return {"status": "STOP_INVALID_LINEAR_SYSTEM_SHAPES_OR_ROWS"}
    if not (np.isfinite(D).all() and np.isfinite(H).all()
            and np.isfinite(e).all() and np.isfinite(W).all()):
        return {"status": "STOP_NONFINITE_LINEAR_SYSTEM_INPUT"}

    nrow, ndof = D.shape
    nf = len(force_rows)
    M = np.zeros((nf + ndof, ndof + nf), dtype=np.float64)
    rhs = np.zeros(nf + ndof, dtype=np.float64)
    local = {row: index for index, row in enumerate(force_rows)}
    H_active = H[:, force_rows]
    for j, row in enumerate(force_rows):
        kind, first, second = laws[row]
        if kind == "spring":
            k, offset = float(first), float(second)
            if not np.isfinite(k) or k <= 0.0 or not np.isfinite(offset):
                return {"status": "STOP_INVALID_SPRING_LAW"}
            # f_i - k_i (D_i a + e_i - H_i f) = offset.
            M[j, :ndof] = -k * D[row]
            M[j, ndof:] = k * H_active[row]
            M[j, ndof + local[row]] += 1.0
            rhs[j] = k * e[row] + offset
        elif kind == "held_q":
            target = float(first)
            if not np.isfinite(target) or not np.isfinite(float(second)):
                return {"status": "STOP_INVALID_HELD_Q_LAW"}
            # D_i a + e_i - H_i f = target.
            M[j, :ndof] = D[row]
            M[j, ndof:] = -H_active[row]
            rhs[j] = target - e[row]
        else:
            return {"status": "STOP_INVALID_LINEAR_LAW_KIND"}

    M[nf:, ndof:] = D[force_rows].T
    rhs[nf:] = W
    singular_values = linalg.svdvals(M, check_finite=True)
    sigma_max = float(np.max(singular_values, initial=0.0))
    sigma_min = float(np.min(singular_values)) if singular_values.size else 0.0
    rank = int(np.count_nonzero(singular_values > LINEAR_RANK_CUTOFF * sigma_max))
    if rank != M.shape[0]:
        return {
            "status": "STOP_RANK_DEFICIENT_LINEAR_SYSTEM",
            "matrix_order": int(M.shape[0]),
            "numerical_rank": rank,
            "singular_value_ratio": sigma_min / sigma_max if sigma_max else 0.0,
        }
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", linalg.LinAlgWarning)
            z = linalg.solve(M, rhs, assume_a="gen", check_finite=True)
    except linalg.LinAlgWarning as error:
        return {"status": "STOP_ILL_CONDITIONED_GENERAL_LU", "detail": str(error)}
    except linalg.LinAlgError as error:
        return {"status": "STOP_SINGULAR_GENERAL_LU", "detail": str(error)}

    a, f_active = z[:ndof], z[ndof:]
    f = np.zeros(nrow, dtype=np.float64)
    f[force_rows] = f_active
    q = D @ a + e - H[:, force_rows] @ f_active
    residual = M @ z - rhs
    relative_residual = max_abs(residual) / max(
        1.0,
        float(linalg.norm(M, ord=np.inf)) * float(linalg.norm(z, ord=np.inf))
        + float(linalg.norm(rhs, ord=np.inf)),
    )
    if relative_residual > LINEAR_RESIDUAL_TOL:
        return {
            "status": "STOP_GENERAL_LU_RESIDUAL",
            "matrix_order": int(M.shape[0]),
            "relative_residual_inf": relative_residual,
            "absolute_residual_inf": max_abs(residual),
        }

    law_residuals = []
    for row in force_rows:
        kind, first, second = laws[row]
        if kind == "spring":
            law_residuals.append(f[row] - float(first) * q[row] - float(second))
        else:
            law_residuals.append(q[row] - float(first))
    balance = D.T @ f - W
    return {
        "status": "PASS_FIXED_BRANCH_GENERAL_LU",
        "a": a,
        "f": f,
        "q": q,
        "matrix_order": int(M.shape[0]),
        "rank": rank,
        "singular_value_ratio": sigma_min / sigma_max,
        "relative_residual_inf": relative_residual,
        "absolute_residual_inf": max_abs(residual),
        "law_residual_inf": max_abs(np.asarray(law_residuals)),
        "balance_residual_inf": max_abs(balance),
    }


def solve_tiny_mask(
    case: dict, mask: tuple[bool, ...], model: dict, active_lower_local: list[int]
) -> dict:
    src = case["selector_input"]
    internal_rows = len(model["K"])
    active_lower_local = set(map(int, active_lower_local))
    force_rows = []
    laws: dict[int, tuple[str, float, float]] = {}
    for local_row, row in enumerate(model["active_global_rows"]):
        if row < internal_rows:
            force_rows.append(row)
            laws[row] = ("spring", 1.0, 0.0)
            continue
        contact_row = row - internal_rows
        cell, component = divmod(contact_row, 2)
        if component == 0:
            force_rows.append(row)
            laws[row] = ("held_q", float(model["qp_reference"][cell]), 0.0)
        elif local_row not in active_lower_local:
            force_rows.append(row)
            laws[row] = ("spring", float(src["normal_penalty_n_per_mm"]), 0.0)
        else:
            # An active f>=0 lower bound prescribes f=0. The associated
            # complementarity multiplier leaves q free; do not impose the
            # closed spring law on this bound row.
            continue
    return solve_fixed_branch(
        model["D_all"], model["H_all"], model["e_all"], model["W"], force_rows, laws
    )


def branch_reasons(case: dict, mask: tuple[bool, ...], result: dict, model: dict) -> list[str]:
    src = case["selector_input"]
    ninternal = len(model["K"])
    contact_f = result["f"][ninternal:]
    contact_q = result["q"][ninternal:]
    reasons: list[str] = []
    k_normal = float(src["normal_penalty_n_per_mm"])
    for i, closed in enumerate(mask):
        tangent_f, normal_f = contact_f[2 * i:2 * i + 2]
        tangent_q, normal_q = contact_q[2 * i:2 * i + 2]
        if closed:
            if abs(tangent_q - model["qp_reference"][i]) > MASK_TOL:
                reasons.append(f"cell_{i}_held_tangent_reference_mismatch")
            if normal_f < -MASK_TOL:
                reasons.append(f"cell_{i}_negative_closed_normal_force")
            if normal_q < -MASK_TOL:
                reasons.append(f"cell_{i}_closed_normal_extension_negative")
            if abs(normal_q - normal_f / k_normal) > MASK_TOL:
                reasons.append(f"cell_{i}_closed_normal_spring_law_mismatch")
        else:
            if abs(tangent_f) > MASK_TOL or abs(normal_f) > MASK_TOL:
                reasons.append(f"cell_{i}_open_contact_force_nonzero")
            if normal_q > MASK_TOL:
                reasons.append(f"cell_{i}_open_normal_extension_positive")
    if max_abs(model["D_all"][:ninternal] @ result["a"] - result["f"][:ninternal]) > 2.0e-8:
        reasons.append("bilateral_spring_bank_law_mismatch")
    if result["balance_residual_inf"] > 2.0e-7:
        reasons.append("source_equilibrium_residual")
    return reasons


def nonsymmetric_high_k_oracle() -> dict:
    # Construct a small, fully specified fixed bilateral branch. A is not a
    # free optimization variable here: the equations are compatibility,
    # force balance, and two spring laws. The known answer defines e from the
    # chosen (a,f) through the raw source equation, without using K*u as a load.
    D = np.array([[1.0], [1.0]])
    H_raw = np.array([[1.0e-6, 4.0e-7], [0.0, 1.0e-6]])
    H_sym = 0.5 * (H_raw + H_raw.T)
    k = np.array([1.0e6, 1.0e6])
    a_expected = np.array([0.0])
    f_expected = np.array([1.0, 2.0])
    q_expected = f_expected / k
    W = D.T @ f_expected
    e = q_expected - D @ a_expected + H_raw @ f_expected
    force_rows = [0, 1]
    laws = {i: ("spring", float(k[i]), 0.0) for i in force_rows}

    raw = solve_fixed_branch(D, H_raw, e, W, force_rows, laws)
    sym = solve_fixed_branch(D, H_sym, e, W, force_rows, laws)
    assert raw["status"] == sym["status"] == "PASS_FIXED_BRANCH_GENERAL_LU"
    raw_answer_error = max(
        max_abs(raw["a"] - a_expected),
        max_abs(raw["f"] - f_expected),
        max_abs(raw["q"] - q_expected),
    )
    assert raw_answer_error < 1.0e-10

    # Evaluate the Hsym solution against the original raw-H constitutive law.
    q_sym_in_raw_source = D @ sym["a"] + e - H_raw @ sym["f"]
    raw_law_residual_after_sym_solve = sym["f"] - k * q_sym_in_raw_source
    sym_force_error = max_abs(sym["f"] - f_expected)
    raw_law_error = max_abs(raw_law_residual_after_sym_solve)
    assert sym_force_error > 1.0e-2
    assert raw_law_error > 1.0e-2
    assert max_abs(raw["f"] - sym["f"]) > 1.0e-2
    return {
        "status": "PASS_RAW_VS_SYMMETRIZED_HIGH_K_DISCRIMINATOR",
        "construction": "e=q_expected-D*a_expected+H_raw*f_expected; W=D.T*f_expected",
        "D": D.tolist(), "H_raw_mm_per_N": H_raw.tolist(),
        "H_sym_mm_per_N": H_sym.tolist(), "k_N_per_mm": k.tolist(),
        "e_mm": e.tolist(), "W_N": W.tolist(),
        "expected": {"a": a_expected.tolist(), "f_N": f_expected.tolist(), "q_mm": q_expected.tolist()},
        "raw_general_lu": {
            "status": raw["status"], "a": raw["a"].tolist(), "f_N": raw["f"].tolist(),
            "q_mm": raw["q"].tolist(), "known_answer_max_error": raw_answer_error,
            "raw_spring_law_residual_inf_N": raw["law_residual_inf"],
            "balance_residual_inf_N": raw["balance_residual_inf"],
            "relative_matrix_residual_inf": raw["relative_residual_inf"],
            "singular_value_ratio": raw["singular_value_ratio"],
        },
        "symmetric_operator_general_lu": {
            "status": sym["status"], "a": sym["a"].tolist(), "f_N": sym["f"].tolist(),
            "q_sym_mm": sym["q"].tolist(), "force_error_from_raw_answer_inf_N": sym_force_error,
            "raw_H_q_mm": q_sym_in_raw_source.tolist(),
            "original_raw_H_spring_law_residual_inf_N": raw_law_error,
            "relative_matrix_residual_inf": sym["relative_residual_inf"],
        },
        "interpretation": "For this deliberately nonsymmetric fixed branch, general LU with H_raw recovers the known source-compatible state. Replacing H_raw by H_sym changes the branch force and fails the original raw-H spring law despite solving its own linear system accurately.",
    }


def produce() -> dict:
    known, old, tiny = load_tiny_sources()
    old_cases = {case["id"]: case for case in old["source_branch_cases"]}
    mask_cases = []
    mask_count = 0
    max_errors = {"a_mm": 0.0, "f_N": 0.0, "q_mm": 0.0}
    max_linear_residual = 0.0
    max_balance = 0.0
    minimum_rank_ratio = float("inf")

    for case in known["results"]:
        source_case = old_cases[case["id"]]
        old_by_mask = {tuple(branch["closed_mask"]): branch for branch in source_case["branches"]}
        branches = []
        case_errors = {"a_mm": 0.0, "f_N": 0.0, "q_mm": 0.0}
        ncontact = len(case["selector_input"]["tangent_reference_mm"])
        for mask in itertools.product((False, True), repeat=ncontact):
            old_branch = old_by_mask[mask]
            model = tiny.assemble_tiny_branch(case, mask)
            source_kkt = tiny.refine_branch(case, mask, old_branch)
            linear_candidates = [
                solve_tiny_mask(case, mask, model, active_lower)
                for active_lower in source_kkt["valid_kkt_active_sets"]
            ]
            if any(result["status"] != "PASS_FIXED_BRANCH_GENERAL_LU" for result in linear_candidates):
                raise AssertionError(f"linear branch failed {case['id']} {mask}: {linear_candidates}")
            result = linear_candidates[0]
            for candidate in linear_candidates[1:]:
                for key in ("a", "f", "q"):
                    if max_abs(candidate[key] - result[key]) > SOURCE_TOL:
                        raise AssertionError(
                            f"multiple active-set raw-H primal results differ {case['id']} {mask} {key}"
                        )

            contact_f = result["f"][len(model["K"]):]
            contact_q = result["q"][len(model["K"]):]
            tangent_f, normal_f = contact_f[0::2], contact_f[1::2]
            reasons = branch_reasons(case, mask, result, model)
            admissible = not reasons
            if admissible != source_kkt["admissible"]:
                raise AssertionError(
                    f"raw-H branch classification differs {case['id']} {mask}: "
                    f"raw={reasons}, source={source_kkt['rejection']}"
                )

            expected_contact_f = np.empty_like(contact_f)
            expected_contact_f[0::2] = np.asarray(source_kkt["tangent_forces_N"])
            expected_contact_f[1::2] = np.asarray(source_kkt["normal_forces_N"])
            comparisons = {
                "a_mm": max_abs(result["a"] - np.asarray(source_kkt["u_mm"])),
                "f_N": max_abs(contact_f - expected_contact_f),
                "q_mm": max_abs(contact_q - np.asarray(source_kkt["contact_q_mm"])),
            }
            for key, error in comparisons.items():
                max_errors[key] = max(max_errors[key], error)
                case_errors[key] = max(case_errors[key], error)
                if error > SOURCE_TOL:
                    raise AssertionError(f"raw-H {key} mismatch {case['id']} {mask}: {error}")

            branches.append({
                "closed_mask": list(mask), "admissible": admissible,
                "rejection": reasons, "u_mm": result["a"].tolist(),
                "contact_q_mm": contact_q.tolist(),
                "tangent_forces_N": tangent_f.tolist(), "normal_forces_N": normal_f.tolist(),
            })
            mask_count += 1
            max_linear_residual = max(max_linear_residual, result["relative_residual_inf"])
            max_balance = max(max_balance, result["balance_residual_inf"])
            minimum_rank_ratio = min(minimum_rank_ratio, result["singular_value_ratio"])

        classification = tiny.classify_branches(branches)
        assert len(branches) == case["possible_binary_masks"]
        assert classification == case["classification"]
        assert [branch["closed_mask"] for branch in branches if branch["admissible"]] == [
            candidate["closed_mask"] for candidate in case["candidate_masks"]
        ]
        mask_cases.append({
            "id": case["id"], "expected_classification": case["classification"],
            "raw_H_general_LU_classification": classification,
            "mask_count": len(branches),
            "admissible_mask_count": sum(branch["admissible"] for branch in branches),
            "max_source_error": case_errors,
        })
    assert mask_count == 24

    # Reuse the earlier fixture's nonzero-H/e sign, rank-stop and invalid-set
    # checks, then independently solve its sign oracle with the raw-H method.
    prior_sign = tiny.sign_fixture(old)
    assert prior_sign["status"] == "PASS_DIRECT_KKT_SIGN_FIXTURE"
    sign_source = old["nonzero_H_e_sign_fixture"]
    sign_D = np.asarray(sign_source["D"], dtype=np.float64)
    sign_H = np.asarray(sign_source["H"], dtype=np.float64)
    sign_e = np.asarray(sign_source["e"], dtype=np.float64)
    sign_k = np.asarray(sign_source["spring_k"], dtype=np.float64)
    sign = solve_fixed_branch(
        sign_D, sign_H, sign_e, np.asarray(sign_source["W"], dtype=np.float64),
        list(range(len(sign_k))),
        {i: ("spring", float(sign_k[i]), 0.0) for i in range(len(sign_k))},
    )
    assert sign["status"] == "PASS_FIXED_BRANCH_GENERAL_LU"
    assert max_abs(sign["a"] - np.asarray(sign_source["known_answer_a"])) <= SOURCE_TOL
    assert max_abs(sign["f"] - np.asarray(sign_source["known_answer_f"])) <= SOURCE_TOL
    assert max_abs(sign["q"] - np.asarray(sign_source["known_answer_q"])) <= SOURCE_TOL
    stop_oracles = tiny.stop_oracles()
    assert stop_oracles["dependent_equalities"]["status"] == "STOP_RANK_DEFICIENT_KKT"
    assert stop_oracles["unconstrained_flat_mode"]["status"] == "STOP_RANK_DEFICIENT_KKT"
    assert stop_oracles["invalid_active_index"]["status"] == "STOP_INVALID_ACTIVE_SET"
    assert stop_oracles["wrong_active_set_dual_sign"]["status"] == "STOP_INVALID_ACTIVE_SET"

    return {
        "schema": "fixed_active_raw_H_linear_fixture/v1",
        "status": "PASS_TINY_24_MASKS_AND_RAW_H_FIXED_BRANCH_METHOD",
        "method": {
            "equations": "q=D*a+e-H_raw*f; D.T*f=W; fixed active row laws are f_i=k_i*q_i+offset or q_i=held_reference; unlisted force rows are exactly zero",
            "linear_system": "general nonsymmetric square compatibility/equilibrium system in [a,f_active]",
            "solver": "scipy.linalg.solve(..., assume_a='gen') (general LU); original unsymmetrized H is used",
            "branch_scope": "one declared fixed mask/active relation at a time; tiny-mask enumeration only",
            "rank_relative_cutoff": LINEAR_RANK_CUTOFF,
            "relative_linear_residual_gate": LINEAR_RESIDUAL_TOL,
            "source_comparison_tolerance": SOURCE_TOL,
            "no_pseudoinverse_or_regularization": True,
            "no_energy_minimization_or_global_contact_claim": True,
        },
        "input_sha256": INPUT_PINS,
        "tiny_mask_count": mask_count,
        "tiny_mask_cases": mask_cases,
        "max_source_error": max_errors,
        "max_linear_relative_residual": max_linear_residual,
        "max_balance_residual": max_balance,
        "minimum_linear_singular_value_ratio": minimum_rank_ratio,
        "nonzero_H_e_sign_oracle": {
            "previous_fixture_oracle": prior_sign["status"],
            "status": sign["status"], "a": sign["a"].tolist(), "f": sign["f"].tolist(),
            "q": sign["q"].tolist(), "law_residual_inf": sign["law_residual_inf"],
            "balance_residual_inf": sign["balance_residual_inf"],
        },
        "reused_rank_and_invalid_set_oracles": {
            "dependent_equalities": stop_oracles["dependent_equalities"]["status"],
            "flat_mode": stop_oracles["unconstrained_flat_mode"]["status"],
            "invalid_active_index": stop_oracles["invalid_active_index"]["status"],
            "wrong_active_set_sign": stop_oracles["wrong_active_set_dual_sign"]["status"],
        },
        "nonsymmetric_high_k_oracle": nonsymmetric_high_k_oracle(),
        "versions": {"numpy": np.__version__, "scipy": scipy.__version__},
        "scope_limits": [
            "The fixture establishes a numerical method for a specified linear branch only; it does not infer a frame mask or select a contact state.",
            "The deliberately perturbed H demonstrates raw-versus-symmetric force amplification but does not bound A12's operator error or explain every frame force-interval miss.",
            "No A12 frame arrays/operators, frame matrix, frame response, native solver, or physical acceptance are included.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.verify:
        if not PINS_PATH.exists():
            raise SystemExit("verification failed: source-pins.json is missing")
        pins = json.loads(PINS_PATH.read_text(encoding="utf-8"))
        if pins.get("producer_sha256") != sha(Path(__file__)):
            raise SystemExit("verification failed: producer hash differs from source-pins.json")
        if pins.get("input_sha256") != INPUT_PINS:
            raise SystemExit("verification failed: input pins differ from source-pins.json")
    assessment = produce()
    observed = (json.dumps(assessment, indent=2, sort_keys=True) + "\n").encode()
    if args.write:
        OUTPUT.write_bytes(observed)
        print(f"wrote {OUTPUT}")
        return
    if not OUTPUT.exists() or OUTPUT.read_bytes() != observed:
        raise SystemExit("verification failed: assessment.json differs from replay")
    pins = json.loads(PINS_PATH.read_text(encoding="utf-8"))
    if pins.get("assessment_sha256") != sha(OUTPUT):
        raise SystemExit("verification failed: assessment hash differs from source-pins.json")
    print("PASS tiny raw-H fixed-active linear fixture replay")


if __name__ == "__main__":
    main()
