#!/usr/bin/env python3
"""Verify the K12 screen contract projection preserves rows and changes only intervals."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
OLD = SERIES / "current-springa-k12-rear-floor-screen-attempt01/screen.json"
REFINED = SERIES / "current-springa-k12-rear-zero-u-token-screen-attempt01/screen.json"
PROJECTED = SERIES / "current-springa-k12-rear-zero-u-token-screen-attempt02/floor-diagnostic-screen.json"
PRODUCER = SERIES / "current-springa-k12-rear-zero-u-token-screen-attempt02/project_k12_rear_screen.py"
OUTPUT = Path(__file__).with_name("projection_verification.json")

PINS = {
    OLD: "445e809585be0efed9acbac9bd853a31de6a929c845b20b114c0ec50f843974b",
    REFINED: "2c4990ac95507208e42ec2fce4261b2d7582694861e0c31b653240a45fcf9a9e",
    PROJECTED: "e7afbc79297178f1d0f98d25247d3ef51e3bd690213daad6bfd290cb04d380e6",
    PRODUCER: "63ae48fda9bc65776f7271cda142bca3dce5b5479a88c9f9640a61712be0667a",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> dict[str, Any]:
    for path, expected in PINS.items():
        require(sha(path) == expected, f"K12 projection verification source changed: {path}")
    old, refined, projected = load(OLD), load(REFINED), load(PROJECTED)
    require(projected["schema"] == "current_case_bound_floor_diagnostic_screen/v1"
            and projected["status"] == "REJECTED_ALL_BEARING_SUPPORT_BRANCH"
            and projected["case_id"] == "k12-rear"
            and projected["corner_demands_usable"] is False,
            "Projected contract does not truthfully preserve rejected K12 status")
    require(len(old["states"]) == len(refined["states"]) == len(projected["states"]) == 7,
            "K12 screen does not contain all seven printed states")

    unchanged_centers = {
        "source_group": 0, "cell_name": 0, "physical_owner": 0,
        "normal_force_diagnostic_N": 0, "q_diagnostic_mm": 0,
    }
    q_radius_changed_rows = 0
    normal_force_radius_changed_rows = 0
    projected_rows = 0
    for old_state, refined_state, projected_state in zip(
        old["states"], refined["states"], projected["states"], strict=True
    ):
        require(old_state["time"] == refined_state["time"] == projected_state["time"],
                "K12 state time changed during projection")
        old_rows = {row["cell_name"]: row for row in old_state["rows"]}
        refined_rows = {row["cell_name"]: row for row in refined_state["full_rows"]}
        projected_by_cell = {row["cell_name"]: row for row in projected_state["rows"]}
        require(len(old_rows) == len(refined_rows) == len(projected_by_cell) == 100
                and old_rows.keys() == refined_rows.keys() == projected_by_cell.keys(),
                f"K12 time {old_state['time']} does not project the same 100 source cells")
        for cell in old_rows:
            old_row, refined_row, projected_row = old_rows[cell], refined_rows[cell], projected_by_cell[cell]
            for field in unchanged_centers:
                require(old_row[field] == refined_row[field] == projected_row[field],
                        f"K12 center/identity field changed at time {old_state['time']}, {cell}: {field}")
            require(projected_row["q_radius_mm"] == refined_row["q_radius_mm"]
                    and projected_row["normal_force_radius_N"] == refined_row["normal_force_radius_N"],
                    f"Projection changed refined interval data at time {old_state['time']}, {cell}")
            if old_row["q_radius_mm"] != refined_row["q_radius_mm"]:
                q_radius_changed_rows += 1
            if old_row["normal_force_radius_N"] != refined_row["normal_force_radius_N"]:
                normal_force_radius_changed_rows += 1
            projected_rows += 1
        require(old_state["bearing_count"] == 16
                and old_state["separating_count"] == (83 if old_state["time"] == 0.1 else 84),
                "Pinned original first-state ambiguity/history changed")
        require(refined_state["positive_count"] == projected_state["bearing_count"] == 16
                and refined_state["strictly_separating_count"] == projected_state["separating_count"] == 84
                and refined_state["unresolved_count"] == 0,
                "Refined K12 state is not exactly a stable 16/84 strict partition")

    old_unresolved = [
        row["source_group"] for row in old["states"][0]["rows"]
        if not row["strictly_positive_after_rounding"] and not row["strictly_separating_after_rounding"]
    ]
    require(old_unresolved == ["SPR1110"], "Original screen's single first-state ambiguity is not SPR1110")
    delta = refined["parser_delta_summary"]
    require(delta["all_parsed_u_values_unchanged"] is True
            and delta["zero_u_components_radius_5e_minus_7_to_zero"] == 91476
            and delta["nonzero_u_components_unchanged"] == 358071
            and delta["all_rf_components_values_and_radii_unchanged"] == 449547,
            "K12 refined source does not prove the narrow zero-U-only parser delta")
    require(projected_rows == 700 and q_radius_changed_rows == 700
            and normal_force_radius_changed_rows == 0,
            "K12 projection changed rows outside the zero-U-driven q intervals")

    result = {
        "schema": "current_k12_rear_screen_contract_projection_verification/v1",
        "status": "PASS_100_ROWS_X_7_STATES_VALUES_UNCHANGED_ZERO_U_INTERVALS_ONLY",
        "source_sha256": {str(path.relative_to(ROOT)): value for path, value in PINS.items()},
        "projected_row_count": projected_rows,
        "printed_state_count": len(projected["states"]),
        "center_and_owner_changes": unchanged_centers,
        "changed_projected_q_radius_rows": q_radius_changed_rows,
        "changed_normal_force_radius_rows": normal_force_radius_changed_rows,
        "original_first_state": {
            "bearing_count": 16,
            "strict_separating_count": 83,
            "unresolved_count": 1,
            "unresolved_source_group": old_unresolved[0],
        },
        "refined_counts_each_state": [
            {"time": state["time"], "positive": state["positive_count"],
             "separating": state["strictly_separating_count"], "unresolved": state["unresolved_count"]}
            for state in refined["states"]
        ],
        "parser_delta_summary": delta,
        "corner_demands_usable": False,
        "native_run_performed_by_verifier": False,
        "producer_sha256": sha(Path(__file__)),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return result


if __name__ == "__main__":
    main()
