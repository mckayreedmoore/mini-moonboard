#!/usr/bin/env python3
"""Classify K12-right attempt02 floor normals and compare prior masks; read-only."""
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
RUN = SERIES / "current-springa-selected-floor-k12-right-attempt02"
REGISTER = SERIES / "current-six-case-source-load-register-attempt01/register.json"
FRESH_MODEL = SERIES / "current-springa-six-case-frame-input-adapter-attempt01/k12-right/model.json"
CONTROL = SERIES / "current-springa-frame-k12-right-all-bearing-attempt01"
ATTEMPT03 = SERIES / "current-springa-case-bound-floor-input-adapter-attempt03/k12-right"
ATTEMPT11 = SERIES / "current-springa-case-bound-floor-input-adapter-attempt11/k12-right"
PRIOR_REPORT = SERIES / "current-springa-k12-right-normal-interval-diagnostic-attempt01/k12-right-normal-intervals.json"
PRIOR_SCREEN = SERIES / "current-springa-k12-right-normal-interval-diagnostic-attempt01/screen.json"
INTERVAL_METHOD = SERIES / "current-springa-selected-floor-normal-interval-diagnostic-attempt01/produce.py"
OUTPUT = HERE / "k12-right-attempt02-normal-interval-comparison.json"

PINNED_SOURCE_SHA256 = {
    "current-springa-selected-floor-k12-right-attempt02/model.json": "99d6ae6efff6c2da8a473867cfeb833a3726f536f65392ae2121ff24861a114d",
    "current-springa-selected-floor-k12-right-attempt02/model.inp": "f94f315bda1b6d1681f3427d5a93fbb777d7ef901f6a11b78d8762043dac5204",
    "current-springa-selected-floor-k12-right-attempt02/model.dat": "aafa8aaed0f08545ae1588aecd113e0d93def81774c6bc308cdbf8803ad779a9",
    "current-springa-selected-floor-k12-right-attempt02/execution.json": "df1dc1ee144e0375d341e607a01c3f2acbe5b3b53c83d663d19e37bf33ba58fe",
    "current-springa-selected-floor-k12-right-attempt02/freeze.json": "98f937787d88feab3793c58d659fc43db1dd245eec1e45fcbbb713e06bad4d89",
    "current-springa-selected-floor-k12-right-attempt02/authorization.json": "875b0775c60567371f5b93dd89f48f6e3bc4b6f772a71fffe7d7404309463421",
    "current-springa-selected-floor-k12-right-attempt02/case-context.json": "bbfc750df3d443b1bb03d4af930ecb26f1e8b722ded2ba550c8f07497f0de8f8",
    "current-springa-selected-floor-k12-right-attempt02/parent-serialized-input-audit.json": "d1349ff3eb4217fc801f55ba483207c9f6d83bc590ed9e8df1d0d5b316132267",
    "current-springa-selected-floor-k12-right-attempt02/parent-terminal-assessment.json": "faf71852ce4dcfebb8702abf3ccaf59619c6491f14c95669672d7af1ea6a239a",
    "current-springa-selected-floor-k12-right-attempt02/parent-case-context-check.json": "e5c6f0215f1a65f4ffd0a2ef7effe87ced8f9c1188a0f42a1048aa5c7b3612cf",
    "current-springa-selected-floor-k12-right-attempt02/parent-readiness-review.json": "a1daf582cbe949af1a3af20d51586bf00e56fb93e68712ff33295a9ebe2daddf",
    "current-springa-selected-floor-k12-right-attempt02/native.stdout": "cf1297499fb5d4fe04b4e074daffbeacd0508768aa92a3304dab862e04743f69",
    "current-springa-selected-floor-k12-right-attempt02/native.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "current-springa-selected-floor-k12-right-attempt02/model.12d": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "current-springa-selected-floor-k12-right-attempt02/model.cvg": "e2654a97b6043771f05e3b6f29f51f2a5b67455569ff3e052d33ed1ee1a76059",
    "current-springa-selected-floor-k12-right-attempt02/model.frd": "df8debc1b56c6347531ea13e04bc04e5660397acacf0a29d3ee6e9d0fc4d9109",
    "current-springa-selected-floor-k12-right-attempt02/model.sta": "b9e7a39125bf59c7c659433aa14b4ac6f2d008a524851605a638ffd778f8eca7",
    "current-springa-selected-floor-k12-right-attempt02/spooles.out": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "current-six-case-source-load-register-attempt01/register.json": "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508",
    "current-springa-six-case-frame-input-adapter-attempt01/k12-right/model.json": "4766c0b06693c15e80758494fb7b2a566eb823089e82d29e0a72182b47e89868",
    "current-springa-frame-k12-right-all-bearing-attempt01/model.json": "f99e6ecbcb3088dca8a740024b92736fd50df2c394a01f25303c14540125f6d9",
    "current-springa-frame-k12-right-all-bearing-attempt01/model.inp": "fcc6be805a0169dd89628872af29a09e878448313c9f594d09fd15586acbf68f",
    "current-springa-frame-k12-right-all-bearing-attempt01/model.dat": "76fd45d0aae2520d90327643c77c47e34babe941eb511c848ab4ef600a313c84",
    "current-springa-frame-k12-right-all-bearing-attempt01/execution.json": "baed9ffbe3854d6709ea378619f406212b50fc4f94fdef120470ed322f56641c",
    "current-springa-frame-k12-right-all-bearing-attempt01/freeze.json": "98f1c701b084fac128d0d7b9a50909546c6867d3986a93abdb1c6222515e8bf2",
    "current-springa-frame-k12-right-all-bearing-attempt01/authorization.json": "3237dd13309ebab8aec30d9edeb5a2dc319c43005ac612859b4a2ecc6704c3a7",
    "current-springa-frame-k12-right-all-bearing-attempt01/parent-serialized-input-audit.json": "7c66bc4771b8de8a4198ba1299e36fb404e8baf9bc0d1da491e20a3bbc977f6e",
    "current-springa-case-bound-floor-input-adapter-attempt03/k12-right/model.json": "38dbfc61ca20b81a736c9cb17997049f582c6abcdaeb1a65dea17709ab0f6492",
    "current-springa-case-bound-floor-input-adapter-attempt03/k12-right/model.inp": "aef1216c8f1196736208f680aa6147e1b36b8f7b28a437998a7d5e6beb7e9fee",
    "current-springa-case-bound-floor-input-adapter-attempt03/k12-right/audit.json": "79473d4c368839bdbab83946e144eed0a86ca07aa03925efa207fe47efd0d647",
    "current-springa-case-bound-floor-input-adapter-attempt03/k12-right/case-bound-input-context.json": "de8836c10b9e4c836e318fad03ca060e80641403579e3ac9dd050f0ba8d0bb63",
    "current-springa-case-bound-floor-input-adapter-attempt03/k12-right/case-bound-input-context-contract.json": "7ea723e536e38c9c41ecbe119af3ca79c2b748951da551fe4100894c735e9f16",
    "current-springa-case-bound-floor-input-adapter-attempt03/k12-right/source-pins.json": "0ccdf64c0429785e2891d039ec7f13a021cbc99c90c1bf3719870363dbf890ea",
    "current-springa-case-bound-floor-input-adapter-attempt11/k12-right/model.json": "a93af8d6e24e45289889bb39ed1c61420719286c78bac3c5415736fcdcbf21d7",
    "current-springa-case-bound-floor-input-adapter-attempt11/k12-right/model.inp": "f94f315bda1b6d1681f3427d5a93fbb777d7ef901f6a11b78d8762043dac5204",
    "current-springa-case-bound-floor-input-adapter-attempt11/k12-right/audit.json": "fad8fa776c3acd5d2d2509ce4370a4ad5afa77a38290c051a4ee1faed592374d",
    "current-springa-case-bound-floor-input-adapter-attempt11/k12-right/case-bound-input-context.json": "0f0f24c28275a922da9fdcb5c06a623f11a5e4a8e7ea69ff317bcb824d709f05",
    "current-springa-case-bound-floor-input-adapter-attempt11/k12-right/case-bound-input-context-contract.json": "7ea723e536e38c9c41ecbe119af3ca79c2b748951da551fe4100894c735e9f16",
    "current-springa-case-bound-floor-input-adapter-attempt11/k12-right/source-pins.json": "fad2c987972b07ca86098a28a5e70f897b24b867c9a0e129941ccd104e1144d4",
    "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py": "1e9edd6d8d1a341c3cd70854710dd80431438f7287e425b1c3e62d94d0f963bc",
    "current-springa-case-bound-parent-input-audit-attempt01/check.py": "cc4db4e8b6455b42f2230dd5284ecbae4c77d29e4165c466d1681d61bfd29b1d",
    "current-springa-case-bound-parent-report-writer-attempt01/write_report.py": "92ea2e378c486674234b31a1ba384df9a6d5ea94da39c57cd4cb1a33a54e7d39",
    "current-springa-frame-response-audit-attempt01/response_audit.py": "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
    "current-springa-zero-u-token-response-audit-attempt01/response_audit.py": "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
    "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py": "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    "current-springa-zero-u-token-response-audit-attempt01/zero_u_token_replay.json": "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1",
    "current-springa-zero-u-token-response-audit-attempt01/replay_zero_u_tokens.py": "6b49312429c78e04d0a70a7a428382028ac9e75ab01a69b53271d9feca91bd32",
    "current-springa-zero-u-token-response-audit-attempt01/README.md": "ef2c8d33ac9e48566c8b5c96f8ae4a0fa0216ff00fa1bc3aa6d7e3c0f76f0d49",
    "current-springa-selected-floor-normal-interval-diagnostic-attempt01/produce.py": "02f1292caf7b1bc1b5bbaca73bdbd4f7c3f7eb4c727a755eb69e458d00d49cd8",
    "current-springa-k12-right-normal-interval-diagnostic-attempt01/produce.py": "63e0aab21a9972b86191095d219be7a4735a3870213adcefdf54e614b2c14e9b",
    "current-springa-k12-right-normal-interval-diagnostic-attempt01/k12-right-normal-intervals.json": "7be4e1ca61b5c532dbfcf1ed590e6b77091bbfd96c8478f20ae31001b87d96d2",
    "current-springa-k12-right-normal-interval-diagnostic-attempt01/screen.json": "22c6011d36a13981db2a09edda9ce44a16d0058a6de95e44f1e55dfae406d99a",
}

OUTPUT = HERE / "k12-right-attempt02-normal-interval-comparison.json"


class DiagnosticError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DiagnosticError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected_json_object:{path}")
    return value


def canonical_sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_sources() -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, expected in PINNED_SOURCE_SHA256.items():
        path = ROOT / SERIES / relative
        require(path.is_file(), f"pinned_source_exists:{relative}")
        actual = sha(path)
        require(actual == expected, f"pinned_source_sha256:{relative}")
        observed[str(SERIES / relative)] = actual
    return observed


def import_interval_method():
    spec = importlib.util.spec_from_file_location("pinned_k12_right_normal_intervals", ROOT / INTERVAL_METHOD)
    require(spec is not None and spec.loader is not None, "pinned_711_interval_method_loads")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mask_input_record(name: str, directory: Path, expected_stage: str) -> dict[str, Any]:
    model_path = ROOT / directory / "model.json"
    context_path = ROOT / directory / "case-bound-input-context.json"
    audit_path = ROOT / directory / "audit.json"
    model, context, audit = load(model_path), load(context_path), load(audit_path)
    branch = model.get("floor_branch_metadata", {})
    selected = set(map(str, branch.get("selected_cells", [])))
    inactive = set(map(str, branch.get("inactive_cells", [])))
    require(model.get("case_id") == context.get("case_id") == audit.get("case_id") == "k12-right", f"{name}_case_binding")
    require(model.get("candidate") == "compact-floor-flush-wood-joints-development", f"{name}_candidate")
    require(model.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1", f"{name}_geometry_revision")
    require(len(selected) == int(context.get("selected_floor_cell_count", -1)) == 10, f"{name}_ten_selected_cells")
    require(len(inactive) == int(context.get("inactive_floor_cell_count", -1)) == 90, f"{name}_ninety_inactive_cells")
    require(selected == set(context.get("selected_cells", [])) and inactive == set(context.get("inactive_cells", [])), f"{name}_context_mask_match")
    require(branch.get("diagnostic_stage") == expected_stage, f"{name}_expected_stage")
    require(branch.get("physical_force_adoption") is False and branch.get("automatic_mask_iteration_authorized") is False, f"{name}_input_only_no_iteration")
    require(context.get("input_only") is True and context.get("mechanical_acceptance") is False, f"{name}_context_is_input_only")
    return {
        "adapter_attempt": name,
        "model_path": str(directory / "model.json"),
        "model_sha256": sha(model_path),
        "deck_path": str(directory / "model.inp"),
        "deck_sha256": sha(ROOT / directory / "model.inp"),
        "audit_path": str(directory / "audit.json"),
        "audit_sha256": sha(audit_path),
        "context_path": str(directory / "case-bound-input-context.json"),
        "context_sha256": sha(context_path),
        "source_pins_path": str(directory / "source-pins.json"),
        "source_pins_sha256": sha(ROOT / directory / "source-pins.json"),
        "diagnostic_screen_status": context.get("diagnostic_floor_screen_status"),
        "diagnostic_screen_sha256": context.get("diagnostic_floor_screen_sha256"),
        "branch_id": branch.get("branch_id"),
        "selected_cell_count": len(selected),
        "selected_cells": sorted(selected),
        "inactive_cell_count": len(inactive),
        "source_model_inputs_sha256": model.get("source_model_inputs_sha256"),
    }


def compare_sets(observed: set[str], prior: set[str]) -> dict[str, Any]:
    common = observed & prior
    observed_only = observed - prior
    prior_only = prior - observed
    return {
        "exact_match": observed == prior,
        "observed_is_strict_superset": prior < observed,
        "observed_is_strict_subset": observed < prior,
        "intersection_count": len(common),
        "intersection_cells": sorted(common),
        "observed_only_count": len(observed_only),
        "observed_only_cells": sorted(observed_only),
        "prior_only_count": len(prior_only),
        "prior_only_cells": sorted(prior_only),
        "symmetric_difference_count": len(observed_only | prior_only),
    }


def build_report(source_hashes: dict[str, str], diagnostic: Any) -> dict[str, Any]:
    model = load(ROOT / RUN / "model.json")
    context = load(ROOT / RUN / "case-context.json")
    register = load(ROOT / REGISTER)
    fresh_model = load(ROOT / FRESH_MODEL)
    execution = load(ROOT / RUN / "execution.json")
    freeze = load(ROOT / RUN / "freeze.json")
    authorization = load(ROOT / RUN / "authorization.json")
    parent_input = load(ROOT / RUN / "parent-serialized-input-audit.json")
    terminal = load(ROOT / RUN / "parent-terminal-assessment.json")
    context_check = load(ROOT / RUN / "parent-case-context-check.json")
    readiness = load(ROOT / RUN / "parent-readiness-review.json")
    deck = (ROOT / RUN / "model.inp").read_text(encoding="utf-8")
    data = (ROOT / RUN / "model.dat").read_text(encoding="utf-8", errors="replace")

    require(model.get("case_id") == context.get("case_id") == "k12-right", "attempt02_exact_case_id")
    require(model.get("candidate") == context.get("candidate") == fresh_model.get("candidate"), "attempt02_candidate_binding")
    require(model.get("geometry_revision_id") == context.get("geometry_revision_id") == fresh_model.get("geometry_revision_id"), "attempt02_geometry_revision_binding")
    require(context.get("selected_input_model_json_path") == str((ROOT / RUN / "model.json").resolve()), "attempt02_absolute_model_path")
    require(context.get("selected_input_deck_path") == str((ROOT / RUN / "model.inp").resolve()), "attempt02_absolute_deck_path")
    require(context.get("selected_input_model_json_sha256") == sha(ROOT / RUN / "model.json"), "attempt02_context_model_hash")
    require(context.get("selected_input_deck_sha256") == sha(ROOT / RUN / "model.inp"), "attempt02_context_deck_hash")
    require(context.get("source_case_load_register_path") == str(REGISTER), "attempt02_register_path")
    require(context.get("source_case_load_register_sha256") == sha(ROOT / REGISTER), "attempt02_register_hash")

    case_rows = [row for row in register.get("cases", []) if row.get("case_id") == "k12-right"]
    require(len(case_rows) == 1, "one_k12_right_register_row")
    case_row = case_rows[0]
    require(canonical_sha(case_row) == context.get("case_record_sha256") == model.get("floor_branch_metadata", {}).get("case_record_sha256"), "attempt02_exact_register_case_record")
    require(model.get("source_model_inputs_sha256") == fresh_model.get("source_model_inputs_sha256") == case_row.get("source_model_inputs_sha256"), "attempt02_fresh_source_inputs_digest")

    attempt03 = mask_input_record("attempt03", ATTEMPT03, "all-bearing")
    attempt11 = mask_input_record("attempt11", ATTEMPT11, "selected-proposal")
    branch = model.get("floor_branch_metadata", {})
    selected = set(map(str, branch.get("selected_cells", [])))
    inactive = set(map(str, branch.get("inactive_cells", [])))
    require(len(selected) == 10 and len(inactive) == 90 and selected.isdisjoint(inactive) and len(selected | inactive) == 100, "attempt02_ten_ninety_input_partition")
    require(selected == set(context.get("selected_cells", [])) and inactive == set(context.get("inactive_cells", [])), "attempt02_model_context_mask_match")
    require(selected == set(attempt11["selected_cells"]), "attempt02_input_is_attempt11_mask")
    require(attempt03["selected_cells"] != attempt11["selected_cells"], "two_distinct_prior_right_ten_cell_inputs")

    require(execution.get("run_id") == "springa-selected-k12-right-attempt02" and execution.get("native_solve_executed") is True, "attempt02_native_execution_identity")
    require(execution.get("returncode") == 0 and execution.get("container_confirmed_terminal") is True, "attempt02_native_execution_terminal")
    require(execution.get("outputs_sha256", {}).get("model.dat") == sha(ROOT / RUN / "model.dat"), "attempt02_execution_dat_hash")
    require(freeze.get("files_sha256", {}).get("model.json") == sha(ROOT / RUN / "model.json") and freeze.get("files_sha256", {}).get("model.inp") == sha(ROOT / RUN / "model.inp"), "attempt02_freeze_binds_exact_model_deck")
    require(authorization.get("input_freeze_sha256") == sha(ROOT / RUN / "freeze.json") and authorization.get("native_execution_authorized") is True, "attempt02_freeze_authorization")
    require(parent_input.get("status") == "PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT" and parent_input.get("case_id") == "k12-right", "attempt02_parent_input_audit")
    require(parent_input.get("proposed_branch_accepted") is False and parent_input.get("corner_demands_usable") is False, "attempt02_parent_input_only_limit")
    require(context_check.get("status") == "PASS_FROZEN_CASE_BOUND_INPUT_CONTRACT_ONLY" and context_check.get("native_response_consumed") is False, "attempt02_context_check_input_only")
    require(readiness.get("input_freeze_sha256") == sha(ROOT / RUN / "freeze.json") and readiness.get("ready_for_scoped_native_run") is True, "attempt02_readiness_binds_frozen_input")

    required_exception = "Inactive floor normal is not strictly separated with zero endpoint RF: SPR1311"
    require(terminal.get("status") == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH", "attempt02_parent_terminal_rejected")
    require(terminal.get("case_id") == "k12-right" and terminal.get("run_id") == execution.get("run_id"), "attempt02_terminal_run_binding")
    require(terminal.get("strict_response_exception") == required_exception, "attempt02_exact_strict_711_exception")
    require(terminal.get("response_auditor_sha256") == PINNED_SOURCE_SHA256["current-springa-zero-u-token-response-audit-attempt01/response_audit.py"], "attempt02_711_auditor_pin")
    require(terminal.get("response_writer_sha256") == PINNED_SOURCE_SHA256["current-springa-case-bound-parent-report-writer-attempt01/write_report.py"], "attempt02_parent_report_writer_pin")
    require(terminal.get("corner_demands_usable") is False and terminal.get("conditional_case_forces_usable") is False, "attempt02_no_case_demands")
    require(terminal.get("physical_failure_inferred") is False and terminal.get("joint_accepted") is False and terminal.get("mechanical_acceptance") is False, "attempt02_no_failure_or_acceptance_claim")
    for name in ("model.json", "model.inp", "model.dat", "execution.json", "case-context.json"):
        path = ROOT / RUN / name
        require(terminal.get("sources_sha256", {}).get(name) == sha(path), f"attempt02_parent_terminal_exact_{name}")

    method = diagnostic.load_method()
    method_contract = method._validate_model(model, deck, context)
    terminal_validation = method._validate_execution(
        ROOT / RUN / "model.json", ROOT / RUN / "model.dat", ROOT / RUN / "model.inp",
        ROOT / RUN / "execution.json", data, context,
    )
    parsed = method.parse_native_blocks(data)
    require(len(parsed) == 7, "seven_parsed_attempt02_states")
    source_normals = {
        str(row["group"]): row for row in method_contract["source_rows"]
        if row.get("role") == "floor_normal" and row.get("intended_law") == "compression_only"
    }
    bindings = {str(row["group"]): row for row in method_contract["bindings"] if str(row["group"]) in source_normals}
    require(len(source_normals) == len(bindings) == 100, "all_100_source_bound_normals")
    expected_nodes = set(map(int, model["nodes"]))
    require(all(set(state["u"]) == expected_nodes and set(state["rf"]) == expected_nodes for state in parsed.values()), "complete_U_RF_node_inventory_all_states")

    times = sorted(parsed)
    factors = [float(method.load_scale(time, float(method_contract["total_time"]))) for time in times]
    require(all(right > left for left, right in zip(times, times[1:])), "strictly_increasing_native_times")
    require(math.isclose(factors[-1], 1.0, rel_tol=0.0, abs_tol=1e-12), "full_load_factor_reached")
    ordered_groups = sorted(source_normals, key=lambda group: int(group.removeprefix("SPR")))
    states: list[dict[str, Any]] = []
    positive_sets: list[set[str]] = []
    for index, (time, factor) in enumerate(zip(times, factors, strict=True)):
        native_state = parsed[time]
        rows = [diagnostic.classify_normal(bindings[group], source_normals[group], native_state, method_contract["emitted_nodes"], method)
                for group in ordered_groups]
        positive = {row["normal_cell"] for row in rows if row["strictly_positive_bearing"]}
        separated = {row["normal_cell"] for row in rows if row["strictly_separated"]}
        unresolved = {row["normal_cell"] for row in rows if row["classification"] == "UNRESOLVED_INTERVALS"}
        require(len(positive) + len(separated) + len(unresolved) == 100 and not (positive & separated or positive & unresolved or separated & unresolved), f"state_{index}_partition")
        positive_sets.append(positive)
        states.append({
            "time": time,
            "load_factor": factor,
            "strict_positive_count": len(positive),
            "strictly_separated_count": len(separated),
            "unresolved_count": len(unresolved),
            "strict_positive_cells": sorted(positive),
            "strictly_separated_cells": sorted({row["normal_cell"] for row in rows if row["strictly_separated"]}),
            "unresolved_cells": sorted(unresolved),
            "rows": rows,
        })

    stable = all(mask == positive_sets[0] for mask in positive_sets[1:])
    fully_resolved = all(state["unresolved_count"] == 0 for state in states)
    observed = positive_sets[-1]
    compare03 = compare_sets(observed, set(attempt03["selected_cells"]))
    compare11 = compare_sets(observed, set(attempt11["selected_cells"]))
    mismatch_group = next(group for group, binding in bindings.items() if group == "SPR1311")
    mismatch_cell = str(bindings[mismatch_group]["name"])
    require(mismatch_cell == "floor_lumber_leg_right_0", "SPR1311_source_binding_to_right_leg_zero")
    require(mismatch_cell in inactive, "SPR1311_is_inactive_in_attempt02_input")
    require(mismatch_cell in observed, "SPR1311_maps_to_strict_positive_observed_cell")

    if stable and fully_resolved:
        status = "STABLE_STRICT_SUPPORT_SET_BUT_ATTEMPT02_SELECTED_MASK_REJECTED"
    else:
        status = "ATTEMPT02_NORMAL_INTERVALS_NOT_FULLY_STABLE_OR_RESOLVED"

    return {
        "schema": "current_springa_k12_right_attempt02_normal_interval_comparison/v1",
        "status": status,
        "case_id": "k12-right",
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "attempt02_run": {
            "run_id": execution["run_id"],
            "model_sha256": sha(ROOT / RUN / "model.json"),
            "deck_sha256": sha(ROOT / RUN / "model.inp"),
            "dat_sha256": sha(ROOT / RUN / "model.dat"),
            "execution_sha256": sha(ROOT / RUN / "execution.json"),
            "freeze_sha256": sha(ROOT / RUN / "freeze.json"),
            "case_context_sha256": sha(ROOT / RUN / "case-context.json"),
            "parent_terminal_assessment_sha256": sha(ROOT / RUN / "parent-terminal-assessment.json"),
            "parent_terminal_status": terminal["status"],
            "parent_terminal_exception": terminal["strict_response_exception"],
            "parent_terminal_auditor_sha256": terminal["response_auditor_sha256"],
            "native_returncode": terminal["native_returncode"],
            "container_confirmed_terminal": terminal["container_confirmed_terminal"],
            "elapsed_seconds": terminal["elapsed_seconds"],
            "corner_demands_usable": terminal["corner_demands_usable"],
            "conditional_case_forces_usable": terminal["conditional_case_forces_usable"],
            "physical_failure_inferred": terminal["physical_failure_inferred"],
            "joint_accepted": terminal["joint_accepted"],
            "mechanical_acceptance": terminal["mechanical_acceptance"],
        },
        "711_normal_interval_method": {
            "method": "Pinned 711 zero-U token wrapper, stable parser, and source-bound interval classifier",
            "wrapper_path": str(SERIES / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"),
            "wrapper_sha256": PINNED_SOURCE_SHA256["current-springa-zero-u-token-response-audit-attempt01/response_audit.py"],
            "stable_parser_sha256": PINNED_SOURCE_SHA256["current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"],
            "method_classifier_path": str(INTERVAL_METHOD),
            "method_classifier_sha256": PINNED_SOURCE_SHA256[str(INTERVAL_METHOD.relative_to(SERIES))],
            "terminal_output_validation": terminal_validation,
            "normal_carriers_per_state": len(source_normals),
            "native_state_count": len(states),
            "load_factors": factors,
            "strictly_classified_all_100_at_all_seven": fully_resolved,
            "positive_set_stable_all_seven": stable,
            "strict_positive_count_per_state": [state["strict_positive_count"] for state in states],
            "strictly_separated_count_per_state": [state["strictly_separated_count"] for state in states],
            "unresolved_count_per_state": [state["unresolved_count"] for state in states],
            "states": states,
        },
        "prior_right_ten_cell_inputs": {
            "attempt03": attempt03,
            "attempt11": attempt11,
            "attempt02_input_mask_matches_attempt11": selected == set(attempt11["selected_cells"]),
            "attempt02_input_mask_matches_attempt03": selected == set(attempt03["selected_cells"]),
        },
        "observed_set_comparison": {
            "observed_positive_cells_at_final_increment": sorted(observed),
            "observed_positive_count": len(observed),
            "observed_separated_count": states[-1]["strictly_separated_count"],
            "observed_unresolved_count": states[-1]["unresolved_count"],
            "relative_to_prior_attempt03_input": compare03,
            "relative_to_prior_attempt11_input": compare11,
            "inactive_mismatch_source_group": mismatch_group,
            "inactive_mismatch_cell": mismatch_cell,
            "attempt02_exact_mask_recurrence": compare03["exact_match"] or compare11["exact_match"],
            "exact_mask_cycle_detected": False,
            "interpretation": (
                "The stable observed set is not equal to either prior right 10-cell input. It strictly contains attempt11's mask by "
                "floor_lumber_leg_right_0; versus attempt03, eight cells overlap, two prior cells are absent, and three observed cells are new. "
                "This is one solved-mask comparison, not evidence of convergence, a cycle, or a generally valid support iteration rule."
            ),
        },
        "conditional_demand_limit": {
            "attempt02_strict_711_response_rejected": True,
            "rejection_is_source_defined_inactive_bearing_mismatch": True,
            "mismatched_normal_group": mismatch_group,
            "mismatched_normal_cell": mismatch_cell,
            "corner_demands_usable": False,
            "conditional_case_forces_usable": False,
            "forces_promoted": False,
            "physical_failure_inferred": False,
            "joint_or_mechanical_acceptance": False,
            "new_proposal_created": False,
            "automatic_iteration_performed": False,
            "new_native_run_performed": False,
        },
        "source_authority": {
            "source_load_register_path": str(REGISTER),
            "source_load_register_sha256": sha(ROOT / REGISTER),
            "case_record_sha256": canonical_sha(case_row),
            "fresh_source_model_inputs_sha256": fresh_model["source_model_inputs_sha256"],
            "attempt02_input_is_attempt11_model": True,
            "attempt03_and_attempt11_are_distinct_prior_case_local_inputs": True,
            "no_a12_or_a1_forces_or_responses_reused": True,
        },
        "artifact_provenance": {
            "source_file_sha256": source_hashes,
            "producer_path": str(Path(__file__).resolve().relative_to(ROOT)),
            "producer_sha256": sha(Path(__file__).resolve()),
        },
        "limits": [
            "Normal interval classifications are computed from the exact K12-right attempt02 response DAT and do not make its strict response gates pass.",
            "The terminal status remains rejected because inactive SPR1311 is not strictly separated with zero endpoint RF; corner and conditional case forces remain unusable.",
            "The 11-positive set is stable over the seven increments of this one solved attempt02 input. Stability over increments does not establish a fixed point across masks or convergence of a support-selection procedure.",
            "This comparison diagnoses the exact two earlier right 10-cell inputs and attempt02 result only. It creates no new proposal or automatic retry, and makes no floor, friction, connector, joint, or physical-failure finding.",
            "No geometry, constitutive law, material, load, acceptance criterion, or original LEG/RUNNER resistance was changed or reopened.",
        ],
    }


def write_or_verify(write: bool) -> None:
    source_hashes = verify_sources()
    diagnostic = import_interval_method()
    report = build_report(source_hashes, diagnostic)
    text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if write:
        HERE.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(text, encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "case_id": report["case_id"],
            "positive_counts": report["711_normal_interval_method"]["strict_positive_count_per_state"],
            "separated_counts": report["711_normal_interval_method"]["strictly_separated_count_per_state"],
            "unresolved_counts": report["711_normal_interval_method"]["unresolved_count_per_state"],
            "matches_attempt03": report["observed_set_comparison"]["relative_to_prior_attempt03_input"]["exact_match"],
            "matches_attempt11": report["observed_set_comparison"]["relative_to_prior_attempt11_input"]["exact_match"],
            "attempt11_strict_superset": report["observed_set_comparison"]["relative_to_prior_attempt11_input"]["observed_is_strict_superset"],
            "mismatch_cell": report["conditional_demand_limit"]["mismatched_normal_cell"],
            "corner_demands_usable": report["conditional_demand_limit"]["corner_demands_usable"],
            "forces_promoted": report["conditional_demand_limit"]["forces_promoted"],
        }, indent=2))
    else:
        require(OUTPUT.is_file(), "attempt02_comparison_report_exists")
        saved = json.loads(OUTPUT.read_text(encoding="utf-8"))
        require(saved == json.loads(text), "attempt02_comparison_reproduces_from_pinned_711_sources")
        print("verified pinned K12-right attempt02 response, 700 normal classifications, both prior masks, and rejection limits")


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
        print(f"K12_RIGHT_ATTEMPT02_INTERVAL_DIAGNOSTIC_BLOCKED: {error}", file=sys.stderr)
        raise
