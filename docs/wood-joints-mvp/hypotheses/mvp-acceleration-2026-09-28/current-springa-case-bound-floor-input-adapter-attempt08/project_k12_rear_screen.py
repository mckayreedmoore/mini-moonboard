#!/usr/bin/env python3
"""Project the pinned K12-rear normal-interval diagnosis to the input-screen contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
OUT = Path(__file__).resolve().parent
DIAGNOSTIC_DIR = BASE / "current-springa-k12-rear-selected-floor-normal-interval-diagnostic-attempt01"
DIAGNOSTIC = DIAGNOSTIC_DIR / "k12-rear-normal-intervals.json"
INTERVAL_PRODUCER = DIAGNOSTIC_DIR / "produce.py"
CONTROL_DIR = BASE / "current-springa-frame-k12-rear-all-bearing-attempt01"
DIRECT_RUN = BASE / "current-springa-selected-floor-k12-rear-attempt02"
CONTROL_MODEL = CONTROL_DIR / "model.json"
FRESH_MODEL = BASE / "current-springa-six-case-frame-input-adapter-attempt01/k12-rear/model.json"
REGISTER = BASE / "current-six-case-source-load-register-attempt01/register.json"
RESPONSE_AUDITOR = BASE / "current-springa-frame-response-audit-attempt01/response_audit.py"
ZERO_U_DIR = BASE / "current-springa-zero-u-token-response-audit-attempt01"
DIAGNOSTIC_PIN_FILE = DIAGNOSTIC_DIR / "source-pins.json"
DIAGNOSTIC_README = DIAGNOSTIC_DIR / "README.md"
EXPECTED: dict[str, str] = {
    str(CONTROL_DIR / "model.json"): "72cc39411bb92d3ee739a9b9aa9b025fe466f2b818f29feaa76a26c284366424",
    str(CONTROL_DIR / "model.inp"): "0cdcee16de7be40e8a7a511c26f6cbf67f116d2475f76eab294fa661ee6fac68",
    str(CONTROL_DIR / "model.dat"): "8c3c7590e11df6c8bce52e814ece2aba2f05ff24eb261517e95e74db41528807",
    str(CONTROL_DIR / "execution.json"): "4e10033ba2a12952122ac790ae6c4dcf4a9585b936d239e86d73465be6db6ccc",
    str(CONTROL_DIR / "freeze.json"): "161e9b8bfecb7ef4d5060db4d6fb25aeeb38df5fa4332a3ba47fbd92df70ac92",
    str(CONTROL_DIR / "authorization.json"): "13050058f4090bb347503c64e18fad137da3ee1a8fcd24b6c5b40d56f116f670",
    str(CONTROL_DIR / "parent-serialized-input-audit.json"): "31752ce76ff4310ae2d85327e4ea9436fc273fcfeddd025f7609e217b6533d80",
    str(DIRECT_RUN / "model.json"): "1870c72e16870521f12d783bb3d0b31c46ca6459a95059881482ee7255c64ff8",
    str(DIRECT_RUN / "model.inp"): "dc06ba59d98b88c201c756112eb760a3999ba8276e92ed75dcd36ffac4bd5cd6",
    str(DIRECT_RUN / "model.dat"): "833f8258417afd0a4a83759b503a47820a424a7639799e17bd5c930432154238",
    str(DIRECT_RUN / "execution.json"): "97ee43a8f0e77d903c9ebf7c76f49314ebc3037cbdb2a93c9b76c9b58069b6e8",
    str(DIRECT_RUN / "freeze.json"): "c375a104f13b78ae238a78a1a1dfed01551f618a2f3ad832b9c8c3ad39bccadd",
    str(DIRECT_RUN / "authorization.json"): "f35757c184bd8481a20be19aa4dbf4d3157d886f3db57b93ccfc3c21f4d3bce3",
    str(DIRECT_RUN / "case-context.json"): "e5f0f3e290ccd86fd332570254195ad3f298622058cd61cb1b94005f899250a6",
    str(DIRECT_RUN / "parent-serialized-input-audit.json"): "0da5ab2bf5a1547c13d76d015d9b77b696568cf701e9e70e66204cac8686c74a",
    str(DIRECT_RUN / "parent-case-context-check.json"): "f1feba6a3486c5bc8f0ab3d73a7a94fc5ecea5fda78d6f91ceb1a1f38a751091",
    str(DIRECT_RUN / "parent-readiness-review.json"): "407d2199e41ed86fdf7f7a5b9efe328d1cfb1a277b5ac76932bddf248a92731e",
    str(DIRECT_RUN / "parent-terminal-assessment.json"): "410868e4b4d7d88e95709ae603ce41f5ef7050fc828bb7efe40307bf300e767f",
    str(DIAGNOSTIC): "a84c8235e64964ce1b52cc8d6adde589d0f062fb1692ba9b4ac95f6972f3c73e",
    str(INTERVAL_PRODUCER): "ee50313fe5a5b456fa54a8f2bc317abf6b8e06274b9a465e4bb5fac37b47479d",
    str(DIAGNOSTIC_PIN_FILE): "6d32be077d7fc63ba0a4210405097d2491ec6aa799b19d0760173313411062af",
    str(DIAGNOSTIC_README): "8b1e4b961fddf94adb26f7a05637420ccd1356805cb8e0bb172bd95c3bc488c8",
    str(ZERO_U_DIR / "response_audit.py"): "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
    str(ZERO_U_DIR / "stable_response_audit.py"): "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    str(ZERO_U_DIR / "replay_zero_u_tokens.py"): "6b49312429c78e04d0a70a7a428382028ac9e75ab01a69b53271d9feca91bd32",
    str(ZERO_U_DIR / "zero_u_token_replay.json"): "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1",
    str(RESPONSE_AUDITOR): "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
    str(FRESH_MODEL): "46155d5637e5d39373cd40d973bdfc499439f7e36d7e1167a7edbb2402d061a8",
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
    direct_context = read_json(ROOT / (DIRECT_RUN / "case-context.json"))
    direct_input_audit = read_json(ROOT / (DIRECT_RUN / "parent-serialized-input-audit.json"))
    direct_context_check = read_json(ROOT / (DIRECT_RUN / "parent-case-context-check.json"))
    direct_readiness = read_json(ROOT / (DIRECT_RUN / "parent-readiness-review.json"))
    direct_terminal = read_json(ROOT / (DIRECT_RUN / "parent-terminal-assessment.json"))
    diagnostic_source_pins = read_json(ROOT / DIAGNOSTIC_PIN_FILE)
    fresh = read_json(ROOT / FRESH_MODEL)
    if (
        diagnostic.get("schema") != "current_springa_selected_floor_normal_interval_diagnostic/v1"
        or diagnostic.get("status") != "COMPLETED_NORMAL_LAW_DIAGNOSTIC_ONLY_PROPOSED_BRANCH_REJECTED"
        or diagnostic.get("native_case_terminal_status") != "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
        or diagnostic.get("case_id") != "k12-rear"
        or diagnostic.get("candidate") != control.get("candidate")
        or diagnostic.get("geometry_revision_id") != control.get("geometry_revision_id")
        or diagnostic.get("selected_floor_branch_id") != "monotone_zero_gap_first_bearing_reference_zero"
        or diagnostic.get("printed_state_count") != 7
        or diagnostic.get("normal_count_per_state") != 100
        or diagnostic.get("strict_positive_cell_set_stable_all_states") is not True
        or diagnostic.get("compatibility_exception_count") != 2
        or diagnostic.get("input_selected_cells_not_strictly_positive") != []
        or diagnostic.get("input_inactive_cells_strictly_positive") != [
            "floor_base_floor_left_27", "floor_base_floor_left_29"
        ]
        or diagnostic_source_pins.get("report_sha256") != EXPECTED[str(DIAGNOSTIC)]
        or diagnostic_source_pins.get("producer_sha256") != EXPECTED[str(INTERVAL_PRODUCER)]
        or diagnostic_source_pins.get("source_sha256") != diagnostic.get("provenance", {}).get("source_sha256")
    ):
        raise RuntimeError("Pinned interval diagnostic identity, status, or branch evidence changed")
    if direct.get("case_id") != "k12-rear" or control.get("case_id") != "k12-rear" or fresh.get("case_id") != "k12-rear":
        raise RuntimeError("The all-bearing physics authority and direct diagnostic lineage must be K12-rear")
    if (execution.get("run_id") != "springa-selected-k12-rear-attempt02"
            or execution.get("returncode") != 0
            or execution.get("container_confirmed_terminal") is not True):
        raise RuntimeError("Direct 21-cell lineage is not the exact terminal run")
    if (direct_context.get("case_id") != "k12-rear"
            or direct_context.get("diagnostic_floor_screen_status") != "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
            or direct_input_audit.get("status") != "PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT"
            or direct_input_audit.get("case_id") != "k12-rear"
            or direct_input_audit.get("proposed_branch_accepted") is not False
            or direct_context_check.get("status") != "PASS_FROZEN_CASE_BOUND_INPUT_CONTRACT_ONLY"
            or direct_context_check.get("native_response_consumed") is not False
            or direct_context_check.get("inventory", {}).get("selected_bearing_cells") != 21
            or direct_context_check.get("inventory", {}).get("inactive_separated_cells") != 79
            or direct_readiness.get("case_id") != "k12-rear"
            or direct_readiness.get("mechanical_acceptance") is not False
            or direct_terminal.get("status") != "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
            or direct_terminal.get("strict_response_exception") != "Inactive floor normal is not strictly separated with zero endpoint RF: SPR1104"
            or direct_terminal.get("corner_demands_usable") is not False
            or direct_terminal.get("physical_failure_inferred") is not False):
        raise RuntimeError("Direct attempt02 rejected lineage or its case context changed")

    direct_mask = set(map(str, direct.get("floor_selected_bearing_cells", [])))
    if len(direct_mask) != 21:
        raise RuntimeError("The direct selected-proposal lineage must have exactly 21 selected cells")
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
    if (len(derived_mask) != 23 or derived_mask - direct_mask != direct_released_positive
            or direct_mask - derived_mask != direct_selected_released):
        raise RuntimeError("The 23-cell positive set does not equal the exact diagnosed 21-to-23 change")
    if direct_released_positive != {
        "floor_base_floor_left_27", "floor_base_floor_left_29",
    } or direct_selected_released:
        raise RuntimeError("The exact 21-input inactive-bearing and selected-release cells changed")

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
        "case_id": "k12-rear",
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
        "source_stage": "selected_21_terminal_run_zero_u_711_normal_interval_projection",
        "source_normal_interval_diagnostic": {
            "path": rel(DIAGNOSTIC),
            "sha256": source_sha[rel(DIAGNOSTIC)],
            "status": diagnostic["status"],
            "schema": diagnostic["schema"],
            "source_selected_cell_count": len(direct_mask),
            "derived_strict_positive_cell_count": len(derived_mask),
            "normal_count_per_state": 100,
            "printed_state_count": len(times),
            "strict_positive_cell_set_stable_all_states": True,
            "compatibility_exception_count": diagnostic["compatibility_exception_count"],
            "inactive_positive_cells": sorted(direct_released_positive),
            "selected_nonpositive_cells": sorted(direct_selected_released),
            "unresolved_row_count_per_state": [int(state["unresolved_count"]) for state in diagnostic["states"]],
            "producer_path": rel(INTERVAL_PRODUCER),
            "producer_sha256": source_sha[rel(INTERVAL_PRODUCER)],
            "source_pins_path": rel(DIAGNOSTIC_PIN_FILE),
            "source_pins_sha256": source_sha[rel(DIAGNOSTIC_PIN_FILE)],
            "native_forces_or_rf_values_copied": False,
        },
        "source_controls_physics_authority": {
            "role": "original_case_bound_all_bearing_source_physics_and_geometry",
            "model_path": rel(CONTROL_MODEL),
            "model_sha256": source_sha[rel(CONTROL_MODEL)],
            "deck_path": rel(CONTROL_DIR / "model.inp"),
            "deck_sha256": source_sha[rel(CONTROL_DIR / "model.inp")],
            "case_id": "k12-rear",
            "diagnostic_forces_used": False,
        },
        "direct_selected_21_run_lineage": {
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
            "input_audit_path": rel(DIRECT_RUN / "parent-serialized-input-audit.json"),
            "input_audit_sha256": source_sha[rel(DIRECT_RUN / "parent-serialized-input-audit.json")],
            "context_check_path": rel(DIRECT_RUN / "parent-case-context-check.json"),
            "context_check_sha256": source_sha[rel(DIRECT_RUN / "parent-case-context-check.json")],
            "readiness_review_path": rel(DIRECT_RUN / "parent-readiness-review.json"),
            "readiness_review_sha256": source_sha[rel(DIRECT_RUN / "parent-readiness-review.json")],
            "terminal_assessment_path": rel(DIRECT_RUN / "parent-terminal-assessment.json"),
            "terminal_assessment_sha256": source_sha[rel(DIRECT_RUN / "parent-terminal-assessment.json")],
            "terminal_status": diagnostic["native_case_terminal_status"],
            "native_forces_or_active_states_adopted": False,
            "strict_response_exception": direct_terminal["strict_response_exception"],
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
            "proposed_21_to_23_added_cells": sorted(derived_mask - direct_mask),
            "proposed_21_to_23_removed_cells": sorted(direct_mask - derived_mask),
            "automatic_mask_iteration_authorized": False,
            "acceptance_or_unique_support_claimed": False,
        },
        "source_sha256": source_sha,
        "limits": [
            "Projection retains only interval-derived normal-law classifications and owner/source identities; it omits all native force and RF values.",
            "The 23-cell mask is one input proposal derived from this exact rejected 21-cell run; no mask, force, or demand transfers from another case.",
            "The original K12-rear all-bearing controls remain the source of geometry, material, CLOAD, and carrier-law authority.",
            "The direct selected-21 native response is classification lineage only and is not adopted as the response to the 23-cell input.",
            "No accepted floor support, release/recontact method, uniqueness, corner demand, or mechanical acceptance is claimed.",
        ],
    }
    write_json(screen_path, screen)
    write_json(pins_path, {
        "schema": "current_springa_k12_rear_23_cell_screen_projection_pins/v1",
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
        "added_cells_from_direct_21": sorted(derived_mask - direct_mask),
        "removed_cells_from_direct_21": sorted(direct_mask - derived_mask),
        "screen_path": rel(screen_path),
        "screen_sha256": sha(screen_path),
        "producer_sha256": sha(Path(__file__)),
        "force_values_copied": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
