"""Run one separate uncut-leg case; no inherited acceptance or released drilling."""
import argparse
import json
from pathlib import Path

from fea.floor_uncut_run import bolt_properties, run
from mini_moonboard import compact_floor_uncut_frame as model
from scripts.clear_space_batch import CASES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=CASES)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-cycles', type=int, default=100)
    parser.add_argument('--frame-size', type=float, default=150.)
    args = parser.parse_args()
    bolts = {c.name: bolt_properties(c) for c in model.connections() if c.kind == 'bolt'}
    hold, horizontal = CASES[args.case]
    report = run(args.output, max_cycles=args.max_cycles,
                 bolt_stiffness={**next(iter(bolts.values())), 'by_name': bolts},
                 hold=hold, pounds=250., horizontal_force=horizontal,
                 frame_size=args.frame_size, leg_floor_grid=3, patch_size=20.)
    print(json.dumps({'candidate': report['candidate'], 'numerically_accepted': report['numerically_accepted'],
                      'termination': report['termination']}))
    if not report['numerically_accepted']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
