"""Resolve positive diagnostic load patches on owned C3D10/TRI6 interfaces.

This module clips one finite quadratic-triangle surface against another using
explicit mesh face references. Quadratic faces are tessellated in reference
space into convex, planar microtriangles; candidate finite faces therefore
retain their mesh-resolved holes and nonconvex boundary. The result is a
diagnostic mesh load patch, not a CAD-exact footprint or a contact-pressure
field. It does not prepare a solver deck, select restraints, or solve a model.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from fea.floor_contact import FACES
from fea.wood_joint_patch_unit_cases import (
    EXPECTED_OWNER_PAIRS,
    DistributedUnitCase,
    PatchNodeWeight,
    UnitWrenchCase,
    distribute_unit_case_to_nodes,
    distribute_wrench_to_nodes,
)
from fea.wood_joint_patch_wrench import Wrench

SCHEMA = "wood_joint_patch_load_patch/v1"
CONTACT_SCHEMA = "wood_joint_wj04_patch_contact_contract/v1"
DEFAULT_SUBDIVISIONS = 8
DEFAULT_AREA_ABSOLUTE_TOLERANCE_MM2 = 0.5
DEFAULT_AREA_RELATIVE_TOLERANCE = 5e-4
DEFAULT_REFINEMENT_RELATIVE_TOLERANCE = 5e-4
DEFAULT_CENTROID_TOLERANCE_MM = 1e-3
DEFAULT_PLANE_TOLERANCE_MM = 1e-5
DEFAULT_NORMAL_ALIGNMENT = 0.95
DEFAULT_CLIP_TOLERANCE_MM = 1e-9

Vector = tuple[float, float, float]
Point2 = tuple[float, float]
NodeId = int
FaceRef = tuple[int, int]


def _vector(value: Any, label: str) -> Vector:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{label} must be a finite XYZ vector")
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must be a finite XYZ vector") from error
    if len(result) != 3 or not all(math.isfinite(component) for component in result):
        raise ValueError(f"{label} must be a finite XYZ vector")
    return result  # type: ignore[return-value]


def _positive(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be positive and finite")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must be positive and finite") from error
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{label} must be positive and finite")
    return number


def _nonnegative(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be nonnegative and finite")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must be nonnegative and finite") from error
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"{label} must be nonnegative and finite")
    return number


def _name(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def _sub(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _add(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _scale(value: Sequence[float], amount: float) -> Vector:
    return tuple(amount * component for component in value)  # type: ignore[return-value]


def _cross(left: Sequence[float], right: Sequence[float]) -> Vector:
    a = _vector(left, "left vector")
    b = _vector(right, "right vector")
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(value: Sequence[float]) -> float:
    return math.sqrt(_dot(value, value))


def _unit(value: Sequence[float], label: str) -> Vector:
    vector = _vector(value, label)
    length = _norm(vector)
    if not math.isfinite(length) or length <= 1e-12:
        raise ValueError(f"{label} must be nonzero")
    return _scale(vector, 1.0 / length)


@dataclass(frozen=True)
class Tri6Surface:
    """Caller-authenticated owner and exact six-node C3D10 face references."""

    owner_body: str
    face_refs: tuple[FaceRef, ...]
    tri6_node_ids: tuple[NodeId, ...]
    outward_normal_global_xyz: Vector
    label: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "owner_body", _name(self.owner_body, "surface owner"))
        object.__setattr__(self, "label", _name(self.label, "surface label"))
        refs = tuple(tuple(int(value) for value in ref) for ref in self.face_refs)
        if not refs or any(len(ref) != 2 for ref in refs):
            raise ValueError("surface must contain element/side references")
        if any(element <= 0 or side not in {1, 2, 3, 4} for element, side in refs):
            raise ValueError(
                "C3D10 face references require positive elements and sides 1–4"
            )
        if len(refs) != len(set(refs)):
            raise ValueError("surface face references must be unique")
        object.__setattr__(self, "face_refs", refs)
        node_ids = tuple(int(value) for value in self.tri6_node_ids)
        if not node_ids or any(node <= 0 for node in node_ids):
            raise ValueError("surface TRI6 node IDs must be positive and nonempty")
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("surface TRI6 node IDs must be unique")
        object.__setattr__(self, "tri6_node_ids", node_ids)
        object.__setattr__(
            self,
            "outward_normal_global_xyz",
            _unit(self.outward_normal_global_xyz, "surface outward normal"),
        )


@dataclass(frozen=True)
class MeshTopology:
    """Mesh coordinates and exact per-body ownership from one frozen mesh."""

    node_xyz_mm: Mapping[int, Sequence[float]]
    elements_by_owner: Mapping[str, Mapping[int, Sequence[int]]]
    owner_node_ids: Mapping[str, Sequence[int]]


@dataclass(frozen=True)
class InterfacePatchBinding:
    """WJ04 semantic pair and source datum extracted from a contact manifest."""

    interface_id: str
    datum_xyz_mm: Vector
    finite_common_area_mm2: float
    host_surface: Tri6Surface
    cleat_surface: Tri6Surface
    source_hashes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class LoadPatchSide:
    """Positive nodal tributary areas on one clipped interface side."""

    owner_body: str
    surface_label: str
    node_weights: tuple[PatchNodeWeight, ...]
    geometric_area_mm2: float
    geometric_centroid_xyz_mm: Vector
    nodal_area_centroid_xyz_mm: Vector
    nodal_centroid_error_mm: float
    scaled_gram_relative_pivot: float


@dataclass(frozen=True)
class SurfaceOverlayResult:
    """Mesh-linearized common patch on both independently owned surfaces."""

    candidate_surface_area_mm2: float
    host_surface_area_mm2: float
    common_area_mm2: float
    common_centroid_xyz_mm: Vector
    candidate_patch: LoadPatchSide
    host_patch: LoadPatchSide
    subdivisions: int
    coarse_subdivisions: int
    coarse_common_area_mm2: float
    refinement_relative_change: float
    candidate_area_source_error_mm2: float | None
    host_common_area_error_mm2: float
    common_centroid_side_error_mm: float
    maximum_plane_residual_mm: float
    maximum_normal_alignment_residual: float


@dataclass(frozen=True)
class ResolvedInterfaceLoadPatch:
    """One source-bound interface with checked positive nodal load patches."""

    binding: InterfacePatchBinding
    overlay: SurfaceOverlayResult


@dataclass(frozen=True)
class _MicroTriangle:
    owner_body: str
    face_ref: FaceRef
    face_node_ids: tuple[int, ...]
    points_2d: tuple[Point2, Point2, Point2]
    face_barycentric_vertices: tuple[Vector, Vector, Vector]


@dataclass(frozen=True)
class _SurfaceGeometry:
    triangles: tuple[_MicroTriangle, ...]
    area_mm2: float
    centroid_xyz_mm: Vector
    area_weights_mm2: Mapping[int, float]


def _parse_face_side(
    value: Any,
    *,
    owner_body: str,
    label: str,
    normal: Sequence[float],
) -> Tri6Surface:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} contact surface must be an object")
    if value.get("owner_body") != owner_body:
        raise ValueError(
            f"{label} surface owner does not match semantic interface owner"
        )
    refs = value.get("remapped_face_refs")
    node_ids = value.get("remapped_face_node_ids")
    if refs is None or node_ids is None:
        raise ValueError(f"{label} surface lacks remapped TRI6 references or nodes")
    if not isinstance(refs, list) or not isinstance(node_ids, list):
        raise TypeError(f"{label} remapped TRI6 references and nodes must be lists")
    return Tri6Surface(
        owner_body,
        tuple(tuple(row) for row in refs),
        tuple(node_ids),
        _vector(normal, f"{label} surface normal"),
        label,
    )


def interface_patch_binding_from_contact_manifest(
    manifest: Mapping[str, Any], interface_id: str
) -> InterfacePatchBinding:
    """Resolve one of the four named WJ04 host/cleat pairs from the adapter."""

    if not isinstance(manifest, Mapping):
        raise TypeError("contact manifest must be an object")
    if manifest.get("schema") != CONTACT_SCHEMA:
        raise ValueError("unexpected WJ04 contact-manifest schema")
    if interface_id not in EXPECTED_OWNER_PAIRS:
        raise ValueError(f"unknown WJ16/WJ04 interface {interface_id!r}")
    ownership = manifest.get("surface_ownership")
    if ownership is None:
        raise ValueError("contact manifest lacks surface ownership")
    if not isinstance(ownership, Mapping):
        raise TypeError("contact manifest surface ownership must be an object")
    interface_owners = ownership.get("physical_interface_owners")
    footprints = ownership.get("wood_contact_footprints")
    if interface_owners is None or footprints is None:
        raise ValueError("contact manifest lacks semantic interface bindings")
    if not isinstance(interface_owners, Mapping) or not isinstance(footprints, Mapping):
        raise TypeError("contact manifest semantic interface bindings must be objects")
    semantic = interface_owners.get(interface_id)
    footprint = footprints.get(interface_id)
    if semantic is None or footprint is None:
        raise ValueError(f"contact manifest omits interface {interface_id!r}")
    if not isinstance(semantic, Mapping) or not isinstance(footprint, Mapping):
        raise TypeError(
            f"contact manifest interface {interface_id!r} bindings must be objects"
        )
    host_body, cleat_body = EXPECTED_OWNER_PAIRS[interface_id]
    ordered_members = semantic.get("ordered_members_head_to_nut")
    if (
        not isinstance(ordered_members, list)
        or len(ordered_members) != 2
        or set(ordered_members) != {host_body, cleat_body}
    ):
        raise ValueError(f"interface {interface_id!r} source owner order changed")
    datum = _vector(
        semantic.get("source_datum_origin_global_xyz_mm"),
        "source interface datum",
    )
    area = _positive(footprint.get("finite_common_area_mm2"), "finite common area")
    pair_id = _name(footprint.get("pair_id"), "wood contact pair ID")
    pair_rows = manifest.get("contact_pairs")
    if pair_rows is None:
        raise ValueError("contact manifest lacks contact-pair rows")
    if not isinstance(pair_rows, list):
        raise TypeError("contact manifest contact-pair rows must be a list")
    matching = [
        row
        for row in pair_rows
        if isinstance(row, Mapping)
        and row.get("pair_id") == pair_id
        and row.get("interface_id") == interface_id
        and row.get("category") == "wood_wood_interface"
    ]
    if len(matching) != 1:
        raise ValueError(f"interface {interface_id!r} contact pair ID is not unique")
    pair = matching[0]
    normal_audit = pair.get("normal_audit")
    if (
        not isinstance(normal_audit, Mapping)
        or normal_audit.get("mode") != "opposed_planar"
        or normal_audit.get("passed") is not True
    ):
        raise ValueError(
            f"interface {interface_id!r} lacks an opposed planar normal audit"
        )
    candidate = _parse_face_side(
        footprint.get("candidate_cleat_contact_side"),
        owner_body=cleat_body,
        label="cleat",
        normal=normal_audit.get("slave_mean_outward_normal_xyz"),
    )
    host = _parse_face_side(
        footprint.get("host_contact_side"),
        owner_body=host_body,
        label="host",
        normal=normal_audit.get("master_mean_outward_normal_xyz"),
    )
    raw_hashes = manifest.get("source_hashes", {})
    if not isinstance(raw_hashes, Mapping):
        raise TypeError("contact source hashes must be an object")
    source_hashes = tuple(
        sorted((str(key), str(value)) for key, value in raw_hashes.items())
    )
    return InterfacePatchBinding(
        interface_id,
        datum,
        area,
        host,
        candidate,
        source_hashes,
    )


def _bary_point(values: Sequence[Vector], weights: Sequence[float]) -> Vector:
    return tuple(
        math.fsum(weights[index] * values[index][axis] for index in range(3))
        for axis in range(3)
    )  # type: ignore[return-value]


def _q2_point(face_xyz: Sequence[Vector], barycentric: Vector) -> Vector:
    a, b, c = barycentric
    shape = (
        a * (2.0 * a - 1.0),
        b * (2.0 * b - 1.0),
        c * (2.0 * c - 1.0),
        4.0 * a * b,
        4.0 * b * c,
        4.0 * c * a,
    )
    return tuple(
        math.fsum(shape[index] * face_xyz[index][axis] for index in range(6))
        for axis in range(3)
    )  # type: ignore[return-value]


def _reference_cells(subdivisions: int):
    def point(i: int, j: int) -> Vector:
        return (
            (subdivisions - i - j) / subdivisions,
            i / subdivisions,
            j / subdivisions,
        )

    for i in range(subdivisions):
        for j in range(subdivisions - i):
            first = point(i, j)
            second = point(i + 1, j)
            third = point(i, j + 1)
            yield (first, second, third)
            if i + j < subdivisions - 1:
                yield (second, point(i + 1, j + 1), third)


def _plane_basis(normal: Vector) -> tuple[Vector, Vector]:
    reference = min(
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        key=lambda axis: abs(_dot(axis, normal)),
    )
    tangent = _unit(_cross(normal, reference), "plane tangent")
    second = _unit(_cross(normal, tangent), "plane second tangent")
    return tangent, second


def _to_2d(point: Vector, origin: Vector, basis: tuple[Vector, Vector]) -> Point2:
    offset = _sub(point, origin)
    return (_dot(offset, basis[0]), _dot(offset, basis[1]))


def _face_normal_and_points(
    owner_body: str,
    face_ref: FaceRef,
    connectivity: Sequence[int],
    node_xyz: Mapping[int, Vector],
) -> tuple[Vector, tuple[int, ...], tuple[Vector, ...]]:
    element, side = face_ref
    if len(connectivity) != 10 or len(set(connectivity)) != 10:
        raise ValueError(f"{owner_body}/{element}: expected ten distinct C3D10 nodes")
    face_indices = FACES[side - 1]
    face_node_ids = tuple(int(connectivity[index]) for index in face_indices)
    face_xyz = tuple(node_xyz[node] for node in face_node_ids)
    first, second, third = face_xyz[:3]
    normal_raw = _cross(_sub(second, first), _sub(third, first))
    magnitude = _norm(normal_raw)
    if not math.isfinite(magnitude) or magnitude <= 1e-12:
        raise ValueError(f"{owner_body}/{element}/S{side}: degenerate C3D10 face")
    normal = _scale(normal_raw, 1.0 / magnitude)
    face_corner_indices = {face_indices[0], face_indices[1], face_indices[2]}
    opposite_indices = [index for index in range(4) if index not in face_corner_indices]
    if len(opposite_indices) != 1:
        raise ValueError(
            f"{owner_body}/{element}/S{side}: invalid C3D10 face corner map"
        )
    opposite = node_xyz[int(connectivity[opposite_indices[0]])]
    face_center = _scale(_add(_add(first, second), third), 1.0 / 3.0)
    if _dot(normal, _sub(opposite, face_center)) > 0.0:
        normal = _scale(normal, -1.0)
    return normal, face_node_ids, face_xyz


def _validate_mesh_ownership(
    mesh: MeshTopology,
    surfaces: tuple[Tri6Surface, Tri6Surface],
    *,
    expected_owner_pair: tuple[str, str] | None,
) -> tuple[dict[int, Vector], dict[str, dict[int, tuple[int, ...]]]]:
    if not isinstance(mesh.node_xyz_mm, Mapping):
        raise TypeError("mesh node coordinates must be keyed by global node ID")
    if not isinstance(mesh.elements_by_owner, Mapping) or not isinstance(
        mesh.owner_node_ids, Mapping
    ):
        raise TypeError("mesh owner elements and node IDs must be mappings")
    owners = tuple(dict.fromkeys(surface.owner_body for surface in surfaces))
    if len(owners) != 2 or owners[0] == owners[1]:
        raise ValueError("interface sides must have two different owner bodies")
    if (
        expected_owner_pair is not None
        and tuple(surface.owner_body for surface in surfaces) != expected_owner_pair
    ):
        raise ValueError("surface owner order differs from semantic host/cleat pair")
    node_xyz: dict[int, Vector] = {}
    for raw_node, raw_xyz in mesh.node_xyz_mm.items():
        if isinstance(raw_node, bool):
            raise TypeError("mesh node IDs must be positive integers")
        node = int(raw_node)
        if node <= 0 or node in node_xyz:
            raise ValueError("mesh node IDs must be unique positive integers")
        node_xyz[node] = _vector(raw_xyz, f"mesh node {node}")
    owner_nodes: dict[str, set[int]] = {}
    elements_by_owner: dict[str, dict[int, tuple[int, ...]]] = {}
    seen_elements: set[int] = set()
    for owner in owners:
        if owner not in mesh.owner_node_ids or owner not in mesh.elements_by_owner:
            raise ValueError(f"mesh ownership omits interface body {owner!r}")
        nodes = tuple(int(value) for value in mesh.owner_node_ids[owner])
        if (
            not nodes
            or len(nodes) != len(set(nodes))
            or any(node <= 0 for node in nodes)
        ):
            raise ValueError(
                f"{owner}: body node inventory is empty, duplicated, or invalid"
            )
        if not set(nodes) <= node_xyz.keys():
            raise ValueError(
                f"{owner}: body node inventory references missing coordinates"
            )
        owner_nodes[owner] = set(nodes)
        elements = mesh.elements_by_owner[owner]
        if not isinstance(elements, Mapping) or not elements:
            raise ValueError(f"{owner}: body C3D10 inventory is empty")
        normalized_elements: dict[int, tuple[int, ...]] = {}
        for raw_element, raw_connectivity in elements.items():
            element = int(raw_element)
            if element <= 0 or element in seen_elements:
                raise ValueError(
                    "C3D10 element IDs must be positive and globally disjoint"
                )
            connectivity = tuple(int(node) for node in raw_connectivity)
            if len(connectivity) != 10 or len(set(connectivity)) != 10:
                raise ValueError(f"{owner}/{element}: invalid C3D10 connectivity")
            if not set(connectivity) <= owner_nodes[owner]:
                raise ValueError(
                    f"{owner}/{element}: element nodes disagree with body owner"
                )
            normalized_elements[element] = connectivity
            seen_elements.add(element)
        if {
            node for row in normalized_elements.values() for node in row
        } != owner_nodes[owner]:
            raise ValueError(
                f"{owner}: body node inventory differs from C3D10 connectivity"
            )
        elements_by_owner[owner] = normalized_elements
    if owner_nodes[owners[0]] & owner_nodes[owners[1]]:
        raise ValueError("independent interface bodies share global mesh node IDs")
    for surface in surfaces:
        if not set(surface.tri6_node_ids) <= owner_nodes[surface.owner_body]:
            raise ValueError(f"{surface.label}: TRI6 nodes do not belong to their body")
        observed_nodes: set[int] = set()
        face_counts: dict[tuple[int, ...], int] = defaultdict(int)
        owner_elements = elements_by_owner[surface.owner_body]
        for connectivity in owner_elements.values():
            for side, indices in enumerate(FACES, start=1):
                key = tuple(sorted(connectivity[index] for index in indices))
                face_counts[key] += 1
        for element, side in surface.face_refs:
            if element not in owner_elements:
                raise ValueError(
                    f"{surface.label}: face element {element} does not belong to {surface.owner_body}"
                )
            connectivity = owner_elements[element]
            face_nodes = tuple(connectivity[index] for index in FACES[side - 1])
            face_key = tuple(sorted(face_nodes))
            if face_counts[face_key] != 1:
                raise ValueError(
                    f"{surface.label}: referenced face is not an exterior face"
                )
            observed_nodes.update(face_nodes)
        if observed_nodes != set(surface.tri6_node_ids):
            raise ValueError(
                f"{surface.label}: declared surface node set differs from exact TRI6 face union"
            )
        if not observed_nodes <= node_xyz.keys():
            raise ValueError(
                f"{surface.label}: TRI6 face references a missing node coordinate"
            )
    return node_xyz, elements_by_owner


def _polygon_area_centroid(points: Sequence[Point2]) -> tuple[float, Point2]:
    if len(points) < 3:
        return 0.0, (0.0, 0.0)
    twice_area = 0.0
    cx = 0.0
    cy = 0.0
    for index, point in enumerate(points):
        following = points[(index + 1) % len(points)]
        cross = point[0] * following[1] - following[0] * point[1]
        twice_area += cross
        cx += (point[0] + following[0]) * cross
        cy += (point[1] + following[1]) * cross
    if abs(twice_area) <= 1e-24:
        return 0.0, (0.0, 0.0)
    signed_area = 0.5 * twice_area
    return abs(signed_area), (cx / (3.0 * twice_area), cy / (3.0 * twice_area))


def _triangle_area_2d(points: Sequence[Point2]) -> float:
    return 0.5 * abs(
        (points[1][0] - points[0][0]) * (points[2][1] - points[0][1])
        - (points[1][1] - points[0][1]) * (points[2][0] - points[0][0])
    )


def _triangle_centroid_2d(points: Sequence[Point2]) -> Point2:
    return (
        math.fsum(point[0] for point in points) / 3.0,
        math.fsum(point[1] for point in points) / 3.0,
    )


def _signed_edge_distance(edge_a: Point2, edge_b: Point2, point: Point2) -> float:
    edge = (edge_b[0] - edge_a[0], edge_b[1] - edge_a[1])
    offset = (point[0] - edge_a[0], point[1] - edge_a[1])
    edge_length = math.hypot(*edge)
    if edge_length <= 1e-15:
        raise ValueError("mesh-linearized clip triangle has a zero-length edge")
    return (edge[0] * offset[1] - edge[1] * offset[0]) / edge_length


def _clean_polygon(points: Sequence[Point2], tolerance: float) -> list[Point2]:
    result: list[Point2] = []
    for point in points:
        if not result or math.dist(point, result[-1]) > tolerance:
            result.append(point)
    if len(result) > 1 and math.dist(result[0], result[-1]) <= tolerance:
        result.pop()
    return result


def _clip_triangle(
    subject: Sequence[Point2], clip: Sequence[Point2], tolerance_mm: float
) -> list[Point2]:
    clip_points = list(clip)
    if _polygon_area_centroid(clip_points)[0] <= 1e-20:
        return []
    # Normalize the clipping triangle to counter-clockwise orientation.
    signed_area2 = sum(
        clip_points[index][0] * clip_points[(index + 1) % 3][1]
        - clip_points[(index + 1) % 3][0] * clip_points[index][1]
        for index in range(3)
    )
    if signed_area2 < 0.0:
        clip_points.reverse()
    output = list(subject)
    for index, edge_a in enumerate(clip_points):
        edge_b = clip_points[(index + 1) % 3]
        incoming = output
        output = []
        if not incoming:
            break
        previous = incoming[-1]
        previous_distance = _signed_edge_distance(edge_a, edge_b, previous)
        for current in incoming:
            current_distance = _signed_edge_distance(edge_a, edge_b, current)
            previous_inside = previous_distance >= -tolerance_mm
            current_inside = current_distance >= -tolerance_mm
            if previous_inside != current_inside:
                denominator = previous_distance - current_distance
                if abs(denominator) > 1e-15:
                    ratio = previous_distance / denominator
                    output.append(
                        (
                            previous[0] + ratio * (current[0] - previous[0]),
                            previous[1] + ratio * (current[1] - previous[1]),
                        )
                    )
            if current_inside:
                output.append(current)
            previous, previous_distance = current, current_distance
        output = _clean_polygon(output, tolerance_mm)
    if len(output) < 3 or _polygon_area_centroid(output)[0] <= 1e-20:
        return []
    return output


def _barycentric_2d(point: Point2, triangle: Sequence[Point2]) -> Vector:
    ax, ay = triangle[0]
    bx, by = triangle[1]
    cx, cy = triangle[2]
    denominator = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(denominator) <= 1e-18:
        raise ValueError(
            "mesh-linearized C3D10 face contains a degenerate microtriangle"
        )
    first = ((by - cy) * (point[0] - cx) + (cx - bx) * (point[1] - cy)) / denominator
    second = ((cy - ay) * (point[0] - cx) + (ax - cx) * (point[1] - cy)) / denominator
    return (first, second, 1.0 - first - second)


def _bernstein_weights(barycentric: Vector) -> tuple[float, ...]:
    a, b, c = barycentric
    values = (a * a, b * b, c * c, 2.0 * a * b, 2.0 * b * c, 2.0 * c * a)
    if any(value < -1e-12 for value in values):
        raise ArithmeticError(
            "positive Bernstein area partition returned a negative weight"
        )
    return tuple(max(0.0, value) for value in values)


def _integrate_polygon_on_microtriangle(
    polygon: Sequence[Point2],
    micro: _MicroTriangle,
    node_areas: dict[int, float],
) -> tuple[float, Point2]:
    polygon_area, polygon_centroid = _polygon_area_centroid(polygon)
    if polygon_area <= 1e-20:
        return 0.0, polygon_centroid
    # Convex triangle intersections are fan-triangulated, then a positive
    # degree-two three-point rule integrates each Bernstein basis exactly over
    # the locally affine microtriangle geometry.
    quadrature = (
        (2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0),
        (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0),
        (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0),
    )
    for index in range(1, len(polygon) - 1):
        subtriangle = (polygon[0], polygon[index], polygon[index + 1])
        area = _triangle_area_2d(subtriangle)
        if area <= 1e-20:
            continue
        for point_weights in quadrature:
            point2 = tuple(
                math.fsum(
                    point_weights[vertex] * subtriangle[vertex][axis]
                    for vertex in range(3)
                )
                for axis in range(2)
            )
            micro_bary = _barycentric_2d(point2, micro.points_2d)
            face_bary = tuple(
                math.fsum(
                    micro_bary[vertex] * micro.face_barycentric_vertices[vertex][axis]
                    for vertex in range(3)
                )
                for axis in range(3)
            )
            for node_id, shape in zip(
                micro.face_node_ids, _bernstein_weights(face_bary), strict=True
            ):
                node_areas[node_id] = (
                    node_areas.get(node_id, 0.0) + (area / 3.0) * shape
                )
    return polygon_area, polygon_centroid


def _surface_microtriangles(
    surface: Tri6Surface,
    mesh: MeshTopology,
    node_xyz: Mapping[int, Vector],
    elements_by_owner: Mapping[str, Mapping[int, tuple[int, ...]]],
    plane_origin: Vector,
    basis: tuple[Vector, Vector],
    plane_normal: Vector,
    subdivisions: int,
    plane_tolerance_mm: float,
    normal_alignment: float,
) -> tuple[_MicroTriangle, ...]:
    result: list[_MicroTriangle] = []
    elements = elements_by_owner[surface.owner_body]
    for face_ref in surface.face_refs:
        connectivity = elements[face_ref[0]]
        actual_normal, face_node_ids, face_xyz = _face_normal_and_points(
            surface.owner_body, face_ref, connectivity, node_xyz
        )
        if _dot(actual_normal, surface.outward_normal_global_xyz) < normal_alignment:
            raise ValueError(
                f"{surface.label}/{face_ref}: outward C3D10 face normal disagrees with source binding"
            )
        for node_id, point in zip(face_node_ids, face_xyz, strict=True):
            distance = abs(_dot(_sub(point, plane_origin), plane_normal))
            if distance > plane_tolerance_mm:
                raise ValueError(
                    f"{surface.label}/{face_ref}: TRI6 node {node_id} lies {distance:g} mm off the interface plane"
                )
        for reference_vertices in _reference_cells(subdivisions):
            mapped = tuple(
                _q2_point(face_xyz, barycentric) for barycentric in reference_vertices
            )
            points2 = tuple(_to_2d(point, plane_origin, basis) for point in mapped)
            area = _triangle_area_2d(points2)
            if not math.isfinite(area) or area <= 1e-16:
                raise ValueError(
                    f"{surface.label}/{face_ref}: quadratic face tessellation contains a degenerate microtriangle"
                )
            result.append(
                _MicroTriangle(
                    surface.owner_body,
                    face_ref,
                    face_node_ids,
                    points2,  # type: ignore[arg-type]
                    reference_vertices,
                )
            )
    if not result:
        raise ValueError(
            f"{surface.label}: no mesh-linearized TRI6 faces were produced"
        )
    return tuple(result)


def _area_weights_on_triangles(
    triangles: Sequence[_MicroTriangle],
    plane_origin: Vector,
    basis: tuple[Vector, Vector],
) -> tuple[float, Vector, dict[int, float]]:
    """Integrate positive full-surface TRI6 area weights on linearized faces."""

    if not triangles:
        raise ValueError("mesh-linearized TRI6 surface has no microtriangles")
    node_areas: dict[int, float] = {}
    areas: list[float] = []
    first_x: list[float] = []
    first_y: list[float] = []
    expected_nodes: set[int] = set()
    for triangle in triangles:
        area = _triangle_area_2d(triangle.points_2d)
        if not math.isfinite(area) or area <= 1e-16:
            raise ValueError(
                "mesh-linearized TRI6 surface has a degenerate microtriangle"
            )
        centroid2 = _triangle_centroid_2d(triangle.points_2d)
        areas.append(area)
        first_x.append(area * centroid2[0])
        first_y.append(area * centroid2[1])
        expected_nodes.update(triangle.face_node_ids)
        # The positive degree-two rule integrates each Bernstein basis exactly
        # over this linearized microtriangle.
        _integrate_polygon_on_microtriangle(triangle.points_2d, triangle, node_areas)
    total_area = math.fsum(areas)
    if not math.isfinite(total_area) or total_area <= 0.0:
        raise ValueError("mesh-linearized TRI6 surface has zero area")
    if set(node_areas) != expected_nodes or any(
        not math.isfinite(area) or area <= 0.0 for area in node_areas.values()
    ):
        raise ArithmeticError(
            "positive Bernstein integration did not retain exact full TRI6 node ownership"
        )
    integrated_area = math.fsum(node_areas.values())
    if not math.isclose(integrated_area, total_area, rel_tol=2e-12, abs_tol=1e-10):
        raise ArithmeticError(
            "positive Bernstein surface areas do not close total area"
        )
    centroid2 = (
        math.fsum(first_x) / total_area,
        math.fsum(first_y) / total_area,
    )
    centroid = _add(
        _add(plane_origin, _scale(basis[0], centroid2[0])),
        _scale(basis[1], centroid2[1]),
    )
    return total_area, centroid, node_areas


def _micro_bboxes(triangles: Sequence[_MicroTriangle]):
    return tuple(
        (
            min(point[0] for point in triangle.points_2d),
            max(point[0] for point in triangle.points_2d),
            min(point[1] for point in triangle.points_2d),
            max(point[1] for point in triangle.points_2d),
        )
        for triangle in triangles
    )


def _spatial_candidates(
    triangles: Sequence[_MicroTriangle],
    bboxes: Sequence[tuple[float, float, float, float]],
):
    total_area = math.fsum(
        _triangle_area_2d(triangle.points_2d) for triangle in triangles
    )
    cell = max(math.sqrt(total_area / max(1, len(triangles))) * 2.0, 1e-6)
    grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    for index, (xmin, xmax, ymin, ymax) in enumerate(bboxes):
        first_x, last_x = math.floor(xmin / cell), math.floor(xmax / cell)
        first_y, last_y = math.floor(ymin / cell), math.floor(ymax / cell)
        if (last_x - first_x + 1) * (last_y - first_y + 1) > 10000:
            raise ValueError(
                "mesh-linearized candidate face exceeds bounded spatial index size"
            )
        for ix in range(first_x, last_x + 1):
            for iy in range(first_y, last_y + 1):
                grid[(ix, iy)].append(index)
    return cell, grid


def _intersect_surfaces(
    host_triangles: Sequence[_MicroTriangle],
    candidate_triangles: Sequence[_MicroTriangle],
    *,
    plane_origin: Vector,
    basis: tuple[Vector, Vector],
    node_areas_by_owner: dict[str, dict[int, float]],
    clip_tolerance_mm: float,
) -> tuple[float, Vector]:
    candidate_bboxes = _micro_bboxes(candidate_triangles)
    host_bboxes = _micro_bboxes(host_triangles)
    cell_size, grid = _spatial_candidates(candidate_triangles, candidate_bboxes)
    area_terms: list[float] = []
    first_x: list[float] = []
    first_y: list[float] = []
    for host, host_bbox in zip(host_triangles, host_bboxes, strict=True):
        xmin, xmax, ymin, ymax = host_bbox
        keys = {
            (ix, iy)
            for ix in range(
                math.floor(xmin / cell_size), math.floor(xmax / cell_size) + 1
            )
            for iy in range(
                math.floor(ymin / cell_size), math.floor(ymax / cell_size) + 1
            )
        }
        possible = sorted({index for key in keys for index in grid.get(key, ())})
        for candidate_index in possible:
            candidate = candidate_triangles[candidate_index]
            cbbox = candidate_bboxes[candidate_index]
            if (
                cbbox[1] < xmin - clip_tolerance_mm
                or cbbox[0] > xmax + clip_tolerance_mm
                or cbbox[3] < ymin - clip_tolerance_mm
                or cbbox[2] > ymax + clip_tolerance_mm
            ):
                continue
            polygon = _clip_triangle(
                host.points_2d, candidate.points_2d, clip_tolerance_mm
            )
            if not polygon:
                continue
            area, centroid = _polygon_area_centroid(polygon)
            if area <= 1e-16:
                continue
            area_terms.append(area)
            first_x.append(area * centroid[0])
            first_y.append(area * centroid[1])
            _integrate_polygon_on_microtriangle(
                polygon,
                host,
                node_areas_by_owner[host.owner_body],
            )
            _integrate_polygon_on_microtriangle(
                polygon,
                candidate,
                node_areas_by_owner[candidate.owner_body],
            )
    common_area = math.fsum(area_terms)
    if not math.isfinite(common_area) or common_area <= 0.0:
        raise ValueError(
            "the two TRI6 surface patches have no positive mesh-linearized overlap"
        )
    centroid2 = (math.fsum(first_x) / common_area, math.fsum(first_y) / common_area)
    centroid3 = _add(
        _add(plane_origin, _scale(basis[0], centroid2[0])),
        _scale(basis[1], centroid2[1]),
    )
    return common_area, centroid3


def _centroid_from_area_weights(
    node_areas: Mapping[int, float], node_xyz: Mapping[int, Vector]
) -> Vector:
    area = math.fsum(node_areas.values())
    if not math.isfinite(area) or area <= 0.0:
        raise ValueError("nodal tributary area sum is not positive")
    return tuple(
        math.fsum(node_areas[node] * node_xyz[node][axis] for node in node_areas) / area
        for axis in range(3)
    )  # type: ignore[return-value]


def _load_patch_side(
    surface: Tri6Surface,
    node_areas: Mapping[int, float],
    area_mm2: float,
    geometric_centroid: Vector,
    datum_xyz_mm: Vector,
    node_xyz: Mapping[int, Vector],
    *,
    centroid_tolerance_mm: float,
) -> LoadPatchSide:
    ordered = tuple(
        PatchNodeWeight(node, node_xyz[node], area)
        for node, area in sorted(node_areas.items())
        if area > 0.0
    )
    area_sum = math.fsum(node.tributary_area_mm2 for node in ordered)
    if not math.isclose(area_sum, area_mm2, rel_tol=2e-12, abs_tol=1e-10):
        raise ArithmeticError(
            f"{surface.label}: positive Bernstein areas do not close total area"
        )
    nodal_centroid = _centroid_from_area_weights(
        {node.node_id: node.tributary_area_mm2 for node in ordered}, node_xyz
    )
    centroid_error = _norm(_sub(nodal_centroid, geometric_centroid))
    if centroid_error > centroid_tolerance_mm:
        raise ValueError(
            f"{surface.label}: positive Bernstein tributary centroid differs from clipped geometry by {centroid_error:g} mm"
        )
    zero = Wrench((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    rank_check = distribute_wrench_to_nodes(
        ordered,
        datum_xyz_mm,
        zero,
        owner_body=surface.owner_body,
    )
    return LoadPatchSide(
        surface.owner_body,
        surface.label,
        ordered,
        area_mm2,
        geometric_centroid,
        nodal_centroid,
        centroid_error,
        rank_check.scaled_gram_relative_pivot,
    )


def _relative_error(actual: float, target: float) -> float:
    return abs(actual - target) / max(abs(target), 1e-300)


def _run_overlay(
    host_surface: Tri6Surface,
    candidate_surface: Tri6Surface,
    mesh: MeshTopology,
    node_xyz: Mapping[int, Vector],
    elements_by_owner: Mapping[str, Mapping[int, tuple[int, ...]]],
    plane_origin: Vector,
    plane_normal: Vector,
    basis: tuple[Vector, Vector],
    subdivisions: int,
    plane_tolerance_mm: float,
    normal_alignment: float,
    clip_tolerance_mm: float,
) -> tuple[
    tuple[_MicroTriangle, ...],
    tuple[_MicroTriangle, ...],
    float,
    Vector,
    dict[str, dict[int, float]],
    float,
    float,
    Vector,
    Vector,
    float,
]:
    host_triangles = _surface_microtriangles(
        host_surface,
        mesh,
        node_xyz,
        elements_by_owner,
        plane_origin,
        basis,
        plane_normal,
        subdivisions,
        plane_tolerance_mm,
        normal_alignment,
    )
    candidate_triangles = _surface_microtriangles(
        candidate_surface,
        mesh,
        node_xyz,
        elements_by_owner,
        plane_origin,
        basis,
        plane_normal,
        subdivisions,
        plane_tolerance_mm,
        normal_alignment,
    )
    host_area, host_centroid, _host_surface_node_areas = _area_weights_on_triangles(
        host_triangles, plane_origin, basis
    )
    candidate_area, candidate_centroid, _candidate_surface_node_areas = (
        _area_weights_on_triangles(candidate_triangles, plane_origin, basis)
    )
    node_areas: dict[str, dict[int, float]] = {
        host_surface.owner_body: {},
        candidate_surface.owner_body: {},
    }
    common_area, common_centroid = _intersect_surfaces(
        host_triangles,
        candidate_triangles,
        plane_origin=plane_origin,
        basis=basis,
        node_areas_by_owner=node_areas,
        clip_tolerance_mm=clip_tolerance_mm,
    )
    maximum_plane_residual = 0.0
    for side in (host_surface, candidate_surface):
        for node_id in side.tri6_node_ids:
            residual = abs(_dot(_sub(node_xyz[node_id], plane_origin), plane_normal))
            maximum_plane_residual = max(maximum_plane_residual, residual)
    centroid_side_error = _norm(_sub(host_centroid, candidate_centroid))
    return (
        host_triangles,
        candidate_triangles,
        common_area,
        common_centroid,
        node_areas,
        host_area,
        candidate_area,
        host_centroid,
        candidate_centroid,
        max(maximum_plane_residual, centroid_side_error),
    )


def overlay_tri6_surface_patches(
    candidate_surface: Tri6Surface,
    host_surface: Tri6Surface,
    mesh: MeshTopology,
    *,
    plane_origin_xyz_mm: Sequence[float],
    plane_normal_global_xyz: Sequence[float],
    datum_xyz_mm: Sequence[float],
    subdivisions: int = DEFAULT_SUBDIVISIONS,
    area_absolute_tolerance_mm2: float = DEFAULT_AREA_ABSOLUTE_TOLERANCE_MM2,
    area_relative_tolerance: float = DEFAULT_AREA_RELATIVE_TOLERANCE,
    refinement_relative_tolerance: float = DEFAULT_REFINEMENT_RELATIVE_TOLERANCE,
    centroid_tolerance_mm: float = DEFAULT_CENTROID_TOLERANCE_MM,
    plane_tolerance_mm: float = DEFAULT_PLANE_TOLERANCE_MM,
    normal_alignment: float = DEFAULT_NORMAL_ALIGNMENT,
    clip_tolerance_mm: float = DEFAULT_CLIP_TOLERANCE_MM,
    expected_common_area_mm2: float | None = None,
) -> SurfaceOverlayResult:
    """Overlay two owned planar TRI6 surfaces and create positive load areas.

    Quadratic geometry is tessellated from its six-node isoparametric mapping.
    Each clipped polygon is integrated with the positive quadratic Bernstein
    partition, explicitly as diagnostic nodal load lumping rather than
    consistent Lagrange traction loads. The two sides' area, first moment,
    rank-six load map, source area error, and refinement change are checked.
    """

    if not isinstance(candidate_surface, Tri6Surface) or not isinstance(
        host_surface, Tri6Surface
    ):
        raise TypeError("candidate and host sides must be Tri6Surface records")
    if not isinstance(mesh, MeshTopology):
        raise TypeError("mesh must be a MeshTopology record")
    if (
        isinstance(subdivisions, bool)
        or not isinstance(subdivisions, int)
        or subdivisions < 2
    ):
        raise ValueError(
            "quadratic face tessellation needs an integer subdivision count >= 2"
        )
    area_absolute_tolerance_mm2 = _nonnegative(
        area_absolute_tolerance_mm2, "area absolute tolerance"
    )
    area_relative_tolerance = _nonnegative(
        area_relative_tolerance, "area relative tolerance"
    )
    refinement_relative_tolerance = _nonnegative(
        refinement_relative_tolerance, "refinement relative tolerance"
    )
    centroid_tolerance_mm = _positive(centroid_tolerance_mm, "centroid tolerance")
    plane_tolerance_mm = _positive(plane_tolerance_mm, "plane tolerance")
    normal_alignment = _positive(normal_alignment, "normal alignment")
    if normal_alignment >= 1.0:
        raise ValueError("normal alignment must be less than one")
    clip_tolerance_mm = _positive(clip_tolerance_mm, "clip tolerance")
    expected_area = (
        None
        if expected_common_area_mm2 is None
        else _positive(expected_common_area_mm2, "expected common area")
    )
    plane_origin = _vector(plane_origin_xyz_mm, "interface clipping-plane origin")
    plane_normal = _unit(plane_normal_global_xyz, "interface clipping-plane normal")
    datum = _vector(datum_xyz_mm, "interface wrench datum")
    if candidate_surface.owner_body == host_surface.owner_body:
        raise ValueError("candidate and host contact sides must have different owners")
    if (
        _dot(
            candidate_surface.outward_normal_global_xyz,
            host_surface.outward_normal_global_xyz,
        )
        > -normal_alignment
    ):
        raise ValueError("candidate and host source face normals are not opposed")
    if (
        _dot(candidate_surface.outward_normal_global_xyz, plane_normal)
        < normal_alignment
        or _dot(host_surface.outward_normal_global_xyz, plane_normal)
        > -normal_alignment
    ):
        raise ValueError(
            "source face normals disagree with the chosen clipping-plane normal"
        )
    node_xyz, elements_by_owner = _validate_mesh_ownership(
        mesh,
        (host_surface, candidate_surface),
        expected_owner_pair=(host_surface.owner_body, candidate_surface.owner_body),
    )
    basis = _plane_basis(plane_normal)
    coarse_subdivisions = max(1, subdivisions // 2)

    fine = _run_overlay(
        host_surface,
        candidate_surface,
        mesh,
        node_xyz,
        elements_by_owner,
        plane_origin,
        plane_normal,
        basis,
        subdivisions,
        plane_tolerance_mm,
        normal_alignment,
        clip_tolerance_mm,
    )
    (
        _host_triangles,
        _candidate_triangles,
        common_area,
        common_centroid,
        node_areas,
        host_surface_area,
        candidate_surface_area,
        _host_surface_centroid,
        _candidate_surface_centroid,
        _unused_residual,
    ) = fine
    coarse = _run_overlay(
        host_surface,
        candidate_surface,
        mesh,
        node_xyz,
        elements_by_owner,
        plane_origin,
        plane_normal,
        basis,
        coarse_subdivisions,
        plane_tolerance_mm,
        normal_alignment,
        clip_tolerance_mm,
    )
    coarse_area = coarse[2]
    refinement_change = _relative_error(common_area, coarse_area)
    if refinement_change > refinement_relative_tolerance:
        raise ValueError(
            "TRI6 overlay common area changes by "
            f"{refinement_change:g} between subdivisions {coarse_subdivisions} and {subdivisions}"
        )
    area_tolerance = max(
        area_absolute_tolerance_mm2,
        area_relative_tolerance * (expected_area or common_area),
    )
    candidate_area_error = (
        None if expected_area is None else candidate_surface_area - expected_area
    )
    host_common_area_error = host_surface_area - common_area
    if expected_area is not None and abs(common_area - expected_area) > area_tolerance:
        raise ValueError(
            "mesh-linearized common area differs from archived area by "
            f"{common_area - expected_area:g} mm² (tolerance {area_tolerance:g} mm²)"
        )
    if abs(candidate_surface_area - common_area) > area_tolerance:
        # The generic overlay permits partial intersections. The WJ04-specific
        # resolver below separately verifies cleat-face/common-area agreement.
        pass
    candidate_patch = _load_patch_side(
        candidate_surface,
        node_areas[candidate_surface.owner_body],
        common_area,
        common_centroid,
        datum,
        node_xyz,
        centroid_tolerance_mm=centroid_tolerance_mm,
    )
    host_patch = _load_patch_side(
        host_surface,
        node_areas[host_surface.owner_body],
        common_area,
        common_centroid,
        datum,
        node_xyz,
        centroid_tolerance_mm=centroid_tolerance_mm,
    )
    centroid_side_error = _norm(
        _sub(
            candidate_patch.geometric_centroid_xyz_mm,
            host_patch.geometric_centroid_xyz_mm,
        )
    )
    if centroid_side_error > centroid_tolerance_mm:
        raise ValueError(
            f"candidate and host clipped patch centroids differ by {centroid_side_error:g} mm"
        )
    maximum_plane_residual = max(
        abs(_dot(_sub(node_xyz[node_id], plane_origin), plane_normal))
        for surface in (candidate_surface, host_surface)
        for node_id in surface.tri6_node_ids
    )
    maximum_normal_residual = max(
        1.0 - _dot(candidate_surface.outward_normal_global_xyz, plane_normal),
        1.0 + _dot(host_surface.outward_normal_global_xyz, plane_normal),
    )
    return SurfaceOverlayResult(
        candidate_surface_area,
        host_surface_area,
        common_area,
        common_centroid,
        candidate_patch,
        host_patch,
        subdivisions,
        coarse_subdivisions,
        coarse_area,
        refinement_change,
        candidate_area_error,
        host_common_area_error,
        centroid_side_error,
        maximum_plane_residual,
        maximum_normal_residual,
    )


def resolve_interface_load_patch(
    binding: InterfacePatchBinding,
    mesh: MeshTopology,
    *,
    subdivisions: int = DEFAULT_SUBDIVISIONS,
    area_absolute_tolerance_mm2: float = DEFAULT_AREA_ABSOLUTE_TOLERANCE_MM2,
    area_relative_tolerance: float = DEFAULT_AREA_RELATIVE_TOLERANCE,
    refinement_relative_tolerance: float = DEFAULT_REFINEMENT_RELATIVE_TOLERANCE,
    centroid_tolerance_mm: float = DEFAULT_CENTROID_TOLERANCE_MM,
    plane_tolerance_mm: float = DEFAULT_PLANE_TOLERANCE_MM,
    normal_alignment: float = DEFAULT_NORMAL_ALIGNMENT,
    clip_tolerance_mm: float = DEFAULT_CLIP_TOLERANCE_MM,
) -> ResolvedInterfaceLoadPatch:
    """Resolve one exact WJ04 finite cleat patch on both wood owners."""

    if not isinstance(binding, InterfacePatchBinding):
        raise TypeError("binding must be an InterfacePatchBinding")
    if binding.interface_id not in EXPECTED_OWNER_PAIRS:
        raise ValueError(
            "interface binding is outside the authenticated four-interface set"
        )
    host_body, cleat_body = EXPECTED_OWNER_PAIRS[binding.interface_id]
    if (binding.host_surface.owner_body, binding.cleat_surface.owner_body) != (
        host_body,
        cleat_body,
    ):
        raise ValueError("interface binding owner references changed")
    overlay = overlay_tri6_surface_patches(
        binding.cleat_surface,
        binding.host_surface,
        mesh,
        plane_origin_xyz_mm=binding.datum_xyz_mm,
        plane_normal_global_xyz=binding.cleat_surface.outward_normal_global_xyz,
        datum_xyz_mm=binding.datum_xyz_mm,
        subdivisions=subdivisions,
        area_absolute_tolerance_mm2=area_absolute_tolerance_mm2,
        area_relative_tolerance=area_relative_tolerance,
        refinement_relative_tolerance=refinement_relative_tolerance,
        centroid_tolerance_mm=centroid_tolerance_mm,
        plane_tolerance_mm=plane_tolerance_mm,
        normal_alignment=normal_alignment,
        clip_tolerance_mm=clip_tolerance_mm,
        expected_common_area_mm2=binding.finite_common_area_mm2,
    )
    area_tolerance = max(
        area_absolute_tolerance_mm2,
        area_relative_tolerance * binding.finite_common_area_mm2,
    )
    if (
        abs(overlay.candidate_surface_area_mm2 - binding.finite_common_area_mm2)
        > area_tolerance
    ):
        raise ValueError(
            "finite cleat TRI6 surface area does not match archived common area within mesh tolerance"
        )
    if abs(overlay.common_area_mm2 - binding.finite_common_area_mm2) > area_tolerance:
        raise ValueError(
            "host clipping does not recover the authenticated finite common area"
        )
    return ResolvedInterfaceLoadPatch(binding, overlay)


def distribute_case_on_resolved_patch(
    case: UnitWrenchCase, patch: ResolvedInterfaceLoadPatch
) -> DistributedUnitCase:
    """Distribute one case only on its resolved common footprint and close it."""

    if not isinstance(case, UnitWrenchCase) or not isinstance(
        patch, ResolvedInterfaceLoadPatch
    ):
        raise TypeError("case and resolved patch must use their canonical records")
    binding = patch.binding
    overlay = patch.overlay
    if not isinstance(binding, InterfacePatchBinding) or not isinstance(
        overlay, SurfaceOverlayResult
    ):
        raise TypeError("resolved patch must retain its interface binding and overlay")
    owned_sides = (
        (binding.host_surface, overlay.host_patch),
        (binding.cleat_surface, overlay.candidate_patch),
    )
    for surface, side in owned_sides:
        if side.owner_body != surface.owner_body:
            raise ValueError(
                "resolved patch nodal owner labels do not match source surfaces"
            )
        node_ids = tuple(row.node_id for row in side.node_weights)
        if (
            not node_ids
            or len(node_ids) != len(set(node_ids))
            or not set(node_ids) <= set(surface.tri6_node_ids)
        ):
            raise ValueError(
                f"{surface.label}: load nodes do not retain exact source-surface ownership"
            )
        side_area = math.fsum(row.tributary_area_mm2 for row in side.node_weights)
        if not math.isclose(
            side_area, overlay.common_area_mm2, rel_tol=2e-12, abs_tol=1e-10
        ):
            raise ValueError(
                f"{surface.label}: tributary areas do not close the common patch"
            )
    if case.interface_id != binding.interface_id:
        raise ValueError("unit case interface does not match its resolved footprint")
    if case.datum_xyz_mm != binding.datum_xyz_mm:
        raise ValueError("unit case moment datum does not match source interface datum")
    if case.owner_bodies != (
        binding.host_surface.owner_body,
        binding.cleat_surface.owner_body,
    ):
        raise ValueError(
            "unit case owner/moment references do not match resolved surface owners"
        )
    return distribute_unit_case_to_nodes(
        case,
        {
            binding.host_surface.owner_body: patch.overlay.host_patch.node_weights,
            binding.cleat_surface.owner_body: patch.overlay.candidate_patch.node_weights,
        },
    )


def resolved_load_patch_payload(patch: ResolvedInterfaceLoadPatch) -> dict[str, Any]:
    """Emit mesh load weights, area errors, ownership, and closure diagnostics."""

    if not isinstance(patch, ResolvedInterfaceLoadPatch):
        raise TypeError("patch must be a ResolvedInterfaceLoadPatch")
    binding = patch.binding
    overlay = patch.overlay

    def side_payload(side: LoadPatchSide) -> dict[str, Any]:
        return {
            "owner_body": side.owner_body,
            "surface_label": side.surface_label,
            "geometric_area_mm2": side.geometric_area_mm2,
            "geometric_centroid_xyz_mm": side.geometric_centroid_xyz_mm,
            "nodal_area_centroid_xyz_mm": side.nodal_area_centroid_xyz_mm,
            "nodal_centroid_error_mm": side.nodal_centroid_error_mm,
            "scaled_gram_relative_pivot": side.scaled_gram_relative_pivot,
            "node_weights": [
                {
                    "node_id": row.node_id,
                    "point_xyz_mm": row.point_xyz_mm,
                    "tributary_area_mm2": row.tributary_area_mm2,
                }
                for row in side.node_weights
            ],
        }

    return {
        "schema": SCHEMA,
        "status": "mesh_linearized_diagnostic_load_lumping_only_no_solver_or_capacity_claim",
        "interface_id": binding.interface_id,
        "datum_xyz_mm": binding.datum_xyz_mm,
        "finite_common_area_archived_mm2": binding.finite_common_area_mm2,
        "method": {
            "surface_overlay": "candidate_finite_TRI6_pieces_clipped_against_host_TRI6_pieces",
            "curved_face_geometry": "reference_subdivided_quadratic_map_to_convex_linearized_microtriangles",
            "area_lumping": "positive_quadratic_Bernstein_partition_diagnostic_loads_not_consistent_Lagrange_tractions",
            "subdivisions": overlay.subdivisions,
            "coarse_subdivisions": overlay.coarse_subdivisions,
            "mesh_boundary_status": "linearized_mesh_boundary_not_exact_CAD_polygon",
        },
        "source_hashes": dict(binding.source_hashes),
        "area_and_moment_checks": {
            "candidate_surface_mesh_area_mm2": overlay.candidate_surface_area_mm2,
            "host_surface_mesh_area_mm2": overlay.host_surface_area_mm2,
            "common_mesh_area_mm2": overlay.common_area_mm2,
            "candidate_surface_area_minus_archived_mm2": overlay.candidate_area_source_error_mm2,
            "host_surface_area_minus_common_area_mm2": overlay.host_common_area_error_mm2,
            "coarse_common_area_mm2": overlay.coarse_common_area_mm2,
            "refinement_relative_change": overlay.refinement_relative_change,
            "common_centroid_xyz_mm": overlay.common_centroid_xyz_mm,
            "candidate_host_centroid_difference_mm": overlay.common_centroid_side_error_mm,
            "maximum_plane_residual_mm": overlay.maximum_plane_residual_mm,
            "maximum_normal_alignment_residual": overlay.maximum_normal_alignment_residual,
        },
        "host_patch": side_payload(overlay.host_patch),
        "cleat_patch": side_payload(overlay.candidate_patch),
        "limitations": [
            "Finite footprint follows source-bound candidate TRI6 face references and their mesh-linearized edges; it is not a reconstructed exact CAD polygon.",
            "Positive Bernstein areas define a diagnostic nodal load distribution, not physical pressure or a consistent Lagrange traction field.",
            "No restraints, contacts, preload, engagement, solver cards, response, or capacity are supplied.",
        ],
    }
