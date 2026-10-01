#!/usr/bin/env python3
"""Verify a hand-solvable, one-cell conditional floor-stick fixture.

This is an analytical branch enumerator, not an FE solver. It tests one normal
contact cell coupled to two ideal tangential stick axes and fixture springs.
"""

from __future__ import annotations

import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"


def close(actual: float, expected: float, tol: float) -> bool:
    return math.isfinite(actual) and abs(actual - expected) <= tol


def normal_candidates(stage: dict, normal: dict, tol: float) -> list[dict]:
    p = stage["downward_load"]
    g0 = normal["initial_gap"]
    kn = normal["penalty_stiffness"]
    kz = normal["fixture_carrier_stiffness"]

    candidates = []

    # Open branch: N=0, so vertical equilibrium fixes z.
    z = -p / kz
    gap = g0 + z
    if gap >= -tol:
        candidates.append({"state": "open", "z": z, "gap": gap, "N": 0.0})

    # Bearing branch: N=-kn*(g0+z), with N>0 and g<0.
    z = -(p + kn * g0) / (kn + kz)
    gap = g0 + z
    reaction = -kn * gap
    if gap < -tol and reaction > tol:
        candidates.append({"state": "bearing", "z": z, "gap": gap, "N": reaction})

    return candidates


def verify() -> dict:
    fixture = json.loads(FIXTURE.read_text())
    tol = fixture["absolute_tolerance"]
    normal = fixture["normal"]
    tangent = fixture["tangent"]
    kz = normal["fixture_carrier_stiffness"]
    kt = tangent["reference_spring_stiffness"]

    previous_state = "open"
    previous_u: list[float] | None = None
    reference: list[float] | None = None
    results = []

    for stage in fixture["stages"]:
        candidates = normal_candidates(stage, normal, tol)
        assert len(candidates) == 1, (
            f"{stage['id']}: expected one admissible normal branch, "
            f"found {len(candidates)}: {candidates}"
        )
        n = candidates[0]
        bearing = n["state"] == "bearing"
        h = stage["tangent_load"]

        if bearing and previous_state != "bearing":
            assert previous_u is not None, f"{stage['id']}: no prior open displacement to reset from"
            reference = list(previous_u)

        if bearing:
            assert reference is not None, f"{stage['id']}: bearing state has no tangent reference"
            u = list(reference)
            spring = [-kt * u[0], -kt * u[1]]
            contact = [-h[0] - spring[0], -h[1] - spring[1]]
        else:
            u = [h[0] / kt, h[1] / kt]
            spring = [-kt * u[0], -kt * u[1]]
            contact = [0.0, 0.0]

        vertical_residual = n["N"] - kz * n["z"] - stage["downward_load"]
        tangent_residual = [h[i] + spring[i] + contact[i] for i in range(2)]
        slip = [u[i] - reference[i] for i in range(2)] if bearing else [0.0, 0.0]

        actual = {
            "state": n["state"],
            "z": n["z"],
            "gap": n["gap"],
            "N": n["N"],
            "reference": reference,
            "u": u,
            "T": contact,
        }
        expected = stage["expected"]
        assert actual["state"] == expected["state"], f"{stage['id']}: state mismatch"
        for key in ("z", "gap", "N"):
            assert close(actual[key], expected[key], tol), (
                f"{stage['id']}: {key}={actual[key]} expected {expected[key]}"
            )
        for key in ("u", "T"):
            assert all(close(a, e, tol) for a, e in zip(actual[key], expected[key])), (
                f"{stage['id']}: {key}={actual[key]} expected {expected[key]}"
            )
        assert actual["reference"] == expected["reference"], (
            f"{stage['id']}: reference={actual['reference']} expected {expected['reference']}"
        )
        assert abs(vertical_residual) <= tol, f"{stage['id']}: vertical residual {vertical_residual}"
        assert all(abs(x) <= tol for x in tangent_residual), (
            f"{stage['id']}: tangent residual {tangent_residual}"
        )
        assert all(abs(x) <= tol for x in slip), f"{stage['id']}: bearing slip {slip}"
        assert bearing or all(abs(x) <= tol for x in contact), (
            f"{stage['id']}: open contact carried tangent reaction {contact}"
        )

        results.append({
            "id": stage["id"],
            **actual,
            "normal_branch_count": len(candidates),
            "vertical_residual": vertical_residual,
            "tangent_residual": tangent_residual,
            "bearing_slip": slip,
        })
        previous_state = n["state"]
        previous_u = u

    return {
        "result": "PASS_LOCAL_ANALYTICAL_FIXTURE",
        "stage_count": len(results),
        "all_stages_have_one_admissible_normal_branch": True,
        "max_abs_vertical_residual": max(abs(x["vertical_residual"]) for x in results),
        "max_abs_tangent_residual": max(
            abs(v) for x in results for v in x["tangent_residual"]
        ),
        "max_abs_bearing_slip": max(
            abs(v) for x in results for v in x["bearing_slip"]
        ),
        "stages": results,
        "limitations": [
            "one normal support cell and two tangent axes only",
            "fixture carrier and reference springs are analytic devices, not floor or frame properties",
            "does not test multi-cell load sharing, rotational coupling, or full-frame branch uniqueness",
            "does not implement or validate a native solver method",
            "does not establish actual floor friction, anchor behavior, support reactions, or structural acceptance"
        ]
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
