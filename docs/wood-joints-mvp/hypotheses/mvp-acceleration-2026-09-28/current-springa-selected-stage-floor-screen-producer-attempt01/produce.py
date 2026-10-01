#!/usr/bin/env python3
"""Read-only, case-bound screen of all floor SPRINGA normals in a selected run.

This producer only classifies printed displacement intervals. It writes no
native force or reaction values and never launches or modifies a solver run.
"""
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
AUDITOR_PATH = SERIES / "current-springa-case-bound-response-audit-attempt01/response_audit.py"
AUDITOR_SHA256 = "df1ed0eedb62ed3657a05a6d679d105e15e63b5ee18b999a731adab190b1b479"
STABLE_PATH = SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py"
STABLE_SHA256 = "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c"
OUTPUT_SCHEMA = "current_case_bound_floor_diagnostic_screen/v1"
PRODUCER_AUDIT_SCHEMA = "current_case_bound_floor_diagnostic_screen_producer_audit/v1"
EXPECTED_TIMES = 7


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_path(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def import_pinned_auditor():
    if sha(AUDITOR_PATH) != AUDITOR_SHA256:
        raise RuntimeError("Pinned df1ed case-bound response auditor changed")
    if sha(STABLE_PATH) != STABLE_SHA256:
        raise RuntimeError("Pinned b20 SPRINGA response kernel changed")
    spec = importlib.util.spec_from_file_location("pinned_df1ed_case_response_auditor", AUDITOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import pinned case-bound response auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strict_pass(auditor: Any, binding: dict[str, Any], check: dict[str, Any],
                state: dict[str, Any], contract: dict[str, Any], selected: bool) -> bool:
    try:
        auditor._strict_normal_branch_check(binding, check, state, contract, selected)
        return True
    except auditor.ResponseAuditError:
        return False


def classify_one(auditor: Any, binding: dict[str, Any], source: dict[str, Any],
                 state: dict[str, Any], contract: dict[str, Any], input_selected: bool) -> dict[str, Any]:
    # The native force/RF values returned here are used only by the pinned
    # conservative classifier and are deliberately not copied to output.
    _force, _radius, check = auditor.audit_springa(
        binding, source, state, contract["emitted_nodes"]
    )
    positive = strict_pass(auditor, binding, check, state, contract, True)
    separated = strict_pass(auditor, binding, check, state, contract, False)

    q = float(check["q_relative_projection_mm"])
    q_radius = float(check["q_relative_projection_radius_mm"])
    q_low, q_high = q - q_radius, q + q_radius

    q_node, ground = map(int, binding["springa_nodes"])
    q_vector = [float(state["u"][q_node][i]) - float(state["u"][ground][i]) for i in range(3)]
    q_vector_radius = [float(state["u_radius"][q_node][i])
                       + float(state["u_radius"][ground][i]) for i in range(3)]
    current_vector = [
        float(contract["emitted_nodes"][q_node][i])
        - float(contract["emitted_nodes"][ground][i]) + q_vector[i]
        for i in range(3)
    ]
    current_length = math.sqrt(sum(value * value for value in current_vector))
    axis = [float(value) for value in binding["numerical_axis_global_xyz"]]
    current_axis = [value / current_length for value in current_vector] if current_length > 0.0 else axis
    geometric_radius = (
        sum(abs(current_axis[i]) * q_vector_radius[i] for i in range(3))
        + float(check["geometric_length_subtraction_arithmetic_guard_mm"])
    )
    geometric = float(check["geometric_spring_elongation_mm"])
    geometric_interval = [geometric - geometric_radius, geometric + geometric_radius]

    if positive and not separated:
        classification = "STRICTLY_POSITIVE"
    elif separated and not positive:
        classification = "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"
    else:
        # Covers a near-zero/contradictory interval or failure of both complete
        # strict tests. No ambiguous row is promoted to either mask.
        classification = "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"

    return {
        "cell_name": str(binding["name"]),
        "source_group": str(binding["group"]),
        "physical_owner": binding["physical_owner"],
        "input_mask_status": "selected" if input_selected else "inactive",
        "classification": classification,
        "strictly_positive_after_rounding": positive,
        "strictly_separating_after_rounding": separated,
        "q_diagnostic_mm": q,
        "q_radius_mm": q_radius,
        "q_interval_mm": [q_low, q_high],
        "geometric_elongation_interval_mm": geometric_interval,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, help="Existing frozen selected-floor native run directory")
    parser.add_argument("--context", required=True, help="Exact case-context.json used by the pinned response auditor")
    parser.add_argument("--output-dir", required=True, help="New case-local screen packet directory")
    parser.add_argument("--expected-run-id", required=True, help="Expected run_id from the existing execution.json")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    context_path = Path(args.context)
    context_path = context_path.resolve() if context_path.is_absolute() else (ROOT / context_path).resolve()
    output_dir = Path(args.output_dir)
    output_dir = output_dir.resolve() if output_dir.is_absolute() else (ROOT / output_dir).resolve()
    if not run_dir.is_dir() or not context_path.is_file():
        raise RuntimeError("Selected run directory or case context is missing")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError("Refusing to overwrite a nonempty screen output directory")
    output_dir.mkdir(parents=True, exist_ok=True)

    auditor = import_pinned_auditor()
    context = load_json(context_path)
    case_pin = auditor._validate_case_context(context)
    model_path, deck_path = run_dir / "model.json", run_dir / "model.inp"
    data_path, execution_path = run_dir / "model.dat", run_dir / "execution.json"
    model, deck, data = load_json(model_path), deck_path.read_text(), data_path.read_text(errors="replace")
    execution = load_json(execution_path)
    if execution.get("run_id") != args.expected_run_id:
        raise RuntimeError("Existing run_id does not match the explicit command pin")
    if Path(case_pin["resolved"]["selected_input_model_json_path"]).resolve() != model_path:
        raise RuntimeError("Case context does not pin this direct selected-run model")
    if Path(case_pin["resolved"]["selected_input_deck_path"]).resolve() != deck_path:
        raise RuntimeError("Case context does not pin this direct selected-run deck")
    contract = auditor._validate_model(model, deck, context)
    terminal = auditor._validate_execution(model_path, data_path, deck_path,
                                           execution_path, data, context)
    states = auditor.parse_native_blocks(data)
    if len(states) != EXPECTED_TIMES or not states or abs(float(max(states)) - 1.0) > 1.0e-12:
        raise RuntimeError(f"Expected seven complete printed states ending at load factor 1.0, got {list(states)}")
    expected_nodes = set(map(int, model["nodes"]))
    for time, state in states.items():
        for key in ("u", "u_radius", "rf", "rf_radius"):
            if set(state[key]) != expected_nodes:
                raise RuntimeError(f"Incomplete {key} node inventory at printed time {time}")

    input_selected = set(map(str, model.get("floor_selected_bearing_cells", [])))
    input_inactive = set(map(str, model.get("floor_inactive_cells", [])))
    floor_bindings = []
    for binding in contract["bindings"]:
        source = contract["source_by_group"][str(binding["group"])]
        if source.get("role") == "floor_normal":
            floor_bindings.append((binding, source))
    all_cells = {str(binding["name"]) for binding, _source in floor_bindings}
    if (len(floor_bindings) != 100 or len(all_cells) != 100
            or input_selected & input_inactive
            or input_selected | input_inactive != all_cells
            or len(input_selected) != int(model.get("floor_branch_metadata", {}).get("selected_cell_count", -1))):
        raise RuntimeError("Serialized selected input does not contain a complete, disjoint 100-cell floor mask")

    states_out = []
    for time, state in states.items():
        rows = [classify_one(auditor, binding, source, state, contract,
                             str(binding["name"]) in input_selected)
                for binding, source in floor_bindings]
        positive_cells = {row["cell_name"] for row in rows if row["strictly_positive_after_rounding"]}
        separated_cells = {row["cell_name"] for row in rows if row["strictly_separating_after_rounding"]}
        ambiguous_cells = {row["cell_name"] for row in rows
                           if row["classification"] == "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"}
        if len(positive_cells | separated_cells | ambiguous_cells) != 100:
            raise RuntimeError(f"Floor normal classifications are incomplete at printed time {time}")
        states_out.append({
            "time": float(time),
            "bearing_count": len(positive_cells),
            "separating_count": len(separated_cells),
            "interval_ambiguous_count": len(ambiguous_cells),
            "rows": rows,
        })

    positive_sets = [
        {row["cell_name"] for row in state["rows"] if row["strictly_positive_after_rounding"]}
        for state in states_out
    ]
    final_rows = states_out[-1]["rows"]
    strict_positive = sorted(row["cell_name"] for row in final_rows if row["strictly_positive_after_rounding"])
    strict_separated = sorted(row["cell_name"] for row in final_rows if row["strictly_separating_after_rounding"])
    final_ambiguous = sorted(row["cell_name"] for row in final_rows
                             if row["classification"] == "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY")
    stable_positive = all(cells == positive_sets[0] for cells in positive_sets)
    status = "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"

    # Pin direct selected run, original all-bearing controls, original source
    # screen, source case/register, both audit kernels, and this producer.
    source_paths: set[Path] = {
        AUDITOR_PATH.resolve(), STABLE_PATH.resolve(), Path(__file__).resolve(), context_path,
        model_path.resolve(), deck_path.resolve(), data_path.resolve(), execution_path.resolve(),
    }
    for key in (
        "source_controls_model_json_path", "source_controls_deck_path",
        "diagnostic_floor_screen_path", "source_case_load_register_path",
    ):
        source_paths.add(auditor._context_path(str(context[key])).resolve())
    for key in ("source_controls_execution_path", "source_controls_terminal_dat_path"):
        if context.get(key):
            source_paths.add(auditor._context_path(str(context[key])).resolve())
    for key in ("source_fresh_case_model_path", "selected_floor_model_json_path", "selected_floor_deck_path"):
        if context.get(key):
            source_paths.add(auditor._context_path(str(context[key])).resolve())
    for name in ("freeze.json", "native.stdout", "native.stderr", "authorization.json",
                 "parent-serialized-input-audit.json", "parent-readiness-review.json",
                 "parent-case-context-check.json"):
        candidate = run_dir / name
        if candidate.is_file():
            source_paths.add(candidate.resolve())
    controls_model_path = case_pin["resolved"]["source_controls_model_json_path"]
    controls_deck_path = case_pin["resolved"]["source_controls_deck_path"]
    if controls_model_path not in source_paths or controls_deck_path not in source_paths:
        raise RuntimeError("Source pin inventory omits the exact all-bearing controls input model/deck")
    source_sha256 = {repo_path(path): sha(path) for path in sorted(source_paths)}
    if (source_sha256[repo_path(controls_model_path)] != context["source_controls_model_json_sha256"]
            or source_sha256[repo_path(controls_deck_path)] != context["source_controls_deck_sha256"]):
        raise RuntimeError("All-bearing controls source hashes differ from case context")

    all_printed_times = [float(value) for value in states]
    source_screen = load_json(case_pin["resolved"]["diagnostic_floor_screen_path"])
    source_times = [float(value) for value in source_screen.get("all_printed_times", [])]
    if len(source_times) != EXPECTED_TIMES or any(
        abs(actual - expected) > 1.0e-12 for actual, expected in zip(all_printed_times, source_times, strict=True)
    ):
        raise RuntimeError("Direct selected run printed-state times differ from its case-bound source screen")

    screen = {
        "schema": OUTPUT_SCHEMA,
        "case_id": model["case_id"],
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "status": status,
        "diagnostic_stage": "selected-floor-proposal-all-normal-screen",
        "selected_floor_branch_id": model.get("floor_branch_metadata", {}).get("branch_id"),
        "corner_demands_usable": False,
        "physical_force_adoption": False,
        "mechanical_acceptance": False,
        "qualified_for_design": False,
        "frame_ready_for_native_run": False,
        "full_step_native_convergence": terminal["returncode"] == 0 and terminal["container_confirmed_terminal"] is True,
        "all_printed_floor_laws_checked": all(len(state["rows"]) == 100 for state in states_out),
        "all_printed_times": all_printed_times,
        "same_positive_cell_set_at_all_printed_times": stable_positive,
        "positive_cell_set_stable_across_all_printed_times": stable_positive,
        "input_selected_cells": sorted(input_selected),
        "input_inactive_cells": sorted(input_inactive),
        "input_selected_cell_count": len(input_selected),
        "input_inactive_cell_count": len(input_inactive),
        "diagnostic_positive_cells_at_final_time": strict_positive,
        "diagnostic_separating_cells_at_final_time": strict_separated,
        "diagnostic_interval_ambiguous_cells_at_final_time": final_ambiguous,
        "diagnostic_positive_cell_count_at_final_time": len(strict_positive),
        "diagnostic_separating_cell_count_at_final_time": len(strict_separated),
        "diagnostic_interval_ambiguous_count_at_final_time": len(final_ambiguous),
        "diagnostic_cell_partition_complete_at_final_time": len(strict_positive) + len(strict_separated) + len(final_ambiguous) == 100,
        "selected_now_separated": sorted(input_selected & set(strict_separated)),
        "inactive_now_positive": sorted(input_inactive & set(strict_positive)),
        "input_selected_not_strictly_positive": sorted(input_selected - set(strict_positive)),
        "input_inactive_not_strictly_separated": sorted(input_inactive - set(strict_separated)),
        "input_mask_to_final_strict_classification_delta": {
            "selected_but_not_strictly_positive": sorted(input_selected - set(strict_positive)),
            "inactive_but_strictly_positive": sorted(input_inactive & set(strict_positive)),
            "final_interval_ambiguous": final_ambiguous,
        },
        "native_run_id": execution["run_id"],
        "terminal_run_provenance": terminal,
        "source_sha256": source_sha256,
        "classification_method": {
            "pinned_auditor_path": repo_path(AUDITOR_PATH),
            "pinned_auditor_sha256": AUDITOR_SHA256,
            "pinned_springa_kernel_path": repo_path(STABLE_PATH),
            "pinned_springa_kernel_sha256": STABLE_SHA256,
            "classification_calls": ["audit_springa", "_strict_normal_branch_check(selected=True)",
                                      "_strict_normal_branch_check(selected=False)"],
            "positive_requires_complete_strict_projected_geometric_and_native_law_test": True,
            "separation_requires_negative_projected_and_geometric_intervals_zero_native_force_and_zero_endpoint_rf": True,
            "dual_intervals_written": ["relative_projection_q_mm", "geometric_spring_elongation_mm"],
            "raw_native_force_values_written": False,
            "raw_endpoint_rf_values_written": False,
        },
        "input_mask_was_read_from_selected_model": True,
        "selected_source_screen_forces_or_active_states_reused_as_response": False,
        "native_solve_executed_by_screen_producer": False,
        "states": states_out,
        "limits": [
            "This screen reclassifies all 100 normal carriers in an already completed, case-bound selected-floor run.",
            "It reports displacement intervals and conservative classifications only; physical forces and reactions are withheld.",
            "A stable positive set is a rejected-branch diagnostic for parent-controlled next-step review, not accepted support or corner demand.",
            "No mask iteration, release/recontact algorithm, uniqueness, mechanical acceptance, or design qualification is claimed.",
        ],
    }
    screen_path = output_dir / "screen.json"
    screen_path.write_text(json.dumps(screen, indent=2, allow_nan=False) + "\n")
    source_pins = {
        "schema": "current_case_bound_floor_screen_source_pins/v1",
        "case_id": model["case_id"],
        "source_sha256": source_sha256,
        "screen_sha256": sha(screen_path),
    }
    (output_dir / "source-pins.json").write_text(json.dumps(source_pins, indent=2) + "\n")
    audit = {
        "schema": PRODUCER_AUDIT_SCHEMA,
        "status": "PASS_READ_ONLY_ALL_NORMAL_SELECTED_STAGE_SCREEN",
        "screen_path": repo_path(screen_path),
        "screen_sha256": sha(screen_path),
        "producer_path": repo_path(Path(__file__)),
        "producer_sha256": sha(Path(__file__)),
        "pinned_auditor_sha256": AUDITOR_SHA256,
        "pinned_springa_kernel_sha256": STABLE_SHA256,
        "case_id": model["case_id"],
        "native_run_id": execution["run_id"],
        "normal_binding_count": len(floor_bindings),
        "printed_state_count": len(states_out),
        "all_state_rows_complete": all(len(state["rows"]) == 100 for state in states_out),
        "stable_positive_cell_set": stable_positive,
        "final_positive_count": len(strict_positive),
        "final_separated_count": len(strict_separated),
        "final_ambiguous_count": len(final_ambiguous),
        "input_selected_count": len(input_selected),
        "selected_but_not_positive_count": len(input_selected - set(strict_positive)),
        "inactive_but_positive_count": len(input_inactive & set(strict_positive)),
        "raw_force_values_written": False,
        "raw_rf_values_written": False,
        "native_solve_launched_by_producer": False,
        "source_sha256": source_sha256,
    }
    (output_dir / "audit.json").write_text(json.dumps(audit, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: audit[key] for key in (
        "status", "screen_path", "screen_sha256", "case_id", "native_run_id",
        "printed_state_count", "final_positive_count", "final_separated_count",
        "final_ambiguous_count", "stable_positive_cell_set", "selected_but_not_positive_count",
        "inactive_but_positive_count",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
