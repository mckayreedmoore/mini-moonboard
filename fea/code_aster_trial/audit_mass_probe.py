"""Audit the frozen curved TETRA10 native mass matrix against its reference."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(attempt, readiness):
    freeze = json.loads((attempt / "input-freeze.json").read_text())
    assert all(sha(attempt / name) == digest
               for name, digest in freeze["input_sha256"].items())
    spec = importlib.util.spec_from_file_location(
        "frozen_mass_reference", attempt / "aster_tetra10_mass.py")
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    data_path = attempt / "tetra10_curved_mass.json"
    data = json.loads(data_path.read_text())
    coords, active = [], False
    for line in (attempt / "tetra10_curved.mass.mail").read_text().splitlines():
        if line == "COOR_3D":
            active = True
            continue
        if active and line == "FINSF":
            break
        if active:
            coords.append([float(value) for value in line.split()[1:]])
    coords = np.asarray(coords)
    assert coords.shape == (10, 3)
    assert np.array_equal(coords, data["node_coords_mm"])
    matrix, description = np.asarray(data["matrix"]), data["dof_map"]
    assert matrix.shape == (30, 30) and np.isfinite(matrix).all()
    assert len(description) == 30
    assert [d["index"] for d in description] == list(range(30))
    assert {(d["node_index"], d["component"]) for d in description} == {
        (node, component) for node in range(10) for component in ("DX", "DY", "DZ")}
    scalar = reference.tetra10_mass_matrix(coords, 7.85e-9)
    alternative = reference.tetra10_mass_matrix(coords, 7.85e-9, "fpg4")
    expected = np.array([
        [scalar[x["node_index"], y["node_index"]]
         if x["component"] == y["component"] else 0.0 for y in description]
        for x in description])
    scale = float(abs(expected).max())
    error = float(abs(matrix - expected).max())
    separation = float(np.linalg.norm(scalar - alternative) / np.linalg.norm(scalar))
    symmetry = float(abs(matrix - matrix.T).max() / scale)
    bounds = json.loads(readiness.read_text())["acceptance"]
    limit = (bounds["absolute_entry_error_floor_tonne"]
             + bounds["normalized_max_entry_error"] * scale)
    assert error <= limit
    assert symmetry <= bounds["matrix_symmetry_normalized_max_error"]
    assert separation > bounds["fpg4_frobenius_relative_separation_min"]
    execution = json.loads((attempt / "execution.json").read_text())
    assert execution["returncode"] == 0 and not execution["timed_out"]
    assert not execution["changed_frozen_inputs"]
    assert "DIAGNOSTIC JOB : OK" in (attempt / "native.stdout").read_text()
    return {
        "status": "PASS_CURVED_TETRA10_MASS_MATRIX",
        "maximum_absolute_entry_error_tonne": error,
        "maximum_expected_entry_tonne": scale,
        "normalized_maximum_error": error / scale,
        "entry_error_limit_tonne": limit,
        "normalized_symmetry_error": symmetry,
        "fpg4_frobenius_relative_separation": separation,
        "matrix_dimensions": [30, 30],
        "all_900_entries_checked": True,
        "output_sha256": sha(data_path),
        "readiness_sha256": sha(readiness),
        "checker_sha256": sha(Path(__file__)),
        "scope": "Observed 17.4 ordinary 3D TETRA10 mass agrees with FPG15 on one curved tetra; no dynamics or joint acceptance.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt", type=Path)
    parser.add_argument("readiness", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.attempt, args.readiness)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
