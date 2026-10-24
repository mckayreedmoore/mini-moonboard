"""Enumerate same-host bolt pairs without assuming their NDS row grouping."""

from __future__ import annotations

import copy
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping
from numbers import Real
from typing import Any

_PARALLEL_TOLERANCE = 1e-8
_RULE_STATUSES = {"pass", "fail", "unresolved"}


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def _vec3(value: Any, label: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{label} must contain three finite numbers")
    return tuple(_number(item, label) for item in value)  # type: ignore[return-value]


def _wood_surfaces(shaft: Mapping[str, Any], axis_id: str) -> dict[str, list[float]]:
    surfaces = shaft.get("surfaces")
    if not isinstance(surfaces, list):
        raise TypeError(f"shaft {axis_id} surfaces must be a list")
    intervals: dict[str, list[float]] = {}
    for surface in surfaces:
        if not isinstance(surface, Mapping):
            raise TypeError(f"shaft {axis_id} has a malformed surface")
        if surface.get("kind") != "wood":
            continue
        host = surface.get("host")
        if not isinstance(host, str) or not host:
            raise ValueError(f"shaft {axis_id} has a wood surface without a host")
        if host in intervals:
            raise ValueError(f"shaft {axis_id} has multiple wood surfaces for {host}")
        interval = surface.get("interval_mm")
        if not isinstance(interval, (list, tuple)) or len(interval) != 2:
            raise ValueError(f"shaft {axis_id} {host} interval must have two values")
        low, high = (_number(value, f"shaft {axis_id} {host} interval") for value in interval)
        if high <= low:
            raise ValueError(f"shaft {axis_id} {host} interval must have positive length")
        intervals[host] = [low, high]
    return intervals


def _axis_data(shafts: Mapping[str, Any]) -> dict[str, tuple[tuple[float, ...], tuple[float, ...], dict[str, list[float]]]]:
    if not isinstance(shafts, Mapping):
        raise TypeError("shafts must map axis IDs to source shaft records")
    data = {}
    for axis_id, shaft in shafts.items():
        if not isinstance(axis_id, str) or not axis_id:
            raise ValueError("shaft mapping keys must be nonempty axis IDs")
        if not isinstance(shaft, Mapping):
            raise TypeError(f"shaft {axis_id} must be a mapping")
        if shaft.get("axis_id") != axis_id:
            raise ValueError(f"shaft mapping key does not match shaft axis_id {axis_id}")
        basis = shaft.get("basis")
        if not isinstance(basis, (list, tuple)) or not basis:
            raise ValueError(f"shaft {axis_id} requires a bore-axis basis vector")
        direction = _vec3(basis[0], f"shaft {axis_id} bore axis")
        magnitude = math.sqrt(sum(value * value for value in direction))
        if abs(magnitude - 1.0) > _PARALLEL_TOLERANCE:
            raise ValueError(f"shaft {axis_id} bore axis must be unit length")
        point = _vec3(shaft.get("point"), f"shaft {axis_id} point")
        intervals = _wood_surfaces(shaft, axis_id)
        data[axis_id] = (direction, point, intervals)
    return data


def _occurrence_map(
    wood_occurrences: Iterable[Mapping[str, Any]],
    shaft_data: Mapping[str, tuple[tuple[float, ...], tuple[float, ...], dict[str, list[float]]]],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    if isinstance(wood_occurrences, (str, bytes, Mapping)):
        raise TypeError("wood_occurrences must be an iterable of occurrence records")
    try:
        records = list(wood_occurrences)
    except TypeError as error:
        raise TypeError("wood_occurrences must be iterable") from error
    occurrence_map: dict[tuple[str, str], Mapping[str, Any]] = {}
    for occurrence in records:
        if not isinstance(occurrence, Mapping):
            raise TypeError("each wood occurrence must be a mapping")
        axis_id, host = occurrence.get("axis_id"), occurrence.get("host")
        if not isinstance(axis_id, str) or not axis_id or not isinstance(host, str) or not host:
            raise ValueError("each occurrence requires nonempty axis_id and host")
        key = (axis_id, host)
        if key in occurrence_map:
            raise ValueError(f"duplicate wood occurrence for {axis_id} in {host}")
        if axis_id not in shaft_data:
            raise ValueError(f"wood occurrence references missing shaft {axis_id}")
        if host not in shaft_data[axis_id][2]:
            raise ValueError(f"wood occurrence {axis_id}/{host} has no matching wood surface")
        placement = occurrence.get("placement")
        if not isinstance(placement, Mapping):
            raise TypeError(f"wood occurrence {axis_id}/{host} placement must be a mapping")
        bearing_interval = placement.get("bearing_interval_mm")
        if not isinstance(bearing_interval, (list, tuple)) or len(bearing_interval) != 2:
            raise ValueError(
                f"wood occurrence {axis_id}/{host} placement interval must have two values"
            )
        low, high = (
            _number(value, f"wood occurrence {axis_id}/{host} placement interval")
            for value in bearing_interval
        )
        if high <= low:
            raise ValueError(
                f"wood occurrence {axis_id}/{host} placement interval must have positive length"
            )
        occurrence_map[key] = occurrence

    expected = {
        (axis_id, host)
        for axis_id, (_, _, intervals) in shaft_data.items()
        for host in intervals
    }
    actual = set(occurrence_map)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"wood occurrence census differs; missing={missing!r}, extra={extra!r}")
    return occurrence_map


def _original_pair_map(
    original_pairs: Iterable[Mapping[str, Any]],
    occurrence_map: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[tuple[str, tuple[str, str]], Mapping[str, Any]]:
    if isinstance(original_pairs, (str, bytes, Mapping)):
        raise TypeError("original_pairs must be an iterable of pair records")
    try:
        records = list(original_pairs)
    except TypeError as error:
        raise TypeError("original_pairs must be iterable") from error
    pairs: dict[tuple[str, tuple[str, str]], Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError("each original pair must be a mapping")
        host, axes = record.get("host"), record.get("axes")
        if not isinstance(host, str) or not host or not isinstance(axes, (list, tuple)) or len(axes) != 2:
            raise ValueError("each original pair requires a host and two axis IDs")
        if not all(isinstance(axis_id, str) and axis_id for axis_id in axes) or axes[0] == axes[1]:
            raise ValueError("original pair axes must be two distinct nonempty IDs")
        pair_axes = tuple(sorted(axes))
        if any((axis_id, host) not in occurrence_map for axis_id in pair_axes):
            raise ValueError(f"original pair {pair_axes!r} lacks a same-host occurrence")
        rule = record.get("rule")
        if not isinstance(rule, Mapping) or rule.get("status") not in _RULE_STATUSES:
            raise ValueError(f"original pair {pair_axes!r} has no supported rule status")
        key = (host, pair_axes)
        if key in pairs:
            raise ValueError(f"duplicate original pair for {host}: {pair_axes!r}")
        pairs[key] = record
    return pairs


def _parallel_spacing(
    first_axis: tuple[float, ...],
    first_point: tuple[float, ...],
    second_axis: tuple[float, ...],
    second_point: tuple[float, ...],
) -> tuple[bool, float | None]:
    dot = sum(a * b for a, b in zip(first_axis, second_axis, strict=True))
    cross = (
        first_axis[1] * second_axis[2] - first_axis[2] * second_axis[1],
        first_axis[2] * second_axis[0] - first_axis[0] * second_axis[2],
        first_axis[0] * second_axis[1] - first_axis[1] * second_axis[0],
    )
    if math.sqrt(sum(value * value for value in cross)) > _PARALLEL_TOLERANCE:
        return False, None

    # Align signs and average the axes so pair ordering and axis reversals do
    # not change the centerline-distance measurement.
    aligned_second = tuple(value if dot >= 0.0 else -value for value in second_axis)
    direction = tuple(a + b for a, b in zip(first_axis, aligned_second, strict=True))
    direction_length = math.sqrt(sum(value * value for value in direction))
    direction = tuple(value / direction_length for value in direction)
    delta = tuple(b - a for a, b in zip(first_point, second_point, strict=True))
    along = sum(value * axis for value, axis in zip(delta, direction, strict=True))
    radial = tuple(value - along * axis for value, axis in zip(delta, direction, strict=True))
    return True, math.sqrt(sum(value * value for value in radial))


def _component_status(rule_status: str) -> str:
    return {
        "pass": "PASS_COMPONENTS_ONLY",
        "fail": "FAIL",
        "unresolved": "UNRESOLVED",
    }[rule_status]


def pair_census(
    shafts: Mapping[str, Any],
    wood_occurrences: Iterable[Mapping[str, Any]],
    original_pairs: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Enumerate every unordered pair of bolt axes sharing each wood host.

    The original receiver-group rules are retained only as component results.
    Pairs omitted by that grouping are listed with unresolved NDS row
    applicability. No spacing minimum or complete Cdelta is invented for
    those pairs.
    """
    shaft_data = _axis_data(shafts)
    occurrence_map = _occurrence_map(wood_occurrences, shaft_data)
    original_map = _original_pair_map(original_pairs, occurrence_map)

    axes_by_host: dict[str, list[str]] = defaultdict(list)
    for axis_id, host in occurrence_map:
        axes_by_host[host].append(axis_id)

    results = []
    for host in sorted(axes_by_host):
        axis_ids = sorted(axes_by_host[host])
        for index, first_id in enumerate(axis_ids):
            for second_id in axis_ids[index + 1 :]:
                pair_axes = (first_id, second_id)
                key = (host, pair_axes)
                source_rule = original_map.get(key)
                first_axis, first_point, first_intervals = shaft_data[first_id]
                second_axis, second_point, second_intervals = shaft_data[second_id]
                first_occurrence = occurrence_map[(first_id, host)]
                second_occurrence = occurrence_map[(second_id, host)]
                parallel, spacing = _parallel_spacing(
                    first_axis, first_point, second_axis, second_point
                )
                original_rule = (
                    copy.deepcopy(source_rule["rule"]) if source_rule is not None else None
                )
                original_status = (
                    str(source_rule["rule"]["status"]) if source_rule is not None else None
                )

                if not parallel:
                    rule_status = "unresolved"
                    reason = "nonparallel bore axes have no single supported centerline spacing"
                elif source_rule is None:
                    rule_status = "unresolved"
                    reason = "same-host pair has no original connection-group rule; NDS connection-row applicability is unverified"
                else:
                    rule_status = original_status
                    reason = "original receiver-group rule retained as a component screen only"

                component_status = _component_status(rule_status)
                results.append(
                    {
                        "host": host,
                        "axes": list(pair_axes),
                        "existing_connection_group_pair": source_rule is not None,
                        "parallel_bore_axes": parallel,
                        "actual_spacing_mm": spacing,
                        "wood_bearing_intervals_mm": [
                            {
                                "axis_id": first_id,
                                "shaft_surface_interval_mm": list(first_intervals[host]),
                                "placement_bearing_interval_mm": list(
                                    first_occurrence["placement"]["bearing_interval_mm"]
                                ),
                            },
                            {
                                "axis_id": second_id,
                                "shaft_surface_interval_mm": list(second_intervals[host]),
                                "placement_bearing_interval_mm": list(
                                    second_occurrence["placement"]["bearing_interval_mm"]
                                ),
                            },
                        ],
                        "status": component_status,
                        "component_status": component_status,
                        "rule_status": rule_status,
                        "original_rule_status": original_status,
                        "original_rule": original_rule,
                        "rule_scope": (
                            "component_only" if source_rule is not None and parallel else "unverified"
                        ),
                        "complete_Cdelta": None,
                        "complete_joint_qualified": False,
                        "reasons": [reason],
                    }
                )
    return results
