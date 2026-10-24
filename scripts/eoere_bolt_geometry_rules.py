"""Bounded principal-axis NDS geometry checks for the EOERE bolt review.

These helpers classify only cases supported by the current geometry method.
Oblique or reversing loads and unclassified rows remain unresolved; component
screens never imply a complete joint or a credited capacity adjustment.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from itertools import pairwise
from typing import Any


def _finite_pair(value: Iterable[float], label: str) -> tuple[float, float]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{label} must contain two finite numbers")
    try:
        pair = tuple(value)
    except TypeError as error:
        raise ValueError(f"{label} must contain two finite numbers") from error
    if len(pair) != 2:
        raise ValueError(f"{label} must contain two finite numbers")
    result: list[float] = []
    for item in pair:
        if isinstance(item, bool):
            raise TypeError(f"{label} must contain two finite numbers")
        try:
            number = float(item)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{label} must contain two finite numbers") from error
        if not math.isfinite(number):
            raise ValueError(f"{label} must contain two finite numbers")
        result.append(number)
    return result[0], result[1]


def _threshold_breaks(first: float, last: float, gate: float) -> list[float]:
    breaks = [0.0, 1.0]
    slope = last - first
    if slope != 0.0:
        for boundary in (-gate, gate):
            t = (boundary - first) / slope
            if 0.0 < t < 1.0:
                breaks.append(t)
    return sorted(breaks)


def _resolved_intervals(
    first: float, last: float, gate: float
) -> list[tuple[float, float, float]]:
    """Return subinterval midpoints where an affine scalar is resolved."""
    breaks = _threshold_breaks(first, last, gate)
    slope = last - first
    return [
        (left, right, (left + right) / 2)
        for left, right in pairwise(breaks)
        if abs(first + slope * ((left + right) / 2)) > gate
    ]


def classify_affine_load(
    first_gv: Iterable[float], last_gv: Iterable[float], force_gate: float = 1e-8
) -> dict[str, Any]:
    """Classify an affine ``(grain, cross-grain)`` force over a bearing path.

    Principal classification is a numerical resolution result only. If both
    components are resolved together anywhere in the affine path, the result
    is oblique even when the endpoints separately lie on principal axes.
    """
    first = _finite_pair(first_gv, "first_gv")
    last = _finite_pair(last_gv, "last_gv")
    if isinstance(force_gate, bool):
        raise TypeError("force_gate must be finite and positive")
    try:
        gate = float(force_gate)
    except (TypeError, ValueError) as error:
        raise ValueError("force_gate must be finite and positive") from error
    if not math.isfinite(gate) or gate <= 0.0:
        raise ValueError("force_gate must be finite and positive")

    grain_intervals = _resolved_intervals(first[0], last[0], gate)
    cross_intervals = _resolved_intervals(first[1], last[1], gate)

    def resolved_values(
        component: int, intervals: list[tuple[float, float, float]]
    ) -> list[float]:
        start, end = first[component], last[component]
        return [start + (end - start) * midpoint for _, _, midpoint in intervals]

    grain_values = resolved_values(0, grain_intervals)
    cross_values = resolved_values(1, cross_intervals)
    combined_breaks = sorted(
        set(_threshold_breaks(first[0], last[0], gate))
        | set(_threshold_breaks(first[1], last[1], gate))
    )
    mixed_interior = any(
        abs(first[0] + (last[0] - first[0]) * t) > gate
        and abs(first[1] + (last[1] - first[1]) * t) > gate
        for t in ((left + right) / 2 for left, right in pairwise(combined_breaks))
    )
    reversal = any(
        a < -gate and b > gate or a > gate and b < -gate
        for a, b in zip(first, last, strict=True)
    )

    if mixed_interior:
        direction = "oblique"
    elif grain_values and cross_values:
        direction = "unresolved"
    elif grain_values:
        direction = "parallel"
    elif cross_values:
        direction = "perpendicular"
    else:
        direction = "unresolved"

    def common_sign(values: list[float]) -> int | None:
        signs = {1 if value > 0.0 else -1 for value in values}
        return next(iter(signs)) if len(signs) == 1 else None

    grain_sign = common_sign(grain_values) if direction == "parallel" else None
    crossgrain_sign = (
        common_sign(cross_values) if direction == "perpendicular" else None
    )
    reasons = []
    if direction == "oblique":
        reasons.append("affine force has a resolved mixed grain/cross-grain interior")
    elif direction == "unresolved":
        reasons.append("affine force does not resolve to one principal direction")
    if reversal:
        reasons.append("a resolved component reverses sign over the affine path")
    return {
        "direction": direction,
        "reversal": reversal,
        "grain_sign": grain_sign,
        "crossgrain_sign": crossgrain_sign,
        "first_gv": list(first),
        "last_gv": list(last),
        "force_gate": gate,
        "reasons": reasons,
        "principal_classification_is_numerical_resolution_only": True,
    }


def _positive(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be finite and positive")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be finite and positive") from error
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{label} must be finite and positive")
    return result


def _optional_row_spacing(value: float | None) -> float | None:
    """Interpret the consumer's zero marker as missing row-spacing evidence."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("maximum_row_spacing must be finite and nonnegative")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "maximum_row_spacing must be finite and nonnegative"
        ) from error
    if not math.isfinite(result) or result < 0.0:
        raise ValueError("maximum_row_spacing must be finite and nonnegative")
    return None if result == 0.0 else result


def _load_direction(load_info: dict[str, Any]) -> tuple[str, bool]:
    if not isinstance(load_info, dict):
        raise TypeError("load_info must be a classified affine-load result")
    direction = load_info.get("direction")
    if not isinstance(direction, str) or direction not in {
        "parallel",
        "perpendicular",
        "oblique",
        "unresolved",
    }:
        raise ValueError("load_info has an unknown direction classification")
    reversal = load_info.get("reversal")
    if not isinstance(reversal, bool):
        raise TypeError("load_info reversal must be boolean")
    return direction, reversal


def _unresolved(reason: str, **details: Any) -> dict[str, Any]:
    return {"status": "unresolved", "required_mm": None, "reasons": [reason], **details}


def edge_rule(
    distances_neg_pos: Iterable[float],
    d: float,
    effective_wood_length: float | None,
    load_info: dict[str, Any],
    maximum_row_spacing: float | None = None,
) -> dict[str, Any]:
    """Check principal-axis bolt edge distances without resolving oblique loads.

    ``distances_neg_pos`` is ordered by the host's negative and positive
    cross-grain directions. Loads with mixed directions or a resolved sign
    reversal remain unresolved rather than receiving componentwise 4D credit.
    """
    distances = _finite_pair(distances_neg_pos, "distances_neg_pos")
    if any(distance < 0.0 for distance in distances):
        raise ValueError("edge distances must be nonnegative")
    diameter = _positive(d, "diameter")
    if effective_wood_length is None:
        wood_length = None
    else:
        wood_length = _positive(effective_wood_length, "effective_wood_length")
    row_spacing = _optional_row_spacing(maximum_row_spacing)
    direction, reversal = _load_direction(load_info)
    if reversal:
        return _unresolved(
            "resolved load reversal prevents one signed loaded-edge classification",
            actual_mm=list(distances),
            direction=direction,
        )
    if direction not in {"parallel", "perpendicular"}:
        return _unresolved(
            "edge rule requires one resolved principal load direction",
            actual_mm=list(distances),
            direction=direction,
        )

    if direction == "perpendicular":
        sign = load_info.get("crossgrain_sign")
        if type(sign) is not int or sign not in (-1, 1):
            return _unresolved(
                "perpendicular load sign is not resolved",
                actual_mm=list(distances),
                direction=direction,
            )
        required = [1.5 * diameter, 1.5 * diameter]
        required[0 if sign < 0 else 1] = 4.0 * diameter
        rule = "NDS 2024 Table 12.5.1C perpendicular-to-grain edge distances"
    else:
        if wood_length is None:
            return _unresolved(
                "parallel edge rule requires effective wood length",
                actual_mm=list(distances),
                direction=direction,
            )
        required_value = 1.5 * diameter
        if wood_length / diameter > 6.0:
            if row_spacing is None:
                return _unresolved(
                    "long parallel penetration requires known row spacing",
                    actual_mm=list(distances),
                    direction=direction,
                )
            required_value = max(required_value, row_spacing / 2.0)
        required = [required_value, required_value]
        rule = "NDS 2024 Table 12.5.1C parallel-to-grain edge distances"

    failed_sides = [
        side
        for side, actual, needed in zip(
            ("negative", "positive"), distances, required, strict=True
        )
        if actual + 1e-5 < needed
    ]
    return {
        "status": "fail" if failed_sides else "pass",
        "required_mm": required,
        "actual_mm": list(distances),
        "direction": direction,
        "loaded_side": (
            "negative" if load_info.get("crossgrain_sign") == -1 else "positive"
        )
        if direction == "perpendicular"
        else None,
        "failed_sides": failed_sides,
        "rule": rule,
        "capacity_or_complete_joint_acceptance": False,
        "reasons": (
            [f"edge distance shortfall on {side} side" for side in failed_sides]
            if failed_sides
            else ["principal-axis edge minimums are met"]
        ),
    }


def end_rule(
    distance: float, d: float, category: str, *, square_end: bool | None
) -> dict[str, Any]:
    """Apply the existing end-distance factor only to a classified square end.

    A sloped or unclassified boundary can retain a numeric diagnostic, but it
    cannot receive a formal end-rule pass, failure, or factor.
    """
    if isinstance(distance, bool):
        raise TypeError("distance must be finite and nonnegative")
    try:
        actual = float(distance)
    except (TypeError, ValueError) as error:
        raise ValueError("distance must be finite and nonnegative") from error
    if not math.isfinite(actual) or actual < 0.0:
        raise ValueError("distance must be finite and nonnegative")
    diameter = _positive(d, "diameter")
    if square_end not in (True, False, None) or type(square_end) not in (
        bool,
        type(None),
    ):
        raise ValueError("square_end must be true, false, or unknown")
    recognized = {
        "softwood_parallel_tension",
        "parallel_compression",
        "perpendicular",
    }
    if category is not None and not isinstance(category, str):
        raise TypeError("category must be a string")
    diagnostic = None
    if isinstance(category, str) and category in recognized:
        from scripts.thin_bolted_timber_resistance import end_geometry_factor

        diagnostic = end_geometry_factor(actual, diameter, category)
    if square_end is not True:
        return {
            "status": "unresolved",
            "factor": None,
            "minimum_mm": None,
            "full_value_mm": None,
            "diagnostic_trial_only": diagnostic,
            "reasons": ["boundary is not established as a square-cut member end"],
            "complete_joint_acceptance": False,
        }
    if diagnostic is None:
        return {
            "status": "unresolved",
            "factor": None,
            "minimum_mm": None,
            "full_value_mm": None,
            "diagnostic_trial_only": None,
            "reasons": ["end-distance loading category is unclassified"],
            "complete_joint_acceptance": False,
        }
    factor = diagnostic["end_factor_only"]
    return {
        "status": "fail" if factor is None else "pass",
        "factor": factor,
        "minimum_mm": diagnostic["minimum_distance_mm"],
        "full_value_mm": diagnostic["full_value_distance_mm"],
        "diagnostic_trial_only": None,
        "actual_mm": actual,
        "category": category,
        "rule": "NDS 2024 Table 12.5.1A and §12.5.1.2(a)",
        "capacity_or_complete_joint_acceptance": False,
        "reasons": (
            ["end distance is below the Cdelta=0.5 minimum"]
            if factor is None
            else ["classified square-end minimum is met; factor is end-only"]
        ),
    }


def _perpendicular_between_row_minimum(ell: float, diameter: float) -> float:
    ratio = ell / diameter
    if ratio <= 2.0:
        return 2.5 * diameter
    if ratio >= 6.0:
        return 5.0 * diameter
    return (5.0 * ell + 10.0 * diameter) / 8.0


def pair_rule(
    delta_gv: Iterable[float],
    d: float,
    ell: float,
    load_info: dict[str, Any],
    *,
    row_classification: str | None = None,
) -> dict[str, Any]:
    """Check an explicitly classified principal-axis pair geometry.

    NDS row rules require a load-aligned row. Diagonal pairs without a proven
    same-row or between-row classification stay unresolved; their Euclidean
    spacing and principal projections are retained as diagnostic markers.
    """
    delta = _finite_pair(delta_gv, "delta_gv")
    diameter = _positive(d, "diameter")
    length = _positive(ell, "ell")
    if row_classification is not None and (
        not isinstance(row_classification, str)
        or row_classification not in {"same_row", "between_rows"}
    ):
        raise ValueError("row_classification must be 'same_row' or 'between_rows'")
    direction, reversal = _load_direction(load_info)
    grain, crossgrain = abs(delta[0]), abs(delta[1])
    actual = math.hypot(grain, crossgrain)
    row_minimum = _perpendicular_between_row_minimum(length, diameter)
    markers = {
        "parallel_same_row_min_mm": 3.0 * diameter,
        "parallel_same_row_cdelta1_mm": 4.0 * diameter,
        "parallel_between_rows_min_mm": 1.5 * diameter,
        "perpendicular_same_row_min_mm": 3.0 * diameter,
        "perpendicular_same_row_cdelta1_mm": None,
        "perpendicular_between_rows_min_mm": row_minimum,
    }
    base = {
        "actual_spacing_mm": actual,
        "grain_projection_mm": grain,
        "crossgrain_projection_mm": crossgrain,
        "principal_markers_mm": markers,
        "direction": direction,
        "row_classification": row_classification,
        "required_mm": None,
        "capacity_or_complete_joint_acceptance": False,
    }
    if reversal:
        return {
            **base,
            **_unresolved(
                "resolved load reversal prevents a single row-direction check"
            ),
        }
    if direction not in {"parallel", "perpendicular"}:
        return {
            **base,
            **_unresolved(
                "pair spacing requires one resolved principal load direction"
            ),
        }
    if row_classification is None:
        return {
            **base,
            **_unresolved(
                "explicit same-row or between-row classification is required"
            ),
        }
    tolerance = 1e-5
    if actual <= tolerance:
        return {
            **base,
            **_unresolved("coincident centers do not define a row direction"),
        }
    if row_classification == "same_row":
        aligned = (
            crossgrain <= tolerance and grain > tolerance
            if direction == "parallel"
            else grain <= tolerance and crossgrain > tolerance
        )
        spacing = grain if direction == "parallel" else crossgrain
        if direction == "parallel":
            required, full = 3.0 * diameter, 4.0 * diameter
            rule = "NDS 2024 Table 12.5.1B parallel-to-grain in-row spacing"
        else:
            required, full = 3.0 * diameter, None
            rule = "NDS 2024 Table 12.5.1B perpendicular-to-grain in-row minimum"
    else:
        aligned = (
            grain <= tolerance and crossgrain > tolerance
            if direction == "parallel"
            else crossgrain <= tolerance and grain > tolerance
        )
        spacing = crossgrain if direction == "parallel" else grain
        if direction == "parallel":
            required, full = 1.5 * diameter, None
            rule = "NDS 2024 Table 12.5.1D parallel-to-grain between-row spacing"
        else:
            required, full = row_minimum, None
            rule = "NDS 2024 Table 12.5.1D perpendicular-to-grain between-row spacing"

    if not aligned:
        return {
            **base,
            **_unresolved(
                "pair vector does not match the explicit principal row classification"
            ),
        }
    status = "fail" if spacing + tolerance < required else "pass"
    reason = (
        "classified minimum row spacing is short"
        if status == "fail"
        else "classified row minimum is met; no Cdelta or complete-joint capacity is established"
    )
    return {
        **base,
        "status": status,
        "required_mm": required,
        "measured_rule_spacing_mm": spacing,
        "full_spacing_mm": full,
        "rule": rule,
        "reasons": [reason],
    }


def rollup_status(statuses: Iterable[str | dict[str, Any]]) -> str:
    """Return only a component-level status; never a joint or Cdelta result."""
    if isinstance(statuses, (str, dict)):
        entries = [statuses]
    else:
        try:
            entries = list(statuses)
        except TypeError as error:
            raise ValueError(
                "statuses must be an iterable of rule results or statuses"
            ) from error
    normalized = []
    for entry in entries:
        value = entry.get("status") if isinstance(entry, dict) else entry
        if not isinstance(value, str) or value.lower() not in {
            "pass",
            "fail",
            "unresolved",
        }:
            raise ValueError(f"unsupported component status: {value!r}")
        normalized.append(value.lower())
    if "fail" in normalized:
        status = "FAIL"
    elif not normalized or "unresolved" in normalized:
        status = "UNRESOLVED"
    else:
        status = "PASS_COMPONENTS_ONLY"
    return status
