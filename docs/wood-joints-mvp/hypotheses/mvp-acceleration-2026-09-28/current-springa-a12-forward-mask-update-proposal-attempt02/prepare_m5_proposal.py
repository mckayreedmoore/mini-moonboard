"""Prepare one source-bound M5 input from the stable strict-positive M4 mask."""
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
RUN = BASE / "current-springa-selected-floor-a12-forward-attempt04"
DIAG_PACKET = BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt03"
DIAG = DIAG_PACKET / "diagnosis.json"
DIAG_PINS = DIAG_PACKET / "source-pins.json"
DIAG_PRODUCER = DIAG_PACKET / "produce.py"
M4_PACKET = BASE / "current-springa-a12-forward-mask-update-proposal-attempt01"
M4_SCREEN = M4_PACKET / "screen.json"
M4_PREPARED = M4_PACKET / "a12-forward"
CONTROL = BASE / "current-springa-frame-a12-forward-all-bearing-attempt01"
REGISTER = BASE / "current-six-case-source-load-register-attempt01/register.json"
FRESH = BASE / "current-springa-six-case-frame-input-adapter-attempt01/a12-forward/model.json"
ADAPTER = BASE / "current-springa-case-bound-floor-input-adapter-attempt02/prepare.py"
PRIOR_ADAPTER_PINS = BASE / "current-springa-case-bound-floor-input-adapter-attempt10/a12-forward/source-pins.json"
SCREEN = HERE / "screen.json"
OUT = HERE / "a12-forward"

EXPECTED = {
    "diagnosis": "888e64e575c49e3169d55007d691e823701ad4b364e500cb3db945c8a9b2ab39",
    "diagnosis_producer": "8f4d94333d1fd8e1b3f2b3e3d4046f5d6d1056e106724f2ec73a6eedc5493d3a",
    "diagnosis_pins": "9b71fd61e57afde69882a6baabd7dce449bd0714cb0c694ca3049375e63fe1bc",
    "m4_model": "d61113db83e94443dfd4a2129793cf6c5f97511ea4c130f29e9b09e0d0f75dc6",
    "m4_deck": "394653fbe1aa0d6ad5d36f66f19eabf6ddd45fef072466ec828d044aa3cf67e1",
    "m4_screen": "722e0f50f88ba5f9f4ce4baf2840031fe5c48c0cd9abc55b13aa4c006cd7c61a",
    "m4_gate": "46f58fe6fe6464c8ee96b6b232f2b5554300e3f40762cd3ed0c5a898f5f6f2ca",
    "m4_source_pins": "090658c1be2f408cdd883d6c0d19f95c19c688a0115ba8a54879ad695c6c0cdc",
    "adapter": "1e9edd6d8d1a341c3cd70854710dd80431438f7287e425b1c3e62d94d0f963bc",
    "register": "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508",
    "control_model": "ed7c43075f11160b12c081c262baa084f100b0087a812ca0d70e6ea14fe096b5",
    "control_deck": "1440e72c7f224092f19520285cf05bea97fc9b93411ea2be3fee9f8f73314479",
    "fresh_case_model": "10f37a9f8a80ee8427c95e4c8acfc7b123ddd621bd68d0493370535fdfcb8a0b",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def add_pin(pins: dict[str, str], path: Path) -> None:
    key = rel(path)
    value = sha(path)
    if key in pins and pins[key] != value:
        raise RuntimeError(f"Conflicting source pin for {key}")
    pins[key] = value


def main() -> None:
    if OUT.exists() or SCREEN.exists():
        raise RuntimeError("Refusing to overwrite a prepared M5 proposal")
    diag = read(DIAG)
    for path, expected in (
        (DIAG, EXPECTED["diagnosis"]),
        (DIAG_PRODUCER, EXPECTED["diagnosis_producer"]),
        (DIAG_PINS, EXPECTED["diagnosis_pins"]),
        (M4_PREPARED / "model.json", EXPECTED["m4_model"]),
        (M4_PREPARED / "model.inp", EXPECTED["m4_deck"]),
        (M4_SCREEN, EXPECTED["m4_screen"]),
        (M4_PACKET / "input-gate.json", EXPECTED["m4_gate"]),
        (M4_PACKET / "input-gate-source-pins.json", EXPECTED["m4_source_pins"]),
        (ADAPTER, EXPECTED["adapter"]),
        (REGISTER, EXPECTED["register"]),
        (CONTROL / "model.json", EXPECTED["control_model"]),
        (CONTROL / "model.inp", EXPECTED["control_deck"]),
        (FRESH, EXPECTED["fresh_case_model"]),
    ):
        if sha(path) != expected:
            raise RuntimeError(f"Pinned M4 source changed: {path}")
    if (diag.get("schema") != "current_springa_a12_forward_attempt04_floor_mask_recurrence_diagnosis/v1"
            or diag.get("native_run_id") != "springa-selected-a12-forward-attempt04"
            or diag.get("parent_response_gate_exception") != "Selected floor normal is not strictly positive after rounding: SPR1068"
            or diag.get("corner_demands_usable") is not False
            or diag.get("physical_force_adoption") is not False):
        raise RuntimeError("M4 diagnosis is not the pinned rejected, non-demand diagnostic")
    if (diag.get("state_positive_set_constant_across_seven_states") is not True
            or diag.get("strict_positive_count_by_state") != [34] * 7
            or diag.get("strict_separated_count_by_state") != [66] * 7
            or diag.get("ambiguous_or_noncomplementary_count_by_state") != [0] * 7):
        raise RuntimeError("M4 positive classification is not the exact stable 34/66/0 pattern")
    if any(summary.get("exact_match_at_any_printed_state") for summary in diag["input_mask_comparison_summary"].values()):
        raise RuntimeError("The M4 output mask matches a prior M1-M4 input; no new proposal is justified")

    observed_masks = [set(state["observed_positive_cells_diagnostic_only"]) for state in diag["history"]]
    if len(observed_masks) != 7 or any(mask != observed_masks[0] for mask in observed_masks[1:]):
        raise RuntimeError("M4 output-positive set is not identical at all seven printed states")
    proposed = observed_masks[0]
    m4_input = set(diag["input_masks_M1_to_M4"]["M4_attempt04_input_37"]["cells"])
    removed = sorted(m4_input - proposed)
    added = sorted(proposed - m4_input)
    if (len(proposed) != 34 or len(removed) != 3 or added
            or set(removed) != {
                "floor_base_floor_left_15", "floor_base_floor_left_17", "floor_base_post_outer_left_1"
            }):
        raise RuntimeError("M5 mask is not the exact 34-cell strict-positive set from M4")

    control = read(CONTROL / "model.json")
    normals = {
        binding["name"]: binding for binding in control["unilateral_springa_bindings"]
        if binding.get("physical_owner", {}).get("role") == "floor_normal"
    }
    if len(normals) != 100:
        raise RuntimeError("A12-forward all-bearing source no longer has 100 normal carriers")

    screen_states = []
    for state in diag["history"]:
        rows = []
        for row in state["rows"]:
            cell = row["cell_name"]
            positive = row["classification"] == "STRICTLY_POSITIVE"
            separated = row["classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"
            ambiguous = row["classification"] == "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"
            if (positive, separated, ambiguous).count(True) != 1:
                raise RuntimeError(f"Noncomplementary interval state for {cell}")
            rows.append({
                "cell_name": cell,
                "source_group": row["source_group"],
                "source_row_id": row["source_row_id"],
                "physical_owner": normals[cell]["physical_owner"],
                "strictly_positive_after_rounding": positive,
                "strictly_separating_after_rounding": separated,
                "q_interval_mm": row["q_interval_mm"],
                "geometric_elongation_interval_mm": row["geometric_elongation_interval_mm"],
            })
        screen_states.append({
            "load_factor": float(state["load_factor"]),
            "bearing_count": 34,
            "separating_count": 66,
            "ambiguous_or_noncomplementary_count": 0,
            "rows": rows,
        })

    # The old M4 diagnostic screen contains the direct A12-forward controls,
    # register, and input/source proof pins. Extend that verified closure with
    # the exact M4 DAT classification and this explicit proposal producer.
    source_hashes: dict[str, str] = dict(read(M4_SCREEN)["source_sha256"])
    for source, expected in diag["source_sha256"].items():
        if sha(ROOT / source) != expected:
            raise RuntimeError(f"M4 diagnostic source closure changed: {source}")
        add_pin(source_hashes, ROOT / source)
    for path in (
        DIAG, DIAG_PINS, DIAG_PRODUCER, M4_SCREEN, M4_PREPARED / "model.json",
        M4_PREPARED / "model.inp", M4_PREPARED / "audit.json", M4_PACKET / "proposal.json",
        M4_PACKET / "input-gate.json", M4_PACKET / "input-gate-source-pins.json",
        RUN / "model.json", RUN / "model.inp", RUN / "model.dat", RUN / "freeze.json",
        RUN / "execution.json", RUN / "case-context.json", RUN / "parent-response-rejection.json",
        RUN / "parent-terminal-assessment.json", ADAPTER, REGISTER, CONTROL / "model.json",
        CONTROL / "model.inp", FRESH, Path(__file__).resolve(),
    ):
        add_pin(source_hashes, path)
    for path, expected in source_hashes.items():
        if sha(ROOT / path) != expected:
            raise RuntimeError(f"M5 source closure changed: {path}")

    screen = {
        "schema": "current_case_bound_floor_diagnostic_screen/v1",
        "status": "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH",
        "case_id": "a12-forward",
        "candidate": control["candidate"],
        "geometry_revision_id": control["geometry_revision_id"],
        "source_stage": "zero-U 711-token strict normal interval classification of rejected M4 DAT",
        "source_native_run_id": diag["native_run_id"],
        "source_native_run_directory": rel(RUN),
        "source_selected_model_sha256": sha(RUN / "model.json"),
        "source_selected_deck_sha256": sha(RUN / "model.inp"),
        "source_selected_DAT_sha256": sha(RUN / "model.dat"),
        "all_printed_times": list(map(float, diag["all_printed_load_factors"])),
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
        "proposed_mask_basis": "the 34 cells strictly positive at all seven printed states in the rejected M4 DAT, using the unchanged pinned 711 zero-U interval method",
        "selected_cells_changed_from_m4_input": {"removed": removed, "added": added},
        "input_mask_comparison": {
            name: {
                "input_cell_count": summary["cell_count"],
                "mask_sha256": summary["mask_sha256"],
                "exact_match_at_any_printed_state": False,
            }
            for name, summary in diag["input_masks_M1_to_M4"].items()
        } | {
            "proposed_m5_34_cell_mask_sha256": hashlib.sha256(("\n".join(sorted(proposed)) + "\n").encode()).hexdigest(),
        },
        "diagnostic_positive_cells_at_final_time": sorted(proposed),
        "diagnostic_separating_cells_at_final_time": sorted(set(normals) - proposed),
        "states": screen_states,
        "source_sha256": dict(sorted(source_hashes.items())),
        "limits": [
            "This is one input-only M5 proposal from the exact M4 strict-positive set; it is not an accepted floor state or response.",
            "M4 was rejected because three M4-selected normals are strictly separated; M4 DAT forces and reactions are not adopted.",
            "All 100 normal laws remain unchanged; this proposal changes only the selected floor tangential constraint rows.",
            "No automatic mask iteration, native launch, freeze, force adoption, floor qualification, or mechanical acceptance follows.",
        ],
    }
    SCREEN.write_text(json.dumps(screen, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

    prior_pins = read(PRIOR_ADAPTER_PINS)
    input_pins = {path: row["sha256"] for path, row in prior_pins["input_pins"].items()}
    input_pins[rel(SCREEN)] = sha(SCREEN)
    input_pins.pop(rel(BASE / "current-springa-case-bound-floor-input-adapter-attempt10/screen.json"), None)
    spec = importlib.util.spec_from_file_location("case_bound_selected_floor_input_adapter_m5", ADAPTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import pinned case-bound selected-floor input adapter")
    adapter = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = adapter
    spec.loader.exec_module(adapter)
    audit = adapter.prepare({
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
    })
    output_model = read(OUT / "model.json")
    if (set(output_model["floor_selected_bearing_cells"]) != proposed
            or len(output_model["floor_reference_nodes_and_load_map"]) != 68
            or audit.get("status") != "PASS_SELECTED_FLOOR_INPUT_ALGEBRA_AND_SOURCE_PRESERVATION"):
        raise RuntimeError("Prepared M5 model differs from the exact source-derived 34-cell proposal")
    proposal = {
        "schema": "current_springa_a12_forward_mask_update_proposal/v1",
        "status": "PASS_INPUT_ONLY_SOURCE_BOUND_MASK_PROPOSAL",
        "case_id": "a12-forward",
        "candidate": output_model["candidate"],
        "geometry_revision_id": output_model["geometry_revision_id"],
        "source_diagnosis_path": rel(DIAG),
        "source_diagnosis_sha256": sha(DIAG),
        "source_run_path": rel(RUN),
        "source_run_model_sha256": sha(RUN / "model.json"),
        "source_run_deck_sha256": sha(RUN / "model.inp"),
        "source_run_DAT_sha256": sha(RUN / "model.dat"),
        "source_response_rejection": read(RUN / "parent-response-rejection.json")["reason"],
        "proposal_input_mask": sorted(proposed),
        "proposal_cell_count": len(proposed),
        "active_floor_tangent_rows": 68,
        "changed_cells_vs_m4_input": {"removed": removed, "added": added},
        "screen_sha256": sha(SCREEN),
        "prepared_model_sha256": sha(OUT / "model.json"),
        "prepared_deck_sha256": sha(OUT / "model.inp"),
        "input_audit_status": audit["status"],
        "screen_classification_is_not_response_for_proposal": True,
        "native_solve_executed": False,
        "freeze_created": False,
        "corner_demands_usable": False,
        "physical_force_adoption": False,
        "mechanical_acceptance": False,
        "parent_native_readiness": False,
    }
    (HERE / "proposal.json").write_text(json.dumps(proposal, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(proposal, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
