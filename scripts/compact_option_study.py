"""Bounded load/leg-position native trials with unchanged selected load defaults."""
import argparse
from pathlib import Path

from fea.current_response_run import run
from mini_moonboard import compact_two_frame
from mini_moonboard.compact_leg_options import option
from scripts.compact_two_study import bolt_stiffness


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--leg', choices=('baseline', 'control', 'foot150', 'foot300', 'lower150', 'upper150'), default='baseline')
    parser.add_argument('--dynamic-factor', type=float, choices=(1., 2.), default=2.)
    parser.add_argument('--rearward-n', type=float, choices=(0., 300.), default=300.)
    args = parser.parse_args()
    candidate = compact_two_frame if args.leg == 'baseline' else option(args.leg)
    result = run(args.output, module=candidate, expected_candidate=candidate.KEY,
        bolt_stiffness=bolt_stiffness(), hold='A12', pounds=250.,
        dynamic_factor=args.dynamic_factor, horizontal_force=(0., args.rearward_n),
        leg_floor_grid=3, patch_size=20.)
    print({k:result.get(k) for k in ('candidate', 'numerically_accepted',
        'maximum_timber_displacement_mm', 'termination')}, flush=True)


if __name__ == '__main__':
    main()
