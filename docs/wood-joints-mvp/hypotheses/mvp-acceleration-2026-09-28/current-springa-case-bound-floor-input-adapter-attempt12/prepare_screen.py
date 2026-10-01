#!/usr/bin/env python3
"""Build the adapter screen from the pinned K12-right attempt02 diagnosis only."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[5]
SERIES = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = Path(__file__).resolve().parent
REPORT = SERIES / "current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01/k12-right-attempt02-normal-interval-comparison.json"
REPORT_PRODUCER = SERIES / "current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01/produce.py"
CONTROL_MODEL = SERIES / "current-springa-frame-k12-right-all-bearing-attempt01/model.json"
OUTPUT = HERE / "screen.json"

PINNED_REPORT_SHA256 = "5b93018b001657c05b670a2b1aecfce448ba291c09a3307f0b49c9369931ac5c"
PINNED_REPORT_PRODUCER_SHA256 = "dce70caf25249f470266d59ee2372b3e63287e8f7fbfba3795b25916ee8f0d72"
PINNED_CONTROL_MODEL_SHA256 = "f99e6ecbcb3088dca8a740024b92736fd50df2c394a01f25303c14540125f6d9"
REQUIRED_SOURCE_HASHES = {
    str(SERIES / "current-springa-selected-floor-k12-right-attempt02/model.json"): "99d6ae6efff6c2da8a473867cfeb833a3726f536f65392ae2121ff24861a114d",
    str(SERIES / "current-springa-selected-floor-k12-right-attempt02/model.inp"): "f94f315bda1b6d1681f3427d5a93fbb777d7ef901f6a11b78d8762043dac5204",
    str(SERIES / "current-springa-selected-floor-k12-right-attempt02/model.dat"): "aafa8aaed0f08545ae1588aecd113e0d93def81774c6bc308cdbf8803ad779a9",
    str(SERIES / "current-springa-selected-floor-k12-right-attempt02/execution.json"): "df1dc1ee144e0375d341e607a01c3f2acbe5b3b53c83d663d19e37bf33ba58fe",
    str(SERIES / "current-springa-frame-k12-right-all-bearing-attempt01/model.json"): PINNED_CONTROL_MODEL_SHA256,
    str(SERIES / "current-springa-frame-k12-right-all-bearing-attempt01/model.inp"): "fcc6be805a0169dd89628872af29a09e878448313c9f594d09fd15586acbf68f",
    str(SERIES / "current-springa-frame-k12-right-all-bearing-attempt01/model.dat"): "76fd45d0aae2520d90327643c77c47e34babe941eb511c848ab4ef600a313c84",
    str(SERIES / "current-springa-frame-k12-right-all-bearing-attempt01/execution.json"): "baed9ffbe3854d6709ea378619f406212b50fc4f94fdef120470ed322f56641c",
    str(SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py"): "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
}


class ScreenError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScreenError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected_json_object:{path}")
    return value


def build_screen() -> dict[str, Any]:
    require(sha(ROOT / REPORT) == PINNED_REPORT_SHA256, "pinned_attempt02_diagnostic_report_sha256")
    require(sha(ROOT / REPORT_PRODUCER) == PINNED_REPORT_PRODUCER_SHA256, "pinned_attempt02_diagnostic_producer_sha256")
    require(sha(ROOT / CONTROL_MODEL) == PINNED_CONTROL_MODEL_SHA256, "pinned_original_all_bearing_control_model_sha256")
    report = read_json(ROOT / REPORT)
    controls = read_json(ROOT / CONTROL_MODEL)
    require(report.get("schema") == "current_springa_k12_right_attempt02_normal_interval_comparison/v1", "attempt02_interval_report_schema")
    require(report.get("status") == "STABLE_STRICT_SUPPORT_SET_BUT_ATTEMPT02_SELECTED_MASK_REJECTED", "attempt02_expected_diagnostic_outcome")
    require(report.get("case_id") == controls.get("case_id") == "k12-right", "exact_case_id")
    require(report.get("candidate") == controls.get("candidate") and report.get("geometry_revision_id") == controls.get("geometry_revision_id"), "case_candidate_revision_binding")
    require(report["conditional_demand_limit"].get("new_proposal_created") is False, "diagnosis_source_has_no_proposal")
    require(report["conditional_demand_limit"].get("forces_promoted") is False, "diagnosis_source_promotes_no_forces")
    require(report["conditional_demand_limit"].get("corner_demands_usable") is False, "diagnosis_source_has_no_corner_demands")
    require(report["conditional_demand_limit"].get("conditional_case_forces_usable") is False, "diagnosis_source_has_no_case_forces")

    method = report["711_normal_interval_method"]
    require(method.get("normal_carriers_per_state") == 100 and method.get("native_state_count") == 7, "all_normals_all_seven_states")
    require(method.get("strictly_classified_all_100_at_all_seven") is True and method.get("positive_set_stable_all_seven") is True, "strict_stable_interval_set")
    require(method.get("strict_positive_count_per_state") == [11] * 7, "eleven_positive_each_state")
    require(method.get("strictly_separated_count_per_state") == [89] * 7 and method.get("unresolved_count_per_state") == [0] * 7, "eighty_nine_separated_zero_unresolved_each_state")
    require(method.get("terminal_output_validation", {}).get("returncode") == 0 and method.get("terminal_output_validation", {}).get("container_confirmed_terminal") is True, "exact_attempt02_terminal_output_validation")
    rows_per_state = [state.get("rows", []) for state in method["states"]]
    require(all(len(rows) == 100 for rows in rows_per_state), "all_700_source_rows_present")
    positive_sets = [
        {str(row["normal_cell"]) for row in rows if row.get("strictly_positive_bearing") is True}
        for rows in rows_per_state
    ]
    require(all(values == positive_sets[0] for values in positive_sets[1:]), "positive_set_stable_from_saved_rows")
    observed_positive = positive_sets[-1]
    observed_separated = {str(row["normal_cell"]) for row in rows_per_state[-1] if row.get("strictly_separated") is True}
    observed_unresolved = {str(row["normal_cell"]) for row in rows_per_state[-1] if row.get("classification") == "UNRESOLVED_INTERVALS"}
    require(len(observed_positive) == 11 and len(observed_separated) == 89 and not observed_unresolved, "final_partition_11_89_0")
    require(observed_positive == set(report["observed_set_comparison"]["observed_positive_cells_at_final_increment"]), "report_final_positive_set")
    require(report["observed_set_comparison"]["relative_to_prior_attempt11_input"].get("observed_is_strict_superset") is True, "attempt11_plus_right_leg_zero")
    require(report["observed_set_comparison"]["relative_to_prior_attempt11_input"].get("observed_only_cells") == ["floor_lumber_leg_right_0"], "exact_one_added_cell")

    source_bindings = {
        str(binding["name"]): binding for binding in controls.get("unilateral_springa_bindings", [])
        if binding.get("physical_owner", {}).get("role") == "floor_normal"
    }
    require(len(source_bindings) == 100, "original_all_bearing_controls_have_100_normals")
    by_cell = {str(binding["name"]): binding for binding in source_bindings.values()}
    time_rows: list[dict[str, Any]] = []
    for state, report_rows in zip(method["states"], rows_per_state, strict=True):
        output_rows = []
        require({str(row["normal_cell"]) for row in report_rows} == set(by_cell), f"all_source_normal_cells_state_{state['time']}")
        for row in report_rows:
            cell = str(row["normal_cell"])
            binding = by_cell[cell]
            output_rows.append({
                "cell_name": cell,
                "source_group": str(row["source_group"]),
                "physical_owner": binding["physical_owner"],
                "classification": (
                    "STRICTLY_POSITIVE" if row["strictly_positive_bearing"]
                    else "STRICTLY_SEPARATED" if row["strictly_separated"]
                    else "UNRESOLVED_INTERVALS"
                ),
                "strictly_positive_after_rounding": bool(row["strictly_positive_bearing"]),
                "strictly_separating_after_rounding": bool(row["strictly_separated"]),
                "input_mask_status": "selected" if cell in report["prior_right_ten_cell_inputs"]["attempt11"]["selected_cells"] else "inactive",
                "q_interval_mm": row["projected_q_interval_mm"],
                "geometric_elongation_interval_mm": row["geometric_spring_elongation_interval_mm"],
            })
        time_rows.append({
            "time": state["time"],
            "bearing_count": state["strict_positive_count"],
            "separating_count": state["strictly_separated_count"],
            "rows": output_rows,
        })

    attempt02_input = set(report["prior_right_ten_cell_inputs"]["attempt11"]["selected_cells"])
    require(attempt02_input == observed_positive - {"floor_lumber_leg_right_0"}, "attempt02_input_mask_and_diagnosed_new_cell_relation")
    source_hashes = dict(report["artifact_provenance"]["source_file_sha256"])
    for source_path, expected_hash in REQUIRED_SOURCE_HASHES.items():
        require(source_hashes.get(source_path) == expected_hash, f"attempt02_report_source_hash:{source_path}")
    source_hashes[str(REPORT)] = sha(ROOT / REPORT)
    source_hashes[str(REPORT_PRODUCER)] = sha(ROOT / REPORT_PRODUCER)

    attempt = report["attempt02_run"]
    return {
        "schema": "current_case_bound_floor_diagnostic_screen/v1",
        "case_id": "k12-right",
        "candidate": report["candidate"],
        "geometry_revision_id": report["geometry_revision_id"],
        "status": "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH",
        "diagnostic_stage": "selected-proposal-attempt02-own-711-interval-diagnosis",
        "selected_floor_branch_id": "monotone_zero_gap_first_bearing_reference_zero",
        "corner_demands_usable": False,
        "conditional_case_forces_usable": False,
        "physical_force_adoption": False,
        "mechanical_acceptance": False,
        "qualified_for_design": False,
        "frame_ready_for_native_run": False,
        "full_step_native_convergence": True,
        "all_printed_floor_laws_checked": True,
        "all_printed_times": [state["time"] for state in method["states"]],
        "same_positive_cell_set_at_all_printed_times": True,
        "positive_cell_set_stable_across_all_printed_times": True,
        "input_selected_cells": sorted(attempt02_input),
        "input_inactive_cells": sorted(set(by_cell) - attempt02_input),
        "input_selected_cell_count": len(attempt02_input),
        "input_inactive_cell_count": len(by_cell) - len(attempt02_input),
        "diagnostic_positive_cells_at_final_time": sorted(observed_positive),
        "diagnostic_separating_cells_at_final_time": sorted(observed_separated),
        "diagnostic_interval_ambiguous_cells_at_final_time": sorted(observed_unresolved),
        "diagnostic_positive_cell_count_at_final_time": len(observed_positive),
        "diagnostic_separating_cell_count_at_final_time": len(observed_separated),
        "diagnostic_interval_ambiguous_count_at_final_time": len(observed_unresolved),
        "diagnostic_cell_partition_complete_at_final_time": len(observed_positive | observed_separated | observed_unresolved) == 100,
        "selected_now_separated": sorted(attempt02_input & observed_separated),
        "inactive_now_positive": sorted((set(by_cell) - attempt02_input) & observed_positive),
        "input_selected_not_strictly_positive": sorted(attempt02_input - observed_positive),
        "input_inactive_not_strictly_separated": sorted((set(by_cell) - attempt02_input) & (observed_positive | observed_unresolved)),
        "input_mask_to_final_strict_classification_delta": {
            "selected_cells_released_by_observed_pattern": sorted(attempt02_input - observed_positive),
            "inactive_cells_selected_by_observed_pattern": sorted((set(by_cell) - attempt02_input) & observed_positive),
            "old_mask_rows_different": len(attempt02_input ^ observed_positive),
        },
        "native_run_id": attempt["run_id"],
        "terminal_run_provenance": {
            "model_sha256": attempt["model_sha256"],
            "deck_sha256": attempt["deck_sha256"],
            "dat_sha256": attempt["dat_sha256"],
            "execution_sha256": attempt["execution_sha256"],
            "case_context_sha256": attempt["case_context_sha256"],
            "parent_terminal_assessment_sha256": attempt["parent_terminal_assessment_sha256"],
            "native_terminal_returncode": attempt["native_returncode"],
            "native_terminal": attempt["container_confirmed_terminal"],
            "parent_terminal_status": attempt["parent_terminal_status"],
            "parent_terminal_exception": attempt["parent_terminal_exception"],
        },
        "classification_method": "Pinned 711 zero-U wrapper, stable parser, and source-bound interval classifier; all 100 normals at all seven attempt02 increments.",
        "diagnostic_report_path": str(REPORT),
        "diagnostic_report_sha256": sha(ROOT / REPORT),
        "diagnostic_report_producer_path": str(REPORT_PRODUCER),
        "diagnostic_report_producer_sha256": sha(ROOT / REPORT_PRODUCER),
        "input_mask_was_read_from_selected_model": True,
        "selected_source_screen_forces_or_active_states_reused_as_response": False,
        "native_solve_executed_by_screen_producer": False,
        "sources": {
            "classification_lineage": "Only current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01 report; no a12, A1, or earlier K12-right response classification is substituted.",
            "physical_load_and_geometry_authority": "Original current-springa-frame-k12-right-all-bearing-attempt01 model/deck and fresh K12-right register case; the adapter02 rechecks these pins.",
            "prior_mask_comparison_is_context_only": "Attempt03 and attempt11 masks are comparison history in the pinned diagnosis; neither supplies positive cells to this screen.",
        },
        "source_sha256": source_hashes,
        "states": time_rows,
        "limits": [
            "This screen translates the pinned attempt02 normal classifications into the immutable adapter02 input-screen schema; it does not make the rejected attempt02 response pass.",
            "Attempt02 failed the strict 711 response gate because inactive SPR1311 (floor_lumber_leg_right_0) is not strictly separated with zero endpoint reaction.",
            "The 11-cell set is only an input candidate for one separate parent-owned run. No force or active state from attempt02 or a prior case is a response for that new input.",
            "No automatic support-mask iteration, floor friction/anchor, physical force adoption, corner demand export, or joint acceptance is authorized by this screen.",
        ],
        "screen_generation": {
            "producer_path": str(Path(__file__).resolve().relative_to(ROOT)),
            "producer_sha256": sha(Path(__file__).resolve()),
            "input_report_sha256": sha(ROOT / REPORT),
            "original_all_bearing_control_model_sha256": sha(ROOT / CONTROL_MODEL),
        },
    }


def write_or_verify(write: bool) -> None:
    screen = build_screen()
    text = json.dumps(screen, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if write:
        HERE.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(text, encoding="utf-8")
        print(json.dumps({
            "status": screen["status"],
            "case_id": screen["case_id"],
            "selected": len(screen["diagnostic_positive_cells_at_final_time"]),
            "inactive": len(screen["diagnostic_separating_cells_at_final_time"]),
            "unresolved": screen["diagnostic_interval_ambiguous_count_at_final_time"],
            "input_mismatches": screen["input_mask_to_final_strict_classification_delta"]["old_mask_rows_different"],
            "screen_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }, indent=2))
    else:
        require(OUTPUT.is_file(), "attempt12_adapter_screen_exists")
        saved = read_json(OUTPUT)
        require(saved == json.loads(text), "attempt12_adapter_screen_reproduces_from_pinned_attempt02_report")
        require(sha(OUTPUT) == hashlib.sha256(text.encode("utf-8")).hexdigest(), "attempt12_adapter_screen_hash")
        print("verified attempt12 screen derives only from pinned K12-right attempt02 diagnosis and original case controls")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    write_or_verify(args.write)


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError) as error:
        print(f"K12_RIGHT_ATTEMPT12_SCREEN_BLOCKED: {error}", file=sys.stderr)
        raise
