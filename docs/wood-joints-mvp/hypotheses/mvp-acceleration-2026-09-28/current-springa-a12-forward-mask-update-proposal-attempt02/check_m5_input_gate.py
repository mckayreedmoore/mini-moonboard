"""Bind the prepared M5 input to the standard A12-forward context and 711 gate."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
PACKET = BASE / "current-springa-a12-forward-mask-update-proposal-attempt02"
OUTPUT = PACKET / "a12-forward"
MODEL = OUTPUT / "model.json"
DECK = OUTPUT / "model.inp"
SCREEN = PACKET / "screen.json"
CONTEXT_TEMPLATE = BASE / "current-springa-case-bound-floor-input-adapter-attempt10/a12-forward/case-bound-input-context.json"
CONTEXT_CONTRACT = BASE / "current-springa-case-bound-floor-input-adapter-attempt10/a12-forward/case-bound-input-context-contract.json"
AUDITOR = BASE / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
STABLE = BASE / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
REGISTER = BASE / "current-six-case-source-load-register-attempt01/register.json"
CONTROL = BASE / "current-springa-frame-a12-forward-all-bearing-attempt01"
FRESH = BASE / "current-springa-six-case-frame-input-adapter-attempt01/a12-forward/model.json"
PROFILE = ROOT / "fea/calculix_223/solver-profile.json"
CONTEXT = PACKET / "case-context.json"
GATE = PACKET / "input-gate.json"
PINS = PACKET / "input-gate-source-pins.json"
PROPOSAL = PACKET / "proposal.json"

AUDITOR_SHA256 = "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"
STABLE_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"
REGISTER_SHA256 = "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def import_auditor():
    spec = importlib.util.spec_from_file_location("pinned711_a12_forward_m5_input_gate", AUDITOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import the pinned 711 response auditor")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    proposal = read(PROPOSAL)
    screen = read(SCREEN)
    record = read(MODEL)
    deck_text = DECK.read_text(encoding="utf-8")
    if proposal.get("status") != "PASS_INPUT_ONLY_SOURCE_BOUND_MASK_PROPOSAL":
        raise RuntimeError("M5 producer did not report the expected input-only proposal status")
    if proposal.get("parent_native_readiness") is not False or proposal.get("native_solve_executed") is not False:
        raise RuntimeError("M5 proposal cannot create native readiness or report a native solve")
    if sha(AUDITOR) != AUDITOR_SHA256 or sha(STABLE) != STABLE_SHA256:
        raise RuntimeError("Pinned 711/stable response checker source changed")
    if sha(REGISTER) != REGISTER_SHA256:
        raise RuntimeError("Pinned case-load register changed")
    if (sha(MODEL) != proposal["prepared_model_sha256"]
            or sha(DECK) != proposal["prepared_deck_sha256"]
            or sha(SCREEN) != proposal["screen_sha256"]):
        raise RuntimeError("M5 proposal hashes do not bind the prepared model/deck/screen")

    contract = read(CONTEXT_CONTRACT)
    if contract.get("schema") != "current_springa_case_bound_input_context_contract/v1":
        raise RuntimeError("Unexpected case-context contract schema")
    if contract.get("instance_schema") != "current_springa_case_bound_input_context/v1":
        raise RuntimeError("Unexpected case-context instance schema")

    selected = sorted(map(str, screen["diagnostic_positive_cells_at_final_time"]))
    inactive = sorted(map(str, screen["diagnostic_separating_cells_at_final_time"]))
    if len(selected) != 34 or len(inactive) != 66 or set(selected) & set(inactive):
        raise RuntimeError("M5 source screen does not partition 100 floor normals as 34/66")
    if set(record["floor_selected_bearing_cells"]) != set(selected):
        raise RuntimeError("Prepared M5 model differs from the source-derived screen mask")
    if (screen.get("proposed_mask_is_selected_response") is not False
            or screen.get("screen_forces_or_active_states_adopted") is not False
            or screen.get("corner_demands_usable") is not False
            or screen.get("physical_force_adoption") is not False):
        raise RuntimeError("M5 diagnostic screen falsely adopts rejected-run response states")

    model_rel, deck_rel, screen_rel = map(rel, (MODEL, DECK, SCREEN))
    model_sha, deck_sha, screen_sha = map(sha, (MODEL, DECK, SCREEN))
    selected_rows = [int(row["source_row_original_index"])
                     for row in record["floor_selected_mask_by_original_row"] if row["selected"] is True]
    inactive_rows = [int(row["source_row_original_index"])
                     for row in record["floor_selected_mask_by_original_row"] if row["selected"] is False]
    if len(selected_rows) != 68 or len(inactive_rows) != 132:
        raise RuntimeError("M5 row mask must retain 68 selected and 132 inactive source tangents")
    if len(record["floor_reference_nodes_and_load_map"]) != 68:
        raise RuntimeError("M5 floor reference map must contain exactly 68 selected tangent rows")

    context = read(CONTEXT_TEMPLATE)
    context.update({
        "diagnostic_floor_screen_case_id": "a12-forward",
        "diagnostic_floor_screen_path": screen_rel,
        "diagnostic_floor_screen_sha256": screen_sha,
        "diagnostic_floor_screen_status": screen["status"],
        "selected_cells": selected,
        "inactive_cells": inactive,
        "selected_floor_cell_count": len(selected),
        "inactive_floor_cell_count": len(inactive),
        "active_original_tangent_row_count": len(selected_rows),
        "inactive_original_tangent_row_count": len(inactive_rows),
        "selected_original_row_indices": selected_rows,
        "inactive_original_row_indices": inactive_rows,
        "selected_floor_input_model_schema": record["schema"],
        "selected_floor_model_json_path": model_rel,
        "selected_floor_model_json_sha256": model_sha,
        "selected_floor_deck_path": deck_rel,
        "selected_floor_deck_sha256": deck_sha,
        "selected_input_model_json_path": model_rel,
        "selected_input_model_json_sha256": model_sha,
        "selected_input_deck_path": deck_rel,
        "selected_input_deck_sha256": deck_sha,
        "input_only": True,
        "native_solve_executed": False,
        "mechanical_acceptance": False,
        "screen_positive_forces_or_active_states_reused_as_response": False,
    })
    required = set(contract["required_context_fields"])
    if not required.issubset(context):
        raise RuntimeError(f"Case context misses required fields: {sorted(required - set(context))}")
    CONTEXT.write_text(json.dumps(context, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

    auditor = import_auditor()
    case_pin = auditor._validate_case_context(context)
    method_contract = auditor._validate_model(record, deck_text, context)
    if (case_pin["selected_cell_count"] != 34
            or case_pin["inactive_cell_count"] != 66
            or method_contract["selected_cells"] != set(selected)
            or method_contract["inactive_cells"] != set(inactive)):
        raise RuntimeError("Pinned input gate returned a different M5 floor mask")

    gate = {
        "schema": "current_springa_a12_forward_m5_input_gate/v1",
        "status": "PASS_PINNED_711_CASE_CONTEXT_AND_MODEL_INPUT_GATE",
        "case_id": "a12-forward",
        "candidate": context["candidate"],
        "geometry_revision_id": context["geometry_revision_id"],
        "model_path": model_rel,
        "model_sha256": model_sha,
        "deck_path": deck_rel,
        "deck_sha256": deck_sha,
        "diagnostic_screen_path": screen_rel,
        "diagnostic_screen_sha256": screen_sha,
        "case_context_path": rel(CONTEXT),
        "case_context_sha256": sha(CONTEXT),
        "context_schema": context["schema"],
        "context_contract_path": rel(CONTEXT_CONTRACT),
        "context_contract_sha256": sha(CONTEXT_CONTRACT),
        "response_auditor_path": rel(AUDITOR),
        "response_auditor_sha256": sha(AUDITOR),
        "pinned_stable_recovery_source_path": rel(STABLE),
        "pinned_stable_recovery_source_sha256": sha(STABLE),
        "selected_normal_cells": len(method_contract["selected_cells"]),
        "inactive_normal_cells": len(method_contract["inactive_cells"]),
        "active_floor_tangent_rows": len(selected_rows),
        "inactive_floor_tangent_rows": len(inactive_rows),
        "source_inventory": method_contract["inventory_summary"],
        "allbearing_control_model_sha256": context["source_controls_model_json_sha256"],
        "allbearing_control_deck_sha256": context["source_controls_deck_sha256"],
        "source_load_register_sha256": context["source_case_load_register_sha256"],
        "selected_input_matches_prepared_model_and_deck": True,
        "input_gate_only": True,
        "native_solve_executed": False,
        "freeze_created": False,
        "parent_native_readiness": False,
        "physical_force_adoption": False,
        "corner_demands_usable": False,
        "mechanical_acceptance": False,
        "limits": [
            "This checks source/load/context and serialized selected-floor input only; no DAT or response forces are consumed.",
            "The M5 screen is a diagnostic hypothesis from rejected M4 output, not an accepted contact state or response.",
            "The parent owns freeze, readiness review, and any serialized native execution.",
        ],
    }
    GATE.write_text(json.dumps(gate, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

    source_paths = [
        Path(__file__).resolve(),
        PACKET / "prepare_m5_proposal.py",
        PACKET / "README.md",
        PROPOSAL,
        OUTPUT / "audit.json",
        OUTPUT / "model.json",
        OUTPUT / "model.inp",
        OUTPUT / "source-pins.json",
        SCREEN,
        CONTEXT_CONTRACT,
        CONTEXT_TEMPLATE,
        AUDITOR,
        STABLE,
        REGISTER,
        CONTROL / "model.json",
        CONTROL / "model.inp",
        CONTROL / "model.dat",
        CONTROL / "execution.json",
        CONTROL / "freeze.json",
        FRESH,
        PROFILE,
    ]
    for source_path, expected in screen["source_sha256"].items():
        path = Path(source_path)
        if not path.is_absolute():
            path = ROOT / path
        if sha(path) != expected:
            raise RuntimeError(f"Pinned M5 diagnostic source changed: {source_path}")
    direct_hashes = {rel(path): sha(path) for path in source_paths}
    screen_pin_map_sha256 = hashlib.sha256(
        json.dumps(screen["source_sha256"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    pins = {
        "schema": "current_springa_a12_forward_m5_input_gate_source_pins/v1",
        "status": "PASS_SOURCE_PINS_REHASHED",
        "direct_source_sha256": dict(sorted(direct_hashes.items())),
        "diagnostic_screen_source_pin_map_sha256": screen_pin_map_sha256,
        "diagnostic_screen_source_pin_map_rehashed": True,
        "transitive_screen_sources_rehashed": True,
        "source_sha256": {
            rel(SCREEN): screen_sha,
            rel(MODEL): model_sha,
            rel(DECK): deck_sha,
            rel(CONTEXT): sha(CONTEXT),
            rel(GATE): sha(GATE),
        },
        "screen_source_pin_count": len(screen["source_sha256"]),
        "solver_profile_path": rel(PROFILE),
        "solver_profile_sha256": sha(PROFILE),
        "direct_source_pin_count": len(direct_hashes),
        "diagnostic_screen_transitive_source_pin_count": len(screen["source_sha256"]),
        "freeze_created": False,
        "native_solve_executed": False,
        "parent_native_readiness": False,
    }
    PINS.write_text(json.dumps(pins, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": gate["status"],
        "context_sha256": gate["case_context_sha256"],
        "model_sha256": model_sha,
        "deck_sha256": deck_sha,
        "screen_sha256": screen_sha,
        "auditor_sha256": sha(AUDITOR),
        "stable_source_sha256": sha(STABLE),
        "direct_source_pins": len(direct_hashes),
        "transitive_screen_pins": len(screen["source_sha256"]),
        "native_solve_executed": False,
        "freeze_created": False,
        "parent_native_readiness": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
