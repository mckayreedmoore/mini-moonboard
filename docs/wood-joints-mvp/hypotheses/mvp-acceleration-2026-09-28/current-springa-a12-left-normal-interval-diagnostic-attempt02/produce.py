#!/usr/bin/env python3
"""Reclassify a12-left attempt03 and compare the two frozen support masks."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
PRIOR_DIAGNOSTIC = SERIES / "current-springa-a12-left-normal-interval-diagnostic-attempt01/a12-left-normal-intervals.json"
PRIOR_DIAGNOSTIC_SHA256 = "029244c02a57ddbe2dff9abd1c2afd3533e39f23a387e37e472b742c9ba53f86"
PRIOR_PRODUCER = SERIES / "current-springa-a12-left-normal-interval-diagnostic-attempt01/produce.py"
PRIOR_PRODUCER_SHA256 = "0bad1eb9c1a29bfb437d84496578d37842ad3a61125c56757e383c50567490ce"
METHOD_PRODUCER = PRIOR_PRODUCER
METHOD_PRODUCER_SHA256 = PRIOR_PRODUCER_SHA256
PRIOR_ATTEMPT = SERIES / "current-springa-selected-floor-a12-left-attempt02"
CURRENT_ATTEMPT = SERIES / "current-springa-selected-floor-a12-left-attempt03"
CONTROL = SERIES / "current-springa-frame-a12-left-all-bearing-attempt01"
PROPOSAL = SERIES / "current-springa-case-bound-floor-input-adapter-attempt09/a12-left"
FRESH_MODEL = SERIES / "current-springa-six-case-frame-input-adapter-attempt01/a12-left/model.json"
REGISTER = SERIES / "current-six-case-source-load-register-attempt01/register.json"
ALL_BEARING_SCREEN = SERIES / "current-springa-a12-left-floor-screen-attempt01/screen.json"
ALL_BEARING_SCREEN_PRODUCER = SERIES / "current-springa-a12-left-floor-screen-attempt01/produce.py"

PRIOR_ATTEMPT_PINS = {
    "model.json": "8e686621023b73d9e3308f2d58b54cec3185930763a9cd23fda8af9e630a6630",
    "model.inp": "4e25e63fa9831e23f22d3b69d7cfcbd7dc503cf7c974a41be76e1b522267c8a9",
    "model.dat": "eeff478cf6c3a011da3330f8d7dd2cc8ad3a2020959a0ba8700520ed15bfa5bc",
    "execution.json": "1b4ed6a574bfb9a001e15693659cb56edca7f778595c45f504b9e7438cb54079",
    "freeze.json": "e2200b761607a021e78de7e6f7ba41a72904e6a7722a7680e236a02bd6ef7a49",
    "authorization.json": "70c6c54ab3f4774306991f90691cadeda1acabe36cd3dec219e17a2c445f1051",
    "case-context.json": "22599cff133cc80b816709e9e8babfa6bdd84fce513c5a5e1f6db76755c4031b",
    "parent-serialized-input-audit.json": "e7b7d74086682bc69bc2f8d2c3438f294bb61ae07c0e5f08bd45ec8005c03174",
    "parent-readiness-review.json": "4a35a5c4ecf1a45f9674515397ee9be1a6310644464675cdbf9712fb2b24065c",
    "parent-case-context-check.json": "e5c6f0215f1a65f4ffd0a2ef7effe87ced8f9c1188a0f42a1048aa5c7b3612cf",
    "parent-terminal-assessment.json": "6d888a68d6097ca8b2a65cffd33654005f9103bab8187e1533a24c17c4aceeef",
    "native.stdout": "e0c3a0c253ca9fa8ce2d4d1e7b1a2dcdbe2f73bf6c34e3b5b82b7e6e034661b9",
    "native.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}
CURRENT_ATTEMPT_PINS = {
    "model.json": "9b759dd40c3b5950b031a4d2be6697b216809d774b07d5bd141ecd2555cd8c17",
    "model.inp": "bda415108a68af5dadd2f8cfecf542c2ab3f3d96ea9f79925b96f48e63823d0d",
    "model.dat": "e0cc24182f44689a6257882d7a3eae3f17ea2ed4b53a22e9b2dc1366da4eb9e5",
    "execution.json": "1045b374618b431907a4fb4b17555f5bcb641a29649e6241ade2534aead156db",
    "freeze.json": "9bc1bce4fcb681f48f2d528c7a72c6a0d5ddecbf34253e5cc850c6e165b446c3",
    "authorization.json": "7642884e5e70933b050de75c7c2a830c9a2d015c06a573fd13eeebcadc5ee45c",
    "case-context.json": "5399f0eda5d13bff3547aa72b57aa4c76efed5f9c271298117f691039c04b6f4",
    "parent-serialized-input-audit.json": "17ba2725dbed06f59c28cb289900a726468582f9300d2b67c428815b8255beb0",
    "parent-readiness-review.json": "42d36f9b5fca7e0a7070bbce932301ec989723483ff4232016a77facdaaf8e49",
    "parent-case-context-check.json": "226d5be5ede03dc8e58061f4e552617570f5435bff9489e69fe294f0a3371a67",
    "parent-terminal-assessment.json": "b7e5711d8f77255b4c68ad2f8640ced6c5c7e8b522adcb389b269f2e768f738d",
}
CONTROL_PINS = {
    "model.json": "4794fb54a8761db8a14b8058bc517e9f5b8b69ffcedea574c1911f79657e9781",
    "model.inp": "7543c3500d185f21c1a27ac7d949235832210dea2a2c802114dd3d6376e62487",
    "model.dat": "3dc673b0d33048ed421e4677988b5ac9b63bf5b9ed753b7f96fa35b4cb79cb13",
    "execution.json": "510366c340fa5007af446efb0fc1a436344a7ed276392f8418cdeb3193e38c7a",
    "freeze.json": "9dca9e49aac519b818fb9017ad69e8d6675b8e7b087c487d789cfaf2d4bebc57",
    "authorization.json": "ba8bb6d2fa18316938ebc484e2c0b04b3efcd233a0780a4da0175655b69ae51a",
    "parent-serialized-input-audit.json": "6c40c26f078b22f9a0a0f2deecfdfb5c1dcad6e29d629e2c638cd41dea7faf86",
}
LINEAGE_PINS = {
    FRESH_MODEL: "4d56602abb6a2325b4cf08d2adbbc92b405cf1435eaf0c356a0e1da9d50a0473",
    REGISTER: "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508",
    ALL_BEARING_SCREEN: "0a04bfad5068b4f20cdb69eab5198e57d25052d1a1db84c70af4b2b67677fdf6",
    ALL_BEARING_SCREEN_PRODUCER: "13e11865e1ef18abebaf6b048ba61f49b7a5b11af2d2e46c0b70938de2d97576",
    PROPOSAL / "model.json": "9e1347fcd5168a465d0994eca361dfd16f7ffc81dfaabf138f7a1fa11f310fd0",
    PROPOSAL / "model.inp": "bda415108a68af5dadd2f8cfecf542c2ab3f3d96ea9f79925b96f48e63823d0d",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_pinned_method():
    require(sha(METHOD_PRODUCER) == METHOD_PRODUCER_SHA256,
            "Pinned 711 interval producer changed")
    spec = importlib.util.spec_from_file_location("pinned_k12_interval_producer", METHOD_PRODUCER)
    require(spec is not None and spec.loader is not None, "Cannot load pinned interval producer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    interval_source, method = module.load_source_module()
    require(sha(PRIOR_DIAGNOSTIC) == PRIOR_DIAGNOSTIC_SHA256
            and sha(PRIOR_PRODUCER) == PRIOR_PRODUCER_SHA256,
            "Pinned prior a12-left 10-cell run diagnostic changed")
    return interval_source, method


def classify_attempt(packet: Path, pins: dict[str, str], expected_active_count: int,
                     expected_exception: str, interval_source: Any, method: Any) -> dict[str, Any]:
    for name, digest in pins.items():
        path = packet / name
        require(path.is_file() and sha(path) == digest,
                f"Source pin mismatch in {packet.name}: {name}")

    record = load(packet / "model.json")
    context = load(packet / "case-context.json")
    execution = load(packet / "execution.json")
    terminal = load(packet / "parent-terminal-assessment.json")
    authorization = load(packet / "authorization.json")
    input_audit = load(packet / "parent-serialized-input-audit.json")
    readiness = load(packet / "parent-readiness-review.json")
    context_check = load(packet / "parent-case-context-check.json")
    deck = (packet / "model.inp").read_text(encoding="utf-8")
    data = (packet / "model.dat").read_text(encoding="utf-8", errors="replace")

    selected = set(map(str, record.get("floor_selected_bearing_cells", [])))
    branch = record.get("floor_branch_metadata", {})
    require(record.get("case_id") == context.get("case_id") == "a12-left"
            and record.get("candidate") == "compact-floor-flush-wood-joints-development"
            and record.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1"
            and len(selected) == expected_active_count
            and branch.get("status") == "proposed_diagnostic_mask_only"
            and branch.get("diagnostic_stage") == "selected-proposal"
            and branch.get("selected_cells") == sorted(selected)
            and branch.get("selected_cell_count") == expected_active_count,
            f"{packet.name} is not the expected frozen selected mask")
    inventory = context_check.get("inventory", {})
    require(readiness.get("ready_for_scoped_native_run") is True
            and readiness.get("max_launches") == 1
            and readiness.get("case_id") == "a12-left"
            and readiness.get("joint_acceptance") is False
            and readiness.get("mechanical_acceptance") is False,
            f"{packet.name} parent readiness no longer binds one conditional diagnostic run")
    require(input_audit.get("status") == "PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT"
            and input_audit.get("case_id") == "a12-left"
            and input_audit.get("baseline_model_sha256") == CONTROL_PINS["model.json"]
            and input_audit.get("baseline_deck_sha256") == CONTROL_PINS["model.inp"]
            and input_audit.get("model_sha256") == pins["model.json"]
            and input_audit.get("deck_sha256") == pins["model.inp"]
            and input_audit.get("physical_body_count") == 50
            and input_audit.get("candidate_bolt_axes") == 92
            and input_audit.get("retained_leg_runner_axes") == 12
            and input_audit.get("hillman_axes") == 66
            and input_audit.get("selected_bearing_cells") == expected_active_count
            and input_audit.get("released_cells") == 100 - expected_active_count
            and input_audit.get("active_tangent_rows") == 2 * expected_active_count
            and input_audit.get("no_geometry_law_load_or_material_change") is True
            and input_audit.get("proposed_branch_accepted") is False
            and input_audit.get("corner_demands_usable") is False,
            f"{packet.name} source-bound input audit failed expected 92/12/66 and mask gates")
    require(context_check.get("status") == "PASS_FROZEN_CASE_BOUND_INPUT_CONTRACT_ONLY"
            and context_check.get("native_response_consumed") is False
            and inventory.get("selected_bearing_cells") == expected_active_count
            and inventory.get("inactive_separated_cells") == 100 - expected_active_count
            and inventory.get("selected_floor_tangent_reaction_rows") == 2 * expected_active_count
            and inventory.get("inactive_floor_tangent_rows_without_restraint") == 2 * (100 - expected_active_count)
            and inventory.get("physical_body_count") == 50
            and inventory.get("new_candidate_bolt_axes") == 92
            and inventory.get("retained_leg_runner_bolt_axes") == 12
            and inventory.get("panel_screw_axes") == 66,
            f"{packet.name} frozen case-bound context inventory changed")
    require(context.get("selected_input_model_json_sha256") == pins["model.json"]
            and context.get("selected_input_deck_sha256") == pins["model.inp"]
            and context.get("source_controls_model_json_sha256") == CONTROL_PINS["model.json"]
            and context.get("source_controls_deck_sha256") == CONTROL_PINS["model.inp"]
            and authorization.get("input_freeze_sha256") == pins["freeze.json"]
            and authorization.get("native_execution_authorized") is True
            and authorization.get("mechanical_acceptance") is False,
            f"{packet.name} source model/deck/freeze authorization binding changed")
    require(terminal.get("status") == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
            and terminal.get("case_id") == "a12-left"
            and terminal.get("strict_response_exception") == expected_exception
            and terminal.get("container_confirmed_terminal") is True
            and terminal.get("native_returncode") == 0
            and terminal.get("corner_demands_usable") is False
            and terminal.get("joint_accepted") is False
            and terminal.get("physical_failure_inferred") is False,
            f"{packet.name} terminal assessment is not the expected rejected diagnostic")
    for name in ("model.json", "model.inp", "model.dat", "execution.json", "case-context.json"):
        require(terminal.get("sources_sha256", {}).get(name) == pins[name],
                f"{packet.name} terminal assessment does not bind {name}")
    require(execution.get("native_solve_executed") is True
            and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True
            and execution.get("run_id") == terminal.get("run_id"),
            f"{packet.name} execution record is not terminal returncode 0")

    contract = method._validate_model(record, deck, context)
    validation = method._validate_execution(
        packet / "model.json", packet / "model.dat", packet / "model.inp",
        packet / "execution.json", data, context,
    )
    parsed = method.parse_native_blocks(data)
    require(len(parsed) == 7, f"{packet.name} DAT does not contain exactly seven states")
    emitted = contract["emitted_nodes"]
    node_inventory = set(map(int, record["nodes"]))
    times = sorted(parsed)
    factors = [float(method.load_scale(time, contract["total_time"])) for time in times]
    require(all(set(state["u"]) == node_inventory and set(state["rf"]) == node_inventory
                for state in parsed.values()), f"{packet.name} DAT omits required U/RF nodes")
    require(all(right > left for left, right in zip(times, times[1:]))
            and math.isclose(factors[-1], 1.0, rel_tol=0.0, abs_tol=1e-12),
            f"{packet.name} is not an ordered seven-state full-factor response")

    normals = {
        str(row["group"]): row for row in contract["source_rows"]
        if row.get("role") == "floor_normal" and row.get("intended_law") == "compression_only"
    }
    bindings = {
        str(binding["group"]): binding for binding in contract["bindings"]
        if str(binding["group"]) in normals
    }
    require(len(normals) == len(bindings) == 100,
            f"{packet.name} does not bind all 100 floor-normal carriers")

    states: list[dict[str, Any]] = []
    positive_sets: list[set[str]] = []
    for time, factor in zip(times, factors, strict=True):
        rows = []
        for group in sorted(normals, key=lambda value: int(value.removeprefix("SPR"))):
            result = interval_source.classify_normal(bindings[group], normals[group], parsed[time], emitted, method)
            result["selected_in_this_input"] = result["normal_cell"] in selected
            rows.append(result)
        positive = {row["normal_cell"] for row in rows if row["strictly_positive_bearing"]}
        separated = {row["normal_cell"] for row in rows if row["strictly_separated"]}
        unresolved = {row["normal_cell"] for row in rows if row["classification"] == "UNRESOLVED_INTERVALS"}
        require(len(rows) == 100 and len(positive) + len(separated) + len(unresolved) == 100
                and not (positive & separated or positive & unresolved or separated & unresolved),
                f"{packet.name} state {time} did not classify 100 disjoint intervals")
        positive_sets.append(positive)
        states.append({
            "time": float(time),
            "load_factor": float(factor),
            "strict_positive_count": len(positive),
            "strictly_separated_count": len(separated),
            "unresolved_count": len(unresolved),
            "observed_positive_cells": sorted(positive),
            "selected_not_strictly_positive": sorted(selected - positive),
            "inactive_strictly_positive": sorted(positive - selected),
            "input_mask_mismatches": [
                {"normal_cell": row["normal_cell"], "source_group": row["source_group"],
                 "selected_in_input": row["selected_in_this_input"],
                 "observed_classification": row["classification"]}
                for row in rows if row["selected_in_this_input"] != row["strictly_positive_bearing"]
            ],
            "rows": rows,
        })
    stable = all(values == positive_sets[0] for values in positive_sets[1:])
    return {
        "attempt_directory": str(packet.relative_to(ROOT)),
        "selected_cells": sorted(selected),
        "selected_count": len(selected),
        "strict_positive_set_stable_all_seven": stable,
        "strict_positive_sets_identical_across_states": all(values == positive_sets[0] for values in positive_sets),
        "parent_terminal_assessment": {
            "status": terminal["status"],
            "run_id": terminal["run_id"],
            "native_returncode": terminal["native_returncode"],
            "strict_response_exception": terminal["strict_response_exception"],
            "corner_demands_usable": terminal["corner_demands_usable"],
        },
            "source_bound_input_gates": {
                "parent_readiness_one_launch": True,
                "parent_serialized_input_audit_pass": True,
                "case_bound_context_inventory_pass": True,
                "source_model_deck_and_freeze_binding_pass": True,
                "92_new_12_retained_66_panel_axes_preserved": True,
                "no_geometry_law_load_or_material_change": True,
            },
            "states": states,
        "terminal_validation": validation,
    }


def rows_by_cell(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["normal_cell"]: row for row in state["rows"]}


def produce() -> dict[str, Any]:
    interval_source, method = load_pinned_method()
    for path, digest in LINEAGE_PINS.items():
        require(path.is_file() and sha(path) == digest, f"Pinned a12-left control/proposal changed: {path}")
    for name, digest in CONTROL_PINS.items():
        require((CONTROL / name).is_file() and sha(CONTROL / name) == digest,
                f"Pinned original all-bearing control changed: {name}")

    prior_report = load(PRIOR_DIAGNOSTIC)
    prior_model = load(PRIOR_ATTEMPT / "model.json")
    prior_terminal = load(PRIOR_ATTEMPT / "parent-terminal-assessment.json")
    current_report = classify_attempt(
        CURRENT_ATTEMPT, CURRENT_ATTEMPT_PINS, 11,
        "Selected floor normal is not strictly positive after rounding: SPR1302",
        interval_source, method,
    )

    prior_selected = set(map(str, prior_model["floor_selected_bearing_cells"]))
    current_selected = set(current_report["selected_cells"])
    proposal_model = load(PROPOSAL / "model.json")
    require(current_selected == set(map(str, proposal_model["floor_selected_bearing_cells"]))
            and prior_selected == set(map(str, prior_model["floor_branch_metadata"]["selected_cells"]))
            and prior_report.get("case_id") == "a12-left"
            and prior_report.get("source_selected_bearing_count") == 10
            and prior_report.get("strict_positive_cell_set_stable_all_states") is True
            and prior_report.get("full_factor_1_reached") is True
            and len(prior_report.get("states", [])) == 7,
            "Prior 10-cell diagnostic or latest 11-cell frozen input lineage changed")
    prior_positive_sets = [
        {row["normal_cell"] for row in state["rows"] if row["strictly_positive_bearing"]}
        for state in prior_report["states"]
    ]
    require(all(values == prior_positive_sets[0] for values in prior_positive_sets)
            and len(prior_positive_sets[0]) == 11,
            "Prior 10-cell attempt no longer has its pinned 11-cell stable positive set")

    current_positive_sets = [set(state["observed_positive_cells"]) for state in current_report["states"]]
    prior_positive = prior_positive_sets[0]
    current_positive = current_positive_sets[0]
    prior10_delta = {
        "observed_positive_not_in_prior_10_cell_input": sorted(prior_positive - prior_selected),
        "prior_10_cell_input_not_observed_strict_positive": sorted(prior_selected - prior_positive),
    }
    current11_delta = {
        "observed_positive_not_in_current_11_cell_input": sorted(current_positive - current_selected),
        "current_11_cell_input_not_observed_strict_positive": sorted(current_selected - current_positive),
    }
    cycle = bool(
        current_report["strict_positive_set_stable_all_seven"]
        and current_positive == prior_selected
        and prior_positive == current_selected
        and len(prior_positive ^ current_positive) == 1
        and prior_positive ^ current_positive == {"floor_lumber_leg_left_1"}
    )

    spr1302_rows = []
    for index, (prior_state, current_state) in enumerate(zip(prior_report["states"], current_report["states"], strict=True)):
        prior_row = next(row for row in prior_state["rows"] if row["source_group"] == "SPR1302")
        current_row = next(row for row in current_state["rows"] if row["source_group"] == "SPR1302")
        require(prior_state["time"] == current_state["time"]
                and prior_state["load_factor"] == current_state["load_factor"],
                "Prior/current a12-left states do not align exactly")
        spr1302_rows.append({
            "time": current_state["time"],
            "load_factor": current_state["load_factor"],
            "prior_10_input_attempt": {
                "classification": prior_row["classification"],
                "selected_in_input": prior_row["source_group_selected_in_proposed_input"],
                "projected_q_interval_mm": prior_row["projected_q_interval_mm"],
                "geometric_spring_elongation_interval_mm": prior_row["geometric_spring_elongation_interval_mm"],
                "native_table_force_interval_N": prior_row["native_table_force_interval_N"],
                "native_endpoint_internal_interval_N": prior_row["native_endpoint_internal_interval_N"],
                "native_ground_rf_interval_N": prior_row["native_ground_rf_interval_N"],
                "endpoint_rf_intervals_all_components_contain_zero": prior_row["endpoint_rf_intervals_all_components_contain_zero"],
            },
            "current_11_input_attempt": {
                "classification": current_row["classification"],
                "selected_in_input": current_row["selected_in_this_input"],
                "projected_q_interval_mm": current_row["projected_q_interval_mm"],
                "geometric_spring_elongation_interval_mm": current_row["geometric_spring_elongation_interval_mm"],
                "native_table_force_interval_N": current_row["native_table_force_interval_N"],
                "native_endpoint_internal_interval_N": current_row["native_endpoint_internal_interval_N"],
                "native_ground_rf_interval_N": current_row["native_ground_rf_interval_N"],
                "endpoint_rf_intervals_all_components_contain_zero": current_row["endpoint_rf_intervals_all_components_contain_zero"],
            },
        })

    per_state_comparison = []
    for old_state, new_state in zip(prior_report["states"], current_report["states"], strict=True):
        old_positive = {row["normal_cell"] for row in old_state["rows"] if row["strictly_positive_bearing"]}
        new_positive = set(new_state["observed_positive_cells"])
        old_by = rows_by_cell(old_state)
        new_by = rows_by_cell(new_state)
        classification_changes = [
            {"normal_cell": cell, "source_group": old_by[cell]["source_group"],
             "prior_10_input_attempt": old_by[cell]["classification"],
             "current_11_input_attempt": new_by[cell]["classification"]}
            for cell in sorted(old_by)
            if old_by[cell]["classification"] != new_by[cell]["classification"]
        ]
        per_state_comparison.append({
            "time": new_state["time"],
            "load_factor": new_state["load_factor"],
            "prior_10_input_attempt_positive_count": len(old_positive),
            "current_11_input_attempt_positive_count": len(new_positive),
            "positive_only_in_prior_10_input_attempt": sorted(old_positive - new_positive),
            "positive_only_in_current_11_input_attempt": sorted(new_positive - old_positive),
            "classification_changes_by_cell": classification_changes,
            "classification_change_count": len(classification_changes),
        })

    source_map: dict[str, str] = {}
    for path, digest in LINEAGE_PINS.items():
        source_map[str(path.relative_to(ROOT))] = digest
    for filename, digest in CONTROL_PINS.items():
        source_map[str((CONTROL / filename).relative_to(ROOT))] = digest
    for filename, digest in PRIOR_ATTEMPT_PINS.items():
        source_map[str((PRIOR_ATTEMPT / filename).relative_to(ROOT))] = digest
    for filename, digest in CURRENT_ATTEMPT_PINS.items():
        source_map[str((CURRENT_ATTEMPT / filename).relative_to(ROOT))] = digest
    source_map[str(PRIOR_DIAGNOSTIC.relative_to(ROOT))] = PRIOR_DIAGNOSTIC_SHA256
    source_map[str(PRIOR_PRODUCER.relative_to(ROOT))] = PRIOR_PRODUCER_SHA256
    source_map[str(METHOD_PRODUCER.relative_to(ROOT))] = METHOD_PRODUCER_SHA256
    prior_source_map = prior_report["provenance"]["source_sha256"]
    source_map.update(prior_source_map)

    require(prior_terminal.get("sources_sha256", {}).get("model.dat") == PRIOR_ATTEMPT_PINS["model.dat"],
            "Prior terminal assessment does not bind the 10-cell DAT")
    return {
        "schema": "current_springa_a12_left_normal_interval_mask_comparison/v1",
        "status": "COMPLETED_NORMAL_LAW_DIAGNOSTIC_ONLY_TWO_MASK_SUPPORT_CYCLE_OBSERVED" if cycle
                  else "COMPLETED_NORMAL_LAW_DIAGNOSTIC_ONLY_NO_TWO_MASK_CYCLE_PROVEN",
        "case_id": "a12-left",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "method": {
            "response_auditor_sha256": "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
            "stable_parser_sha256": "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
            "method_producer_path": str(METHOD_PRODUCER.relative_to(ROOT)),
            "method_producer_sha256": METHOD_PRODUCER_SHA256,
            "zero_u_only_representation_rule": True,
            "nonzero_u_and_all_rf_rounding_retained": True,
            "geometric_subtraction_arithmetic_guard_retained": True,
        },
        "support_cycle_assessment": {
            "observed_two_mask_cycle": cycle,
            "meaning": "The prior 10-cell run classified the 11-cell mask as strictly positive; the frozen 11-cell attempt03 run classifies the prior 10-cell mask as strictly positive.",
            "only_toggled_cell": "floor_lumber_leg_left_1 / SPR1302",
            "prior_10_input_vs_its_observed_positive_set": prior10_delta,
            "current_11_input_vs_its_observed_positive_set": current11_delta,
            "positive_set_symmetric_difference": sorted(prior_positive ^ current_positive),
            "per_increment_comparison": per_state_comparison,
            "automatic_next_mask_or_iteration_proposed": False,
            "active_set_method_recommended": False,
        },
        "spr1302_exact_interval_sign_comparison": {
            "normal_cell": "floor_lumber_leg_left_1",
            "source_group": "SPR1302",
            "prior_attempt": "current-springa-selected-floor-a12-left-attempt02 (10 selected cells)",
            "current_attempt": "current-springa-selected-floor-a12-left-attempt03 (11 selected cells)",
            "by_increment": spr1302_rows,
        },
        "attempts": {
            "prior_10_cell_attempt": {
                "selected_cells": sorted(prior_selected),
                "observed_strict_positive_cells": sorted(prior_positive),
                "observed_set_stable_all_seven": prior_report["strict_positive_cell_set_stable_all_states"],
                "strict_separated_count_each_state": [state["strictly_separated_count"] for state in prior_report["states"]],
                "unresolved_count_each_state": [state["unresolved_count"] for state in prior_report["states"]],
            },
            "current_11_cell_attempt03": {
                "selected_cells": sorted(current_selected),
                "observed_strict_positive_cells": sorted(current_positive),
                "observed_set_stable_all_seven": current_report["strict_positive_set_stable_all_seven"],
                "parent_terminal_assessment": current_report["parent_terminal_assessment"],
                "per_state_counts": [
                    {key: state[key] for key in ("time", "load_factor", "strict_positive_count",
                                                 "strictly_separated_count", "unresolved_count")}
                    for state in current_report["states"]
                ],
                "all_100_normal_intervals_all_seven_states": current_report["states"],
            },
        },
        "lineage": {
            "original_all_bearing_physics_control": str(CONTROL.relative_to(ROOT)),
            "prior_10_cell_attempt": str(PRIOR_ATTEMPT.relative_to(ROOT)),
            "current_11_cell_attempt03": str(CURRENT_ATTEMPT.relative_to(ROOT)),
            "input_proposal_adapter09": str(PROPOSAL.relative_to(ROOT)),
            "fresh_case_model": str(FRESH_MODEL.relative_to(ROOT)),
            "canonical_case_load_register": str(REGISTER.relative_to(ROOT)),
            "original_all_bearing_screen": str(ALL_BEARING_SCREEN.relative_to(ROOT)),
            "normal_carrier_laws_and_geometry_changed": False,
            "rejected_response_forces_adopted_or_exported": False,
            "corner_demands_usable": False,
        },
        "claims": {
            "diagnostic_only": True,
            "all_100_normals_classified_at_all_seven_current_states": True,
            "prior_attempt_two_masks_compared_at_all_seven_states": True,
            "physical_connection_force_export_performed": False,
            "physical_failure_inferred": False,
            "selected_floor_branch_accepted": False,
            "new_mask_or_native_iteration_proposed": False,
            "native_run_performed_by_this_producer": False,
            "numerical_ground_rf_is_not_a_physical_support_reaction": True,
        },
        "limitations": [
            "The result is a zero-gap, source-bound a12-left support-mask diagnostic. It is not a verified physical floor reaction or usable corner demand.",
            "The apparent two-mask recurrence is an observed pair of frozen runs, not proof of general active-set convergence or solver stability.",
            "Intervals bound printed DAT representation and stated arithmetic guards, not nonlinear solver residual, convergence error, pre-format underflow, or the exact continuum solution.",
            "No resistance, joint adequacy, structural qualification, or floor qualification is established.",
        ],
        "provenance": {
            "source_sha256": source_map,
            "prior_diagnostic_sha256": PRIOR_DIAGNOSTIC_SHA256,
            "prior_producer_sha256": PRIOR_PRODUCER_SHA256,
            "producer_sha256": sha(Path(__file__)),
            "attempt03_terminal_validation": current_report["terminal_validation"],
        },
    }


def main() -> None:
    out = HERE / "a12-left-normal-mask-cycle.json"
    pins = HERE / "source-pins.json"
    require(not out.exists() and not pins.exists(), "Refusing to overwrite existing diagnostic output")
    report = produce()
    out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    pins.write_text(json.dumps({
        "schema": "current_springa_a12_left_normal_mask_cycle_source_pins/v1",
        "producer_path": str(Path(__file__).relative_to(ROOT)),
        "producer_sha256": sha(Path(__file__)),
        "diagnostic_path": str(out.relative_to(ROOT)),
        "diagnostic_sha256": sha(out),
        "source_sha256": report["provenance"]["source_sha256"],
    }, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "observed_two_mask_cycle": report["support_cycle_assessment"]["observed_two_mask_cycle"],
        "prior_10_delta": report["support_cycle_assessment"]["prior_10_input_vs_its_observed_positive_set"],
        "current_11_delta": report["support_cycle_assessment"]["current_11_input_vs_its_observed_positive_set"],
        "SPR1302": [
            {"time": row["time"],
             "prior_class": row["prior_10_input_attempt"]["classification"],
             "current_class": row["current_11_input_attempt"]["classification"],
             "prior_q": row["prior_10_input_attempt"]["projected_q_interval_mm"],
             "current_q": row["current_11_input_attempt"]["projected_q_interval_mm"]}
            for row in report["spr1302_exact_interval_sign_comparison"]["by_increment"]
        ],
        "diagnostic_sha256": sha(out),
        "producer_sha256": sha(Path(__file__)),
    }, indent=2))


if __name__ == "__main__":
    main()
