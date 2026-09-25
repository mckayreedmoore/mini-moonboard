"""Exact transverse sweeps for source-verified circular hardware envelopes.

These helpers recognize only single-solid cylinders and annular cylinders from
their BRep faces and symmetric difference against matching analytic geometry.
They return CAD-envelope occupancy for a straight translation, not fit or
clearance claims about delivered hardware.
"""

from __future__ import annotations

import math
from typing import Any

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

_AXIS_PARALLEL_TOLERANCE = 1e-9
_AXIS_LINE_TOLERANCE_MM = 1e-7
_VOLUME_ABSOLUTE_TOLERANCE_MM3 = 1e-5


def _unit(vector: cq.Vector, context: str) -> cq.Vector:
    if not all(math.isfinite(value) for value in vector.toTuple()):
        raise ValueError(f"{context} must be finite")
    if vector.Length <= 1e-12:
        raise ValueError(f"{context} must be nonzero")
    return vector.normalized()


def _projected_extrema(shape: cq.Shape, axis: cq.Vector) -> tuple[float, float] | None:
    values = [vertex.Center().dot(axis) for vertex in shape.Vertices()]
    if not values or not all(math.isfinite(value) for value in values):
        return None
    return min(values), max(values)


def _volume_tolerance(volume: float) -> float:
    return max(_VOLUME_ABSOLUTE_TOLERANCE_MM3, abs(volume) * 1e-8)


def _verified_round_source(
    shape: cq.Shape,
) -> tuple[cq.Vector, cq.Vector, float, float, float] | None:
    """Return source start, axis, length, outer radius, inner radius if exact."""
    if not shape.isValid() or len(shape.Solids()) != 1:
        return None
    faces = shape.Faces()
    cylindrical_faces = [face for face in faces if face.geomType() == "CYLINDER"]
    planar_faces = [face for face in faces if face.geomType() == "PLANE"]
    if len(cylindrical_faces) not in {1, 2} or len(planar_faces) != 2:
        return None

    cylinder_data: list[tuple[float, cq.Vector, cq.Vector]] = []
    try:
        for face in cylindrical_faces:
            cylinder = BRepAdaptor_Surface(face.wrapped, True).Cylinder()
            axis = cylinder.Axis()
            direction = _unit(
                cq.Vector(
                    axis.Direction().X(),
                    axis.Direction().Y(),
                    axis.Direction().Z(),
                ),
                "source cylinder axis",
            )
            location = cq.Vector(
                axis.Location().X(), axis.Location().Y(), axis.Location().Z()
            )
            radius = float(cylinder.Radius())
            if not math.isfinite(radius) or radius <= 0:
                return None
            cylinder_data.append((radius, location, direction))
        axis_direction = cylinder_data[0][2]
        for _radius, location, direction in cylinder_data:
            if abs(direction.dot(axis_direction)) < 1.0 - _AXIS_PARALLEL_TOLERANCE:
                return None
            offset = location - cylinder_data[0][1]
            if (
                offset - axis_direction * offset.dot(axis_direction)
            ).Length > _AXIS_LINE_TOLERANCE_MM:
                return None
        for face in planar_faces:
            normal = _unit(face.normalAt(), "source end-face normal")
            if abs(normal.dot(axis_direction)) < 1.0 - 1e-8:
                return None
    except (RuntimeError, ValueError, OverflowError):
        return None

    radii = sorted(radius for radius, _location, _direction in cylinder_data)
    if len(radii) == 2 and radii[1] - radii[0] <= 1e-9:
        return None
    inner_radius = radii[0] if len(radii) == 2 else 0.0
    outer_radius = radii[-1]
    extrema = _projected_extrema(shape, axis_direction)
    if extrema is None:
        return None
    low, high = extrema
    length = high - low
    if not math.isfinite(length) or length <= 1e-9:
        return None
    axis_point = cylinder_data[0][1]
    start = axis_point + axis_direction * (low - axis_point.dot(axis_direction))

    expected_volume = math.pi * (outer_radius**2 - inner_radius**2) * length
    try:
        matching_outer = cq.Solid.makeCylinder(outer_radius, length, start, axis_direction)
        matching = matching_outer
        if inner_radius > 0:
            matching_inner = cq.Solid.makeCylinder(
                inner_radius, length, start, axis_direction
            )
            matching = matching_outer.cut(matching_inner)
        source_volume = float(shape.Volume())
        matching_volume = float(matching.Volume())
        common_volume = float(shape.intersect(matching).Volume())
    except (RuntimeError, ValueError, OverflowError):
        return None
    tolerance = _volume_tolerance(expected_volume)
    if (
        abs(source_volume - expected_volume) > tolerance
        or abs(matching_volume - expected_volume) > tolerance
    ):
        return None
    symmetric_difference = max(
        0.0, source_volume + matching_volume - 2.0 * common_volume
    )
    if symmetric_difference > tolerance:
        return None
    return start, axis_direction, length, outer_radius, inner_radius


def _capsule_volume(radius: float, length: float, height: float) -> float:
    return (math.pi * radius**2 + 2.0 * radius * length) * height


def _circle_intersection_area(radius: float, center_distance: float) -> float:
    if center_distance >= 2.0 * radius:
        return 0.0
    half_distance = center_distance / 2.0
    return (
        2.0 * radius**2 * math.acos(center_distance / (2.0 * radius))
        - half_distance * math.sqrt(4.0 * radius**2 - center_distance**2)
    )


def exact_transverse_round_component_sweep(
    shape: cq.Shape, displacement_xyz_mm: Any
) -> tuple[cq.Shape | None, str | None]:
    """Return an exact straight transverse sweep of a verified round source BRep.

    The source must be a single-solid cylinder or annular cylinder. Translation
    must be perpendicular to its axis. A solid cylinder sweeps to a capsule
    cross-section extruded through its axial height. For an annulus, the shared
    intersection of the start/end inner bores is removed while it exists; when
    travel is at least twice the inner radius, that intersection is empty and
    the outer capsule is filled by the union of translated material. Unsupported
    or nonperpendicular cases return ``(None, None)`` so callers can keep their
    declared conservative fallback.
    """
    displacement = cq.Vector(displacement_xyz_mm)
    if not all(math.isfinite(value) for value in displacement.toTuple()):
        raise ValueError("component translation must be finite")
    if displacement.Length <= 1e-12:
        return None, None
    verified = _verified_round_source(shape)
    if verified is None:
        return None, None
    start, axis, height, outer_radius, inner_radius = verified
    travel_length = displacement.Length
    travel_direction = displacement.normalized()
    if abs(axis.dot(travel_direction)) > _AXIS_PARALLEL_TOLERANCE:
        return None, None

    try:
        first_outer = cq.Solid.makeCylinder(outer_radius, height, start, axis)
        second_outer = cq.Solid.makeCylinder(
            outer_radius, height, start + displacement, axis
        )
        connector_plane = cq.Plane(
            origin=start, xDir=travel_direction, normal=axis
        )
        connector = (
            cq.Workplane(connector_plane)
            .box(travel_length, 2.0 * outer_radius, height, centered=(False, True, False))
            .val()
        )
        outer_capsule = connector.fuse(first_outer, second_outer)
        if not outer_capsule.isValid() or len(outer_capsule.Solids()) != 1:
            return None, None

        capsule_volume = _capsule_volume(outer_radius, travel_length, height)
        expected_volume = capsule_volume
        result = outer_capsule
        if inner_radius > 0:
            intersection_area = _circle_intersection_area(inner_radius, travel_length)
            expected_volume -= intersection_area * height
            if intersection_area > 0:
                first_inner = cq.Solid.makeCylinder(inner_radius, height, start, axis)
                second_inner = cq.Solid.makeCylinder(
                    inner_radius, height, start + displacement, axis
                )
                shared_bore = first_inner.intersect(second_inner)
                if (
                    not shared_bore.isValid()
                    or len(shared_bore.Solids()) != 1
                    or abs(
                        float(shared_bore.Volume())
                        - intersection_area * height
                    )
                    > _volume_tolerance(intersection_area * height)
                ):
                    return None, None
                result = outer_capsule.cut(shared_bore)
        if not result.isValid() or len(result.Solids()) != 1:
            return None, None
        if abs(float(result.Volume()) - expected_volume) > _volume_tolerance(
            expected_volume
        ):
            return None, None
    except (RuntimeError, ValueError, OverflowError):
        return None, None

    method = (
        "exact_source_brep_transverse_annular_cylinder_sweep"
        if inner_radius > 0
        else "exact_source_brep_transverse_cylinder_sweep"
    )
    return result, method
