#!/usr/bin/env python3
"""Check a constrained CalculiX MATRIXSTORAGE export without running CCX.

Usage after a separately authorized native run:
    python3 constrained_matrix_export_oracle.py --check-results job.sti job.dof

The checker reconstructs the active-coordinate map and checks affine energy,
spring-action, and load-work identities. It does not build element matrices.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import types
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
PACKET = (
    HERE.parent.parent
    / "elastic-matrix-export-method-2026-09-30"
    / "elastic_matrix_packet.py"
)
PACKET_SHA256 = "8ab37ac0e1b1c1737fd478f1d2ee6b423930660c3a91cef2c75127d817b30b4c"
SPC = (1, 1)
MPC_SLAVE = (9, 1)
MPC_MASTERS = ((1, 1, 0.5), (2, 1, 0.5))
SPRING_ENDS = ((9, 1), (2, 1))
SPRING_K_N_PER_MM = 100.0
SPRING_ENERGY_RTOL = 5.0e-7
ENERGY_ATOL_REL = 2.0e-8
REFERENCE_SPC_OFFSET_MM = 0.2
PROBE_U2X_MM = 0.6
PROBE_LOAD_NODE9X_N = 8.0


def fail(message: str) -> None:
    raise ValueError(message)


def load_material_packet():
    try:
        actual = hashlib.sha256(PACKET.read_bytes()).hexdigest()
    except OSError as error:
        raise ValueError(f"cannot read pinned material oracle {PACKET}: {error}") from error
    if actual != PACKET_SHA256:
        fail(f"rotated material oracle hash mismatch: {actual}")
    module = types.ModuleType("pinned_elastic_matrix_packet")
    module.__file__ = str(PACKET)
    try:
        exec(compile(PACKET.read_text(), str(PACKET), "exec"), module.__dict__)
    except (OSError, SyntaxError) as error:
        raise ValueError(f"cannot load pinned rotated material oracle: {error}") from error
    return module


MATERIAL_PACKET = load_material_packet()
COORDS = {node: np.asarray(xyz, dtype=np.float64)
          for node, xyz in MATERIAL_PACKET.NODE_COORDS}
VOIGT_PAIRS = MATERIAL_PACKET.VOIGT_PAIRS
PHYSICAL_DOF_COUNT = len(COORDS) * 3
EXPECTED_LABELS = {
    (node, direction)
    for node in COORDS
    for direction in (1, 2, 3)
} - {SPC, MPC_SLAVE}
REL_TOL = MATERIAL_PACKET.ENERGY_RTOL


def physical_row(label: tuple[int, int]) -> int:
    node, direction = label
    if node not in COORDS or direction not in (1, 2, 3):
        fail(f"physical coordinate outside coupon: {label}")
    return 3 * (node - 1) + direction - 1


def parse_dof_text(text: str) -> list[tuple[int, int]]:
    labels: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for line_number, raw in enumerate(text.splitlines(), 1):
        token = raw.strip()
        if not token:
            continue
        match = re.fullmatch(r"([0-9]+)\.([0-9]+)", token)
        if match is None:
            fail(f".dof line {line_number}: expected node.direction")
        label = tuple(map(int, match.groups()))
        if label[0] not in COORDS or label[1] not in (1, 2, 3):
            fail(f".dof line {line_number}: coordinate outside coupon: {token}")
        if label in seen:
            fail(f".dof line {line_number}: duplicate coordinate {token}")
        seen.add(label)
        labels.append(label)
    if set(labels) != EXPECTED_LABELS or len(labels) != 58:
        all_physical = {
            (node, direction)
            for node in COORDS
            for direction in (1, 2, 3)
        }
        omitted = sorted(all_physical - set(labels))
        fail(
            ".dof must map exactly 58 active coordinates; only SPC (1,1) and "
            f"MPC slave (9,1) are omitted (observed omitted {omitted})"
        )
    return labels


def read_dof(path: Path) -> list[tuple[int, int]]:
    try:
        return parse_dof_text(path.read_text())
    except OSError as error:
        raise ValueError(f"cannot read {path}: {error}") from error


def parse_sti_text(text: str, dimension: int) -> tuple[np.ndarray, int]:
    pairs: dict[tuple[int, int], float] = {}
    diagonal: set[int] = set()
    triangle: str | None = None
    for line_number, raw in enumerate(text.splitlines(), 1):
        fields = raw.split()
        if not fields:
            continue
        if len(fields) != 3:
            fail(f".sti line {line_number}: expected row column value")
        try:
            row, column = int(fields[0]), int(fields[1])
            value = float(fields[2].replace("D", "E").replace("d", "e"))
        except ValueError as error:
            raise ValueError(f".sti line {line_number}: invalid numeric triplet") from error
        if not (1 <= row <= dimension and 1 <= column <= dimension):
            fail(f".sti line {line_number}: index outside .dof map")
        if not math.isfinite(value):
            fail(f".sti line {line_number}: non-finite matrix value")
        pair = (min(row, column), max(row, column))
        if pair in pairs:
            fail(f".sti line {line_number}: duplicate or mirrored pair {pair}")
        if row != column:
            orientation = "upper" if row < column else "lower"
            if triangle is not None and triangle != orientation:
                fail(f".sti line {line_number}: entries span both triangles")
            triangle = orientation
        pairs[pair] = value
        if row == column:
            diagonal.add(row)

    if diagonal != set(range(1, dimension + 1)):
        fail(".sti must store one diagonal for each equation in .dof")
    matrix = np.zeros((dimension, dimension), dtype=np.float64)
    for (row, column), value in pairs.items():
        matrix[row - 1, column - 1] = value
        matrix[column - 1, row - 1] = value
    return matrix, len(pairs)


def read_sti(path: Path, dimension: int) -> tuple[np.ndarray, int]:
    try:
        return parse_sti_text(path.read_text(), dimension)
    except OSError as error:
        raise ValueError(f"cannot read {path}: {error}") from error


def build_expansion(labels: list[tuple[int, int]]) -> np.ndarray:
    if set(labels) != EXPECTED_LABELS or len(labels) != len(EXPECTED_LABELS):
        fail("cannot expand an unexpected active equation map")
    columns = {label: column for column, label in enumerate(labels)}
    expansion = np.zeros((PHYSICAL_DOF_COUNT, len(labels)), dtype=np.float64)
    for label, column in columns.items():
        expansion[physical_row(label), column] = 1.0

    slave = physical_row(MPC_SLAVE)
    expansion[slave, :] = 0.0
    for node, direction, weight in MPC_MASTERS:
        master = (node, direction)
        if master == SPC:
            continue
        if master not in columns:
            fail(f"MPC master unexpectedly absent from active map: {master}")
        expansion[slave, columns[master]] += weight
    return expansion


def offset_vector(
    spc_value_mm: float = 0.0,
    mpc_affine_offset_mm: float = 0.0,
) -> np.ndarray:
    """Build separate prescribed/reference offsets, never read from .dof/.sti."""
    if not (math.isfinite(spc_value_mm) and math.isfinite(mpc_affine_offset_mm)):
        fail("reference offsets must be finite")
    offset = np.zeros(PHYSICAL_DOF_COUNT, dtype=np.float64)
    offset[physical_row(SPC)] = spc_value_mm
    offset[physical_row(MPC_SLAVE)] = (
        0.5 * offset[physical_row((1, 1))]
        + 0.5 * offset[physical_row((2, 1))]
        + mpc_affine_offset_mm
    )
    return offset


def affine_displacements() -> np.ndarray:
    """Return origin-based physical displacements for unit engineering strains."""
    result = np.zeros((PHYSICAL_DOF_COUNT, 6), dtype=np.float64)
    for column, (i, j) in enumerate(VOIGT_PAIRS):
        strain = np.zeros((3, 3), dtype=np.float64)
        strain[i, j] = strain[j, i] = 1.0 if i == j else 0.5
        for node, xyz in COORDS.items():
            displacement = strain @ xyz
            for direction in (1, 2, 3):
                result[physical_row((node, direction)), column] = displacement[direction - 1]
    return result


def active_affines(labels: list[tuple[int, int]], expansion: np.ndarray):
    physical = affine_displacements()
    coordinates = np.vstack([physical[physical_row(label), :] for label in labels])
    reconstructed = expansion @ coordinates
    if not np.allclose(reconstructed, physical, rtol=0.0, atol=1.0e-12):
        fail("one or more affine strain fields violate the permanent SPC/MPC map")
    return coordinates


def spring_direction() -> np.ndarray:
    direction = np.zeros(PHYSICAL_DOF_COUNT, dtype=np.float64)
    direction[physical_row(SPRING_ENDS[1])] = 1.0
    direction[physical_row(SPRING_ENDS[0])] = -1.0
    return direction


def analytical_mapping_probe(labels: list[tuple[int, int]]) -> dict[str, Any]:
    expansion = build_expansion(labels)
    columns = {label: column for column, label in enumerate(labels)}
    q2x = columns[(2, 1)]
    direction = spring_direction()
    projected_spring_direction = expansion.T @ direction
    expected_direction = np.zeros(len(labels), dtype=np.float64)
    expected_direction[q2x] = 0.5
    if not np.allclose(projected_spring_direction, expected_direction, atol=1.0e-13):
        fail("SPRING2 endpoint direction did not project to one half of node 2 X")

    q = np.zeros(len(labels), dtype=np.float64)
    q[q2x] = 0.6
    offset = offset_vector(spc_value_mm=REFERENCE_SPC_OFFSET_MM)
    displacement = expansion @ q + offset
    extension = float(direction @ displacement)
    spring_energy = 0.5 * SPRING_K_N_PER_MM * extension**2
    spring_internal = SPRING_K_N_PER_MM * extension * direction
    projected_spring_force = expansion.T @ spring_internal
    expected_projected_force = np.zeros(len(labels), dtype=np.float64)
    expected_projected_force[q2x] = 10.0
    if not np.allclose(projected_spring_force, expected_projected_force, atol=1.0e-12):
        fail("expanded SPRING2 end forces do not give the expected projected action")

    physical_load = np.zeros(PHYSICAL_DOF_COUNT, dtype=np.float64)
    physical_load[physical_row((9, 1))] = PROBE_LOAD_NODE9X_N
    reduced_load = expansion.T @ physical_load
    expected_reduced_load = np.zeros(len(labels), dtype=np.float64)
    expected_reduced_load[q2x] = 0.5 * PROBE_LOAD_NODE9X_N
    if not np.allclose(reduced_load, expected_reduced_load, atol=1.0e-13):
        fail("load at the MPC slave did not map through B transpose")
    physical_work = float(physical_load @ displacement)
    reduced_work = float(reduced_load @ q + physical_load @ offset)
    if not math.isclose(physical_work, reduced_work, rel_tol=0.0, abs_tol=1.0e-13):
        fail("physical and reduced-coordinate load work differ")

    reduced_spring_tangent = SPRING_K_N_PER_MM * np.outer(
        projected_spring_direction, projected_spring_direction
    )
    return {
        "reference_spc_offset_mm_external_to_export": REFERENCE_SPC_OFFSET_MM,
        "active_node2_x_value_mm": float(q[q2x]),
        "expanded_node1_x_mm": float(displacement[physical_row((1, 1))]),
        "expanded_node2_x_mm": float(displacement[physical_row((2, 1))]),
        "expanded_node9_x_mm": float(displacement[physical_row((9, 1))]),
        "spring_extension_mm": extension,
        "spring_physical_end_force_magnitude_N": float(
            SPRING_K_N_PER_MM * extension
        ),
        "spring_energy_N_mm": spring_energy,
        "spring_projected_force_at_node2_x_N": float(projected_spring_force[q2x]),
        "spring_projected_tangent_at_node2_x_N_per_mm": float(
            reduced_spring_tangent[q2x, q2x]
        ),
        "load_at_mpc_slave_N": PROBE_LOAD_NODE9X_N,
        "projected_load_at_node2_x_N": float(reduced_load[q2x]),
        "physical_load_work_N_mm": physical_work,
        "reduced_load_work_plus_offset_N_mm": reduced_work,
        "reference_offset_captured_by_frequency_export": False,
        "load_vector_exported_by_matrixstorage": False,
    }


def check_export(sti_path: Path, dof_path: Path) -> dict[str, Any]:
    labels = read_dof(dof_path)
    stiffness, entry_count = read_sti(sti_path, len(labels))
    if not np.all(np.isfinite(stiffness)):
        fail("reconstructed stiffness matrix contains non-finite entries")
    if not np.allclose(stiffness, stiffness.T, rtol=0.0, atol=0.0):
        fail("reconstructed stiffness matrix is not symmetric")

    expansion = build_expansion(labels)
    coordinates = active_affines(labels, expansion)
    observed = coordinates.T @ stiffness @ coordinates
    expected = MATERIAL_PACKET.global_engineering_stiffness(angle_degrees=37.0)
    # The unit-side spring extension under unit epsilon_xx is 0.5 mm.
    expected[0, 0] += SPRING_K_N_PER_MM * 0.5**2
    difference = np.abs(observed - expected)
    scale = float(np.max(np.abs(expected)))
    allowed = SPRING_ENERGY_RTOL * np.abs(expected) + ENERGY_ATOL_REL * scale
    if not np.all(difference <= allowed):
        fail(
            "affine energy/cross-energy oracle mismatch; max absolute error "
            f"{float(np.max(difference)):.9g} N/mm"
        )

    probe = analytical_mapping_probe(labels)
    return {
        "status": "PASS_CONSTRAINED_MATRIX_EXPORT_ORACLE",
        "equation_count": len(labels),
        "expected_excluded_coordinates": ["1.1 SPC", "9.1 MPC dependent"],
        "stiffness_triplet_pairs": entry_count,
        "max_affine_cross_energy_error_N_per_mm": float(np.max(difference)),
        "observed_affine_cross_energy_N_per_mm": observed.tolist(),
        "expected_affine_cross_energy_N_per_mm": expected.tolist(),
        "analytical_mapping_probe": probe,
        "mass_matrix_checked": False,
        "mass_matrix_note": "The bounded oracle checks constrained stiffness mapping only; prior free-cube work covers mass export.",
        "native_execution_provenance_checked": False,
        "execution_provenance_note": "The parent runner verifies native executable and run provenance separately.",
        "frame_ready": False,
        "contact_or_joint_accepted": False,
    }


def self_test() -> dict[str, Any]:
    labels = sorted(EXPECTED_LABELS)
    expansion = build_expansion(labels)
    if expansion.shape != (60, 58):
        fail("constraint expansion has unexpected dimensions")
    if np.linalg.matrix_rank(expansion) != 58:
        fail("constraint expansion is not full column rank")
    coordinates = active_affines(labels, expansion)
    material = MATERIAL_PACKET.global_engineering_stiffness(angle_degrees=37.0)
    if material.shape != (6, 6) or not np.allclose(material, material.T, atol=1.0e-10):
        fail("pinned rotated material oracle returned an invalid cross-energy matrix")
    probe = analytical_mapping_probe(labels)
    expected = {
        "expanded_node1_x_mm": 0.2,
        "expanded_node2_x_mm": 0.6,
        "expanded_node9_x_mm": 0.4,
        "spring_extension_mm": 0.2,
        "spring_physical_end_force_magnitude_N": 20.0,
        "spring_energy_N_mm": 2.0,
        "spring_projected_force_at_node2_x_N": 10.0,
        "spring_projected_tangent_at_node2_x_N_per_mm": 25.0,
        "projected_load_at_node2_x_N": 4.0,
        "physical_load_work_N_mm": 3.2,
        "reduced_load_work_plus_offset_N_mm": 3.2,
    }
    for key, value in expected.items():
        if not math.isclose(float(probe[key]), value, rel_tol=0.0, abs_tol=1.0e-12):
            fail(f"analytical map self-test mismatch for {key}: {probe[key]}")
    return {
        "status": "PASS_ANALYTICAL_CONSTRAINED_MAPPING_SELF_TEST",
        "expansion_shape": list(expansion.shape),
        "expansion_rank": int(np.linalg.matrix_rank(expansion)),
        "compatible_affine_strain_fields": int(coordinates.shape[1]),
        "analytical_mapping_probe": probe,
        "native_execution_provenance_checked": False,
        "native_execution_note": "This self-test is algebra only; it does not invoke CalculiX or create an FE operator.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--check-results", nargs=2, metavar=("STI", "DOF"))
    args = parser.parse_args()
    try:
        result = (
            self_test()
            if args.self_test
            else check_export(Path(args.check_results[0]), Path(args.check_results[1]))
        )
    except (ValueError, OSError) as error:
        result = {
            "status": "REJECT_CONSTRAINED_MATRIX_EXPORT_ORACLE",
            "finding": str(error),
            "native_execution_provenance_checked": False,
            "execution_provenance_note": "The parent runner verifies native executable and run provenance separately.",
            "frame_ready": False,
            "contact_or_joint_accepted": False,
        }
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
