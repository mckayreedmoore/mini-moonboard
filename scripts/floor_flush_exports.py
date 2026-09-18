"""Export the requested flush-end revision without borrowing historical acceptance."""
import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path

from mini_moonboard import compact_floor_flush_frame as model
from mini_moonboard import floor_flush_width as width
from mini_moonboard.box_frame import Connection
from scripts import clear_space_exports as existing

shared = existing.shared
PACKAGE = 'docs/floor-flush-build-package.md'
STATUS = 'Selected floor-runner development · six no-slip cases pass · unlisted angle actions disclosed'


@dataclass(frozen=True)
class ViewerPanelScrew(Connection):
    """Nominal owned-screw visual; not a machining or resistance model."""

    @property
    def product_status(self):
        return ('Owned Hillman 42605 #10 x 2-1/2 in panel/kicker screw; '
                '63.5 mm length and nominal #10 body visual only; actual head, '
                'thread, pilot and resistance require separate evidence')


class ViewerModel:
    def __init__(self, frame=model):
        self.frame = frame
        self.KEY = frame.KEY

    def __getattr__(self, name):
        return getattr(self.frame, name)

    def parts(self):
        return tuple(replace(part, description=(
            'Owned Roseburg 23/32 face panel; 66 total Hillman 42605 panel/kicker '
            'axes in selected frame; visual screw dimensions are nominal, '
            'not a pilot or resistance specification')
            ) if part.name.startswith('main_') and 'SPAX' in part.description
            else part for part in self.frame.parts())

    def connections(self):
        panel = {connection.name for connection in self.frame.panel_connections()}
        return tuple(ViewerPanelScrew(connection.name, connection.start,
            connection.direction, 63.5, 4.826, connection.members,
            connection.kind, connection.grip)
            if connection.name in panel else connection
            for connection in self.frame.connections())


viewer_model = ViewerModel()


def selected_authority():
    return json.loads((shared.ROOT / 'current-candidate.json').read_text())


def sources():
    result = existing.sources(model, 'floorflush')
    result[str(Path(__file__).resolve().relative_to(shared.ROOT))] = shared.digest(__file__)
    result['current-candidate.json'] = shared.digest(shared.ROOT / 'current-candidate.json')
    result['mini_moonboard/floor_flush_width.py'] = shared.digest(
        shared.ROOT / 'mini_moonboard/floor_flush_width.py')
    return dict(sorted(result.items()))


def metadata_for(width_option):
    documents = selected_authority()['viewer_documents']
    trim = width.trim_mm(width_option)
    note = ('Twelve complete bolt stacks; nuts and tips outward. All flush cuts require shop inspection.'
            if width_option == width.OFFICIAL else
            f'K-side 1/8 in ({trim:g} mm) kerf presentation of the selected floor-runner. '
            'Official Mini 4×4 six-case evidence is not transferred. Not a fabrication release.')
    def metadata(parts, connections):
        return {**shared.design_metadata(parts, connections),
            'key': model.KEY, 'viewer_key': width.variant(width_option).KEY,
            'width_option': width_option, 'kerf_right_mm': trim,
            'status': STATUS, 'description': STATUS,
            'build_package': PACKAGE, 'assessment_scope':
            'Six fresh no-slip cases pass 36 frozen checks; unlisted ML24Z separation and parallel couple remain disclosed, not rated. Historical finite-friction and taper cases do not transfer.',
            'leg_stock': '4x6', 'outer_rim_stock': '4x6',
            'total_bolt_count': sum(c.kind == 'bolt' for c in connections),
            'leg_bolt_count': 4, 'bolts_per_leg': 2, 'knee_piece_count': 0,
            'upper_bolt_pitch_mm': existing.upper_bolt_pitch_mm(connections),
            'lower_kicker_screw_height_mm': 60.,
            'base_clip_center_y_mm': model.CLIP_CENTER_Y_MM,
            'joint_note': note,
            'panel_screw_visual_scope': '66 Hillman 42605 nominal 63.5 mm visuals; head, thread, pilot and resistance unqualified.',
            'documents': documents}
    return metadata


def export(root=Path('site'), *, width_option=width.OFFICIAL):
    frame = width.variant(width_option)
    return shared.export(root, candidate=ViewerModel(frame), metadata=metadata_for(width_option),
                         source_reader=sources)


def export_all(root=Path('site')):
    return export(root, width_option=width.OFFICIAL), export(root, width_option=width.KERF_RIGHT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('site'))
    parser.add_argument('--width', choices=width.OPTIONS)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.width:
        exporter = lambda root: export(root, width_option=args.width)
        print(shared.check(args.root, candidate=width.variant(args.width), exporter=exporter)
              if args.check else export(args.root, width_option=args.width))
    elif args.check:
        print(shared.check(args.root, candidate=model, exporter=lambda root: export(root, width_option=width.OFFICIAL)))
        print(shared.check(args.root, candidate=width.variant(width.KERF_RIGHT),
                           exporter=lambda root: export(root, width_option=width.KERF_RIGHT)))
    else:
        print(export_all(args.root))
