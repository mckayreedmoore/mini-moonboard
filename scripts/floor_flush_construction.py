"""Generate draft fabrication coordinates for the actual flush floor-beam model.

Profiles describe the current trimmed raw timber, before bores and taper removal.
Blank dimensions remain stock allowances, not finished lengths. No resistance
acceptance or machining tolerance is inferred from this dimensional packet.
"""
import argparse
import json
from contextlib import contextmanager
from pathlib import Path

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as model
from mini_moonboard import panel_grid_v2 as grid
from mini_moonboard.round_service_drilling import passage_rows
from scripts import clear_space_construction as shared
from scripts import floor_flush_exports as exporter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/floor-flush-construction'
STATUS = 'DRAFT — current geometry only; resistance and fabrication checks pending; not a drilling release'


class SheetModel:
    """Delegate current geometry while suppressing inherited historical trim notes."""

    def __getattr__(self, name):
        return getattr(model, name)

    def trim_planes(self):
        # The preceding splice helper reports historical end cuts. Current
        # cut corners are supplied explicitly by profile-corner-datums.csv.
        return {}


@contextmanager
def sheet_context(output):
    values = {'OUT': output, 'model': SheetModel(), 'PACKET_STATUS': STATUS,
                  'PACKAGE': exporter.PACKAGE, 'HARDWARE': 'docs/floor-flush-construction/bolt-hardware.csv'}
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
    raw = {part.name: part for part in model.uncut_wood_parts()}
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


def generate(output=OUT):
    output = Path(output)
    inventory_path = ROOT / 'site/hybrid' / model.KEY / 'parts.json'
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
    output.mkdir(parents=True, exist_ok=True)
    with sheet_context(output):
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
        connections = model.connections()
        axes = [{'name': c.name, 'kind': c.kind, 'first_member': c.members[0], 'second_member': c.members[1],
            'start_x_mm': c.start.x, 'start_y_mm': c.start.y, 'start_z_mm': c.start.z,
            'direction_x': c.direction.x, 'direction_y': c.direction.y, 'direction_z': c.direction.z,
            'modeled_length_mm': c.length, 'modeled_diameter_mm': c.diameter,
            'operation': (f"Draft bolt axis; {model.bolt_dimensions(c)['hole_diameter_mm']:g} mm modeled clearance."
                if c.kind == 'bolt' else 'Fastener axis only; occupied diameter does not specify a pilot.'),
            'assessment_status': STATUS} for c in connections]
        write('connection-axes.csv', axes)
        bolts = [c for c in connections if c.kind == 'bolt']
        write('bolt-hardware.csv', [dict(name=c.name, first_member=c.members[0], second_member=c.members[1],
            **model.bolt_dimensions(c), assessment_status=STATUS) for c in bolts])
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
        for row in model.attachment_datums():
            name = row['panel']
            left = -model.b.HALF if name.endswith('_left') else 0.
            bottom = model.b.HALF if name.startswith('main_upper_') else 0.
            panel.append({'name': row['name'], 'panel': name, 'receiver': row['receiver'],
                'from_left_mm': row['x']-left, 'from_bottom_mm': row['s']-bottom,
                'vertical_axis': 'Z from floor' if name.startswith('kicker_') else 'S along panel slope',
                'operation': 'Retained SPAX axis; no insert pilot or pilot diameter specified.'})
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
                                     for vertex in p.shape.Vertices()})} for p in model.uncut_wood_parts()}
        for name, value in [('stock-profiles.json', profiles), ('timber-passages.json', passage_rows(model)),
                            ('runner-end-geometry.json', model.runner_end_geometry())]:
            (output/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
        if (len(stock), len(axes), len(bolts), len(panel), sum(h['kind'] == 'hold' for h in holes)) != (26, 222, 12, 66, 142):
            raise ValueError('Unexpected candidate inventory counts')
    (output/'README.md').write_text('''# Flush floor-beam construction coordinates — draft

**Geometry reference only. Current resistance and fabrication gates remain open;
these are not released cut or drilling instructions.**

Candidate: `compact-floor-flush-development`. See
[the current package](../floor-flush-build-package.md) for completion status.

- `stock.csv` gives stock allowances, not finished lengths.
- `stock-profiles.json` records actual trimmed raw timber vertices in world millimetres.
- Eight `*-bolt-sheet.svg` sheets show those actual profiles and relocated bolt axes.
- `bolt-member-datums.csv` and `profile-corner-datums.csv` share a physical corner datum,
  along-grain A and signed cross-grain C. Identify the corner on the sheet before layout.
- Leg taper sheets and `leg-taper-cuts.csv` specify separate inner-face removal.
- `runner-end-geometry.json` records the square front and inclined rear cut endpoints.
- `connection-axes.csv`, `panel-attachment-axes.csv`, `panel-hole-axes.csv` and
  `timber-passages.json` retain the current screw, panel and passage coordinates.
- `bolt-hardware.csv` describes current catalog bolt stacks; drawing precision does
  not establish fabrication tolerance, pilot bits, acceptable substitutions or capacity.

Use numerical coordinates, not image scale. Left and right use their own physical
minimum-X datum: do not mirror a datum convention blindly. Kickers remain whole.
All timber profiles assume fresh stock; previous holes are not repair instructions.
''')
    if any(exporter.shared.digest(ROOT/path) != digest for path, digest in sources.items()):
        raise ValueError('Sources changed during construction generation')
    artifacts = {p.name: exporter.shared.digest(p) for p in sorted(output.iterdir()) if p.name != 'manifest.json'}
    (output/'manifest.json').write_text(json.dumps({'candidate': model.KEY, 'assessment_status': STATUS,
        'source_sha256': dict(sorted(sources.items())), 'artifact_sha256': artifacts,
        'scope': 'Draft current geometry coordinates only; no transferred historical acceptance.'}, indent=2)+'\n')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    print(generate(args.output))
