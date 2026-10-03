"""Prepare the frozen six-case header local-transfer input contract.

This extracts saved actions and finished geometry. It performs no mechanical
solve, section calculation, force redistribution or resistance qualification.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RESUME = HERE.parent
HEADER = RESUME / "header-joint-attempt04/four-screw-250-attempt02"
MEMBER = RESUME / "member-screen-attempt02/four-screw-layout01"
OPERATORS = HERE / "operators-attempt02"
FRAME = HERE / "frame-250-attempt02"
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
ADAPTER = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
CONTACTS = BASE / "reduced-static-attempt01/contact-geometry.json"
SURFACES = RESUME.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
DUTIES = HERE / "rawlocal/remaining-block-duties/attempt02/duties.json"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
BLOCKS = ["center_post_cleat_left", "center_post_cleat_right", "center_principal_cleat_left",
          "center_principal_cleat_right", "knee_outer_left_inner_frame_block", "knee_outer_right_inner_frame_block"]
PINS = {
    HEADER / "checks.json": "f34fba71b0416cf7a5d1081a48c66c8d518b642e53e7f7f8a80a0646b707362d",
    HEADER / "joint-actions.json": "2a37efc475fce1e6eb65b23a8e7fd7b0e8bbdd3be3af9f3f41df0620a262452f",
    HEADER / "joint-states.json": "be78ec533e93963ab900103d107e391b57a1d52125025e47eb06a37f16ef6232",
    HEADER / "placement.json": "9f0aef8c98dab5a41e47472f2c1251b9311789730927ec810c04fedd4ca6f58d",
    HEADER / "header-sections.csv": "f32ab4731eb4cb12fbdc400f81a0fb9ba8d8065eabbccc378483ecd0b36e5953",
    HEADER / "source-pins.json": "5e5cb0f210ee33ec6ecc7885e91b9d68d7f294cfdb24f8efb0e5e427ebee95a6",
    OPERATORS / "model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    OPERATORS / "model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    OPERATORS / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    FRAME / "comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    FRAME / "response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    MEMBER / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    MEMBER / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    MEMBER / "action-section-arrays.npz": "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    DUTIES: "5a5c63a27ed6994db900e8c5d2f20e3770a726fd1008a65ac860e891cf00949a",
    SURFACES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    ADAPTER: "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    CONTACTS: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
}
FLAGS = {"native_readiness": False, "mechanics_executed": False,
         "new_resistance_established": False, "complete_joint_acceptance": False, "physical_release": False}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, f"frozen input changed: {path}")


def keyed(records, fields):
    result = {tuple(record[field] for field in fields): record for record in records}
    require(len(result) == len(records), f"duplicate source key: {fields}")
    return result


def saved_actions(case, record, arrays):
    body = "base_header"
    values = arrays[case + "__" + body + "__point_force_free_couple_xyz"]
    positions, stations = arrays[body + "__point_xyz_mm"], arrays[body + "__point_stations_mm"]
    footprints, rows = arrays[body + "__point_footprints_mm"], arrays[body + "__point_rows"]
    require(values.shape == (394, 6) and np.isfinite(values).all(), "header action array census differs")
    return [{"row": int(row), "source_id": identity, "role": role, "other_body": other,
             "point_mm": point.tolist(), "force_n": value[:3].tolist(), "free_moment_nmm": value[3:].tolist(),
             "station_mm": float(station), "footprint_mm": footprint.tolist()}
            for identity, role, other, point, value, station, footprint, row in zip(
                record["point_action_ids"], record["point_action_roles"], record["point_action_other_bodies"],
                positions, values, stations, footprints, rows, strict=True)]


def prepare(output, pins, debug):
    checks, actions = read(HEADER / "checks.json"), read(HEADER / "joint-actions.json")
    states, placements, inherited = read(HEADER / "joint-states.json"), read(HEADER / "placement.json"), read(HEADER / "source-pins.json")
    model, inputs, rows = read(OPERATORS / "model.json"), read(OPERATORS / "model-inputs.json"), read(OPERATORS / "row-identities.json")
    geometry, members, duties = read(MEMBER / "geometry.json"), read(MEMBER / "member-results.json"), read(DUTIES)
    require(checks["case_ids"] == CASES == duties["case_ids"], "six-case order differs")
    require(checks["gap_scale"] == duties["force_source"]["gap_scale"] == 1.0, "source is not the nominal gap")
    require(checks["response_sha256"] == duties["force_source"]["response_sha256"] == pins[FRAME / "response.npz"], "response join differs")
    require(checks["clearance_comparison_sha256"] == duties["force_source"]["comparison_sha256"] == pins[FRAME / "comparison.json"], "comparison join differs")
    comparison = read(FRAME / "comparison.json")
    require(comparison["response_sha256"] == pins[FRAME / "response.npz"], "comparison binds another response")
    require({state["case_id"] for state in comparison["states"] if state["gap_scale"] == 1.0} == set(CASES), "comparison nominal cases differ")
    for path, digest in pins.items():
        if str(path) in inherited:
            require(inherited[str(path)] == digest, "direct artifact differs from inherited source binding")
    for name in ("joint-actions.json", "joint-states.json", "placement.json", "header-sections.csv", "source-pins.json"):
        require(checks["output_sha256"][name] == pins[HEADER / name], "header output binding differs")
    for name in ("geometry.json", "action-section-arrays.npz"):
        require(members["output_sha256"][name] == pins[MEMBER / name], "member output binding differs")
    require([case["case_id"] for case in members["cases"]] == CASES, "member case order differs")
    require(set(duties["finite_next_joint_groups"]["H"]) == set(BLOCKS), "gap H body census differs")
    joints = keyed(actions["interfaces"], ("case_id", "block"))
    require(set(joints) == {(case, block) for case in CASES for block in BLOCKS}, "36 interface census differs")
    axis_ids = {axis for joint in joints.values() for axis in joint["axis_ids"]}
    require(len(axis_ids) == 12 and all(joint["host"] == "base_header" and len(joint["axis_ids"]) == 2 for joint in joints.values()), "header axis census differs")
    expected = {(case, axis) for case in CASES for axis in axis_ids}
    state_map, placement_map = keyed(states, ("case_id", "axis_id")), keyed(placements, ("case_id", "axis_id"))
    require(set(state_map) == set(placement_map) == expected, "72 same-state axis census differs")
    connections = {entry["axis_id"]: entry for entry in inputs["connections"] if entry["kind"] == "candidate_bolt" and entry["axis_id"] in axis_ids}
    require(set(connections) == axis_ids, "header connection join differs")
    features = {entry["member_id"]: entry for entry in read(SURFACES)["records"]}
    bodies = {}
    for body in ["base_header", *BLOCKS]:
        record, feature = geometry["members"][body], features[body]
        path, digest = ROOT / record["current_finished_step"], record["current_finished_step_sha256"]
        require(inherited[str(path)] == feature["step_binding"]["file_sha256"] == digest, "finished STEP join differs")
        pins[path] = digest
        grain = model["material_binding"]["orientation_overrides"][body]
        require(np.max(np.abs(np.array(grain["material_axes_global_xyz"]["L"]) - ([1, 0, 0] if body == "base_header" else [0, 0, 1]))) < 1e-8, "grain binding differs")
        bodies[body] = {"member_geometry": record, "finished_surface_record": feature, "grain_override": grain}
    authenticate(pins)
    sections = [section for section in geometry["saved_matching_finished_sections"] if section["member"] == "base_header"]
    require(len(sections) == 105 and sum(section["properties"]["disconnected_ligaments"] for section in sections) == 6, "finished section census differs")
    section_map = keyed(sections, ("plane_id",))
    with (HEADER / "header-sections.csv").open(newline="") as stream:
        cut_rows = list(csv.DictReader(stream))
    require(len(cut_rows) == 1260 and len({(r["case_id"], r["plane_id"], r["trace"]) for r in cut_rows}) == 1260, "section-state census differs")
    for cut in cut_rows:
        section = section_map[(cut["plane_id"],)]
        require(cut["case_id"] in CASES and cut["trace"] in ("before", "after") and float(cut["station_mm"]) == section["station_mm"], "section-state geometry join differs")
        if section["properties"]["disconnected_ligaments"]:
            require(cut["linear_normal_reference_sum"] == cut["net_area_shear_reference"] == "", "disconnected section gained a reference")
    referenced, case_packets = set(), []
    with (np.load(MEMBER / "action-section-arrays.npz", allow_pickle=False) as arrays,
          np.load(FRAME / "response.npz", allow_pickle=False) as response):
        for case in CASES:
            debug["stage"] = "case-joins: " + case
            header_actions = saved_actions(case, geometry["members"]["base_header"], arrays)
            require(len(header_actions) == 394, "complete header action census differs")
            raw = response[case + "_gap_raw_force_n"]
            require(raw.shape == (1888,) and np.isfinite(raw).all(), "current raw-force census differs")
            packets = []
            for block in BLOCKS:
                joint = copy.deepcopy(joints[(case, block)])
                reciprocal = {a["row"]: a for a in header_actions if a["other_body"] == block}
                target = joint["actions_on_block"]
                require(len(target) == len(reciprocal) == 10 and set(reciprocal) == {a["row"] for a in target}, "ten reciprocal action rows differ")
                ordered = [reciprocal[a["row"]] for a in target]
                for first, second in zip(target, ordered, strict=True):
                    require(first["point_mm"] == second["point_mm"] and first["source_id"] == second["source_id"], "reciprocal action identity differs")
                    require(np.max(np.abs(np.array(first["force_n"]) + second["force_n"])) < 1e-7 and np.max(np.abs(np.array(first["free_moment_nmm"]) + second["free_moment_nmm"])) < 1e-5, "saved reciprocal actions disagree")
                joint["exact_reciprocal_header_actions"] = ordered
                for axis in joint["axis_ids"]:
                    state = state_map[(case, axis)]
                    require(state["block"] == placement_map[(case, axis)]["block"] == block, "axis/block state join differs")
                    require(set(connections[axis]["receiver_member_ids"]) == {"base_header", block}, "axis receiver join differs")
                    require(abs(raw[state["tie_row"]] - state["tension_n"]) < 1e-8, "same-state tie differs")
                    force = np.zeros(3)
                    require(len(state["component_rows"]) == 2, "axis lateral component census differs")
                    for index in state["component_rows"]:
                        ownership = rows[index]["ownership"]
                        require(ownership["role"] == "candidate_bolt_lateral_plane" and rows[index]["row_id"].startswith(axis + "/"), "axis lateral row join differs")
                        force += raw[index] * np.array(ownership["direction_global_xyz"]) * (1 if ownership["first_body"] == block else -1)
                    require(np.max(np.abs(force - state["force_on_block_xyz_n"])) < 1e-7, "same-state signed lateral vector differs")
                packets.append(joint)
                referenced.update(a["row"] for a in joint["complete_block_actions"] if a["row"] >= 0)
            referenced.update(a["row"] for a in header_actions if a["row"] >= 0)
            for body, body_actions in [("base_header", header_actions), *[(j["block"], j["complete_block_actions"]) for j in packets]]:
                for action in body_actions:
                    if action["row"] < 0:
                        continue
                    row = rows[action["row"]]
                    ownership = row["ownership"]
                    require(row["row"] == action["row"] and row["row_id"] == action["source_id"] and ownership["role"] == action["role"], "raw action identity differs")
                    other = ownership["second_body"] if body == ownership["first_body"] else ownership["first_body"]
                    require(body in (ownership["first_body"], ownership["second_body"]) and other == action["other_body"], "raw receiver ownership differs")
                    sign = 1 if body == ownership["first_body"] else -1
                    require(np.max(np.abs(np.array(action["force_n"]) - sign * raw[action["row"]] * np.array(ownership["direction_global_xyz"]))) < 1e-7, "raw signed action join differs")
            case_packets.append({"case_id": case, "complete_header_actions": header_actions, "interfaces": packets,
                                 "axis_states": [s for s in states if s["case_id"] == case], "placements": [p for p in placements if p["case_id"] == case]})
            debug["completed_case_ids"] = [packet["case_id"] for packet in case_packets]
    cells = {cell["name"]: cell for cell in read(ADAPTER)["contact_cell_ownership"]}
    patches = read(CONTACTS)["contact_patches"]
    selected_cells, selected_patches = {}, {}
    for index in sorted(referenced):
        row = rows[index]
        if row["ownership"]["role"] != "timber_or_panel_contact":
            continue
        cell = cells[row["row_id"]]
        patch_index = cell["source_patch_index"]
        patch = patches[patch_index]
        require({cell["first"], cell["second"]} == set(patch["member_ids"]) == {row["ownership"]["first_body"], row["ownership"]["second_body"]}, "contact patch receiver join differs")
        sign = 1 if cell["first"] == row["ownership"]["first_body"] else -1
        require(np.max(np.abs(np.array(cell["normal_xyz"]) * sign - row["ownership"]["direction_global_xyz"])) < 1e-8
                and np.max(np.abs(np.array(cell["point_xyz_mm"]) - row["ownership"]["point_mm"])) < 1e-8, "contact cell point or signed normal differs")
        selected_cells[row["row_id"]], selected_patches[str(patch_index)] = cell, patch
    authenticate(pins)
    write(output / "model.json", {"schema": "header_local_transfer_frozen_geometry/v1", "bodies": bodies,
          "source_identity": {key: model[key] for key in ("candidate", "source_revision", "development_revision")},
          "header_connections": [connections[axis] for axis in sorted(axis_ids)], "saved_header_sections": sections,
          "contact_cells": selected_cells, "contact_patches_by_global_source_index": selected_patches, **FLAGS})
    write(output / "inputs.json", {"schema": "header_local_transfer_frozen_actions/v1", "cases": case_packets,
          "referenced_raw_rows": {str(index): rows[index] for index in sorted(referenced)}, "existing_header_evidence": checks,
          "source_whole_body_balances": actions["whole_body_balances"], "source_force_state_scope": checks["source_force_state_scope"],
          "unavailable_design_resistances": {"Ft_perpendicular_mpa": None, "F90_design_resistance_n": None},
          "recorded_gap_H": duties["requirements"]["H"], "inherited_source_pins_provenance_only": inherited, **FLAGS})
    shutil.copyfile(HEADER / "header-sections.csv", output / "header-sections.csv")
    require(sha(output / "header-sections.csv") == pins[HEADER / "header-sections.csv"], "section byte copy differs")
    return {"bodies": 7, "cases": 6, "axes": 12, "axis_states": 72, "interfaces": 36, "actions_per_interface_each_receiver": 10,
            "complete_header_actions_per_case": 394, "header_sections": 105, "section_states": 1260,
            "disconnected_sections": 6, "referenced_raw_rows": len(referenced), "contact_cells": len(selected_cells)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    owned = (HERE / "rawlocal/header-local-transfer").resolve()
    require(output != owned and output.is_relative_to(owned), f"output must be a fresh child of {owned}")
    require(not output.exists(), f"output already exists: {output}")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__).resolve())}
    counts, failure, debug = {}, None, {"stage": "source-authentication", "completed_case_ids": []}
    try:
        authenticate(pins)
        counts = prepare(output, pins, debug)
        authenticate(pins)
    except (ValueError, KeyError, TypeError, OSError, RuntimeError) as error:
        failure = {"error": str(error), "partial_progress": debug, "mechanical_incompatibility_proved": False}
    status = "STOP_HEADER_INPUT_CONTRACT" if failure else "PREPARED_HEADER_INPUT_CONTRACT_FOR_METHOD_SELECTION"
    sources = {str(path.relative_to(ROOT)): digest for path, digest in sorted(pins.items())}
    artifacts = {path.name: sha(path) for path in output.iterdir() if path.is_file()}
    write(output / "receipt.json", {"schema": "header_local_transfer_preparation/v1", "status": status,
          "counts": counts, "source_sha256": sources, "output_sha256": artifacts, "failure": failure,
          "source_chain_scope": "Only directly consumed artifacts and seven STEP bindings are authenticated. Inherited mutable producer pins remain provenance.",
          "limits": ["Prepared inputs preserve the original 100 mm force-lever, nominal-gap simultaneous actions; no load or geometry change.",
                     "Ceg, Cg, contact and section results remain preserved evidence. No new splitting, torque, oblique-group, Ft-perpendicular or F90 resistance is assigned.",
                     "Pair null directions and disconnected-section null references remain unchanged. No stress, force redistribution or local compatibility result is calculated.",
                     "Saved point actions and free couples are the analytical row representation; shared tie points need not coincide with each physical head/nut bearing face. Future traction mapping must preserve the wrench while locating the supported seats.",
                     "Finished surfaces and STEP files are saved geometric evidence, not delivered-stock inspection. Native readiness and complete joint acceptance remain false."],
          "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}, **FLAGS})
    artifacts["receipt.json"] = sha(output / "receipt.json")
    write(output / "source-pins.json", {"source_sha256": sources, "output_sha256": artifacts, **FLAGS})
    print(json.dumps({"status": status, "receipt_sha256": artifacts["receipt.json"], "counts": counts}))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
