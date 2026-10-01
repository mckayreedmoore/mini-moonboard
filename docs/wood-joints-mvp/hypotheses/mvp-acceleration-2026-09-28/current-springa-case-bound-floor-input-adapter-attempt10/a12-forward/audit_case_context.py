"""Independently verify the A12-forward adapter context binding; never executes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[6]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
PACKET = BASE / "current-springa-case-bound-floor-input-adapter-attempt10"
CONTROL = BASE / "current-springa-frame-a12-forward-all-bearing-attempt01"
FRESH_MODEL = BASE / "current-springa-six-case-frame-input-adapter-attempt01/a12-forward/model.json"
REGISTER = BASE / "current-six-case-source-load-register-attempt01/register.json"
SCREEN = PACKET / "screen.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def source_path(relative: str) -> Path:
    path = ROOT / relative
    assert path.resolve().is_relative_to(ROOT.resolve()), relative
    return path


def main() -> None:
    context_path = HERE / "case-bound-input-context.json"
    contract_path = HERE / "case-bound-input-context-contract.json"
    model_path = HERE / "model.json"
    deck_path = HERE / "model.inp"
    adapter_audit_path = HERE / "audit.json"
    pins_path = HERE / "source-pins.json"

    context = read(context_path)
    contract = read(contract_path)
    model = read(model_path)
    adapter_audit = read(adapter_audit_path)
    pins = read(pins_path)
    control = read(CONTROL / "model.json")
    fresh = read(FRESH_MODEL)
    register = read(REGISTER)
    screen = read(SCREEN)

    assert contract["schema"] == "current_springa_case_bound_input_context_contract/v1"
    assert context["schema"] == contract["instance_schema"] == "current_springa_case_bound_input_context/v1"
    assert set(contract["required_context_fields"]) <= set(context)
    assert context["case_id"] == model["case_id"] == control["case_id"] == fresh["case_id"] == screen["case_id"] == "a12-forward"
    assert context["candidate"] == model["candidate"] == control["candidate"] == fresh["candidate"] == register["candidate"]
    assert context["geometry_revision_id"] == model["geometry_revision_id"] == control["geometry_revision_id"] == fresh["geometry_revision_id"] == register["geometry_revision_id"]
    assert model["schema"] == "current_springa_selected_floor_input_model/v1"

    assert register["schema"] == "current_springa_six_case_source_load_register/v1"
    assert register["status"] == "PASS_FRESH_SIX_CASE_SOURCE_LOAD_WRENCH_REGISTER"
    assert register["same_nonload_signature_across_all_six_cases"] is True
    matching = [record for record in register["cases"] if record.get("case_id") == "a12-forward"]
    assert len(matching) == 1
    record = matching[0]
    assert digest(record) == context["case_record_sha256"]
    assert record["source_model_inputs_sha256"] == context["source_model_inputs_sha256"]
    assert register["candidate"] == context["candidate"]
    assert register["geometry_revision_id"] == context["geometry_revision_id"]

    register_rel = context["source_case_load_register_path"]
    assert register_rel == str(REGISTER.as_posix())
    assert sha(source_path(register_rel)) == context["source_case_load_register_sha256"]
    assert context["source_case_load_register_sha256"] == sha(REGISTER)

    assert context["source_controls_model_json_path"] == str((CONTROL / "model.json").as_posix())
    assert context["source_controls_deck_path"] == str((CONTROL / "model.inp").as_posix())
    assert context["source_controls_model_json_sha256"] == sha(CONTROL / "model.json")
    assert context["source_controls_deck_sha256"] == sha(CONTROL / "model.inp")
    assert context["source_controls_terminal_dat_path"] == str((CONTROL / "model.dat").as_posix())
    assert context["source_controls_terminal_dat_sha256"] == sha(CONTROL / "model.dat")
    assert context["source_controls_execution_path"] == str((CONTROL / "execution.json").as_posix())
    assert context["source_controls_execution_sha256"] == sha(CONTROL / "execution.json")
    assert context["source_controls_freeze_sha256"] == sha(CONTROL / "freeze.json")

    assert context["source_fresh_case_model_path"] == str(FRESH_MODEL.as_posix())
    assert context["source_fresh_case_model_sha256"] == sha(FRESH_MODEL)
    assert control["source_load_register_binding"] == fresh["source_load_register_binding"]
    assert control["source_load_register_binding"]["case_record_sha256"] == context["case_record_sha256"]
    assert control["source_load_register_binding"]["register_sha256"] == context["source_case_load_register_sha256"]

    screen_rel = context["diagnostic_floor_screen_path"]
    assert screen_rel == str(SCREEN.as_posix())
    assert context["diagnostic_floor_screen_sha256"] == sha(SCREEN)
    assert context["diagnostic_floor_screen_case_id"] == screen["case_id"] == "a12-forward"
    assert context["diagnostic_floor_screen_status"] == screen["status"] == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
    assert screen["source_sha256"][context["source_controls_model_json_path"]] == context["source_controls_model_json_sha256"]
    assert screen["source_sha256"][context["source_controls_deck_path"]] == context["source_controls_deck_sha256"]
    assert screen["source_sha256"][context["source_controls_terminal_dat_path"]] == context["source_controls_terminal_dat_sha256"]
    assert screen["source_sha256"][context["source_controls_execution_path"]] == context["source_controls_execution_sha256"]
    for path, expected in screen["source_sha256"].items():
        assert sha(source_path(path)) == expected, path

    assert context["selected_floor_branch_id"] == "monotone_zero_gap_first_bearing_reference_zero"
    selected = set(screen["diagnostic_positive_cells_at_final_time"])
    inactive = set(screen["diagnostic_separating_cells_at_final_time"])
    assert len(selected) == 37 and len(inactive) == 63 and selected.isdisjoint(inactive)
    assert selected == set(context["selected_cells"])
    assert inactive == set(context["inactive_cells"])
    assert selected | inactive == {row["cell_name"] for row in screen["states"][-1]["rows"]}
    refs = model["floor_reference_nodes_and_load_map"]
    assert {str(row["normal_cell"]) for row in refs} == selected
    assert len(refs) == context["active_original_tangent_row_count"] == 74
    assert context["inactive_original_tangent_row_count"] == 126
    assert context["selected_floor_cell_count"] == 37 and context["inactive_floor_cell_count"] == 63

    for field, path in [
        ("selected_input_model_json_sha256", model_path),
        ("selected_floor_model_json_sha256", model_path),
        ("selected_input_deck_sha256", deck_path),
        ("selected_floor_deck_sha256", deck_path),
    ]:
        assert context[field] == sha(path)
    assert context["selected_input_model_json_path"] == str(model_path.relative_to(ROOT).as_posix())
    assert context["selected_floor_model_json_path"] == context["selected_input_model_json_path"]
    assert context["selected_input_deck_path"] == str(deck_path.relative_to(ROOT).as_posix())
    assert context["selected_floor_deck_path"] == context["selected_input_deck_path"]
    assert adapter_audit["case_id"] == "a12-forward"
    assert adapter_audit["input_only"] is True
    assert adapter_audit["native_solve_executed"] is False
    assert adapter_audit["source_response_forces_read"] is False
    assert adapter_audit["screen_packet"]["status"] == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
    assert set(adapter_audit["screen_packet"]["selected_cells"]) == selected
    assert any("No physical force adoption" in limit for limit in adapter_audit["limits"])
    assert adapter_audit["selected_rank"] == 74
    assert adapter_audit["source_preservation"]["physical_body_count"] == 50
    assert adapter_audit["source_preservation"]["source_cload_values_and_nodes_unchanged"] is True
    assert adapter_audit["source_preservation"]["source_geometry_elements_and_material_bindings_unchanged"] is True
    assert pins["case_id"] == "a12-forward"
    assert pins["adapter_script_sha256"] == sha(ROOT / pins["adapter_script_path"])
    assert pins["output_model_sha256"] == sha(model_path)
    assert pins["output_deck_sha256"] == sha(deck_path)
    assert pins["screen_stage"] == "selected-proposal"

    # This is still a preparation packet. Parent owns any future freeze and run.
    assert not (HERE / "freeze.json").exists()
    assert not (HERE / "execution.json").exists()
    assert not (HERE / "model.dat").exists()
    assert context["input_only"] is True and context["native_solve_executed"] is False
    assert context["mechanical_acceptance"] is False
    assert context["screen_positive_forces_or_active_states_reused_as_response"] is False

    result = {
        "schema": "current_springa_case_bound_context_check/v1",
        "status": "PASS_A12_FORWARD_CASE_CONTEXT_BINDING",
        "audit_script_path": str(Path(__file__).resolve().relative_to(ROOT).as_posix()),
        "audit_script_sha256": sha(Path(__file__).resolve()),
        "case_id": "a12-forward",
        "candidate": context["candidate"],
        "geometry_revision_id": context["geometry_revision_id"],
        "case_record_sha256_reproduced": context["case_record_sha256"],
        "control_model_sha256": sha(CONTROL / "model.json"),
        "control_deck_sha256": sha(CONTROL / "model.inp"),
        "register_sha256": sha(REGISTER),
        "screen_sha256": sha(SCREEN),
        "output_model_sha256": sha(model_path),
        "output_deck_sha256": sha(deck_path),
        "selected_proposed_cells": 37,
        "released_cells": 63,
        "active_tangent_rows": 74,
        "source_case_binding_exact": True,
        "screen_source_sha256_map_rehashed": True,
        "no_other_case_transfer": True,
        "no_force_or_demand_adoption": True,
        "input_only_no_freeze_or_native_run": True,
    }
    (HERE / "parent-case-context-check.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
