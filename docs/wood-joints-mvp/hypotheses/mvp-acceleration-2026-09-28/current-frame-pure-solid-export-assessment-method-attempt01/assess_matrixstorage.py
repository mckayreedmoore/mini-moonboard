#!/usr/bin/env python3
"""Sparse post-export checks for the pure physical-solid MATRIXSTORAGE operator.

This reads CalculiX sparse output; it does not assemble finite elements, alter
the operator, reduce constraints, or invoke CalculiX.
"""

from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import scipy
from scipy import sparse


ROOT = Path(__file__).resolve().parents[5]
PACKET = Path(__file__).resolve().parent
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
FRAME_MODEL_REL = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
PINS_PATH = PACKET / "source-pins.json"
FRAME_DOF_COUNT = 37_647
FRAME_NODE_COUNT = 12_549
FRAME_BODY_COUNT = 50
RIGID_RELATIVE_TOLERANCE = 1.0e-8


class AssessmentError(ValueError):
    """An input or numerical result does not meet this method's declared checks."""


def sha256_file(path: Path) -> str:
    full = path if path.is_absolute() else ROOT / path
    return hashlib.sha256(full.read_bytes()).hexdigest()


def verify_source_pins() -> dict[str, object]:
    pins = json.loads(PINS_PATH.read_text(encoding="utf-8"))
    if pins.get("schema") != "current_frame_pure_solid_export_assessment_source_pins/v1":
        raise AssessmentError("unexpected source-pins schema")
    seen: set[str] = set()
    for row in pins.get("files", []):
        rel = str(row["path"])
        if rel in seen:
            raise AssessmentError(f"duplicate source pin: {rel}")
        seen.add(rel)
        actual = sha256_file(Path(rel))
        if actual != row["sha256"]:
            raise AssessmentError(
                f"source pin mismatch for {rel}: observed {actual}, expected {row['sha256']}"
            )
    if not seen:
        raise AssessmentError("source pin list is empty")
    return pins


def parse_dof_lines(lines: Iterable[str], source: str) -> list[tuple[int, int]]:
    labels: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for line_number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        match = re.fullmatch(r"([1-9][0-9]*)\.([123])", line)
        if not match:
            raise AssessmentError(f"{source}:{line_number}: expected positive node.direction")
        node, direction = map(int, match.groups())
        label = (node, direction)
        if label in seen:
            raise AssessmentError(f"{source}:{line_number}: duplicate equation label {label}")
        seen.add(label)
        labels.append(label)
    if not labels:
        raise AssessmentError(f"{source}: empty .dof map")
    return labels


def parse_dof_file(path: Path) -> list[tuple[int, int]]:
    return parse_dof_lines(path.read_text(encoding="utf-8").splitlines(), str(path))


def require_dof_bijection(
    labels: list[tuple[int, int]], physical_node_ids: set[int], expected_count: int
) -> None:
    expected = {(node, direction) for node in physical_node_ids for direction in (1, 2, 3)}
    if len(physical_node_ids) * 3 != expected_count:
        raise AssessmentError(
            f"physical node inventory implies {len(physical_node_ids) * 3} DOFs, "
            f"not the required {expected_count}"
        )
    if len(labels) != expected_count:
        raise AssessmentError(f".dof has {len(labels)} labels; expected {expected_count}")
    observed = set(labels)
    if observed != expected:
        missing = sorted(expected - observed)[:8]
        extra = sorted(observed - expected)[:8]
        raise AssessmentError(
            f".dof is not a physical-node × directions bijection; "
            f"missing={missing}, extra={extra}"
        )


def parse_upper_triangle_lines(
    lines: Iterable[str],
    dimension: int,
    *,
    source: str,
    owner_by_row: np.ndarray | None = None,
    owner_names: list[str] | None = None,
) -> dict[str, object]:
    """Read one-based, upper-triangle triplets into a symmetric CSR matrix.

    Encoded pair keys are kept in packed arrays while parsing so duplicate
    detection does not require a Python object per stiffness entry.
    """
    if dimension <= 0:
        raise AssessmentError("matrix dimension must be positive")
    if owner_by_row is not None and len(owner_by_row) != dimension:
        raise AssessmentError("row-owner map length does not match matrix dimension")
    if owner_names is not None:
        if owner_by_row is None:
            raise AssessmentError("body names require a row-owner map")
        if np.any(owner_by_row < 0) or np.any(owner_by_row >= len(owner_names)):
            raise AssessmentError("row-owner map contains an unknown body index")
    keys = array.array("Q")
    values = array.array("d")
    diagonal_seen = bytearray(dimension)
    diagonal_values = np.zeros(dimension, dtype=np.float64)
    cross_body_nonzero_count = 0
    cross_body_examples: list[dict[str, object]] = []
    zero_pair_count = 0
    for line_number, raw in enumerate(lines, 1):
        fields = raw.split()
        if not fields:
            continue
        if len(fields) != 3:
            raise AssessmentError(f"{source}:{line_number}: expected row column value")
        try:
            row = int(fields[0])
            column = int(fields[1])
            value = float(fields[2].replace("D", "E").replace("d", "e"))
        except ValueError as exc:
            raise AssessmentError(f"{source}:{line_number}: invalid numeric triplet") from exc
        if not (1 <= row <= dimension and 1 <= column <= dimension):
            raise AssessmentError(
                f"{source}:{line_number}: matrix index ({row}, {column}) "
                f"outside 1..{dimension}"
            )
        if row > column:
            raise AssessmentError(
                f"{source}:{line_number}: lower-triangle entry ({row}, {column}); "
                "this reader requires one upper triangle"
            )
        if not math.isfinite(value):
            raise AssessmentError(f"{source}:{line_number}: non-finite matrix value")
        zero_based_row = row - 1
        zero_based_column = column - 1
        if row == column:
            if diagonal_seen[zero_based_row]:
                raise AssessmentError(f"{source}:{line_number}: duplicate diagonal {row}")
            diagonal_seen[zero_based_row] = 1
            diagonal_values[zero_based_row] = value
        if value == 0.0:
            zero_pair_count += 1
        if (
            value != 0.0
            and owner_by_row is not None
            and owner_by_row[zero_based_row] != owner_by_row[zero_based_column]
        ):
            cross_body_nonzero_count += 1
            if len(cross_body_examples) < 8:
                cross_body_examples.append({
                    "row": row,
                    "column": column,
                    "value_N_per_mm": value,
                    "row_body_index": int(owner_by_row[zero_based_row]),
                    "column_body_index": int(owner_by_row[zero_based_column]),
                    "row_body": (
                        owner_names[int(owner_by_row[zero_based_row])]
                        if owner_names is not None else None
                    ),
                    "column_body": (
                        owner_names[int(owner_by_row[zero_based_column])]
                        if owner_names is not None else None
                    ),
                })
        keys.append(zero_based_row * dimension + zero_based_column)
        values.append(value)

    pair_count = len(keys)
    if pair_count == 0:
        raise AssessmentError(f"{source}: no matrix triplets")
    if not all(diagonal_seen):
        missing = [i + 1 for i, present in enumerate(diagonal_seen) if not present][:8]
        raise AssessmentError(f"{source}: missing diagonal entries, first indices {missing}")
    if np.any(diagonal_values <= 0.0):
        bad = np.flatnonzero(diagonal_values <= 0.0)[:8] + 1
        raise AssessmentError(
            f"{source}: diagonal must be strictly positive, first indices {bad.tolist()}"
        )

    key_array = np.frombuffer(keys, dtype=np.dtype("=u8"))
    sorted_keys = np.sort(key_array)
    duplicate_positions = np.flatnonzero(sorted_keys[1:] == sorted_keys[:-1])
    if duplicate_positions.size:
        duplicate_key = int(sorted_keys[int(duplicate_positions[0])])
        duplicate_row, duplicate_column = divmod(duplicate_key, dimension)
        raise AssessmentError(
            f"{source}: duplicate triangular pair "
            f"({duplicate_row + 1}, {duplicate_column + 1})"
        )

    row = (key_array // dimension).astype(np.int64, copy=False)
    column = (key_array % dimension).astype(np.int64, copy=False)
    value_array = np.frombuffer(values, dtype=np.dtype("=f8"))
    off_diagonal = row != column
    full_rows = np.concatenate((row, column[off_diagonal]))
    full_columns = np.concatenate((column, row[off_diagonal]))
    full_values = np.concatenate((value_array, value_array[off_diagonal]))
    matrix = sparse.coo_matrix(
        (full_values, (full_rows, full_columns)),
        shape=(dimension, dimension),
        dtype=np.float64,
    ).tocsr()
    matrix.sum_duplicates()
    matrix.eliminate_zeros()
    difference = (matrix - matrix.transpose()).tocsr()
    difference.eliminate_zeros()
    symmetry_difference_max_abs = (
        float(np.max(np.abs(difference.data))) if difference.nnz else 0.0
    )
    if difference.nnz:
        raise AssessmentError(
            f"{source}: reconstructed symmetric triangle is asymmetric "
            f"(max difference {symmetry_difference_max_abs})"
        )
    return {
        "matrix": matrix,
        "triangle_pair_count": pair_count,
        "symmetric_nonzero_count": int(matrix.nnz),
        "explicit_zero_triangle_pair_count": zero_pair_count,
        "diagonal_min_N_per_mm": float(diagonal_values.min()),
        "diagonal_max_N_per_mm": float(diagonal_values.max()),
        "symmetry_difference_max_abs_N_per_mm": symmetry_difference_max_abs,
        "cross_body_nonzero_pair_count": cross_body_nonzero_count,
        "cross_body_nonzero_examples": cross_body_examples,
    }


def parse_upper_triangle_file(
    path: Path,
    dimension: int,
    *,
    owner_by_row: np.ndarray | None = None,
    owner_names: list[str] | None = None,
) -> dict[str, object]:
    return parse_upper_triangle_lines(
        path.read_text(encoding="utf-8").splitlines(),
        dimension,
        source=str(path),
        owner_by_row=owner_by_row,
        owner_names=owner_names,
    )


def load_frame_source_model(model_path: Path) -> dict[str, object]:
    model = json.loads(model_path.read_text(encoding="utf-8"))
    expected = {
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "case_id": "a12-rear",
    }
    for key, value in expected.items():
        if model.get(key) != value:
            raise AssessmentError(
                f"frame source {key} is {model.get(key)!r}, expected {value!r}"
            )
    raw_nodes = model.get("nodes")
    raw_bodies = model.get("physical_body_nodes")
    if not isinstance(raw_nodes, dict) or not isinstance(raw_bodies, dict):
        raise AssessmentError("frame source lacks nodes or physical_body_nodes")
    coordinates: dict[int, np.ndarray] = {}
    for raw_node, raw_xyz in raw_nodes.items():
        node = int(raw_node)
        xyz = np.asarray(raw_xyz, dtype=np.float64)
        if xyz.shape != (3,) or not np.all(np.isfinite(xyz)):
            raise AssessmentError(f"invalid source coordinate for node {node}")
        if node in coordinates:
            raise AssessmentError(f"duplicate source node coordinate {node}")
        coordinates[node] = xyz
    bodies: dict[str, set[int]] = {}
    owner_by_node: dict[int, int] = {}
    for body_index, (body_name, raw_ids) in enumerate(raw_bodies.items()):
        node_ids = [int(value) for value in raw_ids]
        node_set = set(node_ids)
        if not node_set or len(node_ids) != len(node_set):
            raise AssessmentError(f"empty or duplicate node list for body {body_name}")
        for node in node_set:
            if node not in coordinates:
                raise AssessmentError(f"body {body_name} references absent node {node}")
            if node in owner_by_node:
                raise AssessmentError(
                    f"physical node {node} is shared by bodies "
                    f"{owner_by_node[node]} and {body_name}"
                )
            owner_by_node[node] = body_index
        bodies[str(body_name)] = node_set
    physical_nodes = set(owner_by_node)
    if len(bodies) != FRAME_BODY_COUNT:
        raise AssessmentError(f"source has {len(bodies)} physical bodies, expected 50")
    if len(physical_nodes) != FRAME_NODE_COUNT:
        raise AssessmentError(
            f"source body maps cover {len(physical_nodes)} nodes, expected {FRAME_NODE_COUNT}"
        )
    centroids = {
        name: np.mean(np.vstack([coordinates[node] for node in sorted(node_ids)]), axis=0)
        for name, node_ids in bodies.items()
    }
    return {
        "model": model,
        "coordinates": coordinates,
        "bodies": bodies,
        "physical_nodes": physical_nodes,
        "owner_by_node": owner_by_node,
        "centroids": centroids,
    }


def rigid_mode_screen(
    matrix: sparse.csr_matrix,
    labels: list[tuple[int, int]],
    source: dict[str, object],
) -> dict[str, object]:
    owner_by_node = source["owner_by_node"]
    bodies = source["bodies"]
    coordinates = source["coordinates"]
    centroids = source["centroids"]
    owner_by_row = np.fromiter(
        (owner_by_node[node] for node, _direction in labels),
        dtype=np.int16,
        count=len(labels),
    )
    body_names = list(bodies)
    results: list[dict[str, object]] = []
    worst = 0.0
    for body_index, body_name in enumerate(body_names):
        row_indices = np.flatnonzero(owner_by_row == body_index)
        body_matrix = matrix[row_indices, :][:, row_indices].tocsr()
        row_sums = np.asarray(abs(body_matrix).sum(axis=1)).reshape(-1)
        scale = float(row_sums.max()) if row_sums.size else 0.0
        if not math.isfinite(scale) or scale <= 0.0:
            raise AssessmentError(f"body {body_name} has no positive finite operator scale")
        local_index = {int(global_row): local for local, global_row in enumerate(row_indices)}
        centroid = centroids[body_name]
        mode_rows: list[dict[str, object]] = []
        for axis_index, axis_name in enumerate("xyz"):
            translation = np.zeros(len(row_indices), dtype=np.float64)
            for global_row in row_indices:
                _node, direction = labels[int(global_row)]
                if direction == axis_index + 1:
                    translation[local_index[int(global_row)]] = 1.0
            mode_rows.append(_measure_mode(
                body_matrix, translation, scale, f"translation_{axis_name}",
                displacement_scale="1 mm",
            ))
        for axis_index, axis_name in enumerate("xyz"):
            rotation = np.zeros(len(row_indices), dtype=np.float64)
            axis = np.eye(3, dtype=np.float64)[axis_index]
            for global_row in row_indices:
                node, direction = labels[int(global_row)]
                displacement = np.cross(axis, coordinates[node] - centroid)
                rotation[local_index[int(global_row)]] = displacement[direction - 1]
            mode_rows.append(_measure_mode(
                body_matrix, rotation, scale, f"rotation_{axis_name}",
                displacement_scale="1 rad",
            ))
        body_max = max(float(row["relative_residual"]) for row in mode_rows)
        worst = max(worst, body_max)
        results.append({
            "body": body_name,
            "source_physical_node_count": len(bodies[body_name]),
            "source_mesh_node_centroid_xyz_mm": [float(value) for value in centroid],
            "centroid_definition": (
                "arithmetic mean of exact source adapter coordinates for the body's "
                "unique physical solid mesh nodes; rigid-rotation origin only, not "
                "a volume or mass centroid"
            ),
            "operator_infinity_row_sum_scale_N_per_mm": scale,
            "modes": mode_rows,
            "max_relative_residual": body_max,
            "all_six_within_tolerance": body_max <= RIGID_RELATIVE_TOLERANCE,
        })
    return {
        "mode_family": (
            "three unit translations (1 mm) and three unit rotations (1 rad) "
            "of each isolated physical body about its source mesh-node centroid"
        ),
        "residual_definition": (
            "||K_body v||_infinity / "
            "(||K_body||_infinity-row-sum * ||v||_infinity)"
        ),
        "operator_scale_units": "N/mm",
        "residual_units": "dimensionless; numerator and denominator are N",
        "relative_tolerance": RIGID_RELATIVE_TOLERANCE,
        "screened_body_count": len(results),
        "screened_rigid_mode_count": 6 * len(results),
        "overall_max_relative_residual": worst,
        "all_screened_modes_within_tolerance": worst <= RIGID_RELATIVE_TOLERANCE,
        "full_stiffness_rank_claimed": False,
        "bodies": results,
    }


def require_no_cross_body_coupling(parsed: dict[str, object]) -> None:
    if parsed["cross_body_nonzero_pair_count"]:
        raise AssessmentError(
            "pure-solid matrix has nonzero cross-body pairs: "
            f"{parsed['cross_body_nonzero_examples']}"
        )


def _measure_mode(
    body_matrix: sparse.csr_matrix,
    vector: np.ndarray,
    scale: float,
    name: str,
    *,
    displacement_scale: str,
) -> dict[str, object]:
    vector_scale = float(np.max(np.abs(vector)))
    if not math.isfinite(vector_scale) or vector_scale <= 0.0:
        raise AssessmentError(f"rigid mode {name} has zero or non-finite amplitude")
    residual = np.asarray(body_matrix @ vector).reshape(-1)
    residual_inf = float(np.max(np.abs(residual)))
    denominator = scale * vector_scale
    relative = residual_inf / denominator
    return {
        "mode": name,
        "declared_amplitude": displacement_scale,
        "mode_infinity_norm_mm": vector_scale,
        "operator_scale_times_mode_norm_N": denominator,
        "residual_infinity_norm_N": residual_inf,
        "relative_residual": relative,
        "within_tolerance": relative <= RIGID_RELATIVE_TOLERANCE,
    }


def assess_frame_export(sti_path: Path, dof_path: Path, model_path: Path) -> dict[str, object]:
    source = load_frame_source_model(model_path)
    labels = parse_dof_file(dof_path)
    require_dof_bijection(labels, source["physical_nodes"], FRAME_DOF_COUNT)
    owner_by_node = source["owner_by_node"]
    owner_by_row = np.fromiter(
        (owner_by_node[node] for node, _direction in labels),
        dtype=np.int16,
        count=len(labels),
    )
    body_names = list(source["bodies"])
    parsed = parse_upper_triangle_file(
        sti_path,
        len(labels),
        owner_by_row=owner_by_row,
        owner_names=body_names,
    )
    require_no_cross_body_coupling(parsed)
    modes = rigid_mode_screen(parsed["matrix"], labels, source)
    if modes["screened_body_count"] != FRAME_BODY_COUNT:
        raise AssessmentError("rigid-field screen did not cover all 50 source bodies")
    if modes["screened_rigid_mode_count"] != 6 * FRAME_BODY_COUNT:
        raise AssessmentError("rigid-field screen did not assess exactly 300 modes")
    if not modes["all_screened_modes_within_tolerance"]:
        raise AssessmentError(
            "one or more physical-body rigid modes exceed the declared tolerance"
        )
    return {
        "schema": "current_frame_pure_solid_export_assessment/v1",
        "status": "PASS_PURE_SOLID_SPARSE_STRUCTURE_AND_BODY_RIGID_MODE_SCREEN",
        "candidate": source["model"]["candidate"],
        "geometry_revision_id": source["model"]["geometry_revision_id"],
        "case_id": source["model"]["case_id"],
        "matrix_units": "N/mm",
        "dof_map": {
            "path": str(dof_path),
            "sha256": sha256_file(dof_path),
            "equation_count": len(labels),
            "physical_node_count": len(source["physical_nodes"]),
            "directions": [1, 2, 3],
            "bijection": True,
        },
        "stiffness": {
            "path": str(sti_path),
            "sha256": sha256_file(sti_path),
            "dimension": len(labels),
            "input_triangle": "one-based upper triangle, one unique pair per row",
            "triangle_pair_count": parsed["triangle_pair_count"],
            "reconstructed_symmetric_nonzero_count": parsed["symmetric_nonzero_count"],
            "explicit_zero_triangle_pair_count": parsed["explicit_zero_triangle_pair_count"],
            "diagonal_min_N_per_mm": parsed["diagonal_min_N_per_mm"],
            "diagonal_max_N_per_mm": parsed["diagonal_max_N_per_mm"],
            "symmetry_difference_max_abs_N_per_mm": parsed[
                "symmetry_difference_max_abs_N_per_mm"
            ],
            "cross_body_nonzero_pair_count": parsed["cross_body_nonzero_pair_count"],
            "cross_body_nonzero_examples": parsed["cross_body_nonzero_examples"],
        },
        "body_rigid_mode_screen": modes,
        "limits": [
            "This checks sparse export structure and six kinematic rigid fields per isolated source body.",
            "Small rigid-mode residuals do not establish exact full stiffness rank, positive definiteness on the deformational subspace, or absence of internal mechanisms.",
            "This is not a constrained frame operator, connector projection, gravity equilibrium, contact-state result, or design acceptance.",
            "Freeze and native execution provenance must be checked independently by the parent before relying on output hashes.",
        ],
    }


def parse_nodes_from_inp(path: Path) -> dict[int, np.ndarray]:
    nodes: dict[int, np.ndarray] = {}
    in_nodes = False
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            in_nodes = line.upper().split(",", 1)[0] == "*NODE"
            continue
        if not in_nodes:
            continue
        fields = [part.strip() for part in line.split(",")]
        if len(fields) != 4:
            raise AssessmentError(f"{path}:{line_number}: invalid free-cube node line")
        node = int(fields[0])
        xyz = np.asarray([float(item) for item in fields[1:]], dtype=np.float64)
        if node in nodes or not np.all(np.isfinite(xyz)):
            raise AssessmentError(f"{path}:{line_number}: duplicate or invalid node {node}")
        nodes[node] = xyz
    if len(nodes) != 20:
        raise AssessmentError(f"pinned free-cube input has {len(nodes)} nodes, expected 20")
    return nodes


def check_freecube_fixture() -> dict[str, object]:
    cube = BASE / "current-free-c3d20-matrix-export-native-attempt01"
    labels = parse_dof_file(ROOT / cube / "model.dof")
    nodes = parse_nodes_from_inp(ROOT / cube / "model.inp")
    require_dof_bijection(labels, set(nodes), 60)
    parsed = parse_upper_triangle_file(ROOT / cube / "model.sti", len(labels))
    matrix = parsed["matrix"]
    centroid = np.mean(np.vstack([nodes[node] for node in sorted(nodes)]), axis=0)
    single_body_source = {
        "owner_by_node": {node: 0 for node in nodes},
        "bodies": {"free_unit_cube": set(nodes)},
        "coordinates": nodes,
        "centroids": {"free_unit_cube": centroid},
    }
    screen = rigid_mode_screen(matrix, labels, single_body_source)
    row_by_label = {label: index for index, label in enumerate(labels)}
    rigid_residuals = []
    for axis_index in range(3):
        for rotation in (False, True):
            vector = np.zeros(len(labels), dtype=np.float64)
            axis = np.eye(3)[axis_index]
            for node, xyz in nodes.items():
                displacement = np.cross(axis, xyz - centroid) if rotation else axis
                for direction in range(3):
                    vector[row_by_label[(node, direction + 1)]] = displacement[direction]
            residual = float(np.linalg.norm(matrix @ vector, ord=np.inf))
            scale = float(np.linalg.norm(matrix.toarray(), ord=np.inf))
            rigid_residuals.append(residual / (scale * np.linalg.norm(vector, ord=np.inf)))
    gamma = 0.01
    shear = np.asarray([
        gamma * nodes[node][1] if direction == 1 else 0.0
        for node, direction in labels
    ], dtype=np.float64)
    observed_energy = float(0.5 * shear @ (matrix @ shear))
    expected_energy = 0.5 * (1.0 / (2.0 * (1.0 + 0.25))) * gamma**2
    relative_energy_error = abs(observed_energy - expected_energy) / expected_energy
    if parsed["triangle_pair_count"] != 1830:
        raise AssessmentError(
            f"free-cube triangle has {parsed['triangle_pair_count']} pairs, expected 1830"
        )
    if max(rigid_residuals) > RIGID_RELATIVE_TOLERANCE:
        raise AssessmentError("free-cube parser fixture failed the six rigid fields")
    if not screen["all_screened_modes_within_tolerance"]:
        raise AssessmentError("free-cube body screen failed its six rigid fields")
    if relative_energy_error > RIGID_RELATIVE_TOLERANCE:
        raise AssessmentError(
            f"free-cube analytic shear energy mismatch: relative error {relative_energy_error}"
        )
    prior = json.loads((ROOT / cube / "assessment.json").read_text(encoding="utf-8"))
    if prior.get("status") != "PASS_FREE_C3D20_MATRIX_EXPORT_ORACLE":
        raise AssessmentError("pinned parent-owned free-cube assessment is not a pass")
    return {
        "status": "PASS_PINNED_FREE_C3D20_SPARSE_PARSER_FIXTURE",
        "dof_count": len(labels),
        "upper_triangle_unique_pair_count": parsed["triangle_pair_count"],
        "positive_complete_diagonal": True,
        "reconstructed_symmetry_difference_max_abs_N_per_mm": parsed[
            "symmetry_difference_max_abs_N_per_mm"
        ],
        "max_relative_rigid_mode_residual": max(rigid_residuals),
        "body_screen_rigid_mode_residuals": [
            row["relative_residual"] for row in screen["bodies"][0]["modes"]
        ],
        "observed_shear_energy_N_mm": observed_energy,
        "expected_shear_energy_N_mm": expected_energy,
        "relative_shear_energy_error": relative_energy_error,
        "pinned_existing_known_answer_status": prior["status"],
        "checks_native_execution_provenance": False,
    }


def expect_rejection(
    name: str, text: list[str], dimension: int, expected_fragment: str
) -> dict[str, object]:
    try:
        parse_upper_triangle_lines(text, dimension, source=f"synthetic:{name}")
    except AssessmentError as exc:
        if expected_fragment not in str(exc):
            raise AssessmentError(
                f"synthetic {name}: rejected for unexpected reason: {exc}"
            ) from exc
        return {"case": name, "status": "PASS_REJECTED", "reason": str(exc)}
    raise AssessmentError(f"synthetic {name}: invalid matrix was accepted")


def run_parser_unit_fixtures() -> list[dict[str, object]]:
    valid_labels = parse_dof_lines(
        ["11.1", "11.2", "11.3", "22.1", "22.2", "22.3"], "synthetic.dof"
    )
    require_dof_bijection(valid_labels, {11, 22}, 6)
    mapping_tests = [{"case": "valid_node_direction_bijection", "status": "PASS"}]
    try:
        require_dof_bijection(valid_labels[:-1], {11, 22}, 6)
    except AssessmentError:
        mapping_tests.append({"case": "missing_equation_rejected", "status": "PASS"})
    else:
        raise AssessmentError("synthetic .dof missing-label test was accepted")
    try:
        parse_dof_lines(["11.1", "11.1"], "synthetic-duplicate.dof")
    except AssessmentError:
        mapping_tests.append({"case": "duplicate_equation_rejected", "status": "PASS"})
    else:
        raise AssessmentError("synthetic .dof duplicate-label test was accepted")

    valid = [
        "1 1 2.0",
        "1 2 -1.0",
        "2 2 3.0",
        "2 3 2.0",
        "3 3 4.0",
    ]
    parsed = parse_upper_triangle_lines(valid, 3, source="synthetic-valid")
    expected = np.asarray([[2.0, -1.0, 0.0], [-1.0, 3.0, 2.0], [0.0, 2.0, 4.0]])
    if not np.array_equal(parsed["matrix"].toarray(), expected):
        raise AssessmentError("synthetic signed triangle did not reconstruct exactly")
    if parsed["triangle_pair_count"] != 5:
        raise AssessmentError("synthetic triangle pair count is wrong")
    matrix_tests: list[dict[str, object]] = [{
        "case": "signed_offdiagonal_reconstruction_and_symmetry",
        "status": "PASS",
        "triangle_pair_count": parsed["triangle_pair_count"],
        "negative_offdiagonal_preserved": float(parsed["matrix"][0, 1]) == -1.0,
        "positive_offdiagonal_preserved": float(parsed["matrix"][1, 2]) == 2.0,
        "symmetry_difference_max_abs": parsed["symmetry_difference_max_abs_N_per_mm"],
    }]
    cases = [
        ("duplicate_pair", ["1 1 2", "1 2 -1", "1 2 -1", "2 2 3"], 2, "duplicate triangular pair"),
        ("lower_triangle", ["1 1 2", "2 1 -1", "2 2 3"], 2, "lower-triangle"),
        ("out_of_range_index", ["1 1 2", "1 3 1", "2 2 3"], 2, "outside"),
        ("missing_diagonal", ["1 1 2", "1 2 1"], 2, "missing diagonal"),
        ("nonpositive_diagonal", ["1 1 2", "1 2 1", "2 2 0"], 2, "strictly positive"),
        ("nonfinite_value", ["1 1 2", "1 2 nan", "2 2 3"], 2, "non-finite"),
        ("malformed_triplet", ["1 1 2", "1 2", "2 2 3"], 2, "expected row column value"),
    ]
    matrix_tests.extend(
        expect_rejection(name, text, dimension, fragment)
        for name, text, dimension, fragment in cases
    )
    body_owners = np.asarray([0, 0, 1], dtype=np.int16)
    coupled = parse_upper_triangle_lines(
        ["1 1 2", "2 2 3", "2 3 -0.5", "3 3 4"],
        3,
        source="synthetic-cross-body",
        owner_by_row=body_owners,
        owner_names=["body_a", "body_b"],
    )
    try:
        require_no_cross_body_coupling(coupled)
    except AssessmentError as exc:
        if "cross-body" not in str(exc):
            raise
        matrix_tests.append({
            "case": "nonzero_cross_body_coupling_rejected",
            "status": "PASS_REJECTED",
            "detected_pair_count": coupled["cross_body_nonzero_pair_count"],
        })
    else:
        raise AssessmentError("synthetic cross-body coupling was accepted")
    disconnected = parse_upper_triangle_lines(
        ["1 1 2", "2 2 3", "2 3 0", "3 3 4"],
        3,
        source="synthetic-zero-cross-body",
        owner_by_row=body_owners,
        owner_names=["body_a", "body_b"],
    )
    require_no_cross_body_coupling(disconnected)
    matrix_tests.append({
        "case": "explicit_zero_cross_body_pair_allowed",
        "status": "PASS",
        "detected_pair_count": disconnected["cross_body_nonzero_pair_count"],
    })
    return mapping_tests + matrix_tests


def verify_fixtures() -> dict[str, object]:
    pins = verify_source_pins()
    freecube = check_freecube_fixture()
    parser_tests = run_parser_unit_fixtures()
    return {
        "schema": "current_frame_pure_solid_export_assessment_fixtures/v1",
        "status": "PASS_SPARSE_READER_FIXTURES",
        "runtime": {
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "source_pin_count": len(pins["files"]),
        "freecube": freecube,
        "synthetic_tests": parser_tests,
        "frame_matrix_assessed": False,
        "native_execution_launched": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--verify-fixtures", action="store_true")
    operation.add_argument("--assess-matrix", type=Path, metavar="JOB_BASE")
    args = parser.parse_args()
    try:
        verify_source_pins()
        if args.verify_fixtures:
            result = verify_fixtures()
        else:
            base = args.assess_matrix
            result = assess_frame_export(
                base.with_suffix(".sti"),
                base.with_suffix(".dof"),
                ROOT / FRAME_MODEL_REL,
            )
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (AssessmentError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({
            "status": "REJECT_SPARSE_MATRIX_ASSESSMENT",
            "error": str(exc),
            "frame_ready": False,
        }, indent=2, sort_keys=True, allow_nan=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
