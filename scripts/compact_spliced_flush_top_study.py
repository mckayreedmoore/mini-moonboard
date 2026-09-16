"""Launch selected flush-top candidate's authenticated no-slip response cases."""
import argparse
import json
from pathlib import Path

from fea.compact_spliced_flush_top_run import run
from mini_moonboard import compact_spliced_flush_top as candidate
from scripts.compact_rail_study import bolt_properties

CASES = {
    'a12-left': ('A12', (-300., 0.)),
    'a12-rear': ('A12', (0., 300.)),
    'a12-forward': ('A12', (0., -300.)),
    'k12-right': ('K12', (300., 0.)),
    'k12-rear': ('K12', (0., 300.)),
    'a1-rear': ('A1', (0., 300.)),
}


def launch(output, *, hold='A12', horizontal=(-300., 0.), contact_seed=None):
    """Prepare and solve one fresh authenticated response case."""
    by_name = {
        connection.name: bolt_properties(connection)
        for connection in candidate.connections()
        if connection.kind == 'bolt'
    }
    contacts = [
        {**row, 'stiffness_n_per_mm': 100.*row['tributary_area_mm2']}
        for row in candidate.overlap_contact_datums()
    ]
    seeded = {}
    if contact_seed:
        seed = json.loads(Path(contact_seed).read_text())
        if seed.get('candidate') != candidate.KEY or seed.get('numerically_accepted') is not True:
            raise ValueError('Contact seed must be an accepted result of this candidate')
        seeded['initial_contact_names'] = [row['name'] for row in seed['bearings'] if row['active']]
    return run(
        Path(output),
        bolt_stiffness={**next(iter(by_name.values())), 'by_name': by_name},
        member_contacts=contacts,
        hold=hold,
        pounds=250.,
        horizontal_force=tuple(horizontal),
        leg_floor_grid=3,
        patch_size=20.,
        **seeded,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hold', default='A12')
    parser.add_argument('--horizontal', type=float, nargs=2, default=(-300., 0.))
    parser.add_argument('--contact-seed', type=Path)
    args = parser.parse_args()
    result = launch(args.output, hold=args.hold, horizontal=args.horizontal,
                    contact_seed=args.contact_seed)
    print({key: result.get(key) for key in (
        'candidate', 'numerically_accepted', 'maximum_timber_displacement_mm', 'termination')},
        flush=True)


if __name__ == '__main__':
    main()
