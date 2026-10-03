"""Read-only exact planar section properties for a saved CadQuery solid.

This module extracts a planar intersection and returns its area properties in
an explicit grain/u/v frame. It does not edit, heal, rebuild, or accept the
source solid.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterable, Sequence
from importlib.metadata import PackageNotFoundError, version
from typing import Any


class SectionGeometryError(ValueError):
    """The requested solid section is invalid, empty, or unsupported."""


_FRAME_TOL = 1.0e-8
_NORMAL_TOL = 1.0e-8


def _finite_vector(value: Sequence[float], name: str) -> tuple[float, float, float]:
    try:
        if len(value) != 3:
            raise SectionGeometryError(f"{name} must have exactly three coordinates")
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as exc:
        if isinstance(exc, SectionGeometryError):
            raise
        raise SectionGeometryError(f"{name} must be a finite 3-vector") from exc
    if not all(math.isfinite(component) for component in result):
        raise SectionGeometryError(f"{name} must be a finite 3-vector")
    return result  # type: ignore[return-value]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return math.fsum(a_i * b_i for a_i, b_i in zip(a, b, strict=True))


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(value: Sequence[float]) -> float:
    return math.sqrt(_dot(value, value))


def _validate_frame(
    origin: Sequence[float],
    grain: Sequence[float],
    u: Sequence[float],
    v: Sequence[float],
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    # Check the supplied basis before any kernel object can normalize a vector.
    p = _finite_vector(origin, "origin")
    g = _finite_vector(grain, "grain")
    e_u = _finite_vector(u, "u")
    e_v = _finite_vector(v, "v")
    basis = (("grain", g), ("u", e_u), ("v", e_v))
    for name, axis in basis:
        if abs(_norm(axis) - 1.0) > _FRAME_TOL:
            raise SectionGeometryError(f"{name} must be a unit vector")
    if any(abs(_dot(left, right)) > _FRAME_TOL for (_, left), (_, right) in itertools.combinations(basis, 2)):
        raise SectionGeometryError("grain, u, and v must be mutually orthogonal")
    handedness = _dot(_cross(g, e_u), e_v)
    if abs(handedness - 1.0) > _FRAME_TOL:
        raise SectionGeometryError("(grain, u, v) must be right-handed")
    g_length = _norm(g)
    normalized_grain = tuple(component / g_length for component in g)
    u_projection = _dot(e_u, normalized_grain)
    projected_u = tuple(e_u[i] - u_projection * normalized_grain[i] for i in range(3))
    u_length = _norm(projected_u)
    normalized_u = tuple(component / u_length for component in projected_u)
    normalized_v = _cross(normalized_grain, normalized_u)
    return p, normalized_grain, normalized_u, normalized_v


def _point_xyz(point: Any) -> tuple[float, float, float]:
    return float(point.X()), float(point.Y()), float(point.Z())


def _kernel_versions(cq: Any, ocp: Any) -> dict[str, str]:
    try:
        ocp_version = version("cadquery-ocp")
    except PackageNotFoundError:
        ocp_version = str(getattr(ocp, "__version__", "unknown"))
    return {"cadquery": str(cq.__version__), "ocp": ocp_version}


def _unique_shapes(shapes: Iterable[Any]) -> list[Any]:
    unique: list[Any] = []
    for shape in shapes:
        if not any(shape.wrapped.IsSame(other.wrapped) for other in unique):
            unique.append(shape)
    return unique


def _projection_bounds(solid: Any, plane: Any, origin: Sequence[float], margin: float) -> tuple[float, float, float, float]:
    bounds = solid.BoundingBox()
    corners = itertools.product(
        (bounds.xmin, bounds.xmax),
        (bounds.ymin, bounds.ymax),
        (bounds.zmin, bounds.zmax),
    )
    axes = plane.Position()
    plane_u = _point_xyz(axes.XDirection())
    plane_v = _point_xyz(axes.YDirection())
    relative_points = [tuple(point[i] - origin[i] for i in range(3)) for point in corners]
    u_values = [_dot(point, plane_u) for point in relative_points]
    v_values = [_dot(point, plane_v) for point in relative_points]
    return (
        min(u_values) - margin,
        max(u_values) + margin,
        min(v_values) - margin,
        max(v_values) + margin,
    )


def _face_properties(faces: Sequence[Any], reference: Sequence[float]) -> tuple[float, tuple[float, float, float], Any]:
    from OCP.BRepGProp import BRepGProp
    from OCP.gp import gp_Pnt
    from OCP.GProp import GProp_GProps

    props = GProp_GProps(gp_Pnt(*reference))
    for face in faces:
        # Exact surface geometry is used; triangulation is explicitly disabled.
        face_props = GProp_GProps(gp_Pnt(*reference))
        BRepGProp.SurfaceProperties_s(face.wrapped, face_props, False, False)
        props.Add(face_props)
    area = float(props.Mass())
    center = _point_xyz(props.CentreOfMass())
    inertia = props.MatrixOfInertia()
    return area, center, inertia


def _covariance_from_inertia(
    inertia: Any,
    u: Sequence[float],
    v: Sequence[float],
) -> dict[str, float]:
    matrix = tuple(tuple(float(inertia.Value(row, col)) for col in (1, 2, 3)) for row in (1, 2, 3))

    def quadratic(left: Sequence[float], right: Sequence[float]) -> float:
        return math.fsum(
            left[i] * matrix[i][j] * right[j]
            for i in range(3)
            for j in range(3)
        )

    # OCCT returns a central inertia tensor whose off-diagonal entries have
    # the conventional inertia sign: I_uv = -integral(u * v). For a planar
    # region, C_uu = v.T I v, C_vv = u.T I u, and C_uv = -u.T I v.
    covariance = {
        "uu": quadratic(v, v),
        "uv": -quadratic(u, v),
        "vv": quadratic(u, u),
    }
    if not all(math.isfinite(value) for value in covariance.values()):
        raise SectionGeometryError("OCC returned non-finite section covariance integrals")
    return covariance


def _relative_uv(
    center: Sequence[float], origin: Sequence[float], u: Sequence[float], v: Sequence[float]
) -> list[float]:
    offset = tuple(center[i] - origin[i] for i in range(3))
    return [_dot(offset, u), _dot(offset, v)]


def _face_components(faces: Sequence[Any], tolerance_mm: float) -> list[list[Any]]:
    """Group faces by shared positive-length topological edges."""
    parents = list(range(len(faces)))

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def join(left: int, right: int) -> None:
        left_root = root(left)
        right_root = root(right)
        if left_root != right_root:
            parents[right_root] = left_root

    face_edges: list[list[Any]] = []
    for face in faces:
        edges = _unique_shapes(face.Edges())
        for edge in edges:
            edge_length = float(edge.Length())
            if not math.isfinite(edge_length):
                raise SectionGeometryError("OCC returned a non-finite section boundary edge")
        face_edges.append(edges)

    for left in range(len(faces)):
        for right in range(left + 1, len(faces)):
            if any(
                first.wrapped.IsSame(second.wrapped)
                and float(first.Length()) > max(0.0, tolerance_mm * 1.0e-6)
                for first in face_edges[left]
                for second in face_edges[right]
            ):
                join(left, right)

    groups: dict[int, list[Any]] = {}
    for index, face in enumerate(faces):
        groups.setdefault(root(index), []).append(face)
    return list(groups.values())


def _reject_unattached_lower_dimensional_topology(section: Any, faces: Sequence[Any]) -> None:
    boundary_edges = _unique_shapes(edge for face in faces for edge in face.Edges())
    boundary_vertices = _unique_shapes(vertex for face in faces for vertex in face.Vertices())
    for edge in _unique_shapes(section.Edges()):
        if not any(edge.wrapped.IsSame(boundary.wrapped) for boundary in boundary_edges):
            raise SectionGeometryError("section includes an unsupported edge outside its planar faces")
    for vertex in _unique_shapes(section.Vertices()):
        if not any(vertex.wrapped.IsSame(boundary.wrapped) for boundary in boundary_vertices):
            raise SectionGeometryError("section includes an unsupported vertex outside its planar faces")


def section_properties(
    shape: Any,
    origin: Sequence[float],
    grain: Sequence[float],
    u: Sequence[float],
    v: Sequence[float],
    *,
    tolerance_mm: float = 1.0e-5,
) -> dict[str, Any]:
    """Return area and central moments from exact BRep geometry for the section.

    ``origin`` is a point on the requested plane. ``(grain, u, v)`` must be a
    finite, unit, orthogonal, right-handed frame before this function makes any
    kernel direction from it. ``grain`` is the plane normal; ``u`` and ``v``
    are the reporting axes. Boundary planes are queried by the same one-sided
    solid/plane common operation as interior planes.

    Disjoint planar regions remain separate in ``components``. They are never
    treated as one connected material region by this geometry helper.
    """
    p, g, e_u, e_v = _validate_frame(origin, grain, u, v)
    if not math.isfinite(tolerance_mm) or tolerance_mm <= 0.0:
        raise SectionGeometryError("tolerance_mm must be finite and positive")

    try:
        import cadquery as cq
        import OCP
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
        from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
        from OCP.BRepCheck import BRepCheck_Analyzer
        from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
    except ImportError as exc:
        raise SectionGeometryError(f"CadQuery/OCP are required for section extraction: {exc}") from exc

    if not isinstance(shape, cq.Shape):
        raise SectionGeometryError("shape must be a CadQuery shape containing one solid")
    solids = shape.Solids()
    if len(solids) != 1:
        raise SectionGeometryError("shape must contain exactly one solid")
    solid = solids[0]
    if (
        len(shape.Faces()) != len(solid.Faces())
        or len(shape.Edges()) != len(solid.Edges())
        or len(shape.Vertices()) != len(solid.Vertices())
    ):
        raise SectionGeometryError("shape must not include geometry outside its one solid")
    if not shape.isValid() or not BRepCheck_Analyzer(solid.wrapped).IsValid():
        raise SectionGeometryError("input CadQuery solid is invalid")

    try:
        plane = gp_Pln(gp_Pnt(*p), gp_Dir(*g))
        bbox = solid.BoundingBox()
        characteristic_length = max(bbox.xlen, bbox.ylen, bbox.zlen)
        if not math.isfinite(characteristic_length) or characteristic_length <= 0.0:
            raise SectionGeometryError("input solid has an empty or invalid bounding box")
        cutter_margin = max(10.0 * tolerance_mm, characteristic_length * 1.0e-6, 1.0e-6)
        u_min, u_max, v_min, v_max = _projection_bounds(solid, plane, p, cutter_margin)
        maker = BRepBuilderAPI_MakeFace(plane, u_min, u_max, v_min, v_max)
        if not maker.IsDone():
            raise SectionGeometryError("OCC could not construct the bounded section plane")
        cutter = cq.Face(maker.Face())
        operation = BRepAlgoAPI_Common(solid.wrapped, cutter.wrapped)
        operation.Build()
        if not operation.IsDone():
            raise SectionGeometryError("OCC planar intersection did not complete")
        section = cq.Shape(operation.Shape())
    except SectionGeometryError:
        raise
    except Exception as exc:
        raise SectionGeometryError(f"OCC planar intersection failed: {exc}") from exc

    if section.isNull() or not BRepCheck_Analyzer(section.wrapped).IsValid():
        raise SectionGeometryError("OCC returned an invalid section topology")
    if section.Solids():
        raise SectionGeometryError("OCC returned solid volume for a planar section")

    all_faces = section.Faces()
    if not all_faces:
        raise SectionGeometryError("requested plane is outside the solid or has no positive-area section")

    unique_faces = _unique_shapes(all_faces)
    for face in unique_faces:
        if face.geomType() != "PLANE":
            raise SectionGeometryError(f"unsupported nonplanar section face: {face.geomType()}")
        normal = _finite_vector(face.normalAt().toTuple(), "OCC section face normal")
        center = _finite_vector(face.Center().toTuple(), "OCC section face center")
        if abs(abs(_dot(normal, g)) - 1.0) > _NORMAL_TOL:
            raise SectionGeometryError("OCC returned a section face with a mismatched plane normal")
        if abs(_dot(tuple(center[i] - p[i] for i in range(3)), g)) > tolerance_mm:
            raise SectionGeometryError("OCC returned a section face outside the requested plane")
        for vertex in face.Vertices():
            point = _finite_vector(vertex.toTuple(), "OCC section face vertex")
            if abs(_dot(tuple(point[i] - p[i] for i in range(3)), g)) > tolerance_mm:
                raise SectionGeometryError("OCC returned a section boundary outside the requested plane")
        if not face.Wires():
            raise SectionGeometryError("OCC returned a section face without boundary wires")
    _reject_unattached_lower_dimensional_topology(section, unique_faces)

    try:
        groups = _face_components(unique_faces, tolerance_mm)
        # The projected bounding-box center is close to the section centroid and
        # lies on the plane, improving OCCT's inertia accumulation accuracy.
        box_center = (bbox.xmin + bbox.xlen / 2.0, bbox.ymin + bbox.ylen / 2.0, bbox.zmin + bbox.zlen / 2.0)
        distance_to_plane = _dot(tuple(box_center[i] - p[i] for i in range(3)), g)
        reference = tuple(box_center[i] - distance_to_plane * g[i] for i in range(3))

        components: list[dict[str, Any]] = []
        for component_faces in groups:
            area, center, inertia = _face_properties(component_faces, reference)
            if not math.isfinite(area) or area <= 0.0:
                raise SectionGeometryError("OCC returned a non-positive component area")
            components.append(
                {
                    "area_mm2": area,
                    "centroid_global_xyz_mm": list(center),
                    "centroid_relative_uv_mm": _relative_uv(center, p, e_u, e_v),
                    "area_covariance_integrals_mm4": _covariance_from_inertia(inertia, e_u, e_v),
                    "wire_count": sum(len(face.Wires()) for face in component_faces),
                }
            )
        components.sort(
            key=lambda item: (
                item["centroid_relative_uv_mm"][0],
                item["centroid_relative_uv_mm"][1],
                item["area_mm2"],
            )
        )
        area, center, inertia = _face_properties(unique_faces, reference)
        if not math.isfinite(area) or area <= 0.0:
            raise SectionGeometryError("OCC returned a non-positive total section area")
        component_area = math.fsum(item["area_mm2"] for item in components)
        area_scale = max(area, component_area, 1.0)
        if abs(area - component_area) > max(tolerance_mm * tolerance_mm, area_scale * 1.0e-10):
            raise SectionGeometryError("component area sum disagrees with total OCC area")
        component_count = len(components)
        if component_count == 0:
            raise SectionGeometryError("OCC found no supported positive-area section components")
        return {
            "area_mm2": area,
            "centroid_global_xyz_mm": list(center),
            "centroid_relative_uv_mm": _relative_uv(center, p, e_u, e_v),
            "area_covariance_integrals_mm4": _covariance_from_inertia(inertia, e_u, e_v),
            "component_count": component_count,
            "disconnected_ligaments": component_count > 1,
            "components": components,
            "kernel": _kernel_versions(cq, OCP),
        }
    except SectionGeometryError:
        raise
    except Exception as exc:
        raise SectionGeometryError(f"OCC exact section properties failed: {exc}") from exc


__all__ = ["SectionGeometryError", "section_properties"]
