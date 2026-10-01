#!/usr/bin/env python3
"""Enumerate the four contact masks in the coupled two-cell fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "fixture.json"
OUTPUT_PATH = HERE / "observed.json"

PINNED_SOURCES = {
    "AGENTS.md": (
        "AGENTS.md",
        "672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536",
    ),
    "prior_two_cell_coupled_stick_README.md": (
        "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-two-cell-coupled-stick-fixture-attempt01/README.md",
        "2882f420b8b8bda0db5677aacfae0682407394e6aa13740af7ea6946c96c2c37",
    ),
    "prior_two_cell_coupled_stick_fixture.json": (
        "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-two-cell-coupled-stick-fixture-attempt01/fixture.json",
        "c4fbb8b9c1d87ddba3b848c113bda540945b67a3d0d9435150a5c5e1d195de31",
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve_linear(matrix: list[list[float]], rhs: list[float], pivot_tolerance: float) -> list[float]:
    """Solve a small dense system with partial-pivot Gauss-Jordan elimination."""
    n = len(rhs)
    if len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValueError("linear system dimensions do not match")
    augmented = [list(map(float, row)) + [float(rhs[i])] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(augmented[row][col]))
        if abs(augmented[pivot][col]) <= pivot_tolerance:
            raise ValueError(f"fixture linear system is singular at column {col}")
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        divisor = augmented[col][col]
        augmented[col] = [value / divisor for value in augmented[col]]
        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            if factor != 0.0:
                augmented[row] = [
                    augmented[row][j] - factor * augmented[col][j]
                    for j in range(n + 1)
                ]
    return [augmented[i][n] for i in range(n)]


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(float(a) * float(b) for a, b in zip(row, vector, strict=True)) for row in matrix]


def max_abs(values: list[float]) -> float:
    return max((abs(value) for value in values), default=0.0)


def positive_definite_certificate(k: list[list[float]]) -> dict[str, Any]:
    n = len(k)
    symmetry_error = max(
        (abs(float(k[i][j]) - float(k[j][i])) for i in range(n) for j in range(n)),
        default=0.0,
    )
    margins = [float(k[i][i]) - sum(abs(float(k[i][j])) for j in range(n) if j != i) for i in range(n)]
    is_spd_by_strict_diagonal_dominance = (
        symmetry_error == 0.0
        and all(float(k[i][i]) > 0.0 for i in range(n))
        and all(margin > 0.0 for margin in margins)
    )
    return {
        "symmetric": symmetry_error == 0.0,
        "maximum_symmetry_error_n_per_mm": symmetry_error,
        "positive_diagonal": all(float(k[i][i]) > 0.0 for i in range(n)),
        "strict_diagonal_dominance_margins_n_per_mm": margins,
        "spd_from_symmetric_strict_diagonal_dominance": is_spd_by_strict_diagonal_dominance,
    }


def verify_hand_load_arithmetic(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    model = fixture["model"]
    k = [[float(value) for value in row] for row in model["carrier_stiffness_n_per_mm"]]
    force_tolerance = float(fixture["tolerances"]["force_n"])
    checks = []
    for stage in fixture["stages"]:
        hand = stage["hand_answer"]
        q = [float(value) for value in hand["q_mm"]]
        contact = [float(value) for value in hand["contact_vector_n"]]
        kq = [float(value) for value in hand["Kq_hand_n"]]
        external = [float(value) for value in hand["external_W_n"]]
        computed_kq = matvec(k, q)
        reconstructed_external = [kq[i] - contact[i] for i in range(len(kq))]
        kq_error = max_abs([computed_kq[i] - kq[i] for i in range(len(kq))])
        external_error = max_abs([reconstructed_external[i] - external[i] for i in range(len(external))])
        checks.append({
            "stage_id": stage["id"],
            "hand_Kq_matches_matrix": kq_error <= force_tolerance,
            "hand_external_W_matches_Kq_minus_contact": external_error <= force_tolerance,
            "maximum_Kq_error_n": kq_error,
            "maximum_external_W_error_n": external_error,
        })
    return checks


def candidate_references(
    active: set[int],
    previous_active: set[int],
    previous_references: list[float | None],
    previous_q: list[float],
    contacts: list[dict[str, Any]],
) -> list[float | None]:
    references = previous_references[:]
    for index in active - previous_active:
        x_index = int(contacts[index]["x_index"])
        references[index] = float(previous_q[x_index])
    return references


def solve_mask(
    fixture: dict[str, Any],
    stage: dict[str, Any],
    active_indices: list[int],
    references: list[float | None],
) -> dict[str, Any]:
    model = fixture["model"]
    contacts = model["cells"]
    k = [[float(value) for value in row] for row in model["carrier_stiffness_n_per_mm"]]
    kn = float(model["normal_penalty_stiffness_n_per_mm"])
    pivot_tolerance = float(fixture["tolerances"]["linear_pivot"])
    displacement_tolerance = float(fixture["tolerances"]["displacement_mm"])
    residual_tolerance = float(fixture["tolerances"]["equilibrium_residual_n"])
    external = [float(value) for value in stage["hand_answer"]["external_W_n"]]
    active = set(active_indices)
    label = "".join("T" if index in active else "F" for index in range(len(contacts)))

    # For a trial bearing cell, N=-kn*z is substituted into Kq-contact=W.
    # For a trial open cell, its normal force is zero and no tangent constraint is added.
    system_k = [row[:] for row in k]
    for index in active_indices:
        z_index = int(contacts[index]["z_index"])
        system_k[z_index][z_index] += kn

    constraints: list[tuple[int, int]] = []
    for index in active_indices:
        x_index = int(contacts[index]["x_index"])
        reference = references[index]
        if reference is None:
            raise ValueError(f"{stage['id']} mask {label}: active contact has no episode reference")
        constraints.append((x_index, index))

    size = 4 + len(constraints)
    augmented = [[0.0 for _ in range(size)] for _ in range(size)]
    rhs = [0.0 for _ in range(size)]
    for i in range(4):
        rhs[i] = external[i]
        for j in range(4):
            augmented[i][j] = system_k[i][j]
    for column, (x_index, contact_index) in enumerate(constraints):
        multiplier_index = 4 + column
        augmented[x_index][multiplier_index] = -1.0
        augmented[multiplier_index][x_index] = 1.0
        rhs[multiplier_index] = float(references[contact_index])

    try:
        solution = solve_linear(augmented, rhs, pivot_tolerance)
    except ValueError as exc:
        return {
            "mask": label,
            "active_contacts": [contacts[index]["id"] for index in active_indices],
            "episode_references_mm": references,
            "admissible": False,
            "rejection_reasons": ["linear_solve_failed"],
            "solve_error": str(exc),
        }

    q = solution[:4]
    tangent = [0.0 for _ in contacts]
    for column, (_, contact_index) in enumerate(constraints):
        # The saddle-point multiplier is the signed contact tangent reaction under
        # the balance convention Kq - contact = external_W.
        tangent[contact_index] = solution[4 + column]
    normal = [
        (-kn * q[int(contacts[index]["z_index"])] if index in active else 0.0)
        for index in range(len(contacts))
    ]
    contact_vector: list[float] = []
    for index in range(len(contacts)):
        contact_vector.extend([tangent[index], normal[index]])

    kq = matvec(k, q)
    balance = [external[i] - kq[i] + contact_vector[i] for i in range(4)]
    stick_residual = [
        q[int(contacts[index]["x_index"])] - float(references[index])
        for index in active_indices
    ]
    reasons = []
    for index, contact in enumerate(contacts):
        z = q[int(contact["z_index"])]
        if index in active:
            if not z < 0.0:
                reasons.append(f"{contact['id']}_bearing_gap_not_negative")
            if not normal[index] > 0.0:
                reasons.append(f"{contact['id']}_bearing_normal_not_positive")
        elif z < 0.0:
            reasons.append(f"{contact['id']}_open_gap_negative")
        if index not in active and tangent[index] != 0.0:
            reasons.append(f"{contact['id']}_open_tangent_not_zero")
    if max_abs(stick_residual) > displacement_tolerance:
        reasons.append("active_stick_displacement_residual")
    if max_abs(balance) > residual_tolerance:
        reasons.append("force_balance_residual")

    # K's x/z cross block is reported as a numerical coupling diagnostic.
    # It is not assigned any floor or candidate-frame interpretation.
    x_values = [q[int(contact["x_index"])] for contact in contacts]
    z_values = [q[int(contact["z_index"])] for contact in contacts]
    cross = [[float(value) for value in row] for row in model["normal_tangent_cross_block_n_per_mm"]]
    tangent_rows_from_normal = [sum(cross[i][j] * z_values[j] for j in range(2)) for i in range(2)]
    normal_rows_from_tangent = [sum(cross[j][i] * x_values[j] for j in range(2)) for i in range(2)]

    # These are candidate branch values. Sign-inconsistent trial masks are retained
    # in full and rejected below; no branch is filtered out before recording.
    return {
        "mask": label,
        "active_contacts": [contacts[index]["id"] for index in active_indices],
        "episode_references_mm": references,
        "q_mm": q,
        "normal_forces_n": normal,
        "tangent_forces_n": tangent,
        "contact_vector_n": contact_vector,
        "carrier_Kq_n": kq,
        "carrier_cross_block_contributions_n": {
            "tangent_rows_from_normal_coordinates_x1_x2": tangent_rows_from_normal,
            "normal_rows_from_tangent_coordinates_z1_z2": normal_rows_from_tangent,
        },
        "active_stick_residual_mm": stick_residual,
        "force_balance_residual_n": balance,
        "maximum_force_balance_residual_n": max_abs(balance),
        "maximum_active_stick_residual_mm": max_abs(stick_residual),
        "admissible": not reasons,
        "rejection_reasons": reasons,
    }


def check_selected_answer(
    selected: dict[str, Any],
    stage: dict[str, Any],
    displacement_tolerance: float,
    force_tolerance: float,
) -> list[str]:
    expected = stage["expected"]
    reasons = []
    if selected["active_contacts"] != expected["active_contacts"]:
        reasons.append("selected_active_contacts_differ_from_hand_answer")
    if max_abs([
        float(a) - float(b) for a, b in zip(selected["q_mm"], expected["q_mm"], strict=True)
    ]) > displacement_tolerance:
        reasons.append("selected_q_differs_from_hand_answer")
    if max_abs([
        float(a) - float(b)
        for a, b in zip(selected["episode_references_mm"], expected["episode_references_mm"], strict=True)
    ]) > displacement_tolerance:
        reasons.append("selected_episode_references_differ_from_hand_answer")
    if max_abs([
        float(a) - float(b)
        for a, b in zip(selected["normal_forces_n"], expected["normal_forces_n"], strict=True)
    ]) > force_tolerance:
        reasons.append("selected_normal_forces_differ_from_hand_answer")
    if max_abs([
        float(a) - float(b)
        for a, b in zip(selected["tangent_forces_n"], expected["tangent_forces_n"], strict=True)
    ]) > force_tolerance:
        reasons.append("selected_tangent_forces_differ_from_hand_answer")
    return reasons


def run_fixture(fixture: dict[str, Any], source_hashes: dict[str, str]) -> dict[str, Any]:
    model = fixture["model"]
    contacts = model["cells"]
    k = [[float(value) for value in row] for row in model["carrier_stiffness_n_per_mm"]]
    tolerances = fixture["tolerances"]
    displacement_tolerance = float(tolerances["displacement_mm"])
    force_tolerance = float(tolerances["force_n"])
    residual_tolerance = float(tolerances["equilibrium_residual_n"])

    if len(contacts) != 2 or len(fixture["stages"]) != 4 or len(k) != 4:
        raise ValueError("fixture scope requires exactly two cells, four coordinates, and four stages")
    if any(len(row) != 4 for row in k):
        raise ValueError("fixture carrier stiffness must be 4x4")
    spd_certificate = positive_definite_certificate(k)
    if not spd_certificate["spd_from_symmetric_strict_diagonal_dominance"]:
        raise ValueError("fixture K failed the declared SPD certificate")

    hand_arithmetic_checks = verify_hand_load_arithmetic(fixture)
    hand_arithmetic_pass = all(
        row["hand_Kq_matches_matrix"] and row["hand_external_W_matches_Kq_minus_contact"]
        for row in hand_arithmetic_checks
    )

    start = fixture["starting_state"]
    previous_q = [float(value) for value in start["q_mm"]]
    previous_active: set[int] = set()
    previous_references: list[float | None] = [
        None if value is None else float(value)
        for value in start["episode_references_mm_by_contact"]
    ]
    stage_results = []
    max_balance = 0.0
    max_stick = 0.0
    unique_each_stage = True
    expectation_checks_pass = hand_arithmetic_pass
    stop_reason = None

    # Left/right mask codes in this order: FF, TF, FT, TT.
    masks = [set(), {0}, {1}, {0, 1}]
    for stage in fixture["stages"]:
        candidates = []
        for active in masks:
            refs = candidate_references(active, previous_active, previous_references, previous_q, contacts)
            candidates.append(solve_mask(fixture, stage, sorted(active), refs))

        admissible = [candidate for candidate in candidates if candidate["admissible"]]
        stage_record: dict[str, Any] = {
            "stage_id": stage["id"],
            "candidate_mask_count": len(candidates),
            "mask_order": [candidate["mask"] for candidate in candidates],
            "admissible_mask_count": len(admissible),
            "unique_admissible_mask": len(admissible) == 1,
            "branch_candidates": candidates,
        }
        if len(admissible) != 1:
            unique_each_stage = False
            stage_record["selected_mask"] = None
            stage_record["stage_status"] = "BOUNDED_FAILURE_NO_ADMISSIBLE_MASK" if not admissible else "BOUNDED_FAILURE_AMBIGUOUS_MASKS"
            stage_results.append(stage_record)
            stop_reason = (
                f"{stage['id']}: no admissible mask"
                if not admissible
                else f"{stage['id']}: {len(admissible)} admissible masks"
            )
            break

        selected = admissible[0]
        answer_errors = check_selected_answer(selected, stage, displacement_tolerance, force_tolerance)
        arithmetic_for_stage = next(row for row in hand_arithmetic_checks if row["stage_id"] == stage["id"])
        if not arithmetic_for_stage["hand_Kq_matches_matrix"]:
            answer_errors.append("hand_Kq_scalar_arithmetic_mismatch")
        if not arithmetic_for_stage["hand_external_W_matches_Kq_minus_contact"]:
            answer_errors.append("hand_external_W_scalar_arithmetic_mismatch")
        expectation_checks_pass = expectation_checks_pass and not answer_errors
        stage_record.update({
            "selected_mask": selected["mask"],
            "stage_status": "PASS" if not answer_errors else "FAILED_HAND_ANSWER_OR_LOAD_ORACLE",
            "selected_state": selected,
            "hand_answer_check_errors": answer_errors,
        })
        stage_results.append(stage_record)
        max_balance = max(max_balance, float(selected["maximum_force_balance_residual_n"]))
        max_stick = max(max_stick, float(selected["maximum_active_stick_residual_mm"]))

        previous_active = {
            index
            for index, contact in enumerate(contacts)
            if contact["id"] in selected["active_contacts"]
        }
        previous_references = [
            None if value is None else float(value)
            for value in selected["episode_references_mm"]
        ]
        previous_q = [float(value) for value in selected["q_mm"]]

    completed = len(stage_results) == len(fixture["stages"])
    passed = (
        completed
        and unique_each_stage
        and expectation_checks_pass
        and max_balance <= residual_tolerance
        and max_stick <= displacement_tolerance
    )
    return {
        "schema": "conditional_floor_structural_coupling_fixture/v1",
        "status": "PASS_BOUNDED_COUPLED_TWO_CELL_FIXTURE" if passed else "BOUNDED_FAILURE_OR_FIXTURE_MISMATCH",
        "input_sha256": sha256(FIXTURE_PATH),
        "producer_verifier_sha256": sha256(HERE / "verify_fixture.py"),
        "source_sha256": source_hashes,
        "revision": fixture["revision"],
        "result_summary": {
            "requested_stage_count": len(fixture["stages"]),
            "completed_stage_count": len(stage_results),
            "four_masks_enumerated_each_completed_stage": all(
                row["candidate_mask_count"] == 4 and row["mask_order"] == ["FF", "TF", "FT", "TT"]
                for row in stage_results
            ),
            "unique_admissible_mask_each_completed_stage": unique_each_stage,
            "all_hand_load_arithmetic_checks_pass": hand_arithmetic_pass,
            "all_selected_hand_answers_pass": expectation_checks_pass,
            "maximum_selected_force_balance_residual_n": max_balance,
            "maximum_selected_active_stick_residual_mm": max_stick,
            "floor_or_frame_acceptance": "NOT_EVALUATED",
            "native_solve_run": False,
        },
        "spd_certificate": spd_certificate,
        "hand_load_arithmetic_checks": hand_arithmetic_checks,
        "stages": stage_results,
        "stop_reason": stop_reason,
        "limits": [
            "The 4x4 carrier matrix and its coupling entries are mathematical fixture devices, not candidate, frame, connection, or floor parameters.",
            "This bounded fixture has two cells, one tangent axis per cell, and exactly four masks per stage; it does not establish a scalable whole-frame state-selection method or any frame stability result.",
            "Ideal stick is conditional on positive normal force, has no force cap, and supplies no floor friction, anchorage, stiffness, or resistance.",
            "Re-engagement references use the preceding recorded open-stage tangent positions. The fixture does not locate first contact during continuous load evolution or prove a full-frame loading path.",
            "The actual source-case corner boundary forces for BG001, BG003, and BG045 are missing; this fixture supplies no boundary forces or transferable corner demands.",
            "No native API, three-dimensional body mapping, CAD/mesh, frame solve, physical floor behavior, hardware behavior, or candidate acceptance is evaluated.",
        ],
    }


def validate_pins(fixture: dict[str, Any]) -> dict[str, str]:
    actual_hashes = {}
    for name, (relative_path, expected_hash) in PINNED_SOURCES.items():
        declared = fixture["source_pins"].get(name)
        if declared is None:
            raise ValueError(f"missing source pin {name}")
        if declared.get("path") != relative_path or declared.get("sha256") != expected_hash:
            raise ValueError(f"fixture source pin declaration changed for {name}")
        actual = sha256(ROOT / relative_path)
        if actual != expected_hash:
            raise ValueError(f"source pin mismatch for {name}: {actual} != {expected_hash}")
        actual_hashes[relative_path] = actual
    return actual_hashes


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write the deterministic observed record")
    mode.add_argument("--verify", action="store_true", help="recompute and compare with observed.json")
    args = parser.parse_args()

    fixture = json.loads(FIXTURE_PATH.read_text())
    source_hashes = validate_pins(fixture)
    result = run_fixture(fixture, source_hashes)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT_PATH.write_text(rendered)
        print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}")
        print(f"fixture status: {result['status']}")
        return
    if not OUTPUT_PATH.exists():
        raise SystemExit("missing observed.json; inspect inputs and source pins, then run with --write")
    if OUTPUT_PATH.read_text() != rendered:
        raise SystemExit("verification failed: recomputed record differs from observed.json")
    summary = result["result_summary"]
    if result["status"] != "PASS_BOUNDED_COUPLED_TWO_CELL_FIXTURE":
        raise SystemExit(f"bounded fixture did not pass: {result['stop_reason'] or result['status']}")
    print(
        f"PASS: {summary['completed_stage_count']} stages; four masks per stage; "
        f"maximum balance residual {summary['maximum_selected_force_balance_residual_n']:.3e} N; "
        f"no frame or floor acceptance claimed"
    )


if __name__ == "__main__":
    main()
