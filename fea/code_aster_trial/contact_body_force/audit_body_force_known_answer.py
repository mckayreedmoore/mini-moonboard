#!/usr/bin/env python3
"""Audit the GROUP_MA-restricted FORC_NODA known-answer extraction."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHECKS = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27"
BASE = CHECKS / "contact-body-restricted-forc-noda-known-answer-attempt01"
SAME_PHYSICS = CHECKS / "contact-surface-forc-noda-known-answer-attempt01"
ORIGINAL = CHECKS / "contact-3d-flat-attempt02"
LIMIT_N = 0.1
EXPECTED = (0.0, 0.0, 3000.0)
CENTER = (50.0, 50.0, 0.02)
FIELDS = ("DX", "DY", "DZ", "LAGS_C", "RN", "RNX", "RNY", "RNZ", "CONT", "JEU",
          "SIXX", "SIYY", "SIZZ", "SIXY", "SIXZ", "SIYZ")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(path: Path) -> list[dict[str, str]]:
    lines = [line for line in path.read_text().splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise ValueError(f"empty table: {path}")
    return list(csv.DictReader(lines, delimiter=";"))


def rows_at(path: Path, instant: float = 1.0) -> list[dict[str, str]]:
    selected = [row for row in table(path) if abs(float(row["INST"]) - instant) <= 1.0e-8]
    if not selected:
        raise ValueError(f"no rows at INST={instant:g} in {path.name}")
    return selected


def vector(rows: list[dict[str, str]]) -> tuple[float, float, float]:
    return tuple(math.fsum(float(row[key]) for row in rows) for key in ("DX", "DY", "DZ"))


def moment(rows: list[dict[str, str]]) -> tuple[float, float, float]:
    accum = [[], [], []]
    for row in rows:
        x = float(row["COOR_X"]) - CENTER[0]
        y = float(row["COOR_Y"]) - CENTER[1]
        z = float(row["COOR_Z"]) - CENTER[2]
        fx, fy, fz = (float(row[key]) for key in ("DX", "DY", "DZ"))
        accum[0].append(y * fz - z * fy)
        accum[1].append(z * fx - x * fz)
        accum[2].append(x * fy - y * fx)
    return tuple(math.fsum(values) for values in accum)


def max_delta(a_path: Path, b_path: Path) -> dict:
    a, b = table(a_path), table(b_path)
    key = lambda row: (row["NOEUD"].strip(), float(row["INST"]))
    ma, mb = {key(row): row for row in a}, {key(row): row for row in b}
    if ma.keys() != mb.keys():
        raise ValueError(f"table coverage differs: {a_path.name} vs {b_path.name}")
    by_field = {}
    for field in FIELDS:
        if field not in ma[next(iter(ma))] or field not in mb[next(iter(mb))]:
            continue
        by_field[field] = max(abs(float(ma[k][field]) - float(mb[k][field])) for k in ma)
    return {"rows": len(ma), "maximum_absolute_delta_by_field": by_field,
            "maximum_absolute_delta": max(by_field.values(), default=0.0)}


def main() -> None:
    attempt = BASE
    freeze = json.loads((attempt / "input-freeze.json").read_text())
    readiness = json.loads((attempt / "readiness.json").read_text())
    execution = json.loads((attempt / "execution.json").read_text())
    if execution.get("returncode") != 0 or execution.get("timed_out") is not False:
        raise ValueError("native process did not complete successfully")
    if execution.get("changed_frozen_inputs"):
        raise ValueError("native run changed frozen inputs")
    for name, expected in freeze["input_sha256"].items():
        if digest(attempt / name) != expected:
            raise ValueError(f"input freeze mismatch: {name}")
    if readiness.get("mesh_byte_identical") is not True:
        raise ValueError("readiness does not establish an unchanged mesh")
    if readiness.get("physical_solution_block_byte_identical") is not True:
        raise ValueError("readiness does not establish unchanged physical solve block")
    if digest(attempt / "contact_coupon.mail") != digest(ORIGINAL / "contact_coupon.mail"):
        raise ValueError("coupon mesh differs from the original analytic input")

    body_rows = rows_at(attempt / "slave_body_internal_force.csv")
    surface_rows = rows_at(SAME_PHYSICS / "slave_surface_internal_force.csv")
    if len(body_rows) != 9:
        raise ValueError(f"expected 9 SLNOD values, got {len(body_rows)}")
    body = vector(body_rows)
    surface = vector(surface_rows)
    cut = vector(rows_at(attempt / "slave_cut_force.csv"))
    contact_rows = rows_at(attempt / "contact.csv")
    rn = tuple(math.fsum(float(row[key]) for row in contact_rows) for key in ("RNX", "RNY", "RNZ"))
    first_moment = moment(body_rows)
    errors = {
        "body_restricted_to_analytic_n": math.dist(body, EXPECTED),
        "body_restricted_to_full_surface_n": math.dist(body, surface),
        "body_restricted_plus_slave_cut_n": math.dist(tuple(body[i] + cut[i] for i in range(3)), (0.0, 0.0, 0.0)),
        "body_restricted_plus_rn_contact_action_n": math.dist(tuple(body[i] + rn[i] for i in range(3)), (0.0, 0.0, 0.0)),
        "first_moment_about_patch_center_n_mm": math.dist(first_moment, (0.0, 0.0, 0.0)),
    }
    unchanged = {}
    for name in ("contact.csv", "lagrange.csv", "stress.csv", "slave_cut_force.csv", "master_cut_force.csv",
                 "slave_cut_reaction.csv", "master_cut_reaction.csv"):
        unchanged[name] = max_delta(SAME_PHYSICS / name, attempt / name)

    result = {
        "scope": "Flat fully active PENTA15/TRIA6 analytic coupon; S_SOLID-only stress-derived force summed at the slave contact nodes.",
        "method": "CALC_CHAMP(FORCE='FORC_NODA', GROUP_MA='S_SOLID') into a separate result concept, then POST_RELEVE_T over SLNOD.",
        "analysis_kind": "Parent post-run audit; no solver invocation.",
        "native_execution": execution,
        "provenance": {
            "baseline_attempt": str(ORIGINAL.relative_to(ROOT)),
            "surface_known_answer_attempt": str(SAME_PHYSICS.relative_to(ROOT)),
            "frozen_attempt_inputs_verified": True,
            "physical_analysis_block_unchanged": True,
            "mesh_byte_identical_to_original": True,
            "runtime_image": freeze["image"],
        },
        "analytic_reference": {
            "pressure_mpa": -0.3,
            "area_mm2": 10000.0,
            "expected_slave_body_internal_force_n": list(EXPECTED),
            "expected_slave_contact_action_n": [0.0, 0.0, -3000.0],
            "force_limit_n": LIMIT_N,
            "moment_center_mm": list(CENTER),
            "moment_limit_n_mm": LIMIT_N,
        },
        "observed": {
            "instant": 1.0,
            "interface_node_count": len(body_rows),
            "body_restricted_force_n": list(body),
            "full_domain_interface_force_n": list(surface),
            "same_body_cut_forc_noda_n": list(cut),
            "summed_slave_rn_contact_action_n": list(rn),
            "first_moment_about_patch_center_n_mm": list(first_moment),
            "errors": errors,
        },
        "same_physics_field_comparisons": unchanged,
        "limitations": [
            "The analytic coupon uses PENTA15 volumes; it does not validate TETRA10 group assembly.",
            "This verifies a force resultant and first moment, not local pressure distribution.",
            "DX/DY are constrained at every coupon node, so pointwise tangential nodal forces are not contact traction.",
            "No wood response, joint resistance, or candidate acceptance is inferred.",
        ],
        "status": "PASS" if all(value <= LIMIT_N for value in errors.values()) and all(
            item["maximum_absolute_delta"] == 0.0 for item in unchanged.values()) else "FAIL",
        "mechanical_acceptance": "NOT_INFERRED",
    }
    output = attempt / "parent-audit.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
