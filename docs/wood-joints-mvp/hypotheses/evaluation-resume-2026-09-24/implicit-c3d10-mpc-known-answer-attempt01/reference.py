#!/usr/bin/env python3
"""Generate the closed-form/Newmark reference contract for this tiny fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DT_S = 0.001
PERIOD_S = 0.1
STEPS = 100
RHO_TONNE_PER_MM3 = 6.0
VOLUME_MM3 = 1.0 / 6.0
MASS_TONNE = RHO_TONNE_PER_MM3 * VOLUME_MM3
BETA = 0.25
GAMMA = 0.5


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def contract() -> dict:
    nodes = {
        "physical": list(range(1, 11)),
        "controller": [11],
    }
    loads = {str(node): -RHO_TONNE_PER_MM3 * VOLUME_MM3 / 20.0 for node in range(1, 5)}
    loads.update(
        {str(node): RHO_TONNE_PER_MM3 * VOLUME_MM3 / 5.0 for node in range(5, 11)}
    )

    states = []
    u = v = a_previous = 0.0
    for increment in range(1, STEPS + 1):
        time_s = increment * DT_S
        acceleration_mm_s2 = time_s
        u_next = u + DT_S * v + DT_S**2 * (
            (0.5 - BETA) * a_previous + BETA * acceleration_mm_s2
        )
        v_next = v + DT_S * (
            (1.0 - GAMMA) * a_previous + GAMMA * acceleration_mm_s2
        )
        u_closed = time_s**3 / 6.0 + time_s * DT_S**2 / 12.0
        v_closed = time_s**2 / 2.0
        if abs(u_next - u_closed) > 1e-16 or abs(v_next - v_closed) > 1e-16:
            raise AssertionError("Newmark recurrence disagrees with its derived closed form")

        states.append(
            {
                "increment": increment,
                "time_s": time_s,
                "amplitude": time_s,
                "acceleration_mm_s2": acceleration_mm_s2,
                "u1_mm": u_next,
                "v1_mm_per_s": v_next,
                "ELSE_Nmm": 0.0,
                "ELKE_Nmm": 0.5 * MASS_TONNE * v_next**2,
                "EMAS_tonne": MASS_TONNE,
                "EVOL_mm3": VOLUME_MM3,
            }
        )
        u, v, a_previous = u_next, v_next, acceleration_mm_s2

    input_paths = {
        "direct": HERE / "input/direct.inp",
        "mapped": HERE / "input/mapped.inp",
    }
    return {
        "schema": "implicit_c3d10_mpc_known_answer_expected/v1",
        "scope": {
            "method_fixture_only": True,
            "native_execution_authorized_by_this_packet": False,
            "current_joint_acceptance": False,
            "structural_criterion_acceptance": False,
            "physical_demand_history": False,
        },
        "case_order": ["direct", "mapped"],
        "inputs": {
            case: {
                "path": str(path.relative_to(HERE)),
                "sha256": sha256(path),
                "physical_node_ids": nodes["physical"],
                "controller_node_ids": nodes["controller"] if case == "mapped" else [],
            }
            for case, path in input_paths.items()
        },
        "mesh": {
            "type": "one straight-sided C3D10 tetrahedron",
            "coordinates_mm": [
                [1, 0.0, 0.0, 0.0],
                [2, 1.0, 0.0, 0.0],
                [3, 0.0, 1.0, 0.0],
                [4, 0.0, 0.0, 1.0],
                [5, 0.5, 0.0, 0.0],
                [6, 0.5, 0.5, 0.0],
                [7, 0.0, 0.5, 0.0],
                [8, 0.0, 0.0, 0.5],
                [9, 0.5, 0.0, 0.5],
                [10, 0.0, 0.5, 0.5],
            ],
            "connectivity": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "volume_mm3": VOLUME_MM3,
        },
        "material": {
            "E_N_per_mm2": 1.0,
            "nu": 0.0,
            "density_tonne_per_mm3": RHO_TONNE_PER_MM3,
            "body_mass_tonne": MASS_TONNE,
        },
        "coordinate_maps": {
            "direct": "physical node U1(1..10) are independent; U2=U3=0",
            "mapped": {
                "equation": "U1(1)+U1(2)+U1(3)+U1(4)-4*U1(11)=0",
                "dependent_dof": [1, 1],
                "free_controller_dof": [11, 1],
                "physical_dofs_preserved": "all ten physical U1 coordinates remain represented; only node 1 U1 is eliminated in favor of free q11",
            },
        },
        "load_contract": {
            "reference_acceleration_mm_per_s2": 1.0,
            "amplitude_table_step_time": [[0.0, 0.0], [PERIOD_S, PERIOD_S]],
            "interpolation": "linear",
            "base_CLOAD_N_by_node": loads,
            "base_CLOAD_sum_N": sum(loads.values()),
            "expected_physical_load_at_period_N": {
                node: loads[str(node)] * PERIOD_S for node in range(1, 11)
            },
            "expected_total_load_at_period_N": PERIOD_S,
            "load_vector_is_consistent_mass_times_rigid_acceleration": True,
        },
        "integration": {
            "procedure": "*DYNAMIC,DIRECT,ALPHA=0",
            "time_increment_s": DT_S,
            "period_s": PERIOD_S,
            "increments": STEPS,
            "newmark_beta": BETA,
            "newmark_gamma": GAMMA,
            "initial_u_mm": 0.0,
            "initial_v_mm_per_s": 0.0,
            "initial_acceleration_mm_per_s2": 0.0,
            "target_acceleration_numeric_in_seconds": "a(t)=t_s mm/s^2",
            "discrete_displacement_mm": "t_s^3/6 + t_s*dt_s^2/12",
            "discrete_velocity_mm_per_s": "t_s^2/2",
            "elastic_energy_Nmm": 0.0,
            "kinetic_energy_Nmm": "0.125*t_s^4",
            "rf_is_excluded_from_inertia_oracle": True,
        },
        "outputs": {
            "node_fields": ["U", "V"],
            "element_totals": ["ELSE", "ELKE", "EMAS", "EVOL"],
            "frequency": 1,
            "mapped_controller_matches_physical_translation": True,
        },
        "comparison_tolerances": {
            "status": "not selected; parent/reviewer must set before any native run",
        },
        "states": states,
        "pinned_sources": {
            "source_archive_sha256": "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7",
            "source_files": {
                "nonlingeo.c": {
                    "sha256": "8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f",
                    "line_refs": "904-906",
                },
                "tempload.f": {
                    "sha256": "8933ca0a5bb9fa3db2b55b4ec9344be9dca1297763f5ea28f6ef7c9074ea84aa",
                    "line_refs": "76-108",
                },
                "e_c3d.f": {
                    "sha256": "d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc",
                    "line_refs": "986-1005",
                },
            },
            "manual_pdf_sha256": "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330",
            "manual_html_pages": {
                "node180.html": "b4766a18f82f1ed1d5aa9846366626476fa81c1d6104869aa415b16d3399140c",
                "node273.html": "c36c738d851edf257e10a428e9fffe8d8a01166536311dadb5fa07ae7d4a73b8",
                "node224.html": "d724412f39e26babeeb95083672ec3d61df8d6b241c66a356fe8a40f61480f2f",
            },
        },
    }


def render() -> bytes:
    return (json.dumps(contract(), indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="write expected.json")
    action.add_argument("--check", action="store_true", help="verify expected.json bytes")
    args = parser.parse_args()
    target = HERE / "expected.json"
    data = render()
    if args.write:
        target.write_bytes(data)
        print(f"WROTE {target.name} sha256={hashlib.sha256(data).hexdigest()}")
        return 0
    if target.read_bytes() != data:
        raise SystemExit("FAIL expected.json differs from reference.py output")
    print(f"PASS reference contract; states={STEPS}; terminal_time_s={PERIOD_S}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
