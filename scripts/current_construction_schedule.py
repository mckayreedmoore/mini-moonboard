"""Generate current-candidate coordinates without rebuilding display solids.

Stock blanks come from the standalone current viewer export; fastener and panel
axes come from current model factories. These are dimensional records, not a
resistance approval or a screw pilot specification.
"""
import csv
import json
from pathlib import Path

from mini_moonboard import no_shoes_exports as exporter
from mini_moonboard import no_shoes_frame as model
from mini_moonboard import panel_grid_v2 as grid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/current-construction'
INVENTORY = ROOT / 'site/hybrid/no-shoes-development/parts.json'


def write_csv(name, rows):
    with (OUT/name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def generate():
    sources = exporter.sources()
    sources[str(INVENTORY.relative_to(ROOT))] = exporter.digest(INVENTORY)
    sources[str(Path(__file__).relative_to(ROOT))] = exporter.digest(__file__)
    inventory = json.loads(INVENTORY.read_text())
    if inventory['design']['key'] != model.KEY or inventory['design']['main_face_height_mm'] != 277:
        raise ValueError('Require current 277 mm inventory')
    OUT.mkdir(exist_ok=True)
    stock = []
    for part in inventory['parts']:
        if part['fabrication']['kind'] != 'part' or part['name'].startswith('clip_'):
            continue
        dimensions = part['fabrication']['dimensions_mm']
        stock.append({'member': part['name'], 'blank_length_or_panel_width_mm': dimensions[0],
                          'blank_depth_or_panel_height_mm': dimensions[1], 'thickness_mm': dimensions[2],
                          'quantity': 1, 'detail': 'Model blank envelope; end profile is specified separately.'})
    write_csv('stock.csv', stock)
    connections = model.connections()
    axes = []
    for c in connections:
        axes.append({'name': c.name,'kind': c.kind,'first_member': c.members[0],'second_member': c.members[1],
            'start_x_mm': c.start.x,'start_y_mm': c.start.y,'start_z_mm': c.start.z,
            'direction_x': c.direction.x,'direction_y': c.direction.y,'direction_z': c.direction.z,
            'modeled_length_mm': c.length,'modeled_diameter_mm': c.diameter,
            'operation': 'Provisional leg bolt axis; 11.1125 mm modeled clearance.' if c.kind=='bolt'
                else 'Fastener axis only; occupied diameter is not a pilot-bit instruction.'})
    write_csv('connection-axes.csv',axes)
    panel = []
    for row in model.attachment_datums():
        name=row['panel']; left=-model.b.HALF if name.endswith('_left') else 0.
        bottom=model.b.HALF if name.startswith('main_upper_') else 0.
        panel.append({'name': row['name'],'panel': name,'receiver': row['receiver'],
            'from_left_mm': row['x']-left,'from_bottom_mm': row['s']-bottom,
            'vertical_axis': 'Z from floor' if name.startswith('kicker_') else 'S along panel slope',
            'operation': 'SPAX axis; no insert pilot or pilot diameter specified.'})
    write_csv('panel-attachment-axes.csv',panel)
    holes=[]
    for kind,datums,diameter in [('hold',grid.main_tnut_datums(),11.1125),('LED',grid.main_led_datums(),13.)]:
        for label,(x,s) in datums.items():
            side='left' if x<model.b.HALF else 'right'
            band='lower' if s<model.b.HALF else 'upper'
            holes.append({'label': label,'kind': kind,'panel': f'main_{band}_{side}',
                'from_left_mm': x-(0 if side=='left' else model.b.HALF),
                'from_bottom_mm': s-(0 if band=='lower' else model.b.HALF),'diameter_mm': diameter})
    for label,(x,z) in grid.kicker_foothold_datums().items():
        side='left' if x<model.b.HALF else 'right'
        holes.append({'label': label,'kind': 'hold','panel': 'kicker_'+side,
            'from_left_mm': x-(0 if side=='left' else model.b.HALF),
            'from_bottom_mm': model.KICKER_HEIGHT_MM+z,'diameter_mm': 11.1125})
    write_csv('panel-hole-axes.csv',holes)
    # The candidate translates these exact predecessor passages with its timber.
    # Keep the CAD-defined bore stations, but use current stock for edge offsets.
    from types import SimpleNamespace

    from mini_moonboard.round_service_drilling import passage_rows
    shifted_bores = tuple({**r, 'start_mm': [r['start_mm'][0], r['start_mm'][1],
        r['start_mm'][2]+model.HEIGHT_CHANGE_MM]} for r in model.previous.bore_records())
    adapter = SimpleNamespace(b=model.b, uncut_wood_parts=model.uncut_wood_parts,
                              bore_records=lambda: shifted_bores)
    passages = passage_rows(adapter)
    (OUT/'timber-passages.json').write_text(json.dumps(passages,indent=2)+'\n')
    # Exact raw-member vertices preserve bevels and panel transition profiles.
    # These are world coordinates, suitable for CAD measurement, not drill jigs.
    profiles = {p.name: {'blank_mm': p.blank, 'vertices_world_mm': sorted({
        tuple(round(v,9) for v in vertex.Center().toTuple())
        for vertex in p.shape.Vertices()})} for p in model.uncut_wood_parts()}
    (OUT/'stock-profiles.json').write_text(json.dumps(profiles,indent=2)+'\n')
    if len(stock)!=24 or len(axes)!=218 or len(panel)!=66 or sum(r['kind']=='hold' for r in holes)!=142:
        raise ValueError('Current inventory count changed; update package deliberately')
    if any(exporter.digest(ROOT/path)!=sha for path,sha in sources.items()):
        raise ValueError('Source changed during generation')
    artifacts={p.name:exporter.digest(p) for p in sorted(OUT.iterdir()) if p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps({'candidate': model.KEY,
        'main_face_height_mm': model.KICKER_HEIGHT_MM,'source_sha256': sources,
        'artifact_sha256': artifacts,'scope': 'Current candidate dimensional documentation; leg joint remains provisional.'},indent=2)+'\n')
    return OUT


if __name__=='__main__':
    print(generate())
