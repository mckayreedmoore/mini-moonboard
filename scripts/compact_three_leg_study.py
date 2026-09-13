"""Native response for either of the two bounded higher three-bolt assemblies."""
import argparse
from pathlib import Path

from fea.current_response_run import run
from mini_moonboard.compact_three_leg_225_refined import CANDIDATE as refined225
from mini_moonboard.compact_three_leg_options import option
from scripts.compact_thick_study import bolt_stiffness


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--leg', choices=('upper225', 'upper300', 'upper225-refined'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hold', default='A12')
    parser.add_argument('--horizontal', type=float, nargs=2, default=(0., 300.))
    args = parser.parse_args()
    candidate = refined225 if args.leg == 'upper225-refined' else option(args.leg)
    result = run(args.output, module=candidate, expected_candidate=candidate.KEY,
        bolt_stiffness=bolt_stiffness(), hold=args.hold, pounds=250.,
        horizontal_force=tuple(args.horizontal), leg_floor_grid=3, patch_size=20.)
    print({k:result.get(k) for k in ('candidate', 'numerically_accepted',
        'maximum_timber_displacement_mm', 'termination')}, flush=True)


if __name__ == '__main__':
    main()
