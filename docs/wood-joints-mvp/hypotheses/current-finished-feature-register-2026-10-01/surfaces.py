#!/usr/bin/env python3
"""Extract bounded descriptive face geometry from the reviewed 44 finished STEP solids."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import cadquery as cq
import OCP
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.gp import gp_Trsf
from OCP.TopAbs import TopAbs_IN, TopAbs_ON

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
OUTPUT = OUT_DIR / "surfaces.json"
PINS_OUTPUT = OUT_DIR / "source-pins.json"
STOCK_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01"
)
STOCK_OUTPUT = STOCK_DIR / "envelopes.json"
STOCK_PINS = STOCK_DIR / "source-pins.json"
EXPECTED_ENVELOPES_SHA256 = (
    "0f13d1c697d8c7b3dcb1a5db5a7ab215e05bc9bee4e729fc35763ff449436e01"
)
EXPECTED_MANIFEST_SHA256 = (
    "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11"
)
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_SELECTED = "compact-floor-flush-development"
EXPECTED_CADQUERY = "2.8.0"
EXPECTED_OCP_PACKAGE = "7.9.3.1.1"
LINEAR_TOLERANCE_MM = 1e-5
VOLUME_TOLERANCE_MM3 = 1e-3
FRAME_TOLERANCE = 1e-8
ROUNDTRIP_TOLERANCE_MM = 1e-7
SIDE_TOLERANCE = 1e-6


class SurfaceError(ValueError):
    """Raised when pinned source identity or a geometry contract is inconsistent."""


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_value_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256_bytes(raw)


def _unit(vector: Iterable[float], context: str) -> tuple[float, float, float]:
    values = tuple(float(value) for value in vector)
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        raise SurfaceError(f"{context}: expected three finite vector components")
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 1e-14:
        raise SurfaceError(f"{context}: zero vector")
    return tuple(value / norm for value in values)  # type: ignore[return-value]


def _dot(a: Iterable[float], b: Iterable[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def _cross(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _finite_point(values: Iterable[float], context: str) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3 or not all(math.isfinite(value) for value in result):
        raise SurfaceError(f"{context}: expected three finite coordinates")
    return result  # type: ignore[return-value]


def _validate_frame(
    origin: Iterable[float], columns: Iterable[Iterable[float]]
) -> tuple[
    tuple[float, float, float],
    tuple[tuple[float, float, float], ...],
]:
    frame_origin = _finite_point(origin, "stock-frame origin")
    raw_basis = tuple(
        _finite_point(axis, "stock-frame basis column") for axis in columns
    )
    if len(raw_basis) != 3:
        raise SurfaceError("stock-frame basis must contain g, q, and r columns")
    if any(
        abs(math.sqrt(_dot(axis, axis)) - 1.0) > FRAME_TOLERANCE for axis in raw_basis
    ):
        raise SurfaceError("stock-frame basis columns must already be unit length")
    basis = tuple(_unit(axis, "stock-frame basis column") for axis in raw_basis)
    if any(
        abs(_dot(basis[i], basis[j])) > FRAME_TOLERANCE
        for i in range(3)
        for j in range(i)
    ):
        raise SurfaceError("stock-frame basis columns are not orthogonal")
    handed = _dot(_cross(basis[0], basis[1]), basis[2])
    if abs(handed - 1.0) > FRAME_TOLERANCE:
        raise SurfaceError("stock-frame basis is not right-handed")
    return frame_origin, basis


def _to_stock_point(
    point_global: Iterable[float],
    origin_global: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
) -> tuple[float, float, float]:
    delta = tuple(
        float(x) - o for x, o in zip(point_global, origin_global, strict=True)
    )
    return tuple(_dot(axis, delta) for axis in basis)  # type: ignore[return-value]


def _to_global_point(
    point_stock: Iterable[float],
    origin_global: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
) -> tuple[float, float, float]:
    local = tuple(float(value) for value in point_stock)
    if len(local) != 3 or not all(math.isfinite(value) for value in local):
        raise SurfaceError("stock point must contain three finite coordinates")
    return tuple(
        origin_global[row] + sum(basis[col][row] * local[col] for col in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def _to_stock_vector(
    vector_global: Iterable[float],
    basis: tuple[tuple[float, float, float], ...],
) -> tuple[float, float, float]:
    vector = _finite_point(vector_global, "global vector")
    return tuple(_dot(axis, vector) for axis in basis)  # type: ignore[return-value]


def _to_global_vector(
    vector_stock: Iterable[float], basis: tuple[tuple[float, float, float], ...]
) -> tuple[float, float, float]:
    local = _finite_point(vector_stock, "stock-frame vector")
    return tuple(
        sum(basis[col][row] * local[col] for col in range(3)) for row in range(3)
    )  # type: ignore[return-value]


def _matrix_from_rows(rows: list[list[float]]) -> cq.Matrix:
    transform = gp_Trsf()
    transform.SetValues(
        rows[0][0],
        rows[0][1],
        rows[0][2],
        rows[0][3],
        rows[1][0],
        rows[1][1],
        rows[1][2],
        rows[1][3],
        rows[2][0],
        rows[2][1],
        rows[2][2],
        rows[2][3],
    )
    return cq.Matrix(transform)


def _global_to_frame_matrix(
    origin: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
) -> cq.Matrix:
    rows = []
    for axis in basis:
        rows.append([axis[0], axis[1], axis[2], -_dot(axis, origin)])
    return _matrix_from_rows(rows)


def _global_to_axis_matrix(
    origin: tuple[float, float, float], axis: tuple[float, float, float]
) -> cq.Matrix:
    helper = (1.0, 0.0, 0.0) if abs(axis[0]) < 0.8 else (0.0, 1.0, 0.0)
    local_x = _unit(_cross(helper, axis), "cylinder-axis transverse x")
    local_y = _unit(_cross(axis, local_x), "cylinder-axis transverse y")
    return _global_to_frame_matrix(origin, (local_x, local_y, axis))


def _bbox_values(shape: cq.Shape) -> list[float]:
    bounds = shape.BoundingBox()
    return [
        float(bounds.xmin),
        float(bounds.xmax),
        float(bounds.ymin),
        float(bounds.ymax),
        float(bounds.zmin),
        float(bounds.zmax),
    ]


def _bbox_in_stock(
    shape: cq.Shape,
    origin: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
) -> list[float]:
    return _bbox_values(shape.transformShape(_global_to_frame_matrix(origin, basis)))


def _finite_interval(a: float, b: float) -> list[float] | None:
    if not math.isfinite(a) or not math.isfinite(b):
        return None
    return [float(a), float(b)]


def _vertex_rows(
    face: cq.Face,
    origin: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
) -> list[dict[str, Any]]:
    result = []
    for index, vertex in enumerate(face.Vertices(), start=1):
        global_xyz = _finite_point(vertex.Center().toTuple(), "STEP face vertex")
        stock_gqr = _to_stock_point(global_xyz, origin, basis)
        reconstructed = _to_global_point(stock_gqr, origin, basis)
        if (
            max(abs(a - b) for a, b in zip(global_xyz, reconstructed, strict=True))
            > ROUNDTRIP_TOLERANCE_MM
        ):
            raise SurfaceError("global/stock vertex coordinate round trip failed")
        result.append(
            {
                "vertex_index_one_based": index,
                "global_xyz_mm": list(global_xyz),
                "stock_gqr_mm": list(stock_gqr),
            }
        )
    return result


def _edge_trace(edge: cq.Edge) -> dict[str, Any]:
    adaptor = edge._geomAdaptor()
    first = float(adaptor.FirstParameter())
    last = float(adaptor.LastParameter())
    start = _finite_point(adaptor.Value(first).Coord(), "trim edge start")
    end = _finite_point(adaptor.Value(last).Coord(), "trim edge end")
    vertices = [
        list(_finite_point(vertex.Center().toTuple(), "trim edge vertex"))
        for vertex in edge.Vertices()
    ]
    row: dict[str, Any] = {
        "curve_kind": edge.geomType(),
        "length_mm": float(edge.Length()),
        "parameter_bounds": _finite_interval(first, last),
        "parameter_endpoint_global_xyz_mm": [list(start), list(end)],
        "topological_vertices_global_xyz_mm": vertices,
    }
    if edge.geomType() == "CIRCLE":
        circle = adaptor.Circle()
        row["circle"] = {
            "center_global_xyz_mm": list(
                _finite_point(circle.Location().Coord(), "trim circle center")
            ),
            "axis_unit_global_xyz": list(
                _unit(circle.Axis().Direction().Coord(), "trim circle axis")
            ),
            "radius_mm": float(circle.Radius()),
        }
    elif edge.geomType() == "LINE":
        line = adaptor.Line()
        row["line"] = {
            "origin_global_xyz_mm": list(
                _finite_point(line.Location().Coord(), "trim line origin")
            ),
            "direction_global_xyz": list(
                _unit(line.Direction().Coord(), "trim line direction")
            ),
        }
    return row


def _trim_trace(
    face: cq.Face,
    origin: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
) -> dict[str, Any]:
    u0, u1, v0, v1 = (float(value) for value in face._uvBounds())
    wires = []
    for wire_index, wire in enumerate(face.Wires(), start=1):
        wires.append(
            {
                "wire_index_one_based": wire_index,
                "edge_count": len(wire.Edges()),
                "edges": [_edge_trace(edge) for edge in wire.Edges()],
            }
        )
    return {
        "surface_parameter_bounds": {
            "u": _finite_interval(u0, u1),
            "v": _finite_interval(v0, v1),
        },
        "wire_count": len(wires),
        "edge_count": sum(wire["edge_count"] for wire in wires),
        "wires": wires,
        "bounds_global_xyz_mm": _bbox_values(face),
        "bounds_stock_gqr_mm": _bbox_in_stock(face, origin, basis),
    }


def _plane_trace(
    face: cq.Face,
    centroid_global: tuple[float, float, float],
    centroid_stock: tuple[float, float, float],
    origin: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
) -> dict[str, Any]:
    normal_global = _unit(face.normalAt().toTuple(), "oriented STEP plane normal")
    normal_stock = _to_stock_vector(normal_global, basis)
    normal_stock = _unit(normal_stock, "stock-frame plane normal")
    if (
        max(
            abs(a - b)
            for a, b in zip(
                normal_global, _to_global_vector(normal_stock, basis), strict=True
            )
        )
        > FRAME_TOLERANCE
    ):
        raise SurfaceError("global/stock plane-normal round trip failed")
    # The oriented plane equation is n·x = station. These signed offsets are
    # descriptive coordinates; they do not infer a seat, cut, or taper role.
    global_station = _dot(normal_global, centroid_global)
    stock_station = _dot(normal_stock, centroid_stock)
    axis_angles = {
        name: math.degrees(
            math.acos(min(1.0, max(0.0, abs(_dot(normal_global, axis)))))
        )
        for name, axis in zip(("g", "q", "r"), basis, strict=True)
    }
    return {
        "normal_global_xyz": list(normal_global),
        "normal_stock_gqr": list(normal_stock),
        "signed_plane_station_global_mm": global_station,
        "signed_plane_offset_stock_mm": stock_station,
        "absolute_angle_to_stock_axes_deg": axis_angles,
        "face_topology_orientation": str(face.wrapped.Orientation()),
        "coordinate_equation": "normal · point = signed station",
        "stock_origin_global_xyz_mm": list(origin),
    }


def _cylinder_trace(
    face: cq.Face,
    centroid_global: tuple[float, float, float],
    centroid_stock: tuple[float, float, float],
    origin: tuple[float, float, float],
    basis: tuple[tuple[float, float, float], ...],
) -> dict[str, Any]:
    adaptor = BRepAdaptor_Surface(face.wrapped, True)
    cylinder = adaptor.Cylinder()
    axis_origin = _finite_point(
        cylinder.Axis().Location().Coord(), "STEP cylinder axis origin"
    )
    axis_unit = _unit(cylinder.Axis().Direction().Coord(), "STEP cylinder axis")
    axis_origin_stock = _to_stock_point(axis_origin, origin, basis)
    axis_stock = _unit(_to_stock_vector(axis_unit, basis), "stock-frame cylinder axis")
    if (
        max(
            abs(a - b)
            for a, b in zip(
                axis_unit, _to_global_vector(axis_stock, basis), strict=True
            )
        )
        > FRAME_TOLERANCE
    ):
        raise SurfaceError("global/stock cylinder-axis round trip failed")
    u0, u1, v0, v1 = (float(value) for value in face._uvBounds())
    u_mid = 0.5 * (u0 + u1)
    v_mid = 0.5 * (v0 + v1)
    sample_global = None
    normal_global = None
    radial_dot = None
    sample_state = None
    sample_is_on_trim = False
    side = "ambiguous"
    if all(math.isfinite(value) for value in (u_mid, v_mid)):
        sample = adaptor.Value(u_mid, v_mid)
        sample_global = _finite_point(sample.Coord(), "cylinder face normal sample")
        classifier = BRepClass_FaceClassifier(
            face.wrapped, sample, ROUNDTRIP_TOLERANCE_MM
        )
        sample_state = str(classifier.State())
        sample_is_on_trim = classifier.State() in (TopAbs_IN, TopAbs_ON)
        if sample_is_on_trim:
            normal_global = _unit(
                face.normalAt().toTuple(), "oriented STEP cylinder normal"
            )
            sample_delta = tuple(sample_global[i] - axis_origin[i] for i in range(3))
            axial = _dot(sample_delta, axis_unit)
            radial = tuple(sample_delta[i] - axial * axis_unit[i] for i in range(3))
            radial_norm = math.sqrt(_dot(radial, radial))
            if radial_norm > 1e-10:
                radial_unit = tuple(value / radial_norm for value in radial)
                radial_dot = _dot(normal_global, radial_unit)
                if radial_dot > 1.0 - SIDE_TOLERANCE:
                    side = "exterior_like"
                elif radial_dot < -1.0 + SIDE_TOLERANCE:
                    side = "bore_like"
    oriented_bounds = face.transformShape(
        _global_to_axis_matrix(axis_origin, axis_unit)
    ).BoundingBox()
    station_interval = [float(oriented_bounds.zmin), float(oriented_bounds.zmax)]
    if any(not math.isfinite(value) for value in station_interval):
        raise SurfaceError("cylindrical face has a non-finite oriented axis interval")
    parameter_interval = _finite_interval(v0, v1)
    # BRepAdaptor's finite cylinder V parameters are the same axial coordinate
    # measured from its axis origin. Retain both traces and reject disagreement.
    if (
        parameter_interval is not None
        and max(
            abs(a - b)
            for a, b in zip(station_interval, parameter_interval, strict=True)
        )
        > LINEAR_TOLERANCE_MM
    ):
        raise SurfaceError(
            "cylinder oriented-BBox and exact V-parameter intervals disagree"
        )
    return {
        "axis_origin_global_xyz_mm": list(axis_origin),
        "axis_unit_global_xyz": list(axis_unit),
        "radius_mm": float(cylinder.Radius()),
        "axis_origin_stock_gqr_mm": list(axis_origin_stock),
        "axis_unit_stock_gqr": list(axis_stock),
        "axis_station_interval_mm": station_interval,
        "axis_parameter_interval_mm": parameter_interval,
        "normal_sample_global_xyz_mm": list(sample_global)
        if sample_global is not None
        else None,
        "normal_sample_topology_state": sample_state,
        "normal_sample_valid_on_trim": sample_is_on_trim,
        "normal_global_xyz": list(normal_global) if normal_global is not None else None,
        "radial_normal_dot": radial_dot,
        "material_side_geometry": side,
        "surface_orientation_trace": str(face.wrapped.Orientation()),
        "material_side_method": "oriented solid-face normal dot radial direction at the trimmed UV midpoint; geometry only",
        "centroid_global_xyz_mm": list(centroid_global),
        "centroid_stock_gqr_mm": list(centroid_stock),
    }


def feature_from_face(
    member_id: str,
    face_index_one_based: int,
    face: cq.Face,
    stock_frame: dict[str, Any],
) -> dict[str, Any]:
    origin, basis = _validate_frame(
        stock_frame["origin_global_xyz_mm"],
        stock_frame["basis_columns_global_xyz"],
    )
    centroid_global = _finite_point(face.Center().toTuple(), "STEP face centroid")
    centroid_stock = _to_stock_point(centroid_global, origin, basis)
    if (
        max(
            abs(a - b)
            for a, b in zip(
                centroid_global,
                _to_global_point(centroid_stock, origin, basis),
                strict=True,
            )
        )
        > ROUNDTRIP_TOLERANCE_MM
    ):
        raise SurfaceError(
            f"{member_id}/facet{face_index_one_based:03d}: centroid round trip failed"
        )
    surface_kind = str(face.geomType())
    feature: dict[str, Any] = {
        "feature_id": f"{member_id}/facet{face_index_one_based:03d}",
        "face_index_one_based": face_index_one_based,
        "surface_kind": surface_kind,
        "classification": "descriptive_planar_patch"
        if surface_kind == "PLANE"
        else (
            "descriptive_cylindrical_patch"
            if surface_kind == "CYLINDER"
            else "unsupported_descriptive_only"
        ),
        "area_mm2": float(face.Area()),
        "centroid_global_xyz_mm": list(centroid_global),
        "centroid_stock_gqr_mm": list(centroid_stock),
        "bounds_global_xyz_mm": _bbox_values(face),
        "bounds_stock_gqr_mm": _bbox_in_stock(face, origin, basis),
        "vertices": _vertex_rows(face, origin, basis),
        "trim": _trim_trace(face, origin, basis),
    }
    if surface_kind == "PLANE":
        feature["plane"] = _plane_trace(
            face, centroid_global, centroid_stock, origin, basis
        )
    elif surface_kind == "CYLINDER":
        feature["cylinder"] = _cylinder_trace(
            face, centroid_global, centroid_stock, origin, basis
        )
    else:
        feature["geometry_trace"] = {
            "surface_kind_as_read_by_cadquery": surface_kind,
            "face_topology_orientation": str(face.wrapped.Orientation()),
            "geometry_status": "surface type is retained with finite bounds, vertices, area, centroid, and trim wires; no axis or analytic meaning is inferred",
        }
    return feature


def features_for_shape(
    member_id: str, shape: cq.Shape, stock_frame: dict[str, Any]
) -> list[dict[str, Any]]:
    faces = shape.Faces()
    rows = [
        feature_from_face(member_id, index, face, stock_frame)
        for index, face in enumerate(faces, start=1)
    ]
    if len(rows) != len(faces) or [row["face_index_one_based"] for row in rows] != list(
        range(1, len(faces) + 1)
    ):
        raise SurfaceError(
            f"{member_id}: feature rows do not cover each STEP face exactly once"
        )
    return rows


def _read_json(root: Path, relative: Path) -> tuple[dict[str, Any], bytes]:
    raw = (root / relative).read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SurfaceError(f"expected JSON object: {relative.as_posix()}")
    return value, raw


def _pin(root: Path, pins: dict[str, Any], name: str, relative: Path) -> None:
    raw = (root / relative).read_bytes()
    pins[name] = {
        "path": relative.as_posix(),
        "sha256": sha256_bytes(raw),
        "size_bytes": len(raw),
    }


def verify_pin_document(root: Path, pins: dict[str, Any]) -> None:
    root = Path(root).resolve()
    for name, pin in pins.get("pins", {}).items():
        relative = Path(pin["path"])
        path = root / relative
        if not path.is_file():
            raise SurfaceError(
                f"pinned file is missing: {relative.as_posix()} ({name})"
            )
        raw = path.read_bytes()
        if sha256_bytes(raw) != pin["sha256"] or len(raw) != int(pin["size_bytes"]):
            raise SurfaceError(f"pinned bytes changed: {relative.as_posix()} ({name})")


def verify_canonical_file(path: Path, value: Any, label: str) -> None:
    if path.read_bytes() != canonical_bytes(value):
        raise SurfaceError(f"{label} is not the exact canonical JSON byte sequence")


def _build_stock_frame(row: dict[str, Any]) -> dict[str, Any]:
    proposed = row["proposed_frame"]
    if proposed.get("status") != "CONTAINED":
        raise SurfaceError(f"{row['member_id']}: reviewed stock basis is not contained")
    basis_values = [
        proposed["grain_axis_global_xyz"],
        proposed["section_q_axis_global_xyz"],
        proposed["section_r_axis_global_xyz"],
    ]
    # Validate the saved vectors before normalization can hide a scaled basis.
    _, basis = _validate_frame((0.0, 0.0, 0.0), basis_values)
    proposed_bounds = row["original_stock_containment"][
        "proposed_stock_bounds_g_q_r_mm"
    ]
    if len(proposed_bounds) != 3 or any(len(pair) != 2 for pair in proposed_bounds):
        raise SurfaceError(f"{row['member_id']}: malformed proposed g/q/r stock bounds")
    lows = [float(pair[0]) for pair in proposed_bounds]
    highs = [float(pair[1]) for pair in proposed_bounds]
    dimensions = [high - low for low, high in zip(lows, highs, strict=True)]
    if any(not math.isfinite(v) or v <= 0 for v in dimensions):
        raise SurfaceError(
            f"{row['member_id']}: proposed stock dimensions are not positive"
        )
    origin = tuple(
        sum(basis[col][coordinate] * lows[col] for col in range(3))
        for coordinate in range(3)
    )
    origin, basis = _validate_frame(origin, basis)
    for mask in range(8):
        expected_local = tuple(
            dimensions[index] if mask & (1 << index) else 0.0 for index in range(3)
        )
        corner_global = _to_global_point(expected_local, origin, basis)
        recovered_local = _to_stock_point(corner_global, origin, basis)
        if (
            max(
                abs(actual - expected)
                for actual, expected in zip(
                    recovered_local, expected_local, strict=True
                )
            )
            > ROUNDTRIP_TOLERANCE_MM
        ):
            raise SurfaceError(
                f"{row['member_id']}: original stock dimensions failed frame round trip"
            )
    return {
        "origin_global_xyz_mm": list(origin),
        "basis_columns_global_xyz": [list(axis) for axis in basis],
        "original_dimensions_gqr_mm": dimensions,
        "original_stock_bounds_in_basis_mm": proposed_bounds,
        "datum_status": "proposed minimum g/q/r corner; not a delivered-stock datum",
        "basis_source": "reviewed proposed stock envelope g/q/r basis",
    }


def _load_exact_solid(
    root: Path,
    binding: dict[str, Any],
    solids_row: dict[str, Any],
) -> cq.Solid:
    step_path = Path(binding["path"])
    raw = (root / step_path).read_bytes()
    if (
        len(raw) != int(binding["size_bytes"])
        or sha256_bytes(raw) != binding["file_sha256"]
    ):
        raise SurfaceError(
            f"finished STEP file identity changed: {binding['member_id']}"
        )
    if binding["one_solid_valid_roundtrip"] is not True:
        raise SurfaceError(
            f"manifest lacks one-solid round-trip evidence: {binding['member_id']}"
        )
    if (
        solids_row["step_sha256"] != binding["file_sha256"]
        or int(solids_row["step_size_bytes"]) != int(binding["size_bytes"])
        or solids_row["member_id"] != binding["member_id"]
        or solids_row["source_shape_fingerprint_sha256"]
        != binding["source_shape_fingerprint_sha256"]
    ):
        raise SurfaceError(
            f"manifest and member-solids binding differ: {binding['member_id']}"
        )
    if (
        _canonical_value_sha256(solids_row["shape_summary"])
        != solids_row["shape_summary_sha256"]
    ):
        raise SurfaceError(
            f"member-solids shape-summary hash is inconsistent: {binding['member_id']}"
        )
    if binding["shape_summary_sha256"] != solids_row["shape_summary_sha256"]:
        raise SurfaceError(
            f"manifest shape-summary identity changed: {binding['member_id']}"
        )
    imported = cq.importers.importStep(str(root / step_path)).solids().vals()
    if len(imported) != 1:
        raise SurfaceError(
            f"{binding['member_id']}: expected one imported STEP solid, got {len(imported)}"
        )
    shape = imported[0]
    summary = solids_row["shape_summary"]
    if (
        not shape.isValid()
        or int(summary["solid_count"]) != 1
        or summary["valid"] is not True
    ):
        raise SurfaceError(
            f"{binding['member_id']}: imported or pinned solid is invalid"
        )
    if abs(float(shape.Volume()) - float(summary["volume_mm3"])) > VOLUME_TOLERANCE_MM3:
        raise SurfaceError(
            f"{binding['member_id']}: STEP volume differs from pinned round-trip summary"
        )
    if (
        max(
            abs(actual - float(expected))
            for actual, expected in zip(
                _bbox_values(shape), summary["bounds_xyz_mm"], strict=True
            )
        )
        > LINEAR_TOLERANCE_MM
    ):
        raise SurfaceError(
            f"{binding['member_id']}: STEP bounds differ from pinned round-trip summary"
        )
    if len(shape.Faces()) != int(summary["face_count"]):
        raise SurfaceError(
            f"{binding['member_id']}: STEP face count differs from pinned summary"
        )
    return shape


def _stock_packet(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    envelopes, envelope_raw = _read_json(root, STOCK_OUTPUT)
    if sha256_bytes(envelope_raw) != EXPECTED_ENVELOPES_SHA256:
        raise SurfaceError(
            "reviewed stock envelopes.json does not match its frozen SHA-256"
        )
    stock_pins, pins_raw = _read_json(root, STOCK_PINS)
    if sha256_bytes(pins_raw) != envelopes.get("source_pins_sha256"):
        raise SurfaceError(
            "reviewed stock source-pins.json hash does not match envelopes.json"
        )
    verify_pin_document(root, stock_pins)
    if (
        envelopes.get("candidate") != EXPECTED_CANDIDATE
        or envelopes.get("geometry_revision_id") != EXPECTED_REVISION
        or envelopes.get("selected_candidate_authority_preserved") != EXPECTED_SELECTED
        or envelopes.get("record_count") != 44
    ):
        raise SurfaceError("reviewed stock envelope candidate/revision/count changed")
    stock_producer_pin = stock_pins["pins"].get("producer:stock_envelopes")
    if stock_producer_pin is None or stock_producer_pin["sha256"] != envelopes.get(
        "producer_sha256"
    ):
        raise SurfaceError(
            "reviewed stock producer hash does not match its source pins"
        )
    if (
        envelopes["geometry_runtime"].get("cadquery") != EXPECTED_CADQUERY
        or envelopes["geometry_runtime"].get("cadquery_ocp") != EXPECTED_OCP_PACKAGE
    ):
        raise SurfaceError(
            "reviewed stock envelope runtime is not the pinned CQ2.8/OCP7.9 runtime"
        )
    manifest_pin = stock_pins["pins"].get("current_manifest")
    solids_pin = stock_pins["pins"].get("member_solids")
    if manifest_pin is None or manifest_pin["sha256"] != EXPECTED_MANIFEST_SHA256:
        raise SurfaceError("source pins do not bind the reviewed manifest04 hash")
    if solids_pin is None:
        raise SurfaceError(
            "source pins do not bind the current member-solids descriptor"
        )
    manifest, manifest_raw = _read_json(root, Path(manifest_pin["path"]))
    if sha256_bytes(manifest_raw) != EXPECTED_MANIFEST_SHA256:
        raise SurfaceError("current manifest04 file differs from its frozen SHA-256")
    if (
        manifest.get("manifest_id") != "current-full-frame-input-manifest-attempt04"
        or manifest.get("candidate") != EXPECTED_CANDIDATE
        or manifest.get("geometry_revision_id") != EXPECTED_REVISION
        or manifest.get("selected_candidate_authority_preserved") != EXPECTED_SELECTED
    ):
        raise SurfaceError("current manifest04 identity changed")
    solids, solids_raw = _read_json(root, Path(solids_pin["path"]))
    if sha256_bytes(solids_raw) != solids_pin["sha256"]:
        raise SurfaceError("current member-solids descriptor hash changed")
    if (
        solids.get("candidate") != EXPECTED_CANDIDATE
        or solids.get("geometry_revision_id") != EXPECTED_REVISION
    ):
        raise SurfaceError("current member-solids candidate/revision changed")
    return (
        envelopes,
        stock_pins,
        {
            "manifest": manifest,
            "manifest_pin": manifest_pin,
            "solids": solids,
            "solids_pin": solids_pin,
        },
    )


def _pin_document(
    root: Path,
    envelopes: dict[str, Any],
    stock_pins: dict[str, Any],
    context: dict[str, Any],
    bindings: list[dict[str, Any]],
) -> dict[str, Any]:
    pins: dict[str, Any] = {}
    _pin(root, pins, "reviewed_stock_envelopes", STOCK_OUTPUT)
    _pin(root, pins, "reviewed_stock_source_pins", STOCK_PINS)
    _pin(
        root,
        pins,
        "reviewed_stock_envelopes_producer",
        Path(stock_pins["pins"]["producer:stock_envelopes"]["path"]),
    )
    _pin(root, pins, "current_manifest04", Path(context["manifest_pin"]["path"]))
    _pin(
        root,
        pins,
        "current_member_solids_descriptor",
        Path(context["solids_pin"]["path"]),
    )
    for key in ("producer:current_manifest", "producer:member_solids"):
        pin = stock_pins["pins"].get(key)
        if pin is not None:
            _pin(root, pins, key.replace(":", "_"), Path(pin["path"]))
    for label, path in (
        ("producer_surfaces", Path(__file__).resolve()),
        ("test_surfaces", Path(__file__).with_name("test_surfaces.py").resolve()),
    ):
        _pin(root, pins, label, path.relative_to(root))
    for binding in sorted(bindings, key=lambda row: row["member_id"]):
        relative = Path(binding["path"])
        _pin(root, pins, f"step:{binding['member_id']}", relative)
    return {
        "schema": "wood_joint_current_finished_feature_register_source_pins/v1",
        "candidate": EXPECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "reviewed_stock_envelopes_sha256": sha256_bytes(
            (root / STOCK_OUTPUT).read_bytes()
        ),
        "reviewed_stock_source_pins_sha256": sha256_bytes(
            (root / STOCK_PINS).read_bytes()
        ),
        "current_manifest04_sha256": EXPECTED_MANIFEST_SHA256,
        "pins": pins,
    }


def _build(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(root).resolve()
    try:
        cadquery_version = cq.__version__
        ocp_package_version = importlib.metadata.version("cadquery-ocp")
    except importlib.metadata.PackageNotFoundError as error:
        raise SurfaceError(
            f"pinned CadQuery/OCP runtime unavailable: {error}"
        ) from error
    if (
        cadquery_version != EXPECTED_CADQUERY
        or ocp_package_version != EXPECTED_OCP_PACKAGE
    ):
        raise SurfaceError(
            f"expected CadQuery/cadquery-ocp {EXPECTED_CADQUERY}/{EXPECTED_OCP_PACKAGE}; "
            f"found {cadquery_version}/{ocp_package_version}"
        )
    envelopes, stock_pins, context = _stock_packet(root)
    envelope_records = {row["member_id"]: row for row in envelopes["records"]}
    manifest_bindings = {
        row["member_id"]: row
        for row in context["manifest"]["finished_member_step_bindings"]
    }
    solid_rows = {row["member_id"]: row for row in context["solids"]["members"]}
    expected_ids = sorted(envelope_records)
    if len(expected_ids) != 44 or len(set(expected_ids)) != 44:
        raise SurfaceError(
            "reviewed stock packet does not contain 44 unique member IDs"
        )
    if not set(expected_ids).issubset(manifest_bindings) or not set(
        expected_ids
    ).issubset(solid_rows):
        raise SurfaceError(
            "manifest04 or member-solids descriptor omits a reviewed stock piece"
        )
    if (
        len(
            [
                row
                for row in context["manifest"]["finished_member_step_bindings"]
                if row["member_id"] in envelope_records
            ]
        )
        != 44
    ):
        raise SurfaceError(
            "manifest04 does not supply exactly 44 corresponding finished STEP bindings"
        )

    records = []
    all_bindings = []
    kind_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    for member_id in expected_ids:
        envelope_row = envelope_records[member_id]
        binding = manifest_bindings[member_id]
        solid_row = solid_rows[member_id]
        if (
            binding["path"] != envelope_row["current_finished_step_path"]
            or binding["file_sha256"] != envelope_row["current_finished_step_sha256"]
            or int(binding["size_bytes"])
            != int(envelope_row["current_finished_step_size_bytes"])
            or binding["member_id"] != member_id
        ):
            raise SurfaceError(
                f"reviewed stock and manifest04 finished STEP binding differ: {member_id}"
            )
        bundle_root = Path(context["solids_pin"]["path"]).parent.parent
        try:
            relative_step = Path(binding["path"]).relative_to(bundle_root).as_posix()
        except ValueError as error:
            raise SurfaceError(
                f"manifest04 STEP path is outside the pinned bundle: {member_id}"
            ) from error
        if relative_step != solid_row["step_file"]:
            raise SurfaceError(
                f"manifest04 and member-solids STEP path differ: {member_id}"
            )
        if (
            solid_row["source_shape_fingerprint_sha256"]
            != envelope_row["source_shape_fingerprint_sha256"]
        ):
            raise SurfaceError(
                f"reviewed stock and member-solids shape fingerprint differ: {member_id}"
            )
        shape = _load_exact_solid(root, binding, solid_row)
        frame = _build_stock_frame(envelope_row)
        features = features_for_shape(member_id, shape, frame)
        if len(features) != len(shape.Faces()):
            raise SurfaceError(
                f"{member_id}: not all saved STEP faces received a feature record"
            )
        for feature in features:
            kind_counts[feature["surface_kind"]] += 1
            class_counts[feature["classification"]] += 1
        all_bindings.append(binding)
        records.append(
            {
                "member_id": member_id,
                "step_binding": {
                    "path": binding["path"],
                    "file_sha256": binding["file_sha256"],
                    "size_bytes": int(binding["size_bytes"]),
                    "source_shape_fingerprint_sha256": solid_row[
                        "source_shape_fingerprint_sha256"
                    ],
                    "shape_summary_sha256": solid_row["shape_summary_sha256"],
                    "solid_count": len(shape.Solids()),
                    "face_count": len(shape.Faces()),
                    "valid": bool(shape.isValid()),
                    "manifest_roundtrip_valid": bool(
                        binding["one_solid_valid_roundtrip"]
                    ),
                },
                "stock_frame": frame,
                "features": features,
            }
        )
    if len(records) != 44 or sum(len(row["features"]) for row in records) != sum(
        row["step_binding"]["face_count"] for row in records
    ):
        raise SurfaceError(
            "record/feature count does not cover all 44 finished STEP solids"
        )
    if [row["member_id"] for row in records] != sorted(expected_ids):
        raise SurfaceError("feature register records are not sorted by member ID")

    pins = _pin_document(root, envelopes, stock_pins, context, all_bindings)
    pins_sha = sha256_bytes(canonical_bytes(pins))
    source_pin_sha = sha256_bytes((root / STOCK_PINS).read_bytes())
    stock_env_sha = sha256_bytes((root / STOCK_OUTPUT).read_bytes())
    manifest_sha = sha256_bytes(
        (root / Path(context["manifest_pin"]["path"])).read_bytes()
    )
    producer_sha = sha256_bytes(Path(__file__).read_bytes())
    test_sha = sha256_bytes(Path(__file__).with_name("test_surfaces.py").read_bytes())
    unsupported = [
        {
            "feature_id": feature["feature_id"],
            "surface_kind": feature["surface_kind"],
            "classification": feature["classification"],
        }
        for record in records
        for feature in record["features"]
        if feature["classification"] == "unsupported_descriptive_only"
    ]
    ambiguous_cylinders = [
        feature["feature_id"]
        for record in records
        for feature in record["features"]
        if feature["surface_kind"] == "CYLINDER"
        and feature["cylinder"]["material_side_geometry"] == "ambiguous"
    ]
    report = {
        "schema": "wood_joint_current_finished_feature_register/v1",
        "candidate": EXPECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "source_manifest_id": context["manifest"]["manifest_id"],
        "source_manifest_sha256": manifest_sha,
        "reviewed_stock_envelopes_sha256": stock_env_sha,
        "reviewed_stock_source_pins_sha256": source_pin_sha,
        "source_pins_sha256": pins_sha,
        "producer_sha256": producer_sha,
        "test_sha256": test_sha,
        "geometry_runtime": {
            "cadquery": cadquery_version,
            "cadquery_ocp_module": OCP.__version__,
            "cadquery_ocp_package": ocp_package_version,
            "linear_tolerance_mm": LINEAR_TOLERANCE_MM,
            "volume_tolerance_mm3": VOLUME_TOLERANCE_MM3,
            "coordinate_roundtrip_tolerance_mm": ROUNDTRIP_TOLERANCE_MM,
        },
        "record_count": len(records),
        "finished_step_binding_count": len(all_bindings),
        "finished_face_count": sum(len(row["features"]) for row in records),
        "surface_kind_counts": dict(sorted(kind_counts.items())),
        "classification_counts": dict(sorted(class_counts.items())),
        "unsupported_faces": unsupported,
        "ambiguous_cylinder_material_side_feature_ids": ambiguous_cylinders,
        "claims": {
            "status": "descriptive_exact_finished_step_face_register",
            "face_index_rule": "one-based order returned by pinned CadQuery import of each exact STEP solid",
            "stock_frame_status": "proposed analytical frame; not a delivered-stock datum",
            "surface_acceptance_or_approved_cut_inferred": False,
            "drill_bit_pilot_or_purchase_instruction": False,
            "resistance_or_joint_capacity_claim": False,
            "native_solver_executed": False,
            "geometry_regenerated_or_changed": False,
        },
        "records": records,
    }
    return report, pins


def build_report(root: Path = ROOT) -> dict[str, Any]:
    """Build the deterministic register from the pinned, exact STEP bindings."""
    return _build(root)[0]


def _write_exclusive(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as error:
        raise SurfaceError(f"refusing to overwrite existing output: {path}") from error


def _verify_outputs(root: Path) -> dict[str, Any]:
    report, pins = _build(root)
    stored_pins = json.loads(PINS_OUTPUT.read_text(encoding="utf-8"))
    verify_pin_document(root, stored_pins)
    verify_canonical_file(PINS_OUTPUT, stored_pins, "source-pins.json")
    if canonical_bytes(stored_pins) != canonical_bytes(pins):
        raise SurfaceError(
            "source-pins.json does not match the current exact source inventory"
        )
    verify_canonical_file(OUTPUT, report, "surfaces.json")
    raw = canonical_bytes(report)
    return {
        "status": "verified",
        "record_count": report["record_count"],
        "finished_step_binding_count": report["finished_step_binding_count"],
        "finished_face_count": report["finished_face_count"],
        "surface_kind_counts": report["surface_kind_counts"],
        "unsupported_face_count": len(report["unsupported_faces"]),
        "ambiguous_cylinder_count": len(
            report["ambiguous_cylinder_material_side_feature_ids"]
        ),
        "surfaces_sha256": sha256_bytes(raw),
        "source_pins_sha256": sha256_bytes(canonical_bytes(pins)),
        "producer_sha256": report["producer_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write", action="store_true", help="write ignored raw JSON outputs once"
    )
    mode.add_argument(
        "--verify",
        action="store_true",
        help="replay exact input pins and canonical outputs",
    )
    args = parser.parse_args(argv)
    if args.write:
        if OUTPUT.exists() or PINS_OUTPUT.exists():
            raise SurfaceError(
                "raw outputs already exist; remove only these ignored outputs before --write"
            )
        report, pins = _build(ROOT)
        _write_exclusive(OUTPUT, canonical_bytes(report))
        try:
            _write_exclusive(PINS_OUTPUT, canonical_bytes(pins))
        except Exception:
            OUTPUT.unlink(missing_ok=True)
            raise
        result = {
            "status": "written",
            "record_count": report["record_count"],
            "finished_step_binding_count": report["finished_step_binding_count"],
            "finished_face_count": report["finished_face_count"],
            "surface_kind_counts": report["surface_kind_counts"],
            "unsupported_face_count": len(report["unsupported_faces"]),
            "ambiguous_cylinder_count": len(
                report["ambiguous_cylinder_material_side_feature_ids"]
            ),
            "surfaces_sha256": sha256_bytes(canonical_bytes(report)),
            "source_pins_sha256": sha256_bytes(canonical_bytes(pins)),
            "producer_sha256": report["producer_sha256"],
        }
    else:
        result = _verify_outputs(ROOT)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
