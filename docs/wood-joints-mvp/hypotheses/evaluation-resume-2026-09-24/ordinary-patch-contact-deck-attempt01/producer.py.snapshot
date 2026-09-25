"""Render the frozen current-patch geometry as contact cards only.

The adapter is pinned to the current three-wood/four-bolt classification and
mesh attempt. It emits no material, restraint, load, axial-engagement, or solver
step cards and cannot be used as a complete model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fea.floor_contact import FACES
from fea.stitch_joint_mesh import external_faces
from fea.wood_joint_patch_contact_contract import (
    _render_contact_cards,
    parse_c3d10_deck,
)

ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
CLASSIFICATION_PATH = (
    EVALUATION_DIR
    / "ordinary-patch-contact-classification-attempt01/classification.json"
)
MESH_REPORT_PATH = EVALUATION_DIR / "ordinary-patch-mesh-attempt02/mesh/mesh.json"
MESH_DECK_PATH = EVALUATION_DIR / "ordinary-patch-mesh-attempt02/mesh/mesh.inp"

SCHEMA = "wood_joint_current_contact_deck_fragment/v1"
CLASSIFICATION_SCHEMA = "wood_joint_current_patch_contact_classification/v1"
CLASSIFICATION_SHA256 = (
    "18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13"
)
MESH_SCHEMA = "wood_joint_current_patch_mesh/v1"
MESH_REPORT_SHA256 = "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07"
MESH_DECK_SHA256 = "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803"
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
IMPLEMENTATION_REVISION = "b1e8707d"
INTERACTION_NAME = "WJCP_CURRENT_NUMERICAL_CONTACT"

EXPECTED_COUNTS = {
    "wood_interfaces": 3,
    "planar_hardware_seats": 16,
    "wood_bore_to_shaft_pairs": 8,
    "washer_bore_to_shaft_pairs": 8,
    "intentional_nut_bore_omissions": 4,
    "contact_pairs": 35,
}
FACE_NORMAL_ALIGNMENT_MINIMUM = 0.999998
OPPOSED_NORMAL_DOT_MAXIMUM = -0.95
RADIAL_NORMAL_ALIGNMENT_MINIMUM = 0.8
AXIAL_STATION_TOLERANCE_MM = 1e-7
PLANE_RESIDUAL_TOLERANCE_MM = 1e-5
RADIUS_TOLERANCE_MM = 0.02
RADIAL_GAP_TOLERANCE_MM = 1e-6
CCX_MANUAL_PDF = ROOT / "fea/generated/connection/ccx_2.21.pdf"
CCX_MANUAL_SHA256 = "16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8"


@dataclass(frozen=True)
class MeshData:
    report_path: Path
    deck_path: Path
    report: dict[str, Any]
    report_sha256: str
    deck_sha256: str
    nodes: dict[int, tuple[float, float, float]]
    elements: dict[int, tuple[int, ...]]
    elsets: dict[str, set[int]]
    body_nodes: dict[str, set[int]]
    body_elements: dict[str, set[int]]
    body_surfaces: dict[str, dict[str, dict[str, Any]]]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(path: Path, context: str) -> tuple[bytes, dict[str, Any]]:
    try:
        payload = path.read_bytes()
        record = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{context} missing or invalid: {path}") from error
    if not isinstance(record, dict):
        raise TypeError(f"{context} root must be an object")
    return payload, record


def _positive_penalty(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("penalty_n_per_mm3 must be an explicit positive finite number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError("penalty_n_per_mm3 must be an explicit positive finite number")
    return number


def _vec3(value: Any, context: str) -> tuple[float, float, float]:
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context} must be a finite XYZ vector") from error
    if len(result) != 3 or any(not math.isfinite(component) for component in result):
        raise ValueError(f"{context} must be a finite XYZ vector")
    return result  # type: ignore[return-value]


def _dot(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def _norm(vector: tuple[float, ...]) -> float:
    return math.sqrt(_dot(vector, vector))


def _unit(vector: tuple[float, ...], context: str) -> tuple[float, float, float]:
    length = _norm(vector)
    if not math.isfinite(length) or length <= 0:
        raise ValueError(f"{context} must be nonzero and finite")
    return tuple(value / length for value in vector)  # type: ignore[return-value]


def _cross(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _sub(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _load_classification(path: Path) -> tuple[dict[str, Any], str]:
    payload, classification = _json(path, "current contact classification")
    digest = _sha256(payload)
    if digest != CLASSIFICATION_SHA256:
        raise ValueError("classification digest is not the frozen final attempt 01")
    if (
        classification.get("schema") != CLASSIFICATION_SCHEMA
        or classification.get("status")
        != "CURRENT_PATCH_CONTACT_GEOMETRY_INCOMPLETE_RESPONSE_UNREADY"
        or classification.get("geometry_classification_complete") is not False
        or classification.get("response_ready") is not False
        or classification.get("native_solve_ready") is not False
        or classification.get("contact_laws_assigned") is not False
    ):
        raise ValueError(
            "classification scope/readiness is not the frozen unready diagnostic"
        )
    binding = classification.get("candidate_binding")
    if not isinstance(binding, dict) or (
        binding.get("revision_id") != REVISION_ID
        or binding.get("implementation_revision") != IMPLEMENTATION_REVISION
        or binding.get("mesh_report_sha256") != MESH_REPORT_SHA256
        or binding.get("mesh_input_sha256") != MESH_DECK_SHA256
    ):
        raise ValueError("classification does not bind the frozen current mesh attempt")
    return classification, digest


def _face_nodes(connectivity: tuple[int, ...], face_number: int) -> tuple[int, ...]:
    if face_number not in (1, 2, 3, 4):
        raise ValueError(f"invalid C3D10 local face number {face_number}")
    return tuple(connectivity[index] for index in FACES[face_number - 1])


def _face_outward_normal(
    nodes: dict[int, tuple[float, float, float]],
    connectivity: tuple[int, ...],
    face_number: int,
) -> tuple[float, float, float]:
    corner_nodes = _face_nodes(connectivity, face_number)[:3]
    points = tuple(nodes[node] for node in corner_nodes)
    normal = _unit(
        _cross(_sub(points[1], points[0]), _sub(points[2], points[0])),
        "C3D10 face normal",
    )
    opposite = set(connectivity[:4]) - set(corner_nodes)
    if len(opposite) != 1:
        raise ValueError("C3D10 face has no unique opposite corner")
    center = tuple(math.fsum(point[i] for point in points) / 3 for i in range(3))
    if _dot(normal, _sub(nodes[next(iter(opposite))], center)) > 0:
        normal = tuple(-value for value in normal)
    return normal


def _face_center(
    nodes: dict[int, tuple[float, float, float]],
    connectivity: tuple[int, ...],
    face_number: int,
) -> tuple[float, float, float]:
    points = tuple(nodes[node] for node in _face_nodes(connectivity, face_number)[:3])
    return tuple(math.fsum(point[i] for point in points) / 3 for i in range(3))  # type: ignore[return-value]


def _normalize_refs(value: Any, context: str) -> tuple[tuple[int, int], ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{context}: owner facet references must be a nonempty list")
    refs = []
    for raw in value:
        if not isinstance(raw, (list, tuple)) or len(raw) != 2:
            raise ValueError(f"{context}: each facet ref must be [element, local_face]")
        element, side = raw
        if isinstance(element, bool) or isinstance(side, bool):
            raise TypeError(f"{context}: element/face IDs must be exact integers")
        try:
            element_i, side_i = int(element), int(side)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(f"{context}: malformed element/face ID") from error
        if (
            element_i != element
            or side_i != side
            or element_i <= 0
            or side_i not in (1, 2, 3, 4)
        ):
            raise ValueError(f"{context}: facet ID outside C3D10 range")
        refs.append((element_i, side_i))
    if len(set(refs)) != len(refs):
        raise ValueError(f"{context}: duplicate element facets")
    return tuple(sorted(refs))


def _load_mesh(report_path: Path, deck_path: Path) -> MeshData:
    report_bytes, report = _json(report_path, "current patch mesh report")
    report_sha = _sha256(report_bytes)
    if report_sha != MESH_REPORT_SHA256:
        raise ValueError("mesh report digest is not the frozen attempt 02")
    try:
        deck_bytes = deck_path.read_bytes()
    except OSError as error:
        raise ValueError(f"current patch mesh deck unavailable: {deck_path}") from error
    deck_sha = _sha256(deck_bytes)
    if deck_sha != MESH_DECK_SHA256 or report.get("mesh_input_sha256") != deck_sha:
        raise ValueError("mesh deck digest is not the frozen attempt 02")
    report_deck = (
        report_path.parent / str(report.get("mesh_input_file", ""))
    ).resolve()
    if report_deck != deck_path.resolve():
        raise ValueError("supplied mesh deck path differs from the mesh report binding")
    if (
        report.get("schema") != MESH_SCHEMA
        or report.get("status") != "VERIFIED_C3D10_CURRENT_PATCH_MESH_ONLY_NO_SOLVER"
        or report.get("accepted") is not False
        or report.get("solved") is not False
        or report.get("native_solve_run") is not False
        or report.get("contact_or_interface_classification_assigned") is not False
        or report.get("body_count") != 19
        or report.get("wood_body_count") != 3
        or report.get("physical_metal_body_count") != 16
    ):
        raise ValueError(
            "mesh report is outside the frozen current-only unsolved scope"
        )
    binding = report.get("current_candidate_binding")
    if not isinstance(binding, dict) or (
        binding.get("revision_id") != REVISION_ID
        or binding.get("implementation_revision") != IMPLEMENTATION_REVISION
    ):
        raise ValueError("mesh report candidate revision does not match current inputs")

    try:
        nodes, elements, elsets = parse_c3d10_deck(
            deck_bytes.decode("utf-8"), context="current patch mesh"
        )
    except UnicodeDecodeError as error:
        raise ValueError("current patch mesh deck is not UTF-8") from error
    bodies = report.get("bodies")
    if not isinstance(bodies, dict) or len(bodies) != 19:
        raise ValueError("mesh report does not contain exactly 19 body owners")

    body_nodes: dict[str, set[int]] = {}
    body_elements: dict[str, set[int]] = {}
    body_surfaces: dict[str, dict[str, dict[str, Any]]] = {}
    seen_node_ids: set[int] = set()
    seen_element_ids: set[int] = set()
    owner_kind_counts: Counter[str] = Counter()
    for mesh_body_id, body in bodies.items():
        if not isinstance(body, dict):
            raise TypeError(f"{mesh_body_id}: body report must be an object")
        owner_kind_counts[str(body.get("owner_kind"))] += 1
        expected_elset = str(body.get("element_elset_name", "")).upper()
        if not expected_elset or expected_elset not in elsets:
            raise ValueError(f"{mesh_body_id}: mesh body ELSET missing from deck")
        body_element_ids = {int(value) for value in body.get("elements", ())}
        body_node_ids = {int(value) for value in body.get("nodes", ())}
        if not body_element_ids or body_element_ids != elsets[expected_elset]:
            raise ValueError(
                f"{mesh_body_id}: reported elements differ from owner ELSET"
            )
        conn_node_ids = {
            node for element in body_element_ids for node in elements[element]
        }
        if not body_node_ids or body_node_ids != conn_node_ids:
            raise ValueError(
                f"{mesh_body_id}: reported node ownership differs from C3D10 connectivity"
            )
        if seen_element_ids.intersection(
            body_element_ids
        ) or seen_node_ids.intersection(body_node_ids):
            raise ValueError("mesh report body ownership is not disjoint")
        seen_element_ids.update(body_element_ids)
        seen_node_ids.update(body_node_ids)

        exterior = external_faces(
            {element: elements[element] for element in body_element_ids}
        )
        expected_refs = {(record[0], record[1]) for record in exterior.values()}
        surface_inventory = body.get("surface_inventory")
        if not isinstance(surface_inventory, dict) or not surface_inventory:
            raise ValueError(f"{mesh_body_id}: exact CAD face inventory is missing")
        seen_surface_refs: set[tuple[int, int]] = set()
        normalized_surfaces: dict[str, dict[str, Any]] = {}
        for tag_text, surface in surface_inventory.items():
            if not isinstance(surface, dict):
                raise TypeError(
                    f"{mesh_body_id}/{tag_text}: surface row must be an object"
                )
            try:
                tag = int(tag_text)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"{mesh_body_id}: transient CAD tag is not an integer"
                ) from error
            if surface.get("cad_entity_tag") != tag:
                raise ValueError(
                    f"{mesh_body_id}/{tag}: transient CAD tag does not match its key"
                )
            refs = _normalize_refs(
                surface.get("tri6_exterior_face_refs"), f"{mesh_body_id}/{tag}"
            )
            if any(element not in body_element_ids for element, _face in refs):
                raise ValueError(
                    f"{mesh_body_id}/{tag}: a facet is owned by another C3D10 body"
                )
            if seen_surface_refs.intersection(refs):
                raise ValueError(
                    f"{mesh_body_id}: an exterior C3D10 facet has multiple CAD owners"
                )
            seen_surface_refs.update(refs)
            node_union = {
                node
                for element, side in refs
                for node in _face_nodes(elements[element], side)
            }
            try:
                declared_nodes = {int(node) for node in surface["tri6_node_ids"]}
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    f"{mesh_body_id}/{tag}: TRI6 node union is malformed"
                ) from error
            if declared_nodes != node_union or not node_union <= body_node_ids:
                raise ValueError(
                    f"{mesh_body_id}/{tag}: TRI6 node union disagrees with C3D10 facets"
                )
            normalized_surfaces[str(tag)] = surface
        if seen_surface_refs != expected_refs:
            raise ValueError(
                f"{mesh_body_id}: CAD surfaces do not own every exterior facet exactly once"
            )
        body_nodes[mesh_body_id] = body_node_ids
        body_elements[mesh_body_id] = body_element_ids
        body_surfaces[mesh_body_id] = normalized_surfaces

    if (
        seen_node_ids != set(nodes)
        or seen_element_ids != set(elements)
        or owner_kind_counts != Counter({"wood_member": 3, "physical_metal": 16})
    ):
        raise ValueError(
            "body ownership does not cover exact current 3-wood/16-metal C3D10 mesh"
        )
    return MeshData(
        report_path=report_path,
        deck_path=deck_path,
        report=report,
        report_sha256=report_sha,
        deck_sha256=deck_sha,
        nodes=nodes,
        elements=elements,
        elsets=elsets,
        body_nodes=body_nodes,
        body_elements=body_elements,
        body_surfaces=body_surfaces,
    )


def _surface(
    mesh: MeshData, owner: str, tag_value: Any, context: str
) -> tuple[int, dict[str, Any], tuple[tuple[int, int], ...]]:
    if isinstance(tag_value, bool):
        raise TypeError(f"{context}: transient CAD tag must be an integer")
    try:
        tag = int(tag_value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: transient CAD tag must be an integer") from error
    if tag <= 0 or tag != tag_value:
        raise ValueError(
            f"{context}: transient CAD tag must be a positive exact integer"
        )
    try:
        row = mesh.body_surfaces[owner][str(tag)]
    except KeyError as error:
        raise ValueError(
            f"{context}: tag {tag} is absent from exact owner {owner}"
        ) from error
    refs = _normalize_refs(
        row.get("tri6_exterior_face_refs"), f"{context}/{owner}/{tag}"
    )
    if any(element not in mesh.body_elements[owner] for element, _face in refs):
        raise ValueError(f"{context}: selected facet ownership differs from {owner}")
    return tag, row, refs


def _check_planar_surface(
    mesh: MeshData,
    owner: str,
    row: dict[str, Any],
    expected_normal_value: Any,
    context: str,
) -> dict[str, Any]:
    expected = _unit(_vec3(expected_normal_value, f"{context} source normal"), context)
    if str(row.get("cad_type", "")).casefold() != "plane":
        raise ValueError(
            f"{context}: classified seat must resolve to a planar CAD surface"
        )
    refs = _normalize_refs(row["tri6_exterior_face_refs"], context)
    alignments = [
        _dot(_face_outward_normal(mesh.nodes, mesh.elements[element], side), expected)
        for element, side in refs
    ]
    minimum_alignment = min(alignments)
    if minimum_alignment < FACE_NORMAL_ALIGNMENT_MINIMUM:
        raise ValueError(
            f"{context}: C3D10 outward normals disagree with classified CAD normal"
        )
    return {
        "minimum_classified_outward_alignment": minimum_alignment,
        "face_count": len(refs),
    }


def _check_planar_pair(
    first_normal_audit: dict[str, Any],
    second_normal_audit: dict[str, Any],
    first_normal: tuple[float, float, float],
    second_normal: tuple[float, float, float],
    context: str,
) -> float:
    dot = _dot(first_normal, second_normal)
    if dot > OPPOSED_NORMAL_DOT_MAXIMUM:
        raise ValueError(f"{context}: classified C3D10 seat normals are not opposed")
    if (
        first_normal_audit["minimum_classified_outward_alignment"]
        < FACE_NORMAL_ALIGNMENT_MINIMUM
    ):
        raise ValueError(f"{context}: first surface normal evidence is incomplete")
    if (
        second_normal_audit["minimum_classified_outward_alignment"]
        < FACE_NORMAL_ALIGNMENT_MINIMUM
    ):
        raise ValueError(f"{context}: second surface normal evidence is incomplete")
    return dot


def _side(
    mesh: MeshData,
    owner: str,
    refs: tuple[tuple[int, int], ...],
    *,
    pair_index: int,
    side_name: str,
) -> dict[str, Any]:
    if not refs:
        raise ValueError("contact surface cannot be empty")
    node_ids = sorted(
        {
            node
            for element, face in refs
            for node in _face_nodes(mesh.elements[element], face)
        }
    )
    return {
        "surface_name": f"WJCP_{pair_index:03d}_{side_name}",
        "node_set_name": f"WJCP_N_{pair_index:03d}_{side_name}",
        "remapped_face_node_ids": node_ids,
        "remapped_face_refs": list(refs),
        "owner_body_id": owner,
    }


def _pair(
    mesh: MeshData,
    *,
    pair_index: int,
    pair_id: str,
    category: str,
    slave_owner: str,
    slave_refs: tuple[tuple[int, int], ...],
    master_owner: str,
    master_refs: tuple[tuple[int, int], ...],
    audit: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    pair = {
        "pair_id": pair_id,
        "category": category,
        "slave": _side(
            mesh, slave_owner, slave_refs, pair_index=pair_index, side_name="S"
        ),
        "master": _side(
            mesh, master_owner, master_refs, pair_index=pair_index, side_name="M"
        ),
    }
    summary = {
        "pair_id": pair_id,
        "category": category,
        "slave_owner": slave_owner,
        "master_owner": master_owner,
        "slave_face_count": len(slave_refs),
        "master_face_count": len(master_refs),
        **audit,
    }
    return pair, summary


def _mesh_maps(
    classification: dict[str, Any], mesh: MeshData
) -> tuple[dict[str, str], dict[str, str]]:
    maps = classification.get("mesh_owner_maps")
    if not isinstance(maps, dict):
        raise TypeError("classification has no mesh owner maps")
    woods = maps.get("wood_body_ids")
    metal = maps.get("physical_metal_body_ids")
    if (
        not isinstance(woods, dict)
        or len(woods) != 3
        or not isinstance(metal, dict)
        or len(metal) != 16
    ):
        raise ValueError(
            "classification owner maps do not describe 3 wood + 16 physical metal bodies"
        )
    if set(woods.values()) & set(metal.values()) or set(woods.values()) | set(
        metal.values()
    ) != set(mesh.body_elements):
        raise ValueError("classification owner map and mesh body inventory differ")
    for member, body_id in woods.items():
        body = mesh.report["bodies"][body_id]
        if (
            body.get("owner_kind") != "wood_member"
            or body.get("source_body_id") != member
        ):
            raise ValueError(f"wood owner map disagrees with mesh report for {member}")
    for physical_id, body_id in metal.items():
        body = mesh.report["bodies"][body_id]
        if (
            body.get("owner_kind") != "physical_metal"
            or body.get("physical_body_id") != physical_id
        ):
            raise ValueError(
                f"physical metal owner map disagrees with mesh report for {physical_id}"
            )
    return {str(key): str(value) for key, value in woods.items()}, {
        str(key): str(value) for key, value in metal.items()
    }


def _physical_bolt_context(mesh: MeshData) -> dict[str, dict[str, Any]]:
    geometry = mesh.report.get("input_geometry_context")
    rows = geometry.get("physical_bolts") if isinstance(geometry, dict) else None
    if not isinstance(rows, list) or len(rows) != 4:
        raise ValueError("mesh report must carry exact four-bolt axis/receiver context")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        axis_id = row.get("physical_bolt_id")
        if not isinstance(axis_id, str) or axis_id in result:
            raise ValueError("physical bolt identities are absent or duplicated")
        origin = _vec3(row.get("axis_origin_global_xyz_mm"), f"{axis_id} axis origin")
        direction = _unit(
            _vec3(row.get("axis_direction_head_to_nut_global_xyz"), f"{axis_id} axis"),
            axis_id,
        )
        if (
            abs(
                _norm(_vec3(row["axis_direction_head_to_nut_global_xyz"], axis_id))
                - 1.0
            )
            > 1e-6
        ):
            raise ValueError(
                f"{axis_id}: source-bound head-to-nut direction is not unit length"
            )
        receivers = row.get("receivers_head_to_nut")
        raw_intervals = row.get("raw_receiver_projected_intervals")
        roles = row.get("physical_hardware_roles")
        if (
            not isinstance(receivers, list)
            or len(receivers) != 2
            or not isinstance(raw_intervals, list)
            or len(raw_intervals) != 2
            or not isinstance(roles, list)
        ):
            raise ValueError(
                f"{axis_id}: axis context lacks two receivers or hardware roles"
            )
        intervals: dict[str, tuple[float, float]] = {}
        for order, row_interval in enumerate(raw_intervals, 1):
            member = row_interval.get("member_id")
            projections = row_interval.get(
                "projected_intervals_from_underhead_datum_mm"
            )
            if (
                member != receivers[order - 1]
                or row_interval.get("receiver_order_head_to_nut") != order
                or row_interval.get("current_shaft_covers_raw_receiver") is not True
                or not isinstance(projections, list)
                or len(projections) != 1
            ):
                raise ValueError(
                    f"{axis_id}: receiver order/coverage is not source-bound"
                )
            low, high = (float(value) for value in projections[0])
            if not math.isfinite(low) or not math.isfinite(high) or high <= low:
                raise ValueError(f"{axis_id}/{member}: receiver interval is invalid")
            intervals[member] = (low, high)
        role_intervals = {}
        for role_row in roles:
            role = role_row.get("role")
            projections = role_row.get("axial_projection_from_underhead_datum_mm")
            if (
                not isinstance(role, str)
                or not isinstance(projections, list)
                or len(projections) != 1
            ):
                raise ValueError(f"{axis_id}: hardware axial interval is malformed")
            low, high = (float(value) for value in projections[0])
            if not math.isfinite(low) or not math.isfinite(high) or high <= low:
                raise ValueError(
                    f"{axis_id}/{role}: hardware axial interval is invalid"
                )
            role_intervals[role] = (low, high)
        if set(role_intervals) != {"shaft", "head", "head_washer", "nut_washer", "nut"}:
            raise ValueError(
                f"{axis_id}: hardware role identities differ from current bolt stack"
            )
        result[axis_id] = {
            "origin": origin,
            "direction": direction,
            "receivers": tuple(receivers),
            "receiver_intervals": intervals,
            "role_intervals": role_intervals,
        }
    return result


def _station(
    point: tuple[float, float, float],
    origin: tuple[float, float, float],
    axis: tuple[float, float, float],
) -> float:
    return _dot(_sub(point, origin), axis)


def _select_axial_facets(
    mesh: MeshData,
    owner: str,
    source_refs: tuple[tuple[int, int], ...],
    origin: tuple[float, float, float],
    axis: tuple[float, float, float],
    interval: tuple[float, float],
    context: str,
) -> tuple[tuple[tuple[int, int], ...], dict[str, Any]]:
    low, high = interval
    selected = []
    boundary = 0
    outside = 0
    for element, face in source_refs:
        stations = tuple(
            _station(mesh.nodes[node], origin, axis)
            for node in _face_nodes(mesh.elements[element], face)
        )
        if (
            min(stations) >= low - AXIAL_STATION_TOLERANCE_MM
            and max(stations) <= high + AXIAL_STATION_TOLERANCE_MM
        ):
            selected.append((element, face))
        elif (
            max(stations) < low - AXIAL_STATION_TOLERANCE_MM
            or min(stations) > high + AXIAL_STATION_TOLERANCE_MM
        ):
            outside += 1
        else:
            boundary += 1
    refs = tuple(sorted(selected))
    if not refs:
        raise ValueError(f"{context}: axial clipping produced an empty contact side")
    return refs, {
        "axial_interval_mm": [low, high],
        "station_selection": "all six C3D10 face nodes lie inside interval",
        "station_tolerance_mm": AXIAL_STATION_TOLERANCE_MM,
        "selected_face_count": len(refs),
        "boundary_excluded_face_count": boundary,
        "outside_interval_face_count": outside,
        "contact_or_strength_result": False,
    }


def _radial_audit(
    mesh: MeshData,
    owner: str,
    refs: tuple[tuple[int, int], ...],
    origin: tuple[float, float, float],
    axis: tuple[float, float, float],
    *,
    sign: int,
    context: str,
) -> float:
    if sign not in (-1, 1):
        raise ValueError("radial orientation sign must be +/-1")
    dots = []
    for element, face in refs:
        center = _face_center(mesh.nodes, mesh.elements[element], face)
        delta = _sub(center, origin)
        axial = _dot(delta, axis)
        radial = _sub(delta, tuple(axial * component for component in axis))
        radial_length = _norm(radial)
        if radial_length <= 1e-9:
            raise ValueError(f"{context}: facet center is on the axis")
        outward = _face_outward_normal(mesh.nodes, mesh.elements[element], face)
        alignment = _dot(outward, tuple(value / radial_length for value in radial))
        dots.append(sign * alignment)
    minimum = min(dots)
    if minimum < RADIAL_NORMAL_ALIGNMENT_MINIMUM:
        raise ValueError(
            f"{context}: owner C3D10 outward radial normals disagree with classified role"
        )
    return minimum


def _verify_radial_cylinder_surface(
    mesh: MeshData,
    owner: str,
    surface_row: dict[str, Any],
    *,
    origin: tuple[float, float, float],
    axis: tuple[float, float, float],
    expected_radius: float,
    sign: int,
    context: str,
) -> tuple[tuple[tuple[int, int], ...], dict[str, Any]]:
    if str(surface_row.get("cad_type", "")).casefold() != "cylinder":
        raise ValueError(
            f"{context}: classifier tag does not resolve to a cylindrical CAD surface"
        )
    analytic = surface_row.get("analytic_surface_parameters")
    if (
        not isinstance(analytic, dict)
        or analytic.get("status")
        != "least-squares analytic-cylinder fit from CAD parametric probes"
    ):
        raise ValueError(f"{context}: analytic cylinder fit is absent")
    radius = float(analytic.get("radius_mm"))
    point = _vec3(
        analytic.get("axis_point_global_xyz_mm"), f"{context} fitted axis point"
    )
    fitted_axis = _unit(
        _vec3(
            analytic.get("axis_direction_global_xyz_unoriented"),
            f"{context} fitted axis",
        ),
        context,
    )
    cross_axis = _norm(_cross(fitted_axis, axis))
    if cross_axis > 1e-5:
        raise ValueError(f"{context}: source cylindrical axis disagrees with bolt axis")
    radial_offset = _sub(point, origin)
    radial_offset = _sub(
        radial_offset, tuple(_dot(radial_offset, axis) * c for c in axis)
    )
    if _norm(radial_offset) > 0.05:
        raise ValueError(
            f"{context}: source cylindrical axis is not coaxial with bolt axis"
        )
    if abs(radius - expected_radius) > RADIUS_TOLERANCE_MM:
        raise ValueError(
            f"{context}: fitted cylinder radius differs from classified radius"
        )
    refs = _normalize_refs(surface_row.get("tri6_exterior_face_refs"), context)
    radial_minimum = _radial_audit(
        mesh, owner, refs, origin, axis, sign=sign, context=context
    )
    return refs, {
        "fitted_radius_mm": radius,
        "axis_alignment_dot": abs(_dot(fitted_axis, axis)),
        "axis_line_distance_mm": _norm(radial_offset),
        "minimum_outward_radial_alignment": radial_minimum,
        "face_count": len(refs),
    }


def _planar_pairs(
    classification: dict[str, Any],
    mesh: MeshData,
    wood_map: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pairs: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []
    interfaces = classification.get("wood_interfaces")
    if not isinstance(interfaces, list) or len(interfaces) != 3:
        raise ValueError(
            "classification must contain exactly three current finite wood interfaces"
        )
    expected_interface_ids = {
        "bottom_center_right_cleat_to_base_rail_bottom_right",
        "bottom_center_right_cleat_to_base_principal_center_right",
        "base_rail_bottom_right_to_base_principal_center_right",
    }
    if {row.get("interface_id") for row in interfaces} != expected_interface_ids:
        raise ValueError("wood interface identities differ from frozen current patch")
    for row in interfaces:
        pair_id = str(row["interface_id"])
        if (
            row.get("status") != "FINITE_MESH_PATCH_OVERLAY_VERIFIED_GEOMETRY_ONLY"
            or row.get("load_transfer_law_assigned") is not False
            or row.get("active_pressure_claim") is not False
        ):
            raise ValueError(
                f"{pair_id}: wood interface is not geometry-only/unilateral"
            )
        members = row.get("members")
        if not isinstance(members, list) or len(members) != 2:
            raise ValueError(f"{pair_id}: wood member order is missing")
        sides = []
        audits = []
        normals = []
        for side_index, face_row in enumerate(
            (row.get("first_face"), row.get("second_face"))
        ):
            if not isinstance(face_row, dict):
                raise TypeError(f"{pair_id}: finite face side is missing")
            member = str(face_row.get("body_id"))
            owner = wood_map.get(member)
            if member != members[side_index] or owner != face_row.get("mesh_body_id"):
                raise ValueError(
                    f"{pair_id}: finite face owner order differs from source classification"
                )
            _tag, mesh_surface, refs = _surface(
                mesh, owner, face_row.get("transient_cad_entity_tag"), pair_id
            )
            normal = _unit(
                _vec3(
                    face_row.get("outward_normal_global_xyz"), f"{pair_id} face normal"
                ),
                pair_id,
            )
            audit = _check_planar_surface(mesh, owner, mesh_surface, normal, pair_id)
            sides.append((owner, refs))
            audits.append(audit)
            normals.append(normal)
        dot = _check_planar_pair(audits[0], audits[1], normals[0], normals[1], pair_id)
        overlay = row.get("mesh_overlay")
        if (
            not isinstance(overlay, dict)
            or float(overlay.get("area_mm2", 0.0)) <= 0
            or float(overlay.get("maximum_plane_residual_mm", math.inf))
            > PLANE_RESIDUAL_TOLERANCE_MM
        ):
            raise ValueError(
                f"{pair_id}: finite wood overlay lacks positive area/opposed coplanarity"
            )
        pair, pair_summary = _pair(
            mesh,
            pair_index=len(pairs) + 1,
            pair_id=f"{pair_id}::wood_to_wood",
            category="wood_wood_finite_interface",
            slave_owner=sides[0][0],
            slave_refs=sides[0][1],
            master_owner=sides[1][0],
            master_refs=sides[1][1],
            audit={
                "classified_normal_dot": dot,
                "finite_common_area_mm2": float(row["source_common_area_mm2"]),
                "mesh_overlay_area_mm2": float(overlay["area_mm2"]),
                "maximum_mesh_plane_residual_mm": float(
                    overlay["maximum_plane_residual_mm"]
                ),
                "contact_surface_domain": "complete CAD face refs; master may exceed finite common footprint",
            },
        )
        pairs.append(pair)
        summary.append(pair_summary)

    seats = classification.get("hardware_seats")
    if not isinstance(seats, list) or len(seats) != 16:
        raise ValueError(
            "classification must contain exactly sixteen current planar hardware seats"
        )
    expected_seat_kinds = Counter(
        {
            "head_washer_to_head": 4,
            "head_washer_to_first_receiver": 4,
            "nut_washer_to_nut": 4,
            "nut_washer_to_last_receiver": 4,
        }
    )
    if Counter(str(row.get("seat_kind")) for row in seats) != expected_seat_kinds:
        raise ValueError(
            "hardware seat kind counts differ from the four current bolt stacks"
        )
    seat_ids = set()
    for row in seats:
        pair_id = str(row.get("seat_id"))
        if (
            pair_id in seat_ids
            or row.get("status") != "FINITE_OPPOSED_PLANAR_SEAT_GEOMETRY_VERIFIED"
            or row.get("load_transfer_law_assigned") is not False
            or row.get("preload_or_active_pressure_claim") is not False
        ):
            raise ValueError(
                f"{pair_id}: seat identity/status is invalid or duplicated"
            )
        seat_ids.add(pair_id)
        owners = row.get("owner_pair")
        refs_rows = row.get("surface_refs")
        if (
            not isinstance(owners, list)
            or len(owners) != 2
            or not isinstance(refs_rows, list)
            or len(refs_rows) != 2
        ):
            raise ValueError(
                f"{pair_id}: two classified seat owner surfaces are required"
            )
        sides = []
        audits = []
        normals = []
        for index, side_row in enumerate(refs_rows):
            if (
                not isinstance(side_row, dict)
                or side_row.get("mesh_body_id") != owners[index]
            ):
                raise ValueError(f"{pair_id}: seat owner map/order is inconsistent")
            owner = str(owners[index])
            _tag, mesh_surface, refs = _surface(
                mesh, owner, side_row.get("transient_cad_entity_tag"), pair_id
            )
            if len(refs) != side_row.get("face_count"):
                raise ValueError(
                    f"{pair_id}: classifier face count differs from current tag refs"
                )
            normal = _unit(
                _vec3(side_row.get("outward_normal_global_xyz"), f"{pair_id} normal"),
                pair_id,
            )
            audit = _check_planar_surface(mesh, owner, mesh_surface, normal, pair_id)
            sides.append((owner, refs))
            audits.append(audit)
            normals.append(normal)
        dot = _check_planar_pair(audits[0], audits[1], normals[0], normals[1], pair_id)
        overlay = row.get("mesh_overlay")
        if (
            not isinstance(overlay, dict)
            or float(overlay.get("area_mm2", 0.0)) <= 0
            or float(overlay.get("maximum_plane_residual_mm", math.inf))
            > PLANE_RESIDUAL_TOLERANCE_MM
            or abs(float(overlay.get("maximum_normal_alignment_residual", math.inf)))
            > 2e-6
        ):
            raise ValueError(
                f"{pair_id}: seat overlay area/normal/plane residual is invalid"
            )
        pair, pair_summary = _pair(
            mesh,
            pair_index=len(pairs) + 1,
            pair_id=pair_id,
            category=str(row["seat_kind"]),
            slave_owner=sides[0][0],
            slave_refs=sides[0][1],
            master_owner=sides[1][0],
            master_refs=sides[1][1],
            audit={
                "classified_normal_dot": dot,
                "finite_seat_overlay_area_mm2": float(overlay["area_mm2"]),
                "maximum_mesh_plane_residual_mm": float(
                    overlay["maximum_plane_residual_mm"]
                ),
            },
        )
        pairs.append(pair)
        summary.append(pair_summary)
    return pairs, summary


def _radial_pairs(
    classification: dict[str, Any],
    mesh: MeshData,
    wood_map: dict[str, str],
    metal_map: dict[str, str],
    bolt_context: dict[str, dict[str, Any]],
    *,
    pairs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    summary: list[dict[str, Any]] = []
    bore_rows = classification.get("bolt_receiver_bore_pairs")
    if not isinstance(bore_rows, list) or len(bore_rows) != 4:
        raise ValueError(
            "classification must contain exactly four current bolt receiver pairs"
        )
    seen_wood_bores = set()
    for bolt_row in bore_rows:
        axis_id = str(bolt_row.get("physical_bolt_id"))
        axis = bolt_context.get(axis_id)
        if (
            axis is None
            or bolt_row.get("status") != "BORE_PAIR_IDENTITY_AND_OPEN_GAP_BOUND"
            or bolt_row.get("radial_gap_is_explicitly_open") is not True
        ):
            raise ValueError(
                f"{axis_id}: bolt receiver radial gaps are not explicit/open"
            )
        if list(axis["receivers"]) != bolt_row.get("head_to_nut_receiver_order") or set(
            axis["receivers"]
        ) != set(bolt_row.get("bore_receiver_membership", ())):
            raise ValueError(
                f"{axis_id}: bore identity/ordered receivers differ from mesh source context"
            )
        metal_bolt_id = f"physical_metal/{axis_id}/bolt"
        shaft_owner = metal_map.get(metal_bolt_id)
        shaft_row = bolt_row.get("shaft_surface")
        if (
            not isinstance(shaft_row, dict)
            or shaft_row.get("physical_body_id") != metal_bolt_id
            or shaft_row.get("mesh_body_id") != shaft_owner
        ):
            raise ValueError(
                f"{axis_id}: classified shaft surface does not bind to exact owner body"
            )
        shaft_tag, shaft_surface, shaft_all_refs = _surface(
            mesh, shaft_owner, shaft_row.get("transient_cad_entity_tag"), axis_id
        )
        shaft_refs, _shaft_geom = _verify_radial_cylinder_surface(
            mesh,
            shaft_owner,
            shaft_surface,
            origin=axis["origin"],
            axis=axis["direction"],
            expected_radius=float(shaft_row["fitted_radius_mm"]),
            sign=1,
            context=f"{axis_id} bolt shaft",
        )
        if shaft_refs != shaft_all_refs:
            raise ValueError(
                f"{axis_id}: shaft CAD tag facet refs changed while resolving"
            )
        if len(bolt_row.get("receiver_bore_walls", ())) != 2:
            raise ValueError(f"{axis_id}: exactly two bore wall records are required")
        for receiver_row in bolt_row["receiver_bore_walls"]:
            receiver_id = str(receiver_row.get("receiver_id"))
            key = (axis_id, receiver_id)
            if key in seen_wood_bores or receiver_id not in axis["receiver_intervals"]:
                raise ValueError(
                    f"{axis_id}/{receiver_id}: duplicate/unknown bore receiver"
                )
            seen_wood_bores.add(key)
            owner = wood_map.get(receiver_id)
            if (
                receiver_row.get("mesh_body_id") != owner
                or receiver_row.get("status")
                != "CYLINDRICAL_BORE_WALL_BOUND_TO_DECLARED_AXIS"
                or receiver_row.get("radial_status") != "OPEN_RADIAL_CLEARANCE"
            ):
                raise ValueError(
                    f"{axis_id}/{receiver_id}: classified receiver wall/gap is invalid"
                )
            interval = tuple(
                float(value) for value in receiver_row["declared_receiver_interval_mm"]
            )
            if len(interval) != 2 or any(
                abs(interval[i] - axis["receiver_intervals"][receiver_id][i]) > 1e-6
                for i in (0, 1)
            ):
                raise ValueError(
                    f"{axis_id}/{receiver_id}: receiver interval differs from frozen axis source"
                )
            tag, wall_surface, wall_refs = _surface(
                mesh, owner, receiver_row.get("transient_cad_entity_tag"), key.__str__()
            )
            if len(wall_refs) != receiver_row.get("tri6_face_count"):
                raise ValueError(
                    f"{axis_id}/{receiver_id}: source bore wall face count changed"
                )
            bore_geom_refs, _bore_geom = _verify_radial_cylinder_surface(
                mesh,
                owner,
                wall_surface,
                origin=axis["origin"],
                axis=axis["direction"],
                expected_radius=float(receiver_row["fitted_bore_radius_mm"]),
                sign=-1,
                context=f"{axis_id}/{receiver_id} wood bore",
            )
            if bore_geom_refs != wall_refs:
                raise ValueError(
                    f"{axis_id}/{receiver_id}: wood bore facet refs changed"
                )
            clearance = float(receiver_row["radial_clearance_mm"])
            if (
                clearance <= 0
                or abs(
                    (
                        float(receiver_row["fitted_bore_radius_mm"])
                        - float(receiver_row["shaft_radius_mm"])
                    )
                    - clearance
                )
                > RADIAL_GAP_TOLERANCE_MM
            ):
                raise ValueError(
                    f"{axis_id}/{receiver_id}: classified positive clearance does not match fitted radii"
                )
            clipped_shaft_refs, clip_audit = _select_axial_facets(
                mesh,
                shaft_owner,
                shaft_refs,
                axis["origin"],
                axis["direction"],
                interval,
                key.__str__(),
            )
            clipped_shaft_radial = _radial_audit(
                mesh,
                shaft_owner,
                clipped_shaft_refs,
                axis["origin"],
                axis["direction"],
                sign=1,
                context=f"{axis_id}/{receiver_id} clipped shaft",
            )
            bore_radial = _radial_audit(
                mesh,
                owner,
                bore_geom_refs,
                axis["origin"],
                axis["direction"],
                sign=-1,
                context=f"{axis_id}/{receiver_id} bore wall",
            )
            pair_id = f"{axis_id}::{receiver_id}::shaft_to_wood_bore"
            pair, pair_summary = _pair(
                mesh,
                pair_index=len(pairs) + 1,
                pair_id=pair_id,
                category="open_bolt_shank_to_wood_bore",
                slave_owner=shaft_owner,
                slave_refs=clipped_shaft_refs,
                master_owner=owner,
                master_refs=bore_geom_refs,
                audit={
                    "physical_bolt_id": axis_id,
                    "receiver_id": receiver_id,
                    "transient_cad_tags": [shaft_tag, tag],
                    "radial_clearance_mm": clearance,
                    "initial_contact_state": "open radial clearance; no forced fit or closure",
                    "minimum_shaft_outward_radial_alignment": clipped_shaft_radial,
                    "minimum_bore_inward_radial_alignment": bore_radial,
                    **clip_audit,
                },
            )
            pairs.append(pair)
            summary.append(pair_summary)
    if len(seen_wood_bores) != EXPECTED_COUNTS["wood_bore_to_shaft_pairs"]:
        raise ValueError(
            "wood receiver bore pairs do not cover exactly eight shaft-wall pairs"
        )

    hardware_rows = classification.get("bolt_hardware_radial_clearances")
    if not isinstance(hardware_rows, list) or len(hardware_rows) != 12:
        raise ValueError(
            "classification must contain eight washer walls and four explicit missing nut bores"
        )
    washer_count = 0
    nut_omissions = []
    for radial_row in hardware_rows:
        axis_id = str(radial_row.get("physical_bolt_id"))
        axis = bolt_context.get(axis_id)
        role = radial_row.get("component_role")
        physical_id = radial_row.get("physical_body_id")
        owner = metal_map.get(str(physical_id))
        if axis is None or owner is None:
            raise ValueError(f"{axis_id}/{role}: hardware radial owner is missing")
        shaft_row = radial_row.get("shaft_surface")
        bolt_owner = metal_map.get(f"physical_metal/{axis_id}/bolt")
        if role == "nut":
            if (
                radial_row.get("status") != "MISSING_INTERNAL_BORE_WALL"
                or radial_row.get("candidate_internal_bore_count") != 0
                or radial_row.get("source_nut_geometry", {}).get(
                    "nut_internal_bore_wall_count"
                )
                != 0
            ):
                raise ValueError(
                    f"{axis_id}: nut omission is not explicitly recorded as an absent bore"
                )
            nut_omissions.append(axis_id)
            continue
        if (
            role not in ("head_washer", "nut_washer")
            or radial_row.get("status") != "INTERNAL_BORE_BOUND_TO_DECLARED_BOLT_AXIS"
            or radial_row.get("radial_status") != "OPEN_RADIAL_CLEARANCE"
            or radial_row.get("bolt_shank_contact_active") is not False
        ):
            raise ValueError(
                f"{axis_id}/{role}: only the eight open washer-bore interfaces may be emitted"
            )
        if (
            not isinstance(shaft_row, dict)
            or shaft_row.get("physical_body_id") != f"physical_metal/{axis_id}/bolt"
            or shaft_row.get("transient_cad_entity_tag") is None
        ):
            raise ValueError(f"{axis_id}/{role}: washer shaft parent/tag is missing")
        interval = tuple(
            float(value) for value in radial_row["declared_axial_interval_mm"]
        )
        source_interval = axis["role_intervals"].get(role)
        if (
            source_interval is None
            or len(interval) != 2
            or any(abs(interval[i] - source_interval[i]) > 1e-6 for i in (0, 1))
        ):
            raise ValueError(
                f"{axis_id}/{role}: washer interval differs from frozen source role stations"
            )
        shaft_tag, shaft_surface, shaft_refs_all = _surface(
            mesh, bolt_owner, shaft_row["transient_cad_entity_tag"], axis_id
        )
        shaft_refs, _shaft_geom = _verify_radial_cylinder_surface(
            mesh,
            bolt_owner,
            shaft_surface,
            origin=axis["origin"],
            axis=axis["direction"],
            expected_radius=float(shaft_row["radius_mm"]),
            sign=1,
            context=f"{axis_id}/{role} shaft",
        )
        if shaft_refs != shaft_refs_all:
            raise ValueError(f"{axis_id}/{role}: bolt shaft surface ref set changed")
        tag, bore_surface, bore_refs = _surface(
            mesh, owner, radial_row.get("transient_cad_entity_tag"), f"{axis_id}/{role}"
        )
        if len(bore_refs) != radial_row.get("tri6_face_count"):
            raise ValueError(f"{axis_id}/{role}: washer bore face count changed")
        radius = float(radial_row["fitted_internal_radius_mm"])
        bore_refs_again, _bore_geom = _verify_radial_cylinder_surface(
            mesh,
            owner,
            bore_surface,
            origin=axis["origin"],
            axis=axis["direction"],
            expected_radius=radius,
            sign=-1,
            context=f"{axis_id}/{role} washer bore",
        )
        if bore_refs_again != bore_refs:
            raise ValueError(f"{axis_id}/{role}: washer bore facet ref set changed")
        clearance = float(radial_row["radial_clearance_mm"])
        shaft_radius = float(radial_row["shaft_radius_mm"])
        if (
            clearance <= 0
            or abs((radius - shaft_radius) - clearance) > RADIAL_GAP_TOLERANCE_MM
        ):
            raise ValueError(
                f"{axis_id}/{role}: classified washer-to-shaft open gap does not match fitted radii"
            )
        clipped_shaft_refs, clip_audit = _select_axial_facets(
            mesh,
            bolt_owner,
            shaft_refs,
            axis["origin"],
            axis["direction"],
            interval,
            f"{axis_id}/{role}",
        )
        shaft_radial = _radial_audit(
            mesh,
            bolt_owner,
            clipped_shaft_refs,
            axis["origin"],
            axis["direction"],
            sign=1,
            context=f"{axis_id}/{role} shaft clip",
        )
        bore_radial = _radial_audit(
            mesh,
            owner,
            bore_refs,
            axis["origin"],
            axis["direction"],
            sign=-1,
            context=f"{axis_id}/{role} inner wall",
        )
        pair_id = f"{axis_id}::shaft_to_{role}_bore"
        pair, pair_summary = _pair(
            mesh,
            pair_index=len(pairs) + 1,
            pair_id=pair_id,
            category="open_bolt_shank_to_washer_bore",
            slave_owner=bolt_owner,
            slave_refs=clipped_shaft_refs,
            master_owner=owner,
            master_refs=bore_refs,
            audit={
                "physical_bolt_id": axis_id,
                "hardware_role": str(role),
                "transient_cad_tags": [shaft_tag, tag],
                "radial_clearance_mm": clearance,
                "initial_contact_state": "open radial clearance; no forced fit or closure",
                "minimum_shaft_outward_radial_alignment": shaft_radial,
                "minimum_bore_inward_radial_alignment": bore_radial,
                **clip_audit,
            },
        )
        pairs.append(pair)
        summary.append(pair_summary)
        washer_count += 1
    if (
        washer_count != EXPECTED_COUNTS["washer_bore_to_shaft_pairs"]
        or len(set(nut_omissions)) != 4
    ):
        raise ValueError(
            "hardware bore rows do not produce exactly eight washer pairs/four nut omissions"
        )
    nut_summary = [
        {
            "physical_bolt_id": axis_id,
            "status": "INTENTIONAL_NO_NUT_BORE_CONTACT_PAIR",
            "source_nut_geometry": "solid cylindrical display envelope; no modeled internal bore wall",
            "physical_occupancy_or_interference_claim": False,
        }
        for axis_id in sorted(nut_omissions)
    ]
    return summary, nut_summary


def build_current_contact_deck_fragment(
    classification_path: str | Path,
    mesh_report_path: str | Path,
    mesh_deck_path: str | Path,
    *,
    penalty_n_per_mm3: float,
) -> tuple[str, dict[str, Any]]:
    """Return a pinned unsolved current-patch surface/contact fragment and audit."""
    penalty = _positive_penalty(penalty_n_per_mm3)
    classification, classification_sha = _load_classification(Path(classification_path))
    mesh = _load_mesh(Path(mesh_report_path), Path(mesh_deck_path))
    wood_map, metal_map = _mesh_maps(classification, mesh)
    bolt_context = _physical_bolt_context(mesh)

    pairs, pair_summaries = _planar_pairs(classification, mesh, wood_map)
    radial_summaries, nut_omissions = _radial_pairs(
        classification,
        mesh,
        wood_map,
        metal_map,
        bolt_context,
        pairs=pairs,
    )
    if len(pairs) != EXPECTED_COUNTS["contact_pairs"]:
        raise ValueError(
            f"expected 35 current geometry contact pairs; built {len(pairs)}"
        )
    ids = [pair["pair_id"] for pair in pairs]
    if len(set(ids)) != len(ids):
        raise ValueError("contact pair IDs are not unique")

    lines = _render_contact_cards(pairs, penalty)
    lines = [line.replace("WJ04_NUMERICAL_CONTACT", INTERACTION_NAME) for line in lines]
    lines = [
        "** Current patch contact cards only: no material, restraint, load, engagement, or solver-step cards",
        "** CCX 2.21 surface-to-surface is face-to-face penalty contact; contact activates on positive penetration",
        "** Linear face-to-face behavior takes K only; large-clearance sigma-infinity default is node-to-face only",
        "** Friction is optional; *FRICTION omitted for frictionless contact",
        "** Four displayed nut solids have no bore wall; no nut-bore contact surface or pair is emitted",
        *lines[1:],
    ]
    fragment = "\n".join(lines) + "\n"

    category_counts = Counter(pair["category"] for pair in pairs)
    source_hashes = {
        "classification_sha256": classification_sha,
        "mesh_report_sha256": mesh.report_sha256,
        "mesh_deck_sha256": mesh.deck_sha256,
        "ccx_2_21_manual_pdf_sha256": _sha256(CCX_MANUAL_PDF.read_bytes()),
        "adapter_source_sha256": _sha256(Path(__file__).read_bytes()),
    }
    if source_hashes["ccx_2_21_manual_pdf_sha256"] != CCX_MANUAL_SHA256:
        raise ValueError("local pinned CalculiX 2.21 manual changed")
    return fragment, {
        "schema": SCHEMA,
        "status": "UNSOLVED_CURRENT_PATCH_CONTACT_CARDS_ONLY",
        "accepted": False,
        "response_ready": False,
        "native_solve_run": False,
        "candidate": {
            "revision_id": REVISION_ID,
            "implementation_revision": IMPLEMENTATION_REVISION,
        },
        "source_hashes": source_hashes,
        "scope": {
            **EXPECTED_COUNTS,
            "wood_members": 3,
            "physical_metal_bodies": 16,
            "contact_surfaces": 2 * len(pairs),
            "emitted_material_cards": 0,
            "emitted_restraint_or_load_cards": 0,
            "emitted_engagement_or_tie_cards": 0,
            "emitted_solver_step_cards": 0,
        },
        "contact_law": {
            "calculix_version": "2.21",
            "pair_type": "SURFACE TO SURFACE",
            "pressure_overclosure": "LINEAR",
            "penalty_n_per_mm3": penalty,
            "penalty_role": "explicit numerical contact enforcement only, not physical interface stiffness",
            "normal_behavior": "unilateral compression-only; opening allowed",
            "tension_transfer": False,
            "friction_behavior": "frictionless; optional *FRICTION card omitted",
            "large_clearance_sigma_infinity": "not entered; CCX 2.21 section 7.129 limits it to node-to-face linear contact; face-to-face requires K only",
            "manual_theory": "CCX 2.21 section 6: face-to-face contact element active only for positive penetration",
        },
        "interface_surface_policy": {
            "wood_face_refs": "complete classified source CAD face refs; master can exceed finite common footprint",
            "hardware_seat_refs": "complete classified source CAD face refs; seat overlay area is diagnostic finite overlap",
            "open_bore_shaft_refs": "source bolt cylinder face refs clipped by exact current receiver/washer axial intervals",
            "open_gap_closure": "no adjust, tie, forced fit, preload, or gap closure emitted",
        },
        "intentional_nut_bore_omissions": nut_omissions,
        "pair_category_counts": dict(sorted(category_counts.items())),
        "pairs": pair_summaries + radial_summaries,
        "contact_fragment_sha256": _sha256(fragment.encode("utf-8")),
        "limits": [
            "Geometry-only current diagnostic; no response, strength, or joint acceptance.",
            "Displayed nut envelopes are retained only for washer-to-nut seat-controller surfaces; they are not physical nut occupancy or elastic nut compliance.",
            "No nut-bore radial contact, thread flank contact, bolt axial engagement, material law, or complete joint dynamics is represented.",
            "Rigid-seat controller semantics, metal representation, engagement, and analysis step require parent disposition.",
            "The penalty number is caller-supplied numerical enforcement, not timber, steel, or measured contact stiffness.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classification", type=Path, default=CLASSIFICATION_PATH)
    parser.add_argument("--mesh-report", type=Path, default=MESH_REPORT_PATH)
    parser.add_argument("--mesh-deck", type=Path, default=MESH_DECK_PATH)
    parser.add_argument("--penalty-n-per-mm3", type=float, required=True)
    parser.add_argument("--fragment", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    fragment, manifest = build_current_contact_deck_fragment(
        args.classification,
        args.mesh_report,
        args.mesh_deck,
        penalty_n_per_mm3=args.penalty_n_per_mm3,
    )
    args.fragment.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.fragment.write_text(fragment, encoding="utf-8")
    args.manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "scope": manifest["scope"],
                "fragment_sha256": manifest["contact_fragment_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
