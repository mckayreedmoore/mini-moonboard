"""Pure mesh-report and TRI6 integration oracles for a later mesh-only run."""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping

TRI6_GAUSS_7 = (
    (1 / 3, 1 / 3, 0.225),
    (0.05971587178977, 0.470142064105115, 0.132394152788506),
    (0.470142064105115, 0.05971587178977, 0.132394152788506),
    (0.470142064105115, 0.470142064105115, 0.132394152788506),
    (0.797426985353087, 0.101286507323456, 0.125939180544827),
    (0.101286507323456, 0.797426985353087, 0.125939180544827),
    (0.101286507323456, 0.101286507323456, 0.125939180544827),
)
BODY_IDS = (
    "receiver_base_principal_center_right_R75_crop",
    "washer_center_principal_right_2",
    "nut_H1_center_principal_right_2",
    "washer_center_principal_right_1",
    "nut_H1_center_principal_right_1",
)
FORBIDDEN_CARD_WORDS = (
    "MATERIAL", "ELASTIC", "CONTACT", "TIE", "CLOAD", "DLOAD", "BOUNDARY",
    "PRETENSION", "STEP", "STATIC", "FREQUENCY", "OUTPUT", "NODE FILE",
    "EL FILE", "SOLID SECTION", "SURFACE INTERACTION",
)
SUPPORTED_SOURCE_SURFACE_TYPES = ("Plane", "Cylinder", "Cone")
C3D10_FACE_NODES = (
    (0, 1, 2, 4, 5, 6),
    (0, 3, 1, 7, 8, 4),
    (1, 3, 2, 8, 9, 5),
    (2, 3, 0, 9, 7, 6),
)


def _cross(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def _shape(r: float, s: float) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    q = 1 - r - s
    values = (
        q * (1 - 2 * r - 2 * s),
        r * (2 * r - 1),
        s * (2 * s - 1),
        4 * r * q,
        4 * r * s,
        4 * s * q,
    )
    dr = (
        -3 + 4 * r + 4 * s,
        4 * r - 1,
        0,
        4 * (1 - 2 * r - s),
        4 * s,
        -4 * s,
    )
    ds = (
        -3 + 4 * r + 4 * s,
        0,
        4 * s - 1,
        -4 * r,
        4 * r,
        4 * (1 - r - 2 * s),
    )
    return values, dr, ds


def tri6_area_centroid(
    node_ids: Iterable[int], nodes: dict[int, Iterable[float]]
) -> tuple[float, tuple[float, float, float]]:
    ids = tuple(int(node) for node in node_ids)
    if len(ids) != 6 or len(set(ids)) != 6:
        raise ValueError("TRI6 face must have six distinct nodes")
    xyz = [tuple(float(value) for value in nodes[node]) for node in ids]
    if any(len(point) != 3 or not all(math.isfinite(value) for value in point) for point in xyz):
        raise ValueError("TRI6 coordinates must be finite 3-vectors")
    total_area = 0.0
    first_moment = [0.0, 0.0, 0.0]
    for r, s, weight in TRI6_GAUSS_7:
        values, dr, ds = _shape(r, s)
        point = tuple(math.fsum(values[i] * xyz[i][axis] for i in range(6)) for axis in range(3))
        tangent_r = tuple(math.fsum(dr[i] * xyz[i][axis] for i in range(6)) for axis in range(3))
        tangent_s = tuple(math.fsum(ds[i] * xyz[i][axis] for i in range(6)) for axis in range(3))
        jacobian = math.sqrt(_dot(_cross(tangent_r, tangent_s), _cross(tangent_r, tangent_s)))
        if not math.isfinite(jacobian) or jacobian <= 0:
            raise ValueError("TRI6 face has a nonpositive or nonfinite surface Jacobian")
        differential_area = 0.5 * weight * jacobian
        total_area += differential_area
        for axis in range(3):
            first_moment[axis] += point[axis] * differential_area
    if total_area <= 0:
        raise ValueError("TRI6 face has zero area")
    centroid = tuple(value / total_area for value in first_moment)
    return total_area, centroid


def integrate_uniform_axial_face(
    triangles: Iterable[Iterable[int]],
    nodes: dict[int, Iterable[float]],
    *,
    cad_area_mm2: float,
    force_n: float,
    force_direction: Iterable[float],
    axis_origin_global_mm: Iterable[float],
    plane_x_global_mm: float,
) -> dict[str, Any]:
    if not (math.isfinite(cad_area_mm2) and cad_area_mm2 > 0 and math.isfinite(force_n) and force_n > 0):
        raise ValueError("CAD face area and signed force must be finite and positive")
    direction = tuple(float(value) for value in force_direction)
    origin = tuple(float(value) for value in axis_origin_global_mm)
    if len(direction) != 3 or len(origin) != 3 or not all(math.isfinite(v) for v in (*direction, *origin)):
        raise ValueError("force direction and axis origin must be finite 3-vectors")
    norm = math.sqrt(_dot(direction, direction))
    if abs(norm - 1) > 1e-12:
        raise ValueError("force direction must be unit length")
    tri_rows = [tuple(int(node) for node in row) for row in triangles]
    if not tri_rows:
        raise ValueError("load face has no TRI6 triangles")
    if len({tuple(sorted(row[:3])) for row in tri_rows}) != len(tri_rows):
        raise ValueError("load-face TRI6 triangle corner ownership is duplicated")
    area = 0.0
    first = [0.0, 0.0, 0.0]
    for row in tri_rows:
        tri_area, centroid = tri6_area_centroid(row, nodes)
        area += tri_area
        for axis in range(3):
            first[axis] += tri_area * centroid[axis]
        for node in row:
            point = tuple(float(value) for value in nodes[node])
            if abs(point[0] - plane_x_global_mm) > 1e-6:
                raise ValueError("load-face triangle is not on its authenticated X plane")
    centroid = tuple(value / area for value in first)
    traction = force_n / cad_area_mm2
    integrated_force = tuple(traction * area * component for component in direction)
    arm = tuple(centroid[i] - origin[i] for i in range(3))
    moment = _cross(arm, integrated_force)
    force_error = math.sqrt(math.fsum((integrated_force[i] - force_n * direction[i]) ** 2 for i in range(3)))
    moment_error = math.sqrt(_dot(moment, moment))
    return {
        "triangle_count": len(tri_rows),
        "mesh_area_mm2": area,
        "cad_area_mm2": cad_area_mm2,
        "area_relative_error": abs(area / cad_area_mm2 - 1),
        "mesh_area_centroid_global_mm": list(centroid),
        "uniform_traction_magnitude_N_per_mm2": traction,
        "integrated_force_global_N": list(integrated_force),
        "integrated_moment_about_axis_N_mm": list(moment),
        "force_residual_N": force_error,
        "moment_residual_N_mm": moment_error,
        "passes_contact_coupon_quadrature_limits": force_error <= 0.02 and moment_error <= 0.05,
    }


def _positive_id(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{context} must be a positive integer ID")
    return value


def _tri6_edges(nodes: Iterable[int]) -> dict[tuple[int, int], int]:
    row = tuple(_positive_id(value, "TRI6 node") for value in nodes)
    if len(row) != 6 or len(set(row)) != 6:
        raise ValueError("TRI6 face must have six distinct positive node IDs")
    return {
        tuple(sorted((row[a], row[b]))): row[middle]
        for a, b, middle in ((0, 1, 3), (1, 2, 4), (2, 0, 5))
    }


def audit_c3d10_surface_ownership(
    elements: Mapping[int, Iterable[int]],
    surface_triangles: Mapping[str, Iterable[Iterable[int]]],
) -> dict[str, Any]:
    """Independently reconcile every semantic TRI6 against C3D10 topology.

    The input ordering is CalculiX C3D10: four corners then midside nodes on
    (1-2), (2-3), (3-1), (1-4), (2-4), (3-4). No CAD tag or bounding box is
    used. Shared complete faces establish element adjacency; edge-only or
    point-only contact does not count as a connected solid.
    """
    if not isinstance(elements, Mapping) or not elements:
        raise ValueError("C3D10 body must contain at least one element")
    normalized: dict[int, tuple[int, ...]] = {}
    for raw_element_id, raw_nodes in elements.items():
        element_id = _positive_id(raw_element_id, "C3D10 element")
        row = tuple(_positive_id(value, f"element {element_id} node") for value in raw_nodes)
        if len(row) != 10 or len(set(row)) != 10:
            raise ValueError(f"element {element_id}: C3D10 needs ten distinct nodes")
        normalized[element_id] = row
    if len(normalized) != len(elements):
        raise ValueError("duplicate C3D10 element IDs")

    parent = {element_id: element_id for element_id in normalized}

    def find(element_id: int) -> int:
        while parent[element_id] != element_id:
            parent[element_id] = parent[parent[element_id]]
            element_id = parent[element_id]
        return element_id

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    by_corners: dict[tuple[int, int, int], list[tuple[int, int, tuple[int, ...]]]] = {}
    for element_id, row in normalized.items():
        for face_number, pattern in enumerate(C3D10_FACE_NODES, start=1):
            face_nodes = tuple(row[index] for index in pattern)
            corner_key = tuple(sorted(face_nodes[:3]))
            by_corners.setdefault(corner_key, []).append((element_id, face_number, face_nodes))

    exterior: dict[tuple[int, int, int], tuple[int, int, tuple[int, ...]]] = {}
    interior_keys: set[tuple[int, int, int]] = set()
    for corner_key, members in by_corners.items():
        if len(members) == 1:
            exterior[corner_key] = members[0]
        elif len(members) == 2:
            left, right = members
            if _tri6_edges(left[2]) != _tri6_edges(right[2]):
                raise ValueError("interior C3D10 face has incompatible midside nodes")
            union(left[0], right[0])
            interior_keys.add(corner_key)
        else:
            raise ValueError("C3D10 mesh has a nonmanifold face")

    if not isinstance(surface_triangles, Mapping) or not surface_triangles:
        raise ValueError("semantic surface inventory must be nonempty")
    covered: dict[tuple[int, int], str] = {}
    references: dict[str, list[list[int]]] = {}
    triangle_count = 0
    for semantic_id, triangles in surface_triangles.items():
        if not isinstance(semantic_id, str) or not semantic_id.strip():
            raise ValueError("semantic surface IDs must be nonempty strings")
        rows = list(triangles)
        if not rows:
            raise ValueError(f"{semantic_id}: semantic surface has no TRI6 faces")
        refs: list[list[int]] = []
        for raw_triangle in rows:
            triangle_count += 1
            triangle = tuple(_positive_id(value, f"{semantic_id} TRI6 node") for value in raw_triangle)
            triangle_edges = _tri6_edges(triangle)
            corner_key = tuple(sorted(triangle[:3]))
            owner = exterior.get(corner_key)
            if owner is None:
                if corner_key in interior_keys:
                    raise ValueError(f"{semantic_id}: TRI6 was assigned to an interior C3D10 face")
                raise ValueError(f"{semantic_id}: TRI6 does not match a C3D10 exterior face")
            element_id, face_number, face_nodes = owner
            if triangle_edges != _tri6_edges(face_nodes):
                raise ValueError(f"{semantic_id}: TRI6 midside ownership differs from C3D10 face")
            ref = (element_id, face_number)
            if ref in covered:
                raise ValueError(f"exterior face {ref} is duplicated by {covered[ref]} and {semantic_id}")
            covered[ref] = semantic_id
            refs.append([element_id, face_number])
        references[semantic_id] = sorted(refs)

    expected = {(element_id, face_number) for element_id, face_number, _ in exterior.values()}
    if covered.keys() != expected:
        missing = sorted(expected - covered.keys())
        extra = sorted(covered.keys() - expected)
        raise ValueError(f"exterior TRI6 ownership is incomplete; missing={missing[:8]}, extra={extra[:8]}")

    component_count = len({find(element_id) for element_id in normalized})
    return {
        "element_count": len(normalized),
        "referenced_node_ids": sorted({node for row in normalized.values() for node in row}),
        "connected_component_count": component_count,
        "exterior_c3d10_face_count": len(exterior),
        "tri6_face_count": triangle_count,
        "semantic_surface_ids": sorted(references),
        "face_refs_by_semantic_surface": references,
    }


def _finite_positive(value: Any, context: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{context} must be a finite positive number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context} must be a finite positive number") from error
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{context} must be a finite positive number")
    return result


def validate_mesh_report(
    report: dict[str, Any],
    expected_source_pins_sha256: str,
    *,
    topology_bodies: Mapping[str, Mapping[str, Any]],
) -> None:
    """Fail closed on a parent-produced mesh report; never runs a solver."""
    if report.get("schema") != "conditional_washer_crop_mesh_report/v1":
        raise ValueError("unsupported conditional washer mesh report schema")
    if report.get("status") != "VERIFIED_C3D10_MESH_ONLY_NO_SOLVER":
        raise ValueError("mesh report did not pass its mesh-only status")
    if report.get("source_pins_sha256") != expected_source_pins_sha256:
        raise ValueError("mesh report is not bound to the current source pins")
    if report.get("candidate") != "compact-floor-flush-wood-joints-development" or report.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("mesh report candidate or geometry revision changed")
    if report.get("branch") != "R75_H1_R_T_A_K12_catalog_nominal_frictionless_mesh_only":
        raise ValueError("mesh report is not the one authorized R75/H1 base branch")
    forbidden = ("accepted", "solved", "material_cards", "contact_cards", "tie_cards", "load_cards", "restraint_cards", "preload_cards", "solver_cards")
    if any(report.get(key) is not False for key in forbidden):
        raise ValueError("mesh report exceeds mesh-only scope")
    if report.get("body_count") != len(BODY_IDS) or report.get("body_ids") != list(BODY_IDS):
        raise ValueError("mesh report body inventory differs from the five-body contract")
    bodies = report.get("bodies")
    if not isinstance(bodies, dict) or set(bodies) != set(BODY_IDS):
        raise ValueError("mesh report lacks exact body records")
    if not isinstance(topology_bodies, Mapping) or set(topology_bodies) != set(BODY_IDS):
        raise ValueError("independent topology input does not contain the exact five bodies")
    faces = report.get("surface_ownership")
    if not isinstance(faces, dict) or faces.get("source_ancestry_verified") is not True or faces.get("source_face_ownership_complete") is not True:
        raise ValueError("source-face ancestry/ownership is not complete")
    if faces.get("bbox_only_identity_used") is not False or faces.get("unclassified_source_face_count") != 0 or faces.get("ambiguous_semantic_face_count") != 0:
        raise ValueError("source-face semantic ownership is ambiguous or incomplete")
    if faces.get("crop_generated_surface_ids") != ["receiver.crop_cylinder_R75"]:
        raise ValueError("R75-created boundary is not recorded separately")
    if faces.get("source_signature_family_allowlist") != list(SUPPORTED_SOURCE_SURFACE_TYPES):
        raise ValueError("source surface signature allowlist differs from the pinned analytic families")
    seen_types = faces.get("source_signature_families_seen")
    if not isinstance(seen_types, list) or not set(seen_types) <= set(SUPPORTED_SOURCE_SURFACE_TYPES):
        raise ValueError("source BREP contains an unsupported analytic surface family")
    if faces.get("unsupported_source_surface_types") != [] or faces.get("unmapped_intersecting_source_face_count") != 0 or faces.get("source_face_descendant_coverage_complete") is not True:
        raise ValueError("source-face ancestry does not cover every intersecting natural face")
    categories_by_body = faces.get("surface_categories_by_body")
    semantic_ids_by_body = faces.get("semantic_surface_ids_by_body")
    if not isinstance(categories_by_body, dict) or set(categories_by_body) != set(BODY_IDS):
        raise ValueError("natural/crop/hardware semantic categories do not cover all bodies")
    if not isinstance(semantic_ids_by_body, dict) or set(semantic_ids_by_body) != set(BODY_IDS):
        raise ValueError("semantic surface IDs do not cover all bodies")

    signature_rows = faces.get("source_natural_face_signature_rows")
    if not isinstance(signature_rows, list):
        raise ValueError("source natural-face signature inventory is missing")
    natural_ids = categories_by_body[BODY_IDS[0]].get("source_natural") if isinstance(categories_by_body[BODY_IDS[0]], dict) else None
    if not isinstance(natural_ids, list) or len(signature_rows) != len(natural_ids):
        raise ValueError("source natural-face signature inventory is incomplete")
    signature_ids: set[str] = set()
    for row in signature_rows:
        if not isinstance(row, dict):
            raise ValueError("source face signature row must be an object")
        semantic_id = row.get("semantic_surface_id")
        surface_type = row.get("source_surface_type")
        if not isinstance(semantic_id, str) or semantic_id in signature_ids or surface_type not in SUPPORTED_SOURCE_SURFACE_TYPES:
            raise ValueError("source face signature ID/type is invalid or duplicated")
        signature_ids.add(semantic_id)
        for key in ("source_surface_signature_sha256", "clipped_surface_signature_sha256", "source_step_sha256"):
            digest = row.get(key)
            if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError(f"{semantic_id}: invalid {key}")
        if row.get("source_face_ancestry_verified") is not True:
            raise ValueError(f"{semantic_id}: natural-face ancestry was not verified")
        source_area = _finite_positive(row.get("source_face_area_mm2"), f"{semantic_id} source face area")
        clipped_area = _finite_positive(row.get("clipped_face_area_mm2"), f"{semantic_id} cropped face area")
        if clipped_area > source_area + max(1e-8, source_area * 1e-8):
            raise ValueError(f"{semantic_id}: cropped natural face exceeds its source area")
    if signature_ids != set(natural_ids):
        raise ValueError("source face signature rows do not match the surviving natural face inventory")

    audited_exterior_count = 0
    audited_tri6_count = 0
    seen_nodes: set[int] = set()
    seen_elements: set[int] = set()
    for body_id in BODY_IDS:
        body = bodies[body_id]
        if body.get("solid_count") != 1 or body.get("connected_component_count") != 1:
            raise ValueError(f"{body_id}: expected one valid connected solid")
        if body.get("element_type") != "C3D10":
            raise ValueError(f"{body_id}: unexpected volume element type")
        cad_volume = _finite_positive(body.get("source_cad_volume_mm3"), f"{body_id} CAD volume")
        mesh_volume = _finite_positive(body.get("mesh_integrated_volume_mm3"), f"{body_id} mesh volume")
        if abs(mesh_volume / cad_volume - 1) > 0.001:
            raise ValueError(f"{body_id}: mesh volume differs from exact BREP by over 0.1%")
        if _finite_positive(body.get("minimum_sampled_jacobian"), f"{body_id} sampled Jacobian") <= 0:
            raise ValueError(f"{body_id}: invalid sampled Jacobian")
        if _finite_positive(body.get("minimum_gauss5_jacobian"), f"{body_id} Gauss5 Jacobian") <= 0:
            raise ValueError(f"{body_id}: invalid Gauss5 Jacobian")
        nodes = body.get("node_ids")
        elements = body.get("element_ids")
        if not isinstance(nodes, list) or not nodes or any(isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in nodes) or len(nodes) != len(set(nodes)):
            raise ValueError(f"{body_id}: invalid node ownership")
        if not isinstance(elements, list) or not elements or any(isinstance(e, bool) or not isinstance(e, int) or e <= 0 for e in elements) or len(elements) != len(set(elements)):
            raise ValueError(f"{body_id}: invalid element ownership")
        node_set, element_set = set(nodes), set(elements)
        if seen_nodes & node_set or seen_elements & element_set:
            raise ValueError("separate body meshes share node or element identifiers")
        seen_nodes.update(node_set)
        seen_elements.update(element_set)
        topology = topology_bodies[body_id]
        if not isinstance(topology, Mapping) or not isinstance(topology.get("elements"), Mapping) or not isinstance(topology.get("surface_triangles"), Mapping):
            raise ValueError(f"{body_id}: independent C3D10/TRI6 connectivity is missing")
        if set(topology["elements"]) != element_set:
            raise ValueError(f"{body_id}: independent C3D10 element IDs differ from body ownership")
        audit = audit_c3d10_surface_ownership(topology["elements"], topology["surface_triangles"])
        if set(audit["referenced_node_ids"]) != node_set:
            raise ValueError(f"{body_id}: independent C3D10 connectivity differs from body node ownership")
        if audit["connected_component_count"] != body.get("connected_component_count"):
            raise ValueError(f"{body_id}: independently audited connectivity is not one connected component")
        expected_surface_ids = semantic_ids_by_body.get(body_id)
        if not isinstance(expected_surface_ids, list) or sorted(expected_surface_ids) != audit["semantic_surface_ids"]:
            raise ValueError(f"{body_id}: semantic TRI6 IDs differ from the pinned face map")
        categories = categories_by_body.get(body_id)
        if not isinstance(categories, dict) or set(categories) != {"source_natural", "crop_generated", "conditional_hardware"}:
            raise ValueError(f"{body_id}: natural/crop/hardware face categories are missing")
        category_rows = [categories[key] for key in ("source_natural", "crop_generated", "conditional_hardware")]
        if any(not isinstance(row, list) or len(row) != len(set(row)) for row in category_rows):
            raise ValueError(f"{body_id}: semantic face category list is invalid")
        flattened = [value for row in category_rows for value in row]
        if len(flattened) != len(set(flattened)) or sorted(flattened) != audit["semantic_surface_ids"]:
            raise ValueError(f"{body_id}: face categories overlap or omit semantic surfaces")
        audited_exterior_count += audit["exterior_c3d10_face_count"]
        audited_tri6_count += audit["tri6_face_count"]
    if faces.get("exterior_c3d10_face_count") != audited_exterior_count or faces.get("tri6_face_count") != audited_tri6_count or audited_exterior_count != audited_tri6_count or faces.get("uncovered_exterior_face_count") != 0 or faces.get("duplicate_exterior_face_count") != 0:
        raise ValueError("TRI6/exterior C3D10 ownership is incomplete or duplicated")
    layers = report.get("achieved_minimum_washer_through_thickness_layers")
    if isinstance(layers, bool) or not isinstance(layers, int) or layers < 2:
        raise ValueError("washer thickness resolution is below the nominal two-layer target")
    if _finite_positive(report.get("maximum_local_edge_mm"), "maximum local edge") > 0.8 + 1e-12:
        raise ValueError("local mesh edge exceeds the 0.8 mm branch limit")


def validate_mesh_deck_keywords(text: str) -> None:
    """Reject non-mesh cards in a future no-solver C3D10 input deck."""
    allowed = ("*HEADING", "*NODE", "*ELEMENT,TYPE=C3D10,ELSET=")
    cards = [line.strip().upper() for line in text.splitlines() if line.lstrip().startswith("*")]
    if not cards or cards[0] != "*HEADING":
        raise ValueError("mesh deck must begin with *HEADING")
    for card in cards:
        if not any(card.startswith(prefix) for prefix in allowed):
            if any(word in card for word in FORBIDDEN_CARD_WORDS):
                raise ValueError(f"solver/mechanics card is forbidden in mesh-only deck: {card}")
            raise ValueError(f"unexpected non-mesh deck card: {card}")
