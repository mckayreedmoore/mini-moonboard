"""Classify WJ04 contact and bolt-bore mesh surfaces by authenticated geometry.

This standard-library adapter consumes a frozen mesh report/deck and archived
geometry evidence. It does not import Gmsh or CadQuery, assign contact, or run a
native solver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
from typing import Any

from fea import wood_joint_patch_mesh as mesh_contract

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj04_patch_surface_classification/v1"
MESH_SCHEMA = "wood_joint_patch_mesh/v1"
OVERLAP_SCHEMA_STATUS = "parent_finite_face_overlap_probe_only"
MESH_REPORT_SHA256 = "e8af81e6a92eb53b4ee72fcecc43efd9ed7ab901b3568be603509994c8b3c33c"
MESH_INPUT_SHA256 = "43f50fd605841821391f749ebddf226c639778945fef89b50ff78899c38afe56"
MESH_WORKER_SHA256 = "915ab6d14efc6e81b4a95c4338ffb8b98cb7e4fac1478d23b592bc8bb377564b"
PATCH_INVENTORY_SHA256 = (
    "c208f96bcfcda7a6b089496c9e1c4afe48f874810050f8d0c5cc700f65d5772d"
)
PATCH_HASH_INDEX_SHA256 = (
    "e758d733b9ba3169825220a45aea63ea1d1ebc70da0c9e2cb783464e8e4ea91d"
)
OVERLAP_HASH_INDEX_SHA256 = (
    "b824347ba84612c5a4f43d35b22b6c737d14d816cd7df75cb0cc212bf1f56041"
)
OVERLAP_SHA256 = "d73fae24bf90bf710939cef7980607c5b93b4aa7ff4cefb3226922b61f248e9d"
OVERLAP_PRODUCER_SHA256 = (
    "6c9a6eb71ca030d839e209c6db23acebc8e753eae7a3b4ace1115eb9f0a32cee"
)
OVERLAP_EXECUTION_SHA256 = (
    "02b67865a7ed396de0c14a1b05578a74fb32bacd818fc02c7ff22c1750447a71"
)
MECHANICS_CONTRACT_SOURCE = "scripts/wood_joint_wj04_full_stock_mechanics_contract.py"
MECHANICS_CONTRACT_SOURCE_SHA256 = (
    "fd8bc1c92efa43f57cb51eff07ece9aa044ca3593892f812706a5e01adff020c"
)
PATCH_BUNDLE_RELATIVE = "fea/results/diagnostics/wj04-full-stock-patch-geometry-v1"
OVERLAP_ARCHIVE_RELATIVE = "docs/wood-joints-mvp/hypotheses/wj04-patch-geometry"
DEFAULT_MESH_RELATIVE = "fea/generated/wj04-patch-mesh/attempt-03"

PLANE_DISTANCE_TOLERANCE_MM = 1e-6
CYLINDER_RADIAL_TOLERANCE_MM = 1e-6
CYLINDER_STATION_TOLERANCE_MM = 1e-6
NORMAL_DOT_TOLERANCE = 1e-7
AREA_ABSOLUTE_TOLERANCE_MM2 = 1e-4
AREA_RELATIVE_TOLERANCE = 1e-8
BORE_EXTENSION_EACH_END_MM = 0.1

WOOD_BODY_IDS = mesh_contract.WOOD_BODY_IDS
EXPECTED_INTERFACE_IDS = tuple(sorted(mesh_contract.EXPECTED_INTERFACE_STACKS))
EXPECTED_STACK_IDS = tuple(sorted(mesh_contract.STACK_RECEIVERS))
EXPECTED_BOLT_IDS = {
    mesh_contract.G7_AXIS_PREFIX + stack_id for stack_id in EXPECTED_STACK_IDS
}
EXPECTED_RECEIVER_THICKNESS_MM = {
    "lower_rail_1": (88.9, 38.1),
    "lower_rail_2": (88.9, 38.1),
    "lower_principal_1": (88.9, 38.1),
    "lower_principal_2": (88.9, 38.1),
    "upper_rail_1": (38.1, 88.9),
    "upper_rail_2": (38.1, 88.9),
    "upper_principal_1": (88.9, 38.1),
    "upper_principal_2": (88.9, 38.1),
}
EXPECTED_INTERFACE_BY_STACK = {
    stack_id: interface_id
    for interface_id, stack_ids in mesh_contract.EXPECTED_INTERFACE_STACKS.items()
    for stack_id in stack_ids
}

LIMITS = (
    "Geometric surface classification only; no contact law, tie, active pressure, "
    "material, response, capacity, or release result. Forty hardware roles are not "
    "meshed, so bolt-shank/bore contact and any initial seating or preload are unmodeled. "
    "Gmsh surface tags are local pointers."
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def write_json(path: str | Path, record: Any) -> None:
    Path(path).write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def _vec3(value: Any, context: str) -> tuple[float, float, float]:
    try:
        row = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected a finite XYZ vector") from error
    if len(row) != 3 or not all(math.isfinite(component) for component in row):
        raise ValueError(f"{context}: expected a finite XYZ vector")
    return row  # type: ignore[return-value]


def _positive(value: Any, context: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected a positive finite number") from error
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{context}: expected a positive finite number")
    return result


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def _norm(value: tuple[float, ...]) -> float:
    return math.sqrt(_dot(value, value))


def _unit(value: Any, context: str) -> tuple[float, float, float]:
    vector = _vec3(value, context)
    magnitude = _norm(vector)
    if not math.isfinite(magnitude) or magnitude <= 0:
        raise ValueError(f"{context}: zero-length vector")
    return tuple(component / magnitude for component in vector)  # type: ignore[return-value]


def _sub(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(x - y for x, y in zip(a, b, strict=True))


def _scale(vector: tuple[float, ...], scalar: float) -> tuple[float, ...]:
    return tuple(component * scalar for component in vector)


def _area_close(actual: float, expected: float) -> bool:
    tolerance = max(
        AREA_ABSOLUTE_TOLERANCE_MM2,
        AREA_RELATIVE_TOLERANCE * abs(expected),
    )
    return math.isfinite(actual) and abs(actual - expected) <= tolerance


def _validate_mechanics_contract_source() -> None:
    source = ROOT / MECHANICS_CONTRACT_SOURCE
    if not source.is_file() or sha256_file(source) != MECHANICS_CONTRACT_SOURCE_SHA256:
        raise ValueError(
            "pinned full-stock mechanics source changed; bore extension basis is unauthenticated"
        )


def parse_mesh_deck(
    path: str | Path,
) -> tuple[
    dict[int, tuple[float, float, float]], dict[str, dict[int, tuple[int, ...]]]
]:
    """Read the adapter's node and per-member C3D10 sets without a solver stack."""
    node_rows: dict[int, tuple[float, float, float]] = {}
    element_rows: dict[str, dict[int, tuple[int, ...]]] = {
        body_id: {} for body_id in WOOD_BODY_IDS
    }
    mode: str | None = None
    current_body: str | None = None
    try:
        lines = Path(path).read_text().splitlines()
    except OSError as error:
        raise ValueError(f"mesh input deck is unavailable: {path}") from error
    body_by_elset = {body_id.upper(): body_id for body_id in WOOD_BODY_IDS}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            upper = line.upper()
            mode = None
            current_body = None
            if upper == "*NODE":
                mode = "nodes"
            elif upper.startswith("*ELEMENT,"):
                options = {
                    key.strip(): value.strip()
                    for cell in line.split(",")[1:]
                    if "=" in cell
                    for key, value in (cell.split("=", 1),)
                }
                if options.get("TYPE", "").upper() != "C3D10":
                    raise ValueError(f"line {line_number}: non-C3D10 element block")
                body_id = body_by_elset.get(options.get("ELSET", "").upper())
                if body_id is None:
                    raise ValueError(f"line {line_number}: unknown C3D10 element set")
                current_body = body_id
                mode = "elements"
            continue
        cells = [cell.strip() for cell in line.split(",")]
        try:
            if mode == "nodes":
                if len(cells) != 4:
                    raise ValueError("expected node ID and three coordinates")
                node_id = int(cells[0])
                xyz = _vec3(cells[1:], f"line {line_number} node {node_id}")
                if node_id <= 0 or node_id in node_rows:
                    raise ValueError("node ID is nonpositive or duplicated")
                node_rows[node_id] = xyz
            elif mode == "elements":
                if current_body is None or len(cells) != 11:
                    raise ValueError("expected C3D10 ID and ten node IDs")
                element_id = int(cells[0])
                connectivity = tuple(int(cell) for cell in cells[1:])
                if element_id <= 0 or any(node <= 0 for node in connectivity):
                    raise ValueError("element and node IDs must be positive")
                if len(set(connectivity)) != 10:
                    raise ValueError("C3D10 must have ten distinct nodes")
                if element_id in element_rows[current_body] or any(
                    element_id in body for body in element_rows.values()
                ):
                    raise ValueError("element ID is duplicated")
                element_rows[current_body][element_id] = connectivity
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                f"invalid mesh input at line {line_number}: {error}"
            ) from error
    if not node_rows or any(not rows for rows in element_rows.values()):
        raise ValueError("mesh input deck does not contain all five C3D10 member sets")
    used_nodes = {
        node
        for rows in element_rows.values()
        for conn in rows.values()
        for node in conn
    }
    if not used_nodes <= node_rows.keys():
        raise ValueError("C3D10 connectivity references missing mesh nodes")
    if used_nodes != node_rows.keys():
        raise ValueError("mesh deck contains nodes without C3D10 member ownership")
    return node_rows, element_rows


def _validate_mesh_surface_inventory(
    mesh_record: dict[str, Any],
    node_coordinates: dict[int, tuple[float, float, float]],
    elements_by_body: dict[str, dict[int, tuple[int, ...]]] | None,
) -> dict[str, dict[str, dict[str, Any]]]:
    if mesh_record.get("schema") != MESH_SCHEMA:
        raise ValueError("mesh report schema is not the WJ04 patch mesh contract")
    if mesh_record.get("status") != "VERIFIED_C3D10_MESH_ONLY_NO_SOLVER":
        raise ValueError("mesh report is not a verified C3D10 mesh-only result")
    if (
        mesh_record.get("accepted") is not False
        or mesh_record.get("solved") is not False
    ):
        raise ValueError(
            "mesh report contains an out-of-scope acceptance or solve flag"
        )
    if mesh_record.get("output_contains_material_contact_or_solver_cards") is not False:
        raise ValueError("mesh report includes material/contact/solver input")
    bodies = mesh_record.get("bodies")
    if not isinstance(bodies, dict) or set(bodies) != set(WOOD_BODY_IDS):
        raise ValueError("mesh report does not contain the exact five wood bodies")
    if mesh_record.get("body_count") != 5:
        raise ValueError("mesh report body count differs from the five-body scope")
    if set(node_coordinates) != set(range(1, len(node_coordinates) + 1)):
        raise ValueError(
            "mesh input node IDs are not the expected global contiguous sequence"
        )
    if mesh_record.get("node_count") != len(node_coordinates):
        raise ValueError("mesh report node count differs from the mesh input deck")
    if elements_by_body is not None and set(elements_by_body) != set(WOOD_BODY_IDS):
        raise ValueError(
            "parsed input deck does not contain all five body element sets"
        )

    surface_index: dict[str, dict[str, dict[str, Any]]] = {}
    all_body_nodes: set[int] = set()
    all_body_elements: set[int] = set()
    for body_id in WOOD_BODY_IDS:
        body = bodies[body_id]
        body_nodes = set(body.get("nodes", ()))
        body_elements = set(body.get("elements", ()))
        if (
            not body_nodes
            or not body_elements
            or len(body_nodes) != len(body.get("nodes", ()))
            or len(body_elements) != len(body.get("elements", ()))
            or all_body_nodes & body_nodes
            or all_body_elements & body_elements
        ):
            raise ValueError(
                f"{body_id}: body node/element ownership is empty or overlaps"
            )
        if body.get("node_count") != len(body_nodes) or body.get(
            "element_count"
        ) != len(body_elements):
            raise ValueError(
                f"{body_id}: reported node/element counts differ from ownership"
            )
        all_body_nodes.update(body_nodes)
        all_body_elements.update(body_elements)
        if not body_nodes <= node_coordinates.keys():
            raise ValueError(f"{body_id}: body references absent deck nodes")
        if elements_by_body is not None:
            deck_elements = elements_by_body[body_id]
            if set(deck_elements) != body_elements:
                raise ValueError(f"{body_id}: report/deck element ownership differs")
            deck_nodes = {node for conn in deck_elements.values() for node in conn}
            if deck_nodes != body_nodes:
                raise ValueError(f"{body_id}: report/deck node ownership differs")

        surfaces = body.get("surface_inventory")
        if not isinstance(surfaces, dict) or body.get("surfaces") != surfaces:
            raise ValueError(f"{body_id}: mesh report surface inventories disagree")
        surface_index[body_id] = {}
        tag_values: set[int] = set()
        face_refs: list[tuple[int, int]] = []
        for tag_key, row in surfaces.items():
            if not isinstance(row, dict):
                raise TypeError(f"{body_id}: surface row must be an object")
            try:
                tag = int(tag_key)
                declared_tag = int(row.get("cad_entity_tag"))
            except (TypeError, ValueError, OverflowError) as error:
                raise ValueError(
                    f"{body_id}: malformed transient surface tag"
                ) from error
            if tag != declared_tag or tag in tag_values:
                raise ValueError(f"{body_id}: surface tag key and row disagree")
            tag_values.add(tag)
            _positive(row.get("area_mm2"), f"{body_id} surface {tag} area")
            node_ids = row.get("tri6_node_ids")
            refs = row.get("tri6_exterior_face_refs")
            if (
                not isinstance(node_ids, list)
                or not node_ids
                or not isinstance(refs, list)
                or not refs
            ):
                raise ValueError(
                    f"{body_id} surface {tag}: missing TRI6 mesh references"
                )
            if len(node_ids) != len(set(node_ids)) or not set(node_ids) <= body_nodes:
                raise ValueError(
                    f"{body_id} surface {tag}: TRI6 node ownership is invalid"
                )
            if not set(node_ids) <= node_coordinates.keys():
                raise ValueError(f"{body_id} surface {tag}: mesh deck node is missing")
            for ref in refs:
                if not isinstance(ref, (list, tuple)) or len(ref) != 2:
                    raise ValueError(
                        f"{body_id} surface {tag}: malformed C3D10 face ref"
                    )
                element_id, face_id = int(ref[0]), int(ref[1])
                if element_id not in body_elements or face_id not in {1, 2, 3, 4}:
                    raise ValueError(
                        f"{body_id} surface {tag}: face ref has wrong body IDs"
                    )
                face_refs.append((element_id, face_id))
            if row.get("bounds_order") != "xmin,xmax,ymin,ymax,zmin,zmax":
                raise ValueError(
                    f"{body_id} surface {tag}: bounds order is not explicit"
                )
            surface_index[body_id][str(tag)] = row
        expected_face_count = body.get("exterior_tri6_face_count")
        if len(face_refs) != expected_face_count or len(set(face_refs)) != len(
            face_refs
        ):
            raise ValueError(
                f"{body_id}: exterior face ownership is incomplete or duplicated"
            )
    if elements_by_body is not None and all_body_elements != {
        element for rows in elements_by_body.values() for element in rows
    }:
        raise ValueError("mesh report does not own every deck C3D10 element")
    if mesh_record.get("element_count") != len(all_body_elements):
        raise ValueError("mesh report element count differs from body ownership")
    return surface_index


def _sample_plane_match(
    surface: dict[str, Any],
    point: tuple[float, float, float],
    normal: tuple[float, float, float],
    node_coordinates: dict[int, tuple[float, float, float]],
) -> dict[str, float] | None:
    if str(surface.get("cad_type", "")).casefold() != "plane":
        return None
    analytic = surface.get("analytic_surface_data")
    if (
        not isinstance(analytic, dict)
        or str(analytic.get("surface_type", "")).casefold() != "plane"
    ):
        return None
    try:
        sample_point = _vec3(analytic.get("sample_xyz_mm"), "plane sample point")
        sample_normal = _unit(
            analytic.get("sample_normal_global"), "plane sample normal"
        )
        node_ids = tuple(int(value) for value in surface["tri6_node_ids"])
        points = tuple(node_coordinates[node_id] for node_id in node_ids)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    alignment = abs(_dot(sample_normal, normal))
    sample_offset = abs(_dot(_sub(sample_point, point), normal))
    node_offsets = tuple(abs(_dot(_sub(xyz, point), normal)) for xyz in points)
    if (
        alignment < 1 - NORMAL_DOT_TOLERANCE
        or sample_offset > PLANE_DISTANCE_TOLERANCE_MM
        or max(node_offsets, default=math.inf) > PLANE_DISTANCE_TOLERANCE_MM
    ):
        return None
    return {
        "absolute_sample_normal_dot": alignment,
        "sample_plane_residual_mm": sample_offset,
        "maximum_tri6_node_plane_residual_mm": max(node_offsets),
    }


def _surface_pointer(member_id: str, tag: str) -> dict[str, Any]:
    return {
        "member_id": member_id,
        "cad_entity_tag": int(tag),
        "tag_semantics": "transient pointer within the independent member mesh; not a semantic ID",
    }


def _classify_contact_interfaces(
    surface_index: dict[str, dict[str, dict[str, Any]]],
    node_coordinates: dict[int, tuple[float, float, float]],
    inventory: dict[str, Any],
    overlap: dict[str, Any],
) -> list[dict[str, Any]]:
    interface_rows = inventory.get("wood_interfaces")
    overlap_rows = overlap.get("interfaces")
    if not isinstance(interface_rows, list) or not isinstance(overlap_rows, list):
        raise TypeError("contact interface source rows are missing")
    interface_by_id = {row.get("interface_id"): row for row in interface_rows}
    overlap_by_id = {row.get("interface_id"): row for row in overlap_rows}
    if set(interface_by_id) != set(EXPECTED_INTERFACE_IDS):
        raise ValueError(
            "frozen mechanics inventory differs from the exact four interfaces"
        )
    if set(overlap_by_id) != set(EXPECTED_INTERFACE_IDS):
        raise ValueError("finite-face archive differs from the exact four interfaces")

    classified: list[dict[str, Any]] = []
    for interface_id in EXPECTED_INTERFACE_IDS:
        row = interface_by_id[interface_id]
        probe = overlap_by_id[interface_id]
        candidate = row["candidate_cleat_face"]
        host = row["source_host_face"]
        datum = row["shear_plane_datum"]
        candidate_id = candidate["part_id"]
        host_id = host["part_id"]
        members = set(row["members_head_to_nut"])
        if members != {candidate_id, host_id} or candidate_id == host_id:
            raise ValueError(
                f"{interface_id}: member pair differs from candidate/host bindings"
            )
        if (
            probe.get("cleat_member") != candidate_id
            or probe.get("source_member") != host_id
        ):
            raise ValueError(f"{interface_id}: finite-face member identity changed")
        if (
            probe.get("matched_cleat_planar_faces") != 1
            or probe.get("matched_host_planar_faces") != 1
        ):
            raise ValueError(
                f"{interface_id}: archived finite overlap was not one face pair"
            )
        if probe.get("finite_common_face_count") != 1:
            raise ValueError(f"{interface_id}: archived common face count changed")
        if probe.get("pressure_or_capacity_established") is not False:
            raise ValueError(
                f"{interface_id}: archived overlap makes an unsupported mechanics claim"
            )

        candidate_area = _positive(
            candidate.get("composed_finished_planar_area_mm2"),
            f"{interface_id} cleat plane area",
        )
        probe_candidate_area = _positive(
            probe.get("cleat_planar_area_mm2"), "probe cleat area"
        )
        common_area = _positive(
            probe.get("finite_common_area_mm2"), "probe common area"
        )
        host_area = _positive(
            probe.get("host_planar_area_mm2"), "probe host plane area"
        )
        if not all(
            _area_close(value, candidate_area)
            for value in (probe_candidate_area, common_area)
        ):
            raise ValueError(
                f"{interface_id}: archived common footprint does not cover the whole cleat face"
            )
        if (
            host_area
            + max(
                AREA_ABSOLUTE_TOLERANCE_MM2,
                AREA_RELATIVE_TOLERANCE * host_area,
            )
            < common_area
        ):
            raise ValueError(
                f"{interface_id}: host plane is smaller than the common footprint"
            )

        candidate_normal = _unit(
            candidate.get("plane_normal_global_xyz"),
            f"{interface_id} candidate outward datum",
        )
        host_normal = _unit(
            host.get("normal_global_xyz"), f"{interface_id} host outward datum"
        )
        normal_opposition = _dot(candidate_normal, host_normal)
        if normal_opposition > -1 + NORMAL_DOT_TOLERANCE:
            raise ValueError(
                f"{interface_id}: pinned candidate/host normals are not opposed"
            )
        candidate_point = _vec3(
            datum.get("origin_global_xyz_mm"), f"{interface_id} contact plane point"
        )
        host_point = _vec3(
            host.get("center_global_xyz_mm"), f"{interface_id} host plane point"
        )
        host_plane_offset = abs(
            _dot(_sub(host_point, candidate_point), candidate_normal)
        )
        probe_min_pair_distance = float(probe.get("minimum_pair_distance_mm"))
        probe_max_pair_distance = float(probe.get("maximum_pair_distance_mm"))
        selection_tolerance = float(overlap.get("plane_selection_tolerance_mm"))
        if (
            not math.isfinite(probe_min_pair_distance)
            or not math.isfinite(probe_max_pair_distance)
            or not math.isfinite(selection_tolerance)
            or probe_min_pair_distance < 0
            or probe_min_pair_distance > probe_max_pair_distance
            or probe_max_pair_distance > selection_tolerance
            or host_plane_offset > PLANE_DISTANCE_TOLERANCE_MM
        ):
            raise ValueError(
                f"{interface_id}: source face pair is outside pinned plane tolerance"
            )

        candidate_matches = []
        for tag, surface in surface_index[candidate_id].items():
            evidence = _sample_plane_match(
                surface, candidate_point, candidate_normal, node_coordinates
            )
            if evidence is not None:
                candidate_matches.append((tag, surface, evidence))
        host_matches = []
        for tag, surface in surface_index[host_id].items():
            evidence = _sample_plane_match(
                surface, host_point, host_normal, node_coordinates
            )
            if evidence is not None:
                host_matches.append((tag, surface, evidence))
        if not candidate_matches or not host_matches:
            raise ValueError(
                f"{interface_id}: one or both analytic contact planes were not found"
            )
        candidate_mesh_area = math.fsum(row[1]["area_mm2"] for row in candidate_matches)
        host_mesh_area = math.fsum(row[1]["area_mm2"] for row in host_matches)
        if not _area_close(candidate_mesh_area, candidate_area):
            raise ValueError(
                f"{interface_id}: trimmed cleat mesh plane area differs from archive"
            )
        if not _area_close(host_mesh_area, host_area):
            raise ValueError(
                f"{interface_id}: trimmed host mesh plane area differs from archive"
            )

        expected_bolts = row.get("physical_bolt_ids")
        actual_bolts = [
            bolt.get("physical_bolt_id")
            for bolt in inventory.get("physical_bolts", [])
            if bolt.get("interface_id") == interface_id
        ]
        if expected_bolts != actual_bolts:
            raise ValueError(
                f"{interface_id}: bolt-to-interface membership/order changed"
            )
        classified.append(
            {
                "interface_id": interface_id,
                "candidate_member_id": candidate_id,
                "host_member_id": host_id,
                "physical_bolt_ids": expected_bolts,
                "candidate_surfaces": [
                    {
                        **_surface_pointer(candidate_id, tag),
                        "trimmed_area_mm2": surface["area_mm2"],
                        **evidence,
                    }
                    for tag, surface, evidence in candidate_matches
                ],
                "host_surfaces": [
                    {
                        **_surface_pointer(host_id, tag),
                        "trimmed_area_mm2": surface["area_mm2"],
                        **evidence,
                    }
                    for tag, surface, evidence in host_matches
                ],
                "candidate_trimmed_surface_area_mm2": candidate_mesh_area,
                "expected_candidate_planar_area_mm2": candidate_area,
                "host_trimmed_surface_area_mm2": host_mesh_area,
                "expected_host_planar_area_mm2": host_area,
                "archived_finite_common_area_mm2": common_area,
                "candidate_common_area_fraction": common_area / candidate_area,
                "host_area_is_not_equated_to_common_footprint": True,
                "source_finite_overlap_method": overlap["method"],
                "source_finite_overlap_tolerance_mm": selection_tolerance,
                "pinned_outward_datum_normal_dot": normal_opposition,
                "mesh_sample_normal_convention": (
                    "Gmsh parametric normals are matched unsigned by absolute dot; "
                    "they are not interpreted as outward or signed contact normals"
                ),
                "mesh_outward_normal_verified": False,
                "contact_law_assigned": False,
                "active_pressure_established": False,
            }
        )
    return classified


def _bore_axis_geometry(bolt: dict[str, Any]) -> dict[str, Any]:
    axis_id = bolt.get("physical_bolt_id")
    if axis_id not in EXPECTED_BOLT_IDS:
        raise ValueError(f"unexpected physical bolt ID: {axis_id}")
    stack_id = bolt.get("stack_spec_id")
    if (
        stack_id not in EXPECTED_RECEIVER_THICKNESS_MM
        or axis_id != mesh_contract.G7_AXIS_PREFIX + stack_id
        or bolt.get("interface_id") != EXPECTED_INTERFACE_BY_STACK[stack_id]
    ):
        raise ValueError(f"{axis_id}: physical axis/stack/interface binding changed")
    origin = _vec3(bolt.get("world_axis_origin_xyz_mm"), f"{axis_id} axis origin")
    direction = _unit(
        bolt.get("world_axis_direction_head_to_nut"), f"{axis_id} head-to-nut direction"
    )
    receivers = bolt.get("receivers_head_to_nut")
    if (
        not isinstance(receivers, list)
        or len(receivers) != 2
        or any(not isinstance(receiver, dict) for receiver in receivers)
    ):
        raise ValueError(f"{axis_id}: expected two ordered wood receivers")
    if tuple(receiver.get("member_id") for receiver in receivers) != tuple(
        mesh_contract.STACK_RECEIVERS[stack_id]
    ):
        raise ValueError(
            f"{axis_id}: ordered receiver identities differ from pinned stack map"
        )
    thicknesses = tuple(
        _positive(receiver.get("wood_thickness_mm"), f"{axis_id} wood thickness")
        for receiver in receivers
    )
    if thicknesses != EXPECTED_RECEIVER_THICKNESS_MM[stack_id]:
        raise ValueError(
            f"{axis_id}: ordered receiver thicknesses differ from pinned members"
        )
    grip = math.fsum(thicknesses)
    if not math.isclose(grip, 127.0, abs_tol=1e-8) or bolt.get("wood_grip_mm") != 127.0:
        raise ValueError(f"{axis_id}: authenticated wood grip differs from 127 mm")
    # The STEP inventory omits this manifest field. The pinned source declares
    # 0.1 mm at each end; the derived diameter is then cross-checked against the
    # independently archived bore volume and XYZ bounds below.
    bore = bolt.get("composed_occupancy_bore")
    if not isinstance(bore, dict) or bore.get("solid_count") != 1:
        raise ValueError(f"{axis_id}: composed occupancy bore metadata is incomplete")
    bore_length = grip + 2 * BORE_EXTENSION_EACH_END_MM
    radius = math.sqrt(
        _positive(bore.get("volume_mm3"), f"{axis_id} bore volume")
        / (math.pi * bore_length)
    )
    start = _sub(origin, _scale(direction, BORE_EXTENSION_EACH_END_MM))
    end = tuple(a + b * bore_length for a, b in zip(start, direction, strict=True))
    expected_bounds = []
    for coordinate in range(3):
        transverse = radius * math.sqrt(max(0.0, 1.0 - direction[coordinate] ** 2))
        expected_bounds.extend(
            (
                min(start[coordinate], end[coordinate]) - transverse,
                max(start[coordinate], end[coordinate]) + transverse,
            )
        )
    actual_bounds = _vec3_pair(bore.get("bounds_xyz_mm"), f"{axis_id} bore bounds")
    if any(actual_bounds[index] > actual_bounds[index + 1] for index in (0, 2, 4)):
        raise ValueError(
            f"{axis_id}: bore bounds are inverted or not axis-pair ordered"
        )
    if any(
        abs(a - b) > 1e-6 for a, b in zip(actual_bounds, expected_bounds, strict=True)
    ):
        raise ValueError(
            f"{axis_id}: bore volume-derived radius disagrees with axis bounds"
        )
    return {
        "axis_id": axis_id,
        "stack_spec_id": stack_id,
        "interface_id": bolt["interface_id"],
        "origin": origin,
        "direction": direction,
        "receivers": receivers,
        "thicknesses": thicknesses,
        "wood_grip_mm": grip,
        "extension_mm": BORE_EXTENSION_EACH_END_MM,
        "bore_length_mm": bore_length,
        "radius_mm": radius,
        "bore_volume_mm3": float(bore["volume_mm3"]),
        "bore_bounds_xyz_mm": actual_bounds,
    }


def _vec3_pair(
    value: Any, context: str
) -> tuple[float, float, float, float, float, float]:
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected six finite bounds") from error
    if len(result) != 6 or not all(math.isfinite(component) for component in result):
        raise ValueError(f"{context}: expected six finite bounds")
    return result  # type: ignore[return-value]


def _cylinder_surface_match(
    surface: dict[str, Any],
    node_coordinates: dict[int, tuple[float, float, float]],
    axis: dict[str, Any],
    layer_start: float,
    layer_end: float,
) -> dict[str, float] | None:
    if str(surface.get("cad_type", "")).casefold() != "cylinder":
        return None
    analytic = surface.get("analytic_surface_data")
    if (
        not isinstance(analytic, dict)
        or str(analytic.get("surface_type", "")).casefold() != "cylinder"
    ):
        return None
    try:
        sample_point = _vec3(analytic.get("sample_xyz_mm"), "cylinder sample point")
        sample_normal = _unit(
            analytic.get("sample_normal_global"), "cylinder sample normal"
        )
        node_ids = tuple(int(value) for value in surface["tri6_node_ids"])
        points = tuple(node_coordinates[node_id] for node_id in node_ids)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    origin = axis["origin"]
    direction = axis["direction"]
    radius = axis["radius_mm"]

    def radial_at(
        point: tuple[float, float, float],
    ) -> tuple[float, float, float, float]:
        offset = _sub(point, origin)
        station = _dot(offset, direction)
        radial = tuple(offset[index] - station * direction[index] for index in range(3))
        return station, _norm(radial), radial[0], radial[1], radial[2]

    samples = tuple(radial_at(point) for point in points)
    station_values = tuple(sample[0] for sample in samples)
    radial_errors = tuple(abs(sample[1] - radius) for sample in samples)
    sample_station, sample_radius, sample_rx, sample_ry, sample_rz = radial_at(
        sample_point
    )
    sample_radial = (sample_rx, sample_ry, sample_rz)
    if _norm(sample_radial) <= 1e-12:
        return None
    sample_radial_unit = _unit(sample_radial, "cylinder sample radial vector")
    sample_normal_dot_axis = abs(_dot(sample_normal, direction))
    sample_normal_radial_alignment = abs(_dot(sample_normal, sample_radial_unit))
    if (
        max(radial_errors, default=math.inf) > CYLINDER_RADIAL_TOLERANCE_MM
        or min(station_values, default=math.inf)
        < layer_start - CYLINDER_STATION_TOLERANCE_MM
        or max(station_values, default=-math.inf)
        > layer_end + CYLINDER_STATION_TOLERANCE_MM
        or sample_radius - radius > CYLINDER_RADIAL_TOLERANCE_MM
        or radius - sample_radius > CYLINDER_RADIAL_TOLERANCE_MM
        or sample_station < layer_start - CYLINDER_STATION_TOLERANCE_MM
        or sample_station > layer_end + CYLINDER_STATION_TOLERANCE_MM
        or sample_normal_dot_axis > NORMAL_DOT_TOLERANCE
        or sample_normal_radial_alignment < 1 - NORMAL_DOT_TOLERANCE
    ):
        return None
    return {
        "maximum_tri6_node_radial_residual_mm": max(radial_errors),
        "minimum_axis_station_mm": min(station_values),
        "maximum_axis_station_mm": max(station_values),
        "sample_axis_station_mm": sample_station,
        "sample_radial_residual_mm": abs(sample_radius - radius),
        "absolute_sample_normal_dot_axis": sample_normal_dot_axis,
        "absolute_sample_normal_radial_dot": sample_normal_radial_alignment,
    }


def _classify_bore_pairs(
    surface_index: dict[str, dict[str, dict[str, Any]]],
    node_coordinates: dict[int, tuple[float, float, float]],
    inventory: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bolt_rows = inventory.get("physical_bolts")
    if not isinstance(bolt_rows, list) or len(bolt_rows) != 8:
        raise ValueError(
            "frozen inventory must contain exactly eight physical G7 bolts"
        )
    bolt_by_id = {row.get("physical_bolt_id"): row for row in bolt_rows}
    if set(bolt_by_id) != EXPECTED_BOLT_IDS:
        raise ValueError(
            "frozen inventory physical bolt IDs differ from exact eight-axis set"
        )
    geometry = {
        axis_id: _bore_axis_geometry(row) for axis_id, row in bolt_by_id.items()
    }

    candidate_rows: list[dict[str, Any]] = []
    classified_surface_keys: set[tuple[str, str]] = set()
    surface_match_count: dict[tuple[str, str], int] = {}
    for axis_id in sorted(geometry):
        axis = geometry[axis_id]
        station = 0.0
        for receiver, thickness in zip(
            axis["receivers"], axis["thicknesses"], strict=True
        ):
            member_id = receiver["member_id"]
            layer_start, layer_end = station, station + thickness
            station = layer_end
            matched = []
            for tag, surface in surface_index[member_id].items():
                evidence = _cylinder_surface_match(
                    surface,
                    node_coordinates,
                    axis,
                    layer_start,
                    layer_end,
                )
                if evidence is not None:
                    matched.append((tag, surface, evidence))
                    key = (member_id, tag)
                    surface_match_count[key] = surface_match_count.get(key, 0) + 1
            if not matched:
                raise ValueError(
                    f"{axis_id}/{member_id}: no cylinder wall matches the authenticated axis"
                )
            area = math.fsum(surface["area_mm2"] for _tag, surface, _ev in matched)
            expected_area = 2 * math.pi * axis["radius_mm"] * thickness
            if not _area_close(area, expected_area):
                raise ValueError(
                    f"{axis_id}/{member_id}: matched trimmed cylinder wall area "
                    "does not cover the authenticated receiver thickness"
                )
            station_min = min(
                ev["minimum_axis_station_mm"] for _tag, _surface, ev in matched
            )
            station_max = max(
                ev["maximum_axis_station_mm"] for _tag, _surface, ev in matched
            )
            if (
                abs(station_min - layer_start) > CYLINDER_STATION_TOLERANCE_MM
                or abs(station_max - layer_end) > CYLINDER_STATION_TOLERANCE_MM
            ):
                raise ValueError(
                    f"{axis_id}/{member_id}: cylinder wall does not span the full wood layer"
                )
            classified_surface_keys.update(
                (member_id, tag) for tag, _surface, _ev in matched
            )
            candidate_rows.append(
                {
                    "semantic_pair_id": f"{axis_id}::{member_id}",
                    "physical_bolt_id": axis_id,
                    "stack_spec_id": axis["stack_spec_id"],
                    "interface_id": axis["interface_id"],
                    "member_id": member_id,
                    "receiver_order_head_to_nut": [
                        item["member_id"] for item in axis["receivers"]
                    ],
                    "receiver_layer_station_mm": [layer_start, layer_end],
                    "axis_origin_xyz_mm": list(axis["origin"]),
                    "axis_direction_head_to_nut": list(axis["direction"]),
                    "analysis_occupancy_bore_radius_mm": axis["radius_mm"],
                    "radius_basis": (
                        "sqrt(archived occupancy-cylinder volume / "
                        "(pi * (wood grip + both 0.1 mm probe extensions)))"
                    ),
                    "bore_extension_source": {
                        "source_path": MECHANICS_CONTRACT_SOURCE,
                        "source_sha256": MECHANICS_CONTRACT_SOURCE_SHA256,
                        "extension_each_end_mm": BORE_EXTENSION_EACH_END_MM,
                    },
                    "occupancy_bore_is_hardware_or_drill_instruction": False,
                    "matched_surfaces": [
                        {
                            **_surface_pointer(member_id, tag),
                            "trimmed_area_mm2": surface["area_mm2"],
                            **evidence,
                        }
                        for tag, surface, evidence in matched
                    ],
                    "matched_trimmed_wall_area_mm2": area,
                    "full_cylindrical_wall_area_mm2": expected_area,
                    "wall_area_fraction": area / expected_area,
                    "maximum_radial_residual_mm": max(
                        ev["maximum_tri6_node_radial_residual_mm"]
                        for _tag, _surface, ev in matched
                    ),
                    "contact_or_strength_result": False,
                }
            )
    if any(count != 1 for count in surface_match_count.values()):
        raise ValueError(
            "one mesh cylinder surface ambiguously matches multiple physical axes"
        )

    unclassified = []
    for member_id, rows in surface_index.items():
        for tag, surface in rows.items():
            if (
                str(surface.get("cad_type", "")).casefold() == "cylinder"
                and (
                    member_id,
                    tag,
                )
                not in classified_surface_keys
            ):
                unclassified.append(
                    {
                        **_surface_pointer(member_id, tag),
                        "trimmed_area_mm2": surface["area_mm2"],
                        "status": "not_matched_to_any_authenticated_WJ04_physical_bolt_axis",
                        "classification_limit": (
                            "No hole purpose inferred from Gmsh tag, list order, or broad bounds."
                        ),
                    }
                )
    if len(candidate_rows) != 16:
        raise ValueError(
            "candidate bore classification did not resolve all eight-by-two receiver pairs"
        )
    return candidate_rows, unclassified


def classify_surfaces(
    mesh_record: dict[str, Any],
    node_coordinates: dict[int, tuple[float, float, float]],
    inventory: dict[str, Any],
    overlap: dict[str, Any],
    *,
    elements_by_body: dict[str, dict[int, tuple[int, ...]]] | None = None,
) -> dict[str, Any]:
    """Pure source-contract classifier, suitable for synthetic geometry fixtures."""
    _validate_mechanics_contract_source()
    mesh_contract._validate_inventory_contract(inventory)
    surface_index = _validate_mesh_surface_inventory(
        mesh_record, node_coordinates, elements_by_body
    )
    if overlap.get("status") != OVERLAP_SCHEMA_STATUS:
        raise ValueError(
            "finite overlap evidence is not the parent archived face probe"
        )
    if overlap.get("inventory_sha256") != PATCH_INVENTORY_SHA256:
        raise ValueError(
            "finite overlap evidence belongs to a different patch inventory"
        )
    if (
        overlap.get("native_solve_run") is not False
        or overlap.get("release") is not False
    ):
        raise ValueError(
            "finite overlap evidence contains an out-of-scope solve or release flag"
        )
    if overlap.get("pressure_or_capacity_established") is True:
        raise ValueError(
            "finite overlap evidence cannot establish pressure or capacity"
        )
    if not math.isclose(
        float(overlap.get("plane_selection_tolerance_mm")),
        PLANE_DISTANCE_TOLERANCE_MM,
        abs_tol=1e-15,
    ):
        raise ValueError(
            "finite overlap plane tolerance differs from classifier tolerance"
        )
    contacts = _classify_contact_interfaces(
        surface_index, node_coordinates, inventory, overlap
    )
    bores, other_cylinders = _classify_bore_pairs(
        surface_index, node_coordinates, inventory
    )
    return {
        "schema": SCHEMA,
        "status": "SOURCE_BOUND_GEOMETRIC_SURFACE_CLASSIFICATION_ONLY",
        "limits": LIMITS,
        "accepted": False,
        "native_solve_run": False,
        "contact_law_assigned": False,
        "active_contact_pressure_established": False,
        "capacity_or_release_claim": False,
        "tolerances": {
            "plane_distance_mm": PLANE_DISTANCE_TOLERANCE_MM,
            "cylinder_radial_residual_mm": CYLINDER_RADIAL_TOLERANCE_MM,
            "cylinder_layer_station_mm": CYLINDER_STATION_TOLERANCE_MM,
            "normal_absolute_dot_tolerance": NORMAL_DOT_TOLERANCE,
            "area_absolute_tolerance_mm2": AREA_ABSOLUTE_TOLERANCE_MM2,
            "area_relative_tolerance": AREA_RELATIVE_TOLERANCE,
            "area_comparison_rule": "max(absolute tolerance, relative tolerance * expected area)",
        },
        "normal_convention": {
            "coordinates": "world XYZ",
            "candidate_and_source_outward_datum_normals": (
                "inventory normals are signed and checked opposed; the finite OCC probe pairs the surfaces"
            ),
            "Gmsh_analytic_sample_normals": (
                "treated as unsigned support normals using absolute dot; no outward sign is inferred"
            ),
            "mesh_outward_normals": "not reconstructed or validated in this stage",
            "bolt_axis": "world_axis_direction_head_to_nut; receiver layer stations use ordered thicknesses",
        },
        "wood_contact_pairs": contacts,
        "candidate_bore_member_pairs": bores,
        "physical_bolt_bore_contact": {
            "status": "not_modeled",
            "physical_hardware_roles_meshed": 0,
            "initial_lateral_contact_or_seating": "not represented",
            "bolt_shank_to_bore_clearance_contact": "not represented",
            "contact_or_preload_inference": False,
        },
        "unclassified_cylindrical_surfaces": other_cylinders,
        "unclassified_cylindrical_surface_count": len(other_cylinders),
    }


def _read_json(path: Path, context: str) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{context} is missing or invalid: {path}") from error
    if not isinstance(result, dict):
        raise TypeError(f"{context} root must be a JSON object")
    return result


def _load_overlap_archive(
    overlap_directory: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    index_path = overlap_directory / "sha256.json"
    probe_path = overlap_directory / "finite-face-overlap.json"
    execution_path = overlap_directory / "execution.json"
    index_bytes = index_path.read_bytes()
    if sha256_bytes(index_bytes) != OVERLAP_HASH_INDEX_SHA256:
        raise ValueError("archived finite-face overlap hash index changed")
    index = json.loads(index_bytes)
    expected = {
        "finite-face-overlap.json": OVERLAP_SHA256,
        "finite_face_overlap_probe.py.snapshot": OVERLAP_PRODUCER_SHA256,
        "execution.json": OVERLAP_EXECUTION_SHA256,
    }
    if any(index.get(name) != value for name, value in expected.items()):
        raise ValueError("archived finite-face overlap source pins changed")
    if sha256_file(probe_path) != OVERLAP_SHA256:
        raise ValueError("archived finite-face overlap data changed")
    if sha256_file(execution_path) != OVERLAP_EXECUTION_SHA256:
        raise ValueError("finite-face overlap execution record changed")
    if (
        sha256_file(overlap_directory / "finite_face_overlap_probe.py.snapshot")
        != OVERLAP_PRODUCER_SHA256
    ):
        raise ValueError("finite-face overlap producer snapshot changed")
    probe = _read_json(probe_path, "finite-face overlap report")
    execution = _read_json(execution_path, "finite-face overlap execution record")
    if (
        execution.get("inventory_sha256") != PATCH_INVENTORY_SHA256
        or execution.get("release") is not False
    ):
        raise ValueError(
            "finite-face overlap execution is bound to a different or released inventory"
        )
    return probe, {
        "sha256.json": OVERLAP_HASH_INDEX_SHA256,
        "finite-face-overlap.json": OVERLAP_SHA256,
        "execution.json": OVERLAP_EXECUTION_SHA256,
        "finite_face_overlap_probe.py.snapshot": OVERLAP_PRODUCER_SHA256,
    }


def classify_frozen_mesh(
    mesh_directory: str | Path,
    output_path: str | Path,
    *,
    bundle_directory: str | Path | None = None,
    overlap_directory: str | Path | None = None,
) -> Path:
    """Classify the exact parent mesh attempt; refuses any source/output drift."""
    mesh_dir = Path(mesh_directory).expanduser().resolve()
    bundle_dir = (
        Path(bundle_directory).expanduser().resolve()
        if bundle_directory is not None
        else ROOT / PATCH_BUNDLE_RELATIVE
    )
    overlap_dir = (
        Path(overlap_directory).expanduser().resolve()
        if overlap_directory is not None
        else ROOT / OVERLAP_ARCHIVE_RELATIVE
    )
    output = Path(output_path).expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"classification output already exists: {output}")
    mesh_json_path = mesh_dir / "mesh.json"
    mesh_input_path = mesh_dir / "mesh.inp"
    if sha256_file(mesh_json_path) != MESH_REPORT_SHA256:
        raise ValueError("WJ04 mesh report differs from the frozen parent attempt-03")
    if sha256_file(mesh_input_path) != MESH_INPUT_SHA256:
        raise ValueError("WJ04 mesh input differs from the frozen parent attempt-03")
    mesh_record = _read_json(mesh_json_path, "WJ04 mesh report")
    worker_hashes = mesh_record.get("mesh_worker_source_sha256")
    if (
        not isinstance(worker_hashes, dict)
        or set(worker_hashes) != set(mesh_contract.WORKER_SOURCE_PATHS)
        or worker_hashes.get("fea/wood_joint_patch_mesh.py") != MESH_WORKER_SHA256
        or mesh_record.get("mesh_worker_source_sha256_after") != worker_hashes
    ):
        raise ValueError("mesh report was produced by another worker source snapshot")
    source_paths = {
        "classifier_source": Path(__file__).resolve(),
        MECHANICS_CONTRACT_SOURCE: ROOT / MECHANICS_CONTRACT_SOURCE,
        **{f"mesh_worker/{relative}": ROOT / relative for relative in worker_hashes},
    }
    source_hashes_before = {
        label: sha256_file(path) for label, path in source_paths.items()
    }
    for relative, digest in worker_hashes.items():
        if source_hashes_before[f"mesh_worker/{relative}"] != digest:
            raise ValueError(
                f"live mesh worker source differs from frozen attempt: {relative}"
            )
    if (
        source_hashes_before[MECHANICS_CONTRACT_SOURCE]
        != MECHANICS_CONTRACT_SOURCE_SHA256
    ):
        raise ValueError(
            "pinned full-stock mechanics source changed before classification"
        )

    bundle = mesh_contract.load_geometry_bundle(bundle_dir)
    if (
        bundle["inventory_sha256"] != PATCH_INVENTORY_SHA256
        or bundle["hash_index_sha256"] != PATCH_HASH_INDEX_SHA256
    ):
        raise ValueError("patch bundle inventory differs from frozen classifier inputs")
    if mesh_record.get("input_bundle_hash_index_sha256") != PATCH_HASH_INDEX_SHA256:
        raise ValueError("mesh report patch-bundle hash-index pin changed")
    if (
        mesh_record.get("input_bundle_file_sha256_before")
        != bundle["input_file_sha256"]
    ):
        raise ValueError("mesh report and live patch bundle input hashes differ")
    if mesh_record.get("input_bundle_file_sha256_after") != bundle["input_file_sha256"]:
        raise ValueError("mesh report patch-bundle hashes changed during its run")
    for relative, digest in worker_hashes.items():
        source_snapshot = mesh_dir / "sources" / f"{relative}.snapshot"
        if not source_snapshot.is_file() or sha256_file(source_snapshot) != digest:
            raise ValueError(f"mesh source snapshot changed: {relative}")
    overlap, overlap_hashes = _load_overlap_archive(overlap_dir)
    node_coordinates, elements_by_body = parse_mesh_deck(mesh_input_path)
    pure_record = classify_surfaces(
        mesh_record,
        node_coordinates,
        bundle["inventory"],
        overlap,
        elements_by_body=elements_by_body,
    )
    overlap_hashes_after = _load_overlap_archive(overlap_dir)[1]
    if overlap_hashes_after != overlap_hashes:
        raise ValueError("finite-face archive changed during classification")
    source_hashes_after = {
        label: sha256_file(path) for label, path in source_paths.items()
    }
    if source_hashes_after != source_hashes_before:
        raise ValueError(
            "classifier or mesh helper source changed during classification"
        )
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"classification output appeared during work: {output}")
    source_hashes = {
        "mesh.json": MESH_REPORT_SHA256,
        "mesh.inp": MESH_INPUT_SHA256,
        **{
            f"patch_bundle/{name}": digest
            for name, digest in bundle["input_file_sha256"].items()
        },
        **{
            f"finite_face_archive/{name}": digest
            for name, digest in overlap_hashes.items()
        },
        **source_hashes_after,
    }
    if (
        sha256_file(mesh_json_path) != MESH_REPORT_SHA256
        or sha256_file(mesh_input_path) != MESH_INPUT_SHA256
    ):
        raise ValueError("frozen mesh input changed during classification")
    if (
        mesh_contract.load_geometry_bundle(bundle_dir)["input_file_sha256"]
        != bundle["input_file_sha256"]
    ):
        raise ValueError("frozen patch bundle changed during classification")
    record = {
        **pure_record,
        "source_hashes": source_hashes,
        "mesh_runtime": mesh_record.get("runtime"),
        "mesh_configuration": mesh_record.get("configuration"),
        "mesh_counts": {
            "wood_bodies": mesh_record.get("body_count"),
            "nodes": mesh_record.get("node_count"),
            "c3d10_elements": mesh_record.get("element_count"),
            "physical_bolts": 8,
            "physical_hardware_roles_not_meshed": 40,
        },
        "classifier_runtime": {"python": platform.python_version()},
    }
    write_json(output, record)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mesh_directory", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--bundle-directory", type=Path)
    parser.add_argument("--overlap-directory", type=Path)
    args = parser.parse_args()
    print(
        classify_frozen_mesh(
            args.mesh_directory,
            args.output_json,
            bundle_directory=args.bundle_directory,
            overlap_directory=args.overlap_directory,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
