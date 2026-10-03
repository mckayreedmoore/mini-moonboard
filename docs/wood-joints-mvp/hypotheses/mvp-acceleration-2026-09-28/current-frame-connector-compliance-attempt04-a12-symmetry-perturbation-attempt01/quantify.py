#!/usr/bin/env python3
"""Measure Hsym-H on the seven force vectors from the pinned A12 replay."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import scipy.sparse as sp


ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = ROOT / BASE / "current-frame-connector-compliance-attempt04-a12-symmetry-perturbation-attempt01"
PRIOR = ROOT / BASE / "current-frame-connector-compliance-attempt04-a12-response-replay-attempt01"
COMP = ROOT / BASE / "current-frame-connector-compliance-attempt04"
RUN = ROOT / BASE / "current-springa-selected-floor-a12-rear-attempt03"
OPERATOR_NATIVE = ROOT / BASE / "current-frame-pure-solid-matrix-export-native-attempt01"
SOURCE_MODEL = ROOT / BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
LOAD_MAPS = ROOT / BASE / "current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json"
MATRIX_PARSER = ROOT / BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
RIGID_BASIS = ROOT / BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py"
NATIVE_TOKEN_PARSER = ROOT / BASE / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
OUTPUT = HERE / "assessment.json"

PRIOR_SCRIPT_SHA256 = "c99d00164c77da8ace56ffe86659b2b9d8b2674fa3cbf6bf50e455c2f9a512d1"
PRIOR_ASSESSMENT_SHA256 = "42cc8c0559e4cf6655bdc23013c5c5eed56e22bb2d295e1260251b608627b0fe"
H_NPZ_SHA256 = "88a2f2f384edb7be7daa0e20cc87c7b8672ed13e975f8e86afd56d8aeb385b79"
OUTPUT_SCHEMA = "a12_rear_Hsym_perturbation_diagnostic/v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def import_source(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"source_not_importable:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def max_abs(value: np.ndarray) -> float:
    return float(np.max(np.abs(value))) if value.size else 0.0


def main() -> None:
    replay_path = PRIOR / "replay.py"
    prior_assessment_path = PRIOR / "assessment.json"
    require(sha(replay_path) == PRIOR_SCRIPT_SHA256, "prior_replay_script_hash_changed")
    require(sha(prior_assessment_path) == PRIOR_ASSESSMENT_SHA256,
            "prior_replay_assessment_hash_changed")
    replay = import_source(replay_path, "pinned_a12_response_replay_for_Hsym")
    prior = load_json(prior_assessment_path)
    require(prior.get("status") == "PASS_A12_REAR_AUTHENTICATED_RESPONSE_REPLAY_AGAINST_FROZEN_REDUCTION"
            and prior.get("all_increments_passed") is True
            and len(prior.get("increment_checks", [])) == 7,
            "prior_A12_replay_not_passed")

    # Reauthenticate exactly the prior packet's source inventory. No input or
    # output in that packet is modified by this diagnostic.
    stale_prior_inputs = []
    for key, expected in prior["input_sha256"].items():
        path = replay.PINNED.get(key)
        if path is None:
            stale_prior_inputs.append(key)
            continue
        actual_path = {
            name: path_value
            for name, path_value in {
                "run/response.json": replay.RUN / "response.json",
                "run/model.dat": replay.RUN / "model.dat",
                "run/model.inp": replay.RUN / "model.inp",
                "run/model.json": replay.RUN / "model.json",
                "run/freeze.json": replay.RUN / "freeze.json",
                "run/execution.json": replay.RUN / "execution.json",
                "run/parent-terminal-assessment.json": replay.RUN / "parent-terminal-assessment.json",
                "run/parent-all-body-response-audit.json": replay.RUN / "parent-all-body-response-audit.json",
                "comp/assessment.json": COMP / "assessment.json",
                "comp/inputs.json": COMP / "inputs.json",
                "comp/operators.npz": COMP / "operators.npz",
                "comp/B.npz": COMP / "B.npz",
                "comp/row-identities.json": COMP / "row-identities.json",
                "operator-native/model.dof": OPERATOR_NATIVE / "model.dof",
                "operator-native/model.sti": OPERATOR_NATIVE / "model.sti",
                "operator-native/freeze.json": OPERATOR_NATIVE / "freeze.json",
                "operator-native/execution.json": OPERATOR_NATIVE / "execution.json",
                "operator-native/assessment.json": OPERATOR_NATIVE / "assessment.json",
                "source_model.json": SOURCE_MODEL,
                "projection/projection-contract.json": ROOT / BASE / "current-frame-physical-connector-projection-contract-attempt01/projection-contract.json",
                "loads/source-load-maps.json": LOAD_MAPS,
                "matrix-parser": ROOT / BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
                "rigid-basis": ROOT / BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
                "native-token-parser": ROOT / BASE / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py",
            }.items() if name == key
        }.get(key)
        if actual_path is None or not actual_path.is_file() or sha(actual_path) != expected:
            stale_prior_inputs.append(key)
    require(not stale_prior_inputs, "prior_replay_source_pins_changed:" + ",".join(stale_prior_inputs))

    operators_path = COMP / "operators.npz"
    require(sha(operators_path) == H_NPZ_SHA256, "frozen_H_D_e_W_packet_hash_changed")
    with np.load(operators_path) as record:
        H = record["H"]
        D = record["D"]
        e = record["e"]
        W = record["W"]
    B = sp.load_npz(COMP / "B.npz").tocsr()
    rows = load_json(COMP / "row-identities.json")
    response = load_json(RUN / "response.json")
    parser = replay.import_source(MATRIX_PARSER, "matrixstorage_parser_for_Hsym_replay")
    source_model = parser.load_frame_source_model(SOURCE_MODEL)
    rigid = replay.import_source(RIGID_BASIS, "rigid_basis_for_Hsym_replay")
    dat_parser = replay.import_source(NATIVE_TOKEN_PARSER, "native_dat_parser_for_Hsym_replay")
    labels = parser.parse_dof_file(OPERATOR_NATIVE / "model.dof")
    owners = np.asarray([source_model["owner_by_node"][node] for node, _ in labels], dtype=np.int64)
    body_names = list(source_model["bodies"])
    body_index = {name: index for index, name in enumerate(body_names)}
    native = dat_parser.parse_native_blocks((RUN / "model.dat").read_text(encoding="utf-8"))
    loads = load_json(LOAD_MAPS)["cases"]
    case = next(item for item in loads if item["case_id"] == "a12-rear")
    columns = load_json(COMP / "assessment.json")["load_columns"]
    selected = {item["kind"]: int(item["column"]) for item in columns if item["case_id"] == "a12-rear"}
    require(selected == {"gravity_nodal_map": 0, "climber_nodal_map": 1},
            "A12_load_column_map_changed")

    delta_H = 0.5 * (H.T - H)
    per_increment = []
    max_perturbation = 0.0
    max_raw_ratio = 0.0
    max_sym_ratio = 0.0
    sym_pass = True
    force_hashes = []
    for inc, prior_inc in zip(response["increments"], prior["increment_checks"], strict=True):
        lam = float(inc["load_factor"])
        state = native[float(inc["time"])]
        u = np.asarray([state["u"][node][direction - 1] for node, direction in labels], dtype=np.float64)
        ur = np.asarray([state["u_radius"][node][direction - 1] for node, direction in labels], dtype=np.float64)
        q = np.asarray(B @ u).reshape(-1)
        qr = np.asarray(abs(B) @ ur).reshape(-1)

        springa = {str(item["source_group"]): item for item in inc["springa_components"]}
        bilateral = {str(item["source_group"]): item for item in inc["retained_bilateral_spring2_components"]}
        active = {str(item["source_row_id"]): item for item in inc["exact_floor_tangent_reactions"]}
        inactive = {str(item["source_row_id"]): item for item in inc["inactive_floor_tangent_zero_actions"]}
        f = np.zeros(1840, dtype=np.float64)
        fr = np.zeros(1840, dtype=np.float64)
        for index, row in enumerate(rows):
            if row["family"] == "unilateral_springa":
                item = springa[str(row["source_group"])]
                f[index] = float(item["native_endpoint_internal_force_N"])
                fr[index] = float(item["native_endpoint_internal_radius_N"])
            elif row["family"] == "bilateral_spring2":
                item = bilateral[str(row["source_group"])]
                f[index] = float(item["force_on_first_local_N"])
                fr[index] = float(item["force_rounding_radius_local_N"])
            else:
                item = active.get(str(row["row_id"]))
                if item is None:
                    require(str(row["row_id"]) in inactive, "floor_T_source_row_missing")
                    f[index] = 0.0
                    fr[index] = 0.0
                    continue
                direction = np.asarray(row["ownership"]["direction_global_xyz"], dtype=np.float64)
                corrected = float(item["raw_reference_rf_N"] - item["transferred_source_load_N"])
                require(abs(corrected - float(item["recovered_physical_tangent_reaction_N"])) <= 2.0e-12,
                        "corrected_floor_T_reaction_changed")
                owner_no = body_index[str(row["ownership"]["first_body"])]
                require(np.allclose(D[index, 6 * owner_no:6 * owner_no + 3], direction,
                                    rtol=0.0, atol=2.0e-10), "floor_T_multiplier_sign_map_changed")
                # Same q-conjugate sign used in the prior raw-H replay.
                f[index] = -corrected
                fr[index] = float(np.abs(direction) @ np.asarray(item["force_rounding_radius_xyz_n"]))

        force_hashes.append(hashlib.sha256(np.asarray(f, dtype="<f8").tobytes()).hexdigest())
        a = np.zeros(300, dtype=np.float64)
        ar = np.zeros(300, dtype=np.float64)
        for body_no, body_name in enumerate(body_names):
            dofs = np.flatnonzero(owners == body_no)
            body_labels = [labels[int(index)] for index in dofs]
            _, R, _ = rigid.rigid_basis(body_labels, source_model["coordinates"], rotation_scale_mm=1000.0)
            projector = np.linalg.solve(R.T @ R, R.T)
            a[6 * body_no:6 * body_no + 6] = projector @ u[dofs]
            ar[6 * body_no:6 * body_no + 6] = np.abs(projector) @ ur[dofs]

        e_total = lam * (e[:, selected["gravity_nodal_map"]] + e[:, selected["climber_nodal_map"]])
        raw_residual = q - (D @ a + e_total - H @ f)
        delta_q = delta_H @ f
        sym_residual = raw_residual + delta_q
        arithmetic_guard = 128.0 * np.finfo(float).eps * (
            np.abs(q) + np.abs(D) @ np.abs(a) + np.abs(e_total) + np.abs(H) @ np.abs(f) + 1.0
        )
        dat_bound = qr + np.abs(D) @ ar + np.abs(H) @ fr + arithmetic_guard
        raw_ratio = np.abs(raw_residual) / np.maximum(dat_bound, np.finfo(float).tiny)
        sym_ratio = np.abs(sym_residual) / np.maximum(dat_bound, np.finfo(float).tiny)
        require(abs(max_abs(raw_residual) - float(prior_inc["q_minus_Da_minus_e_plus_Hf_max_abs_mm"])) <= 1.0e-12,
                "reassembled_force_vector_or_raw_H_replay_differs_from_prior_packet")
        require(abs(float(np.max(raw_ratio)) - float(prior_inc["q_equation_max_abs_residual_to_bound_ratio"])) <= 1.0e-10,
                "raw_H_DAT_interval_diagnostic_differs_from_prior_packet")
        perturb_row = int(np.argmax(np.abs(delta_q)))
        sym_gate_pass = bool(np.all(np.abs(sym_residual) <= dat_bound))
        sym_pass = sym_pass and sym_gate_pass
        max_perturbation = max(max_perturbation, max_abs(delta_q))
        max_raw_ratio = max(max_raw_ratio, float(np.max(raw_ratio)))
        max_sym_ratio = max(max_sym_ratio, float(np.max(sym_ratio)))
        per_increment.append({
            "load_factor": lam,
            "force_vector_sha256_f64le": force_hashes[-1],
            "Hsym_minus_H_times_f_max_row_abs_mm": max_abs(delta_q),
            "largest_perturbation_row_index": perturb_row,
            "largest_perturbation_source_row_id": rows[perturb_row]["row_id"],
            "raw_H_max_abs_q_residual_mm": max_abs(raw_residual),
            "raw_H_max_abs_q_residual_to_original_DAT_bound_ratio": float(np.max(raw_ratio)),
            "Hsym_max_abs_q_residual_mm": max_abs(sym_residual),
            "Hsym_max_abs_q_residual_to_original_DAT_bound_ratio": float(np.max(sym_ratio)),
            "Hsym_within_original_H_DAT_interval_gate": sym_gate_pass,
            "maximum_original_DAT_only_q_bound_mm": float(np.max(dat_bound)),
            "unchanged_D_transpose_f_minus_W_max_abs_force_N": prior_inc["D_transpose_f_minus_W_max_abs_force_N"],
            "unchanged_D_transpose_f_minus_W_max_abs_moment_Nmm": prior_inc["D_transpose_f_minus_W_max_abs_moment_Nmm"],
            "unchanged_D_transpose_f_minus_W_interval_ratio": prior_inc["wrench_equation_max_abs_residual_to_bound_ratio"],
            "unchanged_D_transpose_f_equals_W_gate_passed": True,
        })

    comp_assessment = load_json(COMP / "assessment.json")
    raw_H_symmetric_metric = comp_assessment["compliance_checks"]["reciprocity_relative_inf"]
    require(len(force_hashes) == 7 and len(set(force_hashes)) == 7,
            "expected_seven_distinct_source_force_vectors")
    report = {
        "schema": OUTPUT_SCHEMA,
        "status": "PASS_BOUNDED_HSYMMETRY_PERTURBATION_DIAGNOSTIC_ONLY",
        "source_replay_assessment_sha256": PRIOR_ASSESSMENT_SHA256,
        "source_replay_script_sha256": PRIOR_SCRIPT_SHA256,
        "source_response_sha256": replay.PINNED["run/response.json"],
        "source_compliance_assessment_sha256": replay.PINNED["comp/assessment.json"],
        "raw_H_npz_sha256": H_NPZ_SHA256,
        "raw_H_modified_or_replaced": False,
        "symmetrized_H_written_or_frozen": False,
        "new_native_or_state_solve_performed": False,
        "method": {
            "definition": "Hsym = (H + H.T)/2; compute perturbation as (Hsym-H)@f without altering the frozen raw H array",
            "same_seven_force_vectors_as_prior_replay": True,
            "same_source_sign_mapping": True,
            "floor_T_multiplier": "negative corrected physical tangent action, with the previously verified source sign and RF correction",
            "original_DAT_U_RF_intervals_reused": True,
        },
        "raw_H_recorded_reciprocity_relative_inf": raw_H_symmetric_metric,
        "maximum_rowwise_abs_Hsym_minus_H_times_f_mm": max_perturbation,
        "maximum_raw_H_original_interval_ratio": max_raw_ratio,
        "maximum_Hsym_original_interval_ratio": max_sym_ratio,
        "Hsym_passes_all_original_raw_H_q_interval_gates": sym_pass,
        "per_increment": per_increment,
        "interpretation": [
            "The result quantifies the numerical energy approximation's change on the seven authenticated A12-rear force vectors only.",
            "DAT rounding intervals remain separate from elastic-operator numerical residual diagnostics; this packet adds no new error bound for the operator calculation.",
            "Passing the existing response intervals is compatibility evidence for this response, not acceptance of symmetrization as the solver operator or a mechanical acceptance result.",
            "D.T*f=W is unchanged because D and f are unchanged; no additional full-frame or contact-state claim is made.",
        ],
        "input_sha256": {
            "prior_replay.py": sha(replay_path),
            "prior_assessment.json": sha(prior_assessment_path),
            "operators.npz": sha(operators_path),
            "B.npz": sha(COMP / "B.npz"),
            "row-identities.json": sha(COMP / "row-identities.json"),
            "response.json": sha(RUN / "response.json"),
            "model.dat": sha(RUN / "model.dat"),
            "model.json": sha(RUN / "model.json"),
            "model.inp": sha(RUN / "model.inp"),
            "model.dof": sha(OPERATOR_NATIVE / "model.dof"),
            "source-load-maps.json": sha(LOAD_MAPS),
        },
        "diagnostic_script_sha256": sha(Path(__file__).resolve()),
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
                       encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "max_rowwise_abs_Hsym_minus_H_times_f_mm": max_perturbation,
                      "max_raw_H_interval_ratio": max_raw_ratio,
                      "max_Hsym_interval_ratio": max_sym_ratio,
                      "Hsym_passes_original_q_interval_gate": sym_pass,
                      "output": str(OUTPUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
