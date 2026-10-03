"""Read-only hash and metadata replay for the bounded A12 root diagnosis."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
SELECTOR = BASE / "current-a12-gravity-direction-convex-selector-attempt01"
OP_REVIEW = BASE / "current-frame-connector-compliance-attempt04-operator-review-attempt01"
RANK = BASE / "current-frame-gravity-rank-readiness-attempt01"
METHOD = BASE / "current-floor-binary-convex-energy-adapter-attempt01"
CONTRACT = BASE / "current-gravity-direction-initial-selector-contract-attempt01"
OUTPUT = HERE / "diagnosis.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def clean(value: float) -> float:
    return round(float(value), 15)


def produce() -> dict:
    selector_inputs_path = SELECTOR / "inputs.json"
    selector_assessment_path = SELECTOR / "assessment.json"
    selector_pin_path = SELECTOR / "output-pin.json"
    solver_log_path = SELECTOR / "scip-solve-1.log"
    selector_script = SELECTOR / "select_direction.py"
    selector_inputs = read_json(selector_inputs_path)
    selector_assessment = read_json(selector_assessment_path)
    selector_pin = read_json(selector_pin_path)
    method_assessment = read_json(METHOD / "assessment.json")
    operator_assessment = read_json(OP_REVIEW / "assessment.json")
    rank_assessment = read_json(RANK / "audit.json")

    source_pin_results = {
        rel: {"expected": expected, "observed": sha(ROOT / rel),
              "matches": sha(ROOT / rel) == expected}
        for rel, expected in sorted(selector_inputs["source_sha256"].items())
    }
    assert len(source_pin_results) == 18
    assert all(result["matches"] for result in source_pin_results.values())
    assert sha(selector_inputs_path) == selector_assessment["input_record_sha256"]
    assert sha(selector_assessment_path) == selector_pin["assessment_sha256"]
    assert selector_assessment["solver_log_sha256"][solver_log_path.name] == sha(solver_log_path)

    # The selector copied the exact Python sources used into its own frozen
    # source tree. Verify these copies without importing or executing them.
    copied_sources = {
        "select_direction.py": SELECTOR / "sources" / selector_script.relative_to(ROOT),
        "adapter.py": SELECTOR / "sources" / (METHOD / "adapter.py").relative_to(ROOT),
        "verify_adapter.py": SELECTOR / "sources" / (METHOD / "verify_adapter.py").relative_to(ROOT),
    }
    copied_source_hashes = {name: sha(path) for name, path in copied_sources.items()}
    assert copied_source_hashes["select_direction.py"] == sha(selector_script)
    assert copied_source_hashes["adapter.py"] == selector_inputs["source_sha256"][
        str((METHOD / "adapter.py").relative_to(ROOT))]
    assert copied_source_hashes["verify_adapter.py"] == selector_inputs["source_sha256"][
        str((METHOD / "verify_adapter.py").relative_to(ROOT))]

    adapter_source = copied_sources["adapter.py"].read_text()
    selector_source = copied_sources["select_direction.py"].read_text()
    model_semantics_confirmed = all(fragment in adapter_source for fragment in (
        'name=f"a_{j}", lb=None, ub=None',
        'name=f"y_{j}", lb=None, ub=None',
        'name=f"q_{i}", lb=None, ub=None',
        'name="total_elastic_energy", lb=None, ub=None',
        'model.addCons(epigraph >= energy',
        'objective = epigraph - quicksum(float(W[j]) * a[j]',
    ))
    assert model_semantics_confirmed
    assert "D.T@f-W" in selector_source

    operator_modes = operator_assessment["raw_D_rank_reconciliation"]["global_modes"]
    work = operator_modes["gravity_virtual_work_by_mode_and_source_case"]
    mode_names = operator_modes["basis"]
    gravity_columns = [col for col in operator_assessment["W_recomposition"]["columns"]
                       if col["kind"] == "gravity_nodal_map"]
    # This virtual-work array is already restricted to the six gravity cases;
    # W_recomposition itself interleaves gravity and climber columns.
    assert len(gravity_columns) == len(work[0]) == 6
    mode_by_case = {
        mode_names[i]: [float(value) for value in work[i]]
        for i in range(len(mode_names))
    }
    all_gravity_work_max = max(abs(value) for values in mode_by_case.values()
                               for value in values)
    a12_rear_gravity_index = next(i for i, col in enumerate(gravity_columns)
                                  if col["case_id"] == "a12-rear")
    a12_rear_work = {mode_names[i]: float(work[i][a12_rear_gravity_index])
                     for i in range(len(mode_names))}
    branch = operator_modes["all_normal_no_floor_T_row_normalized_residuals"]
    branch_record = operator_assessment["raw_D_rank_reconciliation"]["branch_screens"][
        "all_normal_no_floor_T"]
    all_open_record = rank_assessment["rigid_body_branch_screens"][
        "all_unilateral_open_bilateral_only"]
    full_rows_record = rank_assessment["rigid_body_branch_screens"][
        "all_unilateral_active_with_conditional_all_bearing_floor_stick"]
    solve = selector_assessment["solves"][0]
    assert selector_assessment["status"] == "BUDGET_OR_SOLVER_STOP"
    assert solve["solver_status"] == "timelimit"
    assert solve["nodes"] == 1 and solve["solutions"] == 0
    assert operator_assessment["status"] == "PASS_ATTEMPT04_ELASTIC_OPERATOR_IDENTITY_REVIEW"
    assert method_assessment["status"] == "PASS_TINY_FLOOR_BINARY_CONVEX_ENERGY_ADAPTER"

    source_paths = [
        selector_inputs_path, selector_assessment_path, selector_pin_path,
        selector_script, solver_log_path,
        copied_sources["adapter.py"], copied_sources["verify_adapter.py"],
        METHOD / "assessment.json", OP_REVIEW / "assessment.json",
        OP_REVIEW / "README.md", OP_REVIEW / "verify_review.py",
        RANK / "audit.json", RANK / "README.md",
        CONTRACT / "README.md", HERE / "README.md", HERE / "diagnose.py",
    ]
    source_hashes = {str(path.relative_to(ROOT)): sha(path)
                     for path in sorted(source_paths)}
    log_text = solver_log_path.read_text()
    presolve_line = next(line for line in log_text.splitlines()
                         if line.startswith("Presolving Time:"))
    presolve_seconds = float(presolve_line.split(":", 1)[1].strip())
    log_indicators = {
        "processed_node_count": solve["nodes"],
        "primal_bound_sentinel": "+1.00000000000000e+20 (0 solutions)" in log_text,
        "dual_bound_sentinel": "Dual Bound         : -1.00000000000000e+20" in log_text,
        "gap_infinite": "Gap                : infinite" in log_text,
        "subroutine_timing_breakdown_recorded": False,
    }
    assert all(value for key, value in log_indicators.items()
               if key != "subroutine_timing_breakdown_recorded")

    return {
        "schema": "a12_convex_selector_root_relaxation_diagnosis/v1",
        "status": "FORMULATION_RISK_IDENTIFIED_ROOT_CAUSE_UNPROVEN",
        "candidate": "compact-floor-flush-wood-joints-development",
        "case_id": "a12-rear",
        "geometry_revision_id": rank_assessment["geometry_revision_id"],
        "source_hashes": source_hashes,
        "all_18_frozen_input_source_pins_match": True,
        "frozen_python_source_copies_match": True,
        "model_formulation": {
            "coordinate_definition": "q=D*a+e-L*y; g=L^-T*y",
            "objective": "min eta-W_g^T*a; eta >= convex quadratic spring energy",
            "free_continuous_variables": ["a (300 rigid coordinates)",
                "y (1840 energy coordinates)", "q (1840 connector coordinates)",
                "eta (energy epigraph)"],
            "variable_bounds": "selector explicitly sets lb=None, ub=None for a,y,q,eta; hinge slacks are nonnegative",
            "floor_tangent_state": "all-open floor mask has no held tangent equations; the branch model does not add a gauge or finite displacement bounds",
            "discrete_model_sizes_after_presolve": {
                "binary": 100, "continuous": 5873, "linear_constraints": 3732,
                "nonlinear_energy_constraints": 1, "indicator_constraints": 600,
            },
        },
        "conditional_branch_recession_analysis": {
            "energy_row_subset_direction": "For a recession direction v, require D_energy*v=0, held floor-tangent rows unchanged, and all active/open unilateral hinge signs and floor-normal sign constraints to remain feasible along the chosen ray. Rows for released floor tangents are omitted from D_energy and may change q freely without energy or floor-admissibility cost. With y fixed, the objective changes by -t*(W_g.T*v).",
            "subset_work_nonzero": "If such a feasible one-sided ray has nonzero raw gravity work with the objective-decreasing sign, the energy epigraph has no finite lower bound on that branch; zero work leaves a flat coordinate along that ray.",
            "exact_full_D_null": "If the exact full projected matrix D satisfies D*v=0, adding D.T*g=W_g makes a branch with W_g.T*v!=0 infeasible: multiply the equality by v to obtain 0=W_g.T*v. If W_g.T*v=0, that exact gauge remains compatible and flat unless a separate gauge convention is justified.",
            "released_tangent_caveat": "For a D_energy-null mode that changes only released floor-tangent rows, full D*v need not be zero. D.T*g=W_g alone can then balance work through nonzero released-tangent g, which violates the physical released-row law g_T=0. Enforce and audit that law independently; do not infer a physical state from raw balance alone.",
            "apply_to_stored_frame": "The all-normal/no-floor-T row screen has three common modes with tiny but nonzero stored-row residuals and cutoff-sensitive rank. The full 1,840-row all-bearing envelope has rank 300 in its source-only screen. Neither report proves an exact stored D_energy or full-D null vector, and no gravity-work calculation was made on the 74 extra all-open screen modes.",
            "identified_issue": "The selector leaves all displacement coordinates unbounded and does not add raw equilibrium as an explicit root constraint. The observed no-bound stop is compatible with a weak/near-null branch relaxation; exact recession requires a feasible row-subset direction and its unprojected raw gravity work, neither of which is certified for the actual initial branch.",
        },
        "recorded_common_planar_mode_evidence": {
            "mode_order": mode_names,
            "gravity_virtual_work_by_common_mode_N_mm": {
                key: values for key, values in mode_by_case.items()},
            "a12_rear_gravity_virtual_work_N_mm": {
                key: value for key, value in a12_rear_work.items()},
            "max_abs_work_over_six_gravity_maps_N_mm": clean(all_gravity_work_max),
            "max_abs_work_exceeds_zero_bitwise": all_gravity_work_max > 0.0,
            "source_review_acceptance_screen_N_mm": 1e-8,
            "all_normal_no_floor_tangent_row_normalized_mode_residuals": [
                clean(value) for value in branch],
            "all_normal_no_floor_tangent_rank_nullity": {
                "rank_1e-10": branch_record["rank_by_relative_cutoff"]["1e-10"],
                "nullity_1e-10": branch_record["nullity_by_relative_cutoff"]["1e-10"],
                "rank_1e-12": branch_record["rank_by_relative_cutoff"]["1e-12"],
                "nullity_1e-12": branch_record["nullity_by_relative_cutoff"]["1e-12"],
                "rank_1e-14": branch_record["rank_by_relative_cutoff"]["1e-14"],
                "nullity_1e-14": branch_record["nullity_by_relative_cutoff"]["1e-14"],
            },
            "scope_note": "The optimistic all-normal/no-floor-T row set is a source-only envelope, not an actual selected gravity-start branch. It establishes common-mode conditioning risk, not the active state or an exact null proof.",
        },
        "all_open_bilateral_only_kinematic_screen": {
            "common_modes": 6,
            "additional_relative_mechanisms_at_cutoff_1e-10":
                all_open_record["additional_body_rigid_nullity_at_1e-10"],
            "nullity_by_relative_cutoff":
                all_open_record["screen"]["nullity_by_relative_cutoff"],
            "interpretation": "The source-only all-open row screen has 80 numerical kinematic null directions at cutoff 1e-10 (six common plus 74 additional relative mechanisms). This is not an exact null certificate for the stored floating-point matrix and does not evaluate gravity work on the 74 additional directions or prove an unbounded branch.",
        },
        "full_1840_row_envelope_screen": {
            "rank_at_relative_cutoffs":
                full_rows_record["screen"]["rank_by_relative_cutoff"],
            "nullity_at_relative_cutoffs":
                full_rows_record["screen"]["nullity_by_relative_cutoff"],
            "interpretation": "This optimistic all-bearing/full-row screen has rank 300 at its recorded cutoffs. It shows that the three planar modes in the no-floor-T energy-row subset are not full-D null modes when conditional floor tangent rows are included; those tangent coordinates are free only on the released branch.",
        },
        "recorded_root_stop": {
            "status": selector_assessment["status"],
            "solve_status": solve["solver_status"],
            "nodes": solve["nodes"], "solutions": solve["solutions"],
            "build_seconds": clean(solve["build_elapsed_seconds"]),
            "presolve_seconds": presolve_seconds,
            "solver_time_limit_seconds": selector_inputs["first_solve_limit_s"],
            "log_indicators": log_indicators,
            "interpretation": "No incumbent or finite dual bound was reported before the time limit. The sentinels and one-node log do not prove mathematical unboundedness and contain no root subroutine timing; no subroutine is identified as the bottleneck.",
        },
        "explicit_equilibrium_constraint_assessment": {
            "candidate": "Introduce g with y=L.T*g and add raw D.T*g=W_g as an explicit linear equality.",
            "mathematical_status": "Necessary for any finite stationary solution of the current energy model: a enters the objective linearly and otherwise only through q=D*a+e-L*y. Floor normal/tangent constraints are written on q, so their multipliers do not add a term to a-stationarity.",
            "source_law_effect": "The equality is necessary equilibrium, not a replacement for spring/tangent laws or raw compatibility. In an augmented optimization it adds a multiplier to g-stationarity; a feasible early-stop point is not validated by D.T*g=W alone. At an exact global optimum of an original fixed-mask convex branch, the equilibrium equality already holds and adding it as a redundant physical-state restriction should preserve that branch optimum; verify this against all tiny state-classification oracles first.",
            "relaxation_effect": "It may strengthen a weak root relaxation, but this is an untested performance hypothesis and the log cannot confirm it.",
            "gauge_limit": "For an exact full-D null v with W_g.T*v!=0, the equality makes that branch infeasible by multiplication with v, exposing incompatible load work; zero-work full-D gauges remain flat. For a D_energy-null direction that changes only released tangent rows, the equality alone may balance work through nonphysical released-row g_T unless the source released-law g_T=0 is separately enforced.",
            "tiny_fixture_gate_before_any_frame_use": "On the existing bilateral/unilateral raw-wrench and all floor-mask toys, add the equality and verify unchanged admissible physical states and explicit zero-boundary/no-state/multiple-state classifications. Then test exact-zero-work and perturbed-work gauge toys. Do not project raw W or add an arbitrary anchor.",
        },
        "bounded_next_remedy": [
            "Do not retry the frame with a larger time budget.",
            "First obtain a raw-D/raw-W common-mode compatibility certificate at documented units and tolerances; SVD cutoff alone is not an exact null certificate.",
            "If exact gauge modes are established, require their raw gravity work to be compatible with zero before using a quotient-coordinate formulation; otherwise stop as load-incompatible. Preserve raw D.T*g=W and raw-H audits.",
            "Only after the tiny explicit-equilibrium and gauge toys pass should the parent decide whether a revised bounded root formulation merits separate authorization/readiness review.",
        ],
        "official_documentation": [
            {"url": "https://pyscipopt.readthedocs.io/en/v6.2.0/api/model.html",
             "use": "PySCIPOpt 6.2.0 documents lb=None as negative infinity and ub=None as positive infinity."},
            {"url": "https://pyscipopt.readthedocs.io/en/v6.2.0/faq.html",
             "use": "SCIP's nonlinear objective is represented with a new epigraph variable and a nonlinear constraint."},
            {"url": "https://pyscipopt.readthedocs.io/en/v6.2.0/tutorials/expressions.html",
             "use": "The pinned tutorial gives the equivalent linear-objective epigraph formulation; this supports the model construction but gives no assurance of a useful root bound for unbounded gauge coordinates."},
        ],
        "scope": {
            "read_only": True, "native_run": False,
            "frame_solve": False, "H_rebuilt": False,
            "heavy_rank_or_factor": False, "geometry_changed": False,
            "actual_matrices_loaded": False,
            "diagnosis_is_a_proof_of_actual_root_cause": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(produce(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.verify:
        assert OUTPUT.read_text() == rendered, "stored read-only diagnosis differs from replay"
        print("PASS_A12_ROOT_RELAXATION_DIAGNOSIS: frozen pins and recorded algebra")
    else:
        OUTPUT.write_text(rendered)
        print("Wrote read-only A12 root-relaxation diagnosis")


if __name__ == "__main__":
    main()
