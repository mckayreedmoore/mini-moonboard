"""Signed fastener-load directions to finite outer-member boundaries.

This module classifies geometry only. Loads must be signed forces *on one
specific wood member*. The opposite force on the other member must be passed
separately with that member's grain and coordinate frame. No NDS detailing,
strength, hole/cut net section, or joint-capacity result is produced.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

Vector3 = tuple[float, float, float]
Bounds3 = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]

_AXIS_TOLERANCE = 1e-8
_CENTER_TOLERANCE_MM = 1e-8
_RELATIVE_ZERO_COMPONENT_TOLERANCE = 1e-12


def classify_member_fastener_load(
    *,
    force_on_member_global_n: Sequence[float],
    grain_axis_global_unit: Sequence[float],
    bolt_axis_global_unit: Sequence[float],
    bolt_center_global_mm: Sequence[float],
    member_frame_origin_global_mm: Sequence[float],
    member_axes_global_unit: Sequence[Sequence[float]],
    member_bounds_local_mm: Sequence[Sequence[float]],
) -> dict:
    """Resolve signed grain/end and cross-grain/edge directions for one bolt.

    ``member_axes_global_unit`` is an ordered right-handed orthonormal box
    frame. ``member_bounds_local_mm[i]`` gives the finite lower and upper
    coordinates, in millimetres from ``member_frame_origin_global_mm``, along
    its ``i``th axis. The grain and bolt axes must each align with a different
    member-frame axis. The remaining member-frame axis is the unique in-plane
    cross-grain edge direction for this rectangular, side-grain geometry.

    Both force and position vectors use global XYZ coordinates. The bolt
    center must be inside the closed outer box. A zero or numerically
    negligible lateral component receives no loaded boundary; the opposite or
    unsigned component is never used to choose one.

    Distances are from the bolt center to the two outer-box boundaries along
    the grain and cross-grain axes. Nearby holes, notches, shoulders, and other
    cuts are not included and may create nearer boundaries. This function
    does not decide NDS category/table applicability or calculate resistance.
    """
    force = _vector(force_on_member_global_n, "force_on_member_global_n")
    grain = _unit_vector(grain_axis_global_unit, "grain_axis_global_unit")
    bolt_axis = _unit_vector(bolt_axis_global_unit, "bolt_axis_global_unit")
    center = _vector(bolt_center_global_mm, "bolt_center_global_mm")
    origin = _vector(member_frame_origin_global_mm, "member_frame_origin_global_mm")
    axes = _frame(member_axes_global_unit)
    bounds = _bounds(member_bounds_local_mm)

    grain_axis_index, grain_alignment = _matching_axis(grain, axes, "grain axis")
    bolt_axis_index, _ = _matching_axis(bolt_axis, axes, "bolt axis")
    if grain_axis_index == bolt_axis_index:
        raise ValueError(
            "grain and bolt axes must align with different member-frame axes"
        )
    if abs(_dot(grain, bolt_axis)) > _AXIS_TOLERANCE:
        raise ValueError(
            "grain and bolt axes must be perpendicular for side-grain classification"
        )
    cross_grain_axis_index = next(
        index for index in range(3) if index not in (grain_axis_index, bolt_axis_index)
    )

    local_center = tuple(_dot(_subtract(center, origin), axis) for axis in axes)
    for index, (coordinate, (lower, upper)) in enumerate(
        zip(local_center, bounds, strict=True)
    ):
        if (
            coordinate < lower - _CENTER_TOLERANCE_MM
            or coordinate > upper + _CENTER_TOLERANCE_MM
        ):
            raise ValueError(
                f"bolt center is outside member bounds on frame axis {index}"
            )

    axial_force = _dot(force, bolt_axis)
    lateral_force = _subtract(force, _scale(axial_force, bolt_axis))
    lateral_magnitude = _norm(lateral_force)
    grain_force = _dot(lateral_force, grain)
    cross_axis = axes[cross_grain_axis_index]
    cross_force = _dot(lateral_force, cross_axis)
    cross_grain_force = _scale(cross_force, cross_axis)

    grain_result = _directional_boundary(
        kind="grain_end",
        signed_component_n=grain_force,
        component_axis_global_xyz=grain,
        axis_alignment=grain_alignment,
        member_axis_index=grain_axis_index,
        local_coordinate_mm=local_center[grain_axis_index],
        axis_bounds_mm=bounds[grain_axis_index],
        lateral_magnitude_n=lateral_magnitude,
    )
    cross_result = _directional_boundary(
        kind="cross_grain_edge",
        signed_component_n=cross_force,
        component_axis_global_xyz=cross_axis,
        axis_alignment=1.0,
        member_axis_index=cross_grain_axis_index,
        local_coordinate_mm=local_center[cross_grain_axis_index],
        axis_bounds_mm=bounds[cross_grain_axis_index],
        lateral_magnitude_n=lateral_magnitude,
    )

    return {
        "status": "direction_geometry_only",
        "load_convention": "force_on_member",
        "force_on_member_global_xyz_n": force,
        "force_along_bolt_axis_signed_n": axial_force,
        "bolt_lateral_force_global_xyz_n": lateral_force,
        "bolt_lateral_force_magnitude_n": lateral_magnitude,
        "force_parallel_to_grain_signed_n": grain_force,
        "force_cross_grain_global_xyz_n": cross_grain_force,
        "force_cross_grain_signed_on_frame_axis_n": cross_force,
        "grain_end_direction": grain_result,
        "cross_grain_edge_direction": cross_result,
        "bolt_center_local_coordinates_mm": local_center,
        "member_frame_axes_global_xyz": axes,
        "member_bounds_local_mm": bounds,
        "outer_box_only": True,
        "not_evaluated": [
            "nearby holes, notches, shoulders, or other finished cuts",
            "NDS end/edge distance table or detailing applicability",
            "wood or bolt resistance, utilization, or pass/fail",
            "per-fastener load sharing or fresh demand provenance",
        ],
    }


def _directional_boundary(
    *,
    kind: str,
    signed_component_n: float,
    component_axis_global_xyz: Vector3,
    axis_alignment: float,
    member_axis_index: int,
    local_coordinate_mm: float,
    axis_bounds_mm: tuple[float, float],
    lateral_magnitude_n: float,
) -> dict:
    lower, upper = axis_bounds_mm
    distances = {
        "lower_coordinate_boundary_mm": max(0.0, local_coordinate_mm - lower),
        "upper_coordinate_boundary_mm": max(0.0, upper - local_coordinate_mm),
    }
    is_zero = lateral_magnitude_n == 0.0 or (
        abs(signed_component_n)
        <= _RELATIVE_ZERO_COMPONENT_TOLERANCE * lateral_magnitude_n
    )
    if is_zero:
        return {
            "kind": kind,
            "signed_component_n": signed_component_n,
            "component_axis_global_xyz": component_axis_global_xyz,
            "status": "zero_component_no_loaded_boundary",
            "loaded_component_direction": None,
            "loaded_boundary_direction_global_xyz": None,
            "local_member_axis_index": member_axis_index,
            "local_boundary_side": None,
            "distance_to_loaded_outer_boundary_mm": None,
            "distance_to_both_outer_boundaries_mm": distances,
        }

    component_direction = "positive_axis" if signed_component_n > 0 else "negative_axis"
    coordinate_direction = math.copysign(1.0, signed_component_n) * axis_alignment
    if coordinate_direction > 0:
        side = "upper"
    else:
        side = "lower"
    distance_key = f"{side}_coordinate_boundary_mm"
    return {
        "kind": kind,
        "signed_component_n": signed_component_n,
        "component_axis_global_xyz": component_axis_global_xyz,
        "status": "signed_boundary_classified",
        "loaded_component_direction": component_direction,
        "loaded_boundary_direction_global_xyz": _scale(
            math.copysign(1.0, signed_component_n), component_axis_global_xyz
        ),
        "local_member_axis_index": member_axis_index,
        "local_boundary_side": f"{side}_coordinate_boundary",
        "distance_to_loaded_outer_boundary_mm": distances[distance_key],
        "distance_to_both_outer_boundaries_mm": distances,
    }


def _matching_axis(
    direction: Vector3, axes: tuple[Vector3, Vector3, Vector3], label: str
) -> tuple[int, float]:
    alignments = tuple(_dot(direction, axis) for axis in axes)
    index = max(range(3), key=lambda candidate: abs(alignments[candidate]))
    alignment = alignments[index]
    if abs(alignment) < 1.0 - _AXIS_TOLERANCE:
        raise ValueError(f"{label} must align with one member-frame axis")
    return index, alignment


def _frame(value: Sequence[Sequence[float]]) -> tuple[Vector3, Vector3, Vector3]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 3
    ):
        raise ValueError("member_axes_global_unit must contain three ordered axes")
    axes = tuple(
        _unit_vector(axis, f"member_axes_global_unit[{index}]")
        for index, axis in enumerate(value)
    )
    assert len(axes) == 3
    if any(
        abs(_dot(axes[first], axes[second])) > _AXIS_TOLERANCE
        for first, second in ((0, 1), (0, 2), (1, 2))
    ):
        raise ValueError("member frame axes must be orthogonal")
    handedness = _dot(_cross(axes[0], axes[1]), axes[2])
    if abs(handedness - 1.0) > _AXIS_TOLERANCE:
        raise ValueError("member frame axes must be right-handed")
    return axes  # type: ignore[return-value]


def _bounds(value: Sequence[Sequence[float]]) -> Bounds3:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 3
    ):
        raise ValueError("member_bounds_local_mm must contain three lower/upper pairs")
    parsed: list[tuple[float, float]] = []
    for index, pair in enumerate(value):
        if (
            not isinstance(pair, Sequence)
            or isinstance(pair, (str, bytes))
            or len(pair) != 2
        ):
            raise ValueError(
                f"member_bounds_local_mm[{index}] must be a lower/upper pair"
            )
        lower, upper = (
            _finite_number(pair[0], "lower bound"),
            _finite_number(pair[1], "upper bound"),
        )
        if lower >= upper:
            raise ValueError(f"member_bounds_local_mm[{index}] must have lower < upper")
        parsed.append((lower, upper))
    return tuple(parsed)  # type: ignore[return-value]


def _unit_vector(value: Sequence[float], name: str) -> Vector3:
    vector = _vector(value, name)
    magnitude = _norm(vector)
    if abs(magnitude - 1.0) > _AXIS_TOLERANCE:
        raise ValueError(f"{name} must be a unit vector")
    return vector


def _vector(value: Sequence[float], name: str) -> Vector3:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 3
    ):
        raise ValueError(f"{name} must be a finite 3-vector")
    vector = tuple(_finite_number(component, name) for component in value)
    return vector  # type: ignore[return-value]


def _finite_number(value: object, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{label} must contain only finite numbers")
    return float(value)


def _dot(first: Vector3, second: Vector3) -> float:
    result = sum(left * right for left, right in zip(first, second, strict=True))
    if not math.isfinite(result):
        raise ValueError("vector operation produced a nonfinite value")
    return result


def _cross(first: Vector3, second: Vector3) -> Vector3:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _norm(vector: Vector3) -> float:
    result = math.hypot(*vector)
    if not math.isfinite(result):
        raise ValueError("vector magnitude is nonfinite")
    return result


def _scale(scalar: float, vector: Vector3) -> Vector3:
    result = tuple(scalar * component for component in vector)
    if any(not math.isfinite(component) for component in result):
        raise ValueError("vector operation produced a nonfinite value")
    return result  # type: ignore[return-value]


def _subtract(first: Vector3, second: Vector3) -> Vector3:
    result = tuple(left - right for left, right in zip(first, second, strict=True))
    if any(not math.isfinite(component) for component in result):
        raise ValueError("vector operation produced a nonfinite value")
    return result  # type: ignore[return-value]
