"""Build a bounded current four-nut infinite-thread-stiffness sensitivity MPC.

This adapter binds only to the frozen current three-wood/four-bolt input,
mesh, and classification artifacts. It creates a short shaft-surface rigid
motion fit over each modeled nut span. It does not assign a thread traction
law, nut material, contact, step, or physical engagement claim.
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
from fea.wood_joint_current_patch_contact import _parse_deck
from fea.wood_joint_current_patch_mesh import load_current_patch_bundle

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_current_nut_coupling_sensitivity/v1"
STATUS = "BUILT_CURRENT_4NUT_INFINITE_THREAD_STIFFNESS_SENSITIVITY_INPUT_ONLY"

EVIDENCE_DIR = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
DEFAULT_BUNDLE = EVIDENCE_DIR / "ordinary-patch-inputs-attempt01"
DEFAULT_MESH_DIR = EVIDENCE_DIR / "ordinary-patch-mesh-attempt02/mesh"
DEFAULT_CLASSIFICATION = (
    EVIDENCE_DIR / "ordinary-patch-contact-classification-attempt01/classification.json"
)

EXPECTED_INVENTORY_SHA256 = (
    "70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3"
)
EXPECTED_HASH_INDEX_SHA256 = (
    "eec82992ff292e36389dec148b2d168d9c3679b069bd1633eeec1d7a8a908c7f"
)
EXPECTED_MESH_REPORT_SHA256 = (
    "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07"
)
EXPECTED_MESH_DECK_SHA256 = (
    "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803"
)
EXPECTED_CLASSIFICATION_SHA256 = (
    "18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13"
)

AXIS_IDS = (
    "bottom_center/clip_horizontal_bottom_right_1/rail_1",
    "bottom_center/clip_horizontal_bottom_right_1/rail_2",
    "bottom_center/clip_horizontal_bottom_right_1/principal_1",
    "bottom_center/clip_horizontal_bottom_right_1/principal_2",
)
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
IMPLEMENTATION_REVISION = "b1e8707d"
EXPECTED_NUT_SPAN_MM = 5.7404
AXIS_LINE_TOLERANCE_MM = 1e-5
RADIUS_TOLERANCE_MM = 1e-4
NODE_RADIUS_TOLERANCE_MM = 1e-4
SPAN_BOUNDARY_EPSILON_MM = 1e-9
MAX_FIT_CONDITION_ESTIMATE = 1e8
MAX_REPRODUCTION_ERROR = 1e-10
MAX_ADJOINT_WRENCH_ERROR = 1e-10
ROTATION_CHARACTERISTIC_LENGTH_MM = 3.175

Vector = tuple[float, float, float]
Matrix = list[list[float]]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def _read_json(path: Path, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is unavailable or invalid JSON: {path}") from error
    if not isinstance(value, dict):
        raise TypeError(f"{label} root must be a JSON object")
    return raw, value


def _vec3(value: Any, label: str) -> Vector:
    try:
        result = tuple(float(item) for item in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must be three finite coordinates") from error
    if len(result) != 3 or not all(math.isfinite(item) for item in result):
        raise ValueError(f"{label} must be three finite coordinates")
    return result  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def _sub(left: Sequence[float], right: Sequence[float]) -> Vector:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _add_scaled(
    point: Sequence[float], direction: Sequence[float], scale: float
) -> Vector:
    return tuple(
        float(point[index]) + float(direction[index]) * scale for index in range(3)
    )  # type: ignore[return-value]


def _norm(value: Sequence[float]) -> float:
    return math.sqrt(_dot(value, value))


def _cross(left: Sequence[float], right: Sequence[float]) -> Vector:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _normalise_axis(value: Any, label: str) -> Vector:
    axis = _vec3(value, label)
    length = _norm(axis)
    if abs(length - 1.0) > 1e-8:
        raise ValueError(f"{label} is not a unit vector")
    return tuple(component / length for component in axis)  # type: ignore[return-value]


def _invert_full_rank(matrix: Matrix, label: str) -> tuple[Matrix, list[float]]:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError(f"{label}: expected a nonempty square matrix")
    augmented = [
        [float(value) for value in matrix[row]]
        + [1.0 if row == col else 0.0 for col in range(size)]
        for row in range(size)
    ]
    global_scale = max(abs(value) for row in matrix for value in row)
    if not math.isfinite(global_scale) or global_scale == 0.0:
        raise ValueError(f"{label}: rank deficient (rank 0 of {size})")
    pivots: list[float] = []
    for column in range(size):
        pivot_row = max(
            range(column, size), key=lambda row: abs(augmented[row][column])
        )
        pivot = abs(augmented[pivot_row][column])
        if not math.isfinite(pivot) or pivot <= global_scale * 1e-12:
            raise ValueError(
                f"{label}: rank deficient (rank {column} of {size}); "
                "nut-span shaft patch does not support a full six-DOF fit"
            )
        augmented[column], augmented[pivot_row] = (
            augmented[pivot_row],
            augmented[column],
        )
        divisor = augmented[column][column]
        pivots.append(abs(divisor))
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor:
                augmented[row] = [
                    augmented[row][index] - factor * augmented[column][index]
                    for index in range(2 * size)
                ]
    inverse = [row[size:] for row in augmented]
    return inverse, pivots


def _matrix_inf_norm(matrix: Matrix) -> float:
    return max(math.fsum(abs(value) for value in row) for row in matrix)


def _surface_design_row(offset_mm: Sequence[float], length_mm: float) -> Matrix:
    x, y, z = (value / length_mm for value in offset_mm)
    # u = u0 + theta x r = u0 - [r]x theta. The rotational
    # unknowns in this scaled design are length_mm * theta.
    return [
        [1.0, 0.0, 0.0, 0.0, z, -y],
        [0.0, 1.0, 0.0, -z, 0.0, x],
        [0.0, 0.0, 1.0, y, -x, 0.0],
    ]


def fit_rigid_motion(
    node_positions_global_xyz_mm: Mapping[int, Sequence[float]],
    reference_global_xyz_mm: Sequence[float],
    *,
    characteristic_length_mm: float = ROTATION_CHARACTERISTIC_LENGTH_MM,
    weights: Mapping[int, float] | None = None,
) -> dict[str, Any]:
    """Return the normalized weighted-LS map from nodal U to (u0, theta).

    The returned weights are normalized interpolation weights, not tractions.
    With no caller-supplied weights, each unique SHA-bound surface node has an
    equal weight. Rotation columns are scaled by ``characteristic_length_mm``
    for a dimensionless, better-conditioned rank check.
    """
    if not node_positions_global_xyz_mm:
        raise ValueError("nut-span shaft patch is rank deficient: no eligible nodes")
    if not math.isfinite(characteristic_length_mm) or characteristic_length_mm <= 0:
        raise ValueError("characteristic length must be finite and positive")
    node_ids = tuple(sorted(int(node) for node in node_positions_global_xyz_mm))
    if len(node_ids) != len(set(node_ids)) or any(node <= 0 for node in node_ids):
        raise ValueError("shaft fit node IDs must be unique positive integers")
    reference = _vec3(reference_global_xyz_mm, "nut-seat reference")
    positions = [
        _vec3(node_positions_global_xyz_mm[node], f"node {node}") for node in node_ids
    ]
    if weights is None:
        raw_weights = [1.0] * len(node_ids)
        weighting = "equal_weight_per_unique_SHA_bound_TRI6_surface_node"
    else:
        if set(weights) != set(node_ids):
            raise ValueError(
                "fit weights must name each and only each selected shaft node"
            )
        raw_weights = [float(weights[node]) for node in node_ids]
        weighting = "caller_supplied_positive_normalized_nodal_interpolation_weights"
    if any(not math.isfinite(value) or value <= 0.0 for value in raw_weights):
        raise ValueError("fit weights must be finite and positive")
    weight_sum = math.fsum(raw_weights)
    normalized_weights = [value / weight_sum for value in raw_weights]

    design_rows: list[Matrix] = []
    gram = [[0.0] * 6 for _ in range(6)]
    for position, weight in zip(positions, normalized_weights, strict=True):
        row = _surface_design_row(_sub(position, reference), characteristic_length_mm)
        design_rows.append(row)
        for output in range(6):
            for other in range(6):
                gram[output][other] += weight * math.fsum(
                    row[component][output] * row[component][other]
                    for component in range(3)
                )

    try:
        inverse, pivots = _invert_full_rank(gram, "nut-span shaft patch design")
    except ValueError as error:
        raise ValueError(
            "nut-span shaft patch is rank deficient: "
            f"{len(node_ids)} strict-span surface nodes; {error}"
        ) from error
    rhs = [[0.0] * (3 * len(node_ids)) for _ in range(6)]
    for point_index, (row, weight) in enumerate(
        zip(design_rows, normalized_weights, strict=True)
    ):
        for generalized in range(6):
            for component in range(3):
                rhs[generalized][3 * point_index + component] = (
                    weight * row[component][generalized]
                )
    coefficients_scaled = [
        [
            math.fsum(inverse[row][inner] * rhs[inner][column] for inner in range(6))
            for column in range(3 * len(node_ids))
        ]
        for row in range(6)
    ]
    coefficients = [row[:] for row in coefficients_scaled]
    for row in range(3, 6):
        coefficients[row] = [
            value / characteristic_length_mm for value in coefficients[row]
        ]

    condition_estimate = _matrix_inf_norm(gram) * _matrix_inf_norm(inverse)
    if not math.isfinite(condition_estimate):
        raise ValueError("nut-span shaft patch design condition estimate is nonfinite")

    # C H = I proves the six fitted generalized motions reproduce every
    # infinitesimal rigid translation and rotation at the reference point.
    reproduction = [[0.0] * 6 for _ in range(6)]
    for node_index, (row, position) in enumerate(
        zip(design_rows, positions, strict=True)
    ):
        x, y, z = _sub(position, reference)
        physical_row = [
            [1.0, 0.0, 0.0, 0.0, z, -y],
            [0.0, 1.0, 0.0, -z, 0.0, x],
            [0.0, 0.0, 1.0, y, -x, 0.0],
        ]
        for output in range(6):
            for generalized in range(6):
                reproduction[output][generalized] += math.fsum(
                    coefficients[output][3 * node_index + component]
                    * physical_row[component][generalized]
                    for component in range(3)
                )
    reproduction_error = max(
        abs(reproduction[row][column] - (1.0 if row == column else 0.0))
        for row in range(6)
        for column in range(6)
    )

    # The transpose map passes a generalized force/moment to a virtual-work
    # adjoint distribution. This only audits the map's wrench conservation;
    # it is not a traction law or a solver reaction calculation.
    adjoint_cases: list[dict[str, Any]] = []
    max_adjoint_error = 0.0
    for generalized in range(6):
        requested = [0.0] * 6
        requested[generalized] = 1.0
        resultant_force = [0.0, 0.0, 0.0]
        resultant_moment = [0.0, 0.0, 0.0]
        for node_index, position in enumerate(positions):
            nodal_force = [
                math.fsum(
                    coefficients[dof][3 * node_index + component] * requested[dof]
                    for dof in range(6)
                )
                for component in range(3)
            ]
            for component in range(3):
                resultant_force[component] += nodal_force[component]
            moment = _cross(_sub(position, reference), nodal_force)
            for component in range(3):
                resultant_moment[component] += moment[component]
        if generalized < 3:
            error = max(
                max(
                    abs(resultant_force[component] - requested[component])
                    for component in range(3)
                ),
                max(abs(value) for value in resultant_moment)
                / characteristic_length_mm,
            )
        else:
            error = max(
                characteristic_length_mm * max(abs(value) for value in resultant_force),
                max(
                    abs(resultant_moment[component] - requested[component + 3])
                    for component in range(3)
                ),
            )
        max_adjoint_error = max(max_adjoint_error, error)
        adjoint_cases.append(
            {
                "generalized_load_component": generalized,
                "requested_generalized_wrench": requested,
                "observed_resultant_force": resultant_force,
                "observed_resultant_moment_about_reference_nmm": resultant_moment,
                "scaled_max_error": error,
            }
        )

    if condition_estimate > MAX_FIT_CONDITION_ESTIMATE:
        raise ValueError(
            "nut-span shaft patch fit is full-rank but ill-conditioned: "
            f"condition estimate {condition_estimate:.6g} exceeds "
            f"{MAX_FIT_CONDITION_ESTIMATE:.6g}"
        )
    if reproduction_error > MAX_REPRODUCTION_ERROR:
        raise ValueError(
            "nut-span shaft patch affine-rigid reproduction audit failed: "
            f"{reproduction_error:.6g}"
        )
    if max_adjoint_error > MAX_ADJOINT_WRENCH_ERROR:
        raise ValueError(
            "nut-span shaft patch load-adjoint wrench audit failed: "
            f"{max_adjoint_error:.6g}"
        )

    return {
        "node_ids": list(node_ids),
        "normalized_weights": normalized_weights,
        "weighting": weighting,
        "weight_sum": math.fsum(normalized_weights),
        "characteristic_length_mm": characteristic_length_mm,
        "scaled_design_rank": 6,
        "scaled_design_gram_matrix": gram,
        "scaled_design_gauss_jordan_pivots": pivots,
        "scaled_design_condition_estimate_inf_norm": condition_estimate,
        "coefficient_matrix_rank": 6,
        "fit_coefficients_u0_then_theta": coefficients,
        "affine_rigid_reproduction_max_abs_error": reproduction_error,
        "affine_rigid_reproduction_matrix": reproduction,
        "load_adjoint_wrench_audit": {
            "passed": True,
            "interpretation": "virtual-work coefficient-transpose wrench conservation only; not contact traction or solver reaction",
            "max_scaled_error": max_adjoint_error,
            "unit_generalized_load_cases": adjoint_cases,
        },
        "well_conditioned": True,
    }


def _check_pinned_source_binding(
    inventory: Mapping[str, Any],
    inventory_sha256: str,
    hash_index_sha256: str,
    mesh_report: Mapping[str, Any],
    mesh_report_sha256: str,
    mesh_deck_sha256: str,
    classification: Mapping[str, Any],
    classification_sha256: str,
) -> None:
    if inventory_sha256 != EXPECTED_INVENTORY_SHA256:
        raise ValueError("current input inventory SHA256 differs from the parent pin")
    if hash_index_sha256 != EXPECTED_HASH_INDEX_SHA256:
        raise ValueError("current input hash-index SHA256 differs from the parent pin")
    if mesh_report_sha256 != EXPECTED_MESH_REPORT_SHA256:
        raise ValueError("current mesh report SHA256 differs from the parent pin")
    if mesh_deck_sha256 != EXPECTED_MESH_DECK_SHA256:
        raise ValueError("current mesh deck SHA256 differs from the parent pin")
    if classification_sha256 != EXPECTED_CLASSIFICATION_SHA256:
        raise ValueError(
            "current contact-classification SHA256 differs from the parent pin"
        )
    binding = classification.get("candidate_binding")
    if not isinstance(binding, Mapping) or any(
        binding.get(field) != expected
        for field, expected in {
            "revision_id": REVISION_ID,
            "implementation_revision": IMPLEMENTATION_REVISION,
            "inventory_sha256": EXPECTED_INVENTORY_SHA256,
            "hash_index_sha256": EXPECTED_HASH_INDEX_SHA256,
            "mesh_report_sha256": EXPECTED_MESH_REPORT_SHA256,
            "mesh_input_sha256": EXPECTED_MESH_DECK_SHA256,
        }.items()
    ):
        raise ValueError(
            "classification does not bind the exact current inventory and mesh"
        )
    if mesh_report.get("schema") != "wood_joint_current_patch_mesh/v1":
        raise ValueError(
            "unsupported mesh report schema for the current four-nut sensitivity"
        )
    if mesh_report.get("status") != "VERIFIED_C3D10_CURRENT_PATCH_MESH_ONLY_NO_SOLVER":
        raise ValueError(
            "current mesh report status differs from the frozen mesh contract"
        )
    if (
        mesh_report.get("accepted") is not False
        or mesh_report.get("solved") is not False
        or mesh_report.get("native_solve_run") is not False
        or mesh_report.get("output_contains_material_contact_or_solver_cards")
        is not False
    ):
        raise ValueError(
            "current mesh report scope/status does not match a no-solver mesh"
        )
    if (
        classification.get("schema")
        != "wood_joint_current_patch_contact_classification/v1"
    ):
        raise ValueError("unsupported current contact-classification schema")
    if classification.get("thread_engagement_verified") is not False:
        raise ValueError(
            "classification must keep physical thread engagement unverified"
        )
    if classification.get("contact_laws_assigned") is not False:
        raise ValueError("classification unexpectedly assigns a contact law")
    if (
        classification.get("response_ready") is not False
        or classification.get("native_solve_ready") is not False
    ):
        raise ValueError("classification is not the pinned geometry-only unready input")
    if inventory.get("status") != "current_geometry_patch_inputs_only":
        raise ValueError(
            "input inventory status differs from the current-only contract"
        )
    if inventory.get("migration_blockers") != []:
        raise ValueError("current input inventory has a migration blocker")


def _validate_surface_face_union(
    owner_id: str,
    body_row: Mapping[str, Any],
    surface: Mapping[str, Any],
    elements: Mapping[int, Sequence[int]],
) -> tuple[int, ...]:
    refs = surface.get("tri6_exterior_face_refs")
    declared = surface.get("tri6_node_ids")
    if not isinstance(refs, list) or not refs or not isinstance(declared, list):
        raise ValueError(
            f"{owner_id}: authenticated outer shaft TRI6 surface is incomplete"
        )
    element_ids = {int(value) for value in body_row.get("elements", ())}
    exterior_counts: Counter[tuple[int, ...]] = Counter()
    for element_id, connectivity in elements.items():
        if element_id not in element_ids:
            raise ValueError(
                f"{owner_id}: parsed element is outside its declared owner"
            )
        for face in FACES:
            exterior_counts[tuple(sorted(connectivity[index] for index in face))] += 1
    observed: set[int] = set()
    seen_refs: set[tuple[int, int]] = set()
    for raw in refs:
        if not isinstance(raw, (list, tuple)) or len(raw) != 2:
            raise ValueError(f"{owner_id}: malformed TRI6 exterior-face reference")
        element_id, side = int(raw[0]), int(raw[1])
        if element_id not in element_ids or side not in (1, 2, 3, 4):
            raise ValueError(
                f"{owner_id}: outer-shaft face points outside its C3D10 owner"
            )
        if (element_id, side) in seen_refs:
            raise ValueError(f"{owner_id}: outer-shaft face reference is duplicated")
        seen_refs.add((element_id, side))
        face_nodes = tuple(elements[element_id][index] for index in FACES[side - 1])
        if exterior_counts[tuple(sorted(face_nodes))] != 1:
            raise ValueError(f"{owner_id}: shaft surface contains a non-exterior face")
        observed.update(face_nodes)
    if observed != {int(value) for value in declared}:
        raise ValueError(
            f"{owner_id}: shaft TRI6 node union differs from its face refs"
        )
    if not observed <= {int(value) for value in body_row.get("nodes", ())}:
        raise ValueError(f"{owner_id}: shaft TRI6 nodes cross mesh-body ownership")
    return tuple(sorted(observed))


def _build_axis_row(
    axis_index: int,
    axis_id: str,
    bolt: Mapping[str, Any],
    bore_row: Mapping[str, Any],
    mesh_report: Mapping[str, Any],
    elements_by_owner: Mapping[str, Mapping[int, Sequence[int]]],
    node_positions: Mapping[int, Sequence[float]],
) -> dict[str, Any]:
    if (
        bolt.get("physical_bolt_id") != axis_id
        or bore_row.get("physical_bolt_id") != axis_id
    ):
        raise ValueError(
            f"axis {axis_id}: inventory/classification rows do not match the four-axis order"
        )
    if bolt.get("head_and_shaft_are_one_physical_bolt") is not True:
        raise ValueError(
            f"axis {axis_id}: current head-plus-shaft physical bolt identity is not bound"
        )
    roles = bolt.get("physical_hardware_roles")
    if not isinstance(roles, list):
        raise TypeError(f"axis {axis_id}: current hardware-role list is missing")
    role_rows = [
        row for row in roles if isinstance(row, Mapping) and row.get("role") == "nut"
    ]
    if len(role_rows) != 1:
        raise ValueError(f"axis {axis_id}: expected exactly one modeled nut role")
    nut = role_rows[0]
    intervals = nut.get("axial_projection_from_underhead_datum_mm")
    if not isinstance(intervals, list) or len(intervals) != 1 or len(intervals[0]) != 2:
        raise ValueError(f"axis {axis_id}: nut must have one ordered axial span")
    nut_start, nut_end = (float(value) for value in intervals[0])
    if (
        not math.isfinite(nut_start)
        or not math.isfinite(nut_end)
        or nut_end <= nut_start
    ):
        raise ValueError(f"axis {axis_id}: modeled nut axial interval is invalid")
    if abs((nut_end - nut_start) - EXPECTED_NUT_SPAN_MM) > 1e-8:
        raise ValueError(
            f"axis {axis_id}: modeled nut span differs from 5.7404 mm; refusing another hardware profile"
        )
    axis_origin = _vec3(
        bolt.get("axis_origin_global_xyz_mm"), f"axis {axis_id} source origin"
    )
    axis_direction = _normalise_axis(
        bolt.get("axis_direction_head_to_nut_global_xyz"),
        f"axis {axis_id} head-to-nut direction",
    )
    reference = _add_scaled(axis_origin, axis_direction, nut_start)

    shaft = bore_row.get("shaft_surface")
    if not isinstance(shaft, Mapping):
        raise TypeError(
            f"axis {axis_id}: classification has no bound shaft outer surface"
        )
    mesh_body_id = shaft.get("mesh_body_id")
    physical_body_id = f"physical_metal/{axis_id}/bolt"
    if shaft.get("physical_body_id") != physical_body_id:
        raise ValueError(
            f"axis {axis_id}: classification points to the wrong physical bolt body"
        )
    body_row = mesh_report.get("bodies", {}).get(mesh_body_id)
    if not isinstance(body_row, Mapping):
        raise TypeError(
            f"axis {axis_id}: shaft mesh owner is absent from the frozen mesh report"
        )
    if (
        body_row.get("mesh_body_id") != mesh_body_id
        or body_row.get("owner_kind") != "physical_metal"
        or body_row.get("physical_body_id") != physical_body_id
        or body_row.get("component_role") != "bolt_head_plus_shaft_union"
    ):
        raise ValueError(
            f"axis {axis_id}: shaft surface mesh owner is not the current bolt union"
        )
    surface_tag = int(shaft.get("transient_cad_entity_tag", -1))
    surface = body_row.get("surface_inventory", {}).get(str(surface_tag))
    if not isinstance(surface, Mapping):
        raise TypeError(
            f"axis {axis_id}: classified shaft surface tag is absent from its owner"
        )
    analytic = surface.get("analytic_surface_parameters")
    if (
        surface.get("cad_entity_tag") != surface_tag
        or surface.get("cad_type") != "Cylinder"
        or not isinstance(analytic, Mapping)
        or analytic.get("surface_type") != "Cylinder"
    ):
        raise ValueError(
            f"axis {axis_id}: target shaft surface is not the pinned analytic cylinder"
        )
    fitted_radius = float(shaft.get("fitted_radius_mm"))
    surface_radius = float(analytic.get("radius_mm"))
    if (
        abs(fitted_radius - surface_radius) > RADIUS_TOLERANCE_MM
        or abs(float(shaft.get("fitted_axis_alignment", 0.0)) - 1.0) > 1e-8
    ):
        raise ValueError(
            f"axis {axis_id}: classified shaft surface radius/axis fit is inconsistent"
        )
    class_axis_point = _vec3(
        analytic.get("axis_point_global_xyz_mm"),
        f"axis {axis_id} shaft cylinder axis point",
    )
    class_axis_direction = _normalise_axis(
        analytic.get("axis_direction_global_xyz_unoriented"),
        f"axis {axis_id} cylinder axis direction",
    )
    if abs(_dot(axis_direction, class_axis_direction)) < 1.0 - 1e-8:
        raise ValueError(
            f"axis {axis_id}: shaft cylinder axis is not parallel to the inventory axis"
        )
    axis_line_distance = _norm(
        _cross(_sub(axis_origin, class_axis_point), class_axis_direction)
    )
    if axis_line_distance > AXIS_LINE_TOLERANCE_MM:
        raise ValueError(
            f"axis {axis_id}: inventory datum and shaft cylinder axis disagree"
        )
    interval = shaft.get("axis_interval_mm")
    if not isinstance(interval, list) or len(interval) != 2:
        raise ValueError(f"axis {axis_id}: classified shaft axial interval is missing")
    shaft_lo, shaft_hi = (float(value) for value in interval)
    if not (shaft_lo < nut_start and shaft_hi > nut_end):
        raise ValueError(
            f"axis {axis_id}: modeled nut span is not strictly covered by the shaft surface"
        )

    body_elements = elements_by_owner.get(str(mesh_body_id))
    if not isinstance(body_elements, Mapping):
        raise TypeError(
            f"axis {axis_id}: shaft C3D10 element owner is absent from the deck"
        )
    shaft_surface_nodes = _validate_surface_face_union(
        str(mesh_body_id), body_row, surface, body_elements
    )
    analytic_axis_point = class_axis_point
    eligible_positions: dict[int, Vector] = {}
    eligible_station: dict[int, float] = {}
    eligible_radius_error: dict[int, float] = {}
    for node_id in shaft_surface_nodes:
        point = _vec3(
            node_positions.get(node_id), f"axis {axis_id} shaft node {node_id}"
        )
        station = _dot(_sub(point, axis_origin), axis_direction)
        # Open interval filter prevents the nut seat/end cap from receiving an
        # extrapolated shaft displacement. The epsilon only excludes points
        # numerically coincident with either modeled nut boundary.
        if not (
            nut_start + SPAN_BOUNDARY_EPSILON_MM
            < station
            < nut_end - SPAN_BOUNDARY_EPSILON_MM
        ):
            continue
        radial_vector = _sub(point, analytic_axis_point)
        radial_projection = _dot(radial_vector, class_axis_direction)
        radial_vector = tuple(
            radial_vector[component]
            - radial_projection * class_axis_direction[component]
            for component in range(3)
        )
        radial_error = abs(_norm(radial_vector) - surface_radius)
        if radial_error > NODE_RADIUS_TOLERANCE_MM:
            raise ValueError(
                f"axis {axis_id}: selected shaft surface node {node_id} is off the analytic outer cylinder"
            )
        eligible_positions[node_id] = point
        eligible_station[node_id] = station
        eligible_radius_error[node_id] = radial_error
    if not eligible_positions:
        raise ValueError(
            f"axis {axis_id}: nut-span shaft patch has no outer-surface nodes strictly inside the modeled span"
        )

    fit = fit_rigid_motion(
        eligible_positions,
        reference,
        characteristic_length_mm=ROTATION_CHARACTERISTIC_LENGTH_MM,
    )
    if fit["scaled_design_rank"] != 6 or fit["coefficient_matrix_rank"] != 6:
        raise ValueError(f"axis {axis_id}: nut-span shaft patch fit is rank deficient")
    if not fit["well_conditioned"]:
        raise ValueError(f"axis {axis_id}: nut-span shaft patch fit is ill-conditioned")

    nut_mesh_body_id_rows = [
        (key, row)
        for key, row in mesh_report["bodies"].items()
        if row.get("physical_body_id") == f"physical_metal/{axis_id}/nut"
    ]
    if len(nut_mesh_body_id_rows) != 1:
        raise ValueError(
            f"axis {axis_id}: exact source nut mesh owner is missing or duplicated"
        )
    nut_mesh_body_id, nut_mesh_body_row = nut_mesh_body_id_rows[0]
    if (
        nut_mesh_body_row.get("owner_kind") != "physical_metal"
        or nut_mesh_body_row.get("component_role") != "nut"
        or nut_mesh_body_row.get("mesh_body_id") != nut_mesh_body_id
    ):
        raise ValueError(
            f"axis {axis_id}: source nut mesh owner has an unexpected role"
        )

    return {
        "axis_index": axis_index,
        "physical_bolt_id": axis_id,
        "physical_metal_body_id": physical_body_id,
        "shaft_mesh_body_id": mesh_body_id,
        "shaft_outer_cylinder_surface_tag": surface_tag,
        "shaft_outer_cylinder_radius_mm": surface_radius,
        "shaft_source_classification": {
            "status": bore_row.get("status"),
            "contact_active": bore_row.get("contact_active"),
            "radial_gap_is_explicitly_open": bore_row.get(
                "radial_gap_is_explicitly_open"
            ),
            "thread_engagement_verified": False,
        },
        "modeled_nut_role_source": {
            "cad_shape_sha256": nut.get("cad_shape", {}).get("cad_shape_sha256"),
            "step_artifact_key": nut.get("step_artifact_key"),
            "axial_projection_from_underhead_datum_mm": [nut_start, nut_end],
            "axial_span_mm": nut_end - nut_start,
            "role_is_geometry_only": True,
        },
        "nut_seat_reference": {
            "datum": "modeled nut headward face center on verified current shaft axis",
            "axial_station_from_underhead_datum_mm": nut_start,
            "global_xyz_mm": list(reference),
        },
        "shaft_surface_patch": {
            "strict_open_axial_interval_mm": [nut_start, nut_end],
            "strict_interval_boundary_epsilon_mm": SPAN_BOUNDARY_EPSILON_MM,
            "surface_tri6_node_count": len(shaft_surface_nodes),
            "strict_span_node_count": len(eligible_positions),
            "strict_span_station_min_max_mm": [
                min(eligible_station.values()),
                max(eligible_station.values()),
            ],
            "max_selected_node_radial_error_mm": max(eligible_radius_error.values()),
            "selected_nodes": [
                {
                    "node_id": node_id,
                    "global_xyz_mm": list(eligible_positions[node_id]),
                    "axial_station_from_underhead_datum_mm": eligible_station[node_id],
                    "radial_error_from_analytic_outer_cylinder_mm": eligible_radius_error[
                        node_id
                    ],
                }
                for node_id in fit["node_ids"]
            ],
            "endcap_extrapolation_used": False,
        },
        "least_squares_rigid_motion_fit": fit,
        "control_node_sets": {
            "rigid_control_nset": f"NUT_{axis_index:02d}_RIGID_CONTROL",
            "reference_node_role": "translational u0 control, DOFs 1-3",
            "rotation_node_role": "abstract theta-in-radians control, translations DOFs 1-3",
            "reference_node_dofs": [1, 2, 3],
            "rotation_node_dofs_encode_theta_radians": [1, 2, 3],
            "rigid_control_is_not_a_nut_element_set": True,
        },
        "original_solid_nut_mesh": {
            "mesh_body_id": nut_mesh_body_id,
            "element_elset_name": nut_mesh_body_row.get("element_elset_name"),
            "node_set_name_in_frozen_mesh_report": nut_mesh_body_row.get(
                "node_set_name", nut_mesh_body_row.get("node_nset_name")
            ),
            "node_set_name_available": bool(
                nut_mesh_body_row.get("node_set_name")
                or nut_mesh_body_row.get("node_nset_name")
            ),
            "node_count": nut_mesh_body_row.get("node_count"),
            "element_count": nut_mesh_body_row.get("element_count"),
            "source_step_sha256": nut_mesh_body_row.get("source_step_sha256"),
            "included_in_real_metal_compliance_or_mass": False,
            "included_in_coupling_node_support": False,
            "included_in_contact": False,
        },
    }


def _equation_rows(
    axis_rows: Sequence[Mapping[str, Any]], first_control_node_id: int
) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    equations: list[dict[str, Any]] = []
    nsets: dict[str, list[int]] = {}
    dependent_variables: set[tuple[int, int]] = set()
    for row in axis_rows:
        axis_index = int(row["axis_index"])
        ref_node = first_control_node_id + 2 * axis_index
        rotation_node = ref_node + 1
        names = row["control_node_sets"]
        nsets[names["rigid_control_nset"]] = [ref_node, rotation_node]
        fit = row["least_squares_rigid_motion_fit"]
        node_ids = fit["node_ids"]
        coefficients = fit["fit_coefficients_u0_then_theta"]
        for generalized in range(6):
            control_node = ref_node if generalized < 3 else rotation_node
            dof = generalized + 1 if generalized < 3 else generalized - 2
            dependent = (control_node, dof)
            if dependent in dependent_variables:
                raise ValueError(
                    "duplicate dependent control-node DOF in generated equations"
                )
            dependent_variables.add(dependent)
            terms: list[dict[str, Any]] = [
                {"node_id": control_node, "dof": dof, "coefficient": 1.0}
            ]
            for node_index, node_id in enumerate(node_ids):
                for component in range(3):
                    coefficient = -float(
                        coefficients[generalized][3 * node_index + component]
                    )
                    if coefficient != 0.0:
                        terms.append(
                            {
                                "node_id": int(node_id),
                                "dof": component + 1,
                                "coefficient": coefficient,
                            }
                        )
            equations.append(
                {
                    "physical_bolt_id": row["physical_bolt_id"],
                    "generalized_motion_component": generalized,
                    "dependent_node_id": control_node,
                    "dependent_dof": dof,
                    "term_count": len(terms),
                    "terms": terms,
                }
            )
    if len(equations) != 24 or len(dependent_variables) != 24:
        raise ValueError(
            "current nut adapter did not generate 24 unique dependent variables"
        )
    return equations, nsets


def _format_include(
    axis_rows: Sequence[Mapping[str, Any]],
    equations: Sequence[Mapping[str, Any]],
    nsets: Mapping[str, Sequence[int]],
    control_coordinates: Mapping[int, Sequence[float]],
) -> str:
    lines = [
        "** Current four-nut infinite-thread-stiffness sensitivity input only.",
        "** Rotation controls encode infinitesimal theta in radians through DOFs 1-3.",
        "** A parent rigid-seat representation must bind these controls before analysis.",
        "** No nut solid elements, materials, contacts, steps, or solver controls are included.",
        "*NODE",
    ]
    for node_id in sorted(control_coordinates):
        xyz = control_coordinates[node_id]
        lines.append(f"{node_id},{xyz[0]:.12f},{xyz[1]:.12f},{xyz[2]:.12f}")
    for set_name, node_ids in nsets.items():
        lines.extend(
            (f"*NSET,NSET={set_name}", ",".join(str(value) for value in node_ids))
        )
    lines.append("** Six weighted least-squares shaft-fit equations per nut.")
    for equation in equations:
        lines.append("*EQUATION")
        lines.append(str(equation["term_count"]))
        terms = equation["terms"]
        # CalculiX input permits up to four equation terms on each data line.
        for start in range(0, len(terms), 4):
            cells: list[str] = []
            for term in terms[start : start + 4]:
                cells.extend(
                    (
                        str(term["node_id"]),
                        str(term["dof"]),
                        # CCX 2.21 equations.f reads each coefficient with
                        # f20.0 from only the first 20 characters. A signed
                        # .16e value exceeds that width and truncates its
                        # exponent. Fourteen significant digits fit here.
                        f"{float(term['coefficient']):.13e}",
                    )
                )
            lines.append(",".join(cells))
    return "\n".join(lines) + "\n"


def prepare_current_nut_coupling(
    bundle_directory: str | Path = DEFAULT_BUNDLE,
    mesh_report_path: str | Path = DEFAULT_MESH_DIR / "mesh.json",
    mesh_deck_path: str | Path = DEFAULT_MESH_DIR / "mesh.inp",
    classification_path: str | Path = DEFAULT_CLASSIFICATION,
    *,
    output_directory: str | Path | None = None,
) -> dict[str, Any]:
    """Authenticate the frozen source set and optionally write the MPC input."""
    bundle_directory = Path(bundle_directory).resolve()
    mesh_report_path = Path(mesh_report_path).resolve()
    mesh_deck_path = Path(mesh_deck_path).resolve()
    classification_path = Path(classification_path).resolve()
    bundle = load_current_patch_bundle(
        bundle_directory,
        expected_inventory_sha256=EXPECTED_INVENTORY_SHA256,
        expected_hash_index_sha256=EXPECTED_HASH_INDEX_SHA256,
    )
    mesh_report_bytes, mesh_report = _read_json(mesh_report_path, "current mesh report")
    classification_bytes, classification = _read_json(
        classification_path, "current contact classification"
    )
    mesh_report_sha = sha256_bytes(mesh_report_bytes)
    deck_sha = sha256_file(mesh_deck_path)
    classification_sha = sha256_bytes(classification_bytes)
    _check_pinned_source_binding(
        bundle["inventory"],
        bundle["inventory_sha256"],
        bundle["hash_index_sha256"],
        mesh_report,
        mesh_report_sha,
        deck_sha,
        classification,
        classification_sha,
    )
    inventory = bundle["inventory"]
    if (
        tuple(row.get("physical_bolt_id") for row in inventory["physical_bolts"])
        != AXIS_IDS
    ):
        raise ValueError("current input is not the exact ordered four-axis bundle")
    bore_rows = classification.get("bolt_receiver_bore_pairs")
    if (
        not isinstance(bore_rows, list)
        or tuple(row.get("physical_bolt_id") for row in bore_rows) != AXIS_IDS
    ):
        raise ValueError(
            "classification is not the exact ordered current four-bolt set"
        )
    if (
        classification.get("scope", {}).get("physical_bolts") != 4
        or classification.get("scope", {}).get("physical_metal_bodies") != 16
    ):
        raise ValueError(
            "classification scope does not match current four-bolt/sixteen-body inputs"
        )

    body_ids = tuple(mesh_report.get("bodies", {}))
    nodes, elements_by_owner = _parse_deck(mesh_deck_path, body_ids)
    if mesh_report.get("node_count") != len(nodes) or mesh_report.get(
        "element_count"
    ) != sum(len(rows) for rows in elements_by_owner.values()):
        raise ValueError(
            "current mesh report counts differ from its authenticated deck"
        )
    max_existing_node_id = max(nodes)
    first_control_node_id = max_existing_node_id + 1
    if (
        first_control_node_id <= max_existing_node_id
        or first_control_node_id + 7 in nodes
    ):
        raise ValueError(
            "fresh nut control node allocation collides with current mesh nodes"
        )

    axis_rows = [
        _build_axis_row(
            axis_index,
            axis_id,
            inventory["physical_bolts"][axis_index],
            bore_rows[axis_index],
            mesh_report,
            elements_by_owner,
            nodes,
        )
        for axis_index, axis_id in enumerate(AXIS_IDS)
    ]
    equations, nsets = _equation_rows(axis_rows, first_control_node_id)
    control_coordinates: dict[int, Sequence[float]] = {}
    control_node_roles: dict[int, str] = {}
    for row in axis_rows:
        axis_index = int(row["axis_index"])
        reference_node = first_control_node_id + 2 * axis_index
        rotation_node = reference_node + 1
        row["control_node_ids"] = {
            "translation_reference_node_id": reference_node,
            "rotation_control_node_id": rotation_node,
        }
        reference_xyz = row["nut_seat_reference"]["global_xyz_mm"]
        control_coordinates[reference_node] = reference_xyz
        control_coordinates[rotation_node] = reference_xyz
        control_node_roles[reference_node] = "translation_reference_u0"
        control_node_roles[rotation_node] = "abstract_rotation_theta_radians"
    available_source_nodes = {
        int(node_id)
        for row in axis_rows
        for node_id in row["least_squares_rigid_motion_fit"]["node_ids"]
    }
    available_control_dofs = {
        (node_id, dof) for node_id in control_coordinates for dof in (1, 2, 3)
    }
    seen_dependent: set[tuple[int, int]] = set()
    for equation in equations:
        dependent = (int(equation["dependent_node_id"]), int(equation["dependent_dof"]))
        if (
            dependent in seen_dependent
            or equation["terms"][0]["node_id"] != dependent[0]
            or equation["terms"][0]["dof"] != dependent[1]
        ):
            raise ValueError(
                "nut equations have duplicate or inconsistent dependent variables"
            )
        seen_dependent.add(dependent)
        seen_terms: set[tuple[int, int]] = set()
        for term in equation["terms"]:
            node_id = int(term["node_id"])
            dof = int(term["dof"])
            key = (node_id, dof)
            if key in seen_terms:
                raise ValueError("nut equation contains a duplicate node/DOF term")
            seen_terms.add(key)
            if node_id in control_coordinates:
                if key not in available_control_dofs:
                    raise ValueError(
                        "nut equation references an undeclared control-node DOF"
                    )
            elif node_id in available_source_nodes:
                if not (1 <= dof <= 3) or node_id not in nodes:
                    raise ValueError(
                        "nut equation references an absent shaft displacement DOF"
                    )
            else:
                raise ValueError(
                    "nut equation references a node outside shaft support/control ownership"
                )
    if len(seen_dependent) != 24 or len(nsets) != 4 or len(control_node_roles) != 8:
        raise ValueError(
            "nut control NSET/dependent-variable count differs from exact four-axis contract"
        )
    equation_summaries = [
        {
            key: equation[key]
            for key in (
                "physical_bolt_id",
                "generalized_motion_component",
                "dependent_node_id",
                "dependent_dof",
                "term_count",
            )
        }
        for equation in equations
    ]
    include_text = _format_include(axis_rows, equations, nsets, control_coordinates)
    if any(
        line.upper().startswith(
            (
                "*MATERIAL",
                "*SOLID SECTION",
                "*CONTACT",
                "*STEP",
                "*STATIC",
                "*DYNAMIC",
                "*RIGID BODY",
            )
        )
        for line in include_text.splitlines()
    ):
        raise ValueError(
            "nut sensitivity fragment contains a forbidden physical/model card"
        )

    report: dict[str, Any] = {
        "schema": SCHEMA,
        "status": STATUS,
        "candidate": {
            "revision_id": REVISION_ID,
            "implementation_revision": IMPLEMENTATION_REVISION,
            "physical_bolt_count": 4,
            "physical_metal_body_count": 16,
        },
        "source_binding": {
            "input_bundle_directory": str(bundle_directory),
            "inventory_sha256": bundle["inventory_sha256"],
            "hash_index_sha256": bundle["hash_index_sha256"],
            "mesh_report_path": str(mesh_report_path),
            "mesh_report_sha256": mesh_report_sha,
            "mesh_deck_path": str(mesh_deck_path),
            "mesh_deck_sha256": deck_sha,
            "classification_path": str(classification_path),
            "classification_sha256": classification_sha,
            "producer_source_path": Path(__file__)
            .resolve()
            .relative_to(ROOT)
            .as_posix(),
            "producer_source_sha256": sha256_file(__file__),
            "focused_test_path": "tests/test_wood_joint_current_nut_coupling.py",
            "focused_test_sha256": sha256_file(
                ROOT / "tests/test_wood_joint_current_nut_coupling.py"
            ),
        },
        "scope": {
            "named_sensitivity": "infinite-thread-stiffness nut coupling input",
            "physical_thread_engagement_established": False,
            "physical_thread_traction_law_assigned": False,
            "torque_or_capacity_claim": False,
            "real_metal_nut_compliance_or_mass_modeled": False,
            "contact_cards_emitted": False,
            "material_cards_emitted": False,
            "step_or_load_cards_emitted": False,
            "native_execution_performed": False,
            "large_rotation_exactness": False,
            "kinematics": "small-displacement linearized rigid motion about the modeled nut headward seat center",
            "rigid_seat_representation": "parent-selected; output NSETs are control-node sets only",
            "nut_mesh_interiors_used": False,
            "nut_support_nodes_are_only_sha_bound_shaft_outer-cylinder_nodes": True,
            "shaft_endcap_extrapolation_used": False,
        },
        "fresh_control_node_allocation": {
            "max_existing_mesh_node_id": max_existing_node_id,
            "first_control_node_id": first_control_node_id,
            "last_control_node_id": first_control_node_id + 7,
            "reserved_parent_actuator_node_range_starts_at": max_existing_node_id
            + 1000,
            "control_node_count": 8,
            "control_node_roles": {
                str(node_id): role
                for node_id, role in sorted(control_node_roles.items())
            },
            "nut_control_nset_count": len(nsets),
            "dofs_referenced": [1, 2, 3],
            "rotation_node_translation_dofs_encode_theta_radians": True,
            "all_dependent_control_dofs_unique": True,
        },
        "per_nut": axis_rows,
        "equation_cards": equation_summaries,
        "nsets": {name: list(values) for name, values in nsets.items()},
        "include_file_sha256": sha256_bytes(include_text.encode("utf-8")),
        "audits": {
            "four_exact_current_axes": True,
            "all_selected_nodes_strictly_inside_modeled_nut_span": True,
            "all_selected_nodes_on_sha_bound_outer_shaft_cylinder": True,
            "fit_rank_six_for_each_nut": True,
            "fit_well_conditioned_for_each_nut": True,
            "affine_rigid_reproduction_passed_for_each_nut": True,
            "load_adjoint_wrench_audit_passed_for_each_nut": True,
            "equation_dependent_variables_unique": True,
            "all_source_and_control_equation_dofs_are_declared": True,
            "original_nut_interiors_not_included_in_fit_or_coupling": True,
        },
        "limits": [
            "This is a named infinite-thread-stiffness sensitivity, not proof of physical nut/bolt thread engagement.",
            "Equal-weight normalized nodal interpolation is an algebraic rigid-motion fit, not physical thread traction or a contact-pressure law.",
            "The six-DOF fit is infinitesimal/small-rotation kinematics; large rotations are not exact.",
            "The parent must choose and validate a rigid-seat representation that activates/binds the four control NSETs.",
            "The output makes no reaction, load-path, torque, strength, or capacity claim.",
        ],
    }
    if output_directory is not None:
        output = Path(output_directory).resolve()
        if output.exists():
            raise FileExistsError(
                f"nut coupling output directory already exists: {output}"
            )
        output.mkdir(parents=True)
        include_path = output / "nut-coupling.inp"
        include_path.write_text(include_text, encoding="utf-8")
        report["artifacts"] = {
            "nut-coupling.inp": sha256_file(include_path),
        }
        report_path = output / "nut-coupling.json"
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        (output / "sha256.json").write_text(
            json.dumps(
                {
                    "nut-coupling.inp": sha256_file(include_path),
                    "nut-coupling.json": sha256_file(report_path),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        report["output_directory"] = str(output)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument(
        "--mesh-report", type=Path, default=DEFAULT_MESH_DIR / "mesh.json"
    )
    parser.add_argument("--mesh-deck", type=Path, default=DEFAULT_MESH_DIR / "mesh.inp")
    parser.add_argument("--classification", type=Path, default=DEFAULT_CLASSIFICATION)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    report = prepare_current_nut_coupling(
        args.bundle,
        args.mesh_report,
        args.mesh_deck,
        args.classification,
        output_directory=args.output_dir,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "output_directory": report["output_directory"],
                "control_node_ids": [
                    report["fresh_control_node_allocation"]["first_control_node_id"],
                    report["fresh_control_node_allocation"]["last_control_node_id"],
                ],
                "strict_span_node_counts": [
                    row["shaft_surface_patch"]["strict_span_node_count"]
                    for row in report["per_nut"]
                ],
                "fit_condition_estimates": [
                    row["least_squares_rigid_motion_fit"][
                        "scaled_design_condition_estimate_inf_norm"
                    ]
                    for row in report["per_nut"]
                ],
                "physical_thread_engagement_established": False,
                "native_execution_performed": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
