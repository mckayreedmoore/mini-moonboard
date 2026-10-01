#!/usr/bin/env python3
"""Replay a pinned upper-block geometry and exact-section inventory.

The report is geometry evidence only. It assigns no member force or moment to
the sampled sections and makes no strength or joint-acceptance claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

SOURCE_PINS = (
    {
        "source_id": "upper_outer_and_center",
        "path": "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/upper-joints.json",
        "sha256": "0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6",
    },
    {
        "source_id": "service_and_g7",
        "path": "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/upper-joints.json",
        "sha256": "f4c92d874dcb0f40e5e900971deaff9580e99063b453e1984e9b1ba660a2be9f",
    },
)

EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_SOURCE_BLOCKS = 4
EXPECTED_AXES_PER_SOURCE = 16
EXPECTED_ACTIONS_PER_AXIS = 21
EXPECTED_GROUP_MEMBERS = ("block", "host")
EXPECTED_EDGE_REFERENCE_MM = 25.4
EXPECTED_END_REFERENCE_MM = 44.45
NOMINAL_D_MM = 6.35
GEOMETRY_TOL_MM = 1e-5
VECTOR_TOL = 1e-7
SECTION_STATION_TOL_MM = 1e-5


class InventoryError(ValueError):
    """Raised when a pinned source or its internal geometry is inconsistent."""


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    relative_path: str
    sha256: str
    data: dict[str, Any]


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _unit(vector: Sequence[float]) -> list[float]:
    magnitude = _norm(vector)
    if magnitude <= 0:
        raise InventoryError("zero-length direction vector")
    return [float(value) / magnitude for value in vector]


def _sub(a: Sequence[float], b: Sequence[float]) -> list[float]:
    return [float(x) - float(y) for x, y in zip(a, b, strict=True)]


def _add_scaled(point: Sequence[float], axis: Sequence[float], amount: float) -> list[float]:
    return [float(point[i]) + float(axis[i]) * amount for i in range(3)]


def _clean(value: Any) -> Any:
    """Make stable compact JSON numbers without losing section geometry."""
    if isinstance(value, float):
        if abs(value) < 5e-13:
            return 0.0
        return round(value, 9)
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, tuple):
        return [_clean(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    return value


def load_pinned_sources(
    payload_overrides: Mapping[str, bytes] | None = None,
) -> list[SourceDocument]:
    """Read both exact source reports and reject changed bytes before parsing."""
    payload_overrides = payload_overrides or {}
    documents = []
    for pin in SOURCE_PINS:
        path = ROOT / pin["path"]
        raw = payload_overrides.get(pin["source_id"])
        if raw is None:
            try:
                raw = path.read_bytes()
            except OSError as error:
                raise InventoryError(f"cannot read pinned source {pin['path']}: {error}") from error
        actual = sha256_bytes(raw)
        if actual != pin["sha256"]:
            raise InventoryError(
                f"source hash mismatch for {pin['path']}: expected {pin['sha256']}, got {actual}"
            )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            raise InventoryError(f"pinned source is not valid JSON: {pin['path']}") from error
        if not isinstance(data, dict):
            raise InventoryError(f"pinned source root is not an object: {pin['path']}")
        documents.append(
            SourceDocument(pin["source_id"], pin["path"], actual, data)
        )
    return documents


def _close(a: float, b: float, tolerance: float, label: str) -> None:
    if abs(a - b) > tolerance:
        raise InventoryError(f"{label} differs: {a:.12g} vs {b:.12g}")


def _check_member_geometry(member: dict[str, Any], axis_id: str, role: str) -> None:
    required = (
        "member",
        "finished_step",
        "finished_step_sha256",
        "box_origin_xyz_mm",
        "box_axes_xyz",
        "box_bounds_mm",
        "conditional_grain_xyz",
        "bolt_line_mid_bearing_xyz_mm",
        "boundary_limit",
    )
    missing = [key for key in required if key not in member]
    if missing:
        raise InventoryError(f"{axis_id}/{role} geometry missing {missing}")
    if member["boundary_limit"] != "Outer box only; local cuts and other bores are separate checks.":
        raise InventoryError(f"{axis_id}/{role} no longer declares the outer-box limit")
    if len(member["box_axes_xyz"]) != 3 or len(member["box_bounds_mm"]) != 3:
        raise InventoryError(f"{axis_id}/{role} requires three box axes and bounds")
    axes = [_unit(axis) for axis in member["box_axes_xyz"]]
    for i, axis in enumerate(axes):
        _close(_norm(member["box_axes_xyz"][i]), 1.0, VECTOR_TOL, f"{axis_id}/{role} box axis norm")
    for i in range(3):
        for j in range(i + 1, 3):
            _close(_dot(axes[i], axes[j]), 0.0, VECTOR_TOL, f"{axis_id}/{role} box axes orthogonality")
        lo, hi = member["box_bounds_mm"][i]
        if not math.isfinite(float(lo)) or not math.isfinite(float(hi)) or hi <= lo:
            raise InventoryError(f"{axis_id}/{role} invalid outer-box interval {i}")
    grain = _unit(member["conditional_grain_xyz"])
    _close(_norm(member["conditional_grain_xyz"]), 1.0, VECTOR_TOL, f"{axis_id}/{role} grain norm")
    if max(abs(_dot(grain, axis)) for axis in axes) < 1.0 - VECTOR_TOL:
        raise InventoryError(f"{axis_id}/{role} conditional grain is not a box axis")
    for xyz_name in ("box_origin_xyz_mm", "bolt_line_mid_bearing_xyz_mm"):
        if len(member[xyz_name]) != 3 or not all(math.isfinite(float(x)) for x in member[xyz_name]):
            raise InventoryError(f"{axis_id}/{role} invalid {xyz_name}")


def _source_reports(documents: Sequence[SourceDocument]) -> list[SourceDocument]:
    if len(documents) != len(SOURCE_PINS):
        raise InventoryError(f"expected {len(SOURCE_PINS)} source reports, received {len(documents)}")
    by_id = {document.source_id: document for document in documents}
    if len(by_id) != len(documents) or set(by_id) != {pin["source_id"] for pin in SOURCE_PINS}:
        raise InventoryError("source identifiers do not match the pinned input inventory")
    result = []
    for pin in SOURCE_PINS:
        document = by_id[pin["source_id"]]
        if document.relative_path != pin["path"] or document.sha256 != pin["sha256"]:
            raise InventoryError(f"source metadata no longer matches pin for {pin['source_id']}")
        data = document.data
        if data.get("candidate") != EXPECTED_CANDIDATE:
            raise InventoryError(f"unexpected candidate in {pin['source_id']}")
        if data.get("geometry_revision_id") != EXPECTED_REVISION:
            raise InventoryError(f"unexpected geometry revision in {pin['source_id']}")
        if data.get("reviewed_geometry_changed") is not False:
            raise InventoryError(f"reviewed geometry changed in {pin['source_id']}")
        if data.get("complete_joint_resistance_established") is not False:
            raise InventoryError(f"source promotes complete joint resistance: {pin['source_id']}")
        if data.get("six_case_envelope_established") is not False:
            raise InventoryError(f"source promotes a six-case envelope: {pin['source_id']}")
        result.append(document)
    return result


def _validate_document(document: SourceDocument) -> None:
    data = document.data
    counts = data.get("counts", {})
    if counts.get("upper_blocks") != EXPECTED_SOURCE_BLOCKS:
        raise InventoryError(f"unexpected upper block count in {document.source_id}")
    if counts.get("physical_bolts") != EXPECTED_AXES_PER_SOURCE:
        raise InventoryError(f"unexpected bolt count in {document.source_id}")
    if counts.get("bolt_action_records") != EXPECTED_AXES_PER_SOURCE * EXPECTED_ACTIONS_PER_AXIS:
        raise InventoryError(f"unexpected action count in {document.source_id}")
    if counts.get("signed_member_direction_records") != EXPECTED_AXES_PER_SOURCE * EXPECTED_ACTIONS_PER_AXIS * 2:
        raise InventoryError(f"unexpected direction count in {document.source_id}")

    geometry = data.get("geometry_by_axis")
    actions = data.get("bolt_actions")
    if not isinstance(geometry, dict) or len(geometry) != EXPECTED_AXES_PER_SOURCE:
        raise InventoryError(f"expected {EXPECTED_AXES_PER_SOURCE} geometry axes in {document.source_id}")
    if not isinstance(actions, list) or len(actions) != EXPECTED_AXES_PER_SOURCE * EXPECTED_ACTIONS_PER_AXIS:
        raise InventoryError(f"wrong action record count in {document.source_id}")
    actions_by_axis: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for action in actions:
        axis_id = action.get("axis_id")
        if axis_id not in geometry:
            raise InventoryError(f"action references absent geometry axis {axis_id!r} in {document.source_id}")
        geometry_row = geometry[axis_id]
        if action.get("block") != geometry_row.get("block") or action.get("host") != geometry_row.get("host"):
            raise InventoryError(f"action block/host disagrees with geometry at {axis_id}")
        if set(action.get("member_directions", {})) != set(EXPECTED_GROUP_MEMBERS):
            raise InventoryError(f"action member direction roles are incomplete at {axis_id}")
        actions_by_axis[axis_id].append(action)
    if set(actions_by_axis) != set(geometry):
        raise InventoryError(f"action and geometry axis inventories differ in {document.source_id}")

    expected_cases = set(data.get("source_cases", {}))
    if len(expected_cases) != 3:
        raise InventoryError(f"expected three pinned source cases in {document.source_id}")
    for axis_id, geometry_row in geometry.items():
        hardware = geometry_row.get("hardware_axis_record", {})
        if hardware.get("axis_id") != axis_id:
            raise InventoryError(f"hardware axis does not match geometry key {axis_id}")
        if geometry_row.get("block") is None or geometry_row.get("host") is None:
            raise InventoryError(f"incomplete block/host identity at {axis_id}")
        if set(geometry_row.get("members", {})) != set(EXPECTED_GROUP_MEMBERS):
            raise InventoryError(f"incomplete member geometry at {axis_id}")
        for role in EXPECTED_GROUP_MEMBERS:
            _check_member_geometry(geometry_row["members"][role], axis_id, role)
        states = set()
        for action in actions_by_axis[axis_id]:
            state = (action.get("case"), action.get("increment_index"))
            if state in states:
                raise InventoryError(f"duplicate action state {state} at {axis_id}")
            states.add(state)
            if state[0] not in expected_cases or not isinstance(state[1], int) or not 0 <= state[1] < 7:
                raise InventoryError(f"unexpected action state {state} at {axis_id}")
            geometry_rows = geometry_row["members"]
            action_force = action.get("lateral_force_on_block_n")
            if len(action_force) != 3:
                raise InventoryError(f"invalid lateral vector at {axis_id}")
            for role in EXPECTED_GROUP_MEMBERS:
                member = geometry_rows[role]
                direction = action["member_directions"][role]
                member_force = action_force if role == "block" else [-float(x) for x in action_force]
                grain_component = _dot(member_force, member["conditional_grain_xyz"])
                cross_record = direction["cross_grain_edge_direction"]
                cross_component = _dot(member_force, cross_record["component_axis_global_xyz"])
                _close(
                    grain_component,
                    float(direction["force_parallel_to_grain_signed_n"]),
                    2e-5,
                    f"{axis_id}/{role} grain-force projection",
                )
                _close(
                    cross_component,
                    float(direction["force_cross_grain_signed_on_frame_axis_n"]),
                    2e-5,
                    f"{axis_id}/{role} cross-grain projection",
                )
                magnitude = math.hypot(grain_component, cross_component)
                angle = math.degrees(math.atan2(abs(cross_component), abs(grain_component)))
                _close(magnitude, float(action["lateral_magnitude_n"]), 2e-5, f"{axis_id}/{role} projected lateral magnitude")
                _close(angle, float(direction["unsigned_load_to_grain_degrees"]), 2e-5, f"{axis_id}/{role} load angle")
                for boundary_key in ("cross_grain_edge_direction", "grain_end_direction"):
                    boundary = direction[boundary_key]
                    distance = boundary.get("distance_to_loaded_outer_boundary_mm")
                    if distance is None:
                        continue
                    member_axis_index = boundary.get("local_member_axis_index")
                    if not isinstance(member_axis_index, int) or member_axis_index not in (0, 1, 2):
                        raise InventoryError(f"invalid local axis at {axis_id}/{role}/{boundary_key}")
                    local_axis = member["box_axes_xyz"][member_axis_index]
                    point = member["bolt_line_mid_bearing_xyz_mm"]
                    origin = member["box_origin_xyz_mm"]
                    local_coordinate = _dot(_sub(point, origin), local_axis)
                    lo, hi = member["box_bounds_mm"][member_axis_index]
                    direction_name = boundary.get("loaded_component_direction")
                    if direction_name == "positive_axis":
                        expected_distance = float(hi) - local_coordinate
                        expected_side = "upper_coordinate_boundary"
                    elif direction_name == "negative_axis":
                        expected_distance = local_coordinate - float(lo)
                        expected_side = "lower_coordinate_boundary"
                    else:
                        raise InventoryError(f"invalid loaded direction at {axis_id}/{role}/{boundary_key}")
                    _close(expected_distance, float(distance), GEOMETRY_TOL_MM, f"{axis_id}/{role}/{boundary_key} outer-box distance")
                    if boundary.get("local_boundary_side") != expected_side:
                        raise InventoryError(f"boundary side disagrees with signed direction at {axis_id}/{role}/{boundary_key}")
        expected_states = {(case, increment) for case in expected_cases for increment in range(7)}
        if states != expected_states or len(states) != EXPECTED_ACTIONS_PER_AXIS:
            raise InventoryError(f"incomplete sampled actions at {axis_id}: {len(states)} states")


def _verify_member_steps(documents: Sequence[SourceDocument]) -> list[dict[str, Any]]:
    members: dict[str, dict[str, Any]] = {}
    for document in documents:
        for geometry in document.data["geometry_by_axis"].values():
            for role in EXPECTED_GROUP_MEMBERS:
                member = geometry["members"][role]
                path = member["finished_step"]
                expected = member["finished_step_sha256"]
                if path in members and members[path]["sha256"] != expected:
                    raise InventoryError(f"conflicting STEP pins for {path}")
                members[path] = {
                    "path": path,
                    "sha256": expected,
                    "member": member["member"],
                }
    verified = []
    for relative_path, record in sorted(members.items()):
        path = ROOT / relative_path
        try:
            actual = sha256_file(path)
        except OSError as error:
            raise InventoryError(f"cannot read exact member STEP {relative_path}: {error}") from error
        if actual != record["sha256"]:
            raise InventoryError(
                f"STEP hash mismatch for {relative_path}: expected {record['sha256']}, got {actual}"
            )
        verified.append({**record, "sha256_verified": True})
    return verified


def _section_schedule(
    block_name: str,
    axis_geometry: Sequence[tuple[str, dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[float], list[float]]:
    reference = axis_geometry[0][1]["members"]["block"]
    grain = _unit(reference["conditional_grain_xyz"])
    stations: list[dict[str, Any]] = []
    for axis_id, geometry in axis_geometry:
        member = geometry["members"]["block"]
        axis_grain = _unit(member["conditional_grain_xyz"])
        if _dot(grain, axis_grain) < 1.0 - VECTOR_TOL:
            raise InventoryError(f"conditional grain changes within block {block_name}")
        point = member["bolt_line_mid_bearing_xyz_mm"]
        stations.append(
            {
                "axis_id": axis_id,
                "point_xyz_mm": [float(value) for value in point],
                "grain_coordinate_mm": _dot(point, grain),
            }
        )
    stations.sort(key=lambda row: (row["grain_coordinate_mm"], row["axis_id"]))
    grouped: list[list[dict[str, Any]]] = []
    for station in stations:
        if not grouped or abs(station["grain_coordinate_mm"] - grouped[-1][0]["grain_coordinate_mm"]) > SECTION_STATION_TOL_MM:
            grouped.append([station])
        else:
            grouped[-1].append(station)
    distinct = [
        {
            "grain_coordinate_mm": math.fsum(row["grain_coordinate_mm"] for row in group) / len(group),
            "axis_ids": sorted(row["axis_id"] for row in group),
            "points_xyz_mm": [row["point_xyz_mm"] for row in sorted(group, key=lambda item: item["axis_id"])],
        }
        for group in grouped
    ]
    if len(distinct) < 2:
        raise InventoryError(f"block {block_name} needs at least two distinct bolt stations")
    anchor = stations[0]["point_xyz_mm"]
    anchor_coordinate = stations[0]["grain_coordinate_mm"]
    samples: list[dict[str, Any]] = []
    for index, station in enumerate(distinct):
        samples.append(
            {
                "sample_kind": "bolt_mid_bearing_station",
                "grain_coordinate_mm": station["grain_coordinate_mm"],
                "station_axis_ids": station["axis_ids"],
                "between_station_axis_ids": None,
                "plane_origin_xyz_mm": _add_scaled(
                    anchor,
                    grain,
                    station["grain_coordinate_mm"] - anchor_coordinate,
                ),
            }
        )
        if index + 1 < len(distinct):
            next_station = distinct[index + 1]
            between_coordinate = 0.5 * (
                station["grain_coordinate_mm"] + next_station["grain_coordinate_mm"]
            )
            samples.append(
                {
                    "sample_kind": "between_adjacent_bolt_stations",
                    "grain_coordinate_mm": between_coordinate,
                    "station_axis_ids": [],
                    "between_station_axis_ids": [
                        station["axis_ids"],
                        next_station["axis_ids"],
                    ],
                    "plane_origin_xyz_mm": _add_scaled(
                        anchor,
                        grain,
                        between_coordinate - anchor_coordinate,
                    ),
                }
            )
    return samples, grain, [float(row["grain_coordinate_mm"]) for row in distinct]


def _section_components(shape: Any, origin: Sequence[float], grain: Sequence[float]) -> dict[str, Any]:
    """Return exact trimmed section faces from a pinned single-solid STEP BRep."""
    import cadquery as cq

    normal = _unit(grain)
    raw_x = (1.0, 0.0, 0.0) if abs(normal[0]) < 0.9 else (0.0, 1.0, 0.0)
    projection = _dot(raw_x, normal)
    x_axis = _unit([raw_x[i] - projection * normal[i] for i in range(3)])
    plane = cq.Plane(origin=tuple(float(x) for x in origin), xDir=tuple(x_axis), normal=tuple(normal))
    section = cq.Workplane(plane).add(shape).section().val()
    if not section.isValid():
        raise InventoryError("OCC returned an invalid planar section")
    faces = section.Faces()
    if not faces:
        raise InventoryError("section plane did not return material faces")
    components = []
    for face in faces:
        if face.geomType() != "PLANE" or not face.isValid():
            raise InventoryError("section produced a non-planar or invalid component face")
        area = float(face.Area())
        if not math.isfinite(area) or area <= 0.0:
            raise InventoryError("section produced a non-positive component area")
        components.append(
            {
                "area_mm2": area,
                "boundary_wire_count": len(face.Wires()),
                "boundary_edge_count": len(face.Edges()),
            }
        )
    components.sort(key=lambda row: (row["area_mm2"], row["boundary_wire_count"], row["boundary_edge_count"]))
    return {
        "area_mm2": math.fsum(row["area_mm2"] for row in components),
        "material_component_count": len(components),
        "components": components,
        "section_face_count": len(faces),
        "method": "CadQuery/OCC section of the exact hash-verified STEP solid; areas are summed from returned trimmed planar faces, retaining modeled bores and cuts.",
    }


def _extract_block_sections(
    documents: Sequence[SourceDocument],
    step_sources: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    import cadquery as cq

    member_pins = {row["path"]: row for row in step_sources}
    source_geometry: dict[str, dict[str, Any]] = {}
    source_axes: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for document in documents:
        for axis_id, geometry in document.data["geometry_by_axis"].items():
            member = geometry["members"]["block"]
            name = member["member"]
            if name in source_geometry:
                prior = source_geometry[name]
                if prior["finished_step"] != member["finished_step"] or prior["finished_step_sha256"] != member["finished_step_sha256"]:
                    raise InventoryError(f"block {name} has conflicting exact STEP sources")
            else:
                source_geometry[name] = member
            source_axes[name].append((axis_id, geometry))

    output = []
    sections_by_block: dict[str, dict[str, Any]] = {}
    for block_name in sorted(source_geometry):
        member = source_geometry[block_name]
        relative_path = member["finished_step"]
        if relative_path not in member_pins or not member_pins[relative_path]["sha256_verified"]:
            raise InventoryError(f"block STEP was not hash-verified: {relative_path}")
        path = ROOT / relative_path
        try:
            shape = cq.importers.importStep(str(path)).val()
        except Exception as error:
            raise InventoryError(f"cannot import pinned block STEP {relative_path}: {error}") from error
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise InventoryError(f"block STEP must contain one valid solid: {relative_path}")
        samples, grain, stations = _section_schedule(block_name, source_axes[block_name])
        for sample_index, sample in enumerate(samples, start=1):
            section = _section_components(shape, sample["plane_origin_xyz_mm"], grain)
            sample.update(section)
            sample["sample_id"] = f"{block_name}-S{sample_index:02d}"
            sample["section_plane_normal_global_xyz"] = grain
            sample["sampled_bolt_mid_bearing_station_count"] = len(stations)
            sample["continuous_between_samples_inferred"] = False
        block_result = {
            "block": block_name,
            "exact_geometry_available": True,
            "finished_step": relative_path,
            "finished_step_sha256": member["finished_step_sha256"],
            "declared_grain_global_xyz": grain,
            "distinct_bolt_mid_bearing_stations_mm": stations,
            "sampled_section_count": len(samples),
            "sampled_sections": samples,
            "member_force_moment_to_sampled_sections": "open; no section is assigned a force or moment by this geometry inventory",
            "critical_section_between_samples": "not established; only the listed stations and midpoints were queried",
        }
        output.append(block_result)
        sections_by_block[block_name] = block_result
    return output, sections_by_block


def _direction_record(
    document: SourceDocument,
    axis_id: str,
    geometry: dict[str, Any],
    role: str,
    actions: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    member = geometry["members"][role]
    grain = _unit(member["conditional_grain_xyz"])
    edge_reference = float(document.data["pure_direction_geometry_comparisons"]["conditional_perpendicular_loaded_edge_4D_mm"])
    end_reference = float(document.data["pure_direction_geometry_comparisons"]["conditional_softwood_parallel_tension_7D_mm"])
    _close(edge_reference, EXPECTED_EDGE_REFERENCE_MM, 1e-9, "conditional 4D reference")
    _close(end_reference, EXPECTED_END_REFERENCE_MM, 1e-9, "conditional 7D reference")

    edge_rows = []
    end_rows = []
    lateral_peak = None
    grain_peak = None
    cross_peak = None
    angle_min = None
    angle_max = None
    mixed_state_count = 0
    state_rows = []
    for action in actions:
        direction = action["member_directions"][role]
        member_force = action["lateral_force_on_block_n"] if role == "block" else [-float(x) for x in action["lateral_force_on_block_n"]]
        grain_component = float(direction["force_parallel_to_grain_signed_n"])
        cross_component = float(direction["force_cross_grain_signed_on_frame_axis_n"])
        angle = float(direction["unsigned_load_to_grain_degrees"])
        state = {"case": action["case"], "increment_index": action["increment_index"], "load_factor": action["load_factor"]}
        magnitude = float(action["lateral_magnitude_n"])
        state_rows.append((action, direction, state, member_force, grain_component, cross_component, angle, magnitude))
        if abs(grain_component) > 1e-8 and abs(cross_component) > 1e-8:
            mixed_state_count += 1
        if lateral_peak is None or magnitude > lateral_peak[0]:
            lateral_peak = (magnitude, state)
        grain_abs = abs(grain_component)
        if grain_peak is None or grain_abs > grain_peak[0]:
            grain_peak = (grain_abs, grain_component, state)
        cross_abs = abs(cross_component)
        if cross_peak is None or cross_abs > cross_peak[0]:
            cross_peak = (cross_abs, cross_component, state)
        if angle_min is None or angle < angle_min[0]:
            angle_min = (angle, state)
        if angle_max is None or angle > angle_max[0]:
            angle_max = (angle, state)
        for boundary_key, destination in (
            ("cross_grain_edge_direction", edge_rows),
            ("grain_end_direction", end_rows),
        ):
            boundary = direction[boundary_key]
            distance = boundary.get("distance_to_loaded_outer_boundary_mm")
            if distance is not None:
                destination.append(
                    {
                        "distance_mm": float(distance),
                        "state": state,
                        "side": boundary["local_boundary_side"],
                        "signed_component_n": float(boundary["signed_component_n"]),
                    }
                )

    if not state_rows:
        raise InventoryError(f"no direction states for {axis_id}/{role}")
    min_edge = min(edge_rows, key=lambda row: row["distance_mm"]) if edge_rows else None
    min_end = min(end_rows, key=lambda row: row["distance_mm"]) if end_rows else None
    representative_direction = state_rows[0][1]
    edge_direction = representative_direction["cross_grain_edge_direction"]
    end_direction = representative_direction["grain_end_direction"]
    edge_axis_index = int(edge_direction["local_member_axis_index"])
    grain_axis_index = int(end_direction["local_member_axis_index"])
    box_axes = member["box_axes_xyz"]
    if edge_axis_index == grain_axis_index:
        raise InventoryError(f"edge and grain end directions share one box axis at {axis_id}/{role}")
    _close(abs(_dot(_unit(edge_direction["component_axis_global_xyz"]), _unit(box_axes[edge_axis_index]))), 1.0, VECTOR_TOL, f"{axis_id}/{role} edge direction/box axis")
    _close(abs(_dot(grain, _unit(box_axes[grain_axis_index]))), 1.0, VECTOR_TOL, f"{axis_id}/{role} grain direction/box axis")
    local_coordinates = [
        _dot(_sub(member["bolt_line_mid_bearing_xyz_mm"], member["box_origin_xyz_mm"]), axis)
        for axis in box_axes
    ]
    edge_lo, edge_hi = member["box_bounds_mm"][edge_axis_index]
    grain_lo, grain_hi = member["box_bounds_mm"][grain_axis_index]
    outer_box_basis = {
        "origin_xyz_mm": member["box_origin_xyz_mm"],
        "axes_xyz": box_axes,
        "bounds_mm_by_axis": member["box_bounds_mm"],
        "bolt_line_mid_bearing_local_coordinates_mm": local_coordinates,
        "cross_grain_edge_axis_index": edge_axis_index,
        "cross_grain_edge_distances_mm": {
            "lower_coordinate_boundary": local_coordinates[edge_axis_index] - float(edge_lo),
            "upper_coordinate_boundary": float(edge_hi) - local_coordinates[edge_axis_index],
        },
        "grain_end_axis_index": grain_axis_index,
        "grain_end_distances_mm": {
            "lower_coordinate_boundary": local_coordinates[grain_axis_index] - float(grain_lo),
            "upper_coordinate_boundary": float(grain_hi) - local_coordinates[grain_axis_index],
        },
        "boundary_limit": member["boundary_limit"],
    }
    return {
        "source_id": document.source_id,
        "block": geometry["block"],
        "host": geometry["host"],
        "axis_id": axis_id,
        "member_role": role,
        "member": member["member"],
        "finished_step": member["finished_step"],
        "finished_step_sha256": member["finished_step_sha256"],
        "conditional_grain_global_xyz": grain,
        "bolt_line_mid_bearing_xyz_mm": member["bolt_line_mid_bearing_xyz_mm"],
        "outer_box_geometry": outer_box_basis,
        "outer_box_only": True,
        "conditional_pure_direction_geometry_comparators": {
            "cross_grain_loaded_edge": {
                "minimum_loaded_outer_box_distance_mm": min_edge["distance_mm"] if min_edge else None,
                "minimum_distance_state": min_edge["state"] if min_edge else None,
                "loaded_outer_box_side": min_edge["side"] if min_edge else None,
                "conditional_4D_reference_mm": edge_reference,
                "minimum_distance_divided_by_reference": min_edge["distance_mm"] / edge_reference if min_edge else None,
                "shorter_than_conditional_reference": min_edge["distance_mm"] < edge_reference - GEOMETRY_TOL_MM if min_edge else None,
            },
            "grain_parallel_loaded_end": {
                "minimum_loaded_outer_box_distance_mm": min_end["distance_mm"] if min_end else None,
                "minimum_distance_state": min_end["state"] if min_end else None,
                "loaded_outer_box_side": min_end["side"] if min_end else None,
                "conditional_7D_reference_mm": end_reference,
                "minimum_distance_divided_by_reference": min_end["distance_mm"] / end_reference if min_end else None,
                "shorter_than_conditional_reference": min_end["distance_mm"] < end_reference - GEOMETRY_TOL_MM if min_end else None,
            },
            "interpretation": "Pure-direction conditional geometry comparators only. Outer-box distances exclude bores, seats, cuts and other boundaries; these are not applied to the simultaneous oblique vector.",
        },
        "sampled_actual_lateral_vector_envelope": {
            "sampled_state_count": len(state_rows),
            "states_with_nonzero_grain_and_cross_grain_components": mixed_state_count,
            "resultant_magnitude_max_n": lateral_peak[0],
            "resultant_magnitude_max_state": lateral_peak[1],
            "absolute_grain_component_max_n": grain_peak[0],
            "grain_component_signed_at_max_n": grain_peak[1],
            "grain_component_max_state": grain_peak[2],
            "absolute_cross_grain_component_max_n": cross_peak[0],
            "cross_grain_component_signed_at_max_n": cross_peak[1],
            "cross_grain_component_max_state": cross_peak[2],
            "unsigned_angle_to_grain_min_degrees": angle_min[0],
            "angle_min_state": angle_min[1],
            "unsigned_angle_to_grain_max_degrees": angle_max[0],
            "angle_max_state": angle_max[1],
            "actual_vector_applicability": "unresolved; source component directions are oblique in the sampled states, and no direction-only reference is applied as an oblique-load rule",
        },
        "exact_geometry_available": True,
        "finished_section_applicability": (
            "sampled exact section areas are reported for this block solid; no section demand assignment or member capacity is established"
            if role == "block"
            else "host STEP geometry is hash-pinned, but no host section query or section demand assignment is included"
        ),
    }


def _bolt_groups(documents: Sequence[SourceDocument]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[tuple[SourceDocument, str, dict[str, Any]]]] = defaultdict(list)
    for document in documents:
        for axis_id, geometry in document.data["geometry_by_axis"].items():
            key = (geometry["block"], geometry["host"], document.source_id)
            grouped[key].append((document, axis_id, geometry))
    result = []
    for (block, host, source_id), rows in sorted(grouped.items()):
        rows.sort(key=lambda row: row[1])
        if len(rows) != 2:
            raise InventoryError(f"expected exactly two axes in block/host group {block}/{host}, got {len(rows)}")
        axes = [row[1] for row in rows]
        locations = [row[2]["lateral_plane_xyz_mm"] for row in rows]
        spacing_vector = _sub(locations[1], locations[0])
        spacing = _norm(spacing_vector)
        if spacing <= 0.0:
            raise InventoryError(f"zero bolt pitch in {block}/{host}")
        role_pitch = {}
        for role in EXPECTED_GROUP_MEMBERS:
            member_a = rows[0][2]["members"][role]
            member_b = rows[1][2]["members"][role]
            midpoint_delta = _sub(member_b["bolt_line_mid_bearing_xyz_mm"], member_a["bolt_line_mid_bearing_xyz_mm"])
            _close(_norm(midpoint_delta), spacing, 2e-5, f"{block}/{host}/{role} paired bolt pitch")
            grain = _unit(member_a["conditional_grain_xyz"])
            signed_along_grain = _dot(spacing_vector, grain)
            role_pitch[role] = {
                "conditional_grain_pitch_signed_mm": signed_along_grain,
                "pitch_magnitude_parallel_to_grain_mm": abs(signed_along_grain),
                "pitch_magnitude_perpendicular_to_grain_mm": math.sqrt(max(0.0, spacing * spacing - signed_along_grain * signed_along_grain)),
            }
        head_axes = [_unit(row[2]["head_to_nut_axis_xyz"]) for row in rows]
        if abs(abs(_dot(head_axes[0], head_axes[1])) - 1.0) > VECTOR_TOL:
            raise InventoryError(f"paired bolt axes are not parallel in {block}/{host}")
        result.append(
            {
                "group_id": f"{block}__{host}",
                "source_id": source_id,
                "block": block,
                "host": host,
                "bolt_count": 2,
                "axis_ids": axes,
                "axis_midplane_coordinates_xyz_mm": locations,
                "axis_spacing_vector_xyz_mm": spacing_vector,
                "center_to_center_spacing_mm": spacing,
                "center_to_center_spacing_divided_by_nominal_D": spacing / NOMINAL_D_MM,
                "nominal_D_mm_for_geometric_ratio_only": NOMINAL_D_MM,
                "pitch_by_member": role_pitch,
                "group_resistance_or_spacing_factor_established": False,
                "interpretation": "Physical two-axis geometry grouping only. It does not establish independently resisting bolt capacity, group resistance, splitting or an NDS adjustment.",
            }
        )
    return result


def build_inventory(
    documents: Sequence[SourceDocument],
    *,
    verify_step_files: bool = True,
    extract_sections: bool = True,
) -> dict[str, Any]:
    """Validate two reports and build compact geometry, group and section rows."""
    documents = _source_reports(documents)
    for document in documents:
        _validate_document(document)
    step_sources = _verify_member_steps(documents) if verify_step_files else []

    axis_rows: list[dict[str, Any]] = []
    direction_rows: list[dict[str, Any]] = []
    block_axes: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    member_identity: dict[str, dict[str, Any]] = {}
    for document in documents:
        data = document.data
        actions_by_axis: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for action in data["bolt_actions"]:
            actions_by_axis[action["axis_id"]].append(action)
        for axis_id, geometry in sorted(data["geometry_by_axis"].items()):
            actions = sorted(
                actions_by_axis[axis_id],
                key=lambda row: (row["case"], row["increment_index"]),
            )
            block_member = geometry["members"]["block"]
            block_name = geometry["block"]
            block_axes[block_name].append((axis_id, geometry))
            axis_rows.append(
                {
                    "source_id": document.source_id,
                    "axis_id": axis_id,
                    "block": block_name,
                    "host": geometry["host"],
                    "bolt_axis_head_to_nut_global_xyz": _unit(geometry["head_to_nut_axis_xyz"]),
                    "lateral_plane_xyz_mm": geometry["lateral_plane_xyz_mm"],
                    "block_bolt_line_mid_bearing_xyz_mm": block_member["bolt_line_mid_bearing_xyz_mm"],
                    "block_conditional_grain_xyz": _unit(block_member["conditional_grain_xyz"]),
                    "block_finished_step": block_member["finished_step"],
                    "block_finished_step_sha256": block_member["finished_step_sha256"],
                    "sampled_action_states": len(actions),
                }
            )
            for role in EXPECTED_GROUP_MEMBERS:
                member = geometry["members"][role]
                identity = member_identity.get(member["member"])
                if identity is not None:
                    if identity["finished_step"] != member["finished_step"] or identity["finished_step_sha256"] != member["finished_step_sha256"]:
                        raise InventoryError(f"member identity {member['member']} has conflicting STEP references")
                else:
                    member_identity[member["member"]] = {
                        "member": member["member"],
                        "finished_step": member["finished_step"],
                        "finished_step_sha256": member["finished_step_sha256"],
                    }
                direction_rows.append(_direction_record(document, axis_id, geometry, role, actions))
    if len(axis_rows) != 32 or len(block_axes) != 8:
        raise InventoryError(f"expected 32 axes across 8 blocks, got {len(axis_rows)} axes / {len(block_axes)} blocks")
    if len({row["axis_id"] for row in axis_rows}) != 32:
        raise InventoryError("physical bolt axis identifiers collide across source reports")
    if len(direction_rows) != 64:
        raise InventoryError(f"expected 64 block/host member directions, got {len(direction_rows)}")

    groups = _bolt_groups(documents)
    if len(groups) != 16 or any(row["bolt_count"] != 2 for row in groups):
        raise InventoryError("expected sixteen physical two-bolt host/block groups")

    block_sections = []
    section_engine = None
    if extract_sections:
        if not verify_step_files:
            raise InventoryError("exact section extraction requires hash-verified STEP sources")
        import cadquery as cq
        import OCP

        section_engine = {
            "cadquery_version": cq.__version__,
            "opencascade_version": OCP.__version__,
            "section_call": "cadquery.Workplane.section",
            "section_area_unit": "mm2",
        }
        block_sections, _ = _extract_block_sections(documents, step_sources)
        if len(block_sections) != 8 or sum(row["sampled_section_count"] for row in block_sections) != 40:
            raise InventoryError("expected 8 block solids and 40 station/midpoint section samples")
    else:
        for block_name, rows in sorted(block_axes.items()):
            block_sections.append(
                {
                    "block": block_name,
                    "exact_geometry_available": True,
                    "section_extraction_skipped": True,
                    "member_force_moment_to_sampled_sections": "open",
                }
            )

    blocks = []
    for block_name, rows in sorted(block_axes.items()):
        rows.sort(key=lambda row: row[0])
        first_member = rows[0][1]["members"]["block"]
        section = next(row for row in block_sections if row["block"] == block_name)
        block_groups = [row["group_id"] for row in groups if row["block"] == block_name]
        blocks.append(
            {
                "block": block_name,
                "source_ids": sorted({
                    axis["source_id"]
                    for axis in axis_rows
                    if axis["block"] == block_name
                }),
                "block_finished_step": first_member["finished_step"],
                "block_finished_step_sha256": first_member["finished_step_sha256"],
                "bolt_axis_ids": [axis_id for axis_id, _ in rows],
                "bolt_group_ids": sorted(block_groups),
                "bolt_count": len(rows),
                "conditional_grain_global_xyz": _unit(first_member["conditional_grain_xyz"]),
                "section_sample_count": section.get("sampled_section_count", 0),
                "sampled_section_areas_mm2": [
                    sample["area_mm2"] for sample in section.get("sampled_sections", [])
                ],
                "critical_section_between_samples": section.get("critical_section_between_samples", "not calculated"),
            }
        )

    input_rows = [
        {
            "source_id": document.source_id,
            "path": document.relative_path,
            "sha256": document.sha256,
            "geometry_revision_id": document.data["geometry_revision_id"],
            "block_count": len({geometry["block"] for geometry in document.data["geometry_by_axis"].values()}),
            "physical_bolt_axes": len(document.data["geometry_by_axis"]),
            "sampled_states": len(document.data["bolt_actions"]),
        }
        for document in documents
    ]
    result = {
        "schema": "upper-block-geometry-applicability-inventory/v1",
        "status": "SOURCE_BOUND_CONDITIONAL_GEOMETRY_AND_SAMPLED_SECTION_EVIDENCE",
        "producer_sha256": sha256_file(Path(__file__)),
        "candidate": EXPECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "source_reports": input_rows,
        "counts": {
            "blocks": len(blocks),
            "physical_bolt_axes": len(axis_rows),
            "sampled_bolt_action_states": sum(row["sampled_action_states"] for row in axis_rows),
            "block_host_member_direction_rows": len(direction_rows),
            "two_bolt_block_host_groups": len(groups),
            "hash_verified_unique_member_step_sources": len(step_sources),
            "exact_block_solid_section_samples": sum(row.get("sampled_section_count", 0) for row in block_sections),
        },
        "conditional_comparator_basis": {
            "nominal_bolt_diameter_mm": NOMINAL_D_MM,
            "conditional_cross_grain_edge_reference_4D_mm": EXPECTED_EDGE_REFERENCE_MM,
            "conditional_parallel_tension_end_reference_7D_mm": EXPECTED_END_REFERENCE_MM,
            "use": "Geometry-only pure-direction reference values. No direction-only reference is applied as an oblique-load rule or adopted check.",
        },
        "load_path_and_finished_section_status": {
            "exact_geometry_available_for_verified_STEP_sources": True,
            "finished_outer_box": "The source directional geometry is bounded by its stated outer box; box edges do not exclude bores, seats, or local cuts.",
            "exact_block_section_method": "Hash-verified block STEP BReps were cut by OCC planes normal to each block's declared conditional grain at every distinct bolt mid-bearing station and at the midpoint between each adjacent pair.",
            "section_component_definition": "Each OCC planar trimmed face is one connected material section component; face areas are summed for the reported section area.",
            "section_sampling_limit": "Only the listed bolt stations and adjacent-station midpoints were sampled. No critical section is extrapolated between samples.",
            "member_force_moment_assignment": "Open. This packet does not assign a frame or bolt demand to a section cut.",
            "strength_or_capacity": "Not calculated. Section area and component counts are geometry outputs, not stress, resistance, splitting capacity, or joint acceptance.",
        },
        "section_engine": section_engine,
        "finished_step_sources": step_sources,
        "blocks": blocks,
        "two_bolt_groups": groups,
        "physical_bolt_axes": axis_rows,
        "member_direction_inventory": direction_rows,
        "block_exact_sections": block_sections,
        "complete_joint_resistance_established": False,
        "six_case_envelope_established": False,
        "reviewed_geometry_changed": False,
        "native_solve_executed_by_this_packet": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    return _clean(result)


def replay_bytes() -> bytes:
    documents = load_pinned_sources()
    report = build_inventory(documents)
    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="replay and byte-compare ignored geometry.json")
    args = parser.parse_args()
    target = HERE / "geometry.json"
    output = replay_bytes()
    if args.verify:
        if not target.exists():
            raise SystemExit("geometry.json is missing; run geometry.py once to create it")
        if target.read_bytes() != output:
            raise SystemExit("geometry.json differs from source-bound geometry replay")
    else:
        target.write_bytes(output)
    report = json.loads(output)
    print(
        json.dumps(
            {
                "mode": "verify" if args.verify else "write",
                "status": report["status"],
                "counts": report["counts"],
                "geometry_json_sha256": sha256_bytes(output),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
