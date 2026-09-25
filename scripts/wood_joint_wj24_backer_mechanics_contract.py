"""Source-bound mechanical input contract for the WJ24 center backer joints.

The adapter consumes an already composed WJ24 geometry object. It extracts the
two backer-to-header interfaces, four modeled through-bolt axes, and four fixed
Hillman center-kicker load-entry axes. It does not build WJ24 geometry, assign
loads, calculate resistance, establish contact pressure, or close a release
gate.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import _source_shape_fingerprint

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
SCHEMA = "wood_joint_wj24_backer_mechanics_contract/v1"
LAYOUT_ID = "wj24-twenty-four-duty-integrated-static-v1"
COMPOSITION_TRIAL_ID = "wj24-wj18-plus-top-center-bottom-pairs-v1"
BACKER_FAMILY = "wj05_backer"
BACKER_TRIAL_ID = "compact_bridge_rear_bevel_4x6_spine_137_7"
# WJ24 retains nine source bundles for ten family trial labels. The WJ05
# backer trial is a second label on the shared compact-outer source bundle.
BACKER_SOURCE_BUNDLE = "wj03_compact_outer"
BACKER_IDS = {
    "left": "inner_kicker_backer_left",
    "right": "inner_kicker_backer_right",
}
HEADER_ID = "base_header"
EXPECTED_BOLT_AXIS_IDS = tuple(
    f"backer_header_{side}_{index}"
    for side in ("left", "right")
    for index in (1, 2)
)
EXPECTED_HILLMAN_AXIS_IDS = tuple(
    f"round_kicker_{side}_center_{index}"
    for side in ("left", "right")
    for index in (1, 2)
)
GEOMETRY_TOLERANCE_MM = 1.0e-5
PLANE_TOLERANCE_MM = 1.0e-5
AXIS_ANGULAR_TOLERANCE = 1.0e-7
AXIS_VOLUME_REL_TOLERANCE = 1.0e-8
AXIS_BBOX_TOLERANCE_MM = 2.0e-5
BOOLEAN_VOLUME_TOLERANCE_MM3 = 1.0e-3

Vector = tuple[float, float, float]


def _sha256_file(relative_path: str) -> str:
    path = (ROOT / relative_path).resolve()
    if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
        raise ValueError(f"source fingerprint path is unavailable: {relative_path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vector(value: Any, label: str) -> Vector:
    if isinstance(value, cq.Vector):
        values = tuple(float(component) for component in value.toTuple())
    else:
        values = tuple(float(component) for component in value)
    if len(values) != 3 or not all(math.isfinite(component) for component in values):
        raise ValueError(f"{label} must be a finite three-vector")
    return values  # type: ignore[return-value]


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


def _norm(value: Vector) -> float:
    return math.sqrt(_dot(value, value))


def _unit(value: Any, label: str) -> Vector:
    vector = _vector(value, label)
    length = _norm(vector)
    if length <= GEOMETRY_TOLERANCE_MM:
        raise ValueError(f"{label} has zero length")
    return _scale(1.0 / length, vector)


def _rounded(vector: Vector, digits: int = 12) -> list[float]:
    return [round(value, digits) for value in vector]


def _shape_sha256(shape: Any, label: str) -> str:
    if not isinstance(shape, cq.Shape) or shape.isNull() or not shape.isValid():
        raise ValueError(f"{label} is missing valid composed CAD geometry")
    if not shape.Solids():
        raise ValueError(f"{label} must contain a solid")
    return _source_shape_fingerprint(shape)


def _current_hash_map(values: Any, label: str) -> dict[str, str]:
    if not isinstance(values, Mapping) or not values:
        raise ValueError(f"{label} source fingerprint map is missing or empty")
    result: dict[str, str] = {}
    for path, digest in values.items():
        relative_path, source_digest = str(path), str(digest)
        if (
            len(source_digest) != 64
            or any(char not in "0123456789abcdef" for char in source_digest)
        ):
            raise ValueError(f"{label} has an invalid SHA-256 pin: {relative_path}")
        if _sha256_file(relative_path) != source_digest:
            raise ValueError(f"{label} source changed after WJ24 composition: {relative_path}")
        result[relative_path] = source_digest
    return dict(sorted(result.items()))


def _inventory_rows(inventory: Any, collection: str, key: str) -> dict[str, dict[str, Any]]:
    rows = inventory.get(collection) if isinstance(inventory, Mapping) else None
    if not isinstance(rows, (tuple, list)):
        raise TypeError(f"canonical inventory omits {collection}")
    result = {
        str(row.get(key)): dict(row)
        for row in rows
        if isinstance(row, Mapping) and row.get(key)
    }
    if len(result) != len(rows):
        raise ValueError(f"canonical inventory has malformed or duplicate {key} values")
    return result


def _shape_intersection_volume(first: cq.Shape, second: cq.Shape, label: str) -> float:
    intersection = first.intersect(second)
    if not intersection.isValid():
        raise ValueError(f"{label} Boolean intersection is invalid")
    volume = float(intersection.Volume())
    if not math.isfinite(volume) or volume < -BOOLEAN_VOLUME_TOLERANCE_MM3:
        raise ValueError(f"{label} Boolean intersection volume is invalid")
    return max(0.0, volume)


def _bbox_axis_envelope(shape: cq.Shape, direction: Vector) -> tuple[float, float]:
    box = shape.BoundingBox()
    corners = (
        (box.xmin, box.ymin, box.zmin),
        (box.xmin, box.ymin, box.zmax),
        (box.xmin, box.ymax, box.zmin),
        (box.xmin, box.ymax, box.zmax),
        (box.xmax, box.ymin, box.zmin),
        (box.xmax, box.ymin, box.zmax),
        (box.xmax, box.ymax, box.zmin),
        (box.xmax, box.ymax, box.zmax),
    )
    projections = [_dot(_vector(corner, "bounding-box corner"), direction) for corner in corners]
    return min(projections), max(projections)


def _authenticate_cylinder(
    shape: cq.Shape,
    *,
    origin: Vector,
    direction: Vector,
    diameter_mm: float,
    length_mm: float,
    label: str,
) -> None:
    """Check an occupancy BRep against an authenticated straight cylinder axis."""
    if diameter_mm <= 0 or length_mm <= 0:
        raise ValueError(f"{label} has nonpositive source cylinder dimensions")
    radius = diameter_mm / 2.0
    expected_end = _add(origin, _scale(length_mm, direction))
    box = shape.BoundingBox()
    expected_bounds: list[float] = []
    for coordinate in range(3):
        transverse = radius * math.sqrt(max(0.0, 1.0 - direction[coordinate] ** 2))
        expected_bounds.extend(
            (
                min(origin[coordinate], expected_end[coordinate]) - transverse,
                max(origin[coordinate], expected_end[coordinate]) + transverse,
            )
        )
    actual_bounds = [box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax]
    if any(
        abs(actual - expected) > AXIS_BBOX_TOLERANCE_MM
        for actual, expected in zip(actual_bounds, expected_bounds, strict=True)
    ):
        raise ValueError(f"{label} BRep bounds disagree with the source occupancy axis")
    expected_volume = math.pi * radius**2 * length_mm
    if not math.isclose(
        float(shape.Volume()),
        expected_volume,
        rel_tol=AXIS_VOLUME_REL_TOLERANCE,
        abs_tol=1.0e-7,
    ):
        raise ValueError(f"{label} is not the source full-length cylindrical occupancy")


def _cylindrical_axis(shape: cq.Shape, label: str) -> dict[str, Any]:
    """Extract one coaxial cylindrical surface from a composed BRep."""
    rows = []
    for face in shape.Faces():
        if face.geomType() != "CYLINDER":
            continue
        cylinder = face._geomAdaptor().Cylinder()
        axis = cylinder.Axis()
        location = axis.Location()
        direction = axis.Direction()
        rows.append(
            {
                "radius_mm": float(cylinder.Radius()),
                "point_global_xyz_mm": _vector(
                    (location.X(), location.Y(), location.Z()), f"{label} cylinder location"
                ),
                "direction_global_xyz": _unit(
                    (direction.X(), direction.Y(), direction.Z()), f"{label} cylinder direction"
                ),
            }
        )
    if not rows:
        raise ValueError(f"{label} has no cylindrical face")
    reference = rows[0]
    for row in rows[1:]:
        if (
            abs(abs(_dot(reference["direction_global_xyz"], row["direction_global_xyz"])) - 1.0)
            > AXIS_ANGULAR_TOLERANCE
            or _norm(
                _cross(
                    _sub(row["point_global_xyz_mm"], reference["point_global_xyz_mm"]),
                    reference["direction_global_xyz"],
                )
            )
            > PLANE_TOLERANCE_MM
            or abs(row["radius_mm"] - reference["radius_mm"]) > PLANE_TOLERANCE_MM
        ):
            raise ValueError(f"{label} has multiple noncoaxial/stepped cylindrical surfaces")
    return reference


def _require_member_bore_axis(
    shape: cq.Shape,
    axis: Mapping[str, Any],
    *,
    member_id: str,
    axis_id: str,
) -> None:
    """Confirm a receiver's finished BRep retains the composed bolt-bore line."""
    matches = []
    for face in shape.Faces():
        if face.geomType() != "CYLINDER":
            continue
        cylinder = face._geomAdaptor().Cylinder()
        if abs(float(cylinder.Radius()) - float(axis["radius_mm"])) > PLANE_TOLERANCE_MM:
            continue
        cylinder_axis = cylinder.Axis()
        location = cylinder_axis.Location()
        direction = cylinder_axis.Direction()
        point = _vector((location.X(), location.Y(), location.Z()), f"{axis_id}/{member_id} bore point")
        unit_direction = _unit(
            (direction.X(), direction.Y(), direction.Z()), f"{axis_id}/{member_id} bore direction"
        )
        if (
            abs(abs(_dot(unit_direction, axis["direction_global_xyz"])) - 1.0)
            <= AXIS_ANGULAR_TOLERANCE
            and _norm(
                _cross(
                    _sub(point, axis["point_global_xyz_mm"]),
                    axis["direction_global_xyz"],
                )
            )
            <= PLANE_TOLERANCE_MM
        ):
            matches.append(face)
    if not matches:
        raise ValueError(f"{axis_id}: no matching finished-member bore centerline in {member_id}")


def _line_plane_intersection(
    point: Vector, direction: Vector, plane_point: Vector, plane_normal: Vector, label: str
) -> Vector:
    denominator = _dot(direction, plane_normal)
    if abs(denominator) <= AXIS_ANGULAR_TOLERANCE:
        raise ValueError(f"{label} axis is parallel to the physical interface plane")
    parameter = _dot(_sub(plane_point, point), plane_normal) / denominator
    return _add(point, _scale(parameter, direction))


def _point_on_axis(point: Vector, axis: Mapping[str, Any]) -> bool:
    delta = _sub(point, axis["point_global_xyz_mm"])
    return _norm(_cross(delta, axis["direction_global_xyz"])) <= PLANE_TOLERANCE_MM


def _wire_record(wire: cq.Wire, label: str) -> dict[str, Any]:
    edge_rows = []
    for edge_index, edge in enumerate(wire.Edges()):
        vertices = [_vector(vertex.Center(), f"{label} edge vertex") for vertex in edge.Vertices()]
        row: dict[str, Any] = {
            "edge_index": edge_index,
            "curve_type": edge.geomType(),
            "edge_shape_sha256": _source_shape_fingerprint(edge),
            "vertex_global_xyz_mm": [_rounded(point) for point in vertices],
        }
        if edge.geomType() == "CIRCLE":
            circle = edge._geomAdaptor().Circle()
            center = circle.Location()
            normal = circle.Axis().Direction()
            row["circle"] = {
                "center_global_xyz_mm": _rounded(
                    _vector((center.X(), center.Y(), center.Z()), f"{label} circle center")
                ),
                "axis_global_xyz": _rounded(
                    _unit((normal.X(), normal.Y(), normal.Z()), f"{label} circle axis")
                ),
                "radius_mm": float(circle.Radius()),
            }
        edge_rows.append(row)
    return {
        "wire_shape_sha256": _source_shape_fingerprint(wire),
        "edge_count": len(edge_rows),
        "edges": edge_rows,
    }


def _planar_faces(shape: cq.Shape, member_id: str) -> list[dict[str, Any]]:
    rows = []
    for face_index, face in enumerate(shape.Faces()):
        if face.geomType() != "PLANE":
            continue
        normal = _unit(_vector(face.normalAt(), f"{member_id} planar-face normal"), "face normal")
        point = _vector(face.Center(), f"{member_id} planar-face center")
        rows.append(
            {
                "face": face,
                "member_id": member_id,
                "face_index": face_index,
                "face_id": f"{member_id}/finished_face_{face_index:03d}",
                "face_shape_sha256": _source_shape_fingerprint(face),
                "plane_point_global_xyz_mm": point,
                "outward_normal_global_xyz": normal,
                "outer_wire": _wire_record(face.outerWire(), f"{member_id}/face_{face_index}/outer"),
                "inner_wires": [
                    _wire_record(wire, f"{member_id}/face_{face_index}/inner_{wire_index}")
                    for wire_index, wire in enumerate(face.innerWires())
                ],
                "bounds_global_xyz_mm": {
                    "x": [float(face.BoundingBox().xmin), float(face.BoundingBox().xmax)],
                    "y": [float(face.BoundingBox().ymin), float(face.BoundingBox().ymax)],
                    "z": [float(face.BoundingBox().zmin), float(face.BoundingBox().zmax)],
                },
            }
        )
    if not rows:
        raise ValueError(f"{member_id} has no finished planar faces")
    return rows


def _point_within_face_bounds(point: Vector, face_row: Mapping[str, Any]) -> bool:
    bounds = face_row["bounds_global_xyz_mm"]
    return all(
        bounds[axis][0] - PLANE_TOLERANCE_MM
        <= point[index]
        <= bounds[axis][1] + PLANE_TOLERANCE_MM
        for index, axis in enumerate(("x", "y", "z"))
    )


def _select_interface_face_pair(
    *,
    backer_id: str,
    backer_shape: cq.Shape,
    header_shape: cq.Shape,
    bolt_axes: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], Vector, Vector, list[Vector]]:
    backer_faces = _planar_faces(backer_shape, backer_id)
    header_faces = _planar_faces(header_shape, HEADER_ID)
    candidates = []
    for backer_face in backer_faces:
        for header_face in header_faces:
            backer_normal = backer_face["outward_normal_global_xyz"]
            header_normal = header_face["outward_normal_global_xyz"]
            if _dot(backer_normal, header_normal) > -1.0 + AXIS_ANGULAR_TOLERANCE:
                continue
            center_delta = _sub(
                header_face["plane_point_global_xyz_mm"],
                backer_face["plane_point_global_xyz_mm"],
            )
            plane_gap = abs(_dot(center_delta, backer_normal))
            if plane_gap > PLANE_TOLERANCE_MM:
                continue
            try:
                interface_points = [
                    _line_plane_intersection(
                        axis["point_global_xyz_mm"],
                        axis["direction_global_xyz"],
                        backer_face["plane_point_global_xyz_mm"],
                        backer_normal,
                        axis["label"],
                    )
                    for axis in bolt_axes
                ]
            except ValueError:
                # Other opposed planes can be real component boundaries, but
                # a parallel bolt axis cannot define this through-bolt datum.
                continue
            if not all(
                _point_within_face_bounds(point, backer_face)
                and _point_within_face_bounds(point, header_face)
                for point in interface_points
            ):
                continue
            candidates.append(
                (backer_face, header_face, backer_normal, plane_gap, interface_points)
            )
    if len(candidates) != 1:
        raise ValueError(
            f"{backer_id}/base_header requires one actual opposed finished-face pair; "
            f"found {len(candidates)}"
        )
    backer_face, header_face, outward_normal, plane_gap, interface_points = candidates[0]

    # The two members lie on opposite sides of the measured plane. Their
    # center-to-face projections fix the interface normal sense without
    # requiring their solid centroids to share the same in-plane coordinates.
    backer_center = _vector(backer_shape.Center(), f"{backer_id} solid center")
    header_center = _vector(header_shape.Center(), f"{HEADER_ID} solid center")
    backer_face_side = _dot(
        _sub(backer_face["plane_point_global_xyz_mm"], backer_center), outward_normal
    )
    header_face_side = _dot(
        _sub(header_center, header_face["plane_point_global_xyz_mm"]), outward_normal
    )
    if backer_face_side <= GEOMETRY_TOLERANCE_MM or header_face_side <= GEOMETRY_TOLERANCE_MM:
        raise ValueError(f"{backer_id}/base_header solids do not lie on opposite sides of their interface")
    contact_normal = outward_normal
    if _dot(header_face["outward_normal_global_xyz"], contact_normal) > -1.0 + AXIS_ANGULAR_TOLERANCE:
        raise ValueError(f"{backer_id}/base_header finished face normals are not opposed")
    if plane_gap > PLANE_TOLERANCE_MM:
        raise ValueError(f"{backer_id}/base_header finished face planes do not coincide")
    return backer_face, header_face, contact_normal, backer_face["plane_point_global_xyz_mm"], interface_points


def _basis(contact_normal: Vector) -> dict[str, Any]:
    preferred = (1.0, 0.0, 0.0)
    projected = _sub(preferred, _scale(_dot(preferred, contact_normal), contact_normal))
    if _norm(projected) <= 1.0e-8:
        preferred = (0.0, 1.0, 0.0)
        projected = _sub(preferred, _scale(_dot(preferred, contact_normal), contact_normal))
    u_axis = _unit(projected, "interface local u axis")
    v_axis = _unit(_cross(contact_normal, u_axis), "interface local v axis")
    if abs(_dot(_cross(u_axis, v_axis), contact_normal) - 1.0) > 1.0e-7:
        raise ValueError("interface local basis is not right-handed")
    return {
        "axis_names": ["u", "v", "n"],
        "axes_global_xyz": {
            "u": _rounded(u_axis),
            "v": _rounded(v_axis),
            "n": _rounded(contact_normal),
        },
        "basis_source": (
            "preferred global X projected into the measured interface plane; "
            "v = n cross u; n is confirmed backer-to-header by the opposed finished faces"
        ),
    }


def _member_grain_records(inventory_rows: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    header = inventory_rows.get(HEADER_ID)
    if header is None:
        raise ValueError("canonical inventory omits base_header grain record")
    header_grain = _unit(header.get("grain_axis_global_xyz", ()), "base_header grain axis")
    if header.get("delivered_stock_observed") is not False:
        raise ValueError("base_header stock-observation status changed from the canonical inventory")
    result = {
        HEADER_ID: {
            "grain_axis_global_xyz": _rounded(header_grain),
            "grain_source": f"{INVENTORY_PATH} parts[base_header].grain_axis_global_xyz",
            "grain_status": "source design datum; delivered stock not observed",
            "stock_product": header.get("stock_product"),
            "species_grade_basis": header.get("species_grade_basis"),
            "delivered_stock_observed": False,
        }
    }
    for backer_id in BACKER_IDS.values():
        result[backer_id] = {
            "grain_axis_global_xyz": [0.0, 0.0, 1.0],
            "grain_source": (
                "pinned WJ05 backer producer candidate datum: separate solid-sawn "
                "88.9 x 88.9 x 238.9 mm members, grain along global Z"
            ),
            "grain_status": "candidate design orientation; delivered stock and grain quality unobserved",
            "stock_product": "solid sawn timber candidate",
            "species_grade_basis": "DF-L No. 2 design basis; source availability not verified",
            "delivered_stock_observed": False,
        }
    return result


def _full_bolt_axis_id(trial_id: str, short_axis_id: str) -> str:
    return f"{BACKER_FAMILY}/{trial_id}/{short_axis_id}"


def _backer_bolt_records(geometry: Any) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    actual_ids = {
        axis_id
        for axis_id, bore in geometry.candidate_bores.items()
        if getattr(bore, "family", None) == BACKER_FAMILY
    }
    if actual_ids != set(EXPECTED_BOLT_AXIS_IDS):
        raise ValueError("WJ24 backer bolt axis IDs differ from the exact four-axis contract")
    physical_rows: list[dict[str, Any]] = []
    axes_by_side: dict[str, list[dict[str, Any]]] = {"left": [], "right": []}
    for short_axis_id in EXPECTED_BOLT_AXIS_IDS:
        side = short_axis_id.split("_")[2]
        expected_receivers = (BACKER_IDS[side], HEADER_ID)
        bore = geometry.candidate_bores.get(short_axis_id)
        if bore is None or (
            getattr(bore, "axis_id", None) != short_axis_id
            or getattr(bore, "family", None) != BACKER_FAMILY
            or getattr(bore, "trial_id", None) != BACKER_TRIAL_ID
            or tuple(getattr(bore, "receiver_ids", ())) != expected_receivers
            or getattr(bore, "station_id", None) != f"wj05_backer_{side}"
        ):
            raise ValueError(f"{short_axis_id}: WJ24 composed bore identity/receivers changed")
        bore_hash = _shape_sha256(bore.shape, f"{short_axis_id} composed bore")
        axis = _cylindrical_axis(bore.shape, f"{short_axis_id} composed bore")
        axis["label"] = short_axis_id
        for member_id in expected_receivers:
            receiver_shape = (
                geometry.finished_candidate_parts[member_id]
                if member_id in BACKER_IDS.values()
                else geometry.finished_hosts[member_id]
            )
            _require_member_bore_axis(
                receiver_shape,
                axis,
                member_id=member_id,
                axis_id=short_axis_id,
            )
        components = geometry.candidate_installed_hardware.get(short_axis_id)
        expected_roles = {"bottom_head", "bottom_washer", "shaft", "top_washer", "top_nut"}
        if not isinstance(components, Mapping) or set(components) != expected_roles:
            raise ValueError(f"{short_axis_id}: WJ24 modeled component role set changed")
        component_hashes = {
            str(role): _shape_sha256(shape, f"{short_axis_id}/{role}")
            for role, shape in sorted(components.items())
        }
        canonical_axis_id = _full_bolt_axis_id(BACKER_TRIAL_ID, short_axis_id)
        axis_row = {
            **axis,
            "canonical_axis_id": canonical_axis_id,
            "short_station_axis_alias": short_axis_id,
            "family": BACKER_FAMILY,
            "trial_id": BACKER_TRIAL_ID,
            "station_id": f"wj05_backer_{side}",
            "receiver_ids_head_to_nut_design_order": list(expected_receivers),
            "bore_shape_sha256": bore_hash,
        }
        axes_by_side[side].append(axis_row)
        physical_rows.append(
            {
                "physical_bolt_id": canonical_axis_id,
                "short_station_axis_alias": short_axis_id,
                "family": BACKER_FAMILY,
                "trial_id": BACKER_TRIAL_ID,
                "station_id": f"wj05_backer_{side}",
                "ordered_receiver_ids": list(expected_receivers),
                "axis_line_point_global_xyz_mm": _rounded(axis["point_global_xyz_mm"]),
                "axis_direction_global_xyz": _rounded(axis["direction_global_xyz"]),
                "axis_direction_reference": (
                    "geometric direction oriented backer-to-header; this does not verify a delivered bolt head/nut orientation"
                ),
                "composed_interface_plane_intersection_global_xyz_mm": None,
                "composed_bore_shape_sha256": bore_hash,
                "modeled_component_role_ids": sorted(components),
                "modeled_component_shape_sha256": component_hashes,
                "component_identity_limit": (
                    "CAD occupancy envelopes in the composed hypothesis; not delivered bolt, washer, nut, thread, or stack measurements"
                ),
                "hardware_selection": (
                    "unresolved; provisional ordinary-bolt geometry only, with no selected or received product identity"
                ),
                "thread_transition_status": "unresolved; no SKU/delivered thread transition or smooth-shank-through-wood proof",
                "stack_status": "unresolved; modeled component envelope is not a selected or received physical stack",
                "steel_resistance_status": "unresolved; no delivered fastener identity or applicable resistance calculation",
                "signed_wrench_owner_id": f"bolt_action:{canonical_axis_id}",
            }
        )
    return physical_rows, axes_by_side


def _fixed_hillman_records(
    geometry: Any,
    screw_rows: Mapping[str, Mapping[str, Any]],
    members: Mapping[str, cq.Shape],
) -> list[dict[str, Any]]:
    selected_rows = {axis_id: screw_rows.get(axis_id) for axis_id in EXPECTED_HILLMAN_AXIS_IDS}
    if any(row is None for row in selected_rows.values()):
        raise ValueError("canonical inventory omits one or more fixed center-kicker axes")
    if not set(EXPECTED_HILLMAN_AXIS_IDS) <= set(geometry.fixed_axes):
        raise ValueError("WJ24 composed fixed axes omit one or more center-kicker Hillman axes")
    cut_map = geometry.purchased_panel_cutters_by_candidate_part
    result = []
    for axis_id in EXPECTED_HILLMAN_AXIS_IDS:
        row = selected_rows[axis_id]
        assert row is not None
        side = axis_id.split("_")[2]
        receiver_id = BACKER_IDS[side]
        if (
            row.get("shop_opening_kind") != "hillman_panel"
            or row.get("candidate_finished_receiver_member") != receiver_id
            or row.get("source_finished_receiver_member") != f"base_post_center_{side}"
            or row.get("panel_member") != f"kicker_{side}"
            or list(row.get("members", ())) != [f"kicker_{side}", f"base_post_center_{side}"]
            or row.get("receiver_to_frame_path_complete") is not False
        ):
            raise ValueError(f"{axis_id}: canonical fixed receiver/owner record changed")
        origin = _vector(row.get("origin_global_xyz_mm", ()), f"{axis_id} source origin")
        direction = _unit(row.get("axis_global_xyz", ()), f"{axis_id} source axis")
        source_length = float(row.get("source_occupied_length_mm", 0.0))
        purchase_length = float(row.get("shop_purchased_length_mm", 0.0))
        diameter = float(row.get("source_occupied_diameter_mm", 0.0))
        _authenticate_cylinder(
            geometry.fixed_axes[axis_id],
            origin=origin,
            direction=direction,
            diameter_mm=diameter,
            length_mm=purchase_length,
            label=f"{axis_id} composed fixed occupancy axis",
        )
        cutter = cut_map.get(receiver_id, {}).get(axis_id)
        if cutter is None:
            raise ValueError(f"{axis_id}: composed purchased-length receiver cut is missing")
        cutter_hash = _shape_sha256(cutter, f"{axis_id} receiver cutter")
        _authenticate_cylinder(
            cutter,
            origin=origin,
            direction=direction,
            diameter_mm=diameter,
            length_mm=purchase_length,
            label=f"{axis_id} composed receiver cutter",
        )
        raw_receiver = members[receiver_id + "/raw"]
        finished_receiver = members[receiver_id]
        raw_intersection = cutter.intersect(raw_receiver)
        if not raw_intersection.isValid() or float(raw_intersection.Volume()) <= BOOLEAN_VOLUME_TOLERANCE_MM3:
            raise ValueError(f"{axis_id}: source purchase axis does not enter its raw candidate receiver")
        if abs(direction[0]) > AXIS_ANGULAR_TOLERANCE or abs(direction[2]) > AXIS_ANGULAR_TOLERANCE or abs(abs(direction[1]) - 1.0) > AXIS_ANGULAR_TOLERANCE:
            raise ValueError(f"{axis_id}: fixed WJ24 center-kicker axis is no longer aligned to global Y")
        box = raw_intersection.BoundingBox()
        if direction[1] < 0:
            interval = (origin[1] - box.ymax, origin[1] - box.ymin)
        else:
            interval = (box.ymin - origin[1], box.ymax - origin[1])
        interval = (max(0.0, interval[0]), min(purchase_length, interval[1]))
        if interval[1] <= interval[0]:
            raise ValueError(f"{axis_id}: receiver intersection interval is empty")
        finished_overlap = _shape_intersection_volume(
            cutter, finished_receiver, f"{axis_id} finished receiver cut check"
        )
        if finished_overlap > BOOLEAN_VOLUME_TOLERANCE_MM3:
            raise ValueError(f"{axis_id}: composed finished receiver retains modeled cutter overlap")
        entry = _add(origin, _scale(interval[0], direction))
        result.append(
            {
                "axis_id": axis_id,
                "panel_member_id": str(row["panel_member"]),
                "source_receiver_member_id": str(row["source_finished_receiver_member"]),
                "candidate_receiver_member_id": receiver_id,
                "origin_global_xyz_mm": _rounded(origin),
                "direction_global_xyz": _rounded(direction),
                "shop_purchased_length_mm": purchase_length,
                "source_occupied_length_mm": source_length,
                "source_occupied_diameter_mm": diameter,
                "occupancy_diameter_basis": (
                    "historical CAD occupancy from source inventory; not a Hillman measured diameter, pilot instruction, or resistance input"
                ),
                "fixed_axis_shape_sha256": _shape_sha256(
                    geometry.fixed_axes[axis_id], f"{axis_id} fixed axis"
                ),
                "candidate_cutter_shape_sha256": cutter_hash,
                "raw_candidate_receiver_shape_sha256": _shape_sha256(
                    raw_receiver, f"{receiver_id} raw candidate receiver"
                ),
                "finished_candidate_receiver_shape_sha256": _shape_sha256(
                    finished_receiver, f"{receiver_id} finished candidate receiver"
                ),
                "receiver_cut_status": "composed purchase cutter is present; finished receiver clears the modeled occupancy cylinder",
                "raw_receiver_intersection_interval_mm_along_purchase_axis": [
                    round(interval[0], 9),
                    round(interval[1], 9),
                ],
                "raw_receiver_full_diameter_intersection_length_mm_geometry_only": round(
                    interval[1] - interval[0], 9
                ),
                "receiver_entry_point_global_xyz_mm": _rounded(entry),
                "finished_receiver_overlap_volume_mm3_geometry_only": round(finished_overlap, 9),
                "receiver_to_frame_path_complete": False,
                "capacity_status": "unresolved; no Hillman withdrawal, lateral, group, or receiver-to-frame resistance assigned",
                "signed_wrench_owner_id": f"hillman_receiver_action:{axis_id}",
            }
        )
    return result


def _face_record(face_row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "member_id": face_row["member_id"],
        "face_id": face_row["face_id"],
        "face_index_in_finished_brep": face_row["face_index"],
        "face_shape_sha256": face_row["face_shape_sha256"],
        "plane_point_global_xyz_mm": _rounded(face_row["plane_point_global_xyz_mm"]),
        "outward_normal_global_xyz": _rounded(face_row["outward_normal_global_xyz"]),
        "trimmed_face_bounds_global_xyz_mm": face_row["bounds_global_xyz_mm"],
        "outer_wire": face_row["outer_wire"],
        "inner_wires": face_row["inner_wires"],
        "geometry_limit": "actual finished BRep face identity/trim only; not proof of active contact or load-bearing area",
    }


def _interface_records(
    geometry: Any,
    axes_by_side: Mapping[str, Sequence[Mapping[str, Any]]],
    bolt_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    bolt_by_id = {row["short_station_axis_alias"]: row for row in bolt_records}
    for side in ("left", "right"):
        backer_id = BACKER_IDS[side]
        side_axes = axes_by_side[side]
        if len(side_axes) != 2:
            raise ValueError(f"{side} backer must have exactly two physical bolt axes")
        backer_face, header_face, contact_normal, _plane_point, intersections = _select_interface_face_pair(
            backer_id=backer_id,
            backer_shape=geometry.finished_candidate_parts[backer_id],
            header_shape=geometry.finished_hosts[HEADER_ID],
            bolt_axes=side_axes,
        )
        if _dot(contact_normal, (0.0, 0.0, 1.0)) < 1.0 - 1.0e-6:
            raise ValueError(
                f"{side} actual interface normal changed; frozen WJ05 global-Z datum no longer applies"
            )
        backer_to_header = contact_normal
        for axis in side_axes:
            if _dot(axis["direction_global_xyz"], contact_normal) < 0:
                axis["direction_global_xyz"] = _scale(-1.0, axis["direction_global_xyz"])
        datum = tuple(
            math.fsum(point[index] for point in intersections) / len(intersections)
            for index in range(3)
        )
        datum = _vector(datum, f"{side} interface datum")
        basis = _basis(contact_normal)
        short_axis_ids = [row["label"] for row in side_axes]
        canonical_axis_ids = [bolt_by_id[axis_id]["physical_bolt_id"] for axis_id in short_axis_ids]
        plane_separation = abs(
            _dot(
                _sub(header_face["plane_point_global_xyz_mm"], backer_face["plane_point_global_xyz_mm"]),
                contact_normal,
            )
        )
        for short_axis_id, point, canonical_axis_id in zip(
            short_axis_ids, intersections, canonical_axis_ids, strict=True
        ):
            bolt_by_id[short_axis_id]["composed_interface_plane_intersection_global_xyz_mm"] = _rounded(point)
            bolt_by_id[short_axis_id]["axis_direction_global_xyz"] = _rounded(
                next(axis["direction_global_xyz"] for axis in side_axes if axis["label"] == short_axis_id)
            )
            bolt_by_id[short_axis_id]["signed_wrench_owner_id"] = f"bolt_action:{canonical_axis_id}"
        result.append(
            {
                "interface_id": f"wj05_backer_{side}__base_header",
                "backer_member_id": backer_id,
                "header_member_id": HEADER_ID,
                "ordered_member_ids_backer_to_header": [backer_id, HEADER_ID],
                "physical_interface_datum_id": f"wj05_backer_{side}/interface_datum",
                "datum_global_xyz_mm": _rounded(datum),
                "datum_basis": basis,
                "backer_finished_face": _face_record(backer_face),
                "header_finished_face": _face_record(header_face),
                "backer_face_plane_gap_mm_geometry_only": round(plane_separation, 9),
                "contact_status": (
                    "composed finished faces are geometrically coincident and opposed; "
                    "active contact, tolerance, separation/opening, and load-bearing area are unresolved"
                ),
                "active_contact_area_assigned": False,
                "bolt_axis_ids": canonical_axis_ids,
                "short_station_axis_aliases": short_axis_ids,
                "bolt_centerline_interface_intersections_global_xyz_mm": [
                    _rounded(point) for point in intersections
                ],
                "bolt_group_centroid_datum_basis": (
                    "arithmetic centroid of the two composed bore centerline intersections with the actual opposed finished-face plane"
                ),
                "backer_to_header_direction_global_xyz": _rounded(backer_to_header),
                "backer_to_header_contact_normal_global_xyz": _rounded(contact_normal),
                "signed_wrench_owner_id": f"backer_header_joint_action:wj05_backer_{side}",
            }
        )
    return result


def _wrench_owner_rows(
    hillman_rows: Sequence[Mapping[str, Any]],
    bolt_rows: Sequence[Mapping[str, Any]],
    interface_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    owners = []
    for row in hillman_rows:
        owners.append(
            {
                "owner_id": row["signed_wrench_owner_id"],
                "owner_kind": "fixed_hillman_load_entry_axis",
                "canonical_axis_id": row["axis_id"],
                "member_or_joint_id": row["candidate_receiver_member_id"],
                "action_on": row["candidate_receiver_member_id"],
                "datum_global_xyz_mm": row["receiver_entry_point_global_xyz_mm"],
                "basis_global_xyz": {"x": [1.0, 0.0, 0.0], "y": [0.0, 1.0, 0.0], "z": [0.0, 0.0, 1.0]},
                "component_schema": {
                    "force_global_N": ["Fx", "Fy", "Fz"],
                    "moment_global_Nmm": ["Mx", "My", "Mz"],
                },
                "actions_by_case_id": None,
                "action_status": "signed demand and four-screw load sharing not imported",
            }
        )
    for row in bolt_rows:
        owners.append(
            {
                "owner_id": row["signed_wrench_owner_id"],
                "owner_kind": "physical_bolt_axis",
                "canonical_axis_id": row["physical_bolt_id"],
                "member_or_joint_id": row["physical_bolt_id"],
                "action_on": "physical bolt axis; bolt/member interaction distribution unresolved",
                "datum_global_xyz_mm": row["composed_interface_plane_intersection_global_xyz_mm"],
                "basis_global_xyz": {"x": [1.0, 0.0, 0.0], "y": [0.0, 1.0, 0.0], "z": [0.0, 0.0, 1.0]},
                "component_schema": {
                    "force_global_N": ["Fx", "Fy", "Fz"],
                    "moment_global_Nmm": ["Mx", "My", "Mz"],
                },
                "actions_by_case_id": None,
                "action_status": "no signed bolt actions or group distribution imported",
            }
        )
    for row in interface_rows:
        owners.append(
            {
                "owner_id": row["signed_wrench_owner_id"],
                "owner_kind": "complete_backer_header_joint_interface",
                "canonical_axis_id": None,
                "member_or_joint_id": row["interface_id"],
                "action_on": row["backer_member_id"],
                "datum_global_xyz_mm": row["datum_global_xyz_mm"],
                "basis_global_xyz": row["datum_basis"]["axes_global_xyz"],
                "component_schema": {
                    "force_global_N": ["Fx", "Fy", "Fz"],
                    "moment_global_Nmm": ["Mx", "My", "Mz"],
                },
                "actions_by_case_id": None,
                "action_status": "no fresh WJ09 complete-frame signed interface action imported",
            }
        )
    return owners


def build_mechanics_contract(geometry: Any) -> dict[str, Any]:
    """Extract bounded WJ24 geometry mechanics inputs without assigning actions."""
    if getattr(geometry, "layout_id", None) != LAYOUT_ID:
        raise ValueError("mechanics contract requires the pinned WJ24 layout")
    if getattr(geometry, "trial_id", None) != COMPOSITION_TRIAL_ID:
        raise ValueError("mechanics contract requires the pinned WJ24 composition trial")
    if getattr(geometry, "status", None) != "unaccepted_integrated_hypothesis":
        raise ValueError("mechanics contract requires an unaccepted WJ24 composition")
    inventory_hash = _sha256_file(INVENTORY_PATH)
    if getattr(geometry, "source_inventory_sha256", None) != inventory_hash:
        raise ValueError("WJ24 source inventory hash differs from the canonical file")
    canonical_inventory = json.loads((ROOT / INVENTORY_PATH).read_text())
    if dict(geometry.source_inventory) != canonical_inventory:
        raise ValueError("WJ24 source inventory content differs from the canonical file")
    source_inputs = _current_hash_map(
        getattr(geometry, "source_inputs_sha256", None), "WJ24 composed"
    )
    family_fingerprints = getattr(geometry, "family_source_fingerprints", None)
    family_trials = getattr(geometry, "family_trial_ids", None)
    if not isinstance(family_fingerprints, Mapping) or not isinstance(family_trials, Mapping):
        raise TypeError("WJ24 family source binding is missing")
    wj05_sources = _current_hash_map(
        family_fingerprints.get(BACKER_SOURCE_BUNDLE), "WJ05 backer source bundle"
    )
    if family_trials.get(BACKER_FAMILY) != BACKER_TRIAL_ID:
        raise ValueError("WJ24 backer family trial differs from the pinned WJ05 trial")
    if wj05_sources.get("scripts/wood_joints_wj05_center_backer_transfer_probe.py") is None:
        raise ValueError("WJ24 compact-outer source bundle omits the WJ05 backer producer")
    if any(source_inputs.get(path) != digest for path, digest in wj05_sources.items()):
        raise ValueError("WJ24 merged source closure differs from the retained WJ05 family binding")

    inventory_rows = _inventory_rows(canonical_inventory, "parts", "part_id")
    screw_rows = _inventory_rows(canonical_inventory, "fixed_panel_kicker_screws", "axis_id")
    if len(screw_rows) != 66 or set(geometry.fixed_axes) != set(screw_rows):
        raise ValueError("WJ24 fixed panel/kicker axis identities differ from the canonical 66-axis set")
    backer_grains = _member_grain_records(inventory_rows)
    required_finished = {HEADER_ID, *BACKER_IDS.values()}
    if not required_finished <= set(geometry.finished_hosts) | set(geometry.finished_candidate_parts):
        raise ValueError("WJ24 composed geometry omits a finished backer/header member")
    if HEADER_ID not in geometry.raw_hosts:
        raise ValueError("WJ24 composed geometry omits the raw base_header")
    if not set(BACKER_IDS.values()) <= set(geometry.raw_candidate_parts):
        raise ValueError("WJ24 composed geometry omits one or more raw backers")
    finished_shapes = {
        HEADER_ID: geometry.finished_hosts[HEADER_ID],
        **{backer_id: geometry.finished_candidate_parts[backer_id] for backer_id in BACKER_IDS.values()},
    }
    raw_shapes = {
        HEADER_ID: geometry.raw_hosts[HEADER_ID],
        **{backer_id: geometry.raw_candidate_parts[backer_id] for backer_id in BACKER_IDS.values()},
    }
    member_shapes: dict[str, cq.Shape] = {
        **finished_shapes,
        **{f"{backer_id}/raw": raw_shapes[backer_id] for backer_id in BACKER_IDS.values()},
    }
    member_records = {}
    shape_hashes = {}
    for member_id in (HEADER_ID, BACKER_IDS["left"], BACKER_IDS["right"]):
        finished_hash = _shape_sha256(finished_shapes[member_id], f"{member_id} finished member")
        raw_hash = _shape_sha256(raw_shapes[member_id], f"{member_id} raw member")
        shape_hashes[member_id] = finished_hash
        member_records[member_id] = {
            "member_id": member_id,
            "member_role": "shared WJ24 source host" if member_id == HEADER_ID else "candidate backer receiver",
            "raw_shape_sha256": raw_hash,
            "finished_shape_sha256": finished_hash,
            **backer_grains[member_id],
        }

    bolt_rows, axes_by_side = _backer_bolt_records(geometry)
    hillman_rows = _fixed_hillman_records(geometry, screw_rows, member_shapes)
    interfaces = _interface_records(geometry, axes_by_side, bolt_rows)
    owner_rows = _wrench_owner_rows(hillman_rows, bolt_rows, interfaces)

    return {
        "schema": SCHEMA,
        "status": "bounded_mechanics_inputs_only",
        "scope": (
            "two WJ24 center-kicker backer-to-header joints, four provisional through-bolt axes, "
            "and four fixed Hillman center-kicker load-entry axes"
        ),
        "composition": {
            "layout_id": LAYOUT_ID,
            "trial_id": COMPOSITION_TRIAL_ID,
            "status": geometry.status,
            "source_inventory_sha256": inventory_hash,
            "source_inputs_sha256": source_inputs,
            "family_trial_ids": dict(sorted((str(k), str(v)) for k, v in family_trials.items())),
            "wj05_backer_source_bundle": BACKER_SOURCE_BUNDLE,
            "wj05_backer_source_fingerprints_sha256": wj05_sources,
            "relevant_finished_shape_sha256": dict(sorted(shape_hashes.items())),
        },
        "physical_inventory": {
            "backer_header_interfaces": len(interfaces),
            "ordinary_physical_bolts": len(bolt_rows),
            "fixed_hillman_load_entry_axes": len(hillman_rows),
            "fixed_panel_axis_count_in_composition": len(geometry.fixed_axes),
            "modeled_component_shapes_for_backer_bolts": sum(
                len(row["modeled_component_role_ids"]) for row in bolt_rows
            ),
            "scope_does_not_cover": (
                "other WJ24 duties, downstream center-post/principal-cleat paths, the whole frame, "
                "native analysis, actual installation, or any capacity/release determination"
            ),
        },
        "members": member_records,
        "physical_interfaces": interfaces,
        "physical_bolts": bolt_rows,
        "fixed_hillman_load_entry_axes": hillman_rows,
        "signed_wrench_owners": {
            "global_sign_convention": (
                "positive force components act along the listed basis axes; positive moments follow the right-hand rule; "
                "each owner row names the body receiving the action"
            ),
            "local_basis_convention": (
                "Hillman and bolt-axis owners use global XYZ; interface owners use their measured right-handed u/v/n basis"
            ),
            "action_source_status": "no fresh WJ09 signed case actions imported",
            "action_source": "fresh source-bound complete-frame demand extraction is still required",
            "component_units": {
                "force": "N",
                "moment": "N*mm",
            },
            "component_names": ["Fx", "Fy", "Fz", "Mx", "My", "Mz"],
            "owners": owner_rows,
            "allocation_limit": (
                "owner identities and reference datums are defined; no distribution among Hillman axes, bolts, "
                "fastener shank/thread, or contact is inferred"
            ),
        },
        "unresolved_mechanics_inputs": {
            "fresh_complete_frame_signed_actions": "missing; WJ09 source-bound fresh demand extraction required",
            "hillman_axis_load_allocation": "missing; no per-screw action or group sharing is assigned",
            "bolt_identity_thread_transition_and_delivered_smooth_shank": "missing; no SKU, measured thread runout, delivered body section, or through-wood smooth-shank proof",
            "bolt_nut_washer_stack_and_preload": "missing; CAD envelopes do not define received stack, nut engagement, snug/preload, or installation state",
            "bolt_steel_and_wood_resistance": "missing; no delivered fastener properties or applicable resistance calculation",
            "bolt_group_distribution_and_joint_stiffness": "missing; no adopted axial/lateral/rotational stiffness or group response model",
            "active_contact_gap_opening_and_pressure": "missing; coincident geometric faces do not establish active contact, gap tolerance, opening law, bearing area, or pressure distribution",
            "net_sections_and_loaded_edge_end_distances": "not evaluated; identify actual governing section cuts and loaded edges from signed actions before applying an applicable wood method",
            "backer_cut_effects_and_screw_resistance": "missing; actual WJ24 receiver cuts are bound, but no Hillman withdrawal/lateral/group resistance is assigned",
            "header_transfer_and_downstream_compatibility": "missing; complete eccentric backer-to-header and center-frame transfer remains outside this geometry input contract",
            "received_stock_and_grain_quality": "missing; DF-L No. 2 is a design basis, not received-stock inspection or property verification",
        },
        "method_boundary": {
            "inherited_unit_statics_or_synthetic_wrenches_as_demand": False,
            "capacity_methods_evaluated": False,
            "contact_area_or_bearing_credit_assigned": False,
            "fresh_global_frame_actions_provided": False,
            "criteria_method_map": "docs/wood-joints-mvp/criteria-method-map.md",
        },
        "claims": {
            "capacity_established": False,
            "contact_or_bearing_capacity_established": False,
            "wood_net_section_adequacy_established": False,
            "fastener_thread_or_stack_adequacy_established": False,
            "hillman_receiver_capacity_established": False,
            "native_analysis_ready": False,
            "whole_candidate_complete": False,
            "fabrication_released": False,
            "structural_release": False,
        },
    }
