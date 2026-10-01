#!/usr/bin/env python3
"""Source-bound K12-right 100-normal, seven-state zero-U interval diagnosis."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[5]
SERIES = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = Path(__file__).resolve().parent
RUN = SERIES / "current-springa-selected-floor-k12-right-attempt01"
REGISTER = SERIES / "current-six-case-source-load-register-attempt01/register.json"
FRESH_MODEL = SERIES / "current-springa-six-case-frame-input-adapter-attempt01/k12-right/model.json"
SOURCE_SCREEN = SERIES / "current-springa-k12-right-floor-screen-attempt01/screen.json"
CONTROL = SERIES / "current-springa-frame-k12-right-all-bearing-attempt01"
METHOD_DIAGNOSTIC = SERIES / "current-springa-selected-floor-normal-interval-diagnostic-attempt01/produce.py"
METHOD_DIR = SERIES / "current-springa-zero-u-token-response-audit-attempt01"
METHOD_WRAPPER = METHOD_DIR / "response_audit.py"
METHOD_STABLE = METHOD_DIR / "stable_response_audit.py"
METHOD_REPLAY = METHOD_DIR / "zero_u_token_replay.json"
METHOD_REPLAY_PRODUCER = METHOD_DIR / "replay_zero_u_tokens.py"
METHOD_README = METHOD_DIR / "README.md"
KERNEL = SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py"
ADAPTER02 = SERIES / "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py"
PARENT_INPUT_CHECK = SERIES / "current-springa-case-bound-parent-input-audit-attempt01/check.py"
PRIOR_SCREEN = SERIES / "current-springa-k12-right-selected-floor-screen-attempt02/screen.json"
OUTPUT = HERE / "k12-right-normal-intervals.json"
SCREEN_OUTPUT = HERE / "screen.json"

PINNED_SOURCE_SHA256 = {
    "current-springa-selected-floor-k12-right-attempt01/model.json": "0954343b2af9ca2a9caed8a48cb7e142d77729c2a12192b77b727db428317294",
    "current-springa-selected-floor-k12-right-attempt01/model.inp": "aef1216c8f1196736208f680aa6147e1b36b8f7b28a437998a7d5e6beb7e9fee",
    "current-springa-selected-floor-k12-right-attempt01/model.dat": "14b628ee4968fde71cf3261ddb42618e1795b0c50930ab3a4f7e9a3ef9ae6f6a",
    "current-springa-selected-floor-k12-right-attempt01/execution.json": "d1df4892b695a5307caea17e16ca91fa0695a2648297bcbca4788fd947294be5",
    "current-springa-selected-floor-k12-right-attempt01/freeze.json": "93798bce61f17d0a89e12eec7a2dce7fe0e215b3615012f049739fef17f275f5",
    "current-springa-selected-floor-k12-right-attempt01/authorization.json": "bd9648b9e74e23c94e3ee5887c3a9cd26ddec197e6032de9a85b116fc07ca066",
    "current-springa-selected-floor-k12-right-attempt01/case-context.json": "6f9fdab0676389ed79f4e100241adfc6fdc83c36d7a64faad098c79f84f230c3",
    "current-springa-selected-floor-k12-right-attempt01/parent-serialized-input-audit.json": "c4dbfbb65d6d861ac80ec653b75781e2fe41dce740bb629bda894ca56a0176c5",
    "current-springa-selected-floor-k12-right-attempt01/parent-terminal-assessment.json": "412fba9eeca95cc535f0570e74dc90c3d3fcf4426e32a259982f1f0767996227",
    "current-springa-selected-floor-k12-right-attempt01/parent-case-context-check.json": "e5c6f0215f1a65f4ffd0a2ef7effe87ced8f9c1188a0f42a1048aa5c7b3612cf",
    "current-springa-selected-floor-k12-right-attempt01/parent-readiness-review.json": "c4d82251d9195d6f7e8f3c3252767fd775b984f36146ccba5fdc107bafdfd8e6",
    "current-springa-selected-floor-k12-right-attempt01/native.stdout": "bd55c941941694b7d4896f006ae4bb70c34467ae775386ad4d57f890fa4ab8cb",
    "current-springa-selected-floor-k12-right-attempt01/native.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "current-six-case-source-load-register-attempt01/register.json": "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508",
    "current-springa-six-case-frame-input-adapter-attempt01/k12-right/model.json": "4766c0b06693c15e80758494fb7b2a566eb823089e82d29e0a72182b47e89868",
    "current-springa-k12-right-floor-screen-attempt01/screen.json": "4e0d0cc3b039a43a6df1f287b345ad51006b8db1fcfb05e340093573f6e2ac18",
    "current-springa-frame-k12-right-all-bearing-attempt01/model.json": "f99e6ecbcb3088dca8a740024b92736fd50df2c394a01f25303c14540125f6d9",
    "current-springa-frame-k12-right-all-bearing-attempt01/model.inp": "fcc6be805a0169dd89628872af29a09e878448313c9f594d09fd15586acbf68f",
    "current-springa-frame-k12-right-all-bearing-attempt01/model.dat": "76fd45d0aae2520d90327643c77c47e34babe941eb511c848ab4ef600a313c84",
    "current-springa-frame-k12-right-all-bearing-attempt01/execution.json": "baed9ffbe3854d6709ea378619f406212b50fc4f94fdef120470ed322f56641c",
    "current-springa-frame-k12-right-all-bearing-attempt01/freeze.json": "98f1c701b084fac128d0d7b9a50909546c6867d3986a93abdb1c6222515e8bf2",
    "current-springa-frame-k12-right-all-bearing-attempt01/authorization.json": "3237dd13309ebab8aec30d9edeb5a2dc319c43005ac612859b4a2ecc6704c3a7",
    "current-springa-frame-k12-right-all-bearing-attempt01/parent-serialized-input-audit.json": "7c66bc4771b8de8a4198ba1299e36fb404e8baf9bc0d1da491e20a3bbc977f6e",
    "current-springa-frame-response-audit-attempt01/response_audit.py": "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
    "current-springa-zero-u-token-response-audit-attempt01/response_audit.py": "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
    "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py": "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    "current-springa-zero-u-token-response-audit-attempt01/zero_u_token_replay.json": "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1",
    "current-springa-zero-u-token-response-audit-attempt01/replay_zero_u_tokens.py": "6b49312429c78e04d0a70a7a428382028ac9e75ab01a69b53271d9feca91bd32",
    "current-springa-zero-u-token-response-audit-attempt01/README.md": "ef2c8d33ac9e48566c8b5c96f8ae4a0fa0216ff00fa1bc3aa6d7e3c0f76f0d49",
    "current-springa-selected-floor-normal-interval-diagnostic-attempt01/produce.py": "02f1292caf7b1bc1b5bbaca73bdbd4f7c3f7eb4c727a755eb69e458d00d49cd8",
    "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py": "1e9edd6d8d1a341c3cd70854710dd80431438f7287e425b1c3e62d94d0f963bc",
    "current-springa-case-bound-parent-input-audit-attempt01/check.py": "cc4db4e8b6455b42f2230dd5284ecbae4c77d29e4165c466d1681d61bfd29b1d",
    "current-springa-k12-right-selected-floor-screen-attempt02/screen.json": "f8072ba3b958fc1ade2478c59d2f0cf42218432d01b9a77842f877bb55f31701",
    "current-springa-k12-right-selected-floor-screen-attempt02/audit.json": "faacaabac33a32896a282d956c70df073b4e5c396a22d51747db856bff72a21e",
    "current-springa-k12-right-selected-floor-screen-attempt02/source-pins.json": "ee70b1be98f188c219800efd52916ed1bd9e21082d2b4d026f72e0ad9e6ef7ca",
}


class DiagnosticError(ValueError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DiagnosticError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected_json_object:{path}")
    return value


def canonical_sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_sources() -> dict[str, str]:
    observed: dict[str, str] = {}
    for suffix, expected in PINNED_SOURCE_SHA256.items():
        relative = SERIES / suffix
        path = ROOT / relative
        require(path.is_file(), f"pinned_source_exists:{relative}")
        actual = sha(path)
        require(actual == expected, f"pinned_source_sha256:{relative}")
        observed[str(relative)] = actual
    return observed


def import_prior_diagnostic():
    spec = importlib.util.spec_from_file_location("pinned_floor_normal_interval_classifier", ROOT / METHOD_DIAGNOSTIC)
    require(spec is not None and spec.loader is not None, "pinned_normal_interval_classifier_loads")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_case_authority(model: dict[str, Any], context: dict[str, Any], register: dict[str, Any],
                            execution: dict[str, Any], freeze: dict[str, Any], authorization: dict[str, Any],
                            parent_input: dict[str, Any], terminal: dict[str, Any],
                            context_check: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    require(model.get("case_id") == context.get("case_id") == "k12-right", "exact_k12_right_case_identity")
    require(model.get("candidate") == context.get("candidate") and model.get("geometry_revision_id") == context.get("geometry_revision_id"), "case_candidate_revision_binding")
    require(context.get("selected_input_model_json_path") == str((ROOT / RUN / "model.json").resolve()), "context_exact_model_path")
    require(context.get("selected_input_deck_path") == str((ROOT / RUN / "model.inp").resolve()), "context_exact_deck_path")
    require(context.get("selected_input_model_json_sha256") == sha(ROOT / RUN / "model.json"), "context_exact_model_hash")
    require(context.get("selected_input_deck_sha256") == sha(ROOT / RUN / "model.inp"), "context_exact_deck_hash")
    require(context.get("source_case_load_register_path") == str(REGISTER), "context_exact_register_path")
    require(context.get("source_case_load_register_sha256") == sha(ROOT / REGISTER), "context_register_hash")
    require(register.get("status") == "PASS_FRESH_SIX_CASE_SOURCE_LOAD_WRENCH_REGISTER" and register.get("candidate") == model.get("candidate") and register.get("geometry_revision_id") == model.get("geometry_revision_id"), "passing_source_load_register_identity")
    rows = [row for row in register.get("cases", []) if row.get("case_id") == "k12-right"]
    require(len(rows) == 1 and canonical_sha(rows[0]) == context.get("case_record_sha256"), "exact_registered_case_record")
    require(model.get("source_model_inputs_sha256") == context.get("source_model_inputs_sha256") == rows[0].get("source_model_inputs_sha256"), "fresh_case_source_input_digest")

    branch = model.get("floor_branch_metadata", {})
    selected = list(map(str, branch.get("selected_cells", [])))
    inactive = list(map(str, branch.get("inactive_cells", [])))
    require(set(selected) == set(context.get("selected_cells", [])) and set(inactive) == set(context.get("inactive_cells", [])), "model_context_exact_selected_and_inactive_cells")
    require(len(selected) == int(context.get("selected_floor_cell_count", -1)) == 10, "exact_input_selected_normal_count")
    require(len(inactive) == int(context.get("inactive_floor_cell_count", -1)) == 90, "exact_input_inactive_normal_count")
    require(int(context.get("active_original_tangent_row_count", -1)) == 20 and int(context.get("inactive_original_tangent_row_count", -1)) == 180, "exact_input_tangent_row_partition")
    require(branch.get("physical_force_adoption") is False and branch.get("automatic_mask_iteration_authorized") is False, "selected10_input_remains_diagnostic_only")
    require(context.get("diagnostic_floor_screen_status") == "REJECTED_ALL_BEARING_SUPPORT_BRANCH" and context.get("screen_positive_forces_or_active_states_reused_as_response") is False, "original_screen_is_context_only")

    require(execution.get("run_id") == "springa-selected-k12-right-attempt01" and execution.get("native_solve_executed") is True and execution.get("returncode") == 0 and execution.get("container_confirmed_terminal") is True, "exact_prior_terminal_run")
    output_hashes = execution.get("outputs_sha256", {})
    require(output_hashes.get("model.json") == sha(ROOT / RUN / "model.json") and output_hashes.get("model.inp") == sha(ROOT / RUN / "model.inp") and output_hashes.get("model.dat") == sha(ROOT / RUN / "model.dat"), "execution_output_hashes")
    require(freeze.get("files_sha256", {}).get("model.json") == sha(ROOT / RUN / "model.json") and freeze.get("files_sha256", {}).get("model.inp") == sha(ROOT / RUN / "model.inp"), "original_freeze_binds_input_model_deck")
    require(authorization.get("input_freeze_sha256") == sha(ROOT / RUN / "freeze.json") and authorization.get("native_execution_authorized") is True and authorization.get("mechanical_acceptance") is False, "original_run_authority_and_limit")
    require(parent_input.get("status") == "PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT" and parent_input.get("case_id") == "k12-right" and parent_input.get("proposed_branch_accepted") is False and parent_input.get("corner_demands_usable") is False, "parent_input_proof_is_input_only")
    require(context_check.get("status") == "PASS_FROZEN_CASE_BOUND_INPUT_CONTRACT_ONLY" and context_check.get("native_response_consumed") is False, "parent_context_check_is_input_only")
    require(terminal.get("status") == "REJECTED_SELECTED_FLOOR_SUPPORT_BRANCH" and terminal.get("case_id") == "k12-right" and terminal.get("corner_demands_usable") is False and terminal.get("physical_joint_failure_demonstrated") is False and terminal.get("mechanical_acceptance") is False, "existing_selected10_terminal_stays_rejected")
    require(terminal.get("model_sha256") == sha(ROOT / RUN / "model.json") and terminal.get("deck_sha256") == sha(ROOT / RUN / "model.inp") and terminal.get("dat_sha256") == sha(ROOT / RUN / "model.dat"), "terminal_record_exact_input_hashes")
    require(readiness.get("input_freeze_sha256") == sha(ROOT / RUN / "freeze.json") and readiness.get("ready_for_scoped_native_run") is True and readiness.get("joint_acceptance") is False, "readiness_record_matches_exact_frozen_run")
    require(readiness.get("original_leg_runner_resistance_reopened") is False, "original_twelve_resistances_not_reopened")
    return {
        "case_id": "k12-right",
        "case_record_sha256": canonical_sha(rows[0]),
        "register_path": str(REGISTER),
        "register_sha256": sha(ROOT / REGISTER),
        "source_model_inputs_sha256": context["source_model_inputs_sha256"],
        "selected10_run_model_sha256": sha(ROOT / RUN / "model.json"),
        "selected10_run_deck_sha256": sha(ROOT / RUN / "model.inp"),
        "selected10_run_dat_sha256": sha(ROOT / RUN / "model.dat"),
        "selected10_case_context_path": str(RUN / "case-context.json"),
        "selected10_case_context_sha256": sha(ROOT / RUN / "case-context.json"),
        "original_rejected_terminal_status": terminal["status"],
        "original_terminal_auditor_sha256": terminal.get("response_auditor_sha256"),
        "this_interval_method_is_zero_u_711": True,
        "source_positive_mask_for_new_input_derived_from_k12_right_native_rows_only": True,
        "a12_or_a1_force_or_mask_reused": False,
    }


def build_outputs(source_hashes: dict[str, str], diagnostic: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    model = load(ROOT / RUN / "model.json")
    deck = (ROOT / RUN / "model.inp").read_text(encoding="utf-8")
    data = (ROOT / RUN / "model.dat").read_text(encoding="utf-8", errors="replace")
    context = load(ROOT / RUN / "case-context.json")
    register = load(ROOT / REGISTER)
    execution = load(ROOT / RUN / "execution.json")
    freeze = load(ROOT / RUN / "freeze.json")
    authorization = load(ROOT / RUN / "authorization.json")
    parent_input = load(ROOT / RUN / "parent-serialized-input-audit.json")
    terminal = load(ROOT / RUN / "parent-terminal-assessment.json")
    context_check = load(ROOT / RUN / "parent-case-context-check.json")
    readiness = load(ROOT / RUN / "parent-readiness-review.json")
    case_authority = validate_case_authority(model, context, register, execution, freeze, authorization, parent_input, terminal, context_check, readiness)

    method = diagnostic.load_method()
    contract = method._validate_model(model, deck, context)
    terminal_validation = method._validate_execution(
        ROOT / RUN / "model.json", ROOT / RUN / "model.dat", ROOT / RUN / "model.inp",
        ROOT / RUN / "execution.json", data, context,
    )
    parsed = method.parse_native_blocks(data)
    require(len(parsed) == 7, "seven_parsed_DAT_states")
    expected_nodes = set(map(int, model["nodes"]))
    require(all(set(state["u"]) == expected_nodes and set(state["rf"]) == expected_nodes for state in parsed.values()), "complete_U_RF_node_inventory_each_state")
    times = sorted(parsed)
    factors = [float(method.load_scale(time, float(contract["total_time"]))) for time in times]
    require(all(right > left for left, right in zip(times, times[1:])) and math.isclose(factors[-1], 1.0, rel_tol=0.0, abs_tol=1e-12), "all_seven_increments_through_full_load")

    source_normals = {
        str(row["group"]): row for row in contract["source_rows"]
        if row.get("role") == "floor_normal" and row.get("intended_law") == "compression_only"
    }
    bindings = {str(binding["group"]): binding for binding in contract["bindings"] if str(binding["group"]) in source_normals}
    require(len(source_normals) == len(bindings) == 100, "exact_100_source_bound_floor_normals")
    input_selected = set(map(str, context["selected_cells"]))
    input_inactive = set(map(str, context["inactive_cells"]))
    require(len(input_selected) == 10 and len(input_inactive) == 90 and input_selected.isdisjoint(input_inactive) and len(input_selected | input_inactive) == 100, "selected10_input_partitions_100_normals")

    states: list[dict[str, Any]] = []
    strict_positive_sets: list[set[str]] = []
    screen_states: list[dict[str, Any]] = []
    for state_index, (time, factor) in enumerate(zip(times, factors, strict=True)):
        state = parsed[time]
        rows = []
        screen_rows = []
        for group in sorted(source_normals, key=lambda item: int(item.removeprefix("SPR"))):
            binding, source = bindings[group], source_normals[group]
            row = diagnostic.classify_normal(binding, source, state, contract["emitted_nodes"], method)
            row["source_group_selected_in_input"] = row["normal_cell"] in input_selected
            row["input_mask_compatibility"] = (
                "SELECTED_BUT_STRICTLY_SEPARATED" if row["normal_cell"] in input_selected and row["strictly_separated"]
                else "INACTIVE_BUT_STRICTLY_BEARING" if row["normal_cell"] in input_inactive and row["strictly_positive_bearing"]
                else "UNRESOLVED_INTERVAL" if row["classification"] == "UNRESOLVED_INTERVALS"
                else "CONSISTENT_WITH_SELECTED10_INPUT"
            )
            rows.append(row)
            screen_rows.append({
                "cell_name": row["normal_cell"],
                "source_group": row["source_group"],
                "physical_owner": binding["physical_owner"],
                "classification": (
                    "STRICTLY_POSITIVE" if row["strictly_positive_bearing"]
                    else "STRICTLY_SEPARATED" if row["strictly_separated"] else "UNRESOLVED_INTERVALS"
                ),
                "strictly_positive_after_rounding": row["strictly_positive_bearing"],
                "strictly_separating_after_rounding": row["strictly_separated"],
                "input_mask_status": "selected" if row["normal_cell"] in input_selected else "inactive",
                "q_interval_mm": row["projected_q_interval_mm"],
                "geometric_elongation_interval_mm": row["geometric_spring_elongation_interval_mm"],
            })
        require(len(rows) == len(screen_rows) == 100, f"state_{state_index}_all_normals")
        positive = {row["normal_cell"] for row in rows if row["strictly_positive_bearing"]}
        separated = {row["normal_cell"] for row in rows if row["strictly_separated"]}
        unresolved = {row["normal_cell"] for row in rows if row["classification"] == "UNRESOLVED_INTERVALS"}
        require(len(positive) + len(separated) + len(unresolved) == 100 and not (positive & separated or positive & unresolved or separated & unresolved), f"state_{state_index}_strict_classification_partition")
        strict_positive_sets.append(positive)
        states.append({
            "time": time,
            "load_factor": factor,
            "strict_positive_bearing_count": len(positive),
            "strictly_separated_count": len(separated),
            "unresolved_count": len(unresolved),
            "input_selected_but_separated_count": len(input_selected & separated),
            "input_inactive_but_positive_count": len(input_inactive & positive),
            "rows": rows,
        })
        screen_states.append({
            "time": time,
            "bearing_count": len(positive),
            "separating_count": len(separated),
            "rows": screen_rows,
        })

    stable = all(positive == strict_positive_sets[0] for positive in strict_positive_sets[1:])
    fully_resolved = all(state["unresolved_count"] == 0 for state in states)
    require(stable and fully_resolved, "one_proposal_eligibility_requires_strict_stable_all_100_all_7")
    observed_positive = strict_positive_sets[-1]
    observed_separated = set(source_normals.keys())  # overwritten below from cell names
    observed_separated = {row["normal_cell"] for row in states[-1]["rows"] if row["strictly_separated"]}
    selected_but_separated = input_selected & observed_separated
    inactive_but_positive = input_inactive & observed_positive

    prior_screen = load(ROOT / PRIOR_SCREEN)
    require(prior_screen.get("case_id") == "k12-right", "prior_screen_same_case_for_crosscheck")
    screen_hashes = dict(source_hashes)
    producer_hash = sha(Path(__file__).resolve())
    diagnostic_report = {
        "schema": "current_springa_k12_right_normal_interval_diagnostic/v1",
        "status": "STRICT_STABLE_MASK_IDENTIFIED_INPUT_PROPOSAL_ELIGIBLE",
        "case_id": "k12-right",
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "selected_floor_branch_id": model["floor_branch_metadata"]["branch_id"],
        "current_selected_input_cells": sorted(input_selected),
        "current_inactive_input_cells": sorted(input_inactive),
        "input_selected_count": len(input_selected),
        "input_inactive_count": len(input_inactive),
        "strict_711_normal_diagnosis": {
            "method": "pinned zero-U wrapper and stable parser from current-springa-zero-u-token-response-audit-attempt01",
            "wrapper_path": str(SERIES / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"),
            "wrapper_sha256": PINNED_SOURCE_SHA256["current-springa-zero-u-token-response-audit-attempt01/response_audit.py"],
            "all_floor_normals_checked_per_state": 100,
            "native_increment_count": len(states),
            "full_load_factor_reached": factors[-1],
            "all_states_full_factor_progression": [state["load_factor"] for state in states],
            "strict_classifications_stable_all_seven_states": stable,
            "all_100_normals_strictly_classified_all_seven_states": fully_resolved,
            "strict_positive_count_per_state": [state["strict_positive_bearing_count"] for state in states],
            "strictly_separated_count_per_state": [state["strictly_separated_count"] for state in states],
            "unresolved_count_per_state": [state["unresolved_count"] for state in states],
            "observed_stable_positive_cells": sorted(observed_positive),
            "observed_stable_separated_cells": sorted(observed_separated),
            "input_selected_but_separated_cells": sorted(selected_but_separated),
            "input_inactive_but_positive_cells": sorted(inactive_but_positive),
            "input_mask_mismatch_count_per_state": [state["input_selected_but_separated_count"] + state["input_inactive_but_positive_count"] for state in states],
            "states": states,
        },
        "source_authority": case_authority,
        "parent_original_input_audit": {
            "path": str(RUN / "parent-serialized-input-audit.json"),
            "sha256": sha(ROOT / RUN / "parent-serialized-input-audit.json"),
            "status": parent_input["status"],
            "input_only": True,
            "proposed_branch_accepted": False,
            "corner_demands_usable": False,
        },
        "prior_non_711_screen_crosscheck_only": {
            "path": str(PRIOR_SCREEN),
            "sha256": sha(ROOT / PRIOR_SCREEN),
            "status": prior_screen["status"],
            "same_positive_cell_set_at_all_printed_times": prior_screen.get("same_positive_cell_set_at_all_printed_times"),
            "diagnostic_interval_ambiguous_count_at_final_time": prior_screen.get("diagnostic_interval_ambiguous_count_at_final_time"),
            "used_as_711_classification_authority": False,
        },
        "screen_path_for_single_case_input_proposal": str(SCREEN_OUTPUT.relative_to(ROOT)),
        "screen_sha256": "computed-after-serialization",
        "one_case_local_input_proposal": {
            "eligible": True,
            "selected_cells_from_this_k12_right_response_only": sorted(observed_positive),
            "selected_cell_count": len(observed_positive),
            "inactive_cell_count": 100 - len(observed_positive),
            "input_adapter": str(ADAPTER02),
            "input_adapter_sha256": PINNED_SOURCE_SHA256[str(ADAPTER02.relative_to(SERIES))],
            "parent_input_check": str(PARENT_INPUT_CHECK),
            "parent_input_check_sha256": PINNED_SOURCE_SHA256[str(PARENT_INPUT_CHECK.relative_to(SERIES))],
            "proposal_is_not_native_or_response_acceptance": True,
            "new_native_run_performed": False,
            "forces_promoted": False,
        },
        "artifact_provenance": {
            "source_file_sha256": screen_hashes,
            "normal_interval_method_source_path": str(METHOD_DIAGNOSTIC),
            "normal_interval_method_source_sha256": PINNED_SOURCE_SHA256[str(METHOD_DIAGNOSTIC.relative_to(SERIES))],
            "producer_path": str(Path(__file__).resolve().relative_to(ROOT)),
            "producer_sha256": producer_hash,
            "711_terminal_output_validation": terminal_validation,
            "terminal_response_gates_passed": False,
        },
        "claims": {
            "read_only_diagnostic": True,
            "all_100_normal_cells_checked_at_all_seven_increments": True,
            "input_mask_selected10_rejected": True,
            "one_case_local_right_input_only_prepared_if_exact_pattern_strict_and_stable": True,
            "physical_connector_force_exported": False,
            "native_solve_launched_by_this_producer": False,
            "floor_capacity_or_friction_qualified": False,
            "original_12_leg_runner_resistances_reopened": False,
            "joint_or_mechanical_acceptance": False,
        },
        "limits": [
            "The native response was produced for the selected-10/released-90 mask and its parent terminal status remains rejected. Normal interval classifications diagnose that exact response; they are not an equilibrium response for the newly identified mask.",
            "The one proposed mask only identifies a source-bound case-local input candidate. It has not been solved, force-audited, or accepted.",
            "Intervals bound printed DAT representation and specified arithmetic guards only; they do not bound solver residual, convergence error, pre-format underflow, or continuum solution error.",
            "No a12 or A1 force, active set, or response is reused. No physical connection forces, joint capacities, floor friction/anchorage, or original LEG/RUNNER resistance are inferred.",
        ],
    }
    screen = {
        "schema": "current_case_bound_floor_diagnostic_screen/v1",
        "case_id": "k12-right",
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "status": "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH",
        "diagnostic_stage": "selected-proposal-all-normal-711-interval-classification",
        "selected_floor_branch_id": model["floor_branch_metadata"]["branch_id"],
        "corner_demands_usable": False,
        "physical_force_adoption": False,
        "mechanical_acceptance": False,
        "qualified_for_design": False,
        "frame_ready_for_native_run": False,
        "full_step_native_convergence": True,
        "all_printed_floor_laws_checked": True,
        "all_printed_times": [state["time"] for state in states],
        "same_positive_cell_set_at_all_printed_times": stable,
        "positive_cell_set_stable_across_all_printed_times": stable,
        "input_selected_cells": sorted(input_selected),
        "input_inactive_cells": sorted(input_inactive),
        "input_selected_cell_count": len(input_selected),
        "input_inactive_cell_count": len(input_inactive),
        "diagnostic_positive_cells_at_final_time": sorted(observed_positive),
        "diagnostic_separating_cells_at_final_time": sorted(observed_separated),
        "diagnostic_interval_ambiguous_cells_at_final_time": [],
        "diagnostic_positive_cell_count_at_final_time": len(observed_positive),
        "diagnostic_separating_cell_count_at_final_time": len(observed_separated),
        "diagnostic_interval_ambiguous_count_at_final_time": 0,
        "diagnostic_cell_partition_complete_at_final_time": len(observed_positive | observed_separated) == 100,
        "selected_now_separated": sorted(selected_but_separated),
        "inactive_now_positive": sorted(inactive_but_positive),
        "input_selected_not_strictly_positive": sorted(selected_but_separated),
        "input_inactive_not_strictly_separated": sorted(inactive_but_positive),
        "input_mask_to_final_strict_classification_delta": {
            "selected_cells_released_by_observed_pattern": sorted(selected_but_separated),
            "inactive_cells_selected_by_observed_pattern": sorted(inactive_but_positive),
            "old_mask_rows_different": len(selected_but_separated) + len(inactive_but_positive),
        },
        "native_run_id": execution["run_id"],
        "terminal_run_provenance": {
            "model_sha256": sha(ROOT / RUN / "model.json"),
            "deck_sha256": sha(ROOT / RUN / "model.inp"),
            "dat_sha256": sha(ROOT / RUN / "model.dat"),
            "execution_sha256": sha(ROOT / RUN / "execution.json"),
            "case_context_sha256": sha(ROOT / RUN / "case-context.json"),
            "native_terminal_returncode": execution["returncode"],
            "native_terminal": execution["container_confirmed_terminal"],
        },
        "source_sha256": screen_hashes,
        "classification_method": "Pinned zero-U 711 SPRINGA table, geometric elongation, U/RF endpoint interval classifier; all 100 normals each of seven states.",
        "input_mask_was_read_from_selected_model": True,
        "selected_source_screen_forces_or_active_states_reused_as_response": False,
        "native_solve_executed_by_screen_producer": False,
        "states": screen_states,
        "limits": [
            "Screen uses only the exact k12-right selected10 native state stream and pinned 711 parser. It exports no connector demand force.",
            "Its stable positive mask is one input proposal only; the existing selected10 response is rejected and this mask has not been solved.",
            "No force or active state from a12, A1, or the earlier all-bearing diagnostic screen is reused.",
        ],
    }
    return diagnostic_report, screen


def write_or_verify(write: bool) -> None:
    source_hashes = verify_sources()
    diagnostic = import_prior_diagnostic()
    report, screen = build_outputs(source_hashes, diagnostic)
    screen_text = json.dumps(screen, indent=2, sort_keys=True, allow_nan=False) + "\n"
    screen_hash = hashlib.sha256(screen_text.encode("utf-8")).hexdigest()
    report["screen_sha256"] = screen_hash
    report_text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if write:
        HERE.mkdir(parents=True, exist_ok=True)
        SCREEN_OUTPUT.write_text(screen_text, encoding="utf-8")
        OUTPUT.write_text(report_text, encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "case_id": report["case_id"],
            "strict_positive_count_each_state": report["strict_711_normal_diagnosis"]["strict_positive_count_per_state"],
            "separated_count_each_state": report["strict_711_normal_diagnosis"]["strictly_separated_count_per_state"],
            "unresolved_count_each_state": report["strict_711_normal_diagnosis"]["unresolved_count_per_state"],
            "selected_but_separated": report["strict_711_normal_diagnosis"]["input_selected_but_separated_cells"],
            "inactive_but_positive": report["strict_711_normal_diagnosis"]["input_inactive_but_positive_cells"],
            "proposal_eligible": report["one_case_local_input_proposal"]["eligible"],
            "screen_sha256": screen_hash,
        }, indent=2))
    else:
        require(OUTPUT.is_file() and SCREEN_OUTPUT.is_file(), "diagnostic_report_and_screen_exist")
        saved_report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        saved_screen = json.loads(SCREEN_OUTPUT.read_text(encoding="utf-8"))
        require(saved_report == json.loads(report_text), "K12_right_normal_interval_report_reproduces")
        require(saved_screen == json.loads(screen_text), "K12_right_adapter_screen_reproduces")
        require(sha(SCREEN_OUTPUT) == screen_hash, "K12_right_screen_sha256")
        print("verified frozen K12-right 711 inputs, all 700 normal classifications, stable observed mask, and case-local screen")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    write_or_verify(args.write)


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError) as error:
        print(f"K12_RIGHT_711_DIAGNOSTIC_BLOCKED: {error}", file=sys.stderr)
        raise
