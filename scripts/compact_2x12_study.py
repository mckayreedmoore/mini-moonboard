"""Run fresh assembled response for the unbraced 2x12 leg trial."""
import argparse
from pathlib import Path

from fea.current_response_run import run
from mini_moonboard import compact_2x12_leg_frame as model
from scripts.compact_rail_study import bolt_properties

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staggered',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--hold',default='A12')
    parser.add_argument('--horizontal',type=float,nargs=2,default=(0.,300.))
    args = parser.parse_args()
    if args.staggered:
        from mini_moonboard import compact_2x12_staggered_frame as model
    rows = {c.name:bolt_properties(c) for c in model.connections() if c.kind == 'bolt'}
    result = run(args.output,module=model,expected_candidate=model.KEY,
        bolt_stiffness={**next(iter(rows.values())),'by_name':rows},hold=args.hold,
        pounds=250.,horizontal_force=tuple(args.horizontal),leg_floor_grid=3,patch_size=20.)
    print({k:result.get(k) for k in ('candidate','numerically_accepted','maximum_timber_displacement_mm','termination')})
