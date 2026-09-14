"""Two upper bolts and actual brace-tab geometry under the selected load case."""
import argparse
from pathlib import Path

from fea.current_response_run import run
from mini_moonboard import compact_knee_two_frame as candidate
from scripts.compact_rail_study import bolt_properties


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hold', default='A12')
    parser.add_argument('--horizontal', type=float, nargs=2, default=(0., 300.))
    args = parser.parse_args()
    by_name = {c.name:bolt_properties(c) for c in candidate.connections() if c.kind == 'bolt'}
    properties = {**next(iter(by_name.values())), 'by_name':by_name}
    result = run(args.output, module=candidate, expected_candidate=candidate.KEY,
        bolt_stiffness=properties, hold=args.hold, pounds=250., tab_geometry=True,
        horizontal_force=tuple(args.horizontal), leg_floor_grid=3, patch_size=20.)
    print({k:result.get(k) for k in ('candidate', 'numerically_accepted',
        'maximum_timber_displacement_mm', 'termination')}, flush=True)


if __name__ == '__main__':
    main()
