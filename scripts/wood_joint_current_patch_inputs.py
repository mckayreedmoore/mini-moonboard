"""Export one bounded, current-geometry wood-joint patch as immutable STEP inputs.

This adapter only consumes an already composed and revised G24 geometry object.
It does not materialize or change frame geometry, run a mesh or native solve,
or assign contact behavior. The STEP bundle keeps the three finished timber
solids and all twenty source hardware-role solids, then derives four one-solid
head/shaft bolt bodies for physical metal meshing.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint
from scripts import wood_joint_current_grip_screen as current_grip

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24"
INVENTORY_PATH = ROOT / "docs/wood-joints-mvp/source-inventory.json"
REVISION_REPORT_PATH = REPORT_DIR / "revision.json"
VERIFICATION_REPORT_PATH = REPORT_DIR / "verification.json"
SCENE_SNAPSHOT_PATH = REPORT_DIR / "scene.json.snapshot"
CURRENT_GRIP_REPORT_PATH = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json"
CURRENT_GRIP_REPORT_SHA256 = "9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a"

SCHEMA = "wood_joint_current_patch_inputs/v1"
CURRENT_REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
# Supplied by the parent task context; deliberately not inferred from Git.
CURRENT_IMPLEMENTATION_REVISION = "b1e8707d"
SOURCE_BASELINE_COMMIT = "df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb"
REVISION_REPORT_SHA256 = "148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695"
SCENE_SHA256 = "74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf"
VERIFIED_CURRENT_SOURCE_HASHES = {
    "scripts/wood_joint_wj24_led_clearance.py": "4c33379985baaf4dd19b0909abbd1a9f361fd8fe50c5d91260167c74425f35a9",
    "scripts/wood_joint_wj24_2x6_outer_blocks.py": "fb7e49e354f1ffe718c86caeeb588c129088a604498ef465028320defd13540e",
    "scripts/export_wood_joint_design_review_scene.py": "02baedfa61f281854da947cd5787b83d10b1c91161aa05c252ef3960c9cf3537",
}

WOOD_PARTS = (
    "bottom_center_right_cleat",
    "base_rail_bottom_right",
    "base_principal_center_right",
)
CLEAT_ID = "bottom_center_right_cleat"
AXIS_RECEIVERS = {
    "bottom_center/clip_horizontal_bottom_right_1/rail_1": (
        CLEAT_ID,
        "base_rail_bottom_right",
    ),
    "bottom_center/clip_horizontal_bottom_right_1/rail_2": (
        CLEAT_ID,
        "base_rail_bottom_right",
    ),
    "bottom_center/clip_horizontal_bottom_right_1/principal_1": (
        CLEAT_ID,
        "base_principal_center_right",
    ),
    "bottom_center/clip_horizontal_bottom_right_1/principal_2": (
        CLEAT_ID,
        "base_principal_center_right",
    ),
}
WOOD_INTERFACE_PAIRS = (
    (CLEAT_ID, "base_rail_bottom_right"),
    (CLEAT_ID, "base_principal_center_right"),
    ("base_rail_bottom_right", "base_principal_center_right"),
)
HARDWARE_ROLES = ("shaft", "head", "head_washer", "nut_washer", "nut")
PHYSICAL_BOLT_ROLES = ("head", "shaft")

FACE_NORMAL_TOLERANCE = 1e-7
FACE_PLANE_TOLERANCE_MM = 1e-5
FACE_AREA_TOLERANCE_MM2 = 1e-8
AXIAL_CONTIGUITY_TOLERANCE_MM = 0.02
SOLID_VOLUME_REL_TOLERANCE = 1e-8
SOLID_VOLUME_ABS_TOLERANCE_MM3 = 1e-5
SOLID_POSITION_TOLERANCE_MM = 1e-4
SOLID_SYMMETRIC_DIFFERENCE_ABS_TOLERANCE_MM3 = 1e-3
SOLID_SYMMETRIC_DIFFERENCE_REL_TOLERANCE = 1e-9
UNION_VOLUME_ABS_TOLERANCE_MM3 = 1e-5
UNION_VOLUME_REL_TOLERANCE = 1e-8


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_plain(item) for item in value]
    return value


def _finite_vector(value: Any, context: str) -> tuple[float, float, float]:
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{context}: expected a finite 3-vector") from error
    if len(result) != 3 or not all(math.isfinite(component) for component in result):
        raise ValueError(f"{context}: expected a finite 3-vector")
    return result  # type: ignore[return-value]


def _unit(value: Any, context: str) -> tuple[float, float, float]:
    vector = _finite_vector(value, context)
    length = math.sqrt(sum(component * component for component in vector))
    if not math.isfinite(length) or length < 1e-12:
        raise ValueError(f"{context}: expected a nonzero vector")
    return tuple(component / length for component in vector)  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _sub(left: Sequence[float], right: Sequence[float]) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _center_tuple(value: Any, context: str) -> tuple[float, float, float]:
    if hasattr(value, "toTuple"):
        value = value.toTuple()
    return _finite_vector(value, context)


def _vec_json(vector: Sequence[float]) -> list[float]:
    return [round(float(component), 9) for component in vector]


def _box_record(shape: Any, context: str) -> list[float]:
    box = shape.BoundingBox()
    result = [
        float(box.xmin),
        float(box.xmax),
        float(box.ymin),
        float(box.ymax),
        float(box.zmin),
        float(box.zmax),
    ]
    if not all(math.isfinite(value) for value in result):
        raise ValueError(f"{context}: non-finite CAD bounds")
    return [round(value, 9) for value in result]


def _shape_metadata(shape: Any, context: str) -> dict[str, Any]:
    if shape is None or shape.isNull() or not shape.isValid():
        raise ValueError(f"{context}: missing or invalid CAD shape")
    solids = shape.Solids()
    volume = float(shape.Volume())
    if len(solids) != 1 or not math.isfinite(volume) or volume <= 0:
        raise ValueError(f"{context}: expected one positive-volume solid")
    centroid = _center_tuple(shape.Center(), f"{context} centroid")
    return {
        "solid_count": 1,
        "volume_mm3": round(volume, 9),
        "centroid_global_xyz_mm": _vec_json(centroid),
        "bounds_xyz_mm": _box_record(shape, context),
        "cad_shape_sha256": _source_shape_fingerprint(shape),
    }


def _read_current_grip_inputs() -> dict[str, Any]:
    """Read the frozen 92-axis screen and its geometry/scene source bindings."""
    try:
        report_bytes = CURRENT_GRIP_REPORT_PATH.read_bytes()
        report = json.loads(report_bytes)
        snapshot, scene_report = current_grip.load_frozen_inputs()
        snapshot_bytes = current_grip.SNAPSHOT_PATH.read_bytes()
        scene_bytes = current_grip.REPORT_PATH.read_bytes()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("current-grip screen inputs are not verifiable") from error
    report_sha = _sha256_bytes(report_bytes)
    snapshot_sha = _sha256_bytes(snapshot_bytes)
    scene_sha = _sha256_bytes(scene_bytes)
    if report_sha != CURRENT_GRIP_REPORT_SHA256:
        raise ValueError("current-grip attempt02 report differs from its source-bound pin")
    if (
        report.get("schema") != current_grip.SCHEMA
        or report.get("status") != "exact_geometry_projection_screen_only"
        or report.get("revision_id") != CURRENT_REVISION_ID
        or report.get("reviewed_repository_commit") != CURRENT_IMPLEMENTATION_REVISION
        or report.get("candidate_axis_count") != current_grip.EXPECTED_AXIS_COUNT
    ):
        raise ValueError("current-grip report is not the source-bound 92-axis current revision")
    if report.get("geometry_snapshot_path") != str(current_grip.SNAPSHOT_PATH.relative_to(ROOT)):
        raise ValueError("current-grip report references an unexpected geometry snapshot")
    if report.get("geometry_snapshot_sha256") != snapshot_sha:
        raise ValueError("current-grip report geometry snapshot hash differs from its pin")
    if report.get("scene_report_path") != str(current_grip.REPORT_PATH.relative_to(ROOT)):
        raise ValueError("current-grip report references an unexpected scene report")
    if report.get("scene_report_sha256") != scene_sha:
        raise ValueError("current-grip report scene report hash differs from its pin")
    if snapshot.get("revision_id") != CURRENT_REVISION_ID or snapshot.get(
        "reviewed_repository_commit"
    ) != CURRENT_IMPLEMENTATION_REVISION:
        raise ValueError("current-grip geometry snapshot has a different revision binding")
    if snapshot_sha != report.get("geometry_snapshot_sha256"):
        raise ValueError("current-grip geometry snapshot content changed")
    if scene_sha != report.get("scene_report_sha256"):
        raise ValueError("current-grip scene report content changed")
    report_rows = report.get("axes", ())
    axes = {row.get("axis_id"): row for row in report_rows if isinstance(row, Mapping)}
    if len(report_rows) != current_grip.EXPECTED_AXIS_COUNT or len(axes) != len(report_rows):
        raise ValueError("current-grip report does not contain 92 unique axis rows")
    if set(snapshot.get("axes", {})) != set(axes):
        raise ValueError("current-grip report axis set differs from its frozen geometry snapshot")
    pin_record = {
        "report": str(CURRENT_GRIP_REPORT_PATH.relative_to(ROOT)),
        "report_sha256": report_sha,
        "schema": current_grip.SCHEMA,
        "status": report["status"],
        "candidate_axis_count": len(axes),
        "geometry_snapshot": str(current_grip.SNAPSHOT_PATH.relative_to(ROOT)),
        "geometry_snapshot_sha256": snapshot_sha,
        "scene_report": str(current_grip.REPORT_PATH.relative_to(ROOT)),
        "scene_report_sha256": scene_sha,
        "collector_source_sha256": _sha256_file(Path(current_grip.__file__)),
    }
    return {"report": report, "snapshot": snapshot, "scene_report": scene_report, "axes": axes, "pins": pin_record}


def _read_current_pins(current_grip_inputs: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Load and verify the archived current review and its producer hashes."""
    try:
        revision_bytes = REVISION_REPORT_PATH.read_bytes()
        verification = json.loads(VERIFICATION_REPORT_PATH.read_text())
        scene_bytes = SCENE_SNAPSHOT_PATH.read_bytes()
        revision_report = json.loads(revision_bytes)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("current 2x6 runner review archive is incomplete") from error
    revision_sha = _sha256_bytes(revision_bytes)
    scene_sha = _sha256_bytes(scene_bytes)
    if revision_sha != REVISION_REPORT_SHA256:
        raise ValueError("current 2x6 revision report hash differs from its pin")
    if scene_sha != SCENE_SHA256:
        raise ValueError("current 2x6 scene snapshot hash differs from its pin")
    if verification.get("revision_report_sha256") != revision_sha:
        raise ValueError("verification report does not pin the current revision report")
    if verification.get("scene_sha256") != scene_sha:
        raise ValueError("verification report does not pin the current scene")
    if revision_report.get("revision_id") != CURRENT_REVISION_ID:
        raise ValueError("archived revision report is not the selected current geometry")
    source_hashes = verification.get("source_files_sha256")
    if source_hashes != VERIFIED_CURRENT_SOURCE_HASHES:
        raise ValueError("current verification report source hash set differs from its pin")
    for relative_path, expected in VERIFIED_CURRENT_SOURCE_HASHES.items():
        try:
            observed = _sha256_file(ROOT / relative_path)
        except OSError as error:
            raise ValueError(f"pinned current source is unavailable: {relative_path}") from error
        if observed != expected:
            raise ValueError(f"pinned current source hash changed: {relative_path}")
    return {
        "revision_id": CURRENT_REVISION_ID,
        "implementation_revision": CURRENT_IMPLEMENTATION_REVISION,
        "implementation_revision_source": "parent task context; not read from Git",
        "revision_report": str(REVISION_REPORT_PATH.relative_to(ROOT)),
        "revision_report_sha256": revision_sha,
        "verification_report": str(VERIFICATION_REPORT_PATH.relative_to(ROOT)),
        "verification_report_sha256": _sha256_file(VERIFICATION_REPORT_PATH),
        "scene_snapshot": str(SCENE_SNAPSHOT_PATH.relative_to(ROOT)),
        "scene_sha256": scene_sha,
        "source_files_sha256": dict(sorted(source_hashes.items())),
        "input_adapter_source_sha256": _sha256_file(Path(__file__)),
        "current_grip_screen": dict(
            (current_grip_inputs or _read_current_grip_inputs())["pins"]
        ),
        "report_claim_boundary": "current viewer geometry review only; no joint evaluation or acceptance",
    }


def _inventory_rows(inventory: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {
        str(row["part_id"]): dict(row)
        for row in inventory.get("parts", ())
        if isinstance(row, Mapping) and row.get("part_id")
    }
    if len(rows) != len(inventory.get("parts", ())):
        raise ValueError("source inventory part IDs are missing or duplicated")
    return rows


def _shape_vertices(shape: Any, context: str) -> list[tuple[float, float, float]]:
    vertices = list(shape.Vertices())
    if not vertices:
        raise ValueError(f"{context}: finished receiver has no vertices for axial projection")
    return [_center_tuple(vertex.Center(), context) for vertex in vertices]


def _projected_interval(
    shape: Any,
    origin: Sequence[float],
    direction: Sequence[float],
    context: str,
) -> tuple[float, float]:
    stations = [
        _dot(_sub(point, origin), direction)
        for point in _shape_vertices(shape, context)
    ]
    if not all(math.isfinite(value) for value in stations):
        raise ValueError(f"{context}: non-finite receiver projection")
    lower, upper = min(stations), max(stations)
    if upper <= lower:
        raise ValueError(f"{context}: receiver has no projected axial extent")
    return lower, upper


def _face_record(face: Any, context: str) -> dict[str, Any] | None:
    if face.geomType() != "PLANE":
        return None
    area = float(face.Area())
    normal = _unit(face.normalAt(), f"{context} planar face normal")
    centroid = _center_tuple(face.Center(), f"{context} planar face centroid")
    if not math.isfinite(area) or area <= 0:
        return None
    bounds = _box_record(face, context)
    return {
        "area_mm2": round(area, 9),
        "centroid_global_xyz_mm": _vec_json(centroid),
        "normal_global_xyz": _vec_json(normal),
        "plane_datum_global_xyz_mm": _vec_json(centroid),
        "plane_offset_mm": round(_dot(normal, centroid), 9),
        "bounds_xyz_mm": bounds,
        "wire_count": len(face.Wires()),
        "inner_wire_count": max(0, len(face.Wires()) - 1),
        "cad_face_sha256": _source_shape_fingerprint(face),
    }


def _bounds_intersect(left: Sequence[float], right: Sequence[float]) -> bool:
    return not (
        left[1] < right[0] - FACE_PLANE_TOLERANCE_MM
        or right[1] < left[0] - FACE_PLANE_TOLERANCE_MM
        or left[3] < right[2] - FACE_PLANE_TOLERANCE_MM
        or right[3] < left[2] - FACE_PLANE_TOLERANCE_MM
        or left[5] < right[4] - FACE_PLANE_TOLERANCE_MM
        or right[5] < left[4] - FACE_PLANE_TOLERANCE_MM
    )


def _finite_opposed_face_pairs(
    first_shape: Any,
    second_shape: Any,
    first_id: str,
    second_id: str,
) -> list[dict[str, Any]]:
    """Find finite, opposed planar face intersections without removing bore wires."""
    first_faces = [
        (face, record)
        for index, face in enumerate(first_shape.Faces())
        if (record := _face_record(face, f"{first_id} face {index}")) is not None
    ]
    second_faces = [
        (face, record)
        for index, face in enumerate(second_shape.Faces())
        if (record := _face_record(face, f"{second_id} face {index}")) is not None
    ]
    contacts: list[dict[str, Any]] = []
    for first_face, first in first_faces:
        n_first = first["normal_global_xyz"]
        c_first = first["centroid_global_xyz_mm"]
        for second_face, second in second_faces:
            n_second = second["normal_global_xyz"]
            c_second = second["centroid_global_xyz_mm"]
            if _dot(n_first, n_second) > -1.0 + FACE_NORMAL_TOLERANCE:
                continue
            plane_gap = abs(_dot(n_first, _sub(c_second, c_first)))
            if plane_gap > FACE_PLANE_TOLERANCE_MM:
                continue
            if not _bounds_intersect(first["bounds_xyz_mm"], second["bounds_xyz_mm"]):
                continue
            try:
                common = first_face.intersect(second_face)
                common_faces = list(common.Faces())
            except Exception as error:
                raise ValueError(
                    f"{first_id}/{second_id}: finite planar-face intersection failed"
                ) from error
            finite_faces = []
            for common_face in common_faces:
                if common_face.geomType() != "PLANE":
                    continue
                area = float(common_face.Area())
                centroid = _center_tuple(
                    common_face.Center(), f"{first_id}/{second_id} overlap centroid"
                )
                if math.isfinite(area) and area > FACE_AREA_TOLERANCE_MM2:
                    finite_faces.append((area, centroid))
            area_sum = sum(area for area, _centroid in finite_faces)
            if area_sum <= FACE_AREA_TOLERANCE_MM2:
                continue
            centroid_sum = tuple(
                sum(area * centroid[axis] for area, centroid in finite_faces) / area_sum
                for axis in range(3)
            )
            contacts.append(
                {
                    "first_member": first_id,
                    "second_member": second_id,
                    "first_face": first,
                    "second_face": second,
                    "common_area_mm2": round(area_sum, 9),
                    "common_area_centroid_global_xyz_mm": _vec_json(centroid_sum),
                    "plane_datum_global_xyz_mm": _vec_json(centroid_sum),
                    "plane_normal_first_member_global_xyz": n_first,
                    "plane_normal_second_member_global_xyz": n_second,
                    "measured_plane_gap_mm": round(plane_gap, 9),
                    "overlap_method": "OCC common area of actual finished planar faces; existing inner wires retained",
                }
            )
    return contacts


def _interface_records(wood_shapes: Mapping[str, Any]) -> list[dict[str, Any]]:
    records = []
    for first_id, receiver_id in WOOD_INTERFACE_PAIRS:
        pairs = _finite_opposed_face_pairs(
            wood_shapes[first_id], wood_shapes[receiver_id], first_id, receiver_id
        )
        total_area = sum(float(row["common_area_mm2"]) for row in pairs)
        if total_area > FACE_AREA_TOLERANCE_MM2:
            centroid = tuple(
                sum(
                    float(row["common_area_mm2"])
                    * float(row["common_area_centroid_global_xyz_mm"][axis])
                    for row in pairs
                )
                / total_area
                for axis in range(3)
            )
            status = "finite_opposed_coplanar_patch_extracted"
            centroid_json = _vec_json(centroid)
        else:
            status = "no_finite_opposed_coplanar_patch_found"
            centroid_json = None
        records.append(
            {
                "interface_id": f"{first_id}_to_{receiver_id}",
                "members": [first_id, receiver_id],
                "bolt_axis_ids": sorted(
                    axis
                    for axis, receivers in AXIS_RECEIVERS.items()
                    if set(receivers) == {first_id, receiver_id}
                ),
                "status": status,
                "finite_opposed_face_pair_count": len(pairs),
                "finite_overlap_area_mm2": round(total_area, 9),
                "finite_overlap_area_centroid_global_xyz_mm": centroid_json,
                "actual_face_pairs": pairs,
                "contact_law_assigned": False,
                "active_pressure_patch_established": False,
            }
        )
    return records


def _derive_physical_bolt(
    axis_id: str, head: Any, shaft: Any
) -> tuple[Any, dict[str, Any]]:
    """Fuse the two CAD roles that represent one physical bolt, with identity checks."""
    head_record = _shape_metadata(head, f"{axis_id}/head union source")
    shaft_record = _shape_metadata(shaft, f"{axis_id}/shaft union source")
    try:
        overlap = float(head.intersect(shaft).Volume())
        physical_bolt = head.fuse(shaft).clean()
    except Exception as error:
        raise ValueError(f"{axis_id}: head/shaft physical-bolt union failed") from error
    if physical_bolt.isNull() or not physical_bolt.isValid() or len(physical_bolt.Solids()) != 1:
        raise ValueError(f"{axis_id}: head/shaft union must be one valid physical-bolt solid")
    union_record = _shape_metadata(physical_bolt, f"{axis_id} fused physical bolt")
    head_volume = float(head_record["volume_mm3"])
    shaft_volume = float(shaft_record["volume_mm3"])
    expected_union_volume = head_volume + shaft_volume - overlap
    observed_union_volume = float(union_record["volume_mm3"])
    inclusion_exclusion_error = abs(observed_union_volume - expected_union_volume)
    allowed = UNION_VOLUME_ABS_TOLERANCE_MM3 + (
        UNION_VOLUME_REL_TOLERANCE * max(expected_union_volume, observed_union_volume)
    )
    if not math.isfinite(overlap) or overlap < -allowed:
        raise ValueError(f"{axis_id}: head/shaft overlap volume is invalid")
    if inclusion_exclusion_error > allowed:
        raise ValueError(f"{axis_id}: fused-bolt volume fails head/shaft inclusion-exclusion")
    try:
        head_missing = max(0.0, float(head.cut(physical_bolt).Volume()))
        shaft_missing = max(0.0, float(shaft.cut(physical_bolt).Volume()))
        union_extra = max(
            0.0,
            float(physical_bolt.cut(head).cut(shaft).Volume()),
        )
    except Exception as error:
        raise ValueError(f"{axis_id}: head/shaft union symmetric-difference check failed") from error
    symmetric_difference = head_missing + shaft_missing + union_extra
    if not math.isfinite(symmetric_difference) or symmetric_difference > allowed:
        raise ValueError(f"{axis_id}: head/shaft union changes occupied hardware geometry")
    union_record["physical_bolt_union"] = {
        "source_role_ids": [f"{axis_id}/head", f"{axis_id}/shaft"],
        "source_role_shape_sha256": {
            "head": head_record["cad_shape_sha256"],
            "shaft": shaft_record["cad_shape_sha256"],
        },
        "valid": True,
        "solid_count": 1,
        "head_shaft_overlap_volume_mm3": round(max(0.0, overlap), 12),
        "expected_volume_by_inclusion_exclusion_mm3": round(expected_union_volume, 9),
        "observed_fused_volume_mm3": round(observed_union_volume, 9),
        "inclusion_exclusion_volume_difference_mm3": round(inclusion_exclusion_error, 12),
        "symmetric_difference_volume_mm3": round(symmetric_difference, 12),
        "allowed_volume_difference_mm3": round(allowed, 12),
        "symmetric_difference_passed": True,
        "method": "one OCC fuse of source CAD head and shaft roles; no other stack role included",
    }
    return physical_bolt, union_record


def _expected_geometry_shapes(geometry: Any) -> dict[str, Any]:
    hosts = getattr(geometry, "finished_hosts", None)
    candidates = getattr(geometry, "finished_candidate_parts", None)
    if not isinstance(hosts, Mapping) or not isinstance(candidates, Mapping):
        raise TypeError("current geometry has no finished host and candidate-part maps")
    if CLEAT_ID not in candidates:
        raise ValueError(f"current geometry omits finished cleat {CLEAT_ID}")
    missing_hosts = set(WOOD_PARTS[1:]) - set(hosts)
    if missing_hosts:
        raise ValueError(f"current geometry omits finished receiver members: {sorted(missing_hosts)}")
    shapes = {CLEAT_ID: candidates[CLEAT_ID]}
    shapes.update({part_id: hosts[part_id] for part_id in WOOD_PARTS[1:]})
    for part_id, shape in shapes.items():
        _shape_metadata(shape, f"{part_id} finished member")
    return shapes


def _validated_source_inputs(geometry: Any) -> dict[str, str]:
    source_inputs = getattr(geometry, "source_inputs_sha256", None)
    if not isinstance(source_inputs, Mapping) or not source_inputs:
        raise ValueError("current G24 geometry has no source-input fingerprint map")
    result = {}
    for relative_path, expected in sorted(source_inputs.items()):
        relative_path = str(relative_path)
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError(f"current geometry has an invalid source hash: {relative_path}")
        try:
            observed = _sha256_file(ROOT / relative_path)
        except OSError as error:
            raise ValueError(f"current geometry source input is unavailable: {relative_path}") from error
        if observed != expected:
            raise ValueError(f"current geometry source input hash changed: {relative_path}")
        result[relative_path] = observed
    return result


def _interval_lists_close(
    actual: Sequence[Sequence[float]], expected: Sequence[Sequence[float]], tolerance_mm: float = 1e-3
) -> bool:
    return len(actual) == len(expected) and all(
        len(left) == 2
        and len(right) == 2
        and all(
            math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tolerance_mm)
            for a, b in zip(left, right, strict=True)
        )
        for left, right in zip(actual, expected, strict=True)
    )


def _build_manifest(
    geometry: Any,
    pins: Mapping[str, Any],
    grip_inputs: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if getattr(geometry, "layout_id", None) != CURRENT_REVISION_ID:
        raise ValueError("input geometry is not the selected current revision")
    if getattr(geometry, "trial_id", None) != CURRENT_REVISION_ID:
        raise ValueError("input geometry trial ID differs from the selected current revision")
    if getattr(geometry, "status", None) != "unaccepted_viewer_geometry_revision":
        raise ValueError("input geometry status differs from the current viewer geometry revision")

    inventory_bytes = INVENTORY_PATH.read_bytes()
    inventory_sha = _sha256_bytes(inventory_bytes)
    inventory = json.loads(inventory_bytes)
    if getattr(geometry, "source_inventory_sha256", None) != inventory_sha:
        raise ValueError("current geometry source inventory hash differs from the canonical baseline")
    if inventory.get("source_commit") != SOURCE_BASELINE_COMMIT:
        raise ValueError("canonical source inventory is not pinned to the historical baseline source")
    source_inputs = _validated_source_inputs(geometry)
    if _plain(getattr(geometry, "source_inventory", None)) != inventory:
        raise ValueError("current geometry source inventory differs from canonical baseline")

    shapes = _expected_geometry_shapes(geometry)
    source_rows = _inventory_rows(inventory)
    grain_records: dict[str, dict[str, Any]] = {}
    for part_id in WOOD_PARTS[1:]:
        row = source_rows.get(part_id)
        if row is None:
            raise ValueError(f"source inventory has no grain row for {part_id}")
        vector = _unit(row.get("grain_axis_global_xyz"), f"{part_id} grain axis")
        grain_records[part_id] = {
            "grain_axis_global_xyz": _vec_json(vector),
            "grain_basis": "source inventory grain_axis_global_xyz",
            "source_part_id": part_id,
        }
    rail_row = source_rows.get("base_rail_bottom_right", {})
    local_axes = rail_row.get("local_axes", {})
    cleat_n = _unit(local_axes.get("N"), f"{CLEAT_ID} common-block local N")
    grain_records[CLEAT_ID] = {
        "grain_axis_global_xyz": _vec_json(cleat_n),
        "grain_axis_local_name": "N",
        "grain_basis": (
            "common-block local N mapped by the bottom-center source-local frame; "
            "source inventory base_rail_bottom_right.local_axes.N"
        ),
        "source_part_id": "base_rail_bottom_right",
    }

    bores = getattr(geometry, "candidate_bores", None)
    hardware = getattr(geometry, "candidate_installed_hardware", None)
    if not isinstance(bores, Mapping) or not isinstance(hardware, Mapping):
        raise TypeError("current geometry lacks candidate bore or installed-role maps")
    grip_rows = grip_inputs["axes"]
    if not isinstance(grip_rows, Mapping):
        raise TypeError("source-bound current-grip axis rows are unavailable")
    axes: list[dict[str, Any]] = []
    role_shapes: dict[str, Any] = {}
    physical_bolt_shapes: dict[str, Any] = {}
    physical_metal_rows: list[dict[str, Any]] = []
    if set(AXIS_RECEIVERS) - set(bores) or set(AXIS_RECEIVERS) - set(hardware):
        raise ValueError("current geometry omits one or more of the four selected physical bolts")
    for axis_id, expected_receivers in AXIS_RECEIVERS.items():
        bore = bores[axis_id]
        roles = hardware[axis_id]
        bore_receivers = tuple(getattr(bore, "receiver_ids", ()))
        if (
            getattr(bore, "axis_id", None) != axis_id
            or len(bore_receivers) != 2
            or len(set(bore_receivers)) != 2
            or set(bore_receivers) != set(expected_receivers)
            or getattr(bore, "family", None) != "bottom_center"
        ):
            raise ValueError(f"{axis_id}: current candidate bore identity/membership changed")
        if set(roles) != set(HARDWARE_ROLES):
            raise ValueError(f"{axis_id}: expected exactly five distinct CAD hardware roles")
        row = grip_rows.get(axis_id)
        if not isinstance(row, Mapping) or row.get("axis_id") != axis_id:
            raise ValueError(f"{axis_id}: verified current-grip axis row is unavailable")
        if not row.get("frozen_axis_direction_matches_within_tolerance") or not row.get(
            "frozen_shaft_axis_line_matches_within_tolerance"
        ):
            raise ValueError(f"{axis_id}: current-grip report does not verify the live bolt axis")
        direction = current_grip._unit_direction(roles, axis_id)
        report_direction = _unit(
            row.get("axis_head_to_nut_global_unit"), f"{axis_id} pinned axis direction"
        )
        direction_error = current_grip._direction_difference(direction, report_direction)
        if direction_error > current_grip.AXIS_TOLERANCE:
            raise ValueError(f"{axis_id}: live washer-center direction differs from current-grip report")
        line_point = _finite_vector(
            row.get("frozen_shaft_center_xyz_mm"), f"{axis_id} current-grip shaft center"
        )
        role_offsets = {
            role: current_grip._perpendicular_offset_mm(
                roles[role].Center().toTuple(), line_point, direction
            )
            for role in HARDWARE_ROLES
        }
        if max(role_offsets.values()) > current_grip.AXIS_LINE_POSITION_TOLERANCE_MM:
            raise ValueError(f"{axis_id}: live hardware roles differ from the verified current axis line")

        role_absolute_intervals = {
            role: current_grip.projected_solid_intervals(
                roles[role], direction, axis_id=axis_id, label=role
            )
            for role in HARDWARE_ROLES
        }
        datum_axis_mm, live_head_seat_check = current_grip._underhead_datum(
            role_absolute_intervals, axis_id
        )
        report_head_seat = row.get("underhead_datum", {}).get(
            "head_underface_contact_check", {}
        )
        for field in (
            "head_toward_nut_face_global_axis_mm",
            "head_washer_toward_head_face_global_axis_mm",
            "signed_gap_mm",
        ):
            if field not in report_head_seat or not math.isclose(
                float(live_head_seat_check[field]),
                float(report_head_seat[field]),
                rel_tol=0.0,
                abs_tol=current_grip.INTERFACE_TOLERANCE_MM,
            ):
                raise ValueError(f"{axis_id}: live head/head-washer datum differs from current-grip report")
        origin = tuple(
            line_point[index]
            + (datum_axis_mm - _dot(line_point, direction)) * direction[index]
            for index in range(3)
        )
        role_projection_records = {}
        for role in HARDWARE_ROLES:
            role_record = current_grip._interval_record(
                roles[role], direction, datum_axis_mm, axis_id=axis_id, label=role
            )
            report_role = row.get("hardware_roles", {}).get(role, {})
            if not _interval_lists_close(
                role_record["union_intervals_from_underhead_mm"],
                report_role.get("union_intervals_from_underhead_mm", ()),
            ):
                raise ValueError(f"{axis_id}/{role}: live projection differs from current-grip report")
            role_projection_records[role] = role_record

        report_order = tuple(row.get("ordered_receiver_ids_head_to_nut", ()))
        report_receiver_rows = {
            str(receiver.get("receiver_id")): receiver
            for receiver in row.get("wood_receiver_intervals", ())
            if isinstance(receiver, Mapping)
        }
        if (
            len(report_order) != 2
            or len(set(report_order)) != 2
            or set(report_order) != set(bore_receivers)
            or set(report_receiver_rows) != set(bore_receivers)
        ):
            raise ValueError(f"{axis_id}: current-grip raw receiver membership differs from the bore")
        shaft_diameter = current_grip._shaft_diameter_mm(roles["shaft"], direction, axis_id)
        live_receiver_rows = {}
        for receiver_id in bore_receivers:
            live_receiver = current_grip._receiver_axis_record(
                geometry,
                receiver_id,
                roles["shaft"],
                direction,
                datum_axis_mm,
                shaft_diameter,
                axis_id,
            )
            frozen_receiver = report_receiver_rows[receiver_id]
            if not _interval_lists_close(
                live_receiver["intersection_solid_intervals_from_underhead_mm"],
                frozen_receiver.get("intersection_solid_intervals_from_underhead_mm", ()),
            ):
                raise ValueError(f"{axis_id}/{receiver_id}: raw receiver projection differs from current-grip report")
            if not live_receiver["current_shaft_volume_covers_long_probe_intersection"]:
                raise ValueError(f"{axis_id}/{receiver_id}: live shaft does not cover the raw receiver probe")
            live_receiver_rows[receiver_id] = live_receiver
        sorted_receiver_ids = tuple(
            sorted(
                live_receiver_rows,
                key=lambda receiver_id: min(
                    float(interval[0])
                    for interval in live_receiver_rows[receiver_id][
                        "intersection_solid_intervals_from_underhead_mm"
                    ]
                ),
            )
        )
        if sorted_receiver_ids != report_order:
            raise ValueError(f"{axis_id}: current-grip receiver order differs from live axial intervals")
        raw_receiver_rows = [
            {
                "member_id": receiver_id,
                "receiver_order_head_to_nut": index + 1,
                "projected_intervals_from_underhead_datum_mm": live_receiver_rows[receiver_id][
                    "intersection_solid_intervals_from_underhead_mm"
                ],
                "projected_material_length_mm": live_receiver_rows[receiver_id][
                    "receiver_wood_axis_length_mm"
                ],
                "projection_gaps_mm": live_receiver_rows[receiver_id][
                    "intersection_projection_gaps_mm"
                ],
                "long_probe_minus_current_shaft_volume_mm3": live_receiver_rows[receiver_id][
                    "long_probe_minus_current_shaft_volume_mm3"
                ],
                "current_shaft_covers_raw_receiver": live_receiver_rows[receiver_id][
                    "current_shaft_volume_covers_long_probe_intersection"
                ],
            }
            for index, receiver_id in enumerate(sorted_receiver_ids)
        ]
        axis_roles = []
        role_metadata = {}
        for role in HARDWARE_ROLES:
            role_shape = roles[role]
            role_shapes[f"{axis_id}/{role}"] = role_shape
            metadata = _shape_metadata(role_shape, f"{axis_id}/{role}")
            role_metadata[role] = metadata
            axis_roles.append(
                {
                    "role": role,
                    "cad_shape": metadata,
                    "step_artifact_key": f"hardware/{axis_id}/{role}.step",
                    "axial_projection_from_underhead_datum_mm": role_projection_records[role][
                        "union_intervals_from_underhead_mm"
                    ],
                }
            )
        physical_bolt, physical_bolt_record = _derive_physical_bolt(
            axis_id, roles["head"], roles["shaft"]
        )
        physical_bolt_key = f"physical_metal/{axis_id}/bolt"
        physical_bolt_shapes[physical_bolt_key] = physical_bolt
        physical_metal_rows.append(
            {
                "physical_body_id": physical_bolt_key,
                "physical_kind": "bolt_head_plus_shaft_union",
                "axis_id": axis_id,
                "source_cad_role_ids": [f"{axis_id}/head", f"{axis_id}/shaft"],
                "step_artifact_key": f"{physical_bolt_key}.step",
                "solid": physical_bolt_record,
                "union_identity": physical_bolt_record["physical_bolt_union"],
            }
        )
        for role in ("head_washer", "nut_washer", "nut"):
            physical_body_key = f"physical_metal/{axis_id}/{role}"
            physical_metal_rows.append(
                {
                    "physical_body_id": physical_body_key,
                    "physical_kind": role,
                    "axis_id": axis_id,
                    "source_cad_role_ids": [f"{axis_id}/{role}"],
                    "step_artifact_key": f"hardware/{axis_id}/{role}.step",
                    "solid": role_metadata[role],
                }
            )
        axes.append(
            {
                "physical_bolt_id": axis_id,
                "physical_bolt_count": 1,
                "physical_bolt_roles": list(PHYSICAL_BOLT_ROLES),
                "head_and_shaft_are_one_physical_bolt": True,
                "stack_row_source": "source-bound current-grip report plus live solid projections and raw receiver probes",
                "axis_origin_global_xyz_mm": _vec_json(origin),
                "axis_origin_datum": "live head underface / head-washer headward face on verified current shaft centerline",
                "axis_direction_head_to_nut_global_xyz": _vec_json(direction),
                "axis_source": "current grip-screen attempt02 + live washer-center and solid-axis projections",
                "receivers_head_to_nut": list(sorted_receiver_ids),
                "bore_receiver_ids_membership_only": sorted(bore_receivers),
                "raw_receiver_projected_intervals": raw_receiver_rows,
                "physical_hardware_roles": axis_roles,
                "cad_role_count": len(axis_roles),
                "physical_metal_body_ids": [
                    f"physical_metal/{axis_id}/bolt",
                    f"physical_metal/{axis_id}/head_washer",
                    f"physical_metal/{axis_id}/nut_washer",
                    f"physical_metal/{axis_id}/nut",
                ],
                "occupancy_bore": _shape_metadata(bore.shape, f"{axis_id} occupancy bore"),
            }
        )
    if (
        len(axes) != 4
        or sum(row["cad_role_count"] for row in axes) != 20
        or len(physical_metal_rows) != 16
    ):
        raise ValueError("current patch must contain exactly four bolts and twenty CAD roles")

    body_records = []
    wood_shapes = {}
    for part_id in WOOD_PARTS:
        shape = shapes[part_id]
        wood_shapes[part_id] = shape
        body_records.append(
            {
                "part_id": part_id,
                "geometry_role": "finished_candidate_part" if part_id == CLEAT_ID else "finished_source_host",
                "finished_geometry": _shape_metadata(shape, f"{part_id} finished member"),
                "grain": grain_records[part_id],
                "step_artifact_key": f"wood/{part_id}.step",
                "full_finished_member_exported": True,
                "arbitrary_patch_cut_applied": False,
            }
        )

    interfaces = _interface_records(wood_shapes)
    for record in interfaces:
        if record["status"] != "finite_opposed_coplanar_patch_extracted":
            record["migration_blocker"] = (
                "No actual finite opposed coplanar face pair exists in the supplied finished solids; "
                "do not substitute a centroid, nominal face area, or historical interface pin."
            )

    blockers = [
        {
            "scope": "wood-contact-interface",
            "interface_id": row["interface_id"],
            "reason": row["migration_blocker"],
        }
        for row in interfaces
        if row["status"] != "finite_opposed_coplanar_patch_extracted"
    ]
    inventory_record = {
        "schema": SCHEMA,
        "status": "current_geometry_patch_inputs_only",
        "geometry_binding": {
            "layout_id": geometry.layout_id,
            "trial_id": geometry.trial_id,
            "status": geometry.status,
            "source_inventory_sha256": inventory_sha,
            "source_inputs_sha256": source_inputs,
        },
        "candidate": {
            "revision_id": CURRENT_REVISION_ID,
            "implementation_revision": CURRENT_IMPLEMENTATION_REVISION,
            "source_inventory_baseline_commit": SOURCE_BASELINE_COMMIT,
            "source_inventory_sha256": inventory_sha,
            "current_review_pins": dict(pins),
        },
        "scope": {
            "finished_wood_bodies": 3,
            "physical_bolts": 4,
            "modeled_hardware_cad_roles": 20,
            "wood_interfaces": 3,
            "step_artifacts": 27,
            "derived_physical_bolt_unions": 4,
            "physical_metal_bodies": 16,
            "full_finished_members_exported": True,
            "arbitrary_member_cuts": False,
            "meshed": False,
            "native_solve_run": False,
            "contact_law_assigned": False,
            "boundary_method": "pending",
            "strength_or_joint_acceptance_claim": False,
        },
        "migration_blockers": blockers,
        "wood_bodies": body_records,
        "physical_bolts": axes,
        "physical_metal_bodies": physical_metal_rows,
        "wood_interfaces": interfaces,
        "limitations": [
            "The source inventory commit and current implementation revision are distinct provenance pins.",
            "STEP inputs are the already composed nominal CAD solids, not inspected or received wood or hardware.",
            "Head and shaft CAD roles remain separate shapes but are counted as one physical bolt per axis.",
            "Four derived bolt solids are explicit OCC unions of their source head/shaft roles; washers and nuts remain individual physical bodies.",
            "Coplanar face overlap is a geometric input record; it does not establish a contact law or active pressure region.",
            "Projected receiver intervals are raw geometry containment evidence, not installation or strength conclusions.",
            "A physical-metal mesher must use the four derived bolt unions and twelve separate washers/nuts, not treat all twenty duplicated role solids as twenty physical bodies.",
        ],
    }
    return inventory_record, {**wood_shapes, **role_shapes, **physical_bolt_shapes}


def _vector_close(left: Sequence[float], right: Sequence[float]) -> bool:
    return len(left) == 3 and all(
        math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=SOLID_POSITION_TOLERANCE_MM)
        for a, b in zip(left, right, strict=True)
    )


def _assert_step_identity(source: Mapping[str, Any], readback: Mapping[str, Any], context: str) -> None:
    if readback["solid_count"] != 1:
        raise ValueError(f"{context}: STEP round-trip changed solid count")
    if not math.isclose(
        float(source["volume_mm3"]),
        float(readback["volume_mm3"]),
        rel_tol=SOLID_VOLUME_REL_TOLERANCE,
        abs_tol=SOLID_VOLUME_ABS_TOLERANCE_MM3,
    ):
        raise ValueError(f"{context}: STEP round-trip volume differs")
    if not _vector_close(source["centroid_global_xyz_mm"], readback["centroid_global_xyz_mm"]):
        raise ValueError(f"{context}: STEP round-trip centroid differs")
    if any(
        not math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=SOLID_POSITION_TOLERANCE_MM)
        for a, b in zip(source["bounds_xyz_mm"], readback["bounds_xyz_mm"], strict=True)
    ):
        raise ValueError(f"{context}: STEP round-trip bounds differ")


def _symmetric_difference(source: Any, readback: Any, context: str) -> dict[str, Any]:
    try:
        source_only = max(0.0, float(source.cut(readback).Volume()))
        step_only = max(0.0, float(readback.cut(source).Volume()))
    except Exception as error:
        raise ValueError(f"{context}: STEP/source symmetric difference failed") from error
    volume = float(source.Volume())
    readback_volume = float(readback.Volume())
    difference = source_only + step_only
    allowed = SOLID_SYMMETRIC_DIFFERENCE_ABS_TOLERANCE_MM3 + (
        SOLID_SYMMETRIC_DIFFERENCE_REL_TOLERANCE * max(volume, readback_volume)
    )
    if not all(math.isfinite(value) for value in (difference, allowed)) or difference > allowed:
        raise ValueError(f"{context}: STEP/source occupied-volume difference exceeds tolerance")
    return {
        "source_only_volume_mm3": round(source_only, 12),
        "step_only_volume_mm3": round(step_only, 12),
        "symmetric_difference_volume_mm3": round(difference, 12),
        "allowed_volume_difference_mm3": round(allowed, 12),
        "passed": True,
    }


def _export_one_shape(shape: Any, path: Path, artifact_id: str) -> dict[str, Any]:
    source = _shape_metadata(shape, f"{artifact_id} source solid")
    cq.exporters.export(shape, str(path))
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"{artifact_id}: STEP exporter did not create a nonempty file")
    imported = cq.importers.importStep(str(path)).val()
    readback = _shape_metadata(imported, f"{artifact_id} STEP readback")
    _assert_step_identity(source, readback, artifact_id)
    symmetric = _symmetric_difference(shape, imported, artifact_id)
    return {
        "file": path.name,
        "file_sha256": _sha256_file(path),
        "source_solid": source,
        "step_readback_solid": readback,
        "identity_checks": {
            "solid_count": True,
            "volume": True,
            "centroid": True,
            "bounds": True,
            "symmetric_difference": symmetric,
            "face_ordinal_used": False,
        },
    }


def export_current_patch_inputs(geometry: Any, output_dir: str | Path) -> dict[str, Any]:
    """Export the current bottom-center right local patch to a new STEP bundle.

    ``geometry`` must be the already revised G24 object. The destination must
    not exist. The function only reads its finished member/role shapes and
    writes the exact selected bodies; it never composes or modifies geometry.
    """
    target = Path(output_dir).expanduser().absolute()
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"patch export destination already exists: {target}")
    grip_inputs = _read_current_grip_inputs()
    pins = _read_current_pins(grip_inputs)
    inventory, shapes = _build_manifest(geometry, pins, grip_inputs)

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=str(target.parent)))
    try:
        step_artifacts: dict[str, dict[str, Any]] = {}
        for part_id in WOOD_PARTS:
            rel = Path("wood") / f"{part_id}.step"
            path = staging / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            step_artifacts[f"wood/{part_id}"] = _export_one_shape(shapes[part_id], path, part_id)
        for axis_id in AXIS_RECEIVERS:
            for role in HARDWARE_ROLES:
                artifact_key = f"hardware/{axis_id}/{role}"
                rel = Path(artifact_key + ".step")
                path = staging / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                step_artifacts[artifact_key] = _export_one_shape(
                    shapes[f"{axis_id}/{role}"], path, f"{axis_id}/{role}"
                )
        for axis_id in AXIS_RECEIVERS:
            artifact_key = f"physical_metal/{axis_id}/bolt"
            rel = Path(artifact_key + ".step")
            path = staging / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            step_artifacts[artifact_key] = _export_one_shape(
                shapes[artifact_key], path, artifact_key
            )
        if len(step_artifacts) != 27:
            raise ValueError("patch STEP bundle must contain exactly 27 source/physical solids")
        inventory["step_artifacts"] = step_artifacts
        inventory_bytes = _json_bytes(inventory)
        inventory_path = staging / "inventory.json"
        inventory_path.write_bytes(inventory_bytes)
        artifact_hashes = {
            "inventory.json": _sha256_bytes(inventory_bytes),
            **{
                f"{key}.step": artifact["file_sha256"]
                for key, artifact in step_artifacts.items()
            },
        }
        hashes_bytes = _json_bytes(artifact_hashes)
        (staging / "sha256.json").write_bytes(hashes_bytes)
        for path in staging.rglob("*.step"):
            path.chmod(0o444)
        inventory_path.chmod(0o444)
        (staging / "sha256.json").chmod(0o444)
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"patch export destination appeared during export: {target}")
        os.replace(staging, target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {
        "output_dir": str(target),
        "inventory_path": str(target / "inventory.json"),
        "inventory_sha256": _sha256_file(target / "inventory.json"),
        "artifact_hashes": artifact_hashes,
        "status": inventory["status"],
    }
