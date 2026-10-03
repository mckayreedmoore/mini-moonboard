"""Export fresh global force demands after the parent gravity/frame replay.

No force allocation, capacity calculation or historical local result is run.
The four internal reinforcement allocations remain separate frozen records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-response"
REGISTER = HERE / "rawlocal/working-joint-register/attempt03/register.json"
BASELINE = HERE / "frame-250-attempt02/comparison.json"
INTEGRATION = HERE / "rawlocal/knee-bridge-integration/attempt02/manifest.json"
PINS = {
    REGISTER: "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c",
    BASELINE: "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    INTEGRATION: "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
}


def require(condition, message):
    if not condition:
        raise ValueError(f"STOP: {message}")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def build(output, comparison_path, expected_comparison_sha256):
    output, comparison_path = Path(output).resolve(), Path(comparison_path).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate output child required")
    require(comparison_path.is_relative_to(ROOT), "comparison must be in repository")
    pins = {**PINS, Path(__file__).resolve(): sha(__file__), comparison_path: expected_comparison_sha256}

    def authenticate():
        for path, digest in pins.items():
            require(sha(path) == digest, f"source changed: {path}")

    authenticate()
    register, baseline, integration, comparison = [json.loads(p.read_text()) for p in (
        REGISTER, BASELINE, INTEGRATION, comparison_path)]
    require(not comparison["physical_release"] and not comparison["complete_joint_acceptance"], "unexpected release")
    require(comparison["source_climber_weight_lb"] == comparison["comparison_climber_weight_lb"] == 250
            and comparison["climber_load_scale"] == 1, "live-load scaling changed")
    require(comparison["comparison_horizontal_force_n"] == 300 and comparison["horizontal_load_scale"] == 1,
            "horizontal live load changed")
    cases = register["case_ids"]
    require(len(cases) == 6 and comparison["all_two_receiver_candidate_clearances"]
            and comparison["bounded_nonunique_seating_reported"], "frame method changed")
    require([(s["gap_scale"], s["case_id"]) for s in comparison["states"]]
            == [(gap, case) for gap in (0.0, 1.0) for case in cases], "twelve-state coverage differs")
    require(all(s["status"].startswith("PASS_CONDITIONAL_") for s in comparison["states"]), "incomplete frame response")
    require(comparison["panel_screw_stiffness_n_per_mm"]["lateral_components"]
            == baseline["panel_screw_stiffness_n_per_mm"]["lateral_components"]
            and comparison["panel_screw_stiffness_n_per_mm"]["withdrawal"]
            == baseline["panel_screw_stiffness_n_per_mm"]["withdrawal"], "screw laws changed")
    frame_path = ROOT / comparison["frame_operator_directory"]
    assessment_path = frame_path / "operator-assessment.json"
    require(str(assessment_path.relative_to(ROOT)) in comparison["source_sha256"], "frame does not bind assessment")
    pins[assessment_path] = comparison["source_sha256"][str(assessment_path.relative_to(ROOT))]
    authenticate()
    assessment = json.loads(assessment_path.read_text())
    require(assessment["modeled_mass_kg"] == comparison["modeled_mass_kg"], "gravity mass differs")
    rows_path = frame_path / "row-identities.json"
    pins[rows_path] = assessment["output_sha256"]["row-identities.json"]
    for record, path in ((baseline, BASELINE), (comparison, comparison_path)):
        pins[path.with_name("response.npz")] = record["response_sha256"]
    authenticate()
    rows = json.loads(rows_path.read_text())
    require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)), "row census differs")
    require(len(register["axes"]) == 104 and len(register["panel_kicker_screws"]) == 66, "axis census differs")
    records, frame_deltas = [], []
    with np.load(BASELINE.with_name("response.npz"), allow_pickle=False) as old, np.load(
            comparison_path.with_name("response.npz"), allow_pickle=False) as new:
        for case in cases:
            key = case + "_gap_raw_force_n"
            first, fresh = old[key], new[key]
            require(first.shape == fresh.shape == (1888,) and np.isfinite(fresh).all(), "invalid force field")
            delta = fresh - first
            governing = int(np.argmax(np.abs(delta)))
            frame_deltas.append({"case_id": case, "max_absolute_row_delta_n": float(abs(delta[governing])),
                                 "row": governing, "row_id": rows[governing]["row_id"],
                                 "original_n": float(first[governing]), "fresh_n": float(fresh[governing])})
            for kind, axes in (("structural_bolt", register["axes"]),
                               ("Hillman_panel_kicker_screw", register["panel_kicker_screws"])):
                for axis in axes:
                    tie = axis["outer_tie"]
                    require(rows[tie["row"]]["row_id"] == tie["row_id"], "tie identity differs")
                    interfaces = []
                    for interface in axis["interfaces"]:
                        indices = interface["component_rows"]
                        require(all(rows[i]["row_id"] == interface["plane_id"] for i in indices), "plane identity differs")
                        values = [float(fresh[i]) for i in indices]
                        interfaces.append({"plane_id": interface["plane_id"], "component_rows": indices,
                                           "components_n": values, "lateral_n": math.hypot(*values),
                                           "component_directions_xyz": interface["component_directions_xyz"]})
                    records.append({"case_id": case, "axis_id": axis["axis_id"], "kind": kind,
                                    "receivers": axis["receivers"], "signed_axial_n": float(fresh[tie["row"]]),
                                    "old_global_signed_axial_n": float(first[tie["row"]]),
                                    "interfaces": interfaces,
                                    "peak_interface_lateral_n": max(i["lateral_n"] for i in interfaces),
                                    "force_scope": "Fresh global allocation; historical local reallocation/capacity not transferred."})
    bolts = [r for r in records if r["kind"] == "structural_bolt"]
    screws = [r for r in records if r["kind"] == "Hillman_panel_kicker_screw"]
    require(len(bolts) == 624 and len(screws) == 396, "nominal record census differs")
    require(len({(r["case_id"], r["axis_id"]) for r in records}) == 1020, "duplicate state")
    peak_t = max(screws, key=lambda r: r["signed_axial_n"])
    peak_v = max(screws, key=lambda r: r["peak_interface_lateral_n"])
    compact = lambda r: {k: r[k] for k in (
        "case_id", "axis_id", "signed_axial_n", "peak_interface_lateral_n", "old_global_signed_axial_n")}
    summary = {"schema": "knee-bridge-fresh-global-force-census/v1", "status": "FRESH_GLOBAL_DEMANDS_EXPORTED",
               "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
               "source_comparison_sha256": expected_comparison_sha256,
               "census": {"nominal_cases": 6, "global_structural_bolt_states": 624, "screw_states": 396,
                          "new_internal_allocations_separate": 24, "proposal_bolts": 108},
               "fresh_modeled_mass_kg": comparison["modeled_mass_kg"], "dead_load_factor": comparison["dead_load_factor"],
               "frame_deltas": frame_deltas, "peak_screw_axial_same_state": compact(peak_t),
               "peak_screw_lateral_same_state": compact(peak_v),
               "internal_allocations_reference": integration["proposed_internal_allocations"],
               "internal_allocations_source_directory": str(INTEGRATION.parent.relative_to(ROOT)),
               "internal_allocations_recomputed_for_changed_gravity": False,
               "historical_local_or_component_acceptance_transferred": False,
               "actual_changed_hole_stiffness_qualified": False, "proposal_adopted": False,
               "complete_joint_acceptance": False, "physical_release": False}
    authenticate()
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    with (output / "global-demands.jsonl").open("w") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
    dump(output / "summary.json", summary)
    names = (".gitignore", "producer.py.snapshot", "global-demands.jsonl", "summary.json")
    dump(output / "receipt.json", {"source_sha256": summary["source_sha256"],
                                   "output_sha256": {n: sha(output / n) for n in names},
                                   "physical_release": False, "proposal_adopted": False})
    authenticate()
    return {"status": summary["status"], "census": summary["census"],
            "summary_sha256": sha(output / "summary.json"), "receipt_sha256": sha(output / "receipt.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--comparison-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.comparison, args.comparison_sha256), allow_nan=False))
