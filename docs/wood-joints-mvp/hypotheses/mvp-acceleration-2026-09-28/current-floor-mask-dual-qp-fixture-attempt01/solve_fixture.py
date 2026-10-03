"""Tiny prescribed-mask convex dual fixtures; no frame operator or FEA."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import osqp
import scipy
from scipy import sparse


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "fixed-mask-dual-qp.json"
BASE = "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
KNOWN = BASE + "current-coupled-indicator-selector-fixture-attempt01/known-answer.json"
SELECTOR = BASE + "current-coupled-indicator-selector-fixture-attempt01/select_states.py"

PINNED_INPUTS = {
    KNOWN: "8b42e4282952d8174f93b5f6138de14d0c88cbb1602d3968665aba5558045e88",
    SELECTOR: "9f33d5a49baf2a825a5de58a5b14dd96dd96820538e6f5f2a1c8ffdda90d7d3a",
    BASE + "current-coupled-contact-event-reference-fixture-attempt01/fixture.json":
        "0e5e5f6953a34be3b2078159cd51eb0f5398cb15ff2f22efd9b1d6e7df75b19e",
    BASE + "current-coupled-contact-event-reference-fixture-attempt01/verify.py":
        "858e1326fd057c76d24808fb801996161d70b3484f213a640247d3ac746d4d79",
    BASE + "conditional-floor-structural-coupling-fixture-attempt01/fixture.json":
        "65f1956c02b16e48ae6fa1fc7f112eb3a7564643dbd4dc74365aea4be4479a24",
    BASE + "conditional-floor-structural-coupling-fixture-attempt01/verify_fixture.py":
        "a24fc9f46a072c2b324939728ac26d7084684b99403b91a4965dda1813536ac0",
    BASE + "conditional-floor-structural-coupling-fixture-attempt01/parent-reference-counterexample.json":
        "20e1ced882ff50d34b557d0c5a4dfcb4f884b173697a112f51c907181d0bd57c",
    BASE + "conditional-floor-structural-coupling-fixture-attempt01/parent-reference-counterexample.md":
        "2af7037f256955c0929d6e228813174b33e0f86d275cc177f6bb63ca7003e115",
    BASE + "conditional-floor-structural-coupling-fixture-attempt01/parent_reference_counterexample.py":
        "7f150f308863f8b36c495b1a04595c7377eb30b3a4ae6810ade1ec90eb7e3015",
}

EQ_TOL = 2e-7
LAW_TOL = 2e-8
MASK_TOL = 2e-8
SETTINGS = {
    "verbose": False,
    "eps_abs": 1e-10,
    "eps_rel": 1e-10,
    "eps_prim_inf": 1e-10,
    "eps_dual_inf": 1e-10,
    "max_iter": 200000,
    "time_limit": 20.0,
    "polishing": True,
    "adaptive_rho": False,
    "rho": 0.1,
    "sigma": 1e-6,
    "scaling": 0,
    "check_termination": 1,
    "warm_starting": False,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(x: float) -> float:
    if abs(float(x)) < 5e-13:
        return 0.0
    return round(float(x), 12)


def check_pins() -> dict[str, str]:
    actual = {rel: digest(ROOT / rel) for rel in PINNED_INPUTS}
    assert actual == PINNED_INPUTS, "pinned known-answer or source fixture changed"
    known = json.loads((ROOT / KNOWN).read_text())
    assert known["status"] == "ALL_TINY_FIXTURES_REPLAYED"
    for rel, pin in known["source_pins"].items():
        assert PINNED_INPUTS.get(rel) == pin, f"unbound upstream selector source: {rel}"
    return actual


def qp_solve(
    *,
    D: np.ndarray,
    H: np.ndarray,
    k: np.ndarray,
    e: np.ndarray,
    linear: np.ndarray,
    W: np.ndarray,
    nonnegative: list[int],
) -> dict:
    """Solve min 1/2 f'(H+K^-1)f + (-e+r)'f s.t. D'f=W, f_U>=0."""
    nvar = len(k)
    assert D.shape == (nvar, len(W))
    assert H.shape == (nvar, nvar) and e.shape == linear.shape == (nvar,)
    inverse_k = np.zeros(nvar)
    finite_k = np.isfinite(k)
    inverse_k[finite_k] = 1.0 / k[finite_k]
    P = H + np.diag(inverse_k)
    assert np.max(np.abs(H - H.T)) <= 1e-12
    assert np.linalg.eigvalsh(P).min() >= -1e-12, "QP Hessian is not PSD"
    c = -e + linear

    equality = D.T
    bound_rows = np.zeros((len(nonnegative), nvar))
    for row, index in enumerate(nonnegative):
        bound_rows[row, index] = 1.0
    A = np.vstack([equality, bound_rows])
    lower = np.r_[W, np.zeros(len(nonnegative))]
    upper = np.r_[W, np.full(len(nonnegative), np.inf)]
    model = osqp.OSQP()
    model.setup(
        P=sparse.triu(sparse.csc_matrix(P), format="csc"),
        q=c,
        A=sparse.csc_matrix(A),
        l=lower,
        u=upper,
        **SETTINGS,
    )
    result = model.solve(raise_error=False)
    status = result.info.status.lower()
    info = {
        "status": status,
        "iterations": int(result.info.iter),
        "solver_primal_residual": clean(result.info.prim_res),
        "solver_dual_residual": clean(result.info.dual_res),
        "objective": clean(result.info.obj_val) if np.isfinite(result.info.obj_val) else None,
    }
    if status == "primal infeasible":
        return {"status": status, "info": info}
    assert status == "solved", f"OSQP result not accepted: {status}"
    f = np.asarray(result.x, dtype=float)
    dual_eq = np.asarray(result.y[: len(W)], dtype=float)
    dual_bounds = np.asarray(result.y[len(W) :], dtype=float)
    stationarity = P @ f + c + equality.T @ dual_eq + bound_rows.T @ dual_bounds
    output = {
        "status": status,
        "info": info,
        "f": f,
        "dual_eq": dual_eq,
        "dual_bounds": dual_bounds,
        "stationarity_inf": float(np.max(np.abs(stationarity), initial=0.0)),
        "equality_inf": float(np.max(np.abs(equality @ f - W), initial=0.0)),
        "min_force": float(np.min(f[nonnegative])) if nonnegative else None,
        "max_bound_complementarity": float(
            np.max(np.abs(f[nonnegative] * dual_bounds), initial=0.0)
        ) if nonnegative else 0.0,
        "bound_duals_max": float(np.max(dual_bounds, initial=-np.inf)) if nonnegative else 0.0,
        "dual_bounds": dual_bounds,
    }
    assert output["stationarity_inf"] <= LAW_TOL
    assert output["equality_inf"] <= EQ_TOL
    assert output["min_force"] is None or output["min_force"] >= -LAW_TOL
    assert output["bound_duals_max"] <= LAW_TOL
    assert output["max_bound_complementarity"] <= LAW_TOL
    return output


def exact_sign_fixture() -> dict:
    # Two parallel carriers in a 1-DOF known-answer problem. H is nonzero and
    # e nonzero, so both signs in q=D*a+e-H*f are exercised directly.
    D = np.array([[1.0], [1.0]])
    H = np.diag([0.1, 0.1])
    k = np.array([1.0, 2.0])
    f_expected = np.array([0.5, 1.0])
    a_expected = np.array([0.3])
    e = np.array([0.25, 0.3])
    W = np.array([1.5])
    q_expected = D @ a_expected + e - H @ f_expected
    assert np.allclose(q_expected, f_expected / k, atol=1e-14)
    solved = qp_solve(
        D=D, H=H, k=k, e=e, linear=np.zeros(2), W=W, nonnegative=[1]
    )
    assert solved["status"] == "solved"
    a = -solved["dual_eq"]
    q = D @ a + e - H @ solved["f"]
    assert np.allclose(solved["f"], f_expected, atol=1e-8)
    assert np.allclose(a, a_expected, atol=1e-8)
    assert np.allclose(q, q_expected, atol=1e-8)
    assert solved["stationarity_inf"] <= LAW_TOL
    assert solved["min_force"] >= -LAW_TOL
    assert solved["bound_duals_max"] <= LAW_TOL
    assert solved["max_bound_complementarity"] <= LAW_TOL
    assert abs(q[1] - solved["f"][1] / k[1] - solved["dual_bounds"][0]) <= LAW_TOL
    return {
        "id": "one_dof_nonzero_H_and_e_sign_oracle",
        "D": D.tolist(),
        "H": H.tolist(),
        "spring_k": k.tolist(),
        "e": e.tolist(),
        "W": W.tolist(),
        "known_answer_a": a_expected.tolist(),
        "known_answer_f": f_expected.tolist(),
        "known_answer_q": q_expected.tolist(),
        "solved_a": [clean(v) for v in a],
        "solved_f": [clean(v) for v in solved["f"]],
        "solved_q": [clean(v) for v in q],
        "normal_contact_q_and_f_are_positive": bool(q[1] > 0 and solved["f"][1] > 0),
        "kkt": {key: clean(solved[key]) for key in (
            "stationarity_inf", "equality_inf", "max_bound_complementarity", "bound_duals_max"
        )},
    }


def solve_prescribed_mask(case: dict, mask: tuple[bool, ...]) -> dict:
    src = case["selector_input"]
    K = np.asarray(src["operator_n_per_mm"], dtype=float)
    W = np.asarray(src["external_wrench_n"], dtype=float)
    contact_sign = np.asarray(src["contact_basis_diagonal"], dtype=float)
    ncontact = len(mask)
    ndof = len(W)
    assert ndof == 2 * ncontact and K.shape == (ndof, ndof)
    B = np.linalg.cholesky(K).T
    # Exact algebraic spring-bank factorization K=B'B, not an FE assembly.
    D_internal = B
    D_contact = -np.diag(contact_sign)
    all_D = np.vstack([D_internal, D_contact])
    all_H = np.zeros((len(all_D), len(all_D)))
    all_e = np.zeros(len(all_D))
    # Tangential held constraints have no finite tangent stiffness. Their
    # force variables get only the prescribed-reference linear term.
    qp_reference = [
        -contact_sign[2 * i] * src["tangent_reference_mm"][i]
        for i in range(ncontact)
    ]

    active_global_rows = list(range(ndof))
    active_types = ["internal_bilateral"] * ndof
    k_active = [1.0] * ndof
    e_active = [0.0] * ndof
    linear = [0.0] * ndof
    normal_variable_by_cell = {}
    tangent_variable_by_cell = {}
    for i, closed in enumerate(mask):
        if not closed:
            continue
        tangent_index = ndof + 2 * i
        normal_index = ndof + 2 * i + 1
        tangent_variable_by_cell[i] = len(active_global_rows)
        active_global_rows.append(tangent_index)
        active_types.append("held_tangent")
        k_active.append(np.inf)
        e_active.append(0.0)
        linear.append(qp_reference[i])
        normal_variable_by_cell[i] = len(active_global_rows)
        active_global_rows.append(normal_index)
        active_types.append("closed_floor_normal")
        k_active.append(float(src["normal_penalty_n_per_mm"]))
        e_active.append(0.0)
        linear.append(0.0)

    D_active = all_D[active_global_rows]
    H_active = all_H[np.ix_(active_global_rows, active_global_rows)]
    k_active = np.asarray(k_active, dtype=float)
    e_active = np.asarray(e_active, dtype=float)
    linear = np.asarray(linear, dtype=float)
    nonnegative = [normal_variable_by_cell[i] for i in range(ncontact) if mask[i]]
    solved = qp_solve(
        D=D_active, H=H_active, k=k_active, e=e_active, linear=linear,
        W=W, nonnegative=nonnegative,
    )
    if solved["status"] == "primal infeasible":
        return {
            "closed_mask": list(mask),
            "qp_status": solved["status"],
            "admissible": False,
            "rejection": "prescribed branch QP primal infeasible",
            "solver": solved["info"],
        }

    f_active = solved["f"]
    f_all = np.zeros(len(all_D))
    f_all[active_global_rows] = f_active
    a = -solved["dual_eq"]
    q_all = all_D @ a + all_e - all_H @ f_all
    source_u = a
    source_contact_f = np.zeros(ndof)
    source_contact_q = np.zeros(ndof)
    for i in range(ncontact):
        for comp in (0, 1):
            qrow = ndof + 2 * i + comp
            source_contact_f[2 * i + comp] = f_all[qrow]
            source_contact_q[2 * i + comp] = q_all[qrow]

    # The spring-bank equilibrium is the original source equation
    # K*u - diag(contact_sign)*f = W.
    source_residual = K @ source_u - contact_sign * source_contact_f - W
    reasons = []
    law_error = 0.0
    open_q = []
    for i, closed in enumerate(mask):
        trow, nrow = ndof + 2 * i, ndof + 2 * i + 1
        if closed:
            tangent_error = abs(q_all[trow] - qp_reference[i])
            normal = source_contact_f[2 * i + 1]
            qnormal = source_contact_q[2 * i + 1]
            normal_error = abs(qnormal - normal / src["normal_penalty_n_per_mm"])
            law_error = max(law_error, tangent_error, normal_error)
            if tangent_error > MASK_TOL:
                reasons.append(f"cell_{i}_held_tangent_reference_mismatch")
            if normal < -MASK_TOL:
                reasons.append(f"cell_{i}_negative_closed_normal_force")
            if qnormal < -MASK_TOL:
                reasons.append(f"cell_{i}_closed_normal_extension_negative")
            if normal_error > MASK_TOL:
                reasons.append(f"cell_{i}_closed_normal_spring_law_mismatch")
        else:
            qnormal = source_contact_q[2 * i + 1]
            open_q.append(qnormal)
            if abs(source_contact_f[2 * i]) > MASK_TOL or abs(source_contact_f[2 * i + 1]) > MASK_TOL:
                reasons.append(f"cell_{i}_open_contact_force_nonzero")
            if qnormal > MASK_TOL:
                reasons.append(f"cell_{i}_open_normal_extension_positive")

    internal_law = D_internal @ source_u - f_all[:ndof]
    if np.max(np.abs(internal_law), initial=0.0) > LAW_TOL:
        reasons.append("bilateral_spring_bank_law_mismatch")

    normal_dual_gap = 0.0
    for dual_index, cell in enumerate(i for i in range(ncontact) if mask[i]):
        qnormal = source_contact_q[2 * cell + 1]
        normal = source_contact_f[2 * cell + 1]
        normal_dual_gap = max(
            normal_dual_gap,
            abs(qnormal - normal / src["normal_penalty_n_per_mm"] - solved["dual_bounds"][dual_index]),
        )
    if normal_dual_gap > LAW_TOL:
        reasons.append("normal_lower_bound_dual_sign_relation")

    if solved["stationarity_inf"] > LAW_TOL:
        reasons.append("qp_stationarity_residual")
    if solved["equality_inf"] > EQ_TOL:
        reasons.append("raw_Dt_f_equals_W_residual")
    if np.max(np.abs(source_residual), initial=0.0) > EQ_TOL:
        reasons.append("source_structural_balance_residual")

    # Compare each candidate to the independent established selector answer.
    source_candidate = next(
        (candidate for candidate in case["candidate_masks"] if candidate["closed_mask"] == list(mask)),
        None,
    )
    if not reasons and source_candidate is not None:
        for actual, expected in zip(source_u, source_candidate["u_mm"], strict=True):
            if abs(actual - expected) > MASK_TOL:
                reasons.append("source_displacement_oracle_mismatch")
                break
        for actual, expected in zip(source_contact_f[0::2], source_candidate["tangent_forces_n"], strict=True):
            if abs(actual - expected) > MASK_TOL:
                reasons.append("source_tangent_force_oracle_mismatch")
                break
        for actual, expected in zip(source_contact_f[1::2], source_candidate["normal_forces_n"], strict=True):
            if abs(actual - expected) > MASK_TOL:
                reasons.append("source_normal_force_oracle_mismatch")
                break
    elif not reasons and source_candidate is None:
        reasons.append("mask_has_no_existing_selector_oracle_candidate")

    return {
        "closed_mask": list(mask),
        "qp_status": solved["status"],
        "admissible": not reasons,
        "rejection": None if not reasons else reasons,
        "source_displacement_u_mm": [clean(v) for v in source_u],
        "source_tangent_forces_N": [clean(v) for v in source_contact_f[0::2]],
        "source_normal_forces_N": [clean(v) for v in source_contact_f[1::2]],
        "source_qp_contact_coordinates_mm": [clean(v) for v in source_contact_q],
        "open_normal_q_mm": [clean(v) for v in open_q],
        "max_source_equilibrium_residual_N": clean(float(np.max(np.abs(source_residual), initial=0.0))),
        "max_kkt_stationarity_residual": clean(solved["stationarity_inf"]),
        "max_Dt_f_minus_W_residual": clean(solved["equality_inf"]),
        "max_closed_law_or_held_reference_error": clean(law_error),
        "max_lower_bound_complementarity": clean(solved["max_bound_complementarity"]),
        "max_lower_bound_dual": clean(solved["bound_duals_max"]),
        "max_normal_q_minus_f_over_k_minus_bound_dual": clean(normal_dual_gap),
        "max_internal_spring_law_error": clean(float(np.max(np.abs(internal_law), initial=0.0))),
        "solver": solved["info"],
    }


def solve_source_cases(known: dict) -> list[dict]:
    results = []
    for case in known["results"]:
        src = case["selector_input"]
        ncontact = len(src["tangent_reference_mm"])
        branches = [solve_prescribed_mask(case, mask) for mask in itertools.product((False, True), repeat=ncontact)]
        valid = [branch for branch in branches if branch["admissible"]]
        expected = [candidate["closed_mask"] for candidate in case["candidate_masks"]]
        assert [branch["closed_mask"] for branch in valid] == expected, case["id"]
        cls = case["classification"]
        assert len(valid) == case["oracle_mask_count"], case["id"]
        if not valid:
            actual_class = "NO_ADMISSIBLE_STATE"
        elif len(valid) == 1:
            actual_class = "ONE_ADMISSIBLE_MASK"
        else:
            coincident_zero_boundary = True
            for left, right in itertools.combinations(valid, 2):
                differing = [
                    i for i, (a, b) in enumerate(zip(left["closed_mask"], right["closed_mask"], strict=True))
                    if a != b
                ]
                same_state = (
                    np.allclose(left["source_displacement_u_mm"], right["source_displacement_u_mm"], atol=MASK_TOL)
                    and np.allclose(left["source_tangent_forces_N"], right["source_tangent_forces_N"], atol=MASK_TOL)
                    and np.allclose(left["source_normal_forces_N"], right["source_normal_forces_N"], atol=MASK_TOL)
                )
                boundary = all(
                    abs(left["source_tangent_forces_N"][i]) <= MASK_TOL
                    and abs(left["source_normal_forces_N"][i]) <= MASK_TOL
                    and abs(left["source_qp_contact_coordinates_mm"][2 * i + 1]) <= MASK_TOL
                    for i in differing
                )
                if not (same_state and boundary):
                    coincident_zero_boundary = False
                    break
            actual_class = (
                "AMBIGUOUS_ZERO_BOUNDARY_MASKS"
                if coincident_zero_boundary
                else "MULTIPLE_ADMISSIBLE_MASKS"
            )
        assert actual_class == cls, (case["id"], actual_class, cls)
        results.append({
            "id": case["id"],
            "expected_selector_classification": cls,
            "replayed_classification": actual_class,
            "source_oracle": case["source_oracle"],
            "source_external_wrench_N": case["selector_input"]["external_wrench_n"],
            "source_contact_basis_diagonal": case["selector_input"]["contact_basis_diagonal"],
            "source_tangent_reference_mm": case["selector_input"]["tangent_reference_mm"],
            "source_normal_penalty_N_per_mm": case["selector_input"]["normal_penalty_n_per_mm"],
            "prescribed_masks_exhausted": len(branches) == 2 ** ncontact,
            "valid_mask_count": len(valid),
            "branches": branches,
        })
    return results


def produce() -> dict:
    pins = check_pins()
    known = json.loads((ROOT / KNOWN).read_text())
    exact = exact_sign_fixture()
    results = solve_source_cases(known)
    pins[str(Path(__file__).relative_to(ROOT))] = digest(Path(__file__))
    return {
        "schema": "prescribed_floor_mask_dual_qp_fixture/v1",
        "status": "PASS_TINY_SOURCE_BRANCHES_AND_KKT_FIXTURES",
        "source_sha256": pins,
        "solver": {
            "name": "OSQP",
            "version": osqp.__version__,
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "settings": SETTINGS,
            "accepted_status": "solved only; solved inaccurate is not accepted",
        },
        "formulation": {
            "q_definition": "q = D*a + e - H*f",
            "balance": "D.T*f = W",
            "objective": "0.5*f.T*H*f + sum(f_i^2/(2*k_i)) - e.T*f + held_reference.T*f_t",
            "kkt_free_carrier": "q = f/k + held_reference (bilateral springs have zero reference)",
            "kkt_unilateral_carrier": "f >= 0; q - f/k = lower_bound_dual <= 0 at f=0, and q=f/k when f>0",
            "open_floor": "omit its normal/tangent forces (exactly zero), then independently require q_N<=0",
            "held_floor": "tangent force is signed/free with reference linear term; normal force is nonnegative with its spring compliance",
            "mask_scope": "floor tangent/normal episode status is prescribed; all included unilateral spring forces are represented by lower bounds, with no indicator/binary variable",
        },
        "nonzero_H_e_sign_fixture": exact,
        "source_branch_cases": results,
        "limits": [
            "Only pinned one- and two-contact mathematical fixtures; no source frame operator, body factorization, floor mask selection, frame solve, native solve, panel, or design check.",
            "Source SPD structural matrices are factored exactly as tiny bilateral spring banks solely to compare the dual result with existing source branch oracles; this is not a member/FE model.",
            "References are supplied from existing exact event and stage fixtures; this code does not locate events, capture/update references, establish history, or prove a prescribed mask occurs in a physical path.",
            "QP feasibility and KKT agreement on tiny fixtures do not establish numerical conditioning, runtime, uniqueness, or scalability for 1,192 nonfloor unilateral carriers.",
        ],
        "native_solve_run": False,
        "frame_solve_run": False,
        "full_frame_mask_selected": False,
        "joint_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(produce(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.verify:
        assert OUTPUT.read_text() == rendered, "saved QP fixture differs from pinned replay"
        print("PASS_TINY_SOURCE_BRANCHES_AND_KKT_FIXTURES: 9 cases, all prescribed masks")
    else:
        OUTPUT.write_text(rendered)
        print("Wrote prescribed-mask tiny QP fixture")


if __name__ == "__main__":
    main()
