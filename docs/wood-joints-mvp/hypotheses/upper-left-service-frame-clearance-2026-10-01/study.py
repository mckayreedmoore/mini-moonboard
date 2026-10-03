#!/usr/bin/env python3
"""Finite 252-state comparison; new outputs only, never mutate source packets."""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from check_frame import ROOT, Frame, clearance_offsets, maxabs, sha


def known_answer():
    f0 = np.array([5., 0., 0., 1., 0., 0., 3., 4.])
    response = 2 * np.eye(8)
    h, audit = clearance_offsets(f0, response, 1.15)
    expected_h = np.array([1.15, 0., 0., .5, 0., 0., .69, .92])
    expected_f = np.array([2.7, 0., 0., 0., 0., 0., 1.62, 2.16])
    error = max(maxabs(h - expected_h), maxabs(f0 - response @ h - expected_f))
    if error > 1e-8:
        raise ValueError(f"circular gap known answer failed: {error}")
    return {"two_engaged_pairs_two_free_pairs": True, "maximum_answer_error": error, **audit}


def produce():
    frame = Frame()
    answer = known_answer()
    rigidity = 200000 * math.pi * 6.35**4 / 64
    stiffnesses = [("frozen source", None)] + [
        (f"hypothetical timber E={E} MPa", rigidity * (E / (4 * rigidity))**.75)
        for E in (150, 300, 600)]
    states, summary, baseline_audits = [], [], []
    arrays = []
    for label, stiffness in stiffnesses:
        for clearance in (0., .5, 1.15):
            selected = []
            for case in sorted(frame.sources):
                for increment in range(7):
                    report, values = frame.evaluate(case, increment, 2., clearance, stiffness)
                    report["scenario_id"] = f"{label}; clearance={clearance} mm"
                    selected.append(report)
                    states.append(report)
                    arrays.append(values)
                    if stiffness is None and clearance == 0:
                        baseline_audits.append({"case": case, "increment": increment,
                                                "force_difference_n": report["zero_clearance_native_force_max_difference_n"],
                                                "q_difference_mm": report["zero_clearance_native_q_max_difference_mm"]})
            summary.append({
                "scenario": label, "clearance_mm": clearance, "lateral_k_n_per_mm": stiffness,
                "saved_states": len(selected),
                "floor_consistent_states": sum(r["audit"]["floor_branch_consistent"] for r in selected),
                "target_bolt_peak_shear_n": max(b["shear_n"] for r in selected for b in r["target_bolts"]),
                "target_bolt_peak_tension_n": max(max(r["target_axial_tension_n"]) for r in selected),
                "target_bolt_peak_slip_mm": max(b["slip_mm"] for r in selected for b in r["target_bolts"]),
                "rail_side_rigid_component_peak_movement_mm": max(r["rail_relative_to_side_movement_mm"] for r in selected),
                "rail_side_rigid_component_peak_rotation_deg": max(r["rail_relative_to_side_rotation_deg"] for r in selected),
                "max_contact_branch_solves": max(len(r["normal_branch_iterations"]) for r in selected),
                "local_fit_rail_side_peak_movement_mm": max(r["local_fit_rail_side_movement_mm"] for r in selected),
                "local_fit_rail_side_peak_rotation_deg": max(r["local_fit_rail_side_rotation_deg"] for r in selected),
                "local_fit_maximum_projection_residual_mm": max(f["maximum_nonrigid_projection_residual_mm"] for r in selected for f in r["local_interface_projection_fits"].values()),
            })
            print(json.dumps(summary[-1]), file=sys.stderr, flush=True)
    if any(r["force_difference_n"] > .002 or r["q_difference_mm"] > 1e-4 for r in baseline_audits):
        raise ValueError(f"practical source baseline comparison failed: {baseline_audits}")
    baseline = {(r["case"], r["increment"]): i for i, r in enumerate(states)
                if r["clearance_mm"] == 0 and r["lateral_stiffness_n_per_mm"] == "frozen source"}
    joint_bodies = {"left_service_outer_upper_cleat", "base_rail_service_upper_left", "base_side_left"}
    outside = np.array([i for i, row in enumerate(frame.rows[:1640])
                        if not {row["ownership"]["first_body"], row["ownership"]["second_body"]}.issubset(joint_bodies)])
    # Demand redistribution is a scalar connector-force comparison. It does
    # not convert any source spring force into an adopted joint capacity.
    for i, r in enumerate(states):
        j = baseline[(r["case"], r["increment"])]
        difference = arrays[i]["f"] - arrays[j]["f"]
        worst = int(outside[np.argmax(np.abs(difference[outside]))])
        r["largest_other_spring_force_change"] = {
            "row": worst, "identity": frame.rows[worst],
            "baseline_force_n": float(arrays[j]["f"][worst]),
            "new_force_n": float(arrays[i]["f"][worst]),
            "signed_change_n": float(difference[worst]),
        }
        r["rigid_host_movement_change_from_source_mm"] = float(np.linalg.norm(
            np.array(r["rail_relative_to_side_at_common_datum_mm"])
            - np.array(states[j]["rail_relative_to_side_at_common_datum_mm"])))
        r["rigid_host_rotation_change_from_source_deg"] = float(np.linalg.norm(
            np.array(r["rail_relative_to_side_rotation_rad"])
            - np.array(states[j]["rail_relative_to_side_rotation_rad"]))) * 180 / math.pi
    for row in summary:
        group = [r for r in states if r["clearance_mm"] == row["clearance_mm"]
                 and r["scenario_id"].startswith(row["scenario"] + ";")]
        row["largest_other_spring_force_change_n"] = max(abs(r["largest_other_spring_force_change"]["signed_change_n"]) for r in group)
        row["rigid_host_peak_movement_change_mm"] = max(r["rigid_host_movement_change_from_source_mm"] for r in group)
        row["rigid_host_peak_rotation_change_deg"] = max(r["rigid_host_rotation_change_from_source_deg"] for r in group)
    pins = dict(frame.pins)
    for name in ("check_frame.py", "study.py"):
        path = Path(__file__).with_name(name)
        pins[str(path.relative_to(ROOT))] = sha(path)
    report = {
        "schema": "upper_left_service_frozen_frame_clearance_comparison/v1",
        "status": "CONDITIONAL_COMPARISON_ONLY",
        "complete_joint": "HOLD", "release": False, "native_run": False,
        "source_sha256": pins, "physical_operator_identity": frame.identity,
        "open_normal_law_extension": "Explicit study assumption: zero force continues for q<-10 mm; positive source-table branches are not extrapolated.",
        "raw_H_retained": True, "known_answer": answer,
        "load_scale": 2., "scenario_count": len(summary), "state_count": len(states),
        "practical_baseline_tolerance": {"force_n": .002, "spring_q_mm": 1e-4},
        "source_baseline_checks": baseline_audits,
        "summary": summary, "states": states,
    }
    vectors = {k: np.stack([a[k] for a in arrays]) for k in ("f", "q", "a")}
    return report, vectors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vectors", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.vectors.exists():
        raise ValueError("refusing to overwrite existing evidence")
    report, vectors = produce()
    np.savez_compressed(args.vectors, **vectors)
    report["vectors_sha256"] = sha(args.vectors)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output),
                      "vectors": str(args.vectors), "vectors_sha256": sha(args.vectors)}))


if __name__ == "__main__":
    main()
