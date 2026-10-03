"""Clip a rectangular blank minus disjoint full axis-aligned cylinders.

Coordinates are grain, u, v, with bounds [0, L], [-w/2, w/2], [-d/2, d/2].
Transverse shafts use 3 - removed_interval_axis; longitudinal shafts use 0.
The parent owns frozen-source authentication and saved mass/centroid checks.
This module performs no I/O, CAD inspection, mechanics or resistance analysis.
The parent executes analytical_coupon() before adopting the clipping arithmetic.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from itertools import combinations
from numbers import Integral, Real

GEOMETRY_TOL_MM = 1e-6
AXIS_TOL = 1e-8
VOLUME_TOL_MM3 = 0.001
_GEOMETRY_KEYS = frozenset(
    [
        "grain_length_mm",
        "width_depth_mm",
        "bores",
        "longitudinal_holes",
        "block",
        "grain_frame_rows_xyz",
        "start_xyz_mm",
        "center_xyz_mm",
        "scope",
        "geometry_method",
        "analytic_finished_volume_mm3",
        "source_finished_volume_mm3",
        "saved_finished_volume_mm3",
        "finished_step_path",
        "finished_step_sha256",
    ]
)
_CYLINDER_KEYS = frozenset(
    [
        "axis_id",
        "radius_mm",
        "axis_unit_grain_u_v",
        "axis_parameter_interval_mm",
        "source_center_grain_u_v_mm",
    ]
)
_TRANSVERSE_KEYS = _CYLINDER_KEYS | {
    "station_mm",
    "transverse_center_mm",
    "removed_interval_axis",
}
_LONGITUDINAL_KEYS = _CYLINDER_KEYS | {"disk_center_uv_mm", "full_v_strip_mm"}


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{label}: finite real number required")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label}: finite real number required")
    return value


def _vector(value, size, label):
    if not isinstance(value, (list, tuple)) or len(value) != size:
        raise ValueError(f"{label}: {size} coordinates required")
    return [_number(item, label) for item in value]


def _metadata(hole, shaft, center, radius, bounds):
    """Check optional source direction, center and full-through span metadata."""
    direction = None
    if "axis_unit_grain_u_v" in hole:
        direction = _vector(hole["axis_unit_grain_u_v"], 3, "cylinder direction")
        if abs(abs(direction[shaft]) - 1) > AXIS_TOL or any(
            abs(direction[j]) > AXIS_TOL for j in range(3) if j != shaft
        ):
            raise ValueError("oblique or inconsistent cylinder axis")
    origin = None
    if "source_center_grain_u_v_mm" in hole:
        origin = _vector(hole["source_center_grain_u_v_mm"], 3, "source center")
        if any(
            abs(origin[j] - center[j]) > GEOMETRY_TOL_MM for j in range(3) if j != shaft
        ):
            raise ValueError("source center differs from the declared disk center")
    if "axis_parameter_interval_mm" in hole:
        interval = _vector(hole["axis_parameter_interval_mm"], 2, "shaft interval")
        if direction is None or origin is None or interval[1] <= interval[0]:
            raise ValueError(
                "full-through interval requires its source axis and origin"
            )
        ends = sorted(origin[shaft] + direction[shaft] * t for t in interval)
        if any(abs(a - b) > GEOMETRY_TOL_MM for a, b in zip(ends, bounds[shaft])):
            raise ValueError("partial or extended cylinder span is unsupported")
    if "full_v_strip_mm" in hole:
        strip = _vector(hole["full_v_strip_mm"], 2, "longitudinal disk strip")
        if any(
            abs(a - b) > GEOMETRY_TOL_MM
            for a, b in zip(strip, [center[2] - radius, center[2] + radius])
        ):
            raise ValueError("longitudinal disk strip differs")


def validate_geometry(geom):
    """Return axis bounds and normalized (shaft, center, radius) cylinders.

    All disks must lie strictly inside their radial stock bounds and all
    cylinders must have positive clearance. Extra shape fields, trims, blind
    bores and oblique source axes are refused. Optional saved volumes are
    checked against the declared shape, not treated as inspection evidence.
    Harmless metadata keys are limited to the existing geometry convention.
    """
    if not isinstance(geom, Mapping) or set(geom) - _GEOMETRY_KEYS:
        raise ValueError(
            "unsupported geometry fields; rectangular full-bore shape required"
        )
    length = _number(geom.get("grain_length_mm"), "grain length")
    width, depth = _vector(geom.get("width_depth_mm"), 2, "width/depth")
    if min(length, width, depth) <= 0:
        raise ValueError("positive rectangular dimensions required")
    bounds = [[0.0, length], [-width / 2, width / 2], [-depth / 2, depth / 2]]
    cylinders = []
    for longitudinal, key, allowed in (
        (False, "bores", _TRANSVERSE_KEYS),
        (True, "longitudinal_holes", _LONGITUDINAL_KEYS),
    ):
        holes = geom.get(key, [])
        if not isinstance(holes, (list, tuple)):
            raise TypeError(f"{key}: cylinder list required")
        for hole in holes:
            if not isinstance(hole, Mapping) or set(hole) - allowed:
                raise ValueError("unsupported cylinder fields or trims")
            radius = _number(hole.get("radius_mm"), "bore radius")
            if radius <= 0:
                raise ValueError("positive bore radius required")
            if longitudinal:
                shaft = 0
                center = [
                    length / 2,
                    *_vector(hole.get("disk_center_uv_mm"), 2, "disk center"),
                ]
            else:
                removed = hole.get("removed_interval_axis")
                if (
                    isinstance(removed, bool)
                    or not isinstance(removed, Integral)
                    or removed not in (1, 2)
                ):
                    raise ValueError("transverse removed_interval_axis must be 1 or 2")
                shaft = 3 - int(removed)
                center = [_number(hole.get("station_mm"), "bore station"), 0.0, 0.0]
                center[removed] = _number(
                    hole.get("transverse_center_mm"), "transverse center"
                )
            for j, (lo, hi) in enumerate(bounds):
                if (
                    j != shaft
                    and min(center[j] - radius - lo, hi - center[j] - radius)
                    <= GEOMETRY_TOL_MM
                ):
                    raise ValueError(
                        "cylinder disk reaches a stock edge or lacks clearance"
                    )
            _metadata(hole, shaft, center, radius, bounds)
            cylinders.append((shaft, center, radius))
    for (shaft_a, center_a, radius_a), (shaft_b, center_b, radius_b) in combinations(
        cylinders, 2
    ):
        if shaft_a == shaft_b:
            distance = math.hypot(
                *(center_a[j] - center_b[j] for j in range(3) if j != shaft_a)
            )
        else:
            common = 3 - shaft_a - shaft_b
            distance = abs(center_a[common] - center_b[common])
        if distance - radius_a - radius_b <= GEOMETRY_TOL_MM:
            raise ValueError("cylinders overlap or lack positive clearance")
    full_volume = math.fsum(
        [
            length * width * depth,
            *[-math.pi * r**2 * (bounds[s][1] - bounds[s][0]) for s, _, r in cylinders],
        ]
    )
    if not math.isfinite(full_volume) or full_volume <= 0:
        raise ValueError("nonpositive or nonfinite retained full volume")
    for key in (
        "analytic_finished_volume_mm3",
        "source_finished_volume_mm3",
        "saved_finished_volume_mm3",
    ):
        if key in geom and abs(full_volume - _number(geom[key], key)) > VOLUME_TOL_MM3:
            raise ValueError(
                f"{key}: saved volume differs from rectangular full-bore shape"
            )
    return bounds, cylinders


def disk_segment(radius, offset):
    """Return disk area and centered first moment on coordinate <= offset.

    This is the analytic circle-segment formula used by the existing corner
    physical-gravity calculation; radius is positive and offset is finite.
    """
    radius = _number(radius, "disk radius")
    offset = _number(offset, "disk offset")
    if radius <= 0:
        raise ValueError("positive disk radius required")
    if offset <= -radius:
        return 0.0, 0.0
    if offset >= radius:
        return math.pi * radius**2, 0.0
    root = math.sqrt(max(0.0, radius**2 - offset**2))
    return (
        radius**2 * (math.asin(offset / radius) + math.pi / 2) + offset * root,
        -2 * root**3 / 3,
    )


def volume_first(geom, axis, station):
    """Return negative-half volume and [grain, u, v] first moments.

    Volume is in mm³ and first moments about the local origin are in mm⁴.
    Axis is integer 0, 1 or 2; finite stations outside stock bounds are clamped.
    Every call validates support and disjointness before subtracting cylinders.
    Inputs are not mutated and the returned first moments are a plain list.
    """
    if (
        isinstance(axis, bool)
        or not isinstance(axis, Integral)
        or axis not in (0, 1, 2)
    ):
        raise ValueError("cut axis must be 0, 1 or 2")
    axis = int(axis)
    station = _number(station, "cut station")
    bounds, cylinders = validate_geometry(geom)
    station = min(bounds[axis][1], max(bounds[axis][0], station))
    if station == bounds[axis][0]:
        return 0.0, [0.0, 0.0, 0.0]
    clipped = [list(pair) for pair in bounds]
    clipped[axis][1] = station
    blank = math.prod(hi - lo for lo, hi in clipped)
    volumes = [blank]
    moments = [[blank * (lo + hi) / 2] for lo, hi in clipped]
    for shaft, disk_center, radius in cylinders:
        center = list(disk_center)
        if axis == shaft:
            removed = math.pi * radius**2 * (station - bounds[axis][0])
            center[shaft] = (station + bounds[axis][0]) / 2
            offset_first = 0.0
        else:
            area, offset_first = disk_segment(radius, station - center[axis])
            span = bounds[shaft][1] - bounds[shaft][0]
            removed = area * span
            offset_first *= span
        volumes.append(-removed)
        for j in range(3):
            moments[j].append(-removed * center[j])
        moments[axis].append(-offset_first)
    volume = math.fsum(volumes)
    first = [math.fsum(items) for items in moments]
    if volume < 0 or not all(math.isfinite(x) for x in [volume, *first]):
        raise ValueError("negative or nonfinite retained half volume/first moments")
    return volume, first


def analytical_coupon():
    """Return expected and observed geometric known answers for parent execution.

    The mixed coupon has one full cylinder along each axis, all disjoint.
    Full volumes, shortened shafts, circular half disks, an off-center segment
    and both out-of-bounds clamps have closed-form volume and moment answers.
    This function reads no candidate files and assigns no mechanics capacity.
    """
    pi = math.pi
    geom = {
        "grain_length_mm": 12.0,
        "width_depth_mm": [10.0, 12.0],
        "bores": [
            {
                "radius_mm": 1.0,
                "station_mm": 3.0,
                "transverse_center_mm": 0.0,
                "removed_interval_axis": 2,
            },
            {
                "radius_mm": 1.0,
                "station_mm": 9.0,
                "transverse_center_mm": 2.0,
                "removed_interval_axis": 1,
            },
        ],
        "longitudinal_holes": [{"radius_mm": 1.0, "disk_center_uv_mm": [-2.0, -3.0]}],
    }
    full = (1440 - 34 * pi, [8640 - 210 * pi, 0.0, 36 * pi])
    answers = [
        ("full_mixed_cylinders", geom, 0, 12.0, *full),
        (
            "shortened_grain_shaft",
            geom,
            0,
            6.0,
            720 - 16 * pi,
            [2160 - 48 * pi, 12 * pi, 18 * pi],
        ),
        (
            "transverse_half_disk",
            geom,
            0,
            3.0,
            360 - 8 * pi,
            [540 - 19.5 * pi + 20 / 3, 6 * pi, 9 * pi],
        ),
        (
            "longitudinal_u_half_disk",
            geom,
            1,
            -2.0,
            432 - 9 * pi,
            [2592 - 45 * pi, -1512 + 22.5 * pi + 8, 18 * pi],
        ),
        (
            "longitudinal_v_half_disk",
            geom,
            2,
            -3.0,
            360 - 9 * pi,
            [2160 - 63 * pi, 6 * pi, -1620 + 31.5 * pi + 8],
        ),
    ]
    for axis, low, high in ((0, -1.0, 13.0), (1, -6.0, 6.0), (2, -7.0, 7.0)):
        answers.extend(
            [
                (f"empty_clamp_axis_{axis}", geom, axis, low, 0.0, [0.0, 0.0, 0.0]),
                (f"full_clamp_axis_{axis}", geom, axis, high, *full),
            ]
        )
    single = {**geom, "bores": []}
    root3 = math.sqrt(3)
    answers.append(
        (
            "longitudinal_offset_segment",
            single,
            1,
            -1.5,
            504 - 8 * pi - 3 * root3,
            [
                3024 - 48 * pi - 18 * root3,
                -1638 + 16 * pi + 9 * root3,
                24 * pi + 9 * root3,
            ],
        )
    )
    results = []
    for name, own, axis, station, expected_volume, expected_first in answers:
        observed_volume, observed_first = volume_first(own, axis, station)
        error = max(
            [
                abs(observed_volume - expected_volume),
                *[abs(a - b) for a, b in zip(observed_first, expected_first)],
            ]
        )
        if error > 1e-9:
            raise ValueError(f"geometric known answer differs: {name}: {error}")
        results.append(
            {
                "name": name,
                "axis": axis,
                "station_mm": station,
                "expected_volume_mm3": expected_volume,
                "observed_volume_mm3": observed_volume,
                "expected_first_moment_grain_u_v_mm4": expected_first,
                "observed_first_moment_grain_u_v_mm4": observed_first,
                "maximum_absolute_error": error,
            }
        )
    return {"known_answers_satisfied": True, "cases": results}
