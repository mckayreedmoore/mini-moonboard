#!/usr/bin/env python3
"""Audit every extracted native nodal state against the analytic impact oracle.

Input is the JSON emitted by fea/code_aster_trial/extract_nodal_med.py. This
script never invokes Code_Aster. It hard-checks data coverage and reports
numerical errors/invariants without applying an unreviewed acceptance limit.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import oracle


TIME_TOLERANCE = 2.0e-10


def field_history(data: dict[str, Any], suffix: str) -> tuple[str, list[dict[str, Any]]]:
    matches = [(name, states) for name, states in data.get('fields', {}).items()
               if name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f'expected one nodal field ending in {suffix}; found {[n for n, _ in matches]}')
    return matches[0]


def component_index(state: dict[str, Any], name: str) -> int:
    components = state.get('components', [])
    if name not in components:
        raise ValueError(f'component {name} missing; found {components}')
    return components.index(name)


def node_index(coordinates: list[list[float]], x: float) -> int:
    matches = [i for i, xyz in enumerate(coordinates)
               if len(xyz) >= 3 and math.isclose(float(xyz[0]), x, abs_tol=1e-12, rel_tol=0.0)
               and math.isclose(float(xyz[1]), 0.0, abs_tol=1e-12, rel_tol=0.0)
               and math.isclose(float(xyz[2]), 0.0, abs_tol=1e-12, rel_tol=0.0)]
    if len(matches) != 1:
        raise ValueError(f'expected one mesh node at ({x},0,0); found indices {matches}')
    return matches[0]


def finite_number(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f'non-finite {label}: {value}')
    return number


def compare(case_name: str, source: Path) -> dict[str, Any]:
    if case_name not in {'coarse', 'fine'}:
        raise ValueError('case must be coarse or fine')
    data = json.loads(source.read_text())
    coordinates = data.get('coordinates')
    if not isinstance(coordinates, list):
        raise ValueError('extractor JSON lacks coordinate array')
    i1 = node_index(coordinates, oracle.X1_0)
    i2 = node_index(coordinates, oracle.X2_0)
    depl_name, depl_states = field_history(data, 'DEPL')
    vite_name, vite_states = field_history(data, 'VITE')

    expected_states = oracle.payload()['cases'][case_name]['states']
    if len(depl_states) != len(expected_states) or len(vite_states) != len(expected_states):
        raise ValueError(
            f'{case_name} all-state count mismatch: expected {len(expected_states)}, '
            f'{depl_name}={len(depl_states)}, {vite_name}={len(vite_states)}'
        )

    maximum = {
        'x1_error_mm': {'absolute': -1.0, 'time_s': None},
        'x2_error_mm': {'absolute': -1.0, 'time_s': None},
        'v1_error_mm_s': {'absolute': -1.0, 'time_s': None},
        'v2_error_mm_s': {'absolute': -1.0, 'time_s': None},
        'gap_error_mm': {'absolute': -1.0, 'time_s': None},
        'normal_force_from_gap_error_N': {'absolute': -1.0, 'time_s': None},
        'momentum_error_tonne_mm_s': {'absolute': -1.0, 'time_s': None},
        'total_energy_error_N_mm': {'absolute': -1.0, 'time_s': None},
    }
    max_momentum_drift = 0.0
    max_energy_drift = 0.0
    records: list[dict[str, Any]] = []

    for index, expected in enumerate(expected_states):
        dstate = depl_states[index]
        vstate = vite_states[index]
        time = finite_number(dstate.get('time'), f'{depl_name} time[{index}]')
        vtime = finite_number(vstate.get('time'), f'{vite_name} time[{index}]')
        etime = expected['time_s']
        if abs(time - etime) > TIME_TOLERANCE or abs(vtime - etime) > TIME_TOLERANCE:
            raise ValueError(
                f'{case_name} state {index} time mismatch: DEPL={time:.12g}, '
                f'VITE={vtime:.12g}, expected={etime:.12g}'
            )
        if abs(time - vtime) > TIME_TOLERANCE:
            raise ValueError(f'{case_name} DEPL/VITE state times differ at state {index}')

        dx = component_index(dstate, 'DX')
        vx = component_index(vstate, 'DX')
        dvalues = dstate.get('values', [])
        vvalues = vstate.get('values', [])
        if len(dvalues) != len(coordinates) or len(vvalues) != len(coordinates):
            raise ValueError(f'{case_name} field node count differs from mesh at state {index}')
        u1 = finite_number(dvalues[i1][dx], f'{depl_name} N1 DX[{index}]')
        u2 = finite_number(dvalues[i2][dx], f'{depl_name} N2 DX[{index}]')
        v1 = finite_number(vvalues[i1][vx], f'{vite_name} N1 DX[{index}]')
        v2 = finite_number(vvalues[i2][vx], f'{vite_name} N2 DX[{index}]')
        x1 = oracle.X1_0 + u1
        x2 = oracle.X2_0 + u2
        gap = x2 - x1 - oracle.R_SUM
        penetration = max(0.0, -gap)
        force = oracle.KN * penetration
        momentum = oracle.M1 * v1 + oracle.M2 * v2
        kinetic = 0.5 * oracle.M1 * v1**2 + 0.5 * oracle.M2 * v2**2
        contact_energy = 0.5 * oracle.KN * penetration**2
        total_energy = kinetic + contact_energy
        calculated = {
            'x1_mm': x1,
            'x2_mm': x2,
            'v1_mm_s': v1,
            'v2_mm_s': v2,
            'gap_mm': gap,
            'normal_force_from_gap_N': force,
            'momentum_tonne_mm_s': momentum,
            'kinetic_energy_N_mm': kinetic,
            'penalty_energy_N_mm': contact_energy,
            'total_mechanical_energy_N_mm': total_energy,
        }
        error_sources = {
            'x1_error_mm': abs(x1 - expected['x1_mm']),
            'x2_error_mm': abs(x2 - expected['x2_mm']),
            'v1_error_mm_s': abs(v1 - expected['v1_mm_s']),
            'v2_error_mm_s': abs(v2 - expected['v2_mm_s']),
            'gap_error_mm': abs(gap - expected['gap_mm']),
            'normal_force_from_gap_error_N': abs(force - expected['normal_force_N']),
            'momentum_error_tonne_mm_s': abs(momentum - oracle.INITIAL_MOMENTUM),
            'total_energy_error_N_mm': abs(total_energy - oracle.INITIAL_ENERGY),
        }
        for key, error in error_sources.items():
            if error > maximum[key]['absolute']:
                maximum[key] = {'absolute': error, 'time_s': time}
        max_momentum_drift = max(max_momentum_drift, error_sources['momentum_error_tonne_mm_s'])
        max_energy_drift = max(max_energy_drift, error_sources['total_energy_error_N_mm'])
        records.append({
            'time_s': time,
            'phase': expected['phase'],
            'calculated': calculated,
            'analytic': expected,
            'absolute_errors': error_sources,
        })

    return {
        'status': 'REVIEW_REQUIRED_NO_NUMERICAL_ACCEPTANCE_LIMIT_APPLIED',
        'case': case_name,
        'source_json': str(source),
        'mesh': data.get('mesh'),
        'node_indices': {'N1': i1, 'N2': i2},
        'fields': {'displacement': depl_name, 'velocity': vite_name},
        'state_count': len(records),
        'time_tolerance_s': TIME_TOLERANCE,
        'maximum_absolute_errors': maximum,
        'maximum_momentum_drift_tonne_mm_s': max_momentum_drift,
        'maximum_total_energy_drift_N_mm': max_energy_drift,
        'contact_force_note': (
            'Computed from extracted signed gap and the specified penalty stiffness; '
            'this is not an extraction of native SIEF_ELGA.'
        ),
        'states': records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=('coarse', 'fine'))
    parser.add_argument('nodal_history', type=Path,
                        help='JSON from extract_nodal_med.py for this case MED')
    parser.add_argument('--output', type=Path,
                        help='optional report JSON path; defaults to stdout')
    args = parser.parse_args()
    report = compare(args.case, args.nodal_history)
    content = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(content)
        print(f'Wrote all-state comparison: {args.output}')
    else:
        print(content, end='')


if __name__ == '__main__':
    main()
