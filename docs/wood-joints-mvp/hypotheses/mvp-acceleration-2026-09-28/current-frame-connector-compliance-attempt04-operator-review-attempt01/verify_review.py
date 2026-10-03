#!/usr/bin/env python3
"""Read-only provenance and D/W identity check; does not form H or factor bodies."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import scipy
import scipy.sparse as sp

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
ATTEMPT = BASE / "current-frame-connector-compliance-attempt04"
NATIVE = BASE / "current-frame-pure-solid-matrix-export-native-attempt01"
MODEL = BASE / "current-springa-frame-input-adapter-attempt01" / "a12-rear" / "model.json"
PARSER = BASE / "current-frame-pure-solid-export-assessment-method-attempt01" / "assess_matrixstorage.py"
PROJECTION = BASE / "current-frame-physical-connector-projection-contract-attempt01"
LOADS = BASE / "current-frame-pure-solid-matrix-export-preflight-attempt01" / "source-load-maps.json"
HELPER = BASE / "current-frame-free-body-condensation-preflight-attempt01" / "condensation.py"
METHOD = BASE / "current-elastic-quotient-method-preflight-attempt02"
SCALING = BASE / "current-rigid-wrench-residual-scaling-fixture-attempt01"
RANK_AUDIT = BASE / "current-frame-gravity-rank-readiness-attempt01" / "audit.json"
RANK_AUDIT_SOURCE = BASE / "current-frame-gravity-rank-readiness-attempt01" / "audit.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def maxabs(value) -> float:
    arr = np.asarray(value)
    return float(np.max(np.abs(arr))) if arr.size else 0.0


def run() -> dict:
    inputs = json.loads((ATTEMPT / "inputs.json").read_text())
    assessment = json.loads((ATTEMPT / "assessment.json").read_text())
    if assessment["status"] != "PASS_SOURCE_BOUND_FRAME_CONNECTOR_COMPLIANCE":
        raise ValueError("parent attempt04 is not a completed PASS")
    if assessment["input_record_sha256"] != sha(ATTEMPT / "inputs.json"):
        raise ValueError("attempt04 assessment does not pin its input record")
    pin = json.loads((ATTEMPT / "output-pin.json").read_text())
    if pin["assessment_sha256"] != sha(ATTEMPT / "assessment.json"):
        raise ValueError("attempt04 assessment output pin mismatch")
    if len(assessment["bodies"]) != 50 or assessment["bodies_completed"] != 50:
        raise ValueError("attempt04 body completion count changed")
    for rel, expected in inputs["source_sha256"].items():
        if sha(ROOT / rel) != expected:
            raise ValueError(f"attempt04 input hash changed: {rel}")
    for name, expected in assessment["outputs_sha256"].items():
        if sha(ATTEMPT / name) != expected:
            raise ValueError(f"attempt04 output hash changed: {name}")

    bodies = assessment["bodies"]
    if (sum(item["physical_dofs"] for item in bodies) != 37647
            or any(item["active_source_rows"] <= 0 for item in bodies)):
        raise ValueError("body partition or per-body active-row count does not close")
    if any(item["operator_audit"]["status"] != "PASS_ELASTIC_QUOTIENT_SCREEN"
           or not item["raw_interface_wrench_retained_in_D"]
           or not item["raw_load_wrench_retained_in_W"] for item in bodies):
        raise ValueError("a body lacks operator screen or raw D/W retention flag")
    if any(item["max_kkt_relative_residual"] > 1.0e-10 for item in bodies):
        raise ValueError("a body's unchanged nodal KKT force gate exceeds 1e-10")

    # Verify the recorded method fixture and scaling fixture inputs by pins.
    quotient_assessment = json.loads((METHOD / "assessment.json").read_text())
    if (quotient_assessment["status"] != "PASS_ELASTIC_QUOTIENT_METHOD_KNOWN_ANSWER"
            or quotient_assessment["source_sha256"]["quotient_method.py"] != sha(METHOD / "quotient_method.py")
            or quotient_assessment["source_sha256"]["bounded_refinement.py"]
            != sha(BASE / "current-bordered-refinement-diagnostic-attempt01" / "bounded_refinement.py")):
        raise ValueError("attempt02 method known-answer source pins do not replay")
    quotient_fixture = mod(METHOD / "verify_quotient.py", "attempt04_review_quotient_fixture")
    if quotient_fixture.run() != quotient_assessment:
        raise ValueError("attempt02 quotient known-answer fixture does not replay")
    scaling_assessment = json.loads((SCALING / "assessment.json").read_text())
    if (scaling_assessment["status"] != "PASS_RIGID_WRENCH_RESIDUAL_SCALING_FIXTURE"
            or scaling_assessment["source_sha256"]["quotient_method_attempt01"]
            != sha(BASE / "current-elastic-quotient-method-preflight-attempt01" / "quotient_method.py")):
        raise ValueError("independent residual scaling fixture source pins do not replay")
    scaling_fixture = mod(SCALING / "verify_scaling.py", "attempt04_review_scaling_fixture")
    if scaling_fixture.run() != scaling_assessment:
        raise ValueError("independent rigid-wrench residual scaling fixture does not replay")

    expected_aggregate_gate = (
        "Unchanged nodal residual propagated coordinatewise through R.T, plus measured "
        "independently gated contraction-order error; old fixed absolute gate remains reported"
    )
    builder_source = (ATTEMPT / "build_compliance.py").read_text()
    required_builder_calls = (
        "quotient.solve_quotient_chunk(factor, system, body_K, R, projected, operator_report=operator_audit)",
        "if solved['status'] != quotient.PASS_ELASTIC_QUOTIENT_SCREEN:",
        "displacement = elastic_solve(Fb, '12 separate source gravity/climber columns')",
    )
    if (inputs["aggregate_gate"] != expected_aggregate_gate
            or inputs["chunk_size"] != 16
            or any(fragment not in builder_source for fragment in required_builder_calls)
            or "P K P" not in assessment["elastic_method"]):
        raise ValueError("attempt04 does not integrate the pinned quotient gate as declared")

    parser = mod(PARSER, "attempt04_review_frame_source_parser")
    helper = mod(HELPER, "attempt04_review_rigid_helper")
    source = parser.load_frame_source_model(MODEL)
    labels = parser.parse_dof_file(NATIVE / "model.dof")
    parser.require_dof_bijection(labels, source["physical_nodes"], 37647)
    body_names = list(source["bodies"])
    if assessment["body_names_in_rigid_column_order"] != body_names:
        raise ValueError("stored 300-coordinate column order differs from authenticated source bodies")
    owner_by_label = [source["owner_by_node"][node] for node, _ in labels]
    row_for = {tuple(label): i for i, label in enumerate(labels)}
    if len(row_for) != len(labels) or len(body_names) != 50:
        raise ValueError("native DOF/body identity map is not bijective")
    owners = np.asarray(owner_by_label, dtype=np.int32)

    contract = json.loads((PROJECTION / "projection-contract.json").read_text())
    index_map = json.loads((PROJECTION / "physical-index-map.json").read_text())
    rows = contract["rows"]
    if len(rows) != 1840 or len(index_map) != 12549:
        raise ValueError("physical connector contract dimensions changed")
    b_row, b_col, b_val = [], [], []
    for i, record in enumerate(rows):
        for term in record["physical_sparse_row"]:
            coordinate = int(term["coordinate_index"])
            node = int(index_map[coordinate // 3]["node"])
            b_row.append(i)
            b_col.append(row_for[(node, coordinate % 3 + 1)])
            b_val.append(float(term["coefficient"]))
    B_expected = sp.csr_matrix((b_val, (b_row, b_col)), shape=(1840, len(labels)))
    B_expected.sum_duplicates()
    B_expected.sort_indices()
    B = sp.load_npz(ATTEMPT / "B.npz").tocsr()
    B.sort_indices()
    Bdiff = (B - B_expected).tocsr()
    Bdiff.eliminate_zeros()
    if B.shape != (1840, 37647) or B.nnz != 62607 or Bdiff.nnz:
        raise ValueError("stored B does not reproduce the source projection rows")

    expected_identities = [{
        "row": i,
        "row_id": r["row_id"],
        "family": r["family"],
        "source_group": r.get("source_group"),
        "source_element": r.get("source_element"),
        "source_inventory_row_index": r.get("source_inventory_row_index"),
        "law": r["law"],
        "ownership": r.get("ownership"),
    } for i, r in enumerate(rows)]
    saved_identities = json.loads((ATTEMPT / "row-identities.json").read_text())
    if saved_identities != expected_identities:
        raise ValueError("saved row identity order differs from the frozen projection contract")

    with np.load(ATTEMPT / "operators.npz", allow_pickle=False) as z:
        H = z["H"]
        D = z["D"]
        e = z["e"]
        W = z["W"]
    if (H.shape != (1840, 1840) or D.shape != (1840, 300)
            or e.shape != (1840, 12) or W.shape != (300, 12)
            or not all(np.all(np.isfinite(x)) for x in (H, D, e, W))):
        raise ValueError("stored elastic operator arrays have invalid shape or nonfinite values")

    # Reproduce only the cheap kinematic/raw-wrench maps from frozen sources.
    # No K factor, H action, physical f, or D.T @ f state is computed.
    D_expected = np.zeros((1840, 300), dtype=np.float64)
    W_expected = np.zeros((300, 12), dtype=np.float64)
    load_cases = json.loads(LOADS.read_text())["cases"]
    if len(load_cases) != 6:
        raise ValueError("separated source-load map must contain six cases")
    F = np.zeros((len(labels), 12), dtype=np.float64)
    load_columns = []
    for ci, case in enumerate(load_cases):
        for offset, kind in enumerate(("gravity_nodal_map", "climber_nodal_map")):
            col = 2 * ci + offset
            load_columns.append({"case_id": case["case_id"], "kind": kind})
            for node, xyz_force in case[kind].items():
                for direction, value in enumerate(xyz_force, 1):
                    F[row_for[(int(node), direction)], col] = float(value)
    body_centers = []
    for body_id, body_name in enumerate(body_names):
        dofs = np.flatnonzero(owners == body_id)
        center, R, _ = helper.rigid_basis([labels[int(j)] for j in dofs], source["coordinates"])
        body_centers.append(center)
        D_expected[:, 6 * body_id:6 * body_id + 6] = np.asarray(B[:, dofs] @ R)
        W_expected[6 * body_id:6 * body_id + 6, :] = R.T @ F[dofs, :]
    d_error = maxabs(D - D_expected)
    w_error = maxabs(W - W_expected)
    if d_error > 1.0e-13 or w_error > 1.0e-12:
        raise ValueError(f"raw D/W recomposition mismatch: D={d_error}, W={w_error}")

    # Compare the actual source-bound D subsets with the earlier independent
    # 300-coordinate branch-rank screen. The 200 floor-tangent rows are
    # conditional captured-reference constraints; their inclusion is only a
    # counterfactual all-bearing/no-slip envelope.
    rank_module = mod(RANK_AUDIT_SOURCE, "attempt04_review_rank_audit")
    rank_pins = rank_module.check_pins()
    rank_baseline = json.loads(RANK_AUDIT.read_text())
    if (rank_baseline["status"] != "PASS_SOURCE_BOUND_RIGID_BODY_BRANCH_SCREEN_INITIAL_GRAVITY_GAUGE_OPEN"
            or rank_baseline["native_solve_executed"] is not False
            or rank_baseline["full_physical_tangent_rank_claimed"] is not False):
        raise ValueError("prior rank audit is not the expected source-only branch screen")
    families = np.asarray([row["family"] for row in rows])
    branch_masks = {
        "all_open_bilateral_only": families == "bilateral_spring2",
        "all_normal_no_floor_T": families != "conditional_floor_tangent_constraint",
        "all_open_plus_conditional_floor_T": families != "unilateral_springa",
        "all_normal_plus_conditional_floor_T": np.ones(len(families), dtype=bool),
    }
    prior_branch_names = {
        "all_open_bilateral_only": "all_unilateral_open_bilateral_only",
        "all_normal_no_floor_T": "all_unilateral_active_normal_only_envelope",
        "all_open_plus_conditional_floor_T": "all_unilateral_open_with_conditional_all_bearing_floor_stick",
        "all_normal_plus_conditional_floor_T": "all_unilateral_active_with_conditional_all_bearing_floor_stick",
    }
    branch_rank_checks = {}
    for name, mask in branch_masks.items():
        current = rank_module.rank_sensitivity(D[mask, :])
        prior = rank_baseline["rigid_body_branch_screens"][prior_branch_names[name]]["screen"]
        matches = (current["rank_by_relative_cutoff"] == prior["rank_by_relative_cutoff"]
                   and current["nullity_by_relative_cutoff"] == prior["nullity_by_relative_cutoff"])
        if not matches or current["rows"] != prior["rows"]:
            raise ValueError(f"D branch rank differs from earlier source screen: {name}")
        branch_rank_checks[name] = {
            "rows": current["rows"],
            "rank_by_relative_cutoff": current["rank_by_relative_cutoff"],
            "nullity_by_relative_cutoff": current["nullity_by_relative_cutoff"],
            "matches_prior_audit": True,
        }

    # Build unit common global translations and a unit global z rotation in
    # the authenticated 50-body coordinate order. The Rz translation at each
    # body's arithmetic-mean datum is omega x datum; the rotational coordinate
    # uses the same 1000 mm/rad scale as the body rigid basis.
    common_modes = np.zeros((300, 3), dtype=np.float64)
    for body_id, center in enumerate(body_centers):
        offset = 6 * body_id
        common_modes[offset:offset + 6, 0] = (1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        common_modes[offset:offset + 6, 1] = (0.0, 1.0, 0.0, 0.0, 0.0, 0.0)
        common_modes[offset:offset + 6, 2] = (-center[1], center[0], 0.0, 0.0, 0.0, 1000.0)
    common_modes /= np.linalg.norm(common_modes, axis=0)
    normal_only = D[branch_masks["all_normal_no_floor_T"], :]
    normal_row_norms = np.linalg.norm(normal_only, axis=1)
    kept_normal = normal_row_norms > 1.0e-14
    normal_mode_residuals = np.max(
        np.abs((normal_only[kept_normal] / normal_row_norms[kept_normal, None]) @ common_modes), axis=0
    )
    if np.max(normal_mode_residuals) > 1.0e-10:
        raise ValueError("Tx/Ty/Rz are not annihilated by the all-normal/no-floor-T D subset")
    all_row_norms = np.linalg.norm(D, axis=1)
    kept_all = all_row_norms > 1.0e-14
    full_mode_residuals = np.max(
        np.abs((D[kept_all] / all_row_norms[kept_all, None]) @ common_modes), axis=0
    )
    gravity_columns = [i for i, column in enumerate(assessment["load_columns"])
                       if column["kind"] == "gravity_nodal_map"]
    gravity_mode_work = np.asarray([
        np.asarray([
            (-center[1], center[0], 0.0, 0.0, 0.0, 1000.0)
            if mode_id == 2 else ((1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
                                  if mode_id == 0 else (0.0, 1.0, 0.0, 0.0, 0.0, 0.0))
            for center in body_centers
        ], dtype=np.float64).reshape(300) @ W[:, gravity_columns]
        for mode_id in range(3)
    ])
    if maxabs(gravity_mode_work) > 1.0e-8:
        raise ValueError("separated gravity source wrenches do work on a common planar rigid mode")

    checks = assessment["compliance_checks"]
    if (checks["reciprocity_relative_inf"] > checks["reciprocity_tolerance"]
            or checks["min_symmetric_part_eigenvalue_mm_per_N"]
            < -checks["negative_eigenvalue_tolerance_mm_per_N"]):
        raise ValueError("pinned compliance check values do not satisfy their recorded screens")
    if (assessment["physical_response_computed"] or assessment["contact_state_selected"]
            or assessment["native_launch"] or assessment["mechanical_acceptance"]):
        raise ValueError("attempt04 scope flags unexpectedly claim a physical/native result")

    return {
        "schema": "attempt04_elastic_operator_identity_review/v1",
        "status": "PASS_ATTEMPT04_ELASTIC_OPERATOR_IDENTITY_REVIEW",
        "attempt04_assessment_sha256": sha(ATTEMPT / "assessment.json"),
        "attempt04_input_sha256": sha(ATTEMPT / "inputs.json"),
        "attempt04_build_source_sha256": sha(ATTEMPT / "build_compliance.py"),
        "method_attempt02_sha256": sha(METHOD / "quotient_method.py"),
        "inputs_and_outputs_hashes_match": True,
        "method_fixture_status": quotient_assessment["status"],
        "method_fixture_replayed": True,
        "scaling_fixture_status": scaling_assessment["status"],
        "scaling_fixture_replayed": True,
        "aggregate_gate_integration": {
            "declared_gate": inputs["aggregate_gate"],
            "source_call_and_strict_status_gate_authenticated": True,
            "chunk_size": inputs["chunk_size"],
            "expected_projected_rhs_chunks": int(sum(
                (body["active_source_rows"] + inputs["chunk_size"] - 1) // inputs["chunk_size"] + 1
                for body in bodies
            )),
            "all_chunks_cleared_by_completed_builder": len(bodies) == 50,
            "max_unchanged_nodal_KKT_relative_residual": max(
                body["max_kkt_relative_residual"] for body in bodies
            ),
            "legacy_zero_lambda_failed_chunks_preserved_separately": int(sum(
                body["legacy_zero_multiplier_failed_chunks"] for body in bodies
            )),
            "zero_lambda_gate_reinterpreted_as_support": False,
        },
        "body_counts": {"completed": len(bodies), "physical_dofs": int(sum(x["physical_dofs"] for x in bodies)),
                        "active_body_row_incidences": int(sum(x["active_source_rows"] for x in bodies)),
                        "distinct_source_rows": 1840,
                        "legacy_zero_lambda_failed_chunks": int(sum(x["legacy_zero_multiplier_failed_chunks"] for x in bodies))},
        "source_projection_map": {"shape": list(B.shape), "nnz": int(B.nnz),
                                  "exact_contract_match": Bdiff.nnz == 0,
                                  "ordered_source_rows": len(saved_identities),
                                  "duplicate_text_ids_preserved_by_row_position": True},
        "operator_shapes": {"H": list(H.shape), "D": list(D.shape), "e": list(e.shape), "W": list(W.shape)},
        "D_recomposition": {"definition": "per-body B_b R_b in the recorded 50-body rigid-coordinate order",
                            "max_abs_difference": d_error, "matches_source_map": d_error <= 1.0e-13},
        "W_recomposition": {"definition": "per-body R_b.T F_b from six separate gravity/climber source cases",
                            "columns": load_columns, "max_abs_difference": w_error,
                            "matches_separated_source_maps": w_error <= 1.0e-12,
                            "raw_wrenches_preserved": True},
        "raw_D_rank_reconciliation": {
            "prior_audit_sha256": sha(RANK_AUDIT),
            "prior_audit_source_sha256": sha(RANK_AUDIT_SOURCE),
            "prior_audit_input_pins_verified": len(rank_pins),
            "method": "Repeat prior dense SVD with unit-row and unit-column equilibration on source-row subsets of stored D; no stiffness weighting.",
            "branch_screens": branch_rank_checks,
            "global_modes": {
                "basis": ["global Tx", "global Ty", "global Rz"],
                "all_normal_no_floor_T_row_normalized_residuals": normal_mode_residuals.tolist(),
                "all_1840_rows_including_conditional_floor_T_residuals": full_mode_residuals.tolist(),
                "gravity_virtual_work_by_mode_and_source_case": gravity_mode_work.tolist(),
                "gravity_virtual_work_units": "N*mm for 1 mm Tx/Ty and 1 rad Rz modes",
                "no_floor_T_common_modes_verified": True,
                "gravity_is_orthogonal_to_these_modes_at_1e-8_N_mm": True,
                "conditional_floor_T_rows_constrain_these_modes": bool(np.max(full_mode_residuals) > 1.0e-10),
            },
            "limits": [
                "The all-normal/no-floor-T rows are an optimistic one-sided tangent envelope, not a selected gravity-start active set.",
                "The all-open branch retains 74 additional relative-body kinematic mechanisms beyond its six common rigid modes at the 1e-10 cutoff.",
                "The conditional all-bearing floor-T rows cannot be treated as an initial support or admissible tangent without a captured no-slip history.",
                "These kinematic rank checks do not replace a state-consistent physical tangent or solve D.T @ f = W.",
            ],
        },
        "H_checks_from_pinned_assessment": checks,
        "physical_scope": {"D_transpose_f_equals_W_solved": False,
                           "physical_response_computed": False,
                           "contact_state_selected": False,
                           "native_launch": False,
                           "mechanical_acceptance": False},
        "limitations": [
            "H is checked by its pinned source-bound assessment; this review does not recompute H, eigensolve it, or refactor any body stiffness.",
            "D and W are source-reconstructed kinematic/load maps only. Their presence does not establish a globally balanced connector force f.",
            "The arrays are elastic basis terms, not a physical body-load response or joint acceptance.",
        ],
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    result = run()
    target = HERE / "assessment.json"
    if args.verify:
        if json.loads(target.read_text()) != result:
            raise SystemExit("stored attempt04 operator review does not replay")
        print("PASS_REPLAY_ATTEMPT04_ELASTIC_OPERATOR_IDENTITY_REVIEW")
    else:
        target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
