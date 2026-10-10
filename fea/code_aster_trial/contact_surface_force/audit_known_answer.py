#!/usr/bin/env python3
"""Audit contact-face FORC_NODA on the frozen flat analytic coupon."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/contact-3d-flat-attempt02"
LIMIT_N = 0.1
EXPECTED = (0.0, 0.0, 3000.0)
CENTER = (50.0, 50.0, 0.02)
NUMERIC_COMPONENTS = ("DX", "DY", "DZ", "LAGS_C", "RN", "RNX", "RNY", "RNZ",
                      "CONT", "JEU", "SIXX", "SIYY", "SIZZ", "SIXY", "SIXZ", "SIYZ")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_table(path: Path) -> list[dict[str, str]]:
    lines = [line for line in path.read_text().splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise ValueError(f"empty table: {path}")
    return list(csv.DictReader(lines, delimiter=";"))


def final_rows(path: Path, instant: float = 1.0) -> list[dict[str, str]]:
    rows = [row for row in read_table(path)
            if abs(float(row["INST"]) - instant) <= 1.0e-8]
    if not rows:
        raise ValueError(f"no rows in {path.name} at INST={instant:g}")
    return rows


def vector(rows: list[dict[str, str]]) -> tuple[float, float, float]:
    return tuple(math.fsum(float(row[cmp]) for row in rows) for cmp in ("DX", "DY", "DZ"))


def moment(rows: list[dict[str, str]], center: tuple[float, float, float]) -> tuple[float, float, float]:
    mx, my, mz = [], [], []
    for row in rows:
        x = float(row["COOR_X"]) - center[0]
        y = float(row["COOR_Y"]) - center[1]
        z = float(row["COOR_Z"]) - center[2]
        fx, fy, fz = (float(row[cmp]) for cmp in ("DX", "DY", "DZ"))
        mx.append(y * fz - z * fy)
        my.append(z * fx - x * fz)
        mz.append(x * fy - y * fx)
    return tuple(math.fsum(values) for values in (mx, my, mz))


def max_row_delta(before: Path, after: Path) -> dict:
    a, b = read_table(before), read_table(after)
    key = lambda row: (row["NOEUD"].strip(), float(row["INST"]))
    ma = {key(row): row for row in a}
    mb = {key(row): row for row in b}
    if ma.keys() != mb.keys():
        raise ValueError(f"table coverage changed between {before.name} and {after.name}")
    fields = set(ma[next(iter(ma))]) & set(mb[next(iter(mb))])
    maximum = 0.0
    by_field = {}
    for field in fields:
        if field not in NUMERIC_COMPONENTS:
            continue
        delta = max(abs(float(ma[row_key][field]) - float(mb[row_key][field]))
                    for row_key in ma)
        by_field[field] = delta
        maximum = max(maximum, delta)
    return {"rows": len(ma), "maximum_absolute_delta_by_field": by_field,
            "maximum_absolute_delta": maximum}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("attempt", type=Path, nargs="?", default=ROOT /
        "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/contact-surface-forc-noda-known-answer-attempt01")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    attempt = args.attempt.resolve()

    freeze = json.loads((attempt / "input-freeze.json").read_text())
    readiness = json.loads((attempt / "readiness.json").read_text())
    execution = json.loads((attempt / "execution.json").read_text())
    if execution.get("returncode") != 0 or execution.get("timed_out") is not False:
        raise ValueError("native run did not complete successfully")
    if execution.get("changed_frozen_inputs"):
        raise ValueError("native run changed frozen input files")
    if freeze.get("image") != readiness.get("baseline_image"):
        raise ValueError("runtime image differs from the readiness freeze")
    for name, expected in freeze["input_sha256"].items():
        if digest(attempt / name) != expected:
            raise ValueError(f"frozen run input changed: {name}")

    face_rows = final_rows(attempt / "slave_surface_internal_force.csv")
    if len(face_rows) != 9:
        raise ValueError(f"expected 9 unique slave face nodes, found {len(face_rows)}")
    surface_force = vector(face_rows)
    surface_moment = moment(face_rows, CENTER)
    scut_force = vector(final_rows(attempt / "slave_cut_force.csv"))
    rn_rows = final_rows(attempt / "contact.csv")
    rn = tuple(math.fsum(float(row[cmp]) for row in rn_rows) for cmp in ("RNX", "RNY", "RNZ"))

    error_analytic = math.dist(surface_force, EXPECTED)
    error_cut_pair = math.dist(tuple(surface_force[i] + scut_force[i] for i in range(3)), (0.0, 0.0, 0.0))
    error_contact_pair = math.dist(tuple(surface_force[i] + rn[i] for i in range(3)), (0.0, 0.0, 0.0))
    moment_norm = math.dist(surface_moment, (0.0, 0.0, 0.0))

    repeated_output = {}
    for name in ("contact.csv", "lagrange.csv", "stress.csv", "slave_cut_force.csv",
                 "master_cut_force.csv", "slave_cut_reaction.csv", "master_cut_reaction.csv"):
        repeated_output[name] = max_row_delta(BASE / name, attempt / name)

    result = {
        "scope": "Flat, fully active, conforming 3-D coupon; contact-face FORC_NODA resultant known-answer only.",
        "analysis_kind": "Parent post-run audit; no solver invocation.",
        "mechanical_acceptance": "NOT_INFERRED",
        "native_execution": execution,
        "provenance": {
            "baseline_attempt": str(BASE.relative_to(ROOT)),
            "attempt_input_freeze_sha256": digest(attempt / "input-freeze.json"),
            "baseline_input_freeze_sha256": readiness["baseline_attempt_input_freeze_sha256"],
            "attempt_input_hashes_verified": True,
            "physical_analysis_block_unchanged": readiness["physical_analysis_block_exactly_unchanged"],
            "mesh_hash_unchanged": readiness["mesh_exactly_unchanged"],
            "same_runtime_image": freeze["image"],
        },
        "method": "Sum the stress-derived internal nodal forces on the nine free slave contact-face nodes. Compare with the analytic plane-strain pressure resultant, opposite slave RN action, opposite same-body SCUT FORC_NODA cut resultant, and the analytic zero moment about the contact patch center.",
        "analytic_reference": {
            "pressure_mpa": -0.3,
            "reference_area_mm2": 10000.0,
            "surface_internal_force_n": list(EXPECTED),
            "contact_force_on_slave_n": [0.0, 0.0, -3000.0],
            "moment_center_mm": list(CENTER),
            "surface_force_limit_n": LIMIT_N,
            "surface_moment_limit_n_mm": LIMIT_N,
        },
        "observed": {
            "instant": 1.0,
            "slave_contact_node_count": len(face_rows),
            "surface_internal_force_n": list(surface_force),
            "scut_forc_noda_n": list(scut_force),
            "summed_rn_contact_action_n": list(rn),
            "surface_internal_moment_about_patch_center_n_mm": list(surface_moment),
            "error_to_analytic_surface_force_n": error_analytic,
            "error_to_opposite_scut_force_n": error_cut_pair,
            "error_to_opposite_rn_n": error_contact_pair,
            "moment_norm_n_mm": moment_norm,
        },
        "comparisons_to_original_same_physics_attempt": repeated_output,
        "limitations": [
            "This validates a resultant and first moment for one flat, fully active interface only.",
            "DX/DY are constrained on all nodes in this coupon; per-node tangential FORC_NODA values are not a contact traction distribution.",
            "The curved crop has free interface nodes but still needs its own paired body-group and interface-resultant validation.",
            "No local pressure accuracy, wood response, joint resistance, or candidate acceptance is inferred.",
        ],
        "status": "PASS" if all(value <= LIMIT_N for value in
            (error_analytic, error_cut_pair, error_contact_pair, moment_norm)) else "FAIL",
    }
    output = args.output.resolve() if args.output else attempt / "parent-audit.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
