#!/usr/bin/env python3
"""Read-only replay of the preserved a12 corner report through its legacy exporter.

The script never writes into historical evidence and never launches a native
solver. It compares the legacy report payload while allowing only the current
context-only summary-file hash to differ. It also records why that historical
response cannot be re-labeled as a generic case-context response.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = Path(__file__).resolve().parent
LEGACY_EXPORTER = BASE / "current-corner-native-demand-export-attempt03/produce.py"
LEGACY_EXPORTER_SHA256 = "0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8"
LEGACY_RESPONSE = BASE / "current-springa-selected-floor-a12-rear-attempt03/response.json"
LEGACY_RESPONSE_SHA256 = "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274"
LEGACY_REPORT = BASE / "current-corner-native-demand-export-attempt03/corner-demand-report.json"
LEGACY_REPORT_SHA256 = "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17"
LEGACY_SCREEN = BASE / "current-springa-selected-floor-branch-screen-attempt02/screen.json"
LEGACY_SCREEN_SHA256 = "231b4fa22128bb01ae08f9bf21e6fec9ccb9c7578724781fae01a6f79856ed93"
CONTROLS_MODEL = BASE / "current-springa-frame-a12-rear-controls-attempt01/model.json"
CONTROLS_MODEL_SHA256 = "b89e69abd004bd788d3619f73270375bbd8d8a195edf29313a77baee3c1a8f1e"
CONTROLS_DECK = BASE / "current-springa-frame-a12-rear-controls-attempt01/model.inp"
CONTROLS_DECK_SHA256 = "bab4e4728e6a690dbff66d44cced93977a6125d5fd9fc21fe26d927d83785ca2"
GENERIC_AUDITOR = BASE / "current-springa-case-bound-response-audit-attempt01/response_audit.py"
GENERIC_AUDITOR_SHA256 = "df1ed0eedb62ed3657a05a6d679d105e15e63b5ee18b999a731adab190b1b479"
CONTEXT_ONLY_SUMMARY = BASE / "current-knee-joint-check-summary.md"
OLD_CONTEXT_SUMMARY_SHA256 = "7da2a5c365ead5e2ed991964fdfe4970621ebc92ccef1a7fb7356c1a32a118bb"
OUTPUT_SCHEMA = "current_corner_legacy_a12_replay/v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def import_legacy_exporter(path: Path):
    if sha256(path) != LEGACY_EXPORTER_SHA256:
        raise ValueError("legacy_exporter_source_sha256_mismatch")
    spec = importlib.util.spec_from_file_location("pinned_legacy_corner_exporter", path)
    if spec is None or spec.loader is None:
        raise ValueError("legacy_exporter_source_not_importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def expected_report_shapes(report: dict[str, Any]) -> dict[str, Any]:
    increments = report["increments"]
    rows = []
    for index, inc in enumerate(increments):
        groups = inc["primary_physical_bolt_groups"]
        rows.append({
            "increment_index": index,
            "load_factor": inc["load_factor"],
            "corner_interfaces": len(inc["all_corner_interfaces"]),
            "physical_bolts": sum(group["physical_bolt_count"] for group in groups.values()),
            "lateral_planes": sum(group["lateral_plane_count"] for group in groups.values()),
            "outer_seat_ties": sum(group["outer_seat_tie_count"] for group in groups.values()),
            "contact_rows": len(inc["member_contact_bearing"]["contact_cells"]),
            "washer_seats": len(inc["outer_washer_seats"]),
            "retained_original_leg_runner_interface_records": len(inc["retained_original_leg_runner_interfaces"]),
            "retained_original_leg_runner_arrangements": inc["retained_original_arrangement_count"],
            "five_body_balance_records": len(inc["corner_five_body_balance"]),
        })
    required = {
        "increment_count_is_seven": len(increments) == 7,
        "all_increments_load_factors_match_historical_sequence": [row["load_factor"] for row in rows] == [0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0],
        "all_increments_have_338_corner_interfaces": all(row["corner_interfaces"] == 338 for row in rows),
        "all_increments_have_6_physical_bolts": all(row["physical_bolts"] == 6 for row in rows),
        "all_increments_have_8_lateral_planes": all(row["lateral_planes"] == 8 for row in rows),
        "all_increments_have_6_outer_seat_ties": all(row["outer_seat_ties"] == 6 for row in rows),
        "all_increments_have_232_contact_rows": all(row["contact_rows"] == 232 for row in rows),
        "all_increments_have_12_washer_seats": all(row["washer_seats"] == 12 for row in rows),
        "all_increments_keep_12_original_leg_runner_arrangements": all(row["retained_original_leg_runner_arrangements"] == 12 for row in rows),
        "all_increments_keep_5_body_balance_records": all(row["five_body_balance_records"] == 5 for row in rows),
    }
    source_contract = report["source_contract"]
    required["92_candidate_axes_are_separate_from_original_leg_runner_arrangements"] = (
        source_contract["new_block_axis_count"] == 92
        and source_contract["retained_original_leg_runner_axis_count"] == 12
    )
    return {
        "required_shape_gates": required,
        "all_required_shapes_passed": all(required.values()),
        "per_increment_counts": rows,
        "candidate_axis_count": source_contract["new_block_axis_count"],
        "retained_original_leg_runner_axis_count": source_contract["retained_original_leg_runner_axis_count"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "legacy-a12-replay.json")
    args = parser.parse_args()

    paths = {
        "legacy_exporter": ROOT / LEGACY_EXPORTER,
        "legacy_response": ROOT / LEGACY_RESPONSE,
        "legacy_report": ROOT / LEGACY_REPORT,
        "legacy_screen": ROOT / LEGACY_SCREEN,
        "controls_model": ROOT / CONTROLS_MODEL,
        "controls_deck": ROOT / CONTROLS_DECK,
        "generic_auditor": ROOT / GENERIC_AUDITOR,
        "context_only_summary": ROOT / CONTEXT_ONLY_SUMMARY,
    }
    expected_hashes = {
        "legacy_exporter": LEGACY_EXPORTER_SHA256,
        "legacy_response": LEGACY_RESPONSE_SHA256,
        "legacy_report": LEGACY_REPORT_SHA256,
        "legacy_screen": LEGACY_SCREEN_SHA256,
        "controls_model": CONTROLS_MODEL_SHA256,
        "controls_deck": CONTROLS_DECK_SHA256,
        "generic_auditor": GENERIC_AUDITOR_SHA256,
    }
    observed_hashes = {name: sha256(path) for name, path in paths.items() if path.is_file()}
    missing = [name for name, path in paths.items() if not path.is_file()]
    hash_gates = {name: observed_hashes.get(name) == expected for name, expected in expected_hashes.items()}
    if missing or not all(hash_gates.values()):
        result = {
            "schema": OUTPUT_SCHEMA,
            "status": "BLOCKED_PINNED_READ_ONLY_REPLAY_INPUTS",
            "missing_files": missing,
            "expected_hash_gates": hash_gates,
            "observed_sha256": observed_hashes,
            "historical_files_written": False,
            "native_solve_launched": False,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise SystemExit(result["status"])

    legacy = import_legacy_exporter(paths["legacy_exporter"])
    preflight = legacy.validate_static_inputs(
        ROOT / legacy.DEFAULT_MODEL,
        ROOT / legacy.DEFAULT_CONTRACT,
        ROOT / legacy.DEFAULT_INTERFACE_MAP,
        ROOT / legacy.DEFAULT_CASE_MANIFEST,
    )
    recomputed = legacy.export_report(preflight, paths["legacy_response"])
    stored = load_json(paths["legacy_report"])
    normalized = copy.deepcopy(recomputed)
    saved = copy.deepcopy(stored)
    old_hash = saved["conditional_reference_evidence"]["current_joint_check_summary_context_only"]["sha256"]
    now_hash = normalized["conditional_reference_evidence"]["current_joint_check_summary_context_only"]["sha256"]
    normalized["conditional_reference_evidence"]["current_joint_check_summary_context_only"]["sha256"] = "<context-only-summary-hash>"
    saved["conditional_reference_evidence"]["current_joint_check_summary_context_only"]["sha256"] = "<context-only-summary-hash>"
    payload_equal = normalized == saved

    response = load_json(paths["legacy_response"])
    screen = load_json(paths["legacy_screen"])
    source_pins = screen.get("source_sha256", {})
    controls_model_key = str(CONTROLS_MODEL)
    controls_deck_key = str(CONTROLS_DECK)
    context_fields_absent = [
        key for key in ("case_context_path", "case_context_sha256", "case_context_provenance")
        if key not in response
    ]
    screen_controls_pins = {
        "controls_model_path_present": controls_model_key in source_pins,
        "controls_model_hash_matches": source_pins.get(controls_model_key) == CONTROLS_MODEL_SHA256,
        "controls_deck_path_present": controls_deck_key in source_pins,
        "controls_deck_hash_matches": source_pins.get(controls_deck_key) == CONTROLS_DECK_SHA256,
    }
    shape = expected_report_shapes(recomputed)
    legacy_static_gates_passed = not preflight["failed_static_gates"]
    replay_passed = legacy_static_gates_passed and payload_equal and shape["all_required_shapes_passed"]
    generic_context_recreatable = not context_fields_absent and all(screen_controls_pins.values())

    result = {
        "schema": OUTPUT_SCHEMA,
        "status": "PASS_READ_ONLY_LEGACY_A12_PAYLOAD_REPLAY_WITH_GENERIC_CONTEXT_BLOCKED" if replay_passed and not generic_context_recreatable else "FAIL_REPLAY_OR_UNEXPECTED_CONTEXT_STATE",
        "legacy_replay": {
            "passed_legacy_static_gates": legacy_static_gates_passed,
            "legacy_static_failures": preflight["failed_static_gates"],
            "payload_equal_after_ignoring_only_context_summary_sha256": payload_equal,
            "stored_context_summary_sha256": old_hash,
            "current_context_summary_sha256": now_hash,
            "context_summary_hash_changed": old_hash != now_hash,
            "source_force_projection_recomputed_in_memory_from_pinned_response": True,
            "response_case_id": response.get("case_id"),
            "response_status": response.get("status"),
            "source_model_json_sha256": response.get("source_input_model_json_sha256"),
            "source_deck_sha256": response.get("source_input_deck_sha256"),
            "source_dat_sha256": response.get("native_data_sha256"),
            "source_freeze_sha256": response.get("terminal_execution_provenance", {}).get("freeze_sha256"),
            "source_execution_sha256": response.get("terminal_execution_provenance", {}).get("execution_sha256"),
            "report_sha256": observed_hashes["legacy_report"],
            "payload_shapes": shape,
        },
        "generic_case_context_boundary": {
            "generic_auditor_path": str(GENERIC_AUDITOR),
            "generic_auditor_sha256": observed_hashes["generic_auditor"],
            "response_missing_context_fields": context_fields_absent,
            "legacy_screen_path": str(LEGACY_SCREEN),
            "legacy_screen_sha256": observed_hashes["legacy_screen"],
            "exact_all_bearing_controls_model_path": str(CONTROLS_MODEL),
            "exact_all_bearing_controls_model_sha256": CONTROLS_MODEL_SHA256,
            "exact_all_bearing_controls_deck_path": str(CONTROLS_DECK),
            "exact_all_bearing_controls_deck_sha256": CONTROLS_DECK_SHA256,
            "legacy_screen_controls_source_pins": screen_controls_pins,
            "generic_context_recreatable_from_historical_response_and_screen": generic_context_recreatable,
            "boundary": "The a12 response passed its preserved legacy strict auditor and replays through its pinned legacy exporter. It predates the external generic case-context path/hash/provenance, while its diagnostic screen source map omits the exact all-bearing controls model and deck. Do not synthesize a generic context or treat this replay as a generic case-bound pass.",
        },
        "nonclaims": [
            "This replay does not audit or promote any forward 35/65 or other new response forces.",
            "This replay does not establish generic case-context acceptance for a12 or any other case.",
            "This replay does not establish joint resistance, complete-joint acceptance, floor qualification, fabrication approval, or climbing release.",
        ],
        "historical_files_written": False,
        "native_solve_launched": False,
        "output_only_written_under_new_adapter_folder": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(result["status"])
    if not replay_passed or generic_context_recreatable:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
