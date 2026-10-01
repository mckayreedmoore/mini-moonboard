#!/usr/bin/env python3
"""Classify a12-left attempt02's 100 floor normals with pinned zero-U method 711."""
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
SOURCE_PRODUCER = SERIES / "current-springa-k12-rear-selected-floor-normal-interval-diagnostic-attempt01/produce.py"
SOURCE_PRODUCER_SHA256 = "ee50313fe5a5b456fa54a8f2bc317abf6b8e06274b9a465e4bb5fac37b47479d"
ZERO_U_DIR = SERIES / "current-springa-zero-u-token-response-audit-attempt01"
METHOD_FILES = {
    ZERO_U_DIR / "response_audit.py": "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
    ZERO_U_DIR / "stable_response_audit.py": "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    ZERO_U_DIR / "zero_u_token_replay.json": "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1",
    ZERO_U_DIR / "replay_zero_u_tokens.py": "6b49312429c78e04d0a70a7a428382028ac9e75ab01a69b53271d9feca91bd32",
    ZERO_U_DIR / "README.md": "ef2c8d33ac9e48566c8b5c96f8ae4a0fa0216ff00fa1bc3aa6d7e3c0f76f0d49",
}
RESPONSE_WRITER = SERIES / "current-springa-case-bound-parent-report-writer-attempt01/write_report.py"
RESPONSE_WRITER_SHA256 = "92ea2e378c486674234b31a1ba384df9a6d5ea94da39c57cd4cb1a33a54e7d39"
ATTEMPT = SERIES / "current-springa-selected-floor-a12-left-attempt02"
CONTROL = SERIES / "current-springa-frame-a12-left-all-bearing-attempt01"
FRESH_MODEL = SERIES / "current-springa-six-case-frame-input-adapter-attempt01/a12-left/model.json"
REGISTER = SERIES / "current-six-case-source-load-register-attempt01/register.json"
ALL_BEARING_SCREEN = SERIES / "current-springa-a12-left-floor-screen-attempt01/screen.json"
ALL_BEARING_SCREEN_PRODUCER = SERIES / "current-springa-a12-left-floor-screen-attempt01/produce.py"

ATTEMPT_PINS = {
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
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_source_module():
    require(sha(SOURCE_PRODUCER) == SOURCE_PRODUCER_SHA256,
            "Pinned K12-rear interval producer changed")
    spec = importlib.util.spec_from_file_location("pinned_k12_interval_producer", SOURCE_PRODUCER)
    require(spec is not None and spec.loader is not None, "Cannot load pinned interval producer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(all(path.is_file() and sha(path) == digest for path, digest in METHOD_FILES.items()),
            "Pinned 711 wrapper/proof evidence changed")
    require(sha(RESPONSE_WRITER) == RESPONSE_WRITER_SHA256,
            "Pinned response writer changed")
    require(all(path.is_file() and sha(path) == digest for path, digest in LINEAGE_PINS.items()),
            "A12-left all-bearing/fresh-case lineage changed")
    return module, module.load_method()


def produce() -> dict[str, Any]:
    interval_source, method = load_source_module()
    for name, expected in ATTEMPT_PINS.items():
        path = ATTEMPT / name
        require(path.is_file() and sha(path) == expected,
                f"A12-left attempt02 source pin changed: {name}")
    for name, expected in CONTROL_PINS.items():
        path = CONTROL / name
        require(path.is_file() and sha(path) == expected,
                f"A12-left all-bearing control source pin changed: {name}")

    record = load(ATTEMPT / "model.json")
    context = load(ATTEMPT / "case-context.json")
    execution = load(ATTEMPT / "execution.json")
    authorization = load(ATTEMPT / "authorization.json")
    input_audit = load(ATTEMPT / "parent-serialized-input-audit.json")
    readiness = load(ATTEMPT / "parent-readiness-review.json")
    context_check = load(ATTEMPT / "parent-case-context-check.json")
    terminal = load(ATTEMPT / "parent-terminal-assessment.json")
    control_record = load(CONTROL / "model.json")
    fresh_record = load(FRESH_MODEL)
    register = load(REGISTER)
    all_screen = load(ALL_BEARING_SCREEN)

    require(record.get("case_id") == context.get("case_id") == "a12-left",
            "A12-left record/context identity changed")
    branch = record.get("floor_branch_metadata", {})
    selected = set(map(str, record.get("floor_selected_bearing_cells", [])))
    require(len(selected) == 10 and branch.get("status") == "proposed_diagnostic_mask_only"
            and branch.get("diagnostic_stage") == "selected-proposal",
            "Attempt02 is no longer the direct selected-10 proposal")
    require(branch.get("selected_cells") == sorted(selected)
            and branch.get("inactive_cell_count") == 90,
            "Attempt02 selected-10 branch metadata changed")
    require(readiness.get("ready_for_scoped_native_run") is True
            and readiness.get("max_launches") == 1
            and readiness.get("case_id") == "a12-left"
            and readiness.get("joint_acceptance") is False
            and readiness.get("mechanical_acceptance") is False,
            "Parent readiness evidence does not bind the direct a12-left case")
    inventory = context_check.get("inventory", {})
    require(context_check.get("status") == "PASS_FROZEN_CASE_BOUND_INPUT_CONTRACT_ONLY"
            and context_check.get("native_response_consumed") is False
            and inventory.get("selected_bearing_cells") == 10
            and inventory.get("inactive_separated_cells") == 90
            and inventory.get("selected_floor_tangent_reaction_rows") == 20
            and inventory.get("inactive_floor_tangent_rows_without_restraint") == 180
            and inventory.get("new_candidate_bolt_axes") == 92
            and inventory.get("retained_leg_runner_bolt_axes") == 12
            and inventory.get("panel_screw_axes") == 66,
            "Case-bound input inventory or the 92/12/66 separation changed")
    require(input_audit.get("status") == "PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT"
            and input_audit.get("case_id") == "a12-left"
            and input_audit.get("proposed_branch_accepted") is False
            and input_audit.get("corner_demands_usable") is False,
            "Parent input audit no longer identifies a rejected diagnostic proposal")
    require(terminal.get("status") == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
            and terminal.get("case_id") == "a12-left"
            and terminal.get("strict_response_exception") ==
            "Inactive floor normal is not strictly separated with zero endpoint RF: SPR1302"
            and terminal.get("original_and_zero_u_representation_audits_same_exception") is True
            and terminal.get("container_confirmed_terminal") is True
            and terminal.get("native_returncode") == 0
            and terminal.get("corner_demands_usable") is False
            and terminal.get("joint_accepted") is False
            and terminal.get("physical_failure_inferred") is False,
            "Exact direct selected-10 rejection is not the source state")
    source_hashes = terminal.get("sources_sha256", {})
    for name in ("model.json", "model.inp", "model.dat", "execution.json", "case-context.json"):
        require(source_hashes.get(name) == ATTEMPT_PINS[name],
                f"Terminal assessment does not bind exact {name}")
    require(authorization.get("input_freeze_sha256") == ATTEMPT_PINS["freeze.json"]
            and authorization.get("native_execution_authorized") is True
            and authorization.get("mechanical_acceptance") is False,
            "Terminal authorization is not bound to the frozen input")
    require(execution.get("run_id") == "springa-selected-a12-left-attempt02"
            and execution.get("native_solve_executed") is True
            and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True,
            "Direct a12-left run is not a successful terminal full run")
    require(control_record.get("case_id") == fresh_record.get("case_id") == "a12-left"
            and all_screen.get("case_id") == "a12-left"
            and register.get("schema") == "current_springa_six_case_source_load_register/v1",
            "Original a12-left controls, all-bearing screen, or load-register identity changed")
    require(context.get("source_controls_model_json_sha256") == CONTROL_PINS["model.json"]
            and context.get("source_controls_deck_sha256") == CONTROL_PINS["model.inp"]
            and context.get("source_case_load_register_sha256") == LINEAGE_PINS[REGISTER],
            "Attempt02 is not tied to its own all-bearing controls and canonical case register")

    deck = (ATTEMPT / "model.inp").read_text(encoding="utf-8")
    data = (ATTEMPT / "model.dat").read_text(encoding="utf-8", errors="replace")
    contract = method._validate_model(record, deck, context)
    run_validation = method._validate_execution(
        ATTEMPT / "model.json", ATTEMPT / "model.dat", ATTEMPT / "model.inp",
        ATTEMPT / "execution.json", data, context,
    )
    parsed = method.parse_native_blocks(data)
    require(len(parsed) == 7, "A12-left DAT is missing one of the seven U/RF states")
    node_inventory = set(map(int, record["nodes"]))
    times = sorted(parsed)
    factors = [float(method.load_scale(time, contract["total_time"])) for time in times]
    require(all(set(state["u"]) == node_inventory and set(state["rf"]) == node_inventory
                for state in parsed.values()), "One or more DAT states omit required U/RF nodes")
    require(all(right > left for left, right in zip(times, times[1:]))
            and math.isclose(factors[-1], 1.0, rel_tol=0.0, abs_tol=1e-12),
            "The diagnostic is not the complete ordered 0.1-to-full-load response")

    source_normals = {
        str(row["group"]): row for row in contract["source_rows"]
        if row.get("role") == "floor_normal" and row.get("intended_law") == "compression_only"
    }
    bindings = {
        str(binding["group"]): binding for binding in contract["bindings"]
        if str(binding["group"]) in source_normals
    }
    require(len(source_normals) == len(bindings) == 100,
            "The exact a12-left model does not bind all 100 source floor normals")

    states: list[dict[str, Any]] = []
    positive_sets: list[set[str]] = []
    for time, factor in zip(times, factors, strict=True):
        rows = []
        for group in sorted(source_normals, key=lambda value: int(value.removeprefix("SPR"))):
            row = interval_source.classify_normal(
                bindings[group], source_normals[group], parsed[time], contract["emitted_nodes"], method,
            )
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
        positive = {row["normal_cell"] for row in rows if row["strictly_positive_bearing"]}
        separated = {row["normal_cell"] for row in rows if row["strictly_separated"]}
        unresolved = {row["normal_cell"] for row in rows if row["classification"] == "UNRESOLVED_INTERVALS"}
        require(len(rows) == 100 and len(positive) + len(separated) + len(unresolved) == 100
                and not (positive & separated or positive & unresolved or separated & unresolved),
                f"A12-left state {time} does not strictly classify all 100 normals")
        positive_sets.append(positive)
        states.append({
            "time": float(time),
            "load_factor": float(factor),
            "strict_positive_bearing_count": len(positive),
            "strictly_separated_count": len(separated),
            "unresolved_count": len(unresolved),
            "input_mask_mismatch_count": sum(
                row["input_mask_compatibility"] != "CONSISTENT_WITH_PROPOSED_BRANCH" for row in rows
            ),
            "rows": rows,
        })

    stable = all(values == positive_sets[0] for values in positive_sets[1:])
    require(stable, "Strict-positive cell set changes across the seven a12-left states")
    final_rows = states[-1]["rows"]
    exceptions = []
    for row in final_rows:
        if row["input_mask_compatibility"] != "CONSISTENT_WITH_PROPOSED_BRANCH":
            same = all(
                next(item for item in state["rows"] if item["source_group"] == row["source_group"])["classification"]
                == row["classification"] for state in states
            )
            exceptions.append({
                "source_group": row["source_group"],
                "normal_cell": row["normal_cell"],
                "proposed_input_state": "selected_bearing" if row["source_group_selected_in_proposed_input"] else "released_inactive",
                "observed_interval_classification": row["classification"],
                "compatibility_exception": row["input_mask_compatibility"],
                "same_classification_all_seven_increments": same,
            })
            require(same, f"Exception {row['source_group']} changes classification between states")

    source_map = {
        str((ATTEMPT / name).relative_to(ROOT)): digest for name, digest in ATTEMPT_PINS.items()
    }
    source_map.update({str((CONTROL / name).relative_to(ROOT)): digest for name, digest in CONTROL_PINS.items()})
    source_map.update({str(path.relative_to(ROOT)): digest for path, digest in LINEAGE_PINS.items()})
    source_map.update({str(path.relative_to(ROOT)): digest for path, digest in METHOD_FILES.items()})
    source_map[str(SOURCE_PRODUCER.relative_to(ROOT))] = SOURCE_PRODUCER_SHA256
    source_map[str(RESPONSE_WRITER.relative_to(ROOT))] = RESPONSE_WRITER_SHA256

    return {
        "schema": "current_springa_selected_floor_normal_interval_diagnostic/v1",
        "status": "COMPLETED_NORMAL_LAW_DIAGNOSTIC_ONLY_PROPOSED_BRANCH_REJECTED",
        "case_id": "a12-left",
        "candidate": record["candidate"],
        "geometry_revision_id": record["geometry_revision_id"],
        "selected_floor_branch_id": branch["branch_id"],
        "native_case_terminal_status": terminal["status"],
        "source_selected_bearing_count": len(selected),
        "source_released_inactive_count": 100 - len(selected),
        "printed_state_count": len(states),
        "normal_count_per_state": 100,
        "full_factor_1_reached": True,
        "strict_positive_cell_set_stable_all_states": stable,
        "strict_positive_cells_at_final_state": sorted(positive_sets[-1]),
        "input_selected_cells_not_strictly_positive": sorted({
            row["normal_cell"] for row in final_rows
            if row["source_group_selected_in_proposed_input"] and not row["strictly_positive_bearing"]
        }),
        "input_inactive_cells_strictly_positive": sorted({
            row["normal_cell"] for row in final_rows
            if not row["source_group_selected_in_proposed_input"] and row["strictly_positive_bearing"]
        }),
        "compatibility_exception_count": len(exceptions),
        "compatibility_exceptions": exceptions,
        "states": states,
        "lineage": {
            "original_all_bearing_physics_control": str(CONTROL.relative_to(ROOT)),
            "direct_rejected_selected_10_attempt": str(ATTEMPT.relative_to(ROOT)),
            "fresh_case_model": str(FRESH_MODEL.relative_to(ROOT)),
            "canonical_case_load_register": str(REGISTER.relative_to(ROOT)),
            "original_all_bearing_screen": str(ALL_BEARING_SCREEN.relative_to(ROOT)),
            "rejected_response_forces_adopted": False,
            "other_case_response_states_reused": False,
            "normal_springa_carriers_changed_by_diagnostic": False,
        },
        "provenance": {
            "source_sha256": source_map,
            "producer_sha256": sha(Path(__file__)),
            "source_interval_producer_path": str(SOURCE_PRODUCER.relative_to(ROOT)),
            "source_interval_producer_sha256": SOURCE_PRODUCER_SHA256,
            "zero_u_wrapper_path": str((ZERO_U_DIR / "response_audit.py").relative_to(ROOT)),
            "zero_u_wrapper_sha256": METHOD_FILES[ZERO_U_DIR / "response_audit.py"],
            "stable_parser_sha256": METHOD_FILES[ZERO_U_DIR / "stable_response_audit.py"],
            "proof_replay_sha256": METHOD_FILES[ZERO_U_DIR / "zero_u_token_replay.json"],
            "terminal_validation": run_validation,
        },
        "claims": {
            "diagnostic_only": True,
            "zero_u_only_representation_rule_used": True,
            "nonzero_u_rounding_and_all_rf_rounding_retained": True,
            "geometric_subtraction_arithmetic_guard_retained": True,
            "all_100_normals_classified_at_all_7_states": True,
            "strict_positive_set_stable_at_all_7_states": True,
            "physical_connection_force_export_performed": False,
            "corner_demands_usable": False,
            "physical_failure_inferred": False,
            "selected_floor_branch_accepted": False,
            "floor_mask_or_iteration_proposed_by_diagnostic": False,
            "native_run_performed_by_this_producer": False,
            "numerical_ground_rf_is_not_a_physical_support_reaction": True,
        },
        "limits": [
            "Intervals bound printed DAT representation and stated arithmetic guards, not nonlinear solver residual, convergence error, pre-format underflow, or the exact continuum solution.",
            "The source selected-10 run is rejected at SPR1302; its force response is not adopted or exported.",
            "The strict-positive set is a diagnostic classification from this exact a12-left run only; it is not a selected support response or a physical floor reaction.",
            "No corner demand, resistance, structural adequacy, joint acceptance, or floor qualification is established.",
        ],
    }


def main() -> None:
    out = HERE / "a12-left-normal-intervals.json"
    pins = HERE / "source-pins.json"
    require(not out.exists() and not pins.exists(), "Refusing to overwrite existing a12-left diagnostic output")
    report = produce()
    out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    pins.write_text(json.dumps({
        "schema": "current_springa_a12_left_normal_interval_source_pins/v1",
        "producer_path": str(Path(__file__).relative_to(ROOT)),
        "producer_sha256": sha(Path(__file__)),
        "diagnostic_path": str(out.relative_to(ROOT)),
        "diagnostic_sha256": sha(out),
        "source_sha256": report["provenance"]["source_sha256"],
    }, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "case_id": report["case_id"],
        "state_counts": [
            [state["strict_positive_bearing_count"], state["strictly_separated_count"], state["unresolved_count"]]
            for state in report["states"]
        ],
        "stable_positive_cells": report["strict_positive_cells_at_final_state"],
        "exceptions": report["compatibility_exceptions"],
        "diagnostic_sha256": sha(out),
        "producer_sha256": sha(Path(__file__)),
    }, indent=2))


if __name__ == "__main__":
    main()
