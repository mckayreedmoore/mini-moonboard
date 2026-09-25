"""Stream an unloaded CCX matrix for one candidate rigid translation witness.

This audit expands CalculiX's stored symmetric coordinate triangle by action on
vectors; it never constructs a dense stiffness matrix and makes no general
nullity, stability, capacity, or acceptance claim.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from fea.wood_joint_patch_contact_contract import parse_c3d10_deck

ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
MESH_REPORT_PATH = EVALUATION_DIR / "ordinary-patch-mesh-attempt02/mesh/mesh.json"
MESH_DECK_PATH = EVALUATION_DIR / "ordinary-patch-mesh-attempt02/mesh/mesh.inp"

SCHEMA = "wood_joint_current_matrix_witness/v1"
MESH_SCHEMA = "wood_joint_current_patch_mesh/v1"
MESH_STATUS = "VERIFIED_C3D10_CURRENT_PATCH_MESH_ONLY_NO_SOLVER"
MESH_REPORT_SHA256 = "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07"
MESH_DECK_SHA256 = "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803"
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
TARGET_BODY_ID = "W00_BOTTOM_CENTER_RIGHT_CLEAT"
TARGET_SOURCE_BODY_ID = "bottom_center_right_cleat"
TARGET_DIRECTION = (0.0, -0.766044443118978, 0.6427876096865394)
NULL_RESIDUAL_LIMIT = 1e-8

# Verified against the official CalculiX 2.21 source archive and these writers.
CCX_SOURCE_WITNESS = {
    "version": "2.21",
    "archive_sha256": "52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad",
    "matrixstorage_c_sha256": "211ec4bbb5bb2b6ec0bc3748520774a6562bb54a22088cdf8911b6d4ba363abe",
    "gennactdofinv_f_sha256": "ab4cae9907d229b78867a27c2fe70111484b43659097511150d5a7e9cdfdcb75",
    "matrix_triangle_semantics": (
        "matrixstorage writes neq diagonal entries and nzs off-diagonal entries "
        "from one symmetric profile triangle as 1-based row column value, then "
        "sorts by column and row. The untransformed branch writes (i+1,irow); "
        "the transformed branch explicitly retains row<=column. Determine the "
        "actual upper/lower orientation from the emitted coordinate records."
    ),
    "dof_semantics": (
        "matrixstorage writes one node.direction label per equation index, "
        "with direction IDs from the active degree-of-freedom map."
    ),
}

EXPECTED_BODY_IDS = frozenset(
    [
        "M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION",
        "M01_A00_HEAD_WASHER",
        "M02_A00_NUT_WASHER",
        "M03_A00_NUT",
        "M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION",
        "M05_A01_HEAD_WASHER",
        "M06_A01_NUT_WASHER",
        "M07_A01_NUT",
        "M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION",
        "M09_A02_HEAD_WASHER",
        "M10_A02_NUT_WASHER",
        "M11_A02_NUT",
        "M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION",
        "M13_A03_HEAD_WASHER",
        "M14_A03_NUT_WASHER",
        "M15_A03_NUT",
        "W00_BOTTOM_CENTER_RIGHT_CLEAT",
        "W01_BASE_RAIL_BOTTOM_RIGHT",
        "W02_BASE_PRINCIPAL_CENTER_RIGHT",
    ]
)


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _vector(value: Sequence[float], size: int, label: str) -> np.ndarray:
    try:
        vector = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} must be a finite vector of length {size}") from error
    if vector.shape != (size,) or not np.isfinite(vector).all():
        raise ValueError(f"{label} must be a finite vector of length {size}")
    return vector


def _norm2(values: np.ndarray) -> float:
    result = 0.0
    for value in values:
        result = math.hypot(result, float(value))
    return result


def _norm_inf(values: np.ndarray) -> float:
    return float(np.max(np.abs(values))) if values.size else 0.0


def _summarize_action(
    vector: np.ndarray, product: np.ndarray, absolute_product: np.ndarray
) -> dict[str, Any]:
    energy = math.fsum(
        float(left) * float(right) for left, right in zip(vector, product, strict=True)
    )
    energy_scale = math.fsum(
        abs(float(left)) * float(right)
        for left, right in zip(vector, absolute_product, strict=True)
    )
    residual_inf = _norm_inf(product)
    scale_inf = _norm_inf(absolute_product)
    relative_inf = (
        residual_inf / scale_inf
        if scale_inf
        else (0.0 if residual_inf == 0 else math.inf)
    )
    return {
        "vector_l2_norm": _norm2(vector),
        "kv_l2_norm": _norm2(product),
        "kv_inf_norm": residual_inf,
        "abs_k_abs_v_l2_norm": _norm2(absolute_product),
        "abs_k_abs_v_inf_norm": scale_inf,
        "scaled_residual_inf": relative_inf,
        "scaled_residual_definition": "||Kv||_inf / || |K| |v| ||_inf",
        "quadratic_form_vtkv": energy,
        "absolute_quadratic_scale_sum_abs_v_abs_k_abs_v": energy_scale,
        "scaled_quadratic_form": energy / energy_scale if energy_scale else 0.0,
    }


def _matrix_state(
    dimension: int, vectors: Mapping[str, Sequence[float]]
) -> dict[str, Any]:
    if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension <= 0:
        raise ValueError("dimension must be a positive integer")
    if not vectors:
        raise ValueError("at least one probe vector is required")
    vector_arrays = {
        name: _vector(value, dimension, name) for name, value in vectors.items()
    }
    return {
        "dimension": dimension,
        "vectors": vector_arrays,
        "products": {name: np.zeros(dimension) for name in vectors},
        "product_corrections": {name: np.zeros(dimension) for name in vectors},
        "absolute_products": {name: np.zeros(dimension) for name in vectors},
        "absolute_corrections": {name: np.zeros(dimension) for name in vectors},
        "diagonal_seen": np.zeros(dimension, dtype=np.bool_),
        "previous_key": None,
        "orientation": None,
        "record_count": 0,
        "diagonal_count": 0,
        "zero_count": 0,
        "negative_count": 0,
        "maximum_absolute_entry": 0.0,
    }


def _accumulate_matrix_chunk(
    state: dict[str, Any],
    rows_one_based: np.ndarray,
    columns_one_based: np.ndarray,
    values: np.ndarray,
) -> None:
    dimension = state["dimension"]
    if (
        rows_one_based.ndim != 1
        or columns_one_based.shape != rows_one_based.shape
        or values.shape != rows_one_based.shape
    ):
        raise ValueError(
            "matrix chunk must have matching one-dimensional row, column, value arrays"
        )
    if not rows_one_based.size:
        return
    if (
        not np.isfinite(rows_one_based).all()
        or not np.isfinite(columns_one_based).all()
        or not np.equal(rows_one_based, np.floor(rows_one_based)).all()
        or not np.equal(columns_one_based, np.floor(columns_one_based)).all()
    ):
        raise ValueError("matrix coordinates must be finite integers")
    if not np.isfinite(values).all():
        raise ValueError("matrix coefficient is not finite")
    if (
        np.any(rows_one_based < 1)
        or np.any(columns_one_based < 1)
        or np.any(rows_one_based > dimension)
        or np.any(columns_one_based > dimension)
    ):
        raise ValueError(f"matrix coordinates outside 1..{dimension}")
    rows = rows_one_based.astype(np.int64) - 1
    columns = columns_one_based.astype(np.int64) - 1
    current_order_bad = (columns[1:] < columns[:-1]) | (
        (columns[1:] == columns[:-1]) & (rows[1:] <= rows[:-1])
    )
    if current_order_bad.any():
        index = int(np.flatnonzero(current_order_bad)[0]) + 1
        same = columns[index] == columns[index - 1] and rows[index] == rows[index - 1]
        reason = (
            "duplicate coordinate"
            if same
            else "records are not sorted by column then row"
        )
        raise ValueError(f"matrix record {state['record_count'] + index + 1}: {reason}")
    previous_key = state["previous_key"]
    first_key = (int(columns[0]), int(rows[0]))
    if previous_key is not None and first_key <= previous_key:
        reason = (
            "duplicate coordinate"
            if first_key == previous_key
            else "records are not sorted by column then row"
        )
        raise ValueError(f"matrix record {state['record_count'] + 1}: {reason}")
    state["previous_key"] = (int(columns[-1]), int(rows[-1]))

    diagonal = rows == columns
    diagonal_rows = rows[diagonal]
    if diagonal_rows.size:
        if state["diagonal_seen"][diagonal_rows].any():
            raise ValueError("matrix has a duplicate diagonal record")
        state["diagonal_seen"][diagonal_rows] = True
    off_diagonal = ~diagonal
    if off_diagonal.any():
        lower = np.any(rows[off_diagonal] > columns[off_diagonal])
        upper = np.any(rows[off_diagonal] < columns[off_diagonal])
        if lower and upper:
            raise ValueError("matrix records mix upper and lower triangle entries")
        this_orientation = "lower" if lower else "upper"
        if (
            state["orientation"] is not None
            and state["orientation"] != this_orientation
        ):
            raise ValueError("matrix records mix upper and lower triangle entries")
        state["orientation"] = this_orientation

    off_rows = rows[off_diagonal]
    off_columns = columns[off_diagonal]
    off_values = values[off_diagonal]
    absolute_values = np.abs(values)
    for name, vector in state["vectors"].items():
        row_weights = values * vector[columns]
        absolute_row_weights = absolute_values * np.abs(vector[columns])
        row_product = np.bincount(rows, weights=row_weights, minlength=dimension)
        row_absolute = np.bincount(
            rows, weights=absolute_row_weights, minlength=dimension
        )
        if off_rows.size:
            row_product += np.bincount(
                off_columns, weights=off_values * vector[off_rows], minlength=dimension
            )
            row_absolute += np.bincount(
                off_columns,
                weights=np.abs(off_values) * np.abs(vector[off_rows]),
                minlength=dimension,
            )
        product = state["products"][name]
        correction = state["product_corrections"][name]
        adjusted = row_product - correction
        updated = product + adjusted
        correction[:] = (updated - product) - adjusted
        product[:] = updated
        absolute_product = state["absolute_products"][name]
        absolute_correction = state["absolute_corrections"][name]
        adjusted_absolute = row_absolute - absolute_correction
        updated_absolute = absolute_product + adjusted_absolute
        absolute_correction[:] = (
            updated_absolute - absolute_product
        ) - adjusted_absolute
        absolute_product[:] = updated_absolute

    state["record_count"] += int(values.size)
    state["diagonal_count"] += int(np.count_nonzero(diagonal))
    state["zero_count"] += int(np.count_nonzero(values == 0.0))
    state["negative_count"] += int(np.count_nonzero(values < 0.0))
    state["maximum_absolute_entry"] = max(
        float(state["maximum_absolute_entry"]), float(np.max(absolute_values))
    )


def _finish_matrix(state: dict[str, Any]) -> dict[str, Any]:
    if state["record_count"] == 0:
        raise ValueError("matrix has no coordinate records")
    missing_diagonals = np.flatnonzero(~state["diagonal_seen"])
    if missing_diagonals.size:
        preview = ",".join(str(int(item) + 1) for item in missing_diagonals[:8])
        raise ValueError(
            f"matrix is missing {missing_diagonals.size} diagonal records: {preview}"
        )
    if any(
        not np.isfinite(array).all()
        for collection in (state["products"], state["absolute_products"])
        for array in collection.values()
    ):
        raise ValueError("matrix action overflowed to a non-finite value")
    return {
        "matrix_dimension": state["dimension"],
        "coordinate_record_count": state["record_count"],
        "diagonal_record_count": state["diagonal_count"],
        "off_diagonal_record_count": state["record_count"] - state["diagonal_count"],
        "implicit_symmetric_triangle": state["orientation"] or "diagonal_only",
        "all_matrix_coefficients_finite": True,
        "zero_coefficient_count": state["zero_count"],
        "negative_coefficient_count": state["negative_count"],
        "maximum_absolute_coefficient": state["maximum_absolute_entry"],
        "probes": {
            name: _summarize_action(
                state["vectors"][name],
                state["products"][name],
                state["absolute_products"][name],
            )
            for name in state["vectors"]
        },
    }


def evaluate_symmetric_coordinate_chunks(
    chunks: Iterable[np.ndarray],
    dimension: int,
    vectors: Mapping[str, Sequence[float]],
) -> dict[str, Any]:
    """Evaluate a chunked, sorted coordinate triangle without assembling K."""
    state = _matrix_state(dimension, vectors)
    for chunk in chunks:
        values = np.asarray(chunk, dtype=np.float64)
        if values.ndim != 2 or values.shape[1] != 3:
            raise ValueError("matrix chunks must have exactly three columns")
        _accumulate_matrix_chunk(state, values[:, 0], values[:, 1], values[:, 2])
    return _finish_matrix(state)


def evaluate_symmetric_coordinate_matrix(
    entries: Iterable[tuple[int, int, float]],
    dimension: int,
    vectors: Mapping[str, Sequence[float]],
    *,
    chunk_records: int = 100_000,
) -> dict[str, Any]:
    """Evaluate Kx and |K||x| from a sorted symmetric coordinate triangle.

    Coordinates are 1-based and ordered by (column, row), matching CCX's
    ``isortiid(aj, ai, ...)`` output. Either one consistent upper or lower
    triangle is accepted. No dense matrix or full entry list is retained.
    """
    if (
        isinstance(chunk_records, bool)
        or not isinstance(chunk_records, int)
        or chunk_records <= 0
    ):
        raise ValueError("chunk_records must be a positive integer")

    def chunks() -> Iterable[np.ndarray]:
        pending: list[tuple[int, int, float]] = []
        for record_index, record in enumerate(entries, start=1):
            if len(record) != 3:
                raise ValueError(
                    f"matrix record {record_index}: expected row, column, value"
                )
            row, column, raw_value = record
            if (
                isinstance(row, bool)
                or isinstance(column, bool)
                or not isinstance(row, int)
                or not isinstance(column, int)
            ):
                raise TypeError(
                    f"matrix record {record_index}: coordinates must be integers"
                )
            try:
                value = float(raw_value)
            except (TypeError, ValueError, OverflowError) as error:
                raise ValueError(
                    f"matrix record {record_index}: invalid coefficient"
                ) from error
            pending.append((row, column, value))
            if len(pending) >= chunk_records:
                yield np.asarray(pending, dtype=np.float64)
                pending.clear()
        if pending:
            yield np.asarray(pending, dtype=np.float64)

    return evaluate_symmetric_coordinate_chunks(chunks(), dimension, vectors)


def _iter_sti_chunks(
    path: str | Path, *, records_per_chunk: int = 200_000
) -> Iterable[np.ndarray]:
    with Path(path).open("r", encoding="ascii") as stream:
        while True:
            lines = list(itertools.islice(stream, records_per_chunk))
            if not lines:
                break
            try:
                chunk = np.loadtxt(
                    lines,
                    dtype=np.float64,
                    comments=None,
                    ndmin=2,
                )
            except (TypeError, ValueError, OverflowError) as error:
                raise ValueError(
                    f".sti contains an invalid coordinate chunk: {error}"
                ) from error
            if not chunk.size:
                break
            if chunk.shape[1] != 3:
                raise ValueError(
                    ".sti coordinate records must have exactly three columns"
                )
            yield chunk
            if len(lines) < records_per_chunk:
                break


def _read_dof(path: str | Path) -> list[tuple[int, int]]:
    labels: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    with Path(path).open("r", encoding="ascii") as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            line = raw_line.strip()
            if not line:
                continue
            match = re.fullmatch(r"([0-9]+)\.([0-9]+)", line)
            if not match:
                raise ValueError(f".dof line {line_number}: expected node.direction")
            node, direction = (int(value) for value in match.groups())
            if node <= 0 or direction < 1 or direction > 6:
                raise ValueError(f".dof line {line_number}: invalid node or direction")
            label = (node, direction)
            if label in seen:
                raise ValueError(
                    f".dof line {line_number}: duplicate node.direction label {label}"
                )
            seen.add(label)
            labels.append(label)
    if not labels:
        raise ValueError(".dof has no active equations")
    return labels


def _check_frequency_deck(
    path: str | Path, *, expected_mesh_deck_sha256: str | None = None
) -> dict[str, Any]:
    frequencies: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    end_steps = 0
    forbidden_load_cards: list[str] = []
    prestress_initial_conditions: list[str] = []
    include_paths: dict[Path, str] = {}
    forbidden_load_names = {
        "CLOAD",
        "DLOAD",
        "DSLOAD",
        "DFLUX",
        "CFLUX",
        "BODY FORCE",
        "GRAVITY",
        "RADIATE",
        "FILM",
        "HEAT GENERATION",
        "TEMPERATURE",
    }
    pending = [Path(path).resolve()]
    while pending:
        source = pending.pop()
        if source in include_paths:
            continue
        try:
            file_sha256 = _sha256(source)
            with source.open("r", encoding="utf-8", errors="strict") as stream:
                rows = list(enumerate(stream, start=1))
        except OSError as error:
            raise ValueError(f"matrix input include is missing: {source}") from error
        include_paths[source] = file_sha256
        for line_number, raw_line in rows:
            line = raw_line.strip()
            if not line or line.startswith("**") or not line.startswith("*"):
                continue
            fields = [cell.strip() for cell in line[1:].split(",")]
            name = fields[0].upper()
            option_cells = fields[1:]
            options = {cell.upper() for cell in option_cells}
            if name == "INCLUDE":
                include_value = next(
                    (
                        value.strip().strip("\"'")
                        for cell in option_cells
                        for key, separator, value in [cell.partition("=")]
                        if separator and key.upper() in {"INPUT", "FILE"}
                    ),
                    None,
                )
                if not include_value:
                    raise ValueError(
                        f"input include line {line_number} has no INPUT or FILE path"
                    )
                include_path = (source.parent / include_value).resolve()
                if not include_path.is_file():
                    raise ValueError(f"matrix input include is missing: {include_path}")
                pending.append(include_path)
            elif name == "STEP":
                steps.append(
                    {
                        "line": line_number,
                        "perturbation": "PERTURBATION" in options,
                    }
                )
            elif name == "END STEP":
                end_steps += 1
            elif name == "FREQUENCY":
                frequencies.append(
                    {
                        "line": line_number,
                        "frequency_perturbation_option": "PERTURBATION" in options,
                        "solver_matrixstorage": "SOLVER=MATRIXSTORAGE" in options,
                    }
                )
            elif name in forbidden_load_names:
                forbidden_load_cards.append(f"{name}@{source.name}:{line_number}")
            elif name == "INITIAL CONDITIONS" and any(
                option in {"TYPE=STRESS", "STRESS"} for option in options
            ):
                prestress_initial_conditions.append(
                    f"{name}@{source.name}:{line_number}"
                )
    if len(steps) != 1 or end_steps != 1 or len(frequencies) != 1:
        raise ValueError(
            "matrix input must contain exactly one *STEP, one *FREQUENCY, and one *END STEP"
        )
    step = steps[0]
    frequency = frequencies[0]
    if not step["perturbation"] or not frequency["solver_matrixstorage"]:
        raise ValueError(
            "*STEP must specify PERTURBATION and *FREQUENCY must specify SOLVER=MATRIXSTORAGE"
        )
    if forbidden_load_cards:
        raise ValueError(
            f"unloaded reference deck contains applied load cards: {forbidden_load_cards[:8]}"
        )
    if prestress_initial_conditions:
        raise ValueError("unloaded reference deck contains stress initial conditions")
    if (
        expected_mesh_deck_sha256 is not None
        and expected_mesh_deck_sha256 not in include_paths.values()
    ):
        raise ValueError(
            "matrix input include tree does not contain the exact frozen mesh deck"
        )
    return {
        "step_count": len(steps),
        "step_perturbation": step["perturbation"],
        "frequency_card": frequency,
        "applied_load_cards": forbidden_load_cards,
        "stress_initial_condition_cards": prestress_initial_conditions,
        "include_tree_sha256": {
            str(source): digest for source, digest in sorted(include_paths.items())
        },
        "frozen_mesh_deck_included": expected_mesh_deck_sha256 is not None,
        "unloaded_frequency_reference_deck": True,
        "contact_active_set_or_zero_pressure_state_proven": False,
    }


def _load_mesh_ownership(
    mesh_report_path: str | Path, mesh_deck_path: str | Path
) -> tuple[dict[str, Any], dict[int, tuple[float, float, float]], dict[int, str]]:
    """Read and cross-check the report and C3D10 ownership without remeshing."""
    report_path = Path(mesh_report_path)
    deck_path = Path(mesh_deck_path)
    report_raw = report_path.read_bytes()
    try:
        report = json.loads(report_raw)
    except json.JSONDecodeError as error:
        raise ValueError("mesh report JSON is invalid") from error
    if not isinstance(report, dict):
        raise TypeError("mesh report root must be an object")
    if hashlib.sha256(report_raw).hexdigest() != MESH_REPORT_SHA256:
        raise ValueError("frozen mesh report digest mismatch")
    if _sha256(deck_path) != MESH_DECK_SHA256:
        raise ValueError("frozen mesh deck digest mismatch")
    if (
        report.get("schema") != MESH_SCHEMA
        or report.get("status") != MESH_STATUS
        or report.get("current_candidate_binding", {}).get("revision_id") != REVISION_ID
        or report.get("accepted") is not False
        or report.get("solved") is not False
    ):
        raise ValueError(
            "mesh report is not the frozen current-patch geometry-only artifact"
        )
    bodies = report.get("bodies")
    if not isinstance(bodies, dict) or set(bodies) != EXPECTED_BODY_IDS:
        raise ValueError(
            "frozen mesh does not contain the exact 19 current-patch body owners"
        )
    deck_nodes, deck_elements, deck_elsets = parse_c3d10_deck(
        deck_path.read_text(encoding="utf-8"), context="frozen current mesh"
    )
    node_owner: dict[int, str] = {}
    for mesh_body_id, row in bodies.items():
        if not isinstance(row, dict):
            raise TypeError(f"mesh body {mesh_body_id} record must be an object")
        if (
            mesh_body_id == TARGET_BODY_ID
            and row.get("source_body_id") != TARGET_SOURCE_BODY_ID
        ):
            raise ValueError(
                "cleat body owner does not match bottom_center_right_cleat"
            )
        try:
            body_nodes = {int(node_id) for node_id in row["nodes"]}
            body_elements = {int(element_id) for element_id in row["elements"]}
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                f"mesh body {mesh_body_id} has invalid owner lists"
            ) from error
        if not body_nodes or not body_elements:
            raise ValueError(f"mesh body {mesh_body_id} is empty")
        for node_id in body_nodes:
            if node_id in node_owner:
                raise ValueError(f"mesh node {node_id} has more than one owner")
            node_owner[node_id] = mesh_body_id
        elset_name = str(row.get("element_elset_name", "")).upper()
        if not elset_name or deck_elsets.get(elset_name) != body_elements:
            raise ValueError(
                f"mesh body {mesh_body_id} does not resolve to its exact deck ELSET"
            )
        referenced_nodes = {
            node_id
            for element_id in body_elements
            for node_id in deck_elements[element_id]
        }
        if body_nodes != referenced_nodes:
            raise ValueError(
                f"mesh body {mesh_body_id} node ownership differs from its C3D10 ELSET"
            )
    if set(node_owner) != set(deck_nodes):
        raise ValueError(
            "frozen mesh deck nodes do not exactly match the 19 body node owners"
        )
    return report, deck_nodes, node_owner


def _build_probe_vectors(
    dof_labels: Sequence[tuple[int, int]],
    mesh_nodes: Mapping[int, tuple[float, float, float]],
    node_owner: Mapping[int, str],
    control_node_ids: Sequence[int],
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    controls = set()
    for value in control_node_ids:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("control_node_ids must contain positive integer IDs")
        controls.add(value)
    cleat_nodes = {
        node for node, owner in node_owner.items() if owner == TARGET_BODY_ID
    }
    if not cleat_nodes:
        raise ValueError("frozen mesh has no cleat nodes")
    if controls & cleat_nodes:
        raise ValueError("external control-node ownership overlaps the cleat body")
    unknown_nodes = {node for node, _direction in dof_labels} - set(node_owner)
    if unknown_nodes != (unknown_nodes & controls):
        missing = sorted(unknown_nodes - controls)
        raise ValueError(
            f".dof contains nonmesh nodes without explicit control ownership: {missing[:8]}"
        )
    if controls & set(node_owner):
        control_mesh_overlap = sorted(controls & set(node_owner))
    else:
        control_mesh_overlap = []
    labels_by_node: dict[int, dict[int, int]] = {}
    owner_dof_counts = {
        owner: {
            "equation_count": 0,
            "nodes_with_active_equations": set(),
            "direction_counts": {},
        }
        for owner in sorted(set(node_owner.values()))
    }
    control_directions: dict[int, set[int]] = {}
    for equation_index, (node, direction) in enumerate(dof_labels):
        if node in node_owner and direction > 3:
            raise ValueError(
                f"solid mesh node {node} has nontranslational active direction {direction}"
            )
        labels_by_node.setdefault(node, {})[direction] = equation_index
        if node in node_owner:
            owner = node_owner[node]
            owner_count = owner_dof_counts[owner]
            owner_count["equation_count"] += 1
            owner_count["nodes_with_active_equations"].add(node)
            directions = owner_count["direction_counts"]
            direction_key = str(direction)
            directions[direction_key] = directions.get(direction_key, 0) + 1
        else:
            control_directions.setdefault(node, set()).add(direction)
    candidate = np.zeros(len(dof_labels), dtype=np.float64)
    comparison = np.zeros(len(dof_labels), dtype=np.float64)
    direction = np.asarray(TARGET_DIRECTION, dtype=np.float64)
    if not math.isclose(
        float(np.linalg.norm(direction)), 1.0, rel_tol=0.0, abs_tol=1e-14
    ):
        raise RuntimeError("frozen translation direction is not a unit vector")
    for node in cleat_nodes:
        node_dofs = labels_by_node.get(node, {})
        if set(node_dofs) != {1, 2, 3}:
            raise ValueError(
                f"cleat node {node} does not have all three active translation DOFs"
            )
        for dof_direction, component in enumerate(direction, start=1):
            candidate[node_dofs[dof_direction]] = component
    coordinates = np.asarray(
        [mesh_nodes[node] for node in sorted(cleat_nodes)], dtype=np.float64
    )
    x = coordinates[:, 0]
    centered_x = x - float(math.fsum(float(value) for value in x) / len(x))
    variation = _norm2(centered_x)
    if not math.isfinite(variation) or variation <= 0:
        raise ValueError(
            "cleat mesh has no global-X coordinate variation for comparison witness"
        )
    centered_x /= variation
    for node, displacement in zip(sorted(cleat_nodes), centered_x, strict=True):
        comparison[labels_by_node[node][1]] = float(displacement)
    serialized_owner_dof_counts = {
        owner: {
            "equation_count": row["equation_count"],
            "nodes_with_active_equations": len(row["nodes_with_active_equations"]),
            "direction_counts": dict(sorted(row["direction_counts"].items())),
        }
        for owner, row in owner_dof_counts.items()
    }
    return (
        candidate,
        comparison,
        {
            "target_mesh_body_id": TARGET_BODY_ID,
            "target_source_body_id": TARGET_SOURCE_BODY_ID,
            "target_mesh_node_count": len(cleat_nodes),
            "target_active_translation_dof_count": 3 * len(cleat_nodes),
            "candidate_direction_global_xyz": list(TARGET_DIRECTION),
            "declared_control_node_ids": sorted(controls),
            "declared_control_node_ids_in_mesh": control_mesh_overlap,
            "observed_nonmesh_control_node_ids": sorted(unknown_nodes),
            "external_control_node_active_directions": {
                str(node): sorted(control_directions.get(node, set()))
                for node in sorted(controls)
            },
            "active_dofs_by_mesh_owner": serialized_owner_dof_counts,
            "all_non_target_active_mesh_equation_entries_zero": True,
            "all_control_nodes_zero_in_candidate": True,
            "dependent_dof_values_reconstructed_by_this_audit": False,
            "comparison_witness": "cleat-only centered global-X affine displacement, Euclidean-normalized",
        },
    )


def audit_current_matrix_witness(
    sti_path: str | Path,
    dof_path: str | Path,
    input_deck_path: str | Path,
    *,
    control_node_ids: Sequence[int] = (),
    mesh_report_path: str | Path = MESH_REPORT_PATH,
    mesh_deck_path: str | Path = MESH_DECK_PATH,
    native_log_path: str | Path | None = None,
) -> dict[str, Any]:
    """Audit one CCX ``.sti`` / ``.dof`` pair against the frozen current mesh."""
    deck_check = _check_frequency_deck(
        input_deck_path, expected_mesh_deck_sha256=MESH_DECK_SHA256
    )
    _mesh_report, mesh_nodes, node_owner = _load_mesh_ownership(
        mesh_report_path, mesh_deck_path
    )
    dof_labels = _read_dof(dof_path)
    candidate, comparison, vector_scope = _build_probe_vectors(
        dof_labels, mesh_nodes, node_owner, control_node_ids
    )
    matrix = evaluate_symmetric_coordinate_chunks(
        _iter_sti_chunks(sti_path),
        len(dof_labels),
        {"cleat_normal_translation": candidate, "cleat_affine_strain": comparison},
    )
    candidate_summary = matrix["probes"]["cleat_normal_translation"]
    comparison_summary = matrix["probes"]["cleat_affine_strain"]
    candidate_pass = candidate_summary["scaled_residual_inf"] <= NULL_RESIDUAL_LIMIT
    positive_comparison = comparison_summary["quadratic_form_vtkv"] > 0.0
    source_paths: dict[str, str] = {}
    source_file_paths: dict[str, str] = {}
    for key, path in {
        "sti": sti_path,
        "dof": dof_path,
        "input_deck": input_deck_path,
        "mesh_report": mesh_report_path,
        "mesh_deck": mesh_deck_path,
    }.items():
        source_paths[key] = _sha256(path)
        source_file_paths[key] = str(Path(path).resolve())
    source_paths["auditor_implementation"] = _sha256(__file__)
    source_file_paths["auditor_implementation"] = str(Path(__file__).resolve())
    source_paths.update(
        {
            f"input_include:{Path(source).name}": digest
            for source, digest in deck_check["include_tree_sha256"].items()
        }
    )
    source_file_paths.update(
        {
            f"input_include:{Path(source).name}": source
            for source in deck_check["include_tree_sha256"]
        }
    )
    if native_log_path is not None:
        source_paths["native_log"] = _sha256(native_log_path)
        log_text = Path(native_log_path).read_text(encoding="utf-8", errors="replace")
        version_match = re.search(
            r"CalculiX\s+(?:Version\s+)?(\d+\.\d+)", log_text, re.IGNORECASE
        )
        observed_version = version_match.group(1) if version_match else None
    else:
        observed_version = None
    return {
        "schema": SCHEMA,
        "status": "CANDIDATE_NULL_VECTOR_WITNESS_PASSED"
        if candidate_pass
        else "CANDIDATE_NULL_VECTOR_WITNESS_NOT_PASSED",
        "accepted": False,
        "response_ready": False,
        "capacity_claim": False,
        "universal_nullity_claim": False,
        "structural_acceptance_claim": False,
        "native_solver_run_by_auditor": False,
        "matrix_scope": {
            "matrix_kind": "CCX linearized frequency perturbation stiffness tangent",
            "deck_audit": deck_check,
            "native_version_observed_in_log": observed_version,
            "native_version_verified": observed_version == "2.21",
            "matrix_semantics_source": CCX_SOURCE_WITNESS,
            **{key: value for key, value in matrix.items() if key != "probes"},
        },
        "vector_scope": vector_scope,
        "candidate_null_vector": {
            **candidate_summary,
            "scaled_residual_acceptance_limit": NULL_RESIDUAL_LIMIT,
            "specific_candidate_witness_passed": candidate_pass,
            "interpretation": (
                "This tests only the declared cleat translation at this one "
                "reference tangent; it does not establish total nullity or response."
            ),
        },
        "positive_elastic_comparison": {
            **comparison_summary,
            "positive_quadratic_form": positive_comparison,
            "interpretation": (
                "A normalized affine-strain vector on the cleat has positive "
                "quadratic form as a comparative elastic witness only."
            ),
        },
        "source_sha256": source_paths,
        "source_paths": source_file_paths,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sti", type=Path)
    parser.add_argument("dof", type=Path)
    parser.add_argument("input_deck", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--control-node", action="append", type=int, default=[])
    parser.add_argument("--native-log", type=Path)
    args = parser.parse_args()
    report = audit_current_matrix_witness(
        args.sti,
        args.dof,
        args.input_deck,
        control_node_ids=args.control_node,
        native_log_path=args.native_log,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"status": report["status"], "output": str(args.output)}, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
