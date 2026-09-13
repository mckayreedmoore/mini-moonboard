"""One knee-brace load-path screen; gross brace stiffness is not tab qualification."""
import argparse
from pathlib import Path

from fea.current_response_run import run
from scripts.compact_rail_study import bolt_properties


def main():
    from mini_moonboard import compact_knee_frame as candidate

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    by_name = {c.name:bolt_properties(c) for c in candidate.connections() if c.kind == 'bolt'}
    properties = {**next(iter(by_name.values())), 'by_name':by_name}
    result = run(args.output, module=candidate, expected_candidate=candidate.KEY,
        bolt_stiffness=properties, hold='A12', pounds=250.,
        horizontal_force=(0., 300.), leg_floor_grid=3, patch_size=20.)
    print({k:result.get(k) for k in ('candidate', 'numerically_accepted',
        'maximum_timber_displacement_mm', 'termination')}, flush=True)


if __name__ == '__main__':
    main()
