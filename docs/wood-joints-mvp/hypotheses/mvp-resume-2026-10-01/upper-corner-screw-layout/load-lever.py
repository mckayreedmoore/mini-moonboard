"""Prepare six 50 mm front-face force-lever cases from frozen 100 mm operators.

Only the applied live-load nodal couples and their elastic/rigid load columns
change. This producer reads saved stiffness and does not run a frame or native
solver, assemble stiffness, change geometry, or qualify a physical load lever.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = HERE / "operators-attempt02"
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
LOADS = BASE / "current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json"
SOURCE_MODEL = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
NATIVE = BASE / "current-frame-pure-solid-matrix-export-native-attempt01"
PARSER = BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
CONDENSATION = BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py"
QUOTIENT = BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py"
REFINEMENT = BASE / "current-bordered-refinement-diagnostic-attempt01/bounded_refinement.py"
PINS = {
    SOURCE / "operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    SOURCE / "model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    SOURCE / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    SOURCE / "model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    SOURCE / "operator-assessment.json": "1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a",
    HERE / "load_components.py": "3e7152b5e035e702178a08327df94353e5d77066fba623de71ac9bc05acfd3b8",
    LOADS: "9cd59d7bbafd65c740d2b0200e3dd88a6a49e6dca0bead0a38bc7826e337548c",
    ROOT / "fea/horizontal_panel_frame.py": "9ac5ceb2bd76ffddb6c048f92e54082a4672d72aab635ba2230e4352253378d9",
    ROOT / "fea/vertical_panel_comparison.py": "e3079c6d82219ccc255905a38f4b61bb0354bfd52454f490b1590dc8fa0e79ea",
    REFINEMENT: "ee23cf09dc89b6a4c6581ea86379e0749c2c6559478da1e2f95a8a0b8b599c4e",
}
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
FORCE_REPLAY_TOLERANCE, E_REPLAY_TOLERANCE, W_REPLAY_TOLERANCE = 1e-5, 1e-8, 1e-7
WRENCH_FORCE_TOLERANCE, WRENCH_MOMENT_TOLERANCE = 1e-5, 1e-5


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def array_sha(array):
    value = np.asarray(array)
    digest = hashlib.sha256(f"{value.dtype.str}:{value.shape}".encode())
    digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, f"frozen source differs: {path}")


def pure_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"pure source helper unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bind_sources():
    pins = dict(PINS)
    authenticate(pins)
    assessment = read(SOURCE / "operator-assessment.json")
    require(assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS", "current source operators are incomplete")
    for path, digest in ((ROOT / relative, digest) for relative, digest in assessment["source_sha256"].items()):
        require(path not in pins or pins[path] == digest, "assessment source pins conflict")
        pins[path] = digest
    for relative, digest in assessment["output_sha256"].items():
        path = SOURCE / relative
        require(path not in pins or pins[path] == digest, "assessment output pins conflict")
        pins[path] = digest
    require(all(path in pins for path in (PARSER, CONDENSATION, QUOTIENT, SOURCE_MODEL, NATIVE / "model.sti", NATIVE / "model.dof")),
            "assessment omits a consumed baseline stiffness or quotient helper")
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    authenticate(pins)
    return assessment, pins


def wrench(positions, values, reference):
    return np.r_[np.sum(values, axis=0), np.sum(np.cross(positions - reference, values), axis=0)]


def wrench_error(actual, expected, context):
    force_error = float(np.max(np.abs(actual[:3] - expected[:3])))
    moment_error = float(np.max(np.abs(actual[3:] - expected[3:])))
    require(force_error < WRENCH_FORCE_TOLERANCE and moment_error < WRENCH_MOMENT_TOLERANCE,
            f"{context}: force or moment reconstruction differs")
    return {"force_error_n": force_error, "moment_error_nmm": moment_error,
            "actual_force_xyz_n": actual[:3].tolist(), "actual_moment_xyz_nmm": actual[3:].tolist()}


def patch_loads(traction_wrench, cases, saved_cases, coordinates, row_for, source_live, debug):
    original = np.zeros_like(source_live)
    saved_raw = np.zeros_like(source_live)
    delta = np.zeros_like(source_live)
    reports = []
    tangent = np.array([0.0, np.cos(np.deg2rad(50)), np.sin(np.deg2rad(50))])
    for index, (case, saved) in enumerate(zip(cases, saved_cases, strict=True)):
        require(case["case_id"] == saved["case_id"] == CASES[index], "saved six-case order differs")
        load = case["source_applied_load"]
        nodes = [int(node) for node in saved["climber_nodal_map"]]
        require(len(nodes) == 8 and len(set(nodes)) == 8, "expected the same eight-node surface patch")
        positions = np.array([coordinates[node] for node in nodes])
        center = np.array(load["patch_center_global_xyz_mm"])
        reference = np.array(load["wrench_reference_point_global_xyz_mm"])
        old_point = np.array(load["force_application_point_global_xyz_mm"])
        force = np.array(load["applied_force_global_xyz_n"])
        require(abs(force[2] + 2224.11080763025) < 1e-10 and abs(np.linalg.norm(force[:2]) - 300.0) < 1e-10,
                "the frozen 250 lb times two or signed horizontal force differs")
        require(load["case_inputs"]["pounds"] == 250.0 and load["case_inputs"]["dynamic_factor"] == 2.0,
                "the source live-load scale differs")
        relative = positions - center
        x, t = np.abs(relative[:, 0]), np.abs(relative @ tangent)
        corner = (np.abs(x - 10) < 1e-5) & (np.abs(t - 10) < 1e-5)
        middle = ((x < 1e-5) & (np.abs(t - 10) < 1e-5)) | ((t < 1e-5) & (np.abs(x - 10) < 1e-5))
        require(np.count_nonzero(corner) == 4 and np.count_nonzero(middle) == 4, "saved patch is not the complete S8 square")
        weights = np.where(corner, -1/12, 1/3)
        lever, face_offset = old_point - center, center - reference
        require(abs(np.linalg.norm(lever) - 100.0) < 1e-8 and abs(np.linalg.norm(face_offset) - 9.128125) < 1e-8,
                "front-face lever or retained face/reference offset differs")
        require(np.linalg.norm(np.cross(lever/100.0, face_offset)) < 1e-8, "face/reference offset is not along the source lever")
        original_values = traction_wrench(positions, weights, force, np.cross(lever, force), center)
        saved_values = np.array([saved["climber_nodal_map"][str(node)] for node in nodes])
        saved_error = float(np.max(np.abs(original_values - saved_values)))
        require(saved_error < FORCE_REPLAY_TOLERANCE, "saved S8 nodal map was not reproduced")
        old_reference_moment = np.cross(old_point - reference, force)
        require(np.max(np.abs(old_reference_moment - load["moment_global_xyz_nmm"])) < WRENCH_MOMENT_TOLERANCE,
                "source reference moment was not reproduced")
        new_point = center + 0.5*lever
        new_values = traction_wrench(positions, weights, force, np.cross(new_point - center, force), center)
        delta_moment = np.cross(new_point - old_point, force)
        original_checks = wrench_error(wrench(positions, original_values, reference), np.r_[force, old_reference_moment], "original local patch")
        target_checks = wrench_error(wrench(positions, new_values, reference), np.r_[force, np.cross(new_point - reference, force)], "target local patch")
        for node, old, saved_value, new in zip(nodes, original_values, saved_values, new_values, strict=True):
            for direction in (1, 2, 3):
                row = row_for[(node, direction)]
                original[row, index] = old[direction - 1]
                saved_raw[row, index] = saved_value[direction - 1]
                delta[row, index] = new[direction - 1] - old[direction - 1]
        reports.append({"case_id": case["case_id"], "loaded_panel": case["loaded_panel"], "patch_nodes": nodes,
                        "S8_signed_weights": weights.tolist(), "original_nodal_map_error_n": saved_error,
                        "patch_center_xyz_mm": center.tolist(), "wrench_reference_xyz_mm": reference.tolist(),
                        "front_face_to_reference_offset_xyz_mm": face_offset.tolist(), "front_face_to_reference_offset_mm": float(np.linalg.norm(face_offset)),
                        "original_force_point_xyz_mm": old_point.tolist(), "target_force_point_xyz_mm": new_point.tolist(),
                        "original_front_face_lever_xyz_mm": lever.tolist(), "target_front_face_lever_xyz_mm": (new_point - center).tolist(),
                        "original_front_face_lever_mm": float(np.linalg.norm(lever)), "target_front_face_lever_mm": float(np.linalg.norm(new_point - center)),
                        "force_xyz_n": force.tolist(), "original_moment_at_reference_xyz_nmm": old_reference_moment.tolist(),
                        "target_moment_at_reference_xyz_nmm": np.cross(new_point - reference, force).tolist(),
                        "delta_moment_xyz_nmm": delta_moment.tolist(), "original_local_wrench_check": original_checks,
                        "target_local_wrench_check": target_checks})
        debug.update({"stage": "patch-reconstruction", "case_reports": reports})
    source_error = float(np.max(np.abs(original - source_live)))
    saved_error = float(np.max(np.abs(saved_raw - source_live)))
    require(source_error < FORCE_REPLAY_TOLERANCE and saved_error < FORCE_REPLAY_TOLERANCE,
            "complete original live F columns were not reproduced")
    debug.update({"original_F_error_n": source_error, "saved_map_F_error_n": saved_error})
    return source_live + delta, reports


def panel_responses(parser, helper, quotient, model, operators, target_live, debug):
    source = parser.load_frame_source_model(SOURCE_MODEL)
    require(list(source["bodies"]) == model["body_names"], "baseline stiffness body ordering differs")
    labels = parser.parse_dof_file(NATIVE / "model.dof")
    row_for = {label: index for index, label in enumerate(labels)}
    owners = np.array([source["owner_by_node"][node] for node, _direction in labels])
    parsed = parser.parse_upper_triangle_file(NATIVE / "model.sti", len(labels), owner_by_row=owners, owner_names=model["body_names"])
    parser.require_no_cross_body_coupling(parsed)
    stiffness = parsed["matrix"]
    projection = sparse.load_npz(SOURCE / "B.npz").tocsr()
    coordinates = {int(node): np.array(point) for node, point in model["physical_node_coordinates_mm"].items()}
    require(projection.shape == (operators["e"].shape[0], len(labels)), "current B dimensions differ")
    old_e, target_e = np.zeros_like(operators["e"][:, 1::2]), np.zeros_like(operators["e"][:, 1::2])
    old_w, target_w = np.zeros_like(operators["W"][:, 1::2]), np.zeros_like(operators["W"][:, 1::2])
    bodies = sorted({case["loaded_panel"] for case in read(SOURCE / "model-inputs.json")["cases"]})
    require(bodies == ["main_lower_left", "main_upper_left", "main_upper_right"], "loaded-panel census differs")
    reports = []
    for body in bodies:
        body_id = model["body_names"].index(body)
        dofs = np.flatnonzero(owners == body_id)
        body_labels = [labels[int(index)] for index in dofs]
        require(all(np.array_equal(coordinates[node], source["coordinates"][node]) for node, _direction in body_labels),
                "a loaded panel's source coordinates changed")
        center, rigid, orthonormal = helper.rigid_basis(body_labels, coordinates)
        rigid_error = float(np.max(np.abs(projection[:, dofs] @ rigid - operators["D"][:, 6*body_id:6*body_id + 6])))
        require(rigid_error < 1e-8, "current B rigid projection differs from frozen D")
        raw = np.column_stack((operators["F"][dofs, 1::2], target_live[dofs]))
        elastic = raw - orthonormal @ (orthonormal.T @ raw)
        body_stiffness = stiffness[dofs][:, dofs].tocsr()
        debug.update({"stage": "panel-quotient", "body": body, "body_reports": reports})
        factor, system = helper.factor_bordered(body_stiffness, rigid)
        solved = quotient.solve_quotient_chunk(factor, system, body_stiffness, rigid, elastic)
        report = {"body": body, "physical_dofs": len(dofs), "raw_rhs_columns": 12, "datum_xyz_mm": center.tolist(),
                  "current_B_D_rigid_map_error": rigid_error,
                  **{key: solved.get(key) for key in ("status", "KKT_upper_force_residual_relative",
                      "projected_elastic_force_residual_relative", "max_gauge_R_transpose_u_mm", "corrections", "refinement_stop_reason", "failed_gates")}}
        reports.append(report)
        debug["body_reports"] = reports
        require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, f"{body}: {solved['status']}")
        response = projection[:, dofs] @ solved["displacement_mm"]
        old_e += response[:, :6]
        target_e += response[:, 6:]
        old_w[6*body_id:6*body_id + 6] = rigid.T @ raw[:, :6]
        target_w[6*body_id:6*body_id + 6] = rigid.T @ raw[:, 6:]
    e_error = float(np.max(np.abs(old_e - operators["e"][:, 1::2])))
    w_error = float(np.max(np.abs(old_w - operators["W"][:, 1::2])))
    debug.update({"stage": "original-operator-replay", "original_e_error_mm": e_error, "original_W_error_scaled_n": w_error})
    require(e_error < E_REPLAY_TOLERANCE and w_error < W_REPLAY_TOLERANCE, "complete original live e/W were not reproduced")
    return target_e - old_e, target_w - old_w, labels, row_for, reports


def update_metadata(inputs, reports):
    result = copy.deepcopy(inputs)
    for case, report in zip(result["cases"], reports, strict=True):
        load, delta = case["source_applied_load"], np.array(report["delta_moment_xyz_nmm"])
        load["force_application_point_global_xyz_mm"] = report["target_force_point_xyz_mm"]
        load["moment_global_xyz_nmm"] = report["target_moment_at_reference_xyz_nmm"]
        target = [entry for entry in case["body_external_wrenches"] if entry["member_id"] == case["loaded_panel"]]
        require(len(target) == 1, "loaded panel external-wrench metadata is ambiguous")
        target[0]["assigned_external_moment_xyz_nmm"] = (np.array(target[0]["assigned_external_moment_xyz_nmm"]) + delta).tolist()
        case["including_deferred_hardware_moment_about_origin_xyz_nmm"] = (
            np.array(case["including_deferred_hardware_moment_about_origin_xyz_nmm"]) + delta).tolist()
    restored = copy.deepcopy(result)
    for old_case, case in zip(inputs["cases"], restored["cases"], strict=True):
        case["source_applied_load"]["force_application_point_global_xyz_mm"] = old_case["source_applied_load"]["force_application_point_global_xyz_mm"]
        case["source_applied_load"]["moment_global_xyz_nmm"] = old_case["source_applied_load"]["moment_global_xyz_nmm"]
        for old, new in zip(old_case["body_external_wrenches"], case["body_external_wrenches"], strict=True):
            if old["member_id"] == old_case["loaded_panel"]:
                new["assigned_external_moment_xyz_nmm"] = old["assigned_external_moment_xyz_nmm"]
        case["including_deferred_hardware_moment_about_origin_xyz_nmm"] = old_case["including_deferred_hardware_moment_about_origin_xyz_nmm"]
    require(restored == inputs, "metadata outside the declared force points and moments changed")
    return result


def global_checks(model, operators, old_operators, labels, row_for, reports):
    coordinates = {int(node): np.array(point) for node, point in model["physical_node_coordinates_mm"].items()}
    centers = np.array([np.mean([coordinates[int(node)] for node in sorted(set(model["body_nodes"][body]))], axis=0)
                        for body in model["body_names"]])
    nodes = sorted({node for node, _direction in labels})
    dofs = np.array([[row_for[(node, direction)] for direction in (1, 2, 3)] for node in nodes])
    positions = np.array([coordinates[node] for node in nodes])
    for index, report in enumerate(reports):
        force = np.array(report["force_xyz_n"])
        old_point, new_point = np.array(report["original_force_point_xyz_mm"]), np.array(report["target_force_point_xyz_mm"])
        for role, values, point in (("original", old_operators, old_point), ("target", operators, new_point)):
            work = values["W"][:, 2*index + 1].reshape(-1, 6)
            actual = np.r_[work[:, :3].sum(axis=0), (1000*work[:, 3:] + np.cross(centers, work[:, :3])).sum(axis=0)]
            report[role + "_global_W_wrench_check"] = wrench_error(actual, np.r_[force, np.cross(point, force)], role + " global W")
            actual_f = wrench(positions, values["F"][dofs, 2*index + 1], np.zeros(3))
            report[role + "_global_F_wrench_check"] = wrench_error(actual_f, np.r_[force, np.cross(point, force)], role + " global F")
        report["operator_live_nodal_delta_maximum_n"] = float(np.max(np.abs(
            operators["F"][:, 2*index + 1] - old_operators["F"][:, 2*index + 1])))


def prepare(output, assessment, pins, debug):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    traction_wrench = importlib.import_module("fea.horizontal_panel_frame").traction_wrench
    parser = pure_module(PARSER, "force_lever_parser")
    helper = pure_module(CONDENSATION, "force_lever_condensation")
    quotient = pure_module(QUOTIENT, "force_lever_quotient")
    model, inputs, saved = read(SOURCE / "model.json"), read(SOURCE / "model-inputs.json"), read(LOADS)
    require([case["case_id"] for case in inputs["cases"]] == CASES, "current six-case order differs")
    labels = parser.parse_dof_file(NATIVE / "model.dof")
    row_for = {label: index for index, label in enumerate(labels)}
    coordinates = {int(node): np.array(point) for node, point in model["physical_node_coordinates_mm"].items()}
    with np.load(SOURCE / "operators.npz", allow_pickle=False) as data:
        original = {key: data[key].copy() for key in data.files}
    require(original["F"].shape == (len(labels), 12) and original["e"].shape[1] == original["W"].shape[1] == 12,
            "source live/gravity column census differs")
    target_live, reports = patch_loads(traction_wrench, inputs["cases"], saved["cases"], coordinates, row_for, original["F"][:, 1::2], debug)
    delta_e, delta_w, labels, row_for, body_reports = panel_responses(parser, helper, quotient, model, original, target_live, debug)
    # Replay gates above precede the operator update. Retain baseline solve
    # rounding in e/W and F; introduce only the computed live-load difference.
    operators = {key: value.copy() for key, value in original.items()}
    operators["F"][:, 1::2] = target_live
    operators["e"][:, 1::2] += delta_e
    operators["W"][:, 1::2] += delta_w
    untouched = {}
    for key, value in operators.items():
        old, new = (original[key][:, 0::2], value[:, 0::2]) if key in ("F", "e", "W") else (original[key], value)
        require(array_sha(old) == array_sha(new), f"an unchanged array or gravity column changed: {key}")
        untouched[key + ("/gravity_columns" if key in ("F", "e", "W") else "")] = array_sha(old)
    new_inputs = update_metadata(inputs, reports)
    global_checks(model, operators, original, labels, row_for, reports)
    connections_hash = fingerprint(inputs["connections"])
    require(fingerprint(new_inputs["connections"]) == connections_hash, "connection geometry or laws changed")
    scope = {"scenario": "hypothetical_50mm_front_face_force_lever", "original_front_face_lever_mm": 100.0,
             "target_front_face_lever_mm": 50.0, "retained_front_face_to_reference_offset_mm": 9.128125,
             "weight_lb": 250.0, "dynamic_force_multiplier": 2.0, "vertical_live_force_n": 2224.11080763025,
             "signed_horizontal_force_magnitude_n": 300.0, "same_patch_nodes_and_area_weights": True,
             "gravity_and_accessory_loads_unchanged": True, "all_six_force_resultants_preserved": True,
             "physical_hold_standoff_qualified": False, "original_single_hold_requirement_replaced": False,
             "original_replay_gate_precedes_operator_update": True, "case_reports": reports}
    new_model = copy.deepcopy(model)
    new_model["diagnostic_load_scenario"] = scope
    new_inputs["diagnostic_load_scenario"] = scope
    require({key: value for key, value in new_model.items() if key != "diagnostic_load_scenario"} == model,
            "current model geometry or identities changed")
    authenticate(pins)
    np.savez_compressed(output / "operators.npz", **operators)
    for name in ("B.npz", "row-identities.json"):
        shutil.copyfile(SOURCE / name, output / name)
        require(sha(output / name) == pins[SOURCE / name], f"byte-copied {name} differs")
    write(output / "model.json", new_model)
    write(output / "model-inputs.json", new_inputs)
    debug.update({"stage": "prepared", "case_reports": reports, "body_reports": body_reports})
    return {"diagnostic_load_scenario": scope, "body_reports": body_reports,
            "original_F_error_n": debug["original_F_error_n"], "original_saved_map_F_error_n": debug["saved_map_F_error_n"],
            "original_e_error_mm": debug["original_e_error_mm"], "original_W_error_scaled_n": debug["original_W_error_scaled_n"],
            "unchanged_array_sha256": untouched, "unchanged_connections_sha256": connections_hash,
            "unchanged_geometry_payload_sha256": fingerprint(model),
            "unchanged_file_sha256": {name: sha(output / name) for name in ("B.npz", "row-identities.json")},
            "modeled_mass_kg": assessment["modeled_mass_kg"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    require(not output.exists(), f"output already exists: {output}")
    assessment, pins = bind_sources()
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    source_pins = {str(path.relative_to(ROOT)): digest for path, digest in sorted(pins.items())}
    write(output / "inputs.json", {"producer_sha256": pins[Path(__file__).resolve()], "source_sha256": source_pins,
                                   "case_ids": CASES, "native_launch": False, "geometry_changed": False})
    result, failure, debug = {}, None, {"stage": "preparation-start"}
    try:
        result = prepare(output, assessment, pins, debug)
        authenticate(pins)
    except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
        failure = {"error": str(error), "last_completed_stage": debug, "incompatibility_proved": False}
    status = "STOP_LOAD_LEVER_PREPARATION" if failure else "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
    receipt = {"schema": "front_face_force_lever_preparation/v1", "status": status, "case_ids": CASES,
               "derived_from_operator_assessment_schema": assessment["schema"],
               "counts": {"source_cases": 6, "loaded_panels": 3, "quotient_rhs_per_panel": 12,
                          "completed_preparation": int(failure is None)}, **result, "failure": failure,
               "source_sha256": source_pins, "producer_sha256": pins[Path(__file__).resolve()],
               "criteria": {"original_F_error_n_strictly_below": FORCE_REPLAY_TOLERANCE,
                            "original_e_error_mm_strictly_below": E_REPLAY_TOLERANCE,
                            "original_W_error_scaled_n_strictly_below": W_REPLAY_TOLERANCE,
                            "wrench_force_error_n_strictly_below": WRENCH_FORCE_TOLERANCE,
                            "wrench_moment_error_nmm_strictly_below": WRENCH_MOMENT_TOLERANCE},
               "limits": ["This packet prepares one declared 50 mm front-face lever sensitivity for six unchanged resultant forces. It is not a physical hold measurement or a replacement of the original load requirement.",
                          "The front-face/reference offset stays 9.128125 mm; reference moments are recomputed from the target force point rather than halving the entire original reference moment.",
                          "Saved native stiffness and current B are consumed only for the three loaded panel quotient responses. No stiffness, material, geometry, axes, connections or contact law is recomputed.",
                          "All arrays outside odd live F/e/W columns and all even gravity columns remain bitwise equal. B and row identities are byte copies of the current packet.",
                          "Baseline solve/nodal rounding is retained through a computed target-minus-original live-load update. Original replay checks precede the operator update.",
                          "The quotient method uses its unchanged original-factor audit and bounded corrections. No relaxed criteria, frame/native solve, CAD operation or physical release is introduced."],
               "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
               "native_solve_run": False, "frame_solve_run": False, "geometry_changed": False,
               "complete_joint_acceptance": False, "physical_release": False}
    write(output / "receipt.json", receipt)
    artifacts = {path.name: sha(path) for path in output.iterdir() if path.is_file()}
    record = {"schema": "declared_front_face_force_lever/v1", "status": status,
              "derived_from_operator_assessment_schema": assessment["schema"],
              "producer_sha256": pins[Path(__file__).resolve()], "source_sha256": source_pins,
              "output_sha256": artifacts, "modeled_mass_kg": assessment["modeled_mass_kg"],
              "diagnostic_load_scenario": result.get("diagnostic_load_scenario"), "failure": failure,
              "native_solve_run": False, "native_launch": False, "geometry_changed": False,
              "complete_joint_acceptance": False, "physical_release": False}
    write(output / "operator-assessment.json", record)
    artifacts["operator-assessment.json"] = sha(output / "operator-assessment.json")
    write(output / "source-pins.json", {"source_sha256": source_pins, "output_sha256": artifacts,
                                       "complete_joint_acceptance": False, "physical_release": False})
    authenticate(pins)
    print(json.dumps({"status": status, "operator_assessment_sha256": artifacts["operator-assessment.json"], "case_count": 6}))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
