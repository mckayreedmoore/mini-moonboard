#!/usr/bin/env python3
"""Independent closed-form point-impact reference; no solver imports or calls."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent

# Deliberately restated here rather than imported from generate.py. The audit
# compares the deck values to these independent mechanics inputs.
M1 = 1.0  # tonne
M2 = 2.0  # tonne
X1_0 = 0.0  # mm
X2_0 = 2.0  # mm
R1 = 0.5  # mm
R2 = 0.5  # mm
V1_0 = 10.0  # mm/s
V2_0 = 0.0  # mm/s
T_CONTACT = 0.10  # s
CONTACT_DURATION = 0.08  # s
DT_COARSE = 0.0025  # s
DT_FINE = 0.00125  # s
T_END = 0.24  # s

TOTAL_MASS = M1 + M2
REDUCED_MASS = M1 * M2 / TOTAL_MASS
INITIAL_MOMENTUM = M1 * V1_0 + M2 * V2_0
INITIAL_ENERGY = 0.5 * M1 * V1_0**2 + 0.5 * M2 * V2_0**2
OMEGA = math.pi / CONTACT_DURATION
KN = REDUCED_MASS * OMEGA**2
V_COM = INITIAL_MOMENTUM / TOTAL_MASS
T_RELEASE = T_CONTACT + CONTACT_DURATION
V1_POST = V_COM - M2 / TOTAL_MASS * V1_0
V2_POST = V_COM + M1 / TOTAL_MASS * V1_0
R_SUM = R1 + R2
GAP_0 = X2_0 - X1_0 - R_SUM


def state_at(time: float) -> dict[str, float | str]:
    """Return exact elastic unilateral spring-impact state at ``time``."""
    eps = 1.0e-12
    if time < T_CONTACT - eps:
        x1 = X1_0 + V1_0 * time
        x2 = X2_0 + V2_0 * time
        v1, v2 = V1_0, V2_0
        phase = 'approach'
    elif abs(time - T_CONTACT) <= eps:
        x1 = X1_0 + V1_0 * T_CONTACT
        x2 = X2_0 + V2_0 * T_CONTACT
        v1, v2 = V1_0, V2_0
        phase = 'first_touch'
    elif time < T_RELEASE - eps:
        tau = time - T_CONTACT
        delta = V1_0 / OMEGA * math.sin(OMEGA * tau)
        rel_v = V1_0 * math.cos(OMEGA * tau)
        x1_touch = X1_0 + V1_0 * T_CONTACT
        x2_touch = X2_0 + V2_0 * T_CONTACT
        x1 = x1_touch + V_COM * tau + M2 / TOTAL_MASS * delta
        x2 = x2_touch + V_COM * tau - M1 / TOTAL_MASS * delta
        v1 = V_COM + M2 / TOTAL_MASS * rel_v
        v2 = V_COM - M1 / TOTAL_MASS * rel_v
        phase = 'compression' if tau <= CONTACT_DURATION / 2.0 else 'restitution'
    else:
        x1_touch = X1_0 + V1_0 * T_CONTACT
        x2_touch = X2_0 + V2_0 * T_CONTACT
        x1_release = x1_touch + V_COM * CONTACT_DURATION
        x2_release = x2_touch + V_COM * CONTACT_DURATION
        x1 = x1_release + V1_POST * (time - T_RELEASE)
        x2 = x2_release + V2_POST * (time - T_RELEASE)
        v1, v2 = V1_POST, V2_POST
        phase = 'separation'

    gap = x2 - x1 - R_SUM
    penetration = max(0.0, -gap)
    force = KN * penetration
    kinetic = 0.5 * M1 * v1**2 + 0.5 * M2 * v2**2
    penalty_energy = 0.5 * KN * penetration**2
    momentum = M1 * v1 + M2 * v2
    return {
        'time_s': time,
        'phase': phase,
        'x1_mm': x1,
        'x2_mm': x2,
        'v1_mm_s': v1,
        'v2_mm_s': v2,
        'gap_mm': gap,
        'penetration_mm': penetration,
        'normal_force_N': force,
        'momentum_tonne_mm_s': momentum,
        'kinetic_energy_N_mm': kinetic,
        'penalty_energy_N_mm': penalty_energy,
        'total_mechanical_energy_N_mm': kinetic + penalty_energy,
    }


def times_for_step(step: float) -> list[float]:
    count = round(T_END / step)
    if not math.isclose(count * step, T_END, rel_tol=0.0, abs_tol=1.0e-14):
        raise ValueError('time step must divide the final time')
    return [round(index * step, 12) for index in range(count + 1)]


def payload() -> dict:
    return {
        'status': 'ANALYTIC_REFERENCE_ONLY_NOT_A_SOLVER_RESULT',
        'model': {
            'units': 'mm, tonne, s, N; 1 tonne*mm/s^2 = 1 N',
            'masses_tonne': [M1, M2],
            'initial_centers_mm': [X1_0, X2_0],
            'contact_reach_mm': [R1, R2],
            'initial_center_gap_mm': GAP_0,
            'initial_velocities_mm_s': [V1_0, V2_0],
            'first_touch_s': T_CONTACT,
            'reduced_mass_tonne': REDUCED_MASS,
            'contact_duration_s': CONTACT_DURATION,
            'angular_frequency_rad_s': OMEGA,
            'normal_penalty_stiffness_N_mm': KN,
            'contact_law': 'undamped unilateral linear normal spring; no tangential force',
            'post_impact_velocities_mm_s': [V1_POST, V2_POST],
            'initial_momentum_tonne_mm_s': INITIAL_MOMENTUM,
            'initial_kinetic_energy_N_mm': INITIAL_ENERGY,
        },
        'cases': {
            'coarse': {
                'dt_s': DT_COARSE,
                'time_step_count': len(times_for_step(DT_COARSE)) - 1,
                'states': [state_at(time) for time in times_for_step(DT_COARSE)],
            },
            'fine': {
                'dt_s': DT_FINE,
                'time_step_count': len(times_for_step(DT_FINE)) - 1,
                'states': [state_at(time) for time in times_for_step(DT_FINE)],
            },
        },
        'key_states': [state_at(time) for time in (
            0.0, 0.05, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.24,
        )],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--write', action='store_true', help='write oracle.json (default)')
    group.add_argument('--check', action='store_true', help='check oracle invariants and checked-in JSON')
    args = parser.parse_args()
    expected = json.dumps(payload(), indent=2, sort_keys=True) + '\n'
    output = ROOT / 'oracle.json'
    if args.check:
        if not output.exists() or output.read_text() != expected:
            raise SystemExit('oracle.json does not match oracle.py')
        print('PASS: oracle JSON matches the closed-form generator')
        return
    output.write_text(expected)
    print(f'Wrote {output}')


if __name__ == '__main__':
    main()
