"""Join frozen source axes to finished timber cylinder patches by metadata only.

This module never imports or replays STEP geometry. It checks pinned source
file bytes, including STEP files. The surface producer owns the
face extraction; this consumer validates source identities and evaluates bounded
axis-to-cylinder correspondence from its JSON report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
ATTEMPT_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    / "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
)
DEFAULT_SURFACES = ATTEMPT_DIR / "surfaces.json"
DEFAULT_SURFACE_PRODUCER = ATTEMPT_DIR / "surfaces.py"
DEFAULT_MEMBER_BUNDLE = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    / "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
)
DEFAULT_SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
DEFAULT_RECEIVER_SOURCE = ROOT / "scripts/wood_joint_current_receiver_screen.py"
DEFAULT_COMPOSITOR_SOURCE = ROOT / "scripts/wood_joint_wj24_compositor.py"
DEFAULT_MANIFEST_PRODUCER = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    / "current-full-frame-input-manifest-attempt04/produce.py"
)
DEFAULT_OUTPUT = ATTEMPT_DIR / "axis-features.json"
DEFAULT_PINS = ATTEMPT_DIR / "axis-source-pins.json"
MANIFEST_SHA256 = "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11"
MEMBER_BUNDLE_SHA256 = (
    "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420"
)

AXIS_DIRECTION_SINE_TOLERANCE = 1.0e-6
AXIS_CENTERLINE_TOLERANCE_MM = 1.0e-5
PATCH_CONTAINMENT_TOLERANCE_MM = 1.0e-5
STOCK_FRAME_ORTHONORMAL_TOLERANCE = 1.0e-5
EXPECTED_GROUP_COUNTS = {
    "candidate_bolt_axes": 92,
    "retained_frame_bolt_axes": 12,
    "panel_kicker_screw_axes": 66,
}
EXPECTED_MOVED_SCREW_IDS = frozenset(
    {
        *(
            f"round_panel_lower_{side}_edge_{index}"
            for side in ("left", "right")
            for index in (1, 2)
        ),
        *(
            f"round_kicker_{side}_center_{index}"
            for side in ("left", "right")
            for index in (1, 2)
        ),
    }
)


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode(
        "utf-8"
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _verify_surface_pin_files(document: Mapping[str, Any], root: Path) -> None:
    """Check every surface-source byte binding without importing a CAD runtime."""
    pins = document.get("pins")
    if not isinstance(pins, Mapping) or not pins:
        raise ValueError("surface source pins must contain a nonempty pin map")
    for name, pin in pins.items():
        if not isinstance(pin, Mapping):
            raise TypeError(f"surface source pin {name} must be an object")
        source_path = pin.get("path")
        if not isinstance(source_path, str) or not source_path:
            raise ValueError(f"surface source pin {name} lacks a source path")
        raw = (root / source_path).read_bytes()
        if len(raw) != pin.get("size_bytes") or _sha256_bytes(raw) != pin.get("sha256"):
            raise ValueError(f"surface pinned source bytes changed: {source_path}")


def _number(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a finite number") from error
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def _vec3(value: Any, label: str) -> tuple[float, float, float]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 3
    ):
        raise ValueError(f"{label} must contain three coordinates")
    return tuple(_number(component, label) for component in value)  # type: ignore[return-value]


def _dot(first: Sequence[float], second: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(first, second, strict=True))


def _sub(first: Sequence[float], second: Sequence[float]) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(first, second, strict=True))  # type: ignore[return-value]


def _add_scaled(
    point: Sequence[float], direction: Sequence[float], distance: float
) -> tuple[float, float, float]:
    return tuple(p + d * distance for p, d in zip(point, direction, strict=True))  # type: ignore[return-value]


def _cross(
    first: Sequence[float], second: Sequence[float]
) -> tuple[float, float, float]:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _unit(value: Any, label: str) -> tuple[float, float, float]:
    vector = _vec3(value, label)
    norm = _norm(vector)
    if norm <= 0.0:
        raise ValueError(f"{label} must have nonzero length")
    return tuple(component / norm for component in vector)  # type: ignore[return-value]


def _sorted_ids(records: Sequence[Mapping[str, Any]], label: str) -> list[str]:
    ids = [str(row.get("axis_id", "")) for row in records]
    if any(not value for value in ids):
        raise ValueError(f"{label} contains an empty axis_id")
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label} contains duplicate axis IDs")
    return sorted(ids)


def _stock_frame(record: Mapping[str, Any]) -> dict[str, Any]:
    stock = record.get("stock_frame")
    if not isinstance(stock, Mapping):
        raise TypeError(f"{record.get('member_id')}: missing stock_frame")
    origin = _vec3(stock.get("origin_global_xyz_mm"), "stock-frame origin")
    raw_basis = stock.get("basis_columns_global_xyz")
    if not isinstance(raw_basis, Sequence) or len(raw_basis) != 3:
        raise ValueError(
            f"{record.get('member_id')}: stock basis needs g, q, r columns"
        )
    raw_columns = tuple(_vec3(column, "stock basis column") for column in raw_basis)
    for column in raw_columns:
        if abs(_norm(column) - 1.0) > STOCK_FRAME_ORTHONORMAL_TOLERANCE:
            raise ValueError(
                f"{record.get('member_id')}: stock basis column is not unit"
            )
    basis = raw_columns
    for i, first in enumerate(basis):
        if abs(_norm(first) - 1.0) > STOCK_FRAME_ORTHONORMAL_TOLERANCE:
            raise ValueError(
                f"{record.get('member_id')}: stock basis column is not unit"
            )
        for second in basis[i + 1 :]:
            if abs(_dot(first, second)) > STOCK_FRAME_ORTHONORMAL_TOLERANCE:
                raise ValueError(
                    f"{record.get('member_id')}: stock basis is not orthogonal"
                )
    handedness = _dot(basis[0], _cross(basis[1], basis[2]))
    if handedness <= 0.0 or abs(handedness - 1.0) > STOCK_FRAME_ORTHONORMAL_TOLERANCE:
        raise ValueError(f"{record.get('member_id')}: stock basis must be right-handed")
    dimensions = _vec3(
        stock.get("original_dimensions_gqr_mm"), "stock-frame original dimensions"
    )
    if any(value <= 0.0 for value in dimensions):
        raise ValueError(
            f"{record.get('member_id')}: stock-frame dimensions must be positive"
        )
    result = {
        "origin_global_xyz_mm": list(origin),
        "basis_columns_global_xyz": [list(column) for column in basis],
        "original_dimensions_gqr_mm": list(dimensions),
    }
    for field in ("basis_source", "datum_status", "original_stock_bounds_in_basis_mm"):
        if field in stock:
            result[field] = stock[field]
    return result


def _to_stock_coordinates(
    point: Sequence[float], stock: Mapping[str, Any]
) -> tuple[float, float, float]:
    origin = stock["origin_global_xyz_mm"]
    relative = _sub(point, origin)
    return tuple(_dot(relative, column) for column in stock["basis_columns_global_xyz"])  # type: ignore[return-value]


def _direction_to_stock(
    direction: Sequence[float], stock: Mapping[str, Any]
) -> tuple[float, float, float]:
    return tuple(
        _dot(direction, column) for column in stock["basis_columns_global_xyz"]
    )  # type: ignore[return-value]


def _physical_member_map(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = manifest.get("physical_members")
    if not isinstance(rows, list):
        raise TypeError("manifest has no physical_members list")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        member_id = str(row.get("member_id", ""))
        if not member_id or member_id in result:
            raise ValueError(
                "manifest physical_members has empty or duplicate member IDs"
            )
        result[member_id] = dict(row)
    return result


def _validate_surface_inventory(
    surfaces_report: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    require_full_inventory: bool,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    records = surfaces_report.get("records")
    if not isinstance(records, list):
        raise TypeError("surface report has no records list")
    surface_by_member: dict[str, dict[str, Any]] = {}
    for raw in records:
        if not isinstance(raw, Mapping):
            raise TypeError("surface report record must be an object")
        member_id = str(raw.get("member_id", ""))
        if not member_id or member_id in surface_by_member:
            raise ValueError("surface report has empty or duplicate member IDs")
        surface_by_member[member_id] = dict(raw)

    physical = _physical_member_map(manifest)
    wood_members = {
        member_id: row
        for member_id, row in physical.items()
        if row.get("member_kind") == "timber"
    }
    panel_ids = sorted(
        member_id
        for member_id, row in physical.items()
        if row.get("member_kind") == "panel"
    )
    block_ids = {
        str(row.get("part_id")) for row in manifest.get("candidate_blocks", [])
    }
    if require_full_inventory:
        if len(wood_members) != 44:
            raise ValueError(
                f"manifest must contain 44 current wood members, got {len(wood_members)}"
            )
        if len(block_ids) != 24:
            raise ValueError(
                f"manifest must contain 24 candidate blocks, got {len(block_ids)}"
            )
        if len(panel_ids) != 6:
            raise ValueError(
                f"manifest must contain six excluded plywood panels, got {len(panel_ids)}"
            )
        expected_ids = set(wood_members)
        if set(surface_by_member) != expected_ids:
            missing = sorted(expected_ids - set(surface_by_member))
            extra = sorted(set(surface_by_member) - expected_ids)
            raise ValueError(
                f"surface member inventory mismatch: missing={missing}; extra={extra}"
            )
        if block_ids - expected_ids:
            raise ValueError(
                "candidate block IDs are absent from the current wood member set"
            )

    for member_id, row in surface_by_member.items():
        source = wood_members.get(member_id)
        if source is None:
            if require_full_inventory:
                raise ValueError(f"surface report includes non-wood member {member_id}")
            continue
        expected_binding = source.get("current_finished_step_binding") or {}
        actual_binding = row.get("step_binding") or {}
        for field in ("path", "file_sha256"):
            if expected_binding.get(field) != actual_binding.get(field):
                raise ValueError(
                    f"{member_id}: surface STEP {field} differs from manifest binding"
                )
        if actual_binding.get("manifest_roundtrip_valid") is not True:
            raise ValueError(f"{member_id}: STEP round-trip is not marked valid")
        if actual_binding.get("solid_count") != 1:
            raise ValueError(f"{member_id}: expected one solid in surface STEP binding")
        if not isinstance(row.get("features"), list):
            raise TypeError(f"{member_id}: surface report has no features list")
        _stock_frame(row)
        feature_ids = [
            str(feature.get("feature_id", "")) for feature in row["features"]
        ]
        if any(
            not feature_id.startswith(f"{member_id}/facet")
            for feature_id in feature_ids
        ):
            raise ValueError(
                f"{member_id}: feature IDs must be stable member/facet IDs"
            )
        if len(feature_ids) != len(set(feature_ids)):
            raise ValueError(f"{member_id}: duplicate feature IDs")
    return surface_by_member, {
        "physical_members": physical,
        "wood_members": wood_members,
        "panel_ids": panel_ids,
        "block_ids": sorted(block_ids),
    }


def _axis_inputs(
    group: str,
    row: Mapping[str, Any],
    *,
    source_inventory_axes: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    axis_id = str(row.get("axis_id", ""))
    if not axis_id:
        raise ValueError(f"{group} has an empty axis_id")
    if group == "candidate_bolt_axes":
        geometry = row.get("geometry") or {}
        datum = _vec3(
            geometry.get("shaft_center_global_xyz_mm"), f"{axis_id} shaft center"
        )
        direction = _unit(
            geometry.get("axis_head_to_nut_global"), f"{axis_id} axis direction"
        )
        length = _number(
            geometry.get("modeled_shaft_occupied_length_mm"),
            f"{axis_id} modeled length",
        )
        if length <= 0.0:
            raise ValueError(f"{axis_id}: modeled shaft length must be positive")
        low, high = -length / 2.0, length / 2.0
        extent_source = {
            "field": "geometry.modeled_shaft_occupied_length_mm",
            "datum_field": "geometry.shaft_center_global_xyz_mm",
            "interval_semantics": "centered on the explicitly named shaft center",
            "interval_role": "modeled shaft occupancy envelope",
        }
        receivers = row.get("receiver_member_ids")
        diameter = geometry.get("modeled_shaft_diameter_mm")
        panel_member = None
    elif group == "retained_frame_bolt_axes":
        datum = _vec3(row.get("origin_global_xyz_mm"), f"{axis_id} recorded origin")
        direction = _unit(row.get("axis_global_xyz"), f"{axis_id} axis direction")
        length = _number(
            row.get("source_occupied_length_mm"), f"{axis_id} source length"
        )
        if length <= 0.0:
            raise ValueError(f"{axis_id}: source occupied length must be positive")
        low, high = 0.0, length
        extent_source = {
            "field": "source_occupied_length_mm",
            "datum_field": "origin_global_xyz_mm",
            "interval_semantics": "from the recorded Connection.start/origin along axis_global_xyz",
            "interval_role": "source modeled component-cylinder envelope; not delivered shank",
        }
        receivers = row.get("members_as_recorded")
        diameter = row.get("source_occupied_diameter_mm")
        panel_member = None
    elif group == "panel_kicker_screw_axes":
        datum = _vec3(row.get("origin_global_xyz_mm"), f"{axis_id} recorded origin")
        direction = _unit(row.get("axis_global_xyz"), f"{axis_id} axis direction")
        axis_record = source_inventory_axes.get(axis_id)
        if axis_record is None:
            length = None
            low, high = None, None
            extent_source = {
                "field": None,
                "datum_field": "origin_global_xyz_mm",
                "interval_semantics": "unresolved without the pinned current source inventory",
                "interval_role": "no current finite extent supplied",
            }
        else:
            length = _number(
                axis_record.get("shop_purchased_length_mm"),
                f"{axis_id} STEP cutter length",
            )
            purchased = _number(
                row.get("purchased_nominal_length_mm"), f"{axis_id} nominal length"
            )
            if abs(length - purchased) > 1.0e-9:
                raise ValueError(
                    f"{axis_id}: current source STEP cutter length differs from manifest nominal field"
                )
            low, high = 0.0, length
            extent_source = {
                "field": "manifest.purchased_nominal_length_mm reconciled to source_inventory.shop_purchased_length_mm",
                "manifest_crosscheck_field": "purchased_nominal_length_mm",
                "datum_field": "origin_global_xyz_mm",
                "interval_semantics": "current receiver screen uses the source shop length on the current axis datum and direction",
                "interval_role": "current source axis envelope metadata only; an exact finished-surface match is required to associate a patch",
                "source_step_cut_semantics": "the pinned member-solids _finished_source_hosts cutter uses shop_purchased_length_mm from the source Connection.start; moved stations are owner-directed axis metadata and do not inherit a source-station cut",
                "historical_proxy_occupied_length_mm": (
                    row.get("historical_source_inventory_record") or {}
                ).get("source_occupied_length_mm"),
                "historical_proxy_used_for_current_extent": False,
            }
        receivers = [row.get("receiver_member")]
        diameter = None
        panel_member = row.get("panel_member")
    else:
        raise ValueError(f"unknown axis group {group}")

    if not isinstance(receivers, Sequence) or isinstance(receivers, (str, bytes)):
        raise TypeError(f"{axis_id}: receiver membership must be a list")
    receiver_ids = [str(value) for value in receivers]
    if any(not value for value in receiver_ids) or len(receiver_ids) != len(
        set(receiver_ids)
    ):
        raise ValueError(f"{axis_id}: empty or duplicate receiver membership")
    return {
        "axis_id": axis_id,
        "axis_group": group,
        "datum_global_xyz_mm": list(datum),
        "direction_global_xyz": list(direction),
        "axis_length_mm": length,
        "axis_interval_from_datum_mm": [low, high] if low is not None else None,
        "source_extent": extent_source,
        "source_occupied_diameter_mm": (
            _number(diameter, f"{axis_id} source diameter")
            if diameter is not None
            else None
        ),
        "receiver_member_ids": receiver_ids,
        "panel_member_id": str(panel_member) if panel_member is not None else None,
        "source_record": dict(row),
    }


def _cylinder_candidates(
    axis: Mapping[str, Any],
    member: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    diagnostics = Counter()
    matches: list[dict[str, Any]] = []
    axis_direction = axis["direction_global_xyz"]
    axis_datum = axis["datum_global_xyz_mm"]
    occupied_interval = axis["axis_interval_from_datum_mm"]
    features = member.get("features", [])
    for feature in features:
        if feature.get("surface_kind") != "CYLINDER":
            continue
        diagnostics["cylinder_features_in_receiver"] += 1
        cylinder = feature.get("cylinder") or {}
        cylinder_origin = _vec3(
            cylinder.get("axis_origin_global_xyz_mm"),
            f"{feature.get('feature_id')} cylinder origin",
        )
        cylinder_direction = _unit(
            cylinder.get("axis_unit_global_xyz"),
            f"{feature.get('feature_id')} cylinder axis",
        )
        sine_error = _norm(_cross(axis_direction, cylinder_direction))
        line_distance = _norm(_cross(_sub(cylinder_origin, axis_datum), axis_direction))
        if (
            sine_error > AXIS_DIRECTION_SINE_TOLERANCE
            or line_distance > AXIS_CENTERLINE_TOLERANCE_MM
        ):
            continue
        diagnostics["coaxial_cylinder_features"] += 1
        patch_interval = cylinder.get("axis_station_interval_mm")
        if (
            not isinstance(patch_interval, Sequence)
            or isinstance(patch_interval, (str, bytes))
            or len(patch_interval) != 2
        ):
            station_interval = None
            projected_interval = None
            overlap_length = None
            finite_status = "missing_finite_patch_interval"
        else:
            s0, s1 = (
                _number(value, "cylinder station interval") for value in patch_interval
            )
            if s1 < s0:
                s0, s1 = s1, s0
            endpoint0 = _add_scaled(cylinder_origin, cylinder_direction, s0)
            endpoint1 = _add_scaled(cylinder_origin, cylinder_direction, s1)
            t0 = _dot(_sub(endpoint0, axis_datum), axis_direction)
            t1 = _dot(_sub(endpoint1, axis_datum), axis_direction)
            patch_low, patch_high = sorted((t0, t1))
            station_interval = [s0, s1]
            projected_interval = [patch_low, patch_high]
            if occupied_interval is None:
                overlap_length = None
                finite_status = "source_finite_extent_unresolved"
            else:
                occupied_low, occupied_high = occupied_interval
                overlap_length = max(
                    0.0,
                    min(occupied_high, patch_high) - max(occupied_low, patch_low),
                )
                contained = (
                    patch_low >= occupied_low - PATCH_CONTAINMENT_TOLERANCE_MM
                    and patch_high <= occupied_high + PATCH_CONTAINMENT_TOLERANCE_MM
                )
                if contained:
                    finite_status = "contained_in_source_finite_interval"
                elif overlap_length > PATCH_CONTAINMENT_TOLERANCE_MM:
                    finite_status = "partially_overlaps_source_finite_interval"
                else:
                    finite_status = "outside_source_finite_interval"

        side = str(cylinder.get("material_side_geometry", "ambiguous"))
        if side not in {"bore_like", "exterior_like", "ambiguous"}:
            side = "unrecognized"
        if (
            side == "bore_like"
            and finite_status == "contained_in_source_finite_interval"
        ):
            association_status = "eligible_bore_patch"
            diagnostics["eligible_bore_patches"] += 1
        elif (
            side == "exterior_like"
            and finite_status == "contained_in_source_finite_interval"
        ):
            association_status = "coaxial_exterior_surface_rejected"
            diagnostics["exterior_surfaces_rejected"] += 1
        elif (
            side == "ambiguous"
            and finite_status == "contained_in_source_finite_interval"
        ):
            association_status = "coaxial_surface_classification_ambiguous"
            diagnostics["ambiguous_surfaces"] += 1
        elif finite_status == "source_finite_extent_unresolved":
            association_status = "coaxial_but_source_finite_extent_unresolved"
            diagnostics["unresolved_finite_extent"] += 1
        elif finite_status == "partially_overlaps_source_finite_interval":
            association_status = "coaxial_patch_only_partly_within_source_extent"
            diagnostics["partial_extent_patches"] += 1
        elif finite_status == "outside_source_finite_interval":
            association_status = "coaxial_patch_outside_source_extent"
            diagnostics["outside_extent_patches"] += 1
        elif finite_status == "missing_finite_patch_interval":
            association_status = "coaxial_patch_has_no_finite_interval"
            diagnostics["missing_patch_extents"] += 1
        else:
            association_status = "coaxial_surface_classification_unrecognized"
            diagnostics["unrecognized_classifications"] += 1

        radius = cylinder.get("radius_mm")
        source_diameter = axis.get("source_occupied_diameter_mm")
        matches.append(
            {
                "feature_id": str(feature.get("feature_id")),
                "surface_kind": "CYLINDER",
                "material_side_geometry": side,
                "association_status": association_status,
                "line_distance_mm": line_distance,
                "axis_direction_sine_error": sine_error,
                "cylinder_radius_mm": _number(radius, "cylinder radius")
                if radius is not None
                else None,
                "source_occupied_diameter_mm": source_diameter,
                "radius_minus_source_axis_radius_mm": (
                    _number(radius, "cylinder radius") - source_diameter / 2.0
                    if radius is not None and source_diameter is not None
                    else None
                ),
                "cylinder_axis_station_interval_mm": station_interval,
                "patch_interval_projected_from_axis_datum_mm": projected_interval,
                "source_axis_interval_from_datum_mm": occupied_interval,
                "finite_interval_status": finite_status,
                "axial_overlap_length_mm": overlap_length,
            }
        )
    matches.sort(key=lambda item: item["feature_id"])
    diagnostics.setdefault("cylinder_features_in_receiver", 0)
    diagnostics.setdefault("coaxial_cylinder_features", 0)
    return matches, dict(diagnostics)


def _receiver_result(
    axis: Mapping[str, Any],
    member_id: str,
    surface_members: Mapping[str, Mapping[str, Any]],
    source_member_index: Mapping[str, Any],
) -> dict[str, Any]:
    source_row = source_member_index["physical_members"].get(member_id)
    is_panel = member_id in source_member_index["panel_ids"]
    surface = surface_members.get(member_id)
    if surface is None:
        status = (
            "panel_surface_outside_register"
            if is_panel
            else "receiver_member_geometry_missing"
        )
        return {
            "receiver_member_id": member_id,
            "member_kind": "panel"
            if is_panel
            else (source_row or {}).get("member_kind"),
            "binding_status": status,
            "axis_in_stock_frame": None,
            "cylinder_surface_candidates": [],
            "matched_feature_ids": [],
            "match_status": status,
            "diagnostics": {},
        }

    stock = _stock_frame(surface)
    axis_local = {
        "datum_stock_gqr_mm": list(
            _to_stock_coordinates(axis["datum_global_xyz_mm"], stock)
        ),
        "direction_stock_gqr": list(
            _direction_to_stock(axis["direction_global_xyz"], stock)
        ),
        "axis_interval_from_datum_mm": axis["axis_interval_from_datum_mm"],
    }
    candidates, diagnostics = _cylinder_candidates(axis, surface)
    eligible = [
        candidate
        for candidate in candidates
        if candidate["association_status"] == "eligible_bore_patch"
    ]
    ambiguous = [
        candidate
        for candidate in candidates
        if candidate["association_status"] == "coaxial_surface_classification_ambiguous"
    ]
    if ambiguous:
        match_status = "ambiguous_surface_classification"
    elif len(eligible) == 1:
        match_status = "matched_bore_patch"
    elif len(eligible) > 1:
        radius_groups = {
            round(candidate["cylinder_radius_mm"], 6)
            for candidate in eligible
            if candidate["cylinder_radius_mm"] is not None
        }
        if len(radius_groups) <= 1 and all(
            candidate["cylinder_radius_mm"] is not None for candidate in eligible
        ):
            match_status = "matched_multiple_patches_same_radius_axis"
        else:
            match_status = "ambiguous_multiple_bore_geometries"
    elif any(
        candidate["association_status"]
        == "coaxial_patch_only_partly_within_source_extent"
        for candidate in candidates
    ):
        match_status = "unmatched_partial_finite_interval_overlap"
    elif any(
        candidate["association_status"] == "coaxial_but_source_finite_extent_unresolved"
        for candidate in candidates
    ):
        match_status = "unmatched_source_finite_extent_unresolved"
    elif any(
        candidate["association_status"] == "coaxial_patch_outside_source_extent"
        for candidate in candidates
    ):
        match_status = "unmatched_patch_outside_finite_interval"
    elif diagnostics.get("coaxial_cylinder_features", 0):
        match_status = "unmatched_no_bore_like_cylinder_patch"
    else:
        match_status = "unmatched_no_coaxial_cylinder_patch"

    unambiguous_status = match_status in {
        "matched_bore_patch",
        "matched_multiple_patches_same_radius_axis",
    }
    return {
        "receiver_member_id": member_id,
        "member_kind": "candidate_block"
        if member_id in source_member_index["block_ids"]
        else "frame_timber",
        "binding_status": "bound_to_current_finished_stock_frame",
        "current_finished_step_binding": dict(surface.get("step_binding") or {}),
        "stock_frame": stock,
        "axis_in_stock_frame": axis_local,
        "cylinder_surface_candidates": candidates,
        "matched_feature_ids": [row["feature_id"] for row in eligible]
        if unambiguous_status
        else [],
        "match_status": match_status,
        "diagnostics": diagnostics,
    }


def _source_inventory_screw_axes(
    source_inventory: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if source_inventory is None:
        return {}
    rows = source_inventory.get("fixed_panel_kicker_screws")
    if not isinstance(rows, list):
        raise TypeError("source inventory lacks fixed_panel_kicker_screws")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        axis_id = str(row.get("axis_id", ""))
        if not axis_id or axis_id in result:
            raise ValueError(
                "source inventory has an empty or duplicate panel screw axis ID"
            )
        result[axis_id] = dict(row)
    return result


def _close_vectors(first: Any, second: Any, *, tolerance: float = 1.0e-6) -> bool:
    try:
        a = _vec3(first, "first comparison vector")
        b = _vec3(second, "second comparison vector")
    except ValueError:
        return False
    return all(abs(x - y) <= tolerance for x, y in zip(a, b, strict=True))


def _screw_station_reconciliation(
    row: Mapping[str, Any], source_row: Mapping[str, Any] | None
) -> dict[str, Any]:
    moved = row.get("owner_moved_axis_record")
    is_moved = moved is not None
    source_origin = source_row.get("origin_global_xyz_mm") if source_row else None
    source_direction = source_row.get("axis_global_xyz") if source_row else None
    current_origin = row.get("origin_global_xyz_mm")
    current_direction = row.get("axis_global_xyz")
    if source_row is None:
        position_status = "source_inventory_unavailable"
    elif is_moved:
        old_origin = moved.get("old_start_global_xyz_mm")
        new_origin = moved.get("new_start_global_xyz_mm")
        translation = moved.get("translation_global_xyz_mm")
        unchanged_direction = moved.get("axis_global_xyz_unchanged")
        if not _close_vectors(old_origin, source_origin):
            raise ValueError(
                f"{row.get('axis_id')}: moved-axis old origin differs from source inventory"
            )
        if not _close_vectors(new_origin, current_origin):
            raise ValueError(
                f"{row.get('axis_id')}: moved-axis new origin differs from current manifest"
            )
        if not _close_vectors(
            unchanged_direction, source_direction
        ) or not _close_vectors(unchanged_direction, current_direction):
            raise ValueError(
                f"{row.get('axis_id')}: moved-axis direction differs from source/current axis"
            )
        if translation is None or not _close_vectors(
            [
                old + delta
                for old, delta in zip(source_origin, translation, strict=True)
            ],
            current_origin,
        ):
            raise ValueError(
                f"{row.get('axis_id')}: moved-axis translation does not reach current origin"
            )
        if moved.get("panel_member") != row.get("panel_member"):
            raise ValueError(f"{row.get('axis_id')}: moved-axis panel identity changed")
        if moved.get("receiver_member") != row.get("receiver_member"):
            raise ValueError(
                f"{row.get('axis_id')}: moved-axis receiver differs from current manifest"
            )
        position_status = "owner_moved_from_source_inventory_station"
    else:
        if not _close_vectors(source_origin, current_origin):
            raise ValueError(
                f"{row.get('axis_id')}: unmarked screw origin differs from source inventory"
            )
        if not _close_vectors(source_direction, current_direction):
            raise ValueError(
                f"{row.get('axis_id')}: unmarked screw direction differs from source inventory"
            )
        if row.get("current_location_status") != "source_station_retained":
            raise ValueError(
                f"{row.get('axis_id')}: unchanged screw has inconsistent location status"
            )
        position_status = "source_inventory_station_retained"
    source_length = (
        _number(
            source_row.get("shop_purchased_length_mm"), "source purchased screw length"
        )
        if source_row is not None
        else None
    )
    manifest_length = _number(
        row.get("purchased_nominal_length_mm"), "manifest screw nominal length"
    )
    if source_length is not None and abs(source_length - manifest_length) > 1.0e-9:
        raise ValueError(
            f"{row.get('axis_id')}: current screw length policy differs from source inventory"
        )
    return {
        "current_location_status": row.get("current_location_status"),
        "source_station_position_status": position_status,
        "source_inventory_origin_global_xyz_mm": source_origin,
        "current_axis_origin_global_xyz_mm": current_origin,
        "current_axis_direction_global_xyz": current_direction,
        "previous_receiver_member": row.get("previous_receiver_member"),
        "current_receiver_member": row.get("receiver_member"),
        "owner_moved_axis_record": dict(moved) if is_moved else None,
        "source_inventory_shop_purchased_length_mm": source_length,
        "manifest_purchased_nominal_length_mm": manifest_length,
        "length_role": "modeled/current receiver-axis envelope only; not observed hardware or installation",
        "current_step_patch_evidence": "evaluated against the current axis location separately in receiver_memberships",
    }


def _build_axis_group(
    group: str,
    rows: Sequence[Mapping[str, Any]],
    surface_members: Mapping[str, Mapping[str, Any]],
    source_member_index: Mapping[str, Any],
    *,
    source_inventory_axes: Mapping[str, Mapping[str, Any]],
    require_full_inventory: bool,
) -> dict[str, Any]:
    axis_ids = _sorted_ids(rows, group)
    if require_full_inventory and len(rows) != EXPECTED_GROUP_COUNTS[group]:
        raise ValueError(
            f"{group} must contain {EXPECTED_GROUP_COUNTS[group]} axes, got {len(rows)}"
        )
    entries = []
    for row in sorted(rows, key=lambda item: str(item["axis_id"])):
        axis = _axis_inputs(group, row, source_inventory_axes=source_inventory_axes)
        memberships = []
        for member_id in axis["receiver_member_ids"]:
            memberships.append(
                _receiver_result(axis, member_id, surface_members, source_member_index)
            )
        panel_binding = None
        if axis["panel_member_id"] is not None:
            panel_binding = {
                "member_id": axis["panel_member_id"],
                "coverage_status": "outside_44_piece_register_panel_surface_scope",
            }
        entries.append(
            {
                "axis_id": axis["axis_id"],
                "axis_group": group,
                "source_axis_fields": {
                    "datum_global_xyz_mm": axis["datum_global_xyz_mm"],
                    "direction_global_xyz": axis["direction_global_xyz"],
                    "axis_length_mm": axis["axis_length_mm"],
                    "finite_interval_from_datum_mm": axis[
                        "axis_interval_from_datum_mm"
                    ],
                    "finite_extent_source_semantics": axis["source_extent"],
                    "occupied_diameter_mm": axis["source_occupied_diameter_mm"],
                },
                "receiver_memberships": memberships,
                "panel_member_reference": panel_binding,
                "source_hardware_policy": {
                    "hardware_status": row.get("hardware_status"),
                    "purchased_policy": row.get("purchased_policy"),
                    "purchased_nominal_length_mm": row.get(
                        "purchased_nominal_length_mm"
                    ),
                    "current_location_status": row.get("current_location_status"),
                    "owner_moved_axis_record": row.get("owner_moved_axis_record"),
                }
                if group == "panel_kicker_screw_axes"
                else {"hardware_status": row.get("hardware_status")},
                "panel_axis_station_reconciliation": (
                    _screw_station_reconciliation(
                        row, source_inventory_axes.get(str(row.get("axis_id")))
                    )
                    if group == "panel_kicker_screw_axes"
                    else None
                ),
                "acceptance_note": (
                    "Starting frame bolt geometry is bound for current recheck; no earlier candidate acceptance transfers."
                    if group == "retained_frame_bolt_axes"
                    else None
                ),
            }
        )

    if group == "candidate_bolt_axes":
        policy = "92 candidate structural bolt axes; former angle duties are development geometry only."
    elif group == "retained_frame_bolt_axes":
        policy = "12 retained starting frame-bolt axes; preserve as a separate group and recheck in this candidate."
    else:
        policy = "66 Hillman 42605 panel/kicker axes; source purchase and installation policy is retained."
    return {
        "axis_count": len(rows),
        "axis_ids": axis_ids,
        "policy_and_group_boundary": policy,
        "axes": entries,
    }


def build_report(
    surfaces_report: Mapping[str, Any],
    manifest: Mapping[str, Any],
    source_inventory: Mapping[str, Any] | None = None,
    *,
    require_full_inventory: bool = True,
    input_hashes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic metadata join; the strict mode checks the frozen 170-axis scope."""
    if manifest.get("manifest_id") != "current-full-frame-input-manifest-attempt04":
        raise ValueError("unexpected current input manifest identity")
    if (
        manifest.get("geometry_revision_id")
        != "led-clearance-2x6-runner-seated-blocks-v1"
    ):
        raise ValueError("unexpected reviewed geometry revision")
    if surfaces_report.get("candidate") != manifest.get("candidate"):
        raise ValueError("surface report candidate differs from the current manifest")
    if surfaces_report.get("geometry_revision_id") != manifest.get(
        "geometry_revision_id"
    ):
        raise ValueError("surface report revision differs from the current manifest")
    if surfaces_report.get("source_manifest_id") != manifest.get("manifest_id"):
        raise ValueError("surface report is bound to a different source manifest")
    surface_members, member_index = _validate_surface_inventory(
        surfaces_report, manifest, require_full_inventory=require_full_inventory
    )
    source_screw_axes = _source_inventory_screw_axes(source_inventory)
    manifest_groups = {group: manifest.get(group) for group in EXPECTED_GROUP_COUNTS}
    for group, rows in manifest_groups.items():
        if not isinstance(rows, list):
            raise TypeError(f"manifest lacks {group}")
        _sorted_ids(rows, group)
        if require_full_inventory and len(rows) != EXPECTED_GROUP_COUNTS[group]:
            raise ValueError(
                f"{group} has {len(rows)} rows, expected {EXPECTED_GROUP_COUNTS[group]}"
            )
    ids_by_group = {
        group: set(_sorted_ids(rows, group)) for group, rows in manifest_groups.items()
    }
    if any(
        ids_by_group[first] & ids_by_group[second]
        for i, first in enumerate(ids_by_group)
        for second in list(ids_by_group)[i + 1 :]
    ):
        raise ValueError(
            "source axis identities cross-contaminate the three distinct axis groups"
        )
    if require_full_inventory:
        if len(source_screw_axes) != EXPECTED_GROUP_COUNTS["panel_kicker_screw_axes"]:
            raise ValueError("current source inventory must contain all 66 screw axes")
        if set(source_screw_axes) != ids_by_group["panel_kicker_screw_axes"]:
            raise ValueError("current source inventory screw IDs differ from manifest")
        for row in manifest_groups["panel_kicker_screw_axes"]:
            source_row = source_screw_axes[row["axis_id"]]
            if source_row.get("purchased_policy") not in (
                None,
                row.get("purchased_policy"),
            ):
                raise ValueError(
                    f"{row['axis_id']}: purchased policy differs from current inventory"
                )
            if not str(row.get("purchased_policy", "")).startswith("Hillman 42605"):
                raise ValueError(
                    f"{row['axis_id']}: Hillman 42605 purchased policy was changed"
                )
            if (
                abs(
                    _number(
                        source_row.get("shop_purchased_length_mm"), "shop screw length"
                    )
                    - _number(
                        row.get("purchased_nominal_length_mm"),
                        "manifest screw nominal length",
                    )
                )
                > 1.0e-9
            ):
                raise ValueError(
                    f"{row['axis_id']}: current STEP cutter extent differs from manifest"
                )
        moved_ids = {
            str(row["axis_id"])
            for row in manifest_groups["panel_kicker_screw_axes"]
            if row.get("owner_moved_axis_record") is not None
        }
        if moved_ids != EXPECTED_MOVED_SCREW_IDS:
            raise ValueError(
                "panel screw current-location record differs from the reviewed eight-axis move set"
            )
    groups = {
        group: _build_axis_group(
            group,
            manifest_groups[group],
            surface_members,
            member_index,
            source_inventory_axes=source_screw_axes,
            require_full_inventory=require_full_inventory,
        )
        for group in EXPECTED_GROUP_COUNTS
    }
    totals = Counter()
    unmatched = {group: [] for group in EXPECTED_GROUP_COUNTS}
    for group, group_data in groups.items():
        for axis in group_data["axes"]:
            for membership in axis["receiver_memberships"]:
                totals[membership["match_status"]] += 1
                if membership["match_status"].startswith("unmatched") or membership[
                    "match_status"
                ].endswith("missing"):
                    unmatched[group].append(
                        {
                            "axis_id": axis["axis_id"],
                            "receiver_member_id": membership["receiver_member_id"],
                            "status": membership["match_status"],
                        }
                    )
    finished_members = []
    for member_id in sorted(surface_members):
        row = surface_members[member_id]
        stock = _stock_frame(row)
        finished_members.append(
            {
                "member_id": member_id,
                "member_kind": "candidate_block"
                if member_id in member_index["block_ids"]
                else "frame_timber",
                "step_binding": dict(row.get("step_binding") or {}),
                "stock_frame": stock,
                "feature_ids": sorted(
                    str(feature.get("feature_id"))
                    for feature in row.get("features", [])
                ),
            }
        )
    panel_ids = member_index["panel_ids"]
    return {
        "schema": "wood_joint_axis_finished_feature_register/v1",
        "status": "metadata_join_only_no_installation_or_mechanical_acceptance",
        "candidate": manifest.get("candidate"),
        "geometry_revision_id": manifest.get("geometry_revision_id"),
        "source_manifest": {
            "manifest_id": manifest.get("manifest_id"),
            "manifest_sha256_field": manifest.get("manifest_sha256"),
        },
        "source_hashes": dict(sorted((input_hashes or {}).items())),
        "surface_register": {
            "schema": surfaces_report.get("schema"),
            "record_count": len(surface_members),
            "frame_member_count": sum(
                member["member_kind"] == "frame_timber" for member in finished_members
            ),
            "candidate_block_count": sum(
                member["member_kind"] == "candidate_block"
                for member in finished_members
            ),
            "plywood_panel_count_excluded": len(panel_ids),
            "plywood_panel_member_ids_excluded": panel_ids,
            "panel_member_surface_coverage": "explicitly outside this 44-piece wood register",
            "finished_members": finished_members,
        },
        "matching_method": {
            "axis_parallel_sine_tolerance": AXIS_DIRECTION_SINE_TOLERANCE,
            "axis_centerline_tolerance_mm": AXIS_CENTERLINE_TOLERANCE_MM,
            "patch_containment_tolerance_mm": PATCH_CONTAINMENT_TOLERANCE_MM,
            "finite_patch_requirement": "cylinder axis_station_interval_mm must be present and project wholly inside the source modeled finite interval for association",
            "surface_side_rule": "associate only CYLINDER features classified bore_like; exterior_like is rejected and ambiguous/unrecognized classifications are preserved without association",
            "multiple_patch_rule": "retain every associated feature ID; multiple faces on one receiver are not collapsed or treated as duplicate axes",
            "radius_rule": "record radius comparison only; cylinder radius is not a drill-bit instruction or receiver capacity",
        },
        "source_axis_groups": groups,
        "receiver_membership_status_counts": dict(sorted(totals.items())),
        "unmatched_or_unresolved_receiver_memberships": unmatched,
        "claim_limits": [
            "A match is a source-bound geometric correspondence between a finite axis envelope and a bore-like cylindrical face patch in the exact current finished STEP binding.",
            "A match does not establish a drilled hole, pilot, countersink, fit, engagement, delivered fastener identity, installation, bearing, capacity, or load transfer.",
            "The 92 candidate bolts, 12 retained starting frame bolts, and 66 Hillman 42605 panel/kicker axes remain distinct identity and policy groups.",
            "Retained bolt geometry is only for current candidate recheck; no historical acceptance transfers.",
            "Panel axes keep the current Hillman 42605 policy; the source STEP cutter extent does not describe observed installation.",
        ],
    }


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object in {path}")
    return value


def _source_pin_payload(
    *,
    manifest_path: Path,
    surfaces_path: Path,
    surface_producer_path: Path,
    member_bundle_path: Path,
    source_inventory_path: Path,
    surface_source_pins_path: Path,
    receiver_source_path: Path,
    compositor_source_path: Path,
    manifest_producer_path: Path,
    output_path: Path,
    report_bytes: bytes,
) -> dict[str, Any]:
    manifest_bytes = manifest_path.read_bytes()
    if _sha256_bytes(manifest_bytes) != MANIFEST_SHA256:
        raise ValueError(
            "current attempt04 input manifest differs from its frozen SHA-256"
        )
    bundle_bytes = member_bundle_path.read_bytes()
    if _sha256_bytes(bundle_bytes) != MEMBER_BUNDLE_SHA256:
        raise ValueError("current member-solids bundle differs from its manifest pin")
    bundle = _read_json(member_bundle_path)
    manifest = _read_json(manifest_path)
    pinned_manifest_producer = manifest.get("producer") or {}
    if pinned_manifest_producer.get("path") != str(
        manifest_producer_path.relative_to(ROOT)
    ):
        raise ValueError(
            "current input manifest producer path differs from its frozen record"
        )
    actual_manifest_producer_hash = _sha256_path(manifest_producer_path)
    if pinned_manifest_producer.get("sha256") != actual_manifest_producer_hash:
        raise ValueError(
            "current input manifest producer differs from its frozen SHA-256"
        )
    pinned_cut_source = bundle.get("source_files_sha256", {}).get(
        "mini_moonboard/wood_joint_frame.py"
    )
    current_cut_source = _sha256_path(ROOT / "mini_moonboard/wood_joint_frame.py")
    if not pinned_cut_source or pinned_cut_source != current_cut_source:
        raise ValueError(
            "current wood_joint_frame.py differs from the source used for the finished STEP bundle"
        )
    pinned_connection_source = bundle.get("source_files_sha256", {}).get(
        "mini_moonboard/box_frame.py"
    )
    current_connection_source = _sha256_path(ROOT / "mini_moonboard/box_frame.py")
    if (
        not pinned_connection_source
        or pinned_connection_source != current_connection_source
    ):
        raise ValueError(
            "current box_frame.py differs from the source used for the finished STEP bundle"
        )
    pinned_compositor = bundle.get("source_files_sha256", {}).get(
        "scripts/wood_joint_wj24_compositor.py"
    )
    current_compositor = _sha256_path(compositor_source_path)
    if not pinned_compositor or pinned_compositor != current_compositor:
        raise ValueError(
            "current WJ24 compositor differs from the source used for the finished STEP bundle"
        )
    pinned_source_inventory = bundle.get("source_files_sha256", {}).get(
        "docs/wood-joints-mvp/source-inventory.json"
    )
    current_source_inventory = _sha256_path(source_inventory_path)
    if (
        not pinned_source_inventory
        or pinned_source_inventory != current_source_inventory
    ):
        raise ValueError(
            "current source inventory differs from the member-solids bundle pin"
        )
    attempt04_producer = _sha256_path(manifest_producer_path)
    if attempt04_producer != pinned_manifest_producer.get("sha256"):
        raise ValueError("attempt04 producer hash changed during pin assembly")
    surface_report = _read_json(surfaces_path)
    surface_producer_hash = _sha256_path(surface_producer_path)
    if surface_report.get("producer_sha256") != surface_producer_hash:
        raise ValueError(
            "surface report producer SHA-256 field differs from surfaces.py"
        )
    if surface_report.get("source_manifest_sha256") != _sha256_bytes(manifest_bytes):
        raise ValueError("surface report is bound to a different input manifest file")
    surface_pins = _read_json(surface_source_pins_path)
    # The surface producer records the exact source-pins.json byte hash. Its
    # compact formatting is intentional, so do not hash a reserialized object.
    surface_pins_hash = _sha256_path(surface_source_pins_path)
    if surface_pins_hash != surface_report.get("source_pins_sha256"):
        raise ValueError(
            "surface report source-pins.json differs from its embedded hash"
        )
    _verify_surface_pin_files(surface_pins, ROOT)
    return {
        "schema": "wood_joint_axis_source_pins/v1",
        "sources": {
            "current_full_frame_input_manifest": {
                "path": str(manifest_path.relative_to(ROOT)),
                "sha256": _sha256_bytes(manifest_bytes),
            },
            "current_input_manifest_producer": {
                "path": str(manifest_producer_path.relative_to(ROOT)),
                "sha256": actual_manifest_producer_hash,
            },
            "finished_surfaces_report": {
                "path": str(surfaces_path.relative_to(ROOT)),
                "sha256": _sha256_path(surfaces_path),
            },
            "finished_surfaces_producer": {
                "path": str(surface_producer_path.relative_to(ROOT)),
                "sha256": surface_producer_hash,
            },
            "finished_surfaces_source_pins": {
                "path": str(surface_source_pins_path.relative_to(ROOT)),
                "sha256": surface_pins_hash,
            },
            "current_finished_member_bundle": {
                "path": str(member_bundle_path.relative_to(ROOT)),
                "sha256": _sha256_bytes(bundle_bytes),
            },
            "current_step_cutter_source": {
                "path": "mini_moonboard/wood_joint_frame.py",
                "sha256": current_cut_source,
                "bundle_source_sha256": pinned_cut_source,
                "semantics": "_finished_source_hosts uses shop_purchased_length_mm for the STEP host cutter from Connection.start; geometry extent only",
            },
            "current_axis_map_and_receiver_source": {
                "path": str(receiver_source_path.relative_to(ROOT)),
                "sha256": _sha256_path(receiver_source_path),
                "semantics": "build_current_panel_axis_map binds eight owner-moved axes to current receiver stations and carries the source shop length as a geometric screen envelope",
            },
            "current_wj24_compositor_source": {
                "path": str(compositor_source_path.relative_to(ROOT)),
                "sha256": current_compositor,
                "bundle_source_sha256": pinned_compositor,
                "semantics": "validates the source inventory cutter maps; it does not establish the moved-axis cut at a revised station",
            },
            "current_connection_component_source": {
                "path": "mini_moonboard/box_frame.py",
                "sha256": current_connection_source,
                "bundle_source_sha256": pinned_connection_source,
                "semantics": "Connection.components uses Connection.start, direction, and length for a modeled cylinder envelope",
            },
            "current_screw_source_inventory": {
                "path": str(source_inventory_path.relative_to(ROOT)),
                "sha256": current_source_inventory,
                "bundle_source_sha256": pinned_source_inventory,
            },
            "axis_features_producer": {
                "path": str(Path(__file__).resolve().relative_to(ROOT)),
                "sha256": _sha256_path(Path(__file__).resolve()),
            },
        },
        "outputs": {
            "axis_features": {
                "path": str(output_path.relative_to(ROOT)),
                "sha256": _sha256_bytes(report_bytes),
            }
        },
    }


def _write_exclusive(path: Path, value: bytes) -> None:
    with path.open("xb") as output:
        output.write(value)
        output.flush()
        os.fsync(output.fileno())


def run_write(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    surfaces_path: Path = DEFAULT_SURFACES,
    surface_producer_path: Path = DEFAULT_SURFACE_PRODUCER,
    member_bundle_path: Path = DEFAULT_MEMBER_BUNDLE,
    source_inventory_path: Path = DEFAULT_SOURCE_INVENTORY,
    surface_source_pins_path: Path = ATTEMPT_DIR / "source-pins.json",
    receiver_source_path: Path = DEFAULT_RECEIVER_SOURCE,
    compositor_source_path: Path = DEFAULT_COMPOSITOR_SOURCE,
    manifest_producer_path: Path = DEFAULT_MANIFEST_PRODUCER,
    output_path: Path = DEFAULT_OUTPUT,
    pins_path: Path = DEFAULT_PINS,
) -> dict[str, Any]:
    for path in (output_path, pins_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")
    manifest = _read_json(manifest_path)
    surfaces = _read_json(surfaces_path)
    source_inventory = _read_json(source_inventory_path)
    # Hashes used in the report are recomputed only after the producer, bundle,
    # and model-source identities have been reconciled by the pins builder.
    provisional_hashes = {
        "manifest_sha256": _sha256_path(manifest_path),
        "surfaces_report_sha256": _sha256_path(surfaces_path),
        "surfaces_producer_sha256": _sha256_path(surface_producer_path),
        "surfaces_source_pins_sha256": _sha256_path(surface_source_pins_path),
        "member_bundle_sha256": _sha256_path(member_bundle_path),
        "source_inventory_sha256": _sha256_path(source_inventory_path),
        "receiver_source_sha256": _sha256_path(receiver_source_path),
        "compositor_source_sha256": _sha256_path(compositor_source_path),
        "manifest_producer_sha256": _sha256_path(manifest_producer_path),
    }
    report = build_report(
        surfaces,
        manifest,
        source_inventory,
        require_full_inventory=True,
        input_hashes=provisional_hashes,
    )
    report_bytes = canonical_json_bytes(report)
    pins = _source_pin_payload(
        manifest_path=manifest_path,
        surfaces_path=surfaces_path,
        surface_producer_path=surface_producer_path,
        member_bundle_path=member_bundle_path,
        source_inventory_path=source_inventory_path,
        surface_source_pins_path=surface_source_pins_path,
        receiver_source_path=receiver_source_path,
        compositor_source_path=compositor_source_path,
        manifest_producer_path=manifest_producer_path,
        output_path=output_path,
        report_bytes=report_bytes,
    )
    pins_bytes = canonical_json_bytes(pins)
    created: list[Path] = []
    try:
        _write_exclusive(pins_path, pins_bytes)
        created.append(pins_path)
        _write_exclusive(output_path, report_bytes)
        created.append(output_path)
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return report


def run_verify(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    surfaces_path: Path = DEFAULT_SURFACES,
    surface_producer_path: Path = DEFAULT_SURFACE_PRODUCER,
    member_bundle_path: Path = DEFAULT_MEMBER_BUNDLE,
    source_inventory_path: Path = DEFAULT_SOURCE_INVENTORY,
    surface_source_pins_path: Path = ATTEMPT_DIR / "source-pins.json",
    receiver_source_path: Path = DEFAULT_RECEIVER_SOURCE,
    compositor_source_path: Path = DEFAULT_COMPOSITOR_SOURCE,
    manifest_producer_path: Path = DEFAULT_MANIFEST_PRODUCER,
    output_path: Path = DEFAULT_OUTPUT,
    pins_path: Path = DEFAULT_PINS,
) -> dict[str, Any]:
    saved_pins = _read_json(pins_path)
    manifest = _read_json(manifest_path)
    surfaces = _read_json(surfaces_path)
    source_inventory = _read_json(source_inventory_path)
    provisional_hashes = {
        "manifest_sha256": _sha256_path(manifest_path),
        "surfaces_report_sha256": _sha256_path(surfaces_path),
        "surfaces_producer_sha256": _sha256_path(surface_producer_path),
        "surfaces_source_pins_sha256": _sha256_path(surface_source_pins_path),
        "member_bundle_sha256": _sha256_path(member_bundle_path),
        "source_inventory_sha256": _sha256_path(source_inventory_path),
        "receiver_source_sha256": _sha256_path(receiver_source_path),
        "compositor_source_sha256": _sha256_path(compositor_source_path),
        "manifest_producer_sha256": _sha256_path(manifest_producer_path),
    }
    report = build_report(
        surfaces,
        manifest,
        source_inventory,
        require_full_inventory=True,
        input_hashes=provisional_hashes,
    )
    report_bytes = canonical_json_bytes(report)
    expected_pins = _source_pin_payload(
        manifest_path=manifest_path,
        surfaces_path=surfaces_path,
        surface_producer_path=surface_producer_path,
        member_bundle_path=member_bundle_path,
        source_inventory_path=source_inventory_path,
        surface_source_pins_path=surface_source_pins_path,
        receiver_source_path=receiver_source_path,
        compositor_source_path=compositor_source_path,
        manifest_producer_path=manifest_producer_path,
        output_path=output_path,
        report_bytes=report_bytes,
    )
    if canonical_json_bytes(saved_pins) != canonical_json_bytes(expected_pins):
        raise ValueError(
            "axis source pins differ from the current inputs or generated report"
        )
    if output_path.read_bytes() != report_bytes:
        raise ValueError("axis-features.json differs from the exact canonical replay")
    return report


def _cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write", action="store_true", help="create ignored outputs exclusively"
    )
    mode.add_argument(
        "--verify", action="store_true", help="read-only exact replay verification"
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--surfaces", type=Path, default=DEFAULT_SURFACES)
    parser.add_argument(
        "--surface-producer", type=Path, default=DEFAULT_SURFACE_PRODUCER
    )
    parser.add_argument("--member-bundle", type=Path, default=DEFAULT_MEMBER_BUNDLE)
    parser.add_argument(
        "--source-inventory", type=Path, default=DEFAULT_SOURCE_INVENTORY
    )
    parser.add_argument(
        "--surface-source-pins", type=Path, default=ATTEMPT_DIR / "source-pins.json"
    )
    parser.add_argument("--receiver-source", type=Path, default=DEFAULT_RECEIVER_SOURCE)
    parser.add_argument(
        "--compositor-source", type=Path, default=DEFAULT_COMPOSITOR_SOURCE
    )
    parser.add_argument(
        "--manifest-producer", type=Path, default=DEFAULT_MANIFEST_PRODUCER
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--pins", type=Path, default=DEFAULT_PINS)
    args = parser.parse_args(argv)
    try:
        kwargs = {
            "manifest_path": args.manifest,
            "surfaces_path": args.surfaces,
            "surface_producer_path": args.surface_producer,
            "member_bundle_path": args.member_bundle,
            "source_inventory_path": args.source_inventory,
            "surface_source_pins_path": args.surface_source_pins,
            "receiver_source_path": args.receiver_source,
            "compositor_source_path": args.compositor_source,
            "manifest_producer_path": args.manifest_producer,
            "output_path": args.output,
            "pins_path": args.pins,
        }
        report = run_write(**kwargs) if args.write else run_verify(**kwargs)
    except (OSError, TypeError, ValueError, KeyError) as error:
        print(f"axis_features: {error}", file=sys.stderr)
        return 2
    print(
        f"{report['schema']}: "
        f"{sum(group['axis_count'] for group in report['source_axis_groups'].values())} axes, "
        f"{report['surface_register']['record_count']} finished wood members"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
