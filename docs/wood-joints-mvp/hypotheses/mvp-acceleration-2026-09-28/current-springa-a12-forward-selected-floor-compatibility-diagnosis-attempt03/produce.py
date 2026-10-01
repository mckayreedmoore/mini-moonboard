#!/usr/bin/env python3
"""Classify frozen M4 A12-forward normals and compare only masks M1-M4."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
RUN = BASE / "current-springa-selected-floor-a12-forward-attempt04"
PREPARED = BASE / "current-springa-a12-forward-mask-update-proposal-attempt01/a12-forward"
SCREEN = BASE / "current-springa-a12-forward-mask-update-proposal-attempt01/screen.json"
PROPOSAL = BASE / "current-springa-a12-forward-mask-update-proposal-attempt01/proposal.json"
INPUT_GATE = BASE / "current-springa-a12-forward-mask-update-proposal-attempt01/input-gate.json"
INPUT_PINS = BASE / "current-springa-a12-forward-mask-update-proposal-attempt01/input-gate-source-pins.json"
PRIOR_DIAG = BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/diagnosis.json"
METHODS = BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/produce.py"
AUDITOR = BASE / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
KERNEL = BASE / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
TOKEN_REPLAY = BASE / "current-springa-zero-u-token-response-audit-attempt01/zero_u_token_replay.json"
EXPECTED = {
    "model.json": "c6ff4f67459bef5217502d0f61b25e19ef2aae0c21c0f10444de0c9936795cfc",
    "model.inp": "394653fbe1aa0d6ad5d36f66f19eabf6ddd45fef072466ec828d044aa3cf67e1",
    "model.dat": "2cd771182864e24d8f4ba3f71e56651a4e77e41eb450d962132b190dd70364ad",
    "execution.json": "cab8412fdb2256d6b18098f36259138b1d4ba91935917bccd85b44484968ada1",
    "freeze.json": "0274ab6ef907bb471ec1f0ea541a8a36074656e5df13177361fbf4a4be4264ae",
    "case-context.json": "3226424642d45f6fe7fb12c838cb52fd580ea8775f086d77873afb7131884d9a",
    "authorization.json": "4033b35ed2747208210c1d553bc87c3ef888e1856cc7487020a5a07925bbe3b1",
    "parent-readiness-review.json": "137965f3fdf69f29f03abd68f56939bc04f7ba41cdfb0d81a80cbdf9bfd8a2da",
    "parent-response-rejection.json": "fcee004672523b14a5bc6108b63b69aaf6c15c758af25db387d6a914ee7013aa",
    "parent-terminal-assessment.json": "873c0d3a00e245a5e36f0ec417966fda367b09613937b8cae8eee6a4eaaebb36",
    "native.stdout": "31058519f3532e5bcb38c7756f5a296236c1edf9b59e90ce3a96a43cdd31ca4a",
    "native.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "model.sta": "f898c1f5c7fa419035ef6b92924e3384c744470572f9d277b39c41c84256d9c4",
    "model.cvg": "6d81be7651a4e93b59e7d36118ffbdf2504298cc2c3456abbbaf4c4b1497592d",
    "model.frd": "c24871b8fbb0754803f16df184faf057545e401cce3188a4a310581b321ad1a0",
    "model.12d": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "spooles.out": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}
AUDITOR_SHA256 = "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"
KERNEL_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"
METHODS_SHA256 = "da112686f540e0576fa06ab7391ccd9d0c855b0320ade09932499128b538e2ad"
PRIOR_DIAG_SHA256 = "03d77cde6c1ca73f32fe7036cdf462df60de5fd929207f585d594fbacafb9194"
STATE_TIMES = [0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0]

INPUT_RUNS = {
    "M1_attempt01_input_35": {
        "dir": BASE / "current-springa-selected-floor-a12-forward-attempt01",
        "model": "50edee6194d3abdb758e8e7eb17f361b10cae7fc839dcedfa9f24f070d25324b",
        "deck": "401930f909d503e388a68f3eade5ebfaa1e228d5bc48712a217e170fe8bef553",
        "freeze": "5c0ff289a1ee32254160e3db0d7f9276de409f525cb665d59c17186b2586b45e",
        "count": 35,
    },
    "M2_attempt02_input_31": {
        "dir": BASE / "current-springa-selected-floor-a12-forward-attempt02",
        "model": "b50f560a1296f13a567bf37c17e6cd532ce9699d16b7700421b098aedd1420fe",
        "deck": "945c9d568e46e3fe6d68d4e2af8f93c9424cb9f728e6ee555df81b3fd274fa02",
        "freeze": "0bcd8b1a0da170c69e2e2dc1f52397cfcad0c9c10b9a524da3b07c27543f1f42",
        "count": 31,
    },
    "M3_attempt03_input_37": {
        "dir": BASE / "current-springa-selected-floor-a12-forward-attempt03",
        "model": "4f7d3f0a70a534a1c38cd0ce6e48990eb7b098dc82dc5fc2f412ff34eca3ff0f",
        "deck": "c9d926bd31b970f33f49dc6edf3627244a75d246124a5fef3e393b058bfa5aa4",
        "freeze": "204c1402c145d7f29c16314fc6f2f8231a9bbbc1f58eb2a9d100fb5aeaf8b9bf",
        "count": 37,
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def import_methods():
    spec = importlib.util.spec_from_file_location("pinned_a12_mask_interval_methods", METHODS)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import the pinned prior interval classifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def import_auditor():
    if sha(AUDITOR) != AUDITOR_SHA256 or sha(KERNEL) != KERNEL_SHA256:
        raise RuntimeError("Pinned 711 auditor/recovery kernel changed")
    spec = importlib.util.spec_from_file_location("pinned_a12_m4_zero_u_711", AUDITOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import pinned zero-U 711 auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mask_digest(mask: set[str]) -> str:
    return hashlib.sha256("\n".join(sorted(mask)).encode("utf-8")).hexdigest()


def load_input_masks() -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    masks: dict[str, set[str]] = {}
    pins: dict[str, dict[str, str]] = {}
    for name, values in INPUT_RUNS.items():
        folder = values["dir"]
        model_path, deck_path, freeze_path = folder / "model.json", folder / "model.inp", folder / "freeze.json"
        if (sha(model_path) != values["model"] or sha(deck_path) != values["deck"]
                or sha(freeze_path) != values["freeze"]):
            raise RuntimeError(f"Pinned prior A12-forward input changed: {name}")
        model, freeze = read(model_path), read(freeze_path)
        mask = set(map(str, model["floor_selected_bearing_cells"]))
        if (model.get("case_id") != "a12-forward" or len(mask) != values["count"]
                or freeze.get("files_sha256", {}).get("model.json") != values["model"]
                or freeze.get("files_sha256", {}).get("model.inp") != values["deck"]):
            raise RuntimeError(f"Prior mask input/freeze does not match the pinned {name}")
        masks[name] = mask
        pins[name] = {
            "model_path": rel(model_path), "model_sha256": sha(model_path),
            "deck_path": rel(deck_path), "deck_sha256": sha(deck_path),
            "freeze_path": rel(freeze_path), "freeze_sha256": sha(freeze_path),
        }
    prepared_model, prepared_deck = PREPARED / "model.json", PREPARED / "model.inp"
    prepared = read(prepared_model)
    m4 = set(map(str, prepared["floor_selected_bearing_cells"]))
    if sha(prepared_model) != "d61113db83e94443dfd4a2129793cf6c5f97511ea4c130f29e9b09e0d0f75dc6":
        raise RuntimeError("Pinned M4 prepared model changed")
    if sha(prepared_deck) != EXPECTED["model.inp"] or len(m4) != 37:
        raise RuntimeError("Pinned M4 prepared deck/mask changed")
    masks["M4_attempt04_input_37"] = m4
    pins["M4_attempt04_input_37"] = {
        "model_path": rel(prepared_model), "model_sha256": sha(prepared_model),
        "deck_path": rel(prepared_deck), "deck_sha256": sha(prepared_deck),
        "freeze_path": None, "freeze_sha256": None,
    }
    return masks, pins


def compare_masks(observed: set[str], masks: dict[str, set[str]]) -> dict[str, Any]:
    return {
        name: {
            "input_cell_count": len(mask),
            "exact_match": observed == mask,
            "overlap_count": len(observed & mask),
            "symmetric_difference_count": len(observed ^ mask),
            "observed_positive_outside_input": sorted(observed - mask),
            "input_cells_not_strictly_positive": sorted(mask - observed),
        }
        for name, mask in masks.items()
    }


def main() -> None:
    for filename, expected in EXPECTED.items():
        if sha(RUN / filename) != expected:
            raise RuntimeError(f"Frozen M4 run artifact changed: {filename}")
    if sha(METHODS) != METHODS_SHA256 or sha(PRIOR_DIAG) != PRIOR_DIAG_SHA256:
        raise RuntimeError("Pinned prior M3 interval evidence/method source changed")

    execution = read(RUN / "execution.json")
    freeze = read(RUN / "freeze.json")
    parent_rejection = read(RUN / "parent-response-rejection.json")
    parent_assessment = read(RUN / "parent-terminal-assessment.json")
    model_path, deck_path, data_path = RUN / "model.json", RUN / "model.inp", RUN / "model.dat"
    context_path = RUN / "case-context.json"
    model, deck, data = read(model_path), deck_path.read_text(encoding="utf-8"), data_path.read_text(encoding="utf-8", errors="replace")
    context = read(context_path)

    if (execution.get("run_id") != "springa-selected-a12-forward-attempt04"
            or execution.get("native_solve_executed") is not True
            or execution.get("returncode") != 0
            or execution.get("container_confirmed_terminal") is not True):
        raise RuntimeError("M4 is not the expected completed native execution")
    if (freeze.get("files_sha256") != {
            "model.inp": EXPECTED["model.inp"],
            "model.json": EXPECTED["model.json"],
            "case-context.json": EXPECTED["case-context.json"],
        }):
        raise RuntimeError("Frozen M4 inputs differ from the recorded model/deck/context")
    if (parent_rejection.get("status") != "REJECTED_UNCHANGED_PHYSICAL_RESPONSE_GATE"
            or parent_rejection.get("reason") != "Selected floor normal is not strictly positive after rounding: SPR1068"
            or parent_rejection.get("usable_corner_demands") is not False):
        raise RuntimeError("M4 parent response-gate failure changed or is not the exact expected rejection")
    if (parent_assessment.get("status") != "REJECTED_PARENT_A12_FORWARD_M4_PHYSICAL_COMPATIBILITY"
            or parent_assessment.get("strict_rejection") != parent_rejection["reason"]
            or parent_assessment.get("response_usable_for_conditional_joint_checks") is not False
            or parent_assessment.get("physical_failure_inferred") is not False):
        raise RuntimeError("Parent terminal assessment is absent, altered, or makes a physical-failure inference")
    if model.get("case_id") != context.get("case_id") or model.get("case_id") != "a12-forward":
        raise RuntimeError("M4 case context does not bind A12-forward")
    if set(model.get("floor_selected_bearing_cells", [])) != set(context.get("selected_cells", [])):
        raise RuntimeError("M4 case context and frozen input mask differ")
    if context.get("selected_input_model_json_sha256") != sha(model_path) or context.get("selected_input_deck_sha256") != sha(deck_path):
        raise RuntimeError("M4 frozen context does not pin its exact native input files")
    if (context.get("diagnostic_floor_screen_sha256") != sha(SCREEN)
            or context.get("diagnostic_floor_screen_path") != rel(SCREEN)):
        raise RuntimeError("M4 context does not bind the exact input-only proposal screen")
    screen = read(SCREEN)
    if (context.get("diagnostic_floor_screen_status") != screen.get("status")
            or screen.get("native_solve_launched_by_projection") is not False
            or screen.get("screen_forces_or_active_states_adopted") is not False):
        raise RuntimeError("M4 proposal screen is not the exact diagnostic-only screen")

    for name, expected in execution["outputs_sha256"].items():
        if sha(RUN / name) != expected:
            raise RuntimeError(f"Native output differs from exact execution record: {name}")
    freeze_sources = freeze.get("source_sha256", {})
    if not isinstance(freeze_sources, dict) or not freeze_sources:
        raise RuntimeError("M4 freeze lacks its pinned source closure")
    for raw, expected in freeze_sources.items():
        path = Path(raw)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError(f"Frozen source closure changed: {raw}")

    input_masks, input_pins = load_input_masks()
    run_mask = set(map(str, model["floor_selected_bearing_cells"]))
    if run_mask != input_masks["M4_attempt04_input_37"]:
        raise RuntimeError("Frozen M4 native mask differs from the prepared M4 input")

    prior_diag = read(PRIOR_DIAG)
    m3_observed_before = set(map(str, prior_diag["strict_positive_cells_diagnostic_only"]))
    if (prior_diag.get("native_run_id") != "springa-selected-a12-forward-attempt03"
            or prior_diag.get("strict_positive_pattern_constant_across_seven_states") is not True
            or m3_observed_before != input_masks["M4_attempt04_input_37"]):
        raise RuntimeError("Prior M3 run does not establish the pinned M4 input hypothesis")

    helper = import_methods()
    auditor = helper.import_zero_u_auditor()
    if sha(AUDITOR) != AUDITOR_SHA256 or sha(KERNEL) != KERNEL_SHA256:
        raise RuntimeError("Pinned 711 method source changed after import")
    if parent_rejection.get("model_sha256") != sha(model_path) or parent_rejection.get("deck_sha256") != sha(deck_path):
        raise RuntimeError("Parent strict response rejection refers to different model/deck inputs")
    case_pin = auditor._validate_case_context(context)
    contract = auditor._validate_model(model, deck, context)
    terminal = auditor._validate_execution(model_path, data_path, deck_path, RUN / "execution.json", data, context)
    if terminal.get("native_output_hashes_match") is not True:
        raise RuntimeError("Pinned 711 execution validation failed its native-output integrity check")
    states = auditor.parse_native_blocks(data)
    if list(states) != STATE_TIMES:
        raise RuntimeError(f"Expected the seven exact M4 printed load factors, got {list(states)}")

    normals = []
    for binding in contract["bindings"]:
        source = contract["source_by_group"][str(binding["group"])]
        if source.get("role") == "floor_normal":
            normals.append((binding, source))
    if len(normals) != 100:
        raise RuntimeError(f"Expected 100 source normal carriers, got {len(normals)}")

    history = []
    observed_masks: list[set[str]] = []
    spr1068_history = []
    for time, state in states.items():
        rows = []
        for binding, source in normals:
            # Native force and RF values are used only inside the pinned strict
            # classifier and are deliberately discarded from this report.
            _native_force, _native_radius, check = auditor.audit_springa(
                binding, source, state, contract["emitted_nodes"]
            )
            classification = helper.classify(auditor, binding, check, state, contract)
            q_interval, geometric_interval = helper.intervals(binding, check, state, contract)
            cell = str(binding["name"])
            row = {
                "cell_name": cell,
                "source_group": str(binding["group"]),
                "source_row_id": str(binding["source_row_id"]),
                "M4_input_status": "selected" if cell in run_mask else "inactive",
                "classification": classification,
                "q_interval_mm": q_interval,
                "geometric_elongation_interval_mm": geometric_interval,
            }
            rows.append(row)
            if str(binding["group"]) == "SPR1068":
                spr1068_history.append({
                    "load_factor": float(time), "cell_name": cell,
                    "input_status": row["M4_input_status"],
                    "classification": classification,
                    "q_interval_mm": q_interval,
                    "geometric_elongation_interval_mm": geometric_interval,
                })
        rows.sort(key=lambda row: row["cell_name"])
        if len(rows) != 100 or len({row["cell_name"] for row in rows}) != 100:
            raise RuntimeError(f"Normal carrier rows are incomplete at load factor {time}")
        positive = {row["cell_name"] for row in rows if row["classification"] == "STRICTLY_POSITIVE"}
        separated = {row["cell_name"] for row in rows if row["classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"}
        ambiguous = {row["cell_name"] for row in rows if row["classification"] == "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"}
        if len(positive | separated | ambiguous) != 100 or positive & separated or positive & ambiguous or separated & ambiguous:
            raise RuntimeError(f"Pinned strict classifications do not partition all 100 cells at {time}")
        observed_masks.append(positive)
        history.append({
            "load_factor": float(time),
            "strictly_positive_count": len(positive),
            "strictly_separated_count": len(separated),
            "ambiguous_or_noncomplementary_count": len(ambiguous),
            "observed_positive_cells_diagnostic_only": sorted(positive),
            "observed_positive_mask_sha256": mask_digest(positive),
            "input_mask_comparison": compare_masks(positive, input_masks),
            "rows": rows,
        })

    stable_across_states = all(mask == observed_masks[0] for mask in observed_masks[1:])
    m3_input = input_masks["M3_attempt03_input_37"]
    m4_input = input_masks["M4_attempt04_input_37"]
    m3_output_to_m4_input = m3_observed_before == m4_input
    m4_output_is_m3_input_all_states = all(mask == m3_input for mask in observed_masks)
    recurrence = m3_output_to_m4_input and m4_output_is_m3_input_all_states
    per_mask_summary = {
        name: {
            "input_cell_count": len(mask),
            "exact_match_at_any_printed_state": any(obs == mask for obs in observed_masks),
            "exact_match_at_all_printed_states": all(obs == mask for obs in observed_masks),
            "distinct_symmetric_difference_counts_across_states": sorted({len(obs ^ mask) for obs in observed_masks}),
            "M4_final_output_symmetric_difference_count": len(observed_masks[-1] ^ mask),
            "M4_final_output_extra_positive_cells": sorted(observed_masks[-1] - mask),
            "M4_final_input_cells_not_positive": sorted(mask - observed_masks[-1]),
            **input_pins[name],
        }
        for name, mask in input_masks.items()
    }

    source_paths = {
        *(RUN / filename for filename in EXPECTED),
        RUN / "parent-terminal-assessment.json",
        PREPARED / "model.json", PREPARED / "model.inp", PREPARED / "audit.json",
        SCREEN, PROPOSAL, INPUT_GATE, INPUT_PINS,
        PRIOR_DIAG, METHODS, AUDITOR, KERNEL, TOKEN_REPLAY,
        BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/source-pins.json",
        BASE / "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py",
        BASE / "current-springa-case-bound-floor-input-adapter-attempt10/a12-forward/case-bound-input-context-contract.json",
        BASE / "current-springa-case-bound-response-audit-attempt01/response_audit.py",
    }
    for directory in [spec["dir"] for spec in INPUT_RUNS.values()]:
        source_paths.update({directory / "model.json", directory / "model.inp", directory / "freeze.json"})
    source_sha256 = {rel(path): sha(path) for path in sorted(source_paths)}
    for source, expected in freeze_sources.items():
        source_sha256[source] = expected
    freeze_map_sha = hashlib.sha256(json.dumps(freeze_sources, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    result = {
        "schema": "current_springa_a12_forward_attempt04_floor_mask_recurrence_diagnosis/v1",
        "status": "REJECTED_M4_SELECTED_BEARING_SUPPORT_BRANCH_DIAGNOSTIC_ONLY",
        "case_id": model["case_id"],
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "native_run_id": execution["run_id"],
        "terminal_native_output_consumed": True,
        "native_solve_launched_by_diagnosis": False,
        "run_returncode": execution["returncode"],
        "elapsed_seconds": execution["elapsed_seconds"],
        "parent_response_gate_status": parent_rejection["status"],
        "parent_response_gate_exception": parent_rejection["reason"],
        "parent_terminal_assessment_status": parent_assessment["status"],
        "strict_response_failure_cell": "SPR1068",
        "corner_demands_usable": False,
        "physical_force_adoption": False,
        "response_force_exported": False,
        "numeric_spring_force_or_reference_rf_values_written": False,
        "input_selected_cell_count": len(run_mask),
        "input_selected_cells_M4": sorted(run_mask),
        "all_100_floor_normal_laws_checked_at_every_printed_state": True,
        "all_printed_load_factors": [float(time) for time in states],
        "strict_method": {
            "name": "zero-U 711-token strict normal classification and signed interval",
            "response_auditor_path": rel(AUDITOR),
            "response_auditor_sha256": sha(AUDITOR),
            "recovery_kernel_path": rel(KERNEL),
            "recovery_kernel_sha256": sha(KERNEL),
            "prior_interval_method_source_path": rel(METHODS),
            "prior_interval_method_source_sha256": sha(METHODS),
            "token_replay_path": rel(TOKEN_REPLAY),
            "token_replay_sha256": sha(TOKEN_REPLAY),
        },
        "input_masks_M1_to_M4": {
            name: {"cell_count": len(mask), "cells": sorted(mask), "mask_sha256": mask_digest(mask)}
            for name, mask in input_masks.items()
        },
        "M3_to_M4_transition": {
            "M3_run_observed_positive_set_equals_M4_input": m3_output_to_m4_input,
            "M4_run_observed_positive_set_equals_M3_input_at_all_seven_states": m4_output_is_m3_input_all_states,
            "verified_two_mask_recurrence_M3_M4_for_these_two_frozen_inputs": recurrence,
            "M3_run_observed_positive_set": sorted(m3_observed_before),
            "M4_run_positive_sets_by_state": [row["observed_positive_cells_diagnostic_only"] for row in history],
            "limits": "A recurrence, if true, is verified only for these two frozen proposed masks and this seven-state run pair; it establishes neither an exhaustive active-set cycle nor a support solution/uniqueness result.",
        },
        "input_mask_comparison_summary": per_mask_summary,
        "state_positive_set_constant_across_seven_states": stable_across_states,
        "strict_positive_count_by_state": [row["strictly_positive_count"] for row in history],
        "strict_separated_count_by_state": [row["strictly_separated_count"] for row in history],
        "ambiguous_or_noncomplementary_count_by_state": [row["ambiguous_or_noncomplementary_count"] for row in history],
        "SPR1068_state_intervals": spr1068_history,
        "case_context_validation": {
            "case_context_sha256": sha(context_path),
            "selected_input_model_sha256": sha(model_path),
            "selected_input_deck_sha256": sha(deck_path),
            "case_context_validation_passed": True,
            "pinned_711_model_input_validation_passed": True,
            "execution_hash_validation_passed": terminal["native_output_hashes_match"],
            "selected_count": case_pin["selected_cell_count"],
            "inactive_count": case_pin["inactive_cell_count"],
        },
        "native_output_hashes": {name: sha(RUN / name) for name in EXPECTED},
        "freeze_source_closure": {
            "freeze_sha256": sha(RUN / "freeze.json"),
            "source_pin_count": len(freeze_sources),
            "all_frozen_source_hashes_revalidated": True,
            "canonical_source_pin_map_sha256": freeze_map_sha,
        },
        "history": history,
        "source_sha256": dict(sorted(source_sha256.items())),
        "limits": [
            "This diagnostic reads the frozen M4 DAT only; it does not edit or replace any frozen run file and launches no solver.",
            "Normal classifications reuse the unchanged pinned 711 strict signed-interval method. No tolerance or interval rule is changed.",
            "Native spring/RF values are used only internally by the pinned classifier and are withheld; no corner demand or response force is adopted.",
            "The M4 response is rejected because selected normal SPR1068 is not strictly positive after rounding; this is a model-response incompatibility, not an inferred physical failure.",
            "Only M1-M4 same-case input masks and the seven printed states are compared. No M5 mask, iteration, run, geometry, law, or load change is proposed.",
        ],
    }
    (HERE / "diagnosis.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    pins = {
        "schema": "current_springa_a12_forward_attempt04_floor_mask_recurrence_source_pins/v1",
        "status": "PASS_M4_DIAGNOSTIC_SOURCE_REHASH",
        "diagnosis_path": rel(HERE / "diagnosis.json"),
        "diagnosis_sha256": sha(HERE / "diagnosis.json"),
        "producer_path": rel(Path(__file__).resolve()),
        "producer_sha256": sha(Path(__file__).resolve()),
        "source_sha256": dict(sorted(source_sha256.items())),
        "frozen_source_pin_count_revalidated": len(freeze_sources),
        "input_mask_counts": {name: len(mask) for name, mask in input_masks.items()},
        "native_solve_launched_by_producer": False,
        "spring_force_or_rf_values_exported": False,
    }
    (HERE / "source-pins.json").write_text(json.dumps(pins, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "native_run_id": execution["run_id"],
        "response_rejection": parent_rejection["reason"],
        "positive_counts": result["strict_positive_count_by_state"],
        "separated_counts": result["strict_separated_count_by_state"],
        "ambiguous_counts": result["ambiguous_or_noncomplementary_count_by_state"],
        "stable_across_states": stable_across_states,
        "verified_M3_M4_recurrence": recurrence,
        "SPR1068": spr1068_history,
        "diagnosis_sha256": sha(HERE / "diagnosis.json"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
