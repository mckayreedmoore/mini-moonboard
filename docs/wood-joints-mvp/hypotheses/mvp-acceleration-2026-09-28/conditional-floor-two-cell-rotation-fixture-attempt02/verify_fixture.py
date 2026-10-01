#!/usr/bin/env python3
"""Exhaustively verify the four normal active sets in fixture.json."""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def solve_2x2(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    a, b = matrix[0]
    c, d = matrix[1]
    determinant = a * d - b * c
    if not math.isfinite(determinant) or determinant <= 0.0:
        raise ValueError(f"non-positive or invalid fixture matrix determinant: {determinant}")
    return [(rhs[0] * d - b * rhs[1]) / determinant,
            (a * rhs[1] - rhs[0] * c) / determinant]


def candidate_for_mask(model: dict, stage: dict, mask: tuple[bool, ...]) -> dict:
    contacts = model["contacts"]
    kn = model["normal_penalty_stiffness"]
    kz = model["carrier_stiffness"]["vertical"]
    kr = model["carrier_stiffness"]["rotational"]
    matrix = [[kz, 0.0], [0.0, kr]]
    rhs = [-stage["downward_load"], stage["applied_moment_y"]]

    for contact, active in zip(contacts, mask, strict=True):
        if not active:
            continue
        x = contact["x"]
        row = [1.0, -x]
        g0 = contact["initial_gap"]
        for i in range(2):
            rhs[i] -= kn * row[i] * g0
            for j in range(2):
                matrix[i][j] += kn * row[i] * row[j]

    q = solve_2x2(matrix, rhs)
    gaps = []
    normals = []
    for contact, active in zip(contacts, mask, strict=True):
        gap = contact["initial_gap"] + q[0] - q[1] * contact["x"]
        normal = max(0.0, -kn * gap) if active else 0.0
        gaps.append(gap)
        normals.append(normal)
    return {"mask": mask, "q": q, "gaps": gaps, "normal_forces": normals}


def admissible(candidate: dict, tolerance: float) -> bool:
    for active, gap, normal in zip(
        candidate["mask"], candidate["gaps"], candidate["normal_forces"], strict=True
    ):
        if active and not (gap < -tolerance and normal > tolerance):
            return False
        if not active and not (gap >= -tolerance and normal == 0.0):
            return False
    return True


def evaluate(model: dict, stage: dict, tolerance: float) -> dict:
    contacts = model["contacts"]
    candidates = [
        candidate_for_mask(model, stage, mask)
        for mask in itertools.product((False, True), repeat=len(contacts))
    ]
    valid = [candidate for candidate in candidates if admissible(candidate, tolerance)]
    if len(valid) != 1:
        raise AssertionError(
            f"{stage['id']}: expected one admissible active set, found {len(valid)}; "
            f"candidate masks={[c['mask'] for c in valid]}"
        )

    candidate = valid[0]
    names = [contact["id"] for contact, active in zip(contacts, candidate["mask"], strict=True) if active]
    carrier = [
        -model["carrier_stiffness"]["vertical"] * candidate["q"][0],
        -model["carrier_stiffness"]["rotational"] * candidate["q"][1],
    ]
    contact_generalized = [0.0, 0.0]
    for contact, normal in zip(contacts, candidate["normal_forces"], strict=True):
        contact_generalized[0] += normal
        contact_generalized[1] += -contact["x"] * normal
    external = [-stage["downward_load"], stage["applied_moment_y"]]
    residual = [carrier[i] + external[i] + contact_generalized[i] for i in range(2)]

    expected = stage["expected"]
    if names != expected["active_contacts"]:
        raise AssertionError(f"{stage['id']}: active contacts {names} != {expected['active_contacts']}")
    for field in ("q", "gaps", "normal_forces"):
        actual = candidate[field]
        target = expected[field]
        if any(abs(a - b) > tolerance for a, b in zip(actual, target, strict=True)):
            raise AssertionError(f"{stage['id']}: {field} {actual} != {target}")
    if max(abs(value) for value in residual) > tolerance:
        raise AssertionError(f"{stage['id']}: generalized equilibrium residual {residual}")

    return {
        "id": stage["id"],
        "admissible_active_set_count": len(valid),
        "active_contacts": names,
        "q": candidate["q"],
        "gaps": candidate["gaps"],
        "normal_forces": candidate["normal_forces"],
        "carrier_generalized_reaction": carrier,
        "external_generalized_force": external,
        "contact_generalized_reaction": contact_generalized,
        "generalized_equilibrium_residual": residual,
    }


def main() -> None:
    fixture = json.loads((ROOT / "fixture.json").read_text())
    outputs = [
        evaluate(fixture["model"], stage, fixture["absolute_tolerance"])
        for stage in fixture["stages"]
    ]
    print(json.dumps({
        "result": "PASS_TWO_CELL_NORMAL_ACTIVE_SET_FIXTURE",
        "stage_count": len(outputs),
        "enumerated_subsets_per_stage": 4,
        "all_stages_have_one_admissible_active_set": all(
            output["admissible_active_set_count"] == 1 for output in outputs
        ),
        "max_abs_generalized_equilibrium_residual": max(
            abs(value)
            for output in outputs
            for value in output["generalized_equilibrium_residual"]
        ),
        "limitations": [
            "two support cells and rigid-body vertical/rotational degrees of freedom only",
            "linear carrier springs are analytic fixture devices, not floor or candidate stiffness",
            "normal contact only; no tangential stick, distributed frame flexibility, or multi-cell coupling",
            "does not validate a native solver implementation or establish a full-frame branch uniqueness claim",
            "does not establish actual floor support, friction, anchorage, or structural acceptance"
        ],
        "stages": outputs
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
