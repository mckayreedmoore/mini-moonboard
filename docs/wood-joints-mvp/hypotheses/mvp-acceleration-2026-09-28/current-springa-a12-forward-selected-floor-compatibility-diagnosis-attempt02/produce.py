#!/usr/bin/env python3
"""Reclassify all A12-forward floor normals and detect exact mask recurrence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
RUN = SERIES / "current-springa-selected-floor-a12-forward-attempt03"
CURRENT_INPUT = SERIES / "current-springa-case-bound-floor-input-adapter-attempt10/a12-forward"
ZERO_U_AUDIT = SERIES / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
ZERO_U_KERNEL = SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
ZERO_U_REPLAY = SERIES / "current-springa-zero-u-token-response-audit-attempt01/zero_u_token_replay.json"
ZERO_U_REPLAY_SCRIPT = SERIES / "current-springa-zero-u-token-response-audit-attempt01/replay_zero_u_tokens.py"
EXPECTED_ZERO_U_AUDIT_SHA256 = "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"
EXPECTED_ZERO_U_KERNEL_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"
EXPECTED_ZERO_U_REPLAY_SHA256 = "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1"
EXPECTED_RUN_FILES = {
    "model.json": "4f7d3f0a70a534a1c38cd0ce6e48990eb7b098dc82dc5fc2f412ff34eca3ff0f",
    "model.inp": "c9d926bd31b970f33f49dc6edf3627244a75d246124a5fef3e393b058bfa5aa4",
    "model.dat": "de70b9661f9aa9368da3fa2aa9e0559b5d76835e686a44abe194a82a9073acf4",
    "execution.json": "24fae58d9280cd2a27362e5a143d4ef20df9517afd8b1fc9efaf8ecb66854614",
    "freeze.json": "204c1402c145d7f29c16314fc6f2f8231a9bbbc1f58eb2a9d100fb5aeaf8b9bf",
    "case-context.json": "9c2660cfcf66ac90efaa0aaa0029c576413518102c42d2e78666f1f8560dd453",
    "authorization.json": "bdc08937e095d5fa14f7894c9d0df5ba484f2cf0a5a5cebe8d7fe8ec72f27f9b",
    "parent-serialized-input-audit.json": "1c8aaf99ffd7b722d7796f268a0baf8392dc2183105405bc42865173200b5226",
    "parent-readiness-review.json": "551b053a68646a0a7f7fc0000e793370f00c5eddf3fab823234efc7a0b1c0304",
    "parent-case-context-check.json": "dacfcbe3f9e97a00f3cc493595a5ac08e581f9193a4a9bb8de6bb106fdc5cfb5",
    "parent-terminal-assessment.json": "e2cc3467a22fdcc02940e4379dff3d4164c561ac37632ee24e6bb7f8125cf4c6",
    "native.stdout": "af9115466a34c64373c11d4f4ea86907eef9cb5cd406a6c864da070bb160137d",
    "native.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "model.sta": "f898c1f5c7fa419035ef6b92924e3384c744470572f9d277b39c41c84256d9c4",
    "model.cvg": "65aa5aa79fd5761d4e990597e9078a7a2e92ca93f3b672e99d5be56f286e5883",
    "model.frd": "32a51319fe0059b5bae503735b30b7ef49aa36ee19cb3940b98f46881662c76e",
    "model.12d": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "spooles.out": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}
PRIOR_INPUTS = {
    "attempt01_input_35": {
        "run_dir": SERIES / "current-springa-selected-floor-a12-forward-attempt01",
        "cell_count": 35,
        "model_sha256": "50edee6194d3abdb758e8e7eb17f361b10cae7fc839dcedfa9f24f070d25324b",
        "deck_sha256": "401930f909d503e388a68f3eade5ebfaa1e228d5bc48712a217e170fe8bef553",
        "freeze_sha256": "5c0ff289a1ee32254160e3db0d7f9276de409f525cb665d59c17186b2586b45e",
    },
    "attempt02_input_31": {
        "run_dir": SERIES / "current-springa-selected-floor-a12-forward-attempt02",
        "cell_count": 31,
        "model_sha256": "b50f560a1296f13a567bf37c17e6cd532ce9699d16b7700421b098aedd1420fe",
        "deck_sha256": "945c9d568e46e3fe6d68d4e2af8f93c9424cb9f728e6ee555df81b3fd274fa02",
        "freeze_sha256": "0bcd8b1a0da170c69e2e2dc1f52397cfcad0c9c10b9a524da3b07c27543f1f42",
    },
}
NORMAL_COUNT = 100
STATE_COUNT = 7
SCHEMA = "current_springa_a12_forward_attempt03_floor_recurrence_diagnosis/v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def import_zero_u_auditor() -> Any:
    if sha(ZERO_U_AUDIT) != EXPECTED_ZERO_U_AUDIT_SHA256:
        raise RuntimeError("Pinned exact-zero-U 711 response auditor changed")
    if sha(ZERO_U_KERNEL) != EXPECTED_ZERO_U_KERNEL_SHA256:
        raise RuntimeError("Pinned exact-zero-U response recovery kernel changed")
    if sha(ZERO_U_REPLAY) != EXPECTED_ZERO_U_REPLAY_SHA256:
        raise RuntimeError("Pinned zero-U token replay artifact changed")
    spec = importlib.util.spec_from_file_location("pinned_zero_u_711_a12_forward", ZERO_U_AUDIT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load pinned exact-zero-U response auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def classify(auditor: Any, binding: dict[str, Any], check: dict[str, Any],
             state: dict[str, Any], contract: dict[str, Any]) -> str:
    passed = []
    for selected in (True, False):
        try:
            auditor._strict_normal_branch_check(binding, check, state, contract, selected)
            passed.append(True)
        except auditor.ResponseAuditError:
            passed.append(False)
    if passed == [True, False]:
        return "STRICTLY_POSITIVE"
    if passed == [False, True]:
        return "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"
    return "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"


def intervals(binding: dict[str, Any], check: dict[str, Any],
              state: dict[str, Any], contract: dict[str, Any]) -> tuple[list[float], list[float]]:
    q = float(check["q_relative_projection_mm"])
    q_radius = float(check["q_relative_projection_radius_mm"])
    q_node, ground = map(int, binding["springa_nodes"])
    relative_u = [float(state["u"][q_node][i]) - float(state["u"][ground][i]) for i in range(3)]
    relative_u_radius = [float(state["u_radius"][q_node][i]) + float(state["u_radius"][ground][i])
                         for i in range(3)]
    current = [
        float(contract["emitted_nodes"][q_node][i])
        - float(contract["emitted_nodes"][ground][i]) + relative_u[i]
        for i in range(3)
    ]
    length = math.sqrt(sum(value * value for value in current))
    nominal_axis = [float(value) for value in binding["numerical_axis_global_xyz"]]
    current_axis = [value / length for value in current] if length > 0.0 else nominal_axis
    geometric_radius = (
        sum(abs(current_axis[i]) * relative_u_radius[i] for i in range(3))
        + float(check["geometric_length_subtraction_arithmetic_guard_mm"])
    )
    geometric = float(check["geometric_spring_elongation_mm"])
    return [q - q_radius, q + q_radius], [geometric - geometric_radius, geometric + geometric_radius]


def inspect_prior_inputs() -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    masks: dict[str, set[str]] = {}
    pins: dict[str, dict[str, str]] = {}
    for name, spec in PRIOR_INPUTS.items():
        directory = spec["run_dir"]
        model_path, deck_path, freeze_path = directory / "model.json", directory / "model.inp", directory / "freeze.json"
        model = load(model_path)
        freeze = load(freeze_path)
        if (sha(model_path) != spec["model_sha256"] or sha(deck_path) != spec["deck_sha256"]
                or sha(freeze_path) != spec["freeze_sha256"]):
            raise RuntimeError(f"Prior forward input source changed: {name}")
        if model.get("case_id") != "a12-forward" or len(model.get("floor_selected_bearing_cells", [])) != spec["cell_count"]:
            raise RuntimeError(f"Prior support set is not the pinned A12-forward {spec['cell_count']}-cell input: {name}")
        if freeze.get("files_sha256") != {"model.inp": spec["deck_sha256"], "model.json": spec["model_sha256"]}:
            raise RuntimeError(f"Prior input freeze does not bind the selected input files: {name}")
        masks[name] = set(map(str, model["floor_selected_bearing_cells"]))
        pins[name] = {
            "model_json_path": relative(model_path), "model_json_sha256": sha(model_path),
            "deck_path": relative(deck_path), "deck_sha256": sha(deck_path),
            "freeze_path": relative(freeze_path), "freeze_sha256": sha(freeze_path),
        }
    return masks, pins


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="write to an unused repository-local report directory")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve() if args.output_dir else Path(__file__).resolve().parent
    if not output_dir.is_relative_to(ROOT):
        raise RuntimeError("Output directory must remain inside this checkout")
    output_dir.mkdir(parents=True, exist_ok=True)
    if (output_dir / "diagnosis.json").exists() or (output_dir / "source-pins.json").exists():
        raise RuntimeError("Refusing to overwrite a completed source-bound diagnosis")

    for name, expected in EXPECTED_RUN_FILES.items():
        observed = sha(RUN / name)
        if observed != expected:
            raise RuntimeError(f"Pinned attempt03 source changed for {name}: {observed}")
    model_path, deck_path, data_path = RUN / "model.json", RUN / "model.inp", RUN / "model.dat"
    context_path = RUN / "case-context.json"
    model, deck = load(model_path), deck_path.read_text(encoding="utf-8")
    data = data_path.read_text(encoding="utf-8", errors="replace")
    context = load(context_path)
    execution = load(RUN / "execution.json")
    freeze = load(RUN / "freeze.json")
    parent = load(RUN / "parent-terminal-assessment.json")
    if execution.get("run_id") != "springa-selected-a12-forward-attempt03" or execution.get("native_solve_executed") is not True or execution.get("returncode") != 0 or execution.get("container_confirmed_terminal") is not True:
        raise RuntimeError("Attempt03 is not the expected terminal successful A12-forward run")
    if parent.get("status") != "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH" or parent.get("strict_response_exception") != "Selected floor normal is not strictly positive after rounding: SPR1050":
        raise RuntimeError("Pinned parent terminal assessment does not record the expected SPR1050 exception")
    if parent.get("corner_demands_usable") is not False or parent.get("mechanical_acceptance") is not False:
        raise RuntimeError("Parent assessment scope changed")
    if freeze.get("native_solve_executed") is not False or freeze.get("files_sha256") != {
        "model.inp": EXPECTED_RUN_FILES["model.inp"], "model.json": EXPECTED_RUN_FILES["model.json"]
    }:
        raise RuntimeError("Attempt03 freeze no longer binds the reviewed deck/model")
    output_names = ["model.json", "model.inp", "model.dat", "native.stdout", "native.stderr",
                    "model.cvg", "model.sta", "model.frd", "model.12d"]
    if any(execution.get("outputs_sha256", {}).get(name) != sha(RUN / name) for name in output_names):
        raise RuntimeError("Attempt03 terminal output hashes differ from execution record")

    prior_masks, prior_pins = inspect_prior_inputs()
    this_mask = set(map(str, model.get("floor_selected_bearing_cells", [])))
    if len(this_mask) != 37 or model.get("case_id") != "a12-forward":
        raise RuntimeError("Attempt03 model is not the frozen 37-cell A12-forward input")
    prior_masks["attempt03_input_37"] = this_mask
    prior_pins["attempt03_input_37"] = {
        "model_json_path": relative(model_path), "model_json_sha256": sha(model_path),
        "deck_path": relative(deck_path), "deck_sha256": sha(deck_path),
        "freeze_path": relative(RUN / "freeze.json"), "freeze_sha256": sha(RUN / "freeze.json"),
    }
    current_input_model = load(CURRENT_INPUT / "model.json")
    if set(map(str, current_input_model.get("floor_selected_bearing_cells", []))) != this_mask:
        raise RuntimeError("Attempt03 frozen input mask differs from the exact attempt10 prepared mask")
    current_freeze_input_hashes = load(CURRENT_INPUT / "source-pins.json")
    if (current_freeze_input_hashes.get("output_model_sha256") != sha(CURRENT_INPUT / "model.json")
            or current_freeze_input_hashes.get("output_deck_sha256") != sha(CURRENT_INPUT / "model.inp")):
        raise RuntimeError("Attempt10 prepared source pin ledger changed")

    auditor = import_zero_u_auditor()
    if parent.get("response_auditor_sha256") != EXPECTED_ZERO_U_AUDIT_SHA256:
        raise RuntimeError("Parent terminal assessment used a different response auditor")
    case_pin = auditor._validate_case_context(context)
    contract = auditor._validate_model(model, deck, context)
    terminal = auditor._validate_execution(model_path, data_path, deck_path, RUN / "execution.json", data, context)
    native_states = auditor.parse_native_blocks(data)
    if len(native_states) != STATE_COUNT or abs(float(max(native_states)) - 1.0) > 1.0e-12:
        raise RuntimeError("Attempt03 DAT does not contain exactly seven printed states through load factor 1.0")
    expected_nodes = set(map(int, model["nodes"]))
    for time, state in native_states.items():
        for field in ("u", "u_radius", "rf", "rf_radius"):
            if set(state[field]) != expected_nodes:
                raise RuntimeError(f"Incomplete {field} output at load factor {time}")

    input_cell_count = len(this_mask)
    normal_bindings = []
    for binding in contract["bindings"]:
        source = contract["source_by_group"][str(binding["group"])]
        if source.get("role") == "floor_normal":
            normal_bindings.append((binding, source))
    if len(normal_bindings) != NORMAL_COUNT:
        raise RuntimeError(f"Expected all {NORMAL_COUNT} source floor-normal SPRINGA carriers")

    state_rows: list[dict[str, Any]] = []
    positive_masks: list[set[str]] = []
    spr1050_rows = []
    for time, state in native_states.items():
        rows = []
        for binding, source in normal_bindings:
            # Native force and RF values returned by the auditor are discarded.
            _native_force, _native_radius, check = auditor.audit_springa(
                binding, source, state, contract["emitted_nodes"]
            )
            label = classify(auditor, binding, check, state, contract)
            q_interval, geometric_interval = intervals(binding, check, state, contract)
            cell = str(binding["name"])
            row = {
                "cell_name": cell,
                "source_group": str(binding["group"]),
                "source_row_id": str(binding["source_row_id"]),
                "input_mask_status": "selected" if cell in this_mask else "inactive",
                "zero_u_711_classification": label,
                "q_interval_mm": q_interval,
                "geometric_elongation_interval_mm": geometric_interval,
            }
            rows.append(row)
            if row["source_group"] == "SPR1050":
                spr1050_rows.append({
                    "load_factor": float(time), "cell_name": cell,
                    "input_mask_status": row["input_mask_status"],
                    "classification": label,
                    "q_interval_mm": q_interval,
                    "geometric_elongation_interval_mm": geometric_interval,
                })
        rows.sort(key=lambda item: item["cell_name"])
        if len(rows) != NORMAL_COUNT or len({item["cell_name"] for item in rows}) != NORMAL_COUNT:
            raise RuntimeError(f"Attempt03 normal-carrier inventory is incomplete or duplicated at {time}")
        positive = {row["cell_name"] for row in rows if row["zero_u_711_classification"] == "STRICTLY_POSITIVE"}
        separated = {row["cell_name"] for row in rows if row["zero_u_711_classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"}
        ambiguous = {row["cell_name"] for row in rows if row["zero_u_711_classification"] == "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"}
        positive_masks.append(positive)
        comparison = {
            name: {
                "exact_input_mask_match": positive == mask,
                "overlap_cell_count": len(positive & mask),
                "positive_cells_outside_input": sorted(positive - mask),
                "selected_input_cells_not_strictly_positive": sorted(mask - positive),
            }
            for name, mask in prior_masks.items()
        }
        rows_by_cell = {row["source_group"]: row for row in rows}
        if len(rows_by_cell) != NORMAL_COUNT:
            raise RuntimeError(f"Source SPR group ids are not unique at {time}")
        state_rows.append({
            "load_factor": float(time),
            "positive_count": len(positive),
            "separated_count": len(separated),
            "ambiguous_or_noncomplementary_count": len(ambiguous),
            "strict_positive_cells_diagnostic_only": sorted(positive),
            "exact_positive_set_sha256": hashlib.sha256("\n".join(sorted(positive)).encode()).hexdigest(),
            "input_mask_comparison": comparison,
            "rows": rows,
        })

    if not (len(spr1050_rows) == STATE_COUNT and all(
        row["input_mask_status"] == "selected" and row["classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"
        for row in spr1050_rows
    )):
        raise RuntimeError("SPR1050 classification no longer matches the parent strict-response exception")
    if any((len(pos), NORMAL_COUNT - len(pos)) != (37, 63) for pos in positive_masks):
        raise RuntimeError("Strict 711 normal classification counts changed from the pinned attempt03 result")
    if not all(not row["ambiguous_or_noncomplementary_count"] for row in state_rows):
        raise RuntimeError("Attempt03 contains an ambiguous/noncomplementary strict normal classification")

    stable = all(mask == positive_masks[0] for mask in positive_masks)
    if not stable:
        raise RuntimeError("Attempt03 strict positive support set changed between printed states")
    actual = positive_masks[-1]
    set_recurrence_pairs = [
        {"first_state_index": i + 1, "first_load_factor": state_rows[i]["load_factor"],
         "repeated_state_index": j + 1, "repeated_load_factor": state_rows[j]["load_factor"]}
        for i in range(len(positive_masks)) for j in range(i + 1, len(positive_masks))
        if positive_masks[i] == positive_masks[j]
    ]
    consecutive_transitions = []
    for i in range(1, len(positive_masks)):
        consecutive_transitions.append({
            "from_load_factor": state_rows[i - 1]["load_factor"],
            "to_load_factor": state_rows[i]["load_factor"],
            "cells_added_to_strict_positive_set": sorted(positive_masks[i] - positive_masks[i - 1]),
            "cells_removed_from_strict_positive_set": sorted(positive_masks[i - 1] - positive_masks[i]),
        })
    input_comparison = {
        name: {
            "input_cell_count": len(mask),
            "observed_positive_cell_count": len(actual),
            "exact_recurrence_at_any_printed_state": any(
                actual_mask == mask for actual_mask in positive_masks
            ),
            "exact_recurrence_at_all_printed_states": all(
                actual_mask == mask for actual_mask in positive_masks
            ),
            "overlap_cell_count": len(actual & mask),
            "symmetric_difference_cell_count": len(actual ^ mask),
            "strict_positive_cells_outside_input": sorted(actual - mask),
            "input_cells_not_strictly_positive": sorted(mask - actual),
            **prior_pins[name],
        }
        for name, mask in prior_masks.items()
    }

    run_source_paths = {RUN / name for name in EXPECTED_RUN_FILES}
    run_source_paths.update({RUN / "parent-terminal-assessment.json", RUN / "parent-readiness-review.json", RUN / "parent-case-context-check.json"})
    run_source_paths.update({
        CURRENT_INPUT / "model.json", CURRENT_INPUT / "model.inp", CURRENT_INPUT / "audit.json",
        CURRENT_INPUT / "source-pins.json", CURRENT_INPUT / "case-bound-input-context.json",
        CURRENT_INPUT / "case-bound-input-context-contract.json",
        SERIES / "current-springa-case-bound-floor-input-adapter-attempt10/screen.json",
        SERIES / "current-springa-case-bound-floor-input-adapter-attempt10/screen-source-pins.json",
        SERIES / "current-springa-case-bound-floor-input-adapter-attempt10/input-evidence-pins.json",
        ZERO_U_AUDIT, ZERO_U_KERNEL, ZERO_U_REPLAY, ZERO_U_REPLAY_SCRIPT,
    })
    for details in prior_pins.values():
        run_source_paths.update(ROOT / details[key] for key in ("model_json_path", "deck_path", "freeze_path"))
    for field in [
        "source_controls_model_json_path", "source_controls_deck_path", "source_controls_terminal_dat_path",
        "source_controls_execution_path", "source_case_load_register_path", "source_fresh_case_model_path",
        "diagnostic_floor_screen_path", "selected_floor_model_json_path", "selected_floor_deck_path",
    ]:
        raw = context.get(field)
        if raw:
            candidate = Path(raw)
            run_source_paths.add(candidate.resolve() if candidate.is_absolute() else (ROOT / candidate).resolve())

    freeze_sources = freeze["source_sha256"]
    for source_rel in freeze_sources:
        run_source_paths.add((ROOT / source_rel).resolve())
    source_hashes = {relative(path): sha(path) for path in sorted(run_source_paths)}
    for source_rel, expected in freeze_sources.items():
        if source_hashes.get(source_rel) != expected:
            raise RuntimeError(f"Attempt03 frozen source hash changed: {source_rel}")

    differences_by_input = {
        name: {
            "positive_set_repeats_input_at_any_printed_state": any(
                positive == mask for positive in positive_masks
            ),
            "positive_set_repeats_input_at_all_printed_states": all(
                positive == mask for positive in positive_masks
            ),
            "max_overlap_across_printed_states": max(len(positive & mask) for positive in positive_masks),
            "minimum_symmetric_difference_across_printed_states": min(len(positive ^ mask) for positive in positive_masks),
        }
        for name, mask in prior_masks.items()
    }
    run_pin = {name: sha(RUN / name) for name in EXPECTED_RUN_FILES}
    result = {
        "schema": SCHEMA,
        "status": "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH_DIAGNOSTIC_ONLY",
        "case_id": model["case_id"],
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "native_run_id": execution["run_id"],
        "terminal_native_output_consumed": True,
        "native_solve_launched_by_diagnosis": False,
        "full_step_native_convergence": True,
        "parent_terminal_assessment_status": parent["status"],
        "parent_strict_response_exception": parent["strict_response_exception"],
        "corner_demands_usable": False,
        "mechanical_acceptance": False,
        "physical_force_adoption": False,
        "response_force_exported": False,
        "numeric_spring_force_or_reference_rf_values_written": False,
        "floor_support_mask_created": False,
        "input_selected_cell_count": input_cell_count,
        "input_selected_cells": sorted(this_mask),
        "all_100_floor_normal_laws_checked_at_every_printed_state": True,
        "all_printed_load_factors": [row["load_factor"] for row in state_rows],
        "strict_method": {
            "name": "zero-u 711-token strict normal classification",
            "auditor_path": relative(ZERO_U_AUDIT),
            "auditor_sha256": EXPECTED_ZERO_U_AUDIT_SHA256,
            "recovery_kernel_path": relative(ZERO_U_KERNEL),
            "recovery_kernel_sha256": EXPECTED_ZERO_U_KERNEL_SHA256,
            "token_replay_path": relative(ZERO_U_REPLAY),
            "token_replay_sha256": EXPECTED_ZERO_U_REPLAY_SHA256,
        },
        "strict_positive_count_at_every_state": 37,
        "strict_separated_count_at_every_state": 63,
        "ambiguous_or_noncomplementary_count_at_every_state": 0,
        "strict_positive_pattern_constant_across_seven_states": stable,
        "strict_positive_cells_diagnostic_only": sorted(actual),
        "strict_positive_mask_sha256": state_rows[-1]["exact_positive_set_sha256"],
        "input_mask_comparison_by_same_case_forward_input": input_comparison,
        "mask_recurrence_finding": {
            "same_strict_positive_set_repeats_at_each_printed_state": stable,
            "distinct_strict_positive_masks_in_seven_states": len({frozenset(mask) for mask in positive_masks}),
            "repeated_state_mask_pairs": set_recurrence_pairs,
            "consecutive_state_mask_changes": consecutive_transitions,
            "exact_recurrence_with_any_prior_forward_input": differences_by_input,
            "interpretation": (
                "The strict positive mask is one fixed 37-cell pattern throughout the seven printed load factors. "
                "It is not exactly any of the same-case forward 35-, 31-, or 37-cell input masks. "
                "This supports a stable diagnostic classification across the load ramp; it does not establish "
                "convergence of an active-mask update algorithm or an iteration cycle, because this run used "
                "one fixed 37-cell input and performed no mask updates."
            ),
        },
        "selected_input_cells_not_strictly_positive": sorted(this_mask - actual),
        "strict_positive_cells_outside_selected_input": sorted(actual - this_mask),
        "spr1050_diagnostic": {
            "cell_name": "floor_base_floor_left_10",
            "source_group": "SPR1050",
            "selected_in_attempt03_input": "floor_base_floor_left_10" in this_mask,
            "classification_by_state": spr1050_rows,
            "strictly_positive_at_any_printed_state": any(row["classification"] == "STRICTLY_POSITIVE" for row in spr1050_rows),
            "strictly_separated_at_all_printed_states": all(row["classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF" for row in spr1050_rows),
            "numeric_force_and_rf_values_withheld": True,
        },
        "history": state_rows,
        "run_execution_summary": {
            "returncode": execution["returncode"],
            "container_confirmed_terminal": execution["container_confirmed_terminal"],
            "elapsed_seconds": execution["elapsed_seconds"],
            "terminal_output_hashes_match_execution_record": terminal["native_output_hashes_match"],
            "attempt03_files_sha256": run_pin,
        },
        "source_sha256": source_hashes,
        "limits": [
            "This read-only report classifies one already completed A12-forward attempt03 run; no solver was launched by the report producer.",
            "Only the current A12-forward run supplies native displacement/reaction fields; earlier A12-forward runs contribute frozen input masks only.",
            "No numeric spring force, floor reference reaction, joint force, or corner demand is exported or adopted.",
            "The stationary pattern across printed load factors does not prove active-mask update convergence or uniqueness.",
            "No new support mask, retry, automatic iteration, freeze, or mechanical acceptance is proposed.",
        ],
    }
    out_diag = output_dir / "diagnosis.json"
    write(out_diag, result)
    write(output_dir / "source-pins.json", {
        "schema": "current_springa_a12_forward_attempt03_floor_recurrence_source_pins/v1",
        "case_id": "a12-forward",
        "diagnosis_path": relative(out_diag),
        "diagnosis_sha256": sha(out_diag),
        "producer_path": relative(Path(__file__).resolve()),
        "producer_sha256": sha(Path(__file__).resolve()),
        "source_sha256": dict(sorted(source_hashes.items())),
        "frozen_run_source_pin_count_revalidated": len(freeze_sources),
        "same_case_prior_input_masks": {name: spec["cell_count"] for name, spec in PRIOR_INPUTS.items()} |
            {"attempt03_input_37": len(this_mask)},
        "native_solve_launched_by_producer": False,
        "force_or_rf_values_exported": False,
    })
    print(json.dumps({
        "status": result["status"],
        "case_id": result["case_id"],
        "native_run_id": result["native_run_id"],
        "states": len(state_rows),
        "normal_counts_each_state": "37 positive / 63 separated / 0 ambiguous",
        "same_pattern_all_states": stable,
        "input_matches": {name: item["exact_recurrence_at_all_printed_states"] for name, item in input_comparison.items()},
        "SPR1050_selected_but_separated_all_states": result["spr1050_diagnostic"]["strictly_separated_at_all_printed_states"],
        "source_count": len(source_hashes),
        "diagnosis_sha256": sha(out_diag),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
