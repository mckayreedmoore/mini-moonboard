"""Prepare one source-bound A12-forward mask proposal; never launch CalculiX."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
RUN = BASE / "current-springa-selected-floor-a12-forward-attempt03"
DIAG_PACKET = BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02"
DIAG = DIAG_PACKET / "diagnosis.json"
DIAG_PINS = DIAG_PACKET / "source-pins.json"
DIAG_PRODUCER = DIAG_PACKET / "produce.py"
CONTROL = BASE / "current-springa-frame-a12-forward-all-bearing-attempt01"
REGISTER = BASE / "current-six-case-source-load-register-attempt01/register.json"
FRESH = BASE / "current-springa-six-case-frame-input-adapter-attempt01/a12-forward/model.json"
ADAPTER = BASE / "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py"
PRIOR_ADAPTER_PINS = BASE / "current-springa-case-bound-floor-input-adapter-attempt10/a12-forward/source-pins.json"
SCREEN = HERE / "screen.json"
OUT = HERE / "a12-forward"

PINS = {
    "diagnosis": "03d77cde6c1ca73f32fe7036cdf462df60de5fd929207f585d594fbacafb9194",
    "run_model": "4f7d3f0a70a534a1c38cd0ce6e48990eb7b098dc82dc5fc2f412ff34eca3ff0f",
    "run_deck": "c9d926bd31b970f33f49dc6edf3627244a75d246124a5fef3e393b058bfa5aa4",
    "run_dat": "de70b9661f9aa9368da3fa2aa9e0559b5d76835e686a44abe194a82a9073acf4",
    "attempt03_mask_model": "4f7d3f0a70a534a1c38cd0ce6e48990eb7b098dc82dc5fc2f412ff34eca3ff0f",
    "all_bearing_model": "ed7c43075f11160b12c081c262baa084f100b0087a812ca0d70e6ea14fe096b5",
    "all_bearing_deck": "1440e72c7f224092f19520285cf05bea97fc9b93411ea2be3fee9f8f73314479",
    "all_bearing_dat": "c90aa23a34ad6c06af23707fe4c5ab6e493d64e0f74310e40e1b841920b86d54",
    "all_bearing_execution": "f72c2ce060bd10551d15f5cf6355e28d529f05eb2f8fce4182453b6defd5abdc",
    "register": "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508",
    "fresh_case_model": "10f37a9f8a80ee8427c95e4c8acfc7b123ddd621bd68d0493370535fdfcb8a0b",
    "adapter": "1e9edd6d8d1a341c3cd70854710dd80431438f7287e425b1c3e62d94d0f963bc",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    if OUT.exists():
        raise RuntimeError(f"Refusing to overwrite prepared input: {OUT}")
    diag = read(DIAG)
    assert sha(DIAG) == PINS["diagnosis"]
    assert diag["schema"] == "current_springa_a12_forward_attempt03_floor_recurrence_diagnosis/v1"
    assert diag["status"] == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH_DIAGNOSTIC_ONLY"
    assert diag["native_run_id"] == "springa-selected-a12-forward-attempt03"
    assert diag["case_id"] == "a12-forward"
    assert diag["full_step_native_convergence"] is True
    assert diag["all_100_floor_normal_laws_checked_at_every_printed_state"] is True
    assert diag["corner_demands_usable"] is False
    assert diag["physical_force_adoption"] is False
    assert diag["response_force_exported"] is False
    assert diag["numeric_spring_force_or_reference_rf_values_written"] is False
    assert diag["mechanical_acceptance"] is False
    assert diag["input_selected_cell_count"] == 37
    assert diag["strict_positive_count_at_every_state"] == 37
    assert diag["strict_positive_pattern_constant_across_seven_states"] is True

    run_assessment = read(RUN / "parent-terminal-assessment.json")
    run_freeze = read(RUN / "freeze.json")
    run_context = read(RUN / "case-context.json")
    run_model = read(RUN / "model.json")
    assert run_assessment["status"] == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"
    assert run_assessment["corner_demands_usable"] is False
    assert run_assessment["mechanical_acceptance"] is False
    assert run_freeze["files_sha256"]["model.json"] == PINS["run_model"]
    assert run_freeze["files_sha256"]["model.inp"] == PINS["run_deck"]
    assert run_context["case_id"] == "a12-forward"
    attempt03_mask = set(run_model["floor_branch_metadata"]["selected_cells"])

    # Re-derive the one proposed mask directly from every printed state. No force,
    # RF, or historical spring value participates in this input projection.
    states: list[dict[str, Any]] = []
    positive_masks: list[set[str]] = []
    for state in diag["history"]:
        rows = state["rows"]
        positive = {r["cell_name"] for r in rows if r["zero_u_711_classification"] == "STRICTLY_POSITIVE"}
        separated = {r["cell_name"] for r in rows if r["zero_u_711_classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"}
        if len(rows) != 100 or positive & separated or positive | separated != {r["cell_name"] for r in rows}:
            raise RuntimeError("Attempt03 diagnostic classifications do not partition the exact 100 floor cells")
        if len(positive) != 37 or len(separated) != 63:
            raise RuntimeError("Attempt03 printed state did not classify 37 positive / 63 separated")
        positive_masks.append(positive)
    if any(mask != positive_masks[0] for mask in positive_masks[1:]):
        raise RuntimeError("Stable output-positive set changes across the seven states")
    proposed = positive_masks[0]
    if proposed == attempt03_mask or len(proposed ^ attempt03_mask) != 6:
        raise RuntimeError("Expected a distinct, explicitly derived next mask from attempt03 output")
    lost = sorted(attempt03_mask - proposed)
    gained = sorted(proposed - attempt03_mask)
    expected_lost = {
        "floor_base_floor_left_9", "floor_base_floor_left_11", "floor_base_floor_left_13",
    }
    expected_gained = {
        "floor_base_floor_left_15", "floor_base_floor_left_17", "floor_base_post_outer_left_1",
    }
    if set(lost) != expected_lost or set(gained) != expected_gained:
        raise RuntimeError("Attempt03 mask update differs from the reviewed six-cell change")

    control_model = read(CONTROL / "model.json")
    normals = {
        b["name"]: b for b in control_model["unilateral_springa_bindings"]
        if b.get("physical_owner", {}).get("role") == "floor_normal"
    }
    if len(normals) != 100:
        raise RuntimeError("All-bearing source model no longer contains exactly 100 normal carriers")
    for source, expected in (
        (RUN / "model.json", PINS["run_model"]),
        (RUN / "model.inp", PINS["run_deck"]),
        (RUN / "model.dat", PINS["run_dat"]),
        (CONTROL / "model.json", PINS["all_bearing_model"]),
        (CONTROL / "model.inp", PINS["all_bearing_deck"]),
        (CONTROL / "model.dat", PINS["all_bearing_dat"]),
        (CONTROL / "execution.json", PINS["all_bearing_execution"]),
        (REGISTER, PINS["register"]),
        (FRESH, PINS["fresh_case_model"]),
        (ADAPTER, PINS["adapter"]),
    ):
        if sha(source) != expected:
            raise RuntimeError(f"Pinned source changed: {source}")

    source_hashes = {}
    for source, expected in diag["source_sha256"].items():
        path = Path(source)
        if path.is_absolute():
            path = path.resolve().relative_to(ROOT.resolve())
        source_hashes[path.as_posix()] = expected
    for path in (DIAG, DIAG_PINS, DIAG_PRODUCER, Path(__file__).resolve()):
        source_hashes[rel(path)] = sha(path)
    for source, expected in source_hashes.items():
        if sha(ROOT / source) != expected:
            raise RuntimeError(f"Attempt03 diagnosis source closure changed: {source}")

    screen_states = []
    for state in diag["history"]:
        out_rows = []
        for row in state["rows"]:
            cell = row["cell_name"]
            is_positive = row["zero_u_711_classification"] == "STRICTLY_POSITIVE"
            binding = normals[cell]
            out_rows.append({
                "cell_name": cell,
                "source_group": row["source_group"],
                "source_row_id": row["source_row_id"],
                "physical_owner": binding["physical_owner"],
                "strictly_positive_after_rounding": is_positive,
                "strictly_separating_after_rounding": not is_positive,
                "q_interval_mm": row["q_interval_mm"],
                "geometric_elongation_interval_mm": row["geometric_elongation_interval_mm"],
            })
        screen_states.append({
            "load_factor": float(state["load_factor"]),
            "bearing_count": 37,
            "separating_count": 63,
            "ambiguous_or_noncomplementary_count": 0,
            "rows": out_rows,
        })

    screen = {
        "schema": "current_case_bound_floor_diagnostic_screen/v1",
        "status": "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH",
        "case_id": "a12-forward",
        "candidate": control_model["candidate"],
        "geometry_revision_id": control_model["geometry_revision_id"],
        "source_stage": "strict printed-token interval classifications from rejected attempt03 input response",
        "source_native_run_id": diag["native_run_id"],
        "source_native_run_directory": rel(RUN),
        "source_selected_model_sha256": PINS["run_model"],
        "source_selected_deck_sha256": PINS["run_deck"],
        "source_selected_DAT_sha256": PINS["run_dat"],
        "all_printed_times": [float(x) for x in diag["all_printed_load_factors"]],
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
        "proposed_mask_basis": "exactly the 37 cells strictly positive at every one of seven printed states in rejected attempt03, using its pinned 711 zero-U token interval classification",
        "selected_cells_changed_from_attempt03_input": {"removed": lost, "added": gained},
        "input_mask_comparison": {
            "attempt01_35_cell_mask_sha256": "f523b17b5f0fcfd0df82bbf2d11ef655ef4b5493194119c3144ae0b091ff729f",
            "attempt02_31_cell_mask_sha256": "dde1b78845fde59ebea1ed1dfe889cce4b55d213c2aa1e8410c4c32abeed2939",
            "attempt03_37_cell_mask_sha256": "4153abdfc759307f024a0fc2736ccd828da95ee3528c0b86646912654c8d7e72",
            "proposed_attempt04_37_cell_mask_sha256": hashlib.sha256(("\n".join(sorted(proposed)) + "\n").encode()).hexdigest(),
        },
        "diagnostic_positive_cells_at_final_time": sorted(proposed),
        "diagnostic_separating_cells_at_final_time": sorted(set(normals) - proposed),
        "states": screen_states,
        "source_sha256": dict(sorted(source_hashes.items())),
        "limits": [
            "This is one explicit proposed input mask, not an accepted floor state or response.",
            "Attempt03 used the different 37-cell attempt03 input; its output-positive set is not a response for this proposal.",
            "No spring force, reference reaction, support force, or corner demand is copied from the rejected run.",
            "No automatic mask iteration, native launch, freeze, floor qualification, or mechanical acceptance follows from this proposal.",
        ],
    }
    SCREEN.write_text(json.dumps(screen, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

    prior_pins = read(PRIOR_ADAPTER_PINS)
    common_and_dynamic = prior_pins["input_pins"]
    input_pins = {path: row["sha256"] for path, row in common_and_dynamic.items()}
    input_pins[rel(SCREEN)] = sha(SCREEN)
    input_pins.pop(rel(BASE / "current-springa-case-bound-floor-input-adapter-attempt10/screen.json"), None)

    spec = importlib.util.spec_from_file_location("case_bound_selected_floor_input_adapter", ADAPTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import pinned selected-floor input adapter")
    adapter = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = adapter
    spec.loader.exec_module(adapter)
    cfg = {
        "root": ROOT,
        "case_id": "a12-forward",
        "control_dir": CONTROL,
        "screen_path": SCREEN,
        "register_path": REGISTER,
        "fresh_model_path": FRESH,
        "output_dir": OUT,
        "packet_dir": HERE,
        "diagnostic_stage": "selected-proposal",
        "expected_screen_status": "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH",
        "expected_hashes": input_pins,
    }
    audit = adapter.prepare(cfg)
    output_model = read(OUT / "model.json")
    if (set(output_model["floor_selected_bearing_cells"]) != proposed
            or len(output_model["floor_reference_nodes_and_load_map"]) != 74
            or audit.get("status") != "PASS_SELECTED_FLOOR_INPUT_ALGEBRA_AND_SOURCE_PRESERVATION"):
        raise RuntimeError("Prepared input differs from the exact source-derived M4 proposal")
    result = {
        "schema": "current_springa_a12_forward_mask_update_proposal/v1",
        "status": "PASS_INPUT_ONLY_SOURCE_BOUND_MASK_PROPOSAL",
        "case_id": "a12-forward",
        "candidate": output_model["candidate"],
        "geometry_revision_id": output_model["geometry_revision_id"],
        "source_diagnosis_path": rel(DIAG),
        "source_diagnosis_sha256": sha(DIAG),
        "source_run_path": rel(RUN),
        "source_run_model_sha256": PINS["run_model"],
        "source_run_deck_sha256": PINS["run_deck"],
        "source_run_dat_sha256": PINS["run_dat"],
        "proposal_input_mask": sorted(proposed),
        "proposal_cell_count": len(proposed),
        "active_floor_tangent_rows": 74,
        "changed_cells_vs_attempt03_input": {"removed": lost, "added": gained},
        "screen_sha256": sha(SCREEN),
        "prepared_model_sha256": sha(OUT / "model.json"),
        "prepared_deck_sha256": sha(OUT / "model.inp"),
        "input_audit_status": audit["status"],
        "screened_classification_is_not_response_for_proposal": True,
        "native_solve_executed": False,
        "freeze_created": False,
        "corner_demands_usable": False,
        "physical_force_adoption": False,
        "mechanical_acceptance": False,
        "parent_native_readiness": False,
    }
    (HERE / "proposal.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
