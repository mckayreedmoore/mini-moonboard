"""Classify the selected current three-wood/four-bolt patch mesh.

This is a geometry-only adapter. It binds current-patch source faces and
hardware seats to owned C3D10 exterior faces, measures finite mesh overlays
and open radial clearances, and deliberately leaves the response unready.
Gmsh tags are used only as local pointers inside one mesh-body record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from fea.floor_contact import FACES
from fea.wood_joint_patch_load_patch import (
    MeshTopology,
    Tri6Surface,
    _face_normal_and_points,
    overlay_tri6_surface_patches,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_current_patch_contact_classification/v1"
INPUT_SCHEMA = "wood_joint_current_patch_inputs/v1"
INPUT_STATUS = "current_geometry_patch_inputs_only"
MESH_SCHEMA = "wood_joint_current_patch_mesh/v1"
MESH_STATUS = "VERIFIED_C3D10_CURRENT_PATCH_MESH_ONLY_NO_SOLVER"
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
IMPLEMENTATION_REVISION = "b1e8707d"

WOOD_IDS = (
    "bottom_center_right_cleat",
    "base_rail_bottom_right",
    "base_principal_center_right",
)
AXIS_RECEIVERS = {
    "bottom_center/clip_horizontal_bottom_right_1/rail_1": (
        "bottom_center_right_cleat",
        "base_rail_bottom_right",
    ),
    "bottom_center/clip_horizontal_bottom_right_1/rail_2": (
        "bottom_center_right_cleat",
        "base_rail_bottom_right",
    ),
    "bottom_center/clip_horizontal_bottom_right_1/principal_1": (
        "bottom_center_right_cleat",
        "base_principal_center_right",
    ),
    "bottom_center/clip_horizontal_bottom_right_1/principal_2": (
        "bottom_center_right_cleat",
        "base_principal_center_right",
    ),
}
INTERFACE_MEMBERS = {
    "bottom_center_right_cleat_to_base_rail_bottom_right": (
        "bottom_center_right_cleat",
        "base_rail_bottom_right",
    ),
    "bottom_center_right_cleat_to_base_principal_center_right": (
        "bottom_center_right_cleat",
        "base_principal_center_right",
    ),
    "base_rail_bottom_right_to_base_principal_center_right": (
        "base_rail_bottom_right",
        "base_principal_center_right",
    ),
}
METAL_ROLES = ("bolt", "head_washer", "nut_washer", "nut")
CAD_POSITION_TOLERANCE_MM = 0.02
SEAT_NODAL_AREA_CENTROID_TOLERANCE_MM = 0.02
CAD_AREA_RELATIVE_TOLERANCE = 1e-6
NORMAL_DOT_TOLERANCE = 2e-6
PLANE_TOLERANCE_MM = 1e-5
CYLINDER_LINE_TOLERANCE_MM = 0.05
CYLINDER_AXIS_DOT_MINIMUM = 0.99999
CYLINDER_RADIUS_TOLERANCE_MM = 0.02
SHAFT_INTERVAL_TOLERANCE_MM = 0.05

Vector = tuple[float, float, float]
FaceRef = tuple[int, int]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _vec3(value: Any, context: str) -> Vector:
    try:
        result = tuple(float(item) for item in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected a finite XYZ vector") from error
    if len(result) != 3 or not all(math.isfinite(item) for item in result):
        raise ValueError(f"{context}: expected a finite XYZ vector")
    return result  # type: ignore[return-value]


def _vec6(value: Any, context: str) -> tuple[float, float, float, float, float, float]:
    try:
        result = tuple(float(item) for item in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected six finite bounds") from error
    if len(result) != 6 or not all(math.isfinite(item) for item in result):
        raise ValueError(f"{context}: expected six finite bounds")
    if any(result[index] > result[index + 1] for index in (0, 2, 4)):
        raise ValueError(f"{context}: inverted bounds")
    return result  # type: ignore[return-value]


def _number(value: Any, context: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{context}: expected a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected a finite number") from error
    if not math.isfinite(result):
        raise ValueError(f"{context}: expected a finite number")
    return result


def _unit(value: Any, context: str) -> Vector:
    vector = _vec3(value, context)
    length = math.sqrt(math.fsum(item * item for item in vector))
    if length <= 1e-12:
        raise ValueError(f"{context}: expected a nonzero vector")
    return tuple(item / length for item in vector)  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def _sub(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _add(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _scale(vector: Sequence[float], amount: float) -> Vector:
    return tuple(amount * value for value in vector)  # type: ignore[return-value]


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _line_distance(
    point: Sequence[float], origin: Sequence[float], axis: Sequence[float]
) -> float:
    delta = _sub(point, origin)
    projection = _dot(delta, axis)
    return _norm(_sub(delta, _scale(axis, projection)))


def _json(path: Path, context: str) -> tuple[bytes, dict[str, Any]]:
    try:
        payload = path.read_bytes()
        record = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{context} is unavailable or invalid: {path}") from error
    if not isinstance(record, dict):
        raise TypeError(f"{context} must be a JSON object")
    return payload, record


def _validate_current_inventory(inventory: Mapping[str, Any]) -> None:
    if (
        inventory.get("schema") != INPUT_SCHEMA
        or inventory.get("status") != INPUT_STATUS
    ):
        raise ValueError(
            "source inventory is not the current-patch geometry-only schema"
        )
    candidate = inventory.get("candidate")
    geometry = inventory.get("geometry_binding")
    scope = inventory.get("scope")
    if not isinstance(candidate, Mapping) or not isinstance(geometry, Mapping):
        raise TypeError("current candidate binding is incomplete")
    if (
        candidate.get("revision_id") != REVISION_ID
        or candidate.get("implementation_revision") != IMPLEMENTATION_REVISION
        or geometry.get("layout_id") != REVISION_ID
        or geometry.get("trial_id") != REVISION_ID
        or geometry.get("status") != "unaccepted_viewer_geometry_revision"
    ):
        raise ValueError(
            "source inventory differs from the resumed current geometry revision"
        )
    expected_scope = {
        "finished_wood_bodies": 3,
        "physical_bolts": 4,
        "modeled_hardware_cad_roles": 20,
        "wood_interfaces": 3,
        "step_artifacts": 27,
        "derived_physical_bolt_unions": 4,
        "physical_metal_bodies": 16,
        "meshed": False,
        "native_solve_run": False,
        "contact_law_assigned": False,
        "strength_or_joint_acceptance_claim": False,
    }
    if not isinstance(scope, Mapping) or any(
        scope.get(key) != value for key, value in expected_scope.items()
    ):
        raise ValueError(
            "source inventory scope differs from the three-wood/four-bolt contract"
        )
    woods = inventory.get("wood_bodies")
    if (
        not isinstance(woods, list)
        or tuple(row.get("part_id") for row in woods) != WOOD_IDS
    ):
        raise ValueError("source inventory wood body order is incomplete or changed")
    axes = inventory.get("physical_bolts")
    if not isinstance(axes, list) or tuple(
        row.get("physical_bolt_id") for row in axes
    ) != tuple(AXIS_RECEIVERS):
        raise ValueError("source inventory physical bolt identities or order changed")
    for axis in axes:
        axis_id = axis["physical_bolt_id"]
        receivers = axis.get("receivers_head_to_nut")
        if receivers != list(AXIS_RECEIVERS[axis_id]):
            raise ValueError(
                f"{axis_id}: ordered receiver identities differ from the current model"
            )
        bore_members = set(axis.get("bore_receiver_ids_membership_only", ()))
        if bore_members != set(AXIS_RECEIVERS[axis_id]):
            raise ValueError(
                f"{axis_id}: bore receiver membership does not match its physical bolt"
            )
        origin = _vec3(axis.get("axis_origin_global_xyz_mm"), f"{axis_id} axis origin")
        direction = _unit(
            axis.get("axis_direction_head_to_nut_global_xyz"),
            f"{axis_id} axis direction",
        )
        if abs(_norm(axis.get("axis_direction_head_to_nut_global_xyz")) - 1.0) > 1e-7:
            raise ValueError(f"{axis_id}: declared axis direction is not normalized")
        _ = origin, direction
        receiver_rows = axis.get("raw_receiver_projected_intervals")
        if not isinstance(receiver_rows, list) or len(receiver_rows) != 2:
            raise ValueError(f"{axis_id}: two raw receiver intervals are required")
        previous_end = None
        for order, (receiver, expected_member) in enumerate(
            zip(receiver_rows, receivers, strict=True), 1
        ):
            intervals = receiver.get("projected_intervals_from_underhead_datum_mm")
            if (
                receiver.get("member_id") != expected_member
                or receiver.get("receiver_order_head_to_nut") != order
                or receiver.get("current_shaft_covers_raw_receiver") is not True
                or not isinstance(intervals, list)
                or len(intervals) != 1
            ):
                raise ValueError(
                    f"{axis_id}/{expected_member}: raw receiver coverage is incomplete"
                )
            low, high = (
                _number(value, f"{axis_id}/{expected_member} interval")
                for value in intervals[0]
            )
            if high <= low or (
                previous_end is not None and abs(low - previous_end) > 0.02
            ):
                raise ValueError(
                    f"{axis_id}/{expected_member}: axial receiver intervals are invalid or out of order"
                )
            previous_end = high
        role_rows = axis.get("physical_hardware_roles")
        if not isinstance(role_rows, list) or tuple(
            row.get("role") for row in role_rows
        ) != ("shaft", "head", "head_washer", "nut_washer", "nut"):
            raise ValueError(
                f"{axis_id}: complete ordered physical-role projections are required"
            )

    interfaces = inventory.get("wood_interfaces")
    if not isinstance(interfaces, list) or tuple(
        row.get("interface_id") for row in interfaces
    ) != tuple(INTERFACE_MEMBERS):
        raise ValueError(
            "source inventory must contain the exact three current wood interfaces"
        )
    expected_axes_by_pair = {
        pair: [
            axis_id
            for axis_id, receivers in AXIS_RECEIVERS.items()
            if set(receivers) == set(pair)
        ]
        for pair in INTERFACE_MEMBERS.values()
    }
    for interface in interfaces:
        interface_id = interface["interface_id"]
        members = INTERFACE_MEMBERS[interface_id]
        if interface.get("members") != list(members):
            raise ValueError(f"{interface_id}: wood member ownership or order changed")
        if set(interface.get("bolt_axis_ids", ())) != set(
            expected_axes_by_pair[members]
        ):
            raise ValueError(
                f"{interface_id}: physical bolt ownership differs from its member pair"
            )
        if interface.get("status") != "finite_opposed_coplanar_patch_extracted":
            raise ValueError(
                f"{interface_id}: source finite face-pair extraction is missing"
            )
        area = _number(
            interface.get("finite_overlap_area_mm2"),
            f"{interface_id} finite overlap area",
        )
        pairs = interface.get("actual_face_pairs")
        if area <= 0 or not isinstance(pairs, list) or len(pairs) != 1:
            raise ValueError(
                f"{interface_id}: exactly one positive finite actual face pair is required"
            )
        pair = pairs[0]
        if (
            pair.get("first_member") != members[0]
            or pair.get("second_member") != members[1]
        ):
            raise ValueError(
                f"{interface_id}: source face pair member identity changed"
            )
        if not math.isclose(
            area,
            _number(pair.get("common_area_mm2"), f"{interface_id} common area"),
            rel_tol=0,
            abs_tol=1e-6,
        ):
            raise ValueError(
                f"{interface_id}: finite interface area differs from its actual face overlap"
            )
        first_normal = _unit(
            pair["first_face"]["normal_global_xyz"], f"{interface_id} first face normal"
        )
        second_normal = _unit(
            pair["second_face"]["normal_global_xyz"],
            f"{interface_id} second face normal",
        )
        if _dot(first_normal, second_normal) > -1 + NORMAL_DOT_TOLERANCE:
            raise ValueError(
                f"{interface_id}: source contact face normals are not opposed"
            )
    if inventory.get("migration_blockers"):
        raise ValueError("source inventory contains a current-patch migration blocker")


def _parse_deck(
    path: Path, body_ids: Sequence[str]
) -> tuple[dict[int, Vector], dict[str, dict[int, tuple[int, ...]]]]:
    nodes: dict[int, Vector] = {}
    elements = {body: {} for body in body_ids}
    by_elset = {body.upper(): body for body in body_ids}
    mode: str | None = None
    current_body: str | None = None
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            upper = line.upper()
            mode = None
            current_body = None
            if upper == "*NODE":
                mode = "node"
            elif upper.startswith("*ELEMENT,"):
                options = {}
                for cell in line.split(",")[1:]:
                    if "=" in cell:
                        key, value = cell.split("=", 1)
                        options[key.strip().upper()] = value.strip()
                current_body = by_elset.get(options.get("ELSET", "").upper())
                if options.get("TYPE", "").upper() != "C3D10" or current_body is None:
                    raise ValueError(
                        f"mesh deck line {line_number}: unexpected element block"
                    )
                mode = "element"
            continue
        cells = [cell.strip() for cell in line.split(",")]
        if mode == "node":
            if len(cells) != 4:
                raise ValueError(f"mesh deck line {line_number}: malformed node")
            node = int(cells[0])
            if node <= 0 or node in nodes:
                raise ValueError(
                    f"mesh deck line {line_number}: duplicate or invalid node ID"
                )
            nodes[node] = _vec3(cells[1:], f"mesh deck line {line_number} node")
        elif mode == "element":
            if current_body is None or len(cells) != 11:
                raise ValueError(f"mesh deck line {line_number}: malformed C3D10")
            element = int(cells[0])
            conn = tuple(int(cell) for cell in cells[1:])
            if element <= 0 or len(set(conn)) != 10 or any(node <= 0 for node in conn):
                raise ValueError(
                    f"mesh deck line {line_number}: invalid C3D10 ownership"
                )
            if any(element in body for body in elements.values()):
                raise ValueError(
                    f"mesh deck line {line_number}: duplicate global element ID"
                )
            elements[current_body][element] = conn
    used_nodes = {
        node for rows in elements.values() for conn in rows.values() for node in conn
    }
    if (
        not nodes
        or not used_nodes
        or used_nodes != nodes.keys()
        or any(not rows for rows in elements.values())
    ):
        raise ValueError("mesh deck node/element ownership is incomplete")
    if not used_nodes <= nodes.keys():
        raise ValueError("mesh deck references an absent node")
    return nodes, elements


def _body_maps(
    inventory: Mapping[str, Any],
    mesh_report: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str], dict[str, dict[str, Any]]]:
    bodies = mesh_report.get("bodies")
    if (
        not isinstance(bodies, Mapping)
        or len(bodies) != 19
        or mesh_report.get("body_count") != 19
    ):
        raise ValueError("mesh report does not contain exactly 19 owned bodies")
    wood_map: dict[str, str] = {}
    metal_map: dict[str, str] = {}
    rows: dict[str, dict[str, Any]] = {}
    for mesh_id, row in bodies.items():
        if (
            not isinstance(row, dict)
            or row.get("mesh_body_id") != mesh_id
            or row.get("element_elset_name") != mesh_id
        ):
            raise ValueError(
                "mesh body rows do not preserve stable mesh and ELSET ownership"
            )
        if row.get("owner_kind") == "wood_member":
            logical = row.get("source_body_id")
            if (
                logical not in WOOD_IDS
                or logical in wood_map
                or row.get("physical_body_id") is not None
            ):
                raise ValueError(
                    "mesh report has unexpected or duplicated wood ownership"
                )
            wood_map[logical] = str(mesh_id)
        elif row.get("owner_kind") == "physical_metal":
            logical = row.get("physical_body_id")
            if (
                not isinstance(logical, str)
                or logical in metal_map
                or row.get("source_body_id") is not None
            ):
                raise ValueError(
                    "mesh report has unexpected or duplicated physical metal ownership"
                )
            metal_map[logical] = str(mesh_id)
        else:
            raise ValueError(f"{mesh_id}: unknown mesh owner kind")
        rows[str(mesh_id)] = row
    expected_metal_ids = {
        row["physical_body_id"] for row in inventory["physical_metal_bodies"]
    }
    if (
        set(wood_map) != set(WOOD_IDS)
        or set(metal_map) != expected_metal_ids
        or len(metal_map) != 16
    ):
        raise ValueError(
            "mesh body ownership differs from the exact three-wood/sixteen-metal source inventory"
        )
    return wood_map, metal_map, rows


def _validate_mesh_topology(
    mesh_report: Mapping[str, Any],
    body_rows: Mapping[str, Mapping[str, Any]],
    nodes: Mapping[int, Vector],
    elements: Mapping[str, Mapping[int, Sequence[int]]],
) -> MeshTopology:
    if mesh_report.get("node_count") != len(nodes) or mesh_report.get(
        "element_count"
    ) != sum(map(len, elements.values())):
        raise ValueError("mesh report counts differ from the parsed current mesh deck")
    report_ids = set(body_rows)
    if set(elements) != report_ids:
        raise ValueError(
            "mesh deck ELSET ownership differs from the 19 mesh body records"
        )
    owner_nodes: dict[str, tuple[int, ...]] = {}
    normalized_elements: dict[str, dict[int, tuple[int, ...]]] = {}
    seen_nodes: set[int] = set()
    seen_elements: set[int] = set()
    for owner, row in body_rows.items():
        body_nodes = tuple(int(value) for value in row.get("nodes", ()))
        body_elements = tuple(int(value) for value in row.get("elements", ()))
        if (
            not body_nodes
            or not body_elements
            or len(set(body_nodes)) != len(body_nodes)
            or len(set(body_elements)) != len(body_elements)
        ):
            raise ValueError(
                f"{owner}: mesh node/element owner lists are empty or duplicated"
            )
        if seen_nodes.intersection(body_nodes) or seen_elements.intersection(
            body_elements
        ):
            raise ValueError("current mesh body ownership overlaps globally")
        seen_nodes.update(body_nodes)
        seen_elements.update(body_elements)
        deck_elements = {
            int(key): tuple(int(node) for node in conn)
            for key, conn in elements[owner].items()
        }
        if set(deck_elements) != set(body_elements):
            raise ValueError(f"{owner}: report and deck element ownership differ")
        observed_nodes = {node for conn in deck_elements.values() for node in conn}
        if observed_nodes != set(body_nodes) or not observed_nodes <= nodes.keys():
            raise ValueError(f"{owner}: report and deck node ownership differ")
        if any(
            len(conn) != 10 or len(set(conn)) != 10 or not set(conn) <= set(body_nodes)
            for conn in deck_elements.values()
        ):
            raise ValueError(f"{owner}: malformed C3D10 element ownership")
        if row.get("node_count") != len(body_nodes) or row.get("element_count") != len(
            body_elements
        ):
            raise ValueError(f"{owner}: body counts differ from ownership")
        owner_nodes[owner] = body_nodes
        normalized_elements[owner] = deck_elements
    if seen_nodes != nodes.keys() or seen_elements != {
        element for body in elements.values() for element in body
    }:
        raise ValueError("current mesh deck contains an unowned node or element")

    for owner, row in body_rows.items():
        inventory = row.get("surface_inventory")
        if not isinstance(inventory, Mapping) or not inventory:
            raise ValueError(f"{owner}: surface inventory is missing")
        exterior_counts: Counter[tuple[int, ...]] = Counter()
        for connectivity in normalized_elements[owner].values():
            for face_indices in FACES:
                exterior_counts[
                    tuple(sorted(connectivity[index] for index in face_indices))
                ] += 1
        referenced: list[FaceRef] = []
        for tag, surface in inventory.items():
            if not isinstance(surface, Mapping) or int(
                surface.get("cad_entity_tag", -1)
            ) != int(tag):
                raise ValueError(
                    f"{owner}/{tag}: transient surface pointer is inconsistent"
                )
            refs = surface.get("tri6_exterior_face_refs")
            declared_nodes = surface.get("tri6_node_ids")
            if (
                not isinstance(refs, list)
                or not refs
                or not isinstance(declared_nodes, list)
                or not declared_nodes
            ):
                raise ValueError(f"{owner}/{tag}: TRI6 face ownership is missing")
            observed: set[int] = set()
            for raw_ref in refs:
                if not isinstance(raw_ref, (list, tuple)) or len(raw_ref) != 2:
                    raise ValueError(
                        f"{owner}/{tag}: malformed exterior face reference"
                    )
                element, side = int(raw_ref[0]), int(raw_ref[1])
                if element not in normalized_elements[owner] or side not in (
                    1,
                    2,
                    3,
                    4,
                ):
                    raise ValueError(
                        f"{owner}/{tag}: surface face points to a different body"
                    )
                connectivity = normalized_elements[owner][element]
                face_nodes = tuple(connectivity[index] for index in FACES[side - 1])
                if exterior_counts[tuple(sorted(face_nodes))] != 1:
                    raise ValueError(f"{owner}/{tag}: referenced face is not exterior")
                observed.update(face_nodes)
                referenced.append((element, side))
            if observed != {int(value) for value in declared_nodes}:
                raise ValueError(
                    f"{owner}/{tag}: declared TRI6 node union is incomplete"
                )
            if not observed <= set(owner_nodes[owner]):
                raise ValueError(
                    f"{owner}/{tag}: TRI6 surface nodes have wrong ownership"
                )
            _number(surface.get("cad_area_mm2"), f"{owner}/{tag} CAD area")
            _vec3(
                surface.get("cad_centroid_global_xyz_mm"), f"{owner}/{tag} CAD centroid"
            )
            _vec6(surface.get("bounds_xyz_mm"), f"{owner}/{tag} bounds")
            if surface.get("bounds_order") != "xmin,xmax,ymin,ymax,zmin,zmax":
                raise ValueError(f"{owner}/{tag}: CAD bounds order is missing")
        if len(referenced) != row.get("exterior_tri6_face_count") or len(
            set(referenced)
        ) != len(referenced):
            raise ValueError(
                f"{owner}: exterior TRI6 faces are incomplete or duplicated"
            )
    return MeshTopology(nodes, normalized_elements, owner_nodes)


def _surface_nodes(surface: Mapping[str, Any]) -> tuple[int, ...]:
    return tuple(int(value) for value in surface["tri6_node_ids"])


def _surface_normal(
    owner: str,
    surface: Mapping[str, Any],
    topology: MeshTopology,
    *,
    expected_normal: Sequence[float] | None = None,
    plane_origin: Sequence[float] | None = None,
) -> tuple[Vector, dict[str, float]]:
    refs = tuple(
        (int(row[0]), int(row[1])) for row in surface["tri6_exterior_face_refs"]
    )
    normals = []
    maximum_plane_residual = 0.0
    for ref in refs:
        connectivity = topology.elements_by_owner[owner][ref[0]]
        normal, face_nodes, _face_xyz = _face_normal_and_points(
            owner, ref, connectivity, topology.node_xyz_mm
        )
        normals.append(normal)
        if plane_origin is not None:
            axis = _unit(expected_normal, f"{owner} source face normal")
            maximum_plane_residual = max(
                maximum_plane_residual,
                *(
                    abs(_dot(_sub(topology.node_xyz_mm[node], plane_origin), axis))
                    for node in face_nodes
                ),
            )
    mean = tuple(math.fsum(normal[index] for normal in normals) for index in range(3))
    outward = _unit(mean, f"{owner} finite-element exterior normal")
    min_alignment = min(_dot(outward, normal) for normal in normals)
    if min_alignment < 1 - NORMAL_DOT_TOLERANCE:
        raise ValueError(
            f"{owner}: planar CAD surface has inconsistent C3D10 exterior normals"
        )
    expected_alignment = 1.0
    if expected_normal is not None:
        expected_alignment = _dot(
            outward, _unit(expected_normal, f"{owner} source normal")
        )
        if expected_alignment < 1 - NORMAL_DOT_TOLERANCE:
            raise ValueError(
                f"{owner}: C3D10 exterior normal disagrees with the oriented source face"
            )
    return outward, {
        "minimum_element_outward_normal_alignment": min_alignment,
        "source_oriented_normal_alignment": expected_alignment,
        "maximum_plane_residual_mm": maximum_plane_residual,
    }


def _tri6_surface(
    owner: str,
    tag: str,
    row: Mapping[str, Any],
    topology: MeshTopology,
    *,
    expected_normal: Sequence[float] | None = None,
    expected_plane_point: Sequence[float] | None = None,
) -> tuple[Tri6Surface, dict[str, float]]:
    if str(row.get("cad_type", "")).casefold() != "plane":
        raise ValueError(f"{owner}/{tag}: expected a planar CAD surface")
    normal, audit = _surface_normal(
        owner,
        row,
        topology,
        expected_normal=expected_normal,
        plane_origin=expected_plane_point,
    )
    analytic = row.get("analytic_surface_parameters")
    if (
        not isinstance(analytic, Mapping)
        or str(analytic.get("surface_type", "")).casefold() != "plane"
    ):
        raise ValueError(f"{owner}/{tag}: analytic plane sample is missing")
    sample_point = _vec3(
        analytic.get("sample_point_global_xyz_mm"), f"{owner}/{tag} CAD sample point"
    )
    sample_normal = _unit(
        analytic.get("sample_normal_global_xyz"), f"{owner}/{tag} CAD sample normal"
    )
    if abs(_dot(sample_normal, normal)) < 1 - NORMAL_DOT_TOLERANCE:
        raise ValueError(
            f"{owner}/{tag}: finite-element plane disagrees with its CAD sample normal"
        )
    if expected_plane_point is not None:
        if (
            abs(
                _dot(
                    _sub(sample_point, expected_plane_point),
                    _unit(expected_normal, "source plane normal"),
                )
            )
            > CAD_POSITION_TOLERANCE_MM
        ):
            raise ValueError(
                f"{owner}/{tag}: CAD sample point does not lie on the source finite face plane"
            )
        if audit["maximum_plane_residual_mm"] > CAD_POSITION_TOLERANCE_MM:
            raise ValueError(
                f"{owner}/{tag}: TRI6 nodes leave the source finite face plane"
            )
    result = Tri6Surface(
        owner_body=owner,
        face_refs=tuple(
            (int(item[0]), int(item[1])) for item in row["tri6_exterior_face_refs"]
        ),
        tri6_node_ids=_surface_nodes(row),
        outward_normal_global_xyz=normal,
        label=f"{owner}/CAD-face-{tag}",
    )
    return result, audit


def _face_surface_matches(
    row: Mapping[str, Any],
    source_face: Mapping[str, Any],
    topology: MeshTopology,
) -> bool:
    if str(row.get("cad_type", "")).casefold() != "plane":
        return False
    area = _number(source_face.get("area_mm2"), "source CAD face area")
    mesh_area = _number(row.get("cad_area_mm2"), "mesh CAD face area")
    if abs(mesh_area - area) > max(0.02, CAD_AREA_RELATIVE_TOLERANCE * area):
        return False
    source_centroid = _vec3(
        source_face.get("centroid_global_xyz_mm"), "source CAD face centroid"
    )
    mesh_centroid = _vec3(
        row.get("cad_centroid_global_xyz_mm"), "mesh CAD face centroid"
    )
    source_bounds = _vec6(source_face.get("bounds_xyz_mm"), "source face bounds")
    mesh_bounds = _vec6(row.get("bounds_xyz_mm"), "mesh face bounds")
    if (
        max(abs(a - b) for a, b in zip(source_centroid, mesh_centroid, strict=True))
        > CAD_POSITION_TOLERANCE_MM
    ):
        return False
    if (
        max(abs(a - b) for a, b in zip(source_bounds, mesh_bounds, strict=True))
        > CAD_POSITION_TOLERANCE_MM
    ):
        return False
    source_normal = _unit(
        source_face.get("normal_global_xyz"), "source CAD face normal"
    )
    analytic = row.get("analytic_surface_parameters")
    if not isinstance(analytic, Mapping):
        return False
    sample_point = _vec3(
        analytic.get("sample_point_global_xyz_mm"), "mesh CAD plane sample point"
    )
    sample_normal = _unit(
        analytic.get("sample_normal_global_xyz"), "mesh CAD plane sample normal"
    )
    if abs(_dot(source_normal, sample_normal)) < 1 - NORMAL_DOT_TOLERANCE:
        return False
    if (
        abs(_dot(_sub(sample_point, source_centroid), source_normal))
        > CAD_POSITION_TOLERANCE_MM
    ):
        return False
    owner = str(row.get("_owner_mesh_id", ""))
    nodes = _surface_nodes(row)
    return owner in topology.owner_node_ids and all(
        abs(_dot(_sub(topology.node_xyz_mm[node], source_centroid), source_normal))
        <= CAD_POSITION_TOLERANCE_MM
        for node in nodes
    )


def _source_surface(
    owner_mesh_id: str,
    surfaces: Mapping[str, Mapping[str, Any]],
    source_face: Mapping[str, Any],
    topology: MeshTopology,
) -> tuple[str, Tri6Surface, dict[str, float]]:
    matches = [
        (tag, row)
        for tag, row in surfaces.items()
        if _face_surface_matches(
            {**row, "_owner_mesh_id": owner_mesh_id}, source_face, topology
        )
    ]
    if len(matches) != 1:
        raise ValueError(
            f"source face matches {len(matches)} mesh CAD surfaces; exactly one is required"
        )
    tag, row = matches[0]
    source_normal = _unit(source_face["normal_global_xyz"], "source CAD face normal")
    datum = _vec3(source_face["plane_datum_global_xyz_mm"], "source face plane datum")
    finite_surface, audit = _tri6_surface(
        owner_mesh_id,
        str(tag),
        row,
        topology,
        expected_normal=source_normal,
        expected_plane_point=datum,
    )
    return str(tag), finite_surface, audit


def _overlay_payload(result: Any) -> dict[str, Any]:
    return {
        "area_mm2": result.common_area_mm2,
        "centroid_global_xyz_mm": list(result.common_centroid_xyz_mm),
        "candidate_surface_area_mm2": result.candidate_surface_area_mm2,
        "host_surface_area_mm2": result.host_surface_area_mm2,
        "candidate_node_weight_count": len(result.candidate_patch.node_weights),
        "host_node_weight_count": len(result.host_patch.node_weights),
        "candidate_nodal_area_centroid_residual_mm": result.candidate_patch.nodal_centroid_error_mm,
        "host_nodal_area_centroid_residual_mm": result.host_patch.nodal_centroid_error_mm,
        "candidate_positive_area_sum_mm2": math.fsum(
            row.tributary_area_mm2 for row in result.candidate_patch.node_weights
        ),
        "host_positive_area_sum_mm2": math.fsum(
            row.tributary_area_mm2 for row in result.host_patch.node_weights
        ),
        "candidate_scaled_rank_six_pivot": result.candidate_patch.scaled_gram_relative_pivot,
        "host_scaled_rank_six_pivot": result.host_patch.scaled_gram_relative_pivot,
        "refinement_relative_change": result.refinement_relative_change,
        "maximum_plane_residual_mm": result.maximum_plane_residual_mm,
        "maximum_normal_alignment_residual": result.maximum_normal_alignment_residual,
    }


def _classify_wood_interfaces(
    inventory: Mapping[str, Any],
    wood_map: Mapping[str, str],
    body_rows: Mapping[str, Mapping[str, Any]],
    topology: MeshTopology,
) -> tuple[list[dict[str, Any]], list[str]]:
    results = []
    blockers: list[str] = []
    interfaces_by_id = {
        row["interface_id"]: row for row in inventory["wood_interfaces"]
    }
    for interface_id, members in INTERFACE_MEMBERS.items():
        source = interfaces_by_id[interface_id]
        source_pair = source["actual_face_pairs"][0]
        first_mesh = wood_map[members[0]]
        second_mesh = wood_map[members[1]]
        first_tag, first_surface, first_audit = _source_surface(
            first_mesh,
            body_rows[first_mesh]["surface_inventory"],
            source_pair["first_face"],
            topology,
        )
        second_tag, second_surface, second_audit = _source_surface(
            second_mesh,
            body_rows[second_mesh]["surface_inventory"],
            source_pair["second_face"],
            topology,
        )
        normal = _unit(
            source_pair["plane_normal_first_member_global_xyz"],
            f"{interface_id} plane normal",
        )
        datum = _vec3(
            source_pair["plane_datum_global_xyz_mm"], f"{interface_id} plane datum"
        )
        expected = _number(
            source_pair["common_area_mm2"], f"{interface_id} expected common area"
        )
        centroid = _vec3(
            source_pair["common_area_centroid_global_xyz_mm"],
            f"{interface_id} expected common centroid",
        )
        # OCC source-face common areas are finite and distinct even where two
        # contacts share a larger master CAD face; overlay each pair separately.
        overlay = overlay_tri6_surface_patches(
            first_surface,
            second_surface,
            topology,
            plane_origin_xyz_mm=datum,
            plane_normal_global_xyz=normal,
            datum_xyz_mm=centroid,
            expected_common_area_mm2=expected,
            plane_tolerance_mm=PLANE_TOLERANCE_MM,
        )
        area_tolerance = max(0.5, expected * 5e-4)
        if abs(overlay.common_area_mm2 - expected) > area_tolerance:
            raise ValueError(
                f"{interface_id}: mesh finite patch does not reproduce its independent OCC area"
            )
        centroid_error = _norm(_sub(overlay.common_centroid_xyz_mm, centroid))
        if centroid_error > 0.05:
            raise ValueError(
                f"{interface_id}: mesh patch centroid differs from the source OCC common centroid"
            )
        results.append(
            {
                "interface_id": interface_id,
                "members": list(members),
                "status": "FINITE_MESH_PATCH_OVERLAY_VERIFIED_GEOMETRY_ONLY",
                "source_common_area_mm2": expected,
                "source_common_centroid_global_xyz_mm": list(centroid),
                "first_face": {
                    "body_id": members[0],
                    "mesh_body_id": first_mesh,
                    "transient_cad_entity_tag": int(first_tag),
                    "face_sha256": source_pair["first_face"]["cad_face_sha256"],
                    "outward_normal_global_xyz": list(
                        first_surface.outward_normal_global_xyz
                    ),
                    "normal_audit": first_audit,
                },
                "second_face": {
                    "body_id": members[1],
                    "mesh_body_id": second_mesh,
                    "transient_cad_entity_tag": int(second_tag),
                    "face_sha256": source_pair["second_face"]["cad_face_sha256"],
                    "outward_normal_global_xyz": list(
                        second_surface.outward_normal_global_xyz
                    ),
                    "normal_audit": second_audit,
                },
                "mesh_overlay": _overlay_payload(overlay),
                "source_centroid_error_mm": centroid_error,
                "load_transfer_law_assigned": False,
                "active_pressure_claim": False,
            }
        )
    return results, blockers


def _bbox_intersects(
    a: Sequence[float], b: Sequence[float], tol: float = CAD_POSITION_TOLERANCE_MM
) -> bool:
    return all(
        a[2 * axis] <= b[2 * axis + 1] + tol and b[2 * axis] <= a[2 * axis + 1] + tol
        for axis in range(3)
    )


def _plane_sample(row: Mapping[str, Any]) -> tuple[Vector, Vector] | None:
    if str(row.get("cad_type", "")).casefold() != "plane":
        return None
    data = row.get("analytic_surface_parameters")
    if (
        not isinstance(data, Mapping)
        or str(data.get("surface_type", "")).casefold() != "plane"
    ):
        return None
    try:
        return (
            _vec3(data.get("sample_point_global_xyz_mm"), "plane sample point"),
            _unit(data.get("sample_normal_global_xyz"), "plane sample normal"),
        )
    except (ValueError, TypeError):
        return None


def _surface_objects_for_owner(
    owner: str,
    body_row: Mapping[str, Any],
    topology: MeshTopology,
    *,
    plane_only: bool = False,
) -> list[tuple[str, Mapping[str, Any], Tri6Surface | None]]:
    output = []
    for tag, row in body_row["surface_inventory"].items():
        if plane_only and _plane_sample(row) is None:
            continue
        plane = _plane_sample(row)
        surface = None
        if plane is not None:
            try:
                surface, _audit = _tri6_surface(owner, str(tag), row, topology)
            except (TypeError, ValueError, KeyError):
                continue
        output.append((str(tag), row, surface))
    return output


def _find_plane_seat(
    seat_id: str,
    first_owner: str,
    second_owner: str,
    body_rows: Mapping[str, Mapping[str, Any]],
    topology: MeshTopology,
) -> dict[str, Any]:
    first_rows = _surface_objects_for_owner(
        first_owner, body_rows[first_owner], topology, plane_only=True
    )
    second_rows = _surface_objects_for_owner(
        second_owner, body_rows[second_owner], topology, plane_only=True
    )
    candidates = []
    for first_tag, first_row, first_surface in first_rows:
        first_plane = _plane_sample(first_row)
        assert first_plane is not None
        for second_tag, second_row, second_surface in second_rows:
            second_plane = _plane_sample(second_row)
            assert second_plane is not None
            if first_surface is None or second_surface is None:
                continue
            if (
                _dot(
                    first_surface.outward_normal_global_xyz,
                    second_surface.outward_normal_global_xyz,
                )
                > -1 + NORMAL_DOT_TOLERANCE
            ):
                continue
            if (
                abs(
                    _dot(
                        _sub(first_plane[0], second_plane[0]),
                        first_surface.outward_normal_global_xyz,
                    )
                )
                > 0.02
            ):
                continue
            if not _bbox_intersects(
                first_row["bounds_xyz_mm"], second_row["bounds_xyz_mm"]
            ):
                continue
            origin = first_plane[0]
            datum = tuple(
                (
                    float(first_row["cad_centroid_global_xyz_mm"][i])
                    + float(second_row["cad_centroid_global_xyz_mm"][i])
                )
                / 2
                for i in range(3)
            )
            try:
                overlay = overlay_tri6_surface_patches(
                    first_surface,
                    second_surface,
                    topology,
                    plane_origin_xyz_mm=origin,
                    plane_normal_global_xyz=first_surface.outward_normal_global_xyz,
                    datum_xyz_mm=datum,
                    plane_tolerance_mm=PLANE_TOLERANCE_MM,
                    centroid_tolerance_mm=SEAT_NODAL_AREA_CENTROID_TOLERANCE_MM,
                )
            except (ValueError, ArithmeticError):
                continue
            if overlay.common_area_mm2 > 1e-5:
                candidates.append(
                    (first_tag, second_tag, first_surface, second_surface, overlay)
                )
    if len(candidates) != 1:
        return {
            "seat_id": seat_id,
            "status": "MISSING_OR_AMBIGUOUS_FINITE_SEAT",
            "owner_pair": [first_owner, second_owner],
            "candidate_overlay_count": len(candidates),
            "load_transfer_law_assigned": False,
        }
    first_tag, second_tag, first_surface, second_surface, overlay = candidates[0]
    return {
        "seat_id": seat_id,
        "status": "FINITE_OPPOSED_PLANAR_SEAT_GEOMETRY_VERIFIED",
        "owner_pair": [first_owner, second_owner],
        "surface_refs": [
            {
                "mesh_body_id": first_owner,
                "transient_cad_entity_tag": int(first_tag),
                "face_count": len(first_surface.face_refs),
                "outward_normal_global_xyz": list(
                    first_surface.outward_normal_global_xyz
                ),
            },
            {
                "mesh_body_id": second_owner,
                "transient_cad_entity_tag": int(second_tag),
                "face_count": len(second_surface.face_refs),
                "outward_normal_global_xyz": list(
                    second_surface.outward_normal_global_xyz
                ),
            },
        ],
        "mesh_overlay": _overlay_payload(overlay),
        "load_transfer_law_assigned": False,
        "preload_or_active_pressure_claim": False,
    }


def _classify_hardware_seats(
    inventory: Mapping[str, Any],
    wood_map: Mapping[str, str],
    metal_map: Mapping[str, str],
    body_rows: Mapping[str, Mapping[str, Any]],
    topology: MeshTopology,
) -> tuple[list[dict[str, Any]], list[str]]:
    output = []
    blockers = []
    for axis in inventory["physical_bolts"]:
        axis_id = axis["physical_bolt_id"]
        receiver_head, receiver_nut = axis["receivers_head_to_nut"]
        ids = {
            role: metal_map[f"physical_metal/{axis_id}/{role}"] for role in METAL_ROLES
        }
        expected = (
            ("head_washer_to_head", ids["head_washer"], ids["bolt"]),
            (
                "head_washer_to_first_receiver",
                ids["head_washer"],
                wood_map[receiver_head],
            ),
            ("nut_washer_to_nut", ids["nut_washer"], ids["nut"]),
            ("nut_washer_to_last_receiver", ids["nut_washer"], wood_map[receiver_nut]),
        )
        for suffix, first_owner, second_owner in expected:
            seat_id = f"{axis_id}/{suffix}"
            row = _find_plane_seat(
                seat_id, first_owner, second_owner, body_rows, topology
            )
            row["physical_bolt_id"] = axis_id
            row["seat_kind"] = suffix
            output.append(row)
            if row["status"] != "FINITE_OPPOSED_PLANAR_SEAT_GEOMETRY_VERIFIED":
                blockers.append(f"missing_or_ambiguous_seat:{seat_id}")
    return output, blockers


def _cylinder_fit(row: Mapping[str, Any]) -> dict[str, Any] | None:
    if str(row.get("cad_type", "")).casefold() != "cylinder":
        return None
    fit = row.get("analytic_surface_parameters")
    if (
        not isinstance(fit, Mapping)
        or fit.get("status")
        != "least-squares analytic-cylinder fit from CAD parametric probes"
    ):
        return None
    try:
        return {
            "point": _vec3(
                fit.get("axis_point_global_xyz_mm"), "fitted cylinder axis point"
            ),
            "direction": _unit(
                fit.get("axis_direction_global_xyz_unoriented"),
                "fitted cylinder direction",
            ),
            "radius": _number(fit.get("radius_mm"), "fitted cylinder radius"),
            "fit_residual": _number(
                fit.get("probe_fit_max_residual_mm"), "fitted cylinder residual"
            ),
        }
    except (TypeError, ValueError):
        return None


def _surface_axis_span(
    row: Mapping[str, Any], axis_origin: Vector, axis: Vector, topology: MeshTopology
) -> tuple[float, float]:
    stations = [
        _dot(_sub(topology.node_xyz_mm[node], axis_origin), axis)
        for node in _surface_nodes(row)
    ]
    return min(stations), max(stations)


def _cylinders_near_axis(
    owner: str,
    body_row: Mapping[str, Any],
    axis_origin: Vector,
    axis_direction: Vector,
    topology: MeshTopology,
    *,
    station_interval: tuple[float, float] | None = None,
    radial_orientation: str | None = None,
) -> list[tuple[str, Mapping[str, Any], dict[str, Any]]]:
    matches = []
    for tag, row in body_row["surface_inventory"].items():
        fit = _cylinder_fit(row)
        if fit is None:
            continue
        if abs(_dot(fit["direction"], axis_direction)) < CYLINDER_AXIS_DOT_MINIMUM:
            continue
        if (
            _line_distance(fit["point"], axis_origin, axis_direction)
            > CYLINDER_LINE_TOLERANCE_MM
        ):
            continue
        if radial_orientation is not None:
            sign = _cylinder_radial_normal_sign(
                owner, row, fit, topology, axis_origin, axis_direction
            )
            if radial_orientation == "internal" and sign > -0.8:
                continue
            if radial_orientation == "external" and sign < 0.8:
                continue
        low, high = _surface_axis_span(row, axis_origin, axis_direction, topology)
        if station_interval is not None:
            overlap = min(high, station_interval[1]) - max(low, station_interval[0])
            if (
                overlap
                < station_interval[1]
                - station_interval[0]
                - SHAFT_INTERVAL_TOLERANCE_MM
            ):
                continue
        matches.append((str(tag), row, fit))
    return matches


def _cylinder_radial_normal_sign(
    owner: str,
    row: Mapping[str, Any],
    fit: Mapping[str, Any],
    topology: MeshTopology,
    axis_origin: Vector,
    axis_direction: Vector,
) -> float:
    """Return signed outward-normal alignment with the cylinder radial vector.

    This distinguishes an actual internal bore wall from an external cylindrical
    boundary with the same centerline. Gmsh parametric normals are not used.
    """
    refs = tuple((int(ref[0]), int(ref[1])) for ref in row["tri6_exterior_face_refs"])
    if not refs:
        raise ValueError(f"{owner}: cylinder surface has no TRI6 exterior faces")
    sample_count = min(len(refs), 24)
    sample_indices = sorted(
        {
            round(index * (len(refs) - 1) / max(sample_count - 1, 1))
            for index in range(sample_count)
        }
    )
    signs = []
    for index in sample_indices:
        ref = refs[index]
        connectivity = topology.elements_by_owner[owner][ref[0]]
        normal, face_nodes, _face_xyz = _face_normal_and_points(
            owner, ref, connectivity, topology.node_xyz_mm
        )
        point = tuple(
            math.fsum(topology.node_xyz_mm[node][axis] for node in face_nodes)
            / len(face_nodes)
            for axis in range(3)
        )
        delta = _sub(point, fit["point"])
        radial = _sub(delta, _scale(axis_direction, _dot(delta, axis_direction)))
        if _norm(radial) <= 1e-9:
            continue
        signs.append(_dot(normal, _unit(radial, f"{owner} cylinder radial vector")))
    if not signs or min(signs) < -1 + 0.35 and max(signs) > 1 - 0.35:
        raise ValueError(f"{owner}: cylinder outward-normal radial sign is unresolved")
    return math.fsum(signs) / len(signs)


def _classify_bore_pairs(
    inventory: Mapping[str, Any],
    wood_map: Mapping[str, str],
    metal_map: Mapping[str, str],
    body_rows: Mapping[str, Mapping[str, Any]],
    topology: MeshTopology,
) -> tuple[list[dict[str, Any]], list[str]]:
    output = []
    blockers = []
    for axis_row in inventory["physical_bolts"]:
        axis_id = axis_row["physical_bolt_id"]
        origin = _vec3(axis_row["axis_origin_global_xyz_mm"], f"{axis_id} axis origin")
        direction = _unit(
            axis_row["axis_direction_head_to_nut_global_xyz"],
            f"{axis_id} axis direction",
        )
        expected = axis_row["receivers_head_to_nut"]
        receiver_intervals = {
            row["member_id"]: tuple(
                float(value)
                for value in row["projected_intervals_from_underhead_datum_mm"][0]
            )
            for row in axis_row["raw_receiver_projected_intervals"]
        }
        shaft_owner = metal_map[f"physical_metal/{axis_id}/bolt"]
        all_receiver_intervals = [
            float(value)
            for receiver in axis_row["raw_receiver_projected_intervals"]
            for interval in receiver["projected_intervals_from_underhead_datum_mm"]
            for value in interval
        ]
        shaft_coverage = (min(all_receiver_intervals), max(all_receiver_intervals))
        shaft_candidates = _cylinders_near_axis(
            shaft_owner,
            body_rows[shaft_owner],
            origin,
            direction,
            topology,
            station_interval=shaft_coverage,
            radial_orientation="external",
        )
        if len(shaft_candidates) != 1:
            blockers.append(f"shaft_axis_cylinder_unresolved:{axis_id}")
            shaft_radius = None
            shaft = None
        else:
            shaft_tag, shaft_row, shaft = shaft_candidates[0]
            shaft_radius = shaft["radius"]
            shaft_low, shaft_high = _surface_axis_span(
                shaft_row, origin, direction, topology
            )
        receiver_records = []
        pair_complete = shaft is not None
        for receiver_id in expected:
            owner = wood_map[receiver_id]
            interval = receiver_intervals[receiver_id]
            candidates = _cylinders_near_axis(
                owner,
                body_rows[owner],
                origin,
                direction,
                topology,
                station_interval=interval,
                radial_orientation="internal",
            )
            if len(candidates) != 1 or shaft_radius is None:
                pair_complete = False
                blockers.append(
                    f"receiver_bore_wall_unresolved:{axis_id}:{receiver_id}"
                )
                receiver_records.append(
                    {
                        "receiver_id": receiver_id,
                        "mesh_body_id": owner,
                        "status": "MISSING_OR_AMBIGUOUS_CYLINDRICAL_BORE_WALL",
                        "candidate_wall_surface_count": len(candidates),
                        "declared_receiver_interval_mm": list(interval),
                    }
                )
                continue
            bore_tag, bore_row, bore = candidates[0]
            gap = bore["radius"] - shaft_radius
            radial_status = (
                "OPEN_RADIAL_CLEARANCE"
                if gap > 0.02
                else (
                    "GEOMETRIC_INTERFERENCE" if gap < -0.02 else "NOMINAL_RADIAL_TOUCH"
                )
            )
            if gap <= 0.02:
                pair_complete = False
                blockers.append(
                    f"nonpositive_or_unresolved_radial_clearance:{axis_id}:{receiver_id}"
                )
            receiver_records.append(
                {
                    "receiver_id": receiver_id,
                    "mesh_body_id": owner,
                    "status": "CYLINDRICAL_BORE_WALL_BOUND_TO_DECLARED_AXIS",
                    "transient_cad_entity_tag": int(bore_tag),
                    "tri6_face_count": len(bore_row["tri6_exterior_face_refs"]),
                    "declared_receiver_interval_mm": list(interval),
                    "fitted_bore_axis_line_distance_mm": _line_distance(
                        bore["point"], origin, direction
                    ),
                    "fitted_bore_axis_alignment": abs(
                        _dot(bore["direction"], direction)
                    ),
                    "fitted_bore_radius_mm": bore["radius"],
                    "fitted_bore_radius_residual_mm": bore["fit_residual"],
                    "shaft_radius_mm": shaft_radius,
                    "radial_clearance_mm": gap,
                    "radial_status": radial_status,
                }
            )
        if shaft is not None:
            receiver_span = (
                min(interval[0] for interval in receiver_intervals.values()),
                max(interval[1] for interval in receiver_intervals.values()),
            )
            if (
                shaft_low > receiver_span[0] + SHAFT_INTERVAL_TOLERANCE_MM
                or shaft_high < receiver_span[1] - SHAFT_INTERVAL_TOLERANCE_MM
            ):
                pair_complete = False
                blockers.append(
                    f"shaft_surface_does_not_cover_both_receivers:{axis_id}"
                )
            shaft_record = {
                "physical_body_id": f"physical_metal/{axis_id}/bolt",
                "mesh_body_id": shaft_owner,
                "transient_cad_entity_tag": int(shaft_tag),
                "tri6_face_count": len(shaft_row["tri6_exterior_face_refs"]),
                "axis_interval_mm": [shaft_low, shaft_high],
                "fitted_axis_line_distance_mm": _line_distance(
                    shaft["point"], origin, direction
                ),
                "fitted_axis_alignment": abs(_dot(shaft["direction"], direction)),
                "fitted_radius_mm": shaft_radius,
                "fitted_radius_residual_mm": shaft["fit_residual"],
            }
        else:
            shaft_record = None
        if (
            len(receiver_records) != 2
            or [row["receiver_id"] for row in receiver_records] != expected
        ):
            pair_complete = False
        output.append(
            {
                "physical_bolt_id": axis_id,
                "status": "BORE_PAIR_IDENTITY_AND_OPEN_GAP_BOUND"
                if pair_complete
                else "BORE_PAIR_INCOMPLETE",
                "head_to_nut_receiver_order": expected,
                "bore_receiver_membership": axis_row[
                    "bore_receiver_ids_membership_only"
                ],
                "shaft_surface": shaft_record,
                "receiver_bore_walls": receiver_records,
                "contact_active": False,
                "radial_gap_is_explicitly_open": all(
                    row.get("radial_status") == "OPEN_RADIAL_CLEARANCE"
                    for row in receiver_records
                ),
                "bolt_to_wood_bearing_law_assigned": False,
            }
        )
    return output, blockers


def _classify_hardware_radial_clearances(
    inventory: Mapping[str, Any],
    metal_map: Mapping[str, str],
    body_rows: Mapping[str, Mapping[str, Any]],
    topology: MeshTopology,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Bind washer and nut internal walls to each bolt axis without closing gaps."""
    output = []
    blockers = []
    for axis_row in inventory["physical_bolts"]:
        axis_id = axis_row["physical_bolt_id"]
        origin = _vec3(axis_row["axis_origin_global_xyz_mm"], f"{axis_id} axis origin")
        direction = _unit(
            axis_row["axis_direction_head_to_nut_global_xyz"],
            f"{axis_id} axis direction",
        )
        receiver_bounds = [
            float(value)
            for receiver in axis_row["raw_receiver_projected_intervals"]
            for interval in receiver["projected_intervals_from_underhead_datum_mm"]
            for value in interval
        ]
        bolt_owner = metal_map[f"physical_metal/{axis_id}/bolt"]
        shaft_candidates = _cylinders_near_axis(
            bolt_owner,
            body_rows[bolt_owner],
            origin,
            direction,
            topology,
            station_interval=(min(receiver_bounds), max(receiver_bounds)),
            radial_orientation="external",
        )
        if len(shaft_candidates) != 1:
            blockers.append(
                f"shaft_axis_cylinder_unresolved_for_hardware_bores:{axis_id}"
            )
            shaft_radius = None
            shaft_surface = None
        else:
            shaft_tag, _shaft_row, shaft_surface = shaft_candidates[0]
            shaft_radius = float(shaft_surface["radius"])

        role_rows = {row["role"]: row for row in axis_row["physical_hardware_roles"]}
        for role in ("head_washer", "nut_washer", "nut"):
            physical_id = f"physical_metal/{axis_id}/{role}"
            owner = metal_map[physical_id]
            intervals = role_rows[role].get("axial_projection_from_underhead_datum_mm")
            if not isinstance(intervals, list) or len(intervals) != 1:
                blockers.append(f"hardware_axial_interval_unresolved:{axis_id}:{role}")
                output.append(
                    {
                        "physical_bolt_id": axis_id,
                        "physical_body_id": physical_id,
                        "component_role": role,
                        "status": "HARDWARE_AXIAL_INTERVAL_UNRESOLVED",
                        "candidate_internal_bore_count": 0,
                        "bolt_shank_contact_active": False,
                    }
                )
                continue
            interval = tuple(
                _number(value, f"{axis_id}/{role} interval") for value in intervals[0]
            )
            candidates = _cylinders_near_axis(
                owner,
                body_rows[owner],
                origin,
                direction,
                topology,
                station_interval=interval,
                radial_orientation="internal",
            )
            if len(candidates) != 1 or shaft_radius is None:
                reason = "internal_bore_wall_missing_or_ambiguous"
                if role == "nut":
                    blockers.append(f"nut_internal_bore_unmodeled:{axis_id}")
                    outer_candidates = _cylinders_near_axis(
                        owner,
                        body_rows[owner],
                        origin,
                        direction,
                        topology,
                        station_interval=interval,
                        radial_orientation="external",
                    )
                    nut_geometry: dict[str, Any] | None = None
                    if len(outer_candidates) == 1 and shaft_surface is not None:
                        outer_tag, outer_row, outer = outer_candidates[0]
                        shaft_low, shaft_high = _surface_axis_span(
                            body_rows[bolt_owner]["surface_inventory"][str(shaft_tag)],
                            origin,
                            direction,
                            topology,
                        )
                        overlap_length = max(
                            0.0,
                            min(shaft_high, interval[1]) - max(shaft_low, interval[0]),
                        )
                        if outer["radius"] > shaft_radius and overlap_length > 0:
                            volume = math.pi * shaft_radius**2 * overlap_length
                            nut_geometry = {
                                "status": "COAXIAL_SOLID_NUT_ENVELOPE_OVERLAPS_BOLT_SHAFT",
                                "external_surface_transient_cad_entity_tag": int(
                                    outer_tag
                                ),
                                "external_radius_mm": outer["radius"],
                                "external_axis_line_distance_mm": _line_distance(
                                    outer["point"], origin, direction
                                ),
                                "external_axis_alignment": abs(
                                    _dot(outer["direction"], direction)
                                ),
                                "external_cylinder_radial_normal_sign": _cylinder_radial_normal_sign(
                                    owner,
                                    outer_row,
                                    outer,
                                    topology,
                                    origin,
                                    direction,
                                ),
                                "planar_surface_count": sum(
                                    str(surface.get("cad_type", "")).casefold()
                                    == "plane"
                                    for surface in body_rows[owner][
                                        "surface_inventory"
                                    ].values()
                                ),
                                "cylindrical_surface_count": sum(
                                    str(surface.get("cad_type", "")).casefold()
                                    == "cylinder"
                                    for surface in body_rows[owner][
                                        "surface_inventory"
                                    ].values()
                                ),
                                "nut_internal_bore_wall_count": 0,
                                "shaft_radius_mm": shaft_radius,
                                "coaxial_overlap_interval_mm": [
                                    max(shaft_low, interval[0]),
                                    min(shaft_high, interval[1]),
                                ],
                                "coaxial_source_overlap_volume_mm3": volume,
                                "overlap_basis": (
                                    "analytic intersection of the fitted continuous bolt-shaft cylinder with the "
                                    "source nut's fitted closed external cylindrical envelope; no OCC boolean was run"
                                ),
                            }
                            blockers.append(f"nut_solid_overlaps_bolt_shaft:{axis_id}")
                else:
                    blockers.append(f"washer_internal_bore_unresolved:{axis_id}:{role}")
                output.append(
                    {
                        "physical_bolt_id": axis_id,
                        "physical_body_id": physical_id,
                        "component_role": role,
                        "status": "MISSING_INTERNAL_BORE_WALL",
                        "candidate_internal_bore_count": len(candidates),
                        "declared_axial_interval_mm": list(interval),
                        "shaft_surface": None,
                        "source_nut_geometry": nut_geometry if role == "nut" else None,
                        "bolt_shank_contact_active": False,
                        "interpretation": reason,
                    }
                )
                continue
            tag, bore_row, bore = candidates[0]
            gap = float(bore["radius"]) - shaft_radius
            gap_status = (
                "OPEN_RADIAL_CLEARANCE"
                if gap > 0.02
                else (
                    "GEOMETRIC_INTERFERENCE" if gap < -0.02 else "NOMINAL_RADIAL_TOUCH"
                )
            )
            if gap <= 0.02:
                blockers.append(f"hardware_radial_gap_not_open:{axis_id}:{role}")
            output.append(
                {
                    "physical_bolt_id": axis_id,
                    "physical_body_id": physical_id,
                    "component_role": role,
                    "status": "INTERNAL_BORE_BOUND_TO_DECLARED_BOLT_AXIS",
                    "transient_cad_entity_tag": int(tag),
                    "tri6_face_count": len(bore_row["tri6_exterior_face_refs"]),
                    "declared_axial_interval_mm": list(interval),
                    "fitted_axis_line_distance_mm": _line_distance(
                        bore["point"], origin, direction
                    ),
                    "fitted_axis_alignment": abs(_dot(bore["direction"], direction)),
                    "fitted_internal_radius_mm": bore["radius"],
                    "fitted_radius_residual_mm": bore["fit_residual"],
                    "shaft_radius_mm": shaft_radius,
                    "radial_clearance_mm": gap,
                    "radial_status": gap_status,
                    "shaft_surface": {
                        "physical_body_id": f"physical_metal/{axis_id}/bolt",
                        "transient_cad_entity_tag": int(shaft_tag),
                        "radius_mm": shaft_radius,
                    },
                    "bolt_shank_contact_active": False,
                }
            )
    return output, blockers


def _validate_source_mesh_binding(
    inventory_path: Path,
    mesh_report_path: Path,
    mesh_deck_path: Path,
    inventory: Mapping[str, Any],
    mesh_report: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        mesh_report.get("schema") != MESH_SCHEMA
        or mesh_report.get("status") != MESH_STATUS
    ):
        raise ValueError(
            "mesh report is not the verified current-patch C3D10-only schema"
        )
    if (
        mesh_report.get("accepted") is not False
        or mesh_report.get("solved") is not False
        or mesh_report.get("native_solve_run") is not False
    ):
        raise ValueError(
            "mesh report contains a solve or acceptance claim outside this adapter scope"
        )
    if mesh_report.get("contact_or_interface_classification_assigned") is not False:
        raise ValueError(
            "mesh report already assigns a contact/interface classification"
        )
    bundle_binding = mesh_report.get("current_candidate_binding")
    candidate = inventory.get("candidate")
    if not isinstance(bundle_binding, Mapping) or not isinstance(candidate, Mapping):
        raise TypeError("mesh report candidate/source bundle binding is incomplete")
    if (
        bundle_binding.get("revision_id") != REVISION_ID
        or bundle_binding.get("implementation_revision") != IMPLEMENTATION_REVISION
        or bundle_binding.get("revision_id") != candidate.get("revision_id")
        or bundle_binding.get("implementation_revision")
        != candidate.get("implementation_revision")
        or bundle_binding.get("source_inventory_sha256")
        != candidate.get("source_inventory_sha256")
    ):
        raise ValueError("mesh and manifest candidate revision bindings differ")
    report_context = mesh_report.get("input_geometry_context")
    if not isinstance(report_context, Mapping):
        raise TypeError("mesh report lacks its frozen input geometry context")
    for key in (
        "wood_bodies",
        "physical_bolts",
        "physical_metal_bodies",
        "wood_interfaces",
    ):
        if report_context.get(key) != inventory.get(key):
            raise ValueError(
                f"mesh report source context differs from current inventory: {key}"
            )
    if report_context.get("migration_blockers") != inventory.get(
        "migration_blockers", []
    ):
        raise ValueError(
            "mesh report migration blocker snapshot differs from the source inventory"
        )

    bundle_dir = Path(str(mesh_report.get("input_bundle_directory", ""))).expanduser()
    if not bundle_dir.is_dir():
        # Run records may retain the producer's container mount. The supplied
        # manifest still has to be the local immutable bundle with identical
        # report hashes and the full hash-indexed artifact set.
        bundle_dir = inventory_path.parent
    bundle_dir = bundle_dir.resolve()
    if inventory_path.resolve() != (bundle_dir / "inventory.json").resolve():
        raise ValueError(
            "supplied source inventory is not the input bundle named by the mesh report"
        )
    inventory_bytes = inventory_path.read_bytes()
    if sha256_bytes(inventory_bytes) != mesh_report.get(
        "input_bundle_inventory_sha256"
    ):
        raise ValueError(
            "current-patch inventory SHA differs from the frozen mesh input"
        )
    hash_path = bundle_dir / "sha256.json"
    hash_bytes, hash_index = _json(hash_path, "current-patch SHA256 index")
    if sha256_bytes(hash_bytes) != mesh_report.get("input_bundle_hash_index_sha256"):
        raise ValueError("current-patch SHA index differs from the frozen mesh input")
    before = mesh_report.get("input_bundle_file_sha256_before")
    after = mesh_report.get("input_bundle_file_sha256_after")
    if not isinstance(before, Mapping) or before != after:
        raise ValueError(
            "mesh report does not prove stable input bundle hashes during meshing"
        )
    if hash_index != {
        key: value for key, value in before.items() if key not in {"sha256.json"}
    }:
        # The mesh worker records sha256.json as an outer file, while the index
        # intentionally indexes itself only through the report SHA.
        expected_index = {
            key: value for key, value in before.items() if key not in {"sha256.json"}
        }
        if hash_index != expected_index:
            raise ValueError(
                "current input SHA index differs from the mesh worker's frozen file hashes"
            )
    for relative, digest in hash_index.items():
        target = bundle_dir / relative
        if (
            not target.is_file()
            or target.is_symlink()
            or sha256_bytes(target.read_bytes()) != digest
        ):
            raise ValueError(
                f"current-patch source artifact is missing or changed: {relative}"
            )

    deck_rel = mesh_report.get("mesh_input_file")
    expected_deck = (mesh_report_path.parent / str(deck_rel)).resolve()
    if mesh_deck_path.resolve() != expected_deck:
        raise ValueError(
            "mesh deck path differs from the path bound by the mesh report"
        )
    deck_hash = sha256_bytes(mesh_deck_path.read_bytes())
    if deck_hash != mesh_report.get("mesh_input_sha256"):
        raise ValueError("current mesh deck SHA differs from the frozen mesh report")
    before_sources = mesh_report.get("mesh_worker_source_sha256")
    after_sources = mesh_report.get("mesh_worker_source_sha256_after")
    if not isinstance(before_sources, Mapping) or before_sources != after_sources:
        raise ValueError(
            "mesh preparation source hashes changed during mesh generation"
        )
    for relative, digest in before_sources.items():
        source = ROOT / relative
        if not source.is_file() or sha256_bytes(source.read_bytes()) != digest:
            raise ValueError(
                f"mesh preparation source changed after mesh freeze: {relative}"
            )
    return {
        "inventory_sha256": sha256_bytes(inventory_bytes),
        "hash_index_sha256": sha256_bytes(hash_bytes),
        "mesh_report_sha256": sha256_bytes(mesh_report_path.read_bytes()),
        "mesh_input_sha256": deck_hash,
        "mesh_worker_source_sha256": dict(before_sources),
    }


def classify_current_patch(
    inventory_path: str | Path,
    mesh_report_path: str | Path,
    mesh_deck_path: str | Path,
) -> dict[str, Any]:
    """Return a source-bound geometry-only contact classification report."""
    inventory_path = Path(inventory_path).expanduser().resolve()
    mesh_report_path = Path(mesh_report_path).expanduser().resolve()
    mesh_deck_path = Path(mesh_deck_path).expanduser().resolve()
    _inventory_bytes, inventory = _json(inventory_path, "current-patch inventory")
    _mesh_report_bytes, mesh_report = _json(
        mesh_report_path, "current-patch mesh report"
    )
    _validate_current_inventory(inventory)
    binding = _validate_source_mesh_binding(
        inventory_path, mesh_report_path, mesh_deck_path, inventory, mesh_report
    )
    wood_map, metal_map, body_rows = _body_maps(inventory, mesh_report)
    nodes, elements = _parse_deck(mesh_deck_path, tuple(body_rows))
    topology = _validate_mesh_topology(mesh_report, body_rows, nodes, elements)

    wood_interfaces, blockers = _classify_wood_interfaces(
        inventory, wood_map, body_rows, topology
    )
    hardware_seats, seat_blockers = _classify_hardware_seats(
        inventory, wood_map, metal_map, body_rows, topology
    )
    bore_pairs, bore_blockers = _classify_bore_pairs(
        inventory, wood_map, metal_map, body_rows, topology
    )
    hardware_radial, hardware_radial_blockers = _classify_hardware_radial_clearances(
        inventory, metal_map, body_rows, topology
    )
    blockers.extend(seat_blockers)
    blockers.extend(bore_blockers)
    blockers.extend(hardware_radial_blockers)
    seat_centroid_residuals = [
        value
        for row in hardware_seats
        for value in (
            row.get("mesh_overlay", {}).get(
                "candidate_nodal_area_centroid_residual_mm"
            ),
            row.get("mesh_overlay", {}).get("host_nodal_area_centroid_residual_mm"),
        )
        if isinstance(value, (float, int)) and math.isfinite(value)
    ]
    response_blockers = [
        "no_contact_constitutive_or_enforcement_law_assigned",
        "assembly_state_and_preload_are_not_established",
        "nut_thread_engagement_is_not_modeled_or_verified",
        "bolt_shank_radial_clearances_are_open_on_receiver_members_and_washers",
        "nut_to_shaft_radial_contact_is_unresolved_where_the_nut_bore_is_unmodeled",
        "axial_seat_geometry_does_not_constrain_lateral_nut_or_washer_drift",
        "material_boundary_load_and_joint_response_contracts_are_pending",
    ]
    blockers.extend(response_blockers)
    geometry_complete = (
        len(wood_interfaces) == 3
        and len(hardware_seats) == 16
        and len(bore_pairs) == 4
        and len(hardware_radial) == 12
        and all(
            row["status"] == "FINITE_MESH_PATCH_OVERLAY_VERIFIED_GEOMETRY_ONLY"
            for row in wood_interfaces
        )
        and all(
            row["status"] == "FINITE_OPPOSED_PLANAR_SEAT_GEOMETRY_VERIFIED"
            for row in hardware_seats
        )
        and all(
            row["status"] == "BORE_PAIR_IDENTITY_AND_OPEN_GAP_BOUND"
            for row in bore_pairs
        )
        and all(
            row["status"] == "INTERNAL_BORE_BOUND_TO_DECLARED_BOLT_AXIS"
            for row in hardware_radial
        )
    )
    return {
        "schema": SCHEMA,
        "status": "CURRENT_PATCH_CONTACT_GEOMETRY_CLASSIFIED_RESPONSE_UNREADY"
        if geometry_complete
        else "CURRENT_PATCH_CONTACT_GEOMETRY_INCOMPLETE_RESPONSE_UNREADY",
        "candidate_binding": {
            "revision_id": REVISION_ID,
            "implementation_revision": IMPLEMENTATION_REVISION,
            **binding,
        },
        "scope": {
            "wood_members": 3,
            "physical_bolts": 4,
            "physical_metal_bodies": 16,
            "wood_finite_interfaces": 3,
            "washer_wood_seats": 8,
            "head_washer_seats": 4,
            "nut_washer_seats": 4,
            "bolt_receiver_bore_pairs": 4,
            "receiver_bore_walls_expected": 8,
            "washer_hole_radial_clearances_expected": 8,
            "nut_bore_radial_clearances_expected": 4,
        },
        "mesh_owner_maps": {
            "wood_body_ids": wood_map,
            "physical_metal_body_ids": metal_map,
        },
        "wood_interfaces": wood_interfaces,
        "hardware_seats": hardware_seats,
        "bolt_receiver_bore_pairs": bore_pairs,
        "bolt_hardware_radial_clearances": hardware_radial,
        "geometry_classification_complete": geometry_complete,
        "response_ready": False,
        "native_solve_ready": False,
        "contact_laws_assigned": False,
        "thread_engagement_verified": False,
        "seat_nodal_area_centroid_tolerance_mm": SEAT_NODAL_AREA_CENTROID_TOLERANCE_MM,
        "seat_overlay_tolerance_basis": (
            "The 0.02 mm limit is a geometry-only coarse-mesh area-lumping tolerance, not a frozen criterion or force/contact accuracy claim."
        ),
        "seat_overlay_max_nodal_area_centroid_residual_mm": max(
            seat_centroid_residuals, default=None
        ),
        "seat_overlay_initial_probe_residual_mm": 0.00425031,
        "blockers": blockers,
        "limits": [
            "Finite-mesh geometry classification only; it assigns no contact law, tie, preload, or active pressure.",
            "CAD entity tags are transient pointers and are never used as interface or bore identities.",
            "Open bolt-shank/bore radial gaps remain explicit and do not transfer load in this classification.",
            "Geometry and mesh results are not physical joint acceptance or a fabrication release.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("mesh_report", type=Path)
    parser.add_argument("mesh_deck", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = classify_current_patch(args.inventory, args.mesh_report, args.mesh_deck)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps({"status": report["status"], "output": str(args.output)}, indent=2)
    )


if __name__ == "__main__":
    main()
