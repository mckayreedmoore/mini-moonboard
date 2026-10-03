"""Evaluate six frozen upper-left block cases with separate shared host poses."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import scipy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAIL_PAIR = HERE / "upper-right-rail-pair.py"
SIDE_PAIR = HERE / "upper-right-side-pair.py"
MODEL = HERE / "operators-attempt02/model.json"
MODEL_INPUTS = HERE / "operators-attempt02/model-inputs.json"
OPERATOR_ASSESSMENT = HERE / "operators-attempt02/operator-assessment.json"
ROWS = HERE / "operators-attempt02/row-identities.json"
OPERATORS = HERE / "operators-attempt02/operators.npz"
COMPARISON = HERE / "frame-250-attempt02/comparison.json"
RESPONSE = HERE / "frame-250-attempt02/response.npz"
COMPONENT = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
CLEAT = "top_outer_left_cleat"
COMMON_FORCE_TOLERANCE_N = 0.001
COMMON_MOMENT_TOLERANCE_NMM = 0.2
SOURCE_FORCE_TOLERANCE_N = 1e-6
SOURCE_MOMENT_TOLERANCE_NMM = 1e-6

PINS = {
    RAIL_PAIR: "4243b53bbb7377753f0b1fdd73fa1aa6c80e1a96c99d428def88e82a899e6f96",
    SIDE_PAIR: "ce07e9489d96fb251ee780ecb96cdbb38539b5d204922a74c39066095d9ac0cc",
    MODEL: "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    MODEL_INPUTS: "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    OPERATOR_ASSESSMENT: "1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    OPERATORS: "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    COMPARISON: "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    RESPONSE: "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    COMPONENT: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
}

HOSTS = [
    {
        "key": "rail",
        "host": "base_rail_top",
        "axes": [
            "top_outer/clip_single_top_left_1/rail_1",
            "top_outer/clip_single_top_left_1/rail_2",
        ],
        "expected_rows": list(range(1800, 1804)) + list(range(1834, 1852)),
        "host_length_mm": 38.1,
        "cleat_length_mm": 139.7,
        "washer_id_mm": 8.3058,
        "washer_od_mm": 18.4658,
        "flat_radius_mm": 5.0,
        "reference_axis": [1.0, 0.0, 0.0],
    },
    {
        "key": "side",
        "host": "base_side_left",
        "axes": [
            "top_outer/clip_single_top_left_1/side_1",
            "top_outer/clip_single_top_left_1/side_2",
        ],
        "expected_rows": list(range(1804, 1808)) + list(range(1816, 1834)),
        "host_length_mm": 88.9,
        "cleat_length_mm": 88.9,
        "washer_id_mm": 9.906,
        "washer_od_mm": 22.0472,
        "flat_radius_mm": 6.0,
        "reference_axis": [0.0, 0.0, 1.0],
    },
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def import_private(path, module_name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(module_name, path)
    require(spec is not None and spec.loader is not None, f"private helper unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cross(left, right):
    return np.cross(np.asarray(left, dtype=float), np.asarray(right, dtype=float))


def shift_wrench(wrench, from_datum, to_datum):
    value = np.asarray(wrench, dtype=float)
    force = value[:3]
    moment = value[3:] + cross(np.asarray(from_datum) - np.asarray(to_datum), force)
    return np.r_[force, moment]


def axis_groups(model):
    matches = [record for record in model["proposed_corner_axes"] if record["block"] == CLEAT]
    require(len(matches) == 1, "upper-left cleat axis group differs")
    return {record["axis_id"]: record for record in matches[0]["axes"]}


def source_pins():
    pins = dict(PINS)
    pins[HERE / "upper-right-combined-transfer.py"] = "fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0"
    for path, expected in pins.items():
        require(sha(path) == expected, f"frozen source differs: {path}")
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    return pins


def common_cleat_datum(model):
    coordinates = model["physical_node_coordinates_mm"]
    nodes = sorted(set(model["body_nodes"][CLEAT]))
    require(nodes, "upper-left cleat has no source solid nodes")
    points = np.array([coordinates[str(node)] for node in nodes], dtype=float)
    return np.mean(points, axis=0), len(nodes)


def configure_group(definition, model, identities, comparison, component):
    host = definition["host"]
    axes = definition["axes"]
    selected = sorted(
        (
            row
            for row in identities
            if {row["ownership"]["first_body"], row["ownership"]["second_body"]} == {host, CLEAT}
        ),
        key=lambda row: row["row"],
    )
    require([row["row"] for row in selected] == definition["expected_rows"], f"{host} source row census differs")
    require(all(row["ownership"]["first_body"] == host and row["ownership"]["second_body"] == CLEAT for row in selected),
            f"{host} current row ownership differs")
    face = [row for row in selected if row["ownership"]["role"] == "timber_or_panel_contact"]
    ties = [row for row in selected if row["ownership"]["role"] == "physical_bolt_outer_seat_tension"]
    require(len(face) == 16 and len(ties) == 2, f"{host} face or tie census differs")
    by_row = {row["row"]: row for row in identities}
    axis_records = axis_groups(model)
    bolt_rows = []
    tie_directions = []
    for number, axis_id in enumerate(axes):
        geometry = axis_records[axis_id]
        require(geometry["wood_grip_mm"] == 177.8, f"{axis_id} wood grip differs")
        lateral = [
            row for row in selected
            if row["row_id"].rpartition("/")[0] == axis_id
            and row["ownership"]["role"] == "candidate_bolt_lateral_plane"
        ]
        tie = next((row for row in ties if row["row_id"] == axis_id + "/outer-seat-axial-tie"), None)
        require(len(lateral) == 2 and tie is not None, f"{axis_id} source bolt rows differ")
        require(geometry["nominal_bolt_diameter_mm"] > 0 and geometry["proposed_CAD_bore_envelope_mm"] > geometry["nominal_bolt_diameter_mm"],
                f"{axis_id} bore or diameter source differs")
        require(all(np.allclose(row["ownership"]["point_mm"], lateral[0]["ownership"]["point_mm"], atol=1e-7, rtol=0)
                    for row in lateral), f"{axis_id} lateral planes do not share a station")
        require(np.allclose(tie["ownership"]["point_mm"], lateral[0]["ownership"]["point_mm"], atol=1e-6, rtol=0),
                f"{axis_id} tie and lateral station differ")
        relative_gap = next(
            record["relative_radial_gap_mm"]
            for record in comparison["clearance_planes"]
            if record["plane_id"] == lateral[0]["row_id"]
        )
        tie_direction = np.asarray(tie["ownership"]["direction_global_xyz"], dtype=float)
        require(math.isclose(float(tie_direction @ tie_direction), 1.0, abs_tol=1e-12), f"{axis_id} bolt normal is not unit length")
        tie_directions.append(tie_direction)
        bolt_rows.append({
            "axis_id": axis_id,
            "number": number,
            "interface_point_xyz_mm": list(lateral[0]["ownership"]["point_mm"]),
            "source_component_rows": [row["row"] for row in lateral],
            "source_tie_row": tie["row"],
            "relative_radial_gap_mm": float(relative_gap),
            "geometry": geometry,
        })
    n = tie_directions[0]
    require(all(np.allclose(direction, n, atol=1e-12, rtol=0) for direction in tie_directions),
            f"{host} bolt normals differ")
    basis = np.column_stack((np.asarray(definition["reference_axis"], dtype=float),
                             np.cross(n, np.asarray(definition["reference_axis"], dtype=float))))
    require(np.allclose(basis.T @ basis, np.eye(2), atol=1e-12), f"{host} transverse basis is not orthonormal")
    require(all(np.allclose(row["ownership"]["direction_global_xyz"], -n, atol=1e-10, rtol=0) for row in face),
            f"{host} face normals differ from bolt axis")
    for row in face:
        require(math.isclose(row["law"]["stiffness_N_per_mm"] / row["contact_area_mm2"], 100.0, rel_tol=1e-10),
                f"{host} existing face stiffness differs")
    points = np.array([bolt["interface_point_xyz_mm"] for bolt in bolt_rows], dtype=float)
    datum = np.mean(points, axis=0)
    diameter_values = {record["geometry"]["nominal_bolt_diameter_mm"] for record in bolt_rows}
    bore_values = {record["geometry"]["proposed_CAD_bore_envelope_mm"] for record in bolt_rows}
    grip_values = {record["geometry"]["wood_grip_mm"] for record in bolt_rows}
    gap_values = {record["relative_radial_gap_mm"] for record in bolt_rows}
    require(len(diameter_values) == len(bore_values) == len(grip_values) == len(gap_values) == 1,
            f"{host} nominal bolt group geometry differs")
    diameter = float(next(iter(diameter_values)))
    bore = float(next(iter(bore_values)))
    length = float(next(iter(grip_values)))
    gap = float(next(iter(gap_values))) / 2.0
    require(math.isclose(definition["host_length_mm"] + definition["cleat_length_mm"], length, abs_tol=1e-9),
            f"{host} source grip differs from the preserved receiver lengths")
    require(all(math.isclose(record["relative_radial_gap_mm"], 2 * gap, abs_tol=1e-10) for record in bolt_rows),
            f"{host} receiver gaps differ from saved relative clearance")
    weighted_center = sum(
        row["contact_area_mm2"] * np.asarray(row["ownership"]["point_mm"], dtype=float)
        for row in face
    ) / sum(row["contact_area_mm2"] for row in face)
    require(abs(float(n @ (weighted_center - datum))) <= 1e-6, f"{host} face centroid leaves its interface plane")

    body_index = model["body_names"].index(host)
    coordinates = model["physical_node_coordinates_mm"]
    body_nodes = sorted(set(model["body_nodes"][host]))
    body_datum = np.mean([coordinates[str(node)] for node in body_nodes], axis=0)
    raw_rows = [row["row"] for row in selected]
    source_states = []
    with np.load(OPERATORS, allow_pickle=False) as operators, np.load(RESPONSE, allow_pickle=False) as response:
        dbody = operators["D"][raw_rows, 6 * body_index:6 * body_index + 6]
        for index, row in enumerate(selected):
            require(np.allclose(dbody[index, :3], -np.asarray(row["ownership"]["direction_global_xyz"]), atol=1e-12, rtol=0),
                    f"{host} D translation sign differs from row ownership")
        for case_id in CASES:
            raw = response[case_id + "_gap_raw_force_n"]
            force = -dbody[:, :3].T @ raw[raw_rows]
            moment = -1000 * dbody[:, 3:6].T @ raw[raw_rows] + cross(body_datum - datum, force)
            actions = [np.asarray(row["ownership"]["direction_global_xyz"], dtype=float) * raw[row["row"]]
                       for row in selected]
            point_force = np.sum(actions, axis=0)
            point_moment = sum(
                cross(np.asarray(row["ownership"]["point_mm"], dtype=float) - datum, action)
                for row, action in zip(selected, actions)
            )
            require(np.max(np.abs(force - point_force)) <= 1e-7, f"{host} D and point-force sums differ")
            originals = []
            for bolt in bolt_rows:
                witness = next(
                    record for record in component["states"]
                    if record["case_id"] == case_id and record["axis_id"] == bolt["axis_id"]
                    and record["host"] == host and record["block"] == CLEAT
                )
                host_lateral = sum(
                    np.asarray(by_row[row]["ownership"]["direction_global_xyz"], dtype=float) * raw[row]
                    for row in bolt["source_component_rows"]
                )
                tension = float(raw[bolt["source_tie_row"]])
                require(math.isclose(tension, witness["tension_n"], abs_tol=1e-8)
                        and math.isclose(float(np.linalg.norm(host_lateral)), witness["lateral_n"], abs_tol=1e-8),
                        f"{bolt['axis_id']} original bolt comparison differs")
                originals.append({
                    "axis_id": bolt["axis_id"],
                    "signed_T_n": tension,
                    "V_n": float(witness["lateral_n"]),
                    "signed_plane_components_n": raw[bolt["source_component_rows"]].tolist(),
                    "force_on_host_xyz_n": host_lateral.tolist(),
                })
            source_states.append({
                "case_id": case_id,
                "source_connector_wrench_on_host_n_nmm": np.r_[force, moment].tolist(),
                "external_drive_wrench_n_nmm": (-np.r_[force, moment]).tolist(),
                "D_point_force_residual_n": (force - point_force).tolist(),
                "retained_source_free_couple_nmm": (moment - point_moment).tolist(),
                "source_face_compression_n": float(sum(raw[row["row"]] for row in face)),
                "source_face_cells": [
                    {"row": row["row"], "row_id": row["row_id"],
                     "compression_n": float(raw[row["row"]]),
                     "stiffness_n_per_mm": row["law"]["stiffness_N_per_mm"],
                     "point_xyz_mm": row["ownership"]["point_mm"]}
                    for row in face
                ],
                "source_individual_bolts": originals,
            })

    if host == "base_rail_top":
        require(math.isclose(diameter, 6.35, abs_tol=1e-12) and math.isclose(bore, 7.5, abs_tol=1e-12),
                "left rail hardware envelope differs from the frozen rail model")
    else:
        require(math.isclose(diameter, 7.9375, abs_tol=1e-12) and math.isclose(bore, 9.0, abs_tol=1e-12),
                "left side hardware envelope differs from the frozen side model")

    family = {
        "host_length_mm": definition["host_length_mm"],
        "cleat_length_mm": definition["cleat_length_mm"],
        "diameter_mm": diameter,
        "bore_mm": bore,
        "washer_ID_max_mm": definition["washer_id_mm"],
        "washer_OD_min_mm": definition["washer_od_mm"],
        "flat_radius_mm": definition["flat_radius_mm"],
    }
    return {
        "definition": definition,
        "selected": selected,
        "face": face,
        "bolts": bolt_rows,
        "n": n,
        "basis": basis,
        "datum": datum,
        "body_datum": body_datum,
        "face_centroid": weighted_center,
        "face_area_mm2": float(sum(row["contact_area_mm2"] for row in face)),
        "length": length,
        "diameter": diameter,
        "gap": gap,
        "family": family,
        "sources": source_states,
    }


def configure_mechanics(template, data):
    mechanics = template
    helper = import_private(mechanics.HELPER, "left_" + data["definition"]["key"] + "_contact")
    require((helper.LENGTH, helper.E_BOLT, helper.K_HEAD) == (177.8, 200000.0, 10000.0),
            "frozen local-contact constants differ")
    length, diameter, gap = data["length"], data["diameter"], data["gap"]
    for name, value in {
        "CASES": list(CASES),
        "AXES": [bolt["axis_id"] for bolt in data["bolts"]],
        "HOST": data["definition"]["host"],
        "CLEAT": CLEAT,
        "DATUM": np.asarray(data["datum"], dtype=float),
        "LENGTH": length,
        "DIAMETER": diameter,
        "GAP": gap,
        "KWOOD": 20.0,
        "KHEAD": 10000.0,
        "EBOLT": 200000.0,
        "AREA": math.pi * diameter**2 / 4,
        "AXIAL_COMPLIANCE": length / (200000.0 * math.pi * diameter**2 / 4),
        "FAMILY": dict(data["family"]),
    }.items():
        setattr(mechanics, name, value)
    blocks, cells = mechanics.model_matrices(helper, data["bolts"], data["face"], data["n"], data["basis"])
    return mechanics, helper, blocks, cells


def current_cleat_wrenches(model, model_inputs, assessment, comparison, common_datum):
    require(assessment["dead_load_factor"] == comparison["dead_load_factor"], "dead-load factor differs across source records")
    input_cases = model_inputs["cases"]
    require([case["case_id"] for case in input_cases] == CASES, "model-input case order differs")
    body_index = model["body_names"].index(CLEAT)
    factor = float(comparison["dead_load_factor"])
    output = {}
    with np.load(OPERATORS, allow_pickle=False) as operators:
        generalized = operators["W"]
        require(generalized.shape[0] == 6 * len(model["body_names"]) and generalized.shape[1] == 2 * len(CASES),
                "current W load map dimensions differ")
        for case_index, case_id in enumerate(CASES):
            start = 6 * body_index
            dead = generalized[start:start + 6, 2 * case_index]
            live = generalized[start:start + 6, 2 * case_index + 1]
            body_wrench = factor * np.r_[dead[:3], 1000 * dead[3:]] + np.r_[live[:3], 1000 * live[3:]]
            datum = np.mean([model["physical_node_coordinates_mm"][str(node)]
                             for node in sorted(set(model["body_nodes"][CLEAT]))], axis=0)
            common_wrench = shift_wrench(body_wrench, datum, common_datum)
            output[case_id] = {
                "case_index": case_index,
                "dead_load_factor": factor,
                "current_W_dead_at_cleat_body_datum_n_nmm": (factor * np.r_[dead[:3], 1000 * dead[3:]]).tolist(),
                "current_W_live_at_cleat_body_datum_n_nmm": np.r_[live[:3], 1000 * live[3:]].tolist(),
                "current_W_cleat_applied_wrench_at_common_datum_n_nmm": common_wrench.tolist(),
                "source_formula": "dead_load_factor * operators.W[:, 2*case_index] + operators.W[:, 2*case_index+1]; rotations converted from 1000*theta conjugates, then shifted from the unique source-node mean to the common cleat datum.",
            }
    reference = np.asarray(output[CASES[0]]["current_W_cleat_applied_wrench_at_common_datum_n_nmm"])
    for case_id in CASES[1:]:
        require(np.allclose(output[case_id]["current_W_cleat_applied_wrench_at_common_datum_n_nmm"], reference,
                            atol=1e-8, rtol=0), "current cleat gravity differs between the six saved cases")
    return output


def common_pose(host_state, host_datum, common_datum):
    translation = np.asarray(host_state["host_translation_at_face_datum_xyz_mm"], dtype=float)
    rotation = np.asarray(host_state["host_rotation_xyz_rad"], dtype=float)
    return np.r_[translation + cross(rotation, np.asarray(common_datum) - np.asarray(host_datum)), rotation]


def host_interface_wrench(host_state):
    bolts = np.sum([np.asarray(bolt["wrench_on_host_at_face_datum_n_nmm"], dtype=float)
                    for bolt in host_state["bolts"]], axis=0)
    return bolts + np.asarray(host_state["face_wrench_on_host_at_face_datum_n_nmm"], dtype=float)


def assemble_cleat_case(case_id, host_states, host_data, gravity):
    current_w = np.asarray(gravity[case_id]["current_W_cleat_applied_wrench_at_common_datum_n_nmm"], dtype=float)
    source_on_cleat = np.zeros(6)
    derived_on_cleat = np.zeros(6)
    interfaces = {}
    for host in host_data:
        group = host_data[host]
        state = host_states[host]
        source = next(record for record in group["sources"] if record["case_id"] == case_id)
        source_host = np.asarray(source["source_connector_wrench_on_host_n_nmm"], dtype=float)
        source_common = shift_wrench(source_host, group["datum"], COMMON_DATUM)
        derived_host = host_interface_wrench(state)
        derived_common = shift_wrench(derived_host, group["datum"], COMMON_DATUM)
        source_cleat = -source_common
        derived_cleat = -derived_common
        source_on_cleat += source_cleat
        derived_on_cleat += derived_cleat
        interfaces[host] = {
            "host_interface_datum_xyz_mm": np.asarray(group["datum"]).tolist(),
            "host_pose_at_common_cleat_datum_xyz_mm_rad": common_pose(state, group["datum"], COMMON_DATUM).tolist(),
            "source_wrench_on_host_at_common_cleat_datum_n_nmm": source_common.tolist(),
            "derived_wrench_on_host_at_common_cleat_datum_n_nmm": derived_common.tolist(),
            "source_interface_wrench_on_cleat_at_common_datum_n_nmm": source_cleat.tolist(),
            "derived_interface_wrench_on_cleat_at_common_datum_n_nmm": derived_cleat.tolist(),
            "source_vs_derived_host_wrench_residual_n_nmm": (derived_common - source_common).tolist(),
        }
    source_residual = current_w + source_on_cleat
    derived_residual = current_w + derived_on_cleat
    require(np.max(np.abs(source_residual[:3])) <= SOURCE_FORCE_TOLERANCE_N
            and np.max(np.abs(source_residual[3:])) <= SOURCE_MOMENT_TOLERANCE_NMM,
            "source full-cleat wrench does not balance the current applied W")
    require(np.max(np.abs(derived_residual[:3])) <= 2 * COMMON_FORCE_TOLERANCE_N
            and np.max(np.abs(derived_residual[3:])) <= 2 * COMMON_MOMENT_TOLERANCE_NMM,
            "derived whole-cleat wrench exceeds the summed local balance tolerances")
    return {
        "host_interfaces": interfaces,
        "current_W_cleat_applied_wrench_at_common_datum_n_nmm": current_w.tolist(),
        "source_full_cleat_interface_wrench_on_cleat_n_nmm": source_on_cleat.tolist(),
        "source_full_cleat_balance_residual_n_nmm": source_residual.tolist(),
        "derived_four_bolt_32_face_interface_wrench_on_cleat_n_nmm": derived_on_cleat.tolist(),
        "derived_whole_cleat_balance_residual_n_nmm": derived_residual.tolist(),
        "gravity_count": "current W included once at the cleat; source host drives remain the negative saved interface wrenches and receive no added gravity.",
    }


def build(output: Path):
    output = Path(output).resolve()
    require(not output.exists(), f"preserve previous output: {output}")
    pins = source_pins()
    model = read(MODEL)
    model_inputs = read(MODEL_INPUTS)
    assessment = read(OPERATOR_ASSESSMENT)
    identities = read(ROWS)
    comparison = read(COMPARISON)
    component = read(COMPONENT)
    require(comparison["response_sha256"] == PINS[RESPONSE], "source response metadata binding differs")
    require([state["case_id"] for state in comparison["states"] if state["gap_scale"] == 1.0] == CASES,
            "nominal case order differs")
    require(not comparison["complete_joint_acceptance"] and not comparison["physical_release"],
            "source claims joint acceptance or physical release")
    require(component["source_comparison_sha256"] == PINS[COMPARISON]
            and component["source_response_sha256"] == PINS[RESPONSE], "component force binding differs")
    require(assessment["output_sha256"]["operators.npz"] == PINS[OPERATORS]
            and assessment["output_sha256"]["model.json"] == PINS[MODEL]
            and assessment["output_sha256"]["row-identities.json"] == PINS[ROWS]
            and assessment["output_sha256"]["model-inputs.json"] == PINS[MODEL_INPUTS],
            "operator assessment output binding differs")
    common_datum, common_node_count = common_cleat_datum(model)
    global COMMON_DATUM
    COMMON_DATUM = common_datum
    host_data = {}
    mechanics_data = {}
    for definition in HOSTS:
        template = import_private(RAIL_PAIR, "left_" + definition["key"] + "_mechanics")
        group = configure_group(definition, model, identities, comparison, component)
        mechanics_data[definition["host"]] = configure_mechanics(template, group)
        host_data[definition["host"]] = group
    gravity = current_cleat_wrenches(model, model_inputs, assessment, comparison, common_datum)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    states, beam_rows = [], []
    failure = None
    for case_id in CASES:
        case = {"case_id": case_id, "hosts": {}}
        host_results = {}
        for host in ("base_rail_top", "base_side_left"):
            mechanics, helper, blocks, cells = mechanics_data[host]
            source = next(record for record in host_data[host]["sources"] if record["case_id"] == case_id)
            debug = {}
            try:
                state, fields = mechanics.solve_case(
                    helper, blocks, cells, host_data[host]["n"], host_data[host]["basis"], source, debug
                )
                host_results[host] = state
                case["hosts"][host] = state
                beam_rows.extend({"case_id": case_id, "host": host, **field} for field in fields)
            except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
                failure = {
                    "case_id": case_id,
                    "host": host,
                    "source_wrench": source["external_drive_wrench_n_nmm"],
                    "last_accepted_state": debug,
                    "error": str(error),
                    "incompatibility_proved": False,
                    "retry_or_law_sweep_performed": False,
                }
                case["hosts"][host] = {"status": "STOP", "last_accepted_state": debug}
                break
        if failure:
            states.append(case)
            break
        try:
            case["whole_cleat"] = assemble_cleat_case(case_id, host_results, host_data, gravity)
        except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
            failure = {
                "case_id": case_id,
                "host": "whole-cleat-balance",
                "source_wrench": {
                    host: next(record for record in host_data[host]["sources"] if record["case_id"] == case_id)[
                        "source_connector_wrench_on_host_n_nmm"
                    ]
                    for host in host_results
                },
                "current_W": gravity[case_id]["current_W_cleat_applied_wrench_at_common_datum_n_nmm"],
                "last_accepted_state": {"host_states": host_results},
                "error": str(error),
                "incompatibility_proved": False,
                "retry_or_law_sweep_performed": False,
            }
            case["whole_cleat_failure"] = {"error": str(error), "incompatibility_proved": False}
            states.append(case)
            break
        states.append(case)
    for path, expected in pins.items():
        require(sha(path) == expected, f"source changed during upper-left block calculation: {path}")
    completed = [state for state in states if "whole_cleat" in state]
    host_states = [
        (case["case_id"], host, record)
        for case in states
        for host, record in case["hosts"].items()
        if "bolts" in record
    ]
    if host_states:
        rail_mechanics = mechanics_data["base_rail_top"][0]
        rail_mechanics.write_csv(output / "states.csv", [
            {"case_id": case_id, "host": host,
             "mixed_scaled_gradient_maximum_n": state["mixed_scaled_gradient_maximum_n"],
             "wrench_residual_n_nmm": state["interface_wrench_balance_residual_n_nmm"],
             "host_translation_xyz_mm": state["host_translation_at_face_datum_xyz_mm"],
             "host_rotation_xyz_rad": state["host_rotation_xyz_rad"],
             "tangent_nullity_at_relative_1e_12": state["tangent_nullity_at_relative_1e_12"],
             "elastic_bolt_hypothesis_exceeded": state["elastic_bolt_hypothesis_exceeded"]}
            for case_id, host, state in host_states
        ])
        rail_mechanics.write_csv(output / "bolt-states.csv", [
            {"case_id": case_id, "host": host, **{key: bolt[key] for key in (
                "axis_id", "compatible_T_n", "source_original_T_n", "source_original_V_n", "bore_V_resultant_n",
                "normal_opening_mm", "projected_shortening_mm", "axial_compatibility_residual_mm",
                "wrench_on_host_at_face_datum_n_nmm")}}
            for case_id, host, state in host_states for bolt in state["bolts"]
        ])
        rail_mechanics.write_csv(output / "beam-fields.csv", beam_rows)
        rail_mechanics.write_csv(output / "bore-fields.csv", [
            {"case_id": case_id, "host": host, "axis_id": bolt["axis_id"], **field}
            for case_id, host, state in host_states for bolt in state["bolts"] for field in bolt["bore_fields"]
        ])
        rail_mechanics.write_csv(output / "face-cells.csv", [
            {"case_id": case_id, "host": host, **field}
            for case_id, host, state in host_states for field in state["face_cells"]
        ])
        if completed:
            rail_mechanics.write_csv(output / "cleat-wrenches.csv", [
                {"case_id": case["case_id"],
                 "current_W_cleat_applied_wrench_n_nmm": case["whole_cleat"]["current_W_cleat_applied_wrench_at_common_datum_n_nmm"],
                 "source_cleat_interface_wrench_n_nmm": case["whole_cleat"]["source_full_cleat_interface_wrench_on_cleat_n_nmm"],
                 "source_balance_residual_n_nmm": case["whole_cleat"]["source_full_cleat_balance_residual_n_nmm"],
                 "derived_cleat_interface_wrench_n_nmm": case["whole_cleat"]["derived_four_bolt_32_face_interface_wrench_on_cleat_n_nmm"],
                 "derived_balance_residual_n_nmm": case["whole_cleat"]["derived_whole_cleat_balance_residual_n_nmm"]}
                for case in completed
            ])
    result = {
        "schema": "upper_left_common_cleat_four_bolt_local_pair_sensitivity/v1",
        "status": "STOP" if failure else "FINITE_SHARED_HOST_POSE_BLOCK_HYPOTHESIS",
        "counts": {"source_cases": 6, "completed_cases": len(completed), "hosts": 2,
                   "completed_host_models": len(host_states), "bolts": 4, "face_cells": 32,
                   "local_models": 2, "scaled_unknowns_per_local_model": 142},
        "case_ids": CASES,
        "axis_ids": [axis for group in HOSTS for axis in group["axes"]],
        "states": states,
        "failure": failure,
        "model": {
            "fixed_cleat": CLEAT,
            "common_cleat_datum_xyz_mm": common_datum.tolist(),
            "common_cleat_datum_definition": "Mean of unique source physical-node coordinates for the cleat; the same datum is used for both host groups.",
            "common_cleat_source_node_count": common_node_count,
            "host_groups": {
                host: {
                    "axes": [bolt["axis_id"] for bolt in data["bolts"]],
                    "host_interface_datum_xyz_mm": np.asarray(data["datum"]).tolist(),
                    "source_body_datum_xyz_mm": np.asarray(data["body_datum"]).tolist(),
                    "finished_contact_area_centroid_xyz_mm": np.asarray(data["face_centroid"]).tolist(),
                    "finished_contact_area_mm2": data["face_area_mm2"],
                    "bolt_axis_head_to_nut_xyz": np.asarray(data["n"]).tolist(),
                    "transverse_basis_xyz": np.asarray(data["basis"]).tolist(),
                    "length_mm": data["length"],
                    "diameter_mm": data["diameter"],
                    "per_receiver_radial_gap_mm": data["gap"],
                    "receiver_geometry": data["family"],
                    "source_rows": [row["row"] for row in data["selected"]],
                    "face_cells": [row["row"] for row in data["face"]],
                    "source_axes": [{"axis_id": bolt["axis_id"],
                                     "interface_point_xyz_mm": bolt["interface_point_xyz_mm"],
                                     "source_component_rows": bolt["source_component_rows"],
                                     "source_tie_row": bolt["source_tie_row"],
                                     "relative_radial_gap_mm": bolt["relative_radial_gap_mm"],
                                     "source_geometry": bolt["geometry"]}
                                    for bolt in data["bolts"]],
                }
                for host, data in host_data.items()
            },
            "current_W_cleat_by_case": gravity,
            "Kwood_mpa_per_mm_hypothesis": 20.0,
            "Khead_mpa_per_mm_hypothesis": 10000.0,
            "Ebolt_mpa_hypothesis": 200000.0,
            "face_stiffness_mpa_per_mm": 100.0,
            "conditional_Fyb_comparison_mpa": mechanics_data["base_rail_top"][0].FYB_SCENARIO,
            "local_force_component_tolerance_n": mechanics_data["base_rail_top"][0].FORCE_TOLERANCE,
            "local_moment_component_tolerance_nmm": mechanics_data["base_rail_top"][0].MOMENT_TOLERANCE,
            "common_cleat_source_force_tolerance_n": SOURCE_FORCE_TOLERANCE_N,
            "common_cleat_source_moment_tolerance_nmm": SOURCE_MOMENT_TOLERANCE_NMM,
            "common_cleat_derived_force_tolerance_n": 2 * COMMON_FORCE_TOLERANCE_N,
            "common_cleat_derived_moment_tolerance_nmm": 2 * COMMON_MOMENT_TOLERANCE_NMM,
            "reused_mechanics": "Two private imports of the immutable rail-pair mechanics; each host uses one two-bolt pose and its own 16 source face cells.",
            "joint_scope": "Rigid cleat is the common gauge. Each host pose is solved independently under its saved wrench. No elastic cleat/interface coupling or full-frame redistribution is modeled.",
        },
        "limits": [
            "The exact four-axis, 32-face current source forces are consumed. Current cleat W is included once in the whole-cleat balance; no gravity is added to either host drive.",
            "Rail and side local poses share only the fixed cleat datum. This is not a coupled elastic cleat model or a full-frame solve.",
            "Face-cell points, areas and unilateral stiffnesses remain frozen. Smooth-bolt, wood bore, washer-seat and rigid-washer laws remain hypotheses without preload or friction.",
            "Bore pressure, beam stress, seat pressure and pose are finite local model outputs. No actual wood, washer, delivered hardware or capacity is qualified.",
            "The numerical local criteria do not close the adopted acceptance authority. Complete joint acceptance and physical release remain false.",
            "A numerical STOP preserves the accepted state and does not prove mechanical incompatibility. No relaxed retry, material sweep or law sweep is performed.",
        ],
        "source_sha256": {str(path.relative_to(ROOT)): expected for path, expected in sorted(pins.items())},
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
        "actual_washer_stress_mpa": None,
        "actual_washer_capacity_n": None,
        "actual_hardware_capacity_n": None,
        "coupled_joint_resistance_n": None,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    hashes = {path.name: sha(path) for path in output.iterdir()}
    result["output_sha256"] = hashes.copy()
    dump(output / "checks.json", result)
    hashes["checks.json"] = sha(output / "checks.json")
    dump(output / "source-pins.json", {"source_sha256": result["source_sha256"], "output_sha256": hashes,
                                       "complete_joint_acceptance": False, "physical_release": False})
    for path, expected in pins.items():
        require(sha(path) == expected, f"source changed before final receipt: {path}")
    print(json.dumps({"status": result["status"], "completed_cases": len(completed),
                      "checks_sha256": hashes["checks.json"]}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle", "shared mechanics slot occupied")
        result = build(output)
    if result["failure"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
