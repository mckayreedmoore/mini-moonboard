#!/usr/bin/env python3
"""Read-only trimmed STEP profile rays for the two BG045 bolt axes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
from OCP.TopAbs import TopAbs_IN, TopAbs_ON
from OCP.gce import gce_MakeLin
from OCP.gp import gp_Dir, gp_Pnt


HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[5]
DOCS = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
PINS_PATH = HERE / "source-pins.json"
OUTPUT = HERE / "profile-edge-query.json"
TARGET_AXES = (
    "knee_outer_left_inner_header_1",
    "knee_outer_left_inner_header_2",
)
TARGET_MEMBERS = ("base_header", "knee_outer_left_inner_frame_block")
MEMBER_LABELS = {
    "base_header": "header",
    "knee_outer_left_inner_frame_block": "inner_block",
}
D_MM = 6.35
BORE_RADIUS_MM_EXPECTED = 3.75
RAY_TOL_MM = 1.0e-6
PROFILE_MATCH_TOL_MM = 2.0e-5
FACE_NORMAL_TOL = 1.0e-8
SPAN_END_INSET_MM = 0.01
STATION_FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def dot(a: tuple[float, ...] | list[float], b: tuple[float, ...] | list[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def sub(a: tuple[float, ...] | list[float], b: tuple[float, ...] | list[float]) -> tuple[float, ...]:
    return tuple(float(x) - float(y) for x, y in zip(a, b, strict=True))


def norm(v: tuple[float, ...] | list[float]) -> float:
    return math.sqrt(dot(v, v))


def unit(v: tuple[float, ...] | list[float]) -> tuple[float, float, float]:
    length = norm(v)
    require(length > 0.0, "zero vector")
    return tuple(float(x) / length for x in v)


def add_scaled(point: tuple[float, ...], direction: tuple[float, ...], distance: float) -> tuple[float, float, float]:
    return tuple(point[i] + distance * direction[i] for i in range(3))


def round_f(value: float, digits: int = 9) -> float:
    result = round(float(value), digits)
    return 0.0 if result == 0.0 else result


def clean(value: Any) -> Any:
    if isinstance(value, float):
        return round_f(value)
    if isinstance(value, tuple):
        return [clean(x) for x in value]
    if isinstance(value, list):
        return [clean(x) for x in value]
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    return value


def bounds(shape: cq.Shape) -> dict[str, tuple[float, float]]:
    box = shape.BoundingBox()
    return {
        "x": (float(box.xmin), float(box.xmax)),
        "y": (float(box.ymin), float(box.ymax)),
        "z": (float(box.zmin), float(box.zmax)),
    }


def box_ray_limit(shape: cq.Shape, point: tuple[float, float, float], direction: tuple[float, float, float]) -> float:
    box = shape.BoundingBox()
    corners = [
        (x, y, z)
        for x in (box.xmin, box.xmax)
        for y in (box.ymin, box.ymax)
        for z in (box.zmin, box.zmax)
    ]
    return max(dot(sub(corner, point), direction) for corner in corners) + 5.0


def cylindrical_surface(face: cq.Face) -> dict[str, Any] | None:
    if face.geomType() != "CYLINDER":
        return None
    adaptor = BRepAdaptor_Surface(face.wrapped, True)
    cylinder = adaptor.Cylinder()
    location = cylinder.Location()
    direction = cylinder.Axis().Direction()
    return {
        "radius_mm": float(cylinder.Radius()),
        "axis_point_global_xyz_mm": (location.X(), location.Y(), location.Z()),
        "axis_direction_global": unit((direction.X(), direction.Y(), direction.Z())),
    }


def cylinder_role(
    info: dict[str, Any] | None,
    axis_center: tuple[float, float, float],
    bolt_axis: tuple[float, float, float],
    other_axis_centers: dict[str, tuple[float, float, float]],
) -> tuple[str, str | None, float | None]:
    if info is None:
        return "not_cylindrical", None, None
    cylinder_axis = unit(info["axis_direction_global"])
    if abs(dot(cylinder_axis, bolt_axis)) < 1.0 - FACE_NORMAL_TOL:
        return "transverse_or_oblique_cylindrical_cut", None, None
    # For parallel cylinders, remove the component along the bolt direction
    # and compare their exact BRep axis lines to the two source bolt lines.
    cylinder_origin = tuple(float(x) for x in info["axis_point_global_xyz_mm"])
    own_offset = sub(cylinder_origin, axis_center)
    own_perp = sub(own_offset, tuple(dot(own_offset, bolt_axis) * x for x in bolt_axis))
    distance = norm(own_perp)
    if distance <= 2.0e-4:
        return "own_bolt_bore_wall", None, distance
    for other_id, other_center in other_axis_centers.items():
        delta = sub(cylinder_origin, other_center)
        perp = sub(delta, tuple(dot(delta, bolt_axis) * x for x in bolt_axis))
        other_distance = norm(perp)
        if other_distance <= 2.0e-4:
            return "neighbor_BG045_bolt_bore_wall", other_id, other_distance
    return "other_parallel_cylindrical_cut", None, distance


def exact_ray_hits(
    shape: cq.Shape,
    point: tuple[float, float, float],
    direction: tuple[float, float, float],
    axis_id: str,
    bolt_axis: tuple[float, float, float],
    centerlines: dict[str, tuple[float, float, float]],
) -> list[dict[str, Any]]:
    """Use finite BRep trimmed-face intersections; preserve bore/cut hits."""
    line = gce_MakeLin(gp_Pnt(*point), gp_Dir(*direction)).Value()
    iterator = BRepIntCurveSurface_Inter()
    iterator.Init(shape.wrapped, line, RAY_TOL_MM)
    faces = shape.Faces()
    limit = box_ray_limit(shape, point, direction)
    hits: list[dict[str, Any]] = []
    while iterator.More():
        raw_point = iterator.Pnt()
        xyz = (raw_point.X(), raw_point.Y(), raw_point.Z())
        distance = dot(sub(xyz, point), direction)
        raw_face = iterator.Face()
        face_index = next(
            (index for index, face in enumerate(faces, start=1) if face.wrapped.IsSame(raw_face)),
            None,
        )
        if face_index is not None and -RAY_TOL_MM <= distance <= limit + RAY_TOL_MM:
            face = faces[face_index - 1]
            try:
                normal = unit(face.normalAt(cq.Vector(*xyz)).toTuple())
                normal_dot_ray = dot(normal, direction)
            except Exception:
                normal = None
                normal_dot_ray = None
            cylinder = cylindrical_surface(face)
            cylinder_class, neighbor_axis, centerline_offset = cylinder_role(
                cylinder, centerlines[axis_id], bolt_axis, centerlines
            )
            hits.append(
                {
                    "ray_distance_mm": distance,
                    "point_global_xyz_mm": xyz,
                    "face_index_1based": face_index,
                    "surface_type": face.geomType(),
                    "face_area_mm2": float(face.Area()),
                    "face_center_global_xyz_mm": face.Center().toTuple(),
                    "face_bounds_xyz_mm": [
                        face.BoundingBox().xmin,
                        face.BoundingBox().xmax,
                        face.BoundingBox().ymin,
                        face.BoundingBox().ymax,
                        face.BoundingBox().zmin,
                        face.BoundingBox().zmax,
                    ],
                    "normal_at_hit_global": normal,
                    "normal_dot_outward_ray": normal_dot_ray,
                    "cylindrical_surface": cylinder,
                    "cylindrical_surface_role": cylinder_class,
                    "neighbor_axis_id_if_matched": neighbor_axis,
                    "parallel_cylinder_axis_line_offset_mm": centerline_offset,
                }
            )
        iterator.Next()
    hits.sort(key=lambda row: (row["ray_distance_mm"], row["face_index_1based"]))
    return hits


def receiver_old_envelope(member_id: str, geometry: dict[str, Any]) -> dict[str, tuple[float, float]]:
    start = geometry["start_global_xyz_mm"]
    end = geometry["end_global_xyz_mm"]
    if member_id == "base_header":
        return {
            "x": (float(start[0]), float(end[0])),
            "y": (float(start[1]) - float(geometry["width_mm"]) / 2.0,
                  float(start[1]) + float(geometry["width_mm"]) / 2.0),
        }
    return {
        "x": (float(start[0]) - float(geometry["width_mm"]) / 2.0,
              float(start[0]) + float(geometry["width_mm"]) / 2.0),
        "y": (float(start[1]) - float(geometry["depth_mm"]) / 2.0,
              float(start[1]) + float(geometry["depth_mm"]) / 2.0),
    }


def old_rect_distance(point: tuple[float, float, float], direction: tuple[float, float, float], envelope: dict[str, tuple[float, float]]) -> tuple[str, float, float]:
    axis = "x" if abs(direction[0]) > 0.5 else "y"
    idx = 0 if axis == "x" else 1
    sign = 1 if direction[idx] > 0 else -1
    boundary = envelope[axis][1] if sign > 0 else envelope[axis][0]
    label = ("+" if sign > 0 else "-") + axis.upper()
    return label, abs(boundary - point[idx]), boundary


def query_ray(
    shape: cq.Shape,
    member_id: str,
    axis_id: str,
    point: tuple[float, float, float],
    direction: tuple[float, float, float],
    bolt_axis: tuple[float, float, float],
    centerlines: dict[str, tuple[float, float, float]],
    envelope: dict[str, tuple[float, float]],
) -> dict[str, Any]:
    hits = exact_ray_hits(shape, point, direction, axis_id, bolt_axis, centerlines)
    require(hits, f"no exact trimmed STEP face intersections: {axis_id}/{member_id}/{direction}/{point}")
    positive_hits = [row for row in hits if row["ray_distance_mm"] > RAY_TOL_MM]
    require(positive_hits, f"no positive outward BRep hit: {axis_id}/{member_id}/{direction}/{point}")
    external = max(positive_hits, key=lambda row: row["ray_distance_mm"])
    face_index = external["face_index_1based"]
    face = shape.Faces()[face_index - 1]
    surface_type = external["surface_type"]
    normal = external["normal_at_hit_global"]
    normal_aligned = (
        surface_type == "PLANE"
        and normal is not None
        and abs(dot(normal, direction)) >= 1.0 - FACE_NORMAL_TOL
    )
    plane_distance = None
    projection_inside = None
    projection_trim_state = None
    if surface_type == "PLANE" and normal is not None:
        signed_plane_distance = dot(sub(external["point_global_xyz_mm"], point), normal)
        plane_distance = abs(signed_plane_distance)
        projected = tuple(point[i] + signed_plane_distance * normal[i] for i in range(3))
        classifier = BRepClass_FaceClassifier(face.wrapped, gp_Pnt(*projected), 1.0e-5)
        trim_state = classifier.State()
        projection_trim_state = str(trim_state)
        projection_inside = trim_state in (TopAbs_IN, TopAbs_ON)
    edge_face, rectangle_distance, rectangle_coordinate = old_rect_distance(point, direction, envelope)
    coordinate_index = 0 if edge_face.endswith("X") else 1
    observed_coordinate = float(external["point_global_xyz_mm"][coordinate_index])
    profile_perpendicular_distance = plane_distance if normal_aligned and projection_inside is True else None
    delta = None if profile_perpendicular_distance is None else profile_perpendicular_distance - rectangle_distance
    cuts = [row for row in positive_hits if row["ray_distance_mm"] < external["ray_distance_mm"] - 1.0e-5]
    return {
        "axis_id": axis_id,
        "receiver_member_id": member_id,
        "receiver": MEMBER_LABELS[member_id],
        "station_global_xyz_mm": point,
        "outward_direction": direction,
        "old_rectangular_envelope_face": edge_face,
        "old_rectangular_envelope_distance_mm": rectangle_distance,
        "old_rectangular_envelope_face_coordinate_mm": rectangle_coordinate,
        "finished_profile_last_outward_hit": {
            "face_index_1based": face_index,
            "surface_type": surface_type,
            "point_global_xyz_mm": external["point_global_xyz_mm"],
            "ray_distance_to_last_profile_hit_mm": external["ray_distance_mm"],
            "normal_at_hit_global": normal,
            "normal_dot_outward_ray": external["normal_dot_outward_ray"],
            "perpendicular_plane_distance_mm": plane_distance,
            "perpendicular_projection_inside_trimmed_face": projection_inside,
            "perpendicular_projection_trim_classifier_state": projection_trim_state,
            "profile_face_has_orthogonal_loaded_edge_normal": normal_aligned,
            "profile_perpendicular_distance_comparable_to_rectangular_edge_mm": profile_perpendicular_distance,
            "profile_minus_old_rectangle_mm": delta,
            "face_bounds_xyz_mm": external["face_bounds_xyz_mm"],
        },
        "modeled_cylindrical_bore_and_cut_intersections_before_external_profile": cuts,
        "all_positive_trimmed_face_intersections_in_order": positive_hits,
    }


def source_bindings() -> tuple[dict[str, Any], dict[str, str]]:
    pins = read_json(PINS_PATH)
    require(pins.get("schema") == "current_bg045_finished_profile_edge_source_pins/v1", "source pin schema")
    observed: dict[str, str] = {}
    direct_paths = []
    for category in ("prior_applicability_packet", "current_finished_geometry", "reviewed_profile_query_precedent"):
        direct_paths.extend(item for item in pins[category].values())
    for item in direct_paths:
        path = ROOT / item["path"]
        require(path.is_file(), f"pinned source missing: {item['path']}")
        actual = sha256(path)
        require(actual == item["sha256"], f"pinned source hash mismatch: {item['path']}")
        observed[item["path"]] = actual

    prior_pins = read_json(ROOT / pins["prior_applicability_packet"]["source_pins"]["path"])
    require(prior_pins.get("schema") == "current_bg045_edge_splitting_applicability_source_pins/v1",
            "prior edge-applicability source pin schema changed")
    for relative, expected in prior_pins["input_files"].items():
        path = ROOT / relative
        require(path.is_file(), f"prior pinned input missing: {relative}")
        actual = sha256(path)
        require(actual == expected, f"prior pinned input hash changed: {relative}")
        observed[relative] = actual

    prior_results = read_json(ROOT / pins["prior_applicability_packet"]["results"]["path"])
    require(prior_results["status"] == "CONDITIONAL_EDGE_AND_GEOMETRY_DISPOSITION_COMPLETE_SPLITTING_CAPACITY_UNRESOLVED",
            "prior applicability disposition status changed")
    require(prior_results["checks"]["reviewed_92_axis_geometry_modified"] is False
            and prior_results["checks"]["native_run"] is False,
            "prior geometry/no-native boundary changed")

    manifest = read_json(ROOT / pins["current_finished_geometry"]["attempt04_manifest"]["path"])
    bundle = read_json(ROOT / pins["current_finished_geometry"]["member_bundle_manifest"]["path"])
    require(bundle["artifact_sha256"] == manifest["existing_step_export_evidence"]["artifact_sha256"],
            "attempt04 STEP bundle identity differs from manifest")
    return {"pins": prior_pins, "prior_results": prior_results, "manifest": manifest, "bundle": bundle}, observed


def build() -> dict[str, Any]:
    sources, observed = source_bindings()
    prior_pins = sources["pins"]
    prior_results = sources["prior_results"]
    manifest = sources["manifest"]
    bundle = sources["bundle"]

    target_axes = {
        row["axis_id"]: row
        for row in manifest["candidate_bolt_axes"]
        if row["axis_id"] in TARGET_AXES
    }
    require(set(target_axes) == set(TARGET_AXES), "both BG045 left header axes must exist in current manifest")
    manifest_members = {row["member_id"]: row for row in manifest["finished_member_step_bindings"]}
    bundle_members = {row["member_id"]: row for row in bundle["members"]}
    # Three accepted source models were cross-checked by the prior packet. Bind
    # their receiver STEP descriptors here to the current manifest and BReps.
    geom_by_case = prior_results["source_geometry"]["receiver_geometry_by_case"]
    reference_case = "a12-rear"
    require(set(geom_by_case) == {"a1-rear", "a12-rear", "k12-rear"},
            "prior three-case receiver geometry case inventory changed")
    source_receiver_geometry: dict[str, dict[str, Any]] = {}
    geometry_keys = {
        "base_header": "base_header",
        "knee_outer_left_inner_frame_block": "block",
    }
    for member_id in TARGET_MEMBERS:
        geometry_key = geometry_keys[member_id]
        expected_case_geom = geom_by_case[reference_case][geometry_key]
        source_receiver_geometry[member_id] = expected_case_geom
        for case_id, case_geometry in geom_by_case.items():
            for field in (
                "grain_global_xyz",
                "axis_global_xyz",
                "start_global_xyz_mm",
                "end_global_xyz_mm",
                "length_mm",
                "depth_mm",
                "width_mm",
                "step_path",
                "step_sha256",
            ):
                require(case_geometry[geometry_key][field] == expected_case_geom[field],
                        f"three accepted models disagree at {case_id}/{member_id}/{field}")
        binding = manifest_members[member_id]
        bundle_row = bundle_members[member_id]
        expected_step = Path(expected_case_geom["step_path"])
        step_path = ROOT / expected_step
        expected_sha = expected_case_geom["step_sha256"]
        require(binding["path"] == expected_case_geom["step_path"],
                f"prior source model/current finished STEP path mismatch: {member_id}")
        require(binding["file_sha256"] == expected_sha == sha256(step_path),
                f"prior source model/current finished STEP SHA mismatch: {member_id}")
        require(bundle_row["step_sha256"] == expected_sha and bundle_row["bounds_and_volume_match_current_manifest"] is True,
                f"current STEP bundle identity/status mismatch: {member_id}")
        require(binding["one_solid_valid_roundtrip"] is True and binding["source_bounds_and_volume_match"] is True,
                f"current finished STEP round-trip validation absent: {member_id}")
        observed[expected_step.as_posix()] = expected_sha

    shapes: dict[str, cq.Shape] = {}
    for member_id in TARGET_MEMBERS:
        step_path = ROOT / manifest_members[member_id]["path"]
        shape = cq.importers.importStep(str(step_path)).val()
        require(shape.isValid() and len(shape.Solids()) == 1,
                f"finished member STEP is not one valid solid: {member_id}")
        shapes[member_id] = shape

    axes = {}
    centerlines = {}
    for axis_id in TARGET_AXES:
        row = target_axes[axis_id]
        geom = row["geometry"]
        axis = unit(geom["axis_head_to_nut_global"])
        center = tuple(float(x) for x in geom["shaft_center_global_xyz_mm"])
        require(abs(abs(axis[2]) - 1.0) <= FACE_NORMAL_TOL and abs(axis[0]) <= FACE_NORMAL_TOL and abs(axis[1]) <= FACE_NORMAL_TOL,
                f"BG045 model axis is no longer vertical: {axis_id}")
        require(abs(center[0] + 1085.85) <= PROFILE_MATCH_TOL_MM,
                f"BG045 bolt centerline X station changed: {axis_id}")
        require(abs(float(geom["modeled_shaft_diameter_mm"]) - D_MM) <= 2.0e-6,
                f"conditional modeled D=6.35 mm source changed: {axis_id}")
        require({r["receiver_id"] for r in geom["wood_receiver_intervals"]} == set(TARGET_MEMBERS),
                f"BG045 receiver pair changed: {axis_id}")
        axis_row = {
            "axis_id": axis_id,
            "axis_global": axis,
            "shaft_center_global_xyz_mm": center,
            "modeled_underhead_to_tip_mm": float(geom["modeled_underhead_to_tip_mm"]),
            "modeled_shaft_diameter_mm": float(geom["modeled_shaft_diameter_mm"]),
            "wood_receiver_intervals": {},
        }
        for rec in geom["wood_receiver_intervals"]:
            member_id = rec["receiver_id"]
            intervals = rec["current_shaft_intersection_solid_intervals_from_underhead_mm"]
            require(rec["current_shaft_covers_all_raw_receiver_intervals"] is True
                    if "current_shaft_covers_all_raw_receiver_intervals" in rec
                    else rec.get("current_shaft_covers_long_axis_raw_receiver_projection") is True,
                    f"modeled shaft does not cover receiver axis interval: {axis_id}/{member_id}")
            require(len(intervals) == 1 and len(intervals[0]) == 2,
                    f"expected one contiguous receiver interval: {axis_id}/{member_id}")
            lo, hi = map(float, intervals[0])
            require(hi > lo, f"nonpositive receiver interval: {axis_id}/{member_id}")
            underhead = tuple(center[i] - axis[i] * axis_row["modeled_underhead_to_tip_mm"] / 2.0 for i in range(3))
            endpoint_a = add_scaled(underhead, axis, lo)
            endpoint_b = add_scaled(underhead, axis, hi)
            z_span = tuple(sorted((endpoint_a[2], endpoint_b[2])))
            require(abs((z_span[1] - z_span[0]) - float(rec["receiver_wood_axis_length_mm"])) <= PROFILE_MATCH_TOL_MM,
                    f"manifest receiver interval length mismatch: {axis_id}/{member_id}")
            axis_row["wood_receiver_intervals"][member_id] = {
                "interval_from_underhead_mm": [lo, hi],
                "receiver_wood_axis_length_mm": float(rec["receiver_wood_axis_length_mm"]),
                "endpoint_a_global_xyz_mm": endpoint_a,
                "endpoint_b_global_xyz_mm": endpoint_b,
                "z_span_global_mm": z_span,
                "interval_gap_from_next_receiver_mm": rec["intersection_projection_gaps_mm"],
            }
        require(abs(axis_row["wood_receiver_intervals"]["base_header"]["z_span_global_mm"][0]
                    - axis_row["wood_receiver_intervals"]["knee_outer_left_inner_frame_block"]["z_span_global_mm"][1]) <= PROFILE_MATCH_TOL_MM
                or abs(axis_row["wood_receiver_intervals"]["base_header"]["z_span_global_mm"][1]
                       - axis_row["wood_receiver_intervals"]["knee_outer_left_inner_frame_block"]["z_span_global_mm"][0]) <= PROFILE_MATCH_TOL_MM,
                f"header/block source intervals are not adjacent at the interface: {axis_id}")
        axes[axis_id] = axis_row
        centerlines[axis_id] = center

    # Confirm centerline X/Y stations against the accepted factor-one signed
    # actions at the header/block interface, preserving axis reversal.
    factor_one = {
        (case["case_id"], row["axis_id"]): row
        for case in prior_results["accepted_signed_actions_full_factor_one"]
        for row in case["axis_actions"]
    }
    require(len(factor_one) == 6, "prior report does not contain six factor-one BG045 bolts")
    for axis_id in TARGET_AXES:
        for case_id in ("a1-rear", "a12-rear", "k12-rear"):
            point = factor_one[(case_id, axis_id)]["point_global_xyz_mm"]
            center = axes[axis_id]["shaft_center_global_xyz_mm"]
            require(abs(float(point[0]) - center[0]) <= PROFILE_MATCH_TOL_MM
                    and abs(float(point[1]) - center[1]) <= PROFILE_MATCH_TOL_MM,
                    f"accepted force station and finished profile centerline disagree: {case_id}/{axis_id}")

    envelopes = {}
    for member_id in TARGET_MEMBERS:
        env = receiver_old_envelope(member_id, source_receiver_geometry[member_id])
        old_env_from_packet = prior_results["source_geometry"]
        if member_id == "base_header":
            packet_y = old_env_from_packet["header_source_envelope_Y_mm"]
        else:
            packet_y = old_env_from_packet["block_source_envelope_Y_mm"]
        require(abs(env["y"][0] - float(packet_y[0])) <= PROFILE_MATCH_TOL_MM
                and abs(env["y"][1] - float(packet_y[1])) <= PROFILE_MATCH_TOL_MM,
                f"reconstructed rectangle Y envelope differs from attempt02: {member_id}")
        if member_id == "knee_outer_left_inner_frame_block":
            packet_x = old_env_from_packet["block_source_envelope_X_mm"]
            require(abs(env["x"][0] - float(packet_x[0])) <= PROFILE_MATCH_TOL_MM
                    and abs(env["x"][1] - float(packet_x[1])) <= PROFILE_MATCH_TOL_MM,
                    "reconstructed block rectangle X envelope differs from attempt02")
        envelopes[member_id] = env

    direction_rows = {
        "+X": (1.0, 0.0, 0.0),
        "-X": (-1.0, 0.0, 0.0),
        "+Y": (0.0, 1.0, 0.0),
        "-Y": (0.0, -1.0, 0.0),
    }
    ray_rows: list[dict[str, Any]] = []
    interval_rows = []
    for axis_id in TARGET_AXES:
        axis_row = axes[axis_id]
        center = axis_row["shaft_center_global_xyz_mm"]
        axis = axis_row["axis_global"]
        other_centers = {other_id: other_center for other_id, other_center in centerlines.items() if other_id != axis_id}
        for member_id in TARGET_MEMBERS:
            span = axis_row["wood_receiver_intervals"][member_id]["z_span_global_mm"]
            z0, z1 = span
            length = z1 - z0
            require(length > 2.0 * SPAN_END_INSET_MM, f"receiver too short for inset ray stations: {axis_id}/{member_id}")
            station_offsets = [
                SPAN_END_INSET_MM,
                0.25 * length,
                0.50 * length,
                0.75 * length,
                length - SPAN_END_INSET_MM,
            ]
            station_z = [z0 + offset for offset in station_offsets]
            interval_rows.append(
                {
                    "axis_id": axis_id,
                    "receiver_member_id": member_id,
                    "receiver_z_span_global_mm": [z0, z1],
                    "receiver_wood_axis_length_mm": length,
                    "sample_z_global_mm": station_z,
                    "sample_offset_from_receiver_low_z_mm": station_offsets,
                    "continuous_span_profile_extremum_proven": False,
                }
            )
            for station_index, z in enumerate(station_z, start=1):
                point = (center[0], center[1], z)
                for direction_name, direction in direction_rows.items():
                    result = query_ray(
                        shapes[member_id],
                        member_id,
                        axis_id,
                        point,
                        direction,
                        axis,
                        centerlines,
                        envelopes[member_id],
                    )
                    result["direction_name"] = direction_name
                    result["station_index_1based"] = station_index
                    ray_rows.append(result)

    require(len(ray_rows) == 80, f"expected 80 exact finite-face rays, got {len(ray_rows)}")
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in ray_rows:
        key = (row["axis_id"], row["receiver_member_id"], row["direction_name"])
        groups.setdefault(key, []).append(row)
    profile_summary = []
    for (axis_id, member_id, direction_name), rows in sorted(groups.items()):
        distances = [
            row["finished_profile_last_outward_hit"]["profile_perpendicular_distance_comparable_to_rectangular_edge_mm"]
            for row in rows
        ]
        rectangle_values = {round(float(row["old_rectangular_envelope_distance_mm"]), 9) for row in rows}
        face_ids = sorted({row["finished_profile_last_outward_hit"]["face_index_1based"] for row in rows})
        face_types = sorted({row["finished_profile_last_outward_hit"]["surface_type"] for row in rows})
        profile_values = [float(value) for value in distances if value is not None]
        internal_counts = Counter(
            hit["cylindrical_surface_role"]
            for row in rows
            for hit in row["modeled_cylindrical_bore_and_cut_intersections_before_external_profile"]
            if hit["surface_type"] == "CYLINDER"
        )
        profile_summary.append(
            {
                "axis_id": axis_id,
                "receiver_member_id": member_id,
                "receiver": MEMBER_LABELS[member_id],
                "direction": direction_name,
                "old_rectangular_envelope_distance_mm": next(iter(rectangle_values)) if len(rectangle_values) == 1 else None,
                "finished_profile_perpendicular_distance_range_mm": [min(profile_values), max(profile_values)] if profile_values else None,
                "finished_minus_rectangle_range_mm": [
                    min(profile_values) - next(iter(rectangle_values)),
                    max(profile_values) - next(iter(rectangle_values)),
                ] if profile_values and len(rectangle_values) == 1 else None,
                "profile_face_indices_across_five_stations": face_ids,
                "profile_surface_types_across_five_stations": face_types,
                "same_trimmed_face_at_all_five_stations": len(face_ids) == 1,
                "all_profile_normals_orthogonal_to_ray": all(
                    row["finished_profile_last_outward_hit"]["profile_face_has_orthogonal_loaded_edge_normal"]
                    for row in rows
                ),
                "intermediate_cylindrical_cut_hit_counts": dict(sorted(internal_counts.items())),
            }
        )

    block_minus_y = [
        row for row in profile_summary
        if row["receiver_member_id"] == "knee_outer_left_inner_frame_block"
        and row["direction"] == "-Y"
    ]
    require(len(block_minus_y) == 2, "expected both block bolt-axis minus-Y edge summaries")
    edge2 = next(row for row in block_minus_y if row["axis_id"] == "knee_outer_left_inner_header_2")

    # Basic independent geometric oracles: own-bore wall radius, face-ray
    # agreement with the old orthogonal rectangular distances, and paired
    # opposite-face closure for each member/axis at each sampled station.
    oracles = {
        "source_axes_and_receivers_match_prior_accepted_packet": True,
        "all_80_rays_hit_finite_trimmed_faces": all(bool(row["all_positive_trimmed_face_intersections_in_order"]) for row in ray_rows),
        "own_bore_radius_3_75_mm_hits_seen_at_each_centerline_ray": True,
        "all_80_centerline_projections_inside_selected_trimmed_outer_face": all(
            row["finished_profile_last_outward_hit"]["perpendicular_projection_inside_trimmed_face"] is True
            for row in ray_rows
        ),
        "planar_orthogonal_profile_matches_old_rectangle_at_every_sample": all(
            row["finished_profile_last_outward_hit"]["profile_minus_old_rectangle_mm"] is not None
            and abs(row["finished_profile_last_outward_hit"]["profile_minus_old_rectangle_mm"]) <= PROFILE_MATCH_TOL_MM
            for row in ray_rows
        ),
        "opposite_rectangle_face_distance_closure_mm": {},
    }
    for axis_id in TARGET_AXES:
        for member_id in TARGET_MEMBERS:
            for station_index in range(1, 6):
                pair = {
                    row["direction_name"]: row
                    for row in ray_rows
                    if row["axis_id"] == axis_id and row["receiver_member_id"] == member_id and row["station_index_1based"] == station_index
                }
                for dim, plus, minus in (("x", "+X", "-X"), ("y", "+Y", "-Y")):
                    rectangle_span = envelopes[member_id][dim][1] - envelopes[member_id][dim][0]
                    plus_profile = pair[plus]["finished_profile_last_outward_hit"]["profile_perpendicular_distance_comparable_to_rectangular_edge_mm"]
                    minus_profile = pair[minus]["finished_profile_last_outward_hit"]["profile_perpendicular_distance_comparable_to_rectangular_edge_mm"]
                    closure = None if plus_profile is None or minus_profile is None else plus_profile + minus_profile - rectangle_span
                    label = f"{axis_id}/{member_id}/station{station_index}/{dim}"
                    oracles["opposite_rectangle_face_distance_closure_mm"][label] = closure
    closure_values = [v for v in oracles["opposite_rectangle_face_distance_closure_mm"].values() if v is not None]
    oracles["all_profile_opposite_face_pairs_close_to_source_section_width"] = (
        len(closure_values) == len(oracles["opposite_rectangle_face_distance_closure_mm"])
        and max((abs(x) for x in closure_values), default=math.inf) <= PROFILE_MATCH_TOL_MM
    )
    for row in ray_rows:
        own_wall = [
            hit for hit in row["all_positive_trimmed_face_intersections_in_order"]
            if hit["cylindrical_surface_role"] == "own_bolt_bore_wall"
        ]
        require(own_wall, f"own bore wall missing from centerline ray: {row['axis_id']}/{row['receiver_member_id']}/{row['direction_name']}/{row['station_index_1based']}")
        require(all(abs(float(hit["cylindrical_surface"]["radius_mm"]) - BORE_RADIUS_MM_EXPECTED) <= 2.0e-5 for hit in own_wall),
                f"source STEP own bolt bore radius differs from 3.75 mm: {row['axis_id']}/{row['receiver_member_id']}")
    require(oracles["all_profile_opposite_face_pairs_close_to_source_section_width"],
            "finished profile opposite-face closure did not reproduce source section widths")

    observed[str(PINS_PATH.relative_to(ROOT))] = sha256(PINS_PATH)
    observed[str(Path(__file__).resolve().relative_to(ROOT))] = sha256(Path(__file__).resolve())
    minimum_clearance_sensitivity = D_MM / 2.0
    return clean(
        {
            "schema": "current_bg045_finished_profile_edge_query/v1",
            "status": "PASS_SOURCE_BOUND_FINISHED_PROFILE_EDGE_STATIONS_ONLY",
            "candidate": "compact-floor-flush-wood-joints-development",
            "geometry_revision_id": manifest["geometry_revision_id"],
            "runtime": {"cadquery_version": cq.__version__, "units": "mm"},
            "source_sha256_observed": dict(sorted(observed.items())),
            "scope": {
                "group": "BG045",
                "axis_ids": list(TARGET_AXES),
                "receiver_members": list(TARGET_MEMBERS),
                "directional_profile_rays": len(ray_rows),
                "stations_per_bolt_receiver_span": 5,
                "receiver_spans_are_source_manifest_shaft_intersections": True,
                "actual_stock_inspected": False,
                "geometry_modified": False,
                "native_solve_or_mesh": False,
            "nds_loaded_edge_assignment_redecided": False,
            },
            "conditional_scenario": {
                "modeled_bolt_diameter_mm": D_MM,
                "named_4D_comparator_mm": 4.0 * D_MM,
                "modeled_wood_bolt_bore_radius_mm": BORE_RADIUS_MM_EXPECTED,
                "modeled_bore_to_shaft_radial_clearance_mm": BORE_RADIUS_MM_EXPECTED - minimum_clearance_sensitivity,
                "interpretation": "geometry scenario from the accepted conditional 6.35 mm model; not delivered hardware or an inspected bore",
            },
            "source_geometry": {
                "bolt_receiver_axis_rows": [axes[axis_id] for axis_id in TARGET_AXES],
                "receiver_source_descriptors": source_receiver_geometry,
                "old_rectangular_envelopes_global_mm": {
                    member_id: {dim: list(span) for dim, span in envelopes[member_id].items()}
                    for member_id in TARGET_MEMBERS
                },
            },
            "profile_query_method": {
                "method_precedent": "reviewed current-knee-finished-profile-attempt01 finite trimmed-face ray query using BRepIntCurveSurface_Inter",
                "station_rule": "five centerline z stations per actual receiver interval: 0.01 mm inset from each end plus 1/4, 1/2 and 3/4 span",
                "face_query": "all positive intersections with finite trimmed STEP faces are retained; the greatest ray parameter is the outward external profile hit; intermediate cylinders/cuts are retained and excluded from the external-edge choice",
                "own_bore_identification": "BRep cylinder surface axis line coincident with the source bolt centerline; own bore is recorded as an intermediate hit, never as the external timber edge",
                "perpendicular_edge_measurement": "where the last outward face is planar, its normal is ray-aligned, and the centerline projection lies inside the trimmed face, distance is the plane-normal distance; otherwise only the ray distance is reported",
                "span_coverage_limit": "sampled stations bind exact trimmed face hits but do not optimize a continuous minimum over the full receiver span",
            },
            "summary": {
                "all_profile_direction_samples_match_old_rectangle": oracles["planar_orthogonal_profile_matches_old_rectangle_at_every_sample"],
                "maximum_absolute_profile_minus_old_rectangle_mm": max(
                    abs(float(row["finished_profile_last_outward_hit"]["profile_minus_old_rectangle_mm"]))
                    for row in ray_rows
                    if row["finished_profile_last_outward_hit"]["profile_minus_old_rectangle_mm"] is not None
                ),
                "BG045_block_axis_2_minus_Y_finished_distance_range_mm": edge2["finished_profile_perpendicular_distance_range_mm"],
                "BG045_block_axis_2_minus_Y_old_rectangular_distance_mm": edge2["old_rectangular_envelope_distance_mm"],
                "BG045_block_axis_2_minus_Y_finished_minus_old_mm": edge2["finished_minus_rectangle_range_mm"],
                "BG045_block_axis_2_minus_Y_conditional_4D_deficit_mm": [
                    4.0 * D_MM - float(edge2["finished_profile_perpendicular_distance_range_mm"][1]),
                    4.0 * D_MM - float(edge2["finished_profile_perpendicular_distance_range_mm"][0]),
                ] if edge2["finished_profile_perpendicular_distance_range_mm"] else None,
                "external_trimmed_face_identity_stable_per_direction": all(
                    row["same_trimmed_face_at_all_five_stations"] for row in profile_summary
                ),
                "all_external_faces_are_orthogonal_planes": all(
                    row["all_profile_normals_orthogonal_to_ray"] for row in profile_summary
                ),
                "intermediate_cut_face_hit_count": sum(
                    len(row["modeled_cylindrical_bore_and_cut_intersections_before_external_profile"])
                    for row in ray_rows
                ),
            },
            "oracles": oracles,
            "receiver_span_samples": interval_rows,
            "profile_distance_summary": profile_summary,
            "ray_station_hits": ray_rows,
            "limits": [
                "This is exact model BRep geometry for only the two BG045 left header axes and their header/block receiver spans; it does not inspect as-built stock, actual grain, tolerance, or received bolt size.",
                "The 6.35 mm axis diameter and 3.75 mm bore radius are modeled conditional geometry inputs; actual hole clearance and installed bolt center remain unverified.",
                "Ray endpoints were sampled at five stations per source receiver span; no continuous span extremum is proven. Intermediate own/neighbor/transverse holes and cuts are enumerated but no net-section, shear-out, tear-out, splitting, or group resistance is computed.",
                "The profile comparison reports geometric distances only. It does not decide whether a given face is the NDS required loaded edge for the signed, oblique block action or the mixed-grain header action.",
                "No NDS acceptance, capacity, axis proposal, geometry change, physical inspection, native run, or mesh is established.",
            ],
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"WROTE {OUTPUT.relative_to(ROOT)} sha256={sha256(OUTPUT)}")
        return
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
        raise SystemExit("FAIL profile-edge-query.json differs; rerun this isolated query with --write")
    result = read_json(OUTPUT)
    summary = result["summary"]
    print(
        "PASS BG045 two-axis finished-profile station query; "
        f"block axis-2 -Y {summary['BG045_block_axis_2_minus_Y_finished_distance_range_mm']} mm; "
        f"max profile/envelope delta {summary['maximum_absolute_profile_minus_old_rectangle_mm']:.9f} mm"
    )


if __name__ == "__main__":
    main()
