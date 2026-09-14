"""Actual independent unnotched knee segments with a bolted/contact overlap."""
import argparse
import json
from pathlib import Path

from fea.current_response_run import run
from mini_moonboard import compact_spliced_knee_frame as candidate
from scripts.compact_rail_study import bolt_properties


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hold', default='A12')
    parser.add_argument('--horizontal', type=float, nargs=2, default=(0., 300.))
    parser.add_argument('--contact-seed', type=Path)
    args = parser.parse_args()
    by_name = {c.name:bolt_properties(c) for c in candidate.connections() if c.kind == 'bolt'}
    properties = {**next(iter(by_name.values())), 'by_name':by_name}
    contacts = [{**row, 'stiffness_n_per_mm':100.*row['tributary_area_mm2']}
                for row in candidate.overlap_contact_datums()]
    seeded = {}
    if args.contact_seed:
        seed = json.loads(args.contact_seed.read_text())
        if seed.get('candidate') != candidate.KEY or seed.get('numerically_accepted') is not True:
            raise ValueError('Contact seed must be an accepted result of this candidate')
        seeded['initial_contact_names'] = [row['name'] for row in seed['bearings'] if row['active']]
    result = run(args.output, module=candidate, expected_candidate=candidate.KEY,
        bolt_stiffness=properties, hold=args.hold, pounds=250., member_contacts=contacts,
        horizontal_force=tuple(args.horizontal), leg_floor_grid=3, patch_size=20., **seeded)
    print({k:result.get(k) for k in ('candidate', 'numerically_accepted',
        'maximum_timber_displacement_mm', 'termination')}, flush=True)


if __name__ == '__main__':
    main()
