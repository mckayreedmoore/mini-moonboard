#!/usr/bin/env python3
"""Parse CalculiX MATRIXSTORAGE output and check the free C3D20 oracle.

This script does not invoke CalculiX, construct element stiffness, or solve a
contact/controller problem. Usage after a separately authorized native run:
    python3 matrix_export_oracle.py JOB_BASENAME
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np


COORDS = {
    1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0),
    3: (1.0, 1.0, 0.0), 4: (0.0, 1.0, 0.0),
    5: (0.0, 0.0, 1.0), 6: (1.0, 0.0, 1.0),
    7: (1.0, 1.0, 1.0), 8: (0.0, 1.0, 1.0),
    9: (0.5, 0.0, 0.0), 10: (1.0, 0.5, 0.0),
    11: (0.5, 1.0, 0.0), 12: (0.0, 0.5, 0.0),
    13: (0.5, 0.0, 1.0), 14: (1.0, 0.5, 1.0),
    15: (0.5, 1.0, 1.0), 16: (0.0, 0.5, 1.0),
    17: (0.0, 0.0, 0.5), 18: (1.0, 0.0, 0.5),
    19: (1.0, 1.0, 0.5), 20: (0.0, 1.0, 0.5),
}
NODES = 20
DOFS = 3
E = 1.0
NU = 0.25
DENSITY = 1.0
VOLUME = 1.0
GAMMA = 0.01
REL_TOL = 1.0e-8


def read_dof_map(path: Path) -> list[tuple[int, int]]:
    labels = []
    for line_number, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        match = re.fullmatch(r"(\d+)\.(\d+)", line)
        if not match:
            raise ValueError(f"{path}:{line_number}: expected node.direction")
        node, direction = map(int, match.groups())
        if node not in COORDS or direction not in (1, 2, 3):
            raise ValueError(f"{path}:{line_number}: label outside coupon")
        labels.append((node, direction))
    expected = {(node, direction) for node in COORDS for direction in (1, 2, 3)}
    if len(labels) != NODES * DOFS or set(labels) != expected:
        raise ValueError(".dof must map all 60 free C3D20 equations exactly once")
    return labels


def read_symmetric_triplets(path: Path, dimension: int) -> tuple[np.ndarray, int]:
    pairs: dict[tuple[int, int], float] = {}
    diagonal: set[int] = set()
    for line_number, raw in enumerate(path.read_text().splitlines(), 1):
        fields = raw.split()
        if not fields:
            continue
        if len(fields) != 3:
            raise ValueError(f"{path}:{line_number}: expected row column value")
        try:
            row, column = int(fields[0]), int(fields[1])
            value = float(fields[2])
        except ValueError as error:
            raise ValueError(f"{path}:{line_number}: invalid numeric triplet") from error
        if not (1 <= row <= dimension and 1 <= column <= dimension):
            raise ValueError(f"{path}:{line_number}: matrix index outside .dof map")
        if not math.isfinite(value):
            raise ValueError(f"{path}:{line_number}: non-finite matrix value")
        pair = (min(row, column), max(row, column))
        if pair in pairs:
            raise ValueError(f"{path}:{line_number}: duplicate symmetric pair {pair}")
        pairs[pair] = value
        if row == column:
            diagonal.add(row)

    required_diagonal = set(range(1, dimension + 1))
    if diagonal != required_diagonal:
        raise ValueError("matrix file must emit one diagonal entry for each .dof row")
    matrix = np.zeros((dimension, dimension), dtype=np.float64)
    for (row, column), value in pairs.items():
        matrix[row - 1, column - 1] = value
        matrix[column - 1, row - 1] = value
    return matrix, len(pairs)


def vector_from_labels(labels: list[tuple[int, int]], values: dict[tuple[int, int], float]) -> np.ndarray:
    return np.array([values.get(label, 0.0) for label in labels], dtype=np.float64)


def rigid_vectors(labels: list[tuple[int, int]]) -> list[np.ndarray]:
    axes = np.eye(3)
    modes = []
    for direction in range(3):
        modes.append(vector_from_labels(
            labels, {(node, direction + 1): 1.0 for node in COORDS}))
    for axis in axes:
        values = {}
        for node, xyz in COORDS.items():
            displacement = np.cross(axis, np.asarray(xyz, dtype=np.float64))
            for direction in range(3):
                values[(node, direction + 1)] = float(displacement[direction])
        modes.append(vector_from_labels(labels, values))
    return modes


def check(base: Path) -> dict[str, object]:
    labels = read_dof_map(base.with_suffix(".dof"))
    stiffness, stiffness_pairs = read_symmetric_triplets(
        base.with_suffix(".sti"), len(labels))
    mass, mass_pairs = read_symmetric_triplets(base.with_suffix(".mas"), len(labels))

    scale = float(np.linalg.norm(stiffness, ord=np.inf))
    if scale <= 0.0:
        raise ValueError("stiffness operator is empty")
    rigid_residuals = [
        float(np.linalg.norm(stiffness @ mode, ord=np.inf)
              / (scale * np.linalg.norm(mode, ord=np.inf)))
        for mode in rigid_vectors(labels)
    ]
    eigenvalues = np.linalg.eigvalsh(stiffness)
    eig_tol = float(np.max(np.abs(eigenvalues)) * REL_TOL)
    rigid_count = int(np.count_nonzero(np.abs(eigenvalues) <= eig_tol))
    negative_count = int(np.count_nonzero(eigenvalues < -eig_tol))

    shear = vector_from_labels(labels, {
        (node, 1): GAMMA * xyz[1] for node, xyz in COORDS.items()})
    observed_energy = float(0.5 * shear @ stiffness @ shear)
    shear_modulus = E / (2.0 * (1.0 + NU))
    expected_energy = 0.5 * shear_modulus * GAMMA**2 * VOLUME

    x_translation = vector_from_labels(labels, {
        (node, 1): 1.0 for node in COORDS})
    observed_translational_mass = float(x_translation @ mass @ x_translation)
    expected_translational_mass = DENSITY * VOLUME

    passed = (
        max(rigid_residuals) <= REL_TOL
        and rigid_count == 6
        and negative_count == 0
        and abs(observed_energy - expected_energy)
            <= REL_TOL * max(abs(expected_energy), 1.0e-30)
        and abs(observed_translational_mass - expected_translational_mass)
            <= REL_TOL * max(abs(expected_translational_mass), 1.0e-30)
    )
    return {
        "status": "PASS_FREE_C3D20_MATRIX_EXPORT_ORACLE" if passed
                  else "REJECT_FREE_C3D20_MATRIX_EXPORT_ORACLE",
        "dof_count": len(labels),
        "stiffness_triplet_pairs": stiffness_pairs,
        "mass_triplet_pairs": mass_pairs,
        "rigid_body_mode_count": rigid_count,
        "negative_eigenvalue_count_below_tolerance": negative_count,
        "max_rigid_mode_residual_relative": max(rigid_residuals),
        "stiffness_eigenvalue_tolerance": eig_tol,
        "observed_shear_energy_N_mm": observed_energy,
        "expected_shear_energy_N_mm": expected_energy,
        "observed_unit_translation_mass": observed_translational_mass,
        "expected_unit_translation_mass": expected_translational_mass,
        "native_execution_provenance_checked": False,
        "execution_provenance_note": (
            "The parent runner verifies native executable and run provenance separately."
        ),
        "frame_ready": False,
        "contact_or_joint_accepted": False,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: matrix_export_oracle.py JOB_BASENAME")
    result = check(Path(sys.argv[1]))
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result["status"].startswith("PASS") else 1)
