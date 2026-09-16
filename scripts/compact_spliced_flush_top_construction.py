"""Generate exact, non-release construction coordinates for flush-top candidate."""
import argparse
import csv
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

import cadquery as cq

from mini_moonboard import compact_spliced_flush_top as model
from mini_moonboard import no_shoes_frame as baseline
from mini_moonboard import panel_grid_v2 as grid
from mini_moonboard.round_service_drilling import passage_rows
from scripts import clear_space_construction as shared
from scripts import compact_spliced_flush_top_exports as exporter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/compact-spliced-flush-top-construction'
STATUS = ('Development package — splice/member cases pass; retained ML24Z/SDS '
          'connection gate open')


def write_csv(name, rows):
    """Write reproducible LF-terminated construction tables."""
    with (shared.OUT / name).open('w', newline='') as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(dict.fromkeys(key for row in rows for key in row)),
            lineterminator='\n',
        )
        writer.writeheader()
        writer.writerows(rows)


class SheetModel:
    """Delegate exact geometry while suppressing inherited obsolete trim notes."""

    def __getattr__(self, name):
        return getattr(model, name)

    def trim_planes(self):
        return {}


@contextmanager
def sheet_context(output):
    values = {
        'OUT': output,
        'model': SheetModel(),
        'write_csv': write_csv,
        'PACKET_STATUS': STATUS,
        'PACKAGE': exporter.PACKAGE,
        'HARDWARE': 'docs/compact-spliced-flush-top-construction/bolt-hardware.csv',
    }
    old = {key: getattr(shared, key) for key in values}
    try:
        for key, value in values.items():
            setattr(shared, key, value)
        yield
    finally:
        for key, value in old.items():
            setattr(shared, key, value)


def profile_corner_rows(datums):
    """Dimension each actual joined-member side-profile corner from its datum."""
    raw = {part.name: part for part in model.uncut_wood_parts()}
    rows = []
    for name in sorted({row['member'] for row in datums}):
        datum = next(row for row in datums if row['member'] == name)
        origin = cq.Vector(*(datum[f'origin_{axis}_mm'] for axis in 'xyz'))
        along = cq.Vector(0., datum['along_y'], datum['along_z'])
        cross = cq.Vector(0., datum['cross_y'], datum['cross_z'])
        points = sorted(
            {tuple(vertex.Center().toTuple()) for vertex in raw[name].shape.Vertices()
             if abs(vertex.Center().x - origin.x) < 1.e-6},
            key=lambda point: ((cq.Vector(*point) - origin).dot(along),
                               (cq.Vector(*point) - origin).dot(cross)),
        )
        for number, xyz in enumerate(points, 1):
            offset = cq.Vector(*xyz) - origin
            rows.append({
                'member': name,
                'corner': number,
                'origin_x_mm': origin.x,
                'origin_y_mm': origin.y,
                'origin_z_mm': origin.z,
                'along_from_corner_mm': offset.dot(along),
                'signed_cross_from_corner_mm': offset.dot(cross),
                'world_x_mm': xyz[0],
                'world_y_mm': xyz[1],
                'world_z_mm': xyz[2],
                'detail': 'Exact fresh-stock side-profile corner; perimeter order comes from stock-profiles.json.',
                'assessment_status': STATUS,
            })
    return rows


def _panel_rows():
    rows = []
    for datum in model.attachment_datums():
        name = datum['panel']
        left = -model.b.HALF if name.endswith('_left') else 0.
        bottom = model.b.HALF if name.startswith('main_upper_') else 0.
        rows.append({
            'name': datum['name'],
            'panel': name,
            'receiver': datum['receiver'],
            'from_left_mm': datum['x'] - left,
            'from_bottom_mm': datum['s'] - bottom,
            'vertical_axis': 'Z from floor' if name.startswith('kicker_') else 'S along panel slope',
            'operation': ('Attachment axis retained. Viewer dimensions remain a historical '
                          'SPAX proxy; selected Fas-n-Tite/Hillman 42605 remains contained '
                          'in the 139.7 mm receiver, but exact geometry is not modeled.'),
        })
    return rows


def _panel_holes():
    holes = []
    for kind, datums, diameter in (
            ('hold', grid.main_tnut_datums(), 11.1125),
            ('LED', grid.main_led_datums(), 13.)):
        for label, (x, station) in datums.items():
            side = 'left' if x < model.b.HALF else 'right'
            band = 'lower' if station < model.b.HALF else 'upper'
            holes.append({
                'label': label,
                'kind': kind,
                'panel': f'main_{band}_{side}',
                'from_left_mm': x - (0 if side == 'left' else model.b.HALF),
                'from_bottom_mm': station - (0 if band == 'lower' else model.b.HALF),
                'diameter_mm': diameter,
            })
    for label, (x, z) in grid.kicker_foothold_datums().items():
        side = 'left' if x < model.b.HALF else 'right'
        holes.append({
            'label': label,
            'kind': 'hold',
            'panel': 'kicker_' + side,
            'from_left_mm': x - (0 if side == 'left' else model.b.HALF),
            'from_bottom_mm': baseline.KICKER_HEIGHT_MM + z,
            'diameter_mm': 11.1125,
        })
    return holes


def bolt_hardware_rows(connections):
    """Combine modeled stack geometry with exact catalog acceptance requirements."""
    rows = []
    for connection in connections:
        if connection.kind != 'bolt':
            continue
        dimensions = {
            'modeled_' + key: value
            for key, value in model.bolt_dimensions(connection).items()
            if key not in {'provisional', 'thread_length_mm', 'thread_start_mm'}
        }
        dimensions['catalog_nominal_bolt_diameter_mm'] = connection.diameter
        dimensions['catalog_nominal_bolt_length_mm'] = connection.length
        rows.append({
            'name': connection.name,
            'first_member': connection.members[0],
            'second_member': connection.members[1],
            'assessment_status': STATUS,
            **dimensions,
            **exporter.bolt_hardware_spec(connection),
        })
    return rows


def generate(output=OUT):
    output = Path(output)
    inventory_path = ROOT / 'site/hybrid' / model.KEY / 'parts.json'
    export_manifest_path = inventory_path.with_name('manifest.json')
    export_manifest = json.loads(export_manifest_path.read_text())
    sources = exporter.sources()
    if export_manifest['source_sha256'] != sources:
        raise ValueError('Flush-top viewer sources are stale; rebuild export first')
    for name, digest in export_manifest['artifact_sha256'].items():
        if exporter.shared.digest(inventory_path.parent / name) != digest:
            raise ValueError('Flush-top viewer artifact mismatch: ' + name)
    for path in (Path(__file__), Path(shared.__file__), inventory_path, export_manifest_path):
        sources[str(path.resolve().relative_to(ROOT))] = exporter.shared.digest(path)
    inventory = json.loads(inventory_path.read_text())
    if inventory['design']['key'] != model.KEY:
        raise ValueError('Wrong candidate inventory')

    output.mkdir(parents=True, exist_ok=True)
    with sheet_context(output):
        write = shared.write_csv
        stock = []
        for item in inventory['parts']:
            fabrication = item['fabrication']
            if fabrication['kind'] != 'part' or item['name'].startswith('clip_'):
                continue
            dimensions = fabrication['dimensions_mm']
            stock.append({
                'member': item['name'],
                'blank_length_or_panel_width_mm': dimensions[0],
                'blank_depth_or_panel_height_mm': dimensions[1],
                'thickness_mm': dimensions[2],
                'quantity': 1,
                'detail': 'Stock allowance; exact fresh-stock profile is recorded separately.',
                'assessment_status': STATUS,
            })
        write('stock.csv', stock)

        connections = model.connections()
        bolts = [connection for connection in connections if connection.kind == 'bolt']
        axes = [{
            'name': connection.name,
            'kind': connection.kind,
            'first_member': connection.members[0],
            'second_member': connection.members[1],
            'start_x_mm': connection.start.x,
            'start_y_mm': connection.start.y,
            'start_z_mm': connection.start.z,
            'direction_x': connection.direction.x,
            'direction_y': connection.direction.y,
            'direction_z': connection.direction.z,
            'modeled_length_mm': connection.length,
            'modeled_diameter_mm': connection.diameter,
            'operation': (f"Development bolt axis; {model.bolt_dimensions(connection)['hole_diameter_mm']:g} mm modeled clearance."
                          if connection.kind == 'bolt'
                          else ('Fastener axis only. Panel/kicker occupied dimensions remain '
                                'a historical SPAX proxy; selected model 42605 is not '
                                'dimensionally modeled.')),
            'assessment_status': STATUS,
        } for connection in connections]
        write('connection-axes.csv', axes)
        write('bolt-hardware.csv', bolt_hardware_rows(connections))

        datums = shared.bolt_member_datums(connections)
        for row in datums:
            row['instruction'] = ('Development axis normal to side face; identify physical '
                                  'corner and signed directions. Not a drilling release.')
        write('bolt-member-datums.csv', datums)
        write('profile-corner-datums.csv', profile_corner_rows(datums))
        shared.joined_member_sheets(datums)
        shared.end_trim_diagram()
        for path in output.glob('*.svg'):
            content = path.read_text()
            content = content.replace('conditional package profile', 'DEVELOPMENT current profile')
            content = content.replace('CONDITIONAL BUILD PACKAGE — stated assumptions apply.',
                                      'CONDITIONAL DIY PACKAGE — stated assumptions apply.')
            content = content.replace('Full raw side profile shown; these sheets do not include every machining operation.',
                                      'Exact fresh-stock raw outline shown; see profile-corner-datums.csv.')
            content = content.replace('../compact-spliced-flush-top-construction/bolt-hardware.csv',
                                      'bolt-hardware.csv')
            path.write_text(content)

        panel = _panel_rows()
        holes = _panel_holes()
        write('panel-attachment-axes.csv', panel)
        write('panel-hole-axes.csv', holes)
        profiles = {
            part.name: {
                'stock_blank_allowance_mm': part.blank,
                'vertices_world_mm': sorted({
                    tuple(round(value, 9) for value in vertex.Center().toTuple())
                    for vertex in part.shape.Vertices()
                }),
            }
            for part in model.uncut_wood_parts()
        }
        (output / 'stock-profiles.json').write_text(
            json.dumps(profiles, indent=2, allow_nan=False) + '\n')
        (output / 'timber-passages.json').write_text(
            json.dumps(passage_rows(model), indent=2, allow_nan=False) + '\n')
        if (len(stock), len(axes), len(bolts), len(panel),
                sum(hole['kind'] == 'hold' for hole in holes)) != (28, 230, 20, 66, 142):
            raise ValueError('Unexpected flush-top inventory counts')

    (output / 'README.md').write_text('''# Compact spliced flush-top construction coordinates

**Development package. Six fresh listed assembled cases meet their stated
splice/member criteria. Retained ML24Z/SDS separation and flange-couple
applicability remain an open completion gate. Do not fabricate from this packet.**

Candidate: `compact-spliced-flush-top-development`. See
[the matching build package](../compact-spliced-flush-top-build-package.md).

- Rear-leg tops are flush to the side-rim rear faces; side rims retain 7 mm rear reserve.
- Two half-inch upper bolts per leg use the relocated 56 mm-pitch pair.
- Four independent unnotched 2x6 knee pieces and all sixteen 3/8-inch knee bolts remain.
- All 20 complete bolt stacks point nuts and tips away from the climbing space.
- `stock-profiles.json` and `profile-corner-datums.csv` describe exact fresh-stock profiles.
- Eight bolt sheets and `bolt-member-datums.csv` dimension current bolt centres.
- `bolt-hardware.csv` names exact catalog candidates and delivered-part
  full-body/thread-transition acceptance thresholds for nominal-diameter use.
- Panel, kicker and service schedules retain 66 attachment axes and current passages.
- Fas-n-Tite/Hillman model 42605 screws are selected within the accepted panel
  scope. Their nominal 45.24375 mm timber penetration remains contained in the
  139.7 mm receivers; actual head/shank/thread geometry and product-specific
  design values remain unpublished and are not substituted into archived analysis.

Use numerical coordinates, not image scale. Left and right use their own physical
minimum-X datum. Do not reuse old upper holes or transfer prior case acceptance.
Catalog identity alone does not accept a delivered bolt. Measure full-body shank
through transition, count transition/runout as threaded, and verify nut seating
and full usable formed-thread engagement per the matching build package.
''')
    if any(exporter.shared.digest(ROOT / path) != digest for path, digest in sources.items()):
        raise ValueError('Sources changed during construction generation')
    artifacts = {path.name: exporter.shared.digest(path)
                 for path in sorted(output.iterdir()) if path.name != 'manifest.json'}
    (output / 'manifest.json').write_text(json.dumps({
        'candidate': model.KEY,
        'assessment_status': STATUS,
        'source_sha256': dict(sorted(sources.items())),
        'artifact_sha256': artifacts,
        'scope': ('Exact fresh-stock construction coordinates for selected flush-top '
                  'development package; six fresh listed assembled cases meet stated '
                  'splice/member criteria. Retained ML24Z/SDS connection applicability '
                  'remains open. No transferred historical or unconditional qualification.'),
    }, indent=2) + '\n')
    return output


def check(saved=OUT):
    """Rebuild in an empty directory and require byte-identical package files."""
    saved = Path(saved)
    with tempfile.TemporaryDirectory() as directory:
        rebuilt = generate(Path(directory) / saved.name)
        saved_files = {path.relative_to(saved) for path in saved.rglob('*') if path.is_file()}
        rebuilt_files = {
            path.relative_to(rebuilt) for path in rebuilt.rglob('*') if path.is_file()
        }
        if saved_files != rebuilt_files:
            raise ValueError('Construction package file inventory differs')
        for name in saved_files:
            if (saved / name).read_bytes() != (rebuilt / name).read_bytes():
                raise ValueError('Construction package differs: ' + str(name))
    return saved


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(check(args.output) if args.check else generate(args.output))
