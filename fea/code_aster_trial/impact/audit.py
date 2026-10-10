#!/usr/bin/env python3
"""Offline design audit for the checked-in impact inputs and oracle.

This audit checks fixture arithmetic and text-input consistency only. It does
not invoke, syntax-check, or certify a Code_Aster execution.
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import generate
import oracle


ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_node_x(mesh: str, node: str) -> float:
    match = re.search(rf'(?m)^{re.escape(node)}\s+([-+0-9.eE]+)\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s*$', mesh)
    require(match is not None, f'missing mesh coordinate for {node}')
    return float(match.group(1))


def numeric_parameter(comm: str, name: str) -> float:
    match = re.search(rf'\b{name}\s*=\s*([-+0-9.eE]+)', comm)
    require(match is not None, f'missing {name} in command file')
    return float(match.group(1))


def main() -> None:
    generated = generate.expected_files()
    for path, expected in generated.items():
        require(path.exists(), f'missing generated input {path.relative_to(ROOT)}')
        require(path.read_text() == expected, f'generated input mismatch {path.relative_to(ROOT)}')

    mesh = (ROOT / 'coarse' / 'impact.mail').read_text()
    require(parse_node_x(mesh, 'N1') == oracle.X1_0, 'N1 x coordinate differs from oracle')
    require(parse_node_x(mesh, 'N2') == oracle.X2_0, 'N2 x coordinate differs from oracle')
    require('MASS1 M1' in mesh and 'MASS2 M2' in mesh and 'HITPAIR HIT1' in mesh,
            'mesh element groups do not match mass/contact roles')
    require('HIT1 N1 N2' in mesh, 'contact segment must run from N1 to N2')

    for case_name, (step, med_name) in generate.CASES.items():
        case_dir = ROOT / case_name
        comm = (case_dir / 'impact.comm').read_text()
        export = (case_dir / 'impact.export').read_text()
        require(math.isclose(numeric_parameter(comm, 'RIGI_NOR'), oracle.KN, rel_tol=2e-15),
                f'{case_name} normal stiffness differs from oracle')
        require(numeric_parameter(comm, 'DIST_1') == oracle.R1, f'{case_name} DIST_1 mismatch')
        require(numeric_parameter(comm, 'DIST_2') == oracle.R2, f'{case_name} DIST_2 mismatch')
        require(f'VALE={oracle.M1:g}' in comm and f'VALE={oracle.M2:g}' in comm,
                f'{case_name} point masses differ from oracle')
        require(f'PAS={step:.10g}' in comm, f'{case_name} time step mismatch')
        require("COULOMB=0.0" in comm and "RELATION='DIS_CHOC'" in comm,
                f'{case_name} is not the frictionless DIS_CHOC formulation')
        require("SCHEMA='NEWMARK'" in comm and 'BETA=0.25' in comm and 'GAMMA=0.5' in comm,
                f'{case_name} is not average-acceleration Newmark')
        require("DEBUT();" in comm and "DEBUT(PAR_LOT" not in comm,
                f'{case_name} must use the stock v17 default DEBUT form')
        require('RESI_GLOB_MAXI=1.0e-9' in comm and 'RESI_GLOB_RELA' not in comm,
                f'{case_name} must use the absolute residual tolerance')
        require('DEFI_CONTACT' not in comm and not re.search(r'(?m)^\s*CONTACT\s*=', comm),
                f'{case_name} unexpectedly includes continuous surface contact')
        require(f'F rmed {med_name} R 80' in export, f'{case_name} MED export name mismatch')
        require('/' not in '\n'.join(line for line in export.splitlines() if line.startswith('F ')),
                f'{case_name} export file paths must remain relative')

        case_states = oracle.payload()['cases'][case_name]['states']
        expected_count = round(oracle.T_END / step) + 1
        require(len(case_states) == expected_count, f'{case_name} oracle state count mismatch')
        require(math.isclose(case_states[0]['time_s'], 0.0), f'{case_name} misses initial state')
        require(math.isclose(case_states[-1]['time_s'], oracle.T_END), f'{case_name} misses final state')
        for event in (oracle.T_CONTACT, oracle.T_CONTACT + oracle.CONTACT_DURATION / 2,
                      oracle.T_RELEASE):
            index = round(event / step)
            require(math.isclose(index * step, event, rel_tol=0.0, abs_tol=1e-14),
                    f'{case_name} grid does not align with event {event:g}')
        for state in case_states:
            p = state['momentum_tonne_mm_s']
            e = state['total_mechanical_energy_N_mm']
            require(math.isclose(p, oracle.INITIAL_MOMENTUM, rel_tol=2e-13, abs_tol=2e-13),
                    f'{case_name} momentum invariant failed at t={state["time_s"]}')
            require(math.isclose(e, oracle.INITIAL_ENERGY, rel_tol=2e-13, abs_tol=2e-13),
                    f'{case_name} energy invariant failed at t={state["time_s"]}')
            require(state['penetration_mm'] >= 0.0 and state['normal_force_N'] >= 0.0,
                    f'{case_name} unilateral contact sign failed at t={state["time_s"]}')

    mid = oracle.state_at(0.14)
    release = oracle.state_at(0.18)
    require(math.isclose(mid['penetration_mm'], 0.25464790894703254, rel_tol=2e-14),
            'maximum-compression reference is wrong')
    require(math.isclose(mid['normal_force_N'], 261.7993877991494, rel_tol=2e-14),
            'maximum-contact-force reference is wrong')
    require(math.isclose(release['v1_mm_s'], -10.0 / 3.0, rel_tol=2e-14),
            'post-impact mass 1 velocity is wrong')
    require(math.isclose(release['v2_mm_s'], 20.0 / 3.0, rel_tol=2e-14),
            'post-impact mass 2 velocity is wrong')

    print('PASS: generated decks, relative exports, event grids, and analytic momentum/energy invariants')
    print('LIMIT: offline fixture audit only; no Code_Aster syntax or native result has been checked')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as error:
        print(f'FAIL: {error}', file=sys.stderr)
        raise SystemExit(1)
