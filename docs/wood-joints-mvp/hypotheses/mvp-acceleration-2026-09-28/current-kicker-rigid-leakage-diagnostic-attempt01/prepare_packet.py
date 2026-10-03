#!/usr/bin/env python3
"""Prepare, but do not solve, kicker_left's exact stopped 16-column packet."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
PARENT = BASE / "current-frame-connector-compliance-attempt02"
NATIVE = BASE / "current-frame-pure-solid-matrix-export-native-attempt01"
BODY_AUDIT = BASE / "current-frame-body-elastic-positivity-audit-attempt01"
PROJECTION = BASE / "current-frame-physical-connector-projection-contract-attempt01"
METHOD = BASE / "current-frame-free-body-condensation-preflight-attempt01"
PARSER_PATH = BASE / "current-frame-pure-solid-export-assessment-method-attempt01" / "assess_matrixstorage.py"
MODEL_PATH = BASE / "current-springa-frame-input-adapter-attempt01" / "a12-rear" / "model.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(value)
    return value


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def build() -> dict:
    if (HERE / "packet.json").exists():
        raise ValueError("packet output already exists; preserve it and use a new attempt")

    parent_inputs = json.loads((PARENT / "inputs.json").read_text())
    parent_assessment = json.loads((PARENT / "assessment.json").read_text())
    if parent_assessment.get("status") != "STOP_CONNECTOR_COMPLIANCE_NUMERICAL_GATE":
        raise ValueError("parent attempt02 is not the preserved stopped result")
    stop = parent_assessment.get("stopping_gate", {})
    if stop.get("body") != "kicker_left" or stop.get("basis") != "interface columns 16:32":
        raise ValueError("parent stopped case differs from requested kicker_left chunk")
    for rel, expected in parent_inputs["source_sha256"].items():
        if sha(ROOT / rel) != expected:
            raise ValueError(f"parent input changed: {rel}")

    parser = module(PARSER_PATH, "kicker_packet_parser")
    helper = module(METHOD / "condensation.py", "kicker_packet_helper")
    authenticated = module(NATIVE / "assess.py", "kicker_packet_authenticated_export")
    if authenticated.assess() != json.loads((NATIVE / "assessment.json").read_text()):
        raise ValueError("authenticated native operator export does not replay")
    source = parser.load_frame_source_model(MODEL_PATH)
    labels = parser.parse_dof_file(NATIVE / "model.dof")
    parser.require_dof_bijection(labels, source["physical_nodes"], 37647)
    owners = np.array([source["owner_by_node"][node] for node, _ in labels])
    row_for = {label: i for i, label in enumerate(labels)}
    parsed = parser.parse_upper_triangle_file(
        NATIVE / "model.sti", len(labels),
        owner_by_row=owners, owner_names=list(source["bodies"]),
    )
    parser.require_no_cross_body_coupling(parsed)
    K_frame = parsed["matrix"]

    contract = json.loads((PROJECTION / "projection-contract.json").read_text())
    index_map = json.loads((PROJECTION / "physical-index-map.json").read_text())
    rows = contract["rows"]
    if len(rows) != 1840 or len(index_map) != 12549:
        raise ValueError("source connector projection dimensions changed")
    bi, bj, bv = [], [], []
    for i, record in enumerate(rows):
        for term in record["physical_sparse_row"]:
            coordinate = int(term["coordinate_index"])
            node = int(index_map[coordinate // 3]["node"])
            native_row = row_for[(node, coordinate % 3 + 1)]
            bi.append(i)
            bj.append(native_row)
            bv.append(term["coefficient"])
    B = sp.csr_matrix((bv, (bi, bj)), shape=(1840, len(labels)))
    if B.nnz != 62607:
        raise ValueError("projection row map nnz changed")

    bodies = list(source["bodies"])
    body_id = bodies.index("kicker_left")
    dofs = np.flatnonzero(owners == body_id)
    labels_body = [labels[int(i)] for i in dofs]
    K = K_frame[dofs, :][:, dofs].tocsr()
    _, R, Q = helper.rigid_basis(labels_body, source["coordinates"], 1000.0)
    Bb_all = B[:, dofs].tocsr()
    active_rows = np.flatnonzero(np.diff(Bb_all.indptr))
    Bb = Bb_all[active_rows, :].tocsr()
    if len(dofs) != 1515 or len(active_rows) < 32:
        raise ValueError("kicker_left body or active row dimensions differ")
    selection = np.arange(16, 32)
    selected_contract_rows = active_rows[selection]
    raw = Bb[selection, :].T.toarray()
    projected = raw - Q @ (Q.T @ raw)

    # Diagnose the original physical operator and projected load without a
    # factorization or solve. Long-double products expose rigid leakage.
    K_ld = K.astype(np.longdouble)
    R_ld = np.asarray(R, dtype=np.longdouble)
    raw_ld = np.asarray(raw, dtype=np.longdouble)
    projected_ld = np.asarray(projected, dtype=np.longdouble)
    KR_ld = K_ld @ R_ld
    RKR_ld = R_ld.T @ KR_ld
    RtP_ld = R_ld.T @ projected_ld
    row_norms = np.asarray(np.abs(K).sum(axis=1)).reshape(-1)
    gamma = float(np.max(row_norms))
    rigid_rel = float(
        np.max(np.abs(KR_ld))
        / (np.longdouble(gamma) * np.max(np.abs(R_ld)))
    )
    row_records = []
    for j, row_position in enumerate(selected_contract_rows):
        record = rows[int(row_position)]
        row_records.append({
            "active_chunk_column": int(j),
            "source_row_position": int(row_position),
            "row_id": record.get("row_id"),
            "source_group": record.get("source_group"),
            "source_element": record.get("source_element"),
            "source_inventory_row_index": record.get("source_inventory_row_index"),
            "family": record.get("family"),
        })

    sp.save_npz(HERE / "body-K.npz", K)
    np.savez_compressed(
        HERE / "basis.npz", R=R, Q=Q, raw=raw, projected=projected,
        active_rows=active_rows, selected_contract_rows=selected_contract_rows,
        selected_body_dof_indices=dofs,
    )
    write(HERE / "source-rows.json", row_records)
    report = {
        "schema": "kicker_left_stopped_chunk_equation_diagnostic_inputs/v1",
        "status": "PASS_EXACT_KICKER_CHUNK_PREPARED_NO_SOLVE",
        "parent_attempt02_assessment_sha256": sha(PARENT / "assessment.json"),
        "parent_attempt02_inputs_sha256": sha(PARENT / "inputs.json"),
        "body": "kicker_left",
        "physical_dofs": int(len(dofs)),
        "body_K_nnz": int(K.nnz),
        "active_connector_rows": int(len(active_rows)),
        "chunk_active_column_indices": [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
        "source_rows_sha256": sha(HERE / "source-rows.json"),
        "source_row_identities": row_records,
        "raw_wrench_Rt_raw_N": (R.T @ raw).tolist(),
        "projected_wrench_Rt_projected_N": np.asarray(R_ld.T @ projected_ld, dtype=np.float64).tolist(),
        "max_projected_rigid_wrench_abs_N": float(np.max(np.abs(R_ld.T @ projected_ld))),
        "K_rigid_residual_relative_inf": rigid_rel,
        "gamma_inf_N_per_mm": gamma,
        "max_abs_KR_N_per_mm": float(np.max(np.abs(KR_ld))),
        "R_T_K_R_N_per_mm": np.asarray(RKR_ld, dtype=np.float64).tolist(),
        "body_K_sha256": sha(HERE / "body-K.npz"),
        "basis_sha256": sha(HERE / "basis.npz"),
        "native_launch": False,
        "factorization_or_solve": False,
        "full_compliance_computed": False,
        "mechanical_acceptance": False,
    }
    write(HERE / "packet.json", report)
    return report


if __name__ == "__main__":
    report = build()
    print(report["status"])
