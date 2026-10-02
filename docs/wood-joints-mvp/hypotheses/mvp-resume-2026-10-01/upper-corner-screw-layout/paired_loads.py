"""Build one declared hand/foot load sensitivity from frozen applied-load columns.

Half the vertical live force moves from each upper hold to the saved lower-left
A1 hold. Horizontal force stays at the original hold; A1-rear stays unchanged.
These are applied-load combinations, never averages of solved connector forces.
"""

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import both_corner_frame as frame

ROOT = frame.ROOT
SOURCE = HERE / "operators-attempt02"
COMPONENTS = HERE / "load-components-attempt01"
SEED = HERE.parent / "corner-frame-attempt01"
sha, read, require = frame.sha, frame.read, frame.require


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def build(output):
    require(not output.exists(), "preserve previous paired-load packet")
    assessment = read(SOURCE / "operator-assessment.json")
    receipt = read(COMPONENTS / "receipt.json")
    require(sha(SOURCE / "operators.npz") ==
            "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
            "frozen relocated operators changed")
    require(receipt["frame_operator_sha256"] == sha(SOURCE / "operators.npz"),
            "vertical components belong to another frame")
    pins = {ROOT / p: h for p, h in assessment["source_sha256"].items()}
    pins.update({SOURCE / p: h for p, h in assessment["output_sha256"].items()})
    pins.update({p: sha(p) for p in (SOURCE / "operator-assessment.json",
                                  COMPONENTS / "receipt.json", Path(__file__))})
    pins[COMPONENTS / "components.npz"] = receipt["components_sha256"]
    for path, digest in pins.items():
        require(sha(path) == digest, "changed paired-load source: " + str(path))
    with np.load(SOURCE / "operators.npz", allow_pickle=False) as data:
        operators = {key: data[key].copy() for key in data.files}
    with np.load(COMPONENTS / "components.npz", allow_pickle=False) as data:
        vertical = {key: data[key].copy() for key in data.files}
    inputs = read(SOURCE / "model-inputs.json")
    cases = [case["case_id"] for case in inputs["cases"]]
    require(cases == ["a12-rear", "a12-forward", "a12-left", "k12-right",
                      "k12-rear", "a1-rear"], "case order changed")
    original = copy.deepcopy(inputs["cases"])
    allocations = []
    for index, case in enumerate(inputs["cases"]):
        if index == 5:
            allocations.append({"case_id": case["case_id"], "unchanged_A1_case": True})
            continue
        for key in ("e", "W", "F"):
            component = vertical[{"e": "e_vertical", "W": "W_vertical",
                                  "F": "F_vertical"}[key]]
            require(component.shape == operators[key][:, 1::2].shape,
                    "applied-load component dimensions changed")
            operators[key][:, 2 * index + 1] += 0.5 * (component[:, 5] - component[:, index])
        upper = original[index]["source_applied_load"]
        foot = original[5]["source_applied_load"]
        force = np.array(upper["applied_force_global_xyz_n"], dtype=float)
        vertical_half = np.array([0.0, 0.0, force[2] / 2])
        allocation = {
            "case_id": case["case_id"],
            "original_applied_load": upper,
            "resultant_force_global_xyz_n": force.tolist(),
            "contacts": [
                {"role": "upper_hand_hypothesis", "loaded_panel": original[index]["loaded_panel"],
                 "force_point_global_xyz_mm": upper["force_application_point_global_xyz_mm"],
                 "force_global_xyz_n": (force - vertical_half).tolist()},
                {"role": "lower_left_foot_hypothesis", "loaded_panel": original[5]["loaded_panel"],
                 "force_point_global_xyz_mm": foot["force_application_point_global_xyz_mm"],
                 "force_global_xyz_n": vertical_half.tolist()},
            ],
        }
        case["source_applied_load"] = allocation
        allocations.append(allocation)
    scope = {
        "scenario": "hypothetical_equal_vertical_hand_A1foot_split",
        "weight_lb": 250.0, "dynamic_force_multiplier": 2.0,
        "upper_vertical_fraction": 0.5, "horizontal_force_at_original_hold_n": 300.0,
        "gravity_and_accessory_loads_unchanged": True,
        "all_six_resultant_forces_preserved": True,
        "five_upper_case_moments_changed": True,
        "A1_rear_unchanged": True,
        "physical_stance_or_dynamic_bound_qualified": False,
        "original_single_hold_requirement_replaced": False,
        "contact_allocations": allocations,
    }
    model = read(SOURCE / "model.json")
    centers = [np.mean([model["physical_node_coordinates_mm"][str(node)]
                        for node in model["body_nodes"][body]], axis=0)
               for body in model["body_names"]]
    wrench_checks = []
    for index, allocation in enumerate(allocations):
        work = operators["W"][:, 2 * index + 1].reshape(-1, 6)
        actual_force = work[:, :3].sum(axis=0)
        actual_moment = (1000 * work[:, 3:] + np.cross(centers, work[:, :3])).sum(axis=0)
        contacts = allocation.get("contacts") or [{
            "force_global_xyz_n": original[index]["source_applied_load"]["applied_force_global_xyz_n"],
            "force_point_global_xyz_mm": original[index]["source_applied_load"]["force_application_point_global_xyz_mm"],
        }]
        expected_force = np.sum([contact["force_global_xyz_n"] for contact in contacts], axis=0)
        expected_moment = np.sum([np.cross(contact["force_point_global_xyz_mm"],
                                           contact["force_global_xyz_n"])
                                  for contact in contacts], axis=0)
        force_error = float(np.max(abs(actual_force - expected_force)))
        moment_error = float(np.max(abs(actual_moment - expected_moment)))
        require(force_error < 1e-7 and moment_error < 1e-5,
                "paired applied-load wrench differs from declared contacts")
        wrench_checks.append({"case_id": cases[index],
                              "force_global_xyz_n": actual_force.tolist(),
                              "moment_about_global_origin_xyz_nmm": actual_moment.tolist(),
                              "force_error_n": force_error, "moment_error_nmm": moment_error})
    scope["global_wrench_checks"] = wrench_checks
    model["diagnostic_load_scenario"] = scope
    inputs["diagnostic_load_scenario"] = scope
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during load preparation: " + str(path))
    output.mkdir(parents=True)
    np.savez_compressed(output / "operators.npz", **operators)
    for name in ("B.npz", "row-identities.json"):
        shutil.copyfile(SOURCE / name, output / name)
    write(output / "model.json", model)
    write(output / "model-inputs.json", inputs)
    source_pins = {str(p.relative_to(ROOT)): h for p, h in pins.items()}
    write(output / "inputs.json", {"producer_sha256": sha(Path(__file__)),
                                   "source_sha256": source_pins})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "operator-assessment.json", {
        "schema": "declared_paired_hold_loads/v1",
        "status": "PASS_UPDATED_ELASTIC_FRAME_OPERATORS",
        "producer_sha256": sha(Path(__file__)), "source_sha256": source_pins,
        "modeled_mass_kg": assessment["modeled_mass_kg"],
        "output_sha256": {name: sha(output / name) for name in
                          ("operators.npz", "B.npz", "row-identities.json",
                           "model.json", "model-inputs.json")},
        "diagnostic_load_scenario": scope,
        "native_solve_run": False, "geometry_changed": False,
        "complete_joint_acceptance": False, "physical_release": False,
    })
    return scope


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    args.output = args.output.resolve()
    scope = build(args.output / "operators")
    if args.run:
        frame.run(args.output / "frame", service_joints=True, bottom_corners=True,
                  all_two_receiver_clearances=True, bounded_freeplay=True,
                  frame_directory=args.output / "operators", seed_directory=SEED,
                  connection_inputs=args.output / "operators/model-inputs.json")
