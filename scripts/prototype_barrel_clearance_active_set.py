#!/usr/bin/env python3
"""Throwaway prototype for coupled barrel-bolt lateral clearance.

Question answered: how can the current linear-spring active-set loop represent
a 0.575 mm circular radial dead zone without giving the joint stiffness or
force before the bolt reaches the bore wall?

This is a two-degree-of-freedom equilibrium toy, not a structural model.  A
linear surrounding structure (``SUPPORT_K``) keeps the open state solvable.  An
engaged trial activates both local lateral springs and applies a balanced
reference-force correction, giving the accepted connector law

    force = BEARING_K * (displacement - CLEARANCE * contact_normal).

Updating ``contact_normal`` to the solved displacement direction makes the
converged force equal to ``BEARING_K * max(radius - CLEARANCE, 0)`` in the
radial direction.  At first contact the correction exactly cancels the spring
force, so engagement introduces no fictitious zero-slip force.

Run from repository root:

    uv run python scripts/prototype_barrel_clearance_active_set.py
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isclose

CLEARANCE_MM = 0.575
SUPPORT_K_N_PER_MM = 100.0
BEARING_K_N_PER_MM = 1000.0
TOLERANCE_MM = 1.0e-10
NORMAL_TOLERANCE = 1.0e-10
MAX_CYCLES = 100


Vector = tuple[float, float]


def add(first: Vector, second: Vector) -> Vector:
    return first[0] + second[0], first[1] + second[1]


def scale(value: float, vector: Vector) -> Vector:
    return value * vector[0], value * vector[1]


def norm(vector: Vector) -> float:
    return hypot(*vector)


def unit(vector: Vector) -> Vector:
    length = norm(vector)
    if length <= TOLERANCE_MM:
        raise ValueError("Zero vector has no contact direction")
    return vector[0] / length, vector[1] / length


@dataclass(frozen=True)
class ClearanceState:
    """One coupled state owns both local lateral spring directions."""

    contact_normal: Vector | None = None

    @property
    def name(self) -> str:
        return "OPEN" if self.contact_normal is None else "ENGAGED"


@dataclass(frozen=True)
class Trial:
    cycle: int
    state: ClearanceState
    displacement_mm: Vector
    radius_mm: float
    connector_force_n: Vector
    proposed: ClearanceState
    accepted: bool


def linear_trial(load_n: Vector, state: ClearanceState) -> tuple[Vector, Vector]:
    """Solve one linearized state and recover its offset-corrected force."""
    if state.contact_normal is None:
        displacement = scale(1.0 / SUPPORT_K_N_PER_MM, load_n)
        return displacement, (0.0, 0.0)

    normal = state.contact_normal
    # Equilibrium:
    # load = SUPPORT_K*u + BEARING_K*(u - CLEARANCE*normal).
    displacement = scale(
        1.0 / (SUPPORT_K_N_PER_MM + BEARING_K_N_PER_MM),
        add(load_n, scale(BEARING_K_N_PER_MM * CLEARANCE_MM, normal)),
    )
    connector_force = scale(
        BEARING_K_N_PER_MM,
        add(displacement, scale(-CLEARANCE_MM, normal)),
    )
    return displacement, connector_force


def proposed_state(displacement_mm: Vector) -> ClearanceState:
    """Apply circular-gap complementarity to a solved trial displacement."""
    radius = norm(displacement_mm)
    if radius <= CLEARANCE_MM + TOLERANCE_MM:
        return ClearanceState()
    return ClearanceState(unit(displacement_mm))


def state_matches(first: ClearanceState, second: ClearanceState) -> bool:
    if first.contact_normal is None or second.contact_normal is None:
        return first.contact_normal is second.contact_normal
    return norm(
        add(first.contact_normal, scale(-1.0, second.contact_normal))
    ) <= NORMAL_TOLERANCE


def solve(load_n: Vector, initial: ClearanceState) -> tuple[ClearanceState, list[Trial]]:
    """Resolve one load action using production-shaped active-set iterations."""
    state = initial
    history: list[Trial] = []
    seen: set[tuple[str, float | None, float | None]] = set()
    for cycle in range(MAX_CYCLES):
        signature = (
            state.name,
            None if state.contact_normal is None else round(state.contact_normal[0], 12),
            None if state.contact_normal is None else round(state.contact_normal[1], 12),
        )
        if signature in seen:
            raise RuntimeError(f"Active-set state repeated for load {load_n}")
        seen.add(signature)
        displacement, force = linear_trial(load_n, state)
        proposed = proposed_state(displacement)
        accepted = state_matches(state, proposed)
        history.append(
            Trial(
                cycle=cycle,
                state=state,
                displacement_mm=displacement,
                radius_mm=norm(displacement),
                connector_force_n=force,
                proposed=proposed,
                accepted=accepted,
            )
        )
        if accepted:
            return state, history
        state = proposed
    raise RuntimeError(f"Active set did not converge for load {load_n}")


def expected_force(displacement_mm: Vector) -> Vector:
    """Exact circular dead-zone law used only to audit accepted toy states."""
    radius = norm(displacement_mm)
    if radius <= CLEARANCE_MM:
        return 0.0, 0.0
    return scale(BEARING_K_N_PER_MM * (radius - CLEARANCE_MM), unit(displacement_mm))


def close(first: Vector, second: Vector, tolerance: float = 1.0e-7) -> bool:
    return norm(add(first, scale(-1.0, second))) <= tolerance


def print_trial(scenario: str, action: int, load: Vector, trial: Trial) -> None:
    normal = trial.state.contact_normal
    next_normal = trial.proposed.contact_normal
    print(
        f"{scenario:16s} action={action:02d} load={load!s:>15s} "
        f"cycle={trial.cycle:02d} {trial.state.name:7s} "
        f"n={normal!s:>28s} u={tuple(round(x, 6) for x in trial.displacement_mm)} "
        f"r={trial.radius_mm:.6f} F={tuple(round(x, 6) for x in trial.connector_force_n)} "
        f"=> {trial.proposed.name:7s} next_n={next_normal} accepted={trial.accepted}"
    )


def run_scenario(name: str, loads: tuple[Vector, ...]) -> list[Trial]:
    print(f"\nSCENARIO {name}")
    state = ClearanceState()
    accepted_trials = []
    for action, load in enumerate(loads):
        state, history = solve(load, state)
        for trial in history:
            print_trial(name, action, load, trial)
        accepted_trials.append(history[-1])
    return accepted_trials


def audit(all_trials: dict[str, list[Trial]]) -> None:
    accepted = [trial for trials in all_trials.values() for trial in trials]
    open_trials = [trial for trial in accepted if trial.state.name == "OPEN"]
    engaged_trials = [trial for trial in accepted if trial.state.name == "ENGAGED"]

    invariants = {
        "open_force_is_exactly_zero": all(
            trial.connector_force_n == (0.0, 0.0) for trial in open_trials
        ),
        "no_engagement_inside_or_at_clearance": all(
            trial.radius_mm <= CLEARANCE_MM + TOLERANCE_MM for trial in open_trials
        ),
        "engaged_only_outside_clearance": all(
            trial.radius_mm > CLEARANCE_MM for trial in engaged_trials
        ),
        "accepted_force_matches_circular_dead_zone": all(
            close(trial.connector_force_n, expected_force(trial.displacement_mm))
            for trial in accepted
        ),
        "accepted_engaged_normal_follows_displacement": all(
            close(trial.state.contact_normal, unit(trial.displacement_mm))
            for trial in engaged_trials
        ),
        "boundary_force_is_continuous": close(
            expected_force((CLEARANCE_MM, 0.0)), (0.0, 0.0)
        ),
        "diagonal_contact_uses_radius_not_component_deadbands": (
            norm((0.5, 0.4)) > CLEARANCE_MM
            and abs(0.5) < CLEARANCE_MM
            and abs(0.4) < CLEARANCE_MM
        ),
        "equal_radius_is_rotation_invariant": isclose(
            norm(expected_force((0.7, 0.0))),
            norm(expected_force((0.7 / 2**0.5, 0.7 / 2**0.5))),
            abs_tol=1.0e-9,
        ),
        "reversal_releases_before_opposite_engagement": [
            trial.state.name for trial in all_trials["reversal"]
        ] == ["ENGAGED", "OPEN", "OPEN", "OPEN", "ENGAGED"],
    }
    print("\nINVARIANTS")
    for name, passed in invariants.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not all(invariants.values()):
        raise AssertionError("Prototype invariant failed")


def main() -> None:
    # Threshold load is SUPPORT_K * CLEARANCE = 57.5 N.  Each scenario starts
    # open so its transitions remain independently readable.
    scenarios = {
        "loading": ((0.0, 0.0), (30.0, 0.0), (57.5, 0.0), (100.0, 0.0)),
        "reversal": (
            (100.0, 0.0),
            (50.0, 0.0),
            (0.0, 0.0),
            (-40.0, 0.0),
            (-120.0, 0.0),
        ),
        "asymmetric-2d": (
            (40.0, 40.0),
            (50.0, 40.0),
            (50.0, 10.0),
            (-50.0, 35.0),
        ),
    }
    results = {name: run_scenario(name, loads) for name, loads in scenarios.items()}
    audit(results)


if __name__ == "__main__":
    main()
