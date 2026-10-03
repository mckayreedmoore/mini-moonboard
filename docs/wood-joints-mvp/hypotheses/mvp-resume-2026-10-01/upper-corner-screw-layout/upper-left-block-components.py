"""Replay finished component references on a completed actual left-block result."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))
from corner_checks import lateral_reference

CLEAT = "top_outer_left_cleat"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
COMPONENT = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
INPUTS = HERE / "operators-attempt02/model-inputs.json"
PINS = {
    COMPONENT: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
    INPUTS: "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    HERE.parent / "corner_checks.py": "177e13712575b735dfb2cd4d1314d006e3f8fc77d3cbc9b3e117609fbe561bb0",
    HERE.parent / "lateral_reference.py": "845409d1daf0214bbd41484f0a0a58867cd266bbc7f19060d9eef9d342657e94",
    HERE.parent / "top_corner_correction.py": "6474cbe6aa8306a153b6cbe166c3162001954b41ea7e4da6c6b7fe60031472e9",
    ROOT / "fea/dowel_yield.py": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def run(source, digest, output):
    require(not output.exists(), "preserve existing attempt")
    require(source.is_relative_to(ROOT), "source must be retained inside repository")
    pins = {**PINS, source: digest, Path(__file__).resolve(): sha(Path(__file__).resolve())}
    result = read(source)
    require(result["schema"] == "upper_left_common_cleat_four_bolt_local_pair_sensitivity/v1"
            and result["counts"]["completed_cases"] == 6 and result["counts"]["completed_host_models"] == 12
            and result["failure"] is None, "left common-block result incomplete")
    require(not result["complete_joint_acceptance"] and not result["physical_release"], "source claims acceptance")
    require(result["model"]["fixed_cleat"] == CLEAT and [s["case_id"] for s in result["states"]] == CASES,
            "source left identity or case order differs")
    for relative, expected in result["source_sha256"].items():
        path = ROOT / relative
        require(path not in pins or pins[path] == expected, "conflicting source pin")
        pins[path] = expected
    for path, expected in pins.items():
        require(sha(path) == expected, f"source differs: {path}")
    component, inputs = read(COMPONENT), read(INPUTS)
    grains = {m["member_id"]: np.array(m["reduced_geometry_descriptor"]["axis"])
              for m in inputs["members"] if "axis" in m["reduced_geometry_descriptor"]}
    paths = {(p["axis_id"], p["grain_direction_sign"]): p for p in component["finished_paths"]}
    seats = {(s["axis_id"], s["body"]): s for s in component["washer_seats"]}
    fv, fc = (component["component_references_mpa"][key] for key in ("Fv_parallel", "Fc_perpendicular"))
    states = []
    for case in result["states"]:
        require("whole_cleat" in case and set(case["hosts"]) == {"base_rail_top", "base_side_left"}, "incomplete common block")
        for host, local in case["hosts"].items():
            geometry = result["model"]["host_groups"][host]["receiver_geometry"]
            require(len(local["bolts"]) == 2 and len(local["face_cells"]) == 16, "host census differs")
            for bolt in local["bolts"]:
                force = -np.array(bolt["bore_force_on_host_xyz_n"])
                reference = lateral_reference(force, geometry["diameter_mm"],
                                              [geometry["host_length_mm"], geometry["cleat_length_mm"]],
                                              [grains[host], grains[CLEAT]], 92000.0)
                factor = math.prod(component["rail_component_Cg_Cdelta"]) if host == "base_rail_top" else 1.0
                parallel = float(force @ grains[CLEAT])
                path = paths[(bolt["axis_id"], 1 if parallel >= 0 else -1)]
                seat = seats[(bolt["axis_id"], CLEAT)]
                states.append({"case_id": case["case_id"], "axis_id": bolt["axis_id"], "host": host,
                               "T_n": bolt["compatible_T_n"], "V_n": float(np.linalg.norm(force)),
                               "force_on_cleat_lateral_xyz_n": force.tolist(), "lateral_reference": reference,
                               "Cg_Cdelta_multiplier": factor,
                               "lateral_over_conditional_reference": float(np.linalg.norm(force))/(factor*reference["reference_n"]),
                               "finished_path_sign": path["grain_direction_sign"], "parallel_force_n": parallel,
                               "parallel_over_finished_path_reference": abs(parallel)/(fv*path["minimum_finished_one_plane_area_mm2"]),
                               "mean_pressure_over_Fc_perp": bolt["compatible_T_n"]/(fc*seat["minimum_annulus_area_mm2"]),
                               "sampled_end_wood_pressure_peak_mpa": max(e["wood_contact"]["pressure_peak_mpa"] for e in bolt["end_contacts"]),
                               "smooth_bolt_VM_over_92ksi_hypothesis": bolt["peak_stress_witness"]["proxy_over_conditional_92ksi_Fyb"]})
    require(len(states) == 24, "four-bolt six-case census differs")
    keys = ("lateral_over_conditional_reference", "parallel_over_finished_path_reference",
            "mean_pressure_over_Fc_perp", "smooth_bolt_VM_over_92ksi_hypothesis")
    peaks = {key: max(states, key=lambda state, key=key: state[key]) for key in keys}
    record = {"schema": "upper_left_compatible_block_component_replay/v1", "states": states, "peak_witnesses": peaks,
              "host_splitting_original_source_only": [s for s in component["host_splitting"] if s["block"] == CLEAT],
              "limits": ["These are the unchanged single-shear, bore-tangent and full-annulus mean references applied to changed individual compatible bolt responses.",
                         "Smooth-bolt stress includes pair beam bending; 92 ksi remains a conditional Fyb hypothesis.",
                         "Existing original host splitting geometry/demands are retained for scope only. Local group redistribution is not a new complete-host cut replay or an adopted splitting design conversion.",
                         "Mean wood pressure is not a peak-contact spring utilization. No coupled oblique-group, elastic cleat, actual washer/hardware or full-frame resistance is established."],
              "source_sha256": {str(path.relative_to(ROOT)): expected for path, expected in sorted(pins.items())},
              "complete_joint_acceptance": False, "physical_release": False}
    for path, expected in pins.items():
        require(sha(path) == expected, f"source changed during replay: {path}")
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "checks.json", record)
    dump(output / "receipt.json", {"source_sha256": record["source_sha256"],
                                   "output_sha256": {name: sha(output / name) for name in ("checks.json", "producer.py.snapshot")},
                                   "complete_joint_acceptance": False, "physical_release": False})
    print(json.dumps({"checks_sha256": sha(output / "checks.json"), "peak_indices": {key: row[key] for key, row in peaks.items()}}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source.resolve(), args.source_sha256, args.output.resolve())
