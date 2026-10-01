#!/usr/bin/env python3
"""Read-only normal-law screen of the pinned K12-rear native response."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
SOURCE = SERIES / "current-springa-frame-k12-rear-all-bearing-attempt01"
AUDITOR = SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
BASELINE_AUDITOR = SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py"
OLD_SCREEN = SERIES / "current-springa-k12-rear-floor-screen-attempt01/screen.json"
OUTPUT = Path(__file__).with_name("screen.json")
sys.path.insert(0, str(ROOT))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path):
    return json.loads(path.read_text())


def main() -> dict:
    spec = importlib.util.spec_from_file_location("zero_u_token_response_audit", AUDITOR)
    require(spec is not None and spec.loader is not None, "cannot load refined response auditor")
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    old_spec = importlib.util.spec_from_file_location("baseline_springa_response_audit", BASELINE_AUDITOR)
    require(old_spec is not None and old_spec.loader is not None, "cannot load original response auditor")
    old_audit = importlib.util.module_from_spec(old_spec)
    old_spec.loader.exec_module(old_audit)

    expected_pins = {
        SOURCE / "model.json": "72cc39411bb92d3ee739a9b9aa9b025fe466f2b818f29feaa76a26c284366424",
        SOURCE / "model.inp": "0cdcee16de7be40e8a7a511c26f6cbf67f116d2475f76eab294fa661ee6fac68",
        SOURCE / "model.dat": "8c3c7590e11df6c8bce52e814ece2aba2f05ff24eb261517e95e74db41528807",
        SOURCE / "freeze.json": "161e9b8bfecb7ef4d5060db4d6fb25aeeb38df5fa4332a3ba47fbd92df70ac92",
        SOURCE / "execution.json": "4e10033ba2a12952122ac790ae6c4dcf4a9585b936d239e86d73465be6db6ccc",
        OLD_SCREEN: "",
        BASELINE_AUDITOR: "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
        AUDITOR: "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    }
    old_screen = load(OLD_SCREEN)
    expected_pins[OLD_SCREEN] = ""  # The old screen is independently hashed below.
    for path, expected in expected_pins.items():
        if expected:
            require(sha(path) == expected, f"K12 input/evidence pin mismatch: {path}")
    old_screen_sha256 = sha(OLD_SCREEN)
    model = load(SOURCE / "model.json")
    deck = (SOURCE / "model.inp").read_text()
    dat = (SOURCE / "model.dat").read_text()
    require(not any(line.strip().upper().startswith("*TRANSFORM")
                    for line in deck.splitlines()),
            "K12 source deck uses a transformed coordinate system")
    contract = audit._validate_input_contract(model, deck)
    states = audit.parse_native_blocks(dat)
    old_states = old_audit.parse_native_blocks(dat)
    execution = load(SOURCE / "execution.json")
    freeze = load(SOURCE / "freeze.json")
    require(execution.get("native_solve_executed") is True
            and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True,
            "K12 source run is not a completed terminal native response")
    require(execution.get("outputs_sha256", {}).get("model.dat") == sha(SOURCE / "model.dat"),
            "K12 DAT hash does not match its execution record")
    for name in ("model.json", "model.inp"):
        require(freeze.get("files_sha256", {}).get(name) == sha(SOURCE / name)
                and execution.get("outputs_sha256", {}).get(name) == sha(SOURCE / name),
                f"K12 {name} differs from its adjacent freeze/execution record")
    require(model.get("case_id") == "k12-rear" and abs(max(states) - 1.0) < 1e-12,
            "K12 screen does not cover the full k12-rear response")
    zero_u_components = 0
    nonzero_u_components = 0
    rf_components = 0
    for time, state in states.items():
        require(time in old_states, f"baseline parser omitted K12 time {time}")
        old_state = old_states[time]
        for node, vector in state["u"].items():
            require(vector == old_state["u"][node], f"U values changed at {time} node {node}")
            for dof, value in enumerate(vector):
                old_radius = old_state["u_radius"][node][dof]
                new_radius = state["u_radius"][node][dof]
                if value == 0.0:
                    require(old_radius == 5e-7 and new_radius == 0.0,
                            f"zero U radius delta differs at {time} node {node} DOF {dof+1}")
                    zero_u_components += 1
                else:
                    require(old_radius == new_radius,
                            f"nonzero U radius changed at {time} node {node} DOF {dof+1}")
                    nonzero_u_components += 1
        for node, vector in state["rf"].items():
            require(vector == old_state["rf"][node], f"RF values changed at {time} node {node}")
            require(state["rf_radius"][node] == old_state["rf_radius"][node],
                    f"RF radii changed at {time} node {node}")
            rf_components += len(vector)
    old_reports = {float(row["time"]): row for row in old_screen["states"]}

    reports = []
    for time, state in states.items():
        rows = []
        for binding in contract["bindings"]:
            source = contract["source_by_group"][binding["group"]]
            if source["role"] != "floor_normal":
                continue
            force, force_radius, check = audit._audit_springa(
                binding, source, state, contract["emitted_nodes"]
            )
            q = float(check["q_relative_projection_mm"])
            q_radius = float(check["q_relative_projection_radius_mm"])
            q_node, ground_node = map(int, binding["springa_nodes"])
            initial_vector = (np.asarray(model["nodes"][str(q_node)], dtype=float)
                              - np.asarray(model["nodes"][str(ground_node)], dtype=float))
            q_vector = (np.asarray(state["u"][q_node], dtype=float)
                        - np.asarray(state["u"][ground_node], dtype=float))
            q_vector_radius = (np.asarray(state["u_radius"][q_node], dtype=float)
                               + np.asarray(state["u_radius"][ground_node], dtype=float))
            current_vector = initial_vector + q_vector
            current_length = float(np.linalg.norm(current_vector))
            current_axis = current_vector / current_length
            geometric_radius = float(np.abs(current_axis) @ q_vector_radius) + float(
                check["geometric_length_subtraction_arithmetic_guard_mm"]
            )
            geometric_elongation = float(check["geometric_spring_elongation_mm"])
            geometric_interval = [geometric_elongation - geometric_radius,
                                  geometric_elongation + geometric_radius]
            table_force_interval = [float(value) for value in check["native_table_force_interval_N"]]
            endpoint_internal_force = float(check["native_endpoint_internal_force_N"])
            endpoint_internal_radius = float(check["native_endpoint_internal_radius_N"])
            endpoint_force_guard = float(check["native_endpoint_force_arithmetic_guard_N"])
            positive = bool(
                q - q_radius > 0.0
                and geometric_interval[0] > 0.0
                and table_force_interval[0] > 0.0
                and endpoint_internal_force - endpoint_internal_radius - endpoint_force_guard > 0.0
            )
            separating = bool(
                q + q_radius < 0.0
                and geometric_interval[1] < 0.0
                and table_force_interval == [0.0, 0.0]
                and endpoint_internal_force == 0.0
                and bool(check["native_endpoint_action_reaction_passed"])
            )
            rows.append({
                "source_group": binding["group"],
                "cell_name": binding["name"],
                "physical_owner": binding["physical_owner"],
                "strictly_positive_after_rounding": positive,
                "strictly_separating_after_rounding": separating,
                "unresolved_by_projected_q_or_force_interval": not positive and not separating,
                "normal_force_diagnostic_N": float(force),
                "normal_force_radius_N": float(force_radius),
                "q_diagnostic_mm": q,
                "q_radius_mm": q_radius,
                "projected_q_interval_mm": [q - q_radius, q + q_radius],
                "geometric_spring_elongation_mm": check["geometric_spring_elongation_mm"],
                "geometric_spring_elongation_radius_mm": geometric_radius,
                "geometric_spring_elongation_interval_mm": geometric_interval,
                "geometric_length_subtraction_arithmetic_guard_mm": check[
                    "geometric_length_subtraction_arithmetic_guard_mm"
                ],
                "native_endpoint_internal_force_N": check["native_endpoint_internal_force_N"],
                "native_endpoint_internal_radius_N": check["native_endpoint_internal_radius_N"],
                "table_force_interval_N": table_force_interval,
                "table_force_intersects_native_endpoint_RF": bool(
                    check["table_force_interval_intersects_native_rf"]
                ),
                "endpoint_action_reaction_passed": bool(
                    check["native_endpoint_action_reaction_passed"]
                ),
            })
        require(len(rows) == 100, f"expected 100 floor normal laws at time {time}")
        positive_set = sorted(row["cell_name"] for row in rows if row["strictly_positive_after_rounding"])
        separating_set = sorted(row["cell_name"] for row in rows if row["strictly_separating_after_rounding"])
        unresolved_set = sorted(
            row["cell_name"] for row in rows if row["unresolved_by_projected_q_or_force_interval"]
        )
        old_state = old_reports[time]
        old_positive = sorted(row["cell_name"] for row in old_state["rows"]
                              if row["strictly_positive_after_rounding"])
        old_separating = sorted(row["cell_name"] for row in old_state["rows"]
                                if row["strictly_separating_after_rounding"])
        old_unresolved = sorted(set(row["cell_name"] for row in old_state["rows"])
                                - set(old_positive) - set(old_separating))
        changed = [row for row in rows if row["cell_name"] in set(old_unresolved)]
        reports.append({
            "time": time,
            "positive_count": len(positive_set),
            "strictly_separating_count": len(separating_set),
            "unresolved_count": len(unresolved_set),
            "positive_cells": positive_set,
            "strictly_separating_cells": separating_set,
            "unresolved_cells": unresolved_set,
            "old_screen_counts": {
                "positive": len(old_positive),
                "strictly_separating": len(old_separating),
                "unresolved": len(old_unresolved),
            },
            "old_unresolved_rows_after_refined_parse": [
                row for row in rows if row["cell_name"] in set(old_unresolved)
            ],
            "full_rows": rows,
        })

    positive_sets = [set(row["positive_cells"]) for row in reports]
    separating_sets = [set(row["strictly_separating_cells"]) for row in reports]
    unresolved_counts = [row["unresolved_count"] for row in reports]
    result = {
        "schema": "current_k12_rear_zero_u_token_normal_law_screen/v1",
        "status": "COMPLETED_NORMAL_LAW_DIAGNOSTIC_ONLY",
        "case_id": model["case_id"],
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "source_response_origin": "Existing frozen all-bearing K12-rear native response; this parser replay does not create a new solver response.",
        "existing_all_bearing_support_branch_remains_rejected": True,
        "corner_demands_usable": False,
        "selected_floor_mask_or_support_state": False,
        "native_run_performed_by_this_screen": False,
        "full_factor_response_confirmed": True,
        "all_printed_floor_normal_laws_checked": True,
        "full_floor_law_row_count_per_state": 100,
        "all_printed_times": list(states),
        "strict_positive_cell_set_stable_all_states": all(value == positive_sets[0] for value in positive_sets),
        "strict_separating_cell_set_stable_all_states": all(value == separating_sets[0] for value in separating_sets),
        "unresolved_count_each_state": unresolved_counts,
        "all_cells_classified_strictly_every_state": all(count == 0 for count in unresolved_counts),
        "before_after_count_changes": [
            {
                "time": row["time"],
                "old_screen_counts": row["old_screen_counts"],
                "new_counts": {
                    "positive": row["positive_count"],
                    "strictly_separating": row["strictly_separating_count"],
                    "unresolved": row["unresolved_count"],
                },
            }
            for row in reports
        ],
        "source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in expected_pins},
        "old_screen_sha256": old_screen_sha256,
        "new_zero_u_token_stable_auditor_sha256": sha(AUDITOR),
        "reason_for_refinement": "Only canonical all-zero U-token representation radii are set to zero; nonzero U values/radii, all RF values/radii, geometry guards, law checks, and response data remain unchanged.",
        "parser_delta_summary": {
            "zero_u_components_radius_5e_minus_7_to_zero": zero_u_components,
            "nonzero_u_components_unchanged": nonzero_u_components,
            "all_rf_components_values_and_radii_unchanged": rf_components,
            "all_parsed_u_values_unchanged": True,
        },
        "limits": [
            "This classifies the 100 normal-law intervals from an existing all-bearing diagnostic response only.",
            "The all-bearing support branch remains rejected. No selected floor mask, accepted support state, physical corner demand, or joint acceptance is produced.",
            "No solver convergence, nonlinear solve error, stability, or physical contact uncertainty is bounded by DAT representation parsing.",
        ],
        "states": reports,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    output = main()
    print(json.dumps({
        key: value for key, value in output.items()
        if key not in {"states", "source_sha256", "before_after_count_changes"}
    }, indent=2, sort_keys=True, allow_nan=False))
