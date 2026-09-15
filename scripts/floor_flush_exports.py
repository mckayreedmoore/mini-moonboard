"""Export the requested flush-end revision without borrowing historical acceptance."""
import argparse
from pathlib import Path

from mini_moonboard import compact_floor_flush_frame as model
from scripts import clear_space_exports as existing

shared = existing.shared
PACKAGE = 'docs/floor-flush-build-package.md'
STATUS = 'Development · flush runner, rim and leg ends · current checks incomplete'


def sources():
    result = existing.sources(model, 'floorflush')
    result[str(Path(__file__).resolve().relative_to(shared.ROOT))] = shared.digest(__file__)
    return dict(sorted(result.items()))


def metadata(parts, connections):
    return {**shared.design_metadata(parts, connections),
        'key': model.KEY, 'status': STATUS, 'description': STATUS,
        'build_package': PACKAGE, 'assessment_scope':
        'Fresh geometry revision. Previous six taper cases do not qualify changed ends, bearing, bolt distances or support footprint.',
        'leg_stock': '4x6', 'outer_rim_stock': '4x6',
        'total_bolt_count': sum(c.kind == 'bolt' for c in connections),
        'leg_bolt_count': 4, 'bolts_per_leg': 2, 'knee_piece_count': 0,
        'upper_bolt_pitch_mm': existing.upper_bolt_pitch_mm(connections),
        'lower_kicker_screw_height_mm': 60.,
        'base_clip_center_y_mm': model.CLIP_CENTER_Y_MM,
        'joint_note': 'Twelve complete bolt stacks; nuts and tips outward. All flush cuts require current checks.'}


def export(root=Path('site')):
    return shared.export(root, candidate=model, metadata=metadata, source_reader=sources)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('site'))
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(shared.check(args.root, candidate=model, exporter=export) if args.check else export(args.root))
