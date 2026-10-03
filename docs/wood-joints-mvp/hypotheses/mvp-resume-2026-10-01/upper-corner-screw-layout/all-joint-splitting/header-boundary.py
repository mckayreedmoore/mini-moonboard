"""Prepare cut-capable boundary fields for six header-related cleats.

This source-bound producer maps only the six reviewed header interfaces. It
keeps every remaining body action at its saved point, preserves unsupported
source components explicitly, and performs no strength or compatibility
calculation. Parent owns execution and numeric validation.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
UPPER = HERE.parent
RESUME = UPPER.parent
ROOT = next(
    path for path in HERE.parents if (path / "current-candidate.json").is_file()
)

MEMBER = RESUME / "member-screen-attempt02/four-screw-layout01"
INPUT_DIR = UPPER / "rawlocal/header-local-transfer/attempt01"
REMAINING_DIR = UPPER / "rawlocal/remaining-block-transverse/attempt01"
ALL_JOINT_DIR = HERE / "rawlocal/attempt01"
HEADER_MAP_DIR = UPPER / "rawlocal/header-traction-map/attempt01"
SEAT_SCREEN = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-washer-seat-screen-attempt01/seat-screen.json"
)
CONTACT_HELPER = ROOT / "fea/wood_joint_reduced_contacts.py"
GEOMETRY_HELPER = ROOT / "fea/wood_joint_reduced_geometry.py"
HEADER_MAP = UPPER / "header-traction-map.py"
BORE_MAP = UPPER / "corner-bore-wall.py"
TOP_HOST = UPPER / "top-host-physical-actions.py"

CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
BODIES = (
    "center_post_cleat_left",
    "center_post_cleat_right",
    "center_principal_cleat_left",
    "center_principal_cleat_right",
    "knee_outer_left_inner_frame_block",
    "knee_outer_right_inner_frame_block",
)
WASHER_SCENARIO = "header-traction-map: minimum-area plain washer envelope"
CONTACT_CELL_SIZE_MM = 100.0
MIN_CONTACT_DIVISIONS = 2
GEOMETRY_TOL_MM = 1e-6
ALIGN_TOL = 1e-8
FORCE_ACCOUNTING_TOL_N = 1e-7
MOMENT_ACCOUNTING_TOL_NMM = 1e-5
FLAGS = {
    "native_mechanics_executed": False,
    "cad_or_frame_solve_executed": False,
    "new_resistance_established": False,
    "splitting_qualified": False,
    "existing_host_redistribution_solved": False,
    "elastic_compatibility_solved": False,
    "complete_joint_acceptance": False,
    "formal_criterion_acceptance": False,
    "fabrication_release": False,
    "physical_release": False,
    "proposal_108_adopted": False,
}

PINS = {
    INPUT_DIR
    / "inputs.json": "cccd8969132c30e996fe5d3509069dbe851720786cec92a46a064cc0f7c0758b",
    INPUT_DIR
    / "model.json": "eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52",
    INPUT_DIR
    / "receipt.json": "3b3afc6924dee426c4f0073077e119d906efddcb5ed03a683ec4a3f16fc189a8",
    MEMBER
    / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    MEMBER
    / "action-section-arrays.npz": "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    MEMBER
    / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    REMAINING_DIR
    / "checks.json": "f3118804d3a03df66d274d783ca93248757ac3d629de4a874d23e85da9a61f19",
    REMAINING_DIR
    / "receipt.json": "dce3437a105cdd269aec9ff98ac831c00d6e64e34a807c42254030ca4fffb519",
    REMAINING_DIR
    / "cuts.jsonl.gz": "86757d2db86751aa5cba5343df0065ac3d38cc7d69eeab71f02c55eedc72d4cc",
    ALL_JOINT_DIR
    / "checks.json": "91124cdd68bd440d5221047f77d81b47f13cbcf06e68093f3ebc6c5091a74fb9",
    ALL_JOINT_DIR
    / "receipt.json": "1c037ed5f138cf738f4f4ca8628e377ef2ffbcf332419f496a5b03aab7d759b9",
    ALL_JOINT_DIR
    / "receiver-cuts.jsonl": "9ed12678cc317fac8e0797d295ee8c986e0c7033707fd27361f2c64252077381",
    HEADER_MAP_DIR
    / "result.json": "39d63b41dc495659b02cb4ff4fb638a19a491bc09e6ea3fd76a70314db08a837",
    HEADER_MAP_DIR
    / "receipt.json": "1d454a949640a9b43d6ae3e3cf56ca20705e12ff6ae06f9bb51c1749623d96fd",
    HEADER_MAP: "87bd3b14e6961b95e04788d89ece412334ff5cc5f4ad735433a8ced97472d34d",
    UPPER
    / "header-traction-map.md": "d1a1f1af6036551b420ef8c52f01887184d4e43f730483dde290a6258c823a76",
    BORE_MAP: "0ad9c88be2496f1b2ae9b06cb31f0cb7d9d95a236ffb4b2dc586873b7cf4a185",
    TOP_HOST: "0f005656656d26d1003c3ff4317c696172f2399de438c287ff9a8ea12e926b49",
    CONTACT_HELPER: "4e088d485cee8953bfdca411f646f18abfb49271c9d8f3b46044588a6a7c1ce7",
    GEOMETRY_HELPER: "7483dd6bac169ade5c731af2b22e8d40d8132cd0881ddfda2642ef5430208200",
    SEAT_SCREEN: "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def key(path: Path) -> str:
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def authenticate(pins: dict[Path, str]) -> None:
    for path, expected in pins.items():
        require(path.is_file(), f"missing frozen source: {path}")
        observed = sha(path)
        require(observed == expected, f"changed frozen source: {path}; got {observed}")


def module(path: Path, name: str) -> Any:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"helper unavailable: {path}")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def vec(value: Any) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    require(
        result.shape == (3,) and np.isfinite(result).all(), "invalid saved 3-vector"
    )
    return result


def unit(value: Any, label: str) -> np.ndarray:
    result = vec(value)
    magnitude = float(np.linalg.norm(result))
    require(magnitude > 0.0, f"zero direction: {label}")
    return result / magnitude


def wrench(actions: list[dict[str, Any]], datum: np.ndarray) -> np.ndarray:
    result = np.zeros(6)
    for action in actions:
        force = vec(action["force_n"])
        point = vec(action["point_mm"])
        result[:3] += force
        result[3:] += np.cross(point - datum, force)
        result[3:] += vec(action["free_moment_nmm"])
    return result


def point_wrench(point: np.ndarray, force: np.ndarray, datum: np.ndarray) -> np.ndarray:
    return np.r_[force, np.cross(point - datum, force)]


def transport_wrench(
    wrench_value: np.ndarray, from_datum: np.ndarray, to_datum: np.ndarray
) -> np.ndarray:
    """Express a six-component wrench about a different saved datum."""
    force = wrench_value[:3]
    moment = wrench_value[3:] + np.cross(from_datum - to_datum, force)
    return np.r_[force, moment]


def field_wrench(actions: list[dict[str, Any]], datum: np.ndarray) -> np.ndarray:
    result = np.zeros(6)
    for action in actions:
        force = vec(action["force_xyz_n"])
        point = vec(action["point_xyz_mm"])
        result[:3] += force
        result[3:] += np.cross(point - datum, force)
    return result


def local_guv(point: np.ndarray, geometry: dict[str, Any]) -> list[float]:
    start = vec(geometry["start"])
    axes = [unit(geometry[name], name) for name in ("axis", "section_u", "section_v")]
    return [float(np.dot(point - start, axis)) for axis in axes]


def max_abs(value: np.ndarray) -> float:
    return float(np.max(np.abs(value))) if value.size else 0.0


def receipt_output(receipt: dict[str, Any], filename: str, digest: str) -> None:
    require(
        receipt.get("output_sha256", {}).get(filename) == digest,
        f"receipt output binding differs: {filename}",
    )


def source_context(pins: dict[Path, str]) -> dict[str, Any]:
    inputs = read(INPUT_DIR / "inputs.json")
    model = read(INPUT_DIR / "model.json")
    input_receipt = read(INPUT_DIR / "receipt.json")
    all_joint = read(ALL_JOINT_DIR / "checks.json")
    all_joint_receipt = read(ALL_JOINT_DIR / "receipt.json")
    remaining = read(REMAINING_DIR / "checks.json")
    remaining_receipt = read(REMAINING_DIR / "receipt.json")
    member_geometry = read(MEMBER / "geometry.json")
    member_results = read(MEMBER / "member-results.json")
    header_map = read(HEADER_MAP_DIR / "result.json")
    header_map_receipt = read(HEADER_MAP_DIR / "receipt.json")

    receipt_output(input_receipt, "inputs.json", pins[INPUT_DIR / "inputs.json"])
    receipt_output(input_receipt, "model.json", pins[INPUT_DIR / "model.json"])
    receipt_output(
        all_joint_receipt, "checks.json", pins[ALL_JOINT_DIR / "checks.json"]
    )
    receipt_output(
        all_joint_receipt,
        "receiver-cuts.jsonl",
        pins[ALL_JOINT_DIR / "receiver-cuts.jsonl"],
    )
    receipt_output(
        remaining_receipt, "checks.json", pins[REMAINING_DIR / "checks.json"]
    )
    receipt_output(
        remaining_receipt, "cuts.jsonl.gz", pins[REMAINING_DIR / "cuts.jsonl.gz"]
    )
    receipt_output(header_map_receipt, "result.json", pins[HEADER_MAP_DIR / "result.json"])
    require(
        input_receipt["status"]
        == "PREPARED_HEADER_INPUT_CONTRACT_FOR_METHOD_SELECTION",
        "header input contract is not the prepared current packet",
    )
    require(
        model["schema"] == "header_local_transfer_frozen_geometry/v1"
        and inputs["schema"] == "header_local_transfer_frozen_actions/v1",
        "header transfer schema differs",
    )
    require(
        model["source_identity"]["candidate"]
        == "compact-floor-flush-wood-joints-development"
        and model["source_identity"]["development_revision"]
        == "upper-corner-screw-row-2026-10-02-v1",
        "header transfer candidate/revision differs",
    )
    require(
        all_joint["reviewed_authority"]["bolt_axes"] == 104
        and all_joint["reviewed_authority"]["cases"] == list(CASES),
        "source is not the reviewed six-case 104-axis authority",
    )
    require(
        all_joint["proposal_adopted"] is False
        and all_joint["unadopted_108_axis_proposal"]["proposal_adopted"] is False,
        "108-axis proposal must remain separate and unadopted",
    )
    require(
        all_joint["coverage"]["block_duties"] == 24
        and all_joint["coverage"]["joint_duties"] == 30,
        "frozen all-joint closure coverage differs",
    )
    require(
        not any(
            model.get(flag, False)
            for flag in (
                "native_readiness",
                "mechanics_executed",
                "new_resistance_established",
                "complete_joint_acceptance",
                "physical_release",
            )
        ),
        "input contract carries a forbidden acceptance flag",
    )
    require(
        [case["case_id"] for case in inputs["cases"]] == list(CASES),
        "header input case order differs",
    )
    require(
        [case["case_id"] for case in member_results["cases"]] == list(CASES),
        "member archive case order differs",
    )
    require(
        member_results["output_sha256"]["geometry.json"]
        == pins[MEMBER / "geometry.json"]
        and member_results["output_sha256"]["action-section-arrays.npz"]
        == pins[MEMBER / "action-section-arrays.npz"],
        "member results do not bind cached geometry/action arrays",
    )
    require(
        len(model["header_connections"]) == 12,
        "header source must contain the original twelve of 104 axes",
    )
    require(
        len({axis["axis_id"] for axis in model["header_connections"]}) == 12,
        "duplicate header axis",
    )
    require(
        remaining["evaluated_body_count"] == 20
        and not remaining["affected_scope_stops"],
        "remaining-block transverse archive is incomplete",
    )
    require(
        header_map["schema"] == "header_supported_boundary_mapping/v1"
        and header_map["boundary_mapping_executed"] is True,
        "saved header-side map schema/status differs",
    )
    require(
        abs(header_map["annulus_hypothesis"]["inner_radius_mm"] - 4.1529) < GEOMETRY_TOL_MM
        and abs(header_map["annulus_hypothesis"]["outer_radius_mm"] - 9.2329) < GEOMETRY_TOL_MM,
        "saved minimum-area plain-washer envelope differs",
    )

    member_records = member_geometry["members"]
    bodies = {body["block"] for case in inputs["cases"] for body in case["interfaces"]}
    require(bodies == set(BODIES), "six header-related cleat census differs")
    body_records: dict[str, dict[str, Any]] = {}
    for body in ("base_header", *BODIES):
        record = model["bodies"][body]
        require(
            record["member_geometry"] == member_records[body],
            f"header input geometry differs from member cache: {body}",
        )
        surface = record["finished_surface_record"]
        step_path = ROOT / record["member_geometry"]["current_finished_step"]
        step_digest = record["member_geometry"]["current_finished_step_sha256"]
        require(
            surface["member_id"] == body
            and surface["step_binding"]["file_sha256"] == step_digest,
            f"finished surface/STEP binding differs: {body}",
        )
        pins[step_path] = step_digest
        body_records[body] = record
    authenticate(pins)

    return {
        "inputs": inputs,
        "model": model,
        "all_joint": all_joint,
        "remaining": remaining,
        "member_geometry": member_geometry,
        "body_records": body_records,
        "header_map": header_map,
        "washer_inner_radius_mm": float(
            header_map["annulus_hypothesis"]["inner_radius_mm"]
        ),
        "washer_outer_radius_mm": float(
            header_map["annulus_hypothesis"]["outer_radius_mm"]
        ),
    }


def patch_frame(patch: dict[str, Any]) -> dict[str, Any]:
    lines = [edge for edge in patch["boundary_edges"] if edge["curve_type"] == "LINE"]
    require(len(lines) == 4, "header contact patch outer boundary is not a rectangle")
    require(
        set(patch["boundary_edge_types"]) <= {"LINE", "CIRCLE"},
        "unsupported header contact patch edge",
    )
    normal = unit(patch["normal_on_first_xyz"], "contact patch normal")
    longest = max(lines, key=lambda edge: edge["length_mm"])
    origin = vec(longest["start_xyz_mm"])
    axis_u = unit(vec(longest["end_xyz_mm"]) - origin, "contact cell U axis")
    axis_v = unit(np.cross(normal, axis_u), "contact cell V axis")
    vertices = np.asarray(
        [vec(edge[key]) for edge in lines for key in ("start_xyz_mm", "end_xyz_mm")]
    )
    local = np.column_stack(
        ((vertices - origin) @ axis_u, (vertices - origin) @ axis_v)
    )
    low, high = local.min(axis=0), local.max(axis=0)
    require(
        np.max(np.abs((vertices - origin) @ normal)) < GEOMETRY_TOL_MM,
        "contact outer rectangle is not planar",
    )
    require(
        all(
            min(abs(point[0] - low[0]), abs(point[0] - high[0])) < GEOMETRY_TOL_MM
            and min(abs(point[1] - low[1]), abs(point[1] - high[1])) < GEOMETRY_TOL_MM
            for point in local
        ),
        "contact outer boundary lines do not form aligned rectangle",
    )
    circles = []
    for edge in patch["boundary_edges"]:
        if edge["curve_type"] != "CIRCLE":
            continue
        circle = edge["circle"]
        circle_axis = unit(circle["axis_xyz"], "contact patch bore axis")
        require(
            abs(abs(float(circle_axis @ normal)) - 1.0) < ALIGN_TOL,
            "contact patch circle is not normal to its plane",
        )
        require(
            abs(
                circle["last_parameter_rad"]
                - circle["first_parameter_rad"]
                - 2 * math.pi
            )
            < 1e-7,
            "contact patch contains clipped/partial circular boundary",
        )
        center = vec(circle["center_xyz_mm"])
        circles.append(
            {
                "center_xyz_mm": center.tolist(),
                "center_patch_uv_mm": [
                    (center - origin) @ axis_u,
                    (center - origin) @ axis_v,
                ],
                "radius_mm": float(circle["radius_mm"]),
            }
        )
    require(
        abs(
            float(np.prod(high - low))
            - sum(math.pi * circle["radius_mm"] ** 2 for circle in circles)
            - float(patch["area_mm2"])
        )
        < 1e-5,
        "saved contact patch rectangle-minus-bores area differs",
    )
    return {
        "origin_global_xyz_mm": origin,
        "u_global_xyz": axis_u,
        "v_global_xyz": axis_v,
        "normal_on_first_xyz": normal,
        "bounds_uv_mm": [low, high],
        "circles": circles,
    }


def contact_grid(
    cell: dict[str, Any],
    patch: dict[str, Any],
    geometry: dict[str, Any],
    header_helper: Any,
    grouped_cells: list[dict[str, Any]],
) -> dict[str, Any]:
    patch_index = int(cell["source_patch_index"])
    helper_geometry = header_helper.contact_geometry(cell, patch)
    frame = patch_frame(patch)
    low, high = frame["bounds_uv_mm"]
    width, height = high - low
    nx = max(MIN_CONTACT_DIVISIONS, math.ceil(width / CONTACT_CELL_SIZE_MM))
    ny = max(MIN_CONTACT_DIVISIONS, math.ceil(height / CONTACT_CELL_SIZE_MM))
    require(
        nx * ny == len(grouped_cells) == 4,
        "cached header contact sampler is not the frozen four-cell grid",
    )
    pieces = cell["name"].rsplit("_", 1)
    require(
        len(pieces) == 2 and pieces[0] == f"contact_{patch_index}",
        "contact cell identity differs from its source patch",
    )
    index = int(pieces[1])
    require(0 <= index < nx * ny, "contact cell grid index outside saved grid")
    grid_u, grid_v = divmod(index, ny)
    u_bounds = [low[0] + grid_u * width / nx, low[0] + (grid_u + 1) * width / nx]
    v_bounds = [low[1] + grid_v * height / ny, low[1] + (grid_v + 1) * height / ny]
    centroid = vec(cell["point_xyz_mm"])
    local_cell_uv = [
        (centroid - frame["origin_global_xyz_mm"]) @ frame["u_global_xyz"],
        (centroid - frame["origin_global_xyz_mm"]) @ frame["v_global_xyz"],
    ]
    require(
        u_bounds[0] - GEOMETRY_TOL_MM
        <= local_cell_uv[0]
        <= u_bounds[1] + GEOMETRY_TOL_MM
        and v_bounds[0] - GEOMETRY_TOL_MM
        <= local_cell_uv[1]
        <= v_bounds[1] + GEOMETRY_TOL_MM,
        "cached contact centroid is outside its source sampler cell",
    )
    total_area = math.fsum(float(item["area_mm2"]) for item in grouped_cells)
    first_moment = sum(
        (float(item["area_mm2"]) * vec(item["point_xyz_mm"]) for item in grouped_cells),
        np.zeros(3),
    )
    require(
        abs(total_area - float(patch["area_mm2"])) < 1e-5,
        "saved contact cell areas do not recover source patch area",
    )
    require(
        np.max(np.abs(first_moment / total_area - vec(patch["centroid_xyz_mm"])))
        < 1e-6,
        "saved contact cells do not recover source patch first moment",
    )
    body_axes = [
        unit(geometry[name], name) for name in ("axis", "section_u", "section_v")
    ]
    body_start = vec(geometry["start"])
    rect_corners_global = []
    for u in u_bounds:
        for v in v_bounds:
            rect_corners_global.append(
                frame["origin_global_xyz_mm"]
                + u * frame["u_global_xyz"]
                + v * frame["v_global_xyz"]
            )
    return {
        "representation": "constant normal pressure over saved clipped sampler cell",
        "cell_name": cell["name"],
        "source_patch_index": patch_index,
        "sampler": {
            "size_mm": CONTACT_CELL_SIZE_MM,
            "minimum_divisions": MIN_CONTACT_DIVISIONS,
            "grid_shape": [nx, ny],
            "cell_index_u_v": [grid_u, grid_v],
            "cell_rectangle_patch_uv_mm": [u_bounds, v_bounds],
        },
        "trimmed_domain": {
            "operation": "source_patch_rectangle_minus_full_circular_bores intersect sampler-cell rectangle",
            "source_patch_rectangle_uv_mm": [low.tolist(), high.tolist()],
            "excluded_circles_patch_uv": frame["circles"],
            "cell_rectangle_global_corners_xyz_mm": [
                corner.tolist() for corner in rect_corners_global
            ],
            "cell_rectangle_member_guv_corners_mm": [
                [float(np.dot(corner - body_start, axis)) for axis in body_axes]
                for corner in rect_corners_global
            ],
        },
        "source_cell_area_mm2": float(cell["area_mm2"]),
        "source_cell_centroid_global_xyz_mm": centroid.tolist(),
        "source_cell_centroid_member_guv_mm": local_guv(centroid, geometry),
        "source_patch_boundary_support_check": helper_geometry,
        "area_first_moment_recovered_from_saved_cells": True,
        "pressure_peak_or_cell_stiffness_established": False,
    }


def feature_circle(edge: dict[str, Any]) -> dict[str, Any]:
    circle = edge["circle"]
    center = circle.get("center_global_xyz_mm", circle.get("center_xyz_mm"))
    axis = circle.get("axis_unit_global_xyz", circle.get("axis_xyz"))
    require(center is not None and axis is not None, "surface circle lacks center/axis")
    return {
        "center_global_xyz_mm": vec(center),
        "axis_global_xyz": unit(axis, "surface circle axis"),
        "radius_mm": float(circle["radius_mm"]),
        "parameter_bounds_rad": edge.get("parameter_bounds", [0.0, 2 * math.pi]),
    }


def opposed_unit_normals(first: np.ndarray, second: np.ndarray) -> bool:
    """Require inward traction and the already-selected outward face to oppose."""
    return abs(float(first @ second) + 1.0) < ALIGN_TOL


def end_face_certificate(
    body: str,
    geometry: dict[str, Any],
    surface: dict[str, Any],
    contact_patch: dict[str, Any],
    axis_record: dict[str, Any],
    action: dict[str, Any],
    washer_inner: float,
    washer_outer: float,
) -> dict[str, Any]:
    grain = unit(geometry["axis"], f"{body} grain axis")
    start, end = vec(geometry["start"]), vec(geometry["end"])
    length = float(np.dot(end - start, grain))
    contact_centroid = vec(contact_patch["centroid_xyz_mm"])
    contact_station = float(np.dot(contact_centroid - start, grain))
    if abs(contact_station) <= GEOMETRY_TOL_MM:
        seat_station = length
        outward = grain
    elif abs(contact_station - length) <= GEOMETRY_TOL_MM:
        seat_station = 0.0
        outward = -grain
    else:
        return {
            "status": "UNSUPPORTED_CONTACT_PLANE_NOT_AT_GRAIN_END",
            "contact_station_mm": contact_station,
            "seat_center_global_xyz_mm": None,
        }

    axes = axis_record["receiver_clearance_geometry"]
    receiver = next((item for item in axes if item["receiver_id"] == body), None)
    if receiver is None:
        return {
            "status": "UNSUPPORTED_AXIS_HAS_NO_TARGET_RECEIVER",
            "seat_center_global_xyz_mm": None,
        }
    center = vec(receiver["modeled_shaft_center_global_xyz_mm"])
    bolt_axis = unit(
        receiver["source_bolt_axis_head_to_nut_unit_global_xyz"], "bolt axis"
    )
    target_point = vec(action["point_mm"])
    axis_miss = (
        target_point - center - np.dot(target_point - center, bolt_axis) * bolt_axis
    )
    candidate_faces = []
    for feature in surface["features"]:
        if feature["surface_kind"] != "PLANE":
            continue
        plane = feature["plane"]
        normal = unit(plane["normal_global_xyz"], "seat face normal")
        if float(normal @ outward) < 1.0 - ALIGN_TOL:
            continue
        endpoint = end if seat_station == length else start
        expected_offset = float(normal @ endpoint)
        if (
            abs(float(plane["signed_plane_station_global_mm"]) - expected_offset)
            < GEOMETRY_TOL_MM
        ):
            candidate_faces.append(feature)
    if len(candidate_faces) != 1:
        return {
            "status": "UNSUPPORTED_UNIQUE_OUTER_END_FACE_NOT_FOUND",
            "candidate_face_ids": [
                feature["feature_id"] for feature in candidate_faces
            ],
            "seat_center_global_xyz_mm": None,
        }
    face = candidate_faces[0]
    plane = face["plane"]
    normal = unit(plane["normal_global_xyz"], "seat face normal")
    plane_offset = float(plane["signed_plane_station_global_mm"])
    denominator = float(normal @ bolt_axis)
    if abs(denominator) < 1.0 - ALIGN_TOL:
        return {
            "status": "UNSUPPORTED_WASHER_AXIS_NOT_NORMAL_TO_OUTER_FACE",
            "face_id": face["feature_id"],
            "seat_center_global_xyz_mm": None,
        }
    seat_center = center + bolt_axis * (
        (plane_offset - float(normal @ center)) / denominator
    )
    surface_edges = [edge for wire in face["trim"]["wires"] for edge in wire["edges"]]
    line_edges = [edge for edge in surface_edges if edge["curve_kind"] == "LINE"]
    circles = [
        feature_circle(edge) for edge in surface_edges if edge["curve_kind"] == "CIRCLE"
    ]
    outer_wires = [
        wire
        for wire in face["trim"]["wires"]
        if len(wire["edges"]) == 4
        and all(edge["curve_kind"] == "LINE" for edge in wire["edges"])
    ]
    if len(outer_wires) != 1 or len(line_edges) != 4 or len(circles) != 2:
        return {
            "status": "UNSUPPORTED_OUTER_FACE_NOT_RECTANGLE_MINUS_TWO_BORES",
            "face_id": face["feature_id"],
            "seat_center_global_xyz_mm": seat_center.tolist(),
        }
    u_axis = unit(geometry["section_u"], "member section u")
    v_axis = unit(geometry["section_v"], "member section v")
    line_points = [
        vec(point)
        for edge in line_edges
        for point in edge["parameter_endpoint_global_xyz_mm"]
    ]
    uv = np.asarray(
        [
            [(point - seat_center) @ u_axis, (point - seat_center) @ v_axis]
            for point in line_points
        ]
    )
    low, high = uv.min(axis=0), uv.max(axis=0)
    center_offset = np.array(
        [(seat_center - center) @ u_axis, (seat_center - center) @ v_axis]
    )
    edge_margins = [
        center_offset[0] - low[0],
        high[0] - center_offset[0],
        center_offset[1] - low[1],
        high[1] - center_offset[1],
    ]
    target_matches = [
        circle
        for circle in circles
        if np.linalg.norm(circle["center_global_xyz_mm"] - seat_center)
        < GEOMETRY_TOL_MM
        and abs(circle["radius_mm"] - float(receiver["unique_bore_radius_mm"]))
        < GEOMETRY_TOL_MM
    ]
    target_match_ids = {id(circle) for circle in target_matches}
    other_holes = [circle for circle in circles if id(circle) not in target_match_ids]
    if len(target_matches) != 1 or len(other_holes) != 1:
        return {
            "status": "UNSUPPORTED_TARGET_BORE_FACE_BINDING",
            "face_id": face["feature_id"],
            "seat_center_global_xyz_mm": seat_center.tolist(),
            "circle_count": len(circles),
            "target_circle_match_count": len(target_matches),
        }
    target_bore = target_matches[0]
    other = other_holes[0]
    other_clearance = float(
        np.linalg.norm(other["center_global_xyz_mm"] - seat_center)
        - washer_outer
        - other["radius_mm"]
    )
    edge_clearance = float(min(edge_margins) - washer_outer)
    bore_clearance = float(washer_inner - target_bore["radius_mm"])
    circle_axes_aligned = all(
        abs(abs(float(circle["axis_global_xyz"] @ normal)) - 1.0) < ALIGN_TOL
        for circle in circles
    )
    force = vec(action["force_n"])
    inward = -outward
    scalar = float(force @ inward)
    pressure_force = scalar * inward if scalar > 0.0 else np.zeros(3)
    unsupported_force = force - pressure_force
    support_pass = (
        min(edge_clearance, other_clearance, bore_clearance) >= -GEOMETRY_TOL_MM
        and circle_axes_aligned
        and max_abs(axis_miss) < GEOMETRY_TOL_MM
        and opposed_unit_normals(normal, inward)
    )
    return {
        "status": "FULL_ANNULAR_LAND_SUPPORTED"
        if support_pass
        else "UNSUPPORTED_WASHER_LAND",
        "member_id": body,
        "face_id": face["feature_id"],
        "face_index_one_based": face["face_index_one_based"],
        "seat_point_global_xyz_mm": seat_center.tolist(),
        "seat_point_member_guv_mm": local_guv(seat_center, geometry),
        "inward_normal_xyz": inward.tolist(),
        "outward_normal_xyz": outward.tolist(),
        "target_bore_radius_mm": target_bore["radius_mm"],
        "washer_inner_radius_mm": washer_inner,
        "washer_outer_radius_mm": washer_outer,
        "support_margins_mm": {
            "washer_to_outer_edge": edge_clearance,
            "washer_to_other_hole": other_clearance,
            "washer_opening_to_bore": bore_clearance,
        },
        "force_into_supported_seat_n": pressure_force.tolist(),
        "unsupported_source_force_xyz_n": unsupported_force.tolist(),
        "source_line_to_seat_axis_miss_mm": float(np.linalg.norm(axis_miss)),
        "contact_face_grain_station_mm": contact_station,
        "seat_grain_station_mm": seat_station,
        "source_role": action["role"],
        "geometry_scope": "Saved finished planar feature and circle/line wires only; no CAD import or delivered washer inspection.",
        "uniform_annular_pressure_is_assumption": True,
    }


def bore_features(
    body_record: dict[str, Any], geometry: dict[str, Any]
) -> list[dict[str, Any]]:
    axes = [unit(geometry[name], name) for name in ("axis", "section_u", "section_v")]
    output = []
    for feature in body_record["finished_surface_record"]["features"]:
        if feature["surface_kind"] != "CYLINDER":
            continue
        cylinder = feature["cylinder"]
        direction = unit(cylinder["axis_unit_global_xyz"], "finished bore axis")
        local_direction = np.asarray([float(direction @ axis) for axis in axes])
        axis_index = int(np.argmax(np.abs(local_direction)))
        require(
            abs(abs(float(local_direction[axis_index])) - 1.0) < ALIGN_TOL,
            f"non-axis-aligned saved cylinder on {geometry['name']}",
        )
        low, high = map(float, cylinder["axis_parameter_interval_mm"])
        origin = vec(cylinder["axis_origin_global_xyz_mm"])
        endpoints = [origin + low * direction, origin + high * direction]
        area_expected = 2 * math.pi * float(cylinder["radius_mm"]) * abs(high - low)
        area_error = abs(float(feature["area_mm2"]) - area_expected)
        output.append(
            {
                "feature_id": feature["feature_id"],
                "face_index_one_based": feature["face_index_one_based"],
                "axis_xyz": direction,
                "axis_local_index": axis_index,
                "axis_local_sign": 1.0 if local_direction[axis_index] > 0 else -1.0,
                "axis_origin_xyz_mm": origin,
                "axis_parameter_interval_mm": [low, high],
                "axis_endpoints_xyz_mm": endpoints,
                "axis_endpoints_member_guv_mm": [
                    local_guv(point, geometry) for point in endpoints
                ],
                "radius_mm": float(cylinder["radius_mm"]),
                "area_mm2": float(feature["area_mm2"]),
                "complete_cylindrical_area_error_mm2": area_error,
                "centerline_global_xyz_mm": (endpoints[0] + endpoints[1]) / 2,
            }
        )
    return output


def bore_support_certificate(
    target: dict[str, Any], all_bores: list[dict[str, Any]], geometry: dict[str, Any]
) -> dict[str, Any]:
    length = float(
        np.dot(
            vec(geometry["end"]) - vec(geometry["start"]),
            unit(geometry["axis"], "member grain axis"),
        )
    )
    dimensions = [length, float(geometry["width_mm"]), float(geometry["depth_mm"])]
    bounds = [
        [0.0, dimensions[0]],
        [-dimensions[1] / 2, dimensions[1] / 2],
        [-dimensions[2] / 2, dimensions[2] / 2],
    ]
    target_axis = target["axis_local_index"]
    center = np.asarray(local_guv(target["centerline_global_xyz_mm"], geometry))
    stock_margins = []
    for coordinate in range(3):
        if coordinate == target_axis:
            continue
        low, high = bounds[coordinate]
        stock_margins.extend(
            [
                center[coordinate] - target["radius_mm"] - low,
                high - center[coordinate] - target["radius_mm"],
            ]
        )
    other_margins = {}
    p1 = target["centerline_global_xyz_mm"]
    n1 = target["axis_xyz"]
    for bore in all_bores:
        if bore["feature_id"] == target["feature_id"]:
            continue
        p2, n2 = bore["centerline_global_xyz_mm"], bore["axis_xyz"]
        cross = np.cross(n1, n2)
        cross_norm = float(np.linalg.norm(cross))
        if cross_norm < ALIGN_TOL:
            distance = float(np.linalg.norm(np.cross(p2 - p1, n1)))
        else:
            distance = abs(float(np.dot(p2 - p1, cross))) / cross_norm
        margin = distance - target["radius_mm"] - bore["radius_mm"]
        other_margins[bore["feature_id"]] = margin
    min_stock = float(min(stock_margins)) if stock_margins else math.inf
    min_other = float(min(other_margins.values())) if other_margins else math.inf
    area_error = target["complete_cylindrical_area_error_mm2"]
    passed = (
        min_stock >= -GEOMETRY_TOL_MM
        and min_other > GEOMETRY_TOL_MM
        and area_error < 1e-4
    )
    return {
        "whole_circumference_support_certified": passed,
        "target_cylinder_feature_id": target["feature_id"],
        "stock_coordinate_margins_mm": stock_margins,
        "minimum_stock_margin_mm": min_stock,
        "other_cylinder_clearance_lower_bounds_mm": other_margins,
        "minimum_other_cylinder_clearance_mm": min_other,
        "complete_cylindrical_area_error_mm2": area_error,
        "support_method": "Axis-aligned saved cylindrical faces, gross stock bounds and conservative infinite-axis clearance lower bounds.",
        "scope": "Geometry support for pressure domain only; no contact state, bolt compatibility, bearing resistance or timber strength.",
    }


def map_axial_seat(
    body: str,
    action: dict[str, Any],
    connection: dict[str, Any],
    geometry: dict[str, Any],
    surface: dict[str, Any],
    contact_patch: dict[str, Any],
    washer_inner: float,
    washer_outer: float,
    datum: np.ndarray,
) -> dict[str, Any]:
    seat = end_face_certificate(
        body,
        geometry,
        surface,
        contact_patch,
        connection,
        action,
        washer_inner,
        washer_outer,
    )
    if seat["status"] != "FULL_ANNULAR_LAND_SUPPORTED":
        source_wrench = wrench([action], datum)
        return {
            "source_action": action,
            "field_kind": "axial_washer_annulus",
            "field_status": seat["status"],
            "seat_certificate": seat,
            "boundary_fields": [],
            "mapped_wrench_xyz_n_nmm": [0.0] * 6,
            "source_wrench_xyz_n_nmm": source_wrench.tolist(),
            "source_to_field_wrench_residual_xyz_n_nmm": source_wrench.tolist(),
            "unmapped_source_free_moment_nmm": action["free_moment_nmm"],
            "unmapped_source_force_xyz_n": action["force_n"],
        }
    force = vec(action["force_n"])
    mapped_force = vec(seat["force_into_supported_seat_n"])
    center = vec(seat["seat_point_global_xyz_mm"])
    area = math.pi * (washer_outer**2 - washer_inner**2)
    pressure = float(np.linalg.norm(mapped_force)) / area
    geometry_axes = [unit(geometry[name], name) for name in ("section_u", "section_v")]
    quadrature_radius = math.sqrt((washer_outer**2 + washer_inner**2) / 2.0)
    quadrature = []
    for index in range(8):
        angle = 2 * math.pi * (index + 0.5) / 8
        point = center + quadrature_radius * (
            math.cos(angle) * geometry_axes[0] + math.sin(angle) * geometry_axes[1]
        )
        quadrature.append(
            {
                "quadrature_index": index,
                "point_xyz_mm": point.tolist(),
                "point_member_guv_mm": local_guv(point, geometry),
                "force_xyz_n": (mapped_force / 8).tolist(),
            }
        )
    quadrature_actions = [
        {"point_xyz_mm": item["point_xyz_mm"], "force_xyz_n": item["force_xyz_n"]}
        for item in quadrature
    ]
    q_wrench = field_wrench(quadrature_actions, datum)
    expected_mapped = point_wrench(center, mapped_force, datum)
    require(
        max_abs(q_wrench - expected_mapped) < 1e-8,
        "washer annulus quadrature does not preserve force/first moments",
    )
    field = {
        "field_kind": "uniform_compressive_pressure_on_supported_annulus",
        "domain": {
            "plane_point_xyz_mm": center.tolist(),
            "plane_point_member_guv_mm": seat["seat_point_member_guv_mm"],
            "normal_into_body_xyz": seat["inward_normal_xyz"],
            "inner_radius_mm": washer_inner,
            "outer_radius_mm": washer_outer,
            "area_mm2": area,
            "pressure_mpa": pressure,
            "basis_u_xyz": geometry_axes[0].tolist(),
            "basis_v_xyz": geometry_axes[1].tolist(),
        },
        "integrated_force_xyz_n": mapped_force.tolist(),
        "wrench_quadrature": quadrature,
        "cut_axes_supported_in_record": ["u", "v"],
        "assumption": "Concentric uniform annular bearing pressure; pressure field is a static placement hypothesis, not a measured washer/contact state.",
    }
    source_wrench = wrench([action], datum)
    mapped_wrench = field_wrench(quadrature_actions, datum)
    return {
        "source_action": action,
        "field_kind": "axial_washer_annulus",
        "field_status": "MAPPED_WITH_EXPLICIT_SOURCE_RESIDUALS",
        "seat_certificate": seat,
        "boundary_fields": [field],
        "mapped_wrench_xyz_n_nmm": mapped_wrench.tolist(),
        "source_wrench_xyz_n_nmm": source_wrench.tolist(),
        "source_to_field_wrench_residual_xyz_n_nmm": (
            source_wrench - mapped_wrench
        ).tolist(),
        "unmapped_source_free_moment_nmm": action["free_moment_nmm"],
        "unmapped_source_force_xyz_n": (force - mapped_force).tolist(),
    }


def map_contact_cell(
    body: str,
    action: dict[str, Any],
    cell: dict[str, Any],
    patch: dict[str, Any],
    geometry: dict[str, Any],
    header_helper: Any,
    grouped_cells: list[dict[str, Any]],
    datum: np.ndarray,
) -> dict[str, Any]:
    require(
        cell["name"] == action["source_id"], "contact source/action identity differs"
    )
    require(
        body in (cell["first"], cell["second"])
        and "base_header" in (cell["first"], cell["second"]),
        "contact cell does not belong to the target/header pair",
    )
    require(
        set(patch["member_ids"]) == {cell["first"], cell["second"]},
        "contact patch receivers differ from saved cell",
    )
    normal_on_first = unit(patch["normal_on_first_xyz"], "contact normal on first")
    inward = normal_on_first if body == cell["second"] else -normal_on_first
    force = vec(action["force_n"])
    compression = float(force @ inward)
    mapped_force = max(compression, 0.0) * inward
    unsupported_force = force - mapped_force
    misalignment = float(np.linalg.norm(force - compression * inward))
    group = grouped_cells
    domain = contact_grid(cell, patch, geometry, header_helper, group)
    domain["normal_into_body_xyz"] = inward.tolist()
    area = float(cell["area_mm2"])
    pressure = max(compression, 0.0) / area
    boundary = {
        "field_kind": "uniform_frictionless_normal_pressure_on_saved_trimmed_cell",
        "domain": domain,
        "pressure_mpa": pressure,
        "integrated_force_xyz_n": mapped_force.tolist(),
        "cut_axes_supported_in_record": ["u", "v"],
        "assumption": "Uniform compression over exact saved clipped sampler cell; no tangential friction, pressure peak or compatible contact solution.",
    }
    mapped_wrench = (
        point_wrench(vec(action["point_mm"]), mapped_force, datum)
        if compression >= 0.0
        else np.zeros(6)
    )
    source_wrench = wrench([action], datum)
    status = (
        "MAPPED_WITH_EXPLICIT_SOURCE_RESIDUALS"
        if compression >= 0.0
        else "UNSUPPORTED_TENSILE_CONTACT_ACTION"
    )
    return {
        "source_action": action,
        "field_kind": "trimmed_contact_cell",
        "field_status": status,
        "boundary_fields": [boundary] if compression >= 0.0 else [],
        "mapped_wrench_xyz_n_nmm": mapped_wrench.tolist(),
        "source_wrench_xyz_n_nmm": source_wrench.tolist(),
        "source_to_field_wrench_residual_xyz_n_nmm": (
            source_wrench - mapped_wrench
        ).tolist(),
        "unmapped_source_free_moment_nmm": action["free_moment_nmm"],
        "unmapped_source_force_xyz_n": unsupported_force.tolist(),
        "source_force_normal_misalignment_n": misalignment,
        "compression_force_n": max(compression, 0.0),
    }


def matches_receiver_cylinder(feature: dict[str, Any], saved: dict[str, Any]) -> bool:
    """Bind saved cylinders by geometry; STEP face enumeration can differ."""
    cylinder = feature["cylinder"]
    if abs(float(cylinder["radius_mm"]) - float(saved["radius_mm"])) >= GEOMETRY_TOL_MM:
        return False
    first = tuple(map(float, cylinder["axis_unit_global_xyz"]))
    second = tuple(map(float, saved["cylinder_axis_unit_global_xyz"]))
    require(len(first) == len(second) == 3, "invalid saved cylinder direction")
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))
    require(first_norm > 0 and second_norm > 0, "zero saved cylinder direction")
    first = tuple(value / first_norm for value in first)
    second = tuple(value / second_norm for value in second)

    def cross_norm(a, b):
        return math.sqrt(sum((a[j] * b[k] - a[k] * b[j]) ** 2
                             for j, k in ((1, 2), (2, 0), (0, 1))))

    if cross_norm(first, second) >= ALIGN_TOL:
        return False
    origin = tuple(map(float, cylinder["axis_origin_global_xyz_mm"]))
    saved_origin = tuple(map(float, saved["cylinder_axis_location_global_xyz_mm"]))
    require(len(origin) == len(saved_origin) == 3, "invalid saved cylinder origin")
    offset = tuple(a - b for a, b in zip(origin, saved_origin, strict=True))
    if cross_norm(offset, second) >= GEOMETRY_TOL_MM:
        return False
    endpoints = [tuple(origin[j] + float(t) * first[j] for j in range(3))
                 for t in cylinder["axis_parameter_interval_mm"]]
    saved_endpoints = [tuple(saved_origin[j] + float(t) * second[j] for j in range(3))
                       for t in saved["v_parameter_bounds_mm"]]
    require(len(endpoints) == len(saved_endpoints) == 2,
            "saved cylinder requires two finite endpoints")
    same = max(math.dist(a, b) for a, b in zip(endpoints, saved_endpoints, strict=True))
    reversed_order = max(math.dist(a, b) for a, b in
                         zip(endpoints, reversed(saved_endpoints), strict=True))
    return min(same, reversed_order) < GEOMETRY_TOL_MM


def map_lateral_bore(
    body: str,
    action: dict[str, Any],
    connection: dict[str, Any],
    geometry: dict[str, Any],
    body_record: dict[str, Any],
    datum: np.ndarray,
    bore_helper: Any,
) -> dict[str, Any]:
    axis_id = action["source_id"].split("/")[0]
    receiver = next(
        (
            item
            for item in connection["receiver_clearance_geometry"]
            if item["receiver_id"] == body
        ),
        None,
    )
    require(receiver is not None, f"missing receiver bore geometry: {axis_id}/{body}")
    saved_faces = receiver["coaxial_cylindrical_finished_faces"]
    require(len(saved_faces) == 1
            and receiver["receiver_step_sha256"]
            == body_record["member_geometry"]["current_finished_step_sha256"],
            f"receiver cylinder/finished STEP binding differs: {axis_id}/{body}")
    matching_features = [feature for feature in
                         body_record["finished_surface_record"]["features"]
                         if feature["surface_kind"] == "CYLINDER"
                         and matches_receiver_cylinder(feature, saved_faces[0])]
    require(len(matching_features) == 1,
            f"finished bore geometry does not bind uniquely: {axis_id}/{body}")
    all_bores = bore_features(body_record, geometry)
    target_features = [
        feature
        for feature in all_bores
        if feature["feature_id"] == matching_features[0]["feature_id"]
    ]
    require(
        len(target_features) == 1,
        f"finished bore feature does not bind uniquely: {axis_id}/{body}",
    )
    target = target_features[0]
    require(
        abs(target["radius_mm"] - float(receiver["unique_bore_radius_mm"]))
        < GEOMETRY_TOL_MM,
        f"finished cylinder radius differs: {axis_id}/{body}",
    )
    require(
        target["complete_cylindrical_area_error_mm2"] < 1e-4,
        f"saved target cylinder is not complete: {axis_id}/{body}",
    )
    support = bore_support_certificate(target, all_bores, geometry)
    force = vec(action["force_n"])
    shaft = target["axis_xyz"]
    axial_component = float(force @ shaft) * shaft
    radial_force = force - axial_component
    source_point = vec(action["point_mm"])
    origin = target["axis_origin_xyz_mm"]
    axial_coordinate = float(np.dot(source_point - origin, shaft))
    projected_point = origin + axial_coordinate * shaft
    line_miss = float(np.linalg.norm(source_point - projected_point))
    endpoints = target["axis_endpoints_xyz_mm"]
    distances = [
        float(np.linalg.norm(projected_point - vec(endpoint))) for endpoint in endpoints
    ]
    endpoint_index = int(np.argmin(distances))
    if min(distances) > GEOMETRY_TOL_MM:
        return {
            "source_action": action,
            "field_kind": "frictionless_lateral_bore_pressure",
            "field_status": "UNSUPPORTED_SOURCE_PLANE_NOT_BORE_END",
            "boundary_fields": [],
            "support_certificate": support,
            "source_to_field_wrench_residual_xyz_n_nmm": wrench(
                [action], datum
            ).tolist(),
            "unmapped_source_free_moment_nmm": action["free_moment_nmm"],
            "unmapped_source_force_xyz_n": force.tolist(),
            "source_axis_miss_mm": line_miss,
            "source_plane_to_cylinder_end_mm": min(distances),
        }
    if not support["whole_circumference_support_certified"]:
        return {
            "source_action": action,
            "field_kind": "frictionless_lateral_bore_pressure",
            "field_status": "UNSUPPORTED_WALL_GEOMETRY",
            "boundary_fields": [],
            "support_certificate": support,
            "source_to_field_wrench_residual_xyz_n_nmm": wrench(
                [action], datum
            ).tolist(),
            "unmapped_source_free_moment_nmm": action["free_moment_nmm"],
            "unmapped_source_force_xyz_n": force.tolist(),
            "source_axis_miss_mm": line_miss,
        }
    other_endpoint = vec(endpoints[1 - endpoint_index])
    inward = unit(other_endpoint - projected_point, "bore inward shaft direction")
    span = float(np.linalg.norm(other_endpoint - projected_point))
    axial_weight = span / 8.0
    centers = [
        projected_point + inward * (span / 4.0),
        projected_point + inward * (span / 2.0),
    ]
    body_start = vec(geometry["start"])
    profile_fields = []
    mapped_actions = []
    if np.linalg.norm(radial_force) > 0.0:
        for index, (center, coefficient) in enumerate(
            zip(centers, (2.0, -1.0), strict=True)
        ):
            profile_force = coefficient * radial_force
            profile = bore_helper.pressure_profile(
                center.tolist(),
                profile_force.tolist(),
                shaft.tolist(),
                target["radius_mm"],
                axial_weight,
                identity=axis_id,
                support=support,
            )
            local_station = float(
                np.dot(center - body_start, unit(geometry["axis"], "grain axis"))
            )
            profile_fields.append(
                {
                    "field_kind": "nonnegative_half_cosine_radial_bore_pressure",
                    "source_action_id": action["source_id"],
                    "strip_index": index,
                    "resultant_coefficient": coefficient,
                    "profile": profile,
                    "axial_station_member_g_mm": local_station,
                    "axial_quadrature_weight_mm": axial_weight,
                    "cut_axes_supported_in_record": ["u", "v"],
                    "assumption": "Two opposite-wall compression station measures: +2F at L/4 and -F at L/2, each with axial Gauss weight L/8. Net force and first moments reproduce the source point action; the weights are not physical finite strip widths, and no elastic/contact compatibility is solved.",
                }
            )
            mapped_actions.append(
                {"point_xyz_mm": center.tolist(), "force_xyz_n": profile_force.tolist()}
            )
    mapped_wrench = field_wrench(mapped_actions, datum)
    source_wrench = wrench([action], datum)
    return {
        "source_action": action,
        "field_kind": "frictionless_lateral_bore_pressure",
        "field_status": "MAPPED_WITH_EXPLICIT_SOURCE_RESIDUALS"
        if profile_fields
        else "ZERO_SOURCE_FORCE_NO_PRESSURE_FIELD",
        "boundary_fields": profile_fields,
        "support_certificate": support,
        "source_point_projected_to_axis_xyz_mm": projected_point.tolist(),
        "source_axis_miss_mm": line_miss,
        "source_plane_to_cylinder_end_mm": min(distances),
        "shaft_axis_xyz": shaft.tolist(),
        "shaft_span_available_mm": span,
        "radial_force_xyz_n": radial_force.tolist(),
        "unmapped_axial_force_xyz_n": axial_component.tolist(),
        "mapped_wrench_xyz_n_nmm": mapped_wrench.tolist(),
        "source_wrench_xyz_n_nmm": source_wrench.tolist(),
        "source_to_field_wrench_residual_xyz_n_nmm": (
            source_wrench - mapped_wrench
        ).tolist(),
        "unmapped_source_free_moment_nmm": action["free_moment_nmm"],
        "unmapped_source_force_xyz_n": axial_component.tolist(),
    }


def known_answer_coupon(bore_helper: Any) -> dict[str, Any]:
    """Check annulus first moments and opposite-wall bore-strip wrench algebra."""
    bore_coupon = bore_helper.algebraic_coupon()
    face_normal = np.array([0.0, 0.0, 1.0])
    inward_normal = -face_normal
    require(opposed_unit_normals(face_normal, inward_normal)
            and not opposed_unit_normals(face_normal, face_normal),
            "outward/inward washer-normal known answer differs")
    datum = np.array([0.0, 0.0, 0.0])
    source = np.array([3.0, 4.0, 5.0])
    force = np.array([10.0, 0.0, 0.0])
    axis = np.array([0.0, 0.0, 1.0])
    strip_width = 1.0
    profiles = [
        bore_helper.pressure_profile(
            (source + axis * 2.0).tolist(),
            (2.0 * force).tolist(),
            axis.tolist(),
            2.0,
            strip_width,
            identity="coupon",
        ),
        bore_helper.pressure_profile(
            (source + axis * 4.0).tolist(),
            (-force).tolist(),
            axis.tolist(),
            2.0,
            strip_width,
            identity="coupon",
        ),
    ]
    strip_wrench = sum(
        (
            np.r_[
                vec(profile["force_xyz_n"]),
                np.cross(
                    vec(profile["axis_point_xyz_mm"]) - datum,
                    vec(profile["force_xyz_n"]),
                ),
            ]
            for profile in profiles
        ),
        np.zeros(6),
    )
    expected = point_wrench(source, force, datum)
    require(
        max_abs(strip_wrench - expected) < 1e-10,
        "opposite-wall strip known-answer wrench differs",
    )
    inner, outer, tension = 2.0, 5.0, 40.0
    area = math.pi * (outer**2 - inner**2)
    ring_radius = math.sqrt((outer**2 + inner**2) / 2.0)
    ring_forces = []
    for index in range(8):
        angle = 2 * math.pi * (index + 0.5) / 8
        point = source + ring_radius * np.array([math.cos(angle), math.sin(angle), 0.0])
        ring_forces.append(
            {"point_xyz_mm": point.tolist(), "force_xyz_n": [0.0, 0.0, tension / 8]}
        )
    ring_wrench = field_wrench(ring_forces, datum)
    ring_expected = point_wrench(source, [0.0, 0.0, tension], datum)
    require(
        max_abs(ring_wrench - ring_expected) < 1e-10,
        "washer annulus quadrature known-answer wrench differs",
    )
    return {
        "status": "PASS_KNOWN_ANSWER_BOUNDARY_ALGEBRA",
        "corner_bore_wall_coupon": bore_coupon,
        "two_strip_source_wrench_expected_n_nmm": expected.tolist(),
        "two_strip_source_wrench_returned_n_nmm": strip_wrench.tolist(),
        "annulus_area_coupon_mm2": area,
        "annulus_pressure_coupon_mpa": tension / area,
        "annulus_wrench_expected_n_nmm": ring_expected.tolist(),
        "annulus_wrench_returned_n_nmm": ring_wrench.tolist(),
        "scope": "Algebra only. No solver, CAD, strength value or actual pressure field is evaluated.",
        "washer_normal_coupon": {
            "outward_face_normal_xyz": face_normal.tolist(),
            "inward_pressure_normal_xyz": inward_normal.tolist(),
            "outward_dot_inward": float(face_normal @ inward_normal),
            "opposed_normals_accepted_same_normals_refused": True,
        },
    }


def cut_catalog(
    path: Path, all_joint: dict[str, Any]
) -> dict[tuple[str, str, int], list[dict[str, Any]]]:
    states = {
        (state["body"], state["case_id"], int(state["axis"])): state
        for state in all_joint["states"]
        if state["body"] in BODIES
    }
    require(
        len(states) == len(BODIES) * len(CASES) * 2,
        "all-joint cut-state census differs for six target bodies",
    )
    stations: dict[tuple[str, str, int], dict[float, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    with gzip.open(path, "rt") as stream:
        for line in stream:
            record = json.loads(line)
            body = record["block"]
            axis = int(record["axis"])
            if body not in BODIES or record["case_id"] not in CASES or axis not in (1, 2):
                continue
            identity = (body, record["case_id"], axis)
            require(
                identity in states and record["limit"] in ("before", "after"),
                "cleat cut line is outside six-body transverse source state",
            )
            stations[identity][float(record["station_mm"])].add(record["limit"])
    result = {}
    for identity, state in states.items():
        entries = stations.get(identity, {})
        require(
            entries
            and all(limits == {"before", "after"} for limits in entries.values()),
            f"missing before/after source cuts: {identity}",
        )
        require(
            len(entries) * 2 == int(state["cut_count"]),
            f"cut station count differs from frozen state: {identity}",
        )
        result[identity] = [
            {"station_mm": station, "limits": sorted(limits)}
            for station, limits in sorted(entries.items())
        ]
    return result


def build(output: Path) -> dict[str, Any]:
    output = output.resolve()
    owned = (HERE / "rawlocal/header-boundary").resolve()
    require(
        output != owned and output.is_relative_to(owned),
        f"output must be a fresh child of {owned}",
    )
    require(not output.exists(), f"output already exists: {output}")
    pins = {path.resolve(): digest for path, digest in PINS.items()}
    require(
        "__HEADER_MAP_DOC_SHA__" not in pins.values(),
        "header map documentation pin is unset",
    )
    authenticate(pins)
    header_helper = module(HEADER_MAP, "header_traction_map_reused")
    bore_helper = module(BORE_MAP, "corner_bore_wall_reused")
    context = source_context(pins)
    inputs, model = context["inputs"], context["model"]
    cut_states = cut_catalog(
        REMAINING_DIR / "cuts.jsonl.gz", context["all_joint"]
    )
    connection_map = {axis["axis_id"]: axis for axis in model["header_connections"]}
    closure_duties = {
        duty["joint_id"]: duty for duty in context["all_joint"]["joint_duties"]
    }
    remaining_states = {
        (state["block"], state["case_id"], int(state["axis"])): state
        for state in context["remaining"]["states"]
        if state["block"] in BODIES and int(state["axis"]) in (1, 2)
    }
    require(
        len(remaining_states) == len(BODIES) * len(CASES) * 2,
        "remaining transverse state census differs for six target bodies",
    )
    coupon = known_answer_coupon(bore_helper)

    body_results = []
    aggregate = {
        "cases": 0,
        "interfaces": 0,
        "source_actions": 0,
        "boundary_fields": 0,
        "retained_nonheader_points": 0,
        "u_v_cut_states": 0,
        "u_v_cut_limits": 0,
        "unsupported_source_free_couple_rows": 0,
        "nonzero_source_free_couple_rows": 0,
        "unsupported_boundary_action_rows": 0,
    }
    for case in inputs["cases"]:
        case_id = case["case_id"]
        for interface in case["interfaces"]:
            body = interface["block"]
            if body not in BODIES:
                continue
            aggregate["cases"] += 1
            aggregate["interfaces"] += 1
            body_record = context["body_records"][body]
            geometry_record = body_record["member_geometry"]["geometry"]
            surface = body_record["finished_surface_record"]
            datum = vec(geometry_record["start"])
            header_actions = interface["actions_on_block"]
            full_actions = interface["complete_block_actions"]
            selected_rows = {int(action["row"]) for action in header_actions}
            full_by_row = {
                int(action["row"]): action
                for action in full_actions
                if int(action["row"]) >= 0
            }
            require(
                len(selected_rows) == 10 and selected_rows.issubset(full_by_row),
                f"header action rows not present in complete body source: {body}/{case_id}",
            )
            for action in header_actions:
                complete = full_by_row[int(action["row"])]
                require(
                    action["source_id"] == complete["source_id"]
                    and action["point_mm"] == complete["point_mm"]
                    and action["force_n"] == complete["force_n"]
                    and action["free_moment_nmm"] == complete["free_moment_nmm"],
                    f"interface/whole-body source action differs: {body}/{case_id}/{action['row']}",
                )
            axes = list(interface["axis_ids"])
            require(
                len(axes) == 2 and all(axis in connection_map for axis in axes),
                f"header axis pairing differs: {body}/{case_id}",
            )
            contact_cells = [
                model["contact_cells"][action["source_id"]]
                for action in header_actions
                if action["role"] == "timber_or_panel_contact"
            ]
            require(
                len(contact_cells) == 4,
                f"header contact-cell census differs: {body}/{case_id}",
            )
            contacts_by_patch: dict[int, list[dict[str, Any]]] = defaultdict(list)
            for cell in model["contact_cells"].values():
                if body in (cell["first"], cell["second"]) and "base_header" in (
                    cell["first"],
                    cell["second"],
                ):
                    contacts_by_patch[int(cell["source_patch_index"])].append(cell)
            unmapped_actions = []
            action_results = []
            for action in header_actions:
                role = action["role"]
                if role == "physical_bolt_outer_seat_tension":
                    axis_id = action["source_id"].split("/")[0]
                    connection = connection_map[axis_id]
                    patch_indices = {
                        int(cell["source_patch_index"]) for cell in contact_cells
                    }
                    require(
                        len(patch_indices) == 1,
                        f"header contact actions span multiple source patches: {body}/{case_id}",
                    )
                    patch_index = next(iter(patch_indices))
                    patch = model["contact_patches_by_global_source_index"][
                        str(patch_index)
                    ]
                    result = map_axial_seat(
                        body,
                        action,
                        connection,
                        geometry_record,
                        surface,
                        patch,
                        context["washer_inner_radius_mm"],
                        context["washer_outer_radius_mm"],
                        interface_datum(interface),
                    )
                elif role == "timber_or_panel_contact":
                    cell = model["contact_cells"][action["source_id"]]
                    patch = model["contact_patches_by_global_source_index"][
                        str(cell["source_patch_index"])
                    ]
                    result = map_contact_cell(
                        body,
                        action,
                        cell,
                        patch,
                        geometry_record,
                        header_helper,
                        contacts_by_patch[int(cell["source_patch_index"])],
                        interface_datum(interface),
                    )
                elif role == "candidate_bolt_lateral_plane":
                    axis_id = action["source_id"].split("/")[0]
                    result = map_lateral_bore(
                        body,
                        action,
                        connection_map[axis_id],
                        geometry_record,
                        body_record,
                        interface_datum(interface),
                        bore_helper,
                    )
                else:
                    result = {
                        "source_action": action,
                        "field_kind": "unsupported_header_interface_role",
                        "field_status": "UNSUPPORTED_ACTION_ROLE",
                        "boundary_fields": [],
                        "mapped_wrench_xyz_n_nmm": [0.0] * 6,
                        "source_wrench_xyz_n_nmm": wrench(
                            [action], interface_datum(interface)
                        ).tolist(),
                        "source_to_field_wrench_residual_xyz_n_nmm": wrench(
                            [action], interface_datum(interface)
                        ).tolist(),
                        "unmapped_source_free_moment_nmm": action["free_moment_nmm"],
                        "unmapped_source_force_xyz_n": action["force_n"],
                    }
                action_results.append(result)
                fields = result.get("boundary_fields", [])
                if result["field_status"] not in (
                    "MAPPED_WITH_EXPLICIT_SOURCE_RESIDUALS",
                    "ZERO_SOURCE_FORCE_NO_PRESSURE_FIELD",
                ):
                    unmapped_actions.append(
                        {
                            "row": action["row"],
                            "source_id": action["source_id"],
                            "role": role,
                            "field_status": result["field_status"],
                            "source_force_xyz_n": action["force_n"],
                            "source_free_moment_nmm": action["free_moment_nmm"],
                            "source_to_field_wrench_residual_xyz_n_nmm": result.get(
                                "source_to_field_wrench_residual_xyz_n_nmm"
                            ),
                        }
                    )
                aggregate["source_actions"] += 1
                aggregate["boundary_fields"] += len(fields)
                aggregate["unsupported_source_free_couple_rows"] += int(
                    max_abs(vec(action["free_moment_nmm"])) >= MOMENT_ACCOUNTING_TOL_NMM
                )
                aggregate["nonzero_source_free_couple_rows"] += int(
                    any(float(value) != 0.0 for value in action["free_moment_nmm"])
                )
                aggregate["unsupported_boundary_action_rows"] += int(
                    result["field_status"]
                    not in (
                        "MAPPED_WITH_EXPLICIT_SOURCE_RESIDUALS",
                        "ZERO_SOURCE_FORCE_NO_PRESSURE_FIELD",
                    )
                )

            source_interface_wrench = wrench(
                header_actions, vec(interface["datum_xyz_mm"])
            )
            stored_interface_wrench = np.asarray(
                interface["interface_wrench_on_block_xyz_n_nmm"], dtype=float
            )
            source_interface_join_residual = (
                source_interface_wrench - stored_interface_wrench
            )
            require(
                max_abs(source_interface_join_residual[:3]) < FORCE_ACCOUNTING_TOL_N
                and max_abs(source_interface_join_residual[3:])
                < MOMENT_ACCOUNTING_TOL_NMM,
                f"saved header interface wrench does not restore from source rows: {body}/{case_id}",
            )
            boundary_interface_wrench = sum(
                (
                    np.asarray(item["mapped_wrench_xyz_n_nmm"], dtype=float)
                    for item in action_results
                ),
                np.zeros(6),
            )
            interface_residual = source_interface_wrench - boundary_interface_wrench
            interface_accounting_pass = (
                max_abs(interface_residual[:3]) < FORCE_ACCOUNTING_TOL_N
                and max_abs(interface_residual[3:]) < MOMENT_ACCOUNTING_TOL_NMM
            )

            retained_points = []
            for action in full_actions:
                if int(action["row"]) in selected_rows:
                    continue
                point = vec(action["point_mm"])
                retained_points.append(
                    {
                        "source_row": int(action["row"]),
                        "source_id": action["source_id"],
                        "role": action["role"],
                        "other_body": action["other_body"],
                        "point_xyz_mm": action["point_mm"],
                        "point_member_guv_mm": local_guv(point, geometry_record),
                        "force_xyz_n": action["force_n"],
                        "free_moment_nmm": action["free_moment_nmm"],
                        "placement_status": "UNCHANGED_FROZEN_SOURCE_POINT_NOT_PHYSICALLY_BOUNDARY_RECOVERED",
                    }
                )
            aggregate["retained_nonheader_points"] += len(retained_points)
            source_body_wrench = wrench(full_actions, datum)
            nonheader_source_wrench = wrench(
                [
                    action
                    for action in full_actions
                    if int(action["row"]) not in selected_rows
                ],
                datum,
            )
            body_boundary_interface_wrench = transport_wrench(
                boundary_interface_wrench, vec(interface["datum_xyz_mm"]), datum
            )
            body_accounting_wrench = (
                body_boundary_interface_wrench + nonheader_source_wrench
            )
            body_accounting_residual = source_body_wrench - body_accounting_wrench
            all_joint_duty = closure_duties.get(body)
            require(
                all_joint_duty is not None and case_id in all_joint_duty["case_ids"],
                f"all-joint duty link missing: {body}/{case_id}",
            )
            state_cuts = {}
            for axis_index, axis_name in ((1, "u"), (2, "v")):
                identity = (body, case_id, axis_index)
                remain = remaining_states[identity]
                state_cuts[axis_name] = {
                    "local_axis_index": axis_index,
                    "source_cut_count": int(remain["cut_count"]),
                    "source_states": cut_states[identity],
                    "all_joint_state_source": {
                        "path": key(ALL_JOINT_DIR / "checks.json"),
                        "sha256": pins[ALL_JOINT_DIR / "checks.json"],
                        "pointer": f"/states/{next(i for i, s in enumerate(context['all_joint']['states']) if s['body'] == body and s['case_id'] == case_id and int(s['axis']) == axis_index)}",
                    },
                    "remaining_transverse_source": {
                        "path": key(REMAINING_DIR / "checks.json"),
                        "sha256": pins[REMAINING_DIR / "checks.json"],
                    },
                }
                aggregate["u_v_cut_states"] += 1
                aggregate["u_v_cut_limits"] += sum(
                    len(record["limits"]) for record in cut_states[identity]
                )

            body_results.append(
                {
                    "body": body,
                    "case_id": case_id,
                    "header_axis_ids": axes,
                    "source_interface_datum_xyz_mm": interface["datum_xyz_mm"],
                    "source_body_datum_xyz_mm": datum.tolist(),
                    "header_interface": {
                        "source_action_count": len(header_actions),
                        "source_wrench_xyz_n_nmm": source_interface_wrench.tolist(),
                        "stored_source_wrench_xyz_n_nmm": stored_interface_wrench.tolist(),
                        "source_rows_to_interface_wrench_residual_xyz_n_nmm": source_interface_join_residual.tolist(),
                        "boundary_field_wrench_xyz_n_nmm": boundary_interface_wrench.tolist(),
                        "boundary_field_wrench_datum_xyz_mm": interface["datum_xyz_mm"],
                        "boundary_field_to_source_wrench_residual_xyz_n_nmm": interface_residual.tolist(),
                        "numerical_accounting_within_saved_tolerance": interface_accounting_pass,
                        "unmapped_boundary_actions": unmapped_actions,
                        "unmapped_source_free_couples_nmm": [
                            item["unmapped_source_free_moment_nmm"]
                            for item in action_results
                        ],
                        "actions": action_results,
                    },
                    "whole_body_accounting": {
                        "source_action_count": len(full_actions),
                        "source_wrench_xyz_n_nmm": source_body_wrench.tolist(),
                        "header_boundary_fields_plus_retained_nonheader_source_wrench_xyz_n_nmm": body_accounting_wrench.tolist(),
                        "accounting_datum_xyz_mm": datum.tolist(),
                        "source_to_mixed_inventory_residual_xyz_n_nmm": body_accounting_residual.tolist(),
                        "retained_nonheader_source_point_actions": retained_points,
                        "complete_body_physical_boundary_recovered": False,
                        "reason": "Only header-interface forces are mapped to physical surfaces; other joint actions and discrete body loads retain exact source points.",
                    },
                    "u_v_cut_catalog": state_cuts,
                    "splitting_demand_and_capacity": {
                        "source_diagnostic_only": True,
                        "new_demand_or_resistance_calculated": False,
                        "all_joint_duty_reference": {
                            "path": key(ALL_JOINT_DIR / "checks.json"),
                            "sha256": pins[ALL_JOINT_DIR / "checks.json"],
                            "joint_id": all_joint_duty["joint_id"],
                            "physical_axis_ids": all_joint_duty["physical_axis_ids"],
                        },
                    },
                }
            )

    require(
        aggregate["cases"] == len(BODIES) * len(CASES),
        "six-body/six-case interface coverage differs",
    )
    require(
        aggregate["u_v_cut_states"] == len(BODIES) * len(CASES) * 2,
        "u/v source cut catalog coverage differs",
    )
    authenticate(pins)
    result = {
        "schema": "six_header_cleat_boundary_fields/v1",
        "status": "PREPARED_CONDITIONAL_HEADER_BOUNDARY_FIELDS",
        "source_free_couple_classification": {
            "status": "UNRESOLVED_PHYSICAL_FREE_COUPLES"
            if aggregate["unsupported_source_free_couple_rows"]
            else "WITHIN_SAVED_NUMERICAL_ACCOUNTING_TOLERANCE",
            "component_tolerance_nmm": MOMENT_ACCOUNTING_TOL_NMM,
            "maximum_absolute_component_nmm": max(
                max_abs(vec(action["free_moment_nmm"]))
                for case in inputs["cases"] for interface in case["interfaces"]
                for action in interface["actions_on_block"]
            ),
            "all_raw_free_couples_retained": True,
        },
        "source_authority": {
            "candidate": model["source_identity"]["candidate"],
            "development_revision": model["source_identity"]["development_revision"],
            "selected_axis_count": context["all_joint"]["reviewed_authority"][
                "bolt_axes"
            ],
            "header_axis_count": 12,
            "case_ids": list(CASES),
            "six_target_bodies": list(BODIES),
            "available_108_axis_proposal": context["all_joint"][
                "unadopted_108_axis_proposal"
            ],
            "proposal_adopted": False,
        },
        "boundary_assumptions": {
            "washer": {
                "source": WASHER_SCENARIO,
                "inner_radius_mm": context["washer_inner_radius_mm"],
                "outer_radius_mm": context["washer_outer_radius_mm"],
                "pressure": "concentric uniform annulus on saved opposite-end cleat face",
                "delivered_washer_inspected": False,
            },
            "contact": "Frictionless constant normal traction over each exact saved trimmed sampler cell; geometry comes from frozen patch/cell fields.",
            "lateral_bore": "Frictionless nonnegative half-cosine pressure on two supported axial strips; +2F at L/4 and -F at L/2 preserve source resultant and first moments.",
            "nonheader_actions": "Remain at original source points/free couples and are included once in whole-body accounting.",
            "field_coordinates": "Global XYZ plus each cleat's local grain/u/v frame. Every saved transverse u and v cut station is linked.",
        },
        "known_answer_coupon": coupon,
        "counts": aggregate,
        "bodies": body_results,
        "limits": [
            "Numerical wrench closure is action accounting, not pressure compatibility or timber stress.",
            "Any source free couple or frictionless-incompatible force component remains explicit and unplaced; no balancing couple is invented.",
            "Other interfaces, body gravity, nonheader pressure, hardware resistance and full-body physical boundary fields are not recovered here.",
            "No Ft-perpendicular value, splitting resistance, hardware reserve, preload, friction, native solve, CAD, frame solve, geometry change or adoption is added.",
            "A zero or small source free-couple residual does not establish complete joint acceptance.",
        ],
        **FLAGS,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "result.json", result)
    sources = {key(path): digest for path, digest in sorted(pins.items())}
    artifacts = {path.name: sha(path) for path in output.iterdir() if path.is_file()}
    receipt = {
        "schema": "six_header_cleat_boundary_fields_receipt/v1",
        "status": result["status"],
        "counts": aggregate,
        "source_sha256": sources,
        "output_sha256": artifacts,
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
        **FLAGS,
    }
    write(output / "receipt.json", receipt)
    return {
        "status": result["status"],
        "counts": aggregate,
        "result_sha256": sha(output / "result.json"),
        "receipt_sha256": sha(output / "receipt.json"),
    }


def interface_datum(interface: dict[str, Any]) -> np.ndarray:
    return vec(interface["datum_xyz_mm"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--coupon-only", action="store_true")
    args = parser.parse_args()
    bore_helper = module(BORE_MAP, "corner_bore_wall_coupon")
    if args.coupon_only:
        print(json.dumps(known_answer_coupon(bore_helper), sort_keys=True))
        return
    require(
        args.output is not None, "--output is required unless --coupon-only is selected"
    )
    print(json.dumps(build(args.output), sort_keys=True))


if __name__ == "__main__":
    main()
