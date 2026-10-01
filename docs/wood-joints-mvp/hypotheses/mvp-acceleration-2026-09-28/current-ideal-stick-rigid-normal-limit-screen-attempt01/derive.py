#!/usr/bin/env python3
"""Reproduce the exact-rational rigid-normal limit screen from the prior toy."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
PACKET = Path(__file__).resolve().parent
TOY_SPEC = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    / "current-springa-ideal-stick-branch-cycle-method-attempt01/fixture-spec.json"
)


def frac(value: object) -> Fraction:
    return Fraction(str(value))


def s(value: Fraction) -> str:
    return str(value)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matvec(k: tuple[tuple[Fraction, ...], ...], u: tuple[Fraction, ...]):
    return tuple(sum(k[i][j] * u[j] for j in range(3)) for i in range(3))


def residual(
    k: tuple[tuple[Fraction, ...], ...],
    u: tuple[Fraction, ...],
    lam: tuple[Fraction, Fraction],
    normal: Fraction,
    load: tuple[Fraction, Fraction, Fraction],
):
    internal = matvec(k, u)
    return tuple(
        internal[i] + (lam[i] if i < 2 else normal) - load[i]
        for i in range(3)
    )


def penalty_active(
    k_matrix: tuple[tuple[Fraction, ...], ...],
    fx: Fraction,
    fq: Fraction,
    kn: Fraction,
):
    # t1=t2=0; the normal equilibrium is 2q + kn*max(q,0) = Fq.
    if fq > 0:
        q = fq / (2 + kn)
    else:
        q = fq / 2
    normal = kn * max(q, Fraction(0))
    u = (Fraction(0), Fraction(0), q)
    lam = (fx - q, Fraction(0))
    r = residual(k_matrix, u, lam, normal, (fx, Fraction(0), fq))
    assert r == (0, 0, 0)
    return {
        "u_exact": [s(x) for x in u],
        "normal_force_exact": s(normal),
        "tangent_multiplier_exact": [s(x) for x in lam],
        "body_residual_exact": [s(x) for x in r],
        "strict_positive_normal_gate_passes": q > 0,
    }


def penalty_released(
    k_matrix: tuple[tuple[Fraction, ...], ...],
    fx: Fraction,
    fq: Fraction,
    kn: Fraction,
):
    # First try the open branch. If its q would compress, solve with the
    # unilateral spring engaged; all screen cases land on this compression
    # branch.
    q_open = (-fx + 2 * fq) / 3
    if q_open <= 0:
        q = q_open
        normal = Fraction(0)
    else:
        q = (2 * fq - fx) / (2 * kn + 3)
        normal = kn * q
        assert q > 0
    t1 = (fx - q) / 2
    u = (t1, Fraction(0), q)
    r = residual(k_matrix, u, (Fraction(0), Fraction(0)), normal,
                 (fx, Fraction(0), fq))
    assert r == (0, 0, 0)
    return {
        "u_exact": [s(x) for x in u],
        "normal_force_exact": s(normal),
        "tangent_multiplier_exact": ["0", "0"],
        "body_residual_exact": [s(x) for x in r],
        "released_mask_gate_passes": q <= 0,
    }


def rigid_active(
    k_matrix: tuple[tuple[Fraction, ...], ...],
    fx: Fraction,
    fq: Fraction,
):
    # q=t1=t2=0; support multipliers enter the same internal-force balance.
    u = (Fraction(0), Fraction(0), Fraction(0))
    lam = (fx, Fraction(0))
    normal = fq
    r = residual(k_matrix, u, lam, normal, (fx, Fraction(0), fq))
    assert r == (0, 0, 0)
    return {
        "u_exact": [s(x) for x in u],
        "normal_force_exact": s(normal),
        "tangent_multiplier_exact": [s(x) for x in lam],
        "body_residual_exact": [s(x) for x in r],
        "active_contact_condition_n_nonnegative": normal >= 0,
        "strict_positive_pressure_tangent_gate_passes": normal > 0,
    }


def rigid_released(
    k_matrix: tuple[tuple[Fraction, ...], ...],
    fx: Fraction,
    fq: Fraction,
):
    # Solve K*u=f with both contact/tangent rows released and n=0.
    t1 = (2 * fx - fq) / 3
    q = (-fx + 2 * fq) / 3
    u = (t1, Fraction(0), q)
    r = residual(k_matrix, u, (Fraction(0), Fraction(0)), Fraction(0),
                 (fx, Fraction(0), fq))
    assert r == (0, 0, 0)
    return {
        "u_exact": [s(x) for x in u],
        "normal_force_exact": "0",
        "tangent_multiplier_exact": ["0", "0"],
        "body_residual_exact": [s(x) for x in r],
        "inactive_gap_condition_q_negative": q < 0,
    }


def main() -> None:
    spec = json.loads(TOY_SPEC.read_text())
    k_matrix = tuple(tuple(frac(x) for x in row)
                     for row in spec["structure"]["stiffness_matrix_N_per_mm"])
    source_load = tuple(frac(x) for x in spec["load_N"])
    kn = frac(spec["normal_support"]["stiffness_N_per_mm"])
    assert k_matrix == (
        (Fraction(2), Fraction(0), Fraction(1)),
        (Fraction(0), Fraction(1), Fraction(0)),
        (Fraction(1), Fraction(0), Fraction(2)),
    )
    assert source_load == (Fraction(-4), Fraction(0), Fraction(-1))
    assert kn == 2
    assert spec["normal_support"]["law"] == "n(q) = 2 * max(q, 0)"

    loads = [
        ("original_no_branch", source_load),
        ("strictly_positive_contact_calibration",
         (Fraction(-4), Fraction(0), Fraction(1))),
        ("zero_normal_boundary",
         (Fraction(-4), Fraction(0), Fraction(0))),
    ]
    cases = []
    for name, load in loads:
        fx, _, fq = load
        pa = penalty_active(k_matrix, fx, fq, kn)
        pr = penalty_released(k_matrix, fx, fq, kn)
        ra = rigid_active(k_matrix, fx, fq)
        rr = rigid_released(k_matrix, fx, fq)
        penalty_has_branch = (
            pa["strict_positive_normal_gate_passes"]
            or pr["released_mask_gate_passes"]
        )
        rigid_has_inclusive_branch = (
            ra["active_contact_condition_n_nonnegative"]
            or rr["inactive_gap_condition_q_negative"]
        )
        rigid_has_strict_pressure_branch = (
            ra["strict_positive_pressure_tangent_gate_passes"]
            or rr["inactive_gap_condition_q_negative"]
        )
        cases.append({
            "case_id": name,
            "load_N": [s(x) for x in load],
            "penalty_kn_N_per_mm": s(kn),
            "penalty_active_stick_branch": pa,
            "penalty_released_branch": pr,
            "penalty_gated_static_branch_exists": penalty_has_branch,
            "rigid_active_stick_branch": ra,
            "rigid_released_branch": rr,
            "rigid_gated_static_branch_exists_with_n_nonnegative_active":
                rigid_has_inclusive_branch,
            "rigid_gated_static_branch_exists_if_stick_requires_n_positive":
                rigid_has_strict_pressure_branch,
        })

    # For the original load, the released finite-penalty branch converges in
    # normal closure/reaction but not in tangential stick state.
    fx, _, fq = source_load
    q_num = 2 * fq - fx
    released_limit = {
        "q_of_k_exact": f"{s(q_num)}/(2*k+3)",
        "n_of_k_exact": f"k*{s(q_num)}/(2*k+3)",
        "t1_of_k_exact": f"{s(fx)}/2 - {s(q_num)}/(2*(2*k+3))",
        "limit_k_to_infinity": {
            "q_exact": "0+",
            "normal_force_exact": s(q_num / 2),
            "t1_exact": s(fx / 2),
            "stick_constraint_t1_equals_zero": False,
        },
        "gate_result": (
            "Positive limiting reaction activates the ideal no-slip row, but "
            "the released-mask limit has nonzero t1; it is not a coupled branch."
        ),
    }

    output = {
        "schema": "ideal_stick_rigid_normal_limit_screen/v1",
        "status": "EXACT_RATIONAL_BRANCH_SCREEN_ONLY_NO_NATIVE_RUN",
        "coordinates": ["t1", "t2", "q"],
        "sign_convention": (
            "K*u + [lambda1,lambda2,n] = load; q>0 is compression; "
            "rigid inactive gap q<0,n=0; rigid active q=0,n>=0."
        ),
        "stiffness_matrix_N_per_mm": [[s(x) for x in row] for row in k_matrix],
        "penalty_normal_law": "n(q)=k*max(q,0)",
        "source_toy_stiffness_N_per_mm": s(kn),
        "source_toy_load_N": [s(x) for x in source_load],
        "cases": cases,
        "original_load_released_mask_stiffness_limit": released_limit,
        "reaction_method_authority": {
            "verified_method_fixture": (
                "current-exact-floor-mpc-fixture-attempt02"
            ),
            "verified_tangential_mapping":
                "RF_REFERENCE_MINUS_DEPENDENT_CLOAD",
            "limit": (
                "That coupon verified exact tangential MPC reaction recovery "
                "with dependent-node CLOAD transfer. It did not verify rigid "
                "unilateral branch switching or normal-multiplier sign."
            ),
        },
        "engineering_scope": {
            "current_source_floor_physics_changed": False,
            "frame_corner_demands_unlocked": False,
            "full_frame_no_branch_proven": False,
            "native_solve_launched": False,
            "friction_or_floor_capacity_qualified": False,
        },
        "source_toy_fixture_spec": {
            "path_from_repo_root": str(TOY_SPEC.relative_to(ROOT)),
            "sha256": sha256(TOY_SPEC),
        },
    }
    assert [case["penalty_gated_static_branch_exists"] for case in cases] == [
        False, True, False
    ]
    assert [case[
        "rigid_gated_static_branch_exists_with_n_nonnegative_active"
    ] for case in cases] == [False, True, True]
    assert [case[
        "rigid_gated_static_branch_exists_if_stick_requires_n_positive"
    ] for case in cases] == [False, True, False]
    (PACKET / "screen.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n"
    )
    print(f"wrote {PACKET / 'screen.json'}")


if __name__ == "__main__":
    main()
