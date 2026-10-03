#!/usr/bin/env python3
"""Tiny known-answer checks for explicit raw rigid-equilibrium constraints."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np
import osqp
import pyscipopt
import scipy
from pyscipopt import Model, quicksum


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
ADAPTER_DIR = BASE / "current-floor-binary-convex-energy-adapter-attempt01"
DIAG_DIR = BASE / "current-a12-root-relaxation-diagnosis-attempt01"
SOURCE_SELECTOR = BASE / "current-coupled-indicator-selector-fixture-attempt01" / "select_states.py"
ENERGY_FIXTURE = BASE / "current-primal-energy-condensation-fixture-attempt01" / "primal-energy-fixture.json"
OUTPUT = HERE / "assessment.json"
TOL = 2.0e-7
SCIP_TIME_LIMIT_S = 3.0


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def maxabs(value) -> float:
    arr = np.asarray(value)
    return float(np.max(np.abs(arr), initial=0.0))


def clean(value: float) -> float:
    value = float(value)
    if abs(value) < 5.0e-12:
        return 0.0
    return round(value, 12)


def versions() -> dict:
    model = Model()
    scip = [model.getMajorVersion(), model.getMinorVersion(), model.getTechVersion()]
    del model
    observed = {
        "pyscipopt": pyscipopt.__version__,
        "scip": ".".join(map(str, scip)),
        "numpy": np.__version__,
        "osqp": osqp.__version__,
        "scipy": scipy.__version__,
    }
    expected = {
        "pyscipopt": "6.2.0",
        "scip": "10.0.2",
        "numpy": "2.5.2",
        "osqp": "1.0.4",
        "scipy": "1.18.1",
    }
    if observed != expected:
        raise RuntimeError(f"unexpected solver stack: {observed}")
    return observed


def verify_upstream_pins(adapter_assessment: dict, diagnosis: dict) -> dict[str, str]:
    pins: dict[str, str] = {}
    for rel, expected in adapter_assessment["source_sha256"].items():
        path = ROOT / rel if rel.startswith("docs/") else ADAPTER_DIR / rel
        if sha(path) != expected:
            raise ValueError(f"frozen adapter input changed: {rel}")
        pins[str(path.relative_to(ROOT))] = expected
    for rel, expected in diagnosis["source_hashes"].items():
        path = ROOT / rel
        if sha(path) != expected:
            raise ValueError(f"corrected relaxation diagnosis input changed: {rel}")
        pins[rel] = expected
    for path in (
        ADAPTER_DIR / "README.md",
        ADAPTER_DIR / "assessment.json",
        ADAPTER_DIR / "adapter.py",
        ADAPTER_DIR / "verify_adapter.py",
        DIAG_DIR / "README.md",
        DIAG_DIR / "diagnosis.json",
        DIAG_DIR / "diagnose.py",
        SOURCE_SELECTOR,
        ENERGY_FIXTURE,
    ):
        pins[str(path.relative_to(ROOT))] = sha(path)
    if adapter_assessment["status"] != "PASS_TINY_FLOOR_BINARY_CONVEX_ENERGY_ADAPTER":
        raise ValueError("frozen adapter assessment is not PASS")
    if diagnosis["status"] != "FORMULATION_RISK_IDENTIFIED_ROOT_CAUSE_UNPROVEN":
        raise ValueError("corrected root-relaxation diagnosis status changed")
    return dict(sorted(pins.items()))


def add_raw_equilibrium(adapter, L, D, e, W, laws, floor_cells, excluded_masks=(),
                        release_zero_rows=()):
    """Extend the frozen adapter with g, y=L.T*g, and raw D.T*g=W rows."""
    L = np.asarray(L, dtype=float)
    D = np.asarray(D, dtype=float)
    e = np.asarray(e, dtype=float)
    W = np.asarray(W, dtype=float)
    model, variables = adapter.build_model(
        L, D, e, W, laws, floor_cells, excluded_masks,
        time_limit_s=SCIP_TIME_LIMIT_S)
    n = len(e)
    m = D.shape[1]
    g = [model.addVar(name=f"explicit_g_{i}", lb=None, ub=None) for i in range(n)]

    # y_i = sum_j L[j,i] g_j, exactly the pinned factor relation y=L.T*g.
    for i in range(n):
        rhs = quicksum(float(L[j, i]) * g[j] for j in range(n) if L[j, i] != 0.0)
        model.addCons(variables["y"][i] == rhs, name=f"explicit_factor_link_{i}")
    # Do not derive this row from an objective gradient: impose raw force
    # equilibrium directly on the independent g variables.
    for j in range(m):
        lhs = quicksum(float(D[i, j]) * g[i] for i in range(n) if D[i, j] != 0.0)
        model.addCons(lhs == float(W[j]), name=f"explicit_raw_equilibrium_{j}")
    for i in release_zero_rows:
        model.addCons(g[int(i)] == 0.0, name=f"explicit_released_row_zero_effort_{i}")
    variables["g_explicit"] = g
    return model, variables


def read_explicit_values(model, variables, L, D, W) -> dict:
    solution = model.getBestSol()
    y = np.asarray([model.getSolVal(solution, value) for value in variables["y"]])
    a = np.asarray([model.getSolVal(solution, value) for value in variables["a"]])
    g = np.asarray([model.getSolVal(solution, value) for value in variables["g_explicit"]])
    return {
        "y": y,
        "a": a,
        "g": g,
        "factor_link_inf": maxabs(np.asarray(L).T @ g - y),
        "raw_equilibrium_inf_N": maxabs(np.asarray(D).T @ g - np.asarray(W)),
    }


def run_floor_mask_suite(adapter, original_verifier, source_fixture, old_assessment) -> dict:
    source_cases = source_fixture.source_cases()
    old_by_id = {item["id"]: item for item in old_assessment["floor_source_cases"]}
    case_results = []
    total_masks = 0
    for case in source_cases:
        H_raw, e, C = original_verifier.condensed_source_case(case)
        L, _factor_check = adapter.factor_spd(H_raw)
        n = len(e)
        D = np.zeros((n, 0), dtype=float)
        W = np.zeros(0, dtype=float)
        contact_count = len(case["tangent_reference_mm"])
        penalty = float(case["normal_penalty_n_per_mm"])
        laws = []
        floor_cells = []
        basis = case["contact_basis_diagonal"]
        for i in range(contact_count):
            tangent, normal = 2 * i, 2 * i + 1
            laws.extend([{"kind": "tangent"}, {"kind": "unilateral", "k": penalty}])
            ref_q = -float(basis[tangent]) * float(case["tangent_reference_mm"][i])
            floor_cells.append({"normal_row": normal,
                                "tangent_rows_and_references": [(tangent, ref_q)]})

        all_masks = [list(mask) for mask in itertools.product((False, True), repeat=contact_count)]
        mask_results = []
        polished_states = []
        for target_mask in all_masks:
            # Excluding every other mask forces this prescribed branch without
            # ranking or selecting physical history across masks.
            excluded = [mask for mask in all_masks if mask != target_mask]
            model, variables = add_raw_equilibrium(
                adapter, L, D, e, W, laws, floor_cells, excluded_masks=excluded)
            model.optimize()
            status = str(model.getStatus())
            if status != "optimal" or model.getNSols() < 1:
                raise ValueError(f"augmented prescribed-mask solve stopped: {case['id']} {target_mask} {status}")
            candidate = adapter.recover_and_check(
                L, H_raw, D, e, W, laws, floor_cells,
                model, variables, model.getBestSol(), tolerance=TOL)
            explicit = read_explicit_values(model, variables, L, D, W)
            if candidate["mask"] != target_mask:
                raise ValueError(f"no-good restrictions did not fix requested mask: {case['id']} {target_mask}")
            if (explicit["factor_link_inf"] > TOL or explicit["raw_equilibrium_inf_N"] > TOL
                    or maxabs(explicit["g"] - candidate["g"]) > TOL):
                raise ValueError(f"explicit g/factor/equilibrium identity failed: {case['id']} {target_mask}")

            # Retain the adapter's independent fixed-mask QP polish and its
            # raw-H/q/source-law audits unchanged.
            exact = adapter.polish_fixed_mask_osqp(
                H_raw, L, D, e, W, laws, floor_cells, target_mask, tolerance=TOL)
            u = -C @ exact["q"]
            K = np.asarray(case["operator_n_per_mm"], dtype=float)
            F = np.asarray(case["external_wrench_n"], dtype=float)
            source_force = np.asarray(case["contact_basis_diagonal"], dtype=float) * exact["g"]
            source_balance = maxabs(K @ u - source_force - F)
            polished_pass = bool(exact["source_state_pass"] and source_balance <= TOL
                                 and maxabs(D.T @ exact["g"] - W) <= TOL)
            exact["source_state_pass"] = polished_pass
            state = {
                "closed_mask": exact["mask"],
                "u_mm": [original_verifier.clean(v) for v in u],
                "tangent_forces_n": [original_verifier.clean(v) for v in exact["g"][0::2]],
                "normal_forces_n": [original_verifier.clean(v) for v in exact["g"][1::2]],
            }
            state["max_equilibrium_residual_n"] = original_verifier.clean(source_balance)
            if polished_pass:
                source_fixture.validate_solution(case, state)
                source_fixture.expected_matches(case, state)
                polished_states.append(state)

            mask_results.append({
                "mask": target_mask,
                "scip_status": status,
                "augmented_y_equals_LTg_inf": original_verifier.clean(explicit["factor_link_inf"]),
                "augmented_raw_Dt_g_minus_W_inf_N": original_verifier.clean(explicit["raw_equilibrium_inf_N"]),
                "scip_source_state_pass": bool(candidate["source_state_pass"]),
                "polish_source_state_pass": polished_pass,
                "raw_q_compatibility_inf_mm": original_verifier.clean(exact["compatibility_raw_H_inf_mm"]),
                "polish_raw_equilibrium_inf_N": original_verifier.clean(exact["raw_equilibrium_inf_N"]),
                "source_force_law_error_N": original_verifier.clean(exact["max_source_force_law_error_N"]),
                "normal_bound_reaction_error_N": original_verifier.clean(exact["max_floor_normal_bound_reaction_error_N"]),
                "source_balance_inf_N": original_verifier.clean(source_balance),
            })

        classification = original_verifier.classify_states(
            case, polished_states, source_fixture, complete=True)
        expected = old_by_id[case["id"]]
        masks = [state["closed_mask"] for state in polished_states]
        if classification != expected["observed_classification"]:
            raise ValueError(f"classification changed under explicit equilibrium: {case['id']} {classification}")
        if masks != expected["accepted_masks"]:
            raise ValueError(f"accepted prescribed masks changed: {case['id']} {masks}")
        if len(mask_results) != 2 ** contact_count:
            raise ValueError(f"did not check every prescribed mask: {case['id']}")
        total_masks += len(mask_results)
        case_results.append({
            "id": case["id"],
            "mask_count": len(mask_results),
            "classification": classification,
            "expected_classification": expected["observed_classification"],
            "accepted_masks": masks,
            "matches_frozen_adapter": True,
            "per_mask_checks": mask_results,
        })
    if total_masks != 24 or len(case_results) != 8:
        raise ValueError(f"expected 8 cases and 24 masks, got {len(case_results)}/{total_masks}")
    return {"case_count": len(case_results), "prescribed_mask_count": total_masks,
            "all_classifications_and_masks_preserved": True,
            "scope": "Each floor mask is fixed before optimization; no cross-mask energy winner or physical uniqueness claim.",
            "cases": case_results}


def run_nontrivial_equilibrium_oracle(adapter, energy_fixture) -> dict:
    oracle = energy_fixture["general_kkt_oracle"]
    H = np.asarray(oracle["H"], dtype=float)
    D = np.asarray(oracle["D"], dtype=float)
    e = np.asarray(oracle["e"], dtype=float)
    W = np.asarray(oracle["W"], dtype=float)
    L, factor_check = adapter.factor_spd(H)
    laws = [{"kind": "bilateral", "k": float(oracle["k_bilateral"])},
            {"kind": "unilateral", "k": float(oracle["k_unilateral"])}]
    model, variables = add_raw_equilibrium(adapter, L, D, e, W, laws, [])
    model.optimize()
    if str(model.getStatus()) != "optimal" or model.getNSols() < 1:
        raise ValueError(f"explicit-equilibrium general oracle stopped: {model.getStatus()}")
    check = adapter.recover_and_check(
        L, H, D, e, W, laws, [], model, variables, model.getBestSol(), tolerance=TOL)
    explicit = read_explicit_values(model, variables, L, D, W)
    polished = adapter.polish_fixed_mask_osqp(H, L, D, e, W, laws, [], [], tolerance=TOL)
    expected = oracle["expected"]
    differences = {
        "a": maxabs(check["a"] - [expected["a"]]),
        "g": maxabs(check["g"] - expected["g"]),
        "q": maxabs(check["q"] - expected["q"]),
        "polished_a": maxabs(polished["a"] - [expected["a"]]),
        "polished_g": maxabs(polished["g"] - expected["g"]),
        "polished_q": maxabs(polished["q"] - expected["q"]),
    }
    if (not check["source_state_pass"] or not polished["source_state_pass"]
            or max(differences.values()) > TOL
            or explicit["factor_link_inf"] > TOL
            or explicit["raw_equilibrium_inf_N"] > TOL):
        raise ValueError("nontrivial raw-force identity/oracle did not preserve its known answer")
    return {
        "id": oracle["id"],
        "solver_status": str(model.getStatus()),
        "explicit_equilibrium_row_count": int(D.shape[1]),
        "factor_check": factor_check,
        "explicit_y_equals_LTg_inf": clean(explicit["factor_link_inf"]),
        "explicit_raw_Dt_g_minus_W_inf_N": clean(explicit["raw_equilibrium_inf_N"]),
        "recovered_raw_equilibrium_inf_N": clean(check["raw_equilibrium_inf_N"]),
        "raw_q_compatibility_inf_mm": clean(check["compatibility_raw_H_inf_mm"]),
        "source_force_law_error_N": clean(check["max_source_force_law_error_N"]),
        "hinge_error": clean(check["max_hinge_error"]),
        "fixed_mask_polish_raw_equilibrium_inf_N": clean(polished["raw_equilibrium_inf_N"]),
        "known_answer_max_abs_differences": {k: clean(v) for k, v in differences.items()},
        "used_explicit_source_equilibrium_constraint": True,
        "used_g_gradient_stationarity_as_equilibrium": False,
    }


def run_exact_gauge_oracle(adapter) -> dict:
    H = np.eye(2)
    L = np.eye(2)
    D = np.asarray([[1.0, 1.0], [0.0, 0.0]])
    e = np.zeros(2)
    W = np.asarray([0.2, 0.2])
    laws = [{"kind": "bilateral", "k": 1.0}, {"kind": "bilateral", "k": 1.0}]
    v = np.asarray([1.0, -1.0])
    model, variables = add_raw_equilibrium(adapter, L, D, e, W, laws, [])
    model.optimize()
    if str(model.getStatus()) != "optimal" or model.getNSols() < 1:
        raise ValueError(f"zero-work exact gauge fixture did not solve: {model.getStatus()}")
    check = adapter.recover_and_check(
        L, H, D, e, W, laws, [], model, variables, model.getBestSol(), tolerance=TOL)
    explicit = read_explicit_values(model, variables, L, D, W)
    shifted_a = explicit["a"] + 17.0 * v
    shifted_q = D @ shifted_a + e - H @ explicit["g"]
    original_q = D @ explicit["a"] + e - H @ explicit["g"]
    objective_shift = -float(W @ (17.0 * v))
    if (not check["source_state_pass"] or maxabs(D @ v) != 0.0 or abs(float(W @ v)) > 1.0e-15
            or maxabs(shifted_q - original_q) > 1.0e-12 or abs(objective_shift) > 1.0e-12
            or explicit["raw_equilibrium_inf_N"] > TOL):
        raise ValueError("exact full-D zero-work gauge oracle failed")

    bad_W = np.asarray([0.2, 0.25])
    bad_model, _ = add_raw_equilibrium(adapter, L, D, e, bad_W, laws, [])
    bad_model.optimize()
    bad_status = str(bad_model.getStatus())
    exact_obstruction = float(v @ bad_W)
    if bad_status != "infeasible" or exact_obstruction == 0.0:
        raise ValueError(f"nonzero-work exact gauge was not rejected: {bad_status}")
    return {
        "D": D.tolist(), "null_direction_v": v.tolist(),
        "zero_work_W": W.tolist(), "perturbed_work_W": bad_W.tolist(),
        "D_v_exact": (D @ v).tolist(),
        "zero_work_vT_W": float(v @ W),
        "perturbed_work_vT_W": exact_obstruction,
        "zero_work_solver_status": str(model.getStatus()),
        "zero_work_explicit_equilibrium_inf_N": clean(explicit["raw_equilibrium_inf_N"]),
        "zero_work_source_state_pass": bool(check["source_state_pass"]),
        "gauge_shift_a": (17.0 * v).tolist(),
        "q_change_under_exact_gauge_shift": (shifted_q - original_q).tolist(),
        "objective_change_under_exact_gauge_shift": objective_shift,
        "perturbed_work_solver_status": bad_status,
        "classification": "zero work remains a flat compatible gauge; nonzero work makes exact full-D balance infeasible",
    }


def fixed_mask_feasibility(adapter, L, D, e, W, laws, floor_cells,
                           mask: list[bool], release_zero_rows=()) -> dict:
    all_masks = [list(value) for value in itertools.product((False, True), repeat=len(floor_cells))]
    excluded = [value for value in all_masks if value != mask]
    model, variables = add_raw_equilibrium(
        adapter, L, D, e, W, laws, floor_cells,
        excluded_masks=excluded, release_zero_rows=release_zero_rows)
    # A pinned a is only a constructive algebraic witness for this fixture;
    # it is not a gauge, support, or selector variable bound.
    model.addCons(variables["a"][0] == 1.0, name="known_witness_a_value")
    model.setObjective(variables["epigraph"], "minimize")
    model.optimize()
    result = {"status": str(model.getStatus()), "model": model, "variables": variables}
    if result["status"] == "optimal" and model.getNSols() >= 1:
        explicit = read_explicit_values(model, variables, L, D, W)
        audited = adapter.recover_and_check(
            L, np.asarray(L) @ np.asarray(L).T, D, e, W, laws, floor_cells,
            model, variables, model.getBestSol(), tolerance=TOL)
        result.update({"explicit": explicit, "audit": audited})
    return result


def run_released_tangent_oracle(adapter) -> dict:
    H = np.eye(2)
    L = np.eye(2)
    D = np.asarray([[0.0], [1.0]])
    e = np.zeros(2)
    W = np.asarray([1.0])
    laws = [{"kind": "unilateral", "k": 1.0}, {"kind": "tangent"}]
    floor_cells = [{"normal_row": 0, "tangent_rows_and_references": [(1, 0.0)]}]
    v = np.asarray([1.0])
    D_energy = D[[0], :]

    open_witness = fixed_mask_feasibility(adapter, L, D, e, W, laws, floor_cells, [False])
    open_audit = open_witness.get("audit", {})
    if open_witness["status"] != "optimal":
        raise ValueError("release-law open witness with raw equilibrium should be feasible")
    if (open_audit.get("raw_equilibrium_inf_N", float("inf")) > TOL
            or open_audit.get("compatibility_raw_H_inf_mm", float("inf")) > TOL
            or open_audit.get("max_source_force_law_error_N", float("inf")) > TOL
            or open_audit.get("max_floor_tangent_or_open_effort_error", 0.0) <= 0.5):
        raise ValueError("open-row fixture failed to isolate the missing zero-effort law")

    closed_witness = fixed_mask_feasibility(adapter, L, D, e, W, laws, floor_cells, [True])
    closed_audit = closed_witness.get("audit", {})
    if closed_witness["status"] != "optimal" or not closed_audit.get("source_state_pass", False):
        raise ValueError("closed-held-reference control witness failed")

    enforced_release = fixed_mask_feasibility(
        adapter, L, D, e, W, laws, floor_cells, [False], release_zero_rows=[1])
    if enforced_release["status"] != "infeasible":
        raise ValueError("explicit g_T=0 release law did not expose raw-load incompatibility")

    # Exact branch direction: D_energy*v=0 and the normal row is unchanged,
    # while the released tangent coordinate moves by t and costs no spring
    # energy. Full D*v is nonzero, so equilibrium alone can carry W through
    # the nonphysical open tangent effort g_T=1.
    ray = float(v[0])
    if (maxabs(D_energy @ v) != 0.0 or maxabs(D @ v) == 0.0
            or float(W @ v) != 1.0 or maxabs(D.T @ open_audit["g"] - W) > TOL):
        raise ValueError("released-tangent null/work identity changed")
    return {
        "D": D.tolist(), "D_energy": D_energy.tolist(), "null_direction_v": v.tolist(),
        "D_energy_v": (D_energy @ v).tolist(), "D_full_v": (D @ v).tolist(),
        "W_dot_v_generalized_force_N": float(W @ v),
        "open_mask_equilibrium_only": {
            "status": open_witness["status"],
            "witness_a": open_audit["a"].tolist(),
            "witness_g": open_audit["g"].tolist(),
            "witness_q_raw": (D @ open_audit["a"] + e - H @ open_audit["g"]).tolist(),
            "raw_equilibrium_inf_N": clean(open_audit["raw_equilibrium_inf_N"]),
            "raw_q_compatibility_inf_mm": clean(open_audit["compatibility_raw_H_inf_mm"]),
            "source_force_law_error_N": clean(open_audit["max_source_force_law_error_N"]),
            "open_tangent_effort_error_N": clean(open_audit["max_floor_tangent_or_open_effort_error"]),
            "physical_open_source_law_pass": False,
            "witness_a_pinning_scope": "constructive finite witness only; not a selector bound or support",
        },
        "closed_mask_reference_control": {
            "status": closed_witness["status"],
            "source_state_pass": bool(closed_audit["source_state_pass"]),
            "tangent_reference_error": clean(closed_audit["max_floor_tangent_or_open_effort_error"]),
            "witness_g": closed_audit["g"].tolist(),
            "witness_q_raw": (D @ closed_audit["a"] + e - H @ closed_audit["g"]).tolist(),
        },
        "open_mask_with_gT_zero": {"status": enforced_release["status"],
                                   "raw_equilibrium_requires_gT_N": 1.0},
        "energy_ray": {
            "a_t": "a_0 + t*v, t>=0",
            "ray_parameter_t_unit": "mm",
            "q_normal_change": 0.0,
            "released_q_tangent_change_per_t": float((D @ v)[1]),
            "energy_change_N_mm": 0.0,
            "W_dot_v_generalized_force_N": float(W @ v),
            "original_objective_change": "-t*(W.T*v) N*mm; here W.T*v=1 N and t is measured in mm",
            "equilibrium_only_is_sufficient": False,
        },
        "interpretation": "Exact energy-row-subset null; full-D equilibrium is met only with nonzero open g_T, so retain and audit g_T=0 independently.",
    }


def produce() -> dict:
    adapter = load_module(ADAPTER_DIR / "adapter.py", "frozen_tiny_energy_adapter")
    original_verifier = load_module(ADAPTER_DIR / "verify_adapter.py", "frozen_tiny_energy_verifier")
    source_fixture = load_module(SOURCE_SELECTOR, "frozen_tiny_source_selector")
    source_fixture.verify_source_pins()
    old_assessment = json.loads((ADAPTER_DIR / "assessment.json").read_text())
    diagnosis = json.loads((DIAG_DIR / "diagnosis.json").read_text())
    energy_fixture = json.loads(ENERGY_FIXTURE.read_text())
    if energy_fixture["status"] != "PASS_PRIMAL_KKT_AND_CONDENSED_FLOOR_MASK_TOYS":
        raise ValueError("pinned tiny energy source oracle is not PASS")
    pins = verify_upstream_pins(old_assessment, diagnosis)
    pins[str((HERE / "README.md").relative_to(ROOT))] = sha(HERE / "README.md")
    pins[str((HERE / "verify_equilibrium.py").relative_to(ROOT))] = sha(HERE / "verify_equilibrium.py")
    pins = dict(sorted(pins.items()))
    observed_versions = versions()

    masks = run_floor_mask_suite(adapter, original_verifier, source_fixture, old_assessment)
    general = run_nontrivial_equilibrium_oracle(adapter, energy_fixture)
    gauge = run_exact_gauge_oracle(adapter)
    release = run_released_tangent_oracle(adapter)
    raw_h = original_verifier.raw_h_compatibility_sensitivity(energy_fixture, adapter)
    if raw_h["status"] != "PASS_RAW_H_COMPATIBILITY_SKEW_SENSITIVITY":
        raise ValueError("unchanged independent raw-H skew probe failed")

    return {
        "schema": "floor_energy_explicit_raw_equilibrium_strengthening_fixture/v1",
        "status": "PASS_TINY_FLOOR_ENERGY_EQUILIBRIUM_STRENGTHENING",
        "source_pins_sha256": pins,
        "solver": observed_versions,
        "formulation": {
            "explicit_variables": "g is a signed free variable; impose y=L.T*g",
            "explicit_equilibrium": "For each source rigid coordinate j, impose sum_i D[i,j]*g[i] = W[j] as a separate linear equality.",
            "units": "q,a,e in mm; g,W in N for translational generalized coordinates; D dimensionless; H in mm/N; L in sqrt(mm/N); y in sqrt(N*mm); energy and W.T*a in N*mm.",
            "not_a_gradient_identity": True,
            "compatibility_and_source_audit": "Keep frozen q=D*a+e-L*y; independently compare against raw q=D*a+e-H_raw*g and original spring/floor force laws.",
            "mask_semantics": "Enumerate each prescribed floor mask by excluding all other masks; do not rank energy between masks or claim a physical winner/uniqueness.",
            "released_tangent": "An open floor tangent still requires the independent source law g_T=0; raw equilibrium alone may carry nonzero open effort.",
        },
        "prescribed_floor_masks": masks,
        "nontrivial_raw_equilibrium_known_answer": general,
        "exact_full_D_gauge_oracle": gauge,
        "released_tangent_law_oracle": release,
        "unchanged_raw_H_skew_audit": raw_h,
        "scope": {
            "tiny_analytical_coordinates_only": True,
            "frame_operator_or_actual_frame_matrices_loaded": False,
            "frame_state_solved": False,
            "native_run": False,
            "global_physical_energy_winner_claimed": False,
            "physical_or_mechanical_acceptance": False,
        },
        "limits": [
            "The 24 prescribed floor-mask cases have no generalized rigid coordinate, so their explicit balance rows are empty; the nontrivial two-carrier oracle and exact gauge/release toys exercise nonempty balance equations.",
            "The exact gauges are analytical fixtures, not exact null certificates for the frame's stored floating-point D matrix.",
            "Passing these tiny cases shows classification invariance and exposes the released-row law requirement; it does not establish actual-frame selector readiness, root-bound improvement, a gravity state, or global mask uniqueness.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = produce()
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.verify:
        if not OUTPUT.is_file() or OUTPUT.read_text() != rendered:
            raise SystemExit("stored explicit-equilibrium strengthening result does not replay")
        print("PASS_REPLAY_FLOOR_ENERGY_EXPLICIT_RAW_EQUILIBRIUM_FIXTURE")
    else:
        OUTPUT.write_text(rendered)
        print("PASS_TINY_FLOOR_ENERGY_EQUILIBRIUM_STRENGTHENING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
