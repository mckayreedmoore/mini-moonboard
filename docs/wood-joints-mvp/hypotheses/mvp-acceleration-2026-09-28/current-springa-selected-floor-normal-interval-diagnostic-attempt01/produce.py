#!/usr/bin/env python3
"""Produce source-bound all-100 floor-normal interval diagnostics.

This is a read-only consumer of two already-terminal selected-floor responses.
It checks normal SPRINGA constitutive intervals for every source normal and
does not recover physical connection demands or launch CalculiX.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
METHOD_DIR = SERIES / "current-springa-zero-u-token-response-audit-attempt01"
METHOD_WRAPPER = METHOD_DIR / "response_audit.py"
METHOD_STABLE = METHOD_DIR / "stable_response_audit.py"
METHOD_REPLAY = METHOD_DIR / "zero_u_token_replay.json"
METHOD_REPLAY_PRODUCER = METHOD_DIR / "replay_zero_u_tokens.py"
METHOD_README = METHOD_DIR / "README.md"

METHOD_PINS = {
    METHOD_WRAPPER: "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
    METHOD_STABLE: "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    METHOD_REPLAY: "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1",
    METHOD_REPLAY_PRODUCER: "6b49312429c78e04d0a70a7a428382028ac9e75ab01a69b53271d9feca91bd32",
    METHOD_README: "ef2c8d33ac9e48566c8b5c96f8ae4a0fa0216ff00fa1bc3aa6d7e3c0f76f0d49",
}

CASE_PINS: dict[str, dict[str, str]] = {
    "k12-rear": {
        "model.json": "efb749f0349b23bf5c9dc3fd1cb608f90ee5e519ec06e268ad86280614a80921",
        "model.inp": "ff515e7006fc223e89df245f7bf31cda337611ac75c981df8d1b7cafebf0d691",
        "model.dat": "9da796a6b107d8100392f5113e484085b9196242efba96e48b504d174eeb302d",
        "execution.json": "376a204fc9201b1c90e9263a7cdd9ef8f2646c103f60f866efe90c12b710bb1e",
        "freeze.json": "d41775f65becd71732016b451f9db4e9c7a45b9cd8f8b043a4d517bb8394f83b",
        "authorization.json": "87460cce9b42ac4b1c1f1cbafb76a410bcccf37c33d27862f3d608dfbe26bd4d",
        "case-context.json": "6aba84bbb4ae289000afe10ebccefaa42cadc37bf3b3c69aad620f6b9c287bb6",
        "parent-serialized-input-audit.json": "77c458b8816b64ee705defdda15fb109f05ac05a91fbafac8dea7a2689d3405d",
        "parent-terminal-assessment.json": "b038a9c68062345311e6d2934874c2ac6c8f7ce4bf7e139722f5cd2014de8318",
        "native.stdout": "196259574a4f53c4dbcf39572272e0c68aa88a473cc61a9aa301f584d68368d8",
        "native.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    },
    "a1-rear": {
        "model.json": "3cf43f58ea10027fa58618bc9d69536b67664f8780e457d1cc9451bc9411588e",
        "model.inp": "91e7c87b67ab53517fb774c119ae6b4f52ff15a5c0f0ca73c8b5a4cae6bf8610",
        "model.dat": "22caf3925934fae1d9111374d25e67b7e2741ad9b2e603494b0ba08a4d59dbcb",
        "execution.json": "a8f2df6249f7d04a0da85b2697ae6b6ff55b2984e940b36e313202d471cbe8ff",
        "freeze.json": "2139179dc9672aaf50db330d84a269b2881faab1c29058469873d1cc491e2d6b",
        "authorization.json": "ab96a07cb7178a4e23337591823920cdb03212ce23f37a9d44d850e8994273db",
        "case-context.json": "d816f18a9c444c058944966eb999d862625851ee10512d0ef106bb4b6dac50f0",
        "parent-serialized-input-audit.json": "15baaf613eac54e561f794b5f89876c082b0583115ffa812dca25439890fb0d7",
        "parent-terminal-assessment.json": "c0d9aac117fc17466e90df85225827a46a58d96ad508b4a212978bb87f012d8e",
        "native.stdout": "cae655152bf512511be21da7fadcce7f7d302e2a942ac2e664ad37e8378627e6",
        "native.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    },
}

EXPECTED_REJECTIONS = {
    "k12-rear": "Inactive floor normal is not strictly separated with zero endpoint RF: SPR1074",
    "a1-rear": "Inactive floor normal is not strictly separated with zero endpoint RF: SPR1131",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_method():
    require(sha(METHOD_WRAPPER) == METHOD_PINS[METHOD_WRAPPER],
            "Pinned zero-U case-bound response wrapper changed")
    require(sha(METHOD_STABLE) == METHOD_PINS[METHOD_STABLE],
            "Pinned zero-U stable parser/auditor changed")
    spec = importlib.util.spec_from_file_location("pinned_zero_u_response_audit", METHOD_WRAPPER)
    require(spec is not None and spec.loader is not None, "Cannot load pinned zero-U response wrapper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def interval(center: float, radius: float) -> list[float]:
    require(math.isfinite(center) and math.isfinite(radius) and radius >= 0.0,
            "Nonfinite interval center/radius or negative radius")
    return [center - radius, center + radius]


def classify_normal(binding: dict[str, Any], source: dict[str, Any], state: dict[str, Any],
                    emitted_nodes: dict[int, np.ndarray], method: Any) -> dict[str, Any]:
    _, _, check = method.audit_springa(binding, source, state, emitted_nodes)
    q = float(check["q_relative_projection_mm"])
    q_radius = float(check["q_relative_projection_radius_mm"])
    elongation = float(check["geometric_spring_elongation_mm"])
    q_node, ground = map(int, binding["springa_nodes"])
    q_vector = np.asarray(state["u"][q_node], dtype=float) - np.asarray(state["u"][ground], dtype=float)
    q_vector_radius = (np.asarray(state["u_radius"][q_node], dtype=float)
                       + np.asarray(state["u_radius"][ground], dtype=float))
    current_vector = (np.asarray(emitted_nodes[q_node], dtype=float)
                      - np.asarray(emitted_nodes[ground], dtype=float) + q_vector)
    current_length = float(np.linalg.norm(current_vector))
    require(current_length > 0.0, f"Zero/reversed normal carrier geometry at {binding['group']}")
    current_axis = current_vector / current_length
    geometry_guard = float(check["geometric_length_subtraction_arithmetic_guard_mm"])
    geometry_radius = float(np.abs(current_axis) @ q_vector_radius) + geometry_guard
    q_interval = interval(q, q_radius)
    geometry_interval = interval(elongation, geometry_radius)
    table_interval = [float(value) for value in check["native_table_force_interval_N"]]

    internal = float(check["native_endpoint_internal_force_N"])
    internal_radius = float(check["native_endpoint_internal_radius_N"])
    internal_interval = interval(internal, internal_radius)
    ground_internal = float(check["native_ground_rf_projected_N"])
    ground_radius = float(check["native_ground_rf_radius_N"])
    ground_interval = interval(ground_internal, ground_radius)
    rf_first = np.asarray(state["rf"][q_node], dtype=float)
    rf_first_radius = np.asarray(state["rf_radius"][q_node], dtype=float)
    rf_ground = np.asarray(state["rf"][ground], dtype=float)
    rf_ground_radius = np.asarray(state["rf_radius"][ground], dtype=float)
    force_guard = float(check["native_endpoint_force_arithmetic_guard_N"])
    endpoint_rf_contains_zero = bool(np.all(np.abs(rf_first) <= rf_first_radius + force_guard)
                                     and np.all(np.abs(rf_ground) <= rf_ground_radius + force_guard))

    strictly_positive = bool(
        q_interval[0] > 0.0
        and geometry_interval[0] > 0.0
        and table_interval[0] > 0.0
        and internal_interval[0] > 0.0
        and bool(check["native_endpoint_action_reaction_passed"])
    )
    strictly_separated = bool(
        q_interval[1] < 0.0
        and geometry_interval[1] < 0.0
        and table_interval == [0.0, 0.0]
        and endpoint_rf_contains_zero
        and bool(check["native_endpoint_action_reaction_passed"])
    )
    if strictly_positive:
        classification = "STRICT_POSITIVE_BEARING"
    elif strictly_separated:
        classification = "STRICTLY_SEPARATED"
    else:
        classification = "UNRESOLVED_INTERVALS"

    return {
        "source_group": str(binding["group"]),
        "source_row_id": str(binding["source_row_id"]),
        "source_inventory_row_index": int(binding["source_inventory_row_index"]),
        "normal_cell": str(binding["name"]),
        "physical_owner": source["physical_owner"]["first"],
        "source_law": str(source["intended_law"]),
        "classification": classification,
        "strictly_positive_bearing": strictly_positive,
        "strictly_separated": strictly_separated,
        "projected_q_mm": q,
        "projected_q_rounding_radius_mm": q_radius,
        "projected_q_interval_mm": q_interval,
        "geometric_spring_elongation_mm": elongation,
        "geometric_spring_elongation_radius_mm": geometry_radius,
        "geometric_spring_elongation_interval_mm": geometry_interval,
        "geometric_length_subtraction_arithmetic_guard_mm": geometry_guard,
        "native_table_force_N_from_actual_dd_minus_dd0": float(
            check["native_table_force_N_from_actual_dd_minus_dd0"]),
        "native_table_force_interval_N": table_interval,
        "native_endpoint_internal_force_N": internal,
        "native_endpoint_internal_radius_N": internal_radius,
        "native_endpoint_internal_interval_N": internal_interval,
        "native_ground_rf_projected_N": ground_internal,
        "native_ground_rf_radius_N": ground_radius,
        "native_ground_rf_interval_N": ground_interval,
        "q_endpoint_rf_N": rf_first.tolist(),
        "q_endpoint_rf_rounding_radius_N": rf_first_radius.tolist(),
        "q_endpoint_rf_component_intervals_N": [
            interval(float(value), float(radius))
            for value, radius in zip(rf_first, rf_first_radius, strict=True)
        ],
        "numerical_ground_rf_N": rf_ground.tolist(),
        "numerical_ground_rf_rounding_radius_N": rf_ground_radius.tolist(),
        "numerical_ground_rf_component_intervals_N": [
            interval(float(value), float(radius))
            for value, radius in zip(rf_ground, rf_ground_radius, strict=True)
        ],
        "endpoint_rf_intervals_all_components_contain_zero": endpoint_rf_contains_zero,
        "endpoint_action_reaction_passed": bool(check["native_endpoint_action_reaction_passed"]),
        "table_force_interval_intersects_native_endpoint_rf": bool(
            check["table_force_interval_intersects_native_rf"]),
        "inside_table_domain_including_rounding": bool(check["inside_table_domain_including_rounding"]),
        "source_group_selected_in_proposed_input": False,
        "numerical_ground_rf_is_not_a_physical_support_reaction": True,
    }


def produce_case(case_id: str, method: Any) -> dict[str, Any]:
    packet = SERIES / f"current-springa-selected-floor-{case_id}-attempt01"
    expected = CASE_PINS[case_id]
    for filename, digest in expected.items():
        path = packet / filename
        require(path.is_file() and sha(path) == digest,
                f"{case_id} source pin mismatch: {filename}")

    record = load(packet / "model.json")
    deck = (packet / "model.inp").read_text()
    data = (packet / "model.dat").read_text(errors="replace")
    context = load(packet / "case-context.json")
    execution = load(packet / "execution.json")
    authorization = load(packet / "authorization.json")
    input_audit = load(packet / "parent-serialized-input-audit.json")
    terminal = load(packet / "parent-terminal-assessment.json")

    require(context.get("case_id") == case_id, f"{case_id} explicit context identity changed")
    require(input_audit.get("status") == "PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT"
            and input_audit.get("case_id") == case_id
            and input_audit.get("proposed_branch_accepted") is False
            and input_audit.get("corner_demands_usable") is False,
            f"{case_id} parent serialized-input audit is not the expected rejected proposal")
    require(terminal.get("status") == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
            and terminal.get("case_id") == case_id
            and terminal.get("strict_response_exception") == EXPECTED_REJECTIONS[case_id]
            and terminal.get("container_confirmed_terminal") is True
            and terminal.get("native_returncode") == 0
            and terminal.get("corner_demands_usable") is False
            and terminal.get("joint_accepted") is False
            and terminal.get("physical_failure_inferred") is False,
            f"{case_id} terminal assessment is not the expected rejected full-step response")
    require(terminal.get("zero_u_representation_auditor_sha256") == METHOD_PINS[METHOD_WRAPPER],
            f"{case_id} terminal record does not name the pinned zero-U parser wrapper")
    terminal_source_pins = terminal.get("sources_sha256", {})
    for name in ("model.json", "model.inp", "model.dat", "execution.json", "case-context.json"):
        require(terminal_source_pins.get(name) == expected[name],
                f"{case_id} parent terminal assessment does not bind {name}")
    require(authorization.get("input_freeze_sha256") == expected["freeze.json"]
            and authorization.get("native_execution_authorized") is True
            and authorization.get("mechanical_acceptance") is False,
            f"{case_id} authorization is not bound to the exact input freeze")
    require(execution.get("native_solve_executed") is True
            and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True,
            f"{case_id} terminal native execution is not successful")

    contract = method._validate_model(record, deck, context)
    run_validation = method._validate_execution(
        packet / "model.json", packet / "model.dat", packet / "model.inp",
        packet / "execution.json", data, context,
    )
    parsed = method.parse_native_blocks(data)
    require(len(parsed) == 7, f"{case_id} DAT does not contain all seven U/RF increments")
    expected_nodes = set(map(int, record["nodes"]))
    times = sorted(parsed)
    factors = [float(method.load_scale(time, contract["total_time"])) for time in times]
    require(all(set(state["u"]) == expected_nodes and set(state["rf"]) == expected_nodes
                for state in parsed.values()), f"{case_id} U/RF node inventory is incomplete")
    require(all(b > a for a, b in zip(times, times[1:]))
            and math.isclose(factors[-1], 1.0, rel_tol=0.0, abs_tol=1.0e-12),
            f"{case_id} response is not monotonically printed through full load factor 1")

    source_by_group = contract["source_by_group"]
    source_normals = {
        str(row["group"]): row
        for row in contract["source_rows"]
        if row.get("role") == "floor_normal" and row.get("intended_law") == "compression_only"
    }
    bindings = {
        str(binding["group"]): binding
        for binding in contract["bindings"]
        if str(binding["group"]) in source_normals
    }
    require(len(source_normals) == len(bindings) == 100,
            f"{case_id} source inventory does not have exactly 100 bound floor normals")
    selected = set(map(str, contract["selected_cells"]))
    inactive = set(map(str, contract["inactive_cells"]))
    require(len(selected) + len(inactive) == 100 and selected.isdisjoint(inactive),
            f"{case_id} selected/inactive input branch does not partition the 100 normals")

    states = []
    bearing_sets = []
    for time, factor in zip(times, factors, strict=True):
        state = parsed[time]
        rows = []
        for group in sorted(source_normals, key=lambda value: int(value.removeprefix("SPR"))):
            source = source_normals[group]
            binding = bindings[group]
            require(group in source_by_group, f"{case_id} normal source disappeared: {group}")
            row = classify_normal(binding, source, state, contract["emitted_nodes"], method)
            row["source_group_selected_in_proposed_input"] = row["normal_cell"] in selected
            row["input_mask_compatibility"] = (
                "PROPOSED_BEARING_OBSERVED_STRICTLY_SEPARATED"
                if row["source_group_selected_in_proposed_input"] and row["strictly_separated"]
                else "PROPOSED_INACTIVE_OBSERVED_STRICTLY_BEARING"
                if not row["source_group_selected_in_proposed_input"] and row["strictly_positive_bearing"]
                else "PROPOSED_BEARING_INTERVAL_UNRESOLVED"
                if row["source_group_selected_in_proposed_input"]
                and row["classification"] == "UNRESOLVED_INTERVALS"
                else "PROPOSED_INACTIVE_INTERVAL_UNRESOLVED"
                if not row["source_group_selected_in_proposed_input"]
                and row["classification"] == "UNRESOLVED_INTERVALS"
                else "CONSISTENT_WITH_PROPOSED_BRANCH"
            )
            rows.append(row)
        require(len(rows) == 100, f"{case_id} time {time} is not full 100-normal coverage")
        bearing = {row["normal_cell"] for row in rows if row["strictly_positive_bearing"]}
        separated = {row["normal_cell"] for row in rows if row["strictly_separated"]}
        unresolved = {row["normal_cell"] for row in rows if row["classification"] == "UNRESOLVED_INTERVALS"}
        require(len(bearing) + len(separated) + len(unresolved) == 100
                and bearing.isdisjoint(separated) and bearing.isdisjoint(unresolved)
                and separated.isdisjoint(unresolved),
                f"{case_id} time {time} classifications do not partition the 100 cells")
        bearing_sets.append(bearing)
        states.append({
            "time": time,
            "load_factor": factor,
            "strict_positive_bearing_count": len(bearing),
            "strictly_separated_count": len(separated),
            "unresolved_count": len(unresolved),
            "input_mask_mismatch_count": sum(
                row["input_mask_compatibility"] != "CONSISTENT_WITH_PROPOSED_BRANCH" for row in rows
            ),
            "rows": rows,
        })

    stable_set = all(values == bearing_sets[0] for values in bearing_sets[1:])
    require(stable_set, f"{case_id} observed strict-positive set changes across the seven increments")
    final_rows = states[-1]["rows"]
    exceptions = []
    for row in final_rows:
        if row["input_mask_compatibility"] != "CONSISTENT_WITH_PROPOSED_BRANCH":
            exceptions.append({
                "source_group": row["source_group"],
                "normal_cell": row["normal_cell"],
                "proposed_input_state": "selected_bearing" if row["source_group_selected_in_proposed_input"] else "released_inactive",
                "observed_interval_classification": row["classification"],
                "compatibility_exception": row["input_mask_compatibility"],
                "same_classification_all_seven_increments": all(
                    next(state_row for state_row in state_record["rows"]
                         if state_row["source_group"] == row["source_group"])["classification"]
                    == row["classification"] for state_record in states
                ),
            })
    require(all(item["same_classification_all_seven_increments"] for item in exceptions),
            f"{case_id} exception classification is not stable through full load")

    path_hashes = {str((packet / name).relative_to(ROOT)): digest for name, digest in expected.items()}
    path_hashes[str(METHOD_WRAPPER.relative_to(ROOT))] = sha(METHOD_WRAPPER)
    path_hashes[str(METHOD_STABLE.relative_to(ROOT))] = sha(METHOD_STABLE)
    path_hashes[str(METHOD_REPLAY.relative_to(ROOT))] = sha(METHOD_REPLAY)
    path_hashes[str(METHOD_REPLAY_PRODUCER.relative_to(ROOT))] = sha(METHOD_REPLAY_PRODUCER)
    path_hashes[str(METHOD_README.relative_to(ROOT))] = sha(METHOD_README)
    input_mask_selected_bearing = selected & bearing_sets[-1]
    input_mask_inactive_bearing = inactive & bearing_sets[-1]
    input_mask_selected_separating = selected & {
        row["normal_cell"] for row in final_rows if row["strictly_separated"]
    }
    return {
        "schema": "current_springa_selected_floor_normal_interval_diagnostic/v1",
        "status": "COMPLETED_NORMAL_LAW_DIAGNOSTIC_ONLY_PROPOSED_BRANCH_REJECTED",
        "case_id": case_id,
        "candidate": record["candidate"],
        "geometry_revision_id": record["geometry_revision_id"],
        "selected_floor_branch_id": record["floor_branch_metadata"]["branch_id"],
        "native_case_terminal_status": terminal["status"],
        "source_selected_bearing_count": len(selected),
        "source_released_inactive_count": len(inactive),
        "printed_state_count": len(states),
        "normal_count_per_state": 100,
        "full_factor_1_reached": True,
        "strict_positive_cell_set_stable_all_states": stable_set,
        "strict_positive_cells_at_final_state": sorted(bearing_sets[-1]),
        "input_selected_cells_not_strictly_positive": sorted(input_mask_selected_separating | {
            row["normal_cell"] for row in final_rows
            if row["source_group_selected_in_proposed_input"]
            and row["classification"] == "UNRESOLVED_INTERVALS"
        }),
        "input_inactive_cells_strictly_positive": sorted(input_mask_inactive_bearing),
        "compatibility_exception_count": len(exceptions),
        "compatibility_exceptions": exceptions,
        "states": states,
        "provenance": {
            "source_sha256": path_hashes,
            "producer_sha256": sha(Path(__file__)),
            "terminal_validation": run_validation,
            "parent_rejection_reason": terminal["strict_response_exception"],
            "zero_u_method": {
                "wrapper_path": str(METHOD_WRAPPER.relative_to(ROOT)),
                "wrapper_sha256": sha(METHOD_WRAPPER),
                "stable_parser_path": str(METHOD_STABLE.relative_to(ROOT)),
                "stable_parser_sha256": sha(METHOD_STABLE),
                "proof_replay_path": str(METHOD_REPLAY.relative_to(ROOT)),
                "proof_replay_sha256": sha(METHOD_REPLAY),
                "proof_producer_sha256": sha(METHOD_REPLAY_PRODUCER),
            },
            "input_adapter_audit_sha256": sha(packet / "parent-serialized-input-audit.json"),
            "terminal_assessment_sha256": sha(packet / "parent-terminal-assessment.json"),
            "case_context_sha256": sha(packet / "case-context.json"),
        },
        "claims": {
            "diagnostic_only": True,
            "physical_connection_force_export_performed": False,
            "corner_demands_usable": False,
            "proposed_floor_branch_accepted": False,
            "mechanical_or_joint_acceptance": False,
            "physical_failure_inferred": False,
            "floor_mask_or_iteration_proposed": False,
            "native_run_performed_by_this_producer": False,
            "zero_u_only_representation_rule_used": True,
            "nonzero_u_rounding_and_all_rf_rounding_retained": True,
            "geometric_subtraction_arithmetic_guard_retained": True,
            "numerical_ground_rf_is_not_a_physical_support_reaction": True,
        },
        "limits": [
            "The intervals are native DAT representation intervals and arithmetic guards; they do not bound nonlinear solver residual, convergence error, pre-format underflow, or the exact continuum solution.",
            "A selected-floor proposal whose normal laws contradict its prescribed active/inactive set is rejected. These diagnostics do not synthesize an equilibrium response for a different contact set.",
            "SPRINGA endpoint RF values are numerical constitutive verification data only. This packet exports no physical connector forces, body balance, corner bolt demands, or resistance checks.",
            "No stability, structural adequacy, joint acceptance, fabrication, or climbing-use claim is made.",
        ],
    }


def produce() -> dict[str, Any]:
    require(all(path.is_file() and sha(path) == expected for path, expected in METHOD_PINS.items()),
            "Pinned zero-U method/proof evidence changed")
    method = load_method()
    cases = {case_id: produce_case(case_id, method) for case_id in ("k12-rear", "a1-rear")}
    for case_id, report in cases.items():
        (HERE / f"{case_id}-normal-intervals.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    exception_register = []
    for case_id, report in cases.items():
        for item in report["compatibility_exceptions"]:
            exception_register.append({"case_id": case_id, **item})
    return {
        "schema": "current_springa_selected_floor_normal_compatibility_exception_register/v1",
        "status": "COMPLETED_SOURCE_BOUND_NORMAL_INTERVAL_DIAGNOSTICS_ONLY",
        "cases": {
            case_id: {
                "report_path": f"{case_id}-normal-intervals.json",
                "report_status": report["status"],
                "selected_bearing_count": report["source_selected_bearing_count"],
                "released_inactive_count": report["source_released_inactive_count"],
                "counts_each_state": [
                    {"time": state["time"], "load_factor": state["load_factor"],
                     "strict_positive_bearing": state["strict_positive_bearing_count"],
                     "strictly_separated": state["strictly_separated_count"],
                     "unresolved": state["unresolved_count"],
                     "mask_mismatches": state["input_mask_mismatch_count"]}
                    for state in report["states"]
                ],
                "compatibility_exception_count": report["compatibility_exception_count"],
                "source_sha256": report["provenance"]["source_sha256"],
                "report_sha256": sha(HERE / f"{case_id}-normal-intervals.json"),
            }
            for case_id, report in cases.items()
        },
        "compatibility_exceptions": exception_register,
        "claims": {
            "diagnostic_only": True,
            "no_physical_force_export": True,
            "no_floor_mask_or_automatic_iteration_proposed": True,
            "both_parent_terminal_assessments_remain_rejected": True,
            "corner_demands_usable": False,
            "mechanical_or_joint_acceptance": False,
        },
        "producer_sha256": sha(Path(__file__)),
    }


if __name__ == "__main__":
    combined = produce()
    (HERE / "compatibility-exception-register.json").write_text(
        json.dumps(combined, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "status": combined["status"],
        "cases": {case_id: {
            "status": report["report_status"],
            "counts_each_state": report["counts_each_state"],
            "compatibility_exception_count": report["compatibility_exception_count"],
        } for case_id, report in combined["cases"].items()},
        "compatibility_exceptions": combined["compatibility_exceptions"],
        "corner_demands_usable": False,
    }, indent=2))
