"""Prepare an explicitly owned contact fragment for the WJ04 ordinary patch.

The output contains disjoint C3D10 bodies, stable body node/element sets, and
finite frictionless compression-only contact surfaces. It deliberately omits
material, restraint, load, engagement/tie, and analysis-step cards; it is not a
runnable or accepted structural model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fea import wood_joint_hardware_patch_mesh as metal_mesh_contract
from fea import wood_joint_patch_classification as surface_contract
from fea import wood_joint_patch_mesh as wood_mesh_contract
from fea.floor_contact import FACES
from fea.stitch_joint_mesh import external_faces

SCHEMA = "wood_joint_wj04_patch_contact_contract/v1"
WOOD_NORMAL_AUDIT_STATUS = "parent_signed_mesh_normal_audit_passed"
SEAT_AUDIT_STATUS = "parent_seat_and_envelope_audit_passed"
MECHANICS_INPUTS_SCHEMA = "wood_joint_wj04_full_stock_mechanics_contract/v1"
HARDWARE_SCHEMA = "wood_joint_wj04_mechanics_hardware/v1"
WOOD_BODY_IDS = tuple(wood_mesh_contract.WOOD_BODY_IDS)
STACK_IDS = tuple(metal_mesh_contract.STACK_IDS)
EXPECTED_INTERFACE_IDS = tuple(sorted(wood_mesh_contract.EXPECTED_INTERFACE_STACKS))
EXPECTED_METAL_BODY_IDS = tuple(
    sorted(
        f"{stack_id}__{role}"
        for stack_id in STACK_IDS
        for role in metal_mesh_contract.COMPONENT_ROLES
    )
)
PENALTY_DESCRIPTION = (
    "Caller-supplied linear pressure-overclosure penalty used only for numerical "
    "contact enforcement; it is not timber, steel, or physical interface stiffness. "
    "Penalty sensitivity and convergence remain pending."
)
LIMITS = (
    "Unsolved WJ04 five-wood/32-metal contact fragment only. Contact is unilateral, "
    "frictionless, and compression-only; it permits opening and credits no preload, "
    "friction, tension, capacity, or resistance. The fragment omits materials, "
    "restraints, loads, bolt-to-nut axial engagement, stabilization, and a solver step."
)
PLANE_TOLERANCE_MM = 1e-5
FACE_NORMAL_TOLERANCE = 0.95
RADIAL_NORMAL_TOLERANCE = 0.35
AUDITED_SEAT_GAP_TOLERANCE_MM = 1e-4
AXIAL_FACE_NODE_TOLERANCE_MM = 1e-7


@dataclass(frozen=True)
class MeshInput:
    source_kind: str
    report_path: Path
    deck_path: Path
    report: dict[str, Any]
    report_sha256: str
    deck_sha256: str
    nodes: dict[int, tuple[float, float, float]]
    elements: dict[int, tuple[int, ...]]
    body_nodes: dict[str, tuple[int, ...]]
    body_elements: dict[str, tuple[int, ...]]
    body_surfaces: dict[str, dict[str, dict[str, Any]]]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def _load_json(path: str | Path, context: str) -> tuple[dict[str, Any], bytes]:
    source = Path(path)
    try:
        raw = source.read_bytes()
        record = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{context} JSON is missing or invalid: {source}") from error
    if not isinstance(record, dict):
        raise TypeError(f"{context} JSON root must be an object")
    return record, raw


def _positive_finite(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{context} must be a numeric value, positive and finite")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{context} must be positive and finite")
    return number


def _finite_vector(value: Any, length: int, context: str) -> tuple[float, ...]:
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context} must have {length} finite components") from error
    if len(result) != length or any(not math.isfinite(component) for component in result):
        raise ValueError(f"{context} must have {length} finite components")
    return result


def _dot(first: Iterable[float], second: Iterable[float]) -> float:
    return math.fsum(a * b for a, b in zip(first, second, strict=True))


def _norm(vector: Iterable[float]) -> float:
    values = tuple(vector)
    return math.sqrt(_dot(values, values))


def _unit(vector: Iterable[float], context: str) -> tuple[float, float, float]:
    values = _finite_vector(vector, 3, context)
    length = _norm(values)
    if length <= 0 or not math.isfinite(length):
        raise ValueError(f"{context} must be nonzero")
    return tuple(component / length for component in values)  # type: ignore[return-value]


def _sub(first: Iterable[float], second: Iterable[float]) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(first, second, strict=True))  # type: ignore[return-value]


def _cross(first: Iterable[float], second: Iterable[float]) -> tuple[float, float, float]:
    a = tuple(first)
    b = tuple(second)
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def parse_c3d10_deck(text: str, *, context: str) -> tuple[
    dict[int, tuple[float, float, float]],
    dict[int, tuple[int, ...]],
    dict[str, set[int]],
]:
    """Parse node and C3D10 blocks while retaining their declared ELSET owner."""
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: dict[int, tuple[int, ...]] = {}
    elsets: dict[str, set[int]] = {}
    mode: str | None = None
    current_elset: str | None = None
    for line_number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            upper = line.upper()
            mode = None
            current_elset = None
            if upper == "*HEADING":
                mode = "heading"
            elif upper == "*NODE" or upper.startswith("*NODE,"):
                mode = "nodes"
            elif upper.startswith("*ELEMENT,"):
                options = {
                    key.strip().upper(): value.strip()
                    for cell in line.split(",")[1:]
                    if "=" in cell
                    for key, value in (cell.split("=", 1),)
                }
                if options.get("TYPE", "").upper() != "C3D10":
                    raise ValueError(f"{context} line {line_number}: only C3D10 is supported")
                current_elset = options.get("ELSET", "").upper()
                if not current_elset or current_elset in elsets:
                    raise ValueError(f"{context} line {line_number}: missing/duplicate ELSET")
                elsets[current_elset] = set()
                mode = "elements"
            continue
        cells = [cell.strip() for cell in line.split(",")]
        try:
            if mode == "heading":
                continue
            if mode == "nodes":
                if len(cells) != 4:
                    raise ValueError("expected node ID and XYZ")
                node = int(cells[0])
                xyz = _finite_vector(cells[1:], 3, f"node {node}")
                if node <= 0 or node in nodes:
                    raise ValueError("node ID must be positive and unique")
                nodes[node] = xyz  # type: ignore[assignment]
            elif mode == "elements":
                if current_elset is None or len(cells) != 11:
                    raise ValueError("expected element ID and ten C3D10 node IDs")
                element = int(cells[0])
                connectivity = tuple(int(cell) for cell in cells[1:])
                if element <= 0 or element in elements:
                    raise ValueError("element ID must be positive and unique")
                if any(node <= 0 for node in connectivity) or len(set(connectivity)) != 10:
                    raise ValueError("C3D10 connectivity must contain ten positive unique node IDs")
                elements[element] = connectivity
                elsets[current_elset].add(element)
            else:
                raise ValueError("numeric data appears outside a node or C3D10 block")
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(f"{context} line {line_number}: {error}") from error
    if not nodes or not elements or not elsets:
        raise ValueError(f"{context} deck has no complete node/C3D10 inventory")
    used_nodes = {node for connectivity in elements.values() for node in connectivity}
    if used_nodes != nodes.keys():
        raise ValueError(f"{context} deck contains unowned or unreferenced nodes")
    return nodes, elements, elsets


def _expected_elset(source_kind: str, body_id: str) -> str:
    prefix = "METAL_" if source_kind == "metal" else ""
    return f"{prefix}{body_id}".upper()


def _read_mesh_input(
    source_kind: str,
    report_path: str | Path,
    deck_path: str | Path,
) -> MeshInput:
    report_file = Path(report_path)
    deck_file = Path(deck_path)
    report, report_bytes = _load_json(report_file, f"{source_kind} mesh report")
    try:
        deck_bytes = deck_file.read_bytes()
    except OSError as error:
        raise ValueError(f"{source_kind} mesh deck is unavailable: {deck_file}") from error
    deck_sha = sha256_bytes(deck_bytes)
    if source_kind == "wood":
        expected_schema = wood_mesh_contract.SCHEMA
        expected_status = "VERIFIED_C3D10_MESH_ONLY_NO_SOLVER"
        expected_bodies = set(WOOD_BODY_IDS)
        if report.get("output_contains_material_contact_or_solver_cards") is not False:
            raise ValueError("wood mesh source exceeds its frozen geometry-only scope")
    else:
        expected_schema = metal_mesh_contract.SCHEMA
        expected_status = "VERIFIED_C3D10_PHYSICAL_METAL_MESH_ONLY_NO_SOLVER"
        expected_bodies = set(EXPECTED_METAL_BODY_IDS)
        if report.get("output_contains_material_contact_tie_preload_or_solver_cards") is not False:
            raise ValueError("metal mesh source exceeds its frozen geometry-only scope")
        if report.get("legacy_collision_roles_meshed") != 0:
            raise ValueError("legacy collision envelopes must remain unmeshed metadata")
    if report.get("schema") != expected_schema or report.get("status") != expected_status:
        raise ValueError(f"{source_kind} mesh report schema/status is not the verified WJ04 input")
    if report.get("solved") is not False or report.get("accepted") is not False:
        raise ValueError(f"{source_kind} mesh report must remain unsolved and unaccepted")
    if report.get("mesh_input_sha256") != deck_sha:
        raise ValueError(f"{source_kind} source deck digest differs from its mesh report")
    body_records = report.get("bodies")
    if not isinstance(body_records, dict) or set(body_records) != expected_bodies:
        raise ValueError(f"{source_kind} mesh must contain the exact body inventory")
    if report.get("body_count") != len(expected_bodies):
        raise ValueError(f"{source_kind} mesh body count differs from the contract")

    nodes, elements, elsets = parse_c3d10_deck(deck_bytes.decode("utf-8"), context=source_kind)
    expected_elsets = {_expected_elset(source_kind, body_id) for body_id in expected_bodies}
    if set(elsets) != expected_elsets:
        raise ValueError(f"{source_kind} deck element sets differ from the exact body inventory")

    body_nodes: dict[str, tuple[int, ...]] = {}
    body_elements: dict[str, tuple[int, ...]] = {}
    body_surfaces: dict[str, dict[str, dict[str, Any]]] = {}
    seen_nodes: set[int] = set()
    seen_elements: set[int] = set()
    for body_id in sorted(expected_bodies):
        record = body_records[body_id]
        elset = _expected_elset(source_kind, body_id)
        element_ids = tuple(sorted(elsets[elset]))
        record_elements = tuple(sorted(int(element) for element in record.get("elements", ())))
        if not element_ids or element_ids != record_elements:
            raise ValueError(f"{source_kind}/{body_id}: element report and ELSET differ")
        referenced_nodes = tuple(
            sorted({node for element in element_ids for node in elements[element]})
        )
        record_nodes = tuple(sorted(int(node) for node in record.get("nodes", ())))
        if not referenced_nodes or referenced_nodes != record_nodes:
            raise ValueError(f"{source_kind}/{body_id}: node report and connectivity differ")
        if seen_nodes.intersection(referenced_nodes) or seen_elements.intersection(element_ids):
            raise ValueError(f"{source_kind}/{body_id}: independent body ownership overlaps")
        seen_nodes.update(referenced_nodes)
        seen_elements.update(element_ids)
        if record.get("node_count") != len(referenced_nodes) or record.get("element_count") != len(element_ids):
            raise ValueError(f"{source_kind}/{body_id}: report counts disagree with deck ownership")
        surfaces = record.get("surfaces")
        if not isinstance(surfaces, dict) or not surfaces:
            raise ValueError(f"{source_kind}/{body_id}: surface ownership inventory is missing")
        exterior = external_faces({element: elements[element] for element in element_ids})
        expected_face_refs = {(row[0], row[1]) for row in exterior.values()}
        seen_surface_refs: set[tuple[int, int]] = set()
        parsed_surfaces: dict[str, dict[str, Any]] = {}
        for tag, surface in surfaces.items():
            if not isinstance(surface, dict):
                raise TypeError(f"{source_kind}/{body_id}: surface row must be an object")
            refs = surface.get("tri6_exterior_face_refs")
            if not isinstance(refs, list) or not refs:
                raise ValueError(f"{source_kind}/{body_id}/{tag}: surface has no finite exterior faces")
            normalized = _normalize_face_refs(refs, f"{source_kind}/{body_id}/{tag}")
            if any(element not in element_ids for element, _face in normalized):
                raise ValueError(f"{source_kind}/{body_id}/{tag}: face is owned by another body")
            if seen_surface_refs.intersection(normalized):
                raise ValueError(f"{source_kind}/{body_id}: exterior face is assigned to multiple CAD surfaces")
            seen_surface_refs.update(normalized)
            parsed_surfaces[str(tag)] = surface
        if seen_surface_refs != expected_face_refs:
            raise ValueError(f"{source_kind}/{body_id}: CAD surfaces do not cover exact C3D10 exterior")
        body_nodes[body_id] = referenced_nodes
        body_elements[body_id] = element_ids
        body_surfaces[body_id] = parsed_surfaces
    if seen_nodes != nodes.keys() or seen_elements != elements.keys():
        raise ValueError(f"{source_kind} body ownership does not cover the complete mesh deck")
    return MeshInput(
        source_kind=source_kind,
        report_path=report_file,
        deck_path=deck_file,
        report=report,
        report_sha256=sha256_bytes(report_bytes),
        deck_sha256=deck_sha,
        nodes=nodes,
        elements=elements,
        body_nodes=body_nodes,
        body_elements=body_elements,
        body_surfaces=body_surfaces,
    )


def _normalize_face_refs(value: Any, context: str) -> tuple[tuple[int, int], ...]:
    if not isinstance(value, list):
        raise TypeError(f"{context}: element-face references must be a list")
    refs: list[tuple[int, int]] = []
    for row in value:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            raise ValueError(f"{context}: each face reference must be [element, side]")
        element, side = row
        if isinstance(element, bool) or isinstance(side, bool):
            raise TypeError(f"{context}: element and side references must be exact integers")
        try:
            element_int, side_int = int(element), int(side)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(f"{context}: invalid element-face reference") from error
        if element_int != element or side_int != side or element_int <= 0 or side_int not in (1, 2, 3, 4):
            raise ValueError(f"{context}: element-face reference is outside C3D10 bounds")
        refs.append((element_int, side_int))
    if not refs or len(refs) != len(set(refs)):
        raise ValueError(f"{context}: face references must be nonempty and unique")
    return tuple(sorted(refs))


def _unit_face_outward(
    mesh: MeshInput,
    owner_body: str,
    element_id: int,
    side: int,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return outward normal and corner centroid for one owned C3D10 side."""
    if side not in (1, 2, 3, 4):
        raise ValueError("C3D10 face number must be 1 through 4")
    if element_id not in mesh.body_elements[owner_body]:
        raise ValueError(f"{owner_body}: surface face references an element outside its owner")
    connectivity = mesh.elements[element_id]
    face_indices = FACES[side - 1]
    corner_nodes = tuple(connectivity[index] for index in face_indices[:3])
    face_points = tuple(mesh.nodes[node] for node in corner_nodes)
    centroid = tuple(math.fsum(point[axis] for point in face_points) / 3 for axis in range(3))
    raw_normal = _cross(_sub(face_points[1], face_points[0]), _sub(face_points[2], face_points[0]))
    length = _norm(raw_normal)
    if length <= 0 or not math.isfinite(length):
        raise ValueError("C3D10 contact face has a degenerate corner triangle")
    normal = tuple(component / length for component in raw_normal)
    opposite_corner_ids = set(connectivity[:4]) - set(corner_nodes)
    if len(opposite_corner_ids) != 1:
        raise ValueError("C3D10 face does not have exactly one opposite corner")
    opposite = mesh.nodes[next(iter(opposite_corner_ids))]
    if _dot(normal, _sub(opposite, centroid)) > 0:
        normal = tuple(-component for component in normal)
    return normal, centroid


def _surface_normals(
    mesh: MeshInput,
    owner_body: str,
    refs: Iterable[tuple[int, int]],
) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]:
    normals, centers = [], []
    for element, side in refs:
        normal, center = _unit_face_outward(mesh, owner_body, element, side)
        normals.append(normal)
        centers.append(center)
    return normals, centers


def _surface_by_tag(mesh: MeshInput, owner_body: str, tag: str | int) -> dict[str, Any]:
    key = str(tag)
    try:
        row = mesh.body_surfaces[owner_body][key]
    except KeyError as error:
        raise ValueError(f"{mesh.source_kind}/{owner_body}: surface tag {key} is absent") from error
    if row.get("cad_entity_tag") != int(key):
        raise ValueError(f"{mesh.source_kind}/{owner_body}/{key}: local CAD pointer is inconsistent")
    return row


def _surface_refs(mesh: MeshInput, owner_body: str, tags: Iterable[str | int]) -> tuple[tuple[int, int], ...]:
    refs: list[tuple[int, int]] = []
    for tag in tags:
        refs.extend(_normalize_face_refs(
            _surface_by_tag(mesh, owner_body, tag).get("tri6_exterior_face_refs"),
            f"{mesh.source_kind}/{owner_body}/{tag}",
        ))
    normalized = tuple(sorted(refs))
    if not normalized or len(normalized) != len(set(normalized)):
        raise ValueError(f"{mesh.source_kind}/{owner_body}: selected semantic surface is empty or duplicated")
    return normalized


def _metal_tags_for_role(mesh: MeshInput, owner_body: str, role: str) -> tuple[str, ...]:
    matches = []
    for tag, row in mesh.body_surfaces[owner_body].items():
        classification = row.get("datum_classification", {})
        roles = classification.get("role_candidates", ()) if isinstance(classification, dict) else ()
        if role in roles:
            matches.append(tag)
    if not matches:
        raise ValueError(f"metal/{owner_body}: missing authenticated surface role {role}")
    return tuple(sorted(matches, key=int))


def _wood_plane_tags_at(
    mesh: MeshInput,
    owner_body: str,
    point_xyz: Iterable[float],
    axis: Iterable[float],
) -> tuple[str, ...]:
    point = _finite_vector(point_xyz, 3, f"{owner_body} seat point")
    direction = _unit(axis, f"{owner_body} bolt axis")
    matches = []
    for tag, row in mesh.body_surfaces[owner_body].items():
        if row.get("cad_type") != "Plane":
            continue
        analytic = row.get("analytic_surface_data", {})
        if not isinstance(analytic, dict):
            continue
        plane_point = analytic.get("sample_xyz_mm")
        plane_normal = analytic.get("sample_normal_global")
        if plane_point is None or plane_normal is None:
            continue
        plane_point = _finite_vector(plane_point, 3, f"{owner_body}/{tag} plane point")
        plane_normal = _unit(plane_normal, f"{owner_body}/{tag} plane normal")
        if abs(abs(_dot(plane_normal, direction)) - 1.0) > 1e-7:
            continue
        residual = abs(_dot(_sub(plane_point, point), direction))
        if residual <= PLANE_TOLERANCE_MM:
            matches.append(str(tag))
    if not matches:
        raise ValueError(f"wood/{owner_body}: no source plane matches the washer seat datum")
    return tuple(sorted(matches, key=int))


def _station(point: Iterable[float], origin: Iterable[float], axis: Iterable[float]) -> float:
    return _dot(_sub(point, origin), axis)


def _triangle_area(first: Iterable[float], second: Iterable[float], third: Iterable[float]) -> float:
    return 0.5 * _norm(_cross(_sub(second, first), _sub(third, first)))


def _tri6_chord_area(mesh: MeshInput, element: int, side: int) -> float:
    """Estimate a TRI6 face area by its four corner/midside chord triangles."""
    connectivity = mesh.elements[element]
    face_nodes = tuple(connectivity[index] for index in FACES[side - 1])
    points = tuple(mesh.nodes[node] for node in face_nodes)
    corners = points[:3]
    midsides = points[3:]
    triangles = (
        (corners[0], midsides[0], midsides[2]),
        (midsides[0], corners[1], midsides[1]),
        (midsides[2], midsides[1], corners[2]),
        (midsides[0], midsides[1], midsides[2]),
    )
    return math.fsum(_triangle_area(*triangle) for triangle in triangles)


def _select_axial_faces(
    mesh: MeshInput,
    owner_body: str,
    tags: Iterable[str | int],
    origin_xyz: Iterable[float],
    axis: Iterable[float],
    low_mm: float,
    high_mm: float,
) -> tuple[tuple[tuple[int, int], ...], tuple[str, ...], dict[str, Any]]:
    origin = _finite_vector(origin_xyz, 3, f"{owner_body} station origin")
    direction = _unit(axis, f"{owner_body} station axis")
    if not math.isfinite(low_mm) or not math.isfinite(high_mm) or high_mm <= low_mm:
        raise ValueError("axial face-selection interval must be finite and increasing")
    chosen: list[tuple[int, int]] = []
    selected_tags: list[str] = []
    owned_elements = set(mesh.body_elements.get(owner_body, ()))
    source_refs: set[tuple[int, int]] = set()
    selected_area = 0.0
    boundary_area = 0.0
    outside_area = 0.0
    boundary_count = 0
    outside_count = 0
    for tag in tags:
        row_refs = _normalize_face_refs(
            _surface_by_tag(mesh, owner_body, tag).get("tri6_exterior_face_refs"),
            f"metal/{owner_body}/{tag}",
        )
        local: list[tuple[int, int]] = []
        for element, side in row_refs:
            ref = (element, side)
            if ref in source_refs:
                raise ValueError(f"metal/{owner_body}: axial source surfaces repeat a TRI6 face")
            source_refs.add(ref)
            if element not in owned_elements:
                raise ValueError(f"metal/{owner_body}: axial source face is outside its body ownership")
            connectivity = mesh.elements[element]
            face_nodes = tuple(connectivity[index] for index in FACES[side - 1])
            stations = tuple(_station(mesh.nodes[node], origin, direction) for node in face_nodes)
            area = _tri6_chord_area(mesh, element, side)
            if not math.isfinite(area) or area <= 0:
                raise ValueError(f"metal/{owner_body}: axial source face has invalid TRI6 area")
            if (
                min(stations) >= low_mm - AXIAL_FACE_NODE_TOLERANCE_MM
                and max(stations) <= high_mm + AXIAL_FACE_NODE_TOLERANCE_MM
            ):
                local.append((element, side))
                selected_area += area
            elif max(stations) < low_mm - AXIAL_FACE_NODE_TOLERANCE_MM or min(stations) > high_mm + AXIAL_FACE_NODE_TOLERANCE_MM:
                outside_count += 1
                outside_area += area
            else:
                boundary_count += 1
                boundary_area += area
        if local:
            selected_tags.append(str(tag))
            chosen.extend(local)
    normalized = tuple(sorted(chosen))
    if not normalized or len(normalized) != len(set(normalized)):
        raise ValueError(f"metal/{owner_body}: axial contact patch is empty or duplicated")
    touched_area = selected_area + boundary_area
    return normalized, tuple(selected_tags), {
        "method": "all_six_TRI6_face_nodes_inside_interval",
        "interval_mm": [float(low_mm), float(high_mm)],
        "node_station_tolerance_mm": AXIAL_FACE_NODE_TOLERANCE_MM,
        "source_face_count": len(source_refs),
        "selected_face_count": len(normalized),
        "boundary_excluded_face_count": boundary_count,
        "outside_interval_face_count": outside_count,
        "selected_chord_area_estimate_mm2": selected_area,
        "boundary_excluded_chord_area_estimate_mm2": boundary_area,
        "outside_interval_chord_area_estimate_mm2": outside_area,
        "touched_chord_area_estimate_mm2": touched_area,
        "contained_area_fraction_of_touched_faces": selected_area / touched_area if touched_area > 0 else None,
        "area_method": "four linear chord triangles through each TRI6 face's six nodes",
        "contact_or_strength_result": False,
    }


def _response_readiness(contact_pairs: list[dict[str, Any]]) -> dict[str, Any]:
    """Gate contact-patch readiness on complete axial station coverage.

    Station-crossing TRI6 faces are excluded whole. Their reported chord area is
    a whole-face estimate rather than the exact clipped omission, so any such
    face blocks patch response readiness until a clipped-face resolver closes
    the coverage gap. The geometric fragment remains available for diagnosis.
    """
    axial_categories = {
        "bolt_shank_to_receiver_bore",
        "bolt_to_washer_bore",
        "projected_thread_radial_contact_only",
    }
    unresolved: list[dict[str, Any]] = []
    missing_audits: list[str] = []
    excluded_face_counts: list[int] = []
    excluded_areas: list[float] = []
    for pair in contact_pairs:
        pair_id = str(pair.get("pair_id", "<unnamed>"))
        audits: list[tuple[str, dict[str, Any]]] = []
        for side_name in ("slave", "master"):
            side = pair.get(side_name)
            if not isinstance(side, dict):
                continue
            audit = side.get("axial_face_selection_audit")
            if audit is not None:
                if not isinstance(audit, dict):
                    raise ValueError(
                        f"{pair_id}/{side_name}: axial face-selection audit must be an object"
                    )
                audits.append((side_name, audit))
        if pair.get("category") in axial_categories and not audits:
            missing_audits.append(pair_id)
            continue
        for side_name, audit in audits:
            face_count = audit.get("boundary_excluded_face_count")
            area = audit.get("boundary_excluded_chord_area_estimate_mm2")
            if (
                isinstance(face_count, bool)
                or not isinstance(face_count, int)
                or face_count < 0
            ):
                raise ValueError(
                    f"{pair_id}/{side_name}: invalid boundary-excluded face count"
                )
            if (
                isinstance(area, bool)
                or not isinstance(area, (int, float))
                or not math.isfinite(float(area))
                or float(area) < 0
            ):
                raise ValueError(
                    f"{pair_id}/{side_name}: invalid boundary-excluded chord area"
                )
            area_value = float(area)
            excluded_face_counts.append(face_count)
            excluded_areas.append(area_value)
            if face_count > 0 or area_value > 0:
                unresolved.append(
                    {
                        "pair_id": pair_id,
                        "side": side_name,
                        "owner_body": pair[side_name].get("owner_body"),
                        "boundary_excluded_face_count": face_count,
                        "boundary_excluded_chord_area_estimate_mm2": area_value,
                        "true_interval_omitted_area_known": False,
                    }
                )

    coverage_ready = not unresolved and not missing_audits
    blockers = []
    if unresolved:
        blockers.append(
            "station-straddling faces were excluded whole; resolve clipped contact area"
        )
    if missing_audits:
        blockers.append("axial contact pairs lack a face-selection audit")
    blockers.append(
        "the contact fragment has no materials, restraints, loads, or solved response"
    )
    return {
        "status": (
            "NOT_RESPONSE_READY_AXIAL_BOUNDARY_EXCLUSIONS"
            if unresolved or missing_audits
            else "NOT_RESPONSE_READY_INCOMPLETE_MODEL"
        ),
        "response_ready": False,
        "axial_contact_patch_coverage_ready": coverage_ready,
        "boundary_excluded_face_count": sum(excluded_face_counts),
        "boundary_excluded_chord_area_estimate_mm2": math.fsum(excluded_areas),
        "chord_area_is_exact_interval_omission": False,
        "unresolved_boundary_exclusions": unresolved,
        "axial_pairs_missing_selection_audit": missing_audits,
        "blockers": blockers,
    }


def _radial_alignment(
    mesh: MeshInput,
    owner_body: str,
    refs: Iterable[tuple[int, int]],
    origin_xyz: Iterable[float],
    axis: Iterable[float],
) -> tuple[float, float]:
    origin = _finite_vector(origin_xyz, 3, f"{owner_body} cylinder origin")
    direction = _unit(axis, f"{owner_body} cylinder axis")
    values = []
    for element, side in refs:
        normal, center = _unit_face_outward(mesh, owner_body, element, side)
        delta = _sub(center, origin)
        station = _dot(delta, direction)
        radial = _sub(delta, tuple(station * component for component in direction))
        radial_unit = _unit(radial, f"{owner_body} radial face center")
        values.append(_dot(normal, radial_unit))
    return min(values), math.fsum(values) / len(values)


def _validate_normal_audit(
    audit: dict[str, Any],
    classification_sha256: str,
    wood_mesh: MeshInput,
) -> dict[tuple[str, str], dict[str, Any]]:
    if audit.get("status") != WOOD_NORMAL_AUDIT_STATUS:
        raise ValueError("wood outward-normal audit did not pass")
    if audit.get("classification_sha256") != classification_sha256:
        raise ValueError("wood outward-normal audit is not bound to the surface classification")
    if audit.get("mesh_deck_sha256") != wood_mesh.deck_sha256 or audit.get("mesh_report_sha256") != wood_mesh.report_sha256:
        raise ValueError("wood outward-normal audit is not bound to the exact mesh inputs")
    if audit.get("contact_or_pressure_assigned") is not False or audit.get("native_solve_run") is not False:
        raise ValueError("wood normal audit exceeds its geometry-only scope")
    rows = audit.get("interface_side_rows")
    if not isinstance(rows, list) or len(rows) != 8:
        raise ValueError("wood normal audit must contain both outward sides of all four interfaces")
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("wood normal audit side row must be an object")
        key = (str(row.get("interface_id")), str(row.get("member_id")))
        if key in result:
            raise ValueError("wood normal audit repeats an interface/member side")
        if row.get("minimum_outward_alignment", 0) < FACE_NORMAL_TOLERANCE:
            raise ValueError("wood normal audit has an outward side with an incompatible normal")
        result[key] = row
    if len({key[0] for key in result}) != 4:
        raise ValueError("wood normal audit does not cover four named interfaces")
    return result


def _validate_surface_classification(
    classification: dict[str, Any],
    classification_sha256: str,
    wood_mesh: MeshInput,
    normal_rows: dict[tuple[str, str], dict[str, Any]],
    mechanics: dict[str, Any],
    mechanics_sha256: str,
    patch_inventory: dict[str, Any],
    patch_inventory_sha256: str,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    if classification.get("schema") != surface_contract.SCHEMA:
        raise ValueError("surface classification schema is not the WJ04 source-bound classification")
    if classification.get("status") != "SOURCE_BOUND_GEOMETRIC_SURFACE_CLASSIFICATION_ONLY":
        raise ValueError("surface classification is not the frozen geometry-only result")
    if classification.get("native_solve_run") is not False or classification.get("contact_law_assigned") is not False:
        raise ValueError("surface classification exceeds its no-solver/no-contact scope")
    source_hashes = classification.get("source_hashes", {})
    if source_hashes.get("mesh.json") != wood_mesh.report_sha256 or source_hashes.get("mesh.inp") != wood_mesh.deck_sha256:
        raise ValueError("surface classification is not bound to the supplied wood mesh")
    if source_hashes.get("patch_bundle/inventory.json") != patch_inventory_sha256:
        raise ValueError("surface classification is not bound to the supplied patch inventory")
    if wood_mesh.report.get("input_bundle_inventory_sha256") != patch_inventory_sha256:
        raise ValueError("wood mesh and supplied patch inventory are not source-bound")
    if patch_inventory.get("schema") != "wood_joint_wj04_patch_geometry/v1" or patch_inventory.get("status") != "source_bound_finished_geometry_export_inputs_only":
        raise ValueError("patch inventory is not the source-bound finished WJ04 geometry export")
    composition = patch_inventory.get("composition", {})
    if composition.get("mechanics_manifest_sha256") != mechanics_sha256:
        raise ValueError("patch inventory and mechanics manifest are not source-bound")
    if composition.get("live_composition_report_matches_archive") is not True:
        raise ValueError("patch inventory composition report is not authenticated to its archive")
    mechanics_bolts = mechanics.get("physical_bolts")
    mechanics_interfaces = mechanics.get("physical_interfaces")
    patch_bolts = patch_inventory.get("physical_bolts")
    if not isinstance(mechanics_bolts, list) or len(mechanics_bolts) != len(STACK_IDS):
        raise ValueError("mechanics manifest must contain exactly eight physical bolt records")
    if not isinstance(mechanics_interfaces, list) or len(mechanics_interfaces) != len(EXPECTED_INTERFACE_IDS):
        raise ValueError("mechanics manifest must contain exactly four physical interfaces")
    if not isinstance(patch_bolts, list) or len(patch_bolts) != len(STACK_IDS):
        raise ValueError("patch inventory must contain exactly eight physical bolt records")
    mechanics_bolt_ids = [row.get("stack_spec_id") for row in mechanics_bolts if isinstance(row, dict)]
    mechanics_physical_bolt_ids = [
        row.get("physical_bolt_id") for row in mechanics_bolts if isinstance(row, dict)
    ]
    mechanics_interface_ids = [row.get("interface_id") for row in mechanics_interfaces if isinstance(row, dict)]
    patch_stack_ids = [row.get("stack_spec_id") for row in patch_bolts if isinstance(row, dict)]
    patch_physical_bolt_ids = [
        row.get("physical_bolt_id") for row in patch_bolts if isinstance(row, dict)
    ]
    if len(mechanics_bolt_ids) != len(mechanics_bolts) or set(mechanics_bolt_ids) != set(STACK_IDS) or len(set(mechanics_bolt_ids)) != len(STACK_IDS):
        raise ValueError("mechanics manifest bolt rows must uniquely cover the eight expected stack IDs")
    if (
        len(mechanics_physical_bolt_ids) != len(mechanics_bolts)
        or any(
            not isinstance(value, str) or not value.strip()
            for value in mechanics_physical_bolt_ids
        )
        or len(set(mechanics_physical_bolt_ids)) != len(STACK_IDS)
    ):
        raise ValueError("mechanics manifest must name eight unique physical bolt IDs")
    if len(mechanics_interface_ids) != len(mechanics_interfaces) or set(mechanics_interface_ids) != set(EXPECTED_INTERFACE_IDS) or len(set(mechanics_interface_ids)) != len(EXPECTED_INTERFACE_IDS):
        raise ValueError("mechanics manifest interface rows must uniquely cover the four expected interfaces")
    if len(patch_stack_ids) != len(patch_bolts) or set(patch_stack_ids) != set(STACK_IDS) or len(set(patch_stack_ids)) != len(STACK_IDS):
        raise ValueError("patch inventory bolt rows must uniquely cover the eight expected stack IDs")
    if (
        len(patch_physical_bolt_ids) != len(patch_bolts)
        or any(
            not isinstance(value, str) or not value.strip()
            for value in patch_physical_bolt_ids
        )
        or len(set(patch_physical_bolt_ids)) != len(STACK_IDS)
    ):
        raise ValueError("patch inventory must name eight unique physical bolt IDs")
    mechanics_by_stack = {row["stack_spec_id"]: row for row in mechanics_bolts}
    mechanics_by_interface = {row["interface_id"]: row for row in mechanics_interfaces}
    patch_by_stack = {row["stack_spec_id"]: row for row in patch_bolts}
    for interface_id in EXPECTED_INTERFACE_IDS:
        interface = mechanics_by_interface[interface_id]
        expected_stacks = list(wood_mesh_contract.EXPECTED_INTERFACE_STACKS[interface_id])
        if interface.get("family_stack_ids") != expected_stacks:
            raise ValueError(f"{interface_id}: mechanics family stack mapping differs from WJ04 contract")
        members = interface.get("members_head_to_nut")
        candidate_part = interface.get("candidate_cleat_face", {}).get("part_id")
        host_part = interface.get("source_host_face", {}).get("part_id")
        if not isinstance(members, list) or len(members) != 2 or len(set(members)) != 2:
            raise ValueError(f"{interface_id}: mechanics interface must name two ordered member owners")
        expected_members = wood_mesh_contract.STACK_RECEIVERS[expected_stacks[0]]
        if tuple(members) != expected_members:
            raise ValueError(f"{interface_id}: mechanics interface member order differs from its frozen receiver axes")
        for stack_id in expected_stacks:
            receivers = mechanics_by_stack[stack_id].get("receivers_head_to_nut")
            if not isinstance(receivers, list) or tuple(
                row.get("member_id") for row in receivers if isinstance(row, dict)
            ) != expected_members or len(receivers) != 2:
                raise ValueError(f"{interface_id}/{stack_id}: mechanics receivers differ from the exact ordered interface members")
        if candidate_part not in members or host_part not in members or candidate_part == host_part:
            raise ValueError(f"{interface_id}: mechanics candidate/host face owners are inconsistent")
    expected_bore_keys = {
        (stack_id, receiver["member_id"])
        for stack_id, bolt in mechanics_by_stack.items()
        for receiver in bolt.get("receivers_head_to_nut", ())
    }
    def vectors_match(first: Any, second: Any, *, tolerance: float = 1e-7) -> bool:
        try:
            a = _finite_vector(first, 3, "source identity vector")
            b = _finite_vector(second, 3, "source identity vector")
        except ValueError:
            return False
        return _norm(_sub(a, b)) <= tolerance

    def scalars_match(first: Any, second: Any, *, tolerance: float = 1e-7) -> bool:
        if isinstance(first, bool) or isinstance(second, bool):
            return False
        try:
            a, b = float(first), float(second)
        except (TypeError, ValueError, OverflowError):
            return False
        return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance

    for stack_id in STACK_IDS:
        bolt = mechanics_by_stack[stack_id]
        patch_bolt = patch_by_stack[stack_id]
        if patch_bolt.get("physical_bolt_id") != bolt.get("physical_bolt_id"):
            raise ValueError(f"{stack_id}: mechanics and patch inventory physical bolt IDs differ")
        expected_interface = next(
            key for key, stack_ids in wood_mesh_contract.EXPECTED_INTERFACE_STACKS.items()
            if stack_id in stack_ids
        )
        interface = mechanics_by_interface[expected_interface]
        if stack_id not in interface["family_stack_ids"]:
            raise ValueError(f"{stack_id}: mechanics bolt is not owned by its expected interface")
        if expected_interface.split("__", 1)[-1] != bolt.get("interface_id"):
            raise ValueError(f"{stack_id}: mechanics bolt family label does not match its WJ04 interface")
        if patch_bolt.get("interface_id") != expected_interface:
            raise ValueError(f"{stack_id}: patch inventory bolt is assigned to the wrong full interface")
        if patch_bolt.get("receivers_head_to_nut") != bolt.get("receivers_head_to_nut"):
            raise ValueError(f"{stack_id}: mechanics and patch inventory receiver identities differ")
        if patch_bolt.get("wood_grip_mm") != bolt.get("wood_grip_mm"):
            raise ValueError(f"{stack_id}: mechanics and patch inventory wood grips differ")
        if not vectors_match(patch_bolt.get("world_axis_origin_xyz_mm"), bolt.get("world_axis_origin_xyz_mm")):
            raise ValueError(f"{stack_id}: mechanics and patch inventory axis origins differ")
        if not vectors_match(patch_bolt.get("world_axis_direction_head_to_nut"), bolt.get("world_axis_direction_head_to_nut")):
            raise ValueError(f"{stack_id}: mechanics and patch inventory axes differ")
        bore = patch_bolt.get("composed_occupancy_bore", {})
        _positive_finite(bore.get("volume_mm3"), f"{stack_id} occupancy bore volume")
    wood_pairs = classification.get("wood_contact_pairs")
    bore_pairs = classification.get("candidate_bore_member_pairs")
    if not isinstance(wood_pairs, list) or len(wood_pairs) != 4:
        raise ValueError("surface classification must contain four finite wood interface pairs")
    if not isinstance(bore_pairs, list) or len(bore_pairs) != 16:
        raise ValueError("surface classification must contain sixteen authenticated bore/member pairs")
    by_interface: dict[str, dict[str, Any]] = {}
    seen_wood_ids: set[str] = set()
    for row in wood_pairs:
        if not isinstance(row, dict) or row.get("interface_id") in by_interface:
            raise ValueError("wood surface classification repeats or malforms an interface")
        interface_id = str(row["interface_id"])
        if interface_id in seen_wood_ids:
            raise ValueError("wood surface classification repeats an interface ID")
        seen_wood_ids.add(interface_id)
        if interface_id not in EXPECTED_INTERFACE_IDS or row.get("active_pressure_established") is not False:
            raise ValueError("wood contact row is outside the four geometry-only interfaces")
        candidate = str(row.get("candidate_member_id"))
        host = str(row.get("host_member_id"))
        mechanics_interface = mechanics_by_interface[interface_id]
        if candidate != mechanics_interface["candidate_cleat_face"]["part_id"] or host != mechanics_interface["source_host_face"]["part_id"]:
            raise ValueError(f"{interface_id}: classified candidate/host owners differ from mechanics datums")
        if set(mechanics_interface["members_head_to_nut"]) != {candidate, host}:
            raise ValueError(f"{interface_id}: classified owners differ from the two mechanics interface members")
        if candidate == host or candidate not in WOOD_BODY_IDS or host not in WOOD_BODY_IDS:
            raise ValueError(f"{interface_id}: invalid candidate/host member ownership")
        candidate_surfaces = row.get("candidate_surfaces")
        host_surfaces = row.get("host_surfaces")
        if not isinstance(candidate_surfaces, list) or not candidate_surfaces or not isinstance(host_surfaces, list) or not host_surfaces:
            raise ValueError(f"{interface_id}: finite face-pair surface mapping is missing")
        candidate_tags = tuple(int(item["cad_entity_tag"]) for item in candidate_surfaces)
        host_tags = tuple(int(item["cad_entity_tag"]) for item in host_surfaces)
        candidate_refs = _surface_refs(wood_mesh, candidate, candidate_tags)
        host_refs = _surface_refs(wood_mesh, host, host_tags)
        if len(candidate_refs) != int(normal_rows[(interface_id, candidate)]["exterior_tri6_face_count"]):
            raise ValueError(f"{interface_id}: candidate face ownership differs from normal audit")
        if len(host_refs) != int(normal_rows[(interface_id, host)]["exterior_tri6_face_count"]):
            raise ValueError(f"{interface_id}: host face ownership differs from normal audit")
        area = _positive_finite(row.get("archived_finite_common_area_mm2"), f"{interface_id} finite common area")
        if row.get("host_area_is_not_equated_to_common_footprint") is not True:
            raise ValueError(f"{interface_id}: broad host area cannot be credited as the finite footprint")
        by_interface[interface_id] = {
            "row": row,
            "candidate_tags": candidate_tags,
            "host_tags": host_tags,
            "candidate_refs": candidate_refs,
            "host_refs": host_refs,
            "finite_common_area_mm2": area,
        }
    if set(by_interface) != set(EXPECTED_INTERFACE_IDS):
        raise ValueError("surface classification omits an expected WJ04 interface")
    seen_bore_keys: set[tuple[str, str]] = set()
    seen_semantic_pair_ids: set[str] = set()
    for row in bore_pairs:
        if not isinstance(row, dict) or row.get("contact_or_strength_result") is not False:
            raise ValueError("bolt-bore classification must remain geometric only")
        stack_id = str(row.get("stack_spec_id"))
        owner = str(row.get("member_id"))
        bore_key = (stack_id, owner)
        if bore_key in seen_bore_keys:
            raise ValueError(f"{stack_id}/{owner}: classification repeats a bolt-bore owner pair")
        seen_bore_keys.add(bore_key)
        semantic_pair_id = row.get("semantic_pair_id")
        if not isinstance(semantic_pair_id, str) or not semantic_pair_id or semantic_pair_id in seen_semantic_pair_ids:
            raise ValueError("bolt-bore semantic pair IDs must be present and unique")
        seen_semantic_pair_ids.add(semantic_pair_id)
        if stack_id not in mechanics_by_stack:
            raise ValueError(f"{stack_id}: bore classification names an unknown physical stack")
        bolt = mechanics_by_stack[stack_id]
        expected_interface = next(
            key for key, stack_ids in wood_mesh_contract.EXPECTED_INTERFACE_STACKS.items()
            if stack_id in stack_ids
        )
        if row.get("interface_id") != expected_interface:
            raise ValueError(f"{stack_id}/{owner}: bore classification is assigned to the wrong interface")
        if row.get("physical_bolt_id") != bolt.get("physical_bolt_id"):
            raise ValueError(f"{stack_id}/{owner}: bore classification physical bolt ID differs from mechanics")
        receivers = bolt.get("receivers_head_to_nut")
        if not isinstance(receivers, list) or len(receivers) != 2:
            raise ValueError(f"{stack_id}: mechanics bolt must identify two ordered receivers")
        receiver_ids = [receiver.get("member_id") for receiver in receivers]
        if row.get("receiver_order_head_to_nut") != receiver_ids or owner not in receiver_ids:
            raise ValueError(f"{stack_id}/{owner}: bore receiver ordering differs from mechanics")
        receiver_index = receiver_ids.index(owner)
        interval = _finite_vector(row.get("receiver_layer_station_mm"), 2, f"{stack_id}/{owner} receiver interval")
        low_expected = math.fsum(float(item["wood_thickness_mm"]) for item in receivers[:receiver_index])
        high_expected = low_expected + float(receivers[receiver_index]["wood_thickness_mm"])
        if not scalars_match(interval[0], low_expected) or not scalars_match(interval[1], high_expected):
            raise ValueError(f"{stack_id}/{owner}: bore receiver interval differs from ordered mechanics thicknesses")
        if not vectors_match(row.get("axis_origin_xyz_mm"), bolt.get("world_axis_origin_xyz_mm")):
            raise ValueError(f"{stack_id}/{owner}: bore axis origin differs from mechanics")
        if not vectors_match(row.get("axis_direction_head_to_nut"), bolt.get("world_axis_direction_head_to_nut")):
            raise ValueError(f"{stack_id}/{owner}: bore axis direction differs from mechanics")
        patch_bolt = patch_by_stack[stack_id]
        patch_volume = _positive_finite(patch_bolt["composed_occupancy_bore"].get("volume_mm3"), f"{stack_id} occupancy bore volume")
        radius_expected = math.sqrt(patch_volume / (math.pi * (float(bolt["wood_grip_mm"]) + 0.2)))
        if not scalars_match(row.get("analysis_occupancy_bore_radius_mm"), radius_expected, tolerance=1e-6):
            raise ValueError(f"{stack_id}/{owner}: analysis bore radius differs from source occupancy volume")
        if owner not in WOOD_BODY_IDS or row.get("occupancy_bore_is_hardware_or_drill_instruction") is not False:
            raise ValueError("bolt-bore mapping must identify a wood owner and analysis-only bore")
        surfaces = row.get("matched_surfaces")
        if not isinstance(surfaces, list) or not surfaces:
            raise ValueError("bolt-bore member side is missing its classified finite surface")
        tags = tuple(int(item["cad_entity_tag"]) for item in surfaces)
        refs = _surface_refs(wood_mesh, owner, tags)
        if not refs or _positive_finite(row.get("analysis_occupancy_bore_radius_mm"), "analysis bore radius") <= 0:
            raise ValueError("bolt-bore classification lacks a finite bore surface/radius")
        row["_resolved_member_tags"] = tags
        row["_resolved_member_refs"] = refs
    if seen_bore_keys != expected_bore_keys:
        raise ValueError("bore classification must cover each expected stack/receiver exactly once")
    return by_interface, bore_pairs


def _merge_meshes(wood: MeshInput, metal: MeshInput) -> dict[str, Any]:
    merged_nodes: dict[int, tuple[float, float, float]] = {}
    merged_elements: dict[int, tuple[int, ...]] = {}
    body_maps: dict[str, dict[str, dict[int, int]]] = {"wood": {}, "metal": {}}
    body_node_ids: dict[str, tuple[int, ...]] = {}
    body_element_ids: dict[str, tuple[int, ...]] = {}
    body_inventory: list[dict[str, Any]] = []
    next_node = 1
    next_element = 1
    for mesh in (wood, metal):
        for owner_body in sorted(mesh.body_elements):
            node_map = {old: new for new, old in enumerate(sorted(mesh.body_nodes[owner_body]), start=next_node)}
            element_map = {old: new for new, old in enumerate(sorted(mesh.body_elements[owner_body]), start=next_element)}
            next_node += len(node_map)
            next_element += len(element_map)
            body_maps[mesh.source_kind][owner_body] = {"nodes": node_map, "elements": element_map}
            new_nodes = tuple(sorted(node_map.values()))
            new_elements = tuple(sorted(element_map.values()))
            body_node_ids[owner_body] = new_nodes
            body_element_ids[owner_body] = new_elements
            merged_nodes.update({node_map[old]: xyz for old, xyz in mesh.nodes.items() if old in node_map})
            for old in mesh.body_elements[owner_body]:
                conn = mesh.elements[old]
                merged_elements[element_map[old]] = tuple(node_map[node] for node in conn)
            body_inventory.append({
                "body_id": owner_body,
                "source_kind": mesh.source_kind,
                "node_set": _body_set_name(owner_body, "N"),
                "element_set": _body_set_name(owner_body, "E"),
                "node_count": len(node_map),
                "element_count": len(element_map),
                "remapped_node_min_max": [min(new_nodes), max(new_nodes)],
                "remapped_element_min_max": [min(new_elements), max(new_elements)],
            })
    if len(merged_nodes) != len(set(merged_nodes)) or len(merged_elements) != len(set(merged_elements)):
        raise ValueError("deterministic body remapping produced duplicate global IDs")
    return {
        "nodes": merged_nodes,
        "elements": merged_elements,
        "body_maps": body_maps,
        "body_node_ids": body_node_ids,
        "body_element_ids": body_element_ids,
        "body_inventory": body_inventory,
    }


def _body_set_name(body_id: str, kind: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_]", "_", body_id).upper()
    return f"WJ04_{kind}_{token}"


def _surface_name(index: int, side: str) -> str:
    return f"WJ04_CP_{index:03d}_{side}"


def _format_id_set(name: str, ids: Iterable[int], *, card: str) -> list[str]:
    values = tuple(sorted(ids))
    if not values:
        raise ValueError(f"{name}: cannot write an empty {card}")
    lines = [f"*{card},{card}={name}"]
    lines.extend(",".join(str(value) for value in values[start : start + 16]) for start in range(0, len(values), 16))
    return lines


def _render_mesh_cards(merged: dict[str, Any]) -> list[str]:
    lines = ["** WJ04 body mesh fragment; nodes remain disjoint across every solid", "*NODE"]
    lines.extend(
        f"{node}," + ",".join(f"{value:.15g}" for value in xyz)
        for node, xyz in sorted(merged["nodes"].items())
    )
    for body in merged["body_inventory"]:
        owner = body["body_id"]
        elset = body["element_set"]
        lines.append(f"*ELEMENT,TYPE=C3D10,ELSET={elset}")
        lines.extend(
            f"{element}," + ",".join(str(node) for node in merged["elements"][element])
            for element in merged["body_element_ids"][owner]
        )
        lines.extend(_format_id_set(body["node_set"], merged["body_node_ids"][owner], card="NSET"))
    return lines


def _normal_and_center(mesh: MeshInput, owner: str, refs: Iterable[tuple[int, int]]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    normals, centers = _surface_normals(mesh, owner, refs)
    average = tuple(math.fsum(row[axis] for row in normals) for axis in range(3))
    normal = _unit(average, f"{mesh.source_kind}/{owner} mean surface normal")
    for row in normals:
        if _dot(row, normal) < FACE_NORMAL_TOLERANCE:
            raise ValueError(f"{mesh.source_kind}/{owner}: planar contact surface has inconsistent outward faces")
    center = tuple(math.fsum(row[axis] for row in centers) / len(centers) for axis in range(3))
    return normal, center


def _build_contact_pairs(
    wood: MeshInput,
    metal: MeshInput,
    classification: dict[str, Any],
    classified_wood: dict[str, dict[str, Any]],
    bore_rows: list[dict[str, Any]],
    mechanics: dict[str, Any],
    hardware_inventory: dict[str, Any],
    stacks: dict[str, dict[str, Any]],
    seat_audit_by_key: dict[tuple[str, str], dict[str, Any]],
    merged: dict[str, Any],
) -> list[dict[str, Any]]:
    bolt_rows = mechanics.get("physical_bolts")
    if not isinstance(bolt_rows, list) or len(bolt_rows) != len(STACK_IDS):
        raise ValueError("mechanics input does not bind exactly eight physical bolts")
    input_bolt_ids = [row.get("stack_spec_id") for row in bolt_rows if isinstance(row, dict)]
    if len(input_bolt_ids) != len(bolt_rows) or len(set(input_bolt_ids)) != len(STACK_IDS) or set(input_bolt_ids) != set(STACK_IDS):
        raise ValueError("mechanics input does not bind the exact eight physical bolts")
    interface_rows = mechanics.get("physical_interfaces")
    if not isinstance(interface_rows, list) or len(interface_rows) != len(EXPECTED_INTERFACE_IDS):
        raise ValueError("mechanics input does not bind exactly four physical interfaces")
    input_interface_ids = [row.get("interface_id") for row in interface_rows if isinstance(row, dict)]
    if len(input_interface_ids) != len(interface_rows) or len(set(input_interface_ids)) != len(EXPECTED_INTERFACE_IDS) or set(input_interface_ids) != set(EXPECTED_INTERFACE_IDS):
        raise ValueError("mechanics input does not bind the four physical interfaces")
    interfaces = {row["interface_id"]: row for row in interface_rows}
    profile = metal.report.get("scenario_id")
    pair_rows: list[dict[str, Any]] = []
    surface_cache: dict[tuple[Any, ...], str] = {}
    bolt_face_owners: dict[tuple[str, tuple[int, int]], str] = {}

    def register_side(
        source: MeshInput,
        owner: str,
        tags: Iterable[str | int],
        refs: Iterable[tuple[int, int]],
        semantic_role: str,
        axial_face_selection_audit: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        tag_values = tuple(sorted({str(tag) for tag in tags}, key=lambda value: int(value)))
        source_refs = tuple(sorted(refs))
        if not source_refs:
            raise ValueError(f"{source.source_kind}/{owner}/{semantic_role}: empty finite contact surface")
        element_map = merged["body_maps"][source.source_kind][owner]["elements"]
        node_map = merged["body_maps"][source.source_kind][owner]["nodes"]
        mapped_refs = tuple(sorted((element_map[element], side) for element, side in source_refs))
        key = (source.source_kind, owner, mapped_refs)
        if key not in surface_cache:
            surface_cache[key] = _surface_name(len(surface_cache) + 1, "A")
        face_node_ids = tuple(sorted({
            node_map[source.elements[element][index]]
            for element, side in source_refs
            for index in FACES[side - 1]
        }))
        node_set_name = f"WJ04_N_{surface_cache[key]}"
        result = {
            "surface_name": surface_cache[key],
            "node_set_name": node_set_name,
            "owner_body": owner,
            "source_kind": source.source_kind,
            "semantic_role": semantic_role,
            "source_cad_surface_tags": list(tag_values),
            "source_face_count": len(source_refs),
            "remapped_face_refs": mapped_refs,
            "remapped_face_node_ids": face_node_ids,
            "source_face_refs": source_refs,
        }
        if axial_face_selection_audit is not None:
            if axial_face_selection_audit.get("selected_face_count") != len(source_refs):
                raise ValueError(f"{source.source_kind}/{owner}/{semantic_role}: axial audit count differs from owned faces")
            result["axial_face_selection_audit"] = axial_face_selection_audit
        return result

    def append_pair(
        pair_id: str,
        category: str,
        interface_id: str | None,
        slave_mesh: MeshInput,
        slave_owner: str,
        slave_tags: Iterable[str | int],
        slave_refs: Iterable[tuple[int, int]],
        slave_role: str,
        master_mesh: MeshInput,
        master_owner: str,
        master_tags: Iterable[str | int],
        master_refs: Iterable[tuple[int, int]],
        master_role: str,
        *,
        slave_axial_face_selection_audit: dict[str, Any] | None = None,
        master_axial_face_selection_audit: dict[str, Any] | None = None,
        common_area_mm2: float | None,
        initial_state_assumption: str,
        normal_mode: str = "opposed_planar",
        radial_origin_xyz_mm: Iterable[float] | None = None,
        radial_axis: Iterable[float] | None = None,
        expected_radial_signs: tuple[int, int] | None = None,
        clearance_by_diameter_mm: dict[str, float] | None = None,
    ) -> None:
        slave_ref_tuple = tuple(sorted(slave_refs))
        master_ref_tuple = tuple(sorted(master_refs))
        slave = register_side(
            slave_mesh, slave_owner, slave_tags, slave_ref_tuple, slave_role,
            slave_axial_face_selection_audit,
        )
        master = register_side(
            master_mesh, master_owner, master_tags, master_ref_tuple, master_role,
            master_axial_face_selection_audit,
        )
        if slave["surface_name"] == master["surface_name"]:
            raise ValueError(f"{pair_id}: contact sides cannot share one surface definition")
        normal_check: dict[str, Any]
        if normal_mode == "opposed_planar":
            slave_normal, _ = _normal_and_center(slave_mesh, slave_owner, slave_ref_tuple)
            master_normal, _ = _normal_and_center(master_mesh, master_owner, master_ref_tuple)
            dot = _dot(slave_normal, master_normal)
            if dot > -FACE_NORMAL_TOLERANCE:
                raise ValueError(f"{pair_id}: owned planar face normals are not opposed")
            normal_check = {
                "mode": normal_mode,
                "slave_mean_outward_normal_xyz": list(slave_normal),
                "master_mean_outward_normal_xyz": list(master_normal),
                "mean_outward_normal_dot": dot,
                "passed": True,
            }
        elif normal_mode == "opposed_radial":
            if radial_origin_xyz_mm is None or radial_axis is None or expected_radial_signs is None:
                raise ValueError(f"{pair_id}: radial surface audit needs an axis and signs")
            slave_min, slave_mean = _radial_alignment(slave_mesh, slave_owner, slave_ref_tuple, radial_origin_xyz_mm, radial_axis)
            master_min, master_mean = _radial_alignment(master_mesh, master_owner, master_ref_tuple, radial_origin_xyz_mm, radial_axis)
            slave_sign, master_sign = expected_radial_signs
            if slave_sign * slave_min < RADIAL_NORMAL_TOLERANCE or master_sign * master_min < RADIAL_NORMAL_TOLERANCE:
                raise ValueError(f"{pair_id}: owned cylindrical faces do not face their named radial partner")
            normal_check = {
                "mode": normal_mode,
                "radial_origin_xyz_mm": list(_finite_vector(radial_origin_xyz_mm, 3, "radial origin")),
                "radial_axis_unit_xyz": list(_unit(radial_axis, "radial axis")),
                "slave_expected_radial_sign": slave_sign,
                "slave_min_outward_radial_alignment": slave_min,
                "slave_mean_outward_radial_alignment": slave_mean,
                "master_expected_radial_sign": master_sign,
                "master_min_outward_radial_alignment": master_min,
                "master_mean_outward_radial_alignment": master_mean,
                "passed": True,
            }
        else:
            raise ValueError(f"{pair_id}: unsupported contact normal mode {normal_mode}")
        for source, owner, refs in (
            (slave_mesh, slave_owner, slave_ref_tuple),
            (master_mesh, master_owner, master_ref_tuple),
        ):
            if source.source_kind != "metal" or not owner.endswith("__bolt"):
                continue
            for ref in refs:
                key = (owner, ref)
                previous = bolt_face_owners.get(key)
                if previous is not None:
                    raise ValueError(
                        f"{pair_id}: bolt face {owner}/{ref} is already owned by {previous}"
                    )
                bolt_face_owners[key] = pair_id
        for side in (slave, master):
            side.pop("source_face_refs")
        pair_rows.append({
            "pair_id": pair_id,
            "category": category,
            "interface_id": interface_id,
            "slave": slave,
            "master": master,
            "finite_common_area_mm2": common_area_mm2,
            "initial_state_assumption": initial_state_assumption,
            "normal_audit": normal_check,
            "law": {
                "normal": "compression_only",
                "opening": "allowed",
                "tension_transfer": False,
                "tangential": "frictionless",
                "friction_coefficient": None,
                "preload_credit": False,
            },
            "clearance_by_diameter_mm": clearance_by_diameter_mm,
        })

    # Broad host surfaces remain broad. Their finite common footprints are the
    # opposing cleat face or washer face, not the host surface's full area.
    for index, interface_id in enumerate(EXPECTED_INTERFACE_IDS, start=1):
        info = classified_wood[interface_id]
        row = info["row"]
        candidate = str(row["candidate_member_id"])
        host = str(row["host_member_id"])
        source_face = info["candidate_tags"]
        host_face = info["host_tags"]
        candidate_normal = interfaces[interface_id]["candidate_cleat_face"]["plane_normal_global_xyz"]
        host_normal = interfaces[interface_id]["source_host_face"]["normal_global_xyz"]
        if _dot(_unit(candidate_normal, "candidate face datum normal"), _unit(host_normal, "host face datum normal")) > -FACE_NORMAL_TOLERANCE:
            raise ValueError(f"{interface_id}: pinned face datums are not opposed")
        append_pair(
            pair_id=f"{interface_id}::wood_to_wood",
            category="wood_wood_interface",
            interface_id=interface_id,
            slave_mesh=wood,
            slave_owner=candidate,
            slave_tags=source_face,
            slave_refs=info["candidate_refs"],
            slave_role="finite cleat face",
            master_mesh=wood,
            master_owner=host,
            master_tags=host_face,
            master_refs=info["host_refs"],
            master_role="host face containing finite cleat footprint",
            common_area_mm2=info["finite_common_area_mm2"],
            initial_state_assumption="nominal_zero_gap_geometry_setup; no tie, gap adjustment, preload or active-pressure claim",
        )

    # Map each bolt/bore patch to its own receiver interval. Metal shaft faces
    # are station-partitioned so the same physical TRI6 face is not assigned to
    # both wood receivers at an interface.
    for bore in sorted(bore_rows, key=lambda row: str(row["stack_spec_id"])):
        stack_id = str(bore["stack_spec_id"])
        owner = str(bore["member_id"])
        bolt_body = f"{stack_id}__bolt"
        origin = _finite_vector(bore["axis_origin_xyz_mm"], 3, f"{stack_id} bore datum")
        axis = _unit(bore["axis_direction_head_to_nut"], f"{stack_id} bore axis")
        low, high = _finite_vector(bore["receiver_layer_station_mm"], 2, f"{stack_id} receiver interval")
        tags = tuple(
            tag
            for role in ("bolt_smooth_shank_cylindrical_surface", "bolt_root_sensitivity_cylindrical_surface")
            for tag in _metal_tags_for_role(metal, bolt_body, role)
        )
        bolt_refs, bolt_tags, bolt_face_audit = _select_axial_faces(
            metal, bolt_body, tags, origin, axis, low, high
        )
        bore_refs = bore["_resolved_member_refs"]
        bore_tags = bore["_resolved_member_tags"]
        bore_radius = float(bore["analysis_occupancy_bore_radius_mm"])
        smooth_radius = float(hardware_inventory["selected_hardware_geometry"]["bolt"]["smooth_body_diameter_mm"]) / 2
        root_radius = float(hardware_inventory["thread_and_gage_mapping"]["root_sensitivity_diameter_mm"]) / 2
        min_metal_radial, _ = _radial_alignment(metal, bolt_body, bolt_refs, origin, axis)
        min_wood_radial, _ = _radial_alignment(wood, owner, bore_refs, origin, axis)
        # A bolt's outward normal points away from its axis; a hole wall's
        # outward normal points into the empty bore and therefore toward axis.
        if min_metal_radial < RADIAL_NORMAL_TOLERANCE or min_wood_radial > -RADIAL_NORMAL_TOLERANCE:
            raise ValueError(f"{stack_id}/{owner}: shaft/bore outward normals have incompatible ownership")
        clearance_values = {
            "smooth_body_radial_clearance_mm": bore_radius - smooth_radius,
            "root_sensitivity_radial_clearance_mm": bore_radius - root_radius,
        }
        if any(value <= 0 for value in clearance_values.values()):
            raise ValueError(f"{stack_id}/{owner}: pinned shaft/bore geometry has no positive radial clearance")
        append_pair(
            pair_id=f"{stack_id}::{owner}::bolt_bore",
            category="bolt_shank_to_receiver_bore",
            interface_id=str(bore["interface_id"]),
            slave_mesh=metal,
            slave_owner=bolt_body,
            slave_tags=bolt_tags,
            slave_refs=bolt_refs,
            slave_role="axially clipped bolt cylinder (smooth/root profile surfaces)",
            slave_axial_face_selection_audit=bolt_face_audit,
            master_mesh=wood,
            master_owner=owner,
            master_tags=bore_tags,
            master_refs=bore_refs,
            master_role="authenticated receiver bore wall; analysis occupancy only",
            common_area_mm2=None,
            initial_state_assumption="open_radial_geometry_clearance; exact profile radii retained; no clearance closure",
            normal_mode="opposed_radial",
            radial_origin_xyz_mm=origin,
            radial_axis=axis,
            expected_radial_signs=(1, -1),
            clearance_by_diameter_mm=clearance_values,
        )

    # Every physical surface seat stays separate and unilateral. The wood seat
    # side is found from the recorded finished-face point and bolt axis.
    hardware_geometry = hardware_inventory["selected_hardware_geometry"]
    washer_geometry = hardware_geometry["each_of_two_washers_per_bolt"]
    washer_bore_radius = float(washer_geometry["inside_diameter_mm"]) / 2
    for stack_id in STACK_IDS:
        stack = stacks[stack_id]
        axis_origin = _finite_vector(stack["underhead_origin_global_xyz_mm"], 3, f"{stack_id} underhead origin")
        axis = _unit(stack["world_axis_direction_head_to_nut"], f"{stack_id} bolt axis")
        wood_axis_origin = _finite_vector(stack["wood_head_face_center_global_xyz_mm"], 3, f"{stack_id} first wood face")
        head_receiver = stack["receivers_head_to_nut"][0]["member_id"]
        far_receiver = stack["receivers_head_to_nut"][1]["member_id"]
        bolt_body = f"{stack_id}__bolt"
        head_washer_body = f"{stack_id}__head_washer"
        nut_washer_body = f"{stack_id}__nut_washer"
        nut_body = f"{stack_id}__nut"
        audit_row = seat_audit_by_key[(profile, stack_id)]

        def metal_role_refs(body_id: str, role: str) -> tuple[tuple[str, ...], tuple[tuple[int, int], ...]]:
            role_tags = _metal_tags_for_role(metal, body_id, role)
            return role_tags, _surface_refs(metal, body_id, role_tags)

        def add_seat(
            seat_key: str,
            pair_suffix: str,
            slave_mesh: MeshInput,
            slave_owner: str,
            slave_tags: Iterable[str | int],
            slave_refs: Iterable[tuple[int, int]],
            slave_role: str,
            master_mesh: MeshInput,
            master_owner: str,
            master_tags: Iterable[str | int],
            master_refs: Iterable[tuple[int, int]],
            master_role: str,
            *,
            bound_stack_id: str = stack_id,
            bound_stack: dict[str, Any] = stack,
            bound_audit_row: dict[str, Any] = audit_row,
        ) -> None:
            seat = bound_audit_row["seat_pairs"][seat_key]
            append_pair(
                pair_id=f"{bound_stack_id}::{pair_suffix}",
                category="hardware_surface_seat",
                interface_id=str(bound_stack["interface_id"]),
                slave_mesh=slave_mesh,
                slave_owner=slave_owner,
                slave_tags=slave_tags,
                slave_refs=slave_refs,
                slave_role=slave_role,
                master_mesh=master_mesh,
                master_owner=master_owner,
                master_tags=master_tags,
                master_refs=master_refs,
                master_role=master_role,
                common_area_mm2=float(seat["finite_common_area_mm2"]),
                initial_state_assumption=(
                    "nominal_zero_gap_seat_geometry; audited finite opposed common faces; "
                    "measured roundoff retained with no tie, adjustment or preload"
                ),
            )

        bolt_tags, bolt_refs = metal_role_refs(bolt_body, "bolt_head_washer_bearing_face")
        hw_tags, hw_refs = metal_role_refs(head_washer_body, "head_washer_bolt_bearing_face")
        add_seat("head_to_head_washer", "bolt_head_to_head_washer", metal, bolt_body, bolt_tags, bolt_refs,
                 "bolt head underface", metal, head_washer_body, hw_tags, hw_refs, "head washer bearing face")

        hw_seat_tags, hw_seat_refs = metal_role_refs(head_washer_body, "head_washer_wood_seat_face")
        head_wood_tags = _wood_plane_tags_at(wood, head_receiver, wood_axis_origin, axis)
        head_wood_refs = _surface_refs(wood, head_receiver, head_wood_tags)
        add_seat("head_washer_to_wood", "head_washer_to_wood", metal, head_washer_body, hw_seat_tags, hw_seat_refs,
                 "head washer annular wood seat", wood, head_receiver, head_wood_tags, head_wood_refs,
                 "outer face of head-side wood receiver")

        nw_wood_tags, nw_wood_refs = metal_role_refs(nut_washer_body, "nut_washer_wood_seat_face")
        far_wood_point = _finite_vector(stack["wood_far_face_center_global_xyz_mm"], 3, f"{stack_id} far wood face")
        far_wood_tags = _wood_plane_tags_at(wood, far_receiver, far_wood_point, axis)
        far_wood_refs = _surface_refs(wood, far_receiver, far_wood_tags)
        add_seat("wood_to_nut_washer", "wood_to_nut_washer", metal, nut_washer_body, nw_wood_tags, nw_wood_refs,
                 "nut washer annular wood seat", wood, far_receiver, far_wood_tags, far_wood_refs,
                 "outer face of nut-side wood receiver")

        nw_nut_tags, nw_nut_refs = metal_role_refs(nut_washer_body, "nut_washer_nut_bearing_face")
        nut_bearing_tags, nut_bearing_refs = metal_role_refs(nut_body, "nut_washer_bearing_face")
        add_seat("nut_washer_to_nut", "nut_washer_to_nut", metal, nut_body, nut_bearing_tags, nut_bearing_refs,
                 "nut washer bearing face", metal, nut_washer_body, nw_nut_tags, nw_nut_refs,
                 "nut washer bearing face")

        # Add finite radial contact for annular washer bores. Station clipping
        # prevents the same continuous bolt TRI6 face from entering both seats.
        bolt_cylinder_tags = tuple(
            tag
            for role in ("bolt_smooth_shank_cylindrical_surface", "bolt_root_sensitivity_cylindrical_surface")
            for tag in _metal_tags_for_role(metal, bolt_body, role)
        )
        # The selected head washer bearing plane is the underhead datum; its
        # wood seat plane provides the actual thickness, avoiding a catalog guess.
        head_washer_interval = (0.0, float(washer_geometry["thickness_mm"]))
        head_bolt_refs, head_bolt_tags, head_bolt_audit = _select_axial_faces(
            metal, bolt_body, bolt_cylinder_tags, axis_origin, axis,
            head_washer_interval[0], head_washer_interval[1],
        )
        head_bore_tags, head_bore_refs = metal_role_refs(head_washer_body, "washer_bore_cylindrical_surface")
        head_body_diameter = float(hardware_geometry["bolt"]["smooth_body_diameter_mm"])
        head_washer_clearance = washer_bore_radius - head_body_diameter / 2
        if head_washer_clearance <= 0:
            raise ValueError(f"{stack_id}: washer bore does not retain positive nominal radial clearance")
        append_pair(
            pair_id=f"{stack_id}::bolt_to_head_washer_bore",
            category="bolt_to_washer_bore",
            interface_id=str(stack["interface_id"]),
            slave_mesh=metal, slave_owner=bolt_body, slave_tags=head_bolt_tags, slave_refs=head_bolt_refs,
            slave_role="bolt cylinder clipped to head washer thickness",
            slave_axial_face_selection_audit=head_bolt_audit,
            master_mesh=metal, master_owner=head_washer_body, master_tags=head_bore_tags, master_refs=head_bore_refs,
            master_role="head washer finite bore wall",
            common_area_mm2=None,
            initial_state_assumption="open_radial_hardware_clearance; no forced fit or adjustment",
            normal_mode="opposed_radial", radial_origin_xyz_mm=axis_origin, radial_axis=axis,
            expected_radial_signs=(1, -1),
            clearance_by_diameter_mm={"smooth_body_radial_clearance_mm": head_washer_clearance},
        )

        nut_washer_start = float(stack["nut_washer_start_station_from_underhead_mm"])
        nut_washer_end = nut_washer_start + float(washer_geometry["thickness_mm"])
        nut_bolt_refs, nut_bolt_tags, nut_bolt_audit = _select_axial_faces(
            metal, bolt_body, bolt_cylinder_tags, axis_origin, axis, nut_washer_start, nut_washer_end,
        )
        nut_bore_tags, nut_bore_refs = metal_role_refs(nut_washer_body, "washer_bore_cylindrical_surface")
        max_profile_radius = max(
            float(hardware_geometry["bolt"]["smooth_body_diameter_mm"]) / 2,
            float(hardware_inventory["thread_and_gage_mapping"]["root_sensitivity_diameter_mm"]) / 2,
        )
        nut_washer_clearance = washer_bore_radius - max_profile_radius
        if nut_washer_clearance <= 0:
            raise ValueError(f"{stack_id}: selected root/body profile intersects a washer bore")
        append_pair(
            pair_id=f"{stack_id}::bolt_to_nut_washer_bore",
            category="bolt_to_washer_bore",
            interface_id=str(stack["interface_id"]),
            slave_mesh=metal, slave_owner=bolt_body, slave_tags=nut_bolt_tags, slave_refs=nut_bolt_refs,
            slave_role="bolt cylinder clipped to nut washer thickness",
            slave_axial_face_selection_audit=nut_bolt_audit,
            master_mesh=metal, master_owner=nut_washer_body, master_tags=nut_bore_tags, master_refs=nut_bore_refs,
            master_role="nut washer finite bore wall",
            common_area_mm2=None,
            initial_state_assumption="open_radial_hardware_clearance; no forced fit or adjustment",
            normal_mode="opposed_radial", radial_origin_xyz_mm=axis_origin, radial_axis=axis,
            expected_radial_signs=(1, -1),
            clearance_by_diameter_mm={"largest_profile_radial_clearance_mm": nut_washer_clearance},
        )

        # The cylindrical root/nut pair models radial nonpenetration only. It
        # does not resolve the helical thread, flank engagement, or axial force.
        root_tags = _metal_tags_for_role(metal, bolt_body, "bolt_root_sensitivity_cylindrical_surface")
        nut_start = float(stack["nut_start_station_from_underhead_mm"])
        nut_end = float(stack["nut_end_station_from_underhead_mm"])
        root_nut_refs, root_nut_tags, root_nut_audit = _select_axial_faces(
            metal, bolt_body, root_tags, axis_origin, axis, nut_start, nut_end,
        )
        nut_bore_tags, nut_bore_refs = metal_role_refs(nut_body, "nut_basic_reference_bore_cylindrical_surface")
        nut_bore_radius = float(hardware_geometry["nut"]["smooth_basic_reference_bore_mm"]) / 2
        root_diameter = float(hardware_inventory["thread_and_gage_mapping"]["root_sensitivity_diameter_mm"])
        nut_root_clearance = nut_bore_radius - root_diameter / 2
        if nut_root_clearance <= 0:
            raise ValueError(f"{stack_id}: projected root sensitivity intersects the nut reference bore")
        append_pair(
            pair_id=f"{stack_id}::projected_root_to_nut_bore_radial_contact",
            category="projected_thread_radial_contact_only",
            interface_id=str(stack["interface_id"]),
            slave_mesh=metal, slave_owner=bolt_body, slave_tags=root_nut_tags, slave_refs=root_nut_refs,
            slave_role="named root sensitivity cylinder through nut thickness",
            slave_axial_face_selection_audit=root_nut_audit,
            master_mesh=metal, master_owner=nut_body, master_tags=nut_bore_tags, master_refs=nut_bore_refs,
            master_role="hollow nut basic-reference cylindrical bore",
            common_area_mm2=None,
            initial_state_assumption=(
                "open_radial_basic_reference_gap; radial nonpenetration only; no thread flank, "
                "axial engagement, thread resistance, or delivered-thread claim"
            ),
            normal_mode="opposed_radial", radial_origin_xyz_mm=axis_origin, radial_axis=axis,
            expected_radial_signs=(1, -1),
            clearance_by_diameter_mm={"root_to_nut_radial_reference_gap_mm": nut_root_clearance},
        )

    if len(pair_rows) != 76:
        raise ValueError(f"expected 76 owned contact pairs, got {len(pair_rows)}")
    pair_ids = [row["pair_id"] for row in pair_rows]
    if len(pair_ids) != len(set(pair_ids)):
        raise ValueError("contact pair IDs must be unique")
    return pair_rows


def _render_contact_cards(pairs: list[dict[str, Any]], penalty_n_per_mm3: float) -> list[str]:
    penalty = _positive_finite(penalty_n_per_mm3, "numerical contact penalty")
    lines = [
        "** Contact fragment only: no material, restraint, load, engagement tie, or step cards",
        "*SURFACE INTERACTION,NAME=WJ04_NUMERICAL_CONTACT",
        "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR",
        f"{penalty:.15g}",
    ]
    emitted: set[str] = set()
    for pair in pairs:
        for side_name in ("slave", "master"):
            side = pair[side_name]
            surface_name = side["surface_name"]
            if surface_name in emitted:
                continue
            emitted.add(surface_name)
            lines.extend(_format_id_set(
                side["node_set_name"], side["remapped_face_node_ids"], card="NSET"
            ))
            lines.append(f"*SURFACE,NAME={surface_name},TYPE=ELEMENT")
            lines.extend(f"{element},S{face}" for element, face in side["remapped_face_refs"])
    for pair in pairs:
        lines.extend([
            "*CONTACT PAIR,INTERACTION=WJ04_NUMERICAL_CONTACT,TYPE=SURFACE TO SURFACE",
            f"{pair['slave']['surface_name']},{pair['master']['surface_name']}",
        ])
    return lines


def prepare_contact_fragment(
    wood_mesh_report_path: str | Path,
    wood_mesh_deck_path: str | Path,
    classification_path: str | Path,
    wood_normal_audit_path: str | Path,
    metal_mesh_report_path: str | Path,
    metal_mesh_deck_path: str | Path,
    mechanics_inputs_path: str | Path,
    hardware_inventory_path: str | Path,
    seat_audit_path: str | Path,
    *,
    penalty_n_per_mm3: float,
    wood_patch_inventory_path: str | Path,
) -> tuple[str, dict[str, Any]]:
    """Validate frozen inputs and return a non-runnable mesh/contact deck fragment."""
    penalty = _positive_finite(penalty_n_per_mm3, "numerical contact penalty")
    wood = _read_mesh_input("wood", wood_mesh_report_path, wood_mesh_deck_path)
    metal = _read_mesh_input("metal", metal_mesh_report_path, metal_mesh_deck_path)
    classification, classification_bytes = _load_json(classification_path, "surface classification")
    normal_audit, _normal_bytes = _load_json(wood_normal_audit_path, "wood normal audit")
    mechanics, mechanics_bytes = _load_json(mechanics_inputs_path, "mechanics input")
    hardware_inventory, hardware_bytes = _load_json(hardware_inventory_path, "hardware inventory")
    seat_audit, _seat_bytes = _load_json(seat_audit_path, "hardware seat audit")
    patch_inventory, patch_inventory_bytes = _load_json(wood_patch_inventory_path, "wood patch inventory")
    classification_sha = sha256_bytes(classification_bytes)
    mechanics_sha = sha256_bytes(mechanics_bytes)
    patch_inventory_sha = sha256_bytes(patch_inventory_bytes)
    normal_rows = _validate_normal_audit(normal_audit, classification_sha, wood)
    if mechanics.get("schema") != MECHANICS_INPUTS_SCHEMA or mechanics.get("status") != "bounded_mechanics_inputs_only":
        raise ValueError("mechanics input is not the bounded WJ04 full-stock source contract")
    inventory_sha = sha256_bytes(hardware_bytes)
    hardware_sources = hardware_inventory.get("source_inputs", {}).get("sha256", {})
    if hardware_sources.get("patch_inventory.json") != wood.report.get("input_bundle_inventory_sha256"):
        raise ValueError("wood mesh and hardware profile do not share the same frozen five-body bundle")
    if hardware_sources.get("mechanics_inputs.json") != mechanics_sha:
        raise ValueError("hardware profile and mechanics-input report are not source-bound")
    if metal.report.get("wood_mesh_bundle_sha256") != wood.report.get("input_bundle_inventory_sha256"):
        raise ValueError("metal mesh and wood mesh are not bound to the same five-body source bundle")
    # Pass exact raw inventory digest through a private attribute-free view so
    # all consumers compare the source bytes, not a reserialization.
    stacks, seat_audit_by_key = _validate_hardware_inventory_with_sha(
        hardware_inventory, inventory_sha, metal, seat_audit
    )
    _validate_hardware_stack_mechanics_binding(stacks, mechanics)
    classified_wood, bore_rows = _validate_surface_classification(
        classification,
        classification_sha,
        wood,
        normal_rows,
        mechanics,
        mechanics_sha,
        patch_inventory,
        patch_inventory_sha,
    )
    merged = _merge_meshes(wood, metal)
    contact_pairs = _build_contact_pairs(
        wood,
        metal,
        classification,
        classified_wood,
        bore_rows,
        mechanics,
        hardware_inventory,
        stacks,
        seat_audit_by_key,
        merged,
    )
    response_readiness = _response_readiness(contact_pairs)
    lines = _render_mesh_cards(merged)
    lines.extend(_render_contact_cards(contact_pairs, penalty))
    fragment = "\n".join(lines) + "\n"
    interface_owners = {
        row["interface_id"]: {
            "ordered_members_head_to_nut": list(row["members_head_to_nut"]),
            "source_datum_origin_global_xyz_mm": list(row["shear_plane_datum"]["origin_global_xyz_mm"]),
            "source_datum_normal_head_to_nut_global_xyz": list(row["shear_plane_datum"]["normal_head_to_nut_global_xyz"]),
        }
        for row in mechanics["physical_interfaces"]
    }
    wood_contact_footprints = {}
    for pair in contact_pairs:
        if pair["category"] != "wood_wood_interface":
            continue
        interface_id = str(pair["interface_id"])
        wood_contact_footprints[interface_id] = {
            "pair_id": pair["pair_id"],
            "ordered_members_head_to_nut": interface_owners[interface_id]["ordered_members_head_to_nut"],
            "finite_common_area_mm2": pair["finite_common_area_mm2"],
            "candidate_cleat_contact_side": pair["slave"],
            "host_contact_side": pair["master"],
            "host_surface_clipped_to_common_footprint": False,
            "host_clip_and_tributary_area_resolver": "required before nodal wrench distribution",
        }
    profile = metal.report["scenario_id"]
    thread = hardware_inventory["thread_and_gage_mapping"]
    engagement = {
        "scenario_id": profile,
        "thread_transition_observed": thread.get("thread_transition_observed"),
        "physical_thread_profile_or_engagement_verified": False,
        "full_form_thread_or_runout_modeled": thread.get("full_form_thread_or_runout_modeled"),
        "helical_profile_modeled": thread.get("helical_profile_modeled"),
        "Lb_mm_from_underhead": thread.get("Lb_mm_from_underhead"),
        "Lb_semantics": thread.get("Lb_semantics"),
        "Lg_mm_from_underhead": thread.get("Lg_mm_from_underhead"),
        "Lg_semantics": thread.get("Lg_semantics"),
        "root_nut_model": "frictionless radial cylinder contact only; no axial thread engagement is modeled",
        "nut_full_thickness_engagement": "assumed geometric overlap in the exported profile; not verified delivered engagement",
        "open_gate": "a supported axial bolt-to-nut engagement law is required before a runnable structural deck",
    }
    inputs = {
        "wood_mesh_report_sha256": wood.report_sha256,
        "wood_mesh_deck_sha256": wood.deck_sha256,
        "surface_classification_sha256": classification_sha,
        "wood_normal_audit_sha256": sha256_file(wood_normal_audit_path),
        "mechanics_inputs_sha256": sha256_bytes(mechanics_bytes),
        "wood_patch_inventory_sha256": patch_inventory_sha,
        "hardware_inventory_sha256": inventory_sha,
        "hardware_seat_audit_sha256": sha256_file(seat_audit_path),
        "metal_mesh_report_sha256": metal.report_sha256,
        "metal_mesh_deck_sha256": metal.deck_sha256,
    }
    open_readiness_items = [
        "both wood radial/tangential material orientation cases",
        "a sourced steel material scenario",
        "remote 3-2-1 gauge constraints and restraint sensitivity",
        "case-specific signed unit wrenches and action accounting",
        "supported axial bolt-to-nut engagement behavior",
        "contact-penalty, gap, mesh and response convergence sensitivities",
        "free-mode, stabilization reaction and energy audit",
    ]
    if not response_readiness["axial_contact_patch_coverage_ready"]:
        open_readiness_items.append(
            "resolve station-straddling axial contact faces with an explicit clipped-area method"
        )
    manifest = {
        "schema": SCHEMA,
        "status": "CONTACT_FRAGMENT_PREPARED_NO_SOLVER",
        "accepted": False,
        "solved": False,
        "capacity_or_release_claim": False,
        "candidate": "compact-floor-flush-wood-joints-development",
        "representative_family": "WJ16 right-inner full-stock G7 five-body ordinary joint",
        "hardware_profile": profile,
        "claim_boundary": LIMITS,
        "response_readiness": response_readiness,
        "model_completion": {
            "complete_runnable_model": False,
            "materials_bound": False,
            "restraints_bound": False,
            "unit_wrench_cases_bound": False,
            "axial_bolt_to_nut_engagement_bound": False,
            "solver_step_or_solve_run": False,
            "response_ready": response_readiness["response_ready"],
            "axial_contact_patch_coverage_ready": response_readiness[
                "axial_contact_patch_coverage_ready"
            ],
            "open_readiness_items": open_readiness_items,
        },
        "contact_law": {
            "normal_behavior": "unilateral compression-only",
            "opening": "allowed",
            "tension": "not transmitted",
            "tangential_behavior": "frictionless",
            "preload_n": 0.0,
            "preload_credit": False,
            "deck_card": "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR",
            "penalty_n_per_mm3": penalty,
            "penalty_interpretation": PENALTY_DESCRIPTION,
        },
        "surface_ownership": {
            "five_independent_wood_bodies": list(WOOD_BODY_IDS),
            "32_independent_physical_steel_bodies": list(EXPECTED_METAL_BODY_IDS),
            "unique_physical_bolts": 8,
            "legacy_collision_roles_meshed": 0,
            "independent_mesh_node_sharing": 0,
            "contact_faces_reference_owner_body_and_source_mesh": True,
            "transient_cad_tags_used_only_as_local_mesh_report_pointers": True,
            "body_inventory": merged["body_inventory"],
            "physical_interface_owners": interface_owners,
            "wood_contact_footprints": wood_contact_footprints,
        },
        "contact_pair_count": len(contact_pairs),
        "contact_pairs": contact_pairs,
        "contact_assignment_scope": {
            "assigned_pair_categories": {
                category: sum(pair["category"] == category for pair in contact_pairs)
                for category in sorted({pair["category"] for pair in contact_pairs})
            },
            "all_unlisted_body_surface_pairs": "not assigned contact; no all-to-all or generic body contact",
            "intentionally_omitted": [
                "axial bolt-to-nut thread flank engagement or equivalent axial connector law",
                "thread pitch, helix, flank compliance, friction, torque transfer, and axial resistance",
                "frictional or bonded wood/wood, wood/washer, washer/bolt, washer/nut, or bolt/bore transfer",
                "nut/wood direct contact and washer outer-edge or other unlisted edge/shoulder contact",
                "bolt-head or nut side contacts and cross-contact between distinct physical bolt stacks",
                "any wood/wood contact outside the four named cleat-to-host face pairs",
            ],
        },
        "engagement_assumptions": engagement,
        "free_mode_and_initial_state_audit": {
            "initial_state": "zero preload with all declared geometric clearances retained; unilateral contacts may be open",
            "solver_derived_global_free_mode_count": None,
            "global_free_mode_count_status": "not assessed; depends on case restraints and the active contact set",
            "known_unrestrained_or_clearance_dependent_modes": [
                "axial bolt/stack motion relative to the nut is not restrained because no axial thread engagement law is assigned",
                "frictionless contacts transmit no tangential force or torque; relative sliding and washer/nut spin remain possible",
                "bolt and annular washer translations can occur within open diametral clearances before a bore contact closes",
                "separated members can open without preload or tensile contact transfer",
                "the projected root-to-nut cylinder pair constrains only radial penetration after closure and cannot carry axial load",
            ],
            "zero_work_spin_gauge_candidate": "axisymmetric bolt/washer/nut spin may be a zero-work gauge only after a separate rank audit; no restraint is emitted here",
            "first_case_readiness": [
                "perform a zero-load gauge-only preflight after material, engagement, and restraint contracts are ready",
                "do not start the unit-wrench sweep until the explicit assumed-active-set rank audit dispositions internal free modes",
                "if a loaded force-controlled case is singular, retain that result; any later prescribed-displacement seating trial is a separately named seated-state diagnostic with displacement, reaction, and work recorded",
                "a seated-state diagnostic is not unloaded initial stiffness, physical preload, or a basis for silently adding stabilization, ties, or clamps",
            ],
        },
        "numerical_and_evidence_limits": [
            "No face is tied or adjusted to close a gap.",
            "Finite nominal wood overlap is the archived cleat face common area; the full host-face area is not credited as contact footprint.",
            "The wood contact pair exports the broad host plane as its master surface; an exact host clip and tributary-area map remain required before case load distribution.",
            "Wood/washer face seats use audited nominal zero-gap geometry with measured CAD roundoff retained.",
            "Wood bore clearance uses an analysis occupancy cylinder, not a drill or hardware instruction.",
            "Metal bore, washer-bore and nut-bore initial clearances remain open in geometry and are not force-closed.",
            "The projected root-to-nut cylinder contact transmits radial normal pressure only; it does not model threads or axial engagement.",
            "A penalty parameter is numerical enforcement only. No contact stiffness, pressure response, resistance, or capacity is established.",
            "The deck fragment has no material, restraint, load, step, or solver execution cards and must not be submitted as a complete model.",
        ],
        "source_hashes": inputs,
        "body_counts": {
            "nodes": len(merged["nodes"]),
            "c3d10_elements": len(merged["elements"]),
            "wood_bodies": len(WOOD_BODY_IDS),
            "metal_bodies": len(EXPECTED_METAL_BODY_IDS),
        },
        "deck_fragment_sha256": sha256_bytes(fragment.encode("utf-8")),
    }
    return fragment, manifest


def _validate_hardware_inventory_with_sha(
    inventory: dict[str, Any],
    inventory_sha256: str,
    metal_mesh: MeshInput,
    seat_audit: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    # Kept separate from the public validator to make raw-file hash binding
    # explicit instead of hashing a Python reserialization.
    if metal_mesh.report.get("input_bundle_inventory_sha256") != inventory_sha256:
        raise ValueError("hardware mesh and supplied inventory bytes are not source-bound")
    if seat_audit.get("hardware_inventory_sha256") != inventory_sha256:
        raise ValueError("seat audit and supplied hardware inventory bytes are not source-bound")
    return _validate_hardware_inventory_body(inventory, inventory_sha256, metal_mesh, seat_audit)


def _validate_hardware_stack_mechanics_binding(
    stacks: dict[str, dict[str, Any]], mechanics: dict[str, Any]
) -> None:
    bolt_rows = mechanics.get("physical_bolts")
    if not isinstance(bolt_rows, list) or len(bolt_rows) != len(STACK_IDS):
        raise ValueError("mechanics input must contain the exact eight bolt identities")
    bolt_ids = [row.get("stack_spec_id") for row in bolt_rows if isinstance(row, dict)]
    if len(bolt_ids) != len(bolt_rows) or len(set(bolt_ids)) != len(STACK_IDS) or set(bolt_ids) != set(STACK_IDS):
        raise ValueError("mechanics bolt identities must be unique and complete")
    mechanics_by_stack = {row["stack_spec_id"]: row for row in bolt_rows}
    interfaces = mechanics.get("physical_interfaces")
    if not isinstance(interfaces, list) or len(interfaces) != len(EXPECTED_INTERFACE_IDS):
        raise ValueError("mechanics input must contain the exact four interface identities")
    interface_ids = [row.get("interface_id") for row in interfaces if isinstance(row, dict)]
    if len(interface_ids) != len(interfaces) or len(set(interface_ids)) != len(EXPECTED_INTERFACE_IDS) or set(interface_ids) != set(EXPECTED_INTERFACE_IDS):
        raise ValueError("mechanics interface identities must be unique and complete")
    interfaces_by_id = {row["interface_id"]: row for row in interfaces}
    if set(stacks) != set(STACK_IDS):
        raise ValueError("hardware stack identity set differs from the eight mechanics bolts")

    def vector_equal(first: Any, second: Any, context: str, *, tolerance: float = 1e-7) -> None:
        a = _finite_vector(first, 3, f"{context} first vector")
        b = _finite_vector(second, 3, f"{context} second vector")
        if _norm(_sub(a, b)) > tolerance:
            raise ValueError(f"{context}: source-bound XYZ values differ")

    for stack_id in STACK_IDS:
        stack = stacks[stack_id]
        bolt = mechanics_by_stack[stack_id]
        expected_interface = next(
            key for key, stack_ids in wood_mesh_contract.EXPECTED_INTERFACE_STACKS.items()
            if stack_id in stack_ids
        )
        interface = interfaces_by_id[expected_interface]
        if stack.get("physical_bolt_id") != bolt.get("physical_bolt_id"):
            raise ValueError(f"{stack_id}: hardware stack and mechanics physical bolt IDs differ")
        if stack.get("interface_id") != expected_interface:
            raise ValueError(f"{stack_id}: hardware stack is assigned to the wrong full interface")
        if stack_id not in interface.get("family_stack_ids", ()):
            raise ValueError(f"{stack_id}: hardware stack is absent from its mechanics interface family")
        if stack.get("receivers_head_to_nut") != bolt.get("receivers_head_to_nut"):
            raise ValueError(f"{stack_id}: hardware and mechanics ordered receiver identities differ")
        if stack.get("wood_grip_mm") != bolt.get("wood_grip_mm"):
            raise ValueError(f"{stack_id}: hardware and mechanics wood grip differs")
        if stack.get("world_axis_direction_head_to_nut") != bolt.get("world_axis_direction_head_to_nut"):
            raise ValueError(f"{stack_id}: hardware and mechanics bolt axis differs")
        vector_equal(
            stack.get("wood_head_face_center_global_xyz_mm"),
            bolt.get("world_axis_origin_xyz_mm"),
            f"{stack_id} first wood face datum",
        )
        vector_equal(
            stack.get("underhead_origin_global_xyz_mm"),
            bolt.get("modeled_bolt_under_head_origin_xyz_mm"),
            f"{stack_id} underhead datum",
        )
        receivers = bolt.get("receivers_head_to_nut")
        if not isinstance(receivers, list) or len(receivers) != 2:
            raise ValueError(f"{stack_id}: mechanics receiver identity must have exactly two layers")
        thickness = math.fsum(_positive_finite(row.get("wood_thickness_mm"), f"{stack_id} receiver thickness") for row in receivers)
        if abs(thickness - _positive_finite(bolt.get("wood_grip_mm"), f"{stack_id} wood grip")) > 1e-7:
            raise ValueError(f"{stack_id}: ordered receiver thicknesses do not equal the declared grip")
        receiver_ids = _validate_ordered_receiver_ownership(stack_id, bolt, interface)
        axis = _unit(bolt.get("world_axis_direction_head_to_nut"), f"{stack_id} mechanics axis")
        expected_far_face = tuple(
            start + thickness * component
            for start, component in zip(bolt["world_axis_origin_xyz_mm"], axis, strict=True)
        )
        vector_equal(
            stack.get("wood_far_face_center_global_xyz_mm"),
            expected_far_face,
            f"{stack_id} far wood face datum",
            tolerance=1e-5,
        )
        if receiver_ids != tuple(interface["members_head_to_nut"]):
            raise ValueError(f"{stack_id}: ordered receivers differ from the mechanics interface member order")


def _validate_ordered_receiver_ownership(
    stack_id: str,
    bolt: dict[str, Any],
    interface: dict[str, Any],
) -> tuple[str, str]:
    """Bind one stack's ordered receivers to its frozen WJ04 interface pair."""
    expected = wood_mesh_contract.STACK_RECEIVERS.get(stack_id)
    if expected is None:
        raise ValueError(f"{stack_id}: no frozen receiver mapping exists")
    receivers = bolt.get("receivers_head_to_nut")
    if not isinstance(receivers, list) or len(receivers) != 2 or any(
        not isinstance(row, dict) for row in receivers
    ):
        raise ValueError(f"{stack_id}: mechanics receiver order must contain exactly two member records")
    receiver_ids = tuple(row.get("member_id") for row in receivers)
    if receiver_ids != tuple(expected):
        raise ValueError(f"{stack_id}: ordered mechanics receivers differ from the frozen physical receiver mapping")
    interface_members = interface.get("members_head_to_nut")
    if not isinstance(interface_members, list) or len(interface_members) != 2 or len(set(interface_members)) != 2:
        raise ValueError(f"{stack_id}: mechanics interface must contain exactly two unique ordered members")
    if tuple(interface_members) != receiver_ids:
        raise ValueError(f"{stack_id}: ordered mechanics receivers differ from the mechanics interface member order")
    return receiver_ids  # type: ignore[return-value]


def _validate_hardware_inventory_body(
    inventory: dict[str, Any],
    inventory_sha256: str,
    metal_mesh: MeshInput,
    seat_audit: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    if inventory.get("schema") != HARDWARE_SCHEMA or inventory.get("status") != "conditional_response_hardware_geometry_only":
        raise ValueError("hardware inventory is not the frozen conditional WJ04 profile export")
    profile = metal_mesh.report.get("scenario_id")
    scenario_rows = inventory.get("scenarios")
    if not isinstance(scenario_rows, list) or len(scenario_rows) != len(metal_mesh_contract.SCENARIO_IDS):
        raise ValueError("hardware inventory must carry each named profile exactly once")
    scenario_ids = [row.get("scenario_id") for row in scenario_rows if isinstance(row, dict)]
    if len(scenario_ids) != len(scenario_rows) or len(set(scenario_ids)) != len(metal_mesh_contract.SCENARIO_IDS) or set(scenario_ids) != set(metal_mesh_contract.SCENARIO_IDS):
        raise ValueError("hardware inventory profile IDs must be unique and complete")
    scenarios = {row["scenario_id"]: row for row in scenario_rows}
    if profile not in metal_mesh_contract.SCENARIO_IDS or profile not in scenarios:
        raise ValueError("hardware mesh must contain one of the two named WJ04 profiles")
    if metal_mesh.report.get("physical_mesh_scope", {}).get("selected_profile") != profile or metal_mesh.report.get("physical_mesh_scope", {}).get("other_profile_included") is not False:
        raise ValueError("hardware mesh profile is mixed or inconsistently identified")
    if seat_audit.get("hardware_inventory_sha256") != inventory_sha256:
        raise ValueError("seat audit is not bound to exact hardware inventory bytes")
    if seat_audit.get("all_64_named_seat_pairs_have_finite_opposed_common_faces") is not True:
        raise ValueError("finite opposed hardware seat evidence is incomplete")
    if seat_audit.get("contact_pressure_or_strength_established") is not False or seat_audit.get("native_solve_run") is not False:
        raise ValueError("seat audit exceeds its geometry-only scope")
    expected_seats = {"head_to_head_washer", "head_washer_to_wood", "nut_washer_to_nut", "wood_to_nut_washer"}
    audit_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in seat_audit.get("rows", ()):
        row_profile = str(row.get("scenario_id"))
        if row_profile != profile:
            continue
        key = (row_profile, str(row.get("physical_bolt_id", "")).rsplit("/", 1)[-1])
        if key in audit_by_key or row.get("all_seats_have_finite_opposed_common_face") is not True:
            raise ValueError("hardware seat audit repeats or omits an opposed finite seat")
        seats = row.get("seat_pairs", {})
        if set(seats) != expected_seats:
            raise ValueError(f"{key}: seat audit does not contain every separate hardware/wood face seat")
        for seat_id, seat in seats.items():
            _positive_finite(seat.get("finite_common_area_mm2"), f"{key}/{seat_id} common area")
            if float(seat.get("maximum_pair_gap_mm", math.inf)) > AUDITED_SEAT_GAP_TOLERANCE_MM:
                raise ValueError(f"{key}/{seat_id}: finite seat gap exceeds the geometric roundoff tolerance")
        audit_by_key[key] = row
    if set(audit_by_key) != {(profile, stack_id) for stack_id in STACK_IDS}:
        raise ValueError("seat audit does not cover all eight stacks for the selected profile")
    stack_rows = scenarios[profile].get("stacks")
    if not isinstance(stack_rows, list) or len(stack_rows) != len(STACK_IDS):
        raise ValueError("selected hardware profile must contain exactly eight stack records")
    stack_ids = [row.get("stack_spec_id") for row in stack_rows if isinstance(row, dict)]
    if len(stack_ids) != len(stack_rows) or len(set(stack_ids)) != len(STACK_IDS) or set(stack_ids) != set(STACK_IDS):
        raise ValueError("selected hardware profile lacks the exact eight physical bolt stacks")
    stacks = {row["stack_spec_id"]: row for row in stack_rows}
    thread = inventory.get("thread_and_gage_mapping", {})
    if (
        thread.get("thread_transition_observed") is not False
        or thread.get("full_form_thread_or_runout_modeled") is not False
        or thread.get("helical_profile_modeled") is not False
    ):
        raise ValueError("delivered thread transition and engagement must remain unverified")
    for stack_id, stack in stacks.items():
        if stack.get("wood_grip_mm") != 127.0 or stack.get("scenario_id") != profile:
            raise ValueError(f"{stack_id}: grip/profile differs from the source mechanics basis")
        engagement = stack.get("root_to_nut_engagement", {})
        if engagement.get("physical_thread_profile_or_engagement_verified") is not False or engagement.get("full_nut_thickness_engagement_assumed") is not True:
            raise ValueError(f"{stack_id}: thread assumption is missing or overclaimed")
    return stacks, audit_by_key


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wood-mesh-report", type=Path, required=True)
    parser.add_argument("--wood-mesh-deck", type=Path, required=True)
    parser.add_argument("--classification", type=Path, required=True)
    parser.add_argument("--wood-normal-audit", type=Path, required=True)
    parser.add_argument("--metal-mesh-report", type=Path, required=True)
    parser.add_argument("--metal-mesh-deck", type=Path, required=True)
    parser.add_argument("--mechanics-inputs", type=Path, required=True)
    parser.add_argument("--wood-patch-inventory", type=Path, required=True)
    parser.add_argument("--hardware-inventory", type=Path, required=True)
    parser.add_argument("--seat-audit", type=Path, required=True)
    parser.add_argument("--penalty-n-per-mm3", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists() or args.manifest.exists():
        raise FileExistsError("Refusing to overwrite contact-fragment artifacts")
    fragment, manifest = prepare_contact_fragment(
        args.wood_mesh_report,
        args.wood_mesh_deck,
        args.classification,
        args.wood_normal_audit,
        args.metal_mesh_report,
        args.metal_mesh_deck,
        args.mechanics_inputs,
        args.hardware_inventory,
        args.seat_audit,
        penalty_n_per_mm3=args.penalty_n_per_mm3,
        wood_patch_inventory_path=args.wood_patch_inventory,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(fragment)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
