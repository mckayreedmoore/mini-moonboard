"""Capacity-independent unit-wrench witnesses for the WJ-12 backer joints.

This module consumes an already composed WJ-12 geometry object. It does not
materialize family geometry or assign real backer demands. Two ideal point
fasteners provide a statics baseline; a second witness uses small finite
contact patches only after Boolean containment checks against both finished
members. Neither witness predicts load sharing, resistance, pressure,
stiffness, preload, installation, or release.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import cadquery as cq
from OCP.BRepTools import BRepTools_WireExplorer

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint

SCHEMA = "wood_joint_wj12_backer_statics/v1"
ROOT = Path(__file__).resolve().parents[1]
TRIAL_ID = "wj12-compact-outer-right-rail-center-x190-v1"
GEOMETRY_TOLERANCE_MM = 1.0e-5
STATICS_TOLERANCE = 1.0e-8
PATCH_VOLUME_TOLERANCE_MM3 = 1.0e-6

# These are finite geometric witness dimensions, not selected contact design
# dimensions. Every patch is checked in both actual finished members.
ANNULUS_RADIAL_GAP_MM = 0.5
ANNULUS_RADIAL_WIDTH_MM = 2.0
EDGE_PATCH_RADIUS_MM = 2.0
PATCH_CHECK_DEPTH_MM = 0.25

FAMILY_PRODUCER_PATHS = {
    "wj03_compact_outer": "scripts/wood_joint_wj03_compact_outer_access.py",
    "right_rail_integration": "scripts/wood_joint_right_rail_integration.py",
    "wj04_upper_g7": "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
    "wj06_outer_pair": "scripts/wood_joint_wj06_outer_pair_probe.py",
    "center_x190": "scripts/wood_joint_wj05_center_post_x190_probe.py",
}


Vector = tuple[float, float, float]


def _v(value: Sequence[float], label: str) -> Vector:
    result = tuple(float(component) for component in value)
    if len(result) != 3 or not all(math.isfinite(item) for item in result):
        raise ValueError(f"{label} must be a finite three-vector")
    return result  # type: ignore[return-value]


def _add(first: Vector, second: Vector) -> Vector:
    return tuple(a + b for a, b in zip(first, second, strict=True))  # type: ignore[return-value]


def _sub(first: Vector, second: Vector) -> Vector:
    return tuple(a - b for a, b in zip(first, second, strict=True))  # type: ignore[return-value]


def _scale(value: float, vector: Vector) -> Vector:
    return tuple(value * item for item in vector)  # type: ignore[return-value]


def _dot(first: Vector, second: Vector) -> float:
    return math.fsum(a * b for a, b in zip(first, second, strict=True))


def _cross(first: Vector, second: Vector) -> Vector:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _norm(vector: Vector) -> float:
    return math.sqrt(_dot(vector, vector))


def _unit(vector: Vector, label: str) -> Vector:
    length = _norm(vector)
    if length <= GEOMETRY_TOLERANCE_MM:
        raise ValueError(f"{label} has zero length")
    return _scale(1.0 / length, vector)


def _vector_tuple(vector: cq.Vector) -> Vector:
    return _v(vector.toTuple(), "CAD vector")


def _shape_hash(shape: cq.Shape) -> str:
    if not isinstance(shape, cq.Shape) or not shape.isValid() or not shape.Solids():
        raise ValueError("backer statics requires valid, nonempty solid geometry")
    return _source_shape_fingerprint(shape)


def _ordered_outer_vertices(face: cq.Face, label: str) -> tuple[Vector, ...]:
    """Read a closed straight-edged outer wire in topological connection order."""
    explorer = BRepTools_WireExplorer(face.outerWire().wrapped)
    starts = []
    edges = []
    while explorer.More():
        start = _vector_tuple(cq.Vertex(explorer.CurrentVertex()).Center())
        edge = cq.Edge(explorer.Current())
        if edge.geomType() != "LINE":
            raise ValueError(f"{label} outer boundary contains a curved edge")
        endpoints = tuple(_vector_tuple(vertex.Center()) for vertex in edge.Vertices())
        if len(endpoints) != 2:
            raise ValueError(f"{label} outer boundary edge has no unique endpoints")
        starts.append(start)
        edges.append(endpoints)
        explorer.Next()
    if len(starts) < 3 or len(starts) != len(edges):
        raise ValueError(f"{label} outer boundary has fewer than three ordered edges")
    for index, endpoints in enumerate(edges):
        current = starts[index]
        following = starts[(index + 1) % len(starts)]
        if not (
            _norm(_sub(current, endpoints[0])) <= GEOMETRY_TOLERANCE_MM
            or _norm(_sub(current, endpoints[1])) <= GEOMETRY_TOLERANCE_MM
        ):
            raise ValueError(f"{label} outer wire traversal is not contiguous")
        if not (
            _norm(_sub(following, endpoints[0])) <= GEOMETRY_TOLERANCE_MM
            or _norm(_sub(following, endpoints[1])) <= GEOMETRY_TOLERANCE_MM
        ):
            raise ValueError(f"{label} outer wire traversal is not a closed polygon")
    return tuple(starts)


def _cylindrical_axis(shape: cq.Shape, label: str) -> dict[str, Any]:
    """Read one unstepped cylindrical centerline from an actual BRep shape."""
    rows = []
    for face in shape.Faces():
        if face.geomType() != "CYLINDER":
            continue
        cylinder = face._geomAdaptor().Cylinder()
        axis = cylinder.Axis()
        location = axis.Location()
        direction = axis.Direction()
        rows.append(
            (
                float(cylinder.Radius()),
                _v((location.X(), location.Y(), location.Z()), f"{label} cylinder location"),
                _unit(
                    _v((direction.X(), direction.Y(), direction.Z()), f"{label} cylinder direction"),
                    f"{label} cylinder direction",
                ),
            )
        )
    if not rows:
        raise ValueError(f"{label} has no cylindrical face from which to derive its axis")
    reference_point = rows[0][1]
    reference_direction = rows[0][2]
    if any(
        abs(abs(_dot(reference_direction, direction)) - 1.0) > 1.0e-7
        or _norm(_cross(_sub(point, reference_point), reference_direction)) > 1.0e-5
        for _, point, direction in rows[1:]
    ):
        raise ValueError(f"{label} has multiple noncoaxial cylindrical surfaces")
    radii = {round(radius, 8) for radius, _, _ in rows}
    if len(radii) != 1:
        raise ValueError(f"{label} has stepped cylindrical radii; contact radius is unresolved")
    return {
        "radius_mm": rows[0][0],
        "point_global_xyz_mm": reference_point,
        "direction_global_xyz": reference_direction,
    }


def _line_distance(first: Mapping[str, Any], second: Mapping[str, Any]) -> float:
    first_direction = _v(first["direction_global_xyz"], "first shaft direction")
    second_direction = _v(second["direction_global_xyz"], "second shaft direction")
    if abs(_dot(first_direction, second_direction)) < 1.0 - 1.0e-6:
        return math.inf
    return _norm(
        _cross(
            _sub(
                _v(first["point_global_xyz_mm"], "first shaft point"),
                _v(second["point_global_xyz_mm"], "second shaft point"),
            ),
            first_direction,
        )
    )


def _planar_faces(shape: cq.Shape, label: str) -> list[dict[str, Any]]:
    result = []
    for face in shape.Faces():
        if face.geomType() != "PLANE":
            continue
        normal = _unit(_vector_tuple(face.normalAt()), f"{label} face normal")
        center = _vector_tuple(face.Center())
        result.append(
            {
                "face": face,
                "normal": normal,
                "center": center,
                "area_mm2": float(face.Area()),
                "inner_wire_count": len(face.innerWires()),
            }
        )
    if not result:
        raise ValueError(f"{label} has no planar faces")
    return result


def _plane_basis(normal: Vector) -> tuple[Vector, Vector]:
    seed = min(
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        key=lambda candidate: abs(_dot(candidate, normal)),
    )
    first = _unit(_sub(seed, _scale(_dot(seed, normal), normal)), "plane basis u")
    second = _unit(_cross(normal, first), "plane basis v")
    return first, second


def _projected_bounds(
    points: Sequence[Vector], origin: Vector, first: Vector, second: Vector
) -> tuple[float, float, float, float]:
    projected = [(_dot(_sub(point, origin), first), _dot(_sub(point, origin), second)) for point in points]
    return (
        min(point[0] for point in projected),
        max(point[0] for point in projected),
        min(point[1] for point in projected),
        max(point[1] for point in projected),
    )


def _intersect_bounds(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    return (
        max(first[0], second[0]),
        min(first[1], second[1]),
        max(first[2], second[2]),
        min(first[3], second[3]),
    )


def _contact_face_pair(
    backer: cq.Shape,
    header: cq.Shape,
    bolt_axis: Vector,
) -> dict[str, Any]:
    backer_faces = _planar_faces(backer, "finished backer")
    header_faces = _planar_faces(header, "finished header")
    candidates = []
    for backer_face in backer_faces:
        backer_normal = backer_face["normal"]
        if abs(_dot(backer_normal, bolt_axis)) < 1.0 - 1.0e-6:
            continue
        for header_face in header_faces:
            if _dot(backer_normal, header_face["normal"]) > -1.0 + 1.0e-6:
                continue
            plane_delta = abs(
                _dot(_sub(header_face["center"], backer_face["center"]), backer_normal)
            )
            if plane_delta > GEOMETRY_TOLERANCE_MM:
                continue
            try:
                backer_vertices = _ordered_outer_vertices(
                    backer_face["face"], "candidate backer contact face"
                )
                header_vertices = _ordered_outer_vertices(
                    header_face["face"], "candidate header contact face"
                )
            except ValueError:
                # Ignore curved planar faces such as counterbore floors while
                # searching for the actual opposed member-contact faces.
                continue
            first, second = _plane_basis(backer_normal)
            backer_bounds = _projected_bounds(
                backer_vertices, backer_face["center"], first, second
            )
            header_bounds = _projected_bounds(
                header_vertices, backer_face["center"], first, second
            )
            overlap = _intersect_bounds(backer_bounds, header_bounds)
            overlap_width = overlap[1] - overlap[0]
            overlap_height = overlap[3] - overlap[2]
            if overlap_width <= GEOMETRY_TOLERANCE_MM or overlap_height <= GEOMETRY_TOLERANCE_MM:
                continue
            candidates.append(
                (
                    overlap_width * overlap_height,
                    backer_face,
                    header_face,
                    plane_delta,
                    backer_vertices,
                    header_vertices,
                )
            )
    if not candidates:
        raise ValueError("finished backer and header have no opposed, coplanar contact face")
    _, backer_face, header_face, plane_delta, backer_vertices, header_vertices = max(
        candidates, key=lambda row: row[0]
    )
    backer_face = {**backer_face, "vertices": backer_vertices}
    header_face = {**header_face, "vertices": header_vertices}
    return {
        "backer_face": backer_face,
        "header_face": header_face,
        "normal": backer_face["normal"],
        "plane_delta_mm": plane_delta,
        "projected_bbox_overlap_is_selection_only": True,
    }


def _plane_intersection(
    line_point: Vector,
    line_direction: Vector,
    plane_point: Vector,
    plane_normal: Vector,
    label: str,
) -> Vector:
    denominator = _dot(line_direction, plane_normal)
    if abs(denominator) < 1.0 - 1.0e-6:
        raise ValueError(f"{label} is not normal to the backer contact face")
    parameter = _dot(_sub(plane_point, line_point), plane_normal) / denominator
    return _add(line_point, _scale(parameter, line_direction))


def _cross2(first: tuple[float, float], second: tuple[float, float]) -> float:
    return first[0] * second[1] - first[1] * second[0]


def _point_in_polygon(point: tuple[float, float], polygon: Sequence[tuple[float, float]]) -> bool:
    inside = False
    x, y = point
    for first, second in zip(polygon, (*polygon[1:], polygon[0]), strict=True):
        x1, y1 = first
        x2, y2 = second
        edge = (x2 - x1, y2 - y1)
        relative = (x - x1, y - y1)
        if abs(_cross2(edge, relative)) <= 1.0e-8 and min(x1, x2) - 1.0e-8 <= x <= max(x1, x2) + 1.0e-8 and min(y1, y2) - 1.0e-8 <= y <= max(y1, y2) + 1.0e-8:
            return True
        if (y1 > y) != (y2 > y):
            crossing_x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if crossing_x > x:
                inside = not inside
    return inside


def _ray_boundary_distance(
    origin: Vector,
    direction: float,
    row_axis: Vector,
    transverse_axis: Vector,
    face: Mapping[str, Any],
) -> tuple[float | None, str | None]:
    if not all(edge.geomType() == "LINE" for edge in face["face"].outerWire().Edges()):
        return None, "outer boundary contains curved edges"
    polygon = tuple(
        (
            _dot(_sub(point, origin), row_axis),
            _dot(_sub(point, origin), transverse_axis),
        )
        for point in face["vertices"]
    )
    if len(polygon) < 3:
        return None, "outer boundary has fewer than three vertices"
    query = (0.0, 0.0)
    if not _point_in_polygon(query, polygon):
        return None, "bolt-row centroid lies outside the actual outer face polygon"
    ray = (0.0, direction)
    distances = []
    for first, second in zip(polygon, (*polygon[1:], polygon[0]), strict=True):
        segment = (second[0] - first[0], second[1] - first[1])
        denominator = _cross2(ray, segment)
        relative = (first[0] - query[0], first[1] - query[1])
        if abs(denominator) <= 1.0e-10:
            if abs(relative[0]) <= 1.0e-8:
                return None, "transverse ray overlaps an outer boundary edge"
            continue
        distance = _cross2(relative, segment) / denominator
        segment_fraction = _cross2(relative, ray) / denominator
        if (
            distance > 1.0e-8
            and -1.0e-8 <= segment_fraction <= 1.0 + 1.0e-8
        ):
            distances.append(distance)
    if not distances:
        return None, "transverse ray does not reach the actual outer face boundary"
    return min(distances), None


def _prism(
    center: Vector,
    normal: Vector,
    inner_radius_mm: float,
    outer_radius_mm: float,
    depth_mm: float,
) -> cq.Shape:
    start = cq.Vector(*center)
    direction = cq.Vector(*normal)
    outer = cq.Solid.makeCylinder(outer_radius_mm, depth_mm, start, direction)
    if inner_radius_mm <= 0.0:
        return outer
    inner = cq.Solid.makeCylinder(inner_radius_mm, depth_mm, start, direction)
    return outer.cut(inner)


def _patch_containment(
    member: cq.Shape,
    face: Mapping[str, Any],
    center: Vector,
    inner_radius_mm: float,
    outer_radius_mm: float,
    label: str,
) -> dict[str, Any]:
    inward = _scale(-1.0, face["normal"])
    try:
        patch = _prism(
            center,
            inward,
            inner_radius_mm,
            outer_radius_mm,
            PATCH_CHECK_DEPTH_MM,
        )
        patch_volume = float(patch.Volume())
        intersection_volume = float(patch.intersect(member).Volume())
        outside_volume = float(patch.cut(member).Volume())
    except Exception as error:  # noqa: BLE001 - preserve a fail-closed geometry reason
        return {
            "member_id": label,
            "contained": False,
            "reason": f"Boolean containment check failed: {type(error).__name__}",
            "patch_volume_mm3": None,
            "intersection_volume_mm3": None,
            "outside_volume_mm3": None,
        }
    contained = (
        patch_volume > 0.0
        and abs(intersection_volume - patch_volume) <= PATCH_VOLUME_TOLERANCE_MM3
        and outside_volume <= PATCH_VOLUME_TOLERANCE_MM3
    )
    return {
        "member_id": label,
        "contained": contained,
        "reason": None if contained else "finite patch is not wholly inside finished member material",
        "patch_volume_mm3": patch_volume,
        "intersection_volume_mm3": intersection_volume,
        "outside_volume_mm3": outside_volume,
    }


def _unit_loads() -> tuple[dict[str, Any], ...]:
    cases = []
    for kind, units, unit_label in (
        ("force", "N", "unit_force"),
        ("moment", "Nmm", "unit_moment"),
    ):
        for axis_index, axis_name in enumerate(("X", "Y", "Z")):
            direction = tuple(1.0 if index == axis_index else 0.0 for index in range(3))
            for sign in (1.0, -1.0):
                vector = _scale(sign, direction)  # type: ignore[arg-type]
                cases.append(
                    {
                        "case_id": f"{unit_label}_{axis_name}_{'plus' if sign > 0 else 'minus'}",
                        "kind": kind,
                        "units": units,
                        "load_force_global_xyz_n": vector if kind == "force" else (0.0, 0.0, 0.0),
                        "load_moment_at_group_centroid_global_xyz_nmm": vector
                        if kind == "moment"
                        else (0.0, 0.0, 0.0),
                    }
                )
    return tuple(cases)


def _point_wrench_solution(
    load_force: Vector,
    load_moment: Vector,
    group: Mapping[str, Any],
) -> dict[str, Any]:
    row = group["row_axis"]
    points = group["points"]
    center = group["centroid"]
    spacing = group["spacing_mm"]
    reaction_force = _scale(-1.0, load_force)
    reaction_moment = _scale(-1.0, load_moment)
    unresolved = _scale(_dot(reaction_moment, row), row)
    resolved = _sub(reaction_moment, unresolved)
    couple = _scale(1.0 / spacing, _cross(row, resolved))
    reactions = (
        _add(_scale(0.5, reaction_force), couple),
        _sub(_scale(0.5, reaction_force), couple),
    )
    actual_force = _add(*reactions)
    actual_moment = _add(
        _cross(_sub(points[0], center), reactions[0]),
        _cross(_sub(points[1], center), reactions[1]),
    )
    force_residual = _add(load_force, actual_force)
    moment_residual = _add(load_moment, actual_moment)
    return {
        "bolt_reaction_resultants_global_xyz_n": reactions,
        "idealized_point_reactions_sum_global_xyz_n": actual_force,
        "idealized_point_reactions_moment_at_centroid_global_xyz_nmm": actual_moment,
        "force_equilibrium_residual_global_xyz_n": force_residual,
        "moment_equilibrium_residual_global_xyz_nmm": moment_residual,
        "unresolved_row_moment_global_xyz_nmm": unresolved,
        "force_residual_norm_n": _norm(force_residual),
        "moment_residual_norm_nmm": _norm(moment_residual),
        "equilibrium_closed_by_ideal_point_fasteners": (
            _norm(force_residual) <= STATICS_TOLERANCE
            and _norm(moment_residual) <= STATICS_TOLERANCE
        ),
    }


def _finite_contact_solution(
    load_force: Vector,
    load_moment: Vector,
    group: Mapping[str, Any],
) -> dict[str, Any]:
    baseline = _point_wrench_solution(load_force, load_moment, group)
    normal = group["contact_normal"]
    points = group["points"]
    center = group["centroid"]
    row = group["row_axis"]
    row_coordinate = _dot(_scale(-1.0, load_moment), row)
    bolt_forces = list(baseline["bolt_reaction_resultants_global_xyz_n"])
    contact_rows = []
    unsupported = []

    # Move any ideal point compression at a bore to a tested annular patch.
    for index, axial in enumerate(group["annular_patches"]):
        axial_reaction = _dot(bolt_forces[index], normal)
        if axial_reaction >= -STATICS_TOLERANCE:
            continue
        if axial["fully_contained_in_both_finished_faces"]:
            contact_force = _scale(axial_reaction, normal)
            bolt_forces[index] = _sub(bolt_forces[index], contact_force)
            contact_rows.append(
                {
                    "contact_id": f"annular_bore_{index + 1}",
                    "point_global_xyz_mm": points[index],
                    "reaction_global_xyz_n": contact_force,
                    "patch_kind": "annulus_centered_on_actual_bore_axis",
                    "patch_geometry_verified": True,
                }
            )
        else:
            unsupported.append(
                {
                    "component": f"bolt_{index + 1}_axial_compression",
                    "reason": "finite annular patch does not fit both finished contact faces",
                }
            )

    # A finite edge patch supplies only the row-axis couple. This is a
    # geometric witness construction, not a contact law or capacity check.
    if abs(row_coordinate) > STATICS_TOLERANCE:
        desired_side = "negative" if row_coordinate > 0.0 else "positive"
        patch = group["edge_patches"][desired_side]
        if patch["fully_contained_in_both_finished_faces"]:
            lever = patch["lever_arm_mm"]
            if lever <= GEOMETRY_TOLERANCE_MM:
                unsupported.append(
                    {"component": "row_axis_moment", "reason": "finite edge patch has no lever arm"}
                )
            else:
                couple_force = abs(row_coordinate) / lever
                bolt_addition = _scale(0.5 * couple_force, normal)
                bolt_forces = [
                    _add(force, bolt_addition) for force in bolt_forces
                ]
                contact_force = _scale(-couple_force, normal)
                contact_rows.append(
                    {
                        "contact_id": f"row_moment_{desired_side}_edge_patch",
                        "point_global_xyz_mm": patch["center_global_xyz_mm"],
                        "reaction_global_xyz_n": contact_force,
                        "patch_kind": "finite_disk_halfway_to_actual_outer_face_ray",
                        "patch_geometry_verified": True,
                        "lever_arm_mm": lever,
                        "bolt_tension_resultant_minimum_norm_allocation_n": couple_force,
                    }
                )
        else:
            unsupported.append(
                {
                    "component": "row_axis_moment",
                    "reason": f"{desired_side} finite edge patch is not contained in both finished contact faces",
                }
            )

    force_sum = _add(*bolt_forces)
    moment_sum = (0.0, 0.0, 0.0)
    for point, force in zip(points, bolt_forces, strict=True):
        moment_sum = _add(moment_sum, _cross(_sub(point, center), force))
    for row_data in contact_rows:
        force = row_data["reaction_global_xyz_n"]
        point = row_data["point_global_xyz_mm"]
        force_sum = _add(force_sum, force)
        moment_sum = _add(moment_sum, _cross(_sub(point, center), force))
    force_residual = _add(load_force, force_sum)
    moment_residual = _add(load_moment, moment_sum)
    unilateral_signs_valid = all(
        _dot(force, normal) >= -STATICS_TOLERANCE for force in bolt_forces
    ) and all(
        _dot(row_data["reaction_global_xyz_n"], normal) <= STATICS_TOLERANCE
        for row_data in contact_rows
    )
    algebraic_equilibrium_closes = (
        _norm(force_residual) <= STATICS_TOLERANCE
        and _norm(moment_residual) <= STATICS_TOLERANCE
    )
    return {
        "bolt_reaction_resultants_global_xyz_n": tuple(bolt_forces),
        "contact_reaction_resultants": tuple(contact_rows),
        "force_equilibrium_residual_global_xyz_n": force_residual,
        "moment_equilibrium_residual_global_xyz_nmm": moment_residual,
        "force_residual_norm_n": _norm(force_residual),
        "moment_residual_norm_nmm": _norm(moment_residual),
        "algebraic_equilibrium_closes": algebraic_equilibrium_closes,
        "unilateral_bolt_tension_and_contact_compression_signs_valid": unilateral_signs_valid,
        "equilibrium_witness_closes": algebraic_equilibrium_closes
        and not unsupported
        and unilateral_signs_valid,
        "unresolved_support_components": tuple(unsupported),
        "all_required_finite_contact_patches_verified": not unsupported,
        "idealized_bolt_bearing_support_established": False,
        "bolt_tension_capacity_established": False,
        "bolt_force_allocation_is_a_load_sharing_prediction": False,
        "baseline_unresolved_row_moment_global_xyz_nmm": baseline[
            "unresolved_row_moment_global_xyz_nmm"
        ],
    }


def _validate_provenance(geometry: Any) -> dict[str, Any]:
    binding = getattr(geometry, "source_binding", None)
    if binding is None or not isinstance(getattr(binding, "inventory_sha256", None), str):
        raise TypeError("WJ-12 source binding with an inventory hash is required")
    inventory_hash = getattr(geometry, "source_inventory_sha256", None)
    inventory_matches = inventory_hash == binding.inventory_sha256
    if not isinstance(getattr(geometry, "family_source_fingerprints", None), Mapping):
        raise TypeError("WJ-12 family source fingerprints are required")
    family_trial_ids = getattr(geometry, "family_trial_ids", None)
    if not isinstance(family_trial_ids, Mapping) or not family_trial_ids or any(
        not isinstance(name, str)
        or not name
        or not isinstance(trial_id, str)
        or not trial_id
        for name, trial_id in family_trial_ids.items()
    ):
        raise TypeError("WJ-12 family trial IDs are required and must be nonempty")
    family_sources = {
        family: dict(rows)
        for family, rows in sorted(geometry.family_source_fingerprints.items())
        if isinstance(rows, Mapping)
    }
    merged: dict[str, str] = {}
    conflicts = []
    mismatches = {}
    for rows in family_sources.values():
        for relative_path, expected in rows.items():
            if relative_path in merged and merged[relative_path] != expected:
                conflicts.append(relative_path)
            merged[relative_path] = expected
    for relative_path, expected in sorted(merged.items()):
        path = ROOT / relative_path
        try:
            observed = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            observed = None
        if observed != expected:
            mismatches[relative_path] = {
                "expected_sha256": expected,
                "observed_sha256": observed,
            }
    producer_rows = {}
    for family, relative_path in FAMILY_PRODUCER_PATHS.items():
        expected = merged.get(relative_path)
        try:
            observed = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        except OSError:
            observed = None
        producer_rows[family] = {
            "path": relative_path,
            "source_bound_sha256": expected,
            "current_sha256": observed,
            "matches": expected is not None and expected == observed,
        }
    runtime_modules = getattr(binding, "runtime_module_sha256", {})
    if not isinstance(runtime_modules, Mapping):
        runtime_modules = {}
    producers = {
        "wj12_compositor": "scripts/wood_joint_wj12_compositor.py",
        "wj12_backer_statics": "scripts/wood_joint_wj12_backer_statics.py",
    }
    producer_hashes = {}
    for name, relative_path in producers.items():
        try:
            digest = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        except OSError:
            digest = None
        producer_hashes[name] = {"path": relative_path, "sha256": digest}
    return {
        "source_inventory_sha256": inventory_hash,
        "binding_inventory_sha256": binding.inventory_sha256,
        "source_inventory_matches_binding": inventory_matches,
        "source_commit": getattr(geometry.source_inventory, "get", lambda *_: None)("source_commit"),
        "candidate": getattr(geometry.source_inventory, "get", lambda *_: None)("candidate"),
        "family_trial_ids": dict(sorted(family_trial_ids.items())),
        "family_source_fingerprints_sha256": family_sources,
        "family_input_hash_conflicts": sorted(set(conflicts)),
        "family_input_hash_mismatches": mismatches,
        "family_input_hashes_current": bool(merged) and not conflicts and not mismatches,
        "family_producers": producer_rows,
        "all_family_producers_bound_and_current": all(row["matches"] for row in producer_rows.values()),
        "source_runtime_module_sha256": dict(sorted(runtime_modules.items())),
        "report_producer_hashes_sha256": producer_hashes,
    }


def _side_geometry(geometry: Any, side: str) -> dict[str, Any]:
    part_id = f"inner_kicker_backer_{side}"
    if part_id not in geometry.finished_candidate_parts:
        raise ValueError(f"finished candidate geometry omits {part_id}")
    if "base_header" not in geometry.finished_hosts:
        raise ValueError("finished source geometry omits base_header")
    backer = geometry.finished_candidate_parts[part_id]
    header = geometry.finished_hosts["base_header"]
    _shape_hash(backer)
    _shape_hash(header)
    axis_ids = tuple(f"backer_header_{side}_{index}" for index in (1, 2))
    if any(axis_id not in geometry.candidate_bores for axis_id in axis_ids):
        raise ValueError(f"{side} backer must have exactly its two declared candidate bores")
    bore_shapes = []
    bore_axes = []
    shaft_axes = []
    for axis_id in axis_ids:
        bore = geometry.candidate_bores[axis_id]
        if bore.family != "wj05_backer":
            raise ValueError(f"{axis_id} is not bound to the WJ-05 backer family")
        if bore.trial_id != geometry.family_trial_ids.get("wj05_backer"):
            raise ValueError(
                f"{axis_id} trial ID differs from composed WJ-05 family provenance"
            )
        if set(bore.receiver_ids) != {part_id, "base_header"}:
            raise ValueError(f"{axis_id} receiver identities do not bind backer and header")
        bore_shapes.append(bore.shape)
        bore_axes.append(_cylindrical_axis(bore.shape, f"candidate bore {axis_id}"))
        components = geometry.candidate_installed_hardware.get(axis_id)
        if not isinstance(components, Mapping) or "shaft" not in components:
            raise ValueError(f"{axis_id} has no installed shaft geometry")
        shaft = _cylindrical_axis(components["shaft"], f"installed shaft {axis_id}")
        if _line_distance(bore_axes[-1], shaft) > 1.0e-5:
            raise ValueError(f"{axis_id} installed shaft does not follow its candidate bore")
        shaft_axes.append(shaft)

    axis_direction = _unit(
        _add(bore_axes[0]["direction_global_xyz"], bore_axes[1]["direction_global_xyz"]),
        f"{side} common bore axis",
    )
    if abs(_dot(bore_axes[0]["direction_global_xyz"], bore_axes[1]["direction_global_xyz"])) < 1.0 - 1.0e-6:
        raise ValueError(f"{side} backer bores are not parallel")
    contact = _contact_face_pair(backer, header, axis_direction)
    normal = contact["normal"]
    backer_face = contact["backer_face"]
    header_face = contact["header_face"]
    plane_point = backer_face["center"]
    points = tuple(
        _plane_intersection(
            bore["point_global_xyz_mm"],
            bore["direction_global_xyz"],
            plane_point,
            normal,
            f"backer bolt axis {axis_id}",
        )
        for axis_id, bore in zip(axis_ids, bore_axes, strict=True)
    )
    spacing = _norm(_sub(points[1], points[0]))
    if spacing <= GEOMETRY_TOLERANCE_MM:
        raise ValueError(f"{side} backer bolt row has zero spacing")
    row = _unit(_sub(points[1], points[0]), f"{side} bolt row")
    if abs(_dot(row, normal)) > 1.0e-6:
        raise ValueError(f"{side} bolt row does not lie in the derived contact face")
    centroid = _scale(0.5, _add(points[0], points[1]))
    transverse = _unit(_cross(normal, row), f"{side} face transverse axis")
    if abs(_dot(bore_axes[0]["direction_global_xyz"], normal)) < 1.0 - 1.0e-6:
        raise ValueError(f"{side} candidate bores are not normal to the derived contact face")

    negative_distance, negative_reason = _ray_boundary_distance(
        centroid, -1.0, row, transverse, backer_face
    )
    positive_distance, positive_reason = _ray_boundary_distance(
        centroid, 1.0, row, transverse, backer_face
    )
    edge_distances = {"negative": negative_distance, "positive": positive_distance}
    edge_reasons = {"negative": negative_reason, "positive": positive_reason}

    annular_patches = []
    for index, (axis_id, point, bore) in enumerate(
        zip(axis_ids, points, bore_axes, strict=True), start=1
    ):
        inner_radius = bore["radius_mm"] + ANNULUS_RADIAL_GAP_MM
        outer_radius = inner_radius + ANNULUS_RADIAL_WIDTH_MM
        backer_check = _patch_containment(
            backer,
            backer_face,
            point,
            inner_radius,
            outer_radius,
            part_id,
        )
        header_check = _patch_containment(
            header,
            header_face,
            point,
            inner_radius,
            outer_radius,
            "base_header",
        )
        annular_patches.append(
            {
                "axis_id": axis_id,
                "center_global_xyz_mm": point,
                "inner_radius_mm": inner_radius,
                "outer_radius_mm": outer_radius,
                "radial_gap_from_candidate_bore_mm": ANNULUS_RADIAL_GAP_MM,
                "radial_width_mm": ANNULUS_RADIAL_WIDTH_MM,
                "area_mm2": math.pi * (outer_radius**2 - inner_radius**2),
                "backer_containment": backer_check,
                "header_containment": header_check,
                "fully_contained_in_both_finished_faces": backer_check["contained"]
                and header_check["contained"],
            }
        )

    edge_patches = {}
    for side_name, sign in (("negative", -1.0), ("positive", 1.0)):
        distance = edge_distances[side_name]
        if distance is None:
            edge_patches[side_name] = {
                "side": side_name,
                "fully_contained_in_both_finished_faces": False,
                "reason": edge_reasons[side_name],
                "lever_arm_mm": None,
                "center_global_xyz_mm": None,
                "backer_containment": None,
                "header_containment": None,
            }
            continue
        center = _add(centroid, _scale(sign * 0.5 * distance, transverse))
        backer_check = _patch_containment(
            backer,
            backer_face,
            center,
            0.0,
            EDGE_PATCH_RADIUS_MM,
            part_id,
        )
        header_check = _patch_containment(
            header,
            header_face,
            center,
            0.0,
            EDGE_PATCH_RADIUS_MM,
            "base_header",
        )
        edge_patches[side_name] = {
            "side": side_name,
            "center_global_xyz_mm": center,
            "radius_mm": EDGE_PATCH_RADIUS_MM,
            "center_at_fraction_of_outer_face_ray": 0.5,
            "lever_arm_mm": 0.5 * distance,
            "backer_containment": backer_check,
            "header_containment": header_check,
            "fully_contained_in_both_finished_faces": backer_check["contained"]
            and header_check["contained"],
        }

    return {
        "side": side,
        "part_id": part_id,
        "axis_ids": axis_ids,
        "backer": backer,
        "header": header,
        "backer_face": backer_face,
        "header_face": header_face,
        "points": points,
        "centroid": centroid,
        "spacing_mm": spacing,
        "row_axis": row,
        "contact_normal": normal,
        "transverse_axis": transverse,
        "plane_point": plane_point,
        "edge_distances_mm": edge_distances,
        "edge_distance_reasons": edge_reasons,
        "contact_plane_delta_mm": contact["plane_delta_mm"],
        "annular_patches": tuple(annular_patches),
        "edge_patches": edge_patches,
        "geometry_evidence": {
            "finished_backer_sha256": _shape_hash(backer),
            "finished_header_sha256": _shape_hash(header),
            "bores_sha256": {
                axis_id: _shape_hash(shape)
                for axis_id, shape in zip(axis_ids, bore_shapes, strict=True)
            },
            "shafts_sha256": {
                axis_id: _shape_hash(geometry.candidate_installed_hardware[axis_id]["shaft"])
                for axis_id in axis_ids
            },
        },
    }


def _serialize_side(side: Mapping[str, Any], geometry: Any) -> dict[str, Any]:
    face = side["backer_face"]
    header_face = side["header_face"]
    point_rows = []
    for axis_id, point in zip(side["axis_ids"], side["points"], strict=True):
        point_rows.append({"axis_id": axis_id, "point_global_xyz_mm": point})
    group = {
        "points": side["points"],
        "centroid": side["centroid"],
        "spacing_mm": side["spacing_mm"],
        "row_axis": side["row_axis"],
        "contact_normal": side["contact_normal"],
        "transverse_axis": side["transverse_axis"],
        "annular_patches": side["annular_patches"],
        "edge_patches": side["edge_patches"],
    }
    cases = []
    for unit_case in _unit_loads():
        load_force = unit_case["load_force_global_xyz_n"]
        load_moment = unit_case["load_moment_at_group_centroid_global_xyz_nmm"]
        cases.append(
            {
                **unit_case,
                "point_fastener_baseline": _point_wrench_solution(
                    load_force, load_moment, group
                ),
                "finite_contact_witness": _finite_contact_solution(
                    load_force, load_moment, group
                ),
            }
        )
    return {
        "backer_id": side["part_id"],
        "candidate_bolt_axis_ids": list(side["axis_ids"]),
        "bolt_points_projected_to_actual_contact_plane": point_rows,
        "group_centroid_global_xyz_mm": side["centroid"],
        "bolt_spacing_mm": side["spacing_mm"],
        "bolt_row_axis_global_xyz": side["row_axis"],
        "contact_face_normal_global_xyz": side["contact_normal"],
        "transverse_face_axis_global_xyz": side["transverse_axis"],
        "contact_plane_global_coordinate_mm": _dot(side["plane_point"], side["contact_normal"]),
        "contact_face_geometry": {
            "backer_material_area_mm2_including_real_openings": face["area_mm2"],
            "header_material_area_mm2_including_real_openings": header_face["area_mm2"],
            "backer_inner_wire_count": face["inner_wire_count"],
            "header_inner_wire_count": header_face["inner_wire_count"],
            "opposed_coplanar_face_delta_mm": side["contact_plane_delta_mm"],
            "outer_face_ray_distances_from_bolt_row_centroid_mm": side["edge_distances_mm"],
            "outer_face_ray_unresolved_reasons": side["edge_distance_reasons"],
            "ray_distance_method": "intersection with actual backer contact-face outer-wire polygon; no bounding rectangle used",
            "edge_patch_centers_are_halfway_to_each_actual_outer_boundary": True,
        },
        "finite_contact_patch_checks": {
            "witness_dimensions_mm": {
                "annulus_radial_gap": ANNULUS_RADIAL_GAP_MM,
                "annulus_radial_width": ANNULUS_RADIAL_WIDTH_MM,
                "edge_disk_radius": EDGE_PATCH_RADIUS_MM,
                "boolean_check_depth": PATCH_CHECK_DEPTH_MM,
            },
            "annular_bore_patches": list(side["annular_patches"]),
            "edge_moment_patches": side["edge_patches"],
            "all_annuli_inside_both_finished_faces": all(
                row["fully_contained_in_both_finished_faces"]
                for row in side["annular_patches"]
            ),
            "all_edge_disks_inside_both_finished_faces": all(
                row["fully_contained_in_both_finished_faces"]
                for row in side["edge_patches"].values()
            ),
            "patch_geometry_is_contact_capacity_or_pressure_evidence": False,
        },
        "unit_wrench_cases": cases,
        "geometry_sha256": side["geometry_evidence"],
        "unit_cases_are_real_demands": False,
        "real_backer_header_demand": None,
        "physical_bolt_bearing_support_established": False,
        "backer_header_capacity_established": False,
        "release": False,
    }


def build_report(geometry: Any) -> dict[str, Any]:
    """Build a JSON-safe diagnostic from an already composed WJ-12 object."""
    if getattr(geometry, "trial_id", None) != TRIAL_ID:
        raise ValueError("backer statics requires the corrected WJ-12 trial")
    if getattr(geometry, "status", None) != "unaccepted_integrated_hypothesis":
        raise ValueError("backer statics requires the unaccepted integrated hypothesis")
    if not isinstance(getattr(geometry, "source_inventory", None), Mapping):
        raise TypeError("backer statics requires canonical source inventory evidence")
    provenance = _validate_provenance(geometry)
    sides = {
        side: _side_geometry(geometry, side)
        for side in ("left", "right")
    }
    side_rows = {side: _serialize_side(row, geometry) for side, row in sides.items()}
    gates = {
        "source_inventory_matches_binding": provenance["source_inventory_matches_binding"],
        "family_input_hashes_current": provenance["family_input_hashes_current"],
        "all_family_producers_bound_and_current": provenance[
            "all_family_producers_bound_and_current"
        ],
        "both_backer_contact_planes_derived_from_finished_geometry": True,
        "all_candidate_axes_match_installed_shafts": True,
        "finite_patch_boolean_checks_run": True,
        "all_finite_unit_wrench_equilibrium_witnesses_close": all(
            case["finite_contact_witness"]["equilibrium_witness_closes"]
            for row in side_rows.values()
            for case in row["unit_wrench_cases"]
        ),
        "real_backer_demands_available": False,
        "bolt_or_contact_capacity_established": False,
        "physical_bolt_bearing_support_established": False,
        "load_sharing_or_contact_pressure_assumed": False,
        "fabrication_released": False,
        "structural_released": False,
        "release": False,
    }
    return {
        "schema": SCHEMA,
        "trial_id": geometry.trial_id,
        "status": "capacity_independent_unit_statics_witness",
        "claim_boundary": {
            "scope": "signed unit-wrench equilibrium witnesses for the two WJ-05 backer/header joints",
            "unit_wrenches_are_real_demands": False,
            "historical_surrogate_backer_demand_used": False,
            "fresh_native_solve_performed": False,
            "materialization_performed": False,
            "capacity_pressure_stiffness_preload_or_equal_sharing_acceptance": False,
            "physical_installation_or_fabrication_release": False,
        },
        "source_provenance": provenance,
        "finite_patch_basis": {
            "annular_bore_patch": (
                "For compressive axial point resultants only, use an annulus centered on each actual bore, "
                "with a 0.5 mm radial gap beyond the candidate bore and 2.0 mm radial width. "
                "Extrude 0.25 mm into each finished member and require the entire annular prism to be "
                "contained in both BReps. Its geometric centroid is the resultant location; this does "
                "not prescribe pressure or a capacity."
            ),
            "row_moment_patch": (
                "For a row-axis moment only, use a 2.0 mm radius disk centered halfway along the ray "
                "from the actual bolt-row centroid to the corresponding outer-wire boundary. Test the "
                "0.25 mm inward prism against both finished members. The ray distance comes from the "
                "actual polygon, not a projected bounding rectangle."
            ),
            "unsupported_components": (
                "Fastener transverse bearing remains an ideal point reaction without a bearing patch "
                "model. Any failed annular or edge-patch containment leaves its associated support "
                "component unresolved."
            ),
            "witness_dimensions_are_not_design_or_acceptance_values": True,
        },
        "backers": side_rows,
        "gates": gates,
    }
