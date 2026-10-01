"""Project the revalidated A12-forward diagnostic into one proposed mask.

This is an input proposal only. It exports no contact forces and launches no
native analysis.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
ORIGINAL = BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt01"
REVALIDATION = HERE / "source-revalidation"
CONTROL = BASE / "current-springa-frame-a12-forward-all-bearing-attempt01"
SCREEN_PATH = HERE / "screen.json"
REVALIDATION_AUDIT_PATH = HERE / "source-revalidation-audit.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def main() -> None:
    original_diag_path = ORIGINAL / "diagnosis.json"
    original_pins_path = ORIGINAL / "source-pins.json"
    replay_diag_path = REVALIDATION / "diagnosis.json"
    replay_pins_path = REVALIDATION / "source-pins.json"
    projector_path = Path(__file__).resolve()

    original_diag = read(original_diag_path)
    original_pins = read(original_pins_path)
    replay_diag = read(replay_diag_path)
    replay_pins = read(replay_pins_path)

    assert original_diag["schema"] == "current_springa_selected_floor_compatibility_diagnosis/v1"
    assert original_diag["status"] == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH_DIAGNOSTIC_ONLY"
    assert original_diag["case_id"] == "a12-forward"
    assert original_diag["native_run_id"] == "springa-selected-a12-forward-attempt02"
    assert original_diag["terminal_native_output_consumed"] is True
    assert original_diag["full_step_native_convergence"] is True
    assert original_diag["corner_demands_usable"] is False
    assert original_diag["mechanical_acceptance"] is False
    assert original_diag["physical_force_adoption"] is False
    assert original_diag["response_force_exported"] is False
    assert original_diag["normal_force_or_rf_values_written"] is False
    assert original_diag["new_floor_input_mask_created"] is False
    assert original_diag["native_solve_launched_by_diagnosis"] is False
    assert original_diag["input_selected_cell_count"] == 31
    assert original_diag["input_inactive_cell_count"] == 69

    assert replay_diag == original_diag, "Replayed diagnosis differs from the recorded source-bound diagnosis"
    assert replay_pins["case_id"] == original_pins["case_id"] == "a12-forward"
    assert replay_pins["source_sha256"] == original_pins["source_sha256"]
    assert replay_pins["diagnosis_sha256"] == original_pins["diagnosis_sha256"] == sha(original_diag_path)

    source_hashes = original_pins["source_sha256"]
    assert len(source_hashes) == 40
    for source_path, expected in source_hashes.items():
        actual = sha(ROOT / source_path)
        assert actual == expected, (source_path, expected, actual)

    direct_attempt02 = "current-springa-selected-floor-a12-forward-attempt02/"
    assert any(direct_attempt02 in path and path.endswith("/model.dat") for path in source_hashes)
    assert any(direct_attempt02 in path and path.endswith("/model.json") for path in source_hashes)
    control_model_path = CONTROL / "model.json"
    assert source_hashes.get(rel(control_model_path)) == sha(control_model_path)
    control_model = read(control_model_path)
    assert control_model["case_id"] == "a12-forward"
    assert control_model["candidate"] == original_diag["candidate"]
    assert control_model["geometry_revision_id"] == original_diag["geometry_revision_id"]

    normals = {
        str(binding["name"]): binding
        for binding in control_model["unilateral_springa_bindings"]
        if binding.get("physical_owner", {}).get("role") == "floor_normal"
    }
    assert len(normals) == 100
    times = [float(x) for x in original_diag["all_printed_load_factors"]]
    assert len(times) == 7
    assert len(original_diag["history"]) == 7
    states = []
    positive_by_state: list[set[str]] = []
    for state in original_diag["history"]:
        load_factor = float(state["load_factor"])
        assert load_factor in times
        counts = state["zero_u_711_counts"]
        assert counts == {"positive": 37, "separated": 63, "ambiguous_or_noncomplementary": 0}
        rows = []
        seen: set[str] = set()
        positive: set[str] = set()
        separated: set[str] = set()
        for source_row in state["rows"]:
            cell = str(source_row["cell_name"])
            assert cell not in seen
            seen.add(cell)
            carrier = normals[cell]
            assert carrier["group"] == source_row["source_group"]
            assert carrier["source_row_id"] == source_row["source_row_id"]
            classification = source_row["zero_u_711_classification"]
            is_positive = classification == "STRICTLY_POSITIVE"
            is_separated = classification == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"
            assert is_positive != is_separated
            if is_positive:
                positive.add(cell)
            else:
                separated.add(cell)
            rows.append({
                "cell_name": cell,
                "source_group": str(source_row["source_group"]),
                "source_row_id": str(source_row["source_row_id"]),
                "physical_owner": carrier["physical_owner"],
                "zero_u_711_classification": classification,
                "strictly_positive_after_rounding": is_positive,
                "strictly_separating_after_rounding": is_separated,
                "q_interval_mm": source_row["zero_u_711_q_interval_mm"],
                "geometric_elongation_interval_mm": source_row["zero_u_711_geometric_elongation_interval_mm"],
            })
        assert len(seen) == 100 and len(positive) == 37 and len(separated) == 63
        positive_by_state.append(positive)
        states.append({
            "load_factor": load_factor,
            "bearing_count": len(positive),
            "separating_count": len(separated),
            "ambiguous_or_noncomplementary_count": 0,
            "rows": rows,
        })

    stable_positive = positive_by_state[0]
    assert all(group == stable_positive for group in positive_by_state)
    proposed = set(original_diag["zero_u_711_observed_positive_cells_diagnostic_only"])
    assert proposed == stable_positive and len(proposed) == 37
    assert len(set(original_diag["selected_cells_not_strictly_positive"])) == 3
    assert len(set(original_diag["inactive_cells_strictly_positive"])) == 9
    spr1026 = original_diag["spr1026_diagnostic"]
    assert spr1026["cell_name"] == "floor_base_floor_left_1"
    assert spr1026["source_group"] == "SPR1026"
    assert spr1026["selected_in_attempt02_input"] is True
    assert len(spr1026["zero_u_711_classification_by_state"]) == 7
    assert set(spr1026["zero_u_711_classification_by_state"]) == {"STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"}

    replay_audit = {
        "schema": "current_springa_a12_forward_diagnostic_source_revalidation/v1",
        "status": "PASS_A12_FORWARD_DIAGNOSTIC_SOURCE_REPLAY",
        "case_id": "a12-forward",
        "original_diagnosis_path": rel(original_diag_path),
        "original_diagnosis_sha256": sha(original_diag_path),
        "replayed_diagnosis_path": rel(replay_diag_path),
        "replayed_diagnosis_sha256": sha(replay_diag_path),
        "original_source_pins_sha256": sha(original_pins_path),
        "replayed_source_pins_sha256": sha(replay_pins_path),
        "source_hash_count": len(source_hashes),
        "source_hash_maps_identical": True,
        "all_pinned_sources_rehashed": True,
        "direct_rejected_31_source_lineage_preserved": True,
        "load_state_count": len(states),
        "stable_zero_u_711_classification_counts": {"positive": 37, "separated": 63, "ambiguous": 0},
        "selected_nonpositive_cell_count": 3,
        "inactive_positive_cell_count": 9,
        "spr1026_selected_but_separated_all_states": True,
        "force_or_rf_values_adopted": False,
        "support_proposal_created_by_source_replay": False,
        "source_sha256": {
            **source_hashes,
            rel(original_diag_path): sha(original_diag_path),
            rel(original_pins_path): sha(original_pins_path),
            rel(replay_diag_path): sha(replay_diag_path),
            rel(replay_pins_path): sha(replay_pins_path),
            rel(Path(__file__).resolve()): sha(projector_path),
        },
        "limits": [
            "Revalidates the source-bound rejected 31-cell attempt02 diagnosis; it is not a response for the proposed 37-cell input.",
            "Classification intervals contain no native contact force or support reaction values.",
            "This source replay authorizes no mask iteration, freeze, native solve, or mechanical acceptance.",
        ],
    }
    write(REVALIDATION_AUDIT_PATH, replay_audit)

    screen_source_hashes = dict(replay_audit["source_sha256"])
    screen_source_hashes[rel(REVALIDATION_AUDIT_PATH)] = sha(REVALIDATION_AUDIT_PATH)
    screen = {
        "schema": "current_case_bound_floor_diagnostic_screen/v1",
        "status": "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH",
        "case_id": "a12-forward",
        "candidate": control_model["candidate"],
        "geometry_revision_id": control_model["geometry_revision_id"],
        "source_stage": "direct rejected selected-31 attempt02 output, reclassified by source-pinned zero-u 711 token intervals",
        "direct_selected_31_run_lineage": {
            "native_run_id": original_diag["native_run_id"],
            "run_directory": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-forward-attempt02",
            "input_selected_cell_count": 31,
            "status": original_diag["status"],
            "source_revalidation_audit_path": rel(REVALIDATION_AUDIT_PATH),
        },
        "source_controls_physics_authority": rel(CONTROL / "model.json"),
        "source_normal_interval_diagnostic": rel(replay_diag_path),
        "normal_interval_method": "source-pinned zero-u 711 printed-token intervals; strict complementary classification",
        "proposed_mask_basis": "37 cells strictly positive at all seven printed states in the rejected 31-cell run diagnosis; a new case-bound input proposal only",
        "all_printed_times": times,
        "all_printed_floor_laws_checked": True,
        "same_positive_cell_set_at_all_printed_times": True,
        "full_step_native_convergence": True,
        "corner_demands_usable": False,
        "mechanical_acceptance": False,
        "physical_force_adoption": False,
        "screen_forces_or_active_states_adopted": False,
        "native_solve_launched_by_projection": False,
        "floor_mask_or_iteration_proposed_by_projection": True,
        "proposed_mask_is_selected_response": False,
        "positive_set_stable_at_all_printed_states": True,
        "diagnostic_positive_cell_count_at_final_time": 37,
        "diagnostic_separating_cell_count_at_final_time": 63,
        "diagnostic_positive_cells_at_final_time": sorted(proposed),
        "diagnostic_separating_cells_at_final_time": sorted(set(normals) - proposed),
        "selected_input_cells_released_diagnostic_count": 3,
        "inactive_input_cells_closed_diagnostic_count": 9,
        "selected_input_cells_not_positive": sorted(original_diag["selected_cells_not_strictly_positive"]),
        "inactive_input_cells_positive": sorted(original_diag["inactive_cells_strictly_positive"]),
        "spr1026_selected_but_separated_all_states": True,
        "states": states,
        "source_sha256": screen_source_hashes,
        "limits": [
            "The 37-cell set is proposed as an A12-forward input support branch only; it has no selected-branch response or accepted force values.",
            "The interval classifications come from the source-bound rejected 31-cell terminal run, not from a run with this 37-cell support mask.",
            "No forces or demands transfer from another case or from the all-bearing source control response.",
            "No automatic mask iteration, native launch, freeze, floor qualification, support capacity, or mechanical acceptance is authorized by this screen.",
        ],
    }
    write(SCREEN_PATH, screen)
    write(HERE / "screen-source-pins.json", {
        "schema": "current_springa_case_bound_floor_screen_source_pins/v1",
        "case_id": "a12-forward",
        "screen_path": rel(SCREEN_PATH),
        "screen_sha256": sha(SCREEN_PATH),
        "source_sha256": screen_source_hashes,
        "status": screen["status"],
        "diagnostic_positive_cell_count": 37,
        "diagnostic_separating_cell_count": 63,
        "proposal_only": True,
        "native_solve_executed": False,
    })
    print(json.dumps({
        "status": replay_audit["status"],
        "source_hash_count": len(source_hashes),
        "screen_status": screen["status"],
        "case_id": screen["case_id"],
        "positive_cells": 37,
        "separated_cells": 63,
        "states": len(states),
        "screen_sha256": sha(SCREEN_PATH),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
