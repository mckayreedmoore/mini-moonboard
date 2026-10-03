"""Combine frozen right host-pair responses and replay applicable wood references.

No new mechanics solve is performed. Opposite host wrenches are energy-dual
reactions of the rigid-cleat hypothesis, not recovered elastic cleat tractions.
"""

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

CLEAT = "top_outer_right_cleat"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
PINS = {
    HERE / "rawlocal/upper-right-rail-pair/attempt01/checks.json": "e0cccb56abb94ed16c322da888cd64a9904c4e49d1e34f573a6903c8b8b98d3d",
    HERE / "rawlocal/upper-right-side-pair/attempt01/checks.json": "b507a5a501737c89814a471eee6a12749a3c54224f5444b2c5d583020e875ba7",
    HERE / "operators-attempt02/model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    HERE / "operators-attempt02/model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    HERE / "operators-attempt02/row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    HERE / "operators-attempt02/operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    HERE / "frame-250-attempt02/comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    HERE / "frame-250-attempt02/response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    HERE / "bolted-replay-results/corner-attempt01/component-results.json": "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
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


def dump(path, record):
    path.write_text(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")


def shift(wrench, old, new):
    vector = np.array(wrench, dtype=float)
    return np.r_[vector[:3], vector[3:] + np.cross(np.array(old) - new, vector[:3])]


def run(output):
    require(not output.exists(), "preserve existing attempt")
    pins = dict(PINS)
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    for path, digest in pins.items():
        require(sha(path) == digest, f"frozen source differs: {path}")
    groups = [read(HERE / f"rawlocal/upper-right-{family}-pair/attempt01/checks.json")
              for family in ("rail", "side")]
    for group in groups:
        require([s["case_id"] for s in group["states"]] == CASES, "pair case census differs")
        require(not group["complete_joint_acceptance"] and not group["physical_release"], "pair claims acceptance")
        for relative, digest in group["source_sha256"].items():
            path = ROOT / relative
            require(sha(path) == digest, f"pair source differs: {relative}")
            require(path not in pins or pins[path] == digest, "conflicting source pin")
            pins[path] = digest
    model = read(HERE / "operators-attempt02/model.json")
    inputs = read(HERE / "operators-attempt02/model-inputs.json")
    rows = read(HERE / "operators-attempt02/row-identities.json")
    comparison = read(HERE / "frame-250-attempt02/comparison.json")
    component = read(HERE / "bolted-replay-results/corner-attempt01/component-results.json")
    grains = {m["member_id"]: np.array(m["reduced_geometry_descriptor"]["axis"])
              for m in inputs["members"] if "axis" in m["reduced_geometry_descriptor"]}
    body = model["body_names"].index(CLEAT)
    body_slice = slice(6*body, 6*body + 6)
    datum = np.mean([model["physical_node_coordinates_mm"][str(n)]
                     for n in sorted(set(model["body_nodes"][CLEAT]))], axis=0)
    selected = [r["row"] for r in rows if CLEAT in
                (r["ownership"]["first_body"], r["ownership"]["second_body"])]
    require(len(selected) == 44, "whole-block incident row census differs")
    require({rows[i]["ownership"]["first_body"] for i in selected} == {"base_rail_top", "base_side_right"},
            "unexpected block attachment")
    paths = {(p["axis_id"], p["grain_direction_sign"]): p for p in component["finished_paths"]}
    seats = {(p["axis_id"], p["body"]): p for p in component["washer_seats"]}
    fv, fc = (component["component_references_mpa"][key] for key in ("Fv_parallel", "Fc_perpendicular"))
    states, bolt_states = [], []
    with np.load(HERE / "operators-attempt02/operators.npz", allow_pickle=False) as op, \
            np.load(HERE / "frame-250-attempt02/response.npz", allow_pickle=False) as response:
        for case_index, case in enumerate(CASES):
            case_input = inputs["cases"][case_index]
            require(case_input["case_id"] == case, "load column order differs")
            raw = response[case + "_gap_raw_force_n"]
            weight = comparison["dead_load_factor"]*op["W"][body_slice, 2*case_index] + op["W"][body_slice, 2*case_index + 1]
            weight = weight.copy()
            weight[3:] *= 1000
            original = -op["D"][selected, body_slice].T @ raw[selected]
            original[3:] *= 1000
            derived = np.zeros(6)
            hosts = []
            for group in groups:
                state, spec = group["states"][case_index], group["model"]
                old = np.array(spec["face_datum_xyz_mm"])
                host_wrench = np.sum([b["wrench_on_host_at_face_datum_n_nmm"] for b in state["bolts"]], axis=0)
                host_wrench += np.array(state["face_wrench_on_host_at_face_datum_n_nmm"])
                reaction = -shift(host_wrench, old, datum)
                source_reaction = -shift(state["source_connector_wrench_on_host_n_nmm"], old, datum)
                derived += reaction
                translation = np.array(state["host_translation_at_face_datum_xyz_mm"])
                rotation = np.array(state["host_rotation_xyz_rad"])
                translation += np.cross(rotation, datum - old)
                hosts.append({"host": spec["host"], "source_reaction_on_rigid_cleat_n_nmm": source_reaction.tolist(),
                              "compatible_reaction_on_rigid_cleat_n_nmm": reaction.tolist(),
                              "representative_relative_translation_at_common_datum_mm": translation.tolist(),
                              "representative_relative_rotation_rad": rotation.tolist(),
                              "tangent_nullity": state["tangent_nullity_at_relative_1e_12"],
                              "face_pressure_peak_mpa": max(c["pressure_mpa"] for c in state["face_cells"])})
                for bolt in state["bolts"]:
                    force = -np.array(bolt["bore_force_on_host_xyz_n"])
                    family = spec["geometry"]
                    reference = lateral_reference(force, family["diameter_mm"],
                                                  [family["host_length_mm"], family["cleat_length_mm"]],
                                                  [grains[spec["host"]], grains[CLEAT]], 92000.0)
                    adjustment = math.prod(component["rail_component_Cg_Cdelta"]) if spec["host"] == "base_rail_top" else 1.0
                    parallel = float(force @ grains[CLEAT])
                    path = paths[(bolt["axis_id"], 1 if parallel >= 0 else -1)]
                    seat = seats[(bolt["axis_id"], CLEAT)]
                    pressure = bolt["compatible_T_n"]/seat["minimum_annulus_area_mm2"]
                    record = {"case_id": case, "axis_id": bolt["axis_id"], "host": spec["host"],
                              "T_n": bolt["compatible_T_n"], "V_n": float(np.linalg.norm(force)),
                              "force_on_cleat_lateral_xyz_n": force.tolist(), "lateral_reference": reference,
                              "Cg_Cdelta_multiplier": adjustment,
                              "lateral_over_conditional_reference": float(np.linalg.norm(force))/(reference["reference_n"]*adjustment),
                              "parallel_force_n": parallel, "finished_path_sign": path["grain_direction_sign"],
                              "parallel_over_finished_path_reference": abs(parallel)/(fv*path["minimum_finished_one_plane_area_mm2"]),
                              "full_annulus_mean_wood_pressure_mpa": pressure,
                              "mean_pressure_over_Fc_perp": pressure/fc,
                              "sampled_end_wood_pressure_peak_mpa": max(e["wood_contact"]["pressure_peak_mpa"] for e in bolt["end_contacts"]),
                              "smooth_bolt_VM_over_92ksi_hypothesis": bolt["peak_stress_witness"]["proxy_over_conditional_92ksi_Fyb"],
                              "complete_joint_acceptance": False}
                    bolt_states.append(record)
            source_error, derived_error = original + weight, derived + weight
            require(np.max(abs(source_error[:3])) < 1e-7 and np.max(abs(source_error[3:])) < 1e-5, "source whole-block balance differs")
            require(np.max(abs(derived_error[:3])) < .002 and np.max(abs(derived_error[3:])) < .6, "derived rigid-block balance exceeds pair tolerances")
            states.append({"case_id": case, "hosts": hosts, "applied_weight_wrench_n_nmm": weight.tolist(),
                           "source_connector_wrench_n_nmm": original.tolist(), "compatible_connector_wrench_n_nmm": derived.tolist(),
                           "source_balance_residual_n_nmm": source_error.tolist(), "compatible_balance_residual_n_nmm": derived_error.tolist(),
                           "cleat_translation_xyz_mm": [0, 0, 0], "cleat_rotation_xyz_rad": [0, 0, 0],
                           "cleat_pose_is_rigid_gauge": True})
    require(len(bolt_states) == 24, "four-bolt six-state census differs")
    keys = ("lateral_over_conditional_reference", "parallel_over_finished_path_reference",
            "mean_pressure_over_Fc_perp", "smooth_bolt_VM_over_92ksi_hypothesis")
    peaks = {key: max(bolt_states, key=lambda row, key=key: row[key]) for key in keys}
    result = {"schema": "upper_right_rigid_whole_block_replay/v1", "status": "FINITE_RIGID_BLOCK_ACCOUNTING",
              "cleat": CLEAT, "common_datum_xyz_mm": datum.tolist(), "incident_rows": selected,
              "states": states, "bolt_states": bolt_states, "peak_witnesses": peaks,
              "host_splitting_geometry_and_original_demands": [s for s in component["host_splitting"] if s["block"] == CLEAT],
              "limits": ["Both pair solutions use the same fixed rigid cleat. Opposite, shifted host gradients give its energy-dual reactions; their balance is not an independent elastic-traction validation.",
                         "The two host drives are frozen group wrenches. Local redistribution is not fed back into frame loads, floor contacts or other joints.",
                         "Current mapped W, including assigned hardware and its couple, is retained once. No extra gravity is added to host drives.",
                         "Common-datum host poses are compatible representatives in a rigid-cleat gauge, not unique motion bounds.",
                         "The unchanged single-shear, finished tangent-path and mean full-annulus references are component screens. Peak spring contact pressure is not an adopted bearing utilization.",
                         "Saved host splitting fields carry the original source demands only. Group net wrench is retained, but redistributed individual bolts need not retain local cuts; characteristic F90 is not an adjusted design resistance.",
                         "Elastic cleat deformation, combined oblique-group/splitting resistance and actual washer/hardware properties remain outside this calculation."],
              "complete_joint_acceptance": False, "physical_release": False,
              "source_sha256": {str(path.relative_to(ROOT)): digest for path, digest in sorted(pins.items())}}
    for path, digest in pins.items():
        require(sha(path) == digest, f"source changed during replay: {path}")
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "checks.json", result)
    dump(output / "receipt.json", {"source_sha256": result["source_sha256"],
                                   "output_sha256": {name: sha(output / name) for name in ("checks.json", "producer.py.snapshot")},
                                   "complete_joint_acceptance": False, "physical_release": False})
    print(json.dumps({"checks_sha256": sha(output / "checks.json"),
                      "peak_indices": {key: record[key] for key, record in peaks.items()}}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output.resolve())
