"""Run one current flush-frame case without transferring historical acceptance."""
import argparse
import json
from pathlib import Path

from fea.floor_flush_run import face_contacts, run
from mini_moonboard import compact_floor_flush_frame as model
from scripts.clear_space_batch import CASES
from scripts.compact_rail_study import bolt_properties


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=CASES)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--max-cycles', type=int, default=100)
    parser.add_argument('--contact-stiffness-per-area', type=float, default=100.,
                        help='Normal timber-face penalty in N/mm³; sensitivity input, not measured stiffness')
    parser.add_argument('--frame-size', type=float, default=150.,
                        help='Target timber mesh size in mm; sensitivity input')
    args = parser.parse_args()
    # Native initialization closes the complete normal-contact set.
    assert face_contacts()
    bolts = {c.name: bolt_properties(c) for c in model.connections() if c.kind == 'bolt'}
    hold, force = CASES[args.case]
    report = run(args.output, max_cycles=args.max_cycles,
                 contact_stiffness_per_area=args.contact_stiffness_per_area,
                 frame_size=args.frame_size,
                 bolt_stiffness={**next(iter(bolts.values())), 'by_name': bolts},
                 hold=hold, pounds=250., horizontal_force=force,
                 leg_floor_grid=3, patch_size=20.)
    print(json.dumps({'candidate': report['candidate'],
                      'numerically_accepted': report['numerically_accepted'],
                      'termination': report['termination']}))
    if not report['numerically_accepted']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
