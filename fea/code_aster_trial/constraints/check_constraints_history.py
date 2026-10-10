#!/usr/bin/env python3
"""Independently check a Code_Aster 17.4 constraint-surrogate nodal history.

The input is the plain JSON exported from the parent's MED postprocessor. This
checker does not import Code_Aster or MEDCoupling and does not launch a solve.
It checks all 101 stored states for both modes against the average-acceleration
Newmark history and checks physical-tetra kinetic energy using the consistent
mass matrix in oracle.json.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


COMPONENTS = ("DX", "DY", "DZ", "DRX", "DRY", "DRZ")
VECTOR_COMPONENTS = ("DX", "DY", "DZ")
FIELD_SUFFIX = {"DEPL": "DEPL", "VITE": "VITE", "ACCE": "ACCE"}
STATE_RTOL = 2.0e-4
ZERO_STATE_ATOL = 1.0e-12
ENERGY_RTOL = 2.0e-4
# Consistent with three velocity components each bounded by ZERO_STATE_ATOL
# for a unit-mass body: 0.5 * 1 kg * 3 * (1e-12 m/s)^2 = 1.5e-24 J.
ZERO_ENERGY_ATOL_J = 2.0e-24
COORD_ATOL_M = 1.0e-12
TIME_ATOL_S = 1.0e-12


class CheckError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckError(f"cannot read JSON {path}: {exc}") from exc


def finite_number(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise CheckError(f"{label} is not numeric: {value!r}") from exc
    require(math.isfinite(result), f"{label} is not finite: {result!r}")
    return result


def build_newmark_history(
    ramp_slope: float, dt: float, increments: int, beta: float, gamma: float
) -> list[tuple[float, float, float, float]]:
    """Return (time, q, qdot, qddot), evaluating the discrete recurrence."""
    history = [(0.0, 0.0, 0.0, 0.0)]
    q = qdot = qddot = 0.0
    for step in range(1, increments + 1):
        time = step * dt
        next_accel = ramp_slope * time
        next_q = (
            q
            + dt * qdot
            + dt * dt * (0.5 - beta) * qddot
            + beta * dt * dt * next_accel
        )
        next_qdot = (
            qdot
            + dt * (1.0 - gamma) * qddot
            + dt * gamma * next_accel
        )
        q, qdot, qddot = next_q, next_qdot, next_accel
        history.append((time, q, qdot, qddot))
    return history


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def kinetic_energy(velocities: list[list[float]], scalar_mass: list[list[float]]) -> float:
    """Compute 1/2 v^T M v for 4 physical nodes and uncoupled xyz blocks."""
    energy = 0.0
    for component in range(3):
        v = [velocities[node][component] for node in range(4)]
        mv = [dot(row, v) for row in scalar_mass]
        energy += 0.5 * dot(v, mv)
    return energy


def mode_velocity_shape(
    case: str, physical_coordinates: list[list[float]]
) -> list[list[float]]:
    if case == "translation_x":
        return [[1.0, 0.0, 0.0] for _ in physical_coordinates]
    # Positive DRY maps to (z, 0, -x) for the infinitesimal Y rotation.
    return [[xyz[2], 0.0, -xyz[0]] for xyz in physical_coordinates]


def effective_mode_mass(
    shape: list[list[float]], scalar_mass: list[list[float]]
) -> float:
    result = 0.0
    for component in range(3):
        values = [node[component] for node in shape]
        result += dot(values, [dot(row, values) for row in scalar_mass])
    return result


def expected_field_values(
    case: str,
    quantity: str,
    qstate: tuple[float, float, float, float],
    coordinates: list[list[float]],
) -> list[list[float]]:
    _, q, qdot, qddot = qstate
    scalar = {"DEPL": q, "VITE": qdot, "ACCE": qddot}[quantity]
    expected = [[0.0] * len(COMPONENTS) for _ in coordinates]
    if case == "translation_x":
        for node in range(9):
            expected[node][COMPONENTS.index("DX")] = scalar
        return expected

    for node, xyz in enumerate(coordinates):
        expected[node][COMPONENTS.index("DX")] = xyz[2] * scalar
        expected[node][COMPONENTS.index("DZ")] = -xyz[0] * scalar
    # The last node is the reference point. Its DRY is the generalized angle,
    # angular velocity, or angular acceleration represented by this field.
    expected[8][COMPONENTS.index("DRY")] = scalar
    return expected


def validate_and_index_history(
    history: dict[str, Any],
    expected_coordinates: list[list[float]],
    times: list[float],
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    errors: list[str] = []
    require(isinstance(history, dict), "nodal history top level must be an object")
    coords = history.get("coordinates")
    require(isinstance(coords, list), "nodal history has no coordinates array")
    require(len(coords) == len(expected_coordinates),
            f"expected {len(expected_coordinates)} node coordinates, got {len(coords)}")
    for node, (actual, expected) in enumerate(zip(coords, expected_coordinates)):
        require(isinstance(actual, list) and len(actual) == 3,
                f"coordinate row {node} must contain three numbers")
        for axis, (actual_value, expected_value) in enumerate(zip(actual, expected)):
            actual_number = finite_number(actual_value, f"coordinate[{node}][{axis}]")
            if abs(actual_number - expected_value) > COORD_ATOL_M:
                errors.append(
                    f"coordinate mismatch node-index={node} axis={axis}: "
                    f"{actual_number:.17g} vs {expected_value:.17g} m"
                )

    fields = history.get("fields")
    require(isinstance(fields, dict), "nodal history has no fields object")
    indexed: dict[str, list[dict[str, Any]]] = {}
    expected_field_names = {
        f"RESULT_{prefix}{suffix}"
        for prefix in ("T", "R")
        for suffix in FIELD_SUFFIX.values()
    }
    missing = sorted(expected_field_names.difference(fields))
    require(not missing, f"nodal history is missing fields: {', '.join(missing)}")

    for field_name in sorted(expected_field_names):
        states = fields[field_name]
        require(isinstance(states, list), f"{field_name} must contain a state list")
        require(len(states) == len(times),
                f"{field_name} has {len(states)} states; expected {len(times)}")
        checked: list[dict[str, Any]] = []
        for state_index, (state, expected_time) in enumerate(zip(states, times)):
            require(isinstance(state, dict), f"{field_name}[{state_index}] must be an object")
            for key in ("iteration", "order", "time", "components", "values"):
                require(key in state, f"{field_name}[{state_index}] has no {key!r}")
            require(int(state["iteration"]) == state_index,
                    f"{field_name} iteration sequence mismatch at {state_index}")
            require(int(state["order"]) == state_index,
                    f"{field_name} order sequence mismatch at {state_index}")
            actual_time = finite_number(state["time"], f"{field_name}[{state_index}].time")
            if abs(actual_time - expected_time) > TIME_ATOL_S:
                errors.append(
                    f"{field_name} time mismatch at state {state_index}: "
                    f"{actual_time:.17g} vs {expected_time:.17g} s"
                )
            components = state["components"]
            require(isinstance(components, list), f"{field_name}[{state_index}].components must be a list")
            require(set(components) == set(COMPONENTS) and len(components) == len(COMPONENTS),
                    f"{field_name}[{state_index}] components do not match {COMPONENTS}")
            values = state["values"]
            require(isinstance(values, list) and len(values) == len(expected_coordinates),
                    f"{field_name}[{state_index}] must contain {len(expected_coordinates)} node rows")
            for node, row in enumerate(values):
                require(isinstance(row, list) and len(row) == len(components),
                        f"{field_name}[{state_index}] node row {node} has wrong width")
                for component, value in zip(components, row):
                    finite_number(value, f"{field_name}[{state_index}][{node}].{component}")
            checked.append(state)
        indexed[field_name] = checked

    return indexed, errors


def compare_field(
    actual_states: list[dict[str, Any]],
    expected_states: list[list[list[float]]],
    field_name: str,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    max_abs = 0.0
    max_rel = 0.0
    max_zero_abs = 0.0
    worst_abs: dict[str, Any] | None = None
    worst_rel: dict[str, Any] | None = None
    worst_zero: dict[str, Any] | None = None

    for step, (state, expected_nodes) in enumerate(zip(actual_states, expected_states)):
        components = state["components"]
        index = {name: components.index(name) for name in components}
        for node, (actual_row, expected_row) in enumerate(zip(state["values"], expected_nodes)):
            for component in COMPONENTS:
                actual = finite_number(actual_row[index[component]], f"{field_name}[{step}][{node}].{component}")
                target = expected_row[COMPONENTS.index(component)]
                error = abs(actual - target)
                if error > max_abs:
                    max_abs = error
                    worst_abs = {"state": step, "time_s": state["time"], "node_index": node,
                                 "component": component, "actual": actual, "expected": target}
                if target == 0.0:
                    if error > max_zero_abs:
                        max_zero_abs = error
                        worst_zero = {"state": step, "time_s": state["time"], "node_index": node,
                                      "component": component, "actual": actual}
                    if error > ZERO_STATE_ATOL:
                        errors.append(
                            f"{field_name} zero-state error at state={step}, node-index={node}, "
                            f"component={component}: {error:.6g} exceeds {ZERO_STATE_ATOL:.3g}"
                        )
                else:
                    relative = error / abs(target)
                    if relative > max_rel:
                        max_rel = relative
                        worst_rel = {"state": step, "time_s": state["time"], "node_index": node,
                                     "component": component, "actual": actual, "expected": target,
                                     "relative_error": relative}
                    if relative > STATE_RTOL:
                        errors.append(
                            f"{field_name} relative error at state={step}, node-index={node}, "
                            f"component={component}: {relative:.6g} exceeds {STATE_RTOL:.3g}"
                        )

    return ({
        "states": len(actual_states),
        "max_absolute_error": max_abs,
        "max_absolute_error_location": worst_abs,
        "max_relative_error_nonzero_expected": max_rel,
        "max_relative_error_location": worst_rel,
        "max_absolute_error_zero_expected": max_zero_abs,
        "max_zero_error_location": worst_zero,
        "relative_tolerance": STATE_RTOL,
        "zero_absolute_tolerance": ZERO_STATE_ATOL,
    }, errors)


def check_force_oracles(oracle: dict[str, Any], mass: list[list[float]], ramp: float,
                        coords: list[list[float]]) -> list[str]:
    errors: list[str] = []
    cases = oracle["load_cases"]
    mode_slopes = {
        "translation_x": [[ramp, 0.0, 0.0] for _ in coords[:4]],
        "rotation_y": [[coords[i][2] * ramp, 0.0, -coords[i][0] * ramp] for i in range(4)],
    }
    for case, accelerations in mode_slopes.items():
        computed = [[0.0, 0.0, 0.0] for _ in range(4)]
        for component in range(3):
            a = [row[component] for row in accelerations]
            for i, row in enumerate(mass):
                computed[i][component] = dot(row, a)
        provided = cases[case]["physical_force_vector_per_time_slope_N"]
        for node in range(4):
            for component in range(3):
                if not math.isclose(computed[node][component], float(provided[node][component]),
                                    rel_tol=1.0e-12, abs_tol=1.0e-18):
                    errors.append(
                        f"oracle {case} f=M*a mismatch at physical node {node}, component {component}: "
                        f"{provided[node][component]:.17g} vs {computed[node][component]:.17g} N/s"
                    )
    return errors


def run_check(history_path: Path, oracle_path: Path) -> dict[str, Any]:
    oracle = read_json(oracle_path)
    extracted = read_json(history_path)
    require(oracle.get("fixture") == "code-aster-17.4-weighted-constraint-known-answer-surrogate-v1",
            "unexpected oracle fixture identifier")

    geom = oracle["geometry"]
    physical = geom["physical_tetra_nodes_m"]
    carrier = geom["carrier_tetra_nodes_m"]
    coordinates = [physical[name] for name in ("P1", "P2", "P3", "P4")]
    coordinates += [carrier[name] for name in ("C1", "C2", "C3", "C4")]
    coordinates += [geom["reference_pivot_m"]]
    mass = oracle["physical_consistent_mass"]["scalar_nodal_matrix_kg"]
    require(len(mass) == 4 and all(len(row) == 4 for row in mass),
            "physical scalar consistent mass matrix must be 4x4")
    mass = [[finite_number(v, "consistent mass entry") for v in row] for row in mass]
    total_mass = sum(sum(row) for row in mass)
    require(math.isclose(total_mass, float(geom["physical_mass_kg"]), rel_tol=1.0e-12, abs_tol=1.0e-12),
            f"consistent mass matrix total {total_mass} kg does not match oracle physical mass")
    require(float(geom["carrier_density_kg_m3"]) == 0.0,
            "carrier density must be exactly zero for this fixture")

    load_cases = oracle["load_cases"]
    newmark = load_cases["newmark"]
    dt = finite_number(newmark["dt_s"], "Newmark dt")
    increments = int(newmark["increments"])
    beta = finite_number(newmark["beta"], "Newmark beta")
    gamma = finite_number(newmark["gamma"], "Newmark gamma")
    ramp = finite_number(load_cases["ramp_slope"], "ramp slope")
    require(increments == 100, f"expected 100 increments, oracle says {increments}")
    require(dt > 0.0 and 0.0 < beta <= 0.5 and 0.0 <= gamma <= 1.0,
            "invalid Newmark parameters in oracle")
    newmark_history = build_newmark_history(ramp, dt, increments, beta, gamma)
    # Guard against a stale/contradictory oracle while retaining an independently
    # computed state history for the actual comparison.
    terminal_q = newmark_history[-1][1]
    terminal_v = newmark_history[-1][2]
    terminal_a = newmark_history[-1][3]
    require(math.isclose(terminal_q, load_cases["translation_x"]["newmark_terminal_displacement_m"],
                         rel_tol=1.0e-12, abs_tol=1.0e-18),
            "discrete Newmark terminal displacement disagrees with oracle")
    require(math.isclose(terminal_v, load_cases["translation_x"]["terminal_velocity_m_s"],
                         rel_tol=1.0e-12, abs_tol=1.0e-18),
            "discrete Newmark terminal velocity disagrees with oracle")
    require(math.isclose(terminal_a, load_cases["translation_x"]["terminal_acceleration_m_s2"],
                         rel_tol=1.0e-12, abs_tol=1.0e-18),
            "discrete Newmark terminal acceleration disagrees with oracle")

    indexed, structural_errors = validate_and_index_history(
        extracted, coordinates, [state[0] for state in newmark_history]
    )
    errors = list(structural_errors)
    errors.extend(check_force_oracles(oracle, mass, ramp, coordinates))

    field_summaries: dict[str, Any] = {}
    energy_summaries: dict[str, Any] = {}
    for case, prefix in (("translation_x", "T"), ("rotation_y", "R")):
        expected_by_quantity: dict[str, list[list[list[float]]]] = {}
        for quantity, suffix in FIELD_SUFFIX.items():
            expected = [expected_field_values(case, quantity, state, coordinates)
                        for state in newmark_history]
            expected_by_quantity[quantity] = expected
            field_name = f"RESULT_{prefix}{suffix}"
            summary, field_errors = compare_field(indexed[field_name], expected, field_name)
            field_summaries[field_name] = summary
            errors.extend(field_errors)

        actual_velocity_states = indexed[f"RESULT_{prefix}VITE"]
        energy_max_rel = 0.0
        energy_max_abs = 0.0
        energy_zero_max_abs = 0.0
        worst_energy: dict[str, Any] | None = None
        for step, (actual_state, expected_state) in enumerate(
            zip(actual_velocity_states, expected_by_quantity["VITE"])
        ):
            component_index = {name: actual_state["components"].index(name) for name in COMPONENTS}
            actual_velocities = [
                [finite_number(actual_state["values"][node][component_index[component]],
                               f"{case} VITE state {step} node {node} {component}")
                 for component in VECTOR_COMPONENTS]
                for node in range(4)
            ]
            expected_velocities = [row[:3] for row in expected_state[:4]]
            actual_energy = kinetic_energy(actual_velocities, mass)
            expected_energy = kinetic_energy(expected_velocities, mass)
            energy_error = abs(actual_energy - expected_energy)
            if expected_energy == 0.0:
                energy_zero_max_abs = max(energy_zero_max_abs, energy_error)
                if energy_error > ZERO_ENERGY_ATOL_J:
                    errors.append(
                        f"{case} kinetic energy at zero-energy state {step}: {energy_error:.6g} J "
                        f"exceeds {ZERO_ENERGY_ATOL_J:.3g} J"
                    )
            else:
                relative = energy_error / abs(expected_energy)
                if relative > energy_max_rel:
                    energy_max_rel = relative
                    worst_energy = {"state": step, "time_s": actual_state["time"],
                                    "actual_J": actual_energy, "expected_J": expected_energy,
                                    "relative_error": relative}
                if relative > ENERGY_RTOL:
                    errors.append(
                        f"{case} kinetic energy relative error at state {step}: {relative:.6g} "
                        f"exceeds {ENERGY_RTOL:.3g}"
                    )
            energy_max_abs = max(energy_max_abs, energy_error)

        final_actual_state = actual_velocity_states[-1]
        final_components = {name: final_actual_state["components"].index(name)
                            for name in COMPONENTS}
        final_actual_velocities = [
            [final_actual_state["values"][node][final_components[component]]
             for component in VECTOR_COMPONENTS]
            for node in range(4)
        ]
        energy_summaries[case] = {
            "states": len(actual_velocity_states),
            "physical_mass_matrix_total_kg": total_mass,
            "max_absolute_energy_error_J": energy_max_abs,
            "max_relative_energy_error_nonzero_expected": energy_max_rel,
            "max_relative_error_location": worst_energy,
            "max_absolute_error_at_zero_energy_state_J": energy_zero_max_abs,
            "terminal_actual_J": kinetic_energy(final_actual_velocities, mass),
            "terminal_expected_J": kinetic_energy(
                [row[:3] for row in expected_by_quantity["VITE"][-1][:4]], mass
            ),
            "relative_tolerance": ENERGY_RTOL,
            "zero_absolute_tolerance_J": ZERO_ENERGY_ATOL_J,
        }

    rotation_shape = mode_velocity_shape("rotation_y", coordinates[:4])
    rotation_inertia = effective_mode_mass(rotation_shape, mass)
    oracle_inertia = float(oracle["physical_consistent_mass"]["rotation_y_mass_moment_kg_m2"])
    require(math.isclose(rotation_inertia, oracle_inertia, rel_tol=1.0e-12, abs_tol=1.0e-12),
            f"computed Y-rotation inertia {rotation_inertia} does not match oracle {oracle_inertia}")

    return {
        "fixture": oracle["fixture"],
        "status": "PASS" if not errors else "FAIL",
        "history": str(history_path),
        "oracle": str(oracle_path),
        "states_per_result": len(newmark_history),
        "load_oracle": {"mass_matrix_total_kg": total_mass,
                        "rotation_y_mass_moment_kg_m2": rotation_inertia,
                        "f_equals_m_a": not any("f=M*a mismatch" in error for error in errors)},
        "state_checks": field_summaries,
        "physical_kinetic_energy_checks": energy_summaries,
        "massless_carrier": {
            "density_kg_m3": float(geom["carrier_density_kg_m3"]),
            "carrier_kinetic_energy_J": 0.0,
            "basis": "RHO=0 in the fixture; carrier has no applied load or assigned mass",
        },
        "tolerances": {
            "relative_nonzero_state": STATE_RTOL,
            "absolute_zero_state": ZERO_STATE_ATOL,
            "relative_nonzero_energy": ENERGY_RTOL,
            "absolute_zero_energy_J": ZERO_ENERGY_ATOL_J,
            "coordinate_m": COORD_ATOL_M,
            "time_s": TIME_ATOL_S,
        },
        "errors": errors,
        "claim_limit": "primitive four-node surrogate only; this is not qualification of the A09 current-map equations or any joint",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("history", type=Path, help="parent-exported nodal-history.json")
    parser.add_argument(
        "--oracle", type=Path, default=Path(__file__).with_name("oracle.json"),
        help="fixture oracle JSON (default: beside this script)",
    )
    parser.add_argument("--report", type=Path, help="optional path for machine-readable report JSON")
    args = parser.parse_args()

    try:
        report = run_check(args.history, args.oracle)
    except CheckError as exc:
        report = {"status": "ERROR", "error": str(exc)}
    encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.report:
        args.report.write_text(encoded)
    else:
        sys.stdout.write(encoded)
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
