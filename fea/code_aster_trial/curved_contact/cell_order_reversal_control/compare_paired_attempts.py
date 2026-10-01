#!/usr/bin/env python3
"""Compare the frozen curved-contact baseline and cell-order control outputs.

This is an offline diagnostic. It never invokes Code_Aster and never changes
either attempt's frozen inputs. Node-indexed JEU/CONT are deliberately not
treated as physical invariants because the v17.4 output path can overwrite a
shared node slot as it visits contact samples.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import check_curved_contact as tables  # noqa: E402


EVIDENCE_ROOT = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27"
DEFAULT_BASELINE = EVIDENCE_ROOT / "curved-contact-attempt03"
DEFAULT_CONTROL = EVIDENCE_ROOT / "curved-contact-cell-order-control-attempt01"
BASELINE_SOURCE = ROOT / "fea/code_aster_trial/curved_contact/native_input_v3"
CONTROL_SOURCE = HERE
EVALUATED_INST = tuple(float(value) for value in range(12))
ALL_INST = (-1.0, *EVALUATED_INST)
SLAVE_FACES = 95
EXPECTED_IMAGE = "simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5"
REQUIRED_FROZEN_FILES = {
    "curved_contact.comm", "curved_contact.export", "curved_contact.mail",
    "generate.py", "geometry-oracle.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vector_sum(rows: dict[str, dict[str, str]], components: tuple[str, str, str]):
    return tuple(math.fsum(tables.number(row, name) for row in rows.values())
                 for name in components)


def vector_add(left, right):
    return tuple(a + b for a, b in zip(left, right))


def vector_sub(left, right):
    return tuple(a - b for a, b in zip(left, right))


def vector_norm(vector) -> float:
    return math.sqrt(math.fsum(value * value for value in vector))


def json_vector(vector):
    return [float(value) for value in vector]


def same_sample_assignment(left: dict | None, right: dict | None) -> bool:
    if left is None or right is None:
        return left is right
    return (left["mesh_face"], left["auto_point_index_1based"]) == (
        right["mesh_face"], right["auto_point_index_1based"])


def expect(condition: bool, message: str):
    if not condition:
        raise ValueError(message)


def check_attempt_freeze(attempt: Path, name: str) -> dict:
    execution_path = attempt / "execution.json"
    freeze_path = attempt / "input-freeze.json"
    expect(execution_path.is_file(), f"{name}: missing execution.json")
    expect(freeze_path.is_file(), f"{name}: missing input-freeze.json")
    execution = json.loads(execution_path.read_text())
    freeze = json.loads(freeze_path.read_text())

    expect(execution.get("returncode") == 0, f"{name}: native attempt did not return zero")
    expect(execution.get("timed_out") is False, f"{name}: native attempt timed out")
    expect(execution.get("changed_frozen_inputs") == [],
           f"{name}: execution reported changed frozen inputs")
    expect(freeze.get("image") == EXPECTED_IMAGE,
           f"{name}: runtime image differs from the pinned Code_Aster image")
    inputs = freeze.get("input_sha256")
    expect(isinstance(inputs, dict), f"{name}: input-freeze.json lacks input_sha256")
    expect(REQUIRED_FROZEN_FILES.issubset(inputs),
           f"{name}: missing required frozen hash entries: {sorted(REQUIRED_FROZEN_FILES - set(inputs))}")

    checked = {}
    for filename, expected_hash in inputs.items():
        path = attempt / filename
        expect(path.is_file(), f"{name}: frozen input missing from attempt: {filename}")
        actual_hash = sha256(path)
        expect(actual_hash == expected_hash,
               f"{name}: frozen input changed after run: {filename} ({actual_hash} != {expected_hash})")
        checked[filename] = actual_hash
    return {
        "attempt_directory": str(attempt),
        "returncode": execution["returncode"],
        "timed_out": execution["timed_out"],
        "changed_frozen_inputs": execution["changed_frozen_inputs"],
        "elapsed_seconds": execution.get("elapsed_seconds"),
        "image": freeze["image"],
        "runner_sha256": freeze.get("runner_sha256"),
        "input_sha256_verified": checked,
    }


def normalized_oracle(oracle: dict) -> dict:
    result = copy.deepcopy(oracle)
    source = result["source"]
    source.pop("crop_mail_sha256", None)
    source.pop("cell_order_control", None)
    return result


def validate_inputs(baseline: Path, control: Path) -> dict:
    base_freeze = check_attempt_freeze(baseline, "baseline")
    ctrl_freeze = check_attempt_freeze(control, "cell-order control")
    base_json = json.loads((baseline / "input-freeze.json").read_text())
    ctrl_json = json.loads((control / "input-freeze.json").read_text())

    for filename in ("curved_contact.comm", "curved_contact.export", "generate.py"):
        expect(base_json["input_sha256"][filename] == ctrl_json["input_sha256"][filename],
               f"attempts do not have byte-identical {filename}")
    expect(base_json.get("image") == ctrl_json.get("image"),
           "attempts used different runtime images")
    expect(base_json.get("runner_sha256") == ctrl_json.get("runner_sha256"),
           "attempts used different runner scripts")

    # Pin both attempts to the immutable source-only fixtures, then prove the
    # exact record permutation independently of the copied control manifest.
    base_oracle_path = baseline / "geometry-oracle.json"
    ctrl_oracle_path = control / "geometry-oracle.json"
    base_oracle = tables.load_oracle(base_oracle_path, baseline / "curved_contact.mail")
    ctrl_oracle = tables.load_oracle(ctrl_oracle_path, control / "curved_contact.mail")
    expect(normalized_oracle(base_oracle) == normalized_oracle(ctrl_oracle),
           "baseline/control geometry oracle content differs beyond explicit order provenance")

    baseline_source_hash = sha256(BASELINE_SOURCE / "curved_contact.mail")
    control_source_hash = sha256(CONTROL_SOURCE / "curved_contact.mail")
    expect(sha256(baseline / "curved_contact.mail") == baseline_source_hash,
           "baseline attempt mesh differs from frozen native_input_v3")
    expect(sha256(control / "curved_contact.mail") == control_source_hash,
           "control attempt mesh differs from frozen source-only control")

    manifest_path = CONTROL_SOURCE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    base_manifest_hashes = manifest["baseline"]["file_sha256"]
    control_manifest_hashes = manifest["control"]["file_sha256"]
    expect(base_manifest_hashes["curved_contact.mail"] == baseline_source_hash,
           "control manifest baseline mail hash does not match native_input_v3")
    expect(control_manifest_hashes["curved_contact.mail"] == control_source_hash,
           "control manifest mail hash does not match source control mesh")
    expect(manifest["change_scope"]["sequence_change"]["record_count"] == SLAVE_FACES,
           "control manifest does not specify the expected 95 slave records")
    expect(manifest["change_scope"]["preflight_proofs"]["exact_reversal_proven"] is True,
           "source control preflight did not prove exact reversal")
    tables.prove_slave_cell_order_control(
        BASELINE_SOURCE / "curved_contact.mail",
        control / "curved_contact.mail",
        baseline_source_hash,
        SLAVE_FACES,
    )

    return {
        "both_native_attempts_completed": True,
        "frozen_input_hashes_unchanged": True,
        "same_comm_sha256": base_json["input_sha256"]["curved_contact.comm"],
        "same_export_sha256": base_json["input_sha256"]["curved_contact.export"],
        "same_generator_sha256": base_json["input_sha256"]["generate.py"],
        "same_pinned_image": base_json["image"],
        "same_runner_sha256": base_json["runner_sha256"],
        "baseline_mail_sha256": baseline_source_hash,
        "control_mail_sha256": control_source_hash,
        "exact_slave_record_order_reversal_proven": True,
        "slave_tria6_record_count": SLAVE_FACES,
        "master_record_sequence_unchanged": True,
        "coordinates_solids_connectivity_orientation_and_groups_unchanged": True,
        "geometry_oracle_numeric_content_unchanged": True,
        "baseline_attempt": base_freeze,
        "control_attempt": ctrl_freeze,
        "order_only_proof": {
            "source": str(BASELINE_SOURCE / "curved_contact.mail"),
            "control": str(control / "curved_contact.mail"),
            "method": "exact whole-line reversal of the first 95 SLAVE TRIA6 records; all surrounding mail lines and all remaining element records byte-identical",
            "manifest_sha256": sha256(manifest_path),
        },
    }


def read_group_mail(path: Path, group_keyword: str) -> dict[str, set[str]]:
    lines = path.read_text().splitlines()
    groups: dict[str, set[str]] = {}
    index = 0
    while index < len(lines):
        if lines[index].strip() != group_keyword:
            index += 1
            continue
        end = next((j for j in range(index + 1, len(lines))
                    if lines[j].strip() == "FINSF"), None)
        expect(end is not None, f"unterminated {group_keyword} section")
        tokens = " ".join(line.strip() for line in lines[index + 1:end]).split()
        expect(bool(tokens), f"empty {group_keyword} section")
        name, *members = tokens
        expect(name not in groups, f"duplicate {group_keyword} group {name}")
        groups[name] = set(members)
        index = end + 1
    return groups


def read_tria6_records(path: Path) -> list[tuple[str, tuple[str, ...]]]:
    lines = path.read_text().splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == "TRIA6"]
    expect(len(starts) == 1, f"{path}: expected exactly one TRIA6 section")
    start = starts[0] + 1
    end = next((i for i in range(start, len(lines)) if lines[i].strip() == "FINSF"), None)
    expect(end is not None, f"{path}: TRIA6 section lacks FINSF")
    records = []
    for line in lines[start:end]:
        fields = line.split()
        expect(len(fields) == 7, f"{path}: malformed TRIA6 record {line!r}")
        records.append((fields[0], tuple(fields[1:])))
    expect(len(records) == 183, f"{path}: expected 183 TRIA6 records, found {len(records)}")
    return records


def source_slot_map(mail_path: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    records = read_tria6_records(mail_path)
    groups = read_group_mail(mail_path, "GROUP_MA")
    slave_records = records[:SLAVE_FACES]
    master_records = records[SLAVE_FACES:]
    expect({label for label, _ in slave_records} == groups["SLAVE"],
           f"{mail_path}: first 95 TRIA6 rows do not equal SLAVE membership")
    expect({label for label, _ in master_records} == groups["MASTER"],
           f"{mail_path}: trailing TRIA6 rows do not equal MASTER membership")

    # In the audited v17.4 path, AUTO TRIA6 point iptm uses the matching local
    # connectivity slot. Contact output is written in source face/point order;
    # later visits overwrite earlier values for a shared node slot.
    slots: dict[str, dict] = {}
    visit_counts: dict[str, int] = {}
    for face_order, (face, connectivity) in enumerate(slave_records, start=1):
        for iptm in range(1, 7):
            node = connectivity[iptm - 1]
            visit_counts[node] = visit_counts.get(node, 0) + 1
            slots[node] = {
                "mesh_face": face,
                "face_order_1based": face_order,
                "auto_point_index_1based": iptm,
                "associated_local_connectivity_index_1based": iptm,
                "visit_count_for_output_slot": visit_counts[node],
            }
    return slots, {face: {"connectivity": list(nodes), "face_order_1based": i}
                   for i, (face, nodes) in enumerate(slave_records, start=1)}


def read_table(path: Path, required, oracle: dict, group: str, table_name: str):
    parsed = tables.parse_table(path, required)
    canonical = tables.canonicalize_nodes(parsed, oracle, table_name)
    grouped = tables.grouped(canonical)
    tables.assert_times_with_initial(grouped, table_name)
    expected_nodes = {item["output_node"] for item in oracle["node_groups"][group]}
    result = {}
    for inst in ALL_INST:
        rows = tables.keyed_rows(tables.rows_at(grouped, inst, table_name), expected_nodes,
                                 table_name, inst)
        result[inst] = rows
    return result, expected_nodes


def read_attempt_tables(attempt: Path, oracle: dict) -> dict:
    contact, slave_nodes = read_table(
        attempt / "CONTACT.csv", ("INST", "NOEUD", "RNX", "RNY", "RNZ"),
        oracle, "SNODE", "CONTACT")
    scut, scut_nodes = read_table(
        attempt / "SCUT.csv", ("INST", "NOEUD", "DX", "DY", "DZ"),
        oracle, "SCUT", "SCUT")
    mcut, mcut_nodes = read_table(
        attempt / "MCUT.csv", ("INST", "NOEUD", "DX", "DY", "DZ"),
        oracle, "MCUT", "MCUT")
    sdisp, disp_nodes = read_table(
        attempt / "SDISP.csv", ("INST", "NOEUD", "DX", "DY", "DZ"),
        oracle, "SNODE", "SDISP")
    expect(len(slave_nodes) == 218, f"{attempt}: expected 218 SNODE output nodes")
    expect(len(disp_nodes) == 218, f"{attempt}: expected 218 SDISP output nodes")
    expect(len(scut_nodes) == 110, f"{attempt}: expected 110 SCUT output nodes")
    expect(len(mcut_nodes) == 136, f"{attempt}: expected 136 MCUT output nodes")
    return {"CONTACT": contact, "SCUT": scut, "MCUT": mcut, "SDISP": sdisp,
            "node_sets": {"SNODE": slave_nodes, "SCUT": scut_nodes, "MCUT": mcut_nodes}}


def displacement_comparison(base_rows, ctrl_rows, baseline_slots, control_slots,
                            source_node_by_label, inst: float) -> dict:
    details = []
    norms = []
    for label in sorted(base_rows):
        base = tuple(tables.number(base_rows[label], component) for component in ("DX", "DY", "DZ"))
        ctrl = tuple(tables.number(ctrl_rows[label], component) for component in ("DX", "DY", "DZ"))
        delta = vector_sub(ctrl, base)
        norm = vector_norm(delta)
        norms.append(norm)
        base_slot = baseline_slots.get(label)
        ctrl_slot = control_slots.get(label)
        details.append({
            "output_node": label,
            "source_node": source_node_by_label[label],
            "baseline_displacement_mm": json_vector(base),
            "control_displacement_mm": json_vector(ctrl),
            "control_minus_baseline_mm": json_vector(delta),
            "delta_norm_mm": norm,
            "baseline_final_source_slot": base_slot,
            "control_final_source_slot": ctrl_slot,
            "sample_assignment_changed": not same_sample_assignment(base_slot, ctrl_slot),
            "traversal_ordinal_changed": (
                base_slot is not None and ctrl_slot is not None and
                base_slot["face_order_1based"] != ctrl_slot["face_order_1based"]
            ),
        })
    worst = max(details, key=lambda row: row["delta_norm_mm"])
    return {
        "node_count": len(details),
        "maximum_nodal_delta_norm_mm": max(norms),
        "rms_nodal_delta_norm_mm": math.sqrt(math.fsum(value * value for value in norms) / len(norms)),
        "mean_nodal_delta_norm_mm": math.fsum(norms) / len(norms),
        "worst_node": worst["output_node"],
        "worst_node_delta_norm_mm": worst["delta_norm_mm"],
        "values_by_node": details,
    }


def compare_state(inst: float, base, ctrl, baseline_slots, control_slots,
                  source_node_by_label: dict[str, int]) -> dict:
    contact_nodes = base["node_sets"]["SNODE"]
    rn_base = vector_sum(base["CONTACT"][inst], ("RNX", "RNY", "RNZ"))
    rn_ctrl = vector_sum(ctrl["CONTACT"][inst], ("RNX", "RNY", "RNZ"))
    rn_delta = vector_sub(rn_ctrl, rn_base)

    scut_base = vector_sum(base["SCUT"][inst], ("DX", "DY", "DZ"))
    scut_ctrl = vector_sum(ctrl["SCUT"][inst], ("DX", "DY", "DZ"))
    mcut_base = vector_sum(base["MCUT"][inst], ("DX", "DY", "DZ"))
    mcut_ctrl = vector_sum(ctrl["MCUT"][inst], ("DX", "DY", "DZ"))
    scut_delta = vector_sub(scut_ctrl, scut_base)
    mcut_delta = vector_sub(mcut_ctrl, mcut_base)
    pair_base = vector_add(scut_base, mcut_base)
    pair_ctrl = vector_add(scut_ctrl, mcut_ctrl)
    pair_delta = vector_sub(pair_ctrl, pair_base)

    largest_cut = max(vector_norm(scut_base), vector_norm(scut_ctrl),
                      vector_norm(mcut_base), vector_norm(mcut_ctrl))
    force_tol = max(0.05, 0.001 * largest_cut)
    scut_delta_norm = vector_norm(scut_delta)
    mcut_delta_norm = vector_norm(mcut_delta)
    pair_base_norm = vector_norm(pair_base)
    pair_ctrl_norm = vector_norm(pair_ctrl)
    cut_comparison_pass = scut_delta_norm <= force_tol and mcut_delta_norm <= force_tol
    pair_balance_pass = pair_base_norm <= force_tol and pair_ctrl_norm <= force_tol

    sdisp = displacement_comparison(
        base["SDISP"][inst], ctrl["SDISP"][inst], baseline_slots, control_slots,
        source_node_by_label, inst)
    expect(len(contact_nodes) == 218 and sdisp["node_count"] == 218,
           f"INST={inst:g}: contact or displacement SNODE set is not 218 nodes")

    return {
        "inst": inst,
        "state_type": "evaluated" if inst >= 0 else "initial unevaluated record; omitted from paired value comparisons",
        "contact_resultant_rn_full_vector_sum_n": {
            "baseline": json_vector(rn_base),
            "control": json_vector(rn_ctrl),
            "control_minus_baseline": json_vector(rn_delta),
            "baseline_norm_n": vector_norm(rn_base),
            "control_norm_n": vector_norm(rn_ctrl),
            "delta_norm_n": vector_norm(rn_delta),
            "node_count_each": len(contact_nodes),
            "acceptance_threshold_applied": False,
            "note": "Descriptive only; no RN-to-cut gate is applied by this comparator.",
        },
        "cut_resultants_n": {
            "SCUT": {
                "baseline": json_vector(scut_base), "control": json_vector(scut_ctrl),
                "control_minus_baseline": json_vector(scut_delta),
                "delta_norm_n": scut_delta_norm,
            },
            "MCUT": {
                "baseline": json_vector(mcut_base), "control": json_vector(mcut_ctrl),
                "control_minus_baseline": json_vector(mcut_delta),
                "delta_norm_n": mcut_delta_norm,
            },
            "pair_balance_SCUT_plus_MCUT": {
                "baseline": json_vector(pair_base), "control": json_vector(pair_ctrl),
                "control_minus_baseline": json_vector(pair_delta),
                "baseline_norm_n": pair_base_norm,
                "control_norm_n": pair_ctrl_norm,
                "delta_norm_n": vector_norm(pair_delta),
            },
            "SCUT_node_count_each": len(base["node_sets"]["SCUT"]),
            "MCUT_node_count_each": len(base["node_sets"]["MCUT"]),
            "frozen_force_balance_tolerance_n": force_tol,
            "tolerance_definition": "max(0.05 N, 0.001 * largest norm among both attempts' SCUT and MCUT resultants at this INST)",
            "SCUT_order_delta_within_tolerance": scut_delta_norm <= force_tol,
            "MCUT_order_delta_within_tolerance": mcut_delta_norm <= force_tol,
            "baseline_pair_balance_within_tolerance": pair_base_norm <= force_tol,
            "control_pair_balance_within_tolerance": pair_ctrl_norm <= force_tol,
            "pair_balance_delta_within_tolerance_descriptive_only": vector_norm(pair_delta) <= force_tol,
            "cut_resultant_order_invariance": "PASS" if cut_comparison_pass else "FAIL",
            "pair_balance_screen": "PASS" if pair_balance_pass else "FAIL",
            "combined_cut_diagnostic": "PASS" if cut_comparison_pass and pair_balance_pass else "FAIL",
            "scope_note": "Tolerance applies only to SCUT/MCUT resultant order invariance and each run's cut action/reaction pair balance; it is not an RN-vs-cut acceptance test.",
        },
        "SDISP_node_values_mm": sdisp,
    }


def source_slot_mapping(baseline_mail: Path, control_mail: Path, oracle: dict) -> dict:
    baseline_by_node, _ = source_slot_map(baseline_mail)
    control_by_node, _ = source_slot_map(control_mail)
    source_node_by_label = {
        item["output_node"]: int(item["source_node"])
        for item in oracle["node_groups"]["SNODE"]
    }
    expected_labels = set(source_node_by_label)
    expect(set(baseline_by_node) == expected_labels,
           "baseline source AUTO slots do not cover exactly the 218 oracle SNODE labels")
    expect(set(control_by_node) == expected_labels,
           "control source AUTO slots do not cover exactly the 218 oracle SNODE labels")
    changed = []
    traversal_changed = []
    for label in sorted(expected_labels):
        baseline_assignment = (baseline_by_node[label]["mesh_face"],
                              baseline_by_node[label]["auto_point_index_1based"])
        control_assignment = (control_by_node[label]["mesh_face"],
                              control_by_node[label]["auto_point_index_1based"])
        if baseline_assignment != control_assignment:
            changed.append({
                "output_node": label,
                "source_node": source_node_by_label[label],
                "baseline_final_source_slot": baseline_by_node[label],
                "control_final_source_slot": control_by_node[label],
                "sample_assignment_changed": True,
                "traversal_ordinal_changed": (
                    baseline_by_node[label]["face_order_1based"] !=
                    control_by_node[label]["face_order_1based"]
                ),
            })
        if baseline_by_node[label]["face_order_1based"] != control_by_node[label]["face_order_1based"]:
            traversal_changed.append(label)
    return {
        "source_basis": "Code_Aster upstream 17.4.0 source tag, as audited in curved-contact-attempt03/parent-contact-sample-gap-review.json; runtime binary byte identity is not established.",
        "method": "For each SLAVE face in mesh-record order, visit AUTO TRIA6 iptm=1..6 and associate it with local connectivity slot iptm; the final visit for a node is the last-write source slot reported here.",
        "references": {
            "AUTO_TRIA6_six_point_rule": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_util/mmgaus.F90#L155",
            "AUTO_rule_selection_for_TR6": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/algorith/mmelin.F90#L57",
            "integration_point_to_node_mapping": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_algo/mmapma.F90#L98",
            "AUTO_point_to_connectivity_mapping": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/algorith/mmpnoe.F90#L65",
            "contact_result_writer": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_algo/mmmres.F90#L200",
        },
        "audit_artifact": "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/curved-contact-attempt03/parent-contact-sample-gap-review.json",
        "output_node_count": len(expected_labels),
        "changed_sample_assignment_count": len(changed),
        "unchanged_sample_assignment_count": len(expected_labels) - len(changed),
        "changed_sample_assignments_by_output_node": changed,
        "changed_traversal_ordinal_count": len(traversal_changed),
        "changed_traversal_ordinal_output_nodes": traversal_changed,
        "all_slots_by_output_node": [
            {
                "output_node": label,
                "source_node": source_node_by_label[label],
                "baseline_final_source_slot": baseline_by_node[label],
                "control_final_source_slot": control_by_node[label],
                "sample_assignment_changed": not same_sample_assignment(
                    baseline_by_node[label], control_by_node[label]),
                "traversal_ordinal_changed": (
                    baseline_by_node[label]["face_order_1based"] !=
                    control_by_node[label]["face_order_1based"]
                ),
            }
            for label in sorted(expected_labels)
        ],
        "interpretation_limit": "This predicts which quadrature sample is associated with each saved nodal output slot under the audited source iteration order. It does not identify which duplicate sample generated a particular saved force/status/gap value, nor establish runtime binary identity.",
    }, source_node_by_label


def compare(baseline: Path, control: Path) -> dict:
    baseline = baseline.resolve()
    control = control.resolve()
    provenance = validate_inputs(baseline, control)
    base_oracle = json.loads((baseline / "geometry-oracle.json").read_text())
    ctrl_oracle = json.loads((control / "geometry-oracle.json").read_text())
    base_tables = read_attempt_tables(baseline, base_oracle)
    ctrl_tables = read_attempt_tables(control, ctrl_oracle)
    for table_name in ("SNODE", "SCUT", "MCUT"):
        expect(base_tables["node_sets"][table_name] == ctrl_tables["node_sets"][table_name],
               f"{table_name} output membership differs between attempts")

    slots, source_node_by_label = source_slot_mapping(
        baseline / "curved_contact.mail", control / "curved_contact.mail", base_oracle)
    baseline_slots, _ = source_slot_map(baseline / "curved_contact.mail")
    control_slots, _ = source_slot_map(control / "curved_contact.mail")
    states = [compare_state(inst, base_tables, ctrl_tables,
                            baseline_slots, control_slots,
                            source_node_by_label)
              for inst in EVALUATED_INST]
    initial_sdisp = displacement_comparison(
        base_tables["SDISP"][-1.0], ctrl_tables["SDISP"][-1.0],
        baseline_slots, control_slots, source_node_by_label, -1.0)
    all_cut_pass = all(state["cut_resultants_n"]["combined_cut_diagnostic"] == "PASS"
                       for state in states)
    return {
        "scope": "Offline paired-output order-control diagnostic only; no solver invocation and no contact-method, mechanical, or joint acceptance.",
        "paired_attempt_provenance": provenance,
        "table_coverage": {
            "required_instants": list(ALL_INST),
            "compared_evaluated_instants": list(EVALUATED_INST),
            "initial_minus_one_record": "Coverage checked in each table. Unevaluated RN/SCUT/MCUT values are excluded; the valid zero-motion SDISP vectors are compared separately below.",
            "CONTACT_and_SDISP_nodes_per_evaluated_state": 218,
            "SCUT_nodes_per_evaluated_state": 110,
            "MCUT_nodes_per_evaluated_state": 136,
            "node_indexed_JEU_CONT_comparison": "NOT_PERFORMED; node slots can receive different final AUTO samples after the face order reversal.",
        },
        "initial_minus_one_SDISP_comparison_mm": initial_sdisp,
        "output_slot_reassignment": slots,
        "state_comparisons": states,
        "overall_cut_resultant_order_invariance": "PASS" if all_cut_pass else "FAIL",
        "overall_diagnostic": "No RN-vs-cut test is made. A cut-only PASS does not qualify curved contact or the broader joint; a cut-only FAIL is evidence of result sensitivity to this source-order perturbation.",
        "script_sha256": sha256(Path(__file__).resolve()),
        "source_audit_script_sha256": sha256(HERE.parent / "audit_contact_samples.py"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-attempt", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--control-attempt", type=Path, default=DEFAULT_CONTROL)
    parser.add_argument("--json", type=Path,
                        help="output report path (default: paired-result-comparison.json in the control attempt)")
    args = parser.parse_args()
    report = compare(args.baseline_attempt, args.control_attempt)
    output = args.json or args.control_attempt / "paired-result-comparison.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    for state in report["state_comparisons"]:
        cuts = state["cut_resultants_n"]
        sdisp = state["SDISP_node_values_mm"]
        rn = state["contact_resultant_rn_full_vector_sum_n"]
        print(f"INST={state['inst']:g}: cut={cuts['combined_cut_diagnostic']}, "
              f"tol={cuts['frozen_force_balance_tolerance_n']:.6g} N, "
              f"|dSCUT|={cuts['SCUT']['delta_norm_n']:.6g} N, "
              f"|dMCUT|={cuts['MCUT']['delta_norm_n']:.6g} N, "
              f"pair norms={cuts['pair_balance_SCUT_plus_MCUT']['baseline_norm_n']:.3g}/"
              f"{cuts['pair_balance_SCUT_plus_MCUT']['control_norm_n']:.3g} N, "
              f"|dRN|={rn['delta_norm_n']:.6g} N (descriptive), "
              f"max |dSDISP|={sdisp['maximum_nodal_delta_norm_mm']:.6g} mm")
    print(f"Final sample assignments changed: {report['output_slot_reassignment']['changed_sample_assignment_count']}/218; "
          f"traversal ordinals changed: {report['output_slot_reassignment']['changed_traversal_ordinal_count']}/218")
    print(f"Cut-resultant order invariance: {report['overall_cut_resultant_order_invariance']}")
    print(f"Wrote {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
