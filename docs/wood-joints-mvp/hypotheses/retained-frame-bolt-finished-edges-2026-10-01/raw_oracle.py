#!/usr/bin/env python3
"""Independent stdlib checker for retained-bolt finished-ray evidence.

The oracle reads saved face signatures and signed load-path records as data. It
does not import the finished-ray method or its report producer, and it does not
use CAD, native solvers, stock-box dimensions as a ray fallback, or resistance
helpers. The receipt is a replay/check record, not an acceptance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SURFACES_REL = Path(
    "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/surfaces.json"
)
AXIS_FEATURES_REL = Path(
    "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/axis-features.json"
)
SURFACE_SOURCE_PINS_REL = Path(
    "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/source-pins.json"
)
AXIS_SOURCE_PINS_REL = Path(
    "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/axis-source-pins.json"
)
CRITERIA_REL = Path("docs/wood-joints-mvp/criteria.json")
DEFAULT_LOAD_REPORT = Path(
    "/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json"
)
DEFAULT_RAW_RECEIPT = Path(
    "/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01-raw-oracle.json"
)
DEFAULT_RESISTANCE_REPORT = Path(
    "/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json"
)

EXPECTED_SCHEMA = "retained_frame_bolt_finished_edges/v1"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
LOAD_SHA256 = "f068cd5afc93c2b7027624b1fbec94ccb419f664833d920d2959f79bed661cc1"
LOAD_RAW_SHA256 = "c6d43017d67f864dfc25e6a77832a542a97257a1da23f4ca3a12e82d6a829ea9"
RESISTANCE_SHA256 = "c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1"
APPROVED_REPORT_SHA256 = "75db902ab8ebb64985592e8f1552333db763facb35d9be1630ec521202fe2332"
APPROVED_SOURCE_MANIFEST_SHA256 = "2d7050f533e315fb28a635b93546e1e5d2036011eddfb77e966dcd73c947f9c9"
APPROVED_METHOD_SHA256 = "3aabafb6c1ce25545ae00050dc213ba82a749a9c6ef5a8c0d4819f47c2532aa4"
APPROVED_PRODUCER_SHA256 = "55240f4dda242078be0179e43a4032b67b681a17522ee6844c00895280793ea1"
SURFACES_SHA256 = "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb"
AXIS_FEATURES_SHA256 = "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19"
SURFACE_SOURCE_PINS_SHA256 = "0e8cb56407f14e93d7ab95741115d4355a954eb845ae503365ba1da1149bd9cd"
AXIS_SOURCE_PINS_SHA256 = "7a501047c003174c15461ae12e3cd47af4e4bf59b1d40d3c8e5b76d8e1904d34"
SURFACES_PRODUCER_SHA256 = "a58e8f76b0d308352c734b6eab6bdea8c3adb75ab1c538e0905997d0232bab4f"
AXIS_FEATURES_PRODUCER_SHA256 = "e9787320589db65f1443b2c40607ed347cd5c4e8d5c8a2b9be73a5619275104f"
SURFACES_TEST_SHA256 = "2e7dce60cb030caf330b2ff82db6ad6a84fee53827745a90c58ee8b967c62b1a"
AXES = tuple(
    f"{kind}_bolt_{side}_{number}"
    for kind in ("lumber_leg", "rail_front", "rail_rear")
    for side in ("left", "right")
    for number in (1, 2)
)
CASE_ORDER = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
RECEIVERS = {
    "base_floor_left", "base_floor_right", "base_post_outer_left",
    "base_post_outer_right", "base_side_left", "base_side_right",
    "lumber_leg_left", "lumber_leg_right",
}
FALSE_FLAGS = (
    "native_solve_executed", "qualified_for_design", "mechanical_acceptance",
    "joint_demand_accepted", "floor_capacity_established", "friction_qualified",
    "joint_accepted", "fabrication_release", "CAD_executed",
    "geometry_regenerated_or_changed", "engineering_mvp_complete",
)
EPS = sys.float_info.epsilon
GEOMETRY_TOL = 2e-6
PLANE_TOL = 2e-7
TRIM_TOL = 2e-6
GROUP_TOL = 2e-6


class OracleError(ValueError):
    """Raised for a changed pin, malformed signature, or nonreconciling report."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OracleError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value: Any) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"),
                              allow_nan=False).encode("utf-8"))


def resolved(path: Path) -> Path:
    return path.resolve()


def read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise OracleError(f"cannot read {path}: {error}") from error


def read_json(path: Path) -> tuple[Any, bytes]:
    raw = read_bytes(path)
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OracleError(f"invalid JSON at {path}: {error}") from error
    return value, raw


def finite(value: Any, label: str) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool),
            f"{label} is not numeric")
    result = float(value)
    require(math.isfinite(result), f"{label} is not finite")
    return result


def vec(value: Any, label: str) -> list[float]:
    require(isinstance(value, list) and len(value) == 3, f"{label} must be a 3-vector")
    return [finite(component, f"{label}[{index}]") for index, component in enumerate(value)]


def add(a: list[float], b: list[float]) -> list[float]:
    return [a[i] + b[i] for i in range(3)]


def sub(a: list[float], b: list[float]) -> list[float]:
    return [a[i] - b[i] for i in range(3)]


def scale(value: float, a: list[float]) -> list[float]:
    return [value * component for component in a]


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(a[i] * b[i] for i in range(3))


def norm(a: list[float]) -> float:
    return math.sqrt(math.fsum(component * component for component in a))


def unit(a: list[float], label: str) -> list[float]:
    length = norm(a)
    require(length > 0.0, f"{label} has zero length")
    return [component / length for component in a]


def cross(a: list[float], b: list[float]) -> list[float]:
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def close(a: float, b: float, tolerance: float = GEOMETRY_TOL) -> bool:
    return abs(a - b) <= tolerance + 64.0 * EPS * max(1.0, abs(a), abs(b))


def close_vec(a: list[float], b: list[float], tolerance: float = GEOMETRY_TOL) -> bool:
    return all(close(x, y, tolerance) for x, y in zip(a, b, strict=True))


def compare(actual: Any, expected: Any, label: str, *, numeric_tol: float = GEOMETRY_TOL) -> None:
    """Recursively require every independently derived field in the report."""
    if expected is None or isinstance(expected, (str, bool, int)):
        require(actual == expected, f"{label}: {actual!r} != {expected!r}")
    elif isinstance(expected, float):
        got = finite(actual, label)
        require(close(got, expected, numeric_tol),
                f"{label}: {got:.17g} != {expected:.17g}")
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected),
                f"{label}: array length/schema differs")
        for index, (got, want) in enumerate(zip(actual, expected, strict=True)):
            compare(got, want, f"{label}[{index}]", numeric_tol=numeric_tol)
    elif isinstance(expected, dict):
        require(isinstance(actual, dict), f"{label}: expected object")
        for key, want in expected.items():
            require(key in actual, f"{label}: missing {key}")
            compare(actual[key], want, f"{label}.{key}", numeric_tol=numeric_tol)
    else:
        raise OracleError(f"{label}: unsupported comparison type {type(expected).__name__}")


def pin_file(path: Path, expected: str, label: str) -> bytes:
    raw = read_bytes(path)
    require(sha_bytes(raw) == expected, f"changed pinned {label}: {path}")
    return raw


def load_pinned_json(path: Path, expected: str, label: str) -> tuple[Any, bytes]:
    raw = pin_file(path, expected, label)
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OracleError(f"pinned {label} is invalid JSON: {error}") from error
    require(isinstance(value, dict), f"pinned {label} root must be an object")
    return value, raw


def _line_loop(wire: dict[str, Any], label: str) -> list[list[float]]:
    edges = wire.get("edges")
    require(isinstance(edges, list) and len(edges) >= 3, f"{label}: invalid polygon wire")
    require(all(edge.get("curve_kind") == "LINE" for edge in edges),
            f"{label}: mixed/unsupported polygon wire")
    graph: list[list[list[float]]] = []
    for edge_index, edge in enumerate(edges):
        ends = edge.get("parameter_endpoint_global_xyz_mm")
        require(isinstance(ends, list) and len(ends) == 2,
                f"{label}: missing line endpoints")
        p0, p1 = vec(ends[0], f"{label}.edge[{edge_index}].start"), vec(
            ends[1], f"{label}.edge[{edge_index}].end")
        line = edge.get("line")
        require(isinstance(line, dict), f"{label}: line signature missing")
        line_origin = vec(line.get("origin_global_xyz_mm"), f"{label}.line_origin")
        line_direction = unit(vec(line.get("direction_global_xyz"), f"{label}.line_direction"), label)
        bounds = edge.get("parameter_bounds")
        require(isinstance(bounds, list) and len(bounds) == 2, f"{label}: line bounds missing")
        t0, t1 = finite(bounds[0], label), finite(bounds[1], label)
        require(close_vec(add(line_origin, scale(t0, line_direction)), p0, 2e-5)
                and close_vec(add(line_origin, scale(t1, line_direction)), p1, 2e-5),
                f"{label}: line endpoint signature fails")
        require(close(finite(edge.get("length_mm"), label), abs(t1 - t0), 2e-5),
                f"{label}: line length differs from its parameter interval")
        graph.append([p0, p1])

    points: list[list[float]] = []
    links: list[tuple[int, int]] = []
    for p0, p1 in graph:
        endpoints = []
        for point in (p0, p1):
            found = next((i for i, previous in enumerate(points)
                          if close_vec(point, previous, TRIM_TOL)), None)
            if found is None:
                points.append(point)
                found = len(points) - 1
            endpoints.append(found)
        require(endpoints[0] != endpoints[1], f"{label}: collapsed polygon segment")
        links.append((endpoints[0], endpoints[1]))
    adjacency: dict[int, list[int]] = {index: [] for index in range(len(points))}
    for first, second in links:
        adjacency[first].append(second)
        adjacency[second].append(first)
    require(all(len(neighbours) == 2 for neighbours in adjacency.values()),
            f"{label}: polygon wire is not a single closed chain")
    order = [0]
    previous = -1
    while len(order) < len(points):
        choices = [node for node in adjacency[order[-1]] if node != previous]
        nxt = choices[0]
        require(nxt not in order, f"{label}: self-repeated polygon vertex")
        previous, _ = order[-1], order[-1]
        order.append(nxt)
    require(order[-1] in adjacency[order[0]], f"{label}: polygon is open")
    return [points[index] for index in order]


def _full_circle(edge: dict[str, Any], label: str) -> dict[str, Any]:
    require(edge.get("curve_kind") == "CIRCLE", f"{label}: expected circle")
    circle = edge.get("circle")
    require(isinstance(circle, dict), f"{label}: circle signature missing")
    radius = finite(circle.get("radius_mm"), f"{label}.radius")
    require(radius > 0.0, f"{label}: nonpositive circle radius")
    axis = unit(vec(circle.get("axis_unit_global_xyz"), f"{label}.axis"), label)
    center = vec(circle.get("center_global_xyz_mm"), f"{label}.center")
    bounds = edge.get("parameter_bounds")
    require(isinstance(bounds, list) and len(bounds) == 2, f"{label}: circle interval missing")
    sweep = finite(bounds[1], label) - finite(bounds[0], label)
    require(close(sweep, 2.0 * math.pi, 1e-8), f"{label}: partial circle unsupported")
    require(close(finite(edge.get("length_mm"), label), 2.0 * math.pi * radius, 2e-5),
            f"{label}: circle circumference differs")
    return {"center": center, "axis": axis, "radius": radius}


def _basis2(normal: list[float]) -> tuple[list[float], list[float]]:
    seed = [1.0, 0.0, 0.0] if abs(normal[0]) < 0.8 else [0.0, 1.0, 0.0]
    u = unit(cross(normal, seed), "plane trim basis")
    v = unit(cross(normal, u), "plane trim basis")
    return u, v


def _plane_wire_loop(wire: dict[str, Any], origin: list[float], normal: list[float],
                     label: str) -> dict[str, Any]:
    edges = wire.get("edges")
    require(isinstance(edges, list) and edges, f"{label}: empty wire")
    kinds = {edge.get("curve_kind") for edge in edges}
    if kinds == {"LINE"}:
        vertices3 = _line_loop(wire, label)
        u, v = _basis2(normal)
        vertices2 = []
        for point in vertices3:
            rel = sub(point, origin)
            require(abs(dot(rel, normal)) <= 2e-5, f"{label}: polygon leaves its plane")
            vertices2.append((dot(rel, u), dot(rel, v)))
        area2 = math.fsum(vertices2[i][0] * vertices2[(i + 1) % len(vertices2)][1]
                          - vertices2[(i + 1) % len(vertices2)][0] * vertices2[i][1]
                          for i in range(len(vertices2))) * 0.5
        require(abs(area2) > 1e-10, f"{label}: zero-area polygon")
        return {"kind": "polygon", "points2": vertices2, "area": abs(area2), "outer_candidate": True}
    require(kinds == {"CIRCLE"} and len(edges) == 1,
            f"{label}: plane trim must be a line polygon or one full circle")
    circle = _full_circle(edges[0], label)
    require(abs(dot(sub(circle["center"], origin), normal)) <= 2e-5
            and abs(abs(dot(circle["axis"], normal)) - 1.0) <= 1e-8,
            f"{label}: circle is inconsistent with its plane")
    u, v = _basis2(normal)
    rel = sub(circle["center"], origin)
    return {"kind": "circle", "center2": (dot(rel, u), dot(rel, v)),
            "radius": circle["radius"], "circle3": circle, "area": math.pi * circle["radius"] ** 2,
            "outer_candidate": False}


def _inside_loop(point: tuple[float, float], loop: dict[str, Any], tolerance: float) -> tuple[bool, bool]:
    x, y = point
    if loop["kind"] == "circle":
        dx = x - loop["center2"][0]
        dy = y - loop["center2"][1]
        radial = math.hypot(dx, dy)
        return radial < loop["radius"] - tolerance, abs(radial - loop["radius"]) <= tolerance
    vertices = loop["points2"]
    inside = False
    boundary = False
    for index, p0 in enumerate(vertices):
        p1 = vertices[(index + 1) % len(vertices)]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        denom = dx * dx + dy * dy
        projection = 0.0 if denom == 0 else ((x - p0[0]) * dx + (y - p0[1]) * dy) / denom
        projection = min(1.0, max(0.0, projection))
        gap = math.hypot(x - (p0[0] + projection * dx), y - (p0[1] + projection * dy))
        if gap <= tolerance:
            boundary = True
            continue
        if (p0[1] > y) != (p1[1] > y):
            x_cross = p0[0] + (y - p0[1]) * dx / dy
            if x < x_cross:
                inside = not inside
    return inside, boundary


def _own_circle_match(circle: dict[str, Any], cylinder: dict[str, Any], tolerance: float = TRIM_TOL) -> bool:
    axis_origin = cylinder["axis_origin"]
    axis = cylinder["axis"]
    interval = cylinder["interval"]
    rel = sub(circle["center"], axis_origin)
    station = dot(rel, axis)
    radial = sub(rel, scale(station, axis))
    return (abs(abs(dot(circle["axis"], axis)) - 1.0) <= 1e-8
            and close(circle["radius"], cylinder["radius"], tolerance)
            and norm(radial) <= tolerance
            and min(abs(station - interval[0]), abs(station - interval[1])) <= tolerance)


def _parse_member(record: dict[str, Any]) -> dict[str, Any]:
    member = record.get("member_id")
    require(isinstance(member, str), "surface member lacks id")
    features = record.get("features")
    require(isinstance(features, list) and features, f"{member}: no face features")
    parsed = []
    feature_ids = set()
    for feature in features:
        feature_id = feature.get("feature_id")
        require(isinstance(feature_id, str) and feature_id not in feature_ids,
                f"{member}: duplicate/missing face id")
        feature_ids.add(feature_id)
        kind = feature.get("surface_kind")
        require(kind in ("PLANE", "CYLINDER"), f"{member}/{feature_id}: unsupported surface")
        trim = feature.get("trim")
        require(isinstance(trim, dict) and isinstance(trim.get("wires"), list),
                f"{member}/{feature_id}: missing trim wires")
        require(trim.get("wire_count") == len(trim["wires"])
                and trim.get("edge_count") == sum(len(w.get("edges", [])) for w in trim["wires"]),
                f"{member}/{feature_id}: trim counts differ")
        if kind == "PLANE":
            plane = feature.get("plane")
            require(isinstance(plane, dict), f"{member}/{feature_id}: plane signature missing")
            normal = unit(vec(plane.get("normal_global_xyz"), f"{feature_id}.plane.normal"), feature_id)
            station = finite(plane.get("signed_plane_station_global_mm"), f"{feature_id}.plane.station")
            stock_origin = vec(plane.get("stock_origin_global_xyz_mm"), f"{feature_id}.plane.origin")
            offset = finite(plane.get("signed_plane_offset_stock_mm"), f"{feature_id}.plane.offset")
            normal_stock = unit(vec(plane.get("normal_stock_gqr"), f"{feature_id}.plane.normal_stock"), feature_id)
            frame_basis = record["stock_frame"]["basis_columns_global_xyz"]
            transformed = [math.fsum(normal_stock[j] * frame_basis[j][i] for j in range(3))
                           for i in range(3)]
            require(close_vec(normal, unit(transformed, feature_id), 2e-8),
                    f"{member}/{feature_id}: stock/global plane normal mismatch")
            require(close(dot(normal, stock_origin) + offset, station, 2e-5),
                    f"{member}/{feature_id}: plane station/stock offset mismatch")
            origin = scale(station, normal)
            loops = []
            for wi, wire in enumerate(trim["wires"]):
                loops.append(_plane_wire_loop(wire, origin, normal, f"{feature_id}.wire{wi + 1}"))
            require(loops, f"{member}/{feature_id}: plane has no supported trim")
            for vertex in feature.get("vertices", []):
                point = vec(vertex.get("global_xyz_mm"), f"{feature_id}.vertex")
                require(abs(dot(normal, point) - station) <= 2e-5,
                        f"{member}/{feature_id}: vertex not on plane")
            parsed.append({"source": feature, "kind": kind, "normal": normal,
                           "station": station, "origin": origin, "loops": loops,
                           "feature_id": feature_id})
        else:
            cylinder = feature.get("cylinder")
            require(isinstance(cylinder, dict), f"{member}/{feature_id}: cylinder signature missing")
            axis_origin = vec(cylinder.get("axis_origin_global_xyz_mm"), f"{feature_id}.axis_origin")
            axis = unit(vec(cylinder.get("axis_unit_global_xyz"), f"{feature_id}.axis"), feature_id)
            interval = cylinder.get("axis_parameter_interval_mm")
            require(isinstance(interval, list) and len(interval) == 2, f"{feature_id}: interval missing")
            interval = [finite(interval[0], feature_id), finite(interval[1], feature_id)]
            require(interval[0] < interval[1], f"{feature_id}: invalid finite interval")
            station_alias = cylinder.get("axis_station_interval_mm")
            require(isinstance(station_alias, list) and len(station_alias) == 2
                    and all(close(finite(station_alias[i], feature_id), interval[i], 2e-7)
                            for i in range(2)),
                    f"{feature_id}: axis interval aliases disagree")
            radius = finite(cylinder.get("radius_mm"), f"{feature_id}.radius")
            require(radius > 0.0 and cylinder.get("material_side_geometry") in ("bore_like", "exterior_like"),
                    f"{feature_id}: invalid cylinder radius/side")
            radial_dot = finite(cylinder.get("radial_normal_dot"), f"{feature_id}.radial_dot")
            expected_sign = -1.0 if cylinder["material_side_geometry"] == "bore_like" else 1.0
            require(close(radial_dot, expected_sign, 1e-8), f"{feature_id}: radial normal sign changed")
            surface_bounds = trim.get("surface_parameter_bounds")
            require(isinstance(surface_bounds, dict), f"{feature_id}: cylinder surface bounds missing")
            urange = surface_bounds.get("u")
            vrange = surface_bounds.get("v")
            require(isinstance(urange, list) and len(urange) == 2
                    and close(finite(urange[1], feature_id) - finite(urange[0], feature_id),
                              2.0 * math.pi, 1e-8),
                    f"{feature_id}: non-full-turn cylinder unsupported")
            require(isinstance(vrange, list) and len(vrange) == 2
                    and close_vec([finite(vrange[0], feature_id), finite(vrange[1], feature_id), 0.0],
                                  [interval[0], interval[1], 0.0], 2e-5),
                    f"{feature_id}: cylinder parameter/finite interval mismatch")
            centerline_probe = vec(cylinder.get("normal_sample_global_xyz_mm"), f"{feature_id}.normal_sample")
            sample_rel = sub(centerline_probe, axis_origin)
            sample_station = dot(sample_rel, axis)
            sample_radial = sub(sample_rel, scale(sample_station, axis))
            require(interval[0] - 2e-5 <= sample_station <= interval[1] + 2e-5
                    and close(norm(sample_radial), radius, 2e-5),
                    f"{feature_id}: normal sample lies off its finite cylinder")
            circle_stations = []
            line_count = 0
            for wi, wire in enumerate(trim["wires"]):
                for edge in wire.get("edges", []):
                    if edge.get("curve_kind") == "CIRCLE":
                        circle = _full_circle(edge, f"{feature_id}.wire{wi + 1}")
                        require(close(circle["radius"], radius, 2e-5)
                                and abs(abs(dot(circle["axis"], axis)) - 1.0) < 1e-8,
                                f"{feature_id}: cylinder end circle mismatch")
                        circle_rel = sub(circle["center"], axis_origin)
                        circle_station = dot(circle_rel, axis)
                        circle_radial = sub(circle_rel, scale(circle_station, axis))
                        require(norm(circle_radial) <= 2e-5,
                                f"{feature_id}: cylinder end circle center misses its axis")
                        circle_stations.append(circle_station)
                    elif edge.get("curve_kind") == "LINE":
                        line_count += 1
                        bounds = edge.get("parameter_bounds")
                        line = edge.get("line")
                        ends = edge.get("parameter_endpoint_global_xyz_mm")
                        require(isinstance(bounds, list) and len(bounds) == 2
                                and isinstance(line, dict) and isinstance(ends, list) and len(ends) == 2,
                                f"{feature_id}: malformed cylinder generator")
                        ld = unit(vec(line.get("direction_global_xyz"), feature_id), feature_id)
                        lo = vec(line.get("origin_global_xyz_mm"), feature_id)
                        require(abs(abs(dot(ld, axis)) - 1.0) <= 1e-8,
                                f"{feature_id}: generator is not parallel to axis")
                        for tval, endpoint in zip(bounds, ends, strict=True):
                            require(close_vec(add(lo, scale(finite(tval, feature_id), ld)),
                                              vec(endpoint, feature_id), 2e-5),
                                    f"{feature_id}: generator endpoint mismatch")
                    else:
                        raise OracleError(f"{feature_id}: unsupported cylinder trim edge")
            require(len(circle_stations) == 2 and line_count >= 1
                    and all(any(close(station, endpoint, 2e-5) for endpoint in interval)
                            for station in circle_stations)
                    and all(any(close(station, endpoint, 2e-5) for station in circle_stations)
                            for endpoint in interval),
                    f"{feature_id}: finite cylinder end loops do not cover its interval")
            parsed.append({"source": feature, "kind": kind, "axis_origin": axis_origin,
                           "axis": axis, "interval": interval, "radius": radius,
                           "material_side": cylinder["material_side_geometry"],
                           "normal_sign": expected_sign, "feature_id": feature_id})
    return {"record": record, "member": member, "features": parsed,
            "by_id": {face["feature_id"]: face for face in parsed}}


def _point_in_plane(face: dict[str, Any], point: list[float], own: dict[str, Any]) -> tuple[str, bool]:
    normal = face["normal"]
    origin = face["origin"]
    u, v = _basis2(normal)
    rel = sub(point, origin)
    point2 = (dot(rel, u), dot(rel, v))
    parity = False
    boundary = False
    kept = []
    for loop in face["loops"]:
        if loop["kind"] == "circle" and _own_circle_match(loop["circle3"], own):
            continue
        inside, on_edge = _inside_loop(point2, loop, TRIM_TOL)
        if on_edge:
            boundary = True
        elif inside:
            parity = not parity
        kept.append(loop)
    if boundary:
        return "trim_boundary", False
    return ("interior" if parity else "outside"), any(
        loop["kind"] == "polygon" and _inside_loop(point2, loop, TRIM_TOL)[0]
        for loop in kept)


def _is_blind_cap(member: dict[str, Any], face: dict[str, Any]) -> bool:
    loops = face["loops"]
    if len(loops) != 1 or loops[0]["kind"] != "circle":
        return False
    circle = loops[0]["circle3"]
    for other in member["features"]:
        if other["kind"] != "CYLINDER" or other["material_side"] != "bore_like":
            continue
        if _own_circle_match(circle, other):
            return True
    return False


def _plane_classification(member: dict[str, Any], face: dict[str, Any],
                          point: list[float], own: dict[str, Any]) -> tuple[str, str]:
    trim_position, polygon_region = _point_in_plane(face, point, own)
    if trim_position == "trim_boundary":
        return trim_position, "ambiguous"
    if trim_position == "outside":
        return "outside", "outside"
    if not polygon_region and _is_blind_cap(member, face):
        return trim_position, "blind_circular_cap"
    if polygon_region:
        return trim_position, "polygon_outerwire_plane"
    return trim_position, "non_exterior_plane"


def _face_hits(member: dict[str, Any], own_id: str, origin: list[float],
               direction: list[float]) -> tuple[list[dict[str, Any]], list[str]]:
    own = member["by_id"].get(own_id)
    require(own is not None and own["kind"] == "CYLINDER"
            and own["material_side"] == "bore_like", f"{member['member']}/{own_id}: own bore changed")
    hits: list[dict[str, Any]] = []
    warnings: list[str] = []
    for face in member["features"]:
        if face["feature_id"] == own_id:
            continue
        if face["kind"] == "PLANE":
            denom = dot(face["normal"], direction)
            gap = face["station"] - dot(face["normal"], origin)
            if abs(denom) <= 1e-12:
                if abs(gap) <= PLANE_TOL:
                    warnings.append(f"coplanar ray: {face['feature_id']}")
                continue
            distance = gap / denom
            point = add(origin, scale(distance, direction))
            position, classification = _plane_classification(member, face, point, own)
            if position == "outside":
                continue
            tangent = abs(denom) <= 1e-11
            entry_exit = ("tangent" if tangent else "exit" if denom > 0.0 else "entry")
            if position == "trim_boundary":
                entry_exit = "ambiguous"
            hits.append({"distance": distance, "point": point,
                         "feature_id": face["feature_id"], "surface_kind": "PLANE",
                         "normal_dot": denom, "entry_or_exit": entry_exit,
                         "tangent": tangent, "trim_position": position,
                         "exterior_classification": classification,
                         "corner_ambiguity": position == "trim_boundary"})
        else:
            axis = face["axis"]
            rel = sub(origin, face["axis_origin"])
            d_parallel = dot(direction, axis)
            p_parallel = dot(rel, axis)
            d_perp = sub(direction, scale(d_parallel, axis))
            p_perp = sub(rel, scale(p_parallel, axis))
            aa = dot(d_perp, d_perp)
            cc = dot(p_perp, p_perp) - face["radius"] ** 2
            if aa <= 1e-18:
                if abs(cc) <= PLANE_TOL:
                    warnings.append(f"ray lies on cylinder: {face['feature_id']}")
                continue
            bb = 2.0 * dot(p_perp, d_perp)
            discriminant = bb * bb - 4.0 * aa * cc
            disc_scale = max(bb * bb, abs(4.0 * aa * cc), face["radius"] ** 4, 1.0)
            disc_tol = 128.0 * EPS * disc_scale
            if discriminant < -disc_tol:
                continue
            tangent = discriminant <= disc_tol
            root = math.sqrt(max(0.0, discriminant))
            roots = [-bb / (2.0 * aa)] if tangent else sorted(((-bb - root) / (2.0 * aa),
                                                                 (-bb + root) / (2.0 * aa)))
            for distance in roots:
                point = add(origin, scale(distance, direction))
                point_rel = sub(point, face["axis_origin"])
                station = dot(point_rel, axis)
                tol_station = TRIM_TOL
                if station < face["interval"][0] - tol_station or station > face["interval"][1] + tol_station:
                    continue
                radial = sub(point_rel, scale(station, axis))
                radial_unit = unit(radial, face["feature_id"] + " radial")
                normal = scale(face["normal_sign"], radial_unit)
                normal_dot = dot(normal, direction)
                at_end = min(abs(station - face["interval"][0]),
                             abs(station - face["interval"][1])) <= tol_station
                entry_exit = ("tangent" if tangent or abs(normal_dot) <= 1e-11
                              else "exit" if normal_dot > 0.0 else "entry")
                if at_end and not tangent:
                    entry_exit = "ambiguous"
                hits.append({"distance": distance, "point": point,
                             "feature_id": face["feature_id"], "surface_kind": "CYLINDER",
                             "normal_dot": normal_dot, "entry_or_exit": entry_exit,
                             "tangent": tangent or abs(normal_dot) <= 1e-11,
                             "trim_position": "trim_boundary" if at_end else "interior",
                             "exterior_classification": "bore_wall" if face["material_side"] == "bore_like"
                             else "outer_cylindrical_surface",
                             "corner_ambiguity": at_end})
    return hits, warnings


def _group_hits(hits: list[dict[str, Any]], direction: list[float]) -> list[dict[str, Any]]:
    ordered = sorted(hits, key=lambda hit: hit["distance"])
    groups: list[list[dict[str, Any]]] = []
    for hit in ordered:
        if not groups or abs(hit["distance"] - groups[-1][0]["distance"]) > GROUP_TOL:
            groups.append([hit])
        else:
            groups[-1].append(hit)
    events = []
    for group in groups:
        distance = math.fsum(hit["distance"] for hit in group) / len(group)
        point = add(group[0]["point"], scale(distance - group[0]["distance"], direction))
        ids = sorted({hit["feature_id"] for hit in group})
        kinds = {hit["surface_kind"] for hit in group}
        entries = {hit["entry_or_exit"] for hit in group}
        tangent = any(hit["tangent"] for hit in group)
        corner = len(group) > 1 or any(hit["corner_ambiguity"] for hit in group)
        exterior_kinds = {hit["exterior_classification"] for hit in group}
        if tangent:
            transition = "tangent"
        elif corner or len(entries) != 1:
            transition = "ambiguous"
        else:
            transition = next(iter(entries))
        exterior = next(iter(exterior_kinds)) if len(exterior_kinds) == 1 else "ambiguous"
        normal_dots = [hit["normal_dot"] for hit in group]
        events.append({"distance_mm": distance,
                       "point_global_xyz_mm": point,
                       "feature_id": ids[0] if len(ids) == 1 else None,
                       "feature_ids": ids,
                       "surface_kind": next(iter(kinds)) if len(kinds) == 1 else "SIMULTANEOUS",
                       "oriented_normal_dot": normal_dots[0] if len(normal_dots) == 1 else None,
                       "entry_or_exit": transition,
                       "tangent": tangent,
                       "corner_ambiguity": corner,
                       "exterior_classification": exterior,
                       "hits": [{"feature_id": hit["feature_id"],
                                 "surface_kind": hit["surface_kind"],
                                 "oriented_normal_dot": hit["normal_dot"],
                                 "entry_or_exit": hit["entry_or_exit"],
                                 "tangent": hit["tangent"],
                                 "trim_position": "IN" if hit["trim_position"] == "interior" else "ON",
                                 "exterior_classification": hit["exterior_classification"]}
                                for hit in sorted(group, key=lambda row: row["feature_id"])]})
    return events


def _origin_membership(member: dict[str, Any], own_id: str,
                       origin: list[float], direction: list[float]) -> dict[str, Any]:
    # Both signed half-lines must point from the filled-own-bore interior out
    # through outward-oriented saved faces. The queried line is not assumed to
    # be inside merely because its point lies on the mapped bolt axis.
    answers = []
    for probe_direction in (direction, scale(-1.0, direction)):
        hits, warnings = _face_hits(member, own_id, origin, probe_direction)
        events = _group_hits([hit for hit in hits if hit["distance"] > GROUP_TOL], probe_direction)
        if warnings or not events:
            answers.append("ambiguous")
        elif events[0]["entry_or_exit"] == "exit":
            answers.append("inside")
        elif events[0]["entry_or_exit"] == "entry":
            answers.append("outside")
        else:
            answers.append("ambiguous")
    if answers == ["inside", "inside"]:
        return {"status": "inside_filled_own_bore",
                "reason": "both signed directions have clear outward material crossings"}
    if answers == ["outside", "outside"]:
        return {"status": "outside",
                "reason": "both signed directions have clear inward material crossings"}
    return {"status": "ambiguous",
            "reason": "signed origin probes disagree or meet an ambiguous boundary"}


def _ray(member: dict[str, Any], own_id: str, origin: list[float],
         direction: list[float]) -> dict[str, Any]:
    origin_membership = _origin_membership(member, own_id, origin, direction)
    if origin_membership["status"] != "inside_filled_own_bore":
        status = "ambiguous" if origin_membership["status"] == "ambiguous" else "unsupported"
        return {"schema": "retained_frame_bolt_finished_edge_query/v1",
                "status": status, "member_id": member["member"], "own_feature_id": own_id,
                "origin_global_xyz_mm": origin, "direction_global_unit": direction,
                "origin_membership": origin_membership,
                "events": [], "first_material_exit": None, "first_exterior_exit": None,
                "distance_mm": None,
                "exterior_classification": {"status": status, "kind": None,
                                             "reason": "query origin could not be certified inside filled-own-bore geometry"},
                "reason": "query origin membership unresolved",
                "limits": ["geometric ray distance only; no NDS, Cdelta, group, splitting, or acceptance calculation",
                           "query origin is the supplied interior bolt-bore station and is separate from the physical force point",
                           "directional station results do not establish a through-depth minimum",
                           "saved plane normals are already outward and are not flipped from topology labels"]}
    hits, warnings = _face_hits(member, own_id, origin, direction)
    # A directional ray is the nonnegative half of its signed line profile.
    forward = [hit for hit in hits if hit["distance"] >= -GROUP_TOL]
    events = _group_hits(forward, direction)
    material_exit = None
    exterior_exit = None
    unresolved_before_exterior = False
    for event in events:
        distance = event["distance_mm"]
        if distance < -GROUP_TOL:
            continue
        if event["entry_or_exit"] == "ambiguous" or event["entry_or_exit"] == "tangent":
            # Tangencies are recorded but do not toggle material occupancy.
            if event["entry_or_exit"] == "ambiguous":
                unresolved_before_exterior = True
            continue
        if event["entry_or_exit"] == "exit" and material_exit is None:
            material_exit = event
        if (event["entry_or_exit"] == "exit"
                and event["exterior_classification"] == "polygon_outerwire_plane"
                and exterior_exit is None):
            exterior_exit = event
    status = "ok"
    reason = "analytic face-ray profile resolved from saved finite trims"
    if warnings or unresolved_before_exterior:
        status = "ambiguous"
        reason = warnings[0] if warnings else "a trim corner made a preceding boundary ambiguous"
    elif exterior_exit is None:
        status = "unsupported"
        reason = "no resolved exterior polygon-plane exit exists on this ray"
    distance = exterior_exit["distance_mm"] if status == "ok" and exterior_exit else None
    if status == "ok":
        ext_result = {"status": "classified", "kind": "polygon_outerwire_plane", "reason": None}
    else:
        ext_result = {"status": status, "kind": None, "reason": reason}
    return {"schema": "retained_frame_bolt_finished_edge_query/v1",
            "status": status,
            "member_id": member["member"],
            "own_feature_id": own_id,
            "origin_global_xyz_mm": origin,
            "direction_global_unit": direction,
            "origin_membership": origin_membership,
            "events": events,
            "first_material_exit": material_exit,
            "first_exterior_exit": exterior_exit,
            "distance_mm": distance,
            "exterior_classification": ext_result,
            "reason": None if status == "ok" else reason,
            "limits": ["geometric ray distance only; no NDS, Cdelta, group, splitting, or acceptance calculation",
                       "query origin is the supplied interior bolt-bore station and is separate from the physical force point",
                       "directional station results do not establish a through-depth minimum",
                       "saved plane normals are already outward and are not flipped from topology labels"]}


def _validate_source_chains(report: dict[str, Any], load: dict[str, Any]) -> dict[str, Any]:
    surfaces, surfaces_raw = load_pinned_json(ROOT / SURFACES_REL, SURFACES_SHA256, "surface register")
    axis_data, axis_raw = load_pinned_json(ROOT / AXIS_FEATURES_REL, AXIS_FEATURES_SHA256,
                                           "axis-feature register")
    surface_pins, surface_pin_raw = load_pinned_json(ROOT / SURFACE_SOURCE_PINS_REL,
                                                      SURFACE_SOURCE_PINS_SHA256,
                                                      "surface source-pin manifest")
    axis_pins, axis_pin_raw = load_pinned_json(ROOT / AXIS_SOURCE_PINS_REL,
                                                AXIS_SOURCE_PINS_SHA256,
                                                "axis source-pin manifest")
    require(surfaces.get("producer_sha256") == SURFACES_PRODUCER_SHA256,
            "surface register producer binding changed")
    require(axis_data.get("source_hashes", {}).get("surfaces_producer_sha256")
            == SURFACES_PRODUCER_SHA256,
            "axis-feature surface-producer binding changed")
    require(report.get("source_manifest_sha256") == APPROVED_SOURCE_MANIFEST_SHA256
            and report.get("source_manifest_sha256") == sha_bytes(read_bytes(HERE / "source-pins.json")),
            "finished-ray source manifest hash does not match its bytes")
    manifest, manifest_raw = read_json(HERE / "source-pins.json")
    require(isinstance(manifest, dict) and isinstance(manifest.get("pins"), dict),
            "finished-ray source manifest is malformed")
    require(report.get("source_pins") == manifest["pins"],
            "report source-pin map differs from the source manifest")
    for relative, pin in manifest["pins"].items():
        require(isinstance(relative, str) and isinstance(pin, dict)
                and isinstance(pin.get("sha256"), str), f"malformed source pin {relative!r}")
        path = ROOT / relative
        raw = read_bytes(path)
        require(sha_bytes(raw) == pin["sha256"], f"finished-ray source changed: {relative}")
        if "size_bytes" in pin:
            require(len(raw) == pin["size_bytes"], f"finished-ray source size changed: {relative}")
    require(report.get("producer_sha256") == APPROVED_PRODUCER_SHA256
            and report.get("producer_sha256") == sha_bytes(read_bytes(HERE / "produce.py")),
            "report producer hash does not match bytes")
    require(report.get("method_sha256") == APPROVED_METHOD_SHA256
            and report.get("method_sha256") == sha_bytes(read_bytes(HERE / "method.py")),
            "report method hash does not match bytes")
    require(surfaces.get("candidate") == CANDIDATE
            and surfaces.get("geometry_revision_id") == REVISION
            and surfaces.get("record_count") == 44
            and not surfaces.get("unsupported_faces")
            and not surfaces.get("ambiguous_cylinder_material_side_feature_ids"),
            "finished-face register identity or coverage changed")
    require(axis_data.get("candidate") == CANDIDATE
            and axis_data.get("geometry_revision_id") == REVISION,
            "axis-feature register identity changed")
    # Recheck both upstream manifest payloads, without invoking their producers.
    chain_rows = []
    surface_table = surface_pins.get("pins")
    require(isinstance(surface_table, dict) and surface_table,
            "surface source chain has no pin table")
    chain_rows.extend(("surface", row) for row in surface_table.values())
    for name in ("sources", "outputs"):
        table = axis_pins.get(name)
        require(isinstance(table, dict) and table, f"axis source chain omits {name}")
        chain_rows.extend(("axis", row) for row in table.values())
    for label, row in chain_rows:
        require(isinstance(row, dict) and isinstance(row.get("path"), str)
                and isinstance(row.get("sha256"), str), f"{label} chain row is malformed")
        raw = read_bytes(ROOT / row["path"])
        require(sha_bytes(raw) == row["sha256"],
                f"{label} chain source changed: {row['path']}")
        if "size_bytes" in row:
            require(len(raw) == row["size_bytes"],
                    f"{label} source size changed: {row['path']}")
    require(report.get("rechecked_load_input_pins") == load.get("input_pins"),
            "the report did not preserve the original 143 load-source pins")
    require(isinstance(load.get("input_pins"), dict) and len(load["input_pins"]) == 143,
            "upstream authenticated load-source census changed")
    for relative, pin in load["input_pins"].items():
        require(isinstance(pin, dict) and isinstance(pin.get("sha256"), str),
                f"malformed load-source pin: {relative}")
        raw = read_bytes(ROOT / relative)
        require(sha_bytes(raw) == pin["sha256"], f"original load source changed: {relative}")
        require(len(raw) == pin.get("size_bytes"), f"original load source size changed: {relative}")
    # The three direct current geometry chain values are fixed outside the report.
    expected_direct = {
        str(SURFACES_REL): SURFACES_SHA256,
        str(AXIS_FEATURES_REL): AXIS_FEATURES_SHA256,
        str(SURFACE_SOURCE_PINS_REL): SURFACE_SOURCE_PINS_SHA256,
        str(AXIS_SOURCE_PINS_REL): AXIS_SOURCE_PINS_SHA256,
        str(SURFACES_REL.parent / "surfaces.py"): SURFACES_PRODUCER_SHA256,
        str(AXIS_FEATURES_REL.parent / "axis_features.py"): AXIS_FEATURES_PRODUCER_SHA256,
        str(SURFACES_REL.parent / "test_surfaces.py"): SURFACES_TEST_SHA256,
    }
    report_pins = report["source_pins"]
    for relative, expected in expected_direct.items():
        entry = report_pins.get(relative)
        require(isinstance(entry, dict) and entry.get("sha256") == expected,
                f"finished-ray manifest dropped or changed required geometry source {relative}")
    return {"surfaces": surfaces, "axis_features": axis_data,
            "source_manifest": manifest, "source_manifest_raw": manifest_raw,
            "surface_source_pins": surface_pins, "surface_source_pins_raw": surface_pin_raw,
            "axis_source_pins": axis_pins, "axis_source_pins_raw": axis_pin_raw,
            "surfaces_raw": surfaces_raw, "axis_features_raw": axis_raw}


def _validate_frozen_inputs(report_path: Path, expected_report_sha: str,
                            load_path: Path, raw_path: Path,
                            resistance_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    report_raw = read_bytes(report_path)
    report_sha = sha_bytes(report_raw)
    require(report_sha == expected_report_sha,
            f"finished-ray report hash mismatch: {report_sha} != {expected_report_sha}")
    try:
        report = json.loads(report_raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OracleError(f"invalid finished-ray report: {error}") from error
    require(isinstance(report, dict), "finished-ray report must be an object")
    load, load_raw = read_json(load_path)
    raw, raw_raw = read_json(raw_path)
    resistance, resistance_raw = read_json(resistance_path)
    require(sha_bytes(load_raw) == LOAD_SHA256, "upstream load report hash changed")
    require(sha_bytes(raw_raw) == LOAD_RAW_SHA256, "accepted upstream raw receipt hash changed")
    require(sha_bytes(resistance_raw) == RESISTANCE_SHA256,
            "accepted conditional resistance report hash changed")
    require(report.get("schema") == EXPECTED_SCHEMA
            and report.get("status") == "nominal_source_bound_geometry_with_explicit_applicability_gaps",
            "finished-ray report schema/status changed")
    require(report.get("candidate") == CANDIDATE and report.get("geometry_revision_id") == REVISION,
            "finished-ray report candidate/revision changed")
    _check_report_pins(report, load, raw, resistance)
    require(load.get("candidate") == CANDIDATE and load.get("geometry_revision_id") == REVISION
            and load.get("status") == "PASS_CURRENT_RETAINED_FORCE_AND_BODY_JOIN_ONLY",
            "upstream load report authority changed")
    require(set(load.get("axis_register", {})) == set(AXES)
            and set(load.get("receiver_bodies", [])) == RECEIVERS,
            "upstream retained-axis/receiver census changed")
    require(load.get("counts", {}).get("retained_axes") == 12
            and load.get("counts", {}).get("receiver_memberships") == 24
            and load.get("counts", {}).get("states") == 21
            and load.get("counts", {}).get("combined_receiver_wrenches") == 504,
            "upstream retained load census changed")
    _check_report_release_boundary(report)
    require(all(report.get(flag) is False for flag in (
        "native_solve_executed", "qualified_for_design", "mechanical_acceptance",
        "joint_demand_accepted", "floor_capacity_established", "friction_qualified",
        "joint_accepted", "fabrication_release", "CAD_executed",
        "geometry_regenerated_or_changed", "engineering_mvp_complete")),
        "finished-ray acceptance/release flag is true or missing")
    receipt_sources = {
        "load_report": {"sha256": sha_bytes(load_raw), "path": str(load_path)},
        "accepted_raw_receipt": {"sha256": sha_bytes(raw_raw), "path": str(raw_path)},
        "resistance_report": {"sha256": sha_bytes(resistance_raw), "path": str(resistance_path)},
        "finished_ray_report": {"sha256": report_sha, "path": str(report_path)},
    }
    return report, load, {"report_sha256": report_sha, "report_raw": report_raw,
                          "source_reports": receipt_sources,
                          "load": load, "raw": raw, "resistance": resistance}


def _check_report_pins(report: dict[str, Any], load: dict[str, Any],
                       raw: dict[str, Any], resistance: dict[str, Any]) -> None:
    require(report.get("load_report_sha256") == LOAD_SHA256
            and report.get("accepted_raw_receipt_sha256") == LOAD_RAW_SHA256
            and report.get("resistance_report_sha256") == RESISTANCE_SHA256,
            "finished-ray upstream report pins changed")
    require(raw.get("report_sha256") == LOAD_SHA256
            and resistance.get("load_report_sha256") == LOAD_SHA256,
            "upstream receipts do not bind the accepted load report")
    require(load.get("input_pins") is not None,
            "upstream load report omits the authenticated input pins")


def _check_report_release_boundary(report: dict[str, Any]) -> None:
    for flag in FALSE_FLAGS:
        require(report.get(flag) is False, f"finished-ray report flag {flag} is not false")
    require(report.get("criteria_pending_count") == 47
            and report.get("criteria_status") == "all_47_pending_unchanged"
            and report.get("engineering_mvp_complete") is False,
            "finished-ray report promoted an open criterion or release")
    require(isinstance(report.get("release_flags"), dict)
            and all(value is False for value in report["release_flags"].values()),
            "finished-ray report release flags are not all false")


def _frame(receiver: dict[str, Any]) -> tuple[list[list[float]], list[float], list[float]]:
    frame = receiver.get("stock_frame")
    require(isinstance(frame, dict), "receiver stock frame missing")
    basis = frame.get("basis_columns_global_xyz")
    require(isinstance(basis, list) and len(basis) == 3, "receiver basis missing")
    basis = [unit(vec(axis, "stock basis"), "stock basis") for axis in basis]
    require(all(abs(dot(basis[i], basis[j])) <= 1e-9 for i in range(3) for j in range(i)),
            "receiver stock frame has mixed axes")
    handedness = dot(cross(basis[0], basis[1]), basis[2])
    require(abs(handedness - 1.0) <= 1e-8, "receiver frame is not right-handed")
    origin = vec(frame.get("origin_global_xyz_mm"), "stock origin")
    dims = frame.get("original_dimensions_gqr_mm")
    require(isinstance(dims, list) and len(dims) == 3
            and all(finite(x, "stock dimension") > 0 for x in dims), "stock dimensions malformed")
    return basis, origin, [float(x) for x in dims]


def _axis_receiver_report(load: dict[str, Any], surfaces: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    member_by_id = {record["member_id"]: _parse_member(record) for record in surfaces["records"]}
    require(len(member_by_id) == 44, "surface register member count changed")
    memberships: dict[str, Any] = {}
    query_results: dict[str, Any] = {}
    receiver_face_count = {member: {"PLANE": 0, "CYLINDER": 0} for member in RECEIVERS}
    for member in RECEIVERS:
        require(member in member_by_id, f"missing receiver face signatures: {member}")
        for face in member_by_id[member]["features"]:
            receiver_face_count[member][face["kind"]] += 1
    require(sum(row["PLANE"] for row in receiver_face_count.values()) == 74
            and sum(row["CYLINDER"] for row in receiver_face_count.values()) == 68,
            "receiver plane/full-turn cylinder census changed")
    for axis_id in AXES:
        axis = load["axis_register"][axis_id]
        source = axis["source_axis_fields"]
        axis_origin = vec(source["datum_global_xyz_mm"], f"{axis_id}.axis datum")
        axis_direction = unit(vec(source["direction_global_xyz"], f"{axis_id}.axis direction"), axis_id)
        receivers = axis.get("receivers_head_to_nut")
        require(isinstance(receivers, list) and len(receivers) == 2,
                f"{axis_id}: receiver pair malformed")
        require([receiver.get("member") for receiver in receivers] == [axis.get("first"), axis.get("second")],
                f"{axis_id}: head/nut receiver order changed")
        require(axis.get("first") in RECEIVERS and axis.get("second") in RECEIVERS,
                f"{axis_id}: foreign receiver")
        for side, receiver in zip(("first", "second"), receivers, strict=True):
            member_id = receiver["member"]
            member = member_by_id[member_id]
            require(member["record"].get("step_binding") == receiver.get("finished_step")
                    and member["record"].get("stock_frame") == receiver.get("stock_frame"),
                    f"{axis_id}/{side}: step or stock-frame binding is foreign/mixed")
            own_id = receiver.get("feature_id")
            own = member["by_id"].get(own_id)
            require(own is not None and own["kind"] == "CYLINDER"
                    and own["material_side"] == "bore_like",
                    f"{axis_id}/{side}: mapped own cylinder changed")
            basis, box_origin, dims = _frame(receiver)
            require(abs(dot(axis_direction, basis[0])) <= 1e-9
                    and abs(dot(axis_direction, basis[1])) <= 1e-9
                    and abs(abs(dot(axis_direction, basis[2])) - 1.0) <= 1e-9,
                    f"{axis_id}/{side}: mixed grain/q/bolt frame")
            lo, hi = receiver.get("interval_from_axis_datum_mm", (None, None))
            lo, hi = finite(lo, f"{axis_id}/{side}.interval.lo"), finite(hi, f"{axis_id}/{side}.interval.hi")
            require(0 <= lo < hi <= finite(source.get("axis_length_mm"), axis_id)
                    and hi - lo > 0.02, f"{axis_id}/{side}: invalid finite bearing span")
            # Compare both independently described finite cylinder endpoints to
            # the receiver's source-axis interval; this prevents a foreign/moved bore.
            bore_points = [add(own["axis_origin"], scale(t, own["axis"])) for t in own["interval"]]
            interval_points = [add(axis_origin, scale(t, axis_direction)) for t in (lo, hi)]
            same_order = close_vec(bore_points[0], interval_points[0], 2e-5) and close_vec(
                bore_points[1], interval_points[1], 2e-5)
            reverse_order = close_vec(bore_points[0], interval_points[1], 2e-5) and close_vec(
                bore_points[1], interval_points[0], 2e-5)
            require(same_order or reverse_order,
                    f"{axis_id}/{side}: mapped bore finite envelope differs from axis membership")
            # Axis and face directions must be collinear even when the patch uses
            # its own reversed parameter direction.
            axis_delta = sub(own["axis_origin"], axis_origin)
            line_gap = norm(sub(axis_delta, scale(dot(axis_delta, axis_direction), axis_direction)))
            require(line_gap <= 2e-5 and abs(abs(dot(own["axis"], axis_direction)) - 1.0) <= 1e-9,
                    f"{axis_id}/{side}: bore centerline does not match bolt axis")
            frame = receiver["stock_frame"]
            station_map = {"near_head": lo + 0.01, "midpoint": (lo + hi) / 2.0,
                           "near_nut": hi - 0.01}
            membership_id = f"{axis_id}/{side}"
            physical_point = vec(axis.get("lateral_interface_point_xyz_mm"),
                                 f"{axis_id}.physical interface point")
            membership = {"axis_id": axis_id, "receiver_side": side, "member": member_id,
                          "feature_id": own_id, "finished_step": receiver["finished_step"],
                          "stock_frame": frame,
                          "interval_from_axis_datum_mm": [lo, hi],
                          "query_stations_from_axis_datum_mm": station_map,
                          "physical_lateral_interface_point_xyz_mm": physical_point,
                          "query_point_role": "interior bore-centerline sample, not the physical force application point",
                          "through_depth_minimum_mm": None,
                          "queries_by_sample": {}}
            for sample, station in station_map.items():
                query_origin = add(axis_origin, scale(station, axis_direction))
                box_local = [dot(sub(query_origin, box_origin), basis[i]) for i in range(3)]
                require(all(-1e-5 <= box_local[i] <= dims[i] + 1e-5 for i in range(3)),
                        f"{membership_id}/{sample}: stock locator changed")
                require(norm(sub(query_origin, physical_point)) > 0.009,
                        f"{membership_id}/{sample}: geometric origin collapsed onto force interface point")
                refs = {}
                for dim, axis_name in ((0, "g"), (1, "q")):
                    for sign, sign_name in ((1.0, "+"), (-1.0, "-")):
                        direction_name = axis_name + sign_name
                        ray_direction = scale(sign, basis[dim])
                        ray = _ray(member, own_id, query_origin, ray_direction)
                        key = f"{membership_id}/{sample}/{direction_name}"
                        stock_distance = dims[dim] - box_local[dim] if sign > 0 else box_local[dim]
                        first_ext = ray["first_exterior_exit"]
                        grain_normal = None
                        if first_ext is not None and first_ext["surface_kind"] == "PLANE":
                            ext_feature = member["by_id"][first_ext["feature_id"]]
                            grain_normal = abs(dot(ext_feature["normal"], basis[0])) > 1.0 - 1e-9
                        query = {"query_id": key, "axis_id": axis_id, "receiver_side": side,
                                 "sample": sample, "station_from_axis_datum_mm": station,
                                 "depth_from_receiver_head_mm": station - lo,
                                 "modeled_bearing_length_mm": hi - lo,
                                 "direction_name": direction_name,
                                 "stock_box_distance_mm": stock_distance,
                                 "stock_box_role": "separate proposed envelope locator, never a finished-boundary fallback",
                                 "finished_geometry": ray,
                                 "grain_normal_planar_boundary": grain_normal,
                                 "NDS_square_cut_end_applicability": None,
                                 "through_depth_minimum_mm": None}
                        query_results[key] = query
                        refs[direction_name] = key
                membership["queries_by_sample"][sample] = refs
            memberships[membership_id] = membership
    require(len(memberships) == 24 and len(query_results) == 288,
            "independent receiver/query census changed")
    return memberships, query_results


def _project(force: list[float], radius: list[float], axis: list[float],
             label: str) -> dict[str, Any]:
    component = dot(force, axis)
    uncertainty = dot(radius, [abs(value) for value in axis])
    low, high = component - uncertainty, component + uncertainty
    sign = 1 if low > 0.0 else -1 if high < 0.0 else None
    return {"signed_component_n": component, "rounding_radius_n": uncertainty,
            "interval_n": [low, high], "sign": sign,
            "direction_name": label + ("+" if sign == 1 else "-") if sign is not None else None,
            "selection_status": "resolved" if sign is not None else "sign_interval_contains_zero"}


def _receiver_rows(load: dict[str, Any], memberships: dict[str, Any],
                   query_results: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    seen = set()
    for state in load.get("states", []):
        case_id = state.get("case_id")
        increment = state.get("increment_index")
        require(case_id in CASE_ORDER and isinstance(increment, int) and 0 <= increment < 7,
                "foreign retained state")
        key_state = (case_id, increment)
        require(key_state not in seen, "duplicate retained state")
        seen.add(key_state)
        require(close(finite(state.get("load_factor"), "load factor"), FACTORS[increment], 1e-14),
                "retained state factor changed")
        bolt_states = state.get("bolt_states")
        require(isinstance(bolt_states, dict) and set(bolt_states) == set(AXES),
                "retained bolt state ids changed")
        for axis_id in AXES:
            bolt = bolt_states[axis_id]
            action = bolt.get("lateral_interface_action")
            require(isinstance(action, dict) and action.get("role") == "retained_bolt_lateral_plane"
                    and action.get("axis_id") == axis_id,
                    f"{axis_id}: physical lateral connector role changed")
            force_first = vec(action.get("force_on_first_xyz_n"), f"{axis_id}.force.first")
            force_second = vec(action.get("force_on_second_xyz_n"), f"{axis_id}.force.second")
            radius = vec(action.get("force_rounding_radius_xyz_n"), f"{axis_id}.force.radius")
            require(all(component >= 0.0 for component in radius)
                    and all(abs(a + b) <= 1e-12 for a, b in zip(force_first, force_second, strict=True)),
                    f"{axis_id}: force pair or rounding radius changed")
            force_point = vec(action.get("point"), f"{axis_id}.physical point")
            source_rows = action.get("source_row_ids")
            require(isinstance(source_rows, list) and len(source_rows) == 2,
                    f"{axis_id}: lateral source-channel binding changed")
            for side, member, force in (("first", action.get("first"), force_first),
                                         ("second", action.get("second"), force_second)):
                membership_id = f"{axis_id}/{side}"
                membership = memberships[membership_id]
                require(member == membership["member"]
                        and close_vec(force_point, membership["physical_lateral_interface_point_xyz_mm"], 1e-12),
                        f"{membership_id}: physical action moved or receiver mixed")
                basis = membership["stock_frame"]["basis_columns_global_xyz"]
                candidates = {}
                for dim, label in ((0, "g"), (1, "q")):
                    selection = _project(force, radius, basis[dim], label)
                    sample_result = {}
                    for sample, refs in membership["queries_by_sample"].items():
                        query_id = refs.get(selection["direction_name"]) if selection["direction_name"] else None
                        query = query_results[query_id] if query_id else None
                        geometry = query["finished_geometry"] if query else None
                        material_exit = geometry.get("first_material_exit") if geometry else None
                        exterior_exit = geometry.get("first_exterior_exit") if geometry else None
                        sample_result[sample] = {
                            "query_id": query_id,
                            "finished_exterior_distance_mm": geometry.get("distance_mm") if geometry else None,
                            "first_material_exit_distance_mm": material_exit.get("distance_mm")
                            if material_exit else None,
                        }
                        if query is not None:
                            require(query["finished_geometry"]["direction_global_unit"] == scale(
                                1.0 if selection["direction_name"][-1] == "+" else -1.0,
                                basis[dim]), "loaded direction selected from mixed stock frame")
                        if exterior_exit is not None:
                            require(geometry["distance_mm"] == exterior_exit["distance_mm"],
                                    "finished distance did not preserve exterior polygon-plane exit")
                    candidates[label] = {**selection, "samples": sample_result}
                rows.append({"case_id": case_id, "increment_index": increment,
                             "load_factor": float(state["load_factor"]), "axis_id": axis_id,
                             "membership_id": membership_id, "receiver_side": side,
                             "receiver_member_id": membership["member"],
                             "physical_lateral_interface_point_xyz_mm": force_point,
                             "force_on_receiver_xyz_n": force,
                             "force_rounding_radius_xyz_n": radius,
                             "source_row_ids": source_rows,
                             "loaded_direction_geometric_candidates": candidates,
                             "direction_basis": "separate signed modeled grain and stock-q components; not total-resultant ray",
                             "NDS_loaded_end_edge_classification": None, "Cdelta": None,
                             "Cg": None, "splitting_acceptance": None,
                             "through_depth_minimum_mm": None, "joint_accepted": False})
    require(len(seen) == 21 and len(rows) == 504, "independent force projection census changed")
    return rows


def _validate_criteria() -> dict[str, Any]:
    criteria, raw = read_json(ROOT / CRITERIA_REL)
    legacy = criteria.get("legacy_criteria")
    additions = criteria.get("additional_candidate_obligations")
    require(isinstance(legacy, list) and isinstance(additions, list)
            and len(legacy) + len(additions) == 47,
            "current criterion count differs from 47")
    require(all(item.get("status") == "pending" for item in legacy + additions)
            and criteria.get("engineering_mvp_complete") is False
            and isinstance(criteria.get("release_flags"), dict)
            and all(value is False for value in criteria["release_flags"].values()),
            "an open criterion or release flag changed")
    return {"sha256": sha_bytes(raw), "count": 47, "all_pending": True,
            "engineering_mvp_complete": False,
            "release_flags": criteria["release_flags"]}


def _verify_report(report: dict[str, Any], load: dict[str, Any],
                   sources: dict[str, Any], report_sha: str) -> dict[str, Any]:
    surfaces = sources["surfaces"]
    memberships, queries = _axis_receiver_report(load, surfaces)
    expected_counts = {"retained_axes": 12, "receiver_memberships": 24,
                       "finished_members": 8, "query_depths_per_receiver": 3,
                       "directional_queries": 288, "signed_bolt_states": 252,
                       "signed_receiver_states": 504}
    require(report.get("counts", {}).items() >= expected_counts.items(),
            "finished-ray report counts changed")
    report_memberships = report.get("memberships")
    report_queries = report.get("queries")
    require(isinstance(report_memberships, dict) and isinstance(report_queries, dict)
            and set(report_memberships) == set(memberships)
            and set(report_queries) == set(queries),
            "finished-ray report has foreign/missing receiver memberships or query ids")
    compare(report_memberships, memberships, "memberships")
    for query_id, expected in queries.items():
        actual = report_queries[query_id]
        compare(actual, expected, f"queries[{query_id}]")
    expected_rows = _receiver_rows(load, memberships, queries)
    actual_rows = report.get("receiver_state_rows")
    require(isinstance(actual_rows, list) and len(actual_rows) == 504,
            "finished-ray report omitted one of the 504 receiver projections")
    report_rows = {}
    for row in actual_rows:
        key = (row.get("case_id"), row.get("increment_index"), row.get("axis_id"),
               row.get("receiver_side"))
        require(key not in report_rows, f"duplicate receiver-state row {key}")
        report_rows[key] = row
    require(len(report_rows) == 504, "receiver-state row uniqueness changed")
    for expected in expected_rows:
        key = (expected["case_id"], expected["increment_index"], expected["axis_id"],
               expected["receiver_side"])
        require(key in report_rows, f"missing receiver-state projection {key}")
        compare(report_rows[key], expected, f"receiver_state_rows[{key}]", numeric_tol=1e-8)
    for flag in FALSE_FLAGS:
        require(report.get(flag) is False, f"report {flag} must remain false")
    require(report.get("criteria_status") == "all_47_pending_unchanged"
            and report.get("engineering_mvp_complete") is False,
            "report changed criteria/release status")
    require(all(m["through_depth_minimum_mm"] is None for m in memberships.values())
            and all(row["through_depth_minimum_mm"] is None for row in expected_rows),
            "report adopted an unsampled through-depth minimum")
    require(all(row["NDS_loaded_end_edge_classification"] is None
                and row["Cdelta"] is None and row["Cg"] is None
                and row["splitting_acceptance"] is None and row["joint_accepted"] is False
                for row in expected_rows), "a detailing/resistance/acceptance field was promoted")
    return {"counts": expected_counts,
            "query_statuses": {status: sum(q["finished_geometry"]["status"] == status
                                             for q in queries.values())
                               for status in ("ok", "ambiguous", "unsupported")},
            "membership_count": len(memberships), "query_count": len(queries),
            "receiver_state_row_count": len(expected_rows),
            "projection_component_count": 1008,
            "geometry_method": "independent saved-signature ray/face intersections and planar wire parity",
            "criteria": _validate_criteria(),
            "report_sha256": report_sha}


def _must_reject(label: str, check: Any) -> dict[str, Any]:
    try:
        check()
    except OracleError:
        return {"mutation": label, "rejected": True}
    raise OracleError(f"mutation probe was accepted: {label}")


def _mutation_refusals(report: dict[str, Any], load: dict[str, Any],
                       sources: dict[str, Any], raw: dict[str, Any],
                       resistance: dict[str, Any]) -> list[dict[str, Any]]:
    expected_memberships, expected_queries = _axis_receiver_report(load, sources["surfaces"])
    probes = []

    foreign = copy.deepcopy(report)
    first_query = next(iter(expected_queries))
    foreign["queries"][first_query]["finished_geometry"]["events"][0]["feature_ids"][0] = (
        "foreign_member/facet999")
    probes.append(_must_reject(
        "foreign finished geometry feature",
        lambda: compare(foreign["queries"][first_query], expected_queries[first_query],
                        f"mutation.{first_query}")))

    reversed_normal = copy.deepcopy(report)
    reversed_normal["queries"][first_query]["finished_geometry"]["events"][0][
        "oriented_normal_dot"] *= -1.0
    probes.append(_must_reject(
        "reversed saved-face normal sign",
        lambda: compare(reversed_normal["queries"][first_query], expected_queries[first_query],
                        f"mutation.{first_query}")))

    distinct = next((key for key, query in expected_queries.items()
                     if query["finished_geometry"]["first_material_exit"] is not None
                     and query["finished_geometry"]["first_exterior_exit"] is not None
                     and query["finished_geometry"]["first_material_exit"]["feature_id"]
                     != query["finished_geometry"]["first_exterior_exit"]["feature_id"]), None)
    require(distinct is not None, "no other-bore/exterior pair exists for first-boundary mutation")
    wrong_first = copy.deepcopy(report)
    profile = wrong_first["queries"][distinct]["finished_geometry"]
    profile["first_material_exit"] = copy.deepcopy(profile["first_exterior_exit"])
    probes.append(_must_reject(
        "first material exit replaced by later exterior plane",
        lambda: compare(wrong_first["queries"][distinct], expected_queries[distinct],
                        f"mutation.{distinct}")))

    mixed_stock = copy.deepcopy(report)
    membership_id = next(iter(expected_memberships))
    mixed_stock["memberships"][membership_id]["stock_frame"][
        "basis_columns_global_xyz"][0][0] += 0.25
    probes.append(_must_reject(
        "mixed receiver stock frame",
        lambda: compare(mixed_stock["memberships"][membership_id],
                        expected_memberships[membership_id], f"mutation.{membership_id}")))

    changed_pin = copy.deepcopy(report)
    changed_pin["load_report_sha256"] = "0" * 64
    probes.append(_must_reject(
        "foreign report pin",
        lambda: _check_report_pins(changed_pin, load, raw, resistance)))

    promoted = copy.deepcopy(report)
    promoted["fabrication_release"] = True
    probes.append(_must_reject(
        "fabrication release promotion",
        lambda: _check_report_release_boundary(promoted)))
    return probes


def require_reviewed_oracle_sha256(expected: str | None) -> None:
    """Bind execution to the caller's externally recorded reviewed code pin."""
    require(isinstance(expected, str) and len(expected) == 64
            and all(char in "0123456789abcdef" for char in expected),
            "--expected-oracle-sha256 requires the reviewed lowercase SHA-256 digest")
    require(expected == sha_bytes(read_bytes(Path(__file__))),
            "current oracle differs from the externally supplied reviewed digest")


def verify_report(report_path: Path, expected_report_sha256: str, load_path: Path,
                  raw_path: Path, resistance_path: Path, expected_oracle_sha256: str) -> dict[str, Any]:
    require_reviewed_oracle_sha256(expected_oracle_sha256)
    require(len(expected_report_sha256) == 64 and all(c in "0123456789abcdef" for c in expected_report_sha256),
            "--expected-report-sha256 must be a lowercase SHA-256 hex digest")
    require(expected_report_sha256 == APPROVED_REPORT_SHA256,
            f"expected report SHA is not parent-approved: {expected_report_sha256}")
    report, load, frozen = _validate_frozen_inputs(report_path, expected_report_sha256,
                                                    load_path, raw_path, resistance_path)
    sources = _validate_source_chains(report, load)
    verification = _verify_report(report, load, sources, frozen["report_sha256"])
    verification["mutation_refusal_checks"] = _mutation_refusals(
        report, load, sources, frozen["raw"], frozen["resistance"])
    verification["mutation_refusal_count"] = len(verification["mutation_refusal_checks"])
    source_pins = {relative: dict(pin) for relative, pin in sorted(report["source_pins"].items())}
    load_pins = {relative: dict(pin) for relative, pin in sorted(load["input_pins"].items())}
    return {"schema": "retained_frame_bolt_finished_edges_raw_oracle_receipt/v1",
            "status": "PASS_INDEPENDENT_NUMERICAL_REPLAY_WITH_ACCEPTANCE_GAPS_RETAINED",
            "report_sha256": frozen["report_sha256"],
            "expected_report_sha256": expected_report_sha256,
            "accepted_upstream_report_hashes": {
                "load_report_sha256": LOAD_SHA256,
                "accepted_raw_receipt_sha256": LOAD_RAW_SHA256,
                "resistance_report_sha256": RESISTANCE_SHA256,
                "surfaces_sha256": SURFACES_SHA256,
                "axis_features_sha256": AXIS_FEATURES_SHA256,
            },
            "source_manifest_sha256": sha_bytes(sources["source_manifest_raw"]),
            "source_pins": source_pins,
            "rechecked_load_input_pins_143": load_pins,
            "source_report_paths": frozen["source_reports"],
            "verification": verification,
            "acceptance_boundary": {
                "criteria_status": "all_47_pending_unchanged",
                "joint_accepted": False,
                "fabrication_release": False,
                "through_depth_minimum_mm": None,
                "NDS_classification": None,
                "Cdelta": None,
                "Cg": None,
                "splitting_acceptance": None,
            },
            "oracle_sha256": sha_bytes(read_bytes(Path(__file__))),
            "receipt_sha256": None}


def _seal_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(receipt)
    sealed["receipt_sha256"] = None
    sealed["receipt_sha256"] = canonical_sha(sealed)
    return sealed


def verify_receipt(path: Path, expected_oracle_sha256: str) -> dict[str, Any]:
    require_reviewed_oracle_sha256(expected_oracle_sha256)
    receipt, raw = read_json(path)
    require(isinstance(receipt, dict) and receipt.get("schema") ==
            "retained_frame_bolt_finished_edges_raw_oracle_receipt/v1",
            "not a finished-edge raw-oracle receipt")
    claimed = receipt.get("receipt_sha256")
    copy = dict(receipt)
    copy["receipt_sha256"] = None
    actual = canonical_sha(copy)
    require(claimed == actual, f"receipt self-hash mismatch: {claimed!r} != {actual}")
    require(receipt.get("oracle_sha256") == sha_bytes(read_bytes(Path(__file__))),
            "receipt was produced by different oracle bytes")
    require(receipt.get("status") == "PASS_INDEPENDENT_NUMERICAL_REPLAY_WITH_ACCEPTANCE_GAPS_RETAINED",
            "receipt status is not a passing replay")
    return {"path": str(path), "receipt_file_sha256": sha_bytes(raw),
            "receipt_sha256": claimed, "report_sha256": receipt.get("report_sha256"),
            "status": receipt["status"]}


def _protected_paths(report: dict[str, Any], report_path: Path, load_path: Path,
                     raw_path: Path, resistance_path: Path) -> set[Path]:
    paths = {resolved(report_path), resolved(load_path), resolved(raw_path), resolved(resistance_path),
             resolved(Path(__file__)), resolved(HERE / "produce.py"), resolved(HERE / "method.py"),
             resolved(HERE / "source-pins.json"), resolved(ROOT / SURFACES_REL),
             resolved(ROOT / AXIS_FEATURES_REL), resolved(ROOT / SURFACE_SOURCE_PINS_REL),
             resolved(ROOT / AXIS_SOURCE_PINS_REL), resolved(ROOT / CRITERIA_REL)}
    paths.update(resolved(path) for path in HERE.rglob("*") if path.is_file())
    for table in (report.get("source_pins", {}), report.get("rechecked_load_input_pins", {})):
        if isinstance(table, dict):
            paths.update(resolved(ROOT / relative) for relative in table)
    return paths


def refuse_output_alias(output: Path, protected: Any) -> None:
    """Refuse path and inode aliases before creating or replacing a receipt."""
    output_path = Path(output)
    try:
        output_resolved = output_path.resolve()
    except (OSError, RuntimeError) as error:
        raise OracleError(f"cannot resolve output identity for {output_path}: {error}") from error
    try:
        output_path.stat()
        output_exists = True
    except FileNotFoundError:
        output_exists = False
    except OSError as error:
        raise OracleError(f"cannot inspect output identity for {output_path}: {error}") from error

    for item in protected:
        protected_path = Path(item)
        try:
            protected_resolved = protected_path.resolve()
        except (OSError, RuntimeError) as error:
            raise OracleError(
                f"cannot resolve protected input identity for {protected_path}: {error}"
            ) from error
        if output_resolved == protected_resolved:
            raise OracleError(
                "output aliases the report, an upstream input, or any authenticated source"
            )
        if not output_exists:
            continue
        try:
            protected_path.stat()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise OracleError(
                f"cannot inspect protected input identity for {protected_path}: {error}"
            ) from error
        try:
            aliases = output_path.samefile(protected_path)
        except OSError as error:
            raise OracleError(
                f"cannot verify output identity against {protected_path}: {error}"
            ) from error
        if aliases:
            raise OracleError(
                "output aliases the report, an upstream input, or any authenticated source"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path,
                        default=Path("/tmp/mini-moonboard-retained-frame-bolt-finished-edges-2026-10-01.json"))
    parser.add_argument("--expected-report-sha256", required=False,
                        help="parent-approved final byte hash; mandatory unless checking a receipt")
    parser.add_argument("--expected-oracle-sha256",
                        help="externally recorded reviewed oracle digest; mandatory for both modes")
    parser.add_argument("--load-report", type=Path, default=DEFAULT_LOAD_REPORT)
    parser.add_argument("--raw-receipt", type=Path, default=DEFAULT_RAW_RECEIPT)
    parser.add_argument("--resistance-report", type=Path, default=DEFAULT_RESISTANCE_REPORT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-receipt", type=Path,
                        help="verify a previously written receipt self-hash and oracle hash")
    args = parser.parse_args()
    try:
        require_reviewed_oracle_sha256(args.expected_oracle_sha256)
        if args.check_receipt:
            require(args.output is None and args.expected_report_sha256 is None,
                    "--check-receipt cannot be combined with report production options")
            print(json.dumps(verify_receipt(args.check_receipt, args.expected_oracle_sha256), sort_keys=True))
            return 0
        require(args.expected_report_sha256 is not None,
                "--expected-report-sha256 is required for parent-approved replay")
        require(args.output is not None, "--output is required")
        receipt = verify_report(args.report, args.expected_report_sha256, args.load_report,
                                args.raw_receipt, args.resistance_report, args.expected_oracle_sha256)
        report, _ = read_json(args.report)
        protected = _protected_paths(report, args.report, args.load_report,
                                     args.raw_receipt, args.resistance_report)
        refuse_output_alias(args.output, protected)
        sealed = _seal_receipt(receipt)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(sealed, sort_keys=True, indent=2, allow_nan=False) + "\n"
        args.output.write_text(encoded, encoding="utf-8")
        print(json.dumps({"output": str(args.output), "receipt_sha256": sealed["receipt_sha256"],
                          "report_sha256": sealed["report_sha256"],
                          "verification": sealed["verification"]}, sort_keys=True))
        return 0
    except (OracleError, OSError, TypeError, KeyError, IndexError, ValueError) as error:
        print(f"raw_oracle: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
