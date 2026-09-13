"""Native assembled response for the compact three-bolt solid-4x6 candidate."""
import argparse
import math
from pathlib import Path

from fea.current_response_materials import WOOD_E
from fea.current_response_run import run
from mini_moonboard import compact_thick_frame as candidate


def bolt_stiffness():
    area = math.pi*(candidate.WASHER_OD_MM**2-candidate.HOLE_DIAMETER**2)/4
    steel = 200000.*math.pi*candidate.BOLT_DIAMETER_MM**2/4/(2*candidate.THICKNESS)
    seat = .05*WOOD_E*area/candidate.THICKNESS
    return {'lateral_n_per_mm':500.**1.5*candidate.BOLT_DIAMETER_MM/23.,
            'axial_n_per_mm':1/(1/steel+2/seat),
            'basis':f'Existing slip analogy: {candidate.BOLT_DIAMETER_MM:g} mm bolt and two {candidate.THICKNESS:g} mm wood seats; separate translations at every actual bolt restrain the noncollinear group. Clamp friction, clearance and washer flexibility remain unresolved.',
            'washer_net_area_mm2':area}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--hold',default='A12')
    parser.add_argument('--pounds',type=float,default=250.)
    parser.add_argument('--horizontal',nargs=2,type=float,default=(0.,300.))
    parser.add_argument('--leg-bolt-scale',type=float,default=1.)
    args=parser.parse_args()
    result=run(args.output,module=candidate,expected_candidate=candidate.KEY,
        bolt_stiffness=bolt_stiffness(),hold=args.hold,pounds=args.pounds,
        horizontal_force=tuple(args.horizontal),leg_bolt_scale=args.leg_bolt_scale,
        leg_floor_grid=3,patch_size=20.)
    print({k:result[k] for k in ('candidate','numerically_accepted',
        'maximum_panel_displacement_mm','maximum_timber_displacement_mm')},flush=True)


if __name__=='__main__':
    main()
