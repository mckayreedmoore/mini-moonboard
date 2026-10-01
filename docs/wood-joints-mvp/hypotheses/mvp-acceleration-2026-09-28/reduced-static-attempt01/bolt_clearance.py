#!/usr/bin/env python3
"""Measure current candidate bolt-to-bore radial gaps from pinned STEP faces."""

from __future__ import annotations

import hashlib
import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import cadquery as cq
from OCP.BRepTools import BRepTools


ROOT = Path(__file__).resolve().parents[5]
MANIFEST_REL = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
MANIFEST_SHA256 = "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11"
OUTPUT = Path(__file__).with_name("bolt-clearance.json")

AXIS_ANGLE_TOLERANCE_DEG = 1e-5
AXIS_LINE_OFFSET_TOLERANCE_MM = 1e-5
RADIUS_CLUSTER_TOLERANCE_MM = 1e-6


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def norm(vector: list[float]) -> float:
    return math.sqrt(dot(vector, vector))


def unit(vector: list[float]) -> list[float]:
    magnitude = norm(vector)
    if magnitude <= 0 or not math.isfinite(magnitude):
        raise ValueError("Cannot normalize an invalid geometry direction.")
    return [value / magnitude for value in vector]


def angle_deg(a: list[float], b: list[float]) -> float:
    cosine = min(1.0, max(0.0, abs(dot(unit(a), unit(b)))))
    return math.degrees(math.acos(cosine))


def line_offset_mm(point_a: list[float], direction: list[float], point_b: list[float]) -> float:
    displacement = [point_b[i] - point_a[i] for i in range(3)]
    along = dot(displacement, direction)
    residual = [displacement[i] - along * direction[i] for i in range(3)]
    return norm(residual)


def axial_span(face_data: dict[str, Any], shaft_center: list[float], bolt_axis: list[float]) -> dict[str, Any]:
    v_low, v_high = face_data["v_parameter_bounds_mm"]
    cylinder_direction = face_data["cylinder_axis_unit_global_xyz"]
    cylinder_origin = face_data["cylinder_axis_location_global_xyz_mm"]
    endpoints = []
    for v_value in (v_low, v_high):
        point = [cylinder_origin[i] + cylinder_direction[i] * v_value for i in range(3)]
        endpoints.append(dot([point[i] - shaft_center[i] for i in range(3)], bolt_axis))
    lower, upper = sorted(endpoints)
    return {
        "range_along_source_bolt_axis_from_shaft_center_mm": [lower, upper],
        "axial_span_length_mm": upper - lower,
    }


def radius_clusters(face_records: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    clusters: list[list[dict[str, Any]]] = []
    for face in sorted(face_records, key=lambda record: record["radius_mm"]):
        if not clusters or face["radius_mm"] - clusters[-1][0]["radius_mm"] > RADIUS_CLUSTER_TOLERANCE_MM:
            clusters.append([face])
        else:
            clusters[-1].append(face)
    return clusters


def cylinder_faces(shape: cq.Shape) -> list[dict[str, Any]]:
    records = []
    for face_index, face in enumerate(shape.Faces()):
        if face.geomType() != "CYLINDER":
            continue
        cylinder = face._geomAdaptor().Cylinder()
        axis = cylinder.Axis()
        location = axis.Location()
        direction = axis.Direction()
        u0, u1, v0, v1 = BRepTools.UVBounds_s(face.wrapped)
        values = [cylinder.Radius(), u0, u1, v0, v1]
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"STEP cylinder face {face_index} has non-finite bounds or radius.")
        records.append({
            "face_index": face_index,
            "radius_mm": float(cylinder.Radius()),
            "cylinder_axis_location_global_xyz_mm": [location.X(), location.Y(), location.Z()],
            "cylinder_axis_unit_global_xyz": unit([direction.X(), direction.Y(), direction.Z()]),
            "u_parameter_bounds_rad": [float(u0), float(u1)],
            "v_parameter_bounds_mm": [float(v0), float(v1)],
        })
    return records


def validate_and_load_receivers(
    manifest: dict[str, Any],
    bindings: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, str]]:
    source_records = []
    verified_hashes: dict[str, str] = {}
    for member_id, binding in sorted(bindings.items()):
        step_path = ROOT / binding["path"]
        if not step_path.is_file():
            raise ValueError(f"Missing pinned STEP file for {member_id}: {binding['path']}")
        actual_hash = sha256(step_path)
        if actual_hash != binding["file_sha256"]:
            raise ValueError(f"STEP SHA-256 mismatch for {member_id}: {binding['path']}")
        if step_path.stat().st_size != binding["size_bytes"]:
            raise ValueError(f"STEP size mismatch for {member_id}: {binding['path']}")
        if not binding["one_solid_valid_roundtrip"] or not binding["source_bounds_and_volume_match"]:
            raise ValueError(f"Manifest round-trip evidence incomplete for {member_id}.")
        verified_hashes[binding["path"]] = actual_hash
        source_records.append({
            "member_id": member_id,
            "member_kind": binding["member_kind"],
            "step_path": binding["path"],
            "sha256": actual_hash,
            "size_bytes": binding["size_bytes"],
        })

    receiver_ids = sorted({receiver for axis in manifest["candidate_bolt_axes"] for receiver in axis["receiver_member_ids"]})
    shapes: dict[str, list[dict[str, Any]]] = {}
    for receiver_id in receiver_ids:
        binding = bindings.get(receiver_id)
        if binding is None:
            raise ValueError(f"Candidate receiver is absent from the finished STEP manifest: {receiver_id}")
        step_shape = cq.importers.importStep(str(ROOT / binding["path"])).val()
        solids = step_shape.Solids()
        if len(solids) != 1 or not solids[0].isValid():
            raise ValueError(f"Expected one valid finished STEP solid for receiver {receiver_id}.")
        shapes[receiver_id] = cylinder_faces(solids[0])
    return shapes, source_records, verified_hashes


def receiver_interval_record(axis: dict[str, Any], receiver_id: str) -> dict[str, Any] | None:
    matches = [row for row in axis["geometry"]["wood_receiver_intervals"] if row["receiver_id"] == receiver_id]
    if len(matches) != 1:
        return None
    source = matches[0]
    return {
        "source_intersection_solid_intervals_from_underhead_mm": source.get(
            "current_shaft_intersection_solid_intervals_from_underhead_mm"
        ),
        "source_receiver_axis_length_mm": source.get("receiver_wood_axis_length_mm"),
    }


def measure_receiver(
    axis: dict[str, Any],
    receiver_id: str,
    binding: dict[str, Any],
    face_inventory: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    geometry = axis["geometry"]
    shaft_center = [float(value) for value in geometry["shaft_center_global_xyz_mm"]]
    bolt_axis = unit([float(value) for value in geometry["axis_head_to_nut_global"]])
    shaft_diameter = float(geometry["modeled_shaft_diameter_mm"])
    interval = receiver_interval_record(axis, receiver_id)
    if interval is None:
        return {
            "axis_id": axis["axis_id"],
            "receiver_id": receiver_id,
            "result_status": "exception_receiver_interval_missing_or_duplicated",
            "modeled_shaft_diameter_mm": shaft_diameter,
            "modeled_shaft_center_global_xyz_mm": shaft_center,
            "source_bolt_axis_head_to_nut_unit_global_xyz": bolt_axis,
            "coaxial_cylindrical_finished_faces": [],
            "unique_bore_radius_mm": None,
            "geometry_only_centered_radial_gap_mm": None,
            "exception": "Expected exactly one manifest receiver interval for this axis/member pair.",
        }

    matched = []
    for face in face_inventory[receiver_id]:
        angular_error = angle_deg(bolt_axis, face["cylinder_axis_unit_global_xyz"])
        line_error = line_offset_mm(
            shaft_center,
            bolt_axis,
            face["cylinder_axis_location_global_xyz_mm"],
        )
        face_record = {
            **face,
            "bolt_axis_alignment_abs_dot": abs(dot(bolt_axis, face["cylinder_axis_unit_global_xyz"])),
            "axis_direction_angle_error_deg": angular_error,
            "axis_line_perpendicular_offset_mm": line_error,
            **axial_span(face, shaft_center, bolt_axis),
        }
        if angular_error <= AXIS_ANGLE_TOLERANCE_DEG and line_error <= AXIS_LINE_OFFSET_TOLERANCE_MM:
            matched.append(face_record)

    clusters = radius_clusters(matched)
    result_status = "unique_coaxial_bore_radius" if len(clusters) == 1 else (
        "exception_no_coaxial_cylindrical_finished_face" if not clusters else "exception_multiple_coaxial_bore_radii"
    )
    unique_radius = None
    radial_gap = None
    exception = None
    if len(clusters) == 1:
        unique_radius = sum(row["radius_mm"] for row in clusters[0]) / len(clusters[0])
        radial_gap = (2.0 * unique_radius - shaft_diameter) / 2.0
    elif not clusters:
        exception = "No finished cylindrical face matched both axis angle and perpendicular line-offset tolerances."
    else:
        exception = "Multiple distinct coaxial cylindrical radii matched; no unique centered radial gap was emitted."

    return {
        "axis_id": axis["axis_id"],
        "family": axis.get("family"),
        "trial_id": axis.get("trial_id"),
        "station_id": axis.get("station_id"),
        "receiver_id": receiver_id,
        "receiver_member_kind": binding["member_kind"],
        "receiver_step_path": binding["path"],
        "receiver_step_sha256": binding["file_sha256"],
        "result_status": result_status,
        "modeled_shaft_diameter_mm": shaft_diameter,
        "modeled_shaft_center_global_xyz_mm": shaft_center,
        "source_bolt_axis_head_to_nut_unit_global_xyz": bolt_axis,
        "manifest_receiver_interval": interval,
        "matching_tolerances": {
            "axis_direction_angle_error_max_deg": AXIS_ANGLE_TOLERANCE_DEG,
            "axis_line_perpendicular_offset_max_mm": AXIS_LINE_OFFSET_TOLERANCE_MM,
            "distinct_radius_cluster_tolerance_mm": RADIUS_CLUSTER_TOLERANCE_MM,
        },
        "coaxial_cylindrical_finished_faces": matched,
        "matched_finished_face_count": len(matched),
        "distinct_coaxial_bore_radius_count": len(clusters),
        "unique_bore_radius_mm": unique_radius,
        "modeled_shaft_radius_mm": shaft_diameter / 2.0 if unique_radius is not None else None,
        "centered_radial_gap_formula": "(2*bore_radius_mm-modeled_shaft_diameter_mm)/2",
        "geometry_only_centered_radial_gap_mm": radial_gap,
        "exception": exception,
    }


def build() -> dict[str, Any]:
    manifest_path = ROOT / MANIFEST_REL
    manifest_hash = sha256(manifest_path)
    if manifest_hash != MANIFEST_SHA256:
        raise ValueError(f"Attempt04 manifest SHA-256 mismatch: expected {MANIFEST_SHA256}, got {manifest_hash}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bindings_list = manifest["finished_member_step_bindings"]
    bindings = {row["member_id"]: row for row in bindings_list}
    if (len(bindings_list) != 50 or len(bindings) != 50
            or len({row["path"] for row in bindings_list}) != 50):
        raise ValueError(f"Expected 50 uniquely bound finished STEP members, received {len(bindings_list)}.")
    axes = manifest["candidate_bolt_axes"]
    if len(axes) != 92 or len({row["axis_id"] for row in axes}) != 92:
        raise ValueError("Expected 92 uniquely identified current candidate bolt axes.")

    face_inventory, step_records, verified_hashes = validate_and_load_receivers(manifest, bindings)
    results = []
    for axis in axes:
        receivers = axis["receiver_member_ids"]
        if len(receivers) not in (2, 3):
            raise ValueError(f"Unexpected candidate receiver count for {axis['axis_id']}: {receivers}")
        if len(axis["geometry"]["wood_receiver_intervals"]) != len(receivers):
            raise ValueError(f"Receiver interval count mismatch for {axis['axis_id']}.")
        for receiver_id in receivers:
            results.append(measure_receiver(axis, receiver_id, bindings[receiver_id], face_inventory))
    if len(results) != 188:
        raise ValueError(f"Expected 188 candidate axis/receiver records; generated {len(results)}.")
    expected_pairs = {
        (axis["axis_id"], receiver_id)
        for axis in axes
        for receiver_id in axis["receiver_member_ids"]
    }
    actual_pairs = {(row["axis_id"], row["receiver_id"]) for row in results}
    if len(expected_pairs) != 188 or actual_pairs != expected_pairs or len(actual_pairs) != len(results):
        raise ValueError("The 188 candidate axis/receiver memberships were not conserved exactly once.")

    statuses = Counter(row["result_status"] for row in results)
    radius_counts = Counter(
        f"{row['unique_bore_radius_mm']:.6f}"
        for row in results
        if row["unique_bore_radius_mm"] is not None
    )
    gap_counts = Counter(
        f"{row['geometry_only_centered_radial_gap_mm']:.6f}"
        for row in results
        if row["geometry_only_centered_radial_gap_mm"] is not None
    )
    all_errors = [
        face
        for row in results
        for face in row["coaxial_cylindrical_finished_faces"]
    ]
    payload = {
        "schema": "wood_joint_candidate_bolt_bore_clearance_inventory/v1",
        "status": "source_pinned_finished_step_geometry_only",
        "candidate": manifest.get("candidate"),
        "geometry_revision_id": manifest.get("geometry_revision_id"),
        "input_manifest": {"path": MANIFEST_REL, "sha256": manifest_hash},
        "method": {
            "cadquery_version": cq.__version__,
            "geometry_source": "The 50 finished STEP files and per-file SHA-256 bindings recorded in the pinned attempt04 manifest.",
            "steps": [
                "Hash-check all 50 finished STEP files against their attempt04 manifest bindings.",
                "Import only finished receiver solids used by current candidate axes; do not rebuild CAD.",
                "Select analytic cylindrical faces whose axis direction and perpendicular line offset match each manifest bolt axis within the recorded tolerances.",
                "Read each cylinder face's axial V bounds and project its end stations onto the source bolt axis from the modeled shaft-center point.",
                "If the matched faces have one unique radius within the radius-cluster tolerance, calculate centered radial gap as (2R-modeled shaft diameter)/2.",
            ],
            "matching_tolerances": {
                "axis_direction_angle_error_max_deg": AXIS_ANGLE_TOLERANCE_DEG,
                "axis_line_perpendicular_offset_max_mm": AXIS_LINE_OFFSET_TOLERANCE_MM,
                "distinct_radius_cluster_tolerance_mm": RADIUS_CLUSTER_TOLERANCE_MM,
            },
        },
        "counts": {
            "finished_step_files_sha256_checked": len(step_records),
            "candidate_receiver_solids_imported": len(face_inventory),
            "candidate_axis_count": len(axes),
            "candidate_axis_receiver_count": len(results),
            "candidate_axis_receiver_pairs_unique_and_conserved": True,
            "result_status_counts": dict(sorted(statuses.items())),
            "unique_bore_radius_counts_mm": dict(sorted(radius_counts.items())),
            "geometry_only_centered_radial_gap_counts_mm": dict(sorted(gap_counts.items())),
            "matched_cylindrical_finished_face_count": sum(row["matched_finished_face_count"] for row in results),
            "max_matched_axis_direction_error_deg": max(row["axis_direction_angle_error_deg"] for row in all_errors) if all_errors else None,
            "max_matched_axis_line_offset_mm": max(row["axis_line_perpendicular_offset_mm"] for row in all_errors) if all_errors else None,
            "min_matched_cylindrical_face_axial_span_mm": min(row["axial_span_length_mm"] for row in all_errors) if all_errors else None,
            "max_matched_cylindrical_face_axial_span_mm": max(row["axial_span_length_mm"] for row in all_errors) if all_errors else None,
            "all_axis_receiver_rows_have_unique_radius": all(row["result_status"] == "unique_coaxial_bore_radius" for row in results),
            "all_axis_receiver_rows_have_unique_radius_value": all(row["unique_bore_radius_mm"] is not None for row in results),
        },
        "finished_step_sha256_bindings": step_records,
        "axis_receiver_clearances": results,
        "exceptions": [
            {"axis_id": row["axis_id"], "receiver_id": row["receiver_id"], "result_status": row["result_status"], "exception": row["exception"]}
            for row in results
            if row["exception"] is not None
        ],
        "limits": [
            "These clearances describe analytic surfaces in the current finished CAD STEP solids, not actual as-built holes, received wood, delivered bolt diameter, fit, or installation.",
            "The centered gap is a geometry-only annular clearance from the modeled shaft diameter; no drill-bit size or purchase instruction is inferred.",
            "Matched cylinder radius and axial bounds do not by themselves verify full circumferential or lengthwise bearing engagement, or complete hole topology; those remain connection-mechanics mapping questions.",
            "No spring/contact law, bearing resistance, load, connection demand, NDS check, pass, candidate acceptance, or physical-work authorization is produced.",
        ],
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="Write the regenerated pinned geometry inventory.")
    action.add_argument("--verify", action="store_true", help="Regenerate in memory and compare the existing JSON byte-for-byte.")
    args = parser.parse_args()
    payload = build()
    expected = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if args.write:
        OUTPUT.write_bytes(expected)
        action_word = "wrote"
    else:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            raise SystemExit(f"verification failed: {OUTPUT} is absent or differs from regenerated geometry")
        action_word = "verified"
    counts = payload["counts"]
    print(
        "{} {}: {} candidate axes, {} axis/receiver records, {} exceptions".format(
            action_word,
            OUTPUT,
            counts["candidate_axis_count"],
            counts["candidate_axis_receiver_count"],
            len(payload["exceptions"]),
        )
    )


if __name__ == "__main__":
    main()
