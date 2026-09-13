"""Bounded, reproducible assembled leg-connection study; no load-rating claim."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from fea.current_response_materials import WOOD_E
from fea.current_response_run import run
from mini_moonboard import leg_mvp_frame as candidate
from mini_moonboard import leg_mvp_sole_frame as sole
from mini_moonboard import wider_leg_hardware as hardware

CASES = {
    'baseline-leg-soft': {'leg_bolt_scale': .25},
    'baseline-leg-stiff': {'leg_bolt_scale': 4.},
    'baseline-foot3': {'leg_floor_grid': 3},
    'baseline-foot5': {'leg_floor_grid': 5},
    'sole-foot3': {'leg_floor_grid': 3},
    'sole-foot5': {'leg_floor_grid': 5},
    'sole-soft': {'leg_floor_grid': 3, 'leg_bolt_scale': .25},
    'sole-stiff': {'leg_floor_grid': 3, 'leg_bolt_scale': 4.},
    'sole-static': {'leg_floor_grid': 3, 'dynamic_factor': 1., 'horizontal_force': (0., 0.)},
    'sole-side': {'leg_floor_grid': 3, 'horizontal_force': (-300., 0.)},
    'sole-center': {'leg_floor_grid': 3, 'hold': 'F10'},
    'sole-lower': {'leg_floor_grid': 3, 'hold': 'A1'},
    'candidate-corners': {},
    'candidate-foot3': {'leg_floor_grid': 3},
    'candidate-foot5': {'leg_floor_grid': 5},
    'candidate-leg-soft': {'leg_floor_grid': 3, 'leg_bolt_scale': .25},
    'candidate-leg-stiff': {'leg_floor_grid': 3, 'leg_bolt_scale': 4.},
    'candidate-static': {'leg_floor_grid': 3, 'dynamic_factor': 1., 'horizontal_force': (0., 0.)},
    'candidate-side': {'leg_floor_grid': 3, 'horizontal_force': (-300., 0.)},
    'candidate-center': {'leg_floor_grid': 3, 'hold': 'F10'},
    'candidate-lower': {'leg_floor_grid': 3, 'hold': 'A1'},
}


def bolt_stiffness():
    """Same elastic analogy as baseline, using the actual larger bolt/plate."""
    area = hardware.PLATE_SIDE**2-math.pi*hardware.PLATE_HOLE**2/4
    steel = 200000.*math.pi*hardware.BOLT_DIAMETER**2/4/(2*candidate.THICKNESS)
    seat = .05*WOOD_E*area/candidate.THICKNESS
    return {'lateral_n_per_mm': 500.**1.5*hardware.BOLT_DIAMETER/23.,
            'axial_n_per_mm': 1/(1/steel+2/seat),
            'basis': 'Published slip analogy at density500 kg/m3 and12.7 mm diameter; steel over76.2 mm grip plus two transverse wood columns under BP1/2 net area. Plate flexibility, hole clearance and preload are omitted; scale sensitivities are not measured bounds.',
            'plate_net_area_mm2': area, 'steel_n_per_mm': steel,
            'each_wood_seat_n_per_mm': seat}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=CASES)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    parameters = {'hold': 'A12', 'pounds': 250., 'patch_size': 20., **CASES[args.case]}
    revised = args.case.startswith(('candidate-', 'sole-'))
    module = sole if args.case.startswith('sole-') else candidate
    result = run(args.output, **parameters, **({'module': module,
        'expected_candidate': module.KEY, 'bolt_stiffness': bolt_stiffness()} if revised else {}))
    record = {'case': args.case, 'candidate': result['candidate'],
              'numerically_accepted': result['numerically_accepted'],
              'parameters': result['parameters'],
              'maximum_timber_displacement_mm': result['maximum_timber_displacement_mm'],
              'maximum_panel_displacement_mm': result['maximum_panel_displacement_mm'],
              'producer_driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output/'study-case.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
