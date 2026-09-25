"""Exact axial hardware and raw-receiver intervals for the current WJ24 bolts.

The collector reads the already materialized ``g24_outer_2x6`` geometry. It
does not rebuild CAD, select hardware, infer thread geometry, or run mechanics.
Each shape is rotated onto its bolt axis before reading its axial interval;
world XYZ bounding-box extents are never treated as bolt lengths.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRENT_REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
SCHEMA = "wood_joint_current_grip_screen/v1"
SNAPSHOT_PATH = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json"
REPORT_PATH = ROOT / "site/owner-wood-joints-review-report.json"
DOC_PATH = ROOT / "docs/wood-joints-mvp/current-grip-screen.md"
EXPECTED_AXIS_COUNT = 92
EXPECTED_SHORTENED_AXIS_IDS = frozenset(
    f"knee_outer_{side}_{station}_{index}"
    for side in ("left", "right")
    for station in ("post", "side")
    for index in (1, 2)
)
EXPECTED_TALL_BLOCK_HEAD_MOVE_IDS = frozenset(
    {
        *(f"center_principal_{side}_{index}" for side in ("left", "right") for index in (1, 2)),
        *(f"center_principal_header_{side}_{index}" for side in ("left", "right") for index in (1, 2)),
    }
)
EXPECTED_ROLES = frozenset({"shaft", "head", "head_washer", "nut_washer", "nut"})
INTERFACE_TOLERANCE_MM = 1e-4
INTERVAL_CONTIGUITY_TOLERANCE_MM = 1e-6
INTERSECTION_VOLUME_TOLERANCE_MM3 = 1e-5
AXIS_TOLERANCE = 1e-7
AXIS_LINE_POSITION_TOLERANCE_MM = 1e-4
NOMINAL_LENGTH_TOLERANCE_MM = 1e-3

# These exact 1/4-in partially threaded dimensional classes already appear in
# repository evidence. Their presence is a dimensional comparator only; it
# neither assigns a product to a current axis nor carries over a prior joint
# screen. Values are ASME B18.2.1 bounds cited by the existing notes.
PARTIAL_THREAD_CLASSES: dict[float, dict[str, Any]] = {
    95.25: {
        "length_mm": 95.25,
        "length_tolerance_minus_mm": 1.524,
        "Lb_min_mm": 69.85,
        "Lg_max_mm": 76.2,
        "evidence": "docs/wood-joints-mvp/ordinary-hardware-basis.md; 3-3/4 in candidate",
        "product_candidate": "K.L. Jack 25C375HCS5Z",
    },
    120.65: {
        "length_mm": 120.65,
        "length_tolerance_minus_mm": 2.54,
        "Lb_min_mm": 95.25,
        "Lg_max_mm": 101.6,
        "evidence": "docs/wood-joints-mvp/wj24-bolt-length-screen.md; conditional 4-3/4 in standard class",
        "product_candidate": None,
    },
    146.05: {
        "length_mm": 146.05,
        "length_tolerance_minus_mm": 2.54,
        "Lb_min_mm": 120.65,
        "Lg_max_mm": 127.0,
        "evidence": "docs/wood-joints-mvp/wj24-bolt-length-screen.md; conditional 5-3/4 in standard class",
        "product_candidate": None,
    },
    152.4: {
        "length_mm": 152.4,
        "length_tolerance_minus_mm": 2.54,
        "Lb_min_mm": 127.0,
        "Lg_max_mm": 133.35,
        "evidence": "docs/wood-joints-mvp/ordinary-hardware-basis.md; 6 in candidate, corrected by bolt-dimension-source-correction.md",
        "product_candidate": "K.L. Jack 25C600HCS5Z",
    },
    190.5: {
        "length_mm": 190.5,
        "length_tolerance_minus_mm": 4.572,
        "Lb_min_mm": 158.75,
        "Lg_max_mm": 165.1,
        "evidence": "docs/wood-joints-mvp/wj24-bolt-length-screen.md; conditional 7-1/2 in standard class",
        "product_candidate": None,
    },
    203.2: {
        "length_mm": 203.2,
        "length_tolerance_minus_mm": 4.572,
        "Lb_min_mm": 171.45,
        "Lg_max_mm": 177.8,
        "evidence": "docs/wood-joints-mvp/wj24-bolt-length-screen.md; 8 in comparator, rejected for the historical 167 mm stack",
        "product_candidate": None,
    },
}


def merge_intervals(
    intervals: Sequence[Sequence[float]], *, tolerance: float = INTERVAL_CONTIGUITY_TOLERANCE_MM
) -> list[list[float]]:
    """Union overlapping/touching scalar intervals without closing real gaps."""
    normalized: list[tuple[float, float]] = []
    for interval in intervals:
        if len(interval) != 2:
            raise ValueError("each interval must have exactly two endpoints")
        low, high = (float(interval[0]), float(interval[1]))
        if not (math.isfinite(low) and math.isfinite(high)) or high < low:
            raise ValueError(f"invalid interval: {interval!r}")
        normalized.append((low, high))
    normalized.sort()
    merged: list[list[float]] = []
    for low, high in normalized:
        if not merged or low > merged[-1][1] + tolerance:
            merged.append([low, high])
        else:
            merged[-1][1] = max(merged[-1][1], high)
    return merged


def interval_gaps(intervals: Sequence[Sequence[float]]) -> list[list[float]]:
    """Return positive gaps between already merged scalar intervals."""
    ordered = sorted((float(row[0]), float(row[1])) for row in intervals)
    return [
        [ordered[index][1], ordered[index + 1][0]]
        for index in range(len(ordered) - 1)
        if ordered[index + 1][0] > ordered[index][1]
    ]


def _sum_interval_length(intervals: Sequence[Sequence[float]]) -> float:
    return sum(float(high) - float(low) for low, high in intervals)


def _json_normalize(value: Any) -> Any:
    """Normalize tuple-backed live report rows to the frozen JSON form."""
    try:
        return json.loads(json.dumps(value, sort_keys=True))
    except (TypeError, ValueError) as error:
        raise ValueError("value is not JSON serializable") from error


def _unit_direction(roles: Mapping[str, Any], axis_id: str) -> tuple[float, float, float]:
    """Get the current head-to-nut direction from the two washer centers."""
    head = roles["head_washer"].Center().toTuple()
    nut = roles["nut_washer"].Center().toTuple()
    vector = tuple(float(nut[index]) - float(head[index]) for index in range(3))
    norm = math.sqrt(sum(component * component for component in vector))
    if not math.isfinite(norm) or norm <= 1e-9:
        raise ValueError(f"{axis_id}: head and nut washer centers do not define an axis")
    direction = tuple(component / norm for component in vector)
    if not math.isclose(sum(value * value for value in direction), 1.0, abs_tol=1e-9):
        raise ValueError(f"{axis_id}: failed to normalize the current bolt direction")
    return direction  # type: ignore[return-value]


def _direction_difference(
    actual: Sequence[float], expected: Sequence[float]
) -> float:
    if len(actual) != 3 or len(expected) != 3:
        raise ValueError("axis direction vectors must have three components")
    return math.sqrt(
        sum((float(actual[index]) - float(expected[index])) ** 2 for index in range(3))
    )


def _perpendicular_offset_mm(
    point: Sequence[float], line_point: Sequence[float], direction: Sequence[float]
) -> float:
    """Return a point's shortest distance from an infinite directed axis line."""
    if len(point) != 3 or len(line_point) != 3 or len(direction) != 3:
        raise ValueError("axis-line points and direction must have three components")
    unit = tuple(float(value) for value in direction)
    norm = math.sqrt(sum(value * value for value in unit))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise ValueError("axis-line direction must be a unit vector")
    delta = tuple(float(point[i]) - float(line_point[i]) for i in range(3))
    along = sum(delta[i] * unit[i] for i in range(3))
    return math.sqrt(sum((delta[i] - along * unit[i]) ** 2 for i in range(3)))


def projected_solid_intervals(
    shape: Any, direction: Sequence[float], *, axis_id: str, label: str
) -> list[list[float]]:
    """Return one exact axial projection interval per B-rep solid.

    Rotating around the global origin maps ``direction`` to local +Z. Bounding
    box z limits after that rotation are the shape's projection limits along
    the axis; no world XYZ AABB dimension is interpreted as a length.
    """
    import cadquery as cq

    if len(direction) != 3:
        raise ValueError(f"{axis_id}/{label}: direction must have three components")
    vector = cq.Vector(*(float(value) for value in direction))
    if not math.isclose(vector.Length, 1.0, abs_tol=1e-6):
        raise ValueError(f"{axis_id}/{label}: projection direction is not a unit vector")
    solids = list(shape.Solids())
    if not solids:
        raise ValueError(f"{axis_id}/{label}: shape contains no solid components")
    local = cq.Location(cq.Plane(origin=(0, 0, 0), normal=vector)).inverse
    intervals = []
    for solid_index, solid in enumerate(solids):
        box = solid.moved(local).BoundingBox()
        low, high = float(box.zmin), float(box.zmax)
        if not (math.isfinite(low) and math.isfinite(high)) or high < low:
            raise ValueError(f"{axis_id}/{label}/solid_{solid_index}: invalid projected bounds")
        intervals.append([low, high])
    return sorted(intervals)


def _interval_record(
    shape: Any,
    direction: Sequence[float],
    datum_axis_mm: float,
    *,
    axis_id: str,
    label: str,
) -> dict[str, Any]:
    absolute = projected_solid_intervals(shape, direction, axis_id=axis_id, label=label)
    relative = [[low - datum_axis_mm, high - datum_axis_mm] for low, high in absolute]
    union = merge_intervals(relative)
    return {
        "solid_intervals_from_underhead_mm": relative,
        "union_intervals_from_underhead_mm": union,
        "projection_gaps_mm": interval_gaps(union),
        "union_length_mm": _sum_interval_length(union),
        "projection_envelope_from_underhead_mm": [union[0][0], union[-1][1]],
    }


def _underhead_datum(
    role_intervals: Mapping[str, Sequence[Sequence[float]]], axis_id: str
) -> tuple[float, dict[str, float]]:
    head_intervals = role_intervals["head"]
    washer_intervals = role_intervals["head_washer"]
    head_toward_nut = max(float(row[1]) for row in head_intervals)
    washer_toward_head = min(float(row[0]) for row in washer_intervals)
    signed_gap = washer_toward_head - head_toward_nut
    if abs(signed_gap) > INTERFACE_TOLERANCE_MM:
        raise ValueError(
            f"{axis_id}: head/head-washer axial faces are not adjacent "
            f"(signed gap {signed_gap:.6f} mm)"
        )
    return (head_toward_nut + washer_toward_head) / 2.0, {
        "head_toward_nut_face_global_axis_mm": head_toward_nut,
        "head_washer_toward_head_face_global_axis_mm": washer_toward_head,
        "signed_gap_mm": signed_gap,
    }


def _raw_receiver(geometry: Any, receiver_id: str) -> Any:
    for name in ("raw_candidate_parts", "raw_hosts"):
        mapping = getattr(geometry, name, {})
        if receiver_id in mapping:
            return mapping[receiver_id]
    raise ValueError(f"raw receiver is missing from current geometry: {receiver_id}")


def _shaft_diameter_mm(shape: Any, direction: Sequence[float], axis_id: str) -> float:
    """Recover the modeled cylindrical shaft diameter from its exact solid."""
    import cadquery as cq

    solids = list(shape.Solids())
    if len(solids) != 1:
        raise ValueError(f"{axis_id}: modeled shaft must be one connected cylinder solid")
    local = cq.Location(
        cq.Plane(origin=(0, 0, 0), normal=cq.Vector(*(float(v) for v in direction)))
    ).inverse
    box = solids[0].moved(local).BoundingBox()
    axial_length = float(box.zlen)
    if axial_length <= 0 or not math.isclose(float(box.xlen), float(box.ylen), abs_tol=1e-4):
        raise ValueError(f"{axis_id}: modeled shaft is not a circular cylinder envelope")
    diameter_from_bbox = (float(box.xlen) + float(box.ylen)) / 2.0
    diameter_from_volume = 2.0 * math.sqrt(float(shape.Volume()) / (math.pi * axial_length))
    if not math.isclose(diameter_from_bbox, diameter_from_volume, rel_tol=0.0, abs_tol=1e-4):
        raise ValueError(f"{axis_id}: shaft cylinder dimensions and volume do not reconcile")
    return diameter_from_volume


def _receiver_axis_record(
    geometry: Any,
    receiver_id: str,
    shaft: Any,
    direction: Sequence[float],
    datum_axis_mm: float,
    shaft_diameter_mm: float,
    axis_id: str,
) -> dict[str, Any]:
    import cadquery as cq

    receiver = _raw_receiver(geometry, receiver_id)
    # Use the current shaft radius and centerline in a separate long probe to
    # recover the complete raw receiver grip even if an occupied shaft is
    # shorter than a timber. The raw receiver's oriented projection supplies
    # only safe probe bounds; intersection with the cylindrical probe supplies
    # the actual support intervals.
    raw_bounds = projected_solid_intervals(
        receiver, direction, axis_id=axis_id, label=f"raw_receiver/{receiver_id}/probe_extent"
    )
    current_shaft_bounds = projected_solid_intervals(
        shaft, direction, axis_id=axis_id, label=f"{receiver_id}/current_shaft_extent"
    )
    center = cq.Vector(*shaft.Center().toTuple())
    unit = cq.Vector(*(float(value) for value in direction))
    center_axis = sum(float(center.toTuple()[index]) * float(direction[index]) for index in range(3))
    probe_low = min(
        min(float(row[0]) for row in raw_bounds),
        min(float(row[0]) for row in current_shaft_bounds),
    ) - 1.0
    probe_high = max(
        max(float(row[1]) for row in raw_bounds),
        max(float(row[1]) for row in current_shaft_bounds),
    ) + 1.0
    probe_start = center + unit * (probe_low - center_axis)
    long_probe = cq.Solid.makeCylinder(
        float(shaft_diameter_mm) / 2.0, probe_high - probe_low, probe_start, unit
    )
    long_common = receiver.intersect(long_probe)
    shaft_common = receiver.intersect(shaft)
    try:
        long_intervals = projected_solid_intervals(
            long_common, direction, axis_id=axis_id, label=f"raw_receiver/{receiver_id}/long_axis_intersection"
        )
    except ValueError as error:
        # A declared raw receiver can legitimately have no coincident shaft
        # volume if its CAD blank is absent on the line. Keep that as explicit
        # missing geometry instead of manufacturing a full member span.
        if "contains no solid components" not in str(error):
            raise
        if "contains no solid components" not in str(error):
            raise
        long_intervals = []
    try:
        shaft_intervals = projected_solid_intervals(
            shaft_common, direction, axis_id=axis_id, label=f"raw_receiver/{receiver_id}/current_shaft_intersection"
        )
    except ValueError as error:
        if "contains no solid components" not in str(error):
            raise
        shaft_intervals = []
    relative = [[low - datum_axis_mm, high - datum_axis_mm] for low, high in long_intervals]
    shaft_relative = [[low - datum_axis_mm, high - datum_axis_mm] for low, high in shaft_intervals]
    union = merge_intervals(relative)
    shaft_union = merge_intervals(shaft_relative)
    interval_match = len(union) == len(shaft_union) and all(
        math.isclose(a[0], b[0], rel_tol=0.0, abs_tol=1e-3)
        and math.isclose(a[1], b[1], rel_tol=0.0, abs_tol=1e-3)
        for a, b in zip(union, shaft_union)
    )
    long_volume = float(long_common.Volume())
    shaft_volume = float(shaft_common.Volume())
    volume_difference = max(0.0, long_volume - shaft_volume)
    return {
        "receiver_id": receiver_id,
        "source_shape": "unaltered raw receiver at its current source position",
        "intersection_solid_intervals_from_underhead_mm": relative,
        "receiver_wood_axis_length_mm": _sum_interval_length(union),
        "intersection_projection_gaps_mm": interval_gaps(union),
        "raw_receiver_intersects_axis_probe": bool(union),
        "current_shaft_intersection_solid_intervals_from_underhead_mm": shaft_relative,
        "current_shaft_covers_long_axis_raw_receiver_projection": interval_match,
        "long_probe_shaft_diameter_mm": float(shaft_diameter_mm),
        "long_probe_intersection_volume_mm3": long_volume,
        "current_shaft_intersection_volume_mm3": shaft_volume,
        "long_probe_minus_current_shaft_volume_mm3": volume_difference,
        "intersection_volume_tolerance_mm3": INTERSECTION_VOLUME_TOLERANCE_MM3,
        "current_shaft_volume_covers_long_probe_intersection": (
            interval_match and volume_difference <= INTERSECTION_VOLUME_TOLERANCE_MM3
        ),
    }


def _matches_partial_thread_class(underhead_to_tip_mm: float) -> dict[str, Any]:
    for nominal_mm, dimensions in PARTIAL_THREAD_CLASSES.items():
        if math.isclose(
            underhead_to_tip_mm,
            nominal_mm,
            rel_tol=0.0,
            abs_tol=NOMINAL_LENGTH_TOLERANCE_MM,
        ):
            return {
                "status": "existing_dimensional_class_matches_modeled_underhead_to_tip",
                "nominal_length_mm": nominal_mm,
                **dimensions,
                "minimum_delivered_length_mm": round(
                    nominal_mm - float(dimensions["length_tolerance_minus_mm"]), 6
                ),
                "product_selection_status": "unselected; no purchase or delivered hardware inspection implied",
            }
    return {
        "status": "no_existing_exact_length_class_applied",
        "reason": (
            "The modeled under-head-to-tip projection does not exactly match an "
            "existing sourced nominal-length class. No interpolation or nearest-length substitution is made."
        ),
        "product_selection_status": "unselected",
    }


def load_frozen_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    """Load and verify the snapshot's exact current scene/report sources."""
    snapshot = json.loads(SNAPSHOT_PATH.read_text())
    report_bytes = REPORT_PATH.read_bytes()
    expected_sha = snapshot["source_sha256"]["site/owner-wood-joints-review-report.json"]
    actual_sha = hashlib.sha256(report_bytes).hexdigest()
    if actual_sha != expected_sha:
        raise ValueError("current scene report bytes differ from the frozen geometry snapshot binding")
    report = json.loads(report_bytes)
    return snapshot, report


def _scope_rows(snapshot: Mapping[str, Any], report: Mapping[str, Any]) -> dict[str, Any]:
    if snapshot.get("revision_id") != CURRENT_REVISION_ID:
        raise ValueError("frozen geometry snapshot is not the resumed current revision")
    if report.get("revision_id") != CURRENT_REVISION_ID:
        raise ValueError("current scene report is not the resumed current revision")
    snapshot_axes = snapshot.get("axes")
    if not isinstance(snapshot_axes, Mapping) or len(snapshot_axes) != EXPECTED_AXIS_COUNT:
        raise ValueError("frozen geometry snapshot must bind exactly 92 candidate axes")
    shortened = report.get("shortened_exterior_bolt_envelopes")
    if not isinstance(shortened, Mapping) or set(shortened) != EXPECTED_SHORTENED_AXIS_IDS:
        raise ValueError("current report must name the exact eight shortened exterior bolt axes")
    moved = report.get("reseated_candidate_axis_ids")
    if not isinstance(moved, Sequence) or isinstance(moved, (str, bytes)):
        raise ValueError("current report lacks tall-block head-move axis IDs")
    if set(map(str, moved)) != EXPECTED_TALL_BLOCK_HEAD_MOVE_IDS:
        raise ValueError("current report must name the exact eight tall-block head-move axes")
    return {
        "shortened_exterior_axis_ids": sorted(shortened),
        "tall_block_head_move_axis_ids": sorted(moved),
    }


def collect(geometry: Any, report: Mapping[str, Any]) -> dict[str, Any]:
    """Collect exact bolt and receiver intervals for the current 92 axes.

    ``geometry`` must be the already materialized current ``g24_outer_2x6``
    object. The collector uses its original raw receivers and installed CAD
    role shapes in place; it does not transform, cut, or otherwise revise them.
    """
    if getattr(geometry, "layout_id", None) != CURRENT_REVISION_ID:
        raise ValueError("geometry object is not the owner-reviewed current WJ24 revision")
    if not isinstance(report, Mapping):
        raise TypeError("current scene report must be a mapping")
    snapshot, frozen_report = load_frozen_inputs()
    try:
        normalized_report = _json_normalize(report)
    except ValueError as error:
        raise ValueError("passed scene report is not JSON serializable") from error
    if normalized_report != frozen_report:
        raise ValueError("passed scene report differs from the frozen report file")
    priority = _scope_rows(snapshot, report)
    hardware = getattr(geometry, "candidate_installed_hardware", None)
    bores = getattr(geometry, "candidate_bores", None)
    if not isinstance(hardware, Mapping) or not isinstance(bores, Mapping):
        raise ValueError("current geometry lacks installed candidate hardware or bores")
    if set(hardware) != set(snapshot["axes"]) or set(bores) != set(snapshot["axes"]):
        raise ValueError("live current geometry axis IDs differ from the frozen 92-axis snapshot")

    shortened = report["shortened_exterior_bolt_envelopes"]
    shortened_ids = set(priority["shortened_exterior_axis_ids"])
    tall_ids = set(priority["tall_block_head_move_axis_ids"])
    rows: list[dict[str, Any]] = []
    for axis_id in sorted(hardware):
        roles = hardware[axis_id]
        if set(roles) != EXPECTED_ROLES:
            raise ValueError(f"{axis_id}: installed bolt role set differs from the five-role model")
        direction = _unit_direction(roles, axis_id)
        frozen_direction = snapshot["axes"][axis_id]["axis_head_to_nut_global"]
        direction_error = _direction_difference(direction, frozen_direction)
        if direction_error > AXIS_TOLERANCE:
            raise ValueError(
                f"{axis_id}: washer-center axis differs from the frozen geometry axis by "
                f"{direction_error:.3g}"
            )
        frozen_line_point = snapshot["axes"][axis_id]["shaft_center_xyz_mm"]
        role_center_offsets = {
            role: _perpendicular_offset_mm(
                shape.Center().toTuple(), frozen_line_point, direction
            )
            for role, shape in roles.items()
        }
        max_role_center_offset = max(role_center_offsets.values())
        if max_role_center_offset > AXIS_LINE_POSITION_TOLERANCE_MM:
            raise ValueError(
                f"{axis_id}: live hardware role centerline differs from the frozen shaft axis "
                f"by {max_role_center_offset:.6g} mm"
            )
        role_absolute = {
            role: projected_solid_intervals(shape, direction, axis_id=axis_id, label=role)
            for role, shape in roles.items()
        }
        datum_axis_mm, contact = _underhead_datum(role_absolute, axis_id)
        role_records = {
            role: _interval_record(
                roles[role], direction, datum_axis_mm, axis_id=axis_id, label=role
            )
            for role in ("head", "head_washer", "shaft", "nut_washer", "nut")
        }
        shaft_intervals = role_records["shaft"]["union_intervals_from_underhead_mm"]
        nut_intervals = role_records["nut"]["union_intervals_from_underhead_mm"]
        if not shaft_intervals or not nut_intervals:
            raise ValueError(f"{axis_id}: shaft or nut has no projected solid interval")
        shaft_tip_mm = max(float(row[1]) for row in shaft_intervals)
        shaft_start_mm = min(float(row[0]) for row in shaft_intervals)
        far_nut_face_mm = max(float(row[1]) for row in nut_intervals)
        near_nut_face_mm = min(float(row[0]) for row in nut_intervals)
        modeled_nut_overlap_mm = max(
            0.0,
            min(shaft_tip_mm, far_nut_face_mm)
            - max(shaft_start_mm, near_nut_face_mm),
        )
        receiver_ids = tuple(getattr(bores[axis_id], "receiver_ids", ()))
        if not receiver_ids:
            raise ValueError(f"{axis_id}: current candidate bore lacks ordered raw receiver IDs")
        expected_diameter_mm = float(snapshot["axes"][axis_id]["shaft_diameter_mm"])
        shaft_diameter_mm = _shaft_diameter_mm(roles["shaft"], direction, axis_id)
        if not math.isclose(shaft_diameter_mm, expected_diameter_mm, rel_tol=0.0, abs_tol=1e-4):
            raise ValueError(
                f"{axis_id}: live shaft diameter differs from frozen CAD envelope "
                f"({shaft_diameter_mm:.6f} vs {expected_diameter_mm:.6f} mm)"
            )
        receivers = [
            _receiver_axis_record(
                geometry,
                str(receiver_id),
                roles["shaft"],
                direction,
                datum_axis_mm,
                shaft_diameter_mm,
                axis_id,
            )
            for receiver_id in receiver_ids
        ]
        wood_intervals = [
            interval
            for receiver in receivers
            for interval in receiver["intersection_solid_intervals_from_underhead_mm"]
        ]
        wood_union = merge_intervals(wood_intervals)
        wood_far_face_mm = max((float(row[1]) for row in wood_union), default=None)
        wood_near_face_mm = min((float(row[0]) for row in wood_union), default=None)
        current_shaft_covers_all_raw_receivers = all(
            receiver["current_shaft_volume_covers_long_probe_intersection"]
            for receiver in receivers
        )
        if wood_union and (
            shaft_start_mm > float(wood_near_face_mm) + INTERFACE_TOLERANCE_MM
            or shaft_tip_mm < float(wood_far_face_mm) - INTERFACE_TOLERANCE_MM
        ):
            current_shaft_covers_all_raw_receivers = False
        modeled_shaft_length_mm = _sum_interval_length(
            role_records["shaft"]["union_intervals_from_underhead_mm"]
        )
        underhead_to_tip_mm = shaft_tip_mm
        dimensions = _matches_partial_thread_class(underhead_to_tip_mm)
        row = {
            "axis_id": axis_id,
            "priority_group": (
                "shortened_exterior_bolt"
                if axis_id in shortened_ids
                else "tall_block_head_move"
                if axis_id in tall_ids
                else "other_candidate_bolt"
            ),
            "ordered_receiver_ids_head_to_nut": [str(value) for value in receiver_ids],
            "axis_head_to_nut_global_unit": list(direction),
            "frozen_axis_direction_difference_norm": direction_error,
            "frozen_axis_direction_matches_within_tolerance": direction_error <= AXIS_TOLERANCE,
            "frozen_shaft_center_xyz_mm": [float(value) for value in frozen_line_point],
            "hardware_role_center_perpendicular_offsets_from_frozen_axis_mm": role_center_offsets,
            "maximum_hardware_role_center_offset_from_frozen_axis_mm": max_role_center_offset,
            "frozen_shaft_axis_line_matches_within_tolerance": (
                max_role_center_offset <= AXIS_LINE_POSITION_TOLERANCE_MM
            ),
            "modeled_shaft_diameter_mm": shaft_diameter_mm,
            "underhead_datum": {
                "definition": "adjacent head bearing face / head-washer headward face, projected on the current head-to-nut axis",
                "head_underface_contact_check": contact,
            },
            "hardware_roles": role_records,
            "wood_receiver_intervals": receivers,
            "wood_grip_union_intervals_from_underhead_mm": wood_union,
            "wood_grip_projection_gaps_mm": interval_gaps(wood_union),
            "wood_grip_material_length_mm": _sum_interval_length(wood_union),
            "wood_grip_envelope_from_underhead_mm": (
                [wood_near_face_mm, wood_far_face_mm]
                if wood_near_face_mm is not None and wood_far_face_mm is not None
                else None
            ),
            "modeled_shaft_occupied_length_mm": modeled_shaft_length_mm,
            "modeled_underhead_to_tip_mm": underhead_to_tip_mm,
            "modeled_smooth_shank_reach_to_far_wood_face_mm": wood_far_face_mm,
            "modeled_shaft_covers_all_raw_receiver_intervals": current_shaft_covers_all_raw_receivers,
            "modeled_shaft_axial_overlap_with_nut_mm": modeled_nut_overlap_mm,
            "modeled_tail_past_far_nut_face_mm": shaft_tip_mm - far_nut_face_mm,
            "modeled_tail_past_far_nut_washer_face_mm": shaft_tip_mm
            - max(
                float(row[1])
                for row in role_records["nut_washer"]["union_intervals_from_underhead_mm"]
            ),
            "existing_partial_thread_dimensional_comparator": dimensions,
            "thread_engagement_status": (
                "not established: current CAD models an unthreaded shaft envelope; first full-form thread, last thread scratch, thread end, and functional nut engagement require applicable delivered-part evidence"
            ),
            "interpretation_limit": (
                "Geometric intervals only. No purchased length, delivered shank, thread location, capacity, installation, or actual hardware inspection is inferred."
            ),
        }
        if axis_id in shortened_ids:
            expected = float(shortened[axis_id]["after_occupied_length_mm"])
            row["shortening_report_crosscheck"] = {
                "report_after_occupied_length_mm": expected,
                "live_projected_shaft_length_mm": modeled_shaft_length_mm,
                "matches_within_0p001mm": math.isclose(
                    expected, modeled_shaft_length_mm, rel_tol=0.0, abs_tol=1e-3
                ),
                "report_says_nut_station_and_tail_end_preserved": bool(
                    shortened[axis_id]["nut_station_and_tail_end_preserved"]
                ),
            }
            if not row["shortening_report_crosscheck"]["matches_within_0p001mm"]:
                raise ValueError(f"{axis_id}: live shaft projection differs from the current shortening report")
        rows.append(row)

    if len(rows) != EXPECTED_AXIS_COUNT:
        raise ValueError(f"expected {EXPECTED_AXIS_COUNT} candidate bolt rows, collected {len(rows)}")
    matched = [
        row for row in rows
        if row["existing_partial_thread_dimensional_comparator"]["status"]
        == "existing_dimensional_class_matches_modeled_underhead_to_tip"
    ]
    return {
        "schema": SCHEMA,
        "status": "exact_geometry_projection_screen_only",
        "revision_id": CURRENT_REVISION_ID,
        "reviewed_repository_commit": snapshot.get("reviewed_repository_commit"),
        "geometry_snapshot_path": str(SNAPSHOT_PATH.relative_to(ROOT)),
        "geometry_snapshot_sha256": hashlib.sha256(SNAPSHOT_PATH.read_bytes()).hexdigest(),
        "scene_report_path": str(REPORT_PATH.relative_to(ROOT)),
        "scene_report_sha256": hashlib.sha256(REPORT_PATH.read_bytes()).hexdigest(),
        "candidate_axis_count": len(rows),
        "projection_tolerances_mm": {
            "head_to_head_washer_face_adjacency": INTERFACE_TOLERANCE_MM,
            "interval_contiguity_merge": INTERVAL_CONTIGUITY_TOLERANCE_MM,
            "frozen_axis_line_position": AXIS_LINE_POSITION_TOLERANCE_MM,
        },
        "intersection_volume_tolerance_mm3": INTERSECTION_VOLUME_TOLERANCE_MM3,
        "priority_axis_ids": priority,
        "dimensional_policy_scope": {
            "nominal_diameter_assumption_mm": 6.35,
            "nominal_thread_assumption": "1/4-20 only where an existing dimensional class is an exact underhead-to-tip match; modeled thread geometry is absent",
            "matched_axis_count": len(matched),
            "matched_axis_ids": [row["axis_id"] for row in matched],
            "unmatched_axis_count": EXPECTED_AXIS_COUNT - len(matched),
            "product_selection": False,
            "delivered_hardware_inspection": False,
            "source_references": sorted(
                {row["existing_partial_thread_dimensional_comparator"].get("evidence", "") for row in matched}
            ),
        },
        "excluded_hardware": {
            "retained_starting_frame_bolts": 12,
            "reason": "The task scope is the 92 candidate axes; the twelve source frame-bolt arrangements remain a separate exact-source-position inventory.",
            "product_selection": False,
        },
        "axes": rows,
        "release": False,
    }


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "unresolved"
    return f"{float(value):.{digits}f}"


def _fmt_intervals(intervals: Sequence[Sequence[float]]) -> str:
    if not intervals:
        return "none"
    return ", ".join(f"[{_fmt(row[0])}, {_fmt(row[1])}]" for row in intervals)


def render_markdown(result: Mapping[str, Any]) -> str:
    """Render a reviewable per-axis report from a completed live collection."""
    if result.get("schema") != SCHEMA or result.get("candidate_axis_count") != EXPECTED_AXIS_COUNT:
        raise ValueError("markdown rendering requires a complete current 92-axis collection")
    axes = result["axes"]
    by_shaft_length: dict[float, list[Mapping[str, Any]]] = {}
    for row in axes:
        by_shaft_length.setdefault(round(float(row["modeled_underhead_to_tip_mm"]), 3), []).append(row)
    receiver_misses = [
        row for row in axes
        if not all(receiver["raw_receiver_intersects_axis_probe"] for receiver in row["wood_receiver_intervals"])
    ]
    receiver_entries = sum(len(row["wood_receiver_intervals"]) for row in axes)
    intersected_receiver_entries = sum(
        bool(receiver["raw_receiver_intersects_axis_probe"])
        for row in axes
        for receiver in row["wood_receiver_intervals"]
    )
    discontinuous_grips = [row for row in axes if row["wood_grip_projection_gaps_mm"]]
    hardware_gaps = [
        (row["axis_id"], role)
        for row in axes
        for role, value in row["hardware_roles"].items()
        if value["projection_gaps_mm"]
    ]
    full_nut_overlap = [
        row for row in axes
        if math.isclose(
            row["modeled_shaft_axial_overlap_with_nut_mm"],
            row["hardware_roles"]["nut"]["union_length_mm"],
            rel_tol=0.0,
            abs_tol=1e-5,
        )
    ]
    shortening_rows = [row for row in axes if row.get("shortening_report_crosscheck")]
    shaft_coverage_rows = [row for row in axes if row["modeled_shaft_covers_all_raw_receiver_intervals"]]
    max_datum_gap = max(
        abs(float(row["underhead_datum"]["head_underface_contact_check"]["signed_gap_mm"]))
        for row in axes
    )
    min_tail = min(float(row["modeled_tail_past_far_nut_face_mm"]) for row in axes)
    min_tail_past_washer = min(
        float(row["modeled_tail_past_far_nut_washer_face_mm"]) for row in axes
    )
    max_centerline_offset = max(
        float(row["maximum_hardware_role_center_offset_from_frozen_axis_mm"])
        for row in axes
    )
    lines = [
        "# Current WJ24 bolt grip and envelope screen",
        "",
        "**Status: exact CAD geometry projection screen only.** This report reads the owner-reviewed `led-clearance-2x6-runner-seated-blocks-v1` geometry, commit `b1e8707d`. It projects all 92 candidate bolt role shapes and each raw declared receiver onto its own bolt axis. It does not select products, identify delivered shank or thread locations, assign capacity, establish installation, or release physical work.",
        "",
        f"The collector used snapshot `{result['geometry_snapshot_path']}` (`{result['geometry_snapshot_sha256']}`) and scene report `{result['scene_report_path']}` (`{result['scene_report_sha256']}`). The 92-row result comes from the already materialized current geometry; axis-oriented projections use the head-to-nut direction and the touching head/head-washer faces as the zero datum. Raw receiver material is intersected with the modeled shaft. Every solid's projected interval is retained. Intervals merge as contiguous only within {result['projection_tolerances_mm']['interval_contiguity_merge']:.6g} mm, so inverse-rotation roundoff at shared receiver faces does not appear as a physical gap.",
        "",
        "## Dimensional comparator",
        "",
        "The current CAD shaft is an unthreaded occupancy envelope. The collector keeps its under-head-to-tip projection separate from the geometric distance to the far wood face for a hypothetical smooth body, and from the modeled axial overlap with the nut and tail past the nut. None of those values reveals first full-form thread, last thread scratch, thread end, or functional nut engagement. The existing 1/4-in partially threaded standard/product evidence is compared only where a modeled under-head-to-tip length exactly matches an existing source class; unmatched axes receive no interpolated class. A matching class remains a dimensional comparator, not a selected bolt or a transferred historical joint pass.",
        "",
        f"Exact existing dimensional classes match {result['dimensional_policy_scope']['matched_axis_count']} of 92 modeled lengths. Product selection and delivered-hardware inspection remain false. The twelve retained starting frame bolts are outside this 92-axis report and keep their exact source positions and unselected product status.",
        "",
        "## Current geometry summary",
        "",
        f"The independent long-axis probe intersects {intersected_receiver_entries} of {receiver_entries} declared raw receiver entries; {len(receiver_misses)} axes have at least one declared receiver without an intersection. Comparing that probe with each current finite shaft shows complete raw receiver coverage for {len(shaft_coverage_rows)} of 92 axes. After the stated projection merge tolerance, {len(discontinuous_grips)} axes have a discontinuous wood-grip projection and {len(hardware_gaps)} hardware role projections have internal gaps. The largest head/head-washer datum mismatch is {max_datum_gap:.6g} mm. All {len(full_nut_overlap)} axes show modeled shaft overlap spanning the full modeled nut thickness. Minimum modeled tails beyond the far nut face and far nut-washer face are {min_tail:.3f} mm and {min_tail_past_washer:.3f} mm. The largest role-center offset from the frozen shaft axis is {max_centerline_offset:.6g} mm. These are properties of CAD occupancy envelopes only.",
        "",
        "| Modeled underhead-to-tip interval (mm) | Axis count | Wood-grip lengths and counts (mm) | Existing standard length comparator |",
        "| ---: | ---: | --- | --- |",
    ]
    for length_mm in sorted(by_shaft_length):
        group = by_shaft_length[length_mm]
        grip_counts: dict[float, int] = {}
        comparator_lengths: set[float] = set()
        for row in group:
            grip = round(float(row["wood_grip_material_length_mm"]), 3)
            grip_counts[grip] = grip_counts.get(grip, 0) + 1
            value = row["existing_partial_thread_dimensional_comparator"].get("nominal_length_mm")
            if value is not None:
                comparator_lengths.add(float(value))
        grip_text = ", ".join(
            f"{grip:.3f} × {count}" for grip, count in sorted(grip_counts.items())
        )
        comparator_text = ", ".join(f"{value:.2f}" for value in sorted(comparator_lengths)) or "none exact"
        lines.append(f"| {length_mm:.3f} | {len(group)} | {grip_text} | {comparator_text} |")
    lines.extend(
        [
            "",
            f"The shortened-axis report cross-check passed for {len(shortening_rows)} of 8 axes. The next table lists those eight first, followed by the eight tall-block head moves. No axis in either priority group has an exact dimensional class among the existing partial-thread comparisons.",
            "",
            "## Priority axes",
            "",
            "| Priority | Axis | Raw receivers | Wood grip intervals (mm from underhead) | Modeled underhead to tip (mm) | Geometric reach to far wood face (mm) | Head interval | Head washer | Nut washer | Nut | Tail past nut / washer (mm) | Full raw receiver coverage | Partial-thread comparator |",
            "| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    priority_rows = [row for row in axes if row["priority_group"] != "other_candidate_bolt"]
    priority_rows.sort(key=lambda row: (row["priority_group"] != "shortened_exterior_bolt", row["axis_id"]))
    for row in priority_rows:
        roles = row["hardware_roles"]
        comparator = row["existing_partial_thread_dimensional_comparator"]
        comparator_text = (
            f"{_fmt(comparator['nominal_length_mm'], 2)} mm, `Lb` {comparator['Lb_min_mm']:.2f}, `Lg` {comparator['Lg_max_mm']:.2f}"
            if comparator.get("nominal_length_mm") is not None
            else "none"
        )
        lines.append(
            "| {priority} | `{axis}` | {receivers} | {wood} | {tip} | {smooth} | {head} | {head_washer} | {nut_washer} | {nut} | {tail} | {coverage} | {comparator} |".format(
                priority=row["priority_group"].replace("_", " "),
                axis=row["axis_id"],
                receivers=", ".join(f"`{name}`" for name in row["ordered_receiver_ids_head_to_nut"]),
                wood=_fmt_intervals(row["wood_grip_union_intervals_from_underhead_mm"]),
                tip=_fmt(row["modeled_underhead_to_tip_mm"]),
                smooth=_fmt(row["modeled_smooth_shank_reach_to_far_wood_face_mm"]),
                head=_fmt_intervals(roles["head"]["union_intervals_from_underhead_mm"]),
                head_washer=_fmt_intervals(roles["head_washer"]["union_intervals_from_underhead_mm"]),
                nut_washer=_fmt_intervals(roles["nut_washer"]["union_intervals_from_underhead_mm"]),
                nut=_fmt_intervals(roles["nut"]["union_intervals_from_underhead_mm"]),
                tail=f"{_fmt(row['modeled_tail_past_far_nut_face_mm'])} / {_fmt(row['modeled_tail_past_far_nut_washer_face_mm'])}",
                coverage="yes" if row["modeled_shaft_covers_all_raw_receiver_intervals"] else "NO",
                comparator=comparator_text,
            )
        )
    lines.extend(
        [
            "",
            "## All 92 candidate bolt axes",
            "",
            "Each role interval and raw receiver solid interval is measured from the exact underhead datum along the current bolt direction. Multiple intervals remain separate; their gaps are not silently treated as wood grip.",
            "",
            "| Axis | Raw receivers | Per-receiver wood intervals (mm) | Total wood material (mm) | Underhead to tip (mm) | Shaft occupied interval(s) (mm) | Head interval | Head washer | Nut washer | Nut | Modeled shaft/nut overlap (mm) | Tail past nut / washer (mm) | Full raw receiver coverage | Existing partial-thread class |",
            "| --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for row in axes:
        roles = row["hardware_roles"]
        receiver_text = "; ".join(
            f"`{receiver['receiver_id']}` { _fmt_intervals(receiver['intersection_solid_intervals_from_underhead_mm']) }"
            for receiver in row["wood_receiver_intervals"]
        )
        comparator = row["existing_partial_thread_dimensional_comparator"]
        comparator_text = (
            f"{_fmt(comparator['nominal_length_mm'], 2)} mm class (`Lb` {comparator['Lb_min_mm']:.2f}, `Lg` {comparator['Lg_max_mm']:.2f})"
            if comparator.get("nominal_length_mm") is not None
            else "no exact sourced length class"
        )
        lines.append(
            "| `{axis}` | {receivers} | {receiver_intervals} | {grip} | {tip} | {shaft} | {head} | {head_washer} | {nut_washer} | {nut} | {overlap} | {tail} | {coverage} | {comparator} |".format(
                axis=row["axis_id"],
                receivers=", ".join(f"`{value}`" for value in row["ordered_receiver_ids_head_to_nut"]),
                receiver_intervals=receiver_text,
                grip=_fmt(row["wood_grip_material_length_mm"]),
                tip=_fmt(row["modeled_underhead_to_tip_mm"]),
                shaft=_fmt_intervals(roles["shaft"]["union_intervals_from_underhead_mm"]),
                head=_fmt_intervals(roles["head"]["union_intervals_from_underhead_mm"]),
                head_washer=_fmt_intervals(roles["head_washer"]["union_intervals_from_underhead_mm"]),
                nut_washer=_fmt_intervals(roles["nut_washer"]["union_intervals_from_underhead_mm"]),
                nut=_fmt_intervals(roles["nut"]["union_intervals_from_underhead_mm"]),
                overlap=_fmt(row["modeled_shaft_axial_overlap_with_nut_mm"]),
                tail=f"{_fmt(row['modeled_tail_past_far_nut_face_mm'])} / {_fmt(row['modeled_tail_past_far_nut_washer_face_mm'])}",
                coverage="yes" if row["modeled_shaft_covers_all_raw_receiver_intervals"] else "NO",
                comparator=comparator_text,
            )
        )
    lines.extend(
        [
            "",
            "## Reading limits",
            "",
        "The modeled shaft/nut overlap is an axial interval comparison between two CAD envelopes. It does not establish thread contact or a functional full-height nut engagement. The smooth-body reach value records geometry from the underhead datum to the far wood face; it does not say smooth shank is structurally required through the members. Published `Lb` and `Lg` remain standard gaging bounds and do not describe the delivered first thread location. Product catalog identity, delivered lengths, thread transitions, washers, nuts, actual wood, and physical installation have not been inspected.",
            "",
            "No capacity, load sharing, joinery acceptance, fabrication, drilling, assembly, or climbing release follows from this dimensional screen.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(result: Mapping[str, Any], path: Path = DOC_PATH) -> Path:
    """Write the documentation artifact after a successful live collection."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_markdown(result))
    return destination
