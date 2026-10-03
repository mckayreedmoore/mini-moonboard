#!/usr/bin/env python3
"""Retain simultaneous signed plane/tie actions at each three-case peak."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
SOURCES = {
    "a12-rear": ("current-corner-native-demand-export-attempt03", "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17"),
    "a1-rear": ("current-corner-a1-rear-case-bound-export-attempt01", "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce"),
    "k12-rear": ("current-corner-k12-rear-case-bound-export-attempt01", "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0"),
}


def norm(vector):
    return math.sqrt(sum(x*x for x in vector))


def build():
    assert norm([3., -4., 0.]) == 5.
    rows = []
    pins = {}
    for case, (folder, expected) in SOURCES.items():
        path = BASE/folder/"corner-demand-report.json"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected
        pins[str(path.relative_to(ROOT))] = actual
        report = json.loads(path.read_text())
        assert report["case_id"] == case
        assert report["actual_case_demand_usable_for_conditional_joint_checks"]
        assert len(report["increments"]) == 7
        for inc in report["increments"]:
            assert all(inc["response_audit_gates"].values())
            assert inc["all_five_corner_bodies_raw_and_interval_balance_passed"]
            for group_id, group in report_group_items(inc):
                for bolt in group["bolts"]:
                    ties = [a for a in bolt["actions"] if a["role"] == "physical_bolt_outer_seat_tension"]
                    assert len(ties) == 1
                    for action in bolt["actions"]:
                        if action["role"] != "candidate_bolt_lateral_plane":
                            continue
                        rows.append({"group": group_id, "axis_id": bolt["axis_id"],
                            "case_id": case, "load_factor": inc["load_factor"],
                            "source_connection_name": action["source_connection_name"],
                            "first_receiver": action["first"], "second_receiver": action["second"],
                            "force_on_first_xyz_N": action["force_on_first_xyz_n"],
                            "force_on_second_xyz_N": action["force_on_second_xyz_n"],
                            "point_global_xyz_mm": action["first_point_global_xyz_mm"],
                            "lateral_resultant_N": norm(action["force_on_first_xyz_n"]),
                            "simultaneous_outer_tie": ties[0],
                            "simultaneous_tie_force_magnitude_N": norm(ties[0]["force_on_first_xyz_n"]),
                            "both_same_bolt_plane_actions": [a for a in bolt["actions"] if a["role"] == "candidate_bolt_lateral_plane"],
                        })
    assert len(rows) == 168
    peaks = {}
    for row in rows:
        key = row["source_connection_name"]
        if key not in peaks or row["lateral_resultant_N"] > peaks[key]["lateral_resultant_N"]:
            peaks[key] = row
    assert len(peaks) == 8
    return {"schema": "three_case_corner_signed_component_register/v1",
        "status": "AUTHENTICATED_CONDITIONAL_DEMANDS_COMPLETE_RESISTANCE_OPEN",
        "source_pins": pins, "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "plane_state_count": len(rows), "plane_count": len(peaks), "rows": rows,
        "peak_lateral_states": [peaks[k] for k in sorted(peaks)],
        "limits": ["Three accepted rear cases only, not a six-case/stiffness envelope.",
            "Peak rows retain same-state tie and both planes; no independent maxima are combined and planes/bolts are not summed as capacities.",
            "No capacity, mixed-action ratio or complete-joint acceptance is computed."]}


def report_group_items(inc):
    groups = inc["primary_physical_bolt_groups"]
    assert set(groups) == {"BG001", "BG003", "BG045"}
    return sorted(groups.items())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    content = json.dumps(build(), indent=2, sort_keys=True, allow_nan=False)+"\n"
    path = HERE/"signed-demands.json"
    if args.verify:
        assert path.read_text() == content
        print("PASS_BYTE_IDENTICAL_168_SIGNED_PLANE_STATES")
    else:
        path.write_text(content)
        print("WROTE", path.relative_to(ROOT))
