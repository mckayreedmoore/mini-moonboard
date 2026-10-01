#!/usr/bin/env python3
"""Bind conditional transverse frames to twenty preserved timber grain vectors."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent / "current-frame-timber-material-frame-map-attempt01"
SOURCE = BASE / "current-frame-timber-material-frame-map.json"
SCENARIO = ROOT / "docs/wood-joints-mvp/current-material-scenarios.md"
OUTPUT = HERE / "transverse-scenarios.json"
SOURCE_SHA = "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409"
SCENARIO_SHA = "dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4"
TOLERANCE = 1e-12


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def unit(vector):
    require(len(vector) == 3 and all(math.isfinite(v) for v in vector),
            "Invalid vector")
    norm = math.sqrt(dot(vector, vector))
    require(norm > 1e-10, "Degenerate vector")
    return [v / norm for v in vector]


def audit_frame(axes):
    vectors = [axes[name] for name in ("L", "R", "T")]
    gram_error = max(abs(dot(vectors[i], vectors[j]) - float(i == j))
                     for i in range(3) for j in range(3))
    determinant = dot(vectors[0], cross(vectors[1], vectors[2]))
    require(gram_error <= TOLERANCE and abs(determinant - 1) <= TOLERANCE,
            "Material frame is not right-handed orthonormal")
    return {"max_gram_error": gram_error, "determinant": determinant}


def produce():
    require(sha(SOURCE) == SOURCE_SHA and sha(SCENARIO) == SCENARIO_SHA,
            "Pinned source map or scenario changed")
    source = json.loads(SOURCE.read_text())
    digest_record = dict(source)
    recorded = digest_record.pop("record_sha256")
    require(hashlib.sha256(canonical(digest_record)).hexdigest() == recorded,
            "Source content digest mismatch")
    require(source["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1",
            "Wrong reviewed revision")
    for name, pin in source["source_pins"].items():
        require(sha(ROOT / name) == pin["sha256"], f"Upstream source changed: {name}")
    rows = source["members"]
    require(len(rows) == len({row["member_id"] for row in rows}) == 20,
            "Expected twenty unique frame timber IDs")
    output_rows = []
    for row in rows:
        lineage = row["current_geometry_lineage"]
        step = ROOT / lineage["step_file"]
        require(sha(step) == lineage["step_sha256"]
                and step.stat().st_size == lineage["step_size_bytes"],
                f"STEP changed: {row['member_id']}")
        original = row["conditional_grain_assignment"]["proposed_global_xyz"]
        require(abs(dot(original, original) - 1) < TOLERANCE,
                "Source longitudinal vector is not already unit length")
        longitudinal = unit(original)
        source_axes = row["source_frame"]["axes_global_xyz"]
        # Use source X unless it is parallel to L, then source T. Projection
        # preserves an oblique recorded L without snapping it to a source axis.
        reference_name = "X"
        reference = source_axes[reference_name]
        projection = [v - dot(reference, longitudinal) * l
                      for v, l in zip(reference, longitudinal, strict=True)]
        if dot(projection, projection) < 1e-12:
            reference_name = "T"
            reference = source_axes[reference_name]
            projection = [v - dot(reference, longitudinal) * l
                          for v, l in zip(reference, longitudinal, strict=True)]
        radial = unit(projection)
        tangential = unit(cross(longitudinal, radial))
        cases = {
            "A": {"L": longitudinal, "R": radial, "T": tangential},
            "B": {"L": longitudinal, "R": tangential, "T": [-v for v in radial]},
        }
        audits = {name: audit_frame(axes) for name, axes in cases.items()}
        require(max(abs(cases["A"]["L"][i] - original[i]) for i in range(3)) <= TOLERANCE,
                "Longitudinal direction changed")
        output_rows.append({
            "member_id": row["member_id"],
            "source_member_record_sha256": hashlib.sha256(canonical(row)).hexdigest(),
            "step_file": lineage["step_file"], "step_sha256": lineage["step_sha256"],
            "source_shape_fingerprint_sha256": lineage["source_shape_fingerprint_sha256"],
            "source_longitudinal_global_xyz": original,
            "case_A_radial_reference_source_axis": reference_name,
            "cases_global_xyz": cases, "frame_audits": audits,
            "observed_ring_orientation": None, "selected_case": None,
            "solver_element_assignment": None,
        })
    result = {
        "schema": "current_frame_timber_transverse_scenarios/v1",
        "status": "CONDITIONAL_TRANSVERSE_SCENARIOS_ONLY",
        "candidate": source["candidate"],
        "geometry_revision_id": source["geometry_revision_id"],
        "selected_candidate_preserved": source["selected_candidate_preserved"],
        "source_pins": {str(SOURCE.relative_to(ROOT)): SOURCE_SHA,
                        str(SCENARIO.relative_to(ROOT)): SCENARIO_SHA},
        "producer_sha256": sha(Path(__file__)),
        "source_map_content_sha256": recorded,
        "member_count": 20, "scenario_frame_count": 40,
        "method": "L is the normalized recorded grain vector; R_A is normalized projection of source X perpendicular to L (source T only if X parallel); T_A=L cross R_A; R_B=T_A and T_B=-R_A.",
        "algebra_tolerance": TOLERANCE,
        "scenario_policy": "Two analyst-selected transverse cases per body, not observed ring direction or guaranteed bounds. Uniform all-A/all-B runs do not bound mixed boards; inspect relevant individual-body swaps if response is sensitive.",
        "members": output_rows,
        "wood_properties_assigned": False, "panel_layups_assigned": False,
        "geometry_changed": False, "cad_rebuilt": False, "native_solve_run": False,
        "full_frame_inputs_ready": False, "material_acceptance": False,
        "joint_acceptance": False, "release": False,
    }
    result["record_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = produce()
    if args.write:
        with OUTPUT.open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
    else:
        require(json.loads(OUTPUT.read_text()) == result, "Stored map differs from reproduced map")
    print(json.dumps({"status": "WRITTEN" if args.write else "PASS_SOURCE_AND_FRAME_ALGEBRA",
                      "member_count": 20, "scenario_frame_count": 40,
                      "record_sha256": result["record_sha256"], "native_solve_run": False}))
