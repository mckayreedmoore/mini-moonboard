#!/usr/bin/env python3
"""Check a two-contact normal active set coupled to conditional ideal stick."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "fixture.json"
PINNED_SOURCES = {
    "AGENTS.md": (Path("AGENTS.md"), "672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536"),
    "option-ab-method-selection-2026-09-29.md": (
        Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/option-ab-method-selection-2026-09-29.md"),
        "d73dc9b2583c88b64fab4a8e61b1910dfbdb2881cc6dde629b30911a5425c76a",
    ),
    "attempt02-normal-fixture.json": (
        Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-two-cell-rotation-fixture-attempt02/fixture.json"),
        "80b5e26335d22a2d9f11f5a7b1c9ffe8bbcf2774088ae50c2c5191b2088128ad",
    ),
    "attempt01-coupled-single-cell-fixture.json": (
        Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-stick-coupled-load-fixture-attempt01/fixture.json"),
        "da7961d07502df2fbb0d17de26db0490fc0c868f152dc108b9eae36b01b41a27",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve_linear(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Gauss-Jordan solve for the small known-answer systems in this fixture."""
    n = len(rhs)
    a = [list(map(float, row)) + [float(rhs[i])] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-14:
            raise ValueError("fixture linear system is singular")
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        a[col] = [value / scale for value in a[col]]
        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            a[row] = [a[row][j] - factor * a[col][j] for j in range(n + 1)]
    return [a[i][n] for i in range(n)]


def vec_add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def normal_branch(model: dict[str, Any], stage: dict[str, Any], active_indices: list[int]) -> dict[str, Any]:
    contacts = model["contacts"]
    kn = float(model["penalty_stiffness_n_per_mm"])
    k = model["carrier_stiffness"]
    p = float(stage["normal_load"]["downward_P_n"])
    my = float(stage["normal_load"]["moment_My_nmm"])
    b = [-p, my]
    matrix = [[float(k[i][j]) for j in range(2)] for i in range(2)]
    rhs = b[:]
    for index in active_indices:
        contact = contacts[index]
        x = float(contact["x_mm"])
        row = [1.0, -x]
        gap0 = float(contact["initial_gap_mm"])
        for i in range(2):
            rhs[i] -= kn * gap0 * row[i]
            for j in range(2):
                matrix[i][j] += kn * row[i] * row[j]
    q = solve_linear(matrix, rhs)
    gaps = [
        float(contact["initial_gap_mm"]) + q[0] - q[1] * float(contact["x_mm"])
        for contact in contacts
    ]
    forces = [(-kn * gaps[i] if i in active_indices else 0.0) for i in range(len(contacts))]
    residual = [float(k[i][0]) * q[0] + float(k[i][1]) * q[1] - b[i] for i in range(2)]
    for i, contact in enumerate(contacts):
        if i in active_indices:
            x = float(contact["x_mm"])
            residual[0] -= forces[i]
            residual[1] += x * forces[i]
    return {"q": q, "gaps": gaps, "forces": forces, "residual": residual}


def admissible_normal_masks(model: dict[str, Any], stage: dict[str, Any], tol: float) -> list[dict[str, Any]]:
    contacts = model["contacts"]
    results = []
    for mask in range(1 << len(contacts)):
        active = [i for i in range(len(contacts)) if mask & (1 << i)]
        branch = normal_branch(model, stage, active)
        ok = True
        for i in range(len(contacts)):
            if i in active:
                ok = ok and branch["gaps"][i] < -tol and branch["forces"][i] > tol
            else:
                ok = ok and branch["gaps"][i] >= -tol and abs(branch["forces"][i]) <= tol
        ok = ok and max(abs(value) for value in branch["residual"]) <= tol
        if ok:
            branch["active_indices"] = active
            results.append(branch)
    return results


def solve_tangent(
    tangent_model: dict[str, Any],
    contacts: list[dict[str, Any]],
    stage: dict[str, Any],
    active: list[int],
    references: list[float | None],
) -> dict[str, Any]:
    k = [[float(value) for value in row] for row in tangent_model["carrier_stiffness"]]
    b = [
        float(stage["tangent_load"]["force_Hy_n"]),
        float(stage["tangent_load"]["moment_Mz_nmm"]),
    ]
    constraints = [[1.0, float(contacts[index]["x_mm"])] for index in active]
    if any(references[index] is None for index in active):
        raise ValueError("an active tangential contact has no episode reference")
    rhs_constraint = [float(references[index]) for index in active]
    count = len(active)
    size = 2 + count
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    rhs = [0.0 for _ in range(size)]
    for i in range(2):
        rhs[i] = b[i]
        for j in range(2):
            matrix[i][j] = k[i][j]
    for row, constraint in enumerate(constraints):
        rhs[2 + row] = rhs_constraint[row]
        for dof in range(2):
            matrix[dof][2 + row] = -constraint[dof]
            matrix[2 + row][dof] = constraint[dof]
    solution = solve_linear(matrix, rhs)
    q = solution[:2]
    forces = [0.0 for _ in contacts]
    for index, force in zip(active, solution[2:], strict=True):
        forces[index] = force
    equilibrium = [k[i][0] * q[0] + k[i][1] * q[1] - b[i] for i in range(2)]
    for i, force in enumerate(forces):
        x = float(contacts[i]["x_mm"])
        equilibrium[0] -= force
        equilibrium[1] -= x * force
    slip = [q[0] + q[1] * float(contact["x_mm"]) - float(references[i]) for i, contact in enumerate(contacts) if i in active]
    return {"q": q, "forces": forces, "equilibrium_residual": equilibrium, "active_slip": slip}


def run_fixture(fixture: dict[str, Any], source_hashes: dict[str, str]) -> dict[str, Any]:
    model = fixture["normal"]
    tang = fixture["tangent"]
    tol = float(fixture["tolerance"])
    contacts = model["contacts"]
    active_previous: set[int] = set()
    tangent_q_previous = [0.0, 0.0]
    references: list[float | None] = [None for _ in contacts]
    stage_results = []
    maximum_normal_residual = 0.0
    maximum_tangent_residual = 0.0
    maximum_stick_slip = 0.0

    for stage in fixture["stages"]:
        branches = admissible_normal_masks(model, stage, tol)
        if len(branches) != 1:
            raise ValueError(f"{stage['id']}: expected exactly one admissible normal mask; found {len(branches)}")
        normal = branches[0]
        active_now = set(normal["active_indices"])
        # Reset only when a normal-open contact becomes positively bearing.
        for index in active_now - active_previous:
            x = float(contacts[index]["x_mm"])
            references[index] = tangent_q_previous[0] + tangent_q_previous[1] * x

        tangent = solve_tangent(tang, contacts, stage, sorted(active_now), references)
        for index in range(len(contacts)):
            if index not in active_now and abs(tangent["forces"][index]) > tol:
                raise ValueError(f"{stage['id']}: open contact carries tangential force")
        normal_residual = max(abs(value) for value in normal["residual"])
        tangent_residual = max(abs(value) for value in tangent["equilibrium_residual"])
        slip_residual = max((abs(value) for value in tangent["active_slip"]), default=0.0)
        maximum_normal_residual = max(maximum_normal_residual, normal_residual)
        maximum_tangent_residual = max(maximum_tangent_residual, tangent_residual)
        maximum_stick_slip = max(maximum_stick_slip, slip_residual)
        if max(normal_residual, tangent_residual, slip_residual) > tol:
            raise ValueError(f"{stage['id']}: equilibrium or active-stick tolerance failed")

        active_names = [contacts[index]["id"] for index in sorted(active_now)]
        expected = stage["expected"]
        numeric_checks = {
            "q_normal": normal["q"],
            "gaps": normal["gaps"],
            "normal_forces": normal["forces"],
            "q_tangent": tangent["q"],
            "tangent_forces": tangent["forces"],
        }
        if active_names != expected["active"]:
            raise ValueError(f"{stage['id']}: selected active set differs from known answer")
        for key, observed in numeric_checks.items():
            target = expected[key]
            if max(abs(float(a) - float(b)) for a, b in zip(observed, target, strict=True)) > tol:
                raise ValueError(f"{stage['id']}: {key} differs from known answer")
        for index, target in enumerate(expected["references"]):
            observed = references[index]
            if target is None:
                if observed is not None:
                    raise ValueError(f"{stage['id']}: reference {index} should be unset")
            elif observed is None or abs(float(observed) - float(target)) > tol:
                raise ValueError(f"{stage['id']}: re-engagement reference {index} differs from known answer")

        stage_results.append({
            "stage_id": stage["id"],
            "admissible_normal_mask_count": len(branches),
            "active_contacts": active_names,
            "q_normal": normal["q"],
            "gaps": normal["gaps"],
            "normal_forces": normal["forces"],
            "normal_equilibrium_residual": normal["residual"],
            "q_tangent": tangent["q"],
            "episode_references": references[:],
            "tangent_forces": tangent["forces"],
            "tangent_equilibrium_residual": tangent["equilibrium_residual"],
            "active_stick_slip": tangent["active_slip"],
            "maximum_open_contact_tangent_force": max(
                [abs(tangent["forces"][i]) for i in range(len(contacts)) if i not in active_now],
                default=0.0,
            ),
        })
        active_previous = active_now
        tangent_q_previous = tangent["q"]

    return {
        "schema": "conditional_floor_two_cell_coupled_stick_fixture/v1",
        "status": "PASS_TWO_CELL_NORMAL_TANGENTIAL_RESET_FIXTURE",
        "source_sha256": source_hashes,
        "revision": fixture["revision"],
        "result_summary": {
            "stage_count": len(stage_results),
            "unique_normal_active_set_each_stage": True,
            "max_normal_equilibrium_residual": maximum_normal_residual,
            "max_tangent_equilibrium_residual": maximum_tangent_residual,
            "max_active_stick_slip": maximum_stick_slip,
            "open_contact_tangent_force": 0.0,
            "floor_gate_status": "BLOCKED",
            "native_solve_run": False,
        },
        "stages": stage_results,
        "limits": [
            "This is a hand-solvable two-contact fixture with vertical translation, pitch about +Y, one +Y tangent direction, and yaw about +Z; fixture springs are numerical devices only.",
            "Ideal stick is conditional on strictly positive normal reaction and has no force cap; no floor friction, anchorage, or stiffness is assigned.",
            "It does not establish the actual floor response, a full-frame active set, multidirectional multi-contact uniqueness, or solver convergence/termination on the candidate frame.",
            "The result supports only the bounded local normal/tangential state-selection and re-engagement rule tested here; actual frame reactions remain unresolved.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="recompute without writing")
    mode.add_argument("--write", action="store_true", help="write after frozen source pins pass")
    args = parser.parse_args()

    fixture = json.loads(FIXTURE_PATH.read_text())
    source_hashes = {}
    for name, (relative, expected) in PINNED_SOURCES.items():
        actual = sha256(ROOT / relative)
        if actual != expected or fixture["sources"].get(name) != expected:
            raise ValueError(f"source pin mismatch for {name}: {actual} != {expected}")
        source_hashes[str(relative)] = actual
    result = run_fixture(fixture, source_hashes)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    output_path = HERE / "observed.json"
    if args.write:
        output_path.write_text(rendered)
        print(f"wrote {output_path.relative_to(ROOT)}")
        return
    if not output_path.exists():
        raise SystemExit("missing observed.json; inspect source pins then run with --write")
    if output_path.read_text() != rendered:
        raise SystemExit("verification failed: computed fixture record differs from observed.json")
    summary = result["result_summary"]
    print(
        f"PASS: {summary['stage_count']} stages have unique normal masks, zero open-contact tangent force, "
        f"and equilibrium/slip residuals <= {fixture['tolerance']:.1e}; no frame response is claimed"
    )


if __name__ == "__main__":
    main()
