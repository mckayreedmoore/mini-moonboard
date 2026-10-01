#!/usr/bin/env python3
"""Project a12-left zero-U interval classifications to adapter02's input-only screen API."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
DIAGNOSTIC_DIR = BASE / "current-springa-a12-left-normal-interval-diagnostic-attempt01"
DIAGNOSTIC = DIAGNOSTIC_DIR / "a12-left-normal-intervals.json"
DIAGNOSTIC_PINS = DIAGNOSTIC_DIR / "source-pins.json"
DIAGNOSTIC_PRODUCER = DIAGNOSTIC_DIR / "produce.py"
ADAPTER = BASE / "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py"
CONTROL = BASE / "current-springa-frame-a12-left-all-bearing-attempt01"
DIRECT = BASE / "current-springa-selected-floor-a12-left-attempt02"
FRESH_MODEL = BASE / "current-springa-six-case-frame-input-adapter-attempt01/a12-left/model.json"
REGISTER = BASE / "current-six-case-source-load-register-attempt01/register.json"
RESPONSE_AUDITOR = BASE / "current-springa-frame-response-audit-attempt01/response_audit.py"

EXPECTED = {
    "diagnostic_producer_sha256": "0bad1eb9c1a29bfb437d84496578d37842ad3a61125c56757e383c50567490ce",
    "diagnostic_sha256": "029244c02a57ddbe2dff9abd1c2afd3533e39f23a387e37e472b742c9ba53f86",
    "adapter_sha256": "1e9edd6d8d1a341c3cd70854710dd80431438f7287e425b1c3e62d94d0f963bc",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def main() -> None:
    screen_path = HERE / "a12-left-screen.json"
    pins_path = HERE / "screen-projection-source-pins.json"
    require(not screen_path.exists() and not pins_path.exists(), "Refusing to overwrite existing projection")
    require(sha(DIAGNOSTIC_PRODUCER) == EXPECTED["diagnostic_producer_sha256"]
            and sha(DIAGNOSTIC) == EXPECTED["diagnostic_sha256"]
            and sha(ADAPTER) == EXPECTED["adapter_sha256"],
            "A12-left diagnostic or immutable adapter02 API pin changed")

    diagnostic = load(DIAGNOSTIC)
    source_pins = load(DIAGNOSTIC_PINS)
    control = load(CONTROL / "model.json")
    direct = load(DIRECT / "model.json")
    execution = load(DIRECT / "execution.json")
    register = load(REGISTER)
    fresh = load(FRESH_MODEL)
    require(diagnostic.get("schema") == "current_springa_selected_floor_normal_interval_diagnostic/v1"
            and diagnostic.get("status") == "COMPLETED_NORMAL_LAW_DIAGNOSTIC_ONLY_PROPOSED_BRANCH_REJECTED"
            and diagnostic.get("case_id") == "a12-left"
            and diagnostic.get("native_case_terminal_status") == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
            and diagnostic.get("printed_state_count") == 7
            and diagnostic.get("normal_count_per_state") == 100
            and diagnostic.get("full_factor_1_reached") is True
            and diagnostic.get("strict_positive_cell_set_stable_all_states") is True,
            "Interval diagnostic is not the exact stable full-load a12-left record")
    require(diagnostic.get("input_selected_cells_not_strictly_positive") == []
            and diagnostic.get("input_inactive_cells_strictly_positive") == ["floor_lumber_leg_left_1"]
            and diagnostic.get("compatibility_exception_count") == 1
            and diagnostic["compatibility_exceptions"][0]["source_group"] == "SPR1302",
            "The exact selected-10 branch exception changed")
    require(control.get("case_id") == direct.get("case_id") == fresh.get("case_id") == "a12-left"
            and register.get("schema") == "current_springa_six_case_source_load_register/v1"
            and execution.get("run_id") == "springa-selected-a12-left-attempt02"
            and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True,
            "A12-left case, fresh-register, or direct-run identity changed")
    require(diagnostic.get("lineage", {}).get("rejected_response_forces_adopted") is False
            and diagnostic.get("lineage", {}).get("other_case_response_states_reused") is False,
            "Diagnostic force/other-case lineage scope changed")

    bindings = {
        str(binding["name"]): binding
        for binding in control.get("unilateral_springa_bindings", [])
        if binding.get("physical_owner", {}).get("role") == "floor_normal"
    }
    require(len(bindings) == 100, "Original a12-left control does not have exactly 100 floor-normal carriers")
    positive = set(map(str, diagnostic["strict_positive_cells_at_final_state"]))
    separated = set(bindings) - positive
    require(len(positive) == 11 and len(separated) == 89,
            "A12-left stable strict-positive partition changed from 11/89")

    projected_states = []
    positive_sets = []
    times = []
    for state in diagnostic["states"]:
        rows_by_cell = {str(row["normal_cell"]): row for row in state["rows"]}
        require(len(rows_by_cell) == 100 and set(rows_by_cell) == set(bindings),
                "A12-left state does not bind all normal cells to the original controls")
        state_positive = {
            cell for cell, row in rows_by_cell.items()
            if row.get("classification") == "STRICT_POSITIVE_BEARING"
            and row.get("strictly_positive_bearing") is True
            and row.get("strictly_separated") is False
        }
        state_separated = {
            cell for cell, row in rows_by_cell.items()
            if row.get("classification") == "STRICTLY_SEPARATED"
            and row.get("strictly_positive_bearing") is False
            and row.get("strictly_separated") is True
        }
        require(state_positive == positive and state_separated == separated
                and all(row.get("classification") != "UNRESOLVED_INTERVALS" for row in rows_by_cell.values()),
                "A12-left positive/separated sets are not strict and stable at every increment")
        output_rows = []
        for cell in sorted(bindings):
            diagnostic_row = rows_by_cell[cell]
            carrier = bindings[cell]
            require(diagnostic_row.get("source_group") == carrier.get("group")
                    and diagnostic_row.get("physical_owner") == carrier.get("physical_owner", {}).get("first"),
                    f"A12-left normal source/owner mismatch at {cell}")
            is_positive = cell in positive
            output_rows.append({
                "cell_name": cell,
                "source_group": str(carrier["group"]),
                "source_row_id": str(carrier["source_row_id"]),
                "physical_owner": carrier["physical_owner"],
                "classification_from_zero_u_711_interval_audit": diagnostic_row["classification"],
                "strictly_positive_after_rounding": is_positive,
                "strictly_separating_after_rounding": not is_positive,
            })
        factor = float(state["load_factor"])
        times.append(factor)
        positive_sets.append(state_positive)
        projected_states.append({
            "load_factor": factor,
            "bearing_count": len(state_positive),
            "separating_count": len(state_separated),
            "ambiguous_or_unresolved_count": 0,
            "rows": output_rows,
        })
    require(times[-1] == 1.0 and all(value == positive_sets[0] for value in positive_sets),
            "A12-left strict set is not stable at all seven states through full load")

    source_sha = {
        rel(DIAGNOSTIC): sha(DIAGNOSTIC),
        rel(DIAGNOSTIC_PINS): sha(DIAGNOSTIC_PINS),
        rel(DIAGNOSTIC_PRODUCER): sha(DIAGNOSTIC_PRODUCER),
        rel(ADAPTER): sha(ADAPTER),
        rel(REGISTER): sha(REGISTER),
        rel(FRESH_MODEL): sha(FRESH_MODEL),
        rel(RESPONSE_AUDITOR): sha(RESPONSE_AUDITOR),
    }
    source_sha.update({rel(CONTROL / name): sha(CONTROL / name) for name in (
        "model.json", "model.inp", "model.dat", "execution.json", "freeze.json",
        "authorization.json", "parent-serialized-input-audit.json",
    )})
    source_sha.update({rel(DIRECT / name): sha(DIRECT / name) for name in (
        "model.json", "model.inp", "model.dat", "execution.json", "freeze.json",
        "authorization.json", "case-context.json", "parent-serialized-input-audit.json",
        "parent-terminal-assessment.json",
    )})
    source_sha.update(source_pins.get("source_sha256", {}))

    screen = {
        "schema": "current_case_bound_floor_diagnostic_screen/v1",
        "status": "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH",
        "case_id": "a12-left",
        "candidate": control["candidate"],
        "geometry_revision_id": control["geometry_revision_id"],
        "full_step_native_convergence": True,
        "native_solve_launched_by_projection": False,
        "corner_demands_usable": False,
        "mechanical_acceptance": False,
        "physical_force_adoption": False,
        "screen_forces_or_active_states_adopted": False,
        "all_printed_floor_laws_checked": True,
        "same_positive_cell_set_at_all_printed_times": True,
        "all_printed_times": times,
        "states": projected_states,
        "diagnostic_positive_cells_at_final_time": sorted(positive),
        "diagnostic_separating_cells_at_final_time": sorted(separated),
        "source_stage": "a12_left_direct_selected_10_terminal_run_zero_u_711_interval_projection",
        "source_normal_interval_diagnostic": {
            "path": rel(DIAGNOSTIC),
            "sha256": sha(DIAGNOSTIC),
            "status": diagnostic["status"],
            "schema": diagnostic["schema"],
            "source_selected_cell_count": 10,
            "derived_strict_positive_cell_count": len(positive),
            "inactive_positive_cells": diagnostic["input_inactive_cells_strictly_positive"],
            "selected_nonpositive_cells": diagnostic["input_selected_cells_not_strictly_positive"],
            "unresolved_row_count_per_state": [state["unresolved_count"] for state in diagnostic["states"]],
            "native_connector_forces_copied": False,
        },
        "source_controls_physics_authority": {
            "role": "original_a12_left_all_bearing_geometry_material_law_load_and_carrier_authority",
            "model_path": rel(CONTROL / "model.json"),
            "model_sha256": sha(CONTROL / "model.json"),
            "deck_path": rel(CONTROL / "model.inp"),
            "deck_sha256": sha(CONTROL / "model.inp"),
            "case_id": "a12-left",
            "source_register_path": rel(REGISTER),
            "source_register_sha256": sha(REGISTER),
            "diagnostic_forces_used": False,
        },
        "direct_rejected_selected_10_lineage": {
            "role": "SPR1302_normal_classification_lineage_only",
            "model_path": rel(DIRECT / "model.json"),
            "model_sha256": sha(DIRECT / "model.json"),
            "deck_path": rel(DIRECT / "model.inp"),
            "deck_sha256": sha(DIRECT / "model.inp"),
            "dat_path": rel(DIRECT / "model.dat"),
            "dat_sha256": sha(DIRECT / "model.dat"),
            "execution_path": rel(DIRECT / "execution.json"),
            "execution_sha256": sha(DIRECT / "execution.json"),
            "terminal_status": diagnostic["native_case_terminal_status"],
            "strict_exception": "Inactive floor normal is not strictly separated with zero endpoint RF: SPR1302",
            "native_connector_forces_adopted": False,
        },
        "normal_interval_method": {
            "wrapper_path": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-zero-u-token-response-audit-attempt01/response_audit.py",
            "wrapper_sha256": "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
            "stable_parser_path": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py",
            "stable_parser_sha256": "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
            "classification_only_projection": True,
            "force_values_copied": False,
        },
        "one_case_specific_input_proposal_basis": {
            "cells": sorted(positive),
            "cell_count": len(positive),
            "inactive_cell_count": len(separated),
            "selected_tangent_row_count": 2 * len(positive),
            "inactive_tangent_row_count": 2 * len(separated),
            "status": "one_input_proposal_only_from_same_case_strict_interval_set",
            "automatic_mask_iteration_authorized": False,
            "accepted_support_or_unique_branch_claimed": False,
        },
        "source_sha256": source_sha,
        "limits": [
            "This projection carries only strict normal classifications and source/owner identities; it omits connector and support force values.",
            "The direct selected-10 response remains rejected at SPR1302 and is not adopted as the proposed input's response.",
            "The 11/89 set is a single a12-left input proposal based on this exact full-load rejected-run normal classification; no other-case state is used.",
            "No selected-branch equilibrium response, physical floor reaction, corner demand, resistance, or joint acceptance is established.",
        ],
    }
    screen_path.write_text(json.dumps(screen, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    pins_path.write_text(json.dumps({
        "schema": "current_springa_a12_left_floor_screen_projection_pins/v1",
        "producer_path": rel(Path(__file__)),
        "producer_sha256": sha(Path(__file__)),
        "screen_path": rel(screen_path),
        "screen_sha256": sha(screen_path),
        "source_sha256": source_sha,
    }, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": screen["status"],
        "case_id": screen["case_id"],
        "selected_cells": screen["diagnostic_positive_cells_at_final_time"],
        "selected_count": len(positive),
        "inactive_count": len(separated),
        "screen_sha256": sha(screen_path),
        "producer_sha256": sha(Path(__file__)),
        "native_forces_copied": False,
    }, indent=2))


if __name__ == "__main__":
    main()
