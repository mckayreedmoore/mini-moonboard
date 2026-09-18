"""Generate draft fabrication coordinates for the actual flush floor-beam model.

Profiles describe the current trimmed raw timber, before bores and taper removal.
Blank dimensions remain stock allowances, not finished lengths. No resistance
acceptance or machining tolerance is inferred from this dimensional packet.
"""
import argparse
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as model
from mini_moonboard import floor_flush_width as width
from mini_moonboard import panel_grid_v2 as grid
from mini_moonboard.round_service_drilling import passage_rows
from scripts import clear_space_construction as shared
from scripts import floor_flush_exports as exporter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/floor-flush-construction'
KERF_OUT = ROOT / 'docs/floor-flush-construction-kerf-right'
STATUS = ('DRAFT coordinates — six no-slip cases pass frozen criteria; delivered '
          'hardware and fabrication inspection remain; not a fabrication release')
HILLMAN_LENGTH_MM = 63.5
SDS_LENGTH_MM = 38.1
INCH_MM = 25.4


def shop_axis_fields(connection):
    """Shop instruction beside occupied CAD envelopes. Occupied values are not bits."""
    occupied_length = connection.length
    occupied_diameter = connection.diameter
    if connection.kind == 'bolt':
        hole = model.bolt_dimensions(connection)['hole_diameter_mm']
        return {
            'occupied_length_mm': occupied_length,
            'occupied_diameter_mm': occupied_diameter,
            'shop_opening_kind': 'bolt_clearance',
            'shop_finished_opening_min_mm': connection.diameter + INCH_MM / 32,
            'shop_finished_opening_max_mm': connection.diameter + INCH_MM / 16,
            'shop_purchased_length_mm': '',
            'shop_instruction': (
                'NDS §12.1.3 wood clearance D+1/32 to D+1/16 in; '
                f'CAD occupied hole {hole:g} mm is the upper end, not a bit catalog number.'
            ),
        }
    if connection.name.startswith('clip_'):
        return {
            'occupied_length_mm': occupied_length,
            'occupied_diameter_mm': occupied_diameter,
            'shop_opening_kind': 'sds_wood',
            'shop_purchased_length_mm': SDS_LENGTH_MM,
            'shop_finished_opening_min_mm': INCH_MM * 5 / 32,
            'shop_finished_opening_max_mm': INCH_MM * 5 / 32,
            'shop_instruction': (
                'Specified SDS25112 through purchased ML24Z holes. Occupied CAD diameter '
                '6.35 mm is not a wood pilot. Owner-selected wood lead hole is the Simpson '
                'catalog 5/32 in (3.96875 mm) bit, drilled through the purchased angle holes. '
                'Do not independently predrill from CAD.'
            ),
        }
    return {
        'occupied_length_mm': occupied_length,
        'occupied_diameter_mm': occupied_diameter,
        'shop_opening_kind': 'hillman_panel',
        'shop_finished_opening_min_mm': '',
        'shop_finished_opening_max_mm': '',
        'shop_purchased_length_mm': HILLMAN_LENGTH_MM,
        'shop_instruction': (
            'Purchased Hillman 42605 #10 x 2-1/2 in (63.5 mm). Occupied length/diameter are '
            'historical SPAX envelopes, not Hillman dimensions. Owner-selected Kobalt 80277 '
            '#10 insert: 1/8 in lead-hole pilot and 3/8 in face countersink. Occupied CAD '
            'diameter is not the pilot and not a clearance hole. Do not use this bit for SDS.'
        ),
    }


class SheetModel:
    """Delegate current geometry while suppressing inherited historical trim notes."""

    def __init__(self, source=model):
        self._source = source

    def __getattr__(self, name):
        return getattr(self._source, name)

    def trim_planes(self):
        # The preceding splice helper reports historical end cuts. Current
        # cut corners are supplied explicitly by profile-corner-datums.csv.
        return {}


@contextmanager
def sheet_context(output, source=model):
    values = {'OUT': output, 'model': SheetModel(source), 'PACKET_STATUS': STATUS,
                  'PACKAGE': exporter.PACKAGE, 'HARDWARE': 'bolt-hardware.csv'}
    old = {key: getattr(shared, key) for key in values}
    try:
        for key, value in values.items():
            setattr(shared, key, value)
        yield
    finally:
        for key, value in old.items():
            setattr(shared, key, value)


def profile_corner_rows(datums):
    """Dimension each actual side-profile corner from the drilling datum."""
    raw = {part.name: part for part in shared.model.uncut_wood_parts()}
    rows = []
    for name in sorted({row['member'] for row in datums}):
        datum = next(row for row in datums if row['member'] == name)
        origin = cq.Vector(*(datum[f'origin_{axis}_mm'] for axis in 'xyz'))
        along = cq.Vector(0., datum['along_y'], datum['along_z'])
        cross = cq.Vector(0., datum['cross_y'], datum['cross_z'])
        points = sorted({tuple(vertex.Center().toTuple()) for vertex in raw[name].shape.Vertices()
                         if abs(vertex.Center().x-origin.x) < 1.e-6},
                        key=lambda p: ((cq.Vector(*p)-origin).dot(along),
                                       (cq.Vector(*p)-origin).dot(cross)))
        for number, xyz in enumerate(points, 1):
            offset = cq.Vector(*xyz)-origin
            rows.append({'member': name, 'corner': number,
                'origin_x_mm': origin.x, 'origin_y_mm': origin.y, 'origin_z_mm': origin.z,
                'along_from_corner_mm': offset.dot(along), 'signed_cross_from_corner_mm': offset.dot(cross),
                'world_x_mm': xyz[0], 'world_y_mm': xyz[1], 'world_z_mm': xyz[2],
                'detail': 'Actual trimmed raw side-profile corner; use outline for perimeter order. Taper removal is separate.',
                'assessment_status': STATUS})
    return rows


def generate(output=OUT, *, width_option=width.OFFICIAL):
    output = Path(output)
    frame = width.variant(width_option)
    inventory_path = ROOT / 'site/hybrid' / frame.KEY / 'parts.json'
    manifest_path = inventory_path.with_name('manifest.json')
    export_manifest = json.loads(manifest_path.read_text())
    sources = exporter.sources()
    if export_manifest['source_sha256'] != sources:
        raise ValueError('Flush viewer sources are stale; rebuild the flush export first')
    for name, digest in export_manifest['artifact_sha256'].items():
        if exporter.shared.digest(inventory_path.parent/name) != digest:
            raise ValueError('Flush viewer artifact mismatch: '+name)
    for path in (Path(__file__), Path(shared.__file__), inventory_path, manifest_path):
        sources[str(path.resolve().relative_to(ROOT))] = exporter.shared.digest(path)
    inventory = json.loads(inventory_path.read_text())
    if inventory['design']['key'] != model.KEY:
        raise ValueError('Wrong candidate inventory')
    if inventory['design'].get('width_option', width.OFFICIAL) != width_option:
        raise ValueError('Construction width option does not match viewer inventory')
    output.mkdir(parents=True, exist_ok=True)
    with sheet_context(output, frame):
        write = shared.write_csv
        stock = []
        for part in inventory['parts']:
            if part['fabrication']['kind'] != 'part' or part['name'].startswith('clip_'):
                continue
            dimensions = part['fabrication']['dimensions_mm']
            stock.append({'member': part['name'], 'blank_length_or_panel_width_mm': dimensions[0],
                'blank_depth_or_panel_height_mm': dimensions[1], 'thickness_mm': dimensions[2], 'quantity': 1,
                'detail': 'Stock blank allowance, not finished cut length; actual trimmed corners in stock-profiles.json and profile-corner-datums.csv.',
                'assessment_status': STATUS})
        write('stock.csv', stock)
        connections = frame.connections()
        axes = []
        for connection in connections:
            shop = shop_axis_fields(connection)
            axes.append({'name': connection.name, 'kind': connection.kind,
                'first_member': connection.members[0], 'second_member': connection.members[1],
                'start_x_mm': connection.start.x, 'start_y_mm': connection.start.y,
                'start_z_mm': connection.start.z,
                'direction_x': connection.direction.x, 'direction_y': connection.direction.y,
                'direction_z': connection.direction.z,
                'modeled_length_mm': connection.length, 'modeled_diameter_mm': connection.diameter,
                **shop,
                'operation': shop['shop_instruction'],
                'assessment_status': STATUS})
        write('connection-axes.csv', axes)
        bolts = [c for c in connections if c.kind == 'bolt']
        write('bolt-hardware.csv', [dict(name=c.name, first_member=c.members[0], second_member=c.members[1],
            **model.bolt_dimensions(c), **shop_axis_fields(c), assessment_status=STATUS) for c in bolts])
        datums = shared.bolt_member_datums(connections)
        for row in datums:
            row['instruction'] = 'Draft axis normal to side face; physical corner and signed directions govern. Not a drilling release.'
        write('bolt-member-datums.csv', datums)
        write('profile-corner-datums.csv', profile_corner_rows(datums))
        shared.joined_member_sheets(datums)
        shared.leg_taper_sheets()
        shared.end_trim_diagram()
        # Existing diagram text must not imply an accepted package. All actual
        # geometry above comes from the selected model, never archived sheets.
        for path in output.glob('*.svg'):
            text = path.read_text().replace('conditional package profile', 'DRAFT current profile')
            text = text.replace('Blank length × depth × thickness:', 'Stock allowance (not finished length) × depth × thickness:')
            text = text.replace('Full raw side profile shown; these sheets do not include every machining operation.',
                'Actual trimmed raw outline shown. Cut corners: profile-corner-datums.csv. Taper and bores are separate.')
            text = text.replace('hardware: ../bolt-hardware.csv', 'hardware: bolt-hardware.csv')
            text = text.replace('Hardware: ../bolt-hardware.csv', 'Hardware: bolt-hardware.csv')
            path.write_text(text)
        panel = []
        for row in frame.attachment_datums():
            name = row['panel']
            left = -model.b.HALF if name.endswith('_left') else 0.
            bottom = model.b.HALF if name.startswith('main_upper_') else 0.
            panel.append({'name': row['name'], 'panel': name, 'receiver': row['receiver'],
                'from_left_mm': row['x']-left, 'from_bottom_mm': row['s']-bottom,
                'vertical_axis': 'Z from floor' if name.startswith('kicker_') else 'S along panel slope',
                'shop_purchased_length_mm': HILLMAN_LENGTH_MM,
                'shop_opening_kind': 'hillman_panel',
                'operation': ('Owned Hillman 42605 #10 x 2-1/2 in (63.5 mm) axis; occupied CAD length in '
                              'connection-axes.csv is not this length; owner-selected Kobalt 80277 '
                              '#10 insert 1/8 in pilot and 3/8 in countersink.')})
        write('panel-attachment-axes.csv', panel)
        holes = []
        for kind, hole_datums, diameter in [('hold', grid.main_tnut_datums(), 11.1125),
                                           ('LED', grid.main_led_datums(), 13.)]:
            for label, (x, station) in hole_datums.items():
                side = 'left' if x < model.b.HALF else 'right'
                band = 'lower' if station < model.b.HALF else 'upper'
                holes.append({'label': label, 'kind': kind, 'panel': f'main_{band}_{side}',
                    'from_left_mm': x-(0 if side == 'left' else model.b.HALF),
                    'from_bottom_mm': station-(0 if band == 'lower' else model.b.HALF), 'diameter_mm': diameter})
        for label, (x, z) in grid.kicker_foothold_datums().items():
            side = 'left' if x < model.b.HALF else 'right'
            holes.append({'label': label, 'kind': 'hold', 'panel': 'kicker_'+side,
                'from_left_mm': x-(0 if side == 'left' else model.b.HALF),
                'from_bottom_mm': shared.baseline.KICKER_HEIGHT_MM+z, 'diameter_mm': 11.1125})
        write('panel-hole-axes.csv', holes)
        profiles = {p.name: {'stock_blank_allowance_mm': p.blank,
            'vertices_world_mm': sorted({tuple(round(v, 9) for v in vertex.Center().toTuple())
                                     for vertex in p.shape.Vertices()})} for p in frame.uncut_wood_parts()}
        for name, value in [('stock-profiles.json', profiles), ('timber-passages.json', passage_rows(model)),
                            ('runner-end-geometry.json', model.runner_end_geometry())]:
            (output/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
        if (len(stock), len(axes), len(bolts), len(panel), sum(h['kind'] == 'hold' for h in holes)) != (26, 222, 12, 66, 142):
            raise ValueError('Unexpected candidate inventory counts')
    width_note = ('' if width_option == width.OFFICIAL else
        f'\nThis packet is the **kerf-right** presentation: 1/8 in ({width.KERF_RIGHT_MM:g} mm) '
        'removed from the K-side overall width. Official Mini 4×4 sheets are in '
        '[floor-flush-construction](../floor-flush-construction/). Six-case evidence remains the official geometry.\n')
    (output/'README.md').write_text(f'''# Flush floor-beam construction coordinates

**Dimensional packet for `compact-floor-flush-development`. Not a fabrication release.**
{width_note}
Shop instructions are in the [shop checklist](../floor-flush-shop-checklist.md) and
[assembly guide](../floor-flush-assembly-guide.md). Occupied CAD diameters and
`modeled_length_mm` values are analysis envelopes. Use the `shop_*` columns for
finished bolt-hole range, purchased Hillman length and SDS wood-lead-hole rules.

Candidate: `compact-floor-flush-development`. Width option: `{width_option}`. See
[the current package](../floor-flush-build-package.md) for evidence status.

- `stock.csv` gives stock allowances, not finished lengths.
- `stock-profiles.json` records actual trimmed raw timber vertices in world millimetres.
- Eight `*-bolt-sheet.svg` sheets show those actual profiles and relocated bolt axes.
- `bolt-member-datums.csv` and `profile-corner-datums.csv` share a physical corner datum,
  along-grain A and signed cross-grain C. Identify the corner on the sheet before layout.
- Leg taper sheets and `leg-taper-cuts.csv` specify separate inner-face removal.
- `runner-end-geometry.json` records the square front and inclined rear cut endpoints.
- `connection-axes.csv`, `panel-attachment-axes.csv`, `panel-hole-axes.csv` and
  `timber-passages.json` retain the current screw, panel and passage coordinates.
- `bolt-hardware.csv` describes current catalog bolt stacks plus shop hole-range columns.

Use numerical coordinates, not image scale. Left and right use their own physical
minimum-X datum: do not mirror a datum convention blindly. Kickers remain whole.
All timber profiles assume fresh stock; previous holes are not repair instructions.
''')
    if any(exporter.shared.digest(ROOT/path) != digest for path, digest in sources.items()):
        raise ValueError('Sources changed during construction generation')
    artifacts = {p.name: exporter.shared.digest(p) for p in sorted(output.iterdir()) if p.name != 'manifest.json'}
    (output/'manifest.json').write_text(json.dumps({'candidate': model.KEY, 'width_option': width_option,
        'assessment_status': STATUS,
        'source_sha256': dict(sorted(sources.items())), 'artifact_sha256': artifacts,
        'scope': 'Draft current geometry coordinates only; no transferred historical acceptance.'}, indent=2)+'\n')
    return output


def check(saved=OUT, *, width_option=None):
    """Rebuild in an empty directory and require byte-identical package files."""
    saved = Path(saved)
    if width_option is None:
        width_option = width.KERF_RIGHT if saved.resolve() == KERF_OUT.resolve() else width.OFFICIAL
    with tempfile.TemporaryDirectory() as directory:
        rebuilt = generate(Path(directory) / saved.name, width_option=width_option)
        saved_files = {path.relative_to(saved) for path in saved.rglob('*') if path.is_file()}
        rebuilt_files = {path.relative_to(rebuilt) for path in rebuilt.rglob('*') if path.is_file()}
        if saved_files != rebuilt_files:
            raise ValueError('Construction package file inventory differs')
        for name in saved_files:
            if (saved / name).read_bytes() != (rebuilt / name).read_bytes():
                raise ValueError('Construction package differs: ' + str(name))
    return saved


def generate_all():
    return generate(OUT, width_option=width.OFFICIAL), generate(KERF_OUT, width_option=width.KERF_RIGHT)


def check_all():
    return check(OUT, width_option=width.OFFICIAL), check(KERF_OUT, width_option=width.KERF_RIGHT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--width', choices=width.OPTIONS)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.output or args.width:
        option = args.width or width.OFFICIAL
        target = args.output or (KERF_OUT if option == width.KERF_RIGHT else OUT)
        print(check(target, width_option=option) if args.check else generate(target, width_option=option))
    else:
        print(check_all() if args.check else generate_all())
