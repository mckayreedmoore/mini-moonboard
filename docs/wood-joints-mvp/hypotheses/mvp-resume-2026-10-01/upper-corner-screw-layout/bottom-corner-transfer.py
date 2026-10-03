"""Prepare bottom-corner sources and expose a parent-owned first-order run.

Preparation only extracts saved loads and geometry. Mechanics and known-answer
coupons require an explicit parent call; the default command never solves.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = HERE.parents[4]
BASE = PACKET.parent / "mvp-acceleration-2026-09-28"
RAW = HERE / "rawlocal/bottom-corner-transfer"
MODEL = HERE / "operators-attempt02/model.json"
INPUTS = HERE / "operators-attempt02/model-inputs.json"
ASSESSMENT = HERE / "operators-attempt02/operator-assessment.json"
ROWS = HERE / "operators-attempt02/row-identities.json"
OPERATORS = HERE / "operators-attempt02/operators.npz"
COMPARISON = HERE / "frame-250-attempt02/comparison.json"
RESPONSE = HERE / "frame-250-attempt02/response.npz"
BOTTOM = HERE / "bolted-replay-results/bottom-attempt01/component-results.json"
GEOMETRY = PACKET / "member-screen-attempt02/four-screw-layout01/geometry.json"
CONTACTS = BASE / "reduced-static-attempt01/contact-geometry.json"
CELL_MODEL = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
DOF = BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof"
PARSER = (
    BASE
    / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
)
FASTENERS = (
    PACKET.parent / "hardware-material-specification-2026-09-30/fastener-inputs.json"
)
RAIL = HERE / "upper-right-rail-pair.py"
HELPER = HERE / "upper-right-combined-transfer.py"
FIRST_ORDER = HERE / "corner-first-order.py"
TRACTION = HERE / "cleat-traction.py"
TOP_CHECKS = HERE / "rawlocal/corner-first-order/attempt01/checks.json"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
PINS = {
    MODEL: "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    INPUTS: "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    ASSESSMENT: "1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    OPERATORS: "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    COMPARISON: "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    RESPONSE: "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    BOTTOM: "ec421ee35b9477842660faa6d2528bd957f8a06620f7d84c46d9654e40ce146a",
    GEOMETRY: "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    CONTACTS: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    CELL_MODEL: "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    DOF: "532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d",
    PARSER: "7abfeb3b02843588651b440dba4a86ae3f85106557383225a50c09b5cb080632",
    FASTENERS: "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
    RAIL: "4243b53bbb7377753f0b1fdd73fa1aa6c80e1a96c99d428def88e82a899e6f96",
    HELPER: "fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0",
    FIRST_ORDER: "6e3f899ac99d6eef629ac12570b6ea31ea5c3914467c1c7399b7bcdd8d320563",
    TRACTION: "2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764",
    TOP_CHECKS: "b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe",
}
EXPECTED_ROWS = {
    ("left", "rail"): [16, 17, 18, 19, 700, 701, 702, 703, 1512, 1513],
    ("left", "side"): [20, 21, 22, 23, 960, 961, 962, 963, 1514, 1515],
    ("right", "rail"): [24, 25, 26, 27, 734, 735, 736, 737, 1516, 1517],
    ("right", "side"): [28, 29, 30, 31, 1038, 1039, 1040, 1041, 1518, 1519],
}
FLAGS = {
    "formal_criterion_acceptance": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "fabrication_release": False,
    "reviewed_geometry_changed": False,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, "changed consumed source: " + str(path))


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "missing frozen helper")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def encoded(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def source_map(pins):
    return {
        str(path.relative_to(ROOT)): digest for path, digest in sorted(pins.items())
    }


def body_datum(model, body):
    nodes = sorted(set(model["body_nodes"][body]))
    return np.mean(
        [model["physical_node_coordinates_mm"][str(n)] for n in nodes], axis=0
    )


def shifted(value, old, new):
    result = np.asarray(value, dtype=float).copy()
    result[3:] += np.cross(np.asarray(old) - new, result[:3])
    return result


def prepare():
    """Extract six-case wrenches, nodal weight and geometry; run no mechanics."""
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__).resolve())}
    authenticate(pins)
    model, inputs, assessment, rows, comparison, bottom, geometry, contacts, cells = (
        read(path)
        for path in (
            MODEL,
            INPUTS,
            ASSESSMENT,
            ROWS,
            COMPARISON,
            BOTTOM,
            GEOMETRY,
            CONTACTS,
            CELL_MODEL,
        )
    )
    require(comparison["response_sha256"] == pins[RESPONSE], "response receipt differs")
    require(
        [s["case_id"] for s in comparison["states"] if s["gap_scale"] == 1.0] == CASES,
        "nominal case order differs",
    )
    require(
        [c["case_id"] for c in inputs["cases"]] == CASES, "load column order differs"
    )
    require(
        not comparison["complete_joint_acceptance"]
        and not comparison["physical_release"],
        "source claims acceptance or release",
    )
    for path in (MODEL, INPUTS, ROWS, OPERATORS):
        require(
            assessment["output_sha256"][path.name] == pins[path],
            "operator binding differs",
        )
    require(
        comparison["dead_load_factor"] == assessment["dead_load_factor"],
        "weight factor differs",
    )
    require(
        not bottom["complete_joint_acceptance"] and not bottom["physical_release"],
        "bottom source claims acceptance or release",
    )
    require(
        read(TOP_CHECKS)["status"] == "COMPLETE_FIRST_ORDER_LOCAL_FORCES",
        "method precedent is incomplete",
    )
    axes = {
        c["axis_id"]: c for c in inputs["connections"] if c["kind"] == "candidate_bolt"
    }
    seats = {(s["axis_id"], s["member"]): s for s in bottom["washer_geometry"]}
    cell_by_id = {c["name"]: c for c in cells["contact_cell_ownership"]}
    parser = module(PARSER, "bottom_source_dof_parser")
    traction = module(TRACTION, "bottom_source_traction_arithmetic")
    labels = parser.parse_dof_file(DOF)
    washer = read(FASTENERS)["dimension_inputs"]["washer"]
    groups, blocks = [], {}
    with (
        np.load(OPERATORS, allow_pickle=False) as operators,
        np.load(RESPONSE, allow_pickle=False) as response,
    ):
        D, W, F = operators["D"], operators["W"], operators["F"]
        require(
            F.shape == (len(labels), 12)
            and W.shape == (6 * len(model["body_names"]), 12),
            "mapped load dimensions differ",
        )
        for side in ("left", "right"):
            cleat = "bottom_outer_" + side + "_cleat"
            common = body_datum(model, cleat)
            block_nodes = sorted(set(model["body_nodes"][cleat]))
            selected_dofs = [
                (i, node, dof - 1)
                for i, (node, dof) in enumerate(labels)
                if node in block_nodes
            ]
            require(
                {(node, d) for _, node, d in selected_dofs}
                == {(node, d) for node in block_nodes for d in range(3)}
                and len(selected_dofs) == 3 * len(block_nodes),
                "cleat load DOF census differs",
            )
            weight = {}
            body_index = model["body_names"].index(cleat)
            for index, case in enumerate(CASES):
                forces = {node: np.zeros(3) for node in block_nodes}
                for row, node, dof in selected_dofs:
                    forces[node][dof] = (
                        comparison["dead_load_factor"] * F[row, 2 * index]
                        + F[row, 2 * index + 1]
                    )
                actions = [
                    traction.action(
                        "original_current_mapped_W_node",
                        str(node),
                        model["physical_node_coordinates_mm"][str(node)],
                        forces[node],
                        node_id=node,
                    )
                    for node in block_nodes
                ]
                mapped = traction.wrench(actions, common)
                original = (
                    comparison["dead_load_factor"]
                    * W[6 * body_index : 6 * body_index + 6, 2 * index]
                    + W[6 * body_index : 6 * body_index + 6, 2 * index + 1]
                )
                original = original.copy()
                original[3:] *= 1000
                require(
                    np.max(abs(mapped - original)) < 1e-6,
                    "own nodal weight does not reproduce W",
                )
                weight[case] = {
                    "actions": actions,
                    "wrench_n_nmm": mapped.tolist(),
                    "mapped_F_minus_W_n_nmm": (mapped - original).tolist(),
                }
            blocks[side] = {
                "cleat": cleat,
                "common_datum_xyz_mm": common.tolist(),
                "weight_by_case": weight,
            }
            for key in ("rail", "side"):
                host = (
                    "base_rail_bottom_" + side if key == "rail" else "base_side_" + side
                )
                selected = sorted(
                    [
                        r
                        for r in rows
                        if {r["ownership"]["first_body"], r["ownership"]["second_body"]}
                        == {host, cleat}
                    ],
                    key=lambda r: r["row"],
                )
                require(
                    [r["row"] for r in selected] == EXPECTED_ROWS[side, key],
                    "bottom row census differs",
                )
                host_index = model["body_names"].index(host)
                host_origin = body_datum(model, host)
                face = []
                for row in selected:
                    if row["ownership"]["role"] != "timber_or_panel_contact":
                        continue
                    cell = cell_by_id[row["row_id"]]
                    patch = contacts["contact_patches"][cell["source_patch_index"]]
                    require(
                        {cell["first"], cell["second"]} == {host, cleat}
                        and set(patch["member_ids"]) == {host, cleat},
                        "face patch ownership differs",
                    )
                    require(
                        cell["point_xyz_mm"] == row["ownership"]["point_mm"],
                        "face cell position differs",
                    )
                    require(
                        math.isclose(
                            row["law"]["stiffness_N_per_mm"] / cell["area_mm2"],
                            100.0,
                            rel_tol=1e-10,
                        ),
                        "original normal-contact stiffness differs",
                    )
                    require(
                        row["ownership"]["first_body"] == host,
                        "bottom face row order differs",
                    )
                    face.append(
                        {
                            **row,
                            "contact_area_mm2": cell["area_mm2"],
                            "finished_patch": patch,
                        }
                    )
                require(len(face) == 4, "bottom has four original face cells per host")
                bolt_ids = sorted(
                    a
                    for a, c in axes.items()
                    if set(c["receiver_member_ids"]) == {host, cleat}
                )
                require(len(bolt_ids) == 2, "bottom pair axis census differs")
                bolts = []
                for number, axis_id in enumerate(bolt_ids):
                    axis = axes[axis_id]
                    lateral = [
                        r
                        for r in selected
                        if r["ownership"]["role"] == "candidate_bolt_lateral_plane"
                        and r["row_id"].rpartition("/")[0] == axis_id
                    ]
                    tie = next(
                        r
                        for r in selected
                        if r["row_id"] == axis_id + "/outer-seat-axial-tie"
                    )
                    require(len(lateral) == 2, "missing lateral components")
                    point = np.asarray(lateral[0]["ownership"]["point_mm"])
                    require(
                        np.max(abs(point - lateral[1]["ownership"]["point_mm"])) < 1e-7,
                        "lateral component stations differ",
                    )
                    host_seat, cleat_seat = seats[axis_id, host], seats[axis_id, cleat]
                    delta = (
                        np.asarray(cleat_seat["point_xyz_mm"])
                        - host_seat["point_xyz_mm"]
                    )
                    n = delta / np.linalg.norm(delta)
                    require(
                        np.linalg.norm(
                            np.cross(
                                np.asarray(tie["ownership"]["point_mm"]) - point, n
                            )
                        )
                        < 1e-6,
                        "outer tie point does not lie on its own bolt line",
                    )
                    tie_host_direction = np.asarray(
                        tie["ownership"]["direction_global_xyz"]
                    ) * (1 if tie["ownership"]["first_body"] == host else -1)
                    require(
                        np.max(abs(tie_host_direction - n)) < 1e-12,
                        "tie force sign differs from host-to-cleat axis",
                    )
                    h = round(float(np.dot(point - host_seat["point_xyz_mm"], n)), 4)
                    k = round(
                        float(
                            np.dot(np.asarray(cleat_seat["point_xyz_mm"]) - point, n)
                        ),
                        4,
                    )
                    require(
                        (h, k) == ((38.1, 88.9) if key == "rail" else (88.9, 88.9)),
                        "bottom receiver grips differ",
                    )
                    for member, seat, length in (
                        (host, host_seat, h),
                        (cleat, cleat_seat, k),
                    ):
                        interval = next(
                            v
                            for v in axis["source_record"]["geometry"][
                                "wood_receiver_intervals"
                            ]
                            if v["receiver_id"] == member
                        )
                        spans = interval[
                            "intersection_solid_intervals_from_underhead_mm"
                        ]
                        require(
                            len(spans) == 1
                            and abs(spans[0][1] - spans[0][0] - length) < 1e-6,
                            "receiver is not one continuous source grip",
                        )
                        expected_seat = point + (-h if member == host else k) * n
                        require(
                            np.max(abs(expected_seat - seat["point_xyz_mm"])) < 1e-7,
                            "own supported wood seat differs",
                        )
                        require(
                            seat["geometry_screen_pass"]
                            and all(v["supported"] for v in seat["nominal"]),
                            "unsupported bottom seat",
                        )
                    bore_records = axis["receiver_clearance_geometry"]
                    require(
                        len(bore_records) == 2
                        and all(
                            v["unique_bore_radius_mm"] == 3.75 for v in bore_records
                        ),
                        "bottom finished bores differ",
                    )
                    diameter = round(
                        axis["source_record"]["geometry"]["modeled_shaft_diameter_mm"],
                        4,
                    )
                    require(diameter == 6.35, "bottom quarter-inch policy differs")
                    gaps = [
                        v["relative_radial_gap_mm"]
                        for v in comparison["clearance_planes"]
                        if v["plane_id"] == lateral[0]["row_id"]
                    ]
                    require(
                        len(gaps) == 1 and math.isclose(gaps[0], 1.15, abs_tol=1e-10),
                        "source circular clearance differs",
                    )
                    bolts.append(
                        {
                            "axis_id": axis_id,
                            "number": number,
                            "interface_point_xyz_mm": point.tolist(),
                            "source_component_rows": [v["row"] for v in lateral],
                            "source_tie_row": tie["row"],
                            "source_outer_tie_point_xyz_mm": tie["ownership"][
                                "point_mm"
                            ],
                            "normal_host_to_cleat_xyz": n.tolist(),
                            "host_length_mm": h,
                            "cleat_length_mm": k,
                            "actual_axis_head_to_nut_xyz": axis["axis_xyz"],
                            "host_outer_role": host_seat["role"],
                            "cleat_outer_role": cleat_seat["role"],
                            "supported_seats": [host_seat, cleat_seat],
                            "finished_receiver_bores": bore_records,
                        }
                    )
                n = np.asarray(bolts[0]["normal_host_to_cleat_xyz"])
                require(
                    np.max(abs(n - bolts[1]["normal_host_to_cleat_xyz"])) < 1e-12,
                    "pair axes differ",
                )
                reference = (
                    np.array([1.0, 0.0, 0.0])
                    if key == "rail"
                    else np.array([0.0, 0.0, 1.0])
                )
                basis = np.column_stack((reference, np.cross(n, reference)))
                require(
                    np.max(abs(basis.T @ basis - np.eye(2))) < 1e-12,
                    "local2 basis differs",
                )
                datum = np.mean([b["interface_point_xyz_mm"] for b in bolts], axis=0)
                raw_rows = [r["row"] for r in selected]
                dhost = D[raw_rows, 6 * host_index : 6 * host_index + 6]
                states = []
                for case in CASES:
                    raw = response[case + "_gap_raw_force_n"]
                    values = raw[raw_rows]
                    force = -dhost[:, :3].T @ values
                    wrench = shifted(
                        np.r_[force, -1000 * dhost[:, 3:].T @ values],
                        host_origin,
                        datum,
                    )
                    point_actions = []
                    for index, row in enumerate(selected):
                        ownership = row["ownership"]
                        direction = np.asarray(ownership["direction_global_xyz"]) * (
                            1 if ownership["first_body"] == host else -1
                        )
                        require(
                            np.max(abs(-dhost[index, :3] - direction)) < 1e-12,
                            "D force sign differs",
                        )
                        point_actions.append(
                            traction.action(
                                "source_row_point_force",
                                row["row_id"],
                                ownership["point_mm"],
                                values[index] * direction,
                                row=row["row"],
                            )
                        )
                    point_wrench = traction.wrench(point_actions, datum)
                    require(
                        np.max(abs(wrench[:3] - point_wrench[:3])) < 1e-7,
                        "D and point-force sums differ",
                    )
                    original = []
                    for bolt in bolts:
                        witness = next(
                            v
                            for v in bottom["states"]
                            if (v["case_id"], v["axis_id"]) == (case, bolt["axis_id"])
                        )
                        v = sum(
                            np.asarray(a["force_xyz_n"])
                            for a in point_actions
                            if a["row"] in bolt["source_component_rows"]
                        )
                        tension = float(raw[bolt["source_tie_row"]])
                        require(
                            tension >= 0
                            and abs(tension - witness["tension_n"]) < 1e-8
                            and abs(np.linalg.norm(v) - witness["shear_n"]) < 1e-8,
                            "bottom same-state bolt binding differs",
                        )
                        original.append(
                            {
                                "axis_id": bolt["axis_id"],
                                "signed_T_n": tension,
                                "V_n": float(np.linalg.norm(v)),
                                "signed_plane_components_n": raw[
                                    bolt["source_component_rows"]
                                ].tolist(),
                                "force_on_host_xyz_n": v.tolist(),
                            }
                        )
                    states.append(
                        {
                            "case_id": case,
                            "source_connector_wrench_on_host_n_nmm": wrench.tolist(),
                            "external_drive_wrench_n_nmm": (-wrench).tolist(),
                            "source_individual_bolts": original,
                            "source_point_actions": point_actions,
                            "retained_source_free_couple_nmm": (wrench - point_wrench)[
                                3:
                            ].tolist(),
                            "source_face_cells": [
                                {
                                    "row": r["row"],
                                    "compression_n": float(raw[r["row"]]),
                                    "stiffness_n_per_mm": r["law"][
                                        "stiffness_N_per_mm"
                                    ],
                                }
                                for r in face
                            ],
                        }
                    )
                family = {
                    "host_length_mm": bolts[0]["host_length_mm"],
                    "cleat_length_mm": bolts[0]["cleat_length_mm"],
                    "diameter_mm": 6.35,
                    "bore_mm": 7.5,
                    "washer_ID_max_mm": round(25.4 * max(washer["id_in"]), 4),
                    "washer_OD_min_mm": round(25.4 * min(washer["od_in"]), 4),
                    "flat_radius_mm": 5.0,
                }
                finished = {
                    member: geometry["members"][member] for member in (host, cleat)
                }
                for member, record in finished.items():
                    pins[ROOT / record["current_finished_step"]] = record[
                        "current_finished_step_sha256"
                    ]
                    require(
                        record["current_finished_step_sha256"]
                        == bottom["source_sha256"][
                            str(ROOT / record["current_finished_step"])
                        ],
                        "bottom finished STEP binding differs",
                    )
                rechecks = [
                    v
                    for v in bottom["changed_side_host_washer_sweep_rechecks"]
                    if v["member"] == host
                ]
                if key == "side":
                    require(
                        len(rechecks) == 2
                        and all(
                            v["current_STEP_sha256"]
                            == finished[host]["current_finished_step_sha256"]
                            and all(
                                abs(q["outside_bore_sweep_supported_fraction"] - 1)
                                < 1e-6
                                for q in v["measurements"]
                            )
                            for v in rechecks
                        ),
                        "current side-host seat support differs",
                    )
                groups.append(
                    {
                        "side": side,
                        "key": key,
                        "host": host,
                        "cleat": cleat,
                        "datum_xyz_mm": datum.tolist(),
                        "source_body_datum_xyz_mm": host_origin.tolist(),
                        "n": n.tolist(),
                        "basis": basis.tolist(),
                        "family": family,
                        "bolts": bolts,
                        "face": face,
                        "sources": states,
                        "source_rows": raw_rows,
                        "finished_members": finished,
                        "side_host_seat_rechecks": rechecks,
                        "face_axis_component_difference": float(
                            max(
                                np.max(
                                    abs(
                                        np.asarray(
                                            r["ownership"]["direction_global_xyz"]
                                        )
                                        + n
                                    )
                                )
                                for r in face
                            )
                        ),
                        "finished_paths": [
                            v
                            for v in bottom["finished_paths"]
                            if v["axis_id"] in bolt_ids
                        ],
                    }
                )
        for side, block in blocks.items():
            common = np.asarray(block["common_datum_xyz_mm"])
            residuals = {}
            for case_index, case in enumerate(CASES):
                balance = np.asarray(
                    block["weight_by_case"][case]["wrench_n_nmm"]
                ).copy()
                for group in (g for g in groups if g["side"] == side):
                    balance -= shifted(
                        group["sources"][case_index][
                            "source_connector_wrench_on_host_n_nmm"
                        ],
                        group["datum_xyz_mm"],
                        common,
                    )
                require(
                    np.max(abs(balance)) < 1e-6,
                    "full source cleat does not balance its weight once",
                )
                residuals[case] = balance.tolist()
            block["source_whole_cleat_residuals_n_nmm"] = residuals
    authenticate(pins)
    return {
        "schema": "bottom_corner_first_order_preparation/v1",
        "status": "PREPARED_PARENT_KNOWN_ANSWERS_PENDING",
        "case_ids": CASES,
        "groups": groups,
        "blocks": blocks,
        "source_sha256": source_map(pins),
        "method": {
            "Kwood_mpa_per_mm": 20.0,
            "Khead_mpa_per_mm": 10000.0,
            "Ebolt_mpa": 200000.0,
            "face_stiffness_mpa_per_mm": 100.0,
            "receiver_radial_gap_mm": 0.575,
            "gradient_tolerance_n": 1e-4,
            "host_force_tolerance_n": 0.001,
            "host_moment_tolerance_nmm": 0.2,
            "whole_cleat_force_tolerance_n": 0.002,
            "whole_cleat_moment_tolerance_nmm": 0.4,
            "geometric_shortening_and_preload_stiffness": False,
        },
        "known_answer_plan": [
            "Each actual 127/177.8 mm family: 10 N cantilever tip FL^3/(3EI), rotation FL^2/(2EI), root -F and -FL; reuse the frozen coupon and tolerances.",
            "Each own quarter-inch annulus: centered T=100 N series-seat closure T/(Khead*Aland)+T/(Kwood*Awood), zero moment.",
            "Loaded host and whole-cleat physical actions must independently close with the unchanged top first-order tolerances.",
        ],
        "known_answers_executed": False,
        "local_mechanics_executed": False,
        "no_native_CAD_frame_or_tests_run": True,
        "parent_owns_serialized_execution": True,
        **FLAGS,
    }, pins


def configure(group):
    """Privately bind the same equations to this bottom receiver geometry."""
    mechanics = module(RAIL, "bottom_" + group["side"] + "_" + group["key"] + "_pair")
    helper = module(HELPER, "bottom_" + group["side"] + "_" + group["key"] + "_contact")
    require(
        (helper.LENGTH, helper.E_BOLT, helper.K_HEAD) == (177.8, 200000.0, 10000.0)
        and (
            mechanics.KWOOD,
            mechanics.KHEAD,
            mechanics.EBOLT,
            mechanics.GAP,
            mechanics.GRADIENT_TOLERANCE,
            mechanics.FORCE_TOLERANCE,
            mechanics.MOMENT_TOLERANCE,
        )
        == (20.0, 10000.0, 200000.0, 0.575, 1e-4, 0.001, 0.2),
        "immutable method constants differ",
    )
    family = group["family"]
    length = family["host_length_mm"] + family["cleat_length_mm"]
    # LENGTH is the geometry and DOF scaling parameter, not a material law.
    # The private helper uses it in both Hermite scaling and the actual span.
    helper.LENGTH = length
    for key, value in {
        "HOST": group["host"],
        "CLEAT": group["cleat"],
        "CASES": CASES,
        "DATUM": np.asarray(group["datum_xyz_mm"]),
        "FAMILY": family.copy(),
        "LENGTH": length,
        "DIAMETER": family["diameter_mm"],
        "AREA": math.pi * family["diameter_mm"] ** 2 / 4,
        "AXIAL_COMPLIANCE": length
        / (mechanics.EBOLT * math.pi * family["diameter_mm"] ** 2 / 4),
    }.items():
        setattr(mechanics, key, value)
    n, basis = np.asarray(group["n"]), np.asarray(group["basis"])
    blocks, cells = mechanics.model_matrices(
        helper, group["bolts"], group["face"], n, basis
    )
    for block in blocks:
        block["geometric"] = np.zeros_like(block["geometric"])
    for cell in cells:
        # Retain the actual saved face normal, including its tiny difference
        # from the bore axis. Recover forces with this same normal below.
        cell["opening_row"] = np.asarray(
            cell["source"]["ownership"]["direction_global_xyz"]
        ) @ mechanics.host_map(cell["source"]["ownership"]["point_mm"])
    return mechanics, helper, blocks, cells


def known_answers(prepared):
    """Parent-only cantilever and centered series-contact engineering coupons."""
    first = module(FIRST_ORDER, "bottom_known_answer_cantilever")
    results = []
    for group in prepared["groups"]:
        mechanics, helper, _blocks, _cells = configure(group)
        coupon = first.cantilever_coupon(helper, group["family"])
        family = group["family"]
        head = helper.annulus(family["washer_ID_max_mm"] / 2, family["flat_radius_mm"])
        wood = helper.annulus(
            family["washer_ID_max_mm"] / 2, family["washer_OD_min_mm"] / 2
        )
        seat = helper.series_contact(100.0, 0.0, mechanics.KWOOD, head, wood)
        expected = 100.0 / (mechanics.KHEAD * np.sum(head[0])) + 100.0 / (
            mechanics.KWOOD * np.sum(wood[0])
        )
        require(
            abs(seat["total_closure_mm"] - expected) < 1e-9
            and abs(seat["moment_nmm"]) < 1e-6,
            "centered seat closure/moment known answer failed",
        )
        results.append(
            {
                "side": group["side"],
                "host": group["host"],
                "cantilever": coupon,
                "centered_series_contact": {
                    "T_n": 100.0,
                    "expected_closure_mm": float(expected),
                    "returned": seat,
                },
                **FLAGS,
            }
        )
    return results


def recover(group, mechanics, helper, state):
    traction = module(TRACTION, "bottom_physical_traction_arithmetic")
    n, basis = np.asarray(group["n"]), np.asarray(group["basis"])
    host_actions, cleat_actions, seats = [], [], []
    for bolt, source in zip(state["bolts"], group["bolts"], strict=True):
        require(
            bolt["axis_id"] == source["axis_id"]
            and bolt["projected_shortening_mm"] == 0.0,
            "axis identity or first-order shortening differs",
        )
        bolt["computational_axis_host_to_cleat_xyz"] = bolt.pop(
            "bolt_axis_head_to_nut_xyz"
        )
        bolt["actual_axis_head_to_nut_xyz"] = source["actual_axis_head_to_nut_xyz"]
        for field in bolt["bore_fields"]:
            point = (
                np.asarray(bolt["interface_point_xyz_mm"])
                + (field["x_mm"] - group["family"]["host_length_mm"]) * n
            )
            target = host_actions if field["receiver"] == "host" else cleat_actions
            target.append(
                traction.action(
                    "bore_station_resultant",
                    bolt["axis_id"],
                    point,
                    -np.asarray(field["force_on_beam_xyz_n"]),
                    receiver=field["receiver"],
                    x_mm=field["x_mm"],
                )
            )
        for end, target in ((0, host_actions), (1, cleat_actions)):
            actions, record = traction.wood_seat(
                helper, bolt, end, group["family"], n, basis, mechanics.KWOOD
            )
            supported = source["supported_seats"][end]
            require(
                np.max(
                    abs(
                        np.asarray(record["nominal_outer_wood_seat_xyz_mm"])
                        - supported["point_xyz_mm"]
                    )
                )
                < 1e-7,
                "recovered pressure does not use its own supported wood seat",
            )
            physical_end = ("host_" if end == 0 else "cleat_") + supported["role"]
            record["end"] = physical_end
            record["member"] = supported["member"]
            for action in actions:
                action["end"] = physical_end
                action["member"] = supported["member"]
            bolt["end_contacts"][end]["physical_wood_member"] = supported["member"]
            bolt["end_contacts"][end]["physical_outer_role"] = supported["role"]
            seats.append(record)
            target.extend(actions)
    by_row = {row["row"]: row for row in group["face"]}
    for field in state["face_cells"]:
        normal = np.asarray(by_row[field["row"]]["ownership"]["direction_global_xyz"])
        force = field["compression_n"] * normal
        host_actions.append(
            traction.action("face_cell", field["row_id"], field["point_xyz_mm"], force)
        )
        cleat_actions.append(
            traction.action("face_cell", field["row_id"], field["point_xyz_mm"], -force)
        )
    residual = (
        traction.wrench(host_actions, mechanics.DATUM)
        - state["source_connector_wrench_on_host_n_nmm"]
    )
    require(
        np.max(abs(residual[:3])) <= mechanics.FORCE_TOLERANCE
        and np.max(abs(residual[3:])) <= mechanics.MOMENT_TOLERANCE,
        "physical bottom host wrench does not balance",
    )
    return cleat_actions, {
        "state": state,
        "physical_host_actions": host_actions,
        "wood_seat_recovery": seats,
        "physical_host_residual_n_nmm": residual.tolist(),
    }


def write_packet(output, filename, result, pins):
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "use a fresh owned output child",
    )
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    (output / filename).write_text(encoded(result))
    authenticate(pins)
    receipt = {
        "source_sha256": source_map(pins),
        "output_sha256": {p.name: sha(p) for p in output.iterdir()},
        "source_unchanged_before_and_after_write": True,
        **FLAGS,
    }
    (output / "source-pins.json").write_text(encoded(receipt))
    return result


def run(output):
    """Parent-only finite six-case continuation; the caller owns serialization."""
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "use a fresh owned output child",
    )
    prepared, pins = prepare()
    traction = module(TRACTION, "bottom_run_traction_arithmetic")
    states, coupons, failure, debug, hosts = [], [], None, {}, {}
    case, side, host = None, None, None
    try:
        coupons = known_answers(prepared)
        configured = [(g, configure(g)) for g in prepared["groups"]]
        for index, case in enumerate(CASES):
            for side in ("left", "right"):
                block = prepared["blocks"][side]
                hosts, actions, beam_fields = {}, [], []
                for group, (mechanics, helper, blocks, cells) in configured:
                    if group["side"] != side:
                        continue
                    host = group["host"]
                    debug = {}
                    state, fields = mechanics.solve_case(
                        helper,
                        blocks,
                        cells,
                        np.asarray(group["n"]),
                        np.asarray(group["basis"]),
                        group["sources"][index],
                        debug,
                    )
                    recovered, record = recover(group, mechanics, helper, state)
                    hosts[host] = record
                    actions.extend(recovered)
                    beam_fields.extend({"host": host, **f} for f in fields)
                weight = block["weight_by_case"][case]
                all_actions = actions + weight["actions"]
                datum = np.asarray(block["common_datum_xyz_mm"])
                residual = traction.wrench(all_actions, datum)
                require(
                    np.max(abs(residual[:3])) < 0.002
                    and np.max(abs(residual[3:])) < 0.4,
                    "physical four-bolt whole-cleat balance failed",
                )
                block_groups = [g for g in prepared["groups"] if g["side"] == side]
                grain = np.asarray(
                    block_groups[0]["finished_members"][block["cleat"]]["geometry"][
                        "axis"
                    ]
                )
                grain /= np.linalg.norm(grain)
                points = [
                    (b["axis_id"], b["interface_point_xyz_mm"])
                    for g in block_groups
                    for b in g["bolts"]
                ]
                states.append(
                    {
                        "case_id": case,
                        "side": side,
                        "cleat": block["cleat"],
                        "common_datum_xyz_mm": datum.tolist(),
                        "hosts": hosts,
                        "beam_fields": beam_fields,
                        "physical_cleat_actions": actions,
                        "current_weight_once_n_nmm": weight["wrench_n_nmm"],
                        "own_weight_actions_once": weight["actions"],
                        "physical_whole_cleat_residual_n_nmm": residual.tolist(),
                        "cleat_grain_xyz": grain.tolist(),
                        "grain_cut_action_inventory": traction.cut_inventory(
                            all_actions, points, grain
                        ),
                        **FLAGS,
                    }
                )
    except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
        failure = {
            "case_id": case,
            "side": side,
            "host": host,
            "error": str(error),
            "last_accepted_iteration": debug,
            "physical_failure_claimed": False,
            "partial_block_host_states": hosts,
            "incompatibility_proved": False,
            "retry_or_law_sweep_performed": False,
        }
    result = {
        "schema": "bottom_corner_first_order_independent_traction/v1",
        "status": "STOP" if failure else "COMPLETE_FIRST_ORDER_LOCAL_FORCES",
        "failure": failure,
        "counts": {
            "completed_block_states": len(states),
            "completed_host_states": 2 * len(states),
            "completed_bolt_states": 4 * len(states),
            "source_cases": 6,
            "blocks": 2,
            "bolts_per_block": 4,
            "face_cells_per_host": 4,
        },
        "preparation": prepared,
        "cantilever_and_seat_coupons": coupons,
        "states": states,
        "known_answers_executed": len(coupons) == 4,
        "local_mechanics_executed": bool(debug),
        "geometric_shortening_and_preload_stiffness": False,
        "frame_response_changed": False,
        "material_or_contact_laws_changed": False,
        "balancing_free_couples_added": 0,
        "source_sha256": source_map(pins),
        "tests_run": False,
        "native_CAD_or_frame_execution": False,
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
        "actual_washer_capacity_n": None,
        "actual_hardware_capacity_n": None,
        "Ft_perp": None,
        "group_capacity_n": None,
        "limits": [
            "Rigid cleat gauge and two independent rigid host poses; no elastic timber coupling or frame feedback.",
            "First-order reference geometry, circular clearance, hypothetical K20 bore/wood seats, rigid concentric washers, smooth elastic bolts, and declared 10 mm flat lands.",
            "Bore samples are shaft-axis resultants, not a radial wall traction or allocation to disconnected material regions.",
            "Face samples are original four point cells per host; finished footprints are retained but no continuous patch traction is inferred.",
            "Pressure centroids carry their own moments once; nominal annuli are not translated by beam-end displacement.",
            "Grain cuts retain point-action jumps; no finished-section, ligament, Ft-perp, group/splitting or washer-metal resistance is inferred.",
            "Neutral modes yield representative poses, not motion bounds or assembled stability acceptance.",
        ],
        **FLAGS,
    }
    return write_packet(output, "checks.json", result, pins)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--parent-run",
        action="store_true",
        help="Explicit parent-owned coupons and local mechanics",
    )
    args = parser.parse_args()
    if args.parent_run:
        result = run(args.output)
    else:
        result, pins = prepare()
        write_packet(args.output, "readiness.json", result, pins)
    print(json.dumps({"status": result["status"], "output": str(args.output)}))
    if result.get("failure"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
