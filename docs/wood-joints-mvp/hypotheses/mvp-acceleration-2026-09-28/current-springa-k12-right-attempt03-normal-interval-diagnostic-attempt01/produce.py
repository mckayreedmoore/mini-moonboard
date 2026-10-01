#!/usr/bin/env python3
"""Classify K12-right attempt03 normals and source-bound the mask recurrence."""
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
RUN01 = SERIES / "current-springa-selected-floor-k12-right-attempt01"
RUN02 = SERIES / "current-springa-selected-floor-k12-right-attempt02"
RUN03 = SERIES / "current-springa-selected-floor-k12-right-attempt03"
REGISTER = SERIES / "current-six-case-source-load-register-attempt01/register.json"
CORNER_REGISTER = SERIES / "current-six-case-corner-response-register-attempt01/register.json"
FRESH_MODEL = SERIES / "current-springa-six-case-frame-input-adapter-attempt01/k12-right/model.json"
CONTROL = SERIES / "current-springa-frame-k12-right-all-bearing-attempt01"
ADAPTER01 = SERIES / "current-springa-case-bound-floor-input-adapter-attempt03/k12-right"
ADAPTER02 = SERIES / "current-springa-case-bound-floor-input-adapter-attempt11/k12-right"
ADAPTER03 = SERIES / "current-springa-case-bound-floor-input-adapter-attempt12/k12-right"
REPORT01 = SERIES / "current-springa-k12-right-normal-interval-diagnostic-attempt01/k12-right-normal-intervals.json"
PRODUCER01 = SERIES / "current-springa-k12-right-normal-interval-diagnostic-attempt01/produce.py"
REPORT02 = SERIES / "current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01/k12-right-attempt02-normal-interval-comparison.json"
PRODUCER02 = SERIES / "current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01/produce.py"
INTERVAL_METHOD = SERIES / "current-springa-selected-floor-normal-interval-diagnostic-attempt01/produce.py"
OUTPUT = HERE / "k12-right-attempt03-normal-interval-comparison.json"

PINNED_SOURCE_SHA256 = {
    "current-springa-selected-floor-k12-right-attempt01/model.json": "0954343b2af9ca2a9caed8a48cb7e142d77729c2a12192b77b727db428317294",
    "current-springa-selected-floor-k12-right-attempt01/case-context.json": "6f9fdab0676389ed79f4e100241adfc6fdc83c36d7a64faad098c79f84f230c3",
    "current-springa-selected-floor-k12-right-attempt02/model.json": "99d6ae6efff6c2da8a473867cfeb833a3726f536f65392ae2121ff24861a114d",
    "current-springa-selected-floor-k12-right-attempt02/case-context.json": "bbfc750df3d443b1bb03d4af930ecb26f1e8b722ded2ba550c8f07497f0de8f8",
    "current-springa-selected-floor-k12-right-attempt03/model.json": "c39d93df0f053586e0b7a64a664d25bd410f75c961cdde5687f48d519cc2ba15",
    "current-springa-selected-floor-k12-right-attempt03/model.inp": "c114feb359858651fa67956b0dd9ef3bd39909759d8d2d0d5f8a348de1e8f256",
    "current-springa-selected-floor-k12-right-attempt03/model.dat": "d87d8d1df661ed08988455c841361a147731c885817d9950aa95caf2453f84c4",
    "current-springa-selected-floor-k12-right-attempt03/execution.json": "4aed6333775a07a0e64d527db636789e57ec7493e87cb3bee9178406e12f4f15",
    "current-springa-selected-floor-k12-right-attempt03/freeze.json": "2f5ff72621798bec19366d8c4b7975f48dafa4a60c74ad862f72fd3d7bea3c0b",
    "current-springa-selected-floor-k12-right-attempt03/authorization.json": "aed7ddb1469d9e0323a36606799a8195dde31d1cb00cdf88e46713eb7424576c",
    "current-springa-selected-floor-k12-right-attempt03/case-context.json": "f3de846c9680ec0812d7e5e614a5ceaab68bfaefaf46b42ea38629300845470c",
    "current-springa-selected-floor-k12-right-attempt03/parent-serialized-input-audit.json": "24aa538d073dd23875e20ed49a69c7af91300b4faef8eb636b159d0ef66c8849",
    "current-springa-selected-floor-k12-right-attempt03/parent-terminal-assessment.json": "03ff8251789e93f83defc938cbed3f86bf3543eeb7b6fd7a9e4cb4f704d3ab4f",
    "current-springa-selected-floor-k12-right-attempt03/parent-case-context-check.json": "226d5be5ede03dc8e58061f4e552617570f5435bff9489e69fe294f0a3371a67",
    "current-springa-selected-floor-k12-right-attempt03/parent-readiness-review.json": "0da5c79bfd64285798819f49211db26dbd9df1324309267a820303ba72162cc4",
    "current-springa-selected-floor-k12-right-attempt03/native.stdout": "9cc94e3456e2b00fffe5e015b2dac5e0ae2353e88eb0dad11fdd6568b0057ab1",
    "current-springa-selected-floor-k12-right-attempt03/native.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "current-springa-selected-floor-k12-right-attempt03/model.12d": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "current-springa-selected-floor-k12-right-attempt03/model.cvg": "9b7d77f3e70a74300ad42571f82b8e8304390ff3593c43e726dd7d92275ac29a",
    "current-springa-selected-floor-k12-right-attempt03/model.frd": "989a23cb304d24a1a84e909fe7f360be6651b6c2f6db510bd1bcb5965103070e",
    "current-springa-selected-floor-k12-right-attempt03/model.sta": "b9e7a39125bf59c7c659433aa14b4ac6f2d008a524851605a638ffd778f8eca7",
    "current-springa-selected-floor-k12-right-attempt03/spooles.out": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
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
    "current-springa-case-bound-floor-input-adapter-attempt12/k12-right/model.json": "319711c91726baad6dba752e2f900e700f8efcb7644dff064ea078679971b1ee",
    "current-springa-case-bound-floor-input-adapter-attempt12/k12-right/model.inp": "c114feb359858651fa67956b0dd9ef3bd39909759d8d2d0d5f8a348de1e8f256",
    "current-springa-case-bound-floor-input-adapter-attempt12/k12-right/audit.json": "d145edf3a8b25612d691a0931d9142799efebe025a5bb4b0c32c7c6027f90351",
    "current-springa-case-bound-floor-input-adapter-attempt12/k12-right/case-bound-input-context.json": "3cbb87628ec100730a82c6c54e52b1487aede61ad459c2a595deb204a2580901",
    "current-springa-case-bound-floor-input-adapter-attempt12/k12-right/case-bound-input-context-contract.json": "7ea723e536e38c9c41ecbe119af3ca79c2b748951da551fe4100894c735e9f16",
    "current-springa-case-bound-floor-input-adapter-attempt12/k12-right/source-pins.json": "d7fb7d29e5f6113a5bddc1b454d716a0d20665d3904c27234cc9442eaffa03a8",
    "current-six-case-source-load-register-attempt01/register.json": "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508",
    "current-six-case-corner-response-register-attempt01/register.json": "48c565a4a04bac8890172008af88bc60967c897ed02f8e7997c6b081e5760faf",
    "current-six-case-corner-response-register-attempt01/produce.py": "714301711184483f70d4c55493b1408ed877afb730dd876528b0811a8d1824e1",
    "current-springa-six-case-frame-input-adapter-attempt01/k12-right/model.json": "4766c0b06693c15e80758494fb7b2a566eb823089e82d29e0a72182b47e89868",
    "current-springa-frame-k12-right-all-bearing-attempt01/model.json": "f99e6ecbcb3088dca8a740024b92736fd50df2c394a01f25303c14540125f6d9",
    "current-springa-frame-k12-right-all-bearing-attempt01/model.inp": "fcc6be805a0169dd89628872af29a09e878448313c9f594d09fd15586acbf68f",
    "current-springa-frame-k12-right-all-bearing-attempt01/model.dat": "76fd45d0aae2520d90327643c77c47e34babe941eb511c848ab4ef600a313c84",
    "current-springa-frame-k12-right-all-bearing-attempt01/execution.json": "baed9ffbe3854d6709ea378619f406212b50fc4f94fdef120470ed322f56641c",
    "current-springa-frame-k12-right-all-bearing-attempt01/freeze.json": "98f1c701b084fac128d0d7b9a50909546c6867d3986a93abdb1c6222515e8bf2",
    "current-springa-frame-k12-right-all-bearing-attempt01/authorization.json": "3237dd13309ebab8aec30d9edeb5a2dc319c43005ac612859b4a2ecc6704c3a7",
    "current-springa-frame-k12-right-all-bearing-attempt01/parent-serialized-input-audit.json": "7c66bc4771b8de8a4198ba1299e36fb404e8baf9bc0d1da491e20a3bbc977f6e",
    "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py": "1e9edd6d8d1a341c3cd70854710dd80431438f7287e425b1c3e62d94d0f963bc",
    "current-springa-case-bound-parent-input-audit-attempt01/check.py": "cc4db4e8b6455b42f2230dd5284ecbae4c77d29e4165c466d1681d61bfd29b1d",
    "current-springa-frame-response-audit-attempt01/response_audit.py": "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
    "current-springa-zero-u-token-response-audit-attempt01/response_audit.py": "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
    "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py": "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    "current-springa-zero-u-token-response-audit-attempt01/zero_u_token_replay.json": "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1",
    "current-springa-zero-u-token-response-audit-attempt01/replay_zero_u_tokens.py": "6b49312429c78e04d0a70a7a428382028ac9e75ab01a69b53271d9feca91bd32",
    "current-springa-zero-u-token-response-audit-attempt01/README.md": "ef2c8d33ac9e48566c8b5c96f8ae4a0fa0216ff00fa1bc3aa6d7e3c0f76f0d49",
    "current-springa-selected-floor-normal-interval-diagnostic-attempt01/produce.py": "02f1292caf7b1bc1b5bbaca73bdbd4f7c3f7eb4c727a755eb69e458d00d49cd8",
    "current-springa-k12-right-normal-interval-diagnostic-attempt01/produce.py": "63e0aab21a9972b86191095d219be7a4735a3870213adcefdf54e614b2c14e9b",
    "current-springa-k12-right-normal-interval-diagnostic-attempt01/k12-right-normal-intervals.json": "7be4e1ca61b5c532dbfcf1ed590e6b77091bbfd96c8478f20ae31001b87d96d2",
    "current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01/produce.py": "dce70caf25249f470266d59ee2372b3e63287e8f7fbfba3795b25916ee8f0d72",
    "current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01/k12-right-attempt02-normal-interval-comparison.json": "5b93018b001657c05b670a2b1aecfce448ba291c09a3307f0b49c9369931ac5c",
    "current-springa-case-bound-parent-report-writer-attempt01/write_report.py": "92ea2e378c486674234b31a1ba384df9a6d5ea94da39c57cd4cb1a33a54e7d39",
}


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
    spec = importlib.util.spec_from_file_location("pinned_k12_right_interval_classifier", ROOT / INTERVAL_METHOD)
    require(spec is not None and spec.loader is not None, "pinned_711_interval_classifier_loads")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def comparison(observed: set[str], selected_input: set[str]) -> dict[str, Any]:
    common = observed & selected_input
    observed_only = observed - selected_input
    input_only = selected_input - observed
    return {
        "exact_match": observed == selected_input,
        "intersection_count": len(common),
        "intersection_cells": sorted(common),
        "observed_only_count": len(observed_only),
        "observed_only_cells": sorted(observed_only),
        "input_only_count": len(input_only),
        "input_only_cells": sorted(input_only),
        "symmetric_difference_count": len(observed_only | input_only),
    }


def attempt_mask(run: Path, adapter: Path, attempt_name: str) -> dict[str, Any]:
    model = load(ROOT / run / "model.json")
    context = load(ROOT / run / "case-context.json")
    adapted_model = load(ROOT / adapter / "model.json")
    adapted_context = load(ROOT / adapter / "case-bound-input-context.json")
    selected = set(map(str, model.get("floor_branch_metadata", {}).get("selected_cells", [])))
    adapted = set(map(str, adapted_model.get("floor_branch_metadata", {}).get("selected_cells", [])))
    require(model.get("case_id") == context.get("case_id") == adapted_model.get("case_id") == adapted_context.get("case_id") == "k12-right", f"{attempt_name}_case_identity")
    require(selected == set(context.get("selected_cells", [])), f"{attempt_name}_run_context_mask")
    require(selected == adapted == set(adapted_context.get("selected_cells", [])), f"{attempt_name}_run_matches_case_input_packet")
    require(context.get("selected_floor_model_json_sha256") == sha(ROOT / adapter / "model.json"), f"{attempt_name}_context_pins_input_model")
    require(context.get("selected_floor_model_json_path") == str(adapter / "model.json"), f"{attempt_name}_context_input_model_path")
    return {
        "attempt": attempt_name,
        "run_path": str(run),
        "run_model_sha256": sha(ROOT / run / "model.json"),
        "run_context_sha256": sha(ROOT / run / "case-context.json"),
        "adapter_input_path": str(adapter),
        "adapter_model_sha256": sha(ROOT / adapter / "model.json"),
        "adapter_context_sha256": sha(ROOT / adapter / "case-bound-input-context.json"),
        "selected_count": len(selected),
        "selected_cells": sorted(selected),
        "inactive_count": len(set(model.get("floor_branch_metadata", {}).get("inactive_cells", []))),
        "run_branch_id": model.get("floor_branch_metadata", {}).get("branch_id"),
        "input_screen_status": adapted_context.get("diagnostic_floor_screen_status"),
    }


def build_report(source_hashes: dict[str, str], diagnostic: Any) -> dict[str, Any]:
    # The first two response classifications are reused only from the already-pinned
    # source-bound diagnoses; attempt03 is freshly classified here from its own DAT.
    prior01 = load(ROOT / REPORT01)
    prior02 = load(ROOT / REPORT02)
    require(prior01.get("status") == "STRICT_STABLE_MASK_IDENTIFIED_INPUT_PROPOSAL_ELIGIBLE", "pinned_attempt01_diagnostic_status")
    old01 = prior01["strict_711_normal_diagnosis"]
    require(old01.get("strict_classifications_stable_all_seven_states") is True and old01.get("all_100_normals_strictly_classified_all_seven_states") is True, "attempt01_prior_diagnostic_strict_stable")
    require(old01.get("strict_positive_count_per_state") == [10] * 7 and old01.get("strictly_separated_count_per_state") == [90] * 7 and old01.get("unresolved_count_per_state") == [0] * 7, "attempt01_prior_diagnostic_10_90_0")
    require(prior02.get("status") == "STABLE_STRICT_SUPPORT_SET_BUT_ATTEMPT02_SELECTED_MASK_REJECTED", "pinned_attempt02_diagnostic_status")
    middle02 = prior02["711_normal_interval_method"]
    require(middle02.get("positive_set_stable_all_seven") is True and middle02.get("strictly_classified_all_100_at_all_seven") is True, "attempt02_prior_diagnostic_strict_stable")
    require(middle02.get("strict_positive_count_per_state") == [11] * 7 and middle02.get("strictly_separated_count_per_state") == [89] * 7 and middle02.get("unresolved_count_per_state") == [0] * 7, "attempt02_prior_diagnostic_11_89_0")

    input01 = attempt_mask(RUN01, ADAPTER01, "right01-original10")
    input02 = attempt_mask(RUN02, ADAPTER02, "right02-updated10")
    input03 = attempt_mask(RUN03, ADAPTER03, "right03-selected11")
    i01, i02, i03 = map(lambda record: set(record["selected_cells"]), (input01, input02, input03))
    observed01 = set(map(str, old01["observed_stable_positive_cells"]))
    observed02 = set(map(str, prior02["observed_set_comparison"]["observed_positive_cells_at_final_increment"]))
    require(observed01 == set(map(str, prior01["one_case_local_input_proposal"]["selected_cells_from_this_k12_right_response_only"])), "attempt01_report_mask_consistency")
    require(observed02 == set(map(str, prior02["observed_set_comparison"]["observed_positive_cells_at_final_increment"])), "attempt02_report_mask_consistency")
    require(len(i01) == len(i02) == 10 and len(i03) == 11, "right01_right02_right03_input_counts_10_10_11")
    require(input01["selected_cells"] == prior01["current_selected_input_cells"], "attempt01_response_matches_prior_classifier_input")
    require(input02["selected_cells"] == prior02["prior_right_ten_cell_inputs"]["attempt11"]["selected_cells"], "attempt02_response_matches_prior_classifier_input")
    require(input03["selected_cells"] == prior02["observed_set_comparison"]["observed_positive_cells_at_final_increment"], "attempt03_input_is_attempt02_observed_set")

    current_model = load(ROOT / RUN03 / "model.json")
    current_context = load(ROOT / RUN03 / "case-context.json")
    current_execution = load(ROOT / RUN03 / "execution.json")
    current_freeze = load(ROOT / RUN03 / "freeze.json")
    current_authorization = load(ROOT / RUN03 / "authorization.json")
    parent_input = load(ROOT / RUN03 / "parent-serialized-input-audit.json")
    terminal = load(ROOT / RUN03 / "parent-terminal-assessment.json")
    context_check = load(ROOT / RUN03 / "parent-case-context-check.json")
    readiness = load(ROOT / RUN03 / "parent-readiness-review.json")
    data = (ROOT / RUN03 / "model.dat").read_text(encoding="utf-8", errors="replace")
    deck = (ROOT / RUN03 / "model.inp").read_text(encoding="utf-8")

    require(current_model.get("case_id") == current_context.get("case_id") == "k12-right", "attempt03_case_id")
    require(current_model.get("candidate") == "compact-floor-flush-wood-joints-development" and current_model.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1", "attempt03_candidate_revision")
    require(current_model.get("source_model_inputs_sha256") == "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9", "attempt03_fresh_registered_case_source_digest")
    require(current_context.get("selected_floor_model_json_sha256") == sha(ROOT / ADAPTER03 / "model.json") and current_context.get("selected_floor_deck_sha256") == sha(ROOT / ADAPTER03 / "model.inp"), "attempt03_context_exact_adapter12_model_deck")
    require(current_execution.get("run_id") == "springa-selected-k12-right-attempt03" and current_execution.get("native_solve_executed") is True and current_execution.get("returncode") == 0 and current_execution.get("container_confirmed_terminal") is True, "attempt03_exact_terminal_run")
    require(current_freeze.get("files_sha256", {}).get("model.json") == sha(ROOT / RUN03 / "model.json") and current_freeze.get("files_sha256", {}).get("model.inp") == sha(ROOT / RUN03 / "model.inp"), "attempt03_freeze_model_deck_binding")
    require(current_authorization.get("input_freeze_sha256") == sha(ROOT / RUN03 / "freeze.json") and current_authorization.get("native_execution_authorized") is True, "attempt03_recorded_execution_authority")
    require(parent_input.get("status") == "PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT" and parent_input.get("corner_demands_usable") is False, "attempt03_input_audit_is_input_only")
    require(context_check.get("status") == "PASS_FROZEN_CASE_BOUND_INPUT_CONTRACT_ONLY" and context_check.get("native_response_consumed") is False, "attempt03_context_check_input_only")
    require(readiness.get("input_freeze_sha256") == sha(ROOT / RUN03 / "freeze.json") and readiness.get("joint_acceptance") is False, "attempt03_readiness_record_nonacceptance")

    exception = "Selected floor normal is not strictly positive after rounding: SPR1311"
    require(terminal.get("status") == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH" and terminal.get("strict_response_exception") == exception, "attempt03_exact_rejected_parent_assessment")
    require(terminal.get("case_id") == "k12-right" and terminal.get("run_id") == current_execution.get("run_id"), "attempt03_terminal_run_binding")
    require(terminal.get("response_auditor_sha256") == PINNED_SOURCE_SHA256["current-springa-zero-u-token-response-audit-attempt01/response_audit.py"], "attempt03_711_auditor_pin")
    require(terminal.get("response_writer_sha256") == PINNED_SOURCE_SHA256["current-springa-case-bound-parent-report-writer-attempt01/write_report.py"], "attempt03_parent_writer_pin")
    require(terminal.get("corner_demands_usable") is False and terminal.get("conditional_case_forces_usable") is False and terminal.get("physical_failure_inferred") is False, "attempt03_demands_unusable_no_physical_failure")
    for name in ("model.json", "model.inp", "model.dat", "execution.json", "case-context.json"):
        require(terminal.get("sources_sha256", {}).get(name) == sha(ROOT / RUN03 / name), f"attempt03_terminal_exact_{name}")

    register = load(ROOT / REGISTER)
    corner_register = load(ROOT / CORNER_REGISTER)
    fresh_model = load(ROOT / FRESH_MODEL)
    register_cases = [row for row in register.get("cases", []) if row.get("case_id") == "k12-right"]
    corner_cases = [row for row in corner_register.get("cases", []) if row.get("case_id") == "k12-right"]
    require(len(register_cases) == len(corner_cases) == 1, "one_registered_k12_right_case_each")
    require(canonical_sha(register_cases[0]) == current_context.get("case_record_sha256"), "attempt03_source_load_register_case_binding")
    require(corner_register.get("case_count") == 6 and corner_register.get("usable_corner_demand_cases") == 2 and corner_register.get("usable_conditional_physical_response_cases") == 2, "current_corner_register_scope")
    require(corner_cases[0].get("native_directory") == str(RUN03) and corner_cases[0].get("run_id") == current_execution["run_id"], "current_register_attempt03_run_binding")
    require(corner_cases[0].get("status") == terminal["status"] and corner_cases[0].get("strict_response_exception") == exception and corner_cases[0].get("corner_demands_usable") is False, "current_register_attempt03_rejection_matches_terminal")
    corner_source_pins = corner_register.get("source_pins_sha256", {})
    for name in ("model.json", "model.inp", "model.dat", "execution.json", "parent-terminal-assessment.json"):
        relative = str(RUN03 / name)
        require(corner_source_pins.get(relative) == sha(ROOT / RUN03 / name), f"current_corner_register_source_pin:{name}")

    method = diagnostic.load_method()
    method_contract = method._validate_model(current_model, deck, current_context)
    terminal_validation = method._validate_execution(
        ROOT / RUN03 / "model.json", ROOT / RUN03 / "model.dat", ROOT / RUN03 / "model.inp",
        ROOT / RUN03 / "execution.json", data, current_context,
    )
    parsed = method.parse_native_blocks(data)
    require(len(parsed) == 7, "seven_attempt03_dat_increments")
    source_normals = {
        str(row["group"]): row for row in method_contract["source_rows"]
        if row.get("role") == "floor_normal" and row.get("intended_law") == "compression_only"
    }
    bindings = {str(row["group"]): row for row in method_contract["bindings"] if str(row["group"]) in source_normals}
    require(len(source_normals) == len(bindings) == 100, "all_100_attempt03_floor_normals")
    expected_nodes = set(map(int, current_model["nodes"]))
    require(all(set(state["u"]) == expected_nodes and set(state["rf"]) == expected_nodes for state in parsed.values()), "complete_attempt03_U_RF_inventory")
    times = sorted(parsed)
    factors = [float(method.load_scale(time, float(method_contract["total_time"]))) for time in times]
    require(all(right > left for left, right in zip(times, times[1:])) and math.isclose(factors[-1], 1.0, rel_tol=0.0, abs_tol=1e-12), "attempt03_all_increments_reach_full_load")
    groups = sorted(source_normals, key=lambda group: int(group.removeprefix("SPR")))
    states: list[dict[str, Any]] = []
    positive_sets: list[set[str]] = []
    spr1311_rows: list[dict[str, Any]] = []
    for index, (time, factor) in enumerate(zip(times, factors, strict=True)):
        native_state = parsed[time]
        rows = [diagnostic.classify_normal(bindings[group], source_normals[group], native_state, method_contract["emitted_nodes"], method)
                for group in groups]
        positive = {row["normal_cell"] for row in rows if row["strictly_positive_bearing"]}
        separated = {row["normal_cell"] for row in rows if row["strictly_separated"]}
        unresolved = {row["normal_cell"] for row in rows if row["classification"] == "UNRESOLVED_INTERVALS"}
        require(len(positive) + len(separated) + len(unresolved) == 100 and not (positive & separated or positive & unresolved or separated & unresolved), f"attempt03_state_{index}_partition")
        positive_sets.append(positive)
        state_row = next(row for row in rows if row["source_group"] == "SPR1311")
        spr1311_rows.append(state_row)
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
    stable = all(current == positive_sets[0] for current in positive_sets[1:])
    fully_resolved = all(state["unresolved_count"] == 0 for state in states)
    observed03 = positive_sets[-1]
    require(stable and fully_resolved and [s["strict_positive_count"] for s in states] == [10] * 7, "attempt03_stable_10_90_0")
    require([s["strictly_separated_count"] for s in states] == [90] * 7 and [s["unresolved_count"] for s in states] == [0] * 7, "attempt03_10_90_0_counts")
    require(observed03 == i02, "attempt03_observed_set_recurs_to_attempt02_input")
    require(all(row["strictly_separated"] is True for row in spr1311_rows), "attempt03_selected_spr1311_strictly_separated_all_states")
    require(all(row["native_table_force_interval_N"] == [0.0, 0.0] for row in spr1311_rows), "attempt03_spr1311_zero_native_table_force_all_states")
    require(all(row["normal_cell"] == "floor_lumber_leg_right_0" for row in spr1311_rows), "attempt03_spr1311_cell_mapping")

    observed01 = set(map(str, old01["observed_stable_positive_cells"]))
    observed02 = set(map(str, prior02["observed_set_comparison"]["observed_positive_cells_at_final_increment"]))
    cycle = (observed02 == i03 and observed03 == i02 and i02 != i03)
    require(observed01 == i02 and observed02 == i03 and cycle, "exact_right02_right03_two_mask_recurrence")

    return {
        "schema": "current_springa_k12_right_attempt03_normal_interval_recurrence_diagnostic/v1",
        "status": "EXACT_TWO_MASK_RECURRENCE_IDENTIFIED_NO_CORNER_DEMANDS",
        "case_id": "k12-right",
        "candidate": current_model["candidate"],
        "geometry_revision_id": current_model["geometry_revision_id"],
        "current_attempt03": {
            "run_id": current_execution["run_id"],
            "model_sha256": sha(ROOT / RUN03 / "model.json"),
            "deck_sha256": sha(ROOT / RUN03 / "model.inp"),
            "dat_sha256": sha(ROOT / RUN03 / "model.dat"),
            "execution_sha256": sha(ROOT / RUN03 / "execution.json"),
            "case_context_sha256": sha(ROOT / RUN03 / "case-context.json"),
            "parent_terminal_assessment_sha256": sha(ROOT / RUN03 / "parent-terminal-assessment.json"),
            "run_status": terminal["status"],
            "strict_response_exception": terminal["strict_response_exception"],
            "response_auditor_sha256": terminal["response_auditor_sha256"],
            "native_returncode": terminal["native_returncode"],
            "container_confirmed_terminal": terminal["container_confirmed_terminal"],
            "elapsed_seconds": terminal["elapsed_seconds"],
            "corner_demands_usable": terminal["corner_demands_usable"],
            "conditional_case_forces_usable": terminal["conditional_case_forces_usable"],
            "physical_failure_inferred": terminal["physical_failure_inferred"],
            "joint_accepted": terminal["joint_accepted"],
        },
        "method": {
            "name": "Pinned 711 zero-U token parser with interval classification of q, geometry, table force, projected endpoint internal force, and action/reaction",
            "wrapper_sha256": PINNED_SOURCE_SHA256["current-springa-zero-u-token-response-audit-attempt01/response_audit.py"],
            "stable_parser_sha256": PINNED_SOURCE_SHA256["current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"],
            "interval_classifier_path": str(INTERVAL_METHOD),
            "interval_classifier_sha256": PINNED_SOURCE_SHA256[str(INTERVAL_METHOD.relative_to(SERIES))],
            "terminal_output_validation": terminal_validation,
            "normal_carriers_per_state": len(source_normals),
            "states": len(states),
            "load_factors": factors,
            "all_100_strictly_classified_all_7": fully_resolved,
            "positive_set_stable_all_7": stable,
            "positive_count_per_state": [state["strict_positive_count"] for state in states],
            "separated_count_per_state": [state["strictly_separated_count"] for state in states],
            "unresolved_count_per_state": [state["unresolved_count"] for state in states],
            "states": states,
        },
        "three_attempt_input_masks": {
            "right01_original10": input01,
            "right02_updated10": input02,
            "right03_selected11": input03,
        },
        "observed_masks": {
            "right01_observed": {
                "source_report_path": str(REPORT01),
                "source_report_sha256": sha(ROOT / REPORT01),
                "selected_cells": sorted(observed01),
                "strict_positive_counts": old01["strict_positive_count_per_state"],
            },
            "right02_observed": {
                "source_report_path": str(REPORT02),
                "source_report_sha256": sha(ROOT / REPORT02),
                "selected_cells": sorted(observed02),
                "strict_positive_counts": middle02["strict_positive_count_per_state"],
            },
            "right03_observed": {
                "source": "fresh 711 interval classification in this report",
                "selected_cells": sorted(observed03),
                "strict_positive_counts": [state["strict_positive_count"] for state in states],
            },
        },
        "mask_comparisons": {
            "right01_observed_vs_right01_input": comparison(observed01, i01),
            "right01_observed_vs_right02_input": comparison(observed01, i02),
            "right02_observed_vs_right02_input": comparison(observed02, i02),
            "right02_observed_vs_right03_input": comparison(observed02, i03),
            "right03_observed_vs_right03_input": comparison(observed03, i03),
            "right03_observed_vs_right02_input": comparison(observed03, i02),
            "right02_input_vs_right03_input": comparison(i02, i03),
            "exact_transition_sequence": [
                {"response_from": "right01-original10", "observed_mask_equals": "right02-updated10", "exact": observed01 == i02},
                {"response_from": "right02-updated10", "observed_mask_equals": "right03-selected11", "exact": observed02 == i03},
                {"response_from": "right03-selected11", "observed_mask_equals": "right02-updated10", "exact": observed03 == i02},
            ],
            "right02_right03_two_cycle_detected": cycle,
            "cycle_masks": {
                "right02_updated10": sorted(i02),
                "right03_selected11": sorted(i03),
                "added_cell_from_right02_to_right03": sorted(i03 - i02),
                "cell_lost_from_right03_to_right02": sorted(i03 - observed03),
            },
            "interpretation": (
                "The source-bound classification map for these fixed case inputs is right01 original10 -> right02 updated10, "
                "right02 updated10 -> right03 selected11, and right03 selected11 -> right02 updated10. "
                "The last two are an exact two-mask recurrence, so repeated fixed-support mask updates did not converge across these runs."
            ),
        },
        "spr1311_alternating_normal": {
            "cell": "floor_lumber_leg_right_0",
            "right02_was_inactive_and_classified_positive": "floor_lumber_leg_right_0" in observed02 - i02,
            "right03_is_selected_and_classified_separated": "floor_lumber_leg_right_0" in i03 - observed03,
            "right03_q_interval_each_state_mm": [row["projected_q_interval_mm"] for row in spr1311_rows],
            "right03_native_table_force_interval_each_state_N": [row["native_table_force_interval_N"] for row in spr1311_rows],
            "right02_parent_exception": prior02["attempt02_run"]["parent_terminal_exception"],
            "right03_parent_exception": terminal["strict_response_exception"],
        },
        "conditional_demand_limit": {
            "attempt03_strict_711_response_rejected": True,
            "corner_demands_usable": False,
            "conditional_case_forces_usable": False,
            "forces_promoted": False,
            "physical_failure_inferred": False,
            "new_mask_proposed": False,
            "automatic_iteration_performed": False,
            "new_native_run_performed_by_this_packet": False,
            "joint_or_mechanical_acceptance": False,
        },
        "source_authority": {
            "source_load_register_path": str(REGISTER),
            "source_load_register_sha256": sha(ROOT / REGISTER),
            "fresh_source_model_sha256": sha(ROOT / FRESH_MODEL),
            "current_corner_response_register_path": str(CORNER_REGISTER),
            "current_corner_response_register_sha256": sha(ROOT / CORNER_REGISTER),
            "current_corner_register_run03_status": corner_cases[0]["status"],
            "current_corner_register_source_pins_match_run03": True,
            "original_all_bearing_controls_model_sha256": sha(ROOT / CONTROL / "model.json"),
            "no_a12_or_a1_forces_or_responses_reused": True,
        },
        "artifact_provenance": {
            "source_file_sha256": source_hashes,
            "producer_path": str(Path(__file__).resolve().relative_to(ROOT)),
            "producer_sha256": sha(Path(__file__).resolve()),
        },
        "limits": [
            "Attempt01 and attempt02 observed masks are loaded from their pinned prior source-bound 711 diagnostics; attempt03 is freshly classified here from its exact DAT.",
            "The exact two-mask recurrence is limited to these three K12-right input/response states and this fixed reference support rule; it is not a general theorem about unilateral contact or other cases.",
            "Attempt03's parent response audit rejects selected SPR1311 because it is not strictly positive. The interval diagnosis finds that normal strictly separated across all seven states, while attempt02 found it positive while inactive.",
            "No case forces, corner demands, physical floor reactions, floor qualification, friction, joint acceptance, or physical failure are established.",
            "No new mask proposal or solver run is created. Geometry, source loads, material, constitutive law, criteria, and original LEG/RUNNER resistance remain unchanged.",
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
            "positive_counts": report["method"]["positive_count_per_state"],
            "separated_counts": report["method"]["separated_count_per_state"],
            "unresolved_counts": report["method"]["unresolved_count_per_state"],
            "attempt01_observed_equals_attempt02_input": report["mask_comparisons"]["exact_transition_sequence"][0]["exact"],
            "attempt02_observed_equals_attempt03_input": report["mask_comparisons"]["exact_transition_sequence"][1]["exact"],
            "attempt03_observed_equals_attempt02_input": report["mask_comparisons"]["exact_transition_sequence"][2]["exact"],
            "two_cycle": report["mask_comparisons"]["right02_right03_two_cycle_detected"],
            "attempt03_selected_spr1311_strictly_separated": report["spr1311_alternating_normal"]["right03_is_selected_and_classified_separated"],
            "corner_demands_usable": report["conditional_demand_limit"]["corner_demands_usable"],
        }, indent=2))
    else:
        require(OUTPUT.is_file(), "attempt03_recurrence_report_exists")
        saved = json.loads(OUTPUT.read_text(encoding="utf-8"))
        require(saved == json.loads(text), "attempt03_recurrence_report_reproduces_from_pinned_sources")
        print("verified K12-right attempt03 711 diagnosis, 3 input masks, recurrence, and conditional-force limits")


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
        print(f"K12_RIGHT_ATTEMPT03_RECURRENCE_DIAGNOSTIC_BLOCKED: {error}", file=sys.stderr)
        raise
