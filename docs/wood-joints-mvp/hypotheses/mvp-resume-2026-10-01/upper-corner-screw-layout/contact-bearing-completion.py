"""N05/N06 arithmetic on the frozen ce69/c3a8/62bd nominal frame states.

Import is inert. prepare(output) uses only the standard library and reads no
array values. The parent calls build(output) to evaluate saved forces; neither
entry point solves a frame, changes a model, or calls a native/CAD workflow.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import shutil
import struct
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/contact-bearing-completion"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
FRAME = HERE / "rawlocal/knee-bridge-frame/attempt02"
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
ASSESSMENT = GRAVITY / "operator-assessment.json"
COMPARISON = FRAME / "response/comparison.json"
RESPONSE = FRAME / "response/response.npz"
MODEL = GRAVITY / "model.json"
INPUTS = GRAVITY / "model-inputs.json"
ROWS = GRAVITY / "row-identities.json"
OPERATORS = GRAVITY / "operators.npz"
CARRIER = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
CONTACTS = BASE / "reduced-static-attempt01/contact-geometry.json"
CORRECTED = HERE.parent / "top-corner-contact-geometry.json"
MATERIALS = HERE.parent.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
VECTORS = HERE.parent / "retained_group_checks.py"
WRENCH = HERE.parent / "top_corner_actions.py"
BEARING = ROOT / "scripts/compact_thick_results.py"
FLUSH = ROOT / "scripts/floor_flush_checks.py"
FLOOR_METHOD = HERE.parent / "simple_frame.py"
LAW_METHOD = HERE.parent / "right_corner_clearance.py"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
FLOOR_MEMBERS = (
    "base_floor_left", "base_floor_right", "base_post_center_left",
    "base_post_center_right", "base_post_outer_left", "base_post_outer_right",
    "lumber_leg_left", "lumber_leg_right",
)
PSI_MPA = 0.006894757293168361
# Existing response law gates, not fitted acceptance tolerances.
LAW_TOL_N, GAP_TOL_MM = 1e-4, 1e-8
GEOMETRY_TOL_MM = 1e-7
PINS = {
    ASSESSMENT: "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    COMPARISON: "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    RESPONSE: "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    MODEL: "c14e93e003da72478e2db777cecab1aab7d5a9f7e3b12bdbd6813337f15572c1",
    INPUTS: "b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    OPERATORS: "7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f",
    GRAVITY / "receipt.json": "315c16d2a592b12dcd0160af47f9d4bababb6afaf54c6c74ddcbd41e01d45b6c",
    FRAME / "receipt.json": "6acb01eb1b07dc9f9175cb3a0e916fe74a9a32a7b90941cf3b18e84a24d9c599",
    CARRIER: "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    CONTACTS: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    CORRECTED: "987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f",
    MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    VECTORS: "391b459d20a7cc6bb2f53ec4622259948b74f228a6553f4dee749a2011ff559f",
    WRENCH: "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    BEARING: "3f4f0ec5bfd1535c602c0c00c8017665fd336ca32f9cd6b38ccf9d5813853c1a",
    FLUSH: "8d756c608bef10b8ce6f5141e58cbb0c08df56b0e422b6fd8baa262cec61e9cf",
    FLOOR_METHOD: "3d8c14cccf9306766a4993bad9ea39501bbc9c812af9e79b393875d5d3c09d34",
    LAW_METHOD: "93c7727c1c24fb5b7ed725fc4656651fe6e760a36a378d635a97e202b872fb88",
}
LIMITS = [
    "The results apply only to the saved six nominal simultaneous ce69/c3a8/62bd states and their 104 global bolt axes. The 108-axis proposal includes four internal ties absent from these global connector rows.",
    "The 625 psi DF-L No. 2 Fc_perpendicular comparison is the existing conditional dry-service reference, unchanged by load duration or size factors. Stock, grade, moisture, final-size classification and oblique/end-grain resistance are not qualified here.",
    "Positive saved normal force identifies represented active contact-cell area. Cell means and active-face means are not continuum stress peaks, contact refinement, unsampled clearance, local crushing/splitting or complete joint acceptance.",
    "The existing base sensitivity is four times the largest corner reaction divided by represented area and Fc_perpendicular. Its active-area extension and the separately labeled total-resultant quarter-area bound are arithmetic sensitivities, not pressure fields.",
    "Floor normals are eight uniform mean-footprint degrees of freedom. Saved raw cell forces are area-weighted projections; they do not resolve individual floor-cell uplift or a smaller actual pressure patch. Full supported area is used only under that explicit saved uniform-support law.",
    "N06 includes all eight saved footprints, with base_floor_left/right identified as the two floor rails. No additional runner footprint or support is inferred from a member name or proposed geometry.",
    "Timber/panel interfaces compare only the timber side against the conditional wood reference. Plywood bearing resistance and the nine panel/panel face groups have no adopted capacity in this packet.",
    "No friction coefficient, floor-friction test, anchor, serviceability threshold, common shaft pose, new internal-tie passive law, global stability or permanent release is established by this arithmetic.",
]


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and (path not in pins or pins[path] == digest),
            "conflicting or external source pin: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed: " + str(path))


def source_map(pins):
    return {path.relative_to(ROOT).as_posix(): digest for path, digest in sorted(pins.items())}


def functions(path, names, namespace):
    """Reuse only authenticated pure definitions, without module workflows."""
    tree = ast.parse(path.read_text(), filename=str(path))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require(len(nodes) == len(names) and all(not n.decorator_list for n in nodes),
            "pure helper census differs: " + str(path))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return SimpleNamespace(**{name: namespace[name] for name in names})


def bearing_expressions():
    """Retain the two actual bearing expressions, without historical shear work."""
    tree = ast.parse(BEARING.read_text(), filename=str(BEARING))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "base_comparisons")
    names = ("average_header_bearing_ratio", "quarter_area_corner_sensitivity_ratio")
    found = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=True):
                if isinstance(key, ast.Constant) and key.value in names:
                    require(key.value not in found, "duplicate retained bearing expression")
                    found[key.value] = compile(ast.Expression(body=value), str(BEARING), "eval")
    require(set(found) == set(names), "retained bearing formula census differs")
    return found


def ratios(expressions, reactions, area):
    if area == 0:
        require(sum(reactions) == 0, "nonzero signed normal force with no active area")
        return 0.0, 0.0
    namespace = {"reactions": reactions, "contact": {"area_mm2": area}, "psi": PSI_MPA}
    return tuple(float(eval(expressions[name], {"__builtins__": {"sum": sum, "max": max}}, namespace))
                 for name in ("average_header_bearing_ratio", "quarter_area_corner_sensitivity_ratio"))


def headers(path):
    """Read only NPY metadata, never array values, during preparation."""
    result = {}
    with ZipFile(path) as archive:
        for name in archive.namelist():
            require(name.endswith(".npy") and name[:-4] not in result, "unexpected NPZ member")
            with archive.open(name) as stream:
                prefix = stream.read(8)
                require(prefix[:6] == b"\x93NUMPY" and prefix[6:8] in (b"\x01\x00", b"\x02\x00", b"\x03\x00"),
                        "unsupported NPY header")
                size_bytes = 2 if prefix[6] == 1 else 4
                size = struct.unpack("<H" if size_bytes == 2 else "<I", stream.read(size_bytes))[0]
                require(size < 65536, "unexpected large NPY header")
                record = ast.literal_eval(stream.read(size).decode("utf-8" if prefix[6] == 3 else "latin1"))
                require(record["descr"] == "<f8" and record["fortran_order"] is False, "array representation differs")
                result[name[:-4]] = {**record, "shape": list(record["shape"])}
    return result


def sources(pins):
    for path, digest in PINS.items():
        bind(pins, path, digest)
    bind(pins, Path(__file__), sha(__file__))
    authenticate(pins)
    assessment, comparison = read(ASSESSMENT), read(COMPARISON)
    gravity_receipt, frame_receipt = read(GRAVITY / "receipt.json"), read(FRAME / "receipt.json")
    model, inputs, rows = read(MODEL), read(INPUTS), read(ROWS)
    carrier, contacts, corrected, materials = map(read, (CARRIER, CONTACTS, CORRECTED, MATERIALS))
    require(assessment["schema"] == "knee-bridge-gravity-operators/v1"
            and assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
            and assessment["operator_ready"] is True, "ce69 operators not ready")
    require(comparison["schema"] == "coupled_two_receiver_frame_clearance/v1"
            and comparison["response_sha256"] == PINS[RESPONSE]
            and comparison["frame_operator_directory"] == GRAVITY.relative_to(ROOT).as_posix()
            and comparison["physical_release"] is False
            and comparison["complete_joint_acceptance"] is False, "fresh response authority differs")
    require([(s["gap_scale"], s["case_id"]) for s in comparison["states"]]
            == [(gap, case) for gap in (0.0, 1.0) for case in CASES]
            and all(s["status"].startswith("PASS_CONDITIONAL_") for s in comparison["states"]),
            "six nominal and six reference state census differs")
    require(comparison["source_climber_weight_lb"] == 250
            and comparison["climber_load_scale"] == comparison["horizontal_load_scale"] == 1
            and comparison["comparison_horizontal_force_n"] == 300, "saved live load scales differ")
    for record in (assessment, comparison, model, inputs, gravity_receipt, frame_receipt):
        require(record["modeled_mass_kg"] == 225.19791414318078
                and record["dead_load_factor"] == 1.1110134616260479, "saved gravity binding differs")
    require(frame_receipt["global_receiver_bolt_axes"] == 104
            and frame_receipt["total_unique_proposal_bolt_axes"] == 108
            and frame_receipt["new_internal_bolts_are_global_connectors"] is False,
            "104 global / 108 proposal distinction differs")
    require(gravity_receipt["source_sha256"] == assessment["source_sha256"]
            and gravity_receipt["output_sha256"]["operator-assessment.json"] == PINS[ASSESSMENT],
            "gravity receipt does not bind assessment")
    for packet, receipt in ((GRAVITY, gravity_receipt), (FRAME, frame_receipt)):
        for relative, digest in receipt["output_sha256"].items():
            path = (packet / relative).resolve()
            require(path.is_relative_to(packet), "receipt output leaves packet")
            bind(pins, path, digest)
    for relative, digest in assessment["output_sha256"].items():
        require(gravity_receipt["output_sha256"][relative] == digest, "gravity output receipt differs")
    for record in (assessment, comparison, gravity_receipt, frame_receipt, inputs, contacts, corrected):
        for relative, digest in record["source_sha256"].items():
            bind(pins, ROOT / relative, digest)
    for path in (ASSESSMENT, MODEL, ROWS, OPERATORS):
        require(comparison["source_sha256"][path.relative_to(ROOT).as_posix()] == pins[path],
                "comparison consumed different operator source")
    require(frame_receipt["output_sha256"]["response/comparison.json"] == PINS[COMPARISON]
            and frame_receipt["output_sha256"]["response/response.npz"] == PINS[RESPONSE],
            "frame receipt does not bind response")
    require(materials["conditional_DF_L_No2_base_row"]["base_properties"]["Fc_perpendicular"] == 625,
            "conditional Fc_perpendicular reference changed")
    authenticate(pins)
    vector = functions(VECTORS, ("dot", "norm", "sub", "cross", "angle"), {"math": math})
    return SimpleNamespace(assessment=assessment, comparison=comparison, model=model, inputs=inputs,
                           rows=rows, carrier=carrier, contacts=contacts, corrected=corrected,
                           materials=materials, vector=vector)


def inventory(data):
    """Authenticate actual saved cell areas and joins, not bounding rectangles."""
    rows, v = data.rows, data.vector
    require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)), "raw row identities differ")
    # Some noncontact connector components share an axis ID. Raw row numbers
    # identify those components; consumed normal-contact cell IDs must be unique.
    contact_ids = [r["row_id"] for r in rows if r["ownership"]["role"] in ("timber_or_panel_contact", "floor_normal")]
    require(len(contact_ids) == len(set(contact_ids)), "normal-contact cell IDs duplicated")
    bodies = data.model["body_names"]
    members = {m["member_id"]: m for m in data.inputs["members"]}
    require(len(bodies) == 50 and len(set(bodies)) == 50 and set(members) == set(bodies)
            and Counter(m["member_kind"] for m in members.values()) == {"timber": 44, "panel": 6},
            "current body/material census differs")
    retained = [r["row"] for r in rows if r["ownership"]["second_body"] != "floor"]
    raw_to_q = {row: i for i, row in enumerate(retained)}
    require(len(retained) == 1588, "retained nonfloor prefix differs")
    old_cells = {c["name"]: c for c in data.carrier["contact_cell_ownership"]}
    require(len(old_cells) == len(data.carrier["contact_cell_ownership"]), "carrier cell IDs duplicated")
    top_cells, top_faces = {}, {}
    for cleat in data.corrected["cleats"]:
        for face in cleat["faces"]:
            top_faces[(face["host"], cleat["block"])] = face
        for i, cell in enumerate(cleat["rows"]):
            if cell["kind"] == "contact":
                top_cells[f"{cleat['block']}/contact-cell-{i}"] = {**cell, "first": cell["host"], "second": cleat["block"]}
    groups, floors, cells = {}, {}, []
    for row in rows:
        own = row["ownership"]
        role = own["role"]
        if role not in ("timber_or_panel_contact", "floor_normal"):
            continue
        name = row["row_id"]
        first, second = own["first_body"], own["second_body"]
        require(row["family"] == "unilateral_springa" and row["law"]["intended_law"] == "compression_only"
                and row["law"]["force_law"] == "k * max(q_mm, 0)", "saved contact law differs: " + name)
        if name in top_cells:
            cell = top_cells[name]
            normal = [-x for x in cell["direction_xyz"]]
            point, area = cell["point_mm"], cell["area_mm2"]
            face = top_faces[(first, second)]
            group_id = "corrected/" + first + "/" + second
            face_area, center = face["exact_finished_area_mm2"], face["center_mm"]
            area_ref = {"source": CORRECTED.relative_to(ROOT).as_posix(), "row_id": name}
            require(math.isclose(row["contact_area_mm2"], area, rel_tol=0, abs_tol=1e-9),
                    "explicit corrected cell area differs: " + name)
        else:
            require(name in old_cells, "missing saved cell area: " + name)
            cell = old_cells[name]
            normal, point, area = cell["normal_xyz"], cell["point_xyz_mm"], cell["area_mm2"]
            require(cell["kind"] == role, "saved cell role differs: " + name)
            if role == "floor_normal":
                patch_index = cell["source_floor_patch_index"]
                face = data.contacts["floor_patches"][patch_index]
                require(face["member_id"] == first and second == "floor", "floor patch member differs")
                group_id = "floor/" + first
                require(v.norm(v.sub(normal, [0, 0, 1])) < 1e-8, "floor normal is not signed upward")
            else:
                patch_index = cell["source_patch_index"]
                face = data.contacts["contact_patches"][patch_index]
                require(face["member_ids"] == [first, second], "saved patch member pair differs: " + name)
                require(v.norm([a + b for a, b in zip(normal, face["normal_on_first_xyz"], strict=True)]) < 1e-8,
                        "saved compression direction is not opposite outward normal: " + name)
                group_id = "legacy/contact-patch-" + str(patch_index)
            face_area, center = face["area_mm2"], face["centroid_xyz_mm"]
            area_ref = {"source": CARRIER.relative_to(ROOT).as_posix(), "cell_name": name,
                        "geometry_source": CONTACTS.relative_to(ROOT).as_posix(), "patch_index": patch_index}
        k = row["law"]["stiffness_N_per_mm"]
        require((first, second) == (cell["first"], cell["second"])
                and v.norm(v.sub(point, own["point_mm"])) < GEOMETRY_TOL_MM
                and v.norm(v.sub(normal, own["direction_global_xyz"])) < 1e-8
                and abs(v.norm(normal) - 1) < 1e-8
                and math.isfinite(area) and area > 0
                and math.isclose(k, 100 * area, rel_tol=1e-12, abs_tol=1e-6),
                "signed ownership/point/direction/explicit area/stiffness join differs: " + name)
        domain = row["law"].get("table_domain_mm")
        if name in top_cells:
            require(set(row["law"]) == {"stiffness_N_per_mm", "force_law", "intended_law"},
                    "corrected explicit mathematical contact law differs: " + name)
        else:
            table = row["law"]["scalar_force_table_N_mm"]
            require(domain == [-10.0, 10.0] and table[:2] == [[0.0, -10.0], [0.0, 0.0]]
                    and math.isclose(table[2][0], 10 * k, rel_tol=1e-12, abs_tol=1e-6)
                    and table[2][1] == 10.0, "finite contact table differs: " + name)
        record = {"row": row["row"], "row_id": name, "first": first, "second": second,
                  "role": role, "point_mm": point, "normal_force_on_first_xyz": normal,
                  "area_mm2": area, "k_n_per_mm": k, "area_reference": area_ref,
                  "group_id": group_id, "q_index": raw_to_q.get(row["row"]),
                  "serialized_table_domain_mm": domain}
        cells.append(record)
        target = floors if role == "floor_normal" else groups
        group = target.setdefault(group_id, {"group_id": group_id, "first": first, "second": second,
                                            "geometry_area_mm2": face_area, "datum_mm": center,
                                            "normal_force_on_first_xyz": normal, "cells": []})
        require(group["first"] == first and group["second"] == second
                and v.norm(v.sub(group["normal_force_on_first_xyz"], normal)) < 1e-8,
                "face grouping changes signed owner or normal")
        group["cells"].append(record)
    for group in list(groups.values()) + list(floors.values()):
        area = sum(c["area_mm2"] for c in group["cells"])
        # Retained extracted face areas include holes; allow only the recorded geometry accuracy.
        tolerance = None
        if group["group_id"].startswith("corrected/"):
            corners = top_faces[(group["first"], group["second"])]["corners_mm"]
            outer_perimeter = 2 * (v.norm(v.sub(corners[1], corners[0])) + v.norm(v.sub(corners[2], corners[0])))
            tolerance = 1e-6 + 1e-5 * outer_perimeter
        if group["group_id"].startswith("legacy/"):
            patch = data.contacts["contact_patches"][group["cells"][0]["area_reference"]["patch_index"]]
            tolerance = 1e-6 + 1e-5 * patch["boundary_perimeter_mm"]
        if group["second"] == "floor":
            patch = data.contacts["floor_patches"][group["cells"][0]["area_reference"]["patch_index"]]
            tolerance = 1e-6 + 1e-5 * patch["boundary_perimeter_mm"]
        require(tolerance is not None and abs(area - group["geometry_area_mm2"]) <= tolerance,
                "cell/finished face area closure: " + group["group_id"])
        group["represented_area_mm2"] = area
        group["signed_cell_minus_geometry_area_mm2"] = area - group["geometry_area_mm2"]
        group["geometry_area_tolerance_mm2"] = tolerance
        wood = [body for body in (group["first"], group["second"])
                if body != "floor" and members[body]["member_kind"] == "timber"]
        group["wood_bodies"] = wood
        group["kind"] = "floor" if group["second"] == "floor" else ("timber/timber" if len(wood) == 2 else "timber/panel" if wood else "panel/panel")
        group["base_header_interface"] = group["kind"] == "timber/timber" and "base_header" in (group["first"], group["second"])
        group["normal_to_grain_degrees"] = {}
        for body in wood:
            grain = members[body]["reduced_geometry_descriptor"]["grain_global_xyz"]
            require(abs(v.norm(grain) - 1) < 1e-7, "invalid recorded grain: " + body)
            group["normal_to_grain_degrees"][body] = v.angle(group["normal_force_on_first_xyz"], grain)
    floor_order = sorted(floors.values(), key=lambda g: g["first"])
    require(tuple(g["first"] for g in floor_order) == FLOOR_MEMBERS
            and [len(g["cells"]) for g in floor_order] == [38, 38, 4, 4, 4, 4, 4, 4], "eight exact floor footprints differ")
    for i, (group, saved) in enumerate(zip(floor_order, data.comparison["floor_footprints"], strict=True)):
        group["q_index"] = 1588 + 3 * i
        total_k = sum(c["k_n_per_mm"] for c in group["cells"])
        point = [sum(c["k_n_per_mm"] * c["point_mm"][axis] for c in group["cells"]) / total_k for axis in range(3)]
        require(saved["member_id"] == group["first"] and saved["source_cell_count"] == len(group["cells"])
                and math.isclose(saved["normal_stiffness_n_per_mm"], total_k, rel_tol=1e-12, abs_tol=1e-6)
                and v.norm(v.sub(point, saved["resultant_point_xyz_mm"])) < GEOMETRY_TOL_MM,
                "saved floor lumping/area/point closure differs: " + group["first"])
        group["normal_stiffness_n_per_mm"] = total_k
        group["resultant_point_mm"] = point
        group["floor_rail"] = group["first"] in FLOOR_MEMBERS[:2]
    require(Counter(g["kind"] for g in groups.values()) == {"timber/timber": 82, "timber/panel": 26, "panel/panel": 9}
            and len(cells) == 1170 and sum(c["role"] == "floor_normal" for c in cells) == 100
            and sum(g["base_header_interface"] for g in groups.values()) == 16
            and sum(len(g["cells"]) for g in groups.values() if g["wood_bodies"]) == 856,
            "current contact census differs")
    response_headers, operator_headers = headers(RESPONSE), headers(OPERATORS)
    expected = {case + suffix + field: shape for case in CASES for suffix in ("_zero", "_gap")
                for field, shape in (("_raw_force_n", [1888]), ("_lumped_q_mm", [1612]), ("_rigid_coordinates", [300]))}
    require(set(response_headers) == set(expected)
            and all(response_headers[k]["shape"] == shape for k, shape in expected.items())
            and operator_headers["D"]["shape"] == [1888, 300], "saved array census differs")
    census = {"nominal_cases": 6, "raw_rows": 1888, "nonfloor_q_rows": 1588, "lumped_q_rows": 1612,
              "rigid_columns": 300, "bodies": 50, "wood_face_groups": 108, "wood_contact_cells": 856,
              "timber_timber_faces": 82, "timber_panel_wood_side_faces": 26,
              "excluded_panel_panel_faces": 9, "excluded_panel_panel_cells": 214,
              "base_header_timber_faces": 16, "base_header_face_case_records": 96,
              "wood_face_case_records": 648, "wood_cell_case_records": 5136,
              "floor_footprints": 8, "floor_normal_cells": 100,
              "floor_footprint_case_records": 48, "floor_cell_case_records": 600,
              "floor_rail_case_records": 12, "global_bolt_axes": 104, "proposal_bolt_axes": 108}
    return SimpleNamespace(groups=list(groups.values()), floors=floor_order, cells=cells,
                           retained=retained, census=census, array_headers=response_headers)


def assess_saved(output, data, geometry):
    """Parent-only arithmetic; load D and saved f/q, never H or a solver."""
    import numpy as np

    require(sys.version.split()[0] == data.assessment["runtime"]["python"]
            and np.__version__ == data.assessment["runtime"]["numpy"], "saved Python/NumPy runtime differs")
    wrench = functions(WRENCH, ("wrench",), {"np": np}).wrench
    expressions = bearing_expressions()
    fc = 625 * PSI_MPA
    centers = {body: np.mean([data.model["physical_node_coordinates_mm"][str(n)]
                             for n in sorted(set(data.model["body_nodes"][body]))], axis=0)
               for body in data.model["body_names"]}
    body_index = {name: i for i, name in enumerate(data.model["body_names"])}
    face_records, floor_records, case_audits = [], [], []
    cell_path = output / "cell-actions.jsonl"
    with np.load(OPERATORS, allow_pickle=False) as source, np.load(RESPONSE, allow_pickle=False) as saved, cell_path.open("w") as stream:
        D = source["D"]
        require(np.all(np.isfinite(D)), "nonfinite signed D operator")
        for cell in geometry.cells:
            expected = np.zeros(300)
            direction = np.array(cell["normal_force_on_first_xyz"])
            for body, sign in ((cell["first"], -1), (cell["second"], 1)):
                if body == "floor":
                    continue
                i = body_index[body]
                expected[6 * i:6 * i + 3] = sign * direction
                expected[6 * i + 3:6 * i + 6] = sign * np.cross(np.array(cell["point_mm"]) - centers[body], direction) / 1000
            error = float(np.max(abs(D[cell["row"]] - expected)))
            require(error < 1e-10, f"signed raw D cell geometry: {cell['row_id']} error={error!r}")
        for case in CASES:
            state = next(s for s in data.comparison["states"] if s["case_id"] == case and s["gap_scale"] == 1.0)
            force, q = saved[case + "_gap_raw_force_n"], saved[case + "_gap_lumped_q_mm"]
            require(np.all(np.isfinite(force)) and np.all(np.isfinite(q)), "nonfinite saved state: " + case)
            audit = {"case_id": case, "gap_scale": 1.0, "source_status": state["status"],
                     "source_audit": state["audit"], "contact_law_error_n": 0.0,
                     "floor_projection_error_n": 0.0, "wrench_force_error_n": 0.0,
                     "wrench_moment_error_nmm": 0.0, "force_closure_branch_disagreements": []}
            for group in [g for g in geometry.groups if g["wood_bodies"]] + geometry.floors:
                floor = group["second"] == "floor"
                reactions = [float(force[c["row"]]) for c in group["cells"]]
                total = sum(reactions)
                normal_q = float(q[group["q_index"]]) if floor else None
                if floor:
                    expected = group["normal_stiffness_n_per_mm"] * max(normal_q, 0)
                    error = abs(total - expected)
                    require(error < LAW_TOL_N and normal_q <= 10,
                            f"floor signed normal law: {case}/{group['first']} R={total!r}, q={normal_q!r}, expected={expected!r}")
                    audit["contact_law_error_n"] = max(audit["contact_law_error_n"], error)
                active_area = 0.0
                cell_means, actions = [], []
                for cell, reaction in zip(group["cells"], reactions, strict=True):
                    require(reaction >= 0, f"negative signed normal: {case}/{cell['row_id']} f={reaction!r}")
                    active = reaction > 0
                    closure = normal_q if floor else float(q[cell["q_index"]])
                    if floor:
                        error = abs(reaction - cell["k_n_per_mm"] / group["normal_stiffness_n_per_mm"] * total)
                        audit["floor_projection_error_n"] = max(audit["floor_projection_error_n"], error)
                        require(error < LAW_TOL_N, f"floor area-weight projection differs: {case}/{cell['row_id']}")
                    else:
                        expected = cell["k_n_per_mm"] * max(closure, 0)
                        error = abs(reaction - expected)
                        audit["contact_law_error_n"] = max(audit["contact_law_error_n"], error)
                        require(error < LAW_TOL_N and closure <= 10,
                                f"saved compression law: {case}/{cell['row_id']} f={reaction!r}, q={closure!r}, expected={expected!r}")
                    if active != (closure > 0):
                        audit["force_closure_branch_disagreements"].append(
                            {"row_id": cell["row_id"], "signed_normal_n": reaction, "saved_q_mm": closure,
                             "area_mm2": cell["area_mm2"], "q_is_footprint_mean": floor})
                        require(abs(closure) <= GAP_TOL_MM or reaction <= LAW_TOL_N,
                                f"resolved force/closure branch disagreement: {case}/{cell['row_id']}")
                    if not floor:
                        active_area += cell["area_mm2"] if active else 0.0
                    mean = reaction / cell["area_mm2"]
                    cell_means.append(mean / fc)
                    f = np.array(cell["normal_force_on_first_xyz"]) * reaction
                    action = {"point_mm": cell["point_mm"], "force_n": f.tolist(), "free_moment_nmm": [0, 0, 0]}
                    actions.append(action)
                    record = {"case_id": case, "gap_scale": 1.0, "group_id": group["group_id"],
                              "row": cell["row"], "row_id": cell["row_id"], "first": cell["first"],
                              "second": cell["second"], "area_mm2": cell["area_mm2"],
                              "signed_normal_n": reaction, "active_positive_saved_force": active,
                              "saved_q_mm": closure, "q_is_footprint_mean": floor,
                              "local_mean_mpa": mean, "conditional_Fc_perp_ratio": mean / fc,
                              "force_on_first_xyz_n": f.tolist(), "force_on_second_xyz_n": (-f).tolist(),
                              "point_mm": cell["point_mm"], "is_stress_peak": False}
                    stream.write(json.dumps(record, allow_nan=False, sort_keys=True) + "\n")
                signed_wrench = wrench(actions, np.array(group["datum_mm"]))
                # Check both signed body columns against actual point-action recovery.
                ids = [c["row"] for c in group["cells"]]
                for body, sign in ((group["first"], 1), (group["second"], -1)):
                    if body == "floor":
                        continue
                    i = body_index[body]
                    recovered = -D[ids, 6 * i:6 * i + 6].T @ force[ids]
                    recovered[3:] = 1000 * recovered[3:] + np.cross(centers[body] - group["datum_mm"], recovered[:3])
                    error = recovered - sign * signed_wrench
                    f_error, m_error = float(np.max(abs(error[:3]))), float(np.max(abs(error[3:])))
                    audit["wrench_force_error_n"] = max(audit["wrench_force_error_n"], f_error)
                    audit["wrench_moment_error_nmm"] = max(audit["wrench_moment_error_nmm"], m_error)
                    require(f_error < 1e-7 and m_error < 1e-4,
                            f"signed D/point-wrench closure: {case}/{group['group_id']}/{body} force_error={f_error!r}, moment_error={m_error!r}")
                if floor:
                    active_count = sum(r > 0 for r in reactions)
                    expected_count = len(group["cells"]) if total > 0 else 0
                    require(active_count == expected_count,
                            f"floor uniform projection active mask: {case}/{group['first']} R={total!r}, active_cells={active_count}, expected_cells={expected_count}")
                    # Use exactly the inventory's ordered sum of the same area
                    # terms. A loop accumulator and Python 3.12 sum can differ
                    # by ulps even when every cell is active; do not relax the
                    # guard or infer full support from a near-equal area.
                    active_area = float(sum(c["area_mm2"] for c, r in zip(group["cells"], reactions, strict=True) if r > 0))
                average, quarter = ratios(expressions, reactions, active_area)
                full_average, full_quarter = ratios(expressions, reactions, group["represented_area_mm2"])
                record = {"case_id": case, "gap_scale": 1.0, "group_id": group["group_id"],
                          "first": group["first"], "second": group["second"], "kind": group["kind"],
                          "signed_normal_resultant_n": total, "active_positive_force_area_mm2": active_area,
                          "active_positive_force_cells": sum(r > 0 for r in reactions),
                          "represented_supported_area_mm2": group["represented_area_mm2"],
                          "geometry_area_mm2": group["geometry_area_mm2"],
                          "normal_to_grain_degrees": group["normal_to_grain_degrees"],
                          "datum_mm": group["datum_mm"], "force_on_first_xyz_n": signed_wrench[:3].tolist(),
                          "moment_on_first_xyz_nmm": signed_wrench[3:].tolist(),
                          "active_area_average_Fc_perp_ratio": average,
                          "supported_area_average_Fc_perp_ratio": full_average,
                          "maximum_cell_mean_Fc_perp_ratio": max(cell_means), "is_stress_peak": False}
                if floor:
                    # A positive mean footprint uses its full saved area only under uniform projection.
                    require(active_area == group["represented_area_mm2"] if total > 0 else active_area == 0,
                            f"floor projection unexpectedly selects a partial area: {case}/{group['first']} R={total!r}, active_area={active_area!r}, represented_area={group['represented_area_mm2']!r}")
                    record.update(floor_rail=group["floor_rail"], footprint_mean_q_mm=normal_q,
                                  model_uniform_active_footprint=total > 0,
                                  floor_rail_wood_bearing_passed=full_average <= 1,
                                  actual_pressure_patch_resolved=False)
                    floor_records.append(record)
                else:
                    record.update(base_header_interface=group["base_header_interface"],
                                  flush_face_wood_bearing_passed=max(cell_means) <= 1,
                                  active_area_average_passed=average <= 1)
                    if group["base_header_interface"]:
                        record.update(base_bearing_average_passed=average <= 1,
                                      existing_supported_quarter_corner_ratio=full_quarter,
                                      quarter_active_area_corner_sensitivity_ratio=quarter,
                                      base_bearing_quarter_area_sensitivity_passed=quarter <= 1,
                                      total_resultant_quarter_active_area_bound_ratio=4 * average,
                                      quarter_formula_has_four_saved_corners=len(reactions) == 4)
                    face_records.append(record)
            case_audits.append(audit)
    require(len(face_records) == 648 and len(floor_records) == 48, "finite result census differs")
    base = [r for r in face_records if r["base_header_interface"]]
    checks = {
        "base_bearing_average": all(r["base_bearing_average_passed"] for r in base),
        "base_bearing_quarter_area_sensitivity": all(r["base_bearing_quarter_area_sensitivity_passed"] for r in base),
        "flush_face_wood_bearing": all(r["flush_face_wood_bearing_passed"] and r["active_area_average_passed"] for r in face_records),
        "floor_rail_wood_bearing": all(r["floor_rail_wood_bearing_passed"] for r in floor_records),
    }
    write(output / "bearing-results.json", {"schema": "same-state-contact-bearing-arithmetic/v1",
          "case_audits": case_audits, "wood_faces": face_records, "floor_footprints": floor_records,
          "conditional_reference_checks": checks, "limits": LIMITS})
    return {"conditional_reference_checks": checks,
            "status": "PASS_CONDITIONAL_BEARING_ARITHMETIC" if all(checks.values()) else "FAIL_CONDITIONAL_BEARING_ARITHMETIC",
            "maximum_base_average_ratio": max(r["active_area_average_Fc_perp_ratio"] for r in base),
            "maximum_base_quarter_active_area_corner_ratio": max(r["quarter_active_area_corner_sensitivity_ratio"] for r in base),
            "maximum_wood_cell_mean_ratio": max(r["maximum_cell_mean_Fc_perp_ratio"] for r in face_records),
            "maximum_floor_uniform_mean_ratio": max(r["supported_area_average_Fc_perp_ratio"] for r in floor_records),
            "maximum_floor_rail_uniform_mean_ratio": max(r["supported_area_average_Fc_perp_ratio"] for r in floor_records if r["floor_rail"]),
            "force_closure_branch_disagreement_count": sum(len(a["force_closure_branch_disagreements"]) for a in case_audits),
            "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}}


def execute(output, numerical):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "output must be a fresh immediate RAW child")
    pins = {}
    output.mkdir(parents=True)
    report = {"schema": "contact-bearing-completion/v1", "mode": "build" if numerical else "prepare",
              "status": "PREPARING", "numerical_arithmetic_run": False,
              "frame_solve_run": False, "native_solve_run": False, "CAD_run_executed": False,
              "tests_or_review_run": False, "physical_release": False, "complete_joint_acceptance": False,
              "global_stability_acceptance": False, "proposal_adopted": False, "limits": LIMITS}
    terminal = None
    try:
        data = sources(pins)
        geometry = inventory(data)
        report.update(census=geometry.census, source_pin_count=len(pins), source_sha256=source_map(pins),
                      producer_sha256=sha(__file__), Fc_perpendicular_psi=625,
                      Fc_perpendicular_mpa=625 * PSI_MPA, case_ids=list(CASES), gap_scale=1.0,
                      expected_arithmetic_runtime={name: data.assessment["runtime"][name] for name in ("python", "numpy")},
                      source_law_tolerance_n=LAW_TOL_N, source_gap_tolerance_mm=GAP_TOL_MM,
                      prepared_API={"prepare": "prepare(output): stdlib provenance/geometry/NPY headers only",
                                    "build": "build(output): saved six-case NumPy arithmetic only; parent execution",
                                    "output": "fresh immediate child of rawlocal/contact-bearing-completion",
                                    "raw_force_sign": "positive scalar compression; force on first = scalar * saved direction; second = negative",
                                    "active_area": "sum of explicit saved cell areas with strictly positive saved normal force"},
                      readiness="READY_FOR_PARENT_ARITHMETIC_ONLY", numerical_arithmetic_run=numerical)
        write(output / "geometry-inventory.json", {"census": geometry.census, "contact_faces": geometry.groups,
                                                  "floor_footprints": geometry.floors})
        shutil.copyfile(__file__, output / "producer.py.snapshot")
        if numerical:
            report.update(assess_saved(output, data, geometry))
        else:
            bearing_expressions()
            report.update(status="PREPARED_NOT_NUMERICALLY_RUN", array_headers=geometry.array_headers,
                          runtime={"python": sys.version.split()[0], "numerical_imports": False})
        authenticate(pins)
        report["source_authentication_before_after"] = True
        write(output / "report.json", report)
    except Exception as exc:  # noqa: BLE001 -- Preserve a STOP receipt for any parent arithmetic failure.
        terminal = f"{type(exc).__name__}: {exc}"
        report.update(status="STOP", terminal_exception=terminal, source_sha256=source_map(pins))
        write(output / "report.json", report)
    write(output / "receipt.json", {"schema": "contact-bearing-completion-receipt/v1",
          "status": report["status"], "terminal_exception": terminal,
          "producer_sha256": sha(__file__), "source_sha256": source_map(pins),
          "source_authentication_before_after": report.get("source_authentication_before_after", False),
          "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
          "numerical_arithmetic_run": report["numerical_arithmetic_run"], "physical_release": False})
    require(terminal is None, terminal or "failed arithmetic")
    return report


def prepare(output):
    """Standard-library source/API/geometry preparation only."""
    return execute(output, numerical=False)


def build(output):
    """Parent-owned finite arithmetic on six saved simultaneous states."""
    return execute(output, numerical=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prepare", action="store_true", help="standard-library preparation; no array values")
    args = parser.parse_args()
    result = prepare(args.output) if args.prepare else build(args.output)
    print(json.dumps({"status": result["status"], "output": str(args.output)}))
