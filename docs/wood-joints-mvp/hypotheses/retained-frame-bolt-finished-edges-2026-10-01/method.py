"""Analytic rays against the authenticated finished-member surface register.

The module reads saved JSON only. It has no CAD imports and never uses a
bounding box in place of an analytic trimmed plane or cylinder.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

QUERY_SCHEMA = "retained_frame_bolt_finished_edge_query/v1"
SURFACE_REGISTER_SCHEMA = "wood_joint_current_finished_feature_register/v1"
SURFACE_REGISTER_SHA256 = "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb"
TARGET_MEMBERS = frozenset({
    "base_floor_left", "base_floor_right",
    "base_post_outer_left", "base_post_outer_right",
    "base_side_left", "base_side_right",
    "lumber_leg_left", "lumber_leg_right",
})
LINEAR_TOL_MM = 1.0e-5
COINCIDENT_TOL_MM = 1.0e-5
UNIT_TOL = 1.0e-6
ANGLE_TOL = 1.0e-8
PARAMETER_TOL = 1.0e-8
DOT_TOL = 1.0e-9
ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SURFACES = ROOT / "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/surfaces.json"


class _Refusal(ValueError):
    pass


Vec3 = tuple[float, float, float]
Vec2 = tuple[float, float]


@dataclass(frozen=True)
class _Loop:
    wire_index: int
    kind: str
    points: tuple[Vec2, ...] = ()
    center: Vec2 | None = None
    radius: float | None = None


@dataclass(frozen=True)
class _Plane:
    feature_id: str
    normal: Vec3
    station: float
    basis_u: Vec3
    basis_v: Vec3
    loops: tuple[_Loop, ...]
    outer_is_polygon: bool
    circle_loops: tuple[tuple[int, Vec3, Vec3, float], ...]


@dataclass(frozen=True)
class _Cylinder:
    feature_id: str
    origin: Vec3
    axis: Vec3
    radius: float
    low: float
    high: float
    radial_normal_sign: float
    material_side: str


@dataclass(frozen=True)
class _Member:
    member_id: str
    planes: tuple[_Plane, ...]
    cylinders: tuple[_Cylinder, ...]
    feature_ids: frozenset[str]


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise _Refusal(f"{label}: boolean is not a coordinate")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise _Refusal(f"{label}: expected a finite number") from error
    if not math.isfinite(result):
        raise _Refusal(f"{label}: expected a finite number")
    return result


def _vec3(value: Any, label: str) -> Vec3:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 3:
        raise _Refusal(f"{label}: expected three finite coordinates")
    return tuple(_finite(v, label) for v in value)  # type: ignore[return-value]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _sub(a: Sequence[float], b: Sequence[float]) -> Vec3:
    return tuple(x - y for x, y in zip(a, b, strict=True))  # type: ignore[return-value]


def _add_scaled(a: Sequence[float], b: Sequence[float], scale: float) -> Vec3:
    return tuple(x + scale * y for x, y in zip(a, b, strict=True))  # type: ignore[return-value]


def _cross(a: Sequence[float], b: Sequence[float]) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a: Sequence[float]) -> float:
    return math.sqrt(_dot(a, a))


def _unit(value: Any, label: str) -> Vec3:
    vector = _vec3(value, label)
    length = _norm(vector)
    if length <= 1.0e-14 or abs(length - 1.0) > UNIT_TOL:
        raise _Refusal(f"{label}: expected an already unit vector")
    return tuple(v / length for v in vector)  # type: ignore[return-value]


def _close(a: float, b: float, tol: float = LINEAR_TOL_MM) -> bool:
    return abs(a - b) <= tol


def _points_close(a: Sequence[float], b: Sequence[float], tol: float = LINEAR_TOL_MM) -> bool:
    return _norm(_sub(a, b)) <= tol


def load_authenticated_surface_records(path: str | Path = DEFAULT_SURFACES) -> dict[str, Mapping[str, Any]]:
    """Load the exact saved surface JSON after checking its frozen byte hash."""
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SURFACE_REGISTER_SHA256:
        raise ValueError(f"saved surface-register bytes are not authenticated: {digest}")
    document = json.loads(raw)
    if document.get("schema") != SURFACE_REGISTER_SCHEMA:
        raise ValueError("saved surface-register schema is unsupported")
    if document.get("record_count") != 44 or document.get("finished_face_count") != 648:
        raise ValueError("saved surface-register counts differ from the frozen artifact")
    records = document.get("records")
    if not isinstance(records, list):
        raise TypeError("saved surface-register records must be a list")
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping) or not isinstance(record.get("member_id"), str):
            raise TypeError("saved surface-register contains a malformed member")
        member_id = record["member_id"]
        if member_id in result:
            raise ValueError(f"saved surface-register repeats {member_id}")
        result[member_id] = record
    if not TARGET_MEMBERS.issubset(result):
        raise ValueError("saved surface-register lacks one or more target members")
    return result


def _plane_basis(normal: Vec3) -> tuple[Vec3, Vec3]:
    helper: Vec3 = (1.0, 0.0, 0.0) if abs(normal[0]) < 0.8 else (0.0, 1.0, 0.0)
    raw = _cross(helper, normal)
    length = _norm(raw)
    u = tuple(v / length for v in raw)  # type: ignore[assignment]
    return u, _cross(normal, u)


def _project(point: Vec3, origin: Vec3, u: Vec3, v: Vec3) -> Vec2:
    relative = _sub(point, origin)
    return (_dot(relative, u), _dot(relative, v))


def _line_edge_points(edge: Mapping[str, Any], context: str) -> tuple[Vec3, Vec3]:
    line = edge.get("line")
    if not isinstance(line, Mapping):
        raise _Refusal(f"{context}: LINE edge has no line parameters")
    origin = _vec3(line.get("origin_global_xyz_mm"), f"{context} line origin")
    direction = _unit(line.get("direction_global_xyz"), f"{context} line direction")
    params = edge.get("parameter_bounds")
    endpoints = edge.get("parameter_endpoint_global_xyz_mm")
    vertices = edge.get("topological_vertices_global_xyz_mm")
    if not isinstance(params, Sequence) or len(params) != 2:
        raise _Refusal(f"{context}: LINE parameter bounds are missing")
    if not isinstance(endpoints, Sequence) or len(endpoints) != 2:
        raise _Refusal(f"{context}: LINE endpoints are missing")
    if not isinstance(vertices, Sequence) or len(vertices) != 2:
        raise _Refusal(f"{context}: LINE must have two topological vertices")
    a, b = (_finite(v, f"{context} parameter") for v in params)
    p0, p1 = _vec3(endpoints[0], context), _vec3(endpoints[1], context)
    v0, v1 = _vec3(vertices[0], context), _vec3(vertices[1], context)
    if not _points_close(p0, _add_scaled(origin, direction, a)) or not _points_close(p1, _add_scaled(origin, direction, b)):
        raise _Refusal(f"{context}: LINE endpoints disagree with saved parameters")
    length = _finite(edge.get("length_mm"), f"{context} length")
    if not _close(length, abs(b - a)) or not _close(length, _norm(_sub(p1, p0))) or length <= LINEAR_TOL_MM:
        raise _Refusal(f"{context}: LINE length disagrees with endpoints")
    if not ((_points_close(p0, v0) and _points_close(p1, v1)) or (_points_close(p0, v1) and _points_close(p1, v0))):
        raise _Refusal(f"{context}: LINE topological vertices disagree with endpoints")
    return p0, p1


def _circle_edge(edge: Mapping[str, Any], context: str) -> tuple[Vec3, Vec3, float]:
    circle = edge.get("circle")
    if not isinstance(circle, Mapping):
        raise _Refusal(f"{context}: CIRCLE edge has no circle parameters")
    center = _vec3(circle.get("center_global_xyz_mm"), f"{context} center")
    axis = _unit(circle.get("axis_unit_global_xyz"), f"{context} circle axis")
    radius = _finite(circle.get("radius_mm"), f"{context} radius")
    params = edge.get("parameter_bounds")
    endpoints = edge.get("parameter_endpoint_global_xyz_mm")
    vertices = edge.get("topological_vertices_global_xyz_mm")
    if radius <= 0.0 or not isinstance(params, Sequence) or len(params) != 2:
        raise _Refusal(f"{context}: invalid radius or missing parameters")
    if not isinstance(endpoints, Sequence) or len(endpoints) != 2 or not isinstance(vertices, Sequence) or len(vertices) != 1:
        raise _Refusal(f"{context}: full CIRCLE must have two endpoints and one vertex")
    a, b = (_finite(v, f"{context} parameter") for v in params)
    if abs(abs(b - a) - 2.0 * math.pi) > PARAMETER_TOL:
        raise _Refusal(f"{context}: partial circular trim is unsupported")
    points = [_vec3(v, f"{context} endpoint") for v in endpoints]
    vertex = _vec3(vertices[0], f"{context} vertex")
    for point in (*points, vertex):
        delta = _sub(point, center)
        station = _dot(delta, axis)
        radial = _sub(delta, tuple(station * x for x in axis))
        if abs(station) > LINEAR_TOL_MM or not _close(_norm(radial), radius):
            raise _Refusal(f"{context}: endpoint/vertex disagrees with circle")
    if not _points_close(points[0], points[1]) or not _points_close(points[0], vertex):
        raise _Refusal(f"{context}: full CIRCLE does not close")
    if not _close(_finite(edge.get("length_mm"), f"{context} length"), 2.0 * math.pi * radius):
        raise _Refusal(f"{context}: CIRCLE length disagrees with radius")
    return center, axis, radius


def _node_index(nodes: list[Vec3], point: Vec3) -> int:
    for index, node in enumerate(nodes):
        if _points_close(node, point):
            return index
    nodes.append(point)
    return len(nodes) - 1


def _check_simple_polygon(points: Sequence[Vec2], context: str) -> None:
    n = len(points)
    twice_area = sum(points[i][0] * points[(i + 1) % n][1] - points[(i + 1) % n][0] * points[i][1] for i in range(n))
    if abs(twice_area) <= LINEAR_TOL_MM * LINEAR_TOL_MM:
        raise _Refusal(f"{context}: polygon has negligible area")

    def orient(a: Vec2, b: Vec2, c: Vec2) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_segment(a: Vec2, b: Vec2, p: Vec2) -> bool:
        return (
            min(a[0], b[0]) - LINEAR_TOL_MM <= p[0] <= max(a[0], b[0]) + LINEAR_TOL_MM
            and min(a[1], b[1]) - LINEAR_TOL_MM <= p[1] <= max(a[1], b[1]) + LINEAR_TOL_MM
            and abs(orient(a, b, p)) <= LINEAR_TOL_MM * max(1.0, math.dist(a, b))
        )

    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        for j in range(i + 1, n):
            if j == i or j == (i + 1) % n or (j + 1) % n == i:
                continue
            c, d = points[j], points[(j + 1) % n]
            o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
            if ((o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)) or on_segment(a, b, c) or on_segment(a, b, d) or on_segment(c, d, a) or on_segment(c, d, b):
                raise _Refusal(f"{context}: polygon self-intersects or self-touches")


def _compile_polygon(edges: Sequence[Mapping[str, Any]], u: Vec3, v: Vec3, context: str) -> tuple[Vec2, ...]:
    if len(edges) < 3:
        raise _Refusal(f"{context}: polygon requires at least three LINE edges")
    nodes: list[Vec3] = []
    pairs: list[tuple[int, int]] = []
    for index, edge in enumerate(edges, start=1):
        if edge.get("curve_kind") != "LINE":
            raise _Refusal(f"{context}: only straight polygon wires are supported")
        a, b = _line_edge_points(edge, f"{context} edge {index}")
        ia, ib = _node_index(nodes, a), _node_index(nodes, b)
        if ia == ib:
            raise _Refusal(f"{context}: collapsed polygon edge")
        pairs.append((ia, ib))
    adjacency: dict[int, list[int]] = {i: [] for i in range(len(nodes))}
    for a, b in pairs:
        adjacency[a].append(b)
        adjacency[b].append(a)
    if len(nodes) != len(edges) or any(len(neighbors) != 2 for neighbors in adjacency.values()):
        raise _Refusal(f"{context}: unordered lines do not form one closed polygon")
    start = min(range(len(nodes)), key=lambda i: nodes[i])
    cycle, previous, current = [start], -1, start
    for _ in range(len(edges)):
        next_nodes = sorted(i for i in adjacency[current] if i != previous)
        if not next_nodes:
            raise _Refusal(f"{context}: open polygon chain")
        following = next_nodes[0]
        if following == start and len(cycle) == len(edges):
            break
        if following in cycle:
            raise _Refusal(f"{context}: polygon chain repeats a vertex")
        cycle.append(following)
        previous, current = current, following
    if len(cycle) != len(edges) or start not in adjacency[cycle[-1]]:
        raise _Refusal(f"{context}: unordered lines do not close")
    points = tuple((_dot(nodes[i], u), _dot(nodes[i], v)) for i in cycle)
    _check_simple_polygon(points, context)
    return points


def _point_in_polygon(point: Vec2, polygon: Sequence[Vec2]) -> str:
    x, y = point
    inside = False
    for i, a in enumerate(polygon):
        b = polygon[(i + 1) % len(polygon)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        cross = dx * (y - a[1]) - dy * (x - a[0])
        if abs(cross) <= LINEAR_TOL_MM * max(1.0, length) and min(a[0], b[0]) - LINEAR_TOL_MM <= x <= max(a[0], b[0]) + LINEAR_TOL_MM and min(a[1], b[1]) - LINEAR_TOL_MM <= y <= max(a[1], b[1]) + LINEAR_TOL_MM:
            return "ON"
        if (a[1] > y) != (b[1] > y):
            xcross = a[0] + (y - a[1]) * dx / dy
            if x < xcross:
                inside = not inside
    return "IN" if inside else "OUT"


def _compile_plane(feature: Mapping[str, Any]) -> _Plane:
    feature_id = feature.get("feature_id")
    plane, trim = feature.get("plane"), feature.get("trim")
    if not isinstance(feature_id, str) or not isinstance(plane, Mapping) or not isinstance(trim, Mapping):
        raise _Refusal("plane feature lacks its ID, plane, or trim record")
    normal = _unit(plane.get("normal_global_xyz"), f"{feature_id} outward plane normal")
    station = _finite(plane.get("signed_plane_station_global_mm"), f"{feature_id} station")
    if plane.get("coordinate_equation") != "normal · point = signed station":
        raise _Refusal(f"{feature_id}: unsupported plane equation")
    centroid = _vec3(feature.get("centroid_global_xyz_mm"), f"{feature_id} centroid")
    if abs(_dot(normal, centroid) - station) > LINEAR_TOL_MM:
        raise _Refusal(f"{feature_id}: centroid and plane station disagree")
    wires = trim.get("wires")
    if not isinstance(wires, list) or not wires:
        raise _Refusal(f"{feature_id}: planar face has no trim wires")
    rows = sorted(wires, key=lambda row: row.get("wire_index_one_based", 0))
    if [row.get("wire_index_one_based") for row in rows] != list(range(1, len(rows) + 1)):
        raise _Refusal(f"{feature_id}: plane wire indices are not contiguous")
    u, v = _plane_basis(normal)
    loops: list[_Loop] = []
    circles: list[tuple[int, Vec3, Vec3, float]] = []
    for row in rows:
        wi, edges = int(row["wire_index_one_based"]), row.get("edges")
        if not isinstance(edges, list) or not edges or len(edges) != row.get("edge_count"):
            raise _Refusal(f"{feature_id} wire {wi}: inconsistent edge count")
        if len(edges) == 1 and edges[0].get("curve_kind") == "CIRCLE":
            center, circle_axis, radius = _circle_edge(edges[0], f"{feature_id} wire {wi}")
            if abs(abs(_dot(circle_axis, normal)) - 1.0) > UNIT_TOL or abs(_dot(normal, center) - station) > LINEAR_TOL_MM:
                raise _Refusal(f"{feature_id} wire {wi}: circle is not in the saved plane")
            loops.append(_Loop(wi, "CIRCLE", center=(_dot(center, u), _dot(center, v)), radius=radius))
            circles.append((wi, center, circle_axis, radius))
        else:
            if any(edge.get("curve_kind") != "LINE" for edge in edges):
                raise _Refusal(f"{feature_id} wire {wi}: mixed curves or partial arcs are unsupported")
            for edge in edges:
                for point in _line_edge_points(edge, f"{feature_id} wire {wi}"):
                    if abs(_dot(normal, point) - station) > LINEAR_TOL_MM:
                        raise _Refusal(f"{feature_id} wire {wi}: line endpoint is off plane")
            polygon = _compile_polygon(edges, u, v, f"{feature_id} wire {wi}")
            loops.append(_Loop(wi, "POLYGON", points=polygon))
    if not loops or loops[0].wire_index != 1:
        raise _Refusal(f"{feature_id}: outerwire is missing")
    return _Plane(feature_id, normal, station, u, v, tuple(loops), loops[0].kind == "POLYGON", tuple(circles))


def _compile_cylinder(feature: Mapping[str, Any]) -> _Cylinder:
    feature_id, source, trim = feature.get("feature_id"), feature.get("cylinder"), feature.get("trim")
    if not isinstance(feature_id, str) or not isinstance(source, Mapping) or not isinstance(trim, Mapping):
        raise _Refusal("cylinder feature lacks its ID, cylinder, or trim record")
    origin = _vec3(source.get("axis_origin_global_xyz_mm"), f"{feature_id} axis origin")
    axis = _unit(source.get("axis_unit_global_xyz"), f"{feature_id} axis")
    radius = _finite(source.get("radius_mm"), f"{feature_id} radius")
    station_interval = source.get("axis_station_interval_mm")
    parameter_interval = source.get("axis_parameter_interval_mm")
    uv = trim.get("surface_parameter_bounds")
    if radius <= 0 or not isinstance(station_interval, Sequence) or len(station_interval) != 2 or not isinstance(parameter_interval, Sequence) or len(parameter_interval) != 2 or not isinstance(uv, Mapping):
        raise _Refusal(f"{feature_id}: finite cylinder parameters are missing")
    if not isinstance(uv.get("u"), Sequence) or len(uv["u"]) != 2 or not isinstance(uv.get("v"), Sequence) or len(uv["v"]) != 2:
        raise _Refusal(f"{feature_id}: cylinder UV bounds are malformed")
    low, high = (_finite(x, f"{feature_id} station") for x in station_interval)
    p0, p1 = (_finite(x, f"{feature_id} axis parameter") for x in parameter_interval)
    v0, v1 = (_finite(x, f"{feature_id} V bound") for x in uv["v"])
    u0, u1 = (_finite(x, f"{feature_id} U bound") for x in uv["u"])
    if high - low <= LINEAR_TOL_MM or not (_close(low, min(p0, p1)) and _close(high, max(p0, p1)) and _close(low, min(v0, v1)) and _close(high, max(v0, v1))):
        raise _Refusal(f"{feature_id}: finite axis, V, and saved station intervals disagree")
    if abs(abs(u1 - u0) - 2.0 * math.pi) > PARAMETER_TOL:
        raise _Refusal(f"{feature_id}: partial-turn cylinder trim is unsupported")
    wires = trim.get("wires")
    if not isinstance(wires, list) or len(wires) != 1:
        raise _Refusal(f"{feature_id}: cylinder requires one full side wire")
    edges = wires[0].get("edges")
    if not isinstance(edges, list) or len(edges) != wires[0].get("edge_count"):
        raise _Refusal(f"{feature_id}: cylinder trim edge count disagrees")
    circles: list[tuple[Vec3, float]] = []
    seams: list[tuple[Vec3, Vec3]] = []
    for i, edge in enumerate(edges, start=1):
        context = f"{feature_id} trim edge {i}"
        if edge.get("curve_kind") == "CIRCLE":
            center, circle_axis, circle_radius = _circle_edge(edge, context)
            delta = _sub(center, origin)
            station = _dot(delta, axis)
            radial = _sub(delta, tuple(station * x for x in axis))
            if abs(abs(_dot(circle_axis, axis)) - 1.0) > UNIT_TOL or _norm(radial) > LINEAR_TOL_MM or not _close(circle_radius, radius) or min(abs(station - low), abs(station - high)) > LINEAR_TOL_MM:
                raise _Refusal(f"{context}: circular endpoint disagrees with cylinder parameters")
            circles.append((center, station))
        elif edge.get("curve_kind") == "LINE":
            a, b = _line_edge_points(edge, context)
            line = edge.get("line")
            direction = _unit(line.get("direction_global_xyz"), f"{context} direction")
            if abs(abs(_dot(direction, axis)) - 1.0) > UNIT_TOL:
                raise _Refusal(f"{context}: seam is not parallel to cylinder axis")
            for point in (a, b):
                delta = _sub(point, origin)
                station = _dot(delta, axis)
                radial = _sub(delta, tuple(station * x for x in axis))
                if not _close(_norm(radial), radius) or min(abs(station - low), abs(station - high)) > LINEAR_TOL_MM:
                    raise _Refusal(f"{context}: seam endpoint disagrees with finite cylinder")
            seams.append((a, b))
        else:
            raise _Refusal(f"{context}: unsupported cylinder trim curve")
    if len(circles) != 2 or len(seams) != 1 or not (_close(min(s for _, s in circles), low) and _close(max(s for _, s in circles), high)):
        raise _Refusal(f"{feature_id}: full cylinder must have two end circles and one validated seam")
    side = source.get("material_side_geometry")
    radial_dot = _finite(source.get("radial_normal_dot"), f"{feature_id} radial-normal dot")
    normal = _unit(source.get("normal_global_xyz"), f"{feature_id} saved oriented normal")
    sample = _vec3(source.get("normal_sample_global_xyz_mm"), f"{feature_id} normal sample")
    delta = _sub(sample, origin)
    sample_station = _dot(delta, axis)
    radial = _sub(delta, tuple(sample_station * x for x in axis))
    radial_length = _norm(radial)
    if source.get("normal_sample_valid_on_trim") is not True or not _close(radial_length, radius) or not low - LINEAR_TOL_MM <= sample_station <= high + LINEAR_TOL_MM:
        raise _Refusal(f"{feature_id}: saved oriented-normal sample is outside the finite cylinder")
    expected_dot = _dot(normal, tuple(x / radial_length for x in radial))
    if abs(expected_dot - radial_dot) > UNIT_TOL or abs(abs(radial_dot) - 1.0) > UNIT_TOL:
        raise _Refusal(f"{feature_id}: saved oriented normal conflicts with radial sample")
    if side not in ("bore_like", "exterior_like") or (side == "bore_like") != (radial_dot < 0):
        raise _Refusal(f"{feature_id}: material-side label is ambiguous or inconsistent")
    return _Cylinder(feature_id, origin, axis, radius, low, high, math.copysign(1.0, radial_dot), side)


@lru_cache(maxsize=8)
def _compile_member_cached(canonical: bytes) -> _Member:
    record = json.loads(canonical)
    member_id = record.get("member_id")
    if member_id not in TARGET_MEMBERS:
        raise _Refusal(f"member {member_id!r} is outside the eight target receivers")
    features = record.get("features")
    if not isinstance(features, list) or not features:
        raise _Refusal(f"{member_id}: features must be a nonempty list")
    planes: list[_Plane] = []
    cylinders: list[_Cylinder] = []
    ids: set[str] = set()
    for feature in features:
        if not isinstance(feature, Mapping):
            raise _Refusal(f"{member_id}: malformed feature row")
        feature_id = feature.get("feature_id")
        if not isinstance(feature_id, str) or feature_id in ids:
            raise _Refusal(f"{member_id}: missing or duplicate feature ID")
        ids.add(feature_id)
        if feature.get("surface_kind") == "PLANE":
            planes.append(_compile_plane(feature))
        elif feature.get("surface_kind") == "CYLINDER":
            cylinders.append(_compile_cylinder(feature))
        else:
            raise _Refusal(f"{member_id}: unsupported surface kind {feature.get('surface_kind')!r}")
    if not planes or not cylinders:
        raise _Refusal(f"{member_id}: receiver requires planes and cylinders")
    return _Member(member_id, tuple(planes), tuple(cylinders), frozenset(ids))


def _compile_member(record: Mapping[str, Any]) -> _Member:
    if not isinstance(record, Mapping):
        raise _Refusal("member_record must be a saved member JSON object")
    try:
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise _Refusal(f"member_record is not finite JSON: {error}") from error
    return _compile_member_cached(canonical)


def _circle_matches_endpoint(center: Vec3, circle_axis: Vec3, radius: float, cylinder: _Cylinder) -> tuple[bool, float | None]:
    if abs(abs(_dot(circle_axis, cylinder.axis)) - 1.0) > UNIT_TOL or not _close(radius, cylinder.radius):
        return False, None
    delta = _sub(center, cylinder.origin)
    station = _dot(delta, cylinder.axis)
    radial = _sub(delta, tuple(station * x for x in cylinder.axis))
    if _norm(radial) > LINEAR_TOL_MM or min(abs(station - cylinder.low), abs(station - cylinder.high)) > LINEAR_TOL_MM:
        return False, None
    return True, station


def _own_hole_wires(member: _Member, own_feature_id: str) -> tuple[_Cylinder, frozenset[tuple[str, int]]]:
    matches = [c for c in member.cylinders if c.feature_id == own_feature_id]
    if len(matches) != 1 or matches[0].material_side != "bore_like":
        raise _Refusal(f"{own_feature_id!r} must identify one bore-like cylinder on {member.member_id}")
    own = matches[0]
    endpoint_wires: dict[str, list[tuple[str, int]]] = {"low": [], "high": []}
    for plane in member.planes:
        for wi, center, axis, radius in plane.circle_loops:
            matched, station = _circle_matches_endpoint(center, axis, radius, own)
            if matched and plane.outer_is_polygon and wi != 1:
                side = "low" if abs(station - own.low) <= abs(station - own.high) else "high"
                endpoint_wires[side].append((plane.feature_id, wi))
    if len(endpoint_wires["low"]) != 1 or len(endpoint_wires["high"]) != 1:
        raise _Refusal(f"{own_feature_id}: expected one matching inner trim loop at each bore end")
    for plane in member.planes:
        for wi, center, axis, radius in plane.circle_loops:
            matches = [c for c in member.cylinders if _circle_matches_endpoint(center, axis, radius, c)[0]]
            if len(matches) != 1:
                raise _Refusal(f"{plane.feature_id} wire {wi}: circle maps to {len(matches)} cylinder endpoints; expected one")
    return own, frozenset(endpoint_wires["low"] + endpoint_wires["high"])


def _plane_state(plane: _Plane, point: Vec3, filled_wires: frozenset[int] = frozenset()) -> tuple[str, bool, bool]:
    local = (_dot(point, plane.basis_u), _dot(point, plane.basis_v))
    inside, on, outer = False, False, False
    for loop in plane.loops:
        if loop.wire_index in filled_wires:
            continue
        if loop.kind == "POLYGON":
            state = _point_in_polygon(local, loop.points)
        else:
            assert loop.center is not None and loop.radius is not None
            radial = math.dist(local, loop.center)
            state = "ON" if abs(radial - loop.radius) <= LINEAR_TOL_MM else ("IN" if radial < loop.radius else "OUT")
        if loop.wire_index == 1 and loop.kind == "POLYGON":
            outer = state in ("IN", "ON")
        if state == "ON":
            on = True
        elif state == "IN":
            inside = not inside
    return ("ON" if on else "IN" if inside else "OUT"), outer, on


def _raw_hits(
    member: _Member, origin: Vec3, direction: Vec3, own_feature_id: str,
    own_wires: frozenset[tuple[str, int]], *, fill_own_hole: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    hits: list[dict[str, Any]] = []
    ambiguities: list[str] = []
    fill_by_feature: dict[str, frozenset[int]] = {}
    if fill_own_hole:
        for fid, wi in own_wires:
            fill_by_feature[fid] = fill_by_feature.get(fid, frozenset()) | {wi}
    for plane in member.planes:
        denominator = _dot(plane.normal, direction)
        signed = _dot(plane.normal, origin) - plane.station
        if abs(denominator) <= ANGLE_TOL:
            if abs(signed) <= LINEAR_TOL_MM:
                ambiguities.append(f"{plane.feature_id}: query ray is coplanar with a saved plane")
            continue
        t = -signed / denominator
        if t < -COINCIDENT_TOL_MM:
            continue
        t = 0.0 if abs(t) <= COINCIDENT_TOL_MM else t
        point = _add_scaled(origin, direction, t)
        filled = fill_by_feature.get(plane.feature_id, frozenset()) if fill_own_hole else frozenset()
        state, outer, on = _plane_state(plane, point, filled)
        if state == "OUT":
            continue
        cap = len(plane.loops) == 1 and plane.loops[0].kind == "CIRCLE"
        classification = "ambiguous" if on else (
            "blind_circular_cap" if cap else
            "polygon_outerwire_plane" if plane.outer_is_polygon and outer else
            "non_exterior_plane"
        )
        hits.append({
            "distance_mm": t, "point_global_xyz_mm": point, "feature_id": plane.feature_id,
            "surface_kind": "PLANE", "oriented_normal_dot": denominator,
            "entry_or_exit": "tangent" if abs(denominator) <= DOT_TOL else ("entry" if denominator < 0 else "exit"),
            "tangent": abs(denominator) <= DOT_TOL, "trim_position": state,
            "trim_boundary": on, "exterior_classification": classification,
        })
    for cylinder in member.cylinders:
        if cylinder.feature_id == own_feature_id:
            continue
        delta = _sub(origin, cylinder.origin)
        axial_origin = _dot(delta, cylinder.axis)
        axial_dir = _dot(direction, cylinder.axis)
        dperp = _sub(direction, tuple(axial_dir * x for x in cylinder.axis))
        pperp = _sub(delta, tuple(axial_origin * x for x in cylinder.axis))
        a = _dot(dperp, dperp)
        b = 2.0 * _dot(pperp, dperp)
        c = _dot(pperp, pperp) - cylinder.radius * cylinder.radius
        if a <= ANGLE_TOL * ANGLE_TOL:
            if abs(c) <= LINEAR_TOL_MM * max(1.0, cylinder.radius):
                ambiguities.append(f"{cylinder.feature_id}: ray lies on a cylinder side")
            continue
        discriminant = b * b - 4.0 * a * c
        disc_tol = 1.0e-12 * max(1.0, b * b, abs(4.0 * a * c))
        if discriminant < -disc_tol:
            continue
        tangent_root = abs(discriminant) <= disc_tol
        root = math.sqrt(max(0.0, discriminant))
        roots = [-b / (2.0 * a)] if tangent_root else [(-b - root) / (2.0 * a), (-b + root) / (2.0 * a)]
        for t in sorted(roots):
            if t < -COINCIDENT_TOL_MM:
                continue
            t = 0.0 if abs(t) <= COINCIDENT_TOL_MM else t
            point = _add_scaled(origin, direction, t)
            delta_hit = _sub(point, cylinder.origin)
            station = _dot(delta_hit, cylinder.axis)
            if station < cylinder.low - LINEAR_TOL_MM or station > cylinder.high + LINEAR_TOL_MM:
                continue
            radial = _sub(delta_hit, tuple(station * x for x in cylinder.axis))
            radial_len = _norm(radial)
            if radial_len <= 1.0e-14:
                ambiguities.append(f"{cylinder.feature_id}: cylinder hit lacks a radial normal")
                continue
            normal = tuple(cylinder.radial_normal_sign * x / radial_len for x in radial)
            normal_dot = _dot(normal, direction)
            tangent = tangent_root or abs(normal_dot) <= DOT_TOL
            hits.append({
                "distance_mm": t, "point_global_xyz_mm": point, "feature_id": cylinder.feature_id,
                "surface_kind": "CYLINDER", "oriented_normal_dot": normal_dot,
                "entry_or_exit": "tangent" if tangent else ("entry" if normal_dot < 0 else "exit"),
                "tangent": tangent,
                "trim_position": "IN",
                "trim_boundary": tangent_root or abs(station - cylinder.low) <= LINEAR_TOL_MM or abs(station - cylinder.high) <= LINEAR_TOL_MM,
                "exterior_classification": "bore_wall" if cylinder.material_side == "bore_like" else "non_exterior_plane",
            })
    hits.sort(key=lambda h: (h["distance_mm"], h["feature_id"]))
    return hits, ambiguities


def _group_hits(raw: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: list[list[Mapping[str, Any]]] = []
    for hit in raw:
        if groups and abs(hit["distance_mm"] - groups[-1][0]["distance_mm"]) <= COINCIDENT_TOL_MM and _points_close(hit["point_global_xyz_mm"], groups[-1][0]["point_global_xyz_mm"], COINCIDENT_TOL_MM):
            groups[-1].append(hit)
        else:
            groups.append([hit])
    result = []
    for group in groups:
        group = sorted(group, key=lambda h: h["feature_id"])
        dots = [float(h["oriented_normal_dot"]) for h in group]
        signs = {1 if d > DOT_TOL else -1 for d in dots if abs(d) > DOT_TOL}
        crossing = "ambiguous" if len(signs) > 1 else "tangent" if not signs else ("entry" if next(iter(signs)) < 0 else "exit")
        classes = {str(h["exterior_classification"]) for h in group}
        exterior = next(iter(classes)) if len(classes) == 1 else "ambiguous" if "ambiguous" in classes else "polygon_outerwire_plane" if "polygon_outerwire_plane" in classes else "non_exterior_plane"
        ids = [str(h["feature_id"]) for h in group]
        result.append({
            "distance_mm": float(group[0]["distance_mm"]),
            "point_global_xyz_mm": list(group[0]["point_global_xyz_mm"]),
            "feature_id": ids[0],
            "feature_ids": ids,
            "surface_kind": group[0]["surface_kind"] if len(group) == 1 else "SIMULTANEOUS",
            "oriented_normal_dot": dots[0] if len(signs) <= 1 else None,
            "entry_or_exit": crossing,
            "tangent": not signs,
            "corner_ambiguity": len(group) > 1 or any(bool(h["trim_boundary"]) for h in group) or crossing == "ambiguous",
            "exterior_classification": exterior,
            "hits": [{
                "feature_id": str(h["feature_id"]), "surface_kind": str(h["surface_kind"]),
                "oriented_normal_dot": float(h["oriented_normal_dot"]),
                "entry_or_exit": str(h["entry_or_exit"]), "tangent": bool(h["tangent"]),
                "trim_position": str(h["trim_position"]),
                "exterior_classification": str(h["exterior_classification"]),
            } for h in group],
        })
    return result


def _trace_state(events: Sequence[Mapping[str, Any]], *, initially_inside: bool) -> tuple[bool, str | None]:
    inside = initially_inside
    for event in events:
        if event["distance_mm"] <= COINCIDENT_TOL_MM:
            return inside, f"query origin intersects {event['feature_id']}"
        crossing = event["entry_or_exit"]
        if crossing == "tangent":
            return inside, f"tangent event at {event['feature_id']} prevents a clear material-boundary sequence"
        if crossing == "ambiguous" or event["corner_ambiguity"]:
            return inside, f"corner/simultaneous event at {event['feature_id']} has ambiguous crossing topology"
        expected = "exit" if inside else "entry"
        if crossing != expected:
            return inside, f"non-alternating crossings at {event['feature_id']}: expected {expected}, got {crossing}"
        inside = not inside
    return (inside, "ray ends inside the member after the saved-face trace") if inside else (inside, None)


def _origin_membership(member: _Member, origin: Vec3, direction: Vec3, own_id: str, own_wires: frozenset[tuple[str, int]]) -> dict[str, str]:
    for sign in (1.0, -1.0):
        ray = tuple(sign * x for x in direction)
        raw, ambiguities = _raw_hits(member, origin, ray, own_id, own_wires, fill_own_hole=True)
        if ambiguities:
            return {"status": "ambiguous", "reason": ambiguities[0]}
        inside, reason = _trace_state(_group_hits(raw), initially_inside=True)
        if reason is not None or inside:
            return {"status": "ambiguous", "reason": reason or "filled-own-bore ray did not exit"}
    return {"status": "inside_filled_own_bore", "reason": "both signed directions have clear outward material crossings"}


def _copy_event(event: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(event, allow_nan=False))


def _base_result(status: str, member_id: Any, own_id: str, origin: Vec3 | None, direction: Vec3 | None, reason: str) -> dict[str, Any]:
    return {
        "schema": QUERY_SCHEMA, "status": status,
        "member_id": member_id if isinstance(member_id, str) else None,
        "own_feature_id": own_id,
        "origin_global_xyz_mm": list(origin) if origin is not None else None,
        "direction_global_unit": list(direction) if direction is not None else None,
        "origin_membership": {"status": "ambiguous", "reason": reason},
        "events": [], "first_material_exit": None, "first_exterior_exit": None,
        "distance_mm": None,
        "exterior_classification": {"status": "null", "kind": None, "reason": reason},
        "reason": reason,
        "limits": [
            "geometric ray distance only; no NDS, Cdelta, group, splitting, or acceptance calculation",
            "the supplied interior query origin is distinct from the physical force point",
            "sampled stations do not establish a through-depth minimum",
        ],
    }


def query_member_direction(
    member_record: Mapping[str, Any],
    own_feature_id: str,
    origin_global_xyz_mm: Sequence[float],
    direction_global_unit: Sequence[float],
) -> dict[str, Any]:
    """Query one supplied interior station along one already-unit global ray."""
    member_id = member_record.get("member_id") if isinstance(member_record, Mapping) else None
    origin: Vec3 | None = None
    direction: Vec3 | None = None
    try:
        origin = _vec3(origin_global_xyz_mm, "query origin")
        direction = _unit(direction_global_unit, "query direction")
        if not isinstance(own_feature_id, str) or not own_feature_id:
            raise _Refusal("own_feature_id must be a nonempty feature ID")
        member = _compile_member(member_record)
        own, own_wires = _own_hole_wires(member, own_feature_id)
        own_delta = _sub(origin, own.origin)
        own_station = _dot(own_delta, own.axis)
        own_radial = _sub(own_delta, tuple(own_station * x for x in own.axis))
        if _norm(own_radial) > LINEAR_TOL_MM:
            raise _Refusal(
                f"query origin is {_norm(own_radial):.9g} mm off the {own_feature_id} bore centerline"
            )
        if own_station < own.low - LINEAR_TOL_MM or own_station > own.high + LINEAR_TOL_MM:
            raise _Refusal(
                f"query origin station {own_station:.9g} mm is outside the saved finite {own_feature_id} bore interval"
            )
        # Preserve the forward trace even if the filled-own-bore membership
        # check later refuses the station or detects a corner/tangent.
        raw, ambiguities = _raw_hits(
            member, origin, direction, own.feature_id, own_wires, fill_own_hole=False
        )
        events = _group_hits(raw)
        membership = _origin_membership(member, origin, direction, own.feature_id, own_wires)
        if membership["status"] != "inside_filled_own_bore":
            result = _base_result("ambiguous", member.member_id, own_feature_id, origin, direction, membership["reason"])
            result["origin_membership"] = membership
            result["events"] = events
            return result
        _, path_reason = _trace_state(events, initially_inside=True)
        material_exit = next((_copy_event(e) for e in events if e["entry_or_exit"] == "exit"), None)
        exterior_hits = [e for e in events if e["entry_or_exit"] == "exit" and e["exterior_classification"] == "polygon_outerwire_plane"]
        exterior = _copy_event(exterior_hits[0]) if exterior_hits else None
        reason: str | None = None
        status = "ok"
        if ambiguities:
            status, reason = "ambiguous", ambiguities[0]
        elif path_reason is not None:
            status, reason = "ambiguous", path_reason
        elif exterior is not None and exterior["corner_ambiguity"]:
            status, reason = "ambiguous", "first exterior plane crossing is simultaneous with a trim corner"
        elif exterior is None:
            first_exit = next((e for e in events if e["entry_or_exit"] == "exit"), None)
            if first_exit is None:
                reason = "no outward boundary event is present on the supplied ray"
            elif first_exit["exterior_classification"] == "bore_wall":
                reason = "ray reaches a non-own bore boundary; no polygon outerwire exit is available"
            elif first_exit["exterior_classification"] == "blind_circular_cap":
                reason = "ray reaches a blind circular cap, which is not an exterior free surface"
            else:
                reason = "no supported polygon outerwire plane exit was found"
        if status != "ok":
            exterior = None
        return {
            "schema": QUERY_SCHEMA, "status": status,
            "member_id": member.member_id, "own_feature_id": own_feature_id,
            "origin_global_xyz_mm": list(origin), "direction_global_unit": list(direction),
            "origin_membership": membership, "events": events,
            "first_material_exit": material_exit, "first_exterior_exit": exterior,
            "distance_mm": exterior["distance_mm"] if exterior is not None else None,
            "exterior_classification": {
                "status": "classified" if exterior is not None else "null",
                "kind": "polygon_outerwire_plane" if exterior is not None else None,
                "reason": None if exterior is not None else reason,
            },
            "reason": reason,
            "limits": [
                "geometric ray distance only; no NDS, Cdelta, group, splitting, or acceptance calculation",
                "query origin is the supplied interior bolt-bore station and is separate from the physical force point",
                "directional station results do not establish a through-depth minimum",
                "saved plane normals are already outward and are not flipped from topology labels",
            ],
        }
    except _Refusal as error:
        return _base_result("unsupported", member_id, str(own_feature_id), origin, direction, str(error))


__all__ = [
    "DEFAULT_SURFACES", "QUERY_SCHEMA", "SURFACE_REGISTER_SHA256",
    "TARGET_MEMBERS", "load_authenticated_surface_records", "query_member_direction",
]
