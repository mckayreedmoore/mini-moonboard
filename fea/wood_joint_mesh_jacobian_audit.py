"""Independently audit C3D10 Gauss5 Jacobians and volume from a saved deck.

This module reads a CalculiX C3D10 mesh and its mesh-only report. It does not
import Gmsh or CAD libraries, create or alter a mesh, or run a solver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "c3d10_gauss5_independent_jacobian_audit/v1"
EXPECTED_GMSH_VERSION = "4.12.1"
EXPECTED_SCENARIO_ID = "body_to_far_wood_face"
EXPECTED_REPORT_SCHEMA = "wood_joint_wj04_hardware_patch_mesh/v1"
EXPECTED_REPORT_STATUS = "VERIFIED_C3D10_PHYSICAL_METAL_MESH_ONLY_NO_SOLVER"
EXPECTED_HARDWARE_BODY_IDS = frozenset(
    f"{stack_id}__{role}"
    for stack_id in (
        "lower_rail_1",
        "lower_rail_2",
        "lower_principal_1",
        "lower_principal_2",
        "upper_rail_1",
        "upper_rail_2",
        "upper_principal_1",
        "upper_principal_2",
    )
    for role in ("bolt", "head_washer", "nut_washer", "nut")
)
EXPECTED_BODY_IDS = EXPECTED_HARDWARE_BODY_IDS
EXPECTED_WJ24_WOOD_REPORT_SCHEMA = "wood_joint_wj24_patch_mesh/v1"
EXPECTED_WJ24_WOOD_REPORT_STATUS = "VERIFIED_WJ24_C3D10_MESH_ONLY_NO_SOLVER"
EXPECTED_WJ24_WOOD_BODY_ID_ORDER = (
    "base_rail_service_lower_right",
    "base_rail_service_upper_right",
    "base_principal_center_right",
    "wj04_lower_full_stock_cleat",
    "wj04_upper_g7_crosscut_full_stock_cleat",
)
EXPECTED_WJ24_WOOD_BODY_IDS = frozenset(EXPECTED_WJ24_WOOD_BODY_ID_ORDER)
EXPECTED_WJ24_CALCULIX_ELSET_PREFIX = ""
EXPECTED_HARDWARE_CALCULIX_ELSET_PREFIX = "METAL_"


@dataclass(frozen=True)
class MeshReportContract:
    profile: str
    report_schema: str
    report_status: str
    body_ids: frozenset[str]
    body_order: tuple[str, ...]
    calculix_elset_prefix: str
    source_volume_field: str


HARDWARE_REPORT_CONTRACT = MeshReportContract(
    profile="wj04_physical_hardware",
    report_schema=EXPECTED_REPORT_SCHEMA,
    report_status=EXPECTED_REPORT_STATUS,
    body_ids=EXPECTED_HARDWARE_BODY_IDS,
    body_order=tuple(sorted(EXPECTED_HARDWARE_BODY_IDS)),
    calculix_elset_prefix=EXPECTED_HARDWARE_CALCULIX_ELSET_PREFIX,
    source_volume_field="imported_cad",
)
WJ24_WOOD_REPORT_CONTRACT = MeshReportContract(
    profile="wj24_finished_wood",
    report_schema=EXPECTED_WJ24_WOOD_REPORT_SCHEMA,
    report_status=EXPECTED_WJ24_WOOD_REPORT_STATUS,
    body_ids=EXPECTED_WJ24_WOOD_BODY_IDS,
    body_order=EXPECTED_WJ24_WOOD_BODY_ID_ORDER,
    calculix_elset_prefix=EXPECTED_WJ24_CALCULIX_ELSET_PREFIX,
    source_volume_field="WJ24_finished_geometry",
)

# Gmsh 4.12.1's order-five symmetric tetrahedron rule (tetP5Solin[14]).
# Coordinates are (r, s, t) in the reference tetrahedron; weights integrate
# over its volume 1/6. Source: https://gmsh.info/src/gmsh-4.12.1-source.tgz,
# src/numeric/GaussQuadratureTet.cpp; source archive SHA-256 is recorded below.
GMSH_SOURCE_ARCHIVE_URL = "https://gmsh.info/src/gmsh-4.12.1-source.tgz"
GMSH_SOURCE_ARCHIVE_SHA256 = "59ee2118ba7b099e9d1502572c9af4221501af955103d2b687aaa3890d13325e"
GMSH_TETRA_RULE_SOURCE_SHA256 = "d09ae2bd9a21927daf4e272e25dfd516bf453d0b78a8ecc66100603be4c3c24f"
GMSH_TETRA_RULE_SOURCE_PATH = "src/numeric/GaussQuadratureTet.cpp"
GAUSS5_TETRAHEDRON_14: tuple[tuple[tuple[float, float, float], float], ...] = (
    ((0.0927352503109, 0.0927352503109, 0.0927352503109), 0.01224884051940),
    ((0.7217942490670, 0.0927352503109, 0.0927352503109), 0.01224884051940),
    ((0.0927352503109, 0.7217942490670, 0.0927352503109), 0.01224884051940),
    ((0.0927352503109, 0.0927352503109, 0.7217942490670), 0.01224884051940),
    ((0.3108859192630, 0.3108859192630, 0.3108859192630), 0.01878132095300),
    ((0.0673422422101, 0.3108859192630, 0.3108859192630), 0.01878132095300),
    ((0.3108859192630, 0.0673422422101, 0.3108859192630), 0.01878132095300),
    ((0.3108859192630, 0.3108859192630, 0.0673422422101), 0.01878132095300),
    ((0.4544962958740, 0.4544962958740, 0.0455037041256), 0.00709100346285),
    ((0.4544962958740, 0.0455037041256, 0.4544962958740), 0.00709100346285),
    ((0.0455037041256, 0.4544962958740, 0.4544962958740), 0.00709100346285),
    ((0.4544962958740, 0.0455037041256, 0.0455037041256), 0.00709100346285),
    ((0.0455037041256, 0.4544962958740, 0.0455037041256), 0.00709100346285),
    ((0.0455037041256, 0.0455037041256, 0.4544962958740), 0.00709100346285),
)

# Standard CalculiX C3D10 ordering: vertices 1-4 followed by edge nodes
# (1-2), (2-3), (3-1), (1-4), (2-4), (3-4). The producer swaps Gmsh's final
# two quadratic edge nodes before writing the deck.
TETRAHEDRON_VERTEX_DERIVATIVES = (
    (-1.0, -1.0, -1.0),
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)
TETRAHEDRON_EDGE_VERTICES = (
    (0, 1),
    (1, 2),
    (2, 0),
    (0, 3),
    (1, 3),
    (2, 3),
)


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _finite_float(value: Any, context: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{context}: expected a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected a finite number") from error
    if not math.isfinite(number):
        raise ValueError(f"{context}: expected a finite number")
    return number


def _positive_int(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{context}: expected a positive integer")
    return value


def _source_geometry_volume(
    report_body: dict[str, Any], contract: MeshReportContract, body_id: str
) -> float:
    if contract.source_volume_field not in report_body:
        raise ValueError(
            f"{body_id}: missing {contract.source_volume_field} source geometry record"
        )
    source_geometry = report_body.get(contract.source_volume_field)
    if not isinstance(source_geometry, dict):
        raise TypeError(f"{body_id}: {contract.source_volume_field} must be an object")
    volume = _finite_float(
        source_geometry.get("volume_mm3"),
        f"{body_id} {contract.source_volume_field}.volume_mm3",
    )
    if volume <= 0:
        raise ValueError(
            f"{body_id}: {contract.source_volume_field}.volume_mm3 must be positive"
        )
    return volume


def validate_mesh_report_contract(
    report: dict[str, Any],
) -> tuple[MeshReportContract, dict[str, dict[str, Any]]]:
    """Validate a supported report profile before parsing its mesh deck.

    WJ04 physical-hardware and WJ24 finished-wood mesh reports are distinct
    inputs. Their report schema, status, exact body identities, deck element-set
    names and source-volume fields are selected as one indivisible contract.
    """
    report_schema = report.get("schema")
    if report_schema == HARDWARE_REPORT_CONTRACT.report_schema:
        contract = HARDWARE_REPORT_CONTRACT
    elif report_schema == WJ24_WOOD_REPORT_CONTRACT.report_schema:
        contract = WJ24_WOOD_REPORT_CONTRACT
    else:
        raise ValueError(f"unsupported C3D10 mesh report schema: {report_schema!r}")

    if report.get("status") != contract.report_status:
        raise ValueError(
            f"mesh report status does not match the {contract.profile} contract"
        )
    if contract is HARDWARE_REPORT_CONTRACT:
        if report.get("scenario_id") != EXPECTED_SCENARIO_ID:
            raise ValueError("mesh report scenario is not the pinned body-to-far-wood-face profile")
        if report.get("gmsh_to_calculix_quadratic_node_order") != [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            9,
            8,
        ]:
            raise ValueError("mesh report C3D10 node-order transform differs from the pinned map")
    else:
        if report.get("body_count") != len(contract.body_ids):
            raise ValueError("WJ24 mesh report body count differs from the exact five-body contract")
        if report.get("completed_body_ids") != list(contract.body_order):
            raise ValueError("WJ24 completed body IDs differ from the exact five-body contract")
        mesh_scope = report.get("mesh_scope")
        if not isinstance(mesh_scope, dict) or any(
            mesh_scope.get(key) != expected
            for key, expected in {
                "WJ24_baseline_only": True,
                "WJ24_finished_wood_bodies": len(contract.body_ids),
                "hardware_bodies_meshed": 0,
                "independent_body_models": len(contract.body_ids),
            }.items()
        ):
            raise ValueError("WJ24 mesh scope differs from the exact baseline finished-wood contract")
        if report.get("WJ24_G7_relief_variant_included") is not False:
            raise ValueError("WJ24 mesh report is not the pinned baseline without a G7 relief variant")
        for key in (
            "accepted",
            "solved",
            "capacity_or_release_claim",
            "full_candidate_acceptance_claim",
            "contact_or_interface_classification_assigned",
            "output_contains_material_contact_tie_load_or_solver_cards",
        ):
            if report.get(key) is not False:
                raise ValueError(f"WJ24 mesh report exceeds its geometry-only scope: {key}")

    runtime = report.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("gmsh_version") != EXPECTED_GMSH_VERSION:
        raise ValueError(f"mesh report does not use pinned Gmsh {EXPECTED_GMSH_VERSION}")

    reported_bodies = report.get("bodies")
    if not isinstance(reported_bodies, dict) or set(reported_bodies) != contract.body_ids:
        if contract is HARDWARE_REPORT_CONTRACT:
            raise ValueError("mesh report body inventory differs from the exact 8 × 4 hardware body set")
        raise ValueError("WJ24 mesh report body inventory differs from the exact five-body contract")
    for body_id, report_body in reported_bodies.items():
        if not isinstance(report_body, dict):
            raise TypeError(f"{body_id}: mesh body report must be an object")
        _source_geometry_volume(report_body, contract, body_id)
    return contract, reported_bodies


def validate_gauss5_rule(
    rule: tuple[tuple[tuple[float, float, float], float], ...] = GAUSS5_TETRAHEDRON_14,
) -> dict[str, float | int]:
    if len(rule) != 14:
        raise ValueError("Gmsh 4.12.1 tetrahedron Gauss5 rule must contain 14 points")
    points = set()
    weights = []
    for point, raw_weight in rule:
        if len(point) != 3:
            raise ValueError("tetrahedron reference point must have three coordinates")
        coordinates = tuple(_finite_float(value, "quadrature coordinate") for value in point)
        weight = _finite_float(raw_weight, "quadrature weight")
        if weight <= 0:
            raise ValueError("Gauss5 weights must be positive")
        if min(coordinates) < 0 or math.fsum(coordinates) > 1:
            raise ValueError("Gauss5 point lies outside the reference tetrahedron")
        points.add(coordinates)
        weights.append(weight)
    if len(points) != 14:
        raise ValueError("Gauss5 tetrahedron rule contains duplicate reference points")
    weight_sum = math.fsum(weights)
    if not math.isclose(weight_sum, 1.0 / 6.0, rel_tol=0.0, abs_tol=5e-11):
        raise ValueError("Gauss5 tetrahedron weights do not integrate the reference volume")
    return {
        "point_count": len(rule),
        "weight_sum": weight_sum,
        "minimum_weight": min(weights),
        "maximum_weight": max(weights),
    }


def c3d10_shape_derivatives(
    reference_point: tuple[float, float, float],
) -> tuple[tuple[float, float, float], ...]:
    """Return node-major derivatives dN_i/d(r,s,t) for CalculiX C3D10 order."""
    if len(reference_point) != 3:
        raise ValueError("reference point must have three coordinates")
    r, s, t = (_finite_float(value, "reference coordinate") for value in reference_point)
    barycentric = (1.0 - r - s - t, r, s, t)
    derivatives: list[tuple[float, float, float]] = []
    for index, value in enumerate(barycentric):
        derivatives.append(
            tuple((4.0 * value - 1.0) * component for component in TETRAHEDRON_VERTEX_DERIVATIVES[index])
        )
    for first, second in TETRAHEDRON_EDGE_VERTICES:
        derivatives.append(
            tuple(
                4.0
                * (
                    barycentric[first] * TETRAHEDRON_VERTEX_DERIVATIVES[second][axis]
                    + barycentric[second] * TETRAHEDRON_VERTEX_DERIVATIVES[first][axis]
                )
                for axis in range(3)
            )
        )
    return tuple(derivatives)


def c3d10_jacobian_determinant(
    node_coordinates: tuple[tuple[float, float, float], ...],
    reference_point: tuple[float, float, float],
) -> float:
    """Evaluate det(dX/d(r,s,t)) in square millimetres at one reference point."""
    if len(node_coordinates) != 10:
        raise ValueError("C3D10 element must have exactly ten nodal coordinates")
    coordinates = tuple(
        tuple(_finite_float(value, "node coordinate") for value in point)
        for point in node_coordinates
    )
    if any(len(point) != 3 for point in coordinates):
        raise ValueError("C3D10 node coordinates must be three-dimensional")
    derivatives = c3d10_shape_derivatives(reference_point)
    jacobian = tuple(
        tuple(
            math.fsum(coordinates[node][physical_axis] * derivatives[node][natural_axis] for node in range(10))
            for natural_axis in range(3)
        )
        for physical_axis in range(3)
    )
    a, b, c = jacobian
    determinant = (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )
    if not math.isfinite(determinant):
        raise ValueError("C3D10 Jacobian determinant is nonfinite")
    return determinant


def integrate_c3d10_element(
    node_coordinates: tuple[tuple[float, float, float], ...],
    rule: tuple[tuple[tuple[float, float, float], float], ...] = GAUSS5_TETRAHEDRON_14,
) -> dict[str, Any]:
    rule_summary = validate_gauss5_rule(rule)
    determinant_rows = []
    weighted_volumes = []
    for index, (point, weight) in enumerate(rule):
        determinant = c3d10_jacobian_determinant(node_coordinates, point)
        determinant_rows.append({"point_index": index, "reference_point": list(point), "determinant_mm3": determinant})
        weighted_volumes.append(determinant * weight)
    determinants = [row["determinant_mm3"] for row in determinant_rows]
    return {
        "jacobian_determinant_count": len(determinants),
        "all_jacobians_positive": all(value > 0 for value in determinants),
        "minimum_jacobian_determinant_mm3": min(determinants),
        "maximum_jacobian_determinant_mm3": max(determinants),
        "integrated_volume_mm3": math.fsum(weighted_volumes),
        "weight_sum": rule_summary["weight_sum"],
        "determinants": determinant_rows,
    }


def parse_c3d10_deck(
    path: str | Path,
    *,
    expected_body_ids: frozenset[str] = EXPECTED_HARDWARE_BODY_IDS,
    elset_prefix: str = EXPECTED_HARDWARE_CALCULIX_ELSET_PREFIX,
) -> tuple[dict[int, tuple[float, float, float]], dict[str, dict[int, tuple[int, ...]]]]:
    """Parse a geometry-only C3D10 deck for the selected exact body contract."""
    nodes: dict[int, tuple[float, float, float]] = {}
    bodies: dict[str, dict[int, tuple[int, ...]]] = {}
    mode: tuple[str, str | None] | None = None
    cards: list[str] = []
    for line_number, raw in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("**"):
            continue
        if line.startswith("*"):
            fields = [field.strip() for field in line.upper().split(",")]
            if fields == ["*HEADING"]:
                if cards:
                    raise ValueError("deck *HEADING must be the first card")
                cards.append("HEADING")
                mode = ("heading", None)
            elif fields == ["*NODE"]:
                if "NODE" in cards:
                    raise ValueError("deck contains duplicate *NODE cards")
                cards.append("NODE")
                mode = ("nodes", None)
            elif len(fields) == 3 and fields[0] == "*ELEMENT":
                attributes = {}
                for field in fields[1:]:
                    key, separator, value = field.partition("=")
                    if not separator or key in attributes:
                        raise ValueError(f"deck line {line_number}: malformed *ELEMENT card")
                    attributes[key] = value
                if attributes.get("TYPE") != "C3D10":
                    raise ValueError(f"deck line {line_number}: expected C3D10 elements")
                set_name = attributes.get("ELSET", "")
                body_id = next(
                    (
                        candidate
                        for candidate in expected_body_ids
                        if set_name == f"{elset_prefix}{candidate.upper()}"
                    ),
                    None,
                )
                if body_id is None or body_id in bodies:
                    raise ValueError(f"deck line {line_number}: unknown or duplicate element set {set_name}")
                bodies[body_id] = {}
                cards.append(f"ELEMENT:{body_id}")
                mode = ("elements", body_id)
            else:
                raise ValueError(f"deck line {line_number}: unexpected card {line!r}")
            continue
        if mode is None or mode[0] == "heading":
            continue
        fields = [field.strip() for field in line.split(",")]
        try:
            if mode[0] == "nodes":
                if len(fields) != 4:
                    raise ValueError("node row must have four fields")
                node_id = int(fields[0])
                if node_id <= 0 or node_id in nodes:
                    raise ValueError("node ID must be unique and positive")
                xyz = tuple(_finite_float(value, "node coordinate") for value in fields[1:])
                nodes[node_id] = xyz  # type: ignore[assignment]
            elif mode[0] == "elements":
                if len(fields) != 11:
                    raise ValueError("C3D10 row must have eleven fields")
                element_id = int(fields[0])
                connectivity = tuple(int(value) for value in fields[1:])
                if element_id <= 0 or len(set(connectivity)) != 10 or any(node <= 0 for node in connectivity):
                    raise ValueError("C3D10 IDs must be unique and positive")
                if any(element_id in other for name, other in bodies.items() if name != mode[1]):
                    raise ValueError("element ID is reused across body sets")
                if element_id in bodies[mode[1]]:
                    raise ValueError("duplicate C3D10 element ID")
                bodies[mode[1]][element_id] = connectivity
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(f"deck line {line_number}: {error}") from error
    if (
        cards[:2] != ["HEADING", "NODE"]
        or set(bodies) != expected_body_ids
        or not nodes
    ):
        raise ValueError(
            "deck does not contain heading, nodes, and the exact expected C3D10 body sets"
        )
    if any(not elements for elements in bodies.values()):
        raise ValueError("deck has an empty C3D10 body")
    all_connectivity_nodes = {node for elements in bodies.values() for row in elements.values() for node in row}
    if all_connectivity_nodes != set(nodes):
        raise ValueError("deck contains absent or unreferenced nodes")
    return nodes, bodies


def audit_mesh_directory(mesh_directory: str | Path) -> dict[str, Any]:
    directory = Path(mesh_directory).expanduser().resolve()
    report_path = directory / "mesh.json"
    deck_path = directory / "mesh.inp"
    if not report_path.is_file() or not deck_path.is_file():
        raise ValueError("mesh directory must contain mesh.json and mesh.inp")
    try:
        report = json.loads(report_path.read_text())
    except json.JSONDecodeError as error:
        raise ValueError("mesh.json is invalid JSON") from error
    if not isinstance(report, dict):
        raise TypeError("mesh report root must be an object")
    contract, reported_bodies = validate_mesh_report_contract(report)
    rule_summary = validate_gauss5_rule()
    if sha256_file(deck_path) != report.get("mesh_input_sha256"):
        raise ValueError("mesh deck hash differs from mesh.json")

    nodes, deck_bodies = parse_c3d10_deck(
        deck_path,
        expected_body_ids=contract.body_ids,
        elset_prefix=contract.calculix_elset_prefix,
    )
    if set(deck_bodies) != contract.body_ids:
        raise ValueError("deck body inventory differs from mesh report")

    body_results = {}
    total_elements = 0
    total_gauss_determinants = 0
    total_negative = 0
    global_minimum = math.inf
    worst_relative_volume_error = 0.0
    for body_id in sorted(contract.body_ids):
        report_body = reported_bodies[body_id]
        elements = deck_bodies[body_id]
        expected_elements = {_positive_int(value, f"{body_id} element ID") for value in report_body.get("elements", [])}
        if len(expected_elements) != len(report_body.get("elements", [])) or expected_elements != set(elements):
            raise ValueError(f"{body_id}: deck element IDs disagree with report ownership")
        expected_nodes = {_positive_int(value, f"{body_id} node ID") for value in report_body.get("nodes", [])}
        actual_nodes = {node for row in elements.values() for node in row}
        if len(expected_nodes) != len(report_body.get("nodes", [])) or expected_nodes != actual_nodes:
            raise ValueError(f"{body_id}: deck connectivity nodes disagree with report ownership")
        if not actual_nodes <= set(nodes):
            raise ValueError(f"{body_id}: deck refers to missing nodes")

        element_volumes = []
        minimum_determinant = math.inf
        maximum_determinant = -math.inf
        minimum_location: dict[str, Any] | None = None
        negative_rows = []
        determinant_count = 0
        for element_id, connectivity in elements.items():
            coordinates = tuple(nodes[node] for node in connectivity)
            for point_index, (point, weight) in enumerate(GAUSS5_TETRAHEDRON_14):
                determinant = c3d10_jacobian_determinant(coordinates, point)
                determinant_count += 1
                if determinant < minimum_determinant:
                    minimum_determinant = determinant
                    minimum_location = {
                        "element_id": element_id,
                        "point_index": point_index,
                        "reference_point_rst": list(point),
                    }
                maximum_determinant = max(maximum_determinant, determinant)
                if determinant <= 0:
                    total_negative += 1
                    if len(negative_rows) < 20:
                        negative_rows.append(
                            {
                                "element_id": element_id,
                                "point_index": point_index,
                                "reference_point_rst": list(point),
                                "determinant_mm3": determinant,
                            }
                        )
                element_volumes.append(determinant * weight)
        integrated_volume = math.fsum(element_volumes)
        total_elements += len(elements)
        total_gauss_determinants += determinant_count
        global_minimum = min(global_minimum, minimum_determinant)

        adapter_audit = report_body.get("integrated_mesh_audit", {})
        imported_cad = report_body.get("imported_cad", {})
        source_geometry_volume = _source_geometry_volume(report_body, contract, body_id)
        imported_cad_volume = _finite_float(
            imported_cad.get("volume_mm3"), f"{body_id} imported CAD volume"
        )
        adapter_mesh_volume = _finite_float(
            adapter_audit.get("integrated_mesh_volume_mm3"), f"{body_id} adapter integrated volume"
        )
        adapter_cad_volume = _finite_float(adapter_audit.get("cad_volume_mm3"), f"{body_id} adapter CAD volume")
        adapter_minimum = _finite_float(
            adapter_audit.get("minimum_integration_jacobian"), f"{body_id} adapter minimum Jacobian"
        )
        tolerance = _finite_float(
            adapter_audit.get("relative_volume_tolerance"), f"{body_id} relative volume tolerance"
        )
        reported_relative_error = _finite_float(
            adapter_audit.get("relative_volume_error"), f"{body_id} adapter relative volume error"
        )
        if determinant_count != len(elements) * len(GAUSS5_TETRAHEDRON_14):
            raise ValueError(f"{body_id}: independent Gauss determinant count is incomplete")
        if adapter_audit.get("integration_jacobian_count") != determinant_count:
            raise ValueError(f"{body_id}: independent and adapter integration point counts differ")
        if adapter_audit.get("sampled_jacobian_count") != len(elements):
            raise ValueError(f"{body_id}: adapter sampled Jacobian count differs from C3D10 count")
        if report_body.get("integration_rule", {}).get("weights_per_element") != len(GAUSS5_TETRAHEDRON_14):
            raise ValueError(f"{body_id}: report does not record 14 Gauss5 points per element")
        if not math.isclose(
            _finite_float(report_body.get("integration_rule", {}).get("minimum_weight"), f"{body_id} rule minimum weight"),
            rule_summary["minimum_weight"],
            rel_tol=0.0,
            abs_tol=1e-14,
        ):
            raise ValueError(f"{body_id}: report Gauss5 minimum weight differs from the pinned rule")
        if not math.isclose(imported_cad_volume, adapter_cad_volume, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(f"{body_id}: imported and integrated audit CAD volumes differ")
        source_imported_relative_error = abs(imported_cad_volume / source_geometry_volume - 1.0)
        if contract is WJ24_WOOD_REPORT_CONTRACT:
            imported_tolerance = _finite_float(
                imported_cad.get("relative_volume_tolerance"),
                f"{body_id} imported CAD source-geometry volume tolerance",
            )
            reported_imported_error = _finite_float(
                imported_cad.get("relative_volume_error_vs_export"),
                f"{body_id} imported CAD relative volume error versus WJ24 geometry",
            )
            if source_imported_relative_error > imported_tolerance or not math.isclose(
                source_imported_relative_error,
                reported_imported_error,
                rel_tol=1e-8,
                abs_tol=1e-12,
            ):
                raise ValueError(
                    f"{body_id}: imported STEP volume differs from the WJ24 finished-geometry source"
                )
        if not math.isclose(minimum_determinant, adapter_minimum, rel_tol=2e-8, abs_tol=1e-11):
            raise ValueError(
                f"{body_id}: independently recomputed minimum Gauss5 Jacobian "
                f"{minimum_determinant:.12g} differs from adapter {adapter_minimum:.12g}"
            )
        relative_error = abs(integrated_volume / source_geometry_volume - 1.0)
        adapter_volume_error = abs(integrated_volume / adapter_mesh_volume - 1.0)
        if relative_error > tolerance or not math.isclose(
            integrated_volume, adapter_mesh_volume, rel_tol=2e-9, abs_tol=1e-8
        ):
            raise ValueError(f"{body_id}: independently integrated volume differs from the adapter or tolerance")
        if not math.isclose(reported_relative_error, abs(adapter_mesh_volume / adapter_cad_volume - 1.0), rel_tol=1e-8, abs_tol=1e-12):
            raise ValueError(f"{body_id}: adapter relative-volume summary does not recalculate")
        worst_relative_volume_error = max(worst_relative_volume_error, relative_error)
        body_result = {
            "element_count": len(elements),
            "jacobian_determinant_count": determinant_count,
            "all_gauss5_jacobians_positive": not negative_rows,
            "minimum_gauss5_jacobian_determinant_mm3": minimum_determinant,
            "maximum_gauss5_jacobian_determinant_mm3": maximum_determinant,
            "minimum_location": minimum_location,
            "independently_integrated_volume_mm3": integrated_volume,
            "adapter_integrated_volume_mm3": adapter_mesh_volume,
            "source_geometry_volume_field": f"{contract.source_volume_field}.volume_mm3",
            "source_geometry_volume_mm3": source_geometry_volume,
            "imported_cad_volume_mm3": imported_cad_volume,
            "imported_cad_vs_source_geometry_relative_difference": source_imported_relative_error,
            "independent_vs_adapter_volume_relative_difference": adapter_volume_error,
            "relative_volume_error_vs_source_geometry": relative_error,
            "relative_volume_tolerance": tolerance,
            "nonpositive_determinants": negative_rows,
        }
        if contract is HARDWARE_REPORT_CONTRACT:
            body_result["relative_volume_error_vs_imported_cad"] = relative_error
        else:
            body_result["relative_volume_error_vs_WJ24_finished_geometry"] = relative_error
        body_results[body_id] = body_result
        if negative_rows:
            raise ValueError(f"{body_id}: {len(negative_rows)} sampled Gauss5 Jacobians are nonpositive")

    audit_scope = {
        "input_profile": contract.profile,
        "report_schema": contract.report_schema,
        "report_status": contract.report_status,
        "read_only": True,
        "gmsh_or_cad_imported": False,
        "mesh_generated": False,
        "native_solver_run": False,
        "body_count": len(body_results),
        "element_type": "C3D10",
        "geometry_volume_reference_field": f"{contract.source_volume_field}.volume_mm3",
        "integration_rule": "Gmsh 4.12.1 Gauss5; tetP5Solin; 14-point order-five tetrahedron rule",
        "shape_function_basis": "quadratic barycentric vertex and six edge functions in CalculiX C3D10 order",
        "jacobian_convention": "det(dX/drst), positive for the exported element orientation; units mm^3",
    }
    if contract is HARDWARE_REPORT_CONTRACT:
        audit_scope["scenario_id"] = EXPECTED_SCENARIO_ID
    result = {
        "schema": SCHEMA,
        "status": "PASSED_INDEPENDENT_GAUSS5_JACOBIAN_AND_VOLUME_AUDIT",
        "audit_scope": audit_scope,
        "input_artifacts": {
            "mesh_json": {"path": str(report_path), "sha256": sha256_file(report_path)},
            "mesh_inp": {"path": str(deck_path), "sha256": sha256_file(deck_path)},
        },
        "quadrature_rule_provenance": {
            "gmsh_version": EXPECTED_GMSH_VERSION,
            "source_archive_url": GMSH_SOURCE_ARCHIVE_URL,
            "source_archive_sha256": GMSH_SOURCE_ARCHIVE_SHA256,
            "source_file_path": GMSH_TETRA_RULE_SOURCE_PATH,
            "source_file_sha256": GMSH_TETRA_RULE_SOURCE_SHA256,
            "source_symbol": "tetP5Solin[14]",
            "source_rule_weight_sum": rule_summary["weight_sum"],
            "point_count": rule_summary["point_count"],
            "minimum_weight": rule_summary["minimum_weight"],
        },
        "totals": {
            "node_count": len(nodes),
            "element_count": total_elements,
            "gauss5_jacobian_determinant_count": total_gauss_determinants,
            "nonpositive_gauss5_jacobian_count": total_negative,
            "minimum_gauss5_jacobian_determinant_mm3": global_minimum,
            "maximum_relative_volume_error_vs_source_geometry": worst_relative_volume_error,
        },
        "per_body": body_results,
        "limitations": [
            "This checks positive Jacobian determinants at the 14 Gauss5 points; it does not prove positivity at every point inside each quadratic element.",
            "It is a mesh geometry audit only and establishes no material behavior, contact behavior, stiffness, resistance, response, or release.",
        ],
    }
    if contract is HARDWARE_REPORT_CONTRACT:
        result["totals"]["maximum_relative_volume_error_vs_imported_cad"] = (
            worst_relative_volume_error
        )
        result["totals"]["all_32_bodies_pass_recorded_relative_volume_tolerance"] = True
    else:
        result["totals"]["maximum_relative_volume_error_vs_WJ24_finished_geometry"] = (
            worst_relative_volume_error
        )
        result["totals"][
            "all_5_WJ24_finished_wood_bodies_pass_recorded_relative_volume_tolerance"
        ] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mesh_directory", type=Path)
    parser.add_argument("--output", type=Path, help="write audit JSON to a separate path")
    args = parser.parse_args()
    result = audit_mesh_directory(args.mesh_directory)
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is None:
        print(encoded, end="")
    else:
        output = args.output.expanduser().absolute()
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"audit output already exists: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded)
        print(output, flush=True)


if __name__ == "__main__":
    main()
