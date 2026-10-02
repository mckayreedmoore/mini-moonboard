"""Identify saved force states usable for conditional component arithmetic.

Bounded seating permits replay of the saved forces. It establishes neither
a unique position nor strict tangent stability or complete frame acceptance.
The producer and response hashes remain the responsibility of each consumer.
"""

import math

CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
BOUNDED_SCHEMA = "coupled_two_receiver_frame_clearance/v1"
STRICT_STATUS = "PASS_CONDITIONAL_COUPLED_FRAME_LAWS"
BOUNDED_STATUS = "PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING"


def force_state_scope(comparison):
    """Check the complete source census and preserve its seating distinction."""
    states = comparison["states"]
    if len(states) != 12 or {(s["case_id"], s["gap_scale"]) for s in states} != {
        (case, gap) for case in CASES for gap in (0.0, 1.0)
    }:
        raise ValueError("missing or duplicate six-case zero/nominal force states")
    bounded = []
    for state in states:
        if state["status"] == STRICT_STATUS:
            continue
        certificate = state.get("fixed_force_clearance_certificate") or {}
        if not (
            comparison["schema"] == BOUNDED_SCHEMA
            and comparison.get("all_two_receiver_candidate_clearances") is True
            and comparison.get("bounded_nonunique_seating_reported") is True
            and state["gap_scale"] == 1.0
            and state["status"] == BOUNDED_STATUS
            and certificate.get("schema") == "finite_clearance_fixed_force_certificate/v1"
            and certificate.get("classification") == "BOUNDED_FIXED_FORCE_SEATING_FREEDOM"
            and certificate.get("bounded") is True
            and certificate.get("strict_active_tangent_stability_established") is False
            and certificate.get("complete_joint_acceptance") is False
            and certificate.get("physical_release") is False
            and not certificate.get("recession_directions")
        ):
            raise ValueError("saved force state has no applicable bounded-seating certificate")
        audit = state["audit"]
        if not (
            audit["force_balance_n"] < 0.1
            and audit["moment_balance_nmm"] < 2
            and audit["finite_law_error_n"] < 1e-4
            and audit["minimum_unilateral_force_n"] >= -1e-4
            and audit["held_floor_motion_mm"] < 1e-8
            and audit["released_floor_force_n"] == 0.0
            and audit["positive_normal_domain_mm"] <= 10
        ):
            raise ValueError("bounded seating does not waive balance, law, floor or domain checks")
        bounds = certificate["null_coordinate_bounds"]
        if len(bounds) != certificate["nullity"] or not all(
            math.isfinite(bound["minimum"])
            and math.isfinite(bound["maximum"])
            and bound["minimum"] <= bound["maximum"]
            and all(bound[side]["status"] == "finite" for side in
                    ("lower_certificate", "upper_certificate"))
            for bound in bounds
        ):
            raise ValueError("incomplete finite seating bounds")
        bounded.append(state["case_id"])
    return {
        "source_schema": comparison["schema"],
        "bounded_nominal_cases": bounded,
        "force_scope": "Saved simultaneous force vectors; fixed-force seating freedoms do not change these forces.",
        "motion_scope": "A saved representative position is not a unique pose or an envelope over all permitted seating positions.",
        "all_source_rank300_gates_met": not bounded,
        "strict_tangent_stability_transferred": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
