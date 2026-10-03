"""Known-answer replay for the tiny SCIP floor-binary energy adapter."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import pyscipopt
import osqp
import scipy


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
OUTPUT = HERE / "assessment.json"
SOURCE_SELECTOR = BASE / "current-coupled-indicator-selector-fixture-attempt01/select_states.py"
SOURCE_ENERGY = BASE / "current-primal-energy-condensation-fixture-attempt01/primal-energy-fixture.json"
SOURCE_ENERGY_CHECK = BASE / "current-primal-energy-condensation-fixture-attempt01/verify_energy.py"
SOURCE_ENERGY_README = BASE / "current-primal-energy-condensation-fixture-attempt01/README.md"

TOL = 2e-7
PER_SOLVE_S = 3.0
SUITE_BUDGET_S = 90.0


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clean(value: float) -> float:
    value = float(value)
    if abs(value) < 5e-12:
        return 0.0
    return round(value, 12)


def condensed_source_case(source_case: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    K = np.asarray(source_case["operator_n_per_mm"], dtype=float)
    C = np.diag(np.asarray(source_case["contact_basis_diagonal"], dtype=float))
    F = np.asarray(source_case["external_wrench_n"], dtype=float)
    H = C @ np.linalg.solve(K, C)
    e = -C @ np.linalg.solve(K, F)
    # Original tiny source equilibrium is K*u - C*g = F; its condensed
    # q-coordinate is q = -C*u = e - H*g.
    assert np.linalg.norm(H - H.T, ord=np.inf) <= 1e-12
    return H, e, C


def source_floor_model(source_case: dict, source_fixture, adapter,
                       time_limit_s: float) -> dict:
    H, e, C = condensed_source_case(source_case)
    L, factor_check = adapter.factor_spd(H)
    n = len(e)
    D = np.zeros((n, 0), dtype=float)
    W = np.zeros(0, dtype=float)
    contact_count = len(source_case["tangent_reference_mm"])
    penalty = float(source_case["normal_penalty_n_per_mm"])
    laws = []
    floor_cells = []
    basis = source_case["contact_basis_diagonal"]
    for i in range(contact_count):
        tangent_row, normal_row = 2*i, 2*i+1
        laws.extend([{"kind": "tangent"},
                     {"kind": "unilateral", "k": penalty}])
        # The source fixture reference is expressed in physical u coordinates;
        # q=-C*u, so pass its exact signed q-coordinate value.
        ref_q = -float(basis[tangent_row]) * float(
            source_case["tangent_reference_mm"][i])
        floor_cells.append({"normal_row": normal_row,
                            "tangent_rows_and_references": [(tangent_row, ref_q)]})

    result = adapter.enumerate_floor_masks(
        H, L, D, e, W, laws, floor_cells,
        time_limit_s=time_limit_s, tolerance=TOL)
    assert result["complete"], (source_case["id"], result["stop_reason"])
    assert len(result["candidate_masks"]) == 2 ** contact_count, (
        source_case["id"], result["candidate_masks"])
    polished = []
    for candidate in result["candidate_masks"]:
        exact = adapter.polish_fixed_mask_osqp(
            H, L, D, e, W, laws, floor_cells, candidate["mask"], tolerance=TOL)
        u = -C @ exact["q"]
        state = {
            "closed_mask": exact["mask"],
            "u_mm": [clean(v) for v in u],
            "tangent_forces_n": [clean(v) for v in exact["g"][0::2]],
            "normal_forces_n": [clean(v) for v in exact["g"][1::2]],
        }
        # Check the original (uncondensed) source operator and loads after
        # polishing, not just the condensed energy-coordinate KKT equations.
        K = np.asarray(source_case["operator_n_per_mm"], dtype=float)
        F = np.asarray(source_case["external_wrench_n"], dtype=float)
        source_force = np.asarray(source_case["contact_basis_diagonal"], dtype=float) * exact["g"]
        original_balance = K @ u - source_force - F
        balance_error = float(np.max(np.abs(original_balance), initial=0.0))
        state.update({"max_equilibrium_residual_n": clean(balance_error),
                      "max_source_force_law_error_n": clean(exact["max_source_force_law_error_N"]),
                      "max_floor_normal_bound_reaction_error_n": clean(
                          exact["max_floor_normal_bound_reaction_error_N"]),
                      "osqp_polish": exact["solver"]})
        exact["source_balance_max_abs_N"] = balance_error
        exact["source_state_pass"] = bool(exact["source_state_pass"]
                                          and balance_error <= TOL)
        exact["known_answer_state"] = state
        polished.append(exact)
    states = [candidate["known_answer_state"] for candidate in polished
              if candidate["source_state_pass"]]
    rejected = [candidate for candidate in polished
                if not candidate["source_state_pass"]]
    classification = classify_states(source_case, states, source_fixture,
                                     complete=result["complete"])
    result["classification"] = classification
    result["accepted_masks"] = [state["closed_mask"] for state in states]
    result["rejected_minimizers"] = [{
        "mask": candidate["mask"],
        "max_source_force_law_error_N": candidate["max_source_force_law_error_N"],
        "max_floor_normal_bound_reaction_error_N":
            candidate["max_floor_normal_bound_reaction_error_N"],
        "raw_equilibrium_inf_N": candidate["raw_equilibrium_inf_N"],
        "source_balance_max_abs_N": candidate["source_balance_max_abs_N"],
    } for candidate in rejected]
    for state in states:
        source_fixture.validate_solution(source_case, state)
        source_fixture.expected_matches(source_case, state)
    expected_class = {
        "one_cell_zero_force_event_boundary": "AMBIGUOUS_ZERO_BOUNDARY_MASKS",
        "one_cell_nonzero_episode_reference_held": "ONE_ADMISSIBLE_MASK",
        "one_cell_fixed_reference_no_admissible_state": "NO_ADMISSIBLE_STATE",
        "one_cell_fixed_reference_two_admissible_masks": "MULTIPLE_ADMISSIBLE_MASKS",
        "two_cell_both_bearing": "ONE_ADMISSIBLE_MASK",
        "two_cell_left_only_right_released": "ONE_ADMISSIBLE_MASK",
        "two_cell_both_open": "ONE_ADMISSIBLE_MASK",
        "two_cell_both_reengaged_after_recorded_open_stage": "ONE_ADMISSIBLE_MASK",
    }[source_case["id"]]
    assert classification == expected_class, (source_case["id"], classification, expected_class)
    masks = [state["closed_mask"] for state in states]
    assert sorted(masks) == sorted(source_case["expected_masks_closed_true"]), (
        source_case["id"], masks, source_case["expected_masks_closed_true"])
    if source_case["id"] == "one_cell_fixed_reference_no_admissible_state":
        assert len(result["rejected_minimizers"]) == 2
        assert max(row["max_floor_normal_bound_reaction_error_N"]
                   for row in result["rejected_minimizers"]) > 0.49
    if source_case["id"] == "one_cell_zero_force_event_boundary":
        assert source_fixture.zero_boundary_ambiguity(source_case, states)
    if source_case["id"] == "one_cell_fixed_reference_two_admissible_masks":
        assert not source_fixture.zero_boundary_ambiguity(source_case, states)

    return {
        "id": source_case["id"],
        "expected_classification": expected_class,
        "observed_classification": result["classification"],
        "all_floor_masks_proven_exhausted": result["complete"],
        "stop_reason": result["stop_reason"],
        "solver_status_sequence": result["solver_status_sequence"],
        "accepted_masks": masks,
        "rejected_minimizers": result["rejected_minimizers"],
        "scip_provisional_max_force_law_error_N": clean(max((
            candidate["max_source_force_law_error_N"]
            for candidate in result["candidate_masks"]), default=0.0)),
        "source_balance_max_abs_N": clean(max((
            candidate["source_balance_max_abs_N"] for candidate in polished), default=0.0)),
        "factor_check": {k: clean(v) for k, v in factor_check.items()},
        "max_compatibility_raw_H_inf_mm": clean(max((
            candidate["compatibility_raw_H_inf_mm"] for candidate in polished), default=0.0)),
        "max_all_masks_source_force_law_error_N": clean(max((
            candidate["max_source_force_law_error_N"] for candidate in polished), default=0.0)),
        "max_accepted_source_force_law_error_N": clean(max((
            candidate["max_source_force_law_error_N"] for candidate in polished
            if candidate["source_state_pass"]), default=0.0)),
        "max_all_masks_floor_normal_bound_reaction_error_N": clean(max((
            candidate["max_floor_normal_bound_reaction_error_N"]
            for candidate in polished), default=0.0)),
        "max_accepted_floor_normal_bound_reaction_error_N": clean(max((
            candidate["max_floor_normal_bound_reaction_error_N"]
            for candidate in polished if candidate["source_state_pass"]), default=0.0)),
        "all_mask_polish_results": [{
            "mask": candidate["mask"],
            "accepted_by_source_laws": candidate["source_state_pass"],
            "objective": clean(candidate["objective"]),
            "raw_equilibrium_inf_N": clean(candidate["raw_equilibrium_inf_N"]),
            "source_force_law_error_N": clean(candidate["max_source_force_law_error_N"]),
            "normal_bound_reaction_error_N": clean(
                candidate["max_floor_normal_bound_reaction_error_N"]),
        } for candidate in polished],
    }


def classify_states(source_case, states, source_fixture, complete):
    if not complete:
        return "BUDGET_OR_SOLVER_STOP"
    if not states:
        return "NO_ADMISSIBLE_STATE"
    if len(states) == 1:
        return "ONE_ADMISSIBLE_MASK"
    if source_fixture.zero_boundary_ambiguity(source_case, states):
        return "AMBIGUOUS_ZERO_BOUNDARY_MASKS"
    return "MULTIPLE_ADMISSIBLE_MASKS"


def general_raw_wrench_oracle(energy_fixture: dict, adapter) -> dict:
    oracle = energy_fixture["general_kkt_oracle"]
    H = np.asarray(oracle["H"], dtype=float)
    D = np.asarray(oracle["D"], dtype=float)
    e = np.asarray(oracle["e"], dtype=float)
    W = np.asarray(oracle["W"], dtype=float)
    L, factor_check = adapter.factor_spd(H)
    laws = [{"kind": "bilateral", "k": float(oracle["k_bilateral"])},
            {"kind": "unilateral", "k": float(oracle["k_unilateral"])}]
    model, variables = adapter.build_model(L, D, e, W, laws, [],
                                           time_limit_s=PER_SOLVE_S)
    model.optimize()
    assert str(model.getStatus()) == "optimal" and model.getNSols() >= 1
    result = adapter.recover_and_check(L, H, D, e, W, laws, [], model,
                                      variables, model.getBestSol(), tolerance=TOL)
    polished = adapter.polish_fixed_mask_osqp(H, L, D, e, W, laws, [], [],
                                              tolerance=TOL)
    expected = oracle["expected"]
    assert result["source_state_pass"]
    assert polished["source_state_pass"]
    assert np.max(np.abs(result["a"] - [expected["a"]])) <= TOL
    assert np.max(np.abs(result["g"] - expected["g"])) <= TOL
    assert np.max(np.abs(result["q"] - expected["q"])) <= TOL
    assert np.max(np.abs(polished["a"] - [expected["a"]])) <= TOL
    assert np.max(np.abs(polished["g"] - expected["g"])) <= TOL
    assert np.max(np.abs(polished["q"] - expected["q"])) <= TOL
    s = model.getSolVal(model.getBestSol(), variables["slack"][1])
    assert abs(s - np.sqrt(oracle["k_unilateral"]) * expected["q"][1]) <= TOL
    assert len(variables["floor_bits"]) == 0
    return {
        "id": oracle["id"],
        "solver_status": str(model.getStatus()),
        "a": [clean(v) for v in result["a"]],
        "g": [clean(v) for v in result["g"]],
        "q": [clean(v) for v in result["q"]],
        "hinge_slack_sqrt_kq": clean(s),
        "raw_equilibrium_inf_N": clean(result["raw_equilibrium_inf_N"]),
        "source_force_law_error_N": clean(result["max_source_force_law_error_N"]),
        "scip_force_law_error_N": clean(result["max_source_force_law_error_N"]),
        "polished_force_law_error_N": clean(polished["max_source_force_law_error_N"]),
        "polished_raw_equilibrium_inf_N": clean(polished["raw_equilibrium_inf_N"]),
        "polished_hinge_slack_sqrt_kq": clean(polished["slack"][1]),
        "polish_status": polished["solver"]["status"],
        "factor_check": {k: clean(v) for k, v in factor_check.items()},
        "binary_variable_count": 0,
    }


def raw_h_compatibility_sensitivity(energy_fixture: dict, adapter) -> dict:
    """Inject a small skew into raw H; the sym-QP/raw-H audit must see it."""
    oracle = energy_fixture["general_kkt_oracle"]
    H_sym = np.asarray(oracle["H"], dtype=float)
    H_raw = H_sym.copy()
    injected_skew = 2e-11
    H_raw[0, 1] += injected_skew
    H_raw[1, 0] -= injected_skew
    L, factor_check = adapter.factor_spd(H_sym)
    D = np.asarray(oracle["D"], dtype=float)
    e = np.asarray(oracle["e"], dtype=float)
    W = np.asarray(oracle["W"], dtype=float)
    laws = [{"kind": "bilateral", "k": float(oracle["k_bilateral"])},
            {"kind": "unilateral", "k": float(oracle["k_unilateral"])}]
    result = adapter.polish_fixed_mask_osqp(H_raw, L, D, e, W, laws, [], [],
                                            tolerance=TOL)
    expected_raw_delta = float(np.max(np.abs((H_raw - H_sym) @ result["g"])))
    observed = result["compatibility_raw_H_inf_mm"]
    assert observed > 0.0, "raw-H compatibility audit collapsed to an identity"
    assert abs(observed - expected_raw_delta) <= 1e-15
    assert observed <= TOL
    assert result["compatibility_sym_H_inf_mm"] <= TOL
    return {
        "status": "PASS_RAW_H_COMPATIBILITY_SKEW_SENSITIVITY",
        "injected_skew_entry": injected_skew,
        "raw_H_minus_Hsym_inf": clean(float(np.max(np.abs(H_raw - H_sym)))),
        "independent_raw_compatibility_residual_mm": clean(observed),
        "expected_residual_from_matrix_difference_mm": clean(expected_raw_delta),
        "factor_check": {k: clean(v) for k, v in factor_check.items()},
        "within_fixture_acceptance_tolerance": observed <= TOL,
        "source_force_law_error_N": clean(result["max_source_force_law_error_N"]),
    }


def produce() -> dict:
    import adapter

    start = time.monotonic()
    source_fixture = load_module(SOURCE_SELECTOR, "pinned_source_selector")
    source_fixture.verify_source_pins()
    energy_check = load_module(SOURCE_ENERGY_CHECK, "pinned_energy_fixture_check")
    upstream_energy_pins = energy_check.pins()
    energy_fixture = json.loads(SOURCE_ENERGY.read_text())
    assert energy_fixture["status"] == "PASS_PRIMAL_KKT_AND_CONDENSED_FLOOR_MASK_TOYS"
    source_cases = source_fixture.source_cases()
    floor_results = []
    for case in source_cases:
        if time.monotonic() - start > SUITE_BUDGET_S:
            raise TimeoutError("convex-energy fixture suite budget exhausted")
        floor_results.append(source_floor_model(case, source_fixture, adapter,
                                                PER_SOLVE_S))
    raw = general_raw_wrench_oracle(energy_fixture, adapter)
    raw_h_sensitivity = raw_h_compatibility_sensitivity(energy_fixture, adapter)
    assert len(floor_results) == 8
    assert all(row["all_floor_masks_proven_exhausted"] for row in floor_results)
    return {
        "schema": "tiny_floor_binary_convex_energy_adapter/v1",
        "status": "PASS_TINY_FLOOR_BINARY_CONVEX_ENERGY_ADAPTER",
        "solver": {"pyscipopt": pyscipopt.__version__,
                   "scip": "{}.{}.{}".format(*probe_version()),
                   "osqp": osqp.__version__,
                   "numpy": np.__version__,
                   "scipy": scipy.__version__,
                   "objective_epigraph": "eta >= convex quadratic energy; minimize eta-W.T*a",
                   "global_suite_budget_s": SUITE_BUDGET_S,
                   "scip_per_solve_budget_s": PER_SOLVE_S,
                   "fixed_mask_qp_per_solve_budget_s": 15.0,
                   "fixed_mask_qp_settings": {
                       "eps_abs": 1e-10, "eps_rel": 1e-10,
                       "eps_prim_inf": 1e-10, "eps_dual_inf": 1e-10,
                       "max_iter": 200000, "time_limit": 15.0,
                       "polishing": True, "adaptive_rho": False,
                       "rho": 0.1, "sigma": 1e-6, "scaling": 0,
                       "check_termination": 1, "warm_starting": False}},
        "source_sha256": {
            "adapter.py": sha(HERE / "adapter.py"),
            "verify_adapter.py": sha(Path(__file__)),
            str(SOURCE_SELECTOR.relative_to(ROOT)): sha(SOURCE_SELECTOR),
            str(SOURCE_ENERGY.relative_to(ROOT)): sha(SOURCE_ENERGY),
            str(SOURCE_ENERGY_CHECK.relative_to(ROOT)): sha(SOURCE_ENERGY_CHECK),
            str(SOURCE_ENERGY_README.relative_to(ROOT)): sha(SOURCE_ENERGY_README),
            str((BASE / "current-coupled-indicator-selector-fixture-attempt01/known-answer.json").relative_to(ROOT)):
                sha(BASE / "current-coupled-indicator-selector-fixture-attempt01/known-answer.json"),
            **upstream_energy_pins,
        },
        "formulation": {
            "factor": "H_sym=L*L.T; y=L.T*g; recover g=L^-T*y",
            "compatibility": "q=D*a+e-L*y",
            "raw_balance": "D.T*g=W from objective stationarity; independently checked after solve",
            "objective": "eta-W.T*a, eta >= .5*||y||^2 + sum_bilateral(.5*eta_i^2) + sum_unilateral(.5*s_i^2)",
            "bilateral_energy_coordinate": "eta_i=sqrt(k_i)*q_i; .5*eta_i^2 preserves .5*k_i*q_i^2 while keeping k_i out of the quadratic epigraph coefficient",
            "unilateral_hinge": "s >= sqrt(k)*q; s >= 0",
            "floor_closed": "q_n>=0; q_t equals each supplied episode reference",
            "floor_open": "q_n<=0; q_t remains free and recovered g_t must be zero",
            "floor_normal_force": "recovered g_n must equal k*max(q_n,0), rejecting bound-reaction contamination",
            "binary_scope": "one binary per floor cell only; no binary for ordinary unilateral hinges",
            "mask_search": "no-good exclusion and proof of infeasibility after every tiny floor mask",
            "polish": "each SCIP-selected mask is independently solved as a fixed-mask convex QP; only raw-H/source-law-valid polished states are accepted",
        },
        "floor_source_cases": floor_results,
        "ordinary_unilateral_and_raw_wrench_oracle": raw,
        "raw_H_compatibility_skew_sensitivity": raw_h_sensitivity,
        "limits": [
            "All H/L matrices are 1-4 coordinate analytical fixtures; no 1840-row frame H or factor is loaded, inverted, or solved.",
            "The factor is generated only for exact symmetric positive-definite tiny fixture H and checked by reconstruction.",
            "Energy minimization alone is not path history or contact-episode uniqueness; every tested floor mask is enumerated and source laws are rechecked.",
            "A rejected fixed-mask energy minimizer is not evidence that no physical state exists outside that mask; only the exhaustive tiny fixtures classify their complete mask sets.",
            "Bounded tiny status does not estimate runtime/scalability for 100 floor binaries and 1,192 ordinary rows.",
            "No actual frame state, finite gravity continuation, climber ramp, native solver, geometry edit, or acceptance is included.",
        ],
        "actual_frame_data_loaded": False,
        "frame_state_solved": False,
        "native_run": False,
    }


def probe_version() -> tuple[int, int, int]:
    from pyscipopt import Model
    model = Model()
    version = (model.getMajorVersion(), model.getMinorVersion(), model.getTechVersion())
    del model
    return version


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(produce(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.verify:
        assert OUTPUT.read_text() == rendered, "stored convex-energy assessment differs from replay"
        print("PASS_TINY_FLOOR_BINARY_CONVEX_ENERGY_ADAPTER: 8 source masks plus raw-wrench oracle")
    else:
        OUTPUT.write_text(rendered)
        print("Wrote tiny convex-energy adapter assessment")


if __name__ == "__main__":
    main()
