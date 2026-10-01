#!/usr/bin/env python3
"""Scalar proposal reference only; this neither generates nor runs a native deck."""

import argparse
import json
import math
from pathlib import Path


def reference():
    mass, stiffness, dt, count = 1.0, 400000.0, 0.0001, 70
    initial_velocity = -0.1
    omega = math.sqrt(stiffness / mass)
    phase = 2 * math.atan(omega * dt / 2)
    release_time = math.pi / omega
    initial_energy = 0.5 * mass * initial_velocity**2
    displacement, velocity, acceleration = 0.0, initial_velocity, 0.0
    states = []
    for increment in range(1, count + 1):
        predictor = displacement + dt * velocity + dt**2 * acceleration / 4
        following = predictor / (1 + dt**2 * stiffness / (4 * mass)) if predictor < 0 else predictor
        next_acceleration = -stiffness * min(following, 0) / mass
        next_velocity = velocity + dt * (acceleration + next_acceleration) / 2
        kinetic = 0.5 * mass * next_velocity**2
        contact = 0.5 * stiffness * min(following, 0)**2
        before = 0.5 * mass * velocity**2 + 0.5 * stiffness * min(displacement, 0)**2
        jump = -0.5 * stiffness * displacement * following if displacement < 0 <= following else 0.0
        assert abs(kinetic + contact - before - jump) < 1e-16
        if following < 0:
            assert abs(following - initial_velocity / omega * math.sin(increment * phase)) < 1e-16
            assert abs(next_velocity - initial_velocity * math.cos(increment * phase)) < 1e-14
        time = increment * dt
        continuous_u = initial_velocity / omega * math.sin(omega * time) if time <= release_time else -initial_velocity * (time - release_time)
        continuous_v = initial_velocity * math.cos(omega * time) if time <= release_time else -initial_velocity
        states.append({
            "increment": increment, "time_s": time,
            "displacement_mm": following, "velocity_mm_s": next_velocity,
            "acceleration_mm_s2": next_acceleration,
            "kinetic_energy_Nmm": kinetic, "contact_energy_Nmm": contact,
            "total_energy_Nmm": kinetic + contact,
            "switch_energy_increase_Nmm": jump,
            "continuous_displacement_mm": continuous_u,
            "continuous_velocity_mm_s": continuous_v,
        })
        displacement, velocity, acceleration = following, next_velocity, next_acceleration
    return {
        "schema": "proposed_scalar_free_contact_reference/v1",
        "status": "ANALYTICAL_DESIGN_REFERENCE_ONLY",
        "native_execution": False, "joint_acceptance": False,
        "mass_tonne": mass, "spring_stiffness_N_mm": stiffness,
        "initial_velocity_mm_s": initial_velocity, "initial_energy_Nmm": initial_energy,
        "time_increment_s": dt, "increments": count,
        "omega_rad_s": omega, "continuous_release_time_s": release_time,
        "recurrence": "Newmark beta=1/4, gamma=1/2; m*a=-k*min(u,0); zero external force",
        "release_energy_identity": "H_next-H_old = -k*u_old*u_next/2 when u_old<0<=u_next",
        "max_relative_energy_change": max(abs(s["total_energy_Nmm"] - initial_energy) for s in states) / initial_energy,
        "limits": "Proposed scalar unilateral law only. Native geometry, initialization, contact law, output and method applicability must be reviewed and frozen separately.",
        "states": states,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = reference()
    path = Path(__file__).with_suffix(".json")
    rendered = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if args.write:
        with path.open("x") as stream:
            stream.write(rendered)
    else:
        assert path.read_text() == rendered
    print(json.dumps({"status": "PASS_SCALAR_REFERENCE", "states": len(data["states"]),
                      "max_relative_energy_change": data["max_relative_energy_change"]}))
