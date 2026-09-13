"""Actual two-bolt assembled trial; no transfer from the fixed-wrench screen."""
import argparse
import math
from pathlib import Path

from fea.current_response_materials import WOOD_E
from fea.current_response_run import run
from mini_moonboard import compact_two_frame as candidate


def bolt_stiffness():
    area = math.pi*(candidate.WASHER_OD_MM**2-candidate.HOLE_DIAMETER**2)/4
    grip = 2*candidate.THICKNESS
    steel = 200000.*math.pi*candidate.BOLT_DIAMETER_MM**2/4/grip
    seat = .05*WOOD_E*area/grip
    return {'lateral_n_per_mm':500.**1.5*candidate.BOLT_DIAMETER_MM/23.,
            'axial_n_per_mm':1/(1/steel+1/seat),
            'basis':'Two finite point springs per leg. Rotation about their connecting line is unrestrained in this model; installed clamp friction and clearance are unqualified.',
            'washer_net_area_mm2':area}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hold', default='A12')
    parser.add_argument('--horizontal', nargs=2, type=float, default=(0., 300.))
    args = parser.parse_args()
    result = run(args.output, module=candidate, expected_candidate=candidate.KEY,
        bolt_stiffness=bolt_stiffness(), hold=args.hold, pounds=250.,
        horizontal_force=tuple(args.horizontal), leg_floor_grid=3, patch_size=20.)
    print({k:result[k] for k in ('candidate', 'numerically_accepted',
        'maximum_panel_displacement_mm', 'maximum_timber_displacement_mm')}, flush=True)


if __name__ == '__main__':
    main()
