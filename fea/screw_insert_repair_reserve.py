"""Reserve future insert space around ordinary panel screws; no repair rating."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import cadquery as cq

from fea import single_2x6_screen as screen
from mini_moonboard import wide_frame as wide

DIAMETER = wide.INSERT['nominal_outer_diameter'] + wide.INSERT['drawing_general_tolerance_plus_minus']
DEPTH = wide.ASSUMPTIONS['pilot_tip_clearance_depth']
VOLUME_TOLERANCE = .01
LIMITS = (
    'Geometry reservation only, checked in service-pocketed receiver stock before fastener bores. '
    'Ordinary panel/kicker wood screws are installed; zero inserts are installed. '
    'The full solid reserve is not an installation pilot or permission to predrill. '
    'Existing screw damage, splitting, insert resistance, recess, usable thread engagement, '
    'future panel countersink, driver access and repair installation remain unqualified. '
    'A damaged hole may invalidate this nominal reservation. No structural or repair rating.'
)


def reserve(connection):
    entry = connection.start + connection.direction * wide.PANEL
    return entry, cq.Solid.makeCylinder(DIAMETER / 2, DEPTH, entry, connection.direction)


def overlaps(a, b):
    aa, bb = a.BoundingBox(), b.BoundingBox()
    if any(getattr(aa, axis+'max') <= getattr(bb, axis+'min') or
           getattr(bb, axis+'max') <= getattr(aa, axis+'min') for axis in 'xyz'):
        return False
    return a.intersect(b).Volume() > VOLUME_TOLERANCE


def assess(parts, hardware):
    panels = [c for c in hardware if isinstance(c, wide.timber.PanelScrew)]
    if len(panels) != 56 or len({c.name for c in panels}) != 56:
        raise ValueError('Expected 56 unique panel/kicker wood screws')
    components = [(c.name, shape) for c in hardware for shape in c.components()]
    rows = []
    for c in panels:
        entry, cylinder = reserve(c)
        missing = cylinder.cut(parts[c.members[1]].shape).Volume()
        collisions = sorted({name for name, shape in components
                             if name != c.name and overlaps(cylinder, shape)})
        rows.append({'connection': c.name, 'panel': c.members[0], 'receiver': c.members[1],
                     **dict(zip(('entry_x_mm', 'entry_y_mm', 'entry_z_mm'), entry.toTuple(), strict=True)),
                     **dict(zip(('direction_x', 'direction_y', 'direction_z'), c.direction.toTuple(), strict=True)),
                     'reserve_diameter_mm': DIAMETER, 'reserve_depth_mm': DEPTH,
                     'missing_receiver_volume_mm3': missing,
                     'intersecting_other_fasteners': collisions,
                     'passes_nominal_reserve': missing <= VOLUME_TOLERANCE and not collisions})
    return {'reserve_count': len(rows), 'passes_nominal_reserves': all(r['passes_nominal_reserve'] for r in rows),
            'qualified_for_design': False, 'qualified_repair': False, 'schedule': rows}


def build(variant='baseline'):
    parts, _ = screen.candidates()[variant]
    paths = [Path(__file__).resolve(), Path(screen.__file__).resolve(),
             Path('docs/panel-insert-reference.json').resolve(), Path('docs/ml24z-reference.json').resolve(),
             *sorted(Path('mini_moonboard').resolve().glob('*.py'))]
    return {'variant': variant, 'installed_threaded_inserts': 0, 'limits': LIMITS,
            'missing_volume_tolerance_mm3': VOLUME_TOLERANCE,
            'source_sha256': {str(p.relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in paths},
            **assess(parts, screen.connections())}


def write(report, output):
    """Create a new report directory; never overwrite existing evidence."""
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'report.json').open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    with (output / 'schedule.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(report['schedule'][0]))
        writer.writeheader()
        for row in report['schedule']:
            writer.writerow({**row, 'intersecting_other_fasteners': ';'.join(row['intersecting_other_fasteners'])})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=screen.VARIANTS, default='baseline')
    parser.add_argument('--output', type=Path, required=True, help='New directory for JSON and CSV')
    args = parser.parse_args()
    write(build(args.variant), args.output)
