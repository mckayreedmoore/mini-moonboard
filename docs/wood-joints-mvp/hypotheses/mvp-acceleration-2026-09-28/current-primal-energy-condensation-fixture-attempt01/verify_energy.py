"""Tiny primal-energy condensation fixtures; no frame operator or FEA."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import osqp
import scipy
from scipy import sparse


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "primal-energy-fixture.json"
BASE = "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
KNOWN = BASE + "current-coupled-indicator-selector-fixture-attempt01/known-answer.json"
SELECTOR = BASE + "current-coupled-indicator-selector-fixture-attempt01/select_states.py"
EVENT = BASE + "current-coupled-contact-event-reference-fixture-attempt01/fixture.json"
EVENT_CHECK = BASE + "current-coupled-contact-event-reference-fixture-attempt01/verify.py"
STRUCT = BASE + "conditional-floor-structural-coupling-fixture-attempt01/fixture.json"
STRUCT_CHECK = BASE + "conditional-floor-structural-coupling-fixture-attempt01/verify_fixture.py"
COUNTER = BASE + "conditional-floor-structural-coupling-fixture-attempt01/parent-reference-counterexample.json"
COUNTER_CHECK = BASE + "conditional-floor-structural-coupling-fixture-attempt01/parent_reference_counterexample.py"

PINNED_INPUTS = {
    KNOWN: "8b42e4282952d8174f93b5f6138de14d0c88cbb1602d3968665aba5558045e88",
    SELECTOR: "9f33d5a49baf2a825a5de58a5b14dd96dd96820538e6f5f2a1c8ffdda90d7d3a",
    EVENT: "0e5e5f6953a34be3b2078159cd51eb0f5398cb15ff2f22efd9b1d6e7df75b19e",
    EVENT_CHECK: "858e1326fd057c76d24808fb801996161d70b3484f213a640247d3ac746d4d79",
    STRUCT: "65f1956c02b16e48ae6fa1fc7f112eb3a7564643dbd4dc74365aea4be4479a24",
    STRUCT_CHECK: "a24fc9f46a072c2b324939728ac26d7084684b99403b91a4965dda1813536ac0",
    COUNTER: "20e1ced882ff50d34b557d0c5a4dfcb4f884b173697a112f51c907181d0bd57c",
    COUNTER_CHECK: "7f150f308863f8b36c495b1a04595c7377eb30b3a4ae6810ade1ec90eb7e3015",
}

TOL = 2e-8
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value: float) -> float:
    if abs(float(value)) < 5e-13:
        return 0.0
    return round(float(value), 12)


def pins() -> dict[str, str]:
    actual = {rel: sha256(ROOT / rel) for rel in PINNED_INPUTS}
    assert actual == PINNED_INPUTS, "pinned toy source or known-answer input changed"
    known = json.loads((ROOT / KNOWN).read_text())
    assert known["status"] == "ALL_TINY_FIXTURES_REPLAYED"
    return actual


def solve_qp(P: np.ndarray, linear: np.ndarray, A: np.ndarray,
             lower: np.ndarray, upper: np.ndarray) -> dict:
    P = 0.5 * (P + P.T)
    assert np.linalg.eigvalsh(P).min() >= -1e-12, "QP Hessian is not PSD"
    model = osqp.OSQP()
    model.setup(
        P=sparse.triu(sparse.csc_matrix(P), format="csc"),
        q=linear,
        A=sparse.csc_matrix(A),
        l=lower,
        u=upper,
        **SETTINGS,
    )
    result = model.solve(raise_error=False)
    status = result.info.status.lower()
    assert status == "solved", f"OSQP result not accepted: {status}"
    x = np.asarray(result.x, dtype=float)
    y = np.asarray(result.y, dtype=float)
    stationarity = P @ x + linear + A.T @ y
    assert np.max(np.abs(stationarity), initial=0.0) <= TOL
    return {
        "x": x,
        "y": y,
        "status": status,
        "iterations": int(result.info.iter),
        "solver_primal_residual": clean(result.info.prim_res),
        "solver_dual_residual": clean(result.info.dual_res),
        "stationarity_inf": clean(float(np.max(np.abs(stationarity), initial=0.0))),
        "objective": clean(float(result.info.obj_val)),
    }


def general_kkt_oracle() -> dict:
    # D=[1,1]^T, H=.1I, and known answer a=.3, g=(.5,1), q=(.5,.5).
    # The first carrier is bilateral with k=1; the second is unilateral with k=2.
    H = 0.1 * np.eye(2)
    D = np.ones((2, 1))
    e = np.array([0.25, 0.30])
    W = np.array([1.5])
    k_bilateral = 1.0
    k_unilateral = 2.0

    # Variables x=(a,g_b,g_u,s_u), q_b=a+e_b-.1g_b, q_u=a+e_u-.1g_u.
    v_b = np.array([1.0, -0.1, 0.0, 0.0])
    P = np.zeros((4, 4))
    P[1, 1] += H[0, 0]
    P[2, 2] += H[1, 1]
    P += k_bilateral * np.outer(v_b, v_b)
    P[3, 3] += k_unilateral
    linear = k_bilateral * e[0] * v_b - np.array([W[0], 0.0, 0.0, 0.0])

    # s_u >= q_u and s_u >= 0, with the lower-bound duals returned by OSQP.
    A = np.array([
        [-1.0, 0.0, 0.1, 1.0],
        [0.0, 0.0, 0.0, 1.0],
    ])
    lower = np.array([e[1], 0.0])
    upper = np.full(2, np.inf)
    solved = solve_qp(P, linear, A, lower, upper)
    a, g_b, g_u, s_u = solved["x"]
    g = np.array([g_b, g_u])
    q = D @ np.array([a]) + e - H @ g
    duals = solved["y"]
    alpha, beta = -duals
    checks = {
        "compatibility_inf": float(np.max(np.abs(q - (D @ np.array([a]) + e - H @ g)))),
        "equilibrium_inf": float(np.max(np.abs(D.T @ g - W))),
        "bilateral_law_abs": abs(g_b - k_bilateral * q[0]),
        "unilateral_law_abs": abs(g_u - k_unilateral * s_u),
        "hinge_abs": abs(s_u - max(q[1], 0.0)),
        "epigraph_stationarity_abs": abs(k_unilateral * s_u - alpha - beta),
        "epigraph_dual_min": min(alpha, beta),
    }
    assert abs(a - 0.3) <= TOL
    assert np.max(np.abs(g - np.array([0.5, 1.0]))) <= TOL
    assert np.max(np.abs(q - np.array([0.5, 0.5]))) <= TOL
    assert max(checks[key] for key in checks if key != "epigraph_dual_min") <= TOL
    assert checks["epigraph_dual_min"] >= -TOL
    assert alpha > 0.0 and abs(beta) <= TOL
    return {
        "id": "two_carrier_bilateral_plus_unilateral_known_answer",
        "H": H.tolist(),
        "D": D.tolist(),
        "e": e.tolist(),
        "W": W.tolist(),
        "k_bilateral": k_bilateral,
        "k_unilateral": k_unilateral,
        "expected": {"a": 0.3, "g": [0.5, 1.0], "q": [0.5, 0.5], "s_unilateral": 0.5},
        "solved": {
            "a": clean(a),
            "g": [clean(v) for v in g],
            "q": [clean(v) for v in q],
            "s_unilateral": clean(s_u),
            "epigraph_duals_alpha_beta": [clean(alpha), clean(beta)],
        },
        "checks": {key: clean(value) for key, value in checks.items()},
        "solver": {key: solved[key] for key in (
            "status", "iterations", "solver_primal_residual", "solver_dual_residual",
            "stationarity_inf", "objective"
        )},
    }


def condensed_branch(case: dict, closed: bool) -> dict:
    src = case["selector_input"]
    K = np.asarray(src["operator_n_per_mm"], dtype=float)
    C = np.diag(np.asarray(src["contact_basis_diagonal"], dtype=float))
    W = np.asarray(src["external_wrench_n"], dtype=float)
    k_n = float(src["normal_penalty_n_per_mm"])
    r_t = float(src["tangent_reference_mm"][0])
    assert K.shape == C.shape == (2, 2)
    assert np.linalg.eigvalsh(K).min() > 0.0

    # This is a tiny known-answer condensation only. No actual frame matrix is used.
    H = C @ np.linalg.solve(K, C)
    e = -C @ np.linalg.solve(K, W)
    assert np.max(np.abs(H - H.T)) <= 1e-12
    assert np.linalg.eigvalsh(H).min() > 0.0

    # x=(g_t,g_n,q_t,q_n); q=e-Hg. Open masks fix g=0, then signs are checked.
    if not closed:
        P = np.zeros((4, 4))
        P[:2, :2] = H
        A = np.zeros((4, 4))
        A[:2, :2] = H
        A[:2, 2:] = np.eye(2)
        A[2, 0] = 1.0
        A[3, 1] = 1.0
        lower = np.r_[e, 0.0, 0.0]
        upper = lower.copy()
        solved = solve_qp(P, np.zeros(4), A, lower, upper)
        normal_mu = 0.0
    else:
        P = np.zeros((4, 4))
        P[:2, :2] = H
        P[3, 3] = k_n
        A = np.zeros((4, 4))
        A[:2, :2] = H
        A[:2, 2:] = np.eye(2)
        A[2, 2] = 1.0
        A[3, 3] = 1.0
        lower = np.r_[e, r_t, 0.0]
        upper = np.r_[e, r_t, np.inf]
        solved = solve_qp(P, np.zeros(4), A, lower, upper)
        normal_mu = max(0.0, -float(solved["y"][3]))

    g = solved["x"][:2]
    q = solved["x"][2:]
    u = -C @ q
    source_residual = K @ u - C @ g - W
    compatibility = q + H @ g - e
    if closed:
        normal_law = float(g[1] - k_n * q[1])
        branch_multiplier_law = float(g[1] - k_n * q[1] + normal_mu)
        tangent_error = abs(q[0] - r_t)
        physically_admissible = (
            q[1] >= -TOL and g[1] >= -TOL and
            abs(normal_law) <= TOL and normal_mu <= TOL and tangent_error <= TOL
        )
    else:
        normal_law = float(g[1])
        branch_multiplier_law = 0.0
        tangent_error = 0.0
        physically_admissible = (
            np.max(np.abs(g)) <= TOL and q[1] <= TOL and
            abs(g[1]) <= TOL
        )

    assert np.max(np.abs(compatibility)) <= TOL
    assert np.max(np.abs(source_residual)) <= TOL
    if closed:
        assert abs(branch_multiplier_law) <= TOL
        assert normal_mu >= 0.0

    return {
        "closed_mask": [bool(closed)],
        "status": solved["status"],
        "iterations": solved["iterations"],
        "source_e_N": [clean(v) for v in e],
        "condensed_H_mm_per_N": [[clean(v) for v in row] for row in H],
        "g_N": [clean(v) for v in g],
        "q_mm": [clean(v) for v in q],
        "source_u_mm": [clean(v) for v in u],
        "source_Ku_minus_Cg_minus_W_inf_N": clean(float(np.max(np.abs(source_residual)))),
        "compatibility_q_plus_Hg_minus_e_inf_mm": clean(float(np.max(np.abs(compatibility)))),
        "normal_branch_multiplier_N": clean(normal_mu),
        "normal_spring_law_residual_N": clean(normal_law),
        "normal_law_including_branch_multiplier_residual_N": clean(branch_multiplier_law),
        "held_tangent_reference_error_mm": clean(float(tangent_error)),
        "normal_sign_pass": bool(q[1] >= -TOL if closed else q[1] <= TOL),
        "force_and_law_pass": bool(
            (g[1] >= -TOL and abs(normal_law) <= TOL and normal_mu <= TOL)
            if closed else np.max(np.abs(g)) <= TOL
        ),
        "admissible": bool(physically_admissible),
        "solver_stationarity_inf": solved["stationarity_inf"],
    }


def branch_examples(known: dict) -> list[dict]:
    by_id = {case["id"]: case for case in known["results"]}
    selected = [
        "one_cell_zero_force_event_boundary",
        "one_cell_fixed_reference_no_admissible_state",
        "one_cell_fixed_reference_two_admissible_masks",
    ]
    output = []
    for case_id in selected:
        case = by_id[case_id]
        branches = [condensed_branch(case, closed) for closed in (False, True)]
        valid_masks = [branch["closed_mask"] for branch in branches if branch["admissible"]]
        expected_masks = case["selector_input"]["analytic_expected_masks_closed_true"]
        assert valid_masks == expected_masks, (case_id, valid_masks, expected_masks)

        # Independently compare admissible force/displacement states to the source oracle.
        for branch in branches:
            if not branch["admissible"]:
                continue
            oracle = next(
                candidate for candidate in case["candidate_masks"]
                if candidate["closed_mask"] == branch["closed_mask"]
            )
            assert np.allclose(branch["source_u_mm"], oracle["u_mm"], atol=TOL)
            assert np.allclose(branch["g_N"][0::2], oracle["tangent_forces_n"], atol=TOL)
            assert np.allclose(branch["g_N"][1::2], oracle["normal_forces_n"], atol=TOL)

        if case_id == "one_cell_zero_force_event_boundary":
            assert valid_masks == [[False], [True]]
            assert np.allclose(branches[0]["q_mm"], branches[1]["q_mm"], atol=TOL)
            assert np.allclose(branches[0]["g_N"], branches[1]["g_N"], atol=TOL)
        elif case_id.endswith("no_admissible_state"):
            assert valid_masks == []
            closed = branches[1]
            assert abs(closed["q_mm"][1]) <= TOL
            assert closed["normal_branch_multiplier_N"] > 0.49
            assert closed["g_N"][1] < -0.49
        else:
            assert valid_masks == [[False], [True]]

        output.append({
            "id": case_id,
            "source_classification": case["classification"],
            "replayed_valid_masks": valid_masks,
            "branches": branches,
        })
    return output


def produce() -> dict:
    source_pins = pins()
    known = json.loads((ROOT / KNOWN).read_text())
    general = general_kkt_oracle()
    branches = branch_examples(known)
    source_pins[str(Path(__file__).relative_to(ROOT))] = sha256(Path(__file__))
    return {
        "schema": "primal_energy_condensation_known_answer_fixture/v1",
        "status": "PASS_PRIMAL_KKT_AND_CONDENSED_FLOOR_MASK_TOYS",
        "source_sha256": source_pins,
        "solver": {
            "name": "OSQP",
            "version": osqp.__version__,
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "settings": SETTINGS,
            "accepted_status": "solved only; solved inaccurate is not accepted",
        },
        "formulation": {
            "compatibility": "q = D*a + e - H*g",
            "generalized_force_equilibrium": "D.T*g = W",
            "objective": "0.5*g.T*H*g - W.T*a + bilateral sum(0.5*k*q^2) + unilateral sum(0.5*k*s^2)",
            "unilateral_epigraph": "s >= q; s >= 0; minimize 0.5*k*s^2",
            "held_tangent": "q_t = r; equality multiplier supplies signed tangent force",
            "open_floor_normal": "q_n <= 0 and source normal force must be zero",
            "closed_floor_normal": "q_n >= 0, source spring force k*q_n; explicit normal-bound multiplier must be zero",
        },
        "general_kkt_oracle": general,
        "condensed_source_mask_examples": branches,
        "limits": [
            "All QPs are two-coordinate or one-DOF mathematical fixtures; no actual frame operator, H extraction, factorization, inversion, MIQP, native solve, or path solver is included.",
            "The condensed source toys use exact symmetric positive-definite H formed only from the pinned 2x2 source carriers.",
            "A true zero-gap event can remain ambiguous when both masks yield the same zero-force state; the fixture retains both rather than inventing a tie-break.",
            "Explicit normal branch bounds can introduce extra reaction multipliers at q_n=0. Those multipliers must be zero to recover the source spring/open laws; an energy minimizer alone is not branch acceptance.",
            "The actual frame H is only numerically reciprocal. A later use of H_sym=(H+H.T)/2 is a declared model approximation and must separately audit original raw-H compatibility, source force balance, and branch laws.",
            "The fixture supports an algebraic route for ordinary unilateral springs without binaries under symmetric SPD H; it does not establish a 1,192-contact formulation's conditioning, runtime, scalability, or physical floor history.",
        ],
        "actual_frame_solved": False,
        "frame_matrix_inverted": False,
        "floor_masks_selected": False,
        "native_solve_run": False,
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
        assert OUTPUT.read_text() == rendered, "saved primal-energy output differs from pinned replay"
        print("PASS_PRIMAL_KKT_AND_CONDENSED_FLOOR_MASK_TOYS: 3 cases, 6 prescribed branches")
    else:
        OUTPUT.write_text(rendered)
        print("Wrote primal-energy condensation fixture")


if __name__ == "__main__":
    main()
