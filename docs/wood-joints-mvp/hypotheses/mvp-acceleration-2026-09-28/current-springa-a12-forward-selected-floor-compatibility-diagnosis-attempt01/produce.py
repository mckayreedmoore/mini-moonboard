#!/usr/bin/env python3
"""Read-only dual-parser compatibility diagnosis of the terminal forward31 run."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import argparse
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
RUN = SERIES / "current-springa-selected-floor-a12-forward-attempt02"
DF1ED_AUDIT = SERIES / "current-springa-case-bound-response-audit-attempt01/response_audit.py"
DF1ED_AUDIT_SHA256 = "df1ed0eedb62ed3657a05a6d679d105e15e63b5ee18b999a731adab190b1b479"
DF1ED_KERNEL = SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py"
DF1ED_KERNEL_SHA256 = "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c"
ZERO_U_AUDIT = SERIES / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
ZERO_U_AUDIT_SHA256 = "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"
ZERO_U_KERNEL = SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
ZERO_U_KERNEL_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"
ZERO_U_REPLAY = SERIES / "current-springa-zero-u-token-response-audit-attempt01/zero_u_token_replay.json"
NORMAL_COUNT = 100
PRINTED_STATE_COUNT = 7
SCHEMA = "current_springa_selected_floor_compatibility_diagnosis/v1"

EXPECTED_RUN_HASHES = {
    "model.json": "b50f560a1296f13a567bf37c17e6cd532ce9699d16b7700421b098aedd1420fe",
    "model.inp": "945c9d568e46e3fe6d68d4e2af8f93c9424cb9f728e6ee555df81b3fd274fa02",
    "model.dat": "50483191809643b2b290741882051bd5ae05548ad751b30cb08e734147374809",
    "execution.json": "472debae02983dbdda7d452de00305a4806eac10fa248b371af86bcf2b2d4e5c",
    "freeze.json": "0bcd8b1a0da170c69e2e2dc1f52397cfcad0c9c10b9a524da3b07c27543f1f42",
    "case-context.json": "30c79f37330cbef1afcfce77a620a4c004950ff544d18cc7e2cdb249501feb81",
}
EXPECTED_DIAGNOSTIC_SCREEN_SHA256 = "3dbb35c1af7deee5b1fbcd9be52c8b7ad10768a8235b207e5c1bcdb2170b80b3"
EXPECTED_PRIOR_SELECTED_SCREEN_SHA256 = "e4c1c0f9b570b0225264c6f9610820d0ffc35bdf51a531bca100fc450504fee7"
EXPECTED_ALL_BEARING_SCREEN_SHA256 = "a4abd064c43de600d857d7f3adcae3fbae9690c3b8bb92dbf8cb7bd77ee809b9"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_path(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def import_auditor(name: str, path: Path, expected_sha: str):
    if sha(path) != expected_sha:
        raise RuntimeError(f"Pinned method source changed: {repo_path(path)}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import pinned method source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _classify(auditor: Any, binding: dict[str, Any], check: dict[str, Any],
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


def _intervals(binding: dict[str, Any], check: dict[str, Any],
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


def _scan(auditor: Any, model: dict[str, Any], deck: str, data: str,
          context: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    case_pin = auditor._validate_case_context(context)
    contract = auditor._validate_model(model, deck, context)
    terminal = auditor._validate_execution(
        run_dir / "model.json", run_dir / "model.dat", run_dir / "model.inp",
        run_dir / "execution.json", data, context,
    )
    states = auditor.parse_native_blocks(data)
    if len(states) != PRINTED_STATE_COUNT or abs(float(max(states)) - 1.0) > 1.0e-12:
        raise RuntimeError("Terminal selected-floor DAT does not have the expected seven-state full ramp")
    expected_nodes = set(map(int, model["nodes"]))
    for time, state in states.items():
        for key in ("u", "u_radius", "rf", "rf_radius"):
            if set(state[key]) != expected_nodes:
                raise RuntimeError(f"DAT has incomplete {key} node fields at {time}")

    selected = set(map(str, model.get("floor_selected_bearing_cells", [])))
    floor_bindings = []
    for binding in contract["bindings"]:
        source = contract["source_by_group"][str(binding["group"])]
        if source.get("role") == "floor_normal":
            floor_bindings.append((binding, source))
    if len(floor_bindings) != NORMAL_COUNT or len(selected) != 31:
        raise RuntimeError("Expected this exact 100-normal forward31 input")

    state_rows = []
    for time, state in states.items():
        rows = []
        for binding, source in floor_bindings:
            # Returned force values are deliberately discarded; only the
            # pinned strict tests and displacement intervals enter the record.
            _native_force, _native_force_radius, check = auditor.audit_springa(
                binding, source, state, contract["emitted_nodes"]
            )
            q_interval, geometric_interval = _intervals(binding, check, state, contract)
            rows.append({
                "cell_name": str(binding["name"]),
                "source_group": str(binding["group"]),
                "source_row_id": str(binding["source_row_id"]),
                "input_mask_status": "selected" if str(binding["name"]) in selected else "inactive",
                "classification": _classify(auditor, binding, check, state, contract),
                "q_interval_mm": q_interval,
                "geometric_elongation_interval_mm": geometric_interval,
            })
        if len(rows) != NORMAL_COUNT or len({row["cell_name"] for row in rows}) != NORMAL_COUNT:
            raise RuntimeError(f"Incomplete or duplicated floor-normal rows at {time}")
        positive = {row["cell_name"] for row in rows if row["classification"] == "STRICTLY_POSITIVE"}
        separated = {row["cell_name"] for row in rows
                     if row["classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"}
        ambiguous = {row["cell_name"] for row in rows
                     if row["classification"] == "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"}
        state_rows.append({
            "load_factor": float(time),
            "positive_count": len(positive),
            "separated_count": len(separated),
            "ambiguous_or_noncomplementary_count": len(ambiguous),
            "observed_positive_cells_diagnostic_only": sorted(positive),
            "rows": rows,
        })
    return {
        "case_pin": case_pin,
        "terminal": terminal,
        "states": state_rows,
        "selected_cells": sorted(selected),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="write the derived JSON files to a clean directory inside this checkout",
    )
    args = parser.parse_args()
    output_dir = (args.output_dir.resolve() if args.output_dir
                  else Path(__file__).resolve().parent)
    if not output_dir.is_relative_to(ROOT):
        raise RuntimeError("Output directory must remain inside the repository checkout")
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.glob("diagnosis.json")) or any(output_dir.glob("source-pins.json")):
        raise RuntimeError("Refusing to overwrite a completed diagnosis packet")

    for name, expected in EXPECTED_RUN_HASHES.items():
        if sha(RUN / name) != expected:
            raise RuntimeError(f"Pinned selected run file changed: {name}")
    model_path, deck_path, data_path = RUN / "model.json", RUN / "model.inp", RUN / "model.dat"
    context_path = RUN / "case-context.json"
    model, deck, data, context = load_json(model_path), deck_path.read_text(), data_path.read_text(errors="replace"), load_json(context_path)
    execution = load_json(RUN / "execution.json")
    if (execution.get("run_id") != "springa-selected-a12-forward-attempt02"
            or execution.get("returncode") != 0
            or execution.get("container_confirmed_terminal") is not True):
        raise RuntimeError("Pinned selected-floor run is not the expected terminal run")
    if model.get("case_id") != "a12-forward" or model.get("floor_branch_metadata", {}).get("diagnostic_stage") != "selected-proposal":
        raise RuntimeError("Run is not the expected case-bound selected proposal")

    screen_pin_path = ROOT / context["diagnostic_floor_screen_path"]
    prior_selected_screen = SERIES / "current-springa-a12-forward-selected-floor-screen-attempt01/screen.json"
    all_bearing_screen = SERIES / "current-springa-a12-forward-floor-screen-attempt01/screen.json"
    for path, expected in (
        (screen_pin_path, EXPECTED_DIAGNOSTIC_SCREEN_SHA256),
        (prior_selected_screen, EXPECTED_PRIOR_SELECTED_SCREEN_SHA256),
        (all_bearing_screen, EXPECTED_ALL_BEARING_SCREEN_SHA256),
    ):
        if sha(path) != expected:
            raise RuntimeError(f"Pinned prior diagnostic screen changed: {repo_path(path)}")

    df1ed = import_auditor("pinned_df1ed_forward_auditor", DF1ED_AUDIT, DF1ED_AUDIT_SHA256)
    zero_u = import_auditor("pinned_zero_u_711_forward_auditor", ZERO_U_AUDIT, ZERO_U_AUDIT_SHA256)
    # These are the exact recovery kernels named by the two wrapper sources.
    if sha(DF1ED_KERNEL) != DF1ED_KERNEL_SHA256 or sha(ZERO_U_KERNEL) != ZERO_U_KERNEL_SHA256:
        raise RuntimeError("One pinned response recovery kernel changed")
    df = _scan(df1ed, model, deck, data, context, RUN)
    zu = _scan(zero_u, model, deck, data, context, RUN)
    times_df = [row["load_factor"] for row in df["states"]]
    times_zu = [row["load_factor"] for row in zu["states"]]
    if times_df != times_zu:
        raise RuntimeError("Pinned parsers produced different printed-state histories")

    current_input = set(df["selected_cells"])
    prior_all_bearing = set(map(str, load_json(all_bearing_screen)["diagnostic_positive_cells_at_final_time"]))
    prior_selected = load_json(prior_selected_screen)
    prior_31 = set(map(str, prior_selected["stable_actual_normal_law_mask"]["strictly_positive_cells"]))
    previous_masks = {
        "attempt02_input_31": current_input,
        "original_all_bearing_35": prior_all_bearing,
        "attempt01_selected_input_35": set(map(str, prior_selected["original_proposed_mask"]["selected_cells"])),
        "attempt01_observed_positive_31": prior_31,
        "normalized_attempt02_screen_31": set(map(str, load_json(screen_pin_path)["diagnostic_positive_cells_at_final_time"])),
    }

    states_out = []
    for index, (row_df, row_zu) in enumerate(zip(df["states"], zu["states"], strict=True)):
        by_df = {row["cell_name"]: row for row in row_df["rows"]}
        by_zu = {row["cell_name"]: row for row in row_zu["rows"]}
        if set(by_df) != set(by_zu):
            raise RuntimeError("Pinned parser classifications do not share the same 100 normal cells")
        rows = []
        for cell in sorted(by_df):
            left, right = by_df[cell], by_zu[cell]
            rows.append({
                "cell_name": cell,
                "source_group": left["source_group"],
                "source_row_id": left["source_row_id"],
                "input_mask_status": left["input_mask_status"],
                "df1ed_classification": left["classification"],
                "zero_u_711_classification": right["classification"],
                "df1ed_q_interval_mm": left["q_interval_mm"],
                "df1ed_geometric_elongation_interval_mm": left["geometric_elongation_interval_mm"],
                "zero_u_711_q_interval_mm": right["q_interval_mm"],
                "zero_u_711_geometric_elongation_interval_mm": right["geometric_elongation_interval_mm"],
            })
        positive_df = {row["cell_name"] for row in rows if row["df1ed_classification"] == "STRICTLY_POSITIVE"}
        separated_df = {row["cell_name"] for row in rows if row["df1ed_classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"}
        ambiguous_df = {row["cell_name"] for row in rows if row["df1ed_classification"] == "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"}
        positive_zu = {row["cell_name"] for row in rows if row["zero_u_711_classification"] == "STRICTLY_POSITIVE"}
        separated_zu = {row["cell_name"] for row in rows if row["zero_u_711_classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"}
        ambiguous_zu = {row["cell_name"] for row in rows if row["zero_u_711_classification"] == "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"}
        states_out.append({
            "load_factor": times_df[index],
            "df1ed_counts": {"positive": len(positive_df), "separated": len(separated_df), "ambiguous_or_noncomplementary": len(ambiguous_df)},
            "zero_u_711_counts": {"positive": len(positive_zu), "separated": len(separated_zu), "ambiguous_or_noncomplementary": len(ambiguous_zu)},
            "zero_u_711_mask_compatible_with_attempt02_input": positive_zu == current_input and separated_zu == set(df["case_pin"]["inactive_cells"]),
            "observed_positive_cells_diagnostic_only": sorted(positive_zu),
            "rows": rows,
        })

    final_rows = states_out[-1]["rows"]
    observed = set(states_out[-1]["observed_positive_cells_diagnostic_only"])
    inactive = set(df["case_pin"]["inactive_cells"])
    selected_not_positive = sorted(current_input - observed)
    inactive_positive = sorted(inactive & observed)
    stable_mask = all(set(state["observed_positive_cells_diagnostic_only"]) == observed for state in states_out)
    equality = {
        name: [set(state["observed_positive_cells_diagnostic_only"]) == mask for state in states_out]
        for name, mask in previous_masks.items()
    }

    # Include source and method files plus every explicit case/context pin.
    source_paths: set[Path] = {
        Path(__file__).resolve(), DF1ED_AUDIT.resolve(), DF1ED_KERNEL.resolve(),
        ZERO_U_AUDIT.resolve(), ZERO_U_KERNEL.resolve(), ZERO_U_REPLAY.resolve(),
        model_path.resolve(), deck_path.resolve(), data_path.resolve(), context_path.resolve(),
        (RUN / "execution.json").resolve(), (RUN / "freeze.json").resolve(),
        (RUN / "authorization.json").resolve(), (RUN / "native.stdout").resolve(),
        (RUN / "native.stderr").resolve(), (RUN / "parent-serialized-input-audit.json").resolve(),
        (RUN / "parent-readiness-review.json").resolve(), (RUN / "parent-case-context-check.json").resolve(),
        screen_pin_path.resolve(), prior_selected_screen.resolve(), all_bearing_screen.resolve(),
        (SERIES / "current-springa-selected-floor-a12-forward-attempt01/model.json").resolve(),
        (SERIES / "current-springa-selected-floor-a12-forward-attempt01/model.inp").resolve(),
        (SERIES / "current-springa-selected-floor-a12-forward-attempt01/model.dat").resolve(),
        (SERIES / "current-springa-selected-floor-a12-forward-attempt01/execution.json").resolve(),
        (SERIES / "current-springa-selected-floor-a12-forward-attempt01/freeze.json").resolve(),
        (SERIES / "current-springa-selected-floor-a12-forward-attempt01/case-context.json").resolve(),
        (SERIES / "current-springa-a12-forward-floor-screen-attempt01/produce.py").resolve(),
        (SERIES / "current-springa-a12-forward-selected-floor-screen-attempt01/produce.py").resolve(),
        (SERIES / "current-forward-selected-screen-contract-projection-attempt01/project.py").resolve(),
        (SERIES / "current-springa-zero-u-token-response-audit-attempt01/replay_zero_u_tokens.py").resolve(),
        (SERIES / "current-springa-case-bound-response-audit-attempt01/method_fixture_check.json").resolve(),
        (SERIES / "current-springa-zero-u-token-response-audit-attempt01/zero_u_token_replay.json").resolve(),
    }
    for key in (
        "source_controls_model_json_path", "source_controls_deck_path", "source_controls_execution_path",
        "source_controls_terminal_dat_path", "diagnostic_floor_screen_path", "source_case_load_register_path",
        "source_fresh_case_model_path", "selected_floor_model_json_path", "selected_floor_deck_path",
    ):
        value = context.get(key)
        if value:
            candidate = Path(value)
            resolved = candidate.resolve() if candidate.is_absolute() else (ROOT / candidate).resolve()
            if resolved.is_file():
                source_paths.add(resolved)
    if any(not path.is_file() for path in source_paths):
        missing = sorted(str(path) for path in source_paths if not path.is_file())
        raise RuntimeError("One or more required diagnosis pins are missing: " + ", ".join(missing))
    source_sha256 = {repo_path(path): sha(path) for path in sorted(source_paths)}

    result = {
        "schema": SCHEMA,
        "status": "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH_DIAGNOSTIC_ONLY",
        "case_id": model["case_id"],
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "native_run_id": execution["run_id"],
        "terminal_native_output_consumed": True,
        "full_step_native_convergence": True,
        "corner_demands_usable": False,
        "mechanical_acceptance": False,
        "physical_force_adoption": False,
        "response_force_exported": False,
        "normal_force_or_rf_values_written": False,
        "new_floor_input_mask_created": False,
        "native_solve_launched_by_diagnosis": False,
        "input_selected_cell_count": len(current_input),
        "input_inactive_cell_count": len(inactive),
        "input_selected_cells": sorted(current_input),
        "input_inactive_cells": sorted(inactive),
        "all_100_floor_normal_laws_checked_at_every_printed_state": True,
        "all_printed_load_factors": times_df,
        "history": states_out,
        "zero_u_711_stable_observed_positive_mask": stable_mask,
        "zero_u_711_observed_positive_count": len(observed),
        "zero_u_711_observed_separated_count": NORMAL_COUNT - len(observed),
        "zero_u_711_observed_positive_cells_diagnostic_only": sorted(observed),
        "selected_cells_not_strictly_positive": selected_not_positive,
        "inactive_cells_strictly_positive": inactive_positive,
        "zero_u_711_mask_exactly_repeats_a_prior_mask": {
            name: all(values) for name, values in equality.items()
        },
        "zero_u_711_prior_mask_cell_overlaps": {
            name: len(observed & mask) for name, mask in previous_masks.items()
        },
        "classification_recurrence_finding": {
            "zero_u_711_observed_positive_mask_is_identical_at_all_seven_states": stable_mask,
            "mask_matches_any_prior_allbearing_or_selected_mask": any(all(values) for values in equality.values()),
            "support_polarity_reversal_observed_between_printed_states": False,
            "interpretation": "Stable selected-mask incompatibility, not a state-to-state support reversal/cycle or SPR1026 interval ambiguity.",
        },
        "spr1026_diagnostic": {
            "cell_name": "floor_base_floor_left_1",
            "source_group": "SPR1026",
            "selected_in_attempt02_input": "floor_base_floor_left_1" in current_input,
            "df1ed_classification_by_state": [
                next(row["df1ed_classification"] for row in state["rows"] if row["source_group"] == "SPR1026")
                for state in states_out
            ],
            "zero_u_711_classification_by_state": [
                next(row["zero_u_711_classification"] for row in state["rows"] if row["source_group"] == "SPR1026")
                for state in states_out
            ],
            "df1ed_q_intervals_mm": [
                next(row["df1ed_q_interval_mm"] for row in state["rows"] if row["source_group"] == "SPR1026")
                for state in states_out
            ],
            "df1ed_geometric_elongation_intervals_mm": [
                next(row["df1ed_geometric_elongation_interval_mm"] for row in state["rows"] if row["source_group"] == "SPR1026")
                for state in states_out
            ],
            "zero_u_711_q_intervals_mm": [
                next(row["zero_u_711_q_interval_mm"] for row in state["rows"] if row["source_group"] == "SPR1026")
                for state in states_out
            ],
            "zero_u_711_geometric_elongation_intervals_mm": [
                next(row["zero_u_711_geometric_elongation_interval_mm"] for row in state["rows"] if row["source_group"] == "SPR1026")
                for state in states_out
            ],
            "force_and_rf_interval_values_withheld": True,
        },
        "zero_u_precision_change_diagnostic": {
            "cell_name": "floor_base_floor_right_2",
            "source_group": "SPR1143",
            "df1ed_classification_first_two_states": [
                next(row["df1ed_classification"] for row in state["rows"] if row["source_group"] == "SPR1143")
                for state in states_out[:2]
            ],
            "zero_u_711_classification_first_two_states": [
                next(row["zero_u_711_classification"] for row in state["rows"] if row["source_group"] == "SPR1143")
                for state in states_out[:2]
            ],
            "interpretation": "The exact-zero U-token radius change resolves this separate early-state interval ambiguity; it does not change SPR1026, which remains strictly separated under both methods.",
        },
        "method_pins": {
            "df1ed_auditor_path": repo_path(DF1ED_AUDIT),
            "df1ed_auditor_sha256": DF1ED_AUDIT_SHA256,
            "df1ed_springa_kernel_path": repo_path(DF1ED_KERNEL),
            "df1ed_springa_kernel_sha256": DF1ED_KERNEL_SHA256,
            "zero_u_711_auditor_path": repo_path(ZERO_U_AUDIT),
            "zero_u_711_auditor_sha256": ZERO_U_AUDIT_SHA256,
            "zero_u_711_parser_kernel_path": repo_path(ZERO_U_KERNEL),
            "zero_u_711_parser_kernel_sha256": ZERO_U_KERNEL_SHA256,
            "zero_u_method_replay_path": repo_path(ZERO_U_REPLAY),
            "zero_u_method_replay_sha256": sha(ZERO_U_REPLAY),
            "classification_methods": ["audit_springa", "_strict_normal_branch_check(selected=True)",
                                        "_strict_normal_branch_check(selected=False)"],
            "displacement_intervals_written": ["projected q", "geometric spring elongation"],
            "native_force_and_RF_numeric_values_written": False,
        },
        "source_sha256": source_sha256,
        "limits": [
            "This is a read-only classification of one already completed a12-forward 31/69 run.",
            "The stable 37/63 result is a compatibility diagnosis only; it is not a selected input mask or an accepted support state.",
            "No force response, corner demand, support qualification, or resistance is adopted.",
            "No next mask, automatic iteration, release/recontact method, or branch uniqueness is proposed.",
        ],
    }
    diagnosis_path = output_dir / "diagnosis.json"
    diagnosis_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    pin_record = {
        "schema": "current_springa_a12_forward_compatibility_diagnosis_source_pins/v1",
        "case_id": "a12-forward",
        "source_sha256": source_sha256,
        "diagnosis_sha256": sha(diagnosis_path),
    }
    (output_dir / "source-pins.json").write_text(json.dumps(pin_record, indent=2) + "\n")
    print(json.dumps({
        "status": result["status"],
        "diagnosis_path": repo_path(diagnosis_path),
        "diagnosis_sha256": sha(diagnosis_path),
        "producer_sha256": sha(Path(__file__)),
        "printed_state_count": len(states_out),
        "zero_u_positive_count": result["zero_u_711_observed_positive_count"],
        "zero_u_separated_count": result["zero_u_711_observed_separated_count"],
        "selected_not_positive_count": len(selected_not_positive),
        "inactive_positive_count": len(inactive_positive),
        "spr1026_selected_and_separated_all_states": all(
            name == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"
            for name in result["spr1026_diagnostic"]["zero_u_711_classification_by_state"]
        ),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
