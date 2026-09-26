"""Audit the two frozen finite-actuator fixtures against independent dynamics."""

import hashlib
import json
import math
import re
from itertools import pairwise
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
NODES = {36162, 2, 117162, 117163}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(token, frd=False):
    value = float(token)
    mantissa, exponent = token.upper().split("E")
    quantum = 10.0 ** (int(exponent) - len(mantissa.split(".")[1]))
    bound = quantum / 2
    if frd:
        # CCX 2.21 frdvector.c casts double to float before %12.5E.
        # Bound both binary32 conversion and the subsequent decimal print.
        epsilon = 2.0**-24
        bound += (abs(value) + bound) * epsilon / (1 - epsilon)
    return value, bound


def dat_fields(path):
    text = path.read_text()
    heads = list(
        re.finditer(
            r"(displacements|forces) \([^\n]+\) for set OUTPUT_NODES and time\s+(\S+)",
            text,
        )
    )
    result = {}
    for i, head in enumerate(heads):
        rows = {}
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        for line in text[head.end() : end].splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                node = int(fields[0])
                assert node not in rows and node in NODES
                rows[node] = tuple(number(x) for x in fields[1:])
        assert rows.keys() == NODES
        key = (head.group(1), round(float(head.group(2)), 10))
        assert key not in result
        result[key] = rows
    return result


def frd_velocities(path):
    result = {}
    field = None
    time = None
    for line in path.read_text().splitlines():
        if line.startswith("  100CL"):
            time = round(float(line.split()[2]), 10)
        elif line.startswith(" -4"):
            field = line.split()[1]
            if field == "VELO":
                assert time not in result
                result[time] = {}
        elif line.startswith(" -1") and field == "VELO":
            node = int(line[3:13])
            assert node in NODES and node not in result[time]
            result[time][node] = tuple(
                number(line[13 + 12 * j : 25 + 12 * j].strip(), frd=True)
                for j in range(3)
            )
        elif line.startswith(" -3"):
            field = None
    assert all(rows.keys() == NODES for rows in result.values())
    return result


def continuous_state(t, oracle):
    """Exact piecewise-linear forcing solution, independent of Newmark."""
    stiffness = oracle["Kq_n_mm"] + oracle["actuator_K_n_mm"]
    omega = math.sqrt(stiffness / oracle["Mq_n_s2_mm"])
    gain = oracle["actuator_K_n_mm"] / stiffness
    q = v = 0.0
    knots = [(0.0, 0.0), (0.01, 0.0001), (0.02, 0.0003), (0.03, 0.0002)]
    for (start, target), (end, next_target) in pairwise(knots):
        if t <= start:
            break
        tau = min(t, end) - start
        slope = (next_target - target) / (end - start)
        c = q - gain * target
        d = (v - gain * slope) / omega
        q = (
            gain * (target + slope * tau)
            + c * math.cos(omega * tau)
            + d * math.sin(omega * tau)
        )
        v = (
            gain * slope
            - omega * c * math.sin(omega * tau)
            + omega * d * math.cos(omega * tau)
        )
        if t <= end:
            return q, v, oracle["actuator_K_n_mm"] * (target + slope * tau - q)
    return q, v, oracle["actuator_K_n_mm"] * (knots[-1][1] - q)


def check_print(observed, expected):
    value, rounding = observed
    assert abs(value - expected) <= rounding, (value, expected, rounding)
    return abs(value - expected)


def energy_bound(coefficient, value, bound):
    return abs(coefficient * value) * bound + 0.5 * abs(coefficient) * bound**2


def audit(folder):
    path = BASE / folder
    execution = json.loads((path / "execution.json").read_text())
    freeze = json.loads((path / "input-freeze.json").read_text())
    assert execution["returncode"] == 0
    assert sha(path / "input-freeze.json") == execution["input_freeze_sha256"]
    for mapping in (freeze["artifacts_sha256"], execution["outputs_sha256"]):
        for name, pin in mapping.items():
            assert sha(path / name) == pin, name
    oracle = json.loads((path / "oracle.json").read_text())
    pilot = (path / "pilot.inp").read_text()
    assert "*DYNAMIC,ALPHA=0,DIRECT\n" in pilot and "EXPLICIT" not in pilot
    assert "*MASS,ELSET=MASS_ONE\n0.001\n" in pilot
    assert "*MASS,ELSET=MASS_TWO\n0.002\n" in pilot
    assert "*SPRING,ELSET=JOINT_SPRING\n1,1\n1.0\n" in pilot
    assert "*SPRING,ELSET=ACTUATOR\n1,1\n100000.0\n" in pilot
    assert "*BOUNDARY,AMPLITUDE=Q_HISTORY\n117163,1,1,1\n" in pilot
    assert (
        f"117162,1,1,36162,1,{-1 / oracle['s']:.16f},2,1,{1 / oracle['s']:.16f}\n"
        in pilot
    )
    statuses = [
        line.split()
        for line in (path / "pilot.sta").read_text().splitlines()
        if line.split() and line.split()[0].isdigit()
    ]
    assert len(statuses) == len(oracle["trace"])
    for index, (status, expected) in enumerate(zip(statuses, oracle["trace"]), 1):
        assert status[:3] == ["1", str(index), "1"]
        assert math.isclose(float(status[4]), expected["time_s"], abs_tol=1e-10)
    dat = dat_fields(path / "pilot.dat")
    velocities = frd_velocities(path / "pilot.frd")
    assert len(dat) == 2 * len(oracle["trace"])
    assert len(velocities) == len(oracle["trace"])
    mass1, mass2 = oracle["mass1_n_s2_mm"], oracle["mass2_n_s2_mm"]
    ka, kq = oracle["actuator_K_n_mm"], oracle["Kq_n_mm"]
    previous_target = previous_force = previous_target_bound = previous_force_bound = (
        0.0
    )
    work = work_bound = 0.0
    previous_time = target_velocity = target_velocity_bound = 0.0
    rows = []
    for expected in oracle["trace"]:
        t = round(expected["time_s"], 10)
        u, force, velocity = dat["displacements", t], dat["forces", t], velocities[t]
        for node, key in [
            (36162, "u1_mm"),
            (2, "u2_mm"),
            (117162, "q_actual_mm"),
            (117163, "q_target_mm"),
        ]:
            check_print(u[node][0], expected[key])
        for node, key in [
            (36162, "v1_mm_s"),
            (2, "v2_mm_s"),
            (117162, "q_velocity_mm_s"),
        ]:
            check_print(velocity[node][0], expected[key])
        check_print(force[117163][0], expected["controller_applied_force_n"])
        check_print(force[117162][0], -expected["controller_applied_force_n"])
        target, target_bound = u[117163][0]
        applied, applied_bound = force[117163][0]
        q, q_bound = u[117162][0]
        v1, v1_bound = velocity[36162][0]
        v2, v2_bound = velocity[2][0]
        momentum = mass1 * v1 + mass2 * v2
        momentum_bound = mass1 * v1_bound + mass2 * v2_bound
        assert abs(momentum) <= momentum_bound
        delta_target = target - previous_target
        dt = t - previous_time
        # Prescribed displacement uses the Newmark velocity recurrence, not
        # the analytical segment slope. Propagate DAT displacement precision.
        target_velocity = 2 * delta_target / dt - target_velocity
        target_velocity_bound += 2 * (target_bound + previous_target_bound) / dt
        reported_target_velocity, reported_target_velocity_bound = velocity[117163][0]
        assert abs(reported_target_velocity - target_velocity) <= (
            target_velocity_bound + reported_target_velocity_bound
        )
        mean_force = 0.5 * (applied + previous_force)
        force_bound = 0.5 * (applied_bound + previous_force_bound)
        delta_bound = target_bound + previous_target_bound
        work += mean_force * delta_target
        work_bound += (
            abs(delta_target) * force_bound
            + abs(mean_force) * delta_bound
            + force_bound * delta_bound
        )
        gap = target - q
        total_energy = (
            0.5 * kq * q * q
            + 0.5 * ka * gap * gap
            + 0.5 * mass1 * v1 * v1
            + 0.5 * mass2 * v2 * v2
        )
        total_energy_bound = sum(
            [
                energy_bound(kq, q, q_bound),
                energy_bound(ka, gap, target_bound + q_bound),
                energy_bound(mass1, v1, v1_bound),
                energy_bound(mass2, v2, v2_bound),
            ]
        )
        residual = work - total_energy
        assert abs(residual) <= work_bound + total_energy_bound
        exact_q, exact_v, exact_force = continuous_state(t, oracle)
        rows.append(
            {
                "time_s": t,
                "actual_q_mm": q,
                "controller_force_n": applied,
                "target_velocity_mm_s": reported_target_velocity,
                "target_velocity_from_displacement_recurrence_mm_s": target_velocity,
                "target_velocity_recurrence_print_bound_mm_s": target_velocity_bound
                + reported_target_velocity_bound,
                "momentum_ns": momentum,
                "momentum_rounding_bound_ns": momentum_bound,
                "controller_work_nmm": work,
                "reconstructed_total_energy_nmm": total_energy,
                "work_energy_residual_nmm": residual,
                "combined_work_energy_print_bound_nmm": work_bound + total_energy_bound,
                "exact_continuous_q_mm": exact_q,
                "exact_continuous_q_velocity_mm_s": exact_v,
                "exact_continuous_controller_force_n": exact_force,
                "q_continuous_error_mm": q - exact_q,
                "controller_force_continuous_error_n": applied - exact_force,
            }
        )
        previous_target, previous_force = target, applied
        previous_time = t
        previous_target_bound, previous_force_bound = target_bound, applied_bound
    return {
        "case": folder,
        "execution_sha256": sha(path / "execution.json"),
        "oracle_sha256": sha(path / "oracle.json"),
        "accepted_state_count": len(rows),
        "native_U_V_and_controller_RF_match_discrete_oracle_with_print_precision": True,
        "velocity_oracle_scope": "Physical nodes 36162/2 and proxy 117162; prescribed target 117163 separately checked against Newmark displacement recurrence with propagated output precision, not the continuous ramp slope.",
        "target_velocity_recurrence_checked": True,
        "all_momentum_and_reconstructed_work_energy_checks_within_print_bounds": True,
        "max_q_error_vs_continuous_mm": max(
            abs(r["q_continuous_error_mm"]) for r in rows
        ),
        "q_error_over_continuous_infinity_norm": max(
            abs(r["q_continuous_error_mm"]) for r in rows
        )
        / max(abs(r["exact_continuous_q_mm"]) for r in rows),
        "max_controller_force_error_vs_continuous_n": max(
            abs(r["controller_force_continuous_error_n"]) for r in rows
        ),
        "force_error_over_continuous_infinity_norm": max(
            abs(r["controller_force_continuous_error_n"]) for r in rows
        )
        / max(abs(r["exact_continuous_controller_force_n"]) for r in rows),
        "rows": rows,
    }


if __name__ == "__main__":
    result = {
        "scope": "Two-mass finite-actuator implementation and timestep check only; no current-joint or structural acceptance",
        "implementation_sha256": sha(Path(__file__)),
        "frd_precision_source": {
            "source_archive_sha256": "52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad",
            "frdvector_c_sha256": "2dabcb51ae3cbad1bb43353b6db0f9fc36a72f4b30dc9173d872b0c4bff2001c",
            "meaning": "CCX 2.21 casts vector values to float before %12.5E; FRD bounds include binary32 conversion and decimal printing. DAT bounds use decimal printing only.",
        },
        "cases": [
            audit(f"prescribed-q-native-spring-actuator-attempt{i:02}") for i in (3, 4)
        ],
    }
    (HERE / "report.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            [{k: v for k, v in c.items() if k != "rows"} for c in result["cases"]],
            indent=2,
        )
    )
