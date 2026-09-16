"""Run one current flush-frame case without transferring historical acceptance."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from fea.floor_flush_run import face_contacts, run
from mini_moonboard import compact_floor_flush_frame as model
from scripts.clear_space_batch import CASES
from scripts.clear_space_case_contract import validate_floor_model
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
    parser.add_argument('--contact-update-strategy',
                        choices=('all', 'one_per_floor_body'), default='all',
                        help='Active-set search schedule only; physical support law is unchanged')
    parser.add_argument('--initial-contact-report', type=Path,
                        help='Numerically accepted same-candidate no-slip report for search initialization only')
    args = parser.parse_args()
    # Native initialization closes the complete normal-contact set.
    assert face_contacts()
    bolts = {c.name: bolt_properties(c) for c in model.connections() if c.kind == 'bolt'}
    hold, force = CASES[args.case]
    seeded = {}
    if args.initial_contact_report:
        data = args.initial_contact_report.read_bytes()
        previous = json.loads(gzip.decompress(data) if args.initial_contact_report.suffix == '.gz' else data)
        validate_floor_model(previous)
        if (previous.get('candidate') != model.KEY or
                previous.get('numerically_accepted') is not True or
                previous.get('source_sha256', {}).get(
                    'mini_moonboard/compact_floor_flush_frame.py') !=
                hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest()):
            raise ValueError('Search seed must be an accepted current-candidate no-slip case')
        seeded['initial_contact_names'] = [row['name'] for row in previous['bearings'] if row['active']]
    report = run(args.output, max_cycles=args.max_cycles,
                 contact_stiffness_per_area=args.contact_stiffness_per_area,
                 frame_size=args.frame_size,
                 bolt_stiffness={**next(iter(bolts.values())), 'by_name': bolts},
                 hold=hold, pounds=250., horizontal_force=force,
                 contact_update_strategy=args.contact_update_strategy,
                 leg_floor_grid=3, patch_size=20., **seeded)
    print(json.dumps({'candidate': report['candidate'],
                      'numerically_accepted': report['numerically_accepted'],
                      'termination': report['termination']}))
    if not report['numerically_accepted']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
