#!/usr/bin/env python3
"""Project the pinned A1-rear normal-interval diagnosis to the input-screen contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
OUT = Path(__file__).resolve().parent
DIAGNOSTIC = BASE / "current-springa-selected-floor-normal-interval-diagnostic-attempt01/a1-rear-normal-intervals.json"
INTERVAL_PRODUCER = BASE / "current-springa-selected-floor-normal-interval-diagnostic-attempt01/produce.py"
CONTROL_DIR = BASE / "current-springa-frame-a1-rear-all-bearing-attempt01"
DIRECT_RUN = BASE / "current-springa-selected-floor-a1-rear-attempt01"
CONTROL_MODEL = CONTROL_DIR / "model.json"
FRESH_MODEL = BASE / "current-springa-six-case-frame-input-adapter-attempt01/a1-rear/model.json"
REGISTER = BASE / "current-six-case-source-load-register-attempt01/register.json"
RESPONSE_AUDITOR = BASE / "current-springa-frame-response-audit-attempt01/response_audit.py"
ZERO_U_DIR = BASE / "current-springa-zero-u-token-response-audit-attempt01"
EXPECTED: dict[str, str] = {
    str(CONTROL_DIR / "model.json"): "ddebc07e3f976ebe689511c6be9f9b41a749a7cad819ea90248318c4025a47bf",
    str(CONTROL_DIR / "model.inp"): "03bb5b663c04d3f5f5898c20ad1941457b05e350b1e44d9657d0042831e96216",
    str(CONTROL_DIR / "model.dat"): "d968ad0139241851367ae6720bea17b7e396dfba9746d1e916a7d65a27496ef4",
    str(CONTROL_DIR / "execution.json"): "00ab415290ea999649b72b419ecdf3c57d2d75dbdef4f059dd6c49f06435b81f",
    str(CONTROL_DIR / "freeze.json"): "c9bfbb3d719972fa5f66a710a4d439dccd89d03d333bd9aa89ecd958e37afd0a",
    str(CONTROL_DIR / "authorization.json"): "b5966815b76af1bd584e5f88ff83640713444d8c51f7ced69874fb808dc5e1dd",
    str(CONTROL_DIR / "parent-serialized-input-audit.json"): "632f1f3115fbc194c0f67d9efac47a697513b86f601b9cb9aa69a1a21ec85a6c",
    str(DIRECT_RUN / "model.json"): "3cf43f58ea10027fa58618bc9d69536b67664f8780e457d1cc9451bc9411588e",
    str(DIRECT_RUN / "model.inp"): "91e7c87b67ab53517fb774c119ae6b4f52ff15a5c0f0ca73c8b5a4cae6bf8610",
    str(DIRECT_RUN / "model.dat"): "22caf3925934fae1d9111374d25e67b7e2741ad9b2e603494b0ba08a4d59dbcb",
    str(DIRECT_RUN / "execution.json"): "a8f2df6249f7d04a0da85b2697ae6b6ff55b2984e940b36e313202d471cbe8ff",
    str(DIRECT_RUN / "freeze.json"): "2139179dc9672aaf50db330d84a269b2881faab1c29058469873d1cc491e2d6b",
    str(DIRECT_RUN / "authorization.json"): "ab96a07cb7178a4e23337591823920cdb03212ce23f37a9d44d850e8994273db",
    str(DIRECT_RUN / "case-context.json"): "d816f18a9c444c058944966eb999d862625851ee10512d0ef106bb4b6dac50f0",
    str(DIRECT_RUN / "parent-serialized-input-audit.json"): "15baaf613eac54e561f794b5f89876c082b0583115ffa812dca25439890fb0d7",
    str(DIRECT_RUN / "parent-terminal-assessment.json"): "c0d9aac117fc17466e90df85225827a46a58d96ad508b4a212978bb87f012d8e",
    str(DIAGNOSTIC): "31bd6b4267fb16a4d4eb20151c24e0d17ebd563c260b9fbaf62436bc5db0b2d0",
    str(INTERVAL_PRODUCER): "02f1292caf7b1bc1b5bbaca73bdbd4f7c3f7eb4c727a755eb69e458d00d49cd8",
    str(ZERO_U_DIR / "response_audit.py"): "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
    str(ZERO_U_DIR / "stable_response_audit.py"): "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    str(ZERO_U_DIR / "replay_zero_u_tokens.py"): "6b49312429c78e04d0a70a7a428382028ac9e75ab01a69b53271d9feca91bd32",
    str(ZERO_U_DIR / "zero_u_token_replay.json"): "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1",
    str(RESPONSE_AUDITOR): "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
    str(FRESH_MODEL): "3895f19ecc580cb9e68e917254f4262cdb30b4c06725236437b73969d9eef690",
    str(REGISTER): "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508",
    str(BASE / "current-floor-stick-constraint-audit-attempt01/audit.json"): "43b5aa99468b1577cd273baddafe47955b235fa00ddd5b9d5aff91d490695c95",
    str(BASE / "current-floor-stick-constraint-audit-attempt01/constraint-matrices.npz"): "4fcc630274e2f1c7166c811d2aa97a3f075d60b5724600b88be73afebe308f6e",
    str(BASE / "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json"): "d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    screen_path = OUT / "screen.json"
    pins_path = OUT / "projection-source-pins.json"
    if screen_path.exists() or pins_path.exists():
        raise RuntimeError("Refusing to overwrite an existing projection packet")

    for raw_path, expected in EXPECTED.items():
        path = ROOT / raw_path
        observed = sha(path)
        if observed != expected:
            raise RuntimeError(f"Source hash mismatch for {raw_path}: {observed}")

    diagnostic = read_json(ROOT / DIAGNOSTIC)
    control = read_json(ROOT / CONTROL_MODEL)
    direct = read_json(ROOT / (DIRECT_RUN / "model.json"))
    execution = read_json(ROOT / (DIRECT_RUN / "execution.json"))
    fresh = read_json(ROOT / FRESH_MODEL)
    if (
        diagnostic.get("schema") != "current_springa_selected_floor_normal_interval_diagnostic/v1"
        or diagnostic.get("status") != "COMPLETED_NORMAL_LAW_DIAGNOSTIC_ONLY_PROPOSED_BRANCH_REJECTED"
        or diagnostic.get("native_case_terminal_status") != "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
        or diagnostic.get("case_id") != "a1-rear"
        or diagnostic.get("candidate") != control.get("candidate")
        or diagnostic.get("geometry_revision_id") != control.get("geometry_revision_id")
        or diagnostic.get("selected_floor_branch_id") != "monotone_zero_gap_first_bearing_reference_zero"
        or diagnostic.get("printed_state_count") != 7
        or diagnostic.get("normal_count_per_state") != 100
        or diagnostic.get("strict_positive_cell_set_stable_all_states") is not True
        or diagnostic.get("input_selected_cells_not_strictly_positive") != []
        or diagnostic.get("input_inactive_cells_strictly_positive") != [
            "floor_base_floor_left_36", "floor_base_floor_right_12"
        ]
    ):
        raise RuntimeError("Pinned interval diagnostic identity, status, or branch evidence changed")
    if direct.get("case_id") != "a1-rear" or control.get("case_id") != "a1-rear" or fresh.get("case_id") != "a1-rear":
        raise RuntimeError("The all-bearing physics authority and direct diagnostic lineage must be A1-rear")
    if execution.get("run_id") != "springa-selected-a1-rear-attempt01" or execution.get("returncode") != 0 or execution.get("container_confirmed_terminal") is not True:
        raise RuntimeError("Direct 44-cell lineage is not the exact terminal run")

    direct_mask = set(map(str, direct.get("floor_selected_bearing_cells", [])))
    if len(direct_mask) != 44:
        raise RuntimeError("The direct selected-proposal lineage must have exactly 44 selected cells")
    normal_bindings = {
        str(binding["name"]): binding
        for binding in control.get("unilateral_springa_bindings", [])
        if binding.get("physical_owner", {}).get("role") == "floor_normal"
    }
    if len(normal_bindings) != 100:
        raise RuntimeError("Pinned original all-bearing control must contain all 100 floor normals")

    times = [float(state["load_factor"]) for state in diagnostic["states"]]
    if len(times) != 7 or times[-1] != 1.0:
        raise RuntimeError("Diagnostic does not contain all seven printed states through full factor")
    projected_states = []
    positive_sets = []
    for state in diagnostic["states"]:
        source_rows = state.get("rows", [])
        by_cell = {str(row["normal_cell"]): row for row in source_rows}
        if len(source_rows) != 100 or set(by_cell) != set(normal_bindings):
            raise RuntimeError("Normal interval diagnostic does not cover exactly the controls' 100 cells")
        projected_rows = []
        positive: set[str] = set()
        separated: set[str] = set()
        for cell in sorted(by_cell):
            row = by_cell[cell]
            binding = normal_bindings[cell]
            classification = row.get("classification")
            is_positive = classification == "STRICT_POSITIVE_BEARING"
            is_separated = classification == "STRICTLY_SEPARATED"
            if not (is_positive ^ is_separated):
                raise RuntimeError(f"Unresolved normal interval classification for {cell} at {state['load_factor']}")
            if row.get("source_group") != binding.get("group") or row.get("physical_owner") != binding.get("physical_owner", {}).get("first"):
                raise RuntimeError(f"Normal cell {cell} does not map to the pinned all-bearing carrier owner")
            if is_positive:
                positive.add(cell)
            if is_separated:
                separated.add(cell)
            projected_rows.append({
                "cell_name": cell,
                "source_group": str(binding["group"]),
                "source_row_id": str(binding["source_row_id"]),
                "physical_owner": binding["physical_owner"],
                "classification_from_zero_u_711_interval_audit": classification,
                "strictly_positive_after_rounding": is_positive,
                "strictly_separating_after_rounding": is_separated,
            })
        if len(positive) != int(state.get("strict_positive_bearing_count", -1)) or len(separated) != int(state.get("strictly_separated_count", -1)):
            raise RuntimeError("Projected classification counts differ from the interval diagnostic")
        if state.get("unresolved_count") != 0 or state.get("input_mask_mismatch_count") != 2:
            raise RuntimeError("The two recorded mask exceptions or resolved classification gate changed")
        positive_sets.append(positive)
        projected_states.append({
            "load_factor": float(state["load_factor"]),
            "bearing_count": len(positive),
            "separating_count": len(separated),
            "ambiguous_or_unresolved_count": 0,
            "rows": projected_rows,
        })
    if any(mask != positive_sets[0] for mask in positive_sets[1:]):
        raise RuntimeError("The positive-cell mask is not stable across all seven interval states")
    derived_mask = positive_sets[0]
    direct_released_positive = set(diagnostic["input_inactive_cells_strictly_positive"])
    direct_selected_released = set(diagnostic["input_selected_cells_not_strictly_positive"])
    if len(derived_mask) != 46 or derived_mask - direct_mask != direct_released_positive or direct_mask - derived_mask != direct_selected_released:
        raise RuntimeError("The 46-cell positive set does not equal the exact diagnosed 44-to-46 change")
    if direct_released_positive != {"floor_base_floor_left_36", "floor_base_floor_right_12"} or direct_selected_released:
        raise RuntimeError("The two exact 44-input inactive-bearing cells changed")

    source_sha = {path: sha(ROOT / path) for path in sorted(EXPECTED)}
    # The adapter independently requires these all-bearing physical-control pins
    # in the projected screen's source map.
    source_sha.update({
        rel(CONTROL_DIR / name): sha(ROOT / CONTROL_DIR / name)
        for name in ("model.json", "model.inp", "model.dat", "execution.json")
    })
    source_sha[rel(RESPONSE_AUDITOR)] = sha(ROOT / RESPONSE_AUDITOR)

    screen = {
        "schema": "current_case_bound_floor_diagnostic_screen/v1",
        "status": "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH",
        "case_id": "a1-rear",
        "candidate": diagnostic["candidate"],
        "geometry_revision_id": diagnostic["geometry_revision_id"],
        "full_step_native_convergence": True,
        "native_solve_launched_by_projection": False,
        "corner_demands_usable": False,
        "mechanical_acceptance": False,
        "physical_force_adoption": False,
        "screen_forces_or_active_states_adopted": False,
        "floor_mask_or_iteration_proposed_by_projection": False,
        "all_printed_floor_laws_checked": True,
        "same_positive_cell_set_at_all_printed_times": True,
        "all_printed_times": times,
        "states": projected_states,
        "diagnostic_positive_cells_at_final_time": sorted(derived_mask),
        "diagnostic_separating_cells_at_final_time": sorted(set(normal_bindings) - derived_mask),
        "source_stage": "selected_44_terminal_run_zero_u_711_normal_interval_projection",
        "source_normal_interval_diagnostic": {
            "path": rel(DIAGNOSTIC),
            "sha256": source_sha[rel(DIAGNOSTIC)],
            "status": diagnostic["status"],
            "schema": diagnostic["schema"],
            "source_selected_cell_count": len(direct_mask),
            "derived_strict_positive_cell_count": len(derived_mask),
            "inactive_positive_cells": sorted(direct_released_positive),
            "selected_nonpositive_cells": sorted(direct_selected_released),
            "unresolved_row_count_per_state": [int(state["unresolved_count"]) for state in diagnostic["states"]],
            "native_forces_or_rf_values_copied": False,
        },
        "source_controls_physics_authority": {
            "role": "original_case_bound_all_bearing_source_physics_and_geometry",
            "model_path": rel(CONTROL_MODEL),
            "model_sha256": source_sha[rel(CONTROL_MODEL)],
            "deck_path": rel(CONTROL_DIR / "model.inp"),
            "deck_sha256": source_sha[rel(CONTROL_DIR / "model.inp")],
            "case_id": "a1-rear",
            "diagnostic_forces_used": False,
        },
        "direct_selected_44_run_lineage": {
            "role": "rejected_proposal_classification_lineage_only",
            "model_path": rel(DIRECT_RUN / "model.json"),
            "model_sha256": source_sha[rel(DIRECT_RUN / "model.json")],
            "deck_path": rel(DIRECT_RUN / "model.inp"),
            "deck_sha256": source_sha[rel(DIRECT_RUN / "model.inp")],
            "dat_path": rel(DIRECT_RUN / "model.dat"),
            "dat_sha256": source_sha[rel(DIRECT_RUN / "model.dat")],
            "execution_path": rel(DIRECT_RUN / "execution.json"),
            "execution_sha256": source_sha[rel(DIRECT_RUN / "execution.json")],
            "case_context_path": rel(DIRECT_RUN / "case-context.json"),
            "case_context_sha256": source_sha[rel(DIRECT_RUN / "case-context.json")],
            "terminal_status": diagnostic["native_case_terminal_status"],
            "native_forces_or_active_states_adopted": False,
        },
        "normal_interval_method": {
            "wrapper_path": rel(ZERO_U_DIR / "response_audit.py"),
            "wrapper_sha256": source_sha[rel(ZERO_U_DIR / "response_audit.py")],
            "stable_parser_path": rel(ZERO_U_DIR / "stable_response_audit.py"),
            "stable_parser_sha256": source_sha[rel(ZERO_U_DIR / "stable_response_audit.py")],
            "known_method_replay_path": rel(ZERO_U_DIR / "zero_u_token_replay.json"),
            "known_method_replay_sha256": source_sha[rel(ZERO_U_DIR / "zero_u_token_replay.json")],
            "interval_source_path": rel(DIAGNOSTIC),
            "classification_only_projection": True,
            "force_values_copied": False,
        },
        "proposed_mask_basis": {
            "cells": sorted(derived_mask),
            "status": "diagnostic_positive_set_as_one_input_proposal_only",
            "cell_count": len(derived_mask),
            "inactive_cell_count": 100 - len(derived_mask),
            "selected_tangent_row_count": 2 * len(derived_mask),
            "inactive_tangent_row_count": 2 * (100 - len(derived_mask)),
            "proposed_44_to_46_added_cells": sorted(derived_mask - direct_mask),
            "proposed_44_to_46_removed_cells": sorted(direct_mask - derived_mask),
            "automatic_mask_iteration_authorized": False,
            "acceptance_or_unique_support_claimed": False,
        },
        "source_sha256": source_sha,
        "limits": [
            "Projection retains only interval-derived normal-law classifications and owner/source identities; it omits all native force and RF values.",
            "The 46-cell mask is an input proposal derived from this exact rejected 44-cell run; no mask, force, or demand transfers from another case.",
            "The original A1-rear all-bearing controls remain the source of geometry, material, CLOAD, and carrier-law authority.",
            "The direct selected-44 native response is classification lineage only and is not adopted as the response to the 46-cell input.",
            "No accepted floor support, release/recontact method, uniqueness, corner demand, or mechanical acceptance is claimed.",
        ],
    }
    write_json(screen_path, screen)
    write_json(pins_path, {
        "schema": "current_springa_a1_rear_46_cell_screen_projection_pins/v1",
        "producer_path": rel(Path(__file__)),
        "producer_sha256": sha(Path(__file__)),
        "screen_path": rel(screen_path),
        "screen_sha256": sha(screen_path),
        "source_sha256": source_sha,
    })
    print(json.dumps({
        "status": screen["status"],
        "case_id": screen["case_id"],
        "derived_selected_cell_count": len(derived_mask),
        "derived_inactive_cell_count": 100 - len(derived_mask),
        "added_cells_from_direct_44": sorted(derived_mask - direct_mask),
        "removed_cells_from_direct_44": sorted(direct_mask - derived_mask),
        "screen_path": rel(screen_path),
        "screen_sha256": sha(screen_path),
        "producer_sha256": sha(Path(__file__)),
        "force_values_copied": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
