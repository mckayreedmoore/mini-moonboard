"""Run one current flush-frame case without transferring historical acceptance."""
import argparse
import gzip
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
    parser.add_argument('--seed', type=Path,
                        help='Current flush report; search seed only, accepted or exhausted')
    parser.add_argument('--max-cycles', type=int, default=100)
    args = parser.parse_args()
    options = {}
    if args.seed:
        raw = args.seed.read_bytes()
        report = json.loads(gzip.decompress(raw) if args.seed.suffix == '.gz' else raw)
        if report['candidate'] != model.KEY:
            parser.error('Seed must come from the current flush candidate')
        basis = report['parameters']['floor_friction_assumption']
        if basis['mu'] != .4 or not basis['per_cell_coulomb']:
            parser.error('Seed must use the same per-cell Coulomb law')
        if not report['closed_bearing_assumption_passed']:
            parser.error('This continuation requires converged normal contact')
        options = {
            'initial_contact_names': [r['name'] for r in report['bearings'] if r['active']],
            'initial_tangent_secants': {
                n: r['next_secant_n_per_mm'] for n, r in report['floor_friction_law']['feet'].items()},
        }
    else:
        # No seed means native initialization closes its complete contact set.
        assert face_contacts()
    bolts = {c.name: bolt_properties(c) for c in model.connections() if c.kind == 'bolt'}
    hold, force = CASES[args.case]
    report = run(args.output, mu=.4, max_cycles=args.max_cycles, damping=.5,
                 bolt_stiffness={**next(iter(bolts.values())), 'by_name': bolts},
                 hold=hold, pounds=250., horizontal_force=force,
                 leg_floor_grid=3, patch_size=20., **options)
    print(json.dumps({'candidate': report['candidate'],
                      'numerically_accepted': report['numerically_accepted'],
                      'termination': report['termination']}))
    if not report['numerically_accepted']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
